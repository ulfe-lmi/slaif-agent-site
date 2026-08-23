"""Real PostgreSQL evidence for Agent capability authentication."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_state.capability import (
    compute_digest,
    generate_capability_token,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.db.connections import owner_connection


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    locator = (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-capability-auth-test",
    )


async def _seed_workspace_and_capability(
    database: AgentSiteDatabase,
) -> tuple[str, dict[str, Any]]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        delegator_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Capability.Delegator',
                'capability.delegator',
                '$argon2id$v=19$m=65536,t=3,p=4$'
                'AAAAAAAAAAAAAAAAAAAAAA$'
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                'Capability Delegator', 'ACTIVE'
            ) RETURNING id
            """
        )
        site_id = await owner.fetchval(
            """
            INSERT INTO control.site (
                site_key, display_name, default_locale, component_catalog_version
            ) VALUES ('capability-auth', 'Capability Auth', 'en-US', 'catalog-v1')
            RETURNING id
            """
        )
        workspace_id = await owner.fetchval(
            """
            INSERT INTO control.workspace (
                site_id, created_by, title, delegation_preset,
                effective_scopes, status, expires_at
            ) VALUES (
                $1, $2, 'Capability Auth Workspace', 'L1',
                '["site:read","content-item:read"]'::jsonb, 'ACTIVE',
                now() + interval '1 hour'
            ) RETURNING id
            """,
            site_id,
            delegator_id,
        )
        token, public_id, digest = generate_capability_token()
        expires_at = datetime.now(UTC) + timedelta(minutes=30)
        await owner.execute(
            """
            INSERT INTO control.capability (
                workspace_id, public_id, secret_digest, scopes, expires_at
            ) VALUES ($1, $2, $3, $4::jsonb, $5)
            """,
            workspace_id,
            public_id,
            digest,
            '["site:read","content-item:read"]',
            expires_at,
        )
        row = await owner.fetchrow(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    return token, {
        "capability_id": row["id"],
        "site_id": site_id,
        "workspace_id": workspace_id,
    }


@pytest.mark.asyncio
async def test_capability_authentication_positive_negative_and_expiry_paths(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    valid_token, seeded = await _seed_workspace_and_capability(database)
    unknown_token, _public_id, _unknown_digest = generate_capability_token()
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        capability_database_settings=_control_settings(database),
    )
    async with app.router.lifespan_context(app):
        wrong_secret = valid_token[:-4] + ("0" * 4)
        app_transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=app_transport, base_url="http://agent.test"
        ) as client:
            valid_response = await client.get(
                "/api/agent/v1/session",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
            assert valid_response.status_code == 200
            assert valid_response.json() == {
                "site_id": str(seeded["site_id"]),
                "workspace_id": str(seeded["workspace_id"]),
                "scopes": ["content-item:read", "site:read"],
                "component_catalog_version": "catalog-v1",
                "composition_schema_version": "site-composition/v1",
                "content_model_schema_version": "content-model/v1",
            }

            for token in ("malformed", unknown_token, wrong_secret):
                denied = await client.get(
                    "/api/agent/v1/session",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert denied.status_code == 401
                assert token not in denied.text
                assert "digest" not in denied.text

            public_id = valid_token.split("_")[1]
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.capability SET revoked_at = now() "
                    "WHERE public_id = $1",
                    public_id,
                )
            revoked = await client.get(
                "/api/agent/v1/session",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
            assert revoked.status_code == 401
            assert valid_token not in revoked.text

            expired_token, expired_public_id, _expired_digest = (
                generate_capability_token()
            )
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                workspace_id = await owner.fetchval(
                    "SELECT id FROM control.workspace "
                    "WHERE title = 'Capability Auth Workspace'"
                )
                await owner.execute(
                    """
                    INSERT INTO control.capability (
                        workspace_id, public_id, secret_digest, scopes,
                        created_at, expires_at
                    ) VALUES ($1, $2, $3, '[]'::jsonb, now() - interval '2 hours',
                              now() - interval '1 hour')
                    """,
                    workspace_id,
                    expired_public_id,
                    compute_digest(expired_token),
                )
            expired = await client.get(
                "/api/agent/v1/session",
                headers={"Authorization": f"Bearer {expired_token}"},
            )
            assert expired.status_code == 401
            assert expired_token not in expired.text

    unavailable_settings = _control_settings(database).model_copy(
        update={
            "dsn": SecretStr(
                "postgresql://slaif_control_login:fixture@"
                "127.0.0.1:5432/slaif_unavailable"
            ),
            "expected_database": "slaif_unavailable",
            "application_name": "slaif-capability-unavailable",
        }
    )
    unavailable_app = create_agent_app(
        settings=ServiceSettings.for_test(),
        capability_database_settings=unavailable_settings,
    )
    async with unavailable_app.router.lifespan_context(unavailable_app):
        unavailable_transport = httpx.ASGITransport(app=unavailable_app)
        async with httpx.AsyncClient(
            transport=unavailable_transport, base_url="http://agent.test"
        ) as client:
            response = await client.get(
                "/api/agent/v1/session",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
        assert response.status_code == 503
        assert "postgresql" not in response.text
        assert valid_token not in response.text

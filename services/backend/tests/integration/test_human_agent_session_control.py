"""Public Control/Agent proof for the human Agent session lifecycle."""

# ruff: noqa: E501 -- explicit public route and SQL fixture contracts

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.human_authorization import (
    HumanAuthorizationService,
    MembershipChange,
)


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=3,
        application_name="human-agent-session-test",
    )


def _agent_settings(database: AgentSiteDatabase) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="human-agent-session-agent-test",
    )


@pytest.mark.asyncio
async def test_public_human_agent_workspace_capability_and_revocation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        admin = await owner.fetchval(
            "INSERT INTO control.user_account (id,identity_kind,oidc_issuer,oidc_subject,display_name,status) VALUES ($1,'OIDC','fixture',$2,'Session admin','ACTIVE') RETURNING id",
            uuid4(),
            str(uuid4()),
        )
        user = await owner.fetchval(
            "INSERT INTO control.user_account (id,identity_kind,oidc_issuer,oidc_subject,display_name,status) VALUES ($1,'OIDC','fixture',$2,'Session owner','ACTIVE') RETURNING id",
            uuid4(),
            str(uuid4()),
        )
        site = await owner.fetchval(
            "INSERT INTO control.site (site_key,display_name,default_locale,component_catalog_version) VALUES ($1,'Session site','en','catalog-v1') RETURNING id",
            f"agent-session-{uuid4().hex[:10]}",
        )
        await owner.execute(
            "INSERT INTO control.platform_administrator(user_account_id) VALUES ($1)",
            admin,
        )
    control_pool = await database.role_pool("slaif_control")
    authorization = HumanAuthorizationService(control_pool)
    await authorization.put_membership(
        admin, site, user, MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4)
    )
    adapter = ControlDatabase(_control_settings(database))
    await adapter.start()
    control_app = create_control_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST), database=adapter
    )
    agent_app = create_agent_app(
        settings=ServiceSettings.for_test(), database_settings=_agent_settings(database)
    )
    try:
        session = await adapter.human_session_service().create(user)
        headers = {
            "cookie": f"slaif_session={session.token.get_secret_value()}; slaif_csrf={session.csrf_token.get_secret_value()}",
            "X-CSRF-Token": session.csrf_token.get_secret_value(),
        }
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=control_app),
            base_url="http://control.test",
        ) as control:
            created = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                headers=headers,
                json={
                    "title": "Public Agent proof",
                    "delegation_preset": "L1_CONTENT_EDITOR",
                    "duration_hours": 1,
                    "requested_scopes": ["site:read"],
                    "source_origins": ["HTTPS://Example.COM/"],
                    "request_quota": 4,
                    "mutation_quota": 2,
                },
            )
            assert created.status_code == 201, created.text
            workspace = created.json()
            assert workspace["source_origins"] == ["https://example.com"]
            capability_response = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/{workspace['workspace_id']}/capabilities/",
                headers=headers,
            )
            assert capability_response.status_code == 201, capability_response.text
            token = capability_response.json()["token"]
            assert token.startswith("sas2_")
            listed = await control.get(
                f"/api/control/v1/sites/{site}/workspaces/",
                headers={"cookie": headers["cookie"]},
            )
            assert (
                listed.status_code == 200
                and listed.json()[0]["workspace_id"] == workspace["workspace_id"]
            )
            metadata = await control.get(
                f"/api/control/v1/sites/{site}/workspaces/{workspace['workspace_id']}/capabilities/",
                headers={"cookie": headers["cookie"]},
            )
            assert metadata.status_code == 200 and "token" not in metadata.text
        async with agent_app.router.lifespan_context(agent_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=agent_app),
                base_url="http://agent.test",
            ) as agent:
                session_response = await agent.get(
                    "/api/agent/v1/session",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert session_response.status_code == 200
                assert session_response.json()["source_origins"] == [
                    "https://example.com"
                ]
                for _ in range(3):
                    assert (
                        await agent.get(
                            "/api/agent/v1/session",
                            headers={"Authorization": f"Bearer {token}"},
                        )
                    ).status_code == 200
                assert (
                    await agent.get(
                        "/api/agent/v1/session",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                ).status_code == 429
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=control_app),
                    base_url="http://control.test",
                ) as control_again:
                    revoked = await control_again.post(
                        f"/api/control/v1/sites/{site}/workspaces/{workspace['workspace_id']}/capabilities/{capability_response.json()['capability_id']}/revoke",
                        headers=headers,
                    )
                assert revoked.status_code == 200
                assert (
                    await agent.get(
                        "/api/agent/v1/session",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                ).status_code == 401
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            audit_rows = await owner.fetch(
                "SELECT action, details::text FROM audit.human_agent_session "
                "WHERE workspace_id=$1 ORDER BY occurred_at, id",
                UUID(workspace["workspace_id"]),
            )
            assert [row["action"] for row in audit_rows] == [
                "WORKSPACE_CREATED",
                "CAPABILITY_ISSUED",
                "CAPABILITY_REVOKED",
            ]
            assert all("sas2_" not in row["details"] for row in audit_rows)
    finally:
        await adapter.stop()
        await control_pool.close()

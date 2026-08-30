"""Real Agent HTTP proof for durable, truthful QUEUED preview runs."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import get_session_operations
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection


@dataclass(frozen=True, slots=True)
class TokenBinding:
    token: str
    capability_id: UUID
    site_id: UUID
    workspace_id: UUID
    delegator_id: UUID


def _settings(database: AgentSiteDatabase) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    locator = (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=4,
        application_name="slaif-agent-browser-http-test",
    )


async def _user(owner: asyncpg.Connection[Any], suffix: str) -> UUID:
    value = await owner.fetchval(
        """
        INSERT INTO control.user_account (
            id, identity_kind, local_username, local_username_normalized,
            password_hash, display_name, status
        ) VALUES (
            gen_random_uuid(), 'LOCAL', $1, $2,
            '$argon2id$v=19$m=65536,t=3,p=4$'
            'AAAAAAAAAAAAAAAAAAAAAA$'
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA', $3, 'ACTIVE'
        ) RETURNING id
        """,
        f"Browser.Http.{suffix}",
        f"browser.http.{suffix}",
        f"Browser HTTP {suffix}",
    )
    assert isinstance(value, UUID)
    return value


async def _site(owner: asyncpg.Connection[Any], suffix: str) -> UUID:
    value = await owner.fetchval(
        """
        INSERT INTO control.site (
            site_key, display_name, default_locale, component_catalog_version
        ) VALUES ($1, $2, 'en-US', 'catalog-v1') RETURNING id
        """,
        f"browser-http-{suffix}",
        f"Browser HTTP {suffix}",
    )
    assert isinstance(value, UUID)
    return value


async def _workspace(
    owner: asyncpg.Connection[Any], *, site_id: UUID, user_id: UUID, suffix: str
) -> UUID:
    await owner.execute(
        "INSERT INTO control.site_membership("
        "site_id,user_account_id,role_key,delegation_ceiling) "
        "VALUES ($1,$2,'SITE_OWNER',4)",
        site_id,
        user_id,
    )
    value = await owner.fetchval(
        """
        INSERT INTO control.workspace (
            site_id, created_by, delegator_id, actor_type, title, delegation_preset,
            effective_scopes, status, expires_at
        ) VALUES (
            $1, $2, $2, 'AGENT', $3, 'L1', '["preview:inspect"]'::jsonb,
            'ACTIVE', CURRENT_TIMESTAMP + interval '2 hours'
        ) RETURNING id
        """,
        site_id,
        user_id,
        f"Browser HTTP workspace {suffix}",
    )
    assert isinstance(value, UUID)
    return value


async def _capability(
    owner: asyncpg.Connection[Any],
    *,
    site_id: UUID,
    workspace_id: UUID,
    delegator_id: UUID,
    scopes: tuple[str, ...] = ("preview:inspect",),
    max_runs: int = 20,
    max_concurrent: int = 10,
) -> TokenBinding:
    token, public_id, digest = generate_capability_token()
    capability_id = await owner.fetchval(
        """
        INSERT INTO control.capability (
            workspace_id, public_id, secret_digest, scopes, expires_at,
            browser_max_runs, browser_max_concurrent_runs,
            browser_max_artifact_bytes
        ) VALUES (
            $1, $2, $3, $4::jsonb, CURRENT_TIMESTAMP + interval '1 hour',
            $5, $6, 104857600
        ) RETURNING id
        """,
        workspace_id,
        public_id,
        digest,
        json.dumps(scopes),
        max_runs,
        max_concurrent,
    )
    assert isinstance(capability_id, UUID)
    return TokenBinding(token, capability_id, site_id, workspace_id, delegator_id)


async def _seed(database: AgentSiteDatabase) -> dict[str, TokenBinding]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        user_a = await _user(owner, uuid4().hex[:8])
        user_b = await _user(owner, uuid4().hex[:8])
        site_a = await _site(owner, uuid4().hex[:8])
        site_b = await _site(owner, uuid4().hex[:8])
        workspace_a = await _workspace(
            owner, site_id=site_a, user_id=user_a, suffix="a"
        )
        workspace_b = await _workspace(
            owner, site_id=site_b, user_id=user_b, suffix="b"
        )
        return {
            "primary": await _capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=user_a,
            ),
            "same_workspace": await _capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=user_a,
            ),
            "foreign": await _capability(
                owner,
                site_id=site_b,
                workspace_id=workspace_b,
                delegator_id=user_b,
            ),
            "missing_scope": await _capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=user_a,
                scopes=("site:read",),
            ),
            "quota": await _capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=user_a,
                max_runs=0,
                max_concurrent=0,
            ),
            "race": await _capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=user_a,
            ),
        }


def _authorization(binding: TokenBinding) -> dict[str, str]:
    return {"Authorization": f"Bearer {binding.token}"}


def _create_headers(binding: TokenBinding, key: str) -> dict[str, str]:
    return {**_authorization(binding), "Idempotency-Key": key}


def _body(route: str = "/news?b=2&a=1") -> dict[str, object]:
    return {
        "version": "browser-preview/v1",
        "route": route,
        "target": "desktop-chromium",
        "evidence": ["screenshot", "heading-summary"],
    }


async def _counts(
    database: AgentSiteDatabase, capability_id: UUID
) -> tuple[int, int, int, int]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT "
            "(SELECT count(*) FROM control.browser_run WHERE capability_id=$1), "
            "(SELECT count(*) FROM control.browser_idempotency "
            "WHERE capability_id=$1), "
            "(SELECT count(*) FROM control.browser_artifact WHERE capability_id=$1), "
            "(SELECT count(*) FROM audit.browser_event WHERE capability_id=$1)",
            capability_id,
        )
    return tuple(int(value) for value in row)  # type: ignore[return-value]


async def _wait_for_advisory_waiter(
    administrator: asyncpg.Connection[Any], database_name: str
) -> None:
    for _ in range(200):
        found = await administrator.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_stat_activity "
            "WHERE datname=$1 AND application_name='slaif-agent-browser-http-test' "
            "AND wait_event_type='Lock' AND wait_event='advisory' AND state='active')",
            database_name,
        )
        if found:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("Agent browser HTTP request did not wait on advisory lock")


@pytest.mark.asyncio
async def test_public_agent_browser_routes_are_durable_truthful_and_confined(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    bindings = await _seed(database)
    settings = _settings(database)
    app = create_agent_app(
        settings=ServiceSettings.for_test(), database_settings=settings
    )
    run_id: str
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
        ) as client:
            created = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["primary"], "preview-create"),
                json=_body(),
            )
            assert created.status_code == 202
            assert created.headers["cache-control"] == "private, no-store"
            created_body = created.json()
            run_id = created_body["run_id"]
            assert created_body["state"] == "QUEUED"
            assert created_body["route"] == "/news?a=1&b=2"
            assert created_body["target"] == "desktop-chromium"
            assert "workspace_id" not in created_body
            assert "capability_id" not in created_body
            assert "token" not in created.text.casefold()
            assert await _counts(database, bindings["primary"].capability_id) == (
                1,
                1,
                0,
                1,
            )

            replay = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["primary"], "preview-create"),
                json=_body(),
            )
            assert replay.status_code == 202
            assert replay.json() == created_body
            mismatch = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["primary"], "preview-create"),
                json=_body("/other"),
            )
            assert (mismatch.status_code, mismatch.json()["error"]["code"]) == (
                409,
                "IDEMPOTENCY_MISMATCH",
            )
            assert await _counts(database, bindings["primary"].capability_id) == (
                1,
                1,
                0,
                1,
            )

            missing_key = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_authorization(bindings["primary"]),
                json=_body(),
            )
            invalid_key = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["primary"], "bad key"),
                json=_body(),
            )
            invalid_body = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["primary"], "bad-body"),
                json={**_body(), "workspace_id": str(bindings["primary"].workspace_id)},
            )
            assert missing_key.status_code == invalid_key.status_code == 400
            assert invalid_body.status_code == 422

            scope = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["missing_scope"], "scope"),
                json=_body(),
            )
            quota = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["quota"], "quota"),
                json=_body(),
            )
            assert scope.status_code == 403
            assert quota.status_code == 429
            assert await _counts(database, bindings["quota"].capability_id) == (
                0,
                0,
                0,
                0,
            )

            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.capability SET expires_at="
                    "CURRENT_TIMESTAMP-interval '1 second' WHERE id=$1",
                    bindings["same_workspace"].capability_id,
                )
            expired_capability = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["same_workspace"], "expired-cap"),
                json=_body(),
            )
            assert expired_capability.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.capability SET expires_at="
                    "CURRENT_TIMESTAMP+interval '1 hour' WHERE id=$1",
                    bindings["same_workspace"].capability_id,
                )
                await owner.execute(
                    "UPDATE control.workspace SET status='REVOKED' WHERE id=$1",
                    bindings["same_workspace"].workspace_id,
                )
            revoked_workspace = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["same_workspace"], "revoked-ws"),
                json=_body(),
            )
            assert revoked_workspace.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.workspace SET status='ACTIVE',expires_at="
                    "CURRENT_TIMESTAMP-interval '1 second' WHERE id=$1",
                    bindings["same_workspace"].workspace_id,
                )
            expired_workspace = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["same_workspace"], "expired-ws"),
                json=_body(),
            )
            assert expired_workspace.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.workspace SET expires_at="
                    "CURRENT_TIMESTAMP+interval '2 hours' WHERE id=$1",
                    bindings["same_workspace"].workspace_id,
                )
                await owner.execute(
                    "UPDATE control.site SET status='ARCHIVED' WHERE id=$1",
                    bindings["foreign"].site_id,
                )
            archived_site = await client.post(
                "/api/agent/v1/preview-runs",
                headers=_create_headers(bindings["foreign"], "archived-site"),
                json=_body(),
            )
            assert archived_site.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.site SET status='ACTIVE' WHERE id=$1",
                    bindings["foreign"].site_id,
                )
            assert await _counts(
                database, bindings["same_workspace"].capability_id
            ) == (0, 0, 0, 0)
            assert await _counts(database, bindings["foreign"].capability_id) == (
                0,
                0,
                0,
                0,
            )

            before_reads = await _counts(database, bindings["primary"].capability_id)
            status = await client.get(
                f"/api/agent/v1/preview-runs/{run_id}",
                headers=_authorization(bindings["primary"]),
            )
            artifacts = await client.get(
                f"/api/agent/v1/preview-runs/{run_id}/artifacts",
                headers=_authorization(bindings["primary"]),
            )
            retrieval = await client.get(
                f"/api/agent/v1/preview-runs/{run_id}/artifacts/{uuid4()}",
                headers=_authorization(bindings["primary"]),
            )
            assert status.status_code == 200 and status.json() == created_body
            assert artifacts.status_code == 200 and artifacts.json() == []
            assert retrieval.status_code == 404
            assert (
                await _counts(database, bindings["primary"].capability_id)
                == before_reads
            )

            for binding in (
                bindings["same_workspace"],
                bindings["foreign"],
            ):
                hidden = await client.get(
                    f"/api/agent/v1/preview-runs/{run_id}",
                    headers=_authorization(binding),
                )
                assert hidden.status_code == 404
            random_run = await client.get(
                f"/api/agent/v1/preview-runs/{uuid4()}",
                headers=_authorization(bindings["primary"]),
            )
            assert random_run.status_code == 404
            for path in (
                "/internal/browser/v1/preview-runs",
                f"/internal/browser/v1/runs/{run_id}",
            ):
                absent = await client.get(path)
                assert absent.status_code == 404

    # A new application/pool reads the same durable QUEUED run.
    restarted = create_agent_app(
        settings=ServiceSettings.for_test(), database_settings=settings
    )
    async with restarted.router.lifespan_context(restarted):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=restarted),
            base_url="http://agent.test",
        ) as client:
            status = await client.get(
                f"/api/agent/v1/preview-runs/{run_id}",
                headers=_authorization(bindings["primary"]),
            )
            assert status.status_code == 200
            assert status.json()["state"] == "QUEUED"

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await get_session_operations(
                AsyncpgExecutor(owner),
                bindings["primary"].workspace_id,
                schema="content",
            )
            == []
        )
        await owner.execute(
            "UPDATE control.capability SET revoked_at=CURRENT_TIMESTAMP WHERE id=$1",
            bindings["primary"].capability_id,
        )
    revoked_app = create_agent_app(
        settings=ServiceSettings.for_test(), database_settings=settings
    )
    async with revoked_app.router.lifespan_context(revoked_app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=revoked_app),
            base_url="http://agent.test",
        ) as client:
            revoked = await client.get(
                f"/api/agent/v1/preview-runs/{run_id}",
                headers=_authorization(bindings["primary"]),
            )
            assert revoked.status_code == 401


@pytest.mark.asyncio
async def test_public_create_rechecks_revocation_after_workspace_lock(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    bindings = await _seed(database)
    race = bindings["race"]
    app = create_agent_app(
        settings=ServiceSettings.for_test(), database_settings=_settings(database)
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
        ) as client:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                async with owner.transaction():
                    await owner.fetchval(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1,280))",
                        str(race.workspace_id),
                    )
                    blocked = asyncio.create_task(
                        client.post(
                            "/api/agent/v1/preview-runs",
                            headers=_create_headers(race, "race"),
                            json=_body(),
                        )
                    )
                    await _wait_for_advisory_waiter(
                        database.administrator, database.name
                    )
                    assert not blocked.done()
                    await owner.execute(
                        "UPDATE control.capability SET revoked_at=CURRENT_TIMESTAMP "
                        "WHERE id=$1",
                        race.capability_id,
                    )
            response = await blocked
            assert response.status_code == 404
    assert await _counts(database, race.capability_id) == (0, 0, 0, 0)

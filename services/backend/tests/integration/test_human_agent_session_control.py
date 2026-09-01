"""Public Control/Agent proof for the human Agent session lifecycle."""

# ruff: noqa: E501 -- explicit public route and SQL fixture contracts

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import reconcile, status, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.human_authorization import (
    HumanAuthorizationService,
    MembershipChange,
)
from slaif_agent_site.human_authorization.catalog import (
    L1_SCOPES,
    L2_SCOPES,
    L3_SCOPES,
    L4_SCOPES,
    READ_SCOPES,
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
                json={
                    "title": "Public Agent proof",
                    "delegation_preset": "L1_CONTENT_EDITOR",
                    "duration_hours": 1,
                    "requested_scopes": ["site:read"],
                    "source_origins": ["HTTPS://Example.COM/"],
                    "request_quota": 4,
                    "mutation_quota": 2,
                },
                headers={**headers, "Idempotency-Key": "workspace-proof"},
            )
            assert created.status_code == 201, created.text
            workspace = created.json()
            assert workspace["source_origins"] == ["https://example.com"]
            replayed_workspace = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                json={
                    "title": "Public Agent proof",
                    "delegation_preset": "L1_CONTENT_EDITOR",
                    "duration_hours": 1,
                    "requested_scopes": ["site:read"],
                    "source_origins": ["HTTPS://Example.COM/"],
                    "request_quota": 4,
                    "mutation_quota": 2,
                },
                headers={**headers, "Idempotency-Key": "workspace-proof"},
            )
            assert replayed_workspace.status_code == 200
            assert (
                replayed_workspace.json()["workspace_id"] == workspace["workspace_id"]
            )
            mismatch_workspace = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                json={"title": "different", "delegation_preset": "L1_CONTENT_EDITOR"},
                headers={**headers, "Idempotency-Key": "workspace-proof"},
            )
            assert mismatch_workspace.status_code == 409
            capability_response = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/{workspace['workspace_id']}/capabilities/",
                headers={**headers, "Idempotency-Key": "capability-proof"},
            )
            assert capability_response.status_code == 201, capability_response.text
            token = capability_response.json()["token"]
            assert token.startswith("sas2_")
            capability_replay = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/{workspace['workspace_id']}/capabilities/",
                headers={**headers, "Idempotency-Key": "capability-proof"},
            )
            assert capability_replay.status_code == 200
            assert "token" not in capability_replay.text
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
                        headers={**headers, "Idempotency-Key": "revoke-proof"},
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


@pytest.mark.asyncio
async def test_site_governor_and_delegator_authority_are_rechecked(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            """
            INSERT INTO control.user_account
              (id,identity_kind,oidc_issuer,oidc_subject,display_name,status)
            VALUES
              (gen_random_uuid(),'OIDC','fixture',gen_random_uuid()::text,'Architect','ACTIVE'),
              (gen_random_uuid(),'OIDC','fixture',gen_random_uuid()::text,'Governor','ACTIVE'),
              (gen_random_uuid(),'OIDC','fixture',gen_random_uuid()::text,'Low ceiling','ACTIVE')
            """
        )
        users = {
            row["display_name"]: row["id"]
            for row in await owner.fetch(
                "SELECT id,display_name FROM control.user_account WHERE display_name IN ('Architect','Governor','Low ceiling')"
            )
        }
        creator, governor, low_ceiling = (
            users["Architect"],
            users["Governor"],
            users["Low ceiling"],
        )
        site = await owner.fetchval(
            "INSERT INTO control.site (site_key,display_name,default_locale,component_catalog_version) VALUES ($1,'Governor site','en','catalog-v1') RETURNING id",
            f"governor-{uuid4().hex[:10]}",
        )
        await owner.execute(
            "INSERT INTO control.site_membership(site_id,user_account_id,role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4),($1,$3,'SITE_ARCHITECT',4),($1,$4,'CONTENT_EDITOR',1)",
            site,
            governor,
            creator,
            low_ceiling,
        )
        await owner.execute(
            "INSERT INTO control.site_membership_permission_override(site_id,user_account_id,permission_key,effect) VALUES ($1,$2,'workspace:create','ALLOW')",
            site,
            creator,
        )
        control_pool = await database.role_pool("slaif_control")
    adapter = ControlDatabase(_control_settings(database))
    await adapter.start()
    control_app = create_control_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST), database=adapter
    )
    try:
        creator_session = await adapter.human_session_service().create(creator)
        creator_headers = {
            "cookie": f"slaif_session={creator_session.token.get_secret_value()}; slaif_csrf={creator_session.csrf_token.get_secret_value()}",
            "X-CSRF-Token": creator_session.csrf_token.get_secret_value(),
        }
        governor_session = await adapter.human_session_service().create(governor)
        governor_headers = {
            "cookie": f"slaif_session={governor_session.token.get_secret_value()}; slaif_csrf={governor_session.csrf_token.get_secret_value()}",
            "X-CSRF-Token": governor_session.csrf_token.get_secret_value(),
        }
        low_session = await adapter.human_session_service().create(low_ceiling)
        low_headers = {
            "cookie": f"slaif_session={low_session.token.get_secret_value()}; slaif_csrf={low_session.csrf_token.get_secret_value()}",
            "X-CSRF-Token": low_session.csrf_token.get_secret_value(),
        }
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=control_app),
            base_url="http://control.test",
        ) as control:
            csrf_missing = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                json={"title": "csrf", "delegation_preset": "L1_CONTENT_EDITOR"},
                headers={
                    "cookie": creator_headers["cookie"],
                    "Idempotency-Key": "csrf",
                },
            )
            assert csrf_missing.status_code in {400, 403}
            workspaces: dict[str, dict[str, object]] = {}
            for index, preset in enumerate(
                (
                    "L1_CONTENT_EDITOR",
                    "L2_SITE_EDITOR",
                    "L3_SITE_DESIGNER",
                    "L4_SITE_ARCHITECT",
                )
            ):
                response = await control.post(
                    f"/api/control/v1/sites/{site}/workspaces/",
                    json={"title": preset, "delegation_preset": preset},
                    headers={**creator_headers, "Idempotency-Key": f"preset-{index}"},
                )
                assert response.status_code == 201, response.text
                workspaces[preset] = response.json()
                expected = {
                    "L1_CONTENT_EDITOR": READ_SCOPES | L1_SCOPES,
                    "L2_SITE_EDITOR": READ_SCOPES | L1_SCOPES | L2_SCOPES,
                    "L3_SITE_DESIGNER": READ_SCOPES | L1_SCOPES | L2_SCOPES | L3_SCOPES,
                    "L4_SITE_ARCHITECT": READ_SCOPES
                    | L1_SCOPES
                    | L2_SCOPES
                    | L3_SCOPES
                    | L4_SCOPES,
                }[preset]
                assert expected <= set(response.json()["effective_scopes"])
            empty = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                json={
                    "title": "explicit empty",
                    "delegation_preset": "L1_CONTENT_EDITOR",
                    "requested_scopes": [],
                },
                headers={**creator_headers, "Idempotency-Key": "explicit-empty"},
            )
            assert empty.status_code == 201 and empty.json()["effective_scopes"] == []
            duplicate = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                json={
                    "title": "duplicate",
                    "delegation_preset": "L1_CONTENT_EDITOR",
                    "requested_scopes": ["site:read", "site:read"],
                },
                headers={**creator_headers, "Idempotency-Key": "duplicate"},
            )
            assert duplicate.status_code == 422
            denied = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/",
                json={"title": "too high", "delegation_preset": "L4_SITE_ARCHITECT"},
                headers={**low_headers, "Idempotency-Key": "low-ceiling"},
            )
            assert denied.status_code in {403, 404}
            target = workspaces["L4_SITE_ARCHITECT"]["workspace_id"]
            low_capability = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/{target}/capabilities/",
                headers={**low_headers, "Idempotency-Key": "low-capability"},
            )
            assert low_capability.status_code in {403, 404}
            listed = await control.get(
                f"/api/control/v1/sites/{site}/workspaces/",
                headers={"cookie": governor_headers["cookie"]},
            )
            assert listed.status_code == 200
            assert any(item["workspace_id"] == target for item in listed.json())
            foreign = await control.get(
                f"/api/control/v1/sites/{uuid4()}/workspaces/",
                headers={"cookie": governor_headers["cookie"]},
            )
            assert foreign.status_code == 404
            inspected = await control.get(
                f"/api/control/v1/sites/{site}/workspaces/{target}",
                headers={"cookie": governor_headers["cookie"]},
            )
            assert inspected.status_code == 200
            issued = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/{target}/capabilities/",
                headers={**governor_headers, "Idempotency-Key": "governor-issue"},
            )
            assert issued.status_code == 201 and issued.json()["token"].startswith(
                "sas2_"
            )
            capability_id = issued.json()["capability_id"]
            capability_list = await control.get(
                f"/api/control/v1/sites/{site}/workspaces/{target}/capabilities/",
                headers={"cookie": governor_headers["cookie"]},
            )
            assert capability_list.status_code == 200
            revoked = await control.post(
                f"/api/control/v1/sites/{site}/workspaces/{target}/capabilities/{capability_id}/revoke",
                headers={**governor_headers, "Idempotency-Key": "governor-revoke"},
            )
            assert revoked.status_code == 200
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            audit = await owner.fetch(
                "SELECT action,actor_user_id FROM audit.human_agent_session WHERE actor_user_id=$1 ORDER BY occurred_at,id",
                governor,
            )
            assert [row["action"] for row in audit] == [
                "CAPABILITY_ISSUED",
                "CAPABILITY_REVOKED",
            ]
            await owner.execute(
                "UPDATE control.site_membership SET status='INACTIVE',version=version+1 WHERE site_id=$1 AND user_account_id=$2",
                site,
                creator,
            )
        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool, session_id=UUID(str(target)), operation_id=uuid4()
            ) as cow:
                try:
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_content_type_create($1,$2,$3,$4,$5)",
                        site,
                        "blocked-after-ceiling",
                        '{"en":"Blocked"}',
                        "/blocked/{slug}",
                        "{}",
                    )
                except asyncpg.PostgresError:
                    await cow.rollback()
                else:
                    raise AssertionError(
                        "inactive delegator wrapper unexpectedly succeeded"
                    )
        finally:
            await agent_pool.close()
    finally:
        await adapter.stop()
        await control_pool.close()


@pytest.mark.asyncio
async def test_session_migrations_round_trip_through_037(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="037_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT version_num::text FROM control.alembic_version"
            )
            == "037_001"
        )
        assert await owner.fetchval(
            "SELECT to_regclass('audit.human_agent_session') IS NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regprocedure('control.slaif_agent_capability_context(text)') IS NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regclass('control.workspace') IS NOT NULL"
        )
        assert await owner.fetchval(
            "SELECT NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='control' AND table_name='workspace' AND column_name IN ('delegator_id','request_quota','create_idempotency_key'))"
        )
        assert await owner.fetchval(
            "SELECT has_function_privilege('slaif_agent_runtime','control.slaif_agent_capability_authenticate(text)','EXECUTE')"
        )
        result = await owner.fetchval(
            "SELECT pg_get_function_result('control.slaif_agent_capability_authenticate(text)'::regprocedure)"
        )
        assert (
            "browser_allowed_targets" in result and "resource_constraints" not in result
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )
    await reconcile(database.settings)
    assert (await status(database.settings)).revision == "048_001"

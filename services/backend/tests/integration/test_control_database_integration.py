"""Control pool, readiness function, and denial-matrix integration tests."""

from __future__ import annotations

from urllib.parse import quote

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import (
    ControlDatabase,
    ControlDatabaseReason,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES


def _control_settings(
    database: AgentSiteDatabase, role: str = "slaif_control"
) -> ControlDatabaseSettings:
    login, password = database.credentials[role]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    locator = (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/"
        f"{quote(database.name, safe='')}"
    )
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-control-test",
    )


async def test_readiness_function_owner_security_grants_and_denial_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        metadata = await connection.fetchrow(
            "SELECT owner.rolname::text, proc.prosecdef, proc.provolatile::text, "
            "proc.proparallel::text, "
            "pg_catalog.pg_get_function_identity_arguments(proc.oid), "
            "COALESCE(array_to_string(proc.proconfig, ','), ''), "
            "EXISTS (SELECT 1 FROM pg_catalog.aclexplode(COALESCE(proc.proacl, "
            "pg_catalog.acldefault('f', proc.proowner))) acl "
            "WHERE acl.grantee = 0 AND acl.privilege_type = 'EXECUTE') "
            "FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "JOIN pg_catalog.pg_roles owner ON owner.oid = proc.proowner "
            "WHERE namespace_.nspname = 'control' "
            "AND proc.proname = 'slaif_control_readiness'"
        )
        assert tuple(metadata) == (
            "slaif_owner",
            True,
            "s",
            "r",
            "",
            "search_path=pg_catalog",
            False,
        )
        grants = await connection.fetch(
            "SELECT grantee.rolname::text, acl.privilege_type::text, "
            "acl.is_grantable FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "CROSS JOIN LATERAL pg_catalog.aclexplode(proc.proacl) acl "
            "JOIN pg_catalog.pg_roles grantee ON grantee.oid = acl.grantee "
            "WHERE namespace_.nspname = 'control' "
            "AND proc.proname = 'slaif_control_readiness' "
            "ORDER BY grantee.rolname, acl.privilege_type"
        )
        assert [tuple(row) for row in grants] == [
            ("slaif_control", "EXECUTE", False),
            ("slaif_owner", "EXECUTE", False),
        ]

    pools = {role: await database.role_pool(role) for role in ROLE_NAMES[1:]}
    try:
        async with pools["slaif_control"].acquire() as control:
            row = await control.fetchrow(
                "SELECT * FROM control.slaif_control_readiness()"
            )
            assert row["schema_revision"] == "050_001"
            assert row["marker_revision"] == "050_001"
            assert row["readiness_state"] in ("HARDENED", "HARDENED")
            assert row["safe"] is True
            assert row["foundation_distribution"] == "agent-cow-postgresql"
            assert row["foundation_version"] == "0.2.0"
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await control.fetch("SELECT * FROM control.bootstrap_readiness")
        for role, pool in pools.items():
            if role == "slaif_control":
                continue
            async with pool.acquire() as connection:
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch(
                        "SELECT * FROM control.slaif_control_readiness()"
                    )
    finally:
        for pool in pools.values():
            await pool.close()


async def test_control_pool_reports_exact_marker_migration_and_foundation_state(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    adapter = ControlDatabase(_control_settings(database))
    await adapter.start()
    try:
        assert (await adapter.readiness()).reason is None
        activity = await database.administrator.fetchval(
            "SELECT count(*) FROM pg_catalog.pg_stat_activity "
            "WHERE datname = $1 AND application_name = 'slaif-control-test'",
            database.name,
        )
        assert activity >= 1

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as connection:
            await connection.execute(
                "UPDATE control.bootstrap_readiness "
                "SET migration_revision = '006_001' WHERE singleton"
            )
        assert (await adapter.readiness()).reason == (
            ControlDatabaseReason.MIGRATION_MISMATCH.value
        )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as connection:
            await connection.execute(
                "UPDATE control.bootstrap_readiness "
                "SET migration_revision = '050_001', "
                "foundation_version = '0.0.0' WHERE singleton"
            )
        assert (await adapter.readiness()).reason == (
            ControlDatabaseReason.FOUNDATION_MISMATCH.value
        )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as connection:
            await connection.execute(
                "UPDATE control.bootstrap_readiness SET "
                "foundation_version = '0.2.0', readiness_state = 'PENDING', "
                "content_object_count = 0, content_object_fingerprint = NULL, "
                "foundation_object_count = 0, foundation_object_fingerprint = NULL, "
                "foundation_hardened = FALSE, "
                "foundation_privileges_validated = FALSE, "
                "product_privileges_validated = FALSE, safe = FALSE "
                "WHERE singleton"
            )
        assert (await adapter.readiness()).reason == (
            ControlDatabaseReason.UNSAFE_MARKER.value
        )

        await reconcile(database.settings)
        assert (await adapter.readiness()).reason is None
    finally:
        await adapter.stop()
    activity = await database.administrator.fetchval(
        "SELECT count(*) FROM pg_catalog.pg_stat_activity "
        "WHERE datname = $1 AND application_name = 'slaif-control-test'",
        database.name,
    )
    assert activity == 0


async def test_pool_rejects_wrong_and_combined_authorities(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)

    for role in (
        "slaif_owner",
        "slaif_agent_runtime",
        "slaif_editor_runtime",
        "slaif_reviewer",
    ):
        adapter = ControlDatabase(_control_settings(database, role))
        await adapter.start()
        assert (await adapter.readiness()).reason == (
            ControlDatabaseReason.ROLE_MISMATCH.value
        )
        await adapter.stop()

    control_login, _password = database.credentials["slaif_control"]
    await database.administrator.execute(f'GRANT "slaif_reviewer" TO "{control_login}"')
    try:
        combined = ControlDatabase(_control_settings(database))
        await combined.start()
        assert (await combined.readiness()).reason == (
            ControlDatabaseReason.ROLE_MISMATCH.value
        )
        await combined.stop()
    finally:
        await database.administrator.execute(
            f'REVOKE "slaif_reviewer" FROM "{control_login}"'
        )


@pytest.mark.asyncio
async def test_control_setup_status_http_boundary(
    agent_site_database: AgentSiteDatabase,
) -> None:
    await upgrade(agent_site_database.settings)
    await reconcile(agent_site_database.settings)
    adapter = ControlDatabase(_control_settings(agent_site_database))
    await adapter.start()
    try:
        app = create_app(settings=ServiceSettings.for_test(), database=adapter)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.get("/api/control/v1/setup/status")
        assert response.status_code == 200
        assert response.json() == {"initialized": False, "setup_available": False}
    finally:
        await adapter.stop()

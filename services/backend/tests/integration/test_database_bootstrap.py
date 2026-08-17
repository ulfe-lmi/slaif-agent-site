"""Agent-Site migration, bootstrap, and effective-privilege integration tests."""

from __future__ import annotations

import asyncio
import contextlib
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
    deploy_cow_functions,
)
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
    reconcile,
    status,
    upgrade,
    validate,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.db.privileges import (
    content_object_inventory,
    verify_database_privileges,
)
from slaif_agent_site.db.readiness import ReadinessState
from slaif_agent_site.db.roles import ROLE_NAMES, quote_identifier

QUALIFICATION_TABLE = '"content"."qualification_item"'
QUALIFICATION_BASE = '"content"."qualification_item_base"'
QUALIFICATION_CHANGES = '"content"."qualification_item_changes"'


def _assert_pending(marker: Any, *, deployed: bool) -> None:
    assert marker.state is ReadinessState.PENDING
    assert marker.content_object_count == 0
    assert marker.content_object_fingerprint is None
    assert marker.foundation_object_count == 0
    assert marker.foundation_object_fingerprint is None
    assert marker.foundation_deployed is deployed
    assert not marker.foundation_hardened
    assert not marker.foundation_privileges_validated
    assert not marker.product_privileges_validated
    assert not marker.safe


def _assert_empty_safe(marker: Any) -> None:
    assert marker.state is ReadinessState.EMPTY_SAFE
    assert marker.content_object_count == 0
    assert marker.content_object_fingerprint is None
    assert marker.foundation_object_count > 0
    assert marker.foundation_object_fingerprint is not None
    assert len(marker.foundation_object_fingerprint) == 64
    assert marker.foundation_deployed
    assert not marker.foundation_hardened
    assert not marker.foundation_privileges_validated
    assert marker.product_privileges_validated
    assert marker.safe


def _assert_hardened(marker: Any) -> None:
    assert marker.state is ReadinessState.HARDENED
    assert marker.content_object_count > 0
    assert marker.content_object_fingerprint is not None
    assert len(marker.content_object_fingerprint) == 64
    assert marker.foundation_object_count > 0
    assert marker.foundation_object_fingerprint is not None
    assert len(marker.foundation_object_fingerprint) == 64
    assert marker.foundation_deployed
    assert marker.foundation_hardened
    assert marker.foundation_privileges_validated
    assert marker.product_privileges_validated
    assert marker.safe


async def _create_qualification_table(database: AgentSiteDatabase) -> None:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            f"CREATE TABLE {QUALIFICATION_TABLE} ("
            "id integer PRIMARY KEY, title text NOT NULL)"
        )
        await connection.execute(
            f"INSERT INTO {QUALIFICATION_TABLE} (id, title) VALUES (1, 'canonical')"
        )


async def _prepare_hardened_database(database: AgentSiteDatabase) -> None:
    await upgrade(database.settings)
    await _create_qualification_table(database)
    result = await reconcile(database.settings)
    _assert_hardened(result)


async def test_clean_migration_current_repeat_downgrade_and_rebuild(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    first = await status(database.settings)
    assert first.revision == "006_001"
    _assert_pending(first, deployed=False)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        initial_time = await connection.fetchval(
            "SELECT updated_at FROM control.bootstrap_readiness WHERE singleton"
        )
        schemas = await connection.fetch(
            "SELECT nspname::text, pg_get_userbyid(nspowner)::text "
            "FROM pg_catalog.pg_namespace "
            "WHERE nspname = ANY($1::text[]) ORDER BY nspname",
            ["control", "content", "audit", "agentcow"],
        )
        assert [tuple(row) for row in schemas] == [
            ("audit", "slaif_owner"),
            ("content", "slaif_owner"),
            ("control", "slaif_owner"),
        ]
        relations = await connection.fetch(
            "SELECT schemaname::text, tablename::text FROM pg_catalog.pg_tables "
            "WHERE schemaname = ANY($1::text[]) ORDER BY schemaname, tablename",
            ["control", "content", "audit"],
        )
        assert [tuple(row) for row in relations] == [
            ("control", "alembic_version"),
            ("control", "bootstrap_readiness"),
        ]

    await upgrade(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        assert (
            await connection.fetchval(
                "SELECT updated_at FROM control.bootstrap_readiness WHERE singleton"
            )
            == initial_time
        )

    empty = await reconcile(database.settings)
    _assert_empty_safe(empty)
    validated_marker, validated = await validate(database.settings)
    _assert_empty_safe(validated_marker)
    assert validated.safe, validated.violations
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        empty_objects = await content_object_inventory(connection)
        ready_time = await connection.fetchval(
            "SELECT updated_at FROM control.bootstrap_readiness WHERE singleton"
        )
        foundation_inventory = tuple(
            await connection.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM pg_catalog.pg_class class_ "
                "JOIN pg_catalog.pg_namespace namespace_ "
                "ON namespace_.oid = class_.relnamespace "
                "WHERE namespace_.nspname = 'agentcow'), "
                "(SELECT count(*) FROM pg_catalog.pg_proc proc "
                "JOIN pg_catalog.pg_namespace namespace_ "
                "ON namespace_.oid = proc.pronamespace "
                "WHERE namespace_.nspname = 'agentcow')"
            )
        )
    assert empty_objects == ()
    assert foundation_inventory[0] > 0
    assert foundation_inventory[1] > 0

    repeated = await reconcile(database.settings)
    _assert_empty_safe(repeated)
    repeated_marker, repeated_validation = await validate(database.settings)
    _assert_empty_safe(repeated_marker)
    assert repeated_validation.safe, repeated_validation.violations
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        assert await content_object_inventory(connection) == ()
        assert (
            await connection.fetchval(
                "SELECT updated_at FROM control.bootstrap_readiness WHERE singleton"
            )
            >= ready_time
        )
        repeated_foundation_inventory = tuple(
            await connection.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM pg_catalog.pg_class class_ "
                "JOIN pg_catalog.pg_namespace namespace_ "
                "ON namespace_.oid = class_.relnamespace "
                "WHERE namespace_.nspname = 'agentcow'), "
                "(SELECT count(*) FROM pg_catalog.pg_proc proc "
                "JOIN pg_catalog.pg_namespace namespace_ "
                "ON namespace_.oid = proc.pronamespace "
                "WHERE namespace_.nspname = 'agentcow')"
            )
        )
    assert repeated_foundation_inventory == foundation_inventory

    await downgrade(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        assert not await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace "
            "WHERE nspname IN ('content', 'audit'))"
        )
        assert await connection.fetchval(
            "SELECT to_regclass('control.alembic_version') IS NOT NULL"
        )
        assert (
            await connection.fetchval("SELECT count(*) FROM control.alembic_version")
            == 0
        )

    await upgrade(database.settings)
    rebuilt = await status(database.settings)
    assert rebuilt.revision == "006_001"
    _assert_pending(rebuilt, deployed=False)
    rebuilt_empty = await reconcile(database.settings)
    _assert_empty_safe(rebuilt_empty)


async def test_role_manifest_attributes_membership_and_identity_separation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    rows = await database.administrator.fetch(
        "SELECT rolname::text, rolsuper, rolcreatedb, rolcreaterole, rolinherit, "
        "rolcanlogin, rolreplication, rolbypassrls FROM pg_catalog.pg_roles "
        "WHERE rolname = ANY($1::text[]) ORDER BY rolname",
        list(ROLE_NAMES),
    )
    assert len(rows) == len(ROLE_NAMES)
    assert {row[0] for row in rows} == set(ROLE_NAMES)
    assert all(not any(row[1:]) for row in rows)

    product_edges = await database.administrator.fetch(
        "SELECT granted.rolname::text, member.rolname::text "
        "FROM pg_catalog.pg_auth_members membership "
        "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
        "WHERE granted.rolname = ANY($1::text[]) AND member.rolname = ANY($1::text[])",
        list(ROLE_NAMES),
    )
    assert product_edges == []
    login_memberships = await database.administrator.fetchval(
        "SELECT count(*) FROM pg_catalog.pg_auth_members membership "
        "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
        "WHERE granted.rolname = ANY($1::text[]) AND member.rolcanlogin",
        list(ROLE_NAMES),
    )
    assert login_memberships == len(ROLE_NAMES)


async def test_empty_baseline_is_safe_without_false_foundation_evidence(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    marker = await reconcile(database.settings)
    _assert_empty_safe(marker)
    validated_marker, product = await validate(database.settings)
    _assert_empty_safe(validated_marker)
    assert product.safe, product.violations

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        assert await content_object_inventory(connection) == ()
        assert await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace "
            "WHERE nspname = 'agentcow')"
        )
        marker_row = tuple(
            await connection.fetchrow(
                "SELECT readiness_state, content_object_count, "
                "content_object_fingerprint, foundation_deployed, "
                "foundation_hardened, foundation_privileges_validated, "
                "product_privileges_validated, safe "
                "FROM control.bootstrap_readiness WHERE singleton"
            )
        )
        assert marker_row == (
            "EMPTY_SAFE",
            0,
            None,
            True,
            False,
            False,
            True,
            True,
        )

        for role in ROLE_NAMES[1:]:
            assert not await connection.fetchval(
                "SELECT has_schema_privilege($1, 'content', 'USAGE') "
                "OR has_schema_privilege($1, 'content', 'CREATE')",
                role,
            )
        reviewer_execution = await connection.fetchval(
            "SELECT count(*) FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "WHERE namespace_.nspname = 'agentcow' "
            "AND has_function_privilege('slaif_reviewer', proc.oid, 'EXECUTE')"
        )
        assert reviewer_execution == 0

        with pytest.raises(asyncpg.CheckViolationError):
            await connection.execute(
                "UPDATE control.bootstrap_readiness "
                "SET foundation_hardened = TRUE WHERE singleton"
            )
        with pytest.raises(asyncpg.CheckViolationError):
            await connection.execute(
                "UPDATE control.bootstrap_readiness "
                "SET readiness_state = 'PENDING' WHERE singleton"
            )
        with pytest.raises(asyncpg.CheckViolationError):
            await connection.execute(
                "UPDATE control.bootstrap_readiness "
                "SET readiness_state = 'UNKNOWN' WHERE singleton"
            )

        await connection.execute(
            "UPDATE control.bootstrap_readiness "
            "SET foundation_version = '0.0.0' WHERE singleton"
        )

    stale_marker, stale_validation = await validate(database.settings)
    _assert_empty_safe(stale_marker)
    assert not stale_validation.safe
    assert "marker/version-metadata/state-mismatch" in stale_validation.violations


@pytest.mark.parametrize(
    ("ddl", "expected_category"),
    (
        (
            "CREATE TABLE content.unexpected_table (id integer PRIMARY KEY)",
            "relation:r",
        ),
        ("CREATE VIEW content.unexpected_view AS SELECT 1 AS id", "relation:v"),
        ("CREATE SEQUENCE content.unexpected_sequence", "relation:S"),
        (
            "CREATE FUNCTION content.unexpected_function() RETURNS integer "
            "LANGUAGE sql IMMUTABLE AS 'SELECT 1'",
            "routine:f",
        ),
    ),
)
async def test_any_content_object_invalidates_empty_safe_validation(
    agent_site_database: AgentSiteDatabase,
    ddl: str,
    expected_category: str,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    _assert_empty_safe(await reconcile(database.settings))
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(ddl)
        inventory = await content_object_inventory(connection)
        assert any(item.category == expected_category for item in inventory)

    marker, validation = await validate(database.settings)
    _assert_empty_safe(marker)
    assert not validation.safe
    assert any("unexpected-empty-object" in item for item in validation.violations)


async def test_non_table_content_object_requires_hardening_and_stays_pending(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    _assert_empty_safe(await reconcile(database.settings))
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "CREATE VIEW content.requires_hardening AS SELECT 1 AS id"
        )

    with pytest.raises(BootstrapStateError, match="rejected non-empty content"):
        await reconcile(database.settings)
    _assert_pending(await status(database.settings), deployed=True)


async def test_empty_safe_transitions_to_first_and_repeated_hardened_table(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    _assert_empty_safe(await reconcile(database.settings))
    await _create_qualification_table(database)

    stale_marker, stale_validation = await validate(database.settings)
    _assert_empty_safe(stale_marker)
    assert not stale_validation.safe

    first = await reconcile(database.settings)
    _assert_hardened(first)
    first_marker, first_validation = await validate(database.settings)
    _assert_hardened(first_marker)
    assert first_validation.safe, first_validation.violations
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        with pytest.raises(asyncpg.CheckViolationError):
            await connection.execute(
                "UPDATE control.bootstrap_readiness "
                "SET foundation_privileges_validated = FALSE WHERE singleton"
            )

    repeated = await reconcile(database.settings)
    _assert_hardened(repeated)
    repeated_marker, repeated_validation = await validate(database.settings)
    _assert_hardened(repeated_marker)
    assert repeated_validation.safe, repeated_validation.violations


@pytest.mark.parametrize(
    "statement",
    (
        "ALTER VIEW content.qualification_item RENAME TO qualification_item_renamed",
        "DROP VIEW content.qualification_item",
    ),
)
async def test_hardened_inventory_remove_or_rename_fails_validation(
    agent_site_database: AgentSiteDatabase,
    statement: str,
) -> None:
    database = agent_site_database
    await _prepare_hardened_database(database)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(statement)

    marker, validation = await validate(database.settings)
    _assert_hardened(marker)
    assert not validation.safe
    assert "marker/content-object-inventory/state-mismatch" in validation.violations


async def test_empty_foundation_inventory_rename_fails_validation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    _assert_empty_safe(await reconcile(database.settings))
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        function_reference = await connection.fetchval(
            "SELECT format('%I.%I(%s)', namespace_.nspname, proc.proname, "
            "pg_catalog.pg_get_function_identity_arguments(proc.oid)) "
            "FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "WHERE namespace_.nspname = 'agentcow' ORDER BY proc.oid LIMIT 1"
        )
        assert function_reference is not None
        await connection.execute(
            f"ALTER FUNCTION {function_reference} RENAME TO evidence_renamed"
        )

    marker, validation = await validate(database.settings)
    _assert_empty_safe(marker)
    assert not validation.safe
    assert "marker/foundation-object-inventory/state-mismatch" in validation.violations


async def test_empty_failure_stays_pending_then_retries_safely(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    with pytest.raises(BootstrapStateError, match="injected failure"):
        await reconcile(database.settings, failure_point="before-marker")
    _assert_pending(await status(database.settings), deployed=True)
    pending_marker, pending_validation = await validate(database.settings)
    _assert_pending(pending_marker, deployed=True)
    assert not pending_validation.safe

    repaired = await reconcile(database.settings)
    _assert_empty_safe(repaired)
    marker, validation = await validate(database.settings)
    _assert_empty_safe(marker)
    assert validation.safe, validation.violations


async def test_empty_reviewer_role_and_public_overgrants_are_repaired(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    _assert_empty_safe(await reconcile(database.settings))

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        function_reference = await connection.fetchval(
            "SELECT format('%I.%I(%s)', namespace_.nspname, proc.proname, "
            "pg_catalog.pg_get_function_identity_arguments(proc.oid)) "
            "FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "WHERE namespace_.nspname = 'agentcow' ORDER BY proc.oid LIMIT 1"
        )
        assert function_reference is not None
        await connection.execute(
            f"GRANT EXECUTE ON FUNCTION {function_reference} TO slaif_reviewer"
        )
        await connection.execute("GRANT USAGE ON SCHEMA content TO PUBLIC")
        await connection.execute("GRANT CREATE ON SCHEMA content TO slaif_control")

    marker, validation = await validate(database.settings)
    _assert_empty_safe(marker)
    assert not validation.safe
    assert any("slaif_reviewer/execute" in item for item in validation.violations)
    assert "schema/content/public-authority" in validation.violations
    assert "schema/content/slaif_control/create" in validation.violations

    repaired = await reconcile(database.settings)
    _assert_empty_safe(repaired)
    marker, validation = await validate(database.settings)
    _assert_empty_safe(marker)
    assert validation.safe, validation.violations


async def test_cli_secret_file_empty_bootstrap_current_and_validate(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    database = agent_site_database
    locator = database.settings.resolved_owner_dsn().get_secret_value()
    secret_file = tmp_path / "owner-dsn"
    secret_file.write_text(locator + "\n", encoding="utf-8")
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SLAIF_BOOTSTRAP_")
    }
    environment.update(
        {
            "SLAIF_BOOTSTRAP_MODE": "production",
            "SLAIF_BOOTSTRAP_EXPECTED_DATABASE": database.name,
            "SLAIF_BOOTSTRAP_OWNER_DSN_FILE": str(secret_file),
        }
    )

    def invoke(command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "slaif_agent_site.bootstrap", command],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )

    upgraded = invoke("upgrade")
    assert upgraded.returncode == 0
    assert upgraded.stdout == "upgrade: OK\n"
    current = invoke("current")
    assert current.returncode == 0
    assert current.stdout == ("current: revision=006_001 state=PENDING safe=false\n")
    bootstrapped = invoke("bootstrap")
    assert bootstrapped.returncode == 0
    assert bootstrapped.stdout == (
        "bootstrap: OK revision=006_001 state=EMPTY_SAFE safe=true\n"
    )
    validated = invoke("validate")
    assert validated.returncode == 0
    assert validated.stdout == (
        "validate: OK revision=006_001 state=EMPTY_SAFE safe=true\n"
    )
    ready = invoke("current")
    assert ready.returncode == 0
    assert ready.stdout == ("current: revision=006_001 state=EMPTY_SAFE safe=true\n")
    output = "".join(
        process.stdout + process.stderr
        for process in (upgraded, current, bootstrapped, validated, ready)
    )
    assert locator not in output

    marker = await status(database.settings)
    _assert_empty_safe(marker)


async def test_full_runtime_reader_reviewer_and_service_privilege_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await _prepare_hardened_database(database)
    marker, product = await validate(database.settings)
    _assert_hardened(marker)
    assert product.safe, product.violations

    agent_pool = await database.role_pool("slaif_agent_runtime")
    editor_pool = await database.role_pool("slaif_editor_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    narrow_pools = [
        await database.role_pool(role)
        for role in ("slaif_control", "slaif_scheduler", "slaif_media", "slaif_gc")
    ]
    try:
        async with agent_pool.acquire() as connection:
            with pytest.raises(asyncpg.PostgresError):
                await connection.execute(
                    f"INSERT INTO {QUALIFICATION_TABLE} VALUES (10, 'no context')"
                )
            for internal in (QUALIFICATION_BASE, QUALIFICATION_CHANGES):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch(f"SELECT * FROM {internal}")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await deploy_cow_functions(AsyncpgExecutor(connection))

        agent_session = uuid.uuid4()
        async with asyncpg_cow_session(agent_pool, session_id=agent_session) as cow:
            await cow.execute(
                f"INSERT INTO {QUALIFICATION_TABLE} VALUES (10, 'agent workspace')"
            )
        editor_session = uuid.uuid4()
        async with asyncpg_cow_session(editor_pool, session_id=editor_session) as cow:
            await cow.execute(
                f"INSERT INTO {QUALIFICATION_TABLE} VALUES (11, 'editor workspace')"
            )

        for reader_pool in (public_pool, preview_pool):
            async with reader_pool.acquire() as reader:
                assert [
                    tuple(row)
                    for row in await reader.fetch(
                        f"SELECT id, title FROM {QUALIFICATION_TABLE} ORDER BY id"
                    )
                ] == [(1, "canonical")]
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await reader.execute(
                        f"INSERT INTO {QUALIFICATION_TABLE} VALUES (12, 'denied')"
                    )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await reader.fetch("SELECT * FROM control.bootstrap_readiness")

        with pytest.raises(asyncpg.PostgresError):
            async with asyncpg_cow_reviewer(agent_pool) as unauthorized:
                await unauthorized.operations(agent_session, schema="content")

        async with reviewer_pool.acquire() as reviewer_connection:
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await reviewer_connection.execute(
                    f"INSERT INTO {QUALIFICATION_TABLE} VALUES (13, 'denied')"
                )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await reviewer_connection.execute(
                    "UPDATE control.bootstrap_readiness SET safe = FALSE"
                )

        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            promoted = await reviewer.commit_session(agent_session, schema="content")
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            discarded = await reviewer.discard_session(editor_session, schema="content")
            assert not promoted.no_op
            assert not discarded.no_op

        async with public_pool.acquire() as reader:
            assert [
                tuple(row)
                for row in await reader.fetch(
                    f"SELECT id, title FROM {QUALIFICATION_TABLE} ORDER BY id"
                )
            ] == [(1, "canonical"), (10, "agent workspace")]

        for pool in narrow_pools:
            async with pool.acquire() as connection:
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch(f"SELECT * FROM {QUALIFICATION_TABLE}")
                with pytest.raises(asyncpg.PostgresError):
                    async with asyncpg_cow_reviewer(connection) as unauthorized:
                        await unauthorized.operations(uuid.uuid4(), schema="content")
    finally:
        for pool in reversed(narrow_pools):
            await pool.close()
        await preview_pool.close()
        await public_pool.close()
        await reviewer_pool.close()
        await editor_pool.close()
        await agent_pool.close()


@pytest.mark.parametrize("failure_point", ["after-harden", "before-marker"])
async def test_hardening_failure_rolls_back_and_retry_is_idempotent(
    agent_site_database: AgentSiteDatabase, failure_point: Any
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await _create_qualification_table(database)
    with pytest.raises(BootstrapStateError, match="injected failure"):
        await reconcile(database.settings, failure_point=failure_point)

    marker = await status(database.settings)
    _assert_pending(marker, deployed=True)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        state = await connection.fetchrow(
            "SELECT to_regclass('content.qualification_item'), "
            "to_regclass('content.qualification_item_base'), "
            "to_regclass('content.qualification_item_changes')"
        )
        assert state is not None
        assert state[0] is not None
        assert state[1] is None
        assert state[2] is None

    repaired = await reconcile(database.settings)
    _assert_hardened(repaired)
    repeated = await reconcile(database.settings)
    _assert_hardened(repeated)
    assert repeated.revision == repaired.revision

    marker, product = await validate(database.settings)
    _assert_hardened(marker)
    assert product.safe, product.violations


async def test_direct_and_inherited_overgrants_are_detected(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await _prepare_hardened_database(database)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            f"GRANT SELECT ON {QUALIFICATION_BASE} TO slaif_agent_runtime"
        )
        direct = await verify_database_privileges(
            connection, readiness_state=ReadinessState.HARDENED
        )
        assert not direct.safe
        assert any(
            "qualification_item_base/slaif_agent_runtime/effective-dml" in violation
            for violation in direct.violations
        )
        await connection.execute(
            f"REVOKE SELECT ON {QUALIFICATION_BASE} FROM slaif_agent_runtime"
        )

    excess_role = f"fixture_excess_{uuid.uuid4().hex[:10]}"
    try:
        await database.administrator.execute(
            f"CREATE ROLE {quote_identifier(excess_role)} NOLOGIN"
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as connection:
            await connection.execute(
                f"GRANT SELECT ON {QUALIFICATION_BASE} "
                f"TO {quote_identifier(excess_role)}"
            )
        await database.administrator.execute(
            f"GRANT {quote_identifier(excess_role)} TO slaif_agent_runtime"
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as connection:
            inherited = await verify_database_privileges(
                connection, readiness_state=ReadinessState.HARDENED
            )
            assert not inherited.safe
            assert (
                f"membership/slaif_agent_runtime/can-set-role:{excess_role}"
                in inherited.violations
            )
            assert any(
                "qualification_item_base/slaif_agent_runtime/effective-dml" in violation
                for violation in inherited.violations
            )
    finally:
        await database.administrator.execute(
            f"REVOKE {quote_identifier(excess_role)} FROM slaif_agent_runtime"
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as connection:
            await connection.execute(
                f"REVOKE SELECT ON {QUALIFICATION_BASE} "
                f"FROM {quote_identifier(excess_role)}"
            )
        await database.administrator.execute(
            f"DROP ROLE IF EXISTS {quote_identifier(excess_role)}"
        )


async def test_combined_login_and_foundation_relation_overgrants_are_detected(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await _prepare_hardened_database(database)
    agent_login = database.credentials["slaif_agent_runtime"][0]
    await database.administrator.execute(
        f"GRANT slaif_reviewer TO {quote_identifier(agent_login)}"
    )
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as connection:
            combined = await verify_database_privileges(
                connection, readiness_state=ReadinessState.HARDENED
            )
            assert not combined.safe
            assert any(
                violation.startswith(f"membership/{agent_login}/combined-roles:")
                for violation in combined.violations
            )

            foundation_relation = await connection.fetchval(
                "SELECT format('%I.%I', namespace_.nspname, class_.relname) "
                "FROM pg_catalog.pg_class class_ "
                "JOIN pg_catalog.pg_namespace namespace_ "
                "ON namespace_.oid = class_.relnamespace "
                "WHERE namespace_.nspname = 'agentcow' "
                "AND class_.relkind IN ('r', 'p') ORDER BY class_.relname LIMIT 1"
            )
            assert foundation_relation is not None
            await connection.execute(
                f"GRANT SELECT ON {foundation_relation} TO slaif_public_reader"
            )
            relation = await verify_database_privileges(
                connection, readiness_state=ReadinessState.HARDENED
            )
            assert not relation.safe
            assert any(
                "relation/agentcow." in violation
                and "/slaif_public_reader/effective-dml:select" in violation
                for violation in relation.violations
            )
            await connection.execute(
                f"REVOKE SELECT ON {foundation_relation} FROM slaif_public_reader"
            )
    finally:
        await database.administrator.execute(
            f"REVOKE slaif_reviewer FROM {quote_identifier(agent_login)}"
        )


async def test_cancelled_runtime_and_reviewer_transactions_release_clean_pool(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await _prepare_hardened_database(database)
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    mutation_finished = asyncio.Event()
    keep_open = asyncio.Event()

    async def runtime_mutation() -> None:
        async with asyncpg_cow_session(agent_pool, session_id=uuid.uuid4()) as cow:
            await cow.execute(
                f"INSERT INTO {QUALIFICATION_TABLE} VALUES (20, 'cancelled')"
            )
            mutation_finished.set()
            await keep_open.wait()

    reviewer_started = asyncio.Event()

    async def reviewer_wait() -> None:
        async with reviewer_pool.acquire() as connection:
            async with connection.transaction():
                reviewer_started.set()
                await connection.execute("SELECT pg_sleep(30)")

    try:
        runtime_task = asyncio.create_task(runtime_mutation())
        await asyncio.wait_for(mutation_finished.wait(), timeout=5)
        runtime_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await runtime_task

        async with agent_pool.acquire() as connection:
            assert not connection.is_in_transaction()
            with pytest.raises(asyncpg.PostgresError):
                await connection.execute(
                    f"INSERT INTO {QUALIFICATION_TABLE} VALUES (21, 'no context')"
                )
        async with asyncpg_cow_session(agent_pool, session_id=uuid.uuid4()) as cow:
            assert (
                await cow.execute(f"SELECT id FROM {QUALIFICATION_TABLE} WHERE id = 20")
                == []
            )

        reviewer_task = asyncio.create_task(reviewer_wait())
        await asyncio.wait_for(reviewer_started.wait(), timeout=5)
        reviewer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await reviewer_task
        async with reviewer_pool.acquire() as connection:
            assert not connection.is_in_transaction()
            assert await connection.fetchval("SELECT current_user::text") == (
                "slaif_reviewer"
            )
    finally:
        await reviewer_pool.close()
        await agent_pool.close()

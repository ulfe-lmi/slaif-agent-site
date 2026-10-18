"""Real PostgreSQL proof for the cache-outbox consumer (083/3).

Evidence for order R4/R7: the ``074_001`` round trip (upgrade from
``073_001``, downgrade back to the query-proven ``073_001`` state,
re-upgrade), the grant-surface delta vs the 083/1 baseline (exactly
one new table grant and exactly two new function EXECUTE grants, all
to ``slaif_review_worker``, nothing else), claim semantics (id order,
disjoint claims under concurrent open transactions, the
``OUTBOX_CLAIM_LIMIT_INVALID`` limit gate, the 25-attempt budget),
crash between claim and consume (re-claim with the incremented
attempt, processed exactly once in effect), consume idempotency (zero
rows on replay), corrupt payloads (terminal ``PAYLOAD_INVALID``,
never re-claimed), the ``SUBSUMED`` / ``REVISION_AHEAD`` terminal
states, and outbox/accept coherence (rows == successful terminal
accepts; the duplicate accept adds no row; a mid-reviewer-transaction
failure leaves no orphan row).

In-file (per the order's budget): the ``evaluate_outbox_row`` unit
matrix (every branch), the consumer loop gating pins (poll interval,
batch size, first-run-on-start), and the unit/SQL attempt-budget
equality pin.
"""

# ruff: noqa: E501 -- explicit fixture and SQL contracts

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr, ValidationError
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from slaif_agent_site.review_worker.config import (
    REVIEW_WORKER_OUTBOX_BATCH_SIZE,
    REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS,
    REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS,
    ReviewWorkerDatabaseMode,
    ReviewWorkerSettings,
)
from slaif_agent_site.review_worker.outbox_consumer import (
    PAYLOAD_INVALID,
    REVISION_AHEAD,
    SUBSUMED,
    OutboxOutcome,
    consume_outbox_round,
    evaluate_outbox_row,
    outbox_round_due,
)
from test_real_human_accept import (
    _age_heartbeat,
    _claim_accept,
    _dsn,
    _enqueue_accept,
    _freeze_workspace,
    _media_settings,
    _private_path,
    _restore_media_object,
    _seed_site,
    _worker_pool,
    _worker_settings,
)

_LONG_LIVED_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)
_SNAPSHOT_ID = str(UUID("11111111-1111-4111-8111-111111111111"))
_MEDIA_ID = str(UUID("22222222-2222-4222-8222-222222222222"))
_DIGEST = hashlib.sha256(b"cache-outbox-consumer-fixture-media").hexdigest()
_PUBLIC_KEY = f"public/sha256/{_DIGEST[:2]}/{_DIGEST[2:4]}/{_DIGEST}"
_MIGRATION_074_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "slaif_agent_site"
    / "db"
    / "alembic"
    / "versions"
    / "074_001_cache_outbox_consumer.py"
)


def _payload(
    *,
    snapshot_id: str = _SNAPSHOT_ID,
    digest: str = _DIGEST,
    base: int = 0,
    new: int = 1,
    media_id: str = _MEDIA_ID,
    public_key: str = _PUBLIC_KEY,
    empty_manifest: bool = False,
) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot_id,
        "digest": digest,
        "base_site_revision": base,
        "new_canonical_revision": new,
        "media_manifest": []
        if empty_manifest
        else [
            {
                "media_id": media_id,
                "digest": digest,
                "public_key": public_key,
            }
        ],
    }


async def _seed_site_row(owner: Any, key: str) -> UUID:
    return UUID(
        str(
            await owner.fetchval(
                "INSERT INTO control.site (site_key, display_name, default_locale,"
                " component_catalog_version)"
                " VALUES ($1, $2, 'en', 'catalog-v1') RETURNING id",
                key,
                f"Outbox {key.removeprefix('outbox-')}",
            )
        )
    )


async def _seed_outbox_row(
    owner: Any, site_id: UUID, workspace_id: UUID, payload: Any
) -> int:
    """Insert one outbox row; ``payload`` is a JSON document (any type)."""
    return int(
        await owner.fetchval(
            "INSERT INTO control.cache_outbox (site_id, workspace_id, event_kind,"
            " payload) VALUES ($1, $2, 'WORKSPACE_ACCEPTED', $3::jsonb)"
            " RETURNING id",
            site_id,
            workspace_id,
            json.dumps(payload, sort_keys=True, separators=(",", ":")),
        )
    )


async def _outbox_state(owner: Any, outbox_id: int) -> tuple[Any, ...] | None:
    row = await owner.fetchrow(
        "SELECT attempt_count, last_attempt_at, consumed_at, last_error,"
        " event_kind, payload FROM control.cache_outbox WHERE id = $1",
        outbox_id,
    )
    return tuple(row) if row is not None else None


async def _cache_outbox_surface(owner: Any) -> tuple[Any, ...]:
    """Query-proven state of the outbox object (columns, functions, grants)."""
    columns = await owner.fetch(
        "SELECT column_name, is_nullable, column_default, data_type"
        " FROM information_schema.columns"
        " WHERE table_schema = 'control' AND table_name = 'cache_outbox'"
        " ORDER BY ordinal_position"
    )
    functions = await owner.fetch(
        "SELECT pg_get_function_arguments(p.oid) AS arguments, p.prosecdef,"
        " p.proconfig, r.rolname AS owner"
        " FROM pg_proc p"
        " JOIN pg_namespace n ON n.oid = p.pronamespace"
        " JOIN pg_roles r ON r.oid = p.proowner"
        " WHERE n.nspname = 'control' AND p.proname IN"
        " ('slaif_cache_outbox_claim', 'slaif_cache_outbox_consume')"
        " ORDER BY arguments"
    )
    table_grants = await owner.fetch(
        "SELECT r.rolname, a.privilege_type"
        " FROM pg_class c"
        " JOIN pg_namespace n ON n.oid = c.relnamespace"
        " JOIN LATERAL aclexplode(c.relacl) a ON a.grantee IS NOT NULL"
        " JOIN pg_roles r ON r.oid = a.grantee"
        " WHERE n.nspname = 'control' AND c.relname = 'cache_outbox'"
        " ORDER BY 1, 2"
    )
    function_grants = await owner.fetch(
        "SELECT r.rolname, a.privilege_type"
        " FROM pg_proc p"
        " JOIN pg_namespace n ON n.oid = p.pronamespace"
        " JOIN LATERAL aclexplode(p.proacl) a ON a.grantee IS NOT NULL"
        " JOIN pg_roles r ON r.oid = a.grantee"
        " WHERE n.nspname = 'control' AND p.proname IN"
        " ('slaif_cache_outbox_claim', 'slaif_cache_outbox_consume')"
        " ORDER BY 1, 2"
    )
    return (
        tuple(columns),
        tuple(functions),
        tuple(table_grants),
        tuple(function_grants),
    )


async def _grant_surface_snapshot(owner: Any) -> frozenset[str]:
    """The exact grant/membership surface for the product roles."""

    roles = list(_LONG_LIVED_ROLES)
    tables = await owner.fetch(
        "SELECT r.rolname, n.nspname || '.' || c.relname AS relation, a.privilege_type"
        " FROM pg_class c"
        " JOIN pg_namespace n ON n.oid = c.relnamespace"
        " JOIN LATERAL aclexplode(c.relacl) a ON a.grantee IS NOT NULL"
        " JOIN pg_roles r ON r.oid = a.grantee"
        " WHERE c.relkind IN ('r', 'p', 'S')"
        " AND n.nspname IN ('control', 'audit', 'content')"
        " AND r.rolname = ANY($1)"
        " ORDER BY 1, 2, 3",
        roles,
    )
    functions = await owner.fetch(
        "SELECT r.rolname,"
        " n.nspname || '.' || p.proname || '(' || pg_get_function_arguments(p.oid)"
        " || ')' AS signature, a.privilege_type"
        " FROM pg_proc p"
        " JOIN pg_namespace n ON n.oid = p.pronamespace"
        " JOIN LATERAL aclexplode(p.proacl) a ON a.grantee IS NOT NULL"
        " JOIN pg_roles r ON r.oid = a.grantee"
        " WHERE n.nspname IN ('control', 'audit')"
        " AND r.rolname = ANY($1)"
        " ORDER BY 1, 2",
        roles,
    )
    schemas = await owner.fetch(
        "SELECT r.rolname, n.nspname, a.privilege_type"
        " FROM pg_namespace n"
        " JOIN LATERAL aclexplode(n.nspacl) a ON a.grantee IS NOT NULL"
        " JOIN pg_roles r ON r.oid = a.grantee"
        " WHERE n.nspname IN ('control', 'audit', 'content')"
        " AND r.rolname = ANY($1)"
        " ORDER BY 1, 2, 3",
        roles,
    )
    memberships = await owner.fetch(
        "SELECT r.rolname AS member, m.rolname AS role, am.admin_option"
        " FROM pg_auth_members am"
        " JOIN pg_roles r ON r.oid = am.member"
        " JOIN pg_roles m ON m.oid = am.roleid"
        " WHERE r.rolname = ANY($1) OR m.rolname = ANY($1)"
        " ORDER BY 1, 2",
        roles,
    )
    entries: set[str] = set()
    for row in tables:
        entries.add(f"table:{row['rolname']}:{row['relation']}:{row['privilege_type']}")
    for row in functions:
        entries.add(
            f"function:{row['rolname']}:{row['signature']}:{row['privilege_type']}"
        )
    for row in schemas:
        entries.add(f"schema:{row['rolname']}:{row['nspname']}:{row['privilege_type']}")
    for row in memberships:
        entries.add(
            f"membership:{row['member']}->{row['role']}:admin={row['admin_option']}"
        )
    return frozenset(entries)


async def _worker_connection(database: AgentSiteDatabase) -> asyncpg.Connection[Any]:
    """One direct connection under the narrow worker credential (SET ROLE)."""

    login, password = database.credentials["slaif_review_worker"]
    connection = await asyncpg.connect(
        dsn=_dsn(database, login, password),
        server_settings={"application_name": "outbox-integration-worker"},
    )
    await connection.execute("SET ROLE slaif_review_worker")
    return connection


@pytest.mark.asyncio
async def test_074_001_round_trip_proves_073_001_state(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R1.5/R7.1: up from 073_001, down to the proven 073_001 state, re-up."""

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    await run_migration(
        dsn, expected_database=database.name, operation="upgrade", revision="073_001"
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "073_001"
        )
        baseline = await _cache_outbox_surface(owner)
        # The 074_001 objects do not exist at the baseline.
        assert baseline[1] == () and baseline[3] == ()

    await run_migration(
        dsn, expected_database=database.name, operation="upgrade", revision="head"
    )
    await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "074_001"
        )
        columns, functions, table_grants, function_grants = await _cache_outbox_surface(
            owner
        )
    upgraded = (columns, functions, table_grants, function_grants)
    # The four new columns, exactly (names + nullability + defaults).
    assert [
        (str(row[0]), str(row[1]), row[2])
        for row in columns
        if str(row[0])
        in {
            "attempt_count",
            "last_attempt_at",
            "consumed_at",
            "last_error",
        }
    ] == [
        ("attempt_count", "NO", "0"),
        ("last_attempt_at", "YES", None),
        ("consumed_at", "YES", None),
        ("last_error", "YES", None),
    ]
    # Both functions: SECURITY DEFINER, search_path pinned, owned by
    # slaif_owner, with the exact grant pins.
    assert len(functions) == 2
    for row in functions:
        assert row["prosecdef"] is True
        assert "search_path=pg_catalog" in list(row["proconfig"])
        assert row["owner"] == "slaif_owner"
    table_grant_pairs = {(str(row[0]), str(row[1])) for row in table_grants}
    assert ("slaif_review_worker", "UPDATE") in table_grant_pairs
    assert ("slaif_review_worker", "INSERT") in table_grant_pairs
    assert ("slaif_review_worker", "SELECT") in table_grant_pairs
    # Exact function-grant pin: only the owner (implicit) and
    # slaif_review_worker, one EXECUTE per function for the worker.
    assert {str(row[1]) for row in function_grants} == {"EXECUTE"}
    assert {str(row[0]) for row in function_grants} == {
        "slaif_owner",
        "slaif_review_worker",
    }
    assert (
        sum(1 for row in function_grants if str(row[0]) == "slaif_review_worker") == 2
    )

    # Downgrade to 073_001: the query-proven state is byte-identical to
    # the pre-upgrade baseline (columns absent, functions absent, grants
    # absent, the 083/1-era grants intact).
    await run_migration(
        dsn, expected_database=database.name, operation="downgrade", revision="073_001"
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "073_001"
        )
        downgraded = await _cache_outbox_surface(owner)
    assert downgraded == baseline

    # Re-upgrade: the head state is restored exactly.
    await run_migration(
        dsn, expected_database=database.name, operation="upgrade", revision="head"
    )
    await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "074_001"
        )
        restored = await _cache_outbox_surface(owner)
    assert restored == upgraded


@pytest.mark.asyncio
async def test_grant_surface_delta_vs_083_1_baseline(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4/R7.1: exactly one new table grant + two new EXECUTE grants."""

    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    # The exact increment delta: the migration-applied state at the
    # 073_001 head (the 083/1 baseline) vs the migration-applied state at
    # the 074_001 head. Both sides are pre-reconcile by construction: the
    # reconcile is head-gated (it cannot run below the current head), so
    # this isolates precisely what 074_001 changed; the registry
    # re-application at the head is separately pinned (the validator
    # inside every reconcile + the 083/1 grant-surface test).
    await run_migration(
        dsn, expected_database=database.name, operation="upgrade", revision="073_001"
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "073_001"
        )
        baseline = await _grant_surface_snapshot(owner)

    await run_migration(
        dsn, expected_database=database.name, operation="upgrade", revision="head"
    )
    async with owner_connection(dsn, expected_database=database.name) as owner:
        assert (
            await owner.fetchval("SELECT version_num FROM control.alembic_version")
            == "074_001"
        )
        current = await _grant_surface_snapshot(owner)

    removed = baseline - current
    added = current - baseline
    assert removed == frozenset()
    assert added == frozenset(
        {
            "table:slaif_review_worker:control.cache_outbox:UPDATE",
            "function:slaif_review_worker:control.slaif_cache_outbox_claim(p_limit integer):EXECUTE",
            "function:slaif_review_worker:control.slaif_cache_outbox_consume(p_id bigint, p_error text):EXECUTE",
        }
    )


@pytest.mark.asyncio
async def test_claim_id_order_disjoint_concurrent_and_limit_gate(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4.1/R7.1: id order, SKIP LOCKED disjointness, limit gate."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    dsn = database.settings.resolved_owner_dsn()
    async with owner_connection(dsn, expected_database=database.name) as owner:
        site_id = await _seed_site_row(owner, "outbox-claim")
        row_ids = [
            await _seed_outbox_row(owner, site_id, uuid4(), _payload(new=1 + i))
            for i in range(5)
        ]
    pool = await _worker_pool(database)
    try:
        # Id order + the limit: the two lowest ids, claimed in order.
        async with pool.acquire() as connection:
            first = await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)", 2
            )
        assert [int(row["id"]) for row in first] == [row_ids[0], row_ids[1]]
        assert [int(row["attempt_count"]) for row in first] == [1, 1]

        # Two concurrent claim calls with open transactions: A claims
        # first and HOLDS the locks; B's claim must skip A's rows
        # (SKIP LOCKED) — disjoint, non-empty, union = the pending set.
        rows_a: list[list[Any]] = []
        rows_b: list[list[Any]] = []
        a_claimed = asyncio.Event()
        b_claimed = asyncio.Event()

        async def claim_a() -> None:
            async with pool.acquire() as connection:
                async with connection.transaction():
                    rows_a.append(
                        list(
                            await connection.fetch(
                                "SELECT * FROM control.slaif_cache_outbox_claim($1)",
                                3,
                            )
                        )
                    )
                    a_claimed.set()
                    await asyncio.wait_for(b_claimed.wait(), timeout=10)

        async def claim_b() -> None:
            async with pool.acquire() as connection:
                await a_claimed.wait()
                async with connection.transaction():
                    rows_b.append(
                        list(
                            await connection.fetch(
                                "SELECT * FROM control.slaif_cache_outbox_claim($1)",
                                5,
                            )
                        )
                    )
                    b_claimed.set()

        await asyncio.gather(claim_a(), claim_b())
        ids_a = [int(row["id"]) for row in rows_a[0]]
        ids_b = [int(row["id"]) for row in rows_b[0]]
        assert ids_a == [row_ids[0], row_ids[1], row_ids[2]]
        assert ids_b == [row_ids[3], row_ids[4]]
        assert set(ids_a).isdisjoint(ids_b)
        assert sorted(ids_a + ids_b) == sorted(row_ids)
        # Each row was claimed exactly once by the concurrent pair; rows
        # 0/1 carry the earlier single claim (attempt 2).
        async with owner_connection(dsn, expected_database=database.name) as owner:
            attempts = {
                int(row["id"]): int(row["attempt_count"])
                for row in await owner.fetch(
                    "SELECT id, attempt_count FROM control.cache_outbox ORDER BY id"
                )
            }
        assert attempts == {
            row_ids[0]: 2,
            row_ids[1]: 2,
            row_ids[2]: 1,
            row_ids[3]: 1,
            row_ids[4]: 1,
        }

        # The limit gate: outside 1..64 -> the stable 22023 code.
        for bad_limit in (0, 65, None):
            with pytest.raises(asyncpg.PostgresError) as excinfo:
                async with pool.acquire() as connection:
                    await connection.fetchval(
                        "SELECT control.slaif_cache_outbox_claim($1)", bad_limit
                    )
            assert excinfo.value.sqlstate == "22023"
            assert "OUTBOX_CLAIM_LIMIT_INVALID" in str(excinfo.value)
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_crash_between_claim_and_consume_processed_exactly_once(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4.2/R7.1: claim commits the attempt; re-claim; one consumed_at."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    dsn = database.settings.resolved_owner_dsn()
    async with owner_connection(dsn, expected_database=database.name) as owner:
        site_id = await _seed_site_row(owner, "outbox-crash")
        row_id = await _seed_outbox_row(owner, site_id, uuid4(), _payload())
    pool = await _worker_pool(database)
    try:
        # Claim 1: the attempt increment commits; then the process dies
        # (no consume).
        async with pool.acquire() as connection:
            claimed = await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)", 1
            )
        assert [int(row["id"]) for row in claimed] == [row_id]
        assert int(claimed[0]["attempt_count"]) == 1
        async with owner_connection(dsn, expected_database=database.name) as owner:
            state = await _outbox_state(owner, row_id)
        assert state is not None
        assert state[0] == 1 and state[2] is None  # attempt 1, unconsumed

        # Re-claim after the crash: same row, attempt incremented.
        async with pool.acquire() as connection:
            reclaimed = await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)", 1
            )
        assert [int(row["id"]) for row in reclaimed] == [row_id]
        assert int(reclaimed[0]["attempt_count"]) == 2

        # The eventual consume: one terminal, last_error NULL.
        async with pool.acquire() as connection:
            consumed = await connection.fetch(
                "SELECT control.slaif_cache_outbox_consume($1, $2)",
                row_id,
                None,
            )
        assert [int(row[0]) for row in consumed] == [row_id]
        async with owner_connection(dsn, expected_database=database.name) as owner:
            state = await _outbox_state(owner, row_id)
            terminals = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
                " WHERE consumed_at IS NOT NULL"
            )
        assert state is not None
        assert state[0] == 2
        assert state[2] is not None
        assert state[3] is None
        assert terminals == 1
        # A consumed row is never claimed again.
        async with pool.acquire() as connection:
            again = await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)", 64
            )
        assert [int(row["id"]) for row in again] == []
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_consume_idempotent_replay_changes_nothing(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4.3: a second consume of the same id returns 0 rows."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    dsn = database.settings.resolved_owner_dsn()
    async with owner_connection(dsn, expected_database=database.name) as owner:
        site_id = await _seed_site_row(owner, "outbox-idem")
        row_id = await _seed_outbox_row(
            owner, site_id, uuid4(), _payload(new=5, base=4)
        )
        await owner.execute(
            "UPDATE control.site SET canonical_revision = 7 WHERE id = $1", site_id
        )
    pool = await _worker_pool(database)
    try:
        async with pool.acquire() as connection:
            await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)", 1
            )
            first = await connection.fetch(
                "SELECT control.slaif_cache_outbox_consume($1, $2)",
                row_id,
                SUBSUMED,
            )
        assert [int(row[0]) for row in first] == [row_id]
        async with owner_connection(dsn, expected_database=database.name) as owner:
            before = await _outbox_state(owner, row_id)
        # Replay: 0 rows, and NOTHING changes (not even last_error).
        async with pool.acquire() as connection:
            replay = await connection.fetch(
                "SELECT control.slaif_cache_outbox_consume($1, $2)",
                row_id,
                PAYLOAD_INVALID,
            )
        assert replay == []
        async with owner_connection(dsn, expected_database=database.name) as owner:
            after = await _outbox_state(owner, row_id)
        assert after == before
        assert after is not None
        assert after[3] == SUBSUMED
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_corrupt_payloads_terminal_dead_letter(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4.4: every shape failure is a terminal PAYLOAD_INVALID."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    dsn = database.settings.resolved_owner_dsn()
    settings = _worker_settings(database)
    pool = await _worker_pool(database)

    def without_key(key: str) -> dict[str, Any]:
        payload = _payload()
        del payload[key]
        return payload

    def with_extra() -> dict[str, Any]:
        return {**_payload(), "surprise": 1}

    def with_manifest(entries: list[Any]) -> dict[str, Any]:
        payload = _payload()
        payload["media_manifest"] = entries
        return payload

    variants: list[tuple[str, Any]] = [
        ("non-object array", [1, 2, 3]),
        ("non-object string", "WORKSPACE_ACCEPTED"),
        ("non-object number", 42),
        ("non-object boolean", True),
        ("non-object null", None),
        ("missing snapshot_id", without_key("snapshot_id")),
        ("missing digest", without_key("digest")),
        ("missing base_site_revision", without_key("base_site_revision")),
        ("missing new_canonical_revision", without_key("new_canonical_revision")),
        ("missing media_manifest", without_key("media_manifest")),
        ("extra key", with_extra()),
        ("empty object", {}),
        ("snapshot_id not a uuid", _payload(snapshot_id="not-a-uuid")),
        (
            "snapshot_id unhyphenated",
            _payload(snapshot_id="11111111111141118111111111111111"),
        ),
        ("snapshot_id number", _payload(snapshot_id=1111)),  # type: ignore[arg-type]
        ("digest short", _payload(digest="ab")),
        ("digest non-hex", _payload(digest="z" * 64)),
        ("digest uppercase", _payload(digest="AB" * 32)),
        ("base_site_revision boolean", _payload(base=True)),
        ("base_site_revision float", _payload(base=1.5)),  # type: ignore[arg-type]
        ("base_site_revision string", _payload(base="1")),  # type: ignore[arg-type]
        ("new_canonical_revision boolean", _payload(new=True)),
        ("new_canonical_revision float", _payload(new=2.0)),  # type: ignore[arg-type]
        ("new_canonical_revision string", _payload(new="1")),  # type: ignore[arg-type]
        ("media_manifest string", {**_payload(), "media_manifest": "not-a-list"}),
        ("media_manifest dict", {**_payload(), "media_manifest": {"a": 1}}),
        (
            "manifest entry missing key",
            with_manifest([{"digest": _DIGEST, "public_key": _PUBLIC_KEY}]),
        ),
        (
            "manifest entry extra key",
            with_manifest(
                [
                    {
                        "media_id": _MEDIA_ID,
                        "digest": _DIGEST,
                        "public_key": _PUBLIC_KEY,
                        "extra": 1,
                    }
                ]
            ),
        ),
        ("manifest entry not a dict", with_manifest([1])),
        (
            "manifest entry bad media_id",
            with_manifest(
                [{"media_id": "nope", "digest": _DIGEST, "public_key": _PUBLIC_KEY}]
            ),
        ),
        (
            "manifest entry bad digest",
            with_manifest(
                [{"media_id": _MEDIA_ID, "digest": "z" * 64, "public_key": _PUBLIC_KEY}]
            ),
        ),
        (
            "manifest entry bad public_key",
            with_manifest(
                [
                    {
                        "media_id": _MEDIA_ID,
                        "digest": _DIGEST,
                        "public_key": f"public/sha256/{_DIGEST}",
                    }
                ]
            ),
        ),
    ]
    try:
        for index, (name, payload) in enumerate(variants):
            async with owner_connection(dsn, expected_database=database.name) as owner:
                site_id = await _seed_site_row(owner, f"outbox-corrupt-{index}")
                row_id = await _seed_outbox_row(owner, site_id, uuid4(), payload)
            processed = await consume_outbox_round(pool, settings)
            assert processed == 1, name
            async with owner_connection(dsn, expected_database=database.name) as owner:
                state = await _outbox_state(owner, row_id)
            assert state is not None, name
            assert state[2] is not None, name  # consumed_at set
            assert state[3] == PAYLOAD_INVALID, name
            # Never re-claimed: the claim of everything pending is empty.
            async with pool.acquire() as connection:
                remaining = await connection.fetch(
                    "SELECT * FROM control.slaif_cache_outbox_claim($1)", 64
                )
            assert [int(row["id"]) for row in remaining] == [], name
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_revision_relation_terminal_states(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4.5/R4.6: CONSUMED / SUBSUMED / REVISION_AHEAD, each exactly once."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    dsn = database.settings.resolved_owner_dsn()
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    try:
        for name, new_revision, expected_error in (
            ("consumed", 7, None),
            ("subsumed", 5, SUBSUMED),
            ("revision-ahead", 9, REVISION_AHEAD),
        ):
            async with owner_connection(dsn, expected_database=database.name) as owner:
                site_id = await _seed_site_row(owner, f"outbox-{name}")
                await owner.execute(
                    "UPDATE control.site SET canonical_revision = 7 WHERE id = $1",
                    site_id,
                )
                row_id = await _seed_outbox_row(
                    owner, site_id, uuid4(), _payload(base=6, new=new_revision)
                )
            processed = await consume_outbox_round(pool, settings)
            assert processed == 1, name
            async with owner_connection(dsn, expected_database=database.name) as owner:
                state = await _outbox_state(owner, row_id)
            assert state is not None
            assert state[2] is not None
            assert state[3] == expected_error, name
            async with pool.acquire() as connection:
                remaining = await connection.fetch(
                    "SELECT * FROM control.slaif_cache_outbox_claim($1)", 64
                )
            assert [int(row["id"]) for row in remaining] == [], name
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_attempt_budget_abandons_row_at_25(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4.7/R7.1: 25 claim cycles; the 26th claim is empty (abandoned)."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    dsn = database.settings.resolved_owner_dsn()
    async with owner_connection(dsn, expected_database=database.name) as owner:
        site_id = await _seed_site_row(owner, "outbox-budget")
        row_id = await _seed_outbox_row(owner, site_id, uuid4(), _payload())
    pool = await _worker_pool(database)
    try:
        for attempt in range(1, REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS + 1):
            async with pool.acquire() as connection:
                rows = await connection.fetch(
                    "SELECT * FROM control.slaif_cache_outbox_claim($1)", 1
                )
            assert [int(row["id"]) for row in rows] == [row_id], attempt
            assert int(rows[0]["attempt_count"]) == attempt, attempt
        # Attempt 26: the budget is exhausted — the row is abandoned.
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)", 64
            )
        assert rows == []
        async with owner_connection(dsn, expected_database=database.name) as owner:
            state = await _outbox_state(owner, row_id)
        assert state is not None
        assert state[0] == REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS
        assert state[1] is not None  # last_attempt_at
        assert state[2] is None  # never consumed
        assert state[3] is None  # no stable error (operator-visible abandon)
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_outbox_accept_coherence(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R4.8: rows == successful accepts; duplicate/failure add no row."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    settings = _worker_settings(database)
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    dsn = database.settings.resolved_owner_dsn()
    try:
        await _freeze_workspace(database, ids, pool)
        rows = await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        digest = ids["media_digest"]

        # Mid-reviewer-transaction failure (the 083/1 fault pattern):
        # the private bytes are missing -> ROLLED_BACK, and NO orphan
        # outbox row exists.
        job = await _claim_accept(database, "outbox-coherence-fault")
        assert str(job["id"]) == str(job_id)
        _private_path(media_root, digest).unlink()
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "ROLLED_BACK"
        async with owner_connection(dsn, expected_database=database.name) as owner:
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                ids["site_id"],
            )
        assert outbox_count == 0
        assert revision == 0

        # The healed retry succeeds: exactly one successful terminal
        # accept -> exactly one outbox row. (The retryable failure left
        # the job CLAIMED; the stale-claim gate requires the aged
        # heartbeat, the 083/1 pattern.)
        _restore_media_object(media_root)
        await _age_heartbeat(database, job_id)
        job = await _claim_accept(database, "outbox-coherence-retry")
        assert job["attempt_count"] == 2
        result = await run_accept_job(pool, settings, job, media=boundary)
        assert result.status == "SUCCEEDED", result.error
        async with owner_connection(dsn, expected_database=database.name) as owner:
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            outbox_rows = await owner.fetch(
                "SELECT workspace_id FROM control.cache_outbox ORDER BY id"
            )
        assert outbox_count == 1
        assert [str(row["workspace_id"]) for row in outbox_rows] == [
            str(ids["workspace_id"])
        ]

        # Duplicate accept: the workspace is terminal ACCEPTED -> the
        # stable P0002 code and NO second row.
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            await _enqueue_accept(database, ids["workspace_id"], ids["delegator_id"])
        assert excinfo.value.sqlstate == "P0002"
        assert "WORKSPACE_NOT_IN_REVIEW" in str(excinfo.value)
        async with owner_connection(dsn, expected_database=database.name) as owner:
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
        assert outbox_count == 1
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.parametrize(
    ("payload", "current_revision", "expected_outcome", "expected_code"),
    [
        # CONSUMED: valid payload, new == current (incl. empty manifest).
        (_payload(new=3), 3, OutboxOutcome.CONSUMED, None),
        (_payload(new=3, empty_manifest=True), 3, OutboxOutcome.CONSUMED, None),
        # SUBSUMED: valid payload, new < current.
        (_payload(base=5, new=6), 7, OutboxOutcome.SUBSUMED, None),
        (_payload(new=1), 2, OutboxOutcome.SUBSUMED, None),
        # REVISION_AHEAD: valid payload, new > current.
        (_payload(new=2), 1, OutboxOutcome.DEAD_LETTER, REVISION_AHEAD),
        (_payload(new=100), 99, OutboxOutcome.DEAD_LETTER, REVISION_AHEAD),
        # PAYLOAD_INVALID: not a JSON object at all.
        (None, 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        ("a json string", 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        ([1, 2, 3], 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (42, 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (True, 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        ({}, 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        # PAYLOAD_INVALID: a missing key (each of the five).
        (
            {
                "digest": _DIGEST,
                "base_site_revision": 0,
                "new_canonical_revision": 1,
                "media_manifest": [],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                "snapshot_id": _SNAPSHOT_ID,
                "base_site_revision": 0,
                "new_canonical_revision": 1,
                "media_manifest": [],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                "snapshot_id": _SNAPSHOT_ID,
                "digest": _DIGEST,
                "new_canonical_revision": 1,
                "media_manifest": [],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                "snapshot_id": _SNAPSHOT_ID,
                "digest": _DIGEST,
                "base_site_revision": 0,
                "media_manifest": [],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                "snapshot_id": _SNAPSHOT_ID,
                "digest": _DIGEST,
                "base_site_revision": 0,
                "new_canonical_revision": 1,
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        # PAYLOAD_INVALID: an extra key.
        ({**_payload(), "surprise": 1}, 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        # PAYLOAD_INVALID: wrong field types.
        (_payload(snapshot_id=1111), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),  # type: ignore[arg-type]
        (
            _payload(snapshot_id="not-a-uuid"),
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            _payload(snapshot_id="11111111111141118111111111111111"),
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (_payload(digest="ab"), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (_payload(digest="z" * 64), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (_payload(digest="AB" * 32), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (_payload(base=True), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (_payload(base=1.5), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),  # type: ignore[arg-type]
        (_payload(base="1"), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),  # type: ignore[arg-type]
        (_payload(new=True), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),
        (_payload(new=2.0), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),  # type: ignore[arg-type]
        (_payload(new="1"), 1, OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID),  # type: ignore[arg-type]
        (
            {**_payload(), "media_manifest": "not-a-list"},
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {**_payload(), "media_manifest": {"a": 1}},
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        # PAYLOAD_INVALID: malformed media_manifest entries.
        (
            {
                **_payload(),
                "media_manifest": [{"digest": _DIGEST, "public_key": _PUBLIC_KEY}],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                **_payload(),
                "media_manifest": [
                    {
                        "media_id": _MEDIA_ID,
                        "digest": _DIGEST,
                        "public_key": _PUBLIC_KEY,
                        "extra": 1,
                    }
                ],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {**_payload(), "media_manifest": [1]},
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                **_payload(),
                "media_manifest": [
                    {"media_id": "nope", "digest": _DIGEST, "public_key": _PUBLIC_KEY}
                ],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                **_payload(),
                "media_manifest": [
                    {
                        "media_id": _MEDIA_ID,
                        "digest": "z" * 64,
                        "public_key": _PUBLIC_KEY,
                    }
                ],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
        (
            {
                **_payload(),
                "media_manifest": [
                    {
                        "media_id": _MEDIA_ID,
                        "digest": _DIGEST,
                        "public_key": f"public/sha256/{_DIGEST}",
                    }
                ],
            },
            1,
            OutboxOutcome.DEAD_LETTER,
            PAYLOAD_INVALID,
        ),
    ],
)
def test_evaluate_outbox_row_matrix(
    payload: Any,
    current_revision: int,
    expected_outcome: OutboxOutcome,
    expected_code: str | None,
) -> None:
    """R7.1: the full branch matrix of the pure evaluation."""
    result = evaluate_outbox_row(payload, current_revision)
    assert result.outcome is expected_outcome
    assert result.code == expected_code


def test_outbox_round_due_first_run_and_interval() -> None:
    """R7.1: the gating pins (first run on start, then the interval)."""
    assert outbox_round_due(None, 100.0, 5.0) is True
    assert outbox_round_due(100.0, 104.999, 5.0) is False
    assert outbox_round_due(100.0, 105.0, 5.0) is True
    assert outbox_round_due(99.0, 104.9, 5.0) is True
    assert outbox_round_due(100.0, 100.0, 5.0) is False


def test_outbox_max_attempts_constant_matches_sql_budget() -> None:
    """R7.1: the unit constant equals the SQL-side named constant."""
    source = _MIGRATION_074_PATH.read_text(encoding="utf-8")
    match = re.search(r"max_attempts\s+constant\s+integer\s*:=\s*(\d+)\s*;", source)
    assert match is not None
    assert int(match.group(1)) == REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS
    assert REVIEW_WORKER_OUTBOX_MAX_ATTEMPTS == 25


@pytest.mark.asyncio
async def test_consumer_settings_defaults_and_bounds(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R7.1: the settings defaults carry the documented constants."""

    database = agent_site_database
    settings = _worker_settings(database)
    assert (
        settings.outbox_poll_interval_seconds
        == REVIEW_WORKER_OUTBOX_POLL_INTERVAL_SECONDS
        == 5.0
    )
    assert settings.outbox_batch_size == REVIEW_WORKER_OUTBOX_BATCH_SIZE == 8
    login, password = database.credentials["slaif_review_worker"]

    def _settings(**overrides: Any) -> ReviewWorkerSettings:
        base: dict[str, Any] = {
            "mode": ReviewWorkerDatabaseMode.TEST,
            "dsn": SecretStr(_dsn(database, login, password)),
            "dsn_file": None,
            "expected_database": database.name,
            "expected_login": login,
        }
        base.update(overrides)
        return ReviewWorkerSettings(**base)

    assert (
        _settings(outbox_poll_interval_seconds=0.5).outbox_poll_interval_seconds == 0.5
    )
    assert _settings(outbox_batch_size=16).outbox_batch_size == 16
    with pytest.raises(ValidationError):
        _settings(outbox_poll_interval_seconds=61.0)
    with pytest.raises(ValidationError):
        _settings(outbox_poll_interval_seconds=0.05)
    with pytest.raises(ValidationError):
        _settings(outbox_batch_size=65)
    with pytest.raises(ValidationError):
        _settings(outbox_batch_size=0)

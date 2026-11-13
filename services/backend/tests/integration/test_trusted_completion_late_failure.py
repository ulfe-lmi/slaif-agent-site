"""083/11-a C5 + P6: late failure, cancellation, connection loss, retention.

All three C5 cases run through the REAL agent HTTP surface: the actual
FastAPI app, the actual runtime COW pool, the server-selected operation
UUIDs, and the actual Idempotency-Key semantics.  The controlled failure
is placed strictly AFTER the real 078 completion journal INSERT and
INSIDE the same uncommitted mutation transaction, by a trusted test-only
AFTER INSERT trigger on ``audit.mutation_completion`` (owner objects only;
installed and removed inside each test; no product surface, no grant
change, no schema change beyond the temporary trigger):

* the trigger reaches an advisory-lock rendezvous only after the journal
  row INSERT has executed, so a parked request is exactly "journal
  written, not committed";
* the test-side owner connection holds the rendezvous lock, observes the
  pending request in ``pg_locks`` (real state, bounded wait, no blind
  sleep), then selects the failure mode:

  - ``fail``: release the lock, the trigger raises ``P0001`` inside the
    still-uncommitted mutation transaction; the real request fails with
    503 ``SERVICE_UNAVAILABLE`` and every state (COW pending,
    idempotency reservation, family audit row, journal row) rolls back;
  - ``cancel``: cancel the request's asyncio task while the trigger is
    parked; the in-flight statement is cancelled and the same
    uncommitted transaction aborts;
  - ``kill``: the hold-mode trigger stays parked with the journal
    INSERT executed and uncommitted, and the disposable fixture
    administrator connection terminates ONLY the exact matched runtime
    backend (``pg_terminate_backend`` on the verified pid) - no product
    role policy is changed.

* in every case the durable post-rollback state is compared field-for-
  field (owner) with the pre-request snapshot, and the SAME idempotency
  key retried through the SAME real runtime app/pool completes exactly
  once.  That proves the pool is usable afterwards with the correct
  context and that the rolled-back reservation retains nothing.

P6 then proves the new completion facts survive the REAL review worker
lifecycle: a 078-era completed operation with genuine pending COW work
replays while the workspace is still ACTIVE and eligible, then a real
freeze + discard (rollback) or freeze + accept (promotion) by the actual
worker cleans the pending work while the journal, ledger and audit rows
stay intact; terminal-workspace requests keep their ordinary refusal and
leave every fact unchanged.

No source-string oracles, no mocked foundation replacement: the barrier
is real DB instrumentation on the real completion path, and every durable
assertion runs after the failure has settled (owner post-rollback
queries; no inspection of another connection's uncommitted state).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.review_worker.accept_job import MediaBoundary
from test_agent_mutations import _seed
from test_agent_theme_boundaries import _agent_client
from test_freeze_review_snapshot import (
    _CURRENT_VERSION_FACTS,
    _accept_claim_run,
    _freeze_claim_run,
    _worker_pool,
)
from test_media_security_lifecycle import _media_settings
from test_media_workspace_migration_preservation import (
    _content_operations,
    _discard_claim_run,
)

# One dedicated 64-bit advisory key for the barrier rendezvous.
_BARRIER_LOCK_KEY = 8311005
_BARRIER_RENDEZVOUS_TIMEOUT_S = 30.0
_BARRIER_POLL_S = 0.05
_BACKEND_SETTLE_TIMEOUT_S = 15.0

_BARRIER_TABLE_SQL = """
CREATE TABLE control.c5_completion_barrier (
    workspace_id uuid PRIMARY KEY,
    mode text NOT NULL CHECK (mode IN ('fail', 'hold'))
)
"""

_BARRIER_FUNCTION_SQL = """
CREATE FUNCTION control.slaif_c5_completion_barrier()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog AS $fn$
DECLARE
    c5_mode text;
BEGIN
    SELECT b.mode INTO c5_mode
    FROM control.c5_completion_barrier b
    WHERE b.workspace_id = NEW.workspace_id;
    IF c5_mode IS NULL THEN
        RETURN NEW;
    END IF;
    PERFORM pg_advisory_xact_lock(8311005);
    IF c5_mode = 'fail' THEN
        RAISE EXCEPTION 'C5_COMPLETION_LATE_FAILURE'
            USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END
$fn$
"""

_BARRIER_TRIGGER_SQL = """
CREATE TRIGGER c5_completion_barrier_trg
AFTER INSERT ON audit.mutation_completion
FOR EACH ROW EXECUTE FUNCTION control.slaif_c5_completion_barrier()
"""

_BARRIER_DROP_TRIGGER_SQL = (
    "DROP TRIGGER c5_completion_barrier_trg ON audit.mutation_completion"
)
_BARRIER_DROP_FUNCTION_SQL = "DROP FUNCTION control.slaif_c5_completion_barrier()"
_BARRIER_DROP_TABLE_SQL = "DROP TABLE control.c5_completion_barrier"


def _owner(database: AgentSiteDatabase) -> Any:
    return owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    )


async def _pin_current_version_facts(
    database: AgentSiteDatabase, workspace_id: UUID
) -> None:
    """Give the seeded workspace the exact version-facts pin the real
    workspace creator (``control.slaif_workspace_create``) writes.

    The shared ``_seed`` fixture predates the 076 pin capture, so its
    workspaces carry the empty default; the 076 materializer gate
    refuses to freeze a version-unknown workspace.  Pinning the real
    current facts (same literal as the trusted creator) is what makes
    the real freeze lifecycle applicable to this fixture.
    """
    async with _owner(database) as owner:
        await owner.execute(
            "UPDATE control.workspace SET version_facts = "
            + _CURRENT_VERSION_FACTS
            + " WHERE id = $1",
            workspace_id,
        )


@asynccontextmanager
async def _completion_barrier(
    database: AgentSiteDatabase, workspace_id: UUID, mode: str
) -> AsyncIterator[None]:
    """Install the trusted test-only AFTER INSERT journal barrier.

    Owner objects only, committed before the request, removed in ``finally``
    even on test failure.  With no barrier row for the workspace the
    trigger is a no-op, so the SAME app can serve the exactly-once retry.
    """
    async with _owner(database) as owner:
        async with owner.transaction():
            await owner.execute(_BARRIER_TABLE_SQL)
            await owner.execute(_BARRIER_FUNCTION_SQL)
            await owner.execute(_BARRIER_TRIGGER_SQL)
            await owner.execute(
                "INSERT INTO control.c5_completion_barrier"
                " (workspace_id, mode) VALUES ($1, $2)",
                workspace_id,
                mode,
            )
    try:
        yield
    finally:
        async with _owner(database) as owner:
            async with owner.transaction():
                await owner.execute(_BARRIER_DROP_TRIGGER_SQL)
                await owner.execute(_BARRIER_DROP_FUNCTION_SQL)
                await owner.execute(_BARRIER_DROP_TABLE_SQL)


async def _clear_barrier_row(database: AgentSiteDatabase, workspace_id: UUID) -> None:
    """Disable the barrier for further journal inserts (retry window)."""
    async with _owner(database) as owner:
        await owner.execute(
            "DELETE FROM control.c5_completion_barrier WHERE workspace_id = $1",
            workspace_id,
        )


@asynccontextmanager
async def _barrier_lock_owner(
    database: AgentSiteDatabase,
) -> AsyncIterator[Any]:
    """Hold the rendezvous session lock on an owner connection.

    Yields the holding connection; the test releases the lock explicitly
    at the failure point.  The final unlock is idempotent cleanup for leak
    paths (a session lock also dies with the connection).
    """
    async with _owner(database) as owner:
        await owner.fetchval("SELECT pg_advisory_lock($1)", _BARRIER_LOCK_KEY)
        try:
            yield owner
        finally:
            await owner.fetchval("SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY)


async def _wait_for_barrier_parked(database: AgentSiteDatabase, login: str) -> int:
    """Wait (bounded, real state) for the trigger to park at the rendezvous.

    The pending lock request can only appear AFTER the journal INSERT has
    executed, so this is deterministic positioning, not a sleep oracle.
    A single-bigint advisory key maps in ``pg_locks`` to ``classid`` = high
    32 bits, ``objid`` = low 32 bits, ``objsubid`` = 1, and advisory locks
    are local per database, so the probe is scoped to this fixture database
    and to the exact runtime login's backend.
    Returns the parked backend pid (the request's own runtime connection).
    """
    async with _owner(database) as owner:
        deadline = time.monotonic() + _BARRIER_RENDEZVOUS_TIMEOUT_S
        while True:
            pid = await owner.fetchval(
                "SELECT l.pid"
                " FROM pg_catalog.pg_locks l"
                " JOIN pg_catalog.pg_stat_activity a ON a.pid = l.pid"
                " WHERE l.classid = 0"
                " AND l.objid = $1"
                " AND l.objsubid = 1"
                " AND NOT l.granted"
                " AND l.database = ("
                "   SELECT oid FROM pg_catalog.pg_database"
                "   WHERE datname = current_database()"
                " )"
                " AND a.usename = $2"
                " ORDER BY l.pid LIMIT 1",
                _BARRIER_LOCK_KEY,
                login,
            )
            if pid is not None:
                return int(pid)
            if time.monotonic() >= deadline:
                raise AssertionError(
                    "C5 barrier: the completion journal rendezvous never "
                    "parked (the journal INSERT did not reach the barrier)"
                )
            await asyncio.sleep(_BARRIER_POLL_S)


async def _backend_info(
    database: AgentSiteDatabase, pid: int
) -> tuple[str, str] | None:
    """Owner-visible identity of one backend (state/query are redacted for
    foreign backends, so the state proof uses the fixture administrator)."""
    async with _owner(database) as owner:
        row = await owner.fetchrow(
            "SELECT datname, usename FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
    if row is None:
        return None
    return str(row["datname"]), str(row["usename"])


async def _wait_for_backend_gone(database: AgentSiteDatabase, pid: int) -> None:
    deadline = time.monotonic() + _BACKEND_SETTLE_TIMEOUT_S
    while True:
        if await _backend_info(database, pid) is None:
            return
        if time.monotonic() >= deadline:
            raise AssertionError(f"backend {pid} did not terminate")
        await asyncio.sleep(_BARRIER_POLL_S)


async def _durable_snapshot(
    database: AgentSiteDatabase, seeded: dict[str, UUID]
) -> dict[str, tuple[Any, ...]]:
    """Owner snapshot of the four mutable states + canonical + workspace."""
    async with _owner(database) as owner:
        ledger = tuple(
            sorted(
                str(row[0])
                for row in await owner.fetch(
                    "SELECT row_to_json(t)::text FROM control.agent_idempotency t"
                )
            )
        )
        audit = tuple(
            sorted(
                str(row[0])
                for row in await owner.fetch(
                    "SELECT row_to_json(t)::text FROM audit.agent_mutation t"
                )
            )
        )
        journal = tuple(
            sorted(
                str(row[0])
                for row in await owner.fetch(
                    "SELECT row_to_json(t)::text FROM audit.mutation_completion t"
                )
            )
        )
        canonical_pages = tuple(
            sorted(
                str(row[0])
                for row in await owner.fetch(
                    "SELECT row_to_json(t)::text FROM content.page_base t"
                    " WHERE t.site_id = $1",
                    seeded["site_id"],
                )
            )
        )
        workspace = await owner.fetchrow(
            "SELECT id, status::text, delegator_id, site_id"
            " FROM control.workspace WHERE id = $1",
            seeded["workspace_id"],
        )
    operations = await _content_operations(database, seeded["workspace_id"])
    return {
        "ledger": ledger,
        "audit": audit,
        "journal": journal,
        "canonical_pages": canonical_pages,
        "workspace": tuple(workspace) if workspace is not None else (),
        "operations": tuple(sorted(str(op) for op in operations)),
    }


def _assert_snapshot_equal(
    before: dict[str, tuple[Any, ...]],
    after: dict[str, tuple[Any, ...]],
    *,
    label: str,
) -> None:
    for field in before:
        assert before[field] == after[field], (
            f"{label}: {field} changed: {before[field]!r} -> {after[field]!r}"
        )


async def _completion_facts(
    database: AgentSiteDatabase, operation_id: UUID
) -> dict[str, tuple[Any, ...]]:
    """Byte-exact ledger/audit/journal rows for one operation (owner)."""
    async with _owner(database) as owner:
        ledger = tuple(
            str(row[0])
            for row in await owner.fetch(
                "SELECT row_to_json(t)::text FROM control.agent_idempotency t"
                " WHERE t.operation_id = $1",
                operation_id,
            )
        )
        audit = tuple(
            str(row[0])
            for row in await owner.fetch(
                "SELECT row_to_json(t)::text FROM audit.agent_mutation t"
                " WHERE t.operation_id = $1",
                operation_id,
            )
        )
        journal = tuple(
            str(row[0])
            for row in await owner.fetch(
                "SELECT row_to_json(t)::text FROM audit.mutation_completion t"
                " WHERE t.operation_id = $1",
                operation_id,
            )
        )
    return {"ledger": ledger, "audit": audit, "journal": journal}


async def _workspace_status(database: AgentSiteDatabase, workspace_id: UUID) -> str:
    async with _owner(database) as owner:
        status = await owner.fetchval(
            "SELECT status::text FROM control.workspace WHERE id = $1",
            workspace_id,
        )
    assert status is not None
    return str(status)


def _page_body(slug: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": f"{slug} page",
        "status": "DRAFT",
        "locale": "en",
    }


def _request_headers(token: str, key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key}


async def _create_page(
    client: httpx.AsyncClient, token: str, *, key: str, slug: str
) -> httpx.Response:
    return await client.post(
        "/api/agent/v1/pages",
        json=_page_body(slug),
        headers=_request_headers(token, key),
    )


async def _assert_exactly_once_completion(
    database: AgentSiteDatabase,
    seeded: dict[str, UUID],
    *,
    label: str,
    key: str,
    result: dict[str, Any],
) -> UUID:
    """Durable exactly-once growth after the same-key runtime retry."""
    operation_id = UUID(result["operation_id"])
    page_id = UUID(result["record"]["id"])
    assert result["action"] == "PAGE_CREATED"
    async with _owner(database) as owner:
        ledger_row = await owner.fetchrow(
            "SELECT idempotency_key, status_code, response_body"
            " FROM control.agent_idempotency WHERE operation_id = $1",
            operation_id,
        )
        audit_row = await owner.fetchrow(
            "SELECT resource_type, resource_id, response_status"
            " FROM audit.agent_mutation WHERE operation_id = $1",
            operation_id,
        )
        journal_row = await owner.fetchrow(
            "SELECT family, site_id, workspace_id, capability_id,"
            " human_user_id, request_identity, resource_type, resource_id,"
            " disposition, schema_version"
            " FROM audit.mutation_completion WHERE operation_id = $1",
            operation_id,
        )
    assert ledger_row is not None, f"{label}: retry reservation missing"
    assert str(ledger_row["idempotency_key"]) == key
    assert int(ledger_row["status_code"]) == 201
    assert json.loads(str(ledger_row["response_body"]))["action"] == "PAGE_CREATED"
    assert audit_row is not None, f"{label}: retry family audit row missing"
    assert str(audit_row["resource_type"]) == "page"
    assert audit_row["resource_id"] == page_id
    assert int(audit_row["response_status"]) == 201
    assert journal_row is not None, f"{label}: retry journal row missing"
    assert str(journal_row["family"]) == "agent"
    assert journal_row["site_id"] == seeded["site_id"]
    assert journal_row["workspace_id"] == seeded["workspace_id"]
    assert journal_row["capability_id"] == seeded["capability_id"]
    assert journal_row["human_user_id"] is None
    assert (
        str(journal_row["request_identity"])
        == hashlib.sha256(key.encode("utf-8")).hexdigest()
    )
    # The actual created resource id, not a placeholder attribution.
    assert journal_row["resource_type"] == "page"
    assert journal_row["resource_id"] == page_id
    assert str(journal_row["disposition"]) == "completed"
    assert str(journal_row["schema_version"]) == "mutation-completion/v1"
    operations = await _content_operations(database, seeded["workspace_id"])
    assert tuple(sorted(str(op) for op in operations)) == (str(operation_id),), (
        f"{label}: the returned operation id must be the one public"
        f" pending COW id, got {operations!r}"
    )
    assert await _workspace_status(database, seeded["workspace_id"]) == "ACTIVE"
    return operation_id


@pytest.mark.asyncio
async def test_completion_late_failure_rolls_back_and_retries_once(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C5a: failure strictly after the journal INSERT, inside the same
    uncommitted mutation transaction, rolls back all four states; the same
    key retried on the same real runtime completes exactly once."""
    database = agent_site_database
    token, seeded = await _seed(database)
    ws = seeded["workspace_id"]
    key = "c5-late-fail-key"
    slug = "c5-late-fail"

    async with _completion_barrier(database, ws, "fail"):
        before = await _durable_snapshot(database, seeded)
        async with _agent_client(database) as client:
            async with _barrier_lock_owner(database) as lock_owner:
                task = asyncio.create_task(
                    _create_page(client, token, key=key, slug=slug)
                )
                parked_pid = await _wait_for_barrier_parked(
                    database, database.credentials["slaif_agent_runtime"][0]
                )
                info = await _backend_info(database, parked_pid)
                assert info is not None
                assert info[0] == database.name, info
                assert info[1] == database.credentials["slaif_agent_runtime"][0], info
                # Release the rendezvous: the trigger now raises inside the
                # still-uncommitted mutation transaction.
                assert (
                    await lock_owner.fetchval(
                        "SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY
                    )
                    is True
                )
                failed = await task
            assert failed.status_code == 503, failed.text
            assert json.loads(failed.text)["error"]["code"] == "SERVICE_UNAVAILABLE"
            # The trusted internal marker never reaches the public surface.
            assert "C5_COMPLETION_LATE_FAILURE" not in failed.text
            # The settled rollback must leave every state exactly as before
            # the request (all four states + canonical + workspace + the
            # public pending ids) BEFORE the retry may begin.
            after_failure = await _durable_snapshot(database, seeded)
            _assert_snapshot_equal(before, after_failure, label="late-failure rollback")
            # The rolled-back reservation retains nothing: the barrier row is
            # cleared so the same app serves the fresh same-key retry.
            await _clear_barrier_row(database, ws)
            retried = await _create_page(client, token, key=key, slug=slug)
    assert retried.status_code == 201, retried.text
    result = retried.json()
    await _assert_exactly_once_completion(
        database, seeded, label="late-failure", key=key, result=result
    )
    after = await _durable_snapshot(database, seeded)
    assert len(after["ledger"]) == len(before["ledger"]) + 1
    assert len(after["audit"]) == len(before["audit"]) + 1
    assert len(after["journal"]) == len(before["journal"]) + 1
    assert after["canonical_pages"] == before["canonical_pages"]
    assert after["workspace"] == before["workspace"]
    assert len(after["operations"]) == 1


@pytest.mark.asyncio
async def test_completion_cancellation_after_journal_rolls_back_and_retries_once(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C5b: cancelling the real request task while the trigger is parked
    after the journal INSERT aborts the same uncommitted transaction; the
    same key retried on the same real runtime completes exactly once."""
    database = agent_site_database
    token, seeded = await _seed(database)
    ws = seeded["workspace_id"]
    key = "c5-cancel-key"
    slug = "c5-cancel"

    async with _completion_barrier(database, ws, "hold"):
        before = await _durable_snapshot(database, seeded)
        async with _agent_client(database) as client:
            async with _barrier_lock_owner(database) as lock_owner:
                task = asyncio.create_task(
                    _create_page(client, token, key=key, slug=slug)
                )
                parked_pid = await _wait_for_barrier_parked(
                    database, database.credentials["slaif_agent_runtime"][0]
                )
                info = await _backend_info(database, parked_pid)
                assert info is not None
                assert info[0] == database.name, info
                assert info[1] == database.credentials["slaif_agent_runtime"][0], info
                # The request is parked with the journal INSERT executed and
                # uncommitted; now cancel the real request task.
                task.cancel()
                outcome = await asyncio.gather(task, return_exceptions=True)
                assert isinstance(outcome[0], asyncio.CancelledError), outcome
                assert (
                    await lock_owner.fetchval(
                        "SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY
                    )
                    is True
                )
            after_failure = await _durable_snapshot(database, seeded)
            _assert_snapshot_equal(before, after_failure, label="cancellation rollback")
            await _clear_barrier_row(database, ws)
            retried = await _create_page(client, token, key=key, slug=slug)
    assert retried.status_code == 201, retried.text
    result = retried.json()
    await _assert_exactly_once_completion(
        database, seeded, label="cancellation", key=key, result=result
    )
    after = await _durable_snapshot(database, seeded)
    assert len(after["ledger"]) == len(before["ledger"]) + 1
    assert len(after["audit"]) == len(before["audit"]) + 1
    assert len(after["journal"]) == len(before["journal"]) + 1
    assert after["canonical_pages"] == before["canonical_pages"]
    assert after["workspace"] == before["workspace"]
    assert len(after["operations"]) == 1


@pytest.mark.asyncio
async def test_completion_owned_connection_loss_rolls_back_and_pool_recovers(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """C5c: real connection loss after the journal INSERT and inside the
    uncommitted transaction.  The hold-mode trigger parks the request at
    the real AFTER INSERT boundary; the disposable fixture administrator
    connection (the same superuser that creates and drops this test
    database) terminates ONLY the exact matched runtime backend.  No
    product role policy is changed.  The pool replaces the lost connection
    and the same key retried on the same real runtime completes exactly
    once."""
    database = agent_site_database
    token, seeded = await _seed(database)
    ws = seeded["workspace_id"]
    key = "c5-kill-key"
    slug = "c5-kill"

    async with _completion_barrier(database, ws, "hold"):
        before = await _durable_snapshot(database, seeded)
        async with _agent_client(database) as client:
            async with _barrier_lock_owner(database) as lock_owner:
                task = asyncio.create_task(
                    _create_page(client, token, key=key, slug=slug)
                )
                login = database.credentials["slaif_agent_runtime"][0]
                parked_pid = await _wait_for_barrier_parked(database, login)
                info = await _backend_info(database, parked_pid)
                assert info is not None
                assert info[0] == database.name, info
                assert info[1] == login, info
                # Stable identity + actual state via the fixture
                # administrator (superuser sees unredacted
                # pg_stat_activity): exact database, exact runtime login,
                # actively executing the parked completion.
                act = await database.administrator.fetchrow(
                    "SELECT datname, usename, state::text"
                    " FROM pg_catalog.pg_stat_activity WHERE pid = $1",
                    parked_pid,
                )
                assert act is not None
                assert str(act["datname"]) == database.name, act
                assert str(act["usename"]) == login, act
                assert str(act["state"]) == "active", act
                # Stable backend identity: the same backend is still the
                # waiting rendezvous holder (pg_locks is fully visible).
                assert await _wait_for_barrier_parked(database, login) == parked_pid
                # Bounded fixture-administrator termination of ONLY the
                # exact matched backend (its trigger stays parked, the
                # transaction uncommitted).
                terminated = await database.administrator.fetchval(
                    "SELECT pg_terminate_backend($1)", parked_pid
                )
                assert terminated is True
                assert (
                    await lock_owner.fetchval(
                        "SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY
                    )
                    is True
                )
                killed = await task
            # Real connection loss: with the dead-connection cleanup
            # preserving the body's own error, the runtime surfaces the
            # normal safe unavailable path (the exact public mapping of
            # the rolled-back completion failure).
            assert killed.status_code == 503, killed.text
            assert json.loads(killed.text)["error"]["code"] == "SERVICE_UNAVAILABLE"
            assert "C5_COMPLETION_LATE_FAILURE" not in killed.text
            await _wait_for_backend_gone(database, parked_pid)
            after_failure = await _durable_snapshot(database, seeded)
            _assert_snapshot_equal(
                before, after_failure, label="connection-loss rollback"
            )
            await _clear_barrier_row(database, ws)
            # The SAME app and runtime pool: the lost connection must have
            # been replaced with the correct context.
            retried = await _create_page(client, token, key=key, slug=slug)
    assert retried.status_code == 201, retried.text
    result = retried.json()
    await _assert_exactly_once_completion(
        database, seeded, label="connection-loss", key=key, result=result
    )
    after = await _durable_snapshot(database, seeded)
    assert len(after["ledger"]) == len(before["ledger"]) + 1
    assert len(after["audit"]) == len(before["audit"]) + 1
    assert len(after["journal"]) == len(before["journal"]) + 1
    assert after["canonical_pages"] == before["canonical_pages"]
    assert after["workspace"] == before["workspace"]
    assert len(after["operations"]) == 1


@pytest.mark.asyncio
async def test_real_discard_keeps_new_completion_facts(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """P6a: real worker freeze + discard clears pending COW and leaves the
    workspace terminal, while the journal/ledger/audit rows of the 078-era
    completion stay intact; terminal requests keep their ordinary refusal."""
    database = agent_site_database
    token, seeded = await _seed(database)
    ws = seeded["workspace_id"]
    await _pin_current_version_facts(database, ws)

    async with _agent_client(database) as client:
        created = await _create_page(
            client, token, key="c5-discard-key", slug="c5-discard"
        )
        assert created.status_code == 201, created.text
        result = created.json()
        operation_id = UUID(result["operation_id"])
        page_id = UUID(result["record"]["id"])
        # Ordinary same-key replay while the workspace is still ACTIVE.
        replay = await _create_page(
            client, token, key="c5-discard-key", slug="c5-discard"
        )
        assert replay.status_code == 201, replay.text
        assert replay.json() == result
    assert (await _completion_facts(database, operation_id))["journal"]
    assert await _content_operations(database, ws)

    facts_before = await _completion_facts(database, operation_id)
    pool = await _worker_pool(database)
    try:
        freeze_result, _freeze_job = await _freeze_claim_run(
            database,
            workspace_id=ws,
            site_id=seeded["site_id"],
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant="c5-discard-freeze",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result.error
        discard_result = await _discard_claim_run(
            database,
            pool,
            workspace_id=ws,
            site_id=seeded["site_id"],
            user_id=seeded["delegator_id"],
        )
        assert discard_result.status == "SUCCEEDED", discard_result.error
    finally:
        await pool.close()

    assert not await _content_operations(database, ws)
    assert await _workspace_status(database, ws) == "DISCARDED"
    async with _owner(database) as owner:
        canonical_count = await owner.fetchval(
            "SELECT count(*) FROM content.page_base WHERE id = $1", page_id
        )
    assert int(canonical_count) == 0
    assert await _completion_facts(database, operation_id) == facts_before

    # Terminal workspace: the trusted capability authenticator only sees
    # ACTIVE workspaces (w.status='ACTIVE' in
    # control.slaif_agent_capability_authenticate), so the ordinary
    # terminal refusal is the same 401 an invalid token receives - no
    # state is leaked and no journal/ledger effect is possible.
    async with _agent_client(database) as client:
        denied = await _create_page(
            client, token, key="c5-discard-terminal-key", slug="c5-discard-terminal"
        )
        # The ORIGINAL same key/body after terminal is refused the same
        # way: no reactivation, no successful late replay.
        replay_denied = await _create_page(
            client, token, key="c5-discard-key", slug="c5-discard"
        )
    assert denied.status_code == 401, denied.text
    assert denied.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert replay_denied.status_code == 401, replay_denied.text
    assert replay_denied.json()["error"]["code"] == "AUTHENTICATION_REQUIRED", (
        replay_denied.text
    )
    assert (await _completion_facts(database, operation_id)) == facts_before
    assert not await _content_operations(database, ws)
    assert await _workspace_status(database, ws) == "DISCARDED"


@pytest.mark.asyncio
async def test_real_accept_keeps_new_completion_facts(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """P6b: real worker freeze + accept promotes the pending COW page to
    canonical while the journal/ledger/audit rows of the 078-era completion
    stay intact; terminal requests keep their ordinary refusal."""
    database = agent_site_database
    token, seeded = await _seed(database)
    ws = seeded["workspace_id"]
    await _pin_current_version_facts(database, ws)

    async with _agent_client(database) as client:
        created = await _create_page(
            client, token, key="c5-accept-key", slug="c5-accept"
        )
        assert created.status_code == 201, created.text
        result = created.json()
        operation_id = UUID(result["operation_id"])
        page_id = UUID(result["record"]["id"])
        # Ordinary same-key replay while the workspace is still ACTIVE.
        replay = await _create_page(
            client, token, key="c5-accept-key", slug="c5-accept"
        )
        assert replay.status_code == 201, replay.text
        assert replay.json() == result
    assert (await _completion_facts(database, operation_id))["journal"]
    assert await _content_operations(database, ws)

    facts_before = await _completion_facts(database, operation_id)
    boundary = MediaBoundary(settings=_media_settings(database, tmp_path / "media"))
    pool = await _worker_pool(database)
    try:
        freeze_result, _freeze_job = await _freeze_claim_run(
            database,
            workspace_id=ws,
            site_id=seeded["site_id"],
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant="c5-accept-freeze",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result.error
        accept_result, _accept_job = await _accept_claim_run(
            database,
            workspace_id=ws,
            delegator_id=seeded["delegator_id"],
            pool=pool,
            claimant="c5-accept-claim",
            boundary=boundary,
        )
        assert accept_result.status == "SUCCEEDED", accept_result.error
    finally:
        await boundary.stop()
        await pool.close()

    assert not await _content_operations(database, ws)
    assert await _workspace_status(database, ws) == "ACCEPTED"
    async with _owner(database) as owner:
        canonical_count = await owner.fetchval(
            "SELECT count(*) FROM content.page_base WHERE id = $1", page_id
        )
    assert int(canonical_count) == 1
    assert await _completion_facts(database, operation_id) == facts_before

    # Terminal workspace: ordinary refusal, every fact unchanged (same
    # 401 semantics as the discard path above).
    async with _agent_client(database) as client:
        denied = await _create_page(
            client, token, key="c5-accept-terminal-key", slug="c5-accept-terminal"
        )
        # The ORIGINAL same key/body after terminal is refused the same
        # way: no reactivation, no successful late replay.
        replay_denied = await _create_page(
            client, token, key="c5-accept-key", slug="c5-accept"
        )
    assert denied.status_code == 401, denied.text
    assert denied.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert replay_denied.status_code == 401, replay_denied.text
    assert replay_denied.json()["error"]["code"] == "AUTHENTICATION_REQUIRED", (
        replay_denied.text
    )
    assert (await _completion_facts(database, operation_id)) == facts_before
    assert not await _content_operations(database, ws)
    assert await _workspace_status(database, ws) == "ACCEPTED"

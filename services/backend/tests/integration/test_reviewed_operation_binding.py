"""083/12 companion-manifest integration evidence (real PostgreSQL).

The reviewed-operations/v1 companion is the immutable half of a
logical review snapshot at and after this head.  These cases prove,
on the explicitly owned disposable PostgreSQL with the real product
freeze/accept workers and the real public 0.2.1 foundation getters:

- a real freeze captures the actual public session state (operation
  universe U, foundation dependency pairs, trusted 078 completion
  identities) in the same locked transaction and stores exactly one
  companion bound to snapshot/site/workspace whose manifest digest
  recomputes over the stored content;
- a real mixed-family session (Agent page creates plus HUMAN-on-AGENT
  edits of the SAME page: a superseding title chain ending in a
  net-zero revert, two promoted page rows) freezes with U exactly the
  five public operations and the real same-resource dependency
  closure,
  and the exact approval promotes both pages once with the exact
  applied-ID receipt;
- an exact successful whole-session acceptance (Agent family): the
  real worker reviewer transaction compares approved/live/applied
  operation IDs exactly and persists the append-only promotion
  receipt with the applied IDs and both approval digests;
- idempotent replay dedupe, two same-site workspaces with isolated
  U, and a genuine empty-U freeze/accept;
- a real freeze failure (trusted journal-negative fixture) leaves no
  partial snapshot/companion state and a typed stable job code;
- the human review document carries the companion (and NULL for a
  historical companion-less snapshot, which stays readable but is
  never acceptable);
- the control accept route refuses a companion-less legacy snapshot
  and a real other-workspace companion digest with the uniform 404
  class, creating no job;
- an operation written after the approved freeze is refused INSIDE
  the actual reviewer transaction before any publication effect
  (the approved universe cannot be widened between the preflight and
  the reviewer transaction);
- freeze drains a real in-flight mutation into U and later writes
  are denied while the workspace is in review;
- a discarded-and-refrozen workspace keeps the original
  snapshot/companion bytes immutable while a stale approval of the
  old snapshot is refused and the fresh one accepts;
- cancellation and exact fixture-owned backend loss inside the real
  accept transaction AFTER the foundation promotion executed roll
  canonical/pending/receipt/audit/revision/workspace/job/outbox back
  and the same job re-claims to a real exactly-once promotion (the
  existing A6 witness in test_real_human_accept covers the fail-mode
  late refusal at the same boundary);
- the 079 forward-only repair of content.slaif_content_type_update
  (017 defect) through a real HUMAN-on-AGENT content-model PATCH,
  with real COW pending state, the trusted 078 completion, and a
  real freeze/accept of that human_editor operation.

Fixture honesty: the barrier triggers are trusted test-only owner
objects on the fixture database (installed per case, dropped in
cleanup); they add exactly one documented fault - an advisory-lock
rendezvous hold at the real AFTER INSERT boundary - and no mocked
foundation replacement.  No product grant, endpoint or error mapping
is weakened for any case.
"""

# ruff: noqa: E501 -- explicit fixture and SQL contracts

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_api.models import AgentCapabilityContext
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    get_operation_dependencies,
    get_session_operations,
)
from slaif_agent_site.agent_state.mutations import (
    AgentCowContentModelService,
    AgentMutationUnavailableError,
    execute_agent_mutation,
    mutation_digest,
)
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.content_model.composition_models import (
    AgentUpdateCompositionNodeRequest,
)
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from slaif_agent_site.review_worker.freeze_job import run_freeze_job
from slaif_agent_site.review_worker.operation_manifest import (
    build_operation_manifest,
)
from slaif_agent_site.review_worker.snapshot import (
    build_snapshot_document,
    canonical_json,
)
from test_agent_mutations import _seed
from test_agent_theme_boundaries import _agent_client
from test_media_workspace_isolation import _completion_rows
from test_media_workspace_migration_preservation import _discard_claim_run
from test_real_human_accept import (
    _CURRENT_VERSION_FACTS,
    _WORKER_KINDS,
    _accept_headers,
    _age_heartbeat,
    _claim_accept,
    _control_call,
    _control_settings,
    _CowPoolAdapter,
    _enqueue_bound_accept,
    _error_envelope,
    _freeze_workspace,
    _media_settings,
    _read_manifest,
    _seed_review_state,
    _seed_site,
    _worker_call,
    _worker_pool,
    _worker_settings,
    _workspace_state,
)
from test_trusted_completion_late_failure import (
    _BARRIER_LOCK_KEY,
    _BARRIER_POLL_S,
    _BARRIER_RENDEZVOUS_TIMEOUT_S,
    _barrier_lock_owner,
    _completion_barrier,
    _create_page,
    _wait_for_backend_gone,
    _wait_for_barrier_parked,
)
from test_trusted_completion_producer_families import (
    _editor_headers,
    _editor_stack,
    _human_session,
    _pending_operations,
    _seed_agent_workspace,
)

# One dedicated 64-bit advisory key for the accept-side barrier.
_C12_BARRIER_LOCK_KEY = 8312007
_C12_RENDEZVOUS_TIMEOUT_S = 30.0
_C12_POLL_S = 0.05

_C12_BARRIER_TABLE_SQL = """
CREATE TABLE control.c12_accept_barrier (
    workspace_id uuid PRIMARY KEY,
    mode text NOT NULL CHECK (mode = 'hold')
)
"""

_C12_BARRIER_FUNCTION_SQL = """
CREATE FUNCTION control.slaif_c12_accept_barrier()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog AS $fn$
BEGIN
    PERFORM 1
    FROM control.c12_accept_barrier b
    WHERE b.workspace_id = NEW.workspace_id;
    IF FOUND THEN
        PERFORM pg_advisory_xact_lock(8312007);
    END IF;
    RETURN NEW;
END
$fn$
"""

_C12_BARRIER_TRIGGER_SQL = """
CREATE TRIGGER c12_accept_barrier_trg
AFTER INSERT ON audit.promotion
FOR EACH ROW EXECUTE FUNCTION control.slaif_c12_accept_barrier()
"""

_C12_DROP_TRIGGER_SQL = "DROP TRIGGER c12_accept_barrier_trg ON audit.promotion"
_C12_DROP_FUNCTION_SQL = "DROP FUNCTION control.slaif_c12_accept_barrier()"
_C12_DROP_TABLE_SQL = "DROP TABLE control.c12_accept_barrier"


@asynccontextmanager
async def _owner(database: AgentSiteDatabase) -> AsyncIterator[Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        yield owner


@asynccontextmanager
async def _accept_barrier(
    database: AgentSiteDatabase, workspace_id: UUID
) -> AsyncIterator[None]:
    """Trusted test-only AFTER INSERT barrier on the promotion audit.

    The trigger fires inside the single accept reviewer transaction
    AFTER the real foundation promotion and the in-transaction
    applied/pending checks: it is the post-commit boundary the C5
    cancellation/connection-loss cases park at.  Hold-only; the
    fail-mode late refusal at this boundary is the qualified A6
    witness in test_real_human_accept.  Disarmed and dropped even on
    test failure so the same app/pool serves the retry.
    """
    async with _owner(database) as owner:
        await owner.execute(_C12_BARRIER_TABLE_SQL)
        await owner.execute(_C12_BARRIER_FUNCTION_SQL)
        await owner.execute(_C12_BARRIER_TRIGGER_SQL)
        await owner.execute(
            "INSERT INTO control.c12_accept_barrier (workspace_id, mode) "
            "VALUES ($1, 'hold')",
            workspace_id,
        )
    try:
        yield
    finally:
        async with _owner(database) as owner:
            await owner.execute(
                "DELETE FROM control.c12_accept_barrier WHERE workspace_id = $1",
                workspace_id,
            )
            await owner.execute(_C12_DROP_TRIGGER_SQL)
            await owner.execute(_C12_DROP_FUNCTION_SQL)
            await owner.execute(_C12_DROP_TABLE_SQL)


@asynccontextmanager
async def _c12_barrier_lock_owner(database: AgentSiteDatabase) -> AsyncIterator[Any]:
    """Hold the accept barrier rendezvous on an owner connection."""
    async with _owner(database) as owner:
        await owner.fetchval("SELECT pg_advisory_lock($1)", _C12_BARRIER_LOCK_KEY)
        try:
            yield owner
        finally:
            await owner.fetchval("SELECT pg_advisory_unlock($1)", _C12_BARRIER_LOCK_KEY)


async def _wait_for_c12_parked(database: AgentSiteDatabase, login: str) -> int:
    """Bounded, real-state wait for the accept backend to park at the
    promotion barrier; returns the parked pid.  The pending advisory
    request only exists AFTER the promotion INSERT executed inside
    the not-yet-committed reviewer transaction (post foundation
    commit)."""
    async with _owner(database) as owner:
        deadline = time.monotonic() + _C12_RENDEZVOUS_TIMEOUT_S
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
                _C12_BARRIER_LOCK_KEY,
                login,
            )
            if pid is not None:
                return int(pid)
            if time.monotonic() >= deadline:
                raise AssertionError(
                    "C12 barrier: the accept promotion rendezvous never "
                    "parked (the promotion INSERT did not reach the barrier)"
                )
            await asyncio.sleep(_C12_POLL_S)


async def _backend_identity(
    database: AgentSiteDatabase, pid: int
) -> tuple[str, str] | None:
    async with _owner(database) as owner:
        row = await owner.fetchrow(
            "SELECT datname, usename FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
    if row is None:
        return None
    return str(row["datname"]), str(row["usename"])


async def _wait_for_parked_or_task_failure(
    database: AgentSiteDatabase, login: str, task: asyncio.Task[Any]
) -> int:
    """Bounded wait for the real parked rendezvous.

    A mutation task that dies before its journal INSERT is a real
    defect, not a rendezvous timeout: surface its actual exception
    (or its normal result) instead of a blind timed-out assertion."""
    try:
        return await _wait_for_barrier_parked(database, login)
    except AssertionError as error:
        if task.done():
            if task.cancelled():
                raise AssertionError(
                    "in-flight mutation task was cancelled before the journal barrier"
                ) from None
            exc = task.exception()
            raise AssertionError(
                "in-flight mutation completed without reaching the "
                f"journal barrier (result/exception: {exc!r})"
            ) from exc
        # The task is still alive but never parked: capture where its
        # real backend is executing for the assertion (bounded: state +
        # left of the current statement only).
        async with _owner(database) as owner:
            act = await owner.fetch(
                "SELECT pid, state, LEFT(query, 120) FROM pg_catalog.pg_stat_activity"
                " WHERE usename = $1 AND datname = current_database()"
                " AND pid <> pg_backend_pid() ORDER BY pid",
                login,
            )
        detail = (
            "; ".join(f"pid={r['pid']} state={r['state']} q={r[1]!r}" for r in act)
            or "no backend"
        )
        raise AssertionError(f"{error} | runtime backends: {detail}") from None


async def _wait_for_transaction_lock_waiter(
    database: AgentSiteDatabase, login: str
) -> int:
    """Bounded wait for the real ``login`` backend to hold an
    UNGRANTED transaction-id lock request (deterministic positioning
    through real lock-table state - the fixture owner cannot see other
    roles' activity state, but ``pg_locks`` is public).  A
    transaction-id lock is exactly what PostgreSQL records while a
    statement waits on a row locked by another OPEN transaction; with
    the in-flight mutation parked in its uncommitted COW transaction,
    that is the freeze enqueue being blocked by the in-flight
    mutation.  No blind sleep."""
    async with _owner(database) as owner:
        deadline = time.monotonic() + _BARRIER_RENDEZVOUS_TIMEOUT_S
        while True:
            pid = await owner.fetchval(
                "SELECT l.pid FROM pg_catalog.pg_locks l"
                " WHERE NOT l.granted AND l.locktype = 'transactionid'"
                " AND l.pid = ("
                "   SELECT a.pid FROM pg_catalog.pg_stat_activity a"
                "   WHERE a.usename = $1"
                "   AND a.datname = current_database()"
                "   AND a.pid <> pg_backend_pid()"
                "   ORDER BY a.pid LIMIT 1"
                " )",
                login,
            )
            if pid is not None:
                return int(pid)
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"the {login} backend was never observed waiting "
                    "on the in-flight transaction's row lock"
                )
            await asyncio.sleep(_BARRIER_POLL_S)


async def _apply_node_update(
    database: AgentSiteDatabase,
    ids: dict[str, Any],
    *,
    node_id: UUID,
    props: dict[str, Any],
    key: str,
    expected_row_version: int = 1,
) -> UUID:
    """One real agent composition update through the product executor.

    Returns the public operation ID.  A second update of the same
    node in the same session passes expected_row_version + 1 (the
    real per-session row version the product enforces)."""
    async with _owner(database) as owner:
        capability = await owner.fetchrow(
            "SELECT created_at, expires_at FROM control.capability WHERE id = $1",
            ids["capability_id"],
        )
    assert capability is not None
    context = AgentCapabilityContext(
        capability_id=ids["capability_id"],
        site_id=ids["site_id"],
        workspace_id=ids["workspace_id"],
        delegator_id=ids["delegator_id"],
        scopes=frozenset(ids["scopes"]),
        created_at=capability["created_at"],
        expires_at=capability["expires_at"],
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")

    async def update_node(service: AgentCowContentModelService) -> Any:
        return await service.update_component_for_site(
            ids["site_id"],
            node_id,
            AgentUpdateCompositionNodeRequest(
                props=props,
                expected_row_version=expected_row_version,
            ),
        )

    try:
        result = await execute_agent_mutation(
            database=_CowPoolAdapter(agent_pool),
            context=context,
            key=key,
            digest=mutation_digest(
                method="PATCH",
                path=f"/sites/{ids['site_id']}/components/{node_id}",
                body=props,
            ),
            mutate=update_node,
            resource_type="composition_node",
            status_code=200,
            quota_kind="mutation",
            action="COMPONENT_UPDATED",
            method="PATCH",
        )
    finally:
        await agent_pool.close()
    assert result.operation_id is not None
    return UUID(str(result.operation_id))


async def _apply_one_heading_update(
    database: AgentSiteDatabase,
    ids: dict[str, Any],
    *,
    level: int,
    text: str,
    key: str,
    expected_row_version: int = 1,
) -> UUID:
    """One real agent update of the seeded heading node."""
    return await _apply_node_update(
        database,
        ids,
        node_id=ids["heading_id"],
        props={"level": level, "text": text},
        key=key,
        expected_row_version=expected_row_version,
    )


async def _seed_sibling_agent_workspace(
    database: AgentSiteDatabase, ids: dict[str, Any], *, title: str
) -> dict[str, Any]:
    """Owner fixture: a second workspace + capability on the SAME
    site (the two-workspaces-per-site C2 fact), same delegator."""
    workspace_id = uuid4()
    scopes = list(ids["scopes"])
    async with _owner(database) as owner:
        await owner.execute(
            "INSERT INTO control.workspace (id, site_id, created_by,"
            " delegator_id, title, delegation_preset, effective_scopes,"
            " version_facts, status, expires_at) VALUES ($1,$2,$3,$3,$4,'L4',"
            "$5::jsonb,"
            + _CURRENT_VERSION_FACTS
            + ",'ACTIVE', now()+interval '1 hour')",
            workspace_id,
            ids["site_id"],
            ids["delegator_id"],
            title,
            json.dumps(scopes),
        )
        token, public_id, secret_digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability (workspace_id, public_id,"
            " secret_digest, scopes, expires_at) VALUES ($1,$2,$3,$4::jsonb,"
            " now()+interval '30 minutes')",
            workspace_id,
            public_id,
            secret_digest,
            json.dumps(scopes),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    return {
        **{
            k: ids[k]
            for k in (
                "site_id",
                "delegator_id",
                "page_id",
                "section_id",
                "heading_id",
                "scopes",
            )
        },
        "workspace_id": UUID(str(workspace_id)),
        "capability_id": UUID(str(capability_id)),
    }


async def _public_u(database: AgentSiteDatabase, workspace_id: UUID) -> list[UUID]:
    async with _owner(database) as owner:
        executor = AsyncpgExecutor(owner)
        return list(
            await get_session_operations(executor, workspace_id, schema="content")
        )


async def _journal_rows(database: AgentSiteDatabase, workspace_id: UUID) -> list[Any]:
    async with _owner(database) as owner:
        return list(
            await owner.fetch(
                "SELECT * FROM audit.mutation_completion"
                " WHERE workspace_id = $1 ORDER BY occurred_at, operation_id",
                workspace_id,
            )
        )


async def _accept_durable_state(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    job_id: UUID,
    pending: list[UUID],
) -> dict[str, Any]:
    """The C5 rollback states as exact owner-readable facts."""
    async with _owner(database) as owner:
        revision = await owner.fetchval(
            "SELECT canonical_revision FROM control.site WHERE id = $1", site_id
        )
        promotion_count = await owner.fetchval("SELECT count(*) FROM audit.promotion")
        outbox_count = await owner.fetchval("SELECT count(*) FROM control.cache_outbox")
        workspace_row = await owner.fetchrow(
            "SELECT status, accepted_at, review_snapshot_id FROM"
            " control.workspace WHERE id = $1",
            workspace_id,
        )
        job_row = await owner.fetchrow(
            "SELECT status, error FROM control.review_job WHERE id = $1", job_id
        )
        manifest_count = await owner.fetchval(
            "SELECT count(*) FROM control.review_operation_manifest"
            " WHERE workspace_id = $1",
            workspace_id,
        )
    return {
        "canonical_revision": int(revision),
        "pending": list(pending),
        "promotion_count": int(promotion_count),
        "outbox_count": int(outbox_count),
        "workspace_status": str(workspace_row["status"]),
        "workspace_accepted_at": workspace_row["accepted_at"],
        "bound_snapshot": workspace_row["review_snapshot_id"],
        "job_status": str(job_row["status"]),
        "job_error": job_row["error"],
        "manifest_count": int(manifest_count),
    }


def _jsonb(value: Any) -> Any:
    """Decode fixture-connection JSONB text (canonical byte retention)."""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


@pytest.mark.asyncio
async def test_freeze_companion_exact_and_full_accept(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C1/C2: one real Agent freeze stores exactly one companion whose
    content is the ACTUAL public session state (two operations with
    their real dependency pair and real 078 identities), whose digest
    recomputes over the stored bytes, and whose exact approval the
    real accept worker promotes with an exact applied-ID receipt."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        # The actual public foundation state BEFORE the freeze: the
        # same getters the worker captures in its locked transaction.
        async with _owner(database) as owner:
            executor = AsyncpgExecutor(owner)
            operations = list(
                await get_session_operations(executor, ws, schema="content")
            )
            dependencies = list(
                await get_operation_dependencies(executor, ws, schema="content")
            )
            doc = await owner.fetchval(
                "SELECT control.slaif_review_operation_identities($1, $2, $3)",
                ws,
                site,
                operations,
            )
            if isinstance(doc, str):
                doc = json.loads(doc)
        assert len(operations) == 2
        identities = sorted(list(doc), key=lambda item: item["operation_id"])

        snapshot_id = await _freeze_workspace(database, ids, pool)
        async with _owner(database) as owner:
            stored_digest = await owner.fetchval(
                "SELECT digest::text FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
            manifest_count = await owner.fetchval(
                "SELECT count(*) FROM control.review_operation_manifest"
            )
            row = await owner.fetchrow(
                "SELECT * FROM control.review_operation_manifest"
                " WHERE snapshot_id = $1",
                snapshot_id,
            )
            journal = list(
                await owner.fetch(
                    "SELECT * FROM audit.mutation_completion"
                    " WHERE workspace_id = $1 ORDER BY operation_id::text",
                    ws,
                )
            )
        assert manifest_count == 1
        assert row is not None
        # Exact U: the public operations, canonically sorted.
        assert [str(operation) for operation in row["operation_ids"]] == sorted(
            str(operation) for operation in operations
        )
        # Exact foundation dependency pairs (unique, sorted).
        assert _jsonb(row["dependency_pairs"]) == sorted(
            {
                [str(depends_on), str(operation_id)]
                for depends_on, operation_id in dependencies
            }
        )
        # Exact trusted 078 identities, one per operation.
        stored_identities = _jsonb(row["completion_identities"])
        assert stored_identities == identities
        for identity in stored_identities:
            match = [
                row
                for row in journal
                if str(row["operation_id"]) == identity["operation_id"]
            ]
            assert len(match) == 1
            journal_row = match[0]
            assert str(journal_row["site_id"]) == str(site)
            assert str(journal_row["workspace_id"]) == str(ws)
            assert journal_row["family"] == identity["family"]
            assert journal_row["resource_type"] == identity["resource_type"]
            assert str(journal_row["resource_id"]) == identity["resource_id"]
            assert journal_row["request_identity"] == identity["request_identity"]
            assert journal_row["request_digest"] == identity["request_digest"]
            assert journal_row["disposition"] == identity["disposition"]
        # Binding derives from trusted stored state, not caller JSON.
        assert str(row["snapshot_id"]) == str(snapshot_id)
        assert str(row["site_id"]) == str(site)
        assert str(row["workspace_id"]) == str(ws)
        assert row["schema_version"] == "reviewed-operations/v1"
        assert row["snapshot_digest"] == stored_digest
        # The manifest digest recomputes over the STORED canonical
        # content with the product's own canonical digest expression.
        canonical = {
            "schema_version": "reviewed-operations/v1",
            "snapshot_id": str(snapshot_id),
            "snapshot_digest": stored_digest,
            "site_id": str(site),
            "workspace_id": str(ws),
            "operation_ids": [str(o) for o in row["operation_ids"]],
            "dependency_pairs": _jsonb(row["dependency_pairs"]),
            "completion_identities": _jsonb(row["completion_identities"]),
        }
        recomputed = await _owner_digest_recompute(database, canonical)
        assert recomputed == str(row["manifest_digest"])
        # The authorized read projection is exactly the stored content.
        read_doc = await _read_manifest(database, snapshot_id)
        assert read_doc == {
            "schema_version": "reviewed-operations/v1",
            "manifest_id": str(row["id"]),
            "manifest_digest": str(row["manifest_digest"]),
            "snapshot_digest": stored_digest,
            "site_id": str(site),
            "workspace_id": str(ws),
            "operation_ids": [str(o) for o in row["operation_ids"]],
            "dependency_pairs": _jsonb(row["dependency_pairs"]),
            "completion_identities": _jsonb(row["completion_identities"]),
        }

        # The exact successful whole-session acceptance.
        await _enqueue_bound_accept(database, ws, ids["delegator_id"])
        job = await _claim_accept(database, "binding-accept-1")
        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error

        async with _owner(database) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox = await owner.fetch("SELECT * FROM control.cache_outbox ORDER BY id")
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            created = await owner.fetchrow(
                "SELECT component_type, props FROM content.page_composition_base"
                " WHERE id = $1",
                ids["created_heading_id"],
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws,
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site,
            )
            journal_after = await owner.fetchval(
                "SELECT count(*) FROM audit.mutation_completion"
                " WHERE workspace_id = $1",
                ws,
            )
        # The append-only receipt carries the EXACT applied IDs and
        # both approval digests (the old count stays compatibility).
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == sorted(
            str(operation) for operation in operations
        )
        assert str(audit[0]["manifest_id"]) == str(row["id"])
        assert str(audit[0]["manifest_digest"]) == str(row["manifest_digest"])
        assert audit[0]["committed_operations"] == 2
        assert audit[0]["new_canonical_revision"] == 1
        assert str(audit[0]["snapshot_id"]) == str(snapshot_id)
        # The real promotion happened.
        assert revision == 1
        assert _jsonb(heading["props"])["level"] == 2
        assert created is not None
        assert created["component_type"] == "Heading"
        assert str(workspace["status"]) == "ACCEPTED"
        assert workspace["accepted_at"] is not None
        assert len(outbox) == 1
        # Completion history is retained, never rewritten.
        assert journal_after == 2
        # The public pending universe is empty through the real getter.
        assert await _public_u(database, ws) == []
    finally:
        await boundary.stop()
        await pool.close()


async def _owner_digest_recompute(
    database: AgentSiteDatabase, canonical: dict[str, Any]
) -> str:
    async with _owner(database) as owner:
        return str(
            await owner.fetchval(
                "SELECT encode(sha256(convert_to("
                "control.slaif_canonical_jsonb_text($1::jsonb), 'UTF8')), 'hex')",
                json.dumps(canonical),
            )
        )


@pytest.mark.asyncio
async def test_freeze_dedupe_replay_two_workspaces_and_empty_u(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C2/C4: an idempotent replay keeps ONE pending operation; two
    workspaces on the same site keep isolated U (the frozen workspace
    never captures the sibling's pending operations); a genuine
    empty-U freeze is legal and its no-op acceptance is exact."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    ws1 = ids["workspace_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        # Operation A + an idempotent replay (same key + digest):
        # exactly one pending operation, one journal row.
        op_a = await _apply_one_heading_update(
            database,
            ids,
            level=2,
            text="Dedupe heading",
            key="binding-dedupe-a",
        )
        replay = await _apply_one_heading_update(
            database,
            ids,
            level=2,
            text="Dedupe heading",
            key="binding-dedupe-a",
        )
        assert replay == op_a
        assert await _public_u(database, ws1) == [op_a]
        assert len(await _journal_rows(database, ws1)) == 1

        # Sibling workspace on the SAME site with its own pending op
        # on a DIFFERENT resource (the image node): promoting both
        # workspaces in sequence must not collide on one base row.
        ids2 = await _seed_sibling_agent_workspace(
            database, ids, title="Binding sibling workspace"
        )
        ws2 = ids2["workspace_id"]
        op_b = await _apply_node_update(
            database,
            ids2,
            node_id=ids["image_id"],
            props={"mediaId": str(ids["media_id"]), "alt": "Sibling alt"},
            key="binding-sibling-b",
        )

        # Freeze ws1: its U must be exactly {A} - the sibling's
        # pending operation on the same site is isolated.
        snapshot1 = await _freeze_workspace(database, ids, pool)
        manifest1 = await _read_manifest(database, snapshot1)
        assert manifest1 is not None
        assert manifest1["operation_ids"] == [str(op_a)]
        assert manifest1["dependency_pairs"] == []
        # ws2's operation is still pending in its own session.
        assert await _public_u(database, ws2) == [op_b]
        assert await _public_u(database, ws1) == [op_a]

        # Accept ws1 exactly; ws2 stays REVIEW-pending, untouched.
        await _enqueue_bound_accept(database, ws1, ids["delegator_id"])
        job1 = await _claim_accept(database, "binding-dedupe-accept-1")
        result1 = await run_accept_job(
            pool, _worker_settings(database), job1, media=boundary
        )
        assert result1.status == "SUCCEEDED", result1.error
        async with _owner(database) as owner:
            audit1 = await owner.fetch(
                "SELECT * FROM audit.promotion WHERE workspace_id = $1", ws1
            )
        assert len(audit1) == 1
        assert [str(o) for o in audit1[0]["applied_operation_ids"]] == [str(op_a)]
        assert str(audit1[0]["manifest_id"]) == str(manifest1["manifest_id"])
        assert await _public_u(database, ws2) == [op_b]
        assert (await _workspace_state(database, ws2))[0] == "ACTIVE"

        # Now the sibling: its U is exactly {B} (no leak from ws1).
        snapshot2 = await _freeze_workspace(database, ids2, pool)
        manifest2 = await _read_manifest(database, snapshot2)
        assert manifest2 is not None
        assert manifest2["operation_ids"] == [str(op_b)]
        await _enqueue_bound_accept(database, ws2, ids["delegator_id"])
        job2 = await _claim_accept(database, "binding-dedupe-accept-2")
        result2 = await run_accept_job(
            pool, _worker_settings(database), job2, media=boundary
        )
        assert result2.status == "SUCCEEDED", result2.error
        async with _owner(database) as owner:
            audit2 = await owner.fetch(
                "SELECT * FROM audit.promotion WHERE workspace_id = $1", ws2
            )
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            image = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["image_id"],
            )
        assert len(audit2) == 1
        assert [str(o) for o in audit2[0]["applied_operation_ids"]] == [str(op_b)]
        assert _jsonb(heading["props"])["level"] == 2
        assert _jsonb(image["props"])["alt"] == "Sibling alt"

        # A third same-site workspace with NO operations: the genuine
        # empty-U companion is legal and its acceptance is a no-op.
        ids3 = await _seed_sibling_agent_workspace(
            database, ids, title="Binding empty workspace"
        )
        ws3 = ids3["workspace_id"]
        snapshot3 = await _freeze_workspace(database, ids3, pool)
        manifest3 = await _read_manifest(database, snapshot3)
        assert manifest3 is not None
        assert manifest3["operation_ids"] == []
        assert manifest3["dependency_pairs"] == []
        assert manifest3["completion_identities"] == []
        await _enqueue_bound_accept(database, ws3, ids["delegator_id"])
        job3 = await _claim_accept(database, "binding-dedupe-accept-3")
        result3 = await run_accept_job(
            pool, _worker_settings(database), job3, media=boundary
        )
        assert result3.status == "SUCCEEDED", result3.error
        async with _owner(database) as owner:
            audit3 = await owner.fetch(
                "SELECT * FROM audit.promotion WHERE workspace_id = $1", ws3
            )
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
        assert len(audit3) == 1
        assert list(audit3[0]["applied_operation_ids"]) == []
        assert audit3[0]["committed_operations"] == 0
        assert str(audit3[0]["manifest_id"]) == str(manifest3["manifest_id"])
        assert _jsonb(heading["props"])["level"] == 2
        assert await _public_u(database, ws3) == []
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_freeze_failure_leaves_no_partial_state(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C3: a real freeze whose captured U carries a trusted journal
    negative fixture (one 078 completion row removed by the owner
    fixture, labeled) fails closed through the REAL worker definer:
    typed stable job code, no snapshot row, no companion row, workspace
    FREEZING (070/078 semantics), the pending session and the remaining
    journal history intact.  The legal recovery is then proven for
    real: the exact victim row is restored and a re-enqueued freeze on
    the FREEZING workspace with no live job completes to REVIEW."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        pending = await _public_u(database, ws)
        assert len(pending) == 2
        # Labeled trusted negative fixture: one completion journal row
        # is removed (owner-only DML).  The COW operation itself stays
        # pending, so the frozen capture sees a U member whose trusted
        # 078 provenance no longer exists.
        victim = pending[0]
        victim_row: dict[str, Any] = {}
        async with _owner(database) as owner:
            victim_record = await owner.fetchrow(
                "SELECT * FROM audit.mutation_completion WHERE operation_id = $1",
                victim,
            )
            assert victim_record is not None
            victim_row = dict(victim_record)
            await owner.execute(
                "DELETE FROM audit.mutation_completion WHERE operation_id = $1",
                victim,
            )
        rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
            ws,
            site,
            ids["delegator_id"],
        )
        assert len(rows) == 1
        job_id = UUID(str(rows[0]["job_id"]))
        claimed = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "binding-freeze-fail",
            _WORKER_KINDS,
        )
        assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job_id)
        result = await run_freeze_job(
            pool, _worker_settings(database), dict(claimed[0])
        )
        assert result.status == "FAILED", (result.status, result.error)
        assert str(result.error).startswith("MANIFEST_"), result.error

        async with _owner(database) as owner:
            snapshot_rows = await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
                ws,
            )
            manifest_rows = await owner.fetchval(
                "SELECT count(*) FROM control.review_operation_manifest"
                " WHERE workspace_id = $1",
                ws,
            )
            workspace_row = await owner.fetchrow(
                "SELECT status, review_snapshot_id FROM control.workspace"
                " WHERE id = $1",
                ws,
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            journal_left = await owner.fetch(
                "SELECT operation_id FROM audit.mutation_completion"
                " WHERE workspace_id = $1 ORDER BY operation_id::text",
                ws,
            )
        # No partial review state: nothing was committed.
        assert snapshot_rows == 0
        assert manifest_rows == 0
        assert workspace_row["review_snapshot_id"] is None
        # A failed semantic freeze leaves the workspace FREEZING with
        # no live job (070/078 semantics); recovery is a re-enqueue.
        assert str(workspace_row["status"]) == "FREEZING"
        # The job is terminal with the SAME stable code the worker
        # reported (no invented second failure).
        assert job_row["status"] == "FAILED"
        assert str(job_row["error"]) == str(result.error)
        # The pending session is intact (both operations still
        # pending through the public getter) and the remaining
        # journal history is preserved.
        assert await _public_u(database, ws) == pending
        assert [str(row["operation_id"]) for row in journal_left] == [
            str(operation) for operation in pending if operation != victim
        ]
        # Real recovery: restore the exact labeled victim row (same
        # values), re-enqueue the real freeze on the FREEZING
        # workspace with no live job, and run it to success.
        async with _owner(database) as owner:
            await owner.execute(
                "INSERT INTO audit.mutation_completion ("
                "operation_id, family, site_id, workspace_id, capability_id,"
                " human_user_id, request_identity, request_digest,"
                " resource_type, resource_id, disposition, schema_version,"
                " occurred_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                victim_row["operation_id"],
                victim_row["family"],
                victim_row["site_id"],
                victim_row["workspace_id"],
                victim_row["capability_id"],
                victim_row["human_user_id"],
                victim_row["request_identity"],
                victim_row["request_digest"],
                victim_row["resource_type"],
                victim_row["resource_id"],
                victim_row["disposition"],
                victim_row["schema_version"],
                victim_row["occurred_at"],
            )
        again = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
            ws,
            site,
            ids["delegator_id"],
        )
        assert len(again) == 1
        again_job_id = UUID(str(again[0]["job_id"]))
        re_claimed = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "binding-freeze-fail",
            _WORKER_KINDS,
        )
        assert len(re_claimed) == 1 and str(re_claimed[0]["id"]) == str(again_job_id)
        recovered = await run_freeze_job(
            pool, _worker_settings(database), dict(re_claimed[0])
        )
        assert recovered.status == "SUCCEEDED", (
            recovered.status,
            recovered.error,
        )
        async with _owner(database) as owner:
            snapshot_rows2 = await owner.fetch(
                "SELECT id FROM control.review_snapshot WHERE workspace_id = $1",
                ws,
            )
            manifest2 = await owner.fetchrow(
                "SELECT operation_ids FROM control.review_operation_manifest"
                " WHERE workspace_id = $1",
                ws,
            )
            workspace_row2 = await owner.fetchrow(
                "SELECT status, review_snapshot_id FROM control.workspace"
                " WHERE id = $1",
                ws,
            )
        assert len(snapshot_rows2) == 1
        assert manifest2 is not None
        # The repaired freeze captures the FULL U again (both ops).
        assert [str(op) for op in manifest2["operation_ids"]] == sorted(
            str(op) for op in pending
        )
        assert workspace_row2["review_snapshot_id"] is not None
        assert str(workspace_row2["status"]) == "REVIEW"
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_review_document_carries_companion_and_legacy_null(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R4: the authorized human review document carries the immutable
    companion manifest; a historical companion-less snapshot remains
    readable through the SAME document with manifest NULL (it is
    never acceptable, but its read/render contract is untouched)."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    control = ControlDatabase(_control_settings(database))
    await control.start()
    try:
        # (a) A real freeze: the document carries the exact companion.
        snapshot_id = await _freeze_workspace(database, ids, pool)
        stored = await _read_manifest(database, snapshot_id)
        assert stored is not None
        document = await control.human_agent_workspace_review_read(
            ws, site, ids["delegator_id"]
        )
        assert document is not None
        assert document["manifest"] == stored
        assert document["snapshot"]["id"] == str(snapshot_id)
        assert document["snapshot"]["digest"] == stored["snapshot_digest"]

        # (b) A historical companion-less COMPLETE snapshot on a
        # sibling workspace: readable, manifest NULL.
        ids2 = await _seed_sibling_agent_workspace(
            database, ids, title="Binding legacy workspace"
        )
        ws2 = ids2["workspace_id"]
        legacy_snapshot = uuid4()
        legacy_digest = "77" * 32
        async with _owner(database) as owner:
            await owner.execute(
                "INSERT INTO control.review_snapshot (id, workspace_id,"
                " site_id, status, revision_watermark, versions,"
                " normalized_state, validation_report, media_references,"
                " browser_evidence, payload, digest, created_by) VALUES"
                " ($1,$2,$3,'COMPLETE',0,'{}'::jsonb,'{}'::jsonb,"
                " '{}'::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb,"
                " $4,'legacy-fixture')",
                legacy_snapshot,
                ws2,
                site,
                legacy_digest,
            )
            await owner.execute(
                "UPDATE control.workspace SET status = 'REVIEW',"
                " review_snapshot_id = $1 WHERE id = $2",
                legacy_snapshot,
                ws2,
            )
        document2 = await control.human_agent_workspace_review_read(
            ws2, site, ids["delegator_id"]
        )
        assert document2 is not None
        assert document2["manifest"] is None
        assert document2["snapshot"]["id"] == str(legacy_snapshot)
        assert document2["snapshot"]["digest"] == legacy_digest
    finally:
        await control.stop()
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_denies_legacy_and_cross_workspace_manifest_digest(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """R4: at the real control accept route, a companion-less legacy
    snapshot and a REAL other-workspace companion digest are both a
    uniform, pairwise-indistinguishable 404 with no job created and
    no workspace state change (the gate is not bypassable and never
    fills a missing approval from mutable state)."""
    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site = ids["site_id"]
    ws1 = ids["workspace_id"]
    snapshot1 = await _seed_review_state(database, ids)
    manifest1 = await _read_manifest(database, snapshot1)
    assert manifest1 is not None

    # Sibling workspace with its own (empty) companion M2.
    ids2 = await _seed_sibling_agent_workspace(
        database, ids, title="Binding route sibling"
    )
    snapshot2 = await _seed_review_state(database, ids2)
    manifest2 = await _read_manifest(database, snapshot2)
    assert manifest2 is not None
    assert manifest2["manifest_digest"] != manifest1["manifest_digest"]

    # Historical companion-less workspace (legacy M-).
    ids3 = await _seed_sibling_agent_workspace(
        database, ids, title="Binding route legacy"
    )
    ws3 = ids3["workspace_id"]
    legacy_snapshot = uuid4()
    legacy_digest = "88" * 32
    async with _owner(database) as owner:
        await owner.execute(
            "INSERT INTO control.review_snapshot (id, workspace_id,"
            " site_id, status, revision_watermark, versions,"
            " normalized_state, validation_report, media_references,"
            " browser_evidence, payload, digest, created_by) VALUES"
            " ($1,$2,$3,'COMPLETE',0,'{}'::jsonb,'{}'::jsonb,"
            " '{}'::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb,"
            " $4,'legacy-fixture')",
            legacy_snapshot,
            ws3,
            site,
            legacy_digest,
        )
        await owner.execute(
            "UPDATE control.workspace SET status = 'REVIEW',"
            " review_snapshot_id = $1 WHERE id = $2",
            legacy_snapshot,
            ws3,
        )

    control = ControlDatabase(_control_settings(database))
    await control.start()
    try:
        issued = await control.human_session_service().create(ids["delegator_id"])
        control_app = create_control_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
        )
        async with control_app.router.lifespan_context(control_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=control_app),
                base_url="http://control-binding.test",
            ) as client:
                path = f"/api/control/v1/sites/{site}/workspaces/{{workspace}}/accept/"
                legacy_body = {
                    "snapshot_id": str(legacy_snapshot),
                    "digest": legacy_digest,
                    # A REAL digest, but of another workspace's
                    # companion: the binding must still refuse.
                    "manifest_digest": str(manifest1["manifest_digest"]),
                    "acknowledge_summary": True,
                }
                cross_body = {
                    "snapshot_id": str(snapshot1),
                    "digest": manifest1["snapshot_digest"],
                    "manifest_digest": str(manifest2["manifest_digest"]),
                    "acknowledge_summary": True,
                }
                legacy = await client.post(
                    path.format(workspace=ws3),
                    json=legacy_body,
                    headers=_accept_headers(issued),
                )
                cross = await client.post(
                    path.format(workspace=ws1),
                    json=cross_body,
                    headers=_accept_headers(issued),
                )
                assert legacy.status_code == 404, legacy.text
                assert cross.status_code == 404, cross.text
                # Pairwise indistinguishable from a plain not-found:
                # the stable envelope is byte-identical.
                assert _error_envelope(legacy) == _error_envelope(cross)

        async with _owner(database) as owner:
            jobs = await owner.fetch(
                "SELECT workspace_id FROM control.review_job WHERE job_kind = 'ACCEPT'"
            )
        assert len(jobs) == 0
        assert (await _workspace_state(database, ws3)) == (
            "REVIEW",
            legacy_snapshot,
        )
        assert (await _workspace_state(database, ws1)) == ("REVIEW", snapshot1)
    finally:
        await control.stop()


@pytest.mark.asyncio
async def test_accept_refuses_unreviewed_pending_operation(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C4/R5: no unreviewed pending operation may slip through between
    the accept preflight and the actual reviewer transaction.

    The client side: after the real freeze (workspace REVIEW), a new
    agent write through the real product executor is refused by the
    runtime itself (the workspace is no longer ACTIVE), so no pending
    operation can be created for a workspace under review.

    The enforcement side: the reviewer transaction re-verifies the
    live session AND the trusted 078 provenance of every approved
    operation INSIDE its own transaction, before any publication
    effect.  A labeled trusted negative fixture (owner deletion of
    one approved operation's journal row AFTER the freeze - the
    reverse of the freeze-time case) makes that member's trusted
    provenance missing at review time; the real accept worker must
    refuse inside the reviewer transaction with the stable
    provenance code, publish nothing, and leave the review intact.
    Restoring the exact row and running a FRESH accept then completes
    with the exact applied-ID receipt."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        approved = await _public_u(database, ws)
        assert len(approved) == 2
        snapshot_id = await _freeze_workspace(database, ids, pool)
        manifest = await _read_manifest(database, snapshot_id)
        assert manifest is not None
        assert sorted(str(o) for o in manifest["operation_ids"]) == sorted(
            str(o) for o in approved
        )

        # Client side: the runtime refuses a new write while the
        # workspace is under review (the actual gate that makes a
        # client-created unreviewed operation impossible).
        with pytest.raises(AgentMutationUnavailableError):
            await _apply_one_heading_update(
                database,
                ids,
                level=4,
                text="Unreviewed heading",
                key="binding-unreviewed-heading",
                expected_row_version=2,
            )
        assert await _public_u(database, ws) == approved
        assert len(await _journal_rows(database, ws)) == 2
        async with _owner(database) as owner:
            leftover = await owner.fetchval(
                "SELECT count(*) FROM control.agent_idempotency"
                " WHERE workspace_id = $1 AND idempotency_key = $2",
                ws,
                "binding-unreviewed-heading",
            )
        assert leftover == 0

        # The accept approval verifies (the preflight) and the job is
        # claimed; the reviewer transaction has not run yet.
        rows = await _enqueue_bound_accept(database, ws, ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, "binding-unreviewed-1")
        assert str(job["id"]) == str(job_id)

        # Labeled trusted negative fixture: AFTER the freeze, one
        # approved operation's trusted 078 journal row is removed by
        # the owner fixture.  Its COW operation stays pending; the
        # frozen U still names it, but its provenance no longer
        # exists at review time.
        victim = approved[0]
        victim_row: dict[str, Any] = {}
        async with _owner(database) as owner:
            victim_record = await owner.fetchrow(
                "SELECT * FROM audit.mutation_completion WHERE operation_id = $1",
                victim,
            )
            assert victim_record is not None
            victim_row = dict(victim_record)
            await owner.execute(
                "DELETE FROM audit.mutation_completion WHERE operation_id = $1",
                victim,
            )
            revision_before = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site,
            )

        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "FAILED", (result.status, result.error)
        # The refusal is the typed in-TX provenance verification, not
        # a generic validation or drift code.
        assert result.error == "PROVENANCE_VERIFICATION_FAILED", result.error

        async with _owner(database) as owner:
            revision_after = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site,
            )
            promotion_count = await owner.fetchval(
                "SELECT count(*) FROM audit.promotion"
            )
            outbox_count = await owner.fetchval(
                "SELECT count(*) FROM control.cache_outbox"
            )
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at, review_snapshot_id FROM"
                " control.workspace WHERE id = $1",
                ws,
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            journal_left = await owner.fetch(
                "SELECT operation_id FROM audit.mutation_completion"
                " WHERE workspace_id = $1 ORDER BY operation_id::text",
                ws,
            )
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
        # Nothing was published: the refusal stayed inside the
        # reviewer transaction.
        assert revision_after == revision_before
        assert promotion_count == 0
        assert outbox_count == 0
        assert str(workspace["status"]) == "REVIEW"
        assert workspace["accepted_at"] is None
        assert workspace["review_snapshot_id"] == snapshot_id
        assert job_row["status"] == "FAILED"
        assert str(job_row["error"]) == "PROVENANCE_VERIFICATION_FAILED"
        # The pending session is intact for the next review: BOTH
        # operations are still pending, and the remaining journal
        # history is preserved.
        assert await _public_u(database, ws) == approved
        assert [str(row["operation_id"]) for row in journal_left] == [
            str(operation) for operation in approved if operation != victim
        ]
        assert _jsonb(heading["props"])["level"] == 1

        # Real recovery: restore the exact victim row and run a
        # FRESH accept (the failed job is terminal; a new live job
        # carries the same exact approval).
        async with _owner(database) as owner:
            await owner.execute(
                "INSERT INTO audit.mutation_completion ("
                "operation_id, family, site_id, workspace_id, capability_id,"
                " human_user_id, request_identity, request_digest,"
                " resource_type, resource_id, disposition, schema_version,"
                " occurred_at) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                victim_row["operation_id"],
                victim_row["family"],
                victim_row["site_id"],
                victim_row["workspace_id"],
                victim_row["capability_id"],
                victim_row["human_user_id"],
                victim_row["request_identity"],
                victim_row["request_digest"],
                victim_row["resource_type"],
                victim_row["resource_id"],
                victim_row["disposition"],
                victim_row["schema_version"],
                victim_row["occurred_at"],
            )
        rows2 = await _enqueue_bound_accept(database, ws, ids["delegator_id"])
        assert len(rows2) == 1
        job2 = await _claim_accept(database, "binding-unreviewed-2")
        result2 = await run_accept_job(
            pool, _worker_settings(database), job2, media=boundary
        )
        assert result2.status == "SUCCEEDED", (
            result2.status,
            result2.error,
        )
        async with _owner(database) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == sorted(
            str(operation) for operation in approved
        )
        assert str(audit[0]["manifest_id"]) == str(manifest["manifest_id"])
        assert await _public_u(database, ws) == []
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_freeze_drains_inflight_mutation_and_denies_later_writes(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C4: real freeze vs REAL in-flight mutation, in the product's
    actual lock order.  The in-flight mutation (parked at the trusted
    journal barrier, inside its uncommitted COW transaction) holds
    the in-transaction row locks of the review pipeline; the real
    freeze enqueue is observed genuinely blocked on one of them
    (ungranted transaction-id lock in the real lock table).  When
    the barrier releases, the mutation commits, the blocked enqueue
    completes the FREEZING flip, and the real freeze worker captures
    the committed operation coherently (its U is exactly the drained
    operation).  Later writes are denied while the workspace is in
    review, and the drained operation then accepts exactly."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        # Trusted journal barrier (hold): the in-flight mutation parks
        # INSIDE its COW transaction at the real AFTER INSERT boundary.
        async with _completion_barrier(database, ws, "hold"):
            async with _barrier_lock_owner(database) as lock_owner:
                op_task = asyncio.create_task(
                    _apply_one_heading_update(
                        database,
                        ids,
                        level=2,
                        text="Inflight heading",
                        key="binding-inflight",
                    )
                )
                # Deterministic positioning: the mutation is in flight
                # and parked at the journal boundary.
                runtime_login = database.credentials["slaif_agent_runtime"][0]
                parked_pid = await _wait_for_parked_or_task_failure(
                    database, runtime_login, op_task
                )
                identity = await _backend_identity(database, parked_pid)
                assert identity == (database.name, runtime_login), identity

                # The real freeze enqueue starts while the mutation is
                # in flight: its first statement (the FREEZING flip)
                # blocks on the in-flight mutation's workspace row
                # lock - the real "freeze waits the in-flight
                # mutation" boundary.
                freeze_task = asyncio.create_task(
                    _control_call(
                        database,
                        "SELECT * FROM control.slaif_human_agent_workspace_freeze"
                        "($1,$2,$3)",
                        ws,
                        site,
                        ids["delegator_id"],
                    )
                )
                # Deterministic positioning: the real control backend
                # is observed holding an ungranted transaction-id
                # lock request - the row lock held by the in-flight
                # mutation's uncommitted transaction.
                control_login = database.credentials["slaif_control"][0]
                await _wait_for_transaction_lock_waiter(database, control_login)

                # Release the rendezvous: the mutation commits, which
                # unblocks the frozen enqueue's FREEZING flip.
                await lock_owner.fetchval(
                    "SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY
                )
                op_id = await op_task
                rows = await freeze_task
        assert len(rows) == 1
        job_id = UUID(str(rows[0]["job_id"]))
        claimed = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "binding-drain-freeze",
            _WORKER_KINDS,
        )
        assert len(claimed) == 1
        assert str(claimed[0]["id"]) == str(job_id)
        result = await run_freeze_job(
            pool, _worker_settings(database), dict(claimed[0])
        )
        assert result.status == "SUCCEEDED", (result.status, result.error)
        status, snapshot_id = await _workspace_state(database, ws)
        assert status == "REVIEW"
        assert snapshot_id is not None
        # The captured U contains the drained in-flight operation.
        manifest = await _read_manifest(database, snapshot_id)
        assert manifest is not None
        assert manifest["operation_ids"] == [str(op_id)]
        # The pending operation is still pending (no promotion yet).
        assert await _public_u(database, ws) == [op_id]
        async with _owner(database) as owner:
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
        assert _jsonb(heading["props"])["level"] == 1

        # Later writes are denied while the workspace is in review,
        # and change nothing.
        with pytest.raises(AgentMutationUnavailableError):
            await _apply_one_heading_update(
                database,
                ids,
                level=3,
                text="Post-review heading",
                key="binding-postreview",
            )
        assert await _public_u(database, ws) == [op_id]
        async with _owner(database) as owner:
            journal_count = await owner.fetchval(
                "SELECT count(*) FROM audit.mutation_completion"
                " WHERE workspace_id = $1",
                ws,
            )
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
        assert journal_count == 1
        assert _jsonb(heading["props"])["level"] == 1

        # The drained operation then accepts exactly.
        rows = await _enqueue_bound_accept(database, ws, ids["delegator_id"])
        job = await _claim_accept(database, "binding-drain-accept")
        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error
        async with _owner(database) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion")
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == [str(op_id)]
        assert _jsonb(heading["props"])["level"] == 2
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_rereview_multiple_snapshots_stale_approval_refused(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C4: a real discard ends the first review (workspace DISCARDED,
    the product's terminal review state) while the FIRST snapshot and
    companion bytes stay exactly immutable; a stale approval tab of
    the old snapshot is refused at the real route with no job; the
    product's fresh-workspace re-review path then freezes a second
    snapshot on the same site and accepts it exactly."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        # Snapshot 1 (two operations) and its companion.
        snapshot1 = await _freeze_workspace(database, ids, pool)
        manifest1 = await _read_manifest(database, snapshot1)
        assert manifest1 is not None
        async with _owner(database) as owner:
            snapshot1_row = await owner.fetchrow(
                "SELECT * FROM control.review_snapshot WHERE id = $1",
                snapshot1,
            )
            manifest1_row = await owner.fetchrow(
                "SELECT * FROM control.review_operation_manifest"
                " WHERE snapshot_id = $1",
                snapshot1,
            )

        # Real discard: the pending operations clear and the workspace
        # reaches the terminal DISCARDED review state; snapshot 1
        # stays bound and readable.
        discard = await _discard_claim_run(
            database,
            pool,
            workspace_id=ws,
            site_id=site,
            user_id=ids["delegator_id"],
        )
        assert discard.status == "SUCCEEDED", discard.error
        assert await _public_u(database, ws) == []
        status, bound = await _workspace_state(database, ws)
        assert status == "DISCARDED"
        assert bound == snapshot1
        # The first snapshot/companion bytes are exactly immutable.
        async with _owner(database) as owner:
            snapshot1_after = await owner.fetchrow(
                "SELECT * FROM control.review_snapshot WHERE id = $1",
                snapshot1,
            )
            manifest1_after = await owner.fetchrow(
                "SELECT * FROM control.review_operation_manifest"
                " WHERE snapshot_id = $1",
                snapshot1,
            )
        assert tuple(snapshot1_after.values()) == tuple(snapshot1_row.values())
        assert tuple(manifest1_after.values()) == tuple(manifest1_row.values())

        # Stale approval tab: the OLD snapshot's exact approval is
        # refused at the real route (the workspace is terminal) with
        # the not-in-review conflict and no job.
        control = ControlDatabase(_control_settings(database))
        await control.start()
        try:
            issued = await control.human_session_service().create(ids["delegator_id"])
            control_app = create_control_app(
                settings=ServiceSettings(mode=EnvironmentMode.TEST),
                database=control,
            )
            async with control_app.router.lifespan_context(control_app):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=control_app),
                    base_url="http://control-stale.test",
                ) as client:
                    stale = await client.post(
                        f"/api/control/v1/sites/{site}/workspaces/{ws}/accept/",
                        json={
                            "snapshot_id": str(snapshot1),
                            "digest": manifest1["snapshot_digest"],
                            "manifest_digest": str(manifest1["manifest_digest"]),
                            "acknowledge_summary": True,
                        },
                        headers=_accept_headers(issued),
                    )
                    assert stale.status_code == 409, stale.text
        finally:
            await control.stop()
        async with _owner(database) as owner:
            jobs = await owner.fetch(
                "SELECT id FROM control.review_job WHERE job_kind = 'ACCEPT'"
            )
        assert len(jobs) == 0

        # The product's fresh-workspace re-review path: a second
        # workspace on the same site carries the new operation.
        ids2 = await _seed_sibling_agent_workspace(
            database, ids, title="Binding rereview workspace"
        )
        ws2 = ids2["workspace_id"]
        op2 = await _apply_one_heading_update(
            database,
            ids2,
            level=5,
            text="Rereview heading",
            key="binding-rereview",
        )
        assert await _public_u(database, ws2) == [op2]

        # Snapshot 2 on the fresh workspace and its companion.
        snapshot2 = await _freeze_workspace(database, ids2, pool)
        assert snapshot2 != snapshot1
        manifest2 = await _read_manifest(database, snapshot2)
        assert manifest2 is not None
        assert manifest2["operation_ids"] == [str(op2)]

        # The fresh approval accepts exactly.
        await _enqueue_bound_accept(database, ws2, ids["delegator_id"])
        job = await _claim_accept(database, "binding-rereview-accept")
        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error
        async with _owner(database) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion")
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            snapshot1_final = await owner.fetchrow(
                "SELECT * FROM control.review_snapshot WHERE id = $1",
                snapshot1,
            )
            manifest1_final = await owner.fetchrow(
                "SELECT * FROM control.review_operation_manifest"
                " WHERE snapshot_id = $1",
                snapshot1,
            )
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == [str(op2)]
        assert str(audit[0]["manifest_id"]) == str(manifest2["manifest_id"])
        assert _jsonb(heading["props"])["level"] == 5
        # Through the whole second review (including the canonical
        # promotion), the first snapshot/companion bytes are still
        # exactly the original bytes.
        assert tuple(snapshot1_final.values()) == tuple(snapshot1_row.values())
        assert tuple(manifest1_final.values()) == tuple(manifest1_row.values())
    finally:
        await boundary.stop()
        await pool.close()


async def _accept_post_commit_fault_case(
    database: AgentSiteDatabase,
    tmp_path: Path,
    *,
    fault: str,
) -> None:
    """Shared C5 runner: the real accept transaction parks at the
    trusted promotion barrier AFTER the foundation promotion executed;
    the exact verified fixture backend is then cancelled or
    terminated by the disposable fixture administrator.  Every durable
    state must equal the pre-attempt facts, and the SAME job must
    re-claim to a real exactly-once promotion on the SAME pool."""
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    worker_login = database.credentials["slaif_review_worker"][0]
    try:
        snapshot_id = await _freeze_workspace(database, ids, pool)
        manifest = await _read_manifest(database, snapshot_id)
        assert manifest is not None
        rows = await _enqueue_bound_accept(database, ws, ids["delegator_id"])
        job_id = UUID(str(rows[0]["job_id"]))
        job = await _claim_accept(database, f"binding-c5-{fault}-1")
        assert str(job["id"]) == str(job_id)

        pending_before = await _public_u(database, ws)
        assert len(pending_before) == 2
        pre = await _accept_durable_state(
            database,
            workspace_id=ws,
            site_id=site,
            job_id=job_id,
            pending=pending_before,
        )

        async with _accept_barrier(database, ws):
            async with _c12_barrier_lock_owner(database):
                run_task = asyncio.create_task(
                    run_accept_job(
                        pool, _worker_settings(database), job, media=boundary
                    )
                )
                parked_pid = await _wait_for_c12_parked(database, worker_login)
                identity = await _backend_identity(database, parked_pid)
                assert identity == (database.name, worker_login), identity
                # The bounded administrator signal targets ONLY the
                # exact verified fixture backend.
                if fault == "cancel":
                    signaled = await database.administrator.fetchval(
                        "SELECT pg_cancel_backend($1)", parked_pid
                    )
                else:
                    signaled = await database.administrator.fetchval(
                        "SELECT pg_terminate_backend($1)", parked_pid
                    )
                assert signaled is True, "the fixture signal was refused"
                if fault == "terminate":
                    await _wait_for_backend_gone(database, parked_pid)
                result = await run_task
        assert result.status == "ROLLED_BACK", (
            result.status,
            result.error,
        )

        # Exact durable rollback: every state equals the pre-attempt
        # facts (the job re-queued itself under the same approval).
        post = await _accept_durable_state(
            database,
            workspace_id=ws,
            site_id=site,
            job_id=job_id,
            pending=await _public_u(database, ws),
        )
        assert post == {
            **pre,
            "workspace_status": "ACCEPT_QUEUED",
            "job_status": "CLAIMED",
        }, post
        async with _owner(database) as owner:
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site,
            )
        assert _jsonb(heading["props"])["level"] == 1
        assert revision == 0
        assert await _read_manifest(database, snapshot_id) == manifest

        # Safe retry: the SAME job re-claims (attempt 2) and the SAME
        # app/pool promotes for real, exactly once.
        await _age_heartbeat(database, job_id)
        retry = await _claim_accept(database, f"binding-c5-{fault}-2")
        assert str(retry["id"]) == str(job_id)
        assert retry["attempt_count"] == 2
        result = await run_accept_job(
            pool, _worker_settings(database), retry, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error
        async with _owner(database) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion")
            outbox = await owner.fetch("SELECT * FROM control.cache_outbox ORDER BY id")
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws,
            )
            job_row = await owner.fetchrow(
                "SELECT status, error FROM control.review_job WHERE id = $1",
                job_id,
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site,
            )
            heading = await owner.fetchrow(
                "SELECT props FROM content.page_composition_base WHERE id = $1",
                ids["heading_id"],
            )
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == sorted(
            str(operation) for operation in pending_before
        )
        assert str(audit[0]["manifest_id"]) == str(manifest["manifest_id"])
        assert str(audit[0]["manifest_digest"]) == str(manifest["manifest_digest"])
        assert audit[0]["committed_operations"] == 2
        assert len(outbox) == 1
        assert str(workspace["status"]) == "ACCEPTED"
        assert workspace["accepted_at"] is not None
        assert job_row["status"] == "SUCCEEDED"
        assert job_row["error"] is None
        assert revision == 1
        assert _jsonb(heading["props"])["level"] == 2
        assert await _public_u(database, ws) == []
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_accept_cancellation_after_commit_rolls_back_and_retries(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C5: a real PG cancellation of the exact parked accept backend
    (post foundation promotion, pre business commit) rolls every
    durable state back and the same job re-claims to a real
    exactly-once promotion."""
    await _accept_post_commit_fault_case(agent_site_database, tmp_path, fault="cancel")


@pytest.mark.asyncio
async def test_accept_backend_loss_after_commit_rolls_back_and_recovers(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C5: termination of the EXACT fixture-owned parked accept
    backend (post foundation promotion) rolls every durable state
    back and the SAME worker pool serves the real exactly-once retry
    (pool recovery after an owned connection loss)."""
    await _accept_post_commit_fault_case(
        agent_site_database, tmp_path, fault="terminate"
    )


@pytest.mark.asyncio
async def test_human_editor_content_type_patch_017_regression(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C2 + 017 repair: a real HUMAN-on-AGENT content-model PATCH
    (through the 017-defect function content.slaif_content_type_update,
    forward-only repaired at 079) produces exactly one human_editor
    trusted completion with real COW pending state, and the real
    freeze/accept promotes the canonical type with the exact
    applied-ID receipt."""
    database = agent_site_database
    media_root = tmp_path / "media"
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    _tok, ws_agent, _cap = await _seed_agent_workspace(
        database, site_id, human_id, ["site:read"], "017 regression workspace"
    )
    type_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.content_type_base "
            '(id,site_id,"key",labels,slug_pattern,status,'
            "definition_version,settings) VALUES "
            "($1,$2,'017-regression','{\"en\":\"Regression type\"}'::jsonb,"
            "'/017-regression/{slug}','ACTIVE',1,'{}'::jsonb)",
            type_id,
            site_id,
        )

    async with _editor_stack(database) as (control, client):
        session, csrf = await _human_session(control, human_id)
        updated = await client.patch(
            f"/api/editor/v1/sites/{site_id}/content-model/types/{type_id}",
            json={
                "labels": {"en": "Renamed regression type"},
                "expected_definition_version": 1,
            },
            headers=_editor_headers(session, csrf, "017-regression-patch", ws_agent),
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["labels"]["en"] == "Renamed regression type"
        assert updated.json()["id"] == str(type_id)

    # Real COW pending state + the trusted 078 completion, canonical
    # untouched while pending.
    pending = await _pending_operations(database, ws_agent)
    assert len(pending) == 1
    op = pending[0]
    rows = await _completion_rows(database, workspace_id=ws_agent)
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["disposition"] == "completed"
    assert row["family"] == "human_editor"
    assert str(row["operation_id"]) == str(op)
    assert str(row["resource_type"]) == "editor.sites"
    assert str(row["resource_id"]) == str(type_id)
    assert str(row["site_id"]) == str(site_id)
    assert str(row["workspace_id"]) == str(ws_agent)
    # Canonical type untouched while the edit is pending.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        canonical = await owner.fetchrow(
            "SELECT labels, definition_version FROM"
            " content.content_type_base WHERE id = $1",
            type_id,
        )
        change_rows = await owner.fetchval(
            "SELECT count(*) FROM content.content_type_changes WHERE session_id = $1",
            ws_agent,
        )
    assert _jsonb(canonical["labels"])["en"] == "Regression type"
    assert canonical["definition_version"] == 1
    assert change_rows == 1

    # The real freeze/accept of this human_editor operation.
    ids = {
        "workspace_id": ws_agent,
        "site_id": site_id,
        "delegator_id": human_id,
    }
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        snapshot_id = await _freeze_workspace(database, ids, pool)
        manifest = await _read_manifest(database, snapshot_id)
        assert manifest is not None
        assert manifest["operation_ids"] == [str(op)]
        # The companion identity carries the human_editor family
        # trusted completion (the 017 repair path's journal binding).
        identity = manifest["completion_identities"][0]
        assert identity["operation_id"] == str(op)
        assert identity["family"] == "human_editor"
        assert identity["resource_type"] == "editor.sites"
        assert identity["resource_id"] == str(type_id)

        rows = await _enqueue_bound_accept(database, ws_agent, human_id)
        job = await _claim_accept(database, "binding-017-accept")
        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion")
            canonical = await owner.fetchrow(
                "SELECT labels, definition_version FROM"
                " content.content_type_base WHERE id = $1",
                type_id,
            )
            journal = await owner.fetchval(
                "SELECT count(*) FROM audit.mutation_completion"
                " WHERE workspace_id = $1",
                ws_agent,
            )
            change_rows = await owner.fetchval(
                "SELECT count(*) FROM content.content_type_changes"
                " WHERE session_id = $1",
                ws_agent,
            )
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == [str(op)]
        assert str(audit[0]["manifest_id"]) == str(manifest["manifest_id"])
        assert str(audit[0]["manifest_digest"]) == str(manifest["manifest_digest"])
        assert _jsonb(canonical["labels"])["en"] == "Renamed regression type"
        assert canonical["definition_version"] == 2
        assert journal == 1
        assert change_rows == 0
        assert await _pending_operations(database, ws_agent) == []
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_mixed_family_superseding_netzero_multirow_freeze_accept(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C2: one real freeze of a MIXED-FAMILY session on one site: the
    Agent creates page P (op1) and page P2 (op5, the second promoted
    row), and the delegating human edits the SAME page P inside the
    same agent workspace (HUMAN-on-AGENT): ops 2-3 supersede the
    title and op4 reverts it to the original title (net-zero).  The
    companion's U is exactly the five public operations with the real
    same-resource dependency chain, and the real accept promotes both
    pages exactly once with the exact applied-ID receipt; the
    net-zero page keeps its original title."""
    database = agent_site_database
    media_root = tmp_path / "media"
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    human_id = seeded["delegator_id"]
    token, ws_agent, _capability_id = await _seed_agent_workspace(
        database,
        site_id,
        human_id,
        ["site:read", "page:create", "page:read"],
        "binding mixed-family workspace",
    )
    original_title = "bf-mix-p1 page"
    async with _agent_client(database) as client:
        created1 = await _create_page(client, token, key="bf-mix-p1", slug="bf-mix-p1")
        assert created1.status_code == 201, created1.text
        op1 = UUID(created1.json()["operation_id"])
        page1 = UUID(created1.json()["record"]["id"])

    # HUMAN-on-AGENT: the delegating human edits the SAME page P in
    # the same workspace - a superseding title chain that ends in a
    # net-zero revert to the original title.
    async with _editor_stack(database) as (control, editor):
        session, csrf = await _human_session(control, human_id)
        for version, title in ((1, "Mixed v2"), (2, "Mixed v3"), (3, original_title)):
            updated = await editor.patch(
                f"/api/editor/v1/sites/{site_id}/pages/{page1}",
                json={"title": title, "expected_row_version": version},
                headers=_editor_headers(
                    session, csrf, f"bf-mix-human-{version}", ws_agent
                ),
            )
            assert updated.status_code == 200, updated.text

    async with _agent_client(database) as client:
        created2 = await _create_page(client, token, key="bf-mix-p2", slug="bf-mix-p2")
        assert created2.status_code == 201, created2.text
        op5 = UUID(created2.json()["operation_id"])
        page2 = UUID(created2.json()["record"]["id"])

    # The exact human operations are their durable reservations (the
    # Editor response is the resource record, not an operation field).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        human_ops = list(
            await owner.fetch(
                "SELECT idempotency_key, operation_id "
                "FROM control.human_editor_idempotency "
                "WHERE workspace_id = $1 ORDER BY idempotency_key",
                ws_agent,
            )
        )
    assert [row["idempotency_key"] for row in human_ops] == [
        "bf-mix-human-1",
        "bf-mix-human-2",
        "bf-mix-human-3",
    ]
    op2, op3, op4 = (UUID(str(row["operation_id"])) for row in human_ops)
    expected = {op1, op2, op3, op4, op5}
    pending = await _pending_operations(database, ws_agent)
    assert {operation for operation in pending} == expected

    rows = await _completion_rows(database, workspace_id=ws_agent)
    assert len(rows) == 5, rows
    by_op = {str(row["operation_id"]): row for row in rows}
    for op in (op2, op3, op4):
        assert by_op[str(op)]["family"] == "human_editor"
        assert by_op[str(op)]["resource_type"] == "editor.sites"
        assert by_op[str(op)]["resource_id"] == page1
    assert by_op[str(op1)]["family"] == "agent"
    assert by_op[str(op1)]["resource_type"] == "page"
    assert by_op[str(op1)]["resource_id"] == page1
    assert by_op[str(op5)]["family"] == "agent"
    assert by_op[str(op5)]["resource_type"] == "page"
    assert by_op[str(op5)]["resource_id"] == page2

    ids = {
        "workspace_id": ws_agent,
        "site_id": site_id,
        "delegator_id": human_id,
    }
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        snapshot_id = await _freeze_workspace(database, ids, pool)
        manifest = await _read_manifest(database, snapshot_id)
        assert manifest is not None
        # Exact U: all five operations, canonically sorted.
        assert manifest["operation_ids"] == sorted(str(op) for op in expected)
        # The real same-resource dependency closure: the qualified
        # foundation records every later same-row operation against
        # every earlier one (create -> edits, the superseding chain),
        # and the second page create is independent.
        row_ops = [str(op1), str(op2), str(op3), str(op4)]
        expected_pairs = {
            (earlier, later)
            for i, earlier in enumerate(row_ops)
            for later in row_ops[i + 1 :]
        }
        assert {tuple(pair) for pair in manifest["dependency_pairs"]} == expected_pairs
        assert len(manifest["completion_identities"]) == 5

        rows = await _enqueue_bound_accept(database, ws_agent, human_id)
        job = await _claim_accept(database, "binding-mixed-accept")
        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            page1_row = await owner.fetchrow(
                "SELECT title FROM content.page_base WHERE id = $1", page1
            )
            page2_row = await owner.fetchrow(
                "SELECT title FROM content.page_base WHERE id = $1", page2
            )
            journal = await owner.fetchval(
                "SELECT count(*) FROM audit.mutation_completion "
                "WHERE workspace_id = $1",
                ws_agent,
            )
        # One exact whole-session receipt for the mixed families.
        assert len(audit) == 1
        assert [
            str(operation) for operation in audit[0]["applied_operation_ids"]
        ] == sorted(str(op) for op in expected)
        assert str(audit[0]["manifest_id"]) == str(manifest["manifest_id"])
        assert str(audit[0]["manifest_digest"]) == str(manifest["manifest_digest"])
        assert audit[0]["committed_operations"] == 5
        # The net-zero page keeps its ORIGINAL title; the second page
        # row is promoted once.
        assert page1_row is not None
        assert page1_row["title"] == original_title
        assert page2_row is not None
        assert page2_row["title"] == "bf-mix-p2 page"
        # History is retained: all five completions, nothing rewritten.
        assert journal == 5
        assert await _pending_operations(database, ws_agent) == []
    finally:
        await boundary.stop()
        await pool.close()


async def _seed_proposal_cow_operation(
    database: AgentSiteDatabase, site_id: UUID, workspace_id: UUID
) -> tuple[UUID, dict[str, Any]]:
    """Honest fixture boundary for the trusted-internal form.

    The proposed side effect carries no public API and no 078
    completion (external effects remain proposed/suppressed until
    publication).  The owner fixture binds the workspace COW session
    exactly as the foundation write trigger requires (app.session_id
    + app.operation_id) and invokes the existing trusted constructor;
    the row identity is read back through the existing product list
    contract - no foundation-table coupling, no invented surface.
    Returns the COW operation id (the app.operation_id the change row
    carries) and the listed row.
    """
    proposal_operation_id = uuid4()
    payload = {"scope": "binding-trusted-internal-fixture"}
    async with _owner(database) as owner:
        await owner.execute(
            "SELECT set_config('app.session_id', $1::text, false),"
            " set_config('app.operation_id', $2::text, false)",
            str(workspace_id),
            str(proposal_operation_id),
        )
        try:
            await owner.execute(
                "SELECT content.slaif_proposed_side_effect_create($1,$2,"
                " 'cache_purge',$3::jsonb)",
                site_id,
                workspace_id,
                json.dumps(payload),
            )
            listed = await owner.fetch(
                "SELECT * FROM content.slaif_proposed_side_effect_list($1,$2)",
                site_id,
                workspace_id,
            )
        finally:
            await owner.execute(
                "SELECT set_config('app.session_id', '', false),"
                " set_config('app.operation_id', '', false)"
            )
    matching = [
        row
        for row in listed
        if row["kind"] == "cache_purge"
        and (
            row["payload"]
            if isinstance(row["payload"], dict)
            else json.loads(row["payload"])
        )
        == payload
    ]
    assert len(matching) == 1, [dict(row) for row in listed]
    return proposal_operation_id, dict(matching[0])


@pytest.mark.asyncio
async def test_freeze_accept_with_trusted_internal_proposal_operation(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C2/C3: a real freeze of a workspace whose public U mixes BOTH
    verified provenance forms - two 078-journaled mutation operations
    and one trusted-internal proposed-side-effect operation (labeled
    fixture, no public proposal API) - stores exactly one companion
    carrying the nine-field and the three-field records, recomputes
    its digest over the stored bytes, and the real accept worker
    promotes the whole session with ONE exact receipt covering ALL
    THREE applied operations; the internal row materializes to the
    committed base with its identity retained."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        proposal_op, proposal_row = await _seed_proposal_cow_operation(
            database, site, ws
        )
        payload = {"scope": "binding-trusted-internal-fixture"}
        pending = await _public_u(database, ws)
        # The proposal COW operation is a public U member (the
        # foundation getter unions the trusted-internal changes rows)
        # on top of the two mutation operations.
        assert len(pending) == 3, [str(o) for o in pending]
        assert str(proposal_op) in {str(o) for o in pending}
        assert str(proposal_op) not in {
            str(r["operation_id"]) for r in await _journal_rows(database, ws)
        }

        snapshot_id = await _freeze_workspace(database, ids, pool)
        async with _owner(database) as owner:
            stored_digest = await owner.fetchval(
                "SELECT digest::text FROM control.review_snapshot WHERE id = $1",
                snapshot_id,
            )
            manifest_count = await owner.fetchval(
                "SELECT count(*) FROM control.review_operation_manifest"
            )
            row = await owner.fetchrow(
                "SELECT * FROM control.review_operation_manifest"
                " WHERE snapshot_id = $1",
                snapshot_id,
            )
            journal = list(
                await owner.fetch(
                    "SELECT * FROM audit.mutation_completion"
                    " WHERE workspace_id = $1 ORDER BY operation_id::text",
                    ws,
                )
            )
        assert manifest_count == 1
        assert row is not None
        assert [str(o) for o in row["operation_ids"]] == sorted(str(o) for o in pending)
        stored_identities = _jsonb(row["completion_identities"])
        assert len(stored_identities) == 3
        by_op = {rec["operation_id"]: rec for rec in stored_identities}
        assert set(by_op) == {str(o) for o in pending}, sorted(by_op)
        # The trusted-internal record: exactly the three-field typed
        # form, nothing more (no forgeable metadata).
        assert by_op[str(proposal_op)] == {
            "operation_id": str(proposal_op),
            "resource_types": ["proposed_side_effect"],
            "disposition": "trusted_internal",
        }
        # The two mutation records: field-for-field the actual 078
        # journal rows.
        assert len(journal) == 2
        for jrow in journal:
            identity = by_op[str(jrow["operation_id"])]
            assert set(identity) == {
                "operation_id",
                "family",
                "principal_type",
                "principal_id",
                "request_identity",
                "request_digest",
                "resource_type",
                "resource_id",
                "disposition",
            }
            assert str(jrow["site_id"]) == str(site)
            assert str(jrow["workspace_id"]) == str(ws)
            assert jrow["family"] == identity["family"]
            assert jrow["resource_type"] == identity["resource_type"]
            assert str(jrow["resource_id"]) == identity["resource_id"]
            assert jrow["request_identity"] == identity["request_identity"]
            assert jrow["request_digest"] == identity["request_digest"]
            assert jrow["disposition"] == identity["disposition"]
        # Digest recomputes over the stored canonical content.
        canonical = {
            "schema_version": "reviewed-operations/v1",
            "snapshot_id": str(snapshot_id),
            "snapshot_digest": stored_digest,
            "site_id": str(site),
            "workspace_id": str(ws),
            "operation_ids": [str(o) for o in row["operation_ids"]],
            "dependency_pairs": _jsonb(row["dependency_pairs"]),
            "completion_identities": stored_identities,
        }
        recomputed = await _owner_digest_recompute(database, canonical)
        assert recomputed == str(row["manifest_digest"])

        # The exact successful whole-session acceptance.
        await _enqueue_bound_accept(database, ws, ids["delegator_id"])
        job = await _claim_accept(database, "binding-internal-accept")
        result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert result.status == "SUCCEEDED", result.error

        async with _owner(database) as owner:
            audit = await owner.fetch("SELECT * FROM audit.promotion ORDER BY id")
            outbox = await owner.fetch("SELECT * FROM control.cache_outbox ORDER BY id")
            workspace = await owner.fetchrow(
                "SELECT status, accepted_at FROM control.workspace WHERE id = $1",
                ws,
            )
            revision = await owner.fetchval(
                "SELECT canonical_revision FROM control.site WHERE id = $1",
                site,
            )
            listed_after = await owner.fetch(
                "SELECT * FROM content.slaif_proposed_side_effect_list($1,$2)",
                site,
                ws,
            )
        # One exact receipt for the whole session: ALL THREE applied
        # operations, including the trusted-internal one.
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == sorted(
            str(o) for o in pending
        )
        assert str(audit[0]["manifest_id"]) == str(row["id"])
        assert str(audit[0]["manifest_digest"]) == str(row["manifest_digest"])
        assert audit[0]["committed_operations"] == 3
        assert audit[0]["new_canonical_revision"] == 1
        assert str(audit[0]["snapshot_id"]) == str(snapshot_id)
        assert revision == 1
        assert str(workspace["status"]) == "ACCEPTED"
        assert workspace["accepted_at"] is not None
        assert len(outbox) == 1
        # The trusted-internal row materialized to the committed base
        # with its identity retained (commit upserts by row id).
        matching_after = [
            r
            for r in listed_after
            if r["kind"] == "cache_purge"
            and (
                r["payload"]
                if isinstance(r["payload"], dict)
                else json.loads(r["payload"])
            )
            == payload
        ]
        assert len(matching_after) == 1, [dict(r) for r in listed_after]
        assert str(matching_after[0]["id"]) == str(proposal_row["id"])
        # The public pending universe is empty through the real getter.
        assert await _public_u(database, ws) == []
    finally:
        await boundary.stop()
        await pool.close()


@pytest.mark.asyncio
async def test_writer_refuses_forged_internal_record_for_mutation_operation(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """C4: the trusted completion writer refuses a FORGED
    trusted-internal record.  The real freeze is enqueued and claimed
    first (workspace genuinely FREEZING, no live run), and the
    worker-shaped row is built through the same definer + Python
    builder path the worker uses in its locked transaction.  One
    078-journaled mutation operation is relabeled trusted-internal:
    it carries mutation-table COW rows, so the definer's typed
    internal verification raises the stable PROVENANCE_CONFLICT
    (P0003) before any snapshot/companion write.  No partial state
    survives, and the legitimate real freeze job then completes to
    REVIEW with the exact un-forged companion."""
    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=True)
    ws, site = ids["workspace_id"], ids["site_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        pending = await _public_u(database, ws)
        assert len(pending) == 2
        rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
            ws,
            site,
            ids["delegator_id"],
        )
        assert len(rows) == 1
        job_id = UUID(str(rows[0]["job_id"]))
        claimed = await _worker_call(
            database,
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            "binding-forged-fixture",
            _WORKER_KINDS,
        )
        assert len(claimed) == 1 and str(claimed[0]["id"]) == str(job_id)

        # Worker-shaped row + the real capture (the same definer and
        # Python builder path the freeze worker uses).
        async with _owner(database) as owner:
            executor = AsyncpgExecutor(owner)
            operations = list(
                await get_session_operations(executor, ws, schema="content")
            )
            dependencies = list(
                await get_operation_dependencies(executor, ws, schema="content")
            )
            doc = await owner.fetchval(
                "SELECT control.slaif_review_workspace_state($1)", ws
            )
            row_doc = build_snapshot_document(
                doc,
                created_by="binding-forged-fixture",
                browser_evidence=[],
                cancelled_runs=[],
            )
            identities_doc = await owner.fetchval(
                "SELECT control.slaif_review_operation_identities($1,$2,$3)",
                ws,
                site,
                operations,
            )
        if isinstance(identities_doc, (bytes, bytearray)):
            identities_doc = identities_doc.decode("utf-8")
        if isinstance(identities_doc, str):
            identities_doc = json.loads(identities_doc)
        identities = list(identities_doc)
        assert len(identities) == 2
        # FORGE: relabel one 078-journaled mutation operation as
        # trusted-internal (it actually carries mutation-table COW
        # rows; no trusted-internal row exists for it).
        victim = str(operations[0])
        forged = [
            {
                "operation_id": victim,
                "resource_types": ["proposed_side_effect"],
                "disposition": "trusted_internal",
            }
            if identity["operation_id"] == victim
            else identity
            for identity in identities
        ]
        manifest = build_operation_manifest(
            workspace_id=ws,
            site_id=site,
            operations=list(operations),
            dependencies=list(dependencies),
            completion_identities=forged,
        )
        with pytest.raises(asyncpg.PostgresError) as refusal:
            async with _owner(database) as owner:
                await owner.fetchval(
                    "SELECT control.slaif_review_snapshot_complete_with_manifest"
                    "($1, $2, $3)",
                    ws,
                    canonical_json(row_doc),
                    manifest,
                )
        assert refusal.value.sqlstate == "P0003"
        assert refusal.value.message == "PROVENANCE_CONFLICT"
        # No partial review state from the refused writer call.
        async with _owner(database) as owner:
            snapshot_rows = await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
                ws,
            )
            manifest_rows = await owner.fetchval(
                "SELECT count(*) FROM control.review_operation_manifest"
                " WHERE workspace_id = $1",
                ws,
            )
            workspace_row = await owner.fetchrow(
                "SELECT status, review_snapshot_id FROM control.workspace"
                " WHERE id = $1",
                ws,
            )
        assert snapshot_rows == 0
        assert manifest_rows == 0
        assert workspace_row["review_snapshot_id"] is None
        assert str(workspace_row["status"]) == "FREEZING"
        # The pending session is untouched.
        assert await _public_u(database, ws) == pending
        # Legitimate recovery: the real claimed freeze job completes
        # to REVIEW with the exact un-forged companion.
        result = await run_freeze_job(
            pool, _worker_settings(database), dict(claimed[0])
        )
        assert result.status == "SUCCEEDED", (result.status, result.error)
        status, bound = await _workspace_state(database, ws)
        assert status == "REVIEW" and bound is not None
        async with _owner(database) as owner:
            row = await owner.fetchrow(
                "SELECT * FROM control.review_operation_manifest"
                " WHERE workspace_id = $1",
                ws,
            )
            stored_digest = await owner.fetchval(
                "SELECT digest::text FROM control.review_snapshot WHERE id = $1",
                bound,
            )
        assert row is not None
        assert [str(o) for o in row["operation_ids"]] == sorted(str(o) for o in pending)
        stored_identities = _jsonb(row["completion_identities"])
        assert len(stored_identities) == 2
        # The stored companion carries ONLY the genuine nine-field
        # records (this workspace has no trusted-internal operations).
        assert all(
            set(rec)
            == {
                "operation_id",
                "family",
                "principal_type",
                "principal_id",
                "request_identity",
                "request_digest",
                "resource_type",
                "resource_id",
                "disposition",
            }
            for rec in stored_identities
        ), stored_identities
        assert sorted(rec["operation_id"] for rec in stored_identities) == sorted(
            identity["operation_id"] for identity in identities
        )
        canonical = {
            "schema_version": "reviewed-operations/v1",
            "snapshot_id": str(bound),
            "snapshot_digest": stored_digest,
            "site_id": str(site),
            "workspace_id": str(ws),
            "operation_ids": [str(o) for o in row["operation_ids"]],
            "dependency_pairs": _jsonb(row["dependency_pairs"]),
            "completion_identities": stored_identities,
        }
        recomputed = await _owner_digest_recompute(database, canonical)
        assert recomputed == str(row["manifest_digest"])
    finally:
        await boundary.stop()
        await pool.close()

"""083-13-a/b: bounded heading-props row effect pilot (migration 080_001).

Real runtime evidence for the actual mutation boundary of a successful
changed heading-props write through both trusted editorial surfaces:

- the Agent HTTP path (062 ``content.slaif_agent_component_update``);
- the Human-on-Agent Editor HTTP path (060
  ``content.slaif_composition_node_update``).

Every case runs on the owned fixture through the real HTTP envelopes,
real COW sessions, real reservations/journals and (where the canonical
row moves) the real freeze + human acceptance job lifecycle.  Public
surfaces only: the canonical content projection (view read without a
COW session GUC), the real HTTP records, the typed public conflict and
operation inspection (``CowReviewer``) and the product-owned
journals/control state.  No private foundation storage reads and no
owner writes to canonical rows anywhere in this module.  The 083-13-b
additions instrument the real boundary with fixture-only trusted test
objects (an AFTER INSERT journal barrier with a same-transaction
staged-effect witness, and a design-validator wrapper that parks the
named request at its real call) that are installed and removed inside
each test; they add no product surface, no grant and no production
test interface.

Pilot boundary (explicit, preserved by test):
- only ``Heading`` writes whose props actually changed in the write
  record a fact, decided on the actual same-statement image pair (the
  Agent definer's own no-effect short-circuit; the Editor's captured
  ``prior``/``post`` pair, scoped to the session's own
  ``actor_type = 'AGENT'`` workspace); unchanged-props and
  structural-only Editor writes, every other component type, every
  other mutation family and the ordinary Human workspace path keep
  their legacy behavior and record nothing;
- no fact commits unbound: the deferred constraint trigger refuses a
  missing or mismatched 078 completion at the real commit boundary
  and rolls back the staged COW change and the fact together (proved
  by a real runtime-role transaction and by the late-failure and
  cancellation rollbacks of the real HTTP envelopes);
- the Editor write contract is observed, not hardened (no version
  predicate): a stale Editor write is NOT refused by the boundary, and
  its fact still captures the exact DML image in the real COW view,
  even when the earlier in-command read saw another version;
- the Agent row-version guard is not by itself proof of all old-row
  bytes (a concurrent committed change between the pre-read and the
  UPDATE is rejected, but the guard proves the version, not the full
  pre-image); the exact pre-image comes from the same-statement
  ``prior``/``post`` capture under the statement's shared snapshot;
- historical heading writes (pre-080) are unknown, never backfilled:
  an old workspace without facts proves nothing about its history.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import re
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import (
    AgentDatabaseMode,
    AgentDatabaseSettings,
)
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
)
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.config import (
    EditorDatabaseMode,
    EditorDatabaseSettings,
)
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.review_worker.accept_job import MediaBoundary
from slaif_agent_site.review_worker.discard_job import run_discard_job
from sqlalchemy.exc import DBAPIError
from test_freeze_review_snapshot import (
    _accept_claim_run,
    _create_workspace,
    _freeze_claim_run,
    _public_conflicts,
    _public_operations,
    _worker_pool,
)
from test_human_agent_editor_workspace import _create_agent_workspace
from test_real_human_accept import (
    _AGGON2,
    _media_settings,
    _seed_site,
)
from test_real_human_discard import (
    _claim_discard,
    _enqueue_discard,
    _worker_settings,
)

_SCHEMA_VERSION = "heading-row-effect/v1"
_SCOPES = [
    "site:read",
    "page:read",
    "composition:read",
    "component-structure:create",
    "component-content-props:write",
    "component-variant:write",
]
_DENY_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)
# ---------------------------------------------------------------------------
# 083-13-b fixture-only instrumentation (trusted test objects, installed
# and removed inside each test; no product surface, no grant change, no
# production test interface)
# ---------------------------------------------------------------------------

_BARRIER_LOCK_KEY = 8313105
_RACE_LOCK_KEY = 8313106
_RENDEZVOUS_TIMEOUT_S = 30.0
_POLL_S = 0.05

_BARRIER_TABLE_SQL = """
CREATE TABLE control.h13b_completion_barrier (
    workspace_id uuid PRIMARY KEY,
    mode text NOT NULL CHECK (mode IN ('fail', 'cancel'))
)
"""

_BARRIER_FUNCTION_SQL = (
    """
CREATE FUNCTION control.slaif_h13b_completion_barrier()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog AS $fn$
DECLARE
    h13b_mode text;
    staged_props jsonb;
    staged_rv integer;
    fact_after jsonb;
BEGIN
    SELECT b.mode INTO h13b_mode
    FROM control.h13b_completion_barrier b
    WHERE b.workspace_id = NEW.workspace_id;
    IF h13b_mode IS NULL THEN
        RETURN NEW;
    END IF;
    -- Same-transaction witness, before the rendezvous: the heading fact
    -- for this operation is staged, and its after image matches the
    -- staged COW row this transaction itself sees.
    SELECT f.props_after INTO fact_after
    FROM audit.heading_row_effect f
    WHERE f.operation_id = NEW.operation_id;
    IF fact_after IS NULL THEN
        RAISE EXCEPTION 'H13B_BARRIER_NO_STAGED_FACT'
            USING ERRCODE = 'P0001';
    END IF;
    SELECT c.props, c.row_version INTO staged_props, staged_rv
    FROM content.page_composition c
    WHERE c.id = NEW.resource_id;
    IF staged_rv IS NULL OR staged_props IS DISTINCT FROM fact_after THEN
        RAISE EXCEPTION 'H13B_BARRIER_NO_STAGED_ROW'
            USING ERRCODE = 'P0001';
    END IF;
    PERFORM pg_advisory_xact_lock("""
    + str(_BARRIER_LOCK_KEY)
    + """);
    IF h13b_mode = 'fail' THEN
        RAISE EXCEPTION 'H13B_COMPLETION_LATE_FAILURE'
            USING ERRCODE = 'P0001';
    END IF;
    RETURN NEW;
END
$fn$
"""
)

_BARRIER_TRIGGER_SQL = """
CREATE TRIGGER h13b_completion_barrier_trg
AFTER INSERT ON audit.mutation_completion
FOR EACH ROW EXECUTE FUNCTION control.slaif_h13b_completion_barrier()
"""

_BARRIER_DROP_SQL = (
    "DROP TRIGGER h13b_completion_barrier_trg ON audit.mutation_completion",
    "DROP FUNCTION control.slaif_h13b_completion_barrier()",
    "DROP TABLE control.h13b_completion_barrier",
)


@asynccontextmanager
async def _h13b_completion_barrier(
    database: AgentSiteDatabase, workspace_id: UUID, mode: str
) -> AsyncIterator[None]:
    """Install the trusted test-only AFTER INSERT journal barrier.

    Owner objects only, committed before the request, removed in
    ``finally`` even on test failure.  With no barrier row for the
    workspace the trigger is a no-op, so the SAME app can serve the
    exactly-once retry.
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await owner.execute(_BARRIER_TABLE_SQL)
            await owner.execute(_BARRIER_FUNCTION_SQL)
            await owner.execute(_BARRIER_TRIGGER_SQL)
            await owner.execute(
                "INSERT INTO control.h13b_completion_barrier"
                " (workspace_id, mode) VALUES ($1, $2)",
                workspace_id,
                mode,
            )
    try:
        yield
    finally:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            async with owner.transaction():
                for statement in _BARRIER_DROP_SQL:
                    await owner.execute(statement)


@asynccontextmanager
async def _h13b_lock_owner(database: AgentSiteDatabase, key: int) -> AsyncIterator[Any]:
    """Hold the rendezvous session lock on an owner connection.

    Yields the holding connection; the test releases the lock explicitly
    at the failure point.  The final unlock is idempotent cleanup for
    leak paths (a session lock also dies with the connection).
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.fetchval("SELECT pg_advisory_lock($1)", key)
        try:
            yield owner
        finally:
            await owner.fetchval("SELECT pg_advisory_unlock($1)", key)


async def _h13b_wait_parked(database: AgentSiteDatabase, key: int, login: str) -> int:
    """Bounded, real-state wait for the named runtime backend to park at
    the rendezvous.  The pending lock request can only appear AFTER the
    instrumented statement has executed, so this is deterministic
    positioning, not a sleep oracle.  A single-bigint advisory key maps
    in ``pg_locks`` to ``classid`` = high 32 bits, ``objid`` = low 32
    bits, ``objsubid`` = 1, and advisory locks are local per database.
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        deadline = time.monotonic() + _RENDEZVOUS_TIMEOUT_S
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
                key,
                login,
            )
            if pid is not None:
                return int(pid)
            if time.monotonic() >= deadline:
                raise AssertionError(
                    f"h13b: the runtime backend for login {login!r} never "
                    "parked at the rendezvous"
                )
            await asyncio.sleep(_POLL_S)


async def _h13b_parked_lock_order(
    database: AgentSiteDatabase,
    pid: int,
    *,
    workspace_id: UUID,
    site_id: UUID,
    park_key: int,
) -> tuple[int, str | None, int, int]:
    """Granted workspace locks + pending rendezvous request of the parked
    backend (owner view; advisory keys are database-local).

    Returns (workspace_granted, workspace_mode, page_granted,
    park_pending).  The Agent definer's structural lock (the 050 body's
    exact statements) takes the workspace key in shared mode plus the
    page-structure key in exclusive mode before the in-command read.  The
    Editor definer itself takes no structural lock, but the Human-on-Agent
    request's workspace assert (state-changing) holds the same workspace
    key in exclusive mode, so the parked Editor backend shows a workspace
    lock but no page-structure lock.
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        sql = (
            """
            WITH k AS (
                SELECT hashtextextended($2::text, 280) AS shared_key,
                       hashtextextended($2::text || chr(58) || $3::text
                           || chr(58) || 'page-structure', 994) AS page_key,
                       """
            + str(park_key)
            + """::bigint AS park_key
            )
            SELECT
                count(*) FILTER (
                    WHERE l.granted AND l.objsubid = 1
                      AND l.classid = ((k.shared_key >> 32) & 4294967295)::oid
                      AND l.objid = (k.shared_key & 4294967295)::oid
                ) AS workspace_granted,
                max(l.mode) FILTER (
                    WHERE l.granted AND l.objsubid = 1
                      AND l.classid = ((k.shared_key >> 32) & 4294967295)::oid
                      AND l.objid = (k.shared_key & 4294967295)::oid
                ) AS workspace_mode,
                count(*) FILTER (
                    WHERE l.granted AND l.objsubid = 1
                      AND l.classid = ((k.page_key >> 32) & 4294967295)::oid
                      AND l.objid = (k.page_key & 4294967295)::oid
                ) AS page_granted,
                count(*) FILTER (
                    WHERE NOT l.granted AND l.objsubid = 1
                      AND l.classid = ((k.park_key >> 32) & 4294967295)::oid
                      AND l.objid = (k.park_key & 4294967295)::oid
                ) AS park_pending
            FROM pg_locks l, k
            WHERE l.pid = $1
              AND l.database = (
                  SELECT oid FROM pg_catalog.pg_database
                  WHERE datname = current_database()
              )
            """
        )
        row = await owner.fetchrow(sql, pid, str(workspace_id), str(site_id))
    return (
        int(row["workspace_granted"]),
        str(row["workspace_mode"]) if row["workspace_mode"] is not None else None,
        int(row["page_granted"]),
        int(row["park_pending"]),
    )


async def _h13b_parked_xid(database: AgentSiteDatabase, pid: int) -> int:
    """The parked backend's own open transaction id (owner view of its
    granted ``transactionid`` ExclusiveLock row)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        xid = await owner.fetchval(
            "SELECT l.transactionid"
            " FROM pg_catalog.pg_locks l"
            " WHERE l.pid = $1"
            " AND l.locktype = 'transactionid'"
            " AND l.granted"
            " AND l.mode = 'ExclusiveLock'",
            pid,
        )
    assert xid is not None, "parked backend has no open transaction"
    return int(xid)


async def _h13b_resolved_order(
    database: AgentSiteDatabase,
    parked_pid: int,
    sibling_task: asyncio.Task[tuple[Any, UUID]],
    *,
    reviewer_login: str,
) -> tuple[str, int | None]:
    """Bounded real-state observation of the RESOLVED order between the
    parked command and the sibling's real freeze job (the materializer
    blocking statement is the same on both routes).

    Returns exactly one of:
    - ``("reviewer-waiting", reviewer_pid)``: the review job's real
      reviewer backend shows the exact native blocking edge on the
      parked backend's open transaction (a non-granted
      ``transactionid`` ShareLock on the parked xid, the native display
      of the reviewer's blocked site-row ``FOR UPDATE`` in the 076
      workspace-state materializer).  The reviewer can only proceed
      once the parked command's transaction ends, so the command's
      DML + commit is deterministically ordered BEFORE the blocked
      statement and every publication after it.
    - ``("published-first", None)``: the review job's task completed
      while the command was still parked: no wait edge exists on that
      route, so the job's effect is ordered BEFORE the released
      command's DML.

    The ten-second product lock budget is deliberately NOT the oracle:
    only the observed lock edge or the completed real job decides.
    """

    parked_xid = await _h13b_parked_xid(database, parked_pid)
    deadline = time.monotonic() + _RENDEZVOUS_TIMEOUT_S
    while True:
        if sibling_task.done():
            return "published-first", None
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            reviewer_pid = await owner.fetchval(
                # transactionid lock rows carry database = 0 in
                # pg_locks, so the database must not be filtered.
                "SELECT l.pid"
                " FROM pg_catalog.pg_locks l"
                " JOIN pg_catalog.pg_stat_activity a ON a.pid = l.pid"
                " WHERE l.locktype = 'transactionid'"
                " AND l.mode = 'ShareLock'"
                " AND NOT l.granted"
                " AND l.transactionid = $1"
                " AND a.usename = $2"
                " ORDER BY l.pid LIMIT 1",
                parked_xid,
                reviewer_login,
            )
        if reviewer_pid is not None:
            return "reviewer-waiting", int(reviewer_pid)
        if time.monotonic() >= deadline:
            raise AssertionError(
                "h13b: neither the exact reviewer blocking edge on the "
                f"parked xid {parked_xid} nor the real acceptance "
                "completion became observable within the bounded wait"
            )
        await asyncio.sleep(_POLL_S)


async def _h13b_durable_state(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    heading: UUID,
    family: str,
) -> dict[str, Any]:
    """Owner snapshot of the exact durable states a rollback must
    restore: the view row, the public pending operations, the heading
    facts, the family reservation, the family audit and the completion
    journal."""
    if family == "agent":
        reservation_sql = (
            "SELECT row_to_json(t)::text FROM control.agent_idempotency t"
            " WHERE t.workspace_id = $1 ORDER BY 1"
        )
        audit_sql = (
            "SELECT row_to_json(t)::text FROM audit.agent_mutation t"
            " WHERE t.workspace_id = $1 ORDER BY 1"
        )
    else:
        reservation_sql = (
            "SELECT row_to_json(t)::text"
            " FROM control.human_editor_idempotency t"
            " WHERE t.workspace_id = $1 ORDER BY 1"
        )
        audit_sql = (
            "SELECT row_to_json(t)::text FROM audit.human_editor_mutation t"
            " WHERE t.workspace_id = $1 ORDER BY 1"
        )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        view = await owner.fetchrow(
            "SELECT props::text, row_version FROM content.page_composition"
            " WHERE id = $1",
            heading,
        )
        reservations = tuple(
            str(r[0]) for r in await owner.fetch(reservation_sql, workspace_id)
        )
        audit = tuple(str(r[0]) for r in await owner.fetch(audit_sql, workspace_id))
        journal = tuple(
            str(r[0])
            for r in await owner.fetch(
                "SELECT row_to_json(t)::text FROM audit.mutation_completion t"
                " WHERE t.workspace_id = $1 ORDER BY 1",
                workspace_id,
            )
        )
        facts = tuple(
            str(r[0])
            for r in await owner.fetch(
                "SELECT row_to_json(t)::text FROM audit.heading_row_effect t"
                " WHERE t.component_id = $1 ORDER BY 1",
                heading,
            )
        )
    operations = await _public_operations(database, workspace_id)
    return {
        "view": (view["props"], view["row_version"]),
        "reservations": reservations,
        "audit": audit,
        "journal": journal,
        "facts": facts,
        "operations": tuple(sorted(str(op) for op in operations)),
    }


_VALIDATOR_REGPROC = (
    "content.slaif_agent_component_validate_design"
    "(uuid,uuid,uuid,text,text,uuid,text,jsonb,jsonb,boolean)"
)


def _race_park_block(workspace_id: UUID, heading: UUID) -> str:
    """The fixture-only park inserted after the real validator's BEGIN:
    it preserves the real call and parks the named workspace's exact
    request at the design-validator boundary (after the in-command read,
    before the view update) until the test releases the rendezvous."""
    return f"""
    IF current_setting('app.session_id', true) = '{workspace_id}'
       AND p_node_id = '{heading}' THEN
        PERFORM pg_advisory_xact_lock({_RACE_LOCK_KEY});
    END IF;
"""


@asynccontextmanager
async def _h13b_race_park(
    database: AgentSiteDatabase, *, workspace_id: UUID, heading: UUID
) -> AsyncIterator[None]:
    """Install the fixture-only wrapper around the REAL design validator.

    The original definition is fetched from the live catalog, the park
    block is inserted immediately after its BEGIN, and the original
    bytes are re-installed in ``finally`` (ownership and grants are
    unchanged: the owner re-emits its own function).
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        original_ddl = await owner.fetchval(
            "SELECT pg_get_functiondef($1::regprocedure)", _VALIDATOR_REGPROC
        )
        original_body = await owner.fetchval(
            "SELECT p.prosrc"
            " FROM pg_proc p"
            " JOIN pg_namespace n ON n.oid = p.pronamespace"
            " WHERE n.nspname = 'content'"
            " AND p.proname = 'slaif_agent_component_validate_design'"
        )
        assert original_ddl is not None, "validator definition missing"
        assert original_body is not None, "validator body missing"
        # The stored body keeps its original indentation, so anchor on a
        # line that is exactly BEGIN (allowing leading/trailing blanks)
        # and insert the park after that line's newline.
        match = re.search(r"^[ \t]*BEGIN[ \t]*\r?\n", original_body, re.MULTILINE)
        assert match is not None, "validator body BEGIN anchor not found"
        insert_at = match.end()
        parked_body = (
            original_body[:insert_at]
            + _race_park_block(workspace_id, heading)
            + original_body[insert_at:]
        )
        # pg_get_functiondef re-quotes the body with its own tag, so the
        # stored prosrc is a verbatim substring of the DDL; swap the body
        # in place (independent of whatever quote tag is emitted).
        if original_ddl.count(original_body) != 1:
            raise AssertionError(
                "validator body not found exactly once in function DDL"
            )
        await owner.execute(original_ddl.replace(original_body, parked_body, 1) + ";")
    try:
        yield
    finally:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                original_ddl.replace(
                    "CREATE FUNCTION ", "CREATE OR REPLACE FUNCTION ", 1
                )
            )


async def _backend_info(
    database: AgentSiteDatabase, pid: int
) -> tuple[str, str] | None:
    """Owner-visible identity of one backend (state/query are redacted
    for foreign backends, so the identity proof uses the fixture
    administrator's owner connection)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT datname, usename FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
    if row is None:
        return None
    return str(row["datname"]), str(row["usename"])


# ---------------------------------------------------------------------------
# shared helpers (public surfaces only)
# ---------------------------------------------------------------------------


async def _new_capability(owner: Any, workspace_id: UUID) -> str:
    """One fixture capability (trusted rows) with the real bearer token."""

    token, public_id, digest = generate_capability_token()
    await owner.execute(
        "INSERT INTO control.capability (workspace_id, public_id, secret_digest,"
        " scopes, expires_at) VALUES ($1,$2,$3,$4::jsonb,"
        " now() + interval '30 minutes')",
        workspace_id,
        public_id,
        digest,
        json.dumps(_SCOPES),
    )
    return token


async def _canonical_projection(
    database: AgentSiteDatabase, component_id: UUID
) -> dict[str, Any]:
    """The public canonical content projection (no COW session GUC)."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT id, site_id, page_id, component_type, slot_key, order_key,"
            " props, row_version, updated_at"
            " FROM content.page_composition WHERE id = $1",
            component_id,
        )
    assert row is not None
    result = dict(row)
    if isinstance(result.get("props"), str):
        result["props"] = json.loads(result["props"])
    return result


async def _heading_facts(
    database: AgentSiteDatabase,
    component_id: UUID,
    workspace_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """The product-owned facts (owner read, fixture verification)."""

    query = (
        "SELECT operation_id, schema_version, family, mutation_kind,"
        " site_id, workspace_id, component_id, row_version_before,"
        " row_version_after, props_before, props_after, capability_id,"
        " human_user_id, occurred_at"
        " FROM audit.heading_row_effect WHERE component_id = $1"
    )
    args: list[Any] = [component_id]
    if workspace_id is not None:
        query += " AND workspace_id = $2"
        args.append(workspace_id)
    query += " ORDER BY row_version_before"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(query, *args)
    result: list[dict[str, Any]] = []
    for row in rows:
        fact = dict(row)
        for column in ("props_before", "props_after"):
            if isinstance(fact[column], str):
                fact[column] = json.loads(fact[column])
        result.append(fact)
    return result


async def _journal_rows(
    database: AgentSiteDatabase, *operation_ids: UUID
) -> list[dict[str, Any]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT operation_id, family, resource_type, resource_id,"
            " disposition FROM audit.mutation_completion"
            " WHERE operation_id = ANY($1::uuid[]) ORDER BY operation_id",
            list(operation_ids),
        )
    return [dict(row) for row in rows]


# The real-command race tests hold one live request at its real design
# validator across the sibling REAL freeze and the real acceptance up
# to the resolved-order observation point (the exact native blocking
# edge, or the acceptance completion on routes without that edge).
# The race test apps are given the maximum product-allowed command and
# lock budgets (product defaults unchanged) so the fixture pause
# cannot cancel the command before its UPDATE runs after release; the
# park window is additionally guarded by a wall-clock assertion.
_RACE_PARK_BUDGET = {
    "command_timeout_seconds": 30,
    "statement_timeout_ms": 30000,
    "lock_timeout_ms": 10000,
    "idle_transaction_timeout_ms": 30000,
}
_RACE_PARK_BUDGET_SECONDS = 8.0


def _agent_settings(
    database: AgentSiteDatabase, *, race_park: bool = False
) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    settings = AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-083-13a-heading-agent",
    )
    if race_park:
        settings = settings.model_copy(update=dict(_RACE_PARK_BUDGET))
    return settings


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-083-13a-heading-control",
    )


def _editor_db_settings(
    database: AgentSiteDatabase, *, race_park: bool = False
) -> EditorDatabaseSettings:
    login, password = database.credentials["slaif_editor_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    settings = EditorDatabaseSettings(
        mode=EditorDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-083-13a-heading-editor",
    )
    if race_park:
        settings = settings.model_copy(update=dict(_RACE_PARK_BUDGET))
    return settings


async def _agent_patch(
    database: AgentSiteDatabase,
    token: str,
    heading: UUID,
    props: dict[str, Any],
    *,
    expected_row_version: int,
    idempotency_key: str,
) -> httpx.Response:
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://agent.test",
            timeout=60,
        ) as client:
            return await client.patch(
                f"/api/agent/v1/components/{heading}",
                json={
                    "props": props,
                    "expected_row_version": expected_row_version,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": idempotency_key,
                },
            )


@pytest.mark.asyncio
async def test_agent_heading_patches_record_exact_row_effects(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Agent path: two same-resource writes keep BOTH exact transitions."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]
    del site_id, delegator_id

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws1)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws1,
        )

    A = await _canonical_projection(database, heading)
    assert A["props"] == {"level": 1, "text": "Accept"}
    assert A["row_version"] == 1

    r1 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "H1"},
        expected_row_version=1,
        idempotency_key="13a-agent-1",
    )
    assert r1.status_code == 200, r1.text
    op1 = UUID(str(r1.json()["operation_id"]))

    r2 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "H2"},
        expected_row_version=2,
        idempotency_key="13a-agent-2",
    )
    assert r2.status_code == 200, r2.text
    op2 = UUID(str(r2.json()["operation_id"]))
    assert op2 != op1

    # Both transitions retained, in order, with the exact DML images.
    facts = await _heading_facts(database, heading, ws1)
    assert len(facts) == 2
    f1, f2 = facts
    for fact in facts:
        assert fact["schema_version"] == _SCHEMA_VERSION
        assert fact["family"] == "agent"
        assert fact["mutation_kind"] == "heading_props"
        assert fact["site_id"] == ids["site_id"]
        assert fact["workspace_id"] == ws1
        assert fact["component_id"] == heading
        assert fact["capability_id"] == capability_id
        assert fact["human_user_id"] is None
        assert fact["row_version_after"] == fact["row_version_before"] + 1
    assert f1["operation_id"] == op1
    assert (f1["row_version_before"], f1["row_version_after"]) == (1, 2)
    assert f1["props_before"] == A["props"]
    assert f1["props_after"] == {"level": 2, "text": "H1"}
    assert f2["operation_id"] == op2
    assert (f2["row_version_before"], f2["row_version_after"]) == (2, 3)
    assert f2["props_before"] == f1["props_after"]
    assert f2["props_after"] == {"level": 2, "text": "H2"}

    # Same-transaction trusted completion binding: every fact operation
    # journaled exactly once, disposition completed, same resource.
    journal = await _journal_rows(database, op1, op2)
    assert len(journal) == 2
    by_op = {row["operation_id"]: row for row in journal}
    assert set(by_op) == {op1, op2}
    for row in journal:
        assert row["family"] == "agent"
        assert row["resource_type"] == "composition_node"
        assert row["resource_id"] == heading
        assert row["disposition"] == "completed"

    # The effective row shows the final value; the canonical row still
    # shows the pre-workspace value (no publication happened).
    view = await _canonical_projection(database, heading)
    assert view["props"] == A["props"]


@pytest.mark.asyncio
async def test_editor_human_on_agent_heading_patch_records_and_replay_is_inert(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Human-on-Agent Editor path: human principal from the real
    reservation, wire contract preserved, replay adds no second fact."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    # The seeded workspace is a HUMAN workspace; the Human-on-Agent
    # editor path requires a real AGENT workspace (product trusted
    # create).  role_pool is max_size=1: never hold a connection while
    # the helper acquires the same pool.
    owner_pool = await database.role_pool("slaif_owner")
    ws_agent = await _create_agent_workspace(
        owner_pool,
        site_id=site_id,
        delegator_id=delegator_id,
        title="13a heading effects agent workspace",
    )
    await owner_pool.close()

    A = await _canonical_projection(database, heading)

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        await control.start()
        await editor.start()
        session = await control.human_session_service().create(delegator_id)
        token = session.token.get_secret_value()
        csrf = session.csrf_token.get_secret_value()

        def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
            base = {
                "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
                "x-csrf-token": csrf,
                "x-editor-workspace": str(ws_agent),
            }
            return {**base, **(extra or {})}

        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            r1 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 3, "text": "E1"}},
                headers=_headers({"Idempotency-Key": "13a-editor-1"}),
            )
            assert r1.status_code == 200, r1.text
            rec1 = r1.json()
            # Pre-080 wire contract preserved: the Editor record omits
            # row_version (maps to the fixed 1), never the actual row.
            assert rec1["row_version"] == 1
            assert rec1["props"] == {"level": 3, "text": "E1"}

            # Replay: the stored body is returned; the definer never
            # re-runs, so no second fact.
            r1r = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 3, "text": "E1"}},
                headers=_headers({"Idempotency-Key": "13a-editor-1"}),
            )
            assert r1r.status_code == 200
            assert r1r.json() == rec1
    finally:
        await editor.stop()
        await control.stop()

    facts = await _heading_facts(database, heading, ws_agent)
    assert len(facts) == 1
    fact = facts[0]
    assert fact["schema_version"] == _SCHEMA_VERSION
    assert fact["family"] == "human_editor"
    assert fact["mutation_kind"] == "heading_props"
    assert fact["site_id"] == site_id
    assert fact["workspace_id"] == ws_agent
    assert fact["component_id"] == heading
    assert fact["capability_id"] is None
    # The human principal comes from the actual in-progress reservation
    # row (the session's delegator), never from caller-supplied values.
    assert fact["human_user_id"] == delegator_id
    assert (fact["row_version_before"], fact["row_version_after"]) == (1, 2)
    assert fact["props_before"] == A["props"]
    assert fact["props_after"] == {"level": 3, "text": "E1"}

    # Same-transaction trusted completion for the editor family.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        journal_op = await owner.fetchval(
            "SELECT operation_id FROM audit.mutation_completion"
            " WHERE family = 'human_editor'"
            " AND resource_id = $1",
            heading,
        )
    assert journal_op is not None
    assert UUID(str(journal_op)) == fact["operation_id"]


@pytest.mark.asyncio
async def test_no_effect_and_late_refusal_leave_no_fact(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Genuine no-effect and genuine late refusal: rollback/no-effect
    semantics leave NO effect fact; the corrected retry records once."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws1)

    # 1. HTTP-level no-effect: identical props complete with the
    #    explicit trusted no-effect disposition and NO fact.
    r0 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 1, "text": "Accept"},
        expected_row_version=1,
        idempotency_key="13a-noeffect",
    )
    assert r0.status_code == 200, r0.text
    rec0 = r0.json()["record"]
    assert rec0["props"] == {"level": 1, "text": "Accept"}
    assert rec0["row_version"] == 1
    no_effect_ops = await _journal_rows_for_family(database, "agent", heading)
    assert [row["disposition"] for row in no_effect_ops] == ["no_effect"]
    assert await _heading_facts(database, heading, ws1) == []

    # 2. A real first write, then a late request at the STALE version:
    #    refused, rolled back, no fact and no completion for it.
    r1 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "Real1"},
        expected_row_version=1,
        idempotency_key="13a-late-1",
    )
    assert r1.status_code == 200, r1.text
    op1 = UUID(str(r1.json()["operation_id"]))

    r_stale = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "Late"},
        expected_row_version=1,
        idempotency_key="13a-late-2",
    )
    assert r_stale.status_code == 409, r_stale.text

    # The stale request left no durable trace: its reservation rolled
    # back with the refused mutation, it journaled nothing, and the
    # effective row is untouched.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        stale_reservation = await owner.fetchval(
            "SELECT count(*) FROM control.agent_idempotency WHERE idempotency_key = $1",
            "13a-late-2",
        )
    assert stale_reservation == 0
    facts = await _heading_facts(database, heading, ws1)
    assert [f["operation_id"] for f in facts] == [op1]
    assert facts[0]["props_after"] == {"level": 2, "text": "Real1"}
    journal = await _journal_rows(database, op1)
    assert [row["disposition"] for row in journal] == ["completed"]
    view = await _canonical_projection(database, heading)
    assert view["props"] == {"level": 1, "text": "Accept"}

    # 3. The corrected retry at the actual version records exactly once.
    r2 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "Real2"},
        expected_row_version=2,
        idempotency_key="13a-late-3",
    )
    assert r2.status_code == 200, r2.text
    op2 = UUID(str(r2.json()["operation_id"]))
    facts = await _heading_facts(database, heading, ws1)
    assert [f["operation_id"] for f in facts] == [op1, op2]
    assert facts[1]["props_before"] == {"level": 2, "text": "Real1"}
    assert facts[1]["props_after"] == {"level": 2, "text": "Real2"}


async def _journal_rows_for_family(
    database: AgentSiteDatabase, family: str, resource_id: UUID
) -> list[dict[str, Any]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        rows = await owner.fetch(
            "SELECT operation_id, family, resource_id, disposition"
            " FROM audit.mutation_completion"
            " WHERE family = $1 AND resource_id = $2"
            " ORDER BY operation_id",
            family,
            resource_id,
        )
    return [dict(row) for row in rows]


@pytest.mark.asyncio
async def test_first_touch_conflict_control_case(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 3 control: both same-site first touches committed before the
    winner is accepted; the four distinct sources are each observed
    through a supported read path, the typed public conflict is exact,
    and both same-resource transitions keep their facts."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        A = await _canonical_projection(database, heading)
        assert A["props"] == {"level": 1, "text": "Accept"}
        assert A["row_version"] == 1

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            token1 = await _new_capability(owner, ws1)
            ws2, _cap2 = await _create_workspace(
                owner, site_id, delegator_id, "13a conflict W2"
            )
            token2 = await _new_capability(owner, ws2)

        # W1 first touch (real HTTP), then W2 first touch (real HTTP) -
        # BOTH committed before the winner is accepted.
        r1 = await _agent_patch(
            database,
            token1,
            heading,
            {"level": 2, "text": "W1v1"},
            expected_row_version=1,
            idempotency_key="13a-conf-w1",
        )
        assert r1.status_code == 200, r1.text
        op1 = UUID(str(r1.json()["operation_id"]))
        r2 = await _agent_patch(
            database,
            token2,
            heading,
            {"level": 1, "text": "W2v2"},
            expected_row_version=1,
            idempotency_key="13a-conf-w2",
        )
        assert r2.status_code == 200, r2.text

        # Real W2 freeze + human accept publishes B.
        result2, _ = await _freeze_claim_run(
            database,
            workspace_id=ws2,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-conf-w2f",
        )
        assert result2.status == "SUCCEEDED", result2.error
        result2a, _ = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-conf-w2a",
            boundary=boundary,
        )
        assert result2a.status == "SUCCEEDED", result2a.error

        B = await _canonical_projection(database, heading)
        assert B["props"] == {"level": 1, "text": "W2v2"}
        assert B["row_version"] == 2

        conflicts_mid = await _public_conflicts(database, ws1)
        assert len(conflicts_mid) == 1
        assert conflicts_mid[0]["conflict_kind"] == "BASE_ROW_CHANGED"
        assert conflicts_mid[0]["table_name"] == "page_composition"
        assert conflicts_mid[0]["primary_key"] == {"id": str(heading)}
        assert UUID(str(conflicts_mid[0]["operation_id"])) == op1

        # W1's second edit at the actual request version (2).
        r1b = await _agent_patch(
            database,
            token1,
            heading,
            {"level": 2, "text": "W1v2"},
            expected_row_version=2,
            idempotency_key="13a-conf-w1b",
        )
        assert r1b.status_code == 200, r1b.text
        op2 = UUID(str(r1b.json()["operation_id"]))

        # Four distinct sources, each observed through a supported
        # read path: canonical at W1's first touch (A), W1's earlier
        # value (its effective row), W2's published value (canonical
        # after the real acceptance) and W1's actual new value.
        w1_ops = await _public_operations(database, ws1)
        assert op1 in w1_ops and op2 in w1_ops
        sources = {
            "canonical_at_first_touch": A["props"],
            "w1_earlier_value": {"level": 2, "text": "W1v1"},
            "w2_published_value": B["props"],
            "w1_actual_new_value": {"level": 2, "text": "W1v2"},
        }
        assert len({json.dumps(v, sort_keys=True) for v in sources.values()}) == 4

        # Both W1 transitions keep their exact facts.  The second
        # write's DML pre-image is W1's own effective COW row at write
        # time - the value W1 wrote earlier - neither the session's
        # first-touch baseline A nor the W2 value W2 published to
        # canonical: the mutation applies to W1's own copy of the row,
        # and the same-statement prior capture records exactly that
        # pre-write row.  The divergence from the published row is
        # observed through the typed public conflict above
        # (BASE_ROW_CHANGED); the baseline bookkeeping is separate
        # foundation state.  The numeric row versions agree because
        # both lineages anchor to the same first-touch baseline rv 1
        # with one write applied each.
        facts = await _heading_facts(database, heading, ws1)
        assert [f["operation_id"] for f in facts] == [op1, op2]
        assert facts[0]["props_before"] == A["props"]
        assert facts[0]["props_after"] == {"level": 2, "text": "W1v1"}
        assert facts[1]["props_before"] == {"level": 2, "text": "W1v1"}
        assert facts[1]["row_version_before"] == 2
        assert facts[1]["props_after"] == {"level": 2, "text": "W1v2"}
        assert facts[1]["row_version_after"] == 3
    finally:
        await pool.close()


async def _structural_locks(cow: Any, workspace_id: UUID, site_id: UUID) -> None:
    """The deployed 050 structural-lock body's exact statements, same
    keys and order (the agent role cannot EXECUTE the definer wrapper
    itself, so the replay issues the identical lock statements)."""

    await cow.native.execute(
        "SELECT pg_advisory_xact_lock_shared(hashtextextended($1::text, 280))",
        str(workspace_id),
    )
    await cow.native.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended("
        "$1::text || chr(58) || $2::text || chr(58) || "
        "'page-structure', 994))",
        str(workspace_id),
        str(site_id),
    )


@pytest.mark.asyncio
async def test_agent_first_write_race_real_command(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 3 (Agent): the ACTUAL supported Agent command is paused by a
    fixture barrier exactly at its real design-validator call - after
    the in-command read and before the view update - while the sibling
    workspace's REAL freeze is started.  The parked command's
    pre-park FOR SHARE on the shared site row (the 039 require-cow-site
    recheck inside the pre-validator authorize) blocks the freeze's
    real reviewer materialization at its site-row FOR UPDATE: the test
    observes that EXACT native blocking edge, proves the canonical is
    still the pre-publication row, releases the real command and
    observes its ACTUAL outcome (200 on the pre-publication row), then
    lets the unblocked freeze and the real acceptance publish the
    sibling value in the resolved order, with the typed public
    conflict and the retained before/after facts asserted exactly."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        A = await _canonical_projection(database, heading)
        assert A["props"] == {"level": 1, "text": "Accept"}
        assert A["row_version"] == 1

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            token1 = await _new_capability(owner, ws1)
            capability_id = await owner.fetchval(
                "SELECT id FROM control.capability WHERE workspace_id = $1"
                " ORDER BY created_at DESC LIMIT 1",
                ws1,
            )
            ws2, _cap2 = await _create_workspace(
                owner, site_id, delegator_id, "13b race W2"
            )
            token2 = await _new_capability(owner, ws2)

        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database, race_park=True),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://agent.test",
                timeout=120,
            ) as client:
                async with _h13b_race_park(database, workspace_id=ws1, heading=heading):
                    async with _h13b_lock_owner(database, _RACE_LOCK_KEY) as lock_owner:
                        task = asyncio.create_task(
                            client.patch(
                                f"/api/agent/v1/components/{heading}",
                                json={
                                    "props": {"level": 2, "text": "W1stale"},
                                    "expected_row_version": 1,
                                },
                                headers={
                                    "Authorization": f"Bearer {token1}",
                                    "Idempotency-Key": "13b-race-w1",
                                },
                            )
                        )
                        # The parked command's lock wait starts at its
                        # validator arrival; the whole park-to-release
                        # window must stay inside the park budget.
                        park_clock = time.monotonic()
                        login = database.credentials["slaif_agent_runtime"][0]
                        parked_pid = await _h13b_wait_parked(
                            database, _RACE_LOCK_KEY, login
                        )
                        # Observed ownership: the parked backend is the
                        # request's own runtime connection in this
                        # fixture database.
                        info = await _backend_info(database, parked_pid)
                        assert info is not None
                        assert info == (database.name, login), info
                        # Observed lock order: the definer's workspace
                        # structural locks are already granted (taken
                        # before the in-command read) while the request
                        # waits at the validator rendezvous.
                        (
                            workspace,
                            workspace_mode,
                            page,
                            pending,
                        ) = await _h13b_parked_lock_order(
                            database,
                            parked_pid,
                            workspace_id=ws1,
                            site_id=site_id,
                            park_key=_RACE_LOCK_KEY,
                        )
                        assert (workspace, workspace_mode, page, pending) == (
                            1,
                            "ShareLock",
                            1,
                            1,
                        )
                        # The in-command read is done (the validator
                        # call ran on the rv-1 row) and the view update
                        # has NOT run: the canonical row is still A.
                        view_parked = await _canonical_projection(database, heading)
                        assert (
                            view_parked["props"],
                            view_parked["row_version"],
                        ) == (A["props"], 1)

                        # The sibling's real first touch, then the
                        # REAL freeze STARTED, not awaited: the
                        # freeze's real reviewer materialization (the
                        # 076 workspace-state SQL) takes the shared
                        # site row FOR UPDATE, which the parked
                        # command's pre-park FOR SHARE (the 039
                        # slaif_agent_require_cow_site recheck, called
                        # through the pre-validator authorize) holds
                        # until the command's own transaction ends.
                        r2 = await _agent_patch(
                            database,
                            token2,
                            heading,
                            {"level": 1, "text": "W2v2"},
                            expected_row_version=1,
                            idempotency_key="13b-race-w2",
                        )
                        assert r2.status_code == 200, r2.text
                        t_freeze = time.monotonic()
                        freeze_task = asyncio.create_task(
                            _freeze_claim_run(
                                database,
                                workspace_id=ws2,
                                site_id=site_id,
                                delegator_id=delegator_id,
                                pool=pool,
                                claimant="13b-race-w2f",
                            )
                        )
                        # Observe the RESOLVED order through the exact
                        # native blocking edge: the parked command's
                        # pre-park site-row FOR SHARE is held until
                        # its own commit, so the freeze's blocked
                        # reviewer statement (and every publication
                        # after it) cannot precede the command's DML
                        # on this route.
                        (resolved_order, reviewer_pid) = await _h13b_resolved_order(
                            database,
                            parked_pid,
                            freeze_task,
                            reviewer_login=database.credentials["slaif_review_worker"][
                                0
                            ],
                        )
                        assert resolved_order == "reviewer-waiting", (
                            resolved_order,
                            reviewer_pid,
                        )
                        assert reviewer_pid is not None
                        # The waiting backend is the freeze job's
                        # real reviewer connection in this fixture
                        # database.
                        reviewer_info = await _backend_info(database, reviewer_pid)
                        assert reviewer_info == (
                            database.name,
                            database.credentials["slaif_review_worker"][0],
                        ), reviewer_info
                        # The publication is still pending while the
                        # freeze waits: the canonical row is A.
                        view_blocked = await _canonical_projection(database, heading)
                        assert (
                            view_blocked["props"],
                            view_blocked["row_version"],
                        ) == (A["props"], 1)
                        t_edge = time.monotonic()
                        assert time.monotonic() - park_clock < (
                            _RACE_PARK_BUDGET_SECONDS
                        ), (
                            "the fixture pause outlived the parked command "
                            f"budget (r2={t_freeze - park_clock:.2f}s "
                            f"freeze-to-edge={t_edge - t_freeze:.2f}s)"
                        )

                        # Release the park: the real command resumes,
                        # its version-guarded UPDATE lands on the
                        # pre-publication row, and only its COMMIT
                        # unblocks the freeze's pending statement.
                        assert (
                            await lock_owner.fetchval(
                                "SELECT pg_advisory_unlock($1)", _RACE_LOCK_KEY
                            )
                            is True
                        )
                        response = await task
        assert response.status_code == 200, response.text
        rec = response.json()
        # The "stale" expectation SUCCEEDS: the resolved order proved
        # above means its DML ran before the sibling publication, so
        # the version guard matched the pre-publication row.
        op1 = UUID(str(rec["operation_id"]))
        assert rec["record"]["row_version"] == 2
        assert rec["record"]["props"] == {"level": 2, "text": "W1stale"}

        # The unblocked freeze now completes, and only then does the
        # real acceptance publish B.
        result2, _job2 = await freeze_task
        assert result2.status == "SUCCEEDED", result2.error
        result2a, _job2a = await _accept_claim_run(
            database,
            workspace_id=ws2,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13b-race-w2a",
            boundary=boundary,
        )
        assert result2a.status == "SUCCEEDED", result2a.error
        B = await _canonical_projection(database, heading)
        assert B["props"] == {"level": 1, "text": "W2v2"}
        assert B["row_version"] == 2

        # The released command's exact durable evidence: one fact
        # with the pre-publication image pair, one completed journal
        # row, the committed reservation, exactly one public
        # operation and the typed public conflict against the
        # published base.
        facts = await _heading_facts(database, heading, ws1)
        assert len(facts) == 1
        fact = facts[0]
        assert fact["schema_version"] == _SCHEMA_VERSION
        assert fact["family"] == "agent"
        assert fact["mutation_kind"] == "heading_props"
        assert fact["site_id"] == site_id
        assert fact["workspace_id"] == ws1
        assert fact["component_id"] == heading
        assert fact["capability_id"] == capability_id
        assert fact["human_user_id"] is None
        assert fact["operation_id"] == op1
        assert (fact["row_version_before"], fact["row_version_after"]) == (1, 2)
        assert fact["props_before"] == A["props"]
        assert fact["props_after"] == {"level": 2, "text": "W1stale"}
        journal = await _journal_rows(database, op1)
        assert len(journal) == 1
        assert journal[0]["family"] == "agent"
        assert journal[0]["resource_type"] == "composition_node"
        assert journal[0]["resource_id"] == heading
        assert journal[0]["disposition"] == "completed"
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            reservations = await owner.fetchval(
                "SELECT count(*) FROM control.agent_idempotency"
                " WHERE workspace_id = $1",
                ws1,
            )
        assert reservations == 1
        # The COW view keeps the workspace's own value at its own
        # version even though the base moved to the published B.
        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool,
                session_id=ws1,
                operation_id=uuid.uuid4(),
            ) as cow:
                row = await cow.native.fetchrow(
                    "SELECT props, row_version"
                    " FROM content.page_composition WHERE id = $1",
                    heading,
                )
        finally:
            await agent_pool.close()
        effective_props = row["props"]
        if isinstance(effective_props, str):
            effective_props = json.loads(effective_props)
        assert effective_props == {"level": 2, "text": "W1stale"}
        assert int(row["row_version"]) == 2
        assert await _public_operations(database, ws1) == [op1]
        conflicts = await _public_conflicts(database, ws1)
        assert len(conflicts) == 1
        assert conflicts[0]["conflict_kind"] == "BASE_ROW_CHANGED"
        assert conflicts[0]["table_name"] == "page_composition"
        assert conflicts[0]["primary_key"] == {"id": str(heading)}
        assert UUID(str(conflicts[0]["operation_id"])) == op1
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_editor_first_write_race_real_command(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 3 (Human-on-Agent Editor): the ACTUAL supported Editor
    command is paused by a fixture barrier exactly at its real
    design-validator call - after the in-command read and before the
    view update - while the sibling workspace's REAL freeze is
    started.  The parked command's idempotency INSERT holds FOR KEY
    SHARE on the shared site row (the 028
    human_editor_idempotency.site_id reference to control.site), so
    the freeze's real reviewer materialization is blocked at its
    site-row FOR UPDATE: the test observes that EXACT native blocking
    edge, proves the canonical is still the pre-publication row,
    releases the real command and observes its ACTUAL outcome (200
    with the unversioned wire contract on the pre-publication row),
    then lets the unblocked freeze and the real acceptance publish
    the sibling value in the resolved order, with the typed public
    conflict and the retained pre-publication before/after facts
    asserted exactly."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]
    pool = await _worker_pool(database)
    boundary = MediaBoundary(settings=_media_settings(database, media_root))
    try:
        A = await _canonical_projection(database, heading)
        assert A["props"] == {"level": 1, "text": "Accept"}
        assert A["row_version"] == 1

        owner_pool = await database.role_pool("slaif_owner")
        try:
            ws_agent = await _create_agent_workspace(
                owner_pool,
                site_id=site_id,
                delegator_id=delegator_id,
                title="13b race agent workspace",
            )
            ws2, _cap2 = await _create_workspace(
                owner_pool, site_id, delegator_id, "13b race W2"
            )
            token2 = await _new_capability(owner_pool, ws2)
        finally:
            await owner_pool.close()

        merged_props = {"level": 3, "text": "ERace"}
        control = ControlDatabase(_control_settings(database))
        editor = EditorDatabase(_editor_db_settings(database, race_park=True))
        app = create_editor_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )
        try:
            await control.start()
            await editor.start()
            session = await control.human_session_service().create(delegator_id)
            token = session.token.get_secret_value()
            csrf = session.csrf_token.get_secret_value()
            headers = {
                "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
                "x-csrf-token": csrf,
                "x-editor-workspace": str(ws_agent),
                "Idempotency-Key": "13b-race-editor",
            }
            comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://editor.test",
                timeout=120,
            ) as client:
                async with _h13b_race_park(
                    database, workspace_id=ws_agent, heading=heading
                ):
                    async with _h13b_lock_owner(database, _RACE_LOCK_KEY) as lock_owner:
                        task = asyncio.create_task(
                            client.patch(
                                f"{comp_path}/components/{heading}",
                                json={"props": merged_props},
                                headers=headers,
                            )
                        )
                        # The parked command's lock wait starts at its
                        # validator arrival; the whole park-to-release
                        # window must stay inside the park budget.
                        park_clock = time.monotonic()
                        login = database.credentials["slaif_editor_runtime"][0]
                        parked_pid = await _h13b_wait_parked(
                            database, _RACE_LOCK_KEY, login
                        )
                        info = await _backend_info(database, parked_pid)
                        assert info is not None
                        assert info == (database.name, login), info
                        # Observed lock order: the Editor definer itself
                        # takes no structural lock (no page-structure
                        # lock), but the Human-on-Agent request's
                        # state-changing workspace assert holds the
                        # workspace key in exclusive mode; the only
                        # pending request is the rendezvous itself.
                        (
                            workspace,
                            workspace_mode,
                            page,
                            pending,
                        ) = await _h13b_parked_lock_order(
                            database,
                            parked_pid,
                            workspace_id=ws_agent,
                            site_id=site_id,
                            park_key=_RACE_LOCK_KEY,
                        )
                        assert (workspace, workspace_mode, page, pending) == (
                            1,
                            "ExclusiveLock",
                            0,
                            1,
                        )
                        # The earlier in-command read (and its
                        # validation) saw the pre-publish version; the
                        # view update has NOT run.
                        view_parked = await _canonical_projection(database, heading)
                        assert (
                            view_parked["props"],
                            view_parked["row_version"],
                        ) == (A["props"], 1)

                        # The sibling's real first touch, then the
                        # REAL freeze STARTED, not awaited: the
                        # parked command's idempotency INSERT holds
                        # FOR KEY SHARE on the shared site row (the
                        # 028 human_editor_idempotency.site_id
                        # reference to control.site), and the
                        # freeze's real reviewer materialization
                        # takes that site row FOR UPDATE.
                        r2 = await _agent_patch(
                            database,
                            token2,
                            heading,
                            {"level": 1, "text": "W2v2"},
                            expected_row_version=1,
                            idempotency_key="13b-race-w2",
                        )
                        assert r2.status_code == 200, r2.text
                        t_freeze = time.monotonic()
                        freeze_task = asyncio.create_task(
                            _freeze_claim_run(
                                database,
                                workspace_id=ws2,
                                site_id=site_id,
                                delegator_id=delegator_id,
                                pool=pool,
                                claimant="13b-race-w2f",
                            )
                        )
                        # Observe the RESOLVED order through the exact
                        # native blocking edge: the parked command's
                        # FK referential-integrity site-row lock is
                        # held until its own commit, so the freeze's
                        # blocked reviewer statement (and every
                        # publication after it) cannot precede the
                        # command's DML on this route.
                        (resolved_order, reviewer_pid) = await _h13b_resolved_order(
                            database,
                            parked_pid,
                            freeze_task,
                            reviewer_login=database.credentials["slaif_review_worker"][
                                0
                            ],
                        )
                        assert resolved_order == "reviewer-waiting", (
                            resolved_order,
                            reviewer_pid,
                        )
                        assert reviewer_pid is not None
                        # The waiting backend is the freeze job's
                        # real reviewer connection in this fixture
                        # database.
                        reviewer_info = await _backend_info(database, reviewer_pid)
                        assert reviewer_info == (
                            database.name,
                            database.credentials["slaif_review_worker"][0],
                        ), reviewer_info
                        # The publication is still pending while the
                        # freeze waits: the canonical row is A.
                        view_blocked = await _canonical_projection(database, heading)
                        assert (
                            view_blocked["props"],
                            view_blocked["row_version"],
                        ) == (A["props"], 1)
                        t_edge = time.monotonic()
                        assert time.monotonic() - park_clock < (
                            _RACE_PARK_BUDGET_SECONDS
                        ), (
                            "the fixture pause outlived the parked command "
                            f"budget (r2={t_freeze - park_clock:.2f}s "
                            f"freeze-to-edge={t_edge - t_freeze:.2f}s)"
                        )

                        # Release the park: the real unversioned write
                        # proceeds against the PRE-pUBLICATION row, and
                        # only its COMMIT unblocks the freeze's
                        # pending statement.
                        assert (
                            await lock_owner.fetchval(
                                "SELECT pg_advisory_unlock($1)", _RACE_LOCK_KEY
                            )
                            is True
                        )
                        response = await task
            assert response.status_code == 200, response.text
            rec = response.json()
            # The unversioned wire contract is intact (constant
            # row_version 1, actual props); the resolved order proved
            # the DML ran before the sibling publication.
            assert rec["row_version"] == 1
            assert rec["props"] == merged_props

            # The unblocked freeze now completes, and only then does
            # the real acceptance publish B.
            result2, _job2 = await freeze_task
            assert result2.status == "SUCCEEDED", result2.error
            result2a, _job2a = await _accept_claim_run(
                database,
                workspace_id=ws2,
                delegator_id=delegator_id,
                pool=pool,
                claimant="13b-race-w2a",
                boundary=boundary,
            )
            assert result2a.status == "SUCCEEDED", result2a.error
            B = await _canonical_projection(database, heading)
            assert B["props"] == {"level": 1, "text": "W2v2"}
            assert B["row_version"] == 2

            # The released write's exact durable evidence: one fact
            # with the PRE-publication image pair (both the earlier
            # validation read and the actual DML saw A at version
            # 1), one completed journal row, and - because the sibling
            # publication moved the base row after the write - the
            # typed public conflict against that operation.
            facts = await _heading_facts(database, heading, ws_agent)
            assert len(facts) == 1
            fact = facts[0]
            assert fact["family"] == "human_editor"
            assert fact["human_user_id"] == delegator_id
            assert fact["props_before"] == A["props"]
            assert fact["props_after"] == merged_props
            assert (
                fact["row_version_before"],
                fact["row_version_after"],
            ) == (1, 2)
            op = fact["operation_id"]
            journal = await _journal_rows(database, op)
            assert len(journal) == 1
            assert journal[0]["disposition"] == "completed"

            # The effective COW view keeps the workspace's own merged
            # value at its own version even though the base moved to
            # the published B.
            agent_pool = await database.role_pool("slaif_agent_runtime")
            try:
                async with asyncpg_cow_session(
                    agent_pool,
                    session_id=ws_agent,
                    operation_id=uuid.uuid4(),
                ) as cow:
                    row = await cow.native.fetchrow(
                        "SELECT props, row_version"
                        " FROM content.page_composition WHERE id = $1",
                        heading,
                    )
            finally:
                await agent_pool.close()
            effective_props = row["props"]
            if isinstance(effective_props, str):
                effective_props = json.loads(effective_props)
            assert effective_props == merged_props
            assert int(row["row_version"]) == 2
            assert await _public_operations(database, ws_agent) == [op]
            conflicts = await _public_conflicts(database, ws_agent)
            assert len(conflicts) == 1
            assert conflicts[0]["conflict_kind"] == "BASE_ROW_CHANGED"
            assert conflicts[0]["table_name"] == "page_composition"
            assert conflicts[0]["primary_key"] == {"id": str(heading)}
            assert UUID(str(conflicts[0]["operation_id"])) == op
        finally:
            await editor.stop()
            await control.stop()
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_attribution_isolation_and_legal_discard(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 4: both HTTP paths attribute the same resource's transitions
    to distinct families/principals with chaining images; cross-site
    denials at the real login boundaries record nothing; a legal
    discard removes the pending COW rows but the committed effect
    facts remain; non-heading writes stay outside the pilot."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    # A real AGENT workspace carries BOTH paths for a clean attribution
    # chain (the seeded workspace is a HUMAN workspace).
    owner_pool = await database.role_pool("slaif_owner")
    ws_agent = await _create_agent_workspace(
        owner_pool,
        site_id=site_id,
        delegator_id=delegator_id,
        title="13a attribution agent workspace",
    )
    await owner_pool.close()

    A = await _canonical_projection(database, heading)

    # 1. Agent path first, then Human-on-Agent Editor on the SAME
    #    heading in the SAME workspace: the images chain exactly.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws_agent)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws_agent,
        )

    r1 = await _agent_patch(
        database,
        token,
        heading,
        {"level": 2, "text": "AgentSide"},
        expected_row_version=1,
        idempotency_key="13a-attr-agent",
    )
    assert r1.status_code == 200, r1.text

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        await control.start()
        await editor.start()
        session = await control.human_session_service().create(delegator_id)
        tok = session.token.get_secret_value()
        csrf = session.csrf_token.get_secret_value()
        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            r2 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 3, "text": "HumanSide"}},
                headers={
                    "cookie": f"slaif_session={tok}; slaif_csrf={csrf}",
                    "x-csrf-token": csrf,
                    "x-editor-workspace": str(ws_agent),
                    "Idempotency-Key": "13a-attr-editor",
                },
            )
            assert r2.status_code == 200, r2.text
    finally:
        await editor.stop()
        await control.stop()

    facts = await _heading_facts(database, heading, ws_agent)
    assert len(facts) == 2
    f_agent, f_editor = facts
    assert f_agent["family"] == "agent"
    assert f_agent["capability_id"] == capability_id
    assert f_agent["human_user_id"] is None
    assert f_editor["family"] == "human_editor"
    assert f_editor["capability_id"] is None
    assert f_editor["human_user_id"] == delegator_id
    assert f_agent["operation_id"] != f_editor["operation_id"]
    # Exact chaining across families on the same resource.
    assert f_agent["props_before"] == A["props"]
    assert f_agent["props_after"] == {"level": 2, "text": "AgentSide"}
    assert f_editor["props_before"] == f_agent["props_after"]
    assert f_editor["props_after"] == {"level": 3, "text": "HumanSide"}
    assert f_editor["row_version_before"] == f_agent["row_version_after"]

    # 2. Cross-site denial at the real Agent login boundary: a
    #    capability bound to a DIFFERENT site cannot touch this
    #    component; nothing is recorded.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        other_delegator = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Accept.13a.Other',
                'accept.13a.other', $1, 'Accept 13a Other', 'ACTIVE'
            ) RETURNING id
            """,
            _AGGON2,
        )
        other_site = await owner.fetchval(
            "INSERT INTO control.site (site_key, display_name,"
            " default_locale, component_catalog_version)"
            " VALUES ('accept-13a-other', 'Accept 13a Other', 'en-US',"
            " 'catalog-v1') RETURNING id"
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            other_site,
            other_delegator,
        )
        other_ws, _other_cap = await _create_workspace(
            owner, other_site, other_delegator, "13a other site ws"
        )
        token_other = await _new_capability(owner, other_ws)

    r_cross = await _agent_patch(
        database,
        token_other,
        heading,
        {"level": 2, "text": "CrossSite"},
        expected_row_version=1,
        idempotency_key="13a-cross-site",
    )
    assert r_cross.status_code == 404, r_cross.text
    assert await _heading_facts(database, heading) == [f_agent, f_editor]

    # 3. Cross-site denial at the real Editor login boundary: a session
    #    enrolled on the other site cannot write this site's page.
    control = ControlDatabase(_control_settings(database))
    editor2 = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor2,
    )
    try:
        await control.start()
        await editor2.start()
        other_session = await control.human_session_service().create(other_delegator)
        otok = other_session.token.get_secret_value()
        ocsrf_token = other_session.csrf_token.get_secret_value()
        other_cookie = f"slaif_session={otok}; slaif_csrf={ocsrf_token}"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            r_cross_e = await client.patch(
                f"/api/editor/v1/sites/{site_id}/pages/{page_id}"
                f"/composition/components/{heading}",
                json={"props": {"level": 3, "text": "CrossSiteE"}},
                headers={
                    "cookie": other_cookie,
                    "x-csrf-token": ocsrf_token,
                    "x-editor-workspace": str(other_ws),
                    "Idempotency-Key": "13a-cross-site-e",
                },
            )
    finally:
        await editor2.stop()
        await control.stop()
    assert r_cross_e.status_code in (403, 404), r_cross_e.text
    assert await _heading_facts(database, heading) == [f_agent, f_editor]

    # 4. Pilot boundary: a non-heading props write through the SAME
    #    agent path completes normally but records NO fact.
    section_id: UUID = ids["section_id"]
    section_view = await _canonical_projection(database, section_id)
    assert section_view["component_type"] == "Section"
    section_props = dict(section_view["props"])
    section_props["variant"] = "narrow"
    r_sec = await _agent_patch(
        database,
        token,
        section_id,
        section_props,
        expected_row_version=section_view["row_version"],
        idempotency_key="13a-boundary-section",
    )
    assert r_sec.status_code == 200, r_sec.text
    assert await _heading_facts(database, heading) == [f_agent, f_editor]
    assert await _heading_facts_for_component(database, section_id) == []

    # 5. Legal discard: the real freeze + human discard lifecycle
    #    removes the pending COW rows of the workspace, but the
    #    COMMITTED effect facts remain (audit is not COW state).
    pool = await _worker_pool(database)
    try:
        ops_before = await _public_operations(database, ws_agent)
        assert len(ops_before) >= 2  # the heading ops (+ section op)
        result_f, _ = await _freeze_claim_run(
            database,
            workspace_id=ws_agent,
            site_id=site_id,
            delegator_id=delegator_id,
            pool=pool,
            claimant="13a-attr-freeze",
        )
        assert result_f.status == "SUCCEEDED", result_f.error
        rows = await _enqueue_discard(database, ws_agent, delegator_id)
        assert len(rows) == 1
        job = await _claim_discard(database, "13a-attr-discard")
        result_d = await run_discard_job(pool, _worker_settings(database), job)
        assert result_d.status == "SUCCEEDED", result_d.error
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            ws_status = await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1",
                ws_agent,
            )
        assert ws_status == "DISCARDED"
        # Public operation inspection: the pending COW rows are gone.
        assert await _public_operations(database, ws_agent) == []
        # The committed facts survive the discard, byte-for-byte.
        facts_after = await _heading_facts(database, heading)
        assert [f["operation_id"] for f in facts_after] == [
            f_agent["operation_id"],
            f_editor["operation_id"],
        ]
        assert facts_after[0]["props_after"] == {"level": 2, "text": "AgentSide"}
        assert facts_after[1]["props_after"] == {"level": 3, "text": "HumanSide"}
    finally:
        await pool.close()

    # 6. Old workspace without facts = unknown: a workspace that never
    #    recorded proves nothing; the facts table simply has no row for
    #    it (no synthetic history, no claim of no-effect).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        no_fact_count = await owner.fetchval(
            "SELECT count(*) FROM audit.heading_row_effect WHERE workspace_id = $1",
            other_ws,
        )
    assert no_fact_count == 0


@pytest.mark.asyncio
async def test_missing_completion_refuses_commit_and_leaves_no_residue(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 1 negative path (real runtime role): a heading fact whose
    transaction has no genuine completed 078 operation is refused at the
    real commit boundary; the whole staged transaction rolls back and
    leaves no residue anywhere."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    site_id: UUID = ids["site_id"]
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await _new_capability(owner, ws1)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws1,
        )

    A = await _canonical_projection(database, heading)
    assert A["row_version"] == 1
    before = await _h13b_durable_state(
        database, workspace_id=ws1, heading=heading, family="agent"
    )

    agent_pool = await database.role_pool("slaif_agent_runtime")
    unbound_operation = uuid.uuid4()
    try:
        with pytest.raises(asyncpg.PostgresError) as exc:
            async with asyncpg_cow_session(
                agent_pool, session_id=ws1, operation_id=unbound_operation
            ) as cow:
                await cow.native.execute(
                    "SELECT set_config('app.capability_id',$1,true)",
                    str(capability_id),
                )
                begun = await cow.native.fetchrow(
                    "SELECT * FROM control.slaif_agent_idempotency_begin"
                    "($1,$2,$3,$4,$5)",
                    capability_id,
                    ws1,
                    "13b-no-completion",
                    "0" * 64,
                    unbound_operation,
                )
                assert begun["state"] == "STARTED"
                row = await cow.native.fetchrow(
                    "SELECT * FROM content.slaif_agent_component_update"
                    "($1,$2,$3::jsonb,$4)",
                    site_id,
                    heading,
                    json.dumps({"level": 2, "text": "Unbound"}),
                    1,
                )
                assert row is not None
    finally:
        await agent_pool.close()

    # The refusal is the deferred completion binding at COMMIT, not an
    # earlier input check: the reservation and the staged write were
    # accepted, and the commit itself is what was refused.
    assert getattr(exc.value, "sqlstate", None) == "P0001"
    assert "HEADING_EFFECT_COMPLETION_UNBOUND" in str(getattr(exc.value, "message", ""))

    # Exact no-residue: the durable state is byte-for-byte the pre-state.
    after = await _h13b_durable_state(
        database, workspace_id=ws1, heading=heading, family="agent"
    )
    assert before == after
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM audit.heading_row_effect WHERE operation_id = $1",
                unbound_operation,
            )
            == 0
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM control.agent_idempotency"
                " WHERE operation_id = $1",
                unbound_operation,
            )
            == 0
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM audit.agent_mutation WHERE operation_id = $1",
                unbound_operation,
            )
            == 0
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM audit.mutation_completion"
                " WHERE operation_id = $1",
                unbound_operation,
            )
            == 0
        )
    view = await _canonical_projection(database, heading)
    assert (view["props"], view["row_version"]) == (A["props"], A["row_version"])
    assert await _public_operations(database, ws1) == []


@pytest.mark.asyncio
async def test_agent_late_failure_rolls_back_staged_write_and_fact(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Item 2 (Agent envelope): after a REAL staged COW write and heading
    fact inside the uncommitted transaction, a real late completion
    failure refuses the commit; every durable state is byte-for-byte the
    pre-state, the same body and key retried completes exactly once, and
    an ordinary replay stays inert."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    ws1: UUID = ids["workspace_id"]
    heading: UUID = ids["heading_id"]

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        token = await _new_capability(owner, ws1)
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1"
            " ORDER BY created_at DESC LIMIT 1",
            ws1,
        )

    A = await _canonical_projection(database, heading)
    assert A["row_version"] == 1
    key = "13b-agent-late"
    props = {"level": 2, "text": "LateFailure"}
    before = await _h13b_durable_state(
        database, workspace_id=ws1, heading=heading, family="agent"
    )

    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    async with app.router.lifespan_context(app):
        async with _h13b_completion_barrier(database, ws1, "fail"):
            async with _h13b_lock_owner(database, _BARRIER_LOCK_KEY) as lock_owner:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://agent.test",
                    timeout=60,
                ) as client:
                    task = asyncio.create_task(
                        client.patch(
                            f"/api/agent/v1/components/{heading}",
                            json={
                                "props": props,
                                "expected_row_version": 1,
                            },
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Idempotency-Key": key,
                            },
                        )
                    )
                    login = database.credentials["slaif_agent_runtime"][0]
                    parked_pid = await _h13b_wait_parked(
                        database, _BARRIER_LOCK_KEY, login
                    )
                    # The parked backend is the request's own runtime
                    # connection in this fixture database.
                    info = await _backend_info(database, parked_pid)
                    assert info is not None
                    assert info == (database.name, login), info
                    # Independent connection: the staged effect is NOT
                    # visible before commit (another connection cannot
                    # attest the staged values pre-commit).
                    assert await _heading_facts(database, heading, ws1) == []
                    view_parked = await _canonical_projection(database, heading)
                    assert (view_parked["props"], view_parked["row_version"]) == (
                        A["props"],
                        A["row_version"],
                    )
                    # Release: the trigger raises the late failure inside
                    # the still-uncommitted mutation transaction.
                    assert (
                        await lock_owner.fetchval(
                            "SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY
                        )
                        is True
                    )
                    response = await task
        assert response.status_code == 503, response.text

    after = await _h13b_durable_state(
        database, workspace_id=ws1, heading=heading, family="agent"
    )
    assert before == after
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        stale_reservation = await owner.fetchval(
            "SELECT count(*) FROM control.agent_idempotency WHERE idempotency_key = $1",
            key,
        )
    assert stale_reservation == 0

    # The SAME body and idempotency key retried completes exactly once.
    r2 = await _agent_patch(
        database,
        token,
        heading,
        props,
        expected_row_version=1,
        idempotency_key=key,
    )
    assert r2.status_code == 200, r2.text
    op2 = UUID(str(r2.json()["operation_id"]))
    facts = await _heading_facts(database, heading, ws1)
    assert len(facts) == 1
    assert facts[0]["operation_id"] == op2
    assert facts[0]["family"] == "agent"
    assert facts[0]["capability_id"] == capability_id
    assert (facts[0]["row_version_before"], facts[0]["row_version_after"]) == (1, 2)
    assert facts[0]["props_before"] == A["props"]
    assert facts[0]["props_after"] == props
    journal = await _journal_rows(database, op2)
    assert len(journal) == 1
    assert journal[0]["family"] == "agent"
    assert journal[0]["resource_type"] == "composition_node"
    assert journal[0]["resource_id"] == heading
    assert journal[0]["disposition"] == "completed"
    after_retry = await _h13b_durable_state(
        database, workspace_id=ws1, heading=heading, family="agent"
    )
    assert len(after_retry["facts"]) == len(before["facts"]) + 1
    assert len(after_retry["audit"]) == len(before["audit"]) + 1
    assert len(after_retry["journal"]) == len(before["journal"]) + 1
    assert len(after_retry["reservations"]) == len(before["reservations"]) + 1

    # An ordinary retry of the successful result stays inert (stored
    # body; the definer never re-runs).
    r3 = await _agent_patch(
        database,
        token,
        heading,
        props,
        expected_row_version=1,
        idempotency_key=key,
    )
    assert r3.status_code == 200
    assert r3.json() == r2.json()
    assert len(await _heading_facts(database, heading, ws1)) == 1
    assert UUID(str(r3.json()["operation_id"])) == op2


@pytest.mark.asyncio
async def test_editor_late_cancellation_rolls_back_staged_write_and_fact(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Item 2 (Human-on-Agent Editor envelope): after a REAL staged COW
    write and heading fact inside the uncommitted transaction, a real
    cancellation of the in-flight request aborts the same transaction;
    every durable state is byte-for-byte the pre-state, the same body
    and key retried completes exactly once, and the replay stays inert."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    owner_pool = await database.role_pool("slaif_owner")
    ws_agent = await _create_agent_workspace(
        owner_pool,
        site_id=site_id,
        delegator_id=delegator_id,
        title="13b editor late-cancellation workspace",
    )
    await owner_pool.close()

    A = await _canonical_projection(database, heading)
    assert A["row_version"] == 1
    key = "13b-editor-late"
    props = {"level": 3, "text": "LateCancel"}
    before = await _h13b_durable_state(
        database, workspace_id=ws_agent, heading=heading, family="human_editor"
    )

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        await control.start()
        await editor.start()
        session = await control.human_session_service().create(delegator_id)
        token = session.token.get_secret_value()
        csrf = session.csrf_token.get_secret_value()
        headers = {
            "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
            "x-csrf-token": csrf,
            "x-editor-workspace": str(ws_agent),
            "Idempotency-Key": key,
        }
        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            async with _h13b_completion_barrier(database, ws_agent, "cancel"):
                async with _h13b_lock_owner(database, _BARRIER_LOCK_KEY) as lock_owner:
                    task = asyncio.create_task(
                        client.patch(
                            f"{comp_path}/components/{heading}",
                            json={"props": props},
                            headers=headers,
                        )
                    )
                    login = database.credentials["slaif_editor_runtime"][0]
                    parked_pid = await _h13b_wait_parked(
                        database, _BARRIER_LOCK_KEY, login
                    )
                    info = await _backend_info(database, parked_pid)
                    assert info is not None
                    assert info == (database.name, login), info
                    # Independent connection: the staged effect is NOT
                    # visible before commit.
                    assert await _heading_facts(database, heading, ws_agent) == []
                    view_parked = await _canonical_projection(database, heading)
                    assert (view_parked["props"], view_parked["row_version"]) == (
                        A["props"],
                        A["row_version"],
                    )
                    # The real cancellation aborts the still-uncommitted
                    # transaction at the rendezvous.
                    task.cancel()
                    outcome = await asyncio.gather(task, return_exceptions=True)
                    assert isinstance(outcome[0], asyncio.CancelledError), outcome
                    assert (
                        await lock_owner.fetchval(
                            "SELECT pg_advisory_unlock($1)", _BARRIER_LOCK_KEY
                        )
                        is True
                    )
            after = await _h13b_durable_state(
                database,
                workspace_id=ws_agent,
                heading=heading,
                family="human_editor",
            )
            assert before == after

            # The SAME body and idempotency key retried completes exactly
            # once.
            r2 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": props},
                headers=headers,
            )
            assert r2.status_code == 200, r2.text
            rec2 = r2.json()
            assert rec2["row_version"] == 1
            assert rec2["props"] == props
            facts = await _heading_facts(database, heading, ws_agent)
            assert len(facts) == 1
            fact = facts[0]
            assert fact["family"] == "human_editor"
            assert fact["human_user_id"] == delegator_id
            assert fact["capability_id"] is None
            assert (fact["row_version_before"], fact["row_version_after"]) == (1, 2)
            assert fact["props_before"] == A["props"]
            assert fact["props_after"] == props
            op2 = fact["operation_id"]
            journal = await _journal_rows(database, op2)
            assert len(journal) == 1
            assert journal[0]["family"] == "human_editor"
            assert journal[0]["resource_type"] == "editor.sites"
            assert journal[0]["resource_id"] == heading
            assert journal[0]["disposition"] == "completed"
            after_retry = await _h13b_durable_state(
                database,
                workspace_id=ws_agent,
                heading=heading,
                family="human_editor",
            )
            assert len(after_retry["facts"]) == len(before["facts"]) + 1
            assert len(after_retry["audit"]) == len(before["audit"]) + 1
            assert len(after_retry["journal"]) == len(before["journal"]) + 1
            assert len(after_retry["reservations"]) == len(before["reservations"]) + 1

            # An ordinary replay of the successful result stays inert
            # (the stored body is returned; no second fact).
            r3 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": props},
                headers=headers,
            )
            assert r3.status_code == 200
            assert r3.json() == rec2
            assert len(await _heading_facts(database, heading, ws_agent)) == 1
    finally:
        await editor.stop()
        await control.stop()


@pytest.mark.asyncio
async def test_editor_unchanged_props_and_structural_only_record_no_fact(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Item 4: an unchanged-props Editor write and a structural-only
    Editor write on a Heading keep their legacy behavior byte-for-byte
    and record NO heading-props fact; a mixed props+structural change
    records the exact props pair (and claims nothing about the
    structural history); the ordinary Human workspace path keeps its
    existing behavior and records nothing."""

    database = agent_site_database
    ids = await _seed_site(database, media_root=None, with_ops=False)
    site_id: UUID = ids["site_id"]
    delegator_id: UUID = ids["delegator_id"]
    heading: UUID = ids["heading_id"]
    page_id: UUID = ids["page_id"]

    owner_pool = await database.role_pool("slaif_owner")
    ws_agent = await _create_agent_workspace(
        owner_pool,
        site_id=site_id,
        delegator_id=delegator_id,
        title="13b editor pilot scope workspace",
    )
    await owner_pool.close()

    ws_human: UUID = ids["workspace_id"]

    A = await _canonical_projection(database, heading)
    assert A["props"] == {"level": 1, "text": "Accept"}
    assert A["row_version"] == 1

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_db_settings(database))
    app = create_editor_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST),
        database=control,
        editor_database=editor,
    )
    try:
        await control.start()
        await editor.start()
        session = await control.human_session_service().create(delegator_id)
        token = session.token.get_secret_value()
        csrf = session.csrf_token.get_secret_value()
        headers = {
            "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
            "x-csrf-token": csrf,
            "x-editor-workspace": str(ws_agent),
        }
        comp_path = f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=60,
        ) as client:
            # 1. Unchanged props: the legacy write still runs (the wire
            #    row_version stays the constant 1), but no fact.
            r1 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": dict(A["props"])},
                headers={**headers, "Idempotency-Key": "13b-editor-same"},
            )
            assert r1.status_code == 200, r1.text
            assert r1.json()["props"] == A["props"]
            assert await _heading_facts(database, heading, ws_agent) == []
            # 2. Structural-only (order_key, no props): the seeded
            #    heading sits in its Section's only allowed slot
            #    ("default"), so the structural field a supported
            #    update may change here is the order key. Legacy
            #    behavior, no fact.
            r2 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"order_key": 2},
                headers={**headers, "Idempotency-Key": "13b-editor-order"},
            )
            assert r2.status_code == 200, r2.text
            assert r2.json()["order_key"] == 2
            assert r2.json()["props"] == A["props"]
            assert await _heading_facts(database, heading, ws_agent) == []
            # 3. Mixed change (props + order_key): the accurate props
            #    pair is recorded; the structural part claims nothing.
            mixed_props = {"level": 4, "text": "Mixed"}
            r3 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": mixed_props, "order_key": 3},
                headers={**headers, "Idempotency-Key": "13b-editor-mixed"},
            )
            assert r3.status_code == 200, r3.text
            assert r3.json()["props"] == mixed_props
            assert r3.json()["order_key"] == 3
            # 4. Ordinary Human workspace (the seeded workspace): the
            #    existing behavior is intact - the legacy write runs
            #    and no fact is recorded.  Ordinary human editing does
            #    not send the workspace header; the server resolves
            #    the session's own HUMAN workspace.
            human_headers = {
                k: v for k, v in headers.items() if k != "x-editor-workspace"
            }
            r4 = await client.patch(
                f"{comp_path}/components/{heading}",
                json={"props": {"level": 5, "text": "HumanWs"}},
                headers={
                    **human_headers,
                    "Idempotency-Key": "13b-editor-human-ws",
                },
            )
            assert r4.status_code == 200, r4.text
            assert r4.json()["props"] == {"level": 5, "text": "HumanWs"}
    finally:
        await editor.stop()
        await control.stop()

    # The ordinary Human workspace write is durable in its own COW view.
    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        async with asyncpg_cow_session(
            agent_pool, session_id=ws_human, operation_id=uuid.uuid4()
        ) as cow:
            row = await cow.native.fetchrow(
                "SELECT props, row_version FROM content.page_composition WHERE id = $1",
                heading,
            )
        effective_props = row["props"]
        if isinstance(effective_props, str):
            effective_props = json.loads(effective_props)
        effective = (effective_props, int(row["row_version"]))
    finally:
        await agent_pool.close()
    assert effective == ({"level": 5, "text": "HumanWs"}, 2)
    assert await _heading_facts(database, heading, ws_human) == []

    facts = await _heading_facts(database, heading, ws_agent)
    assert len(facts) == 1
    fact = facts[0]
    assert fact["family"] == "human_editor"
    assert fact["human_user_id"] == delegator_id
    assert fact["props_before"] == A["props"]
    assert fact["props_after"] == mixed_props
    # Three legacy writes happened (1->2 unchanged, 2->3 structural,
    # 3->4 mixed); the single fact covers the mixed write's exact
    # transition.
    assert (fact["row_version_before"], fact["row_version_after"]) == (3, 4)
    view = await _canonical_projection(database, heading)
    assert view["props"] == A["props"]


async def _heading_facts_for_component(
    database: AgentSiteDatabase, component_id: UUID
) -> list[dict[str, Any]]:
    return await _heading_facts(database, component_id)


def _dsn(database: AgentSiteDatabase, user: str, password: str) -> str:
    params = database.connection_parameters
    host = quote(str(params["host"]), safe="[]:.")
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@"
        f"{host}:{params['port']}/{database.name}"
    )


async def _real_login(database: AgentSiteDatabase, role: str) -> asyncpg.Connection:
    """One connection on the REAL provisioned login for the role
    (no SET ROLE): LOGIN-identity proof under fixture trust auth."""

    login, password = database.credentials[role]
    return await asyncpg.connect(dsn=_dsn(database, login, password))


def _split_statements(sql: str) -> list[str]:
    """Split a multi-statement DDL block on statement-ending
    semicolons outside ``$fn$`` function bodies (the same rule 080's
    own ``_execute_block`` applies)."""

    stmts: list[str] = []
    current: list[str] = []
    in_body = False
    for line in sql.splitlines(keepends=True):
        current.append(line)
        if line.count("$fn$") % 2:
            in_body = not in_body
        if line.rstrip().endswith(";") and not in_body:
            stmts.append("".join(current))
            current = []
    if "".join(current).strip():
        stmts.append("".join(current))
    return [s for s in stmts if s.strip()]


@pytest.mark.asyncio
async def test_facts_authority_boundaries_and_downgrade_ratchet(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Runtime roles cannot forge/read/update/delete the facts, the
    recorder is owner-only and context-bound (no general fact insert),
    the versioned format is bounded, and the downgrade ratchet refuses
    at both the operator and the direct Alembic level (081 first, the
    080 and 079 bodies still intact behind it)."""

    database = agent_site_database
    media_root = tmp_path / "media"
    ids = await _seed_site(database, media_root=media_root, with_ops=False)
    heading: UUID = ids["heading_id"]

    # 1. Real logins: every runtime role is denied on the facts table
    #    and on the owner-only recorder.
    for role in _DENY_ROLES:
        conn = await _real_login(database, role)
        try:
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.fetchval("SELECT count(*) FROM audit.heading_row_effect")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(
                    "INSERT INTO audit.heading_row_effect"
                    " (operation_id, family, mutation_kind, site_id,"
                    " workspace_id, component_id, row_version_before,"
                    " row_version_after, props_before, props_after)"
                    " VALUES (gen_random_uuid(), 'agent', 'heading_props',"
                    " $1, $1, $2, 1, 2, '{}'::jsonb, '{}'::jsonb)"
                    " ON CONFLICT DO NOTHING",
                    ids["site_id"],
                    heading,
                )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await conn.execute(
                    "SELECT control.slaif_heading_row_effect_record("
                    " gen_random_uuid(), 'agent', $1, $1, $1, $2, 1, 2,"
                    " '{}'::jsonb, '{}'::jsonb)",
                    ids["site_id"],
                    heading,
                )
        finally:
            await conn.close()

    # The recorder has no role EXECUTE at all (owner only).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for role in _DENY_ROLES:
            granted = await owner.fetchval(
                "SELECT has_function_privilege("
                " $1, 'control.slaif_heading_row_effect_record"
                "(uuid,text,uuid,uuid,uuid,uuid,integer,integer,jsonb,jsonb)',"
                " 'EXECUTE')",
                role,
            )
            assert granted is False
        table_grants = await owner.fetchval(
            "SELECT has_table_privilege('slaif_owner',"
            " 'audit.heading_row_effect', 'SELECT')"
        )
        assert table_grants is True

    # 2. No general fact insert: even the owner, outside the trusted
    #    COW session context, is refused before any effect.
    with pytest.raises(asyncpg.PostgresError) as no_ctx:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "SELECT control.slaif_heading_row_effect_record("
                " gen_random_uuid(), 'agent', $1, $1, $1, $2, 1, 2,"
                " '{}'::jsonb, '{}'::jsonb)",
                ids["site_id"],
                heading,
            )
    assert getattr(no_ctx.value, "sqlstate", None) == "P0001"
    assert "HEADING_EFFECT" in str(getattr(no_ctx.value, "message", ""))

    # 3. Bounded versioned format: the props images are capped at the
    #    existing composition 16384-octet ceiling; a larger image is
    #    refused by the table itself (defense in depth behind the
    #    definer's own props validation).
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        with pytest.raises(asyncpg.PostgresError) as over:
            await owner.execute(
                "INSERT INTO audit.heading_row_effect"
                " (operation_id, family, mutation_kind, site_id,"
                " workspace_id, component_id, row_version_before,"
                " row_version_after, props_before, props_after)"
                " VALUES (gen_random_uuid(), 'agent', 'heading_props',"
                " $1, $1, $2, 1, 2, jsonb_build_object('text', $3::text),"
                " '{}'::jsonb)",
                ids["site_id"],
                heading,
                "x" * 16385,
            )
    assert getattr(over.value, "sqlstate", None) == "23514"

    # 4. Downgrade ratchet: at the current head the operator path
    # refuses via the retained-heading-review-facts preflight; the
    # direct downgrade commits the function-only 082 step (the guarded
    # rollback to 071 semantics restores the 071 read model and the
    # 070 freeze body and drops the two 082 functions) and then the
    # 081 body refuses 081 -> 080, leaving the 081 surface and all
    # product state exactly as found.  Staged from the released 080
    # head the 080 body still refuses 080 -> 079, and the 079 body
    # still refuses 079 -> 078 when staged from the released 079 head.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        before = await owner.fetchrow("SELECT version_num FROM control.alembic_version")
        assert before["version_num"] == "082_001"

    with pytest.raises(BootstrapStateError, match="retained heading review facts"):
        await downgrade(database.settings)
    with pytest.raises(DBAPIError) as direct_081_exc:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="079_001",
        )
    underlying_081 = direct_081_exc.value.orig
    assert "HEADING_RETENTION_DOWNGRADE_UNSUPPORTED" in str(underlying_081)
    assert getattr(underlying_081, "sqlstate", None) == "P0001"

    # Stage the released 080 head.  The 081 surface has no supported
    # downgrade (proved above), so a 080-era release deployment is
    # simulated at the fixture level: the owner drops the 081
    # retention table and both definer functions and stages the 080
    # version row.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "DROP FUNCTION control.slaif_review_heading_effects_read"
            "(uuid,uuid,uuid,uuid)"
        )
        await owner.execute(
            "DROP FUNCTION control.slaif_review_retain_heading_facts(uuid,uuid)"
        )
        await owner.execute("DROP TABLE control.heading_review_retention")
        await owner.execute(
            "UPDATE control.alembic_version SET version_num = '080_001'"
        )

    # The 080 body refuses 080 -> 079 (the released 080-era step).
    with pytest.raises(DBAPIError) as direct_exc:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="079_001",
        )
    underlying = direct_exc.value.orig
    assert "HEADING_ROW_EFFECT_DOWNGRADE_UNSUPPORTED" in str(underlying)
    assert getattr(underlying, "sqlstate", None) == "P0001"

    # Stage the released 079 head.  The 080 surface has no supported
    # downgrade (proved above), so a 079-era release deployment is
    # simulated at the fixture level: the owner restores the two
    # definer bodies to their original pre-080 forms from the live
    # sibling migration sources, drops the 080 recorder and facts
    # table, and stages the 079 version row.
    _m080 = importlib.import_module(
        "slaif_agent_site.db.alembic.versions.080_001_heading_row_effect"
    )
    editor_block = str(_m080._M063._legacy_composition_sql())
    _e_idx = editor_block.index(_m080._EDITOR_UPDATE_MARKER)
    _e_end = editor_block.find(_m080._EDITOR_UPDATE_END, _e_idx)
    editor_stmt = editor_block[_e_idx : _e_end + len(_m080._EDITOR_UPDATE_END)]
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for stmt in _split_statements(str(_m080._M062._component_update_sql())):
            await owner.execute(stmt)
        await owner.execute(editor_stmt)
        await owner.execute(
            "DROP FUNCTION control.slaif_heading_row_effect_record"
            "(uuid,text,uuid,uuid,uuid,uuid,integer,integer,jsonb,jsonb)"
        )
        await owner.execute("DROP TABLE audit.heading_row_effect")
        await owner.execute(
            "UPDATE control.alembic_version SET version_num = '079_001'"
        )
        for fn in (
            "slaif_agent_component_update",
            "slaif_composition_node_update",
        ):
            src = await owner.fetchrow(
                "SELECT p.prosrc FROM pg_proc p"
                " JOIN pg_namespace n ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'content' AND p.proname = $1",
                fn,
            )
            assert "slaif_heading_row_effect_record" not in src["prosrc"]
    with pytest.raises(DBAPIError) as direct_079_exc:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="078_001",
        )
    underlying_079 = direct_079_exc.value.orig
    assert "REVIEWED_OPERATION_BINDING_DOWNGRADE_REFUSED" in str(underlying_079)
    assert getattr(underlying_079, "sqlstate", None) == "P0001"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        after = await owner.fetchval("SELECT version_num FROM control.alembic_version")
        facts_present = await owner.fetchval(
            "SELECT to_regclass('audit.heading_row_effect') IS NULL"
        )
    assert after == "079_001"
    assert facts_present is True

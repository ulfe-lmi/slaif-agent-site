"""Durable DISCARD job processing: the real discard (083/2).

The discard job is the MVP conflict remedy and the "I do not want this
pending work" path.  Its sequence:

1. re-read the workspace in its own transaction (pipeline states
   ``DISCARD_QUEUED``/``DISCARDING`` only; anything else is a terminal
   ``STATE_DRIFT`` with no mutation);
2. mark ``DISCARDING`` (guarded transition; fresh claims and crash
   replays both match, and 0 rows is a terminal ``STATE_DRIFT``);
3. ONE ``asyncpg_cow_reviewer`` connection/transaction, all-or-nothing:
   the established exclusive product advisory lock (the workspace
   lifecycle key 280, the same usage the freeze and accept workers
   already use), the ``DISCARDING`` re-check under ``FOR UPDATE``, the
   foundation ``discard_session`` (which commits nothing), the guarded
   workspace ``DISCARDED`` transition (+ ``discarded_at``), and the job
   ``SUCCEEDED`` terminal.  Any failure rolls back ALL of it.

Explicit order requirement: the discard path contains NO
``dependencies(session_id)`` closure check anywhere - discard commits
nothing, so the 083/1 known foundation ``get_cow_dependencies``
composite-FK limitation cannot affect it (the report confirms by grep
that the discard path calls only ``discard_session`` plus control-table
updates).

Crash replay converges idempotently: ``discard_session`` on an
already-discarded session is a foundation no-op (no dirty tables ->
``DiscardResult`` with ``no_op=True`` and empty operations), so a
re-claimed job replays from step 1 and writes exactly one terminal.

Terminal failure classes (all with the job terminal FAILED and the
workspace returned to its origin status from the job payload -
``REVIEW`` or ``CONFLICTED`` - so there is no dead end): state drift ->
``STATE_DRIFT``; transient/infrastructure failure -> the job stays
``CLAIMED`` (stale-claim recovery re-queues under the attempt budget)
or, at budget, the origin status + ``REVIEW_JOB_STALE_AT_BUDGET``.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

import asyncpg

from ..agent_state.foundation import asyncpg_cow_reviewer
from .config import ReviewWorkerSettings
from .freeze_job import JobResult, _lock_timeout_literal, _mark_terminal

LOGGER = logging.getLogger(__name__)


class DiscardJobError(Exception):
    """A structured DISCARD failure with its stable job code."""

    def __init__(self, code: str, *, kind: str) -> None:
        """kind: state | discard."""

        super().__init__(code)
        self.code = code
        self.kind = kind


async def _set_workspace_status(
    pool: Any, workspace_id: UUID, expected: str, target: str
) -> bool:
    """Best-effort guarded workspace transition outside the job tx."""

    try:
        async with pool.acquire() as connection:
            executed = await connection.execute(
                "UPDATE control.workspace SET status=$2 WHERE id=$1 AND status=$3",
                workspace_id,
                target,
                expected,
            )
        return str(executed) == "UPDATE 1"
    except (asyncpg.PostgresError, TimeoutError, OSError):
        LOGGER.warning(
            "discard workspace transition deferred",
            extra={"event_fields": {"workspace_id": str(workspace_id)}},
        )
        return False


async def _read_workspace_status(pool: Any, workspace_id: UUID) -> str | None:
    """The workspace status, or ``None`` on a transient DB failure.

    A missing workspace is reported as ``WORKSPACE_MISSING`` (a
    terminal ``STATE_DRIFT`` at the caller).
    """

    try:
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT status FROM control.workspace WHERE id = $1",
                workspace_id,
            )
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return None
    if row is None:
        return "WORKSPACE_MISSING"
    return str(row["status"])


async def run_discard_job(
    pool: Any, settings: ReviewWorkerSettings, job: dict[str, Any]
) -> JobResult:
    """Process one claimed DISCARD job to a terminal outcome."""

    job_id = UUID(str(job["id"]))
    workspace_id = UUID(str(job["workspace_id"]))
    max_attempts = int(job["max_attempts"])
    attempt_count = int(job["attempt_count"])
    payload = job.get("payload")
    if isinstance(payload, (bytes, bytearray)):
        payload = json.loads(payload.decode("utf-8"))
    elif isinstance(payload, str):
        payload = json.loads(payload)
    origin_status: str | None = None
    if isinstance(payload, dict):
        origin = str(payload.get("origin_status") or "")
        if origin in ("REVIEW", "CONFLICTED"):
            origin_status = origin
    if origin_status is None:
        # The enqueue is the only writer of this payload; an invalid
        # shape is a structural invariant violation, not retryable.
        await _mark_terminal(pool, job_id, "FAILED", "DISCARD_PAYLOAD_INVALID")
        return JobResult("FAILED", "DISCARD_PAYLOAD_INVALID")

    def _at_budget() -> bool:
        return attempt_count >= max_attempts

    async def _retryable_or_budget() -> JobResult:
        """Retryable failure: re-queue under budget, terminate at budget."""

        if _at_budget():
            budget_code = "REVIEW_JOB_STALE_AT_BUDGET"
            await _set_workspace_status(pool, workspace_id, "DISCARDING", origin_status)
            await _mark_terminal(pool, job_id, "FAILED", budget_code)
            return JobResult("FAILED", budget_code)
        # No terminal: the job stays CLAIMED and the claim function's
        # stale-claim recovery re-queues it while the budget remains.
        # The workspace stays DISCARDING; a re-claim replays from step 1
        # and the foundation discard is a no-op if it already applied.
        return JobResult("ROLLED_BACK")

    # Step 1: re-read the workspace in its own transaction.
    workspace_status = await _read_workspace_status(pool, workspace_id)
    if workspace_status is None:
        # Transient database failure: state unknown, stay CLAIMED.
        return JobResult("ROLLED_BACK")
    if workspace_status not in ("DISCARD_QUEUED", "DISCARDING"):
        await _mark_terminal(pool, job_id, "FAILED", "STATE_DRIFT")
        return JobResult("FAILED", "STATE_DRIFT")

    # Step 2: mark DISCARDING (fresh claims transition, replays match).
    try:
        async with pool.acquire() as connection:
            result = await connection.execute(
                "UPDATE control.workspace SET status = 'DISCARDING' "
                "WHERE id = $1 AND status IN ('DISCARD_QUEUED','DISCARDING')",
                workspace_id,
            )
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return JobResult("ROLLED_BACK")
    if result != "UPDATE 1":
        await _mark_terminal(pool, job_id, "FAILED", "STATE_DRIFT")
        return JobResult("FAILED", "STATE_DRIFT")

    # Steps 3-5: the discard transaction (one reviewer scope,
    # all-or-nothing).
    try:
        async with pool.acquire() as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                await reviewer.native.execute(
                    "SET LOCAL lock_timeout = '"
                    + _lock_timeout_literal(settings.drain_lock_timeout_seconds)
                    + "'"
                )
                # Step 3: the established exclusive product lock (the
                # workspace lifecycle key 280).
                await reviewer.native.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                    str(workspace_id),
                )
                # Step 4: the DISCARDING re-check in the locked
                # transaction.
                status = await reviewer.native.fetchval(
                    "SELECT status FROM control.workspace WHERE id = $1 FOR UPDATE",
                    workspace_id,
                )
                if status != "DISCARDING":
                    raise DiscardJobError("STATE_DRIFT", kind="state")
                # Step 5: the foundation discard.  It commits nothing;
                # no dependencies() closure check is performed (order
                # R3.2.5: discard never promotes, so the 083/1
                # foundation closure-check limitation is out of the
                # discard path by design).
                discard_result = await reviewer.discard_session(
                    workspace_id, schema="content"
                )
                LOGGER.info(
                    "discard job foundation result: job=%s workspace=%s "
                    "discarded_tables=%s discarded_operations=%s "
                    "no_op=%s",
                    job_id,
                    workspace_id,
                    sorted(str(table) for table in discard_result.discarded_tables),
                    len(discard_result.discarded_operations),
                    discard_result.no_op,
                )
                updated = await reviewer.native.execute(
                    "UPDATE control.workspace SET status = 'DISCARDED', "
                    "discarded_at = now() "
                    "WHERE id = $1 AND status = 'DISCARDING'",
                    workspace_id,
                )
                if updated != "UPDATE 1":
                    raise DiscardJobError("STATE_DRIFT", kind="state")
                await reviewer.native.fetchval(
                    "SELECT control.slaif_review_job_terminal($1, 'SUCCEEDED', NULL)",
                    job_id,
                )
        return JobResult("SUCCEEDED")
    except DiscardJobError as error:
        await _set_workspace_status(pool, workspace_id, "DISCARDING", origin_status)
        await _mark_terminal(pool, job_id, "FAILED", error.code)
        return JobResult("FAILED", error.code)
    except (asyncpg.PostgresError, TimeoutError, OSError):
        # Transient failure inside the reviewer transaction: the scope
        # rolled back everything; retryable under the attempt budget.
        return await _retryable_or_budget()


__all__ = ["DiscardJobError", "run_discard_job"]

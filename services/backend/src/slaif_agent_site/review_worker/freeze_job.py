"""Durable FREEZE job processing: drain, materialize, complete (R2/R5).

One locked database transaction performs the exclusive product lock, the
freeze policy for outstanding browser runs, snapshot materialization, and
the atomic REVIEW transition; the job's terminal SUCCEEDED state commits
in the same transaction. Semantic failure paths mark the job FAILED with
a stable structured code after the transaction rolls back (the workspace
remains FREEZING, no snapshot row exists, no REVIEW state is reachable).
A job that dies mid-transaction without a terminal row stays CLAIMED and
is recovered by the claim function's stale-claim recovery under the
attempt budget.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import asyncpg

from . import snapshot
from .config import ReviewWorkerSettings

LOGGER = logging.getLogger(__name__)

_PHASE_ERROR_CODES = {
    "drain": "SNAPSHOT_MATERIALIZE_FAILED",
    "recheck": "STATE_DRIFT",
    "evidence": "SNAPSHOT_MATERIALIZE_FAILED",
    "materialize": "SNAPSHOT_MATERIALIZE_FAILED",
    "complete": "SNAPSHOT_COMPLETE_FAILED",
}
_DOMAIN_ERROR_CODES = {
    "REVIEW_WORKSPACE_NOT_FOUND": "STATE_DRIFT",
    "REVIEW_SITE_NOT_ACTIVE": "STATE_DRIFT",
    "SNAPSHOT_ROW_INVALID": "SNAPSHOT_COMPLETE_FAILED",
    "SNAPSHOT_DIGEST_MISMATCH": "SNAPSHOT_COMPLETE_FAILED",
    "WORKSPACE_NOT_FREEZING": "SNAPSHOT_COMPLETE_FAILED",
    "REVIEW_TERMINAL_INVALID": "SNAPSHOT_COMPLETE_FAILED",
    "REVIEW_JOB_NOT_CLAIMED": "SNAPSHOT_COMPLETE_FAILED",
}


@dataclass(frozen=True, slots=True)
class JobResult:
    """The terminal outcome of one claimed job.

    ``status`` is ``SUCCEEDED`` or ``FAILED`` when a terminal row was
    written, or ``ROLLED_BACK`` when the job stays CLAIMED for
    stale-claim recovery (database failure before a reliable terminal).
    """

    status: str
    error: str | None = None


def _lock_timeout_literal(seconds: float) -> str:
    return f"{seconds:g}s"


async def _drain_browser_runs(
    connection: Any,
    workspace_id: UUID,
    settings: ReviewWorkerSettings,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Wait for outstanding durable browser runs; bounded cancel on timeout.

    Returns ``(completed_evidence, cancelled_runs)``. Completed runs
    contribute evidence; cancelled runs are reported as
    ``cancelled_by_freeze`` and contribute no evidence.
    """

    loop = asyncio.get_running_loop()
    deadline = loop.time() + settings.evidence_deadline_seconds
    cancelled: list[dict[str, Any]] = []
    while True:
        outstanding = await connection.fetchval(
            "SELECT count(*) FROM control.browser_run "
            "WHERE workspace_id = $1 AND state IN ('QUEUED','RUNNING')",
            workspace_id,
        )
        if outstanding == 0:
            break
        if loop.time() >= deadline:
            report = await connection.fetchval(
                "SELECT control.slaif_review_browser_runs_cancel($1)",
                workspace_id,
            )
            if isinstance(report, str):
                report = json.loads(report)
            cancelled = list((report or {}).get("cancelled", []))
            break
        await asyncio.sleep(settings.evidence_poll_seconds)
    runs = await connection.fetch(
        "SELECT id FROM control.browser_run "
        "WHERE workspace_id = $1 AND state = 'COMPLETED' ORDER BY id",
        workspace_id,
    )
    return ([{"id": str(row["id"])} for row in runs], cancelled)


def _terminal_code_for(error: asyncpg.PostgresError, phase: str) -> str:
    """Map a semantic SQL failure to the stable job error code."""

    domain = _DOMAIN_ERROR_CODES.get(error.message or "")
    if domain is not None:
        return domain
    return _PHASE_ERROR_CODES.get(phase, "SNAPSHOT_MATERIALIZE_FAILED")


async def _mark_terminal(
    pool: Any, job_id: UUID, status: str, error: str | None
) -> bool:
    """Best-effort terminal record outside the rolled-back transaction."""

    try:
        async with pool.acquire() as connection:
            await connection.fetchval(
                "SELECT control.slaif_review_job_terminal($1, $2, $3)",
                job_id,
                status,
                error,
            )
        return True
    except (asyncpg.PostgresError, TimeoutError, OSError):
        LOGGER.warning(
            "review job terminal record deferred to stale-claim recovery",
            extra={"event_fields": {"job_id": str(job_id), "status": status}},
        )
        return False


async def run_freeze_job(
    pool: Any, settings: ReviewWorkerSettings, job: dict[str, Any]
) -> JobResult:
    """Process one claimed FREEZE job to a terminal outcome."""

    job_id = UUID(str(job["id"]))
    workspace_id = UUID(str(job["workspace_id"]))
    claimant = str(job["claimed_by"])
    max_attempts = int(job["max_attempts"])
    attempt_count = int(job["attempt_count"])
    drain_attempts = max(1, max_attempts - attempt_count + 1)

    # Step 1: re-read the workspace in its own transaction. A failed
    # re-read leaves the job CLAIMED for stale-claim recovery: the state
    # is unknown, so no terminal code may be fabricated.
    try:
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT w.status AS workspace_status, s.status AS site_status "
                "FROM control.workspace AS w "
                "JOIN control.site AS s ON s.id = w.site_id "
                "WHERE w.id = $1",
                workspace_id,
            )
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return JobResult("ROLLED_BACK")
    if (
        row is None
        or row["workspace_status"] != "FREEZING"
        or row["site_status"] != "ACTIVE"
    ):
        await _mark_terminal(pool, job_id, "FAILED", "STATE_DRIFT")
        return JobResult("FAILED", "STATE_DRIFT")

    for _drain_attempt in range(drain_attempts):
        phase = "drain"
        try:
            async with pool.acquire() as connection:
                async with connection.transaction():
                    # Step 2: the exclusive product lock (bounded drain).
                    await connection.execute(
                        "SET LOCAL lock_timeout = '"
                        + _lock_timeout_literal(settings.drain_lock_timeout_seconds)
                        + "'"
                    )
                    await connection.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                        str(workspace_id),
                    )
                    # Step 3: re-check FREEZING in the locked transaction.
                    status = await connection.fetchval(
                        "SELECT status FROM control.workspace WHERE id = $1",
                        workspace_id,
                    )
                    if status != "FREEZING":
                        raise snapshot.SnapshotBuildError(
                            "STATE_DRIFT", reason="not_freezing"
                        )
                    # Step 4: freeze policy for outstanding browser runs.
                    phase = "evidence"
                    evidence, cancelled = await _drain_browser_runs(
                        connection, workspace_id, settings
                    )
                    # Step 5: materialize through the trusted SQL surface.
                    phase = "materialize"
                    doc = await connection.fetchval(
                        "SELECT control.slaif_review_workspace_state($1)",
                        workspace_id,
                    )
                    row_doc = snapshot.build_snapshot_document(
                        doc,
                        created_by=claimant,
                        browser_evidence=evidence,
                        cancelled_runs=cancelled,
                    )
                    # Step 6: atomic snapshot insert + REVIEW transition.
                    phase = "complete"
                    await connection.fetchval(
                        "SELECT control.slaif_review_snapshot_complete($1, $2)",
                        workspace_id,
                        json.dumps(row_doc, sort_keys=True, separators=(",", ":")),
                    )
                    # Step 7: job SUCCEEDED, same transaction.
                    await connection.fetchval(
                        "SELECT control.slaif_review_job_terminal("
                        "$1, 'SUCCEEDED', NULL)",
                        job_id,
                    )
        except snapshot.SnapshotBuildError as error:
            code = error.code
            LOGGER.exception(
                "freeze job failed: job=%s workspace=%s code=%s",
                job_id,
                workspace_id,
                code,
            )
            await _mark_terminal(pool, job_id, "FAILED", code)
            return JobResult("FAILED", code)
        except asyncpg.PostgresError as error:
            if error.sqlstate == "55P03" and phase == "drain":
                if _drain_attempt < drain_attempts - 1:
                    await asyncio.sleep(1.0)
                    continue
                await _mark_terminal(pool, job_id, "FAILED", "DRAIN_TIMEOUT")
                return JobResult("FAILED", "DRAIN_TIMEOUT")
            code = _terminal_code_for(error, phase)
            LOGGER.exception(
                "freeze job database failure: job=%s workspace=%s phase=%s code=%s",
                job_id,
                workspace_id,
                phase,
                code,
            )
            await _mark_terminal(pool, job_id, "FAILED", code)
            return JobResult("FAILED", code)
        except (TimeoutError, OSError):
            return JobResult("ROLLED_BACK")
        else:
            return JobResult("SUCCEEDED")
    await _mark_terminal(pool, job_id, "FAILED", "DRAIN_TIMEOUT")
    return JobResult("FAILED", "DRAIN_TIMEOUT")


async def run_job(
    pool: Any, settings: ReviewWorkerSettings, job: dict[str, Any]
) -> JobResult:
    """Dispatch one claimed job by kind (FREEZE + ACCEPT + DISCARD)."""

    kind = str(job.get("job_kind"))
    if kind == "FREEZE":
        return await run_freeze_job(pool, settings, job)
    if kind == "ACCEPT":
        from .accept_job import run_accept_job, shared_media_boundary

        return await run_accept_job(pool, settings, job, shared_media_boundary())
    if kind == "DISCARD":
        from .discard_job import run_discard_job

        return await run_discard_job(pool, settings, job)
    job_id = UUID(str(job["id"]))
    code = "JOB_KIND_UNSUPPORTED"
    await _mark_terminal(pool, job_id, "FAILED", code)
    return JobResult("FAILED", code)


__all__ = ["JobResult", "run_freeze_job", "run_job"]

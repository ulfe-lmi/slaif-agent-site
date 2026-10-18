"""Durable review worker: bounded poll/claim/execute loop over review jobs."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

import asyncpg

from .accept_job import shutdown_media_boundary
from .config import ReviewWorkerConfigurationError, ReviewWorkerSettings
from .freeze_job import JobResult, run_job
from .outbox_consumer import consume_outbox_round, outbox_round_due

LOGGER = logging.getLogger(__name__)


def _claimant_identity() -> str:
    return f"review-worker-{uuid.uuid4().hex[:12]}"


async def _verify_connection(connection: Any, settings: ReviewWorkerSettings) -> None:
    """Fail fast unless the connection uses the narrow worker credential."""

    row = await connection.fetchrow(
        "SELECT current_database()::text, session_user::text, "
        "current_user::text, ARRAY("
        "SELECT target.rolname::text FROM pg_catalog.pg_roles target "
        "WHERE target.rolname = ANY($1::text[]) "
        "AND pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
        "ORDER BY target.rolname)",
        [settings.expected_privilege_role],
    )
    if (
        row is None
        or tuple(row[:3])
        != (
            settings.expected_database,
            settings.expected_login,
            settings.expected_login,
        )
        or tuple(row[3]) != (settings.expected_privilege_role,)
    ):
        raise ReviewWorkerConfigurationError(
            "Invalid SLAIF review-worker configuration."
        )


async def _wait_for_stop(stop: asyncio.Event, timeout: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), timeout=timeout)
    except TimeoutError:
        pass


async def _heartbeat_loop(
    pool: Any,
    job: dict[str, Any],
    settings: ReviewWorkerSettings,
    stop: asyncio.Event,
) -> None:
    """Keep the claimed job fresh on a separate connection while it runs."""

    job_id = str(job["id"])
    while not stop.is_set():
        await _wait_for_stop(stop, settings.heartbeat_interval_seconds)
        if stop.is_set():
            break
        try:
            async with pool.acquire() as connection:
                await connection.fetchval(
                    "SELECT control.slaif_review_job_heartbeat($1)", job_id
                )
        except (asyncpg.PostgresError, TimeoutError, OSError):
            LOGGER.warning(
                "review job heartbeat missed",
                extra={"event_fields": {"job_id": job_id}},
            )


async def _worker_loop(
    pool: Any, settings: ReviewWorkerSettings, stop: asyncio.Event
) -> None:
    """Claim/execute loop over the durable review-job queue (batch 1)."""

    claimant = _claimant_identity()
    LOGGER.info(
        "review worker started",
        extra={"event_fields": {"claimant": claimant}},
    )
    last_outbox_run: float | None = None
    while not stop.is_set():
        job: dict[str, Any] | None = None
        try:
            async with pool.acquire() as connection:
                job_row = await connection.fetchrow(
                    "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                    claimant,
                    ["FREEZE", "ACCEPT", "DISCARD"],
                )
            job = dict(job_row) if job_row is not None else None
        except (asyncpg.PostgresError, TimeoutError, OSError):
            LOGGER.warning(
                "review job claim unavailable",
                extra={"event_fields": {"claimant": claimant}},
            )
        if job is None:
            await _wait_for_stop(stop, settings.poll_interval_seconds)
        else:
            LOGGER.info(
                "review job claimed",
                extra={
                    "event_fields": {
                        "job_id": str(job["id"]),
                        "workspace_id": str(job["workspace_id"]),
                        "job_kind": str(job["job_kind"]),
                        "attempt": int(job["attempt_count"]),
                    }
                },
            )
            heartbeat = asyncio.create_task(_heartbeat_loop(pool, job, settings, stop))
            try:
                result: JobResult
                try:
                    result = await run_job(pool, settings, job)
                except Exception:
                    LOGGER.exception(
                        "review job crashed without a terminal record",
                        extra={"event_fields": {"job_id": str(job["id"])}},
                    )
                    result = JobResult("ROLLED_BACK")
            finally:
                heartbeat.cancel()
                try:
                    await heartbeat
                except asyncio.CancelledError:
                    pass
            LOGGER.info(
                "review job finished",
                extra={
                    "event_fields": {
                        "job_id": str(job["id"]),
                        "status": result.status,
                        "error": result.error,
                    }
                },
            )
        # Durable cache-outbox round (083/3): last-run gated, first
        # run on worker start, after each job-claim cycle.
        if outbox_round_due(
            last_outbox_run,
            time.monotonic(),
            settings.outbox_poll_interval_seconds,
        ):
            processed = await consume_outbox_round(pool, settings)
            if processed:
                LOGGER.info(
                    "outbox rows processed",
                    extra={"event_fields": {"processed": processed}},
                )
            last_outbox_run = time.monotonic()


async def run_review_worker(
    stop: asyncio.Event, settings: ReviewWorkerSettings | None = None
) -> None:
    """Connect with the narrow worker credential and run the claim loop."""

    settings = settings or ReviewWorkerSettings.load()
    dsn = settings.resolved_dsn().get_secret_value()

    async def _initialize(connection: Any) -> None:
        await _verify_connection(connection, settings)

    try:
        pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=2,
            server_settings=settings.server_settings,
            init=_initialize,
        )
    except (asyncpg.PostgresError, TimeoutError, OSError):
        raise ReviewWorkerConfigurationError(
            "Invalid SLAIF review-worker configuration."
        ) from None
    try:
        await _worker_loop(pool, settings, stop)
    finally:
        await shutdown_media_boundary()
        await pool.close()
        LOGGER.info("review worker stopped")


__all__ = ["run_review_worker"]

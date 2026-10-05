"""Durable ACCEPT job processing: the real human promotion (083/1).

The accept job is the only promotion path in the product.  Its sequence:

1. re-read the workspace in its own transaction (pipeline states
   ``ACCEPT_QUEUED``/``PROMOTING`` only; anything else is a terminal
   ``STATE_DRIFT`` with no mutation);
2. mark ``PROMOTING`` (fresh claims only);
3. a locked verification transaction: the established exclusive product
   lock (the workspace lifecycle key 280, the same usage the freeze
   worker already uses), the ``PROMOTING`` re-check, the site
   ``canonical_revision`` drift gate under ``FOR UPDATE``, and the
   re-materialization + digest/versions re-validation through the exact
   082/1 snapshot path (the materializer sets a transaction-local COW
   context GUC, so it runs in this separate transaction, never inside
   the reviewer transaction);
4. media finalization FIRST (before the commit) through the lazily
   built media boundary (``store_unavailable``/
   ``repository_unavailable`` are retryable; an unresolvable media
   reference is a validation failure);
5. ONE ``asyncpg_cow_reviewer`` transaction, all-or-nothing: advisory
   lock, ``PROMOTING`` re-check, the authoritative drift gate on the
   locked site row, the operation-watermark closure check through the
   foundation, ``commit_session(conflict_policy='error')``, the
   canonical revision increment, the ``audit.promotion`` row, the
   workspace ``ACCEPTED`` transition, the job ``SUCCEEDED`` terminal,
   and the ``control.cache_outbox`` row.  Any failure (including a
   ``CowConflictError``) rolls back ALL of it.

Terminal failure classes (all with the job terminal FAILED and the
workspace returned to a human-actionable state): drift -> ``REVIEW`` +
``SITE_REVISION_CHANGED``; validation -> ``REVIEW`` +
``SNAPSHOT_VALIDATION_FAILED``; conflict -> ``CONFLICTED`` + the
structured ``BASE_ROW_*``/``BASE_SCHEMA_CHANGED`` code; crash (no
terminal) -> the job stays ``CLAIMED`` and the claim function's
stale-claim recovery re-queues it under the attempt budget; at budget
the handler writes ``REVIEW_JOB_STALE_AT_BUDGET`` + ``REVIEW`` so there
is no dead end.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

import asyncpg

from ..agent_state.foundation import CowConflictError, asyncpg_cow_reviewer
from ..media_service.config import (
    MediaDatabaseConfigurationError,
    MediaSettings,
)
from ..media_service.database import MediaDatabase
from ..media_service.finalize import (
    FinalizationError,
    FinalizationManifest,
    MediaFinalizationRepository,
    finalize_media_for_promotion,
)
from ..media_service.store import MediaStore
from . import snapshot as snapshot_module
from .config import ReviewWorkerSettings
from .freeze_job import JobResult, _lock_timeout_literal, _mark_terminal

LOGGER = logging.getLogger(__name__)

# Finalization reasons that retry can legitimately heal.
_RETRYABLE_FINALIZATION_REASONS = frozenset(
    {"store_unavailable", "repository_unavailable"}
)
_CONFLICT_KINDS = frozenset(
    {"BASE_ROW_CHANGED", "BASE_ROW_DELETED", "BASE_ROW_CREATED", "BASE_SCHEMA_CHANGED"}
)


class AcceptJobError(Exception):
    """A structured ACCEPT failure with its stable job code."""

    def __init__(self, code: str, *, kind: str) -> None:
        """kind: drift | validation | conflict | state | promotion."""

        super().__init__(code)
        self.code = code
        self.kind = kind


class MediaBoundary:
    """The lazily built media finalization boundary (ACCEPT jobs only).

    Built from the worker process environment on first use (compose
    mounts the media secret + data volume); freeze jobs never touch it.
    An explicit ``settings`` injects a test locator.
    """

    def __init__(self, settings: MediaSettings | None = None) -> None:
        self._settings = settings
        self._database: MediaDatabase | None = None
        self._store: MediaStore | None = None
        self._lock = asyncio.Lock()

    async def finalize(
        self,
        site_id: UUID,
        workspace_id: UUID,
        media_ids: list[UUID],
    ) -> FinalizationManifest:
        async with self._lock:
            if self._database is None or self._store is None:
                selected = self._settings or MediaSettings.load()
                database = MediaDatabase(selected)
                await database.start()
                self._database = database
                self._store = MediaStore(
                    selected.media_root,
                    max_upload_bytes=selected.max_upload_bytes,
                )
        assert self._database is not None and self._store is not None
        repository = MediaFinalizationRepository(self._database)
        return await finalize_media_for_promotion(
            site_id, workspace_id, media_ids, store=self._store, repository=repository
        )

    async def stop(self) -> None:
        async with self._lock:
            database, self._database = self._database, None
            self._store = None
        if database is not None:
            await database.stop()


_shared_boundary: MediaBoundary | None = None


def shared_media_boundary() -> MediaBoundary:
    """The process-lifetime media boundary (one pool, shut down once)."""

    global _shared_boundary
    if _shared_boundary is None:
        _shared_boundary = MediaBoundary()
    return _shared_boundary


async def shutdown_media_boundary() -> None:
    """Shut the shared media boundary down with the process."""

    global _shared_boundary
    boundary, _shared_boundary = _shared_boundary, None
    if boundary is not None:
        await boundary.stop()


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
            "accept workspace transition deferred",
            extra={"event_fields": {"workspace_id": str(workspace_id)}},
        )
        return False


def _payload_uuid(payload: Any, key: str) -> UUID:
    return UUID(str(payload[key]))


def _conflict_code(conflicts: Any) -> str:
    """Map structured conflicts to the stable job code (first kind wins)."""

    kinds = {
        str(conflict.get("conflict_kind", ""))
        for conflict in (conflicts or ())
        if isinstance(conflict, dict)
    }
    for kind in sorted(kinds):
        if kind in _CONFLICT_KINDS:
            return kind
    return "BASE_ROW_CHANGED"


async def _read_pipeline_state(
    pool: Any, workspace_id: UUID
) -> tuple[str | None, str | None]:
    """(workspace_status, site_status) or (None, None) on a transient DB failure."""

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
        return None, None
    if row is None:
        return None, "SITE_MISSING"
    return str(row["workspace_status"]), str(row["site_status"])


async def _verify_snapshot(
    pool: Any,
    *,
    workspace_id: UUID,
    site_id: UUID,
    snapshot_id: UUID,
    claimant: str,
    lock_timeout_seconds: float,
) -> dict[str, Any]:
    """Locked re-materialization + digest/versions re-validation (step 3).

    Returns the verified snapshot facts for the promotion transaction.
    Raises ``AcceptJobError`` (drift/validation/state) or propagates a
    transient database failure (the caller rolls back to CLAIMED).
    """

    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "SET LOCAL lock_timeout = '"
                    + _lock_timeout_literal(lock_timeout_seconds)
                    + "'"
                )
                await connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                    str(workspace_id),
                )
                status = await connection.fetchval(
                    "SELECT status FROM control.workspace WHERE id = $1 FOR UPDATE",
                    workspace_id,
                )
                if status != "PROMOTING":
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                base_site_revision = await connection.fetchval(
                    "SELECT canonical_revision FROM control.site "
                    "WHERE id = $1 FOR UPDATE",
                    site_id,
                )
                stored = await connection.fetchrow(
                    "SELECT digest, versions, normalized_state, "
                    "media_references FROM control.review_snapshot "
                    "WHERE id = $1",
                    snapshot_id,
                )
                if stored is None:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                doc = await connection.fetchval(
                    "SELECT control.slaif_review_workspace_state($1)",
                    workspace_id,
                )
    except (asyncpg.PostgresError, TimeoutError, OSError) as error:
        message = str(error)
        if "REVIEW_WORKSPACE_NOT_FOUND" in message:
            raise AcceptJobError("STATE_DRIFT", kind="state") from None
        if "REVIEW_SITE_NOT_ACTIVE" in message:
            raise AcceptJobError("STATE_DRIFT", kind="state") from None
        raise
    # asyncpg 0.31.0 returns jsonb as str: decode the materialized doc
    # here so the replay normalization below sees the media dict (the
    # same str behavior the other jsonb reads guard against).
    if isinstance(doc, (bytes, bytearray)):
        doc = json.loads(doc.decode("utf-8"))
    elif isinstance(doc, str):
        try:
            doc = json.loads(doc)
        except ValueError:
            raise AcceptJobError(
                "SNAPSHOT_VALIDATION_FAILED", kind="validation"
            ) from None
    media_references = stored["media_references"]
    if isinstance(media_references, (bytes, bytearray)):
        media_references = json.loads(media_references.decode("utf-8"))
    elif isinstance(media_references, str):
        media_references = json.loads(media_references)
    # Crash-replay idempotency (R3.10): media finalization (step 4,
    # before the commit) marks the snapshot's referenced media public
    # directly on the canonical base. A job re-claimed after a crash
    # therefore observes exactly that private -> public flip. Normalize
    # the re-materialized doc back to the freeze-time status for the
    # snapshot-referenced media set before the digest comparison so the
    # replay re-validates and commits exactly once; media outside the
    # set keep their observed status, and every other drift still fails
    # closed.
    frozen_status_by_id: dict[str, str] = {}
    if isinstance(media_references, list):
        for reference in media_references:
            if isinstance(reference, dict) and isinstance(reference.get("id"), str):
                frozen_status_by_id[str(reference["id"])] = str(
                    reference.get("public_status")
                )
    if isinstance(doc, dict) and isinstance(doc.get("media"), dict):
        for media_key, descriptor in doc["media"].items():
            if (
                frozen_status_by_id.get(str(media_key)) == "private"
                and isinstance(descriptor, dict)
                and descriptor.get("public_status") == "public"
            ):
                descriptor["public_status"] = "private"
    try:
        fresh = snapshot_module.build_snapshot_document(doc, created_by=claimant)
    except snapshot_module.SnapshotBuildError as error:
        raise AcceptJobError(
            error.code or "SNAPSHOT_VALIDATION_FAILED", kind="validation"
        ) from None
    if str(fresh["digest"]) != str(stored["digest"]):
        raise AcceptJobError("SNAPSHOT_VALIDATION_FAILED", kind="validation")
    versions = stored["versions"]
    if isinstance(versions, (bytes, bytearray)):
        versions = json.loads(versions.decode("utf-8"))
    elif isinstance(versions, str):
        versions = json.loads(versions)
    if fresh["versions"] != versions:
        raise AcceptJobError("SNAPSHOT_VALIDATION_FAILED", kind="validation")
    normalized = stored["normalized_state"]
    if isinstance(normalized, (bytes, bytearray)):
        normalized = json.loads(normalized.decode("utf-8"))
    elif isinstance(normalized, str):
        normalized = json.loads(normalized)
    if not isinstance(normalized, dict):
        raise AcceptJobError("SNAPSHOT_VALIDATION_FAILED", kind="validation")
    try:
        stored_base_revision = int(normalized["base_site_revision"])
    except (KeyError, TypeError, ValueError):
        raise AcceptJobError("SNAPSHOT_VALIDATION_FAILED", kind="validation") from None
    if int(base_site_revision) != stored_base_revision:
        raise AcceptJobError("SITE_REVISION_CHANGED", kind="drift")
    media_ids: list[UUID] = []
    if isinstance(media_references, list):
        for reference in media_references:
            if isinstance(reference, dict) and "id" in reference:
                try:
                    media_ids.append(UUID(str(reference["id"])))
                except ValueError:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
    return {
        "snapshot_id": snapshot_id,
        "digest": str(stored["digest"]),
        "versions": fresh["versions"],
        "base_site_revision": stored_base_revision,
        "media_ids": media_ids,
        "media_manifest": None,
    }


async def run_accept_job(
    pool: Any,
    settings: ReviewWorkerSettings,
    job: dict[str, Any],
    media: MediaBoundary | None = None,
) -> JobResult:
    """Process one claimed ACCEPT job to a terminal outcome."""

    job_id = UUID(str(job["id"]))
    workspace_id = UUID(str(job["workspace_id"]))
    site_id = UUID(str(job["site_id"]))
    claimant = str(job["claimed_by"])
    max_attempts = int(job["max_attempts"])
    attempt_count = int(job["attempt_count"])
    boundary = media if media is not None else shared_media_boundary()
    payload = job.get("payload")
    if isinstance(payload, (bytes, bytearray)):
        payload = json.loads(payload.decode("utf-8"))
    elif isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        await _mark_terminal(pool, job_id, "FAILED", "SNAPSHOT_VALIDATION_FAILED")
        return JobResult("FAILED", "SNAPSHOT_VALIDATION_FAILED")
    try:
        snapshot_id = _payload_uuid(payload, "snapshot_id")
        actor_user_account_id = _payload_uuid(payload, "actor_user_account_id")
    except (KeyError, TypeError, ValueError):
        await _mark_terminal(pool, job_id, "FAILED", "SNAPSHOT_VALIDATION_FAILED")
        return JobResult("FAILED", "SNAPSHOT_VALIDATION_FAILED")

    def _at_budget() -> bool:
        return attempt_count >= max_attempts

    async def _retryable_or_budget() -> JobResult:
        """Retryable failure: re-queue under budget, terminate at budget."""

        if _at_budget():
            budget_code = "REVIEW_JOB_STALE_AT_BUDGET"
            await _set_workspace_status(pool, workspace_id, "PROMOTING", "REVIEW")
            await _mark_terminal(pool, job_id, "FAILED", budget_code)
            return JobResult("FAILED", budget_code)
        await _set_workspace_status(pool, workspace_id, "PROMOTING", "ACCEPT_QUEUED")
        # No terminal: the job stays CLAIMED and the claim function's
        # stale-claim recovery re-queues it while the budget remains.
        return JobResult("ROLLED_BACK")

    # Step 1: re-read the workspace in its own transaction.
    workspace_status, site_status = await _read_pipeline_state(pool, workspace_id)
    if workspace_status is None and site_status is None:
        # Transient database failure: state unknown, stay CLAIMED.
        return JobResult("ROLLED_BACK")
    if (
        workspace_status not in ("ACCEPT_QUEUED", "PROMOTING")
        or site_status != "ACTIVE"
    ):
        if workspace_status in ("ACCEPT_QUEUED", "PROMOTING"):
            await _set_workspace_status(pool, workspace_id, workspace_status, "REVIEW")
        await _mark_terminal(pool, job_id, "FAILED", "STATE_DRIFT")
        return JobResult("FAILED", "STATE_DRIFT")

    # Step 2: fresh claims mark PROMOTING (replays already are).
    if workspace_status == "ACCEPT_QUEUED":
        try:
            async with pool.acquire() as connection:
                result = await connection.execute(
                    "UPDATE control.workspace SET status = 'PROMOTING' "
                    "WHERE id = $1 AND status = 'ACCEPT_QUEUED'",
                    workspace_id,
                )
        except (asyncpg.PostgresError, TimeoutError, OSError):
            return JobResult("ROLLED_BACK")
        if result != "UPDATE 1":
            await _mark_terminal(pool, job_id, "FAILED", "STATE_DRIFT")
            return JobResult("FAILED", "STATE_DRIFT")

    # Step 3: locked verification (drift gate + re-validation).
    try:
        facts = await _verify_snapshot(
            pool,
            workspace_id=workspace_id,
            site_id=site_id,
            snapshot_id=snapshot_id,
            claimant=claimant,
            lock_timeout_seconds=settings.drain_lock_timeout_seconds,
        )
    except AcceptJobError as error:
        if error.kind == "drift":
            await _set_workspace_status(pool, workspace_id, "PROMOTING", "REVIEW")
        elif error.kind == "validation":
            await _set_workspace_status(pool, workspace_id, "PROMOTING", "REVIEW")
        await _mark_terminal(pool, job_id, "FAILED", error.code)
        return JobResult("FAILED", error.code)
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return JobResult("ROLLED_BACK")

    # Step 4: media finalization FIRST (before the commit).
    try:
        manifest = await boundary.finalize(site_id, workspace_id, facts["media_ids"])
    except FinalizationError as error:
        if error.reason in _RETRYABLE_FINALIZATION_REASONS:
            LOGGER.warning(
                "accept media finalization retryable: job=%s reason=%s",
                job_id,
                error.reason,
            )
            return await _retryable_or_budget()
        await _set_workspace_status(pool, workspace_id, "PROMOTING", "REVIEW")
        await _mark_terminal(pool, job_id, "FAILED", "SNAPSHOT_VALIDATION_FAILED")
        return JobResult("FAILED", "SNAPSHOT_VALIDATION_FAILED")
    except MediaDatabaseConfigurationError:
        return await _retryable_or_budget()
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return JobResult("ROLLED_BACK")
    facts["media_manifest"] = manifest.to_list()

    # Step 5: the promotion transaction (one reviewer scope, all-or-nothing).
    try:
        async with pool.acquire() as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                await reviewer.native.execute(
                    "SET LOCAL lock_timeout = '"
                    + _lock_timeout_literal(settings.drain_lock_timeout_seconds)
                    + "'"
                )
                await reviewer.native.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                    str(workspace_id),
                )
                status = await reviewer.native.fetchval(
                    "SELECT status FROM control.workspace WHERE id = $1 FOR UPDATE",
                    workspace_id,
                )
                if status != "PROMOTING":
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                revision = await reviewer.native.fetchval(
                    "SELECT canonical_revision FROM control.site "
                    "WHERE id = $1 FOR UPDATE",
                    site_id,
                )
                if int(revision) != facts["base_site_revision"]:
                    raise AcceptJobError("SITE_REVISION_CHANGED", kind="drift")
                operations = await reviewer.operations(workspace_id, schema="content")
                dependencies = await reviewer.dependencies(
                    workspace_id, schema="content"
                )
                operation_set = set(operations)
                if any(parent not in operation_set for parent, _child in dependencies):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                try:
                    result = await reviewer.commit_session(
                        workspace_id,
                        schema="content",
                        defer_fk_constraints=True,
                        conflict_policy="error",
                    )
                except CowConflictError as error:
                    raise AcceptJobError(
                        _conflict_code(error.conflicts), kind="conflict"
                    ) from None
                new_revision = await reviewer.native.fetchval(
                    "UPDATE control.site SET canonical_revision = "
                    "canonical_revision + 1 WHERE id = $1 RETURNING "
                    "canonical_revision",
                    site_id,
                )
                await reviewer.native.execute(
                    "INSERT INTO audit.promotion "
                    "(site_id, workspace_id, snapshot_id, job_id, digest, "
                    "base_site_revision, new_canonical_revision, "
                    "committed_operations, versions, actor_user_account_id) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
                    site_id,
                    workspace_id,
                    facts["snapshot_id"],
                    job_id,
                    facts["digest"],
                    facts["base_site_revision"],
                    int(new_revision),
                    len(result.committed_operations),
                    json.dumps(
                        facts["versions"], sort_keys=True, separators=(",", ":")
                    ),
                    actor_user_account_id,
                )
                updated = await reviewer.native.execute(
                    "UPDATE control.workspace SET status = 'ACCEPTED', "
                    "accepted_at = now() WHERE id = $1 AND status = 'PROMOTING'",
                    workspace_id,
                )
                if updated != "UPDATE 1":
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                await reviewer.native.fetchval(
                    "SELECT control.slaif_review_job_terminal($1, 'SUCCEEDED', NULL)",
                    job_id,
                )
                await reviewer.native.execute(
                    "INSERT INTO control.cache_outbox "
                    "(site_id, workspace_id, event_kind, payload) "
                    "VALUES ($1, $2, 'WORKSPACE_ACCEPTED', $3)",
                    site_id,
                    workspace_id,
                    json.dumps(
                        {
                            "snapshot_id": str(facts["snapshot_id"]),
                            "digest": facts["digest"],
                            "base_site_revision": facts["base_site_revision"],
                            "new_canonical_revision": int(new_revision),
                            "media_manifest": facts["media_manifest"],
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
        return JobResult("SUCCEEDED")
    except AcceptJobError as error:
        if error.kind == "drift" or error.kind == "validation":
            await _set_workspace_status(pool, workspace_id, "PROMOTING", "REVIEW")
        elif error.kind == "conflict":
            await _set_workspace_status(pool, workspace_id, "PROMOTING", "CONFLICTED")
        await _mark_terminal(pool, job_id, "FAILED", error.code)
        return JobResult("FAILED", error.code)
    except (asyncpg.PostgresError, TimeoutError, OSError):
        # Transient failure inside the reviewer transaction: the scope
        # rolled back everything; the job stays CLAIMED for recovery.
        return await _retryable_or_budget()


__all__ = [
    "AcceptJobError",
    "MediaBoundary",
    "run_accept_job",
    "shutdown_media_boundary",
    "shared_media_boundary",
]

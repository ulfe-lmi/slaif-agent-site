"""Durable ACCEPT job processing: the real human promotion (083/1).

The accept job is the only promotion path in the product.  Its sequence:

1. re-read the workspace in its own transaction (pipeline states
   ``ACCEPT_QUEUED``/``PROMOTING`` only; anything else is a terminal
   ``STATE_DRIFT`` with no mutation);
2. mark ``PROMOTING`` (fresh claims only);
3. a locked verification transaction: the established exclusive product
   lock (the workspace lifecycle key 280, the same usage the freeze
   worker already uses), the ``PROMOTING`` re-check, the site
   ``canonical_revision`` drift gate under ``FOR UPDATE``, the stored
   snapshot/site/workspace binding check, and the trusted stored
   ``base_site_revision`` checked against that locked current revision
   BEFORE the re-materialization + digest/versions re-validation
   through the exact 082/1 snapshot path (a post-freeze publication
   therefore fails as ``SITE_REVISION_CHANGED`` drift, never obscured
   by a re-materialized digest mismatch; the materializer sets a
   transaction-local COW context GUC, so it runs in this separate
   transaction, never inside the reviewer transaction);
4. media byte preparation FIRST (before the commit) through the lazily
   built media boundary: each referenced media is resolved in the
   workspace's COW context (pending assets included), digest-verified
   and idempotently copied to the public namespace — byte preparation
   only, no database status mutation (``store_unavailable``/
   ``repository_unavailable`` are retryable; an unresolvable media
   reference is a validation failure);
5. ONE ``asyncpg_cow_reviewer`` transaction, all-or-nothing: advisory
   lock, ``PROMOTING`` re-check, the authoritative drift gate on the
   locked site row, the stored domain approval re-verification on the
   locked connection (exact durable approval tuple, binding, versions
   and normalized-state shapes), the live manifest/U/dependency/provenance
   re-checks, ``commit_session(conflict_policy='error')``, the
   in-transaction publication mark (the least-authority
   ``content.slaif_media_publicize_promoted`` helper over exactly the
   promoted, base-referenced media), the canonical revision increment,
   the ``audit.promotion`` row, the workspace ``ACCEPTED`` transition,
   the job ``SUCCEEDED`` terminal, and the ``control.cache_outbox``
   row.  Any failure (including a ``CowConflictError`` or a unique
   constraint conflict) rolls back ALL of it.

Terminal failure classes (all with the job terminal FAILED and the
workspace returned to a human-actionable state): drift -> ``REVIEW`` +
``SITE_REVISION_CHANGED`` (checked before re-materialization, so drift
always outranks compatibility); unsupported stored version facts ->
``REVIEW`` + ``SNAPSHOT_COMPATIBILITY_REFUSED`` (stable compatibility
refusal, never retryable); validation -> ``REVIEW`` +
``SNAPSHOT_VALIDATION_FAILED``; conflict -> ``CONFLICTED`` + the
structured ``BASE_ROW_*``/``BASE_SCHEMA_CHANGED`` code; crash (no
terminal) -> the job stays ``CLAIMED`` and the claim function's
stale-claim recovery re-queues it under the attempt budget; at budget
the handler writes ``REVIEW_JOB_STALE_AT_BUDGET`` + ``REVIEW`` so there
is no dead end.

Every recovery state change (workspace transition and/or job terminal
mark) is made inside ONE transaction under locked reads: the workspace
row is locked first, then the job row (the promotion-transaction and
enqueue lock order), and the job must still be CLAIMED by exactly this
attempt (claimant, attempt count, site/workspace binding and - whenever
the payload carries them - the exact dual approval digest).  Verify and
write are atomic, so a claim that moves in the gap the separate
verify-then-write sequence used to leave can never be overwritten: it
blocks on the locked rows and then sees the terminal/transitioned
state.  A lost or unverifiable claim makes NO write at all and leaves
recovery to the claim function's stale-claim handling.  The promotion
transaction itself re-verifies the durable claim under its own locks
(job payload, snapshot and dual digests, claimant, attempt, binding)
BEFORE any publication step.

An uncertain reviewer-transaction outcome (a driver or interface
failure, including scope/pool cleanup AFTER a possible native commit)
is reconciled against the EXACT durable publication receipt: the job
must be SUCCEEDED, the workspace ACCEPTED, and the narrow owner-definer
promotion-receipt read must return exactly ONE audit.promotion row for
this job matching every approval fact (site/workspace/snapshot, both
digests, manifest identity, base and incremented revision, actor,
versions and the applied operation IDs).  Only that fingerprint
authorizes recovered success (never re-run).  A SUCCEEDED job without
the exact receipt, an ambiguous multiple-row receipt, or ANY receipt on
a nonterminal claim is contradictory: uncertain, fail-closed, no state
change and no re-queue.  Re-queue is authorized only when NO receipt
exists at all and this attempt still verifiably owns the claim.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Literal
from uuid import UUID

import asyncpg

from ..agent_state.foundation import (
    CowConflictError,
    CowPromotionStateError,
    asyncpg_cow_reviewer,
)
from ..content_model.canonical import (
    canonical_digest,
    canonical_json,
    parse_snapshot_text,
)
from ..media_service.config import (
    MediaDatabaseConfigurationError,
    MediaSettings,
)
from ..media_service.database import MediaDatabase
from ..media_service.finalize import (
    FinalizationError,
    FinalizationManifest,
    FinalizationRepositoryError,
    MediaFinalizationRepository,
    finalize_media_for_promotion,
    log_bounded_db_failure,
    publicize_promoted_media,
)
from ..media_service.store import MediaStore
from . import operation_manifest
from . import snapshot as snapshot_module
from .config import ReviewWorkerSettings
from .freeze_job import JobResult, _lock_timeout_literal
from .operation_manifest import build_operation_manifest

LOGGER = logging.getLogger(__name__)

# Finalization reasons that retry can legitimately heal.
_RETRYABLE_FINALIZATION_REASONS = frozenset(
    {"store_unavailable", "repository_unavailable"}
)
_CONFLICT_KINDS = frozenset(
    {"BASE_ROW_CHANGED", "BASE_ROW_DELETED", "BASE_ROW_CREATED", "BASE_SCHEMA_CHANGED"}
)

# Recognized stable semantic failures of the trusted re-
# materialization (076).  Given the locked data they are
# deterministic, so a retry can never heal them: the job goes
# terminal FAILED (workspace REVIEW) with the mapped stable code
# BEFORE any replay, media finalization or canonical effect.
# Anything not recognized here stays a true transient (lock,
# timeout, connection) and remains retryable ROLLED_BACK.
# 083/12: the trusted whole-workspace provenance refusal (typed
# SQLSTATE P0001/P0003 messages from the definer check).  Any of these
# means the reviewer transaction must refuse BEFORE publication; any
# other error stays a true transient and remains retryable.
_PROVENANCE_REFUSALS = frozenset(
    {
        "PROVENANCE_INPUT_INVALID",
        "PROVENANCE_MISSING",
        "PROVENANCE_RESERVATION_MISMATCH",
        "PROVENANCE_EVENT_MISMATCH",
        "PROVENANCE_CONFLICT",
    }
)
_DIGEST_64_RE = re.compile(r"^[0-9a-f]{64}$")
_STABLE_MATERIALIZER_FAILURES = {
    "REVIEW_WORKSPACE_VERSION_UNKNOWN": "SNAPSHOT_COMPATIBILITY_REFUSED",
    "SNAPSHOT_WORKSPACE_VERSIONS_UNSUPPORTED": "SNAPSHOT_COMPATIBILITY_REFUSED",
    "SNAPSHOT_WORKSPACE_VERSIONS_MISMATCH": "SNAPSHOT_COMPATIBILITY_REFUSED",
    "SNAPSHOT_VALIDATION_FAILED": "SNAPSHOT_VALIDATION_FAILED",
    "REVIEW_SNAPSHOT_OVER_BUDGET": "SNAPSHOT_VALIDATION_FAILED",
    "REVIEW_MEDIA_REF_UNRESOLVED": "SNAPSHOT_VALIDATION_FAILED",
    "REVIEW_STRING_COST_INVALID_UTF8": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_MEDIA_REFERENCES_MISMATCH": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_ROW_INVALID": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_DIGEST_MISMATCH": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_STATE_PAYLOAD_DIVERGED": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_SITE_MISMATCH": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_PAYLOAD_INVALID": "SNAPSHOT_VALIDATION_FAILED",
    "SNAPSHOT_BROWSER_EVIDENCE_UNRESOLVED": "SNAPSHOT_VALIDATION_FAILED",
}


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
                failed_reason = database.last_failure_reason
                if failed_reason is not None:
                    LOGGER.warning(
                        "slaif-diag: review-job phase=media-db-start "
                        "outcome=failed reason=%s",
                        failed_reason,
                    )
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


def _strict_manifest_identities(
    manifest_doc: dict[str, Any],
    expected_operations: frozenset[UUID],
    expected_pairs: set[tuple[UUID, UUID]],
) -> tuple[frozenset[UUID], set[tuple[UUID, UUID]]]:
    """Strict staged derivation of the manifest's approved identities.

    Fail-closed shape checks before any comparison: ``operation_ids``
    must be a list of unique canonical UUID strings and
    ``dependency_pairs`` a list of unique two-element UUID-string
    pairs; the derived sets must equal the previously verified
    (step-3) identities exactly.  Raises ``ValueError`` on any shape
    or identity disagreement - the caller maps that to the stable
    validation refusal.
    """
    operation_ids = manifest_doc.get("operation_ids")
    pairs = manifest_doc.get("dependency_pairs")
    if not isinstance(operation_ids, list) or not isinstance(pairs, list):
        raise ValueError("identity shape")
    operations: set[UUID] = set()
    for operation in operation_ids:
        if not isinstance(operation, str):
            raise ValueError("operation shape")
        try:
            parsed = UUID(operation)
        except ValueError:
            raise ValueError("operation uuid") from None
        if str(parsed) != operation:
            raise ValueError("operation canonical")
        if parsed in operations:
            raise ValueError("duplicate operation")
        operations.add(parsed)
    if frozenset(operations) != expected_operations:
        raise ValueError("operation identity")
    pair_set: set[tuple[UUID, UUID]] = set()
    for pair in pairs:
        if (
            not isinstance(pair, (list, tuple))
            or len(pair) != 2
            or not all(isinstance(endpoint, str) for endpoint in pair)
        ):
            raise ValueError("pair shape")
        try:
            parent = UUID(pair[0])
            child = UUID(pair[1])
        except (IndexError, ValueError):
            raise ValueError("pair uuid") from None
        if str(parent) != pair[0] or str(child) != pair[1]:
            raise ValueError("pair canonical")
        if (parent, child) in pair_set:
            raise ValueError("duplicate pair")
        pair_set.add((parent, child))
    if pair_set != expected_pairs:
        raise ValueError("pair identity")
    return frozenset(operations), pair_set


async def _claim_gated_state_change(
    pool: Any,
    *,
    job_id: UUID,
    workspace_id: UUID,
    site_id: UUID,
    claimant: str,
    attempt_count: int,
    claimed_payload: Any,
    workspace_from: str | tuple[str, ...] | None,
    workspace_target: str | None,
    job_failed_code: str | None,
) -> str:
    """One transaction: claim verification + recovery state changes.

    Locked reads in the promotion-transaction lock order - the
    workspace row FIRST, then the job row - verify that this attempt
    still owns the durable claim: the job is a CLAIMED ACCEPT job
    owned by exactly this claimant and attempt for this
    site/workspace, the workspace is bound to that site, and the job
    payload is TYPED-EXACTLY the
    claimed payload (the full decoded JSONB compared with explicit
    types: a numeric digest never equals its string form, a missing
    field never equals a present one, and a tampered field defers).
    Approval SHAPE validation (64-hex, UUIDs) stays with the caller
    - this gate proves only that the durable approval is unchanged.
    Only then are the requested writes made in the SAME transaction:
    the guarded workspace transition (from the locked state) and/or
    the job FAILED terminal through the definer mark.  Returns:
      applied   - owned the claim and every requested write landed;
      deferred  - the claim moved, the payload disagrees, or a
                 requested transition no longer matches: NO write;
      unknown   - the locked state was temporarily unreadable: the
                 transaction rolled back, NO write.
    In both non-applied cases the caller makes no state change and
    leaves recovery to the claim function's stale-claim handling, so
    a stale attempt can never re-queue or terminal-mark a moved
    claim and a successful terminal record is never touched.
    """
    if (workspace_from is None) != (workspace_target is None):
        raise ValueError("workspace transition requires both states")
    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                ws = await connection.fetchrow(
                    "SELECT status, site_id FROM control.workspace "
                    "WHERE id = $1 FOR UPDATE",
                    workspace_id,
                )
                if ws is None or str(ws["site_id"]) != str(site_id):
                    return "deferred"
                # The claimed payload is bound as JSONB and compared
                # with PostgreSQL's TYPE-SENSITIVE jsonb value
                # equality (a nested true never equals 1, a numeric
                # digest never equals its string form): a mismatched
                # row simply is not the claimed job; the job kind
                # must agree with the recovery binding (an unchanged
                # payload/claimant on a re-kinded row must never be
                # terminal-marked).
                job = await connection.fetchrow(
                    "SELECT status, job_kind, claimed_by, attempt_count, "
                    "workspace_id, site_id "
                    "FROM control.review_job "
                    "WHERE id = $1 "
                    "  AND payload IS NOT DISTINCT FROM $2::jsonb "
                    "FOR UPDATE",
                    job_id,
                    json.dumps(claimed_payload, sort_keys=True, separators=(",", ":")),
                )
                if job is None:
                    return "deferred"
                owned = (
                    str(job["status"]) == "CLAIMED"
                    and str(job["job_kind"]) == "ACCEPT"
                    and str(job["claimed_by"]) == claimant
                    and int(job["attempt_count"]) == attempt_count
                    and str(job["workspace_id"]) == str(workspace_id)
                    and str(job["site_id"]) == str(site_id)
                )
                if not owned:
                    return "deferred"
                if workspace_target is not None:
                    if isinstance(workspace_from, tuple):
                        executed = await connection.execute(
                            "UPDATE control.workspace SET status = $3 "
                            "WHERE id = $1 AND status = ANY($2::text[])",
                            workspace_id,
                            list(workspace_from),
                            workspace_target,
                        )
                    else:
                        executed = await connection.execute(
                            "UPDATE control.workspace SET status = $3 "
                            "WHERE id = $1 AND status = $2",
                            workspace_id,
                            workspace_from,
                            workspace_target,
                        )
                    if executed != "UPDATE 1":
                        # The locked row is not in the guarded from-
                        # state: a contradictory intermediate state.
                        # Make no write at all (nothing was written
                        # before this in the transaction).
                        return "deferred"
                if job_failed_code is not None:
                    await connection.fetchval(
                        "SELECT control.slaif_review_job_terminal($1, 'FAILED', $2)",
                        job_id,
                        job_failed_code,
                    )
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return "unknown"
    return "applied"


def _receipt_matches(receipt: Any, expected: dict[str, Any]) -> bool:
    """Exact promotion-receipt validation (c2).

    True only for the single-row projection matching EVERY approval
    fact and the retained promotion result: site/workspace/snapshot
    binding, both digests, manifest identity, base revision, the
    incremented result revision, committed count, actor, exact
    versions and the exact ordered applied operation IDs.  Anything
    else - absent (None), the ambiguous multiple-row marker, a
    malformed shape, or one mismatching field - is False: uncertain,
    never success.
    """
    if not isinstance(receipt, dict) or receipt.get("receipt_rows") != 1:
        return False
    if (
        str(receipt.get("site_id")) != str(expected["site_id"])
        or str(receipt.get("workspace_id")) != str(expected["workspace_id"])
        or str(receipt.get("snapshot_id")) != str(expected["snapshot_id"])
        or receipt.get("digest") != expected["digest"]
        or receipt.get("manifest_digest") != expected["manifest_digest"]
        or str(receipt.get("manifest_id")) != str(expected["manifest_id"])
        or receipt.get("base_site_revision") != expected["base_site_revision"]
        or receipt.get("new_canonical_revision") != expected["base_site_revision"] + 1
        or receipt.get("committed_operations") != expected["committed_operations"]
        or str(receipt.get("actor_user_account_id"))
        != str(expected["actor_user_account_id"])
        or receipt.get("applied_operation_ids") != expected["applied_operation_ids"]
    ):
        return False
    versions = _decode_jsonb(receipt.get("versions"))
    return isinstance(versions, dict) and versions == expected["versions"]


async def _reconcile_uncertain_outcome(
    pool: Any,
    *,
    job_id: UUID,
    workspace_id: UUID,
    site_id: UUID,
    claimant: str,
    attempt_count: int,
    claimed_payload: Any,
    expected_receipt: dict[str, Any],
) -> str:
    """Reconcile an uncertain reviewer-transaction outcome against the
    EXACT durable publication receipt (c2).

    The promotion transaction commits as one: the promotion receipt,
    the workspace ACCEPTED transition, the job SUCCEEDED terminal and
    the outbox row.  A driver or interface failure inside the reviewer
    scope or its cleanup does not by itself prove rollback - the
    failure can occur AFTER the native commit - nor success.  The
    receipt read is the narrow owner-definer projection (the worker
    holds no SELECT on audit.promotion) and distinguishes absent /
    exactly-one / ambiguous-multiple.  Locked reads use the
    workspace-then-job order.  The locked job read additionally binds
    the EXACT claimed payload (type-sensitive jsonb equality, as the
    claim gate), and the durable outbox row for this publication is
    checked for existence/absence consistency (072 grants the worker
    SELECT on control.cache_outbox; 074 consumes rows by UPDATE, so a
    consumed row still counts as present).  Returns:
      committed   - the job is SUCCEEDED, the workspace ACCEPTED, the
                    receipt exists exactly once matching every
                    approval fact, the exact claim payload is intact,
                    and the durable outbox holds exactly the one
                    EXACT row for this publication (type-sensitive
                    payload equality, and NO other WORKSPACE_ACCEPTED
                    row for the site/workspace): recover success,
                    never re-run;
      rolled_back - NO receipt exists at all, NO WORKSPACE_ACCEPTED
                    outbox row exists for the site/workspace, the
                    workspace is still in
                    the promotion pipeline, and this attempt still
                    verifiably owns the EXACT claimed job: safe to
                    re-queue under budget;
      unknown     - everything else: unreadable, a payload that no
                    longer matches the claim, a SUCCEEDED job without
                    the exact receipt, an ambiguous receipt, a
                    mismatching or duplicate outbox fact, or ANY
                    receipt on a nonterminal claim: a contradictory
                    publication state that must fail closed and
                    authorize NO
                    re-queue): make NO state change and leave the job
                    to the claim function's stale-claim handling.
    """
    try:
        async with pool.acquire() as connection:
            async with connection.transaction():
                # Two locked reads, one row each: the workspace row
                # FIRST, then the job row - the planner is never given
                # a lock-order choice (promotion-TX/enqueue order).
                ws = await connection.fetchrow(
                    "SELECT status, site_id FROM control.workspace "
                    "WHERE id = $1 FOR UPDATE",
                    workspace_id,
                )
                if ws is None or str(ws["site_id"]) != str(site_id):
                    return "unknown"
                # The EXACT claimed payload is part of the claim
                # identity (type-sensitive jsonb equality): a mutated
                # or re-kinded row is not this claim's job (the job
                # kind must agree with the recovery binding).
                job = await connection.fetchrow(
                    "SELECT status, job_kind, claimed_by, attempt_count, "
                    "workspace_id, site_id "
                    "FROM control.review_job "
                    "WHERE id = $1 "
                    "  AND payload IS NOT DISTINCT FROM $2::jsonb "
                    "FOR UPDATE",
                    job_id,
                    json.dumps(claimed_payload, sort_keys=True, separators=(",", ":")),
                )
                if (
                    job is None
                    or str(job["job_kind"]) != "ACCEPT"
                    or str(job["workspace_id"]) != str(workspace_id)
                    or str(job["site_id"]) != str(site_id)
                ):
                    return "unknown"
                receipt = await connection.fetchval(
                    "SELECT control.slaif_review_promotion_receipt_read($1)",
                    job_id,
                )
                if isinstance(receipt, (bytes, bytearray, str)):
                    receipt = _decode_jsonb(receipt)
                # Durable outbox consistency for THIS publication:
                # the promotion transaction inserts exactly one
                # WORKSPACE_ACCEPTED row whose payload is the exact
                # retained result (snapshot, digest, base/incremented
                # revision, media manifest).  ACCEPTED is terminal,
                # so a workspace can re-freeze before first
                # acceptance but can never publish a second snapshot
                # afterward: ANY WORKSPACE_ACCEPTED row bound to this
                # site/workspace (right snapshot or not, well-formed
                # or not) is part of the publication history, and
                # only the single EXACT row (type-sensitive jsonb
                # equality - a row with the right snapshot id but a
                # wrong digest/revision/media projection, a wrong-
                # snapshot row, or a duplicate) can confirm success.
                # A proven rollback requires NO row at all (074
                # consumes rows by UPDATE, so a consumed row still
                # counts as present).  Missing vs mismatching vs
                # duplicate facts are all distinguished: anything
                # other than the single exact row (or, for a proven
                # absence, nothing) is a contradictory state - never
                # a rollback proof and never a success proof.
                expected_outbox_payload = json.dumps(
                    {
                        "snapshot_id": str(expected_receipt["snapshot_id"]),
                        "digest": expected_receipt["digest"],
                        "base_site_revision": expected_receipt["base_site_revision"],
                        "new_canonical_revision": (
                            expected_receipt["base_site_revision"] + 1
                        ),
                        "media_manifest": expected_receipt["media_manifest"],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                outbox_stats = await connection.fetchrow(
                    "SELECT count(*) AS total, "
                    "  count(*) FILTER (WHERE payload IS NOT DISTINCT FROM $3::jsonb) "
                    "  AS exact "
                    "FROM control.cache_outbox "
                    "WHERE site_id = $1 AND workspace_id = $2 "
                    "  AND event_kind = 'WORKSPACE_ACCEPTED'",
                    site_id,
                    workspace_id,
                    expected_outbox_payload,
                )
                outbox_total = int(outbox_stats["total"])
                outbox_exact = int(outbox_stats["exact"])
                workspace_status = str(ws["status"])
                job_status = str(job["status"])
                if job_status == "SUCCEEDED":
                    if (
                        workspace_status == "ACCEPTED"
                        and _receipt_matches(receipt, expected_receipt)
                        and outbox_exact == 1
                        and outbox_total == 1
                    ):
                        return "committed"
                    return "unknown"
                if job_status == "FAILED":
                    return "unknown"
                if receipt is not None:
                    # ANY non-NULL receipt value (the single-row
                    # projection, the ambiguous multiple-row marker,
                    # or any unexpected shape) on a nonterminal claim
                    # is a contradictory durable state: fail closed -
                    # no re-queue, no terminal write, no rollback
                    # assumption.
                    return "unknown"
                if outbox_total != 0:
                    # ANY WORKSPACE_ACCEPTED row bound to this
                    # site/workspace (the exact one, a wrong-snapshot
                    # one, a mismatching one, or a duplicate) without
                    # the exact receipt on a nonterminal claim is a
                    # contradictory publication history: fail closed.
                    return "unknown"
                if (
                    workspace_status in ("PROMOTING", "ACCEPT_QUEUED")
                    and job_status == "CLAIMED"
                    and str(job["claimed_by"]) == claimant
                    and int(job["attempt_count"]) == attempt_count
                ):
                    return "rolled_back"
                return "unknown"
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return "unknown"


_TRANSPORT_REVIEWER_ERRORS: tuple[type[BaseException], ...] = (
    asyncpg.PostgresConnectionError,
    asyncpg.QueryCanceledError,
    TimeoutError,
    OSError,
)


# Transient SQL faults that are safe to retry (bounded by the attempt
# budget): the lock timeout our own SET LOCAL lock_timeout raises
# (55P03), a detected deadlock (40P01), and a serialization failure
# (40001) - PostgreSQL's retry-eligible class 40 faults.  Every other
# server-declared fault is deterministic: retrying re-fires the same fault.
_TRANSIENT_REVIEWER_SQL: tuple[type[asyncpg.PostgresError], ...] = (
    asyncpg.LockNotAvailableError,
    asyncpg.DeadlockDetectedError,
    asyncpg.SerializationError,
)


def _error_chain_has_transport(error: BaseException) -> bool:
    """True when the error or its implicit/explicit chain carries a
    transport-grade fault (a lost backend, a native cancellation, a
    timeout, an OS fault).

    The SDK's post-failure rollback can RAISE OVER the body's primary
    error; the driver links the two in the exception chain, so the
    transport class survives even when the observed exception is the
    rollback's client-mechanism error.
    """
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, _TRANSPORT_REVIEWER_ERRORS):
            return True
        current = current.__context__ or current.__cause__
    return False


def _reviewer_failure_class(
    error: BaseException, body_completed: bool
) -> Literal["uncertain", "retry", "programming"]:
    """Classify a reviewer-scope failure (c2) BEFORE any recovery
    mutation.

    The SDK commits ONLY when the body returns cleanly - the commit
    runs at scope exit and a body exception rolls the transaction
    back - so the commit state is provable from the exception point:

      uncertain   - the body COMPLETED and the failure arose at the
                    commit/cleanup boundary (a commit-statement
                    transport loss, or the post-commit scope/pool
                    channel): the native commit MAY have landed, so
                    the outcome is reconciled against the exact
                    durable receipt - success ONLY on that
                    fingerprint, never assumed;
      retry       - the body raised a transport/transport failure
                    (a lost backend, a native cancellation, a
                    timeout), possibly masked by the SDK's
                    post-failure rollback error: the transaction
                    cannot have committed, and the failure is
                    transport-grade, so the ordinary requeue under
                    budget applies with no receipt read (the commit
                    is proven absent, not merely unknown);
      programming - a deterministic SQL/programming fault (e.g.
                    42P01, 42501, P0001) or a generic
                    client-mechanism InterfaceError raised inside
                    the body: the transaction is aborted and can
                    NEVER commit; retrying can only re-fire the same
                    fault, so this must NOT enter the ordinary
                    retry/recovery mutation.

    A DETERMINISTIC server-declared fault observed with the body
    COMPLETED (e.g. a deferred integrity rejection at COMMIT, or
    the native-SQL cleanup after a successful native commit) also
    returns ``programming``: the handler then settles the possible
    publication durably FIRST (success on the exact receipt
    fingerprint, deferral on contradiction) and terminals ONLY on a
    proven durable absence - never assuming the exit SQLSTATE
    originated at COMMIT.
    """
    if isinstance(error, _TRANSPORT_REVIEWER_ERRORS):
        # Transport-grade: at the commit/cleanup boundary the commit
        # MAY have landed (uncertain - the receipt decides); mid-body
        # the SDK rolled the transaction back, so the commit is
        # proven absent (ordinary requeue, no receipt read).
        return "uncertain" if body_completed else "retry"
    if isinstance(error, asyncpg.PostgresError):
        if isinstance(error, _TRANSIENT_REVIEWER_SQL):
            # A transient SQL fault: mid-body the transaction aborted
            # (retry under budget); at the boundary the commit state
            # is reconciled and a proven rollback keeps the bounded
            # retry.
            return "uncertain" if body_completed else "retry"
        # A server-declared DETERMINISTIC fault (e.g. 42P01, 42501,
        # P0001, a deferred integrity rejection at COMMIT, or the
        # SDK's post-commit cleanup SQL after a SUCCESSFUL native
        # commit): mid-body the transaction is aborted and can never
        # commit; at the boundary the fault is NOT by itself proof
        # that the commit was rejected (the post-commit cleanup can
        # raise after the commit landed - the real boundary negative
        # proves it), so the handler settles the possible
        # publication durably first and terminals ONLY on a proven
        # durable absence.  Either way: never an ordinary retry.
        return "programming"
    # InterfaceError or other client-mechanism fault: a completed
    # body means the post-commit scope/pool channel (the commit MAY
    # have landed - the receipt decides); a body-stage fault is a
    # transport-grade loss only when the exception chain keeps one,
    # otherwise it is a programming fault inside the body.
    if body_completed:
        return "uncertain"
    return "retry" if _error_chain_has_transport(error) else "programming"


async def _programming_terminal(
    pool: Any,
    *,
    job_id: UUID,
    workspace_id: UUID,
    site_id: UUID,
    claimant: str,
    attempt_count: int,
    claimed_payload: Any,
) -> JobResult:
    """Terminal the claim for a deterministic reviewer-TX fault (c2).

    The publication is provenly absent (the SDK never commits on a
    raised body), so the terminal record is written through the SAME
    locked claim-gated transaction as every other recovery: the
    workspace moves PROMOTING -> REVIEW (human attention) and the job
    becomes terminally FAILED in one atomic state change.  A moved or
    mutated claim defers with NO write and leaves recovery to the
    claim function's stale-claim handling.
    """
    applied = await _claim_gated_state_change(
        pool,
        job_id=job_id,
        workspace_id=workspace_id,
        site_id=site_id,
        claimant=claimant,
        attempt_count=attempt_count,
        claimed_payload=claimed_payload,
        workspace_from="PROMOTING",
        workspace_target="REVIEW",
        job_failed_code="REVIEWER_TX_PROGRAMMING_FAILURE",
    )
    if applied != "applied":
        LOGGER.warning(
            "slaif-diag: review-job phase=programming-terminal outcome=%s job=%s",
            applied,
            job_id,
        )
        return JobResult("ROLLED_BACK")
    return JobResult("FAILED", "REVIEWER_TX_PROGRAMMING_FAILURE")


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
    except (asyncpg.PostgresError, TimeoutError, OSError) as error:
        log_bounded_db_failure("pipeline-read", error)
        return None, None
    if row is None:
        return None, "SITE_MISSING"
    return str(row["workspace_status"]), str(row["site_status"])


def _decode_jsonb(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


async def _verify_snapshot(
    pool: Any,
    *,
    workspace_id: UUID,
    site_id: UUID,
    snapshot_id: UUID,
    claimant: str,
    lock_timeout_seconds: float,
    snapshot_digest: str,
    manifest_digest: str,
) -> dict[str, Any]:
    """Locked preflight + re-materialization re-validation (step 3).

    Under the workspace-then-site lock order the freeze worker uses:
    stored binding check, trusted stored ``base_site_revision`` vs the
    locked current canonical revision (``SITE_REVISION_CHANGED`` drift
    before any replay), then the re-materialization + digest/versions
    re-validation. The final revision gate after re-validation remains
    as defense in depth.

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
                    "SELECT workspace_id, site_id, digest, versions, "
                    "normalized_state, media_references "
                    "FROM control.review_snapshot WHERE id = $1",
                    snapshot_id,
                )
                if stored is None:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # 083/4 preflight (before replay normalization/digest):
                # the stored snapshot must be bound to this exact
                # workspace + site, and its trusted stored revision must
                # equal the locked current canonical revision. A
                # post-freeze publication is drift, reported as the
                # stable SITE_REVISION_CHANGED, never obscured by a
                # re-materialized digest mismatch.
                if str(stored["workspace_id"]) != str(workspace_id) or str(
                    stored["site_id"]
                ) != str(site_id):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # 083/12-b: the durable human approval must name this
                # snapshot's EXACT stored domain digest.  The passed
                # approval digest is compared explicitly - it is never
                # silently filled from (or re-derived against) current
                # state.
                if snapshot_digest != str(stored["digest"]):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # 083/12: the companion manifest must exist for this
                # snapshot (a historical companion-less snapshot can
                # never be approved at or after 079) and must carry
                # exactly the approved digests and the exact
                # site/workspace binding.
                manifest_doc = await connection.fetchval(
                    "SELECT control.slaif_review_operation_manifest_read($1)",
                    snapshot_id,
                )
                try:
                    manifest_doc = _decode_jsonb(manifest_doc)
                except ValueError:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
                if not isinstance(manifest_doc, dict):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                if (
                    manifest_doc.get("schema_version")
                    != operation_manifest.MANIFEST_SCHEMA_VERSION
                    or manifest_doc.get("manifest_digest") != manifest_digest
                    or manifest_doc.get("snapshot_digest") != str(stored["digest"])
                    or manifest_doc.get("site_id") != str(site_id)
                    or manifest_doc.get("workspace_id") != str(workspace_id)
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                approved_operation_ids = manifest_doc.get("operation_ids")
                approved_pairs = manifest_doc.get("dependency_pairs")
                if not isinstance(approved_operation_ids, list) or not isinstance(
                    approved_pairs, list
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # 083/12-b: malformed or filtered-away dependency
                # entries are refused, never silently skipped: every
                # entry must be exactly two UUID strings.
                if any(
                    not isinstance(pair, (list, tuple))
                    or len(pair) != 2
                    or not all(isinstance(endpoint, str) for endpoint in pair)
                    for pair in approved_pairs
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                try:
                    approved_operations = [
                        UUID(str(operation)) for operation in approved_operation_ids
                    ]
                    approved_pair_set = {
                        (UUID(str(pair[0])), UUID(str(pair[1])))
                        for pair in approved_pairs
                    }
                    if len(approved_operations) != len(set(approved_operations)):
                        raise ValueError("duplicate operation")
                except ValueError:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
                preflight_normalized = stored["normalized_state"]
                if isinstance(preflight_normalized, (bytes, bytearray)):
                    preflight_normalized = preflight_normalized.decode("utf-8")
                if isinstance(preflight_normalized, str):
                    try:
                        preflight_normalized = json.loads(preflight_normalized)
                    except ValueError:
                        raise AcceptJobError(
                            "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                        ) from None
                if not isinstance(preflight_normalized, dict):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                try:
                    preflight_revision = int(preflight_normalized["base_site_revision"])
                except (KeyError, TypeError, ValueError):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
                if int(base_site_revision) != preflight_revision:
                    raise AcceptJobError("SITE_REVISION_CHANGED", kind="drift")
                doc = await connection.fetchval(
                    "SELECT control.slaif_review_workspace_state($1)",
                    workspace_id,
                )
    except (asyncpg.PostgresError, TimeoutError, OSError) as error:
        message = getattr(error, "message", None) or str(error)
        if "REVIEW_WORKSPACE_NOT_FOUND" in message:
            raise AcceptJobError("STATE_DRIFT", kind="state") from None
        if "REVIEW_SITE_NOT_ACTIVE" in message:
            raise AcceptJobError("STATE_DRIFT", kind="state") from None
        # Stable semantic refusal (version compatibility or
        # validation/budget): the locked data will not change on
        # retry.  Drift precedence is structural: the locked
        # base_site_revision gate above runs before the
        # re-materialization that raises these.
        stable_code = _STABLE_MATERIALIZER_FAILURES.get(message.strip())
        if stable_code is None:
            stable_code = next(
                (
                    code
                    for marker, code in _STABLE_MATERIALIZER_FAILURES.items()
                    if marker in message
                ),
                None,
            )
        if stable_code is not None:
            raise AcceptJobError(stable_code, kind="validation") from None
        log_bounded_db_failure("verify-snapshot", error)
        raise
    # asyncpg 0.31.0 returns jsonb as str: decode the materialized doc
    # here so the replay normalization below sees the media dict (the
    # same str behavior the other jsonb reads guard against).  The
    # shared exact decoder keeps every raw fractional digit/scale so
    # the shared builder re-materializes the exact capture (a plain
    # json.loads would collapse e.g. 1.50 -> 1.5 and break the
    # digest comparison).
    if isinstance(doc, (bytes, bytearray, str)):
        try:
            doc_text = (
                doc.decode("utf-8") if isinstance(doc, (bytes, bytearray)) else doc
            )
            doc = parse_snapshot_text(doc_text)
        except ValueError:
            raise AcceptJobError(
                "SNAPSHOT_VALIDATION_FAILED", kind="validation"
            ) from None
    media_references = stored["media_references"]
    if isinstance(media_references, (bytes, bytearray, str)):
        try:
            media_text = (
                media_references.decode("utf-8")
                if isinstance(media_references, (bytes, bytearray))
                else media_references
            )
            media_references = parse_snapshot_text(media_text)
        except ValueError:
            raise AcceptJobError(
                "SNAPSHOT_VALIDATION_FAILED", kind="validation"
            ) from None
    # Crash-replay idempotency (R3.10, retained legacy compatibility):
    # a job interrupted BETWEEN the pre-077 pre-transaction mark and the
    # promotion transaction persisted a private -> public flip on the
    # canonical base that the new in-transaction mark never creates.
    # For such retained pre-077 state a re-claim observes exactly that
    # flip, so the re-materialized doc is normalized back to the
    # freeze-time status for the snapshot-referenced media set before
    # the digest comparison and the replay re-validates and commits
    # exactly once; media outside the set keep their observed status,
    # and every other drift still fails closed.
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
    # The 076 v2 capture additionally retains the full media inventory
    # (metadata only, no bytes) carrying public_status/published_at/
    # updated_at.  Finalization mutates exactly those fields on the
    # referenced rows, so the crash-replay inverse restores the exact
    # freeze-time values (from the stored capture) for the flipped set
    # only; every other media row change still fails the digest
    # comparison below.
    if (
        isinstance(doc, dict)
        and isinstance(doc.get("media_inventory"), list)
        and isinstance(preflight_normalized, dict)
    ):
        frozen_inventory: dict[str, Any] = {}
        stored_inventory = preflight_normalized.get("media_inventory")
        if isinstance(stored_inventory, list):
            for stored_entry in stored_inventory:
                if isinstance(stored_entry, dict) and isinstance(
                    stored_entry.get("id"), str
                ):
                    frozen_inventory[str(stored_entry["id"])] = stored_entry
        for inventory_entry in doc["media_inventory"]:
            if not isinstance(inventory_entry, dict):
                continue
            inventory_id = str(inventory_entry.get("id"))
            if (
                frozen_status_by_id.get(inventory_id) == "private"
                and inventory_entry.get("public_status") == "public"
                and inventory_id in frozen_inventory
            ):
                stored_entry = frozen_inventory[inventory_id]
                inventory_entry["public_status"] = stored_entry.get("public_status")
                inventory_entry["published_at"] = stored_entry.get("published_at")
                inventory_entry["updated_at"] = stored_entry.get("updated_at")
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
        "manifest_id": str(manifest_doc["manifest_id"]),
        "manifest_digest": manifest_digest,
        "approved_operations": frozenset(approved_operations),
        "approved_pairs": approved_pair_set,
    }


async def _malformed_approval_refusal(
    pool: Any,
    *,
    job_id: UUID,
    workspace_id: UUID,
    site_id: UUID,
    claimant: str,
    attempt_count: int,
    claimed_payload: Any,
) -> JobResult:
    """A malformed durable approval is a validation refusal, not a
    transient: in ONE locked claim-gated transaction the workspace
    returns to the human-actionable REVIEW (from the promotion
    pipeline states) and the job terminal-marks, never left stuck in
    ACCEPT_QUEUED.  The raw (possibly malformed) claimed payload is
    the typed claim-ownership proof against the locked job row - a
    numeric or object digest still matches exactly the unchanged row
    it came from, so the refusal terminals its own claim.  A lost or
    unverifiable claim makes no write at all (the claim function's
    stale-claim recovery owns the job) and the handler reports
    ROLLED_BACK.
    """
    applied = await _claim_gated_state_change(
        pool,
        job_id=job_id,
        workspace_id=workspace_id,
        site_id=site_id,
        claimant=claimant,
        attempt_count=attempt_count,
        claimed_payload=claimed_payload,
        workspace_from=("ACCEPT_QUEUED", "PROMOTING"),
        workspace_target="REVIEW",
        job_failed_code="SNAPSHOT_VALIDATION_FAILED",
    )
    if applied != "applied":
        LOGGER.warning(
            "slaif-diag: review-job phase=malformed-approval outcome=no-action job=%s",
            job_id,
        )
        return JobResult("ROLLED_BACK")
    return JobResult("FAILED", "SNAPSHOT_VALIDATION_FAILED")


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
        return await _malformed_approval_refusal(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
        )
    try:
        snapshot_id = _payload_uuid(payload, "snapshot_id")
        actor_user_account_id = _payload_uuid(payload, "actor_user_account_id")
        # 083/12: the durable job payload carries the exact approval -
        # the domain snapshot digest PLUS the companion manifest
        # digest (both 64-hex).  A pre-079 payload (digest-less
        # approval) fails closed: it can never name the companion.
        # 083/12-c: both digests must be JSON STRINGS in the durable
        # payload.  A str() coercion would let a 64-digit JSON NUMBER
        # through the hex shape check (every decimal digit is a valid
        # hex character) and into the typed claim binding, where it
        # can no longer terminally refuse its own unchanged numeric
        # claim.
        snapshot_digest = payload["snapshot_digest"]
        manifest_digest = payload["manifest_digest"]
        if not isinstance(snapshot_digest, str) or not isinstance(manifest_digest, str):
            raise ValueError("digest type")
        if not _DIGEST_64_RE.fullmatch(snapshot_digest) or not _DIGEST_64_RE.fullmatch(
            manifest_digest
        ):
            raise ValueError("digest shape")
    except (KeyError, TypeError, ValueError):
        # 083/12-b: a malformed durable approval (missing/JSON-null/
        # non-64-hex digest) is a validation refusal, not a transient:
        # the workspace returns to REVIEW before the terminal mark,
        # never left stuck in ACCEPT_QUEUED.
        # 083/12-c: the claimed payload (raw, possibly malformed) is
        # the typed claim-ownership proof against the locked job row.
        return await _malformed_approval_refusal(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
        )

    def _at_budget() -> bool:
        return attempt_count >= max_attempts

    async def _retryable_or_budget(reason: str) -> JobResult:
        """Retryable failure: re-queue under budget, terminate at budget.

        The recovery state change (workspace transition and, at
        budget, the job terminal) is made in ONE locked claim-gated
        transaction; a lost or unverifiable claim leaves the durable
        state untouched for the claim function's stale-claim recovery
        (no state write, no terminal claim).
        """
        at_budget = _at_budget()
        applied = await _claim_gated_state_change(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            workspace_from="PROMOTING",
            workspace_target="REVIEW" if at_budget else "ACCEPT_QUEUED",
            job_failed_code="REVIEW_JOB_STALE_AT_BUDGET" if at_budget else None,
        )
        if applied != "applied":
            LOGGER.warning(
                "slaif-diag: review-job phase=retry outcome=no-action "
                "reason=%s outcome=%s attempt=%s job=%s",
                reason,
                applied,
                attempt_count,
                job_id,
            )
            return JobResult("ROLLED_BACK")
        LOGGER.warning(
            "slaif-diag: review-job phase=retry outcome=%s reason=%s "
            "attempt=%s max_attempts=%s",
            "budget" if at_budget else "requeue",
            reason,
            attempt_count,
            max_attempts,
        )
        if at_budget:
            return JobResult("FAILED", "REVIEW_JOB_STALE_AT_BUDGET")
        # No terminal: the job stays CLAIMED (the gated transition
        # only moved the workspace) and the claim function's
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
        transition_from = (
            workspace_status
            if workspace_status in ("ACCEPT_QUEUED", "PROMOTING")
            else None
        )
        applied = await _claim_gated_state_change(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            workspace_from=transition_from,
            workspace_target="REVIEW" if transition_from is not None else None,
            job_failed_code="STATE_DRIFT",
        )
        if applied != "applied":
            return JobResult("ROLLED_BACK")
        return JobResult("FAILED", "STATE_DRIFT")

    # Step 2: fresh claims mark PROMOTING (replays already are).
    # 083/12-c: the initial transition is claim-gated in the SAME
    # locked transaction as the ownership proof (job kind + claimant
    # + attempt + typed-exact payload): a stale invocation against a
    # moved claim must never move the new owner's workspace before
    # the reviewer refuses it.
    if workspace_status == "ACCEPT_QUEUED":
        applied = await _claim_gated_state_change(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            workspace_from="ACCEPT_QUEUED",
            workspace_target="PROMOTING",
            job_failed_code=None,
        )
        if applied == "unknown":
            return JobResult("ROLLED_BACK")
        if applied != "applied":
            # Either the claim moved (the new owner's state stays
            # untouched) or the locked workspace left the guarded
            # state while this attempt still owns the claim (drift):
            # the second locked check distinguishes the two - the
            # terminal mark lands only while the exact claim is
            # still owned.
            drift = await _claim_gated_state_change(
                pool,
                job_id=job_id,
                workspace_id=workspace_id,
                site_id=site_id,
                claimant=claimant,
                attempt_count=attempt_count,
                claimed_payload=payload,
                workspace_from=None,
                workspace_target=None,
                job_failed_code="STATE_DRIFT",
            )
            if drift == "applied":
                return JobResult("FAILED", "STATE_DRIFT")
            return JobResult("ROLLED_BACK")

    # Step 3: locked verification (drift gate + re-validation).
    try:
        facts = await _verify_snapshot(
            pool,
            workspace_id=workspace_id,
            site_id=site_id,
            snapshot_id=snapshot_id,
            claimant=claimant,
            lock_timeout_seconds=settings.drain_lock_timeout_seconds,
            snapshot_digest=snapshot_digest,
            manifest_digest=manifest_digest,
        )
    except AcceptJobError as error:
        applied = await _claim_gated_state_change(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            workspace_from="PROMOTING",
            workspace_target="REVIEW"
            if error.kind in ("drift", "validation")
            else None,
            job_failed_code=error.code,
        )
        if applied != "applied":
            return JobResult("ROLLED_BACK")
        return JobResult("FAILED", error.code)
    except (asyncpg.PostgresError, TimeoutError, OSError):
        return JobResult("ROLLED_BACK")

    # Step 4: media finalization FIRST (before the commit).
    try:
        manifest = await boundary.finalize(site_id, workspace_id, facts["media_ids"])
    except FinalizationError as error:
        if error.reason in _RETRYABLE_FINALIZATION_REASONS:
            LOGGER.warning(
                "slaif-diag: review-job phase=finalization outcome=failed "
                "job=%s reason=%s",
                job_id,
                error.reason,
            )
            return await _retryable_or_budget(error.reason)
        applied = await _claim_gated_state_change(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            workspace_from="PROMOTING",
            workspace_target="REVIEW",
            job_failed_code="SNAPSHOT_VALIDATION_FAILED",
        )
        if applied != "applied":
            return JobResult("ROLLED_BACK")
        return JobResult("FAILED", "SNAPSHOT_VALIDATION_FAILED")
    except MediaDatabaseConfigurationError:
        LOGGER.warning(
            "slaif-diag: review-job phase=media-config outcome=failed "
            "reason=configuration_invalid"
        )
        return await _retryable_or_budget("media_config_invalid")
    except (asyncpg.PostgresError, TimeoutError, OSError) as error:
        # Bounded diagnostic: class + SQLSTATE only, never the message.
        log_bounded_db_failure("media-finalize", error)
        return JobResult("ROLLED_BACK")
    facts["media_manifest"] = manifest.to_list()

    # The exact durable publication receipt the promotion transaction
    # WILL commit for this job: the full approval tuple (site,
    # workspace, snapshot, actor, both digests, manifest identity,
    # base revision) plus the retained result (incremented revision,
    # committed count, exact versions, exact ordered applied IDs).
    # Uncertain-outcome reconciliation accepts success ONLY on this
    # fingerprint (read through the narrow worker-only definer).
    expected_receipt: dict[str, Any] = {
        "site_id": site_id,
        "workspace_id": workspace_id,
        "snapshot_id": facts["snapshot_id"],
        "digest": snapshot_digest,
        "manifest_digest": manifest_digest,
        "manifest_id": facts["manifest_id"],
        "base_site_revision": facts["base_site_revision"],
        "committed_operations": len(facts["approved_operations"]),
        "actor_user_account_id": actor_user_account_id,
        "versions": facts["versions"],
        "applied_operation_ids": [
            str(operation) for operation in sorted(facts["approved_operations"])
        ],
        # The exact media manifest the promotion transaction WILL
        # journal into the durable outbox row (the outbox payload is
        # part of the recovery fingerprint: the receipt alone cannot
        # distinguish a media projection).
        "media_manifest": facts["media_manifest"],
    }

    async def _settle_uncertain(
        error: BaseException, absence_policy: Literal["retryable", "terminal"]
    ) -> JobResult:
        """Settle an uncertain commit-boundary outcome (c2).

        The native commit MAY have landed, so the durable publication
        state decides: success ONLY on the exact terminal receipt
        fingerprint (exact receipt + workspace + job + outbox); a
        PROVEN durable absence (no receipt at all, no outbox row for
        this publication, the pipeline still open, this attempt still
        owning the exact claim) then follows the absence policy -
        ``retryable`` keeps the ordinary requeue under budget for a
        transport/transient fault, while ``terminal`` applies to a
        deterministic server-declared fault (e.g. a deferred
        integrity rejection at COMMIT): the absence is proven, and
        retrying can only re-fire the same fault; anything
        contradictory makes NO state change and defers to the claim
        function's stale-claim recovery (the heartbeat stopped with
        this attempt, so there is no dead end).
        """
        outcome = await _reconcile_uncertain_outcome(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            expected_receipt=expected_receipt,
        )
        if outcome == "committed":
            LOGGER.warning(
                "slaif-diag: review-job phase=reviewer-step step=%s "
                "outcome=committed-durable job=%s",
                reviewer_step,
                job_id,
            )
            return JobResult("SUCCEEDED")
        if outcome == "unknown":
            # Not a proven rollback: the commit state is uncertain
            # and NO state write was made.  The explicit nonterminal
            # DEFERRED result status (no public job state, no
            # durable transition - the job simply stays CLAIMED for
            # stale-claim recovery) keeps the structured finish log
            # from labelling an unproven transaction outcome as a
            # rollback; the UNCERTAIN_OUTCOME diagnostic carries the
            # uncertainty.
            LOGGER.warning(
                "slaif-diag: review-job phase=reviewer-step step=%s "
                "outcome=uncertain-deferred job=%s",
                reviewer_step,
                job_id,
            )
            return JobResult("DEFERRED", "UNCERTAIN_OUTCOME")
        if absence_policy == "terminal":
            LOGGER.warning(
                "slaif-diag: review-job phase=reviewer-step step=%s "
                "outcome=programming-terminal-after-settlement job=%s",
                reviewer_step,
                job_id,
            )
            return await _programming_terminal(
                pool,
                job_id=job_id,
                workspace_id=workspace_id,
                site_id=site_id,
                claimant=claimant,
                attempt_count=attempt_count,
                claimed_payload=payload,
            )
        return await _retryable_or_budget(
            "postgres_transient"
            if isinstance(error, asyncpg.PostgresError)
            else "io_transient"
        )

    # Step 5: the promotion transaction (one reviewer scope, all-or-nothing).
    reviewer_step = "entry"
    # The SDK commits ONLY when the body returns cleanly (the commit
    # runs at scope exit, after a clean body).  This flag separates
    # the commit/cleanup boundary (commit state genuinely uncertain)
    # from body-stage faults (the SDK rolls back; a commit is
    # impossible), which drives the c2 failure classification.
    reviewer_body_completed = False
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
                # 083/12-c c1: the active-site preflight can become
                # stale before this transaction (a site archive holds
                # the row lock but does NOT advance the revision), so
                # the locked reads recheck the full binding, not only
                # the revision: the workspace row must still bind
                # exactly this site and be PROMOTING, and the site row
                # must still be ACTIVE at the approved base revision.
                ws_live = await reviewer.native.fetchrow(
                    "SELECT status, site_id FROM control.workspace "
                    "WHERE id = $1 FOR UPDATE",
                    workspace_id,
                )
                if (
                    ws_live is None
                    or str(ws_live["status"]) != "PROMOTING"
                    or str(ws_live["site_id"]) != str(site_id)
                ):
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                site_live = await reviewer.native.fetchrow(
                    "SELECT canonical_revision, status FROM control.site "
                    "WHERE id = $1 FOR UPDATE",
                    site_id,
                )
                if (
                    site_live is None
                    or int(site_live["canonical_revision"])
                    != facts["base_site_revision"]
                ):
                    raise AcceptJobError("SITE_REVISION_CHANGED", kind="drift")
                if str(site_live["status"]) != "ACTIVE":
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                # 083/12-c: the durable claim re-verified under this
                # transaction's own locks BEFORE any publication step:
                # the job must still be a CLAIMED ACCEPT job owned by
                # exactly this attempt (claimant, attempt count,
                # site/workspace binding) and its payload - decoded
                # with explicit JSONB types, never text-coerced -
                # must still carry exactly this snapshot, the actor,
                # the exact dual approval digest, and the site bound
                # in the JSON approval, all as typed strings (a
                # numeric or object digest is NOT its string form and
                # cannot publish).  A moved, mutated, or re-kinded
                # claim aborts the transaction before ANY effect
                # (kind "state": no workspace transition, no terminal
                # write by a stale attempt - the gated recovery
                # defers to the new owner).
                reviewer_step = "claim"
                job_live = await reviewer.native.fetchrow(
                    "SELECT status, job_kind, claimed_by, attempt_count, "
                    "workspace_id, site_id, payload "
                    "FROM control.review_job WHERE id = $1 FOR UPDATE",
                    job_id,
                )
                job_payload = (
                    _decode_jsonb(job_live["payload"]) if job_live is not None else None
                )
                if (
                    job_live is None
                    or str(job_live["status"]) != "CLAIMED"
                    or str(job_live["job_kind"]) != "ACCEPT"
                    or str(job_live["claimed_by"]) != claimant
                    or int(job_live["attempt_count"]) != attempt_count
                    or str(job_live["workspace_id"]) != str(workspace_id)
                    or str(job_live["site_id"]) != str(site_id)
                    or not isinstance(job_payload, dict)
                    or job_payload.get("snapshot_id") != str(facts["snapshot_id"])
                    or job_payload.get("site_id") != str(site_id)
                    or job_payload.get("actor_user_account_id")
                    != str(actor_user_account_id)
                    or job_payload.get("snapshot_digest") != snapshot_digest
                    or job_payload.get("manifest_digest") != manifest_digest
                ):
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                # 083/12-c c2: pre-publication exact receipt check.
                # A durable promotion receipt already exists for this
                # job while the job is still CLAIMED: a contradictory
                # publication state (a previous attempt's commit can
                # only leave the job SUCCEEDED in the SAME
                # transaction, never CLAIMED).  This attempt must
                # NEVER publish the same job again (double
                # publication); the typed refusal defers to the gated
                # terminal, which ends the requeue loop when this
                # attempt still owns the claim.  The queue contract
                # (the stale-claim function) is unchanged.
                reviewer_step = "receipt-preflight"
                existing_receipt = await reviewer.native.fetchval(
                    "SELECT control.slaif_review_promotion_receipt_read($1)",
                    job_id,
                )
                if existing_receipt is not None:
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                # 083/12 binding step: the workspace must still point
                # at exactly the approved snapshot, and the companion
                # re-read under the locked workspace must carry exactly
                # the approved digests and binding (defense in depth
                # over the step-3 verification; the manifest is
                # immutable per snapshot, so a disagreement is
                # approval corruption, not drift to retry).
                reviewer_step = "binding"
                bound_snapshot_id = await reviewer.native.fetchval(
                    "SELECT review_snapshot_id FROM control.workspace WHERE id = $1",
                    workspace_id,
                )
                if bound_snapshot_id is None or str(bound_snapshot_id) != str(
                    facts["snapshot_id"]
                ):
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                manifest_live = await reviewer.native.fetchval(
                    "SELECT control.slaif_review_operation_manifest_read($1)",
                    facts["snapshot_id"],
                )
                try:
                    manifest_live = _decode_jsonb(manifest_live)
                except ValueError:
                    manifest_live = None
                if (
                    not isinstance(manifest_live, dict)
                    or manifest_live.get("schema_version")
                    != operation_manifest.MANIFEST_SCHEMA_VERSION
                    or manifest_live.get("manifest_digest") != facts["manifest_digest"]
                    or manifest_live.get("snapshot_digest") != facts["digest"]
                    or manifest_live.get("manifest_id") != facts["manifest_id"]
                    or manifest_live.get("site_id") != str(site_id)
                    or manifest_live.get("workspace_id") != str(workspace_id)
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # 083/12-c: the approved identities (operation set and
                # dependency pairs) are derived STRICTLY from THIS live
                # read - staged shape checks (unique canonical UUID
                # strings, unique two-endpoint pairs) plus exact
                # equality with the step-3 verified facts - and those
                # derived sets drive the live U/dependency/provenance
                # comparisons below.  The manifest is immutable per
                # snapshot, so any disagreement is corruption.
                reviewer_step = "identities"
                try:
                    live_operations, live_pairs = _strict_manifest_identities(
                        manifest_live,
                        facts["approved_operations"],
                        facts["approved_pairs"],
                    )
                    # 083/12-c: the companion envelope re-validated
                    # from THIS live read with the SAME fail-closed
                    # builder the freeze worker uses (strict identity
                    # forms, one per U member, exact U coverage).
                    # Sorting/deduplication NEVER repairs a corrupted
                    # stored array: the stored arrays must already be
                    # in the exact canonical order, enforced by the
                    # order-sensitive equality below BEFORE the digest
                    # re-derivation.
                    raw_identities = manifest_live.get("completion_identities")
                    if not isinstance(raw_identities, list):
                        raise ValueError("identity list shape")
                    envelope = json.loads(
                        build_operation_manifest(
                            workspace_id=workspace_id,
                            site_id=site_id,
                            operations=sorted(live_operations),
                            dependencies=sorted(live_pairs),
                            completion_identities=raw_identities,
                        )
                    )
                    if (
                        manifest_live.get("operation_ids") != envelope["operation_ids"]
                        or manifest_live.get("dependency_pairs")
                        != envelope["dependency_pairs"]
                        or manifest_live.get("completion_identities")
                        != envelope["completion_identities"]
                    ):
                        raise ValueError("stored array not canonical")
                    # The companion manifest digest re-derived over
                    # the exact 079 canonical input (schema_version,
                    # snapshot/site/workspace binding, the validated
                    # canonical arrays - manifest_id/manifest_digest
                    # are bindings OUTSIDE the hashed input): the
                    # stored digest field is never trusted alone.
                    if (
                        canonical_digest(
                            {
                                "schema_version": manifest_live.get("schema_version"),
                                "snapshot_id": str(facts["snapshot_id"]),
                                "snapshot_digest": facts["digest"],
                                "site_id": str(site_id),
                                "workspace_id": str(workspace_id),
                                "operation_ids": envelope["operation_ids"],
                                "dependency_pairs": envelope["dependency_pairs"],
                                "completion_identities": envelope[
                                    "completion_identities"
                                ],
                            }
                        )
                        != facts["manifest_digest"]
                    ):
                        raise ValueError("manifest digest")
                except ValueError:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
                # 083/12-c: re-verify the stored domain approval on
                # the locked reviewer connection - the exact durable
                # approval tuple (both payload digests), the stored
                # snapshot's workspace/site binding, versions and
                # normalized-state strict shapes, and the 076 v2
                # invariants re-derived from the ACTUAL stored
                # content: normalized_state IS NOT DISTINCT FROM
                # payload (PG jsonb value equality, type-sensitive -
                # checked in SQL so a nested true/1 pair can never
                # pass) plus the trusted digest recomputed over the
                # stored payload with the 070 canonical form (the
                # Decimal-aware parser + the byte-identical Python
                # canonical serializer need no materializer and no
                # new SQL grant).  So a between-phase mutation of the
                # stored approval cannot reach publication.  The full
                # re-materialization stays in the step-3 transaction:
                # the 076 materializer owns a transaction-local COW
                # context and never runs inside the reviewer scope.
                reviewer_step = "stored-approval"
                stored_live = await reviewer.native.fetchrow(
                    "SELECT workspace_id, site_id, digest, versions, "
                    "normalized_state, payload "
                    "FROM control.review_snapshot "
                    "WHERE id = $1 "
                    "  AND normalized_state IS NOT DISTINCT FROM payload",
                    facts["snapshot_id"],
                )
                if (
                    stored_live is None
                    or str(stored_live["workspace_id"]) != str(workspace_id)
                    or str(stored_live["site_id"]) != str(site_id)
                    or not isinstance(stored_live["digest"], str)
                    or not _DIGEST_64_RE.fullmatch(stored_live["digest"])
                    or str(stored_live["digest"]) != snapshot_digest
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # Trusted digest re-derivation over the actual stored
                # content (076 invariant recomputed here, in-
                # transaction): a stored digest that no longer matches
                # its own payload is approval corruption.
                stored_payload_text = stored_live["payload"]
                if isinstance(stored_payload_text, (bytes, bytearray)):
                    stored_payload_text = stored_payload_text.decode("utf-8")
                if not isinstance(stored_payload_text, str):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                try:
                    stored_payload = parse_snapshot_text(stored_payload_text)
                except ValueError:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
                if not isinstance(stored_payload, dict) or canonical_digest(
                    stored_payload
                ) != str(stored_live["digest"]):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                versions_live = stored_live["versions"]
                if isinstance(versions_live, (bytes, bytearray)):
                    versions_live = versions_live.decode("utf-8")
                if isinstance(versions_live, str):
                    try:
                        versions_live = json.loads(versions_live)
                    except ValueError:
                        versions_live = None
                if (
                    not isinstance(versions_live, dict)
                    or versions_live != facts["versions"]
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                normalized_live = stored_live["normalized_state"]
                if isinstance(normalized_live, (bytes, bytearray)):
                    normalized_live = normalized_live.decode("utf-8")
                if isinstance(normalized_live, str):
                    try:
                        normalized_live = json.loads(normalized_live)
                    except ValueError:
                        normalized_live = None
                if (
                    not isinstance(normalized_live, dict)
                    or not isinstance(normalized_live.get("base_site_revision"), int)
                    or isinstance(normalized_live.get("base_site_revision"), bool)
                    or normalized_live.get("base_site_revision")
                    != facts["base_site_revision"]
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                reviewer_step = "operations"
                operations = await reviewer.operations(workspace_id, schema="content")
                if len(operations) != len(set(operations)):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                if set(operations) != live_operations:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                reviewer_step = "dependencies"
                dependencies = await reviewer.dependencies(
                    workspace_id, schema="content"
                )
                if len(dependencies) != len(set(dependencies)) or any(
                    parent not in live_operations or child not in live_operations
                    for parent, child in dependencies
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                if set(dependencies) != live_pairs:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                # 083/12-c: the CURRENT trusted completion records of
                # exactly live U - the 078 journal projection or the
                # 083/12 provenance step: the trusted whole-workspace
                # check (every U member's 078 journal binding, the
                # family reservation and event relation, and no
                # conflicting prospective facts) must pass in this
                # same transaction before any publication - and
                # BEFORE the selected-U identity projection is used:
                # the projection omits a member whose 078 journal
                # identity is missing, so a missing-journal refusal
                # must surface as the typed provenance refusal (with
                # its own stable code), not be masked into a generic
                # validation failure by the projection comparison.
                reviewer_step = "provenance"
                try:
                    await reviewer.native.fetchval(
                        "SELECT control.slaif_review_operation_provenance($1, $2, $3)",
                        workspace_id,
                        site_id,
                        sorted(live_operations, key=str),
                    )
                except asyncpg.PostgresError as error:
                    message = (error.message or "").strip()
                    if message in _PROVENANCE_REFUSALS:
                        raise AcceptJobError(
                            "PROVENANCE_VERIFICATION_FAILED", kind="validation"
                        ) from None
                    raise
                # Trusted producer records as of THIS transaction -
                # must equal the frozen companion identities.  The
                # provenance predicate alone does not compare the
                # current exact completion record of each U member to
                # the previously approved one, so the direct worker
                # identity projection (the same call the freeze
                # worker uses) is re-run here - after the whole-
                # workspace provenance check has already passed - and
                # compared with the type-sensitive canonical bytes of
                # the stored identities.
                reviewer_step = "identity-projection"
                projection = await reviewer.native.fetchval(
                    "SELECT control.slaif_review_operation_identities($1, $2, $3)",
                    workspace_id,
                    site_id,
                    [str(operation) for operation in sorted(live_operations)],
                )
                projected = _decode_jsonb(projection)
                if not isinstance(projected, list) or canonical_json(
                    projected
                ) != canonical_json(envelope["completion_identities"]):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                try:
                    reviewer_step = "commit-session"
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
                except asyncpg.UniqueViolationError:
                    # A session row collides with a canonical row on a
                    # unique key (two workspaces proposed the same media
                    # hash; the first promotion committed it).  This is
                    # deterministic: a retry can never repair it, so the
                    # job terminates as a typed conflict.  The whole
                    # transaction rolls back: no partial canonical
                    # effect, no revision/audit/outbox.
                    raise AcceptJobError(
                        "UNIQUE_CONSTRAINT_CONFLICT", kind="conflict"
                    ) from None
                # 083/12 applied-identity check: the real commit must
                # have applied EXACTLY the approved operation universe
                # to exactly this session, with no pending remainder -
                # re-inspected through the public session getter in
                # this same transaction after the real commit and
                # before any business (revision/audit) effect.
                reviewer_step = "applied"
                committed_operations = tuple(result.committed_operations)
                if (
                    len(committed_operations) != len(set(committed_operations))
                    or set(committed_operations) != live_operations
                    or result.session_id != workspace_id
                    or result.schema != "content"
                    or result.has_pending_operations is not False
                ):
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                if await reviewer.operations(workspace_id, schema="content") != []:
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    )
                try:
                    reviewer_step = "publicize"
                    await publicize_promoted_media(
                        site_id, facts["media_ids"], native=reviewer.native
                    )
                except FinalizationRepositoryError:
                    # The promoted base state diverged from the frozen
                    # media closure (missing or unreferenced row).
                    # Deterministic: terminal validation refusal, same
                    # transaction rollback.
                    raise AcceptJobError(
                        "SNAPSHOT_VALIDATION_FAILED", kind="validation"
                    ) from None
                reviewer_step = "revision"
                new_revision = await reviewer.native.fetchval(
                    "UPDATE control.site SET canonical_revision = "
                    "canonical_revision + 1 WHERE id = $1 RETURNING "
                    "canonical_revision",
                    site_id,
                )
                reviewer_step = "audit"
                await reviewer.native.execute(
                    "INSERT INTO audit.promotion "
                    "(site_id, workspace_id, snapshot_id, job_id, digest, "
                    "base_site_revision, new_canonical_revision, "
                    "committed_operations, versions, actor_user_account_id, "
                    "applied_operation_ids, manifest_id, manifest_digest) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)",
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
                    [str(operation) for operation in sorted(live_operations)],
                    UUID(facts["manifest_id"]),
                    facts["manifest_digest"],
                )
                reviewer_step = "workspace-terminal"
                updated = await reviewer.native.execute(
                    "UPDATE control.workspace SET status = 'ACCEPTED', "
                    "accepted_at = now() WHERE id = $1 AND status = 'PROMOTING'",
                    workspace_id,
                )
                if updated != "UPDATE 1":
                    raise AcceptJobError("STATE_DRIFT", kind="state")
                reviewer_step = "job-terminal"
                await reviewer.native.fetchval(
                    "SELECT control.slaif_review_job_terminal($1, 'SUCCEEDED', NULL)",
                    job_id,
                )
                reviewer_step = "outbox"
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
                reviewer_step = "transaction-exit"
                reviewer_body_completed = True
        return JobResult("SUCCEEDED")
    except AcceptJobError as error:
        # The terminal state change (workspace transition + job
        # terminal mark) is made in ONE locked claim-gated
        # transaction: a stale attempt must never re-queue or
        # terminal-mark a moved claim (the claim function's
        # stale-claim recovery owns the moved job, and the next claim
        # re-verifies the same durable facts).  Kind "state" (a
        # moved/corrupted durable claim or pipeline state) makes NO
        # workspace transition at all: the durable state is left
        # exactly as found for the new owner or the human, and the
        # from/to pair must stay consistent (a from without a target
        # would raise before the fail-closed gate ran).  A still-
        # owned valid refusal terminal-marks the job with NO
        # transition; a stale/mutated claim defers with no write.
        if error.kind in ("drift", "validation"):
            workspace_from: str | None = "PROMOTING"
            workspace_target: str | None = "REVIEW"
        elif error.kind == "conflict":
            workspace_from, workspace_target = "PROMOTING", "CONFLICTED"
        else:
            workspace_from, workspace_target = None, None
        applied = await _claim_gated_state_change(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
            workspace_from=workspace_from,
            workspace_target=workspace_target,
            job_failed_code=error.code,
        )
        if applied != "applied":
            LOGGER.warning(
                "slaif-diag: review-job phase=terminal-deferral code=%s "
                "outcome=%s attempt=%s job=%s",
                error.code,
                applied,
                attempt_count,
                job_id,
            )
            return JobResult("ROLLED_BACK")
        return JobResult("FAILED", error.code)
    except (asyncpg.PostgresError, TimeoutError, OSError) as error:
        # Reviewer-scope driver failure (c2): classify BEFORE any
        # recovery mutation.  The SDK commits and THEN runs native
        # SQL cleanup (safe_session.clean_after_transaction), so a
        # PostgresError can arrive AFTER a successful native commit:
        # whenever the body completed, reconcile the possible
        # publication first (bounded diagnostic: closed step state +
        # class + SQLSTATE only, never the message).  With the body
        # still running, the SDK rolled the transaction back, so the
        # commit is proven absent: a transport/transient fault (a
        # lost backend, a native cancellation, the lock timeout our
        # own SET LOCAL raises) keeps the ordinary requeue under
        # budget with no receipt read, and a deterministic SQL/
        # programming fault (e.g. 42P01, 42501, P0001) is terminal -
        # it must not enter the ordinary retry/requeue path.
        failure_class = _reviewer_failure_class(error, reviewer_body_completed)
        log_bounded_db_failure("reviewer-tx", error)
        LOGGER.warning(
            "slaif-diag: review-job phase=reviewer-step step=%s "
            "failure-class=%s outcome=failed job=%s",
            reviewer_step,
            failure_class,
            job_id,
        )
        if failure_class == "retry":
            # Proven absent (the SDK rolled the transaction back):
            # no receipt read, the ordinary requeue under budget.
            return await _retryable_or_budget(
                "postgres_transient"
                if isinstance(error, asyncpg.PostgresError)
                else "io_transient"
            )
        if failure_class == "programming" and not reviewer_body_completed:
            # Proven absent and deterministic: terminal, no retry.
            return await _programming_terminal(
                pool,
                job_id=job_id,
                workspace_id=workspace_id,
                site_id=site_id,
                claimant=claimant,
                attempt_count=attempt_count,
                claimed_payload=payload,
            )
        # "uncertain", or a DETERMINISTIC server-declared fault at
        # the commit/cleanup boundary (it may have arrived after a
        # successful native commit): the durable outcome decides -
        # success on the exact fingerprint, deferral on
        # contradiction, and on a proven absence the policy above
        # keeps a bounded retry for a transient fault and terminals
        # a definite rejection (e.g. a deferred constraint at
        # COMMIT).
        return await _settle_uncertain(
            error, "terminal" if failure_class == "programming" else "retryable"
        )
    except asyncpg.InterfaceError as error:
        # A client-mechanism InterfaceError (c2): the SDK's
        # post-COMMIT scope/pool cleanup re-raises ONLY when the body
        # and the native commit succeeded, so a completed body means
        # the commit state is uncertain and the outcome is reconciled
        # against the durable publication state exactly like the
        # driver-error path above - never assumed to be success,
        # never assumed to be a proven rollback.  A body-stage
        # InterfaceError (possibly the SDK's post-failure rollback
        # masking a transport loss, which the chain keeps
        # transport-class) can NEVER have committed: transport-grade
        # faults in the chain keep the ordinary requeue; a generic
        # client-mechanism fault is a programming failure -
        # terminal, no retry.
        failure_class = _reviewer_failure_class(error, reviewer_body_completed)
        log_bounded_db_failure("reviewer-tx", error)
        LOGGER.warning(
            "slaif-diag: review-job phase=reviewer-step step=%s "
            "failure-class=%s outcome=failed job=%s",
            reviewer_step,
            failure_class,
            job_id,
        )
        if failure_class == "retry":
            # Proven absent (the SDK rolled the transaction back):
            # no receipt read, the ordinary requeue under budget.
            return await _retryable_or_budget("io_transient")
        if failure_class == "programming" and not reviewer_body_completed:
            # Proven absent and deterministic: terminal, no retry.
            return await _programming_terminal(
                pool,
                job_id=job_id,
                workspace_id=workspace_id,
                site_id=site_id,
                claimant=claimant,
                attempt_count=attempt_count,
                claimed_payload=payload,
            )
        # Post-commit scope/pool channel: the durable outcome
        # decides, exactly like the driver-error path.
        return await _settle_uncertain(error, "retryable")
    except CowPromotionStateError as error:
        # The SDK's own public state invariant (c2): safe_promotion
        # commits and THEN runs the native-SQL cleanup, and raises
        # this both when the owned transaction ended unexpectedly
        # (before the body) and when a COW context survives cleanup
        # (AFTER a possibly successful native commit).  With the
        # body completed, reconcile the possible publication first,
        # exactly like the driver-error path; before the body the
        # commit cannot have landed and the invariant violation is
        # deterministic - terminal, no retry.
        log_bounded_db_failure("reviewer-tx", error)
        LOGGER.warning(
            "slaif-diag: review-job phase=reviewer-step step=%s "
            "failure-class=state-error outcome=failed job=%s",
            reviewer_step,
            job_id,
        )
        if reviewer_body_completed:
            return await _settle_uncertain(error, "retryable")
        return await _programming_terminal(
            pool,
            job_id=job_id,
            workspace_id=workspace_id,
            site_id=site_id,
            claimant=claimant,
            attempt_count=attempt_count,
            claimed_payload=payload,
        )


__all__ = [
    "AcceptJobError",
    "MediaBoundary",
    "run_accept_job",
    "shutdown_media_boundary",
    "shared_media_boundary",
]

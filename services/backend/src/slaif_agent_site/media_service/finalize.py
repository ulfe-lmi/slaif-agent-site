"""Promotion-boundary media finalization: byte preparation + in-tx mark.

The publication boundary is split into two phases that the accept job
drives from opposite sides of the reviewer transaction:

- Phase 1, ``finalize_media_for_promotion`` (accept step 4, BEFORE the
  reviewer transaction): each referenced media is resolved in the
  workspace's own COW context (pending assets included), digest-verified
  through ``open_verified``, and idempotently copied to the public
  namespace.  This is byte preparation only: it performs NO database
  status mutation, so a failure or a later rollback leaves the canonical
  state untouched and at most leaves harmless unreferenced public
  objects (the 083/1 orphan rule).
- Phase 2, ``publicize_promoted_media`` (accept step 5, INSIDE the
  single ``asyncpg_cow_reviewer`` transaction, after the foundation
  promotion): the least-authority product helper
  ``content.slaif_media_publicize_promoted`` (EXECUTE granted to
  ``slaif_review_worker`` only) marks exactly the promoted,
  base-referenced rows public on the canonical base, atomically with the
  promotion, the site revision, the promotion audit, the workspace/job
  success and the cache outbox.  There is no separately committed mark:
  any failure aborts the whole transaction.

The module is pure orchestration over the immutable store and a narrow
record repository: no HTTP, no browser, no network, and no DB session
parameter beyond what the record repository and the actual reviewer
connection need.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID, uuid4

import asyncpg

from slaif_agent_site.agent_state.foundation import asyncpg_cow_session

from .database import MediaDatabase, MediaRecord, _record
from .store import MediaStore, MediaStoreError

LOGGER = logging.getLogger(__name__)

# Closed allowlist of the stable MediaStoreError reason tokens (the
# exact constants the store raises); any other value is logged as
# store_error. No exception message is ever forwarded.
_STORE_REASON_TOKENS = frozenset(
    {
        "media-pdf-too-large",
        "media_missing",
        "media_signature_mismatch",
        "storage_corrupt",
        "storage_unavailable",
        "unsupported_media",
    }
)
_SQLSTATE_ALPHABET = frozenset("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_IDENTIFIER_SHAPE = re.compile(r"[A-Za-z_][A-Za-z0-9_$]{0,62}\Z")
_CLASS_NAME_SHAPE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}\Z")


def _bounded_sqlstate(error: asyncpg.PostgresError) -> str:
    sqlstate = error.sqlstate
    if (
        not isinstance(sqlstate, str)
        or len(sqlstate) != 5
        or not _SQLSTATE_ALPHABET.issuperset(sqlstate)
    ):
        return "-"
    return sqlstate


def _bounded_class_name(error: BaseException) -> str:
    # A class name is code-identifiable; anything outside the closed
    # identifier shape (which no real class produces) is emitted as the
    # fixed token unknown rather than forwarded.
    name = type(error).__name__
    if not _CLASS_NAME_SHAPE.fullmatch(name):
        return "unknown"
    return name


def _bounded_constraint(error: BaseException) -> str:
    # The pinned asyncpg public field is constraint_name (error field
    # 'n'); the value is a trusted identifier or omitted.
    constraint = getattr(error, "constraint_name", None)
    if isinstance(constraint, str) and _IDENTIFIER_SHAPE.fullmatch(constraint):
        return constraint
    return "-"


def log_bounded_db_failure(phase: str, error: BaseException) -> None:
    """Bounded worker diagnostic for a database-side failure.

    Emits only the exception class name and, for PostgreSQL errors, the
    five-character SQLSTATE from the closed alphabet. Never the
    exception message: it can carry server detail, SQL text, or
    connection strings.
    """

    if isinstance(error, asyncpg.PostgresError):
        LOGGER.warning(
            "slaif-diag: review-job phase=%s outcome=failed class=%s sqlstate=%s",
            phase,
            _bounded_class_name(error),
            _bounded_sqlstate(error),
        )
    else:
        LOGGER.warning(
            "slaif-diag: review-job phase=%s outcome=failed class=%s",
            phase,
            _bounded_class_name(error),
        )


def log_bounded_fetch_failure(error: BaseException) -> None:
    """Bounded worker diagnostic for the finalization COW fetch failure."""

    if isinstance(error, asyncpg.PostgresError):
        LOGGER.warning(
            "slaif-diag: review-job phase=fetch outcome=failed class=%s "
            "sqlstate=%s constraint=%s",
            _bounded_class_name(error),
            _bounded_sqlstate(error),
            _bounded_constraint(error),
        )
    else:
        LOGGER.warning(
            "slaif-diag: review-job phase=fetch outcome=failed class=%s",
            _bounded_class_name(error),
        )


MEDIA_PUBLIC_FETCH_SQL = "SELECT * FROM content.slaif_media_public_fetch($1,$2)"
MEDIA_PUBLICIZE_SQL = "SELECT content.slaif_media_publicize_promoted($1,$2)"


@dataclass(frozen=True, slots=True)
class FinalizedMedia:
    """One finalized media entry: the deterministic manifest shape."""

    media_id: UUID
    digest: str
    public_key: str


@dataclass(frozen=True, slots=True)
class FinalizationManifest:
    """Deterministically ordered manifest of the bytes made public."""

    entries: tuple[FinalizedMedia, ...]

    def to_list(self) -> list[dict[str, str]]:
        return [
            {
                "media_id": str(entry.media_id),
                "digest": entry.digest,
                "public_key": entry.public_key,
            }
            for entry in self.entries
        ]


class FinalizationRepositoryError(RuntimeError):
    """A bounded record-boundary failure with a stable, non-sensitive reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class FinalizationError(RuntimeError):
    """Finalization failure carrying the exact manifest of bytes made public."""

    def __init__(self, reason: str, manifest: FinalizationManifest) -> None:
        super().__init__(reason)
        self.reason = reason
        self.manifest = manifest


class FinalizationRepository(Protocol):
    """The narrow record boundary the primitive orchestrates over."""

    async def fetch_media(
        self, site_id: UUID, media_id: UUID, workspace_id: UUID
    ) -> MediaRecord | None:
        """Return the site-owned record in the workspace's COW context.

        Resolves base rows plus the workspace's own pending change rows
        (a freshly uploaded asset is visible to its own workspace only);
        never another site's row.
        """


class MediaFinalizationRepository:
    """COW-bound record adapter for finalization over the media pool."""

    def __init__(self, database: MediaDatabase) -> None:
        self._database = database

    async def fetch_media(
        self, site_id: UUID, media_id: UUID, workspace_id: UUID
    ) -> MediaRecord | None:
        # The fetch must see the workspace's own overlay: a freshly
        # registered (pending) asset exists only as this session's change
        # row, so the read runs in the workspace's COW context exactly
        # like every other authorized workspace media read.
        try:
            async with asyncpg_cow_session(
                self._database.cow_pool(),
                session_id=workspace_id,
                operation_id=uuid4(),
            ) as cow:
                row = await cow.native.fetchrow(
                    MEDIA_PUBLIC_FETCH_SQL, site_id, media_id
                )
        except asyncio.CancelledError:
            raise
        except Exception as error:
            # Bounded worker diagnostic (class/SQLSTATE/constraint only,
            # never the message); the stable reason mapping is unchanged.
            log_bounded_fetch_failure(error)
            raise FinalizationRepositoryError("repository_unavailable") from None
        return None if row is None else _record(row)


def _log_store_failure(phase: str, error: MediaStoreError) -> None:
    """Bounded worker diagnostic: the stable store reason only, no paths.

    The message is consulted only for closed-set membership; it is
    never forwarded.
    """

    reason = str(error)
    if reason not in _STORE_REASON_TOKENS:
        reason = "store_error"
    LOGGER.warning(
        "slaif-diag: review-job phase=%s outcome=failed reason=%s",
        phase,
        reason,
    )


async def finalize_media_for_promotion(
    site_id: UUID,
    workspace_id: UUID,
    media_ids: Sequence[UUID],
    *,
    store: MediaStore,
    repository: FinalizationRepository,
) -> FinalizationManifest:
    """Phase 1: prepare the bytes for exactly the referenced media.

    Each input media is resolved in the workspace's COW context and
    validated as site-owned, digest-verified through ``open_verified``,
    and idempotently copied to the public namespace.  No database status
    mutation happens here: the public-status mark is phase 2, inside the
    reviewer transaction.  Entries are processed in deterministic
    (sorted, deduplicated) order and the returned manifest is the audit
    of truth for the bytes prepared for publication.
    """

    manifest: list[FinalizedMedia] = []

    def _failure(reason: str) -> FinalizationError:
        return FinalizationError(reason, FinalizationManifest(tuple(manifest)))

    for media_id in sorted(set(media_ids)):
        try:
            record = await repository.fetch_media(site_id, media_id, workspace_id)
        except FinalizationRepositoryError as error:
            raise _failure(error.reason) from None
        if record is None:
            raise _failure("media_not_found") from None
        descriptor: int | None = None
        try:
            descriptor, _size = await asyncio.to_thread(
                store.open_verified,
                record.storage_key,
                record.content_hash,
                record.size_bytes,
            )
        except MediaStoreError as error:
            _log_store_failure("open_verified", error)
            raise _failure("store_unavailable") from None
        finally:
            if descriptor is not None:
                os.close(descriptor)
        try:
            public_key = await asyncio.to_thread(
                store.publish_public,
                record.storage_key,
                record.content_hash,
                record.size_bytes,
            )
        except MediaStoreError as error:
            _log_store_failure("publish_public", error)
            raise _failure("store_unavailable") from None
        manifest.append(
            FinalizedMedia(
                media_id=media_id,
                digest=record.content_hash,
                public_key=public_key,
            )
        )
    return FinalizationManifest(tuple(manifest))


async def publicize_promoted_media(
    site_id: UUID,
    media_ids: Sequence[UUID],
    *,
    native: Any,
) -> None:
    """Phase 2: mark the promoted media public on the canonical base.

    Must run INSIDE the single reviewer promotion transaction, after the
    foundation promotion has committed the session's pending rows.  The
    helper is least-authority (EXECUTE to ``slaif_review_worker`` only)
    and fails closed on a missing, invalid or unreferenced row
    (P0002/P0003 ->
    ``media_not_found``/``media_not_workspace_referenced``); any failure
    raises and the caller's transaction rolls back the promotion, the
    revision increment, the promotion audit, the workspace/job success
    and the outbox together with this mark.
    """

    try:
        await native.execute(MEDIA_PUBLICIZE_SQL, site_id, list(media_ids))
    except asyncio.CancelledError:
        raise
    except asyncpg.PostgresError as error:
        sqlstate = getattr(error, "sqlstate", None)
        if sqlstate == "P0002":
            raise FinalizationRepositoryError("media_not_found") from None
        if sqlstate == "P0003":
            raise FinalizationRepositoryError(
                "media_not_workspace_referenced"
            ) from None
        raise
    except Exception:
        raise


__all__ = [
    "FinalizationError",
    "FinalizationManifest",
    "FinalizationRepository",
    "FinalizationRepositoryError",
    "FinalizedMedia",
    "MediaFinalizationRepository",
    "finalize_media_for_promotion",
    "publicize_promoted_media",
]

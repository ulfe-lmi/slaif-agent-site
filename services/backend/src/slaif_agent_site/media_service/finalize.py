"""Promotion-callable media finalization primitive (pure orchestration).

This module owns the exact promotion-boundary call later promotion orders
will make inside the reviewer boundary, before commit.  It is pure
orchestration over the immutable store and a narrow record repository: no
HTTP, no browser, no network, and no DB session parameter beyond what the
record repository needs.  A mid-run failure leaves previously public assets
untouched and at most unreferenced public objects for GC; the raised
manifest lists exactly which bytes were made public.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

import asyncpg

from slaif_agent_site.agent_state.foundation import asyncpg_cow_session

from .database import MediaDatabase, MediaRecord, _record
from .store import MediaStore, MediaStoreError

MEDIA_PUBLIC_FETCH_SQL = "SELECT * FROM content.slaif_media_public_fetch($1,$2)"
MEDIA_PUBLIC_MARK_SQL = "SELECT * FROM content.slaif_media_public_mark($1,$2,$3,$4)"


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

    async def fetch_media(self, site_id: UUID, media_id: UUID) -> MediaRecord | None:
        """Return the site-owned record or None; never another site's row."""

    async def mark_public(
        self, site_id: UUID, media_id: UUID, workspace_id: UUID
    ) -> None:
        """Set public_status='public' + published_at; idempotent for public."""


class MediaFinalizationRepository:
    """COW-bound record adapter for finalization over the media pool."""

    def __init__(self, database: MediaDatabase) -> None:
        self._database = database

    async def fetch_media(self, site_id: UUID, media_id: UUID) -> MediaRecord | None:
        try:
            async with self._database.cow_pool().acquire(
                timeout=self._database.settings.acquire_timeout_seconds
            ) as connection:
                row = await connection.fetchrow(
                    MEDIA_PUBLIC_FETCH_SQL, site_id, media_id
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise FinalizationRepositoryError("repository_unavailable") from None
        return None if row is None else _record(row)

    async def mark_public(
        self, site_id: UUID, media_id: UUID, workspace_id: UUID
    ) -> None:
        operation_id = uuid4()
        try:
            async with asyncpg_cow_session(
                self._database.cow_pool(),
                session_id=workspace_id,
                operation_id=operation_id,
            ) as cow:
                row = await cow.native.fetchrow(
                    MEDIA_PUBLIC_MARK_SQL,
                    site_id,
                    media_id,
                    workspace_id,
                    operation_id,
                )
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
            raise FinalizationRepositoryError("repository_unavailable") from None
        except Exception:
            raise FinalizationRepositoryError("repository_unavailable") from None
        if row is None:
            raise FinalizationRepositoryError("media_not_found") from None


async def finalize_media_for_promotion(
    site_id: UUID,
    workspace_id: UUID,
    media_ids: Sequence[UUID],
    *,
    store: MediaStore,
    repository: FinalizationRepository,
) -> FinalizationManifest:
    """Finalize exactly the referenced media for one promotion boundary.

    Each input media is validated as site-owned and workspace-referenced
    (the mark function fails closed otherwise), digest-verified through
    ``open_verified``, idempotently published to the public namespace, and
    marked public with a stable ``published_at``.  Entries are processed in
    deterministic (sorted, deduplicated) order and the returned manifest is
    the audit of truth for the bytes made public.
    """

    manifest: list[FinalizedMedia] = []

    def _failure(reason: str) -> FinalizationError:
        return FinalizationError(reason, FinalizationManifest(tuple(manifest)))

    for media_id in sorted(set(media_ids)):
        try:
            record = await repository.fetch_media(site_id, media_id)
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
        except MediaStoreError:
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
        except MediaStoreError:
            raise _failure("store_unavailable") from None
        manifest.append(
            FinalizedMedia(
                media_id=media_id,
                digest=record.content_hash,
                public_key=public_key,
            )
        )
        try:
            await repository.mark_public(site_id, media_id, workspace_id)
        except FinalizationRepositoryError as error:
            raise _failure(error.reason) from None
    return FinalizationManifest(tuple(manifest))


__all__ = [
    "FinalizationError",
    "FinalizationManifest",
    "FinalizationRepository",
    "FinalizationRepositoryError",
    "FinalizedMedia",
    "MediaFinalizationRepository",
    "finalize_media_for_promotion",
]

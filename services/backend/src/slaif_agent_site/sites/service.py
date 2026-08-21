"""Control-only semantic site persistence and trusted resolver service."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

import asyncpg

from .models import (
    CreateSiteRequest,
    DomainMapping,
    DomainMappingRequest,
    SiteContext,
    SiteRecord,
    SiteStatus,
    UpdateSiteRequest,
)
from .normalization import (
    SiteInputError,
    normalize_authority,
    normalize_request_path,
    normalize_site_key,
    path_is_reserved,
)

COMPONENT_CATALOG_VERSION = "catalog-v0"
CREATE_SITE_SQL = "SELECT * FROM control.slaif_site_create($1, $2, $3, $4)"
GET_SITE_SQL = "SELECT * FROM control.slaif_site_get($1)"
LIST_SITES_SQL = "SELECT * FROM control.slaif_site_list()"
UPDATE_SITE_SQL = "SELECT * FROM control.slaif_site_update($1, $2, $3)"
ARCHIVE_SITE_SQL = "SELECT * FROM control.slaif_site_archive($1)"
PUT_DOMAIN_SQL = "SELECT * FROM control.slaif_site_domain_put($1, $2, $3, $4, $5)"
REMOVE_DOMAIN_SQL = "SELECT control.slaif_site_domain_remove($1, $2)"
RESOLVE_SITE_SQL = "SELECT * FROM control.slaif_site_resolve($1, $2)"
RESOLVE_LOCAL_SQL = "SELECT * FROM control.slaif_site_resolve_local($1)"


class SiteServiceReason(StrEnum):
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"


class SiteServiceError(RuntimeError):
    """A stable public-safe site operation failure."""

    def __init__(self, reason: SiteServiceReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


def _site(row: Any) -> SiteRecord:
    return SiteRecord(
        site_id=row[0],
        site_key=row[1],
        display_name=row[2],
        status=row[3],
        canonical_revision=row[4],
        default_locale=row[5],
        component_catalog_version=row[6],
        content_model_revision=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


def _mapping(row: Any) -> DomainMapping:
    return DomainMapping(
        domain_id=row[0],
        site_id=row[1],
        hostname=row[2],
        path_prefix=row[3],
        is_primary=row[4],
        created_at=row[5],
    )


class SiteService:
    """Perform semantic Control operations without relation authority."""

    def __init__(self, pool: _Pool, *, acquire_timeout: float = 3.0) -> None:
        self._pool = pool
        self._acquire_timeout = acquire_timeout

    async def _fetchrow(self, sql: str, *arguments: object) -> Any:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                async with connection.transaction():
                    return await connection.fetchrow(sql, *arguments)
        except asyncio.CancelledError:
            raise
        except asyncpg.UniqueViolationError:
            raise SiteServiceError(SiteServiceReason.CONFLICT) from None
        except asyncpg.RaiseError:
            raise SiteServiceError(SiteServiceReason.CONFLICT) from None
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise SiteServiceError(SiteServiceReason.UNAVAILABLE) from None

    async def create(self, request: CreateSiteRequest) -> SiteRecord:
        row = await self._fetchrow(
            CREATE_SITE_SQL,
            request.site_key,
            request.display_name,
            request.default_locale,
            COMPONENT_CATALOG_VERSION,
        )
        if row is None:
            raise SiteServiceError(SiteServiceReason.CONFLICT)
        return _site(row)

    async def get(self, site_id: UUID) -> SiteRecord:
        row = await self._fetchrow(GET_SITE_SQL, site_id)
        if row is None:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        return _site(row)

    async def list(self) -> tuple[SiteRecord, ...]:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                rows = await connection.fetch(LIST_SITES_SQL)
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise SiteServiceError(SiteServiceReason.UNAVAILABLE) from None
        return tuple(_site(row) for row in rows)

    async def update(
        self, context: SiteContext, request: UpdateSiteRequest
    ) -> SiteRecord:
        if context.status is not SiteStatus.ACTIVE:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        row = await self._fetchrow(
            UPDATE_SITE_SQL,
            context.site_id,
            request.display_name,
            request.default_locale,
        )
        if row is None:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        return _site(row)

    async def archive(self, context: SiteContext) -> SiteRecord:
        row = await self._fetchrow(ARCHIVE_SITE_SQL, context.site_id)
        if row is None:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        return _site(row)

    async def put_domain(
        self,
        context: SiteContext,
        request: DomainMappingRequest,
        *,
        domain_id: UUID | None = None,
    ) -> DomainMapping:
        if context.status is not SiteStatus.ACTIVE:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        row = await self._fetchrow(
            PUT_DOMAIN_SQL,
            context.site_id,
            domain_id,
            request.hostname,
            request.path_prefix,
            request.is_primary,
        )
        if row is None:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        return _mapping(row)

    async def remove_domain(self, context: SiteContext, domain_id: UUID) -> None:
        if context.status is not SiteStatus.ACTIVE:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        removed = await self._fetchrow(REMOVE_DOMAIN_SQL, context.site_id, domain_id)
        if removed is None or removed[0] is not True:
            raise SiteServiceError(SiteServiceReason.CONFLICT)

    async def resolve(self, authority: str, path: str) -> SiteContext:
        """Resolve trusted routing facts only; this grants no authorization."""

        try:
            normalized_authority = normalize_authority(authority)
            normalized_path = normalize_request_path(path)
        except SiteInputError:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND) from None
        if path_is_reserved(normalized_path):
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)

        segments = normalized_path.split("/")
        if len(segments) >= 2 and segments[1] == "s":
            if normalized_authority.hostname == "localhost" and len(segments) >= 3:
                try:
                    key = normalize_site_key(segments[2])
                except SiteInputError:
                    raise SiteServiceError(SiteServiceReason.NOT_FOUND) from None
                row = await self._fetchrow(RESOLVE_LOCAL_SQL, key)
                if row is None:
                    raise SiteServiceError(SiteServiceReason.NOT_FOUND)
                return SiteContext._from_database(
                    (*tuple(row), normalized_authority.hostname, f"/s/{key}")
                )
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)

        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                rows = await connection.fetch(
                    RESOLVE_SITE_SQL, normalized_authority.hostname, normalized_path
                )
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise SiteServiceError(SiteServiceReason.UNAVAILABLE) from None
        if not rows:
            raise SiteServiceError(SiteServiceReason.NOT_FOUND)
        if len(rows) > 1 and len(rows[0][6]) == len(rows[1][6]):
            raise SiteServiceError(SiteServiceReason.CONFLICT)
        return SiteContext._from_database(rows[0])


__all__ = [
    "ARCHIVE_SITE_SQL",
    "COMPONENT_CATALOG_VERSION",
    "CREATE_SITE_SQL",
    "GET_SITE_SQL",
    "LIST_SITES_SQL",
    "PUT_DOMAIN_SQL",
    "REMOVE_DOMAIN_SQL",
    "RESOLVE_LOCAL_SQL",
    "RESOLVE_SITE_SQL",
    "UPDATE_SITE_SQL",
    "SiteService",
    "SiteServiceError",
    "SiteServiceReason",
]

"""Resolver-only site boundary for read-only rendering processes."""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

import asyncpg

from .models import SiteContext
from .normalization import (
    SiteInputError,
    normalize_authority,
    normalize_request_path,
    normalize_site_key,
    path_is_reserved,
)

RESOLVE_SITE_SQL = "SELECT * FROM control.slaif_site_resolve($1, $2)"
RESOLVE_LOCAL_SQL = "SELECT * FROM control.slaif_site_resolve_local($1)"


class SiteResolverReason:
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UNAVAILABLE = "unavailable"


class SiteResolverError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


class SiteResolver:
    """Resolve only normalized public routing facts; grant no authorization."""

    def __init__(self, pool: _Pool, *, acquire_timeout: float = 3.0) -> None:
        self._pool = pool
        self._acquire_timeout = acquire_timeout

    async def resolve(self, authority: str, request_path: str) -> SiteContext:
        try:
            normalized_authority = normalize_authority(authority)
            normalized_path = normalize_request_path(request_path)
        except SiteInputError:
            raise SiteResolverError(SiteResolverReason.NOT_FOUND) from None
        if path_is_reserved(normalized_path):
            raise SiteResolverError(SiteResolverReason.NOT_FOUND)

        segments = normalized_path.split("/")
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                if len(segments) >= 2 and segments[1] == "s":
                    if (
                        normalized_authority.hostname != "localhost"
                        or len(segments) < 3
                    ):
                        raise SiteResolverError(SiteResolverReason.NOT_FOUND)
                    try:
                        key = normalize_site_key(segments[2])
                    except SiteInputError:
                        raise SiteResolverError(SiteResolverReason.NOT_FOUND) from None
                    row = await connection.fetchrow(RESOLVE_LOCAL_SQL, key)
                    if row is None:
                        raise SiteResolverError(SiteResolverReason.NOT_FOUND)
                    return SiteContext._from_database(
                        (*tuple(row), normalized_authority.hostname, f"/s/{key}")
                    )
                rows = await connection.fetch(
                    RESOLVE_SITE_SQL, normalized_authority.hostname, normalized_path
                )
        except asyncio.CancelledError:
            raise
        except SiteResolverError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise SiteResolverError(SiteResolverReason.UNAVAILABLE) from None
        if not rows:
            raise SiteResolverError(SiteResolverReason.NOT_FOUND)
        if len(rows) > 1 and len(rows[0][6]) == len(rows[1][6]):
            raise SiteResolverError(SiteResolverReason.CONFLICT)
        return SiteContext._from_database(rows[0])


__all__ = [
    "RESOLVE_LOCAL_SQL",
    "RESOLVE_SITE_SQL",
    "SiteResolver",
    "SiteResolverError",
    "SiteResolverReason",
]

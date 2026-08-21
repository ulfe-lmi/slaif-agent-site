"""Control-only semantic service for site membership and human authority."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

import asyncpg

from .models import (
    HumanSiteContext,
    MembershipChange,
    MembershipRecord,
    PermissionCatalogRecord,
)

AUTHORIZE_SQL = "SELECT * FROM control.slaif_human_authorize($1, $2, $3, $4)"
MEMBERSHIP_PUT_SQL = (
    "SELECT * FROM control.slaif_membership_put($1, $2, $3, $4, $5, $6, $7, $8)"
)
MEMBERSHIP_GET_SQL = "SELECT * FROM control.slaif_membership_get($1, $2)"
MEMBERSHIP_LIST_SQL = "SELECT * FROM control.slaif_membership_list($1)"
CATALOG_SQL = "SELECT * FROM control.slaif_human_rbac_catalog()"


class HumanAuthorizationReason(StrEnum):
    NOT_FOUND = "not_found"
    DENIED = "denied"
    CONFLICT = "conflict"
    UNAVAILABLE = "unavailable"


class HumanAuthorizationError(RuntimeError):
    def __init__(self, reason: HumanAuthorizationReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


def _context(row: Any) -> HumanSiteContext:
    return HumanSiteContext._from_database(row)


def _membership(row: Any) -> MembershipRecord:
    return MembershipRecord(
        site_id=row[0],
        user_account_id=row[1],
        role_key=row[2],
        delegation_ceiling=row[3],
        status=row[4],
        version=row[5],
        allow_permissions=frozenset(row[6]),
        deny_permissions=frozenset(row[7]),
        created_at=row[8],
        updated_at=row[9],
    )


class HumanAuthorizationService:
    """Evaluate and mutate RBAC only through fixed Control functions."""

    def __init__(self, pool: _Pool, *, acquire_timeout: float = 3.0) -> None:
        self._pool = pool
        self._acquire_timeout = acquire_timeout

    async def authorize(
        self,
        user_account_id: UUID,
        site_id: UUID,
        permission_key: str,
        *,
        expected_membership_version: int,
    ) -> HumanSiteContext:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                row = await connection.fetchrow(
                    AUTHORIZE_SQL,
                    user_account_id,
                    site_id,
                    permission_key,
                    expected_membership_version,
                )
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise HumanAuthorizationError(
                HumanAuthorizationReason.UNAVAILABLE
            ) from None
        if row is None:
            raise HumanAuthorizationError(HumanAuthorizationReason.DENIED)
        return _context(row)

    async def catalog(self) -> tuple[PermissionCatalogRecord, ...]:
        rows = await self._fetch(CATALOG_SQL)
        return tuple(
            PermissionCatalogRecord(
                permission_key=row[0],
                category=row[1],
                agent_delegation_level=row[2],
                site_assignable=row[3],
                installation_only=row[4],
                system_only=row[5],
                role_keys=tuple(row[6]),
            )
            for row in rows
        )

    async def membership(
        self, site_id: UUID, user_account_id: UUID
    ) -> MembershipRecord:
        rows = await self._fetch(MEMBERSHIP_GET_SQL, site_id, user_account_id)
        if not rows:
            raise HumanAuthorizationError(HumanAuthorizationReason.NOT_FOUND)
        return _membership(rows[0])

    async def memberships(self, site_id: UUID) -> tuple[MembershipRecord, ...]:
        return tuple(
            _membership(row) for row in await self._fetch(MEMBERSHIP_LIST_SQL, site_id)
        )

    async def _fetch(self, sql: str, *arguments: object) -> list[Any]:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                return list(await connection.fetch(sql, *arguments))
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise HumanAuthorizationError(
                HumanAuthorizationReason.UNAVAILABLE
            ) from None

    async def put_membership(
        self,
        actor_user_id: UUID,
        site_id: UUID,
        target_user_id: UUID,
        change: MembershipChange,
    ) -> HumanSiteContext:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                async with connection.transaction():
                    row = await connection.fetchrow(
                        MEMBERSHIP_PUT_SQL,
                        actor_user_id,
                        site_id,
                        target_user_id,
                        change.role_key,
                        change.delegation_ceiling,
                        change.status.value,
                        change.expected_version,
                        [
                            *(
                                f"ALLOW:{key}"
                                for key in sorted(change.allow_permissions)
                            ),
                            *(f"DENY:{key}" for key in sorted(change.deny_permissions)),
                        ],
                    )
        except asyncio.CancelledError:
            raise
        except asyncpg.SerializationError:
            raise HumanAuthorizationError(HumanAuthorizationReason.CONFLICT) from None
        except asyncpg.RaiseError as error:
            reason = {
                "RBAC_DENIED": HumanAuthorizationReason.DENIED,
                "RBAC_NOT_FOUND": HumanAuthorizationReason.NOT_FOUND,
                "RBAC_CONFLICT": HumanAuthorizationReason.CONFLICT,
            }.get(str(error), HumanAuthorizationReason.DENIED)
            raise HumanAuthorizationError(reason) from None
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise HumanAuthorizationError(
                HumanAuthorizationReason.UNAVAILABLE
            ) from None
        if row is None:
            raise HumanAuthorizationError(HumanAuthorizationReason.NOT_FOUND)
        return _context(row)


__all__ = [
    "AUTHORIZE_SQL",
    "CATALOG_SQL",
    "MEMBERSHIP_GET_SQL",
    "MEMBERSHIP_LIST_SQL",
    "MEMBERSHIP_PUT_SQL",
    "HumanAuthorizationError",
    "HumanAuthorizationReason",
    "HumanAuthorizationService",
]

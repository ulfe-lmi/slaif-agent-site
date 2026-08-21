"""Control-only semantic service for site membership and human authority."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

import asyncpg

from .catalog import ROLE_CEILINGS, ROLE_DEFAULTS, ROLE_LABELS
from .models import (
    CurrentHumanAuthority,
    CurrentHumanSite,
    HumanSiteContext,
    MembershipChange,
    MembershipRecord,
    PermissionCatalogRecord,
    RoleCatalogRecord,
)

AUTHORIZE_SQL = "SELECT * FROM control.slaif_human_authorize($1, $2, $3, $4)"
MEMBERSHIP_PUT_SQL = (
    "SELECT * FROM control.slaif_membership_put($1, $2, $3, $4, $5, $6, $7, $8)"
)
MEMBERSHIP_GET_SQL = "SELECT * FROM control.slaif_membership_get($1, $2)"
MEMBERSHIP_LIST_SQL = "SELECT * FROM control.slaif_membership_list($1)"
CATALOG_SQL = "SELECT * FROM control.slaif_human_rbac_catalog()"
CURRENT_HUMAN_SITES_SQL = "SELECT * FROM control.slaif_current_human_sites($1)"
CURRENT_HUMAN_AUTHORITY_SQL = (
    "SELECT * FROM control.slaif_current_human_authority($1, $2)"
)


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
        effective_delegation_ceiling=row[8],
        effective_permissions=frozenset(row[9]),
        platform_administrator=row[10],
        created_at=row[11],
        updated_at=row[12],
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

    async def current_human_sites(
        self, user_account_id: UUID
    ) -> tuple[CurrentHumanSite, ...]:
        rows = await self._fetch(CURRENT_HUMAN_SITES_SQL, user_account_id)
        return tuple(
            CurrentHumanSite(
                site_id=row[0],
                site_key=row[1],
                display_name=row[2],
                status=row[3],
                default_locale=row[4],
                canonical_revision=row[5],
                role_key=row[6],
                membership_version=row[7],
                explicit_delegation_ceiling=row[8],
                effective_delegation_ceiling=row[9],
                platform_administrator=row[10],
            )
            for row in rows
        )

    async def current_human_authority(
        self, user_account_id: UUID, site_id: UUID
    ) -> CurrentHumanAuthority:
        rows = await self._fetch(CURRENT_HUMAN_AUTHORITY_SQL, user_account_id, site_id)
        if not rows:
            raise HumanAuthorizationError(HumanAuthorizationReason.NOT_FOUND)
        row = rows[0]
        return CurrentHumanAuthority(
            site_id=row[0],
            site_key=row[1],
            display_name=row[2],
            status=row[3],
            default_locale=row[4],
            canonical_revision=row[5],
            role_key=row[6],
            membership_version=row[7],
            explicit_delegation_ceiling=row[8],
            effective_delegation_ceiling=row[9],
            effective_permissions=tuple(row[10]),
            platform_administrator=row[11],
        )

    def roles(self) -> tuple[RoleCatalogRecord, ...]:
        return tuple(
            RoleCatalogRecord(
                role_key=role_key,
                label=ROLE_LABELS[role_key],
                description=f"Built-in {ROLE_LABELS[role_key]} role.",
                default_delegation_ceiling=ceiling,
                default_permissions=tuple(sorted(ROLE_DEFAULTS[role_key])),
            )
            for role_key, ceiling in ROLE_CEILINGS.items()
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
        context, _record = await self._put_membership(
            actor_user_id, site_id, target_user_id, change
        )
        return context

    async def put_membership_record(
        self,
        actor_user_id: UUID,
        site_id: UUID,
        target_user_id: UUID,
        change: MembershipChange,
    ) -> MembershipRecord:
        """Mutate and read the resulting record under the same transaction locks."""

        _context, record = await self._put_membership(
            actor_user_id, site_id, target_user_id, change
        )
        return record

    async def _put_membership(
        self,
        actor_user_id: UUID,
        site_id: UUID,
        target_user_id: UUID,
        change: MembershipChange,
    ) -> tuple[HumanSiteContext, MembershipRecord]:
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
                    record_row = await connection.fetchrow(
                        MEMBERSHIP_GET_SQL, site_id, target_user_id
                    )
        except asyncio.CancelledError:
            raise
        except asyncpg.TransactionRollbackError:
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
        if row is None or record_row is None:
            raise HumanAuthorizationError(HumanAuthorizationReason.NOT_FOUND)
        return _context(row), _membership(record_row)


__all__ = [
    "AUTHORIZE_SQL",
    "CATALOG_SQL",
    "CURRENT_HUMAN_AUTHORITY_SQL",
    "CURRENT_HUMAN_SITES_SQL",
    "MEMBERSHIP_GET_SQL",
    "MEMBERSHIP_LIST_SQL",
    "MEMBERSHIP_PUT_SQL",
    "HumanAuthorizationError",
    "HumanAuthorizationReason",
    "HumanAuthorizationService",
]

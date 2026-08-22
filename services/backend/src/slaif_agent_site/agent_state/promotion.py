"""Workspace promotion using the COW foundation reviewer.

Architecture reference: ARCHITECTURE-for-agents.md §8 (workspace lifecycle,
freeze, review, promotion). Full acceptance commits all COW operations
atomically with conflict_policy="error" — no overwrite is ever exposed.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

import asyncpg

from slaif_agent_site.agent_state.foundation import (
    CowConflictError,
    PromotionResult,
    asyncpg_cow_reviewer,
)


class PromotionError(Exception):
    """Raised when a promotion cannot be completed safely."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


async def promote_workspace(
    pool: _Pool,
    session_id: UUID,
    schema: str = "content",
    *,
    acquire_timeout: float = 10.0,
) -> PromotionResult:
    """Promote a COW session's changes to canonical.

    Uses the foundation's ``asyncpg_cow_reviewer`` to atomically commit
    all pending operations. Raises :class:`PromotionError` on conflicts.
    """
    try:
        async with pool.acquire(timeout=acquire_timeout) as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                result = await reviewer.commit_session(session_id, schema=schema)
                return result
    except CowConflictError as exc:
        raise PromotionError(f"COW conflict during promotion: {exc}") from exc
    except asyncpg.PostgresError as exc:
        raise PromotionError(f"database error during promotion: {exc}") from exc


async def discard_workspace(
    pool: _Pool,
    session_id: UUID,
    schema: str = "content",
    *,
    acquire_timeout: float = 10.0,
) -> Any:
    """Discard a COW session's changes without promoting."""
    try:
        async with pool.acquire(timeout=acquire_timeout) as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                return await reviewer.discard_session(session_id, schema=schema)
    except asyncpg.PostgresError as exc:
        raise PromotionError(f"database error during discard: {exc}") from exc


async def get_conflicts(
    pool: _Pool,
    session_id: UUID,
    schema: str = "content",
) -> list[dict[str, Any]]:
    """Check for base-row conflicts before attempting promotion."""
    try:
        async with pool.acquire(timeout=5.0) as connection:
            async with asyncpg_cow_reviewer(connection) as reviewer:
                conflicts = await reviewer.conflicts(session_id, schema=schema)
                return [dict(c) for c in conflicts] if conflicts else []
    except asyncpg.PostgresError as exc:
        raise PromotionError(f"database error checking conflicts: {exc}") from exc

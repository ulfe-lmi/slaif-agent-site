"""Workspace reviewer surface using the COW foundation.

Architecture reference: ARCHITECTURE-for-agents.md §8 (workspace lifecycle,
freeze, review, promotion). The real human accept promotion path lives in
``review_worker.accept_job`` (083/1); ``promote_workspace`` was retired in
that increment (the accept job is the only promotion path).  The real
human discard path lives in ``review_worker.discard_job`` (083/2);
``discard_workspace`` was retired in that increment (the DISCARD job is
the only discard path).  Conflict inspection (``get_conflicts``) remains
for the 084 conflict-resolution increment.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

import asyncpg

from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
)


class PromotionError(Exception):
    """Raised when a promotion cannot be completed safely."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


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

"""Trusted pre-statement advisory lock helpers for active workspace writes."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from slaif_agent_site.agent_state.foundation import asyncpg_cow_session


async def acquire_workspace_structure_lock(
    connection: Any, *, workspace_id: UUID, site_id: UUID
) -> None:
    """Acquire lifecycle shared then site-structure exclusive authority."""

    await acquire_workspace_lifecycle_lock(connection, workspace_id=workspace_id)
    await connection.fetchval(
        "SELECT pg_advisory_xact_lock(hashtextextended($1,994))",
        f"{workspace_id}:{site_id}:page-structure",
    )


async def acquire_workspace_lifecycle_lock(
    connection: Any, *, workspace_id: UUID
) -> None:
    await connection.fetchval(
        "SELECT pg_advisory_xact_lock_shared(hashtextextended($1,280))",
        str(workspace_id),
    )


async def acquire_type_dependency_lock(
    connection: Any, *, workspace_id: UUID, type_id: UUID
) -> None:
    """Serialize a type with creation/deletion of its direct dependencies."""

    await acquire_workspace_lifecycle_lock(connection, workspace_id=workspace_id)
    await connection.fetchval(
        "SELECT pg_advisory_xact_lock(hashtextextended($1,994))",
        f"{workspace_id}:{type_id}:content-type-dependency",
    )


@asynccontextmanager
async def prelocked_cow_session(
    pool: Any,
    *,
    session_id: UUID,
    operation_id: UUID,
    site_id: UUID | None = None,
    type_id: UUID | None = None,
):
    """Hold session-level locks before the COW transaction takes its snapshot."""

    connection = await pool.acquire()
    locks: list[tuple[str, str]] = []
    try:
        await connection.fetchval(
            "SELECT pg_advisory_lock_shared(hashtextextended($1,280))",
            str(session_id),
        )
        locks.append(("shared", str(session_id)))
        if site_id is not None:
            await connection.fetchval(
                "SELECT pg_advisory_lock(hashtextextended($1,994))",
                f"{session_id}:{site_id}:page-structure",
            )
            locks.append(("exclusive", f"{session_id}:{site_id}:page-structure"))
        if type_id is not None:
            await connection.fetchval(
                "SELECT pg_advisory_lock(hashtextextended($1,994))",
                f"{session_id}:{type_id}:content-type-dependency",
            )
            locks.append(
                ("exclusive", f"{session_id}:{type_id}:content-type-dependency")
            )
        async with asyncpg_cow_session(
            connection, session_id=session_id, operation_id=operation_id
        ) as cow:
            yield cow
    finally:
        for mode, key in reversed(locks):
            function = (
                "pg_advisory_unlock_shared"
                if mode == "shared"
                else "pg_advisory_unlock"
            )
            await connection.fetchval(
                f"SELECT {function}(hashtextextended($1,{280 if mode == 'shared' else 994}))",
                key,
            )
        await pool.release(connection)

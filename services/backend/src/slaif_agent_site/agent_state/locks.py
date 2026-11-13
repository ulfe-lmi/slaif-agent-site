"""Trusted pre-statement advisory lock helpers for active workspace writes."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

import asyncpg

from slaif_agent_site.agent_state.foundation import asyncpg_cow_session

# Driver-level connection failures: client-side interface errors (a
# pool-auto-released proxy, a closing protocol) and the actual PostgreSQL
# connection-error branch of the driver (the backend died mid-flight,
# for example between a public usable-check and the awaited unlock or
# the foundation's cleanup).  Server-side PostgresErrors (constraint,
# aborted transaction, ...) are deliberately NOT in this set: on a live
# connection they are real failures that must stay visible.
_DRIVER_CONNECTION_ERRORS: tuple[type[BaseException], ...] = (
    asyncpg.InterfaceError,
    asyncpg.PostgresConnectionError,
    OSError,
)


def _connection_usable(connection: Any) -> bool:
    """Public-API liveness check for a pooled connection or its proxy.

    A dead backend, a closed protocol, or a proxy the pool has already
    auto-released all report unusable state; a released proxy raises
    ``InterfaceError`` on any method call, so the check itself never
    raises.
    """
    try:
        return not connection.is_closed()
    except _DRIVER_CONNECTION_ERRORS:
        return False


async def _release_prelocked_locks(
    connection: Any, locks: list[tuple[str, str]]
) -> None:
    """Release pre-statement session locks in reverse acquisition order.

    A live pooled connection keeps advisory session locks until explicit
    unlock, so an unlock failure on a connection that is still usable
    propagates: a live unlock failure must stay visible, not be turned
    into a silent success or a raw-ROLLBACK guess.  A connection that
    has actually died (backend terminated, protocol closed, holder
    already auto-released by the pool) needs no unlock: PostgreSQL
    released that backend's session locks at backend shutdown.  A
    driver-level connection error (interface or the driver's
    PostgreSQL connection-error branch) is therefore suppressed only
    when the connection's actual public state now proves it dead or
    released.
    """
    if not locks or not _connection_usable(connection):
        return
    for mode, key in reversed(locks):
        function = (
            "pg_advisory_unlock_shared" if mode == "shared" else "pg_advisory_unlock"
        )
        namespace = 280 if mode == "shared" else 994
        try:
            await connection.fetchval(
                f"SELECT {function}(hashtextextended($1,{namespace}))",
                key,
            )
        except _DRIVER_CONNECTION_ERRORS:
            if _connection_usable(connection):
                # Still usable: this is a live unlock failure, keep it
                # visible instead of assuming the locks were released.
                raise
            # The backend died while unlocking (including between the
            # check above and this await); PostgreSQL released that
            # backend's session locks at shutdown.
            return


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
) -> AsyncIterator[Any]:
    """Hold session-level locks before the COW transaction takes its snapshot.

    If the owned connection dies inside the scope (for example the
    backend is terminated mid-transaction), PostgreSQL releases that
    backend's session advisory locks at backend shutdown and the pool
    auto-releases the dead holder.  The body's own exception (or
    cancellation) is captured directly at the yield and restored, as
    that same object with its original cause preserved, when the public
    foundation's dead-connection cleanup raised a driver error instead;
    a still-usable connection is never re-masked.  The holder is always
    returned to the pool, and a release error on a connection that is
    still usable stays visible.
    """

    connection = await pool.acquire()
    locks: list[tuple[str, str]] = []
    body_error: BaseException | None = None
    body_cause: BaseException | None = None
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
        try:
            async with asyncpg_cow_session(
                connection, session_id=session_id, operation_id=operation_id
            ) as cow:
                try:
                    yield cow
                except BaseException as body_exc:
                    # Capture the exact object the body raised (or the
                    # cancellation that hit it) before the public
                    # foundation context exit can replace it.
                    body_error = body_exc
                    body_cause = body_exc.__cause__
                    raise
        except BaseException as masked:
            if body_error is None or body_error is masked:
                # No body failure, or the foundation propagated the
                # body exception itself: original behavior is correct.
                raise
            if _connection_usable(connection):
                # A usable connection cannot have lost its body error to
                # dead-connection cleanup; propagate the foundation's
                # error unchanged.
                raise
            if not isinstance(masked, _DRIVER_CONNECTION_ERRORS):
                # Only driver-level connection errors are known
                # dead-connection masks; never guess from other
                # exception types.
                raise
            # The public foundation's dead-connection cleanup raised a
            # driver error while exiting, masking the body's own
            # exception (or cancellation).  Re-raise the captured SAME
            # object from its saved original cause: the original cause
            # (including None) is preserved exactly, and the driver mask
            # stays recorded in the implicit re-raise context.
            raise body_error from body_cause

    finally:
        try:
            await _release_prelocked_locks(connection, locks)
        finally:
            # Always return the holder to the pool, even if unlock
            # cleanup raised.  Pool.release is a no-op when the pool has
            # already auto-released a dead holder; a release error on a
            # connection that is still usable must stay visible.
            try:
                await pool.release(connection)
            except _DRIVER_CONNECTION_ERRORS:
                if _connection_usable(connection):
                    raise

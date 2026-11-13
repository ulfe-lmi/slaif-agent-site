"""Cleanup and error-preservation contracts for the pre-locked COW session.

Pure fakes (no database): pin the dead-connection cleanup semantics of
``prelocked_cow_session`` - the body's own exception (or cancellation),
captured directly at the yield, is the only object ever restored, live
unlock failures and live release failures stay visible, dead-connection
driver errors are suppressed only with actual death proof, and the holder
is always returned to the pool exactly once.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from slaif_agent_site.agent_state import locks as agent_locks

Body = Callable[[str], Awaitable[None]]


class _FakeConnection:
    """Pooled connection stand-in with selectable live/closed/released state.

    ``mode``:
      - ``"live"``: usable protocol (default);
      - ``"closed"``: protocol closed, ``is_closed()`` reports True;
      - ``"released"``: pool auto-released the proxy, every method raises
        ``InterfaceError``.
    """

    def __init__(self, *, dies_on_unlock: bool = False) -> None:
        self.mode = "live"
        self.unlock_error: Exception | None = None
        self.dies_on_unlock = dies_on_unlock
        self.statements: list[tuple[str, tuple[Any, ...]]] = []

    def die(self, mode: str) -> None:
        self.mode = mode

    def is_closed(self) -> bool:
        if self.mode == "released":
            raise asyncpg.InterfaceError("connection is closed or has been released")
        return self.mode == "closed"

    async def fetchval(self, sql: str, *args: Any) -> Any:
        if self.mode != "live":
            raise asyncpg.InterfaceError("connection is closed or has been released")
        if self.dies_on_unlock and "unlock" in sql:
            self.die("released")
            raise asyncpg.InterfaceError("connection died while unlocking")
        self.statements.append((sql, args))
        if self.unlock_error is not None and "unlock" in sql:
            raise self.unlock_error
        return True


class _FakeCowSession:
    """Async CM emulating the public foundation COW session exit.

    The real SDK always re-raises the in-flight body exception; on a dead
    connection its cleanup raises a fresh driver error that replaces the
    in-flight one - modeled here as ``mask``.
    """

    def __init__(self, mask: BaseException | None) -> None:
        self._mask = mask

    async def __aenter__(self) -> str:
        return "cow-session"

    async def __aexit__(self, *_args: object) -> None:
        if self._mask is not None:
            raise self._mask


class _CowFactory:
    def __init__(self, mask: BaseException | None) -> None:
        self._mask = mask

    def __call__(
        self, connection: Any, *, session_id: UUID, operation_id: UUID
    ) -> _FakeCowSession:
        return _FakeCowSession(self._mask)


class _FakePool:
    def __init__(
        self,
        connection: _FakeConnection,
        release_error: Exception | None = None,
    ) -> None:
        self.connection = connection
        self.release_error = release_error
        self.release_calls = 0

    async def acquire(self) -> _FakeConnection:
        return self.connection

    async def release(self, connection: _FakeConnection) -> None:
        self.release_calls += 1
        if self.release_error is not None:
            raise self.release_error


def _patch_cow(monkeypatch: pytest.MonkeyPatch, mask: BaseException | None) -> None:
    monkeypatch.setattr(agent_locks, "asyncpg_cow_session", _CowFactory(mask))


async def _run(
    pool: _FakePool,
    body: Body,
    *,
    site_id: UUID | None = None,
    type_id: UUID | None = None,
) -> BaseException | None:
    try:
        async with agent_locks.prelocked_cow_session(
            pool,
            session_id=uuid4(),
            operation_id=uuid4(),
            site_id=site_id,
            type_id=type_id,
        ) as cow:
            await body(cow)
    except BaseException as exc:
        return exc
    return None


def test_connection_usable_reflects_actual_public_state() -> None:
    assert agent_locks._connection_usable(_FakeConnection()) is True
    closed = _FakeConnection()
    closed.die("closed")
    assert agent_locks._connection_usable(closed) is False
    released = _FakeConnection()
    released.die("released")
    assert agent_locks._connection_usable(released) is False


async def test_dead_connection_restores_the_body_error_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_cause = asyncpg.PostgresError("underlying failure")
    body_error = ValueError("body failed")
    body_error.__cause__ = original_cause
    body_error.__suppress_context__ = True
    mask = asyncpg.InterfaceError("dead proxy cleanup")
    connection = _FakeConnection()
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, mask)

    async def body(_cow: str) -> None:
        connection.die("released")
        raise body_error

    exc = await _run(pool, body)
    assert exc is body_error
    # The cleanup mask must not replace the body error's original cause.
    assert exc.__cause__ is original_cause
    assert exc.__suppress_context__ is True
    # The driver mask stays recorded as the re-raise context.
    assert exc.__context__ is mask
    assert pool.release_calls == 1
    # No unlock was attempted on the dead holder.
    assert not any("unlock" in sql for sql, _ in connection.statements)


async def test_dead_connection_restores_the_cancellation_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cancellation = asyncio.CancelledError()
    mask = asyncpg.InterfaceError("dead proxy cleanup")
    connection = _FakeConnection()
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, mask)

    async def body(_cow: str) -> None:
        connection.die("released")
        raise cancellation

    exc = await _run(pool, body)
    assert exc is cancellation
    assert isinstance(exc, asyncio.CancelledError)
    # Originally cause-less: the mask must not be installed as cause.
    assert exc.__cause__ is None
    assert exc.__context__ is mask
    assert pool.release_calls == 1


async def test_dead_connection_restores_body_postgres_error_with_original_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The body's own raw driver error (e.g. a constraint failure whose
    # backend then dies) must come back as the SAME object with its
    # original cause intact, masked by the actual connection-died error.
    original_cause = OSError("backend admin shutdown")
    body_error = asyncpg.PostgresError("body statement failed")
    body_error.__cause__ = original_cause
    body_error.__suppress_context__ = True
    mask = asyncpg.ConnectionDoesNotExistError()
    connection = _FakeConnection()
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, mask)

    async def body(_cow: str) -> None:
        connection.die("released")
        raise body_error

    exc = await _run(pool, body)
    assert exc is body_error
    assert exc.__cause__ is original_cause
    assert exc.__context__ is mask
    assert pool.release_calls == 1


async def test_live_connection_does_not_exist_error_on_unlock_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unlock_failure = asyncpg.ConnectionDoesNotExistError()
    connection = _FakeConnection()
    connection.unlock_error = unlock_failure
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        return None

    exc = await _run(pool, body)
    assert isinstance(exc, asyncpg.ConnectionDoesNotExistError)
    assert pool.release_calls == 1


async def test_dead_connection_suppresses_connection_error_on_unlock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Real typed fault with a death transition: the unlock raises the
    # actual connection-died error and the connection's public state now
    # proves unusable, so cleanup must settle silently.
    connection = _FakeConnection(dies_on_unlock=True)
    connection.unlock_error = asyncpg.ConnectionDoesNotExistError()
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        return None

    assert await _run(pool, body) is None
    assert connection.mode == "released"
    assert pool.release_calls == 1


async def test_live_connection_propagates_foundation_error_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body_error = ValueError("body failed")
    mask = asyncpg.InterfaceError("foundation cleanup on live connection")
    connection = _FakeConnection()
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, mask)

    async def body(_cow: str) -> None:
        raise body_error

    exc = await _run(pool, body)
    # Live connection: the foundation's error is genuine; the body error
    # must not be substituted for it.
    assert exc is mask
    assert pool.release_calls == 1
    assert "pg_advisory_unlock_shared" in connection.statements[-1][0]


async def test_live_unlock_failure_propagates_and_holder_still_released(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unlock_failure = OSError("unlock failed")
    connection = _FakeConnection()
    connection.unlock_error = unlock_failure
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        return None

    exc = await _run(pool, body)
    assert exc is unlock_failure
    assert pool.release_calls == 1


async def test_live_postgres_error_on_unlock_propagates_without_rollback_guess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = asyncpg.PostgresError("current transaction is aborted")
    connection = _FakeConnection()
    connection.unlock_error = failure
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        return None

    exc = await _run(pool, body)
    assert exc is failure
    assert pool.release_calls == 1
    # The removed blanket fallback must not issue raw ROLLBACK guesses.
    assert not any("ROLLBACK" in sql for sql, _ in connection.statements)


async def test_dead_connection_suppresses_unlock_error_with_death_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _FakeConnection(dies_on_unlock=True)
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        return None

    assert await _run(pool, body) is None
    assert connection.mode == "released"
    assert pool.release_calls == 1


async def test_release_failure_on_live_connection_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_failure = asyncpg.InterfaceError("pool closed during release")
    connection = _FakeConnection()
    pool = _FakePool(connection, release_error=release_failure)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        return None

    exc = await _run(pool, body)
    assert exc is release_failure
    assert pool.release_calls == 1


async def test_release_failure_on_released_connection_is_suppressed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    release_failure = asyncpg.InterfaceError("holder already released")
    connection = _FakeConnection()
    pool = _FakePool(connection, release_error=release_failure)
    _patch_cow(monkeypatch, None)

    async def body(_cow: str) -> None:
        connection.die("released")

    assert await _run(pool, body) is None
    assert pool.release_calls == 1


async def test_normal_exit_unlocks_in_reverse_order_and_releases_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = _FakeConnection()
    pool = _FakePool(connection)
    _patch_cow(monkeypatch, None)
    site_id = uuid4()
    type_id = uuid4()

    async def body(_cow: str) -> None:
        return None

    assert await _run(pool, body, site_id=site_id, type_id=type_id) is None
    assert pool.release_calls == 1
    sqls = [sql for sql, _ in connection.statements]
    assert sqls[0].startswith("SELECT pg_advisory_lock_shared")
    assert "pg_advisory_lock" in sqls[1] and "shared" not in sqls[1]
    assert "pg_advisory_lock" in sqls[2] and "shared" not in sqls[2]
    # Reverse acquisition order: type dependency, site, session.
    assert "pg_advisory_unlock" in sqls[3] and "shared" not in sqls[3]
    assert "pg_advisory_unlock" in sqls[4] and "shared" not in sqls[4]
    assert sqls[5].startswith("SELECT pg_advisory_unlock_shared")
    keys = [args[0] for _, args in connection.statements]
    session_key = keys[0]
    assert keys[1] == f"{session_key}:{site_id}:page-structure"
    assert keys[2] == f"{session_key}:{type_id}:content-type-dependency"
    assert keys[3:] == list(reversed(keys[:3]))


async def test_release_helper_skips_dead_connection_without_statements() -> None:
    connection = _FakeConnection()
    connection.die("released")
    await agent_locks._release_prelocked_locks(
        connection, [("shared", "s"), ("exclusive", "x")]
    )
    assert connection.statements == []


async def test_release_helper_live_unlock_error_propagates() -> None:
    connection = _FakeConnection()
    connection.unlock_error = OSError("boom")
    with pytest.raises(OSError, match="boom"):
        await agent_locks._release_prelocked_locks(
            connection, [("shared", "s"), ("exclusive", "x")]
        )


async def test_release_helper_suppresses_death_mid_unlock() -> None:
    connection = _FakeConnection(dies_on_unlock=True)
    # Must not raise: the connection's actual public state proves death.
    await agent_locks._release_prelocked_locks(
        connection, [("shared", "s"), ("exclusive", "x")]
    )
    assert connection.mode == "released"

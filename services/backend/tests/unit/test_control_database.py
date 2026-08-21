"""Bounded Control pool lifecycle, identity, and readiness unit contracts."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type
from pydantic import SecretStr
from slaif_agent_site.bootstrap.setup_token import (
    digest_setup_token,
    generate_setup_token,
)
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import (
    INITIAL_SETUP_COMPLETE_SQL,
    INITIAL_SETUP_LOCK_SQL,
    READINESS_SQL,
    ControlDatabase,
    ControlDatabaseReason,
    InitialSetupError,
)
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.identity.models import InitialLocalAdministratorRequest
from slaif_agent_site.identity.passwords import PasswordService


def _settings(**updates: object) -> ControlDatabaseSettings:
    values: dict[str, object] = {
        "mode": ControlDatabaseMode.TEST,
        "dsn": SecretStr(
            "postgresql://slaif_control_login:fake-control-password@"
            "example.test:5432/slaif"
        ),
        "dsn_file": None,
        "pool_min_size": 1,
        "pool_max_size": 2,
        "shutdown_timeout_seconds": 0.1,
    }
    values.update(updates)
    return ControlDatabaseSettings.model_validate(values)


class FakeConnection:
    def __init__(
        self,
        *,
        database: str = "slaif",
        login: str = "slaif_control_login",
        roles: tuple[str, ...] = ("slaif_control",),
        readiness_row: tuple[object, ...] | None = (
            "013_001",
            "013_001",
            "EMPTY_SAFE",
            True,
            "agent-cow-postgresql",
            "0.2.0",
        ),
        setup_lock_row: tuple[object, ...] | None = None,
        setup_complete_row: tuple[object, ...] | None = None,
    ) -> None:
        self.database = database
        self.login = login
        self.roles = roles
        self.readiness_row = readiness_row
        self.setup_lock_row = setup_lock_row
        self.setup_complete_row = setup_complete_row
        self.queries: list[str] = []
        self.arguments: list[tuple[object, ...]] = []
        self.transactions = 0

    async def fetchrow(self, query: str, *arguments: object) -> Any:
        self.queries.append(query)
        self.arguments.append(arguments)
        if query == READINESS_SQL:
            return self.readiness_row
        if query == INITIAL_SETUP_LOCK_SQL:
            return self.setup_lock_row
        if query == INITIAL_SETUP_COMPLETE_SQL:
            return self.setup_complete_row
        return (self.database, self.login, self.login, list(self.roles))

    def transaction(self) -> FakeTransaction:
        return FakeTransaction(self)


class FakeTransaction:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> None:
        self.connection.transactions += 1

    async def __aexit__(self, *_arguments: object) -> None:
        self.connection.transactions -= 1


class FakeAcquire:
    def __init__(self, pool: FakePool) -> None:
        self.pool = pool

    async def __aenter__(self) -> FakeConnection:
        if self.pool.acquire_error is not None:
            raise self.pool.acquire_error
        self.pool.acquired += 1
        return self.pool.connection

    async def __aexit__(self, *_arguments: object) -> None:
        self.pool.released += 1


class FakePool:
    def __init__(
        self,
        connection: FakeConnection,
        *,
        acquire_error: BaseException | None = None,
        block_close: bool = False,
    ) -> None:
        self.connection = connection
        self.acquire_error = acquire_error
        self.block_close = block_close
        self.acquired = 0
        self.released = 0
        self.closed = False
        self.terminated = False

    def acquire(self, *, timeout: float) -> FakeAcquire:
        assert timeout > 0
        return FakeAcquire(self)

    async def close(self) -> None:
        if self.block_close:
            await asyncio.Event().wait()
        self.closed = True

    def terminate(self) -> None:
        self.terminated = True


def _pool_factory(
    connection: FakeConnection,
    pool: FakePool,
    captured: dict[str, object],
) -> Callable[..., Awaitable[Any]]:
    async def create(**kwargs: object) -> FakePool:
        captured.update(kwargs)
        initializer = kwargs["init"]
        assert callable(initializer)
        await initializer(connection)
        return pool

    return create


async def test_pool_is_bounded_initialized_once_and_closed_cleanly() -> None:
    connection = FakeConnection()
    pool = FakePool(connection)
    captured: dict[str, object] = {}
    database = ControlDatabase(
        _settings(),
        pool_factory=_pool_factory(connection, pool, captured),
    )

    await database.start()
    assert await database.readiness() == await _ready_result()
    assert captured["min_size"] == 1
    assert captured["max_size"] == 2
    assert captured["timeout"] == 3.0
    assert captured["command_timeout"] == 2.0
    assert captured["max_inactive_connection_lifetime"] == 60.0
    assert captured["server_settings"] == {
        "application_name": "slaif-control-api",
        "statement_timeout": "2000",
        "lock_timeout": "500",
        "idle_in_transaction_session_timeout": "2000",
    }
    assert set(captured) == {
        "dsn",
        "min_size",
        "max_size",
        "timeout",
        "command_timeout",
        "max_inactive_connection_lifetime",
        "server_settings",
        "init",
    }
    assert connection.queries[0].startswith("SELECT current_database()")
    assert connection.queries[1] == READINESS_SQL
    assert pool.acquired == pool.released == 1

    await database.stop()
    assert pool.closed
    stopped = await database.readiness()
    assert stopped.reason == ControlDatabaseReason.SHUTDOWN.value


def _setup_password_service() -> PasswordService:
    return PasswordService(
        PasswordHasher(
            time_cost=1,
            memory_cost=8,
            parallelism=1,
            hash_len=16,
            salt_len=8,
            type=Type.ID,
        )
    )


def _setup_request(token: SecretStr) -> InitialLocalAdministratorRequest:
    return InitialLocalAdministratorRequest(
        username="Local.Admin",
        password=SecretStr("fixture-" + "p" * 20),
        display_name="Local Administrator",
        email="admin@example.test",
        setup_token=token,
    )


async def test_initial_setup_is_one_semantic_transaction_without_raw_surface() -> None:
    token = generate_setup_token(lambda size: bytes([19]) * size)
    user_id = UUID("00000000-0000-4000-8000-000000000019")
    now = datetime.now(UTC)
    connection = FakeConnection(
        setup_lock_row=(
            False,
            now + timedelta(minutes=30),
            1,
            digest_setup_token(token),
        ),
        setup_complete_row=(
            user_id,
            "Local.Admin",
            "Local Administrator",
            "admin@example.test",
            "ACTIVE",
            now,
        ),
    )
    pool = FakePool(connection)
    database = ControlDatabase(
        _settings(),
        pool_factory=_pool_factory(connection, pool, {}),
        password_service=_setup_password_service(),
        uuid_factory=lambda: user_id,
    )
    await database.start()
    request = _setup_request(token)
    result = await database.create_initial_local_administrator(request)
    assert result.user_account_id == user_id
    assert result.username == "Local.Admin"
    assert "password" not in result.model_dump_json()
    assert "digest" not in result.model_dump_json()
    assert connection.transactions == 0
    assert connection.queries[-2:] == [
        INITIAL_SETUP_LOCK_SQL,
        INITIAL_SETUP_COMPLETE_SQL,
    ]
    completion_arguments = connection.arguments[-1]
    assert completion_arguments[0] == 1
    assert completion_arguments[1] == digest_setup_token(token)
    assert request.password.get_secret_value() not in repr(completion_arguments)
    assert request.setup_token.get_secret_value() not in repr(completion_arguments)
    assert not hasattr(database, "execute") and not hasattr(database, "fetch")


async def test_initial_setup_wrong_token_uses_one_constant_failure() -> None:
    stored = generate_setup_token(lambda size: bytes([20]) * size)
    presented = generate_setup_token(lambda size: bytes([21]) * size)
    connection = FakeConnection(
        setup_lock_row=(
            False,
            datetime.now(UTC) + timedelta(minutes=30),
            1,
            digest_setup_token(stored),
        )
    )
    pool = FakePool(connection)
    database = ControlDatabase(
        _settings(),
        pool_factory=_pool_factory(connection, pool, {}),
        password_service=_setup_password_service(),
    )
    await database.start()
    with pytest.raises(InitialSetupError) as context:
        await database.create_initial_local_administrator(_setup_request(presented))
    assert str(context.value) == "Initial setup failed."
    assert INITIAL_SETUP_COMPLETE_SQL not in connection.queries
    assert connection.transactions == 0


async def _ready_result() -> Any:
    from slaif_agent_site.health import ProbeResult

    return ProbeResult.ready()


@pytest.mark.parametrize(
    ("connection", "reason"),
    (
        (FakeConnection(database="wrong"), ControlDatabaseReason.IDENTITY_MISMATCH),
        (FakeConnection(login="wrong"), ControlDatabaseReason.IDENTITY_MISMATCH),
        (FakeConnection(roles=()), ControlDatabaseReason.ROLE_MISMATCH),
        (
            FakeConnection(roles=("slaif_control", "slaif_owner")),
            ControlDatabaseReason.ROLE_MISMATCH,
        ),
        (
            FakeConnection(roles=("slaif_agent_runtime", "slaif_control")),
            ControlDatabaseReason.ROLE_MISMATCH,
        ),
        (
            FakeConnection(roles=("slaif_control", "slaif_reviewer")),
            ControlDatabaseReason.ROLE_MISMATCH,
        ),
    ),
)
async def test_new_connection_identity_and_exact_role_are_fail_closed(
    connection: FakeConnection,
    reason: ControlDatabaseReason,
) -> None:
    pool = FakePool(connection)
    database = ControlDatabase(
        _settings(), pool_factory=_pool_factory(connection, pool, {})
    )
    await database.start()
    result = await database.readiness()
    assert result.reason == reason.value
    assert pool.acquired == pool.released == 0


@pytest.mark.parametrize(
    ("row", "reason"),
    (
        (None, ControlDatabaseReason.UNSAFE_MARKER),
        (
            ("006_001", "013_001", "EMPTY_SAFE", True, "agent-cow-postgresql", "0.2.0"),
            ControlDatabaseReason.MIGRATION_MISMATCH,
        ),
        (
            ("013_001", "006_001", "EMPTY_SAFE", True, "agent-cow-postgresql", "0.2.0"),
            ControlDatabaseReason.MIGRATION_MISMATCH,
        ),
        (
            ("013_001", "013_001", "PENDING", False, "agent-cow-postgresql", "0.2.0"),
            ControlDatabaseReason.UNSAFE_MARKER,
        ),
        (
            ("013_001", "013_001", "EMPTY_SAFE", True, "other", "0.2.0"),
            ControlDatabaseReason.FOUNDATION_MISMATCH,
        ),
        (
            ("013_001", "013_001", "HARDENED", True, "agent-cow-postgresql", "0.1.0"),
            ControlDatabaseReason.FOUNDATION_MISMATCH,
        ),
    ),
)
async def test_readiness_rows_return_only_stable_bounded_reasons(
    row: tuple[object, ...] | None,
    reason: ControlDatabaseReason,
) -> None:
    connection = FakeConnection(readiness_row=row)
    pool = FakePool(connection)
    database = ControlDatabase(
        _settings(), pool_factory=_pool_factory(connection, pool, {})
    )
    await database.start()
    result = await database.readiness()
    assert result.reason == reason.value
    await database.stop()


async def test_startup_acquire_timeout_and_close_timeout_are_sanitized() -> None:
    async def unavailable_factory(**_kwargs: object) -> Any:
        raise OSError("postgresql://must:not@escape.example/slaif")

    unavailable = ControlDatabase(_settings(), pool_factory=unavailable_factory)
    await unavailable.start()
    result = await unavailable.readiness()
    assert result.reason == ControlDatabaseReason.CONNECTION_UNAVAILABLE.value
    assert "postgresql" not in repr(result)

    connection = FakeConnection()
    timeout_pool = FakePool(connection, acquire_error=TimeoutError())
    timeout = ControlDatabase(
        _settings(), pool_factory=_pool_factory(connection, timeout_pool, {})
    )
    await timeout.start()
    assert (await timeout.readiness()).reason == ControlDatabaseReason.TIMEOUT.value
    await timeout.stop()

    blocking_pool = FakePool(connection, block_close=True)
    blocking = ControlDatabase(
        _settings(), pool_factory=_pool_factory(connection, blocking_pool, {})
    )
    await blocking.start()
    await blocking.stop()
    assert blocking_pool.terminated


async def test_start_cancellation_propagates_and_leaves_shutdown_state() -> None:
    async def cancelled_factory(**_kwargs: object) -> Any:
        raise asyncio.CancelledError

    database = ControlDatabase(_settings(), pool_factory=cancelled_factory)
    with pytest.raises(asyncio.CancelledError):
        await database.start()
    assert (await database.readiness()).reason == ControlDatabaseReason.SHUTDOWN.value


def test_adapter_exposes_no_native_pool_or_sql_locator() -> None:
    public = {name for name in dir(ControlDatabase) if not name.startswith("_")}
    assert public == {
        "create_initial_local_administrator",
        "authenticate_local_login",
        "authorize_platform_administrator",
        "human_session_service",
        "site_service",
        "setup_status",
        "readiness",
        "start",
        "stop",
    }
    assert not ({"native", "pool", "execute", "fetch", "sql"} & public)
    assert set(ROLE_NAMES) >= {
        "slaif_owner",
        "slaif_control",
        "slaif_editor_runtime",
        "slaif_agent_runtime",
        "slaif_reviewer",
    }

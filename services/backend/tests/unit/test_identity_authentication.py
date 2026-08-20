"""Unit contracts for local credential verification secrecy and denials."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import SecretStr
from slaif_agent_site.identity.authentication import (
    DUMMY_LOCAL_PASSWORD_HASH,
    LOOKUP_LOCAL_LOGIN_SQL,
    LocalAuthenticationError,
    LocalAuthenticationService,
    LocalLoginRequest,
)
from slaif_agent_site.identity.passwords import PasswordService


class SpyHasher:
    def __init__(self, *, result: bool = True) -> None:
        self.result = result
        self.verified: list[str] = []

    def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
        return "replacement"

    def verify(self, encoded: str | bytes, password: str | bytes) -> bool:
        self.verified.append(str(encoded))
        return self.result

    def check_needs_rehash(self, encoded: str | bytes) -> bool:
        return False


class Acquire:
    def __init__(self, connection: object) -> None:
        self.connection = connection

    async def __aenter__(self) -> object:
        return self.connection

    async def __aexit__(self, *_args: object) -> None:
        return None


class Connection:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row
        self.queries: list[str] = []

    async def fetchrow(self, query: str, *_args: object) -> tuple[object, ...] | None:
        self.queries.append(query)
        return self.row


class Pool:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def acquire(self, *, timeout: float) -> Acquire:
        return Acquire(self.connection)


@pytest.mark.asyncio
async def test_unknown_login_executes_fixed_dummy_verifier() -> None:
    spy = SpyHasher()
    connection = Connection(None)
    service = LocalAuthenticationService(
        Pool(connection), password_service=PasswordService(spy)
    )

    with pytest.raises(LocalAuthenticationError, match="^Local login failed\\.$"):
        await service.authenticate(
            LocalLoginRequest(username="unknown.user", password=SecretStr("password"))
        )

    assert connection.queries == [LOOKUP_LOCAL_LOGIN_SQL]
    assert spy.verified == [DUMMY_LOCAL_PASSWORD_HASH]


@pytest.mark.asyncio
async def test_valid_login_returns_minimal_identity_without_hash() -> None:
    user_id = uuid4()
    spy = SpyHasher()
    connection = Connection(
        (user_id, "local.user", DUMMY_LOCAL_PASSWORD_HASH, "ACTIVE")
    )
    service = LocalAuthenticationService(
        Pool(connection), password_service=PasswordService(spy)
    )

    result = await service.authenticate(
        LocalLoginRequest(username="LOCAL.USER", password=SecretStr("password"))
    )

    assert result.user_account_id == user_id
    assert result.username == "local.user"
    assert result.rehashed is False
    assert "password_hash" not in result.model_dump_json().casefold()
    assert spy.verified == [DUMMY_LOCAL_PASSWORD_HASH]

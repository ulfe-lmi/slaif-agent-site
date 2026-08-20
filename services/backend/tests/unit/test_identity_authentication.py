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
    def __init__(self, *, result: bool = True, needs_rehash: bool = False) -> None:
        self.result = result
        self.needs_rehash = needs_rehash
        self.verified: list[str] = []
        self.hashed: list[str] = []

    def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
        self.hashed.append(str(password))
        return DUMMY_LOCAL_PASSWORD_HASH

    def verify(self, encoded: str | bytes, password: str | bytes) -> bool:
        self.verified.append(str(encoded))
        return self.result

    def check_needs_rehash(self, encoded: str | bytes) -> bool:
        return self.needs_rehash


class Acquire:
    def __init__(self, connection: object) -> None:
        self.connection = connection

    async def __aenter__(self) -> object:
        return self.connection

    async def __aexit__(self, *_args: object) -> None:
        return None


class Connection:
    def __init__(
        self,
        row: tuple[object, ...] | None,
        *,
        cas_result: bool = True,
        error: BaseException | None = None,
    ) -> None:
        self.row = row
        self.cas_result = cas_result
        self.error = error
        self.queries: list[str] = []
        self.cas_arguments: tuple[object, ...] | None = None

    async def fetchrow(self, query: str, *_args: object) -> tuple[object, ...] | None:
        self.queries.append(query)
        if self.error is not None:
            raise self.error
        return self.row

    async def fetchval(self, query: str, *args: object) -> bool:
        self.queries.append(query)
        self.cas_arguments = args
        return self.cas_result


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
@pytest.mark.parametrize(
    "row",
    [
        (uuid4(), "disabled.user", DUMMY_LOCAL_PASSWORD_HASH, "DISABLED"),
        (uuid4(), "oidc.user", None, "ACTIVE"),
        (uuid4(), "broken.user", "not-an-argon2-hash", "ACTIVE"),
        (uuid4(), None, DUMMY_LOCAL_PASSWORD_HASH, "ACTIVE"),
    ],
)
async def test_invalid_candidates_use_dummy_and_constant_failure(
    row: tuple[object, ...],
) -> None:
    spy = SpyHasher()
    service = LocalAuthenticationService(
        Pool(Connection(row)), password_service=PasswordService(spy)
    )

    with pytest.raises(LocalAuthenticationError, match="^Local login failed\\.$"):
        await service.authenticate(
            LocalLoginRequest(username="candidate.user", password=SecretStr("password"))
        )

    assert spy.verified == [DUMMY_LOCAL_PASSWORD_HASH]


@pytest.mark.asyncio
async def test_rehash_success_uses_exact_old_and_new_values() -> None:
    user_id = uuid4()
    spy = SpyHasher(needs_rehash=True)
    connection = Connection(
        (user_id, "local.user", DUMMY_LOCAL_PASSWORD_HASH, "ACTIVE")
    )
    service = LocalAuthenticationService(
        Pool(connection), password_service=PasswordService(spy)
    )

    result = await service.authenticate(
        LocalLoginRequest(
            username="local.user", password=SecretStr("verified-password")
        )
    )

    assert result.rehashed is True
    assert spy.hashed == ["verified-password"]
    assert connection.cas_arguments == (
        user_id,
        DUMMY_LOCAL_PASSWORD_HASH,
        DUMMY_LOCAL_PASSWORD_HASH,
    )


@pytest.mark.asyncio
async def test_rehash_cas_miss_and_lookup_failure_are_constant_denials() -> None:
    user_id = uuid4()
    spy = SpyHasher(needs_rehash=True)
    cas_miss = Connection(
        (user_id, "local.user", DUMMY_LOCAL_PASSWORD_HASH, "ACTIVE"), cas_result=False
    )
    service = LocalAuthenticationService(
        Pool(cas_miss), password_service=PasswordService(spy)
    )
    with pytest.raises(LocalAuthenticationError, match="^Local login failed\\.$"):
        await service.authenticate(
            LocalLoginRequest(username="local.user", password=SecretStr("verified"))
        )
    failure = Connection(None, error=RuntimeError("private driver detail"))
    failing = LocalAuthenticationService(
        Pool(failure), password_service=PasswordService(SpyHasher())
    )
    with pytest.raises(LocalAuthenticationError, match="^Local login failed\\.$"):
        await failing.authenticate(
            LocalLoginRequest(username="local.user", password=SecretStr("verified"))
        )


def test_login_request_excludes_password_from_repr_and_serialization() -> None:
    request = LocalLoginRequest(
        username="local.user", password=SecretStr("plaintext-not-output")
    )

    assert "plaintext-not-output" not in repr(request)
    assert "plaintext-not-output" not in str(request)
    assert "password" not in request.model_dump()
    assert "password" not in request.model_dump_json()


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

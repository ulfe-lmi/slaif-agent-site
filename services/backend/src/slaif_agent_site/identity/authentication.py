"""Control-only local credential verification and safe password rehashing."""

from __future__ import annotations

import asyncio
import re
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from .models import IdentityInputError, normalize_local_username
from .passwords import PasswordService

LOCAL_LOGIN_FAILURE = "Local login failed."
DUMMY_LOCAL_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$Mx0/HcGuBz/Q2ZbIZ3ApcA$"
    "pXULL7WDerETM/dh0aQBWX+e01uHaWdl1BDILcX3OLU"
)
LOCAL_HASH_PATTERN = re.compile(
    r"\A\$argon2id\$v=19\$m=65536,t=3,p=4\$[A-Za-z0-9+/]{22}\$[A-Za-z0-9+/]{43}\Z"
)
LOOKUP_LOCAL_LOGIN_SQL = (
    "SELECT user_account_id, local_username_normalized, password_hash, status "
    'FROM "control"."slaif_lookup_local_login"($1)'
)
CAS_LOCAL_PASSWORD_HASH_SQL = (
    'SELECT "control"."slaif_compare_and_set_local_password_hash"($1, $2, $3)'
)


class LocalLoginRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    username: str
    password: SecretStr

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        try:
            return normalize_local_username(value)
        except IdentityInputError:
            raise ValueError("invalid local login input") from None


class LocalAuthenticationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    user_account_id: UUID
    username: str
    rehashed: bool


class LocalAuthenticationError(RuntimeError):
    """One external-safe denial for every local credential failure."""

    def __init__(self) -> None:
        super().__init__(LOCAL_LOGIN_FAILURE)


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


class LocalAuthenticationService:
    """Verify local credentials using only the Control pool and functions."""

    def __init__(
        self,
        pool: _Pool,
        *,
        acquire_timeout: float = 3.0,
        password_service: PasswordService | None = None,
    ) -> None:
        self._pool = pool
        self._acquire_timeout = acquire_timeout
        self._password_service = password_service or PasswordService()

    async def _lookup(self, username: str) -> Any:
        async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
            return await connection.fetchrow(LOOKUP_LOCAL_LOGIN_SQL, username)

    async def _compare_and_set(
        self, user_id: UUID, expected: SecretStr, replacement: SecretStr
    ) -> bool:
        async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
            return bool(
                await connection.fetchval(
                    CAS_LOCAL_PASSWORD_HASH_SQL,
                    user_id,
                    expected.get_secret_value(),
                    replacement.get_secret_value(),
                )
            )

    async def authenticate(
        self, request: LocalLoginRequest
    ) -> LocalAuthenticationResult:
        candidate: Any = None
        try:
            candidate = await self._lookup(request.username)
            valid_candidate = (
                candidate is not None
                and candidate[0] is not None
                and candidate[1] == request.username
                and candidate[2] is not None
                and isinstance(candidate[2], str)
                and LOCAL_HASH_PATTERN.fullmatch(candidate[2]) is not None
                and candidate[3] == "ACTIVE"
            )
            encoded = (
                SecretStr(candidate[2])
                if valid_candidate
                else SecretStr(DUMMY_LOCAL_PASSWORD_HASH)
            )
            verified = self._password_service.verify_password(encoded, request.password)
            if not valid_candidate or not verified:
                raise LocalAuthenticationError()
            rehashed = False
            if self._password_service.check_needs_rehash(encoded):
                replacement = self._password_service.hash_for_rehash(request.password)
                if not await self._compare_and_set(candidate[0], encoded, replacement):
                    raise LocalAuthenticationError()
                rehashed = True
            return LocalAuthenticationResult(
                user_account_id=candidate[0], username=candidate[1], rehashed=rehashed
            )
        except asyncio.CancelledError:
            raise
        except LocalAuthenticationError:
            raise
        except Exception:
            if candidate is None:
                self._password_service.verify_password(
                    SecretStr(DUMMY_LOCAL_PASSWORD_HASH), request.password
                )
            raise LocalAuthenticationError() from None


__all__ = [
    "CAS_LOCAL_PASSWORD_HASH_SQL",
    "DUMMY_LOCAL_PASSWORD_HASH",
    "LOCAL_LOGIN_FAILURE",
    "LOOKUP_LOCAL_LOGIN_SQL",
    "LocalAuthenticationError",
    "LocalAuthenticationResult",
    "LocalAuthenticationService",
    "LocalLoginRequest",
]

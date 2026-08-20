"""Opaque human-session credentials, policy, and Control adapter."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

import asyncpg
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

SESSION_VERSION = "sas2"
SESSION_PUBLIC_ID_PATTERN = re.compile(r"^sas2_[0-9a-f]{32}$")
_SESSION_SECRET_BYTES = 32
_CSRF_SECRET_BYTES = 32
_B64_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


class SessionCredentialError(ValueError):
    """A stable malformed/invalid credential error without credential data."""

    def __init__(self) -> None:
        super().__init__("Invalid session credential.")


class HumanSessionError(RuntimeError):
    """A constant external-safe session failure."""

    def __init__(self) -> None:
        super().__init__("Human session unavailable.")


class HumanSessionPolicy(BaseModel):
    """Bounded database-clock session and recent-auth policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    idle_timeout_seconds: int = Field(default=1800, ge=2, le=86400)
    absolute_lifetime_seconds: int = Field(default=28800, ge=3, le=604800)
    recent_auth_window_seconds: int = Field(default=900, ge=1, le=604800)
    touch_interval_seconds: int = Field(default=300, ge=1, le=86400)

    def validate_ordering(self) -> HumanSessionPolicy:
        if not (
            0
            < self.touch_interval_seconds
            < self.idle_timeout_seconds
            < self.absolute_lifetime_seconds
            and 0 < self.recent_auth_window_seconds <= self.absolute_lifetime_seconds
        ):
            raise ValueError("session timeout ordering is invalid")
        return self


@dataclass(frozen=True, slots=True)
class SessionCookiePolicy:
    """Cookie attributes for future HTTP handlers; no response is emitted here."""

    name: str
    http_only: bool
    secure: bool
    same_site: str
    path: str
    domain: str | None
    max_age_seconds: int

    def __post_init__(self) -> None:
        if (
            not self.http_only
            or self.same_site not in {"lax", "strict"}
            or self.path != "/"
            or self.domain is not None
            or self.max_age_seconds <= 0
        ):
            raise ValueError("session cookie policy is invalid")
        if self.secure and not self.name.startswith("__Host-"):
            raise ValueError("secure session cookies require __Host- semantics")


def session_cookie_policy(
    *, production: bool, policy: HumanSessionPolicy
) -> SessionCookiePolicy:
    """Return the production `__Host-` or development-local cookie contract."""

    policy.validate_ordering()
    return SessionCookiePolicy(
        name="__Host-slaif_session" if production else "slaif_session",
        http_only=True,
        secure=production,
        same_site="lax",
        path="/",
        domain=None,
        max_age_seconds=policy.absolute_lifetime_seconds,
    )


def _encode_secret(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_secret(value: str) -> bytes:
    if not _B64_PATTERN.fullmatch(value):
        raise SessionCredentialError()
    try:
        decoded = base64.urlsafe_b64decode(value + "=")
    except (binascii.Error, ValueError, UnicodeError):
        raise SessionCredentialError() from None
    if len(decoded) != _SESSION_SECRET_BYTES:
        raise SessionCredentialError()
    return decoded


def digest_secret(secret: bytes) -> bytes:
    """Hash one boundary-only secret; only this digest reaches PostgreSQL."""

    if len(secret) != _SESSION_SECRET_BYTES:
        raise SessionCredentialError()
    return hashlib.sha256(secret).digest()


def constant_time_digest_equal(left: bytes, right: bytes) -> bool:
    """Compare fixed-size digests with the standard constant-time primitive."""

    return secrets.compare_digest(left, right)


def make_session_public_id(*, id_factory: Any = uuid4) -> str:
    value = id_factory()
    if not isinstance(value, UUID):
        raise SessionCredentialError()
    return f"{SESSION_VERSION}_{value.hex}"


def format_session_token(public_id: str, secret: bytes) -> SecretStr:
    if SESSION_PUBLIC_ID_PATTERN.fullmatch(public_id) is None:
        raise SessionCredentialError()
    if len(secret) != _SESSION_SECRET_BYTES:
        raise SessionCredentialError()
    return SecretStr(
        f"{SESSION_VERSION}_session_{public_id.removeprefix('sas2_')}_{_encode_secret(secret)}"
    )


def parse_session_token(token: SecretStr | str) -> tuple[str, bytes]:
    value = token.get_secret_value() if isinstance(token, SecretStr) else token
    parts = value.split("_")
    if len(parts) != 4 or parts[0] != SESSION_VERSION or parts[1] != "session":
        raise SessionCredentialError()
    public_id = f"{SESSION_VERSION}_{parts[2]}"
    if SESSION_PUBLIC_ID_PATTERN.fullmatch(public_id) is None:
        raise SessionCredentialError()
    return public_id, _decode_secret(parts[3])


def format_csrf_token(secret: bytes) -> SecretStr:
    if len(secret) != _CSRF_SECRET_BYTES:
        raise SessionCredentialError()
    return SecretStr(f"{SESSION_VERSION}_csrf_{_encode_secret(secret)}")


def parse_csrf_token(token: SecretStr | str) -> bytes:
    value = token.get_secret_value() if isinstance(token, SecretStr) else token
    parts = value.split("_")
    if len(parts) != 3 or parts[:2] != [SESSION_VERSION, "csrf"]:
        raise SessionCredentialError()
    return _decode_secret(parts[2])


class SessionDatabase(Protocol):
    async def fetchrow(self, query: str, *args: object) -> asyncpg.Record | None: ...

    async def execute(self, query: str, *args: object) -> str: ...


@dataclass(frozen=True, slots=True)
class IssuedHumanSession:
    session_id: UUID
    public_id: str
    token: SecretStr
    csrf_token: SecretStr
    created_at: datetime
    last_seen_at: datetime
    absolute_expires_at: datetime
    recent_auth_at: datetime

    def __repr__(self) -> str:
        return (
            "IssuedHumanSession(session_id=... , public_id=... , token=<redacted>, "
            "csrf_token=<redacted>, created_at=..., last_seen_at=..., "
            "absolute_expires_at=..., recent_auth_at=...)"
        )


@dataclass(frozen=True, slots=True)
class HumanSessionContext:
    session_id: UUID
    user_account_id: UUID
    public_id: str
    recent_auth: bool
    last_seen_at: datetime
    absolute_expires_at: datetime


class HumanSessionService:
    """Control-only semantic session service over the three owner functions."""

    def __init__(
        self,
        pool: Any,
        *,
        policy: HumanSessionPolicy | None = None,
        random_bytes: Any = secrets.token_bytes,
        id_factory: Any = uuid4,
    ) -> None:
        self._pool = pool
        self._policy = (policy or HumanSessionPolicy()).validate_ordering()
        self._random_bytes = random_bytes
        self._id_factory = id_factory

    def _secret(self, size: int) -> bytes:
        value = self._random_bytes(size)
        if not isinstance(value, bytes) or len(value) != size:
            raise HumanSessionError()
        return value

    async def create(self, user_account_id: UUID) -> IssuedHumanSession:
        """Create only for a trusted already-authenticated active user."""

        if not isinstance(user_account_id, UUID):
            raise HumanSessionError()
        session_id = self._id_factory()
        if not isinstance(session_id, UUID):
            raise HumanSessionError()
        secret = self._secret(_SESSION_SECRET_BYTES)
        csrf_secret = self._secret(_CSRF_SECRET_BYTES)
        public_id = make_session_public_id(id_factory=lambda: session_id)
        try:
            async with self._pool.acquire() as connection:
                row = await connection.fetchrow(
                    'SELECT * FROM "control"."slaif_create_human_session"('
                    "$1, $2, $3, $4, $5, $6, $7, $8)",
                    session_id,
                    public_id,
                    digest_secret(secret),
                    digest_secret(csrf_secret),
                    user_account_id,
                    self._policy.idle_timeout_seconds,
                    self._policy.absolute_lifetime_seconds,
                    self._policy.recent_auth_window_seconds,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise HumanSessionError() from None
        if row is None:
            raise HumanSessionError()
        return IssuedHumanSession(
            session_id=row[0],
            public_id=row[1],
            token=format_session_token(public_id, secret),
            csrf_token=format_csrf_token(csrf_secret),
            created_at=row[2],
            last_seen_at=row[3],
            absolute_expires_at=row[4],
            recent_auth_at=row[5],
        )

    async def resolve(
        self, token: SecretStr | str, csrf_token: SecretStr | str
    ) -> HumanSessionContext:
        """Resolve both credentials and return only minimal trusted context."""

        try:
            public_id, secret = parse_session_token(token)
            csrf_secret = parse_csrf_token(csrf_token)
            async with self._pool.acquire() as connection:
                row = await connection.fetchrow(
                    'SELECT * FROM "control"."slaif_resolve_human_session"('
                    "$1, $2, $3, $4, $5, $6)",
                    public_id,
                    digest_secret(secret),
                    digest_secret(csrf_secret),
                    self._policy.idle_timeout_seconds,
                    self._policy.touch_interval_seconds,
                    self._policy.recent_auth_window_seconds,
                )
        except (SessionCredentialError, ValidationError):
            raise HumanSessionError() from None
        except asyncio.CancelledError:
            raise
        except Exception:
            raise HumanSessionError() from None
        if row is None:
            raise HumanSessionError()
        return HumanSessionContext(
            session_id=row[0],
            user_account_id=row[1],
            public_id=row[2],
            recent_auth=bool(row[3]),
            last_seen_at=row[4],
            absolute_expires_at=row[5],
        )

    async def revoke(self, token: SecretStr | str) -> None:
        """Revoke idempotently; malformed/unknown credentials fail closed."""

        try:
            public_id, secret = parse_session_token(token)
            async with self._pool.acquire() as connection:
                await connection.fetchval(
                    'SELECT "control"."slaif_revoke_human_session"($1, $2)',
                    public_id,
                    digest_secret(secret),
                )
        except SessionCredentialError:
            raise HumanSessionError() from None
        except asyncio.CancelledError:
            raise
        except Exception:
            raise HumanSessionError() from None


__all__ = [
    "HumanSessionContext",
    "HumanSessionError",
    "HumanSessionPolicy",
    "HumanSessionService",
    "IssuedHumanSession",
    "SESSION_VERSION",
    "SessionCookiePolicy",
    "SessionCredentialError",
    "constant_time_digest_equal",
    "digest_secret",
    "format_csrf_token",
    "format_session_token",
    "make_session_public_id",
    "parse_csrf_token",
    "parse_session_token",
    "session_cookie_policy",
]

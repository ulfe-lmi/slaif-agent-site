"""Typed Media database and private-store configuration."""

from __future__ import annotations

import os
import re
import stat
from enum import StrEnum
from pathlib import Path
from typing import Self
from urllib.parse import parse_qsl, unquote, urlsplit

from pydantic import Field, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MEDIA_LOGIN = "slaif_media_login"
MEDIA_PRIVILEGE_ROLE = "slaif_media"
MEDIA_DSN_FILE = Path("/run/slaif-media/media-dsn")
MEDIA_APPLICATION_NAME = "slaif-media-service"
MEDIA_ROOT = Path("/var/lib/slaif/media")
_ERROR = "Invalid SLAIF Media configuration."


class MediaDatabaseMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class MediaDatabaseConfigurationError(RuntimeError):
    """A constant failure without locator or storage details."""


class MediaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SLAIF_MEDIA_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        frozen=True,
        validate_default=True,
    )

    mode: MediaDatabaseMode = MediaDatabaseMode.DEVELOPMENT
    dsn: SecretStr | None = None
    dsn_file: Path | None = MEDIA_DSN_FILE
    expected_database: str = "slaif"
    expected_login: str = MEDIA_LOGIN
    expected_privilege_role: str = MEDIA_PRIVILEGE_ROLE
    pool_min_size: int = Field(default=1, ge=1, le=4)
    pool_max_size: int = Field(default=4, ge=1, le=16)
    acquire_timeout_seconds: float = Field(default=1.5, ge=0.05, le=10)
    command_timeout_seconds: float = Field(default=2, ge=0.05, le=30)
    connect_timeout_seconds: float = Field(default=3, ge=0.05, le=30)
    shutdown_timeout_seconds: float = Field(default=5, ge=0.1, le=30)
    max_inactive_connection_lifetime_seconds: float = Field(default=60, ge=1, le=900)
    statement_timeout_ms: int = Field(default=5000, ge=50, le=30000)
    lock_timeout_ms: int = Field(default=1000, ge=10, le=10000)
    idle_transaction_timeout_ms: int = Field(default=5000, ge=50, le=30000)
    media_root: Path = MEDIA_ROOT
    max_upload_bytes: int = Field(default=100 * 1024 * 1024, ge=1, le=500 * 1024 * 1024)
    application_name: str = MEDIA_APPLICATION_NAME

    @field_validator("dsn_file", "media_root")
    @classmethod
    def absolute_path(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("Media paths must be absolute")
        return value

    @field_validator("expected_database", "expected_login", "expected_privilege_role")
    @classmethod
    def identity(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
            raise ValueError("Media database identity is invalid")
        return value

    @field_validator("application_name")
    @classmethod
    def application_name_value(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", value):
            raise ValueError("Media application name is invalid")
        return value

    @model_validator(mode="after")
    def boundary(self) -> Self:
        if self.pool_min_size > self.pool_max_size:
            raise ValueError("Media pool bounds are invalid")
        if (
            self.dsn is not None
            and self.dsn_file is not None
            and self.mode is not MediaDatabaseMode.TEST
        ):
            raise ValueError("configure one Media database locator source")
        if self.mode is MediaDatabaseMode.TEST:
            if self.dsn is None and self.dsn_file is None:
                raise ValueError("test mode requires one Media database locator")
        elif self.dsn is not None or self.dsn_file is None:
            raise ValueError("Media database locator must use a mounted file")
        if self.expected_privilege_role != MEDIA_PRIVILEGE_ROLE:
            raise ValueError("Media privilege role is fixed")
        if (
            self.mode is not MediaDatabaseMode.TEST
            and self.expected_login != MEDIA_LOGIN
        ):
            raise ValueError("Media identity must use the fixed authority")
        return self

    def _read_file(self, path: Path) -> str:
        try:
            info = path.stat(follow_symlinks=False)
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o400
                or info.st_uid != os.geteuid()
            ):
                raise ValueError
            value = path.read_text(encoding="ascii")
        except (OSError, UnicodeError, ValueError):
            raise MediaDatabaseConfigurationError(_ERROR) from None
        if not value or "\n" in value or "\r" in value:
            raise MediaDatabaseConfigurationError(_ERROR)
        return value

    def _validate_locator(self, value: str) -> SecretStr:
        try:
            parsed = urlsplit(value)
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            query = dict(pairs)
            if (
                parsed.scheme not in {"postgres", "postgresql"}
                or not parsed.hostname
                or unquote(parsed.username or "") != self.expected_login
                or not parsed.password
                or unquote(parsed.path.removeprefix("/")) != self.expected_database
                or parsed.fragment
                or parsed.port not in {None, 5432}
                or len(query) != len(pairs)
                or set(query) - {"sslmode", "sslrootcert", "target_session_attrs"}
            ):
                raise ValueError
            if query.get("target_session_attrs") not in {None, "read-write"}:
                raise ValueError
            if self.mode is MediaDatabaseMode.PRODUCTION:
                if (
                    query.get("sslmode") != "verify-full"
                    or query.get("target_session_attrs") != "read-write"
                    or not Path(query.get("sslrootcert", "")).is_absolute()
                ):
                    raise ValueError
            elif query.get("sslmode") not in {None, "disable"}:
                raise ValueError
            if (
                self.mode is MediaDatabaseMode.DEVELOPMENT
                and parsed.hostname != "postgres"
            ):
                raise ValueError
            if self.mode is MediaDatabaseMode.TEST and self.dsn is not None:
                host = parsed.hostname.casefold()
                if host not in {"127.0.0.1", "::1", "localhost"} and not host.endswith(
                    ".test"
                ):
                    raise ValueError
        except (TypeError, ValueError):
            raise MediaDatabaseConfigurationError(_ERROR) from None
        return SecretStr(value)

    def resolved_dsn(self) -> SecretStr:
        if self.dsn is not None:
            value = self.dsn.get_secret_value()
        elif self.dsn_file is not None:
            value = self._read_file(self.dsn_file)
        else:
            raise MediaDatabaseConfigurationError(_ERROR)
        return self._validate_locator(value)

    @property
    def server_settings(self) -> dict[str, str]:
        return {
            "application_name": self.application_name,
            "statement_timeout": str(self.statement_timeout_ms),
            "lock_timeout": str(self.lock_timeout_ms),
            "idle_in_transaction_session_timeout": str(
                self.idle_transaction_timeout_ms
            ),
        }

    @classmethod
    def load(cls) -> Self:
        try:
            return cls()
        except (OSError, ValidationError, ValueError):
            raise MediaDatabaseConfigurationError(_ERROR) from None


__all__ = [
    "MEDIA_APPLICATION_NAME",
    "MEDIA_DSN_FILE",
    "MEDIA_LOGIN",
    "MEDIA_PRIVILEGE_ROLE",
    "MEDIA_ROOT",
    "MediaDatabaseConfigurationError",
    "MediaDatabaseMode",
    "MediaSettings",
]

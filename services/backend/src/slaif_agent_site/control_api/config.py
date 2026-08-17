"""Typed, secret-safe database settings owned only by the Control API."""

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

CONTROL_LOGIN = "slaif_control_login"
CONTROL_PRIVILEGE_ROLE = "slaif_control"
CONTROL_DSN_FILE = Path("/run/slaif-control/control-dsn")
CONTROL_APPLICATION_NAME = "slaif-control-api"
_CONSTANT_ERROR = "Invalid SLAIF Control database configuration."


class ControlDatabaseMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class ControlDatabaseConfigurationError(RuntimeError):
    """A constant configuration failure that never contains locator material."""


class ControlDatabaseSettings(BaseSettings):
    """Frozen settings for the Control API's one database authority."""

    model_config = SettingsConfigDict(
        env_prefix="SLAIF_CONTROL_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        frozen=True,
        validate_default=True,
    )

    mode: ControlDatabaseMode = ControlDatabaseMode.DEVELOPMENT
    dsn: SecretStr | None = None
    dsn_file: Path | None = CONTROL_DSN_FILE
    expected_database: str = "slaif"
    expected_login: str = CONTROL_LOGIN
    expected_privilege_role: str = CONTROL_PRIVILEGE_ROLE
    pool_min_size: int = Field(default=1, ge=1, le=4)
    pool_max_size: int = Field(default=4, ge=1, le=16)
    acquire_timeout_seconds: float = Field(default=1.5, ge=0.05, le=10.0)
    command_timeout_seconds: float = Field(default=2.0, ge=0.05, le=30.0)
    connect_timeout_seconds: float = Field(default=3.0, ge=0.05, le=30.0)
    shutdown_timeout_seconds: float = Field(default=5.0, ge=0.1, le=30.0)
    max_inactive_connection_lifetime_seconds: float = Field(
        default=60.0, ge=1.0, le=900.0
    )
    statement_timeout_ms: int = Field(default=2000, ge=50, le=30000)
    lock_timeout_ms: int = Field(default=500, ge=10, le=10000)
    idle_transaction_timeout_ms: int = Field(default=2000, ge=50, le=30000)
    application_name: str = CONTROL_APPLICATION_NAME

    @field_validator("dsn_file")
    @classmethod
    def validate_absolute_file(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("Control database file must be absolute")
        return value

    @field_validator("expected_database", "expected_login", "expected_privilege_role")
    @classmethod
    def validate_identity(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
            raise ValueError("Control database identity is invalid")
        return value

    @field_validator("application_name")
    @classmethod
    def validate_application_name(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", value):
            raise ValueError("Control application name is invalid")
        return value

    @model_validator(mode="after")
    def validate_boundary(self) -> Self:
        if self.pool_min_size > self.pool_max_size:
            raise ValueError("Control pool bounds are invalid")
        if (
            self.dsn is not None
            and self.dsn_file is not None
            and not (
                self.mode is ControlDatabaseMode.TEST
                and self.dsn_file == CONTROL_DSN_FILE
            )
        ):
            raise ValueError("configure one Control database locator source")
        if self.mode is ControlDatabaseMode.TEST:
            if self.dsn is None and self.dsn_file is None:
                raise ValueError("test mode requires one Control database locator")
        elif self.dsn is not None or self.dsn_file is None:
            raise ValueError("Control database locator must use a mounted file")
        if self.mode is not ControlDatabaseMode.TEST and (
            self.expected_login != CONTROL_LOGIN
            or self.expected_privilege_role != CONTROL_PRIVILEGE_ROLE
        ):
            raise ValueError("Control database identity must use the fixed authority")
        if self.expected_privilege_role != CONTROL_PRIVILEGE_ROLE:
            raise ValueError("Control privilege role is fixed")
        return self

    def _read_locator_file(self, path: Path) -> str:
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
            raise ControlDatabaseConfigurationError(_CONSTANT_ERROR) from None
        if not value or "\n" in value or "\r" in value:
            raise ControlDatabaseConfigurationError(_CONSTANT_ERROR)
        return value

    def _validate_locator(self, value: str) -> SecretStr:
        try:
            parsed = urlsplit(value)
            query = dict(parse_qsl(parsed.query, keep_blank_values=True))
            if (
                parsed.scheme not in {"postgres", "postgresql"}
                or not parsed.hostname
                or unquote(parsed.username or "") != self.expected_login
                or not parsed.password
                or unquote(parsed.path.removeprefix("/")) != self.expected_database
                or parsed.fragment
                or parsed.port not in {None, 5432}
                or len(query) != len(parse_qsl(parsed.query, keep_blank_values=True))
            ):
                raise ValueError
            allowed_query = {"sslmode", "sslrootcert", "target_session_attrs"}
            if set(query) - allowed_query:
                raise ValueError
            target_session = query.get("target_session_attrs")
            if target_session not in {None, "read-write"}:
                raise ValueError
            if self.mode is ControlDatabaseMode.PRODUCTION:
                root_certificate = query.get("sslrootcert", "")
                if (
                    query.get("sslmode") != "verify-full"
                    or target_session != "read-write"
                    or not Path(root_certificate).is_absolute()
                ):
                    raise ValueError
            elif query.get("sslmode") not in {None, "disable"}:
                raise ValueError
            if (
                self.mode is ControlDatabaseMode.DEVELOPMENT
                and parsed.hostname != "postgres"
            ):
                raise ValueError
            if self.mode is ControlDatabaseMode.TEST and self.dsn is not None:
                host = parsed.hostname.casefold()
                if host not in {"127.0.0.1", "::1", "localhost"} and not host.endswith(
                    ".test"
                ):
                    raise ValueError
        except (TypeError, ValueError):
            raise ControlDatabaseConfigurationError(_CONSTANT_ERROR) from None
        return SecretStr(value)

    def resolved_dsn(self) -> SecretStr:
        """Resolve and validate one locator without exposing it in failures."""

        try:
            value = (
                self.dsn.get_secret_value()
                if self.dsn is not None
                else self._read_locator_file(self.dsn_file)  # type: ignore[arg-type]
            )
            return self._validate_locator(value)
        except ControlDatabaseConfigurationError:
            raise
        except (OSError, TypeError, ValueError):
            raise ControlDatabaseConfigurationError(_CONSTANT_ERROR) from None

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
            raise ControlDatabaseConfigurationError(_CONSTANT_ERROR) from None


__all__ = [
    "CONTROL_APPLICATION_NAME",
    "CONTROL_DSN_FILE",
    "CONTROL_LOGIN",
    "CONTROL_PRIVILEGE_ROLE",
    "ControlDatabaseConfigurationError",
    "ControlDatabaseMode",
    "ControlDatabaseSettings",
]

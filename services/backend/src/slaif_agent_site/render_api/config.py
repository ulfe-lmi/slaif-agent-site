"""Typed, secret-safe database settings owned only by Render."""

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

RENDER_LOGIN = "slaif_public_login"
RENDER_PRIVILEGE_ROLE = "slaif_public_reader"
RENDER_DSN_FILE = Path("/run/slaif-render/render-dsn")
RENDER_PREVIEW_LOGIN = "slaif_preview_login"
RENDER_PREVIEW_PRIVILEGE_ROLE = "slaif_preview_reader"
RENDER_PREVIEW_DSN_FILE = Path("/run/slaif-render-preview/preview-dsn")
RENDER_SERVICE_TOKEN_FILE = Path("/run/slaif-render-auth/render-token")
RENDER_APPLICATION_NAME = "slaif-render-api"
_ERROR = "Invalid SLAIF Render database configuration."


class RenderDatabaseMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class RenderDatabaseConfigurationError(RuntimeError):
    """A constant failure which never contains database locator material."""


class RenderDatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SLAIF_RENDER_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        frozen=True,
        validate_default=True,
    )

    mode: RenderDatabaseMode = RenderDatabaseMode.DEVELOPMENT
    dsn: SecretStr | None = None
    dsn_file: Path | None = RENDER_DSN_FILE
    preview_dsn: SecretStr | None = None
    preview_dsn_file: Path | None = RENDER_PREVIEW_DSN_FILE
    service_token: SecretStr | None = None
    service_token_file: Path | None = RENDER_SERVICE_TOKEN_FILE
    expected_database: str = "slaif"
    expected_login: str = RENDER_LOGIN
    expected_privilege_role: str = RENDER_PRIVILEGE_ROLE
    preview_expected_login: str = RENDER_PREVIEW_LOGIN
    preview_expected_privilege_role: str = RENDER_PREVIEW_PRIVILEGE_ROLE
    pool_min_size: int = Field(default=1, ge=1, le=4)
    pool_max_size: int = Field(default=4, ge=1, le=16)
    acquire_timeout_seconds: float = Field(default=1.5, ge=0.05, le=10)
    command_timeout_seconds: float = Field(default=2, ge=0.05, le=30)
    connect_timeout_seconds: float = Field(default=3, ge=0.05, le=30)
    shutdown_timeout_seconds: float = Field(default=5, ge=0.1, le=30)
    max_inactive_connection_lifetime_seconds: float = Field(default=60, ge=1, le=900)
    statement_timeout_ms: int = Field(default=2000, ge=50, le=30000)
    lock_timeout_ms: int = Field(default=500, ge=10, le=10000)
    idle_transaction_timeout_ms: int = Field(default=2000, ge=50, le=30000)
    preview_idle_timeout_seconds: int = Field(default=1800, ge=2, le=86400)
    preview_touch_interval_seconds: int = Field(default=300, ge=1, le=86400)
    preview_recent_auth_seconds: int = Field(default=900, ge=1, le=604800)
    application_name: str = RENDER_APPLICATION_NAME

    @field_validator("dsn_file", "preview_dsn_file", "service_token_file")
    @classmethod
    def absolute_file(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("Render database file must be absolute")
        return value

    @field_validator(
        "expected_database",
        "expected_login",
        "expected_privilege_role",
        "preview_expected_login",
        "preview_expected_privilege_role",
    )
    @classmethod
    def identity(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
            raise ValueError("Render database identity is invalid")
        return value

    @model_validator(mode="after")
    def boundary(self) -> Self:
        if self.pool_min_size > self.pool_max_size:
            raise ValueError("Render pool bounds are invalid")
        if (
            self.dsn is not None
            and self.dsn_file is not None
            and not (
                self.mode is RenderDatabaseMode.TEST
                and self.dsn_file == RENDER_DSN_FILE
            )
        ):
            raise ValueError("configure one Render database locator source")
        if self.mode is RenderDatabaseMode.TEST:
            if self.dsn is None and self.dsn_file is None:
                raise ValueError("test mode requires one Render database locator")
        elif self.dsn is not None or self.dsn_file is None:
            raise ValueError("Render database locator must use a mounted file")
        if self.preview_dsn is not None and self.preview_dsn_file is not None:
            if not (
                self.mode is RenderDatabaseMode.TEST
                and self.preview_dsn_file == RENDER_PREVIEW_DSN_FILE
            ):
                raise ValueError("configure one preview database locator source")
        if self.mode is RenderDatabaseMode.TEST:
            if self.preview_dsn is not None and self.preview_dsn_file is None:
                raise ValueError("preview test locator must use one source")
        elif self.preview_dsn is not None or self.preview_dsn_file is None:
            raise ValueError("preview database locator must use a mounted file")
        if self.service_token is not None and self.service_token_file is not None:
            if not (
                self.mode is RenderDatabaseMode.TEST
                and self.service_token_file == RENDER_SERVICE_TOKEN_FILE
            ):
                raise ValueError("configure one Render service credential source")
        if self.mode is RenderDatabaseMode.PRODUCTION and (
            self.service_token is None and self.service_token_file is None
        ):
            raise ValueError("Render service credential must use a mounted file")
        if self.expected_privilege_role != RENDER_PRIVILEGE_ROLE:
            raise ValueError("Render privilege role is fixed")
        if self.preview_expected_login != RENDER_PREVIEW_LOGIN:
            raise ValueError("Render preview identity is fixed")
        if self.preview_expected_privilege_role != RENDER_PREVIEW_PRIVILEGE_ROLE:
            raise ValueError("Render preview role is fixed")
        if (
            self.mode is not RenderDatabaseMode.TEST
            and self.expected_login != RENDER_LOGIN
        ):
            raise ValueError("Render database identity must use the fixed authority")
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
            raise RenderDatabaseConfigurationError(_ERROR) from None
        if not value or "\n" in value or "\r" in value:
            raise RenderDatabaseConfigurationError(_ERROR)
        return value

    def _validate_locator(
        self, value: str, *, expected_login: str | None = None
    ) -> SecretStr:
        login = expected_login or self.expected_login
        try:
            parsed = urlsplit(value)
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            query = dict(pairs)
            if (
                parsed.scheme not in {"postgres", "postgresql"}
                or not parsed.hostname
                or unquote(parsed.username or "") != login
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
            if self.mode is RenderDatabaseMode.PRODUCTION:
                if (
                    query.get("sslmode") != "verify-full"
                    or query.get("target_session_attrs") != "read-write"
                    or not Path(query.get("sslrootcert", "")).is_absolute()
                ):
                    raise ValueError
            elif query.get("sslmode") not in {None, "disable"}:
                raise ValueError
            if (
                self.mode is RenderDatabaseMode.DEVELOPMENT
                and parsed.hostname != "postgres"
            ):
                raise ValueError
            if self.mode is RenderDatabaseMode.TEST and self.dsn is not None:
                host = parsed.hostname.casefold()
                if host not in {"127.0.0.1", "::1", "localhost"} and not host.endswith(
                    ".test"
                ):
                    raise ValueError
        except (TypeError, ValueError):
            raise RenderDatabaseConfigurationError(_ERROR) from None
        return SecretStr(value)

    def resolved_dsn(self) -> SecretStr:
        if self.dsn is not None:
            value = self.dsn.get_secret_value()
        else:
            if self.dsn_file is None:
                raise RenderDatabaseConfigurationError(_ERROR)
            value = self._read_file(self.dsn_file)
        return self._validate_locator(value)

    def resolved_preview_dsn(self) -> SecretStr:
        if self.preview_dsn is not None:
            value = self.preview_dsn.get_secret_value()
        else:
            if self.preview_dsn_file is None:
                raise RenderDatabaseConfigurationError(_ERROR)
            value = self._read_file(self.preview_dsn_file)
        return self._validate_locator(value, expected_login=RENDER_PREVIEW_LOGIN)

    def resolved_service_token(self) -> SecretStr | None:
        if self.service_token is not None:
            value = self.service_token.get_secret_value()
        elif self.service_token_file is not None:
            value = self._read_file(self.service_token_file)
        else:
            return None
        try:
            directory = (
                self.service_token_file.parent if self.service_token_file else None
            )
            if directory is None:
                raise ValueError
            info = directory.stat(follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
                raise ValueError
            if info.st_uid != os.geteuid():
                raise ValueError
        except (OSError, ValueError):
            raise RenderDatabaseConfigurationError(_ERROR) from None
        if len(value) < 32 or len(value) > 256 or any(char.isspace() for char in value):
            raise RenderDatabaseConfigurationError(_ERROR)
        return SecretStr(value)

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
            raise RenderDatabaseConfigurationError(_ERROR) from None

"""Typed, secret-safe database settings owned only by Agent API."""

from __future__ import annotations

import os
import re
import stat
from enum import StrEnum
from pathlib import Path
from typing import Self
from urllib.parse import parse_qsl, unquote, urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

AGENT_LOGIN = "slaif_agent_login"
AGENT_PRIVILEGE_ROLE = "slaif_agent_runtime"
AGENT_DSN_FILE = Path("/run/slaif-agent/agent-dsn")
AGENT_BROWSER_SIGNING_KEY_FILE = Path("/run/slaif-browser-signing/signing-key")
AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE = Path(
    "/run/slaif-browser-worker/worker-token"
)
AGENT_APPLICATION_NAME = "slaif-agent-api"
_ERROR = "Invalid SLAIF Agent database configuration."


class AgentDatabaseMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class AgentDatabaseConfigurationError(RuntimeError):
    """A constant failure which never contains database locator material."""


class AgentDispatcherSettings(BaseModel):
    """Bounded settings for the Agent-owned browser dispatcher."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = True
    poll_interval_seconds: float = Field(default=0.5, ge=0.05, le=10)
    backoff_seconds: float = Field(default=2, ge=0.1, le=30)
    lease_seconds: int = Field(default=30, ge=1, le=60)
    renewal_interval_seconds: float = Field(default=10, ge=0.1, le=59)
    worker_timeout_seconds: float = Field(default=120, ge=5, le=120)
    concurrency: int = Field(default=1, ge=1, le=2)
    shutdown_timeout_seconds: float = Field(default=5, ge=0.1, le=30)

    @model_validator(mode="after")
    def bounded_lifecycle(self) -> Self:
        if self.renewal_interval_seconds >= self.lease_seconds:
            raise ValueError("Agent dispatcher renewal interval must be below lease")
        return self


class AgentDatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SLAIF_AGENT_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        frozen=True,
        validate_default=True,
    )

    mode: AgentDatabaseMode = AgentDatabaseMode.DEVELOPMENT
    dsn: SecretStr | None = None
    dsn_file: Path | None = AGENT_DSN_FILE
    browser_signing_key_file: Path = AGENT_BROWSER_SIGNING_KEY_FILE
    browser_worker_service_credential_file: Path = (
        AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE
    )
    browser_worker_endpoint: str = "http://browser-worker:3100"
    expected_database: str = "slaif"
    expected_login: str = AGENT_LOGIN
    expected_privilege_role: str = AGENT_PRIVILEGE_ROLE
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
    application_name: str = AGENT_APPLICATION_NAME
    dispatcher_enabled: bool = True
    dispatcher_poll_interval_seconds: float = Field(default=0.5, ge=0.05, le=10)
    dispatcher_backoff_seconds: float = Field(default=2, ge=0.1, le=30)
    dispatcher_lease_seconds: int = Field(default=30, ge=1, le=60)
    dispatcher_renewal_interval_seconds: float = Field(default=10, ge=0.1, le=59)
    dispatcher_worker_timeout_seconds: float = Field(default=120, ge=5, le=120)
    dispatcher_concurrency: int = Field(default=1, ge=1, le=2)
    dispatcher_shutdown_timeout_seconds: float = Field(default=5, ge=0.1, le=30)

    @field_validator(
        "dsn_file",
        "browser_signing_key_file",
        "browser_worker_service_credential_file",
    )
    @classmethod
    def absolute_file(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("Agent database file must be absolute")
        return value

    @field_validator("expected_database", "expected_login", "expected_privilege_role")
    @classmethod
    def identity(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
            raise ValueError("Agent database identity is invalid")
        return value

    @field_validator("application_name")
    @classmethod
    def application_name_value(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", value):
            raise ValueError("Agent application name is invalid")
        return value

    @model_validator(mode="after")
    def boundary(self) -> Self:
        if self.pool_min_size > self.pool_max_size:
            raise ValueError("Agent pool bounds are invalid")
        if (
            self.dsn is not None
            and self.dsn_file is not None
            and self.mode is not AgentDatabaseMode.TEST
        ):
            raise ValueError("configure one Agent database locator source")
        if self.mode is AgentDatabaseMode.TEST:
            if self.dsn is None and self.dsn_file is None:
                raise ValueError("test mode requires one Agent database locator")
        elif self.dsn is not None or self.dsn_file is None:
            raise ValueError("Agent database locator must use a mounted file")
        if self.expected_privilege_role != AGENT_PRIVILEGE_ROLE:
            raise ValueError("Agent privilege role is fixed")
        if (
            self.mode is not AgentDatabaseMode.TEST
            and self.expected_login != AGENT_LOGIN
        ):
            raise ValueError("Agent database identity must use the fixed authority")
        endpoint = urlsplit(self.browser_worker_endpoint)
        if (
            endpoint.scheme != "http"
            or endpoint.username
            or endpoint.password
            or endpoint.path not in {"", "/"}
            or endpoint.query
            or endpoint.fragment
            or endpoint.port != 3100
            or endpoint.hostname is None
            or self.mode is not AgentDatabaseMode.TEST
            and endpoint.hostname != "browser-worker"
            or self.mode is AgentDatabaseMode.TEST
            and endpoint.hostname != "browser-worker"
            and not endpoint.hostname.endswith(".test")
        ):
            raise ValueError("Agent browser worker endpoint is fixed")
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
            raise AgentDatabaseConfigurationError(_ERROR) from None
        if not value or "\n" in value or "\r" in value:
            raise AgentDatabaseConfigurationError(_ERROR)
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
            if self.mode is AgentDatabaseMode.PRODUCTION:
                if (
                    query.get("sslmode") != "verify-full"
                    or query.get("target_session_attrs") != "read-write"
                    or not Path(query.get("sslrootcert", "")).is_absolute()
                ):
                    raise ValueError
            elif query.get("sslmode") not in {None, "disable"}:
                raise ValueError
            if (
                self.mode is AgentDatabaseMode.DEVELOPMENT
                and parsed.hostname != "postgres"
            ):
                raise ValueError
            if self.mode is AgentDatabaseMode.TEST and self.dsn is not None:
                host = parsed.hostname.casefold()
                if host not in {"127.0.0.1", "::1", "localhost"} and not host.endswith(
                    ".test"
                ):
                    raise ValueError
        except (TypeError, ValueError):
            raise AgentDatabaseConfigurationError(_ERROR) from None
        return SecretStr(value)

    def resolved_dsn(self) -> SecretStr:
        value = (
            self.dsn.get_secret_value()
            if self.dsn is not None
            else self._read_file(self.dsn_file)  # type: ignore[arg-type]
        )
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

    @property
    def dispatcher_settings(self) -> AgentDispatcherSettings:
        return AgentDispatcherSettings(
            enabled=self.dispatcher_enabled,
            poll_interval_seconds=self.dispatcher_poll_interval_seconds,
            backoff_seconds=self.dispatcher_backoff_seconds,
            lease_seconds=self.dispatcher_lease_seconds,
            renewal_interval_seconds=self.dispatcher_renewal_interval_seconds,
            worker_timeout_seconds=self.dispatcher_worker_timeout_seconds,
            concurrency=self.dispatcher_concurrency,
            shutdown_timeout_seconds=self.dispatcher_shutdown_timeout_seconds,
        )

    @classmethod
    def load(cls) -> Self:
        try:
            return cls()
        except (OSError, ValidationError, ValueError):
            raise AgentDatabaseConfigurationError(_ERROR) from None


__all__ = [
    "AGENT_APPLICATION_NAME",
    "AGENT_BROWSER_SIGNING_KEY_FILE",
    "AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE",
    "AGENT_DSN_FILE",
    "AGENT_LOGIN",
    "AGENT_PRIVILEGE_ROLE",
    "AgentDatabaseConfigurationError",
    "AgentDatabaseMode",
    "AgentDatabaseSettings",
    "AgentDispatcherSettings",
]

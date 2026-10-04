"""Typed review-worker configuration (narrow worker credential only)."""

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

REVIEW_WORKER_LOGIN = "slaif_review_worker_login"
REVIEW_WORKER_PRIVILEGE_ROLE = "slaif_review_worker"
REVIEW_WORKER_DSN_FILE = Path("/run/slaif-review-worker/review-worker-dsn")
REVIEW_WORKER_APPLICATION_NAME = "slaif-review-worker"
# Pinned product version surfaces recorded in every immutable snapshot.
REVIEW_WORKER_STATE_VERSION = "review-snapshot/v1"
REVIEW_WORKER_PUCK_VERSION_PIN = "0.20.2"
REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION = "content-model/v1"
REVIEW_WORKER_POLL_INTERVAL_SECONDS = 1.0
REVIEW_WORKER_BATCH_SIZE = 1
REVIEW_WORKER_STALENESS_SECONDS = 60.0
REVIEW_WORKER_DRAIN_LOCK_TIMEOUT_SECONDS = 30.0
REVIEW_WORKER_EVIDENCE_DEADLINE_SECONDS = 120.0
REVIEW_WORKER_HEARTBEAT_INTERVAL_SECONDS = 20.0
REVIEW_WORKER_EVIDENCE_POLL_SECONDS = 2.0
_ERROR = "Invalid SLAIF review-worker configuration."


class ReviewWorkerDatabaseMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class ReviewWorkerConfigurationError(RuntimeError):
    """A constant failure without locator or credential details."""


class ReviewWorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SLAIF_REVIEW_WORKER_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        frozen=True,
        validate_default=True,
    )

    mode: ReviewWorkerDatabaseMode = ReviewWorkerDatabaseMode.DEVELOPMENT
    dsn: SecretStr | None = None
    dsn_file: Path | None = REVIEW_WORKER_DSN_FILE
    expected_database: str = "slaif"
    expected_login: str = REVIEW_WORKER_LOGIN
    expected_privilege_role: str = REVIEW_WORKER_PRIVILEGE_ROLE
    poll_interval_seconds: float = Field(
        default=REVIEW_WORKER_POLL_INTERVAL_SECONDS, ge=0.1, le=30
    )
    batch_size: int = Field(default=REVIEW_WORKER_BATCH_SIZE, ge=1, le=8)
    staleness_seconds: float = Field(
        default=REVIEW_WORKER_STALENESS_SECONDS, ge=10, le=600
    )
    drain_lock_timeout_seconds: float = Field(
        default=REVIEW_WORKER_DRAIN_LOCK_TIMEOUT_SECONDS, ge=5, le=300
    )
    evidence_deadline_seconds: float = Field(
        default=REVIEW_WORKER_EVIDENCE_DEADLINE_SECONDS, ge=5, le=600
    )
    heartbeat_interval_seconds: float = Field(
        default=REVIEW_WORKER_HEARTBEAT_INTERVAL_SECONDS, ge=1, le=120
    )
    evidence_poll_seconds: float = Field(
        default=REVIEW_WORKER_EVIDENCE_POLL_SECONDS, ge=0.5, le=30
    )
    application_name: str = REVIEW_WORKER_APPLICATION_NAME

    @field_validator("dsn_file")
    @classmethod
    def absolute_path(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("Review worker paths must be absolute")
        return value

    @field_validator("expected_database", "expected_login", "expected_privilege_role")
    @classmethod
    def identity(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
            raise ValueError("Review worker database identity is invalid")
        return value

    @field_validator("application_name")
    @classmethod
    def application_name_value(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", value):
            raise ValueError("Review worker application name is invalid")
        return value

    @model_validator(mode="after")
    def boundary(self) -> Self:
        if (
            self.dsn is not None
            and self.dsn_file is not None
            and self.mode is not ReviewWorkerDatabaseMode.TEST
        ):
            raise ValueError("configure one review-worker database locator source")
        if self.mode is ReviewWorkerDatabaseMode.TEST:
            if self.dsn is None and self.dsn_file is None:
                raise ValueError(
                    "test mode requires one review-worker database locator"
                )
        elif self.dsn is not None or self.dsn_file is None:
            raise ValueError("review-worker database locator must use a mounted file")
        if self.expected_privilege_role != REVIEW_WORKER_PRIVILEGE_ROLE:
            raise ValueError("review-worker privilege role is fixed")
        if (
            self.mode is not ReviewWorkerDatabaseMode.TEST
            and self.expected_login != REVIEW_WORKER_LOGIN
        ):
            raise ValueError("review-worker identity must use the fixed authority")
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
            raise ReviewWorkerConfigurationError(_ERROR) from None
        if not value or "\n" in value or "\r" in value:
            raise ReviewWorkerConfigurationError(_ERROR)
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
            if self.mode is ReviewWorkerDatabaseMode.PRODUCTION:
                if (
                    query.get("sslmode") != "verify-full"
                    or query.get("target_session_attrs") != "read-write"
                    or not Path(query.get("sslrootcert", "")).is_absolute()
                ):
                    raise ValueError
            elif query.get("sslmode") not in {None, "disable"}:
                raise ValueError
            if (
                self.mode is ReviewWorkerDatabaseMode.DEVELOPMENT
                and parsed.hostname != "postgres"
            ):
                raise ValueError
            if self.mode is ReviewWorkerDatabaseMode.TEST and self.dsn is not None:
                host = parsed.hostname.casefold()
                if host not in {"127.0.0.1", "::1", "localhost"} and not host.endswith(
                    ".test"
                ):
                    raise ValueError
        except (TypeError, ValueError):
            raise ReviewWorkerConfigurationError(_ERROR) from None
        return SecretStr(value)

    def resolved_dsn(self) -> SecretStr:
        if self.dsn is not None:
            value = self.dsn.get_secret_value()
        elif self.dsn_file is not None:
            value = self._read_file(self.dsn_file)
        else:
            raise ReviewWorkerConfigurationError(_ERROR)
        return self._validate_locator(value)

    @property
    def server_settings(self) -> dict[str, str]:
        return {
            "application_name": self.application_name,
            "statement_timeout": "600000",
            "lock_timeout": "600000",
            "idle_in_transaction_session_timeout": "600000",
        }

    @classmethod
    def load(cls) -> Self:
        try:
            return cls()
        except (OSError, ValidationError, ValueError):
            raise ReviewWorkerConfigurationError(_ERROR) from None


__all__ = [
    "REVIEW_WORKER_APPLICATION_NAME",
    "REVIEW_WORKER_BATCH_SIZE",
    "REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION",
    "REVIEW_WORKER_DRAIN_LOCK_TIMEOUT_SECONDS",
    "REVIEW_WORKER_DSN_FILE",
    "REVIEW_WORKER_EVIDENCE_DEADLINE_SECONDS",
    "REVIEW_WORKER_EVIDENCE_POLL_SECONDS",
    "REVIEW_WORKER_HEARTBEAT_INTERVAL_SECONDS",
    "REVIEW_WORKER_LOGIN",
    "REVIEW_WORKER_POLL_INTERVAL_SECONDS",
    "REVIEW_WORKER_PRIVILEGE_ROLE",
    "REVIEW_WORKER_PUCK_VERSION_PIN",
    "REVIEW_WORKER_STALENESS_SECONDS",
    "REVIEW_WORKER_STATE_VERSION",
    "ReviewWorkerConfigurationError",
    "ReviewWorkerDatabaseMode",
    "ReviewWorkerSettings",
]

"""Typed, local-only service configuration with fail-closed production rules."""

from __future__ import annotations

import os
import re
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import (
    Field,
    HttpUrl,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(StrEnum):
    JSON = "json"


class ConfigurationError(RuntimeError):
    """A deliberately non-diagnostic startup error safe for stderr/logs."""


class ServiceSettings(BaseSettings):
    """Shared settings; process identity remains trusted module-owned data."""

    model_config = SettingsConfigDict(
        env_prefix="SLAIF_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        env_file_encoding="utf-8",
        frozen=True,
        validate_default=True,
    )

    mode: EnvironmentMode = EnvironmentMode.DEVELOPMENT
    public_url: HttpUrl = HttpUrl("http://localhost:8080")
    bind_host: str = "127.0.0.1"
    bind_port: int = Field(default=8000, ge=1, le=65535)
    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.JSON
    env_file: Path | None = None
    app_secret: SecretStr | None = None
    app_secret_file: Path | None = None
    secure_cookies: bool = False
    shutdown_timeout_seconds: int = Field(default=15, ge=1, le=120)
    readiness_timeout_seconds: float = Field(default=2.0, ge=0.05, le=30.0)

    @field_validator("bind_host")
    @classmethod
    def validate_bind_host(cls, value: str) -> str:
        candidate = value.strip()
        if (
            not candidate
            or len(candidate) > 253
            or any(character.isspace() for character in candidate)
            or not re.fullmatch(r"[A-Za-z0-9.:[\]-]+", candidate)
        ):
            raise ValueError("bind host is invalid")
        return candidate

    @field_validator("env_file", "app_secret_file")
    @classmethod
    def validate_absolute_file_reference(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("file references must be absolute")
        return value

    @model_validator(mode="after")
    def validate_security_boundary(self) -> Self:
        if self.env_file is not None and self.mode is not EnvironmentMode.DEVELOPMENT:
            raise ValueError("environment files are development-only")
        if self.app_secret is not None and self.app_secret_file is not None:
            raise ValueError("configure one secret source, not two")
        if self.public_url.username or self.public_url.password:
            raise ValueError("public URL credentials are forbidden")
        if self.public_url.query or self.public_url.fragment:
            raise ValueError("public URL query and fragment are forbidden")
        if self.mode is EnvironmentMode.PRODUCTION:
            if self.public_url.scheme != "https":
                raise ValueError("production public URL must use HTTPS")
            if not self.secure_cookies:
                raise ValueError("production requires secure cookies")
            self._validated_secret_value()
        return self

    def _validated_secret_value(self) -> SecretStr:
        secret = self.app_secret
        if self.app_secret_file is not None:
            try:
                raw = self.app_secret_file.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                raise ValueError("configured secret file is unavailable") from None
            secret = SecretStr(raw.rstrip("\r\n"))
        if secret is None:
            raise ValueError("a production secret source is required")
        value = secret.get_secret_value()
        weak_values = {
            "change-me",
            "changeme",
            "development",
            "password",
            "secret",
            "test",
        }
        weak_marker = re.search(
            r"(?:^|[_:=.-])(?:change-?me|password|secret|token)(?:$|[_:=.-])",
            value,
            re.IGNORECASE,
        )
        if (
            len(value) < 32
            or value.casefold() in weak_values
            or len(set(value)) < 8
            or weak_marker is not None
        ):
            raise ValueError("the configured production secret is weak")
        return secret

    def resolved_app_secret(self) -> SecretStr | None:
        """Resolve the configured secret without exposing it in model output."""

        if self.app_secret is None and self.app_secret_file is None:
            return None
        return self._validated_secret_value()

    @classmethod
    def load(cls) -> Self:
        """Load `SLAIF_` settings and optionally one explicit development file."""

        raw_mode = os.environ.get("SLAIF_MODE", EnvironmentMode.DEVELOPMENT.value)
        env_file = os.environ.get("SLAIF_ENV_FILE")
        try:
            if env_file and raw_mode.casefold() == EnvironmentMode.DEVELOPMENT.value:
                return cls(_env_file=env_file)  # type: ignore[call-arg]
            return cls()
        except (OSError, ValidationError, ValueError):
            raise ConfigurationError("Invalid SLAIF service configuration.") from None

    @classmethod
    def for_test(cls) -> Self:
        """Return deterministic settings with no production credential."""

        return cls(
            mode=EnvironmentMode.TEST,
            public_url=HttpUrl("http://testserver"),
            bind_host="127.0.0.1",
            bind_port=8000,
            log_level=LogLevel.WARNING,
            secure_cookies=False,
            readiness_timeout_seconds=0.1,
        )


__all__ = [
    "ConfigurationError",
    "EnvironmentMode",
    "LogFormat",
    "LogLevel",
    "ServiceSettings",
]

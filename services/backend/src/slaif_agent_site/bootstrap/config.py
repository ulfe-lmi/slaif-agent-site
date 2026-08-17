"""Secret-safe configuration used only by the one-shot bootstrap package."""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BootstrapMode(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


class BootstrapConfigurationError(RuntimeError):
    """Constant public configuration failure safe for CLI output."""


class BootstrapSettings(BaseSettings):
    """Separate provisioner/owner locators for an explicit one-shot command."""

    model_config = SettingsConfigDict(
        env_prefix="SLAIF_BOOTSTRAP_",
        case_sensitive=False,
        extra="forbid",
        env_file=None,
        frozen=True,
        validate_default=True,
    )

    mode: BootstrapMode
    expected_database: str
    provisioner_dsn: SecretStr | None = None
    provisioner_dsn_file: Path | None = None
    owner_dsn: SecretStr | None = None
    owner_dsn_file: Path | None = None

    @field_validator("expected_database")
    @classmethod
    def validate_database_name(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", value):
            raise ValueError("expected database name is invalid")
        return value

    @field_validator("provisioner_dsn_file", "owner_dsn_file")
    @classmethod
    def validate_absolute_secret_file(cls, value: Path | None) -> Path | None:
        if value is not None and not value.is_absolute():
            raise ValueError("secret-file references must be absolute")
        return value

    @model_validator(mode="after")
    def validate_sources(self) -> Self:
        pairs = (
            (self.provisioner_dsn, self.provisioner_dsn_file),
            (self.owner_dsn, self.owner_dsn_file),
        )
        if any(direct is not None and file is not None for direct, file in pairs):
            raise ValueError("configure one source for each database authority")
        if self.mode is BootstrapMode.PRODUCTION and any(
            direct is not None for direct, _file in pairs
        ):
            raise ValueError("production database locators require secret files")
        return self

    @staticmethod
    def _read_secret_file(path: Path) -> SecretStr:
        try:
            value = path.read_text(encoding="utf-8").rstrip("\r\n")
        except (OSError, UnicodeError):
            raise ValueError("database locator file is unavailable") from None
        if not value:
            raise ValueError("database locator file is empty")
        return SecretStr(value)

    def resolved_provisioner_dsn(self) -> SecretStr:
        source = self.provisioner_dsn
        if self.provisioner_dsn_file is not None:
            source = self._read_secret_file(self.provisioner_dsn_file)
        if source is None:
            raise ValueError("cluster provisioner locator is required")
        return source

    def resolved_owner_dsn(self) -> SecretStr:
        source = self.owner_dsn
        if self.owner_dsn_file is not None:
            source = self._read_secret_file(self.owner_dsn_file)
        if source is None:
            raise ValueError("setup-owner locator is required")
        return source

    @classmethod
    def load(cls) -> Self:
        try:
            return cls()  # type: ignore[call-arg]
        except (OSError, ValidationError, ValueError):
            raise BootstrapConfigurationError(
                "Invalid SLAIF database bootstrap configuration."
            ) from None


__all__ = [
    "BootstrapConfigurationError",
    "BootstrapMode",
    "BootstrapSettings",
]

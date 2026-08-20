"""Secret-safe semantic identity inputs and bounded setup results."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

LOCAL_USERNAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9._-]{2,62}")
_DISPLAY_NAME_MAX_CHARACTERS = 128
_EMAIL_MAX_CHARACTERS = 254


class IdentityInputError(ValueError):
    """Constant public-safe local identity validation failure."""


def normalize_local_username(username: str) -> str:
    """Normalize the deliberately ASCII-only local identity key."""

    if LOCAL_USERNAME_PATTERN.fullmatch(username) is None:
        raise IdentityInputError("Invalid local identity input.")
    return username.lower()


class InitialLocalAdministratorRequest(BaseModel):
    """Validated semantic input without caller-selected object identities."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    username: str
    password: SecretStr = Field(exclude=True, repr=False)
    display_name: str
    email: str | None = None
    setup_token: SecretStr = Field(exclude=True, repr=False)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        try:
            normalize_local_username(value)
        except IdentityInputError:
            raise ValueError("invalid local identity input") from None
        return value

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if (
            not normalized
            or len(normalized) > _DISPLAY_NAME_MAX_CHARACTERS
            or "\x00" in normalized
        ):
            raise ValueError("invalid local identity input")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if (
            not normalized
            or len(normalized) > _EMAIL_MAX_CHARACTERS
            or "\x00" in normalized
            or normalized.count("@") != 1
            or any(character.isspace() for character in normalized)
        ):
            raise ValueError("invalid local identity input")
        local, domain = normalized.split("@", 1)
        if (
            not local
            or "." not in domain
            or domain.startswith(".")
            or domain.endswith(".")
        ):
            raise ValueError("invalid local identity input")
        return normalized

    @property
    def normalized_username(self) -> str:
        return normalize_local_username(self.username)


class InitialLocalAdministratorResult(BaseModel):
    """Bounded identity result with no credential or setup-token material."""

    model_config = ConfigDict(frozen=True)

    user_account_id: UUID
    username: str
    display_name: str
    email: str | None
    status: str
    created_at: datetime


__all__ = [
    "IdentityInputError",
    "InitialLocalAdministratorRequest",
    "InitialLocalAdministratorResult",
    "LOCAL_USERNAME_PATTERN",
    "normalize_local_username",
]

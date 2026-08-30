"""Bounded fixed site-data records used by the human Editor."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import _bounded_json, _bounded_text
from .site_data_validators import (
    validate_locale_tag,
    validate_redirect,
    validate_target,
)


class CreateLocaleRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tag: str
    enabled: bool = True
    is_default: bool = False
    position: int = Field(default=0, ge=0, le=999)
    metadata: dict[str, Any] = {}

    @field_validator("tag")
    @classmethod
    def tag_is_normalized(cls, value: str) -> str:
        return validate_locale_tag(value)

    @field_validator("metadata")
    @classmethod
    def metadata_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class UpdateLocaleRequest(CreateLocaleRequest):
    expected_row_version: int = Field(ge=1)


class LocaleRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    tag: str
    enabled: bool
    is_default: bool
    position: int
    metadata: dict[str, Any]
    row_version: int
    created_at: datetime
    updated_at: datetime


class CreateNavigationItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    navigation_id: UUID
    parent_id: UUID | None = None
    page_id: UUID | None = None
    target_kind: str = "INTERNAL"
    target_value: str = "/"
    labels: dict[str, str] = {}
    locale: str | None = None
    position: int = Field(default=0, ge=0, le=999)

    @field_validator("target_kind")
    @classmethod
    def target_kind_is_safe(cls, value: str) -> str:
        if value not in {"PAGE", "INTERNAL", "EXTERNAL"}:
            raise ValueError("invalid navigation target kind")
        return value

    @field_validator("target_value")
    @classmethod
    def target_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 512)

    @field_validator("labels")
    @classmethod
    def labels_are_bounded(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 16:
            raise ValueError("too many navigation labels")
        return {
            validate_locale_tag(key): _bounded_text(label, 256)
            for key, label in value.items()
        }

    @field_validator("locale")
    @classmethod
    def locale_is_normalized(cls, value: str | None) -> str | None:
        return validate_locale_tag(value) if value is not None else None

    @model_validator(mode="after")
    def target_is_safe(self) -> CreateNavigationItemRequest:
        validate_target(self.target_kind, self.target_value)
        if not self.labels and self.locale is None:
            raise ValueError("navigation item needs a label")
        return self


class UpdateNavigationItemRequest(CreateNavigationItemRequest):
    expected_row_version: int = Field(ge=1)


class MoveNavigationItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    parent_id: UUID | None = None
    position: int = Field(ge=0, le=999)
    expected_row_version: int = Field(ge=1)


class NavigationItemRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    navigation_id: UUID
    parent_id: UUID | None
    page_id: UUID | None
    target_kind: str
    target_value: str
    labels: dict[str, str]
    locale: str | None
    position: int
    row_version: int
    created_at: datetime
    updated_at: datetime


class CreateRedirectRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_route: str
    target: str
    status_code: int = Field(default=302, ge=301, le=308)
    locale: str | None = None

    @field_validator("source_route")
    @classmethod
    def source_is_normalized(cls, value: str) -> str:
        return value

    @field_validator("target")
    @classmethod
    def target_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 2048)

    @field_validator("locale")
    @classmethod
    def locale_is_normalized(cls, value: str | None) -> str | None:
        return validate_locale_tag(value) if value is not None else None

    @model_validator(mode="after")
    def redirect_is_safe(self) -> CreateRedirectRequest:
        source, _ = validate_redirect(self.source_route, self.target)
        object.__setattr__(self, "source_route", source)
        return self


class UpdateRedirectRequest(CreateRedirectRequest):
    expected_row_version: int = Field(ge=1)


class RedirectRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    source_route: str
    target: str
    status_code: int
    locale: str | None
    row_version: int
    created_at: datetime
    updated_at: datetime


class CreateProposedSideEffectRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: UUID
    kind: str
    payload: dict[str, Any]

    @field_validator("kind")
    @classmethod
    def kind_is_allowlisted(cls, value: str) -> str:
        if value not in {"analytics_event", "cache_purge"}:
            raise ValueError("side effect kind is not allowlisted")
        return value

    @field_validator("payload")
    @classmethod
    def payload_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class ProposedSideEffectRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    workspace_id: UUID
    kind: str
    payload: dict[str, Any]
    state: str
    created_at: datetime
    updated_at: datetime


__all__ = [
    "CreateLocaleRequest",
    "CreateNavigationItemRequest",
    "CreateProposedSideEffectRequest",
    "CreateRedirectRequest",
    "LocaleRecord",
    "MoveNavigationItemRequest",
    "NavigationItemRecord",
    "ProposedSideEffectRecord",
    "RedirectRecord",
    "UpdateLocaleRequest",
    "UpdateNavigationItemRequest",
    "UpdateRedirectRequest",
]

"""Bounded fixed site-data records used by the human Editor."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .models import _bounded_json, _bounded_text
from .site_data_validators import (
    validate_agent_target,
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


class AgentCreateLocaleRequest(CreateLocaleRequest):
    """Agent-facing alias with the same bounded locale-create contract."""


class UpdateLocaleRequest(CreateLocaleRequest):
    expected_row_version: int = Field(ge=1)


class AgentUpdateLocaleRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool | None = None
    is_default: bool | None = None
    position: int | None = Field(default=None, ge=0, le=999)
    metadata: dict[str, Any] | None = None
    expected_row_version: int = Field(ge=1)

    @field_validator("metadata")
    @classmethod
    def metadata_is_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @model_validator(mode="after")
    def update_is_nonempty(self) -> AgentUpdateLocaleRequest:
        if not self.model_fields_set.intersection(
            {"enabled", "is_default", "position", "metadata"}
        ):
            raise ValueError("locale update cannot be empty")
        return self


class AgentCreateNavigationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    label: str
    labels: dict[str, str] = {}
    settings: dict[str, Any] = {}

    @field_validator("key")
    @classmethod
    def key_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 63)

    @field_validator("label")
    @classmethod
    def label_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 256)

    @field_validator("labels")
    @classmethod
    def labels_are_bounded(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 16:
            raise ValueError("too many navigation labels")
        return {
            validate_locale_tag(key): _bounded_text(label, 256)
            for key, label in value.items()
        }

    @field_validator("settings")
    @classmethod
    def settings_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class AgentUpdateNavigationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str | None = None
    labels: dict[str, str] | None = None
    settings: dict[str, Any] | None = None
    expected_row_version: int = Field(ge=1)

    @field_validator("label")
    @classmethod
    def label_is_bounded(cls, value: str | None) -> str | None:
        return _bounded_text(value, 256) if value is not None else None

    @field_validator("labels")
    @classmethod
    def labels_are_bounded(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        if len(value) > 16:
            raise ValueError("too many navigation labels")
        return {
            validate_locale_tag(key): _bounded_text(label, 256)
            for key, label in value.items()
        }

    @field_validator("settings")
    @classmethod
    def settings_are_bounded(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @model_validator(mode="after")
    def update_is_nonempty(self) -> AgentUpdateNavigationRequest:
        if not self.model_fields_set.intersection({"label", "labels", "settings"}):
            raise ValueError("navigation update cannot be empty")
        return self


class AgentCreateNavigationItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    navigation_id: UUID | None = None
    parent_id: UUID | None = None
    page_id: UUID | None = None
    target_kind: str = "INTERNAL"
    target_value: str = "/"
    labels: dict[str, str] = {}
    locale: str | None = None
    before_item_id: UUID | None = None
    after_item_id: UUID | None = None

    @field_validator("target_kind")
    @classmethod
    def target_kind_is_safe(cls, value: str) -> str:
        if value not in {"PAGE", "INTERNAL", "EXTERNAL"}:
            raise ValueError("invalid navigation target kind")
        return value

    @field_validator("target_value")
    @classmethod
    def target_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 2048)

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
    def target_is_safe(self) -> AgentCreateNavigationItemRequest:
        validate_agent_target(self.target_kind, self.target_value)
        if self.target_kind == "PAGE":
            if self.page_id is None or self.target_value != str(self.page_id):
                raise ValueError("page target must match page_id")
        elif self.page_id is not None:
            raise ValueError("non-page navigation target cannot have page_id")
        if self.before_item_id is not None and self.after_item_id is not None:
            raise ValueError("navigation item cannot have both anchors")
        if not self.labels and self.locale is None:
            raise ValueError("navigation item needs a label")
        return self


class AgentUpdateNavigationItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    page_id: UUID | None = None
    target_kind: str | None = None
    target_value: str | None = None
    labels: dict[str, str] | None = None
    locale: str | None = None
    expected_row_version: int = Field(ge=1)

    @field_validator("target_kind")
    @classmethod
    def target_kind_is_safe(cls, value: str | None) -> str | None:
        if value is not None and value not in {"PAGE", "INTERNAL", "EXTERNAL"}:
            raise ValueError("invalid navigation target kind")
        return value

    @field_validator("target_value")
    @classmethod
    def target_is_bounded(cls, value: str | None) -> str | None:
        return _bounded_text(value, 2048) if value is not None else None

    @field_validator("labels")
    @classmethod
    def labels_are_bounded(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
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
    def update_is_nonempty(self) -> AgentUpdateNavigationItemRequest:
        if not self.model_fields_set.intersection(
            {"page_id", "target_kind", "target_value", "labels", "locale"}
        ):
            raise ValueError("navigation item update cannot be empty")
        return self


class AgentMoveNavigationItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Required even when null: root placement must be an explicit client intent.
    parent_id: UUID | None
    before_item_id: UUID | None = None
    after_item_id: UUID | None = None
    expected_row_version: int = Field(ge=1)

    @model_validator(mode="after")
    def anchors_are_exclusive(self) -> AgentMoveNavigationItemRequest:
        if self.before_item_id is not None and self.after_item_id is not None:
            raise ValueError("navigation item cannot have both anchors")
        return self


class AgentNavigationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    key: str
    label: str
    labels: dict[str, str]
    settings: dict[str, Any]
    row_version: int
    created_at: datetime
    updated_at: datetime


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
        if self.target_kind == "PAGE":
            if self.page_id is None or self.target_value != str(self.page_id):
                raise ValueError("page target must match page_id")
        elif self.page_id is not None:
            raise ValueError("non-page navigation target cannot have page_id")
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

    @field_validator("status_code")
    @classmethod
    def status_is_redirect(cls, value: int) -> int:
        if value not in {301, 302, 303, 307, 308}:
            raise ValueError("unsupported redirect status")
        return value

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
    "AgentCreateLocaleRequest",
    "AgentCreateNavigationItemRequest",
    "AgentCreateNavigationRequest",
    "AgentMoveNavigationItemRequest",
    "AgentNavigationRecord",
    "AgentUpdateLocaleRequest",
    "AgentUpdateNavigationItemRequest",
    "AgentUpdateNavigationRequest",
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

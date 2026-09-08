"""Page request and record models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import _bounded_text
from .site_data_validators import validate_locale_tag


def _normalize_page_segment(value: str) -> str:
    normalized = value.strip().strip("/").lower()
    if (
        not normalized
        or len(normalized) > 63
        or not normalized.isascii()
        or any(marker in normalized for marker in ("/", "\\", "%", "?", "#"))
        or normalized in {".", ".."}
        or any(
            not (character.isalnum() or character in {"-", "_", ".", "~"})
            for character in normalized
        )
        or not normalized[0].isalnum()
    ):
        raise ValueError("invalid page slug")
    return normalized


def _normalize_route_template(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "{slug}":
        return normalized
    raise ValueError("route template must be null or {slug}")


class CreatePageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str
    title: str
    status: str = "DRAFT"
    locale: str = "en"
    parent_id: UUID | None = None
    route_template: str | None = None

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: str) -> str:
        return _normalize_page_segment(value)

    @field_validator("title")
    @classmethod
    def title_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 256)

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, value: str) -> str:
        if value not in ("DRAFT", "PUBLISHED", "ARCHIVED"):
            raise ValueError("status must be DRAFT, PUBLISHED, or ARCHIVED")
        return value

    @field_validator("locale")
    @classmethod
    def locale_is_valid(cls, value: str) -> str:
        try:
            return validate_locale_tag(value)
        except ValueError:
            raise ValueError("invalid locale") from None

    @field_validator("route_template")
    @classmethod
    def route_template_is_safe(cls, value: str | None) -> str | None:
        return _normalize_route_template(value)


class UpdatePageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str | None = None
    title: str | None = None
    status: str | None = None
    locale: str | None = None
    route_template: str | None = None
    expected_row_version: int = Field(gt=0)

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_page_segment(value)

    @field_validator("title")
    @classmethod
    def title_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 256)

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in ("DRAFT", "PUBLISHED", "ARCHIVED"):
            raise ValueError("status must be DRAFT, PUBLISHED, or ARCHIVED")
        return value

    @field_validator("locale")
    @classmethod
    def locale_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_locale_tag(value)
        except ValueError:
            raise ValueError("invalid locale") from None

    @field_validator("route_template")
    @classmethod
    def route_template_is_safe(cls, value: str | None) -> str | None:
        return _normalize_route_template(value)


class MovePageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    parent_id: UUID | None = None
    expected_row_version: int = Field(gt=0)


class RestorePageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_row_version: int = Field(gt=0)


class PageRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    slug: str
    title: str
    status: str
    locale: str
    parent_id: UUID | None
    route_template: str | None = None
    effective_route: str | None = None
    deleted_at: datetime | None = None
    row_version: int
    created_at: datetime
    updated_at: datetime

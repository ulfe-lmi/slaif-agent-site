"""Page request and record models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_text


class CreatePageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str
    title: str
    status: str = "DRAFT"
    locale: str = "en"
    parent_id: UUID | None = None

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: str) -> str:
        normalized = value.strip().strip("/")
        if not normalized or ".." in normalized or "\x00" in normalized:
            raise ValueError("invalid page slug")
        if len(normalized) > 512:
            raise ValueError("slug too long")
        return normalized

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
        normalized = value.strip().lower()
        if not normalized or len(normalized) > 10:
            raise ValueError("invalid locale")
        return normalized


class UpdatePageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str | None = None
    title: str | None = None
    status: str | None = None
    parent_id: UUID | None = None
    expected_row_version: int | None = None

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().strip("/")
        if not normalized or ".." in normalized:
            raise ValueError("invalid page slug")
        return normalized

    @field_validator("title")
    @classmethod
    def title_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 256)


class PageRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    slug: str
    title: str
    status: str
    locale: str
    parent_id: UUID | None
    row_version: int
    created_at: datetime
    updated_at: datetime

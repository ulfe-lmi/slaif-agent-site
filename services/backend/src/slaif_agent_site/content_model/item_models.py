"""Content item request and record models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text


class CreateContentItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type_id: UUID
    slug: str
    status: str = "DRAFT"
    values: dict[str, Any] = {}

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: str) -> str:
        return _bounded_text(value, 255)

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, value: str) -> str:
        if value not in ("DRAFT", "PUBLISHED", "ARCHIVED"):
            raise ValueError("status must be DRAFT, PUBLISHED, or ARCHIVED")
        return value

    @field_validator("values")
    @classmethod
    def values_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class UpdateContentItemRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str | None = None
    status: str | None = None
    values: dict[str, Any] | None = None
    expected_row_version: int | None = None

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 255)

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in ("DRAFT", "PUBLISHED", "ARCHIVED"):
            raise ValueError("status must be DRAFT, PUBLISHED, or ARCHIVED")
        return value

    @field_validator("values")
    @classmethod
    def values_are_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class ContentItemRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    type_id: UUID
    slug: str
    status: str
    type_definition_version: int
    values: dict[str, Any]
    row_version: int
    created_at: datetime
    updated_at: datetime

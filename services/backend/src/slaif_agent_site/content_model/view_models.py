"""Collection view request and record models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text


class CreateCollectionViewRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type_id: UUID
    definition_version: int | None = None
    key: str
    filter_spec: dict[str, Any] = {}
    sort_spec: dict[str, Any] = {}
    projection_spec: dict[str, Any] = {}
    pagination_spec: dict[str, Any] = {}

    @field_validator("key")
    @classmethod
    def key_is_valid(cls, value: str) -> str:
        return _bounded_text(value, 63)

    @field_validator("filter_spec")
    @classmethod
    def filter_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("sort_spec")
    @classmethod
    def sort_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("projection_spec")
    @classmethod
    def projection_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("pagination_spec")
    @classmethod
    def pagination_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class UpdateCollectionViewRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    filter_spec: dict[str, Any] | None = None
    sort_spec: dict[str, Any] | None = None
    projection_spec: dict[str, Any] | None = None
    pagination_spec: dict[str, Any] | None = None
    expected_row_version: int
    definition_version: int | None = None

    @field_validator("expected_row_version")
    @classmethod
    def row_version_is_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("expected_row_version must be positive")
        return value

    @field_validator("filter_spec")
    @classmethod
    def filter_is_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("sort_spec")
    @classmethod
    def sort_is_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("projection_spec")
    @classmethod
    def projection_is_bounded(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("pagination_spec")
    @classmethod
    def pagination_is_bounded(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class CollectionViewRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    type_id: UUID
    key: str
    filter_spec: dict[str, Any]
    sort_spec: dict[str, Any]
    projection_spec: dict[str, Any]
    pagination_spec: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    definition_version: int = 1
    row_version: int = 1

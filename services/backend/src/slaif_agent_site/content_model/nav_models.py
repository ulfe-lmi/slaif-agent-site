"""Navigation and theme models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text


class CreateNavigationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    label: str
    settings: dict[str, Any] = {}

    @field_validator("key")
    @classmethod
    def key_is_valid(cls, value: str) -> str:
        return _bounded_text(value, 63)

    @field_validator("label")
    @classmethod
    def label_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 256)

    @field_validator("settings")
    @classmethod
    def settings_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class NavigationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    key: str
    label: str
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class UpdateThemeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    palette: dict[str, Any] | None = None
    typography: dict[str, Any] | None = None
    layout: dict[str, Any] | None = None
    shape: dict[str, Any] | None = None

    @field_validator("palette")
    @classmethod
    def palette_is_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("typography")
    @classmethod
    def typography_is_bounded(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class ThemeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    palette: dict[str, Any]
    typography: dict[str, Any]
    layout: dict[str, Any]
    shape: dict[str, Any]
    created_at: datetime
    updated_at: datetime

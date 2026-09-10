"""Navigation and theme models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text
from .theme import ThemeRecord, UpdateThemeRequest


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


__all__ = [
    "CreateNavigationRequest",
    "NavigationRecord",
    "ThemeRecord",
    "UpdateThemeRequest",
]

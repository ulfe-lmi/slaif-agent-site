"""Page composition request and record models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text


class CreateCompositionNodeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    component_type: str
    parent_id: str | None = None
    slot_key: str = "default"
    order_key: int = 0
    props: dict[str, Any] = {}

    @field_validator("component_type")
    @classmethod
    def component_type_is_valid(cls, value: str) -> str:
        if not value or len(value) > 63 or "\x00" in value:
            raise ValueError("invalid component type")
        return value

    @field_validator("parent_id")
    @classmethod
    def parent_id_is_uuid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return str(UUID(value))
        except ValueError:
            raise ValueError("parent_id must be a UUID") from None

    @field_validator("slot_key")
    @classmethod
    def slot_key_is_valid(cls, value: str) -> str:
        return _bounded_text(value, 63)

    @field_validator("props")
    @classmethod
    def props_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        # Security check: no executable prop names
        forbidden = {
            "innerHTML",
            "dangerouslySetInnerHTML",
            "script",
            "eval",
            "onclick",
            "onload",
        }
        for key in result:
            if key.lower() in forbidden:
                raise ValueError(f"forbidden prop name: {key}")
        return result


class UpdateCompositionNodeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    props: dict[str, Any] | None = None
    slot_key: str | None = None
    order_key: int | None = None

    @field_validator("slot_key")
    @classmethod
    def slot_key_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 63)

    @field_validator("props")
    @classmethod
    def props_are_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        forbidden = {"innerHTML", "dangerouslySetInnerHTML", "script", "eval"}
        for key in result:
            if key.lower() in forbidden:
                raise ValueError(f"forbidden prop name: {key}")
        return result


class MoveCompositionNodeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    new_parent_id: str | None = None
    new_slot_key: str | None = None
    new_order_key: int = 0


class CompositionNodeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    page_id: UUID
    site_id: UUID
    component_type: str
    schema_version: str
    parent_id: UUID | None
    slot_key: str
    order_key: int
    props: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PageCompositionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    page_id: UUID
    site_id: UUID
    locale: str
    schema_version: str
    catalog_version: str
    nodes: tuple[CompositionNodeRecord, ...]
    updated_at: datetime

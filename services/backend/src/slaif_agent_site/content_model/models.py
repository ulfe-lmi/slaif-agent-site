"""Immutable content model request and record models.

Architecture reference: ARCHITECTURE-for-agents.md §7 (website data,
composition, design) and §10 (logical COW content model). All models are
frozen Pydantic models; clients cannot mutate them after validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .primitives import FieldPrimitive, FieldPrimitiveError


def _bounded_text(value: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > max_length or "\x00" in normalized:
        raise ValueError(f"text must be 1-{max_length} characters")
    return normalized


def _bounded_json(value: Any, max_depth: int = 8) -> Any:
    if isinstance(value, dict):
        if len(value) > 64:
            raise ValueError("object has too many keys")
        return {k: _bounded_json(v, max_depth - 1) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 128:
            raise ValueError("array has too many items")
        return [_bounded_json(v, max_depth - 1) for v in value]
    if isinstance(value, str) and len(value) > 4096:
        raise ValueError("string too long")
    return value


class CreateContentTypeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    labels: dict[str, str] = {}
    slug_pattern: str
    settings: dict[str, Any] = {}

    @field_validator("key")
    @classmethod
    def key_is_valid(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or not normalized.replace("-", "").replace("_", "").isalnum():
            raise ValueError("key must be alphanumeric with hyphens or underscores")
        if len(normalized) > 63:
            raise ValueError("key too long")
        return normalized

    @field_validator("slug_pattern")
    @classmethod
    def slug_pattern_is_valid(cls, value: str) -> str:
        return _bounded_text(value, 128)

    @field_validator("labels")
    @classmethod
    def labels_are_bounded(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 16:
            raise ValueError("too many labels")
        return {k: _bounded_text(v, 256) for k, v in value.items()}

    @field_validator("settings")
    @classmethod
    def settings_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class UpdateContentTypeRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    labels: dict[str, str] | None = None
    slug_pattern: str | None = None
    settings: dict[str, Any] | None = None
    expected_definition_version: int = Field(default=1, ge=1)

    @field_validator("slug_pattern")
    @classmethod
    def slug_pattern_is_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 128)

    @field_validator("labels")
    @classmethod
    def labels_are_bounded(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        if len(value) > 16:
            raise ValueError("too many labels")
        return {k: _bounded_text(v, 256) for k, v in value.items()}

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


class DeleteDefinitionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_definition_version: int = Field(default=1, ge=1)


class ContentTypeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    key: str
    labels: dict[str, str]
    slug_pattern: str
    status: str
    definition_version: int
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CreateFieldDefinitionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    label: str
    field_type: str
    required: bool = False
    localized: bool = False
    cardinality: int = 1
    position: int = 0
    validation: dict[str, Any] = {}
    ui_options: dict[str, Any] = {}

    @field_validator("key")
    @classmethod
    def key_is_valid(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or not normalized.replace("-", "").replace("_", "").isalnum():
            raise ValueError("key must be alphanumeric with hyphens or underscores")
        if len(normalized) > 63:
            raise ValueError("key too long")
        return normalized

    @field_validator("label")
    @classmethod
    def label_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 256)

    @field_validator("field_type")
    @classmethod
    def field_type_is_primitive(cls, value: str) -> str:
        try:
            FieldPrimitive.from_value(value)
        except FieldPrimitiveError:
            raise ValueError(
                "field_type must be one of: "
                + ", ".join(p.value for p in FieldPrimitive)
            ) from None
        return value

    @field_validator("cardinality")
    @classmethod
    def cardinality_is_bounded(cls, value: int) -> int:
        if not 1 <= value <= 32:
            raise ValueError("cardinality must be between 1 and 32")
        return value

    @field_validator("position")
    @classmethod
    def position_is_bounded(cls, value: int) -> int:
        if not 0 <= value <= 999:
            raise ValueError("position must be between 0 and 999")
        return value

    @field_validator("validation")
    @classmethod
    def validation_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("ui_options")
    @classmethod
    def ui_options_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @model_validator(mode="after")
    def relation_configuration_is_bounded(self) -> CreateFieldDefinitionRequest:
        if self.field_type == "reference" and self.cardinality != 1:
            raise ValueError("reference cardinality must be exactly one")
        if self.field_type == "multi_reference" and self.cardinality < 1:
            raise ValueError("multi_reference cardinality must be positive")
        if self.field_type in ("reference", "multi_reference"):
            unknown = set(self.validation) - {"target_type_id"}
            if unknown:
                raise ValueError("relation validation has unsupported keys")
            target = self.validation.get("target_type_id")
            if target is not None:
                try:
                    UUID(str(target))
                except (TypeError, ValueError):
                    raise ValueError("target_type_id must be a UUID") from None
        return self


class UpdateFieldDefinitionRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str | None = None
    required: bool | None = None
    localized: bool | None = None
    cardinality: int | None = None
    position: int | None = None
    validation: dict[str, Any] | None = None
    ui_options: dict[str, Any] | None = None
    expected_definition_version: int = Field(default=1, ge=1)
    expected_row_version: int | None = Field(default=None, ge=1)

    @field_validator("label")
    @classmethod
    def label_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 256)

    @field_validator("cardinality")
    @classmethod
    def cardinality_is_bounded(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if not 1 <= value <= 32:
            raise ValueError("cardinality must be between 1 and 32")
        return value

    @field_validator("position")
    @classmethod
    def position_is_bounded(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if not 0 <= value <= 999:
            raise ValueError("position must be between 0 and 999")
        return value

    @field_validator("validation")
    @classmethod
    def validation_is_bounded(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("ui_options")
    @classmethod
    def ui_options_are_bounded(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class FieldDefinitionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    type_id: UUID
    key: str
    label: str
    field_type: str
    required: bool
    localized: bool
    cardinality: int
    position: int
    validation: dict[str, Any]
    ui_options: dict[str, Any]
    definition_version: int
    created_at: datetime
    updated_at: datetime


class CreateTranslationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    locale: str
    localized_values: dict[str, Any] = {}

    @field_validator("locale")
    @classmethod
    def locale_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        import re

        normalized = value.strip()
        if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}", normalized):
            raise ValueError("locale must be a bounded BCP-47-like tag")
        return normalized

    @field_validator("localized_values")
    @classmethod
    def values_are_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class UpdateTranslationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    locale: str | None = None
    localized_values: dict[str, Any] | None = None
    expected_row_version: int

    @field_validator("locale")
    @classmethod
    def locale_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        import re

        normalized = value.strip()
        if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}", normalized):
            raise ValueError("locale must be a bounded BCP-47-like tag")
        return normalized

    @field_validator("localized_values")
    @classmethod
    def values_are_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result

    @field_validator("expected_row_version")
    @classmethod
    def row_version_is_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("expected_row_version must be positive")
        return value


class DeleteTranslationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_row_version: int = Field(gt=0)


class TranslationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    item_id: UUID
    locale: str
    localized_values: dict[str, Any]
    row_version: int
    created_at: datetime
    updated_at: datetime


class CreateRelationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    field_definition_id: UUID
    target_item_id: UUID
    position: int = 0
    metadata: dict[str, Any] = {}

    @field_validator("position")
    @classmethod
    def position_is_bounded(cls, value: int) -> int:
        if not 0 <= value <= 999:
            raise ValueError("position must be between 0 and 999")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_is_bounded(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class UpdateRelationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    target_item_id: UUID | None = None
    position: int | None = None
    metadata: dict[str, Any] | None = None
    expected_row_version: int

    @field_validator("position")
    @classmethod
    def position_is_bounded(cls, value: int | None) -> int | None:
        if value is not None and not 0 <= value <= 999:
            raise ValueError("position must be between 0 and 999")
        return value

    @field_validator("expected_row_version")
    @classmethod
    def row_version_is_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("expected_row_version must be positive")
        return value

    @field_validator("metadata")
    @classmethod
    def metadata_is_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class RelationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    source_item_id: UUID
    field_definition_id: UUID
    target_item_id: UUID
    position: int
    metadata: dict[str, Any]
    row_version: int
    created_at: datetime
    updated_at: datetime


__all__ = [
    "ContentTypeRecord",
    "CreateContentTypeRequest",
    "CreateFieldDefinitionRequest",
    "FieldDefinitionRecord",
    "CreateTranslationRequest",
    "DeleteTranslationRequest",
    "UpdateTranslationRequest",
    "TranslationRecord",
    "CreateRelationRequest",
    "UpdateRelationRequest",
    "RelationRecord",
    "UpdateContentTypeRequest",
    "UpdateFieldDefinitionRequest",
]

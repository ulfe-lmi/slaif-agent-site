"""Media asset request and record models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text


class UpdateMediaRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    alt_text: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("alt_text")
    @classmethod
    def alt_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _bounded_text(value, 512)

    @field_validator("metadata")
    @classmethod
    def metadata_is_bounded(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        result = _bounded_json(value)
        assert isinstance(result, dict)
        return result


class MediaAssetRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    uploaded_by: UUID | None
    filename: str
    mime_type: str
    size_bytes: int
    content_hash: str
    storage_key: str
    alt_text: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

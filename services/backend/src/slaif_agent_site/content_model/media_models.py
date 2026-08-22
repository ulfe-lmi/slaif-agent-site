"""Media asset request and record models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text

ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "application/pdf",
        "video/mp4",
        "audio/mpeg",
    }
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class CreateMediaRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    filename: str
    mime_type: str
    size_bytes: int
    alt_text: str = ""
    metadata: dict[str, Any] = {}

    @field_validator("filename")
    @classmethod
    def filename_is_safe(cls, value: str) -> str:
        normalized = value.strip()
        if (
            not normalized
            or ".." in normalized
            or "/" in normalized
            or "\\" in normalized
        ):
            raise ValueError("invalid filename")
        if len(normalized) > 255:
            raise ValueError("filename too long")
        return normalized

    @field_validator("mime_type")
    @classmethod
    def mime_type_is_allowed(cls, value: str) -> str:
        if value not in ALLOWED_MIME_TYPES:
            raise ValueError(f"unsupported media type: {value}")
        return value

    @field_validator("size_bytes")
    @classmethod
    def size_is_bounded(cls, value: int) -> int:
        if not 1 <= value <= MAX_FILE_SIZE:
            raise ValueError(f"file size must be between 1 and {MAX_FILE_SIZE} bytes")
        return value

    @field_validator("alt_text")
    @classmethod
    def alt_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 512)


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

"""Bounded site-global region (header/footer) content and typed update contracts.

Architecture reference: ARCHITECTURE-for-agents.md §5 (L4 global regions) and
§11 (Agent semantic API). Region records are site-level COW data validated
fail-closed by the PostgreSQL region validator; the typed models mirror the
closed enums, counts, lengths, and target bounds so both the human Editor and
the Agent API share one server-side contract.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

GLOBAL_REGION_SCHEMA_VERSION: Literal["global-region/v1"] = "global-region/v1"

RegionKey = Literal["header", "footer"]
HeaderVariant = Literal["institutional", "minimal"]
FooterVariant = Literal["multi-column", "single-column"]
RegionVariant = HeaderVariant | FooterVariant
RegionTargetKind = Literal["page", "internal", "external"]

REGION_VARIANTS: dict[RegionKey, tuple[RegionVariant, ...]] = {
    "header": ("institutional", "minimal"),
    "footer": ("multi-column", "single-column"),
}

MAX_LABEL_LENGTH = 256
MAX_NOTE_LENGTH = 4096
MAX_EXTERNAL_TARGET_LENGTH = 2048
MAX_INTERNAL_TARGET_LENGTH = 256
MAX_CONTENT_BYTES = 16 * 1024
MAX_HEADER_NAV_ENTRIES = 12
MAX_FOOTER_LINK_ENTRIES = 16

_PAGE_TARGET = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_INTERNAL_TARGET = re.compile(r"^/[a-z0-9._~/-]*$")
_EXTERNAL_TARGET = re.compile(r"^https?://[^/@][!-~]*$")
_RESERVED_ROUTE_PREFIXES = (
    "api",
    "admin",
    "agent",
    "control",
    "editor",
    "health",
    "internal",
    "login",
    "logout",
    "mcp",
    "media",
    "preview",
    "setup",
    "_next",
    "static",
)


def validate_region_label(label: str) -> str:
    if not label or len(label) > MAX_LABEL_LENGTH or label != label.strip():
        raise ValueError("region label must be 1-256 characters without padding")
    return label


def validate_region_target(kind: RegionTargetKind, value: str) -> str:
    """Apply the closed target bounds for one kind (server-side, fail-closed)."""
    if not isinstance(value, str) or not value:
        raise ValueError("region target value is required")
    if kind == "page":
        if not _PAGE_TARGET.fullmatch(value):
            raise ValueError("page region targets require a canonical page UUID")
        return value
    if kind == "internal":
        if len(value) > MAX_INTERNAL_TARGET_LENGTH:
            raise ValueError("internal region target exceeds its bound")
        if not _INTERNAL_TARGET.fullmatch(value):
            raise ValueError("internal region target is not a normalized route")
        if "//" in value or ".." in value or "%" in value:
            raise ValueError("internal region target is not safe")
        first_segment = value.strip("/").split("/", 1)[0]
        if first_segment in _RESERVED_ROUTE_PREFIXES:
            raise ValueError("internal region target uses a reserved route")
        return value
    if len(value) < 8 or len(value) > MAX_EXTERNAL_TARGET_LENGTH:
        raise ValueError("external region target exceeds its bound")
    if "@" in value:
        raise ValueError("external region targets may not carry credentials")
    if not _EXTERNAL_TARGET.fullmatch(value):
        raise ValueError("external region targets require an http/https URL")
    return value


class RegionTarget(BaseModel):
    """Bounded header/footer entry target: page, internal route, or http(s)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: RegionTargetKind
    value: str

    @model_validator(mode="after")
    def validate_target(self) -> RegionTarget:
        validate_region_target(self.kind, self.value)
        return self


class RegionEntry(BaseModel):
    """One ordered nav/link entry with a bounded localized label and target."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)
    target: RegionTarget

    @model_validator(mode="after")
    def validate_entry(self) -> RegionEntry:
        validate_region_label(self.label)
        return self


class GlobalRegionContent(BaseModel):
    """Bounded region content document.

    Header content is exactly ``{"nav": [...]}`` (1-12 entries). Footer content
    is ``{"links": [...]}`` (0-16 entries) with an optional ``note``. The
    serialized document is bounded to 16 KiB.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nav: tuple[RegionEntry, ...] | None = Field(
        default=None, min_length=1, max_length=MAX_HEADER_NAV_ENTRIES
    )
    links: tuple[RegionEntry, ...] | None = Field(
        default=None, max_length=MAX_FOOTER_LINK_ENTRIES
    )
    note: str | None = Field(default=None, max_length=MAX_NOTE_LENGTH)

    @model_validator(mode="after")
    def validate_shape(self) -> GlobalRegionContent:
        if self.nav is not None:
            if self.links is not None or self.note is not None:
                raise ValueError("header region content only carries nav entries")
            return self
        if self.links is None:
            raise ValueError("footer region content requires the links list")
        return self

    def is_header(self) -> bool:
        return self.nav is not None

    def document(self) -> dict[str, Any]:
        """Serialize the exact bounded document stored in the region row."""
        if self.nav is not None:
            document: dict[str, Any] = {
                "nav": [entry.model_dump(mode="json") for entry in self.nav]
            }
        else:
            document = {
                "links": [entry.model_dump(mode="json") for entry in self.links or ()]
            }
            if self.note is not None:
                document["note"] = self.note
        serialized = len(json.dumps(document, sort_keys=True).encode("utf-8"))
        if serialized > MAX_CONTENT_BYTES:
            raise ValueError("region content exceeds the 16 KiB bound")
        return document


class UpdateGlobalRegionRequest(BaseModel):
    """Partial region update: provided fields replace their current state.

    ``variant`` and ``content`` are both optional but at least one must be
    supplied; omitted fields are preserved server-side. ``content`` is the
    complete bounded document for the region, never a partial merge.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    variant: RegionVariant | None = None
    content: GlobalRegionContent | None = None
    expected_row_version: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_selection(self) -> UpdateGlobalRegionRequest:
        if self.variant is None and self.content is None:
            raise ValueError("region update must select at least one field")
        return self


class AgentUpdateGlobalRegionRequest(UpdateGlobalRegionRequest):
    """Agent updates always carry the observed row version (optimistic)."""

    expected_row_version: int = Field(gt=0)


class GlobalRegionRecord(BaseModel):
    """Trusted region row as returned by the region projection functions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    site_id: UUID
    region_key: RegionKey
    variant: RegionVariant
    content: GlobalRegionContent
    schema_version: Literal["global-region/v1"]
    row_version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime

    @model_serializer(mode="wrap")
    def serialize_record(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        data["content"] = self.content.document()
        return data

    @model_validator(mode="after")
    def validate_variant_key(self) -> GlobalRegionRecord:
        if self.variant not in REGION_VARIANTS[self.region_key]:
            raise ValueError("region variant does not match its region key")
        if self.content.is_header() is not (self.region_key == "header"):
            raise ValueError("region content shape does not match its region key")
        self.content.document()
        return self


class AgentGlobalRegionMutationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    record: GlobalRegionRecord
    operation_id: UUID
    action: Literal["GLOBAL_REGION_UPDATED"] | None = None


def global_region_record_from_row(row: Any) -> GlobalRegionRecord:

    if len(row) < 9:
        raise ValueError("region row shape is incomplete")
    content_value = row[4]
    if isinstance(content_value, str):
        content_value = json.loads(content_value)
    return GlobalRegionRecord(
        id=row[0],
        site_id=row[1],
        region_key=row[2],
        variant=row[3],
        content=GlobalRegionContent.model_validate(content_value),
        schema_version=row[5],
        row_version=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def global_region_content_json(content: GlobalRegionContent | None) -> str | None:

    if content is None:
        return None
    return json.dumps(content.document(), sort_keys=True)


__all__ = [
    "AgentGlobalRegionMutationResponse",
    "AgentUpdateGlobalRegionRequest",
    "FooterVariant",
    "GLOBAL_REGION_SCHEMA_VERSION",
    "GlobalRegionContent",
    "GlobalRegionRecord",
    "HeaderVariant",
    "MAX_CONTENT_BYTES",
    "MAX_EXTERNAL_TARGET_LENGTH",
    "MAX_FOOTER_LINK_ENTRIES",
    "MAX_HEADER_NAV_ENTRIES",
    "MAX_INTERNAL_TARGET_LENGTH",
    "MAX_LABEL_LENGTH",
    "MAX_NOTE_LENGTH",
    "RegionEntry",
    "RegionKey",
    "RegionTarget",
    "RegionVariant",
    "REGION_VARIANTS",
    "UpdateGlobalRegionRequest",
    "global_region_content_json",
    "global_region_record_from_row",
    "validate_region_label",
    "validate_region_target",
]

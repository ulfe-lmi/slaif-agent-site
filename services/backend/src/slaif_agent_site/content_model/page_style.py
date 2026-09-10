"""Closed page-style/v1 overrides using the site theme token vocabulary."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

from .theme import (
    ThemeLayout,
    ThemeLayoutPatch,
    ThemePalette,
    ThemePalettePatch,
    ThemeRecord,
    ThemeShape,
    ThemeShapePatch,
    ThemeTypography,
    ThemeTypographyPatch,
)

PAGE_STYLE_SCHEMA_VERSION: Literal["page-style/v1"] = "page-style/v1"
ThemeTokenKey = Literal[
    "palette.preset",
    "typography.family",
    "typography.scale",
    "typography.weight",
    "layout.content_width",
    "layout.spacing",
    "layout.grid_gap",
    "shape.radius",
    "shape.shadow",
]


class PageStyleOverrides(BaseModel):
    """Typed raw state; omitted groups mean that group inherits the site theme."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    palette: ThemePalettePatch | None = None
    typography: ThemeTypographyPatch | None = None
    layout: ThemeLayoutPatch | None = None
    shape: ThemeShapePatch | None = None

    @model_serializer(mode="plain")
    def serialize(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name in ("palette", "typography", "layout", "shape"):
            value = getattr(self, name)
            if value is not None:
                result[name] = value.model_dump(
                    mode="json", exclude_unset=True, exclude_none=True
                )
        return result


class UpdatePageStyleRequest(BaseModel):
    """Partial page-owned overrides and explicit reset-to-inherit operations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    palette: ThemePalettePatch | None = None
    typography: ThemeTypographyPatch | None = None
    layout: ThemeLayoutPatch | None = None
    shape: ThemeShapePatch | None = None
    reset_tokens: tuple[ThemeTokenKey, ...] = ()
    expected_row_version: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_operation(self) -> UpdatePageStyleRequest:
        groups = ("palette", "typography", "layout", "shape")
        for name in groups:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("page style group cannot be null")
        if len(set(self.reset_tokens)) != len(self.reset_tokens):
            raise ValueError("page style reset_tokens must be unique")
        selected: set[str] = set()
        for name in groups:
            value = getattr(self, name)
            if value is not None:
                selected.update(f"{name}.{key}" for key in value.model_fields_set)
        overlap = selected.intersection(self.reset_tokens)
        if overlap:
            raise ValueError("page style token cannot be updated and reset together")
        if not selected and not self.reset_tokens:
            raise ValueError("page style update must select at least one token")
        return self


class AgentUpdatePageStyleRequest(UpdatePageStyleRequest):
    expected_row_version: int = Field(gt=0)


class PageStyleRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    page_id: UUID
    site_id: UUID
    schema_version: Literal["page-style/v1"]
    row_version: int = Field(gt=0)
    overrides: PageStyleOverrides
    resolved: ThemeRecord
    created_at: datetime
    updated_at: datetime


class AgentPageStyleMutationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    record: PageStyleRecord
    operation_id: UUID
    action: Literal["PAGE_STYLE_UPDATED"] | None = None


def page_style_patch_groups(
    request: UpdatePageStyleRequest,
) -> dict[str, dict[str, Any] | None]:
    return {
        name: (
            getattr(request, name).model_dump(
                mode="json", exclude_unset=True, exclude_none=True
            )
            if getattr(request, name) is not None
            else None
        )
        for name in ("palette", "typography", "layout", "shape")
    }


def page_style_patch_json(request: UpdatePageStyleRequest, name: str) -> str | None:
    import json

    value = page_style_patch_groups(request)[name]
    return json.dumps(value, sort_keys=True) if value is not None else None


def page_style_record_from_row(row: Any) -> PageStyleRecord:
    import json

    if len(row) < 9:
        raise ValueError("page style row shape is incomplete")

    def decoded(value: Any) -> Any:
        return json.loads(value) if isinstance(value, str) else value

    return PageStyleRecord(
        id=row[0],
        page_id=row[1],
        site_id=row[2],
        schema_version=row[3],
        row_version=row[4],
        overrides=PageStyleOverrides.model_validate(decoded(row[5])),
        resolved=ThemeRecord.model_validate(decoded(row[6])),
        created_at=row[7],
        updated_at=row[8],
    )


__all__ = [
    "AgentPageStyleMutationResponse",
    "AgentUpdatePageStyleRequest",
    "PAGE_STYLE_SCHEMA_VERSION",
    "PageStyleOverrides",
    "PageStyleRecord",
    "ThemeTokenKey",
    "UpdatePageStyleRequest",
    "page_style_patch_groups",
    "page_style_patch_json",
    "page_style_record_from_row",
    "ThemeLayout",
    "ThemePalette",
    "ThemeShape",
    "ThemeTypography",
]

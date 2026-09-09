"""Closed theme-schema/v1 models and validation shared by Editor and Agent."""

from __future__ import annotations

import copy
import json
from datetime import datetime
from typing import Any, Literal, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

THEME_SCHEMA_VERSION: Literal["theme-schema/v1"] = "theme-schema/v1"
THEME_RENDERER_VERSION: Literal["renderer-v1"] = "renderer-v1"
THEME_RESPONSIVE_LABELS = ("desktop", "tablet", "mobile")

ThemePalettePreset = Literal["ocean", "meadow", "ember"]
ThemeTypographyFamily = Literal["system", "serif", "mono"]
ThemeTypographyScale = Literal["compact", "balanced", "spacious"]
ThemeTypographyWeight = Literal["regular", "medium", "bold"]
ThemeLayoutWidth = Literal["sm", "md", "lg", "xl"]
ThemeSpacingToken = Literal["sm", "md", "lg"]
ThemeRadiusToken = Literal["none", "sm", "md", "lg", "full"]
ThemeShadowToken = Literal["none", "sm", "md", "lg"]

THEME_PALETTE_PRESETS = ("ocean", "meadow", "ember")
THEME_TYPOGRAPHY_FAMILIES = ("system", "serif", "mono")
THEME_TOKEN_KEYS = (
    "palette.preset",
    "typography.family",
    "typography.scale",
    "typography.weight",
    "layout.content_width",
    "layout.spacing",
    "layout.grid_gap",
    "shape.radius",
    "shape.shadow",
)
THEME_RESOURCE_CONSTRAINT_KEYS = (
    "allowed_theme_palette_presets",
    "allowed_theme_typography_families",
    "allowed_theme_tokens",
)


class ThemePalette(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    preset: ThemePalettePreset


class ThemeTypography(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family: ThemeTypographyFamily
    scale: ThemeTypographyScale
    weight: ThemeTypographyWeight


class ThemeLayout(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    content_width: ThemeLayoutWidth
    spacing: ThemeSpacingToken
    grid_gap: ThemeSpacingToken


class ThemeShape(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    radius: ThemeRadiusToken
    shadow: ThemeShadowToken


class ThemePalettePatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    preset: ThemePalettePreset | None = None

    @model_validator(mode="after")
    def reject_null(self) -> ThemePalettePatch:
        if "preset" in self.model_fields_set and self.preset is None:
            raise ValueError("theme token cannot be null")
        return self


class ThemeTypographyPatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    family: ThemeTypographyFamily | None = None
    scale: ThemeTypographyScale | None = None
    weight: ThemeTypographyWeight | None = None

    @model_validator(mode="after")
    def reject_null(self) -> ThemeTypographyPatch:
        if any(
            name in self.model_fields_set and getattr(self, name) is None
            for name in ("family", "scale", "weight")
        ):
            raise ValueError("theme token cannot be null")
        return self


class ThemeLayoutPatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    content_width: ThemeLayoutWidth | None = None
    spacing: ThemeSpacingToken | None = None
    grid_gap: ThemeSpacingToken | None = None

    @model_validator(mode="after")
    def reject_null(self) -> ThemeLayoutPatch:
        if any(
            name in self.model_fields_set and getattr(self, name) is None
            for name in ("content_width", "spacing", "grid_gap")
        ):
            raise ValueError("theme token cannot be null")
        return self


class ThemeShapePatch(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    radius: ThemeRadiusToken | None = None
    shadow: ThemeShadowToken | None = None

    @model_validator(mode="after")
    def reject_null(self) -> ThemeShapePatch:
        if any(
            name in self.model_fields_set and getattr(self, name) is None
            for name in ("radius", "shadow")
        ):
            raise ValueError("theme token cannot be null")
        return self


def _patch_has_values(value: BaseModel | None) -> bool:
    return value is not None and bool(value.model_fields_set)


class UpdateThemeRequest(BaseModel):
    """Partial normalized theme update for the human Editor surface."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    palette: ThemePalettePatch | None = None
    typography: ThemeTypographyPatch | None = None
    layout: ThemeLayoutPatch | None = None
    shape: ThemeShapePatch | None = None

    @model_validator(mode="after")
    def require_token(self) -> UpdateThemeRequest:
        if not any(
            _patch_has_values(value)
            for value in (self.palette, self.typography, self.layout, self.shape)
        ):
            raise ValueError("theme update must select at least one token")
        return self


class AgentUpdateThemeRequest(UpdateThemeRequest):
    expected_row_version: int = Field(gt=0)


class ThemeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    site_id: UUID
    schema_version: Literal["theme-schema/v1"]
    renderer_version: Literal["renderer-v1"]
    row_version: int = Field(gt=0)
    palette: ThemePalette
    typography: ThemeTypography
    layout: ThemeLayout
    shape: ThemeShape
    created_at: datetime
    updated_at: datetime


class ThemeSchemaToken(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: Literal["enum"]
    values: tuple[str, ...]
    default: str
    accessibility_class: Literal["AA"]
    responsive: Literal[False]


class ThemeSchemaGroup(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: Literal["palette", "typography", "layout", "shape"]
    tokens: tuple[ThemeSchemaToken, ...]


class AgentThemeSchemaResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["theme-schema/v1"]
    renderer_version: Literal["renderer-v1"]
    compatibility_versions: tuple[str, ...]
    responsive: Literal[False]
    responsive_labels: tuple[Literal["desktop", "tablet", "mobile"], ...]
    groups: tuple[ThemeSchemaGroup, ...]


class AgentThemeMutationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    record: ThemeRecord
    operation_id: UUID
    action: Literal["THEME_UPDATED"] | None = None


THEME_DEFAULT_PALETTE = {"preset": "ocean"}
THEME_DEFAULT_TYPOGRAPHY = {
    "family": "system",
    "scale": "balanced",
    "weight": "regular",
}
THEME_DEFAULT_LAYOUT = {"content_width": "md", "spacing": "md", "grid_gap": "md"}
THEME_DEFAULT_SHAPE = {"radius": "md", "shadow": "sm"}

_THEME_SCHEMA_DOCUMENT: dict[str, Any] = {
    "version": THEME_SCHEMA_VERSION,
    "renderer_version": THEME_RENDERER_VERSION,
    "compatibility_versions": [THEME_SCHEMA_VERSION, THEME_RENDERER_VERSION],
    "responsive": False,
    "responsive_labels": list(THEME_RESPONSIVE_LABELS),
    "groups": [
        {
            "name": "palette",
            "tokens": [
                {
                    "name": "preset",
                    "type": "enum",
                    "values": list(THEME_PALETTE_PRESETS),
                    "default": "ocean",
                    "accessibility_class": "AA",
                    "responsive": False,
                }
            ],
        },
        {
            "name": "typography",
            "tokens": [
                {
                    "name": "family",
                    "type": "enum",
                    "values": list(THEME_TYPOGRAPHY_FAMILIES),
                    "default": "system",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
                {
                    "name": "scale",
                    "type": "enum",
                    "values": ["compact", "balanced", "spacious"],
                    "default": "balanced",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
                {
                    "name": "weight",
                    "type": "enum",
                    "values": ["regular", "medium", "bold"],
                    "default": "regular",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
            ],
        },
        {
            "name": "layout",
            "tokens": [
                {
                    "name": "content_width",
                    "type": "enum",
                    "values": ["sm", "md", "lg", "xl"],
                    "default": "md",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
                {
                    "name": "spacing",
                    "type": "enum",
                    "values": ["sm", "md", "lg"],
                    "default": "md",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
                {
                    "name": "grid_gap",
                    "type": "enum",
                    "values": ["sm", "md", "lg"],
                    "default": "md",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
            ],
        },
        {
            "name": "shape",
            "tokens": [
                {
                    "name": "radius",
                    "type": "enum",
                    "values": ["none", "sm", "md", "lg", "full"],
                    "default": "md",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
                {
                    "name": "shadow",
                    "type": "enum",
                    "values": ["none", "sm", "md", "lg"],
                    "default": "sm",
                    "accessibility_class": "AA",
                    "responsive": False,
                },
            ],
        },
    ],
}


def theme_schema_document() -> dict[str, Any]:
    return copy.deepcopy(_THEME_SCHEMA_DOCUMENT)


def theme_defaults(site_id: UUID, timestamp: datetime) -> ThemeRecord:
    return ThemeRecord(
        id=site_id,
        site_id=site_id,
        schema_version=THEME_SCHEMA_VERSION,
        renderer_version=THEME_RENDERER_VERSION,
        row_version=1,
        palette=ThemePalette.model_validate(THEME_DEFAULT_PALETTE),
        typography=ThemeTypography.model_validate(THEME_DEFAULT_TYPOGRAPHY),
        layout=ThemeLayout.model_validate(THEME_DEFAULT_LAYOUT),
        shape=ThemeShape.model_validate(THEME_DEFAULT_SHAPE),
        created_at=timestamp,
        updated_at=timestamp,
    )


def merge_theme_patch(record: ThemeRecord, patch: UpdateThemeRequest) -> ThemeRecord:
    groups: dict[str, dict[str, Any]] = {
        "palette": record.palette.model_dump(),
        "typography": record.typography.model_dump(),
        "layout": record.layout.model_dump(),
        "shape": record.shape.model_dump(),
    }
    for name in ("palette", "typography", "layout", "shape"):
        value = getattr(patch, name)
        if value is not None:
            groups[name].update(value.model_dump(exclude_unset=True, exclude_none=True))
    return record.model_copy(
        update={
            "palette": ThemePalette.model_validate(groups["palette"]),
            "typography": ThemeTypography.model_validate(groups["typography"]),
            "layout": ThemeLayout.model_validate(groups["layout"]),
            "shape": ThemeShape.model_validate(groups["shape"]),
        }
    )


def theme_patch_groups(patch: UpdateThemeRequest) -> dict[str, dict[str, Any] | None]:
    return {
        name: (
            getattr(patch, name).model_dump(exclude_unset=True, exclude_none=True)
            if getattr(patch, name) is not None
            else None
        )
        for name in ("palette", "typography", "layout", "shape")
    }


def validate_theme_resource_constraints(constraints: dict[str, Any]) -> None:
    """Validate the optional human-issued theme allowlists."""
    for key in THEME_RESOURCE_CONSTRAINT_KEYS:
        value = constraints.get(key)
        if value is None:
            continue
        if (
            not isinstance(value, list)
            or len(value) > len(THEME_TOKEN_KEYS)
            or any(not isinstance(item, str) or not item for item in value)
            or len(set(value)) != len(value)
        ):
            raise ValueError("theme resource constraint is malformed")
    palette = constraints.get("allowed_theme_palette_presets")
    if palette is not None and any(
        item not in THEME_PALETTE_PRESETS for item in palette
    ):
        raise ValueError("theme palette resource constraint is malformed")
    families = constraints.get("allowed_theme_typography_families")
    if families is not None and any(
        item not in THEME_TYPOGRAPHY_FAMILIES for item in families
    ):
        raise ValueError("theme typography resource constraint is malformed")
    tokens = constraints.get("allowed_theme_tokens")
    if tokens is not None and any(item not in THEME_TOKEN_KEYS for item in tokens):
        raise ValueError("theme token resource constraint is malformed")


def theme_patch_json(patch: UpdateThemeRequest, name: str) -> str | None:
    value = theme_patch_groups(patch)[name]
    return json.dumps(value, sort_keys=True) if value is not None else None


def theme_record_from_row(row: Any) -> ThemeRecord:
    """Decode the stable Agent/Render theme row shape."""

    def decoded(value: Any) -> Any:
        return json.loads(value) if isinstance(value, str) else value

    if len(row) < 11:
        raise ValueError("theme row shape is incomplete")
    return ThemeRecord(
        id=row[0],
        site_id=row[1],
        schema_version=cast(Literal["theme-schema/v1"], row[2]),
        renderer_version=cast(Literal["renderer-v1"], row[3]),
        row_version=row[4],
        palette=decoded(row[5]),
        typography=decoded(row[6]),
        layout=decoded(row[7]),
        shape=decoded(row[8]),
        created_at=row[9],
        updated_at=row[10],
    )


__all__ = [
    "AgentThemeMutationResponse",
    "AgentThemeSchemaResponse",
    "AgentUpdateThemeRequest",
    "THEME_DEFAULT_LAYOUT",
    "THEME_DEFAULT_PALETTE",
    "THEME_DEFAULT_SHAPE",
    "THEME_DEFAULT_TYPOGRAPHY",
    "THEME_PALETTE_PRESETS",
    "THEME_RENDERER_VERSION",
    "THEME_RESOURCE_CONSTRAINT_KEYS",
    "THEME_SCHEMA_VERSION",
    "THEME_TOKEN_KEYS",
    "THEME_TYPOGRAPHY_FAMILIES",
    "ThemeLayout",
    "ThemeLayoutPatch",
    "ThemePalette",
    "ThemePalettePatch",
    "ThemeRecord",
    "ThemeShape",
    "ThemeShapePatch",
    "ThemeTypography",
    "ThemeTypographyPatch",
    "UpdateThemeRequest",
    "merge_theme_patch",
    "theme_defaults",
    "theme_patch_groups",
    "theme_patch_json",
    "theme_record_from_row",
    "theme_schema_document",
    "validate_theme_resource_constraints",
]

"""Agent API capability authentication and request models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..browser_contracts import BrowserCapabilityLimits
from ..content_model.primitives import FieldPrimitive
from ..content_model.site_data_validators import (
    validate_internal_route,
    validate_locale_tag,
)


class AgentCapabilityContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    capability_id: UUID
    site_id: UUID
    workspace_id: UUID
    delegator_id: UUID
    scopes: frozenset[str]
    created_at: datetime
    expires_at: datetime
    browser_limits: BrowserCapabilityLimits = Field(
        default_factory=BrowserCapabilityLimits
    )
    resource_constraints: dict[str, Any] = Field(default_factory=dict)
    source_origins: tuple[str, ...] = ()
    request_quota: int = 0
    mutation_quota: int = 0
    delete_quota: int = 0
    upload_quota: int = 0

    @model_validator(mode="after")
    def validate_resource_constraints(self) -> AgentCapabilityContext:
        allowed = {
            "allowed_type_ids",
            "allowed_type_keys",
            "allowed_component_types",
            "allowed_component_variants",
            "max_content_types",
            "max_fields_per_type",
            "max_components_per_page",
            "max_component_depth",
            "max_visible_components",
            "delete_enabled",
            "max_deletes",
            "allowed_locales",
            "route_prefix",
            "allowed_page_root_ids",
            "max_visible_pages",
            "max_page_depth",
            "allowed_navigation_keys",
            "allowed_navigation_ids",
            "max_visible_locales",
            "max_visible_navigations",
            "max_visible_navigation_items",
            "max_navigation_depth",
            "max_visible_redirects",
            "responsive_design_enabled",
        }
        unknown = set(self.resource_constraints) - allowed
        if unknown:
            raise ValueError("unknown resource constraint")
        constraints = self.resource_constraints
        for key in (
            "allowed_type_ids",
            "allowed_type_keys",
            "allowed_component_types",
            "allowed_component_variants",
        ):
            value = constraints.get(key)
            if value is not None and (
                not isinstance(value, list)
                or len(value) > 256
                or any(not isinstance(item, str) or not item for item in value)
            ):
                raise ValueError("resource allowlist is malformed")
        allowed_locales = constraints.get("allowed_locales")
        if allowed_locales is not None:
            if (
                not isinstance(allowed_locales, list)
                or len(allowed_locales) > 64
                or any(
                    not isinstance(item, str) or not item for item in allowed_locales
                )
            ):
                raise ValueError("locale allowlist is malformed")
            try:
                for locale in allowed_locales:
                    validate_locale_tag(locale)
            except ValueError:
                raise ValueError("locale allowlist is malformed") from None
        for key in ("allowed_navigation_keys", "allowed_navigation_ids"):
            value = constraints.get(key)
            if value is not None and (
                not isinstance(value, list)
                or len(value) > 256
                or any(not isinstance(item, str) or not item for item in value)
            ):
                raise ValueError("navigation allowlist is malformed")
        allowed_navigation_ids = constraints.get("allowed_navigation_ids")
        if allowed_navigation_ids is not None:
            try:
                for navigation_id in allowed_navigation_ids:
                    UUID(navigation_id)
            except (TypeError, ValueError):
                raise ValueError("navigation allowlist is malformed") from None
        allowed_page_roots = constraints.get("allowed_page_root_ids")
        if allowed_page_roots is not None:
            if (
                not isinstance(allowed_page_roots, list)
                or len(allowed_page_roots) > 256
                or any(
                    not isinstance(item, str) or not item for item in allowed_page_roots
                )
            ):
                raise ValueError("page-root allowlist is malformed")
            try:
                for page_id in allowed_page_roots:
                    UUID(page_id)
            except (TypeError, ValueError):
                raise ValueError("page-root allowlist is malformed") from None
        route_prefix = constraints.get("route_prefix")
        if route_prefix is not None:
            if not isinstance(route_prefix, str) or len(route_prefix) > 512:
                raise ValueError("route prefix is malformed")
            try:
                validate_internal_route(route_prefix)
            except ValueError:
                raise ValueError("route prefix is malformed") from None
        for key in (
            "max_content_types",
            "max_fields_per_type",
            "max_components_per_page",
            "max_component_depth",
            "max_visible_components",
            "max_deletes",
            "max_visible_pages",
            "max_page_depth",
            "max_visible_locales",
            "max_visible_navigations",
            "max_visible_navigation_items",
            "max_navigation_depth",
            "max_visible_redirects",
        ):
            value = constraints.get(key)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise ValueError("resource maximum is malformed")
        enabled = constraints.get("delete_enabled")
        if enabled is not None and not isinstance(enabled, bool):
            raise ValueError("delete_enabled is malformed")
        responsive_enabled = constraints.get("responsive_design_enabled")
        if responsive_enabled is not None and not isinstance(responsive_enabled, bool):
            raise ValueError("responsive design setting is malformed")
        return self


class AgentDiscoveryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_id: UUID
    workspace_id: UUID
    scopes: tuple[str, ...]
    component_catalog_version: str
    composition_schema_version: str
    content_model_schema_version: str
    resource_constraints: dict[str, Any] = Field(default_factory=dict)
    source_origins: tuple[str, ...] = ()
    request_quota: int = 0
    mutation_quota: int = 0
    delete_quota: int = 0
    upload_quota: int = 0


class AgentComponentSchemaNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["string", "number", "boolean", "enum", "reference", "object", "array"]
    required: bool | tuple[str, ...] | None = None
    enum_values: tuple[str, ...] | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    min_items: int | None = None
    max_items: int | None = None
    max_length: int | None = None
    format: Literal["uuid"] | None = None
    properties: dict[str, AgentComponentSchemaNode] | None = None
    additional_properties: bool | None = None
    items: AgentComponentSchemaNode | None = None


class AgentComponentPropDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["string", "number", "boolean", "enum", "reference", "object", "array"]
    required: bool
    enum_values: tuple[str, ...] | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    min_items: int | None = None
    max_items: int | None = None
    localized: bool | None = None
    authority: Literal["content", "design"]
    max_length: int | None = None
    format: Literal["uuid"] | None = None
    schema_: AgentComponentSchemaNode | None = Field(default=None, alias="schema")


class AgentComponentDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str
    category: Literal["layout", "basic", "data", "institutional", "global"]
    schema_version: str
    allowed_slots: tuple[str, ...]
    max_children: int
    binding_kind: Literal["none", "collection_view", "media_asset"]
    authority_class: Literal["content", "structure", "global"]
    props: dict[str, AgentComponentPropDescriptor]


class AgentComponentCatalogResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["catalog-v1"]
    composition_schema_version: Literal["site-composition/v1"]
    components: tuple[AgentComponentDescriptor, ...]


class AgentDesignPropertyDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    type: Literal["enum", "number"]
    values: tuple[str, ...] | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    integer: Literal[True] | None = None
    default: str | int | float
    required: bool
    responsive: Literal[True]
    scope: Literal["component-props:write", "component-variant:write", "layout:write"]
    token: str


class AgentDesignComponentDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str
    variants: tuple[str, ...]
    properties: tuple[AgentDesignPropertyDescriptor, ...]


class AgentDesignTokenSet(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    spacing: tuple[str, ...]
    gap: tuple[str, ...]
    width: tuple[str, ...]
    alignment: tuple[str, ...]
    columns: tuple[int, ...]
    radius: tuple[str, ...]
    shadow: tuple[str, ...]
    aspect_ratio: tuple[str, ...]


class AgentDesignSystemResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["design-system/v1"]
    catalog_version: Literal["catalog-v1"]
    composition_schema_version: Literal["site-composition/v1"]
    renderer_version: Literal["renderer-v1"]
    responsive_labels: tuple[Literal["desktop", "tablet", "mobile"], ...]
    responsive_scope: Literal["responsive-design:write"]
    responsive_fallback: tuple[Literal["desktop", "tablet", "mobile"], ...]
    tokens: AgentDesignTokenSet
    components: tuple[AgentDesignComponentDescriptor, ...]


class AgentPermissionsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_id: UUID
    workspace_id: UUID
    scopes: tuple[str, ...]


class AgentFieldPrimitiveDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    primitive: FieldPrimitive
    executable: Literal[False] = False


class AgentErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    error_code: str
    message: str
    request_id: str | None = None
    operation_id: UUID | None = None


class AgentMutationResponse(BaseModel):
    """One semantic record and the server-selected COW operation identity."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    record: dict[str, object]
    operation_id: UUID
    action: str | None = None


class AgentDeleteRequest(BaseModel):
    """Positive optimistic-lock token for Agent destructive mutations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_row_version: int = Field(gt=0)

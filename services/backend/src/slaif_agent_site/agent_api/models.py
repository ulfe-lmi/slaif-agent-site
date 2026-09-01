"""Agent API capability authentication and request models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..browser_contracts import BrowserCapabilityLimits


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
            "max_content_types",
            "max_fields_per_type",
            "delete_enabled",
            "max_deletes",
        }
        unknown = set(self.resource_constraints) - allowed
        if unknown:
            raise ValueError("unknown resource constraint")
        constraints = self.resource_constraints
        for key in ("allowed_type_ids", "allowed_type_keys"):
            value = constraints.get(key)
            if value is not None and (
                not isinstance(value, list)
                or len(value) > 256
                or any(not isinstance(item, str) or not item for item in value)
            ):
                raise ValueError("resource allowlist is malformed")
        for key in ("max_content_types", "max_fields_per_type", "max_deletes"):
            value = constraints.get(key)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value < 0
            ):
                raise ValueError("resource maximum is malformed")
        enabled = constraints.get("delete_enabled")
        if enabled is not None and not isinstance(enabled, bool):
            raise ValueError("delete_enabled is malformed")
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

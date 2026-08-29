"""Agent API capability authentication and request models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    request_quota: int = 0
    mutation_quota: int = 0
    delete_quota: int = 0
    upload_quota: int = 0


class AgentDiscoveryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_id: UUID
    workspace_id: UUID
    scopes: tuple[str, ...]
    component_catalog_version: str
    composition_schema_version: str
    content_model_schema_version: str


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

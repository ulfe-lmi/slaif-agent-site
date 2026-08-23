"""Agent API capability authentication and request models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AgentCapabilityContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    capability_id: UUID
    site_id: UUID
    workspace_id: UUID
    delegator_id: UUID
    scopes: frozenset[str]
    created_at: datetime
    expires_at: datetime


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

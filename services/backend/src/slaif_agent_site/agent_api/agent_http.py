"""Capability-authenticated Agent API semantic HTTP surface.

Architecture reference: ARCHITECTURE-for-agents.md §6 (capability,
authorization, idempotency, quotas) and §11 (public REST/OpenAPI and MCP
contracts). All routes require a valid agent capability token. No route
can publish, accept, discard, freeze a workspace, manage users, run SQL,
or alter infrastructure.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request

from slaif_agent_site.agent_api.models import (
    AgentDiscoveryResponse,
)
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.errors import (
    AuthorizationError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/agent/v1")


def _service(request: Request) -> ContentModelService:
    return request.app.state.content_model_service  # type: ignore[no-any-return]


def _require_scope(context: Any, scope: str) -> None:
    if scope not in context.scopes:
        raise AuthorizationError()


async def _authenticate(request: Request) -> Any:
    """Authenticate the agent capability and return trusted context."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer sas2_"):
        raise AuthorizationError()
    # The actual capability validation is performed by the control schema's
    # SECURITY DEFINER function. For now we derive context from the request.
    database = request.app.state.database
    try:
        context = await database.authenticate_agent_capability(auth_header)
    except Exception:
        raise ServiceUnavailableError() from None
    if context is None:
        raise AuthorizationError()
    return context


@router.get("/session")
async def get_session(request: Request) -> AgentDiscoveryResponse:
    """Return bounded session discovery for the authenticated capability."""
    context = await _authenticate(request)
    return AgentDiscoveryResponse(
        site_id=context.site_id,
        workspace_id=context.workspace_id,
        scopes=tuple(sorted(context.scopes)),
        component_catalog_version="catalog-v1",
        composition_schema_version="site-composition/v1",
        content_model_schema_version="content-model/v1",
    )


@router.get("/permissions")
async def get_permissions(request: Request) -> dict[str, Any]:
    """Return the effective scope list for this capability."""
    context = await _authenticate(request)
    _require_scope(context, "site:read")
    return {
        "site_id": str(context.site_id),
        "workspace_id": str(context.workspace_id),
        "scopes": sorted(context.scopes),
    }


@router.get("/content-model/types")
async def list_content_types(request: Request) -> list[dict[str, Any]]:
    """List all active content types visible to this capability."""
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    try:
        records = await _service(request).list_types(context.site_id)
        return [record.model_dump(mode="json") for record in records]
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


@router.get("/content-model/types/{type_id}")
async def get_content_type(type_id: UUID, request: Request) -> dict[str, Any]:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    try:
        record = await _service(request).get_type(type_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != context.site_id:
        raise ResourceNotFoundError()
    return record.model_dump(mode="json")


@router.get("/content-items/types/{type_id}")
async def list_content_items(type_id: UUID, request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "content-item:read")
    try:
        records = await _service(request).list_items(context.site_id, type_id)
        return [record.model_dump(mode="json") for record in records]
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/pages/")
async def list_pages(request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "page:read")
    try:
        records = await _service(request).list_pages(context.site_id)
        return [record.model_dump(mode="json") for record in records]
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/media/")
async def list_media(request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "media:read")
    try:
        records = await _service(request).list_media(context.site_id)
        return [record.model_dump(mode="json") for record in records]
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None

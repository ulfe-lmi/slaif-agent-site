"""Capability-authenticated Agent API semantic HTTP surface.

Architecture reference: ARCHITECTURE-for-agents.md §6 (capability,
authorization, idempotency, quotas) and §11 (public REST/OpenAPI and MCP
contracts). All routes require a valid agent capability token. No route
can publish, accept, discard, freeze a workspace, manage users, run SQL,
or alter infrastructure.
"""

from __future__ import annotations

from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request

from slaif_agent_site.agent_api.models import (
    AgentDiscoveryResponse,
    AgentMutationResponse,
)
from slaif_agent_site.agent_state.mutations import (
    AgentMutationConflictError,
    AgentMutationUnavailableError,
    AgentQuotaExceededError,
    InvalidIdempotencyKeyError,
    MissingIdempotencyKeyError,
    execute_agent_mutation,
    mutation_digest,
    validate_idempotency_key,
)
from slaif_agent_site.agent_state.mutations import (
    IdempotencyMismatchError as DurableIdempotencyMismatchError,
)
from slaif_agent_site.agent_state.reads import (
    AgentRead,
    execute_agent_read,
)
from slaif_agent_site.content_model.composition_models import (
    CreateCompositionNodeRequest,
)
from slaif_agent_site.content_model.item_models import CreateContentItemRequest
from slaif_agent_site.content_model.models import (
    ContentTypeRecord,
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    DeleteDefinitionRequest,
    UpdateContentTypeRequest,
    UpdateFieldDefinitionRequest,
)
from slaif_agent_site.content_model.page_models import CreatePageRequest
from slaif_agent_site.content_model.service import (
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.errors import (
    AuthenticationError,
    AuthorizationError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    QuotaExceededError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/agent/v1")


def _require_scope(context: Any, scope: str) -> None:
    if scope not in context.scopes:
        raise AuthorizationError()


async def _authenticate(request: Request) -> Any:
    """Authenticate the agent capability and return trusted context."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer sas2_"):
        raise AuthenticationError()
    # The control-owned database validates the token and lifecycle state before
    # returning a trusted, immutable capability context.
    database = request.app.state.database
    try:
        context = await database.authenticate_agent_capability(auth_header)
    except Exception:
        raise ServiceUnavailableError() from None
    if context is None:
        raise AuthenticationError()
    consume = getattr(database, "consume_agent_quota", None)
    if consume is None:
        raise ServiceUnavailableError()
    try:
        if not await consume(context, "request"):
            raise QuotaExceededError()
    except QuotaExceededError:
        raise
    except Exception:
        raise ServiceUnavailableError() from None
    return context


async def _execute_read(
    request: Request,
    context: Any,
    read: AgentRead,
) -> Any:
    try:
        return await execute_agent_read(
            database=request.app.state.database,
            context=context,
            read=read,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


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
        resource_constraints=context.resource_constraints,
        source_origins=context.source_origins,
        request_quota=context.request_quota,
        mutation_quota=context.mutation_quota,
        delete_quota=context.delete_quota,
        upload_quota=context.upload_quota,
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
    records = await _execute_read(
        request, context, lambda service: service.list_types(context.site_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/content-model/types/{type_id}/fields")
async def list_field_definitions(
    type_id: UUID, request: Request
) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_fields(context.site_id, type_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/content-model/types/{type_id}")
async def get_content_type(type_id: UUID, request: Request) -> dict[str, Any]:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    record = cast(
        ContentTypeRecord,
        await _execute_read(
            request, context, lambda service: service.get_type(context.site_id, type_id)
        ),
    )
    return record.model_dump(mode="json")


@router.get("/content-model/types/{type_id}/fields/{field_id}")
async def get_field_definition(
    type_id: UUID, field_id: UUID, request: Request
) -> dict[str, Any]:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    record = await _execute_read(
        request,
        context,
        lambda service: service.get_field(context.site_id, type_id, field_id),
    )
    return cast(dict[str, Any], record.model_dump(mode="json"))


@router.get("/content-items/types/{type_id}")
async def list_content_items(type_id: UUID, request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "content-item:read")
    records = await _execute_read(
        request, context, lambda service: service.list_items(context.site_id, type_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/pages/")
async def list_pages(request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "page:read")
    records = await _execute_read(
        request, context, lambda service: service.list_pages(context.site_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/pages/{page_id}/components")
async def list_components(page_id: UUID, request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "composition:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_composition(context.site_id, page_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/media/")
async def list_media(request: Request) -> list[dict[str, Any]]:
    context = await _authenticate(request)
    _require_scope(context, "media:read")
    records = await _execute_read(
        request, context, lambda service: service.list_media(context.site_id)
    )
    return [record.model_dump(mode="json") for record in records]


IdempotencyHeader = Annotated[str | None, Header(alias="Idempotency-Key")]


async def _execute_mutation(
    request: Request,
    context: Any,
    body: Any,
    idempotency_key: str | None,
    *,
    resource_type: str,
    mutate: Any,
) -> AgentMutationResponse:
    try:
        key = validate_idempotency_key(idempotency_key)
    except MissingIdempotencyKeyError:
        raise IdempotencyKeyRequiredError() from None
    except InvalidIdempotencyKeyError:
        raise IdempotencyKeyInvalidError() from None
    digest = mutation_digest(
        method=request.method,
        path=request.url.path,
        body=body.model_dump(mode="json"),
    )
    try:
        return await execute_agent_mutation(
            database=request.app.state.database,
            context=context,
            key=key,
            digest=digest,
            mutate=mutate,
            resource_type=resource_type,
        )
    except DurableIdempotencyMismatchError:
        raise IdempotencyMismatchError() from None
    except AgentMutationConflictError:
        raise ResourceConflictError() from None
    except AgentQuotaExceededError:
        raise QuotaExceededError() from None
    except AgentMutationUnavailableError:
        raise ServiceUnavailableError() from None
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.post("/content-model/types", status_code=201)
async def create_content_type(
    request: Request,
    body: CreateContentTypeRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    """Create a content type (L4 scope required)."""
    context = await _authenticate(request)
    _require_scope(context, "content-model:create")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_type",
        mutate=lambda service: service.create_type(context.site_id, body),
    )


@router.post("/content-model/types/{type_id}/fields", status_code=201)
async def create_field_definition(
    type_id: UUID,
    request: Request,
    body: CreateFieldDefinitionRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "content-model:create")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="field_definition",
        mutate=lambda service: service.create_field_for_site(
            context.site_id, type_id, body
        ),
    )


@router.patch("/content-model/types/{type_id}")
async def update_content_type(
    type_id: UUID,
    request: Request,
    body: UpdateContentTypeRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "content-model:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_type",
        mutate=lambda service: service.update_type_for_site(
            context.site_id, type_id, body
        ),
    )


@router.patch("/content-model/types/{type_id}/fields/{field_id}")
async def update_field_definition(
    type_id: UUID,
    field_id: UUID,
    request: Request,
    body: UpdateFieldDefinitionRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "field-definition:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="field_definition",
        mutate=lambda service: service.update_field_for_site(
            context.site_id, type_id, field_id, body
        ),
    )


@router.delete("/content-model/types/{type_id}")
async def delete_content_type(
    type_id: UUID,
    request: Request,
    body: DeleteDefinitionRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "content-model:delete")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_type",
        mutate=lambda service: service.delete_type_for_site(
            context.site_id, type_id, body.expected_definition_version
        ),
    )


@router.delete("/content-model/types/{type_id}/fields/{field_id}")
async def delete_field_definition(
    type_id: UUID,
    field_id: UUID,
    request: Request,
    body: DeleteDefinitionRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "field-definition:delete")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="field_definition",
        mutate=lambda service: service.delete_field_for_site(
            context.site_id, type_id, field_id, body.expected_definition_version
        ),
    )


@router.post("/content-items/types/{type_id}", status_code=201)
async def create_content_item(
    type_id: UUID,
    request: Request,
    body: CreateContentItemRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    """Create a content item within this workspace."""
    context = await _authenticate(request)
    _require_scope(context, "content-item:create")
    if body.type_id != type_id:
        raise ResourceNotFoundError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item",
        mutate=lambda service: service.create_item_for_site(
            context.site_id, type_id, body
        ),
    )


@router.post("/pages/", status_code=201)
async def create_page(
    request: Request,
    body: CreatePageRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    """Create a page within this workspace."""
    context = await _authenticate(request)
    _require_scope(context, "page:create")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="page",
        mutate=lambda service: service.create_page_for_site(context.site_id, body),
    )


@router.post("/pages/{page_id}/components", status_code=201)
async def create_component(
    page_id: UUID,
    request: Request,
    body: CreateCompositionNodeRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "component-structure:create")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="composition_node",
        mutate=lambda service: service.add_component_for_site(
            context.site_id, page_id, body
        ),
    )

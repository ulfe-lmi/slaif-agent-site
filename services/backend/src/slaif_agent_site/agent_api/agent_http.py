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
    AgentDeleteRequest,
    AgentDiscoveryResponse,
    AgentFieldPrimitiveDescriptor,
    AgentMutationResponse,
    AgentPermissionsResponse,
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
from slaif_agent_site.authority import ProcessKind
from slaif_agent_site.content_model.composition_models import (
    CompositionNodeRecord,
    CreateCompositionNodeRequest,
)
from slaif_agent_site.content_model.item_models import (
    AgentUpdateContentItemRequest,
    ContentItemRecord,
    CreateContentItemRequest,
    DeleteContentItemRequest,
)
from slaif_agent_site.content_model.media_models import MediaAssetRecord
from slaif_agent_site.content_model.models import (
    ContentTypeRecord,
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    CreateRelationRequest,
    CreateTranslationRequest,
    DeleteDefinitionRequest,
    DeleteTranslationRequest,
    FieldDefinitionRecord,
    RelationRecord,
    TranslationRecord,
    UpdateContentTypeRequest,
    UpdateFieldDefinitionRequest,
    UpdateRelationRequest,
    UpdateTranslationRequest,
)
from slaif_agent_site.content_model.page_models import (
    CreatePageRequest,
    MovePageRequest,
    PageRecord,
    RestorePageRequest,
    UpdatePageRequest,
)
from slaif_agent_site.content_model.primitives import FieldPrimitive
from slaif_agent_site.content_model.service import (
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.content_model.site_data_models import (
    AgentCreateLocaleRequest,
    AgentCreateNavigationItemRequest,
    AgentCreateNavigationRequest,
    AgentCreateRedirectRequest,
    AgentMoveNavigationItemRequest,
    AgentNavigationRecord,
    AgentUpdateLocaleRequest,
    AgentUpdateNavigationItemRequest,
    AgentUpdateNavigationRequest,
    AgentUpdateRedirectRequest,
    LocaleRecord,
    NavigationItemRecord,
    RedirectRecord,
)
from slaif_agent_site.content_model.view_models import (
    CollectionViewRecord,
    CreateCollectionViewRequest,
    UpdateCollectionViewRequest,
)
from slaif_agent_site.control_api.route_policy import conditional_scopes_for_fields
from slaif_agent_site.errors import (
    AuthenticationError,
    AuthorizationError,
    DomainValidationError,
    FieldDependenciesError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    QuotaExceededError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
    TypeDependenciesError,
)

router = APIRouter(prefix="/api/agent/v1")


def _require_scope(context: Any, scope: str) -> None:
    if scope not in context.scopes:
        raise AuthorizationError()


def _enforce_resource_constraint(
    context: Any, *, type_id: UUID | None = None, type_key: str | None = None
) -> None:
    """Apply immutable capability resource allowlists before opening COW."""
    constraints = context.resource_constraints
    if not isinstance(constraints, dict):
        return
    allowed_ids = constraints.get("allowed_type_ids")
    if type_id is not None and isinstance(allowed_ids, (list, tuple, set)):
        if str(type_id) not in {str(value) for value in allowed_ids}:
            raise AuthorizationError()
    allowed_keys = constraints.get("allowed_type_keys")
    if type_key is not None and isinstance(allowed_keys, (list, tuple, set)):
        if type_key not in {str(value) for value in allowed_keys}:
            raise AuthorizationError()


def _constraint(context: Any, key: str, default: Any = None) -> Any:
    values = context.resource_constraints
    return values.get(key, default) if isinstance(values, dict) else default


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
        if exc.reason is ContentModelServiceReason.VALIDATION:
            raise AuthorizationError() from None
        if exc.reason is ContentModelServiceReason.AUTHORIZATION:
            raise AuthorizationError() from None
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
async def get_permissions(request: Request) -> AgentPermissionsResponse:
    """Return the effective scope list for this capability."""
    context = await _authenticate(request)
    _require_scope(context, "site:read")
    return AgentPermissionsResponse(
        site_id=context.site_id,
        workspace_id=context.workspace_id,
        scopes=tuple(sorted(context.scopes)),
    )


@router.get("/content-model/primitives")
async def list_field_primitives(
    request: Request,
) -> tuple[AgentFieldPrimitiveDescriptor, ...]:
    context = await _authenticate(request)
    _require_scope(context, "validation:read")
    return tuple(
        AgentFieldPrimitiveDescriptor(primitive=primitive)
        for primitive in FieldPrimitive
    )


@router.get("/content-model/types")
async def list_content_types(request: Request) -> list[ContentTypeRecord]:
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
) -> list[FieldDefinitionRecord]:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    _enforce_resource_constraint(context, type_id=type_id)
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_fields(context.site_id, type_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/content-model/types/{type_id}")
async def get_content_type(type_id: UUID, request: Request) -> ContentTypeRecord:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    _enforce_resource_constraint(context, type_id=type_id)
    record = cast(
        ContentTypeRecord,
        await _execute_read(
            request, context, lambda service: service.get_type(context.site_id, type_id)
        ),
    )
    return cast(ContentTypeRecord, record.model_dump(mode="json"))


@router.get("/content-model/types/{type_id}/fields/{field_id}")
async def get_field_definition(
    type_id: UUID, field_id: UUID, request: Request
) -> FieldDefinitionRecord:
    context = await _authenticate(request)
    _require_scope(context, "content-model:read")
    _enforce_resource_constraint(context, type_id=type_id)
    record = await _execute_read(
        request,
        context,
        lambda service: service.get_field(context.site_id, type_id, field_id),
    )
    return cast(FieldDefinitionRecord, record.model_dump(mode="json"))


@router.get("/content-items/types/{type_id}")
async def list_content_items(
    type_id: UUID, request: Request
) -> list[ContentItemRecord]:
    context = await _authenticate(request)
    _require_scope(context, "content-item:read")
    _enforce_resource_constraint(context, type_id=type_id)
    records = await _execute_read(
        request, context, lambda service: service.list_items(context.site_id, type_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/pages")
@router.get("/pages/")
async def list_pages(request: Request) -> list[PageRecord]:
    context = await _authenticate(request)
    _require_scope(context, "page:read")
    records = await _execute_read(
        request, context, lambda service: service.list_pages(context.site_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/pages/{page_id}")
async def get_page(page_id: UUID, request: Request) -> PageRecord:
    context = await _authenticate(request)
    _require_scope(context, "page:read")
    record = await _execute_read(
        request, context, lambda service: service.get_page(context.site_id, page_id)
    )
    return cast(PageRecord, record.model_dump(mode="json"))


@router.get("/locales")
async def list_locales(request: Request) -> list[LocaleRecord]:
    context = await _authenticate(request)
    _require_scope(context, "site:read")
    records = await _execute_read(
        request, context, lambda service: service.list_locales(context.site_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/locales/{locale_id}")
async def get_locale(locale_id: UUID, request: Request) -> LocaleRecord:
    context = await _authenticate(request)
    _require_scope(context, "site:read")
    record = await _execute_read(
        request,
        context,
        lambda service: service.get_locale(context.site_id, locale_id),
    )
    return cast(LocaleRecord, record.model_dump(mode="json"))


@router.get("/redirects")
async def list_redirects(request: Request) -> list[RedirectRecord]:
    context = await _authenticate(request)
    _require_scope(context, "redirect:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_redirects_for_site(context.site_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/redirects/{redirect_id}")
async def get_redirect(redirect_id: UUID, request: Request) -> RedirectRecord:
    context = await _authenticate(request)
    _require_scope(context, "redirect:read")
    record = await _execute_read(
        request,
        context,
        lambda service: service.get_redirect_for_site(context.site_id, redirect_id),
    )
    return cast(RedirectRecord, record.model_dump(mode="json"))


@router.get("/navigation")
async def list_navigation(request: Request) -> list[AgentNavigationRecord]:
    context = await _authenticate(request)
    _require_scope(context, "navigation:read")
    records = await _execute_read(
        request, context, lambda service: service.list_navigation(context.site_id)
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/navigation/{navigation_id}/items")
async def list_navigation_items(
    navigation_id: UUID, request: Request
) -> list[NavigationItemRecord]:
    context = await _authenticate(request)
    _require_scope(context, "navigation:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_navigation_items(context.site_id, navigation_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/navigation/{navigation_id}")
async def get_navigation(
    navigation_id: UUID, request: Request
) -> AgentNavigationRecord:
    context = await _authenticate(request)
    _require_scope(context, "navigation:read")
    record = await _execute_read(
        request,
        context,
        lambda service: service.get_navigation(context.site_id, navigation_id),
    )
    return cast(AgentNavigationRecord, record.model_dump(mode="json"))


@router.get("/navigation-items/{item_id}")
async def get_navigation_item(item_id: UUID, request: Request) -> NavigationItemRecord:
    context = await _authenticate(request)
    _require_scope(context, "navigation:read")
    record = await _execute_read(
        request,
        context,
        lambda service: service.get_navigation_item(context.site_id, item_id),
    )
    return cast(NavigationItemRecord, record.model_dump(mode="json"))


@router.get("/pages/{page_id}/components")
async def list_components(
    page_id: UUID, request: Request
) -> list[CompositionNodeRecord]:
    context = await _authenticate(request)
    _require_scope(context, "composition:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_composition(context.site_id, page_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/media/")
async def list_media(request: Request) -> list[MediaAssetRecord]:
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
    status_code: int = 201,
    quota_kind: str = "mutation",
    action: str | None = None,
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
            status_code=status_code,
            quota_kind=quota_kind,
            action=action,
            method=request.method,
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
        if exc.reason is ContentModelServiceReason.VALIDATION:
            if exc.code == "FIELD_DEPENDENCIES":
                raise FieldDependenciesError() from None
            if exc.code == "TYPE_DEPENDENCIES":
                raise TypeDependenciesError() from None
            if exc.code == "PAGE_ROUTE_CONFLICT":
                raise ResourceConflictError() from None
            if exc.code in {
                "LOCALE_REFERENCED",
                "LOCALE_DEFAULT_REQUIRED",
                "NAVIGATION_CHILDREN",
                "NAVIGATION_KEY_CONFLICT",
                "NAVIGATION_POSITION_LIMIT",
                "REDIRECT_SOURCE_CONFLICT",
                "REDIRECT_TARGET_DANGLING",
                "REDIRECT_CYCLE",
                "REDIRECT_CHAIN_LIMIT",
                "REDIRECT_DEPENDENCY",
            }:
                raise ResourceConflictError() from None
            if exc.code == "REDIRECT_ROUTE_PREFIX_DENIED":
                raise AuthorizationError() from None
            raise DomainValidationError() from None
        if exc.reason is ContentModelServiceReason.AUTHORIZATION:
            raise AuthorizationError() from None
        if exc.reason is ContentModelServiceReason.QUOTA:
            raise QuotaExceededError() from None
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
    _enforce_resource_constraint(context, type_key=body.key)
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_type",
        action="CONTENT_TYPE_CREATED",
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
    _require_scope(context, "field-definition:create")
    _enforce_resource_constraint(context, type_id=type_id)
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="field_definition",
        action="FIELD_DEFINITION_CREATED",
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
    _enforce_resource_constraint(context, type_id=type_id)
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_type",
        status_code=200,
        action="CONTENT_TYPE_UPDATED",
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
    _enforce_resource_constraint(context, type_id=type_id)
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="field_definition",
        status_code=200,
        action="FIELD_DEFINITION_UPDATED",
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
    _enforce_resource_constraint(context, type_id=type_id)
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_type",
        status_code=200,
        quota_kind="delete",
        action="CONTENT_TYPE_DELETED",
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
    _enforce_resource_constraint(context, type_id=type_id)
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="field_definition",
        status_code=200,
        quota_kind="delete",
        action="FIELD_DEFINITION_DELETED",
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
    _enforce_resource_constraint(context, type_id=type_id)
    if body.type_id != type_id:
        raise ResourceNotFoundError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item",
        action="CONTENT_ITEM_CREATED",
        mutate=lambda service: service.create_item_for_site(
            context.site_id, type_id, body
        ),
    )


@router.get("/content-items/{item_id}")
async def get_content_item(item_id: UUID, request: Request) -> ContentItemRecord:
    context = await _authenticate(request)
    _require_scope(context, "content-item:read")
    record = cast(
        ContentItemRecord,
        await _execute_read(
            request,
            context,
            lambda service: service.get_item(context.site_id, item_id),
        ),
    )
    _enforce_resource_constraint(context, type_id=record.type_id)
    return cast(ContentItemRecord, record.model_dump(mode="json"))


@router.patch("/content-items/{item_id}")
async def update_content_item(
    item_id: UUID,
    request: Request,
    body: AgentUpdateContentItemRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "content-item:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item",
        status_code=200,
        action="CONTENT_ITEM_UPDATED",
        mutate=lambda service: service.update_item_for_site(
            context.site_id, item_id, body
        ),
    )


@router.delete("/content-items/{item_id}")
async def delete_content_item(
    item_id: UUID,
    request: Request,
    body: DeleteContentItemRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "content-item:delete")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item",
        status_code=200,
        quota_kind="delete",
        action="CONTENT_ITEM_DELETED",
        mutate=lambda service: service.delete_item_for_site(
            context.site_id, item_id, body
        ),
    )


@router.get("/content-items/{item_id}/translations")
async def list_content_item_translations(
    item_id: UUID, request: Request
) -> list[TranslationRecord]:
    context = await _authenticate(request)
    _require_scope(context, "translation:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_translations_for_site(context.site_id, item_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/content-items/{item_id}/translations/{translation_id}")
async def get_content_item_translation(
    item_id: UUID, translation_id: UUID, request: Request
) -> TranslationRecord:
    context = await _authenticate(request)
    _require_scope(context, "translation:read")
    record = cast(
        TranslationRecord,
        await _execute_read(
            request,
            context,
            lambda service: service.get_translation_for_site(
                context.site_id, item_id, translation_id
            ),
        ),
    )
    return cast(TranslationRecord, record.model_dump(mode="json"))


@router.post("/content-items/{item_id}/translations", status_code=201)
async def create_content_item_translation(
    item_id: UUID,
    request: Request,
    body: CreateTranslationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "translation:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item_translation",
        action="CONTENT_ITEM_TRANSLATION_CREATED",
        mutate=lambda service: service.create_translation_for_site(
            context.site_id, item_id, body
        ),
    )


@router.patch("/content-items/{item_id}/translations/{translation_id}")
async def update_content_item_translation(
    item_id: UUID,
    translation_id: UUID,
    request: Request,
    body: UpdateTranslationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "translation:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item_translation",
        status_code=200,
        action="CONTENT_ITEM_TRANSLATION_UPDATED",
        mutate=lambda service: service.update_translation_for_site(
            context.site_id, item_id, translation_id, body
        ),
    )


@router.delete("/content-items/{item_id}/translations/{translation_id}")
async def delete_content_item_translation(
    item_id: UUID,
    translation_id: UUID,
    request: Request,
    body: DeleteTranslationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "translation:write")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="content_item_translation",
        status_code=200,
        quota_kind="delete",
        action="CONTENT_ITEM_TRANSLATION_DELETED",
        mutate=lambda service: service.delete_translation_for_site(
            context.site_id, item_id, translation_id, body
        ),
    )


@router.get("/content-items/{item_id}/relations")
async def list_content_item_relations(
    item_id: UUID, request: Request
) -> list[RelationRecord]:
    context = await _authenticate(request)
    _require_scope(context, "content-item:read")
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_relations_for_site(context.site_id, item_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/content-items/{item_id}/relations/{relation_id}")
async def get_content_item_relation(
    item_id: UUID, relation_id: UUID, request: Request
) -> RelationRecord:
    context = await _authenticate(request)
    _require_scope(context, "content-item:read")
    record = cast(
        RelationRecord,
        await _execute_read(
            request,
            context,
            lambda service: service.get_relation_for_site(
                context.site_id, item_id, relation_id
            ),
        ),
    )
    return cast(RelationRecord, record.model_dump(mode="json"))


@router.post("/content-items/{item_id}/relations", status_code=201)
async def create_content_item_relation(
    item_id: UUID,
    request: Request,
    body: CreateRelationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "relationship:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="item_relation",
        action="ITEM_RELATION_CREATED",
        mutate=lambda service: service.create_relation_for_site(
            context.site_id, item_id, body
        ),
    )


@router.patch("/content-items/{item_id}/relations/{relation_id}")
async def update_content_item_relation(
    item_id: UUID,
    relation_id: UUID,
    request: Request,
    body: UpdateRelationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "relationship:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="item_relation",
        status_code=200,
        action="ITEM_RELATION_UPDATED",
        mutate=lambda service: service.update_relation_for_site(
            context.site_id, item_id, relation_id, body
        ),
    )


@router.delete("/content-items/{item_id}/relations/{relation_id}")
async def delete_content_item_relation(
    item_id: UUID,
    relation_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "relationship:write")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="item_relation",
        status_code=200,
        quota_kind="delete",
        action="ITEM_RELATION_DELETED",
        mutate=lambda service: service.delete_relation_for_site(
            context.site_id, item_id, relation_id, body.expected_row_version
        ),
    )


@router.get("/collection-views/types/{type_id}")
async def list_collection_views(
    type_id: UUID, request: Request
) -> list[CollectionViewRecord]:
    context = await _authenticate(request)
    _require_scope(context, "collection-view:read")
    _enforce_resource_constraint(context, type_id=type_id)
    records = await _execute_read(
        request,
        context,
        lambda service: service.list_views_for_site(context.site_id, type_id),
    )
    return [record.model_dump(mode="json") for record in records]


@router.post("/collection-views/types/{type_id}", status_code=201)
async def create_collection_view(
    type_id: UUID,
    request: Request,
    body: CreateCollectionViewRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "collection-view:create")
    _enforce_resource_constraint(context, type_id=type_id)
    if body.type_id != type_id:
        raise ResourceNotFoundError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="collection_view",
        action="COLLECTION_VIEW_CREATED",
        mutate=lambda service: service.create_view_for_site(context.site_id, body),
    )


@router.get("/collection-views/{view_id}")
async def get_collection_view(view_id: UUID, request: Request) -> CollectionViewRecord:
    context = await _authenticate(request)
    _require_scope(context, "collection-view:read")
    record = cast(
        CollectionViewRecord,
        await _execute_read(
            request,
            context,
            lambda service: service.get_view_for_site(context.site_id, view_id),
        ),
    )
    _enforce_resource_constraint(context, type_id=record.type_id)
    return cast(CollectionViewRecord, record.model_dump(mode="json"))


@router.patch("/collection-views/{view_id}")
async def update_collection_view(
    view_id: UUID,
    request: Request,
    body: UpdateCollectionViewRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "collection-view:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="collection_view",
        status_code=200,
        action="COLLECTION_VIEW_UPDATED",
        mutate=lambda service: service.update_view_for_site(
            context.site_id, view_id, body
        ),
    )


@router.delete("/collection-views/{view_id}")
async def delete_collection_view(
    view_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "collection-view:delete")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="collection_view",
        status_code=200,
        quota_kind="delete",
        action="COLLECTION_VIEW_DELETED",
        mutate=lambda service: service.delete_view_for_site(
            context.site_id, view_id, body.expected_row_version
        ),
    )


@router.post("/locales", status_code=201)
async def create_locale(
    request: Request,
    body: AgentCreateLocaleRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "locale:configure")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="locale",
        action="LOCALE_CREATED",
        mutate=lambda service: service.create_locale(context.site_id, body),
    )


@router.patch("/locales/{locale_id}")
async def update_locale(
    locale_id: UUID,
    request: Request,
    body: AgentUpdateLocaleRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "locale:configure")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="locale",
        status_code=200,
        action="LOCALE_UPDATED",
        mutate=lambda service: service.update_locale(context.site_id, locale_id, body),
    )


@router.delete("/locales/{locale_id}")
async def delete_locale(
    locale_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "locale:configure")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="locale",
        status_code=200,
        quota_kind="delete",
        action="LOCALE_DELETED",
        mutate=lambda service: service.delete_locale(
            context.site_id, locale_id, body.expected_row_version
        ),
    )


@router.post("/redirects", status_code=201)
async def create_redirect(
    request: Request,
    body: AgentCreateRedirectRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "redirect:create")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="redirect",
        action="REDIRECT_CREATED",
        mutate=lambda service: service.create_redirect_for_site(context.site_id, body),
    )


@router.patch("/redirects/{redirect_id}")
async def update_redirect(
    redirect_id: UUID,
    request: Request,
    body: AgentUpdateRedirectRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "redirect:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="redirect",
        status_code=200,
        action="REDIRECT_UPDATED",
        mutate=lambda service: service.update_redirect_for_site(
            context.site_id, redirect_id, body
        ),
    )


@router.delete("/redirects/{redirect_id}")
async def delete_redirect(
    redirect_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "redirect:delete")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="redirect",
        status_code=200,
        quota_kind="delete",
        action="REDIRECT_DELETED",
        mutate=lambda service: service.delete_redirect_for_site(
            context.site_id, redirect_id, body.expected_row_version
        ),
    )


@router.post("/navigation", status_code=201)
async def create_navigation(
    request: Request,
    body: AgentCreateNavigationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:create")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation",
        action="NAVIGATION_CREATED",
        mutate=lambda service: service.create_navigation(context.site_id, body),
    )


@router.patch("/navigation/{navigation_id}")
async def update_navigation(
    navigation_id: UUID,
    request: Request,
    body: AgentUpdateNavigationRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation",
        status_code=200,
        action="NAVIGATION_UPDATED",
        mutate=lambda service: service.update_navigation(
            context.site_id, navigation_id, body
        ),
    )


@router.delete("/navigation/{navigation_id}")
async def delete_navigation(
    navigation_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:delete")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation",
        status_code=200,
        quota_kind="delete",
        action="NAVIGATION_DELETED",
        mutate=lambda service: service.delete_navigation(
            context.site_id, navigation_id, body.expected_row_version
        ),
    )


@router.post("/navigation/{navigation_id}/items", status_code=201)
async def create_navigation_item(
    navigation_id: UUID,
    request: Request,
    body: AgentCreateNavigationItemRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:write")
    if body.navigation_id is not None and body.navigation_id != navigation_id:
        raise ResourceNotFoundError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation_item",
        action="NAVIGATION_ITEM_CREATED",
        mutate=lambda service: service.create_navigation_item(
            context.site_id, navigation_id, body
        ),
    )


@router.patch("/navigation-items/{item_id}")
async def update_navigation_item(
    item_id: UUID,
    request: Request,
    body: AgentUpdateNavigationItemRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation_item",
        status_code=200,
        action="NAVIGATION_ITEM_UPDATED",
        mutate=lambda service: service.update_navigation_item(
            context.site_id, item_id, body
        ),
    )


@router.post("/navigation-items/{item_id}:move", status_code=200)
async def move_navigation_item(
    item_id: UUID,
    request: Request,
    body: AgentMoveNavigationItemRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation_item",
        status_code=200,
        action="NAVIGATION_ITEM_MOVED",
        mutate=lambda service: service.move_navigation_item(
            context.site_id, item_id, body
        ),
    )


@router.delete("/navigation-items/{item_id}")
async def delete_navigation_item(
    item_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "navigation:delete")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="navigation_item",
        status_code=200,
        quota_kind="delete",
        action="NAVIGATION_ITEM_DELETED",
        mutate=lambda service: service.delete_navigation_item(
            context.site_id, item_id, body.expected_row_version
        ),
    )


@router.post("/pages", status_code=201)
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
        action="PAGE_CREATED",
        mutate=lambda service: service.create_page_for_site(context.site_id, body),
    )


@router.patch("/pages/{page_id}")
async def update_page(
    page_id: UUID,
    request: Request,
    body: UpdatePageRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "page:write")
    for scope in conditional_scopes_for_fields(
        ProcessKind.AGENT_API,
        "PATCH",
        "/api/agent/v1/pages/{page_id}",
        body.model_fields_set,
    ):
        _require_scope(context, scope)
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="page",
        status_code=200,
        action="PAGE_UPDATED",
        mutate=lambda service: service.update_page_for_site(
            context.site_id, page_id, body
        ),
    )


@router.delete("/pages/{page_id}")
async def delete_page(
    page_id: UUID,
    request: Request,
    body: AgentDeleteRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "page:delete")
    if _constraint(context, "delete_enabled", True) is False:
        raise AuthorizationError()
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="page",
        status_code=200,
        quota_kind="delete",
        action="PAGE_DELETED",
        mutate=lambda service: service.delete_page_for_site(
            context.site_id, page_id, body.expected_row_version
        ),
    )


@router.post("/pages/{page_id}:move", status_code=200)
async def move_page(
    page_id: UUID,
    request: Request,
    body: MovePageRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "page:move")
    _require_scope(context, "route:write")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="page",
        status_code=200,
        action="PAGE_MOVED",
        mutate=lambda service: service.move_page_for_site(
            context.site_id, page_id, body
        ),
    )


@router.post("/pages/{page_id}:restore", status_code=200)
async def restore_page(
    page_id: UUID,
    request: Request,
    body: RestorePageRequest,
    idempotency_key: IdempotencyHeader = None,
) -> AgentMutationResponse:
    context = await _authenticate(request)
    _require_scope(context, "page:restore")
    return await _execute_mutation(
        request,
        context,
        body,
        idempotency_key,
        resource_type="page",
        status_code=200,
        action="PAGE_RESTORED",
        mutate=lambda service: service.restore_page_for_site(
            context.site_id, page_id, body
        ),
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

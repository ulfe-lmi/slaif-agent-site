"""Authenticated Editor API page-composition HTTP surface."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.bounded_embed import (
    validate_map_embed_props,
    validate_video_embed_props,
)
from slaif_agent_site.content_model.component_facets import (
    FacetValidationError,
    field_primitive_map,
    validate_collection_filter_facets,
)
from slaif_agent_site.content_model.composition_models import (
    CompositionNodeRecord,
    CreateCompositionNodeRequest,
    MoveCompositionNodeRequest,
    UpdateCompositionNodeRequest,
)
from slaif_agent_site.content_model.design_system import (
    required_scopes_for_component_create,
    required_scopes_for_component_update,
)
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.control_api.site_authority import (
    SiteRequestAuthority,
    authorize_site_request,
)
from slaif_agent_site.editor_api.mutations import request_service
from slaif_agent_site.errors import (
    AuthorizationError,
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/pages/{page_id}/composition")


def _service(request: Request) -> ContentModelService:
    return request_service(request)


async def _page_and_node(
    request: Request,
    site_id: UUID,
    page_id: UUID,
    node_id: UUID | None = None,
    parent_id: UUID | None = None,
) -> CompositionNodeRecord | None:
    service = _service(request)
    try:
        page = await service.get_page(page_id)
        if page.site_id != site_id:
            raise ResourceNotFoundError()
        nodes = await service.list_composition(page_id)
    except ResourceNotFoundError:
        raise
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    found = next((node for node in nodes if node.id == node_id), None)
    if node_id is not None and found is None:
        raise ResourceNotFoundError()
    if parent_id is not None and not any(node.id == parent_id for node in nodes):
        raise ResourceNotFoundError()
    return found


def _require_component_scopes(authority: Any, required_scopes: tuple[str, ...]) -> None:
    if authority.platform_administrator:
        return
    if not set(required_scopes) <= authority.effective_permissions:
        raise AuthorizationError()


async def _validate_collection_filter_facets(
    request: Request,
    site_id: UUID,
    component_type: str,
    props: dict[str, Any],
) -> None:
    """Fail-closed facet vocabulary validation for the human Puck path.

    Resolves the site-scoped collection view and its content-type fields,
    then rejects any facet whose fieldKey is absent or whose operator is
    outside the field's per-primitive query vocabulary.  The Editor update
    endpoint replaces props wholesale, so the supplied props are exactly
    the post-write state.
    """
    if component_type != "CollectionFilter":
        return
    raw_view_id = props.get("viewId")
    try:
        view_id = UUID(str(raw_view_id))
    except (TypeError, ValueError):
        raise DomainValidationError() from None
    service = _service(request)
    try:
        view = await service.get_view(site_id, view_id)
    except ContentModelServiceError as error:
        if error.reason is ContentModelServiceReason.NOT_FOUND:
            raise DomainValidationError() from None
        raise
    fields = field_primitive_map(await service.list_fields(view.type_id))
    try:
        validate_collection_filter_facets(props.get("facets"), fields)
    except FacetValidationError:
        raise DomainValidationError() from None


async def _validate_embed_props(component_type: str, props: dict[str, Any]) -> None:
    """Fail-closed bounded embed policy validation for the human Puck path.

    Only VideoEmbed and MapBlock are governed by the versioned bounded embed
    policy; all other component types pass through.  The Editor update
    endpoint replaces props wholesale, so the supplied props are exactly the
    post-write state.
    """
    if component_type == "VideoEmbed":
        ok, _key = validate_video_embed_props(props)
    elif component_type == "MapBlock":
        ok, _key = validate_map_embed_props(props)
    else:
        return
    if not ok:
        raise DomainValidationError() from None


async def _auth(
    request: Request, site_id: UUID, *, permission: str, state_changing: bool
) -> SiteRequestAuthority:
    return await authorize_site_request(
        request,
        request.app.state.database,
        request.app.state.settings,
        site_id,
        permission,
        state_changing=state_changing,
    )


@router.post("/components", status_code=201)
async def add_component(
    site_id: UUID,
    page_id: UUID,
    request: Request,
    body: CreateCompositionNodeRequest,
) -> CompositionNodeRecord:
    authority = await _auth(
        request, site_id, permission="component-structure:create", state_changing=True
    )
    parent = UUID(body.parent_id) if body.parent_id else None
    await _page_and_node(request, site_id, page_id, parent_id=parent)
    try:
        required = required_scopes_for_component_create(body.component_type, body.props)
    except (TypeError, ValueError):
        raise DomainValidationError() from None
    _require_component_scopes(authority, required)
    await _validate_collection_filter_facets(
        request, site_id, body.component_type, body.props
    )
    await _validate_embed_props(body.component_type, body.props)
    try:
        return await _service(request).add_composition_node(  # type: ignore[no-any-return]
            site_id=site_id,
            page_id=page_id,
            component_type=body.component_type,
            parent_id=parent,
            slot_key=body.slot_key,
            order_key=body.order_key,
            props=body.props,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/")
async def get_composition(
    site_id: UUID, page_id: UUID, request: Request
) -> list[CompositionNodeRecord]:
    await _auth(request, site_id, permission="composition:read", state_changing=False)
    await _page_and_node(request, site_id, page_id)
    try:
        return list(await _service(request).list_composition(page_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.patch("/components/{node_id}")
async def update_component(
    site_id: UUID,
    page_id: UUID,
    node_id: UUID,
    request: Request,
    body: UpdateCompositionNodeRequest,
) -> CompositionNodeRecord:
    authority = await _auth(
        request,
        site_id,
        permission="component-content-props:write",
        state_changing=True,
    )
    current = await _page_and_node(request, site_id, page_id, node_id=node_id)
    if current is None:
        raise ResourceNotFoundError()
    try:
        required = required_scopes_for_component_update(
            current.component_type,
            current.props,
            body.props or {},
        )
    except (TypeError, ValueError):
        raise DomainValidationError() from None
    _require_component_scopes(authority, required)
    if body.props is not None:
        await _validate_collection_filter_facets(
            request, site_id, current.component_type, body.props
        )
        await _validate_embed_props(current.component_type, body.props)
    try:
        return await _service(request).update_composition_node(  # type: ignore[no-any-return]
            node_id=node_id,
            props=body.props,
            slot_key=body.slot_key,
            order_key=body.order_key,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


@router.post("/components/{node_id}/move")
async def move_component(
    site_id: UUID,
    page_id: UUID,
    node_id: UUID,
    request: Request,
    body: MoveCompositionNodeRequest,
) -> CompositionNodeRecord:
    await _auth(
        request, site_id, permission="component-structure:move", state_changing=True
    )
    parent = UUID(body.new_parent_id) if body.new_parent_id else None
    await _page_and_node(request, site_id, page_id, node_id=node_id, parent_id=parent)
    try:
        return await _service(request).move_composition_node(  # type: ignore[no-any-return]
            node_id=node_id,
            new_parent_id=parent,
            new_slot_key=body.new_slot_key,
            new_order_key=body.new_order_key,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


@router.delete("/components/{node_id}", status_code=204)
async def delete_component(
    site_id: UUID, page_id: UUID, node_id: UUID, request: Request
) -> Response:
    await _auth(
        request, site_id, permission="component-structure:delete", state_changing=True
    )
    await _page_and_node(request, site_id, page_id, node_id=node_id)
    await _service(request).delete_composition_node(node_id)
    return Response(status_code=204)

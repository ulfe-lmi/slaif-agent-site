"""Authenticated Editor API page-composition HTTP surface."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.composition_models import (
    CompositionNodeRecord,
    CreateCompositionNodeRequest,
    MoveCompositionNodeRequest,
    UpdateCompositionNodeRequest,
)
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.control_api.site_authority import authorize_site_request
from slaif_agent_site.errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/pages/{page_id}/composition")


def _service(request: Request) -> ContentModelService:
    return request.app.state.content_model_service  # type: ignore[no-any-return]


async def _auth(
    request: Request, site_id: UUID, *, permission: str, state_changing: bool
) -> None:
    await authorize_site_request(
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
    await _auth(
        request, site_id, permission="component-structure:create", state_changing=True
    )
    try:
        return await _service(request).add_composition_node(
            site_id=site_id,
            page_id=page_id,
            component_type=body.component_type,
            parent_id=None,
            slot_key=body.slot_key,
            order_key=body.order_key,
            props=body.props,
        )  # type: ignore[no-any-return]
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/")
async def get_composition(
    site_id: UUID, page_id: UUID, request: Request
) -> list[CompositionNodeRecord]:
    await _auth(request, site_id, permission="composition:read", state_changing=False)
    try:
        return list(await _service(request).list_composition(page_id))
    except ContentModelServiceError as exc:
        raise ServiceUnavailableError() from None


@router.patch("/components/{node_id}")
async def update_component(
    site_id: UUID,
    page_id: UUID,
    node_id: UUID,
    request: Request,
    body: UpdateCompositionNodeRequest,
) -> CompositionNodeRecord:
    await _auth(
        request,
        site_id,
        permission="component-content-props:write",
        state_changing=True,
    )
    try:
        return await _service(request).update_composition_node(
            node_id=node_id,
            props=body.props,
            slot_key=body.slot_key,
            order_key=body.order_key,
        )  # type: ignore[no-any-return]
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
    try:
        return await _service(request).move_composition_node(
            node_id=node_id,
            new_parent_id=parent,
            new_slot_key=body.new_slot_key,
            new_order_key=body.new_order_key,
        )  # type: ignore[no-any-return]
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
    await _service(request).delete_composition_node(node_id)
    return Response(status_code=204)

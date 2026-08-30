"""Authenticated Editor API content-item HTTP surface."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.item_models import (
    ContentItemRecord,
    CreateContentItemRequest,
    UpdateContentItemRequest,
)
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.control_api.site_authority import authorize_site_request
from slaif_agent_site.editor_api.mutations import request_service
from slaif_agent_site.errors import (
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/content-items")


def _service(request: Request) -> ContentModelService:
    return request_service(request)


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


@router.post("/", status_code=201)
async def create_item(
    site_id: UUID, request: Request, body: CreateContentItemRequest
) -> ContentItemRecord:
    await _auth(request, site_id, permission="content-item:create", state_changing=True)
    try:
        return await _service(request).create_item(  # type: ignore[no-any-return]
            site_id=site_id,
            type_id=body.type_id,
            slug=body.slug,
            status=body.status,
            values=body.values,
            type_definition_version=(
                await _service(request).get_type(body.type_id)
            ).definition_version,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.VALIDATION:
            raise DomainValidationError() from None
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/types/{type_id}")
async def list_items(
    site_id: UUID, type_id: UUID, request: Request
) -> list[ContentItemRecord]:
    await _auth(request, site_id, permission="content-item:read", state_changing=False)
    try:
        return list(await _service(request).list_items(site_id, type_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/{item_id}")
async def get_item(site_id: UUID, item_id: UUID, request: Request) -> ContentItemRecord:
    await _auth(request, site_id, permission="content-item:read", state_changing=False)
    try:
        record = await _service(request).get_item(item_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    return record  # type: ignore[no-any-return]


@router.patch("/{item_id}")
async def update_item(
    site_id: UUID, item_id: UUID, request: Request, body: UpdateContentItemRequest
) -> ContentItemRecord:
    await _auth(request, site_id, permission="content-item:write", state_changing=True)
    try:
        record = await _service(request).get_item(item_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(request).update_item(  # type: ignore[no-any-return]
            item_id=item_id,
            slug=body.slug,
            status=body.status,
            values=body.values,
            expected_row_version=body.expected_row_version,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        if exc.reason is ContentModelServiceReason.VALIDATION:
            raise DomainValidationError() from None
        raise ResourceConflictError() from None


@router.delete("/{item_id}", status_code=204)
async def delete_item(site_id: UUID, item_id: UUID, request: Request) -> Response:
    await _auth(request, site_id, permission="content-item:delete", state_changing=True)
    try:
        record = await _service(request).get_item(item_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    await _service(request).delete_item(item_id, expected_row_version=None)
    return Response(status_code=204)

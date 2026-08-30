"""Authenticated Editor API collection-view HTTP surface."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Request, Response

from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.content_model.view_models import (
    CollectionViewRecord,
    CreateCollectionViewRequest,
    UpdateCollectionViewRequest,
)
from slaif_agent_site.control_api.site_authority import authorize_site_request
from slaif_agent_site.editor_api.mutations import request_service
from slaif_agent_site.errors import (
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/collection-views")


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


@router.post("/types/{type_id}", status_code=201)
async def create_view(
    site_id: UUID, type_id: UUID, request: Request, body: CreateCollectionViewRequest
) -> CollectionViewRecord:
    await _auth(
        request, site_id, permission="collection-view:create", state_changing=True
    )
    try:
        return await _service(request).create_view(  # type: ignore[no-any-return]
            site_id=site_id,
            type_id=type_id,
            key=body.key,
            filter_spec=body.filter_spec,
            sort_spec=body.sort_spec,
            projection_spec=body.projection_spec,
            pagination_spec=body.pagination_spec,
            definition_version=body.definition_version,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.VALIDATION:
            raise DomainValidationError() from None
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/types/{type_id}")
async def list_views(
    site_id: UUID, type_id: UUID, request: Request
) -> list[CollectionViewRecord]:
    await _auth(
        request, site_id, permission="collection-view:read", state_changing=False
    )
    try:
        return list(await _service(request).list_views(site_id, type_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/{view_id}")
async def get_view(
    site_id: UUID, view_id: UUID, request: Request
) -> CollectionViewRecord:
    await _auth(
        request, site_id, permission="collection-view:read", state_changing=False
    )
    try:
        record = await _service(request).get_view(site_id, view_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    return record  # type: ignore[no-any-return]


@router.patch("/{view_id}")
async def update_view(
    site_id: UUID, view_id: UUID, request: Request, body: UpdateCollectionViewRequest
) -> CollectionViewRecord:
    await _auth(
        request, site_id, permission="collection-view:write", state_changing=True
    )
    try:
        record = await _service(request).get_view(site_id, view_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(request).update_view(  # type: ignore[no-any-return]
            site_id=site_id,
            view_id=view_id,
            filter_spec=body.filter_spec,
            sort_spec=body.sort_spec,
            projection_spec=body.projection_spec,
            pagination_spec=body.pagination_spec,
            expected_row_version=body.expected_row_version,
            definition_version=body.definition_version,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        if exc.reason is ContentModelServiceReason.VALIDATION:
            raise DomainValidationError() from None
        raise ResourceConflictError() from None


@router.delete("/{view_id}", status_code=204)
async def delete_view(
    site_id: UUID,
    view_id: UUID,
    request: Request,
    expected_row_version: int = Query(..., ge=1),
) -> Response:
    await _auth(
        request, site_id, permission="collection-view:delete", state_changing=True
    )
    try:
        record = await _service(request).get_view(site_id, view_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        await _service(request).delete_view(site_id, view_id, expected_row_version)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ResourceConflictError() from None
    return Response(status_code=204)

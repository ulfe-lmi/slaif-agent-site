"""Authenticated Editor API page HTTP surface."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.page_models import (
    CreatePageRequest,
    PageRecord,
    UpdatePageRequest,
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

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/pages")


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


@router.post("/", status_code=201)
async def create_page(
    site_id: UUID, request: Request, body: CreatePageRequest
) -> PageRecord:
    await _auth(request, site_id, permission="page:create", state_changing=True)
    try:
        return await _service(request).create_page(  # type: ignore[no-any-return]
            site_id=site_id,
            slug=body.slug,
            title=body.title,
            status=body.status,
            locale=body.locale,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/")
async def list_pages(site_id: UUID, request: Request) -> list[PageRecord]:
    await _auth(request, site_id, permission="page:read", state_changing=False)
    try:
        return list(await _service(request).list_pages(site_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/{page_id}")
async def get_page(site_id: UUID, page_id: UUID, request: Request) -> PageRecord:
    await _auth(request, site_id, permission="page:read", state_changing=False)
    try:
        record = await _service(request).get_page(page_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    return record


@router.patch("/{page_id}")
async def update_page(
    site_id: UUID, page_id: UUID, request: Request, body: UpdatePageRequest
) -> PageRecord:
    await _auth(request, site_id, permission="page:write", state_changing=True)
    try:
        record = await _service(request).get_page(page_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(request).update_page(
            page_id=page_id,
            slug=body.slug,
            title=body.title,
            status=body.status,
            expected_row_version=body.expected_row_version,
        )  # type: ignore[no-any-return]
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ResourceConflictError() from None


@router.delete("/{page_id}", status_code=204)
async def delete_page(site_id: UUID, page_id: UUID, request: Request) -> Response:
    await _auth(request, site_id, permission="page:delete", state_changing=True)
    try:
        record = await _service(request).get_page(page_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    await _service(request).delete_page(page_id)
    return Response(status_code=204)


# Fix the first two routes that need type ignores too

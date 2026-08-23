"""Authenticated Editor API navigation and theme HTTP surface."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.nav_models import (
    CreateNavigationRequest,
    NavigationRecord,
    ThemeRecord,
    UpdateThemeRequest,
)
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.control_api.site_authority import authorize_site_request
from slaif_agent_site.editor_api.mutations import request_service
from slaif_agent_site.errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}")


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


# -- Navigation --


@router.post("/navigation", status_code=201)
async def create_navigation(
    site_id: UUID, request: Request, body: CreateNavigationRequest
) -> NavigationRecord:
    await _auth(request, site_id, permission="navigation:create", state_changing=True)
    try:
        return await _service(request).create_navigation(  # type: ignore[no-any-return]
            site_id=site_id, key=body.key, label=body.label, settings=body.settings
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/navigation")
async def list_navigation(site_id: UUID, request: Request) -> list[NavigationRecord]:
    await _auth(request, site_id, permission="navigation:read", state_changing=False)
    try:
        return list(await _service(request).list_navigation(site_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/navigation/{nav_id}")
async def get_navigation(
    site_id: UUID, nav_id: UUID, request: Request
) -> NavigationRecord:
    await _auth(request, site_id, permission="navigation:read", state_changing=False)
    try:
        record = await _service(request).get_navigation(nav_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    return record  # type: ignore[no-any-return]


@router.patch("/navigation/{nav_id}")
async def update_navigation(
    site_id: UUID, nav_id: UUID, request: Request, body: CreateNavigationRequest
) -> NavigationRecord:
    await _auth(request, site_id, permission="navigation:write", state_changing=True)
    try:
        record = await _service(request).get_navigation(nav_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(request).update_navigation(  # type: ignore[no-any-return]
            nav_id=nav_id, label=body.label, settings=body.settings
        )
    except ContentModelServiceError:
        raise ResourceNotFoundError() from None


@router.delete("/navigation/{nav_id}", status_code=204)
async def delete_navigation(site_id: UUID, nav_id: UUID, request: Request) -> Response:
    await _auth(request, site_id, permission="navigation:delete", state_changing=True)
    await _service(request).delete_navigation(nav_id)
    return Response(status_code=204)


# -- Theme --


@router.get("/theme")
async def get_theme(site_id: UUID, request: Request) -> ThemeRecord:
    await _auth(request, site_id, permission="theme:read", state_changing=False)
    try:
        return await _service(request).get_theme(site_id)  # type: ignore[no-any-return]
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.patch("/theme")
async def update_theme(
    site_id: UUID, request: Request, body: UpdateThemeRequest
) -> ThemeRecord:
    await _auth(request, site_id, permission="theme-global:write", state_changing=True)
    try:
        return await _service(request).update_theme(  # type: ignore[no-any-return]
            site_id=site_id,
            palette=body.palette,
            typography=body.typography,
            layout=None,
            shape=None,
        )
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None

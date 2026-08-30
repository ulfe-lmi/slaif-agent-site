"""Authenticated Editor routes for fixed site-data substrate entities."""

from __future__ import annotations

from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response

from ..content_model.service import (
    ContentModelServiceError,
    ContentModelServiceReason,
)
from ..content_model.site_data_models import (
    CreateLocaleRequest,
    CreateNavigationItemRequest,
    CreateRedirectRequest,
    LocaleRecord,
    MoveNavigationItemRequest,
    NavigationItemRecord,
    RedirectRecord,
    UpdateLocaleRequest,
    UpdateNavigationItemRequest,
    UpdateRedirectRequest,
)
from ..control_api.site_authority import authorize_site_request
from ..errors import (
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from .mutations import request_service

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}")


async def _auth(
    request: Request, site_id: UUID, permission: str, changing: bool
) -> None:
    await authorize_site_request(
        request,
        request.app.state.database,
        request.app.state.settings,
        site_id,
        permission,
        state_changing=changing,
    )


def _error(error: ContentModelServiceError) -> NoReturn:
    if error.reason is ContentModelServiceReason.NOT_FOUND:
        raise ResourceNotFoundError() from None
    if error.reason is ContentModelServiceReason.VALIDATION:
        raise DomainValidationError() from None
    if error.reason is ContentModelServiceReason.CONFLICT:
        raise ResourceConflictError() from None
    raise ServiceUnavailableError() from None


# Locales
@router.post("/locales", status_code=201)
async def create_locale(
    site_id: UUID, request: Request, body: CreateLocaleRequest
) -> LocaleRecord:
    await _auth(request, site_id, "locale:configure", True)
    try:
        return await request_service(request).create_locale(site_id, body)
    except ContentModelServiceError as error:
        _error(error)


@router.get("/locales")
async def list_locales(site_id: UUID, request: Request) -> list[LocaleRecord]:
    await _auth(request, site_id, "site:read", False)
    try:
        return list(await request_service(request).list_locales(site_id))
    except ContentModelServiceError as error:
        _error(error)


@router.get("/locales/{locale_id}")
async def get_locale(site_id: UUID, locale_id: UUID, request: Request) -> LocaleRecord:
    await _auth(request, site_id, "site:read", False)
    try:
        return await request_service(request).get_locale(site_id, locale_id)
    except ContentModelServiceError as error:
        _error(error)


@router.patch("/locales/{locale_id}")
async def update_locale(
    site_id: UUID, locale_id: UUID, request: Request, body: UpdateLocaleRequest
) -> LocaleRecord:
    await _auth(request, site_id, "locale:configure", True)
    try:
        return await request_service(request).update_locale(site_id, locale_id, body)
    except ContentModelServiceError as error:
        _error(error)


@router.delete("/locales/{locale_id}", status_code=204)
async def delete_locale(
    site_id: UUID,
    locale_id: UUID,
    request: Request,
    expected_row_version: int = Query(..., ge=1),
) -> Response:
    await _auth(request, site_id, "locale:configure", True)
    try:
        await request_service(request).delete_locale(
            site_id, locale_id, expected_row_version
        )
    except ContentModelServiceError as error:
        _error(error)
    return Response(status_code=204)


# Navigation items (the existing /navigation routes remain the container API).
@router.post("/navigation/{navigation_id}/items", status_code=201)
async def create_navigation_item(
    site_id: UUID,
    navigation_id: UUID,
    request: Request,
    body: CreateNavigationItemRequest,
) -> NavigationItemRecord:
    await _auth(request, site_id, "navigation:write", True)
    if body.navigation_id != navigation_id:
        raise ResourceNotFoundError()
    try:
        return await request_service(request).create_navigation_item(site_id, body)
    except ContentModelServiceError as error:
        _error(error)


@router.get("/navigation/{navigation_id}/items")
async def list_navigation_items(
    site_id: UUID, navigation_id: UUID, request: Request
) -> list[NavigationItemRecord]:
    await _auth(request, site_id, "navigation:read", False)
    try:
        return list(
            await request_service(request).list_navigation_items(site_id, navigation_id)
        )
    except ContentModelServiceError as error:
        _error(error)


@router.get("/navigation-items/{item_id}")
async def get_navigation_item(
    site_id: UUID, item_id: UUID, request: Request
) -> NavigationItemRecord:
    await _auth(request, site_id, "navigation:read", False)
    try:
        return await request_service(request).get_navigation_item(site_id, item_id)
    except ContentModelServiceError as error:
        _error(error)


@router.patch("/navigation-items/{item_id}")
async def update_navigation_item(
    site_id: UUID, item_id: UUID, request: Request, body: UpdateNavigationItemRequest
) -> NavigationItemRecord:
    await _auth(request, site_id, "navigation:write", True)
    try:
        return await request_service(request).update_navigation_item(
            site_id, item_id, body
        )
    except ContentModelServiceError as error:
        _error(error)


@router.post("/navigation-items/{item_id}/move")
async def move_navigation_item(
    site_id: UUID, item_id: UUID, request: Request, body: MoveNavigationItemRequest
) -> NavigationItemRecord:
    await _auth(request, site_id, "navigation:write", True)
    try:
        return await request_service(request).move_navigation_item(
            site_id, item_id, body.parent_id, body.position, body.expected_row_version
        )
    except ContentModelServiceError as error:
        _error(error)


@router.delete("/navigation-items/{item_id}", status_code=204)
async def delete_navigation_item(
    site_id: UUID,
    item_id: UUID,
    request: Request,
    expected_row_version: int = Query(..., ge=1),
) -> Response:
    await _auth(request, site_id, "navigation:delete", True)
    try:
        await request_service(request).delete_navigation_item(
            site_id, item_id, expected_row_version
        )
    except ContentModelServiceError as error:
        _error(error)
    return Response(status_code=204)


# Redirects
@router.post("/redirects", status_code=201)
async def create_redirect(
    site_id: UUID, request: Request, body: CreateRedirectRequest
) -> RedirectRecord:
    await _auth(request, site_id, "redirect:create", True)
    try:
        return await request_service(request).create_redirect(site_id, body)
    except ContentModelServiceError as error:
        _error(error)


@router.get("/redirects")
async def list_redirects(site_id: UUID, request: Request) -> list[RedirectRecord]:
    await _auth(request, site_id, "redirect:read", False)
    try:
        return list(await request_service(request).list_redirects(site_id))
    except ContentModelServiceError as error:
        _error(error)


@router.get("/redirects/{redirect_id}")
async def get_redirect(
    site_id: UUID, redirect_id: UUID, request: Request
) -> RedirectRecord:
    await _auth(request, site_id, "redirect:read", False)
    try:
        return await request_service(request).get_redirect(site_id, redirect_id)
    except ContentModelServiceError as error:
        _error(error)


@router.patch("/redirects/{redirect_id}")
async def update_redirect(
    site_id: UUID, redirect_id: UUID, request: Request, body: UpdateRedirectRequest
) -> RedirectRecord:
    await _auth(request, site_id, "redirect:write", True)
    try:
        return await request_service(request).update_redirect(
            site_id, redirect_id, body
        )
    except ContentModelServiceError as error:
        _error(error)


@router.delete("/redirects/{redirect_id}", status_code=204)
async def delete_redirect(
    site_id: UUID,
    redirect_id: UUID,
    request: Request,
    expected_row_version: int = Query(..., ge=1),
) -> Response:
    await _auth(request, site_id, "redirect:delete", True)
    try:
        await request_service(request).delete_redirect(
            site_id, redirect_id, expected_row_version
        )
    except ContentModelServiceError as error:
        _error(error)
    return Response(status_code=204)

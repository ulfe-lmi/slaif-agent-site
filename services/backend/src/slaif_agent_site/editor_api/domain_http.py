"""Editor CRUD for site-confined translations and normalized relations."""

from __future__ import annotations

from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Request, Response

from ..content_model.models import (
    CreateRelationRequest,
    CreateTranslationRequest,
    RelationRecord,
    TranslationRecord,
    UpdateRelationRequest,
    UpdateTranslationRequest,
)
from ..content_model.service import ContentModelServiceError, ContentModelServiceReason
from ..control_api.site_authority import authorize_site_request
from ..errors import (
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from .mutations import request_service

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/content-items/{item_id}")


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


def _error(exc: ContentModelServiceError) -> NoReturn:
    if exc.reason is ContentModelServiceReason.NOT_FOUND:
        raise ResourceNotFoundError() from None
    if exc.reason is ContentModelServiceReason.VALIDATION:
        raise DomainValidationError() from None
    if exc.reason is ContentModelServiceReason.CONFLICT:
        raise ResourceConflictError() from None
    raise ServiceUnavailableError() from None


@router.get("/translations")
async def list_translations(
    site_id: UUID, item_id: UUID, request: Request
) -> list[TranslationRecord]:
    await _auth(request, site_id, "translation:read", False)
    try:
        return list(await request_service(request).list_translations(site_id, item_id))
    except ContentModelServiceError as exc:
        _error(exc)


@router.post("/translations", status_code=201)
async def create_translation(
    site_id: UUID, item_id: UUID, request: Request, body: CreateTranslationRequest
) -> TranslationRecord:
    await _auth(request, site_id, "translation:write", True)
    try:
        return await request_service(request).create_translation(site_id, item_id, body)
    except ContentModelServiceError as exc:
        _error(exc)


@router.get("/translations/{translation_id}")
async def get_translation(
    site_id: UUID, item_id: UUID, translation_id: UUID, request: Request
) -> TranslationRecord:
    await _auth(request, site_id, "translation:read", False)
    try:
        record = await request_service(request).get_translation(site_id, translation_id)
        if record.item_id != item_id:
            raise ResourceNotFoundError()
        return record
    except ContentModelServiceError as exc:
        _error(exc)


@router.patch("/translations/{translation_id}")
async def update_translation(
    site_id: UUID,
    item_id: UUID,
    translation_id: UUID,
    request: Request,
    body: UpdateTranslationRequest,
) -> TranslationRecord:
    await _auth(request, site_id, "translation:write", True)
    try:
        current = await request_service(request).get_translation(
            site_id, translation_id
        )
        if current.item_id != item_id:
            raise ResourceNotFoundError()
        return await request_service(request).update_translation(
            site_id, translation_id, body
        )
    except ContentModelServiceError as exc:
        _error(exc)


@router.delete("/translations/{translation_id}", status_code=204)
async def delete_translation(
    site_id: UUID, item_id: UUID, translation_id: UUID, request: Request
) -> Response:
    await _auth(request, site_id, "translation:write", True)
    try:
        current = await request_service(request).get_translation(
            site_id, translation_id
        )
        if current.item_id != item_id:
            raise ResourceNotFoundError()
        await request_service(request).delete_translation(site_id, translation_id)
    except ContentModelServiceError as exc:
        _error(exc)
    return Response(status_code=204)


@router.get("/relations")
async def list_relations(
    site_id: UUID, item_id: UUID, request: Request
) -> list[RelationRecord]:
    await _auth(request, site_id, "relationship:read", False)
    try:
        return list(await request_service(request).list_relations(site_id, item_id))
    except ContentModelServiceError as exc:
        _error(exc)


@router.post("/relations", status_code=201)
async def create_relation(
    site_id: UUID, item_id: UUID, request: Request, body: CreateRelationRequest
) -> RelationRecord:
    await _auth(request, site_id, "relationship:write", True)
    try:
        return await request_service(request).create_relation(site_id, item_id, body)
    except ContentModelServiceError as exc:
        _error(exc)


@router.get("/relations/{relation_id}")
async def get_relation(
    site_id: UUID, item_id: UUID, relation_id: UUID, request: Request
) -> RelationRecord:
    await _auth(request, site_id, "relationship:read", False)
    try:
        record = await request_service(request).get_relation(site_id, relation_id)
        if record.source_item_id != item_id:
            raise ResourceNotFoundError()
        return record
    except ContentModelServiceError as exc:
        _error(exc)


@router.patch("/relations/{relation_id}")
async def update_relation(
    site_id: UUID,
    item_id: UUID,
    relation_id: UUID,
    request: Request,
    body: UpdateRelationRequest,
) -> RelationRecord:
    await _auth(request, site_id, "relationship:write", True)
    try:
        current = await request_service(request).get_relation(site_id, relation_id)
        if current.source_item_id != item_id:
            raise ResourceNotFoundError()
        return await request_service(request).update_relation(
            site_id, relation_id, body
        )
    except ContentModelServiceError as exc:
        _error(exc)


@router.delete("/relations/{relation_id}", status_code=204)
async def delete_relation(
    site_id: UUID, item_id: UUID, relation_id: UUID, request: Request
) -> Response:
    await _auth(request, site_id, "relationship:write", True)
    try:
        current = await request_service(request).get_relation(site_id, relation_id)
        if current.source_item_id != item_id:
            raise ResourceNotFoundError()
        await request_service(request).delete_relation(site_id, relation_id)
    except ContentModelServiceError as exc:
        _error(exc)
    return Response(status_code=204)

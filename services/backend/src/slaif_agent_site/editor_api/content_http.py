"""Authenticated Editor API content-model HTTP surface."""

from __future__ import annotations

from typing import Any, Never, cast
from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.models import (
    ContentTypeRecord,
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    FieldDefinitionRecord,
    UpdateContentTypeRequest,
    UpdateFieldDefinitionRequest,
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
from slaif_agent_site.errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/content-model")


def _service(database: Any) -> ContentModelService:
    return cast(ContentModelService, database.content_model_service())


def _raise_cm_error(error: ContentModelServiceError) -> Never:
    if error.reason is ContentModelServiceReason.NOT_FOUND:
        raise ResourceNotFoundError() from None
    if error.reason is ContentModelServiceReason.CONFLICT:
        raise ResourceConflictError() from None
    raise ServiceUnavailableError() from None


async def _authorize(
    request: Request,
    database: Any,
    settings: Any,
    site_id: UUID,
    *,
    permission: str,
    state_changing: bool,
) -> SiteRequestAuthority:
    return await authorize_site_request(
        request,
        database,
        settings,
        site_id,
        permission,
        state_changing=state_changing,
    )


# -- Content Type routes --


@router.post("/types", status_code=201)
async def create_content_type(
    site_id: UUID, request: Request, body: CreateContentTypeRequest
) -> ContentTypeRecord:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:create",
        state_changing=True,
    )
    try:
        return await _service(database).create_type(site_id, body)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)


@router.get("/types")
async def list_content_types(
    site_id: UUID, request: Request
) -> list[ContentTypeRecord]:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:read",
        state_changing=False,
    )
    try:
        return list(await _service(database).list_types(site_id))
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)


@router.get("/types/{type_id}")
async def get_content_type(
    site_id: UUID, type_id: UUID, request: Request
) -> ContentTypeRecord:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:read",
        state_changing=False,
    )
    try:
        record = await _service(database).get_type(type_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    return record


@router.patch("/types/{type_id}")
async def update_content_type(
    site_id: UUID, type_id: UUID, request: Request, body: UpdateContentTypeRequest
) -> ContentTypeRecord:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:write",
        state_changing=True,
    )
    try:
        record = await _service(database).get_type(type_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(database).update_type(type_id, body)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)


@router.delete("/types/{type_id}", status_code=204)
async def delete_content_type(
    site_id: UUID, type_id: UUID, request: Request
) -> Response:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:delete",
        state_changing=True,
    )
    try:
        record = await _service(database).get_type(type_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    await _service(database).delete_type(type_id)
    return Response(status_code=204)


# -- Field Definition routes --


@router.post("/types/{type_id}/fields", status_code=201)
async def create_field_definition(
    site_id: UUID, type_id: UUID, request: Request, body: CreateFieldDefinitionRequest
) -> FieldDefinitionRecord:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="field-definition:create",
        state_changing=True,
    )
    try:
        ct = await _service(database).get_type(type_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    if ct.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(database).create_field(type_id, body)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)


@router.get("/types/{type_id}/fields")
async def list_field_definitions(
    site_id: UUID, type_id: UUID, request: Request
) -> list[FieldDefinitionRecord]:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:read",
        state_changing=False,
    )
    try:
        ct = await _service(database).get_type(type_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    if ct.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return list(await _service(database).list_fields(type_id))
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)


@router.get("/fields/{field_id}")
async def get_field_definition(
    site_id: UUID, field_id: UUID, request: Request
) -> FieldDefinitionRecord:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="content-model:read",
        state_changing=False,
    )
    try:
        record = await _service(database).get_field(field_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    ct = await _service(database).get_type(record.type_id)
    if ct.site_id != site_id:
        raise ResourceNotFoundError()
    return record


@router.patch("/fields/{field_id}")
async def update_field_definition(
    site_id: UUID, field_id: UUID, request: Request, body: UpdateFieldDefinitionRequest
) -> FieldDefinitionRecord:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="field-definition:write",
        state_changing=True,
    )
    try:
        record = await _service(database).get_field(field_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    ct = await _service(database).get_type(record.type_id)
    if ct.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(database).update_field(field_id, body)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)


@router.delete("/fields/{field_id}", status_code=204)
async def delete_field_definition(
    site_id: UUID, field_id: UUID, request: Request
) -> Response:
    database = request.app.state.database
    settings = request.app.state.settings
    await _authorize(
        request,
        database,
        settings,
        site_id,
        permission="field-definition:delete",
        state_changing=True,
    )
    try:
        record = await _service(database).get_field(field_id)
    except ContentModelServiceError as exc:
        _raise_cm_error(exc)
    ct = await _service(database).get_type(record.type_id)
    if ct.site_id != site_id:
        raise ResourceNotFoundError()
    await _service(database).delete_field(field_id)
    return Response(status_code=204)

"""Authenticated Editor API media HTTP surface."""

from __future__ import annotations

import hashlib
from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.content_model.media_models import (
    CreateMediaRequest,
    MediaAssetRecord,
    UpdateMediaRequest,
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

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}/media")


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


@router.post("/register", status_code=201)
async def register_media(
    site_id: UUID, request: Request, body: CreateMediaRequest
) -> MediaAssetRecord:
    """Register a media asset. The actual bytes are uploaded separately to storage."""
    await _auth(request, site_id, permission="media:upload", state_changing=True)
    content_hash = hashlib.sha256(body.filename.encode()).hexdigest()
    storage_key = f"{site_id}/{content_hash}/{body.filename}"
    try:
        return await _service(request).create_media(  # type: ignore[no-any-return]
            site_id=site_id,
            uploaded_by=None,
            filename=body.filename,
            mime_type=body.mime_type,
            size_bytes=body.size_bytes,
            content_hash=content_hash,
            storage_key=storage_key,
            alt_text=body.alt_text,
            metadata=body.metadata,
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None


@router.get("/")
async def list_media(site_id: UUID, request: Request) -> list[MediaAssetRecord]:
    await _auth(request, site_id, permission="media:read", state_changing=False)
    try:
        return list(await _service(request).list_media(site_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/{media_id}")
async def get_media(
    site_id: UUID, media_id: UUID, request: Request
) -> MediaAssetRecord:
    await _auth(request, site_id, permission="media:read", state_changing=False)
    try:
        record = await _service(request).get_media(media_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    return record  # type: ignore[no-any-return]


@router.patch("/{media_id}")
async def update_media(
    site_id: UUID, media_id: UUID, request: Request, body: UpdateMediaRequest
) -> MediaAssetRecord:
    await _auth(
        request, site_id, permission="media-metadata:write", state_changing=True
    )
    try:
        record = await _service(request).get_media(media_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    try:
        return await _service(request).update_media(  # type: ignore[no-any-return]
            media_id=media_id, alt_text=body.alt_text, metadata=body.metadata
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


@router.delete("/{media_id}", status_code=204)
async def delete_media(site_id: UUID, media_id: UUID, request: Request) -> Response:
    await _auth(
        request, site_id, permission="media-reference:delete", state_changing=True
    )
    try:
        record = await _service(request).get_media(media_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if record.site_id != site_id:
        raise ResourceNotFoundError()
    await _service(request).delete_media(media_id)
    return Response(status_code=204)

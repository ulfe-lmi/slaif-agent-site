"""Authenticated Editor API site-global region HTTP surface."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request

from slaif_agent_site.content_model.region_models import (
    GlobalRegionRecord,
    UpdateGlobalRegionRequest,
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

router = APIRouter(prefix="/api/editor/v1/sites/{site_id}")


def _service(request: Request) -> ContentModelService:
    return request_service(request)


async def _authority(
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


@router.get("/global-regions")
async def list_global_regions(
    site_id: UUID, request: Request
) -> list[GlobalRegionRecord]:
    await _authority(
        request, site_id, permission="global-region:read", state_changing=False
    )
    try:
        return list(await _service(request).list_global_regions(site_id))
    except ContentModelServiceError:
        raise ServiceUnavailableError() from None


@router.get("/global-regions/{region_id}")
async def get_global_region(
    site_id: UUID, region_id: UUID, request: Request
) -> GlobalRegionRecord:
    await _authority(
        request, site_id, permission="global-region:read", state_changing=False
    )
    try:
        return await _service(request).get_global_region(site_id, region_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


@router.patch("/global-regions/{region_id}")
async def update_global_region(
    site_id: UUID,
    region_id: UUID,
    request: Request,
    body: UpdateGlobalRegionRequest,
) -> GlobalRegionRecord:
    authority = await _authority(
        request, site_id, permission="global-region:write", state_changing=True
    )
    try:
        current = await _service(request).get_global_region(site_id, region_id)
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    # A variant change additionally requires the L4 header-footer authority,
    # mirroring the Agent deferred-write gating at the HTTP boundary.
    if (
        body.variant is not None
        and body.variant != current.variant
        and not authority.platform_administrator
        and "header-footer:write" not in authority.effective_permissions
    ):
        raise AuthorizationError()
    try:
        return await _service(request).update_global_region(
            site_id=site_id, region_key=current.region_key, request=body
        )
    except ContentModelServiceError as exc:
        if exc.reason is ContentModelServiceReason.NOT_FOUND:
            raise ResourceNotFoundError() from None
        if exc.reason is ContentModelServiceReason.VALIDATION:
            raise DomainValidationError() from None
        if exc.reason is ContentModelServiceReason.CONFLICT:
            raise ResourceConflictError() from None
        if exc.reason is ContentModelServiceReason.AUTHORIZATION:
            raise AuthorizationError() from None
        raise ServiceUnavailableError() from None

"""Authenticated Platform Administrator site-management HTTP surface."""

from __future__ import annotations

from typing import Any, Never, cast
from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.errors import (
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.sites.models import (
    CreateSiteRequest,
    DomainMapping,
    DomainMappingRequest,
    SiteContext,
    SiteRecord,
    SiteStatus,
    UpdateSiteRequest,
)
from slaif_agent_site.sites.service import (
    SiteService,
    SiteServiceError,
    SiteServiceReason,
)

from .auth_http import authenticate_human_request
from .site_authority import authorize_site_request


def _service(database: Any) -> SiteService:
    return cast(SiteService, database.site_service())


def _raise_site_error(error: SiteServiceError) -> Never:
    if error.reason is SiteServiceReason.NOT_FOUND:
        raise ResourceNotFoundError() from None
    if error.reason is SiteServiceReason.CONFLICT:
        raise ResourceConflictError() from None
    raise ServiceUnavailableError() from None


async def _authorize(
    request: Request,
    database: Any,
    settings: Any,
    *,
    state_changing: bool,
) -> None:
    session = await authenticate_human_request(
        request, database, settings, state_changing=state_changing
    )
    try:
        allowed = await database.authorize_platform_administrator(
            session.user_account_id
        )
    except Exception:
        raise ServiceUnavailableError() from None
    if not allowed:
        raise AuthorizationError()


async def _record(service: SiteService, site_id: UUID) -> SiteRecord:
    try:
        return await service.get(site_id)
    except SiteServiceError as error:
        _raise_site_error(error)


async def _active_context(
    service: SiteService, site_id: UUID
) -> tuple[SiteRecord, SiteContext]:
    record = await _record(service, site_id)
    if record.status is not SiteStatus.ACTIVE:
        raise ResourceConflictError()
    try:
        return record, await service.active_context(site_id)
    except SiteServiceError as error:
        _raise_site_error(error)


def install_control_site_routes(app: Any, database: Any, settings: Any) -> None:
    """Install exactly the bounded authenticated site routes."""

    router = APIRouter(prefix="/api/control/v1/sites")

    @router.get("", response_model=list[SiteRecord])
    async def list_sites(request: Request) -> tuple[SiteRecord, ...]:
        await _authorize(request, database, settings, state_changing=False)
        try:
            return await _service(database).list()
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.post("", response_model=SiteRecord, status_code=201)
    async def create_site(request: Request, body: CreateSiteRequest) -> SiteRecord:
        await _authorize(request, database, settings, state_changing=True)
        try:
            return await _service(database).create(body)
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.get("/{site_id}", response_model=SiteRecord)
    async def get_site(request: Request, site_id: UUID) -> SiteRecord:
        await authorize_site_request(
            request, database, settings, site_id, "site:read", state_changing=False
        )
        return await _record(_service(database), site_id)

    @router.patch("/{site_id}", response_model=SiteRecord)
    async def update_site(
        request: Request, site_id: UUID, body: UpdateSiteRequest
    ) -> SiteRecord:
        await authorize_site_request(
            request,
            database,
            settings,
            site_id,
            "site-policy:manage",
            state_changing=True,
        )
        service = _service(database)
        _existing, context = await _active_context(service, site_id)
        try:
            return await service.update(context, body)
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.post("/{site_id}/archive", response_model=SiteRecord)
    async def archive_site(request: Request, site_id: UUID) -> SiteRecord:
        authority = await authorize_site_request(
            request,
            database,
            settings,
            site_id,
            "site:archive",
            state_changing=True,
            active_required=False,
        )
        if not authority.platform_administrator or not authority.session.recent_auth:
            raise AuthorizationError()
        service = _service(database)
        existing = await _record(service, site_id)
        if existing.status is SiteStatus.ARCHIVED:
            return existing
        try:
            context = await service.active_context(site_id)
            return await service.archive(context)
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.get("/{site_id}/domains", response_model=list[DomainMapping])
    async def list_domains(
        request: Request, site_id: UUID
    ) -> tuple[DomainMapping, ...]:
        await authorize_site_request(
            request, database, settings, site_id, "site:read", state_changing=False
        )
        service = _service(database)
        await _record(service, site_id)
        try:
            return await service.list_domains(site_id)
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.post("/{site_id}/domains", response_model=DomainMapping, status_code=201)
    async def create_domain(
        request: Request, site_id: UUID, body: DomainMappingRequest
    ) -> DomainMapping:
        await authorize_site_request(
            request,
            database,
            settings,
            site_id,
            "site-domain:manage",
            state_changing=True,
        )
        service = _service(database)
        _existing, context = await _active_context(service, site_id)
        try:
            return await service.put_domain(context, body)
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.put("/{site_id}/domains/{domain_id}", response_model=DomainMapping)
    async def replace_domain(
        request: Request,
        site_id: UUID,
        domain_id: UUID,
        body: DomainMappingRequest,
    ) -> DomainMapping:
        await authorize_site_request(
            request,
            database,
            settings,
            site_id,
            "site-domain:manage",
            state_changing=True,
        )
        service = _service(database)
        _existing, context = await _active_context(service, site_id)
        try:
            return await service.put_domain(context, body, domain_id=domain_id)
        except SiteServiceError as error:
            _raise_site_error(error)

    @router.delete("/{site_id}/domains/{domain_id}", status_code=204)
    async def delete_domain(
        request: Request, site_id: UUID, domain_id: UUID
    ) -> Response:
        await authorize_site_request(
            request,
            database,
            settings,
            site_id,
            "site-domain:manage",
            state_changing=True,
        )
        service = _service(database)
        _existing, context = await _active_context(service, site_id)
        try:
            await service.remove_domain(context, domain_id)
        except SiteServiceError as error:
            _raise_site_error(error)
        return Response(status_code=204)

    app.include_router(router)


__all__ = ["install_control_site_routes"]

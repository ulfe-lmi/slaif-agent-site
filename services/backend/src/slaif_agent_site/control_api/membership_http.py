"""Authenticated Control HTTP catalogs and site-membership lifecycle."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Annotated, Any, Never, cast
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from slaif_agent_site.errors import (
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.human_authorization import (
    ROLE_CEILINGS,
    HumanAuthorizationError,
    HumanAuthorizationReason,
    HumanAuthorizationService,
    MembershipChange,
    MembershipRecord,
    MembershipStatus,
    PermissionCatalogRecord,
    RoleCatalogRecord,
)
from slaif_agent_site.human_authorization.catalog import PERMISSION_BY_KEY
from slaif_agent_site.identity.sessions import HumanSessionContext
from slaif_agent_site.sites import SiteService, SiteServiceError, SiteStatus

from .auth_http import authenticate_human_request


def _role_key(value: str) -> str:
    if value not in ROLE_CEILINGS:
        raise ValueError("unknown built-in role")
    return value


def _permission_set(value: frozenset[str]) -> frozenset[str]:
    if not value <= set(PERMISSION_BY_KEY):
        raise ValueError("unknown permission")
    return value


RoleKey = Annotated[str, AfterValidator(_role_key)]
PermissionSet = Annotated[frozenset[str], AfterValidator(_permission_set)]


class CreateMembershipRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    target_user_id: UUID
    role_key: RoleKey
    delegation_ceiling: int = Field(ge=0, le=4)
    allow_permissions: PermissionSet
    deny_permissions: PermissionSet

    @model_validator(mode="after")
    def overrides_are_disjoint(self) -> CreateMembershipRequest:
        if self.delegation_ceiling > ROLE_CEILINGS[self.role_key]:
            raise ValueError("ceiling exceeds built-in role")
        if self.allow_permissions & self.deny_permissions:
            raise ValueError("permission override conflict")
        return self


class UpdateMembershipRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(gt=0)
    role_key: RoleKey
    delegation_ceiling: int = Field(ge=0, le=4)
    status: MembershipStatus
    allow_permissions: PermissionSet
    deny_permissions: PermissionSet

    @model_validator(mode="after")
    def overrides_are_disjoint(self) -> UpdateMembershipRequest:
        if self.delegation_ceiling > ROLE_CEILINGS[self.role_key]:
            raise ValueError("ceiling exceeds built-in role")
        if self.allow_permissions & self.deny_permissions:
            raise ValueError("permission override conflict")
        return self


class MembershipResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    site_id: UUID
    user_account_id: UUID
    role_key: str
    delegation_ceiling: int
    effective_delegation_ceiling: int
    status: MembershipStatus
    version: int
    allow_permissions: tuple[str, ...]
    deny_permissions: tuple[str, ...]
    effective_permissions: tuple[str, ...]
    platform_administrator: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: MembershipRecord) -> MembershipResponse:
        return cls(
            site_id=record.site_id,
            user_account_id=record.user_account_id,
            role_key=record.role_key,
            delegation_ceiling=record.delegation_ceiling,
            effective_delegation_ceiling=record.effective_delegation_ceiling,
            status=record.status,
            version=record.version,
            allow_permissions=tuple(sorted(record.allow_permissions)),
            deny_permissions=tuple(sorted(record.deny_permissions)),
            effective_permissions=tuple(sorted(record.effective_permissions)),
            platform_administrator=record.platform_administrator,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


def _authorization(database: Any) -> HumanAuthorizationService:
    try:
        return cast(HumanAuthorizationService, database.human_authorization_service())
    except Exception:
        raise ServiceUnavailableError() from None


def _sites(database: Any) -> SiteService:
    try:
        return cast(SiteService, database.site_service())
    except Exception:
        raise ServiceUnavailableError() from None


def _raise_authorization_error(error: HumanAuthorizationError) -> Never:
    if error.reason is HumanAuthorizationReason.NOT_FOUND:
        raise ResourceNotFoundError() from None
    if error.reason is HumanAuthorizationReason.DENIED:
        raise AuthorizationError() from None
    if error.reason is HumanAuthorizationReason.CONFLICT:
        raise ResourceConflictError() from None
    raise ServiceUnavailableError() from None


async def _active_site(database: Any, site_id: UUID) -> None:
    try:
        site = await _sites(database).get(site_id)
        if site.status is not SiteStatus.ACTIVE:
            raise ResourceNotFoundError()
        await _sites(database).active_context(site_id)
    except ResourceNotFoundError:
        raise
    except SiteServiceError as error:
        if error.reason.value == "not_found":
            raise ResourceNotFoundError() from None
        if error.reason.value == "conflict":
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None


async def _site_authority(
    request: Request,
    database: Any,
    settings: Any,
    site_id: UUID,
    *,
    state_changing: bool,
) -> tuple[HumanSessionContext, HumanAuthorizationService]:
    session = await authenticate_human_request(
        request, database, settings, state_changing=state_changing
    )
    await _active_site(database, site_id)
    try:
        if await database.authorize_platform_administrator(session.user_account_id):
            return session, _authorization(database)
    except asyncio.CancelledError:
        raise
    except Exception:
        raise ServiceUnavailableError() from None
    service = _authorization(database)
    try:
        membership = await service.membership(site_id, session.user_account_id)
        for permission in ("membership:manage", "role:manage"):
            await service.authorize(
                session.user_account_id,
                site_id,
                permission,
                expected_membership_version=membership.version,
            )
    except HumanAuthorizationError as error:
        _raise_authorization_error(error)
    return session, service


def _change(
    *,
    role_key: str,
    delegation_ceiling: int,
    status: MembershipStatus,
    expected_version: int | None,
    allow_permissions: frozenset[str],
    deny_permissions: frozenset[str],
) -> MembershipChange:
    return MembershipChange(
        role_key=role_key,
        delegation_ceiling=delegation_ceiling,
        status=status,
        expected_version=expected_version,
        allow_permissions=allow_permissions,
        deny_permissions=deny_permissions,
    )


def install_control_membership_routes(app: Any, database: Any, settings: Any) -> None:
    router = APIRouter(prefix="/api/control/v1")

    @router.get("/roles", response_model=list[RoleCatalogRecord])
    async def roles(request: Request) -> tuple[RoleCatalogRecord, ...]:
        await authenticate_human_request(
            request, database, settings, state_changing=False
        )
        return _authorization(database).roles()

    @router.get("/permissions", response_model=list[PermissionCatalogRecord])
    async def permissions(request: Request) -> tuple[PermissionCatalogRecord, ...]:
        await authenticate_human_request(
            request, database, settings, state_changing=False
        )
        try:
            return await _authorization(database).catalog()
        except HumanAuthorizationError as error:
            _raise_authorization_error(error)

    @router.get("/sites/{site_id}/memberships", response_model=list[MembershipResponse])
    async def memberships(
        request: Request, site_id: UUID
    ) -> tuple[MembershipResponse, ...]:
        _session, service = await _site_authority(
            request, database, settings, site_id, state_changing=False
        )
        try:
            records = await service.memberships(site_id)
        except HumanAuthorizationError as error:
            _raise_authorization_error(error)
        return tuple(MembershipResponse.from_record(record) for record in records)

    @router.get(
        "/sites/{site_id}/memberships/{user_id}",
        response_model=MembershipResponse,
    )
    async def membership(
        request: Request, site_id: UUID, user_id: UUID
    ) -> MembershipResponse:
        _session, service = await _site_authority(
            request, database, settings, site_id, state_changing=False
        )
        try:
            return MembershipResponse.from_record(
                await service.membership(site_id, user_id)
            )
        except HumanAuthorizationError as error:
            _raise_authorization_error(error)

    @router.post(
        "/sites/{site_id}/memberships",
        response_model=MembershipResponse,
        status_code=201,
    )
    async def create_membership(
        request: Request, site_id: UUID, body: CreateMembershipRequest
    ) -> MembershipResponse:
        session, service = await _site_authority(
            request, database, settings, site_id, state_changing=True
        )
        if session.user_account_id == body.target_user_id:
            raise AuthorizationError()
        try:
            record = await service.put_membership_record(
                session.user_account_id,
                site_id,
                body.target_user_id,
                _change(
                    role_key=body.role_key,
                    delegation_ceiling=body.delegation_ceiling,
                    status=MembershipStatus.ACTIVE,
                    expected_version=None,
                    allow_permissions=body.allow_permissions,
                    deny_permissions=body.deny_permissions,
                ),
            )
        except HumanAuthorizationError as error:
            _raise_authorization_error(error)
        return MembershipResponse.from_record(record)

    @router.patch(
        "/sites/{site_id}/memberships/{user_id}",
        response_model=MembershipResponse,
    )
    async def update_membership(
        request: Request,
        site_id: UUID,
        body: UpdateMembershipRequest,
        user_id: UUID,
    ) -> MembershipResponse:
        session, service = await _site_authority(
            request, database, settings, site_id, state_changing=True
        )
        if session.user_account_id == user_id:
            raise AuthorizationError()
        try:
            await service.membership(site_id, user_id)
            record = await service.put_membership_record(
                session.user_account_id,
                site_id,
                user_id,
                _change(
                    role_key=body.role_key,
                    delegation_ceiling=body.delegation_ceiling,
                    status=body.status,
                    expected_version=body.expected_version,
                    allow_permissions=body.allow_permissions,
                    deny_permissions=body.deny_permissions,
                ),
            )
        except HumanAuthorizationError as error:
            _raise_authorization_error(error)
        return MembershipResponse.from_record(record)

    @router.delete(
        "/sites/{site_id}/memberships/{user_id}",
        response_model=MembershipResponse,
    )
    async def deactivate_membership(
        request: Request,
        site_id: UUID,
        user_id: UUID,
        expected_version: Annotated[int, Query(gt=0)],
    ) -> MembershipResponse:
        session, service = await _site_authority(
            request, database, settings, site_id, state_changing=True
        )
        if session.user_account_id == user_id:
            raise AuthorizationError()
        try:
            existing = await service.membership(site_id, user_id)
            record = await service.put_membership_record(
                session.user_account_id,
                site_id,
                user_id,
                _change(
                    role_key=existing.role_key,
                    delegation_ceiling=existing.delegation_ceiling,
                    status=MembershipStatus.INACTIVE,
                    expected_version=expected_version,
                    allow_permissions=existing.allow_permissions,
                    deny_permissions=existing.deny_permissions,
                ),
            )
        except HumanAuthorizationError as error:
            _raise_authorization_error(error)
        return MembershipResponse.from_record(record)

    app.include_router(router)


__all__ = [
    "CreateMembershipRequest",
    "MembershipResponse",
    "UpdateMembershipRequest",
    "install_control_membership_routes",
]

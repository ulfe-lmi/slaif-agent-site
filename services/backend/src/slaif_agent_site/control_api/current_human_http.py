"""Authenticated current-human site and authority read routes."""

from __future__ import annotations

import asyncio
from typing import Any, Never, cast
from uuid import UUID

from fastapi import APIRouter, Request

from slaif_agent_site.errors import ResourceNotFoundError, ServiceUnavailableError
from slaif_agent_site.human_authorization import (
    CurrentHumanAuthority,
    CurrentHumanSite,
    HumanAuthorizationError,
    HumanAuthorizationReason,
    HumanAuthorizationService,
)

from .auth_http import authenticate_human_request


def _service(database: Any) -> HumanAuthorizationService:
    try:
        return cast(HumanAuthorizationService, database.human_authorization_service())
    except Exception:
        raise ServiceUnavailableError() from None


def _raise(error: HumanAuthorizationError) -> Never:
    if error.reason in {
        HumanAuthorizationReason.NOT_FOUND,
        HumanAuthorizationReason.DENIED,
    }:
        raise ResourceNotFoundError() from None
    raise ServiceUnavailableError() from None


def install_current_human_routes(app: Any, database: Any, settings: Any) -> None:
    router = APIRouter(prefix="/api/control/v1")

    @router.get("/me/sites", response_model=list[CurrentHumanSite])
    async def current_sites(request: Request) -> tuple[CurrentHumanSite, ...]:
        session = await authenticate_human_request(
            request, database, settings, state_changing=False
        )
        try:
            return await _service(database).current_human_sites(session.user_account_id)
        except asyncio.CancelledError:
            raise
        except HumanAuthorizationError as error:
            _raise(error)

    @router.get("/sites/{site_id}/my-authority", response_model=CurrentHumanAuthority)
    async def current_authority(
        request: Request, site_id: UUID
    ) -> CurrentHumanAuthority:
        session = await authenticate_human_request(
            request, database, settings, state_changing=False
        )
        try:
            return await _service(database).current_human_authority(
                session.user_account_id, site_id
            )
        except asyncio.CancelledError:
            raise
        except HumanAuthorizationError as error:
            _raise(error)

    app.include_router(router)


__all__ = ["install_current_human_routes"]

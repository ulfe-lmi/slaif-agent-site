"""Reusable fail-closed Control authority for one active site."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import Any, Never, cast
from uuid import UUID

from fastapi import Request

from slaif_agent_site.errors import (
    AuthorizationError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.human_authorization import (
    HumanAuthorizationError,
    HumanAuthorizationReason,
    HumanAuthorizationService,
)
from slaif_agent_site.identity.sessions import HumanSessionContext
from slaif_agent_site.sites import SiteService, SiteServiceError, SiteStatus

from .auth_http import authenticate_human_request


@dataclass(frozen=True, slots=True)
class SiteRequestAuthority:
    session: HumanSessionContext
    platform_administrator: bool


def _authorization(database: Any) -> HumanAuthorizationService:
    try:
        return cast(HumanAuthorizationService, database.human_authorization_service())
    except Exception:
        raise ServiceUnavailableError() from None


def _deny(error: HumanAuthorizationError) -> Never:
    if error.reason is HumanAuthorizationReason.CONFLICT:
        raise AuthorizationError() from None
    if error.reason in {
        HumanAuthorizationReason.NOT_FOUND,
        HumanAuthorizationReason.DENIED,
    }:
        raise ResourceNotFoundError() from None
    raise ServiceUnavailableError() from None


async def authorize_site_request(
    request: Request,
    database: Any,
    settings: Any,
    site_id: UUID,
    permission: str,
    *,
    state_changing: bool,
    active_required: bool = True,
) -> SiteRequestAuthority:
    """Authenticate once and derive current server authority immediately."""

    session = await authenticate_human_request(
        request, database, settings, state_changing=state_changing
    )
    try:
        administrator = await database.authorize_platform_administrator(
            session.user_account_id
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        raise ServiceUnavailableError() from None
    if not administrator:
        authorization = _authorization(database)
        try:
            membership = await authorization.membership(
                site_id, session.user_account_id
            )
            await authorization.authorize(
                session.user_account_id,
                site_id,
                permission,
                expected_membership_version=membership.version,
            )
        except HumanAuthorizationError as error:
            _deny(error)
    try:
        site = await cast(SiteService, database.site_service()).get(site_id)
        if (
            active_required
            and not administrator
            and site.status is not SiteStatus.ACTIVE
        ):
            raise ResourceNotFoundError()
    except ResourceNotFoundError:
        raise
    except SiteServiceError:
        raise ResourceNotFoundError() from None
    authority = SiteRequestAuthority(session, bool(administrator))
    editor_database = getattr(request.app.state, "editor_database", None)
    if request.url.path.startswith("/api/editor/") and editor_database is not None:
        from slaif_agent_site.editor_api.database import (
            EditorIdempotencyMismatchError,
            EditorIdempotencyReplayError,
        )
        from slaif_agent_site.editor_api.mutations import request_mutation_digest

        try:
            idempotency_key: str | None = None
            request_digest: str | None = None
            if state_changing:
                try:
                    idempotency_key, request_digest = await request_mutation_digest(
                        request
                    )
                except ValueError as error:
                    if str(error) == "missing":
                        raise IdempotencyKeyRequiredError() from None
                    raise IdempotencyKeyInvalidError() from None
            workspace_id = await database.resolve_human_editor_workspace(
                site_id, session.user_account_id
            )
            request_context = editor_database.request_content_service(
                workspace_id=workspace_id,
                human_user_id=session.user_account_id,
                site_id=site_id,
                human_session_id=session.session_id,
                state_changing=state_changing,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )
            context = await request_context.__aenter__()
        except IdempotencyKeyRequiredError:
            raise
        except IdempotencyKeyInvalidError:
            raise
        except EditorIdempotencyMismatchError:
            raise IdempotencyMismatchError() from None
        except EditorIdempotencyReplayError:
            raise
        except asyncio.CancelledError:
            raise
        except Exception:
            raise ServiceUnavailableError() from None
        try:
            request.state.editor_content_context = request_context
            request.state.editor_request_context = context
            request.state.content_model_service = context.service
            request.state.editor_workspace_id = workspace_id
        except Exception:
            await request_context.__aexit__(*sys.exc_info())
            raise
    return authority


__all__ = ["SiteRequestAuthority", "authorize_site_request"]

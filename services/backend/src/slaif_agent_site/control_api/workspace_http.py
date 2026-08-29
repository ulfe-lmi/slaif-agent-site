"""Human-authorized Agent workspace Control routes."""

# ruff: noqa: E501 -- route signatures and policy calls remain explicit

from __future__ import annotations

from typing import Any, Never
from uuid import UUID

from fastapi import APIRouter, Request

from slaif_agent_site.agent_state.workspace_models import (
    CreateWorkspaceRequest,
    DelegationPreset,
)
from slaif_agent_site.errors import (
    AuthorizationError,
    DomainValidationError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.human_authorization.catalog import (
    L1_SCOPES,
    L2_SCOPES,
    L3_SCOPES,
    L4_SCOPES,
    READ_SCOPES,
)

from .site_authority import authorize_site_request

router = APIRouter(prefix="/api/control/v1/sites/{site_id}/workspaces")
_PRESET_SCOPES = {
    DelegationPreset.L1_CONTENT_EDITOR: READ_SCOPES | L1_SCOPES,
    DelegationPreset.L2_SITE_EDITOR: READ_SCOPES | L1_SCOPES | L2_SCOPES,
    DelegationPreset.L3_SITE_DESIGNER: READ_SCOPES | L1_SCOPES | L2_SCOPES | L3_SCOPES,
    DelegationPreset.L4_SITE_ARCHITECT: READ_SCOPES
    | L1_SCOPES
    | L2_SCOPES
    | L3_SCOPES
    | L4_SCOPES,
}


def _database(request: Request) -> Any:
    try:
        return request.app.state.control_database
    except AttributeError:
        raise ServiceUnavailableError() from None


def _raise(exc: Exception) -> Never:
    if "DENIED" in str(exc) or "P0002" in str(exc):
        raise AuthorizationError() from None
    if "NOT_FOUND" in str(exc):
        raise ResourceNotFoundError() from None
    raise ServiceUnavailableError() from None


def _record(row: Any) -> dict[str, Any]:
    scopes = row["effective_scopes"]
    if isinstance(scopes, str):
        import json

        scopes = json.loads(scopes)
    return {
        "workspace_id": str(row["id"]),
        "site_id": str(row["site_id"]),
        "title": row["title"],
        "task_description": row["task_description"],
        "status": row["status"],
        "delegation_preset": row["delegation_preset"],
        "effective_scopes": sorted(scopes),
        "resource_constraints": row["resource_constraints"],
        "source_origins": list(row["source_origins"]),
        "request_quota": row["request_quota"],
        "mutation_quota": row["mutation_quota"],
        "delete_quota": row["delete_quota"],
        "upload_quota": row["upload_quota"],
        "browser_quota": row["browser_quota"],
        "base_site_revision": row["base_site_revision"],
        "created_at": row["created_at"].isoformat(),
        "expires_at": row["expires_at"].isoformat(),
    }


@router.post("/", status_code=201)
async def create_workspace(
    site_id: UUID, request: Request, body: CreateWorkspaceRequest
) -> dict[str, Any]:
    database = _database(request)
    authority = await authorize_site_request(
        request,
        database,
        request.app.state.settings,
        site_id,
        "workspace:create",
        state_changing=True,
    )
    preset = body.delegation_preset
    scopes = body.requested_scopes or frozenset(_PRESET_SCOPES[preset])
    if not scopes <= _PRESET_SCOPES[preset]:
        raise DomainValidationError()
    try:
        row = await database.human_agent_workspace_create(
            site_id,
            authority.session.user_account_id,
            body.title,
            body.task_description,
            preset.value,
            sorted(scopes),
            body.resource_constraints,
            list(body.source_origins),
            body.request_quota,
            body.mutation_quota,
            body.delete_quota,
            body.upload_quota,
            body.browser_quota,
            body.duration_hours,
        )
    except Exception as exc:
        _raise(exc)
    if row is None:
        raise ResourceNotFoundError()
    return _record(row)


@router.get("/{workspace_id}")
async def get_workspace(
    site_id: UUID, workspace_id: UUID, request: Request
) -> dict[str, Any]:
    database = _database(request)
    authority = await authorize_site_request(
        request,
        database,
        request.app.state.settings,
        site_id,
        "workspace:read-all",
        state_changing=False,
    )
    try:
        row = await database.human_agent_workspace_get(
            workspace_id, site_id, authority.session.user_account_id
        )
    except Exception as exc:
        _raise(exc)
    if row is None:
        raise ResourceNotFoundError()
    return _record(row)


def install_control_workspace_routes(app: Any, database: Any, settings: Any) -> None:
    app.include_router(router)


__all__ = ["install_control_workspace_routes"]

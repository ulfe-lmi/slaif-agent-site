"""Human-authorized Agent workspace Control routes."""

# ruff: noqa: E501 -- route signatures and policy calls remain explicit

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any, Never, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from slaif_agent_site.agent_state.workspace_models import (
    CreateWorkspaceRequest,
    DelegationPreset,
)
from slaif_agent_site.errors import (
    AuthenticationError,
    AuthorizationError,
    DomainValidationError,
    ResourceConflictError,
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
    if "IDEMPOTENCY_MISMATCH" in str(exc):
        raise ResourceConflictError() from None
    if "INPUT_INVALID" in str(exc):
        raise DomainValidationError() from None
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
    expires_at = row["expires_at"]
    status = row["status"]
    if status == "ACTIVE" and expires_at <= datetime.now(UTC):
        status = "EXPIRED"
    return {
        "workspace_id": str(row["id"]),
        "site_id": str(row["site_id"]),
        "title": row["title"],
        "task_description": row["task_description"],
        "status": status,
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


async def _authorize_workspace_read(
    request: Request, database: Any, site_id: UUID
) -> Any:
    """Permit read-all governors and creators inspecting their own workspaces."""
    try:
        return await authorize_site_request(
            request,
            database,
            request.app.state.settings,
            site_id,
            "workspace:read-all",
            state_changing=False,
        )
    except (AuthorizationError, ResourceNotFoundError):
        return await authorize_site_request(
            request,
            database,
            request.app.state.settings,
            site_id,
            "workspace:create",
            state_changing=False,
        )


@router.post("/", status_code=201)
async def create_workspace(
    site_id: UUID,
    request: Request,
    body: CreateWorkspaceRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    if (
        idempotency_key is None
        or not idempotency_key.isascii()
        or not re.fullmatch(r"[A-Za-z0-9._~-]{1,128}", idempotency_key)
    ):
        raise DomainValidationError()
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
    scopes = body.requested_scopes
    if scopes is None:
        scopes = frozenset(_PRESET_SCOPES[preset])
    if not scopes <= _PRESET_SCOPES[preset]:
        raise DomainValidationError()
    try:
        digest = hashlib.sha256(
            json.dumps(
                body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        row = await database.human_agent_workspace_create_idempotent(
            site_id,
            authority.session.user_account_id,
            body.title,
            body.task_description,
            preset.value,
            sorted(scopes),
            json.dumps(body.resource_constraints, sort_keys=True),
            list(body.source_origins),
            body.request_quota,
            body.mutation_quota,
            body.delete_quota,
            body.upload_quota,
            body.browser_quota,
            body.duration_hours,
            idempotency_key,
            digest,
        )
    except Exception as exc:
        _raise(exc)
    if row is None:
        raise ResourceNotFoundError()
    if row["replayed"]:
        response.status_code = 200
    return _record(row)


@router.get("/")
async def list_workspaces(site_id: UUID, request: Request) -> list[dict[str, Any]]:
    database = _database(request)
    authority = await _authorize_workspace_read(request, database, site_id)
    try:
        rows = await database.human_agent_workspace_list(
            site_id, authority.session.user_account_id
        )
    except Exception as exc:
        _raise(exc)
    return [_record(row) for row in rows]


@router.get("/{workspace_id}")
async def get_workspace(
    site_id: UUID, workspace_id: UUID, request: Request
) -> dict[str, Any]:
    database = _database(request)
    authority = await _authorize_workspace_read(request, database, site_id)
    try:
        row = await database.human_agent_workspace_get(
            workspace_id, site_id, authority.session.user_account_id
        )
    except Exception as exc:
        _raise(exc)
    if row is None:
        raise ResourceNotFoundError()
    return _record(row)


@router.get("/{workspace_id}/review/")
async def get_workspace_review(
    site_id: UUID, workspace_id: UUID, request: Request
) -> dict[str, Any]:
    """One deterministic read-only review document for a frozen workspace."""
    database = _database(request)
    authority = await _authorize_workspace_read(request, database, site_id)
    try:
        document = await database.human_agent_workspace_review_read(
            workspace_id, site_id, authority.session.user_account_id
        )
    except Exception as exc:
        # The read model fails closed with one stable internal class;
        # every gate failure is the same uniform 404 (no oracle).
        if "REVIEW_READ_UNAVAILABLE" in str(exc):
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    if document is None:
        raise ResourceNotFoundError()
    return cast("dict[str, Any]", document)


@router.post("/{workspace_id}/freeze/", status_code=202)
async def freeze_workspace(
    site_id: UUID, workspace_id: UUID, request: Request
) -> dict[str, Any]:
    """Freeze one workspace: capability revocation + durable snapshot job."""
    database = _database(request)
    authority = await authorize_site_request(
        request,
        database,
        request.app.state.settings,
        site_id,
        "workspace:freeze",
        state_changing=True,
    )
    try:
        row = await database.human_agent_workspace_freeze(
            workspace_id, site_id, authority.session.user_account_id
        )
    except Exception as exc:
        message = str(exc)
        if "WORKSPACE_NOT_FOUND" in message:
            raise ResourceNotFoundError() from None
        if "WORKSPACE_NOT_ACTIVE" in message:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None
    if row is None:
        raise ResourceNotFoundError()
    return {"job_id": str(row["job_id"]), "status": row["status"]}


class AcceptWorkspaceRequest(BaseModel):
    """Strict accept body (R2.3): the exact three fields, nothing else."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: UUID
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    acknowledge_summary: bool

    @field_validator("acknowledge_summary", mode="before")
    @classmethod
    def acknowledge_must_be_boolean_true(cls, value: Any) -> Any:
        # JSON ``1`` must not coerce to a boolean acknowledgement.
        if value is not True:
            raise ValueError("acknowledge_summary must be the boolean true")
        return value


@router.post("/{workspace_id}/accept/", status_code=202)
async def accept_workspace(
    site_id: UUID,
    workspace_id: UUID,
    request: Request,
    body: AcceptWorkspaceRequest,
) -> dict[str, Any]:
    """Real human accept: dual-permission gate + idempotent ACCEPT job."""
    database = _database(request)
    authority = await authorize_site_request(
        request,
        database,
        request.app.state.settings,
        site_id,
        "workspace:accept",
        state_changing=True,
    )
    if not (
        authority.platform_administrator
        or "site:publish" in authority.effective_permissions
    ):
        raise ResourceNotFoundError()
    if not authority.session.recent_auth:
        raise AuthenticationError()
    try:
        row = await database.human_agent_workspace_accept(
            workspace_id,
            site_id,
            body.snapshot_id,
            body.digest,
            authority.session.user_account_id,
        )
    except Exception as exc:
        message = str(exc)
        if "WORKSPACE_NOT_IN_REVIEW" in message:
            raise ResourceConflictError() from None
        raise ServiceUnavailableError() from None
    if row is None:
        raise ResourceNotFoundError()
    return {"job_id": str(row["job_id"]), "status": row["status"]}


def install_control_workspace_routes(app: Any, database: Any, settings: Any) -> None:
    app.include_router(router)


__all__ = ["install_control_workspace_routes"]

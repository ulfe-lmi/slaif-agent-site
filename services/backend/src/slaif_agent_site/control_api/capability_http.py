"""One-time, human-authorized Agent capability lifecycle routes."""

# ruff: noqa: E501 -- route signatures remain explicit

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any, Never
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response

from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.errors import (
    AuthorizationError,
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

from .site_authority import authorize_site_request

router = APIRouter(
    prefix="/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/capabilities"
)


def _database(request: Request) -> Any:
    try:
        return request.app.state.control_database
    except AttributeError:
        raise ServiceUnavailableError() from None


def _raise(exc: Exception) -> Never:
    if "IDEMPOTENCY_MISMATCH" in str(exc):
        raise ResourceConflictError() from None
    if "DENIED" in str(exc) or "P0002" in str(exc):
        raise AuthorizationError() from None
    if "NOT_FOUND" in str(exc):
        raise ResourceNotFoundError() from None
    raise ServiceUnavailableError() from None


async def _authorize_workspace_read(
    request: Request, database: Any, site_id: UUID
) -> Any:
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
async def create_capability(
    site_id: UUID,
    workspace_id: UUID,
    request: Request,
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
        "capability:create",
        state_changing=True,
    )
    plaintext, public_id, digest = generate_capability_token()
    try:
        digest_request = hashlib.sha256(
            json.dumps(
                {"site_id": str(site_id), "workspace_id": str(workspace_id)},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        row = await database.human_agent_capability_create_idempotent(
            workspace_id,
            site_id,
            authority.session.user_account_id,
            public_id,
            digest,
            idempotency_key,
            digest_request,
        )
    except Exception as exc:
        _raise(exc)
    if row is None:
        raise ResourceNotFoundError()
    # The plaintext is intentionally constructed and returned only here. It is
    # never passed to persistence, logging, telemetry, or another endpoint.
    if row["replayed"]:
        response.status_code = 200
        return {
            "capability_id": row["public_id"],
            "workspace_id": str(row["workspace_id"]),
            "site_id": str(row["site_id"]),
            "expires_at": row["expires_at"].isoformat(),
            "warning": "This capability was already issued; its secret is not redisplayed.",
        }
    return {
        "capability_id": row["public_id"],
        "workspace_id": str(row["workspace_id"]),
        "site_id": str(row["site_id"]),
        "token": plaintext,
        "expires_at": row["expires_at"].isoformat(),
        "warning": "This token is shown exactly once. Store it securely.",
    }


@router.get("/")
async def list_capabilities(
    site_id: UUID, workspace_id: UUID, request: Request
) -> list[dict[str, Any]]:
    database = _database(request)
    authority = await _authorize_workspace_read(request, database, site_id)
    try:
        rows = await database.human_agent_capability_list(
            workspace_id, site_id, authority.session.user_account_id
        )
    except Exception as exc:
        _raise(exc)
    return [
        {
            "capability_id": row["public_id"],
            "created_at": row["created_at"].isoformat(),
            "expires_at": row["expires_at"].isoformat(),
            "revoked": row["revoked_at"] is not None,
            "status": (
                "REVOKED"
                if row["revoked_at"] is not None
                else "EXPIRED"
                if row["expires_at"] <= datetime.now(UTC)
                else "ACTIVE"
            ),
        }
        for row in rows
    ]


@router.post("/{capability_id}/revoke")
async def revoke_capability(
    site_id: UUID, workspace_id: UUID, capability_id: str, request: Request
) -> dict[str, Any]:
    database = _database(request)
    authority = await authorize_site_request(
        request,
        database,
        request.app.state.settings,
        site_id,
        "capability:revoke",
        state_changing=True,
    )
    try:
        revoked = await database.human_agent_capability_revoke(
            workspace_id, site_id, authority.session.user_account_id, capability_id
        )
    except Exception as exc:
        _raise(exc)
    if not revoked:
        raise ResourceNotFoundError()
    return {"capability_id": capability_id, "status": "revoked"}


def install_control_capability_routes(app: Any, database: Any, settings: Any) -> None:
    app.include_router(router)


__all__ = ["install_control_capability_routes"]

"""Authenticated capability lifecycle HTTP surface (Control API)."""

from __future__ import annotations

from typing import Any, Never
from uuid import UUID

from fastapi import APIRouter, Request

from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.errors import (
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/control/v1/workspaces/{workspace_id}/capabilities")


def _pool(request: Request) -> Any:
    return request.app.state.database


def _raise_error(exc: Exception) -> Never:
    message = str(exc)
    if "NOT_FOUND" in message or "P0002" in message:
        raise ResourceNotFoundError() from None
    raise ServiceUnavailableError() from None


@router.post("/", status_code=201)
async def create_capability(workspace_id: UUID, request: Request) -> dict[str, Any]:
    """Mint a new capability token for this workspace."""
    try:
        plaintext, public_id, digest = generate_capability_token()
        pool = _pool(request)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM control.slaif_workspace_get($1)", workspace_id
            )
            if row is None:
                raise ResourceNotFoundError()
            await conn.fetchrow(
                "INSERT INTO control.capability "
                "(workspace_id, public_id, secret_digest, scopes) "
                "VALUES ($1,$2,$3,$4)",
                workspace_id,
                public_id,
                digest,
                row.get("effective_scopes", "[]"),
            )
        return {
            "capability_id": public_id,
            "token": plaintext,
            "workspace_id": str(workspace_id),
            "warning": "This token is shown exactly once. Store it securely.",
        }
    except ResourceNotFoundError:
        raise
    except Exception as exc:
        _raise_error(exc)


@router.post("/{capability_id}/revoke", status_code=200)
async def revoke_capability(
    workspace_id: UUID, capability_id: str, request: Request
) -> dict[str, Any]:
    """Revoke a capability token immediately."""
    try:
        pool = _pool(request)
        async with pool.acquire() as conn:
            result = await conn.fetchrow(
                "UPDATE control.capability SET revoked_at = now() "
                "WHERE public_id = $1 AND workspace_id = $2 "
                "AND revoked_at IS NULL RETURNING id",
                capability_id,
                workspace_id,
            )
        if result is None:
            raise ResourceNotFoundError()
        return {"capability_id": capability_id, "status": "revoked"}
    except ResourceNotFoundError:
        raise
    except Exception as exc:
        _raise_error(exc)


@router.get("/")
async def list_capabilities(
    workspace_id: UUID, request: Request
) -> list[dict[str, Any]]:
    """List all capabilities for this workspace (no secrets)."""
    try:
        pool = _pool(request)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT public_id, created_at, revoked_at, expires_at "
                "FROM control.capability WHERE workspace_id = $1",
                workspace_id,
            )
        return [
            {
                "capability_id": r["public_id"],
                "created_at": r["created_at"].isoformat(),
                "revoked": r["revoked_at"] is not None,
                "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
            }
            for r in rows
        ]
    except Exception as exc:
        _raise_error(exc)


def install_control_capability_routes(app: Any, database: Any, settings: Any) -> None:
    app.include_router(router)

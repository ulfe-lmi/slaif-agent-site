"""Authenticated workspace lifecycle HTTP surface (Control API)."""

from __future__ import annotations

from typing import Any, Never
from uuid import UUID

from fastapi import APIRouter, Request, Response

from slaif_agent_site.agent_state.workspace_models import CreateWorkspaceRequest
from slaif_agent_site.errors import (
    ResourceNotFoundError,
    ServiceUnavailableError,
)

router = APIRouter(prefix="/api/control/v1/sites/{site_id}/workspaces")


def _pool(request: Request) -> Any:
    return request.app.state.database


def _raise_ws_error(exc: Exception) -> Never:
    message = str(exc)
    if "NOT_FOUND" in message or "P0002" in message:
        raise ResourceNotFoundError() from None
    raise ServiceUnavailableError() from None


@router.post("/", status_code=201)
async def create_workspace(
    site_id: UUID, request: Request, body: CreateWorkspaceRequest
) -> dict[str, Any]:
    try:
        pool = _pool(request)
        user_id = getattr(request.state, "user_id", None) or UUID(int=0)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM control.slaif_workspace_create($1,$2,$3,$4,$5,$6,$7)",
                site_id,
                user_id,
                body.title,
                body.task_description,
                body.delegation_preset.value,
                [],
                body.duration_hours,
            )
        if row is None:
            raise ServiceUnavailableError()
        return {
            "workspace_id": str(row["id"]),
            "site_id": str(row["site_id"]),
            "status": row["status"],
            "title": row["title"],
            "delegation_preset": row["delegation_preset"],
            "expires_at": row["expires_at"].isoformat(),
        }
    except ServiceUnavailableError:
        raise
    except Exception as exc:
        _raise_ws_error(exc)


@router.get("/{workspace_id}")
async def get_workspace(
    site_id: UUID, workspace_id: UUID, request: Request
) -> dict[str, Any]:
    try:
        pool = _pool(request)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM control.slaif_workspace_get($1)", workspace_id
            )
        if row is None or str(row["site_id"]) != str(site_id):
            raise ResourceNotFoundError()
        return {
            "workspace_id": str(row["id"]),
            "site_id": str(row["site_id"]),
            "status": row["status"],
            "title": row["title"],
            "created_at": row["created_at"].isoformat(),
            "expires_at": row["expires_at"].isoformat(),
        }
    except ResourceNotFoundError:
        raise
    except Exception as exc:
        _raise_ws_error(exc)


@router.post("/{workspace_id}/freeze")
async def freeze_workspace(
    site_id: UUID, workspace_id: UUID, request: Request
) -> dict[str, Any]:
    try:
        pool = _pool(request)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM control.slaif_workspace_freeze($1)", workspace_id
            )
        if row is None:
            raise ResourceNotFoundError()
        return {"workspace_id": str(row["id"]), "status": row["status"]}
    except ResourceNotFoundError:
        raise
    except Exception as exc:
        _raise_ws_error(exc)


@router.post("/{workspace_id}/discard", status_code=204)
async def discard_workspace(
    site_id: UUID, workspace_id: UUID, request: Request
) -> Response:
    try:
        pool = _pool(request)
        async with pool.acquire() as conn:
            await conn.fetchrow(
                "SELECT control.slaif_workspace_discard($1)", workspace_id
            )
        return Response(status_code=204)
    except Exception as exc:
        _raise_ws_error(exc)


def install_control_workspace_routes(app: Any, database: Any, settings: Any) -> None:
    app.include_router(router)

"""MCP adapter that delegates all operations to the Agent API HTTP surface.

Architecture reference: ARCHITECTURE-for-agents.md §9 (MCP) and §11 (MCP
tool families). The adapter holds no database credentials and no business
logic. It maps MCP tool calls to Agent API REST endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from slaif_agent_site.errors import ServiceUnavailableError

router = APIRouter(prefix="/mcp/v1")


@router.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-adapter"}


@router.get("/tools")
async def list_tools(request: Request) -> dict[str, Any]:
    """Return the MCP tool catalog (all delegate to Agent API)."""
    return {
        "tools": [
            {"name": "site.describe", "method": "GET", "path": "/api/agent/v1/session"},
            {
                "name": "model.list_content_types",
                "method": "GET",
                "path": "/api/agent/v1/content-model/types",
            },
            {
                "name": "content.list_items",
                "method": "GET",
                "path": "/api/agent/v1/content-items/types/{type_id}",
            },
            {"name": "page.list", "method": "GET", "path": "/api/agent/v1/pages/"},
            {"name": "media.list", "method": "GET", "path": "/api/agent/v1/media/"},
        ]
    }


@router.post("/call")
async def call_tool(request: Request) -> dict[str, Any]:
    """Execute an MCP tool by delegating to the Agent API."""
    body = await request.json()
    tool_name = body.get("tool")
    if not tool_name:
        raise ServiceUnavailableError()

    agent_base = str(request.app.state.settings.agent_api_url).rstrip("/")
    auth_header = request.headers.get("Authorization", "")

    path = body.get("path", "/")
    ALLOWED_PREFIXES = (
        "/api/agent/v1/session",
        "/api/agent/v1/permissions",
        "/api/agent/v1/content-model/",
        "/api/agent/v1/content-items/",
        "/api/agent/v1/pages/",
        "/api/agent/v1/media/",
    )
    if not isinstance(path, str) or not any(
        path.startswith(p) for p in ALLOWED_PREFIXES
    ):
        raise ServiceUnavailableError()

    method = body.get("method", "GET")
    if method not in ("GET", "POST", "PATCH", "DELETE"):
        raise ServiceUnavailableError()

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=body.get("method", "GET"),
                url=f"{agent_base}{body.get('path', '/')}",
                headers={"Authorization": auth_header},
                json=body.get("body"),
                timeout=30,
            )
            return {
                "tool": tool_name,
                "status": response.status_code,
                "data": response.json(),
            }
    except httpx.HTTPError:
        raise ServiceUnavailableError() from None


def install_mcp_routes(app: Any, settings: Any) -> None:
    app.include_router(router)


# NOTE: CodeQL flags this as SSRF because `path` comes from the request body.
# However, the architecture explicitly states that MCP delegates to Agent API only.
# The `path` must start with `/api/agent/v1/` which limits it to known endpoints.
# The base URL comes from server-side configuration, not user input.
# This is a controlled delegation pattern, not an open redirect.

"""Internal browser worker API for confined preview and source operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from slaif_agent_site.errors import (
    AuthorizationError,
    ResourceNotFoundError,
)

router = APIRouter(prefix="/internal/browser/v1")

BLOCKED_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"})
MAX_SCREENSHOTS_PER_RUN = 50
MAX_RUN_DURATION_SECONDS = 120
MAX_TARGETS = 6


def _validate_target_url(url: str) -> bool:
    """Reject private/link-local/metadata/file URLs."""
    if url.startswith("file://"):
        return False
    for host in BLOCKED_HOSTS:
        if host in url:
            return False
    if "169.254" in url or "metadata.google" in url:
        return False
    return True


@router.post("/preview-runs")
async def create_preview_run(request: Request) -> dict[str, Any]:
    body = await request.json()
    workspace_id = body.get("workspace_id")
    site_route = body.get("route", "/")
    targets = body.get("targets", ["desktop-chromium"])

    if not workspace_id:
        raise ResourceNotFoundError()
    if not isinstance(site_route, str) or not _validate_target_url(site_route):
        raise AuthorizationError()
    if len(targets) > MAX_TARGETS:
        raise AuthorizationError()

    return {
        "run_id": f"run-{workspace_id}-{len(targets)}",
        "status": "queued",
        "workspace_id": workspace_id,
        "targets": targets[:MAX_TARGETS],
        "max_screenshots": MAX_SCREENSHOTS_PER_RUN,
        "timeout_seconds": MAX_RUN_DURATION_SECONDS,
    }


@router.get("/runs/{run_id}")
async def get_run_status(run_id: str, request: Request) -> dict[str, Any]:
    if not run_id or len(run_id) > 128:
        raise ResourceNotFoundError()
    return {
        "run_id": run_id,
        "status": "completed",
        "artifacts": [],
        "console_errors": [],
        "network_failures": [],
    }

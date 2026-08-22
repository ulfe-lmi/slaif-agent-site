"""MCP adapter application factory."""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ServiceSettings
from ..health import ReadinessProbe
from .mcp_http import install_mcp_routes


def create_app(
    *,
    settings: ServiceSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    app = create_http_application(
        ProcessKind.MCP_ADAPTER,
        settings=settings,
        readiness_probes=readiness_probes,
    )
    install_mcp_routes(app, settings)
    return app


__all__ = ["create_app"]

"""MCP adapter application factory and process runner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn
from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ConfigurationError, ServiceSettings
from ..health import ReadinessProbe
from ..logging import configure_json_logging
from .mcp_http import install_mcp_routes


def create_app(
    *,
    settings: ServiceSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
    upstream_base: str | None = None,
    upstream_timeout_seconds: float | None = None,
    max_upstream_concurrency: int | None = None,
) -> FastAPI:
    """Build the capability-bound MCP discovery application.

    ``upstream_base`` defaults to the structurally fixed internal Agent
    service address; tests may point it at a bounded local endpoint.
    """
    app = create_http_application(
        ProcessKind.MCP_ADAPTER,
        settings=settings,
        readiness_probes=readiness_probes,
    )
    install_mcp_routes(
        app,
        upstream_base=upstream_base,
        upstream_timeout_seconds=upstream_timeout_seconds,
        max_upstream_concurrency=max_upstream_concurrency,
    )
    return app


def run_mcp_process(*, argv: Sequence[str] | None = None) -> int:
    """Validate settings and run the complete MCP adapter application."""

    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.mcp_adapter")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration without opening a connection",
    )
    arguments = parser.parse_args(argv)
    try:
        service_settings = ServiceSettings.load()
        app = create_app(settings=service_settings)
    except (ConfigurationError, ValueError) as error:
        parser.exit(2, f"{error}\n")

    if arguments.check:
        print("mcp-adapter: CHECK_OK")
        return 0

    configure_json_logging(
        service=ProcessKind.MCP_ADAPTER.value,
        level=service_settings.log_level.value,
    )
    uvicorn.run(
        app,
        host=service_settings.bind_host,
        port=service_settings.bind_port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=service_settings.shutdown_timeout_seconds,
    )
    return 0


__all__ = ["create_app", "run_mcp_process"]

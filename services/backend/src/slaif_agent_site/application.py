"""Shared health-only FastAPI factory and explicit HTTP process runner."""

from __future__ import annotations

import argparse
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse

from .authority import LifecycleKind, ProcessKind, authority_for
from .config import ConfigurationError, ServiceSettings
from .correlation import CorrelationMiddleware
from .errors import ErrorEnvelope, install_error_handlers
from .health import (
    LivenessResponse,
    ReadinessProbe,
    ReadinessResponse,
    ReadinessStatus,
    evaluate_readiness,
)
from .logging import configure_json_logging

LOGGER = logging.getLogger(__name__)


def create_http_application(
    process: ProcessKind,
    *,
    settings: ServiceSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    """Build a side-effect-free app containing only live/ready endpoints."""

    descriptor = authority_for(process)
    if descriptor.lifecycle is not LifecycleKind.HTTP or not descriptor.has_listener:
        raise ValueError("the selected process has no HTTP listener")
    selected_settings = settings or ServiceSettings.load()
    probes = tuple(readiness_probes)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.started = True
        LOGGER.info(
            "service lifecycle started",
            extra={"event_fields": {"process": process.value, "status": "SKELETON"}},
        )
        try:
            yield
        finally:
            app.state.started = False
            LOGGER.info(
                "service lifecycle stopped",
                extra={"event_fields": {"process": process.value}},
            )

    app = FastAPI(
        title=f"SLAIF Agent-Site {process.value}",
        version="0.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.process_kind = process
    app.state.authority = descriptor
    app.state.settings = selected_settings
    app.add_middleware(CorrelationMiddleware)
    install_error_handlers(app)

    @app.get(
        "/health/live",
        response_model=LivenessResponse,
        responses={500: {"model": ErrorEnvelope}},
    )
    async def live() -> LivenessResponse:
        return LivenessResponse(service=process)

    @app.get(
        "/health/ready",
        response_model=ReadinessResponse,
        responses={503: {"model": ReadinessResponse}},
    )
    async def ready() -> ReadinessResponse | JSONResponse:
        result = await evaluate_readiness(
            process,
            probes,
            timeout=selected_settings.readiness_timeout_seconds,
        )
        if result.status is ReadinessStatus.READY:
            return result
        return JSONResponse(status_code=503, content=result.model_dump(mode="json"))

    return app


def run_http_process(process: ProcessKind, *, argv: Sequence[str] | None = None) -> int:
    """Load typed settings and run one concrete app without import-string magic."""

    module_name = process.value.replace("-", "_")
    parser = argparse.ArgumentParser(prog=f"python -m slaif_agent_site.{module_name}")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration and app identity without binding a port",
    )
    args = parser.parse_args(argv)
    try:
        settings = ServiceSettings.load()
        app = create_http_application(process, settings=settings)
    except ConfigurationError as exc:
        parser.exit(2, f"{exc}\n")

    if args.check:
        print(f"{process.value}: CHECK_OK")
        return 0

    configure_json_logging(service=process.value, level=settings.log_level.value)
    uvicorn.run(
        app,
        host=settings.bind_host,
        port=settings.bind_port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=settings.shutdown_timeout_seconds,
    )
    return 0


__all__ = ["create_http_application", "run_http_process"]

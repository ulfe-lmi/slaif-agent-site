"""Editor API application factory."""

from __future__ import annotations

import argparse
import sys
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ConfigurationError, ServiceSettings
from ..control_api.config import (
    ControlDatabaseConfigurationError,
    ControlDatabaseSettings,
)
from ..control_api.database import ControlDatabase
from ..control_api.route_policy import validate_route_policy_coverage
from ..health import ReadinessProbe
from ..logging import configure_json_logging
from .composition_http import router as composition_router
from .config import EditorDatabaseConfigurationError, EditorDatabaseSettings
from .content_http import router as content_model_router
from .database import EditorDatabase, EditorIdempotencyReplayError
from .item_http import router as content_item_router
from .media_http import router as media_router
from .mutations import resource_type, response_payload, response_resource_id
from .nav_theme_http import router as nav_theme_router
from .page_http import router as page_router
from .view_http import router as collection_view_router


def create_app(
    *,
    settings: ServiceSettings | None = None,
    database: Any | None = None,
    database_settings: ControlDatabaseSettings | None = None,
    editor_database: Any | None = None,
    editor_database_settings: EditorDatabaseSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_control_database = database or ControlDatabase(
        database_settings or ControlDatabaseSettings.load()
    )
    selected_editor_database = editor_database or EditorDatabase(
        editor_database_settings or EditorDatabaseSettings.load()
    )

    @asynccontextmanager
    async def database_lifespan(app: FastAPI) -> AsyncIterator[None]:
        await selected_control_database.start()
        await selected_editor_database.start()
        try:
            yield
        finally:
            await selected_editor_database.stop()
            await selected_control_database.stop()

    app = create_http_application(
        ProcessKind.EDITOR_API,
        settings=settings,
        readiness_probes=(
            ReadinessProbe("database", selected_control_database.readiness),
            ReadinessProbe("editor_database", selected_editor_database.readiness),
            *readiness_probes,
        ),
        lifespan_factory=database_lifespan,
    )
    app.state.database = selected_control_database
    app.state.editor_database = selected_editor_database

    @app.exception_handler(EditorIdempotencyReplayError)
    async def editor_replay_handler(
        _request: Request, error: EditorIdempotencyReplayError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=error.response_body,
        )

    @app.middleware("http")
    async def close_editor_content_context(request: Request, call_next: Any) -> Any:
        context_manager: Any = None

        async def rollback(error: BaseException) -> None:
            nonlocal context_manager
            if context_manager is not None:
                await context_manager.__aexit__(type(error), error, error.__traceback__)
                context_manager = None
                request.state.editor_content_context = None

        try:
            response = await call_next(request)
            context_manager = getattr(request.state, "editor_content_context", None)
            context = getattr(request.state, "editor_request_context", None)
            if context_manager is None or context is None:
                return response
            if response.status_code >= 400:
                await rollback(RuntimeError("editor mutation response failed"))
                return response
            body = getattr(response, "body", None)
            if body is None:
                body = b"".join([chunk async for chunk in response.body_iterator])
                response = Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    background=response.background,
                )
            if context.idempotency_key is not None:
                await selected_editor_database.complete_request(
                    context,
                    response_status=response.status_code,
                    response_body=response_payload(body),
                    action=f"{request.method} {request.url.path}",
                    resource_type=resource_type(request),
                    resource_id=response_resource_id(
                        request, response_payload(body), context.site_id
                    ),
                )
            await context_manager.__aexit__(None, None, None)
            context_manager = None
            request.state.editor_content_context = None
            return response
        except BaseException:
            error = sys.exc_info()
            if context_manager is None:
                context_manager = getattr(request.state, "editor_content_context", None)
            if context_manager is not None:
                await context_manager.__aexit__(*error)
                request.state.editor_content_context = None
            raise

    @app.middleware("http")
    async def editor_security_headers(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        if request.url.path.startswith("/api/editor/"):
            response.headers["Cache-Control"] = "private, no-store"
            response.headers["Pragma"] = "no-cache"
            response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        return response

    app.include_router(content_model_router)
    app.include_router(content_item_router)
    app.include_router(collection_view_router)
    app.include_router(nav_theme_router)
    app.include_router(page_router)
    app.include_router(composition_router)
    app.include_router(media_router)
    validate_route_policy_coverage(app, ProcessKind.EDITOR_API)
    return app


def run_editor_process(*, argv: Sequence[str] | None = None) -> int:
    """Validate settings and run the authenticated Editor API application."""

    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.editor_api")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration without opening a database connection",
    )
    arguments = parser.parse_args(argv)
    try:
        service_settings = ServiceSettings.load()
        database_settings = ControlDatabaseSettings.load()
        editor_database_settings = EditorDatabaseSettings.load()
        app = create_app(
            settings=service_settings,
            database_settings=database_settings,
            editor_database_settings=editor_database_settings,
        )
    except (
        ConfigurationError,
        ControlDatabaseConfigurationError,
        EditorDatabaseConfigurationError,
    ) as error:
        parser.exit(2, f"{error}\n")

    if arguments.check:
        print("editor-api: CHECK_OK")
        return 0

    configure_json_logging(
        service=ProcessKind.EDITOR_API.value,
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


__all__ = ["create_app", "run_editor_process"]

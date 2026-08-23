"""Editor API application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ServiceSettings
from ..control_api.config import (
    ControlDatabaseSettings,
)
from ..control_api.database import ControlDatabase
from ..control_api.route_policy import validate_route_policy_coverage
from ..health import ReadinessProbe
from .composition_http import router as composition_router
from .content_http import router as content_model_router
from .item_http import router as content_item_router
from .media_http import router as media_router
from .nav_theme_http import router as nav_theme_router
from .page_http import router as page_router
from .view_http import router as collection_view_router


def create_app(
    *,
    settings: ServiceSettings | None = None,
    database_settings: ControlDatabaseSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_database = ControlDatabase(
        database_settings or ControlDatabaseSettings.load()
    )

    @asynccontextmanager
    async def database_lifespan(app: FastAPI) -> AsyncIterator[None]:
        await selected_database.start()
        try:
            yield
        finally:
            await selected_database.stop()

    app = create_http_application(
        ProcessKind.EDITOR_API,
        settings=settings,
        readiness_probes=readiness_probes,
        lifespan_factory=database_lifespan,
    )
    app.state.database = selected_database
    app.state.content_model_service = selected_database.content_model_service()
    app.include_router(content_model_router)
    app.include_router(content_item_router)
    app.include_router(collection_view_router)
    app.include_router(nav_theme_router)
    app.include_router(page_router)
    app.include_router(composition_router)
    app.include_router(media_router)
    validate_route_policy_coverage(app, ProcessKind.EDITOR_API)
    return app


__all__ = ["create_app"]

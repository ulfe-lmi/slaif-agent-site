"""Internal Render API application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, Protocol

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ServiceSettings
from ..health import ReadinessProbe
from .config import RenderDatabaseSettings
from .database import RenderDatabase
from .site_http import RenderPrivateHeadersMiddleware, install_render_site_route


class RenderDatabaseAdapter(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def readiness(self) -> Any: ...
    def resolver(self) -> Any: ...


def create_app(
    *,
    settings: ServiceSettings | None = None,
    database_settings: RenderDatabaseSettings | None = None,
    database: RenderDatabaseAdapter | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_database = database or RenderDatabase(
        database_settings or RenderDatabaseSettings.load()
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await selected_database.start()
        try:
            yield
        finally:
            await selected_database.stop()

    app = create_http_application(
        ProcessKind.RENDER_API,
        settings=settings,
        readiness_probes=(
            ReadinessProbe("database", selected_database.readiness),
            *readiness_probes,
        ),
        lifespan_factory=lifespan,
    )
    app.state.render_database = selected_database
    install_render_site_route(app, selected_database)
    app.add_middleware(RenderPrivateHeadersMiddleware)
    return app


__all__ = ["create_app"]

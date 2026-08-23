"""Agent API application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from ..agent_state.capability_auth import (
    create_capability_authentication_database,
)
from ..application import create_http_application
from ..authority import ProcessKind
from ..browser_worker.browser_http import router as browser_router
from ..config import ServiceSettings
from ..health import ReadinessProbe
from .agent_http import router as agent_router
from .database import AgentDatabase, AgentDatabaseAdapter, CapabilityDatabase


def create_app(
    *,
    settings: ServiceSettings | None = None,
    capability_database_settings: Any | None = None,
    capability_database: CapabilityDatabase | None = None,
    database: AgentDatabaseAdapter | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_database = database or AgentDatabase(
        capability_database=(
            capability_database
            or create_capability_authentication_database(capability_database_settings)
        )
    )

    @asynccontextmanager
    async def database_lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await selected_database.start()
        try:
            yield
        finally:
            await selected_database.stop()

    app = create_http_application(
        ProcessKind.AGENT_API,
        settings=settings,
        readiness_probes=(
            ReadinessProbe("database", selected_database.readiness),
            *readiness_probes,
        ),
        lifespan_factory=database_lifespan,
    )
    app.state.database = selected_database
    app.state.content_model_service = selected_database.content_model_service()
    app.include_router(agent_router)
    app.include_router(browser_router)
    return app

"""Agent API application factory."""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..browser_worker.browser_http import router as browser_router
from ..config import ServiceSettings
from ..health import ReadinessProbe
from .agent_http import router as agent_router
from .database import AgentDatabase


def create_app(
    *,
    settings: ServiceSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    database = AgentDatabase()

    app = create_http_application(
        ProcessKind.AGENT_API,
        settings=settings,
        readiness_probes=readiness_probes,
    )
    app.state.database = database
    app.state.content_model_service = database.content_model_service()
    app.include_router(agent_router)
    app.include_router(browser_router)
    return app

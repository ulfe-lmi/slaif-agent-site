"""Editor API application factory."""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ServiceSettings
from ..control_api.route_policy import validate_route_policy_coverage
from ..health import ReadinessProbe
from .content_http import router as content_model_router
from .item_http import router as content_item_router


def create_app(
    *,
    settings: ServiceSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    app = create_http_application(
        ProcessKind.EDITOR_API,
        settings=settings,
        readiness_probes=readiness_probes,
    )
    app.include_router(content_model_router)
    app.include_router(content_item_router)
    validate_route_policy_coverage(app, ProcessKind.EDITOR_API)
    return app


__all__ = ["create_app"]

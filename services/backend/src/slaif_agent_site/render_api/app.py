"""Internal Render API application factory."""

from __future__ import annotations

from collections.abc import Sequence

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ServiceSettings
from ..health import ReadinessProbe


def create_app(
    *,
    settings: ServiceSettings | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    return create_http_application(
        ProcessKind.RENDER_API,
        settings=settings,
        readiness_probes=readiness_probes,
    )


__all__ = ["create_app"]

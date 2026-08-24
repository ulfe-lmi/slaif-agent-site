"""Authenticated private Media service application."""

from __future__ import annotations

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ConfigurationError, ServiceSettings
from ..health import ProbeResult, ReadinessProbe
from .config import MediaDatabaseConfigurationError, MediaSettings
from .database import MediaDatabase
from .media_http import router as media_router
from .store import MediaStore


def create_app(
    *,
    settings: ServiceSettings | None = None,
    media_settings: MediaSettings | None = None,
    database: MediaDatabase | None = None,
    store: MediaStore | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_settings = media_settings or MediaSettings.load()
    selected_database = database or MediaDatabase(selected_settings)
    selected_store = store or MediaStore(
        selected_settings.media_root,
        max_upload_bytes=selected_settings.max_upload_bytes,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await selected_database.start()
        try:
            yield
        finally:
            await selected_database.stop()

    app = create_http_application(
        ProcessKind.MEDIA_SERVICE,
        settings=settings,
        readiness_probes=(
            ReadinessProbe("database", selected_database.readiness),
            ReadinessProbe(
                "media_store",
                lambda: _store_probe(selected_store),
            ),
            *readiness_probes,
        ),
        lifespan_factory=lifespan,
    )
    app.state.settings = settings or ServiceSettings.load()
    app.state.media_database = selected_database
    app.state.media_store = selected_store
    app.include_router(media_router)
    return app


async def _store_probe(store: MediaStore) -> ProbeResult:
    return (
        ProbeResult.ready()
        if await store.readiness()
        else ProbeResult.unavailable("storage_unavailable")
    )


def run_media_process(*, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.media_service")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        service_settings = ServiceSettings.load()
        media_settings = MediaSettings.load()
        app = create_app(settings=service_settings, media_settings=media_settings)
    except (ConfigurationError, MediaDatabaseConfigurationError) as error:
        parser.exit(2, f"{error}\n")
    if arguments.check:
        print("media-service: CHECK_OK")
        return 0
    uvicorn.run(
        app,
        host=service_settings.bind_host,
        port=service_settings.bind_port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=service_settings.shutdown_timeout_seconds,
    )
    return 0


__all__ = ["create_app", "run_media_process"]

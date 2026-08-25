"""Agent API application factory."""

from __future__ import annotations

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..browser_preview_credentials import (
    BrowserPreviewCredentialError,
    BrowserPreviewCredentialSigner,
    load_browser_signing_key,
)
from ..config import ConfigurationError, ServiceSettings
from ..health import ProbeResult, ReadinessProbe
from ..logging import configure_json_logging
from .agent_http import router as agent_router
from .browser_http import router as browser_router
from .browser_service import AgentBrowserRunService
from .config import AgentDatabaseConfigurationError, AgentDatabaseSettings
from .database import AgentDatabase, AgentDatabaseAdapter


def create_app(
    *,
    settings: ServiceSettings | None = None,
    database_settings: AgentDatabaseSettings | None = None,
    database: AgentDatabaseAdapter | None = None,
    browser_signer: BrowserPreviewCredentialSigner | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_database_settings = database_settings or AgentDatabaseSettings.load()
    selected_database = database or AgentDatabase(settings=selected_database_settings)
    test_mode = (
        getattr(getattr(settings, "mode", None), "value", None) == "test"
        or selected_database_settings.mode.value == "test"
    )
    selected_signer = browser_signer
    if selected_signer is None and not test_mode:
        try:
            selected_signer = BrowserPreviewCredentialSigner(
                load_browser_signing_key(
                    selected_database_settings.browser_signing_key_file
                )
            )
        except BrowserPreviewCredentialError:
            selected_signer = None

    async def browser_signing_readiness() -> ProbeResult:
        if selected_signer is None:
            return ProbeResult.unavailable("signing_key_unavailable")
        return ProbeResult.ready()

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
            *(
                (ReadinessProbe("browser-signing-key", browser_signing_readiness),)
                if not test_mode or browser_signer is not None
                else ()
            ),
            *readiness_probes,
        ),
        lifespan_factory=database_lifespan,
    )
    app.state.database = selected_database
    app.state.browser_run_service = AgentBrowserRunService(selected_database)
    app.state.browser_preview_signer = selected_signer
    app.include_router(agent_router)
    app.include_router(browser_router)
    return app


def run_agent_process(*, argv: Sequence[str] | None = None) -> int:
    """Validate settings and run the complete Agent API application."""

    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.agent_api")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration without opening a database connection",
    )
    arguments = parser.parse_args(argv)
    try:
        service_settings = ServiceSettings.load()
        database_settings = AgentDatabaseSettings.load()
        app = create_app(
            settings=service_settings,
            database_settings=database_settings,
        )
    except (ConfigurationError, AgentDatabaseConfigurationError) as error:
        parser.exit(2, f"{error}\n")

    if arguments.check:
        print("agent-api: CHECK_OK")
        return 0

    configure_json_logging(
        service=ProcessKind.AGENT_API.value,
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


__all__ = ["create_app", "run_agent_process"]

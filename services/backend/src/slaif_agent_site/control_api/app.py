"""Control API application factory and package-local process runner."""

from __future__ import annotations

import argparse
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..config import ConfigurationError, ServiceSettings
from ..health import ReadinessProbe
from ..logging import configure_json_logging
from .auth_http import install_control_auth_routes
from .capability_http import install_control_capability_routes
from .config import ControlDatabaseConfigurationError, ControlDatabaseSettings
from .current_human_http import install_current_human_routes
from .database import ControlDatabase, ControlDatabaseAdapter
from .membership_http import install_control_membership_routes
from .route_policy import validate_route_policy_coverage
from .site_http import install_control_site_routes
from .workspace_http import install_control_workspace_routes


def create_app(
    *,
    settings: ServiceSettings | None = None,
    database_settings: ControlDatabaseSettings | None = None,
    database: ControlDatabaseAdapter | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_database = database or ControlDatabase(
        database_settings or ControlDatabaseSettings.load()
    )

    @asynccontextmanager
    async def database_lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await selected_database.start()
        try:
            yield
        finally:
            await selected_database.stop()

    app = create_http_application(
        ProcessKind.CONTROL_API,
        settings=settings,
        readiness_probes=(
            ReadinessProbe("database", selected_database.readiness),
            *readiness_probes,
        ),
        lifespan_factory=database_lifespan,
    )
    app.state.control_database = selected_database
    install_control_auth_routes(app, selected_database, app.state.settings)
    install_control_site_routes(app, selected_database, app.state.settings)
    install_control_membership_routes(app, selected_database, app.state.settings)
    install_current_human_routes(app, selected_database, app.state.settings)
    install_control_workspace_routes(app, selected_database, app.state.settings)
    install_control_capability_routes(app, selected_database, app.state.settings)
    validate_route_policy_coverage(app, ProcessKind.CONTROL_API)
    return app


def run_control_process(*, argv: Sequence[str] | None = None) -> int:
    """Validate both settings models and run the package-local Control app."""

    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.control_api")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration without reading a DSN or opening a connection",
    )
    arguments = parser.parse_args(argv)
    try:
        service_settings = ServiceSettings.load()
        database_settings = ControlDatabaseSettings.load()
        app = create_app(
            settings=service_settings,
            database_settings=database_settings,
        )
    except (ConfigurationError, ControlDatabaseConfigurationError) as error:
        parser.exit(2, f"{error}\n")

    if arguments.check:
        print("control-api: CHECK_OK")
        return 0

    configure_json_logging(
        service=ProcessKind.CONTROL_API.value,
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


__all__ = ["create_app", "run_control_process"]

"""Internal Render API application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, Protocol

from fastapi import FastAPI

from ..application import create_http_application
from ..authority import ProcessKind
from ..browser_preview_credentials import (
    BrowserPreviewCredentialError,
    BrowserPreviewCredentialSigner,
    load_browser_signing_key,
)
from ..config import ServiceSettings
from ..health import ProbeResult, ReadinessProbe
from .config import RenderDatabaseConfigurationError, RenderDatabaseSettings
from .database import RenderDatabase
from .site_http import (
    RenderPrivateHeadersMiddleware,
    RenderServiceAuthenticationMiddleware,
    install_render_projection_routes,
    install_render_site_route,
)


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
    browser_verifier: BrowserPreviewCredentialSigner | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_render_settings = database_settings or RenderDatabaseSettings.load()
    selected_database = database or RenderDatabase(selected_render_settings)
    test_mode = (
        getattr(getattr(settings, "mode", None), "value", None) == "test"
        or selected_render_settings.mode.value == "test"
    )
    service_token: bytes | None = None
    if not test_mode:
        try:
            resolved_token = selected_render_settings.resolved_service_token()
            service_token = (
                resolved_token.get_secret_value().encode("ascii")
                if resolved_token is not None
                else None
            )
        except RenderDatabaseConfigurationError:
            service_token = None
    selected_browser_verifier = browser_verifier
    if selected_browser_verifier is None and not test_mode:
        try:
            selected_browser_verifier = BrowserPreviewCredentialSigner(
                load_browser_signing_key(
                    selected_render_settings.browser_signing_key_file
                )
            )
        except BrowserPreviewCredentialError:
            selected_browser_verifier = None

    async def browser_signing_readiness() -> ProbeResult:
        if selected_browser_verifier is None:
            return ProbeResult.unavailable("signing_key_unavailable")
        return ProbeResult.ready()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if not test_mode and service_token is None:
            raise RenderDatabaseConfigurationError("Invalid Render service credential.")
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
            *(
                (ReadinessProbe("browser-signing-key", browser_signing_readiness),)
                if not test_mode or browser_verifier is not None
                else ()
            ),
            *readiness_probes,
        ),
        lifespan_factory=lifespan,
    )
    app.state.render_database = selected_database
    install_render_site_route(app, selected_database)
    install_render_projection_routes(
        app, selected_database, browser_verifier=selected_browser_verifier
    )
    app.state.browser_preview_verifier = selected_browser_verifier
    app.add_middleware(
        RenderServiceAuthenticationMiddleware,
        allow_test=test_mode,
        service_token=service_token,
    )
    app.add_middleware(RenderPrivateHeadersMiddleware)
    return app


__all__ = ["create_app"]

"""Health-only application and readiness contracts for all HTTP processes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from slaif_agent_site.agent_api import create_app as create_agent_app
from slaif_agent_site.authority import ProcessKind, authority_for
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api import create_app as create_control_app
from slaif_agent_site.editor_api import create_app as create_editor_app
from slaif_agent_site.health import ComponentStatus, ProbeResult, ReadinessProbe
from slaif_agent_site.identity.models import (
    InitialLocalAdministratorRequest,
    InitialLocalAdministratorResult,
)
from slaif_agent_site.mcp_adapter import create_app as create_mcp_app
from slaif_agent_site.media_service import create_app as create_media_app
from slaif_agent_site.render_api import create_app as create_render_app

AppFactory = Callable[..., FastAPI]
HTTP_APPS: tuple[tuple[ProcessKind, AppFactory], ...] = (
    (ProcessKind.CONTROL_API, create_control_app),
    (ProcessKind.EDITOR_API, create_editor_app),
    (ProcessKind.AGENT_API, create_agent_app),
    (ProcessKind.RENDER_API, create_render_app),
    (ProcessKind.MCP_ADAPTER, create_mcp_app),
    (ProcessKind.MEDIA_SERVICE, create_media_app),
)


class FakeControlDatabase:
    def __init__(self, result: ProbeResult | None = None) -> None:
        self.result = result or ProbeResult.ready()
        self.started = 0
        self.stopped = 0

    async def start(self) -> None:
        self.started += 1

    async def stop(self) -> None:
        self.stopped += 1

    async def readiness(self) -> ProbeResult:
        return self.result

    async def setup_status(self) -> tuple[bool, bool]:
        raise AssertionError("health-only app cannot invoke setup status")

    def human_session_service(self) -> Any:
        raise AssertionError("health-only app cannot invoke sessions")

    async def authenticate_local_login(self, _request: Any) -> Any:
        raise AssertionError("health-only app cannot invoke login")

    async def authorize_platform_administrator(self, _user_id: Any) -> bool:
        raise AssertionError("health-only app cannot invoke authorization")

    def site_service(self) -> Any:
        raise AssertionError("health-only app cannot invoke site service")

    def human_authorization_service(self) -> Any:
        raise AssertionError("health-only app cannot invoke membership service")

    async def create_initial_local_administrator(
        self, _request: InitialLocalAdministratorRequest
    ) -> InitialLocalAdministratorResult:
        raise AssertionError("health-only app cannot invoke initial setup")


def _route_paths(app: FastAPI) -> set[str]:
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    for route in app.routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            paths.update(
                child.path for child in original.routes if isinstance(child, APIRoute)
            )
    return paths


@pytest.mark.parametrize(("process", "factory"), HTTP_APPS)
async def test_each_app_has_only_typed_health_routes(
    process: ProcessKind, factory: AppFactory
) -> None:
    database = FakeControlDatabase()
    arguments: dict[str, object] = {"settings": ServiceSettings.for_test()}
    if process in {ProcessKind.CONTROL_API, ProcessKind.RENDER_API}:
        arguments["database"] = database
    app = factory(**arguments)
    expected_routes = {"/health/live", "/health/ready"}
    if process is ProcessKind.CONTROL_API:
        expected_routes |= {
            "/api/control/v1/setup/status",
            "/api/control/v1/setup",
            "/api/control/v1/login",
            "/api/control/v1/session",
            "/api/control/v1/logout",
            "/api/control/v1/sites",
            "/api/control/v1/sites/{site_id}",
            "/api/control/v1/sites/{site_id}/archive",
            "/api/control/v1/sites/{site_id}/domains",
            "/api/control/v1/sites/{site_id}/domains/{domain_id}",
            "/api/control/v1/roles",
            "/api/control/v1/permissions",
            "/api/control/v1/sites/{site_id}/memberships",
            "/api/control/v1/sites/{site_id}/memberships/{user_id}",
            "/api/control/v1/me/sites",
            "/api/control/v1/sites/{site_id}/my-authority",
        }
    if process is ProcessKind.EDITOR_API:
        expected_routes |= {
            "/api/editor/v1/sites/{site_id}/content-model/types",
            "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}",
            "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}/fields",
            "/api/editor/v1/sites/{site_id}/content-model/fields/{field_id}",
            "/api/editor/v1/sites/{site_id}/content-items/",
            "/api/editor/v1/sites/{site_id}/content-items/types/{type_id}",
            "/api/editor/v1/sites/{site_id}/content-items/{item_id}",
            "/api/editor/v1/sites/{site_id}/collection-views/types/{type_id}",
            "/api/editor/v1/sites/{site_id}/collection-views/{view_id}",
            "/api/editor/v1/sites/{site_id}/navigation",
            "/api/editor/v1/sites/{site_id}/navigation/{nav_id}",
            "/api/editor/v1/sites/{site_id}/theme",
            "/api/editor/v1/sites/{site_id}/pages/",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}/move",
        }
    if process is ProcessKind.RENDER_API:
        expected_routes.add("/internal/render/v1/site-context")
    assert _route_paths(app) == expected_routes
    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None
    assert app.state.process_kind is process
    assert app.state.authority is authority_for(process)

    schema = app.openapi()
    assert set(schema["paths"]) == expected_routes
    assert "LivenessResponse" in schema["components"]["schemas"]
    assert "ReadinessResponse" in schema["components"]["schemas"]
    assert "ErrorEnvelope" in schema["components"]["schemas"]

    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            live = await client.get("/health/live")
            ready = await client.get("/health/ready")
            assert live.status_code == 200
            assert live.json() == {"status": "ok", "service": process.value}
            assert ready.status_code == 200
            assert ready.json() == {
                "status": "ready",
                "service": process.value,
                "components": (
                    [{"component": "database", "status": "ok", "reason": None}]
                    if process in {ProcessKind.CONTROL_API, ProcessKind.RENDER_API}
                    else []
                ),
            }
            for hidden in ("/docs", "/redoc", "/openapi.json"):
                assert (await client.get(hidden)).status_code == 404
    if process in {ProcessKind.CONTROL_API, ProcessKind.RENDER_API}:
        assert database.started == database.stopped == 1


async def test_readiness_aggregates_success_failure_timeout_and_sanitizes_error() -> (
    None
):
    async def healthy() -> ProbeResult:
        return ProbeResult.ready()

    async def unavailable() -> ProbeResult:
        return ProbeResult.unavailable("dependency_unavailable")

    async def slow() -> ProbeResult:
        await asyncio.sleep(0.2)
        return ProbeResult.ready()

    async def raises_internal_error() -> ProbeResult:
        raise RuntimeError("password=local-fixture-must-not-escape")

    settings = ServiceSettings.for_test().model_copy(
        update={"readiness_timeout_seconds": 0.05}
    )
    app = create_agent_app(
        settings=settings,
        readiness_probes=(
            ReadinessProbe("healthy", healthy),
            ReadinessProbe("unavailable", unavailable),
            ReadinessProbe("slow", slow),
            ReadinessProbe("error", raises_internal_error),
        ),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "agent-api",
        "components": [
            {"component": "healthy", "status": "ok", "reason": None},
            {
                "component": "unavailable",
                "status": "unavailable",
                "reason": "dependency_unavailable",
            },
            {"component": "slow", "status": "unavailable", "reason": "timeout"},
            {
                "component": "error",
                "status": "unavailable",
                "reason": "probe_error",
            },
        ],
    }
    assert "local-fixture" not in response.text


async def test_lifespan_has_explicit_start_and_stop_state() -> None:
    database = FakeControlDatabase()
    app = create_control_app(settings=ServiceSettings.for_test(), database=database)
    assert not hasattr(app.state, "started")
    async with app.router.lifespan_context(app):
        assert app.state.started is True
        assert database.started == 1
    assert app.state.started is False
    assert database.stopped == 1


async def test_control_liveness_is_independent_of_database_readiness() -> None:
    database = FakeControlDatabase(ProbeResult.unavailable("migration_mismatch"))
    app = create_control_app(settings=ServiceSettings.for_test(), database=database)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            live = await client.get("/health/live")
            ready = await client.get("/health/ready")
    assert live.status_code == 200
    assert live.json() == {"status": "ok", "service": "control-api"}
    assert ready.status_code == 503
    assert ready.json() == {
        "status": "not_ready",
        "service": "control-api",
        "components": [
            {
                "component": "database",
                "status": "unavailable",
                "reason": "migration_mismatch",
            }
        ],
    }


def test_probe_component_and_reason_are_bounded_codes() -> None:
    async def healthy() -> ProbeResult:
        return ProbeResult.ready()

    with pytest.raises(ValueError):
        ReadinessProbe("INVALID COMPONENT", healthy)
    with pytest.raises(ValueError):
        ProbeResult.unavailable("contains internal details")
    with pytest.raises(ValueError):
        ProbeResult(status=ComponentStatus.OK, reason="unexpected_reason")
    with pytest.raises(ValueError):
        ProbeResult(status=ComponentStatus.UNAVAILABLE)

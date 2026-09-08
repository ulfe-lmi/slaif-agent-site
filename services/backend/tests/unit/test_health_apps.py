"""Health-only application and readiness contracts for all HTTP processes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from slaif_agent_site.agent_api import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseSettings
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

    def content_model_service(self) -> Any:
        raise AssertionError("health-only app cannot invoke content model service")

    async def authenticate_local_login(self, _request: Any) -> Any:
        raise AssertionError("health-only app cannot invoke login")

    async def authorize_platform_administrator(self, _user_id: Any) -> bool:
        raise AssertionError("health-only app cannot invoke authorization")

    async def resolve_human_editor_workspace(self, _site_id: Any, _user_id: Any) -> Any:
        raise AssertionError("health-only app cannot invoke workspace resolution")

    def site_service(self) -> Any:
        raise AssertionError("health-only app cannot invoke site service")

    def human_authorization_service(self) -> Any:
        raise AssertionError("health-only app cannot invoke membership service")

    async def create_initial_local_administrator(
        self, _request: InitialLocalAdministratorRequest
    ) -> InitialLocalAdministratorResult:
        raise AssertionError("health-only app cannot invoke initial setup")


class FakeAgentDatabase(FakeControlDatabase):
    def content_model_service(self) -> Any:
        return object()

    def cow_pool(self) -> Any:
        raise AssertionError("health-only app cannot invoke COW mutations")

    async def authenticate_agent_capability(self, _auth_header: str) -> Any:
        raise AssertionError("health-only app cannot invoke capability auth")


class FakeMediaStore:
    async def readiness(self) -> bool:
        return True


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
    database = (
        FakeAgentDatabase()
        if process is ProcessKind.AGENT_API
        else FakeControlDatabase()
    )
    editor_database = FakeAgentDatabase() if process is ProcessKind.EDITOR_API else None
    arguments: dict[str, object] = {"settings": ServiceSettings.for_test()}
    if process in {
        ProcessKind.CONTROL_API,
        ProcessKind.EDITOR_API,
        ProcessKind.RENDER_API,
        ProcessKind.AGENT_API,
        ProcessKind.MEDIA_SERVICE,
    }:
        arguments["database"] = database
    if process is ProcessKind.MEDIA_SERVICE:
        arguments["database"] = database
        arguments["store"] = FakeMediaStore()
    if editor_database is not None:
        arguments["editor_database"] = editor_database
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
            "/api/control/v1/sites/{site_id}/workspaces/",
            "/api/control/v1/sites/{site_id}/workspaces/{workspace_id}",
            "/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/capabilities/",
            "/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/capabilities/{capability_id}/revoke",
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
            "/api/editor/v1/sites/{site_id}/content-items/{item_id}/translations",
            "/api/editor/v1/sites/{site_id}/content-items/{item_id}/translations/{translation_id}",
            "/api/editor/v1/sites/{site_id}/content-items/{item_id}/relations",
            "/api/editor/v1/sites/{site_id}/content-items/{item_id}/relations/{relation_id}",
            "/api/editor/v1/sites/{site_id}/collection-views/types/{type_id}",
            "/api/editor/v1/sites/{site_id}/collection-views/{view_id}",
            "/api/editor/v1/sites/{site_id}/navigation",
            "/api/editor/v1/sites/{site_id}/navigation/{nav_id}",
            "/api/editor/v1/sites/{site_id}/navigation/{navigation_id}/items",
            "/api/editor/v1/sites/{site_id}/navigation-items/{item_id}",
            "/api/editor/v1/sites/{site_id}/navigation-items/{item_id}/move",
            "/api/editor/v1/sites/{site_id}/locales",
            "/api/editor/v1/sites/{site_id}/locales/{locale_id}",
            "/api/editor/v1/sites/{site_id}/redirects",
            "/api/editor/v1/sites/{site_id}/redirects/{redirect_id}",
            "/api/editor/v1/sites/{site_id}/theme",
            "/api/editor/v1/sites/{site_id}/pages/",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}",
            "/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/components/{node_id}/move",
            "/api/editor/v1/sites/{site_id}/media/",
            "/api/editor/v1/sites/{site_id}/media/{media_id}",
        }
    if process is ProcessKind.MEDIA_SERVICE:
        expected_routes |= {
            "/v1/sites/{site_id}/assets",
            "/v1/sites/{site_id}/assets/{media_id}/content",
        }
    if process is ProcessKind.MCP_ADAPTER:
        expected_routes |= {
            "/mcp/v1/health/live",
            "/mcp/v1/tools",
            "/mcp/v1/call",
        }
    if process is ProcessKind.AGENT_API:
        expected_routes |= {
            "/api/agent/v1/session",
            "/api/agent/v1/permissions",
            "/api/agent/v1/content-model/primitives",
            "/api/agent/v1/content-model/types",
            "/api/agent/v1/content-model/types/{type_id}",
            "/api/agent/v1/content-model/types/{type_id}/fields",
            "/api/agent/v1/content-model/types/{type_id}/fields/{field_id}",
            "/api/agent/v1/content-items/types/{type_id}",
            "/api/agent/v1/content-items/{item_id}",
            "/api/agent/v1/content-items/{item_id}/translations",
            "/api/agent/v1/content-items/{item_id}/translations/{translation_id}",
            "/api/agent/v1/content-items/{item_id}/relations",
            "/api/agent/v1/content-items/{item_id}/relations/{relation_id}",
            "/api/agent/v1/collection-views/types/{type_id}",
            "/api/agent/v1/collection-views/{view_id}",
            "/api/agent/v1/locales",
            "/api/agent/v1/locales/{locale_id}",
            "/api/agent/v1/redirects",
            "/api/agent/v1/redirects/{redirect_id}",
            "/api/agent/v1/navigation",
            "/api/agent/v1/navigation/{navigation_id}",
            "/api/agent/v1/navigation/{navigation_id}/items",
            "/api/agent/v1/navigation-items/{item_id}",
            "/api/agent/v1/navigation-items/{item_id}:move",
            "/api/agent/v1/pages/",
            "/api/agent/v1/pages",
            "/api/agent/v1/pages/{page_id}",
            "/api/agent/v1/pages/{page_id}:move",
            "/api/agent/v1/pages/{page_id}:restore",
            "/api/agent/v1/pages/{page_id}/components",
            "/api/agent/v1/media/",
            "/api/agent/v1/preview-runs",
            "/api/agent/v1/preview-runs/{run_id}",
            "/api/agent/v1/preview-runs/{run_id}/artifacts",
            "/api/agent/v1/preview-runs/{run_id}/artifacts/{artifact_id}",
            "/api/agent/v1/openapi.json",
        }
    if process is ProcessKind.RENDER_API:
        expected_routes.add("/internal/render/v1/site-context")
        expected_routes |= {
            "/internal/render/v1/page",
            "/internal/render/v1/preview",
        }
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
                "components": [
                    {"component": "database", "status": "ok", "reason": None},
                    *(
                        [
                            {
                                "component": "media_store",
                                "status": "ok",
                                "reason": None,
                            }
                        ]
                        if process is ProcessKind.MEDIA_SERVICE
                        else []
                    ),
                    *(
                        [
                            {
                                "component": "editor_database",
                                "status": "ok",
                                "reason": None,
                            }
                        ]
                        if process is ProcessKind.EDITOR_API
                        else []
                    ),
                ]
                if process
                in {
                    ProcessKind.CONTROL_API,
                    ProcessKind.EDITOR_API,
                    ProcessKind.RENDER_API,
                    ProcessKind.AGENT_API,
                    ProcessKind.MEDIA_SERVICE,
                }
                else [],
            }
            for hidden in ("/docs", "/redoc", "/openapi.json"):
                assert (await client.get(hidden)).status_code == 404
    if process in {
        ProcessKind.CONTROL_API,
        ProcessKind.EDITOR_API,
        ProcessKind.RENDER_API,
        ProcessKind.AGENT_API,
        ProcessKind.MEDIA_SERVICE,
    }:
        assert database.started == database.stopped == 1
    if editor_database is not None:
        assert editor_database.started == editor_database.stopped == 1


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
    database = FakeAgentDatabase()
    app = create_agent_app(
        settings=settings,
        database=database,
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
            {"component": "database", "status": "ok", "reason": None},
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


async def test_agent_bad_browser_signing_key_blocks_only_readiness(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "browser-signing"
    directory.mkdir(mode=0o700)
    key_file = directory / "signing-key"
    key_file.write_text("invalid-browser-key", encoding="ascii")
    key_file.chmod(0o400)
    database = FakeAgentDatabase()
    app = create_agent_app(
        settings=ServiceSettings(),
        database_settings=AgentDatabaseSettings(browser_signing_key_file=key_file),
        database=database,
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            live = await client.get("/health/live")
            ready = await client.get("/health/ready")
    assert live.status_code == 200
    assert ready.status_code == 503
    assert ready.json()["components"] == [
        {"component": "database", "status": "ok", "reason": None},
        {
            "component": "browser-signing-key",
            "status": "unavailable",
            "reason": "signing_key_unavailable",
        },
        {
            "component": "browser-worker-client",
            "status": "unavailable",
            "reason": "worker_credential_unavailable",
        },
        {
            "component": "browser-dispatcher",
            "status": "unavailable",
            "reason": "dispatcher_dependency_unavailable",
        },
    ]


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

"""Exact Control/Editor route-policy declaration registry evidence."""

from __future__ import annotations

from typing import Any, cast

import httpx
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from slaif_agent_site.authority import ProcessKind
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.content_model.page_models import UpdatePageRequest
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.route_policy import (
    ROUTE_POLICIES,
    RouteAuthorityKind,
    RouteConditionalScope,
    RouteMutationClass,
    RoutePolicy,
    RoutePolicyKind,
    conditional_scopes_for_fields,
    route_policies_for,
    validate_conditional_scope_openapi_document,
    validate_conditional_scope_schema,
    validate_route_policy_coverage,
)
from slaif_agent_site.editor_api import create_app as create_editor_app
from slaif_agent_site.health import ProbeResult


class PolicyDatabase:
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()


def test_registry_exact_inventory_and_policy_shapes() -> None:
    keys = [policy.key for policy in ROUTE_POLICIES]
    assert len(keys) == len(set(keys)) == 152
    assert {policy.process for policy in ROUTE_POLICIES} == {
        ProcessKind.CONTROL_API,
        ProcessKind.EDITOR_API,
        ProcessKind.AGENT_API,
    }
    control = route_policies_for(ProcessKind.CONTROL_API)
    editor = route_policies_for(ProcessKind.EDITOR_API)
    agent = route_policies_for(ProcessKind.AGENT_API)
    assert len(agent) == 52
    assert all(
        policy.authority_kind
        in {RouteAuthorityKind.AGENT_CAPABILITY, RouteAuthorityKind.SYSTEM_EXEMPTION}
        for policy in agent
    )
    assert len(control) == 31
    assert len(editor) == 69
    health_routes = [p for p in editor if p.path_template.startswith("/health")]
    assert len(health_routes) == 2
    assert all(
        policy.policy_kind is RoutePolicyKind.SYSTEM_HEALTH for policy in health_routes
    )
    content_routes = [p for p in editor if "content-model" in p.path_template]
    assert len(content_routes) == 10
    assert all(
        policy.policy_kind is RoutePolicyKind.SITE_PERMISSION
        and policy.authority_kind is RouteAuthorityKind.SITE_PERMISSION
        for policy in content_routes
    )
    membership = [
        policy for policy in control if "/memberships" in policy.path_template
    ]
    assert len(membership) == 5
    assert all(
        policy.authority_kind is RouteAuthorityKind.SITE_PERMISSION
        and policy.required_permissions == ("membership:manage", "role:manage")
        for policy in membership
    )
    assert all(
        policy.csrf_required is (policy.mutation_class is RouteMutationClass.MUTATION)
        for policy in membership
    )
    current_human = [
        policy
        for policy in control
        if policy.policy_kind is RoutePolicyKind.CURRENT_HUMAN_READ
    ]
    assert [policy.path_template for policy in current_human] == [
        "/api/control/v1/me/sites",
        "/api/control/v1/sites/{site_id}/my-authority",
    ]
    assert all(
        policy.authority_kind is RouteAuthorityKind.AUTHENTICATED_SESSION
        and policy.mutation_class is RouteMutationClass.READ
        and not policy.csrf_required
        and not policy.required_permissions
        for policy in current_human
    )


def test_registry_rejects_unknown_permission_and_invalid_csrf_shape() -> None:
    with pytest.raises(ValueError, match="unknown permission"):
        RoutePolicy(
            ProcessKind.CONTROL_API,
            "GET",
            "/synthetic",
            RouteMutationClass.READ,
            True,
            False,
            RouteAuthorityKind.SITE_PERMISSION,
            RoutePolicyKind.SITE_PERMISSION,
            ("unknown:permission",),
        )
    with pytest.raises(ValueError, match="CSRF"):
        RoutePolicy(
            ProcessKind.CONTROL_API,
            "GET",
            "/synthetic",
            RouteMutationClass.READ,
            True,
            True,
            RouteAuthorityKind.AUTHENTICATED_SESSION,
            RoutePolicyKind.AUTHENTICATED_SESSION_READ,
        )


def test_agent_page_patch_conditional_route_scope_is_machine_auditable() -> None:
    page_patch = next(
        policy
        for policy in route_policies_for(ProcessKind.AGENT_API)
        if policy.method == "PATCH"
        and policy.path_template == "/api/agent/v1/pages/{page_id}"
    )
    assert page_patch.conditional_scopes == (
        RouteConditionalScope(
            when_fields=("slug", "locale", "route_template"),
            required_scopes=("route:write",),
        ),
    )
    assert (
        conditional_scopes_for_fields(
            ProcessKind.AGENT_API,
            "PATCH",
            "/api/agent/v1/pages/{page_id}",
            {"title", "status"},
        )
        == ()
    )
    assert conditional_scopes_for_fields(
        ProcessKind.AGENT_API,
        "PATCH",
        "/api/agent/v1/pages/{page_id}",
        {"route_template"},
    ) == ("route:write",)


def test_conditional_scope_validation_rejects_scope_field_read_and_metadata_drift() -> (
    None
):
    with pytest.raises(ValueError, match="invalid Agent scope"):
        RouteConditionalScope(("title",), ("not-a-scope",))

    app = FastAPI()

    @app.patch("/api/agent/v1/synthetic")
    async def synthetic(body: UpdatePageRequest) -> dict[str, str]:
        return {"title": body.title or ""}

    route = next(
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.endswith("synthetic")
    )
    policy = RoutePolicy(
        ProcessKind.AGENT_API,
        "PATCH",
        "/api/agent/v1/synthetic",
        RouteMutationClass.MUTATION,
        False,
        False,
        RouteAuthorityKind.AGENT_CAPABILITY,
        RoutePolicyKind.AGENT_CAPABILITY,
        required_scopes=("page:write",),
        conditional_scopes=(RouteConditionalScope(("missing",), ("route:write",)),),
    )
    with pytest.raises(RuntimeError, match="absent from the request schema"):
        validate_conditional_scope_schema(route, policy)

    with pytest.raises(ValueError, match="Agent mutation"):
        RoutePolicy(
            ProcessKind.AGENT_API,
            "GET",
            "/api/agent/v1/synthetic-read",
            RouteMutationClass.READ,
            False,
            False,
            RouteAuthorityKind.AGENT_CAPABILITY,
            RoutePolicyKind.AGENT_CAPABILITY,
            conditional_scopes=(RouteConditionalScope(("title",), ("route:write",)),),
        )

    metadata_policy = RoutePolicy(
        ProcessKind.AGENT_API,
        "PATCH",
        "/api/agent/v1/synthetic",
        RouteMutationClass.MUTATION,
        False,
        False,
        RouteAuthorityKind.AGENT_CAPABILITY,
        RoutePolicyKind.AGENT_CAPABILITY,
        required_scopes=("page:write",),
        conditional_scopes=(RouteConditionalScope(("title",), ("route:write",)),),
    )
    with pytest.raises(RuntimeError, match="metadata mismatch"):
        validate_conditional_scope_openapi_document(
            {
                "paths": {
                    "/api/agent/v1/synthetic": {
                        "patch": {"x-slaif-conditional-scopes": []}
                    }
                }
            },
            (metadata_policy,),
        )


def test_actual_control_and_editor_routes_have_exact_policy_coverage() -> None:
    control = create_control_app(
        settings=ServiceSettings.for_test(),
        database=cast(Any, PolicyDatabase()),
    )
    editor = create_editor_app(settings=ServiceSettings.for_test())
    validate_route_policy_coverage(control, ProcessKind.CONTROL_API)
    validate_route_policy_coverage(editor, ProcessKind.EDITOR_API)
    assert tuple(control.state.route_policies) == route_policies_for(
        ProcessKind.CONTROL_API
    )
    assert tuple(editor.state.route_policies) == route_policies_for(
        ProcessKind.EDITOR_API
    )


def test_synthetic_undeclared_or_mismatched_route_fails_closed() -> None:
    app = create_control_app(
        settings=ServiceSettings.for_test(),
        database=cast(Any, PolicyDatabase()),
    )

    @app.post("/api/control/v1/synthetic-mutation")
    async def synthetic_mutation() -> dict[str, bool]:
        return {"unexpected": True}

    with pytest.raises(RuntimeError, match="coverage mismatch"):
        validate_route_policy_coverage(app, ProcessKind.CONTROL_API)

    # Agent API has its own route policy entries; coverage is tested separately.


@pytest.mark.anyio
async def test_head_and_options_have_deterministic_unregistered_behavior() -> None:
    app = create_control_app(
        settings=ServiceSettings.for_test(),
        database=cast(Any, PolicyDatabase()),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        head = await client.head("/api/control/v1/roles")
        options = await client.options("/api/control/v1/roles")
    assert head.status_code == options.status_code == 405

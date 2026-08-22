"""Immutable auditable policy declarations for Control and Editor HTTP routes."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Final

from fastapi.routing import APIRoute

from slaif_agent_site.authority import ProcessKind
from slaif_agent_site.human_authorization.catalog import PERMISSION_BY_KEY


class RouteMutationClass(StrEnum):
    READ = "READ"
    MUTATION = "MUTATION"


class RouteAuthorityKind(StrEnum):
    SYSTEM_EXEMPTION = "SYSTEM_EXEMPTION"
    PUBLIC = "PUBLIC"
    AUTHENTICATED_SESSION = "AUTHENTICATED_SESSION"
    PLATFORM_ADMINISTRATOR = "PLATFORM_ADMINISTRATOR"
    SITE_PERMISSION = "SITE_PERMISSION"


class RoutePolicyKind(StrEnum):
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
    PUBLIC_SETUP_STATUS = "PUBLIC_SETUP_STATUS"
    ONE_TIME_SETUP = "ONE_TIME_SETUP"
    PUBLIC_LOGIN = "PUBLIC_LOGIN"
    AUTHENTICATED_SESSION_READ = "AUTHENTICATED_SESSION_READ"
    BOUND_SESSION_CSRF = "BOUND_SESSION_CSRF"
    PLATFORM_ADMINISTRATOR = "PLATFORM_ADMINISTRATOR"
    AUTHENTICATED_CATALOG_READ = "AUTHENTICATED_CATALOG_READ"
    CURRENT_HUMAN_READ = "CURRENT_HUMAN_READ"
    SITE_PERMISSION = "SITE_PERMISSION"


@dataclass(frozen=True, slots=True)
class RoutePolicy:
    process: ProcessKind
    method: str
    path_template: str
    mutation_class: RouteMutationClass
    session_required: bool
    csrf_required: bool
    authority_kind: RouteAuthorityKind
    policy_kind: RoutePolicyKind
    required_permissions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.process not in {ProcessKind.CONTROL_API, ProcessKind.EDITOR_API}:
            raise ValueError("route policy process is not registered")
        if self.method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("route policy method is not explicit")
        if not self.path_template.startswith("/") or "//" in self.path_template:
            raise ValueError("route policy path is not normalized")
        if self.csrf_required and (
            not self.session_required
            or self.mutation_class is not RouteMutationClass.MUTATION
        ):
            raise ValueError("CSRF policy requires a bound session mutation")
        if self.required_permissions and (
            self.authority_kind is not RouteAuthorityKind.SITE_PERMISSION
            or not self.session_required
        ):
            raise ValueError("permission policy requires site session authority")
        if len(set(self.required_permissions)) != len(self.required_permissions):
            raise ValueError("route policy repeats a permission")
        if not set(self.required_permissions) <= set(PERMISSION_BY_KEY):
            raise ValueError("route policy names an unknown permission")
        if any(
            not PERMISSION_BY_KEY[permission].site_assignable
            for permission in self.required_permissions
        ):
            raise ValueError("route policy names non-site authority")
        if (self.authority_kind is RouteAuthorityKind.SITE_PERMISSION) is not bool(
            self.required_permissions
        ):
            raise ValueError("site authority requires explicit permissions")
        expected_authority = {
            RoutePolicyKind.SYSTEM_HEALTH: RouteAuthorityKind.SYSTEM_EXEMPTION,
            RoutePolicyKind.PUBLIC_SETUP_STATUS: RouteAuthorityKind.PUBLIC,
            RoutePolicyKind.ONE_TIME_SETUP: RouteAuthorityKind.PUBLIC,
            RoutePolicyKind.PUBLIC_LOGIN: RouteAuthorityKind.PUBLIC,
            RoutePolicyKind.AUTHENTICATED_SESSION_READ: (
                RouteAuthorityKind.AUTHENTICATED_SESSION
            ),
            RoutePolicyKind.BOUND_SESSION_CSRF: (
                RouteAuthorityKind.AUTHENTICATED_SESSION
            ),
            RoutePolicyKind.PLATFORM_ADMINISTRATOR: (
                RouteAuthorityKind.PLATFORM_ADMINISTRATOR
            ),
            RoutePolicyKind.AUTHENTICATED_CATALOG_READ: (
                RouteAuthorityKind.AUTHENTICATED_SESSION
            ),
            RoutePolicyKind.CURRENT_HUMAN_READ: (
                RouteAuthorityKind.AUTHENTICATED_SESSION
            ),
            RoutePolicyKind.SITE_PERMISSION: RouteAuthorityKind.SITE_PERMISSION,
        }[self.policy_kind]
        if self.authority_kind is not expected_authority:
            raise ValueError("route policy kind and authority mismatch")
        expected_session = self.authority_kind not in {
            RouteAuthorityKind.SYSTEM_EXEMPTION,
            RouteAuthorityKind.PUBLIC,
        }
        if self.session_required is not expected_session:
            raise ValueError("route policy session shape mismatch")
        expected_csrf = self.policy_kind is RoutePolicyKind.BOUND_SESSION_CSRF or (
            self.authority_kind
            in {
                RouteAuthorityKind.PLATFORM_ADMINISTRATOR,
                RouteAuthorityKind.SITE_PERMISSION,
            }
            and self.mutation_class is RouteMutationClass.MUTATION
        )
        if self.csrf_required is not expected_csrf:
            raise ValueError("route policy CSRF shape mismatch")

    @property
    def key(self) -> tuple[ProcessKind, str, str]:
        return self.process, self.method, self.path_template


def _policy(
    process: ProcessKind,
    method: str,
    path: str,
    mutation: RouteMutationClass,
    session: bool,
    csrf: bool,
    authority: RouteAuthorityKind,
    kind: RoutePolicyKind,
    *permissions: str,
) -> RoutePolicy:
    return RoutePolicy(
        process=process,
        method=method,
        path_template=path,
        mutation_class=mutation,
        session_required=session,
        csrf_required=csrf,
        authority_kind=authority,
        policy_kind=kind,
        required_permissions=tuple(permissions),
    )


_R = RouteMutationClass.READ
_M = RouteMutationClass.MUTATION
_CONTROL = ProcessKind.CONTROL_API
_EDITOR = ProcessKind.EDITOR_API
_HEALTH = RouteAuthorityKind.SYSTEM_EXEMPTION
_PUBLIC = RouteAuthorityKind.PUBLIC
_SESSION = RouteAuthorityKind.AUTHENTICATED_SESSION
_ADMIN = RouteAuthorityKind.PLATFORM_ADMINISTRATOR
_SITE = RouteAuthorityKind.SITE_PERMISSION

ROUTE_POLICIES: Final[tuple[RoutePolicy, ...]] = (
    *(
        _policy(
            process,
            "GET",
            path,
            _R,
            False,
            False,
            _HEALTH,
            RoutePolicyKind.SYSTEM_HEALTH,
        )
        for process in (_CONTROL, _EDITOR)
        for path in ("/health/live", "/health/ready")
    ),
    _policy(
        _CONTROL,
        "GET",
        "/api/control/v1/setup/status",
        _R,
        False,
        False,
        _PUBLIC,
        RoutePolicyKind.PUBLIC_SETUP_STATUS,
    ),
    _policy(
        _CONTROL,
        "POST",
        "/api/control/v1/setup",
        _M,
        False,
        False,
        _PUBLIC,
        RoutePolicyKind.ONE_TIME_SETUP,
    ),
    _policy(
        _CONTROL,
        "POST",
        "/api/control/v1/login",
        _M,
        False,
        False,
        _PUBLIC,
        RoutePolicyKind.PUBLIC_LOGIN,
    ),
    _policy(
        _CONTROL,
        "GET",
        "/api/control/v1/session",
        _R,
        True,
        False,
        _SESSION,
        RoutePolicyKind.AUTHENTICATED_SESSION_READ,
    ),
    _policy(
        _CONTROL,
        "POST",
        "/api/control/v1/logout",
        _M,
        True,
        True,
        _SESSION,
        RoutePolicyKind.BOUND_SESSION_CSRF,
    ),
    *(
        _policy(
            _CONTROL,
            method,
            path,
            mutation,
            True,
            mutation is _M,
            _ADMIN,
            RoutePolicyKind.PLATFORM_ADMINISTRATOR,
        )
        for method, path, mutation in (
            ("GET", "/api/control/v1/sites", _R),
            ("POST", "/api/control/v1/sites", _M),
            ("POST", "/api/control/v1/sites/{site_id}/archive", _M),
        )
    ),
    *(
        _policy(
            _CONTROL,
            method,
            path,
            mutation,
            True,
            mutation is _M,
            _SITE,
            RoutePolicyKind.SITE_PERMISSION,
            permission,
        )
        for method, path, mutation, permission in (
            ("GET", "/api/control/v1/sites/{site_id}", _R, "site:read"),
            ("PATCH", "/api/control/v1/sites/{site_id}", _M, "site-policy:manage"),
            ("GET", "/api/control/v1/sites/{site_id}/domains", _R, "site:read"),
            (
                "POST",
                "/api/control/v1/sites/{site_id}/domains",
                _M,
                "site-domain:manage",
            ),
            (
                "PUT",
                "/api/control/v1/sites/{site_id}/domains/{domain_id}",
                _M,
                "site-domain:manage",
            ),
            (
                "DELETE",
                "/api/control/v1/sites/{site_id}/domains/{domain_id}",
                _M,
                "site-domain:manage",
            ),
        )
    ),
    *(
        _policy(
            _CONTROL,
            "GET",
            path,
            _R,
            True,
            False,
            _SESSION,
            RoutePolicyKind.AUTHENTICATED_CATALOG_READ,
        )
        for path in ("/api/control/v1/roles", "/api/control/v1/permissions")
    ),
    *(
        _policy(
            _CONTROL,
            "GET",
            path,
            _R,
            True,
            False,
            _SESSION,
            RoutePolicyKind.CURRENT_HUMAN_READ,
        )
        for path in (
            "/api/control/v1/me/sites",
            "/api/control/v1/sites/{site_id}/my-authority",
        )
    ),
    *(
        _policy(
            _CONTROL,
            method,
            path,
            mutation,
            True,
            mutation is _M,
            _SITE,
            RoutePolicyKind.SITE_PERMISSION,
            "membership:manage",
            "role:manage",
        )
        for method, path, mutation in (
            ("GET", "/api/control/v1/sites/{site_id}/memberships", _R),
            ("GET", "/api/control/v1/sites/{site_id}/memberships/{user_id}", _R),
            ("POST", "/api/control/v1/sites/{site_id}/memberships", _M),
            ("PATCH", "/api/control/v1/sites/{site_id}/memberships/{user_id}", _M),
            ("DELETE", "/api/control/v1/sites/{site_id}/memberships/{user_id}", _M),
        )
    ),
    *(
        _policy(
            _EDITOR,
            method,
            path,
            mutation,
            True,
            csrf,
            _SITE,
            RoutePolicyKind.SITE_PERMISSION,
            permission,
        )
        for method, path, mutation, csrf, permission in (
            (
                "POST",
                "/api/editor/v1/sites/{site_id}/content-model/types",
                _M,
                True,
                "content-model:create",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/content-model/types",
                _R,
                False,
                "content-model:read",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}",
                _R,
                False,
                "content-model:read",
            ),
            (
                "PATCH",
                "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}",
                _M,
                True,
                "content-model:write",
            ),
            (
                "DELETE",
                "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}",
                _M,
                True,
                "content-model:delete",
            ),
            (
                "POST",
                "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}/fields",
                _M,
                True,
                "field-definition:create",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/content-model/types/{type_id}/fields",
                _R,
                False,
                "content-model:read",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/content-model/fields/{field_id}",
                _R,
                False,
                "content-model:read",
            ),
            (
                "PATCH",
                "/api/editor/v1/sites/{site_id}/content-model/fields/{field_id}",
                _M,
                True,
                "field-definition:write",
            ),
            (
                "DELETE",
                "/api/editor/v1/sites/{site_id}/content-model/fields/{field_id}",
                _M,
                True,
                "field-definition:delete",
            ),
        )
    ),
    *(
        _policy(
            _EDITOR,
            method,
            path,
            mutation,
            True,
            csrf,
            _SITE,
            RoutePolicyKind.SITE_PERMISSION,
            permission,
        )
        for method, path, mutation, csrf, permission in (
            (
                "POST",
                "/api/editor/v1/sites/{site_id}/content-items/",
                _M,
                True,
                "content-item:create",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/content-items/types/{type_id}",
                _R,
                False,
                "content-item:read",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/content-items/{item_id}",
                _R,
                False,
                "content-item:read",
            ),
            (
                "PATCH",
                "/api/editor/v1/sites/{site_id}/content-items/{item_id}",
                _M,
                True,
                "content-item:write",
            ),
            (
                "DELETE",
                "/api/editor/v1/sites/{site_id}/content-items/{item_id}",
                _M,
                True,
                "content-item:delete",
            ),
        )
    ),
    *(
        _policy(
            _EDITOR,
            method,
            path,
            mutation,
            True,
            csrf,
            _SITE,
            RoutePolicyKind.SITE_PERMISSION,
            permission,
        )
        for method, path, mutation, csrf, permission in (
            (
                "POST",
                "/api/editor/v1/sites/{site_id}/collection-views/types/{type_id}",
                _M,
                True,
                "collection-view:create",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/collection-views/types/{type_id}",
                _R,
                False,
                "collection-view:read",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/collection-views/{view_id}",
                _R,
                False,
                "collection-view:read",
            ),
            (
                "PATCH",
                "/api/editor/v1/sites/{site_id}/collection-views/{view_id}",
                _M,
                True,
                "collection-view:write",
            ),
            (
                "DELETE",
                "/api/editor/v1/sites/{site_id}/collection-views/{view_id}",
                _M,
                True,
                "collection-view:delete",
            ),
        )
    ),
    *(
        _policy(
            _EDITOR,
            method,
            path,
            mutation,
            True,
            csrf,
            _SITE,
            RoutePolicyKind.SITE_PERMISSION,
            permission,
        )
        for method, path, mutation, csrf, permission in (
            (
                "POST",
                "/api/editor/v1/sites/{site_id}/navigation",
                _M,
                True,
                "navigation:create",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/navigation",
                _R,
                False,
                "navigation:read",
            ),
            (
                "GET",
                "/api/editor/v1/sites/{site_id}/navigation/{nav_id}",
                _R,
                False,
                "navigation:read",
            ),
            (
                "PATCH",
                "/api/editor/v1/sites/{site_id}/navigation/{nav_id}",
                _M,
                True,
                "navigation:write",
            ),
            (
                "DELETE",
                "/api/editor/v1/sites/{site_id}/navigation/{nav_id}",
                _M,
                True,
                "navigation:delete",
            ),
            ("GET", "/api/editor/v1/sites/{site_id}/theme", _R, False, "theme:read"),
            (
                "PATCH",
                "/api/editor/v1/sites/{site_id}/theme",
                _M,
                True,
                "theme-global:write",
            ),
        )
    ),
)

_POLICY_BY_KEY = MappingProxyType({policy.key: policy for policy in ROUTE_POLICIES})
if len(_POLICY_BY_KEY) != len(ROUTE_POLICIES):
    raise RuntimeError("duplicate Control/Editor route policy")


def route_policies_for(process: ProcessKind) -> tuple[RoutePolicy, ...]:
    return tuple(policy for policy in ROUTE_POLICIES if policy.process is process)


def _api_routes(routes: list[Any]) -> tuple[APIRoute, ...]:
    found: list[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            found.append(route)
            continue
        original = getattr(route, "original_router", None)
        if original is not None:
            found.extend(_api_routes(list(original.routes)))
    return tuple(found)


def validate_route_policy_coverage(app: Any, process: ProcessKind) -> None:
    """Fail closed on missing, stale, duplicate, or handler-shape policy."""

    declared = {policy.key: policy for policy in route_policies_for(process)}
    actual: dict[tuple[ProcessKind, str, str], APIRoute] = {}
    for route in _api_routes(list(app.routes)):
        for method in sorted(route.methods or set()):
            key = (process, method, route.path)
            if key in actual:
                raise RuntimeError("duplicate actual Control/Editor route")
            actual[key] = route
    if actual.keys() != declared.keys():
        raise RuntimeError("Control/Editor route policy coverage mismatch")
    for key, route in actual.items():
        policy = declared[key]
        if (
            policy.session_required
            and "request" not in inspect.signature(route.endpoint).parameters
        ):
            raise RuntimeError("session route lacks a request-bound handler")
        if policy.method in {"GET"} and policy.mutation_class is not _R:
            raise RuntimeError("safe method declared as mutation")
        if policy.method in {"POST", "PUT", "PATCH", "DELETE"} and (
            policy.mutation_class is not _M
        ):
            raise RuntimeError("mutating method declared as read")
    app.state.route_policies = route_policies_for(process)


__all__ = [
    "ROUTE_POLICIES",
    "RouteAuthorityKind",
    "RouteMutationClass",
    "RoutePolicy",
    "RoutePolicyKind",
    "route_policies_for",
    "validate_route_policy_coverage",
]

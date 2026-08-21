"""Real session, CSRF, PostgreSQL, and FastAPI membership HTTP evidence."""

from __future__ import annotations

import asyncio
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.bootstrap.service import ensure_setup_token, reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.human_authorization import ROLE_CEILINGS, ROLE_DEFAULTS

_PASSWORD = "fixture-membership-http-password-123"
_PRIVATE = {
    "cache-control": "private, no-store",
    "pragma": "no-cache",
    "x-robots-tag": "noindex, nofollow, noarchive",
}


def _database_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=8,
        application_name="slaif-membership-http-test",
    )


def _read(token: str) -> dict[str, str]:
    return {"cookie": f"slaif_session={token}"}


def _mutate(token: str, csrf: str) -> dict[str, str]:
    return {
        "cookie": f"slaif_session={token}; slaif_csrf={csrf}",
        "x-csrf-token": csrf,
    }


def _assert_private(response: httpx.Response) -> None:
    assert {name: response.headers[name] for name in _PRIVATE} == _PRIVATE
    assert len(response.headers.get_list("x-request-id")) == 1


def _assert_safe(response: httpx.Response) -> None:
    _assert_private(response)
    lowered = response.text.lower()
    for forbidden in (
        "password",
        "cookie",
        "session",
        "digest",
        "postgresql://",
        "select ",
    ):
        assert forbidden not in lowered


async def _setup(
    database: AgentSiteDatabase,
) -> tuple[ControlDatabase, httpx.AsyncClient, UUID, str, str]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(database.settings)
    assert issued.setup_token is not None
    adapter = ControlDatabase(_database_settings(database))
    await adapter.start()
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(
            app=create_app(
                settings=ServiceSettings(mode=EnvironmentMode.TEST),
                database=adapter,
            )
        ),
        base_url="http://control.test",
    )
    response = await client.post(
        "/api/control/v1/setup",
        json={
            "setup_token": issued.setup_token.get_secret_value(),
            "username": "Membership.Admin",
            "password": _PASSWORD,
            "display_name": "Membership Administrator",
        },
    )
    assert response.status_code == 200
    administrator = UUID(response.json()["user_account_id"])
    token = response.cookies["slaif_session"]
    csrf = response.cookies["slaif_csrf"]
    client.cookies.clear()
    return adapter, client, administrator, token, csrf


async def _user(
    database: AgentSiteDatabase, label: str, *, active: bool = True
) -> UUID:
    identifier = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.user_account (id,identity_kind,oidc_issuer,"
            "oidc_subject,display_name,status) VALUES "
            "($1,'OIDC','https://identity.example.test',$2,$3,$4)",
            identifier,
            str(identifier),
            label,
            "ACTIVE" if active else "DISABLED",
        )
    return identifier


async def _human_headers(
    adapter: ControlDatabase, user_id: UUID
) -> tuple[dict[str, str], dict[str, str]]:
    issued = await adapter.human_session_service().create(user_id)
    token = issued.token.get_secret_value()
    csrf = issued.csrf_token.get_secret_value()
    return _read(token), _mutate(token, csrf)


async def _site(client: httpx.AsyncClient, headers: dict[str, str], key: str) -> UUID:
    response = await client.post(
        "/api/control/v1/sites",
        headers=headers,
        json={
            "site_key": key,
            "display_name": key.title(),
            "default_locale": "en",
        },
    )
    assert response.status_code == 201
    return UUID(response.json()["site_id"])


def _membership(
    target: UUID,
    role: str,
    ceiling: int,
    *,
    allow: list[str] | None = None,
    deny: list[str] | None = None,
) -> dict[str, object]:
    return {
        "target_user_id": str(target),
        "role_key": role,
        "delegation_ceiling": ceiling,
        "allow_permissions": allow or [],
        "deny_permissions": deny or [],
    }


@pytest.mark.asyncio
async def test_catalog_membership_lifecycle_authority_and_site_isolation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    adapter, client, administrator, admin_token, admin_csrf = await _setup(database)
    admin_read, admin_mutate = _read(admin_token), _mutate(admin_token, admin_csrf)
    try:
        alpha = await _site(client, admin_mutate, "alpha-membership")
        beta = await _site(client, admin_mutate, "beta-membership")

        roles = await client.get("/api/control/v1/roles", headers=admin_read)
        permissions = await client.get(
            "/api/control/v1/permissions", headers=admin_read
        )
        assert roles.status_code == permissions.status_code == 200
        assert [row["role_key"] for row in roles.json()] == list(ROLE_CEILINGS)
        assert {
            row["role_key"]: set(row["default_permissions"]) for row in roles.json()
        } == {key: set(value) for key, value in ROLE_DEFAULTS.items()}
        assert all(
            set(row)
            == {
                "permission_key",
                "category",
                "agent_delegation_level",
                "site_assignable",
                "installation_only",
                "system_only",
                "role_keys",
            }
            for row in permissions.json()
        )
        _assert_safe(roles)
        _assert_safe(permissions)

        owner = await _user(database, "Alpha Owner")
        target = await _user(database, "Two-site target")
        viewer = await _user(database, "Lower role")
        bounded_manager = await _user(database, "Bounded manager")
        bounded_target = await _user(database, "Bounded target")
        beta_only = await _user(database, "Beta-only target")
        target_admin = await _user(database, "Target administrator")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner_connection_:
            await owner_connection_.execute(
                "INSERT INTO control.platform_administrator (user_account_id) "
                "VALUES ($1)",
                target_admin,
            )

        for site_id, role, ceiling in (
            (alpha, "SITE_OWNER", 4),
            (beta, "VIEWER", 0),
        ):
            response = await client.post(
                f"/api/control/v1/sites/{site_id}/memberships",
                headers=admin_mutate,
                json=_membership(owner, role, ceiling),
            )
            assert response.status_code == 201
            assert response.json()["platform_administrator"] is False
        beta_member = await client.post(
            f"/api/control/v1/sites/{beta}/memberships",
            headers=admin_mutate,
            json=_membership(target, "CONTENT_EDITOR", 1),
        )
        assert beta_member.status_code == 201
        assert beta_member.json()["effective_delegation_ceiling"] == 1
        await client.post(
            f"/api/control/v1/sites/{beta}/memberships",
            headers=admin_mutate,
            json=_membership(beta_only, "VIEWER", 0),
        )

        owner_read, owner_mutate = await _human_headers(adapter, owner)
        created = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=owner_mutate,
            json=_membership(target, "SITE_ARCHITECT", 4),
        )
        assert created.status_code == 201
        created_body = created.json()
        assert created_body["version"] == 1
        assert created_body["effective_delegation_ceiling"] == 4
        assert "site:publish" not in created_body["effective_permissions"]
        _assert_safe(created)

        listed = await client.get(
            f"/api/control/v1/sites/{alpha}/memberships", headers=owner_read
        )
        fetched = await client.get(
            f"/api/control/v1/sites/{alpha}/memberships/{target}",
            headers=owner_read,
        )
        assert listed.status_code == fetched.status_code == 200
        assert fetched.json() == created_body
        assert {row["user_account_id"] for row in listed.json()} == {
            str(owner),
            str(target),
        }

        wrong_site = await client.get(
            f"/api/control/v1/sites/{beta}/memberships", headers=owner_read
        )
        crossed_read = await client.get(
            f"/api/control/v1/sites/{alpha}/memberships/{beta_only}",
            headers=owner_read,
        )
        crossed_write = await client.patch(
            f"/api/control/v1/sites/{alpha}/memberships/{beta_only}",
            headers=owner_mutate,
            json={
                "expected_version": 1,
                "role_key": "SITE_OWNER",
                "delegation_ceiling": 4,
                "status": "ACTIVE",
                "allow_permissions": [],
                "deny_permissions": [],
            },
        )
        assert wrong_site.status_code == 403
        assert crossed_read.status_code == crossed_write.status_code == 404

        published = await client.patch(
            f"/api/control/v1/sites/{alpha}/memberships/{target}",
            headers=owner_mutate,
            json={
                "expected_version": 1,
                "role_key": "SITE_ARCHITECT",
                "delegation_ceiling": 4,
                "status": "ACTIVE",
                "allow_permissions": ["site:publish"],
                "deny_permissions": [],
            },
        )
        assert published.status_code == 200
        assert published.json()["version"] == 2
        assert published.json()["effective_delegation_ceiling"] == 4
        assert set(published.json()["effective_permissions"]) == (
            set(created_body["effective_permissions"]) | {"site:publish"}
        )
        denied_publish = await client.patch(
            f"/api/control/v1/sites/{alpha}/memberships/{target}",
            headers=owner_mutate,
            json={
                "expected_version": 2,
                "role_key": "SITE_ARCHITECT",
                "delegation_ceiling": 4,
                "status": "ACTIVE",
                "allow_permissions": [],
                "deny_permissions": ["site:publish"],
            },
        )
        assert denied_publish.status_code == 200
        assert denied_publish.json()["version"] == 3
        assert "site:publish" not in denied_publish.json()["effective_permissions"]
        assert denied_publish.json()["effective_delegation_ceiling"] == 4

        stale = await client.patch(
            f"/api/control/v1/sites/{alpha}/memberships/{target}",
            headers=owner_mutate,
            json={
                "expected_version": 2,
                "role_key": "VIEWER",
                "delegation_ceiling": 0,
                "status": "ACTIVE",
                "allow_permissions": [],
                "deny_permissions": [],
            },
        )
        duplicate = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=owner_mutate,
            json=_membership(target, "VIEWER", 0),
        )
        assert stale.status_code == duplicate.status_code == 409

        target_admin_create = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=owner_mutate,
            json=_membership(target_admin, "VIEWER", 0),
        )
        assert target_admin_create.status_code == 201
        assert target_admin_create.json()["platform_administrator"] is True
        deactivated_admin = await client.delete(
            f"/api/control/v1/sites/{alpha}/memberships/{target_admin}",
            params={"expected_version": 1},
            headers=owner_mutate,
        )
        assert deactivated_admin.status_code == 200
        assert deactivated_admin.json()["status"] == "INACTIVE"
        assert deactivated_admin.json()["version"] == 2
        assert deactivated_admin.json()["effective_permissions"] == []
        assert deactivated_admin.json()["platform_administrator"] is True

        lower = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=owner_mutate,
            json=_membership(viewer, "VIEWER", 0),
        )
        assert lower.status_code == 201
        viewer_read, _viewer_mutate = await _human_headers(adapter, viewer)
        lower_denied = await client.get(
            f"/api/control/v1/sites/{alpha}/memberships", headers=viewer_read
        )
        assert lower_denied.status_code == 403

        manager = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=admin_mutate,
            json=_membership(
                bounded_manager,
                "SITE_EDITOR",
                2,
                allow=["membership:manage", "role:manage"],
            ),
        )
        assert manager.status_code == 201
        manager_read, manager_mutate = await _human_headers(adapter, bounded_manager)
        assert (
            await client.get(
                f"/api/control/v1/sites/{alpha}/memberships", headers=manager_read
            )
        ).status_code == 200
        ceiling_escape = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=manager_mutate,
            json=_membership(bounded_target, "SITE_ARCHITECT", 4),
        )
        permission_escape = await client.post(
            f"/api/control/v1/sites/{alpha}/memberships",
            headers=manager_mutate,
            json=_membership(
                bounded_target, "VIEWER", 0, allow=["content-model:write"]
            ),
        )
        assert ceiling_escape.status_code == permission_escape.status_code == 403
        manager_inactive = await client.patch(
            f"/api/control/v1/sites/{alpha}/memberships/{bounded_manager}",
            headers=admin_mutate,
            json={
                "expected_version": 1,
                "role_key": "SITE_EDITOR",
                "delegation_ceiling": 2,
                "status": "INACTIVE",
                "allow_permissions": ["membership:manage", "role:manage"],
                "deny_permissions": [],
            },
        )
        assert manager_inactive.status_code == 200
        assert (
            await client.get(
                f"/api/control/v1/sites/{alpha}/memberships", headers=manager_read
            )
        ).status_code == 403

        for response in (
            wrong_site,
            crossed_read,
            crossed_write,
            stale,
            duplicate,
            lower_denied,
            deactivated_admin,
            ceiling_escape,
            permission_escape,
            manager_inactive,
        ):
            _assert_safe(response)

        alpha_target = await client.get(
            f"/api/control/v1/sites/{alpha}/memberships/{target}",
            headers=admin_read,
        )
        beta_target = await client.get(
            f"/api/control/v1/sites/{beta}/memberships/{target}",
            headers=admin_read,
        )
        assert alpha_target.json()["role_key"] == "SITE_ARCHITECT"
        assert beta_target.json()["role_key"] == "CONTENT_EDITOR"
        assert alpha_target.json()["site_id"] != beta_target.json()["site_id"]
    finally:
        await client.aclose()
        await adapter.stop()


@pytest.mark.asyncio
async def test_membership_http_error_validation_csrf_and_atomic_state(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    adapter, client, administrator, admin_token, admin_csrf = await _setup(database)
    admin_read, admin_mutate = _read(admin_token), _mutate(admin_token, admin_csrf)
    try:
        site = await _site(client, admin_mutate, "membership-errors")
        owner = await _user(database, "Owner")
        target = await _user(database, "Target")
        disabled = await _user(database, "Disabled", active=False)
        await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=admin_mutate,
            json=_membership(owner, "SITE_OWNER", 4),
        )
        owner_read, owner_mutate = await _human_headers(adapter, owner)

        unauthenticated = await client.get("/api/control/v1/roles")
        missing_csrf = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=owner_read,
            json=_membership(target, "VIEWER", 0),
        )
        wrong_csrf = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers={
                "cookie": owner_mutate["cookie"],
                "x-csrf-token": "sas2_csrf_wrong",
            },
            json=_membership(target, "VIEWER", 0),
        )
        duplicate_csrf = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=[
                ("cookie", owner_mutate["cookie"]),
                ("x-csrf-token", owner_mutate["x-csrf-token"]),
                ("x-csrf-token", owner_mutate["x-csrf-token"]),
            ],
            json=_membership(target, "VIEWER", 0),
        )
        assert unauthenticated.status_code == 401
        assert (
            missing_csrf.status_code
            == wrong_csrf.status_code
            == duplicate_csrf.status_code
            == 403
        )

        invalid_bodies = (
            {**_membership(target, "UNKNOWN", 0)},
            {**_membership(target, "VIEWER", 9)},
            {**_membership(target, "VIEWER", 1)},
            {
                **_membership(target, "VIEWER", 0),
                "allow_permissions": ["unknown:permission"],
            },
            {
                **_membership(target, "VIEWER", 0),
                "allow_permissions": ["site:read"],
                "deny_permissions": ["site:read"],
            },
            {**_membership(target, "VIEWER", 0), "site_id": str(site)},
            {
                **_membership(target, "VIEWER", 0),
                "expected_version": 1,
            },
        )
        for body in invalid_bodies:
            response = await client.post(
                f"/api/control/v1/sites/{site}/memberships",
                headers=owner_mutate,
                json=body,
            )
            assert response.status_code == 422
            _assert_safe(response)

        unknown = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=owner_mutate,
            json=_membership(uuid4(), "VIEWER", 0),
        )
        inactive_target = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=owner_mutate,
            json=_membership(disabled, "VIEWER", 0),
        )
        system_scope = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=owner_mutate,
            json=_membership(target, "VIEWER", 0, allow=["schema:migrate"]),
        )
        installation_scope = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=owner_mutate,
            json=_membership(target, "VIEWER", 0, allow=["identity:configure"]),
        )
        assert unknown.status_code == 404
        assert (
            inactive_target.status_code
            == system_scope.status_code
            == installation_scope.status_code
            == 403
        )
        assert (
            await client.get(
                f"/api/control/v1/sites/{site}/memberships/{target}",
                headers=admin_read,
            )
        ).status_code == 404

        created = await client.post(
            f"/api/control/v1/sites/{site}/memberships",
            headers=owner_mutate,
            json=_membership(target, "VIEWER", 0),
        )
        assert created.status_code == 201
        self_change = await client.patch(
            f"/api/control/v1/sites/{site}/memberships/{owner}",
            headers=owner_mutate,
            json={
                "expected_version": 1,
                "role_key": "VIEWER",
                "delegation_ceiling": 0,
                "status": "ACTIVE",
                "allow_permissions": [],
                "deny_permissions": [],
            },
        )
        invalid_version = await client.delete(
            f"/api/control/v1/sites/{site}/memberships/{target}",
            params={"expected_version": 0},
            headers=owner_mutate,
        )
        assert self_change.status_code == 403
        assert invalid_version.status_code == 422
        unchanged = await client.get(
            f"/api/control/v1/sites/{site}/memberships/{target}",
            headers=owner_read,
        )
        assert unchanged.status_code == 200
        assert unchanged.json()["version"] == 1
        assert unchanged.json()["status"] == "ACTIVE"

        concurrent = await asyncio.gather(
            *(
                client.patch(
                    f"/api/control/v1/sites/{site}/memberships/{target}",
                    headers=owner_mutate,
                    json={
                        "expected_version": 1,
                        "role_key": role,
                        "delegation_ceiling": ceiling,
                        "status": "ACTIVE",
                        "allow_permissions": [],
                        "deny_permissions": [],
                    },
                )
                for role, ceiling in (("VIEWER", 0), ("CONTENT_EDITOR", 1))
            )
        )
        assert sorted(response.status_code for response in concurrent) == [200, 409]
        current = await client.get(
            f"/api/control/v1/sites/{site}/memberships/{target}",
            headers=owner_read,
        )
        assert current.json()["version"] == 2

        malformed_path = await client.get(
            "/api/control/v1/sites/not-a-uuid/memberships", headers=admin_read
        )
        missing_version = await client.delete(
            f"/api/control/v1/sites/{site}/memberships/{target}",
            headers=owner_mutate,
        )
        assert malformed_path.status_code == missing_version.status_code == 422

        archived = await client.post(
            f"/api/control/v1/sites/{site}/archive", headers=admin_mutate
        )
        assert archived.status_code == 200
        archived_read = await client.get(
            f"/api/control/v1/sites/{site}/memberships", headers=admin_read
        )
        assert archived_read.status_code == 404

        for response in (
            unauthenticated,
            missing_csrf,
            wrong_csrf,
            duplicate_csrf,
            unknown,
            inactive_target,
            system_scope,
            installation_scope,
            self_change,
            invalid_version,
            malformed_path,
            missing_version,
            archived_read,
        ):
            _assert_safe(response)
        assert administrator != owner
        await adapter.stop()
        unavailable = await client.get("/api/control/v1/roles", headers=admin_read)
        assert unavailable.status_code == 503
        _assert_safe(unavailable)
    finally:
        await client.aclose()
        await adapter.stop()

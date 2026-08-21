"""Real PostgreSQL current-human read-model isolation evidence."""

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.human_authorization import (
    HumanAuthorizationError,
    HumanAuthorizationReason,
    HumanAuthorizationService,
    MembershipChange,
)
from slaif_agent_site.sites import CreateSiteRequest, SiteService


def _settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
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
        pool_max_size=4,
        application_name="slaif-current-human-http-test",
    )


def _headers(token: str) -> dict[str, str]:
    return {"cookie": f"slaif_session={token}"}


def _assert_private(response: httpx.Response) -> None:
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"


async def _account(
    owner: asyncpg.Connection[asyncpg.Record], status: str = "ACTIVE"
) -> UUID:
    identifier = uuid4()
    await owner.execute(
        "INSERT INTO control.user_account (id, identity_kind, oidc_issuer, "
        "oidc_subject, display_name, status) VALUES ($1, 'OIDC', 'fixture', "
        "$2, 'Current human fixture', $3)",
        identifier,
        str(identifier),
        status,
    )
    return identifier


async def test_current_human_global_and_site_authority_are_server_filtered(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool = await database.role_pool("slaif_control")
    sites = SiteService(pool)
    authorization = HumanAuthorizationService(pool)
    try:
        alpha = (
            await sites.create(
                CreateSiteRequest(
                    site_key="current-alpha", display_name="Alpha", default_locale="en"
                )
            )
        ).site_id
        beta = (
            await sites.create(
                CreateSiteRequest(
                    site_key="current-beta", display_name="Beta", default_locale="sl"
                )
            )
        ).site_id
        archived = (
            await sites.create(
                CreateSiteRequest(
                    site_key="current-archived",
                    display_name="Archived",
                    default_locale="en",
                )
            )
        ).site_id
        await sites.archive(await sites.active_context(archived))
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            administrator = await _account(owner)
            owner_user = await _account(owner)
            viewer = await _account(owner)
            disabled = await _account(owner)
            await owner.execute(
                "INSERT INTO control.platform_administrator "
                "(user_account_id) VALUES ($1)",
                administrator,
            )
        await authorization.put_membership(
            administrator,
            alpha,
            owner_user,
            MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4),
        )
        await authorization.put_membership(
            administrator,
            beta,
            viewer,
            MembershipChange(role_key="VIEWER", delegation_ceiling=0),
        )
        await authorization.put_membership(
            administrator,
            alpha,
            disabled,
            MembershipChange(role_key="VIEWER", delegation_ceiling=0),
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_account SET status='DISABLED' WHERE id=$1",
                disabled,
            )

        global_sites = await authorization.current_human_sites(administrator)
        assert [item.site_key for item in global_sites] == [
            "current-alpha",
            "current-archived",
            "current-beta",
        ]
        assert all(
            item.platform_administrator and item.role_key is None
            for item in global_sites
        )
        member_sites = await authorization.current_human_sites(owner_user)
        assert [(item.site_key, item.role_key) for item in member_sites] == [
            ("current-alpha", "SITE_OWNER")
        ]
        assert await authorization.current_human_sites(disabled) == ()

        member = await authorization.current_human_authority(owner_user, alpha)
        assert member.role_key == "SITE_OWNER"
        assert "membership:manage" in member.effective_permissions
        global_authority = await authorization.current_human_authority(
            administrator, archived
        )
        assert global_authority.platform_administrator
        assert global_authority.role_key is None
        assert global_authority.effective_permissions == ()
        for user, site in ((owner_user, beta), (viewer, alpha), (disabled, alpha)):
            with pytest.raises(HumanAuthorizationError) as denied:
                await authorization.current_human_authority(user, site)
            assert denied.value.reason is HumanAuthorizationReason.NOT_FOUND

        adapter = ControlDatabase(_settings(database))
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
        try:
            admin_session = await adapter.human_session_service().create(administrator)
            owner_session = await adapter.human_session_service().create(owner_user)
            admin_headers = _headers(admin_session.token.get_secret_value())
            owner_headers = _headers(owner_session.token.get_secret_value())

            listed = await client.get("/api/control/v1/me/sites", headers=admin_headers)
            assert listed.status_code == 200
            _assert_private(listed)
            assert [item["site_key"] for item in listed.json()] == [
                "current-alpha",
                "current-archived",
                "current-beta",
            ]
            authority_response = await client.get(
                f"/api/control/v1/sites/{alpha}/my-authority", headers=owner_headers
            )
            assert authority_response.status_code == 200
            _assert_private(authority_response)
            assert list(authority_response.json()) == [
                "site_id",
                "site_key",
                "display_name",
                "status",
                "default_locale",
                "canonical_revision",
                "role_key",
                "membership_version",
                "explicit_delegation_ceiling",
                "effective_delegation_ceiling",
                "platform_administrator",
                "effective_permissions",
            ]
            denied_response = await client.get(
                f"/api/control/v1/sites/{beta}/my-authority", headers=owner_headers
            )
            malformed = await client.get(
                "/api/control/v1/sites/not-a-uuid/my-authority", headers=owner_headers
            )
            assert denied_response.status_code == 404
            denied_error = denied_response.json()["error"]
            assert denied_error["code"] == "RESOURCE_NOT_FOUND"
            assert denied_error["message"] == "The resource is not available."
            assert denied_error["request_id"].startswith("req_")
            assert malformed.status_code == 422
            _assert_private(malformed)
        finally:
            await client.aclose()
            await adapter.stop()
    finally:
        await pool.close()

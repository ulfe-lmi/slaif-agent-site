"""Real PostgreSQL and FastAPI Platform Administrator site API evidence."""

from __future__ import annotations

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
from slaif_agent_site.identity.sessions import parse_session_token

_PASSWORD = "fixture-site-http-password-123"


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
        application_name="slaif-site-http-test",
    )


def _cookie(session: str, csrf: str | None = None) -> str:
    value = f"slaif_session={session}"
    return value if csrf is None else f"{value}; slaif_csrf={csrf}"


def _get_headers(session: str) -> dict[str, str]:
    return {"cookie": _cookie(session)}


def _mutation_headers(session: str, csrf: str) -> dict[str, str]:
    return {"cookie": _cookie(session, csrf), "x-csrf-token": csrf}


def _assert_private(response: httpx.Response) -> None:
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
    assert len(response.headers.get_list("x-request-id")) == 1


async def _setup(
    database: AgentSiteDatabase,
) -> tuple[ControlDatabase, httpx.AsyncClient, str, str]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(database.settings)
    assert issued.setup_token is not None
    adapter = ControlDatabase(_settings(database))
    await adapter.start()
    app = create_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST), database=adapter
    )
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://control.test"
    )
    response = await client.post(
        "/api/control/v1/setup",
        json={
            "setup_token": issued.setup_token.get_secret_value(),
            "username": "Site.Admin",
            "password": _PASSWORD,
            "display_name": "Site Administrator",
        },
    )
    assert response.status_code == 200
    session = response.cookies["slaif_session"]
    csrf = response.cookies["slaif_csrf"]
    client.cookies.clear()
    return adapter, client, session, csrf


@pytest.mark.asyncio
async def test_platform_administrator_site_lifecycle_and_isolation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    adapter, client, session, csrf = await _setup(database)
    read = _get_headers(session)
    mutate = _mutation_headers(session, csrf)
    try:
        created: list[dict[str, object]] = []
        for key, locale in (("alpha", "sl-si"), ("beta", "de-de")):
            response = await client.post(
                "/api/control/v1/sites",
                headers=mutate,
                json={
                    "site_key": key,
                    "display_name": key.title(),
                    "default_locale": locale,
                },
            )
            assert response.status_code == 201
            _assert_private(response)
            created.append(response.json())
        alpha, beta = created
        alpha_id, beta_id = str(alpha["site_id"]), str(beta["site_id"])

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.site_policy SET max_sites = 2 WHERE singleton"
            )
        quota = await client.post(
            "/api/control/v1/sites",
            headers=mutate,
            json={
                "site_key": "over-quota",
                "display_name": "Over Quota",
                "default_locale": "en",
            },
        )
        assert quota.status_code == 409

        listed = await client.get("/api/control/v1/sites", headers=read)
        assert listed.status_code == 200
        assert [row["site_key"] for row in listed.json()] == ["alpha", "beta"]
        _assert_private(listed)
        fetched = await client.get(f"/api/control/v1/sites/{alpha_id}", headers=read)
        assert fetched.status_code == 200
        updated = await client.patch(
            f"/api/control/v1/sites/{alpha_id}",
            headers=mutate,
            json={"display_name": "Alpha Updated", "default_locale": "fr-fr"},
        )
        assert updated.status_code == 200
        assert updated.json()["default_locale"] == "fr-FR"

        domains: list[dict[str, object]] = []
        for site_id, hostname, prefix in (
            (alpha_id, "A.EXAMPLE.TEST.", "/Alpha"),
            (beta_id, "b.example.test", "/Beta"),
        ):
            response = await client.post(
                f"/api/control/v1/sites/{site_id}/domains",
                headers=mutate,
                json={
                    "hostname": hostname,
                    "path_prefix": prefix,
                    "is_primary": True,
                },
            )
            assert response.status_code == 201
            domains.append(response.json())
        alpha_domain, beta_domain = domains
        replaced = await client.put(
            f"/api/control/v1/sites/{alpha_id}/domains/{alpha_domain['domain_id']}",
            headers=mutate,
            json={
                "hostname": "A.EXAMPLE.TEST",
                "path_prefix": "/Alpha",
                "is_primary": True,
            },
        )
        assert replaced.status_code == 200
        alpha_domain = replaced.json()
        temporary = await client.post(
            f"/api/control/v1/sites/{alpha_id}/domains",
            headers=mutate,
            json={
                "hostname": "temporary.example.test",
                "path_prefix": "/",
                "is_primary": False,
            },
        )
        assert temporary.status_code == 201
        deleted = await client.delete(
            f"/api/control/v1/sites/{alpha_id}/domains/{temporary.json()['domain_id']}",
            headers=mutate,
        )
        assert deleted.status_code == 204
        assert deleted.content == b""
        _assert_private(deleted)
        duplicate_mapping = await client.post(
            f"/api/control/v1/sites/{beta_id}/domains",
            headers=mutate,
            json={
                "hostname": "a.example.test",
                "path_prefix": "/alpha",
                "is_primary": False,
            },
        )
        assert duplicate_mapping.status_code == 409
        domain_list = await client.get(
            f"/api/control/v1/sites/{alpha_id}/domains", headers=read
        )
        assert domain_list.status_code == 200
        assert domain_list.json() == [alpha_domain]

        substituted = await client.put(
            f"/api/control/v1/sites/{alpha_id}/domains/{beta_domain['domain_id']}",
            headers=mutate,
            json={
                "hostname": "stolen.example.test",
                "path_prefix": "/",
                "is_primary": False,
            },
        )
        assert substituted.status_code == 404
        assert substituted.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
        unchanged = await client.get(
            f"/api/control/v1/sites/{beta_id}/domains", headers=read
        )
        assert unchanged.json() == [beta_domain]

        primary_delete = await client.delete(
            f"/api/control/v1/sites/{alpha_id}/domains/{alpha_domain['domain_id']}",
            headers=mutate,
        )
        assert primary_delete.status_code == 409
        duplicate = await client.post(
            "/api/control/v1/sites",
            headers=mutate,
            json={
                "site_key": "ALPHA",
                "display_name": "Duplicate",
                "default_locale": "en",
            },
        )
        assert duplicate.status_code == 409

        archived = await client.post(
            f"/api/control/v1/sites/{alpha_id}/archive", headers=mutate
        )
        assert archived.status_code == 200
        assert archived.json()["status"] == "ARCHIVED"
        assert (
            await client.post(
                f"/api/control/v1/sites/{alpha_id}/archive", headers=mutate
            )
        ).status_code == 200
        assert (
            await client.get(f"/api/control/v1/sites/{alpha_id}", headers=read)
        ).status_code == 200
        archived_mutations = (
            await client.patch(
                f"/api/control/v1/sites/{alpha_id}",
                headers=mutate,
                json={"display_name": "No", "default_locale": "en"},
            ),
            await client.post(
                f"/api/control/v1/sites/{alpha_id}/domains",
                headers=mutate,
                json={
                    "hostname": "new.example.test",
                    "path_prefix": "/",
                    "is_primary": False,
                },
            ),
            await client.put(
                f"/api/control/v1/sites/{alpha_id}/domains/{alpha_domain['domain_id']}",
                headers=mutate,
                json={
                    "hostname": "changed.example.test",
                    "path_prefix": "/",
                    "is_primary": False,
                },
            ),
            await client.delete(
                f"/api/control/v1/sites/{alpha_id}/domains/{alpha_domain['domain_id']}",
                headers=mutate,
            ),
        )
        assert [response.status_code for response in archived_mutations] == [
            409,
            409,
            409,
            409,
        ]
        for response in (
            *archived_mutations,
            substituted,
            primary_delete,
            duplicate,
            duplicate_mapping,
            quota,
        ):
            _assert_private(response)

        forbidden_fields = await client.post(
            "/api/control/v1/sites",
            headers=mutate,
            json={
                "site_key": "forged",
                "display_name": "Forged",
                "default_locale": "en",
                "site_id": str(uuid4()),
                "status": "ACTIVE",
                "canonical_revision": 9,
            },
        )
        assert forbidden_fields.status_code == 422
        _assert_private(forbidden_fields)

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.site WHERE id = $1",
                    UUID(str(alpha["site_id"])),
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.site_domain WHERE id = $1",
                    UUID(str(alpha_domain["domain_id"])),
                )
                == 1
            )
    finally:
        await client.aclose()
        await adapter.stop()


@pytest.mark.asyncio
async def test_site_http_authentication_csrf_administrator_and_failure_contract(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    adapter, client, session, csrf = await _setup(database)
    path = "/api/control/v1/sites"
    payload = {
        "site_key": "denied",
        "display_name": "Denied",
        "default_locale": "en",
    }
    try:
        for headers in (
            {},
            {"cookie": "slaif_session=invalid"},
            [("cookie", _cookie(session)), ("cookie", _cookie(session))],
            {"cookie": f"__Host-slaif_session={session}"},
        ):
            response = await client.get(path, headers=headers)
            assert response.status_code == 401
            _assert_private(response)

        for headers in (
            _get_headers(session),
            {"cookie": _cookie(session, csrf)},
            {
                "cookie": _cookie(session, "sas2_csrf_wrong"),
                "x-csrf-token": "sas2_csrf_wrong",
            },
            [
                ("cookie", _cookie(session, csrf)),
                ("x-csrf-token", csrf),
                ("x-csrf-token", csrf),
            ],
        ):
            response = await client.post(path, headers=headers, json=payload)
            assert response.status_code == 403
            _assert_private(response)

        non_admin_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO control.user_account (id, identity_kind, oidc_issuer, "
                "oidc_subject, display_name) VALUES ($1, 'OIDC', $2, $3, $4)",
                non_admin_id,
                "https://identity.example.test",
                "non-admin",
                "Non Administrator",
            )
            admin_id = await owner.fetchval(
                "SELECT user_account_id FROM control.platform_administrator"
            )
        issued = await adapter.human_session_service().create(non_admin_id)
        non_admin = await client.get(
            path,
            headers={"cookie": _cookie(issued.token.get_secret_value())},
        )
        assert non_admin.status_code == 403
        _assert_private(non_admin)

        valid_for_failure = await adapter.human_session_service().create(admin_id)
        await adapter.human_session_service().revoke(session, csrf)
        revoked = await client.get(path, headers=_get_headers(session))
        assert revoked.status_code == 401
        _assert_private(revoked)

        expiring = await adapter.human_session_service().create(admin_id)
        expiring_token = expiring.token.get_secret_value()
        public_id, _secret = parse_session_token(expiring_token)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET "
                "created_at = current_timestamp - interval '3 seconds', "
                "last_seen_at = current_timestamp - interval '2 seconds', "
                "recent_auth_at = current_timestamp - interval '2 seconds', "
                "absolute_expires_at = current_timestamp - interval '1 second' "
                "WHERE public_id = $1",
                public_id,
            )
        expired = await client.get(path, headers=_get_headers(expiring_token))
        assert expired.status_code == 401
        _assert_private(expired)

        await adapter.stop()
        unavailable = await client.get(
            path,
            headers=_get_headers(valid_for_failure.token.get_secret_value()),
        )
        assert unavailable.status_code == 503
        _assert_private(unavailable)
        combined = unavailable.text + non_admin.text
        for forbidden in (
            session,
            csrf,
            "postgresql://",
            "asyncpg",
            "SELECT ",
            "non-admin",
        ):
            assert forbidden not in combined
    finally:
        await client.aclose()
        await adapter.stop()

"""Actual PostgreSQL-backed Control authentication HTTP flows."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from urllib.parse import quote

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

_PASSWORD = "fixture-control-http-password-123"
_UNDERSCORE_SECRETS = tuple(
    bytes.fromhex(value)
    for value in (
        "fe1e004b2f1cd6bade61f13fc301ff4f8c5aea1b7b19fe9075a0be3b5706655c",
        "22d592a0490f32ff825dd9c615b55dfdf58dcc6da586cfeb791498b3fc1fa94c",
        "d28e93e6f630cf8d2730b21c573e6e3fa1efe8594f2f901553f151cfa7cca7fa",
        "0f6bffa9661cb5dd2f3f7b2929f33061f58a7ba7fdd689530b1a306f8ed8f3ec",
        "ff" * 32,
        "fe1e004b2f1cd6bade61f13fc301ff4f8c5aea1b7b19fe9075a0be3b5706655c",
    )
)


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
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
        application_name="slaif-control-http-test",
    )


def _random_factory() -> tuple[Iterator[bytes], Callable[[int], bytes]]:
    values = iter(_UNDERSCORE_SECRETS)

    def random_bytes(size: int) -> bytes:
        value = next(values)
        assert size == 32
        assert len(value) == size
        return value

    return values, random_bytes


def _cookie_header(session: str, csrf: str | None = None) -> str:
    value = f"slaif_session={session}"
    return value if csrf is None else f"{value}; slaif_csrf={csrf}"


async def _row_state(database: AgentSiteDatabase) -> tuple[int, int, int]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return (
            int(
                await owner.fetchval(
                    "SELECT count(*) FROM control.user_account "
                    "WHERE identity_kind = 'LOCAL' AND status = 'ACTIVE'"
                )
            ),
            int(await owner.fetchval("SELECT count(*) FROM control.user_session")),
            int(
                await owner.fetchval(
                    "SELECT count(*) FROM control.user_session "
                    "WHERE revoked_at IS NOT NULL"
                )
            ),
        )


@pytest.mark.asyncio
async def test_control_auth_actual_setup_login_session_logout_and_denials(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    _values, random_bytes = _random_factory()
    adapter = ControlDatabase(
        _control_settings(database), session_random_bytes=random_bytes
    )
    await adapter.start()
    app = create_app(
        settings=ServiceSettings(mode=EnvironmentMode.TEST), database=adapter
    )
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://control.test"
        ) as client:
            status = await client.get("/api/control/v1/setup/status")
            assert status.status_code == 200
            assert status.json() == {"initialized": False, "setup_available": False}

            issued_setup = await ensure_setup_token(database.settings)
            assert issued_setup.setup_token is not None
            setup_token = issued_setup.setup_token.get_secret_value()
            status = await client.get("/api/control/v1/setup/status")
            assert status.json() == {"initialized": False, "setup_available": True}

            setup_payload = {
                "setup_token": setup_token,
                "username": "Local.Admin",
                "password": _PASSWORD,
                "display_name": "Local Administrator",
                "email": "admin@example.test",
            }
            first, second = await asyncio.gather(
                client.post("/api/control/v1/setup", json=setup_payload),
                client.post("/api/control/v1/setup", json=setup_payload),
            )
            assert sorted((first.status_code, second.status_code)) == [200, 422]
            success = first if first.status_code == 200 else second
            denial = second if first.status_code == 200 else first
            assert setup_token not in str(success.request.url)
            assert setup_token not in success.text
            assert setup_token not in denial.text
            assert await _row_state(database) == (1, 1, 0)
            setup_session = success.cookies["slaif_session"]
            setup_csrf = success.cookies["slaif_csrf"]
            assert "_" in setup_session[len("sas2_session_") + 33 :]
            assert "_" in setup_csrf.removeprefix("sas2_csrf_")

            status = await client.get("/api/control/v1/setup/status")
            assert status.json() == {"initialized": True, "setup_available": False}
            inspected = await client.get(
                "/api/control/v1/session",
                headers={"cookie": _cookie_header(setup_session)},
            )
            assert inspected.status_code == 200
            assert "csrf" not in inspected.text.casefold()
            setup_public_id = inspected.json()["public_id"]

            before = await _row_state(database)
            for username, password in (
                ("local.admin", "wrong-password"),
                ("unknown.user", _PASSWORD),
            ):
                denied = await client.post(
                    "/api/control/v1/login",
                    json={"username": username, "password": password},
                )
                assert denied.status_code == 401
                assert "set-cookie" not in denied.headers
                assert await _row_state(database) == before

            login = await client.post(
                "/api/control/v1/login",
                json={"username": "LOCAL.ADMIN", "password": _PASSWORD},
            )
            assert login.status_code == 200
            login_session = login.cookies["slaif_session"]
            login_csrf = login.cookies["slaif_csrf"]
            assert "_" in login_session[len("sas2_session_") + 33 :]
            assert "_" in login_csrf.removeprefix("sas2_csrf_")
            assert await _row_state(database) == (1, 2, 0)
            login_context = await client.get(
                "/api/control/v1/session",
                headers={"cookie": _cookie_header(login_session)},
            )
            assert login_context.status_code == 200
            login_public_id = login_context.json()["public_id"]

            for headers in (
                [
                    ("cookie", _cookie_header(setup_session, login_csrf)),
                    ("x-csrf-token", login_csrf),
                ],
                [("cookie", _cookie_header(setup_session, setup_csrf))],
                [
                    ("cookie", _cookie_header(setup_session, setup_csrf)),
                    ("x-csrf-token", setup_csrf),
                    ("x-csrf-token", setup_csrf),
                ],
            ):
                denied = await client.post("/api/control/v1/logout", headers=headers)
                assert denied.status_code == 403
                assert "set-cookie" not in denied.headers
                assert await _row_state(database) == (1, 2, 0)

            logout = await client.post(
                "/api/control/v1/logout",
                headers={
                    "cookie": _cookie_header(setup_session, setup_csrf),
                    "x-csrf-token": setup_csrf,
                },
            )
            assert logout.status_code == 204
            assert logout.content == b""
            assert len(logout.headers.get_list("set-cookie")) == 2
            assert await _row_state(database) == (1, 2, 1)
            replay = await client.post(
                "/api/control/v1/logout",
                headers={
                    "cookie": _cookie_header(setup_session, setup_csrf),
                    "x-csrf-token": setup_csrf,
                },
            )
            assert replay.status_code == 204
            assert await _row_state(database) == (1, 2, 1)
            assert (
                await client.get(
                    "/api/control/v1/session",
                    headers={"cookie": _cookie_header(setup_session)},
                )
            ).status_code == 401

            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.user_session SET "
                    "created_at = current_timestamp - interval '3 seconds', "
                    "last_seen_at = current_timestamp - interval '2 seconds', "
                    "recent_auth_at = current_timestamp - interval '2 seconds', "
                    "absolute_expires_at = current_timestamp - interval '1 second' "
                    "WHERE public_id = $1",
                    login_public_id,
                )
            assert (
                await client.get(
                    "/api/control/v1/session",
                    headers={"cookie": _cookie_header(login_session)},
                )
            ).status_code == 401
            expired_logout = await client.post(
                "/api/control/v1/logout",
                headers={
                    "cookie": _cookie_header(login_session, login_csrf),
                    "x-csrf-token": login_csrf,
                },
            )
            assert expired_logout.status_code == 403
            assert "set-cookie" not in expired_logout.headers
            assert await _row_state(database) == (1, 2, 1)

            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                await owner.execute(
                    "UPDATE control.user_account SET status = 'DISABLED' "
                    "WHERE local_username_normalized = 'local.admin'"
                )
            disabled = await client.post(
                "/api/control/v1/login",
                json={"username": "local.admin", "password": _PASSWORD},
            )
            assert disabled.status_code == 401
            assert await _row_state(database) == (0, 2, 1)
            assert setup_public_id != login_public_id
    finally:
        await adapter.stop()

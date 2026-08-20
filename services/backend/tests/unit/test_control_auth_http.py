"""Control authentication HTTP contract tests."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import SecretStr
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.identity.authentication import LocalAuthenticationResult
from slaif_agent_site.identity.models import InitialLocalAdministratorResult
from slaif_agent_site.identity.sessions import (
    HumanSessionContext,
    IssuedHumanSession,
)


class FakeSessions:
    def __init__(self) -> None:
        self.revoked: list[tuple[str, str]] = []
        self.context = HumanSessionContext(
            session_id=uuid4(),
            user_account_id=UUID("11111111-1111-4111-8111-111111111111"),
            public_id="sas2_" + "a" * 32,
            recent_auth=True,
            last_seen_at=datetime.now(UTC),
            absolute_expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    async def create(self, _user_id: UUID) -> IssuedHumanSession:
        now = datetime.now(UTC)
        return IssuedHumanSession(
            session_id=self.context.session_id,
            public_id=self.context.public_id,
            token=SecretStr("t" * 43),
            csrf_token=SecretStr("c" * 43),
            created_at=now,
            last_seen_at=now,
            absolute_expires_at=now + timedelta(hours=1),
            recent_auth_at=now,
        )

    async def authenticate(self, token: str) -> HumanSessionContext:
        if token != "t" * 43:
            from slaif_agent_site.identity.sessions import HumanSessionError

            raise HumanSessionError()
        return self.context

    async def revoke(self, token: str, csrf: str) -> None:
        self.revoked.append((token, csrf))


class FakeDatabase:
    def __init__(self) -> None:
        self.sessions = FakeSessions()

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> Any:
        from slaif_agent_site.health import ProbeResult

        return ProbeResult.ready()

    async def setup_status(self) -> tuple[bool, bool]:
        return False, True

    async def create_initial_local_administrator(
        self, request: Any
    ) -> InitialLocalAdministratorResult:
        return InitialLocalAdministratorResult(
            user_account_id=self.sessions.context.user_account_id,
            username=request.username,
            display_name=request.display_name,
            email=request.email,
            status="ACTIVE",
            created_at=datetime.now(UTC),
        )

    def human_session_service(self) -> FakeSessions:
        return self.sessions

    async def authenticate_local_login(self, request: Any) -> LocalAuthenticationResult:
        return LocalAuthenticationResult(
            user_account_id=self.sessions.context.user_account_id,
            username=request.username,
            rehashed=False,
        )


@pytest.mark.anyio
async def test_control_auth_routes_and_cookie_contract() -> None:
    database = FakeDatabase()
    app = create_app(settings=ServiceSettings.for_test(), database=cast(Any, database))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        status = await client.get("/api/control/v1/setup/status")
        assert status.status_code == 200
        assert status.json() == {"initialized": False, "setup_available": True}
        assert status.headers["cache-control"] == "private, no-store"
        assert status.headers["x-robots-tag"] == "noindex, nofollow, noarchive"

        login = await client.post(
            "/api/control/v1/login",
            json={"username": "Admin", "password": "correct horse"},
        )
        assert login.status_code == 200
        assert "slaif_session=" in login.headers["set-cookie"]
        assert "slaif_csrf=" in login.headers["set-cookie"]
        assert "correct horse" not in login.text
        client.cookies.clear()

        session = await client.get(
            "/api/control/v1/session", cookies={"slaif_session": "t" * 43}
        )
        assert session.status_code == 200
        assert session.json()["public_id"] == database.sessions.context.public_id

        bad_logout = await client.post(
            "/api/control/v1/logout",
            headers={"X-CSRF-Token": "wrong"},
            cookies={"slaif_session": "t" * 43, "slaif_csrf": "c" * 43},
        )
        assert bad_logout.status_code == 401
        logout = await client.post(
            "/api/control/v1/logout",
            headers={"X-CSRF-Token": "c" * 43},
            cookies={"slaif_session": "t" * 43, "slaif_csrf": "c" * 43},
        )
        assert logout.status_code == 200
        assert database.sessions.revoked == [("t" * 43, "c" * 43)]


def test_control_openapi_is_internal_only() -> None:
    app = create_app(
        settings=ServiceSettings.for_test(), database=cast(Any, FakeDatabase())
    )
    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None
    assert "/api/control/v1/login" in app.openapi()["paths"]

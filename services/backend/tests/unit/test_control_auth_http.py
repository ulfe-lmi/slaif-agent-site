"""Strict Control authentication HTTP contracts and secret-safety proofs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

import httpx
import pytest
from pydantic import HttpUrl, SecretStr
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.app import create_app
from slaif_agent_site.control_api.database import InitialSetupError
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.identity.authentication import (
    LocalAuthenticationError,
    LocalAuthenticationResult,
)
from slaif_agent_site.identity.models import InitialLocalAdministratorResult
from slaif_agent_site.identity.sessions import (
    HumanSessionContext,
    HumanSessionError,
    IssuedHumanSession,
    format_csrf_token,
    format_session_token,
)

USER_ID = UUID("11111111-1111-4111-8111-111111111111")
PUBLIC_ID = "sas2_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SESSION_TOKEN = format_session_token(PUBLIC_ID, bytes(range(32))).get_secret_value()
CSRF_TOKEN = format_csrf_token(bytes(range(32, 64))).get_secret_value()
OTHER_PUBLIC_ID = "sas2_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
OTHER_SESSION_TOKEN = format_session_token(
    OTHER_PUBLIC_ID, bytes(range(64, 96))
).get_secret_value()
OTHER_CSRF_TOKEN = format_csrf_token(bytes(range(96, 128))).get_secret_value()
SECURITY_HEADERS = {
    "cache-control": "private, no-store",
    "pragma": "no-cache",
    "x-robots-tag": "noindex, nofollow, noarchive",
}


def _issued(
    *, token: str = SESSION_TOKEN, csrf: str = CSRF_TOKEN
) -> IssuedHumanSession:
    now = datetime.now(UTC)
    return IssuedHumanSession(
        session_id=uuid4(),
        public_id=PUBLIC_ID,
        token=SecretStr(token),
        csrf_token=SecretStr(csrf),
        created_at=now,
        last_seen_at=now,
        absolute_expires_at=now + timedelta(hours=1),
        recent_auth_at=now,
    )


class StrictSessions:
    def __init__(self) -> None:
        self.created: list[UUID] = []
        self.authenticated: list[str] = []
        self.revoke_calls: list[tuple[str, str]] = []
        self.revoked: set[str] = set()
        self.create_error: Exception | None = None
        self.context = HumanSessionContext(
            session_id=uuid4(),
            user_account_id=USER_ID,
            public_id=PUBLIC_ID,
            recent_auth=True,
            last_seen_at=datetime.now(UTC),
            absolute_expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

    async def create(self, user_id: UUID) -> IssuedHumanSession:
        self.created.append(user_id)
        if self.create_error is not None:
            raise self.create_error
        return _issued()

    async def authenticate(self, token: str) -> HumanSessionContext:
        self.authenticated.append(token)
        if token != SESSION_TOKEN or token in self.revoked:
            raise HumanSessionError()
        return self.context

    async def revoke(self, token: str, csrf: str) -> None:
        self.revoke_calls.append((token, csrf))
        valid_pair = (token, csrf) in {
            (SESSION_TOKEN, CSRF_TOKEN),
            (OTHER_SESSION_TOKEN, OTHER_CSRF_TOKEN),
        }
        if not valid_pair:
            raise HumanSessionError()
        self.revoked.add(token)


class StrictDatabase:
    def __init__(self) -> None:
        self.sessions = StrictSessions()
        self.status: tuple[bool, bool] = (False, True)
        self.status_error: Exception | None = None
        self.setup_error: Exception | None = None
        self.login_error: Exception | None = None
        self.setup_requests: list[Any] = []
        self.login_requests: list[Any] = []

    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    async def setup_status(self) -> tuple[bool, bool]:
        if self.status_error is not None:
            raise self.status_error
        return self.status

    async def create_initial_local_administrator(
        self, request: Any
    ) -> InitialLocalAdministratorResult:
        self.setup_requests.append(request)
        if self.setup_error is not None:
            raise self.setup_error
        return InitialLocalAdministratorResult(
            user_account_id=USER_ID,
            username=request.username,
            display_name=request.display_name,
            email=request.email,
            status="ACTIVE",
            created_at=datetime.now(UTC),
        )

    def human_session_service(self) -> StrictSessions:
        return self.sessions

    async def authenticate_local_login(self, request: Any) -> LocalAuthenticationResult:
        self.login_requests.append(request)
        if self.login_error is not None:
            raise self.login_error
        if request.password.get_secret_value() != "correct horse battery staple":
            raise LocalAuthenticationError()
        return LocalAuthenticationResult(
            user_account_id=USER_ID,
            username=request.username,
            rehashed=False,
        )


def _settings(*, production_cookies: bool = False) -> ServiceSettings:
    settings = ServiceSettings.for_test()
    if not production_cookies:
        return settings
    return settings.model_copy(
        update={
            "secure_cookies": True,
            "public_url": HttpUrl("https://testserver"),
        }
    )


def _app(database: StrictDatabase, *, production_cookies: bool = False) -> Any:
    return create_app(
        settings=_settings(production_cookies=production_cookies),
        database=cast(Any, database),
    )


def _assert_secure_headers(response: httpx.Response) -> None:
    assert {
        name: response.headers[name] for name in SECURITY_HEADERS
    } == SECURITY_HEADERS


def _assert_issue_cookies(
    response: httpx.Response, *, production: bool = False
) -> None:
    cookies = response.headers.get_list("set-cookie")
    assert len(cookies) == 2
    session_name = "__Host-slaif_session" if production else "slaif_session"
    csrf_name = "__Host-slaif_csrf" if production else "slaif_csrf"
    session = next(value for value in cookies if value.startswith(f"{session_name}="))
    csrf = next(value for value in cookies if value.startswith(f"{csrf_name}="))
    for value in cookies:
        assert "Path=/" in value
        assert "Domain=" not in value
        assert "SameSite=lax" in value
        assert "Max-Age=3600" in value
        assert ("; Secure" in value) is production
    assert "; HttpOnly" in session
    assert "; HttpOnly" not in csrf
    assert SESSION_TOKEN in session
    assert CSRF_TOKEN in csrf
    assert SESSION_TOKEN not in response.text
    assert CSRF_TOKEN not in response.text


@pytest.mark.anyio
async def test_status_setup_login_and_all_error_responses_are_private() -> None:
    database = StrictDatabase()
    secret = "setup-fixture-secret-never-returned"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app(database), raise_app_exceptions=False),
        base_url="http://testserver",
    ) as client:
        status = await client.get("/api/control/v1/setup/status")
        assert status.json() == {"initialized": False, "setup_available": True}
        _assert_secure_headers(status)

        validation = await client.post(
            "/api/control/v1/setup",
            json={"setup_token": secret, "username": "admin", "password": secret},
        )
        assert validation.status_code == 422
        assert secret not in validation.text
        _assert_secure_headers(validation)

        setup = await client.post(
            "/api/control/v1/setup",
            json={
                "setup_token": secret,
                "username": "admin",
                "password": "correct horse battery staple",
                "display_name": "Administrator",
            },
        )
        assert setup.status_code == 200
        _assert_issue_cookies(setup)
        _assert_secure_headers(setup)
        assert secret not in setup.text
        client.cookies.clear()

        login = await client.post(
            "/api/control/v1/login",
            json={
                "username": "Admin",
                "password": "correct horse battery staple",
            },
        )
        assert login.status_code == 200
        _assert_issue_cookies(login)
        _assert_secure_headers(login)

        database.login_error = LocalAuthenticationError()
        denial = await client.post(
            "/api/control/v1/login",
            json={"username": "admin", "password": "wrong password"},
        )
        assert denial.status_code == 401
        assert denial.headers.get_list("set-cookie") == []
        _assert_secure_headers(denial)

        database.login_error = RuntimeError("driver secret must stay hidden")
        unavailable = await client.post(
            "/api/control/v1/login",
            json={"username": "admin", "password": secret},
        )
        assert unavailable.status_code == 503
        assert secret not in unavailable.text
        assert "driver" not in unavailable.text
        _assert_secure_headers(unavailable)


@pytest.mark.anyio
async def test_setup_denials_and_session_issue_failures_set_no_cookie() -> None:
    database = StrictDatabase()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=_app(database)),
        base_url="http://testserver",
    ) as client:
        body = {
            "setup_token": "setup-fixture-secret",
            "username": "admin",
            "password": "correct horse battery staple",
            "display_name": "Administrator",
        }
        database.setup_error = InitialSetupError()
        denial = await client.post("/api/control/v1/setup", json=body)
        assert denial.status_code == 422
        assert denial.headers.get_list("set-cookie") == []
        _assert_secure_headers(denial)

        database.setup_error = None
        database.sessions.create_error = HumanSessionError()
        unavailable = await client.post("/api/control/v1/setup", json=body)
        assert unavailable.status_code == 503
        assert unavailable.headers.get_list("set-cookie") == []
        _assert_secure_headers(unavailable)


@pytest.mark.anyio
@pytest.mark.parametrize("production", (False, True))
async def test_exact_local_and_production_issue_and_logout_cookies(
    production: bool,
) -> None:
    database = StrictDatabase()
    scheme = "https" if production else "http"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(
            app=_app(database, production_cookies=production)
        ),
        base_url=f"{scheme}://testserver",
    ) as client:
        login = await client.post(
            "/api/control/v1/login",
            json={
                "username": "admin",
                "password": "correct horse battery staple",
            },
        )
        _assert_issue_cookies(login, production=production)
        client.cookies.clear()
        session_name = "__Host-slaif_session" if production else "slaif_session"
        csrf_name = "__Host-slaif_csrf" if production else "slaif_csrf"
        logout = await client.post(
            "/api/control/v1/logout",
            headers=[
                ("Cookie", f"{session_name}={SESSION_TOKEN}; {csrf_name}={CSRF_TOKEN}"),
                ("X-CSRF-Token", CSRF_TOKEN),
            ],
        )
        assert logout.status_code == 204
        assert logout.content == b""
        _assert_secure_headers(logout)
        clears = logout.headers.get_list("set-cookie")
        assert len(clears) == 2
        for name in (session_name, csrf_name):
            clear = next(value for value in clears if value.startswith(f"{name}="))
            assert "Max-Age=0" in clear
            assert "Path=/" in clear
            assert "Domain=" not in clear
            assert ("; Secure" in clear) is production
        assert "; HttpOnly" in next(
            value for value in clears if value.startswith(f"{session_name}=")
        )
        assert "; HttpOnly" not in next(
            value for value in clears if value.startswith(f"{csrf_name}=")
        )


@pytest.mark.anyio
async def test_session_and_logout_reject_credential_ambiguity_before_authority() -> (
    None
):
    database = StrictDatabase()
    app = _app(database)
    session_cases: tuple[list[tuple[str, str]], ...] = (
        [],
        [("Cookie", "slaif_session=")],
        [("Cookie", f"slaif_session={SESSION_TOKEN}; broken")],
        [("Cookie", f"slaif_session={SESSION_TOKEN}; slaif_session={SESSION_TOKEN}")],
        [("Cookie", f"slaif_session={SESSION_TOKEN}"), ("Cookie", "other=value")],
        [("Cookie", f"slaif_session={SESSION_TOKEN}; __Host-slaif_csrf=value")],
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        for headers in session_cases:
            response = await client.get("/api/control/v1/session", headers=headers)
            assert response.status_code == 401
            _assert_secure_headers(response)
        assert database.sessions.authenticated == []

        valid_session = await client.get(
            "/api/control/v1/session",
            headers={"Cookie": f"unrelated=ok; slaif_session={SESSION_TOKEN}"},
        )
        assert valid_session.status_code == 200
        assert set(valid_session.json()) == {
            "user_account_id",
            "public_id",
            "recent_auth",
            "absolute_expires_at",
        }

        base_cookie = f"slaif_session={SESSION_TOKEN}; slaif_csrf={CSRF_TOKEN}"
        csrf_denials: tuple[list[tuple[str, str]], ...] = (
            [("Cookie", base_cookie)],
            [("Cookie", base_cookie), ("X-CSRF-Token", "")],
            [("Cookie", base_cookie), ("X-CSRF-Token", "wrong")],
            [
                ("Cookie", base_cookie),
                ("X-CSRF-Token", CSRF_TOKEN),
                ("X-CSRF-Token", CSRF_TOKEN),
            ],
            [
                (
                    "Cookie",
                    f"slaif_session={SESSION_TOKEN}; slaif_csrf={OTHER_CSRF_TOKEN}",
                ),
                ("X-CSRF-Token", OTHER_CSRF_TOKEN),
            ],
        )
        for headers in csrf_denials:
            response = await client.post("/api/control/v1/logout", headers=headers)
            assert response.status_code == 403
            assert response.headers.get_list("set-cookie") == []
            _assert_secure_headers(response)
        assert database.sessions.revoked == set()

        auth_denials: tuple[list[tuple[str, str]], ...] = (
            [("Cookie", f"slaif_csrf={CSRF_TOKEN}"), ("X-CSRF-Token", CSRF_TOKEN)],
            [
                (
                    "Cookie",
                    f"slaif_session={SESSION_TOKEN}; "
                    f"__Host-slaif_session={SESSION_TOKEN}; "
                    f"slaif_csrf={CSRF_TOKEN}",
                ),
                ("X-CSRF-Token", CSRF_TOKEN),
            ],
            [
                ("Cookie", base_cookie),
                ("Cookie", "unrelated=value"),
                ("X-CSRF-Token", CSRF_TOKEN),
            ],
        )
        for headers in auth_denials:
            response = await client.post("/api/control/v1/logout", headers=headers)
            assert response.status_code == 401
            assert response.headers.get_list("set-cookie") == []
        assert database.sessions.revoke_calls == [(SESSION_TOKEN, OTHER_CSRF_TOKEN)]


@pytest.mark.anyio
async def test_logout_is_externally_idempotent_and_docs_urls_stay_disabled() -> None:
    database = StrictDatabase()
    app = _app(database)
    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None
    assert set(app.openapi()["paths"]) >= {
        "/api/control/v1/setup/status",
        "/api/control/v1/setup",
        "/api/control/v1/login",
        "/api/control/v1/session",
        "/api/control/v1/logout",
    }
    headers = {
        "Cookie": f"slaif_session={SESSION_TOKEN}; slaif_csrf={CSRF_TOKEN}",
        "X-CSRF-Token": CSRF_TOKEN,
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        first = await client.post("/api/control/v1/logout", headers=headers)
        client.cookies.clear()
        replay = await client.post("/api/control/v1/logout", headers=headers)
    assert first.status_code == replay.status_code == 204
    assert database.sessions.revoke_calls == [
        (SESSION_TOKEN, CSRF_TOKEN),
        (SESSION_TOKEN, CSRF_TOKEN),
    ]

"""Typed, secret-safe Control authentication HTTP orchestration."""

from __future__ import annotations

import secrets
from datetime import datetime
from re import compile as compile_pattern
from typing import Any, cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from slaif_agent_site.control_api.database import InitialSetupError
from slaif_agent_site.errors import (
    AuthenticationError,
    AuthorizationError,
    DomainValidationError,
    ServiceUnavailableError,
)
from slaif_agent_site.identity.authentication import (
    LocalAuthenticationError,
    LocalLoginRequest,
)
from slaif_agent_site.identity.models import InitialLocalAdministratorRequest
from slaif_agent_site.identity.sessions import (
    HumanSessionContext,
    HumanSessionError,
    IssuedHumanSession,
)

SETUP_STATUS_SQL = 'SELECT * FROM "control"."slaif_setup_status"()'
_COOKIE_NAME = compile_pattern(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_COOKIE_VALUE = compile_pattern(r"^[\x21\x23-\x2B\x2D-\x3A\x3C-\x5B\x5D-\x7E]*$")
_AUTH_PATHS = {
    "/api/control/v1/setup/status",
    "/api/control/v1/setup",
    "/api/control/v1/login",
    "/api/control/v1/session",
    "/api/control/v1/logout",
}


class SetupStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    initialized: bool
    setup_available: bool


class SetupRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    setup_token: SecretStr = Field(exclude=True, repr=False)
    username: str
    password: SecretStr = Field(exclude=True, repr=False)
    display_name: str
    email: str | None = None


class IdentityResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    user_account_id: str
    username: str


class SessionResponse(BaseModel):
    recent_auth: bool
    absolute_expires_at: datetime
    user_account_id: str
    public_id: str


def _secure_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"


def _private_control_path(path: str) -> bool:
    return (
        path in _AUTH_PATHS
        or path == "/api/control/v1/sites"
        or path.startswith("/api/control/v1/sites/")
    )


class ControlAuthSecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        if _private_control_path(request.url.path):
            _secure_headers(response)
        return response


def _raw_header_values(request: Request, expected_name: bytes) -> list[bytes]:
    headers = cast(list[tuple[bytes, bytes]], request.scope.get("headers", []))
    return [value for name, value in headers if name.lower() == expected_name]


def _cookie_values(request: Request) -> dict[str, str]:
    raw_headers = _raw_header_values(request, b"cookie")
    if len(raw_headers) != 1:
        raise AuthenticationError()
    try:
        raw = raw_headers[0].decode("ascii")
    except UnicodeDecodeError:
        raise AuthenticationError() from None
    if not raw:
        raise AuthenticationError()
    values: dict[str, str] = {}
    for part in raw.split(";"):
        pair = part.strip()
        if not pair or pair.count("=") != 1:
            raise AuthenticationError()
        name, value = pair.split("=", 1)
        if (
            not _COOKIE_NAME.fullmatch(name)
            or not _COOKIE_VALUE.fullmatch(value)
            or name in values
        ):
            raise AuthenticationError()
        values[name] = value
    return values


def _csrf_header(request: Request) -> str:
    raw_headers = _raw_header_values(request, b"x-csrf-token")
    if len(raw_headers) != 1:
        raise AuthorizationError()
    try:
        value = raw_headers[0].decode("ascii")
    except UnicodeDecodeError:
        raise AuthorizationError() from None
    if not value or value != value.strip():
        raise AuthorizationError()
    return value


async def authenticate_human_request(
    request: Request,
    database: Any,
    settings: Any,
    *,
    state_changing: bool,
) -> HumanSessionContext:
    """Apply the strict cookie policy and optional bound CSRF proof."""

    names = _cookie_values(request)
    session_name = (
        "__Host-slaif_session" if settings.secure_cookies else "slaif_session"
    )
    csrf_name = "__Host-slaif_csrf" if settings.secure_cookies else "slaif_csrf"
    alternate_names = (
        {"slaif_session", "slaif_csrf"}
        if settings.secure_cookies
        else {"__Host-slaif_session", "__Host-slaif_csrf"}
    )
    if alternate_names & names.keys():
        raise AuthenticationError()
    token = names.get(session_name)
    if not token:
        raise AuthenticationError()
    try:
        service = database.human_session_service()
    except HumanSessionError:
        raise ServiceUnavailableError() from None
    try:
        context = cast(HumanSessionContext, await service.authenticate(token))
    except HumanSessionError:
        raise AuthenticationError() from None
    if not state_changing:
        return context
    header = _csrf_header(request)
    csrf = names.get(csrf_name)
    if not csrf or not secrets.compare_digest(csrf, header):
        raise AuthorizationError()
    try:
        return cast(
            HumanSessionContext,
            await service.authenticate_state_changing(token, csrf),
        )
    except HumanSessionError:
        raise AuthorizationError() from None


def _set_session_cookies(
    response: Response, issued: IssuedHumanSession, *, production: bool
) -> None:
    session_name = "__Host-slaif_session" if production else "slaif_session"
    csrf_name = "__Host-slaif_csrf" if production else "slaif_csrf"
    max_age = max(
        1, int((issued.absolute_expires_at - issued.created_at).total_seconds())
    )
    response.set_cookie(
        session_name,
        issued.token.get_secret_value(),
        max_age=max_age,
        path="/",
        secure=production,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        csrf_name,
        issued.csrf_token.get_secret_value(),
        max_age=max_age,
        path="/",
        secure=production,
        httponly=False,
        samesite="lax",
    )


def _clear_session_cookies(response: Response, *, production: bool) -> None:
    for name in (
        ("__Host-slaif_session", "__Host-slaif_csrf")
        if production
        else ("slaif_session", "slaif_csrf")
    ):
        response.delete_cookie(
            name,
            path="/",
            secure=production,
            httponly=(name.endswith("session")),
            samesite="lax",
        )


def install_control_auth_routes(app: Any, database: Any, settings: Any) -> None:
    router = APIRouter(prefix="/api/control/v1")
    app.add_middleware(ControlAuthSecurityHeadersMiddleware)

    @router.get("/setup/status", response_model=SetupStatusResponse)
    async def setup_status(response: Response) -> SetupStatusResponse:
        _secure_headers(response)
        try:
            initialized, available = await database.setup_status()
        except Exception:
            raise ServiceUnavailableError() from None
        return SetupStatusResponse(
            initialized=bool(initialized), setup_available=bool(available)
        )

    @router.post("/setup", response_model=IdentityResponse)
    async def setup(request: SetupRequest, response: Response) -> IdentityResponse:
        _secure_headers(response)
        try:
            identity = await database.create_initial_local_administrator(
                InitialLocalAdministratorRequest(
                    username=request.username,
                    password=request.password,
                    display_name=request.display_name,
                    email=request.email,
                    setup_token=request.setup_token,
                )
            )
            issued = await database.human_session_service().create(
                identity.user_account_id
            )
        except InitialSetupError:
            raise DomainValidationError() from None
        except Exception:
            raise ServiceUnavailableError() from None
        _set_session_cookies(response, issued, production=settings.secure_cookies)
        return IdentityResponse(
            user_account_id=str(identity.user_account_id), username=identity.username
        )

    @router.post("/login", response_model=IdentityResponse)
    async def login(request: LocalLoginRequest, response: Response) -> IdentityResponse:
        _secure_headers(response)
        try:
            identity = await database.authenticate_local_login(request)
            issued = await database.human_session_service().create(
                identity.user_account_id
            )
        except LocalAuthenticationError:
            raise AuthenticationError() from None
        except Exception:
            raise ServiceUnavailableError() from None
        _set_session_cookies(response, issued, production=settings.secure_cookies)
        return IdentityResponse(
            user_account_id=str(identity.user_account_id), username=identity.username
        )

    @router.get("/session", response_model=SessionResponse)
    async def session(request: Request, response: Response) -> SessionResponse:
        _secure_headers(response)
        context = await authenticate_human_request(
            request, database, settings, state_changing=False
        )
        return SessionResponse(
            user_account_id=str(context.user_account_id),
            public_id=context.public_id,
            recent_auth=context.recent_auth,
            absolute_expires_at=context.absolute_expires_at,
        )

    @router.post("/logout", response_model=None, status_code=204)
    async def logout(request: Request) -> Response:
        names = _cookie_values(request)
        session_name = (
            "__Host-slaif_session" if settings.secure_cookies else "slaif_session"
        )
        csrf_name = "__Host-slaif_csrf" if settings.secure_cookies else "slaif_csrf"
        alternate_session = (
            "slaif_session" if settings.secure_cookies else "__Host-slaif_session"
        )
        alternate_csrf = (
            "slaif_csrf" if settings.secure_cookies else "__Host-slaif_csrf"
        )
        if alternate_session in names or alternate_csrf in names:
            raise AuthenticationError()
        token, csrf = names.get(session_name), names.get(csrf_name)
        if not token:
            raise AuthenticationError()
        csrf_header = _csrf_header(request)
        if not csrf or not secrets.compare_digest(csrf, csrf_header):
            raise AuthorizationError()
        try:
            await database.human_session_service().revoke(token, csrf)
        except HumanSessionError:
            raise AuthorizationError() from None
        response = Response(status_code=204)
        _clear_session_cookies(response, production=settings.secure_cookies)
        return response

    app.include_router(router)


__all__ = [
    "ControlAuthSecurityHeadersMiddleware",
    "authenticate_human_request",
    "install_control_auth_routes",
]

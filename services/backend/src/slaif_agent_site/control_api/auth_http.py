"""Typed, secret-safe Control authentication HTTP orchestration."""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from slaif_agent_site.control_api.database import InitialSetupError
from slaif_agent_site.errors import (
    AuthenticationError,
    DomainValidationError,
    ServiceUnavailableError,
)
from slaif_agent_site.identity.authentication import (
    LocalAuthenticationError,
    LocalLoginRequest,
)
from slaif_agent_site.identity.models import InitialLocalAdministratorRequest
from slaif_agent_site.identity.sessions import HumanSessionError, IssuedHumanSession

SETUP_STATUS_SQL = 'SELECT * FROM "control"."slaif_setup_status"()'


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


def _cookie_values(request: Request) -> dict[str, str]:
    raw = request.headers.get("cookie", "")
    values: dict[str, str] = {}
    for part in raw.split(";"):
        if not part.strip() or "=" not in part:
            continue
        name, value = part.strip().split("=", 1)
        if name in values:
            raise AuthenticationError()
        values[name] = value
    return values


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
        names = _cookie_values(request)
        name = "__Host-slaif_session" if settings.secure_cookies else "slaif_session"
        alternate = (
            "slaif_session" if settings.secure_cookies else "__Host-slaif_session"
        )
        if alternate in names:
            raise AuthenticationError()
        token = names.get(name)
        if token is None:
            raise AuthenticationError()
        try:
            context = await database.human_session_service().authenticate(token)
        except HumanSessionError:
            raise AuthenticationError() from None
        return SessionResponse(
            user_account_id=str(context.user_account_id),
            public_id=context.public_id,
            recent_auth=context.recent_auth,
            absolute_expires_at=context.absolute_expires_at,
        )

    @router.post("/logout", response_model=None)
    async def logout(
        request: Request,
        response: Response,
        x_csrf_token: str | None = Header(default=None),
    ) -> None:
        _secure_headers(response)
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
        if (
            token is None
            or csrf is None
            or x_csrf_token is None
            or not secrets.compare_digest(csrf, x_csrf_token)
        ):
            raise AuthenticationError()
        try:
            await database.human_session_service().revoke(token, csrf)
        except HumanSessionError:
            raise AuthenticationError() from None
        _clear_session_cookies(response, production=settings.secure_cookies)

    app.include_router(router)

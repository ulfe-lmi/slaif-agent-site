"""Private Render site-context resolution endpoint."""

from __future__ import annotations

import secrets
from typing import Any, Never
from uuid import UUID

from fastapi import APIRouter, FastAPI, Request, Response
from pydantic import BaseModel, ConfigDict, SecretStr
from starlette.responses import JSONResponse

from slaif_agent_site.browser_preview_credentials import BROWSER_RENDER_HEADER
from slaif_agent_site.errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.sites.resolver import SiteResolverError, SiteResolverReason

from .projection import (
    ProjectionError,
    RenderPageProjection,
    RenderPageRequest,
    RenderPreviewRequest,
    RenderProjectionService,
)


class RenderSiteContextRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    authority: str
    path: str


class RenderSiteContextResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    site_id: UUID
    site_key: str
    canonical_revision: int
    default_locale: str
    matched_hostname: str
    matched_path_prefix: str


def _headers(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"


def install_render_site_route(app: FastAPI, database: Any) -> None:
    router = APIRouter()

    @router.post(
        "/internal/render/v1/site-context", response_model=RenderSiteContextResponse
    )
    async def resolve_site(
        payload: RenderSiteContextRequest, response: Response
    ) -> RenderSiteContextResponse:
        _headers(response)
        try:
            context = await database.resolver().resolve(payload.authority, payload.path)
        except SiteResolverError as error:
            if error.reason == SiteResolverReason.CONFLICT:
                raise ResourceConflictError() from None
            if error.reason == SiteResolverReason.NOT_FOUND:
                raise ResourceNotFoundError() from None
            raise ServiceUnavailableError() from None
        except Exception:
            raise ServiceUnavailableError() from None
        return RenderSiteContextResponse(
            site_id=context.site_id,
            site_key=context.site_key,
            canonical_revision=context.canonical_revision,
            default_locale=context.default_locale,
            matched_hostname=context.matched_hostname or "",
            matched_path_prefix=context.matched_path_prefix or "",
        )

    app.include_router(router)


def _projection_error(error: ProjectionError) -> Never:
    if error.reason == "not_found":
        raise ResourceNotFoundError() from None
    if error.reason == "unavailable":
        raise ServiceUnavailableError() from None
    raise ResourceNotFoundError() from None


def install_render_projection_routes(
    app: FastAPI, database: Any, *, browser_verifier: Any = None
) -> None:
    router = APIRouter(prefix="/internal/render/v1")
    service = RenderProjectionService(database, browser_verifier=browser_verifier)

    @router.post("/page", response_model=RenderPageProjection)
    async def canonical_page(
        payload: RenderPageRequest, response: Response
    ) -> RenderPageProjection:
        _headers(response)
        try:
            return await service.canonical(payload)
        except ProjectionError as error:
            _projection_error(error)

    @router.post("/preview", response_model=RenderPageProjection)
    async def preview_page(
        payload: RenderPreviewRequest,
        response: Response,
        request: Request,
    ) -> RenderPageProjection:
        _headers(response)
        headers = request.scope.get("headers", [])
        human_values = [
            value for name, value in headers if name.lower() == b"x-slaif-human-session"
        ]
        browser_header = BROWSER_RENDER_HEADER.casefold().encode("ascii")
        browser_values = [
            value for name, value in headers if name.lower() == browser_header
        ]
        if (
            len(human_values) > 1
            or len(browser_values) > 1
            or bool(human_values and browser_values)
        ):
            raise ResourceNotFoundError()
        selected = payload
        try:
            if human_values:
                selected = payload.model_copy(
                    update={"session_token": SecretStr(human_values[0].decode("ascii"))}
                )
            elif browser_values:
                token = browser_values[0].decode("ascii")
                if (
                    not token
                    or len(token) > 4096
                    or any(character.isspace() for character in token)
                ):
                    raise ValueError
                selected = payload.model_copy(
                    update={"browser_token": SecretStr(token)}
                )
        except (UnicodeError, ValueError):
            raise ResourceNotFoundError() from None
        try:
            return await service.preview(selected)
        except ProjectionError as error:
            _projection_error(error)

    app.include_router(router)


class RenderServiceAuthenticationMiddleware:
    """Authenticate Web-to-Render calls before any projection body is used."""

    def __init__(
        self,
        app: Any,
        *,
        allow_test: bool = False,
        service_token: bytes | None = None,
    ) -> None:
        self.app = app
        self.allow_test = allow_test
        self.service_token = service_token

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        path = scope.get("path", "")
        if scope.get("type") != "http" or not path.startswith("/internal/render/v1/"):
            await self.app(scope, receive, send)
            return
        if self.allow_test:
            await self.app(scope, receive, send)
            return
        headers = scope.get("headers", [])
        values = [
            value for name, value in headers if name.lower() == b"x-slaif-render-token"
        ]
        expected = self.service_token
        candidate = values[0] if len(values) == 1 else None
        well_formed = False
        if candidate is not None:
            try:
                decoded = candidate.decode("ascii")
            except UnicodeDecodeError:
                decoded = ""
            well_formed = bool(decoded) and not any(
                character.isspace() for character in decoded
            )
        if (
            expected is None
            or candidate is None
            or not well_formed
            or not secrets.compare_digest(candidate, expected)
        ):
            response = JSONResponse({"error": "authentication_error"}, status_code=401)
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)


class RenderPrivateHeadersMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        async def secured(message: Any) -> None:
            if message["type"] == "http.response.start" and scope.get(
                "path", ""
            ).startswith("/internal/render/v1/"):
                protected = {b"cache-control", b"pragma", b"x-robots-tag"}
                headers = [
                    item
                    for item in message.get("headers", [])
                    if item[0].lower() not in protected
                ]
                headers.extend(
                    [
                        (b"cache-control", b"private, no-store"),
                        (b"pragma", b"no-cache"),
                        (b"x-robots-tag", b"noindex, nofollow, noarchive"),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, secured)

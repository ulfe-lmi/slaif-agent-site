"""Private Render site-context resolution endpoint."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, FastAPI, Response
from pydantic import BaseModel, ConfigDict

from slaif_agent_site.errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.sites.resolver import SiteResolverError, SiteResolverReason


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


class RenderPrivateHeadersMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        async def secured(message: Any) -> None:
            if (
                message["type"] == "http.response.start"
                and scope.get("path") == "/internal/render/v1/site-context"
            ):
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

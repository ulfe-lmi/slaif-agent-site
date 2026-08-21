"""Least-privilege Render configuration and endpoint contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.render_api import create_app
from slaif_agent_site.render_api.config import (
    RENDER_APPLICATION_NAME,
    RENDER_DSN_FILE,
    RENDER_LOGIN,
    RENDER_PRIVILEGE_ROLE,
    RenderDatabaseConfigurationError,
    RenderDatabaseMode,
    RenderDatabaseSettings,
)
from slaif_agent_site.render_api.database import RenderDatabase
from slaif_agent_site.sites.models import SiteContext
from slaif_agent_site.sites.resolver import SiteResolverError, SiteResolverReason


class _Resolver:
    def __init__(self) -> None:
        self.error: str | None = None
        self.calls: list[tuple[str, str]] = []

    async def resolve(self, authority: str, path: str) -> SiteContext:
        self.calls.append((authority, path))
        if self.error:
            raise SiteResolverError(self.error)
        return SiteContext._from_database(
            (
                UUID("11111111-1111-4111-8111-111111111111"),
                "docs",
                "ACTIVE",
                7,
                "en",
                "example.test",
                "/docs",
            )
        )


class _Database:
    def __init__(self) -> None:
        self.site_resolver = _Resolver()

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    def resolver(self) -> _Resolver:
        return self.site_resolver


class _IdentityConnection:
    def __init__(self, row: tuple[Any, ...]) -> None:
        self.row = row

    async def fetchrow(self, *_args: Any) -> tuple[Any, ...]:
        return self.row


class _ClosedPool:
    def __init__(self) -> None:
        self.closed = 0
        self.terminated = 0

    async def close(self) -> None:
        self.closed += 1

    def terminate(self) -> None:
        self.terminated += 1


def test_fixed_render_identity_and_test_locator_boundary() -> None:
    settings = RenderDatabaseSettings(
        mode=RenderDatabaseMode.TEST,
        dsn=SecretStr(
            "postgresql://slaif_public_login:fake@127.0.0.1/slaif?sslmode=disable"
        ),
    )
    assert settings.expected_login == RENDER_LOGIN
    assert settings.expected_privilege_role == RENDER_PRIVILEGE_ROLE
    assert settings.application_name == RENDER_APPLICATION_NAME
    assert RENDER_DSN_FILE == Path("/run/slaif-render/render-dsn")
    assert "fake" not in repr(settings)

    with pytest.raises(RenderDatabaseConfigurationError):
        RenderDatabaseSettings(
            mode=RenderDatabaseMode.TEST,
            dsn=SecretStr(
                "postgresql://slaif_public_login:secret@external.example/slaif"
            ),
        ).resolved_dsn()
    with pytest.raises(ValidationError):
        RenderDatabaseSettings(
            mode=RenderDatabaseMode.PRODUCTION,
            dsn_file=Path("relative"),
        )


@pytest.mark.asyncio
async def test_render_database_fails_closed_and_shutdown_is_owned() -> None:
    settings = RenderDatabaseSettings(
        mode=RenderDatabaseMode.TEST,
        dsn=SecretStr(
            "postgresql://slaif_public_login:fake@127.0.0.1/slaif?sslmode=disable"
        ),
    )

    async def unavailable_pool(**_kwargs: Any) -> Any:
        raise TimeoutError

    database = RenderDatabase(settings, pool_factory=unavailable_pool)
    await database.start()
    readiness = await database.readiness()
    assert readiness.reason == "timeout"

    with pytest.raises(RuntimeError, match="identity_mismatch"):
        await database._initialize(  # noqa: SLF001 - exact adapter boundary proof
            _IdentityConnection(
                ("wrong", RENDER_LOGIN, RENDER_LOGIN, (RENDER_PRIVILEGE_ROLE,))
            )
        )
    with pytest.raises(RuntimeError, match="role_mismatch"):
        await database._initialize(  # noqa: SLF001 - exact adapter boundary proof
            _IdentityConnection(
                ("slaif", RENDER_LOGIN, RENDER_LOGIN, ("slaif_control",))
            )
        )

    pool = _ClosedPool()
    database._pool = pool  # noqa: SLF001 - owned shutdown proof
    await database.stop()
    assert pool.closed == 1
    assert pool.terminated == 0
    assert (await database.readiness()).reason == "shutdown"


@pytest.mark.asyncio
async def test_render_exposes_one_private_resolution_route_and_safe_failures() -> None:
    database = _Database()
    app = create_app(settings=ServiceSettings.for_test(), database=database)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://render.test"
        ) as client:
            response = await client.post(
                "/internal/render/v1/site-context",
                json={"authority": "EXAMPLE.test:443", "path": "/docs/page"},
                headers={"x-site-id": "forged", "x-workspace-id": "forged"},
            )
            assert response.status_code == 200
            assert response.json() == {
                "site_id": "11111111-1111-4111-8111-111111111111",
                "site_key": "docs",
                "canonical_revision": 7,
                "default_locale": "en",
                "matched_hostname": "example.test",
                "matched_path_prefix": "/docs",
            }
            assert database.site_resolver.calls == [("EXAMPLE.test:443", "/docs/page")]
            assert response.headers["cache-control"] == "private, no-store"
            assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
            assert response.headers["x-request-id"]

            assert (
                await client.post(
                    "/internal/render/v1/site-context",
                    json={"authority": "x.test", "path": "/", "site_id": "x"},
                )
            ).status_code == 422
            for reason, status in (
                (SiteResolverReason.NOT_FOUND, 404),
                (SiteResolverReason.CONFLICT, 409),
                (SiteResolverReason.UNAVAILABLE, 503),
            ):
                database.site_resolver.error = reason
                denied = await client.post(
                    "/internal/render/v1/site-context",
                    json={"authority": "x.test", "path": "/"},
                )
                assert denied.status_code == status
                assert denied.headers["cache-control"] == "private, no-store"
                assert "secret" not in denied.text

"""Least-privilege Render configuration and endpoint contracts."""

from __future__ import annotations

import os
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
from slaif_agent_site.render_api.site_http import RenderServiceAuthenticationMiddleware
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


def test_render_service_credential_file_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "auth"
    directory.mkdir()
    directory.chmod(0o700)
    token_file = directory / "render-token"
    token_file.write_text("t" * 43, encoding="ascii")
    token_file.chmod(0o400)
    settings = RenderDatabaseSettings(
        mode=RenderDatabaseMode.TEST,
        dsn=SecretStr(
            "postgresql://slaif_public_login:fake@127.0.0.1/slaif?sslmode=disable"
        ),
        service_token_file=token_file,
    )
    assert settings.resolved_service_token() == SecretStr("t" * 43)

    token_file.chmod(0o600)
    with pytest.raises(RenderDatabaseConfigurationError):
        settings.resolved_service_token()
    token_file.chmod(0o400)
    directory.chmod(0o755)
    with pytest.raises(RenderDatabaseConfigurationError):
        settings.resolved_service_token()
    directory.chmod(0o700)
    real_euid = os.geteuid()
    monkeypatch.setattr(os, "geteuid", lambda: real_euid + 1)
    with pytest.raises(RenderDatabaseConfigurationError):
        settings.resolved_service_token()
    monkeypatch.setattr(os, "geteuid", lambda: real_euid)
    token_file.unlink()
    token_file.symlink_to(directory / "missing")
    with pytest.raises(RenderDatabaseConfigurationError):
        settings.resolved_service_token()


@pytest.mark.asyncio
async def test_render_service_auth_rejects_invalid_tokens() -> None:
    from starlette.responses import JSONResponse

    async def endpoint(scope: Any, receive: Any, send: Any) -> None:
        await JSONResponse({"ok": True})(scope, receive, send)

    app = RenderServiceAuthenticationMiddleware(endpoint, service_token=b"t" * 43)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://render.test"
    ) as client:
        cases: tuple[tuple[list[tuple[str, str]], int], ...] = (
            ([], 401),
            ([("x-slaif-render-token", "")], 401),
            ([("x-slaif-render-token", "wrong")], 401),
            (
                [
                    ("x-slaif-render-token", "t" * 43),
                    ("x-slaif-render-token", "t" * 43),
                ],
                401,
            ),
            ([("x-slaif-render-token", "t" * 43)], 200),
        )
        for headers, expected in cases:
            response = await client.post(
                "/internal/render/v1/page", headers=headers, content=b"{}"
            )
            assert response.status_code == expected

    unconfigured = RenderServiceAuthenticationMiddleware(endpoint)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=unconfigured), base_url="http://render.test"
    ) as client:
        response = await client.post(
            "/internal/render/v1/page",
            headers={"x-slaif-render-token": ""},
            content=b"{}",
        )
        assert response.status_code == 401


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

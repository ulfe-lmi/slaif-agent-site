"""Render-owned least-privilege asyncpg pool."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any

import asyncpg

from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.sites.resolver import SiteResolver

from .config import (
    RENDER_PREVIEW_LOGIN,
    RENDER_PREVIEW_PRIVILEGE_ROLE,
    RenderDatabaseConfigurationError,
    RenderDatabaseMode,
    RenderDatabaseSettings,
)

READINESS_SQL = "SELECT * FROM control.slaif_site_resolve($1, $2)"
IDENTITY_SQL = (
    "SELECT current_database()::text, session_user::text, current_user::text, "
    "ARRAY(SELECT target.rolname::text FROM pg_catalog.pg_roles target "
    "WHERE target.rolname = ANY($1::text[]) AND "
    "pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
    "ORDER BY target.rolname)"
)


class RenderDatabase:
    def __init__(
        self,
        settings: RenderDatabaseSettings,
        *,
        pool_factory: Any = asyncpg.create_pool,
    ) -> None:
        self._settings = settings
        self._pool_factory = pool_factory
        self._pool: Any = None
        self._preview_pool: Any = None
        self._reason = "connection_unavailable"

    async def _initialize_identity(
        self, connection: Any, *, expected_login: str, expected_role: str
    ) -> None:
        row = await connection.fetchrow(
            IDENTITY_SQL,
            list(ROLE_NAMES),
        )
        if row is None or tuple(row[:3]) != (
            self._settings.expected_database,
            expected_login,
            expected_login,
        ):
            raise RuntimeError("identity_mismatch")
        if tuple(row[3]) != (expected_role,):
            raise RuntimeError("role_mismatch")

    async def _initialize(self, connection: Any) -> None:
        await self._initialize_identity(
            connection,
            expected_login=self._settings.expected_login,
            expected_role=self._settings.expected_privilege_role,
        )

    async def _initialize_preview(self, connection: Any) -> None:
        await self._initialize_identity(
            connection,
            expected_login=RENDER_PREVIEW_LOGIN,
            expected_role=RENDER_PREVIEW_PRIVILEGE_ROLE,
        )

    async def _create_pool(self, dsn: Any, *, init: Any) -> Any:
        return await self._pool_factory(
            dsn=dsn.get_secret_value(),
            min_size=self._settings.pool_min_size,
            max_size=self._settings.pool_max_size,
            timeout=self._settings.connect_timeout_seconds,
            command_timeout=self._settings.command_timeout_seconds,
            max_inactive_connection_lifetime=self._settings.max_inactive_connection_lifetime_seconds,
            server_settings=self._settings.server_settings,
            init=init,
        )

    async def start(self) -> None:
        if self._pool is not None:
            return
        try:
            dsn = self._settings.resolved_dsn()
            self._pool = await self._create_pool(dsn, init=self._initialize)
            if self._settings.mode is not RenderDatabaseMode.TEST:
                preview_dsn = self._settings.resolved_preview_dsn()
                self._preview_pool = await self._create_pool(
                    preview_dsn, init=self._initialize_preview
                )
        except asyncio.CancelledError:
            raise
        except RenderDatabaseConfigurationError:
            self._reason = "configuration_invalid"
        except TimeoutError:
            self._reason = "timeout"
        except Exception as error:
            self._reason = (
                str(error)
                if str(error) in {"identity_mismatch", "role_mismatch"}
                else "connection_unavailable"
            )

    async def stop(self) -> None:
        pool, self._pool = self._pool, None
        preview_pool, self._preview_pool = self._preview_pool, None
        self._reason = "shutdown"
        for selected_pool in (pool, preview_pool):
            if selected_pool is None:
                continue
            task = asyncio.create_task(selected_pool.close())
            try:
                await asyncio.wait_for(
                    asyncio.shield(task), self._settings.shutdown_timeout_seconds
                )
            except asyncio.CancelledError:
                try:
                    await asyncio.wait_for(
                        asyncio.shield(task), self._settings.shutdown_timeout_seconds
                    )
                except TimeoutError:
                    selected_pool.terminate()
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
                raise
            except TimeoutError:
                selected_pool.terminate()
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    async def readiness(self) -> ProbeResult:
        if self._pool is None:
            return ProbeResult.unavailable(self._reason)
        try:
            async with self._pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                await connection.fetch(READINESS_SQL, "readiness.invalid", "/")
            return ProbeResult.ready()
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            return ProbeResult.unavailable("timeout")
        except (asyncpg.UndefinedFunctionError, asyncpg.InsufficientPrivilegeError):
            return ProbeResult.unavailable("migration_mismatch")
        except Exception:
            return ProbeResult.unavailable("connection_unavailable")

    def resolver(self) -> SiteResolver:
        if self._pool is None:
            raise RuntimeError("database unavailable")
        return SiteResolver(
            self._pool, acquire_timeout=self._settings.acquire_timeout_seconds
        )

    @property
    def acquire_timeout(self) -> float:
        return self._settings.acquire_timeout_seconds

    def public_pool(self) -> Any:
        if self._pool is None:
            raise RuntimeError("database unavailable")
        return self._pool

    @property
    def preview_policy(self) -> tuple[int, int, int]:
        return (
            self._settings.preview_idle_timeout_seconds,
            self._settings.preview_touch_interval_seconds,
            self._settings.preview_recent_auth_seconds,
        )

    def preview_pool(self) -> Any:
        if self._preview_pool is None:
            raise RuntimeError("preview database unavailable")
        return self._preview_pool

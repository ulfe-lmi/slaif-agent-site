"""Render-owned least-privilege asyncpg pool."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Any

import asyncpg

from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.sites.resolver import SiteResolver

from .config import RenderDatabaseConfigurationError, RenderDatabaseSettings

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
        self._reason = "connection_unavailable"

    async def _initialize(self, connection: Any) -> None:
        row = await connection.fetchrow(
            IDENTITY_SQL,
            list(ROLE_NAMES),
        )
        if row is None or tuple(row[:3]) != (
            self._settings.expected_database,
            self._settings.expected_login,
            self._settings.expected_login,
        ):
            raise RuntimeError("identity_mismatch")
        if tuple(row[3]) != (self._settings.expected_privilege_role,):
            raise RuntimeError("role_mismatch")

    async def start(self) -> None:
        if self._pool is not None:
            return
        try:
            dsn = self._settings.resolved_dsn()
            self._pool = await self._pool_factory(
                dsn=dsn.get_secret_value(),
                min_size=self._settings.pool_min_size,
                max_size=self._settings.pool_max_size,
                timeout=self._settings.connect_timeout_seconds,
                command_timeout=self._settings.command_timeout_seconds,
                max_inactive_connection_lifetime=self._settings.max_inactive_connection_lifetime_seconds,
                server_settings=self._settings.server_settings,
                init=self._initialize,
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
        self._reason = "shutdown"
        if pool is not None:
            task = asyncio.create_task(pool.close())
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
                    pool.terminate()
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
                raise
            except TimeoutError:
                pool.terminate()
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

"""Editor-owned least-privilege asyncpg pool for semantic content calls."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from typing import Any
from uuid import UUID, uuid4

import asyncpg

from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.content_model.service import ContentModelService
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.health import ProbeResult

from .config import EditorDatabaseConfigurationError, EditorDatabaseSettings

IDENTITY_SQL = (
    "SELECT current_database()::text, session_user::text, current_user::text, "
    "ARRAY(SELECT target.rolname::text FROM pg_catalog.pg_roles target "
    "WHERE target.rolname = ANY($1::text[]) AND "
    "pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
    "ORDER BY target.rolname)"
)
READINESS_SQL = "SELECT * FROM content.slaif_page_list($1)"


class _UnstartedPool:
    def acquire(self, *, timeout: float) -> Any:
        del timeout
        raise TimeoutError()


class EditorDatabase:
    """Own exactly one Editor runtime pool for one application lifespan."""

    def __init__(
        self,
        settings: EditorDatabaseSettings,
        *,
        pool_factory: Any = asyncpg.create_pool,
    ) -> None:
        self._settings = settings
        self._pool_factory = pool_factory
        self._pool: Any = None
        self._reason = "connection_unavailable"

    async def _initialize(self, connection: Any) -> None:
        row = await connection.fetchrow(IDENTITY_SQL, list(ROLE_NAMES))
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
                max_inactive_connection_lifetime=(
                    self._settings.max_inactive_connection_lifetime_seconds
                ),
                server_settings=self._settings.server_settings,
                init=self._initialize,
            )
        except asyncio.CancelledError:
            raise
        except EditorDatabaseConfigurationError:
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
        if pool is None:
            return
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
                await connection.fetch(
                    READINESS_SQL, "00000000-0000-0000-0000-000000000000"
                )
            return ProbeResult.ready()
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            return ProbeResult.unavailable("timeout")
        except (asyncpg.UndefinedFunctionError, asyncpg.InsufficientPrivilegeError):
            return ProbeResult.unavailable("migration_mismatch")
        except Exception:
            return ProbeResult.unavailable("connection_unavailable")

    def content_model_service(self) -> ContentModelService:
        return ContentModelService(
            self._pool or _UnstartedPool(),
            acquire_timeout=self._settings.acquire_timeout_seconds,
        )

    @asynccontextmanager
    async def request_content_service(self, session_id: UUID) -> Any:
        if self._pool is None:
            raise RuntimeError("editor database unavailable")
        async with asyncpg_cow_session(
            self._pool,
            session_id=session_id,
            operation_id=uuid4(),
        ) as cow:
            yield ContentModelService.for_cow_session(
                cow, acquire_timeout=self._settings.acquire_timeout_seconds
            )


__all__ = ["EditorDatabase"]

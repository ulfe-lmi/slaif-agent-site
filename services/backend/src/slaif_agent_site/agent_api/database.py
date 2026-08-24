"""Agent-owned least-privilege pool and semantic database adapter."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from enum import StrEnum
from typing import Any, Protocol

import asyncpg

from slaif_agent_site.agent_state.capability_auth import (
    CapabilityAuthenticationUnavailableError,
    authenticate_capability,
)
from slaif_agent_site.health import ProbeResult

from .config import AgentDatabaseConfigurationError, AgentDatabaseSettings
from .models import AgentCapabilityContext

IDENTITY_SQL = (
    "SELECT current_database()::text, session_user::text, current_user::text, "
    "ARRAY(SELECT target.rolname::text FROM pg_catalog.pg_roles target "
    "WHERE target.rolname = ANY($1::text[]) AND "
    "pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
    "ORDER BY target.rolname)"
)


class AgentDatabaseReason(StrEnum):
    CONNECTION_UNAVAILABLE = "connection_unavailable"
    CONFIGURATION_INVALID = "configuration_invalid"
    IDENTITY_MISMATCH = "identity_mismatch"
    ROLE_MISMATCH = "role_mismatch"
    SHUTDOWN = "shutdown"
    TIMEOUT = "timeout"


class AgentDatabaseError(RuntimeError):
    """A stable failure with no driver, locator, or role detail."""

    def __init__(self, reason: AgentDatabaseReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


class AgentDatabaseAdapter(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> ProbeResult: ...

    def cow_pool(self) -> Any: ...

    async def authenticate_agent_capability(self, auth_header: str) -> Any: ...


PoolFactory = Any


class AgentDatabase:
    """Own exactly one Agent runtime pool for exactly one app lifespan."""

    def __init__(
        self,
        pool: _Pool | None = None,
        *,
        settings: AgentDatabaseSettings | None = None,
        pool_factory: PoolFactory = asyncpg.create_pool,
    ) -> None:
        self._settings = settings
        self._pool_factory = pool_factory
        self._pool: Any = pool
        self._owns_pool = pool is None
        self._reason = AgentDatabaseReason.CONNECTION_UNAVAILABLE

    async def _initialize(self, connection: Any) -> None:
        assert self._settings is not None
        row = await connection.fetchrow(
            IDENTITY_SQL, [self._settings.expected_privilege_role]
        )
        if row is None or tuple(row[:3]) != (
            self._settings.expected_database,
            self._settings.expected_login,
            self._settings.expected_login,
        ):
            raise AgentDatabaseError(AgentDatabaseReason.IDENTITY_MISMATCH)
        if tuple(row[3]) != (self._settings.expected_privilege_role,):
            raise AgentDatabaseError(AgentDatabaseReason.ROLE_MISMATCH)

    async def start(self) -> None:
        if self._pool is not None or self._settings is None:
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
            self._owns_pool = True
            self._reason = AgentDatabaseReason.CONNECTION_UNAVAILABLE
        except asyncio.CancelledError:
            raise
        except AgentDatabaseConfigurationError:
            self._reason = AgentDatabaseReason.CONFIGURATION_INVALID
        except AgentDatabaseError as error:
            self._reason = error.reason
        except TimeoutError:
            self._reason = AgentDatabaseReason.TIMEOUT
        except Exception:
            self._reason = AgentDatabaseReason.CONNECTION_UNAVAILABLE

    async def stop(self) -> None:
        pool, self._pool = self._pool, None
        self._reason = AgentDatabaseReason.SHUTDOWN
        if pool is None or not self._owns_pool:
            return
        task = asyncio.create_task(pool.close())
        try:
            await asyncio.wait_for(
                asyncio.shield(task),
                self._settings.shutdown_timeout_seconds,  # type: ignore[union-attr]
            )
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(
                    asyncio.shield(task),
                    self._settings.shutdown_timeout_seconds,  # type: ignore[union-attr]
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
            return ProbeResult.unavailable(self._reason.value)
        try:
            async with self._pool.acquire(
                timeout=self._settings.acquire_timeout_seconds  # type: ignore[union-attr]
            ) as connection:
                await connection.fetchval("SELECT 1")
            return ProbeResult.ready()
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            return ProbeResult.unavailable(AgentDatabaseReason.TIMEOUT.value)
        except Exception:
            return ProbeResult.unavailable(
                AgentDatabaseReason.CONNECTION_UNAVAILABLE.value
            )

    def cow_pool(self) -> Any:
        """Return the already-owned Agent pool for one COW session."""

        if self._pool is None:
            raise AgentDatabaseError(AgentDatabaseReason.CONNECTION_UNAVAILABLE)
        return self._pool

    async def authenticate_agent_capability(
        self, auth_header: str
    ) -> AgentCapabilityContext | None:
        pool = self._pool
        if pool is None or self._settings is None:
            raise AgentDatabaseError(AgentDatabaseReason.CONNECTION_UNAVAILABLE)
        try:
            record = await authenticate_capability(
                pool,
                acquire_timeout=self._settings.acquire_timeout_seconds,
                auth_header=auth_header,
            )
        except CapabilityAuthenticationUnavailableError:
            raise AgentDatabaseError(
                AgentDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None
        if record is None:
            return None
        return AgentCapabilityContext(
            capability_id=record.capability_id,
            site_id=record.site_id,
            workspace_id=record.workspace_id,
            delegator_id=record.delegator_id,
            scopes=record.scopes,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )


__all__ = [
    "AgentDatabase",
    "AgentDatabaseAdapter",
    "AgentDatabaseError",
    "AgentDatabaseReason",
]

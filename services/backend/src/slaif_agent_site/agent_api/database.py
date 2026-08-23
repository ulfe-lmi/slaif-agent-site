"""Agent-owned bounded database adapter."""

from __future__ import annotations

from typing import Any, Protocol

from slaif_agent_site.content_model.service import ContentModelService
from slaif_agent_site.health import ProbeResult


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


class _UnstartedPool:
    """Fail closed without exposing driver or locator details."""

    def acquire(self, *, timeout: float) -> Any:
        del timeout
        raise TimeoutError()


class CapabilityDatabase(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> ProbeResult: ...

    async def authenticate_agent_capability(self, auth_header: str) -> Any: ...


class AgentDatabaseAdapter(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> ProbeResult: ...

    def content_model_service(self) -> ContentModelService: ...

    async def authenticate_agent_capability(self, auth_header: str) -> Any: ...


class AgentDatabase:
    """Own one runtime pool and expose only semantic service creation."""

    def __init__(
        self,
        pool: _Pool | None = None,
        *,
        capability_database: CapabilityDatabase | None = None,
    ) -> None:
        self._pool: _Pool = pool if pool is not None else _UnstartedPool()
        self._capability_database = capability_database

    async def start(self) -> None:
        if self._capability_database is not None:
            await self._capability_database.start()

    async def stop(self) -> None:
        if self._capability_database is not None:
            await self._capability_database.stop()

    async def readiness(self) -> ProbeResult:
        if self._capability_database is None:
            return ProbeResult.unavailable("database_unavailable")
        return await self._capability_database.readiness()

    def content_model_service(self) -> ContentModelService:
        """Return the semantic adapter for the owned runtime pool."""

        return ContentModelService(self._pool)

    async def authenticate_agent_capability(self, auth_header: str) -> Any:
        if self._capability_database is None:
            raise RuntimeError("capability database unavailable")
        return await self._capability_database.authenticate_agent_capability(
            auth_header
        )


__all__ = ["AgentDatabase", "AgentDatabaseAdapter", "CapabilityDatabase"]

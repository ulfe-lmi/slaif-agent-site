"""Narrow server-owned capability authentication dependency for Agent API."""

from __future__ import annotations

from typing import Any, cast

from slaif_agent_site.health import ProbeResult


class CapabilityAuthenticationDatabase:
    """Expose only capability authentication across the Agent API seam."""

    def __init__(self, database: Any) -> None:
        self._database = database

    async def start(self) -> None:
        await self._database.start()

    async def stop(self) -> None:
        await self._database.stop()

    async def readiness(self) -> ProbeResult:
        return cast(ProbeResult, await self._database.readiness())

    async def authenticate_agent_capability(self, auth_header: str) -> Any:
        return await self._database.authenticate_agent_capability(auth_header)


def create_capability_authentication_database(
    settings: Any | None = None,
) -> CapabilityAuthenticationDatabase:
    """Create the server-owned capability dependency for one app lifespan."""

    from slaif_agent_site.control_api.config import ControlDatabaseSettings
    from slaif_agent_site.control_api.database import ControlDatabase

    selected_settings = settings or ControlDatabaseSettings.load()
    return CapabilityAuthenticationDatabase(ControlDatabase(selected_settings))


__all__ = [
    "CapabilityAuthenticationDatabase",
    "create_capability_authentication_database",
]

"""Agent-owned bounded database adapter."""

from __future__ import annotations

from typing import Any, Protocol

from slaif_agent_site.content_model.service import ContentModelService


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


class _UnstartedPool:
    """Fail closed without exposing driver or locator details."""

    def acquire(self, *, timeout: float) -> Any:
        del timeout
        raise TimeoutError()


class AgentDatabase:
    """Own one runtime pool and expose only semantic service creation."""

    def __init__(self, pool: _Pool | None = None) -> None:
        self._pool: _Pool = pool if pool is not None else _UnstartedPool()

    def content_model_service(self) -> ContentModelService:
        """Return the semantic adapter for the owned runtime pool."""

        return ContentModelService(self._pool)


__all__ = ["AgentDatabase"]

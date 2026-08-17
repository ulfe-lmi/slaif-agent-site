"""Small asyncpg adapter for the foundation's public executor protocol."""

from __future__ import annotations

from typing import Any

import asyncpg


class AsyncpgExecutor:
    """Execute foundation SQL on one caller-owned asyncpg transaction."""

    def __init__(self, connection: asyncpg.Connection[Any]) -> None:
        self._connection = connection

    async def execute(self, sql: str) -> list[tuple[Any, ...]]:
        return [tuple(row) for row in await self._connection.fetch(sql)]


__all__ = ["AsyncpgExecutor"]

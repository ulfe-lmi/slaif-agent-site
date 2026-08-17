"""Explicit one-shot asyncpg connection factories with authority checks."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from pydantic import SecretStr

from .roles import OWNER_ROLE, quote_identifier


@asynccontextmanager
async def provisioner_connection(
    dsn: SecretStr, *, expected_database: str
) -> AsyncIterator[asyncpg.Connection[Any]]:
    connection = await asyncpg.connect(dsn.get_secret_value())
    try:
        row = await connection.fetchrow(
            "SELECT current_database()::text, role_.rolsuper, role_.rolcreaterole "
            "FROM pg_catalog.pg_roles role_ WHERE role_.rolname = current_user"
        )
        if row is None or row[0] != expected_database or not (row[1] or row[2]):
            raise PermissionError("cluster provisioner authority validation failed")
        yield connection
    finally:
        await connection.close()


@asynccontextmanager
async def owner_connection(
    dsn: SecretStr, *, expected_database: str
) -> AsyncIterator[asyncpg.Connection[Any]]:
    connection = await asyncpg.connect(dsn.get_secret_value())
    try:
        row = await connection.fetchrow(
            "SELECT current_database()::text, current_user::text, "
            "pg_has_role(current_user, $1, 'MEMBER')",
            OWNER_ROLE,
        )
        if (
            row is None
            or row[0] != expected_database
            or not (row[1] == OWNER_ROLE or row[2])
        ):
            raise PermissionError("setup-owner authority validation failed")
        await connection.execute(f"SET ROLE {quote_identifier(OWNER_ROLE)}")
        if await connection.fetchval("SELECT current_user::text") != OWNER_ROLE:
            raise PermissionError("setup-owner authority activation failed")
        yield connection
    finally:
        await connection.close()


__all__ = ["owner_connection", "provisioner_connection"]

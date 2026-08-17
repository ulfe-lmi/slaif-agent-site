"""Exact non-login PostgreSQL privilege-role manifest and reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import asyncpg


@dataclass(frozen=True, slots=True)
class DatabaseRole:
    """One password-free privilege role with fail-closed cluster attributes."""

    name: str
    purpose: str
    service_credential: bool


DATABASE_ROLES: Final[tuple[DatabaseRole, ...]] = (
    DatabaseRole("slaif_owner", "one-shot migration and COW owner", False),
    DatabaseRole("slaif_control", "control service", True),
    DatabaseRole("slaif_editor_runtime", "human-editor COW runtime", True),
    DatabaseRole("slaif_agent_runtime", "agent COW runtime", True),
    DatabaseRole("slaif_public_reader", "canonical render reader", True),
    DatabaseRole("slaif_preview_reader", "workspace preview reader", True),
    DatabaseRole("slaif_reviewer", "review and promotion worker", True),
    DatabaseRole("slaif_scheduler", "job scheduler", True),
    DatabaseRole("slaif_media", "media metadata service", True),
    DatabaseRole("slaif_gc", "media garbage collector", True),
)
ROLE_NAMES: Final[tuple[str, ...]] = tuple(role.name for role in DATABASE_ROLES)
OWNER_ROLE: Final[str] = "slaif_owner"
RUNTIME_ROLES: Final[tuple[str, str]] = (
    "slaif_editor_runtime",
    "slaif_agent_runtime",
)
REVIEWER_ROLES: Final[tuple[str]] = ("slaif_reviewer",)


def quote_identifier(identifier: str) -> str:
    """Quote a trusted or validated PostgreSQL identifier deterministically."""

    if not identifier or "\x00" in identifier:
        raise ValueError("invalid PostgreSQL identifier")
    return '"' + identifier.replace('"', '""') + '"'


async def provision_database_roles(
    connection: asyncpg.Connection[Any], *, expected_database: str
) -> None:
    """Create/reconcile privilege roles using explicit operator authority.

    The function never creates login principals or passwords. An institution
    may instead pre-provision this manifest and use the validation command.
    """

    row = await connection.fetchrow(
        "SELECT current_database()::text AS database_name, "
        "current_user::text AS user_name, role_.rolsuper, role_.rolcreaterole "
        "FROM pg_catalog.pg_roles role_ WHERE role_.rolname = current_user"
    )
    if (
        row is None
        or row["database_name"] != expected_database
        or not (row["rolsuper"] or row["rolcreaterole"])
    ):
        raise PermissionError("cluster provisioner authority validation failed")

    for role in DATABASE_ROLES:
        identifier = quote_identifier(role.name)
        exists = await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = $1)",
            role.name,
        )
        if not exists:
            await connection.execute(f"CREATE ROLE {identifier}")
        await connection.execute(
            f"ALTER ROLE {identifier} NOLOGIN NOSUPERUSER NOCREATEDB "
            "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS"
        )

    # A privilege role must not inherit or SET ROLE into any other role.
    inherited_edges = await connection.fetch(
        "SELECT granted.rolname::text, member.rolname::text "
        "FROM pg_catalog.pg_auth_members membership "
        "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
        "WHERE member.rolname = ANY($1::text[])",
        list(ROLE_NAMES),
    )
    for granted, member in inherited_edges:
        await connection.execute(
            f"REVOKE {quote_identifier(granted)} FROM {quote_identifier(member)}"
        )

    database = quote_identifier(expected_database)
    await connection.execute(
        f"GRANT CONNECT, CREATE ON DATABASE {database} TO "
        f"{quote_identifier(OWNER_ROLE)}"
    )
    await connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
    await connection.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")


__all__ = [
    "DATABASE_ROLES",
    "OWNER_ROLE",
    "REVIEWER_ROLES",
    "ROLE_NAMES",
    "RUNTIME_ROLES",
    "DatabaseRole",
    "provision_database_roles",
    "quote_identifier",
]

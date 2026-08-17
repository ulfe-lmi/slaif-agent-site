"""Exact non-login PostgreSQL privilege-role manifest and reconciliation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

import asyncpg


@dataclass(frozen=True, slots=True)
class DatabaseRole:
    """One password-free privilege role with fail-closed cluster attributes."""

    name: str
    purpose: str
    service_credential: bool


@dataclass(frozen=True, slots=True)
class DatabaseLogin:
    """One fixed local login principal and its sole privilege membership."""

    name: str
    privilege_role: str
    secret_file_stem: str


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
DATABASE_LOGINS: Final[tuple[DatabaseLogin, ...]] = (
    DatabaseLogin("slaif_bootstrap_login", "slaif_owner", "bootstrap"),
    DatabaseLogin("slaif_control_login", "slaif_control", "control"),
    DatabaseLogin("slaif_editor_login", "slaif_editor_runtime", "editor"),
    DatabaseLogin("slaif_agent_login", "slaif_agent_runtime", "agent"),
    DatabaseLogin("slaif_public_login", "slaif_public_reader", "public"),
    DatabaseLogin("slaif_preview_login", "slaif_preview_reader", "preview"),
    DatabaseLogin("slaif_reviewer_login", "slaif_reviewer", "reviewer"),
    DatabaseLogin("slaif_scheduler_login", "slaif_scheduler", "scheduler"),
    DatabaseLogin("slaif_media_login", "slaif_media", "media"),
    DatabaseLogin("slaif_gc_login", "slaif_gc", "gc"),
)
LOGIN_NAMES: Final[tuple[str, ...]] = tuple(login.name for login in DATABASE_LOGINS)


def quote_identifier(identifier: str) -> str:
    """Quote a trusted or validated PostgreSQL identifier deterministically."""

    if not identifier or "\x00" in identifier:
        raise ValueError("invalid PostgreSQL identifier")
    return '"' + identifier.replace('"', '""') + '"'


async def provision_database_roles(
    connection: asyncpg.Connection[Any],
    *,
    expected_database: str,
    login_passwords: Mapping[str, str] | None = None,
) -> None:
    """Create/reconcile privilege roles using explicit operator authority.

    Login provisioning is optional and used only by the local deployment
    bootstrap. Names and memberships remain fixed by this module; callers may
    supply password values but cannot select database principals or grants.
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

    if login_passwords is None:
        return
    if set(login_passwords) != set(LOGIN_NAMES):
        raise ValueError("local login password manifest is incomplete")

    for login in DATABASE_LOGINS:
        identifier = quote_identifier(login.name)
        exists = await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = $1)",
            login.name,
        )
        if not exists:
            await connection.execute(f"CREATE ROLE {identifier}")
        password_literal = await connection.fetchval(
            "SELECT pg_catalog.quote_literal($1::text)", login_passwords[login.name]
        )
        if not isinstance(password_literal, str):
            raise RuntimeError("PostgreSQL password quoting failed")
        await connection.execute(
            f"ALTER ROLE {identifier} LOGIN PASSWORD {password_literal} "
            "NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION NOBYPASSRLS"
        )

    membership_edges = await connection.fetch(
        "SELECT granted.rolname::text, member.rolname::text "
        "FROM pg_catalog.pg_auth_members membership "
        "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
        "WHERE member.rolname = ANY($1::text[])",
        list(LOGIN_NAMES),
    )
    for granted, member in membership_edges:
        await connection.execute(
            f"REVOKE {quote_identifier(granted)} FROM {quote_identifier(member)}"
        )
    delegation_edges = await connection.fetch(
        "SELECT granted.rolname::text, member.rolname::text "
        "FROM pg_catalog.pg_auth_members membership "
        "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
        "WHERE granted.rolname = ANY($1::text[])",
        list(LOGIN_NAMES),
    )
    for granted, member in delegation_edges:
        await connection.execute(
            f"REVOKE {quote_identifier(granted)} FROM {quote_identifier(member)}"
        )
    for login in DATABASE_LOGINS:
        await connection.execute(
            f"GRANT {quote_identifier(login.privilege_role)} "
            f"TO {quote_identifier(login.name)}"
        )


async def local_login_violations(
    connection: asyncpg.Connection[Any],
) -> tuple[str, ...]:
    """Return stable violations for the fixed local-login security contract."""

    violations: list[str] = []
    for login in DATABASE_LOGINS:
        row = await connection.fetchrow(
            "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, "
            "rolinherit, rolreplication, rolbypassrls "
            "FROM pg_catalog.pg_roles WHERE rolname = $1",
            login.name,
        )
        if row is None:
            violations.append(f"login/{login.name}/missing")
            continue
        if tuple(bool(value) for value in row) != (
            True,
            False,
            False,
            False,
            True,
            False,
            False,
        ):
            violations.append(f"login/{login.name}/attributes")
        memberships = await connection.fetch(
            "SELECT granted.rolname::text, membership.admin_option "
            "FROM pg_catalog.pg_auth_members membership "
            "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
            "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
            "WHERE member.rolname = $1 ORDER BY granted.rolname",
            login.name,
        )
        actual = tuple((row[0], bool(row[1])) for row in memberships)
        if actual != ((login.privilege_role, False),):
            violations.append(f"login/{login.name}/memberships")
        delegated = await connection.fetchval(
            "SELECT EXISTS ("
            "SELECT 1 FROM pg_catalog.pg_auth_members membership "
            "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
            "WHERE granted.rolname = $1)",
            login.name,
        )
        if delegated:
            violations.append(f"login/{login.name}/members")
    return tuple(violations)


__all__ = [
    "DATABASE_ROLES",
    "DATABASE_LOGINS",
    "LOGIN_NAMES",
    "OWNER_ROLE",
    "REVIEWER_ROLES",
    "ROLE_NAMES",
    "RUNTIME_ROLES",
    "DatabaseRole",
    "DatabaseLogin",
    "local_login_violations",
    "provision_database_roles",
    "quote_identifier",
]

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
LOCAL_LOGIN_CONNECTION_LIMIT: Final[int] = 10
LOCAL_LOGIN_SCHEMAS: Final[tuple[str, ...]] = (
    "control",
    "content",
    "audit",
    "agentcow",
)
_DEFAULT_PRIVILEGE_OBJECTS: Final[dict[str, str]] = {
    "r": "TABLES",
    "S": "SEQUENCES",
    "f": "FUNCTIONS",
    "T": "TYPES",
    "n": "SCHEMAS",
}
_COLUMN_PRIVILEGES: Final[frozenset[str]] = frozenset(
    {"SELECT", "INSERT", "UPDATE", "REFERENCES"}
)


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
            f"REVOKE {quote_identifier(granted)} FROM "
            f"{quote_identifier(member)} CASCADE"
        )

    database = quote_identifier(expected_database)
    await connection.execute(f"REVOKE ALL ON DATABASE {database} FROM PUBLIC")
    for role in DATABASE_ROLES:
        role_identifier = quote_identifier(role.name)
        await connection.execute(
            f"REVOKE ALL ON DATABASE {database} FROM {role_identifier}"
        )
        await connection.execute(
            f"GRANT CONNECT ON DATABASE {database} TO {role_identifier}"
        )
    await connection.execute(
        f"GRANT CREATE ON DATABASE {database} TO {quote_identifier(OWNER_ROLE)}"
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
            "NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION "
            f"NOBYPASSRLS CONNECTION LIMIT {LOCAL_LOGIN_CONNECTION_LIMIT} "
            "VALID UNTIL 'infinity'"
        )
        await connection.execute(f"ALTER ROLE {identifier} RESET ALL")

    ownerships = await _local_login_ownerships(
        connection, expected_database=expected_database
    )
    if ownerships:
        login_name, category, identity = ownerships[0]
        raise RuntimeError(
            "local login owns protected database object: "
            f"{login_name}/{category}/{identity}"
        )

    default_grants = await _local_login_default_grants(connection)
    unknown_default_types = sorted(
        {row[3] for row in default_grants if row[3] not in _DEFAULT_PRIVILEGE_OBJECTS}
    )
    if unknown_default_types:
        raise RuntimeError("local login has an unknown default-privilege object type")
    column_grants = await _local_login_direct_column_grants(connection)
    if any(row[4] not in _COLUMN_PRIVILEGES for row in column_grants):
        raise RuntimeError("local login has an unknown column privilege")

    existing_schemas = tuple(
        row[0]
        for row in await connection.fetch(
            "SELECT nspname::text FROM pg_catalog.pg_namespace "
            "WHERE nspname = ANY($1::text[]) ORDER BY nspname",
            list(LOCAL_LOGIN_SCHEMAS),
        )
    )
    for login in DATABASE_LOGINS:
        login_identifier = quote_identifier(login.name)
        await connection.execute(
            f"REVOKE ALL ON DATABASE {database} FROM {login_identifier} CASCADE"
        )
        for schema in existing_schemas:
            schema_identifier = quote_identifier(schema)
            await connection.execute(
                f"REVOKE ALL ON SCHEMA {schema_identifier} "
                f"FROM {login_identifier} CASCADE"
            )
            await connection.execute(
                f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema_identifier} "
                f"FROM {login_identifier} CASCADE"
            )
            await connection.execute(
                f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema_identifier} "
                f"FROM {login_identifier} CASCADE"
            )
            await connection.execute(
                f"REVOKE ALL ON ALL ROUTINES IN SCHEMA {schema_identifier} "
                f"FROM {login_identifier} CASCADE"
            )

    for (
        login_name,
        column_schema,
        relation_name,
        column_name,
        privilege,
    ) in column_grants:
        await connection.execute(
            f"REVOKE {privilege} ({quote_identifier(column_name)}) ON TABLE "
            f"{quote_identifier(column_schema)}.{quote_identifier(relation_name)} "
            f"FROM {quote_identifier(login_name)} CASCADE"
        )

    for login_name, owner_name, schema_name, object_type in default_grants:
        schema_clause = (
            "" if schema_name is None else f" IN SCHEMA {quote_identifier(schema_name)}"
        )
        await connection.execute(
            "ALTER DEFAULT PRIVILEGES FOR ROLE "
            f"{quote_identifier(owner_name)}{schema_clause} REVOKE ALL ON "
            f"{_DEFAULT_PRIVILEGE_OBJECTS[object_type]} FROM "
            f"{quote_identifier(login_name)}"
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
            f"REVOKE {quote_identifier(granted)} FROM "
            f"{quote_identifier(member)} CASCADE"
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
            f"REVOKE {quote_identifier(granted)} FROM "
            f"{quote_identifier(member)} CASCADE"
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
    missing_login = False
    for login in DATABASE_LOGINS:
        row = await connection.fetchrow(
            "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, "
            "rolinherit, rolreplication, rolbypassrls, "
            "rolconnlimit = $2, rolvaliduntil = 'infinity'::timestamptz, "
            "rolconfig IS NULL OR cardinality(rolconfig) = 0 "
            "FROM pg_catalog.pg_roles WHERE rolname = $1",
            login.name,
            LOCAL_LOGIN_CONNECTION_LIMIT,
        )
        if row is None:
            violations.append(f"login/{login.name}/missing")
            missing_login = True
            continue
        if tuple(bool(value) for value in row) != (
            True,
            False,
            False,
            False,
            True,
            False,
            False,
            True,
            True,
            True,
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

    current_database = await connection.fetchval("SELECT current_database()::text")
    database_owner = await connection.fetchval(
        "SELECT owner.rolname::text FROM pg_catalog.pg_database database_ "
        "JOIN pg_catalog.pg_roles owner ON owner.oid = database_.datdba "
        "WHERE database_.datname = current_database()"
    )
    database_acl = await connection.fetch(
        "SELECT COALESCE(grantee.rolname::text, 'PUBLIC'), "
        "acl.privilege_type::text, acl.is_grantable "
        "FROM pg_catalog.pg_database database_ "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(database_.datacl) acl "
        "LEFT JOIN pg_catalog.pg_roles grantee ON grantee.oid = acl.grantee "
        "WHERE database_.datname = current_database() "
        "ORDER BY 1, 2"
    )
    expected_database_acl = {
        (role.name, privilege, False)
        for role in DATABASE_ROLES
        for privilege in (
            ("CONNECT", "CREATE") if role.name == OWNER_ROLE else ("CONNECT",)
        )
    }
    actual_product_acl = {
        (row[0], row[1], bool(row[2]))
        for row in database_acl
        if row[0] in {*ROLE_NAMES, *LOGIN_NAMES, "PUBLIC"}
    }
    if actual_product_acl != expected_database_acl:
        violations.append("database/product-principal-acl")
    unexpected_acl = {
        (row[0], row[1], bool(row[2]))
        for row in database_acl
        if row[0] not in {*ROLE_NAMES, *LOGIN_NAMES, "PUBLIC", database_owner}
    }
    if unexpected_acl:
        violations.append("database/unexpected-principal-acl")

    for login_name, category, identity, privilege in await _local_login_direct_grants(
        connection
    ):
        violations.append(
            f"login/{login_name}/direct-{category}:{identity}:{privilege.casefold()}"
        )
    for (
        login_name,
        owner_name,
        schema_name,
        object_type,
    ) in await _local_login_default_grants(connection):
        scope = schema_name or "global"
        violations.append(
            f"login/{login_name}/default-acl:{owner_name}:{scope}:{object_type}"
        )
    for login_name, category, identity in await _local_login_ownerships(
        connection, expected_database=str(current_database)
    ):
        violations.append(f"login/{login_name}/owner:{category}:{identity}")
    if not missing_login:
        violations.extend(await _effective_authority_violations(connection))
    return tuple(violations)


async def _local_login_direct_grants(
    connection: asyncpg.Connection[Any],
) -> tuple[tuple[str, str, str, str], ...]:
    rows = await connection.fetch(
        "SELECT login.rolname::text, grant_.category, grant_.identity, "
        "grant_.privilege_type FROM pg_catalog.pg_roles login JOIN LATERAL ("
        "SELECT 'database'::text AS category, database_.datname::text AS identity, "
        "acl.privilege_type::text AS privilege_type, acl.grantee "
        "FROM pg_catalog.pg_database database_ "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(database_.datacl) acl "
        "WHERE database_.datname = current_database() UNION ALL "
        "SELECT 'schema', namespace_.nspname::text, acl.privilege_type::text, "
        "acl.grantee FROM pg_catalog.pg_namespace namespace_ "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(namespace_.nspacl) acl "
        "WHERE namespace_.nspname = ANY($2::text[]) UNION ALL "
        "SELECT CASE WHEN class_.relkind = 'S' THEN 'sequence' ELSE 'relation' END, "
        "namespace_.nspname::text || '.' || class_.relname::text, "
        "acl.privilege_type::text, acl.grantee FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(class_.relacl) acl "
        "WHERE namespace_.nspname = ANY($2::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'f', 'S') UNION ALL "
        "SELECT 'column', namespace_.nspname::text || '.' || "
        "class_.relname::text || '.' || attribute_.attname::text, "
        "acl.privilege_type::text, acl.grantee "
        "FROM pg_catalog.pg_attribute attribute_ "
        "JOIN pg_catalog.pg_class class_ ON class_.oid = attribute_.attrelid "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(attribute_.attacl) acl "
        "WHERE namespace_.nspname = ANY($2::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'f') "
        "AND attribute_.attnum > 0 AND NOT attribute_.attisdropped UNION ALL "
        "SELECT 'routine', namespace_.nspname::text || '.' || proc.proname::text || "
        "'(' || pg_catalog.pg_get_function_identity_arguments(proc.oid) || ')', "
        "acl.privilege_type::text, acl.grantee FROM pg_catalog.pg_proc proc "
        "JOIN pg_catalog.pg_namespace namespace_ ON namespace_.oid = proc.pronamespace "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(proc.proacl) acl "
        "WHERE namespace_.nspname = ANY($2::text[])"
        ") grant_ ON grant_.grantee = login.oid "
        "WHERE login.rolname = ANY($1::text[]) "
        "ORDER BY login.rolname, grant_.category, grant_.identity, "
        "grant_.privilege_type",
        list(LOGIN_NAMES),
        list(LOCAL_LOGIN_SCHEMAS),
    )
    return tuple(tuple(row) for row in rows)


async def _local_login_direct_column_grants(
    connection: asyncpg.Connection[Any],
) -> tuple[tuple[str, str, str, str, str], ...]:
    rows = await connection.fetch(
        "SELECT login.rolname::text, namespace_.nspname::text, "
        "class_.relname::text, attribute_.attname::text, acl.privilege_type::text "
        "FROM pg_catalog.pg_attribute attribute_ "
        "JOIN pg_catalog.pg_class class_ ON class_.oid = attribute_.attrelid "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(attribute_.attacl) acl "
        "JOIN pg_catalog.pg_roles login ON login.oid = acl.grantee "
        "WHERE login.rolname = ANY($1::text[]) "
        "AND namespace_.nspname = ANY($2::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'f') "
        "AND attribute_.attnum > 0 AND NOT attribute_.attisdropped "
        "ORDER BY login.rolname, namespace_.nspname, class_.relname, "
        "attribute_.attname, acl.privilege_type",
        list(LOGIN_NAMES),
        list(LOCAL_LOGIN_SCHEMAS),
    )
    return tuple(tuple(row) for row in rows)


async def _local_login_default_grants(
    connection: asyncpg.Connection[Any],
) -> tuple[tuple[str, str, str | None, str], ...]:
    rows = await connection.fetch(
        "SELECT DISTINCT login.rolname::text, owner.rolname::text, "
        "namespace_.nspname::text, defaults.defaclobjtype::text "
        "FROM pg_catalog.pg_default_acl defaults "
        "JOIN pg_catalog.pg_roles owner ON owner.oid = defaults.defaclrole "
        "LEFT JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = defaults.defaclnamespace "
        "CROSS JOIN LATERAL pg_catalog.aclexplode(defaults.defaclacl) acl "
        "JOIN pg_catalog.pg_roles login ON login.oid = acl.grantee "
        "WHERE login.rolname = ANY($1::text[]) "
        "AND (defaults.defaclnamespace = 0 "
        "OR namespace_.nspname = ANY($2::text[])) "
        "ORDER BY 1, 2, 3, 4",
        list(LOGIN_NAMES),
        list(LOCAL_LOGIN_SCHEMAS),
    )
    return tuple(tuple(row) for row in rows)


async def _local_login_ownerships(
    connection: asyncpg.Connection[Any], *, expected_database: str
) -> tuple[tuple[str, str, str], ...]:
    rows = await connection.fetch(
        "SELECT login.rolname::text, owned.category, owned.identity "
        "FROM pg_catalog.pg_roles login JOIN LATERAL ("
        "SELECT 'database'::text AS category, database_.datname::text AS identity, "
        "database_.datdba AS owner_oid FROM pg_catalog.pg_database database_ "
        "WHERE database_.datname = $2 UNION ALL "
        "SELECT 'schema', namespace_.nspname::text, namespace_.nspowner "
        "FROM pg_catalog.pg_namespace namespace_ "
        "WHERE namespace_.nspname = ANY($3::text[]) UNION ALL "
        "SELECT CASE WHEN class_.relkind = 'S' THEN 'sequence' ELSE 'relation' END, "
        "namespace_.nspname::text || '.' || class_.relname::text, class_.relowner "
        "FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "WHERE namespace_.nspname = ANY($3::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'f', 'S') UNION ALL "
        "SELECT 'routine', namespace_.nspname::text || '.' || proc.proname::text || "
        "'(' || pg_catalog.pg_get_function_identity_arguments(proc.oid) || ')', "
        "proc.proowner FROM pg_catalog.pg_proc proc "
        "JOIN pg_catalog.pg_namespace namespace_ ON namespace_.oid = proc.pronamespace "
        "WHERE namespace_.nspname = ANY($3::text[])"
        ") owned ON owned.owner_oid = login.oid "
        "WHERE login.rolname = ANY($1::text[]) "
        "ORDER BY login.rolname, owned.category, owned.identity",
        list(LOGIN_NAMES),
        expected_database,
        list(LOCAL_LOGIN_SCHEMAS),
    )
    return tuple(tuple(row) for row in rows)


async def _effective_authority_violations(
    connection: asyncpg.Connection[Any],
) -> tuple[str, ...]:
    rows = await connection.fetch(
        "WITH principals AS ("
        "SELECT * FROM unnest($1::text[], $2::text[]) "
        "AS pair(login_name, role_name)), comparisons AS ("
        "SELECT pair.login_name, 'database'::text AS category, "
        "current_database()::text AS identity, privilege.name::text AS privilege, "
        "has_database_privilege(pair.login_name, current_database(), privilege.name) "
        "IS NOT DISTINCT FROM has_database_privilege("
        "pair.role_name, current_database(), privilege.name) AS equal "
        "FROM principals pair CROSS JOIN "
        "(VALUES ('CONNECT'), ('CREATE'), ('TEMPORARY')) privilege(name) UNION ALL "
        "SELECT pair.login_name, 'schema', namespace_.nspname::text, privilege.name, "
        "has_schema_privilege(pair.login_name, namespace_.oid, privilege.name) "
        "IS NOT DISTINCT FROM has_schema_privilege("
        "pair.role_name, namespace_.oid, privilege.name) "
        "FROM principals pair CROSS JOIN pg_catalog.pg_namespace namespace_ "
        "CROSS JOIN (VALUES ('USAGE'), ('CREATE')) privilege(name) "
        "WHERE namespace_.nspname = ANY($3::text[]) UNION ALL "
        "SELECT pair.login_name, 'relation', "
        "namespace_.nspname::text || '.' || class_.relname::text, privilege.name, "
        "has_table_privilege(pair.login_name, class_.oid, privilege.name) "
        "IS NOT DISTINCT FROM has_table_privilege("
        "pair.role_name, class_.oid, privilege.name) "
        "FROM principals pair CROSS JOIN pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "CROSS JOIN (VALUES ('SELECT'), ('INSERT'), ('UPDATE'), ('DELETE'), "
        "('TRUNCATE'), ('REFERENCES'), ('TRIGGER')) privilege(name) "
        "WHERE namespace_.nspname = ANY($3::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'f') UNION ALL "
        "SELECT pair.login_name, 'column', namespace_.nspname::text || '.' || "
        "class_.relname::text || '.' || attribute_.attname::text, privilege.name, "
        "has_column_privilege(pair.login_name, class_.oid, attribute_.attnum, "
        "privilege.name) IS NOT DISTINCT FROM has_column_privilege("
        "pair.role_name, class_.oid, attribute_.attnum, privilege.name) "
        "FROM principals pair CROSS JOIN pg_catalog.pg_attribute attribute_ "
        "JOIN pg_catalog.pg_class class_ ON class_.oid = attribute_.attrelid "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "CROSS JOIN (VALUES ('SELECT'), ('INSERT'), ('UPDATE'), ('REFERENCES')) "
        "privilege(name) WHERE namespace_.nspname = ANY($3::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'f') "
        "AND attribute_.attnum > 0 AND NOT attribute_.attisdropped UNION ALL "
        "SELECT pair.login_name, 'sequence', "
        "namespace_.nspname::text || '.' || class_.relname::text, privilege.name, "
        "has_sequence_privilege(pair.login_name, class_.oid, privilege.name) "
        "IS NOT DISTINCT FROM has_sequence_privilege("
        "pair.role_name, class_.oid, privilege.name) "
        "FROM principals pair CROSS JOIN pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "CROSS JOIN (VALUES ('SELECT'), ('UPDATE'), ('USAGE')) privilege(name) "
        "WHERE namespace_.nspname = ANY($3::text[]) AND class_.relkind = 'S' UNION ALL "
        "SELECT pair.login_name, 'routine', "
        "namespace_.nspname::text || '.' || proc.proname::text || '(' || "
        "pg_catalog.pg_get_function_identity_arguments(proc.oid) || ')', 'EXECUTE', "
        "has_function_privilege(pair.login_name, proc.oid, 'EXECUTE') "
        "IS NOT DISTINCT FROM has_function_privilege("
        "pair.role_name, proc.oid, 'EXECUTE') "
        "FROM principals pair CROSS JOIN pg_catalog.pg_proc proc "
        "JOIN pg_catalog.pg_namespace namespace_ ON namespace_.oid = proc.pronamespace "
        "WHERE namespace_.nspname = ANY($3::text[])) "
        "SELECT login_name, category, identity, privilege FROM comparisons "
        "WHERE NOT equal ORDER BY login_name, category, identity, privilege",
        [login.name for login in DATABASE_LOGINS],
        [login.privilege_role for login in DATABASE_LOGINS],
        list(LOCAL_LOGIN_SCHEMAS),
    )
    return tuple(
        f"login/{login}/effective-{category}:{identity}:{privilege.casefold()}"
        for login, category, identity, privilege in rows
    )


__all__ = [
    "DATABASE_ROLES",
    "DATABASE_LOGINS",
    "LOGIN_NAMES",
    "LOCAL_LOGIN_CONNECTION_LIMIT",
    "LOCAL_LOGIN_SCHEMAS",
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

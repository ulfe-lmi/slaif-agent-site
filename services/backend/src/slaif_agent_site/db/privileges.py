"""Product-owned PostgreSQL privilege application and effective verification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import asyncpg

from .roles import (
    OWNER_ROLE,
    REVIEWER_ROLES,
    ROLE_NAMES,
    RUNTIME_ROLES,
    quote_identifier,
)

PRODUCT_SCHEMAS = ("control", "content", "audit")
READ_ROLES = ("slaif_public_reader", "slaif_preview_reader")
NO_CONTENT_ROLES = (
    "slaif_control",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)
ALLOWED_CLEAN_RELATIONS = {
    ("control", "alembic_version"),
    ("control", "bootstrap_readiness"),
}


@dataclass(frozen=True, slots=True)
class PrivilegeValidation:
    safe: bool
    violations: tuple[str, ...]


async def revoke_public_foundation_access(
    connection: asyncpg.Connection[Any],
) -> None:
    """Remove PostgreSQL defaults without naming foundation-private objects."""

    exists = await connection.fetchval(
        "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_namespace "
        "WHERE nspname = 'agentcow')"
    )
    if not exists:
        raise RuntimeError("foundation schema is missing")
    await connection.execute("REVOKE ALL ON SCHEMA agentcow FROM PUBLIC")
    await connection.execute(
        "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA agentcow FROM PUBLIC"
    )
    await connection.execute("REVOKE ALL ON ALL TABLES IN SCHEMA agentcow FROM PUBLIC")


async def apply_product_privileges(
    connection: asyncpg.Connection[Any],
) -> None:
    """Apply only grants that correspond to objects present in this baseline."""

    for schema in (*PRODUCT_SCHEMAS, "agentcow"):
        schema_identifier = quote_identifier(schema)
        await connection.execute(
            f"REVOKE ALL ON SCHEMA {schema_identifier} FROM PUBLIC"
        )
        for role in ROLE_NAMES[1:]:
            await connection.execute(
                f"REVOKE CREATE ON SCHEMA {schema_identifier} "
                f"FROM {quote_identifier(role)}"
            )

    for schema in ("control", "audit"):
        schema_identifier = quote_identifier(schema)
        for role in ROLE_NAMES[1:]:
            role_identifier = quote_identifier(role)
            await connection.execute(
                f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema_identifier} "
                f"FROM {role_identifier}"
            )
            await connection.execute(
                f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema_identifier} "
                f"FROM {role_identifier}"
            )
            await connection.execute(
                f"REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA {schema_identifier} "
                f"FROM {role_identifier}"
            )

    for role in (*NO_CONTENT_ROLES, *READ_ROLES):
        role_identifier = quote_identifier(role)
        await connection.execute(
            f'REVOKE ALL ON ALL TABLES IN SCHEMA "content" FROM {role_identifier}'
        )
        await connection.execute(
            f'REVOKE ALL ON ALL SEQUENCES IN SCHEMA "content" FROM {role_identifier}'
        )
        await connection.execute(
            'REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA "content" '
            f"FROM {role_identifier}"
        )

    for role in ROLE_NAMES[1:]:
        await connection.execute(
            f"REVOKE ALL ON ALL TABLES IN SCHEMA agentcow FROM {quote_identifier(role)}"
        )
    for role in (*RUNTIME_ROLES, *NO_CONTENT_ROLES, *READ_ROLES):
        await connection.execute(
            "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA agentcow "
            f"FROM {quote_identifier(role)}"
        )

    for role in READ_ROLES:
        await connection.execute(
            f'GRANT USAGE ON SCHEMA "content" TO {quote_identifier(role)}'
        )

    views = await connection.fetch(
        "SELECT class_.relname::text FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "WHERE namespace_.nspname = 'content' AND class_.relkind = 'v' "
        "ORDER BY class_.relname"
    )
    for (view_name,) in views:
        relation = f'"content".{quote_identifier(view_name)}'
        for role in READ_ROLES:
            await connection.execute(
                f"GRANT SELECT ON {relation} TO {quote_identifier(role)}"
            )


async def _role_violations(connection: asyncpg.Connection[Any]) -> list[str]:
    violations: list[str] = []
    rows = await connection.fetch(
        "SELECT rolname::text, rolsuper, rolcreatedb, rolcreaterole, rolinherit, "
        "rolcanlogin, rolreplication, rolbypassrls FROM pg_catalog.pg_roles "
        "WHERE rolname = ANY($1::text[]) ORDER BY rolname",
        list(ROLE_NAMES),
    )
    by_name = {row[0]: tuple(row[1:]) for row in rows}
    for role in ROLE_NAMES:
        flags = by_name.get(role)
        if flags is None:
            violations.append(f"role/{role}/missing")
        elif any(flags):
            labels = (
                "superuser",
                "createdb",
                "createrole",
                "inherit",
                "login",
                "replication",
                "bypassrls",
            )
            enabled = ",".join(
                label for label, value in zip(labels, flags, strict=True) if value
            )
            violations.append(f"role/{role}/unsafe-attributes:{enabled}")

    edges = await connection.fetch(
        "SELECT granted.rolname::text, member.rolname::text "
        "FROM pg_catalog.pg_auth_members membership "
        "JOIN pg_catalog.pg_roles granted ON granted.oid = membership.roleid "
        "JOIN pg_catalog.pg_roles member ON member.oid = membership.member "
        "WHERE member.rolname = ANY($1::text[]) "
        "ORDER BY granted.rolname, member.rolname",
        list(ROLE_NAMES),
    )
    for granted, member in edges:
        violations.append(f"membership/{member}/can-set-role:{granted}")

    combined = await connection.fetch(
        "SELECT principal.rolname::text, "
        "array_agg(target.rolname::text ORDER BY target.rolname) "
        "FROM pg_catalog.pg_roles principal "
        "CROSS JOIN pg_catalog.pg_roles target "
        "WHERE target.rolname = ANY($1::text[]) "
        "AND NOT (principal.rolsuper OR principal.rolcreaterole) "
        "AND pg_has_role(principal.oid, target.oid, 'MEMBER') "
        "GROUP BY principal.oid, principal.rolname HAVING count(*) > 1 "
        "ORDER BY principal.rolname",
        list(ROLE_NAMES),
    )
    for principal, authorities in combined:
        violations.append(
            f"membership/{principal}/combined-roles:{','.join(authorities)}"
        )
    return violations


async def _schema_violations(connection: asyncpg.Connection[Any]) -> list[str]:
    violations: list[str] = []
    schemas = await connection.fetch(
        "SELECT namespace_.nspname::text, owner.rolname::text, "
        "EXISTS (SELECT 1 FROM aclexplode(COALESCE(namespace_.nspacl, "
        "acldefault('n', namespace_.nspowner))) acl "
        "WHERE acl.grantee = 0 AND acl.privilege_type IN ('USAGE', 'CREATE')) "
        "FROM pg_catalog.pg_namespace namespace_ "
        "JOIN pg_catalog.pg_roles owner ON owner.oid = namespace_.nspowner "
        "WHERE namespace_.nspname = ANY($1::text[]) ORDER BY namespace_.nspname",
        [*PRODUCT_SCHEMAS, "agentcow"],
    )
    by_name = {row[0]: (row[1], row[2]) for row in schemas}
    for schema in (*PRODUCT_SCHEMAS, "agentcow"):
        state = by_name.get(schema)
        if state is None:
            violations.append(f"schema/{schema}/missing")
            continue
        owner, public_access = state
        if owner != OWNER_ROLE:
            violations.append(f"schema/{schema}/owner:{owner}")
        if public_access:
            violations.append(f"schema/{schema}/public-authority")
        for role in ROLE_NAMES[1:]:
            can_create = await connection.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                "AND has_schema_privilege(reachable.oid, $2, 'CREATE'))",
                role,
                schema,
            )
            if can_create:
                violations.append(f"schema/{schema}/{role}/create")
    return violations


async def _relation_violations(
    connection: asyncpg.Connection[Any], *, expect_clean_content: bool
) -> list[str]:
    violations: list[str] = []
    relations = await connection.fetch(
        "SELECT namespace_.nspname::text, class_.relname::text, class_.relkind::text, "
        "owner.rolname::text, class_.oid::bigint "
        "FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "JOIN pg_catalog.pg_roles owner ON owner.oid = class_.relowner "
        "WHERE namespace_.nspname = ANY($1::text[]) "
        "AND class_.relkind IN ('r', 'p', 'v', 'm', 'S') "
        "ORDER BY namespace_.nspname, class_.relname",
        [*PRODUCT_SCHEMAS, "agentcow"],
    )
    for schema, name, kind, owner, oid in relations:
        if owner != OWNER_ROLE:
            violations.append(f"relation/{schema}.{name}/owner:{owner}")
        if expect_clean_content and schema == "content":
            violations.append(f"relation/{schema}.{name}/unexpected-clean-object")
        if (
            expect_clean_content
            and schema in {"control", "audit"}
            and (schema, name) not in ALLOWED_CLEAN_RELATIONS
        ):
            violations.append(f"relation/{schema}.{name}/unexpected-clean-object")

        for role in ROLE_NAMES[1:]:
            privileges = tuple(
                bool(value)
                for value in await connection.fetchrow(
                    "SELECT "
                    "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                    "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                    "AND has_table_privilege(reachable.oid, $2::oid, 'SELECT')), "
                    "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                    "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                    "AND has_table_privilege(reachable.oid, $2::oid, 'INSERT')), "
                    "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                    "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                    "AND has_table_privilege(reachable.oid, $2::oid, 'UPDATE')), "
                    "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                    "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                    "AND has_table_privilege(reachable.oid, $2::oid, 'DELETE')), "
                    "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                    "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                    "AND has_table_privilege(reachable.oid, $2::oid, 'TRUNCATE'))",
                    role,
                    oid,
                )
            )
            expected = (False, False, False, False, False)
            if schema == "content" and kind == "v":
                if role in RUNTIME_ROLES:
                    expected = (True, True, True, True, False)
                elif role in (*REVIEWER_ROLES, *READ_ROLES):
                    expected = (True, False, False, False, False)
            if privileges != expected:
                violations.append(
                    f"relation/{schema}.{name}/{role}/effective-dml:"
                    + ",".join(
                        privilege
                        for privilege, enabled in zip(
                            ("select", "insert", "update", "delete", "truncate"),
                            privileges,
                            strict=True,
                        )
                        if enabled
                    )
                )
            if kind == "S":
                sequence_privileges = tuple(
                    bool(value)
                    for value in await connection.fetchrow(
                        "SELECT "
                        "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                        "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                        "AND has_sequence_privilege("
                        "reachable.oid, $2::oid, 'SELECT')), "
                        "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                        "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                        "AND has_sequence_privilege("
                        "reachable.oid, $2::oid, 'UPDATE')), "
                        "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                        "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                        "AND has_sequence_privilege("
                        "reachable.oid, $2::oid, 'USAGE'))",
                        role,
                        oid,
                    )
                )
                if any(sequence_privileges):
                    violations.append(
                        f"relation/{schema}.{name}/{role}/effective-sequence:"
                        + ",".join(
                            privilege
                            for privilege, enabled in zip(
                                ("select", "update", "usage"),
                                sequence_privileges,
                                strict=True,
                            )
                            if enabled
                        )
                    )
    return violations


async def _function_violations(connection: asyncpg.Connection[Any]) -> list[str]:
    violations: list[str] = []
    functions = await connection.fetch(
        "SELECT namespace_.nspname::text, proc.proname::text, proc.oid::bigint, "
        "owner.rolname::text, proc.prosecdef, "
        "COALESCE(array_to_string(proc.proconfig, ','), ''), "
        "EXISTS (SELECT 1 FROM aclexplode(COALESCE(proc.proacl, "
        "acldefault('f', proc.proowner))) acl "
        "WHERE acl.grantee = 0 AND acl.privilege_type = 'EXECUTE') "
        "FROM pg_catalog.pg_proc proc "
        "JOIN pg_catalog.pg_namespace namespace_ ON namespace_.oid = proc.pronamespace "
        "JOIN pg_catalog.pg_roles owner ON owner.oid = proc.proowner "
        "WHERE namespace_.nspname = ANY($1::text[]) "
        "ORDER BY namespace_.nspname, proc.proname, proc.oid",
        [*PRODUCT_SCHEMAS, "agentcow"],
    )
    reviewer_exec = 0
    for schema, name, oid, owner, security_definer, config, public_exec in functions:
        if owner != OWNER_ROLE:
            violations.append(f"function/{schema}.{name}/owner:{owner}")
        if public_exec:
            violations.append(f"function/{schema}.{name}/public-execute")
        for role in ROLE_NAMES[1:]:
            can_execute = await connection.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                "AND has_function_privilege(reachable.oid, $2::oid, 'EXECUTE'))",
                role,
                oid,
            )
            allowed = schema == "agentcow" and role in REVIEWER_ROLES
            if can_execute and not allowed:
                violations.append(f"function/{schema}.{name}/{role}/execute")
            if can_execute and allowed:
                reviewer_exec += 1
                if not security_definer or "search_path=pg_catalog" not in config:
                    violations.append(
                        f"function/{schema}.{name}/{role}/unsafe-security-definer"
                    )
    content_views = await connection.fetchval(
        "SELECT count(*) FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "WHERE namespace_.nspname = 'content' AND class_.relkind = 'v'"
    )
    if content_views and reviewer_exec == 0:
        violations.append("function/agentcow/slaif_reviewer/missing-controlled-surface")
    return violations


async def verify_database_privileges(
    connection: asyncpg.Connection[Any], *, expect_clean_content: bool = False
) -> PrivilegeValidation:
    """Verify effective roles, owners, schemas, relations, and functions."""

    violations = [
        *(await _role_violations(connection)),
        *(await _schema_violations(connection)),
        *(
            await _relation_violations(
                connection, expect_clean_content=expect_clean_content
            )
        ),
        *(await _function_violations(connection)),
    ]
    ordered = tuple(sorted(set(violations)))
    return PrivilegeValidation(safe=not ordered, violations=ordered)


__all__ = [
    "ALLOWED_CLEAN_RELATIONS",
    "PrivilegeValidation",
    "apply_product_privileges",
    "revoke_public_foundation_access",
    "verify_database_privileges",
]

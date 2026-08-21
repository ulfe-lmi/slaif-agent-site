"""Product-owned PostgreSQL privilege application and effective verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import asyncpg

from .readiness import ReadinessState
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
    ("control", "installation_state"),
    ("control", "platform_administrator"),
    ("control", "user_account"),
    ("control", "user_session"),
    ("control", "site"),
    ("control", "site_domain"),
    ("control", "site_policy"),
}
FOUNDATION_SCHEMA = "agentcow"
CONTROL_READINESS_FUNCTION = "slaif_control_readiness"
CONTROL_SETUP_STATUS_FUNCTION = "slaif_setup_status"
CONTROL_ROLE = "slaif_control"
PUBLIC_RESOLVER_FUNCTIONS = {
    ("slaif_site_resolve", "p_hostname text, p_path text"): "text, text",
    ("slaif_site_resolve_local", "p_site_key text"): "text",
}
CONTROL_FUNCTIONS = {
    (CONTROL_READINESS_FUNCTION, ""): "",
    (CONTROL_SETUP_STATUS_FUNCTION, ""): "",
    ("slaif_initial_setup_lock", ""): "",
    (
        "slaif_complete_initial_local_administrator",
        "p_expected_generation bigint, p_presented_digest bytea, "
        "p_user_account_id uuid, p_local_username text, "
        "p_local_username_normalized text, p_password_hash text, "
        "p_display_name text, p_email text",
    ): "bigint, bytea, uuid, text, text, text, text, text",
    (
        "slaif_inspect_human_session",
        "p_public_id text",
    ): "text",
    (
        "slaif_finalize_human_session",
        "p_public_id text, p_secret_digest bytea, p_idle_seconds integer, "
        "p_touch_interval_seconds integer, p_recent_auth_seconds integer",
    ): "text, bytea, integer, integer, integer",
    (
        "slaif_create_human_session",
        "p_session_id uuid, p_public_id text, p_secret_digest bytea, "
        "p_csrf_secret_digest bytea, p_user_account_id uuid, "
        "p_idle_seconds integer, p_absolute_seconds integer, "
        "p_recent_auth_seconds integer",
    ): "uuid, text, bytea, bytea, uuid, integer, integer, integer",
    (
        "slaif_finalize_state_changing_human_session",
        "p_public_id text, p_secret_digest bytea, "
        "p_csrf_secret_digest bytea, p_idle_seconds integer, "
        "p_touch_interval_seconds integer, p_recent_auth_seconds integer",
    ): "text, bytea, bytea, integer, integer, integer",
    (
        "slaif_revoke_human_session",
        "p_public_id text, p_secret_digest bytea, p_csrf_secret_digest bytea",
    ): "text, bytea, bytea",
    (
        "slaif_lookup_local_login",
        "p_local_username_normalized text",
    ): "text",
    (
        "slaif_compare_and_set_local_password_hash",
        "p_user_account_id uuid, p_expected_password_hash text, "
        "p_new_password_hash text",
    ): "uuid, text, text",
    (
        "slaif_site_create",
        "p_site_key text, p_display_name text, p_default_locale text, "
        "p_component_catalog_version text",
    ): "text, text, text, text",
    ("slaif_site_context", "p_site_id uuid"): "uuid",
    (
        "slaif_platform_administrator_authorized",
        "p_user_account_id uuid",
    ): "uuid",
    ("slaif_site_domain_list", "p_site_id uuid"): "uuid",
    ("slaif_site_get", "p_site_id uuid"): "uuid",
    ("slaif_site_list", ""): "",
    (
        "slaif_site_update",
        "p_site_id uuid, p_display_name text, p_default_locale text",
    ): "uuid, text, text",
    ("slaif_site_archive", "p_site_id uuid"): "uuid",
    (
        "slaif_site_domain_put",
        "p_site_id uuid, p_domain_id uuid, p_hostname text, "
        "p_path_prefix text, p_is_primary boolean",
    ): "uuid, uuid, text, text, boolean",
    (
        "slaif_site_domain_remove",
        "p_site_id uuid, p_domain_id uuid",
    ): "uuid, uuid",
    (
        "slaif_site_resolve",
        "p_hostname text, p_path text",
    ): "text, text",
    ("slaif_site_resolve_local", "p_site_key text"): "text",
}


@dataclass(frozen=True, slots=True)
class PrivilegeValidation:
    safe: bool
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContentObject:
    """One generic PostgreSQL object proving that `content` is not empty."""

    category: str
    identity: str


async def content_object_inventory(
    connection: asyncpg.Connection[Any],
) -> tuple[ContentObject, ...]:
    """Inventory schema-scoped objects without foundation-private knowledge."""

    rows = await connection.fetch(
        "SELECT category, identity FROM ("
        "SELECT 'relation:' || class_.relkind::text AS category, "
        "class_.relname::text AS identity "
        "FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'routine:' || proc.prokind::text, "
        "proc.proname::text || '(' || "
        "pg_catalog.pg_get_function_identity_arguments(proc.oid) || ')' "
        "FROM pg_catalog.pg_proc proc "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = proc.pronamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'type:' || type_.typtype::text, type_.typname::text "
        "FROM pg_catalog.pg_type type_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = type_.typnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'collation', collation_.collname::text "
        "FROM pg_catalog.pg_collation collation_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = collation_.collnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'conversion', conversion_.conname::text "
        "FROM pg_catalog.pg_conversion conversion_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = conversion_.connamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'operator', operator_.oprname::text "
        "FROM pg_catalog.pg_operator operator_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = operator_.oprnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'operator-class', class_.opcname::text "
        "FROM pg_catalog.pg_opclass class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.opcnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'operator-family', family_.opfname::text "
        "FROM pg_catalog.pg_opfamily family_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = family_.opfnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'statistics', statistics_.stxname::text "
        "FROM pg_catalog.pg_statistic_ext statistics_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = statistics_.stxnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'text-search-configuration', config_.cfgname::text "
        "FROM pg_catalog.pg_ts_config config_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = config_.cfgnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'text-search-dictionary', dictionary_.dictname::text "
        "FROM pg_catalog.pg_ts_dict dictionary_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = dictionary_.dictnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'text-search-parser', parser_.prsname::text "
        "FROM pg_catalog.pg_ts_parser parser_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = parser_.prsnamespace "
        "WHERE namespace_.nspname = 'content' "
        "UNION ALL "
        "SELECT 'text-search-template', template_.tmplname::text "
        "FROM pg_catalog.pg_ts_template template_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = template_.tmplnamespace "
        "WHERE namespace_.nspname = 'content'"
        ") inventory ORDER BY category, identity"
    )
    return tuple(ContentObject(row[0], row[1]) for row in rows)


async def foundation_object_inventory(
    connection: asyncpg.Connection[Any],
) -> tuple[ContentObject, ...]:
    """Inventory deployed foundation objects without naming private members."""

    rows = await connection.fetch(
        "SELECT category, identity FROM ("
        "SELECT 'relation:' || class_.relkind::text AS category, "
        "class_.relname::text AS identity "
        "FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "WHERE namespace_.nspname = 'agentcow' "
        "UNION ALL "
        "SELECT 'routine:' || proc.prokind::text, "
        "proc.proname::text || '(' || "
        "pg_catalog.pg_get_function_identity_arguments(proc.oid) || ')' "
        "FROM pg_catalog.pg_proc proc "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = proc.pronamespace "
        "WHERE namespace_.nspname = 'agentcow' "
        "UNION ALL "
        "SELECT 'type:' || type_.typtype::text, type_.typname::text "
        "FROM pg_catalog.pg_type type_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = type_.typnamespace "
        "WHERE namespace_.nspname = 'agentcow'"
        ") inventory ORDER BY category, identity"
    )
    return tuple(ContentObject(row[0], row[1]) for row in rows)


def content_inventory_fingerprint(inventory: tuple[ContentObject, ...]) -> str:
    """Hash a sorted generic inventory for later drift detection."""

    digest = hashlib.sha256()
    for item in inventory:
        digest.update(item.category.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.identity.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


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
    await connection.execute(
        "REVOKE ALL ON ALL SEQUENCES IN SCHEMA agentcow FROM PUBLIC"
    )


async def apply_product_privileges(
    connection: asyncpg.Connection[Any],
    *,
    readiness_state: ReadinessState,
) -> None:
    """Apply only grants that correspond to objects present in this baseline."""

    if readiness_state is ReadinessState.PENDING:
        raise ValueError("cannot apply ready privileges for a pending state")

    for schema in (*PRODUCT_SCHEMAS, "agentcow"):
        schema_identifier = quote_identifier(schema)
        await connection.execute(
            f"REVOKE ALL ON SCHEMA {schema_identifier} FROM PUBLIC"
        )
        await connection.execute(
            f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema_identifier} FROM PUBLIC"
        )
        await connection.execute(
            f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema_identifier} FROM PUBLIC"
        )
        await connection.execute(
            f"REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA {schema_identifier} FROM PUBLIC"
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

    denied_content_roles = (
        ROLE_NAMES[1:]
        if readiness_state is ReadinessState.EMPTY_SAFE
        else (*NO_CONTENT_ROLES, *READ_ROLES)
    )
    for role in denied_content_roles:
        role_identifier = quote_identifier(role)
        if readiness_state is ReadinessState.EMPTY_SAFE or role in NO_CONTENT_ROLES:
            await connection.execute(
                f'REVOKE ALL ON SCHEMA "content" FROM {role_identifier}'
            )
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
        await connection.execute(
            "REVOKE ALL ON ALL SEQUENCES IN SCHEMA agentcow "
            f"FROM {quote_identifier(role)}"
        )
    denied_foundation_roles = (
        ROLE_NAMES[1:]
        if readiness_state is ReadinessState.EMPTY_SAFE
        else (*RUNTIME_ROLES, *NO_CONTENT_ROLES, *READ_ROLES)
    )
    for role in denied_foundation_roles:
        if readiness_state is ReadinessState.EMPTY_SAFE or role not in REVIEWER_ROLES:
            await connection.execute(
                f"REVOKE ALL ON SCHEMA agentcow FROM {quote_identifier(role)}"
            )
        await connection.execute(
            "REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA agentcow "
            f"FROM {quote_identifier(role)}"
        )

    if readiness_state is ReadinessState.HARDENED:
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

    await connection.execute(
        f'GRANT USAGE ON SCHEMA "control" TO {quote_identifier(CONTROL_ROLE)}'
    )
    for (name, _identity), signature in CONTROL_FUNCTIONS.items():
        await connection.execute(
            "GRANT EXECUTE ON FUNCTION "
            f'"control".{quote_identifier(name)}({signature}) '
            f"TO {quote_identifier(CONTROL_ROLE)}"
        )
    await connection.execute('GRANT USAGE ON SCHEMA "control" TO "slaif_public_reader"')
    for (name, _identity), signature in PUBLIC_RESOLVER_FUNCTIONS.items():
        await connection.execute(
            "GRANT EXECUTE ON FUNCTION "
            f'"control".{quote_identifier(name)}({signature}) '
            'TO "slaif_public_reader"'
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


async def _schema_violations(
    connection: asyncpg.Connection[Any], *, readiness_state: ReadinessState
) -> list[str]:
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
        schema_state = by_name.get(schema)
        if schema_state is None:
            violations.append(f"schema/{schema}/missing")
            continue
        owner, public_access = schema_state
        if owner != OWNER_ROLE:
            violations.append(f"schema/{schema}/owner:{owner}")
        if public_access:
            violations.append(f"schema/{schema}/public-authority")
        for role in ROLE_NAMES[1:]:
            can_create, can_use = await connection.fetchrow(
                "SELECT "
                "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                "AND has_schema_privilege(reachable.oid, $2, 'CREATE')), "
                "EXISTS (SELECT 1 FROM pg_catalog.pg_roles reachable "
                "WHERE pg_has_role($1, reachable.rolname, 'MEMBER') "
                "AND has_schema_privilege(reachable.oid, $2, 'USAGE'))",
                role,
                schema,
            )
            if can_create:
                violations.append(f"schema/{schema}/{role}/create")
            expected_usage = (
                schema == "control" and role in {CONTROL_ROLE, "slaif_public_reader"}
            ) or (
                readiness_state is ReadinessState.HARDENED
                and (
                    (
                        schema == "content"
                        and role in (*RUNTIME_ROLES, *REVIEWER_ROLES, *READ_ROLES)
                    )
                    or (schema == FOUNDATION_SCHEMA and role in REVIEWER_ROLES)
                )
            )
            if bool(can_use) != expected_usage:
                usage_state = "missing-usage" if expected_usage else "usage"
                violations.append(f"schema/{schema}/{role}/{usage_state}")
    return violations


async def _relation_violations(
    connection: asyncpg.Connection[Any], *, readiness_state: ReadinessState
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
        if readiness_state is ReadinessState.EMPTY_SAFE and schema == "content":
            violations.append(f"relation/{schema}.{name}/unexpected-clean-object")
        if (
            readiness_state is ReadinessState.EMPTY_SAFE
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
            if (
                readiness_state is ReadinessState.HARDENED
                and schema == "content"
                and kind == "v"
            ):
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


async def _function_violations(
    connection: asyncpg.Connection[Any], *, readiness_state: ReadinessState
) -> list[str]:
    violations: list[str] = []
    functions = await connection.fetch(
        "SELECT namespace_.nspname::text, proc.proname::text, "
        "pg_catalog.pg_get_function_identity_arguments(proc.oid), proc.oid::bigint, "
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
    foundation_functions = 0
    control_function_counts = {identity: 0 for identity in CONTROL_FUNCTIONS}
    for (
        schema,
        name,
        arguments,
        oid,
        owner,
        security_definer,
        config,
        public_exec,
    ) in functions:
        control_identity = (name, arguments)
        is_control_function = (
            schema == "control" and control_identity in CONTROL_FUNCTIONS
        )
        if schema == FOUNDATION_SCHEMA:
            foundation_functions += 1
        elif is_control_function:
            control_function_counts[control_identity] += 1
            if not security_definer or "search_path=pg_catalog" not in config:
                violations.append(f"function/{schema}.{name}/unsafe-security-definer")
        elif readiness_state is ReadinessState.EMPTY_SAFE:
            violations.append(f"function/{schema}.{name}/unexpected-clean-object")
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
            public_resolver = (
                schema == "control"
                and (name, arguments) in PUBLIC_RESOLVER_FUNCTIONS
                and role == "slaif_public_reader"
            )
            allowed = (
                (is_control_function and role == CONTROL_ROLE)
                or public_resolver
                or (
                    readiness_state is ReadinessState.HARDENED
                    and schema == FOUNDATION_SCHEMA
                    and role in REVIEWER_ROLES
                )
            )
            if can_execute and not allowed:
                violations.append(f"function/{schema}.{name}/{role}/execute")
            if is_control_function and role == CONTROL_ROLE and not can_execute:
                violations.append(f"function/{schema}.{name}/{role}/missing-execute")
            if can_execute and allowed and schema == FOUNDATION_SCHEMA:
                reviewer_exec += 1
            if (
                can_execute
                and allowed
                and (not security_definer or "search_path=pg_catalog" not in config)
            ):
                violations.append(
                    f"function/{schema}.{name}/{role}/unsafe-security-definer"
                )
    content_views = await connection.fetchval(
        "SELECT count(*) FROM pg_catalog.pg_class class_ "
        "JOIN pg_catalog.pg_namespace namespace_ "
        "ON namespace_.oid = class_.relnamespace "
        "WHERE namespace_.nspname = 'content' AND class_.relkind = 'v'"
    )
    if foundation_functions == 0:
        violations.append("foundation/agentcow/functions/missing")
    for (name, arguments), count in control_function_counts.items():
        if count != 1:
            violations.append(f"function/control/{name}({arguments})/count:{count}")
    if (
        readiness_state is ReadinessState.HARDENED
        and content_views
        and reviewer_exec == 0
    ):
        violations.append("function/agentcow/slaif_reviewer/missing-controlled-surface")
    return violations


async def verify_database_privileges(
    connection: asyncpg.Connection[Any], *, readiness_state: ReadinessState
) -> PrivilegeValidation:
    """Verify effective roles, owners, schemas, relations, and functions."""

    if readiness_state is ReadinessState.PENDING:
        return PrivilegeValidation(
            safe=False, violations=("marker/readiness-state/pending",)
        )

    inventory_violations = []
    if readiness_state is ReadinessState.EMPTY_SAFE:
        inventory_violations = [
            f"content/object/{item.category}/{item.identity}/unexpected-empty-object"
            for item in await content_object_inventory(connection)
        ]
    elif not await content_object_inventory(connection):
        inventory_violations = ["content/object/missing-hardened-inventory"]
    violations = [
        *inventory_violations,
        *(await _role_violations(connection)),
        *(await _schema_violations(connection, readiness_state=readiness_state)),
        *(await _relation_violations(connection, readiness_state=readiness_state)),
        *(await _function_violations(connection, readiness_state=readiness_state)),
    ]
    ordered = tuple(sorted(set(violations)))
    return PrivilegeValidation(safe=not ordered, violations=ordered)


__all__ = [
    "ALLOWED_CLEAN_RELATIONS",
    "CONTROL_FUNCTIONS",
    "CONTROL_READINESS_FUNCTION",
    "ContentObject",
    "PrivilegeValidation",
    "apply_product_privileges",
    "content_inventory_fingerprint",
    "content_object_inventory",
    "foundation_object_inventory",
    "revoke_public_foundation_access",
    "verify_database_privileges",
]

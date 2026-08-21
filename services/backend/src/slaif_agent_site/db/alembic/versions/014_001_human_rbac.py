"""Add deterministic site-scoped human membership and built-in RBAC."""

# ruff: noqa: E501 -- SQL signatures and policy predicates stay inspectable.

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "014_001"
down_revision: str | Sequence[str] | None = "013_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

READ = """site:read content-model:read content-item:read collection-view:read
page:read composition:read navigation:read translation:read media:read theme:read
redirect:read component-catalog:read preview:inspect validation:read""".split()
L1 = """content-item:create content-item:write content-item:delete
translation:write media:upload media-metadata:write media-reference:delete
component-content-props:write seo:write preview:inspect""".split()
L2 = """page:create page:write page:delete page:restore page:move route:write
redirect:create redirect:write redirect:delete navigation:create navigation:write
navigation:delete collection-view:create collection-view:write collection-view:delete
component-structure:create component-structure:delete component-structure:move
relationship:write""".split()
L3 = """composition:write component-props:write component-variant:write layout:write
responsive-design:write page-style:write theme-tokens:write
preview:responsive-sweep""".split()
L4 = """content-model:create content-model:write content-model:delete
field-definition:create field-definition:write field-definition:delete
content-model:mapping site-structure:write global-region:create global-region:write
global-region:delete header-footer:write theme-global:write locale:configure
site-import:validate site-import:apply source:inspect site-reset:workspace""".split()
GOVERNANCE = """site-domain:manage workspace:create workspace:freeze
workspace:accept workspace:accept-selective workspace:discard capability:create
capability:revoke site:publish membership:manage role:manage workspace:read-all
site-policy:manage audit:read audit:export""".split()
INSTALLATION = """site:create site:archive site:delete identity:configure
installation:manage component-code:install server:configure secret:read
audit:delete""".split()
SYSTEM = """schema:migrate cow:deploy cow:harden cow:validate job:claim
browser:internal-preview browser:internal-source media:gc artifact:gc backup:run
restore:run""".split()

ROLES = (
    ("SITE_OWNER", "Site Owner", 4),
    ("SITE_ARCHITECT", "Site Architect", 4),
    ("SITE_DESIGNER", "Site Designer", 3),
    ("SITE_EDITOR", "Site Editor", 2),
    ("CONTENT_EDITOR", "Content Editor", 1),
    ("REVIEWER", "Reviewer", 0),
    ("VIEWER", "Viewer", 0),
)
EDITORIAL = {
    0: set(READ),
    1: set(READ + L1),
    2: set(READ + L1 + L2),
    3: set(READ + L1 + L2 + L3),
    4: set(READ + L1 + L2 + L3 + L4),
}
ROLE_DEFAULTS = {
    "SITE_OWNER": EDITORIAL[4] | set(GOVERNANCE),
    "SITE_ARCHITECT": EDITORIAL[4],
    "SITE_DESIGNER": EDITORIAL[3],
    "SITE_EDITOR": EDITORIAL[2],
    "CONTENT_EDITOR": EDITORIAL[1],
    "REVIEWER": EDITORIAL[0] | {"audit:read", "workspace:read-all"},
    "VIEWER": EDITORIAL[0],
}


def _values(rows: Sequence[tuple[object, ...]]) -> str:
    def literal(value: object) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, int):
            return str(value)
        return "'" + str(value).replace("'", "''") + "'"

    return ",\n".join("(" + ", ".join(map(literal, row)) + ")" for row in rows)


def _secure(functions: tuple[str, ...]) -> None:
    for function in functions:
        op.execute(f'ALTER FUNCTION "control".{function} OWNER TO "slaif_owner"')
        op.execute(f'REVOKE ALL ON FUNCTION "control".{function} FROM PUBLIC')
        op.execute(f'GRANT EXECUTE ON FUNCTION "control".{function} TO "slaif_control"')


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "control"."permission" (
            "permission_key" text PRIMARY KEY,
            "label" text NOT NULL,
            "description" text NOT NULL,
            "category" text NOT NULL,
            "agent_delegation_level" smallint,
            "site_assignable" boolean NOT NULL,
            "installation_only" boolean NOT NULL,
            "system_only" boolean NOT NULL,
            CONSTRAINT "permission_key_bounded" CHECK (
                char_length(permission_key) BETWEEN 3 AND 64
                AND permission_key ~ '^[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$'
            ),
            CONSTRAINT "permission_text_bounded" CHECK (
                char_length(label) BETWEEN 1 AND 96
                AND char_length(description) BETWEEN 1 AND 256
            ),
            CONSTRAINT "permission_category_exact" CHECK (
                category IN ('READ', 'L1_WRITE', 'L2_WRITE', 'L3_WRITE',
                    'L4_WRITE', 'HUMAN_ONLY', 'INSTALLATION_ONLY', 'SYSTEM_ONLY')
            ),
            CONSTRAINT "permission_delegation_bounded" CHECK (
                agent_delegation_level IS NULL
                OR agent_delegation_level BETWEEN 0 AND 4
            ),
            CONSTRAINT "permission_authority_separated" CHECK (
                NOT (installation_only AND system_only)
                AND (NOT installation_only OR NOT site_assignable)
                AND (NOT system_only OR NOT site_assignable)
                AND (agent_delegation_level IS NULL OR site_assignable)
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "control"."human_role" (
            "role_key" text PRIMARY KEY,
            "label" text NOT NULL,
            "description" text NOT NULL,
            "default_delegation_ceiling" smallint NOT NULL,
            "built_in" boolean NOT NULL DEFAULT TRUE,
            CONSTRAINT "human_role_key_bounded" CHECK (
                char_length(role_key) BETWEEN 3 AND 32
                AND role_key ~ '^[A-Z][A-Z0-9_]*$'
            ),
            CONSTRAINT "human_role_text_bounded" CHECK (
                char_length(label) BETWEEN 1 AND 96
                AND char_length(description) BETWEEN 1 AND 256
            ),
            CONSTRAINT "human_role_ceiling_bounded" CHECK (
                default_delegation_ceiling BETWEEN 0 AND 4
            ),
            CONSTRAINT "human_role_builtin_only" CHECK (built_in)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "control"."human_role_permission" (
            "role_key" text NOT NULL REFERENCES "control"."human_role"
                ("role_key") ON DELETE RESTRICT,
            "permission_key" text NOT NULL REFERENCES "control"."permission"
                ("permission_key") ON DELETE RESTRICT,
            PRIMARY KEY (role_key, permission_key)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "control"."site_membership" (
            "site_id" uuid NOT NULL REFERENCES "control"."site" ("id")
                ON DELETE RESTRICT,
            "user_account_id" uuid NOT NULL REFERENCES "control"."user_account"
                ("id") ON DELETE RESTRICT,
            "role_key" text NOT NULL REFERENCES "control"."human_role"
                ("role_key") ON DELETE RESTRICT,
            "delegation_ceiling" smallint NOT NULL,
            "status" text NOT NULL DEFAULT 'ACTIVE',
            "version" bigint NOT NULL DEFAULT 1,
            "created_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "site_membership_primary_key"
                PRIMARY KEY (site_id, user_account_id),
            CONSTRAINT "site_membership_parent_identity" UNIQUE
                (site_id, user_account_id),
            CONSTRAINT "site_membership_ceiling_bounded" CHECK
                (delegation_ceiling BETWEEN 0 AND 4),
            CONSTRAINT "site_membership_status_exact" CHECK
                (status IN ('ACTIVE', 'INACTIVE')),
            CONSTRAINT "site_membership_version_positive" CHECK (version >= 1)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "control"."site_membership_permission_override" (
            "site_id" uuid NOT NULL,
            "user_account_id" uuid NOT NULL,
            "permission_key" text NOT NULL REFERENCES "control"."permission"
                ("permission_key") ON DELETE RESTRICT,
            "effect" text NOT NULL,
            "created_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (site_id, user_account_id, permission_key),
            CONSTRAINT "membership_override_parent_fk" FOREIGN KEY
                (site_id, user_account_id) REFERENCES "control"."site_membership"
                (site_id, user_account_id) ON DELETE RESTRICT,
            CONSTRAINT "membership_override_effect_exact" CHECK
                (effect IN ('ALLOW', 'DENY'))
        )
        """
    )
    for table in (
        "permission",
        "human_role",
        "human_role_permission",
        "site_membership",
        "site_membership_permission_override",
    ):
        op.execute(f'ALTER TABLE "control"."{table}" OWNER TO "slaif_owner"')
        op.execute(f'REVOKE ALL ON TABLE "control"."{table}" FROM PUBLIC')

    permission_rows: dict[str, tuple[object, ...]] = {}
    for category, level, keys in (
        ("READ", 0, READ),
        ("L1_WRITE", 1, L1),
        ("L2_WRITE", 2, L2),
        ("L3_WRITE", 3, L3),
        ("L4_WRITE", 4, L4),
        ("HUMAN_ONLY", None, GOVERNANCE),
        ("INSTALLATION_ONLY", None, INSTALLATION),
        ("SYSTEM_ONLY", None, SYSTEM),
    ):
        for key in keys:
            permission_rows.setdefault(
                key,
                (
                    key,
                    key,
                    f"Built-in {category.lower()} authority.",
                    category,
                    level,
                    category not in {"INSTALLATION_ONLY", "SYSTEM_ONLY"},
                    category == "INSTALLATION_ONLY",
                    category == "SYSTEM_ONLY",
                ),
            )
    op.execute(
        'INSERT INTO "control"."permission" '
        "(permission_key, label, description, category, agent_delegation_level, "
        "site_assignable, installation_only, system_only) VALUES "
        + _values([permission_rows[key] for key in sorted(permission_rows)])
    )
    op.execute(
        'INSERT INTO "control"."human_role" '
        "(role_key, label, description, default_delegation_ceiling, built_in) VALUES "
        + _values(
            [
                (key, label, f"Built-in {label} role.", ceiling, True)
                for key, label, ceiling in ROLES
            ]
        )
    )
    role_permissions = [
        (role, permission)
        for role, permissions in ROLE_DEFAULTS.items()
        for permission in sorted(permissions)
    ]
    op.execute(
        'INSERT INTO "control"."human_role_permission" '
        "(role_key, permission_key) VALUES " + _values(role_permissions)
    )

    op.execute(
        """
        CREATE FUNCTION "control"."slaif_effective_human_membership"(
            "p_user_account_id" uuid, "p_site_id" uuid
        ) RETURNS TABLE (
            "user_account_id" uuid, "site_id" uuid, "role_key" text,
            "membership_version" bigint, "explicit_ceiling" smallint,
            "effective_ceiling" smallint, "effective_permissions" text[],
            "platform_administrator" boolean
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
            SELECT account.id, site.id, membership.role_key, membership.version,
                membership.delegation_ceiling,
                LEAST(membership.delegation_ceiling,
                    role.default_delegation_ceiling)::smallint,
                ARRAY(
                    SELECT permission_key FROM (
                        SELECT defaults.permission_key
                        FROM "control"."human_role_permission" AS defaults
                        WHERE defaults.role_key = membership.role_key
                        UNION
                        SELECT override_.permission_key
                        FROM "control"."site_membership_permission_override" AS override_
                        JOIN "control"."permission" AS permission
                          ON permission.permission_key = override_.permission_key
                        WHERE override_.site_id = membership.site_id
                          AND override_.user_account_id = membership.user_account_id
                          AND override_.effect = 'ALLOW'
                          AND permission.site_assignable
                    ) allowed
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM "control"."site_membership_permission_override" AS denied
                        WHERE denied.site_id = membership.site_id
                          AND denied.user_account_id = membership.user_account_id
                          AND denied.permission_key = allowed.permission_key
                          AND denied.effect = 'DENY'
                    ) ORDER BY permission_key COLLATE "C"
                ),
                EXISTS (
                    SELECT 1 FROM "control"."platform_administrator" AS admin
                    WHERE admin.user_account_id = account.id
                )
            FROM "control"."site_membership" AS membership
            JOIN "control"."user_account" AS account
              ON account.id = membership.user_account_id
            JOIN "control"."site" AS site ON site.id = membership.site_id
            JOIN "control"."human_role" AS role
              ON role.role_key = membership.role_key
            WHERE membership.user_account_id = p_user_account_id
              AND membership.site_id = p_site_id
              AND membership.status = 'ACTIVE'
              AND account.status = 'ACTIVE' AND site.status = 'ACTIVE'
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_human_authorize"(
            "p_user_account_id" uuid, "p_site_id" uuid,
            "p_permission_key" text, "p_expected_membership_version" bigint
        ) RETURNS TABLE (
            "user_account_id" uuid, "site_id" uuid, "role_key" text,
            "membership_version" bigint, "explicit_ceiling" smallint,
            "effective_ceiling" smallint, "effective_permissions" text[],
            "platform_administrator" boolean
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
            SELECT context.*
            FROM "control"."slaif_effective_human_membership"(
                p_user_account_id, p_site_id
            ) AS context
            WHERE context.membership_version = p_expected_membership_version
              AND p_permission_key = ANY(context.effective_permissions)
              AND EXISTS (
                  SELECT 1 FROM "control"."permission" AS permission
                  WHERE permission.permission_key = p_permission_key
                    AND permission.site_assignable
              )
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_human_rbac_catalog"()
        RETURNS TABLE (
            "permission_key" text, "category" text,
            "agent_delegation_level" smallint, "site_assignable" boolean,
            "installation_only" boolean, "system_only" boolean,
            "role_keys" text[]
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog AS $function$
            SELECT permission.permission_key, permission.category,
                permission.agent_delegation_level, permission.site_assignable,
                permission.installation_only, permission.system_only,
                ARRAY(
                    SELECT role_permission.role_key
                    FROM "control"."human_role_permission" AS role_permission
                    WHERE role_permission.permission_key = permission.permission_key
                    ORDER BY role_permission.role_key COLLATE "C"
                )
            FROM "control"."permission" AS permission
            ORDER BY permission.permission_key COLLATE "C"
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_membership_get"(
            "p_site_id" uuid, "p_user_account_id" uuid
        ) RETURNS TABLE (
            "site_id" uuid, "user_account_id" uuid, "role_key" text,
            "delegation_ceiling" smallint, "status" text, "version" bigint,
            "allow_permissions" text[], "deny_permissions" text[],
            "effective_ceiling" smallint, "effective_permissions" text[],
            "platform_administrator" boolean,
            "created_at" timestamp with time zone,
            "updated_at" timestamp with time zone
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
            SELECT membership.site_id, membership.user_account_id,
                membership.role_key, membership.delegation_ceiling,
                membership.status, membership.version,
                ARRAY(SELECT permission_key FROM
                    "control"."site_membership_permission_override" AS override_
                    WHERE override_.site_id = membership.site_id
                      AND override_.user_account_id = membership.user_account_id
                      AND override_.effect = 'ALLOW'
                    ORDER BY permission_key COLLATE "C"),
                ARRAY(SELECT permission_key FROM
                    "control"."site_membership_permission_override" AS override_
                    WHERE override_.site_id = membership.site_id
                      AND override_.user_account_id = membership.user_account_id
                      AND override_.effect = 'DENY'
                    ORDER BY permission_key COLLATE "C"),
                COALESCE(context.effective_ceiling,
                    LEAST(membership.delegation_ceiling,
                        role.default_delegation_ceiling)::smallint),
                COALESCE(context.effective_permissions, ARRAY[]::text[]),
                EXISTS (
                    SELECT 1 FROM "control"."platform_administrator" AS admin
                    WHERE admin.user_account_id = membership.user_account_id
                ),
                membership.created_at, membership.updated_at
            FROM "control"."site_membership" AS membership
            JOIN "control"."human_role" AS role
              ON role.role_key = membership.role_key
            LEFT JOIN LATERAL "control"."slaif_effective_human_membership"(
                membership.user_account_id, membership.site_id
            ) AS context ON TRUE
            WHERE membership.site_id = p_site_id
              AND membership.user_account_id = p_user_account_id
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_membership_list"("p_site_id" uuid)
        RETURNS TABLE (
            "site_id" uuid, "user_account_id" uuid, "role_key" text,
            "delegation_ceiling" smallint, "status" text, "version" bigint,
            "allow_permissions" text[], "deny_permissions" text[],
            "effective_ceiling" smallint, "effective_permissions" text[],
            "platform_administrator" boolean,
            "created_at" timestamp with time zone,
            "updated_at" timestamp with time zone
        )
        LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog AS $function$
            SELECT result.* FROM "control"."site_membership" AS membership
            CROSS JOIN LATERAL "control"."slaif_membership_get"(
                membership.site_id, membership.user_account_id
            ) AS result
            WHERE membership.site_id = p_site_id
            ORDER BY result.user_account_id
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_membership_put"(
            "p_actor_user_id" uuid, "p_site_id" uuid,
            "p_target_user_id" uuid, "p_role_key" text,
            "p_delegation_ceiling" smallint, "p_status" text,
            "p_expected_version" bigint, "p_overrides" text[]
        ) RETURNS TABLE (
            "user_account_id" uuid, "site_id" uuid, "role_key" text,
            "membership_version" bigint, "explicit_ceiling" smallint,
            "effective_ceiling" smallint, "effective_permissions" text[],
            "platform_administrator" boolean
        ) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
        #variable_conflict use_column
        DECLARE
            actor_admin boolean; actor_context record; target_role record;
            actor_status text; target_status text; target_admin boolean;
            current_ record; item text; effect_ text; permission_ text;
            target_permissions text[];
        BEGIN
            -- Canonical lock order: active site; both user rows ordered by UUID;
            -- administrator assignments; both site memberships; then overrides.
            -- The site lock serializes membership_put calls for this site while
            -- the row locks also serialize owner-driven account/authority edits.
            PERFORM 1 FROM "control"."site" AS site
                WHERE site.id = p_site_id AND site.status = 'ACTIVE' FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'RBAC_NOT_FOUND' USING ERRCODE='P0001'; END IF;

            PERFORM 1 FROM "control"."user_account" AS account
                WHERE account.id = ANY(ARRAY[p_actor_user_id, p_target_user_id])
                ORDER BY account.id FOR UPDATE;
            SELECT account.status INTO actor_status
                FROM "control"."user_account" AS account
                WHERE account.id = p_actor_user_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'RBAC_NOT_FOUND' USING ERRCODE='P0001'; END IF;
            SELECT account.status INTO target_status
                FROM "control"."user_account" AS account
                WHERE account.id = p_target_user_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'RBAC_NOT_FOUND' USING ERRCODE='P0001'; END IF;

            PERFORM 1 FROM "control"."platform_administrator" AS admin
                WHERE admin.user_account_id = ANY(
                    ARRAY[p_actor_user_id, p_target_user_id]
                ) ORDER BY admin.user_account_id FOR UPDATE;
            SELECT EXISTS (
                SELECT 1 FROM "control"."platform_administrator" AS admin
                WHERE admin.user_account_id = p_actor_user_id
            ) AND actor_status = 'ACTIVE' INTO actor_admin;
            SELECT EXISTS (
                SELECT 1 FROM "control"."platform_administrator" AS admin
                WHERE admin.user_account_id = p_target_user_id
            ) INTO target_admin;

            PERFORM 1 FROM "control"."site_membership" AS membership
                WHERE membership.site_id = p_site_id
                  AND membership.user_account_id = ANY(
                      ARRAY[p_actor_user_id, p_target_user_id]
                  ) ORDER BY membership.user_account_id FOR UPDATE;
            PERFORM 1
                FROM "control"."site_membership_permission_override" AS override_
                WHERE override_.site_id = p_site_id
                  AND override_.user_account_id = ANY(
                      ARRAY[p_actor_user_id, p_target_user_id]
                  )
                ORDER BY override_.user_account_id, override_.permission_key
                FOR UPDATE;

            IF actor_status <> 'ACTIVE' THEN
                RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
            END IF;
            IF NOT actor_admin THEN
                IF p_actor_user_id = p_target_user_id THEN
                    RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
                END IF;
                SELECT * INTO actor_context
                FROM "control"."slaif_effective_human_membership"(
                    p_actor_user_id, p_site_id
                );
                IF NOT FOUND OR NOT ('membership:manage' = ANY(actor_context.effective_permissions))
                    OR NOT ('role:manage' = ANY(actor_context.effective_permissions)) THEN
                    RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
                END IF;
            END IF;
            SELECT * INTO target_role FROM "control"."human_role" AS role
                WHERE role.role_key = p_role_key AND role.built_in;
            IF NOT FOUND OR p_delegation_ceiling < 0
                OR p_delegation_ceiling > target_role.default_delegation_ceiling
                OR p_status NOT IN ('ACTIVE', 'INACTIVE') THEN
                RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
            END IF;
            IF p_status = 'ACTIVE' AND target_status <> 'ACTIVE' THEN
                RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
            END IF;
            IF NOT actor_admin THEN
                IF p_delegation_ceiling > actor_context.effective_ceiling THEN
                    RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
                END IF;
            END IF;
            SELECT * INTO current_ FROM "control"."site_membership" AS membership
                WHERE membership.site_id = p_site_id
                  AND membership.user_account_id = p_target_user_id;
            IF NOT FOUND THEN
                IF p_expected_version IS NOT NULL THEN
                    RAISE EXCEPTION 'RBAC_CONFLICT' USING ERRCODE='P0001';
                END IF;
            ELSIF p_expected_version IS NULL OR current_.version <> p_expected_version THEN
                RAISE EXCEPTION 'RBAC_CONFLICT' USING ERRCODE='P0001';
            END IF;
            SELECT ARRAY(
                SELECT role_permission.permission_key
                FROM "control"."human_role_permission" AS role_permission
                WHERE role_permission.role_key = p_role_key
                ORDER BY role_permission.permission_key COLLATE "C"
            ) INTO target_permissions;
            FOREACH item IN ARRAY COALESCE(p_overrides, ARRAY[]::text[]) LOOP
                effect_ := split_part(item, ':', 1);
                permission_ := substring(item FROM position(':' IN item) + 1);
                IF effect_ NOT IN ('ALLOW', 'DENY') OR NOT EXISTS (
                    SELECT 1 FROM "control"."permission" AS permission
                    WHERE permission.permission_key = permission_
                      AND permission.site_assignable
                ) THEN RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001'; END IF;
                IF effect_ = 'ALLOW' AND NOT (permission_ = ANY(target_permissions)) THEN
                    target_permissions := array_append(target_permissions, permission_);
                ELSIF effect_ = 'DENY' THEN
                    target_permissions := array_remove(target_permissions, permission_);
                END IF;
            END LOOP;
            IF NOT actor_admin THEN
                IF NOT target_permissions <@ actor_context.effective_permissions THEN
                    RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
                END IF;
                IF 'site:publish' = ANY(target_permissions)
                    AND NOT ('site:publish' = ANY(actor_context.effective_permissions)) THEN
                    RAISE EXCEPTION 'RBAC_DENIED' USING ERRCODE='P0001';
                END IF;
            END IF;
            INSERT INTO "control"."site_membership" AS membership (
                site_id, user_account_id, role_key, delegation_ceiling, status
            ) VALUES (
                p_site_id, p_target_user_id, p_role_key,
                p_delegation_ceiling, p_status
            ) ON CONFLICT ON CONSTRAINT site_membership_primary_key DO UPDATE SET
                role_key = EXCLUDED.role_key,
                delegation_ceiling = EXCLUDED.delegation_ceiling,
                status = EXCLUDED.status,
                version = membership.version + 1,
                updated_at = CURRENT_TIMESTAMP;
            DELETE FROM "control"."site_membership_permission_override" AS override_
                WHERE override_.site_id = p_site_id
                  AND override_.user_account_id = p_target_user_id;
            FOREACH item IN ARRAY COALESCE(p_overrides, ARRAY[]::text[]) LOOP
                effect_ := split_part(item, ':', 1);
                permission_ := substring(item FROM position(':' IN item) + 1);
                INSERT INTO "control"."site_membership_permission_override" (
                    site_id, user_account_id, permission_key, effect
                ) VALUES (p_site_id, p_target_user_id, permission_, effect_);
            END LOOP;
            IF p_status = 'INACTIVE' THEN
                RETURN QUERY SELECT p_target_user_id, p_site_id, p_role_key,
                    membership.version, p_delegation_ceiling,
                    LEAST(p_delegation_ceiling,
                        target_role.default_delegation_ceiling)::smallint,
                    ARRAY[]::text[], target_admin
                    FROM "control"."site_membership" AS membership
                    WHERE membership.site_id = p_site_id
                      AND membership.user_account_id = p_target_user_id;
            ELSE
                RETURN QUERY SELECT *
                FROM "control"."slaif_effective_human_membership"(
                    p_target_user_id, p_site_id
                );
            END IF;
        END $function$
        """
    )
    _secure(
        (
            '"slaif_effective_human_membership"(uuid, uuid)',
            '"slaif_human_authorize"(uuid, uuid, text, bigint)',
            '"slaif_human_rbac_catalog"()',
            '"slaif_membership_get"(uuid, uuid)',
            '"slaif_membership_list"(uuid)',
            '"slaif_membership_put"(uuid, uuid, uuid, text, smallint, text, bigint, text[])',
        )
    )


def downgrade() -> None:
    for function in (
        '"slaif_membership_put"(uuid, uuid, uuid, text, smallint, text, bigint, text[])',
        '"slaif_membership_list"(uuid)',
        '"slaif_membership_get"(uuid, uuid)',
        '"slaif_human_rbac_catalog"()',
        '"slaif_human_authorize"(uuid, uuid, text, bigint)',
        '"slaif_effective_human_membership"(uuid, uuid)',
    ):
        op.execute(f'DROP FUNCTION "control".{function}')
    op.execute('DROP TABLE "control"."site_membership_permission_override"')
    op.execute('DROP TABLE "control"."site_membership"')
    op.execute('DROP TABLE "control"."human_role_permission"')
    op.execute('DROP TABLE "control"."human_role"')
    op.execute('DROP TABLE "control"."permission"')

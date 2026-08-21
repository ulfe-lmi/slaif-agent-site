"""Add current-human site and authority read models."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "015_001"
down_revision: str | Sequence[str] | None = "014_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FUNCTIONS = (
    '"control"."slaif_current_human_sites"(uuid)',
    '"control"."slaif_current_human_authority"(uuid, uuid)',
)


def _secure() -> None:
    for function in _FUNCTIONS:
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_control")


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_current_human_sites"(
            "p_user_account_id" uuid
        ) RETURNS TABLE (
            "site_id" uuid, "site_key" text, "display_name" text,
            "status" text, "default_locale" text,
            "canonical_revision" bigint, "role_key" text,
            "membership_version" bigint, "explicit_ceiling" smallint,
            "effective_ceiling" smallint, "platform_administrator" boolean
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog AS $function$
            WITH actor AS (
                SELECT account.id,
                    EXISTS (
                        SELECT 1 FROM "control"."platform_administrator" admin
                        WHERE admin.user_account_id = account.id
                    ) AS global_admin
                FROM "control"."user_account" account
                WHERE account.id = p_user_account_id
                  AND account.status = 'ACTIVE'
            )
            SELECT site.id, site.site_key, site.display_name, site.status,
                site.default_locale, site.canonical_revision,
                CASE WHEN actor.global_admin THEN NULL ELSE membership.role_key END,
                CASE WHEN actor.global_admin THEN NULL ELSE membership.version END,
                CASE WHEN actor.global_admin THEN NULL
                    ELSE membership.delegation_ceiling END,
                CASE WHEN actor.global_admin THEN NULL
                    ELSE LEAST(membership.delegation_ceiling,
                        role.default_delegation_ceiling)::smallint END,
                actor.global_admin
            FROM actor
            JOIN "control"."site" site ON (
                actor.global_admin OR site.status = 'ACTIVE'
            )
            LEFT JOIN "control"."site_membership" membership
              ON membership.site_id = site.id
             AND membership.user_account_id = actor.id
             AND membership.status = 'ACTIVE'
             AND NOT actor.global_admin
            LEFT JOIN "control"."human_role" role
              ON role.role_key = membership.role_key
            WHERE actor.global_admin OR membership.user_account_id IS NOT NULL
            ORDER BY site.site_key COLLATE "C", site.id
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_current_human_authority"(
            "p_user_account_id" uuid, "p_site_id" uuid
        ) RETURNS TABLE (
            "site_id" uuid, "site_key" text, "display_name" text,
            "status" text, "default_locale" text,
            "canonical_revision" bigint, "role_key" text,
            "membership_version" bigint, "explicit_ceiling" smallint,
            "effective_ceiling" smallint, "effective_permissions" text[],
            "platform_administrator" boolean
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
            WITH actor AS (
                SELECT account.id,
                    EXISTS (
                        SELECT 1 FROM "control"."platform_administrator" admin
                        WHERE admin.user_account_id = account.id
                    ) AS global_admin
                FROM "control"."user_account" account
                WHERE account.id = p_user_account_id
                  AND account.status = 'ACTIVE'
            )
            SELECT site.id, site.site_key, site.display_name, site.status,
                site.default_locale, site.canonical_revision,
                CASE WHEN actor.global_admin THEN NULL ELSE membership.role_key END,
                CASE WHEN actor.global_admin THEN NULL ELSE membership.version END,
                CASE WHEN actor.global_admin THEN NULL
                    ELSE membership.delegation_ceiling END,
                CASE WHEN actor.global_admin THEN NULL
                    ELSE context.effective_ceiling END,
                CASE WHEN actor.global_admin THEN ARRAY[]::text[]
                    ELSE context.effective_permissions END,
                actor.global_admin
            FROM actor
            JOIN "control"."site" site ON site.id = p_site_id
            LEFT JOIN "control"."site_membership" membership
              ON membership.site_id = site.id
             AND membership.user_account_id = actor.id
             AND membership.status = 'ACTIVE'
             AND site.status = 'ACTIVE'
             AND NOT actor.global_admin
            LEFT JOIN "control"."slaif_effective_human_membership"(
                p_user_account_id, p_site_id
            ) context ON NOT actor.global_admin
            WHERE actor.global_admin OR context.user_account_id IS NOT NULL
        $function$
        """
    )
    _secure()


def downgrade() -> None:
    for function in reversed(_FUNCTIONS):
        op.execute(f"DROP FUNCTION {function}")

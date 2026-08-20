"""Add Control-only local credential lookup and compare-and-set rehash."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "011_001"
down_revision: str | Sequence[str] | None = "010_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HASH_SHAPE = (
    r"^\\$argon2id\\$v=19\\$m=65536,t=3,p=4\\$"
    r"[A-Za-z0-9+/]{22}\\$[A-Za-z0-9+/]{43}$"
)


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_lookup_local_login"(
            "p_local_username_normalized" text
        )
        RETURNS TABLE (
            "user_account_id" uuid,
            "local_username_normalized" text,
            "password_hash" text,
            "status" text
        )
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        PARALLEL SAFE
        SET search_path = pg_catalog
        ROWS 1
        AS $function$
            SELECT account.id, account.local_username_normalized,
                   account.password_hash, account.status
            FROM "control"."user_account" AS account
            WHERE p_local_username_normalized IS NOT NULL
              AND p_local_username_normalized ~ '^[a-z][a-z0-9._-]{2,62}$'
              AND account.identity_kind = 'LOCAL'
              AND account.local_username_normalized = p_local_username_normalized
        $function$
        """
    )
    op.execute(
        f"""
        CREATE FUNCTION "control"."slaif_compare_and_set_local_password_hash"(
            "p_user_account_id" uuid,
            "p_expected_password_hash" text,
            "p_new_password_hash" text
        )
        RETURNS boolean
        LANGUAGE sql
        VOLATILE
        SECURITY DEFINER
        PARALLEL UNSAFE
        SET search_path = pg_catalog
        AS $function$
            UPDATE "control"."user_account" AS account
            SET "password_hash" = p_new_password_hash,
                "updated_at" = CURRENT_TIMESTAMP
            WHERE p_user_account_id IS NOT NULL
              AND p_expected_password_hash ~ '{_HASH_SHAPE}'
              AND p_new_password_hash ~ '{_HASH_SHAPE}'
              AND account.id = p_user_account_id
              AND account.identity_kind = 'LOCAL'
              AND account.status = 'ACTIVE'
              AND account.password_hash = p_expected_password_hash
            RETURNING TRUE
        $function$
        """
    )
    for function in (
        '"control"."slaif_lookup_local_login"(text)',
        '"control"."slaif_compare_and_set_local_password_hash"(uuid, text, text)',
    ):
        op.execute(f'ALTER FUNCTION {function} OWNER TO "slaif_owner"')
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f'GRANT EXECUTE ON FUNCTION {function} TO "slaif_control"')


def downgrade() -> None:
    op.execute(
        'DROP FUNCTION "control"."slaif_compare_and_set_local_password_hash"('
        "uuid, text, text)"
    )
    op.execute('DROP FUNCTION "control"."slaif_lookup_local_login"(text)')

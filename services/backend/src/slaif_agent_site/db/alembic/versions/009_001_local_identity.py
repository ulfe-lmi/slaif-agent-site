"""Add local identity and atomic initial-administrator setup.

Revision ID: 009_001
Revises: 008_001
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "009_001"
down_revision: str | Sequence[str] | None = "008_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "control"."user_account" (
            "id" uuid PRIMARY KEY,
            "identity_kind" text NOT NULL,
            "local_username" text,
            "local_username_normalized" text,
            "password_hash" text,
            "oidc_issuer" text,
            "oidc_subject" text,
            "email" text,
            "display_name" text NOT NULL,
            "status" text NOT NULL DEFAULT 'ACTIVE',
            "created_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "user_account_identity_kind"
                CHECK (identity_kind IN ('LOCAL', 'OIDC')),
            CONSTRAINT "user_account_status"
                CHECK (status IN ('ACTIVE', 'DISABLED')),
            CONSTRAINT "user_account_display_name"
                CHECK (
                    char_length(display_name) BETWEEN 1 AND 128
                ),
            CONSTRAINT "user_account_email"
                CHECK (
                    email IS NULL OR (
                        char_length(email) BETWEEN 3 AND 254
                    )
                ),
            CONSTRAINT "user_account_identity_shape"
                CHECK (
                    (
                        identity_kind = 'LOCAL'
                        AND local_username IS NOT NULL
                        AND local_username_normalized IS NOT NULL
                        AND password_hash IS NOT NULL
                        AND oidc_issuer IS NULL
                        AND oidc_subject IS NULL
                    ) OR (
                        identity_kind = 'OIDC'
                        AND local_username IS NULL
                        AND local_username_normalized IS NULL
                        AND password_hash IS NULL
                        AND oidc_issuer IS NOT NULL
                        AND oidc_subject IS NOT NULL
                    )
                ),
            CONSTRAINT "user_account_local_username_shape"
                CHECK (
                    local_username IS NULL OR (
                        local_username ~ '^[A-Za-z][A-Za-z0-9._-]{2,62}$'
                        AND local_username_normalized ~
                            '^[a-z][a-z0-9._-]{2,62}$'
                        AND local_username_normalized =
                            pg_catalog.lower(local_username)
                    )
                ),
            CONSTRAINT "user_account_password_hash_shape"
                CHECK (
                    password_hash IS NULL OR password_hash ~
                    '^\\$argon2id\\$v=19\\$m=65536,t=3,p=4\\$'
                    '[A-Za-z0-9+/]{22}\\$[A-Za-z0-9+/]{43}$'
                ),
            CONSTRAINT "user_account_oidc_shape"
                CHECK (
                    oidc_issuer IS NULL OR (
                        char_length(oidc_issuer) BETWEEN 1 AND 2048
                        AND char_length(oidc_subject) BETWEEN 1 AND 255
                    )
                ),
            CONSTRAINT "user_account_local_username_unique"
                UNIQUE (local_username_normalized),
            CONSTRAINT "user_account_oidc_identity_unique"
                UNIQUE (oidc_issuer, oidc_subject)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "control"."platform_administrator" (
            "user_account_id" uuid PRIMARY KEY
                REFERENCES "control"."user_account" ("id")
                ON DELETE RESTRICT,
            "assigned_at" timestamp with time zone NOT NULL
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    for table in ("user_account", "platform_administrator"):
        op.execute(f'ALTER TABLE "control"."{table}" OWNER TO "slaif_owner"')
        op.execute(f'REVOKE ALL ON TABLE "control"."{table}" FROM PUBLIC')

    op.execute(
        """
        CREATE FUNCTION "control"."slaif_initial_setup_lock"()
        RETURNS TABLE (
            "initialized" boolean,
            "setup_token_expires_at" timestamp with time zone,
            "setup_token_generation" bigint,
            "setup_token_digest" bytea
        )
        LANGUAGE sql
        VOLATILE
        SECURITY DEFINER
        PARALLEL UNSAFE
        SET search_path = pg_catalog
        ROWS 1
        AS $function$
            SELECT state.initialized_at IS NOT NULL,
                   state.setup_token_expires_at,
                   state.setup_token_generation,
                   state.setup_token_digest
            FROM "control"."installation_state" AS state
            WHERE state.singleton
            FOR UPDATE
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_complete_initial_local_administrator"(
            "p_expected_generation" bigint,
            "p_presented_digest" bytea,
            "p_user_account_id" uuid,
            "p_local_username" text,
            "p_local_username_normalized" text,
            "p_password_hash" text,
            "p_display_name" text,
            "p_email" text
        )
        RETURNS TABLE (
            "user_account_id" uuid,
            "local_username" text,
            "display_name" text,
            "email" text,
            "status" text,
            "created_at" timestamp with time zone
        )
        LANGUAGE plpgsql
        VOLATILE
        SECURITY DEFINER
        PARALLEL UNSAFE
        SET search_path = pg_catalog
        ROWS 1
        AS $function$
        DECLARE
            installation "control"."installation_state"%ROWTYPE;
            created timestamp with time zone;
        BEGIN
            SELECT * INTO STRICT installation
            FROM "control"."installation_state"
            WHERE singleton
            FOR UPDATE;

            IF installation.initialized_at IS NOT NULL
               OR installation.setup_token_digest IS NULL
               OR installation.setup_token_expires_at <= CURRENT_TIMESTAMP
               OR installation.setup_token_generation <> p_expected_generation
               OR installation.setup_token_digest <> p_presented_digest THEN
                RAISE EXCEPTION USING
                    ERRCODE = 'P0001', MESSAGE = 'initial setup failed';
            END IF;

            INSERT INTO "control"."user_account" AS account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, email, status
            ) VALUES (
                p_user_account_id, 'LOCAL', p_local_username,
                p_local_username_normalized, p_password_hash, p_display_name,
                p_email, 'ACTIVE'
            ) RETURNING account.created_at INTO created;

            INSERT INTO "control"."platform_administrator" (user_account_id)
            VALUES (p_user_account_id);

            UPDATE "control"."installation_state" SET
                initialized_at = CURRENT_TIMESTAMP,
                setup_token_digest = NULL,
                setup_token_issued_at = NULL,
                setup_token_expires_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE singleton;

            RETURN QUERY SELECT p_user_account_id, p_local_username,
                p_display_name, p_email, 'ACTIVE'::text, created;
        END
        $function$
        """
    )
    for function in (
        '"control"."slaif_initial_setup_lock"()',
        '"control"."slaif_complete_initial_local_administrator"('
        "bigint, bytea, uuid, text, text, text, text, text)",
    ):
        op.execute(f'ALTER FUNCTION {function} OWNER TO "slaif_owner"')
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f'GRANT EXECUTE ON FUNCTION {function} TO "slaif_control"')


def downgrade() -> None:
    op.execute(
        'DROP FUNCTION "control"."slaif_complete_initial_local_administrator"('
        "bigint, bytea, uuid, text, text, text, text, text)"
    )
    op.execute('DROP FUNCTION "control"."slaif_initial_setup_lock"()')
    op.execute('DROP TABLE "control"."platform_administrator"')
    op.execute('DROP TABLE "control"."user_account"')

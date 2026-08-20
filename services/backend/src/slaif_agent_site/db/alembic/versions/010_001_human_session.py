"""Add opaque human sessions and Control-only lifecycle functions.

Revision ID: 010_001
Revises: 009_001
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "010_001"
down_revision: str | Sequence[str] | None = "009_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "control"."user_session" (
            "id" uuid PRIMARY KEY,
            "public_id" text NOT NULL,
            "secret_digest" bytea NOT NULL,
            "csrf_secret_digest" bytea NOT NULL,
            "user_account_id" uuid NOT NULL
                REFERENCES "control"."user_account" ("id") ON DELETE RESTRICT,
            "created_at" timestamp with time zone NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            "last_seen_at" timestamp with time zone NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            "absolute_expires_at" timestamp with time zone NOT NULL,
            "recent_auth_at" timestamp with time zone NOT NULL
                DEFAULT CURRENT_TIMESTAMP,
            "revoked_at" timestamp with time zone,
            CONSTRAINT "user_session_public_id_unique" UNIQUE ("public_id"),
            CONSTRAINT "user_session_secret_digest_unique" UNIQUE ("secret_digest"),
            CONSTRAINT "user_session_csrf_digest_unique"
                UNIQUE ("csrf_secret_digest"),
            CONSTRAINT "user_session_public_id_shape" CHECK (
                "public_id" ~ '^sas2_[0-9a-f]{32}$'
            ),
            CONSTRAINT "user_session_secret_digest_shape" CHECK (
                pg_catalog.octet_length("secret_digest") = 32
            ),
            CONSTRAINT "user_session_csrf_digest_shape" CHECK (
                pg_catalog.octet_length("csrf_secret_digest") = 32
            ),
            CONSTRAINT "user_session_time_order" CHECK (
                "created_at" <= "last_seen_at"
                AND "created_at" <= "recent_auth_at"
                AND "last_seen_at" <= "absolute_expires_at"
                AND "recent_auth_at" <= "absolute_expires_at"
                AND ("revoked_at" IS NULL OR "revoked_at" >= "created_at")
            )
        )
        """
    )
    op.execute(
        'CREATE INDEX "user_session_user_account_idx" '
        'ON "control"."user_session" ("user_account_id")'
    )
    op.execute(
        'CREATE INDEX "user_session_expiry_idx" '
        'ON "control"."user_session" ("absolute_expires_at")'
    )
    op.execute('ALTER TABLE "control"."user_session" OWNER TO "slaif_owner"')
    op.execute('REVOKE ALL ON TABLE "control"."user_session" FROM PUBLIC')

    op.execute(
        """
        CREATE FUNCTION "control"."slaif_create_human_session"(
            "p_session_id" uuid,
            "p_public_id" text,
            "p_secret_digest" bytea,
            "p_csrf_secret_digest" bytea,
            "p_user_account_id" uuid,
            "p_idle_seconds" integer,
            "p_absolute_seconds" integer,
            "p_recent_auth_seconds" integer
        )
        RETURNS TABLE (
            "session_id" uuid,
            "public_id" text,
            "created_at" timestamp with time zone,
            "last_seen_at" timestamp with time zone,
            "absolute_expires_at" timestamp with time zone,
            "recent_auth_at" timestamp with time zone
        )
        LANGUAGE sql
        VOLATILE
        SECURITY DEFINER
        PARALLEL UNSAFE
        SET search_path = pg_catalog
        ROWS 1
        AS $function$
            INSERT INTO "control"."user_session" (
                "id", "public_id", "secret_digest", "csrf_secret_digest",
                "user_account_id", "created_at", "last_seen_at",
                "absolute_expires_at", "recent_auth_at"
            )
            SELECT "p_session_id", "p_public_id", "p_secret_digest",
                   "p_csrf_secret_digest", "account"."id", current_timestamp,
                   current_timestamp,
                   current_timestamp + ("p_absolute_seconds" * interval '1 second'),
                   current_timestamp
            FROM "control"."user_account" AS "account"
            WHERE "account"."id" = "p_user_account_id"
              AND "account"."status" = 'ACTIVE'
              AND "p_idle_seconds" > 0
              AND "p_recent_auth_seconds" > 0
              AND "p_absolute_seconds" > "p_idle_seconds"
              AND "p_recent_auth_seconds" <= "p_absolute_seconds"
              AND pg_catalog.octet_length("p_secret_digest") = 32
              AND pg_catalog.octet_length("p_csrf_secret_digest") = 32
              AND "p_public_id" ~ '^sas2_[0-9a-f]{32}$'
            RETURNING "id", "public_id", "created_at", "last_seen_at",
                      "absolute_expires_at", "recent_auth_at"
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_resolve_human_session"(
            "p_public_id" text,
            "p_secret_digest" bytea,
            "p_csrf_secret_digest" bytea,
            "p_idle_seconds" integer,
            "p_touch_interval_seconds" integer,
            "p_recent_auth_seconds" integer
        )
        RETURNS TABLE (
            "session_id" uuid,
            "user_account_id" uuid,
            "public_id" text,
            "recent_auth" boolean,
            "last_seen_at" timestamp with time zone,
            "absolute_expires_at" timestamp with time zone
        )
        LANGUAGE plpgsql
        VOLATILE
        SECURITY DEFINER
        PARALLEL UNSAFE
        SET search_path = pg_catalog
        ROWS 1
        AS $function$
        DECLARE
            "candidate" "control"."user_session"%ROWTYPE;
            "account_status" text;
            "now_at" timestamp with time zone;
            "next_seen" timestamp with time zone;
        BEGIN
            IF "p_public_id" IS NULL
               OR "p_secret_digest" IS NULL
               OR "p_csrf_secret_digest" IS NULL
               OR pg_catalog.octet_length("p_secret_digest") IS DISTINCT FROM 32
               OR pg_catalog.octet_length("p_csrf_secret_digest") IS DISTINCT FROM 32
               OR "p_idle_seconds" <= 0
               OR "p_touch_interval_seconds" <= 0
               OR "p_recent_auth_seconds" <= 0
               OR "p_public_id" !~ '^sas2_[0-9a-f]{32}$' THEN
                RETURN;
            END IF;

            SELECT * INTO "candidate"
            FROM "control"."user_session" AS "session"
            WHERE "session"."public_id" = "p_public_id"
              AND "session"."secret_digest" = "p_secret_digest"
              AND "session"."csrf_secret_digest" = "p_csrf_secret_digest"
            FOR UPDATE;

            IF NOT FOUND THEN
                RETURN;
            END IF;

            SELECT "status" INTO "account_status"
            FROM "control"."user_account"
            WHERE "id" = "candidate"."user_account_id";
            "now_at" := current_timestamp;
            IF "account_status" IS DISTINCT FROM 'ACTIVE'
               OR "candidate"."revoked_at" IS NOT NULL
               OR "candidate"."absolute_expires_at" <= "now_at"
               OR "candidate"."last_seen_at" +
                    ("p_idle_seconds" * interval '1 second') <= "now_at" THEN
                RETURN;
            END IF;

            "next_seen" := "candidate"."last_seen_at";
            IF "candidate"."last_seen_at" +
                    ("p_touch_interval_seconds" * interval '1 second') <= "now_at"
               AND "now_at" < "candidate"."absolute_expires_at" THEN
                "next_seen" := "now_at";
                UPDATE "control"."user_session"
                SET "last_seen_at" = "now_at"
                WHERE "id" = "candidate"."id"
                  AND "revoked_at" IS NULL
                  AND "absolute_expires_at" > "now_at";
            END IF;

            RETURN QUERY SELECT "candidate"."id",
                "candidate"."user_account_id", "candidate"."public_id",
                "candidate"."recent_auth_at" >=
                    ("now_at" - ("p_recent_auth_seconds" * interval '1 second')),
                "next_seen", "candidate"."absolute_expires_at";
        END
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_revoke_human_session"(
            "p_public_id" text,
            "p_secret_digest" bytea
        )
        RETURNS boolean
        LANGUAGE sql
        VOLATILE
        SECURITY DEFINER
        PARALLEL UNSAFE
        SET search_path = pg_catalog
        AS $function$
            UPDATE "control"."user_session"
            SET "revoked_at" = COALESCE("revoked_at", current_timestamp)
            WHERE "public_id" = "p_public_id"
              AND "secret_digest" = "p_secret_digest"
              AND "revoked_at" IS NULL
            RETURNING true
        $function$
        """
    )
    for function in (
        '"control"."slaif_create_human_session"('
        "uuid, text, bytea, bytea, uuid, integer, integer, integer)",
        '"control"."slaif_resolve_human_session"('
        "text, bytea, bytea, integer, integer, integer)",
        '"control"."slaif_revoke_human_session"(text, bytea)',
    ):
        op.execute(f'ALTER FUNCTION {function} OWNER TO "slaif_owner"')
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f'GRANT EXECUTE ON FUNCTION {function} TO "slaif_control"')


def downgrade() -> None:
    op.execute('DROP FUNCTION "control"."slaif_revoke_human_session"(text, bytea)')
    op.execute(
        'DROP FUNCTION "control"."slaif_resolve_human_session"('
        "text, bytea, bytea, integer, integer, integer)"
    )
    op.execute(
        'DROP FUNCTION "control"."slaif_create_human_session"('
        "uuid, text, bytea, bytea, uuid, integer, integer, integer)"
    )
    op.execute('DROP INDEX "control"."user_session_expiry_idx"')
    op.execute('DROP INDEX "control"."user_session_user_account_idx"')
    op.execute('DROP TABLE "control"."user_session"')

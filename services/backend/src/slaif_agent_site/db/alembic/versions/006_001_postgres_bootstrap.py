"""Create the product schema and bootstrap-marker baseline.

Revision ID: 006_001
Revises: None
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "006_001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS "control" AUTHORIZATION "slaif_owner"')
    op.execute('CREATE SCHEMA "content" AUTHORIZATION "slaif_owner"')
    op.execute('CREATE SCHEMA "audit" AUTHORIZATION "slaif_owner"')
    for schema in ("control", "content", "audit"):
        op.execute(f'REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC')
        op.execute(
            f'ALTER DEFAULT PRIVILEGES FOR ROLE "slaif_owner" IN SCHEMA "{schema}" '
            "REVOKE ALL ON TABLES FROM PUBLIC"
        )
        op.execute(
            f'ALTER DEFAULT PRIVILEGES FOR ROLE "slaif_owner" IN SCHEMA "{schema}" '
            "REVOKE ALL ON SEQUENCES FROM PUBLIC"
        )
        op.execute(
            f'ALTER DEFAULT PRIVILEGES FOR ROLE "slaif_owner" IN SCHEMA "{schema}" '
            "REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
        )

    op.execute(
        """
        CREATE TABLE "control"."bootstrap_readiness" (
            "singleton" boolean PRIMARY KEY DEFAULT TRUE CHECK ("singleton"),
            "migration_revision" text NOT NULL,
            "foundation_distribution" text NOT NULL,
            "foundation_version" text NOT NULL,
            "readiness_state" text NOT NULL DEFAULT 'PENDING',
            "content_object_count" integer NOT NULL DEFAULT 0,
            "content_object_fingerprint" text,
            "foundation_object_count" integer NOT NULL DEFAULT 0,
            "foundation_object_fingerprint" text,
            "foundation_deployed" boolean NOT NULL DEFAULT FALSE,
            "foundation_hardened" boolean NOT NULL DEFAULT FALSE,
            "foundation_privileges_validated" boolean NOT NULL DEFAULT FALSE,
            "product_privileges_validated" boolean NOT NULL DEFAULT FALSE,
            "safe" boolean NOT NULL DEFAULT FALSE,
            "updated_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (
                (
                    "readiness_state" = 'PENDING'
                    AND NOT "foundation_hardened"
                    AND NOT "foundation_privileges_validated"
                    AND NOT "product_privileges_validated"
                    AND "content_object_count" = 0
                    AND "content_object_fingerprint" IS NULL
                    AND "foundation_object_count" = 0
                    AND "foundation_object_fingerprint" IS NULL
                    AND NOT "safe"
                )
                OR (
                    "readiness_state" = 'EMPTY_SAFE'
                    AND "foundation_deployed"
                    AND NOT "foundation_hardened"
                    AND NOT "foundation_privileges_validated"
                    AND "product_privileges_validated"
                    AND "content_object_count" = 0
                    AND "content_object_fingerprint" IS NULL
                    AND "foundation_object_count" > 0
                    AND "foundation_object_fingerprint" ~ '^[0-9a-f]{64}$'
                    AND "safe"
                )
                OR (
                    "readiness_state" = 'HARDENED'
                    AND "foundation_deployed"
                    AND "foundation_hardened"
                    AND "foundation_privileges_validated"
                    AND "product_privileges_validated"
                    AND "content_object_count" > 0
                    AND "content_object_fingerprint" ~ '^[0-9a-f]{64}$'
                    AND "foundation_object_count" > 0
                    AND "foundation_object_fingerprint" ~ '^[0-9a-f]{64}$'
                    AND "safe"
                )
            )
        )
        """
    )
    op.execute(
        """
        INSERT INTO "control"."bootstrap_readiness" (
            "singleton", "migration_revision", "foundation_distribution",
            "foundation_version"
        ) VALUES (
            TRUE, '006_001', 'agent-cow-postgresql', '0.2.0'
        )
        """
    )
    op.execute('REVOKE ALL ON TABLE "control"."bootstrap_readiness" FROM PUBLIC')


def downgrade() -> None:
    op.execute('DROP TABLE "control"."bootstrap_readiness"')
    op.execute('DROP SCHEMA "audit"')
    op.execute('DROP SCHEMA "content"')

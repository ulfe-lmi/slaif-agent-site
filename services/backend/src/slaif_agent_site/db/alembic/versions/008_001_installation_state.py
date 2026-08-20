"""Add the singleton installation and setup-token state.

Revision ID: 008_001
Revises: 007_001
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "008_001"
down_revision: str | Sequence[str] | None = "007_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "control"."installation_state" (
            "singleton" boolean PRIMARY KEY DEFAULT TRUE,
            "initialized_at" timestamp with time zone,
            "setup_token_digest" bytea,
            "setup_token_issued_at" timestamp with time zone,
            "setup_token_expires_at" timestamp with time zone,
            "setup_token_generation" bigint NOT NULL DEFAULT 0,
            "updated_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "installation_state_singleton_true"
                CHECK (singleton),
            CONSTRAINT "installation_state_digest_length"
                CHECK (
                    setup_token_digest IS NULL
                    OR octet_length(setup_token_digest) = 32
                ),
            CONSTRAINT "installation_state_token_triplet"
                CHECK (
                    (setup_token_digest IS NULL
                     AND setup_token_issued_at IS NULL
                     AND setup_token_expires_at IS NULL)
                    OR
                    (setup_token_digest IS NOT NULL
                     AND setup_token_issued_at IS NOT NULL
                     AND setup_token_expires_at IS NOT NULL)
                ),
            CONSTRAINT "installation_state_expiry_after_issue"
                CHECK (
                    setup_token_expires_at IS NULL
                    OR setup_token_expires_at > setup_token_issued_at
                ),
            CONSTRAINT "installation_state_initialized_has_no_token"
                CHECK (
                    initialized_at IS NULL
                    OR setup_token_digest IS NULL
                ),
            CONSTRAINT "installation_state_generation_nonnegative"
                CHECK (setup_token_generation >= 0)
        )
        """
    )
    op.execute(
        """
        INSERT INTO "control"."installation_state" ("singleton")
        VALUES (TRUE)
        """
    )
    op.execute('ALTER TABLE "control"."installation_state" OWNER TO "slaif_owner"')
    op.execute('REVOKE ALL ON TABLE "control"."installation_state" FROM PUBLIC')


def downgrade() -> None:
    op.execute('DROP TABLE "control"."installation_state"')

"""Add the narrow Control setup-status function for HTTP orchestration."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "012_001"
down_revision: str | Sequence[str] | None = "011_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_setup_status"()
        RETURNS TABLE ("initialized" boolean, "setup_available" boolean)
        LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1
        AS $function$
            SELECT state.initialized_at IS NOT NULL,
                   state.initialized_at IS NULL
                   AND state.setup_token_digest IS NOT NULL
                   AND state.setup_token_expires_at > CURRENT_TIMESTAMP
            FROM "control"."installation_state" AS state
            WHERE state.singleton
        $function$
        """
    )
    function = '"control"."slaif_setup_status"()'
    op.execute(f'ALTER FUNCTION {function} OWNER TO "slaif_owner"')
    op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(f'GRANT EXECUTE ON FUNCTION {function} TO "slaif_control"')


def downgrade() -> None:
    op.execute('DROP FUNCTION "control"."slaif_setup_status"()')

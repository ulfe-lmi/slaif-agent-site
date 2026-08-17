"""Add the narrow Control database readiness surface.

Revision ID: 007_001
Revises: 006_001
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "007_001"
down_revision: str | Sequence[str] | None = "006_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_control_readiness"()
        RETURNS TABLE (
            "schema_revision" text,
            "marker_revision" text,
            "readiness_state" text,
            "safe" boolean,
            "foundation_distribution" text,
            "foundation_version" text
        )
        LANGUAGE sql
        STABLE
        SECURITY DEFINER
        PARALLEL RESTRICTED
        SET search_path = pg_catalog
        ROWS 1
        AS $function$
            SELECT version_.version_num::text,
                   marker.migration_revision,
                   marker.readiness_state,
                   marker.safe,
                   marker.foundation_distribution,
                   marker.foundation_version
            FROM "control"."alembic_version" AS version_
            CROSS JOIN "control"."bootstrap_readiness" AS marker
            WHERE marker.singleton
        $function$
        """
    )
    op.execute(
        'ALTER FUNCTION "control"."slaif_control_readiness"() OWNER TO "slaif_owner"'
    )
    op.execute(
        'REVOKE ALL ON FUNCTION "control"."slaif_control_readiness"() FROM PUBLIC'
    )
    op.execute('GRANT USAGE ON SCHEMA "control" TO "slaif_control"')
    op.execute(
        'GRANT EXECUTE ON FUNCTION "control"."slaif_control_readiness"() '
        'TO "slaif_control"'
    )


def downgrade() -> None:
    op.execute(
        'REVOKE EXECUTE ON FUNCTION "control"."slaif_control_readiness"() '
        'FROM "slaif_control"'
    )
    op.execute('DROP FUNCTION "control"."slaif_control_readiness"()')
    op.execute('REVOKE USAGE ON SCHEMA "control" FROM "slaif_control"')

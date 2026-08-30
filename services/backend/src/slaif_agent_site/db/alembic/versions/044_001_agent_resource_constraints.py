# ruff: noqa: E501
"""Validate immutable Agent resource constraints from trusted COW context."""

from __future__ import annotations

from alembic import op

revision = "044_001"
down_revision = "043_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_resource_constraints()
        RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE workspace_id uuid; result jsonb;
        BEGIN
          workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
          IF workspace_id IS NULL OR NULLIF(current_setting('app.operation_id', true), '') IS NULL THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
          END IF;
          SELECT w.resource_constraints INTO result FROM control.workspace w
          WHERE w.id=workspace_id AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
            AND EXISTS (SELECT 1 FROM control.site s WHERE s.id=w.site_id AND s.status='ACTIVE')
            AND EXISTS (SELECT 1 FROM control.user_account a WHERE a.id=coalesce(w.delegator_id,w.created_by) AND a.status='ACTIVE');
          IF result IS NULL OR jsonb_typeof(result)<>'object' THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
          IF EXISTS (SELECT 1 FROM jsonb_object_keys(result) k WHERE k NOT IN ('allowed_type_ids','allowed_type_keys','max_content_types','max_fields_per_type','delete_enabled','max_deletes')) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
          RETURN result;
        END;
        $fn$
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS control.slaif_agent_resource_constraints()")

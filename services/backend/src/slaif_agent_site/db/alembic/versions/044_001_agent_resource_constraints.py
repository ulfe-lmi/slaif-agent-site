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
        CREATE FUNCTION control.slaif_agent_resource_constraints(p_site_id uuid)
        RETURNS TABLE(allowed_type_ids uuid[], allowed_type_keys text[], max_content_types integer, max_fields_per_type integer, delete_enabled boolean, max_deletes integer)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE workspace_id uuid; result jsonb; operation_id uuid;
        BEGIN
          BEGIN workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid; operation_id := NULLIF(current_setting('app.operation_id', true), '')::uuid; EXCEPTION WHEN invalid_text_representation THEN RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END;
          IF workspace_id IS NULL OR operation_id IS NULL THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
          END IF;
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          SELECT w.resource_constraints INTO result FROM control.workspace w
          WHERE w.id=workspace_id AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
            AND EXISTS (SELECT 1 FROM control.site s WHERE s.id=w.site_id AND s.status='ACTIVE')
            AND EXISTS (SELECT 1 FROM control.user_account a WHERE a.id=coalesce(w.delegator_id,w.created_by) AND a.status='ACTIVE');
          IF result IS NULL OR jsonb_typeof(result)<>'object' THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
          IF EXISTS (SELECT 1 FROM jsonb_object_keys(result) k WHERE k NOT IN ('allowed_type_ids','allowed_type_keys','max_content_types','max_fields_per_type','delete_enabled','max_deletes')) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
          allowed_type_ids := ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) value);
          allowed_type_keys := ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_keys','[]'::jsonb)) value);
          max_content_types := CASE WHEN result ? 'max_content_types' THEN (result->>'max_content_types')::integer ELSE NULL END;
          max_fields_per_type := CASE WHEN result ? 'max_fields_per_type' THEN (result->>'max_fields_per_type')::integer ELSE NULL END;
          delete_enabled := CASE WHEN result ? 'delete_enabled' THEN (result->>'delete_enabled')::boolean ELSE NULL END;
          max_deletes := CASE WHEN result ? 'max_deletes' THEN (result->>'max_deletes')::integer ELSE NULL END;
          RETURN NEXT;
        END;
        $fn$
        """
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_agent_resource_constraints(uuid) FROM PUBLIC, slaif_agent_runtime, slaif_editor_runtime, slaif_control"
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS control.slaif_agent_resource_constraints(uuid)")

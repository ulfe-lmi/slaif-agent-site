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
          IF (result ? 'allowed_type_ids' AND jsonb_typeof(result->'allowed_type_ids') <> 'array') OR (result ? 'allowed_type_keys' AND jsonb_typeof(result->'allowed_type_keys') <> 'array') OR (result ? 'delete_enabled' AND jsonb_typeof(result->'delete_enabled') <> 'boolean') OR (result ? 'max_content_types' AND jsonb_typeof(result->'max_content_types') <> 'number') OR (result ? 'max_fields_per_type' AND jsonb_typeof(result->'max_fields_per_type') <> 'number') OR (result ? 'max_deletes' AND jsonb_typeof(result->'max_deletes') <> 'number') THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
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
    op.execute(
        "DROP FUNCTION content.slaif_agent_content_type_update(uuid,uuid,jsonb,text,jsonb,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_update(
            p_site_id uuid, p_type_id uuid, p_labels jsonb,
            p_slug_pattern text, p_settings jsonb, p_expected integer
        ) RETURNS SETOF content.content_type
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
          locked_type content.content_type;
          constraints record;
          updated content.content_type;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          PERFORM pg_advisory_xact_lock(
            hashtextextended(
              p_site_id::text || ':' || p_type_id::text || '_content_type_definition',
              994
            )
          );
          SELECT t.* INTO locked_type
          FROM content.content_type AS t
          WHERE t.site_id = p_site_id
            AND t.id = p_type_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          IF locked_type.definition_version <> p_expected THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;

          SELECT * INTO STRICT constraints
          FROM control.slaif_agent_resource_constraints(p_site_id);
          IF coalesce(cardinality(constraints.allowed_type_ids), 0) > 0
             AND NOT (locked_type.id = ANY(constraints.allowed_type_ids))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF coalesce(cardinality(constraints.allowed_type_keys), 0) > 0
             AND NOT (locked_type.key = ANY(constraints.allowed_type_keys))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE = 'P0003';
          END IF;

          UPDATE content.content_type
          SET labels = coalesce(p_labels, labels),
              slug_pattern = coalesce(p_slug_pattern, slug_pattern),
              settings = coalesce(p_settings, settings),
              definition_version = definition_version + 1,
              updated_at = now()
          WHERE id = locked_type.id
            AND site_id = p_site_id
            AND status = 'ACTIVE'
          RETURNING * INTO updated;
          RETURN NEXT updated;
        END;
        $fn$
        """
    )
    op.execute(
        "DROP FUNCTION content.slaif_agent_content_type_delete(uuid,uuid,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_delete(
            p_site_id uuid, p_type_id uuid, p_expected integer
        ) RETURNS SETOF content.content_type
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
          locked_type content.content_type;
          constraints record;
          deleted content.content_type;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          PERFORM pg_advisory_xact_lock(
            hashtextextended(
              p_site_id::text || ':' || p_type_id::text || '_content_type_definition',
              994
            )
          );
          SELECT t.* INTO locked_type
          FROM content.content_type AS t
          WHERE t.site_id = p_site_id
            AND t.id = p_type_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          IF locked_type.definition_version <> p_expected THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;

          SELECT * INTO STRICT constraints
          FROM control.slaif_agent_resource_constraints(p_site_id);
          IF coalesce(cardinality(constraints.allowed_type_ids), 0) > 0
             AND NOT (locked_type.id = ANY(constraints.allowed_type_ids))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF coalesce(cardinality(constraints.allowed_type_keys), 0) > 0
             AND NOT (locked_type.key = ANY(constraints.allowed_type_keys))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF constraints.delete_enabled IS FALSE THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE = 'P0003';
          END IF;
          IF EXISTS (
            SELECT 1 FROM content.content_item
            WHERE site_id = p_site_id AND type_id = locked_type.id
          ) THEN
            RAISE EXCEPTION 'TYPE_DEPENDENCIES' USING ERRCODE = 'P0003';
          END IF;

          UPDATE content.content_type
          SET status = 'DELETED',
              definition_version = definition_version + 1,
              updated_at = now()
          WHERE id = locked_type.id
            AND site_id = p_site_id
            AND status = 'ACTIVE'
          RETURNING * INTO deleted;
          RETURN NEXT deleted;
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_content_type_update(
            uuid,uuid,jsonb,text,jsonb,integer
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_content_type_delete(
            uuid,uuid,integer
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_update(
            uuid,uuid,jsonb,text,jsonb,integer
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_delete(
            uuid,uuid,integer
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_agent_content_type_create(
            p_site_id uuid, p_key text, p_labels jsonb,
            p_slug_pattern text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, key text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
          workspace_id uuid;
          constraints record;
          visible_type_count bigint;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          BEGIN
            workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
          EXCEPTION WHEN invalid_text_representation THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
          END;
          IF workspace_id IS NULL THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
          END IF;

          SELECT * INTO STRICT constraints
          FROM control.slaif_agent_resource_constraints(p_site_id);
          IF coalesce(cardinality(constraints.allowed_type_keys), 0) > 0
             AND NOT (p_key = ANY(constraints.allowed_type_keys))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE='P0003';
          END IF;

          PERFORM pg_advisory_xact_lock(
            hashtextextended(workspace_id::text || '_content_type_create', 994)
          );
          IF constraints.max_content_types IS NOT NULL THEN
            SELECT count(*) INTO visible_type_count
            FROM content.content_type AS content_type
            WHERE content_type.site_id=p_site_id
              AND content_type.status='ACTIVE';
            IF visible_type_count >= constraints.max_content_types THEN
              RAISE EXCEPTION 'AGENT_RESOURCE_CONTENT_TYPE_LIMIT'
                USING ERRCODE='P0001';
            END IF;
          END IF;

          RETURN QUERY
          SELECT * FROM content.slaif_agent_unchecked_content_type_create(
            p_site_id, p_key, p_labels, p_slug_pattern, p_settings
          );
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_content_type_create(
            uuid,text,jsonb,text,jsonb
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_agent_runtime, slaif_public_reader, slaif_preview_reader,
            slaif_reviewer, slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_create(
            uuid,text,jsonb,text,jsonb
        ) TO slaif_agent_runtime
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION content.slaif_agent_content_type_update(uuid,uuid,jsonb,text,jsonb,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_update(
            p_site_id uuid, p_type_id uuid, p_labels jsonb,
            p_slug_pattern text, p_settings jsonb, p_expected integer
        ) RETURNS SETOF content.content_type
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE updated content.content_type;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          IF NOT EXISTS(
            SELECT 1 FROM content.content_type
            WHERE id = p_type_id AND site_id = p_site_id
              AND status = 'ACTIVE' AND definition_version = p_expected
          ) THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          UPDATE content.content_type
          SET labels = coalesce(p_labels, labels),
              slug_pattern = coalesce(p_slug_pattern, slug_pattern),
              settings = coalesce(p_settings, settings),
              definition_version = definition_version + 1,
              updated_at = now()
          WHERE id = p_type_id AND site_id = p_site_id
          RETURNING * INTO updated;
          RETURN NEXT updated;
        END;
        $fn$
        """
    )
    op.execute(
        "DROP FUNCTION content.slaif_agent_content_type_delete(uuid,uuid,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_content_type_delete(
            p_site_id uuid, p_type_id uuid, p_expected integer
        ) RETURNS SETOF content.content_type
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE deleted content.content_type;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          IF NOT EXISTS(
            SELECT 1 FROM content.content_type
            WHERE id = p_type_id AND site_id = p_site_id
              AND status = 'ACTIVE' AND definition_version = p_expected
          ) THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          IF EXISTS(
            SELECT 1 FROM content.content_item
            WHERE site_id = p_site_id AND type_id = p_type_id
          ) THEN
            RAISE EXCEPTION 'TYPE_DEPENDENCIES' USING ERRCODE = 'P0003';
          END IF;
          UPDATE content.content_type
          SET status = 'DELETED',
              definition_version = definition_version + 1,
              updated_at = now()
          WHERE id = p_type_id AND site_id = p_site_id
          RETURNING * INTO deleted;
          RETURN NEXT deleted;
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_content_type_update(
            uuid,uuid,jsonb,text,jsonb,integer
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_content_type_delete(
            uuid,uuid,integer
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_update(
            uuid,uuid,jsonb,text,jsonb,integer
        ) TO PUBLIC, slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_delete(
            uuid,uuid,integer
        ) TO PUBLIC, slaif_agent_runtime
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_agent_content_type_create(
            p_site_id uuid, p_key text, p_labels jsonb,
            p_slug_pattern text, p_settings jsonb
        ) RETURNS TABLE (
            id uuid, site_id uuid, key text, labels jsonb,
            slug_pattern text, status text, definition_version integer,
            settings jsonb, created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          RETURN QUERY
          SELECT * FROM content.slaif_agent_unchecked_content_type_create(
            p_site_id, p_key, p_labels, p_slug_pattern, p_settings
          );
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_content_type_create(
            uuid,text,jsonb,text,jsonb
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_agent_runtime, slaif_public_reader, slaif_preview_reader,
            slaif_reviewer, slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_content_type_create(
            uuid,text,jsonb,text,jsonb
        ) TO slaif_agent_runtime
        """
    )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_agent_resource_constraints(uuid)")

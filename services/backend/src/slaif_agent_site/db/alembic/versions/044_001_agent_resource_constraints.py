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
        "DROP FUNCTION content.slaif_agent_field_definition_create(uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_create(
            p_site_id uuid, p_type_id uuid, p_key text, p_label text,
            p_field_type text, p_required boolean, p_localized boolean,
            p_cardinality integer, p_position integer, p_validation jsonb,
            p_ui_options jsonb
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
          workspace_id uuid;
          parent_type content.content_type;
          constraints record;
          visible_field_count bigint;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          BEGIN
            workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
          EXCEPTION WHEN invalid_text_representation THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
          END;
          IF workspace_id IS NULL THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
          END IF;

          SELECT t.* INTO parent_type
          FROM content.content_type AS t
          WHERE t.id = p_type_id
            AND t.site_id = p_site_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'FIELD_TYPE_SITE_NOT_FOUND' USING ERRCODE = 'P0002';
          END IF;

          SELECT * INTO STRICT constraints
          FROM control.slaif_agent_resource_constraints(p_site_id);
          IF coalesce(cardinality(constraints.allowed_type_ids), 0) > 0
             AND NOT (parent_type.id = ANY(constraints.allowed_type_ids))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF coalesce(cardinality(constraints.allowed_type_keys), 0) > 0
             AND NOT (parent_type.key = ANY(constraints.allowed_type_keys))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE = 'P0003';
          END IF;

          PERFORM pg_advisory_xact_lock(
            hashtextextended(
              workspace_id::text || ':' || parent_type.id::text ||
                '_field_definition_create',
              994
            )
          );
          IF constraints.max_fields_per_type IS NOT NULL THEN
            SELECT count(*) INTO visible_field_count
            FROM content.field_definition AS field
            WHERE field.site_id = p_site_id
              AND field.type_id = parent_type.id;
            IF visible_field_count >= constraints.max_fields_per_type THEN
              RAISE EXCEPTION 'AGENT_RESOURCE_FIELD_DEFINITION_LIMIT'
                USING ERRCODE = 'P0001';
            END IF;
          END IF;

          INSERT INTO content.field_definition(
            site_id, type_id, key, label, field_type, required, localized,
            cardinality, "position", validation, ui_options
          ) VALUES (
            p_site_id, p_type_id, p_key, p_label, p_field_type, p_required,
            p_localized, p_cardinality, p_position, p_validation, p_ui_options
          );
          RETURN QUERY
          SELECT f.id, f.type_id, f.key, f.label, f.field_type, f.required,
                 f.localized, f.cardinality, f."position", f.validation,
                 f.ui_options, f.definition_version, f.created_at, f.updated_at
          FROM content.field_definition AS f
          WHERE f.site_id = p_site_id
            AND f.type_id = p_type_id
            AND f.key = p_key
          ORDER BY f.created_at DESC
          LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_field_definition_create(
            uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_create(
            uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        "DROP FUNCTION content.slaif_agent_field_definition_update(uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_update(
            p_site_id uuid, p_type_id uuid, p_field_id uuid, p_label text,
            p_required boolean, p_localized boolean, p_cardinality integer,
            p_position integer, p_validation jsonb, p_ui_options jsonb,
            p_expected integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, "key" text, label text,
            field_type text, required boolean, localized boolean,
            cardinality integer, "position" integer, validation jsonb,
            ui_options jsonb, definition_version integer,
            created_at timestamptz, updated_at timestamptz
        )
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
          workspace_id uuid;
          locked_parent content.content_type;
          locked_field content.field_definition;
          constraints record;
          updated content.field_definition;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          BEGIN
            workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
          EXCEPTION WHEN invalid_text_representation THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
          END;
          IF workspace_id IS NULL THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
          END IF;

          PERFORM pg_advisory_xact_lock(
            hashtextextended(
              workspace_id::text || ':' || p_type_id::text || ':' ||
                p_field_id::text || '_field_definition',
              994
            )
          );
          SELECT t.* INTO locked_parent
          FROM content.content_type AS t
          WHERE t.site_id = p_site_id
            AND t.id = p_type_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          SELECT f.* INTO locked_field
          FROM content.field_definition AS f
          JOIN content.content_type AS t
            ON t.site_id = f.site_id AND t.id = f.type_id
          WHERE f.site_id = p_site_id
            AND f.type_id = locked_parent.id
            AND f.id = p_field_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          IF locked_field.definition_version <> p_expected THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;

          SELECT * INTO STRICT constraints
          FROM control.slaif_agent_resource_constraints(p_site_id);
          IF coalesce(cardinality(constraints.allowed_type_ids), 0) > 0
             AND NOT (locked_parent.id = ANY(constraints.allowed_type_ids))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF coalesce(cardinality(constraints.allowed_type_keys), 0) > 0
             AND NOT (locked_parent.key = ANY(constraints.allowed_type_keys))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE = 'P0003';
          END IF;

          UPDATE content.field_definition AS field
          SET label = coalesce(p_label, field.label),
              required = coalesce(p_required, field.required),
              localized = coalesce(p_localized, field.localized),
              cardinality = coalesce(p_cardinality, field.cardinality),
              "position" = coalesce(p_position, field."position"),
              validation = coalesce(p_validation, field.validation),
              ui_options = coalesce(p_ui_options, field.ui_options),
              definition_version = field.definition_version + 1,
              updated_at = now()
          WHERE field.id = locked_field.id
            AND field.site_id = p_site_id
            AND field.type_id = locked_parent.id
            AND field.definition_version = locked_field.definition_version
          RETURNING field.* INTO updated;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          RETURN QUERY
          SELECT updated.id, updated.site_id, updated.type_id, updated.key,
                 updated.label, updated.field_type, updated.required,
                 updated.localized, updated.cardinality, updated."position",
                 updated.validation, updated.ui_options,
                 updated.definition_version, updated.created_at,
                 updated.updated_at;
        END;
        $fn$
        """
    )
    op.execute(
        "DROP FUNCTION content.slaif_agent_field_definition_delete(uuid,uuid,uuid,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_delete(
            p_site_id uuid, p_type_id uuid, p_field_id uuid, p_expected integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, type_id uuid, "key" text, label text,
            field_type text, required boolean, localized boolean,
            cardinality integer, "position" integer, validation jsonb,
            ui_options jsonb, definition_version integer,
            created_at timestamptz, updated_at timestamptz
        )
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
          workspace_id uuid;
          locked_parent content.content_type;
          locked_field content.field_definition;
          constraints record;
          deleted content.field_definition;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          BEGIN
            workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
          EXCEPTION WHEN invalid_text_representation THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
          END;
          IF workspace_id IS NULL THEN
            RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE = '22023';
          END IF;

          PERFORM pg_advisory_xact_lock(
            hashtextextended(
              workspace_id::text || ':' || p_type_id::text || ':' ||
                p_field_id::text || '_field_definition',
              994
            )
          );
          SELECT t.* INTO locked_parent
          FROM content.content_type AS t
          WHERE t.site_id = p_site_id
            AND t.id = p_type_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          SELECT f.* INTO locked_field
          FROM content.field_definition AS f
          JOIN content.content_type AS t
            ON t.site_id = f.site_id AND t.id = f.type_id
          WHERE f.site_id = p_site_id
            AND f.type_id = locked_parent.id
            AND f.id = p_field_id
            AND t.status = 'ACTIVE'
          FOR UPDATE;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          IF locked_field.definition_version <> p_expected THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;

          SELECT * INTO STRICT constraints
          FROM control.slaif_agent_resource_constraints(p_site_id);
          IF coalesce(cardinality(constraints.allowed_type_ids), 0) > 0
             AND NOT (locked_parent.id = ANY(constraints.allowed_type_ids))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_ID_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF coalesce(cardinality(constraints.allowed_type_keys), 0) > 0
             AND NOT (locked_parent.key = ANY(constraints.allowed_type_keys))
          THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_TYPE_KEY_DENIED' USING ERRCODE = 'P0003';
          END IF;
          IF constraints.delete_enabled IS FALSE THEN
            RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE = 'P0003';
          END IF;
          IF EXISTS (
            SELECT 1
            FROM content.content_item AS item
            WHERE item.site_id = p_site_id
              AND item.type_id = locked_parent.id
              AND item."values" ? locked_field.key
          ) THEN
            RAISE EXCEPTION 'FIELD_DEPENDENCIES' USING ERRCODE = 'P0003';
          END IF;

          DELETE FROM content.field_definition AS field
          WHERE field.id = locked_field.id
            AND field.site_id = p_site_id
            AND field.type_id = locked_parent.id
            AND field.definition_version = locked_field.definition_version
          RETURNING field.* INTO deleted;
          IF NOT FOUND THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          RETURN QUERY
          SELECT deleted.id, deleted.site_id, deleted.type_id, deleted.key,
                 deleted.label, deleted.field_type, deleted.required,
                 deleted.localized, deleted.cardinality, deleted."position",
                 deleted.validation, deleted.ui_options,
                 deleted.definition_version, deleted.created_at,
                 deleted.updated_at;
        END;
        $fn$
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_field_definition_update(
            uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION content.slaif_agent_field_definition_delete(
            uuid,uuid,uuid,integer
        ) FROM PUBLIC, slaif_control, slaif_editor_runtime,
            slaif_public_reader, slaif_preview_reader, slaif_reviewer,
            slaif_scheduler, slaif_media, slaif_gc
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_update(
            uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_delete(
            uuid,uuid,uuid,integer
        ) TO slaif_agent_runtime
        """
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
        "DROP FUNCTION content.slaif_agent_field_definition_update(uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_update(
            p_site_id uuid, p_type_id uuid, p_field_id uuid, p_label text,
            p_required boolean, p_localized boolean, p_cardinality integer,
            p_position integer, p_validation jsonb, p_ui_options jsonb,
            p_expected integer
        ) RETURNS SETOF content.field_definition
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE updated content.field_definition;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          IF NOT EXISTS (
            SELECT 1
            FROM content.field_definition AS f
            JOIN content.content_type AS t ON t.id = f.type_id
            WHERE f.id = p_field_id
              AND f.site_id = p_site_id
              AND f.type_id = p_type_id
              AND f.definition_version = p_expected
              AND t.status = 'ACTIVE'
          ) THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          UPDATE content.field_definition
          SET label = coalesce(p_label, label),
              required = coalesce(p_required, required),
              localized = coalesce(p_localized, localized),
              cardinality = coalesce(p_cardinality, cardinality),
              "position" = coalesce(p_position, "position"),
              validation = coalesce(p_validation, validation),
              ui_options = coalesce(p_ui_options, ui_options),
              definition_version = definition_version + 1,
              updated_at = now()
          WHERE id = p_field_id
            AND site_id = p_site_id
          RETURNING * INTO updated;
          RETURN NEXT updated;
        END;
        $fn$
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_update(
            uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        "DROP FUNCTION content.slaif_agent_field_definition_delete(uuid,uuid,uuid,integer)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_delete(
            p_site_id uuid, p_type_id uuid, p_field_id uuid, p_expected integer
        ) RETURNS SETOF content.field_definition
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE deleted content.field_definition;
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          IF NOT EXISTS (
            SELECT 1
            FROM content.field_definition
            WHERE id = p_field_id
              AND site_id = p_site_id
              AND type_id = p_type_id
              AND definition_version = p_expected
          ) THEN
            RAISE EXCEPTION 'STALE_DEFINITION' USING ERRCODE = 'P0003';
          END IF;
          IF EXISTS (
            SELECT 1
            FROM content.content_item AS item
            WHERE item.site_id = p_site_id
              AND item.type_id = p_type_id
              AND item."values" ? (
                SELECT key FROM content.field_definition WHERE id = p_field_id
              )
          ) THEN
            RAISE EXCEPTION 'FIELD_DEPENDENCIES' USING ERRCODE = 'P0003';
          END IF;
          DELETE FROM content.field_definition
          WHERE id = p_field_id AND site_id = p_site_id
          RETURNING * INTO deleted;
          RETURN NEXT deleted;
        END;
        $fn$
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_delete(
            uuid,uuid,uuid,integer
        ) TO slaif_agent_runtime
        """
    )
    op.execute(
        "DROP FUNCTION content.slaif_agent_field_definition_create(uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_field_definition_create(
            p_site_id uuid, p_type_id uuid, p_key text, p_label text,
            p_field_type text, p_required boolean, p_localized boolean,
            p_cardinality integer, p_position integer, p_validation jsonb,
            p_ui_options jsonb
        ) RETURNS TABLE (
            id uuid, type_id uuid, "key" text, label text, field_type text,
            required boolean, localized boolean, cardinality integer,
            "position" integer, validation jsonb, ui_options jsonb,
            definition_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
          PERFORM control.slaif_agent_require_cow_site(p_site_id);
          IF NOT EXISTS (
            SELECT 1 FROM content.content_type AS t
            WHERE t.id = p_type_id
              AND t.site_id = p_site_id
              AND t.status = 'ACTIVE'
          ) THEN
            RAISE EXCEPTION 'FIELD_TYPE_SITE_NOT_FOUND' USING ERRCODE = 'P0002';
          END IF;
          INSERT INTO content.field_definition(
            site_id, type_id, key, label, field_type, required, localized,
            cardinality, "position", validation, ui_options
          ) VALUES (
            p_site_id, p_type_id, p_key, p_label, p_field_type, p_required,
            p_localized, p_cardinality, p_position, p_validation, p_ui_options
          );
          RETURN QUERY
          SELECT f.id, f.type_id, f.key, f.label, f.field_type, f.required,
                 f.localized, f.cardinality, f."position", f.validation,
                 f.ui_options, f.definition_version, f.created_at, f.updated_at
          FROM content.field_definition AS f
          WHERE f.site_id = p_site_id
            AND f.type_id = p_type_id
            AND f.key = p_key
          ORDER BY f.created_at DESC
          LIMIT 1;
        END;
        $fn$
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_create(
            uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb
        ) TO slaif_agent_runtime
        """
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

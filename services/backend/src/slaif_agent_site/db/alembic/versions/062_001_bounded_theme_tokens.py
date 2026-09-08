# ruff: noqa: E501
"""Add the closed theme-schema/v1 data plane and Agent theme authority."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "062_001"
down_revision: str | Sequence[str] | None = "061_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_THEME_COLUMNS = """
    id uuid, site_id uuid, schema_version text, renderer_version text,
    row_version integer, palette jsonb, typography jsonb, layout jsonb,
    shape jsonb, created_at timestamptz, updated_at timestamptz
"""


def _execute_block(sql: str) -> None:
    statements: list[str] = []
    in_function = False
    for line in sql.splitlines(keepends=True):
        statements.append(line)
        if line.count("$fn$") % 2:
            in_function = not in_function
        if line.rstrip().endswith(";") and not in_function:
            op.execute("".join(statements))
            statements = []
    if "".join(statements).strip():
        op.execute("".join(statements))


def _validate_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_theme_validate_groups(
            p_palette jsonb, p_typography jsonb, p_layout jsonb, p_shape jsonb
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            IF jsonb_typeof(p_palette)<>'object'
               OR p_palette ?| ARRAY['preset'] IS FALSE
               OR (SELECT count(*) FROM jsonb_object_keys(p_palette))<>1
               OR p_palette->>'preset' NOT IN ('ocean','meadow','ember')
            THEN RAISE EXCEPTION 'THEME_PALETTE_INVALID' USING ERRCODE='P0003'; END IF;
            IF jsonb_typeof(p_typography)<>'object'
               OR (SELECT count(*) FROM jsonb_object_keys(p_typography))<>3
               OR EXISTS (
                   SELECT 1 FROM jsonb_object_keys(p_typography) key
                   WHERE key NOT IN ('family','scale','weight')
               )
               OR p_typography->>'family' NOT IN ('system','serif','mono')
               OR p_typography->>'scale' NOT IN ('compact','balanced','spacious')
               OR p_typography->>'weight' NOT IN ('regular','medium','bold')
            THEN RAISE EXCEPTION 'THEME_TYPOGRAPHY_INVALID' USING ERRCODE='P0003'; END IF;
            IF jsonb_typeof(p_layout)<>'object'
               OR (SELECT count(*) FROM jsonb_object_keys(p_layout))<>3
               OR EXISTS (
                   SELECT 1 FROM jsonb_object_keys(p_layout) key
                   WHERE key NOT IN ('content_width','spacing','grid_gap')
               )
               OR p_layout->>'content_width' NOT IN ('sm','md','lg','xl')
               OR p_layout->>'spacing' NOT IN ('sm','md','lg')
               OR p_layout->>'grid_gap' NOT IN ('sm','md','lg')
            THEN RAISE EXCEPTION 'THEME_LAYOUT_INVALID' USING ERRCODE='P0003'; END IF;
            IF jsonb_typeof(p_shape)<>'object'
               OR (SELECT count(*) FROM jsonb_object_keys(p_shape))<>2
               OR EXISTS (
                   SELECT 1 FROM jsonb_object_keys(p_shape) key
                   WHERE key NOT IN ('radius','shadow')
               )
               OR p_shape->>'radius' NOT IN ('none','sm','md','lg','full')
               OR p_shape->>'shadow' NOT IN ('none','sm','md','lg')
            THEN RAISE EXCEPTION 'THEME_SHAPE_INVALID' USING ERRCODE='P0003'; END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_each_text(p_palette) item
                WHERE item.value LIKE '%:%' OR item.value LIKE '%;%' OR item.value LIKE '%/%'
            ) THEN RAISE EXCEPTION 'THEME_RAW_STYLE_FORBIDDEN' USING ERRCODE='P0003'; END IF;
        END;
        $fn$;
    """


def _default_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_theme_default(p_site_id uuid)
        RETURNS TABLE({_THEME_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT p_site_id, p_site_id, 'theme-schema/v1', 'renderer-v1', 1,
                '{{"preset":"ocean"}}'::jsonb,
                '{{"family":"system","scale":"balanced","weight":"regular"}}'::jsonb,
                '{{"content_width":"md","spacing":"md","grid_gap":"md"}}'::jsonb,
                '{{"radius":"md","shadow":"sm"}}'::jsonb,
                s.created_at, s.created_at
            FROM control.site s WHERE s.id=p_site_id
        $fn$;

        CREATE FUNCTION content.slaif_theme_project(p_site_id uuid)
        RETURNS TABLE({_THEME_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT t.id,t.site_id,t.schema_version,t.renderer_version,t.row_version,
                t.palette,t.typography,t.layout,t.shape,t.created_at,t.updated_at
            FROM content.theme t WHERE t.site_id=p_site_id
            UNION ALL
            SELECT d.id,d.site_id,d.schema_version,d.renderer_version,d.row_version,
                d.palette,d.typography,d.layout,d.shape,d.created_at,d.updated_at
            FROM content.slaif_theme_default(p_site_id) d
            WHERE NOT EXISTS (
                SELECT 1 FROM content.theme existing WHERE existing.site_id=p_site_id
            )
        $fn$;
    """


def _legacy_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_theme_get(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,palette jsonb,typography jsonb,
            layout jsonb,shape jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            SELECT id,site_id,palette,typography,layout,shape,created_at,updated_at
            FROM content.slaif_theme_project(p_site_id)
        $fn$;

        CREATE OR REPLACE FUNCTION content.slaif_theme_update(
            p_site_id uuid,p_palette jsonb,p_typography jsonb,
            p_layout jsonb,p_shape jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,palette jsonb,typography jsonb,
            layout jsonb,shape jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE current_theme record; next_palette jsonb; next_typography jsonb;
            next_layout jsonb; next_shape jsonb; exists_row boolean;
        BEGIN
            SELECT * INTO current_theme FROM content.slaif_theme_project(p_site_id);
            IF current_theme.id IS NULL THEN
                RAISE EXCEPTION 'THEME_SITE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            exists_row:=EXISTS(SELECT 1 FROM content.theme t WHERE t.site_id=p_site_id);
            IF p_palette IS NOT NULL AND jsonb_typeof(p_palette)<>'object' THEN
                RAISE EXCEPTION 'THEME_PALETTE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_typography IS NOT NULL AND jsonb_typeof(p_typography)<>'object' THEN
                RAISE EXCEPTION 'THEME_TYPOGRAPHY_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_layout IS NOT NULL AND jsonb_typeof(p_layout)<>'object' THEN
                RAISE EXCEPTION 'THEME_LAYOUT_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_shape IS NOT NULL AND jsonb_typeof(p_shape)<>'object' THEN
                RAISE EXCEPTION 'THEME_SHAPE_INVALID' USING ERRCODE='P0003';
            END IF;
            next_palette:=current_theme.palette||coalesce(p_palette,'{{}}'::jsonb);
            next_typography:=current_theme.typography||coalesce(p_typography,'{{}}'::jsonb);
            next_layout:=current_theme.layout||coalesce(p_layout,'{{}}'::jsonb);
            next_shape:=current_theme.shape||coalesce(p_shape,'{{}}'::jsonb);
            PERFORM content.slaif_theme_validate_groups(
                next_palette,next_typography,next_layout,next_shape);
            IF next_palette IS NOT DISTINCT FROM current_theme.palette
               AND next_typography IS NOT DISTINCT FROM current_theme.typography
               AND next_layout IS NOT DISTINCT FROM current_theme.layout
               AND next_shape IS NOT DISTINCT FROM current_theme.shape
            THEN
                RETURN QUERY SELECT current_theme.id,current_theme.site_id,
                    current_theme.palette,current_theme.typography,current_theme.layout,
                    current_theme.shape,current_theme.created_at,current_theme.updated_at;
                RETURN;
            END IF;
            IF NOT exists_row THEN
                INSERT INTO content.theme(
                    id,site_id,schema_version,renderer_version,row_version,
                    palette,typography,layout,shape,created_at,updated_at
                ) VALUES (
                    current_theme.id,current_theme.site_id,current_theme.schema_version,
                    current_theme.renderer_version,current_theme.row_version+1,next_palette,
                    next_typography,next_layout,next_shape,current_theme.created_at,now()
                );
            ELSE
                UPDATE content.theme AS t SET palette=next_palette,typography=next_typography,
                    layout=next_layout,shape=next_shape,row_version=t.row_version+1,
                    updated_at=now() WHERE t.site_id=p_site_id;
            END IF;
            RETURN QUERY SELECT t.id,t.site_id,t.palette,t.typography,t.layout,t.shape,
                t.created_at,t.updated_at FROM content.theme t
                WHERE t.site_id=p_site_id;
        END;
        $fn$;
    """


def _agent_read_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_agent_theme_get(p_site_id uuid)
        RETURNS TABLE({_THEME_COLUMNS}) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'theme:read');
            RETURN QUERY SELECT * FROM content.slaif_theme_project(p_site_id);
        END;
        $fn$;
    """


def _agent_update_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_agent_theme_update(
            p_site_id uuid,p_expected integer,p_palette jsonb,p_typography jsonb,
            p_layout jsonb,p_shape jsonb,p_no_effect boolean
        ) RETURNS TABLE({_THEME_COLUMNS}, no_effect boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE current_theme record; next_palette jsonb; next_typography jsonb;
            next_layout jsonb; next_shape jsonb; constraints jsonb;
            workspace_id uuid; capability_id uuid; exists_row boolean;
            token_key text; group_name text; changed boolean:=false;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'theme-tokens:write');
            BEGIN
                workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF workspace_id IS NULL OR NULLIF(current_setting('app.operation_id',true),'') IS NULL
            THEN RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END IF;
            IF p_expected IS NULL OR p_expected<=0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||chr(58)||p_site_id::text||chr(58)||'theme',995));
            SELECT c.resource_constraints INTO constraints
            FROM control.capability c WHERE c.id=capability_id;
            SELECT * INTO current_theme FROM content.slaif_theme_project(p_site_id);
            IF current_theme.id IS NULL THEN
                RAISE EXCEPTION 'THEME_SITE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            exists_row:=EXISTS(SELECT 1 FROM content.theme t WHERE t.site_id=p_site_id);
            IF current_theme.schema_version<>'theme-schema/v1'
               OR current_theme.renderer_version<>'renderer-v1'
               OR current_theme.row_version<=0
            THEN RAISE EXCEPTION 'THEME_SCHEMA_UNSUPPORTED' USING ERRCODE='P0003'; END IF;
            IF current_theme.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF (
                p_palette IS NULL AND p_typography IS NULL AND p_layout IS NULL AND p_shape IS NULL
            ) THEN RAISE EXCEPTION 'THEME_UPDATE_EMPTY' USING ERRCODE='P0003'; END IF;
            FOR group_name,token_key IN
                SELECT 'palette',entry.key FROM jsonb_each(coalesce(p_palette,'{{}}'::jsonb)) entry
                UNION ALL SELECT 'typography',entry.key FROM jsonb_each(coalesce(p_typography,'{{}}'::jsonb)) entry
                UNION ALL SELECT 'layout',entry.key FROM jsonb_each(coalesce(p_layout,'{{}}'::jsonb)) entry
                UNION ALL SELECT 'shape',entry.key FROM jsonb_each(coalesce(p_shape,'{{}}'::jsonb)) entry
            LOOP
                IF jsonb_typeof(constraints->'allowed_theme_tokens')='array'
                   AND jsonb_array_length(constraints->'allowed_theme_tokens')>0
                   AND NOT (constraints->'allowed_theme_tokens' ? (group_name||'.'||token_key))
                THEN RAISE EXCEPTION 'AGENT_RESOURCE_THEME_TOKEN_DENIED' USING ERRCODE='P0007'; END IF;
            END LOOP;
            IF p_palette ? 'preset'
               AND jsonb_typeof(constraints->'allowed_theme_palette_presets')='array'
               AND jsonb_array_length(constraints->'allowed_theme_palette_presets')>0
               AND NOT (constraints->'allowed_theme_palette_presets' ? (p_palette->>'preset'))
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_THEME_PALETTE_DENIED' USING ERRCODE='P0007'; END IF;
            IF p_typography ? 'family'
               AND jsonb_typeof(constraints->'allowed_theme_typography_families')='array'
               AND jsonb_array_length(constraints->'allowed_theme_typography_families')>0
               AND NOT (constraints->'allowed_theme_typography_families' ? (p_typography->>'family'))
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_THEME_TYPOGRAPHY_DENIED' USING ERRCODE='P0007'; END IF;
            IF p_palette IS NOT NULL AND jsonb_typeof(p_palette)<>'object'
               OR p_typography IS NOT NULL AND jsonb_typeof(p_typography)<>'object'
               OR p_layout IS NOT NULL AND jsonb_typeof(p_layout)<>'object'
               OR p_shape IS NOT NULL AND jsonb_typeof(p_shape)<>'object'
            THEN RAISE EXCEPTION 'THEME_UPDATE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_palette IS NOT NULL AND EXISTS (
                SELECT 1 FROM jsonb_object_keys(p_palette) key
                WHERE key NOT IN ('preset')
            ) THEN RAISE EXCEPTION 'THEME_PALETTE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_typography IS NOT NULL AND EXISTS (
                SELECT 1 FROM jsonb_object_keys(p_typography) key
                WHERE key NOT IN ('family','scale','weight')
            ) THEN RAISE EXCEPTION 'THEME_TYPOGRAPHY_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_layout IS NOT NULL AND EXISTS (
                SELECT 1 FROM jsonb_object_keys(p_layout) key
                WHERE key NOT IN ('content_width','spacing','grid_gap')
            ) THEN RAISE EXCEPTION 'THEME_LAYOUT_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_shape IS NOT NULL AND EXISTS (
                SELECT 1 FROM jsonb_object_keys(p_shape) key
                WHERE key NOT IN ('radius','shadow')
            ) THEN RAISE EXCEPTION 'THEME_SHAPE_INVALID' USING ERRCODE='P0003'; END IF;
            next_palette:=current_theme.palette||coalesce(p_palette,'{{}}'::jsonb);
            next_typography:=current_theme.typography||coalesce(p_typography,'{{}}'::jsonb);
            next_layout:=current_theme.layout||coalesce(p_layout,'{{}}'::jsonb);
            next_shape:=current_theme.shape||coalesce(p_shape,'{{}}'::jsonb);
            PERFORM content.slaif_theme_validate_groups(
                next_palette,next_typography,next_layout,next_shape);
            changed:=next_palette IS DISTINCT FROM current_theme.palette
                OR next_typography IS DISTINCT FROM current_theme.typography
                OR next_layout IS DISTINCT FROM current_theme.layout
                OR next_shape IS DISTINCT FROM current_theme.shape;
            IF NOT changed THEN
                RETURN QUERY SELECT current_theme.id,current_theme.site_id,
                    current_theme.schema_version,current_theme.renderer_version,
                    current_theme.row_version,current_theme.palette,current_theme.typography,
                    current_theme.layout,current_theme.shape,current_theme.created_at,
                    current_theme.updated_at,true;
                RETURN;
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation')
            THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            IF NOT exists_row THEN
                INSERT INTO content.theme(
                    id,site_id,schema_version,renderer_version,row_version,
                    palette,typography,layout,shape,created_at,updated_at
                ) VALUES (
                    current_theme.id,current_theme.site_id,'theme-schema/v1','renderer-v1',
                    current_theme.row_version+1,next_palette,next_typography,next_layout,
                    next_shape,current_theme.created_at,now()
                );
            ELSE
                UPDATE content.theme AS t SET palette=next_palette,typography=next_typography,
                    layout=next_layout,shape=next_shape,row_version=t.row_version+1,
                    updated_at=now() WHERE t.site_id=p_site_id
                    AND t.row_version=p_expected;
                IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            END IF;
            RETURN QUERY SELECT t.id,t.site_id,t.schema_version,t.renderer_version,
                t.row_version,t.palette,t.typography,t.layout,t.shape,t.created_at,
                t.updated_at,false FROM content.theme t WHERE t.site_id=p_site_id;
        END;
        $fn$;
    """


def _resource_constraint_sql() -> str:
    return """
        DROP FUNCTION control.slaif_agent_resource_constraints(uuid);
        CREATE FUNCTION control.slaif_agent_resource_constraints(p_site_id uuid)
        RETURNS TABLE(
            allowed_type_ids uuid[], allowed_type_keys text[],
            max_content_types integer, max_fields_per_type integer,
            delete_enabled boolean, max_deletes integer,
            allowed_locales text[], route_prefix text,
            allowed_page_root_ids uuid[], max_visible_pages integer,
            max_page_depth integer, allowed_navigation_keys text[],
            allowed_navigation_ids uuid[], max_visible_locales integer,
            max_visible_navigations integer, max_visible_navigation_items integer,
            max_navigation_depth integer, max_visible_redirects integer,
            allowed_component_types text[], max_components_per_page integer,
            max_component_depth integer, max_visible_components integer,
            allowed_theme_palette_presets text[], allowed_theme_typography_families text[],
            allowed_theme_tokens text[]
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; result jsonb;
        BEGIN
            BEGIN workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END;
            IF workspace_id IS NULL OR NULLIF(current_setting('app.operation_id',true),'') IS NULL
            THEN RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END IF;
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            SELECT w.resource_constraints INTO result FROM control.workspace w
            JOIN control.site s ON s.id=w.site_id JOIN control.user_account a
              ON a.id=coalesce(w.delegator_id,w.created_by)
            WHERE w.id=workspace_id AND w.site_id=p_site_id AND w.status='ACTIVE'
              AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE';
            IF result IS NULL OR jsonb_typeof(result)<>'object' THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF EXISTS (SELECT 1 FROM jsonb_object_keys(result) key WHERE key NOT IN (
                'allowed_type_ids','allowed_type_keys','max_content_types','max_fields_per_type',
                'delete_enabled','max_deletes','allowed_locales','route_prefix','allowed_page_root_ids',
                'max_visible_pages','max_page_depth','allowed_navigation_keys','allowed_navigation_ids',
                'max_visible_locales','max_visible_navigations','max_visible_navigation_items',
                'max_navigation_depth','max_visible_redirects','allowed_component_types',
                'max_components_per_page','max_component_depth','max_visible_components',
                'allowed_theme_palette_presets','allowed_theme_typography_families','allowed_theme_tokens'
            )) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF EXISTS (SELECT 1 FROM (VALUES
                ('allowed_type_ids'),('allowed_type_keys'),('allowed_locales'),('allowed_page_root_ids'),
                ('allowed_navigation_keys'),('allowed_navigation_ids'),('allowed_component_types'),
                ('allowed_theme_palette_presets'),('allowed_theme_typography_families'),('allowed_theme_tokens')
            ) names(key) WHERE result ? names.key AND jsonb_typeof(result->names.key)<>'array')
            THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF EXISTS (SELECT 1 FROM (VALUES
                ('max_content_types'),('max_fields_per_type'),('max_deletes'),('max_visible_pages'),
                ('max_page_depth'),('max_visible_locales'),('max_visible_navigations'),
                ('max_visible_navigation_items'),('max_navigation_depth'),('max_visible_redirects'),
                ('max_components_per_page'),('max_component_depth'),('max_visible_components')
            ) names(key) WHERE result ? names.key
              AND (jsonb_typeof(result->names.key)<>'number' OR result->>names.key !~ '^[0-9]+$'))
            THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF jsonb_array_length(coalesce(result->'allowed_theme_palette_presets','[]'::jsonb))>3
               OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_theme_palette_presets','[]'::jsonb)) v WHERE v NOT IN ('ocean','meadow','ember'))
               OR jsonb_array_length(coalesce(result->'allowed_theme_typography_families','[]'::jsonb))>3
               OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_theme_typography_families','[]'::jsonb)) v WHERE v NOT IN ('system','serif','mono'))
               OR jsonb_array_length(coalesce(result->'allowed_theme_tokens','[]'::jsonb))>9
               OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_theme_tokens','[]'::jsonb)) v WHERE v NOT IN (
                    'palette.preset','typography.family','typography.scale','typography.weight',
                    'layout.content_width','layout.spacing','layout.grid_gap','shape.radius','shape.shadow'))
            THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            allowed_type_ids:=ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) value);
            allowed_type_keys:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_keys','[]'::jsonb)) value);
            max_content_types:=CASE WHEN result ? 'max_content_types' THEN (result->>'max_content_types')::integer END;
            max_fields_per_type:=CASE WHEN result ? 'max_fields_per_type' THEN (result->>'max_fields_per_type')::integer END;
            delete_enabled:=CASE WHEN result ? 'delete_enabled' THEN (result->>'delete_enabled')::boolean END;
            max_deletes:=CASE WHEN result ? 'max_deletes' THEN (result->>'max_deletes')::integer END;
            allowed_locales:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) value);
            route_prefix:=CASE WHEN result ? 'route_prefix' THEN result->>'route_prefix' END;
            allowed_page_root_ids:=ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_page_root_ids','[]'::jsonb)) value);
            max_visible_pages:=CASE WHEN result ? 'max_visible_pages' THEN (result->>'max_visible_pages')::integer END;
            max_page_depth:=CASE WHEN result ? 'max_page_depth' THEN (result->>'max_page_depth')::integer END;
            allowed_navigation_keys:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) value);
            allowed_navigation_ids:=ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_ids','[]'::jsonb)) value);
            max_visible_locales:=CASE WHEN result ? 'max_visible_locales' THEN (result->>'max_visible_locales')::integer END;
            max_visible_navigations:=CASE WHEN result ? 'max_visible_navigations' THEN (result->>'max_visible_navigations')::integer END;
            max_visible_navigation_items:=CASE WHEN result ? 'max_visible_navigation_items' THEN (result->>'max_visible_navigation_items')::integer END;
            max_navigation_depth:=CASE WHEN result ? 'max_navigation_depth' THEN (result->>'max_navigation_depth')::integer END;
            max_visible_redirects:=CASE WHEN result ? 'max_visible_redirects' THEN (result->>'max_visible_redirects')::integer END;
            allowed_component_types:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_component_types','[]'::jsonb)) value);
            max_components_per_page:=CASE WHEN result ? 'max_components_per_page' THEN (result->>'max_components_per_page')::integer END;
            max_component_depth:=CASE WHEN result ? 'max_component_depth' THEN (result->>'max_component_depth')::integer END;
            max_visible_components:=CASE WHEN result ? 'max_visible_components' THEN (result->>'max_visible_components')::integer END;
            allowed_theme_palette_presets:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_theme_palette_presets','[]'::jsonb)) value);
            allowed_theme_typography_families:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_theme_typography_families','[]'::jsonb)) value);
            allowed_theme_tokens:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_theme_tokens','[]'::jsonb)) value);
            RETURN NEXT;
        END;
        $fn$;
    """


def _semantic_completion_sql(*, include_theme: bool) -> str:
    theme_row = (
        """
                       ('THEME_UPDATED','theme','PATCH',200,'mutation'),
"""
        if include_theme
        else ""
    )
    return f"""
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid,p_workspace_id uuid,p_idempotency_key text,
            p_request_digest text,p_operation_id uuid,p_status_code integer,
            p_response_body jsonb,p_resource_type text,p_resource_id uuid,
            p_site_id uuid,p_action text,p_http_method text,p_quota_kind text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE expected_site uuid;
        BEGIN
            IF p_capability_id IS NULL OR p_workspace_id IS NULL
               OR p_idempotency_key IS NULL OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest IS NULL OR p_request_digest !~ '^[0-9a-f]{{64}}$'
               OR p_operation_id IS NULL OR p_resource_id IS NULL
               OR p_response_body IS NULL OR jsonb_typeof(p_response_body)<>'object'
               OR p_response_body->>'action' IS DISTINCT FROM p_action
               OR p_response_body->>'operation_id' IS DISTINCT FROM p_operation_id::text
               OR p_response_body->'record'->>'id' IS DISTINCT FROM p_resource_id::text
               OR NOT EXISTS (
                   SELECT 1 FROM (VALUES
                       ('CONTENT_TYPE_CREATED','content_type','POST',201,'mutation'),
                       ('FIELD_DEFINITION_CREATED','field_definition','POST',201,'mutation'),
                       ('CONTENT_ITEM_CREATED','content_item','POST',201,'mutation'),
                       ('CONTENT_ITEM_TRANSLATION_CREATED','content_item_translation','POST',201,'mutation'),
                       ('ITEM_RELATION_CREATED','item_relation','POST',201,'mutation'),
                       ('COLLECTION_VIEW_CREATED','collection_view','POST',201,'mutation'),
                       ('PAGE_CREATED','page','POST',201,'mutation'),
                       ('LOCALE_CREATED','locale','POST',201,'mutation'),
                       ('NAVIGATION_CREATED','navigation','POST',201,'mutation'),
                       ('NAVIGATION_ITEM_CREATED','navigation_item','POST',201,'mutation'),
                       ('REDIRECT_CREATED','redirect','POST',201,'mutation'),
                       ('COMPONENT_CREATED','composition_node','POST',201,'mutation'),
                       ('CONTENT_TYPE_UPDATED','content_type','PATCH',200,'mutation'),
                       ('FIELD_DEFINITION_UPDATED','field_definition','PATCH',200,'mutation'),
                       ('CONTENT_ITEM_UPDATED','content_item','PATCH',200,'mutation'),
                       ('CONTENT_ITEM_TRANSLATION_UPDATED','content_item_translation','PATCH',200,'mutation'),
                       ('ITEM_RELATION_UPDATED','item_relation','PATCH',200,'mutation'),
                       ('COLLECTION_VIEW_UPDATED','collection_view','PATCH',200,'mutation'),
                       ('PAGE_UPDATED','page','PATCH',200,'mutation'),
                       ('LOCALE_UPDATED','locale','PATCH',200,'mutation'),
                       ('NAVIGATION_UPDATED','navigation','PATCH',200,'mutation'),
                       ('NAVIGATION_ITEM_UPDATED','navigation_item','PATCH',200,'mutation'),
                       ('REDIRECT_UPDATED','redirect','PATCH',200,'mutation'),
                       ('COMPONENT_UPDATED','composition_node','PATCH',200,'mutation'),
{theme_row}                       ('CONTENT_TYPE_DELETED','content_type','DELETE',200,'delete'),
                       ('FIELD_DEFINITION_DELETED','field_definition','DELETE',200,'delete'),
                       ('CONTENT_ITEM_DELETED','content_item','DELETE',200,'delete'),
                       ('CONTENT_ITEM_TRANSLATION_DELETED','content_item_translation','DELETE',200,'delete'),
                       ('ITEM_RELATION_DELETED','item_relation','DELETE',200,'delete'),
                       ('COLLECTION_VIEW_DELETED','collection_view','DELETE',200,'delete'),
                       ('PAGE_DELETED','page','DELETE',200,'delete'),
                       ('LOCALE_DELETED','locale','DELETE',200,'delete'),
                       ('NAVIGATION_DELETED','navigation','DELETE',200,'delete'),
                       ('NAVIGATION_ITEM_DELETED','navigation_item','DELETE',200,'delete'),
                       ('REDIRECT_DELETED','redirect','DELETE',200,'delete'),
                       ('COMPONENT_DELETED','composition_node','DELETE',200,'delete'),
                       ('PAGE_MOVED','page','POST',200,'mutation'),
                       ('PAGE_RESTORED','page','POST',200,'mutation'),
                       ('NAVIGATION_ITEM_MOVED','navigation_item','POST',200,'mutation'),
                       ('COMPONENT_MOVED','composition_node','POST',200,'mutation')
                   ) AS allowed(action,resource_type,http_method,response_status,quota_kind)
                   WHERE allowed.action=p_action AND allowed.resource_type=p_resource_type
                     AND allowed.http_method=p_http_method AND allowed.response_status=p_status_code
                     AND allowed.quota_kind=p_quota_kind
               )
            THEN RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001'; END IF;
            SELECT w.site_id INTO expected_site FROM control.capability c
            JOIN control.workspace w ON w.id=c.workspace_id
            WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id AND w.site_id=p_site_id;
            IF expected_site IS NULL THEN RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001'; END IF;
            UPDATE control.agent_idempotency SET status_code=p_status_code,
                response_body=p_response_body,resource_type=p_resource_type,
                resource_id=p_resource_id,completed_at=CURRENT_TIMESTAMP
            WHERE capability_id=p_capability_id AND workspace_id=p_workspace_id
              AND idempotency_key=p_idempotency_key AND request_digest=p_request_digest
              AND operation_id=p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            INSERT INTO audit.agent_mutation(operation_id,capability_id,workspace_id,site_id,
                resource_type,resource_id,request_digest,response_status,action,http_method,quota_kind)
            VALUES(p_operation_id,p_capability_id,p_workspace_id,p_site_id,p_resource_type,
                p_resource_id,p_request_digest,p_status_code,p_action,p_http_method,p_quota_kind);
        END;
        $fn$;
    """


def _semantic_constraint_sql(*, include_theme: bool) -> str:
    theme_clause = (
        """
        OR (action='THEME_UPDATED' AND resource_type='theme' AND http_method='PATCH'
            AND response_status=200 AND quota_kind='mutation')
"""
        if include_theme
        else ""
    )
    return f"""
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED','REDIRECT_CREATED','COMPONENT_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED','REDIRECT_UPDATED','COMPONENT_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
{theme_clause}            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED','REDIRECT_DELETED','COMPONENT_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED','COMPONENT_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
        )
    """


def _no_effect_completion_sql(*, include_theme: bool) -> str:
    theme = ", 'theme'" if include_theme else ""
    return f"""
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            p_capability_id uuid,p_workspace_id uuid,p_idempotency_key text,
            p_request_digest text,p_operation_id uuid,p_status_code integer,
            p_response_body jsonb,p_resource_type text,p_resource_id uuid,
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE expected_site uuid;
        BEGIN
            SELECT workspace.site_id INTO expected_site FROM control.capability capability
            JOIN control.workspace workspace ON workspace.id=capability.workspace_id
            WHERE capability.id=p_capability_id AND capability.workspace_id=p_workspace_id
              AND workspace.site_id=p_site_id;
            IF expected_site IS NULL OR p_status_code NOT BETWEEN 200 AND 299
               OR p_response_body IS NULL OR p_resource_id IS NULL
               OR p_resource_type NOT IN ('content_type','field_definition','content_item',
                   'page','composition_node'{theme})
            THEN RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION' USING ERRCODE='P0001'; END IF;
            UPDATE control.agent_idempotency SET status_code=p_status_code,
                response_body=p_response_body,resource_type=p_resource_type,
                resource_id=p_resource_id,completed_at=current_timestamp
            WHERE capability_id=p_capability_id AND workspace_id=p_workspace_id
              AND idempotency_key=p_idempotency_key AND request_digest=p_request_digest
              AND operation_id=p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND'
                USING ERRCODE='P0002'; END IF;
        END;
        $fn$;
        ALTER FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid) TO slaif_agent_runtime;
    """


def _drop_cow_for_upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE kind char; pending boolean;
        BEGIN
            SELECT c.relkind INTO kind FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='theme';
            IF kind='v' THEN
                SELECT EXISTS (
                    SELECT 1 FROM pg_catalog.pg_class c
                    JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='content' AND c.relname='theme_changes'
                ) INTO pending;
                IF pending THEN
                    EXECUTE 'SELECT EXISTS (SELECT 1 FROM content.theme_changes)'
                        INTO pending;
                    IF pending THEN
                        RAISE EXCEPTION 'THEME_MIGRATION_PENDING_COW'
                            USING ERRCODE='P0001';
                    END IF;
                END IF;
                IF pg_catalog.to_regprocedure('agentcow.teardown_cow(text,text)') IS NULL THEN
                    RAISE EXCEPTION 'THEME_MIGRATION_REQUIRES_FOUNDATION'
                        USING ERRCODE='P0001';
                END IF;
                PERFORM agentcow.teardown_cow('content','theme');
                EXECUTE 'ALTER TABLE content.theme_base RENAME TO theme';
            END IF;
        END $$;
        """
    )


def _backfill() -> None:
    _execute_block(
        """
        ALTER TABLE content.theme
            ADD COLUMN IF NOT EXISTS schema_version text NOT NULL DEFAULT 'theme-schema/v1',
            ADD COLUMN IF NOT EXISTS renderer_version text NOT NULL DEFAULT 'renderer-v1',
            ADD COLUMN IF NOT EXISTS row_version integer NOT NULL DEFAULT 1
        """
    )
    op.execute(
        """
        DO $$
        DECLARE row_data record; normalized_palette jsonb; normalized_typography jsonb;
            normalized_layout jsonb; normalized_shape jsonb;
        BEGIN
            FOR row_data IN SELECT * FROM content.theme LOOP
                IF jsonb_typeof(row_data.palette)<>'object'
                   OR jsonb_typeof(row_data.typography)<>'object'
                   OR jsonb_typeof(row_data.layout)<>'object'
                   OR jsonb_typeof(row_data.shape)<>'object'
                THEN RAISE EXCEPTION 'THEME_UPGRADE_INVALID'; END IF;
                normalized_palette:='{"preset":"ocean"}'::jsonb||row_data.palette;
                normalized_typography:='{"family":"system","scale":"balanced","weight":"regular"}'::jsonb||row_data.typography;
                normalized_layout:='{"content_width":"md","spacing":"md","grid_gap":"md"}'::jsonb||row_data.layout;
                normalized_shape:='{"radius":"md","shadow":"sm"}'::jsonb||row_data.shape;
                PERFORM content.slaif_theme_validate_groups(
                    normalized_palette,normalized_typography,normalized_layout,normalized_shape);
                UPDATE content.theme SET palette=normalized_palette,typography=normalized_typography,
                    layout=normalized_layout,shape=normalized_shape,schema_version='theme-schema/v1',
                    renderer_version='renderer-v1',row_version=GREATEST(row_data.row_version,1)
                WHERE id=row_data.id;
            END LOOP;
        END $$
        """
    )
    op.execute(
        """
        ALTER TABLE content.theme
            ADD CONSTRAINT theme_schema_version_exact CHECK (schema_version='theme-schema/v1'),
            ADD CONSTRAINT theme_renderer_version_exact CHECK (renderer_version='renderer-v1'),
            ADD CONSTRAINT theme_row_version_positive CHECK (row_version>0)
        """
    )


def upgrade() -> None:
    _drop_cow_for_upgrade()
    _execute_block(_validate_sql())
    _backfill()
    _execute_block(_default_sql())
    _execute_block(_legacy_sql())
    _execute_block(_agent_read_sql())
    _execute_block(_agent_update_sql())
    _execute_block(_resource_constraint_sql())
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql(include_theme=True))
    _execute_block(_semantic_completion_sql(include_theme=True))
    op.execute(
        "ALTER FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) TO slaif_agent_runtime"
    )
    for function in (
        "content.slaif_theme_validate_groups(jsonb,jsonb,jsonb,jsonb)",
        "content.slaif_theme_default(uuid)",
        "content.slaif_theme_project(uuid)",
        "content.slaif_agent_theme_get(uuid)",
        "content.slaif_agent_theme_update(uuid,integer,jsonb,jsonb,jsonb,jsonb,boolean)",
        "control.slaif_agent_resource_constraints(uuid)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_theme_get(uuid),"
        "content.slaif_agent_theme_update(uuid,integer,jsonb,jsonb,jsonb,jsonb,boolean) "
        "TO slaif_agent_runtime"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_theme_get(uuid),"
        "content.slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb) "
        "TO slaif_editor_runtime, slaif_control"
    )
    # The no-effect idempotency boundary introduced by 061 is extended to the
    # theme resource without changing its signature or older semantics.
    _execute_block(_no_effect_completion_sql(include_theme=True))


def downgrade() -> None:
    # Pending COW state must never be discarded while restoring the legacy
    # representation.
    _drop_cow_for_upgrade()
    _execute_block(
        """
        DROP FUNCTION IF EXISTS content.slaif_agent_theme_update(
            uuid,integer,jsonb,jsonb,jsonb,jsonb,boolean
        ) CASCADE;
        DROP FUNCTION IF EXISTS content.slaif_agent_theme_get(uuid) CASCADE;
        DROP FUNCTION IF EXISTS content.slaif_theme_project(uuid) CASCADE;
        DROP FUNCTION IF EXISTS content.slaif_theme_default(uuid) CASCADE;
        DROP FUNCTION IF EXISTS content.slaif_theme_validate_groups(
            jsonb,jsonb,jsonb,jsonb
        ) CASCADE;
        DROP FUNCTION IF EXISTS control.slaif_agent_resource_constraints(uuid) CASCADE;
        ALTER TABLE content.theme
            DROP CONSTRAINT IF EXISTS theme_schema_version_exact,
            DROP CONSTRAINT IF EXISTS theme_renderer_version_exact,
            DROP CONSTRAINT IF EXISTS theme_row_version_positive,
            DROP COLUMN IF EXISTS schema_version,
            DROP COLUMN IF EXISTS renderer_version,
            DROP COLUMN IF EXISTS row_version;
        """
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql(include_theme=False))
    _execute_block(_semantic_completion_sql(include_theme=False))
    _execute_block(_no_effect_completion_sql(include_theme=False))
    # Recreate the exact pre-062 resource function from 050/060 by replaying
    # the current migration's historical implementation through a small
    # compatibility wrapper; its output shape is restored by migration 060 on
    # a full downgrade.  The immediate downgrade remains data-bearing and
    # leaves the legacy theme rows intact.
    _execute_block(
        """
        CREATE FUNCTION control.slaif_agent_resource_constraints(p_site_id uuid)
        RETURNS TABLE(
            allowed_type_ids uuid[], allowed_type_keys text[], max_content_types integer,
            max_fields_per_type integer, delete_enabled boolean, max_deletes integer,
            allowed_locales text[], route_prefix text, allowed_page_root_ids uuid[],
            max_visible_pages integer, max_page_depth integer, allowed_navigation_keys text[],
            allowed_navigation_ids uuid[], max_visible_locales integer,
            max_visible_navigations integer, max_visible_navigation_items integer,
            max_navigation_depth integer, max_visible_redirects integer,
            allowed_component_types text[], max_components_per_page integer,
            max_component_depth integer, max_visible_components integer
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; result jsonb;
        BEGIN
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            SELECT w.resource_constraints INTO result FROM control.workspace w
            WHERE w.id=workspace_id AND w.site_id=p_site_id AND w.status='ACTIVE';
            IF result IS NULL OR jsonb_typeof(result)<>'object' THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            allowed_type_ids:=ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) value);
            allowed_type_keys:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_keys','[]'::jsonb)) value);
            max_content_types:=NULLIF(result->>'max_content_types','')::integer;
            max_fields_per_type:=NULLIF(result->>'max_fields_per_type','')::integer;
            delete_enabled:=NULLIF(result->>'delete_enabled','')::boolean;
            max_deletes:=NULLIF(result->>'max_deletes','')::integer;
            allowed_locales:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) value);
            route_prefix:=result->>'route_prefix';
            allowed_page_root_ids:=ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_page_root_ids','[]'::jsonb)) value);
            max_visible_pages:=NULLIF(result->>'max_visible_pages','')::integer;
            max_page_depth:=NULLIF(result->>'max_page_depth','')::integer;
            allowed_navigation_keys:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) value);
            allowed_navigation_ids:=ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_ids','[]'::jsonb)) value);
            max_visible_locales:=NULLIF(result->>'max_visible_locales','')::integer;
            max_visible_navigations:=NULLIF(result->>'max_visible_navigations','')::integer;
            max_visible_navigation_items:=NULLIF(result->>'max_visible_navigation_items','')::integer;
            max_navigation_depth:=NULLIF(result->>'max_navigation_depth','')::integer;
            max_visible_redirects:=NULLIF(result->>'max_visible_redirects','')::integer;
            allowed_component_types:=ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_component_types','[]'::jsonb)) value);
            max_components_per_page:=NULLIF(result->>'max_components_per_page','')::integer;
            max_component_depth:=NULLIF(result->>'max_component_depth','')::integer;
            max_visible_components:=NULLIF(result->>'max_visible_components','')::integer;
            RETURN NEXT;
        END;
        $fn$;
        ALTER FUNCTION control.slaif_agent_resource_constraints(uuid) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION control.slaif_agent_resource_constraints(uuid) FROM PUBLIC;
        """
    )
    # Restore the exact legacy wrappers from 020, including the old open JSON
    # representation, while retaining the existing rows and timestamps.
    _execute_block(
        """
        CREATE OR REPLACE FUNCTION content.slaif_theme_get(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,palette jsonb,typography jsonb,
            layout jsonb,shape jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.theme (site_id) VALUES (p_site_id)
                ON CONFLICT (site_id) DO NOTHING;
            RETURN QUERY SELECT t.id,t.site_id,t.palette,t.typography,t.layout,t.shape,
                t.created_at,t.updated_at FROM content.theme t WHERE t.site_id=p_site_id;
        END; $fn$;
        CREATE OR REPLACE FUNCTION content.slaif_theme_update(
            p_site_id uuid,p_palette jsonb,p_typography jsonb,p_layout jsonb,p_shape jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,palette jsonb,typography jsonb,
            layout jsonb,shape jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM content.slaif_theme_get(p_site_id);
            UPDATE content.theme SET palette=coalesce(p_palette,palette),
                typography=coalesce(p_typography,typography),layout=coalesce(p_layout,layout),
                shape=coalesce(p_shape,shape),updated_at=current_timestamp
            WHERE site_id=p_site_id;
            RETURN QUERY SELECT t.id,t.site_id,t.palette,t.typography,t.layout,t.shape,
                t.created_at,t.updated_at FROM content.theme t WHERE t.site_id=p_site_id;
        END; $fn$;
        ALTER FUNCTION content.slaif_theme_get(uuid) OWNER TO slaif_owner;
        ALTER FUNCTION content.slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION content.slaif_theme_get(uuid),content.slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION content.slaif_theme_get(uuid),content.slaif_theme_update(uuid,jsonb,jsonb,jsonb,jsonb) TO slaif_editor_runtime,slaif_control;
        """
    )

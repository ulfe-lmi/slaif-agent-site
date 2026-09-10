# ruff: noqa: E501
"""Add bounded per-page theme-token overrides over the accepted site theme."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "066_001"
down_revision: str | Sequence[str] | None = "065_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PAGE_STYLE_COLUMNS = """
    id uuid, page_id uuid, site_id uuid, schema_version text, row_version integer,
    overrides jsonb, resolved jsonb, created_at timestamptz, updated_at timestamptz
"""


def _execute_block(sql: str) -> None:
    statement: list[str] = []
    in_function_body = False
    for line in sql.splitlines(keepends=True):
        statement.append(line)
        if line.count("$fn$") % 2:
            in_function_body = not in_function_body
        if line.rstrip().endswith(";") and not in_function_body:
            op.execute("".join(statement))
            statement = []
    if "".join(statement).strip():
        op.execute("".join(statement))


def _drop_cow_for_page_change() -> None:
    """Refuse to discard pending workspace state before changing page columns."""

    op.execute(
        """
        DO $guard$
        DECLARE relation_kind char; pending boolean;
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='page';
            IF relation_kind='v' THEN
                SELECT EXISTS (
                    SELECT 1 FROM pg_catalog.pg_class c
                    JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='content' AND c.relname='page_changes'
                ) INTO pending;
                IF pending THEN
                    EXECUTE 'SELECT EXISTS (SELECT 1 FROM content.page_changes)'
                        INTO pending;
                    IF pending THEN
                        RAISE EXCEPTION 'PAGE_STYLE_MIGRATION_PENDING_COW'
                            USING ERRCODE='P0001';
                    END IF;
                END IF;
                IF pg_catalog.to_regprocedure('agentcow.teardown_cow(text,text)') IS NULL THEN
                    RAISE EXCEPTION 'PAGE_STYLE_MIGRATION_REQUIRES_FOUNDATION'
                        USING ERRCODE='P0001';
                END IF;
                PERFORM agentcow.teardown_cow('content','page');
                EXECUTE 'ALTER TABLE content.page_base RENAME TO page';
            END IF;
        END $guard$;
        """
    )


def _style_data_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_page_style_overrides_valid(p_overrides jsonb)
        RETURNS boolean LANGUAGE sql IMMUTABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT jsonb_typeof(p_overrides)='object'
               AND NOT EXISTS (
                   SELECT 1 FROM jsonb_object_keys(p_overrides) key
                   WHERE key NOT IN ('palette','typography','layout','shape')
               )
               AND NOT EXISTS (
                   SELECT 1 FROM jsonb_each(p_overrides) item
                   WHERE (item.key='palette' AND (
                       jsonb_typeof(item.value) IS DISTINCT FROM 'object'
                       OR (SELECT count(*) FROM jsonb_object_keys(item.value))<>1
                       OR NOT item.value ? 'preset'
                       OR jsonb_typeof(item.value->'preset') IS DISTINCT FROM 'string'
                       OR item.value->>'preset' NOT IN ('ocean','meadow','ember')
                   )) OR (item.key='typography' AND (
                       jsonb_typeof(item.value) IS DISTINCT FROM 'object'
                       OR (SELECT count(*) FROM jsonb_object_keys(item.value))=0
                       OR EXISTS (SELECT 1 FROM jsonb_object_keys(item.value) key
                           WHERE key NOT IN ('family','scale','weight'))
                       OR EXISTS (SELECT 1 FROM jsonb_each(item.value) value
                           WHERE (value.key='family' AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('system','serif','mono')))
                              OR (value.key='scale' AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('compact','balanced','spacious')))
                              OR (value.key='weight' AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('regular','medium','bold'))))
                   )) OR (item.key='layout' AND (
                       jsonb_typeof(item.value) IS DISTINCT FROM 'object'
                       OR (SELECT count(*) FROM jsonb_object_keys(item.value))=0
                       OR EXISTS (SELECT 1 FROM jsonb_object_keys(item.value) key
                           WHERE key NOT IN ('content_width','spacing','grid_gap'))
                       OR EXISTS (SELECT 1 FROM jsonb_each(item.value) value
                           WHERE (value.key='content_width' AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('sm','md','lg','xl')))
                              OR (value.key IN ('spacing','grid_gap') AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('sm','md','lg'))))
                   )) OR (item.key='shape' AND (
                       jsonb_typeof(item.value) IS DISTINCT FROM 'object'
                       OR (SELECT count(*) FROM jsonb_object_keys(item.value))=0
                       OR EXISTS (SELECT 1 FROM jsonb_object_keys(item.value) key
                           WHERE key NOT IN ('radius','shadow'))
                       OR EXISTS (SELECT 1 FROM jsonb_each(item.value) value
                           WHERE (value.key='radius' AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('none','sm','md','lg','full')))
                              OR (value.key='shadow' AND (
                               jsonb_typeof(value.value) IS DISTINCT FROM 'string'
                               OR value.value #>> '{{}}' NOT IN ('none','sm','md','lg'))))
                   ))
               )
        $fn$;

        CREATE FUNCTION content.slaif_page_style_resolved(
            p_site_id uuid, p_overrides jsonb
        ) RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE current_theme record; resolved jsonb;
        BEGIN
            IF NOT content.slaif_page_style_overrides_valid(coalesce(p_overrides,'{{}}'::jsonb))
            THEN RAISE EXCEPTION 'PAGE_STYLE_INVALID' USING ERRCODE='P0003'; END IF;
            SELECT * INTO current_theme FROM content.slaif_theme_project(p_site_id);
            IF current_theme.id IS NULL THEN
                RAISE EXCEPTION 'THEME_SITE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            resolved:=jsonb_build_object(
                'id',current_theme.id,'site_id',current_theme.site_id,
                'schema_version',current_theme.schema_version,
                'renderer_version',current_theme.renderer_version,
                'row_version',current_theme.row_version,
                'palette',current_theme.palette||coalesce(p_overrides->'palette','{{}}'::jsonb),
                'typography',current_theme.typography||coalesce(p_overrides->'typography','{{}}'::jsonb),
                'layout',current_theme.layout||coalesce(p_overrides->'layout','{{}}'::jsonb),
                'shape',current_theme.shape||coalesce(p_overrides->'shape','{{}}'::jsonb),
                'created_at',current_theme.created_at,'updated_at',current_theme.updated_at);
            PERFORM content.slaif_theme_validate_groups(
                resolved->'palette',resolved->'typography',resolved->'layout',resolved->'shape');
            RETURN resolved;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_page_style_project(p_page_id uuid)
        RETURNS TABLE({_PAGE_STYLE_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT p.id,p.id,p.site_id,'page-style/v1',p.row_version,p.style_overrides,
                content.slaif_page_style_resolved(p.site_id,p.style_overrides),
                p.created_at,p.updated_at
            FROM content.page p
            WHERE p.id=p_page_id AND p.deleted_at IS NULL
        $fn$;

        CREATE FUNCTION content.slaif_page_style_get(p_site_id uuid,p_page_id uuid)
        RETURNS TABLE({_PAGE_STYLE_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT * FROM content.slaif_page_style_project(p_page_id)
            WHERE site_id=p_site_id
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_style_get(
            p_site_id uuid,p_page_id uuid
        ) RETURNS TABLE({_PAGE_STYLE_COLUMNS})
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'page:read');
            IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id) THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            RETURN QUERY SELECT * FROM content.slaif_page_style_get(p_site_id,p_page_id);
        END;
        $fn$;

        CREATE FUNCTION content.slaif_page_style_apply(
            p_site_id uuid,p_page_id uuid,p_expected integer,
            p_palette jsonb,p_typography jsonb,p_layout jsonb,p_shape jsonb,
            p_reset_tokens text[],p_agent boolean
        ) RETURNS TABLE({_PAGE_STYLE_COLUMNS}, no_effect boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE page_row record; current_theme record; constraints jsonb;
            capability_id uuid; workspace_id uuid; current_overrides jsonb;
            next_overrides jsonb; resolved jsonb; group_value jsonb;
            group_name text; token_key text; token text; selected text;
            reset_tokens text[]; changed boolean:=false;
        BEGIN
            BEGIN
                workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF workspace_id IS NULL OR NULLIF(current_setting('app.operation_id',true),'') IS NULL
            THEN RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END IF;
            IF p_agent AND (p_expected IS NULL OR p_expected<=0) THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            PERFORM pg_advisory_xact_lock_shared(hashtextextended(workspace_id::text,280));
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||chr(58)||p_site_id::text||chr(58)||'page-structure',994));
            -- Page-style resolution reads the site theme more than once while
            -- applying a raw override. Serialize that read against a theme
            -- mutation after the lifecycle and structure barriers, so the
            -- returned effective state has one theme serialization point.
            PERFORM pg_advisory_xact_lock_shared(hashtextextended(
                workspace_id::text||chr(58)||p_site_id::text||chr(58)||'theme',995));
            IF p_agent THEN
                capability_id:=control.slaif_agent_require_capability(p_site_id,'page:read');
                IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id) THEN
                    RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
                END IF;
            END IF;
            SELECT p.* INTO page_row FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF p_expected IS NOT NULL AND page_row.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            current_overrides:=coalesce(page_row.style_overrides,'{{}}'::jsonb);
            IF NOT content.slaif_page_style_overrides_valid(current_overrides) THEN
                RAISE EXCEPTION 'PAGE_STYLE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_palette IS NOT NULL AND (
                jsonb_typeof(p_palette) IS DISTINCT FROM 'object'
                OR EXISTS (SELECT 1 FROM jsonb_object_keys(p_palette) key
                    WHERE key NOT IN ('preset'))
            ) THEN RAISE EXCEPTION 'PAGE_STYLE_PALETTE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_typography IS NOT NULL AND (
                jsonb_typeof(p_typography) IS DISTINCT FROM 'object'
                OR EXISTS (SELECT 1 FROM jsonb_object_keys(p_typography) key
                    WHERE key NOT IN ('family','scale','weight'))
            ) THEN RAISE EXCEPTION 'PAGE_STYLE_TYPOGRAPHY_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_layout IS NOT NULL AND (
                jsonb_typeof(p_layout) IS DISTINCT FROM 'object'
                OR EXISTS (SELECT 1 FROM jsonb_object_keys(p_layout) key
                    WHERE key NOT IN ('content_width','spacing','grid_gap'))
            ) THEN RAISE EXCEPTION 'PAGE_STYLE_LAYOUT_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_shape IS NOT NULL AND (
                jsonb_typeof(p_shape) IS DISTINCT FROM 'object'
                OR EXISTS (SELECT 1 FROM jsonb_object_keys(p_shape) key
                    WHERE key NOT IN ('radius','shadow'))
            ) THEN RAISE EXCEPTION 'PAGE_STYLE_SHAPE_INVALID' USING ERRCODE='P0003'; END IF;
            reset_tokens:=coalesce(p_reset_tokens,ARRAY[]::text[]);
            IF cardinality(reset_tokens)<>cardinality(
                ARRAY(SELECT DISTINCT value FROM unnest(reset_tokens) value))
            THEN RAISE EXCEPTION 'PAGE_STYLE_RESET_INVALID' USING ERRCODE='P0003'; END IF;
            IF EXISTS (SELECT 1 FROM unnest(reset_tokens) value WHERE value NOT IN (
                'palette.preset','typography.family','typography.scale','typography.weight',
                'layout.content_width','layout.spacing','layout.grid_gap','shape.radius','shape.shadow'))
            THEN RAISE EXCEPTION 'PAGE_STYLE_RESET_INVALID' USING ERRCODE='P0003'; END IF;
            IF coalesce(p_palette ? 'preset',false)
                   AND 'palette.preset'=ANY(reset_tokens)
               OR EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(p_typography,'{{}}'::jsonb)) key
                   WHERE ('typography.'||key)=ANY(reset_tokens))
               OR EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(p_layout,'{{}}'::jsonb)) key
                   WHERE ('layout.'||key)=ANY(reset_tokens))
               OR EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(p_shape,'{{}}'::jsonb)) key
                   WHERE ('shape.'||key)=ANY(reset_tokens))
            THEN RAISE EXCEPTION 'PAGE_STYLE_RESET_OVERLAP' USING ERRCODE='P0003'; END IF;
            IF NOT (coalesce(p_palette ? 'preset',false)
                OR coalesce(p_typography ?| ARRAY['family','scale','weight'],false)
                OR coalesce(p_layout ?| ARRAY['content_width','spacing','grid_gap'],false)
                OR coalesce(p_shape ?| ARRAY['radius','shadow'],false)
                OR cardinality(reset_tokens)>0)
            THEN RAISE EXCEPTION 'PAGE_STYLE_UPDATE_EMPTY' USING ERRCODE='P0003'; END IF;
            next_overrides:=current_overrides;
            FOREACH token IN ARRAY reset_tokens LOOP
                group_name:=split_part(token,'.',1); token_key:=split_part(token,'.',2);
                group_value:=coalesce(next_overrides->group_name,'{{}}'::jsonb)-token_key;
                IF group_value='{{}}'::jsonb THEN
                    next_overrides:=next_overrides-group_name;
                ELSE
                    next_overrides:=jsonb_set(next_overrides,ARRAY[group_name],group_value,true);
                END IF;
            END LOOP;
            IF p_palette ? 'preset' THEN
                next_overrides:=jsonb_set(next_overrides,ARRAY['palette'],
                    coalesce(next_overrides->'palette','{{}}'::jsonb)||p_palette,true);
            END IF;
            IF p_typography ?| ARRAY['family','scale','weight'] THEN
                next_overrides:=jsonb_set(next_overrides,ARRAY['typography'],
                    coalesce(next_overrides->'typography','{{}}'::jsonb)||p_typography,true);
            END IF;
            IF p_layout ?| ARRAY['content_width','spacing','grid_gap'] THEN
                next_overrides:=jsonb_set(next_overrides,ARRAY['layout'],
                    coalesce(next_overrides->'layout','{{}}'::jsonb)||p_layout,true);
            END IF;
            IF p_shape ?| ARRAY['radius','shadow'] THEN
                next_overrides:=jsonb_set(next_overrides,ARRAY['shape'],
                    coalesce(next_overrides->'shape','{{}}'::jsonb)||p_shape,true);
            END IF;
            IF NOT content.slaif_page_style_overrides_valid(next_overrides) THEN
                RAISE EXCEPTION 'PAGE_STYLE_INVALID' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO current_theme FROM content.slaif_theme_project(p_site_id);
            IF current_theme.id IS NULL THEN
                RAISE EXCEPTION 'THEME_SITE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            resolved:=content.slaif_page_style_resolved(p_site_id,next_overrides);
            FOREACH group_name IN ARRAY ARRAY['palette','typography','layout','shape'] LOOP
                FOR token_key IN
                    SELECT value FROM unnest(CASE group_name
                        WHEN 'palette' THEN ARRAY['preset']::text[]
                        WHEN 'typography' THEN ARRAY['family','scale','weight']::text[]
                        WHEN 'layout' THEN ARRAY['content_width','spacing','grid_gap']::text[]
                        ELSE ARRAY['radius','shadow']::text[] END) value
                LOOP
                IF (current_overrides->group_name->token_key)
                    IS DISTINCT FROM (next_overrides->group_name->token_key) THEN
                    changed:=true;
                    IF p_agent THEN
                        token:=group_name||'.'||token_key;
                        SELECT to_jsonb(resource_constraints) INTO constraints
                        FROM control.slaif_agent_resource_constraints(p_site_id)
                            resource_constraints;
                        IF jsonb_typeof(constraints->'allowed_theme_tokens')='array'
                           AND jsonb_array_length(constraints->'allowed_theme_tokens')>0
                           AND NOT (constraints->'allowed_theme_tokens' ? token)
                        THEN RAISE EXCEPTION 'AGENT_RESOURCE_PAGE_STYLE_TOKEN_DENIED'
                            USING ERRCODE='P0007'; END IF;
                        selected:=resolved #>> ARRAY[group_name,token_key];
                        IF group_name='palette'
                           AND jsonb_typeof(constraints->'allowed_theme_palette_presets')='array'
                           AND jsonb_array_length(constraints->'allowed_theme_palette_presets')>0
                           AND NOT (constraints->'allowed_theme_palette_presets' ? selected)
                        THEN RAISE EXCEPTION 'AGENT_RESOURCE_THEME_PALETTE_DENIED'
                            USING ERRCODE='P0007'; END IF;
                        IF group_name='typography' AND token_key='family'
                           AND jsonb_typeof(constraints->'allowed_theme_typography_families')='array'
                           AND jsonb_array_length(constraints->'allowed_theme_typography_families')>0
                           AND NOT (constraints->'allowed_theme_typography_families' ? selected)
                        THEN RAISE EXCEPTION 'AGENT_RESOURCE_THEME_TYPOGRAPHY_DENIED'
                            USING ERRCODE='P0007'; END IF;
                    END IF;
                END IF;
                END LOOP;
            END LOOP;
            IF NOT changed THEN
                RETURN QUERY SELECT page_row.id,page_row.id,page_row.site_id,'page-style/v1',
                    page_row.row_version,current_overrides,resolved,
                    page_row.created_at,page_row.updated_at,true;
                RETURN;
            END IF;
            IF p_agent THEN
                PERFORM control.slaif_agent_require_capability(p_site_id,'page-style:write');
                IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation')
                THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            END IF;
            UPDATE content.page p SET style_overrides=next_overrides,
                row_version=p.row_version+1,updated_at=now()
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL
              AND (p_expected IS NULL OR p.row_version=p_expected);
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT p.id,p.id,p.site_id,'page-style/v1',p.row_version,
                p.style_overrides,content.slaif_page_style_resolved(p.site_id,p.style_overrides),
                p.created_at,p.updated_at,false FROM content.page p
                WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_page_style_update(
            p_site_id uuid,p_page_id uuid,p_expected integer,
            p_palette jsonb,p_typography jsonb,p_layout jsonb,p_shape jsonb,
            p_reset_tokens text[]
        ) RETURNS TABLE({_PAGE_STYLE_COLUMNS})
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT applied.id,applied.page_id,applied.site_id,
                applied.schema_version,applied.row_version,applied.overrides,
                applied.resolved,applied.created_at,applied.updated_at
            FROM content.slaif_page_style_apply(
                p_site_id,p_page_id,p_expected,p_palette,p_typography,p_layout,p_shape,
                p_reset_tokens,false) AS applied;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_style_update(
            p_site_id uuid,p_page_id uuid,p_expected integer,
            p_palette jsonb,p_typography jsonb,p_layout jsonb,p_shape jsonb,
            p_reset_tokens text[]
        ) RETURNS TABLE({_PAGE_STYLE_COLUMNS}, no_effect boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_page_style_apply(
                p_site_id,p_page_id,p_expected,p_palette,p_typography,p_layout,p_shape,
                p_reset_tokens,true);
        END;
        $fn$;
    """


def _semantic_completion_sql(*, include_style: bool) -> str:
    style_row = (
        "                       ('PAGE_STYLE_UPDATED','page_style','PATCH',200,'mutation'),\n"
        if include_style
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
               OR NOT EXISTS (SELECT 1 FROM (VALUES
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
{style_row}                       ('THEME_UPDATED','theme','PATCH',200,'mutation'),
                       ('CONTENT_TYPE_DELETED','content_type','DELETE',200,'delete'),
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
                     AND allowed.quota_kind=p_quota_kind)
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


def _semantic_constraint_sql(*, include_style: bool) -> str:
    style_clause = (
        "            OR (action='PAGE_STYLE_UPDATED' AND resource_type='page_style' AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')\n"
        if include_style
        else ""
    )
    return f"""
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED','REDIRECT_CREATED','COMPONENT_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED','REDIRECT_UPDATED','COMPONENT_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
{style_clause}            OR (action='THEME_UPDATED' AND resource_type='theme' AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED','REDIRECT_DELETED','COMPONENT_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED','COMPONENT_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
        )
    """


def _no_effect_completion_sql(*, include_style: bool) -> str:
    extra = ", 'theme', 'page_style'" if include_style else ", 'theme'"
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
                   'page','composition_node'{extra})
            THEN RAISE EXCEPTION 'INVALID_IDEMPOTENCY_COMPLETION' USING ERRCODE='P0001'; END IF;
            UPDATE control.agent_idempotency SET status_code=p_status_code,
                response_body=p_response_body,resource_type=p_resource_type,
                resource_id=p_resource_id,completed_at=current_timestamp
            WHERE capability_id=p_capability_id AND workspace_id=p_workspace_id
              AND idempotency_key=p_idempotency_key AND request_digest=p_request_digest
              AND operation_id=p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
        END;
        $fn$;
        ALTER FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete_no_effect(
            uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid) TO slaif_agent_runtime;
    """


def upgrade() -> None:
    _drop_cow_for_page_change()
    op.execute(
        "ALTER TABLE content.page ADD COLUMN style_overrides jsonb NOT NULL DEFAULT '{}'::jsonb"
    )
    _execute_block(_style_data_sql())
    op.execute(
        "ALTER TABLE content.page ADD CONSTRAINT page_style_overrides_valid "
        "CHECK (content.slaif_page_style_overrides_valid(style_overrides))"
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    _execute_block(_semantic_completion_sql(include_style=True))
    op.execute(_semantic_constraint_sql(include_style=True))
    _execute_block(_no_effect_completion_sql(include_style=True))
    for function in (
        "content.slaif_page_style_overrides_valid(jsonb)",
        "content.slaif_page_style_resolved(uuid,jsonb)",
        "content.slaif_page_style_project(uuid)",
        "content.slaif_page_style_get(uuid,uuid)",
        "content.slaif_agent_page_style_get(uuid,uuid)",
        "content.slaif_page_style_apply(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[],boolean)",
        "content.slaif_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
        "content.slaif_agent_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_page_style_get(uuid,uuid),"
        "content.slaif_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[]) "
        "TO slaif_editor_runtime"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_page_style_get(uuid,uuid),"
        "content.slaif_agent_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[]) "
        "TO slaif_agent_runtime"
    )


def downgrade() -> None:
    _drop_cow_for_page_change()
    op.execute(
        """
        DO $guard$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM content.page
                WHERE style_overrides IS DISTINCT FROM '{}'::jsonb
            ) THEN
                RAISE EXCEPTION 'PAGE_STYLE_MIGRATION_DATA_PRESENT'
                    USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM audit.agent_mutation
                WHERE action='PAGE_STYLE_UPDATED'
            ) THEN
                RAISE EXCEPTION 'PAGE_STYLE_MIGRATION_AUDIT_PRESENT'
                    USING ERRCODE='P0001';
            END IF;
        END $guard$;
        """
    )
    _execute_block(
        """
        DROP FUNCTION IF EXISTS content.slaif_agent_page_style_update(
            uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[]);
        DROP FUNCTION IF EXISTS content.slaif_page_style_update(
            uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[]);
        DROP FUNCTION IF EXISTS content.slaif_page_style_apply(
            uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[],boolean);
        DROP FUNCTION IF EXISTS content.slaif_agent_page_style_get(uuid,uuid);
        DROP FUNCTION IF EXISTS content.slaif_page_style_get(uuid,uuid);
        DROP FUNCTION IF EXISTS content.slaif_page_style_project(uuid);
        DROP FUNCTION IF EXISTS content.slaif_page_style_resolved(uuid,jsonb);
        ALTER TABLE content.page DROP CONSTRAINT IF EXISTS page_style_overrides_valid;
        ALTER TABLE content.page DROP COLUMN IF EXISTS style_overrides;
        DROP FUNCTION IF EXISTS content.slaif_page_style_overrides_valid(jsonb);
        """
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    _execute_block(_semantic_completion_sql(include_style=False))
    op.execute(_semantic_constraint_sql(include_style=False))
    _execute_block(_no_effect_completion_sql(include_style=False))

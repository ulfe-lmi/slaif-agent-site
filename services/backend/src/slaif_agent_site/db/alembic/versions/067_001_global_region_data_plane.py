# ruff: noqa: E501
"""Add the bounded site-global region data plane with header/footer variants."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "067_001"
down_revision: str | Sequence[str] | None = "066_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_REGION_COLUMNS = """
    id uuid, site_id uuid, region_key text, variant text, content jsonb,
    schema_version text, row_version integer, created_at timestamptz, updated_at timestamptz
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


def _drop_cow_for_region_change() -> None:
    """Refuse to discard pending workspace state before changing region state."""

    op.execute(
        """
        DO $guard$
        DECLARE relation_kind char; pending boolean;
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='site_global_region';
            IF relation_kind='v' THEN
                SELECT EXISTS (
                    SELECT 1 FROM pg_catalog.pg_class c
                    JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='content' AND c.relname='site_global_region_changes'
                ) INTO pending;
                IF pending THEN
                    EXECUTE 'SELECT EXISTS (SELECT 1 FROM content.site_global_region_changes)'
                        INTO pending;
                    IF pending THEN
                        RAISE EXCEPTION 'REGION_MIGRATION_PENDING_COW'
                            USING ERRCODE='P0001';
                    END IF;
                END IF;
                IF pg_catalog.to_regprocedure('agentcow.teardown_cow(text,text)') IS NULL THEN
                    RAISE EXCEPTION 'REGION_MIGRATION_REQUIRES_FOUNDATION'
                        USING ERRCODE='P0001';
                END IF;
                PERFORM agentcow.teardown_cow('content','site_global_region');
                EXECUTE 'ALTER TABLE content.site_global_region_base RENAME TO site_global_region';
            END IF;
        END $guard$;
        """
    )


def _validator_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_region_variant_valid(
            p_region_key text, p_variant text
        ) RETURNS boolean LANGUAGE sql IMMUTABLE
        SET search_path=pg_catalog AS $fn$
            SELECT (p_region_key='header'
                    AND p_variant IN ('institutional','minimal'))
                OR (p_region_key='footer'
                    AND p_variant IN ('multi-column','single-column'))
        $fn$;

        CREATE FUNCTION content.slaif_region_target_valid(p_target jsonb)
        RETURNS boolean LANGUAGE sql IMMUTABLE
        SET search_path=pg_catalog AS $fn$
            SELECT jsonb_typeof(p_target)='object'
               AND (SELECT count(*) FROM jsonb_object_keys(p_target))=2
               AND p_target ? 'kind' AND p_target ? 'value'
               AND jsonb_typeof(p_target->'kind')='string'
               AND (p_target->>'kind') IN ('page','internal','external')
               AND jsonb_typeof(p_target->'value')='string'
               AND (
                   ((p_target->>'kind')='page'
                        AND (p_target->>'value') ~
                            '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
                   OR ((p_target->>'kind')='internal'
                        AND length(p_target->>'value') BETWEEN 1 AND 256
                        AND (p_target->>'value') ~ '^/[a-z0-9._~/-]*$'
                        AND NOT ((p_target->>'value') ~ '//|\\.\\.|%'
                                 OR (p_target->>'value') ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'))
                   OR ((p_target->>'kind')='external'
                        AND length(p_target->>'value') BETWEEN 8 AND 2048
                        AND (p_target->>'value') ~ '^https?://[^/@][!-~]*$')
               )
        $fn$;

        CREATE FUNCTION content.slaif_region_entry_valid(p_entry jsonb)
        RETURNS boolean LANGUAGE sql IMMUTABLE
        SET search_path=pg_catalog AS $fn$
            SELECT jsonb_typeof(p_entry)='object'
               AND (SELECT count(*) FROM jsonb_object_keys(p_entry))=2
               AND p_entry ? 'label' AND p_entry ? 'target'
               AND jsonb_typeof(p_entry->'label')='string'
               AND length(p_entry->>'label') BETWEEN 1 AND 256
               AND (p_entry->>'label')=btrim(p_entry->>'label')
               AND content.slaif_region_target_valid(p_entry->'target')
        $fn$;

        CREATE FUNCTION content.slaif_region_content_valid(
            p_region_key text, p_content jsonb
        ) RETURNS boolean LANGUAGE sql IMMUTABLE
        SET search_path=pg_catalog AS $fn$
            SELECT jsonb_typeof(p_content)='object'
               AND length(coalesce(p_content::text,''))<=16384
               AND (
                   (p_region_key='header'
                        AND (SELECT count(*) FROM jsonb_object_keys(p_content))=1
                        AND p_content ? 'nav'
                        AND jsonb_typeof(p_content->'nav')='array'
                        AND jsonb_array_length(p_content->'nav') BETWEEN 1 AND 12
                        AND NOT EXISTS (
                            SELECT 1 FROM jsonb_array_elements(p_content->'nav') entry
                            WHERE NOT content.slaif_region_entry_valid(entry.value)
                        ))
                   OR (p_region_key='footer'
                        AND (SELECT count(*) FROM jsonb_object_keys(p_content)) BETWEEN 1 AND 2
                        AND p_content ? 'links'
                        AND NOT (p_content ?| ARRAY['nav'])
                        AND NOT (p_content ? 'note' AND (
                            jsonb_typeof(p_content->'note') IS DISTINCT FROM 'string'
                            OR length(p_content->>'note')>4096))
                        AND jsonb_typeof(p_content->'links')='array'
                        AND jsonb_array_length(p_content->'links') BETWEEN 0 AND 16
                        AND NOT EXISTS (
                            SELECT 1 FROM jsonb_array_elements(p_content->'links') entry
                            WHERE NOT content.slaif_region_entry_valid(entry.value)
                        ))
               )
        $fn$;
    """


def _resolution_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_region_default_id(p_site_id uuid, p_region_key text)
        RETURNS uuid LANGUAGE sql IMMUTABLE
        SET search_path=pg_catalog AS $fn$
            SELECT md5(p_site_id::text||':'||p_region_key)::uuid
        $fn$;

        CREATE FUNCTION content.slaif_region_default(p_site_id uuid, p_region_key text)
        RETURNS TABLE({_REGION_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT content.slaif_region_default_id(p_site_id,p_region_key),
                p_site_id, p_region_key,
                CASE WHEN p_region_key='header' THEN 'institutional'
                     ELSE 'single-column' END,
                CASE WHEN p_region_key='header'
                     THEN jsonb_build_object('nav',jsonb_build_array(
                            jsonb_build_object(
                                'label',s.site_key,
                                'target',jsonb_build_object('kind','internal','value','/')
                            )
                         ))
                     ELSE jsonb_build_object('links','[]'::jsonb,'note','')
                END,
                'global-region/v1', 1, s.created_at, s.created_at
            FROM control.site s
            WHERE s.id=p_site_id
              AND p_region_key IN ('header','footer')
        $fn$;

        CREATE FUNCTION content.slaif_region_project(p_site_id uuid, p_region_key text)
        RETURNS TABLE({_REGION_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT r.id,r.site_id,r.region_key,r.variant,r.content,
                r.schema_version,r.row_version,r.created_at,r.updated_at
            FROM content.site_global_region r
            WHERE r.site_id=p_site_id AND r.region_key=p_region_key
            UNION ALL
            SELECT d.id,d.site_id,d.region_key,d.variant,d.content,
                d.schema_version,d.row_version,d.created_at,d.updated_at
            FROM content.slaif_region_default(p_site_id,p_region_key) d
            WHERE NOT EXISTS (
                SELECT 1 FROM content.site_global_region existing
                WHERE existing.site_id=p_site_id AND existing.region_key=p_region_key
            )
        $fn$;

        CREATE FUNCTION content.slaif_region_list(p_site_id uuid)
        RETURNS TABLE({_REGION_COLUMNS}) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT * FROM content.slaif_region_project(p_site_id,'header')
            UNION ALL
            SELECT * FROM content.slaif_region_project(p_site_id,'footer')
        $fn$;

        CREATE FUNCTION content.slaif_region_page_targets_valid(
            p_site_id uuid, p_content jsonb
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(
                    coalesce(p_content->'nav',p_content->'links')
                ) entry
                WHERE entry.value->'target'->>'kind'='page'
                  AND NOT EXISTS (
                      SELECT 1 FROM content.page p
                      WHERE p.id=(entry.value->'target'->>'value')::uuid
                        AND p.site_id=p_site_id
                        AND p.deleted_at IS NULL
                  )
            )
        $fn$;

        CREATE FUNCTION content.slaif_page_ancestor_chain(
            p_site_id uuid, p_page_id uuid
        ) RETURNS TABLE(
            chain_position integer, id uuid, site_id uuid, title text, locale text,
            effective_route text
        ) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            WITH RECURSIVE chain AS (
                SELECT p.id, p.site_id, p.title, p.locale, p.parent_id, 1 AS depth
                FROM content.page p
                WHERE p.id=p_page_id AND p.site_id=p_site_id
                  AND p.deleted_at IS NULL
                UNION ALL
                SELECT par.id, par.site_id, par.title, par.locale, par.parent_id,
                    chain.depth+1
                FROM chain
                JOIN content.page par ON par.id=chain.parent_id
                WHERE par.site_id=p_site_id AND par.deleted_at IS NULL
                  AND par.locale=chain.locale
                  AND chain.depth<64
            )
            SELECT max(depth) OVER ()-depth+1, id, site_id, title, locale,
                content.slaif_agent_page_effective_route(id)
            FROM chain
            WHERE depth>1
            ORDER BY depth DESC
        $fn$;

        CREATE FUNCTION content.slaif_agent_region_list(p_site_id uuid)
        RETURNS TABLE({_REGION_COLUMNS}) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'global-region:read');
            RETURN QUERY SELECT * FROM content.slaif_region_list(p_site_id);
        END;
        $fn$;

        CREATE FUNCTION content.slaif_region_apply(
            p_site_id uuid, p_region_key text, p_expected integer,
            p_variant text, p_content jsonb, p_agent boolean
        ) RETURNS TABLE({_REGION_COLUMNS}, no_effect boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; current_row record;
            exists_row boolean; next_variant text; next_content jsonb;
            variant_changed boolean; content_changed boolean;
        BEGIN
            BEGIN
                workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF workspace_id IS NULL OR NULLIF(current_setting('app.operation_id',true),'') IS NULL
            THEN RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END IF;
            IF p_region_key IS DISTINCT FROM 'header'
               AND p_region_key IS DISTINCT FROM 'footer'
            THEN RAISE EXCEPTION 'REGION_KEY_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_agent AND (p_expected IS NULL OR p_expected<=0) THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            -- Lifecycle is the outer workspace lock.  Take only its advisory
            -- phase here; the capability helper performs its row-locking and
            -- scope checks after the resource lock, mirroring the theme and
            -- page-style mutation barriers.
            PERFORM pg_advisory_xact_lock_shared(hashtextextended(workspace_id::text,280));
            PERFORM pg_advisory_xact_lock(hashtextextended(
                workspace_id::text||chr(58)||p_site_id::text||chr(58)||'global-region',996));
            IF p_agent THEN
                capability_id:=control.slaif_agent_require_capability(
                    p_site_id,'global-region:read');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM control.site s WHERE s.id=p_site_id) THEN
                RAISE EXCEPTION 'REGION_SITE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            SELECT * INTO current_row FROM content.slaif_region_project(
                p_site_id,p_region_key);
            IF current_row.id IS NULL THEN
                RAISE EXCEPTION 'REGION_STATE_INVALID' USING ERRCODE='P0001';
            END IF;
            IF NOT content.slaif_region_variant_valid(p_region_key,current_row.variant)
               OR NOT content.slaif_region_content_valid(p_region_key,current_row.content)
            THEN RAISE EXCEPTION 'REGION_STATE_INVALID' USING ERRCODE='P0001'; END IF;
            IF current_row.schema_version<>'global-region/v1'
               OR current_row.row_version<=0
            THEN RAISE EXCEPTION 'REGION_STATE_INVALID' USING ERRCODE='P0001'; END IF;
            IF p_expected IS NOT NULL AND current_row.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF p_variant IS NOT NULL
               AND NOT content.slaif_region_variant_valid(p_region_key,p_variant)
            THEN RAISE EXCEPTION 'REGION_VARIANT_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_content IS NOT NULL
               AND (jsonb_typeof(p_content) IS DISTINCT FROM 'object'
                    OR NOT content.slaif_region_content_valid(p_region_key,p_content))
            THEN RAISE EXCEPTION 'REGION_CONTENT_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_content IS NOT NULL
               AND NOT content.slaif_region_page_targets_valid(p_site_id,p_content)
            THEN RAISE EXCEPTION 'REGION_PAGE_TARGET_INVALID' USING ERRCODE='P0003'; END IF;
            next_variant:=coalesce(p_variant,current_row.variant);
            next_content:=coalesce(p_content,current_row.content);
            variant_changed:=next_variant IS DISTINCT FROM current_row.variant;
            content_changed:=next_content IS DISTINCT FROM current_row.content;
            IF NOT variant_changed AND NOT content_changed THEN
                RETURN QUERY SELECT current_row.id,current_row.site_id,
                    current_row.region_key,current_row.variant,current_row.content,
                    'global-region/v1',current_row.row_version,current_row.created_at,
                    current_row.updated_at,true;
                RETURN;
            END IF;
            IF p_agent THEN
                PERFORM control.slaif_agent_require_capability(
                    p_site_id,'global-region:write');
                IF variant_changed THEN
                    PERFORM control.slaif_agent_require_capability(
                        p_site_id,'header-footer:write');
                END IF;
                IF NOT control.slaif_agent_quota_consume(
                    capability_id,workspace_id,'mutation')
                THEN RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED'
                    USING ERRCODE='P0005'; END IF;
            END IF;
            exists_row:=EXISTS (
                SELECT 1 FROM content.site_global_region r
                WHERE r.site_id=p_site_id AND r.region_key=p_region_key
            );
            IF NOT exists_row THEN
                INSERT INTO content.site_global_region(
                    id,site_id,region_key,variant,content,schema_version,
                    row_version,created_at,updated_at
                ) VALUES (
                    content.slaif_region_default_id(p_site_id,p_region_key),
                    p_site_id,p_region_key,next_variant,next_content,
                    'global-region/v1',current_row.row_version+1,
                    current_row.created_at,now()
                );
            ELSE
                UPDATE content.site_global_region AS r SET variant=next_variant,
                    content=next_content,row_version=r.row_version+1,updated_at=now()
                WHERE r.site_id=p_site_id AND r.region_key=p_region_key
                  AND (p_expected IS NULL OR r.row_version=p_expected);
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
                END IF;
            END IF;
            RETURN QUERY SELECT r.id,r.site_id,r.region_key,r.variant,r.content,
                'global-region/v1',r.row_version,r.created_at,r.updated_at,false
            FROM content.site_global_region r
            WHERE r.site_id=p_site_id AND r.region_key=p_region_key;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_region_update(
            p_site_id uuid, p_region_key text, p_expected integer,
            p_variant text, p_content jsonb
        ) RETURNS TABLE({_REGION_COLUMNS})
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT applied.id,applied.site_id,applied.region_key,
                applied.variant,applied.content,applied.schema_version,
                applied.row_version,applied.created_at,applied.updated_at
            FROM content.slaif_region_apply(
                p_site_id,p_region_key,p_expected,p_variant,p_content,false
            ) AS applied;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_region_update(
            p_site_id uuid, p_region_key text, p_expected integer,
            p_variant text, p_content jsonb
        ) RETURNS TABLE({_REGION_COLUMNS}, no_effect boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_region_apply(
                p_site_id,p_region_key,p_expected,p_variant,p_content,true);
        END;
        $fn$;
    """


def _semantic_completion_sql(*, include_region: bool) -> str:
    region_row = (
        "                       ('GLOBAL_REGION_UPDATED','global_region','PATCH',200,'mutation'),\n"
        if include_region
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
                       ('PAGE_STYLE_UPDATED','page_style','PATCH',200,'mutation'),
                       ('THEME_UPDATED','theme','PATCH',200,'mutation'),
{region_row}                       ('CONTENT_TYPE_DELETED','content_type','DELETE',200,'delete'),
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


def _semantic_constraint_sql(*, include_region: bool) -> str:
    region_clause = (
        "            OR (action='GLOBAL_REGION_UPDATED' AND resource_type='global_region' AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')\n"
        if include_region
        else ""
    )
    return f"""
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED','REDIRECT_CREATED','COMPONENT_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED','REDIRECT_UPDATED','COMPONENT_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action='PAGE_STYLE_UPDATED' AND resource_type='page_style' AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action='THEME_UPDATED' AND resource_type='theme' AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
{region_clause}            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED','REDIRECT_DELETED','COMPONENT_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED','COMPONENT_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
        )
    """


def _no_effect_completion_sql(*, include_region: bool) -> str:
    extra = (
        ", 'theme', 'page_style', 'global_region'"
        if include_region
        else ", 'theme', 'page_style'"
    )
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


def upgrade() -> None:
    _drop_cow_for_region_change()
    op.execute(
        """
        CREATE TABLE content.site_global_region (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES control.site(id),
            region_key text NOT NULL,
            variant text NOT NULL,
            content jsonb NOT NULL,
            schema_version text NOT NULL DEFAULT 'global-region/v1',
            row_version integer NOT NULL DEFAULT 1,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (site_id, region_key),
            CONSTRAINT site_global_region_key CHECK (region_key IN ('header','footer')),
            CONSTRAINT site_global_region_schema_version CHECK (
                schema_version='global-region/v1'),
            CONSTRAINT site_global_region_row_version CHECK (row_version>0)
        )
        """
    )
    _execute_block(_validator_sql())
    op.execute(
        "ALTER TABLE content.site_global_region "
        "ADD CONSTRAINT site_global_region_variant_valid "
        "CHECK (content.slaif_region_variant_valid(region_key, variant))"
    )
    op.execute(
        "ALTER TABLE content.site_global_region "
        "ADD CONSTRAINT site_global_region_content_valid "
        "CHECK (content.slaif_region_content_valid(region_key, content))"
    )
    _execute_block(_resolution_sql())
    op.execute(
        """
        INSERT INTO control.permission (
            permission_key,label,description,category,agent_delegation_level,
            site_assignable,installation_only,system_only
        ) VALUES (
            'global-region:read','global-region:read',
            'Built-in read authority.','READ',0,true,false,false
        ) ON CONFLICT (permission_key) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO control.human_role_permission (role_key, permission_key)
        SELECT r.role_key, 'global-region:read'
        FROM control.human_role r
        WHERE NOT EXISTS (
            SELECT 1 FROM control.human_role_permission hp
            WHERE hp.role_key=r.role_key AND hp.permission_key='global-region:read'
        )
        """
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql(include_region=True))
    _execute_block(_semantic_completion_sql(include_region=True))
    _execute_block(_no_effect_completion_sql(include_region=True))
    for function in (
        "content.slaif_region_variant_valid(text,text)",
        "content.slaif_region_target_valid(jsonb)",
        "content.slaif_region_entry_valid(jsonb)",
        "content.slaif_region_content_valid(text,jsonb)",
        "content.slaif_region_default_id(uuid,text)",
        "content.slaif_region_default(uuid,text)",
        "content.slaif_region_project(uuid,text)",
        "content.slaif_region_list(uuid)",
        "content.slaif_region_page_targets_valid(uuid,jsonb)",
        "content.slaif_page_ancestor_chain(uuid,uuid)",
        "content.slaif_agent_region_list(uuid)",
        "content.slaif_region_apply(uuid,text,integer,text,jsonb,boolean)",
        "content.slaif_region_update(uuid,text,integer,text,jsonb)",
        "content.slaif_agent_region_update(uuid,text,integer,text,jsonb)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_region_list(uuid),"
        "content.slaif_region_update(uuid,text,integer,text,jsonb) "
        "TO slaif_editor_runtime"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_region_list(uuid),"
        "content.slaif_agent_region_update(uuid,text,integer,text,jsonb) "
        "TO slaif_agent_runtime"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_region_list(uuid),"
        "content.slaif_page_ancestor_chain(uuid,uuid) "
        "TO slaif_public_reader, slaif_preview_reader"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_page_effective_route(uuid) "
        "TO slaif_public_reader, slaif_preview_reader"
    )
    op.execute(
        "ALTER FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "TO slaif_agent_runtime"
    )


def downgrade() -> None:
    _drop_cow_for_region_change()
    op.execute(
        """
        DO $guard$
        BEGIN
            IF EXISTS (SELECT 1 FROM content.site_global_region) THEN
                RAISE EXCEPTION 'REGION_MIGRATION_DATA_PRESENT'
                    USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM audit.agent_mutation
                WHERE action='GLOBAL_REGION_UPDATED'
            ) THEN
                RAISE EXCEPTION 'REGION_MIGRATION_AUDIT_PRESENT'
                    USING ERRCODE='P0001';
            END IF;
        END $guard$;
        """
    )
    op.execute(
        "ALTER TABLE content.site_global_region DROP CONSTRAINT IF EXISTS site_global_region_content_valid"
    )
    op.execute(
        "ALTER TABLE content.site_global_region DROP CONSTRAINT IF EXISTS site_global_region_variant_valid"
    )
    _execute_block(
        """
        DROP FUNCTION IF EXISTS content.slaif_agent_region_update(
            uuid,text,integer,text,jsonb);
        DROP FUNCTION IF EXISTS content.slaif_region_update(
            uuid,text,integer,text,jsonb);
        DROP FUNCTION IF EXISTS content.slaif_region_apply(
            uuid,text,integer,text,jsonb,boolean);
        DROP FUNCTION IF EXISTS content.slaif_region_page_targets_valid(uuid,jsonb);
        DROP FUNCTION IF EXISTS content.slaif_agent_region_list(uuid);
        DROP FUNCTION IF EXISTS content.slaif_region_list(uuid);
        DROP FUNCTION IF EXISTS content.slaif_region_project(uuid,text);
        DROP FUNCTION IF EXISTS content.slaif_region_default(uuid,text);
        DROP FUNCTION IF EXISTS content.slaif_region_default_id(uuid,text);
        DROP FUNCTION IF EXISTS content.slaif_region_content_valid(text,jsonb);
        DROP FUNCTION IF EXISTS content.slaif_region_entry_valid(jsonb);
        DROP FUNCTION IF EXISTS content.slaif_region_target_valid(jsonb);
        DROP FUNCTION IF EXISTS content.slaif_region_variant_valid(text,text);
        DROP FUNCTION IF EXISTS content.slaif_page_ancestor_chain(uuid,uuid);
        """
    )
    op.execute("DROP TABLE IF EXISTS content.site_global_region")
    op.execute(
        "DELETE FROM control.human_role_permission WHERE permission_key='global-region:read'"
    )
    op.execute(
        "DELETE FROM control.permission WHERE permission_key='global-region:read'"
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    _execute_block(_semantic_completion_sql(include_region=False))
    op.execute(_semantic_constraint_sql(include_region=False))
    _execute_block(_no_effect_completion_sql(include_region=False))

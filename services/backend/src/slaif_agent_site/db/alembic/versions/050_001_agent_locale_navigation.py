# ruff: noqa: E501
"""Add capability-bound Agent locale and navigation semantics."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "050_001"
down_revision: str | Sequence[str] | None = "049_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_NAV_RETURN = """
    id uuid, site_id uuid, \"key\" text, label text, labels jsonb,
    settings jsonb, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""

_ITEM_RETURN = """
    id uuid, site_id uuid, navigation_id uuid, parent_id uuid, page_id uuid,
    target_kind text, target_value text, labels jsonb, locale text,
    "position" integer, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""


def _resource_constraint_sql() -> str:
    return """
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
            max_navigation_depth integer
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE
            workspace_id uuid; result jsonb;
        BEGIN
            BEGIN
                workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF workspace_id IS NULL
               OR NULLIF(current_setting('app.operation_id', true), '') IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END IF;
            SELECT w.resource_constraints INTO result
            FROM control.workspace w
            JOIN control.site s ON s.id=w.site_id
            JOIN control.user_account a ON a.id=coalesce(w.delegator_id,w.created_by)
            WHERE w.id=workspace_id AND w.site_id=p_site_id
              AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
              AND s.status='ACTIVE' AND a.status='ACTIVE';
            IF result IS NULL OR jsonb_typeof(result) <> 'object' THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_object_keys(result) k
                WHERE k NOT IN (
                    'allowed_type_ids','allowed_type_keys','max_content_types',
                    'max_fields_per_type','delete_enabled','max_deletes',
                    'allowed_locales','route_prefix','allowed_page_root_ids',
                    'max_visible_pages','max_page_depth','allowed_navigation_keys',
                    'allowed_navigation_ids','max_visible_locales',
                    'max_visible_navigations','max_visible_navigation_items',
                    'max_navigation_depth'
                )
            ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF (result ? 'allowed_type_ids' AND jsonb_typeof(result->'allowed_type_ids') <> 'array')
               OR (result ? 'allowed_type_keys' AND jsonb_typeof(result->'allowed_type_keys') <> 'array')
               OR (result ? 'allowed_locales' AND jsonb_typeof(result->'allowed_locales') <> 'array')
               OR (result ? 'allowed_page_root_ids' AND jsonb_typeof(result->'allowed_page_root_ids') <> 'array')
               OR (result ? 'allowed_navigation_keys' AND jsonb_typeof(result->'allowed_navigation_keys') <> 'array')
               OR (result ? 'allowed_navigation_ids' AND jsonb_typeof(result->'allowed_navigation_ids') <> 'array')
               OR (result ? 'delete_enabled' AND jsonb_typeof(result->'delete_enabled') <> 'boolean')
               OR (result ? 'route_prefix' AND (jsonb_typeof(result->'route_prefix') <> 'string' OR result->>'route_prefix'=''))
               OR EXISTS (
                   SELECT 1 FROM (VALUES
                       ('max_content_types'),('max_fields_per_type'),('max_deletes'),
                       ('max_visible_pages'),('max_page_depth'),
                       ('max_visible_locales'),('max_visible_navigations'),
                       ('max_visible_navigation_items'),('max_navigation_depth')
                   ) AS numeric_key(key)
                   WHERE result ? numeric_key.key
                     AND jsonb_typeof(result->numeric_key.key) <> 'number'
               ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_each_text(result) item
                WHERE item.key IN (
                    'max_content_types','max_fields_per_type','max_deletes',
                    'max_visible_pages','max_page_depth','max_visible_locales',
                    'max_visible_navigations','max_visible_navigation_items',
                    'max_navigation_depth'
                ) AND (item.value !~ '^[0-9]+$' OR item.value::numeric>2147483647)
            ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) v
                WHERE v !~ '^[A-Za-z0-9._~-]{1,63}$'
            ) OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) value))>256
              OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_ids','[]'::jsonb)) value))>256
              OR EXISTS (
                  SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_ids','[]'::jsonb)) v
                  WHERE v !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
              ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) v
                WHERE v !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
            ) OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) value))>64
            THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF result ? 'route_prefix' AND (
                result->>'route_prefix' !~ '^/[a-z0-9][a-z0-9._~-]*(/[a-z0-9][a-z0-9._~-]*)*$'
                AND result->>'route_prefix'<>'/'
                OR result->>'route_prefix' ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
            ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            allowed_type_ids := ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) value);
            allowed_type_keys := ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_keys','[]'::jsonb)) value);
            max_content_types := CASE WHEN result ? 'max_content_types' THEN (result->>'max_content_types')::integer END;
            max_fields_per_type := CASE WHEN result ? 'max_fields_per_type' THEN (result->>'max_fields_per_type')::integer END;
            delete_enabled := CASE WHEN result ? 'delete_enabled' THEN (result->>'delete_enabled')::boolean END;
            max_deletes := CASE WHEN result ? 'max_deletes' THEN (result->>'max_deletes')::integer END;
            allowed_locales := ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) value);
            route_prefix := CASE WHEN result ? 'route_prefix' THEN result->>'route_prefix' END;
            allowed_page_root_ids := ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_page_root_ids','[]'::jsonb)) value);
            max_visible_pages := CASE WHEN result ? 'max_visible_pages' THEN (result->>'max_visible_pages')::integer END;
            max_page_depth := CASE WHEN result ? 'max_page_depth' THEN (result->>'max_page_depth')::integer END;
            allowed_navigation_keys := ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) value);
            allowed_navigation_ids := ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_ids','[]'::jsonb)) value);
            max_visible_locales := CASE WHEN result ? 'max_visible_locales' THEN (result->>'max_visible_locales')::integer END;
            max_visible_navigations := CASE WHEN result ? 'max_visible_navigations' THEN (result->>'max_visible_navigations')::integer END;
            max_visible_navigation_items := CASE WHEN result ? 'max_visible_navigation_items' THEN (result->>'max_visible_navigation_items')::integer END;
            max_navigation_depth := CASE WHEN result ? 'max_navigation_depth' THEN (result->>'max_navigation_depth')::integer END;
            RETURN NEXT;
        END;
        $fn$
    """


def _semantic_constraint_sql() -> str:
    return """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
        );
    """


def _idempotency_completion_sql() -> str:
    return """
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
               OR p_request_digest IS NULL OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_operation_id IS NULL OR p_resource_id IS NULL
               OR p_response_body IS NULL OR jsonb_typeof(p_response_body)<>'object'
               OR p_response_body->>'action' IS DISTINCT FROM p_action
               OR p_response_body->>'operation_id' IS DISTINCT FROM p_operation_id::text
               OR p_response_body->'record'->>'id' IS DISTINCT FROM p_resource_id::text
               OR NOT (
                   (p_action='CONTENT_TYPE_CREATED' AND p_resource_type='content_type' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='FIELD_DEFINITION_CREATED' AND p_resource_type='field_definition' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='CONTENT_ITEM_CREATED' AND p_resource_type='content_item' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='CONTENT_ITEM_TRANSLATION_CREATED' AND p_resource_type='content_item_translation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='ITEM_RELATION_CREATED' AND p_resource_type='item_relation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='COLLECTION_VIEW_CREATED' AND p_resource_type='collection_view' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='PAGE_CREATED' AND p_resource_type='page' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='LOCALE_CREATED' AND p_resource_type='locale' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='NAVIGATION_CREATED' AND p_resource_type='navigation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='NAVIGATION_ITEM_CREATED' AND p_resource_type='navigation_item' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                   OR (p_action='CONTENT_TYPE_UPDATED' AND p_resource_type='content_type' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='FIELD_DEFINITION_UPDATED' AND p_resource_type='field_definition' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='CONTENT_ITEM_UPDATED' AND p_resource_type='content_item' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='CONTENT_ITEM_TRANSLATION_UPDATED' AND p_resource_type='content_item_translation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='ITEM_RELATION_UPDATED' AND p_resource_type='item_relation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='COLLECTION_VIEW_UPDATED' AND p_resource_type='collection_view' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='PAGE_UPDATED' AND p_resource_type='page' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='LOCALE_UPDATED' AND p_resource_type='locale' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='NAVIGATION_UPDATED' AND p_resource_type='navigation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='NAVIGATION_ITEM_UPDATED' AND p_resource_type='navigation_item' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='CONTENT_TYPE_DELETED' AND p_resource_type='content_type' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='FIELD_DEFINITION_DELETED' AND p_resource_type='field_definition' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='CONTENT_ITEM_DELETED' AND p_resource_type='content_item' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='CONTENT_ITEM_TRANSLATION_DELETED' AND p_resource_type='content_item_translation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='ITEM_RELATION_DELETED' AND p_resource_type='item_relation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='COLLECTION_VIEW_DELETED' AND p_resource_type='collection_view' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='PAGE_DELETED' AND p_resource_type='page' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='LOCALE_DELETED' AND p_resource_type='locale' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='NAVIGATION_DELETED' AND p_resource_type='navigation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='NAVIGATION_ITEM_DELETED' AND p_resource_type='navigation_item' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                   OR (p_action='PAGE_MOVED' AND p_resource_type='page' AND p_http_method='POST' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='PAGE_RESTORED' AND p_resource_type='page' AND p_http_method='POST' AND p_status_code=200 AND p_quota_kind='mutation')
                   OR (p_action='NAVIGATION_ITEM_MOVED' AND p_resource_type='navigation_item' AND p_http_method='POST' AND p_status_code=200 AND p_quota_kind='mutation')
               )
            THEN RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001'; END IF;
            SELECT w.site_id INTO expected_site
            FROM control.capability c JOIN control.workspace w ON w.id=c.workspace_id
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
        $fn$
    """


def upgrade() -> None:
    # Bootstrap runs migrations with content COW disabled. Reconcile then
    # recreates overlays for these changed public product relations.
    op.execute(
        "ALTER TABLE content.navigation ADD COLUMN labels jsonb NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        "ALTER TABLE content.navigation ADD COLUMN row_version integer NOT NULL DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE content.navigation ADD CONSTRAINT navigation_labels_bounded CHECK (jsonb_typeof(labels)='object' AND octet_length(labels::text)<=16384)"
    )
    op.execute(
        "ALTER TABLE content.navigation ADD CONSTRAINT navigation_row_version_positive CHECK (row_version>0)"
    )
    op.execute(
        "ALTER TABLE content.navigation_item ADD COLUMN parent_key uuid NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000'::uuid"
    )
    op.execute(
        "UPDATE content.navigation_item SET parent_key=coalesce(parent_id,'00000000-0000-0000-0000-000000000000'::uuid)"
    )
    op.execute("DROP INDEX IF EXISTS content.navigation_item_sibling_position")
    op.execute(
        "ALTER TABLE content.navigation_item ADD CONSTRAINT navigation_item_sibling_position UNIQUE (site_id,navigation_id,parent_key,position) DEFERRABLE INITIALLY DEFERRED"
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_create(
            p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE parent_nav uuid; created content.navigation_item;
            created_id uuid;
            desired_position integer; sibling_count integer;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            IF NOT EXISTS (SELECT 1 FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id) THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF p_parent_id IS NOT NULL THEN
                SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i
                WHERE i.id=p_parent_id AND i.site_id=p_site_id;
                IF parent_nav IS NULL OR parent_nav<>p_navigation_id THEN
                    RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
            END IF;
            IF p_target_kind='PAGE' AND (p_page_id IS NULL OR p_target_value<>p_page_id::text) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target_kind<>'PAGE' AND p_page_id IS NOT NULL THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_page_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL
            ) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_position NOT BETWEEN 0 AND 999
               OR jsonb_typeof(p_labels)<>'object' THEN
                RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003';
            END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,p_labels);
            SELECT count(*)::integer INTO sibling_count
            FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
              AND i.parent_id IS NOT DISTINCT FROM p_parent_id;
            IF sibling_count>=1000 THEN
                RAISE EXCEPTION 'NAVIGATION_POSITION_LIMIT' USING ERRCODE='P0003';
            END IF;
            desired_position:=least(p_position,sibling_count);
            UPDATE content.navigation_item i SET position=i.position+1,
                row_version=i.row_version+1,updated_at=now()
            WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
              AND i.parent_id IS NOT DISTINCT FROM p_parent_id
              AND i.position>=desired_position;
            INSERT INTO content.navigation_item(
                id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,
                target_value,labels,locale,position
            ) VALUES (
                gen_random_uuid(),p_site_id,p_navigation_id,p_parent_id,
                coalesce(p_parent_id,'00000000-0000-0000-0000-000000000000'::uuid),
                p_page_id,p_target_kind,p_target_value,p_labels,p_locale,desired_position
            ) RETURNING id INTO created_id;
            SELECT i.* INTO created FROM content.navigation_item i WHERE i.id=created_id;
            RETURN NEXT created;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_update(
            p_site_id uuid,p_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer,p_expected integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.navigation_item; parent_nav uuid;
            target_parent uuid; target_page uuid; new_target_kind text;
            new_target_value text; new_target_labels jsonb; new_target_locale text;
            cursor_id uuid; desired_position integer; sibling_count integer;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT i.* INTO old FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF p_parent_id IS NOT NULL THEN
                SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.id=p_parent_id;
                IF parent_nav IS NULL OR parent_nav<>old.navigation_id OR p_parent_id=p_id THEN
                    RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
                cursor_id:=p_parent_id;
                LOOP
                    IF cursor_id=p_id THEN
                        RAISE EXCEPTION 'NAVIGATION_CYCLE' USING ERRCODE='P0003';
                    END IF;
                    SELECT i.parent_id INTO cursor_id FROM content.navigation_item i
                    WHERE i.site_id=p_site_id AND i.id=cursor_id;
                    EXIT WHEN cursor_id IS NULL;
                END LOOP;
            END IF;
            target_parent:=p_parent_id;
            target_page:=CASE WHEN p_target_kind IS NOT NULL AND p_target_kind<>'PAGE'
                THEN NULL ELSE coalesce(p_page_id,old.page_id) END;
            new_target_kind:=coalesce(p_target_kind,old.target_kind);
            new_target_value:=coalesce(p_target_value,old.target_value);
            new_target_labels:=coalesce(p_labels,old.labels);
            new_target_locale:=p_locale;
            IF new_target_kind='PAGE'
               AND (target_page IS NULL OR new_target_value<>target_page::text)
            THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF new_target_kind<>'PAGE' AND target_page IS NOT NULL
            THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF target_page IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.id=target_page AND p.site_id=p_site_id AND p.deleted_at IS NULL
            ) THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF new_target_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=new_target_locale AND l.enabled
            ) THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF new_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_position IS NOT NULL AND p_position NOT BETWEEN 0 AND 999
               OR jsonb_typeof(new_target_labels)<>'object'
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,new_target_labels);
            SELECT count(*)::integer INTO sibling_count
            FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
              AND i.parent_id IS NOT DISTINCT FROM target_parent AND i.id<>p_id;
            desired_position:=least(coalesce(p_position,old.position),sibling_count);
            UPDATE content.navigation_item i SET position=999
            WHERE i.site_id=p_site_id AND i.id=p_id;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM old.parent_id AND i.id<>p_id
            ) UPDATE content.navigation_item i SET position=ranked.compact_position,
                row_version=CASE WHEN i.position IS DISTINCT FROM ranked.compact_position
                    THEN i.row_version+1 ELSE i.row_version END,
                updated_at=CASE WHEN i.position IS DISTINCT FROM ranked.compact_position
                    THEN now() ELSE i.updated_at END
            FROM ranked WHERE i.id=ranked.id;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM target_parent AND i.id<>p_id
            ) UPDATE content.navigation_item i SET position=ranked.compact_position+1,
                row_version=i.row_version+1,updated_at=now()
            FROM ranked WHERE i.id=ranked.id
              AND ranked.compact_position>=desired_position;
            UPDATE content.navigation_item AS i SET
                parent_id=target_parent,
                parent_key=coalesce(target_parent,'00000000-0000-0000-0000-000000000000'::uuid),
                page_id=target_page,target_kind=new_target_kind,target_value=new_target_value,
                labels=new_target_labels,locale=new_target_locale,position=desired_position,
                row_version=i.row_version+1,
                updated_at=now()
            WHERE i.site_id=p_site_id AND i.id=p_id AND i.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT i.* FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id;
        END; $fn$
        """
    )

    op.execute("DROP FUNCTION control.slaif_agent_resource_constraints(uuid)")
    op.execute(_resource_constraint_sql())
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql())
    op.execute(_idempotency_completion_sql())

    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_structural_lock(p_site_id uuid)
        RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid;
        BEGIN
            BEGIN workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF workspace_id IS NULL THEN RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023'; END IF;
            -- All online structural writes take the workspace lifecycle lock
            -- first, then this one workspace+site structural lock.  The key is
            -- equal to the 049 page lock so every interface shares one order.
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text,280));
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text||chr(58)||p_site_id::text||chr(58)||'page-structure',994));
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_require_capability(
            p_site_id uuid, p_required_scope text
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            cow_workspace_id uuid; capability_id uuid; operation_id uuid;
            expected_site uuid; delegator_id uuid; preset text;
            required_level integer; platform_admin boolean;
            effective_ceiling integer; effective_scopes jsonb;
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            BEGIN
                cow_workspace_id := NULLIF(current_setting('app.session_id', true), '')::uuid;
                operation_id := NULLIF(current_setting('app.operation_id', true), '')::uuid;
                capability_id := NULLIF(current_setting('app.capability_id', true), '')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'AGENT_CAPABILITY_CONTEXT_REQUIRED' USING ERRCODE = '22023';
            END;
            IF cow_workspace_id IS NULL OR operation_id IS NULL OR capability_id IS NULL THEN
                RAISE EXCEPTION 'AGENT_CAPABILITY_CONTEXT_REQUIRED' USING ERRCODE = '22023';
            END IF;
            -- Establish the lifecycle shared lock before any structural lock.
            PERFORM pg_advisory_xact_lock(hashtextextended(cow_workspace_id::text,280));
            SELECT w.site_id, COALESCE(w.delegator_id,w.created_by),
                   w.delegation_preset, c.scopes
              INTO expected_site, delegator_id, preset, effective_scopes
            FROM control.capability c
            JOIN control.workspace w ON w.id=c.workspace_id
            JOIN control.site s ON s.id=w.site_id
            JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
            WHERE c.id=capability_id AND c.workspace_id=cow_workspace_id
              AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
              AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
              AND s.status='ACTIVE' AND a.status='ACTIVE';
            IF expected_site IS NULL OR expected_site IS DISTINCT FROM p_site_id THEN
                RAISE EXCEPTION 'AGENT_CAPABILITY_SITE_MISMATCH' USING ERRCODE='P0002';
            END IF;
            IF p_required_scope IS NULL OR btrim(p_required_scope)='' OR effective_scopes IS NULL
               OR jsonb_typeof(effective_scopes)<>'array'
            THEN RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007'; END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_array_elements(effective_scopes) AS scope(value)
                WHERE jsonb_typeof(scope.value)<>'string'
            ) OR NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(effective_scopes) AS scope(value)
                WHERE scope.value #>> '{}'=p_required_scope
            ) THEN RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007'; END IF;
            required_level:=CASE preset
                WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END;
            SELECT EXISTS (SELECT 1 FROM control.platform_administrator pa
                WHERE pa.user_account_id=delegator_id) INTO platform_admin;
            IF NOT platform_admin THEN
                SELECT MAX(m.effective_ceiling) INTO effective_ceiling
                FROM control.slaif_effective_human_membership(delegator_id,p_site_id) m;
                IF effective_ceiling IS NULL OR effective_ceiling<required_level THEN
                    RAISE EXCEPTION 'COW_AUTHORITY_REVOKED' USING ERRCODE='P0002';
                END IF;
            END IF;
            RETURN capability_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_agent_page_effective_route(p_page_id uuid)
        RETURNS text LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE current_page record; current_id uuid:=p_page_id;
            segments text[]:=ARRAY[]::text[]; route text:=''; depth integer:=0;
            index integer; default_locale text; page_locale text; segment text;
        BEGIN
            SELECT p.* INTO current_page FROM content.page p WHERE p.id=p_page_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            page_locale:=current_page.locale;
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=current_page.site_id AND l.enabled AND l.is_default;
            IF default_locale IS NULL THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF NOT EXISTS (SELECT 1 FROM content.site_locale l WHERE l.site_id=current_page.site_id AND l.tag=page_locale AND l.enabled) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            LOOP
                depth:=depth+1; IF depth>64 THEN RAISE EXCEPTION 'PAGE_HIERARCHY_CYCLE' USING ERRCODE='P0003'; END IF;
                segment:=coalesce(nullif(current_page.route_template,''),current_page.slug);
                segments:=array_append(segments,segment); EXIT WHEN current_page.parent_id IS NULL;
                SELECT p.* INTO current_page FROM content.page p WHERE p.id=current_page.parent_id AND p.site_id=current_page.site_id AND p.deleted_at IS NULL;
                IF NOT FOUND OR current_page.locale IS DISTINCT FROM page_locale THEN RAISE EXCEPTION 'PAGE_PARENT_INVALID' USING ERRCODE='P0003'; END IF;
                IF current_page.route_template='{slug}' THEN RAISE EXCEPTION 'PAGE_DYNAMIC_PARENT' USING ERRCODE='P0003'; END IF;
            END LOOP;
            IF page_locale IS DISTINCT FROM default_locale THEN route:='/'||page_locale; END IF;
            FOR index IN REVERSE array_length(segments,1)..1 LOOP
                IF index=array_length(segments,1) AND segments[index]='home' THEN CONTINUE; END IF;
                route:=route||'/'||segments[index];
            END LOOP;
            IF route='' THEN RETURN '/'; END IF; RETURN route;
        END;
        $fn$
        """
    )

    # Keep the Editor container response byte shape stable after the new Agent
    # columns are added, while making its existing update row-version-safe.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_create(
            p_site_id uuid, p_slug text, p_title text, p_status text, p_locale text
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            IF NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            INSERT INTO content.page(site_id,slug,title,status,locale)
            VALUES(p_site_id,p_slug,p_title,p_status,p_locale);
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.row_version,p.created_at,p.updated_at FROM content.page p
            WHERE p.site_id=p_site_id AND p.slug=p_slug AND p.locale=p_locale
            ORDER BY p.created_at DESC LIMIT 1;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_update(
            p_page_id uuid, p_slug text, p_title text, p_status text,
            p_expected_row_version integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid;
        BEGIN
            SELECT p.site_id INTO target_site FROM content.page p WHERE p.id=p_page_id;
            IF target_site IS NULL THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM control.slaif_agent_structural_lock(target_site);
            UPDATE content.page AS page SET
                slug=coalesce(p_slug,page.slug), title=coalesce(p_title,page.title),
                status=coalesce(p_status,page.status), row_version=page.row_version+1,
                updated_at=CURRENT_TIMESTAMP
            WHERE page.id=p_page_id
              AND page.deleted_at IS NULL
              AND (p_expected_row_version IS NULL OR page.row_version=p_expected_row_version);
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.row_version,p.created_at,p.updated_at FROM content.page p
            WHERE p.id=p_page_id AND p.deleted_at IS NULL;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_delete(p_page_id uuid)
        RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid;
        BEGIN
            SELECT p.site_id INTO target_site FROM content.page p WHERE p.id=p_page_id;
            IF target_site IS NULL THEN RETURN; END IF;
            PERFORM control.slaif_agent_structural_lock(target_site);
            DELETE FROM content.page WHERE id=p_page_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_create(p_site_id uuid,p_key text,p_label text,p_settings jsonb)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            INSERT INTO content.navigation(site_id,\"key\",label,settings,labels) VALUES(p_site_id,p_key,p_label,p_settings,'{}'::jsonb);
            RETURN QUERY SELECT n.id,n.site_id,n.\"key\",n.label,n.settings,n.created_at,n.updated_at FROM content.navigation n WHERE n.site_id=p_site_id AND n.\"key\"=p_key LIMIT 1;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_list(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $fn$
            SELECT n.id,n.site_id,n.\"key\",n.label,n.settings,n.created_at,n.updated_at FROM content.navigation n WHERE n.site_id=p_site_id ORDER BY n.\"key\" COLLATE \"C\"
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_get(p_nav_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $fn$
            SELECT n.id,n.site_id,n.\"key\",n.label,n.settings,n.created_at,n.updated_at FROM content.navigation n WHERE n.id=p_nav_id
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_update(p_nav_id uuid,p_label text,p_settings jsonb)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid;
        BEGIN
            SELECT n.site_id INTO target_site FROM content.navigation n WHERE n.id=p_nav_id;
            IF target_site IS NULL THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM control.slaif_agent_structural_lock(target_site);
            UPDATE content.navigation n SET label=coalesce(p_label,n.label),settings=coalesce(p_settings,n.settings),row_version=n.row_version+1,updated_at=current_timestamp WHERE n.id=p_nav_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            RETURN QUERY SELECT n.id,n.site_id,n.\"key\",n.label,n.settings,n.created_at,n.updated_at FROM content.navigation n WHERE n.id=p_nav_id;
        END; $fn$
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_locale_create(
            p_site_id uuid,p_tag text,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb
        ) RETURNS SETOF content.site_locale
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            IF p_tag IS NULL OR p_tag !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
               OR p_position IS NULL OR p_position NOT BETWEEN 0 AND 999
               OR p_metadata IS NULL OR jsonb_typeof(p_metadata)<>'object'
               OR p_default AND NOT p_enabled
            THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_default THEN
                UPDATE content.site_locale l SET is_default=false,
                    row_version=l.row_version+1,updated_at=now()
                WHERE l.site_id=p_site_id AND l.is_default;
            END IF;
            INSERT INTO content.site_locale(site_id,tag,enabled,is_default,position,metadata)
            VALUES(p_site_id,p_tag,p_enabled,p_default,p_position,p_metadata);
            RETURN QUERY SELECT l.* FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.tag=p_tag;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_locale_update(
            p_site_id uuid,p_id uuid,p_tag text,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb,p_expected integer
        ) RETURNS SETOF content.site_locale
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.site_locale;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT l.* INTO old FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF p_tag IS NOT NULL AND p_tag !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
               OR coalesce(p_position,old.position) NOT BETWEEN 0 AND 999
            THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF old.is_default AND (p_enabled IS FALSE OR p_default IS FALSE)
            THEN RAISE EXCEPTION 'LOCALE_DEFAULT_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF p_tag IS NOT NULL AND p_tag<>old.tag AND (
                EXISTS(SELECT 1 FROM content.navigation n
                       WHERE n.site_id=p_site_id AND n.labels ? old.tag)
                OR EXISTS(SELECT 1 FROM content.navigation_item i
                           WHERE i.site_id=p_site_id AND i.labels ? old.tag)
            ) THEN RAISE EXCEPTION 'LOCALE_REFERENCED' USING ERRCODE='P0003'; END IF;
            IF p_default IS TRUE THEN
                UPDATE content.site_locale l SET is_default=false,
                    row_version=l.row_version+1,updated_at=now()
                WHERE l.site_id=p_site_id AND l.id<>p_id AND l.is_default;
            END IF;
            UPDATE content.site_locale l SET tag=coalesce(p_tag,l.tag),
                enabled=coalesce(p_enabled,l.enabled),is_default=coalesce(p_default,l.is_default),
                position=coalesce(p_position,l.position),metadata=coalesce(p_metadata,l.metadata),
                row_version=l.row_version+1,updated_at=now()
            WHERE l.site_id=p_site_id AND l.id=p_id AND l.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT l.* FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.id=p_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_locale_delete(
            p_site_id uuid,p_id uuid,p_expected integer
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.site_locale;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT l.* INTO old FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF old.is_default OR EXISTS(SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.locale=old.tag)
               OR EXISTS(SELECT 1 FROM content.navigation n WHERE n.site_id=p_site_id AND n.labels ? old.tag)
               OR EXISTS(SELECT 1 FROM content.navigation_item n WHERE n.site_id=p_site_id AND (n.locale=old.tag OR n.labels ? old.tag))
               OR EXISTS(SELECT 1 FROM content.redirect r WHERE r.site_id=p_site_id AND r.locale=old.tag)
            THEN RAISE EXCEPTION 'LOCALE_REFERENCED' USING ERRCODE='P0003'; END IF;
            DELETE FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_id AND l.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_delete(p_nav_id uuid)
        RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid;
        BEGIN
            SELECT n.site_id INTO target_site FROM content.navigation n WHERE n.id=p_nav_id;
            IF target_site IS NULL THEN RETURN; END IF;
            PERFORM control.slaif_agent_structural_lock(target_site);
            DELETE FROM content.navigation n WHERE n.id=p_nav_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_delete(
            p_site_id uuid,p_id uuid,p_expected integer
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.navigation_item;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT i.* INTO old FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected
            THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF EXISTS(SELECT 1 FROM content.navigation_item c
                      WHERE c.site_id=p_site_id AND c.parent_id=p_id)
            THEN RAISE EXCEPTION 'NAVIGATION_CHILDREN' USING ERRCODE='P0003'; END IF;
            DELETE FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_id AND i.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS new_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM old.parent_id
            ) UPDATE content.navigation_item i SET position=ranked.new_position,
                row_version=CASE WHEN i.position IS DISTINCT FROM ranked.new_position
                    THEN i.row_version+1 ELSE i.row_version END,
                updated_at=CASE WHEN i.position IS DISTINCT FROM ranked.new_position
                    THEN now() ELSE i.updated_at END
            FROM ranked WHERE i.id=ranked.id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_validate_labels(
            p_site_id uuid, p_labels jsonb
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; label_locale text;
        BEGIN
            IF p_labels IS NULL OR jsonb_typeof(p_labels)<>'object'
               OR octet_length(p_labels::text)>16384
               OR (SELECT count(*) FROM jsonb_object_keys(p_labels))>16
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id);
            FOR label_locale IN SELECT key FROM jsonb_object_keys(p_labels) AS key LOOP
                IF label_locale !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
                   OR jsonb_typeof(p_labels->label_locale)<>'string'
                   OR octet_length(p_labels->>label_locale)>256
                THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM content.site_locale l
                    WHERE l.site_id=p_site_id AND l.tag=label_locale AND l.enabled
                ) THEN RAISE EXCEPTION 'NAVIGATION_LABEL_LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
                IF cardinality(constraints.allowed_locales)>0
                   AND NOT label_locale=ANY(constraints.allowed_locales)
                THEN RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
            END LOOP;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_validate_target(
            p_site_id uuid,p_page_id uuid,p_target_kind text,p_target_value text,
            p_labels jsonb,p_locale text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record;
        BEGIN
            IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_target_value IS NULL OR octet_length(p_target_value)>2048
               OR p_target_value ~ '[[:cntrl:] ]'
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,p_labels);
            IF p_target_kind='PAGE' THEN
                IF p_page_id IS NULL OR p_target_value<>p_page_id::text
                   OR NOT content.slaif_agent_page_accessible(p_site_id,p_page_id)
                THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            ELSIF p_page_id IS NOT NULL THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            ELSIF p_target_kind='INTERNAL' THEN
                IF NOT (p_target_value='/' OR p_target_value ~ '^/[a-z0-9][a-z0-9._~/-]*$')
                   OR p_target_value ~ '//|\\.\\.|%|\\\\'
                   OR p_target_value ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
                THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM content.page p
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                      AND p.route_template IS NULL
                      AND content.slaif_agent_page_accessible(p_site_id,p.id)
                      AND content.slaif_agent_page_effective_route(p.id)=p_target_value
                ) THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
            ELSE
                IF p_target_value !~ '^https://[^/@?#]+([/?#].*)?$'
                   OR p_target_value ~ '[[:cntrl:] ]'
                THEN RAISE EXCEPTION 'NAVIGATION_TARGET_UNSAFE' USING ERRCODE='P0003'; END IF;
            END IF;
            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id);
            IF p_locale IS NOT NULL AND cardinality(constraints.allowed_locales)>0
               AND NOT p_locale=ANY(constraints.allowed_locales)
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
            IF NOT EXISTS (SELECT 1 FROM jsonb_object_keys(coalesce(p_labels,'{}'::jsonb)))
               AND p_locale IS NULL THEN
                RAISE EXCEPTION 'NAVIGATION_LABEL_REQUIRED' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_list(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,tag text,enabled boolean,is_default boolean,
            "position" integer,metadata jsonb,row_version integer,created_at timestamptz,
            updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; visible_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'site:read');
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            SELECT count(*) INTO visible_count FROM content.site_locale l
            WHERE l.site_id=p_site_id
              AND (cardinality(constraints.allowed_locales)=0 OR l.tag=ANY(constraints.allowed_locales));
            IF constraints.max_visible_locales IS NOT NULL AND visible_count>constraints.max_visible_locales THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_LIMIT' USING ERRCODE='P0007';
            END IF;
            RETURN QUERY SELECT l.id,l.site_id,l.tag,l.enabled,l.is_default,l.position,l.metadata,l.row_version,l.created_at,l.updated_at
            FROM content.site_locale l WHERE l.site_id=p_site_id
              AND (cardinality(constraints.allowed_locales)=0 OR l.tag=ANY(constraints.allowed_locales))
            ORDER BY l.position,l.tag COLLATE "C";
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_get(p_site_id uuid,p_locale_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,tag text,enabled boolean,is_default boolean,
            "position" integer,metadata jsonb,row_version integer,created_at timestamptz,
            updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; found_locale content.site_locale;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'site:read');
            SELECT l.* INTO found_locale FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_locale_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'LOCALE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_locales)>0 AND NOT found_locale.tag=ANY(constraints.allowed_locales) THEN
                RAISE EXCEPTION 'LOCALE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            RETURN QUERY SELECT found_locale.id,found_locale.site_id,found_locale.tag,
                found_locale.enabled,found_locale.is_default,found_locale.position,
                found_locale.metadata,found_locale.row_version,found_locale.created_at,
                found_locale.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_create(
            p_site_id uuid,p_tag text,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,tag text,enabled boolean,is_default boolean,
            "position" integer,metadata jsonb,row_version integer,created_at timestamptz,
            updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            visible_count bigint; created content.site_locale;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'locale:configure');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_locales)>0 AND NOT p_tag=ANY(constraints.allowed_locales) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
            SELECT count(*) INTO visible_count FROM content.site_locale l
            WHERE l.site_id=p_site_id
              AND (cardinality(constraints.allowed_locales)=0 OR l.tag=ANY(constraints.allowed_locales));
            IF constraints.max_visible_locales IS NOT NULL AND visible_count>=constraints.max_visible_locales THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_LIMIT' USING ERRCODE='P0007'; END IF;
            IF p_tag IS NULL OR p_tag !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
               OR p_position IS NULL OR p_position NOT BETWEEN 0 AND 999
               OR p_metadata IS NULL OR jsonb_typeof(p_metadata)<>'object'
               OR p_default AND NOT p_enabled
            THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF NOT EXISTS (SELECT 1 FROM content.site_locale l WHERE l.site_id=p_site_id AND l.is_default)
               AND NOT p_default THEN RAISE EXCEPTION 'LOCALE_DEFAULT_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            IF p_default THEN
                UPDATE content.site_locale l SET is_default=false,
                    row_version=l.row_version+1,updated_at=now()
                WHERE l.site_id=p_site_id AND l.is_default;
            END IF;
            INSERT INTO content.site_locale(site_id,tag,enabled,is_default,position,metadata)
            VALUES(p_site_id,p_tag,p_enabled,p_default,p_position,p_metadata);
            SELECT l.* INTO created FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.tag=p_tag;
            RETURN QUERY SELECT created.id,created.site_id,created.tag,created.enabled,
                created.is_default,created.position,created.metadata,created.row_version,
                created.created_at,created.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_update(
            p_site_id uuid,p_locale_id uuid,p_enabled boolean,p_default boolean,
            p_position integer,p_metadata jsonb,p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,tag text,enabled boolean,is_default boolean,
            "position" integer,metadata jsonb,row_version integer,created_at timestamptz,
            updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.site_locale; updated content.site_locale;
            constraints record; new_enabled boolean; new_default boolean;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'locale:configure');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT l.* INTO old FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_locale_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'LOCALE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_locales)>0 AND NOT old.tag=ANY(constraints.allowed_locales) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
            IF p_enabled IS NULL AND p_default IS NULL AND p_position IS NULL AND p_metadata IS NULL
            THEN RAISE EXCEPTION 'LOCALE_UPDATE_EMPTY' USING ERRCODE='P0003'; END IF;
            new_enabled:=coalesce(p_enabled,old.enabled); new_default:=coalesce(p_default,old.is_default);
            IF new_default AND NOT new_enabled THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF old.is_default AND NOT new_default THEN RAISE EXCEPTION 'LOCALE_DEFAULT_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old.is_default AND NOT new_enabled THEN RAISE EXCEPTION 'LOCALE_REFERENCED' USING ERRCODE='P0003'; END IF;
            IF NOT new_enabled AND (
                EXISTS (SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.locale=old.tag AND p.deleted_at IS NULL)
                OR EXISTS (SELECT 1 FROM content.navigation n WHERE n.site_id=p_site_id AND n.labels ? old.tag)
                OR EXISTS (SELECT 1 FROM content.navigation_item n WHERE n.site_id=p_site_id AND (n.locale=old.tag OR n.labels ? old.tag))
                OR EXISTS (SELECT 1 FROM content.redirect r WHERE r.site_id=p_site_id AND r.locale=old.tag)
                OR EXISTS (SELECT 1 FROM content.content_item_translation t
                    JOIN content.content_item i ON i.id=t.item_id AND i.site_id=p_site_id
                    WHERE t.locale=old.tag AND i.status<>'DELETED')
            ) THEN RAISE EXCEPTION 'LOCALE_REFERENCED' USING ERRCODE='P0003'; END IF;
            IF p_position IS NOT NULL AND p_position NOT BETWEEN 0 AND 999 THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_metadata IS NOT NULL AND (jsonb_typeof(p_metadata)<>'object' OR octet_length(p_metadata::text)>16384) THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF new_default THEN
                UPDATE content.site_locale l SET is_default=false,
                    row_version=l.row_version+1,updated_at=now()
                WHERE l.site_id=p_site_id AND l.id<>p_locale_id AND l.is_default;
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            UPDATE content.site_locale AS l SET enabled=new_enabled,is_default=new_default,
                position=coalesce(p_position,l.position),metadata=coalesce(p_metadata,l.metadata),
                row_version=l.row_version+1,updated_at=now()
            WHERE l.site_id=p_site_id AND l.id=p_locale_id AND l.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT l.* INTO updated FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.id=p_locale_id;
            RETURN QUERY SELECT updated.id,updated.site_id,updated.tag,updated.enabled,
                updated.is_default,updated.position,updated.metadata,updated.row_version,
                updated.created_at,updated.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_locale_delete(p_site_id uuid,p_locale_id uuid,p_expected integer)
        RETURNS TABLE(id uuid,site_id uuid,tag text,enabled boolean,is_default boolean,
            "position" integer,metadata jsonb,row_version integer,created_at timestamptz,
            updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.site_locale;
            constraints record;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'locale:configure');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT l.* INTO old FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_locale_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'LOCALE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF old.is_default THEN RAISE EXCEPTION 'LOCALE_DEFAULT_REQUIRED' USING ERRCODE='P0003'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_locales)>0 AND NOT old.tag=ANY(constraints.allowed_locales) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
            IF EXISTS (SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.locale=old.tag AND p.deleted_at IS NULL)
               OR EXISTS (SELECT 1 FROM content.navigation n WHERE n.site_id=p_site_id AND n.labels ? old.tag)
               OR EXISTS (SELECT 1 FROM content.navigation_item n WHERE n.site_id=p_site_id AND (n.locale=old.tag OR n.labels ? old.tag))
               OR EXISTS (SELECT 1 FROM content.redirect r WHERE r.site_id=p_site_id AND r.locale=old.tag)
               OR EXISTS (SELECT 1 FROM content.content_item_translation t JOIN content.content_item i ON i.id=t.item_id AND i.site_id=p_site_id WHERE t.locale=old.tag AND i.status<>'DELETED')
            THEN RAISE EXCEPTION 'LOCALE_REFERENCED' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            DELETE FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_locale_id AND l.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT old.id,old.site_id,old.tag,old.enabled,old.is_default,
                old.position,old.metadata,old.row_version,old.created_at,old.updated_at;
        END; $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_list(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,labels jsonb,
            settings jsonb,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; visible_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'navigation:read');
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            SELECT count(*) INTO visible_count FROM content.navigation n
            WHERE n.site_id=p_site_id
              AND (cardinality(constraints.allowed_navigation_keys)=0 OR n."key"=ANY(constraints.allowed_navigation_keys))
              AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids));
            IF constraints.max_visible_navigations IS NOT NULL AND visible_count>constraints.max_visible_navigations THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_LIMIT' USING ERRCODE='P0007'; END IF;
            RETURN QUERY SELECT n.id,n.site_id,n.\"key\",n.label,n.labels,n.settings,n.row_version,n.created_at,n.updated_at
            FROM content.navigation n WHERE n.site_id=p_site_id
              AND (cardinality(constraints.allowed_navigation_keys)=0 OR n.\"key\"=ANY(constraints.allowed_navigation_keys))
              AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids))
            ORDER BY n.\"key\" COLLATE \"C\",n.id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_get(p_site_id uuid,p_navigation_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,labels jsonb,
            settings jsonb,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; found_navigation content.navigation;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'navigation:read');
            SELECT n.* INTO found_navigation FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT found_navigation.\"key\"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT found_navigation.id=ANY(constraints.allowed_navigation_ids))
            THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            RETURN QUERY SELECT found_navigation.id,found_navigation.site_id,
                found_navigation."key",found_navigation.label,found_navigation.labels,
                found_navigation.settings,found_navigation.row_version,
                found_navigation.created_at,found_navigation.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_create(
            p_site_id uuid,p_key text,p_label text,p_labels jsonb,p_settings jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,labels jsonb,
            settings jsonb,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            visible_count bigint; created content.navigation;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'navigation:create');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_navigation_keys)>0 AND NOT p_key=ANY(constraints.allowed_navigation_keys)
               OR cardinality(constraints.allowed_navigation_ids)>0
            THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_DENIED' USING ERRCODE='P0007'; END IF;
            SELECT count(*) INTO visible_count FROM content.navigation n
            WHERE n.site_id=p_site_id
              AND (cardinality(constraints.allowed_navigation_keys)=0 OR n."key"=ANY(constraints.allowed_navigation_keys))
              AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids));
            IF constraints.max_visible_navigations IS NOT NULL AND visible_count>=constraints.max_visible_navigations THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_LIMIT' USING ERRCODE='P0007'; END IF;
            IF p_key IS NULL OR p_key !~ '^[A-Za-z0-9][A-Za-z0-9._~-]{0,62}$'
               OR p_label IS NULL OR btrim(p_label)='' OR length(p_label)>256
               OR p_labels IS NULL OR jsonb_typeof(p_labels)<>'object' OR octet_length(p_labels::text)>16384
               OR p_settings IS NULL OR jsonb_typeof(p_settings)<>'object' OR octet_length(p_settings::text)>16384
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,p_labels);
            IF EXISTS (SELECT 1 FROM content.navigation n WHERE n.site_id=p_site_id AND n.\"key\"=p_key) THEN
                RAISE EXCEPTION 'NAVIGATION_KEY_CONFLICT' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            INSERT INTO content.navigation(site_id,\"key\",label,labels,settings,row_version)
            VALUES(p_site_id,p_key,p_label,p_labels,p_settings,1);
            SELECT n.* INTO created FROM content.navigation n
            WHERE n.site_id=p_site_id AND n.\"key\"=p_key;
            RETURN QUERY SELECT created.id,created.site_id,created."key",created.label,
                created.labels,created.settings,created.row_version,created.created_at,
                created.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_update(
            p_site_id uuid,p_navigation_id uuid,p_label text,p_labels jsonb,
            p_settings jsonb,p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,labels jsonb,
            settings jsonb,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.navigation;
            updated content.navigation; constraints record;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'navigation:write');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT n.* INTO old FROM content.navigation n WHERE n.site_id=p_site_id AND n.id=p_navigation_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT old.\"key\"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT old.id=ANY(constraints.allowed_navigation_ids))
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_DENIED' USING ERRCODE='P0007'; END IF;
            IF p_label IS NULL AND p_labels IS NULL AND p_settings IS NULL THEN
                RAISE EXCEPTION 'NAVIGATION_UPDATE_EMPTY' USING ERRCODE='P0003'; END IF;
            IF p_label IS NOT NULL AND (btrim(p_label)='' OR length(p_label)>256)
               OR p_labels IS NOT NULL AND (jsonb_typeof(p_labels)<>'object' OR octet_length(p_labels::text)>16384)
               OR p_settings IS NOT NULL AND (jsonb_typeof(p_settings)<>'object' OR octet_length(p_settings::text)>16384)
            THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_labels IS NOT NULL THEN
                PERFORM content.slaif_agent_navigation_validate_labels(p_site_id,p_labels);
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            UPDATE content.navigation AS n SET label=coalesce(p_label,n.label),labels=coalesce(p_labels,n.labels),
                settings=coalesce(p_settings,n.settings),row_version=n.row_version+1,updated_at=now()
            WHERE n.site_id=p_site_id AND n.id=p_navigation_id AND n.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT n.* INTO updated FROM content.navigation n
            WHERE n.site_id=p_site_id AND n.id=p_navigation_id;
            RETURN QUERY SELECT updated.id,updated.site_id,updated."key",updated.label,
                updated.labels,updated.settings,updated.row_version,updated.created_at,
                updated.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_delete(p_site_id uuid,p_navigation_id uuid,p_expected integer)
        RETURNS TABLE(id uuid,site_id uuid,\"key\" text,label text,labels jsonb,
            settings jsonb,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.navigation; constraints record;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'navigation:delete');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT n.* INTO old FROM content.navigation n WHERE n.site_id=p_site_id AND n.id=p_navigation_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT old."key"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT old.id=ANY(constraints.allowed_navigation_ids)) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_DENIED' USING ERRCODE='P0007'; END IF;
            IF constraints.delete_enabled IS FALSE THEN RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0007'; END IF;
            IF EXISTS (SELECT 1 FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id) THEN
                RAISE EXCEPTION 'NAVIGATION_CHILDREN' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            DELETE FROM content.navigation n WHERE n.site_id=p_site_id AND n.id=p_navigation_id AND n.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT old.id,old.site_id,old."key",old.label,old.labels,
                old.settings,old.row_version,old.created_at,old.updated_at;
        END; $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_apply(
            p_site_id uuid,p_item_id uuid,p_navigation_id uuid,p_parent_id uuid,
            p_page_id uuid,p_target_kind text,p_target_value text,p_labels jsonb,
            p_locale text,p_before uuid,p_after uuid,p_expected integer,p_is_create boolean
        ) RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            old content.navigation_item; created content.navigation_item;
            created_id uuid;
            navigation_row content.navigation; parent_row content.navigation_item;
            cursor_id uuid; anchor_position integer; desired_position integer;
            depth integer:=1; item_count bigint;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'navigation:write');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT n.* INTO navigation_row FROM content.navigation n
            WHERE n.id=p_navigation_id AND n.site_id=p_site_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT navigation_row.\"key\"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT navigation_row.id=ANY(constraints.allowed_navigation_ids))
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_DENIED' USING ERRCODE='P0007'; END IF;
            IF NOT p_is_create THEN
                SELECT i.* INTO old FROM content.navigation_item i
                WHERE i.id=p_item_id AND i.site_id=p_site_id FOR UPDATE;
                IF NOT FOUND OR old.navigation_id<>p_navigation_id THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
                IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            END IF;
            IF p_before IS NOT NULL AND p_after IS NOT NULL THEN RAISE EXCEPTION 'NAVIGATION_ANCHORS_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_before=p_item_id OR p_after=p_item_id THEN RAISE EXCEPTION 'NAVIGATION_ANCHORS_INVALID' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_target(p_site_id,p_page_id,p_target_kind,p_target_value,p_labels,p_locale);
            IF p_parent_id IS NOT NULL THEN
                SELECT i.* INTO parent_row FROM content.navigation_item i
                WHERE i.id=p_parent_id AND i.site_id=p_site_id AND i.navigation_id=p_navigation_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003'; END IF;
                cursor_id:=p_parent_id;
                LOOP
                    IF NOT p_is_create AND cursor_id=p_item_id THEN RAISE EXCEPTION 'NAVIGATION_CYCLE' USING ERRCODE='P0003'; END IF;
                    SELECT i.parent_id INTO cursor_id FROM content.navigation_item i
                    WHERE i.id=cursor_id AND i.site_id=p_site_id AND i.navigation_id=p_navigation_id;
                    depth:=depth+1; EXIT WHEN cursor_id IS NULL;
                    IF depth>coalesce(constraints.max_navigation_depth,8) THEN RAISE EXCEPTION 'NAVIGATION_DEPTH' USING ERRCODE='P0003'; END IF;
                END LOOP;
            END IF;
            IF constraints.max_visible_navigation_items IS NOT NULL THEN
                SELECT count(*) INTO item_count
                FROM content.navigation_item i JOIN content.navigation n
                  ON n.site_id=i.site_id AND n.id=i.navigation_id
                WHERE i.site_id=p_site_id
                  AND (cardinality(constraints.allowed_navigation_keys)=0 OR n."key"=ANY(constraints.allowed_navigation_keys))
                  AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids));
                IF (p_is_create AND item_count>=constraints.max_visible_navigation_items)
                   OR (NOT p_is_create AND item_count>constraints.max_visible_navigation_items) THEN
                    RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_ITEM_LIMIT' USING ERRCODE='P0007';
                END IF;
            END IF;
            IF p_before IS NOT NULL THEN
                SELECT compact_position INTO anchor_position FROM (
                    SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                    FROM content.navigation_item i
                    WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
                      AND i.parent_id IS NOT DISTINCT FROM p_parent_id
                      AND (p_is_create OR i.id<>p_item_id)
                ) ranked WHERE ranked.id=p_before;
                IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_ANCHOR_INVALID' USING ERRCODE='P0003'; END IF;
                desired_position:=anchor_position;
            ELSIF p_after IS NOT NULL THEN
                SELECT compact_position INTO anchor_position FROM (
                    SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                    FROM content.navigation_item i
                    WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
                      AND i.parent_id IS NOT DISTINCT FROM p_parent_id
                      AND (p_is_create OR i.id<>p_item_id)
                ) ranked WHERE ranked.id=p_after;
                IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_ANCHOR_INVALID' USING ERRCODE='P0003'; END IF;
                desired_position:=anchor_position+1;
            ELSE
                SELECT count(*)::integer INTO desired_position FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM p_parent_id
                  AND (p_is_create OR i.id<>p_item_id);
            END IF;
            IF desired_position IS NULL OR desired_position>999 THEN RAISE EXCEPTION 'NAVIGATION_POSITION_LIMIT' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            -- Remove a moved row from its old sibling set, then compact only
            -- rows whose final position changes.  The deferred sibling
            -- constraint permits the transaction-local reordering.
            IF NOT p_is_create THEN
                UPDATE content.navigation_item i SET position=999
                WHERE i.id=p_item_id AND i.site_id=p_site_id;
                WITH ranked AS (
                    SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS new_position
                    FROM content.navigation_item i
                    WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                      AND i.parent_id IS NOT DISTINCT FROM old.parent_id AND i.id<>p_item_id
                ) UPDATE content.navigation_item i SET position=ranked.new_position,
                    row_version=CASE WHEN i.position IS DISTINCT FROM ranked.new_position THEN i.row_version+1 ELSE i.row_version END,
                    updated_at=CASE WHEN i.position IS DISTINCT FROM ranked.new_position THEN now() ELSE i.updated_at END
                  FROM ranked WHERE i.id=ranked.id;
            END IF;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS compact_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM p_parent_id
                  AND (p_is_create OR i.id<>p_item_id)
            ), final_positions AS (
                SELECT ranked.id,
                    ranked.compact_position + CASE
                        WHEN p_before IS NOT NULL AND ranked.compact_position>=desired_position THEN 1
                        WHEN p_after IS NOT NULL AND ranked.compact_position>=desired_position THEN 1
                        ELSE 0 END AS new_position
                FROM ranked
            )
            UPDATE content.navigation_item i SET position=final_positions.new_position,
                row_version=CASE WHEN i.position IS DISTINCT FROM final_positions.new_position THEN i.row_version+1 ELSE i.row_version END,
                updated_at=CASE WHEN i.position IS DISTINCT FROM final_positions.new_position THEN now() ELSE i.updated_at END
            FROM final_positions WHERE i.id=final_positions.id;
            IF p_is_create THEN
                created_id:=gen_random_uuid();
                INSERT INTO content.navigation_item(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,target_value,labels,locale,position,row_version)
                VALUES(created_id,p_site_id,p_navigation_id,p_parent_id,coalesce(p_parent_id,'00000000-0000-0000-0000-000000000000'::uuid),p_page_id,p_target_kind,p_target_value,p_labels,p_locale,desired_position,1);
            ELSE
                UPDATE content.navigation_item i SET parent_id=p_parent_id,parent_key=coalesce(p_parent_id,'00000000-0000-0000-0000-000000000000'::uuid),page_id=p_page_id,
                    target_kind=p_target_kind,target_value=p_target_value,labels=p_labels,locale=p_locale,
                    position=desired_position,row_version=i.row_version+1,updated_at=now()
                WHERE i.id=p_item_id AND i.site_id=p_site_id AND i.row_version=p_expected
                ;
                IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            END IF;
            SELECT i.* INTO created FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=coalesce(created_id,p_item_id);
            RETURN QUERY SELECT created.id,created.site_id,created.navigation_id,
                created.parent_id,created.page_id,created.target_kind,created.target_value,
                created.labels,created.locale,created.position,created.row_version,
                created.created_at,created.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_create(
            p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_before uuid,p_after uuid
        ) RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_agent_navigation_item_apply(
                p_site_id,NULL,p_navigation_id,p_parent_id,p_page_id,p_target_kind,
                p_target_value,p_labels,p_locale,p_before,p_after,NULL,true);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_update(
            p_site_id uuid,p_item_id uuid,p_navigation_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_expected integer
        ) RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; navigation_row content.navigation; item_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'navigation:write');
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT n.* INTO navigation_row
            FROM content.navigation_item i
            JOIN content.navigation n ON n.site_id=i.site_id AND n.id=i.navigation_id
            WHERE i.site_id=p_site_id AND i.id=p_item_id AND i.navigation_id=p_navigation_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT navigation_row."key"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT navigation_row.id=ANY(constraints.allowed_navigation_ids))
            THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT count(*) INTO item_count
            FROM content.navigation_item i JOIN content.navigation n
              ON n.site_id=i.site_id AND n.id=i.navigation_id
            WHERE i.site_id=p_site_id
              AND (cardinality(constraints.allowed_navigation_keys)=0 OR n."key"=ANY(constraints.allowed_navigation_keys))
              AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids));
            IF constraints.max_visible_navigation_items IS NOT NULL AND item_count>constraints.max_visible_navigation_items
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_ITEM_LIMIT' USING ERRCODE='P0007'; END IF;
            IF p_item_id IS NULL OR p_navigation_id IS NULL OR p_expected IS NULL OR p_expected<=0
               OR p_target_kind IS NULL OR p_target_value IS NULL OR p_labels IS NULL
            THEN RAISE EXCEPTION 'NAVIGATION_UPDATE_EMPTY' USING ERRCODE='P0003'; END IF;
            PERFORM content.slaif_agent_navigation_validate_target(
                p_site_id,p_page_id,p_target_kind,p_target_value,p_labels,p_locale);
            RETURN QUERY
            UPDATE content.navigation_item i SET
                page_id=CASE WHEN p_target_kind='PAGE' THEN p_page_id ELSE NULL END,
                target_kind=p_target_kind,target_value=p_target_value,labels=p_labels,
                locale=p_locale,row_version=i.row_version+1,updated_at=now()
            WHERE i.site_id=p_site_id AND i.id=p_item_id
              AND i.navigation_id=p_navigation_id AND i.row_version=p_expected
            RETURNING i.id,i.site_id,i.navigation_id,i.parent_id,i.page_id,i.target_kind,
                i.target_value,i.labels,i.locale,i.position,i.row_version,i.created_at,i.updated_at;
            IF NOT FOUND THEN
                IF EXISTS (SELECT 1 FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_item_id)
                THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
                ELSE RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            END IF;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_list(p_site_id uuid,p_navigation_id uuid)
        RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; navigation_row content.navigation; item_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'navigation:read');
            SELECT n.* INTO navigation_row FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT navigation_row.\"key\"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT navigation_row.id=ANY(constraints.allowed_navigation_ids))
            THEN RAISE EXCEPTION 'NAVIGATION_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT count(*) INTO item_count
            FROM content.navigation_item i JOIN content.navigation n
              ON n.site_id=i.site_id AND n.id=i.navigation_id
            WHERE i.site_id=p_site_id
              AND (cardinality(constraints.allowed_navigation_keys)=0 OR n."key"=ANY(constraints.allowed_navigation_keys))
              AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids));
            IF constraints.max_visible_navigation_items IS NOT NULL AND item_count>constraints.max_visible_navigation_items THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_ITEM_LIMIT' USING ERRCODE='P0007'; END IF;
            RETURN QUERY SELECT i.id,i.site_id,i.navigation_id,i.parent_id,i.page_id,i.target_kind,
                i.target_value,i.labels,i.locale,i.position,i.row_version,i.created_at,i.updated_at
            FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id
            ORDER BY i.parent_id NULLS FIRST,i.position,i.id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_get(p_site_id uuid,p_item_id uuid)
        RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; navigation_row content.navigation;
            found_item content.navigation_item; item_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'navigation:read');
            SELECT n.* INTO navigation_row
            FROM content.navigation_item i
            JOIN content.navigation n ON n.site_id=i.site_id AND n.id=i.navigation_id
            WHERE i.site_id=p_site_id AND i.id=p_item_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT i.* INTO found_item FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_item_id;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT navigation_row."key"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT navigation_row.id=ANY(constraints.allowed_navigation_ids))
            THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            SELECT count(*) INTO item_count
            FROM content.navigation_item i JOIN content.navigation n
              ON n.site_id=i.site_id AND n.id=i.navigation_id
            WHERE i.site_id=p_site_id
              AND (cardinality(constraints.allowed_navigation_keys)=0 OR n."key"=ANY(constraints.allowed_navigation_keys))
              AND (cardinality(constraints.allowed_navigation_ids)=0 OR n.id=ANY(constraints.allowed_navigation_ids));
            IF constraints.max_visible_navigation_items IS NOT NULL AND item_count>constraints.max_visible_navigation_items
            THEN RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_ITEM_LIMIT' USING ERRCODE='P0007'; END IF;
            RETURN QUERY SELECT found_item.id,found_item.site_id,found_item.navigation_id,
                found_item.parent_id,found_item.page_id,found_item.target_kind,
                found_item.target_value,found_item.labels,found_item.locale,
                found_item.position,found_item.row_version,found_item.created_at,
                found_item.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_move(
            p_site_id uuid,p_item_id uuid,p_parent_id uuid,p_before uuid,p_after uuid,p_expected integer
        ) RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.navigation_item;
        BEGIN
            SELECT i.* INTO old FROM content.navigation_item i WHERE i.id=p_item_id AND i.site_id=p_site_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            RETURN QUERY SELECT * FROM content.slaif_agent_navigation_item_apply(
                p_site_id,p_item_id,old.navigation_id,p_parent_id,old.page_id,old.target_kind,
                old.target_value,old.labels,old.locale,p_before,p_after,p_expected,false);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_navigation_item_delete(
            p_site_id uuid,p_item_id uuid,p_expected integer
        ) RETURNS TABLE("""
        + _ITEM_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.navigation_item;
            constraints record; navigation_row content.navigation;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'navigation:delete');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT i.* INTO old FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_item_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NAVIGATION_ITEM_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            SELECT n.* INTO navigation_row FROM content.navigation n
            WHERE n.site_id=p_site_id AND n.id=old.navigation_id;
            IF (cardinality(constraints.allowed_navigation_keys)>0 AND NOT navigation_row."key"=ANY(constraints.allowed_navigation_keys))
               OR (cardinality(constraints.allowed_navigation_ids)>0 AND NOT navigation_row.id=ANY(constraints.allowed_navigation_ids)) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_NAVIGATION_DENIED' USING ERRCODE='P0007'; END IF;
            IF constraints.delete_enabled IS FALSE THEN RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0007'; END IF;
            IF EXISTS (SELECT 1 FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.parent_id=p_item_id) THEN
                RAISE EXCEPTION 'NAVIGATION_CHILDREN' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005'; END IF;
            DELETE FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_item_id AND i.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            WITH ranked AS (
                SELECT i.id,(row_number() OVER (ORDER BY i.position,i.id)-1)::integer AS new_position
                FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.navigation_id=old.navigation_id
                  AND i.parent_id IS NOT DISTINCT FROM old.parent_id
            ) UPDATE content.navigation_item i SET position=ranked.new_position,
                row_version=CASE WHEN i.position IS DISTINCT FROM ranked.new_position THEN i.row_version+1 ELSE i.row_version END,
                updated_at=CASE WHEN i.position IS DISTINCT FROM ranked.new_position THEN now() ELSE i.updated_at END
            FROM ranked WHERE i.id=ranked.id;
            RETURN QUERY SELECT old.id,old.site_id,old.navigation_id,old.parent_id,
                old.page_id,old.target_kind,old.target_value,old.labels,old.locale,
                old.position,old.row_version,old.created_at,old.updated_at;
        END; $fn$
        """
    )

    for function in (
        "content.slaif_agent_locale_list(uuid)",
        "content.slaif_agent_locale_get(uuid,uuid)",
        "content.slaif_agent_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
        "content.slaif_agent_locale_update(uuid,uuid,boolean,boolean,integer,jsonb,integer)",
        "content.slaif_agent_locale_delete(uuid,uuid,integer)",
        "content.slaif_agent_navigation_list(uuid)",
        "content.slaif_agent_navigation_get(uuid,uuid)",
        "content.slaif_agent_navigation_create(uuid,text,text,jsonb,jsonb)",
        "content.slaif_agent_navigation_update(uuid,uuid,text,jsonb,jsonb,integer)",
        "content.slaif_agent_navigation_delete(uuid,uuid,integer)",
        "content.slaif_agent_navigation_item_list(uuid,uuid)",
        "content.slaif_agent_navigation_item_get(uuid,uuid)",
        "content.slaif_agent_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,uuid,uuid)",
        "content.slaif_agent_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_agent_navigation_item_move(uuid,uuid,uuid,uuid,uuid,integer)",
        "content.slaif_agent_navigation_item_delete(uuid,uuid,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")
    for function in (
        "content.slaif_agent_navigation_validate_labels(uuid,jsonb)",
        "content.slaif_agent_navigation_validate_target(uuid,uuid,text,text,jsonb,text)",
        "content.slaif_agent_navigation_item_apply(uuid,uuid,uuid,uuid,uuid,text,text,jsonb,text,uuid,uuid,integer,boolean)",
        "control.slaif_agent_structural_lock(uuid)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime"
        )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_agent_structural_lock(uuid) "
        "TO slaif_editor_runtime"
    )


def downgrade() -> None:
    # Direct Alembic downgrade must not operate on active COW views. The
    # bootstrap path disables COW through the public foundation API first.
    op.execute(
        """
        DO $$
        DECLARE relation_kind \"char\";
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n
              ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='navigation';
            IF relation_kind='v' THEN
                RAISE EXCEPTION '049_DOWNGRADE_REQUIRES_PUBLIC_COW_DISABLE'
                    USING ERRCODE='P0003',
                    HINT='Run the product bootstrap downgrade so agentcow.postgres.disable_cow_schema disables COW before Alembic.';
            END IF;
        END;
        $$
        """
    )
    for function in (
        "content.slaif_agent_navigation_item_delete(uuid,uuid,integer)",
        "content.slaif_agent_navigation_item_move(uuid,uuid,uuid,uuid,uuid,integer)",
        "content.slaif_agent_navigation_item_get(uuid,uuid)",
        "content.slaif_agent_navigation_item_list(uuid,uuid)",
        "content.slaif_agent_navigation_item_update(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)",
        "content.slaif_agent_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,uuid,uuid)",
        "content.slaif_agent_navigation_item_apply(uuid,uuid,uuid,uuid,uuid,text,text,jsonb,text,uuid,uuid,integer,boolean)",
        "content.slaif_agent_navigation_delete(uuid,uuid,integer)",
        "content.slaif_agent_navigation_update(uuid,uuid,text,jsonb,jsonb,integer)",
        "content.slaif_agent_navigation_create(uuid,text,text,jsonb,jsonb)",
        "content.slaif_agent_navigation_get(uuid,uuid)",
        "content.slaif_agent_navigation_list(uuid)",
        "content.slaif_agent_locale_delete(uuid,uuid,integer)",
        "content.slaif_agent_locale_update(uuid,uuid,boolean,boolean,integer,jsonb,integer)",
        "content.slaif_agent_locale_create(uuid,text,boolean,boolean,integer,jsonb)",
        "content.slaif_agent_locale_get(uuid,uuid)",
        "content.slaif_agent_locale_list(uuid)",
        "content.slaif_agent_navigation_validate_labels(uuid,jsonb)",
        "content.slaif_agent_navigation_validate_target(uuid,uuid,text,text,jsonb,text)",
        "control.slaif_agent_structural_lock(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function} CASCADE")
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(
        """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action IN ('PAGE_MOVED','PAGE_RESTORED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
        )
        """
    )
    op.execute(
        "ALTER TABLE content.navigation_item DROP CONSTRAINT navigation_item_sibling_position"
    )
    op.execute("DROP INDEX IF EXISTS content.navigation_item_sibling_position")
    op.execute("ALTER TABLE content.navigation_item DROP COLUMN parent_key")
    op.execute(
        "CREATE UNIQUE INDEX navigation_item_sibling_position ON content.navigation_item(site_id,navigation_id,coalesce(parent_id,'00000000-0000-0000-0000-000000000000'::uuid),position)"
    )
    op.execute("ALTER TABLE content.navigation DROP COLUMN labels")
    op.execute("ALTER TABLE content.navigation DROP COLUMN row_version")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_create(
            p_site_id uuid,p_key text,p_label text,p_settings jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.navigation(site_id,"key",label,settings)
            VALUES(p_site_id,p_key,p_label,p_settings);
            RETURN QUERY SELECT n.* FROM content.navigation n
            WHERE n.site_id=p_site_id AND n."key"=p_key LIMIT 1;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_list(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $fn$
            SELECT n.* FROM content.navigation n WHERE n.site_id=p_site_id
            ORDER BY n."key" COLLATE "C"
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_get(p_nav_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $fn$
            SELECT n.* FROM content.navigation n WHERE n.id=p_nav_id
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_update(
            p_nav_id uuid,p_label text,p_settings jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,
            created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            UPDATE content.navigation n SET label=coalesce(p_label,n.label),
                settings=coalesce(p_settings,n.settings),updated_at=now()
            WHERE n.id=p_nav_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            RETURN QUERY SELECT n.* FROM content.navigation n WHERE n.id=p_nav_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_create(
            p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE parent_nav uuid; created content.navigation_item;
        BEGIN
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || '_navigation',0));
            IF NOT EXISTS (SELECT 1 FROM content.navigation n
                WHERE n.id=p_navigation_id AND n.site_id=p_site_id) THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF p_parent_id IS NOT NULL THEN
                SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i
                WHERE i.id=p_parent_id AND i.site_id=p_site_id;
                IF parent_nav IS NULL OR parent_nav<>p_navigation_id THEN
                    RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
            END IF;
            IF p_target_kind='PAGE' AND (p_page_id IS NULL OR p_target_value<>p_page_id::text) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target_kind<>'PAGE' AND p_page_id IS NOT NULL THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_page_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id
            ) THEN
                RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL')
               OR p_position NOT BETWEEN 0 AND 999
               OR jsonb_typeof(p_labels)<>'object' THEN
                RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003';
            END IF;
            INSERT INTO content.navigation_item(
                site_id,navigation_id,parent_id,page_id,target_kind,target_value,
                labels,locale,position
            ) VALUES(
                p_site_id,p_navigation_id,p_parent_id,p_page_id,p_target_kind,
                p_target_value,p_labels,p_locale,p_position
            ) RETURNING * INTO created;
            RETURN NEXT created;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_update(
            p_site_id uuid,p_id uuid,p_parent_id uuid,p_page_id uuid,
            p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,
            p_position integer,p_expected integer
        ) RETURNS SETOF content.navigation_item
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.navigation_item; parent_nav uuid; updated content.navigation_item;
        BEGIN
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || '_navigation',0));
            SELECT i.* INTO old FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF p_parent_id IS NOT NULL THEN
                SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i
                WHERE i.site_id=p_site_id AND i.id=p_parent_id;
                IF parent_nav IS NULL OR parent_nav<>old.navigation_id OR p_parent_id=p_id THEN
                    RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
            END IF;
            IF coalesce(p_target_kind,old.target_kind)='PAGE'
               AND (coalesce(p_page_id,old.page_id) IS NULL
                    OR coalesce(p_target_value,old.target_value)<>coalesce(p_page_id,old.page_id)::text)
            THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF coalesce(p_target_kind,old.target_kind)<>'PAGE'
               AND coalesce(p_page_id,old.page_id) IS NOT NULL
            THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            UPDATE content.navigation_item AS i SET parent_id=p_parent_id,
                page_id=CASE WHEN p_target_kind IS NOT NULL AND p_target_kind<>'PAGE'
                    THEN NULL ELSE coalesce(p_page_id,i.page_id) END,
                target_kind=coalesce(p_target_kind,i.target_kind),
                target_value=coalesce(p_target_value,i.target_value),
                labels=coalesce(p_labels,i.labels),locale=p_locale,
                position=coalesce(p_position,i.position),row_version=i.row_version+1,
                updated_at=now()
            WHERE i.site_id=p_site_id AND i.id=p_id;
            RETURN QUERY SELECT i.* FROM content.navigation_item i
            WHERE i.site_id=p_site_id AND i.id=p_id;
        END; $fn$
        """
    )

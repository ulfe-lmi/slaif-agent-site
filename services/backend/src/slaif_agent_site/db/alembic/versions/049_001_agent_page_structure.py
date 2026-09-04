# ruff: noqa: E501
"""Add capability-bound Agent page hierarchy and derived-route semantics."""

from __future__ import annotations

import re

from alembic import op

revision = "049_001"
down_revision = "048_001"
branch_labels = None
depends_on = None


_AGENT_PAGE_RETURN = """
    id uuid, site_id uuid, slug text, title text, status text, locale text,
    parent_id uuid, route_template text, effective_route text,
    deleted_at timestamptz, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""

_DOLLAR_TAG = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|)\$")


def _split_sql_statements(sql: str) -> tuple[str, ...]:
    """Split function DDL without splitting semicolons inside dollar quotes."""

    statements: list[str] = []
    current: list[str] = []
    dollar_tag: str | None = None
    single_quote = False
    double_quote = False
    index = 0
    while index < len(sql):
        character = sql[index]
        if dollar_tag is not None:
            if sql.startswith(dollar_tag, index):
                current.append(dollar_tag)
                index += len(dollar_tag)
                dollar_tag = None
                continue
            current.append(character)
            index += 1
            continue
        if single_quote:
            current.append(character)
            if character == "'":
                if index + 1 < len(sql) and sql[index + 1] == "'":
                    current.append("'")
                    index += 2
                    continue
                single_quote = False
            index += 1
            continue
        if double_quote:
            current.append(character)
            if character == '"':
                if index + 1 < len(sql) and sql[index + 1] == '"':
                    current.append('"')
                    index += 2
                    continue
                double_quote = False
            index += 1
            continue
        if character == "'":
            single_quote = True
            current.append(character)
            index += 1
            continue
        if character == '"':
            double_quote = True
            current.append(character)
            index += 1
            continue
        if character == "$":
            match = _DOLLAR_TAG.match(sql, index)
            if match is not None:
                dollar_tag = match.group(0)
                current.append(dollar_tag)
                index = match.end()
                continue
        if character == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(character)
        index += 1
    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return tuple(statements)


def _semantic_constraint_sql() -> str:
    return """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action = 'CONTENT_TYPE_CREATED' AND resource_type = 'content_type' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_TYPE_UPDATED' AND resource_type = 'content_type' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_TYPE_DELETED' AND resource_type = 'content_type' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'FIELD_DEFINITION_CREATED' AND resource_type = 'field_definition' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'FIELD_DEFINITION_UPDATED' AND resource_type = 'field_definition' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'FIELD_DEFINITION_DELETED' AND resource_type = 'field_definition' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'CONTENT_ITEM_CREATED' AND resource_type = 'content_item' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_UPDATED' AND resource_type = 'content_item' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_DELETED' AND resource_type = 'content_item' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'CONTENT_ITEM_TRANSLATION_CREATED' AND resource_type = 'content_item_translation' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_TRANSLATION_UPDATED' AND resource_type = 'content_item_translation' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'CONTENT_ITEM_TRANSLATION_DELETED' AND resource_type = 'content_item_translation' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'ITEM_RELATION_CREATED' AND resource_type = 'item_relation' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'ITEM_RELATION_UPDATED' AND resource_type = 'item_relation' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'ITEM_RELATION_DELETED' AND resource_type = 'item_relation' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'COLLECTION_VIEW_CREATED' AND resource_type = 'collection_view' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'COLLECTION_VIEW_UPDATED' AND resource_type = 'collection_view' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'COLLECTION_VIEW_DELETED' AND resource_type = 'collection_view' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'PAGE_CREATED' AND resource_type = 'page' AND http_method = 'POST' AND response_status = 201 AND quota_kind = 'mutation')
            OR (action = 'PAGE_UPDATED' AND resource_type = 'page' AND http_method = 'PATCH' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'PAGE_DELETED' AND resource_type = 'page' AND http_method = 'DELETE' AND response_status = 200 AND quota_kind = 'delete')
            OR (action = 'PAGE_MOVED' AND resource_type = 'page' AND http_method = 'POST' AND response_status = 200 AND quota_kind = 'mutation')
            OR (action = 'PAGE_RESTORED' AND resource_type = 'page' AND http_method = 'POST' AND response_status = 200 AND quota_kind = 'mutation')
        )
    """


def _idempotency_completion_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_complete(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_status_code integer,
            p_response_body jsonb, p_resource_type text, p_resource_id uuid,
            p_site_id uuid, p_action text, p_http_method text, p_quota_kind text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE expected_site uuid;
        BEGIN
            IF p_capability_id IS NULL OR p_workspace_id IS NULL
               OR p_idempotency_key IS NULL
               OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest IS NULL
               OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_operation_id IS NULL OR p_resource_id IS NULL
               OR p_action IS NULL OR p_http_method IS NULL
               OR p_quota_kind IS NULL
               OR NOT (
                   (p_action='CONTENT_TYPE_CREATED' AND p_resource_type='content_type' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_TYPE_UPDATED' AND p_resource_type='content_type' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_TYPE_DELETED' AND p_resource_type='content_type' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='FIELD_DEFINITION_CREATED' AND p_resource_type='field_definition' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='FIELD_DEFINITION_UPDATED' AND p_resource_type='field_definition' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='FIELD_DEFINITION_DELETED' AND p_resource_type='field_definition' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='CONTENT_ITEM_CREATED' AND p_resource_type='content_item' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_UPDATED' AND p_resource_type='content_item' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_DELETED' AND p_resource_type='content_item' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='CONTENT_ITEM_TRANSLATION_CREATED' AND p_resource_type='content_item_translation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_TRANSLATION_UPDATED' AND p_resource_type='content_item_translation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='CONTENT_ITEM_TRANSLATION_DELETED' AND p_resource_type='content_item_translation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='ITEM_RELATION_CREATED' AND p_resource_type='item_relation' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='ITEM_RELATION_UPDATED' AND p_resource_type='item_relation' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='ITEM_RELATION_DELETED' AND p_resource_type='item_relation' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='COLLECTION_VIEW_CREATED' AND p_resource_type='collection_view' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='COLLECTION_VIEW_UPDATED' AND p_resource_type='collection_view' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='COLLECTION_VIEW_DELETED' AND p_resource_type='collection_view' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='PAGE_CREATED' AND p_resource_type='page' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
                OR (p_action='PAGE_UPDATED' AND p_resource_type='page' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='PAGE_DELETED' AND p_resource_type='page' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
                OR (p_action='PAGE_MOVED' AND p_resource_type='page' AND p_http_method='POST' AND p_status_code=200 AND p_quota_kind='mutation')
                OR (p_action='PAGE_RESTORED' AND p_resource_type='page' AND p_http_method='POST' AND p_status_code=200 AND p_quota_kind='mutation')
               )
               OR p_response_body IS NULL
               OR jsonb_typeof(p_response_body) <> 'object'
               OR jsonb_typeof(p_response_body->'record') <> 'object'
               OR p_response_body->>'action' IS DISTINCT FROM p_action
               OR p_response_body->>'operation_id' IS DISTINCT FROM p_operation_id::text
               OR p_response_body->'record'->>'id' IS DISTINCT FROM p_resource_id::text
            THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001';
            END IF;

            SELECT workspace.site_id INTO expected_site
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id;
            IF expected_site IS NULL THEN
                RAISE EXCEPTION 'INVALID_SEMANTIC_COMPLETION' USING ERRCODE='P0001';
            END IF;

            UPDATE control.agent_idempotency
            SET status_code = p_status_code, response_body = p_response_body,
                resource_type = p_resource_type, resource_id = p_resource_id,
                completed_at = CURRENT_TIMESTAMP
            WHERE capability_id = p_capability_id
              AND workspace_id = p_workspace_id
              AND idempotency_key = p_idempotency_key
              AND request_digest = p_request_digest
              AND operation_id = p_operation_id AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'IDEMPOTENCY_RESERVATION_NOT_FOUND' USING ERRCODE='P0002';
            END IF;

            INSERT INTO audit.agent_mutation(
                operation_id, capability_id, workspace_id, site_id,
                resource_type, resource_id, request_digest, response_status,
                action, http_method, quota_kind
            ) VALUES (
                p_operation_id, p_capability_id, p_workspace_id, p_site_id,
                p_resource_type, p_resource_id, p_request_digest, p_status_code,
                p_action, p_http_method, p_quota_kind
            );
        END;
        $fn$
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
            max_page_depth integer
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
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            SELECT w.resource_constraints INTO result
            FROM control.workspace w
            JOIN control.site s ON s.id = w.site_id
            JOIN control.user_account a ON a.id = coalesce(w.delegator_id,w.created_by)
            WHERE w.id = workspace_id AND w.site_id = p_site_id
              AND w.status = 'ACTIVE' AND w.expires_at > CURRENT_TIMESTAMP
              AND s.status = 'ACTIVE' AND a.status = 'ACTIVE';
            IF result IS NULL OR jsonb_typeof(result) <> 'object' THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_object_keys(result) k
                WHERE k NOT IN (
                    'allowed_type_ids','allowed_type_keys','max_content_types',
                    'max_fields_per_type','delete_enabled','max_deletes',
                    'allowed_locales','route_prefix','allowed_page_root_ids',
                    'max_visible_pages','max_page_depth'
                )
            ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF (result ? 'allowed_type_ids' AND jsonb_typeof(result->'allowed_type_ids') <> 'array')
               OR (result ? 'allowed_type_keys' AND jsonb_typeof(result->'allowed_type_keys') <> 'array')
               OR (result ? 'allowed_locales' AND jsonb_typeof(result->'allowed_locales') <> 'array')
               OR (result ? 'allowed_page_root_ids' AND jsonb_typeof(result->'allowed_page_root_ids') <> 'array')
               OR (result ? 'delete_enabled' AND jsonb_typeof(result->'delete_enabled') <> 'boolean')
               OR (result ? 'route_prefix' AND (jsonb_typeof(result->'route_prefix') <> 'string' OR result->>'route_prefix' = ''))
               OR EXISTS (
                   SELECT 1 FROM (VALUES
                       ('max_content_types'),('max_fields_per_type'),('max_deletes'),
                       ('max_visible_pages'),('max_page_depth')
                   ) AS numeric_key(key)
                   WHERE result ? numeric_key.key
                     AND jsonb_typeof(result->numeric_key.key) <> 'number'
               )
            THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) v
                WHERE v !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_page_root_ids','[]'::jsonb)) v
                WHERE v !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) v
                WHERE v !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
            ) OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) value)) > 256
               OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_keys','[]'::jsonb)) value)) > 256
               OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) value)) > 64
               OR cardinality(ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_page_root_ids','[]'::jsonb)) value)) > 256
            THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF result ? 'route_prefix' AND (
                result->>'route_prefix' !~ '^/[a-z0-9][a-z0-9._~-]*(/[a-z0-9][a-z0-9._~-]*)*$'
                AND result->>'route_prefix' <> '/'
                OR result->>'route_prefix' ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
            ) THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_each_text(result) item
                WHERE item.key IN ('max_content_types','max_fields_per_type','max_deletes','max_visible_pages','max_page_depth')
                  AND (item.value !~ '^[0-9]+$' OR item.value::numeric > 2147483647)
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
            RETURN NEXT;
        END;
        $fn$
    """


def _page_functions_sql() -> str:
    return (
        """
        CREATE FUNCTION content.slaif_agent_page_ensure_locale(
            p_site_id uuid, p_locale text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            IF p_locale IS NULL OR p_locale !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$' THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.site_locale
                WHERE site_id=p_site_id AND tag=p_locale AND enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_effective_route(p_page_id uuid)
        RETURNS text LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE
            current_page record; current_id uuid := p_page_id;
            segments text[] := ARRAY[]::text[]; route text := '';
            depth integer := 0; index integer; default_locale text;
            page_locale text; segment text;
        BEGIN
            SELECT p.* INTO current_page FROM content.page p
            WHERE p.id = p_page_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            page_locale := current_page.locale;
            SELECT s.default_locale INTO default_locale
            FROM control.site s WHERE s.id = current_page.site_id;
            IF default_locale IS NULL THEN
                RAISE EXCEPTION 'PAGE_SITE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.site_locale
                WHERE site_id=current_page.site_id AND tag=current_page.locale AND enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            LOOP
                depth := depth + 1;
                IF depth > 64 THEN
                    RAISE EXCEPTION 'PAGE_HIERARCHY_CYCLE' USING ERRCODE='P0003';
                END IF;
                segment := coalesce(nullif(current_page.route_template,''), current_page.slug);
                segments := array_append(segments, segment);
                EXIT WHEN current_page.parent_id IS NULL;
                SELECT p.* INTO current_page
                FROM content.page p
                WHERE p.id = current_page.parent_id
                  AND p.site_id = current_page.site_id
                  AND p.deleted_at IS NULL;
                IF NOT FOUND OR current_page.locale IS DISTINCT FROM page_locale THEN
                    RAISE EXCEPTION 'PAGE_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
                IF current_page.route_template = '{slug}' THEN
                    RAISE EXCEPTION 'PAGE_DYNAMIC_PARENT' USING ERRCODE='P0003';
                END IF;
            END LOOP;
            IF page_locale IS DISTINCT FROM default_locale THEN
                route := '/' || page_locale;
            END IF;
            FOR index IN REVERSE array_length(segments, 1)..1 LOOP
                IF index = array_length(segments, 1)
                   AND segments[index] = 'home' THEN
                    CONTINUE;
                END IF;
                route := route || '/' || segments[index];
            END LOOP;
            IF route = '' THEN RETURN '/'; END IF;
            RETURN route;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_route_conflict(
            p_page_id uuid, p_candidate text
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE existing record; candidate_dynamic boolean;
            existing_dynamic boolean; candidate_prefix text; existing_prefix text;
            remainder text;
        BEGIN
            candidate_dynamic := right(p_candidate, 6) = '{slug}';
            candidate_prefix := CASE WHEN candidate_dynamic
                THEN left(p_candidate, length(p_candidate)-6) END;
            FOR existing IN
                SELECT p.id, content.slaif_agent_page_effective_route(p.id) AS route
                FROM content.page p
                WHERE p.site_id = (SELECT site_id FROM content.page WHERE id=p_page_id)
                  AND p.locale = (SELECT locale FROM content.page WHERE id=p_page_id)
                  AND p.deleted_at IS NULL
                  AND p.id <> p_page_id
            LOOP
                IF existing.route = p_candidate THEN RETURN true; END IF;
                existing_dynamic := right(existing.route, 6) = '{slug}';
                existing_prefix := CASE WHEN existing_dynamic
                    THEN left(existing.route, length(existing.route)-6) END;
                IF candidate_dynamic AND NOT existing_dynamic THEN
                    remainder := substr(existing.route, length(candidate_prefix)+1);
                    IF left(existing.route, length(candidate_prefix)) = candidate_prefix
                       AND remainder <> '' AND position('/' in remainder) = 0
                    THEN RETURN true; END IF;
                ELSIF existing_dynamic AND NOT candidate_dynamic THEN
                    remainder := substr(p_candidate, length(existing_prefix)+1);
                    IF left(p_candidate, length(existing_prefix)) = existing_prefix
                       AND remainder <> '' AND position('/' in remainder) = 0
                    THEN RETURN true; END IF;
                END IF;
            END LOOP;
            RETURN false;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_validate(
            p_site_id uuid, p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE
            current_page record; parent_page record; constraints record;
            cursor_id uuid; root_id uuid; visited uuid[] := ARRAY[]::uuid[];
            depth integer := 0; route text; first_segment text;
        BEGIN
            SELECT p.* INTO current_page FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF current_page.slug !~ '^[a-z0-9][a-z0-9._~-]{0,62}$'
               OR (current_page.route_template IS NOT NULL
                   AND current_page.route_template <> '{slug}')
            THEN
                RAISE EXCEPTION 'PAGE_ROUTE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=current_page.locale AND l.enabled
            ) THEN
                RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003';
            END IF;
            IF current_page.route_template = '{slug}' AND EXISTS (
                SELECT 1 FROM content.page child
                WHERE child.site_id=p_site_id AND child.parent_id=p_page_id
                  AND child.deleted_at IS NULL
            ) THEN
                RAISE EXCEPTION 'PAGE_DYNAMIC_PARENT' USING ERRCODE='P0003';
            END IF;

            cursor_id := p_page_id;
            LOOP
                IF cursor_id = ANY(visited) THEN
                    RAISE EXCEPTION 'PAGE_HIERARCHY_CYCLE' USING ERRCODE='P0003';
                END IF;
                visited := array_append(visited, cursor_id);
                depth := depth + 1;
                IF depth > 64 THEN
                    RAISE EXCEPTION 'PAGE_DEPTH_EXCEEDED' USING ERRCODE='P0003';
                END IF;
                SELECT p.* INTO parent_page FROM content.page p
                WHERE p.id=cursor_id AND p.site_id=p_site_id
                  AND p.deleted_at IS NULL;
                IF NOT FOUND OR parent_page.locale IS DISTINCT FROM current_page.locale THEN
                    RAISE EXCEPTION 'PAGE_PARENT_INVALID' USING ERRCODE='P0003';
                END IF;
                IF parent_page.route_template = '{slug}' AND parent_page.id <> p_page_id THEN
                    RAISE EXCEPTION 'PAGE_DYNAMIC_PARENT' USING ERRCODE='P0003';
                END IF;
                IF parent_page.parent_id IS NULL THEN
                    root_id := parent_page.id;
                    EXIT;
                END IF;
                cursor_id := parent_page.parent_id;
            END LOOP;

            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_locales) > 0
               AND NOT current_page.locale = ANY(constraints.allowed_locales) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007';
            END IF;
            IF cardinality(constraints.allowed_page_root_ids) > 0
               AND NOT root_id = ANY(constraints.allowed_page_root_ids) THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_PAGE_ROOT_DENIED' USING ERRCODE='P0007';
            END IF;
            IF constraints.max_page_depth IS NOT NULL AND depth > constraints.max_page_depth THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_PAGE_DEPTH_LIMIT' USING ERRCODE='P0007';
            END IF;
            route := content.slaif_agent_page_effective_route(p_page_id);
            IF constraints.route_prefix IS NOT NULL AND constraints.route_prefix <> '/'
               AND route <> constraints.route_prefix
               AND left(route, length(constraints.route_prefix)+1)
                   <> constraints.route_prefix || '/' THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_ROUTE_PREFIX_DENIED' USING ERRCODE='P0007';
            END IF;
            first_segment := split_part(trim(both '/' from route), '/', 1);
            IF first_segment = current_page.locale AND current_page.locale <> (SELECT default_locale FROM control.site WHERE id=p_site_id) THEN
                first_segment := split_part(trim(both '/' from substr(route, length(current_page.locale)+2)), '/', 1);
            END IF;
            IF first_segment IN ('api','admin','agent','control','editor','health','internal','login','logout','mcp','media','preview','setup','_next','static') THEN
                RAISE EXCEPTION 'PAGE_ROUTE_RESERVED' USING ERRCODE='P0003';
            END IF;
            IF content.slaif_agent_page_route_conflict(p_page_id, route) THEN
                RAISE EXCEPTION 'PAGE_ROUTE_CONFLICT' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_validate_subtree(
            p_site_id uuid, p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE child record;
        BEGIN
            PERFORM content.slaif_agent_page_validate(p_site_id,p_page_id);
            FOR child IN
                WITH RECURSIVE descendants(id) AS (
                    SELECT p.id FROM content.page p
                    WHERE p.site_id=p_site_id AND p.parent_id=p_page_id
                      AND p.deleted_at IS NULL
                    UNION ALL
                    SELECT p.id FROM content.page p
                    JOIN descendants d ON d.id=p.parent_id
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                ) SELECT id FROM descendants
            LOOP
                PERFORM content.slaif_agent_page_validate(p_site_id,child.id);
            END LOOP;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_accessible(
            p_site_id uuid, p_page_id uuid
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE page_row record; ancestor record; constraints record;
            cursor_id uuid; root_id uuid; visited uuid[] := ARRAY[]::uuid[];
            depth integer := 0; route text;
        BEGIN
            SELECT p.* INTO page_row FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id
              AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RETURN false; END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.site_locale
                WHERE site_id=p_site_id AND tag=page_row.locale AND enabled
            ) THEN
                RETURN false;
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            IF cardinality(constraints.allowed_locales) > 0
               AND NOT page_row.locale = ANY(constraints.allowed_locales) THEN RETURN false; END IF;
            cursor_id := p_page_id;
            LOOP
                IF cursor_id = ANY(visited) OR depth >= 64 THEN RETURN false; END IF;
                visited := array_append(visited,cursor_id); depth := depth+1;
                SELECT p.* INTO ancestor FROM content.page p
                WHERE p.id=cursor_id AND p.site_id=p_site_id
                  AND p.deleted_at IS NULL;
                IF NOT FOUND OR ancestor.locale IS DISTINCT FROM page_row.locale THEN RETURN false; END IF;
                IF ancestor.route_template = '{slug}' AND ancestor.id <> p_page_id THEN RETURN false; END IF;
                IF ancestor.route_template = '{slug}' AND EXISTS (
                    SELECT 1 FROM content.page child
                    WHERE child.site_id=p_site_id AND child.parent_id=ancestor.id
                      AND child.deleted_at IS NULL
                ) THEN RETURN false; END IF;
                IF ancestor.parent_id IS NULL THEN root_id := ancestor.id; EXIT; END IF;
                cursor_id := ancestor.parent_id;
            END LOOP;
            IF cardinality(constraints.allowed_page_root_ids) > 0
               AND NOT root_id = ANY(constraints.allowed_page_root_ids) THEN RETURN false; END IF;
            IF constraints.max_page_depth IS NOT NULL AND depth > constraints.max_page_depth THEN RETURN false; END IF;
            route := content.slaif_agent_page_effective_route(p_page_id);
            IF constraints.route_prefix IS NOT NULL AND constraints.route_prefix <> '/'
               AND route <> constraints.route_prefix
               AND left(route,length(constraints.route_prefix)+1) <> constraints.route_prefix || '/' THEN RETURN false; END IF;
            RETURN true;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_create(
            p_site_id uuid, p_slug text, p_title text, p_status text,
            p_locale text, p_parent_id uuid, p_route_template text
        ) RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE page_id uuid; workspace_id uuid; capability_id uuid;
            constraints record; visible_count bigint;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'page:create');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text || chr(58) || p_site_id::text || chr(58) || 'page-structure',994));
            PERFORM content.slaif_agent_page_ensure_locale(p_site_id,p_locale);
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            SELECT count(*) INTO visible_count FROM content.page p
            WHERE p.site_id=p_site_id AND content.slaif_agent_page_accessible(p_site_id,p.id);
            IF constraints.max_visible_pages IS NOT NULL AND visible_count >= constraints.max_visible_pages THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_PAGE_COUNT_LIMIT' USING ERRCODE='P0007';
            END IF;
            IF p_parent_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.id=p_parent_id AND p.site_id=p_site_id AND p.locale=p_locale
                  AND p.deleted_at IS NULL
            ) THEN RAISE EXCEPTION 'PAGE_PARENT_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            page_id := gen_random_uuid();
            INSERT INTO content.page(id,site_id,slug,title,status,locale,parent_id,route_template)
            VALUES(page_id,p_site_id,p_slug,p_title,p_status,p_locale,p_parent_id,p_route_template);
            PERFORM content.slaif_agent_page_validate(p_site_id,page_id);
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=page_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_get(p_site_id uuid,p_page_id uuid)
        RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'page:read');
            IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id) THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_list(p_site_id uuid)
        RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; visible_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'page:read');
            SELECT * INTO STRICT constraints FROM control.slaif_agent_resource_constraints(p_site_id);
            SELECT count(*) INTO visible_count FROM content.page p
            WHERE p.site_id=p_site_id AND content.slaif_agent_page_accessible(p_site_id,p.id);
            IF constraints.max_visible_pages IS NOT NULL AND visible_count > constraints.max_visible_pages THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_PAGE_COUNT_LIMIT' USING ERRCODE='P0007';
            END IF;
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p
            WHERE p.site_id=p_site_id AND content.slaif_agent_page_accessible(p_site_id,p.id)
            ORDER BY content.slaif_agent_page_effective_route(p.id) COLLATE "C",p.id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_update(
            p_site_id uuid,p_page_id uuid,p_slug text,p_title text,p_status text,
            p_locale text,p_route_template text,p_route_template_set boolean,
            p_expected integer
        ) RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old_page record;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'page:write');
            IF p_slug IS NOT NULL OR p_locale IS NOT NULL OR p_route_template_set THEN
                PERFORM control.slaif_agent_require_capability(p_site_id,'route:write');
            END IF;
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text || chr(58) || p_site_id::text || chr(58) || 'page-structure',994));
            IF p_locale IS NOT NULL THEN
                PERFORM content.slaif_agent_page_ensure_locale(p_site_id,p_locale);
            END IF;
            IF p_expected IS NULL OR p_expected <= 0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            SELECT p.* INTO old_page FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old_page.row_version <> p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            PERFORM content.slaif_agent_page_ensure_locale(p_site_id,old_page.locale);
            IF p_slug IS NULL AND p_title IS NULL AND p_status IS NULL AND p_locale IS NULL AND NOT p_route_template_set THEN
                RAISE EXCEPTION 'PAGE_UPDATE_EMPTY' USING ERRCODE='P0003';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page p SET
                slug=coalesce(p_slug,p.slug), title=coalesce(p_title,p.title),
                status=coalesce(p_status,p.status), locale=coalesce(p_locale,p.locale),
                route_template=CASE WHEN p_route_template_set THEN p_route_template ELSE p.route_template END,
                row_version=p.row_version+1, updated_at=now()
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_page_validate_subtree(p_site_id,p_page_id);
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_move(
            p_site_id uuid,p_page_id uuid,p_parent_id uuid,p_expected integer
        ) RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old_page record;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'page:move');
            PERFORM control.slaif_agent_require_capability(p_site_id,'route:write');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text || chr(58) || p_site_id::text || chr(58) || 'page-structure',994));
            SELECT p.* INTO old_page FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF p_expected IS NULL OR p_expected <= 0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old_page.row_version <> p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_page_ensure_locale(p_site_id,old_page.locale);
            IF p_parent_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p WHERE p.id=p_parent_id AND p.site_id=p_site_id
                  AND p.locale=old_page.locale AND p.deleted_at IS NULL
            ) THEN RAISE EXCEPTION 'PAGE_PARENT_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_parent_id = p_page_id OR EXISTS (
                WITH RECURSIVE descendants(id) AS (
                    SELECT p.id FROM content.page p WHERE p.parent_id=p_page_id AND p.site_id=p_site_id
                      AND p.deleted_at IS NULL
                    UNION ALL SELECT p.id FROM content.page p JOIN descendants d ON d.id=p.parent_id
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                ) SELECT 1 FROM descendants WHERE descendants.id=p_parent_id
            ) THEN RAISE EXCEPTION 'PAGE_HIERARCHY_CYCLE' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page p SET parent_id=p_parent_id,row_version=p.row_version+1,updated_at=now()
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_page_validate_subtree(p_site_id,p_page_id);
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_delete(
            p_site_id uuid,p_page_id uuid,p_expected integer
        ) RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old_page record;
            constraints record; old_route text;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'page:delete');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text || chr(58) || p_site_id::text || chr(58) || 'page-structure',994));
            SELECT p.* INTO old_page FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF p_expected IS NULL OR p_expected <= 0 THEN RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003'; END IF;
            IF old_page.row_version <> p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_page_ensure_locale(p_site_id,old_page.locale);
            IF EXISTS (SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.parent_id=p_page_id)
               OR EXISTS (SELECT 1 FROM content.page_composition c WHERE c.site_id=p_site_id AND c.page_id=p_page_id)
               OR EXISTS (SELECT 1 FROM content.navigation_item n WHERE n.site_id=p_site_id AND n.page_id=p_page_id)
            THEN
                RAISE EXCEPTION 'PAGE_DEPENDENCIES' USING ERRCODE='P0003';
            END IF;
            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id);
            IF constraints.delete_enabled IS FALSE THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_DELETE_DISABLED' USING ERRCODE='P0003';
            END IF;
            old_route := content.slaif_agent_page_effective_route(p_page_id);
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page p SET deleted_at=now(), row_version=p.row_version+1,
                updated_at=now()
            WHERE p.id=p_page_id AND p.site_id=p_site_id
              AND p.row_version=p_expected AND p.deleted_at IS NULL;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,old_route,p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_page_restore(
            p_site_id uuid,p_page_id uuid,p_expected integer
        ) RETURNS TABLE("""
        + _AGENT_PAGE_RETURN
        + """)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; deleted record;
        BEGIN
            capability_id := control.slaif_agent_require_capability(p_site_id,'page:restore');
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM pg_advisory_xact_lock(hashtextextended(workspace_id::text || chr(58) || p_site_id::text || chr(58) || 'page-structure',994));
            SELECT p.* INTO deleted FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NOT NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'PAGE_NOT_DELETED' USING ERRCODE='P0003';
            END IF;
            PERFORM content.slaif_agent_page_ensure_locale(p_site_id,deleted.locale);
            IF deleted.row_version <> p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF deleted.parent_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.id=deleted.parent_id AND p.site_id=p_site_id AND p.locale=deleted.locale
                  AND p.deleted_at IS NULL
            ) THEN RAISE EXCEPTION 'PAGE_PARENT_INVALID' USING ERRCODE='P0003'; END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page p SET deleted_at=NULL,row_version=p.row_version+1,updated_at=now()
            WHERE p.id=p_page_id AND p.site_id=p_site_id
              AND p.deleted_at IS NOT NULL AND p.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_page_validate_subtree(p_site_id,p_page_id);
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.route_template,content.slaif_agent_page_effective_route(p.id),
                p.deleted_at,p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id;
        END;
        $fn$;
    """
    )


def upgrade() -> None:
    # Bootstrap disables content COW before invoking Alembic, so this changes
    # the canonical page table and the next reconcile recreates matching COW
    # change columns/triggers from the public foundation API.
    op.execute("ALTER TABLE content.page ADD COLUMN route_template text")
    op.execute("ALTER TABLE content.page ADD COLUMN deleted_at timestamptz")
    op.execute("ALTER TABLE content.page DROP CONSTRAINT uq_page_site_locale_slug")
    op.execute(
        "CREATE UNIQUE INDEX uq_page_site_locale_parent_slug_active "
        "ON content.page(site_id,locale,coalesce(parent_id,'00000000-0000-0000-0000-000000000000'::uuid),slug) "
        "WHERE deleted_at IS NULL"
    )
    op.execute(
        "ALTER TABLE content.page ADD CONSTRAINT page_route_template_bounded "
        "CHECK (route_template IS NULL OR route_template = '{slug}')"
    )

    # Adding a column makes the old SELECT * page functions invalid against
    # their ten-column return contracts. Keep the Editor/Control contract
    # stable with explicit projections while Agent receives route columns.
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
        CREATE OR REPLACE FUNCTION content.slaif_page_list(p_site_id uuid)
        RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $fn$
            SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.row_version,p.created_at,p.updated_at FROM content.page p
            WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM content.site_locale l
                  WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
              )
            ORDER BY p.slug COLLATE "C"
        $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_page_get(p_page_id uuid)
        RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $fn$
            SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.row_version,p.created_at,p.updated_at FROM content.page p
            WHERE p.id=p_page_id AND p.deleted_at IS NULL
              AND EXISTS (
                  SELECT 1 FROM content.site_locale l
                  WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
              )
        $fn$
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
        BEGIN
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
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql())
    op.execute(_idempotency_completion_sql())
    op.execute(
        "DROP FUNCTION content.slaif_agent_page_create(uuid,text,text,text,text,uuid)"
    )
    op.execute("DROP FUNCTION content.slaif_agent_page_list(uuid)")
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_agent_page_update(uuid,uuid,text,text,text,integer)"
    )
    op.execute("DROP FUNCTION control.slaif_agent_resource_constraints(uuid)")
    op.execute(_resource_constraint_sql())
    for statement in _split_sql_statements(_page_functions_sql()):
        op.execute(statement)

    # The old function's return contract is replaced by the route-aware input
    # and output. Keep every new function narrow and grant
    # only EXECUTE to the Agent runtime role.
    for function in (
        "content.slaif_agent_page_create(uuid,text,text,text,text,uuid,text)",
        "content.slaif_agent_page_get(uuid,uuid)",
        "content.slaif_agent_page_list(uuid)",
        "content.slaif_agent_page_update(uuid,uuid,text,text,text,text,text,boolean,integer)",
        "content.slaif_agent_page_move(uuid,uuid,uuid,integer)",
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
        "content.slaif_agent_page_restore(uuid,uuid,integer)",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")

    # Internal helpers are reachable only through the SECURITY DEFINER page
    # wrappers, never as an Agent runtime SQL surface.
    for function in (
        "content.slaif_agent_page_effective_route(uuid)",
        "content.slaif_agent_page_route_conflict(uuid,text)",
        "content.slaif_agent_page_validate(uuid,uuid)",
        "content.slaif_agent_page_validate_subtree(uuid,uuid)",
        "content.slaif_agent_page_accessible(uuid,uuid)",
        "control.slaif_agent_resource_constraints(uuid)",
    ):
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime"
        )


def downgrade() -> None:
    # Direct Alembic invocation must use the bootstrap's public COW disable
    # path. Detect a view generically without naming foundation base/change
    # relations, and fail before any function, data, or privilege mutation.
    op.execute(
        """
        DO $$
        DECLARE relation_kind "char";
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='page';
            IF relation_kind = 'v' THEN
                RAISE EXCEPTION '049_DOWNGRADE_REQUIRES_PUBLIC_COW_DISABLE'
                    USING ERRCODE='P0003',
                    HINT='Run the product bootstrap downgrade so agentcow.postgres.disable_cow_schema disables COW before Alembic.';
            END IF;
        END;
        $$
        """
    )

    # 048 has no representation for route templates, product tombstones, or
    # the PAGE_* semantic audit actions. Refuse before any teardown so a
    # data-bearing downgrade is atomic and never discards review history.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM content.page
                WHERE route_template IS NOT NULL OR deleted_at IS NOT NULL
            ) OR EXISTS (
                SELECT 1 FROM audit.agent_mutation
                WHERE action LIKE 'PAGE_%'
            ) THEN
                RAISE EXCEPTION '049_DOWNGRADE_PAGE_DATA_PRESENT'
                    USING ERRCODE='P0003';
            END IF;
        END;
        $$
        """
    )

    for function in (
        "content.slaif_agent_page_restore(uuid,uuid,integer)",
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
        "content.slaif_agent_page_move(uuid,uuid,uuid,integer)",
        "content.slaif_agent_page_update(uuid,uuid,text,text,text,text,text,boolean,integer)",
        "content.slaif_agent_page_list(uuid)",
        "content.slaif_agent_page_get(uuid,uuid)",
        "content.slaif_agent_page_create(uuid,text,text,text,text,uuid,text)",
        "content.slaif_agent_page_accessible(uuid,uuid)",
        "content.slaif_agent_page_validate_subtree(uuid,uuid)",
        "content.slaif_agent_page_validate(uuid,uuid)",
        "content.slaif_agent_page_route_conflict(uuid,text)",
        "content.slaif_agent_page_effective_route(uuid)",
        "content.slaif_agent_page_ensure_locale(uuid,text)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS control.slaif_agent_resource_constraints(uuid)")
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_resource_constraints(p_site_id uuid)
        RETURNS TABLE(allowed_type_ids uuid[],allowed_type_keys text[],max_content_types integer,max_fields_per_type integer,delete_enabled boolean,max_deletes integer)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; result jsonb;
        BEGIN
            workspace_id := NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            SELECT w.resource_constraints INTO result FROM control.workspace w
            WHERE w.id=workspace_id AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP;
            IF result IS NULL OR jsonb_typeof(result)<>'object' THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            allowed_type_ids := ARRAY(SELECT value::uuid FROM jsonb_array_elements_text(coalesce(result->'allowed_type_ids','[]'::jsonb)) value);
            allowed_type_keys := ARRAY(SELECT value FROM jsonb_array_elements_text(coalesce(result->'allowed_type_keys','[]'::jsonb)) value);
            max_content_types := CASE WHEN result ? 'max_content_types' THEN (result->>'max_content_types')::integer END;
            max_fields_per_type := CASE WHEN result ? 'max_fields_per_type' THEN (result->>'max_fields_per_type')::integer END;
            delete_enabled := CASE WHEN result ? 'delete_enabled' THEN (result->>'delete_enabled')::boolean END;
            max_deletes := CASE WHEN result ? 'max_deletes' THEN (result->>'max_deletes')::integer END;
            RETURN NEXT;
        END; $fn$
        """
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(
        """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
        )
        """
    )
    op.execute(
        "ALTER TABLE content.page DROP CONSTRAINT IF EXISTS page_route_template_bounded"
    )
    op.execute("DROP INDEX IF EXISTS content.uq_page_site_locale_parent_slug_active")
    op.execute("ALTER TABLE content.page DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE content.page DROP COLUMN IF EXISTS route_template")
    op.execute(
        "ALTER TABLE content.page ADD CONSTRAINT uq_page_site_locale_slug "
        "UNIQUE (site_id, locale, slug)"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_create(
            p_site_id uuid,p_slug text,p_title text,p_status text,p_locale text,p_parent_id uuid
        ) RETURNS TABLE(id uuid,site_id uuid,slug text,title text,status text,locale text,parent_id uuid,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT * FROM content.slaif_agent_unchecked_page_create(p_site_id,p_slug,p_title,p_status,p_locale,p_parent_id);
        END; $fn$
        """
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_page_create(uuid,text,text,text,text,uuid) TO slaif_agent_runtime"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_list(p_site_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,slug text,title text,status text,locale text,parent_id uuid,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT p.* FROM content.page p WHERE p.site_id=p_site_id ORDER BY p.slug COLLATE "C";
        END; $fn$
        """
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_page_list(uuid) TO slaif_agent_runtime"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_update(
            p_site_id uuid,p_page_id uuid,p_slug text,p_title text,p_status text,
            p_expected integer
        ) RETURNS TABLE(id uuid,site_id uuid,slug text,title text,status text,locale text,parent_id uuid,row_version integer,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            UPDATE content.page AS page SET
                slug=coalesce(p_slug,page.slug),title=coalesce(p_title,page.title),
                status=coalesce(p_status,page.status),row_version=page.row_version+1,
                updated_at=now()
            WHERE page.site_id=p_site_id AND page.id=p_page_id
              AND page.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            RETURN QUERY SELECT p.id,p.site_id,p.slug,p.title,p.status,p.locale,p.parent_id,
                p.row_version,p.created_at,p.updated_at
            FROM content.page p WHERE p.site_id=p_site_id AND p.id=p_page_id;
        END; $fn$
        """
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_page_update(uuid,uuid,text,text,text,integer) TO slaif_agent_runtime"
    )

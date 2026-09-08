# ruff: noqa: E501
"""Add capability-bound Agent redirect and route graph semantics."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "051_001"
down_revision: str | Sequence[str] | None = "050_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_REDIRECT_RETURN = """
    id uuid, site_id uuid, source_route text, target text, status_code integer,
    locale text, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""

_PAGE_RETURN = """
    id uuid, site_id uuid, slug text, title text, status text, locale text,
    parent_id uuid, route_template text, effective_route text,
    deleted_at timestamptz, row_version integer, created_at timestamptz,
    updated_at timestamptz
"""


def _semantic_constraint_sql() -> str:
    return """
        ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED','REDIRECT_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED','REDIRECT_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED','REDIRECT_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
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
                   OR (p_action='REDIRECT_CREATED' AND p_resource_type='redirect' AND p_http_method='POST' AND p_status_code=201 AND p_quota_kind='mutation')
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
                   OR (p_action='REDIRECT_UPDATED' AND p_resource_type='redirect' AND p_http_method='PATCH' AND p_status_code=200 AND p_quota_kind='mutation')
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
                   OR (p_action='REDIRECT_DELETED' AND p_resource_type='redirect' AND p_http_method='DELETE' AND p_status_code=200 AND p_quota_kind='delete')
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
    # Migration 050 owns the complete immutable resource-constraint parser.
    # Redirect code receives only the narrow projection it needs; it must not
    # parse a second copy of the resource JSON and drift from other callers.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_redirect_constraints(
            p_site_id uuid
        ) RETURNS TABLE(
            allowed_locales text[], route_prefix text,
            max_visible_redirects integer
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record;
        BEGIN
            SELECT c.* INTO STRICT constraints
            FROM control.slaif_agent_resource_constraints(p_site_id) AS c;
            allowed_locales:=constraints.allowed_locales;
            route_prefix:=constraints.route_prefix;
            max_visible_redirects:=constraints.max_visible_redirects;
            RETURN NEXT;
        END;
        $fn$
        """
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql())
    op.execute(_idempotency_completion_sql())
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_is_visible(
            p_site_id uuid, p_source text, p_locale text
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE constraints record;
        BEGIN
            SELECT * INTO STRICT constraints
            FROM control.slaif_agent_redirect_constraints(p_site_id);
            IF constraints.route_prefix IS NOT NULL
               AND constraints.route_prefix<>'/'
               AND p_source<>constraints.route_prefix
               AND left(p_source,length(constraints.route_prefix)+1)
                   <>constraints.route_prefix||'/' THEN RETURN false; END IF;
            IF p_locale IS NOT NULL AND cardinality(constraints.allowed_locales)>0
               AND NOT p_locale=ANY(constraints.allowed_locales) THEN RETURN false; END IF;
            RETURN true;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_source_conflict(
            p_site_id uuid, p_source text, p_locale text, p_redirect_id uuid
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE page_row record; page_route text; dynamic_prefix text;
        BEGIN
            FOR page_row IN
                SELECT p.id,p.locale,p.route_template
                FROM content.page p
                WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                  AND (p_locale IS NULL OR p.locale=p_locale)
            LOOP
                page_route:=content.slaif_agent_page_effective_route(page_row.id);
                IF page_row.route_template IS NULL AND page_route=p_source THEN
                    RETURN true;
                END IF;
                IF page_row.route_template='{slug}' AND page_route ~ '\\{slug\\}$' THEN
                    dynamic_prefix:=left(page_route,length(page_route)-6);
                    IF left(p_source,length(dynamic_prefix))=dynamic_prefix
                       AND length(substr(p_source,length(dynamic_prefix)+1))>0
                       AND position('/' in substr(p_source,length(dynamic_prefix)+1))=0
                    THEN RETURN true; END IF;
                END IF;
            END LOOP;
            RETURN false;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_static_target_exists(
            p_site_id uuid, p_target text, p_locale text, p_agent boolean
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE default_locale text;
        BEGIN
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.enabled AND l.is_default;
            IF p_agent THEN
                RETURN EXISTS (
                    SELECT 1 FROM content.page p
                    WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                      AND p.route_template IS NULL
                      AND p.locale=coalesce(p_locale,default_locale)
                      AND content.slaif_agent_page_accessible(p_site_id,p.id)
                      AND content.slaif_agent_page_effective_route(p.id)=p_target
                );
            END IF;
            RETURN EXISTS (
                SELECT 1 FROM content.page p
                WHERE p.site_id=p_site_id AND p.deleted_at IS NULL
                  AND p.route_template IS NULL
                  AND p.locale=coalesce(p_locale,default_locale)
                  AND EXISTS (
                      SELECT 1 FROM content.site_locale l
                      WHERE l.site_id=p.site_id AND l.tag=p.locale AND l.enabled
                  )
                  AND content.slaif_agent_page_effective_route(p.id)=p_target
            );
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_validate_input(
            p_site_id uuid, p_source text, p_target text, p_status integer,
            p_locale text, p_agent boolean
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record;
        BEGIN
            IF p_source IS NULL OR octet_length(p_source)>512
               OR p_source<>'/'||ltrim(p_source,'/')
               OR p_source='/' OR p_source<>lower(p_source)
               OR p_source !~ '^/[a-z0-9][a-z0-9._~-]*(/[a-z0-9][a-z0-9._~-]*)*$'
               OR p_source ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
               OR p_source ~ '\\.(asp|aspx|bash|cgi|dll|exe|jsp|jspx|php|pl|sh)(/|$)'
            THEN RAISE EXCEPTION 'REDIRECT_SOURCE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_status NOT IN (301,302,303,307,308)
            THEN RAISE EXCEPTION 'REDIRECT_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_target IS NULL OR octet_length(p_target)>2048
               OR p_target ~ '[[:cntrl:] ]' THEN
                RAISE EXCEPTION 'REDIRECT_TARGET_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target LIKE '/%' THEN
                IF p_target<>'/' AND (
                    p_target<>lower(p_target)
                    OR p_target !~ '^/[a-z0-9][a-z0-9._~-]*(/[a-z0-9][a-z0-9._~-]*)*$'
                    OR p_target ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
                ) THEN RAISE EXCEPTION 'REDIRECT_TARGET_INVALID' USING ERRCODE='P0003'; END IF;
            ELSIF p_target !~ '^https://[^/@?#]+([/?#].*)?$' THEN
                RAISE EXCEPTION 'REDIRECT_TARGET_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_target=p_source THEN
                RAISE EXCEPTION 'REDIRECT_CYCLE' USING ERRCODE='P0003';
            END IF;
            IF p_locale IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.site_locale l
                WHERE l.site_id=p_site_id AND l.tag=p_locale AND l.enabled
            ) THEN RAISE EXCEPTION 'REDIRECT_LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_agent THEN
                SELECT * INTO STRICT constraints
                FROM control.slaif_agent_redirect_constraints(p_site_id);
                IF p_locale IS NOT NULL AND cardinality(constraints.allowed_locales)>0
                   AND NOT p_locale=ANY(constraints.allowed_locales)
                THEN RAISE EXCEPTION 'AGENT_RESOURCE_LOCALE_DENIED' USING ERRCODE='P0007'; END IF;
                IF constraints.route_prefix IS NOT NULL AND constraints.route_prefix<>'/' AND (
                    (p_source<>constraints.route_prefix AND left(p_source,length(constraints.route_prefix)+1)<>constraints.route_prefix||'/')
                    OR (p_target LIKE '/%' AND p_target<>constraints.route_prefix AND left(p_target,length(constraints.route_prefix)+1)<>constraints.route_prefix||'/')
                ) THEN RAISE EXCEPTION 'REDIRECT_ROUTE_PREFIX_DENIED' USING ERRCODE='P0007'; END IF;
            END IF;
            IF content.slaif_redirect_source_conflict(p_site_id,p_source,p_locale,NULL) THEN
                RAISE EXCEPTION 'REDIRECT_SOURCE_CONFLICT' USING ERRCODE='P0003';
            END IF;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_validate_state(
            p_site_id uuid, p_agent boolean
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE redirect_row record; next_target text; cursor_route text;
            visited text[]; steps integer; constraints record;
        BEGIN
            IF p_agent THEN
                SELECT * INTO STRICT constraints
                FROM control.slaif_agent_redirect_constraints(p_site_id);
            END IF;
            FOR redirect_row IN
                SELECT r.* FROM content.redirect r WHERE r.site_id=p_site_id
            LOOP
                IF content.slaif_redirect_source_conflict(
                    p_site_id,redirect_row.source_route,redirect_row.locale,redirect_row.id
                ) THEN
                    RAISE EXCEPTION 'REDIRECT_SOURCE_CONFLICT' USING ERRCODE='P0003';
                END IF;
                IF redirect_row.target NOT LIKE '/%' THEN CONTINUE; END IF;
                cursor_route:=redirect_row.target; visited:=ARRAY[]::text[]; steps:=0;
                LOOP
                    IF cursor_route=ANY(visited) THEN
                        RAISE EXCEPTION 'REDIRECT_CYCLE' USING ERRCODE='P0003';
                    END IF;
                    visited:=array_append(visited,cursor_route); steps:=steps+1;
                    IF steps>16 THEN
                        RAISE EXCEPTION 'REDIRECT_CHAIN_LIMIT' USING ERRCODE='P0003';
                    END IF;
                    SELECT r.target INTO next_target
                    FROM content.redirect r
                    WHERE r.site_id=p_site_id AND r.source_route=cursor_route
                      AND (
                        (redirect_row.locale IS NOT NULL AND
                         (r.locale=redirect_row.locale OR r.locale IS NULL))
                        OR (redirect_row.locale IS NULL AND r.locale IS NULL)
                      )
                    ORDER BY CASE WHEN redirect_row.locale IS NOT NULL
                                      AND r.locale=redirect_row.locale THEN 0 ELSE 1 END,
                             r.id DESC LIMIT 1;
                    IF FOUND THEN
                        IF next_target NOT LIKE '/%' THEN
                            EXIT;
                        END IF;
                        cursor_route:=next_target; CONTINUE;
                    END IF;
                    IF content.slaif_redirect_static_target_exists(
                        p_site_id,cursor_route,redirect_row.locale,false
                    ) THEN EXIT; END IF;
                    RAISE EXCEPTION 'REDIRECT_TARGET_DANGLING' USING ERRCODE='P0003';
                END LOOP;
            END LOOP;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_page_guard(
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM content.slaif_redirect_validate_state(p_site_id,false);
        END; $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_page_target_dependency(
            p_site_id uuid, p_route text
        ) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT EXISTS (
                SELECT 1 FROM content.redirect r
                WHERE r.site_id=p_site_id AND r.target=p_route
            )
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_page_target_dependency(
            p_site_id uuid, p_route text, p_page_id uuid
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE incoming record; default_locale text;
        BEGIN
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.enabled AND l.is_default;
            FOR incoming IN
                SELECT r.* FROM content.redirect r
                WHERE r.site_id=p_site_id AND r.target=p_route
            LOOP
                IF EXISTS (
                    SELECT 1 FROM content.page p
                    WHERE p.site_id=p_site_id AND p.id<>p_page_id
                      AND p.deleted_at IS NULL AND p.route_template IS NULL
                      AND p.locale=coalesce(incoming.locale,default_locale)
                      AND content.slaif_agent_page_effective_route(p.id)=p_route
                ) THEN
                    CONTINUE;
                END IF;
                IF EXISTS (
                    SELECT 1 FROM content.redirect alternate
                    WHERE alternate.site_id=p_site_id
                      AND alternate.source_route=p_route
                      AND (
                        (incoming.locale IS NOT NULL AND
                         (alternate.locale=incoming.locale OR alternate.locale IS NULL))
                        OR (incoming.locale IS NULL AND alternate.locale IS NULL)
                      )
                ) THEN
                    CONTINUE;
                END IF;
                RETURN true;
            END LOOP;
            RETURN false;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_source_dependency(
            p_site_id uuid, p_source text, p_redirect_id uuid
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE incoming record;
        BEGIN
            FOR incoming IN
                SELECT r.* FROM content.redirect r
                WHERE r.site_id=p_site_id AND r.id<>p_redirect_id
                  AND r.target=p_source
            LOOP
                IF content.slaif_redirect_static_target_exists(
                    p_site_id,p_source,incoming.locale,false
                ) THEN
                    CONTINUE;
                END IF;
                IF EXISTS (
                    SELECT 1 FROM content.redirect alternate
                    WHERE alternate.site_id=p_site_id
                      AND alternate.id<>p_redirect_id
                      AND alternate.source_route=p_source
                      AND (
                        (incoming.locale IS NOT NULL AND
                         (alternate.locale=incoming.locale OR alternate.locale IS NULL))
                        OR (incoming.locale IS NULL AND alternate.locale IS NULL)
                      )
                ) THEN
                    CONTINUE;
                END IF;
                RETURN true;
            END LOOP;
            RETURN false;
        END; $fn$
        """
    )

    # Page validation is the common post-mutation hook for Agent create,
    # route-update, move, and restore. Rename the applied implementation to
    # a private base and retain its public identity as the guarded wrapper.
    op.execute(
        "ALTER FUNCTION content.slaif_agent_page_validate(uuid,uuid) "
        "RENAME TO slaif_agent_page_validate_base_051"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_validate(
            p_site_id uuid, p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM content.slaif_agent_page_validate_base_051(p_site_id,p_page_id);
            PERFORM content.slaif_redirect_page_guard(p_site_id);
        END; $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION content.slaif_agent_page_delete(uuid,uuid,integer) "
        "RENAME TO slaif_agent_page_delete_base_051"
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_page_delete(
            p_site_id uuid, p_page_id uuid, p_expected integer
        ) RETURNS TABLE("""
        + _PAGE_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE old_route text;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT content.slaif_agent_page_effective_route(p.id)
                INTO old_route
            FROM content.page p
            WHERE p.id=p_page_id AND p.site_id=p_site_id AND p.deleted_at IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF content.slaif_redirect_page_target_dependency(
                p_site_id,old_route,p_page_id
            ) THEN
                RAISE EXCEPTION 'REDIRECT_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
            RETURN QUERY SELECT * FROM content.slaif_agent_page_delete_base_051(
                p_site_id,p_page_id,p_expected
            );
            PERFORM content.slaif_redirect_page_guard(p_site_id);
        END; $fn$
        """
    )

    # Editor page functions also participate in the same site structural
    # lock (the 050 bodies retain that lock) and must not leave redirects
    # dangling or colliding with a page route.
    for function, base_name in (
        (
            "content.slaif_page_create(uuid,text,text,text,text)",
            "slaif_page_create_base_051",
        ),
        (
            "content.slaif_page_update(uuid,text,text,text,integer)",
            "slaif_page_update_base_051",
        ),
        ("content.slaif_page_delete(uuid)", "slaif_page_delete_base_051"),
    ):
        op.execute(f"ALTER FUNCTION {function} RENAME TO {base_name}")
    op.execute(
        """
        CREATE FUNCTION content.slaif_page_create(
            p_site_id uuid, p_slug text, p_title text, p_status text, p_locale text
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            RETURN QUERY SELECT * FROM content.slaif_page_create_base_051(
                p_site_id,p_slug,p_title,p_status,p_locale
            );
            PERFORM content.slaif_redirect_page_guard(p_site_id);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_page_update(
            p_page_id uuid, p_slug text, p_title text, p_status text,
            p_expected_row_version integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, slug text, title text, status text, locale text,
            parent_id uuid, row_version integer, created_at timestamptz,
            updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid;
        BEGIN
            SELECT p.site_id INTO target_site FROM content.page p
            WHERE p.id=p_page_id;
            RETURN QUERY SELECT * FROM content.slaif_page_update_base_051(
                p_page_id,p_slug,p_title,p_status,p_expected_row_version
            );
            IF target_site IS NOT NULL THEN
                PERFORM content.slaif_redirect_page_guard(target_site);
            END IF;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_page_delete(p_page_id uuid)
        RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE target_site uuid; old_route text;
        BEGIN
            SELECT p.site_id,content.slaif_agent_page_effective_route(p.id)
                INTO target_site,old_route
            FROM content.page p WHERE p.id=p_page_id;
            IF target_site IS NULL THEN RETURN; END IF;
            PERFORM control.slaif_agent_structural_lock(target_site);
            IF content.slaif_redirect_page_target_dependency(
                target_site,old_route,p_page_id
            ) THEN
                RAISE EXCEPTION 'REDIRECT_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
            PERFORM content.slaif_page_delete_base_051(p_page_id);
            PERFORM content.slaif_redirect_page_guard(target_site);
        END; $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_redirect_list(p_site_id uuid)
        RETURNS TABLE("""
        + _REDIRECT_RETURN
        + """) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE constraints record; visible_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'redirect:read');
            SELECT * INTO STRICT constraints FROM control.slaif_agent_redirect_constraints(p_site_id);
            SELECT count(*) INTO visible_count FROM content.redirect r
            WHERE r.site_id=p_site_id AND content.slaif_redirect_is_visible(p_site_id,r.source_route,r.locale);
            IF constraints.max_visible_redirects IS NOT NULL AND visible_count>constraints.max_visible_redirects THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_REDIRECT_LIMIT' USING ERRCODE='P0007';
            END IF;
            RETURN QUERY SELECT r.id,r.site_id,r.source_route,r.target,r.status_code,
                r.locale,r.row_version,r.created_at,r.updated_at
            FROM content.redirect r
            WHERE r.site_id=p_site_id AND content.slaif_redirect_is_visible(p_site_id,r.source_route,r.locale)
            ORDER BY r.source_route COLLATE "C",coalesce(r.locale,''),r.id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_redirect_get(p_site_id uuid,p_id uuid)
        RETURNS TABLE("""
        + _REDIRECT_RETURN
        + """) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE found_redirect content.redirect; constraints record; visible_count bigint;
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'redirect:read');
            SELECT r.* INTO found_redirect FROM content.redirect r
            WHERE r.site_id=p_site_id AND r.id=p_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REDIRECT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF NOT content.slaif_redirect_is_visible(
                p_site_id,found_redirect.source_route,found_redirect.locale
            ) THEN
                RAISE EXCEPTION 'REDIRECT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_redirect_constraints(p_site_id);
            SELECT count(*) INTO visible_count FROM content.redirect r
            WHERE r.site_id=p_site_id AND content.slaif_redirect_is_visible(p_site_id,r.source_route,r.locale);
            IF constraints.max_visible_redirects IS NOT NULL AND visible_count>constraints.max_visible_redirects THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_REDIRECT_LIMIT' USING ERRCODE='P0007';
            END IF;
            RETURN QUERY SELECT found_redirect.id,found_redirect.site_id,found_redirect.source_route,
                found_redirect.target,found_redirect.status_code,found_redirect.locale,
                found_redirect.row_version,found_redirect.created_at,found_redirect.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_redirect_create(
            p_site_id uuid,p_source text,p_target text,p_status integer,p_locale text
        ) RETURNS TABLE("""
        + _REDIRECT_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; constraints record;
            visible_count bigint; created content.redirect;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'redirect:create');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT * INTO STRICT constraints FROM control.slaif_agent_redirect_constraints(p_site_id);
            PERFORM content.slaif_redirect_validate_input(p_site_id,p_source,p_target,p_status,p_locale,true);
            SELECT count(*) INTO visible_count FROM content.redirect r
            WHERE r.site_id=p_site_id AND content.slaif_redirect_is_visible(p_site_id,r.source_route,r.locale);
            IF constraints.max_visible_redirects IS NOT NULL AND visible_count>=constraints.max_visible_redirects THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_REDIRECT_LIMIT' USING ERRCODE='P0007';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            INSERT INTO content.redirect(site_id,source_route,target,status_code,locale)
            VALUES(p_site_id,p_source,p_target,p_status,p_locale) RETURNING * INTO created;
            PERFORM content.slaif_redirect_validate_state(p_site_id,true);
            RETURN QUERY SELECT created.id,created.site_id,created.source_route,created.target,
                created.status_code,created.locale,created.row_version,created.created_at,created.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_redirect_update(
            p_site_id uuid,p_id uuid,p_source text,p_target text,p_status integer,
            p_locale text,p_expected integer
        ) RETURNS TABLE("""
        + _REDIRECT_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.redirect;
            constraints record; visible_count bigint; updated content.redirect;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'redirect:write');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT r.* INTO old FROM content.redirect r
            WHERE r.site_id=p_site_id AND r.id=p_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REDIRECT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF NOT content.slaif_redirect_is_visible(p_site_id,old.source_route,old.locale) THEN
                RAISE EXCEPTION 'REDIRECT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF old.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            SELECT * INTO STRICT constraints FROM control.slaif_agent_redirect_constraints(p_site_id);
            PERFORM content.slaif_redirect_validate_input(p_site_id,p_source,p_target,p_status,p_locale,true);
            SELECT count(*) INTO visible_count FROM content.redirect r
            WHERE r.site_id=p_site_id AND content.slaif_redirect_is_visible(p_site_id,r.source_route,r.locale);
            IF constraints.max_visible_redirects IS NOT NULL AND visible_count>constraints.max_visible_redirects THEN
                RAISE EXCEPTION 'AGENT_RESOURCE_REDIRECT_LIMIT' USING ERRCODE='P0007';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.redirect r SET source_route=p_source,target=p_target,status_code=p_status,
                locale=p_locale,row_version=r.row_version+1,updated_at=now()
            WHERE r.site_id=p_site_id AND r.id=p_id AND r.row_version=p_expected
            RETURNING * INTO updated;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_redirect_validate_state(p_site_id,true);
            RETURN QUERY SELECT updated.id,updated.site_id,updated.source_route,updated.target,
                updated.status_code,updated.locale,updated.row_version,updated.created_at,updated.updated_at;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_agent_redirect_delete(
            p_site_id uuid,p_id uuid,p_expected integer
        ) RETURNS TABLE("""
        + _REDIRECT_RETURN
        + """) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; old content.redirect;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'redirect:delete');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT r.* INTO old FROM content.redirect r
            WHERE r.site_id=p_site_id AND r.id=p_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REDIRECT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF NOT content.slaif_redirect_is_visible(p_site_id,old.source_route,old.locale) THEN
                RAISE EXCEPTION 'REDIRECT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF old.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF content.slaif_redirect_source_dependency(
                p_site_id,old.source_route,old.id
            ) THEN
                RAISE EXCEPTION 'REDIRECT_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            DELETE FROM content.redirect r WHERE r.site_id=p_site_id AND r.id=p_id
              AND r.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_redirect_validate_state(p_site_id,true);
            RETURN QUERY SELECT old.id,old.site_id,old.source_route,old.target,old.status_code,
                old.locale,old.row_version,old.created_at,old.updated_at;
        END; $fn$
        """
    )

    # The Editor keeps its human authorization/audit envelope, but its
    # redirect SQL shares the same structural lock and graph invariants.
    for function, base_name in (
        (
            "content.slaif_redirect_create(uuid,text,text,integer,text)",
            "slaif_redirect_create_base_051",
        ),
        (
            "content.slaif_redirect_update(uuid,uuid,text,text,integer,text,integer)",
            "slaif_redirect_update_base_051",
        ),
        (
            "content.slaif_redirect_delete(uuid,uuid,integer)",
            "slaif_redirect_delete_base_051",
        ),
    ):
        op.execute(f"ALTER FUNCTION {function} RENAME TO {base_name}")
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_create(
            p_site_id uuid,p_source text,p_target text,p_status integer,p_locale text
        ) RETURNS SETOF content.redirect LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE created content.redirect;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            PERFORM content.slaif_redirect_validate_input(p_site_id,p_source,p_target,p_status,p_locale,false);
            INSERT INTO content.redirect(site_id,source_route,target,status_code,locale)
            VALUES(p_site_id,p_source,p_target,p_status,p_locale) RETURNING * INTO created;
            PERFORM content.slaif_redirect_validate_state(p_site_id,false);
            RETURN NEXT created;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_update(
            p_site_id uuid,p_id uuid,p_source text,p_target text,p_status integer,
            p_locale text,p_expected integer
        ) RETURNS SETOF content.redirect LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE old content.redirect; updated content.redirect;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT r.* INTO old FROM content.redirect r
            WHERE r.site_id=p_site_id AND r.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_redirect_validate_input(p_site_id,p_source,p_target,p_status,p_locale,false);
            UPDATE content.redirect r SET source_route=p_source,target=p_target,status_code=p_status,
                locale=p_locale,row_version=r.row_version+1,updated_at=now()
            WHERE r.site_id=p_site_id AND r.id=p_id AND r.row_version=p_expected
            RETURNING * INTO updated;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_redirect_validate_state(p_site_id,false);
            RETURN NEXT updated;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_redirect_delete(
            p_site_id uuid,p_id uuid,p_expected integer
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old content.redirect;
        BEGIN
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT r.* INTO old FROM content.redirect r
            WHERE r.site_id=p_site_id AND r.id=p_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            IF content.slaif_redirect_source_dependency(
                p_site_id,old.source_route,old.id
            ) THEN
                RAISE EXCEPTION 'REDIRECT_DEPENDENCY' USING ERRCODE='P0003';
            END IF;
            DELETE FROM content.redirect r WHERE r.site_id=p_site_id AND r.id=p_id
              AND r.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_redirect_validate_state(p_site_id,false);
        END; $fn$
        """
    )

    for function in (
        "content.slaif_agent_redirect_list(uuid)",
        "content.slaif_agent_redirect_get(uuid,uuid)",
        "content.slaif_agent_redirect_create(uuid,text,text,integer,text)",
        "content.slaif_agent_redirect_update(uuid,uuid,text,text,integer,text,integer)",
        "content.slaif_agent_redirect_delete(uuid,uuid,integer)",
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")
    for function in (
        "content.slaif_agent_page_delete_base_051(uuid,uuid,integer)",
        "content.slaif_agent_page_validate_base_051(uuid,uuid)",
        "content.slaif_page_create_base_051(uuid,text,text,text,text)",
        "content.slaif_page_update_base_051(uuid,text,text,text,integer)",
        "content.slaif_page_delete_base_051(uuid)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime, "
            "slaif_editor_runtime, slaif_control"
        )
    for function in (
        "control.slaif_agent_redirect_constraints(uuid)",
        "content.slaif_redirect_is_visible(uuid,text,text)",
        "content.slaif_redirect_source_conflict(uuid,text,text,uuid)",
        "content.slaif_redirect_static_target_exists(uuid,text,text,boolean)",
        "content.slaif_redirect_validate_input(uuid,text,text,integer,text,boolean)",
        "content.slaif_redirect_validate_state(uuid,boolean)",
        "content.slaif_redirect_page_guard(uuid)",
        "content.slaif_redirect_page_target_dependency(uuid,text)",
        "content.slaif_redirect_page_target_dependency(uuid,text,uuid)",
        "content.slaif_redirect_source_dependency(uuid,text,uuid)",
        "content.slaif_agent_page_validate(uuid,uuid)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime, slaif_editor_runtime"
        )
    for function in (
        "content.slaif_redirect_create(uuid,text,text,integer,text)",
        "content.slaif_redirect_update(uuid,uuid,text,text,integer,text,integer)",
        "content.slaif_redirect_delete(uuid,uuid,integer)",
        "content.slaif_page_create(uuid,text,text,text,text)",
        "content.slaif_page_update(uuid,text,text,text,integer)",
        "content.slaif_page_delete(uuid)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        op.execute(
            f"GRANT EXECUTE ON FUNCTION {function} TO slaif_editor_runtime, slaif_control"
        )
    for function in (
        "content.slaif_redirect_create_base_051(uuid,text,text,integer,text)",
        "content.slaif_redirect_update_base_051(uuid,uuid,text,text,integer,text,integer)",
        "content.slaif_redirect_delete_base_051(uuid,uuid,integer)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(
            f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC, slaif_agent_runtime, "
            "slaif_editor_runtime, slaif_control"
        )


def downgrade() -> None:
    # No redirect bytes are discarded by this downgrade. Restore the function
    # identities that 050 supplied so a later 050->051 upgrade is repeatable.
    for function in (
        "content.slaif_agent_redirect_delete(uuid,uuid,integer)",
        "content.slaif_agent_redirect_update(uuid,uuid,text,text,integer,text,integer)",
        "content.slaif_agent_redirect_create(uuid,text,text,integer,text)",
        "content.slaif_agent_redirect_get(uuid,uuid)",
        "content.slaif_agent_redirect_list(uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function} CASCADE")

    for function in (
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
        "content.slaif_agent_page_validate(uuid,uuid)",
        "content.slaif_page_create(uuid,text,text,text,text)",
        "content.slaif_page_update(uuid,text,text,text,integer)",
        "content.slaif_page_delete(uuid)",
        "content.slaif_redirect_create(uuid,text,text,integer,text)",
        "content.slaif_redirect_update(uuid,uuid,text,text,integer,text,integer)",
        "content.slaif_redirect_delete(uuid,uuid,integer)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}")

    for base_name, function, signature in (
        (
            "content.slaif_agent_page_delete_base_051",
            "content.slaif_agent_page_delete",
            "uuid,uuid,integer",
        ),
        (
            "content.slaif_agent_page_validate_base_051",
            "content.slaif_agent_page_validate",
            "uuid,uuid",
        ),
        (
            "content.slaif_page_create_base_051",
            "content.slaif_page_create",
            "uuid,text,text,text,text",
        ),
        (
            "content.slaif_page_update_base_051",
            "content.slaif_page_update",
            "uuid,text,text,text,integer",
        ),
        ("content.slaif_page_delete_base_051", "content.slaif_page_delete", "uuid"),
        (
            "content.slaif_redirect_create_base_051",
            "content.slaif_redirect_create",
            "uuid,text,text,integer,text",
        ),
        (
            "content.slaif_redirect_update_base_051",
            "content.slaif_redirect_update",
            "uuid,uuid,text,text,integer,text,integer",
        ),
        (
            "content.slaif_redirect_delete_base_051",
            "content.slaif_redirect_delete",
            "uuid,uuid,integer",
        ),
    ):
        op.execute(
            f"ALTER FUNCTION {base_name}({signature}) "
            f"RENAME TO {function.rsplit('.', 1)[1]}"
        )

    for function in (
        "control.slaif_agent_redirect_constraints(uuid)",
        "content.slaif_redirect_is_visible(uuid,text,text)",
        "content.slaif_redirect_source_conflict(uuid,text,text,uuid)",
        "content.slaif_redirect_static_target_exists(uuid,text,text,boolean)",
        "content.slaif_redirect_validate_input(uuid,text,text,integer,text,boolean)",
        "content.slaif_redirect_validate_state(uuid,boolean)",
        "content.slaif_redirect_page_guard(uuid)",
        "content.slaif_redirect_page_target_dependency(uuid,text)",
        "content.slaif_redirect_page_target_dependency(uuid,text,uuid)",
        "content.slaif_redirect_source_dependency(uuid,text,uuid)",
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function} CASCADE")

    for function in (
        "content.slaif_agent_page_delete(uuid,uuid,integer)",
        "content.slaif_page_create(uuid,text,text,text,text)",
        "content.slaif_page_update(uuid,text,text,text,integer)",
        "content.slaif_page_delete(uuid)",
    ):
        op.execute(
            f"GRANT EXECUTE ON FUNCTION {function} TO slaif_editor_runtime, slaif_control"
            if function.startswith("content.slaif_page_")
            else f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime"
        )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_redirect_create(uuid,text,text,integer,text) "
        "TO slaif_editor_runtime, slaif_control"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_redirect_update(uuid,uuid,text,text,integer,text,integer) "
        "TO slaif_editor_runtime, slaif_control"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_redirect_delete(uuid,uuid,integer) "
        "TO slaif_editor_runtime, slaif_control"
    )

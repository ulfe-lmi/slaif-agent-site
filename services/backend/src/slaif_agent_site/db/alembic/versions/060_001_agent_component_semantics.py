# ruff: noqa: E501
"""Add the capability-bound Agent component data plane and catalog authority."""

from __future__ import annotations

import json
from collections.abc import Sequence

from alembic import op

revision: str = "060_001"
down_revision: str | Sequence[str] | None = "059_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Reviewed catalog-v1 snapshot. This migration deliberately does not import
# the mutable current runtime catalog, so clean installs remain deterministic.
CATALOG_V1_REVIEWED_SHA256 = (
    "8e95ba57bf1ef2a77df89189fa7da4231f1bcef34aff380de59a322bf5b8085a"
)
_CATALOG_V1_JSON = '{"components":[{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":32,"props":{"background":{"authority":"design","localized":false,"max_length":4096,"required":false,"type":"string"},"variant":{"authority":"design","enum_values":["default","full","narrow"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Section"},{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":16,"props":{"width":{"authority":"design","enum_values":["sm","md","lg","xl"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Container"},{"allowed_slots":["col-1","col-2","col-3","col-4"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":4,"props":{"count":{"authority":"design","localized":false,"maximum":4,"minimum":1,"required":true,"type":"number"},"gap":{"authority":"design","enum_values":["none","sm","md","lg"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Columns"},{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":24,"props":{"columns":{"authority":"design","localized":false,"maximum":12,"minimum":1,"required":false,"type":"number"},"gap":{"authority":"design","enum_values":["sm","md","lg"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Grid"},{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":16,"props":{"direction":{"authority":"design","enum_values":["vertical","horizontal"],"localized":false,"required":false,"type":"enum"},"gap":{"authority":"design","enum_values":["none","sm","md","lg"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Stack"},{"allowed_slots":[],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":0,"props":{"size":{"authority":"design","enum_values":["xs","sm","md","lg","xl"],"localized":false,"required":true,"type":"enum"}},"schema_version":"1","type":"Spacer"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"level":{"authority":"content","localized":false,"maximum":6,"minimum":1,"required":true,"type":"number"},"text":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"}},"schema_version":"1","type":"Heading"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"content":{"authority":"content","localized":true,"required":true,"schema":{"additional_properties":false,"properties":{"children":{"items":{"additional_properties":false,"properties":{"bold":{"required":false,"type":"boolean"},"italic":{"required":false,"type":"boolean"},"text":{"max_length":4096,"required":true,"type":"string"}},"required":["text"],"type":"object"},"max_items":64,"min_items":1,"required":true,"type":"array"},"type":{"enum_values":["paragraph","heading","quote"],"required":true,"type":"enum"}},"required":["type","children"],"type":"object"},"type":"object"}},"schema_version":"1","type":"RichText"},{"allowed_slots":[],"authority_class":"content","binding_kind":"media_asset","category":"basic","max_children":0,"props":{"alt":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"},"aspectRatio":{"authority":"content","enum_values":["auto","16:9","4:3","1:1"],"required":false,"type":"enum"},"mediaId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"Image"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"href":{"authority":"content","max_length":4096,"required":true,"type":"string"},"label":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"},"variant":{"authority":"content","enum_values":["primary","secondary","ghost"],"required":false,"type":"enum"}},"schema_version":"1","type":"Button"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"attribution":{"authority":"content","localized":true,"max_length":4096,"required":false,"type":"string"},"text":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"}},"schema_version":"1","type":"Quote"},{"allowed_slots":["item"],"authority_class":"content","binding_kind":"collection_view","category":"data","max_children":0,"props":{"limit":{"authority":"content","maximum":100,"minimum":1,"required":false,"type":"number"},"viewId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"CollectionList"},{"allowed_slots":["item"],"authority_class":"content","binding_kind":"collection_view","category":"data","max_children":0,"props":{"columns":{"authority":"content","maximum":6,"minimum":1,"required":false,"type":"number"},"viewId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"CollectionGrid"},{"allowed_slots":[],"authority_class":"content","binding_kind":"collection_view","category":"data","max_children":0,"props":{"viewId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"CollectionDetail"},{"allowed_slots":["content"],"authority_class":"content","binding_kind":"media_asset","category":"institutional","max_children":8,"props":{"heading":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"},"mediaId":{"authority":"content","format":"uuid","required":false,"type":"reference"},"subheading":{"authority":"content","localized":true,"max_length":4096,"required":false,"type":"string"}},"schema_version":"1","type":"Hero"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"institutional","max_children":0,"props":{"items":{"authority":"content","max_items":64,"min_items":1,"required":true,"schema":{"items":{"additional_properties":false,"properties":{"label":{"max_length":256,"required":true,"type":"string"},"value":{"max_length":256,"required":true,"type":"string"}},"required":["label","value"],"type":"object"},"max_items":64,"min_items":1,"type":"array"},"type":"array"}},"schema_version":"1","type":"Statistics"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"institutional","max_children":0,"props":{"items":{"authority":"content","max_items":64,"min_items":1,"required":true,"schema":{"items":{"additional_properties":false,"properties":{"description":{"max_length":4096,"required":true,"type":"string"},"title":{"max_length":256,"required":true,"type":"string"}},"required":["title","description"],"type":"object"},"max_items":64,"min_items":1,"type":"array"},"type":"array"}},"schema_version":"1","type":"Timeline"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"institutional","max_children":0,"props":{"items":{"authority":"content","max_items":64,"min_items":1,"required":true,"schema":{"items":{"additional_properties":false,"properties":{"answer":{"max_length":4096,"required":true,"type":"string"},"question":{"max_length":4096,"required":true,"type":"string"}},"required":["question","answer"],"type":"object"},"max_items":64,"min_items":1,"type":"array"},"type":"array"}},"schema_version":"1","type":"FAQ"},{"allowed_slots":["nav"],"authority_class":"global","binding_kind":"none","category":"global","max_children":12,"props":{},"schema_version":"1","type":"Header"},{"allowed_slots":["links"],"authority_class":"global","binding_kind":"none","category":"global","max_children":16,"props":{},"schema_version":"1","type":"Footer"},{"allowed_slots":[],"authority_class":"global","binding_kind":"none","category":"global","max_children":0,"props":{},"schema_version":"1","type":"Breadcrumbs"},{"allowed_slots":[],"authority_class":"global","binding_kind":"none","category":"global","max_children":0,"props":{},"schema_version":"1","type":"LanguageSwitcher"}],"composition_schema_version":"site-composition/v1","version":"catalog-v1"}'


_NEW_FUNCTIONS = (
    "control.slaif_component_catalog()",
    "content.slaif_component_reject_nested(jsonb)",
    "content.slaif_component_validate_schema(jsonb,jsonb)",
    "content.slaif_agent_component_validate(uuid,uuid,uuid,text,text,uuid,text,jsonb,boolean)",
    "content.slaif_agent_component_tree_validate(uuid,uuid)",
    "content.slaif_agent_component_reposition(uuid,uuid,uuid,uuid,text,integer)",
    "content.slaif_agent_component_resequence(uuid,uuid,uuid,text)",
    "content.slaif_agent_component_list(uuid,uuid)",
    "content.slaif_agent_component_get(uuid,uuid)",
    "content.slaif_agent_component_create(uuid,uuid,text,uuid,text,uuid,uuid,jsonb)",
    "content.slaif_agent_component_update(uuid,uuid,jsonb,integer)",
    "content.slaif_agent_component_move(uuid,uuid,uuid,text,uuid,uuid,integer)",
    "content.slaif_agent_component_delete(uuid,uuid,integer)",
)


def _execute_block(sql: str) -> None:
    """Execute one DDL statement at a time for asyncpg-backed Alembic."""

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
            max_navigation_depth integer, max_visible_redirects integer,
            allowed_component_types text[], max_components_per_page integer,
            max_component_depth integer, max_visible_components integer
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; result jsonb;
        BEGIN
            BEGIN
                workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF workspace_id IS NULL OR NULLIF(current_setting('app.operation_id',true),'') IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END IF;
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            SELECT w.resource_constraints INTO result
            FROM control.workspace w JOIN control.site s ON s.id=w.site_id
                JOIN control.user_account a ON a.id=coalesce(w.delegator_id,w.created_by)
            WHERE w.id=workspace_id AND w.site_id=p_site_id AND w.status='ACTIVE'
              AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE';
            IF result IS NULL OR jsonb_typeof(result)<>'object' THEN
                RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001';
            END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_object_keys(result) k
                WHERE k NOT IN (
                    'allowed_type_ids','allowed_type_keys','max_content_types',
                    'max_fields_per_type','delete_enabled','max_deletes','allowed_locales',
                    'route_prefix','allowed_page_root_ids','max_visible_pages','max_page_depth',
                    'allowed_navigation_keys','allowed_navigation_ids','max_visible_locales',
                    'max_visible_navigations','max_visible_navigation_items','max_navigation_depth',
                    'max_visible_redirects','allowed_component_types','max_components_per_page',
                    'max_component_depth','max_visible_components'
                )
            ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF (result ? 'allowed_type_ids' AND jsonb_typeof(result->'allowed_type_ids')<>'array')
               OR (result ? 'allowed_type_keys' AND jsonb_typeof(result->'allowed_type_keys')<>'array')
               OR (result ? 'allowed_locales' AND jsonb_typeof(result->'allowed_locales')<>'array')
               OR (result ? 'allowed_page_root_ids' AND jsonb_typeof(result->'allowed_page_root_ids')<>'array')
               OR (result ? 'allowed_navigation_keys' AND jsonb_typeof(result->'allowed_navigation_keys')<>'array')
               OR (result ? 'allowed_navigation_ids' AND jsonb_typeof(result->'allowed_navigation_ids')<>'array')
               OR (result ? 'allowed_component_types' AND jsonb_typeof(result->'allowed_component_types')<>'array')
               OR (result ? 'delete_enabled' AND jsonb_typeof(result->'delete_enabled')<>'boolean')
               OR (result ? 'route_prefix' AND (jsonb_typeof(result->'route_prefix')<>'string' OR result->>'route_prefix'=''))
               OR EXISTS (
                   SELECT 1 FROM (VALUES
                       ('max_content_types'),('max_fields_per_type'),('max_deletes'),
                       ('max_visible_pages'),('max_page_depth'),('max_visible_locales'),
                       ('max_visible_navigations'),('max_visible_navigation_items'),
                       ('max_navigation_depth'),('max_visible_redirects'),
                       ('max_components_per_page'),('max_component_depth'),('max_visible_components')
                   ) AS numeric_key(key)
                   WHERE result ? numeric_key.key AND jsonb_typeof(result->numeric_key.key)<>'number'
               ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_each_text(result) item
                WHERE item.key IN (
                    'max_content_types','max_fields_per_type','max_deletes','max_visible_pages',
                    'max_page_depth','max_visible_locales','max_visible_navigations',
                    'max_visible_navigation_items','max_navigation_depth','max_visible_redirects',
                    'max_components_per_page','max_component_depth','max_visible_components'
                ) AND (item.value !~ '^[0-9]+$' OR item.value::numeric>2147483647)
            ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF jsonb_array_length(coalesce(result->'allowed_type_ids','[]'::jsonb))>256
               OR jsonb_array_length(coalesce(result->'allowed_type_keys','[]'::jsonb))>256
               OR jsonb_array_length(coalesce(result->'allowed_locales','[]'::jsonb))>64
               OR jsonb_array_length(coalesce(result->'allowed_page_root_ids','[]'::jsonb))>256
               OR jsonb_array_length(coalesce(result->'allowed_navigation_keys','[]'::jsonb))>256
               OR jsonb_array_length(coalesce(result->'allowed_navigation_ids','[]'::jsonb))>256
               OR jsonb_array_length(coalesce(result->'allowed_component_types','[]'::jsonb))>256
               OR EXISTS (
                   SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_component_types','[]'::jsonb)) v
                   WHERE v !~ '^[A-Za-z][A-Za-z0-9]{0,62}$'
               ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_array_elements(coalesce(result->'allowed_type_ids','[]'::jsonb)) item
                WHERE jsonb_typeof(item.value)<>'string'
                   OR item.value #>> '{}' !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements(coalesce(result->'allowed_type_keys','[]'::jsonb)) item
                WHERE jsonb_typeof(item.value)<>'string'
                   OR item.value #>> '{}' !~ '^[A-Za-z0-9._~-]{1,63}$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements(coalesce(result->'allowed_locales','[]'::jsonb)) item
                WHERE jsonb_typeof(item.value)<>'string'
                   OR item.value #>> '{}' !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements(coalesce(result->'allowed_page_root_ids','[]'::jsonb)) item
                WHERE jsonb_typeof(item.value)<>'string'
                   OR item.value #>> '{}' !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) item
                WHERE jsonb_typeof(item.value)<>'string'
                   OR item.value #>> '{}' !~ '^[A-Za-z0-9._~-]{1,63}$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements(coalesce(result->'allowed_navigation_ids','[]'::jsonb)) item
                WHERE jsonb_typeof(item.value)<>'string'
                   OR item.value #>> '{}' !~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
            ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_locales','[]'::jsonb)) value
                WHERE value !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'
            ) OR EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(coalesce(result->'allowed_navigation_keys','[]'::jsonb)) value
                WHERE value !~ '^[A-Za-z0-9._~-]{1,63}$'
            ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
            IF result ? 'route_prefix' AND (
                (result->>'route_prefix' !~ '^/[a-z0-9][a-z0-9._~-]*(/[a-z0-9][a-z0-9._~-]*)*$' AND result->>'route_prefix'<>'/')
                OR result->>'route_prefix' ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)'
            ) THEN RAISE EXCEPTION 'INVALID_RESOURCE_CONSTRAINTS' USING ERRCODE='P0001'; END IF;
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
            RETURN NEXT;
        END;
        $fn$;
        ALTER FUNCTION control.slaif_agent_resource_constraints(uuid) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION control.slaif_agent_resource_constraints(uuid) FROM PUBLIC;
    """


def _catalog_sql() -> str:
    definitions = json.dumps(json.loads(_CATALOG_V1_JSON)["components"], sort_keys=True)
    escaped = definitions.replace("'", "''")
    return f"""
        CREATE TABLE control.component_catalog (
            version text PRIMARY KEY,
            composition_schema_version text NOT NULL,
            definitions jsonb NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT component_catalog_version_shape CHECK (version='catalog-v1'),
            CONSTRAINT component_catalog_schema_shape CHECK (
                composition_schema_version='site-composition/v1'
            )
        );
        ALTER TABLE control.component_catalog OWNER TO slaif_owner;
        REVOKE ALL ON TABLE control.component_catalog FROM PUBLIC;
        INSERT INTO control.component_catalog(
            version,composition_schema_version,definitions
        ) VALUES (
            'catalog-v1','site-composition/v1','{escaped}'::jsonb
        );
        CREATE FUNCTION control.slaif_component_catalog()
        RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT jsonb_build_object(
                'version',version,
                'composition_schema_version',composition_schema_version,
                'components',definitions
            )
            FROM control.component_catalog
            WHERE version='catalog-v1'
        $fn$;
        ALTER FUNCTION control.slaif_component_catalog() OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION control.slaif_component_catalog() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION control.slaif_component_catalog()
            TO slaif_agent_runtime;
    """


def _nested_validator_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_component_reject_nested(p_value jsonb)
        RETURNS boolean LANGUAGE plpgsql IMMUTABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE key text; child jsonb; lowered text;
        BEGIN
            IF p_value IS NULL THEN RETURN true; END IF;
            IF jsonb_typeof(p_value)='object' THEN
                FOR key,child IN SELECT e.key,e.value FROM jsonb_each(p_value) e LOOP
                    lowered:=lower(key);
                    IF lowered IN (
                        '__proto__','constructor','prototype','innerhtml',
                        'dangerouslysetinnerhtml','style','class','classname',
                        'onclick','onload','handler','script','eval','html',
                        'template','query','code','package','callback'
                    ) THEN RETURN true; END IF;
                    IF content.slaif_component_reject_nested(child) THEN RETURN true; END IF;
                END LOOP;
            ELSIF jsonb_typeof(p_value)='array' THEN
                FOR child IN SELECT value FROM jsonb_array_elements(p_value) LOOP
                    IF content.slaif_component_reject_nested(child) THEN RETURN true; END IF;
                END LOOP;
            ELSIF jsonb_typeof(p_value)='string' THEN
                lowered:=lower(p_value #>> '{}');
                IF lowered LIKE 'javascript:%' OR lowered LIKE 'data:%'
                   OR lowered LIKE 'file:%' OR lowered LIKE 'vbscript:%'
                   OR lowered LIKE '%<script%'
                   OR lowered LIKE '%onerror=%' OR lowered LIKE '%onload=%'
                THEN RETURN true; END IF;
            END IF;
            RETURN false;
        END;
        $fn$;
        ALTER FUNCTION content.slaif_component_reject_nested(jsonb) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION content.slaif_component_reject_nested(jsonb) FROM PUBLIC;
    """


def _schema_validator_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_component_validate_schema(
            p_value jsonb,p_schema jsonb
        ) RETURNS void LANGUAGE plpgsql IMMUTABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE kind text; key text; child jsonb; rule jsonb;
            required_value jsonb; minimum numeric; maximum numeric;
        BEGIN
            IF p_schema IS NULL THEN RETURN; END IF;
            kind:=p_schema->>'type';
            IF kind='string' THEN
                IF jsonb_typeof(p_value)<>'string' THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                END IF;
                IF p_schema ? 'max_length' AND length(p_value #>> '{}')>(p_schema->>'max_length')::integer THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003';
                END IF;
            ELSIF kind='number' THEN
                IF jsonb_typeof(p_value)<>'number' THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                END IF;
                minimum:=NULLIF(p_schema->>'minimum','')::numeric;
                maximum:=NULLIF(p_schema->>'maximum','')::numeric;
                IF minimum IS NOT NULL AND (p_value #>> '{}')::numeric<minimum THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003';
                END IF;
                IF maximum IS NOT NULL AND (p_value #>> '{}')::numeric>maximum THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003';
                END IF;
            ELSIF kind='boolean' THEN
                IF jsonb_typeof(p_value)<>'boolean' THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                END IF;
            ELSIF kind='enum' THEN
                IF jsonb_typeof(p_value)<>'string' OR NOT (p_schema->'enum_values' ? (p_value #>> '{}')) THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_ENUM' USING ERRCODE='P0003';
                END IF;
            ELSIF kind='reference' THEN
                BEGIN PERFORM (p_value #>> '{}')::uuid;
                EXCEPTION WHEN invalid_text_representation THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_REFERENCE' USING ERRCODE='P0003';
                END;
            ELSIF kind='object' THEN
                IF jsonb_typeof(p_value)<>'object' THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                END IF;
                required_value:=p_schema->'required';
                IF jsonb_typeof(required_value)='array' AND EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(required_value) required_key
                    WHERE NOT (p_value ? required_key)
                ) THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_REQUIRED' USING ERRCODE='P0003';
                END IF;
                IF p_schema->>'additional_properties'='false' AND EXISTS (
                    SELECT 1 FROM jsonb_object_keys(p_value) object_key
                    WHERE NOT (p_schema->'properties' ? object_key)
                ) THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_UNKNOWN' USING ERRCODE='P0003';
                END IF;
                FOR key,child IN SELECT entry.key,entry.value FROM jsonb_each(p_value) entry LOOP
                    rule:=p_schema->'properties'->key;
                    IF rule IS NOT NULL THEN
                        PERFORM content.slaif_component_validate_schema(child,rule);
                    END IF;
                END LOOP;
            ELSIF kind='array' THEN
                IF jsonb_typeof(p_value)<>'array' THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                END IF;
                IF p_schema ? 'min_items' AND jsonb_array_length(p_value)<(p_schema->>'min_items')::integer THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003';
                END IF;
                IF p_schema ? 'max_items' AND jsonb_array_length(p_value)>(p_schema->>'max_items')::integer THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003';
                END IF;
                IF p_schema->'items' IS NOT NULL THEN
                    FOR child IN SELECT value FROM jsonb_array_elements(p_value) LOOP
                        PERFORM content.slaif_component_validate_schema(child,p_schema->'items');
                    END LOOP;
                END IF;
            ELSE
                RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
            END IF;
        END;
        $fn$;
        ALTER FUNCTION content.slaif_component_validate_schema(jsonb,jsonb) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION content.slaif_component_validate_schema(jsonb,jsonb) FROM PUBLIC;
    """


def _component_validator_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_agent_component_validate(
            p_site_id uuid,p_page_id uuid,p_node_id uuid,p_component_type text,
            p_schema_version text,p_parent_id uuid,p_slot_key text,p_props jsonb,
            p_allow_design boolean
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE definition jsonb; prop_rule jsonb; value jsonb; key text;
            parent_type text; parent_definition jsonb; expected_type text;
            child_count integer; total_count integer; depth integer:=0;
            cursor_id uuid; parent_cursor uuid; max_value numeric;
            binding_id uuid; href text;
        BEGIN
            IF p_site_id IS NULL OR p_page_id IS NULL OR p_component_type IS NULL
               OR p_schema_version IS NULL OR p_slot_key IS NULL
               OR p_props IS NULL OR jsonb_typeof(p_props)<>'object'
               OR octet_length(p_props::text)>16384
            THEN RAISE EXCEPTION 'COMPONENT_INVALID' USING ERRCODE='P0003'; END IF;
            SELECT entry INTO definition
            FROM control.component_catalog c,
                 jsonb_array_elements(c.definitions) entry
            WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
            IF definition IS NULL OR definition->>'schema_version'<>p_schema_version
            THEN RAISE EXCEPTION 'COMPONENT_TYPE_INVALID' USING ERRCODE='P0003'; END IF;
            IF p_parent_id IS NULL THEN
                IF p_slot_key<>'default' THEN
                    RAISE EXCEPTION 'COMPONENT_SLOT_INVALID' USING ERRCODE='P0003';
                END IF;
            ELSE
                SELECT c.component_type INTO parent_type
                FROM content.page_composition c
                WHERE c.id=p_parent_id AND c.site_id=p_site_id
                  AND c.page_id=p_page_id;
                IF parent_type IS NULL THEN
                    RAISE EXCEPTION 'COMPONENT_PARENT_INVALID' USING ERRCODE='P0002';
                END IF;
                SELECT entry INTO parent_definition
                FROM control.component_catalog c,
                     jsonb_array_elements(c.definitions) entry
                WHERE c.version='catalog-v1' AND entry->>'type'=parent_type;
                IF NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(
                        coalesce(parent_definition->'allowed_slots','[]'::jsonb)
                    ) slot WHERE slot=p_slot_key
                ) THEN
                    RAISE EXCEPTION 'COMPONENT_SLOT_INVALID' USING ERRCODE='P0003';
                END IF;
                SELECT count(*) INTO child_count FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                  AND c.parent_id=p_parent_id;
                IF p_node_id IS NULL OR NOT EXISTS (
                    SELECT 1 FROM content.page_composition c
                    WHERE c.id=p_node_id AND c.parent_id=p_parent_id
                ) THEN child_count:=child_count+1; END IF;
                IF child_count > (parent_definition->>'max_children')::integer THEN
                    RAISE EXCEPTION 'COMPONENT_CHILD_LIMIT' USING ERRCODE='P0003';
                END IF;
            END IF;
            SELECT count(*) INTO total_count FROM content.page_composition c
            WHERE c.site_id=p_site_id AND c.page_id=p_page_id
              AND (p_node_id IS NULL OR c.id<>p_node_id);
            IF total_count+(CASE WHEN p_node_id IS NULL THEN 1 ELSE 0 END) > 128 THEN
                RAISE EXCEPTION 'COMPONENT_PAGE_LIMIT' USING ERRCODE='P0003';
            END IF;
            cursor_id:=p_parent_id;
            WHILE cursor_id IS NOT NULL LOOP
                depth:=depth+1;
                IF depth>16 OR cursor_id=p_node_id THEN
                    RAISE EXCEPTION 'COMPONENT_CYCLE' USING ERRCODE='P0003';
                END IF;
                SELECT c.parent_id INTO parent_cursor
                FROM content.page_composition c
                WHERE c.id=cursor_id AND c.site_id=p_site_id AND c.page_id=p_page_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'COMPONENT_PARENT_INVALID' USING ERRCODE='P0002';
                END IF;
                cursor_id:=parent_cursor;
            END LOOP;
            IF content.slaif_component_reject_nested(p_props) THEN
                RAISE EXCEPTION 'COMPONENT_PROPS_UNSAFE' USING ERRCODE='P0003';
            END IF;
            FOR key,value IN SELECT e.key,e.value FROM jsonb_each(p_props) e LOOP
                prop_rule:=definition->'props'->key;
                IF prop_rule IS NULL THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_UNKNOWN' USING ERRCODE='P0003';
                END IF;
                IF NOT p_allow_design AND prop_rule->>'authority'='design' THEN
                    RAISE EXCEPTION 'COMPONENT_DESIGN_PROP' USING ERRCODE='P0007';
                END IF;
                expected_type:=prop_rule->>'type';
                IF expected_type IN ('string','enum','reference')
                   AND jsonb_typeof(value)<>'string'
                THEN RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003'; END IF;
                IF expected_type='number' AND jsonb_typeof(value)<>'number'
                THEN RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003'; END IF;
                IF expected_type='boolean' AND jsonb_typeof(value)<>'boolean'
                THEN RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003'; END IF;
                IF expected_type='object' AND jsonb_typeof(value)<>'object'
                THEN RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003'; END IF;
                IF expected_type='array' AND jsonb_typeof(value)<>'array'
                THEN RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003'; END IF;
                IF expected_type='string' AND prop_rule ? 'max_length'
                   AND length(value #>> '{}')>(prop_rule->>'max_length')::integer
                THEN RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003'; END IF;
                IF expected_type='enum' AND NOT (prop_rule->'enum_values' ? (value #>> '{}'))
                THEN RAISE EXCEPTION 'COMPONENT_PROP_ENUM' USING ERRCODE='P0003'; END IF;
                IF prop_rule ? 'schema' THEN
                    PERFORM content.slaif_component_validate_schema(value,prop_rule->'schema');
                END IF;
                IF expected_type='reference' THEN
                    BEGIN binding_id:=(value #>> '{}')::uuid;
                    EXCEPTION WHEN invalid_text_representation THEN
                        RAISE EXCEPTION 'COMPONENT_PROP_REFERENCE' USING ERRCODE='P0003';
                    END;
                END IF;
                IF expected_type='number' THEN
                    max_value:=NULLIF(prop_rule->>'minimum','')::numeric;
                    IF max_value IS NOT NULL AND (value #>> '{}')::numeric<max_value
                    THEN RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003'; END IF;
                    max_value:=NULLIF(prop_rule->>'maximum','')::numeric;
                    IF max_value IS NOT NULL AND (value #>> '{}')::numeric>max_value
                    THEN RAISE EXCEPTION 'COMPONENT_PROP_BOUND' USING ERRCODE='P0003'; END IF;
                END IF;
            END LOOP;
            FOR key IN SELECT jsonb_object_keys(definition->'props') LOOP
                prop_rule:=definition->'props'->key;
                IF prop_rule->>'required'='true' AND NOT (p_props ? key) THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_REQUIRED' USING ERRCODE='P0003';
                END IF;
            END LOOP;
            IF p_component_type='Button' THEN
                href:=p_props->>'href';
                IF href IS NULL OR href LIKE '//%' OR href NOT LIKE '/%'
                   OR href ~* '^(javascript|data|file|vbscript):'
                THEN RAISE EXCEPTION 'COMPONENT_PROP_UNSAFE' USING ERRCODE='P0003'; END IF;
            END IF;
            IF definition->>'binding_kind'='collection_view' THEN
                BEGIN binding_id:=(p_props->>'viewId')::uuid;
                EXCEPTION WHEN invalid_text_representation THEN
                    RAISE EXCEPTION 'COMPONENT_BINDING_INVALID' USING ERRCODE='P0003';
                END;
                IF NOT EXISTS (
                    SELECT 1 FROM content.collection_view v
                    JOIN content.content_type t ON t.site_id=v.site_id AND t.id=v.type_id
                    WHERE v.id=binding_id AND v.site_id=p_site_id AND t.status='ACTIVE'
                      AND t.definition_version=v.definition_version
                ) THEN RAISE EXCEPTION 'COMPONENT_BINDING_INVALID' USING ERRCODE='P0003'; END IF;
            ELSIF definition->>'binding_kind'='media_asset' AND p_props ? 'mediaId' THEN
                BEGIN binding_id:=(p_props->>'mediaId')::uuid;
                EXCEPTION WHEN invalid_text_representation THEN
                    RAISE EXCEPTION 'COMPONENT_BINDING_INVALID' USING ERRCODE='P0003';
                END;
                IF NOT EXISTS (
                    SELECT 1 FROM content.media_asset m
                    WHERE m.id=binding_id AND m.site_id=p_site_id
                ) THEN RAISE EXCEPTION 'COMPONENT_BINDING_INVALID' USING ERRCODE='P0003'; END IF;
            END IF;
        END;
        $fn$;
        ALTER FUNCTION content.slaif_agent_component_validate(
            uuid,uuid,uuid,text,text,uuid,text,jsonb,boolean
        ) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION content.slaif_agent_component_validate(
            uuid,uuid,uuid,text,text,uuid,text,jsonb,boolean
        ) FROM PUBLIC;
    """


def _tree_validator_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_agent_component_tree_validate(
            p_site_id uuid,p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE node record; positions integer[]; expected integer[];
        BEGIN
            FOR node IN SELECT * FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
            LOOP
                PERFORM content.slaif_agent_component_validate(
                    p_site_id,p_page_id,node.id,node.component_type,node.schema_version,
                    node.parent_id,node.slot_key,node.props,true);
            END LOOP;
            FOR node IN
                SELECT c.parent_id,c.slot_key,count(*)::integer AS amount
                FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                GROUP BY c.parent_id,c.slot_key
            LOOP
                SELECT array_agg(c.order_key ORDER BY c.order_key,c.id)
                    INTO positions FROM content.page_composition c
                    WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                      AND c.parent_id IS NOT DISTINCT FROM node.parent_id
                      AND c.slot_key=node.slot_key;
                expected:=ARRAY(SELECT value FROM generate_series(0,node.amount-1) value);
                IF positions IS DISTINCT FROM expected THEN
                    RAISE EXCEPTION 'COMPONENT_ORDER_INVALID' USING ERRCODE='P0003';
                END IF;
            END LOOP;
        END;
        $fn$;
        ALTER FUNCTION content.slaif_agent_component_tree_validate(uuid,uuid) OWNER TO slaif_owner;
        REVOKE ALL ON FUNCTION content.slaif_agent_component_tree_validate(uuid,uuid) FROM PUBLIC;
    """


def _agent_component_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_agent_component_reposition(
            p_site_id uuid,p_page_id uuid,p_component_id uuid,p_parent_id uuid,
            p_slot_key text,p_position integer
        ) RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            WITH remaining AS (
                SELECT c.id,c.parent_id,c.slot_key,
                    (row_number() OVER (
                        PARTITION BY c.parent_id,c.slot_key
                        ORDER BY c.order_key,c.id
                    )-1)::integer AS remaining_order
                FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                  AND c.id<>p_component_id
            ), desired AS (
                SELECT id,parent_id,slot_key,
                    CASE WHEN parent_id IS NOT DISTINCT FROM p_parent_id
                              AND slot_key=p_slot_key
                         THEN remaining_order+
                              CASE WHEN remaining_order>=p_position THEN 1 ELSE 0 END
                         ELSE remaining_order END AS desired_order
                FROM remaining
                UNION ALL
                SELECT p_component_id,p_parent_id,p_slot_key,p_position
            )
            UPDATE content.page_composition c
            SET parent_id=d.parent_id,slot_key=d.slot_key,order_key=d.desired_order,
                row_version=c.row_version+1,updated_at=now()
            FROM desired d
            WHERE c.id=d.id AND c.site_id=p_site_id AND c.page_id=p_page_id
              AND (c.parent_id IS DISTINCT FROM d.parent_id
                   OR c.slot_key IS DISTINCT FROM d.slot_key
                   OR c.order_key IS DISTINCT FROM d.desired_order)
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_resequence(
            p_site_id uuid,p_page_id uuid,p_parent_id uuid,p_slot_key text
        ) RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            WITH ranked AS (
                SELECT c.id,
                    (row_number() OVER (ORDER BY c.order_key,c.id)-1)::integer
                        AS desired_order
                FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                  AND c.parent_id IS NOT DISTINCT FROM p_parent_id
                  AND c.slot_key=p_slot_key
            )
            UPDATE content.page_composition c
            SET order_key=r.desired_order,row_version=c.row_version+1,updated_at=now()
            FROM ranked r
            WHERE c.id=r.id AND c.order_key<>r.desired_order
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_list(
            p_site_id uuid,p_page_id uuid
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id,'composition:read');
            IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id) THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,
                c.row_version,c.created_at,c.updated_at
            FROM content.page_composition c
            WHERE c.site_id=p_site_id AND c.page_id=p_page_id
              AND content.slaif_agent_page_accessible(p_site_id,p_page_id)
            ORDER BY c.parent_id NULLS FIRST,c.slot_key COLLATE "C",c.order_key,c.id
            LIMIT COALESCE((
                SELECT LEAST(
                    128,
                    COALESCE(NULLIF(cap.resource_constraints->>'max_components_per_page','')::integer,128)
                )
                FROM control.capability cap
                WHERE cap.id=NULLIF(current_setting('app.capability_id',true),'')::uuid
            ),128);
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_get(
            p_site_id uuid,p_component_id uuid
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,
                c.row_version,c.created_at,c.updated_at
            FROM content.page_composition c
            WHERE c.site_id=p_site_id AND c.id=p_component_id
              AND content.slaif_agent_page_accessible(p_site_id,c.page_id)
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_create(
            p_site_id uuid,p_page_id uuid,p_component_type text,p_parent_id uuid,
            p_slot_key text,p_before uuid,p_after uuid,p_props jsonb
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE workspace_id uuid; capability_id uuid; position integer;
            anchor_parent uuid; anchor_slot text; anchor_order integer;
            new_id uuid; constraints jsonb; visible_count integer; parent_depth integer:=0;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'component-structure:create');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT cap.resource_constraints INTO constraints
            FROM control.capability cap WHERE cap.id=capability_id;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            IF p_before IS NOT NULL AND p_after IS NOT NULL THEN
                RAISE EXCEPTION 'COMPONENT_ANCHORS_INVALID' USING ERRCODE='P0003';
            END IF;
            IF NOT content.slaif_agent_page_accessible(p_site_id,p_page_id) THEN
                RAISE EXCEPTION 'PAGE_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            PERFORM content.slaif_agent_component_validate(
                p_site_id,p_page_id,NULL,p_component_type,'1',p_parent_id,
                p_slot_key,p_props,false);
            IF jsonb_typeof(constraints->'allowed_component_types')='array'
               AND NOT (constraints->'allowed_component_types' ? p_component_type)
            THEN RAISE EXCEPTION 'COMPONENT_TYPE_DENIED' USING ERRCODE='P0007'; END IF;
            SELECT count(*) INTO visible_count FROM content.page_composition c
            WHERE c.site_id=p_site_id AND c.page_id=p_page_id;
            IF NULLIF(constraints->>'max_components_per_page','') IS NOT NULL
               AND visible_count+1 > (constraints->>'max_components_per_page')::integer
            THEN RAISE EXCEPTION 'COMPONENT_PAGE_LIMIT' USING ERRCODE='P0003'; END IF;
            SELECT count(*) INTO visible_count FROM content.page_composition c
            WHERE c.site_id=p_site_id
              AND content.slaif_agent_page_accessible(p_site_id,c.page_id);
            IF NULLIF(constraints->>'max_visible_components','') IS NOT NULL
               AND visible_count+1 > (constraints->>'max_visible_components')::integer
            THEN RAISE EXCEPTION 'COMPONENT_PAGE_LIMIT' USING ERRCODE='P0003'; END IF;
            IF p_parent_id IS NOT NULL THEN
                WITH RECURSIVE ancestors(id,parent_id,depth) AS (
                    SELECT c.id,c.parent_id,1 FROM content.page_composition c
                    WHERE c.id=p_parent_id AND c.site_id=p_site_id AND c.page_id=p_page_id
                    UNION ALL
                    SELECT c.id,c.parent_id,a.depth+1
                    FROM content.page_composition c JOIN ancestors a ON c.id=a.parent_id
                    WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                ) SELECT coalesce(max(depth),0) INTO parent_depth FROM ancestors;
            END IF;
            IF parent_depth+1 > 16 THEN
                RAISE EXCEPTION 'COMPONENT_DEPTH_LIMIT' USING ERRCODE='P0003';
            END IF;
            IF NULLIF(constraints->>'max_component_depth','') IS NOT NULL
               AND parent_depth+1 > (constraints->>'max_component_depth')::integer
            THEN RAISE EXCEPTION 'COMPONENT_DEPTH_LIMIT' USING ERRCODE='P0003'; END IF;
            IF p_before IS NOT NULL OR p_after IS NOT NULL THEN
                SELECT c.parent_id,c.slot_key,c.order_key INTO anchor_parent,anchor_slot,anchor_order
                FROM content.page_composition c
                WHERE c.id=coalesce(p_before,p_after) AND c.site_id=p_site_id AND c.page_id=p_page_id;
                IF NOT FOUND OR anchor_parent IS DISTINCT FROM p_parent_id OR anchor_slot<>p_slot_key THEN
                    RAISE EXCEPTION 'COMPONENT_ANCHOR_INVALID' USING ERRCODE='P0003';
                END IF;
                position:=anchor_order+CASE WHEN p_after IS NOT NULL THEN 1 ELSE 0 END;
            ELSE
                SELECT coalesce(max(c.order_key)+1,0) INTO position
                FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                  AND c.parent_id IS NOT DISTINCT FROM p_parent_id AND c.slot_key=p_slot_key;
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            new_id:=gen_random_uuid();
            INSERT INTO content.page_composition(
                id,site_id,page_id,component_type,schema_version,catalog_version,
                parent_id,slot_key,order_key,props,row_version
            ) VALUES (
                new_id,p_site_id,p_page_id,p_component_type,'1','catalog-v1',p_parent_id,
                p_slot_key,position,p_props,1
            );
            PERFORM content.slaif_agent_component_reposition(
                p_site_id,p_page_id,new_id,p_parent_id,p_slot_key,position);
            PERFORM content.slaif_agent_component_tree_validate(p_site_id,p_page_id);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,c.row_version,
                c.created_at,c.updated_at FROM content.page_composition c WHERE c.id=new_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_update(
            p_site_id uuid,p_component_id uuid,p_props jsonb,p_expected integer
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record; workspace_id uuid; capability_id uuid;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'component-content-props:write');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT c.* INTO old FROM content.page_composition c
            WHERE c.id=p_component_id AND c.site_id=p_site_id;
            IF NOT FOUND OR NOT content.slaif_agent_page_accessible(p_site_id,old.page_id) THEN
                RAISE EXCEPTION 'COMPONENT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF p_expected IS NULL OR p_expected<=0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            IF old.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM jsonb_object_keys(
                    coalesce(old.props,'{}'::jsonb) || coalesce(p_props,'{}'::jsonb)
                ) key
                CROSS JOIN LATERAL jsonb_array_elements(
                    (SELECT c.definitions FROM control.component_catalog c
                     WHERE c.version='catalog-v1')
                ) definition
                WHERE definition->>'type'=old.component_type
                  AND (definition->'props'->key->>'authority')='design'
                  AND (p_props->key) IS DISTINCT FROM (old.props->key)
            ) THEN RAISE EXCEPTION 'COMPONENT_DESIGN_PROP' USING ERRCODE='P0007'; END IF;
            PERFORM content.slaif_agent_component_validate(
                p_site_id,old.page_id,old.id,old.component_type,old.schema_version,
                old.parent_id,old.slot_key,p_props,true);
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page_composition c SET props=p_props,row_version=c.row_version+1,
                updated_at=now() WHERE c.id=p_component_id AND c.site_id=p_site_id
                AND c.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_component_tree_validate(p_site_id,old.page_id);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,c.row_version,
                c.created_at,c.updated_at FROM content.page_composition c WHERE c.id=p_component_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_move(
            p_site_id uuid,p_component_id uuid,p_parent_id uuid,p_slot_key text,
            p_before uuid,p_after uuid,p_expected integer
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record; workspace_id uuid; capability_id uuid; position integer;
            anchor_order integer; anchor_parent uuid; anchor_slot text;
            constraints jsonb; parent_depth integer:=0; subtree_height integer:=0;
            visible_count integer;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'component-structure:move');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            SELECT cap.resource_constraints INTO constraints
            FROM control.capability cap WHERE cap.id=capability_id;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            IF p_before IS NOT NULL AND p_after IS NOT NULL THEN
                RAISE EXCEPTION 'COMPONENT_ANCHORS_INVALID' USING ERRCODE='P0003';
            END IF;
            SELECT c.* INTO old FROM content.page_composition c
            WHERE c.id=p_component_id AND c.site_id=p_site_id;
            IF NOT FOUND OR NOT content.slaif_agent_page_accessible(p_site_id,old.page_id) THEN
                RAISE EXCEPTION 'COMPONENT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF p_expected IS NULL OR p_expected<=0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            IF old.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF p_parent_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM content.page_composition c
                WHERE c.id=p_parent_id AND c.site_id=p_site_id AND c.page_id=old.page_id
            ) THEN RAISE EXCEPTION 'COMPONENT_PARENT_INVALID' USING ERRCODE='P0002'; END IF;
            IF p_parent_id=p_component_id THEN
                RAISE EXCEPTION 'COMPONENT_PARENT_INVALID' USING ERRCODE='P0003';
            END IF;
            IF p_parent_id IS NOT NULL THEN
                WITH RECURSIVE ancestors(id,parent_id,depth) AS (
                    SELECT c.id,c.parent_id,1 FROM content.page_composition c
                    WHERE c.id=p_parent_id AND c.site_id=p_site_id AND c.page_id=old.page_id
                    UNION ALL
                    SELECT c.id,c.parent_id,a.depth+1
                    FROM content.page_composition c JOIN ancestors a ON c.id=a.parent_id
                    WHERE c.site_id=p_site_id AND c.page_id=old.page_id
                ) SELECT coalesce(max(depth),0) INTO parent_depth FROM ancestors;
            END IF;
            WITH RECURSIVE descendants(id,relative_depth) AS (
                SELECT c.id,0 FROM content.page_composition c
                WHERE c.id=p_component_id AND c.site_id=p_site_id AND c.page_id=old.page_id
                UNION ALL
                SELECT child.id,d.relative_depth+1
                FROM content.page_composition child JOIN descendants d
                  ON child.parent_id=d.id
                WHERE child.site_id=p_site_id AND child.page_id=old.page_id
            ) SELECT coalesce(max(relative_depth),0) INTO subtree_height FROM descendants;
            SELECT count(*) INTO visible_count FROM content.page_composition c
            WHERE c.site_id=p_site_id AND c.page_id=old.page_id;
            IF NULLIF(constraints->>'max_components_per_page','') IS NOT NULL
               AND visible_count > (constraints->>'max_components_per_page')::integer
            THEN RAISE EXCEPTION 'COMPONENT_PAGE_LIMIT' USING ERRCODE='P0003'; END IF;
            IF parent_depth+1+subtree_height > 16 THEN
                RAISE EXCEPTION 'COMPONENT_DEPTH_LIMIT' USING ERRCODE='P0003';
            END IF;
            IF NULLIF(constraints->>'max_component_depth','') IS NOT NULL
               AND parent_depth+1+subtree_height > (constraints->>'max_component_depth')::integer
            THEN RAISE EXCEPTION 'COMPONENT_DEPTH_LIMIT' USING ERRCODE='P0003'; END IF;
            IF p_before IS NOT NULL OR p_after IS NOT NULL THEN
                SELECT c.parent_id,c.slot_key,c.order_key INTO anchor_parent,anchor_slot,anchor_order
                FROM content.page_composition c
                WHERE c.id=coalesce(p_before,p_after) AND c.site_id=p_site_id AND c.page_id=old.page_id;
                IF NOT FOUND OR anchor_parent IS DISTINCT FROM p_parent_id OR anchor_slot<>p_slot_key
                   OR coalesce(p_before,p_after)=p_component_id
                THEN RAISE EXCEPTION 'COMPONENT_ANCHOR_INVALID' USING ERRCODE='P0003'; END IF;
                IF p_before IS NOT NULL THEN
                    SELECT count(*) INTO position FROM content.page_composition c
                    WHERE c.site_id=p_site_id AND c.page_id=old.page_id
                      AND c.id<>p_component_id
                      AND c.parent_id IS NOT DISTINCT FROM p_parent_id
                      AND c.slot_key=p_slot_key AND c.order_key<anchor_order;
                ELSE
                    SELECT count(*) INTO position FROM content.page_composition c
                    WHERE c.site_id=p_site_id AND c.page_id=old.page_id
                      AND c.id<>p_component_id
                      AND c.parent_id IS NOT DISTINCT FROM p_parent_id
                      AND c.slot_key=p_slot_key AND c.order_key<=anchor_order;
                END IF;
            ELSE
                SELECT count(*) INTO position FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=old.page_id
                  AND c.id<>p_component_id
                  AND c.parent_id IS NOT DISTINCT FROM p_parent_id
                  AND c.slot_key=p_slot_key;
            END IF;
            PERFORM content.slaif_agent_component_validate(
                p_site_id,old.page_id,old.id,old.component_type,old.schema_version,
                p_parent_id,p_slot_key,old.props,true);
            -- A satisfied semantic move is a deliberate versioned no-op: it
            -- consumes the normal mutation quota and produces one audit event,
            -- while only advancing the requested row version.
            IF old.parent_id IS NOT DISTINCT FROM p_parent_id
               AND old.slot_key=p_slot_key AND old.order_key=position THEN
                IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                    RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
                END IF;
                UPDATE content.page_composition c SET row_version=c.row_version+1,
                    updated_at=now()
                WHERE c.id=p_component_id AND c.site_id=p_site_id
                  AND c.row_version=p_expected;
                IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            ELSE
                IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                    RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
                END IF;
                PERFORM content.slaif_agent_component_reposition(
                    p_site_id,old.page_id,p_component_id,p_parent_id,p_slot_key,position);
            END IF;
            PERFORM content.slaif_agent_component_tree_validate(p_site_id,old.page_id);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,c.row_version,
                c.created_at,c.updated_at FROM content.page_composition c WHERE c.id=p_component_id;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_delete(
            p_site_id uuid,p_component_id uuid,p_expected integer
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record; workspace_id uuid; capability_id uuid;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'component-structure:delete');
            workspace_id:=NULLIF(current_setting('app.session_id',true),'')::uuid;
            PERFORM control.slaif_agent_structural_lock(p_site_id);
            SELECT c.* INTO old FROM content.page_composition c
            WHERE c.id=p_component_id AND c.site_id=p_site_id;
            IF NOT FOUND OR NOT content.slaif_agent_page_accessible(p_site_id,old.page_id) THEN
                RAISE EXCEPTION 'COMPONENT_NOT_FOUND' USING ERRCODE='P0002';
            END IF;
            IF p_expected IS NULL OR p_expected<=0 THEN
                RAISE EXCEPTION 'ROW_VERSION_REQUIRED' USING ERRCODE='P0003';
            END IF;
            IF old.row_version<>p_expected THEN
                RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004';
            END IF;
            IF EXISTS (
                SELECT 1 FROM content.page_composition c
                WHERE c.parent_id=p_component_id AND c.site_id=p_site_id
                  AND c.page_id=old.page_id
            ) THEN
                RAISE EXCEPTION 'COMPONENT_DEPENDENCIES' USING ERRCODE='P0003';
            END IF;
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'delete') THEN
                RAISE EXCEPTION 'AGENT_DELETE_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            DELETE FROM content.page_composition c WHERE c.id=p_component_id AND c.site_id=p_site_id
                AND c.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_component_resequence(
                p_site_id,old.page_id,old.parent_id,old.slot_key);
            PERFORM content.slaif_agent_component_tree_validate(p_site_id,old.page_id);
            RETURN QUERY SELECT old.id,old.site_id,old.page_id,old.component_type,
                old.schema_version,old.catalog_version,old.parent_id,old.slot_key,
                old.order_key,old.props,old.row_version,old.created_at,old.updated_at;
        END;
        $fn$;
    """


def _semantic_completion_sql() -> str:
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
                     AND allowed.quota_kind=p_quota_kind
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
        $fn$;
    """


def _legacy_semantic_constraint_sql() -> str:
    return """ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
        (http_method IS NULL AND quota_kind IS NULL)
        OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED','REDIRECT_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
        OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED','REDIRECT_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
        OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED','REDIRECT_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
        OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
    )"""


def _legacy_composition_sql(*, restored: bool = False) -> str:
    if restored:
        return """
            CREATE OR REPLACE FUNCTION content.slaif_composition_node_add(
                p_site_id uuid,p_page_id uuid,p_component_type text,p_parent_id uuid,
                p_slot_key text,p_order_key integer,p_props jsonb
            ) RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,
                schema_version text,parent_id uuid,slot_key text,order_key integer,
                props jsonb,created_at timestamptz,updated_at timestamptz)
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            BEGIN
                INSERT INTO content.page_composition(site_id,page_id,component_type,parent_id,slot_key,order_key,props)
                VALUES(p_site_id,p_page_id,p_component_type,p_parent_id,p_slot_key,p_order_key,p_props);
                RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                    c.parent_id,c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
                FROM content.page_composition c WHERE c.site_id=p_site_id AND c.page_id=p_page_id
                  AND c.component_type=p_component_type AND c.slot_key=p_slot_key
                  AND c.order_key=p_order_key ORDER BY c.created_at DESC LIMIT 1;
            END; $fn$;
            CREATE OR REPLACE FUNCTION content.slaif_composition_node_update(
                p_node_id uuid,p_props jsonb,p_slot_key text,p_order_key integer
            ) RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,
                schema_version text,parent_id uuid,slot_key text,order_key integer,
                props jsonb,created_at timestamptz,updated_at timestamptz)
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            BEGIN
                UPDATE content.page_composition SET props=coalesce(p_props,props),
                    slot_key=coalesce(p_slot_key,slot_key),order_key=coalesce(p_order_key,order_key),updated_at=now()
                WHERE id=p_node_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
                RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                    c.parent_id,c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
                FROM content.page_composition c WHERE c.id=p_node_id;
            END; $fn$;
            CREATE OR REPLACE FUNCTION content.slaif_composition_node_move(
                p_node_id uuid,p_new_parent_id uuid,p_new_slot_key text,p_new_order_key integer
            ) RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,
                schema_version text,parent_id uuid,slot_key text,order_key integer,
                props jsonb,created_at timestamptz,updated_at timestamptz)
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            BEGIN
                UPDATE content.page_composition SET parent_id=coalesce(p_new_parent_id,parent_id),
                    slot_key=coalesce(p_new_slot_key,slot_key),order_key=p_new_order_key,updated_at=now()
                WHERE id=p_node_id;
                IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
                RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                    c.parent_id,c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
                FROM content.page_composition c WHERE c.id=p_node_id;
            END; $fn$;
            CREATE OR REPLACE FUNCTION content.slaif_composition_node_delete(p_node_id uuid)
            RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            BEGIN DELETE FROM content.page_composition WHERE id=p_node_id; END; $fn$;
            CREATE OR REPLACE FUNCTION content.slaif_composition_list(p_page_id uuid)
            RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
                parent_id uuid,slot_key text,order_key integer,props jsonb,created_at timestamptz,updated_at timestamptz)
            LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
                SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,c.parent_id,
                    c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
                FROM content.page_composition c WHERE c.page_id=p_page_id
                ORDER BY c.slot_key COLLATE "C",c.order_key
            $fn$;
        """
    return """
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_add(
            p_site_id uuid,p_page_id uuid,p_component_type text,p_parent_id uuid,
            p_slot_key text,p_order_key integer,p_props jsonb
        ) RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,
            schema_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE new_id uuid;
        BEGIN
            PERFORM content.slaif_agent_component_validate(
                p_site_id,p_page_id,NULL,p_component_type,'1',p_parent_id,p_slot_key,p_props,true);
            new_id:=gen_random_uuid();
            INSERT INTO content.page_composition(id,site_id,page_id,component_type,schema_version,
                catalog_version,parent_id,slot_key,order_key,props,row_version)
            VALUES(new_id,p_site_id,p_page_id,p_component_type,'1','catalog-v1',p_parent_id,p_slot_key,
                coalesce(p_order_key,0),p_props,1);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.parent_id,c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
            FROM content.page_composition c WHERE c.id=new_id;
        END; $fn$;
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_update(
            p_node_id uuid,p_props jsonb,p_slot_key text,p_order_key integer
        ) RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,
            schema_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record; merged jsonb;
        BEGIN
            SELECT c.* INTO old FROM content.page_composition c WHERE c.id=p_node_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            merged:=coalesce(p_props,old.props);
            PERFORM content.slaif_agent_component_validate(old.site_id,old.page_id,old.id,
                old.component_type,old.schema_version,old.parent_id,coalesce(p_slot_key,old.slot_key),merged,true);
            UPDATE content.page_composition AS composition
            SET props=merged,slot_key=coalesce(p_slot_key,composition.slot_key),
                order_key=coalesce(p_order_key,composition.order_key),
                row_version=composition.row_version+1,updated_at=now()
            WHERE composition.id=p_node_id;
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.parent_id,c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
            FROM content.page_composition c WHERE c.id=p_node_id;
        END; $fn$;
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_move(
            p_node_id uuid,p_new_parent_id uuid,p_new_slot_key text,p_new_order_key integer
        ) RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,
            schema_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record;
        BEGIN
            SELECT c.* INTO old FROM content.page_composition c WHERE c.id=p_node_id;
            IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
            PERFORM content.slaif_agent_component_validate(old.site_id,old.page_id,old.id,
                old.component_type,old.schema_version,p_new_parent_id,coalesce(p_new_slot_key,old.slot_key),old.props,true);
            UPDATE content.page_composition AS composition
            SET parent_id=coalesce(p_new_parent_id,composition.parent_id),
                slot_key=coalesce(p_new_slot_key,composition.slot_key),
                order_key=coalesce(p_new_order_key,composition.order_key),
                row_version=composition.row_version+1,updated_at=now()
            WHERE composition.id=p_node_id;
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.parent_id,c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
            FROM content.page_composition c WHERE c.id=p_node_id;
        END; $fn$;
        CREATE OR REPLACE FUNCTION content.slaif_composition_node_delete(p_node_id uuid)
        RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record; child uuid;
        BEGIN
            SELECT c.* INTO old FROM content.page_composition c WHERE c.id=p_node_id;
            IF NOT FOUND THEN RETURN; END IF;
            FOR child IN SELECT id FROM content.page_composition WHERE parent_id=p_node_id LOOP
                PERFORM content.slaif_composition_node_delete(child);
            END LOOP;
            DELETE FROM content.page_composition AS composition WHERE composition.id=p_node_id;
        END; $fn$;
        CREATE OR REPLACE FUNCTION content.slaif_composition_list(p_page_id uuid)
        RETURNS TABLE(id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            parent_id uuid,slot_key text,order_key integer,props jsonb,created_at timestamptz,updated_at timestamptz)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
            SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,c.parent_id,
                c.slot_key,c.order_key,c.props,c.created_at,c.updated_at
            FROM content.page_composition c WHERE c.page_id=p_page_id
            ORDER BY c.parent_id NULLS FIRST,c.slot_key COLLATE "C",c.order_key,c.id
        $fn$;
    """


def upgrade() -> None:
    op.execute(
        "ALTER FUNCTION control.slaif_agent_resource_constraints(uuid) "
        "RENAME TO slaif_agent_resource_constraints_059"
    )
    _execute_block(_resource_constraint_sql())
    _execute_block(_catalog_sql())
    _execute_block(_nested_validator_sql())
    _execute_block(_schema_validator_sql())
    _execute_block(_component_validator_sql())
    _execute_block(_tree_validator_sql())
    op.execute(
        "ALTER TABLE content.page_composition ADD COLUMN catalog_version text NOT NULL DEFAULT 'catalog-v1'"
    )
    op.execute(
        "ALTER TABLE content.page_composition ADD COLUMN row_version integer NOT NULL DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE content.page_composition ADD CONSTRAINT page_composition_row_version_positive CHECK (row_version>0)"
    )
    _execute_block(_legacy_composition_sql())
    _execute_block(_agent_component_sql())
    op.execute(
        "ALTER FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "RENAME TO slaif_agent_idempotency_complete_059"
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(
        """ALTER TABLE audit.agent_mutation ADD CONSTRAINT agent_mutation_semantic_shape CHECK (
            (http_method IS NULL AND quota_kind IS NULL)
            OR (action IN ('CONTENT_TYPE_CREATED','FIELD_DEFINITION_CREATED','CONTENT_ITEM_CREATED','CONTENT_ITEM_TRANSLATION_CREATED','ITEM_RELATION_CREATED','COLLECTION_VIEW_CREATED','PAGE_CREATED','LOCALE_CREATED','NAVIGATION_CREATED','NAVIGATION_ITEM_CREATED','REDIRECT_CREATED','COMPONENT_CREATED') AND http_method='POST' AND response_status=201 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_UPDATED','FIELD_DEFINITION_UPDATED','CONTENT_ITEM_UPDATED','CONTENT_ITEM_TRANSLATION_UPDATED','ITEM_RELATION_UPDATED','COLLECTION_VIEW_UPDATED','PAGE_UPDATED','LOCALE_UPDATED','NAVIGATION_UPDATED','NAVIGATION_ITEM_UPDATED','REDIRECT_UPDATED','COMPONENT_UPDATED') AND http_method='PATCH' AND response_status=200 AND quota_kind='mutation')
            OR (action IN ('CONTENT_TYPE_DELETED','FIELD_DEFINITION_DELETED','CONTENT_ITEM_DELETED','CONTENT_ITEM_TRANSLATION_DELETED','ITEM_RELATION_DELETED','COLLECTION_VIEW_DELETED','PAGE_DELETED','LOCALE_DELETED','NAVIGATION_DELETED','NAVIGATION_ITEM_DELETED','REDIRECT_DELETED','COMPONENT_DELETED') AND http_method='DELETE' AND response_status=200 AND quota_kind='delete')
            OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED','COMPONENT_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')
        )"""
    )
    _execute_block(_semantic_completion_sql())
    op.execute(
        "ALTER FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "TO slaif_agent_runtime"
    )
    for function in _NEW_FUNCTIONS[2:]:
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    for function in (
        "content.slaif_agent_component_list(uuid,uuid)",
        "content.slaif_agent_component_get(uuid,uuid)",
        "content.slaif_agent_component_create(uuid,uuid,text,uuid,text,uuid,uuid,jsonb)",
        "content.slaif_agent_component_update(uuid,uuid,jsonb,integer)",
        "content.slaif_agent_component_move(uuid,uuid,uuid,text,uuid,uuid,integer)",
        "content.slaif_agent_component_delete(uuid,uuid,integer)",
    ):
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")


def downgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE relation_kind "char";
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='page_composition';
            IF relation_kind='v' THEN
                RAISE EXCEPTION '053_DOWNGRADE_REQUIRES_PUBLIC_COW_DISABLE'
                    USING ERRCODE='P0003';
            END IF;
        END $$
        """
    )
    for function in reversed(_NEW_FUNCTIONS[2:]):
        op.execute(f"DROP FUNCTION IF EXISTS {function}")
    op.execute("DROP FUNCTION IF EXISTS content.slaif_component_reject_nested(jsonb)")
    op.execute(
        "ALTER TABLE content.page_composition DROP CONSTRAINT IF EXISTS page_composition_row_version_positive"
    )
    op.execute("ALTER TABLE content.page_composition DROP COLUMN IF EXISTS row_version")
    op.execute(
        "ALTER TABLE content.page_composition DROP COLUMN IF EXISTS catalog_version"
    )
    _execute_block(_legacy_composition_sql(restored=True))
    op.execute("DROP FUNCTION control.slaif_agent_resource_constraints(uuid)")
    op.execute(
        "ALTER FUNCTION control.slaif_agent_resource_constraints_059(uuid) "
        "RENAME TO slaif_agent_resource_constraints"
    )
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_legacy_semantic_constraint_sql())
    op.execute(
        "DROP FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text)"
    )
    op.execute(
        "ALTER FUNCTION control.slaif_agent_idempotency_complete_059("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "RENAME TO slaif_agent_idempotency_complete"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_agent_idempotency_complete("
        "uuid,uuid,text,text,uuid,integer,jsonb,text,uuid,uuid,text,text,text) "
        "TO slaif_agent_runtime"
    )
    op.execute("DROP FUNCTION IF EXISTS control.slaif_component_catalog()")
    op.execute("DROP TABLE IF EXISTS control.component_catalog")

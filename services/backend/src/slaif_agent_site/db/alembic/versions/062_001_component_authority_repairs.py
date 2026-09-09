# ruff: noqa: E501
"""Repair component property authority, initial design selection, and replay."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any

from alembic import op

revision: str = "062_001"
down_revision: str | Sequence[str] | None = "061_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DESIGN_SCOPE_FUNCTION = "control.slaif_agent_component_design_scope(text,text)"
_AUTHORIZE_UPDATE_FUNCTION = (
    "control.slaif_agent_component_authorize_update(uuid,text,jsonb,jsonb)"
)
_AUTHORIZE_CREATE_FUNCTION = (
    "control.slaif_agent_component_authorize_create(uuid,text,jsonb)"
)
_COMPONENT_CREATE_FUNCTION = (
    "content.slaif_agent_component_create(uuid,uuid,text,uuid,text,uuid,uuid,jsonb)"
)
_COMPONENT_UPDATE_FUNCTION = (
    "content.slaif_agent_component_update(uuid,uuid,jsonb,integer)"
)
_M061: Any = import_module(
    "slaif_agent_site.db.alembic.versions.061_001_agent_component_design_semantics"
)


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


def _authority_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION control.slaif_agent_component_authorize_update(
            p_site_id uuid,p_component_type text,p_old_props jsonb,p_new_props jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE capability_id uuid; scopes jsonb; constraints jsonb; key text;
            old_value jsonb; new_value jsonb; authority text; required_scope text;
            old_present boolean; new_present boolean; old_responsive boolean;
            new_responsive boolean;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'site:read');
            SELECT c.scopes,coalesce(c.resource_constraints,'{}'::jsonb)
                INTO scopes,constraints
            FROM control.capability c WHERE c.id=capability_id;
            IF p_old_props IS NULL OR p_new_props IS NULL
               OR jsonb_typeof(p_old_props)<>'object'
               OR jsonb_typeof(p_new_props)<>'object'
            THEN RAISE EXCEPTION 'COMPONENT_PROPS_INVALID' USING ERRCODE='P0003'; END IF;
            FOR key IN
                SELECT jsonb_object_keys(coalesce(p_old_props,'{}'::jsonb)
                    ||coalesce(p_new_props,'{}'::jsonb))
            LOOP
                old_present:=p_old_props ? key;
                new_present:=(p_new_props ? key)
                    AND jsonb_typeof(p_new_props->key)<>'null';
                old_value:=p_old_props->key;
                new_value:=p_new_props->key;
                IF old_present IS DISTINCT FROM new_present
                   OR (new_present AND old_value IS DISTINCT FROM new_value)
                THEN
                    required_scope:=control.slaif_agent_component_design_scope(
                        p_component_type,key);
                    SELECT entry->'props'->key->>'authority' INTO authority
                    FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                    WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                    IF required_scope IS NULL THEN
                        IF authority='design' THEN
                            RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED'
                                USING ERRCODE='P0003';
                        END IF;
                        IF NOT (scopes ? 'component-content-props:write') THEN
                            RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                        END IF;
                    ELSE
                        IF NOT (scopes ? required_scope) THEN
                            RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                        END IF;
                        old_responsive:=old_present
                            AND jsonb_typeof(old_value)='object'
                            AND (SELECT count(*) FROM jsonb_object_keys(old_value))>0
                            AND NOT EXISTS (
                                SELECT 1 FROM jsonb_object_keys(old_value) label
                                WHERE label NOT IN ('desktop','tablet','mobile')
                            );
                        new_responsive:=new_present
                            AND jsonb_typeof(new_value)='object'
                            AND (SELECT count(*) FROM jsonb_object_keys(new_value))>0
                            AND NOT EXISTS (
                                SELECT 1 FROM jsonb_object_keys(new_value) label
                                WHERE label NOT IN ('desktop','tablet','mobile')
                            );
                        IF new_responsive
                           AND constraints->>'responsive_design_enabled'='false'
                        THEN
                            RAISE EXCEPTION 'AGENT_RESOURCE_DENIED' USING ERRCODE='P0007';
                        END IF;
                        IF (old_responsive OR new_responsive)
                           AND NOT (scopes ? 'responsive-design:write')
                        THEN
                            RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                        END IF;
                        IF key='variant' AND new_present
                           AND jsonb_typeof(constraints->'allowed_component_variants')='array'
                        THEN
                            IF new_responsive THEN
                                IF EXISTS (
                                    SELECT 1 FROM jsonb_each_text(new_value) item
                                    WHERE NOT (
                                        constraints->'allowed_component_variants' ? item.value
                                    )
                                ) THEN
                                    RAISE EXCEPTION 'AGENT_RESOURCE_DENIED'
                                        USING ERRCODE='P0007';
                                END IF;
                            ELSIF NOT (
                                constraints->'allowed_component_variants' ? (new_value #>> '{}')
                            ) THEN
                                RAISE EXCEPTION 'AGENT_RESOURCE_DENIED'
                                    USING ERRCODE='P0007';
                            END IF;
                        END IF;
                    END IF;
                END IF;
            END LOOP;
            RETURN capability_id;
        END;
        $fn$;

        CREATE OR REPLACE FUNCTION control.slaif_agent_component_authorize_create(
            p_site_id uuid,p_component_type text,p_props jsonb
        ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE capability_id uuid; scopes jsonb; constraints jsonb; key text;
            value jsonb; authority text; required_scope text; normalized jsonb;
            responsive boolean;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'component-structure:create');
            SELECT c.scopes,coalesce(c.resource_constraints,'{}'::jsonb)
                INTO scopes,constraints
            FROM control.capability c WHERE c.id=capability_id;
            IF p_props IS NULL OR jsonb_typeof(p_props)<>'object'
            THEN RAISE EXCEPTION 'COMPONENT_PROPS_INVALID' USING ERRCODE='P0003'; END IF;
            FOR key,value IN SELECT entry.key,entry.value FROM jsonb_each(p_props) entry
            LOOP
                required_scope:=control.slaif_agent_component_design_scope(
                    p_component_type,key);
                SELECT entry->'props'->key->>'authority' INTO authority
                FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                IF required_scope IS NULL AND authority='design' THEN
                    RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED'
                        USING ERRCODE='P0003';
                END IF;
                IF required_scope IS NOT NULL THEN
                    IF NOT (scopes ? required_scope) THEN
                        RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                    END IF;
                    responsive:=jsonb_typeof(value)='object'
                        AND (SELECT count(*) FROM jsonb_object_keys(value))>0
                        AND NOT EXISTS (
                            SELECT 1 FROM jsonb_object_keys(value) label
                            WHERE label NOT IN ('desktop','tablet','mobile')
                        );
                    IF responsive
                       AND constraints->>'responsive_design_enabled'='false'
                    THEN
                        RAISE EXCEPTION 'AGENT_RESOURCE_DENIED' USING ERRCODE='P0007';
                    END IF;
                    IF responsive AND NOT (scopes ? 'responsive-design:write') THEN
                        RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                    END IF;
                    IF key='variant'
                       AND jsonb_typeof(constraints->'allowed_component_variants')='array'
                    THEN
                        IF responsive THEN
                            IF EXISTS (
                                SELECT 1 FROM jsonb_each_text(value) item
                                WHERE NOT (
                                    constraints->'allowed_component_variants' ? item.value
                                )
                            ) THEN
                                RAISE EXCEPTION 'AGENT_RESOURCE_DENIED'
                                    USING ERRCODE='P0007';
                            END IF;
                        ELSIF NOT (
                            constraints->'allowed_component_variants' ? (value #>> '{}')
                        ) THEN
                            RAISE EXCEPTION 'AGENT_RESOURCE_DENIED'
                                USING ERRCODE='P0007';
                        END IF;
                    END IF;
                END IF;
            END LOOP;
            normalized:=p_props;
            IF p_component_type='Columns' AND NOT (normalized ? 'count') THEN
                normalized:=jsonb_set(normalized,ARRAY['count'],'1'::jsonb,true);
            ELSIF p_component_type='Spacer' AND NOT (normalized ? 'size') THEN
                normalized:=jsonb_set(normalized,ARRAY['size'],'"md"'::jsonb,true);
            END IF;
            RETURN normalized;
        END;
        $fn$;
    """


def _component_create_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_agent_component_create(
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
            normalized_props jsonb;
        BEGIN
            normalized_props:=control.slaif_agent_component_authorize_create(
                p_site_id,p_component_type,p_props);
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
                p_slot_key,normalized_props,true);
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
                p_slot_key,position,normalized_props,1);
            PERFORM content.slaif_agent_component_reposition(
                p_site_id,p_page_id,new_id,p_parent_id,p_slot_key,position);
            PERFORM content.slaif_agent_component_tree_validate(p_site_id,p_page_id);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,c.row_version,
                c.created_at,c.updated_at FROM content.page_composition c WHERE c.id=new_id;
        END;
        $fn$;
    """


def _component_update_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_agent_component_update(
            p_site_id uuid,p_component_id uuid,p_props jsonb,p_expected integer
        ) RETURNS TABLE(
            id uuid,site_id uuid,page_id uuid,component_type text,schema_version text,
            catalog_version text,parent_id uuid,slot_key text,order_key integer,
            props jsonb,row_version integer,created_at timestamptz,updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
        DECLARE old record; workspace_id uuid; capability_id uuid;
            new_props jsonb; key text;
        BEGIN
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
            IF p_props IS NULL OR jsonb_typeof(p_props)<>'object' THEN
                RAISE EXCEPTION 'COMPONENT_PROPS_INVALID' USING ERRCODE='P0003';
            END IF;
            new_props:=p_props;
            FOR key IN SELECT jsonb_object_keys(p_props) LOOP
                IF jsonb_typeof(p_props->key)='null' AND old.props ? key THEN
                    new_props:=new_props-key;
                END IF;
            END LOOP;
            PERFORM control.slaif_agent_component_authorize_update(
                p_site_id,old.component_type,old.props,new_props);
            PERFORM content.slaif_agent_component_validate_design(
                p_site_id,old.page_id,old.id,old.component_type,old.schema_version,
                old.parent_id,old.slot_key,old.props,new_props,true);
            IF old.props IS NOT DISTINCT FROM new_props THEN
                RETURN QUERY SELECT old.id,old.site_id,old.page_id,old.component_type,
                    old.schema_version,old.catalog_version,old.parent_id,old.slot_key,
                    old.order_key,old.props,old.row_version,old.created_at,old.updated_at;
                RETURN;
            END IF;
            capability_id:=control.slaif_agent_require_capability(
                p_site_id,'site:read');
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page_composition c SET props=new_props,row_version=c.row_version+1,
                updated_at=now() WHERE c.id=p_component_id AND c.site_id=p_site_id
                AND c.row_version=p_expected;
            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            PERFORM content.slaif_agent_component_tree_validate_design(p_site_id,old.page_id);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,c.row_version,
                c.created_at,c.updated_at FROM content.page_composition c WHERE c.id=p_component_id;
        END;
        $fn$;
    """


def upgrade() -> None:
    _execute_block(_authority_sql())
    _execute_block(_component_update_sql())
    _execute_block(_component_create_sql())
    for function in (_DESIGN_SCOPE_FUNCTION, _AUTHORIZE_UPDATE_FUNCTION):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(f"ALTER FUNCTION {_AUTHORIZE_CREATE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_AUTHORIZE_CREATE_FUNCTION} FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_AUTHORIZE_CREATE_FUNCTION} TO slaif_agent_runtime"
    )
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_COMPONENT_CREATE_FUNCTION} TO slaif_agent_runtime"
    )


def downgrade() -> None:
    op.execute(f"DROP FUNCTION IF EXISTS {_AUTHORIZE_CREATE_FUNCTION}")
    op.execute(f"DROP FUNCTION IF EXISTS {_COMPONENT_CREATE_FUNCTION}")
    _execute_block("""
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
                p_slot_key,position,p_props,1);
            PERFORM content.slaif_agent_component_reposition(
                p_site_id,p_page_id,new_id,p_parent_id,p_slot_key,position);
            PERFORM content.slaif_agent_component_tree_validate(p_site_id,p_page_id);
            RETURN QUERY SELECT c.id,c.site_id,c.page_id,c.component_type,c.schema_version,
                c.catalog_version,c.parent_id,c.slot_key,c.order_key,c.props,c.row_version,
                c.created_at,c.updated_at FROM content.page_composition c WHERE c.id=new_id;
        END;
        $fn$;
    """)
    op.execute(f"ALTER FUNCTION {_COMPONENT_CREATE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_COMPONENT_CREATE_FUNCTION} FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_COMPONENT_CREATE_FUNCTION} TO slaif_agent_runtime"
    )
    _execute_block(_M061._component_update_sql())
    op.execute(f"ALTER FUNCTION {_COMPONENT_UPDATE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_COMPONENT_UPDATE_FUNCTION} FROM PUBLIC")
    op.execute(
        f"GRANT EXECUTE ON FUNCTION {_COMPONENT_UPDATE_FUNCTION} TO slaif_agent_runtime"
    )
    _execute_block("""
        CREATE OR REPLACE FUNCTION control.slaif_agent_component_authorize_update(
            p_site_id uuid,p_component_type text,p_old_props jsonb,p_new_props jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE capability_id uuid; scopes jsonb; constraints jsonb; key text;
            value jsonb; authority text; required_scope text;
        BEGIN
            capability_id:=control.slaif_agent_require_capability(p_site_id,'site:read');
            SELECT c.scopes,c.resource_constraints INTO scopes,constraints
            FROM control.capability c WHERE c.id=capability_id;
            IF p_old_props IS NULL OR p_new_props IS NULL
               OR jsonb_typeof(p_old_props)<>'object'
               OR jsonb_typeof(p_new_props)<>'object'
            THEN RAISE EXCEPTION 'COMPONENT_PROPS_INVALID' USING ERRCODE='P0003'; END IF;
            FOR key,value IN SELECT entry.key,entry.value FROM jsonb_each(p_new_props) entry LOOP
                IF (p_old_props->key) IS DISTINCT FROM value THEN
                    required_scope:=control.slaif_agent_component_design_scope(
                        p_component_type,key);
                    SELECT entry->'props'->key->>'authority' INTO authority
                    FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                    WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                    IF required_scope IS NULL THEN
                        IF authority='design' THEN
                            RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED'
                                USING ERRCODE='P0003';
                        END IF;
                        IF NOT (scopes ? 'component-content-props:write') THEN
                            RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                        END IF;
                    ELSE
                        IF NOT (scopes ? required_scope) THEN
                            RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                        END IF;
                        IF constraints->>'responsive_design_enabled'='false'
                           AND jsonb_typeof(value)='object'
                           AND (SELECT count(*) FROM jsonb_object_keys(value))>0
                           AND NOT EXISTS (
                               SELECT 1 FROM jsonb_object_keys(value) label
                               WHERE label NOT IN ('desktop','tablet','mobile')
                           )
                        THEN
                            RAISE EXCEPTION 'AGENT_RESOURCE_DENIED' USING ERRCODE='P0007';
                        END IF;
                        IF key='variant'
                           AND jsonb_typeof(constraints->'allowed_component_variants')='array'
                        THEN
                            IF jsonb_typeof(value)='object' THEN
                                IF EXISTS (
                                    SELECT 1 FROM jsonb_each_text(value) item
                                    WHERE NOT (
                                        constraints->'allowed_component_variants' ? item.value
                                    )
                                ) THEN
                                    RAISE EXCEPTION 'AGENT_RESOURCE_DENIED'
                                        USING ERRCODE='P0007';
                                END IF;
                            ELSIF NOT (
                                constraints->'allowed_component_variants' ? (value #>> '{}')
                            ) THEN
                                RAISE EXCEPTION 'AGENT_RESOURCE_DENIED'
                                    USING ERRCODE='P0007';
                            END IF;
                        END IF;
                        IF jsonb_typeof(value)='object'
                           AND (SELECT count(*) FROM jsonb_object_keys(value))>0
                           AND NOT EXISTS (
                               SELECT 1 FROM jsonb_object_keys(value) label
                               WHERE label NOT IN ('desktop','tablet','mobile')
                           )
                           AND NOT (scopes ? 'responsive-design:write')
                        THEN
                            RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
                        END IF;
                    END IF;
                END IF;
            END LOOP;
            RETURN capability_id;
        END;
        $fn$;
    """)
    op.execute(f"ALTER FUNCTION {_AUTHORIZE_UPDATE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_AUTHORIZE_UPDATE_FUNCTION} FROM PUBLIC")
    op.execute(f"ALTER FUNCTION {_DESIGN_SCOPE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_DESIGN_SCOPE_FUNCTION} FROM PUBLIC")

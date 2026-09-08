# ruff: noqa: E501
"""Add the append-only design-system/v1 Agent component update boundary."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "061_001"
down_revision: str | Sequence[str] | None = "060_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DESIGN_SCOPE_FUNCTION = "control.slaif_agent_component_design_scope(text,text)"
_AUTHORIZE_FUNCTION = (
    "control.slaif_agent_component_authorize_update(uuid,text,jsonb,jsonb)"
)
_VALIDATE_FUNCTION = (
    "content.slaif_agent_component_validate_design("
    "uuid,uuid,uuid,text,text,uuid,text,jsonb,jsonb,boolean)"
)
_TREE_VALIDATE_FUNCTION = (
    "content.slaif_agent_component_tree_validate_design(uuid,uuid)"
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
        CREATE FUNCTION control.slaif_agent_component_design_scope(
            p_component_type text,p_prop_key text
        ) RETURNS text LANGUAGE sql IMMUTABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
            SELECT CASE
                WHEN p_component_type='Section' AND p_prop_key='variant'
                    THEN 'component-variant:write'
                WHEN p_component_type IN ('Section','Container','Columns','Grid','Stack','Heading')
                     AND p_prop_key='alignment' THEN 'layout:write'
                WHEN p_component_type='Container' AND p_prop_key='width'
                    THEN 'layout:write'
                WHEN p_component_type='Columns' AND p_prop_key IN ('count','gap')
                    THEN 'layout:write'
                WHEN p_component_type='Grid' AND p_prop_key IN ('columns','gap')
                    THEN 'layout:write'
                WHEN p_component_type='Stack' AND p_prop_key IN ('direction','gap')
                    THEN 'layout:write'
                WHEN p_component_type='Spacer' AND p_prop_key='size'
                    THEN 'layout:write'
                ELSE NULL
            END
        $fn$;

        CREATE FUNCTION control.slaif_agent_component_authorize_update(
            p_site_id uuid,p_component_type text,p_old_props jsonb,p_new_props jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE capability_id uuid; scopes jsonb; constraints jsonb; key text;
            value jsonb; authority text; required_scope text; changed boolean:=false;
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
                    changed:=true;
                    required_scope:=control.slaif_agent_component_design_scope(
                        p_component_type,key);
                    SELECT entry->'props'->key->>'authority' INTO authority
                    FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                    WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                    IF required_scope IS NULL AND authority='design' THEN
                        RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED' USING ERRCODE='P0003';
                    ELSIF required_scope IS NULL OR authority='content' THEN
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
                                    WHERE NOT (constraints->'allowed_component_variants' ? item.value)
                                ) THEN
                                    RAISE EXCEPTION 'AGENT_RESOURCE_DENIED' USING ERRCODE='P0007';
                                END IF;
                            ELSIF NOT (constraints->'allowed_component_variants' ? (value #>> '{}')) THEN
                                RAISE EXCEPTION 'AGENT_RESOURCE_DENIED' USING ERRCODE='P0007';
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
            IF NOT changed AND NOT (scopes ? 'component-content-props:write') THEN
                RAISE EXCEPTION 'AGENT_SCOPE_DENIED' USING ERRCODE='P0007';
            END IF;
            RETURN capability_id;
        END;
        $fn$;
    """


def _design_validator_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_agent_component_validate_design(
            p_site_id uuid,p_page_id uuid,p_node_id uuid,p_component_type text,
            p_schema_version text,p_parent_id uuid,p_slot_key text,p_old_props jsonb,
            p_new_props jsonb,p_allow_design boolean
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE key text; value jsonb; leaf jsonb; authority text; scope text;
            collapsed jsonb; candidate jsonb; fallback jsonb;
        BEGIN
            IF p_new_props IS NULL OR jsonb_typeof(p_new_props)<>'object'
            THEN RAISE EXCEPTION 'COMPONENT_PROPS_INVALID' USING ERRCODE='P0003'; END IF;
            collapsed:=p_new_props-'alignment';
            FOR key,value IN SELECT entry.key,entry.value FROM jsonb_each(p_new_props) entry LOOP
                scope:=control.slaif_agent_component_design_scope(p_component_type,key);
                SELECT entry->'props'->key->>'authority' INTO authority
                FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                IF scope IS NULL AND authority='design'
                   AND (p_old_props->key) IS DISTINCT FROM value
                THEN
                    RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED' USING ERRCODE='P0003';
                END IF;
                IF key='alignment' AND scope IS NOT NULL THEN
                    IF jsonb_typeof(value)='object' THEN
                        IF (SELECT count(*) FROM jsonb_object_keys(value))=0
                           OR EXISTS (
                               SELECT 1 FROM jsonb_object_keys(value) label
                               WHERE label NOT IN ('desktop','tablet','mobile')
                           )
                        THEN
                            RAISE EXCEPTION 'COMPONENT_PROP_ENUM' USING ERRCODE='P0003';
                        END IF;
                        FOR leaf IN SELECT entry.value FROM jsonb_each(value) entry LOOP
                            IF leaf #>> '{}' NOT IN ('start','center','end','stretch')
                            THEN RAISE EXCEPTION 'COMPONENT_PROP_ENUM' USING ERRCODE='P0003'; END IF;
                        END LOOP;
                    ELSIF value #>> '{}' NOT IN ('start','center','end','stretch')
                    THEN RAISE EXCEPTION 'COMPONENT_PROP_ENUM' USING ERRCODE='P0003'; END IF;
                END IF;
                IF scope IS NOT NULL AND jsonb_typeof(value)='object'
                   AND (SELECT count(*) FROM jsonb_object_keys(value))>0
                   AND NOT EXISTS (
                       SELECT 1 FROM jsonb_object_keys(value) label
                       WHERE label NOT IN ('desktop','tablet','mobile')
                   )
                THEN
                    fallback:=coalesce(value->'desktop',value->'tablet',value->'mobile');
                    IF key<>'alignment' THEN
                        collapsed:=jsonb_set(collapsed,ARRAY[key],fallback,true);
                    END IF;
                END IF;
            END LOOP;
            PERFORM content.slaif_agent_component_validate(
                p_site_id,p_page_id,p_node_id,p_component_type,p_schema_version,
                p_parent_id,p_slot_key,collapsed,p_allow_design);
            FOR key,value IN SELECT entry.key,entry.value FROM jsonb_each(p_new_props) entry LOOP
                scope:=control.slaif_agent_component_design_scope(p_component_type,key);
                IF scope IS NOT NULL AND key<>'alignment'
                   AND jsonb_typeof(value)='object'
                   AND (SELECT count(*) FROM jsonb_object_keys(value))>0
                   AND NOT EXISTS (
                       SELECT 1 FROM jsonb_object_keys(value) label
                       WHERE label NOT IN ('desktop','tablet','mobile')
                   )
                THEN
                    FOR leaf IN SELECT entry.value FROM jsonb_each(value) entry LOOP
                        candidate:=collapsed;
                        candidate:=jsonb_set(candidate,ARRAY[key],leaf,true);
                        PERFORM content.slaif_agent_component_validate(
                            p_site_id,p_page_id,p_node_id,p_component_type,p_schema_version,
                            p_parent_id,p_slot_key,candidate,p_allow_design);
                    END LOOP;
                END IF;
            END LOOP;
        END;
        $fn$;

        CREATE FUNCTION content.slaif_agent_component_tree_validate_design(
            p_site_id uuid,p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE node record; positions integer[]; expected integer[];
        BEGIN
            FOR node IN SELECT * FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
            LOOP
                PERFORM content.slaif_agent_component_validate_design(
                    p_site_id,p_page_id,node.id,node.component_type,node.schema_version,
                    node.parent_id,node.slot_key,node.props,node.props,true);
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

        CREATE OR REPLACE FUNCTION content.slaif_agent_component_tree_validate(
            p_site_id uuid,p_page_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE node record; positions integer[]; expected integer[];
        BEGIN
            FOR node IN SELECT * FROM content.page_composition c
                WHERE c.site_id=p_site_id AND c.page_id=p_page_id
            LOOP
                PERFORM content.slaif_agent_component_validate_design(
                    p_site_id,p_page_id,node.id,node.component_type,node.schema_version,
                    node.parent_id,node.slot_key,node.props,node.props,true);
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
            capability_id:=control.slaif_agent_component_authorize_update(
                p_site_id,old.component_type,old.props,p_props);
            PERFORM content.slaif_agent_component_validate_design(
                p_site_id,old.page_id,old.id,old.component_type,old.schema_version,
                old.parent_id,old.slot_key,old.props,p_props,true);
            IF NOT control.slaif_agent_quota_consume(capability_id,workspace_id,'mutation') THEN
                RAISE EXCEPTION 'AGENT_MUTATION_QUOTA_EXCEEDED' USING ERRCODE='P0005';
            END IF;
            UPDATE content.page_composition c SET props=p_props,row_version=c.row_version+1,
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


def _restore_component_update_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_agent_component_update(
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
                FROM jsonb_object_keys(coalesce(old.props,'{}'::jsonb)||coalesce(p_props,'{}'::jsonb)) key
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
    """


def _restore_tree_validator_sql() -> str:
    return """
        CREATE OR REPLACE FUNCTION content.slaif_agent_component_tree_validate(
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
    """


def upgrade() -> None:
    _execute_block(_authority_sql())
    _execute_block(_design_validator_sql())
    _execute_block(_component_update_sql())
    for function in (
        _DESIGN_SCOPE_FUNCTION,
        _AUTHORIZE_FUNCTION,
        _VALIDATE_FUNCTION,
        _TREE_VALIDATE_FUNCTION,
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")


def downgrade() -> None:
    op.execute(f"DROP FUNCTION IF EXISTS {_TREE_VALIDATE_FUNCTION}")
    _execute_block(_restore_tree_validator_sql())
    op.execute(f"DROP FUNCTION IF EXISTS {_VALIDATE_FUNCTION}")
    _execute_block(_restore_component_update_sql())
    op.execute(f"DROP FUNCTION IF EXISTS {_AUTHORIZE_FUNCTION}")
    op.execute(f"DROP FUNCTION IF EXISTS {_DESIGN_SCOPE_FUNCTION}")

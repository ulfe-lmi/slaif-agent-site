# ruff: noqa: E501
"""Close final component validation, responsive CREATE, and Editor findings."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any, cast

from alembic import op

revision: str = "063_001"
down_revision: str | Sequence[str] | None = "062_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_M060: Any = import_module(
    "slaif_agent_site.db.alembic.versions.060_001_agent_component_semantics"
)
_M061: Any = import_module(
    "slaif_agent_site.db.alembic.versions.061_001_agent_component_design_semantics"
)
_M062: Any = import_module(
    "slaif_agent_site.db.alembic.versions.062_001_component_authority_repairs"
)

_DESIGN_VALIDATE = (
    "content.slaif_agent_component_validate_design("
    "uuid,uuid,uuid,text,text,uuid,text,jsonb,jsonb,boolean)"
)
_TREE_DESIGN_VALIDATE = "content.slaif_agent_component_tree_validate_design(uuid,uuid)"
_COMPONENT_CREATE = (
    "content.slaif_agent_component_create(uuid,uuid,text,uuid,text,uuid,uuid,jsonb)"
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


def _design_validator_sql() -> str:
    sql = cast(str, _M061._design_validator_sql())
    sql = sql.replace(
        "CREATE FUNCTION content.slaif_agent_component_validate_design(",
        "CREATE OR REPLACE FUNCTION content.slaif_agent_component_validate_design(",
    ).replace(
        "CREATE FUNCTION content.slaif_agent_component_tree_validate_design(",
        "CREATE OR REPLACE FUNCTION content.slaif_agent_component_tree_validate_design(",
    )
    old = """                scope:=control.slaif_agent_component_design_scope(p_component_type,key);
                SELECT entry->'props'->key->>'authority' INTO authority
                FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                IF scope IS NULL AND authority='design'
                   AND (p_old_props->key) IS DISTINCT FROM value
                THEN
                    RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED' USING ERRCODE='P0003';
                END IF;
                IF key='alignment' AND scope IS NOT NULL THEN
"""
    new = """                scope:=control.slaif_agent_component_design_scope(p_component_type,key);
                SELECT entry->'props'->key->>'authority' INTO authority
                FROM control.component_catalog c,jsonb_array_elements(c.definitions) entry
                WHERE c.version='catalog-v1' AND entry->>'type'=p_component_type;
                IF jsonb_typeof(value)='null'
                   OR content.slaif_component_reject_nested(value)
                THEN
                    RAISE EXCEPTION 'COMPONENT_PROPS_UNSAFE' USING ERRCODE='P0003';
                END IF;
                IF scope IS NULL AND authority IS NULL THEN
                    RAISE EXCEPTION 'COMPONENT_PROP_UNKNOWN' USING ERRCODE='P0003';
                END IF;
                IF scope IS NULL AND authority='design'
                   AND (p_old_props->key) IS DISTINCT FROM value
                THEN
                    RAISE EXCEPTION 'COMPONENT_DESIGN_PROP_UNSUPPORTED' USING ERRCODE='P0003';
                END IF;
                IF scope IS NOT NULL AND key IN ('count','columns') THEN
                    IF jsonb_typeof(value)='number'
                       AND (value #>> '{}')::numeric<>trunc((value #>> '{}')::numeric)
                    THEN
                        RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                    ELSIF jsonb_typeof(value)='object' THEN
                        FOR leaf IN SELECT entry.value FROM jsonb_each(value) entry LOOP
                            IF jsonb_typeof(leaf)='number'
                               AND (leaf #>> '{}')::numeric<>trunc((leaf #>> '{}')::numeric)
                            THEN
                                RAISE EXCEPTION 'COMPONENT_PROP_TYPE' USING ERRCODE='P0003';
                            END IF;
                        END LOOP;
                    END IF;
                END IF;
                IF key='alignment' AND scope IS NOT NULL THEN
"""
    if old not in sql:
        raise RuntimeError("063 design validator anchor drift")
    sql = sql.replace(old, new, 1)
    sql = sql.replace(
        "IF leaf #>> '{}' NOT IN ('start','center','end','stretch')",
        "IF jsonb_typeof(leaf)<>'string' OR leaf #>> '{}' NOT IN ('start','center','end','stretch')",
    )
    sql = sql.replace(
        "ELSIF value #>> '{}' NOT IN ('start','center','end','stretch')",
        "ELSIF jsonb_typeof(value)<>'string' OR value #>> '{}' NOT IN ('start','center','end','stretch')",
    )
    return sql


def _component_create_sql() -> str:
    sql = cast(str, _M062._component_create_sql())
    old = """            PERFORM content.slaif_agent_component_validate(
                p_site_id,p_page_id,NULL,p_component_type,'1',p_parent_id,
                p_slot_key,normalized_props,true);
"""
    new = """            PERFORM content.slaif_agent_component_validate_design(
                p_site_id,p_page_id,NULL,p_component_type,'1',p_parent_id,
                p_slot_key,'{}'::jsonb,normalized_props,true);
"""
    if old not in sql:
        raise RuntimeError("063 component CREATE validator anchor drift")
    return sql.replace(old, new, 1)


def _legacy_composition_sql() -> str:
    sql = cast(str, _M060._legacy_composition_sql())
    replacements = {
        """            PERFORM content.slaif_agent_component_validate(
                p_site_id,p_page_id,NULL,p_component_type,'1',p_parent_id,p_slot_key,p_props,true);""": """            PERFORM content.slaif_agent_component_validate_design(
                p_site_id,p_page_id,NULL,p_component_type,'1',p_parent_id,p_slot_key,
                '{}'::jsonb,p_props,true);""",
        """            PERFORM content.slaif_agent_component_validate(old.site_id,old.page_id,old.id,
                old.component_type,old.schema_version,old.parent_id,coalesce(p_slot_key,old.slot_key),merged,true);""": """            PERFORM content.slaif_agent_component_validate_design(
                old.site_id,old.page_id,old.id,old.component_type,old.schema_version,
                old.parent_id,coalesce(p_slot_key,old.slot_key),old.props,merged,true);""",
        """            PERFORM content.slaif_agent_component_validate(old.site_id,old.page_id,old.id,
                old.component_type,old.schema_version,p_new_parent_id,coalesce(p_new_slot_key,old.slot_key),old.props,true);""": """            PERFORM content.slaif_agent_component_validate_design(
                old.site_id,old.page_id,old.id,old.component_type,old.schema_version,
                p_new_parent_id,coalesce(p_new_slot_key,old.slot_key),old.props,old.props,true);""",
    }
    for old, new in replacements.items():
        if old not in sql:
            raise RuntimeError("063 Editor composition validator anchor drift")
        sql = sql.replace(old, new, 1)
    return sql


def upgrade() -> None:
    _execute_block(_design_validator_sql())
    _execute_block(_component_create_sql())
    _execute_block(_legacy_composition_sql())
    for function in (_DESIGN_VALIDATE, _TREE_DESIGN_VALIDATE, _COMPONENT_CREATE):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_COMPONENT_CREATE} TO slaif_agent_runtime")


def downgrade() -> None:
    # Restore the prior validator and component wrappers from immutable sources.
    old_validator = (
        _M061._design_validator_sql()
        .replace(
            "CREATE FUNCTION content.slaif_agent_component_validate_design(",
            "CREATE OR REPLACE FUNCTION content.slaif_agent_component_validate_design(",
        )
        .replace(
            "CREATE FUNCTION content.slaif_agent_component_tree_validate_design(",
            "CREATE OR REPLACE FUNCTION content.slaif_agent_component_tree_validate_design(",
        )
    )
    _execute_block(old_validator)
    _execute_block(_M062._component_update_sql())
    _execute_block(_M062._component_create_sql())
    _execute_block(_M060._legacy_composition_sql())
    for function in (_DESIGN_VALIDATE, _TREE_DESIGN_VALIDATE, _COMPONENT_CREATE):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_COMPONENT_CREATE} TO slaif_agent_runtime")

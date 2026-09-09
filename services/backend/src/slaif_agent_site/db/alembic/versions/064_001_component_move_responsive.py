# ruff: noqa: E501
"""Allow the Agent component MOVE path to preserve responsive design props."""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any, cast

from alembic import op

revision: str = "064_001"
down_revision: str | Sequence[str] | None = "063_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_M060: Any = import_module(
    "slaif_agent_site.db.alembic.versions.060_001_agent_component_semantics"
)
_MOVE_FUNCTION = (
    "content.slaif_agent_component_move(uuid,uuid,uuid,text,uuid,uuid,integer)"
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


def _move_sql(*, responsive: bool) -> str:
    source = cast(str, _M060._agent_component_sql())
    start = source.index("        CREATE FUNCTION content.slaif_agent_component_move(")
    end = source.index("        $fn$;", start) + len("        $fn$;")
    sql = source[start:end].replace(
        "CREATE FUNCTION content.slaif_agent_component_move(",
        "CREATE OR REPLACE FUNCTION content.slaif_agent_component_move(",
        1,
    )
    scalar = """            PERFORM content.slaif_agent_component_validate(
                p_site_id,old.page_id,old.id,old.component_type,old.schema_version,
                p_parent_id,p_slot_key,old.props,true);"""
    design = """            PERFORM content.slaif_agent_component_validate_design(
                p_site_id,old.page_id,old.id,old.component_type,old.schema_version,
                p_parent_id,p_slot_key,old.props,old.props,true);"""
    expected = design if responsive else scalar
    if scalar not in sql:
        raise RuntimeError("064 component MOVE validator anchor drift")
    return sql.replace(scalar, expected, 1)


def upgrade() -> None:
    _execute_block(_move_sql(responsive=True))
    op.execute(f"ALTER FUNCTION {_MOVE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_MOVE_FUNCTION} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_MOVE_FUNCTION} TO slaif_agent_runtime")


def downgrade() -> None:
    op.execute(
        """
        DO $guard$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM content.page_composition c
                CROSS JOIN LATERAL jsonb_each(c.props) property
                WHERE property.key = 'alignment'
                   OR (
                       jsonb_typeof(property.value) = 'object'
                       AND (
                           property.value ? 'desktop'
                           OR property.value ? 'tablet'
                           OR property.value ? 'mobile'
                       )
                   )
            ) THEN
                RAISE EXCEPTION '064_DOWNGRADE_RESPONSIVE_COMPONENT_STATE'
                    USING ERRCODE = 'P0003';
            END IF;
        END
        $guard$;
        """
    )
    _execute_block(_move_sql(responsive=False))
    op.execute(f"ALTER FUNCTION {_MOVE_FUNCTION} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_MOVE_FUNCTION} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_MOVE_FUNCTION} TO slaif_agent_runtime")

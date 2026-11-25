# ruff: noqa: E501
"""Bounded heading-props row-effect pilot (083-13-a).

A successful changed heading-props write through either trusted editorial
boundary (the 062 Agent component update definer or the 060 Editor
composition node update definer) leaves exactly one durable product-owned
row effect in ``audit.heading_row_effect`` in the SAME transaction as the
COW write, the family audit row and the idempotency completion:

- server operation id (global primary key: the same operation cannot
  record twice; replays never reach a definer because the stored body is
  returned before completion, and a rolled-back request leaves no row);
- the actual mutation family: ``agent`` (bound to the agent capability)
  or ``human_editor`` (HUMAN-on-AGENT editing; the human principal is
  resolved from the actual in-progress reservation row, never from
  caller-supplied values);
- site, workspace, component id and the exact DML image pair:
  ``row_version_before`` / ``row_version_after`` (always ``+1``) and
  ``props_before`` / ``props_after`` (both bounded by the existing
  composition 16384-octet props ceiling);
- ``schema_version`` ``heading-row-effect/v1`` and a trusted
  ``occurred_at``.

The images are captured by the DEFINER itself, inside one statement: a
``prior`` CTE (a simple SELECT, fully read before the data-modifying
``post`` CTE executes per the documented WITH execution order) holds the
pre-write image and the ``post`` CTE performs the byte-identical original
write with ``RETURNING``.  A later re-read of the row is NOT the
pre-write image (under READ COMMITTED a concurrent committed change can
land between statements); this capture is what makes the recorded before
image exact.  Non-heading component types keep the pre-080 write
byte-for-byte (explicit pilot boundary: the pilot observes and records,
it does not harden the Editor version contract or change any other
mutation family).

The record helper is owner-only (no PUBLIC, no role EXECUTE).  Inside the
real mutation transaction it:

- validates the input shape (family/principal pairing, version shape,
  object-typed bounded props, workspace belongs to the site);
- requires the server COW context GUCs (app.session_id /
  app.operation_id, set by the trusted session for the whole COW
  transaction) to name exactly this workspace and operation, so a record
  outside its own COW session context is refused before any effect;
- verifies the claimed after image against the CURRENT session view of
  the row (Heading type, exact row_version and props), i.e. the fact is
  generated from the definer's own checked COW write;
- binds the claimed identity to the ACTUAL in-progress reservation row
  of the correct family ledger (status_code IS NULL: completion happens
  later in the same transaction) with the human principal resolved FROM
  that row;
- takes the transaction-scoped advisory lock on the operation id (same
  key as the 078 completion journal, so both locks compose);
- inserts the fact; the primary key is the final transactional guard.

Downgrade is an explicit fail-closed refusal (no conditional path):
rolling back below 080 would restore the unrecording definer bodies while
080-era row effects persist, leaving the provenance state ambiguous.  The
bootstrap operator path refuses the rollback before any operator effect;
this migration's own downgrade body is the second line of defense.  This
revision adds no COW teardown, no HTTP API, no new grant surface beyond
the two re-secured writer definers and no foundation change; the
re-emitted bodies keep every existing validation, the existing ownership
and the exact existing EXECUTE grant surface.
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any

from alembic import op

revision: str = "080_001"
down_revision: str | Sequence[str] | None = "079_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_M060: Any = import_module(
    "slaif_agent_site.db.alembic.versions.060_001_agent_component_semantics"
)
_M062: Any = import_module(
    "slaif_agent_site.db.alembic.versions.062_001_component_authority_repairs"
)

_FACTS_TABLE = "audit.heading_row_effect"
_RECORDER = "control.slaif_heading_row_effect_record"
_AGENT_UPDATE = "content.slaif_agent_component_update(uuid,uuid,jsonb,integer)"
_EDITOR_UPDATE = "content.slaif_composition_node_update(uuid,jsonb,text,integer)"
_ROLES_WITHOUT_FACTS_ACCESS = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_reviewer",
    "slaif_review_worker",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)

_FACTS_TABLE_SQL = """
        CREATE TABLE audit.heading_row_effect (
            operation_id uuid PRIMARY KEY,
            schema_version text NOT NULL DEFAULT 'heading-row-effect/v1',
            family text NOT NULL CHECK (family IN ('agent','human_editor')),
            mutation_kind text NOT NULL DEFAULT 'heading_props'
                CHECK (mutation_kind = 'heading_props'),
            site_id uuid NOT NULL,
            workspace_id uuid NOT NULL,
            component_id uuid NOT NULL,
            row_version_before integer NOT NULL,
            row_version_after integer NOT NULL,
            props_before jsonb NOT NULL,
            props_after jsonb NOT NULL,
            capability_id uuid REFERENCES control.capability(id),
            human_user_id uuid REFERENCES control.user_account(id),
            occurred_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT heading_row_effect_schema_version CHECK (
                schema_version = 'heading-row-effect/v1'
            ),
            CONSTRAINT heading_row_effect_version_shape CHECK (
                row_version_before > 0 AND row_version_after = row_version_before + 1
            ),
            CONSTRAINT heading_row_effect_principal CHECK (
                (family = 'agent' AND capability_id IS NOT NULL
                    AND human_user_id IS NULL)
                OR (family = 'human_editor' AND capability_id IS NULL
                    AND human_user_id IS NOT NULL)
            ),
            CONSTRAINT heading_row_effect_props_before_shape CHECK (
                jsonb_typeof(props_before) = 'object'
                AND octet_length(props_before::text) <= 16384
            ),
            CONSTRAINT heading_row_effect_props_after_shape CHECK (
                jsonb_typeof(props_after) = 'object'
                AND octet_length(props_after::text) <= 16384
            )
        )
"""

_RECORDER_SQL = f"""
        CREATE FUNCTION {_RECORDER}(
            p_operation_id uuid, p_family text, p_site_id uuid,
            p_workspace_id uuid, p_agent_capability_id uuid, p_component_id uuid,
            p_row_version_before integer, p_row_version_after integer,
            p_props_before jsonb, p_props_after jsonb
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE human_user_id uuid;
        BEGIN
            IF p_operation_id IS NULL OR p_site_id IS NULL
               OR p_workspace_id IS NULL OR p_component_id IS NULL
               OR p_row_version_before IS NULL OR p_row_version_after IS NULL
               OR p_row_version_before <= 0
               OR p_row_version_after <> p_row_version_before + 1
               OR p_props_before IS NULL OR jsonb_typeof(p_props_before) <> 'object'
               OR p_props_after IS NULL OR jsonb_typeof(p_props_after) <> 'object'
               OR p_family NOT IN ('agent','human_editor')
               OR (p_family = 'agent' AND p_agent_capability_id IS NULL)
               OR (p_family = 'human_editor' AND p_agent_capability_id IS NOT NULL)
               OR NOT EXISTS (SELECT 1 FROM control.workspace AS w
                              WHERE w.id = p_workspace_id
                                AND w.site_id = p_site_id)
            THEN RAISE EXCEPTION 'HEADING_EFFECT_INPUT'
                USING ERRCODE = 'P0001';
            END IF;
            IF NULLIF(current_setting('app.session_id', true), '')
                   IS DISTINCT FROM p_workspace_id::text
               OR NULLIF(current_setting('app.operation_id', true), '')
                   IS DISTINCT FROM p_operation_id::text
            THEN RAISE EXCEPTION 'HEADING_EFFECT_CONTEXT_MISMATCH'
                USING ERRCODE = 'P0001';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.page_composition AS c
                WHERE c.id = p_component_id
                  AND c.component_type = 'Heading'
                  AND c.row_version = p_row_version_after
                  AND c.props IS NOT DISTINCT FROM p_props_after
            ) THEN RAISE EXCEPTION 'HEADING_EFFECT_IMAGE_MISMATCH'
                USING ERRCODE = 'P0001';
            END IF;
            IF p_family = 'agent' THEN
                IF NOT EXISTS (
                    SELECT 1 FROM control.agent_idempotency AS r
                    WHERE r.operation_id = p_operation_id
                      AND r.capability_id = p_agent_capability_id
                      AND r.workspace_id = p_workspace_id
                      AND r.status_code IS NULL
                ) THEN RAISE EXCEPTION 'HEADING_EFFECT_RESERVATION_MISMATCH'
                    USING ERRCODE = 'P0001';
                END IF;
            ELSE
                SELECT r.human_user_id INTO human_user_id
                FROM control.human_editor_idempotency AS r
                WHERE r.operation_id = p_operation_id
                  AND r.workspace_id = p_workspace_id
                  AND r.site_id = p_site_id
                  AND r.status_code IS NULL;
                IF NOT FOUND THEN RAISE EXCEPTION
                    'HEADING_EFFECT_RESERVATION_MISMATCH'
                    USING ERRCODE = 'P0001';
                END IF;
            END IF;
            PERFORM pg_advisory_xact_lock(
                hashtextextended(p_operation_id::text, 280));
            INSERT INTO audit.heading_row_effect(
                operation_id, family, site_id, workspace_id, component_id,
                row_version_before, row_version_after, props_before,
                props_after, capability_id, human_user_id
            ) VALUES (
                p_operation_id, p_family, p_site_id, p_workspace_id,
                p_component_id, p_row_version_before, p_row_version_after,
                p_props_before, p_props_after, p_agent_capability_id,
                human_user_id
            );
        END;
        $fn$
"""

_IMAGE_DECLARE = (
    "            props_before jsonb; props_after jsonb;\n"
    "            rv_before integer; rv_after integer;\n"
)

_AGENT_DECLARE_ANCHOR = (
    "        DECLARE old record; workspace_id uuid; capability_id uuid;\n"
    "            new_props jsonb; key text;\n"
)
_AGENT_WRITE_ANCHOR = (
    "            UPDATE content.page_composition c"
    " SET props=new_props,row_version=c.row_version+1,\n"
    "                updated_at=now()"
    " WHERE c.id=p_component_id AND c.site_id=p_site_id\n"
    "                AND c.row_version=p_expected;\n"
    "            IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH'"
    " USING ERRCODE='P0004'; END IF;\n"
)
_AGENT_WRITE_REPLACEMENT = """\
            IF old.component_type = 'Heading' THEN
                -- 083-13-a pilot: capture the same-statement DML image of
                -- the actual heading write, then record it trusted.  The
                -- prior CTE (a simple SELECT) is fully read before the
                -- data-modifying post CTE executes; FROM prior preserves
                -- the original write byte-for-byte.  Non-heading types
                -- keep the pre-080 write unchanged.
                WITH prior AS (
                    SELECT c.id,c.props,c.row_version
                    FROM content.page_composition c
                    WHERE c.id=p_component_id AND c.site_id=p_site_id
                ), post AS (
                    UPDATE content.page_composition c SET props=new_props,
                        row_version=c.row_version+1,updated_at=now()
                    FROM prior
                    WHERE c.id=p_component_id AND c.site_id=p_site_id
                        AND c.row_version=p_expected
                    RETURNING c.props,c.row_version
                )
                SELECT prior.props,prior.row_version,
                       post.props,post.row_version
                INTO props_before,rv_before,props_after,rv_after
                FROM prior CROSS JOIN post;
                IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH'
                    USING ERRCODE='P0004'; END IF;
                PERFORM control.slaif_heading_row_effect_record(
                    NULLIF(current_setting('app.operation_id',true),'')::uuid,
                    'agent',p_site_id,workspace_id,capability_id,
                    p_component_id, rv_before,rv_after,
                    props_before,props_after);
            ELSE
                UPDATE content.page_composition c SET props=new_props,row_version=c.row_version+1,
                    updated_at=now() WHERE c.id=p_component_id AND c.site_id=p_site_id
                    AND c.row_version=p_expected;
                IF NOT FOUND THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF;
            END IF;
"""

_EDITOR_UPDATE_MARKER = (
    "CREATE OR REPLACE FUNCTION content.slaif_composition_node_update("
)
_EDITOR_UPDATE_END = "END; $fn$;"
_EDITOR_DECLARE_ANCHOR = "        DECLARE old record; merged jsonb;\n"
_EDITOR_WRITE_ANCHOR = (
    "            UPDATE content.page_composition AS composition\n"
    "            SET props=merged,"
    "slot_key=coalesce(p_slot_key,composition.slot_key),\n"
    "                order_key=coalesce(p_order_key,composition.order_key),\n"
    "                row_version=composition.row_version+1,updated_at=now()\n"
    "            WHERE composition.id=p_node_id;\n"
)
_EDITOR_WRITE_REPLACEMENT = """\
            IF old.component_type = 'Heading' THEN
                -- 083-13-a pilot: capture the same-statement DML image of
                -- the actual heading write, then record it trusted.  The
                -- prior CTE (a simple SELECT) is fully read before the
                -- data-modifying post CTE executes.  The write keeps the
                -- pre-080 Editor contract byte-for-byte (no version
                -- predicate, no site filter): the pilot observes and
                -- records; it does not harden the Editor boundary.
                WITH prior AS (
                    SELECT c.id,c.props,c.row_version
                    FROM content.page_composition c
                    WHERE c.id=p_node_id
                ), post AS (
                    UPDATE content.page_composition AS composition
                    SET props=merged,slot_key=coalesce(p_slot_key,composition.slot_key),
                        order_key=coalesce(p_order_key,composition.order_key),
                        row_version=composition.row_version+1,updated_at=now()
                    FROM prior
                    WHERE composition.id=p_node_id
                    RETURNING composition.props,composition.row_version
                )
                SELECT prior.props,prior.row_version,
                       post.props,post.row_version
                INTO props_before,rv_before,props_after,rv_after
                FROM prior CROSS JOIN post;
                IF NOT FOUND THEN RAISE EXCEPTION
                    'HEADING_EFFECT_IMAGE_MISSING'
                    USING ERRCODE='P0001'; END IF;
                PERFORM control.slaif_heading_row_effect_record(
                    NULLIF(current_setting('app.operation_id',true),'')::uuid,
                    'human_editor',old.site_id,
                    NULLIF(current_setting('app.session_id',true),'')::uuid,
                    NULL,p_node_id, rv_before,rv_after,
                    props_before,props_after);
            ELSE
                UPDATE content.page_composition AS composition
                SET props=merged,slot_key=coalesce(p_slot_key,composition.slot_key),
                    order_key=coalesce(p_order_key,composition.order_key),
                    row_version=composition.row_version+1,updated_at=now()
                WHERE composition.id=p_node_id;
            END IF;
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


def _replace_once(body: str, anchor: str, replacement: str, what: str) -> str:
    count = body.count(anchor)
    if count != 1:
        raise RuntimeError(
            f"080_001: {what} anchor not found exactly once (count={count})"
        )
    return body.replace(anchor, replacement, 1)


def _agent_update_body() -> str:
    body = str(_M062._component_update_sql())
    if (
        body.count("CREATE OR REPLACE FUNCTION content.slaif_agent_component_update(")
        != 1
    ):
        raise RuntimeError("080_001: agent component_update body missing in 062_001")
    body = _replace_once(
        body,
        _AGENT_DECLARE_ANCHOR,
        _AGENT_DECLARE_ANCHOR + _IMAGE_DECLARE,
        "agent DECLARE",
    )
    body = _replace_once(
        body, _AGENT_WRITE_ANCHOR, _AGENT_WRITE_REPLACEMENT, "agent write"
    )
    return body


def _editor_update_body() -> str:
    block = str(_M060._legacy_composition_sql())
    count = block.count(_EDITOR_UPDATE_MARKER)
    if count != 1:
        raise RuntimeError(
            f"080_001: editor node_update marker count={count} in 060_001"
        )
    idx = block.index(_EDITOR_UPDATE_MARKER)
    end = block.find(_EDITOR_UPDATE_END, idx)
    if end == -1:
        raise RuntimeError("080_001: editor node_update terminator missing")
    body = block[idx : end + len(_EDITOR_UPDATE_END)]
    body = _replace_once(
        body,
        _EDITOR_DECLARE_ANCHOR,
        _EDITOR_DECLARE_ANCHOR + _IMAGE_DECLARE,
        "editor DECLARE",
    )
    body = _replace_once(
        body, _EDITOR_WRITE_ANCHOR, _EDITOR_WRITE_REPLACEMENT, "editor write"
    )
    return body


def _secure_function(qualified: str, roles: tuple[str, ...]) -> None:
    op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")
    for role in roles:
        op.execute(f"GRANT EXECUTE ON FUNCTION {qualified} TO {role}")


def upgrade() -> None:
    op.execute(_FACTS_TABLE_SQL)
    op.execute(f"ALTER TABLE {_FACTS_TABLE} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON TABLE {_FACTS_TABLE} FROM PUBLIC")
    for role in _ROLES_WITHOUT_FACTS_ACCESS:
        op.execute(f"REVOKE ALL ON TABLE {_FACTS_TABLE} FROM {role}")

    op.execute(_RECORDER_SQL)
    op.execute(f"ALTER FUNCTION {_RECORDER} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_RECORDER} FROM PUBLIC")
    for role in _ROLES_WITHOUT_FACTS_ACCESS:
        op.execute(f"REVOKE ALL ON FUNCTION {_RECORDER} FROM {role}")

    # Agent 062 update definer: the currently deployed 062_001 body with
    # the bounded Heading same-statement capture and trusted record.
    _execute_block(_agent_update_body())
    _secure_function(_AGENT_UPDATE, ("slaif_agent_runtime",))

    # Editor 060 update definer: the currently deployed 060_001 body with
    # the bounded Heading same-statement capture and trusted record.
    _execute_block(_editor_update_body())
    _secure_function(_EDITOR_UPDATE, ("slaif_editor_runtime", "slaif_control"))


def downgrade() -> None:
    # Explicit fail-closed refusal (no conditional path): restoring the
    # unrecording definer bodies would leave the 080-era row-effect
    # history uninterpretable against them, and no supported path can
    # re-derive which historical heading writes were recorded.  The
    # refusal raises before any restoration and touches no canonical,
    # pending, audit, idempotency or snapshot state.  The bootstrap
    # operator path refuses this rollback earlier still (before the
    # readiness PENDING marker and the content COW disable); this body
    # is the defense for direct migration invocations.
    op.execute(
        """
        DO $guard$
        BEGIN
            RAISE EXCEPTION
                'HEADING_ROW_EFFECT_DOWNGRADE_UNSUPPORTED'
                USING ERRCODE = 'P0001';
        END $guard$;
        """
    )

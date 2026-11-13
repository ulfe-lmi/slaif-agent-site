# ruff: noqa: E501
"""Trusted mutation completion provenance across the three audit families.

Each newly completed editorial mutation leaves exactly one durable trusted
completion identity in ``audit.mutation_completion`` in the SAME transaction
as its COW mutation, family audit row and idempotency completion:

- operation id (a GLOBAL primary key: the same operation cannot complete
  again under another family or identity, and no uniqueness constraint is
  placed on the resource identity - the same resource may lawfully have
  many operations and families);
- family, exactly ``agent`` / ``human_editor`` / ``media`` (HUMAN-on-AGENT
  editing is the ``human_editor`` family, not a fourth family);
- site, workspace and the ACTUAL principal (the agent capability or the
  human user bound to the completed reservation);
- bounded request identity: an opaque SHA-256 reference to the raw
  client-supplied idempotency key plus the existing 64-hex request digest.
  The raw key is arbitrary client header content and is NEVER persisted in
  the journal; the exact raw-key reservation match stays internal to the
  idempotency ledgers and the helper call;
- primary resource type/id and an honest ``disposition``:
  ``'completed'`` (a normal completion may legitimately have zero COW rows,
  for example ordinary media dedupe returning an existing asset) or
  ``'no_effect'`` (the agent's EXPLICIT no-effect completion decision, which
  updates the idempotency row without a mutation audit row).

Covered completion producers (all actual latest deployed definitions):

- agent 13-argument semantic completion: the 068_001 cumulative body
  (``068_001._semantic_completion_sql()``, which wraps the 067_001
  ``include_region=True`` body and adds the accepted MEDIA_UPLOADED/media
  asset/POST/201/upload row);
- agent 10-argument legacy completion: the 047_001 body, still deployed;
- agent 10-argument explicit no-effect completion: the 067_001
  ``include_region=True`` body;
- HUMAN editor completion for HUMAN workspaces: the 028_001 body;
- HUMAN editor completion for AGENT workspaces: the 069_001 body;
- human media upload completion: the 030_001 body.

Every body is re-emitted to the currently deployed definition (the literal
bodies are read from the sibling version sources at migration time and a
drift failure aborts the migration; the 028/069/030 bodies get exactly one
deterministic ``CREATE`` to ``CREATE OR REPLACE`` edit) plus ONE appended
``PERFORM control.slaif_mutation_completion_record(...)`` placed after the
complete success work and before the outer ``END``.  Each keeps its exact
validation, reservation guard, family audit insert, idempotency update,
ownership, REVOKE FROM PUBLIC and role grants.  Replays never reach a
completion definer (the stored body is returned before completion) and
therefore create no new completion; failed or rolled-back requests leave no
row because the journal insert shares the mutation transaction.

The helper is owner-only (no PUBLIC, no role EXECUTE).  Inside the real
mutation transaction it:

- validates the input shape and that the workspace belongs to the site;
- takes a transaction-scoped advisory lock on the operation id;
- requires the server COW context GUCs (app.session_id / app.operation_id,
  set by the trusted session for the whole COW transaction) to name exactly
  this workspace and operation, so a completion outside its own COW session
  context is refused before any journal effect (the GUCs are context
  binding, not credentials: the principal and reservation guards below
  remain authoritative);
- binds the claimed identity to the ACTUAL completed reservation row of the
  correct family ledger (operation, principal, workspace/site, raw key and
  digest, status_code NOT NULL) so a wrong principal or context cannot be
  journaled;
- rejects conflicting committed historical identity (any of the three
  pre-078 family audit tables under a different family or principal);
- rejects a previously COMPLETED reservation of the same operation id in
  ANY of the three family idempotency ledgers (this catches explicit
  pre-078 agent no-effect completions, which have a completed ledger row
  but no audit row), excluding only the exact current row;
- inserts the identity row; the primary key is the final transactional
  guard.

Prospective coverage: this revision records completions from the 078 head
forward.  Historical completions (and their unknown no-effect decisions)
are NOT backfilled: old missing provenance is unknown, not proof of no
effect or corruption, and no synthetic rows are invented.  Freeze/accept
eligibility is unchanged by this revision.

Downgrade is an explicit fail-closed refusal (no conditional path):
rolling back below 078 would restore the unrecorded completion bodies
while the journal history of 078-era completions persists, leaving the
provenance state ambiguous.  The bootstrap operator path refuses the
rollback before the readiness PENDING marker is committed and before the
content COW disable; this migration's own downgrade body is the second
line of defense for direct migration invocations.  The refusal raises
before any restoration and touches no canonical, pending, audit,
idempotency or snapshot state.  This revision adds no COW teardown, no
snapshot-format change, no new HTTP API and no foundation change.
"""

from __future__ import annotations

import ast
from collections.abc import Sequence
from importlib import import_module
from pathlib import Path
from typing import Any

from alembic import op

revision: str = "078_001"
down_revision: str | Sequence[str] | None = "077_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_VERSIONS_DIR = Path(__file__).resolve().parent
_M067: Any = import_module(
    "slaif_agent_site.db.alembic.versions.067_001_global_region_data_plane"
)
_M068: Any = import_module(
    "slaif_agent_site.db.alembic.versions.068_001_media_publication_core"
)

_JOURNAL = "control.slaif_mutation_completion_record"
_OUTER_END_ANCHOR = "        END;\n        $fn$"
_ROLES_WITHOUT_JOURNAL_ACCESS = (
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

_JOURNAL_TABLE_SQL = """
        CREATE TABLE audit.mutation_completion (
            operation_id uuid PRIMARY KEY,
            family text NOT NULL CHECK (family IN ('agent','human_editor','media')),
            site_id uuid NOT NULL,
            workspace_id uuid NOT NULL,
            capability_id uuid REFERENCES control.capability(id),
            human_user_id uuid REFERENCES control.user_account(id),
            request_identity text NOT NULL,
            request_digest text NOT NULL,
            resource_type text NOT NULL,
            resource_id uuid NOT NULL,
            disposition text NOT NULL CHECK (disposition IN ('completed','no_effect')),
            schema_version text NOT NULL DEFAULT 'mutation-completion/v1',
            occurred_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT mutation_completion_principal CHECK (
                (family = 'agent' AND capability_id IS NOT NULL AND human_user_id IS NULL)
                OR (family IN ('human_editor','media') AND capability_id IS NULL
                    AND human_user_id IS NOT NULL)
            ),
            CONSTRAINT mutation_completion_identity_shape CHECK (
                request_identity ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT mutation_completion_digest_shape CHECK (
                request_digest ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT mutation_completion_schema_version CHECK (
                schema_version = 'mutation-completion/v1'
            ),
            CONSTRAINT mutation_completion_resource_shape CHECK (
                length(resource_type) BETWEEN 1 AND 128
            )
        )
"""

_JOURNAL_HELPER_SQL = f"""
        CREATE FUNCTION {_JOURNAL}(
            p_operation_id uuid, p_family text, p_site_id uuid,
            p_workspace_id uuid, p_capability_id uuid, p_human_user_id uuid,
            p_idempotency_key text, p_request_digest text, p_resource_type text,
            p_resource_id uuid, p_disposition text
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            IF p_operation_id IS NULL OR p_site_id IS NULL OR p_workspace_id IS NULL
               OR p_idempotency_key IS NULL
               OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_request_digest IS NULL OR p_request_digest !~ '^[0-9a-f]{{64}}$'
               OR p_resource_type IS NULL
               OR length(p_resource_type) NOT BETWEEN 1 AND 128
               OR p_resource_id IS NULL
               OR p_family NOT IN ('agent','human_editor','media')
               OR p_disposition NOT IN ('completed','no_effect')
               OR (p_family = 'agent' AND p_capability_id IS NULL)
               OR (p_family IN ('human_editor','media') AND p_human_user_id IS NULL)
               OR NOT EXISTS (SELECT 1 FROM control.workspace AS w
                              WHERE w.id = p_workspace_id AND w.site_id = p_site_id)
            THEN RAISE EXCEPTION 'COMPLETION_RECORD_INPUT'
                USING ERRCODE = 'P0001';
            END IF;
            IF NULLIF(current_setting('app.session_id', true), '')
                   IS DISTINCT FROM p_workspace_id::text
               OR NULLIF(current_setting('app.operation_id', true), '')
                   IS DISTINCT FROM p_operation_id::text
            THEN RAISE EXCEPTION 'COMPLETION_CONTEXT_MISMATCH'
                USING ERRCODE = 'P0001';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_operation_id::text, 280));
            IF p_family = 'agent' AND NOT EXISTS (
                SELECT 1 FROM control.agent_idempotency AS r
                WHERE r.operation_id = p_operation_id
                  AND r.capability_id = p_capability_id
                  AND r.workspace_id = p_workspace_id
                  AND r.idempotency_key = p_idempotency_key
                  AND r.request_digest = p_request_digest
                  AND r.status_code IS NOT NULL
            ) THEN RAISE EXCEPTION 'COMPLETION_RESERVATION_MISMATCH'
                USING ERRCODE = 'P0001';
            END IF;
            IF p_family = 'human_editor' AND NOT EXISTS (
                SELECT 1 FROM control.human_editor_idempotency AS r
                WHERE r.operation_id = p_operation_id
                  AND r.workspace_id = p_workspace_id
                  AND r.site_id = p_site_id
                  AND r.human_user_id = p_human_user_id
                  AND r.idempotency_key = p_idempotency_key
                  AND r.request_digest = p_request_digest
                  AND r.status_code IS NOT NULL
            ) THEN RAISE EXCEPTION 'COMPLETION_RESERVATION_MISMATCH'
                USING ERRCODE = 'P0001';
            END IF;
            IF p_family = 'media' AND NOT EXISTS (
                SELECT 1 FROM control.media_idempotency AS r
                WHERE r.operation_id = p_operation_id
                  AND r.workspace_id = p_workspace_id
                  AND r.site_id = p_site_id
                  AND r.human_user_id = p_human_user_id
                  AND r.idempotency_key = p_idempotency_key
                  AND r.request_digest = p_request_digest
                  AND r.status_code IS NOT NULL
            ) THEN RAISE EXCEPTION 'COMPLETION_RESERVATION_MISMATCH'
                USING ERRCODE = 'P0001';
            END IF;
            IF p_family = 'agent' AND (
                EXISTS (SELECT 1 FROM audit.human_editor_mutation AS t
                        WHERE t.operation_id = p_operation_id)
                OR EXISTS (SELECT 1 FROM audit.media_mutation AS t
                        WHERE t.operation_id = p_operation_id)
                OR EXISTS (SELECT 1 FROM audit.agent_mutation AS t
                        WHERE t.operation_id = p_operation_id
                          AND t.capability_id IS DISTINCT FROM p_capability_id)
            ) THEN RAISE EXCEPTION 'COMPLETION_IDENTITY_CONFLICT'
                USING ERRCODE = 'P0003';
            END IF;
            IF p_family = 'human_editor' AND (
                EXISTS (SELECT 1 FROM audit.agent_mutation AS t
                        WHERE t.operation_id = p_operation_id)
                OR EXISTS (SELECT 1 FROM audit.media_mutation AS t
                        WHERE t.operation_id = p_operation_id)
                OR EXISTS (SELECT 1 FROM audit.human_editor_mutation AS t
                        WHERE t.operation_id = p_operation_id
                          AND t.human_user_id IS DISTINCT FROM p_human_user_id)
            ) THEN RAISE EXCEPTION 'COMPLETION_IDENTITY_CONFLICT'
                USING ERRCODE = 'P0003';
            END IF;
            IF p_family = 'media' AND (
                EXISTS (SELECT 1 FROM audit.agent_mutation AS t
                        WHERE t.operation_id = p_operation_id)
                OR EXISTS (SELECT 1 FROM audit.human_editor_mutation AS t
                        WHERE t.operation_id = p_operation_id)
                OR EXISTS (SELECT 1 FROM audit.media_mutation AS t
                        WHERE t.operation_id = p_operation_id
                          AND t.human_user_id IS DISTINCT FROM p_human_user_id)
            ) THEN RAISE EXCEPTION 'COMPLETION_IDENTITY_CONFLICT'
                USING ERRCODE = 'P0003';
            END IF;
            IF EXISTS (
                SELECT 1 FROM control.agent_idempotency AS r
                WHERE r.operation_id = p_operation_id AND r.status_code IS NOT NULL
                  AND NOT (p_family = 'agent'
                       AND r.capability_id = p_capability_id
                       AND r.workspace_id = p_workspace_id
                       AND r.idempotency_key = p_idempotency_key
                       AND r.request_digest = p_request_digest)
            ) THEN RAISE EXCEPTION 'COMPLETION_IDENTITY_CONFLICT'
                USING ERRCODE = 'P0003';
            END IF;
            IF EXISTS (
                SELECT 1 FROM control.human_editor_idempotency AS r
                WHERE r.operation_id = p_operation_id AND r.status_code IS NOT NULL
                  AND NOT (p_family = 'human_editor'
                       AND r.workspace_id = p_workspace_id
                       AND r.site_id = p_site_id
                       AND r.human_user_id = p_human_user_id
                       AND r.idempotency_key = p_idempotency_key
                       AND r.request_digest = p_request_digest)
            ) THEN RAISE EXCEPTION 'COMPLETION_IDENTITY_CONFLICT'
                USING ERRCODE = 'P0003';
            END IF;
            IF EXISTS (
                SELECT 1 FROM control.media_idempotency AS r
                WHERE r.operation_id = p_operation_id AND r.status_code IS NOT NULL
                  AND NOT (p_family = 'media'
                       AND r.workspace_id = p_workspace_id
                       AND r.site_id = p_site_id
                       AND r.human_user_id = p_human_user_id
                       AND r.idempotency_key = p_idempotency_key
                       AND r.request_digest = p_request_digest)
            ) THEN RAISE EXCEPTION 'COMPLETION_IDENTITY_CONFLICT'
                USING ERRCODE = 'P0003';
            END IF;
            INSERT INTO audit.mutation_completion(
                operation_id, family, site_id, workspace_id, capability_id,
                human_user_id, request_identity, request_digest, resource_type,
                resource_id, disposition
            ) VALUES (
                p_operation_id, p_family, p_site_id, p_workspace_id,
                p_capability_id, p_human_user_id,
                encode(sha256(convert_to(p_idempotency_key, 'UTF8')), 'hex'),
                p_request_digest, p_resource_type, p_resource_id, p_disposition
            );
        END;
        $fn$
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


def _journal_call(
    family: str,
    *,
    capability_param: str | None,
    human_param: str | None,
    key_param: str,
    digest_param: str,
    disposition: str,
) -> str:
    capability = capability_param if capability_param is not None else "NULL"
    human = human_param if human_param is not None else "NULL"
    return (
        "            PERFORM control.slaif_mutation_completion_record(\n"
        f"                p_operation_id, '{family}', p_site_id, p_workspace_id,\n"
        f"                {capability}, {human}, {key_param}, {digest_param},\n"
        f"                p_resource_type, p_resource_id, '{disposition}'\n"
        "            );\n"
    )


def _inject_journal(body: str, call: str) -> str:
    count = body.count(_OUTER_END_ANCHOR)
    if count != 1:
        raise RuntimeError(
            "078_001: completion body outer-END anchor not found exactly once "
            f"(count={count})"
        )
    return body.replace(_OUTER_END_ANCHOR, call + _OUTER_END_ANCHOR, 1)


def _source_completion_body(
    version_file: str,
    function_name: str,
    *,
    want_13arg: bool = False,
) -> str:
    """Extract the final deployed literal body from a sibling version file.

    The re-emitted body must stay byte-identical to the currently deployed
    definition; a drift failure aborts the migration instead of silently
    changing trusted completion behavior.
    """
    path = _VERSIONS_DIR / version_file
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError) as error:
        raise RuntimeError(f"078_001: cannot read {version_file}: {error}") from error
    matches: list[str] = []
    marker = f"FUNCTION control.{function_name}("
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        candidate = node.value
        idx = candidate.find(marker)
        if idx == -1:
            continue
        if (
            not candidate[max(0, idx - 40) : idx]
            .rstrip()
            .endswith(("CREATE", "CREATE OR REPLACE"))
        ):
            continue
        if function_name == "slaif_agent_idempotency_complete":
            header = candidate[
                candidate.index("(", idx) : candidate.index(") RETURNS", idx)
            ]
            if ("p_action text" in header) != want_13arg:
                continue
        matches.append(candidate)
    if not matches:
        raise RuntimeError(f"078_001: {function_name} body missing in {version_file}")
    return matches[-1]


def _or_replace(body: str, function_name: str) -> str:
    plain = f"CREATE FUNCTION control.{function_name}("
    replaced = body.replace(
        plain, f"CREATE OR REPLACE FUNCTION control.{function_name}(", 1
    )
    if replaced == body:
        raise RuntimeError(
            f"078_001: {function_name} CREATE marker missing (body drift)"
        )
    return replaced


def _parameter_types(body: str) -> str:
    name_end = body.index(") RETURNS")
    open_idx = body.index("(", body.index("FUNCTION control."))
    params = body[open_idx + 1 : name_end]
    return ",".join(
        part.strip().split()[-1] for part in params.split(",") if part.strip()
    )


def _secure_function(name: str, signature: str, role: str) -> None:
    op.execute(f"ALTER FUNCTION control.{name}({signature}) OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION control.{name}({signature}) FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION control.{name}({signature}) TO {role}")


def upgrade() -> None:
    op.execute(_JOURNAL_TABLE_SQL)
    op.execute("ALTER TABLE audit.mutation_completion OWNER TO slaif_owner")
    op.execute("REVOKE ALL ON TABLE audit.mutation_completion FROM PUBLIC")
    for role in _ROLES_WITHOUT_JOURNAL_ACCESS:
        op.execute(f"REVOKE ALL ON TABLE audit.mutation_completion FROM {role}")
    op.execute(_JOURNAL_HELPER_SQL)
    op.execute(f"ALTER FUNCTION {_JOURNAL} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_JOURNAL} FROM PUBLIC")
    for role in _ROLES_WITHOUT_JOURNAL_ACCESS:
        op.execute(f"REVOKE ALL ON FUNCTION {_JOURNAL} FROM {role}")

    # Agent 13-argument semantic completion: the 068_001 cumulative body
    # (067 include_region=True plus the accepted media upload row) plus the
    # journal record.  The builder emits the CREATE only; the explicit
    # ownership/grants follow.
    semantic_body = _inject_journal(
        str(_M068._semantic_completion_sql()),
        _journal_call(
            "agent",
            capability_param="p_capability_id",
            human_param=None,
            key_param="p_idempotency_key",
            digest_param="p_request_digest",
            disposition="completed",
        ),
    )
    _execute_block(semantic_body)
    _secure_function(
        "slaif_agent_idempotency_complete",
        _parameter_types(semantic_body),
        "slaif_agent_runtime",
    )

    # Agent 10-argument explicit no-effect completion: the 067_001 body
    # (include_region=True is the deployed form) plus the journal record
    # with the EXPLICIT trusted no-effect disposition.  The builder block
    # already carries its ownership/grant statements.
    no_effect_body = _inject_journal(
        _M067._no_effect_completion_sql(include_region=True),
        _journal_call(
            "agent",
            capability_param="p_capability_id",
            human_param=None,
            key_param="p_idempotency_key",
            digest_param="p_request_digest",
            disposition="no_effect",
        ),
    )
    _execute_block(no_effect_body)

    # Agent 10-argument legacy completion: the 047_001 body, still deployed
    # (Python routes always pass the semantic action, but the legacy
    # boundary remains trusted and is covered).
    legacy_body = _inject_journal(
        _source_completion_body(
            "047_001_repair_item_semantics_and_translations.py",
            "slaif_agent_idempotency_complete",
            want_13arg=False,
        ),
        _journal_call(
            "agent",
            capability_param="p_capability_id",
            human_param=None,
            key_param="p_idempotency_key",
            digest_param="p_request_digest",
            disposition="completed",
        ),
    )
    _execute_block(legacy_body)
    _secure_function(
        "slaif_agent_idempotency_complete",
        _parameter_types(legacy_body),
        "slaif_agent_runtime",
    )

    # HUMAN editor completion for HUMAN workspaces: the 028_001 body with
    # the single deterministic CREATE -> CREATE OR REPLACE edit.
    human_body = _inject_journal(
        _or_replace(
            _source_completion_body(
                "028_001_human_editor_workspace_envelope.py",
                "slaif_human_editor_idempotency_complete",
            ),
            "slaif_human_editor_idempotency_complete",
        ),
        _journal_call(
            "human_editor",
            capability_param=None,
            human_param="p_human_user_id",
            key_param="p_idempotency_key",
            digest_param="p_request_digest",
            disposition="completed",
        ),
    )
    _execute_block(human_body)
    _secure_function(
        "slaif_human_editor_idempotency_complete",
        _parameter_types(human_body),
        "slaif_editor_runtime",
    )

    # HUMAN editor completion for AGENT workspaces: the 069_001 body with
    # the single deterministic CREATE -> CREATE OR REPLACE edit.
    human_agent_body = _inject_journal(
        _or_replace(
            _source_completion_body(
                "069_001_human_agent_workspace_editor.py",
                "slaif_human_agent_editor_idempotency_complete",
            ),
            "slaif_human_agent_editor_idempotency_complete",
        ),
        _journal_call(
            "human_editor",
            capability_param=None,
            human_param="p_human_user_id",
            key_param="p_idempotency_key",
            digest_param="p_request_digest",
            disposition="completed",
        ),
    )
    _execute_block(human_agent_body)
    _secure_function(
        "slaif_human_agent_editor_idempotency_complete",
        _parameter_types(human_agent_body),
        "slaif_editor_runtime",
    )

    # Human media upload completion: the 030_001 body (p_key/p_digest
    # parameter names) with the single deterministic CREATE edit.
    media_body = _inject_journal(
        _or_replace(
            _source_completion_body(
                "030_001_media_service_surface.py",
                "slaif_media_idempotency_complete",
            ),
            "slaif_media_idempotency_complete",
        ),
        _journal_call(
            "media",
            capability_param=None,
            human_param="p_human_user_id",
            key_param="p_key",
            digest_param="p_digest",
            disposition="completed",
        ),
    )
    _execute_block(media_body)
    _secure_function(
        "slaif_media_idempotency_complete",
        _parameter_types(media_body),
        "slaif_media",
    )


def downgrade() -> None:
    # Explicit fail-closed refusal (no conditional path): restoring the
    # pre-078 completion bodies would leave the journal history of 078-era
    # completions uninterpretable against the unrecorded bodies, and no
    # supported path can re-derive the explicit no-effect decisions.  The
    # refusal raises before any restoration and touches no canonical,
    # pending, audit, idempotency or snapshot state.  The bootstrap
    # operator path refuses this rollback earlier still (before the
    # readiness PENDING marker and the content COW disable); this body is
    # the defense for direct migration invocations.
    op.execute(
        """
        DO $guard$
        BEGIN
            RAISE EXCEPTION
                'TRUSTED_MUTATION_COMPLETIONS_DOWNGRADE_UNSUPPORTED'
                USING ERRCODE = 'P0001';
        END $guard$;
        """
    )

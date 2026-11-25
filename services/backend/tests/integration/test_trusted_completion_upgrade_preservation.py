"""083/11-a: trusted completion provenance upgrade/downgrade preservation.

C6 qualification for the 078_001 trusted mutation completion journal:

- a fresh install at the 078 head reaches the real ready phase with the
  journal table and owner-only helper present, zero-grant, and empty (no
  historical backfill), and the six re-emitted completion bodies keep
  their original guards while the private helper carries the context,
  reservation, identity and request-privacy checks;
- the bootstrap operator refuses a downgrade to base BEFORE committing
  readiness PENDING or disabling content COW whenever the product-owned
  journal table is present (feature-presence guard: the released 078 head
  with a genuinely empty journal, and a fixture-proven later-head
  presence case), leaving the complete state exactly as found;
- the 078_001 Alembic downgrade body is the second line of defense for
  direct migration invocations (immediate 078 -> 077 boundary and
  downgrade to base);
- the quiescent 077 -> 078 upgrade (to the released 078 head)
  preserves pre-078 family audit, idempotency (including explicit
  no-effect), the genuine retained review snapshot history (a
  review-snapshot/v2 built by the real trusted materializer and the
  released 077-era completion definer under the real freeze job
  lifecycle, plus a faithful 075-contract v1 document, in a separate
  workspace quiesced by the real supported discard lifecycle) and
  canonical history byte-exact across ALL THREE families, invents no
  journal rows, keeps old idempotency replays working, and records new
  (078-era) completions forward;
- the normal pending-COW upgrade refusal (from a real 077 head toward
  the current head, 079_001 at this source) preserves the complete
  preexisting state before any migration step.
- 083/12: the quiescent 078 -> 079 upgrade preserves the 078-era
  journal/family/snapshot/canonical history byte-exact, leaves the
  companion-less historical snapshot readable with a NULL manifest
  projection, works forward (real 079 freeze stores the companion,
  real dual-digest accept promotes exactly), and both the operator
  downgrade and the direct 079_001 Alembic body refuse before any
  effect; the pending-COW refusal fires from a real 078 head toward
  the 079 target head.

Direct owner-level completion-definer exercise is the bounded evidence
here; it is not a full HTTP+COW lifecycle proof (the existing C2 media/
editor/agent suites cover those paths).
The 078 -> 079 retained-snapshot fixture is likewise bounded: the
078-era workers predate this source, so the retained historical row is
the faithful owner-seeded v1 document, while the forward v2 +
companion are real current-worker generated.
The 077 -> 078 retained v2 is likewise bounded: the current freeze
worker carries the 079 companion step and cannot run at the released
077 head, so the v2 is produced by the real trusted materializer and
the released 077-era completion definer under the real freeze
enqueue/claim/terminal job lifecycle, not by the current worker.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

import asyncpg
import pytest
import slaif_agent_site.bootstrap.service as bootstrap_service
import sqlalchemy.exc as sqlalchemy_exc
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import (
    get_cow_status,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
    reconcile,
    upgrade,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.review_worker import snapshot
from slaif_agent_site.review_worker.accept_job import MediaBoundary, run_accept_job
from test_agent_mutations import _expected_head_override, _seed
from test_agent_theme_boundaries import _agent_client
from test_freeze_review_snapshot import (
    _create_workspace,
    _digest_is_valid,
    _freeze_claim_run,
    _freeze_enqueue_claim,
    _rc6_build_snapshot_document,
    _rc6_canonical_digest,
    _snapshot_row,
    _worker_pool,
)
from test_media_workspace_migration_preservation import (
    _content_operations,
    _cow_component_create,
    _discard_claim_run,
)
from test_real_human_accept import (
    _claim_accept,
    _enqueue_bound_accept,
    _media_settings,
    _worker_settings,
)
from test_trusted_completion_late_failure import _create_page
from test_trusted_completion_producer_families import _seed_agent_workspace

HISTORICAL_077_HEAD = "077_001"

_JOURNAL_TABLE = "audit.mutation_completion"
_JOURNAL_HELPER = "control.slaif_mutation_completion_record"
_COMPLETER_NAMES = (
    "slaif_agent_idempotency_complete",
    "slaif_agent_idempotency_complete_no_effect",
    "slaif_human_editor_idempotency_complete",
    "slaif_human_agent_editor_idempotency_complete",
    "slaif_media_idempotency_complete",
)

ROLES_WITHOUT_JOURNAL_ACCESS = (
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

_TABLE_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _owner_settings(database: AgentSiteDatabase) -> tuple[Any, str]:
    return (
        database.settings.resolved_owner_dsn(),
        database.name,
    )


async def _seed_077(database: AgentSiteDatabase) -> tuple[str, dict[str, uuid.UUID]]:
    """Real released 077_001 head (pre-journal) plus the standard fixture."""
    return await _seed(database, historical_head=HISTORICAL_077_HEAD)


async def _set_cow_gucs(
    connection: asyncpg.Connection[Any],
    workspace_id: uuid.UUID,
    operation_id: uuid.UUID,
    capability_id: uuid.UUID | None = None,
) -> None:
    await connection.execute(
        "SELECT set_config('app.session_id', $1, true)", str(workspace_id)
    )
    await connection.execute(
        "SELECT set_config('app.operation_id', $1, true)", str(operation_id)
    )
    if capability_id is not None:
        await connection.execute(
            "SELECT set_config('app.capability_id', $1, true)", str(capability_id)
        )


async def _agent_semantic_completion(
    database: AgentSiteDatabase,
    ids: dict[str, uuid.UUID],
    *,
    key: str,
    operation_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    status: int = 201,
    method: str = "POST",
    quota: str = "mutation",
) -> None:
    """One real agent semantic completion through the actual definer."""
    digest = _digest(key, str(resource_id))
    body = {
        "action": action,
        "operation_id": str(operation_id),
        "record": {"id": str(resource_id)},
    }
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(connection, ids["workspace_id"], operation_id)
            row = await connection.fetchrow(
                "SELECT * FROM control.slaif_agent_idempotency_begin($1,$2,$3,$4,$5)",
                ids["capability_id"],
                ids["workspace_id"],
                key,
                digest,
                operation_id,
            )
            assert row is not None and str(row[0]) == "STARTED"
            await connection.execute(
                "SELECT control.slaif_agent_idempotency_complete"
                "($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                ids["capability_id"],
                ids["workspace_id"],
                key,
                digest,
                operation_id,
                status,
                json.dumps(body),
                resource_type,
                resource_id,
                ids["site_id"],
                action,
                method,
                quota,
            )


async def _agent_no_effect_completion(
    database: AgentSiteDatabase,
    ids: dict[str, uuid.UUID],
    *,
    key: str,
    operation_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
    status: int = 200,
) -> None:
    """One real agent EXPLICIT no-effect completion through the definer."""
    digest = _digest(key, "no-effect", str(resource_id))
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(connection, ids["workspace_id"], operation_id)
            row = await connection.fetchrow(
                "SELECT * FROM control.slaif_agent_idempotency_begin($1,$2,$3,$4,$5)",
                ids["capability_id"],
                ids["workspace_id"],
                key,
                digest,
                operation_id,
            )
            assert row is not None and str(row[0]) == "STARTED"
            await connection.execute(
                "SELECT control.slaif_agent_idempotency_complete_no_effect"
                "($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                ids["capability_id"],
                ids["workspace_id"],
                key,
                digest,
                operation_id,
                status,
                "{}",
                resource_type,
                resource_id,
                ids["site_id"],
            )


async def _human_editor_fixture(
    database: AgentSiteDatabase, site_id: uuid.UUID
) -> dict[str, Any]:
    """A real HUMAN editorial surface: user, membership, session, workspace."""
    human_user_id = uuid.uuid4()
    human_session_id = uuid.uuid4()
    session_public_id = f"sas2_{uuid.uuid4().hex}"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "INSERT INTO control.user_account "
            "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
            "VALUES ($1, 'OIDC', 'https://completion.test', $2, 'Completion Human')",
            human_user_id,
            str(human_user_id),
        )
        await connection.execute(
            "INSERT INTO control.site_membership "
            "(site_id, user_account_id, role_key, delegation_ceiling) "
            "VALUES ($1, $2, 'SITE_EDITOR', 2)",
            site_id,
            human_user_id,
        )
        session = await connection.fetchrow(
            "SELECT * FROM control.slaif_create_human_session($1,$2,$3,$4,$5,$6,$7,$8)",
            human_session_id,
            session_public_id,
            b"h" * 32,
            b"c" * 32,
            human_user_id,
            3600,
            7200,
            3600,
        )
        assert session is not None
        workspace_id = await connection.fetchval(
            "SELECT control.slaif_human_editor_workspace_resolve($1, $2)",
            site_id,
            human_user_id,
        )
    return {
        "human_user_id": human_user_id,
        "human_session_id": human_session_id,
        "workspace_id": workspace_id,
        "site_id": site_id,
    }


async def _human_editor_completion(
    database: AgentSiteDatabase,
    hfx: dict[str, Any],
    *,
    key: str,
    operation_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID,
    permission: str = "page:create",
    status: int = 200,
) -> None:
    """One real HUMAN editor completion through the actual definer."""
    digest = _digest(key, str(resource_id))
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(connection, hfx["workspace_id"], operation_id)
            row = await connection.fetchrow(
                "SELECT * FROM control.slaif_human_editor_idempotency_begin"
                "($1,$2,$3,$4,$5,$6,$7,$8)",
                hfx["workspace_id"],
                hfx["human_user_id"],
                hfx["site_id"],
                hfx["human_session_id"],
                permission,
                key,
                digest,
                operation_id,
            )
            assert row is not None and str(row[0]) == "STARTED"
            await connection.execute(
                "SELECT control.slaif_human_editor_idempotency_complete"
                "($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                hfx["workspace_id"],
                hfx["human_user_id"],
                hfx["site_id"],
                hfx["human_session_id"],
                permission,
                key,
                digest,
                operation_id,
                status,
                json.dumps({"ok": True}),
                action,
                resource_type,
                resource_id,
            )


async def _media_completion(
    database: AgentSiteDatabase,
    hfx: dict[str, Any],
    *,
    key: str,
    operation_id: uuid.UUID,
    resource_id: uuid.UUID,
) -> None:
    """One real human media upload completion through the actual definer.

    The media definer's assert requires the COW context GUCs to name the
    HUMAN workspace and this operation (pre-078 bodies already enforce
    the context), a HUMAN workspace owned by the human, and an active
    session; the asset row is content-addressed canonical media.
    """
    digest = _digest(key, "media", str(resource_id))
    asset_id = resource_id
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(connection, hfx["workspace_id"], operation_id)
            row = await connection.fetchrow(
                "SELECT * FROM control.slaif_media_idempotency_begin"
                "($1,$2,$3,$4,$5,$6,$7,$8)",
                hfx["workspace_id"],
                hfx["human_user_id"],
                hfx["site_id"],
                hfx["human_session_id"],
                "media:upload",
                key,
                digest,
                operation_id,
            )
            assert row is not None and str(row[0]) == "STARTED"
            await connection.execute(
                "SELECT control.slaif_media_idempotency_complete"
                "($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                hfx["workspace_id"],
                hfx["human_user_id"],
                hfx["site_id"],
                hfx["human_session_id"],
                "media:upload",
                key,
                digest,
                operation_id,
                201,
                json.dumps({"record": {"id": str(asset_id)}}),
                "MEDIA_UPLOADED",
                "media_asset",
                asset_id,
            )


async def _journal_rows(
    database: AgentSiteDatabase,
) -> tuple[tuple[Any, ...], ...]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        exists = await connection.fetchval(
            f"SELECT to_regclass('{_JOURNAL_TABLE}') IS NOT NULL"
        )
        if not exists:
            return ()
        return tuple(
            tuple(row)
            for row in await connection.fetch(
                "SELECT operation_id, family, site_id, workspace_id, "
                "capability_id, human_user_id, request_identity, "
                "request_digest, resource_type, resource_id, disposition, "
                "schema_version, occurred_at FROM "
                + _JOURNAL_TABLE
                + " ORDER BY operation_id"
            )
        )


async def _family_history(
    database: AgentSiteDatabase,
) -> tuple[tuple[Any, ...], ...]:
    """Complete pre-078 family audit + idempotency history (all columns)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        audit = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM audit.agent_mutation ORDER BY operation_id"
            )
        )
        human_audit = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM audit.human_editor_mutation ORDER BY operation_id"
            )
        )
        media_audit = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM audit.media_mutation ORDER BY operation_id"
            )
        )
        agent_ledger = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM control.agent_idempotency "
                "ORDER BY capability_id, idempotency_key"
            )
        )
        human_ledger = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM control.human_editor_idempotency "
                "ORDER BY workspace_id, idempotency_key"
            )
        )
        media_ledger = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM control.media_idempotency "
                "ORDER BY workspace_id, idempotency_key"
            )
        )
        snapshots = tuple(
            row
            for row in await connection.fetch(
                "SELECT * FROM control.review_snapshot ORDER BY id"
            )
        )
        return (
            audit,
            human_audit,
            media_audit,
            agent_ledger,
            human_ledger,
            media_ledger,
            snapshots,
        )


async def _canonical_history(
    database: AgentSiteDatabase,
) -> tuple[tuple[Any, ...], ...]:
    """Complete canonical content rows touched by the fixtures."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        return tuple(
            (
                tuple(
                    tuple(row)
                    for row in await connection.fetch(
                        "SELECT * FROM content.page ORDER BY id"
                    )
                ),
                tuple(
                    tuple(row)
                    for row in await connection.fetch(
                        "SELECT * FROM content.content_item ORDER BY id"
                    )
                ),
                tuple(
                    tuple(row)
                    for row in await connection.fetch(
                        "SELECT * FROM content.media_asset ORDER BY id"
                    )
                ),
            )
        )


async def _pending_operation_ids(
    database: AgentSiteDatabase, workspace_id: uuid.UUID
) -> list[uuid.UUID]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        executor = AsyncpgExecutor(connection)
        operations: list[uuid.UUID] = await get_session_operations(
            executor, workspace_id, schema="content"
        )
        return operations


async def _function_defs(
    database: AgentSiteDatabase,
) -> tuple[tuple[str, str], ...]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        rows = await connection.fetch(
            "SELECT proc.proname, pg_get_functiondef(proc.oid) "
            "FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace ns ON ns.oid = proc.pronamespace "
            "WHERE ns.nspname = 'control' AND proc.proname IN "
            "('slaif_agent_idempotency_complete', "
            "'slaif_agent_idempotency_complete_no_effect', "
            "'slaif_human_editor_idempotency_complete', "
            "'slaif_human_agent_editor_idempotency_complete', "
            "'slaif_media_idempotency_complete', "
            "'slaif_mutation_completion_record') "
            "ORDER BY proc.proname, proc.oid"
        )
        return tuple((row[0], row[1]) for row in rows)


async def _readiness_snapshot(database: AgentSiteDatabase) -> tuple[Any, ...]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        return tuple(
            await connection.fetchrow(
                "SELECT readiness_state, migration_revision, "
                "content_object_count, content_object_fingerprint, "
                "foundation_object_count, foundation_object_fingerprint, "
                "foundation_deployed, foundation_hardened, "
                "foundation_privileges_validated, product_privileges_validated, "
                "safe, updated_at FROM control.bootstrap_readiness "
                "WHERE singleton"
            )
        )


async def _cow_enabled(database: AgentSiteDatabase) -> bool:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        return bool(
            (await get_cow_status(AsyncpgExecutor(connection), schema="content"))[
                "enabled"
            ]
        )


async def _grant_fingerprint(database: AgentSiteDatabase) -> tuple[Any, ...]:
    """Effective EXECUTE / table privileges of every role on the journal."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        table_oid = await connection.fetchval(
            f"SELECT to_regclass('{_JOURNAL_TABLE}')::bigint"
        )
        if table_oid is None:
            return ("absent", None, ())
        helper_oid = await connection.fetchval(
            "SELECT to_regprocedure('control.slaif_mutation_completion_record"
            "(uuid,text,uuid,uuid,uuid,uuid,text,text,text,uuid,text)')"
            "::bigint"
        )
        rows: list[tuple[Any, ...]] = []
        for role in ROLES_WITHOUT_JOURNAL_ACCESS:
            table_privs: list[bool] = []
            for priv in _TABLE_PRIVILEGES:
                table_privs.append(
                    bool(
                        await connection.fetchval(
                            "SELECT has_table_privilege($1, $2, $3)",
                            role,
                            _JOURNAL_TABLE,
                            priv,
                        )
                    )
                )
            if helper_oid is None:
                fn_exec: bool | None = None
            else:
                fn_exec = bool(
                    await connection.fetchval(
                        "SELECT has_function_privilege($1, $2::regproc, 'EXECUTE')",
                        role,
                        str(helper_oid),
                    )
                )
            rows.append((role, tuple(table_privs), fn_exec))
        return (table_oid, helper_oid, tuple(rows))


async def _full_state(database: AgentSiteDatabase) -> dict[str, Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        revision = await connection.fetchval(
            "SELECT version_num::text FROM control.alembic_version"
        )
    pending: list[tuple[uuid.UUID, tuple[uuid.UUID, ...]]] = []
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        workspaces = await connection.fetch(
            "SELECT id FROM control.workspace ORDER BY id"
        )
        executor = AsyncpgExecutor(connection)
        for ws in workspaces:
            pending.append(
                (
                    ws["id"],
                    tuple(
                        await get_session_operations(
                            executor, ws["id"], schema="content"
                        )
                    ),
                )
            )
    return {
        "revision": revision,
        "cow_enabled": await _cow_enabled(database),
        "readiness": await _readiness_snapshot(database),
        "pending": tuple(pending),
        "family_history": await _family_history(database),
        "canonical": await _canonical_history(database),
        "functions": await _function_defs(database),
        "grants": await _grant_fingerprint(database),
    }


def _assert_state_equal(before: dict[str, Any], after: dict[str, Any]) -> None:
    for key in before:
        assert after[key] == before[key], f"state changed: {key}"


async def test_fresh_078_head_install_journal_contract(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Fresh install at the released 078 head: real ready phase, owner-only journal.

    The 078 head is historical at this source (current head 079_001), so
    the fresh install is staged to the released 078_001 revision and the
    real reconcile runs under the narrow expected-head seam.
    """
    database = agent_site_database
    result = await _upgrade_historical(database, HISTORICAL_078_HEAD)
    assert result.safe
    assert result.revision == HISTORICAL_078_HEAD

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        table_oid = await connection.fetchval(
            f"SELECT to_regclass('{_JOURNAL_TABLE}')::bigint"
        )
        assert table_oid is not None
        owner = await connection.fetchval(
            "SELECT r.rolname::text FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_roles r ON r.oid = c.relowner "
            "WHERE c.oid = $1",
            table_oid,
        )
        assert owner == "slaif_owner"
        for role in ROLES_WITHOUT_JOURNAL_ACCESS:
            for priv in _TABLE_PRIVILEGES:
                assert not await connection.fetchval(
                    "SELECT has_table_privilege($1, $2, $3)",
                    role,
                    _JOURNAL_TABLE,
                    priv,
                ), (role, priv)

        helper_oid = await connection.fetchval(
            "SELECT to_regprocedure('control.slaif_mutation_completion_record"
            "(uuid,text,uuid,uuid,uuid,uuid,text,text,text,uuid,text)')::bigint"
        )
        assert helper_oid is not None
        row = await connection.fetchrow(
            "SELECT prosecdef, array_to_string(proconfig, ',') AS config, "
            "proowner::regrole::text AS owner, "
            "COALESCE(array_to_string(proacl, ','), '') AS acl "
            "FROM pg_catalog.pg_proc WHERE oid = $1",
            helper_oid,
        )
        assert row["prosecdef"] is True
        assert "search_path=pg_catalog" in row["config"]
        assert row["owner"] == "slaif_owner"
        for role in ROLES_WITHOUT_JOURNAL_ACCESS:
            assert not await connection.fetchval(
                "SELECT has_function_privilege($1, $2::regproc, 'EXECUTE')",
                role,
                str(helper_oid),
            ), role
        public_exec = await connection.fetchval(
            "SELECT EXISTS (SELECT 1 FROM aclexplode(COALESCE("
            "proc.proacl, acldefault('f', proc.proowner))) acl "
            "WHERE acl.grantee = 0 AND acl.privilege_type = 'EXECUTE') "
            "FROM pg_catalog.pg_proc proc WHERE proc.oid = $1",
            helper_oid,
        )
        assert public_exec is False

        # The private helper carries the trusted completion checks.
        helper_body = await connection.fetchval(
            "SELECT pg_get_functiondef($1::oid)", helper_oid
        )
        for marker in (
            "COMPLETION_RECORD_INPUT",
            "COMPLETION_CONTEXT_MISMATCH",
            "COMPLETION_RESERVATION_MISMATCH",
            "COMPLETION_IDENTITY_CONFLICT",
            "app.session_id",
            "app.operation_id",
            "pg_advisory_xact_lock",
            "sha256(convert_to(p_idempotency_key, 'UTF8'))",
        ):
            assert marker in helper_body, marker
        assert "digest(convert_to" not in helper_body
        # All three family ledgers are cross-checked for completed rows.
        for ledger in (
            "control.agent_idempotency",
            "control.human_editor_idempotency",
            "control.media_idempotency",
        ):
            assert helper_body.count(ledger) >= 2, ledger

        # A fresh 078 head has NO historical completions: no backfill.
        assert await connection.fetchval(f"SELECT count(*) FROM {_JOURNAL_TABLE}") == 0

        # The six re-emitted completion bodies each carry exactly one
        # journal call and keep their ORIGINAL guards (no pgcrypto, no
        # invented outer context text: the context guard lives in the
        # private helper, asserted above).
        rows = await connection.fetch(
            "SELECT proc.proname, pg_get_functiondef(proc.oid) AS body, "
            "proc.oid FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace ns ON ns.oid = proc.pronamespace "
            "WHERE ns.nspname = 'control' "
            "AND proc.proname IN "
            "('slaif_agent_idempotency_complete', "
            "'slaif_agent_idempotency_complete_no_effect', "
            "'slaif_human_editor_idempotency_complete', "
            "'slaif_human_agent_editor_idempotency_complete', "
            "'slaif_media_idempotency_complete') "
            "ORDER BY proc.proname, proc.oid"
        )
        assert len(rows) == 6
        for row in rows:
            assert row["body"].count("slaif_mutation_completion_record(") == 1
            assert "digest(convert_to" not in row["body"]
        by_kind: dict[str, list[str]] = {"13arg": [], "legacy": [], "no_effect": []}
        for row in rows:
            if row["proname"] == "slaif_agent_idempotency_complete":
                kind = "13arg" if "p_quota_kind" in row["body"] else "legacy"
                by_kind[kind].append(row["body"])
            elif row["proname"] == "slaif_agent_idempotency_complete_no_effect":
                by_kind["no_effect"].append(row["body"])
        assert len(by_kind["13arg"]) == 1
        assert len(by_kind["legacy"]) == 1
        assert len(by_kind["no_effect"]) == 1
        semantic, legacy, no_effect = (
            by_kind["13arg"][0],
            by_kind["legacy"][0],
            by_kind["no_effect"][0],
        )
        # Latest lineage markers: 068 media row + region row in the
        # semantic body; 047 content_item_translation exclusion in the
        # legacy body; 067 no-effect resource list with global_region.
        assert "MEDIA_UPLOADED" in semantic
        assert "GLOBAL_REGION_UPDATED" in semantic
        assert "INVALID_SEMANTIC_COMPLETION" in semantic
        assert "content_item_translation" in legacy
        assert "INVALID_IDEMPOTENCY_COMPLETION" in legacy
        assert "global_region" in no_effect
        # Original per-definer failure guards survive byte-level re-emission.
        assert "HUMAN_EDITOR_IDEMPOTENCY_NOT_STARTED" in next(
            r["body"]
            for r in rows
            if r["proname"] == "slaif_human_editor_idempotency_complete"
        )
        assert "HUMAN_AGENT_EDITOR_IDEMPOTENCY_NOT_STARTED" in next(
            r["body"]
            for r in rows
            if r["proname"] == "slaif_human_agent_editor_idempotency_complete"
        )
        media_body = next(
            r["body"]
            for r in rows
            if r["proname"] == "slaif_media_idempotency_complete"
        )
        assert "MEDIA_IDEMPOTENCY_NOT_STARTED" in media_body
        assert "media_asset" in media_body


async def test_operator_downgrade_refuses_before_effects_at_078(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Operator downgrade at the 078 head refuses before any effect.

    The state carries NO retained review-snapshot/v2 rows, so the 077/v2
    guards cannot mask the completion-provenance refusal.  The fixture
    is staged at the released 078 head (historical at this source).
    """
    database = agent_site_database
    token, ids = await _seed_078(database)
    del token

    # Real 078-era history across agent, human editor and media families.
    page_id = uuid.uuid4()
    await _agent_semantic_completion(
        database,
        ids,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=uuid.uuid4(),
        action="PAGE_CREATED",
        resource_type="page",
        resource_id=page_id,
    )
    await _agent_no_effect_completion(
        database,
        ids,
        key=f"theme-{uuid.uuid4().hex}",
        operation_id=uuid.uuid4(),
        resource_type="page",
        resource_id=page_id,
        status=200,
    )
    hfx = await _human_editor_fixture(database, ids["site_id"])
    await _human_editor_completion(
        database,
        hfx,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=uuid.uuid4(),
        action="PAGE_UPDATED",
        resource_type="page",
        resource_id=page_id,
    )
    asset_id = uuid.uuid4()
    await _media_completion(
        database,
        hfx,
        key=f"media-{uuid.uuid4().hex}",
        operation_id=uuid.uuid4(),
        resource_id=asset_id,
    )
    journal_before = await _journal_rows(database)
    assert len(journal_before) == 4
    families = sorted(row[1] for row in journal_before)
    assert families == ["agent", "agent", "human_editor", "media"]
    dispositions = {row[0]: row[10] for row in journal_before}
    assert sorted(set(dispositions.values())) == ["completed", "no_effect"]

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        v2_rows = await connection.fetchval(
            "SELECT count(*) FROM control.review_snapshot "
            "WHERE payload->>'state_version' = 'review-snapshot/v2'"
        )
    assert v2_rows == 0

    before = await _full_state(database)
    assert before["revision"] == "078_001"

    disable_calls = 0

    async def forbidden_disable(*_args: Any, **_kwargs: Any) -> None:
        nonlocal disable_calls
        disable_calls += 1
        raise AssertionError("public COW disable must not run during preflight")

    monkeypatch.setattr(bootstrap_service, "disable_cow_schema", forbidden_disable)
    with pytest.raises(BootstrapStateError, match="trusted mutation completion"):
        await downgrade(database.settings)
    after = await _full_state(database)
    _assert_state_equal(before, after)
    assert disable_calls == 0
    assert await _journal_rows(database) == journal_before


async def test_fresh_078_empty_journal_downgrade_refuses(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A genuinely fresh 078 head (empty journal) still refuses downgrade.

    The released 078 head is historical at this source: the fresh
    install is staged to 078_001 and the real reconcile runs under the
    narrow expected-head seam, so the operator downgrade starts at the
    released 078 head, not the current 079 head.
    """
    database = agent_site_database
    await _upgrade_historical(database, HISTORICAL_078_HEAD)
    assert await _journal_rows(database) == ()

    disable_calls = 0

    async def forbidden_disable(*_args: Any, **_kwargs: Any) -> None:
        nonlocal disable_calls
        disable_calls += 1
        raise AssertionError("public COW disable must not run during preflight")

    monkeypatch.setattr(bootstrap_service, "disable_cow_schema", forbidden_disable)
    before = await _full_state(database)
    with pytest.raises(BootstrapStateError, match="trusted mutation completion"):
        await downgrade(database.settings)
    after = await _full_state(database)
    _assert_state_equal(before, after)
    assert disable_calls == 0
    assert await _journal_rows(database) == ()


async def test_operator_downgrade_presence_guard_without_078_head(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The refusal is feature-presence based, not a single version name.

    Version-independent property proof: at a 077 head the 078 table does
    not exist, so a LATER head retaining the journal must also refuse.
    A fixture table proves the presence guard fires before the 077 media
    guard, and a plain 077 head still hits the original 077 refusal.
    This is a property test of the guard, not a deployed future head.
    """
    database = agent_site_database
    _token, _ids = await _seed_077(database)

    disable_calls = 0

    async def forbidden_disable(*_args: Any, **_kwargs: Any) -> None:
        nonlocal disable_calls
        disable_calls += 1
        raise AssertionError("public COW disable must not run during preflight")

    monkeypatch.setattr(bootstrap_service, "disable_cow_schema", forbidden_disable)

    # Plain 077 head: the original media-isolation refusal still fires.
    before = await _full_state(database)
    with pytest.raises(BootstrapStateError, match="workspace-isolated media contract"):
        await downgrade(database.settings)
    _assert_state_equal(before, await _full_state(database))

    # Feature present (as a later head would retain it): the completion
    # provenance refusal fires first, before any effect.
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "CREATE TABLE " + _JOURNAL_TABLE + " ( operation_id uuid PRIMARY KEY)"
        )
    try:
        before = await _full_state(database)
        with pytest.raises(BootstrapStateError, match="trusted mutation completion"):
            await downgrade(database.settings)
        _assert_state_equal(before, await _full_state(database))
    finally:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as connection:
            await connection.execute("DROP TABLE IF EXISTS " + _JOURNAL_TABLE)
    assert disable_calls == 0


async def test_078_direct_downgrade_refuses_without_effects(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The 078_001 Alembic body is the second line of defense.

    Both the immediate 078 -> 077 boundary and the downgrade to base
    must raise the unconditional ratchet before any restoration.
    The fixture is staged at the released 078 head (historical at this
    source), so the direct downgrade starts from 078_001 and runs the
    078 body, not the 079 body.
    """
    database = agent_site_database
    token, ids = await _seed_078(database)
    del token
    page_id = uuid.uuid4()
    await _agent_semantic_completion(
        database,
        ids,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=uuid.uuid4(),
        action="PAGE_CREATED",
        resource_type="page",
        resource_id=page_id,
    )
    journal_before = await _journal_rows(database)
    before = await _full_state(database)

    # Immediate boundary: direct downgrade to 077_001 runs 078's body.
    with pytest.raises(sqlalchemy_exc.DBAPIError) as exc_info:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="077_001",
        )
    underlying = exc_info.value.orig
    assert "TRUSTED_MUTATION_COMPLETIONS_DOWNGRADE_UNSUPPORTED" in str(underlying)
    assert getattr(underlying, "sqlstate", None) == "P0001"
    after = await _full_state(database)
    _assert_state_equal(before, after)
    assert await _journal_rows(database) == journal_before

    # Downgrade to base: same ratchet, same preservation.
    with pytest.raises(sqlalchemy_exc.DBAPIError) as exc_info:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="base",
        )
    underlying = exc_info.value.orig
    assert "TRUSTED_MUTATION_COMPLETIONS_DOWNGRADE_UNSUPPORTED" in str(underlying)
    assert getattr(underlying, "sqlstate", None) == "P0001"
    after = await _full_state(database)
    _assert_state_equal(before, after)
    assert await _journal_rows(database) == journal_before


async def _materialize_v1_document(
    database: AgentSiteDatabase,
    site_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> dict[str, Any]:
    """Faithful 075-era raw snapshot document over the real DB rows.

    Mirrors the 070_001/075 materializer's document construction (site,
    locales, theme, regions, navigation, redirects, pages with their
    composition nodes, media references) for the frozen workspace's site.
    The 077 head no longer deploys the 075 materializer function, so the
    materialization queries are test-owned while the document shape, node
    contract and canonical digest are the genuine 075 ones (applied by
    ``_rc6_build_snapshot_document``).
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        site = await owner.fetchrow(
            "SELECT site_key, display_name, default_locale, "
            "component_catalog_version FROM control.site WHERE id = $1",
            site_id,
        )
        ws = await owner.fetchrow(
            "SELECT base_site_revision, operation_watermark "
            "FROM control.workspace WHERE id = $1",
            workspace_id,
        )
        locales = await owner.fetch(
            "SELECT tag, enabled, is_default, position FROM content.site_locale "
            'WHERE site_id = $1 ORDER BY position, tag COLLATE "C"',
            site_id,
        )
        theme = await owner.fetchrow(
            "SELECT row_to_json(t)::text FROM content.slaif_theme_project($1) AS t",
            site_id,
        )
        regions = await owner.fetch(
            "SELECT row_to_json(r)::text FROM content.slaif_region_list($1) AS r "
            "ORDER BY r.region_key, r.variant",
            site_id,
        )
        nav_defs = await owner.fetch(
            "SELECT row_to_json(d)::text FROM content.navigation d "
            'WHERE d.site_id = $1 ORDER BY d.key COLLATE "C"',
            site_id,
        )
        nav_items = await owner.fetch(
            "SELECT row_to_json(n)::text FROM "
            "content.slaif_render_navigation_items($1, $2, "
            "ARRAY['PUBLISHED','DRAFT']) AS n "
            'ORDER BY n.navigation_id, n."position", n.id',
            site_id,
            site["default_locale"],
        )
        redirects = await owner.fetch(
            "SELECT row_to_json(rd)::text FROM (SELECT id, site_id, "
            "source_route, target, status_code, locale FROM content.redirect "
            'WHERE site_id = $1) AS rd ORDER BY rd.source_route COLLATE "C", '
            "rd.locale NULLS FIRST",
            site_id,
        )
        pages_raw = await owner.fetch(
            "SELECT row_to_json(p)::text FROM content.page p "
            "WHERE p.site_id = $1 AND p.deleted_at IS NULL "
            "AND p.status IN ('PUBLISHED','DRAFT') "
            'ORDER BY p.locale COLLATE "C", p.slug COLLATE "C", p.id',
            site_id,
        )
        doc_pages: list[dict[str, Any]] = []
        for raw in pages_raw:
            page = json.loads(raw[0])
            try:
                route = await owner.fetchval(
                    "SELECT content.slaif_agent_page_effective_route($1)",
                    page["id"],
                )
            except asyncpg.PostgresError:
                route = None
            nodes = await owner.fetch(
                "SELECT row_to_json(c)::text FROM content.page_composition c "
                "WHERE c.site_id = $1 AND c.page_id = $2 "
                "ORDER BY c.slot_key, c.order_key, c.id",
                site_id,
                page["id"],
            )
            doc_pages.append(
                {
                    "id": page["id"],
                    "site_id": page["site_id"],
                    "slug": page["slug"],
                    "title": page["title"],
                    "status": page["status"],
                    "locale": page["locale"],
                    "parent_id": page["parent_id"],
                    "route_template": page["route_template"],
                    "effective_route": route,
                    "row_version": page["row_version"],
                    "nodes": [json.loads(node[0]) for node in nodes],
                }
            )
        return {
            "state_version": "review-snapshot/v1",
            "workspace_id": str(workspace_id),
            "site_id": str(site_id),
            "site": {
                "site_key": site["site_key"],
                "display_name": site["display_name"],
                "default_locale": site["default_locale"],
                "component_catalog_version": site["component_catalog_version"],
            },
            "base_site_revision": ws["base_site_revision"],
            "operation_watermark": ws["operation_watermark"],
            "locales": [dict(row) for row in locales],
            "theme": json.loads(theme[0]) if theme is not None else {},
            "regions": [json.loads(row[0]) for row in regions],
            "navigation": {
                "definitions": [json.loads(row[0]) for row in nav_defs],
                "items": [json.loads(row[0]) for row in nav_items],
            },
            "redirects": [json.loads(row[0]) for row in redirects],
            "pages": doc_pages,
            "media": {},
        }


async def _seed_retained_snapshot_row(
    database: AgentSiteDatabase, row: dict[str, Any]
) -> None:
    """Owner-insert one retained review_snapshot row (fixture history).

    The 077 head's ``slaif_review_snapshot_complete`` only accepts the v2
    contract, so base-era v1 history predating that contract is inserted
    directly by the setup owner, matching the retained-row fixture
    pattern of the bootstrap downgrade tests.
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "INSERT INTO control.review_snapshot "
            "(workspace_id, site_id, status, revision_watermark, versions, "
            " normalized_state, validation_report, media_references, "
            " browser_evidence, payload, digest, created_by) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
            row["workspace_id"],
            row["site_id"],
            row["status"],
            row["revision_watermark"],
            json.dumps(row["versions"]),
            json.dumps(row["normalized_state"]),
            json.dumps(row["validation_report"]),
            json.dumps(row["media_references"]),
            json.dumps(row["browser_evidence"]),
            json.dumps(row["payload"]),
            row["digest"],
            row["created_by"],
        )


async def _snapshot_rows_text(database: AgentSiteDatabase) -> tuple[str, ...]:
    """Byte-exact row_to_json text of every retained review snapshot."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        return tuple(
            row[0]
            for row in await connection.fetch(
                "SELECT row_to_json(r)::text FROM control.review_snapshot r "
                "ORDER BY r.workspace_id, r.created_at, r.id"
            )
        )


async def test_quiescent_077_to_078_upgrade_preserves_history(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Quiescent 077 -> 078 (released 078 head) keeps ALL history intact.

    The retained review history is genuine: a review-snapshot/v2 built
    by the real trusted materializer and the released 077-era
    completion definer under the real freeze enqueue/claim/terminal job
    lifecycle (the current freeze worker cannot run at the 077 head:
    its completion call is the 079 companion variant) plus a faithful
    075-contract v1 document over the real site rows, in a SEPARATE
    workspace quiesced by the real supported discard lifecycle (pending
    COW cleared, terminal DISCARDED) BEFORE the normal quiescent
    operator upgrade to the released 078 head.  The active agent fixture
    workspace stays eligible for its replay and forward completions.
    """
    database = agent_site_database
    token, ids = await _seed_077(database)
    del token

    # Actual canonical resource for the fixture completions.
    canonical_page_id = uuid.uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "INSERT INTO content.page_base "
            "(id, site_id, slug, title, status, locale) "
            "VALUES ($1, $2, 'completion-canonical', 'Completion canonical', "
            "'DRAFT', 'en')",
            canonical_page_id,
            ids["site_id"],
        )

    # --- Separate frozen workspace: genuine retained snapshot history ---
    frozen_page_id = uuid.uuid4()
    frozen_section_id = uuid.uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        ws_frozen, cap_frozen = await _create_workspace(
            owner,
            ids["site_id"],
            ids["delegator_id"],
            "083/11-a completion quiescent freeze",
        )
        await owner.execute(
            "INSERT INTO content.page_base (id, site_id, slug, title, status,"
            " locale) VALUES ($1, $2, 'frozen-home', 'Frozen home', 'PUBLISHED',"
            " 'en-US')",
            frozen_page_id,
            ids["site_id"],
        )
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES ($1, $2, $3, 'Section', '1', NULL, 'default', 0,"
            " '{}'::jsonb)",
            frozen_section_id,
            ids["site_id"],
            frozen_page_id,
        )
    # Genuine pending COW work the freeze captures and the discard clears.
    await _cow_component_create(
        database,
        workspace_id=ws_frozen,
        capability_id=cap_frozen,
        site_id=ids["site_id"],
        page_id=frozen_page_id,
        parent_id=frozen_section_id,
        component_type="Heading",
        props={"level": 1, "text": "083/11-a quiescent freeze marker"},
    )
    assert await _content_operations(database, ws_frozen)

    pool = await _worker_pool(database)
    try:
        # The released 077-era completion boundary: real freeze enqueue
        # + worker claim (workspace FREEZING, job CLAIMED), then the
        # exact 078-era worker transaction through the real trusted
        # materializer and the 077 head's own v2 completion definer.
        # The CURRENT worker cannot run here: its completion call is the
        # 079 companion-manifest variant, which the released 077 head
        # does not deploy.
        freeze_job_id, _freeze_job = await _freeze_enqueue_claim(
            database,
            workspace_id=ws_frozen,
            site_id=ids["site_id"],
            delegator_id=ids["delegator_id"],
            claimant="c6-quiescent-freeze",
        )
        async with pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                    str(ws_frozen),
                )
                assert (
                    await connection.fetchval(
                        "SELECT status FROM control.workspace WHERE id = $1",
                        ws_frozen,
                    )
                    == "FREEZING"
                )
                doc = await connection.fetchval(
                    "SELECT control.slaif_review_workspace_state($1)",
                    ws_frozen,
                )
                row_doc = snapshot.build_snapshot_document(
                    doc,
                    created_by="c6-quiescent-freeze",
                    browser_evidence=[],
                    cancelled_runs=[],
                )
                await connection.fetchval(
                    "SELECT control.slaif_review_snapshot_complete($1, $2)",
                    ws_frozen,
                    snapshot.canonical_json(row_doc),
                )
                await connection.fetchval(
                    "SELECT control.slaif_review_job_terminal($1, 'SUCCEEDED', NULL)",
                    freeze_job_id,
                )
        snap_v2 = await _snapshot_row(database, ws_frozen)
        assert snap_v2 is not None
        assert str(snap_v2["status"]) == "COMPLETE"
        payload_v2 = snap_v2["payload"]
        if isinstance(payload_v2, str):
            payload_v2 = json.loads(payload_v2)
        assert payload_v2["state_version"] == "review-snapshot/v2"
        v2_snap_id = uuid.UUID(str(snap_v2["id"]))
        assert await _digest_is_valid(database, v2_snap_id)

        # Faithful base-era v1 document over the real site rows, built
        # with the genuine 075 contract (shape + canonical digest).
        doc = await _materialize_v1_document(database, ids["site_id"], ws_frozen)
        v1_row = _rc6_build_snapshot_document(doc, created_by="unit-worker")
        assert v1_row["digest"] == _rc6_canonical_digest(v1_row["payload"])
        await _seed_retained_snapshot_row(database, v1_row)

        # Real supported discard: pending COW cleared, both snapshot rows
        # retained, workspace terminal.
        discard_result = await _discard_claim_run(
            database,
            pool,
            workspace_id=ws_frozen,
            site_id=ids["site_id"],
            user_id=ids["delegator_id"],
        )
        assert discard_result.status == "SUCCEEDED", discard_result.error
        assert not await _content_operations(database, ws_frozen)
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            ws_status = await owner.fetchval(
                "SELECT status::text FROM control.workspace WHERE id = $1",
                ws_frozen,
            )
        assert ws_status == "DISCARDED"
    finally:
        await pool.close()

    # 077-era completions across ALL THREE families through the PRE-078
    # definer bodies (no journal exists yet).
    semantic_key = f"page-{uuid.uuid4().hex}"
    semantic_op = uuid.uuid4()
    await _agent_semantic_completion(
        database,
        ids,
        key=semantic_key,
        operation_id=semantic_op,
        action="PAGE_CREATED",
        resource_type="page",
        resource_id=canonical_page_id,
    )
    noeffect_key = f"theme-{uuid.uuid4().hex}"
    noeffect_op = uuid.uuid4()
    await _agent_no_effect_completion(
        database,
        ids,
        key=noeffect_key,
        operation_id=noeffect_op,
        resource_type="page",
        resource_id=canonical_page_id,
        status=200,
    )
    hfx = await _human_editor_fixture(database, ids["site_id"])
    human_op = uuid.uuid4()
    await _human_editor_completion(
        database,
        hfx,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=human_op,
        action="PAGE_UPDATED",
        resource_type="page",
        resource_id=canonical_page_id,
    )
    asset_id = uuid.uuid4()
    await _media_completion(
        database,
        hfx,
        key=f"media-{uuid.uuid4().hex}",
        operation_id=uuid.uuid4(),
        resource_id=asset_id,
    )

    history_before = await _family_history(database)
    (
        audit_before,
        human_audit_before,
        media_audit_before,
        agent_ledger_before,
        human_ledger_before,
        media_ledger_before,
        snapshots_before,
    ) = history_before
    # Nonempty fixtures across all three families plus retained snapshot.
    # Two agent audits: the semantic completion and the frozen
    # workspace's genuine COW component create; the explicit
    # no-effect completion leaves a ledger row but NO audit row.
    assert len(audit_before) == 2
    assert len(human_audit_before) == 1
    assert len(media_audit_before) == 1
    # Three agent idempotency rows: the two completion reservations
    # plus the frozen workspace's genuine COW component create.
    assert len(agent_ledger_before) == 3
    assert len(human_ledger_before) == 1
    assert len(media_ledger_before) == 1
    assert len(snapshots_before) == 2  # genuine v2 + faithful 075-contract v1
    # The explicit no-effect row: completed ledger, NO audit row. Named
    # 025 schema identity: ledger operation_id (5th column) and audit
    # operation_id (1st column), NOT the audit resource_type at [4].
    no_effect_rows = [
        row for row in agent_ledger_before if row["operation_id"] == noeffect_op
    ]
    assert len(no_effect_rows) == 1
    assert no_effect_rows[0]["status_code"] is not None  # completed shape
    agent_ops = {row["operation_id"] for row in audit_before}
    assert noeffect_op not in agent_ops
    canonical_before = await _canonical_history(database)
    snapshots_before_text = await _snapshot_rows_text(database)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        assert await connection.fetchval(
            f"SELECT to_regclass('{_JOURNAL_TABLE}') IS NULL"
        )

    # Normal quiescent operator upgrade to the released 078 head
    # (historical at this source; the 079 companion head is not reached).
    result = await _upgrade_historical(database, HISTORICAL_078_HEAD)
    assert result.safe
    assert result.revision == HISTORICAL_078_HEAD

    # ALL pre-078 history (audit, ledgers incl. no-effect, snapshot,
    # canonical) preserved byte-exact.
    history_after = await _family_history(database)
    assert history_after == history_before
    assert await _canonical_history(database) == canonical_before
    # Retained review snapshot rows byte-exact, validity re-verified with
    # each contract's own digest (v2: product canonicalization, v1: the
    # genuine 075 canonical serializer).
    assert await _snapshot_rows_text(database) == snapshots_before_text
    assert await _digest_is_valid(database, v2_snap_id)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        v1_rows_after = await connection.fetch(
            "SELECT payload, digest FROM control.review_snapshot "
            "WHERE workspace_id = $1 "
            "AND payload->>'state_version' = 'review-snapshot/v1'",
            ws_frozen,
        )
    assert len(v1_rows_after) == 1
    v1_payload_after = v1_rows_after[0]["payload"]
    if isinstance(v1_payload_after, str):
        v1_payload_after = json.loads(v1_payload_after)
    assert v1_rows_after[0]["digest"] == _rc6_canonical_digest(v1_payload_after)
    # No synthetic/backfilled journal rows for historical completions.
    assert await _journal_rows(database) == ()

    # Old idempotency replay still works (same key/digest; the SAME
    # actual request operation UUID names the COW context).
    digest = _digest(semantic_key, str(canonical_page_id))
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(connection, ids["workspace_id"], semantic_op)
            replay = await connection.fetchrow(
                "SELECT * FROM control.slaif_agent_idempotency_begin($1,$2,$3,$4,$5)",
                ids["capability_id"],
                ids["workspace_id"],
                semantic_key,
                digest,
                semantic_op,
            )
        assert replay is not None
        assert str(replay[0]) == "REPLAY"
        assert str(replay[1]) == str(semantic_op)

    # Forward (078-era) completions across families are recorded.
    forward_op = uuid.uuid4()
    await _agent_semantic_completion(
        database,
        ids,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=forward_op,
        action="PAGE_CREATED",
        resource_type="page",
        resource_id=uuid.uuid4(),
    )
    forward_human_op = uuid.uuid4()
    await _human_editor_completion(
        database,
        hfx,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=forward_human_op,
        action="PAGE_UPDATED",
        resource_type="page",
        resource_id=canonical_page_id,
    )
    journal = await _journal_rows(database)
    assert len(journal) == 2
    by_op = {row[0]: row for row in journal}
    agent_row = by_op[forward_op]
    assert agent_row[1] == "agent"
    assert agent_row[4] == ids["capability_id"]
    assert agent_row[5] is None
    assert agent_row[10] == "completed"
    human_row = by_op[forward_human_op]
    assert human_row[1] == "human_editor"
    assert human_row[4] is None
    assert human_row[5] == hfx["human_user_id"]
    assert human_row[10] == "completed"
    # Opaque request identity: 64-hex, never the raw key material.
    for row in journal:
        assert len(row[6]) == 64
        int(row[6], 16)
        int(row[7], 16)


async def test_upgrade_refuses_with_pending_cow_toward_078(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Pending-COW refusal from a real 077 head toward the current head.

    The fixture stays at the 077 stage: the operator upgrade's target is
    the current head (079_001 at this source), and the normal
    pending-work refusal fires before ANY migration step, so neither
    the 078 journal nor the 079 companion surface is created and the
    complete preexisting state is preserved.
    """
    database = agent_site_database
    token, ids = await _seed_077(database)
    del token

    # One real agent COW write that stays pending (operation registered,
    # no completion, no commit_cow_session).
    operation_id = uuid.uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(
                connection,
                ids["workspace_id"],
                operation_id,
                capability_id=ids["capability_id"],
            )
            row = await connection.fetchrow(
                "SELECT * FROM content.slaif_agent_page_create($1,$2,$3,$4,$5,$6,$7)",
                ids["site_id"],
                "pending-cow-page",
                "Pending COW page",
                "DRAFT",
                "en",
                None,
                None,
            )
            assert row is not None
    pending_before = await _pending_operation_ids(database, ids["workspace_id"])
    assert operation_id in pending_before
    before = await _full_state(database)
    assert before["revision"] == HISTORICAL_077_HEAD
    assert before["cow_enabled"] is True

    with pytest.raises(BootstrapStateError, match="pending COW operations"):
        await upgrade(database.settings)

    # Complete preexisting state exactly as found; the 078 head was never
    # reached and no journal object exists.
    after = await _full_state(database)
    _assert_state_equal(before, after)
    assert await _pending_operation_ids(database, ids["workspace_id"]) == pending_before
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        journal_present = await connection.fetchval(
            f"SELECT to_regclass('{_JOURNAL_TABLE}') IS NOT NULL"
        )
    assert journal_present is False


# ---------------------------------------------------------------------------
# 083/12-a: reviewed-operation binding (079_001) upgrade/downgrade.
# ---------------------------------------------------------------------------

HISTORICAL_078_HEAD = "078_001"
_MANIFEST_TABLE = "control.review_operation_manifest"
_MANIFEST_READ = "control.slaif_review_operation_manifest_read"


async def _seed_078(database: AgentSiteDatabase) -> tuple[str, dict[str, uuid.UUID]]:
    """Real released 078_001 head (journal present, companion absent)."""
    return await _seed(database, historical_head=HISTORICAL_078_HEAD)


async def _upgrade_historical(database: AgentSiteDatabase, head: str) -> Any:
    """Real upgrade to a released head plus real reconcile under the seam.

    The current 079-graph reconcile deliberately expects the current
    head; the narrow expected-head seam (test-only, no production gate
    change) lets the REAL production reconcile run against the released
    historical head.
    """
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision=head,
    )
    with _expected_head_override(head):
        return await reconcile(database.settings)


async def _manifest_row_count(database: AgentSiteDatabase) -> int:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        return int(await connection.fetchval(f"SELECT count(*) FROM {_MANIFEST_TABLE}"))


async def test_quiescent_078_to_079_upgrade_preserves_history(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """Quiescent 078 -> 079 keeps ALL pre-079 history and works forward.

    The pre-079 fixture is genuine 078-era state: real family
    completions through the 078 definer bodies (four journal rows
    including the explicit no-effect) plus a faithful 075-contract v1
    retained snapshot row over the real site rows in a separate
    quiescent workspace.  The upgrade preserves that history byte-exact,
    invents no journal rows, leaves the companion-less snapshot readable
    with a NULL manifest projection, and the product works forward: a
    real 079 freeze stores the companion and the real dual-digest
    accept promotes exactly.  The operator downgrade and the direct
    079_001 Alembic body both refuse before any effect.

    Bounded evidence: the 078-era freeze/accept workers predate this
    source (their completion call changed at 079), so the retained
    078-era snapshot is the faithful owner-seeded v1 row, not a
    078-worker-generated v2; the forward v2 + companion is real
    current-worker generated.
    """
    database = agent_site_database
    media_root = tmp_path / "media"
    token, ids = await _seed_078(database)
    del token

    canonical_page_id = uuid.uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "INSERT INTO content.page_base "
            "(id, site_id, slug, title, status, locale) "
            "VALUES ($1, $2, 'binding-canonical', 'Binding canonical', "
            "'DRAFT', 'en')",
            canonical_page_id,
            ids["site_id"],
        )

    # --- Separate quiescent workspace: faithful retained v1 history ---
    frozen_page_id = uuid.uuid4()
    frozen_section_id = uuid.uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        ws_frozen, _cap_frozen = await _create_workspace(
            owner,
            ids["site_id"],
            ids["delegator_id"],
            "083/12-a binding quiescent freeze",
        )
        await owner.execute(
            "INSERT INTO content.page_base (id, site_id, slug, title, status,"
            " locale) VALUES ($1, $2, 'binding-frozen', 'Binding frozen',"
            " 'PUBLISHED', 'en-US')",
            frozen_page_id,
            ids["site_id"],
        )
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES ($1, $2, $3, 'Section', '1', NULL, 'default', 0,"
            " '{}'::jsonb)",
            frozen_section_id,
            ids["site_id"],
            frozen_page_id,
        )
    doc = await _materialize_v1_document(database, ids["site_id"], ws_frozen)
    v1_row = _rc6_build_snapshot_document(doc, created_by="unit-worker")
    assert v1_row["digest"] == _rc6_canonical_digest(v1_row["payload"])
    await _seed_retained_snapshot_row(database, v1_row)
    v1_snap_id: uuid.UUID | None = None
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        v1_snap_id = await owner.fetchval(
            "SELECT id FROM control.review_snapshot WHERE workspace_id = $1",
            ws_frozen,
        )
    assert v1_snap_id is not None

    # 078-era completions across ALL THREE families through the 078
    # definer bodies (journal rows exist now).
    semantic_key = f"page-{uuid.uuid4().hex}"
    semantic_op = uuid.uuid4()
    await _agent_semantic_completion(
        database,
        ids,
        key=semantic_key,
        operation_id=semantic_op,
        action="PAGE_CREATED",
        resource_type="page",
        resource_id=canonical_page_id,
    )
    noeffect_key = f"theme-{uuid.uuid4().hex}"
    noeffect_op = uuid.uuid4()
    await _agent_no_effect_completion(
        database,
        ids,
        key=noeffect_key,
        operation_id=noeffect_op,
        resource_type="page",
        resource_id=canonical_page_id,
        status=200,
    )
    hfx = await _human_editor_fixture(database, ids["site_id"])
    human_op = uuid.uuid4()
    await _human_editor_completion(
        database,
        hfx,
        key=f"page-{uuid.uuid4().hex}",
        operation_id=human_op,
        action="PAGE_UPDATED",
        resource_type="page",
        resource_id=canonical_page_id,
    )
    media_op = uuid.uuid4()
    await _media_completion(
        database,
        hfx,
        key=f"media-{uuid.uuid4().hex}",
        operation_id=media_op,
        resource_id=uuid.uuid4(),
    )

    journal_before = await _journal_rows(database)
    assert len(journal_before) == 4
    history_before = await _family_history(database)
    canonical_before = await _canonical_history(database)
    snapshots_before_text = await _snapshot_rows_text(database)
    before = await _full_state(database)
    assert before["revision"] == HISTORICAL_078_HEAD
    assert before["cow_enabled"] is True
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        manifest_absent = await connection.fetchval(
            f"SELECT to_regclass('{_MANIFEST_TABLE}') IS NULL"
        )
    assert manifest_absent is True

    # Normal quiescent operator upgrade to the 079 head.
    await upgrade(database.settings)
    result = await reconcile(database.settings)
    assert result.safe
    assert result.revision == "079_001"

    # ALL pre-079 history preserved byte-exact; no synthetic journal.
    assert await _family_history(database) == history_before
    assert await _canonical_history(database) == canonical_before
    assert await _snapshot_rows_text(database) == snapshots_before_text
    assert await _journal_rows(database) == journal_before
    # The companion surface exists and is empty; the historical
    # companion-less snapshot stays readable with a NULL projection.
    assert await _manifest_row_count(database) == 0
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        legacy_read = await connection.fetchval(
            f"SELECT {_MANIFEST_READ}($1)", v1_snap_id
        )
    assert legacy_read is None

    # Forward at 079: a real freeze stores the companion and the real
    # dual-digest accept promotes exactly.
    # A real agent HTTP page create (full trusted completion: the
    # operation is pending COW but carries its 078 journal identity,
    # which the 079 companion requires for every U member).
    token_forward, ws_forward, _cap_forward = await _seed_agent_workspace(
        database,
        ids["site_id"],
        ids["delegator_id"],
        ["site:read", "page:create", "page:read"],
        "083/12-a binding forward workspace",
    )
    async with _agent_client(database) as client:
        created = await _create_page(
            client, token_forward, key="bf-fwd-page", slug="bf-fwd-page"
        )
        assert created.status_code == 201, created.text
        forward_op = uuid.UUID(created.json()["operation_id"])
    assert await _content_operations(database, ws_forward) == [forward_op]

    pool = await _worker_pool(database)
    try:
        freeze_result, _freeze_job = await _freeze_claim_run(
            database,
            workspace_id=ws_forward,
            site_id=ids["site_id"],
            delegator_id=ids["delegator_id"],
            pool=pool,
            claimant="c6-079-forward-freeze",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result.error
        snap_forward = await _snapshot_row(database, ws_forward)
        assert snap_forward is not None
        assert str(snap_forward["status"]) == "COMPLETE"
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            manifest_row = await owner.fetchrow(
                f"SELECT * FROM {_MANIFEST_TABLE} WHERE snapshot_id = $1",
                snap_forward["id"],
            )
        assert manifest_row is not None
        assert [str(o) for o in manifest_row["operation_ids"]] == [str(forward_op)]
        assert await _manifest_row_count(database) == 1

        enqueued = await _enqueue_bound_accept(
            database, ws_forward, ids["delegator_id"]
        )
        job = await _claim_accept(database, "c6-079-forward-accept")
        assert str(job["id"]) == str(enqueued[0]["job_id"])
        boundary = MediaBoundary(settings=_media_settings(database, media_root))
        accept_result = await run_accept_job(
            pool, _worker_settings(database), job, media=boundary
        )
        assert accept_result.status == "SUCCEEDED", accept_result.error
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            audit = await owner.fetch(
                "SELECT * FROM audit.promotion WHERE workspace_id = $1",
                ws_forward,
            )
            ws_status = await owner.fetchval(
                "SELECT status::text FROM control.workspace WHERE id = $1",
                ws_forward,
            )
        assert len(audit) == 1
        assert [str(o) for o in audit[0]["applied_operation_ids"]] == [str(forward_op)]
        assert str(audit[0]["manifest_id"]) == str(manifest_row["id"])
        assert str(audit[0]["manifest_digest"]) == str(manifest_row["manifest_digest"])
        assert ws_status == "ACCEPTED"
        # The forward completion joins the journal: the four 078-era
        # rows stay byte-exact under their operation IDs (the journal
        # orders by operation_id, so the new row may interleave) and
        # exactly one new row, the forward completion, was added.
        journal_after = await _journal_rows(database)
        assert len(journal_after) == 5
        by_op = {row[0]: row for row in journal_after}
        historical_ops = tuple(row[0] for row in journal_before)
        assert tuple(by_op[op] for op in historical_ops) == journal_before
        assert set(by_op) == set(historical_ops) | {forward_op}
        # Historical companion-less snapshot still has no companion.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as connection:
            legacy_read = await connection.fetchval(
                f"SELECT {_MANIFEST_READ}($1)", v1_snap_id
            )
        assert legacy_read is None
        assert await _pending_operation_ids(database, ws_forward) == []
    finally:
        await pool.close()

    # Operator downgrade: refused BEFORE any effect.
    before_refusal = await _full_state(database)
    with pytest.raises(BootstrapStateError, match="reviewed operation binding"):
        await downgrade(database.settings)
    after_refusal = await _full_state(database)
    _assert_state_equal(before_refusal, after_refusal)
    assert after_refusal["revision"] == "079_001"

    # Direct 079_001 Alembic body: the second line of defense.
    with pytest.raises(sqlalchemy_exc.DBAPIError) as exc_info:
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="078_001",
        )
    underlying = exc_info.value.orig
    assert "REVIEWED_OPERATION_BINDING_DOWNGRADE_REFUSED" in str(underlying)
    assert getattr(underlying, "sqlstate", None) == "P0001"
    after_direct = await _full_state(database)
    _assert_state_equal(before_refusal, after_direct)
    assert await _journal_rows(database) == journal_after


async def test_upgrade_refuses_with_pending_cow_toward_079(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Pending-COW refusal from a real 078 head toward the 079 target.

    The fixture stays at the 078 stage: the normal pending-work refusal
    fires before the 079 head is reached, preserving the complete
    preexisting state and the 078-era journal bytes.
    """
    database = agent_site_database
    token, ids = await _seed_078(database)
    del token

    # One real agent COW write that stays pending.
    operation_id = uuid.uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        async with connection.transaction():
            await _set_cow_gucs(
                connection,
                ids["workspace_id"],
                operation_id,
                capability_id=ids["capability_id"],
            )
            row = await connection.fetchrow(
                "SELECT * FROM content.slaif_agent_page_create($1,$2,$3,$4,$5,$6,$7)",
                ids["site_id"],
                "binding-pending-page",
                "Binding pending page",
                "DRAFT",
                "en",
                None,
                None,
            )
            assert row is not None
    pending_before = await _pending_operation_ids(database, ids["workspace_id"])
    assert operation_id in pending_before
    journal_before = await _journal_rows(database)
    before = await _full_state(database)
    assert before["revision"] == HISTORICAL_078_HEAD
    assert before["cow_enabled"] is True

    with pytest.raises(BootstrapStateError, match="pending COW operations"):
        await upgrade(database.settings)

    # Complete preexisting state exactly as found; the 079 head was
    # never reached and the companion surface does not exist.
    after = await _full_state(database)
    _assert_state_equal(before, after)
    assert await _pending_operation_ids(database, ids["workspace_id"]) == pending_before
    assert await _journal_rows(database) == journal_before
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        manifest_absent = await connection.fetchval(
            f"SELECT to_regclass('{_MANIFEST_TABLE}') IS NULL"
        )
    assert manifest_absent is True

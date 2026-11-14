"""C3 security evidence for the 083/12-a reviewed-operation binding
(079_001): the immutable companion table and the 078 journal boundary
at the 079 head, the exact EXECUTE allow matrix of the new 079
surface, the non-bypassability of the dropped old accept entry
points, the R2 discarded-history provenance semantics (legal
completed history outside U stays honest; conflicting prospective
facts refuse; old unknown history is never demanded or re-dated), the
trusted completion definer's typed envelope refusals, and the
null-safe live-ACCEPT-job payload refusal of 072-era legacy payloads.

Bounded C3 evidence subset (real PG, real provisioned logins for
worker/control actions, no mocks): it does not claim C1/C2 positive
accept, C4/C5/C6, the 079 worker consumer, or full-gate acceptance.

Fixture honesty:
- Role pools (``database.role_pool``) are fixture LOGIN + SET ROLE
  and are labeled as fixtures; the worker/control actions in the
  runtime cells run on the REAL provisioned logins
  (``database.credentials``) with no SET ROLE.  The disposable
  cluster uses trust authentication, so login names are
  LOGIN-identity proofs, not credential-authentication proofs.
- Every owner-created row that stands in for historical or legacy
  state (the legacy ACCEPT job payload, the lone pre-078
  reservation, the mismatched counterparts) is a labeled trusted
  negative/legacy fixture; the companion manifest and the REVIEW
  snapshot in the legacy-payload test are produced by the real 079
  worker definer, never inserted by the owner.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    get_operation_dependencies,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.review_worker import freeze_job, snapshot
from test_agent_mutations import _seed
from test_agent_theme_boundaries import _agent_client
from test_mutation_completion_authority import (
    _JOURNAL_ROW_SQL,
    _JOURNAL_TABLE,
    _M078,
)
from test_real_human_accept import (
    _WORKER_KINDS,
    _dsn,
    _worker_settings,
)
from test_trusted_completion_late_failure import _request_headers
from test_trusted_completion_producer_families import (
    _AGENT_MODEL_SCOPES,
    _seed_agent_workspace,
)

# Bound to the real 079_001 migration source: its names are the surface
# under test (the same pattern the 078 module uses for _M078).
_M079 = importlib.import_module(
    "slaif_agent_site.db.alembic.versions.079_001_reviewed_operation_binding"
)

assert _M078 is not None  # the 078 module import is the journal binding

_MANIFEST_TABLE = "control.review_operation_manifest"
_JOURNAL_HELPER = "control.slaif_mutation_completion_record"

_ROLES: tuple[str, ...] = tuple(_M079._LONG_LIVED_ROLES)

# regproc forms (for to_regprocedure / has_function_privilege), exactly
# as the 079 migration spells them.
_IDENTITIES_FUNCTION = _M079._IDENTITIES_FUNCTION
_PROVENANCE_FUNCTION = _M079._PROVENANCE_FUNCTION
_COMPLETE_WITH_MANIFEST_FUNCTION = _M079._COMPLETE_WITH_MANIFEST_FUNCTION
_MANIFEST_READ_FUNCTION = _M079._MANIFEST_READ_FUNCTION
_STANDALONE_COMPLETE_FUNCTION = _M079._STANDALONE_COMPLETE_FUNCTION
_OLD_HUMAN_ACCEPT_FUNCTION = _M079._OLD_HUMAN_ACCEPT_FUNCTION
_OLD_INNER_ACCEPT_FUNCTION = _M079._OLD_INNER_ACCEPT_FUNCTION
_NEW_INNER_ACCEPT_FUNCTION = _M079._INNER_ACCEPT_FUNCTION
_NEW_HUMAN_ACCEPT_FUNCTION = _M079._HUMAN_ACCEPT_FUNCTION


def _jsonb(value: Any) -> Any:
    """Decode fixture-connection JSONB text (canonical byte retention)."""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


# Bare names for real SQL calls.
_IDENTITIES_CALL = "control.slaif_review_operation_identities"
_PROVENANCE_CALL = "control.slaif_review_operation_provenance"
_COMPLETE_WITH_MANIFEST_CALL = "control.slaif_review_snapshot_complete_with_manifest"
_MANIFEST_READ_CALL = "control.slaif_review_operation_manifest_read"
_STANDALONE_COMPLETE_CALL = "control.slaif_review_snapshot_complete"

# The exact 079 EXECUTE allow matrix (bound to the migration's GRANT
# statements and the 079 phase in db.privileges): which long-lived role
# may EXECUTE each 079-era function at the 079 head.
_EXPECTED_EXECUTE: dict[str, frozenset[str]] = {
    _IDENTITIES_FUNCTION: frozenset({"slaif_review_worker"}),
    _PROVENANCE_FUNCTION: frozenset({"slaif_review_worker"}),
    _COMPLETE_WITH_MANIFEST_FUNCTION: frozenset({"slaif_review_worker"}),
    _MANIFEST_READ_FUNCTION: frozenset({"slaif_control", "slaif_review_worker"}),
    # 079 revokes the last online EXECUTE of the standalone completion
    # (it remains deployed and definer-reachable only).
    _STANDALONE_COMPLETE_FUNCTION: frozenset(),
    # The new inner enqueue is owner-internal: NO role EXECUTE grants.
    _NEW_INNER_ACCEPT_FUNCTION: frozenset(),
    # The new human entry point: control only (the definer inner is
    # reached by it as owner).
    _NEW_HUMAN_ACCEPT_FUNCTION: frozenset({"slaif_control"}),
}

# The real 072-era ACCEPT job payload shape (3 keys, no digests) - the
# legacy shape that a pre-079 enqueue would have stored.
_LEGACY_PAYLOAD_KEYS = ("snapshot_id", "site_id", "actor_user_account_id")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


async def _owner(database: AgentSiteDatabase) -> Any:
    return owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    )


async def _assert_079_head(database: AgentSiteDatabase) -> None:
    """upgrade + reconcile to the real current head, then bind the phase."""
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with await _owner(database) as owner:
        head = await owner.fetch("SELECT version_num FROM control.alembic_version")
    assert len(head) == 1, "single alembic chain expected"
    assert head[0]["version_num"] == "079_001", (
        f"this module binds to the 079 head, observed {head[0]['version_num']}"
    )


async def _real_login(database: AgentSiteDatabase, role: str) -> asyncpg.Connection:
    """One connection on the REAL provisioned login for the privilege
    role (no SET ROLE): the production identity for worker/control
    actions in this module (LOGIN-identity proof under fixture trust
    auth)."""
    login, password = database.credentials[role]
    return await asyncpg.connect(dsn=_dsn(database, login, password))


async def _close(connection: asyncpg.Connection | None) -> None:
    if connection is not None:
        await connection.close()


async def _agent_type_create(
    client: Any, token: str, *, key: str, label: str
) -> tuple[UUID, UUID]:
    """Real HTTP agent content-type create (201); (operation, record)."""
    created = await client.post(
        "/api/agent/v1/content-model/types",
        json={
            "key": key,
            "labels": {"en": label},
            "slug_pattern": f"/{key}s/{{slug}}",
            "settings": {"editor": "bounded"},
        },
        headers=_request_headers(token, key),
    )
    assert created.status_code == 201, created.text
    result = created.json()
    return UUID(result["operation_id"]), UUID(result["record"]["id"])


async def _public_universe(
    database: AgentSiteDatabase, workspace_id: UUID
) -> tuple[list[UUID], list[tuple[UUID, UUID]]]:
    """Public 0.2.1 getters on a clean owner connection (no COW GUCs)."""
    async with await _owner(database) as owner:
        executor = AsyncpgExecutor(owner)
        operations = await get_session_operations(
            executor, workspace_id, schema="content"
        )
        dependencies = await get_operation_dependencies(
            executor, workspace_id, schema="content"
        )
    return operations, dependencies


def _envelope(
    *,
    site_id: UUID,
    workspace_id: UUID,
    operation_ids: list[UUID],
    dependency_pairs: list[tuple[UUID, UUID]],
    completion_identities: list[dict[str, str]],
) -> dict[str, Any]:
    """The exact 6-key manifest envelope (079 contract)."""
    return {
        "schema_version": "reviewed-operations/v1",
        "site_id": str(site_id),
        "workspace_id": str(workspace_id),
        "operation_ids": [str(op) for op in operation_ids],
        "dependency_pairs": [
            [str(depends_on), str(operation_id)]
            for depends_on, operation_id in dependency_pairs
        ],
        "completion_identities": completion_identities,
    }


async def _worker_identities(
    worker: asyncpg.Connection,
    workspace_id: UUID,
    site_id: UUID,
    operation_ids: list[UUID],
) -> list[dict[str, Any]]:
    """The real worker-executed 078 identity projection (9 fields/op)."""
    raw = await worker.fetchrow(
        f"SELECT {_IDENTITIES_CALL}($1, $2, $3::uuid[])",
        workspace_id,
        site_id,
        [str(op) for op in operation_ids],
    )
    doc = raw[0]
    if isinstance(doc, (bytes, bytearray)):
        doc = doc.decode("utf-8")
    if isinstance(doc, str):
        doc = json.loads(doc)
    return [dict(record) for record in doc]


async def _run_provenance(
    worker: asyncpg.Connection,
    workspace_id: UUID,
    site_id: UUID,
    operation_ids: list[UUID],
) -> None:
    await worker.execute(
        f"SELECT {_PROVENANCE_CALL}($1, $2, $3::uuid[])",
        workspace_id,
        site_id,
        [str(op) for op in operation_ids],
    )


async def _freeze_and_claim(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    user_id: UUID,
    claimant: str,
) -> UUID:
    """Real freeze entry (control login) + real kind-aware claim (worker
    login); returns the claimed FREEZE job id."""
    control = await _real_login(database, "slaif_control")
    worker = await _real_login(database, "slaif_review_worker")
    try:
        row = await control.fetchrow(
            "SELECT * FROM control.slaif_human_agent_workspace_freeze($1, $2, $3)",
            workspace_id,
            site_id,
            user_id,
        )
        assert row is not None and row["status"] == "FREEZING", (
            "real freeze entry did not return FREEZING"
        )
        claimed = await worker.fetchrow(
            "SELECT * FROM control.slaif_review_job_claim($1, $2)",
            claimant,
            _WORKER_KINDS,
        )
        assert claimed is not None, "worker claim returned no job"
        assert str(claimed["workspace_id"]) == str(workspace_id)
        assert claimed["job_kind"] == "FREEZE"
        return UUID(str(claimed["id"]))
    finally:
        await _close(control)
        await _close(worker)


async def _worker_complete_with_manifest(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    site_id: UUID,
    job_id: UUID,
    claimant: str,
    operations: list[UUID],
    dependency_pairs: list[tuple[UUID, UUID]],
) -> UUID:
    """ONE caller-owned worker TX (real worker login, no SET ROLE)
    through the real 079 trusted completion: exclusive workspace lock,
    FREEZING recheck, real browser-run drain, the 076 materializer, the
    real 079 complete-with-manifest definer, and the job terminal.
    Returns the stored snapshot id."""
    worker = await _real_login(database, "slaif_review_worker")
    try:
        identities = await _worker_identities(worker, workspace_id, site_id, operations)
        envelope = _envelope(
            site_id=site_id,
            workspace_id=workspace_id,
            operation_ids=operations,
            dependency_pairs=dependency_pairs,
            completion_identities=identities,
        )
        settings = _worker_settings(database)
        async with worker.transaction():
            await worker.execute("SET LOCAL lock_timeout = '30s'")
            await worker.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                str(workspace_id),
            )
            status = await worker.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1",
                workspace_id,
            )
            assert status == "FREEZING"
            evidence, cancelled = await freeze_job._drain_browser_runs(
                worker, workspace_id, settings
            )
            assert evidence == [] and cancelled == []
            doc = await worker.fetchval(
                "SELECT control.slaif_review_workspace_state($1)",
                workspace_id,
            )
            row_doc = snapshot.build_snapshot_document(
                doc,
                created_by=claimant,
                browser_evidence=evidence,
                cancelled_runs=cancelled,
            )
            snapshot_id = await worker.fetchval(
                f"SELECT {_COMPLETE_WITH_MANIFEST_CALL}($1, $2::jsonb, $3::jsonb)",
                workspace_id,
                snapshot.canonical_json(row_doc),
                json.dumps(envelope),
            )
            await worker.fetchval(
                "SELECT control.slaif_review_job_terminal($1, 'SUCCEEDED', NULL)",
                job_id,
            )
        return UUID(str(snapshot_id))
    finally:
        await _close(worker)


async def _seed_r2_site(
    database: AgentSiteDatabase, title: str
) -> tuple[dict[str, UUID], str, UUID, UUID]:
    """Real base site + one genuine AGENT workspace;
    returns (seed, token, workspace_id, capability_id)."""
    _token, seeded = await _seed(database)
    token, workspace_id, capability_id = await _seed_agent_workspace(
        database,
        seeded["site_id"],
        seeded["delegator_id"],
        _AGENT_MODEL_SCOPES,
        title,
    )
    return seeded, token, workspace_id, capability_id


# ----------------------------------------------------------------------
# 1. Companion table + journal boundary at the 079 head
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manifest_table_and_journal_denied_at_079_head(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Owner-only companion table; 078 journal boundary unchanged at 079."""
    database = agent_site_database
    await _assert_079_head(database)
    assert len(_ROLES) == 10
    table_probes = (
        (
            "SELECT",
            f"SELECT count(*) FROM {_MANIFEST_TABLE}",
        ),
        (
            "INSERT",
            f"INSERT INTO {_MANIFEST_TABLE} "
            "(snapshot_id, site_id, workspace_id, schema_version, "
            "snapshot_digest, manifest_digest, operation_ids, "
            "dependency_pairs, completion_identities) "
            "VALUES (gen_random_uuid(), gen_random_uuid(), "
            "gen_random_uuid(), 'reviewed-operations/v1', repeat('0', 64), "
            "repeat('0', 64), '{}', '[]'::jsonb, '[]'::jsonb)",
        ),
        (
            "UPDATE",
            f"UPDATE {_MANIFEST_TABLE} SET schema_version = "
            "'reviewed-operations/v1' WHERE id = gen_random_uuid()",
        ),
        (
            "DELETE",
            f"DELETE FROM {_MANIFEST_TABLE} WHERE id = gen_random_uuid()",
        ),
        ("TRUNCATE", f"TRUNCATE {_MANIFEST_TABLE}"),
    )
    journal_probes = (
        (
            "JOURNAL SELECT",
            f"SELECT count(*) FROM {_JOURNAL_TABLE}",
        ),
        (
            "JOURNAL HELPER EXECUTE",
            f"SELECT {_JOURNAL_HELPER}(gen_random_uuid(), 'agent', "
            "gen_random_uuid(), gen_random_uuid(), gen_random_uuid(), "
            "NULL, 'binding-probe', repeat('0', 64), 'page', "
            "gen_random_uuid(), 'completed')",
        ),
    )
    for role in _ROLES:
        pool = await database.role_pool(role)
        try:
            async with pool.acquire() as connection:
                assert await connection.fetchval("SELECT current_user::text") == role
                for verb, sql in (*table_probes, *journal_probes):
                    with pytest.raises(asyncpg.InsufficientPrivilegeError) as err:
                        await connection.execute(sql)
                    assert err.value.sqlstate == "42501", (role, verb)
        finally:
            await pool.close()
    # PUBLIC is an ACL grantee, never a login fixture: check the ACL
    # directly (the has_*_privilege functions do not resolve the PUBLIC
    # pseudo-role as a user name on PostgreSQL 18).
    async with await _owner(database) as owner:
        for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            public_granted = await owner.fetchval(
                "SELECT EXISTS ("
                "SELECT 1 FROM aclexplode(p.relacl) a"
                " WHERE a.grantee = 0 AND a.privilege_type = $1)"
                " FROM pg_class p JOIN pg_namespace n"
                " ON n.oid = p.relnamespace"
                " WHERE n.nspname = 'control'"
                " AND p.relname = 'review_operation_manifest'",
                privilege,
            )
            assert public_granted is False, (privilege, "PUBLIC table grant")
    # Trusted owner reads the actual outcome.
    async with await _owner(database) as owner:
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'control' "
                "AND table_name = 'review_operation_manifest'"
            )
            == 1
        )
        assert await owner.fetchval(f"SELECT count(*) FROM {_MANIFEST_TABLE}") == 0, (
            "denied probes must leave the companion table empty"
        )
        assert await owner.fetchval(f"SELECT count(*) FROM {_JOURNAL_TABLE}") == 0


# ----------------------------------------------------------------------
# 2. Exact EXECUTE allow matrix for the 079 surface
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reviewed_operation_surface_allow_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Worker-only projections/completion; control read; nothing else."""
    database = agent_site_database
    await _assert_079_head(database)
    seeded, _token, workspace_id, _capability_id = await _seed_r2_site(
        database, "binding allow matrix ws"
    )
    site_id = seeded["site_id"]
    async with await _owner(database) as owner:
        for function, allowed_roles in _EXPECTED_EXECUTE.items():
            # Functions default to PUBLIC EXECUTE while proacl is NULL:
            # the revoke sweep must have installed an explicit ACL with
            # no PUBLIC EXECUTE entry (grantee oid 0).
            public_granted = await owner.fetchval(
                "SELECT p.proacl IS NULL OR EXISTS ("
                "SELECT 1 FROM aclexplode(p.proacl) a"
                " WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE')"
                " FROM pg_proc p JOIN pg_namespace n"
                " ON n.oid = p.pronamespace"
                " WHERE n.nspname = 'control'"
                " AND p.oid = to_regprocedure($1)",
                function,
            )
            assert public_granted is False, (
                function,
                "PUBLIC must never be an EXECUTE grantee",
            )
            for role in _ROLES:
                granted = await owner.fetchval(
                    "SELECT has_function_privilege($1::regrole,"
                    " to_regprocedure($2), 'EXECUTE')",
                    role,
                    function,
                )
                assert granted is (role in allowed_roles), (
                    function,
                    role,
                    granted,
                )
    # Real runtime EXECUTEs: the allowed cells are live, the denied
    # cells are refused at execution, not only in the ACL.
    worker = await _real_login(database, "slaif_review_worker")
    control = await _real_login(database, "slaif_control")
    try:
        # Allowed: the worker identity projection on the real workspace
        # (empty U -> empty array).
        assert await _worker_identities(worker, workspace_id, site_id, []) == []
        # Allowed: the worker manifest read projection (no row -> NULL).
        read_row = await worker.fetchrow(
            f"SELECT {_MANIFEST_READ_CALL}(gen_random_uuid())"
        )
        assert read_row[0] is None
        # Allowed: the worker provenance check on the real workspace
        # with an empty U (no prospective facts to check -> passes).
        await _run_provenance(worker, workspace_id, site_id, [])
        # Allowed: the control manifest read projection (no row -> NULL).
        control_read = await control.fetchrow(
            f"SELECT {_MANIFEST_READ_CALL}(gen_random_uuid())"
        )
        assert control_read[0] is None
        # Denied at runtime (not only in the ACL): control on the
        # worker-only surface.
        for sql, args in (
            (
                f"SELECT {_IDENTITIES_CALL}($1, $2, '{{}}'::uuid[])",
                (workspace_id, site_id),
            ),
            (
                f"SELECT {_PROVENANCE_CALL}($1, $2, '{{}}'::uuid[])",
                (workspace_id, site_id),
            ),
            (
                f"SELECT {_COMPLETE_WITH_MANIFEST_CALL}"
                "($1, '{}'::jsonb, '{}'::jsonb)",
                (workspace_id,),
            ),
        ):
            with pytest.raises(asyncpg.InsufficientPrivilegeError) as err:
                await control.execute(sql, *args)
            assert err.value.sqlstate == "42501"
        # Denied at runtime: reviewer on the control-read projection
        # (fixture role pool).
        reviewer_pool = await database.role_pool("slaif_reviewer")
        try:
            async with reviewer_pool.acquire() as connection:
                with pytest.raises(asyncpg.InsufficientPrivilegeError) as err:
                    await connection.execute(
                        f"SELECT {_MANIFEST_READ_CALL}($1)", uuid4()
                    )
                assert err.value.sqlstate == "42501"
        finally:
            await reviewer_pool.close()
    finally:
        await _close(worker)
        await _close(control)


# ----------------------------------------------------------------------
# 3. Old accept entry points: absent => nonbypassable
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_old_accept_entry_points_nonbypassable(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The old 5-arg human and 2-arg inner accepts are gone at 079."""
    database = agent_site_database
    await _assert_079_head(database)
    async with await _owner(database) as owner:
        old_human = await owner.fetchval(
            "SELECT to_regprocedure($1)", _OLD_HUMAN_ACCEPT_FUNCTION
        )
        old_inner = await owner.fetchval(
            "SELECT to_regprocedure($1)", _OLD_INNER_ACCEPT_FUNCTION
        )
        new_human = await owner.fetchval(
            "SELECT to_regprocedure($1)", _NEW_HUMAN_ACCEPT_FUNCTION
        )
        new_inner = await owner.fetchval(
            "SELECT to_regprocedure($1)", _NEW_INNER_ACCEPT_FUNCTION
        )
    assert old_human is None, "old 5-arg human accept must be dropped"
    assert old_inner is None, "old 2-arg inner accept must be dropped"
    assert new_human is not None, "new 6-arg human accept must exist"
    assert new_inner is not None, "new 5-arg inner accept must exist"
    # A real old-shape call cannot enqueue or accept: the entry point
    # does not resolve at all (no actorless legacy path remains).
    control = await _real_login(database, "slaif_control")
    try:
        with pytest.raises(asyncpg.UndefinedFunctionError) as err:
            await control.fetchrow(
                "SELECT * FROM control.slaif_workspace_accept($1, $2)",
                uuid4(),
                uuid4(),
            )
        assert err.value.sqlstate == "42883"
        with pytest.raises(asyncpg.UndefinedFunctionError) as err:
            await control.fetchrow(
                "SELECT * FROM control.slaif_human_agent_workspace_accept"
                "($1, $2, $3, $4, $5)",
                uuid4(),
                uuid4(),
                uuid4(),
                "ab" * 32,
                uuid4(),
            )
        assert err.value.sqlstate == "42883"
    finally:
        await _close(control)
    # A second real reconcile at the 079 head must not restore the old
    # surface, re-grant the standalone completion, or leak anything.
    await reconcile(database.settings)
    async with await _owner(database) as owner:
        assert (
            await owner.fetchval(
                "SELECT to_regprocedure($1)", _OLD_HUMAN_ACCEPT_FUNCTION
            )
            is None
        )
        assert (
            await owner.fetchval(
                "SELECT to_regprocedure($1)", _OLD_INNER_ACCEPT_FUNCTION
            )
            is None
        )
        for function, allowed_roles in _EXPECTED_EXECUTE.items():
            for role in _ROLES:
                granted = await owner.fetchval(
                    "SELECT has_function_privilege($1::regrole,"
                    " to_regprocedure($2), 'EXECUTE')",
                    role,
                    function,
                )
                assert granted is (role in allowed_roles), (
                    "reconcile drifted the 079 surface",
                    function,
                    role,
                )
    # The revoked standalone completion cannot be executed by the
    # worker even after the second reconcile.
    worker = await _real_login(database, "slaif_review_worker")
    try:
        with pytest.raises(asyncpg.InsufficientPrivilegeError) as err:
            await worker.execute(
                f"SELECT {_STANDALONE_COMPLETE_CALL}($1, $2::jsonb)",
                uuid4(),
                json.dumps({"schema_version": "review-snapshot/v2"}),
            )
        assert err.value.sqlstate == "42501"
    finally:
        await _close(worker)


# ----------------------------------------------------------------------
# 4. R2: discarded history outside U stays honest; mismatches refuse
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_r2_discarded_history_provenance(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Real HTTP A+B; real public discard of A; provenance over U={B}."""
    database = agent_site_database
    await _assert_079_head(database)
    seeded, token, workspace_id, capability_id = await _seed_r2_site(
        database, "binding r2 ws"
    )
    site_id = seeded["site_id"]
    op_a: UUID
    op_b: UUID
    async with _agent_client(database) as client:
        op_a, _type_a = await _agent_type_create(
            client, token, key="r2-a", label="R2 A"
        )
        op_b, _type_b = await _agent_type_create(
            client, token, key="r2-b", label="R2 B"
        )
    # Both real HTTP completions are pending in U and fully journaled.
    operations, _dependencies = await _public_universe(database, workspace_id)
    assert set(operations) == {op_a, op_b}
    async with await _owner(database) as owner:
        for operation_id in (op_a, op_b):
            journal = await owner.fetchrow(_JOURNAL_ROW_SQL, operation_id)
            assert journal is not None, (
                f"completed operation {operation_id} must be journaled"
            )
            assert journal["family"] == "agent"
            assert journal["disposition"] == "completed"
            assert journal["site_id"] == site_id
            assert journal["workspace_id"] == workspace_id
    # The REAL public 0.2.1 foundation discard (reviewer authority):
    # A leaves the pending universe; B remains.
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            result = await reviewer.discard_operations(
                workspace_id, [op_a], schema="content"
            )
        assert result.no_op is False
        assert result.discarded_operations == (op_a,)
        assert result.has_pending_operations is True
    finally:
        await reviewer_pool.close()
    operations, _dependencies_after = await _public_universe(database, workspace_id)
    assert set(operations) == {op_b}, (
        "the discarded operation must leave U; B must stay pending"
    )
    # A's genuine 078 history is retained by the discard.
    async with await _owner(database) as owner:
        journal_a = await owner.fetchrow(_JOURNAL_ROW_SQL, op_a)
        assert journal_a is not None, "discard must retain A's 078 journal"
        assert journal_a["disposition"] == "completed"
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM audit.agent_mutation WHERE operation_id = $1",
                op_a,
            )
            == 1
        ), "discard must retain A's family audit row"
        reservation_a = await owner.fetchrow(
            "SELECT status_code, resource_type "
            "FROM control.agent_idempotency "
            "WHERE operation_id = $1 AND workspace_id = $2",
            op_a,
            workspace_id,
        )
        assert reservation_a is not None
        assert reservation_a["status_code"] == 201
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM content.content_type_base WHERE site_id = $1",
                site_id,
            )
            == 0
        ), "pre-freeze: the discarded overlay never reaches canonical"
    worker = await _real_login(database, "slaif_review_worker")
    try:
        # The legal case: A outside U is honest history; provenance
        # over U={B} must PASS.
        await _run_provenance(worker, workspace_id, site_id, [op_b])
        # The worker identity projection for U={B} is exactly B's real
        # 078 identity (the nine fields, bound to the journal).
        identities_b = await _worker_identities(worker, workspace_id, site_id, [op_b])
        assert len(identities_b) == 1
        identity_b = identities_b[0]
        assert identity_b["operation_id"] == str(op_b)
        assert identity_b["family"] == "agent"
        assert identity_b["principal_type"] == "capability"
        assert identity_b["disposition"] == "completed"
        assert set(identity_b) == {
            "operation_id",
            "family",
            "principal_type",
            "principal_id",
            "request_identity",
            "request_digest",
            "resource_type",
            "resource_id",
            "disposition",
        }
        # TRUSTED NEGATIVE FIXTURE (labeled): MISMATCH A's family-event
        # counterpart (its journal is retained).  The whole-workspace
        # scan must refuse even though A is outside U.
        async with await _owner(database) as owner:
            original_resource = await owner.fetchval(
                "SELECT resource_id FROM audit.agent_mutation WHERE operation_id = $1",
                op_a,
            )
            await owner.execute(
                "UPDATE audit.agent_mutation SET resource_id = "
                "gen_random_uuid() WHERE operation_id = $1",
                op_a,
            )
        try:
            with pytest.raises(asyncpg.PostgresError) as err:
                await _run_provenance(worker, workspace_id, site_id, [op_b])
            assert err.value.sqlstate == "P0003"
            assert "PROVENANCE_CONFLICT" in err.value.message
        finally:
            async with await _owner(database) as owner:
                await owner.execute(
                    "UPDATE audit.agent_mutation SET resource_id = $2 "
                    "WHERE operation_id = $1",
                    op_a,
                    original_resource,
                )
        # TRUSTED NEGATIVE FIXTURE (labeled): MISMATCH A's reservation
        # binding (the digest no longer equals the journal binding).
        async with await _owner(database) as owner:
            original_digest = await owner.fetchval(
                "SELECT request_digest FROM control.agent_idempotency "
                "WHERE operation_id = $1 AND workspace_id = $2",
                op_a,
                workspace_id,
            )
            await owner.execute(
                "UPDATE control.agent_idempotency SET request_digest = "
                "repeat('0', 64) WHERE operation_id = $1 "
                "AND workspace_id = $2",
                op_a,
                workspace_id,
            )
        try:
            with pytest.raises(asyncpg.PostgresError) as err:
                await _run_provenance(worker, workspace_id, site_id, [op_b])
            assert err.value.sqlstate == "P0003"
            assert "PROVENANCE_CONFLICT" in err.value.message
        finally:
            async with await _owner(database) as owner:
                await owner.execute(
                    "UPDATE control.agent_idempotency SET request_digest "
                    "= $2 WHERE operation_id = $1 AND workspace_id = $3",
                    op_a,
                    original_digest,
                    workspace_id,
                )
        # Boundary pin (honest): DELETING A's same-family counterpart
        # while retaining its journal is UNKNOWN history by design, not
        # a conflict - the provenance never demands a nonexistent fact.
        async with await _owner(database) as owner:
            await owner.execute(
                "DELETE FROM audit.agent_mutation WHERE operation_id = $1",
                op_a,
            )
        await _run_provenance(worker, workspace_id, site_id, [op_b])
        # Boundary pin (honest): a lone pre-078 completed reservation
        # with NO journal row anywhere in the site is old UNKNOWN
        # history and stays allowed (never re-dated, never backfilled).
        op_old = uuid4()
        async with await _owner(database) as owner:
            await owner.execute(
                "INSERT INTO control.agent_idempotency "
                "(capability_id, workspace_id, idempotency_key, "
                "request_digest, operation_id, status_code, "
                "response_body, resource_type, resource_id, "
                "completed_at) "
                "VALUES ($1, $2, 'r2-old-history', $3, $4, 201, "
                "'{\"action\": \"OLD_HISTORY\"}'::jsonb, 'content_type', "
                "$5, now())",
                capability_id,
                workspace_id,
                hashlib.sha256(b"r2-old-history").hexdigest(),
                op_old,
                uuid4(),
            )
        await _run_provenance(worker, workspace_id, site_id, [op_b])
        # A missing journal row INSIDE U fails closed.
        with pytest.raises(asyncpg.PostgresError) as err:
            await _run_provenance(worker, workspace_id, site_id, [op_b, uuid4()])
        assert err.value.sqlstate == "P0001"
        assert "PROVENANCE_MISSING" in err.value.message
    finally:
        await _close(worker)


# ----------------------------------------------------------------------
# 5. complete-with-manifest: typed envelope refusals (worker EXECUTE)
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_completion_with_manifest_envelope_refusals(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The 079 completion definer fails closed with typed refusals."""
    database = agent_site_database
    await _assert_079_head(database)
    seeded, token, workspace_id, _capability_id = await _seed_r2_site(
        database, "binding envelope ws"
    )
    site_id = seeded["site_id"]
    async with _agent_client(database) as client:
        op_x, _type_x = await _agent_type_create(
            client, token, key="env-x", label="Envelope X"
        )
    operations, dependency_pairs = await _public_universe(database, workspace_id)
    assert set(operations) == {op_x}
    worker = await _real_login(database, "slaif_review_worker")
    try:
        identities = await _worker_identities(worker, workspace_id, site_id, [op_x])
        assert len(identities) == 1
        base = _envelope(
            site_id=site_id,
            workspace_id=workspace_id,
            operation_ids=[op_x],
            dependency_pairs=dependency_pairs,
            completion_identities=identities,
        )

        def _tampered_identity() -> list[dict[str, Any]]:
            """A real identity with ONE hex char flipped: it passes
            every shape guard but no longer matches the journal."""
            tampered = json.loads(json.dumps(identities))
            identity = tampered[0]["request_identity"]
            flip = "b" if identity[-1] != "b" else "a"
            tampered[0]["request_identity"] = identity[:-1] + flip
            return [dict(record) for record in tampered]

        def _with(**changes: Any) -> str:
            envelope = json.loads(json.dumps(base))
            for key, value in changes.items():
                if value is ...:
                    envelope.pop(key)
                else:
                    envelope[key] = value
            return json.dumps(envelope)

        probes = (
            (
                "non-object manifest",
                "[]",
                "MANIFEST_INPUT_INVALID",
            ),
            (
                "five-key manifest",
                _with(completion_identities=...),
                "MANIFEST_INPUT_INVALID",
            ),
            (
                "wrong schema version",
                _with(schema_version="reviewed-operations/v0"),
                "MANIFEST_INPUT_INVALID",
            ),
            (
                "duplicate operation",
                _with(operation_ids=[str(op_x), str(op_x)]),
                "MANIFEST_DUPLICATE_OPERATION",
            ),
            (
                "dependency endpoint outside U",
                _with(dependency_pairs=[[str(op_x), str(uuid4())]]),
                "MANIFEST_DEPENDENCY_ENDPOINT",
            ),
            (
                "tampered completion identity",
                _with(completion_identities=_tampered_identity()),
                "MANIFEST_IDENTITY_MISMATCH",
            ),
        )
        for label, manifest_json, expected_message in probes:
            async with worker.transaction():
                with pytest.raises(asyncpg.PostgresError) as err:
                    await worker.fetchval(
                        f"SELECT {_COMPLETE_WITH_MANIFEST_CALL}"
                        "($1, $2::jsonb, $3::jsonb)",
                        workspace_id,
                        json.dumps({"schema_version": "review-snapshot/v2"}),
                        manifest_json,
                    )
            assert expected_message in err.value.message, (
                label,
                err.value.message,
            )
            assert err.value.sqlstate == "P0001", (
                label,
                err.value.sqlstate,
            )
    finally:
        await _close(worker)
    # Every refusal rolled back: the workspace is untouched.
    async with await _owner(database) as owner:
        assert (
            await owner.fetchval(
                "SELECT status FROM control.workspace WHERE id = $1",
                workspace_id,
            )
            == "ACTIVE"
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM control.review_snapshot WHERE workspace_id = $1",
                workspace_id,
            )
            == 0
        )
        assert (
            await owner.fetchval(
                f"SELECT count(*) FROM {_MANIFEST_TABLE} WHERE workspace_id = $1",
                workspace_id,
            )
            == 0
        )
    operations, _dependencies = await _public_universe(database, workspace_id)
    assert set(operations) == {op_x}, (
        "envelope refusals must not touch the pending universe"
    )


# ----------------------------------------------------------------------
# 6. Real 079 completion + legacy live ACCEPT payload refusal
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_legacy_live_accept_payload_refused(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Genuine 079 REVIEW + companion; a 072-era live payload refuses.

    TRUSTED LEGACY-STATE FIXTURE: the live ACCEPT job payload is the
    real 072 3-key shape (snapshot_id, site_id, actor_user_account_id,
    no digests), simulating a job enqueued before 079.  The snapshot and
    the companion manifest are produced by the real 079 worker definer -
    the owner never inserts a manifest.  The matching 5-key replay and
    the full accept publication are PRIMARY's C1/C2 consumer surface.
    """
    database = agent_site_database
    await _assert_079_head(database)
    seeded, token, workspace_id, _capability_id = await _seed_r2_site(
        database, "binding legacy payload ws"
    )
    site_id = seeded["site_id"]
    delegator_id = seeded["delegator_id"]
    op_a: UUID
    op_b: UUID
    async with _agent_client(database) as client:
        op_a, _type_a = await _agent_type_create(
            client, token, key="legacy-a", label="Legacy A"
        )
        op_b, _type_b = await _agent_type_create(
            client, token, key="legacy-b", label="Legacy B"
        )
    # Fixture honesty: the delegator must really hold the accept
    # permissions; without them the outer definer would silently RETURN.
    async with await _owner(database) as owner:
        assert await owner.fetchval(
            "SELECT 'workspace:accept' = ANY(m.effective_permissions) "
            "AND 'site:publish' = ANY(m.effective_permissions) "
            "FROM control.slaif_effective_human_membership($1, $2) AS m",
            delegator_id,
            site_id,
        ), "delegating owner must hold workspace:accept + site:publish"

    # Real freeze + claim + the real 079 worker completion (genuine
    # REVIEW snapshot + one-to-one immutable companion).
    job_id = await _freeze_and_claim(
        database,
        workspace_id=workspace_id,
        site_id=site_id,
        user_id=delegator_id,
        claimant="binding-legacy-freeze",
    )
    operations, dependency_pairs = await _public_universe(database, workspace_id)
    assert set(operations) == {op_a, op_b}
    snapshot_id = await _worker_complete_with_manifest(
        database,
        workspace_id=workspace_id,
        site_id=site_id,
        job_id=job_id,
        claimant="binding-legacy-freeze",
        operations=operations,
        dependency_pairs=dependency_pairs,
    )
    async with await _owner(database) as owner:
        ws_row = await owner.fetchrow(
            "SELECT status, review_snapshot_id FROM control.workspace WHERE id = $1",
            workspace_id,
        )
        assert ws_row["status"] == "REVIEW"
        assert ws_row["review_snapshot_id"] == snapshot_id
        snapshot_row = await owner.fetchrow(
            "SELECT site_id, digest, status FROM control.review_snapshot WHERE id = $1",
            snapshot_id,
        )
        assert snapshot_row["site_id"] == site_id
        assert snapshot_row["status"] == "COMPLETE"
        snapshot_digest: str = snapshot_row["digest"]
        assert len(snapshot_digest) == 64
        # The genuine one-to-one companion binding.
        companion = await owner.fetchrow(
            f"SELECT site_id, workspace_id, schema_version, "
            f"snapshot_digest, manifest_digest, operation_ids, "
            f"completion_identities FROM {_MANIFEST_TABLE} "
            "WHERE snapshot_id = $1",
            snapshot_id,
        )
        assert companion is not None, (
            "the 079 worker completion must create its companion"
        )
        assert companion["site_id"] == site_id
        assert companion["workspace_id"] == workspace_id
        assert companion["schema_version"] == "reviewed-operations/v1"
        assert companion["snapshot_digest"] == snapshot_digest
        manifest_digest: str = companion["manifest_digest"]
        assert len(manifest_digest) == 64
        assert sorted(str(op) for op in companion["operation_ids"]) == sorted(
            str(op) for op in (op_a, op_b)
        )
        assert len(_jsonb(companion["completion_identities"])) == 2
        assert (
            await owner.fetchval(
                "SELECT status FROM control.review_job WHERE id = $1",
                job_id,
            )
            == "SUCCEEDED"
        )
        # No promotion receipt exists yet (accept has not happened).
        assert await owner.fetchval("SELECT count(*) FROM audit.promotion") == 0

    # TRUSTED LEGACY-STATE FIXTURE: a live ACCEPT job carrying the real
    # 072 3-key payload shape (no digests).
    async with await _owner(database) as owner:
        legacy_job_id = await owner.fetchval(
            "INSERT INTO control.review_job "
            "(workspace_id, site_id, job_kind, status, payload) "
            "VALUES ($1, $2, 'ACCEPT', 'QUEUED', $3::jsonb) "
            "RETURNING id",
            workspace_id,
            site_id,
            json.dumps(
                {
                    "snapshot_id": str(snapshot_id),
                    "site_id": str(site_id),
                    "actor_user_account_id": str(delegator_id),
                }
            ),
        )
    control = await _real_login(database, "slaif_control")

    async def _outer_accept() -> None:
        await control.fetchrow(
            "SELECT * FROM control.slaif_human_agent_workspace_accept"
            "($1, $2, $3, $4, $5, $6)",
            workspace_id,
            site_id,
            snapshot_id,
            snapshot_digest,
            manifest_digest,
            delegator_id,
        )

    async def _assert_no_accept_side_effects() -> None:
        async with await _owner(database) as owner:
            assert (
                await owner.fetchval(
                    "SELECT status FROM control.workspace WHERE id = $1",
                    workspace_id,
                )
                == "REVIEW"
            ), "a refused accept must not move the workspace"
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.review_job "
                    "WHERE workspace_id = $1 AND job_kind = 'ACCEPT' "
                    "AND status IN ('QUEUED', 'CLAIMED')",
                    workspace_id,
                )
                == 1
            ), "a refused accept must not enqueue a second live job"
            assert await owner.fetchval("SELECT count(*) FROM audit.promotion") == 0, (
                "a refused accept must write no promotion receipt"
            )

    try:
        # The legacy 3-key payload cannot match the exact 5-field
        # approval: typed refusal, never a 202 replay, never a fill.
        with pytest.raises(asyncpg.PostgresError) as err:
            await _outer_accept()
        assert err.value.sqlstate == "P0003"
        assert "ACCEPT_LIVE_JOB_MISMATCH" in err.value.message
        await _assert_no_accept_side_effects()
        async with await _owner(database) as owner:
            payload = await owner.fetchrow(
                "SELECT payload FROM control.review_job WHERE id = $1",
                UUID(str(legacy_job_id)),
            )
            assert set(_jsonb(payload["payload"])) == set(_LEGACY_PAYLOAD_KEYS), (
                "the legacy payload must be untouched (no silent fill)"
            )
        # Null-safe variant: a 4-key payload missing manifest_digest
        # (->> yields NULL) is refused exactly like a wrong digest.
        async with await _owner(database) as owner:
            await owner.execute(
                "UPDATE control.review_job SET payload = $2::jsonb WHERE id = $1",
                UUID(str(legacy_job_id)),
                json.dumps(
                    {
                        "snapshot_id": str(snapshot_id),
                        "site_id": str(site_id),
                        "actor_user_account_id": str(delegator_id),
                        "snapshot_digest": snapshot_digest,
                    }
                ),
            )
        with pytest.raises(asyncpg.PostgresError) as err:
            await _outer_accept()
        assert err.value.sqlstate == "P0003"
        assert "ACCEPT_LIVE_JOB_MISMATCH" in err.value.message
        await _assert_no_accept_side_effects()
        # NULL payload: the comparison chain is NULL and must refuse.
        async with await _owner(database) as owner:
            await owner.execute(
                "UPDATE control.review_job SET payload = NULL WHERE id = $1",
                UUID(str(legacy_job_id)),
            )
        with pytest.raises(asyncpg.PostgresError) as err:
            await _outer_accept()
        assert err.value.sqlstate == "P0003"
        assert "ACCEPT_LIVE_JOB_MISMATCH" in err.value.message
        await _assert_no_accept_side_effects()
    finally:
        await _close(control)

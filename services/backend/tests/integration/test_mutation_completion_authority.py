"""Bounded C4 authority subset for the 078_001 trusted mutation completion.

Against the real product migration chain (current head) and the real fixture
roles, this module verifies the journal table/function authority boundary,
the completion definers' context and reservation binding, the global
same-operation identity across families, and one real two-transaction
same-operation completion race:

1. Direct role denial: every runtime role in 078_001's
   ``_ROLES_WITHOUT_JOURNAL_ACCESS`` is refused SELECT/INSERT/UPDATE/
   DELETE/TRUNCATE on ``audit.mutation_completion`` and EXECUTE of
   ``control.slaif_mutation_completion_record`` (SQLSTATE 42501).  No
   inspection rights are granted; the trusted owner then reads the actual
   outcome (table present, empty, no probe effect anywhere).
2. Agent completion definer under the real ``slaif_agent_runtime`` role in
   real public COW transactions:
   - positive: begin + real COW write + 13-argument semantic completion
     commit; the owner reads the durable journal row (opaque SHA-256
     request identity, digest bound to the reservation), the family audit
     row, the completed reservation, and the public reviewer sees exactly
     the one pending operation.
   - refusals with deliberately wrong bindings (missing COW context GUCs,
     wrong ``app.operation_id``, wrong ``app.session_id`` against a
     second, existing same-site workspace, wrong site, wrong principal
     capability, wrong reservation digest, and a missing reservation
     with no idempotency_begin): each refusal rolls back the
     transaction's COW write, family audit, reservation completion, and
     journal effects.  The missing-GUC and missing-reservation states
     are malformed direct calls (a product COW session always sets the
     GUCs and begins first), exercised as trusted negative fixtures
     rather than HTTP proofs.
3. Global same-operation identity:
   - an agent-completed operation cannot be completed by the human family
     (real editor role + real human session + real COW session):
     COMPLETION_IDENTITY_CONFLICT and the whole human transaction rolls
     back while the agent identity stays untouched;
   - a trusted owner fixture representing a pre-078 explicit no-effect
     agent completion (completed ledger row and NO family audit row and NO
     journal row, by design of that era; a historical-state label, not a
     legacy-migration proof or backfill) is likewise blocked for a new
     human-family completion by the any-family completed-ledger check.
4. A real two-transaction cross-family same-operation completion race
   with a controlled barrier: the agent winner performs its real COW
   write and completion and holds the transaction (and the operation's
   completion serialization) uncommitted; the human loser begins the same
   operation in its own family's ledger and reaches the completion
   boundary, where it is observed in pg_catalog.pg_stat_activity executing
   the human completion and blocked by the winner's backend before the
   winner commits.  Exactly one journal identity exists in total (the
   winner's); the loser is refused with the documented cross-family
   completion-identity conflict and leaves no reservation/audit/journal
   row after its rollback.

All durable reads go through the trusted owner fixture connection; pending
operation probes use the public foundation reviewer surface only AFTER the
probed transaction has committed or rolled back.  Real fixture roles and
real SQL only; nothing is mocked.  This module is a bounded C4 subset and
does not claim C5 late-boundary, C6 upgrade, or full C2 coverage.
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from test_agent_mutations import _seed
from test_media_security_lifecycle import _control_settings
from test_media_workspace_isolation import _seed_agent_fixture
from test_real_human_accept import _CURRENT_VERSION_FACTS

_JOURNAL_TABLE = "audit.mutation_completion"

# Bound to the real 078_001 migration source (its role list is the
# authority boundary under test).
_M078 = importlib.import_module(
    "slaif_agent_site.db.alembic.versions.078_001_trusted_mutation_completions"
)

_JOURNAL_ROW_SQL = (
    "SELECT operation_id, family, site_id, workspace_id, capability_id, "
    "human_user_id, request_identity, request_digest, resource_type, "
    "resource_id, disposition, schema_version "
    f"FROM {_JOURNAL_TABLE} WHERE operation_id = $1"
)

_AGENT_BEGIN_SQL = "SELECT * FROM control.slaif_agent_idempotency_begin($1,$2,$3,$4,$5)"
_AGENT_COMPLETE_SQL = (
    "SELECT control.slaif_agent_idempotency_complete("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)"
)
_HUMAN_BEGIN_SQL = (
    "SELECT * FROM control.slaif_human_agent_editor_idempotency_begin("
    "$1,$2,$3,$4,$5,$6,$7,$8)"
)
_HUMAN_COMPLETE_SQL = (
    "SELECT control.slaif_human_agent_editor_idempotency_complete("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)"
)
_CONTENT_TYPE_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_type_create($1,$2,$3,$4,$5)"
)
_PAGE_CREATE_SQL = "SELECT * FROM content.slaif_agent_page_create($1,$2,$3,$4,$5,$6,$7)"


@asynccontextmanager
async def _cow_session(
    pool: Any,
    *,
    session_id: UUID,
    operation_id: UUID,
    capability_id: UUID | None = None,
) -> Any:
    """A real public COW session carrying the request capability context."""
    async with asyncpg_cow_session(
        pool, session_id=session_id, operation_id=operation_id
    ) as cow:
        if capability_id is not None:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(capability_id),
            )
        yield cow


def _key_identity(key: str) -> str:
    """The journal's bounded request identity for a raw client key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _digest(payload: str) -> str:
    """A 64-hex request digest in the shape the envelopes require."""
    material = "083-11-a:" + payload
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _response_body(action: str, operation_id: UUID, resource_id: UUID) -> str:
    """A semantic completion body matching the definer's contract checks."""
    return json.dumps(
        {
            "action": action,
            "operation_id": str(operation_id),
            "record": {"id": str(resource_id)},
        }
    )


async def _owner(database: AgentSiteDatabase) -> Any:
    return owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    )


async def _assert_no_durable_effects(
    database: AgentSiteDatabase,
    reviewer_pool: Any,
    *,
    workspace_id: UUID,
    operation_ids: list[UUID],
    agent_idempotency_keys: list[str],
) -> None:
    """Owner-verified: every effect of a refused completion rolled back."""
    async with await _owner(database) as owner:
        for operation_id in operation_ids:
            assert (
                await owner.fetchval(
                    f"SELECT count(*) FROM {_JOURNAL_TABLE} WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            ), f"journal row survived for {operation_id}"
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.agent_mutation WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            ), f"family audit row survived for {operation_id}"
        for key in agent_idempotency_keys:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.agent_idempotency "
                    "WHERE idempotency_key = $1",
                    key,
                )
                == 0
            ), f"reservation survived for {key}"
    async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
        pending = await reviewer.operations(workspace_id, schema="content")
    for operation_id in operation_ids:
        assert operation_id not in pending, (
            f"refused operation {operation_id} left a pending COW operation"
        )


async def _effective_permission_key(
    database: AgentSiteDatabase, human_user_id: UUID, site_id: UUID
) -> str:
    """Pick a real permission key from the user's effective membership."""
    async with await _owner(database) as owner:
        permissions: list[str] = await owner.fetchval(
            "SELECT effective_permissions FROM "
            "control.slaif_effective_human_membership($1, $2)",
            human_user_id,
            site_id,
        )
    assert permissions, "delegating owner must have effective permissions"
    if "page:write" in permissions:
        return "page:write"
    return sorted(permissions)[0]


_FULL_MODEL_SCOPES = [
    "site:read",
    "content-model:create",
    "field-definition:create",
    "content-model:read",
    "content-item:create",
    "content-item:read",
    "page:create",
    "page:read",
    "composition:read",
    "media:read",
    "component-structure:create",
]


async def _seed_agent_content_workspace(
    database: AgentSiteDatabase, site_id: UUID, delegator_id: UUID
) -> dict[str, UUID]:
    """Owner fixture: an AGENT workspace (L4, delegator = the site owner)
    with a capability carrying the full editorial-model scopes, so agent
    content-model writes are authorized by their real scope on a
    legitimately scoped workspace and capability."""
    workspace_id = uuid4()
    async with await _owner(database) as owner:
        await owner.execute(
            "INSERT INTO control.workspace "
            "(id, site_id, created_by, delegator_id, actor_type, title, "
            "delegation_preset, effective_scopes, version_facts, status, "
            "expires_at) VALUES ($1, $2, $3, $3, 'AGENT', "
            "'authority agent content workspace', 'L4', $4::jsonb, "
            + _CURRENT_VERSION_FACTS
            + ", 'ACTIVE', now() + interval '2 hours')",
            workspace_id,
            site_id,
            delegator_id,
            json.dumps(_FULL_MODEL_SCOPES),
        )
        _token, public_id, secret_digest = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability "
            "(id, workspace_id, public_id, secret_digest, scopes, "
            "request_quota, mutation_quota, delete_quota, upload_quota, "
            "expires_at, browser_max_concurrent_runs, "
            "browser_max_artifact_bytes) "
            "VALUES ($1, $2, $3, $4, $5::jsonb, 1000, 500, 100, 50, "
            "now() + interval '30 minutes', 10, 104857600)",
            uuid4(),
            workspace_id,
            public_id,
            secret_digest,
            json.dumps(_FULL_MODEL_SCOPES),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    return {"workspace_id": workspace_id, "capability_id": capability_id}


@pytest.mark.asyncio
async def test_journal_denied_to_every_runtime_role(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """078 grants: journal table + helper are owner-only; 42501 for all 10."""
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    roles = tuple(_M078._ROLES_WITHOUT_JOURNAL_ACCESS)
    assert len(roles) == 10
    probes = (
        (
            "SELECT",
            f"SELECT count(*) FROM {_JOURNAL_TABLE}",
        ),
        (
            "INSERT",
            f"INSERT INTO {_JOURNAL_TABLE} "
            "(operation_id, family, site_id, workspace_id, request_identity, "
            "request_digest, resource_type, resource_id, disposition) "
            "VALUES (gen_random_uuid(), 'agent', gen_random_uuid(), "
            "gen_random_uuid(), repeat('0', 64), repeat('0', 64), 'page', "
            "gen_random_uuid(), 'completed')",
        ),
        (
            "UPDATE",
            f"UPDATE {_JOURNAL_TABLE} SET disposition = 'completed' "
            "WHERE operation_id = gen_random_uuid()",
        ),
        (
            "DELETE",
            f"DELETE FROM {_JOURNAL_TABLE} WHERE operation_id = gen_random_uuid()",
        ),
        ("TRUNCATE", f"TRUNCATE {_JOURNAL_TABLE}"),
        (
            "EXECUTE",
            "SELECT control.slaif_mutation_completion_record("
            "gen_random_uuid(), 'agent', gen_random_uuid(), gen_random_uuid(), "
            "gen_random_uuid(), NULL, 'denial-probe', repeat('0', 64), "
            "'page', gen_random_uuid(), 'completed')",
        ),
    )
    for role in roles:
        pool = await database.role_pool(role)
        try:
            async with pool.acquire() as connection:
                assert await connection.fetchval("SELECT current_user::text") == role
                for verb, sql in probes:
                    with pytest.raises(asyncpg.InsufficientPrivilegeError) as err:
                        await connection.execute(sql)
                    assert err.value.sqlstate == "42501", (role, verb)
        finally:
            await pool.close()
    # Trusted owner reads the actual outcome: the table exists (owner can
    # read it), and no denied probe left any effect behind.
    async with await _owner(database) as owner:
        assert await owner.fetchval(f"SELECT count(*) FROM {_JOURNAL_TABLE}") == 0
        assert (
            await owner.fetchval("SELECT count(*) FROM control.agent_idempotency") == 0
        )
        assert await owner.fetchval("SELECT count(*) FROM audit.agent_mutation") == 0


@pytest.mark.asyncio
async def test_agent_completion_positive_durable_journal(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Positive control: real COW write + semantic completion is durable."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    workspace_id = seeded["workspace_id"]
    capability_id = seeded["capability_id"]
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    operation_id = uuid4()
    idempotency_key = "authority-positive-083-11-a"
    request_digest = _digest(idempotency_key)
    type_id: UUID | None = None
    try:
        async with _cow_session(
            agent_pool,
            session_id=workspace_id,
            operation_id=operation_id,
            capability_id=capability_id,
        ) as cow:
            started = await cow.native.fetchrow(
                _AGENT_BEGIN_SQL,
                capability_id,
                workspace_id,
                idempotency_key,
                request_digest,
                operation_id,
            )
            assert started[0] == "STARTED"
            created = await cow.native.fetchrow(
                _CONTENT_TYPE_CREATE_SQL,
                site_id,
                "authority-positive",
                '{"en":"Authority Positive"}',
                "/authority-positive",
                "{}",
            )
            type_id = created[0]
            await cow.native.fetchrow(
                _AGENT_COMPLETE_SQL,
                capability_id,
                workspace_id,
                idempotency_key,
                request_digest,
                operation_id,
                201,
                _response_body("CONTENT_TYPE_CREATED", operation_id, type_id),
                "content_type",
                type_id,
                site_id,
                "CONTENT_TYPE_CREATED",
                "POST",
                "mutation",
            )
        # The public COW session committed on scope exit.
        async with await _owner(database) as owner:
            journal = await owner.fetchrow(_JOURNAL_ROW_SQL, operation_id)
            assert journal is not None, "completed operation must be journaled"
            assert journal["family"] == "agent"
            assert journal["site_id"] == site_id
            assert journal["workspace_id"] == workspace_id
            assert journal["capability_id"] == capability_id
            assert journal["human_user_id"] is None
            assert journal["request_identity"] == _key_identity(idempotency_key)
            assert journal["request_digest"] == request_digest
            assert journal["resource_type"] == "content_type"
            assert journal["resource_id"] == type_id
            assert journal["disposition"] == "completed"
            assert journal["schema_version"] == "mutation-completion/v1"
            audit = await owner.fetchrow(
                "SELECT capability_id, workspace_id, site_id, resource_type, "
                "resource_id, request_digest, response_status, action, "
                "http_method, quota_kind "
                "FROM audit.agent_mutation WHERE operation_id = $1",
                operation_id,
            )
            assert audit is not None
            assert audit["capability_id"] == capability_id
            assert audit["workspace_id"] == workspace_id
            assert audit["resource_id"] == type_id
            assert audit["request_digest"] == request_digest
            assert audit["response_status"] == 201
            assert audit["action"] == "CONTENT_TYPE_CREATED"
            assert audit["http_method"] == "POST"
            assert audit["quota_kind"] == "mutation"
            ledger = await owner.fetchrow(
                "SELECT status_code, resource_type, resource_id "
                "FROM control.agent_idempotency "
                "WHERE capability_id = $1 AND idempotency_key = $2",
                capability_id,
                idempotency_key,
            )
            assert ledger is not None
            assert ledger["status_code"] == 201
            assert ledger["resource_id"] == type_id
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_type_base WHERE site_id = $1",
                    site_id,
                )
                == 0
            ), "pre-freeze: the write stays in the workspace overlay"
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            pending = await reviewer.operations(workspace_id, schema="content")
        assert pending == [operation_id]
    finally:
        await agent_pool.close()
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_agent_completion_refusals_rollback_all_effects(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Wrong context/site/principal/reservation bindings: refuse + rollback."""
    database = agent_site_database
    _token, seeded = await _seed(database)
    site_id = seeded["site_id"]
    other_site_id = seeded["site_b_id"]
    workspace_id = seeded["workspace_id"]
    capability_id = seeded["capability_id"]
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    # A second, distinct principal capability on the same workspace
    # (trusted fixture for the wrong-principal sub-case).
    async with await _owner(database) as owner:
        _t2, public_id2, secret_digest2 = generate_capability_token()
        await owner.execute(
            "INSERT INTO control.capability "
            "(workspace_id, public_id, secret_digest, scopes, expires_at) "
            "VALUES ($1, $2, $3, $4::jsonb, $5)",
            workspace_id,
            public_id2,
            secret_digest2,
            json.dumps(["site:read"]),
            datetime.now(UTC) + timedelta(minutes=30),
        )
        other_capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id2
        )
        # A second, same-site workspace (trusted fixture for the
        # wrong-session sub-case).
        wrong_workspace_id = uuid4()
        await owner.execute(
            "INSERT INTO control.workspace "
            "(id, site_id, created_by, delegator_id, title, "
            "delegation_preset, effective_scopes, status, expires_at) "
            "VALUES ($1, $2, $3, $3, 'Refusal Wrong Session', "
            "'L2_SITE_EDITOR', '[]'::jsonb, 'ACTIVE', "
            "now() + interval '1 hour')",
            wrong_workspace_id,
            site_id,
            seeded["delegator_id"],
        )
    try:
        # (a) Missing COW context GUCs: a plain agent-role connection never
        #     sets them.  A product COW session always does, so this is a
        #     malformed/unreachable direct call, exercised as a trusted
        #     negative fixture: begin + complete in one explicit transaction
        #     must fail in the journal context check and roll everything back.
        op = uuid4()
        key = "refusal-missing-context"
        digest = _digest(key)
        resource_id = uuid4()
        async with agent_pool.acquire() as connection:
            with pytest.raises(asyncpg.PostgresError) as err:
                async with connection.transaction():
                    started = await connection.fetchrow(
                        _AGENT_BEGIN_SQL,
                        capability_id,
                        workspace_id,
                        key,
                        digest,
                        op,
                    )
                    assert started[0] == "STARTED"
                    await connection.fetchrow(
                        _AGENT_COMPLETE_SQL,
                        capability_id,
                        workspace_id,
                        key,
                        digest,
                        op,
                        201,
                        _response_body("CONTENT_TYPE_CREATED", op, resource_id),
                        "content_type",
                        resource_id,
                        site_id,
                        "CONTENT_TYPE_CREATED",
                        "POST",
                        "mutation",
                    )
            assert err.value.sqlstate == "P0001"
            assert "COMPLETION_CONTEXT_MISMATCH" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op],
            agent_idempotency_keys=[key],
        )

        # (b) Wrong app.operation_id: a real COW session stamped with one
        #     operation while the caller tries to complete a different one.
        #     The refusal must roll back the real COW write AND both
        #     reservations in the same transaction.
        op_session = uuid4()
        op_claimed = uuid4()
        key_session = "refusal-wrong-op-session"
        key_claimed = "refusal-wrong-op-claim"
        digest_session = _digest(key_session)
        digest_claimed = _digest(key_claimed)
        claimed_resource = uuid4()
        with pytest.raises(asyncpg.PostgresError) as err:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=op_session,
                capability_id=capability_id,
            ) as cow:
                row_session = await cow.native.fetchrow(
                    _AGENT_BEGIN_SQL,
                    capability_id,
                    workspace_id,
                    key_session,
                    digest_session,
                    op_session,
                )
                assert row_session[0] == "STARTED"
                await cow.native.fetchrow(
                    _CONTENT_TYPE_CREATE_SQL,
                    site_id,
                    "refusal-wrong-op",
                    '{"en":"Wrong Op"}',
                    "/refusal-wrong-op",
                    "{}",
                )
                row_claimed = await cow.native.fetchrow(
                    _AGENT_BEGIN_SQL,
                    capability_id,
                    workspace_id,
                    key_claimed,
                    digest_claimed,
                    op_claimed,
                )
                assert row_claimed[0] == "STARTED"
                await cow.native.fetchrow(
                    _AGENT_COMPLETE_SQL,
                    capability_id,
                    workspace_id,
                    key_claimed,
                    digest_claimed,
                    op_claimed,
                    201,
                    _response_body(
                        "CONTENT_TYPE_CREATED", op_claimed, claimed_resource
                    ),
                    "content_type",
                    claimed_resource,
                    site_id,
                    "CONTENT_TYPE_CREATED",
                    "POST",
                    "mutation",
                )
        assert err.value.sqlstate == "P0001"
        assert "COMPLETION_CONTEXT_MISMATCH" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op_session, op_claimed],
            agent_idempotency_keys=[key_session, key_claimed],
        )

        # (c) Wrong app.session_id: the session is stamped with a different
        #     (same-site) workspace than the one the completion targets.
        op = uuid4()
        key = "refusal-wrong-session"
        digest = _digest(key)
        resource_id = uuid4()
        with pytest.raises(asyncpg.PostgresError) as err:
            async with _cow_session(
                agent_pool,
                session_id=wrong_workspace_id,
                operation_id=op,
                capability_id=capability_id,
            ) as cow:
                started = await cow.native.fetchrow(
                    _AGENT_BEGIN_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                )
                assert started[0] == "STARTED"
                await cow.native.fetchrow(
                    _AGENT_COMPLETE_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                    201,
                    _response_body("CONTENT_TYPE_CREATED", op, resource_id),
                    "content_type",
                    resource_id,
                    site_id,
                    "CONTENT_TYPE_CREATED",
                    "POST",
                    "mutation",
                )
        assert err.value.sqlstate == "P0001"
        assert "COMPLETION_CONTEXT_MISMATCH" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op],
            agent_idempotency_keys=[key],
        )

        # (d) Wrong site: the definer's capability/workspace/site binding
        #     check refuses before any durable effect.
        op = uuid4()
        key = "refusal-wrong-site"
        digest = _digest(key)
        resource_id = uuid4()
        with pytest.raises(asyncpg.PostgresError) as err:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=op,
                capability_id=capability_id,
            ) as cow:
                started = await cow.native.fetchrow(
                    _AGENT_BEGIN_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                )
                assert started[0] == "STARTED"
                await cow.native.fetchrow(
                    _AGENT_COMPLETE_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                    201,
                    _response_body("CONTENT_TYPE_CREATED", op, resource_id),
                    "content_type",
                    resource_id,
                    other_site_id,
                    "CONTENT_TYPE_CREATED",
                    "POST",
                    "mutation",
                )
        assert err.value.sqlstate == "P0001"
        assert "INVALID_SEMANTIC_COMPLETION" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op],
            agent_idempotency_keys=[key],
        )

        # (e) Wrong principal: a different capability on the same workspace
        #     cannot complete the reservation made under the real one.
        op = uuid4()
        key = "refusal-wrong-principal"
        digest = _digest(key)
        resource_id = uuid4()
        with pytest.raises(asyncpg.PostgresError) as err:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=op,
                capability_id=capability_id,
            ) as cow:
                started = await cow.native.fetchrow(
                    _AGENT_BEGIN_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                )
                assert started[0] == "STARTED"
                await cow.native.fetchrow(
                    _AGENT_COMPLETE_SQL,
                    other_capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                    201,
                    _response_body("CONTENT_TYPE_CREATED", op, resource_id),
                    "content_type",
                    resource_id,
                    site_id,
                    "CONTENT_TYPE_CREATED",
                    "POST",
                    "mutation",
                )
        assert err.value.sqlstate == "P0002"
        assert "IDEMPOTENCY_RESERVATION_NOT_FOUND" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op],
            agent_idempotency_keys=[key],
        )

        # (f) Wrong reservation identity: same key, different request digest
        #     cannot consume the reservation.
        op = uuid4()
        key = "refusal-wrong-digest"
        digest_reserved = _digest(key + "-reserved")
        digest_wrong = _digest(key + "-wrong")
        resource_id = uuid4()
        with pytest.raises(asyncpg.PostgresError) as err:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=op,
                capability_id=capability_id,
            ) as cow:
                started = await cow.native.fetchrow(
                    _AGENT_BEGIN_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest_reserved,
                    op,
                )
                assert started[0] == "STARTED"
                await cow.native.fetchrow(
                    _AGENT_COMPLETE_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest_wrong,
                    op,
                    201,
                    _response_body("CONTENT_TYPE_CREATED", op, resource_id),
                    "content_type",
                    resource_id,
                    site_id,
                    "CONTENT_TYPE_CREATED",
                    "POST",
                    "mutation",
                )
        assert err.value.sqlstate == "P0002"
        assert "IDEMPOTENCY_RESERVATION_NOT_FOUND" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op],
            agent_idempotency_keys=[key],
        )
        # (g) Missing reservation: a real COW-context completion with no
        #     idempotency_begin at all is refused by the definer's own
        #     reservation guard before any audit/journal effect.  A
        #     product agent session always begins first, so this is a
        #     malformed direct call, exercised as a trusted negative
        #     fixture; no editorial write is performed.
        op = uuid4()
        key = "refusal-missing-reservation"
        digest = _digest(key)
        resource_id = uuid4()
        with pytest.raises(asyncpg.PostgresError) as err:
            async with _cow_session(
                agent_pool,
                session_id=workspace_id,
                operation_id=op,
                capability_id=capability_id,
            ) as cow:
                await cow.native.fetchrow(
                    _AGENT_COMPLETE_SQL,
                    capability_id,
                    workspace_id,
                    key,
                    digest,
                    op,
                    201,
                    _response_body("CONTENT_TYPE_CREATED", op, resource_id),
                    "content_type",
                    resource_id,
                    site_id,
                    "CONTENT_TYPE_CREATED",
                    "POST",
                    "mutation",
                )
        assert err.value.sqlstate == "P0002"
        assert "IDEMPOTENCY_RESERVATION_NOT_FOUND" in str(err.value)
        await _assert_no_durable_effects(
            database,
            reviewer_pool,
            workspace_id=workspace_id,
            operation_ids=[op],
            agent_idempotency_keys=[key],
        )
    finally:
        await agent_pool.close()
        await reviewer_pool.close()


async def _human_session_and_key(
    database: AgentSiteDatabase,
    control: ControlDatabase,
    human_user_id: UUID,
    site_id: UUID,
) -> tuple[Any, str]:
    """A real human session (product service) + one of its real permissions."""
    session = await control.human_session_service().create(human_user_id)
    permission_key = await _effective_permission_key(database, human_user_id, site_id)
    return session, permission_key


async def _human_attempt_same_operation(
    database: AgentSiteDatabase,
    control: ControlDatabase,
    editor_pool: Any,
    *,
    site_id: UUID,
    workspace_id: UUID,
    human_user_id: UUID,
    operation_id: UUID,
    human_key: str,
) -> None:
    """Run a real human-family completion of the given operation.

    Returns the raised PostgresError to the caller via re-raise; the COW
    session's exception path rolls back the attempt before it propagates.
    """
    human_digest = _digest(human_key)
    session, permission_key = await _human_session_and_key(
        database, control, human_user_id, site_id
    )
    async with _cow_session(
        editor_pool,
        session_id=workspace_id,
        operation_id=operation_id,
    ) as cow:
        started = await cow.native.fetchrow(
            _HUMAN_BEGIN_SQL,
            workspace_id,
            human_user_id,
            site_id,
            session.session_id,
            permission_key,
            human_key,
            human_digest,
            operation_id,
        )
        assert started[0] == "STARTED"
        await cow.native.fetchrow(
            _HUMAN_COMPLETE_SQL,
            workspace_id,
            human_user_id,
            site_id,
            session.session_id,
            permission_key,
            human_key,
            human_digest,
            operation_id,
            200,
            json.dumps({"action": "PAGE_UPDATED"}),
            "PAGE_UPDATED",
            "page",
            uuid4(),
        )


@pytest.mark.asyncio
async def test_cross_family_completion_identity_conflict(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """An agent-completed operation cannot be re-completed by the human."""
    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    site_id = ids["site_a"]
    human_user_id = ids["user_a"]
    # Legitimately scoped AGENT workspace (L4, delegator = the site
    # owner) with the full editorial-model scopes: the agent content-type
    # write is authorized by its real scope, not a widened grant.
    seeded_ws = await _seed_agent_content_workspace(database, site_id, human_user_id)
    workspace_id = seeded_ws["workspace_id"]
    capability_id = seeded_ws["capability_id"]
    control = ControlDatabase(_control_settings(database))
    agent_pool = await database.role_pool("slaif_agent_runtime")
    editor_pool = await database.role_pool("slaif_editor_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    operation_id = uuid4()
    agent_key = "cross-family-agent-083-11-a"
    agent_digest = _digest(agent_key)
    try:
        # The agent family lawfully completes the operation first.
        async with _cow_session(
            agent_pool,
            session_id=workspace_id,
            operation_id=operation_id,
            capability_id=capability_id,
        ) as cow:
            started = await cow.native.fetchrow(
                _AGENT_BEGIN_SQL,
                capability_id,
                workspace_id,
                agent_key,
                agent_digest,
                operation_id,
            )
            assert started[0] == "STARTED"
            created = await cow.native.fetchrow(
                _CONTENT_TYPE_CREATE_SQL,
                site_id,
                "cross-family",
                '{"en":"Cross Family"}',
                "/cross-family",
                "{}",
            )
            type_id = created[0]
            await cow.native.fetchrow(
                _AGENT_COMPLETE_SQL,
                capability_id,
                workspace_id,
                agent_key,
                agent_digest,
                operation_id,
                201,
                _response_body("CONTENT_TYPE_CREATED", operation_id, type_id),
                "content_type",
                type_id,
                site_id,
                "CONTENT_TYPE_CREATED",
                "POST",
                "mutation",
            )
        async with await _owner(database) as owner:
            assert (
                await owner.fetchval(
                    f"SELECT count(*) FROM {_JOURNAL_TABLE} WHERE operation_id = $1",
                    operation_id,
                )
                == 1
            ), "baseline: exactly one agent identity is durable"
        # The human family now attempts to complete the SAME operation.
        await control.start()
        try:
            with pytest.raises(asyncpg.PostgresError) as err:
                await _human_attempt_same_operation(
                    database,
                    control,
                    editor_pool,
                    site_id=site_id,
                    workspace_id=workspace_id,
                    human_user_id=human_user_id,
                    operation_id=operation_id,
                    human_key="cross-family-human-083-11-a",
                )
            assert err.value.sqlstate == "P0003"
            assert "COMPLETION_IDENTITY_CONFLICT" in str(err.value)
        finally:
            await control.stop()
        # The agent identity is untouched; the human attempt left nothing.
        async with await _owner(database) as owner:
            journal_rows = await owner.fetch(
                "SELECT family, capability_id, human_user_id, "
                "request_identity "
                f"FROM {_JOURNAL_TABLE} WHERE operation_id = $1",
                operation_id,
            )
            assert len(journal_rows) == 1
            assert journal_rows[0]["family"] == "agent"
            assert journal_rows[0]["capability_id"] == capability_id
            assert journal_rows[0]["human_user_id"] is None
            assert journal_rows[0]["request_identity"] == _key_identity(agent_key)
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.human_editor_mutation "
                    "WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            ), "refused human audit row must have rolled back"
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.human_editor_idempotency "
                    "WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            ), "refused human reservation must have rolled back"
            assert (
                await owner.fetchval(
                    "SELECT status_code FROM control.agent_idempotency "
                    "WHERE idempotency_key = $1",
                    agent_key,
                )
                == 201
            ), "the agent completion must stay untouched"
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert await reviewer.operations(workspace_id, schema="content") == [
                operation_id
            ]
    finally:
        await agent_pool.close()
        await editor_pool.close()
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_historical_noeffect_completion_blocks_other_family(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """A pre-078 completed no-effect op blocks a new other-family completion.

    The historical state is a trusted owner fixture: a completed agent
    ledger row with NO family audit row and NO journal row (pre-078
    explicit no-effect completions wrote neither).  It is a label for that
    historical state, not a claim about legacy migration behavior or a
    backfill.
    """
    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    site_id = ids["site_a"]
    workspace_id = ids["agent_workspace"]
    human_user_id = ids["user_a"]
    control = ControlDatabase(_control_settings(database))
    editor_pool = await database.role_pool("slaif_editor_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    operation_id = uuid4()
    historical_key = "pre078-noeffect-historical"
    historical_digest = _digest(historical_key)
    try:
        async with await _owner(database) as owner:
            capability_id = await owner.fetchval(
                "SELECT id FROM control.capability WHERE workspace_id = $1",
                workspace_id,
            )
            await owner.execute(
                "INSERT INTO control.agent_idempotency "
                "(capability_id, workspace_id, idempotency_key, "
                "request_digest, operation_id, status_code, response_body, "
                "resource_type, resource_id, completed_at) "
                "VALUES ($1, $2, $3, $4, $5, 200, $6::jsonb, 'theme', "
                "$7, now())",
                capability_id,
                workspace_id,
                historical_key,
                historical_digest,
                operation_id,
                json.dumps({"action": None, "no_effect": True}),
                uuid4(),
            )
        # The human family attempts to complete the same historical
        # operation: the any-family completed-ledger check must refuse it.
        await control.start()
        try:
            with pytest.raises(asyncpg.PostgresError) as err:
                await _human_attempt_same_operation(
                    database,
                    control,
                    editor_pool,
                    site_id=site_id,
                    workspace_id=workspace_id,
                    human_user_id=human_user_id,
                    operation_id=operation_id,
                    human_key="historical-human-083-11-a",
                )
            assert err.value.sqlstate == "P0003"
            assert "COMPLETION_IDENTITY_CONFLICT" in str(err.value)
        finally:
            await control.stop()
        # The historical row is untouched; the new attempt left nothing.
        async with await _owner(database) as owner:
            assert (
                await owner.fetchval(
                    f"SELECT count(*) FROM {_JOURNAL_TABLE} WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            ), "no journal row may be created for the historical operation"
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.human_editor_mutation "
                    "WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.human_editor_idempotency "
                    "WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            )
            historical = await owner.fetchrow(
                "SELECT status_code, idempotency_key "
                "FROM control.agent_idempotency WHERE operation_id = $1",
                operation_id,
            )
            assert historical is not None
            assert historical["status_code"] == 200
            assert historical["idempotency_key"] == historical_key
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert await reviewer.operations(workspace_id, schema="content") == []
    finally:
        await editor_pool.close()
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_same_operation_completion_race_single_winner(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Concurrent cross-family same-op completions: one journal identity total.

    The agent winner performs a real COW write in its own AGENT workspace
    and completes the operation, holding its transaction (and the
    operation's completion serialization) uncommitted; the human loser
    begins the same operation in a second, separately eligible AGENT
    workspace (same site, same delegating owner) and reaches the
    completion boundary, where a trusted pg_catalog observation proves
    the loser is executing the human completion and blocked by the
    winner's backend before the winner commits.  Exactly one journal
    identity exists in total (the winner's); the loser is refused with
    the documented cross-family completion-identity conflict and leaves
    no reservation/audit/journal row after its rollback, and its own
    workspace shows no pending operation.
    """
    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    site_id = ids["site_a"]
    human_user_id = ids["user_a"]
    # Two legitimately eligible AGENT workspaces (L4, same delegating
    # site owner, full editorial-model scopes): the agent winner and the
    # human loser each operate in their own real workspace context, so
    # only the operation-level completion serialization is shared.
    winner_ws = await _seed_agent_content_workspace(database, site_id, human_user_id)
    loser_ws = await _seed_agent_content_workspace(database, site_id, human_user_id)
    workspace_id = winner_ws["workspace_id"]
    capability_id = winner_ws["capability_id"]
    loser_workspace_id = loser_ws["workspace_id"]
    control = ControlDatabase(_control_settings(database))
    agent_pool = await database.role_pool("slaif_agent_runtime")
    editor_pool = await database.role_pool("slaif_editor_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    operation_id = uuid4()
    winner_key = "race-winner-083-11-a"
    winner_digest = _digest(winner_key)
    loser_key = "race-loser-083-11-a"
    loser_digest = _digest(loser_key)
    winner_ready = asyncio.Event()
    human_in_flight = asyncio.Event()
    overlap_proven = asyncio.Event()
    pids: dict[str, int] = {}
    loser_error: dict[str, str] = {}
    observed: dict[str, Any] = {}
    try:
        await control.start()
        try:
            session, permission_key = await _human_session_and_key(
                database, control, human_user_id, site_id
            )

            async def winner() -> None:
                async with _cow_session(
                    agent_pool,
                    session_id=workspace_id,
                    operation_id=operation_id,
                    capability_id=capability_id,
                ) as cow:
                    pids["winner"] = int(
                        await cow.native.fetchval("SELECT pg_backend_pid()")
                    )
                    started = await cow.native.fetchrow(
                        _AGENT_BEGIN_SQL,
                        capability_id,
                        workspace_id,
                        winner_key,
                        winner_digest,
                        operation_id,
                    )
                    assert started[0] == "STARTED"
                    created = await cow.native.fetchrow(
                        _CONTENT_TYPE_CREATE_SQL,
                        site_id,
                        "race-winner",
                        '{"en":"Race Winner"}',
                        "/race-winner",
                        "{}",
                    )
                    winner_type_id = created[0]
                    await cow.native.fetchrow(
                        _AGENT_COMPLETE_SQL,
                        capability_id,
                        workspace_id,
                        winner_key,
                        winner_digest,
                        operation_id,
                        201,
                        _response_body(
                            "CONTENT_TYPE_CREATED", operation_id, winner_type_id
                        ),
                        "content_type",
                        winner_type_id,
                        site_id,
                        "CONTENT_TYPE_CREATED",
                        "POST",
                        "mutation",
                    )
                    winner_ready.set()
                    # The winner stays uncommitted until the observer has
                    # seen the loser actually blocked at the completion
                    # boundary.
                    await overlap_proven.wait()
                # Scope exit commits the winner's full completion.

            async def loser() -> None:
                await winner_ready.wait()
                with pytest.raises(asyncpg.PostgresError) as err:
                    async with _cow_session(
                        editor_pool,
                        session_id=loser_workspace_id,
                        operation_id=operation_id,
                    ) as cow:
                        pids["loser"] = int(
                            await cow.native.fetchval("SELECT pg_backend_pid()")
                        )
                        started = await cow.native.fetchrow(
                            _HUMAN_BEGIN_SQL,
                            loser_workspace_id,
                            human_user_id,
                            site_id,
                            session.session_id,
                            permission_key,
                            loser_key,
                            loser_digest,
                            operation_id,
                        )
                        assert started[0] == "STARTED"
                        # A zero-DML completion: no agent quota or shared
                        # structural rows; the operation-level completion
                        # boundary itself is the conflict point.  The
                        # in-flight signal is set before the potentially
                        # blocking call.
                        human_in_flight.set()
                        await cow.native.fetchrow(
                            _HUMAN_COMPLETE_SQL,
                            loser_workspace_id,
                            human_user_id,
                            site_id,
                            session.session_id,
                            permission_key,
                            loser_key,
                            loser_digest,
                            operation_id,
                            200,
                            json.dumps({"action": "PAGE_UPDATED"}),
                            "PAGE_UPDATED",
                            "page",
                            uuid4(),
                        )
                loser_error["sqlstate"] = err.value.sqlstate
                loser_error["message"] = str(err.value)

            async def observer() -> None:
                # Trusted catalog observation of the two exact test
                # backends via the fixture administrator connection: the
                # loser must be seen executing the human completion and
                # blocked by the winner while the winner still holds its
                # uncommitted transaction.
                await human_in_flight.wait()
                loop = asyncio.get_running_loop()
                deadline = loop.time() + 30
                last_rows: list[dict[str, Any]] = []
                while not overlap_proven.is_set():
                    if loop.time() > deadline:
                        break
                    rows = await database.administrator.fetch(
                        "SELECT a.pid, a.state, a.query, "
                        "pg_catalog.pg_blocking_pids(a.pid) AS blockers "
                        "FROM pg_catalog.pg_stat_activity AS a "
                        "WHERE a.pid = ANY($1) ORDER BY a.pid",
                        [pids["winner"], pids["loser"]],
                    )
                    last_rows = [
                        {
                            "pid": row["pid"],
                            "state": row["state"],
                            "query": (row["query"] or "")[:120],
                            "blockers": list(row["blockers"]),
                        }
                        for row in rows
                    ]
                    by_pid = {row["pid"]: row for row in last_rows}
                    loser_row = by_pid.get(pids["loser"])
                    winner_row = by_pid.get(pids["winner"])
                    if (
                        loser_row is not None
                        and loser_row["state"] == "active"
                        and pids["winner"] in loser_row["blockers"]
                        and "slaif_human_agent_editor_idempotency_complete"
                        in loser_row["query"]
                        and winner_row is not None
                        and winner_row["state"] == "idle in transaction"
                    ):
                        observed["rows"] = last_rows
                        overlap_proven.set()
                        return
                    await asyncio.sleep(0.05)
                raise AssertionError(
                    "the loser was never observed executing the human "
                    f"completion blocked by the winner: {last_rows}"
                )

            tasks = [
                asyncio.create_task(coro) for coro in (winner(), loser(), observer())
            ]
            try:
                await asyncio.wait_for(asyncio.gather(*tasks), timeout=180)
            finally:
                # Bounded drain of the exact barrier tasks on every path
                # (success, timeout, or early exception) before the
                # control database and pools are released: each cancelled
                # COW session rolls back its own transaction.
                for task in tasks:
                    if not task.done():
                        task.cancel()
                drained = await asyncio.gather(*tasks, return_exceptions=True)
                observed["drain"] = [
                    type(item).__name__ if isinstance(item, BaseException) else "done"
                    for item in drained
                ]
        finally:
            await control.stop()
        # The overlap was observed before the winner released.
        assert observed.get("rows"), "overlap must be proven from pg_catalog"
        # The loser's documented conflict: the new global cross-family
        # completion identity (078_001), not an old ledger unique key.
        assert loser_error["sqlstate"] == "P0003"
        assert "COMPLETION_IDENTITY_CONFLICT" in loser_error["message"]
        # Exactly ONE journal identity in total: the agent winner's, in
        # the winner's own workspace.
        async with await _owner(database) as owner:
            journal_rows = await owner.fetch(
                "SELECT family, capability_id, human_user_id, workspace_id, "
                "request_identity, request_digest, disposition "
                f"FROM {_JOURNAL_TABLE} WHERE operation_id = $1",
                operation_id,
            )
            assert len(journal_rows) == 1
            assert journal_rows[0]["family"] == "agent"
            assert journal_rows[0]["capability_id"] == capability_id
            assert journal_rows[0]["workspace_id"] == workspace_id
            assert journal_rows[0]["human_user_id"] is None
            assert journal_rows[0]["request_identity"] == _key_identity(winner_key)
            assert journal_rows[0]["request_digest"] == winner_digest
            assert journal_rows[0]["disposition"] == "completed"
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.agent_mutation WHERE operation_id = $1",
                    operation_id,
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.human_editor_mutation "
                    "WHERE operation_id = $1",
                    operation_id,
                )
                == 0
            ), "the loser's human audit row must have rolled back"
            assert (
                await owner.fetchval(
                    "SELECT status_code FROM control.agent_idempotency "
                    "WHERE idempotency_key = $1",
                    winner_key,
                )
                == 201
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.human_editor_idempotency "
                    "WHERE idempotency_key = $1",
                    loser_key,
                )
                == 0
            ), "the loser must leave no reservation row"
            # Canonical base is untouched (pre-freeze).
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_type_base WHERE site_id = $1",
                    site_id,
                )
                == 0
            )
        # Committed workspace projections under explicit COW session
        # contexts (session-scoped GUCs inside one transaction each):
        # the winner's one pending row in its workspace; none in the
        # loser's workspace (zero-DML completion, rolled back).
        async with await _owner(database) as owner:
            async with owner.transaction():
                await owner.execute(
                    "SELECT set_config('app.session_id', $1, true)",
                    str(workspace_id),
                )
                winner_rows = await owner.fetchval(
                    "SELECT count(*) FROM content.content_type "
                    'WHERE site_id = $1 AND "key" = $2',
                    site_id,
                    "race-winner",
                )
            async with owner.transaction():
                await owner.execute(
                    "SELECT set_config('app.session_id', $1, true)",
                    str(loser_workspace_id),
                )
                loser_rows = await owner.fetchval(
                    "SELECT count(*) FROM content.content_type "
                    'WHERE site_id = $1 AND "key" = $2',
                    site_id,
                    "race-loser",
                )
        assert winner_rows == 1, "the winner's pending COW write is durable"
        assert loser_rows == 0, "the loser's zero-DML completion left no row"
        # The public surface sees exactly the winner's one operation in
        # the winner's workspace, and nothing pending in the loser's.
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert await reviewer.operations(workspace_id, schema="content") == [
                operation_id
            ]
            assert await reviewer.operations(loser_workspace_id, schema="content") == []
    finally:
        await agent_pool.close()
        await editor_pool.close()
        await reviewer_pool.close()

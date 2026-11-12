"""083/10-a peer A7 slice: 077 media publication-helper privilege/phase contract.

Test-only module (peer task; primary owns full A7).  Delivered against
the six 083/10-a production inputs (077_001 migration, bootstrap,
content_model, privileges, finalize, accept_job); the exact input
SHA-256 receipts are recorded in the 083/10-a round report, not here.

Real conftest provisioning, real bootstrap/harden/verify primitives, real
fixture-credential role pools (the SET ROLE envelope).  No mocks of COW,
credentials, privilege verification or SQL execution.  No app locators:
only raw asyncpg plus BootstrapSettings DSNs against the private
127.0.0.10 endpoint.

Coverage (bounded A7 slice; full A7 preservation stays primary's):
1. fresh 077 hardened/ready: grant shape is owner + worker-EXECUTE only
   (exact regprocedure identity, no PUBLIC execute); the real
   reviewer-worker login is refused on the SAME present helper after
   SET ROLE into the reachable generic reviewer (reachable role carries
   no EXECUTE), EXECUTEs it as its own effective role (empty referenced
   set = EXECUTE-success probe, not a publication proof); every ordinary
   non-owner/non-worker role is refused with SQLSTATE 42501; the dropped
   creator/mark are absent.
2. drop the helper on a current 077 head: actual current-head privilege
   validation refuses (missing-required-object) and the real reconcile
   readiness path raises.
3. an ACTUAL 076-phase database (existing migration harness stopped at
   076_001; lawful setup/harden fixture seams in the reconcile order):
   the current-graph reconcile head gate still refuses it (deliberately
   NOT weakened), the phase-aware apply re-grants the 068 public_mark
   slaif_media EXECUTE at the historical head and the verifier is
   coherent, and the real upgrade() to 077 plus reconcile() reaches ready.
4. effective content USAGE negative: at the ready 077 head, revoking ONLY
   the worker's direct schema USAGE makes the real worker probe fail
   42501 and the current verifier flag exactly
   schema/content/slaif_review_worker/effective-usage-missing (the
   membership-reachable reviewer USAGE alone no longer satisfies it);
   the real reconcile restores the grant, the verifier is safe again and
   the actual worker helper call succeeds.
"""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from slaif_agent_site.agent_state.foundation import (
    deploy_cow_functions,
    enable_cow_schema,
    harden_cow_schema,
)
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    reconcile,
    upgrade,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.db.privileges import (
    apply_product_privileges,
    revoke_public_foundation_access,
    verify_database_privileges,
)
from slaif_agent_site.db.readiness import ReadinessState
from slaif_agent_site.db.roles import (
    REVIEW_WORKER_ROLE,
    REVIEWER_ROLES,
    RUNTIME_ROLES,
)

# regprocedure IDENTITY (full signature): existence, DROP, to_regprocedure.
_PUBLICIZE_IDENTITY = "content.slaif_media_publicize_promoted(uuid,uuid[])"
# callable name only: actual EXECUTE probes (no double-parenthesis SQL).
_PUBLICIZE_CALLABLE = "content.slaif_media_publicize_promoted"
_CREATOR_IDENTITY = (
    "content.slaif_media_create(uuid,uuid,text,text,bigint,text,text,text,jsonb)"
)
_LEGACY_MARK_IDENTITY = "content.slaif_media_public_mark(uuid,uuid,uuid,uuid)"

# every existing non-owner/non-worker product role (roles.py ROLE_NAMES)
DENIAL_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)

_PROBE_SITE = "11111111-1111-1111-1111-111111111111"
_DENIED_SITE = "22222222-2222-2222-2222-222222222222"


async def _head(database: AgentSiteDatabase) -> str:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return str(
            await owner.fetchval(
                "SELECT version_num::text FROM control.alembic_version"
            )
        )


async def _function_shape(
    database: AgentSiteDatabase, identity: str
) -> dict[str, Any] | None:
    """Owner-side ACL shape for one exact regprocedure identity (None if absent)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT o.rolname AS owner_r, "
            "COALESCE(bool_or(a.grantee = 0 AND a.privilege_type = 'EXECUTE'),"
            " false) AS public_exec, "
            "array_agg(DISTINCT g.rolname) FILTER"
            " (WHERE a.privilege_type = 'EXECUTE') AS execute_grantees "
            "FROM pg_catalog.pg_proc p "
            "JOIN pg_catalog.pg_roles o ON o.oid = p.proowner "
            "LEFT JOIN LATERAL aclexplode(p.proacl) a ON true "
            "LEFT JOIN pg_catalog.pg_roles g ON g.oid = a.grantee "
            "WHERE p.oid = to_regprocedure($1) "
            "GROUP BY o.rolname",
            identity,
        )
    return dict(row) if row is not None else None


async def _probe_callable(conn: asyncpg.Connection) -> None:
    """EXECUTE the present helper with an empty referenced set (no-op body)."""
    await conn.execute(
        f"SELECT {_PUBLICIZE_CALLABLE}($1::uuid, $2::uuid[])",
        _PROBE_SITE,
        [],
    )


async def _probe_refused(conn: asyncpg.Connection) -> None:
    with pytest.raises(asyncpg.InsufficientPrivilegeError) as excinfo:
        await conn.execute(
            f"SELECT {_PUBLICIZE_CALLABLE}($1::uuid, $2::uuid[])",
            _DENIED_SITE,
            [],
        )
    assert excinfo.value.sqlstate == "42501"


@pytest.mark.asyncio
async def test_077_fresh_hardened_reviewer_only_publicize(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)  # harden + apply + verify => ready at 077
    assert await _head(database) == "077_001"

    # the legacy creator/mark were dropped by 077 (exact identities)
    assert await _function_shape(database, _CREATOR_IDENTITY) is None
    assert await _function_shape(database, _LEGACY_MARK_IDENTITY) is None

    # grant shape: owner slaif_owner, no PUBLIC execute, worker only
    shape = await _function_shape(database, _PUBLICIZE_IDENTITY)
    assert shape is not None, "publication helper missing at 077 head"
    assert shape["owner_r"] == "slaif_owner"
    assert shape["public_exec"] is False
    # REQUIRE the worker EXECUTE; allow only the known owner + worker
    # (the default explicit owner EXECUTE may lawfully remain)
    grantees = set(shape["execute_grantees"] or [])
    assert "slaif_review_worker" in grantees
    assert grantees <= {"slaif_owner", "slaif_review_worker"}

    # real reviewer-worker login (SET ROLE envelope): the REACHABLE generic
    # reviewer role still must not unlock the helper (no EXECUTE there)...
    pool = await database.role_pool(REVIEW_WORKER_ROLE)
    try:
        async with pool.acquire() as conn:
            assert (
                await conn.fetchval("SELECT current_user::text") == REVIEW_WORKER_ROLE
            )
            await conn.execute("SET ROLE slaif_reviewer")
            await _probe_refused(conn)
            await conn.execute(f"SET ROLE {REVIEW_WORKER_ROLE}")
            # ...and the worker's own effective role EXECUTEs it (empty
            # referenced set touches no rows: presence + EXECUTE proof,
            # not publication proof).
            await _probe_callable(conn)
    finally:
        await pool.close()

    # every ordinary non-owner/non-worker login refused on the SAME helper
    for role in DENIAL_ROLES:
        denied_pool = await database.role_pool(role)
        try:
            async with denied_pool.acquire() as conn:
                await _probe_refused(conn)
        finally:
            await denied_pool.close()


@pytest.mark.asyncio
async def test_077_missing_helper_refuses_current_head(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(f"DROP FUNCTION {_PUBLICIZE_IDENTITY}")

    # actual current-head privilege validation (no fake source assertion)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        result = await verify_database_privileges(
            owner, readiness_state=ReadinessState.HARDENED
        )
    assert result.safe is False
    assert (
        "function/content.slaif_media_publicize_promoted/missing-required-object"
        in [str(v) for v in result.violations]
    )

    # the real readiness path refuses too
    with pytest.raises(BootstrapStateError) as excinfo:
        await reconcile(database.settings)
    assert "privilege validation failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_076_historical_phase_coherent_then_upgrades_to_077(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    # stop the EXISTING migration harness at the historical 076 head
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="076_001",
    )
    assert await _head(database) == "076_001"
    assert await _function_shape(database, _LEGACY_MARK_IDENTITY) is not None, (
        "068 public_mark must exist at the 076 phase"
    )

    # the current 077-graph reconcile head gate is deliberately preserved:
    # a 076 database is refused until it is upgraded (no gate weakening)
    with pytest.raises(BootstrapStateError) as gate:
        await reconcile(database.settings)
    assert "not at the required migration" in str(gate.value)

    # lawful setup/harden fixture seams in the reconcile order (product
    # public API; the product bootstrap runs this exact sequence)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        executor = AsyncpgExecutor(owner)
        await deploy_cow_functions(executor)
        await revoke_public_foundation_access(owner)
        await enable_cow_schema(
            executor,
            schema="content",
            allow_deferred_fks=True,
            allow_unsafe_canonical_writes=False,
        )
        hardened = await harden_cow_schema(
            executor,
            schema="content",
            runtime_roles=list(RUNTIME_ROLES),
            reviewer_roles=list(REVIEWER_ROLES),
        )
        assert hardened["safe"], hardened["violations"]
        await apply_product_privileges(owner, readiness_state=ReadinessState.HARDENED)
        result = await verify_database_privileges(
            owner, readiness_state=ReadinessState.HARDENED
        )
    # historical phase is coherent under the NEW verifier/apply: the 068
    # public_mark slaif_media grant is re-granted at this head and the 077
    # helper is phase-exempt (existence-guarded grant, head-gated verify)
    assert result.safe is True, [str(v) for v in result.violations]
    mark_shape = await _function_shape(database, _LEGACY_MARK_IDENTITY)
    assert mark_shape is not None, "076 legacy public_mark helper missing"
    assert "slaif_media" in set(mark_shape["execute_grantees"] or [])
    violations = [str(v) for v in result.violations]
    assert not [v for v in violations if "slaif_media" in v]
    assert not [v for v in violations if "publicize" in v]

    # the real upgrade path then reaches a ready 077 head
    await upgrade(database.settings)
    await reconcile(database.settings)
    assert await _head(database) == "077_001"
    assert await _function_shape(database, _PUBLICIZE_IDENTITY) is not None
    assert await _function_shape(database, _LEGACY_MARK_IDENTITY) is None
    assert await _function_shape(database, _CREATOR_IDENTITY) is None


@pytest.mark.asyncio
async def test_077_effective_worker_usage_negative_and_reconcile_restore(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        before = await verify_database_privileges(
            owner, readiness_state=ReadinessState.HARDENED
        )
    assert before.safe is True, [str(v) for v in before.violations]
    before_set = {str(v) for v in before.violations}

    # preconditions: the worker's DIRECT content USAGE (its own effective
    # role, NOINHERIT membership inherits nothing) and the generic
    # reviewer's own USAGE both exist before the revoke
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        worker_direct = await owner.fetchval(
            "SELECT has_schema_privilege('slaif_review_worker', 'content', 'USAGE')"
        )
        reviewer_own = await owner.fetchval(
            "SELECT has_schema_privilege('slaif_reviewer', 'content', 'USAGE')"
        )
    assert worker_direct is True
    assert reviewer_own is True

    # actual worker helper call before the revoke
    pool = await database.role_pool(REVIEW_WORKER_ROLE)
    try:
        async with pool.acquire() as conn:
            await _probe_callable(conn)
    finally:
        await pool.close()

    # revoke ONLY the worker's direct schema USAGE (owner-side, exact)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute('REVOKE USAGE ON SCHEMA content FROM "slaif_review_worker"')

    # the real worker probe now fails 42501: the membership-reachable
    # reviewer USAGE cannot be combined with the worker's own effective
    # role (NOINHERIT), so the schema no longer resolves for it
    pool = await database.role_pool(REVIEW_WORKER_ROLE)
    try:
        async with pool.acquire() as conn:
            with pytest.raises(asyncpg.InsufficientPrivilegeError) as excinfo:
                await _probe_callable(conn)
            assert excinfo.value.sqlstate == "42501"
    finally:
        await pool.close()

    # the current verifier flags EXACTLY the new effective-usage violation
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        after = await verify_database_privileges(
            owner, readiness_state=ReadinessState.HARDENED
        )
    after_set = {str(v) for v in after.violations}
    assert after.safe is False
    assert after_set - before_set == {
        "schema/content/slaif_review_worker/effective-usage-missing"
    }

    # the real reconcile restores the direct grant and readiness
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        restored = await verify_database_privileges(
            owner, readiness_state=ReadinessState.HARDENED
        )
    assert restored.safe is True, [str(v) for v in restored.violations]

    # actual worker helper call succeeds again
    pool = await database.role_pool(REVIEW_WORKER_ROLE)
    try:
        async with pool.acquire() as conn:
            await _probe_callable(conn)
    finally:
        await pool.close()

"""Real PostgreSQL proof for capability-bound browser-run control state."""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import asyncpg
import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from slaif_agent_site.agent_state.foundation import get_session_operations
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.browser_contracts import preview_run_request_digest
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES

BEGIN_SQL = """
SELECT * FROM control.slaif_agent_browser_run_begin(
    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17
)
"""
GET_SQL = "SELECT * FROM control.slaif_agent_browser_run_get($1,$2,$3,$4,$5)"
ARTIFACT_LIST_SQL = (
    "SELECT * FROM control.slaif_agent_browser_artifact_list($1,$2,$3,$4,$5)"
)
CLAIM_SQL = "SELECT * FROM control.slaif_agent_browser_run_claim($1,$2)"
RENEW_SQL = "SELECT control.slaif_agent_browser_run_renew($1,$2,$3)"
RELEASE_SQL = "SELECT control.slaif_agent_browser_run_release($1,$2)"
COMPLETE_SQL = "SELECT control.slaif_agent_browser_run_complete($1,$2,$3,$4,$5,$6)"
REGISTER_SQL = (
    "SELECT control.slaif_agent_browser_artifact_register("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10)"
)


@dataclass(frozen=True, slots=True)
class Binding:
    capability_id: uuid.UUID
    site_id: uuid.UUID
    workspace_id: uuid.UUID
    delegator_id: uuid.UUID


async def _insert_user(owner: asyncpg.Connection[Any], suffix: str) -> uuid.UUID:
    user_id = await owner.fetchval(
        """
        INSERT INTO control.user_account (
            id, identity_kind, local_username, local_username_normalized,
            password_hash, display_name, status
        ) VALUES (
            gen_random_uuid(), 'LOCAL', $1, $2,
            '$argon2id$v=19$m=65536,t=3,p=4$'
            'AAAAAAAAAAAAAAAAAAAAAA$'
            'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
            $3, 'ACTIVE'
        ) RETURNING id
        """,
        f"Browser.{suffix}",
        f"browser.{suffix}",
        f"Browser {suffix}",
    )
    assert isinstance(user_id, uuid.UUID)
    return user_id


async def _insert_site(owner: asyncpg.Connection[Any], suffix: str) -> uuid.UUID:
    site_id = await owner.fetchval(
        """
        INSERT INTO control.site (
            site_key, display_name, default_locale, component_catalog_version
        ) VALUES ($1, $2, 'en-US', 'catalog-v1') RETURNING id
        """,
        f"browser-{suffix}",
        f"Browser {suffix}",
    )
    assert isinstance(site_id, uuid.UUID)
    return site_id


async def _insert_workspace(
    owner: asyncpg.Connection[Any],
    *,
    site_id: uuid.UUID,
    delegator_id: uuid.UUID,
    suffix: str,
) -> uuid.UUID:
    workspace_id = await owner.fetchval(
        """
        INSERT INTO control.workspace (
            site_id, created_by, actor_type, title, delegation_preset,
            effective_scopes, status, expires_at
        ) VALUES (
            $1, $2, 'AGENT', $3, 'L1',
            '["preview:inspect"]'::jsonb, 'ACTIVE',
            CURRENT_TIMESTAMP + interval '2 hours'
        ) RETURNING id
        """,
        site_id,
        delegator_id,
        f"Browser workspace {suffix}",
    )
    assert isinstance(workspace_id, uuid.UUID)
    return workspace_id


async def _insert_capability(
    owner: asyncpg.Connection[Any],
    *,
    site_id: uuid.UUID,
    workspace_id: uuid.UUID,
    delegator_id: uuid.UUID,
    suffix: str,
    scopes: tuple[str, ...] = ("preview:inspect",),
    max_runs: int = 20,
    max_concurrent: int = 2,
    max_screenshots: int = 50,
    max_artifact_bytes: int = 100_000,
    max_routes: int = 10,
    max_evidence: int = 9,
    max_duration: int = 120,
    max_attempts: int = 3,
    targets: tuple[str, ...] = (
        "desktop-chromium",
        "tablet",
        "mobile-chromium",
    ),
) -> Binding:
    capability_id = await owner.fetchval(
        """
        INSERT INTO control.capability (
            workspace_id, public_id, secret_digest, scopes, expires_at,
            browser_max_runs, browser_max_concurrent_runs,
            browser_max_screenshots, browser_max_artifact_bytes,
            browser_max_routes_per_run, browser_max_evidence_per_run,
            browser_max_duration_seconds, browser_max_attempts,
            browser_allowed_targets
        ) VALUES (
            $1, $2, $3, $4::jsonb,
            CURRENT_TIMESTAMP + interval '1 hour',
            $5,$6,$7,$8,$9,$10,$11,$12,$13::text[]
        ) RETURNING id
        """,
        workspace_id,
        f"browser-{suffix}-{uuid.uuid4().hex}",
        hashlib.sha256(suffix.encode()).hexdigest(),
        json.dumps(scopes),
        max_runs,
        max_concurrent,
        max_screenshots,
        max_artifact_bytes,
        max_routes,
        max_evidence,
        max_duration,
        max_attempts,
        list(targets),
    )
    return Binding(capability_id, site_id, workspace_id, delegator_id)


async def _prepare(
    database: AgentSiteDatabase,
) -> tuple[dict[str, Binding], dict[str, uuid.UUID]]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        delegator_a = await _insert_user(owner, uuid.uuid4().hex[:10])
        delegator_b = await _insert_user(owner, uuid.uuid4().hex[:10])
        site_a = await _insert_site(owner, uuid.uuid4().hex[:10])
        site_b = await _insert_site(owner, uuid.uuid4().hex[:10])
        workspace_a = await _insert_workspace(
            owner,
            site_id=site_a,
            delegator_id=delegator_a,
            suffix="a",
        )
        workspace_b = await _insert_workspace(
            owner,
            site_id=site_b,
            delegator_id=delegator_b,
            suffix="b",
        )
        bindings = {
            "primary": await _insert_capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=delegator_a,
                suffix="primary",
                max_concurrent=10,
                max_attempts=2,
            ),
            "independent": await _insert_capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=delegator_a,
                suffix="independent",
                max_concurrent=10,
            ),
            "foreign": await _insert_capability(
                owner,
                site_id=site_b,
                workspace_id=workspace_b,
                delegator_id=delegator_b,
                suffix="foreign",
                max_concurrent=10,
            ),
            "missing_scope": await _insert_capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=delegator_a,
                suffix="missing-scope",
                scopes=("site:read",),
            ),
            "race": await _insert_capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=delegator_a,
                suffix="race",
            ),
            "cancel": await _insert_capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=delegator_a,
                suffix="cancel",
            ),
        }
        quota_specs: dict[str, dict[str, Any]] = {
            "total": {"max_runs": 0, "max_concurrent": 0},
            "concurrent": {"max_runs": 2, "max_concurrent": 0},
            "screenshot": {"max_screenshots": 0},
            "artifact": {"max_artifact_bytes": 10},
            "route": {"max_routes": 0},
            "evidence": {"max_evidence": 1},
            "duration": {"max_duration": 5},
            "target": {"targets": ("tablet",)},
        }
        for name, limits in quota_specs.items():
            bindings[f"quota_{name}"] = await _insert_capability(
                owner,
                site_id=site_a,
                workspace_id=workspace_a,
                delegator_id=delegator_a,
                suffix=f"quota-{name}",
                **limits,
            )
    return bindings, {
        "site_a": site_a,
        "site_b": site_b,
        "workspace_a": workspace_a,
        "workspace_b": workspace_b,
    }


def _begin_arguments(
    binding: Binding,
    *,
    key: str,
    route: str = "/news?locale=en",
    target: str = "desktop-chromium",
    evidence: tuple[str, ...] = ("screenshot", "heading-summary"),
    request_digest: str | None = None,
    operation_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    reserved_artifact_bytes: int = 500,
    reserved_routes: int = 1,
    duration_seconds: int = 30,
) -> tuple[object, ...]:
    digest = request_digest or preview_run_request_digest(
        {
            "version": "browser-preview/v1",
            "route": route,
            "target": target,
            "evidence": list(evidence),
        }
    )
    return (
        binding.capability_id,
        binding.site_id,
        binding.workspace_id,
        binding.delegator_id,
        key,
        digest,
        operation_id or uuid.uuid4(),
        run_id or uuid.uuid4(),
        "browser-preview/v1",
        route,
        hashlib.sha256(route.encode()).hexdigest(),
        target,
        list(evidence),
        1 if "screenshot" in evidence else 0,
        reserved_artifact_bytes,
        reserved_routes,
        duration_seconds,
    )


async def _wait_for_advisory_waiter(
    administrator: asyncpg.Connection[Any], pid: int
) -> None:
    for _ in range(200):
        row = await administrator.fetchrow(
            "SELECT wait_event_type, wait_event, state "
            "FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
        if row is not None and tuple(row) == ("Lock", "advisory", "active"):
            return
        await asyncio.sleep(0.01)
    raise AssertionError("browser begin did not wait on the workspace advisory lock")


async def _counts_for_capability(
    database: AgentSiteDatabase, capability_id: uuid.UUID
) -> tuple[int, int, int]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(
            "SELECT "
            "(SELECT count(*) FROM control.browser_run WHERE capability_id = $1), "
            "(SELECT count(*) FROM control.browser_idempotency "
            "WHERE capability_id = $1), "
            "(SELECT count(*) FROM audit.browser_event WHERE capability_id = $1)",
            capability_id,
        )
    return int(row[0]), int(row[1]), int(row[2])


@pytest.mark.asyncio
async def test_browser_begin_idempotency_quotas_isolation_and_lock_recheck(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    bindings, ids = await _prepare(database)
    primary = bindings["primary"]
    pool_a = await database.role_pool("slaif_agent_runtime")
    pool_b = await database.role_pool("slaif_agent_runtime")
    try:
        shared_key = "same-key"
        shared_digest = "a" * 64
        first_args = _begin_arguments(
            primary, key=shared_key, request_digest=shared_digest
        )
        second_args = _begin_arguments(
            primary, key=shared_key, request_digest=shared_digest
        )

        async def begin(pool: asyncpg.Pool[Any], arguments: tuple[object, ...]) -> Any:
            async with pool.acquire() as connection:
                return await connection.fetchrow(BEGIN_SQL, *arguments)

        first, second = await asyncio.gather(
            begin(pool_a, first_args), begin(pool_b, second_args)
        )
        assert {first["result"], second["result"]} == {"STARTED", "REPLAY"}
        assert first["run_id"] == second["run_id"]
        assert first["operation_id"] == second["operation_id"]
        assert await _counts_for_capability(database, primary.capability_id) == (
            1,
            1,
            1,
        )

        async with pool_a.acquire() as agent:
            mismatch = await agent.fetchrow(
                BEGIN_SQL,
                *_begin_arguments(primary, key=shared_key, request_digest="b" * 64),
            )
            assert mismatch["result"] == "MISMATCH"
            assert mismatch["run_id"] == first["run_id"]
            before_reads = await _counts_for_capability(database, primary.capability_id)
            visible = await agent.fetchrow(
                GET_SQL,
                primary.capability_id,
                primary.site_id,
                primary.workspace_id,
                primary.delegator_id,
                first["run_id"],
            )
            assert visible["state"] == "QUEUED"
            assert (
                await agent.fetch(
                    GET_SQL,
                    bindings["foreign"].capability_id,
                    primary.site_id,
                    primary.workspace_id,
                    primary.delegator_id,
                    first["run_id"],
                )
                == []
            )
            assert (
                await agent.fetch(
                    GET_SQL,
                    primary.capability_id,
                    ids["site_b"],
                    ids["workspace_b"],
                    bindings["foreign"].delegator_id,
                    first["run_id"],
                )
                == []
            )
            assert (
                await agent.fetch(
                    GET_SQL,
                    primary.capability_id,
                    primary.site_id,
                    primary.workspace_id,
                    primary.delegator_id,
                    uuid.uuid4(),
                )
                == []
            )
            assert (
                await agent.fetch(
                    ARTIFACT_LIST_SQL,
                    primary.capability_id,
                    primary.site_id,
                    primary.workspace_id,
                    primary.delegator_id,
                    first["run_id"],
                )
                == []
            )
            assert await agent.fetchval("SELECT 1") == 1
        assert (
            await _counts_for_capability(database, primary.capability_id)
            == before_reads
        )

        async with pool_a.acquire() as agent:
            independent = await agent.fetchrow(
                BEGIN_SQL,
                *_begin_arguments(bindings["independent"], key="independent"),
            )
            assert independent["result"] == "STARTED"
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(
                    BEGIN_SQL,
                    *_begin_arguments(bindings["missing_scope"], key="missing"),
                )
            forged = _begin_arguments(primary, key="forged")
            forged = (
                forged[0],
                ids["site_b"],
                ids["workspace_b"],
                bindings["foreign"].delegator_id,
                *forged[4:],
            )
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(BEGIN_SQL, *forged)

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET revoked_at = CURRENT_TIMESTAMP "
                "WHERE id = $1",
                primary.capability_id,
            )
        async with pool_a.acquire() as agent:
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(
                    BEGIN_SQL, *_begin_arguments(primary, key="revoked")
                )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET revoked_at = NULL, "
                "expires_at = CURRENT_TIMESTAMP - interval '1 second' WHERE id = $1",
                primary.capability_id,
            )
        async with pool_a.acquire() as agent:
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(
                    BEGIN_SQL, *_begin_arguments(primary, key="expired-capability")
                )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET expires_at = "
                "CURRENT_TIMESTAMP + interval '1 hour' "
                "WHERE id = $1",
                primary.capability_id,
            )
            await owner.execute(
                "UPDATE control.workspace SET status = 'REVOKED' WHERE id = $1",
                primary.workspace_id,
            )
        async with pool_a.acquire() as agent:
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(
                    BEGIN_SQL, *_begin_arguments(primary, key="revoked-workspace")
                )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET status = 'ACTIVE', "
                "expires_at = CURRENT_TIMESTAMP - interval '1 second' WHERE id = $1",
                primary.workspace_id,
            )
        async with pool_a.acquire() as agent:
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(
                    BEGIN_SQL, *_begin_arguments(primary, key="expired-workspace")
                )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET expires_at = "
                "CURRENT_TIMESTAMP + interval '2 hours' "
                "WHERE id = $1",
                primary.workspace_id,
            )
            await owner.execute(
                "UPDATE control.site SET status = 'ARCHIVED' WHERE id = $1",
                primary.site_id,
            )
        async with pool_a.acquire() as agent:
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchrow(
                    BEGIN_SQL, *_begin_arguments(primary, key="archived-site")
                )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.site SET status = 'ACTIVE' WHERE id = $1",
                primary.site_id,
            )

        quota_calls: dict[str, dict[str, Any]] = {
            "quota_total": {},
            "quota_concurrent": {},
            "quota_screenshot": {},
            "quota_artifact": {"reserved_artifact_bytes": 11},
            "quota_route": {},
            "quota_evidence": {},
            "quota_duration": {"duration_seconds": 6},
            "quota_target": {},
        }
        async with pool_a.acquire() as agent:
            for name, changes in quota_calls.items():
                binding = bindings[name]
                with pytest.raises(asyncpg.PostgresError):
                    await agent.fetchrow(
                        BEGIN_SQL,
                        *_begin_arguments(binding, key=name, **changes),
                    )
                assert await agent.fetchval("SELECT 1") == 1
        for name in quota_calls:
            assert await _counts_for_capability(
                database, bindings[name].capability_id
            ) == (0, 0, 0)

        race = bindings["race"]
        race_arguments = _begin_arguments(race, key="freeze-race")
        async with pool_a.acquire() as agent:
            blocked_pid = agent.get_server_pid()
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                async with owner.transaction():
                    await owner.fetchval(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                        str(race.workspace_id),
                    )
                    blocked = asyncio.create_task(
                        agent.fetchrow(BEGIN_SQL, *race_arguments)
                    )
                    await _wait_for_advisory_waiter(database.administrator, blocked_pid)
                    assert not blocked.done()
                    await owner.execute(
                        "UPDATE control.capability SET revoked_at = CURRENT_TIMESTAMP "
                        "WHERE id = $1",
                        race.capability_id,
                    )
            with pytest.raises(asyncpg.PostgresError):
                await blocked
            assert await agent.fetchval("SELECT 1") == 1
        assert await _counts_for_capability(database, race.capability_id) == (0, 0, 0)

        cancel = bindings["cancel"]
        cancel_arguments = _begin_arguments(cancel, key="cancelled-wait")
        async with pool_a.acquire() as agent:
            blocked_pid = agent.get_server_pid()

            async def cancelled_begin() -> Any:
                async with agent.transaction():
                    return await agent.fetchrow(BEGIN_SQL, *cancel_arguments)

            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                async with owner.transaction():
                    await owner.fetchval(
                        "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                        str(cancel.workspace_id),
                    )
                    cancelled = asyncio.create_task(cancelled_begin())
                    await _wait_for_advisory_waiter(database.administrator, blocked_pid)
                    cancelled.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await cancelled
            assert await agent.fetchval("SELECT 1") == 1
        assert await _counts_for_capability(database, cancel.capability_id) == (0, 0, 0)
    finally:
        await pool_b.close()
        await pool_a.close()


@pytest.mark.asyncio
async def test_browser_leases_artifacts_terminal_state_and_exact_privileges(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    bindings, _ids = await _prepare(database)
    binding = bindings["primary"]
    pool_a = await database.role_pool("slaif_agent_runtime")
    pool_b = await database.role_pool("slaif_agent_runtime")
    try:
        async with pool_a.acquire() as agent:
            retry = await agent.fetchrow(
                BEGIN_SQL,
                *_begin_arguments(binding, key="retry", duration_seconds=30),
            )
            completion = await agent.fetchrow(
                BEGIN_SQL,
                *_begin_arguments(binding, key="completion", duration_seconds=30),
            )
            release = await agent.fetchrow(
                BEGIN_SQL,
                *_begin_arguments(binding, key="release", duration_seconds=30),
            )
            assert [retry["result"], completion["result"], release["result"]] == [
                "STARTED",
                "STARTED",
                "STARTED",
            ]

        first_lease = uuid.uuid4()
        async with pool_a.acquire() as claimant, pool_b.acquire() as other:
            async with claimant.transaction():
                claimed = await claimant.fetchrow(CLAIM_SQL, first_lease, 1)
                assert claimed["run_id"] == retry["run_id"]
                assert claimed["attempt"] == 1
                assert await other.fetchrow(CLAIM_SQL, uuid.uuid4(), 30) is not None
                # The second claimant skips the locked first row and obtains the
                # next deterministic queue item rather than the same run.
                second_claimed = await other.fetchrow(
                    GET_SQL,
                    binding.capability_id,
                    binding.site_id,
                    binding.workspace_id,
                    binding.delegator_id,
                    completion["run_id"],
                )
                assert second_claimed["state"] == "RUNNING"

        await asyncio.sleep(1.1)
        second_lease = uuid.uuid4()
        async with pool_a.acquire() as agent:
            retried = await agent.fetchrow(CLAIM_SQL, second_lease, 1)
            assert retried["run_id"] == retry["run_id"]
            assert retried["attempt"] == 2
        await asyncio.sleep(1.1)
        async with pool_a.acquire() as agent:
            next_claim = await agent.fetchrow(CLAIM_SQL, uuid.uuid4(), 30)
            assert next_claim["run_id"] == release["run_id"]
            retry_status = await agent.fetchrow(
                GET_SQL,
                binding.capability_id,
                binding.site_id,
                binding.workspace_id,
                binding.delegator_id,
                retry["run_id"],
            )
            assert (retry_status["state"], retry_status["error_code"]) == (
                "FAILED",
                "MAX_ATTEMPTS",
            )

            release_lease = next_claim["lease_id"]
            renewed = await agent.fetchval(
                RENEW_SQL, release["run_id"], release_lease, 30
            )
            assert renewed > datetime.now(UTC)
            assert (
                await agent.fetchval(RELEASE_SQL, release["run_id"], release_lease)
                == "QUEUED"
            )
            released_again = await agent.fetchrow(CLAIM_SQL, uuid.uuid4(), 30)
            assert released_again["run_id"] == release["run_id"]
            assert (
                await agent.fetchval(
                    RELEASE_SQL, release["run_id"], released_again["lease_id"]
                )
                == "FAILED"
            )

        # The completion run was leased by the concurrent claimant above.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            completion_lease = await owner.fetchval(
                "SELECT lease_id FROM control.browser_run WHERE id = $1",
                completion["run_id"],
            )
            assert completion_lease is not None
        artifact_id = uuid.uuid4()
        artifact_expiry = datetime.now(UTC) + timedelta(minutes=10)
        route = "/news?locale=en"
        route_digest = hashlib.sha256(route.encode()).hexdigest()
        async with pool_a.acquire() as agent:
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchval(
                    COMPLETE_SQL,
                    completion["run_id"],
                    completion_lease,
                    "RUNNING",
                    json.dumps({}),
                    None,
                    None,
                )
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchval(
                    REGISTER_SQL,
                    completion["run_id"],
                    completion_lease,
                    artifact_id,
                    "screenshot",
                    "image/png",
                    "c" * 64,
                    100,
                    "tablet",
                    route_digest,
                    artifact_expiry,
                )
            assert (
                await agent.fetchval(
                    REGISTER_SQL,
                    completion["run_id"],
                    completion_lease,
                    artifact_id,
                    "screenshot",
                    "image/png",
                    "c" * 64,
                    100,
                    "desktop-chromium",
                    route_digest,
                    artifact_expiry,
                )
                == artifact_id
            )
            assert (
                await agent.fetchval(
                    REGISTER_SQL,
                    completion["run_id"],
                    completion_lease,
                    artifact_id,
                    "screenshot",
                    "image/png",
                    "c" * 64,
                    100,
                    "desktop-chromium",
                    route_digest,
                    artifact_expiry,
                )
                == artifact_id
            )
            assert (
                await agent.fetchval(
                    COMPLETE_SQL,
                    completion["run_id"],
                    completion_lease,
                    "COMPLETED",
                    json.dumps({"ok": True}),
                    None,
                    None,
                )
                == "COMPLETED"
            )
            assert (
                await agent.fetchval(
                    COMPLETE_SQL,
                    completion["run_id"],
                    completion_lease,
                    "COMPLETED",
                    json.dumps({"ok": True}),
                    None,
                    None,
                )
                == "COMPLETED"
            )
            artifacts = await agent.fetch(
                ARTIFACT_LIST_SQL,
                binding.capability_id,
                binding.site_id,
                binding.workspace_id,
                binding.delegator_id,
                completion["run_id"],
            )
            assert len(artifacts) == 1
            assert tuple(
                artifacts[0][key]
                for key in ("artifact_id", "kind", "mime_type", "visibility")
            ) == (artifact_id, "screenshot", "image/png", "PRIVATE")
            event_count = await _counts_for_capability(database, binding.capability_id)
            await agent.fetch(
                GET_SQL,
                binding.capability_id,
                binding.site_id,
                binding.workspace_id,
                binding.delegator_id,
                completion["run_id"],
            )
            await agent.fetch(
                ARTIFACT_LIST_SQL,
                binding.capability_id,
                binding.site_id,
                binding.workspace_id,
                binding.delegator_id,
                completion["run_id"],
            )
            assert (
                await _counts_for_capability(database, binding.capability_id)
                == event_count
            )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await get_session_operations(
                    AsyncpgExecutor(owner), binding.workspace_id, schema="content"
                )
                == []
            )
            terminal_events = await owner.fetchval(
                "SELECT count(*) FROM audit.browser_event "
                "WHERE run_id = $1 AND event_type = 'COMPLETED'",
                completion["run_id"],
            )
            artifact_events = await owner.fetchval(
                "SELECT count(*) FROM audit.browser_event "
                "WHERE run_id = $1 AND event_type = 'ARTIFACT_REGISTERED'",
                completion["run_id"],
            )
            assert (terminal_events, artifact_events) == (1, 1)
            await owner.execute(
                "UPDATE control.capability SET revoked_at = CURRENT_TIMESTAMP "
                "WHERE id = $1",
                binding.capability_id,
            )
        async with pool_a.acquire() as agent:
            assert (
                await agent.fetch(
                    ARTIFACT_LIST_SQL,
                    binding.capability_id,
                    binding.site_id,
                    binding.workspace_id,
                    binding.delegator_id,
                    completion["run_id"],
                )
                == []
            )
            with pytest.raises(asyncpg.PostgresError):
                await agent.fetchval(
                    REGISTER_SQL,
                    completion["run_id"],
                    completion_lease,
                    uuid.uuid4(),
                    "heading-summary",
                    "application/json",
                    "d" * 64,
                    10,
                    "desktop-chromium",
                    route_digest,
                    artifact_expiry,
                )
            for relation in (
                "control.browser_run",
                "control.browser_idempotency",
                "control.browser_artifact",
                "audit.browser_event",
                "control.capability",
                "content.page_base",
                "content.page_changes",
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await agent.fetch(f"SELECT * FROM {relation}")
            for function in (
                "control.slaif_setup_status()",
                "control.slaif_workspace_get(NULL::uuid)",
                "control.slaif_workspace_accept(NULL::uuid)",
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await agent.fetchval(f"SELECT {function}")
            assert await agent.fetchval("SELECT 1") == 1

        for role in ROLE_NAMES[1:]:
            if role == "slaif_agent_runtime":
                continue
            role_pool = await database.role_pool(role)
            try:
                async with role_pool.acquire() as connection:
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetchrow(
                            BEGIN_SQL,
                            *_begin_arguments(bindings["independent"], key=role),
                        )
                    for relation in (
                        "control.browser_run",
                        "control.browser_idempotency",
                        "control.browser_artifact",
                        "audit.browser_event",
                    ):
                        with pytest.raises(asyncpg.InsufficientPrivilegeError):
                            await connection.fetch(f"SELECT * FROM {relation}")
            finally:
                await role_pool.close()

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            functions = await owner.fetch(
                "SELECT proc.proname::text, owner.rolname::text, proc.prosecdef, "
                "COALESCE(array_to_string(proc.proconfig, ','), ''), "
                "has_function_privilege('slaif_agent_runtime', proc.oid, 'EXECUTE'), "
                "has_function_privilege('slaif_editor_runtime', proc.oid, 'EXECUTE'), "
                "EXISTS (SELECT 1 FROM pg_catalog.aclexplode(COALESCE("
                "proc.proacl, pg_catalog.acldefault('f', proc.proowner))) AS acl "
                "WHERE acl.grantee = 0 AND acl.privilege_type = 'EXECUTE') "
                "FROM pg_catalog.pg_proc AS proc "
                "JOIN pg_catalog.pg_namespace AS namespace_ "
                "ON namespace_.oid = proc.pronamespace "
                "JOIN pg_catalog.pg_roles AS owner ON owner.oid = proc.proowner "
                "WHERE namespace_.nspname = 'control' "
                "AND proc.proname LIKE 'slaif_agent_browser_%' "
                "ORDER BY proc.proname"
            )
            assert len(functions) == 9
            for row in functions:
                is_private_helper = row["proname"] == "slaif_agent_browser_authorized"
                assert row["rolname"] == "slaif_owner"
                assert row["prosecdef"] is True
                assert "search_path=pg_catalog" in row[3]
                assert row[4] is (not is_private_helper)
                assert row[5] is False
                assert row[6] is False
    finally:
        await pool_b.close()
        await pool_a.close()

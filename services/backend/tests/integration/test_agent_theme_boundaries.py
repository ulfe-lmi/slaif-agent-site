"""Focused PostgreSQL proof for the 078-q trusted theme boundaries."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_state.foundation import asyncpg_cow_reviewer
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection
from test_agent_mutations import (
    _agent_settings,
    _capability_with_scopes,
    _seed,
    _set_resource_constraints,
    _workspace_capability,
    asyncpg_cow_session,
)


async def _theme_state(
    database: AgentSiteDatabase, seeded: dict[str, UUID], reviewer_pool: Any
) -> tuple[Any, ...]:
    """Capture physical theme, durable Agent accounting, and COW operations."""

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        base = await owner.fetchrow(
            "SELECT count(*), coalesce(min(row_version),0), "
            "min(updated_at)::text FROM content.theme_base WHERE site_id=$1",
            seeded["site_id"],
        )
        changes = await owner.fetchval(
            "SELECT count(*) FROM content.theme_changes WHERE site_id=$1",
            seeded["site_id"],
        )
        accounting = await owner.fetchrow(
            "SELECT coalesce(sum(mutation_used),0), "
            "(SELECT count(*) FROM control.agent_idempotency WHERE workspace_id=$1), "
            "(SELECT count(*) FROM audit.agent_mutation WHERE workspace_id=$1) "
            "FROM control.capability WHERE workspace_id=$1",
            seeded["workspace_id"],
        )
        watermark = await owner.fetchval(
            "SELECT operation_watermark FROM control.workspace WHERE id=$1",
            seeded["workspace_id"],
        )
    async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
        operations = await reviewer.operations(seeded["workspace_id"], schema="content")
    return tuple(base), changes, tuple(accounting), watermark, len(operations)


@asynccontextmanager
async def _agent_client(
    database: AgentSiteDatabase,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
        ) as client:
            yield client


async def _direct_theme_update(
    agent_pool: Any,
    seeded: dict[str, UUID],
    *,
    group: str,
    encoded_value: str,
    expected: int = 1,
    forged_no_effect: bool = False,
) -> None:
    values: dict[str, str | None] = {
        "palette": None,
        "typography": None,
        "layout": None,
        "shape": None,
    }
    values[group] = encoded_value
    async with asyncpg_cow_session(
        agent_pool, session_id=seeded["workspace_id"], operation_id=uuid4()
    ) as cow:
        try:
            await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_theme_update("
                "$1,$2,$3::jsonb,$4::jsonb,$5::jsonb,$6::jsonb,$7)",
                seeded["site_id"],
                expected,
                values["palette"],
                values["typography"],
                values["layout"],
                values["shape"],
                forged_no_effect,
            )
        except asyncpg.PostgresError:
            await cow.rollback()
            raise


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("group", "http_value", "sql_values"),
    (
        (
            "palette",
            {"preset": None},
            (
                '{"preset":null}',
                "[]",
                '{"preset":"url(http://evil.invalid)"}',
                '{"unknown":"x"}',
            ),
        ),
        (
            "typography",
            {"family": None, "scale": "balanced", "weight": "regular"},
            (
                '{"family":null,"scale":"balanced","weight":"regular"}',
                '"raw"',
                '{"family":"@import","scale":"balanced","weight":"regular"}',
                '{"unknown":"x"}',
            ),
        ),
        (
            "layout",
            {"content_width": "md", "spacing": None, "grid_gap": "md"},
            (
                '{"content_width":"md","spacing":null,"grid_gap":"md"}',
                "[]",
                '{"content_width":"md","spacing":"md","grid_gap":"var(--evil)"}',
                '{"unknown":"x"}',
            ),
        ),
        (
            "shape",
            {"radius": None, "shadow": "sm"},
            (
                '{"radius":null,"shadow":"sm"}',
                "[]",
                '{"radius":"calc(1px)","shadow":"sm"}',
                '{"unknown":"x"}',
            ),
        ),
    ),
)
async def test_theme_invalid_values_fail_at_http_and_trusted_sql_without_residue(
    agent_site_database: AgentSiteDatabase,
    group: str,
    http_value: dict[str, Any],
    sql_values: tuple[str, ...],
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database, seeded, ["site:read", "theme:read", "theme-tokens:write"]
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        baseline = await _theme_state(database, seeded, reviewer_pool)
        async with _agent_client(database) as client:
            response = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": f"invalid-http-{group}",
                },
                json={"expected_row_version": 1, group: http_value},
            )
            assert response.status_code == 422, response.text
        assert await _theme_state(database, seeded, reviewer_pool) == baseline

        for encoded in sql_values:
            with pytest.raises(asyncpg.PostgresError, match="THEME_"):
                await _direct_theme_update(
                    agent_pool,
                    seeded,
                    group=group,
                    encoded_value=encoded,
                )
            assert await _theme_state(database, seeded, reviewer_pool) == baseline
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_theme_no_effect_is_read_authorized_and_changed_value_is_not_forgable(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    read_token = await _capability_with_scopes(
        database, seeded, ["site:read", "theme:read"]
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        baseline = await _theme_state(database, seeded, reviewer_pool)
        async with _agent_client(database) as client:
            no_effect = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": "theme-read-only-no-effect",
                },
                json={"expected_row_version": 1, "palette": {"preset": "ocean"}},
            )
            assert no_effect.status_code == 200, no_effect.text
            assert no_effect.json()["record"]["row_version"] == 1
            assert no_effect.json().get("action") is None
            after_no_effect = await _theme_state(database, seeded, reviewer_pool)
            assert after_no_effect[0] == baseline[0]
            assert after_no_effect[1] == baseline[1]
            assert after_no_effect[2][0] == baseline[2][0]
            assert after_no_effect[2][2] == baseline[2][2]
            assert after_no_effect[3] == baseline[3]
            assert after_no_effect[4] == baseline[4]
            assert after_no_effect[2][1] == baseline[2][1] + 1

            replay = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": "theme-read-only-no-effect",
                },
                json={"expected_row_version": 1, "palette": {"preset": "ocean"}},
            )
            assert replay.status_code == 200
            assert replay.content == no_effect.content
            assert (await _theme_state(database, seeded, reviewer_pool))[2][1] == (
                baseline[2][1] + 1
            )

            changed_read_only = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": "theme-read-only-changed",
                },
                json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
            )
            assert changed_read_only.status_code == 403, changed_read_only.text
            assert (
                await _theme_state(database, seeded, reviewer_pool) == after_no_effect
            )

            with pytest.raises(asyncpg.PostgresError, match="AGENT_SCOPE_DENIED"):
                await _direct_theme_update(
                    agent_pool,
                    seeded,
                    group="palette",
                    encoded_value='{"preset":"meadow"}',
                    forged_no_effect=True,
                )
            assert (
                await _theme_state(database, seeded, reviewer_pool) == after_no_effect
            )

            mismatch = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": "theme-read-only-no-effect",
                },
                json={"expected_row_version": 1, "palette": {"preset": "ember"}},
            )
            assert mismatch.status_code == 409, mismatch.text

            missing_read_token = await _capability_with_scopes(
                database, seeded, ["site:read"]
            )
            missing_read = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {missing_read_token}",
                    "Idempotency-Key": "theme-missing-read",
                },
                json={"expected_row_version": 1, "palette": {"preset": "ocean"}},
            )
            assert missing_read.status_code == 403, missing_read.text

            write_token = await _capability_with_scopes(
                database,
                seeded,
                ["site:read", "theme:read", "theme-tokens:write"],
            )
            await _set_resource_constraints(
                database,
                seeded["workspace_id"],
                {
                    "allowed_theme_palette_presets": ["meadow"],
                    "allowed_theme_tokens": ["palette.preset"],
                },
            )
            l3_success = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {write_token}",
                    "Idempotency-Key": "theme-narrowed-l3-success",
                },
                json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
            )
            assert l3_success.status_code == 200, l3_success.text
            assert l3_success.json()["action"] == "THEME_UPDATED"
            assert l3_success.json()["record"]["row_version"] == 2

            replay_changed = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {write_token}",
                    "Idempotency-Key": "theme-narrowed-l3-success",
                },
                json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
            )
            assert replay_changed.status_code == 200
            assert replay_changed.content == l3_success.content

            denied_resource = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {write_token}",
                    "Idempotency-Key": "theme-narrowed-resource-denied",
                },
                json={"expected_row_version": 2, "palette": {"preset": "ember"}},
            )
            assert denied_resource.status_code == 403, denied_resource.text
            await _set_resource_constraints(database, seeded["workspace_id"], {})

            global_token = await _capability_with_scopes(
                database, seeded, ["site:read", "theme:read", "theme-global:write"]
            )
            global_substitution = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {global_token}",
                    "Idempotency-Key": "theme-global-substitution",
                },
                json={"expected_row_version": 2, "palette": {"preset": "ember"}},
            )
            assert global_substitution.status_code == 403, global_substitution.text

            stale = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {write_token}",
                    "Idempotency-Key": "theme-stale-version",
                },
                json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
            )
            assert stale.status_code == 409, stale.text
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_theme_lifecycle_foreign_context_read_purity_and_reconnect(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database, seeded, ["site:read", "theme:read", "theme-tokens:write"]
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        baseline = await _theme_state(database, seeded, reviewer_pool)
        async with _agent_client(database) as client:
            first_read = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert first_read.status_code == 200
            assert await _theme_state(database, seeded, reviewer_pool) == baseline

            with pytest.raises(asyncpg.PostgresError, match="COW_SITE_MISMATCH|AGENT_"):
                async with asyncpg_cow_session(
                    agent_pool, session_id=seeded["workspace_id"], operation_id=uuid4()
                ) as cow:
                    try:
                        await cow.native.fetchrow(
                            "SELECT * FROM content.slaif_agent_theme_get($1)",
                            seeded["site_b_id"],
                        )
                    except asyncpg.PostgresError:
                        await cow.rollback()
                        raise

            await _set_resource_constraints(
                database, seeded["workspace_id"], {"allowed_theme_tokens": [1]}
            )
            with pytest.raises(asyncpg.PostgresError, match="permission denied"):
                async with asyncpg_cow_session(
                    agent_pool, session_id=seeded["workspace_id"], operation_id=uuid4()
                ) as cow:
                    try:
                        await cow.native.fetchrow(
                            "SELECT * FROM "
                            "control.slaif_agent_resource_constraints($1)",
                            seeded["site_id"],
                        )
                    except asyncpg.PostgresError:
                        await cow.rollback()
                        raise
            with pytest.raises(
                asyncpg.PostgresError, match="INVALID_RESOURCE_CONSTRAINTS"
            ):
                await _direct_theme_update(
                    agent_pool,
                    seeded,
                    group="palette",
                    encoded_value='{"preset":"meadow"}',
                )
            await _set_resource_constraints(database, seeded["workspace_id"], {})

            await _set_resource_constraints(
                database,
                seeded["workspace_id"],
                {"allowed_theme_tokens": ["palette.preset"]},
            )
            changed = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "theme-read-purity-materialize",
                },
                json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
            )
            assert changed.status_code == 200, changed.text
            existing_before = await _theme_state(database, seeded, reviewer_pool)
            existing_read = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert existing_read.status_code == 200
            assert (
                await _theme_state(database, seeded, reviewer_pool) == existing_before
            )

            other_token, other_workspace = await _workspace_capability(
                database, seeded, ["site:read", "theme:read"], "theme-isolation"
            )
            other_read = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {other_token}"},
            )
            assert other_read.status_code == 200, other_read.text
            assert other_read.json()["row_version"] == 1
            assert other_read.json()["palette"] == {"preset": "ocean"}
            assert other_workspace != seeded["workspace_id"]

            await _set_resource_constraints(database, seeded["workspace_id"], {})
            before_quota = await _theme_state(database, seeded, reviewer_pool)
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE control.capability SET mutation_quota=0 "
                    "WHERE workspace_id=$1",
                    seeded["workspace_id"],
                )
            exhausted = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "theme-exhausted-quota",
                },
                json={"expected_row_version": 2, "palette": {"preset": "ember"}},
            )
            assert exhausted.status_code == 429, exhausted.text
            assert await _theme_state(database, seeded, reviewer_pool) == before_quota
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE control.capability SET mutation_quota=250 "
                    "WHERE workspace_id=$1",
                    seeded["workspace_id"],
                )
                await owner.execute(
                    "UPDATE control.workspace SET expires_at=now()-interval '1 second' "
                    "WHERE id=$1",
                    seeded["workspace_id"],
                )
            expired = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert expired.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE control.workspace SET expires_at=now()+interval '1 hour',"
                    "status='ACTIVE' WHERE id=$1",
                    seeded["workspace_id"],
                )
                await owner.execute(
                    "UPDATE control.workspace SET status='FREEZING' WHERE id=$1",
                    seeded["workspace_id"],
                )
            freezing = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert freezing.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE control.workspace SET status='ACTIVE' WHERE id=$1",
                    seeded["workspace_id"],
                )
                await owner.execute(
                    "UPDATE control.site SET status='ARCHIVED' WHERE id=$1",
                    seeded["site_id"],
                )
            archived = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert archived.status_code == 401
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE control.site SET status='ACTIVE' WHERE id=$1",
                    seeded["site_id"],
                )
                await owner.execute(
                    "UPDATE control.capability SET revoked_at=now() "
                    "WHERE workspace_id=$1",
                    seeded["workspace_id"],
                )
            revoked = await client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert revoked.status_code == 401

            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                other_capability_id = await owner.fetchval(
                    "SELECT id FROM control.capability WHERE workspace_id=$1 "
                    "AND revoked_at IS NULL LIMIT 1",
                    other_workspace,
                )
            assert other_capability_id is not None
            async with asyncpg_cow_session(
                agent_pool, session_id=seeded["workspace_id"], operation_id=uuid4()
            ) as cow:
                await cow.native.execute(
                    "SELECT set_config('app.capability_id',$1,true)",
                    str(other_capability_id),
                )
                with pytest.raises(asyncpg.PostgresError, match="AGENT_"):
                    try:
                        await cow.native.fetchrow(
                            "SELECT * FROM content.slaif_agent_theme_get($1)",
                            seeded["site_id"],
                        )
                    except asyncpg.PostgresError:
                        await cow.rollback()
                        raise
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


async def _theme_lock_key(connection: Any, seeded: dict[str, UUID]) -> int:
    return int(
        await connection.fetchval(
            "SELECT hashtextextended($1,995)",
            f"{seeded['workspace_id']}:{seeded['site_id']}:theme",
        )
    )


async def _wait_for_theme_waiters(
    connection: Any, lock_key: int, expected: int
) -> None:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        waiting = await connection.fetchval(
            "SELECT count(*) FROM pg_locks "
            "WHERE locktype='advisory' AND NOT granted "
            "AND classid::bigint=(($1::bigint >> 32) & 4294967295) "
            "AND objid::bigint=($1::bigint & 4294967295)",
            lock_key,
        )
        if waiting >= expected:
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"expected {expected} theme lock waiters")


@asynccontextmanager
async def _hold_theme_lock(
    database: AgentSiteDatabase, seeded: dict[str, UUID]
) -> AsyncIterator[Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await owner.fetchval(
                "SELECT pg_advisory_xact_lock(hashtextextended($1,995))",
                f"{seeded['workspace_id']}:{seeded['site_id']}:theme",
            )
            yield owner


@pytest.mark.asyncio
async def test_theme_races_use_database_barrier_and_cancel_without_residue(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token_a = await _capability_with_scopes(
        database, seeded, ["site:read", "theme:read", "theme-tokens:write"]
    )
    token_b = await _capability_with_scopes(
        database, seeded, ["site:read", "theme:read", "theme-tokens:write"]
    )
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        async with _agent_client(database) as client:
            async with _hold_theme_lock(database, seeded) as blocker:
                task_a = asyncio.create_task(
                    client.patch(
                        "/api/agent/v1/theme",
                        headers={
                            "Authorization": f"Bearer {token_a}",
                            "Idempotency-Key": "theme-barrier-first-a",
                        },
                        json={
                            "expected_row_version": 1,
                            "palette": {"preset": "meadow"},
                        },
                    )
                )
                task_b = asyncio.create_task(
                    client.patch(
                        "/api/agent/v1/theme",
                        headers={
                            "Authorization": f"Bearer {token_b}",
                            "Idempotency-Key": "theme-barrier-first-b",
                        },
                        json={
                            "expected_row_version": 1,
                            "palette": {"preset": "ember"},
                        },
                    )
                )
                await _wait_for_theme_waiters(
                    blocker, await _theme_lock_key(blocker, seeded), 2
                )
            responses = await asyncio.gather(task_a, task_b)
            assert sorted(response.status_code for response in responses) == [200, 409]
            first_state = await _theme_state(database, seeded, reviewer_pool)
            assert first_state[0][0] == 0
            assert first_state[2][0] == 1
            assert first_state[2][1] == 1
            assert first_state[2][2] == 1
            assert first_state[4] == 1

            async with _hold_theme_lock(database, seeded) as blocker:
                existing_a = asyncio.create_task(
                    client.patch(
                        "/api/agent/v1/theme",
                        headers={
                            "Authorization": f"Bearer {token_a}",
                            "Idempotency-Key": "theme-barrier-existing-a",
                        },
                        json={
                            "expected_row_version": 2,
                            "palette": {"preset": "ocean"},
                        },
                    )
                )
                existing_b = asyncio.create_task(
                    client.patch(
                        "/api/agent/v1/theme",
                        headers={
                            "Authorization": f"Bearer {token_b}",
                            "Idempotency-Key": "theme-barrier-existing-b",
                        },
                        json={
                            "expected_row_version": 2,
                            "palette": {"preset": "ember"},
                        },
                    )
                )
                await _wait_for_theme_waiters(
                    blocker, await _theme_lock_key(blocker, seeded), 2
                )
            existing_responses = await asyncio.gather(existing_a, existing_b)
            assert sorted(response.status_code for response in existing_responses) == [
                200,
                409,
            ]
            existing_state = await _theme_state(database, seeded, reviewer_pool)
            assert existing_state[2][0] == 2
            assert existing_state[2][1] == 2
            assert existing_state[2][2] == 2
            assert existing_state[4] == 2

            before_cancel = await _theme_state(database, seeded, reviewer_pool)
            async with _hold_theme_lock(database, seeded) as blocker:
                cancellation = asyncio.create_task(
                    client.patch(
                        "/api/agent/v1/theme",
                        headers={
                            "Authorization": f"Bearer {token_a}",
                            "Idempotency-Key": "theme-barrier-cancelled",
                        },
                        json={
                            "expected_row_version": 3,
                            "palette": {"preset": "ocean"},
                        },
                    )
                )
                await _wait_for_theme_waiters(
                    blocker, await _theme_lock_key(blocker, seeded), 1
                )
                cancellation.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await cancellation
            assert await _theme_state(database, seeded, reviewer_pool) == before_cancel

        async with _agent_client(database) as restarted_client:
            restarted = await restarted_client.get(
                "/api/agent/v1/theme",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            assert restarted.status_code == 200
            assert restarted.json()["row_version"] == 3
    finally:
        await reviewer_pool.close()

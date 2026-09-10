"""Focused PostgreSQL proof for page-style/v1 inheritance and authority."""

from __future__ import annotations

import asyncio
import json
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
from slaif_agent_site.bootstrap.service import reconcile
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from sqlalchemy.exc import DBAPIError
from test_agent_mutations import (
    _agent_settings,
    _capability_with_scopes,
    _disable_content_cow,
    _hold_agent_structure_lock,
    _seed,
    _set_resource_constraints,
    _wait_for_page_structure_waiters,
    _workspace_capability,
    asyncpg_cow_session,
)


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


async def _wait_for_advisory_waiters(connection: Any, lock_key: int) -> None:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        waiting = await connection.fetchval(
            "SELECT count(*) FROM pg_locks WHERE locktype='advisory' "
            "AND NOT granted "
            "AND classid::bigint=(($1::bigint >> 32) & 4294967295) "
            "AND objid::bigint=($1::bigint & 4294967295)",
            lock_key,
        )
        if waiting:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("expected advisory lock waiter")


@asynccontextmanager
async def _hold_workspace_lifecycle_lock(
    database: AgentSiteDatabase, workspace_id: UUID
) -> AsyncIterator[Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await owner.fetchval(
                "SELECT pg_advisory_xact_lock(hashtextextended($1,280))",
                str(workspace_id),
            )
            yield owner


@asynccontextmanager
async def _hold_theme_lock(
    database: AgentSiteDatabase, workspace_id: UUID, site_id: UUID
) -> AsyncIterator[Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await owner.fetchval(
                "SELECT pg_advisory_xact_lock(hashtextextended($1,995))",
                f"{workspace_id}:{site_id}:theme",
            )
            yield owner


@pytest.mark.asyncio
async def test_page_style_is_typed_inherited_resettable_and_scope_bound(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        [
            "site:read",
            "page:create",
            "page:read",
            "page-style:write",
            "theme:read",
            "theme-tokens:write",
        ],
    )
    read_token = await _capability_with_scopes(
        database, seeded, ["site:read", "page:read"]
    )
    await _set_resource_constraints(
        database,
        seeded["workspace_id"],
        {
            "allowed_theme_palette_presets": ["ocean", "meadow", "ember"],
            "allowed_theme_typography_families": ["system", "serif"],
            "allowed_theme_tokens": [
                "palette.preset",
                "typography.family",
                "typography.scale",
                "typography.weight",
                "layout.content_width",
                "layout.spacing",
                "layout.grid_gap",
                "shape.radius",
                "shape.shadow",
            ],
        },
    )
    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-page-create",
            },
            json={"slug": "styled", "title": "Styled", "locale": "en-US"},
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])

        initial = await client.get(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert initial.status_code == 200, initial.text
        assert initial.json()["overrides"] == {}
        assert initial.json()["resolved"]["palette"]["preset"] == "ocean"
        assert initial.json()["row_version"] == 1

        equal_inherited = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-explicit-inherited-value",
            },
            json={
                "expected_row_version": 1,
                "typography": {"family": "system"},
            },
        )
        assert equal_inherited.status_code == 200, equal_inherited.text
        assert equal_inherited.json()["record"]["row_version"] == 2
        assert equal_inherited.json()["record"]["overrides"] == {
            "typography": {"family": "system"}
        }

        changed_body = {
            "expected_row_version": 2,
            "palette": {"preset": "meadow"},
            "typography": {
                "family": "serif",
                "scale": "spacious",
                "weight": "bold",
            },
            "layout": {
                "content_width": "xl",
                "spacing": "lg",
                "grid_gap": "sm",
            },
            "shape": {"radius": "lg", "shadow": "md"},
            "reset_tokens": [],
        }
        changed = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-all-groups",
            },
            json=changed_body,
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["action"] == "PAGE_STYLE_UPDATED"
        assert changed.json()["record"]["row_version"] == 3
        assert changed.json()["record"]["overrides"]["layout"] == {
            "content_width": "xl",
            "grid_gap": "sm",
            "spacing": "lg",
        }

        replay = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-all-groups",
            },
            json=changed_body,
        )
        assert replay.status_code == 200
        assert replay.content == changed.content

        mismatch = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-all-groups",
            },
            json={**changed_body, "palette": {"preset": "ember"}},
        )
        assert mismatch.status_code == 409, mismatch.text

        stale = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-stale-version",
            },
            json={
                "expected_row_version": 2,
                "palette": {"preset": "ember"},
            },
        )
        assert stale.status_code == 409, stale.text

        read_no_effect = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-read-no-effect",
            },
            json={
                "expected_row_version": 3,
                "palette": {"preset": "meadow"},
            },
        )
        assert read_no_effect.status_code == 200, read_no_effect.text
        assert read_no_effect.json()["action"] is None
        assert read_no_effect.json()["record"]["row_version"] == 3

        denied = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-read-change",
            },
            json={
                "expected_row_version": 3,
                "palette": {"preset": "ember"},
            },
        )
        assert denied.status_code == 403, denied.text

        reset = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-reset-palette",
            },
            json={
                "expected_row_version": 3,
                "reset_tokens": ["palette.preset"],
            },
        )
        assert reset.status_code == 200, reset.text
        assert reset.json()["record"]["row_version"] == 4
        assert "palette" not in reset.json()["record"]["overrides"]
        assert reset.json()["record"]["resolved"]["palette"]["preset"] == "ocean"

        theme_token = await _capability_with_scopes(
            database,
            seeded,
            ["site:read", "page:read", "theme:read", "theme-tokens:write"],
        )
        theme = await client.patch(
            "/api/agent/v1/theme",
            headers={
                "Authorization": f"Bearer {theme_token}",
                "Idempotency-Key": "page-style-site-theme",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ember"}},
        )
        assert theme.status_code == 200, theme.text
        follows_theme = await client.get(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert follows_theme.json()["resolved"]["palette"]["preset"] == "ember"
        assert follows_theme.json()["resolved"]["typography"]["family"] == "serif"

        invalid = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-invalid-overlap",
            },
            json={
                "expected_row_version": 4,
                "palette": {"preset": "meadow"},
                "reset_tokens": ["palette.preset"],
            },
        )
        assert invalid.status_code == 422, invalid.text

        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool,
                session_id=seeded["workspace_id"],
                operation_id=uuid4(),
            ) as cow:
                with pytest.raises(asyncpg.PostgresError, match="PAGE_STYLE_"):
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_page_style_update("
                        "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                        seeded["site_id"],
                        page_id,
                        4,
                        '{"preset":null}',
                        None,
                        None,
                        None,
                        [],
                    )
                await cow.rollback()
        finally:
            await agent_pool.close()

        foreign = await client.get(
            f"/api/agent/v1/pages/{seeded['page_b_id']}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert foreign.status_code == 404, foreign.text

        final = await client.get(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert final.status_code == 200
        assert final.json()["row_version"] == 4
        assert final.json()["overrides"]["typography"] == {
            "family": "serif",
            "scale": "spacious",
            "weight": "bold",
        }


@pytest.mark.asyncio
async def test_page_style_visibility_version_and_mixed_reset_authority(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:create", "page:read", "page-style:write"],
    )
    auth = {"Authorization": f"Bearer {token}"}
    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={**auth, "Idempotency-Key": "page-style-authority-create"},
            json={"slug": "outside", "title": "Outside", "locale": "en-US"},
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])
        path = f"/api/agent/v1/pages/{page_id}/style"

        await _set_resource_constraints(
            database, seeded["workspace_id"], {"route_prefix": "/allowed"}
        )
        assert (await client.get(path, headers=auth)).status_code == 404
        assert (
            await client.patch(
                path,
                headers={**auth, "Idempotency-Key": "page-style-resource-http"},
                json={
                    "expected_row_version": 1,
                    "palette": {"preset": "meadow"},
                },
            )
        ).status_code == 404

        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool,
                session_id=seeded["workspace_id"],
                operation_id=uuid4(),
            ) as cow:
                with pytest.raises(asyncpg.PostgresError, match="PAGE_NOT_FOUND"):
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_page_style_update("
                        "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                        seeded["site_id"],
                        page_id,
                        1,
                        '{"preset":"meadow"}',
                        None,
                        None,
                        None,
                        [],
                    )
                await cow.rollback()
            async with asyncpg_cow_session(
                agent_pool,
                session_id=seeded["workspace_id"],
                operation_id=uuid4(),
            ) as cow:
                with pytest.raises(asyncpg.PostgresError, match="ROW_VERSION_REQUIRED"):
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_page_style_update("
                        "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                        seeded["site_id"],
                        page_id,
                        None,
                        '{"preset":"meadow"}',
                        None,
                        None,
                        None,
                        [],
                    )
                await cow.rollback()
        finally:
            await agent_pool.close()

        await _set_resource_constraints(database, seeded["workspace_id"], {})
        initial_style = await client.get(path, headers=auth)
        assert initial_style.status_code == 200
        assert initial_style.json()["row_version"] == 1

        first = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-mixed-first"},
            json={
                "expected_row_version": 1,
                "typography": {"family": "serif", "weight": "bold"},
            },
        )
        assert first.status_code == 200, first.text
        assert first.json()["record"]["row_version"] == 2

        mixed = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-mixed-reset"},
            json={
                "expected_row_version": 2,
                "typography": {"weight": "medium"},
                "reset_tokens": ["typography.family"],
            },
        )
        assert mixed.status_code == 200, mixed.text
        assert mixed.json()["record"]["row_version"] == 3
        assert mixed.json()["record"]["overrides"] == {
            "typography": {"weight": "medium"}
        }
        assert mixed.json()["record"]["resolved"]["typography"]["family"] == "system"

        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool,
                session_id=seeded["workspace_id"],
                operation_id=uuid4(),
            ) as cow:
                direct = await cow.native.fetchrow(
                    "SELECT * FROM content.slaif_agent_page_style_update("
                    "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                    seeded["site_id"],
                    page_id,
                    3,
                    None,
                    '{"scale":"spacious"}',
                    None,
                    None,
                    ["typography.weight"],
                )
                assert direct is not None
                assert direct[4] == 4
                assert json.loads(direct[5]) == {"typography": {"scale": "spacious"}}
                await cow.rollback()
        finally:
            await agent_pool.close()

        after_direct_rollback = await client.get(path, headers=auth)
        assert after_direct_rollback.status_code == 200
        assert after_direct_rollback.json()["row_version"] == 3
        assert after_direct_rollback.json()["overrides"] == {
            "typography": {"weight": "medium"}
        }

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert not await owner.fetchval(
            "SELECT has_function_privilege('slaif_agent_runtime',$1,'EXECUTE')",
            "content.slaif_page_style_apply(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[],boolean)",
        )
        assert await owner.fetchval(
            "SELECT has_function_privilege('slaif_agent_runtime',$1,'EXECUTE')",
            "content.slaif_agent_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
        )


@pytest.mark.asyncio
async def test_page_style_066_round_trip_preserves_legacy_data_and_blocks_loss(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    legacy_page_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.page_base "
            "(id,site_id,slug,title,status,locale) "
            "VALUES ($1,$2,'legacy-round-trip','Legacy round trip','DRAFT','en-US')",
            legacy_page_id,
            seeded["site_id"],
        )
        before = tuple(
            await owner.fetchrow(
                "SELECT slug,title,status,locale,row_version FROM content.page_base "
                "WHERE id=$1",
                legacy_page_id,
            )
        )

    await _disable_content_cow(database)
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="065_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT version_num::text FROM control.alembic_version"
            )
            == "065_001"
        )
        assert (
            tuple(
                await owner.fetchrow(
                    "SELECT slug,title,status,locale,row_version FROM content.page "
                    "WHERE id=$1",
                    legacy_page_id,
                )
            )
            == before
        )

    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT version_num::text FROM control.alembic_version"
            )
            == "066_001"
        )
        round_trip = await owner.fetchrow(
            "SELECT slug,title,status,locale,row_version,style_overrides::text "
            "FROM content.page_base WHERE id=$1",
            legacy_page_id,
        )
        assert round_trip is not None
        assert tuple(round_trip[:5]) == before
        assert json.loads(round_trip[5]) == {}
        for signature, expected_volatility in (
            ("content.slaif_page_style_resolved(uuid,jsonb)", "s"),
            ("content.slaif_page_style_project(uuid)", "s"),
            ("content.slaif_page_style_get(uuid,uuid)", "s"),
            (
                "content.slaif_agent_page_style_get(uuid,uuid)",
                "s",
            ),
            (
                "content.slaif_page_style_apply(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[],boolean)",
                "v",
            ),
            (
                "content.slaif_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
                "v",
            ),
            (
                "content.slaif_agent_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
                "v",
            ),
        ):
            contract = await owner.fetchrow(
                "SELECT pg_get_userbyid(proowner),provolatile,proconfig "
                "FROM pg_proc WHERE oid=$1::regprocedure",
                signature,
            )
            assert contract is not None
            assert contract[0] == "slaif_owner"
            actual_volatility = (
                contract[1].decode() if isinstance(contract[1], bytes) else contract[1]
            )
            assert actual_volatility == expected_volatility
            assert "search_path=pg_catalog" in (contract[2] or [])
            assert not await owner.fetchval(
                "SELECT has_function_privilege('public',$1,'EXECUTE')", signature
            )
        assert await owner.fetchval(
            "SELECT has_function_privilege('slaif_editor_runtime',$1,'EXECUTE')",
            "content.slaif_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
        )
        assert await owner.fetchval(
            "SELECT has_function_privilege('slaif_agent_runtime',$1,'EXECUTE')",
            "content.slaif_agent_page_style_update(uuid,uuid,integer,jsonb,jsonb,jsonb,jsonb,text[])",
        )
        constraint = await owner.fetchval(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid='audit.agent_mutation'::regclass "
            "AND conname='agent_mutation_semantic_shape'"
        )
        assert constraint is not None
        assert "PAGE_STYLE_UPDATED" in constraint

    token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:read", "page-style:write"],
    )
    async with _agent_client(database) as client:
        changed = await client.patch(
            f"/api/agent/v1/pages/{legacy_page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-migration-data",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ember"}},
        )
        assert changed.status_code == 200, changed.text

    with pytest.raises(DBAPIError, match="PAGE_STYLE_MIGRATION_PENDING_COW"):
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="065_001",
        )

    await _disable_content_cow(database)
    with pytest.raises(DBAPIError, match="PAGE_STYLE_MIGRATION_DATA_PRESENT"):
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="065_001",
        )


@pytest.mark.asyncio
async def test_page_style_accounting_constraints_lifecycle_restart_and_restore(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    full_token = await _capability_with_scopes(
        database,
        seeded,
        [
            "site:read",
            "page:create",
            "page:read",
            "page:write",
            "page:delete",
            "page:restore",
            "page-style:write",
        ],
    )
    read_token = await _capability_with_scopes(
        database, seeded, ["site:read", "page:read"]
    )
    limited_token = await _capability_with_scopes(
        database, seeded, ["site:read", "page:read", "theme-tokens:write"]
    )
    other_token, other_workspace = await _workspace_capability(
        database,
        seeded,
        ["site:read", "page:read", "page-style:write"],
        "page-style-isolation",
    )
    auth = {"Authorization": f"Bearer {full_token}"}

    async def accounting() -> tuple[int, int, int]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT coalesce(sum(mutation_used),0), "
                "(SELECT count(*) FROM control.agent_idempotency "
                "WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                "WHERE workspace_id=$1 AND action='PAGE_STYLE_UPDATED') "
                "FROM control.capability WHERE workspace_id=$1",
                seeded["workspace_id"],
            )
            assert row is not None
            return tuple(row)

    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={**auth, "Idempotency-Key": "page-style-accounting-create"},
            json={
                "slug": "style-accounting",
                "title": "Style accounting",
                "locale": "en-US",
            },
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])
        path = f"/api/agent/v1/pages/{page_id}/style"
        initial = await client.get(path, headers=auth)
        assert initial.status_code == 200
        assert initial.json()["row_version"] == 1

        before_no_effect = await accounting()
        no_effect = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-accounting-reset-inherit",
            },
            json={"expected_row_version": 1, "reset_tokens": ["palette.preset"]},
        )
        assert no_effect.status_code == 200, no_effect.text
        assert no_effect.json()["action"] is None
        assert no_effect.json()["record"]["row_version"] == 1
        after_no_effect = await accounting()
        assert after_no_effect[0] == before_no_effect[0]
        assert after_no_effect[1] == before_no_effect[1] + 1
        assert after_no_effect[2] == before_no_effect[2]

        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {
                "allowed_theme_tokens": ["palette.preset"],
                "allowed_theme_palette_presets": ["ember"],
            },
        )
        changed = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-accounting-ember"},
            json={"expected_row_version": 1, "palette": {"preset": "ember"}},
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["record"]["row_version"] == 2
        after_change = await accounting()
        assert after_change[0] == before_no_effect[0] + 1
        assert after_change[1] == after_no_effect[1] + 1
        assert after_change[2] == before_no_effect[2] + 1

        read_no_effect = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-accounting-read-replay",
            },
            json={"expected_row_version": 2, "palette": {"preset": "ember"}},
        )
        assert read_no_effect.status_code == 200, read_no_effect.text
        assert read_no_effect.json()["action"] is None
        assert read_no_effect.json()["record"]["overrides"] == {
            "palette": {"preset": "ember"}
        }
        after_read_no_effect = await accounting()
        assert after_read_no_effect[0] == after_change[0]
        assert after_read_no_effect[1] == after_change[1] + 1
        assert after_read_no_effect[2] == after_change[2]

        await _set_resource_constraints(database, seeded["workspace_id"], {})
        denied_token = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {limited_token}",
                "Idempotency-Key": "page-style-accounting-unrelated-scope",
            },
            json={"expected_row_version": 2, "palette": {"preset": "ocean"}},
        )
        assert denied_token.status_code == 403, denied_token.text
        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {
                "allowed_theme_tokens": ["palette.preset"],
                "allowed_theme_palette_presets": ["ember"],
            },
        )
        before_failed = await accounting()
        denied_constraint = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-accounting-denied-token"},
            json={"expected_row_version": 2, "palette": {"preset": "ocean"}},
        )
        assert denied_constraint.status_code == 403, denied_constraint.text
        assert await accounting() == before_failed

        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {
                "allowed_theme_tokens": ["palette.preset"],
                "allowed_theme_palette_presets": ["ocean"],
            },
        )
        reset = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-accounting-reset"},
            json={"expected_row_version": 2, "reset_tokens": ["palette.preset"]},
        )
        assert reset.status_code == 200, reset.text
        assert reset.json()["record"]["row_version"] == 3
        assert reset.json()["record"]["overrides"] == {}

        await _set_resource_constraints(database, seeded["workspace_id"], {})
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET mutation_quota=0 WHERE workspace_id=$1",
                seeded["workspace_id"],
            )
        before_quota = await accounting()
        exhausted = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-accounting-quota"},
            json={"expected_row_version": 3, "palette": {"preset": "ember"}},
        )
        assert exhausted.status_code == 429, exhausted.text
        assert await accounting() == before_quota
        assert (await client.get(path, headers=auth)).json()["overrides"] == {}

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET mutation_quota=250,delete_quota=50 "
                "WHERE workspace_id=$1",
                seeded["workspace_id"],
            )
            await owner.execute(
                "UPDATE control.workspace SET expires_at=now()-interval '1 second' "
                "WHERE id=$1",
                seeded["workspace_id"],
            )
        assert (await client.get(path, headers=auth)).status_code == 401
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET expires_at=now()+interval '1 hour',"
                "status='FREEZING' WHERE id=$1",
                seeded["workspace_id"],
            )
        assert (await client.get(path, headers=auth)).status_code == 401
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
        assert (await client.get(path, headers=auth)).status_code == 401
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.site SET status='ACTIVE' WHERE id=$1",
                seeded["site_id"],
            )

        await _set_resource_constraints(database, seeded["workspace_id"], {})
        restorable = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-accounting-preserve"},
            json={"expected_row_version": 3, "palette": {"preset": "ember"}},
        )
        assert restorable.status_code == 200, restorable.text
        assert restorable.json()["record"]["row_version"] == 4
        async with _agent_client(database) as restarted_client:
            restarted_style = await restarted_client.get(path, headers=auth)
            assert restarted_style.status_code == 200, restarted_style.text
            assert restarted_style.json()["overrides"] == {
                "palette": {"preset": "ember"}
            }
        deleted = await client.request(
            "DELETE",
            f"/api/agent/v1/pages/{page_id}",
            headers={
                **auth,
                "Idempotency-Key": "page-style-accounting-delete",
            },
            json={"expected_row_version": 4},
        )
        assert deleted.status_code == 200, deleted.text
        assert (await client.get(path, headers=auth)).status_code == 404
        restored = await client.post(
            f"/api/agent/v1/pages/{page_id}:restore",
            headers={
                **auth,
                "Idempotency-Key": "page-style-accounting-restore",
            },
            json={"expected_row_version": 5},
        )
        assert restored.status_code == 200, restored.text
        preserved = await client.get(path, headers=auth)
        assert preserved.status_code == 200, preserved.text
        assert preserved.json()["overrides"] == {"palette": {"preset": "ember"}}

        other_style = await client.get(
            path, headers={"Authorization": f"Bearer {other_token}"}
        )
        assert other_style.status_code == 404, other_style.text
        assert other_workspace != seeded["workspace_id"]
        assert (
            await client.get(
                f"/api/agent/v1/pages/{seeded['page_b_id']}/style", headers=auth
            )
        ).status_code == 404
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET revoked_at=now() WHERE public_id=$1",
                limited_token.split("_", maxsplit=2)[1],
            )
        assert (
            await client.get(path, headers={"Authorization": f"Bearer {limited_token}"})
        ).status_code == 401

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert not await owner.fetchval(
            "SELECT EXISTS (SELECT 1 FROM content.page_base WHERE id=$1)", page_id
        )


@pytest.mark.asyncio
async def test_page_style_structural_races_serialize_with_page_operations(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token_a = await _capability_with_scopes(
        database,
        seeded,
        [
            "site:read",
            "page:create",
            "page:read",
            "page:write",
            "page:move",
            "route:write",
            "page:delete",
            "page-style:write",
        ],
    )
    token_b = await _capability_with_scopes(
        database,
        seeded,
        [
            "site:read",
            "page:create",
            "page:read",
            "page:write",
            "page:move",
            "route:write",
            "page:delete",
            "page-style:write",
        ],
    )

    async with _agent_client(database) as client:

        async def create_page(slug: str, key: str) -> UUID:
            response = await client.post(
                "/api/agent/v1/pages",
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"slug": slug, "title": slug, "locale": "en-US"},
            )
            assert response.status_code == 201, response.text
            return UUID(response.json()["record"]["id"])

        async def race(
            first: Any,
            second: Any,
            first_key: str,
            second_key: str,
            loser_status: int | tuple[int, ...] = 409,
        ) -> tuple[httpx.Response, httpx.Response]:
            async with _hold_agent_structure_lock(
                database, seeded["workspace_id"], seeded["site_id"]
            ) as blocker:
                first_task = asyncio.create_task(first(first_key))
                await _wait_for_page_structure_waiters(blocker, 1)
                second_task = asyncio.create_task(second(second_key))
                await _wait_for_page_structure_waiters(blocker, 2)
            first_response, second_response = await asyncio.gather(
                first_task, second_task
            )
            statuses = sorted((first_response.status_code, second_response.status_code))
            loser_statuses = (
                (loser_status,) if isinstance(loser_status, int) else loser_status
            )
            assert statuses in ([200, status] for status in loser_statuses), (
                first_response.text,
                second_response.text,
            )
            return first_response, second_response

        style_page = await create_page("style-race", "page-style-race-create")
        style_path = f"/api/agent/v1/pages/{style_page}/style"

        async def style_first(key: str) -> httpx.Response:
            return await client.patch(
                style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
            )

        async def style_second(key: str) -> httpx.Response:
            return await client.patch(
                style_path,
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={
                    "expected_row_version": 1,
                    "typography": {"family": "serif"},
                },
            )

        first_style, second_style = await race(
            style_first,
            style_second,
            "page-style-race-a",
            "page-style-race-b",
        )
        final_style = await client.get(
            style_path, headers={"Authorization": f"Bearer {token_a}"}
        )
        assert final_style.status_code == 200
        assert final_style.json()["row_version"] == 2
        assert final_style.json()["overrides"] in (
            {"palette": {"preset": "meadow"}},
            {"typography": {"family": "serif"}},
        )
        assert (first_style.status_code, second_style.status_code).count(200) == 1

        update_page = await create_page("style-update-race", "page-style-update-create")
        update_path = f"/api/agent/v1/pages/{update_page}"
        update_style_path = f"{update_path}/style"

        async def style_again(key: str) -> httpx.Response:
            return await client.patch(
                update_style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "layout": {"spacing": "lg"}},
            )

        async def page_update(key: str) -> httpx.Response:
            return await client.patch(
                update_path,
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "title": "Updated"},
            )

        await race(style_again, page_update, "page-style-v-page", "page-update-v-style")
        assert (
            await client.get(
                update_path, headers={"Authorization": f"Bearer {token_a}"}
            )
        ).status_code == 200

        parent_page = await create_page("style-move-parent", "page-style-move-parent")
        move_page = await create_page("style-move-race", "page-style-move-create")
        move_path = f"/api/agent/v1/pages/{move_page}"
        move_style_path = f"{move_path}/style"

        async def style_before_move(key: str) -> httpx.Response:
            return await client.patch(
                move_style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "shape": {"radius": "lg"}},
            )

        async def page_move(key: str) -> httpx.Response:
            return await client.post(
                f"{move_path}:move",
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "parent_id": str(parent_page)},
            )

        await race(
            style_before_move, page_move, "page-style-v-move", "page-move-v-style"
        )

        delete_page = await create_page("style-delete-race", "page-style-delete-create")
        delete_path = f"/api/agent/v1/pages/{delete_page}"
        delete_style_path = f"{delete_path}/style"

        async def style_before_delete(key: str) -> httpx.Response:
            return await client.patch(
                delete_style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "shape": {"shadow": "lg"}},
            )

        async def page_delete(key: str) -> httpx.Response:
            return await client.request(
                "DELETE",
                delete_path,
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1},
            )

        await race(
            style_before_delete,
            page_delete,
            "page-style-v-delete",
            "page-delete-v-style",
            loser_status=(404, 409),
        )


@pytest.mark.asyncio
async def test_page_style_waits_on_lifecycle_and_theme_barriers(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:create", "page:read", "page-style:write"],
    )
    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-lock-create",
            },
            json={"slug": "style-locks", "title": "Style locks", "locale": "en-US"},
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])
        path = f"/api/agent/v1/pages/{page_id}/style"

        async with _hold_workspace_lifecycle_lock(
            database, seeded["workspace_id"]
        ) as blocker:
            lifecycle_lock = await blocker.fetchval(
                "SELECT hashtextextended($1,280)", str(seeded["workspace_id"])
            )
            task = asyncio.create_task(
                client.patch(
                    path,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "page-style-lifecycle-wait",
                    },
                    json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
                )
            )
            await _wait_for_advisory_waiters(blocker, lifecycle_lock)
        lifecycle_response = await task
        assert lifecycle_response.status_code == 200, lifecycle_response.text

        async with _hold_theme_lock(
            database, seeded["workspace_id"], seeded["site_id"]
        ) as blocker:
            theme_lock = await blocker.fetchval(
                "SELECT hashtextextended($1,995)",
                f"{seeded['workspace_id']}:{seeded['site_id']}:theme",
            )
            task = asyncio.create_task(
                client.patch(
                    path,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "page-style-theme-wait",
                    },
                    json={
                        "expected_row_version": 2,
                        "typography": {"scale": "spacious"},
                    },
                )
            )
            await _wait_for_advisory_waiters(blocker, theme_lock)
        theme_response = await task
        assert theme_response.status_code == 200, theme_response.text
        assert (
            theme_response.json()["record"]["resolved"]["typography"]["scale"]
            == "spacious"
        )

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
from slaif_agent_site.agent_state.foundation import asyncpg_cow_reviewer
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


async def _wait_for_advisory_waiters(
    connection: Any, lock_key: int, expected: int = 1
) -> None:
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        waiting = await connection.fetchval(
            "SELECT count(DISTINCT pid) FROM pg_locks WHERE locktype='advisory' "
            "AND NOT granted "
            "AND classid::bigint=(($1::bigint >> 32) & 4294967295) "
            "AND objid::bigint=($1::bigint & 4294967295)",
            lock_key,
        )
        if waiting >= expected:
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"expected {expected} distinct advisory lock waiters")


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
            for invalid_reset in (
                [None],
                ["palette.unknown"],
                ["palette.preset", "palette.preset"],
            ):
                async with asyncpg_cow_session(
                    agent_pool,
                    session_id=seeded["workspace_id"],
                    operation_id=uuid4(),
                ) as cow:
                    with pytest.raises(
                        asyncpg.PostgresError, match="PAGE_STYLE_RESET_INVALID"
                    ):
                        await cow.native.fetchrow(
                            "SELECT * FROM content.slaif_agent_page_style_update("
                            "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                            seeded["site_id"],
                            page_id,
                            4,
                            None,
                            None,
                            None,
                            None,
                            invalid_reset,
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
                with pytest.raises(asyncpg.PostgresError, match="PAGE_NOT_FOUND"):
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_page_style_update("
                        "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                        seeded["site_id"],
                        page_id,
                        1,
                        None,
                        None,
                        None,
                        None,
                        ["palette.preset"],
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
        root_response = await client.post(
            "/api/agent/v1/pages",
            headers={
                **auth,
                "Idempotency-Key": "page-style-resource-root",
            },
            json={"slug": "style-root", "title": "Style root", "locale": "en-US"},
        )
        assert root_response.status_code == 201, root_response.text
        root_id = UUID(root_response.json()["record"]["id"])
        child_response = await client.post(
            "/api/agent/v1/pages",
            headers={
                **auth,
                "Idempotency-Key": "page-style-resource-child",
            },
            json={
                "slug": "style-child",
                "title": "Style child",
                "locale": "en-US",
                "parent_id": str(root_id),
            },
        )
        assert child_response.status_code == 201, child_response.text
        child_id = UUID(child_response.json()["record"]["id"])
        grandchild_response = await client.post(
            "/api/agent/v1/pages",
            headers={
                **auth,
                "Idempotency-Key": "page-style-resource-grandchild",
            },
            json={
                "slug": "style-grandchild",
                "title": "Style grandchild",
                "locale": "en-US",
                "parent_id": str(child_id),
            },
        )
        assert grandchild_response.status_code == 201, grandchild_response.text
        grandchild_id = UUID(grandchild_response.json()["record"]["id"])
        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {
                "allowed_page_root_ids": [str(root_id)],
                "max_page_depth": 2,
            },
        )
        assert (
            await client.get(f"/api/agent/v1/pages/{child_id}/style", headers=auth)
        ).status_code == 200
        assert (
            await client.get(f"/api/agent/v1/pages/{grandchild_id}/style", headers=auth)
        ).status_code == 404
        assert (await client.get(path, headers=auth)).status_code == 404
        await _set_resource_constraints(
            database, seeded["workspace_id"], {"allowed_locales": ["en"]}
        )
        assert (await client.get(path, headers=auth)).status_code == 404
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
async def test_page_style_fresh_065_baseline_restores_exactly_through_066(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    site_id = uuid4()
    page_id = uuid4()

    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="065_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.site "
            "(id,site_key,display_name,default_locale,component_catalog_version) "
            "VALUES ($1,'fresh-style','Fresh style','en-US','catalog-v1')",
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.page "
            "(id,site_id,slug,title,status,locale) "
            "VALUES ($1,$2,'fresh-page','Fresh page','DRAFT','en-US')",
            page_id,
            site_id,
        )

        async def snapshot() -> tuple[tuple[tuple[Any, ...], ...], str]:
            rows = await owner.fetch(
                "SELECT proname,pg_get_functiondef(oid),"
                "pg_get_userbyid(proowner),proacl::text,provolatile,proconfig "
                "FROM pg_proc WHERE pronamespace='control'::regnamespace "
                "AND proname IN ('slaif_agent_idempotency_complete',"
                "'slaif_agent_idempotency_complete_no_effect') "
                "ORDER BY proname"
            )
            constraint = await owner.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid='audit.agent_mutation'::regclass "
                "AND conname='agent_mutation_semantic_shape'"
            )
            assert constraint is not None
            return tuple(tuple(row) for row in rows), constraint

        baseline = await snapshot()

    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="066_001",
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
        restored = await owner.fetch(
            "SELECT proname,pg_get_functiondef(oid),"
            "pg_get_userbyid(proowner),proacl::text,provolatile,proconfig "
            "FROM pg_proc WHERE pronamespace='control'::regnamespace "
            "AND proname IN ('slaif_agent_idempotency_complete',"
            "'slaif_agent_idempotency_complete_no_effect') "
            "ORDER BY proname"
        )
        constraint = await owner.fetchval(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conrelid='audit.agent_mutation'::regclass "
            "AND conname='agent_mutation_semantic_shape'"
        )
        assert tuple(tuple(row) for row in restored) == baseline[0]
        assert constraint == baseline[1]
        assert tuple(
            await owner.fetchrow(
                "SELECT slug,title,status,locale,row_version FROM content.page "
                "WHERE id=$1",
                page_id,
            )
        ) == ("fresh-page", "Fresh page", "DRAFT", "en-US", 1)

    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="066_001",
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
            page_id,
        )
        assert round_trip is not None
        assert tuple(round_trip[:5]) == (
            "fresh-page",
            "Fresh page",
            "DRAFT",
            "en-US",
            1,
        )
        assert json.loads(round_trip[5]) == {}


@pytest.mark.asyncio
async def test_page_style_downgrade_rejects_style_audit_without_data_loss(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:read", "page-style:write"],
    )
    page_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.page_base "
            "(id,site_id,slug,title,status,locale) "
            "VALUES ($1,$2,'audit-only','Audit only','DRAFT','en-US')",
            page_id,
            seeded["site_id"],
        )
    async with _agent_client(database) as client:
        path = f"/api/agent/v1/pages/{page_id}/style"
        changed = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-audit-only-change",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ember"}},
        )
        assert changed.status_code == 200, changed.text
        reset = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-audit-only-reset",
            },
            json={"expected_row_version": 2, "reset_tokens": ["palette.preset"]},
        )
        assert reset.status_code == 200, reset.text
        assert reset.json()["record"]["overrides"] == {}

    await _disable_content_cow(database)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT style_overrides::text FROM content.page WHERE id=$1", page_id
            )
            == "{}"
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM audit.agent_mutation "
                "WHERE action='PAGE_STYLE_UPDATED' AND workspace_id=$1",
                seeded["workspace_id"],
            )
            == 2
        )
    with pytest.raises(DBAPIError, match="PAGE_STYLE_MIGRATION_AUDIT_PRESENT"):
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
            == "066_001"
        )
        assert (
            await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "content.slaif_agent_page_style_get(uuid,uuid)",
            )
            is not None
        )


@pytest.mark.asyncio
async def test_page_style_cancellation_after_dml_rolls_back_everything(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:create", "page:read", "page-style:write"],
    )
    reviewer_pool = await database.role_pool("slaif_reviewer")
    agent_pool = await database.role_pool("slaif_agent_runtime")

    async def durable_state() -> tuple[Any, tuple[Any, ...]]:
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
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations = tuple(
                await reviewer.operations(seeded["workspace_id"], schema="content")
            )
        return tuple(row), operations

    try:
        async with _agent_client(database) as client:
            created = await client.post(
                "/api/agent/v1/pages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "page-style-cancel-create",
                },
                json={
                    "slug": "cancel-style",
                    "title": "Cancel style",
                    "locale": "en-US",
                },
            )
            assert created.status_code == 201, created.text
            page_id = UUID(created.json()["record"]["id"])
            path = f"/api/agent/v1/pages/{page_id}/style"
            baseline = await durable_state()
            dml_finished = asyncio.Event()

            async def direct_update() -> None:
                async with asyncpg_cow_session(
                    agent_pool,
                    session_id=seeded["workspace_id"],
                    operation_id=uuid4(),
                ) as cow:
                    row = await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_page_style_update("
                        "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                        seeded["site_id"],
                        page_id,
                        1,
                        '{"preset":"ember"}',
                        None,
                        None,
                        None,
                        [],
                    )
                    assert row is not None
                    assert row[4] == 2
                    dml_finished.set()
                    await asyncio.Future()

            task = asyncio.create_task(direct_update())
            await asyncio.wait_for(dml_finished.wait(), timeout=8)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert await durable_state() == baseline
            readback = await client.get(
                path, headers={"Authorization": f"Bearer {token}"}
            )
            assert readback.status_code == 200
            assert readback.json()["row_version"] == 1

            retry = await client.patch(
                path,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "page-style-cancel-retry",
                },
                json={"expected_row_version": 1, "palette": {"preset": "ember"}},
            )
            assert retry.status_code == 200, retry.text
            assert retry.json()["record"]["row_version"] == 2
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_page_style_public_cancellation_while_waiting_leaves_no_residue(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:create", "page:read", "page-style:write"],
    )
    reviewer_pool = await database.role_pool("slaif_reviewer")

    async def durable_state() -> tuple[Any, tuple[Any, ...]]:
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
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations = tuple(
                await reviewer.operations(seeded["workspace_id"], schema="content")
            )
        return tuple(row), operations

    try:
        async with _agent_client(database) as client:
            created = await client.post(
                "/api/agent/v1/pages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "page-style-public-cancel-create",
                },
                json={
                    "slug": "public-cancel-style",
                    "title": "Public cancel style",
                    "locale": "en-US",
                },
            )
            assert created.status_code == 201, created.text
            page_id = UUID(created.json()["record"]["id"])
            path = f"/api/agent/v1/pages/{page_id}/style"
            baseline = await durable_state()
            async with _hold_agent_structure_lock(
                database, seeded["workspace_id"], seeded["site_id"]
            ) as blocker:
                task = asyncio.create_task(
                    client.patch(
                        path,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Idempotency-Key": "page-style-public-cancel-reuse",
                        },
                        json={
                            "expected_row_version": 1,
                            "palette": {"preset": "ember"},
                        },
                    )
                )
                await _wait_for_page_structure_waiters(blocker, 1)
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            assert await durable_state() == baseline
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                lock_key = await owner.fetchval(
                    "SELECT hashtextextended($1,994)",
                    f"{seeded['workspace_id']}:{seeded['site_id']}:page-structure",
                )
                leaked = await owner.fetchval(
                    "SELECT count(*) FROM pg_locks WHERE locktype='advisory' "
                    "AND classid::bigint=(($1::bigint >> 32) & 4294967295) "
                    "AND objid::bigint=($1::bigint & 4294967295)",
                    lock_key,
                )
                assert leaked == 0
            retry = await client.patch(
                path,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": "page-style-public-cancel-reuse",
                },
                json={
                    "expected_row_version": 1,
                    "palette": {"preset": "ember"},
                },
            )
            assert retry.status_code == 200, retry.text
            assert retry.json()["record"]["row_version"] == 2
    finally:
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_page_style_raw_changes_require_write_when_pixels_are_equal(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    full_token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "page:create", "page:read", "page-style:write"],
    )
    read_token = await _capability_with_scopes(
        database, seeded, ["site:read", "page:read"]
    )
    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={
                "Authorization": f"Bearer {full_token}",
                "Idempotency-Key": "page-style-raw-equal-create",
            },
            json={"slug": "raw-equal", "title": "Raw equal", "locale": "en-US"},
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])
        path = f"/api/agent/v1/pages/{page_id}/style"
        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {
                "allowed_theme_tokens": ["typography.family"],
                "allowed_theme_typography_families": ["system"],
            },
        )
        family_denied = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {full_token}",
                "Idempotency-Key": "page-style-family-denied",
            },
            json={"expected_row_version": 1, "typography": {"family": "serif"}},
        )
        assert family_denied.status_code == 403, family_denied.text
        await _set_resource_constraints(database, seeded["workspace_id"], {})
        set_equal = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-raw-equal-read-set",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ocean"}},
        )
        assert set_equal.status_code == 403, set_equal.text
        assert (
            await client.get(path, headers={"Authorization": f"Bearer {read_token}"})
        ).json()["row_version"] == 1

        explicit = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {full_token}",
                "Idempotency-Key": "page-style-raw-equal-set",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ocean"}},
        )
        assert explicit.status_code == 200, explicit.text
        assert explicit.json()["record"]["row_version"] == 2
        reset = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-raw-equal-read-reset",
            },
            json={"expected_row_version": 2, "reset_tokens": ["palette.preset"]},
        )
        assert reset.status_code == 403, reset.text
        unchanged = await client.get(
            path, headers={"Authorization": f"Bearer {read_token}"}
        )
        assert unchanged.status_code == 200
        assert unchanged.json()["row_version"] == 2
        assert unchanged.json()["overrides"] == {"palette": {"preset": "ocean"}}

        restored = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {full_token}",
                "Idempotency-Key": "page-style-raw-equal-reset",
            },
            json={"expected_row_version": 2, "reset_tokens": ["palette.preset"]},
        )
        assert restored.status_code == 200, restored.text
        assert restored.json()["record"]["row_version"] == 3
        no_effect = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-raw-equal-no-effect",
            },
            json={"expected_row_version": 3, "reset_tokens": ["palette.preset"]},
        )
        assert no_effect.status_code == 200, no_effect.text
        assert no_effect.json()["action"] is None


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
        changed_operation_id = UUID(changed.json()["operation_id"])
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            capability_id = await owner.fetchval(
                "SELECT id FROM control.capability WHERE public_id=$1",
                full_token.split("_", maxsplit=2)[1],
            )
            audit_row = await owner.fetchrow(
                "SELECT audit.operation_id,audit.capability_id,audit.workspace_id,"
                "audit.site_id,workspace.delegator_id,audit.resource_type,"
                "audit.resource_id,audit.response_status,audit.action,"
                "audit.http_method,audit.quota_kind "
                "FROM audit.agent_mutation audit "
                "JOIN control.workspace workspace ON workspace.id=audit.workspace_id "
                "WHERE audit.operation_id=$1",
                changed_operation_id,
            )
            assert audit_row is not None
            assert tuple(audit_row) == (
                changed_operation_id,
                capability_id,
                seeded["workspace_id"],
                seeded["site_id"],
                seeded["delegator_id"],
                "page_style",
                page_id,
                200,
                "PAGE_STYLE_UPDATED",
                "PATCH",
                "mutation",
            )
            idempotency_row = await owner.fetchrow(
                "SELECT operation_id,capability_id,workspace_id,status_code,"
                "resource_id,resource_type FROM control.agent_idempotency "
                "WHERE workspace_id=$1 AND idempotency_key=$2",
                seeded["workspace_id"],
                "page-style-accounting-ember",
            )
            assert idempotency_row is not None
            assert tuple(idempotency_row) == (
                changed_operation_id,
                capability_id,
                seeded["workspace_id"],
                200,
                page_id,
                "page_style",
            )

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
        denied_reset = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-accounting-denied-reset"},
            json={"expected_row_version": 2, "reset_tokens": ["palette.preset"]},
        )
        assert denied_reset.status_code == 403, denied_reset.text
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
        expired_patch = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-expired-patch"},
            json={"expected_row_version": 3, "palette": {"preset": "ember"}},
        )
        assert expired_patch.status_code == 401, expired_patch.text
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.workspace SET expires_at=now()+interval '1 hour',"
                "status='FREEZING' WHERE id=$1",
                seeded["workspace_id"],
            )
        assert (await client.get(path, headers=auth)).status_code == 401
        frozen_patch = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-frozen-patch"},
            json={"expected_row_version": 3, "palette": {"preset": "ember"}},
        )
        assert frozen_patch.status_code == 401, frozen_patch.text
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
        archived_patch = await client.patch(
            path,
            headers={**auth, "Idempotency-Key": "page-style-archived-patch"},
            json={"expected_row_version": 3, "palette": {"preset": "ember"}},
        )
        assert archived_patch.status_code == 401, archived_patch.text
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
        revoked_patch = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {limited_token}",
                "Idempotency-Key": "page-style-revoked-patch",
            },
            json={"expected_row_version": 6, "palette": {"preset": "ember"}},
        )
        assert revoked_patch.status_code == 401, revoked_patch.text

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
    auth = {"Authorization": f"Bearer {token_a}"}
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.capability SET mutation_quota=1000,delete_quota=100 "
            "WHERE workspace_id=$1",
            seeded["workspace_id"],
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

        style_update_response, page_update_response = await race(
            style_again, page_update, "page-style-v-page", "page-update-v-style"
        )
        final_update_page = await client.get(
            update_path, headers={"Authorization": f"Bearer {token_a}"}
        )
        final_update_style = await client.get(
            update_style_path, headers={"Authorization": f"Bearer {token_a}"}
        )
        assert final_update_page.status_code == 200
        assert final_update_page.json()["row_version"] == 2
        if style_update_response.status_code == 200:
            assert page_update_response.status_code == 409
            assert final_update_page.json()["title"] == "style-update-race"
            assert final_update_style.json()["overrides"] == {
                "layout": {"spacing": "lg"}
            }
        else:
            assert page_update_response.status_code == 200
            assert final_update_page.json()["title"] == "Updated"
            assert final_update_style.json()["overrides"] == {}

        reverse_update_page = await create_page(
            "style-reverse-update", "page-style-reverse-update-create"
        )
        reverse_update_path = f"/api/agent/v1/pages/{reverse_update_page}"
        reverse_update_style_path = f"{reverse_update_path}/style"

        async def page_update_first(key: str) -> httpx.Response:
            return await client.patch(
                reverse_update_path,
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "title": "Updated first"},
            )

        async def style_after_page_update(key: str) -> httpx.Response:
            return await client.patch(
                reverse_update_style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "layout": {"spacing": "lg"}},
            )

        reverse_page_response, reverse_style_response = await race(
            page_update_first,
            style_after_page_update,
            "page-update-first",
            "page-style-after-update",
        )
        assert reverse_page_response.status_code == 200
        assert reverse_style_response.status_code == 409
        reverse_page = await client.get(reverse_update_path, headers=auth)
        reverse_style = await client.get(reverse_update_style_path, headers=auth)
        assert reverse_page.json()["title"] == "Updated first"
        assert reverse_style.json()["overrides"] == {}

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

        style_move_response, page_move_response = await race(
            style_before_move, page_move, "page-style-v-move", "page-move-v-style"
        )
        final_move_page = await client.get(move_path, headers=auth)
        final_move_style = await client.get(move_style_path, headers=auth)
        assert final_move_page.status_code == 200
        if style_move_response.status_code == 200:
            assert page_move_response.status_code == 409
            assert final_move_page.json()["parent_id"] is None
            assert final_move_style.json()["overrides"] == {"shape": {"radius": "lg"}}
        else:
            assert page_move_response.status_code == 200
            assert final_move_page.json()["parent_id"] == str(parent_page)
            assert final_move_style.json()["overrides"] == {}

        reverse_move_parent = await create_page(
            "style-reverse-move-parent", "page-style-reverse-move-parent"
        )
        reverse_move_page = await create_page(
            "style-reverse-move", "page-style-reverse-move-create"
        )
        reverse_move_path = f"/api/agent/v1/pages/{reverse_move_page}"
        reverse_move_style_path = f"{reverse_move_path}/style"

        async def page_move_first(key: str) -> httpx.Response:
            return await client.post(
                f"{reverse_move_path}:move",
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={
                    "expected_row_version": 1,
                    "parent_id": str(reverse_move_parent),
                },
            )

        async def style_after_page_move(key: str) -> httpx.Response:
            return await client.patch(
                reverse_move_style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "shape": {"radius": "lg"}},
            )

        reverse_move_response, reverse_move_style_response = await race(
            page_move_first,
            style_after_page_move,
            "page-move-first",
            "page-style-after-move",
        )
        assert reverse_move_response.status_code == 200
        assert reverse_move_style_response.status_code == 409
        reverse_move = await client.get(reverse_move_path, headers=auth)
        reverse_move_style = await client.get(reverse_move_style_path, headers=auth)
        assert reverse_move.json()["parent_id"] == str(reverse_move_parent)
        assert reverse_move_style.json()["overrides"] == {}

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

        style_delete_response, page_delete_response = await race(
            style_before_delete,
            page_delete,
            "page-style-v-delete",
            "page-delete-v-style",
            loser_status=(404, 409),
        )
        if style_delete_response.status_code == 200:
            assert page_delete_response.status_code == 409
            final_delete_style = await client.get(delete_style_path, headers=auth)
            assert final_delete_style.status_code == 200
            assert final_delete_style.json()["overrides"] == {"shape": {"shadow": "lg"}}
        else:
            assert page_delete_response.status_code == 200
            assert (await client.get(delete_path, headers=auth)).status_code == 404

        reverse_delete_page = await create_page(
            "style-reverse-delete", "page-style-reverse-delete-create"
        )
        reverse_delete_path = f"/api/agent/v1/pages/{reverse_delete_page}"
        reverse_delete_style_path = f"{reverse_delete_path}/style"

        async def page_delete_first(key: str) -> httpx.Response:
            return await client.request(
                "DELETE",
                reverse_delete_path,
                headers={
                    "Authorization": f"Bearer {token_b}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1},
            )

        async def style_after_page_delete(key: str) -> httpx.Response:
            return await client.patch(
                reverse_delete_style_path,
                headers={
                    "Authorization": f"Bearer {token_a}",
                    "Idempotency-Key": key,
                },
                json={"expected_row_version": 1, "shape": {"shadow": "lg"}},
            )

        reverse_delete_response, reverse_delete_style_response = await race(
            page_delete_first,
            style_after_page_delete,
            "page-delete-first",
            "page-style-after-delete",
            loser_status=(404, 409),
        )
        assert reverse_delete_response.status_code == 200
        assert reverse_delete_style_response.status_code == 404
        assert (await client.get(reverse_delete_path, headers=auth)).status_code == 404


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


@pytest.mark.asyncio
async def test_page_style_reset_serializes_with_concurrent_theme_change(
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
    await _set_resource_constraints(
        database,
        seeded["workspace_id"],
        {
            "allowed_theme_tokens": ["palette.preset"],
            "allowed_theme_palette_presets": ["ocean", "meadow", "ember"],
        },
    )
    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-theme-race-create",
            },
            json={
                "slug": "style-theme-race",
                "title": "Style theme race",
                "locale": "en-US",
            },
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])
        path = f"/api/agent/v1/pages/{page_id}/style"
        initial = await client.patch(
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-theme-race-initial",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ember"}},
        )
        assert initial.status_code == 200, initial.text

        async with _hold_theme_lock(
            database, seeded["workspace_id"], seeded["site_id"]
        ) as blocker:
            theme_lock = await blocker.fetchval(
                "SELECT hashtextextended($1,995)",
                f"{seeded['workspace_id']}:{seeded['site_id']}:theme",
            )
            theme_task = asyncio.create_task(
                client.patch(
                    "/api/agent/v1/theme",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "page-style-theme-race-theme",
                    },
                    json={"expected_row_version": 1, "palette": {"preset": "meadow"}},
                )
            )
            await _wait_for_advisory_waiters(blocker, theme_lock)
            reset_task = asyncio.create_task(
                client.patch(
                    path,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "page-style-theme-race-reset",
                    },
                    json={
                        "expected_row_version": 2,
                        "reset_tokens": ["palette.preset"],
                    },
                )
            )
            await _wait_for_advisory_waiters(blocker, theme_lock, expected=2)
        theme_response, reset_response = await asyncio.gather(theme_task, reset_task)
        assert theme_response.status_code == 200, theme_response.text
        assert reset_response.status_code == 200, reset_response.text
        assert theme_response.json()["record"]["palette"]["preset"] == "meadow"
        assert reset_response.json()["record"]["overrides"] == {}
        assert (
            reset_response.json()["record"]["resolved"]["palette"]["preset"] == "meadow"
        )
        final = await client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert final.status_code == 200
        assert final.json()["resolved"]["palette"]["preset"] == "meadow"

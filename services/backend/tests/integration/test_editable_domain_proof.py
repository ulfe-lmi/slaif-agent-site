"""Real PostgreSQL proof for the 075-b migration boundary."""

from __future__ import annotations

from uuid import uuid4

import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import (
    deploy_cow_functions,
    disable_cow_schema,
    enable_cow_schema,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.db.migrations import run_migration


@pytest.mark.asyncio
async def test_editable_domain_migration_round_trip_restores_field_contract(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await disable_cow_schema(AsyncpgExecutor(owner), schema="content")
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert await owner.fetchval(
            "SELECT to_regclass('content.content_item_translation') IS NOT NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regclass('content.item_relation') IS NOT NULL"
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="039_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert await owner.fetchval(
            "SELECT to_regclass('content.content_item_translation') IS NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regprocedure("
            "'content.slaif_field_definition_create("
            "uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)') "
            "IS NOT NULL"
        )
        site_id = await owner.fetchval(
            "INSERT INTO control.site("
            "site_key,display_name,default_locale,component_catalog_version) "
            "VALUES ($1,'Round Trip','en','catalog-v1') RETURNING id",
            f"round-trip-{uuid4().hex[:12]}",
        )
        type_id = uuid4()
        await owner.execute(
            "INSERT INTO content.content_type (id,site_id,key,slug_pattern) "
            "VALUES ($1,$2,'round-trip','/{slug}')",
            type_id,
            site_id,
        )
        field = await owner.fetchrow(
            "SELECT * FROM content.slaif_field_definition_create("
            "$1,'title','Title','short_text',false,false,1,0,'{}','{}')",
            type_id,
        )
        assert field is not None
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )


@pytest.mark.asyncio
async def test_collection_contract_downgrades_from_head_to_040_and_back(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="040_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert await owner.fetchval(
            "SELECT NOT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_schema='content' AND table_name='collection_view' "
            "AND column_name='row_version')"
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )


@pytest.mark.asyncio
async def test_055_downgrade_restores_054_functions_grants_and_data(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Prove 054↔055 restores the exact lock/helper contract and rows."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await disable_cow_schema(AsyncpgExecutor(owner), schema="content")
            site_id = await owner.fetchval(
                "INSERT INTO control.site("
                "site_key,display_name,default_locale,component_catalog_version) "
                "VALUES ($1,'055 round trip','en-US','catalog-v1') RETURNING id",
                f"round-trip-055-{uuid4().hex[:12]}",
            )
            await owner.execute(
                "INSERT INTO content.site_locale "
                "(site_id,tag,enabled,is_default,position) "
                "VALUES ($1,'en-US',true,true,0)",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.page "
                "(site_id,slug,title,status,locale) "
                "VALUES ($1,'round-trip','Round trip','PUBLISHED','en-US')",
                site_id,
            )
    function_sql = (
        "SELECT pg_get_functiondef($1::regprocedure), "
        "pg_get_userbyid(proowner), "
        "has_function_privilege('public',$1,'EXECUTE'), "
        "has_function_privilege('slaif_editor_runtime',$1,'EXECUTE') "
        "FROM pg_proc WHERE oid=$1::regprocedure"
    )
    helper_signature = "content.slaif_redirect_page_target_dependency(uuid,text,uuid)"
    editor_signature = (
        "control.slaif_human_editor_workspace_assert(uuid,uuid,uuid,uuid,text,boolean)"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        before = await owner.fetchrow(function_sql, helper_signature)
        assert "candidate record" in before[0]
        assert "pg_advisory_xact_lock_shared" in (
            await owner.fetchval(
                "SELECT pg_get_functiondef($1::regprocedure)", editor_signature
            )
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="054_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        helper = await owner.fetchrow(function_sql, helper_signature)
        editor = await owner.fetchrow(function_sql, editor_signature)
        assert "candidate record" not in helper[0]
        assert "pg_advisory_xact_lock_shared" not in editor[0]
        assert tuple(helper[1:]) == ("slaif_owner", False, False)
        assert tuple(editor[1:]) == ("slaif_owner", False, True)
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM content.page WHERE slug='round-trip'"
            )
            == 1
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        helper = await owner.fetchrow(function_sql, helper_signature)
        editor = await owner.fetchrow(function_sql, editor_signature)
        assert "candidate record" in helper[0]
        assert "pg_advisory_xact_lock_shared" in editor[0]
        assert tuple(helper[1:]) == ("slaif_owner", False, False)
        assert tuple(editor[1:]) == ("slaif_owner", False, True)
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM content.page WHERE slug='round-trip'"
            )
            == 1
        )


@pytest.mark.asyncio
async def test_site_data_substrate_downgrades_from_head_to_041_and_back(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        async with owner.transaction():
            await disable_cow_schema(AsyncpgExecutor(owner), schema="content")
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert await owner.fetchval(
            "SELECT to_regclass('content.site_locale') IS NOT NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regclass('content.navigation_item') IS NOT NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regclass('content.redirect') IS NOT NULL"
        )
        assert await owner.fetchval(
            "SELECT to_regclass('content.proposed_side_effect') IS NOT NULL"
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="041_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        for table in (
            "site_locale",
            "navigation_item",
            "redirect",
            "proposed_side_effect",
        ):
            assert await owner.fetchval(
                "SELECT to_regclass($1) IS NULL", f"content.{table}"
            )
        assert await owner.fetchval(
            "SELECT to_regprocedure("
            "'content.slaif_collection_view_v2_get(uuid,uuid)') IS NOT NULL"
        )
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="upgrade",
        revision="head",
    )


@pytest.mark.asyncio
async def test_upgrade_rebuilds_enabled_cow_without_pending_workspace_operations(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The production path tears down empty COW views before 040-042."""
    database = agent_site_database
    await upgrade(database.settings)
    await run_migration(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
        operation="downgrade",
        revision="041_001",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        executor = AsyncpgExecutor(owner)
        await deploy_cow_functions(executor)
        await enable_cow_schema(
            executor,
            schema="content",
            allow_deferred_fks=True,
            allow_unsafe_canonical_writes=False,
        )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        before = await owner.fetchval(
            "SELECT to_regclass('content.page_base') IS NOT NULL"
        )
        assert before
    await upgrade(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT version_num::text FROM control.alembic_version"
            )
            == "065_001"
        )
        assert await owner.fetchval("SELECT to_regclass('content.page') IS NOT NULL")
        assert await owner.fetchval("SELECT to_regclass('content.page_base') IS NULL")

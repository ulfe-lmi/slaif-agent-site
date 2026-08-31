"""Real PostgreSQL proof for the 075-b migration boundary."""

from __future__ import annotations

from uuid import uuid4

import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import (
    deploy_cow_functions,
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
async def test_site_data_substrate_downgrades_from_head_to_041_and_back(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
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
            == "046_001"
        )
        assert await owner.fetchval("SELECT to_regclass('content.page') IS NOT NULL")
        assert await owner.fetchval("SELECT to_regclass('content.page_base') IS NULL")

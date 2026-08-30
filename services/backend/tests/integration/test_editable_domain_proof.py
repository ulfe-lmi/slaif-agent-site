"""Real PostgreSQL proof for the 075-b migration boundary."""

from __future__ import annotations

from uuid import uuid4

import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration


@pytest.mark.asyncio
async def test_editable_domain_migration_round_trip_restores_field_contract(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
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

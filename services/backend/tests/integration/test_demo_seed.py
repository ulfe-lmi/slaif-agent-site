"""Fresh-install-only demo-site bootstrap evidence."""

from __future__ import annotations

import asyncio

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    ensure_demo_site,
    reconcile,
    upgrade,
)
from slaif_agent_site.db.connections import owner_connection


async def _rows(database: AgentSiteDatabase) -> list[tuple[object, ...]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return [
            tuple(row)
            for row in await owner.fetch(
                "SELECT site_key, display_name, default_locale, status, "
                "canonical_revision, content_model_revision, "
                "component_catalog_version FROM control.site ORDER BY site_key"
            )
        ]


async def test_demo_seed_is_exact_idempotent_concurrent_and_mismatch_safe(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)

    await asyncio.gather(
        ensure_demo_site(database.settings), ensure_demo_site(database.settings)
    )
    expected = [("demo", "SLAIF Demo Site", "en", "ACTIVE", 0, 0, "catalog-v0")]
    assert await _rows(database) == expected
    await ensure_demo_site(database.settings)
    assert await _rows(database) == expected

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.site SET display_name = 'Unexpected' "
            "WHERE site_key = 'demo'"
        )
    with pytest.raises(BootstrapStateError, match="demo seed state mismatch"):
        await ensure_demo_site(database.settings)
    assert (await _rows(database))[0][1] == "Unexpected"


async def test_demo_seed_skips_initialized_installation_without_overwrite(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.installation_state SET initialized_at = CURRENT_TIMESTAMP "
            "WHERE singleton"
        )
    await ensure_demo_site(database.settings)
    assert await _rows(database) == []


async def test_disabled_seed_leaves_fresh_catalog_empty(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    assert database.settings.demo_seed is False
    assert await _rows(database) == []


async def test_demo_seed_failure_rolls_back_insert(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "CREATE FUNCTION control.slaif_test_reject_demo() RETURNS trigger "
            "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'fixture rejection'; END $$"
        )
        await owner.execute(
            "CREATE TRIGGER slaif_test_reject_demo AFTER INSERT ON control.site "
            "FOR EACH ROW EXECUTE FUNCTION control.slaif_test_reject_demo()"
        )
    with pytest.raises(asyncpg.RaiseError, match="fixture rejection"):
        await ensure_demo_site(database.settings)
    assert await _rows(database) == []

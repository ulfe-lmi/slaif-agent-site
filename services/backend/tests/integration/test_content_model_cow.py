"""Integration test proving content model tables are COW-enabled after bootstrap.

Architecture reference: ARCHITECTURE-for-agents.md §10 (logical COW content
model) and §8 (workspace lifecycle). Requires a real PostgreSQL instance
with the full migration chain and COW foundation deployed.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import (
    deploy_cow_functions,
    enable_cow_schema,
)
from slaif_agent_site.bootstrap.service import upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor


def _owner_dsn(database: AgentSiteDatabase) -> str:
    parameters = database.connection_parameters
    host = quote(str(parameters["host"]), safe="[]:.")
    login, password = database.credentials["slaif_owner"]
    return (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{parameters['port']}/{database.name}"
    )


EXPECTED_CONTENT_TABLES = frozenset(
    {
        "content_type",
        "field_definition",
        "content_item",
        "collection_view",
    }
)


@pytest.mark.asyncio
async def test_content_tables_have_cow_triplets(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """After migrations + COW enable, each content table has base/changes companions."""
    settings = agent_site_database.settings
    await upgrade(settings)
    async with owner_connection(
        settings.resolved_owner_dsn(), expected_database=settings.expected_database
    ) as connection:
        await _assert_cow_triplets(connection)


async def _assert_cow_triplets(connection: Any) -> None:
    executor = AsyncpgExecutor(connection)
    await deploy_cow_functions(executor)
    await enable_cow_schema(
        executor,
        schema="content",
        allow_deferred_fks=True,
        allow_unsafe_canonical_writes=False,
    )
    rows = await connection.fetch(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'content'
        ORDER BY table_name
        """
    )
    table_names = {row["table_name"] for row in rows}

    for name in sorted(EXPECTED_CONTENT_TABLES):
        assert f"{name}_base" in table_names, (
            f"missing COW base companion for content.{name}"
        )
        assert f"{name}_changes" in table_names, (
            f"missing COW changes companion for content.{name}"
        )
        assert name in table_names, f"missing canonical view for content.{name}"

    # Verify the base tables have the common columns guaranteed for all
    # site-rooted content tables.
    for name in sorted(EXPECTED_CONTENT_TABLES):
        cols = {
            row["column_name"]
            for row in await connection.fetch(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'content' AND table_name = $1
                """,
                f"{name}_base",
            )
        }
        assert "id" in cols, f"{name}_base missing id column"
        assert "created_at" in cols, f"{name}_base missing created_at column"
        assert "updated_at" in cols, f"{name}_base missing updated_at column"

    content_type_columns = await connection.fetch(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'content' AND table_name = 'content_type_base'
        """
    )
    assert {"site_id", "key"} <= {row["column_name"] for row in content_type_columns}

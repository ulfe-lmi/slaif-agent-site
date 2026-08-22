"""Integration test proving content model tables are COW-enabled after bootstrap.

Architecture reference: ARCHITECTURE-for-agents.md §10 (logical COW content
model) and §8 (workspace lifecycle). Requires a real PostgreSQL instance
with the full migration chain and COW foundation deployed.
"""

from __future__ import annotations

from typing import Any

import asyncpg
import pytest

EXPECTED_CONTENT_TABLES = frozenset(
    {
        "content_type",
        "field_definition",
        "content_item",
    }
)


@pytest.mark.asyncio
async def test_content_tables_have_cow_triplets(postgres: Any) -> None:
    """After migrations + COW enable, each content table has base/changes companions."""
    conn: asyncpg.Connection = postgres
    rows = await conn.fetch(
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

    # Verify the base tables have expected columns.
    for name in sorted(EXPECTED_CONTENT_TABLES):
        cols = {
            row["column_name"]
            for row in await conn.fetch(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'content' AND table_name = $1
                """,
                f"{name}_base",
            )
        }
        assert "id" in cols, f"{name}_base missing id column"
        assert "site_id" in cols, f"{name}_base missing site_id column"
        assert "created_at" in cols, f"{name}_base missing created_at column"
        assert "updated_at" in cols, f"{name}_base missing updated_at column"

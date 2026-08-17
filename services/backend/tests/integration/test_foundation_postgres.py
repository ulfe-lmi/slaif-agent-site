"""Downstream adoption tests for the public PostgreSQL foundation API."""

from __future__ import annotations

import asyncio
import contextlib
import uuid

import asyncpg
import pytest
from conftest import FoundationDatabase
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
)


async def test_runtime_session_isolates_then_reviewer_promotes(
    foundation_database: FoundationDatabase,
) -> None:
    session_id = uuid.uuid4()
    operation_id = uuid.uuid4()

    async with asyncpg_cow_session(
        foundation_database.runtime_pool,
        session_id=session_id,
        operation_id=operation_id,
    ) as cow:
        await cow.execute(
            f"INSERT INTO {foundation_database.relation} (id, title) "
            "VALUES (1001, 'workspace')"
        )
        await cow.execute(
            f"UPDATE {foundation_database.relation} "
            "SET title = 'workspace update' WHERE id = 1"
        )
        rows = await cow.execute(
            f"SELECT id, title FROM {foundation_database.relation} ORDER BY id"
        )
        assert rows == [(1, "workspace update"), (1001, "workspace")]

    canonical = await foundation_database.setup.fetch(
        f"SELECT id, title FROM {foundation_database.relation} ORDER BY id"
    )
    assert [tuple(row) for row in canonical] == [(1, "canonical")]

    async with asyncpg_cow_reviewer(foundation_database.reviewer_pool) as reviewer:
        operations = await reviewer.operations(
            session_id, schema=foundation_database.schema
        )
        assert operations == [operation_id]
        assert (
            await reviewer.dependencies(session_id, schema=foundation_database.schema)
            == []
        )
        assert (
            await reviewer.conflicts(session_id, schema=foundation_database.schema)
            == []
        )
        result = await reviewer.commit_session(
            session_id, schema=foundation_database.schema
        )
        assert result.conflict_policy == "error"
        assert not result.no_op
        assert not result.has_pending_operations

    promoted = await foundation_database.setup.fetch(
        f"SELECT id, title FROM {foundation_database.relation} ORDER BY id"
    )
    assert [tuple(row) for row in promoted] == [
        (1, "workspace update"),
        (1001, "workspace"),
    ]


async def test_reviewer_discards_complete_session(
    foundation_database: FoundationDatabase,
) -> None:
    session_id = uuid.uuid4()

    async with asyncpg_cow_session(
        foundation_database.runtime_pool, session_id=session_id
    ) as cow:
        await cow.execute(
            f"INSERT INTO {foundation_database.relation} (id, title) "
            "VALUES (1002, 'discard me')"
        )

    async with asyncpg_cow_reviewer(foundation_database.reviewer_pool) as reviewer:
        result = await reviewer.discard_session(
            session_id, schema=foundation_database.schema
        )
        assert not result.no_op
        assert not result.has_pending_operations

    assert (
        await foundation_database.setup.fetchval(
            f"SELECT count(*) FROM {foundation_database.relation} WHERE id = 1002"
        )
        == 0
    )


async def test_runtime_and_reviewer_paths_fail_closed(
    foundation_database: FoundationDatabase,
) -> None:
    async with foundation_database.runtime_pool.acquire() as runtime:
        with pytest.raises(asyncpg.PostgresError):
            await runtime.execute(
                f"INSERT INTO {foundation_database.relation} (id, title) "
                "VALUES (1003, 'missing context')"
            )
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await runtime.fetch(
                f"SELECT * FROM {foundation_database.canonical_relation}"
            )

    with pytest.raises(asyncpg.PostgresError):
        async with asyncpg_cow_reviewer(
            foundation_database.runtime_pool
        ) as unauthorized_reviewer:
            await unauthorized_reviewer.operations(
                uuid.uuid4(), schema=foundation_database.schema
            )


async def test_cancelled_scope_rolls_back_and_cleans_pooled_context(
    foundation_database: FoundationDatabase,
) -> None:
    cancelled_session = uuid.uuid4()
    replacement_session = uuid.uuid4()
    mutation_finished = asyncio.Event()
    keep_scope_open = asyncio.Event()

    async def mutate_until_cancelled() -> None:
        async with asyncpg_cow_session(
            foundation_database.runtime_pool,
            session_id=cancelled_session,
        ) as cow:
            await cow.execute(
                f"INSERT INTO {foundation_database.relation} (id, title) "
                "VALUES (1004, 'cancelled')"
            )
            mutation_finished.set()
            await keep_scope_open.wait()

    task = asyncio.create_task(mutate_until_cancelled())
    await asyncio.wait_for(mutation_finished.wait(), timeout=5)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    async with foundation_database.runtime_pool.acquire() as runtime:
        with pytest.raises(asyncpg.PostgresError):
            await runtime.execute(
                f"INSERT INTO {foundation_database.relation} (id, title) "
                "VALUES (1005, 'leaked context')"
            )

    async with asyncpg_cow_session(
        foundation_database.runtime_pool,
        session_id=replacement_session,
    ) as cow:
        rows = await cow.execute(
            f"SELECT id FROM {foundation_database.relation} WHERE id = 1004"
        )
        assert rows == []

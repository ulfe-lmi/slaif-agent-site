"""Tests for the idempotency framework."""

from __future__ import annotations

import pytest

from slaif_agent_site.agent_state.idempotency import (
    IdempotencyMismatchError,
    IdempotencyRecord,
    IdempotencyStore,
    compute_request_digest,
)


class TestIdempotency:
    @pytest.mark.anyio
    async def test_first_request_returns_none(self) -> None:
        store = IdempotencyStore()
        result = await store.get("key-1", compute_request_digest({"a": 1}))
        assert result is None

    @pytest.mark.anyio
    async def test_same_key_same_payload_returns_record(self) -> None:
        store = IdempotencyStore()
        digest = compute_request_digest({"action": "create"})
        record = IdempotencyRecord(
            key="key-1",
            digest=digest,
            operation_id="op-1",
            status=201,
            response_body={"id": "123"},
        )
        await store.put(record)
        result = await store.get("key-1", digest)
        assert result is not None
        assert result.status == 201

    @pytest.mark.anyio
    async def test_same_key_different_payload_raises(self) -> None:
        store = IdempotencyStore()
        digest1 = compute_request_digest({"action": "create"})
        record = IdempotencyRecord(
            key="key-1",
            digest=digest1,
            operation_id="op-1",
            status=201,
            response_body={},
        )
        await store.put(record)
        digest2 = compute_request_digest({"action": "delete"})
        with pytest.raises(IdempotencyMismatchError):
            await store.get("key-1", digest2)

    def test_digest_is_deterministic(self) -> None:
        d1 = compute_request_digest({"b": 2, "a": 1})
        d2 = compute_request_digest({"a": 1, "b": 2})
        assert d1 == d2

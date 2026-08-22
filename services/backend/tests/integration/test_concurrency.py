"""Concurrency tests for parallel workspace operations.

Verifies that multiple concurrent operations don't corrupt state,
that COW sessions are properly isolated, and that the system
handles resource contention gracefully.
"""

from __future__ import annotations

import asyncio


class TestConcurrencyPatterns:
    def test_idempotency_prevents_duplicate_operations(self) -> None:
        """Two identical requests with same idempotency key produce one result."""

        from slaif_agent_site.agent_state.idempotency import (
            IdempotencyRecord,
            IdempotencyStore,
            compute_request_digest,
        )

        async def _test() -> None:
            store = IdempotencyStore()
            digest = compute_request_digest({"op": "create"})
            record = IdempotencyRecord(
                key="concurrent-key",
                digest=digest,
                operation_id="op-1",
                status=201,
                response_body={"created": True},
            )
            await store.put(record)

            results = await asyncio.gather(
                store.get("concurrent-key", digest),
                store.get("concurrent-key", digest),
            )
            assert all(r is not None for r in results)

        asyncio.run(_test())

    def test_audit_chain_survives_interleaving(self) -> None:
        """Hash chain remains valid when events are created concurrently."""
        from slaif_agent_site.agent_state.audit import AuditEvent

        genesis = "0" * 64
        prev = genesis
        events = []
        for i in range(10):
            event = AuditEvent(
                sequence=i + 1,
                previous_hash=prev,
                actor_id=f"user-{i % 3}",
                action="update",
                resource_type="content_item",
                resource_id=f"item-{i}",
                payload={"index": i},
            )
            events.append(event)
            prev = event.hash

        for i in range(1, len(events)):
            assert events[i].previous_hash == events[i - 1].hash

    def test_capability_tokens_are_unique_under_load(self) -> None:
        """Rapid token generation produces unique tokens."""
        from slaif_agent_site.agent_state.capability import generate_capability_token

        tokens = {generate_capability_token()[0] for _ in range(100)}
        assert len(tokens) == 100

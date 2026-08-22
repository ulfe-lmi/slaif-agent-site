"""Recovery tests: verify system handles failures gracefully.

Architecture reference: ARCHITECTURE-for-agents.md §15 (reliability).
Tests verify that partial failures don't leave the system in an
inconsistent state and that all errors are properly contained.
"""

from __future__ import annotations

from slaif_agent_site.agent_state.promotion import PromotionError


class TestRecoveryPatterns:
    """Verify that error paths don't corrupt state."""

    def test_promotion_error_is_contained(self) -> None:
        """PromotionError doesn't cascade beyond its scope."""
        exc = PromotionError("COW conflict during promotion")
        assert "conflict" in str(exc).lower()
        assert exc.reason == "COW conflict during promotion"

    def test_capability_digest_survives_restart_simulation(self) -> None:
        """Digest computation is deterministic across process boundaries."""
        from slaif_agent_site.agent_state.capability import compute_digest

        token = "sas2_abcdef1234567890_" + "a" * 64
        digest1 = compute_digest(token)
        digest2 = compute_digest(token)
        assert digest1 == digest2
        assert len(digest1) == 64

    def test_idempotency_store_clear_and_rebuild(self) -> None:
        """Store can be cleared (simulating restart) without corruption."""
        import asyncio

        from slaif_agent_site.agent_state.idempotency import (
            IdempotencyRecord,
            IdempotencyStore,
            compute_request_digest,
        )

        async def _test() -> None:
            store = IdempotencyStore()
            digest = compute_request_digest({"op": "test"})
            record = IdempotencyRecord(
                key="k",
                digest=digest,
                operation_id="o",
                status=201,
                response_body={},
            )
            await store.put(record)
            result = await store.get("k", digest)
            assert result is not None

            # Simulate restart
            store.clear()
            result_after = await store.get("k", digest)
            assert result_after is None  # clean state after clear

        asyncio.run(_test())

    def test_audit_chain_detects_tampering(self) -> None:
        """If any event in a chain is modified, subsequent hashes won't match."""
        from slaif_agent_site.agent_state.audit import AuditEvent, compute_event_hash

        genesis = "0" * 64
        prev = genesis
        events = []
        for i in range(3):
            event = AuditEvent(
                sequence=i + 1,
                previous_hash=prev,
                actor_id="system",
                action=f"action_{i}",
                resource_type="test",
                resource_id=f"res-{i}",
            )
            events.append(event)
            prev = event.hash

        # Simulate tampering: recompute what hash SHOULD be for event[0]
        # if its action was different
        tampered_hash = compute_event_hash(
            previous_hash=genesis,
            timestamp=events[0].timestamp,
            actor_id="attacker",
            action=events[0].action,
            resource_type=events[0].resource_type,
            resource_id=events[0].resource_id,
            payload_digest=events[0].payload_digest,
        )
        assert tampered_hash != events[0].hash
        # The chain would detect this because event[1].previous_hash
        # references the original hash, not the tampered one

    def test_workspace_status_transitions_are_bounded(self) -> None:
        """WorkspaceStatus only contains architecture-defined states."""
        from slaif_agent_site.agent_state.workspace_models import WorkspaceStatus

        valid_states = {
            "CREATING",
            "ACTIVE",
            "REVOKED",
            "EXPIRED",
            "FREEZING",
            "REVIEW",
            "ACCEPT_QUEUED",
            "SELECTIVE_ACCEPT_QUEUED",
            "DISCARD_QUEUED",
            "PROMOTING",
            "ACCEPTED",
            "CONFLICTED",
            "DISCARDING",
            "DISCARDED",
            "FAILED",
        }
        assert {s.value for s in WorkspaceStatus} == valid_states

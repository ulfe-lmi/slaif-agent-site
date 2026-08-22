"""Tests for audit trail integrity."""

from __future__ import annotations

from slaif_agent_site.agent_state.audit import (
    AuditEvent,
    compute_payload_digest,
)


class TestAuditEvent:
    def test_creates_event_with_hash_chain(self) -> None:
        e1 = AuditEvent(
            sequence=1,
            previous_hash="genesis",
            actor_id="user-1",
            action="create",
            resource_type="content_type",
            resource_id="ct-1",
        )
        assert len(e1.hash) == 64
        assert e1.previous_hash == "genesis"

    def test_chain_links(self) -> None:
        e1 = AuditEvent(
            sequence=1,
            previous_hash="genesis",
            actor_id="u",
            action="create",
            resource_type="page",
            resource_id="p-1",
        )
        e2 = AuditEvent(
            sequence=2,
            previous_hash=e1.hash,
            actor_id="u",
            action="update",
            resource_type="page",
            resource_id="p-1",
        )
        assert e2.previous_hash == e1.hash
        assert e2.hash != e1.hash

    def test_different_payload_different_hash(self) -> None:
        d1 = compute_payload_digest({"key": "value"})
        d2 = compute_payload_digest({"key": "other"})
        assert d1 != d2

    def test_same_payload_same_digest(self) -> None:
        d1 = compute_payload_digest({"a": 1, "b": 2})
        d2 = compute_payload_digest({"b": 2, "a": 1})
        assert d1 == d2  # order-independent

"""Append-only audit trail with hash-chain integrity.

Architecture reference: ARCHITECTURE-for-agents.md §10 (logical audit model)
and §14 (security). Every mutation produces a semantic event in the same
transaction. Events form a hash chain for tamper detection.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def compute_event_hash(
    previous_hash: str,
    timestamp: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    payload_digest: str,
) -> str:
    """Compute the SHA-256 hash for an audit event in the chain."""
    data = f"{previous_hash}:{timestamp}:{actor_id}:{action}:{resource_type}:{resource_id}:{payload_digest}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_payload_digest(payload: dict[str, Any]) -> str:
    """Compute a deterministic digest of the event payload."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditEvent:
    """A single immutable audit event."""

    __slots__ = (
        "event_id",
        "sequence",
        "previous_hash",
        "hash",
        "timestamp",
        "actor_id",
        "action",
        "resource_type",
        "resource_id",
        "site_id",
        "workspace_id",
        "operation_id",
        "payload_digest",
    )

    def __init__(
        self,
        *,
        sequence: int,
        previous_hash: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        site_id: UUID | None = None,
        workspace_id: UUID | None = None,
        operation_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.sequence = sequence
        self.previous_hash = previous_hash
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.actor_id = actor_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.site_id = site_id
        self.workspace_id = workspace_id
        self.operation_id = operation_id
        self.payload_digest = compute_payload_digest(payload or {})
        self.hash = compute_event_hash(
            previous_hash=previous_hash,
            timestamp=self.timestamp,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload_digest=self.payload_digest,
        )
        import uuid

        self.event_id = uuid.uuid5(uuid.NAMESPACE_OID, self.hash)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "sequence": self.sequence,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "payload_digest": self.payload_digest,
        }

"""Idempotency key management for safe mutation retries.

Architecture reference: ARCHITECTURE-for-agents.md §6 (every mutation
requires Idempotency-Key). Same key + same payload returns stored result;
same key + different payload returns 409 IDEMPOTENCY_MISMATCH.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_request_digest(payload: dict[str, Any]) -> str:
    """Compute a deterministic digest of the request payload."""
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class IdempotencyRecord:
    """Stores the result of a previously executed operation."""

    __slots__ = ("key", "digest", "operation_id", "status", "response_body")

    def __init__(
        self,
        *,
        key: str,
        digest: str,
        operation_id: str,
        status: int,
        response_body: dict[str, Any],
    ) -> None:
        self.key = key
        self.digest = digest
        self.operation_id = operation_id
        self.status = status
        self.response_body = response_body


class IdempotencyMismatchError(Exception):
    """Raised when same key is used with different payload."""


class IdempotencyStore:
    """In-memory idempotency store. Production should use PostgreSQL."""

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    async def get(self, key: str, payload_digest: str) -> IdempotencyRecord | None:
        """Return the stored record if digest matches; raise on mismatch."""
        record = self._records.get(key)
        if record is None:
            return None
        if record.digest != payload_digest:
            raise IdempotencyMismatchError(
                f"same key used with different payload: {key}"
            )
        return record

    async def put(self, record: IdempotencyRecord) -> None:
        """Store an idempotency record."""
        self._records[record.key] = record

    def clear(self) -> None:
        """Clear all records (for testing)."""
        self._records.clear()

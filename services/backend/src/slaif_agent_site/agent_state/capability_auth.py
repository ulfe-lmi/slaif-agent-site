"""Shared, bounded capability-token lookup for trusted server processes."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from .capability import (
    compute_digest,
    constant_time_digest_compare,
    validate_token_format,
)

CAPABILITY_AUTHENTICATION_SQL = """
SELECT capability.id, capability.public_id, capability.secret_digest,
       workspace.id AS workspace_id, workspace.site_id,
       workspace.created_by, capability.scopes, capability.created_at,
       capability.expires_at, capability.revoked_at
FROM control.capability AS capability
JOIN control.workspace AS workspace ON workspace.id = capability.workspace_id
WHERE capability.public_id = $1
  AND capability.revoked_at IS NULL
  AND capability.expires_at > CURRENT_TIMESTAMP
"""


class CapabilityAuthenticationUnavailableError(RuntimeError):
    """The bounded capability lookup could not reach its database pool."""


@dataclass(frozen=True, slots=True)
class CapabilityAuthenticationRecord:
    capability_id: UUID
    site_id: UUID
    workspace_id: UUID
    delegator_id: UUID
    scopes: frozenset[str]
    created_at: datetime
    expires_at: datetime


async def authenticate_capability(
    pool: Any,
    *,
    acquire_timeout: float,
    auth_header: str,
) -> CapabilityAuthenticationRecord | None:
    """Validate one capability through a caller-owned, bounded pool."""

    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ")
    if not validate_token_format(token):
        return None
    _prefix, public_id, _secret = token.split("_", maxsplit=2)
    try:
        async with pool.acquire(timeout=acquire_timeout) as connection:
            row = await connection.fetchrow(CAPABILITY_AUTHENTICATION_SQL, public_id)
    except asyncio.CancelledError:
        raise
    except Exception:
        raise CapabilityAuthenticationUnavailableError() from None
    if row is None:
        return None
    try:
        presented_digest = compute_digest(token)
        stored_digest = row["secret_digest"]
        if isinstance(stored_digest, bytes):
            stored_digest = stored_digest.hex()
        if not isinstance(stored_digest, str) or not constant_time_digest_compare(
            presented_digest, stored_digest
        ):
            return None
        if row["revoked_at"] is not None:
            return None
        expires_at = row["expires_at"]
        if (
            not isinstance(expires_at, datetime)
            or expires_at.tzinfo is None
            or expires_at <= datetime.now(UTC)
        ):
            return None
        scopes_value = row["scopes"]
        scopes = (
            json.loads(scopes_value) if isinstance(scopes_value, str) else scopes_value
        )
        if not isinstance(scopes, list) or not all(
            isinstance(scope, str) for scope in scopes
        ):
            return None
        return CapabilityAuthenticationRecord(
            capability_id=row["id"],
            site_id=row["site_id"],
            workspace_id=row["workspace_id"],
            delegator_id=row["created_by"],
            scopes=frozenset(scopes),
            created_at=row["created_at"],
            expires_at=expires_at,
        )
    except (KeyError, TypeError, ValueError):
        return None


__all__ = [
    "CAPABILITY_AUTHENTICATION_SQL",
    "CapabilityAuthenticationRecord",
    "CapabilityAuthenticationUnavailableError",
    "authenticate_capability",
]

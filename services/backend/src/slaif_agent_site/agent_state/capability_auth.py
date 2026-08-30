"""Shared, bounded capability-token lookup for trusted server processes."""

# ruff: noqa: E501 -- fixed SQL remains inspectable

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import ValidationError

from ..browser_contracts import BrowserCapabilityLimits
from .capability import (
    compute_digest,
    constant_time_digest_compare,
    validate_token_format,
)

CAPABILITY_AUTHENTICATION_SQL = """
SELECT * FROM control.slaif_agent_capability_context($1)
"""

CONTROL_CAPABILITY_AUTHENTICATION_SQL = CAPABILITY_AUTHENTICATION_SQL


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
    browser_limits: BrowserCapabilityLimits
    resource_constraints: dict[str, Any]
    source_origins: tuple[str, ...]
    request_quota: int
    mutation_quota: int
    delete_quota: int
    upload_quota: int
    request_used: int
    mutation_used: int
    delete_used: int
    upload_used: int


async def authenticate_capability(
    pool: Any,
    *,
    acquire_timeout: float,
    auth_header: str,
    query: str = CAPABILITY_AUTHENTICATION_SQL,
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
            row = await connection.fetchrow(query, public_id)
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
        targets_value = row["browser_allowed_targets"]
        if not isinstance(targets_value, (list, tuple)):
            return None
        browser_limits = BrowserCapabilityLimits.model_validate(
            {
                "max_runs": row["browser_max_runs"],
                "max_concurrent_runs": row["browser_max_concurrent_runs"],
                "max_screenshots": row["browser_max_screenshots"],
                "max_artifact_bytes": row["browser_max_artifact_bytes"],
                "max_routes_per_run": row["browser_max_routes_per_run"],
                "max_evidence_per_run": row["browser_max_evidence_per_run"],
                "max_duration_seconds": row["browser_max_duration_seconds"],
                "max_attempts": row["browser_max_attempts"],
                "allowed_targets": targets_value,
            }
        )
        constraints_value = row["resource_constraints"]
        if isinstance(constraints_value, str):
            constraints_value = json.loads(constraints_value)
        if not isinstance(constraints_value, dict):
            return None
        origins_value = row["source_origins"]
        if not isinstance(origins_value, (list, tuple)) or not all(
            isinstance(origin, str) for origin in origins_value
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
            browser_limits=browser_limits,
            resource_constraints=constraints_value,
            source_origins=tuple(origins_value),
            request_quota=row["request_quota"],
            mutation_quota=row["mutation_quota"],
            delete_quota=row["delete_quota"],
            upload_quota=row["upload_quota"],
            request_used=row["request_used"],
            mutation_used=row["mutation_used"],
            delete_used=row["delete_used"],
            upload_used=row["upload_used"],
        )
    except (KeyError, TypeError, ValidationError, ValueError):
        return None


__all__ = [
    "CAPABILITY_AUTHENTICATION_SQL",
    "CONTROL_CAPABILITY_AUTHENTICATION_SQL",
    "CapabilityAuthenticationRecord",
    "CapabilityAuthenticationUnavailableError",
    "authenticate_capability",
]

"""The reviewed-operations/v1 companion manifest builder (083/12).

The freeze worker assembles the companion envelope from the actual
public foundation session state captured in the SAME locked freeze
transaction: the full operation universe U (the public
``get_session_operations`` getter), the actual public foundation
dependency pairs (explicitly foundation dependencies, not product
semantic causality), and the bounded trusted 078 completion
identities of exactly U (the narrow owner-only journal projection).

The envelope is serialized in the exact canonical content form the
trusted completion function stores (U sorted, dependency pairs unique
+ sorted by both endpoints, identities sorted by operation), and the
server recomputes the manifest digest over that stored content plus
the stored snapshot binding.  This module performs the same
fail-closed shape validation so a malformed capture never reaches the
database as an untyped raw error; the database keeps its own
independent validation (the Python check is not the security
boundary).

Every U member carries exactly one verified provenance record:

* the nine-field 078 trusted completion identity (public mutation
  operations), or
* the three-field trusted-internal record (operation_id,
  resource_types, disposition ``trusted_internal``) for operations
  whose surviving COW change rows are confined to the
  trusted-internal (non-mutation) tables - workspace state written
  only by trusted control definers, which carries no 078 completion.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

MANIFEST_SCHEMA_VERSION = "reviewed-operations/v1"

# The exact nine trusted 078 completion identity fields (the narrow
# owner projection, string-typed end to end).
_IDENTITY_KEYS = frozenset(
    {
        "operation_id",
        "family",
        "principal_type",
        "principal_id",
        "request_identity",
        "request_digest",
        "resource_type",
        "resource_id",
        "disposition",
    }
)
# The typed trusted-internal provenance record (083/12): one per U
# member whose surviving COW change rows are confined to the
# trusted-internal (non-mutation) tables.  Must match the 079
# migration's trusted-internal table set and shape guards.
_INTERNAL_IDENTITY_KEYS = frozenset({"operation_id", "resource_types", "disposition"})
_INTERNAL_DISPOSITION = "trusted_internal"
_TRUSTED_INTERNAL_COW_TABLES = ("proposed_side_effect",)


class SnapshotManifestError(ValueError):
    """A bounded companion-manifest build failure with a stable code."""

    def __init__(self, code: str, *, reason: str = "") -> None:
        super().__init__(f"{code}:{reason}" if reason else code)
        self.code = code
        self.reason = reason


def _canonical_uuid(value: Any, *, field: str, code: str) -> str:
    """Lowercase canonical UUID text; anything else is a typed refusal."""

    if isinstance(value, UUID):
        return str(value)
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise SnapshotManifestError(code, reason=field) from None


def _identity_field(identity: dict[str, Any], key: str) -> str:
    value = identity[key]
    if not isinstance(value, str):
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason=key)
    return value


def _internal_identity_record(identity: dict[str, Any]) -> dict[str, Any]:
    """Validate/canonicalize one trusted-internal provenance record."""
    operation_text = identity["operation_id"]
    if not isinstance(operation_text, str):
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="operation_id")
    resource_types = identity["resource_types"]
    if (
        not isinstance(resource_types, list)
        or len(resource_types) != 1
        or not all(isinstance(table, str) for table in resource_types)
        or set(resource_types) != set(_TRUSTED_INTERNAL_COW_TABLES)
    ):
        raise SnapshotManifestError(
            "MANIFEST_IDENTITY_INVALID", reason="resource_types"
        )
    if identity["disposition"] != _INTERNAL_DISPOSITION:
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="disposition")
    return {
        "operation_id": operation_text,
        "resource_types": sorted(resource_types),
        "disposition": _INTERNAL_DISPOSITION,
    }


def build_operation_manifest(
    *,
    workspace_id: UUID,
    site_id: UUID,
    operations: list[UUID],
    dependencies: list[tuple[UUID, UUID]],
    completion_identities: list[dict[str, Any]],
) -> str:
    """Serialize the reviewed-operations/v1 companion envelope.

    Fail-closed, ordered checks (mirroring the trusted completion
    function's server-side guards): every operation is a canonical
    lowercase UUID string with duplicates refusing before any set
    conversion; every dependency is a two-endpoint UUID pair with both
    endpoints in U; the provenance records are exactly one of the two
    trusted forms (nine-field 078 completion identity, or three-field
    trusted-internal record), string-typed, one per operation,
    covering U exactly.  The returned JSON is the compact sorted-key
    form; the stored arrays are canonically ordered (U sorted, pairs
    unique + sorted, identities sorted by operation).
    """

    seen: set[str] = set()
    operation_ids: list[str] = []
    for operation in operations:
        text = _canonical_uuid(
            operation, field="operation", code="MANIFEST_OPERATION_INVALID"
        )
        if text in seen:
            raise SnapshotManifestError("MANIFEST_DUPLICATE_OPERATION", reason=text)
        seen.add(text)
        operation_ids.append(text)
    operation_ids.sort()
    operation_set = frozenset(operation_ids)

    pairs: set[tuple[str, str]] = set()
    for depends_on, operation_id in dependencies:
        start = _canonical_uuid(
            depends_on, field="depends_on", code="MANIFEST_DEPENDENCY_INVALID"
        )
        end = _canonical_uuid(
            operation_id, field="operation_id", code="MANIFEST_DEPENDENCY_INVALID"
        )
        if start not in operation_set or end not in operation_set:
            raise SnapshotManifestError(
                "MANIFEST_DEPENDENCY_ENDPOINT", reason=f"{start}->{end}"
            )
        pairs.add((start, end))

    identities: list[dict[str, Any]] = []
    identity_operations: set[str] = set()
    for identity in completion_identities:
        if not isinstance(identity, dict):
            raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID")
        if set(identity) == _IDENTITY_KEYS:
            canonical: dict[str, Any] = {
                key: _identity_field(identity, key) for key in _IDENTITY_KEYS
            }
        elif set(identity) == _INTERNAL_IDENTITY_KEYS:
            canonical = _internal_identity_record(identity)
        else:
            raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID")
        operation_text = canonical["operation_id"]
        if operation_text != _canonical_uuid(
            operation_text,
            field="operation_id",
            code="MANIFEST_IDENTITY_INVALID",
        ):
            # The journal projection emits canonical lowercase UUID
            # text; any other shape is not a trusted identity.
            raise SnapshotManifestError(
                "MANIFEST_IDENTITY_INVALID", reason="operation_id"
            )
        if operation_text in identity_operations:
            raise SnapshotManifestError(
                "MANIFEST_DUPLICATE_OPERATION", reason=operation_text
            )
        identity_operations.add(operation_text)
        identities.append(canonical)
    identities.sort(key=lambda item: item["operation_id"])
    if len(identities) != len(operation_ids) or identity_operations != operation_set:
        raise SnapshotManifestError("MANIFEST_IDENTITY_MISMATCH")

    envelope = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "site_id": str(site_id),
        "workspace_id": str(workspace_id),
        "operation_ids": operation_ids,
        "dependency_pairs": [list(pair) for pair in sorted(pairs)],
        "completion_identities": identities,
    }
    return json.dumps(envelope, sort_keys=True, separators=(",", ":"))


__all__ = [
    "MANIFEST_SCHEMA_VERSION",
    "SnapshotManifestError",
    "build_operation_manifest",
]

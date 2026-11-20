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

* the nine-field 078 trusted completion identity (ordinary Agent,
  HUMAN Editor and Media mutation operations), or
* the versioned proposed-effect/v1 trusted producer record for the
  Control-only proposed-side-effect producer - a product-owned
  prospective completion record the real trusted constructor wrote
  in the SAME transaction as its COW insert (operation, constant
  producer, service principal, exact sorted resource ids), never
  inferred from private COW storage.
"""

from __future__ import annotations

import json
import re
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
# The versioned trusted producer record (083/12-b): one per U member
# created by the trusted Control-only proposed-side-effect producer.
# Must match the 079 migration's proposed_effect_completion contract
# and shape guards.
_PRODUCER_RECORD_VERSION = "proposed-effect/v1"
_PRODUCER_CONST = "slaif_proposed_side_effect_create"
_PRODUCER_PRINCIPAL_TYPE = "service"
_PRODUCER_PRINCIPAL_SHAPE_RE = re.compile(r"^[A-Za-z0-9_$]{1,64}$")
_MAX_PRODUCER_RESOURCES = 1024
_PRODUCER_RECORD_KEYS = frozenset(
    {
        "operation_id",
        "record_version",
        "producer",
        "principal_type",
        "principal_id",
        "resource_ids",
    }
)


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


def _producer_identity_record(identity: dict[str, Any]) -> dict[str, Any]:
    """Validate/canonicalize one versioned trusted producer record."""
    operation_text = identity["operation_id"]
    if not isinstance(operation_text, str):
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="operation_id")
    if identity["record_version"] != _PRODUCER_RECORD_VERSION:
        raise SnapshotManifestError(
            "MANIFEST_IDENTITY_INVALID", reason="record_version"
        )
    if identity["producer"] != _PRODUCER_CONST:
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="producer")
    if identity["principal_type"] != _PRODUCER_PRINCIPAL_TYPE:
        raise SnapshotManifestError(
            "MANIFEST_IDENTITY_INVALID", reason="principal_type"
        )
    principal_id = identity["principal_id"]
    if (
        not isinstance(principal_id, str)
        or _PRODUCER_PRINCIPAL_SHAPE_RE.fullmatch(principal_id) is None
    ):
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="principal_id")
    resource_ids = identity["resource_ids"]
    if (
        not isinstance(resource_ids, list)
        or not 1 <= len(resource_ids) <= _MAX_PRODUCER_RESOURCES
        or len(set(resource_ids)) != len(resource_ids)
    ):
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="resource_ids")
    canonical_resources: list[str] = []
    for resource in resource_ids:
        if not isinstance(resource, str):
            raise SnapshotManifestError(
                "MANIFEST_IDENTITY_INVALID", reason="resource_ids"
            )
        canonical = _canonical_uuid(
            resource, field="resource_id", code="MANIFEST_IDENTITY_INVALID"
        )
        if canonical != resource:
            raise SnapshotManifestError(
                "MANIFEST_IDENTITY_INVALID", reason="resource_ids"
            )
        canonical_resources.append(canonical)
    if canonical_resources != sorted(canonical_resources):
        # The worker projection emits the exact stored (sorted) array;
        # any other order is not the trusted canonical form.
        raise SnapshotManifestError("MANIFEST_IDENTITY_INVALID", reason="resource_ids")
    return {
        "operation_id": operation_text,
        "record_version": _PRODUCER_RECORD_VERSION,
        "producer": _PRODUCER_CONST,
        "principal_type": _PRODUCER_PRINCIPAL_TYPE,
        "principal_id": principal_id,
        "resource_ids": canonical_resources,
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
        elif set(identity) == _PRODUCER_RECORD_KEYS:
            canonical = _producer_identity_record(identity)
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

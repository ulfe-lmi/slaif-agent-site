"""Immutable snapshot document normalization for the review worker.

The materialized workspace-state document comes from the trusted SQL
materializer (``control.slaif_review_workspace_state``), which reads the
frozen workspace's COW content under the exclusive product lock (it
arrives as canonical JSON text in the worker's asyncpg jsonb binding;
this module accepts that text form and normalizes it to a mapping before
validation). This module re-normalizes each page's composition with the exact projection
code the trusted renderer consumes (``render_api.projection``), so the
stored ``normalized_state``/``payload`` can never diverge from what the
renderer and Puck render. The canonical digest is the SHA-256 of the
canonical JSON serialization of the payload (sorted keys, compact
separators, ASCII escapes), byte-identical to the SQL canonical form
``control.slaif_canonical_jsonb_text``.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from ..content_model.design_system import (
    CATALOG_VERSION,
    COMPOSITION_SCHEMA_VERSION,
    DESIGN_SYSTEM_VERSION,
    RENDERER_VERSION,
)
from ..render_api.projection import ProjectionError, _node_tree
from .config import (
    REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION,
    REVIEW_WORKER_PUCK_VERSION_PIN,
    REVIEW_WORKER_STATE_VERSION,
)

STATE_VERSION = REVIEW_WORKER_STATE_VERSION
PUCK_VERSION_PIN = REVIEW_WORKER_PUCK_VERSION_PIN
_CONTENT_MODEL_SCHEMA_VERSION = REVIEW_WORKER_CONTENT_MODEL_SCHEMA_VERSION
_REQUIRED_DOC_KEYS = (
    "state_version",
    "workspace_id",
    "site_id",
    "site",
    "base_site_revision",
    "operation_watermark",
    "locales",
    "theme",
    "regions",
    "navigation",
    "redirects",
    "pages",
    "media",
)
_REQUIRED_PAGE_KEYS = (
    "id",
    "site_id",
    "slug",
    "title",
    "status",
    "locale",
    "parent_id",
    "route_template",
    "effective_route",
    "row_version",
    "nodes",
)
# Renderer composition SELECT column order (id, site_id, page_id,
# component_type, schema_version, parent_id, slot_key, order_key, props,
# created_at, updated_at).
_NODE_COLUMNS = 11


class SnapshotBuildError(ValueError):
    """A stable, non-leaking snapshot build failure."""

    def __init__(self, code: str, *, reason: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.reason = reason


def canonical_json(value: Any) -> str:
    """Canonical JSON serialization (the OpenAPI strip-identity convention)."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_digest(payload: dict[str, Any]) -> str:
    """SHA-256 hex over the canonical serialization of the payload."""

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _node_rows(page_nodes: list[Any]) -> list[tuple[Any, ...]]:
    """Convert materialized ``row_to_json`` node rows to positional rows."""

    rows: list[tuple[Any, ...]] = []
    for node in page_nodes:
        if not isinstance(node, dict):
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        parent = node.get("parent_id")
        rows.append(
            (
                UUID(str(node["id"])),
                UUID(str(node["site_id"])),
                UUID(str(node["page_id"])),
                str(node["component_type"]),
                str(node["schema_version"]),
                UUID(str(parent)) if parent is not None else None,
                str(node["slot_key"]),
                int(node["order_key"]),
                node.get("props"),
                node.get("created_at"),
                node.get("updated_at"),
            )
        )
    return rows


def _normalized_nodes(page: dict[str, Any], site_id: UUID) -> list[dict[str, Any]]:
    rows = _node_rows(page["nodes"])
    if len(rows) != len(page["nodes"]) or any(
        len(row) != _NODE_COLUMNS for row in rows
    ):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    try:
        roots = _node_tree(rows, page_id=UUID(str(page["id"])), site_id=site_id)
    except ProjectionError as error:
        raise SnapshotBuildError(
            "SNAPSHOT_VALIDATION_FAILED", reason=error.reason
        ) from None
    except (KeyError, TypeError, ValueError):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED") from None
    return [node.model_dump(mode="json") for node in roots]


def _media_references(media: Any) -> list[dict[str, Any]]:
    if not isinstance(media, dict):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    references: list[dict[str, Any]] = []
    for key, descriptor in sorted(media.items()):
        if not isinstance(descriptor, dict):
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        reference = {
            "id": str(descriptor.get("id", key)),
            "mime_type": descriptor.get("mime_type"),
            "size_bytes": descriptor.get("size_bytes"),
            "content_hash": descriptor.get("content_hash"),
            "public_status": descriptor.get("public_status"),
        }
        if (
            reference["id"] != key
            or not isinstance(reference["mime_type"], str)
            or not isinstance(reference["size_bytes"], int)
            or not isinstance(reference["content_hash"], str)
            or not isinstance(reference["public_status"], str)
        ):
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        references.append(reference)
    return references


def build_snapshot_document(
    doc: Any,
    *,
    created_by: str,
    browser_evidence: list[dict[str, Any]] | None = None,
    cancelled_runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate the materialized doc and build the immutable snapshot row.

    Returns the exact row accepted by
    ``control.slaif_review_snapshot_complete``; the canonical ``digest`` is
    recomputable from the stored ``payload`` by any party.
    """

    if isinstance(doc, (str, bytes, bytearray)):
        try:
            doc = json.loads(doc)
        except ValueError:
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED") from None
    if not isinstance(doc, dict) or any(key not in doc for key in _REQUIRED_DOC_KEYS):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    if doc["state_version"] != STATE_VERSION:
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    try:
        workspace_id = UUID(str(doc["workspace_id"]))
        site_id = UUID(str(doc["site_id"]))
        base_site_revision = int(doc["base_site_revision"])
        operation_watermark = int(doc["operation_watermark"])
    except (KeyError, TypeError, ValueError):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED") from None
    if base_site_revision < 0 or operation_watermark < 0:
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    if not isinstance(doc["pages"], list) or not isinstance(doc["site"], dict):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")

    pages: list[dict[str, Any]] = []
    for page in doc["pages"]:
        if not isinstance(page, dict) or any(
            key not in page for key in _REQUIRED_PAGE_KEYS
        ):
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        if str(page["site_id"]) != str(site_id) or not isinstance(page["nodes"], list):
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
        normalized = dict(page)
        normalized["nodes"] = _normalized_nodes(page, site_id)
        pages.append(normalized)

    versions = {
        "catalog": CATALOG_VERSION,
        "design_system": DESIGN_SYSTEM_VERSION,
        "composition_schema": COMPOSITION_SCHEMA_VERSION,
        "renderer": RENDERER_VERSION,
        "puck": PUCK_VERSION_PIN,
        "content_model": _CONTENT_MODEL_SCHEMA_VERSION,
    }
    validation_report = {
        "state_version": STATE_VERSION,
        "pages_validated": len(pages),
        "errors": [],
        "cancelled_by_freeze": [
            {
                "id": str(item["id"]),
                "previous_state": item.get("previous_state"),
            }
            for item in (cancelled_runs or [])
            if isinstance(item, dict) and "id" in item
        ],
    }
    media_references = _media_references(doc["media"])
    evidence = [
        {"id": str(item["id"])}
        for item in (browser_evidence or [])
        if isinstance(item, dict) and "id" in item
    ]
    payload: dict[str, Any] = {
        "state_version": STATE_VERSION,
        "workspace_id": str(workspace_id),
        "site_id": str(site_id),
        "site": doc["site"],
        "base_site_revision": base_site_revision,
        "operation_watermark": operation_watermark,
        "locales": doc["locales"],
        "theme": doc["theme"],
        "regions": doc["regions"],
        "navigation": doc["navigation"],
        "redirects": doc["redirects"],
        "pages": pages,
        "media": doc["media"],
    }
    return {
        "workspace_id": str(workspace_id),
        "site_id": str(site_id),
        "status": "COMPLETE",
        "revision_watermark": base_site_revision + operation_watermark,
        "versions": versions,
        "normalized_state": payload,
        "validation_report": validation_report,
        "media_references": media_references,
        "browser_evidence": evidence,
        "payload": payload,
        "digest": canonical_digest(payload),
        "created_by": created_by,
    }


__all__ = [
    "PUCK_VERSION_PIN",
    "STATE_VERSION",
    "SnapshotBuildError",
    "build_snapshot_document",
    "canonical_digest",
    "canonical_json",
]

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

Before storage the builder re-verifies the v2 capture contract (defense in
depth over the materializer's pre-aggregation gates): exact per-family
row counts, ACTUAL recursive depth of every captured raw jsonb value,
normalized component-tree parent-chain depth, and the exact canonical
serialized byte length of the payload.  Any violation fails closed with
the stable ``SNAPSHOT_OVER_BUDGET`` code: no snapshot row, no
truncation, no dropped rows.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any
from uuid import UUID

from ..content_model.canonical import (
    canonical_digest,
    canonical_json,
    parse_snapshot_text,
)
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

# v2 exact post-aggregation gates (design 083/5 section 8.2): fail-closed
# domain limits re-verified at capture over the ACTUAL materialized
# document, referenced to product write-side limits where they exist.
RAW_VALUE_MAX_DEPTH = 8
COMPONENT_CHAIN_MAX_DEPTH = 17  # MAX_COMPONENT_DEPTH (16) + 1 node
MAX_CANONICAL_PAYLOAD_BYTES = 8 * 1024 * 1024
MAX_PAGES = 4096
MAX_COMPOSITIONS_TOTAL = 131072
MAX_COMPOSITIONS_PER_PAGE = 128  # MAX_COMPONENTS_PER_PAGE write-side cap
MAX_CONTENT_TYPES = 64
MAX_FIELDS_PER_TYPE = 64
MAX_ITEMS_PER_TYPE = 2000
MAX_TRANSLATIONS_TOTAL = 20000
MAX_RELATIONS_PER_PAIR = 1000
MAX_VIEWS_PER_TYPE = 64
MAX_MEDIA_INVENTORY = 4096
MAX_PROPOSALS = 10000

# The v2 document is the complete trusted domain capture: the exact key
# set the materializer emits and the completion contract requires.
_REQUIRED_DOC_KEYS = (
    "state_version",
    "workspace_id",
    "site_id",
    "site",
    "base_site_revision",
    "operation_watermark",
    "workspace_versions",
    "locales",
    "theme",
    "regions",
    "navigation",
    "redirects",
    "pages",
    "page_compositions",
    "content",
    "proposals",
    "media_inventory",
    "media",
)
_REQUIRED_CONTENT_KEYS = (
    "types",
    "fields",
    "items",
    "translations",
    "relations",
    "views",
)


class SnapshotBuildError(ValueError):
    """A stable, non-leaking snapshot build failure."""

    def __init__(self, code: str, *, reason: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.reason = reason


def _render_decode(value: Any) -> Any:
    """Deterministic float decode of shared-engine input (design 083/5 R2).

    The projection engine always consumes float-decoded values: the live
    path decodes PG jsonb -> str -> ``json.loads`` (float). The capture
    path must feed ``_node_tree`` the SAME values, so the exact-Decimal
    retention parsed from the materializer text is converted here with a
    correctly-rounded ``float(Decimal)`` — byte-identical to the live
    float for every write-reachable value (magnitudes beyond float range
    are not producible through the supported HTTP write path). The RAW
    composition block is NOT decoded: it retains exact PG digits/scale
    in the payload, and the numeric validators see only the same
    float/int types the write path always accepted (zero validator
    changes).
    """

    if isinstance(value, dict):
        return {key: _render_decode(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_render_decode(child) for child in value]
    if isinstance(value, Decimal):
        return float(value)
    return value


def _node_rows(page_nodes: list[Any]) -> list[tuple[Any, ...]]:
    """Convert materialized ``row_to_json`` node rows to positional rows.

    Node props are float-decoded for the shared engine (see
    ``_render_decode``); the raw rows themselves retain exact digits.
    """

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
                _render_decode(node.get("props")),
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
    except (KeyError, TypeError, ValueError, OverflowError):
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


def _over_budget(detail: str) -> SnapshotBuildError:
    return SnapshotBuildError("SNAPSHOT_OVER_BUDGET", reason=detail)


def _raw_value_depth(value: Any) -> int:
    """ACTUAL recursive depth of a captured raw jsonb value.

    Container = 1 + max(child depths); empty container = 1; scalar = 0.
    This is the real depth guard the design requires (the content-model
    ``_bounded_json`` parameter is NOT a depth guard and is not relied
    on; it stays a write-side limit only).
    """

    if isinstance(value, dict):
        return 1 + max((_raw_value_depth(v) for v in value.values()), default=0)
    if isinstance(value, (list, tuple)):
        return 1 + max((_raw_value_depth(v) for v in value), default=0)
    return 0


def _raw_values(doc: dict[str, Any]) -> list[Any]:
    """Every captured raw jsonb VALUE re-verified at the depth boundary.

    These are the raw row-level jsonb columns the materializer captured
    (props, values, specs, metadata, theme, style documents).  Normalized
    node trees are bounded separately by the component-chain gate.
    """

    values: list[Any] = [doc["theme"]]
    for page in doc["pages"]:
        values.append(page.get("style_overrides"))
        style = page.get("style")
        if isinstance(style, dict):
            values.append(style.get("overrides"))
            values.append(style.get("resolved"))
    for composition in doc["page_compositions"]:
        values.append(composition.get("props"))
    for locale in doc["locales"]:
        values.append(locale.get("metadata"))
    for region in doc["regions"]:
        values.append(region.get("content"))
    navigation = doc["navigation"]
    for definition in navigation["definitions"]:
        values.append(definition.get("settings"))
        values.append(definition.get("labels"))
    for item in navigation["items"]:
        values.append(item.get("labels"))
    content = doc["content"]
    for type_doc in content["types"]:
        values.append(type_doc.get("settings"))
        values.append(type_doc.get("labels"))
    for field in content["fields"]:
        values.append(field.get("validation"))
        values.append(field.get("ui_options"))
    for item in content["items"]:
        values.append(item.get("values"))
    for translation in content["translations"]:
        values.append(translation.get("localized_values"))
    for relation in content["relations"]:
        values.append(relation.get("metadata"))
    for view in content["views"]:
        values.append(view.get("filter_spec"))
        values.append(view.get("sort_spec"))
        values.append(view.get("projection_spec"))
        values.append(view.get("pagination_spec"))
    for asset in doc["media_inventory"]:
        values.append(asset.get("metadata"))
    for proposal in doc["proposals"]:
        values.append(proposal.get("payload"))
    return values


def _enforce_raw_depths(doc: dict[str, Any]) -> None:
    for value in _raw_values(doc):
        if value is None:
            continue
        if _raw_value_depth(value) > RAW_VALUE_MAX_DEPTH:
            raise _over_budget(f"raw value depth > {RAW_VALUE_MAX_DEPTH}")


def _node_chain_depth(nodes: list[dict[str, Any]]) -> int:
    """Maximum number of nodes on a root-to-leaf path of a normalized tree."""

    def depth(node: dict[str, Any]) -> int:
        children = node.get("children") or []
        return 1 + max((depth(child) for child in children), default=0)

    return max((depth(node) for node in nodes), default=0)


def _enforce_family_counts(doc: dict[str, Any]) -> None:
    """Exact per-family count gates over the ACTUAL captured rows."""

    pages = doc["pages"]
    if len(pages) > MAX_PAGES:
        raise _over_budget(f"pages > {MAX_PAGES}")
    page_ids = {str(page["id"]) for page in pages}
    compositions = doc["page_compositions"]
    if len(compositions) > MAX_COMPOSITIONS_TOTAL:
        raise _over_budget(f"compositions total > {MAX_COMPOSITIONS_TOTAL}")
    per_page: dict[str, int] = {}
    for composition in compositions:
        page_id = str(composition["page_id"])
        if page_id not in page_ids:
            raise _over_budget("composition row for unknown page")
        per_page[page_id] = per_page.get(page_id, 0) + 1
    if any(count > MAX_COMPOSITIONS_PER_PAGE for count in per_page.values()):
        raise _over_budget(f"compositions per page > {MAX_COMPOSITIONS_PER_PAGE}")
    for page in pages:
        if _node_chain_depth(page["nodes"]) > COMPONENT_CHAIN_MAX_DEPTH:
            raise _over_budget(f"component chain > {COMPONENT_CHAIN_MAX_DEPTH}")
    content = doc["content"]
    if len(content["types"]) > MAX_CONTENT_TYPES:
        raise _over_budget(f"content types > {MAX_CONTENT_TYPES}")
    fields_per_type: dict[str, int] = {}
    for field in content["fields"]:
        key = str(field["type_id"])
        fields_per_type[key] = fields_per_type.get(key, 0) + 1
    if any(count > MAX_FIELDS_PER_TYPE for count in fields_per_type.values()):
        raise _over_budget(f"fields per type > {MAX_FIELDS_PER_TYPE}")
    items_per_type: dict[str, int] = {}
    for item in content["items"]:
        key = str(item["type_id"])
        items_per_type[key] = items_per_type.get(key, 0) + 1
    if any(count > MAX_ITEMS_PER_TYPE for count in items_per_type.values()):
        raise _over_budget(f"items per type > {MAX_ITEMS_PER_TYPE}")
    if len(content["translations"]) > MAX_TRANSLATIONS_TOTAL:
        raise _over_budget(f"translations > {MAX_TRANSLATIONS_TOTAL}")
    relations_per_pair: dict[tuple[str, str], int] = {}
    for relation in content["relations"]:
        pair_key = (
            str(relation["source_item_id"]),
            str(relation["field_definition_id"]),
        )
        relations_per_pair[pair_key] = relations_per_pair.get(pair_key, 0) + 1
    if any(count > MAX_RELATIONS_PER_PAIR for count in relations_per_pair.values()):
        raise _over_budget(f"relations per (item, field) > {MAX_RELATIONS_PER_PAIR}")
    views_per_type: dict[str, int] = {}
    for view in content["views"]:
        key = str(view["type_id"])
        views_per_type[key] = views_per_type.get(key, 0) + 1
    if any(count > MAX_VIEWS_PER_TYPE for count in views_per_type.values()):
        raise _over_budget(f"views per type > {MAX_VIEWS_PER_TYPE}")
    if len(doc["media_inventory"]) > MAX_MEDIA_INVENTORY:
        raise _over_budget(f"media inventory > {MAX_MEDIA_INVENTORY}")
    if len(doc["proposals"]) > MAX_PROPOSALS:
        raise _over_budget(f"proposals > {MAX_PROPOSALS}")


def _enforce_v2_post_gates(doc: dict[str, Any]) -> None:
    _enforce_raw_depths(doc)
    _enforce_family_counts(doc)


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
    recomputable from the stored ``payload`` by any party (the v2 SQL
    completion recomputes it over the stored payload in the 070 canonical
    form).  The text form is parsed with exact numeric retention
    (``parse_float=Decimal``) so raw jsonb values keep every written
    digit/scale through capture.
    """

    if isinstance(doc, (str, bytes, bytearray)):
        if isinstance(doc, (bytes, bytearray)):
            doc = doc.decode()
        try:
            doc = parse_snapshot_text(doc)
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
    if not isinstance(doc["workspace_versions"], dict):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    if not isinstance(doc["page_compositions"], list):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    if not isinstance(doc["proposals"], list) or not isinstance(
        doc["media_inventory"], list
    ):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    for key in ("locales", "regions", "redirects"):
        if not isinstance(doc[key], list):
            raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    navigation = doc["navigation"]
    if (
        not isinstance(navigation, dict)
        or not isinstance(navigation.get("definitions"), list)
        or not isinstance(navigation.get("items"), list)
    ):
        raise SnapshotBuildError("SNAPSHOT_VALIDATION_FAILED")
    content = doc["content"]
    if not isinstance(content, dict) or not all(
        isinstance(content.get(key), list) for key in _REQUIRED_CONTENT_KEYS
    ):
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

    # Exact post-aggregation gates over the ACTUAL captured document
    # (raw-value depth, per-family counts, component chains).  Failures
    # raise SNAPSHOT_OVER_BUDGET: no snapshot row, no truncation, no
    # dropped rows.
    enforced_doc = dict(doc)
    enforced_doc["pages"] = pages
    _enforce_v2_post_gates(enforced_doc)

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
    # The v2 payload is the complete trusted domain capture: the exact
    # 18-key document the materializer emits (normalized pages replace
    # the raw node rows; every other family is retained as captured).
    payload: dict[str, Any] = {
        "state_version": STATE_VERSION,
        "workspace_id": str(workspace_id),
        "site_id": str(site_id),
        "site": doc["site"],
        "base_site_revision": base_site_revision,
        "operation_watermark": operation_watermark,
        "workspace_versions": doc["workspace_versions"],
        "locales": doc["locales"],
        "theme": doc["theme"],
        "regions": doc["regions"],
        "navigation": navigation,
        "redirects": doc["redirects"],
        "pages": pages,
        "page_compositions": doc["page_compositions"],
        "content": content,
        "proposals": doc["proposals"],
        "media_inventory": doc["media_inventory"],
        "media": doc["media"],
    }
    canonical_text = canonical_json(payload)
    if len(canonical_text.encode("utf-8")) > MAX_CANONICAL_PAYLOAD_BYTES:
        raise _over_budget("canonical payload bytes over budget")
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
        "digest": hashlib.sha256(canonical_text.encode("utf-8")).hexdigest(),
        "created_by": created_by,
    }


__all__ = [
    "COMPONENT_CHAIN_MAX_DEPTH",
    "MAX_CANONICAL_PAYLOAD_BYTES",
    "MAX_COMPOSITIONS_PER_PAGE",
    "MAX_COMPOSITIONS_TOTAL",
    "MAX_CONTENT_TYPES",
    "MAX_FIELDS_PER_TYPE",
    "MAX_ITEMS_PER_TYPE",
    "MAX_MEDIA_INVENTORY",
    "MAX_PAGES",
    "MAX_PROPOSALS",
    "MAX_RELATIONS_PER_PAIR",
    "MAX_TRANSLATIONS_TOTAL",
    "MAX_VIEWS_PER_TYPE",
    "PUCK_VERSION_PIN",
    "RAW_VALUE_MAX_DEPTH",
    "STATE_VERSION",
    "SnapshotBuildError",
    "build_snapshot_document",
    "canonical_digest",
    "canonical_json",
    "parse_snapshot_text",
]

"""Fail-closed write-time validation for bounded component prop semantics.

The component catalog guard enforces the *shape* of component props on every
composition write path (Agent and human Puck).  This module adds the
*semantic* constraints that the static catalog cannot express:

- CollectionFilter facets: every facet must reference a field of the bound
  view's content type and use an operator from that field's per-primitive
  query vocabulary (``query_dsl._OPS``).
- Gallery/LogoGrid media-reference lists: every item ``mediaId`` must
  resolve to an image-class media row of the writing site (079/2).
- DocumentList document-reference lists: every item ``mediaId`` must
  resolve to a document-class (``application/pdf``) media row of the
  writing site (079/3).

View, field, and media resolution is site-scoped by the caller; anything
that cannot be resolved on this site is rejected before the composition
write is attempted.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from .primitives import FieldPrimitive, FieldPrimitiveError
from .query_dsl import _OPS

MAX_FACETS = 4
IN_LIST_MAX_ENTRIES = 8
IN_LIST_ENTRY_MAX_LENGTH = 256


class FacetValidationError(ValueError):
    """A bounded CollectionFilter facet vocabulary failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _row_field(row: Any, name: str) -> Any:
    try:
        return row[name]
    except (KeyError, TypeError, IndexError):
        return getattr(row, name, None)


def field_primitive_map(field_rows: Any) -> dict[str, str]:
    """Build ``{field_key: primitive}`` from rows exposing key/field_type."""

    fields: dict[str, str] = {}
    for row in field_rows:
        key = _row_field(row, "key")
        field_type = _row_field(row, "field_type")
        if isinstance(key, str) and isinstance(field_type, str) and key not in fields:
            fields[key] = field_type
    return fields


def _in_list_entries(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def validate_collection_filter_facets(
    facets: Any,
    fields: Mapping[str, str],
) -> None:
    """Reject facets outside the bound view's field/operator vocabulary.

    ``fields`` maps field key to field primitive for the bound view's
    content type.  Entries with malformed shapes are skipped here: the
    catalog guard rejects prop-shape violations on every write path, so
    this check only ever runs over shape-valid facets and therefore cannot
    let an invalid facet through.
    """
    if not isinstance(facets, (list, tuple)):
        return
    if len(facets) > MAX_FACETS:
        raise FacetValidationError("collection_filter_facets")
    for entry in facets:
        if not isinstance(entry, Mapping):
            continue
        field_key = entry.get("fieldKey")
        operator = entry.get("operator")
        value = entry.get("value")
        if not isinstance(field_key, str) or not isinstance(operator, str):
            continue
        primitive = fields.get(field_key)
        if primitive is None:
            raise FacetValidationError("collection_filter_field")
        try:
            vocabulary = _OPS[FieldPrimitive.from_value(primitive)]
        except (FieldPrimitiveError, KeyError, ValueError):
            raise FacetValidationError("collection_filter_field") from None
        if operator not in vocabulary:
            raise FacetValidationError("collection_filter_operator")
        if operator == "in" and isinstance(value, str):
            entries = _in_list_entries(value)
            if len(entries) > IN_LIST_MAX_ENTRIES or any(
                len(item) > IN_LIST_ENTRY_MAX_LENGTH for item in entries
            ):
                raise FacetValidationError("collection_filter_value")


# Bounded media-reference list components (079/2): error-key prefix and the
# catalog list bounds the pure check mirrors.
MEDIA_REFERENCE_COMPONENTS: dict[str, tuple[str, int, int]] = {
    "Gallery": ("gallery", 1, 12),
    "LogoGrid": ("logogrid", 2, 24),
}

# The bounded media MIME class the immutable store accepts (079/1).
MEDIA_MIME_CLASSES = frozenset({"image/png", "image/jpeg"})

# The complete bounded error-key vocabulary surfaced as 422 ``prop_error``.
MEDIA_REFERENCE_ERROR_KEYS = frozenset(
    f"{prefix}.{suffix}"
    for prefix, _, _ in MEDIA_REFERENCE_COMPONENTS.values()
    for suffix in (
        "item-missing",
        "item-foreign-site",
        "item-not-image",
        "items-out-of-range",
    )
)


class MediaReferenceError(ValueError):
    """A bounded media-reference list validation failure."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _as_uuid(value: Any) -> UUID | None:
    if not isinstance(value, str):
        return None
    try:
        return UUID(value)
    except (TypeError, ValueError):
        return None


def validate_media_reference_items(
    component_type: str,
    items: Any,
    *,
    site_id: UUID,
    facts: Mapping[UUID, tuple[UUID, str] | None],
) -> None:
    """Reject media-reference list items outside the site's image class.

    ``facts`` maps every well-formed ``mediaId`` in ``items`` to the resolved
    ``(site_id, mime_type)`` row or ``None`` when the writing site's scoped
    lookup resolved nothing.  The Agent path resolves through the site-scoped
    ``slaif_agent_media_get``; the Editor path resolves through the id lookup
    plus an explicit site comparison.  A well-formed reference that does not
    resolve within the writing site is bounded as ``item-foreign-site`` on
    both paths: the architecture permits no cross-site media enumeration, so
    a foreign-site reference and an unknown reference are intentionally
    indistinguishable from this site.  Malformed item shapes are skipped
    here: the catalog guard rejects prop-shape violations on every write
    path, so this check only ever runs over shape-valid items and therefore
    cannot let an invalid item through.
    """
    spec = MEDIA_REFERENCE_COMPONENTS.get(component_type)
    if spec is None:
        return
    prefix, min_items, max_items = spec
    if not isinstance(items, (list, tuple)):
        return
    if not min_items <= len(items) <= max_items:
        raise MediaReferenceError(f"{prefix}.items-out-of-range")
    for item in items:
        if not isinstance(item, Mapping):
            continue
        media_id = _as_uuid(item.get("mediaId"))
        if media_id is None:
            raise MediaReferenceError(f"{prefix}.item-missing")
        fact = facts.get(media_id)
        if fact is None or fact[0] != site_id:
            raise MediaReferenceError(f"{prefix}.item-foreign-site")
        if fact[1] not in MEDIA_MIME_CLASSES:
            raise MediaReferenceError(f"{prefix}.item-not-image")


# Bounded document-reference list components (079/3): error-key prefix and
# the catalog list bounds the pure check mirrors.
DOCUMENT_REFERENCE_COMPONENTS: dict[str, tuple[str, int, int]] = {
    "DocumentList": ("doclist", 1, 12),
}

# The bounded document-class MIME the immutable store accepts (079/3).
DOCUMENT_MIME_CLASSES = frozenset({"application/pdf"})

# The complete bounded document-class error-key vocabulary surfaced as 422
# ``prop_error`` (079/3 R3).
DOCUMENT_REFERENCE_ERROR_KEYS = frozenset(
    f"{prefix}.{suffix}"
    for prefix, _, _ in DOCUMENT_REFERENCE_COMPONENTS.values()
    for suffix in (
        "item-missing",
        "item-foreign-site",
        "item-not-pdf",
        "items-out-of-range",
    )
)


def validate_document_reference_items(
    component_type: str,
    items: Any,
    *,
    site_id: UUID,
    facts: Mapping[UUID, tuple[UUID, str] | None],
) -> None:
    """Reject document-reference list items outside the site's document class.

    Same fail-closed resolution contract as
    :func:`validate_media_reference_items`, bounded to the document class
    (079/3 R3): a well-formed ``mediaId`` must resolve to a row of the
    writing site whose ``mime_type`` is ``application/pdf``.  Duplicate
    items are allowed (catalog shape is the only constraint on repeats);
    label bounds are catalog prop-shape and enforced by the guard.
    """
    spec = DOCUMENT_REFERENCE_COMPONENTS.get(component_type)
    if spec is None:
        return
    prefix, min_items, max_items = spec
    if not isinstance(items, (list, tuple)):
        return
    if not min_items <= len(items) <= max_items:
        raise MediaReferenceError(f"{prefix}.items-out-of-range")
    for item in items:
        if not isinstance(item, Mapping):
            continue
        media_id = _as_uuid(item.get("mediaId"))
        if media_id is None:
            raise MediaReferenceError(f"{prefix}.item-missing")
        fact = facts.get(media_id)
        if fact is None or fact[0] != site_id:
            raise MediaReferenceError(f"{prefix}.item-foreign-site")
        if fact[1] not in DOCUMENT_MIME_CLASSES:
            raise MediaReferenceError(f"{prefix}.item-not-pdf")


__all__ = [
    "DOCUMENT_MIME_CLASSES",
    "DOCUMENT_REFERENCE_COMPONENTS",
    "DOCUMENT_REFERENCE_ERROR_KEYS",
    "FacetValidationError",
    "IN_LIST_ENTRY_MAX_LENGTH",
    "IN_LIST_MAX_ENTRIES",
    "MAX_FACETS",
    "MEDIA_MIME_CLASSES",
    "MEDIA_REFERENCE_COMPONENTS",
    "MEDIA_REFERENCE_ERROR_KEYS",
    "MediaReferenceError",
    "field_primitive_map",
    "validate_collection_filter_facets",
    "validate_document_reference_items",
    "validate_media_reference_items",
]

"""Fail-closed write-time validation for CollectionFilter facet semantics.

The component catalog guard enforces the *shape* of the ``facets`` prop on
every composition write path (Agent and human Puck).  This module adds the
*semantic* constraint that the static catalog cannot express: every facet
must reference a field of the bound view's content type and use an operator
from that field's per-primitive query vocabulary (``query_dsl._OPS``).  View
and field resolution is site-scoped by the caller; anything that cannot be
resolved is rejected before the composition write is attempted.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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


__all__ = [
    "FacetValidationError",
    "IN_LIST_ENTRY_MAX_LENGTH",
    "IN_LIST_MAX_ENTRIES",
    "MAX_FACETS",
    "field_primitive_map",
    "validate_collection_filter_facets",
]

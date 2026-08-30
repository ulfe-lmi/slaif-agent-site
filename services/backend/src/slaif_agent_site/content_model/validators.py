"""Pure, bounded validation for editable domain values."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from .models import FieldDefinitionRecord
from .primitives import FieldPrimitive

_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,62}$")
_EXECUTABLE = re.compile(
    r"(?:<script|javascript:|__proto__|constructor|prototype)", re.I
)


def _scalar_ok(kind: FieldPrimitive, value: Any, validation: dict[str, Any]) -> bool:
    if isinstance(value, str) and _EXECUTABLE.search(value):
        return False
    if kind in (
        FieldPrimitive.SHORT_TEXT,
        FieldPrimitive.LONG_TEXT,
        FieldPrimitive.RICH_TEXT,
        FieldPrimitive.URL,
        FieldPrimitive.EMAIL,
        FieldPrimitive.MEDIA,
        FieldPrimitive.DOCUMENT,
        FieldPrimitive.REFERENCE,
    ):
        return isinstance(value, str) and bool(value.strip())
    if kind is FieldPrimitive.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if kind is FieldPrimitive.DECIMAL:
        return isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
    if kind is FieldPrimitive.BOOLEAN:
        return isinstance(value, bool)
    if kind is FieldPrimitive.DATE:
        try:
            dt.date.fromisoformat(value)
        except (TypeError, ValueError):
            return False
        return isinstance(value, str)
    if kind is FieldPrimitive.DATETIME:
        try:
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return False
        return isinstance(value, str)
    if kind is FieldPrimitive.ENUM:
        choices = validation.get(
            "choices", validation.get("values", validation.get("enum"))
        )
        return isinstance(value, str) and (not choices or value in choices)
    if kind is FieldPrimitive.LOCATION:
        return isinstance(value, dict) and set(value) <= {
            "latitude",
            "longitude",
            "label",
            "address",
        }
    if kind is FieldPrimitive.OBJECT:
        return isinstance(value, dict)
    return True


def validate_values(
    values: dict[str, Any],
    fields: Iterable[FieldDefinitionRecord],
    *,
    localized: bool = False,
) -> None:
    definitions = {field.key: field for field in fields}
    if any(not isinstance(key, str) or not _KEY.fullmatch(key) for key in values):
        raise ValueError("field keys must be bounded identifiers")
    for key, value in values.items():
        field = definitions.get(key)
        if field is None:
            raise ValueError(f"unknown field: {key}")
        if field.localized != localized:
            raise ValueError(f"field localization mismatch: {key}")
        values_to_check = value if field.cardinality > 1 else [value]
        if field.cardinality > 1:
            if not isinstance(value, list) or not 1 <= len(value) <= field.cardinality:
                raise ValueError(f"invalid cardinality: {key}")
        elif isinstance(value, list):
            raise ValueError(f"scalar field cannot contain an array: {key}")
        kind = FieldPrimitive.from_value(field.field_type)
        if not all(
            _scalar_ok(kind, item, field.validation) for item in values_to_check
        ):
            raise ValueError(f"invalid value for field: {key}")
    missing = [
        f.key
        for f in definitions.values()
        if f.required and f.localized == localized and f.key not in values
    ]
    if missing:
        raise ValueError("required fields missing: " + ",".join(missing))

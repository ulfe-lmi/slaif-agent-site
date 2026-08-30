"""Canonical, typed, and bounded collection query contracts.

The Editor persists this small declarative language and Render evaluates the
same language. This module deliberately contains no SQL or executable
callbacks: a query is data, and every accepted operation has a fixed meaning.
"""

from __future__ import annotations

import datetime as dt
import math
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

from .primitives import FieldPrimitive

MAX_DEPTH = 4
MAX_CLAUSES = 32
MAX_PAGE_SIZE = 100
MAX_OFFSET = 10_000
MAX_QUERY_NODES = 256
MAX_QUERY_BYTES = 16_384
MAX_CANDIDATES = 1_000

_COMMON_FIELDS = {"id", "site_id", "type_id", "slug", "status", "values"}
_OPS: dict[FieldPrimitive, frozenset[str]] = {
    FieldPrimitive.SHORT_TEXT: frozenset({"eq", "contains", "prefix"}),
    FieldPrimitive.LONG_TEXT: frozenset({"eq", "contains"}),
    FieldPrimitive.RICH_TEXT: frozenset({"eq", "contains"}),
    FieldPrimitive.INTEGER: frozenset({"eq", "lt", "lte", "gt", "gte"}),
    FieldPrimitive.DECIMAL: frozenset({"eq", "lt", "lte", "gt", "gte"}),
    FieldPrimitive.BOOLEAN: frozenset({"eq"}),
    FieldPrimitive.DATE: frozenset({"eq", "lt", "lte", "gt", "gte"}),
    FieldPrimitive.DATETIME: frozenset({"eq", "lt", "lte", "gt", "gte"}),
    FieldPrimitive.URL: frozenset({"eq", "contains"}),
    FieldPrimitive.EMAIL: frozenset({"eq", "contains"}),
    FieldPrimitive.ENUM: frozenset({"eq", "in"}),
}
_SORTABLE = frozenset(
    {
        FieldPrimitive.SHORT_TEXT,
        FieldPrimitive.LONG_TEXT,
        FieldPrimitive.RICH_TEXT,
        FieldPrimitive.INTEGER,
        FieldPrimitive.DECIMAL,
        FieldPrimitive.BOOLEAN,
        FieldPrimitive.DATE,
        FieldPrimitive.DATETIME,
        FieldPrimitive.URL,
        FieldPrimitive.EMAIL,
        FieldPrimitive.ENUM,
    }
)
_EXECUTABLE_MARKERS = (";", "--", "/*", "*/")


def _walk(value: Any, depth: int = 0, state: list[int] | None = None) -> int:
    """Walk every supported container and enforce aggregate query bounds."""

    counters = state if state is not None else [0, 0]
    if depth > MAX_DEPTH:
        raise ValueError("query logical depth exceeds limit")
    counters[0] += 1
    if counters[0] > MAX_QUERY_NODES:
        raise ValueError("query node count exceeds limit")
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("query object keys must be text")
            counters[1] += len(key.encode("utf-8"))
            _reject_executable(key)
            _walk(child, depth + 1, counters)
    elif isinstance(value, (list, tuple)):
        if len(value) > MAX_CLAUSES:
            raise ValueError("query clause count exceeds limit")
        for child in value:
            _walk(child, depth + 1, counters)
    elif isinstance(value, str):
        counters[1] += len(value.encode("utf-8"))
        _reject_executable(value)
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise ValueError("query values must be JSON scalars")
    if counters[1] > MAX_QUERY_BYTES:
        raise ValueError("query byte budget exceeds limit")
    return counters[0]


def _reject_executable(value: str) -> None:
    if any(marker in value for marker in _EXECUTABLE_MARKERS):
        raise ValueError("query values cannot contain executable SQL fragments")


def _choices(field: Any) -> set[str] | None:
    validation = getattr(field, "validation", {})
    if not isinstance(validation, Mapping):
        return None
    choices = validation.get(
        "choices", validation.get("values", validation.get("enum"))
    )
    if choices is None:
        return None
    if not isinstance(choices, (list, tuple, set, frozenset)) or not all(
        isinstance(item, str) for item in choices
    ):
        raise ValueError("enum choices are malformed")
    return set(choices)


def _scalar_type_ok(kind: FieldPrimitive, value: Any, field: Any) -> bool:
    if kind in {
        FieldPrimitive.SHORT_TEXT,
        FieldPrimitive.LONG_TEXT,
        FieldPrimitive.RICH_TEXT,
        FieldPrimitive.URL,
        FieldPrimitive.EMAIL,
    }:
        return isinstance(value, str) and bool(value.strip())
    if kind is FieldPrimitive.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if kind is FieldPrimitive.DECIMAL:
        return (
            isinstance(value, (int, float, Decimal))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    if kind is FieldPrimitive.BOOLEAN:
        return isinstance(value, bool)
    if kind is FieldPrimitive.DATE:
        if not isinstance(value, str):
            return False
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            return False
        return True
    if kind is FieldPrimitive.DATETIME:
        if not isinstance(value, str):
            return False
        try:
            dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
        return True
    if kind is FieldPrimitive.ENUM:
        choices = _choices(field)
        return isinstance(value, str) and (choices is None or value in choices)
    return False


def _clause_value_ok(field: Any, operator: str, value: Any) -> bool:
    kind = FieldPrimitive.from_value(field.field_type)
    if operator == "in":
        return (
            kind is FieldPrimitive.ENUM
            and isinstance(value, list)
            and 1 <= len(value) <= MAX_CLAUSES
            and all(isinstance(item, str) for item in value)
            and len(set(value)) == len(value)
            and all(_scalar_type_ok(kind, item, field) for item in value)
        )
    if operator in {"contains", "prefix"} and kind not in {
        FieldPrimitive.SHORT_TEXT,
        FieldPrimitive.LONG_TEXT,
        FieldPrimitive.RICH_TEXT,
        FieldPrimitive.URL,
        FieldPrimitive.EMAIL,
    }:
        return False
    return _scalar_type_ok(kind, value, field)


def _validate_filter_node(node: Any, definitions: Mapping[str, Any]) -> None:
    if not isinstance(node, dict):
        raise ValueError("invalid logical filter")
    allowed = {"status", "slug", "and", "or", "not", "field", "op", "value"}
    if set(node) - allowed:
        raise ValueError("unknown filter member")
    if "status" in node and (
        not isinstance(node["status"], str)
        or node["status"] not in {"DRAFT", "PUBLISHED", "ARCHIVED"}
    ):
        raise ValueError("invalid status filter")
    if "slug" in node and not isinstance(node["slug"], str):
        raise ValueError("slug filter must be text")
    if "field" in node or "op" in node or "value" in node:
        if set(node) & {"field", "op", "value"} != {"field", "op", "value"}:
            raise ValueError("filter clause requires field, op, and value")
        name, operator = node["field"], node["op"]
        field = definitions.get(name) if isinstance(name, str) else None
        if field is None or field.localized:
            raise ValueError("unknown or localized filter field")
        try:
            kind = FieldPrimitive.from_value(field.field_type)
        except (AttributeError, ValueError):
            raise ValueError("unknown filter primitive") from None
        if not isinstance(operator, str) or (
            operator not in _OPS.get(kind, frozenset())
            or not _clause_value_ok(field, operator, node["value"])
        ):
            raise ValueError("operator or value is not valid for field primitive")
    for key in ("and", "or"):
        if key in node:
            clauses = node[key]
            if not isinstance(clauses, list) or len(clauses) > MAX_CLAUSES:
                raise ValueError("invalid logical filter")
            for clause in clauses:
                _validate_filter_node(clause, definitions)
    if "not" in node:
        _validate_filter_node(node["not"], definitions)


def validate_query_contract(
    filter_spec: dict[str, Any],
    sort_spec: dict[str, Any],
    projection_spec: dict[str, Any] | list[str],
    pagination_spec: dict[str, Any],
    fields: Iterable[Any],
) -> None:
    """Validate a query before persistence or execution."""

    _walk((filter_spec, sort_spec, projection_spec, pagination_spec))
    if not isinstance(filter_spec, dict) or not isinstance(sort_spec, dict):
        raise ValueError("query specs must be objects")
    if not isinstance(pagination_spec, dict):
        raise ValueError("pagination spec must be an object")
    definitions = {field.key: field for field in fields}
    _validate_filter_node(filter_spec, definitions)
    if set(sort_spec) - {"field", "direction"}:
        raise ValueError("unknown sort member")
    sort_field = sort_spec.get("field", "slug")
    if not isinstance(sort_field, str):
        raise ValueError("sort field must be text")
    if sort_field not in {"slug", "id"}:
        field = definitions.get(sort_field)
        if (
            field is None
            or field.localized
            or getattr(field, "cardinality", 1) != 1
            or FieldPrimitive.from_value(field.field_type) not in _SORTABLE
        ):
            raise ValueError("field is not sortable")
    if not isinstance(sort_spec.get("direction", "asc"), str) or sort_spec.get(
        "direction", "asc"
    ) not in {"asc", "desc"}:
        raise ValueError("invalid sort direction")
    if isinstance(projection_spec, dict):
        if set(projection_spec) not in ({"fields"}, set()):
            raise ValueError("invalid projection shape")
        projection_fields = projection_spec.get("fields", [])
    elif isinstance(projection_spec, list):
        projection_fields = projection_spec
    else:
        raise ValueError("invalid projection shape")
    if not isinstance(projection_fields, list) or len(projection_fields) > 16:
        raise ValueError("projection field limit exceeded")
    if not all(isinstance(name, str) for name in projection_fields):
        raise ValueError("projection field must be text")
    if len(set(projection_fields)) != len(projection_fields):
        raise ValueError("duplicate projection field")
    for name in projection_fields:
        field = definitions.get(name) if isinstance(name, str) else None
        if not isinstance(name, str) or name in _COMMON_FIELDS or field is None:
            raise ValueError("unknown or reserved projection field")
        if field.localized:
            raise ValueError("localized fields are not valid projection fields")
    if set(pagination_spec) - {"limit", "offset"}:
        raise ValueError("unknown pagination member")
    limit = pagination_spec.get("limit", 24)
    offset = pagination_spec.get("offset", 0)
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 1 <= limit <= MAX_PAGE_SIZE
    ):
        raise ValueError("pagination limit exceeds bound")
    if (
        isinstance(offset, bool)
        or not isinstance(offset, int)
        or not 0 <= offset <= MAX_OFFSET
    ):
        raise ValueError("pagination offset exceeds bound")


def _compare(actual: Any, expected: Any, operator: str) -> bool:
    if operator == "eq":
        return bool(actual == expected)
    if operator == "contains":
        return isinstance(actual, str) and expected in actual
    if operator == "prefix":
        return isinstance(actual, str) and actual.startswith(expected)
    if operator == "in":
        return bool(actual in expected)
    try:
        return bool(
            {
                "lt": actual < expected,
                "lte": actual <= expected,
                "gt": actual > expected,
                "gte": actual >= expected,
            }[operator]
        )
    except (KeyError, TypeError):
        return False


def _field_matches(actual: Any, operator: str, expected: Any) -> bool:
    actual_values = actual if isinstance(actual, list) else [actual]
    return any(_compare(value, expected, operator) for value in actual_values)


def matches_filter(
    filter_spec: Mapping[str, Any],
    values: Mapping[str, Any],
    *,
    slug: str,
    status: str,
) -> bool:
    """Evaluate the already-validated filter form without dynamic code/SQL."""

    if "status" in filter_spec and status != filter_spec["status"]:
        return False
    if "slug" in filter_spec and slug != filter_spec["slug"]:
        return False
    if "and" in filter_spec and not all(
        matches_filter(clause, values, slug=slug, status=status)
        for clause in filter_spec["and"]
    ):
        return False
    if (
        "or" in filter_spec
        and filter_spec["or"]
        and not any(
            matches_filter(clause, values, slug=slug, status=status)
            for clause in filter_spec["or"]
        )
    ):
        return False
    if "not" in filter_spec and matches_filter(
        filter_spec["not"], values, slug=slug, status=status
    ):
        return False
    if "field" in filter_spec:
        return _field_matches(
            values.get(filter_spec["field"]),
            filter_spec["op"],
            filter_spec["value"],
        )
    return True


def sort_collection_items(
    items: list[dict[str, Any]], sort_spec: Mapping[str, Any]
) -> None:
    """Sort with the requested direction and an ascending ID tie-break."""

    field = sort_spec.get("field", "slug")
    direction = sort_spec.get("direction", "asc")
    items.sort(key=lambda item: str(item["id"]))

    def primary(item: dict[str, Any]) -> tuple[int, Any]:
        value = item["slug"] if field == "slug" else item["values"].get(field)
        if value is None:
            return (0, "")
        if isinstance(value, (dict, list)):
            raise ValueError("unsortable stored field value")
        if isinstance(value, bool):
            return (1, int(value))
        if isinstance(value, (int, float, Decimal, str)):
            return (1, value)
        raise ValueError("unsortable stored field value")

    items.sort(key=primary, reverse=direction == "desc")


__all__ = [
    "MAX_CANDIDATES",
    "MAX_CLAUSES",
    "MAX_DEPTH",
    "MAX_OFFSET",
    "MAX_PAGE_SIZE",
    "MAX_QUERY_BYTES",
    "MAX_QUERY_NODES",
    "matches_filter",
    "sort_collection_items",
    "validate_query_contract",
]

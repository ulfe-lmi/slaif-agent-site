"""Canonical, non-executable collection query contract shared by Editor/Render."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .primitives import FieldPrimitive

MAX_DEPTH = 4
MAX_CLAUSES = 32
MAX_PAGE_SIZE = 100

_COMMON_FIELDS = {"id", "site_id", "type_id", "slug", "status"}
_OPS: dict[FieldPrimitive, set[str]] = {
    FieldPrimitive.SHORT_TEXT: {"eq", "contains", "prefix"},
    FieldPrimitive.LONG_TEXT: {"eq", "contains"},
    FieldPrimitive.RICH_TEXT: {"eq", "contains"},
    FieldPrimitive.INTEGER: {"eq", "lt", "lte", "gt", "gte"},
    FieldPrimitive.DECIMAL: {"eq", "lt", "lte", "gt", "gte"},
    FieldPrimitive.BOOLEAN: {"eq"},
    FieldPrimitive.DATE: {"eq", "lt", "lte", "gt", "gte"},
    FieldPrimitive.DATETIME: {"eq", "lt", "lte", "gt", "gte"},
    FieldPrimitive.URL: {"eq", "contains"},
    FieldPrimitive.EMAIL: {"eq", "contains"},
    FieldPrimitive.ENUM: {"eq", "in"},
}


def _walk(value: Any, depth: int = 0) -> int:
    if depth > MAX_DEPTH:
        raise ValueError("query logical depth exceeds limit")
    if isinstance(value, dict):
        return 1 + sum(_walk(item, depth + 1) for item in value.values())
    if isinstance(value, list):
        if len(value) > MAX_CLAUSES:
            raise ValueError("query clause count exceeds limit")
        return 1 + sum(_walk(item, depth + 1) for item in value)
    if isinstance(value, str) and (";" in value or "--" in value or "/*" in value):
        raise ValueError("query values cannot contain executable SQL fragments")
    return 1


def validate_query_contract(
    filter_spec: dict[str, Any],
    sort_spec: dict[str, Any],
    projection_spec: dict[str, Any] | list[str],
    pagination_spec: dict[str, Any],
    fields: Iterable[Any],
) -> None:
    """Validate and reject non-canonical query data before persistence/render."""
    _walk((filter_spec, sort_spec, projection_spec, pagination_spec))
    definitions = {field.key: field for field in fields}
    if set(filter_spec) - {
        "status",
        "slug",
        "and",
        "or",
        "not",
        "field",
        "op",
        "value",
    }:
        raise ValueError("unknown filter member")
    if set(sort_spec) - {"field", "direction"}:
        raise ValueError("unknown sort member")
    if set(pagination_spec) - {"limit", "offset"}:
        raise ValueError("unknown pagination member")
    if filter_spec.get("status") is not None and filter_spec["status"] not in {
        "DRAFT",
        "PUBLISHED",
        "ARCHIVED",
    }:
        raise ValueError("invalid status filter")
    if filter_spec.get("slug") is not None and not isinstance(filter_spec["slug"], str):
        raise ValueError("slug filter must be text")
    clauses: list[dict[str, Any]] = []
    for key in ("and", "or"):
        value = filter_spec.get(key, [])
        if not isinstance(value, list) or len(value) > MAX_CLAUSES:
            raise ValueError("invalid logical filter")
        clauses.extend(value)
    if "not" in filter_spec:
        if not isinstance(filter_spec["not"], dict):
            raise ValueError("invalid negated filter")
        clauses.append(filter_spec["not"])
    if "field" in filter_spec or "op" in filter_spec:
        clauses.append(filter_spec)
    for clause in clauses:
        if not isinstance(clause, dict) or set(clause) - {"field", "op", "value"}:
            raise ValueError("invalid filter clause")
        name, operator = clause.get("field"), clause.get("op")
        field = definitions.get(name) if isinstance(name, str) else None
        if field is None or field.localized:
            raise ValueError("unknown or localized filter field")
        if operator not in _OPS.get(FieldPrimitive.from_value(field.field_type), set()):
            raise ValueError("operator is not valid for field primitive")
        if "value" not in clause:
            raise ValueError("filter value is required")
    sort_field = sort_spec.get("field", "slug")
    if sort_field != "slug":
        field = definitions.get(sort_field)
        if (
            field is None
            or field.localized
            or FieldPrimitive.from_value(field.field_type) not in _OPS
        ):
            raise ValueError("field is not sortable")
    if sort_spec.get("direction", "asc") not in {"asc", "desc"}:
        raise ValueError("invalid sort direction")
    if isinstance(projection_spec, dict):
        if set(projection_spec) not in ({"fields"}, set()):
            raise ValueError("invalid projection shape")
        projection_fields = projection_spec.get("fields", [])
    else:
        projection_fields = projection_spec
    if not isinstance(projection_fields, list) or len(projection_fields) > 16:
        raise ValueError("projection field limit exceeded")
    if len(set(projection_fields)) != len(projection_fields):
        raise ValueError("duplicate projection field")
    for name in projection_fields:
        if (
            not isinstance(name, str)
            or name in _COMMON_FIELDS
            or name not in definitions
        ):
            raise ValueError("unknown or reserved projection field")
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
        or not 0 <= offset <= 10000
    ):
        raise ValueError("pagination offset exceeds bound")

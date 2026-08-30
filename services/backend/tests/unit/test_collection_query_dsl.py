from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from slaif_agent_site.content_model.models import FieldDefinitionRecord
from slaif_agent_site.content_model.query_dsl import (
    MAX_CANDIDATES,
    matches_filter,
    sort_collection_items,
    validate_query_contract,
)


def _field(
    key: str = "title", kind: str = "short_text", localized: bool = False
) -> FieldDefinitionRecord:
    now = datetime.now(UTC)
    return FieldDefinitionRecord(
        id=uuid4(),
        site_id=uuid4(),
        type_id=uuid4(),
        key=key,
        label=key,
        field_type=kind,
        required=False,
        localized=localized,
        cardinality=1,
        position=0,
        validation={},
        ui_options={},
        definition_version=1,
        created_at=now,
        updated_at=now,
    )


def test_query_dsl_accepts_typed_clause_and_projection() -> None:
    validate_query_contract(
        {"and": [{"field": "title", "op": "contains", "value": "news"}]},
        {"field": "title", "direction": "asc"},
        {"fields": ["title"]},
        {"limit": 10, "offset": 0},
        [_field()],
    )


@pytest.mark.parametrize(
    "query",
    [
        {"filter": {"field": "title", "op": "raw_sql", "value": "1; DROP"}},
        {"filter": {"field": "missing", "op": "eq", "value": "x"}},
        {"filter": {"field": "title", "op": "contains", "value": "x"}, "limit": 1000},
    ],
)
def test_query_dsl_rejects_unsafe_or_unbounded_shape(query: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        validate_query_contract(
            cast(dict[str, Any], query.get("filter", {})),
            {},
            {},
            {"limit": query.get("limit", 24)},
            [_field()],
        )


def test_query_dsl_rejects_localized_filter() -> None:
    with pytest.raises(ValueError):
        validate_query_contract(
            {"field": "title", "op": "eq", "value": "x"},
            {},
            {},
            {},
            [_field(localized=True)],
        )


def test_query_dsl_walks_top_level_and_nested_containers() -> None:
    with pytest.raises(ValueError, match="depth"):
        validate_query_contract(
            {"and": [{"and": [{"and": [{"and": [{"status": "PUBLISHED"}]}]}]}]},
            {},
            {},
            {},
            [_field()],
        )
    with pytest.raises(ValueError, match="executable"):
        validate_query_contract(
            {"and": [{"slug": "safe; DROP"}]},
            {},
            {},
            {},
            [_field()],
        )
    with pytest.raises(ValueError, match="node"):
        validate_query_contract(
            {f"unknown-{index}": index for index in range(260)},
            {},
            {},
            {},
            [_field()],
        )
    with pytest.raises(ValueError, match="byte"):
        validate_query_contract({"slug": "x" * 17_000}, {}, {}, {}, [_field()])


def test_query_dsl_validates_primitive_values_and_enum_bounds() -> None:
    integer = _field("rank", "integer")
    enum = _field("state", "enum")
    enum = enum.model_copy(update={"validation": {"choices": ["news", "opinion"]}})
    with pytest.raises(ValueError, match="primitive"):
        validate_query_contract(
            {"field": "rank", "op": "gt", "value": "3"},
            {},
            {},
            {},
            [integer],
        )
    with pytest.raises(ValueError, match="primitive"):
        validate_query_contract(
            {"field": "state", "op": "in", "value": ["news", "news"]},
            {},
            {},
            {},
            [enum],
        )
    validate_query_contract(
        {"field": "state", "op": "in", "value": ["news"]},
        {"field": "rank", "direction": "desc"},
        {"fields": ["state", "rank"]},
        {"limit": 2, "offset": 1},
        [integer, enum],
    )


def test_query_evaluator_and_sort_share_the_contract_semantics() -> None:
    query = {
        "and": [
            {"field": "headline", "op": "contains", "value": "release"},
            {"not": {"slug": "draft"}},
        ]
    }
    assert matches_filter(
        query,
        {"headline": "Product release", "rank": 2},
        slug="published",
        status="PUBLISHED",
    )
    assert not matches_filter(
        query,
        {"headline": "Product release", "rank": 2},
        slug="draft",
        status="PUBLISHED",
    )
    items = [
        {"id": "b", "slug": "b", "values": {"rank": 2}},
        {"id": "a", "slug": "a", "values": {"rank": 2}},
        {"id": "c", "slug": "c", "values": {"rank": 1}},
    ]
    sort_collection_items(items, {"field": "rank", "direction": "desc"})
    assert [item["id"] for item in items] == ["a", "b", "c"]
    assert MAX_CANDIDATES == 1_000

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from slaif_agent_site.content_model.models import FieldDefinitionRecord
from slaif_agent_site.content_model.query_dsl import validate_query_contract


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

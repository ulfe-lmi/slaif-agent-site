"""Fail-closed CollectionFilter facet vocabulary contracts."""

from types import SimpleNamespace

import pytest
from slaif_agent_site.content_model.component_facets import (
    FacetValidationError,
    field_primitive_map,
    validate_collection_filter_facets,
)

FIELDS = {
    "title": "short_text",
    "summary": "long_text",
    "rank": "integer",
    "published_on": "date",
    "active": "boolean",
    "kind": "enum",
    "site": "url",
}


def _facets(*entries: dict[str, object]) -> list[dict[str, object]]:
    return list(entries)


def test_valid_facet_vocabularies_pass() -> None:
    validate_collection_filter_facets(
        _facets(
            {"fieldKey": "title", "operator": "contains", "value": "news"},
            {"fieldKey": "rank", "operator": "gte", "value": "1"},
            {"fieldKey": "kind", "operator": "in", "value": "a, b ,c"},
        ),
        FIELDS,
    )


def test_unknown_field_key_is_rejected() -> None:
    with pytest.raises(FacetValidationError) as exc:
        validate_collection_filter_facets(
            _facets({"fieldKey": "missing", "operator": "eq", "value": "x"}), FIELDS
        )
    assert exc.value.code == "collection_filter_field"


@pytest.mark.parametrize(
    ("field_key", "operator"),
    [
        ("summary", "prefix"),  # long_text vocabulary is eq/contains
        ("rank", "contains"),  # integer vocabulary is comparison operators
        ("rank", "in"),
        ("published_on", "contains"),
        ("active", "in"),
        ("kind", "contains"),  # enum vocabulary is eq/in
        ("site", "prefix"),  # url vocabulary is eq/contains
    ],
)
def test_out_of_vocabulary_operators_are_rejected(
    field_key: str, operator: str
) -> None:
    with pytest.raises(FacetValidationError) as exc:
        validate_collection_filter_facets(
            _facets({"fieldKey": field_key, "operator": operator, "value": "x"}),
            FIELDS,
        )
    assert exc.value.code == "collection_filter_operator"


def test_fifth_facet_is_rejected() -> None:
    entries: list[dict[str, object]] = [
        {"fieldKey": "title", "operator": "eq", "value": str(i)} for i in range(5)
    ]
    facets = _facets(*entries)
    with pytest.raises(FacetValidationError) as exc:
        validate_collection_filter_facets(facets, FIELDS)
    assert exc.value.code == "collection_filter_facets"


def test_nine_entry_in_list_is_rejected() -> None:
    with pytest.raises(FacetValidationError) as exc:
        validate_collection_filter_facets(
            _facets(
                {
                    "fieldKey": "kind",
                    "operator": "in",
                    "value": ",".join(f"e{i}" for i in range(9)),
                }
            ),
            FIELDS,
        )
    assert exc.value.code == "collection_filter_value"


def test_overlong_in_list_entry_is_rejected() -> None:
    with pytest.raises(FacetValidationError) as exc:
        validate_collection_filter_facets(
            _facets(
                {
                    "fieldKey": "kind",
                    "operator": "in",
                    "value": f"a,{chr(97) * 257}",
                }
            ),
            FIELDS,
        )
    assert exc.value.code == "collection_filter_value"


def test_eight_entry_in_list_with_padding_is_accepted() -> None:
    validate_collection_filter_facets(
        _facets(
            {
                "fieldKey": "kind",
                "operator": "in",
                "value": f" ,{chr(97) * 256},  ,",
            }
        ),
        FIELDS,
    )


def test_malformed_shapes_are_skipped_for_the_catalog_guard() -> None:
    validate_collection_filter_facets(None, FIELDS)
    validate_collection_filter_facets("not-a-list", FIELDS)
    validate_collection_filter_facets(
        [{"fieldKey": "title", "operator": "eq"}, "junk", 7], FIELDS
    )


def test_unknown_field_primitive_is_rejected() -> None:
    with pytest.raises(FacetValidationError) as exc:
        validate_collection_filter_facets(
            _facets({"fieldKey": "mystery", "operator": "eq", "value": "x"}),
            {"mystery": "not_a_primitive"},
        )
    assert exc.value.code == "collection_filter_field"


def test_field_primitive_map_accepts_record_and_object_rows() -> None:
    class _Record:
        def __getitem__(self, name: str) -> str:
            values = {"key": "rank", "field_type": "integer"}
            if name not in values:
                raise KeyError(name)
            return values[name]

    mapped = field_primitive_map(
        [
            _Record(),
            SimpleNamespace(key="title", field_type="short_text"),
            SimpleNamespace(key="dup", field_type="ignored"),
            SimpleNamespace(key="rank", field_type="ignored"),
            {"key": "kind", "field_type": "enum"},
            SimpleNamespace(key=123, field_type="enum"),
        ]
    )
    assert mapped == {
        "rank": "integer",
        "title": "short_text",
        "dup": "ignored",
        "kind": "enum",
    }

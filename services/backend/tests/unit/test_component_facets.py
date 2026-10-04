"""Fail-closed CollectionFilter facet vocabulary contracts."""

from types import SimpleNamespace
from uuid import UUID

import pytest
from slaif_agent_site.content_model.component_facets import (
    MEDIA_MIME_CLASSES,
    MEDIA_REFERENCE_COMPONENTS,
    MEDIA_REFERENCE_ERROR_KEYS,
    FacetValidationError,
    MediaReferenceError,
    field_primitive_map,
    validate_collection_filter_facets,
    validate_media_reference_items,
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


# ---------------------------------------------------------------- 079/2
# Gallery/LogoGrid media-reference list semantics (pure, resolved facts).
SITE = UUID("11111111-2222-4333-8444-555555555555")
FOREIGN_SITE = UUID("22222222-3333-4444-8555-666666666666")
M_A = UUID("11111111-1111-4111-8111-111111111111")
M_B = UUID("11111111-1111-4111-8111-111111111112")
M_C = UUID("11111111-1111-4111-8111-111111111113")
M_TEXT = UUID("11111111-1111-4111-8111-111111111114")


def _facts(*rows: tuple[UUID, UUID, str] | None) -> dict[UUID, tuple[UUID, str] | None]:
    facts: dict[UUID, tuple[UUID, str] | None] = {}
    for row in rows:
        if row is None:
            continue
        media_id, site_id, mime = row
        facts[media_id] = (site_id, mime)
    return facts


def _gallery_items(*media_ids: object) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for index, media_id in enumerate(media_ids):
        item: dict[str, object] = {"alt": f"alt-{index}"}
        if media_id is not Ellipsis:
            item["mediaId"] = str(media_id)
        items.append(item)
    return items


def _logogrid_items(*media_ids: object) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for index, media_id in enumerate(media_ids):
        item: dict[str, object] = {"name": f"name-{index}"}
        if media_id is not Ellipsis:
            item["mediaId"] = str(media_id)
        items.append(item)
    return items


def test_valid_gallery_items_pass() -> None:
    facts = _facts(
        (M_A, SITE, "image/png"),
        (M_B, SITE, "image/jpeg"),
    )
    validate_media_reference_items(
        "Gallery", _gallery_items(M_A, M_B), site_id=SITE, facts=facts
    )


def test_valid_logogrid_items_pass() -> None:
    facts = _facts(
        (M_A, SITE, "image/png"),
        (M_B, SITE, "image/jpeg"),
    )
    validate_media_reference_items(
        "LogoGrid", _logogrid_items(M_A, M_B), site_id=SITE, facts=facts
    )


def test_duplicate_items_are_allowed() -> None:
    facts = _facts((M_A, SITE, "image/png"))
    validate_media_reference_items(
        "Gallery", _gallery_items(M_A, M_A), site_id=SITE, facts=facts
    )
    validate_media_reference_items(
        "LogoGrid", _logogrid_items(M_A, M_A, M_A), site_id=SITE, facts=facts
    )


def test_bounds_edges_pass() -> None:
    facts = _facts(
        (M_A, SITE, "image/png"),
        (M_B, SITE, "image/jpeg"),
        (M_C, SITE, "image/png"),
    )
    one = [M_A] * 1
    twelve = [M_A, M_B, M_C] * 4
    assert len(one) == MEDIA_REFERENCE_COMPONENTS["Gallery"][1]
    assert len(twelve) == MEDIA_REFERENCE_COMPONENTS["Gallery"][2]
    validate_media_reference_items(
        "Gallery", _gallery_items(*one), site_id=SITE, facts=facts
    )
    validate_media_reference_items(
        "Gallery", _gallery_items(*twelve), site_id=SITE, facts=facts
    )
    two = [M_A, M_B]
    twenty_four = [M_A, M_B, M_C] * 8
    assert len(two) == MEDIA_REFERENCE_COMPONENTS["LogoGrid"][1]
    assert len(twenty_four) == MEDIA_REFERENCE_COMPONENTS["LogoGrid"][2]
    validate_media_reference_items(
        "LogoGrid", _logogrid_items(*two), site_id=SITE, facts=facts
    )
    validate_media_reference_items(
        "LogoGrid", _logogrid_items(*twenty_four), site_id=SITE, facts=facts
    )


@pytest.mark.parametrize(
    ("component_type", "items", "code"),
    [
        ("Gallery", [], "gallery.items-out-of-range"),
        ("Gallery", [M_A] * 13, "gallery.items-out-of-range"),
        ("LogoGrid", [M_A], "logogrid.items-out-of-range"),
        ("LogoGrid", [M_A] * 25, "logogrid.items-out-of-range"),
    ],
)
def test_list_bounds_are_rejected_with_the_exact_key(
    component_type: str, items: list[object], code: str
) -> None:
    facts = _facts((M_A, SITE, "image/png"))
    builder = _gallery_items if component_type == "Gallery" else _logogrid_items
    with pytest.raises(MediaReferenceError) as exc:
        validate_media_reference_items(
            component_type, builder(*items), site_id=SITE, facts=facts
        )
    assert exc.value.code == code


@pytest.mark.parametrize(
    ("component_type", "items", "facts", "code"),
    [
        ("Gallery", _gallery_items(Ellipsis), _facts(), "gallery.item-missing"),
        (
            "Gallery",
            _gallery_items("not-a-uuid"),
            _facts(),
            "gallery.item-missing",
        ),
        (
            "Gallery",
            _gallery_items(7),
            _facts(),
            "gallery.item-missing",
        ),
        (
            "Gallery",
            _gallery_items(M_A, M_B),
            _facts((M_B, SITE, "image/png")),  # M_A never resolved
            "gallery.item-foreign-site",
        ),
        (
            "Gallery",
            _gallery_items(M_A),
            _facts((M_A, FOREIGN_SITE, "image/png")),
            "gallery.item-foreign-site",
        ),
        (
            "Gallery",
            _gallery_items(M_TEXT),
            _facts((M_TEXT, SITE, "text/plain")),
            "gallery.item-not-image",
        ),
        (
            "LogoGrid",
            _logogrid_items(Ellipsis, M_A),
            _facts((M_A, SITE, "image/png")),
            "logogrid.item-missing",
        ),
        (
            "LogoGrid",
            _logogrid_items(M_A, M_B),
            _facts((M_A, SITE, "image/png"), (M_B, FOREIGN_SITE, "image/jpeg")),
            "logogrid.item-foreign-site",
        ),
        (
            "LogoGrid",
            _logogrid_items(M_A, M_TEXT),
            _facts(
                (M_A, SITE, "image/png"),
                (M_TEXT, SITE, "image/svg+xml"),
            ),
            "logogrid.item-not-image",
        ),
    ],
)
def test_media_reference_failures_use_the_exact_bounded_key(
    component_type: str,
    items: list[dict[str, object]],
    facts: dict[UUID, tuple[UUID, str] | None],
    code: str,
) -> None:
    with pytest.raises(MediaReferenceError) as exc:
        validate_media_reference_items(component_type, items, site_id=SITE, facts=facts)
    assert exc.value.code == code


def test_malformed_shapes_and_unknown_types_pass_through() -> None:
    facts = _facts((M_A, SITE, "image/png"))
    validate_media_reference_items("Image", {"mediaId": M_A}, site_id=SITE, facts=facts)
    validate_media_reference_items("Gallery", "not-a-list", site_id=SITE, facts=facts)
    # Non-dict items are shape skips (the catalog guard owns shapes); a dict
    # item without a well-formed mediaId is the semantic item-missing case.
    validate_media_reference_items(
        "Gallery",
        ["junk", 7, M_A, None],
        site_id=SITE,
        facts=facts,
    )


def test_error_key_vocabulary_is_exactly_the_ordered_set() -> None:
    assert MEDIA_REFERENCE_ERROR_KEYS == {
        "gallery.item-missing",
        "gallery.item-foreign-site",
        "gallery.item-not-image",
        "gallery.items-out-of-range",
        "logogrid.item-missing",
        "logogrid.item-foreign-site",
        "logogrid.item-not-image",
        "logogrid.items-out-of-range",
    }
    assert MEDIA_MIME_CLASSES == {"image/png", "image/jpeg"}

"""Exact catalog-v1 and nested-prop validation contracts."""

import json
from pathlib import Path

import pytest
from slaif_agent_site.content_model.component_catalog import (
    CATALOG_DOCUMENT,
    COMPONENT_CATALOG,
    catalog_document,
    validate_component_props,
)

from tools import generate_component_catalog


def test_catalog_document_is_the_runtime_catalog_and_is_complete() -> None:
    assert catalog_document() == CATALOG_DOCUMENT
    assert CATALOG_DOCUMENT["version"] == "catalog-v1"
    assert CATALOG_DOCUMENT["composition_schema_version"] == "site-composition/v1"
    assert len(COMPONENT_CATALOG) == 27
    assert all(
        item["authority_class"] in {"content", "structure", "global"}
        for item in CATALOG_DOCUMENT["components"]
    )
    assert all(
        "schema" in prop
        for item in CATALOG_DOCUMENT["components"]
        for prop in item["props"].values()
        if prop["type"] in {"object", "array"}
    )


def test_rich_text_schema_preserves_the_existing_fixture_shape() -> None:
    valid = {
        "type": "paragraph",
        "children": [{"text": "A bounded paragraph.", "bold": True}],
    }
    assert validate_component_props("RichText", {"content": valid})["content"] == valid
    with pytest.raises(ValueError, match="nested prop unknown"):
        validate_component_props(
            "RichText",
            {
                "content": {
                    "type": "paragraph",
                    "children": [{"text": "bad", "onClick": "run"}],
                }
            },
        )
    with pytest.raises(ValueError, match="nested prop required"):
        validate_component_props(
            "RichText",
            {"content": {"type": "paragraph", "children": [{}]}},
        )
    with pytest.raises(ValueError, match="unsafe value"):
        validate_component_props(
            "RichText",
            {
                "content": {
                    "type": "paragraph",
                    "children": [{"text": "vbscript:alert(1)"}],
                }
            },
        )


@pytest.mark.parametrize(
    ("component_type", "props"),
    [
        (
            "Statistics",
            {"items": [{"label": "Users", "value": "42"}]},
        ),
        (
            "Timeline",
            {"items": [{"title": "Launch", "description": "Released."}]},
        ),
        (
            "FAQ",
            {"items": [{"question": "Why?", "answer": "Because."}]},
        ),
    ],
)
def test_structured_array_schemas_have_meaningful_bounded_values(
    component_type: str, props: dict[str, object]
) -> None:
    assert validate_component_props(component_type, props) == props
    key = next(iter(props))
    assert isinstance(props[key], list)
    malformed = {key: [{"unexpected": "value"}]}
    with pytest.raises(ValueError, match="nested prop"):
        validate_component_props(component_type, malformed)


def test_catalog_json_is_stably_serializable() -> None:
    encoded = json.dumps(CATALOG_DOCUMENT, sort_keys=True, separators=(",", ":"))
    assert json.loads(encoded) == CATALOG_DOCUMENT


def test_catalog_generator_check_detects_one_byte_artifact_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "component_catalog.py"
    path.write_text(generate_component_catalog.PYTHON_TARGET.read_text() + "\n")
    monkeypatch.setattr(generate_component_catalog, "PYTHON_TARGET", path)
    with pytest.raises(SystemExit, match="catalog drift"):
        generate_component_catalog.check()


def test_078_7_catalog_entries_match_the_binding_decisions() -> None:
    by_type = {item["type"]: item for item in CATALOG_DOCUMENT["components"]}
    call_to_action = by_type["CallToAction"]
    assert (
        call_to_action["category"],
        call_to_action["binding_kind"],
        call_to_action["authority_class"],
        call_to_action["allowed_slots"],
        call_to_action["max_children"],
    ) == ("basic", "none", "content", [], 0)
    assert call_to_action["props"] == {
        "heading": {
            "type": "string",
            "required": True,
            "max_length": 256,
            "localized": True,
            "authority": "content",
        },
        "text": {
            "type": "string",
            "required": False,
            "max_length": 1024,
            "localized": True,
            "authority": "content",
        },
        "label": {
            "type": "string",
            "required": True,
            "max_length": 64,
            "localized": True,
            "authority": "content",
        },
        "href": {
            "type": "string",
            "required": True,
            "max_length": 4096,
            "authority": "content",
        },
        "variant": {
            "type": "enum",
            "required": False,
            "enum_values": ["primary", "secondary", "ghost"],
            "authority": "content",
        },
    }
    contact_block = by_type["ContactBlock"]
    assert (
        contact_block["category"],
        contact_block["binding_kind"],
        contact_block["allowed_slots"],
        contact_block["max_children"],
    ) == ("institutional", "none", [], 0)
    assert contact_block["props"] == {
        "organization": {
            "type": "string",
            "required": True,
            "max_length": 256,
            "localized": True,
            "authority": "content",
        },
        "address": {
            "type": "string",
            "required": False,
            "max_length": 512,
            "localized": True,
            "authority": "content",
        },
        "phone": {
            "type": "string",
            "required": False,
            "max_length": 32,
            "authority": "content",
        },
        "email": {
            "type": "string",
            "required": False,
            "max_length": 254,
            "authority": "content",
        },
        "hours": {
            "type": "string",
            "required": False,
            "max_length": 512,
            "localized": True,
            "authority": "content",
        },
    }
    search = by_type["CollectionSearch"]
    assert (
        search["category"],
        search["binding_kind"],
        search["allowed_slots"],
        search["max_children"],
    ) == ("data", "collection_view", [], 0)
    assert search["props"] == {
        "viewId": {
            "type": "reference",
            "required": True,
            "format": "uuid",
            "authority": "content",
        },
        "limit": {
            "type": "number",
            "required": False,
            "minimum": 1,
            "maximum": 100,
            "authority": "content",
        },
        "placeholder": {
            "type": "string",
            "required": False,
            "max_length": 64,
            "localized": True,
            "authority": "content",
        },
    }
    filter_component = by_type["CollectionFilter"]
    assert (
        filter_component["category"],
        filter_component["binding_kind"],
        filter_component["allowed_slots"],
        filter_component["max_children"],
    ) == ("data", "collection_view", [], 0)
    assert filter_component["props"]["viewId"] == search["props"]["viewId"]
    assert filter_component["props"]["limit"] == search["props"]["limit"]
    assert filter_component["props"]["facets"] == {
        "type": "array",
        "required": True,
        "min_items": 1,
        "max_items": 4,
        "authority": "content",
        "schema": {
            "type": "array",
            "min_items": 1,
            "max_items": 4,
            "items": {
                "type": "object",
                "required": ["fieldKey", "operator", "value"],
                "additional_properties": False,
                "properties": {
                    "fieldKey": {"type": "string", "required": True, "max_length": 64},
                    "operator": {
                        "type": "enum",
                        "required": True,
                        "enum_values": [
                            "eq",
                            "contains",
                            "prefix",
                            "lt",
                            "lte",
                            "gt",
                            "gte",
                            "in",
                        ],
                    },
                    "value": {"type": "string", "required": True, "max_length": 4096},
                },
            },
        },
    }
    related = by_type["RelatedItems"]
    assert (
        related["category"],
        related["binding_kind"],
        related["allowed_slots"],
        related["max_children"],
    ) == ("data", "collection_view", [], 0)
    assert related["props"] == {
        "viewId": {
            "type": "reference",
            "required": True,
            "format": "uuid",
            "authority": "content",
        },
        "limit": {
            "type": "number",
            "required": False,
            "minimum": 1,
            "maximum": 20,
            "authority": "content",
        },
        "heading": {
            "type": "string",
            "required": False,
            "max_length": 256,
            "localized": True,
            "authority": "content",
        },
    }


def test_078_7_catalog_prop_validation_round_trip() -> None:
    assert (
        validate_component_props(
            "CallToAction",
            {
                "heading": "Ship it",
                "label": "Read more",
                "href": "/news",
                "variant": "secondary",
            },
        )["variant"]
        == "secondary"
    )
    with pytest.raises(ValueError, match="unsafe value"):
        validate_component_props(
            "CallToAction",
            {"heading": "x", "label": "y", "href": "javascript:alert(1)"},
        )
    with pytest.raises(ValueError, match="prop bound"):
        validate_component_props(
            "RelatedItems",
            {
                "viewId": "11111111-1111-4111-8111-111111111111",
                "limit": 21,
            },
        )
    with pytest.raises(ValueError, match="prop bound"):
        validate_component_props(
            "CollectionFilter",
            {
                "viewId": "11111111-1111-4111-8111-111111111111",
                "facets": [
                    {"fieldKey": "title", "operator": "eq", "value": "a"},
                    {"fieldKey": "title", "operator": "eq", "value": "b"},
                    {"fieldKey": "title", "operator": "eq", "value": "c"},
                    {"fieldKey": "title", "operator": "eq", "value": "d"},
                    {"fieldKey": "title", "operator": "eq", "value": "e"},
                ],
            },
        )

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
    assert len(COMPONENT_CATALOG) == 22
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

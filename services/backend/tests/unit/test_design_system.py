"""Unit proof for the deterministic design-system/v1 authority."""

from __future__ import annotations

import pytest
from slaif_agent_site.content_model.design_system import (
    DESIGN_SYSTEM_DOCUMENT,
    design_property,
    required_scopes_for_component_update,
    validate_agent_component_props,
    validate_design_resource_constraints,
)


def test_design_system_is_catalog_bound_and_has_fixed_responsive_labels() -> None:
    assert DESIGN_SYSTEM_DOCUMENT["version"] == "design-system/v1"
    assert DESIGN_SYSTEM_DOCUMENT["catalog_version"] == "catalog-v1"
    assert DESIGN_SYSTEM_DOCUMENT["responsive_labels"] == [
        "desktop",
        "tablet",
        "mobile",
    ]
    assert design_property("Grid", "columns")["scope"] == "layout:write"  # type: ignore[index]
    assert design_property("Heading", "alignment")["scope"] == "layout:write"  # type: ignore[index]


def test_changed_properties_derive_exact_design_and_responsive_scopes() -> None:
    assert required_scopes_for_component_update(
        "Heading",
        {"text": "before", "level": 2},
        {
            "text": "after",
            "alignment": {"desktop": "start", "tablet": "center"},
        },
    ) == (
        "component-content-props:write",
        "layout:write",
        "responsive-design:write",
    )
    assert required_scopes_for_component_update(
        "Section", {"variant": "default"}, {"variant": "narrow"}
    ) == ("component-variant:write",)


def test_agent_validation_normalizes_responsive_maps_and_rejects_unsafe_design() -> (
    None
):
    props = validate_agent_component_props(
        "Grid",
        {"columns": 1, "gap": "md"},
        {
            "columns": {"mobile": 1, "desktop": 4},
            "gap": "lg",
            "alignment": "center",
        },
    )
    assert props["columns"] == {"desktop": 4, "mobile": 1}
    assert props["alignment"] == "center"
    with pytest.raises(ValueError, match="unsupported design prop"):
        validate_agent_component_props(
            "Section", {"variant": "default"}, {"background": "#fff"}
        )
    with pytest.raises(ValueError, match="alignment"):
        validate_agent_component_props(
            "Heading", {"text": "bad", "level": 2}, {"alignment": "left"}
        )


def test_design_resource_constraints_narrow_safe_choices() -> None:
    with pytest.raises(ValueError, match="responsive"):
        validate_design_resource_constraints(
            "Grid",
            {},
            {"columns": {"desktop": 4, "mobile": 1}},
            {"responsive_design_enabled": False},
        )
    with pytest.raises(ValueError, match="variant"):
        validate_design_resource_constraints(
            "Section",
            {"variant": "default"},
            {"variant": "full"},
            {"allowed_component_variants": ["narrow"]},
        )

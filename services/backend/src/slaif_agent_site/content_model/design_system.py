"""Generated design-system/v1 authority; edit design-system-v1.json instead."""

# ruff: noqa: E501 -- the embedded reviewed source is deterministic.

from __future__ import annotations

import json
from typing import Any, cast

from .component_catalog import component_definition, validate_component_props

DESIGN_SYSTEM_VERSION = "design-system/v1"
CATALOG_VERSION = "catalog-v1"
COMPOSITION_SCHEMA_VERSION = "site-composition/v1"
RENDERER_VERSION = "renderer-v1"
RESPONSIVE_LABELS = ("desktop", "tablet", "mobile")
RESPONSIVE_SCOPE = "responsive-design:write"

_DESIGN_SYSTEM_JSON = '{"catalog_version":"catalog-v1","components":[{"properties":[{"default":"default","name":"variant","required":false,"responsive":true,"scope":"component-variant:write","token":"variant","type":"enum","values":["default","full","narrow"]},{"default":"stretch","name":"alignment","required":false,"responsive":true,"scope":"layout:write","token":"alignment","type":"enum","values":["start","center","end","stretch"]}],"type":"Section","variants":["default","full","narrow"]},{"properties":[{"default":"md","name":"width","required":false,"responsive":true,"scope":"layout:write","token":"width","type":"enum","values":["sm","md","lg","xl"]},{"default":"stretch","name":"alignment","required":false,"responsive":true,"scope":"layout:write","token":"alignment","type":"enum","values":["start","center","end","stretch"]}],"type":"Container","variants":[]},{"properties":[{"default":1,"maximum":4,"minimum":1,"name":"count","required":true,"responsive":true,"scope":"layout:write","token":"columns","type":"number"},{"default":"md","name":"gap","required":false,"responsive":true,"scope":"layout:write","token":"gap","type":"enum","values":["none","sm","md","lg"]},{"default":"stretch","name":"alignment","required":false,"responsive":true,"scope":"layout:write","token":"alignment","type":"enum","values":["start","center","end","stretch"]}],"type":"Columns","variants":[]},{"properties":[{"default":1,"maximum":12,"minimum":1,"name":"columns","required":false,"responsive":true,"scope":"layout:write","token":"columns","type":"number"},{"default":"md","name":"gap","required":false,"responsive":true,"scope":"layout:write","token":"gap","type":"enum","values":["sm","md","lg"]},{"default":"stretch","name":"alignment","required":false,"responsive":true,"scope":"layout:write","token":"alignment","type":"enum","values":["start","center","end","stretch"]}],"type":"Grid","variants":[]},{"properties":[{"default":"vertical","name":"direction","required":false,"responsive":true,"scope":"layout:write","token":"direction","type":"enum","values":["vertical","horizontal"]},{"default":"md","name":"gap","required":false,"responsive":true,"scope":"layout:write","token":"gap","type":"enum","values":["none","sm","md","lg"]},{"default":"stretch","name":"alignment","required":false,"responsive":true,"scope":"layout:write","token":"alignment","type":"enum","values":["start","center","end","stretch"]}],"type":"Stack","variants":[]},{"properties":[{"default":"md","name":"size","required":true,"responsive":true,"scope":"layout:write","token":"spacing","type":"enum","values":["xs","sm","md","lg","xl"]}],"type":"Spacer","variants":[]},{"properties":[{"default":"start","name":"alignment","required":false,"responsive":true,"scope":"layout:write","token":"alignment","type":"enum","values":["start","center","end","stretch"]}],"type":"Heading","variants":[]},{"properties":[],"type":"RichText","variants":[]},{"properties":[],"type":"Image","variants":[]},{"properties":[],"type":"Button","variants":[]},{"properties":[],"type":"Quote","variants":[]},{"properties":[],"type":"CollectionList","variants":[]},{"properties":[],"type":"CollectionGrid","variants":[]},{"properties":[],"type":"CollectionDetail","variants":[]},{"properties":[],"type":"Hero","variants":[]},{"properties":[],"type":"Statistics","variants":[]},{"properties":[],"type":"Timeline","variants":[]},{"properties":[],"type":"FAQ","variants":[]},{"properties":[],"type":"Header","variants":[]},{"properties":[],"type":"Footer","variants":[]},{"properties":[],"type":"Breadcrumbs","variants":[]},{"properties":[],"type":"LanguageSwitcher","variants":[]}],"composition_schema_version":"site-composition/v1","renderer_version":"renderer-v1","responsive_fallback":["desktop","tablet","mobile"],"responsive_labels":["desktop","tablet","mobile"],"responsive_scope":"responsive-design:write","tokens":{"alignment":["start","center","end","stretch"],"aspect_ratio":["auto","16:9","4:3","1:1"],"columns":[1,2,3,4,5,6,7,8,9,10,11,12],"gap":["none","sm","md","lg"],"radius":["none","sm","md","lg","full"],"shadow":["none","sm","md","lg"],"spacing":["none","xs","sm","md","lg","xl"],"width":["sm","md","lg","xl"]},"version":"design-system/v1"}'
DESIGN_SYSTEM_DOCUMENT: dict[str, Any] = json.loads(_DESIGN_SYSTEM_JSON)
_COMPONENTS = {item["type"]: item for item in DESIGN_SYSTEM_DOCUMENT["components"]}
_PROPERTIES = {
    (component_type, prop["name"]): prop
    for component_type, component in _COMPONENTS.items()
    for prop in component["properties"]
}


def design_system_document() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_DESIGN_SYSTEM_JSON))


def design_property(component_type: str, name: str) -> dict[str, Any] | None:
    value = _PROPERTIES.get((component_type, name))
    return dict(value) if value is not None else None


def _property_required_scopes(prop: dict[str, Any]) -> list[str]:
    result = [prop["scope"]]
    if prop["responsive"]:
        result.append(RESPONSIVE_SCOPE)
    return result


def design_scope_metadata() -> list[dict[str, Any]]:
    """Return deterministic property-level scope metadata for Agent OpenAPI."""
    return [
        {
            "component_type": component["type"],
            "property": prop["name"],
            "required_scopes": _property_required_scopes(prop),
        }
        for component in DESIGN_SYSTEM_DOCUMENT["components"]
        for prop in component["properties"]
    ]


def is_responsive_value(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and 1 <= len(value) <= len(RESPONSIVE_LABELS)
        and set(value) <= set(RESPONSIVE_LABELS)
    )


def _normalize_responsive(value: dict[str, Any]) -> dict[str, Any]:
    if not is_responsive_value(value):
        raise ValueError("responsive value")
    return {label: value[label] for label in RESPONSIVE_LABELS if label in value}


def _collapsed(props: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for key, value in props.items():
        if key == "alignment":
            continue
        if is_responsive_value(value):
            result[key] = next(
                value[label] for label in RESPONSIVE_LABELS if label in value
            )
        else:
            result[key] = value
    return result


def _validate_alignment(value: Any) -> None:
    allowed = {"start", "center", "end", "stretch"}
    if isinstance(value, str) and value in allowed:
        return
    raise ValueError("alignment")


def required_scopes_for_component_update(
    component_type: str, old_props: dict[str, Any], patch_props: dict[str, Any]
) -> tuple[str, ...]:
    """Derive scopes from changed trusted properties, never caller labels."""
    definition = component_definition(component_type)
    result: list[str] = []
    changed = False
    for key, value in patch_props.items():
        if old_props.get(key) == value:
            continue
        changed = True
        property_definition = design_property(component_type, key)
        if property_definition is not None:
            scope = property_definition["scope"]
            if scope not in result:
                result.append(scope)
            if is_responsive_value(value) and RESPONSIVE_SCOPE not in result:
                result.append(RESPONSIVE_SCOPE)
            continue
        catalog_property = definition.props.get(key)
        if catalog_property is None or catalog_property.authority == "content":
            if "component-content-props:write" not in result:
                result.append("component-content-props:write")
        else:
            if "component-props:write" not in result:
                result.append("component-props:write")
    if not changed and "component-content-props:write" not in result:
        result.append("component-content-props:write")
    return tuple(result)


def validate_design_resource_constraints(
    component_type: str,
    old_props: dict[str, Any],
    patch_props: dict[str, Any],
    constraints: dict[str, Any],
) -> None:
    """Reject design choices outside the immutable capability resource bounds."""
    allowed_variants = constraints.get("allowed_component_variants")
    responsive_enabled = constraints.get("responsive_design_enabled", True)
    for key, value in patch_props.items():
        if old_props.get(key) == value:
            continue
        property_definition = design_property(component_type, key)
        if property_definition is None:
            continue
        if responsive_enabled is False and is_responsive_value(value):
            raise ValueError("responsive design resource constraint")
        if key == "variant" and isinstance(allowed_variants, list):
            allowed = {str(item) for item in allowed_variants}
            values = value.values() if is_responsive_value(value) else (value,)
            if any(str(item) not in allowed for item in values):
                raise ValueError("component variant resource constraint")


def validate_agent_component_props(
    component_type: str, old_props: dict[str, Any], patch_props: dict[str, Any]
) -> dict[str, Any]:
    """Validate the complete merged Agent composition props with design maps."""
    definition = component_definition(component_type)
    merged = {**old_props, **patch_props}
    normalized = dict(merged)
    for key, value in patch_props.items():
        property_definition = design_property(component_type, key)
        catalog_property = definition.props.get(key)
        if property_definition is not None:
            if is_responsive_value(value):
                normalized[key] = _normalize_responsive(value)
            continue
        if catalog_property is not None and catalog_property.authority == "design":
            raise ValueError("unsupported design prop")
    for key, value in normalized.items():
        property_definition = design_property(component_type, key)
        if property_definition is None:
            continue
        if is_responsive_value(value):
            for leaf in value.values():
                if key == "alignment":
                    _validate_alignment(leaf)
                else:
                    candidate = _collapsed(normalized)
                    candidate[key] = leaf
                    validate_component_props(
                        component_type, candidate, allow_design=True
                    )
        elif key == "alignment":
            _validate_alignment(value)
    validate_component_props(
        component_type,
        _collapsed(normalized),
        allow_design=True,
    )
    return normalized


__all__ = [
    "CATALOG_VERSION",
    "COMPOSITION_SCHEMA_VERSION",
    "DESIGN_SYSTEM_DOCUMENT",
    "DESIGN_SYSTEM_VERSION",
    "RENDERER_VERSION",
    "RESPONSIVE_LABELS",
    "RESPONSIVE_SCOPE",
    "design_property",
    "design_scope_metadata",
    "design_system_document",
    "is_responsive_value",
    "required_scopes_for_component_update",
    "validate_design_resource_constraints",
    "validate_agent_component_props",
]

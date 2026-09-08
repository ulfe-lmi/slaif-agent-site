"""Generate and validate the cross-runtime design-system/v1 authority."""

# ruff: noqa: E501 -- generated source template remains directly auditable.

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages/component-catalog/src/design-system-v1.json"
CATALOG_SOURCE = ROOT / "packages/component-catalog/src/catalog-v1.json"
PYTHON_TARGET = ROOT / (
    "services/backend/src/slaif_agent_site/content_model/design_system.py"
)
COMPOSITION_TARGET = ROOT / "packages/composition-schema/src/design-system-v1.json"

_ALLOWED_SCOPES = {
    "component-props:write",
    "component-variant:write",
    "layout:write",
}
_FORBIDDEN_TEXT = (
    "javascript:",
    "vbscript:",
    "<script",
    "selector",
    "media query",
    "font url",
)
_UNSUPPORTED_CATALOG_DESIGN_PROPERTIES = {("Section", "background")}
_DESIGN_SYSTEM_ONLY_PROPERTIES = {
    ("Section", "alignment"),
    ("Container", "alignment"),
    ("Columns", "alignment"),
    ("Grid", "alignment"),
    ("Stack", "alignment"),
    ("Heading", "alignment"),
}


def _document() -> dict[str, Any]:
    value = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("design system source must be an object")
    required = {
        "version",
        "catalog_version",
        "composition_schema_version",
        "renderer_version",
        "responsive_labels",
        "responsive_scope",
        "responsive_fallback",
        "tokens",
        "components",
    }
    if set(value) != required:
        raise ValueError("design system source keys are not exact")
    if value["version"] != "design-system/v1":
        raise ValueError("design system version is not exact")
    if value["catalog_version"] != "catalog-v1":
        raise ValueError("design system catalog binding is not exact")
    if value["composition_schema_version"] != "site-composition/v1":
        raise ValueError("design system composition binding is not exact")
    labels = value["responsive_labels"]
    if labels != ["desktop", "tablet", "mobile"]:
        raise ValueError("responsive labels are not exact")
    if value["responsive_scope"] != "responsive-design:write":
        raise ValueError("responsive scope is not exact")
    if value["responsive_fallback"] != labels:
        raise ValueError("responsive fallback is not exact")
    if not isinstance(value["tokens"], dict) or not isinstance(
        value["components"], list
    ):
        raise ValueError("design system collections are malformed")
    catalog = json.loads(CATALOG_SOURCE.read_text(encoding="utf-8"))
    catalog_types = [item["type"] for item in catalog["components"]]
    design_types = [item["type"] for item in value["components"]]
    if design_types != catalog_types:
        raise ValueError("design system component inventory is not catalog-v1 exact")
    catalog_by_type = {item["type"]: item for item in catalog["components"]}
    design_by_type = {item["type"]: item for item in value["components"]}
    for component in value["components"]:
        if not isinstance(component, dict) or set(component) != {
            "type",
            "variants",
            "properties",
        }:
            raise ValueError("design component descriptor is malformed")
        if not isinstance(component["properties"], list):
            raise ValueError("design property collection is malformed")
        for prop in component["properties"]:
            if not isinstance(prop, dict) or set(prop) < {
                "name",
                "type",
                "default",
                "required",
                "responsive",
                "scope",
                "token",
            }:
                raise ValueError("design property descriptor is malformed")
            if prop["scope"] not in _ALLOWED_SCOPES:
                raise ValueError("design property scope is not delegatable")
            if prop["responsive"] is not True:
                raise ValueError("design properties must declare responsiveness")
            catalog_prop = catalog_by_type[component["type"]]["props"].get(prop["name"])
            if catalog_prop is None:
                if (
                    component["type"],
                    prop["name"],
                ) not in _DESIGN_SYSTEM_ONLY_PROPERTIES:
                    raise ValueError(
                        "design property is not catalog-v1 or approved extension"
                    )
                continue
            if prop["type"] != catalog_prop["type"]:
                raise ValueError("design property type disagrees with catalog-v1")
            if prop["type"] == "enum" and prop.get("values") != catalog_prop.get(
                "enum_values", []
            ):
                raise ValueError("design property enum disagrees with catalog-v1")
            if prop["type"] == "number" and (
                prop.get("minimum") != catalog_prop.get("minimum")
                or prop.get("maximum") != catalog_prop.get("maximum")
            ):
                raise ValueError("design property bounds disagree with catalog-v1")
    for component in catalog["components"]:
        design_names = {
            prop["name"] for prop in design_by_type[component["type"]]["properties"]
        }
        for name, prop in component["props"].items():
            if (
                prop.get("authority") == "design"
                and name not in design_names
                and (component["type"], name)
                not in _UNSUPPORTED_CATALOG_DESIGN_PROPERTIES
            ):
                raise ValueError("catalog design property lacks design authority")
    encoded = json.dumps(value, ensure_ascii=False).casefold()
    if any(marker in encoded for marker in _FORBIDDEN_TEXT):
        raise ValueError("design system contains an unsafe editable primitive")
    return value


def _python_source(document: dict[str, Any]) -> str:
    encoded = json.dumps(
        document, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    return f'''"""Generated design-system/v1 authority; edit design-system-v1.json instead."""

# ruff: noqa: E501 -- the embedded reviewed source is deterministic.

from __future__ import annotations

import json
from typing import Any, cast

from .component_catalog import (
    COMPONENT_CATALOG,
    component_definition,
    validate_component_props,
)

DESIGN_SYSTEM_VERSION = "design-system/v1"
CATALOG_VERSION = "catalog-v1"
COMPOSITION_SCHEMA_VERSION = "site-composition/v1"
RENDERER_VERSION = "renderer-v1"
RESPONSIVE_LABELS = ("desktop", "tablet", "mobile")
RESPONSIVE_SCOPE = "responsive-design:write"

_DESIGN_SYSTEM_JSON = {encoded!r}
DESIGN_SYSTEM_DOCUMENT: dict[str, Any] = json.loads(_DESIGN_SYSTEM_JSON)
_COMPONENTS = {{item["type"]: item for item in DESIGN_SYSTEM_DOCUMENT["components"]}}
_PROPERTIES = {{
    (component_type, prop["name"]): prop
    for component_type, component in _COMPONENTS.items()
    for prop in component["properties"]
}}


def design_system_document() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_DESIGN_SYSTEM_JSON))


def design_property(component_type: str, name: str) -> dict[str, Any] | None:
    value = _PROPERTIES.get((component_type, name))
    return dict(value) if value is not None else None


def component_property_scope_metadata() -> list[dict[str, Any]]:
    """Return the exact scalar/responsive scope for every catalog property."""
    result: list[dict[str, Any]] = []
    for component in COMPONENT_CATALOG:
        design_component = _COMPONENTS[component.type]
        design_names = [prop["name"] for prop in design_component["properties"]]
        property_names = list(component.props)
        property_names.extend(
            name for name in design_names if name not in component.props
        )
        for name in property_names:
            catalog_property = component.props.get(name)
            design = design_property(component.type, name)
            if design is not None:
                scalar_scopes = [design["scope"]]
                responsive = bool(design["responsive"])
                responsive_scopes = [RESPONSIVE_SCOPE] if responsive else []
                supported = True
            elif (
                catalog_property is not None and catalog_property.authority == "design"
            ):
                scalar_scopes = []
                responsive = False
                responsive_scopes = []
                supported = False
            else:
                scalar_scopes = ["component-content-props:write"]
                responsive = False
                responsive_scopes = []
                supported = True
            result.append(
                {{
                    "component_type": component.type,
                    "property": name,
                    "supported": supported,
                    "scalar_required_scopes": scalar_scopes,
                    "responsive": responsive,
                    "responsive_required_scopes": responsive_scopes,
                }}
            )
    return result


def component_property_scope(component_type: str, name: str) -> dict[str, Any] | None:
    for item in component_property_scope_metadata():
        if item["component_type"] == component_type and item["property"] == name:
            return dict(item)
    return None


def design_scope_metadata() -> list[dict[str, Any]]:
    """Return deterministic property-level design scope metadata."""
    return [
        item
        for item in component_property_scope_metadata()
        if item["supported"]
        and item["scalar_required_scopes"] != ["component-content-props:write"]
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
    return {{label: value[label] for label in RESPONSIVE_LABELS if label in value}}


def _collapsed(props: dict[str, Any]) -> dict[str, Any]:
    result = {{}}
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
    allowed = {{"start", "center", "end", "stretch"}}
    if isinstance(value, str) and value in allowed:
        return
    raise ValueError("alignment")


def required_scopes_for_component_update(
    component_type: str, old_props: dict[str, Any], patch_props: dict[str, Any]
) -> tuple[str, ...]:
    """Derive scopes from changed trusted properties, never caller labels."""
    result: list[str] = []
    for key, value in patch_props.items():
        if old_props.get(key) == value:
            continue
        property_scope = component_property_scope(component_type, key)
        if property_scope is None:
            raise ValueError("unknown prop")
        if not property_scope["supported"]:
            raise ValueError("unsupported design prop")
        for scope in property_scope["scalar_required_scopes"]:
            if scope not in result:
                result.append(scope)
        if property_scope["responsive"] and is_responsive_value(value):
            for scope in property_scope["responsive_required_scopes"]:
                if scope not in result:
                    result.append(scope)
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
            allowed = {{str(item) for item in allowed_variants}}
            values = value.values() if is_responsive_value(value) else (value,)
            if any(str(item) not in allowed for item in values):
                raise ValueError("component variant resource constraint")


def validate_agent_component_props(
    component_type: str, old_props: dict[str, Any], patch_props: dict[str, Any]
) -> dict[str, Any]:
    """Validate the complete merged Agent composition props with design maps."""
    definition = component_definition(component_type)
    merged = {{**old_props, **patch_props}}
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
            if not property_definition["responsive"]:
                raise ValueError("responsive prop")
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
    "component_property_scope",
    "component_property_scope_metadata",
    "design_property",
    "design_scope_metadata",
    "design_system_document",
    "is_responsive_value",
    "required_scopes_for_component_update",
    "validate_design_resource_constraints",
    "validate_agent_component_props",
]
'''


def generate() -> bytes:
    return _python_source(_document()).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="generate_design_system")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = generate()
    if args.check:
        if (
            not PYTHON_TARGET.is_file()
            or PYTHON_TARGET.read_bytes() != generated
            or not COMPOSITION_TARGET.is_file()
            or COMPOSITION_TARGET.read_bytes() != SOURCE.read_bytes()
        ):
            raise SystemExit("design-system: generated source drift")
        print("design-system: OK")
        return 0
    PYTHON_TARGET.write_bytes(generated)
    COMPOSITION_TARGET.write_bytes(SOURCE.read_bytes())
    print(
        "design-system: WROTE "
        f"{PYTHON_TARGET.relative_to(ROOT)} and {COMPOSITION_TARGET.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

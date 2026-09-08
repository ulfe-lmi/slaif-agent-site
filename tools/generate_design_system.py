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

from .component_catalog import component_definition, validate_component_props

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


def _property_required_scopes(prop: dict[str, Any]) -> list[str]:
    result = [prop["scope"]]
    if prop["responsive"]:
        result.append(RESPONSIVE_SCOPE)
    return result


def design_scope_metadata() -> list[dict[str, Any]]:
    """Return deterministic property-level scope metadata for Agent OpenAPI."""
    return [
        {{
            "component_type": component["type"],
            "property": prop["name"],
            "required_scopes": _property_required_scopes(prop),
        }}
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

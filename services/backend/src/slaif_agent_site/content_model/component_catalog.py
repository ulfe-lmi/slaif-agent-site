"""Generated catalog-v1 authority; edit catalog-v1.json instead."""

# ruff: noqa: E501 -- the embedded reviewed source is deterministic.

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, cast
from urllib.parse import urlsplit
from uuid import UUID

from .models import _bounded_json

COMPONENT_CATALOG_VERSION = "catalog-v1"
COMPOSITION_SCHEMA_VERSION = "site-composition/v1"
MAX_COMPONENTS_PER_PAGE = 128
MAX_COMPONENT_DEPTH = 16
MAX_COMPONENT_PROPS_BYTES = 16_384

_CATALOG_JSON = '{"components":[{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":32,"props":{"background":{"authority":"design","localized":false,"max_length":4096,"required":false,"type":"string"},"variant":{"authority":"design","enum_values":["default","full","narrow"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Section"},{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":16,"props":{"width":{"authority":"design","enum_values":["sm","md","lg","xl"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Container"},{"allowed_slots":["col-1","col-2","col-3","col-4"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":4,"props":{"count":{"authority":"design","localized":false,"maximum":4,"minimum":1,"required":true,"type":"number"},"gap":{"authority":"design","enum_values":["none","sm","md","lg"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Columns"},{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":24,"props":{"columns":{"authority":"design","localized":false,"maximum":12,"minimum":1,"required":false,"type":"number"},"gap":{"authority":"design","enum_values":["sm","md","lg"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Grid"},{"allowed_slots":["default"],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":16,"props":{"direction":{"authority":"design","enum_values":["vertical","horizontal"],"localized":false,"required":false,"type":"enum"},"gap":{"authority":"design","enum_values":["none","sm","md","lg"],"localized":false,"required":false,"type":"enum"}},"schema_version":"1","type":"Stack"},{"allowed_slots":[],"authority_class":"structure","binding_kind":"none","category":"layout","max_children":0,"props":{"size":{"authority":"design","enum_values":["xs","sm","md","lg","xl"],"localized":false,"required":true,"type":"enum"}},"schema_version":"1","type":"Spacer"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"level":{"authority":"content","localized":false,"maximum":6,"minimum":1,"required":true,"type":"number"},"text":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"}},"schema_version":"1","type":"Heading"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"content":{"authority":"content","localized":true,"required":true,"schema":{"additional_properties":false,"properties":{"children":{"items":{"additional_properties":false,"properties":{"bold":{"required":false,"type":"boolean"},"italic":{"required":false,"type":"boolean"},"text":{"max_length":4096,"required":true,"type":"string"}},"required":["text"],"type":"object"},"max_items":64,"min_items":1,"required":true,"type":"array"},"type":{"enum_values":["paragraph","heading","quote"],"required":true,"type":"enum"}},"required":["type","children"],"type":"object"},"type":"object"}},"schema_version":"1","type":"RichText"},{"allowed_slots":[],"authority_class":"content","binding_kind":"media_asset","category":"basic","max_children":0,"props":{"alt":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"},"aspectRatio":{"authority":"content","enum_values":["auto","16:9","4:3","1:1"],"required":false,"type":"enum"},"mediaId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"Image"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"href":{"authority":"content","max_length":4096,"required":true,"type":"string"},"label":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"},"variant":{"authority":"content","enum_values":["primary","secondary","ghost"],"required":false,"type":"enum"}},"schema_version":"1","type":"Button"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"basic","max_children":0,"props":{"attribution":{"authority":"content","localized":true,"max_length":4096,"required":false,"type":"string"},"text":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"}},"schema_version":"1","type":"Quote"},{"allowed_slots":["item"],"authority_class":"content","binding_kind":"collection_view","category":"data","max_children":0,"props":{"limit":{"authority":"content","maximum":100,"minimum":1,"required":false,"type":"number"},"viewId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"CollectionList"},{"allowed_slots":["item"],"authority_class":"content","binding_kind":"collection_view","category":"data","max_children":0,"props":{"columns":{"authority":"content","maximum":6,"minimum":1,"required":false,"type":"number"},"viewId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"CollectionGrid"},{"allowed_slots":[],"authority_class":"content","binding_kind":"collection_view","category":"data","max_children":0,"props":{"viewId":{"authority":"content","format":"uuid","required":true,"type":"reference"}},"schema_version":"1","type":"CollectionDetail"},{"allowed_slots":["content"],"authority_class":"content","binding_kind":"media_asset","category":"institutional","max_children":8,"props":{"heading":{"authority":"content","localized":true,"max_length":4096,"required":true,"type":"string"},"mediaId":{"authority":"content","format":"uuid","required":false,"type":"reference"},"subheading":{"authority":"content","localized":true,"max_length":4096,"required":false,"type":"string"}},"schema_version":"1","type":"Hero"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"institutional","max_children":0,"props":{"items":{"authority":"content","max_items":64,"min_items":1,"required":true,"schema":{"items":{"additional_properties":false,"properties":{"label":{"max_length":256,"required":true,"type":"string"},"value":{"max_length":256,"required":true,"type":"string"}},"required":["label","value"],"type":"object"},"max_items":64,"min_items":1,"type":"array"},"type":"array"}},"schema_version":"1","type":"Statistics"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"institutional","max_children":0,"props":{"items":{"authority":"content","max_items":64,"min_items":1,"required":true,"schema":{"items":{"additional_properties":false,"properties":{"description":{"max_length":4096,"required":true,"type":"string"},"title":{"max_length":256,"required":true,"type":"string"}},"required":["title","description"],"type":"object"},"max_items":64,"min_items":1,"type":"array"},"type":"array"}},"schema_version":"1","type":"Timeline"},{"allowed_slots":[],"authority_class":"content","binding_kind":"none","category":"institutional","max_children":0,"props":{"items":{"authority":"content","max_items":64,"min_items":1,"required":true,"schema":{"items":{"additional_properties":false,"properties":{"answer":{"max_length":4096,"required":true,"type":"string"},"question":{"max_length":4096,"required":true,"type":"string"}},"required":["question","answer"],"type":"object"},"max_items":64,"min_items":1,"type":"array"},"type":"array"}},"schema_version":"1","type":"FAQ"},{"allowed_slots":["nav"],"authority_class":"global","binding_kind":"none","category":"global","max_children":12,"props":{},"schema_version":"1","type":"Header"},{"allowed_slots":["links"],"authority_class":"global","binding_kind":"none","category":"global","max_children":16,"props":{},"schema_version":"1","type":"Footer"},{"allowed_slots":[],"authority_class":"global","binding_kind":"none","category":"global","max_children":0,"props":{},"schema_version":"1","type":"Breadcrumbs"},{"allowed_slots":[],"authority_class":"global","binding_kind":"none","category":"global","max_children":0,"props":{},"schema_version":"1","type":"LanguageSwitcher"}],"composition_schema_version":"site-composition/v1","version":"catalog-v1"}'
CATALOG_DOCUMENT: dict[str, Any] = json.loads(_CATALOG_JSON)

PropType = Literal[
    "string", "number", "boolean", "enum", "reference", "object", "array"
]
PropAuthority = Literal["content", "design"]
BindingKind = Literal["none", "collection_view", "media_asset"]


@dataclass(frozen=True, slots=True)
class ComponentProp:
    type: PropType
    required: bool = False
    enum_values: tuple[str, ...] = ()
    minimum: int | float | None = None
    maximum: int | float | None = None
    localized: bool = False
    authority: PropAuthority = "content"
    schema: dict[str, Any] | None = None
    max_length: int | None = None
    format: str | None = None


@dataclass(frozen=True, slots=True)
class ComponentDefinition:
    type: str
    category: Literal["layout", "basic", "data", "institutional", "global"]
    schema_version: str
    allowed_slots: tuple[str, ...]
    max_children: int
    props: MappingProxyType[str, ComponentProp]
    binding_kind: BindingKind = "none"
    authority_class: Literal["content", "structure", "global"] = "content"


def _build_prop(value: dict[str, Any]) -> ComponentProp:
    return ComponentProp(
        type=value["type"],
        required=value.get("required", False),
        enum_values=tuple(value.get("enum_values", [])),
        minimum=value.get("minimum"),
        maximum=value.get("maximum"),
        localized=value.get("localized", False),
        authority=value.get("authority", "content"),
        schema=value.get("schema"),
        max_length=value.get("max_length"),
        format=value.get("format"),
    )


def _build_component(value: dict[str, Any]) -> ComponentDefinition:
    return ComponentDefinition(
        type=value["type"],
        category=value["category"],
        schema_version=value["schema_version"],
        allowed_slots=tuple(value["allowed_slots"]),
        max_children=value["max_children"],
        props=MappingProxyType(
            {key: _build_prop(prop) for key, prop in value["props"].items()}
        ),
        binding_kind=value["binding_kind"],
        authority_class=value["authority_class"],
    )


COMPONENT_CATALOG = tuple(
    _build_component(item) for item in CATALOG_DOCUMENT["components"]
)
COMPONENT_BY_TYPE = MappingProxyType({item.type: item for item in COMPONENT_CATALOG})
TRUSTED_COMPONENT_TYPES = frozenset(COMPONENT_BY_TYPE)

_FORBIDDEN_KEYS = frozenset(
    {
        "__proto__",
        "constructor",
        "prototype",
        "innerhtml",
        "dangerouslysetinnerhtml",
        "style",
        "class",
        "classname",
        "onclick",
        "onload",
        "handler",
        "script",
        "eval",
        "html",
        "template",
        "query",
        "code",
        "package",
        "callback",
    }
)


def component_definition(component_type: str) -> ComponentDefinition:
    try:
        return COMPONENT_BY_TYPE[component_type]
    except KeyError:
        raise ValueError("unknown component type") from None


def _validate_nested(value: Any, *, depth: int = 0) -> None:
    if depth > 8:
        raise ValueError("props depth exceeded")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or key.casefold() in _FORBIDDEN_KEYS:
                raise ValueError("executable prop")
            _validate_nested(child, depth=depth + 1)
    elif isinstance(value, list):
        for child in value:
            _validate_nested(child, depth=depth + 1)
    elif isinstance(value, str):
        lowered = value.casefold()
        if lowered.startswith(("javascript:", "data:", "file:", "vbscript:")) or any(
            marker in lowered for marker in ("<script", "onerror=", "onload=")
        ):
            raise ValueError("unsafe value")


def _validate_schema(value: Any, schema: dict[str, Any]) -> None:
    kind = schema.get("type")
    if kind == "string":
        if not isinstance(value, str):
            raise ValueError("prop type")
        if schema.get("max_length") is not None and len(value) > schema["max_length"]:
            raise ValueError("prop bound")
    elif kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("prop type")
        if schema.get("minimum") is not None and value < schema["minimum"]:
            raise ValueError("prop bound")
        if schema.get("maximum") is not None and value > schema["maximum"]:
            raise ValueError("prop bound")
    elif kind == "boolean":
        if not isinstance(value, bool):
            raise ValueError("prop type")
    elif kind == "enum":
        if value not in schema.get("enum_values", []):
            raise ValueError("prop enum")
    elif kind == "reference":
        try:
            UUID(str(value))
        except (TypeError, ValueError):
            raise ValueError("prop reference") from None
    elif kind == "object":
        if not isinstance(value, dict):
            raise ValueError("prop type")
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if any(key not in value for key in required):
            raise ValueError("nested prop required")
        if schema.get("additional_properties") is False and set(value) - set(
            properties
        ):
            raise ValueError("nested prop unknown")
        for key, child in value.items():
            if key in properties:
                _validate_schema(child, properties[key])
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError("prop type")
        if schema.get("min_items") is not None and len(value) < schema["min_items"]:
            raise ValueError("prop bound")
        if schema.get("max_items") is not None and len(value) > schema["max_items"]:
            raise ValueError("prop bound")
        item_schema = schema.get("items")
        if item_schema is not None:
            for child in value:
                _validate_schema(child, item_schema)


def validate_component_props(
    component_type: str,
    props: dict[str, Any],
    *,
    allow_design: bool = False,
    partial: bool = False,
) -> dict[str, Any]:
    definition = component_definition(component_type)
    if not isinstance(props, dict):
        raise ValueError("props must be an object")
    bounded = _bounded_json(props)
    if not isinstance(bounded, dict):
        raise ValueError("props must be an object")
    if set(bounded) - set(definition.props):
        raise ValueError("unknown prop")
    if not partial:
        missing = [
            key
            for key, rule in definition.props.items()
            if rule.required and key not in bounded
        ]
        if missing:
            raise ValueError("missing prop")
    for key, value in bounded.items():
        rule = definition.props[key]
        if rule.authority == "design" and not allow_design:
            raise ValueError("design prop")
        if rule.schema is not None:
            _validate_schema(value, rule.schema)
        elif rule.type == "string" and not isinstance(value, str):
            raise ValueError("prop type")
        elif rule.type == "number" and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise ValueError("prop type")
        elif rule.type == "boolean" and not isinstance(value, bool):
            raise ValueError("prop type")
        elif rule.type == "enum" and value not in rule.enum_values:
            raise ValueError("prop enum")
        elif rule.type == "reference":
            try:
                UUID(str(value))
            except (TypeError, ValueError):
                raise ValueError("prop reference") from None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if rule.minimum is not None and value < rule.minimum:
                raise ValueError("prop bound")
            if rule.maximum is not None and value > rule.maximum:
                raise ValueError("prop bound")
        if (
            isinstance(value, str)
            and rule.max_length is not None
            and len(value) > rule.max_length
        ):
            raise ValueError("prop bound")
    if component_type == "Button":
        href = bounded.get("href")
        if isinstance(href, str):
            parts = urlsplit(href)
            if (
                href.startswith("//")
                or (parts.scheme and parts.scheme not in {"http", "https"})
                or not href.startswith("/")
            ):
                raise ValueError("unsafe value")
    _validate_nested(bounded)
    if (
        len(json.dumps(bounded, separators=(",", ":"), ensure_ascii=True))
        > MAX_COMPONENT_PROPS_BYTES
    ):
        raise ValueError("props too large")
    return bounded


def catalog_document() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(_CATALOG_JSON))


__all__ = [
    "CATALOG_DOCUMENT",
    "COMPONENT_CATALOG",
    "COMPONENT_CATALOG_VERSION",
    "COMPONENT_BY_TYPE",
    "COMPOSITION_SCHEMA_VERSION",
    "MAX_COMPONENT_DEPTH",
    "MAX_COMPONENT_PROPS_BYTES",
    "MAX_COMPONENTS_PER_PAGE",
    "TRUSTED_COMPONENT_TYPES",
    "catalog_document",
    "component_definition",
    "validate_component_props",
]

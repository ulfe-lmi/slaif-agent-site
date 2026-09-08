"""The trusted, versioned component catalog used by Agent and Render."""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import UUID

from .models import _bounded_json

COMPONENT_CATALOG_VERSION = "catalog-v1"
COMPOSITION_SCHEMA_VERSION = "site-composition/v1"
MAX_COMPONENTS_PER_PAGE = 128
MAX_COMPONENT_DEPTH = 16
MAX_COMPONENT_PROPS_BYTES = 16_384

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


def _props(**values: ComponentProp) -> MappingProxyType[str, ComponentProp]:
    return MappingProxyType(values)


def _p(
    kind: PropType,
    *,
    required: bool = False,
    enum: tuple[str, ...] = (),
    minimum: int | float | None = None,
    maximum: int | float | None = None,
    localized: bool = False,
    authority: PropAuthority = "content",
) -> ComponentProp:
    return ComponentProp(
        kind,
        required,
        enum,
        minimum,
        maximum,
        localized,
        authority,
    )


COMPONENT_CATALOG: tuple[ComponentDefinition, ...] = (
    ComponentDefinition(
        "Section",
        "layout",
        "1",
        ("default",),
        32,
        _props(
            variant=_p("enum", enum=("default", "full", "narrow"), authority="design"),
            background=_p("string", authority="design"),
        ),
        authority_class="structure",
    ),
    ComponentDefinition(
        "Container",
        "layout",
        "1",
        ("default",),
        16,
        _props(width=_p("enum", enum=("sm", "md", "lg", "xl"), authority="design")),
        authority_class="structure",
    ),
    ComponentDefinition(
        "Columns",
        "layout",
        "1",
        ("col-1", "col-2", "col-3", "col-4"),
        4,
        _props(
            count=_p("number", required=True, minimum=1, maximum=4, authority="design"),
            gap=_p("enum", enum=("none", "sm", "md", "lg"), authority="design"),
        ),
        authority_class="structure",
    ),
    ComponentDefinition(
        "Grid",
        "layout",
        "1",
        ("default",),
        24,
        _props(
            columns=_p("number", minimum=1, maximum=12, authority="design"),
            gap=_p("enum", enum=("sm", "md", "lg"), authority="design"),
        ),
        authority_class="structure",
    ),
    ComponentDefinition(
        "Stack",
        "layout",
        "1",
        ("default",),
        16,
        _props(
            direction=_p("enum", enum=("vertical", "horizontal"), authority="design"),
            gap=_p("enum", enum=("none", "sm", "md", "lg"), authority="design"),
        ),
        authority_class="structure",
    ),
    ComponentDefinition(
        "Spacer",
        "layout",
        "1",
        (),
        0,
        _props(
            size=_p(
                "enum",
                required=True,
                enum=("xs", "sm", "md", "lg", "xl"),
                authority="design",
            )
        ),
        authority_class="structure",
    ),
    ComponentDefinition(
        "Heading",
        "basic",
        "1",
        (),
        0,
        _props(
            text=_p("string", required=True, localized=True),
            level=_p("number", required=True, minimum=1, maximum=6),
        ),
    ),
    ComponentDefinition(
        "RichText",
        "basic",
        "1",
        (),
        0,
        _props(content=_p("object", required=True, localized=True)),
    ),
    ComponentDefinition(
        "Image",
        "basic",
        "1",
        (),
        0,
        _props(
            mediaId=_p("reference", required=True),
            alt=_p("string", required=True, localized=True),
            aspectRatio=_p("enum", enum=("auto", "16:9", "4:3", "1:1")),
        ),
        binding_kind="media_asset",
    ),
    ComponentDefinition(
        "Button",
        "basic",
        "1",
        (),
        0,
        _props(
            label=_p("string", required=True, localized=True),
            href=_p("string", required=True),
            variant=_p("enum", enum=("primary", "secondary", "ghost")),
        ),
    ),
    ComponentDefinition(
        "Quote",
        "basic",
        "1",
        (),
        0,
        _props(
            text=_p("string", required=True, localized=True),
            attribution=_p("string", localized=True),
        ),
    ),
    ComponentDefinition(
        "CollectionList",
        "data",
        "1",
        ("item",),
        0,
        _props(
            viewId=_p("reference", required=True),
            limit=_p("number", minimum=1, maximum=100),
        ),
        binding_kind="collection_view",
    ),
    ComponentDefinition(
        "CollectionGrid",
        "data",
        "1",
        ("item",),
        0,
        _props(
            viewId=_p("reference", required=True),
            columns=_p("number", minimum=1, maximum=6),
        ),
        binding_kind="collection_view",
    ),
    ComponentDefinition(
        "CollectionDetail",
        "data",
        "1",
        (),
        0,
        _props(viewId=_p("reference", required=True)),
        binding_kind="collection_view",
    ),
    ComponentDefinition(
        "Hero",
        "institutional",
        "1",
        ("content",),
        8,
        _props(
            heading=_p("string", required=True, localized=True),
            subheading=_p("string", localized=True),
            mediaId=_p("reference"),
        ),
        binding_kind="media_asset",
    ),
    ComponentDefinition(
        "Statistics",
        "institutional",
        "1",
        (),
        0,
        _props(items=_p("array", required=True)),
    ),
    ComponentDefinition(
        "Timeline",
        "institutional",
        "1",
        (),
        0,
        _props(items=_p("array", required=True)),
    ),
    ComponentDefinition(
        "FAQ", "institutional", "1", (), 0, _props(items=_p("array", required=True))
    ),
    ComponentDefinition(
        "Header", "global", "1", ("nav",), 12, _props(), authority_class="global"
    ),
    ComponentDefinition(
        "Footer", "global", "1", ("links",), 16, _props(), authority_class="global"
    ),
    ComponentDefinition(
        "Breadcrumbs", "global", "1", (), 0, _props(), authority_class="global"
    ),
    ComponentDefinition(
        "LanguageSwitcher", "global", "1", (), 0, _props(), authority_class="global"
    ),
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
        if lowered.startswith(("javascript:", "data:", "file:")):
            raise ValueError("unsafe value")
        if any(marker in lowered for marker in ("<script", "onerror=", "onload=")):
            raise ValueError("executable value")


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
        if rule.type == "string" and not isinstance(value, str):
            raise ValueError("prop type")
        if rule.type == "number" and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise ValueError("prop type")
        if rule.type == "boolean" and not isinstance(value, bool):
            raise ValueError("prop type")
        if rule.type == "enum" and value not in rule.enum_values:
            raise ValueError("prop enum")
        if rule.type == "reference":
            try:
                UUID(str(value))
            except (TypeError, ValueError):
                raise ValueError("prop reference") from None
        if rule.type == "object" and not isinstance(value, dict):
            raise ValueError("prop type")
        if rule.type == "array" and not isinstance(value, list):
            raise ValueError("prop type")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if rule.minimum is not None and value < rule.minimum:
                raise ValueError("prop bound")
            if rule.maximum is not None and value > rule.maximum:
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
    return {
        "version": COMPONENT_CATALOG_VERSION,
        "composition_schema_version": COMPOSITION_SCHEMA_VERSION,
        "components": [
            {
                "type": item.type,
                "category": item.category,
                "schema_version": item.schema_version,
                "allowed_slots": list(item.allowed_slots),
                "max_children": item.max_children,
                "binding_kind": item.binding_kind,
                "authority_class": item.authority_class,
                "props": {
                    key: {
                        "type": prop.type,
                        "required": prop.required,
                        "enum_values": list(prop.enum_values),
                        "minimum": prop.minimum,
                        "maximum": prop.maximum,
                        "localized": prop.localized,
                        "authority": prop.authority,
                    }
                    for key, prop in item.props.items()
                },
            }
            for item in COMPONENT_CATALOG
        ],
    }


__all__ = [
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

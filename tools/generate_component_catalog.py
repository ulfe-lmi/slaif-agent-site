"""Generate and verify the cross-runtime catalog-v1 artifacts."""

# ruff: noqa: E501 -- generated source templates remain byte-stable.

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages/component-catalog/src/catalog-v1.json"
PYTHON_TARGET = (
    ROOT / "services/backend/src/slaif_agent_site/content_model/component_catalog.py"
)
TYPESCRIPT_TARGET = ROOT / "packages/component-catalog/src/index.ts"
PUCK_CATALOG_TARGET = ROOT / "packages/composition-schema/src/catalog-v1.json"
MIGRATION_TARGET = ROOT / (
    "services/backend/src/slaif_agent_site/db/alembic/versions/"
    "060_001_agent_component_semantics.py"
)


def _document() -> dict[str, Any]:
    value = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("catalog source must be an object")
    return value


def _python_source(document: dict[str, Any]) -> str:
    encoded = json.dumps(
        document, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    return f'''"""Generated catalog-v1 authority; edit catalog-v1.json instead."""

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

_CATALOG_JSON = {encoded!r}
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
            {{key: _build_prop(prop) for key, prop in value["props"].items()}}
        ),
        binding_kind=value["binding_kind"],
        authority_class=value["authority_class"],
    )


COMPONENT_CATALOG = tuple(
    _build_component(item) for item in CATALOG_DOCUMENT["components"]
)
COMPONENT_BY_TYPE = MappingProxyType({{item.type: item for item in COMPONENT_CATALOG}})
TRUSTED_COMPONENT_TYPES = frozenset(COMPONENT_BY_TYPE)

_FORBIDDEN_KEYS = frozenset(
    {{
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
    }}
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
        properties = schema.get("properties", {{}})
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
                or (parts.scheme and parts.scheme not in {{"http", "https"}})
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
'''


def _typescript_source() -> str:
    return """/** Generated catalog-v1 authority; edit catalog-v1.json instead. */

import catalog from "./catalog-v1.json" with { type: "json" };

export interface PropSchema {
  readonly type:
    "string" | "number" | "boolean" | "enum" | "reference" | "object" | "array";
  readonly required?: boolean | readonly string[];
  readonly enum_values?: readonly string[];
  readonly minimum?: number | null;
  readonly maximum?: number | null;
  readonly min_items?: number;
  readonly max_items?: number;
  readonly max_length?: number;
  readonly format?: "uuid";
  readonly properties?: Readonly<Record<string, PropSchema>>;
  readonly required_keys?: readonly string[];
  readonly additional_properties?: boolean;
  readonly items?: PropSchema;
}

export interface PropDefinition {
  readonly type: PropSchema["type"];
  readonly required: boolean;
  readonly enumValues?: readonly string[];
  readonly bounded?: { readonly min?: number; readonly max?: number };
  readonly localized?: boolean;
  readonly authority: "content" | "design";
  readonly schema?: PropSchema;
}

export interface ComponentDefinition {
  readonly type: string;
  readonly category: "layout" | "basic" | "data" | "institutional" | "global";
  readonly schemaVersion: string;
  readonly allowedSlots: readonly string[];
  readonly maxChildren: number;
  readonly propsSchema: Readonly<Record<string, PropDefinition>>;
  readonly bindingKind: "none" | "collection_view" | "media_asset";
  readonly authorityClass: "content" | "structure" | "global";
}

interface CatalogPropInput {
  readonly type: PropSchema["type"];
  readonly required: boolean;
  readonly enum_values?: readonly string[];
  readonly minimum?: number | null;
  readonly maximum?: number | null;
  readonly localized?: boolean;
  readonly authority: "content" | "design";
  readonly schema?: Record<string, unknown>;
}

interface CatalogComponentInput {
  readonly type: string;
  readonly category: ComponentDefinition["category"];
  readonly schema_version: string;
  readonly allowed_slots: readonly string[];
  readonly max_children: number;
  readonly props: Readonly<Record<string, CatalogPropInput>>;
  readonly binding_kind: ComponentDefinition["bindingKind"];
  readonly authority_class: ComponentDefinition["authorityClass"];
}

interface CatalogDocumentInput {
  readonly version: string;
  readonly composition_schema_version: string;
  readonly components: readonly CatalogComponentInput[];
}

const catalogDocument = catalog as unknown as CatalogDocumentInput;

export const COMPONENT_CATALOG_VERSION = "catalog-v1" as const;
export const COMPOSITION_SCHEMA_VERSION = "site-composition/v1" as const;

function propSchema(value: Record<string, unknown>): PropSchema {
  const properties = value.properties as
    Record<string, Record<string, unknown>> | undefined;
  return {
    type: value.type as PropSchema["type"],
    ...(value.required === undefined
      ? {}
      : { required: value.required as boolean | readonly string[] }),
    ...(value.enum_values === undefined
      ? {}
      : { enum_values: value.enum_values as readonly string[] }),
    ...(value.minimum === undefined ? {} : { minimum: value.minimum as number | null }),
    ...(value.maximum === undefined ? {} : { maximum: value.maximum as number | null }),
    ...(value.min_items === undefined ? {} : { min_items: value.min_items as number }),
    ...(value.max_items === undefined ? {} : { max_items: value.max_items as number }),
    ...(value.max_length === undefined
      ? {}
      : { max_length: value.max_length as number }),
    ...(value.format === undefined ? {} : { format: value.format as "uuid" }),
    ...(value.additional_properties === undefined
      ? {}
      : { additional_properties: value.additional_properties as boolean }),
    ...(value.items === undefined
      ? {}
      : { items: propSchema(value.items as Record<string, unknown>) }),
    ...(properties === undefined
      ? {}
      : {
          properties: Object.fromEntries(
            Object.entries(properties).map(([key, item]) => [key, propSchema(item)]),
          ),
        }),
  };
}

export const COMPONENT_CATALOG: readonly ComponentDefinition[] =
  catalogDocument.components.map((component) => ({
    type: component.type,
    category: component.category,
    schemaVersion: component.schema_version,
    allowedSlots: component.allowed_slots,
    maxChildren: component.max_children,
    bindingKind: component.binding_kind,
    authorityClass: component.authority_class,
    propsSchema: Object.fromEntries(
      Object.entries(component.props).map(([key, prop]) => [
        key,
        {
          type: prop.type,
          required: prop.required,
          ...((prop.enum_values ?? []).length === 0
            ? {}
            : { enumValues: prop.enum_values }),
          ...(prop.minimum === null && prop.maximum === null
            ? {}
            : {
                bounded: {
                  min: prop.minimum ?? undefined,
                  max: prop.maximum ?? undefined,
                },
              }),
          ...(prop.localized ? { localized: true } : {}),
          authority: prop.authority,
          ...(prop.schema === undefined ? {} : { schema: propSchema(prop.schema) }),
        },
      ]),
    ),
  })) as unknown as readonly ComponentDefinition[];

export const COMPONENT_TYPES: ReadonlySet<string> = new Set(
  COMPONENT_CATALOG.map((component) => component.type),
);
export const FORBIDDEN_PROP_KEYS: ReadonlySet<string> = new Set([
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
]);

export function getComponent(type: string): ComponentDefinition | undefined {
  return COMPONENT_CATALOG.find((component) => component.type === type);
}

export function validateComponentType(type: string): boolean {
  return COMPONENT_TYPES.has(type);
}

export const COMPONENT_CATALOG_DOCUMENT = catalogDocument;
export * from "./design-system";
"""


def _node_document() -> dict[str, Any]:
    script = (
        "import { COMPONENT_CATALOG_DOCUMENT } from './packages/component-catalog/src/index.js'; "
        "console.log(JSON.stringify(COMPONENT_CATALOG_DOCUMENT));"
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError("TypeScript catalog is not an object")
    return value


def check() -> None:
    document = _document()
    canonical_bytes = json.dumps(
        document, sort_keys=True, separators=(",", ":")
    ).encode()
    expected_python = _python_source(document)
    expected_typescript = _typescript_source()
    if PYTHON_TARGET.read_text(encoding="utf-8") != expected_python:
        raise SystemExit(f"catalog drift: {PYTHON_TARGET}")
    if TYPESCRIPT_TARGET.read_text(encoding="utf-8") != expected_typescript:
        raise SystemExit(f"catalog drift: {TYPESCRIPT_TARGET}")
    if PUCK_CATALOG_TARGET.read_bytes() != SOURCE.read_bytes():
        raise SystemExit(f"catalog drift: {PUCK_CATALOG_TARGET}")
    if json.dumps(document, sort_keys=True, separators=(",", ":")) != json.dumps(
        __import__(
            "slaif_agent_site.content_model.component_catalog",
            fromlist=["catalog_document"],
        ).catalog_document(),
        sort_keys=True,
        separators=(",", ":"),
    ):
        raise SystemExit("catalog semantic drift: Python")
    if json.dumps(document, sort_keys=True, separators=(",", ":")) != json.dumps(
        _node_document(), sort_keys=True, separators=(",", ":")
    ):
        raise SystemExit("catalog semantic drift: TypeScript")
    migration = importlib.import_module(
        "slaif_agent_site.db.alembic.versions.060_001_agent_component_semantics"
    )
    snapshot = json.loads(migration._CATALOG_V1_JSON)
    if (
        json.dumps(document, sort_keys=True, separators=(",", ":"))
        != json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
        or migration.CATALOG_V1_REVIEWED_SHA256
        != hashlib.sha256(canonical_bytes).hexdigest()
    ):
        raise SystemExit(
            f"catalog snapshot drift: {MIGRATION_TARGET.relative_to(ROOT)}"
        )
    print("component-catalog: OK catalog-v1 Python/TypeScript semantic equality")


def write() -> None:
    document = _document()
    PYTHON_TARGET.write_text(_python_source(document), encoding="utf-8")
    TYPESCRIPT_TARGET.write_text(_typescript_source(), encoding="utf-8")
    PUCK_CATALOG_TARGET.write_bytes(SOURCE.read_bytes())
    print("component-catalog: generated Python and TypeScript artifacts")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check()
    else:
        write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

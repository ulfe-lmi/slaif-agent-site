"""Validate the deterministic theme-schema/v1 authority across runtimes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages/composition-schema/src/theme-schema-v1.json"


def _document() -> dict[str, Any]:
    value = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("theme schema source must be an object")
    if set(value) != {
        "version",
        "renderer_version",
        "compatibility_versions",
        "responsive",
        "responsive_labels",
        "groups",
    }:
        raise ValueError("theme schema source keys are not exact")
    if value["version"] != "theme-schema/v1":
        raise ValueError("theme schema version is not exact")
    if value["renderer_version"] != "renderer-v1":
        raise ValueError("theme renderer version is not exact")
    if value["compatibility_versions"] != ["theme-schema/v1", "renderer-v1"]:
        raise ValueError("theme compatibility versions are not exact")
    if value["responsive"] is not False or value["responsive_labels"] != [
        "desktop",
        "tablet",
        "mobile",
    ]:
        raise ValueError("theme responsive contract is not exact")
    groups = value["groups"]
    if not isinstance(groups, list) or [item.get("name") for item in groups] != [
        "palette",
        "typography",
        "layout",
        "shape",
    ]:
        raise ValueError("theme group inventory is not exact")
    names: set[str] = set()
    for group in groups:
        if not isinstance(group, dict) or set(group) != {"name", "tokens"}:
            raise ValueError("theme group descriptor is malformed")
        tokens = group["tokens"]
        if not isinstance(tokens, list) or not tokens:
            raise ValueError("theme token inventory is malformed")
        for token in tokens:
            if not isinstance(token, dict) or set(token) != {
                "name",
                "type",
                "values",
                "default",
                "accessibility_class",
                "responsive",
            }:
                raise ValueError("theme token descriptor is malformed")
            key = f"{group['name']}.{token['name']}"
            if key in names or token["type"] != "enum":
                raise ValueError("theme token key/type is invalid")
            names.add(key)
            values = token["values"]
            if (
                not isinstance(values, list)
                or not values
                or len(values) != len(set(values))
                or any(not isinstance(item, str) or not item for item in values)
                or token["default"] not in values
                or token["accessibility_class"] != "AA"
                or token["responsive"] is not False
            ):
                raise ValueError("theme token bounds are invalid")
    if names != {
        "palette.preset",
        "typography.family",
        "typography.scale",
        "typography.weight",
        "layout.content_width",
        "layout.spacing",
        "layout.grid_gap",
        "shape.radius",
        "shape.shadow",
    }:
        raise ValueError("theme token inventory is incomplete")
    return value


def check() -> None:
    document = _document()
    sys.path.insert(0, str(ROOT / "services/backend/src"))
    from slaif_agent_site.content_model.theme import theme_schema_document

    if theme_schema_document() != document:
        raise SystemExit("theme-schema: Python authority drift")
    print("theme-schema: OK")


def main() -> int:
    parser = argparse.ArgumentParser(prog="generate_theme_schema")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        raise SystemExit("theme-schema is source-owned; use --check")
    check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

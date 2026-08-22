"""Generate a CycloneDX-style SBOM for Python and Node dependencies.

Architecture reference: ARCHITECTURE-for-agents.md §17 (CI supply-chain).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def get_python_deps() -> list[dict[str, str]]:
    """Extract Python dependencies from uv.lock."""
    result = subprocess.run(
        ["uv", "export", "--frozen", "--format", "requirements-txt", "--no-hashes"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    deps = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split("==")
            if len(parts) == 2:
                deps.append({"name": parts[0], "version": parts[1], "type": "library"})
    return deps


def get_node_deps() -> list[dict[str, str]]:
    """Extract direct Node dependencies from package.json files."""
    deps = []
    for manifest in ROOT.rglob("package.json"):
        if "node_modules" in str(manifest):
            continue
        try:
            data = json.loads(manifest.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        for section in ("dependencies", "devDependencies"):
            for name, version in (data.get(section) or {}).items():
                deps.append(
                    {"name": name, "version": version.lstrip("^~"), "type": "library"}
                )
    return deps


def generate_sbom() -> dict[str, Any]:
    """Generate a minimal CycloneDX-compatible SBOM."""
    python_deps = get_python_deps()
    node_deps = get_node_deps()

    # Deduplicate by name+version
    seen: set[tuple[str, str]] = set()
    components = []
    for dep in python_deps + node_deps:
        key = (dep["name"], dep["version"])
        if key not in seen:
            seen.add(key)
            components.append(dep)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {"type": "application", "name": "slaif-agent-site"},
        },
        "components": [
            {
                "type": dep["type"],
                "name": dep["name"],
                "version": dep["version"],
                "purl": f"pkg:{'pypi' if dep in python_deps else 'npm'}/{dep['name']}@{dep['version']}",
            }
            for dep in sorted(components, key=lambda d: d["name"])
        ],
    }


FORBIDDEN_LICENSES = {"AGPL-3.0", "SSPL-1.0", "GPL-3.0"}


def check_forbidden_licenses(sbom: dict[str, Any]) -> list[str]:
    """Check for known non-permissive licenses in dependency metadata."""
    violations = []
    for component in sbom.get("components", []):
        name = component.get("name", "")
        for license_name in FORBIDDEN_LICENSES:
            if license_name.lower() in name.lower():
                violations.append(f"{name}: possible {license_name}")
    return violations


if __name__ == "__main__":
    sbom = generate_sbom()
    output_path = ROOT / "sbom.json"
    output_path.write_text(json.dumps(sbom, indent=2))
    print(f"SBOM written to {output_path} ({len(sbom['components'])} components)")

    violations = check_forbidden_licenses(sbom)
    if violations:
        print(f"License violations found: {violations}", file=sys.stderr)
        sys.exit(1)
    print("License check: PASS")

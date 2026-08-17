#!/usr/bin/env python3
"""Check deterministic preparation policies for the Agent-Site repository.

Usage:
    python tools/check_repository.py [--root PATH]

The checker uses only the Python standard library. It is intentionally a
focused preparation guardrail, not a complete secret scanner, YAML validator,
Markdown parser, or legal analyzer.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

LOGO_SHA256 = "0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08"
FOUNDATION_VERSION = "0.2.0"
FOUNDATION_REGISTRY = "https://pypi.org/simple"
FOUNDATION_WHEEL = "agent_cow_postgresql-0.2.0-py3-none-any.whl"
FOUNDATION_WHEEL_SHA256 = (
    "c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1"
)
FOUNDATION_SDIST = "agent_cow_postgresql-0.2.0.tar.gz"
FOUNDATION_SDIST_SHA256 = (
    "eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c"
)
PYTHON_RUNTIME_DEPENDENCIES = [
    "agent-cow-postgresql==0.2.0",
    "asyncpg==0.31.0",
    "fastapi==0.141.1",
    "pydantic==2.13.4",
    "pydantic-settings==2.15.0",
    "uvicorn==0.52.3",
]
PYTHON_DIRECT_VERSIONS = {
    "agent-cow-postgresql": "0.2.0",
    "asyncpg": "0.31.0",
    "fastapi": "0.141.1",
    "httpx": "0.28.1",
    "pydantic": "2.13.4",
    "pydantic-settings": "2.15.0",
    "uvicorn": "0.52.3",
}
PYTHON_DEPENDENCY_GROUPS = {
    "build": ["build>=1.3,<2", "uv-build==0.12.5"],
    "qualification": ["packaging>=24,<26"],
    "quality": ["mypy>=1.17,<2", "ruff>=0.12,<1"],
    "test": ["httpx==0.28.1", "pytest>=8.4,<10", "pytest-asyncio>=1.1,<2"],
}
HTTP_PROCESS_PACKAGES = {
    "agent_api": "agent-api",
    "control_api": "control-api",
    "editor_api": "editor-api",
    "mcp_adapter": "mcp-adapter",
    "media_service": "media-service",
    "render_api": "render-api",
}
WORKER_PROCESS_PACKAGES = {
    "bootstrap": "bootstrap",
    "media_gc": "media-gc",
    "review_worker": "review-worker",
    "scheduler": "scheduler",
}
BACKEND_PROCESS_VALUES = set(HTTP_PROCESS_PACKAGES.values()) | set(
    WORKER_PROCESS_PACKAGES.values()
)
PNPM_VERSION = "11.22.0"
PNPM_INTEGRITY_HEX = (
    "1ff870c4c6133dfd88fb2afc46dd13d47f09c9794b438c6fdb47ca98caf3bc16"
    "381ee0be93a091b8e3824cf01f889f46d7d9e20910fb0be1ab0fb5baa80dd621"
)
PACKAGE_MANAGER = f"pnpm@{PNPM_VERSION}+sha512.{PNPM_INTEGRITY_HEX}"
NODE_DEV_DEPENDENCIES = {
    "@eslint/js": "10.0.1",
    "@types/node": "24.13.3",
    "eslint": "10.8.1",
    "prettier": "3.9.6",
    "typescript": "6.0.3",
    "typescript-eslint": "8.67.0",
    "vitest": "4.1.10",
}
NODE_SCRIPTS = {
    "lint": "eslint . --max-warnings 0",
    "format:check": (
        "prettier --check package.json pnpm-workspace.yaml tsconfig.base.json "
        "tsconfig.json eslint.config.mjs prettier.config.mjs "
        '"packages/*/package.json" "packages/*/src/**/*.ts" '
        '"packages/*/tsconfig.json" "tests/contracts/**/*.ts"'
    ),
    "typecheck": "pnpm build && tsc --project tsconfig.json --noEmit",
    "test": "pnpm build && vitest run",
    "build": "pnpm --recursive run build",
    "licenses": "pnpm licenses list --json",
    "inventory": "pnpm list --recursive --depth Infinity",
    "check": (
        "pnpm lint && pnpm format:check && pnpm typecheck && pnpm test && pnpm build"
    ),
}
WORKSPACE_PACKAGES = {
    "api-client": "@slaif-agent-site/api-client",
    "browser-tool-contracts": "@slaif-agent-site/browser-tool-contracts",
    "component-catalog": "@slaif-agent-site/component-catalog",
    "composition-schema": "@slaif-agent-site/composition-schema",
    "content-model-schema": "@slaif-agent-site/content-model-schema",
    "scope-catalog": "@slaif-agent-site/scope-catalog",
    "test-fixtures": "@slaif-agent-site/test-fixtures",
}
ROOT_NODE_DEV_DEPENDENCIES = NODE_DEV_DEPENDENCIES | {
    name: "workspace:0.0.0" for name in WORKSPACE_PACKAGES.values()
}
PACKAGE_SCRIPTS = {
    "build": "tsc --project tsconfig.json",
    "typecheck": "tsc --project tsconfig.json --noEmit",
}
LIFECYCLE_SCRIPTS = {
    "install",
    "postinstall",
    "postpack",
    "preinstall",
    "prepack",
    "prepare",
    "prepublish",
    "prepublishOnly",
}
FORBIDDEN_HOSTED_DEPENDENCY_PREFIXES = (
    "@aws-sdk/",
    "@azure/",
    "@datadog/",
    "@google-cloud/",
    "@sentry/",
    "@supabase/",
    "@vercel/",
    "auth0",
    "cloudinary",
    "firebase",
    "newrelic",
)
NODE_REQUIRED_FILES = (
    "contracts/README.md",
    "eslint.config.mjs",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "prettier.config.mjs",
    "tests/contracts/workspace-contracts.test.ts",
    "tsconfig.base.json",
    "tsconfig.json",
) + tuple(
    path
    for slug in WORKSPACE_PACKAGES
    for path in (
        f"packages/{slug}/package.json",
        f"packages/{slug}/src/index.ts",
        f"packages/{slug}/tsconfig.json",
    )
)
REQUIRED_FILES = (
    (
        ".github/dependabot.yml",
        ".github/pull_request_template.md",
        ".github/workflows/ci.yml",
        ".github/workflows/codeql.yml",
        ".markdownlint-cli2.yaml",
        "AGENTS.md",
        "ARCHITECTURE.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "NOTICE",
        "OAP-COMMUNICATION-coding-agent.md",
        "README.md",
        "SECURITY.md",
        "docs/FOUNDATION_INTEGRATION.md",
        "docs/CONFIGURATION.md",
        "docs/SERVICE_AUTHORITY.md",
        "docs/assets/README.md",
        "docs/assets/slaif-logo.svg",
        "oap/active",
        "pyproject.toml",
        "services/backend/src/slaif_agent_site/__init__.py",
        "services/backend/src/slaif_agent_site/agent_state/__init__.py",
        "services/backend/src/slaif_agent_site/agent_state/foundation.py",
        "services/backend/src/slaif_agent_site/application.py",
        "services/backend/src/slaif_agent_site/authority.py",
        "services/backend/src/slaif_agent_site/config.py",
        "services/backend/src/slaif_agent_site/correlation.py",
        "services/backend/src/slaif_agent_site/errors.py",
        "services/backend/src/slaif_agent_site/health.py",
        "services/backend/src/slaif_agent_site/logging.py",
        "services/backend/src/slaif_agent_site/worker.py",
        "services/backend/tests/conftest.py",
        "services/backend/tests/integration/test_foundation_postgres.py",
        "services/backend/tests/unit/test_foundation_contract.py",
        "services/backend/tests/unit/test_authority.py",
        "services/backend/tests/unit/test_config.py",
        "services/backend/tests/unit/test_correlation_logging.py",
        "services/backend/tests/unit/test_errors.py",
        "services/backend/tests/unit/test_health_apps.py",
        "services/backend/tests/unit/test_process_entrypoints.py",
        "tests/repository/test_mermaid.py",
        "tests/repository/test_repository_policy.py",
        "tools/check_mermaid.py",
        "tools/check_repository.py",
        "uv.lock",
    )
    + tuple(
        f"services/backend/src/slaif_agent_site/{package}/{filename}"
        for package in HTTP_PROCESS_PACKAGES
        for filename in ("__init__.py", "__main__.py", "app.py")
    )
    + tuple(
        f"services/backend/src/slaif_agent_site/{package}/{filename}"
        for package in WORKER_PROCESS_PACKAGES
        for filename in ("__init__.py", "__main__.py")
    )
    + NODE_REQUIRED_FILES
)
REQUIRED_README_TARGETS = (
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "docs/FOUNDATION_INTEGRATION.md",
    "docs/CONFIGURATION.md",
    "docs/SERVICE_AUTHORITY.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "docs/assets/README.md",
    "oap/",
)
APPROVED_ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-python": "5fda3b95a4ea91299a34e894583c3862153e4b97",
    "actions/setup-node": "820762786026740c76f36085b0efc47a31fe5020",
    "github/codeql-action/init": "ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd",
    "github/codeql-action/analyze": "ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd",
    "actions/dependency-review-action": "a1d282b36b6f3519aa1f3fc636f609c47dddb294",
    "DavidAnson/markdownlint-cli2-action": "21c1be1b93ad9ed58fa840aacc3f279cde2a72ff",
    "astral-sh/setup-uv": "20cfd1bf945f4377ade1205e4dbc17946fc9a30d",
    "pnpm/action-setup": "0977fd99725f1db4007ccb2928dbb4e90d06cc86",
}
TEXT_NAMES = {
    "LICENSE",
    "NOTICE",
    "active",
}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}
CONFLICT_MARKER = re.compile(r"^(?:<<<<<<<(?: |$)|=======$|>>>>>>>)(?: |$)")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s+#\s*(\S.*))?\s*$")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
OAP_IDENTIFIER = re.compile(r"\d{3}-[a-z]")
OAP_ARTIFACT = re.compile(r"^(\d{3}-[a-z])(?:-.+)?\.md$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")
HTML_LINK = re.compile(r"(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
MANIFEST_NAMES = {
    "Pipfile",
    "pyproject.toml",
    "requirements.in",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
}


class RepositoryPolicy:
    """Accumulate stable, sorted policy diagnostics for one repository root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.errors: list[str] = []

    def error(self, path: str | Path, message: str) -> None:
        candidate = Path(path)
        if candidate.is_absolute():
            try:
                label = candidate.relative_to(self.root).as_posix()
            except ValueError:
                label = candidate.as_posix()
        else:
            label = candidate.as_posix()
        self.errors.append(f"{label}: {message}")

    def run(self) -> list[str]:
        self.check_required_files()
        self.check_text_files()
        self.check_logo()
        self.check_readme()
        self.check_oap()
        self.check_workflows()
        self.check_python_quality_configuration()
        self.check_foundation_dependencies()
        self.check_python_dependencies()
        self.check_backend_skeleton()
        self.check_node_workspace()
        return sorted(set(self.errors))

    def check_required_files(self) -> None:
        for relative in REQUIRED_FILES:
            if not (self.root / relative).is_file():
                self.error(relative, "required preparation file is missing")

    def iter_text_files(self) -> list[Path]:
        paths: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.root)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES:
                paths.append(path)
        return sorted(paths, key=lambda item: item.relative_to(self.root).as_posix())

    def read_utf8(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            self.error(path, f"is not valid UTF-8 ({exc})")
        except OSError as exc:
            self.error(path, f"cannot be read ({exc})")
        return None

    def check_text_files(self) -> None:
        for path in self.iter_text_files():
            text = self.read_utf8(path)
            if text is None:
                continue
            is_markdown = path.suffix.lower() == ".md"
            for number, line in enumerate(text.splitlines(), start=1):
                if CONFLICT_MARKER.match(line):
                    self.error(path, f"line {number} contains a merge-conflict marker")
                trailing = re.search(r"[ \t]+$", line)
                if trailing and not (is_markdown and trailing.group(0) == "  "):
                    self.error(path, f"line {number} has invalid trailing whitespace")

    def check_logo(self, expected_hash: str = LOGO_SHA256) -> None:
        path = self.root / "docs/assets/slaif-logo.svg"
        if not path.is_file():
            return
        try:
            data = path.read_bytes()
        except OSError as exc:
            self.error(path, f"cannot be read ({exc})")
            return
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_hash:
            self.error(path, f"SHA-256 is {digest}, expected {expected_hash}")
        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            self.error(path, f"is not well-formed XML ({exc})")
            return
        if self.local_name(root.tag).lower() != "svg":
            self.error(path, "XML root element is not svg")
        forbidden_elements = {
            "embed",
            "foreignobject",
            "iframe",
            "image",
            "object",
            "script",
        }
        for element in root.iter():
            element_name = self.local_name(element.tag).lower()
            if element_name in forbidden_elements:
                self.error(path, f"contains forbidden <{element_name}> element")
            for raw_name, value in element.attrib.items():
                name = self.local_name(raw_name).lower()
                normalized = value.strip().lower()
                if name.startswith("on"):
                    self.error(path, f"contains event-handler attribute {name}")
                if (
                    name in {"href", "src"}
                    and normalized
                    and not normalized.startswith("#")
                ):
                    self.error(path, f"contains external resource reference in {name}")
                if (
                    "javascript:" in normalized
                    or "data:" in normalized
                    or "file:" in normalized
                ):
                    self.error(path, f"contains unsafe attribute value in {name}")
        xml_text = data.decode("utf-8", errors="replace")
        if re.search(r"@import", xml_text, re.IGNORECASE):
            self.error(path, "contains a CSS @import")
        for reference in re.findall(
            r"url\(\s*['\"]?([^)'\"\s]+)", xml_text, re.IGNORECASE
        ):
            if not reference.startswith("#"):
                self.error(path, "contains an external CSS resource reference")

    @staticmethod
    def local_name(name: str) -> str:
        return name.rsplit("}", 1)[-1]

    def check_readme(self) -> None:
        path = self.root / "README.md"
        if not path.is_file():
            return
        text = self.read_utf8(path)
        if text is None:
            return
        logo_block = re.search(
            r"<a\s+href=['\"]https://www\.slaif\.si['\"][^>]*>\s*"
            r"<img\s+([^>]+)>\s*</a>",
            text,
            re.IGNORECASE,
        )
        if logo_block is None:
            self.error(path, "must link the local logo to https://www.slaif.si")
        else:
            attributes = {
                key.lower(): value
                for key, _, value in re.findall(
                    r"([:\w-]+)\s*=\s*(['\"])(.*?)\2", logo_block.group(1)
                )
            }
            if attributes.get("src") != "docs/assets/slaif-logo.svg":
                self.error(path, "logo src must be docs/assets/slaif-logo.svg")
            if len(attributes.get("alt", "").strip()) < 5:
                self.error(path, "logo must have meaningful alt text")
            if not re.fullmatch(r"\d+", attributes.get("width", "")):
                self.error(path, "logo must specify a numeric width")
            if "height" in attributes:
                self.error(path, "logo must use width only, without height")

        destinations = [match.group(1) for match in MARKDOWN_LINK.finditer(text)]
        destinations.extend(match.group(1) for match in HTML_LINK.finditer(text))
        local_targets: set[str] = set()
        for destination in destinations:
            split = urlsplit(destination)
            if split.scheme or split.netloc or destination.startswith("#"):
                continue
            relative = unquote(split.path)
            if not relative:
                continue
            local_targets.add(relative)
            target = (path.parent / relative).resolve()
            try:
                target.relative_to(self.root)
            except ValueError:
                self.error(path, f"local link escapes repository: {destination}")
                continue
            if not target.exists():
                self.error(path, f"local link does not resolve: {destination}")
        for required in REQUIRED_README_TARGETS:
            if required not in local_targets:
                self.error(path, f"required internal link is absent: {required}")

    def check_oap(self) -> None:
        active_path = self.root / "oap/active"
        orders_dir = self.root / "oap/orders"
        reports_dir = self.root / "oap/reports"
        active: str | None = None
        if active_path.is_file():
            text = self.read_utf8(active_path)
            if text is not None:
                if not re.fullmatch(r"\d{3}-[a-z]\n?", text):
                    self.error(
                        active_path,
                        "must contain one NNN-x identifier and optional final newline",
                    )
                else:
                    active = text.strip()

        orders = self.group_oap_artifacts(orders_dir, "order")
        reports = self.group_oap_artifacts(reports_dir, "report")
        if active is not None and len(orders.get(active, [])) != 1:
            self.error(
                orders_dir, f"active identifier {active} must have exactly one order"
            )
        for identifier in sorted(orders):
            count = len(reports.get(identifier, []))
            if identifier == active:
                if count > 1:
                    self.error(
                        reports_dir,
                        f"active identifier {identifier} has more than one report",
                    )
            elif count != 1:
                self.error(
                    reports_dir,
                    f"historical identifier {identifier} must have exactly one report",
                )
        for identifier in sorted(set(reports) - set(orders)):
            self.error(
                reports_dir, f"identifier {identifier} has a report without an order"
            )

        oap_root = self.root / "oap"
        if oap_root.exists():
            temporary = re.compile(r"(?:^\.|\.tmp$|\.part$|\.new$|\.bak$|\.swp$|~$)")
            for path in sorted(oap_root.rglob("*")):
                if path.is_file() and temporary.search(path.name):
                    self.error(
                        path, "temporary/publication artifact is forbidden in oap"
                    )

    def group_oap_artifacts(self, directory: Path, label: str) -> dict[str, list[Path]]:
        grouped: dict[str, list[Path]] = defaultdict(list)
        if not directory.is_dir():
            self.error(directory, f"OAP {label} directory is missing")
            return grouped
        for path in sorted(directory.glob("*.md")):
            match = OAP_ARTIFACT.fullmatch(path.name)
            if match is None:
                self.error(path, f"OAP {label} filename does not start with NNN-x")
                continue
            grouped[match.group(1)].append(path)
        for identifier, paths in sorted(grouped.items()):
            if len(paths) > 1:
                self.error(
                    directory, f"identifier {identifier} has {len(paths)} {label} files"
                )
        return grouped

    def check_workflows(self) -> None:
        directory = self.root / ".github/workflows"
        if not directory.is_dir():
            return
        for path in sorted((*directory.glob("*.yml"), *directory.glob("*.yaml"))):
            text = self.read_utf8(path)
            if text is None:
                continue
            if re.search(r"^\s*pull_request_target\s*:", text, re.MULTILINE):
                self.error(path, "pull_request_target trigger is forbidden")
            if re.search(r"\bwrite-all\b", text, re.IGNORECASE):
                self.error(path, "write-all permission is forbidden")
            for number, line in enumerate(text.splitlines(), start=1):
                permission = re.match(
                    r"^\s*([a-z][a-z-]*)\s*:\s*write\s*(?:#.*)?$", line
                )
                if permission and permission.group(1) != "security-events":
                    self.error(
                        path,
                        f"line {number} grants forbidden {permission.group(1)}: write",
                    )
                uses = USES_LINE.match(line)
                if uses is None:
                    continue
                reference, release_comment = uses.groups()
                if reference.startswith("./"):
                    continue
                if "@" not in reference:
                    self.error(path, f"line {number} external action has no @ revision")
                    continue
                action, revision = reference.rsplit("@", 1)
                if not FULL_SHA.fullmatch(revision):
                    self.error(
                        path,
                        f"line {number} action revision is not a lowercase full SHA",
                    )
                    continue
                approved = APPROVED_ACTIONS.get(action)
                if approved != revision:
                    self.error(path, f"line {number} action revision is not approved")
                if not release_comment or not re.fullmatch(
                    r"v\d+(?:\.\d+){1,2}", release_comment
                ):
                    self.error(
                        path, f"line {number} action needs a release-version comment"
                    )

    def check_foundation_dependencies(self) -> None:
        pyproject_path = self.root / "pyproject.toml"
        lock_path = self.root / "uv.lock"
        if pyproject_path.is_file():
            self.check_foundation_pyproject(pyproject_path)
        if lock_path.is_file():
            self.check_foundation_lock(lock_path)

        candidates: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or any(
                part in SKIP_DIRS for part in path.relative_to(self.root).parts
            ):
                continue
            if path != pyproject_path and (
                path.name in MANIFEST_NAMES or path.name.startswith("requirements")
            ):
                candidates.append(path)
        for path in sorted(candidates):
            text = self.read_utf8(path)
            if text is None or "agent-cow-postgresql" not in text.lower():
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                lower = line.lower()
                if "agent-cow-postgresql" not in lower:
                    continue
                forbidden = (
                    re.search(r"(?:git|hg|svn|bzr)\+", lower)
                    or re.search(r"\s@\s*(?:https?|file):", lower)
                    or re.search(r"(?:^|\s)-e(?:\s|$)", lower)
                    or re.search(r"\b(?:path|editable|git|url)\s*=", lower)
                    or ("http://" in lower or "https://" in lower or "file:" in lower)
                )
                if forbidden:
                    self.error(
                        path,
                        f"line {number} uses a forbidden foundation dependency source",
                    )
                    continue
                if "==" not in lower:
                    self.error(
                        path,
                        f"line {number} foundation dependency is not exactly "
                        "version-pinned",
                    )

    def check_python_dependencies(self) -> None:
        """Require the exact minimal direct Python dependency boundary."""

        pyproject_path = self.root / "pyproject.toml"
        lock_path = self.root / "uv.lock"
        if pyproject_path.is_file():
            document = self.load_toml(pyproject_path)
            if document is not None:
                project = document.get("project")
                dependencies: object = None
                if isinstance(project, dict):
                    dependencies = project.get("dependencies")
                if dependencies != PYTHON_RUNTIME_DEPENDENCIES:
                    self.error(
                        pyproject_path,
                        "project.dependencies must match the approved exact "
                        "runtime set",
                    )

                groups = document.get("dependency-groups")
                if groups != PYTHON_DEPENDENCY_GROUPS:
                    self.error(
                        pyproject_path,
                        "dependency-groups must match the approved "
                        "build/quality/test set",
                    )

                tool = document.get("tool")
                sources: object = None
                if isinstance(tool, dict):
                    uv = tool.get("uv")
                    if isinstance(uv, dict):
                        sources = uv.get("sources")
                if isinstance(sources, dict):
                    direct_names = {
                        name.replace("-", "_") for name in PYTHON_DIRECT_VERSIONS
                    }
                    overridden = {
                        str(name)
                        for name in sources
                        if str(name).lower().replace("-", "_") in direct_names
                    }
                    if overridden:
                        self.error(
                            pyproject_path,
                            "direct Python dependency source overrides are forbidden",
                        )

        if not lock_path.is_file():
            return
        lock = self.load_toml(lock_path)
        if lock is None:
            return
        packages = lock.get("package")
        if not isinstance(packages, list):
            self.error(lock_path, "lock package inventory is missing")
            return
        for name, version in PYTHON_DIRECT_VERSIONS.items():
            matches = [
                package
                for package in packages
                if isinstance(package, dict) and package.get("name") == name
            ]
            if len(matches) != 1:
                self.error(lock_path, f"must contain exactly one locked {name} package")
                continue
            package = matches[0]
            if package.get("version") != version:
                self.error(lock_path, f"{name} must be locked at exactly {version}")
            if package.get("source") != {"registry": FOUNDATION_REGISTRY}:
                self.error(lock_path, f"{name} must use the approved PyPI registry")

            sdist = package.get("sdist")
            if not isinstance(sdist, dict) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", str(sdist.get("hash", ""))
            ):
                self.error(lock_path, f"{name} sdist lacks a SHA-256 hash")
            wheels = package.get("wheels")
            if not isinstance(wheels, list) or not wheels:
                self.error(lock_path, f"{name} wheel inventory is missing")
            elif any(
                not isinstance(wheel, dict)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(wheel.get("hash", "")))
                for wheel in wheels
            ):
                self.error(lock_path, f"{name} wheel lacks a SHA-256 hash")

    def check_backend_skeleton(self) -> None:
        """Apply bounded static checks to process/config/route separation."""

        package_root = self.root / "services/backend/src/slaif_agent_site"
        authority_path = package_root / "authority.py"
        if authority_path.is_file():
            source = self.read_utf8(authority_path)
            if source is not None:
                try:
                    tree = ast.parse(source)
                except SyntaxError as exc:
                    self.error(authority_path, f"cannot parse Python ({exc})")
                else:
                    values: set[str] = set()
                    for node in tree.body:
                        if (
                            not isinstance(node, ast.ClassDef)
                            or node.name != "ProcessKind"
                        ):
                            continue
                        for statement in node.body:
                            if (
                                isinstance(statement, ast.Assign)
                                and isinstance(statement.value, ast.Constant)
                                and isinstance(statement.value.value, str)
                            ):
                                values.add(statement.value.value)
                    if values != BACKEND_PROCESS_VALUES:
                        self.error(
                            authority_path,
                            "ProcessKind must contain exactly the approved ten "
                            "processes",
                        )
                for forbidden in (
                    "all_authority",
                    "all-authority",
                    "credential_value",
                    "password",
                    "connection_string",
                ):
                    if forbidden in source.casefold():
                        self.error(
                            authority_path,
                            f"authority descriptors contain forbidden {forbidden!r}",
                        )

        config_path = package_root / "config.py"
        if config_path.is_file():
            source = self.read_utf8(config_path)
            if source is not None and re.search(
                r"\b(?:database_url|postgres_url|postgres_dsn|db_dsn)\b",
                source,
                re.IGNORECASE,
            ):
                self.error(config_path, "database connection configuration is deferred")

        application_path = package_root / "application.py"
        if application_path.is_file():
            source = self.read_utf8(application_path)
            if source is not None:
                route_literals = set(
                    re.findall(r"[\"'](/(?:health|api|internal)[^\"']*)[\"']", source)
                )
                if route_literals != {"/health/live", "/health/ready"}:
                    self.error(
                        application_path,
                        "shared HTTP skeleton may expose only live/ready routes",
                    )
                if "CORSMiddleware" in source or "allow_origins" in source:
                    self.error(
                        application_path, "CORS is not approved for this skeleton"
                    )

        for package in WORKER_PROCESS_PACKAGES:
            main_path = package_root / package / "__main__.py"
            if not main_path.is_file():
                continue
            source = self.read_utf8(main_path)
            if source is not None and any(
                forbidden in source.casefold()
                for forbidden in ("uvicorn", "fastapi", "asyncpg", "database_url")
            ):
                self.error(
                    main_path,
                    "non-listening entrypoint contains a listener/database dependency",
                )

    def check_python_quality_configuration(self) -> None:
        path = self.root / "pyproject.toml"
        if not path.is_file():
            return
        document = self.load_toml(path)
        if document is None:
            return
        tool = document.get("tool")
        ruff: object = None
        if isinstance(tool, dict):
            ruff = tool.get("ruff")
        if not isinstance(ruff, dict):
            self.error(path, "tool.ruff configuration is required")
            return

        for key in ("exclude", "extend-exclude", "force-exclude"):
            if key in ruff:
                self.error(
                    path,
                    f"tool.ruff.{key} may not narrow declared Python quality paths",
                )

        configured = repr(ruff)
        for required in (
            "tests/repository/test_mermaid.py",
            "tools/check_mermaid.py",
        ):
            if required in configured or Path(required).name in configured:
                self.error(
                    path,
                    f"Ruff configuration may not ignore required file {required}",
                )

    def check_node_workspace(self) -> None:
        root_manifest_path = self.root / "package.json"
        workspace_path = self.root / "pnpm-workspace.yaml"
        lock_path = self.root / "pnpm-lock.yaml"

        root_manifest = self.load_json(root_manifest_path)
        if root_manifest is not None:
            expected_root = {
                "name": "slaif-agent-site",
                "version": "0.0.0",
                "private": True,
                "license": "Apache-2.0",
                "type": "module",
                "engines": {"node": ">=24 <25"},
                "packageManager": PACKAGE_MANAGER,
                "scripts": NODE_SCRIPTS,
                "devDependencies": ROOT_NODE_DEV_DEPENDENCIES,
            }
            if root_manifest != expected_root:
                self.error(
                    root_manifest_path,
                    "root Node manifest must match the approved private toolchain",
                )
            self.check_node_manifest_safety(root_manifest_path, root_manifest)

        if workspace_path.is_file():
            workspace_text = self.read_utf8(workspace_path)
            if workspace_text is not None and workspace_text != (
                "packages:\n  - packages/*\n\nallowBuilds:\n  esbuild: false\n\n"
                "autoInstallPeers: false\n\noverrides:\n  esbuild: 0.28.1\n"
                "  vite: 7.3.6\n"
            ):
                self.error(
                    workspace_path,
                    "workspace must contain only packages/* and approved settings",
                )

        packages_root = self.root / "packages"
        discovered = {
            path.parent.name
            for path in packages_root.glob("*/package.json")
            if path.is_file()
        }
        expected_slugs = set(WORKSPACE_PACKAGES)
        if discovered != expected_slugs:
            self.error(
                packages_root,
                "workspace package set must be exactly "
                + ", ".join(sorted(expected_slugs)),
            )

        for slug, expected_name in WORKSPACE_PACKAGES.items():
            self.check_workspace_package(slug, expected_name)

        if lock_path.is_file():
            self.check_pnpm_lock(lock_path)

        base_config_path = self.root / "tsconfig.base.json"
        base_config = self.load_json(base_config_path)
        if base_config is not None:
            compiler_options = base_config.get("compilerOptions")
            required_options = {
                "paths": {"@slaif-agent-site/*": ["./packages/*/src/index.ts"]},
                "strict": True,
                "noUncheckedIndexedAccess": True,
                "exactOptionalPropertyTypes": True,
                "verbatimModuleSyntax": True,
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True,
            }
            if not isinstance(compiler_options, dict) or any(
                compiler_options.get(key) != value
                for key, value in required_options.items()
            ):
                self.error(
                    base_config_path,
                    "base TypeScript config is missing required strict/build options",
                )

    def check_node_manifest_safety(
        self, path: Path, document: dict[str, object]
    ) -> None:
        scripts = document.get("scripts")
        if isinstance(scripts, dict):
            lifecycle = sorted(set(scripts) & LIFECYCLE_SCRIPTS)
            if lifecycle:
                self.error(
                    path,
                    "lifecycle scripts are forbidden: " + ", ".join(lifecycle),
                )
        if "publishConfig" in document:
            self.error(path, "publish configuration is forbidden")

        for field in (
            "dependencies",
            "devDependencies",
            "optionalDependencies",
            "peerDependencies",
        ):
            dependencies = document.get(field)
            if not isinstance(dependencies, dict):
                continue
            for dependency in dependencies:
                lowered = str(dependency).lower()
                if lowered.startswith(FORBIDDEN_HOSTED_DEPENDENCY_PREFIXES):
                    self.error(
                        path,
                        f"{field} contains forbidden hosted SDK {dependency}",
                    )

    def check_workspace_package(self, slug: str, expected_name: str) -> None:
        package_root = self.root / "packages" / slug
        manifest_path = package_root / "package.json"
        source_path = package_root / "src" / "index.ts"
        config_path = package_root / "tsconfig.json"

        manifest = self.load_json(manifest_path)
        if manifest is not None:
            expected_keys = {
                "description",
                "exports",
                "files",
                "license",
                "name",
                "private",
                "scripts",
                "type",
                "types",
                "version",
            }
            if set(manifest) != expected_keys:
                self.error(
                    manifest_path,
                    "package manifest contains an unapproved field set",
                )
            expected_values = {
                "name": expected_name,
                "version": "0.0.0",
                "private": True,
                "license": "Apache-2.0",
                "type": "module",
                "files": ["dist"],
                "exports": {
                    ".": {
                        "types": "./dist/index.d.ts",
                        "import": "./dist/index.js",
                    }
                },
                "types": "./dist/index.d.ts",
                "scripts": PACKAGE_SCRIPTS,
            }
            if any(
                manifest.get(key) != value for key, value in expected_values.items()
            ):
                self.error(
                    manifest_path,
                    "package identity/export/build contract is not approved",
                )
            description = manifest.get("description")
            if not isinstance(description, str) or not {
                "scaffold",
                "unimplemented",
            }.issubset(description.lower().split()):
                self.error(
                    manifest_path,
                    "description must identify an unimplemented scaffold",
                )
            self.check_node_manifest_safety(manifest_path, manifest)

        source = self.read_utf8(source_path) if source_path.is_file() else None
        if source is not None:
            exported_names = re.findall(
                r"^export\s+(?:const|type|interface|class|function)\s+(\w+)",
                source,
                re.MULTILINE,
            )
            required_literals = (expected_name, "pre-alpha-scaffold", '"0.0.0"')
            if exported_names != ["packageMetadata"] or any(
                literal not in source for literal in required_literals
            ):
                self.error(
                    source_path,
                    "source must export only exact scaffold packageMetadata",
                )
            if re.search(r"\bany\b", source):
                self.error(source_path, "unsafe any export is forbidden")

        config = self.load_json(config_path)
        if config is not None:
            expected_config = {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "rootDir": "src",
                    "outDir": "dist",
                    "tsBuildInfoFile": "dist/.tsbuildinfo",
                },
                "include": ["src/**/*.ts"],
            }
            if config != expected_config:
                self.error(
                    config_path, "package TypeScript build boundary is not exact"
                )

    def check_pnpm_lock(self, path: Path) -> None:
        text = self.read_utf8(path)
        if text is None:
            return
        if not text.startswith("lockfileVersion: '9.0'\n"):
            self.error(path, "lockfile version must be the pnpm 11 format")

        audited_text = text
        for slug, package_name in WORKSPACE_PACKAGES.items():
            expected_link = re.compile(
                rf"^      '{re.escape(package_name)}':\n"
                rf"        specifier: workspace:0\.0\.0\n"
                rf"        version: link:packages/{re.escape(slug)}$",
                re.MULTILINE,
            )
            if not expected_link.search(text):
                self.error(
                    path,
                    f"workspace package {package_name} lacks its exact internal link",
                )
            audited_text = audited_text.replace(
                "specifier: workspace:0.0.0", "specifier: internal-workspace"
            )
            audited_text = audited_text.replace(
                f"version: link:packages/{slug}", "version: internal-workspace"
            )

        forbidden_source = re.search(
            r"(?:^|[\s'\"{[(,])(?:git\+https?|git|github|gitlab|bitbucket|file|"
            r"link|patch|workspace|path|directory):",
            audited_text,
            re.IGNORECASE,
        )
        if forbidden_source:
            self.error(
                path,
                f"forbidden lock source form {forbidden_source.group(0).strip()}",
            )
        if "../" in audited_text:
            self.error(path, "workspace/path escape is forbidden in pnpm lock")

        urls = re.findall(r"https?://[^\s,}\]]+", audited_text, re.IGNORECASE)
        for url in urls:
            if not url.startswith("https://registry.npmjs.org/"):
                self.error(path, f"unapproved package registry or direct URL {url}")
            else:
                self.error(path, "direct URL lock sources are forbidden")

        importer_section = self.lock_section(text, "importers")
        importers = set(
            re.findall(
                r"^  ([^\s].*?):(?:\s+\{\})?\s*$",
                importer_section,
                re.MULTILINE,
            )
        )
        expected_importers = {"."} | {f"packages/{slug}" for slug in WORKSPACE_PACKAGES}
        if importers != expected_importers:
            self.error(path, "lock importer set does not match the exact workspace")

        packages_section = self.lock_section(text, "packages")
        package_entries = list(
            re.finditer(r"^  ([^\s].*):\s*$", packages_section, re.MULTILINE)
        )
        if not package_entries:
            self.error(path, "lock contains no external package entries")
            return
        for index, match in enumerate(package_entries):
            end = (
                package_entries[index + 1].start()
                if index + 1 < len(package_entries)
                else len(packages_section)
            )
            block = packages_section[match.end() : end]
            if not re.search(r"\bintegrity:\s*sha512-[A-Za-z0-9+/]+={0,2}", block):
                self.error(
                    path,
                    f"external package {match.group(1)} lacks sha512 integrity",
                )

    @staticmethod
    def lock_section(text: str, name: str) -> str:
        match = re.search(
            rf"^{re.escape(name)}:\s*$\n(.*?)(?=^\S[^\n]*:\s*$|\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        return match.group(1) if match else ""

    def load_json(self, path: Path) -> dict[str, object] | None:
        if not path.is_file():
            return None
        try:
            document: object = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.error(path, f"cannot parse JSON ({exc})")
            return None
        if not isinstance(document, dict):
            self.error(path, "JSON root must be an object")
            return None
        return document

    def load_toml(self, path: Path) -> dict[str, object] | None:
        try:
            with path.open("rb") as handle:
                return tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            self.error(path, f"cannot parse TOML ({exc})")
        return None

    def check_foundation_pyproject(self, path: Path) -> None:
        document = self.load_toml(path)
        if document is None:
            return
        project = document.get("project")
        dependencies: object = None
        if isinstance(project, dict):
            dependencies = project.get("dependencies")
        expected = f"agent-cow-postgresql=={FOUNDATION_VERSION}"
        matches = []
        if isinstance(dependencies, list):
            matches = [
                dependency
                for dependency in dependencies
                if isinstance(dependency, str)
                and "agent-cow-postgresql" in dependency.lower()
            ]
        if matches != [expected]:
            self.error(
                path,
                f"project.dependencies must contain exactly {expected!r}",
            )

        tool = document.get("tool")
        uv_sources: object = None
        if isinstance(tool, dict):
            uv = tool.get("uv")
            if isinstance(uv, dict):
                uv_sources = uv.get("sources")
        if isinstance(uv_sources, dict) and any(
            str(name).lower().replace("_", "-") == "agent-cow-postgresql"
            for name in uv_sources
        ):
            self.error(path, "foundation dependency source override is forbidden")

    def check_foundation_lock(self, path: Path) -> None:
        document = self.load_toml(path)
        if document is None:
            return
        packages = document.get("package")
        matches: list[dict[str, object]] = []
        if isinstance(packages, list):
            matches = [
                package
                for package in packages
                if isinstance(package, dict)
                and package.get("name") == "agent-cow-postgresql"
            ]
        if len(matches) != 1:
            self.error(path, "must contain exactly one locked foundation package")
            return
        package = matches[0]
        if package.get("version") != FOUNDATION_VERSION:
            self.error(path, f"foundation version must be exactly {FOUNDATION_VERSION}")
        source = package.get("source")
        if source != {"registry": FOUNDATION_REGISTRY}:
            self.error(
                path,
                "foundation source must be the approved registry "
                f"{FOUNDATION_REGISTRY}",
            )

        sdist = package.get("sdist")
        expected_sdist_hash = f"sha256:{FOUNDATION_SDIST_SHA256}"
        if not isinstance(sdist, dict):
            self.error(path, "foundation sdist artifact is missing")
        else:
            if not str(sdist.get("url", "")).endswith(f"/{FOUNDATION_SDIST}"):
                self.error(path, "foundation sdist filename is not approved")
            if sdist.get("hash") != expected_sdist_hash:
                self.error(path, "foundation sdist SHA-256 is missing or unapproved")

        wheels = package.get("wheels")
        expected_wheel_hash = f"sha256:{FOUNDATION_WHEEL_SHA256}"
        approved_wheel = False
        if isinstance(wheels, list):
            approved_wheel = any(
                isinstance(wheel, dict)
                and str(wheel.get("url", "")).endswith(f"/{FOUNDATION_WHEEL}")
                and wheel.get("hash") == expected_wheel_hash
                for wheel in wheels
            )
        if not approved_wheel:
            self.error(path, "foundation wheel and approved SHA-256 are required")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of this tool's directory)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    errors = RepositoryPolicy(args.root).run()
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"FAIL repository policy ({len(errors)} error(s))")
        return 1
    print("PASS repository policy")
    return 0


if __name__ == "__main__":
    sys.exit(main())

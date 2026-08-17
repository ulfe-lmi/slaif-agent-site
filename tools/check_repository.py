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
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


LOGO_SHA256 = "0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08"
REQUIRED_FILES = (
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
    "docs/assets/README.md",
    "docs/assets/slaif-logo.svg",
    "oap/active",
    "tests/repository/test_mermaid.py",
    "tests/repository/test_repository_policy.py",
    "tools/check_mermaid.py",
    "tools/check_repository.py",
)
REQUIRED_README_TARGETS = (
    ".github/workflows/ci.yml",
    ".github/workflows/codeql.yml",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
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
        self.check_foundation_dependencies()
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
        forbidden_elements = {"embed", "foreignobject", "iframe", "image", "object", "script"}
        for element in root.iter():
            element_name = self.local_name(element.tag).lower()
            if element_name in forbidden_elements:
                self.error(path, f"contains forbidden <{element_name}> element")
            for raw_name, value in element.attrib.items():
                name = self.local_name(raw_name).lower()
                normalized = value.strip().lower()
                if name.startswith("on"):
                    self.error(path, f"contains event-handler attribute {name}")
                if name in {"href", "src"} and normalized and not normalized.startswith("#"):
                    self.error(path, f"contains external resource reference in {name}")
                if "javascript:" in normalized or "data:" in normalized or "file:" in normalized:
                    self.error(path, f"contains unsafe attribute value in {name}")
        xml_text = data.decode("utf-8", errors="replace")
        if re.search(r"@import", xml_text, re.IGNORECASE):
            self.error(path, "contains a CSS @import")
        for reference in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", xml_text, re.IGNORECASE):
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
                    self.error(active_path, "must contain one NNN-x identifier and optional final newline")
                else:
                    active = text.strip()

        orders = self.group_oap_artifacts(orders_dir, "order")
        reports = self.group_oap_artifacts(reports_dir, "report")
        if active is not None and len(orders.get(active, [])) != 1:
            self.error(orders_dir, f"active identifier {active} must have exactly one order")
        for identifier in sorted(orders):
            count = len(reports.get(identifier, []))
            if identifier == active:
                if count > 1:
                    self.error(reports_dir, f"active identifier {identifier} has more than one report")
            elif count != 1:
                self.error(reports_dir, f"historical identifier {identifier} must have exactly one report")
        for identifier in sorted(set(reports) - set(orders)):
            self.error(reports_dir, f"identifier {identifier} has a report without an order")

        oap_root = self.root / "oap"
        if oap_root.exists():
            temporary = re.compile(r"(?:^\.|\.tmp$|\.part$|\.new$|\.bak$|\.swp$|~$)")
            for path in sorted(oap_root.rglob("*")):
                if path.is_file() and temporary.search(path.name):
                    self.error(path, "temporary/publication artifact is forbidden in oap")

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
                self.error(directory, f"identifier {identifier} has {len(paths)} {label} files")
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
                permission = re.match(r"^\s*([a-z][a-z-]*)\s*:\s*write\s*(?:#.*)?$", line)
                if permission and permission.group(1) != "security-events":
                    self.error(path, f"line {number} grants forbidden {permission.group(1)}: write")
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
                    self.error(path, f"line {number} action revision is not a lowercase full SHA")
                    continue
                approved = APPROVED_ACTIONS.get(action)
                if approved != revision:
                    self.error(path, f"line {number} action revision is not approved")
                if not release_comment or not re.fullmatch(r"v\d+(?:\.\d+){1,2}", release_comment):
                    self.error(path, f"line {number} action needs a release-version comment")

    def check_foundation_dependencies(self) -> None:
        candidates: list[Path] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            if path.name in MANIFEST_NAMES or path.name.startswith("requirements"):
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
                    self.error(path, f"line {number} uses a forbidden foundation dependency source")
                    continue
                if "==" not in lower:
                    self.error(path, f"line {number} foundation dependency is not exactly version-pinned")


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

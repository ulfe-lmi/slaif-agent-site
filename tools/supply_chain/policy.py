#!/usr/bin/env python3
"""Validate supply-chain policy and build deterministic dependency notices."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import sys
import tomllib
from collections import deque
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "supply-chain/policy.json"
LICENSE_EXCEPTIONS_PATH = ROOT / "supply-chain/license-exceptions.json"
VULNERABILITY_EXCEPTIONS_PATH = ROOT / "supply-chain/vulnerability-exceptions.json"
NOTICES_PATH = ROOT / "THIRD_PARTY_NOTICES.md"
SHA256 = re.compile(r"[0-9a-f]{64}")
FULL_SHA = re.compile(r"[0-9a-f]{40}")
ACTION = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.MULTILINE)
REQUIREMENT_NAME = re.compile(r"^[A-Za-z0-9_.-]+")
IMMUTABLE_IMAGE = re.compile(
    r"^[a-z0-9][a-z0-9./_-]*:[A-Za-z0-9_.-]+@sha256:[0-9a-f]{64}$"
)
SIMPLE_LICENSE = re.compile(r"^[A-Za-z0-9.+-]+(?: (?:AND|OR) [A-Za-z0-9.+-]+)*$")


class PolicyError(ValueError):
    """A stable policy failure intended for humans and CI."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = path.as_posix()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"{label}: invalid JSON ({exc})") from exc
    if not isinstance(value, dict):
        raise PolicyError(f"{label}: root must be an object")
    return value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def python_purl(name: str, version: str) -> str:
    return f"pkg:pypi/{normalized_name(name)}@{version}"


def npm_purl(name: str, version: str) -> str:
    return f"pkg:npm/{quote(name, safe='/')}@{version}"


def normalize_license_expression(expression: str) -> str:
    for operator in (" OR ", " AND "):
        parts = expression.split(operator)
        if len(parts) > 1 and all(
            " AND " not in part and " OR " not in part for part in parts
        ):
            return operator.join(sorted(part.strip() for part in parts))
    return expression.strip()


def require_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - set(value))
    if missing:
        raise PolicyError(f"{label}: missing keys: {', '.join(missing)}")
    unexpected = sorted(set(value) - keys)
    if unexpected:
        raise PolicyError(f"{label}: unexpected keys: {', '.join(unexpected)}")


def validate_policy(policy: dict[str, Any]) -> None:
    required = {
        "application_licenses",
        "alpine_package_overrides",
        "attribution_notes",
        "browser_runtime",
        "container_license_policy",
        "evidence",
        "github_actions",
        "license_metadata_reviews",
        "oci_sources",
        "project",
        "required_images",
        "scanner_tools",
        "schema_version",
        "source_date_epoch",
        "sources",
        "vulnerability_policy",
    }
    require_keys(policy, required, "policy")
    if policy["schema_version"] != 1:
        raise PolicyError("policy: schema_version must be 1")
    epoch = policy["source_date_epoch"]
    if not isinstance(epoch, int) or not 946684800 <= epoch <= 4102444800:
        raise PolicyError("policy: source_date_epoch must be a bounded UTC epoch")

    project = policy["project"]
    if not isinstance(project, dict):
        raise PolicyError("policy: project must be an object")
    require_keys(project, {"license", "repository", "version"}, "policy.project")
    if project != {
        "license": "Apache-2.0",
        "repository": "https://github.com/ulfe-lmi/slaif-agent-site",
        "version": "0.0.0",
    }:
        raise PolicyError("policy: project identity is invalid")

    licenses = policy["application_licenses"]
    if not isinstance(licenses, dict):
        raise PolicyError("policy: application_licenses must be an object")
    require_keys(
        licenses,
        {
            "automatic",
            "attribution_review",
            "explicit_review",
            "prohibited_tokens",
            "unknown_direct_fails",
        },
        "policy.application_licenses",
    )
    allowed = (
        licenses["automatic"]
        + licenses["attribution_review"]
        + licenses["explicit_review"]
    )
    if not all(
        isinstance(item, str) and SIMPLE_LICENSE.fullmatch(item) for item in allowed
    ) or len(allowed) != len(set(allowed)):
        raise PolicyError("policy: approved licenses must be unique SPDX expressions")
    prohibited = licenses["prohibited_tokens"]
    if not isinstance(prohibited, list) or not all(
        isinstance(item, str) and item for item in prohibited
    ):
        raise PolicyError("policy: prohibited license tokens must be non-empty strings")
    for expression in allowed:
        if any(token.casefold() in expression.casefold() for token in prohibited):
            raise PolicyError(f"policy: prohibited license is approved: {expression}")

    container_policy = policy["container_license_policy"]
    if not isinstance(container_policy, dict):
        raise PolicyError("policy: container_license_policy must be an object")
    expected_container_policy = {
        "application_allowlist_does_not_reclassify_os_packages": True,
        "classification": "container-os-runtime-aggregation",
        "inventory_all_packages": True,
        "legal_advice": False,
        "unknown_metadata_result": "legal-review-required",
    }
    if container_policy != expected_container_policy:
        raise PolicyError("policy: container license boundary is invalid")

    attribution = policy["attribution_notes"]
    if not isinstance(attribution, dict) or not all(
        isinstance(purl, str)
        and purl.startswith("pkg:")
        and isinstance(note, str)
        and note.strip()
        for purl, note in attribution.items()
    ):
        raise PolicyError("policy: attribution notes are malformed")

    reviews = policy["license_metadata_reviews"]
    if not isinstance(reviews, dict):
        raise PolicyError("policy: license metadata reviews must be an object")
    for purl, review in reviews.items():
        if not isinstance(review, dict):
            raise PolicyError(f"policy: license review for {purl} is malformed")
        require_keys(review, {"license", "source"}, f"policy review {purl}")
        if (
            not purl.startswith("pkg:")
            or review["license"] not in allowed
            or not isinstance(review["source"], str)
            or not review["source"].startswith("https://")
        ):
            raise PolicyError(f"policy: license review for {purl} is invalid")

    sources = policy["sources"]
    if not isinstance(sources, dict):
        raise PolicyError("policy: sources must be an object")
    require_keys(
        sources,
        {
            "denied_hosted_package_prefixes",
            "foundation",
            "npm_registry",
            "python_registry",
            "telemetry_must_default_off",
        },
        "policy.sources",
    )
    if (
        sources["python_registry"] != "https://pypi.org/simple"
        or sources["npm_registry"] != "https://registry.npmjs.org"
        or sources["telemetry_must_default_off"] is not True
    ):
        raise PolicyError("policy: source registry/telemetry boundary is invalid")
    denied_prefixes = sources["denied_hosted_package_prefixes"]
    if (
        not isinstance(denied_prefixes, list)
        or denied_prefixes != sorted(set(denied_prefixes))
        or not all(isinstance(item, str) and item for item in denied_prefixes)
    ):
        raise PolicyError("policy: denied hosted package prefixes are malformed")
    foundation = sources["foundation"]
    if not isinstance(foundation, dict):
        raise PolicyError("policy: foundation source must be an object")
    require_keys(
        foundation,
        {"distribution", "import", "sdist_sha256", "version", "wheel_sha256"},
        "policy.sources.foundation",
    )
    if (
        foundation["distribution"] != "agent-cow-postgresql"
        or foundation["import"] != "agentcow.postgres"
        or foundation["version"] != "0.2.0"
        or not SHA256.fullmatch(str(foundation["wheel_sha256"]))
        or not SHA256.fullmatch(str(foundation["sdist_sha256"]))
    ):
        raise PolicyError("policy: foundation source identity is invalid")

    actions = policy["github_actions"]
    if not isinstance(actions, dict) or not actions:
        raise PolicyError("policy: github_actions must be a non-empty object")
    for action, revision in actions.items():
        if not isinstance(action, str) or not FULL_SHA.fullmatch(str(revision)):
            raise PolicyError(f"policy: invalid GitHub Action pin for {action}")

    images = policy["oci_sources"]
    if not isinstance(images, dict) or len(images) < 6:
        raise PolicyError("policy: OCI source inventory is incomplete")
    for name, reference in images.items():
        if not isinstance(reference, str) or not IMMUTABLE_IMAGE.fullmatch(reference):
            raise PolicyError(f"policy: OCI source {name} is not tag+digest pinned")

    overrides = policy["alpine_package_overrides"]
    if not isinstance(overrides, dict) or set(overrides) != {"images", "registry"}:
        raise PolicyError("policy: Alpine package overrides are malformed")
    if overrides["registry"] != "https://dl-cdn.alpinelinux.org/alpine/v3.23":
        raise PolicyError("policy: Alpine package registry is not exact and approved")
    expected_override_images = {"apache", "backend", "nginx", "postgres", "web"}
    if (
        not isinstance(overrides["images"], dict)
        or set(overrides["images"]) != expected_override_images
    ):
        raise PolicyError(
            "policy: Alpine package override image coverage is incomplete"
        )
    for name, configuration in overrides["images"].items():
        if not isinstance(configuration, dict) or set(configuration) != {
            "install",
            "remove",
        }:
            raise PolicyError(
                f"policy: Alpine package overrides for {name} are malformed"
            )
        installed = configuration["install"]
        removed = configuration["remove"]
        if not isinstance(installed, list) or not all(
            isinstance(item, str)
            and re.fullmatch(
                r"[a-z0-9][a-z0-9+_.-]*=[0-9][a-zA-Z0-9+_.-]*-r[0-9]+", item
            )
            for item in installed
        ):
            raise PolicyError(
                f"policy: Alpine package overrides for {name} are not exact"
            )
        if installed != sorted(set(installed)):
            raise PolicyError(
                f"policy: Alpine package overrides for {name} are not sorted"
            )
        if not isinstance(removed, list) or removed != sorted(set(removed)):
            raise PolicyError(
                f"policy: Alpine package removals for {name} are malformed"
            )

    browser_runtime = policy["browser_runtime"]
    if not isinstance(browser_runtime, dict):
        raise PolicyError("policy: browser runtime must be an object")
    require_keys(
        browser_runtime,
        {
            "allowed_capabilities",
            "base_image",
            "chromium_archive_sha256",
            "chromium_archive_url",
            "chromium_executable",
            "chromium_revision",
            "chromium_version",
            "forbidden_product_browsers",
            "node_version",
            "platform",
            "playwright_core_version",
            "seccomp_profile_sha256",
        },
        "policy.browser_runtime",
    )
    if (
        browser_runtime["base_image"] != "playwright"
        or browser_runtime["playwright_core_version"] != "1.62.1"
        or browser_runtime["chromium_revision"] != "1669021"
        or browser_runtime["chromium_version"] != "152.0.7977.82"
        or browser_runtime["chromium_archive_url"]
        != "https://storage.googleapis.com/chrome-for-testing-public/152.0.7977.82/linux64/chrome-linux64.zip"
        or browser_runtime["chromium_archive_sha256"]
        != "0704631fb3e4f741092e08f55272f90abc3e307f991f05f332924364415b02e0"
        or browser_runtime["platform"] != "linux/amd64"
        or browser_runtime["node_version"] != "24.18.1"
        or browser_runtime["chromium_executable"]
        != "/ms-playwright/chromium-1669021/chrome-linux64/chrome"
        or browser_runtime["allowed_capabilities"] != ["SYS_CHROOT"]
        or browser_runtime["forbidden_product_browsers"] != ["firefox", "webkit"]
        or not SHA256.fullmatch(str(browser_runtime["seccomp_profile_sha256"]))
    ):
        raise PolicyError("policy: browser runtime facts are invalid")

    scanners = policy["scanner_tools"]
    if not isinstance(scanners, dict) or set(scanners) != {"grype", "syft"}:
        raise PolicyError("policy: scanner set must be exactly grype and syft")
    scanner_required = {
        "image",
        "license",
        "release_certificate_sha256",
        "release_checksums_sha256",
        "release_signature_sha256",
        "source",
        "source_commit",
        "version",
    }
    for name, scanner in scanners.items():
        if not isinstance(scanner, dict):
            raise PolicyError(f"policy: scanner {name} must be an object")
        require_keys(scanner, scanner_required, f"policy.scanner_tools.{name}")
        if not IMMUTABLE_IMAGE.fullmatch(str(scanner["image"])):
            raise PolicyError(f"policy: scanner {name} image is mutable")
        if scanner["license"] != "Apache-2.0":
            raise PolicyError(f"policy: scanner {name} license is not reviewed")
        if not FULL_SHA.fullmatch(str(scanner["source_commit"])):
            raise PolicyError(f"policy: scanner {name} source commit is not exact")
        for field in (
            "release_certificate_sha256",
            "release_checksums_sha256",
            "release_signature_sha256",
        ):
            if not SHA256.fullmatch(str(scanner[field])):
                raise PolicyError(f"policy: scanner {name} {field} is invalid")

    required_images = policy["required_images"]
    expected = {"apache", "backend", "browser-worker", "nginx", "postgres", "web"}
    if not isinstance(required_images, dict) or set(required_images) != expected:
        raise PolicyError("policy: required image set must contain exactly six targets")
    for name, image in required_images.items():
        if not isinstance(image, dict):
            raise PolicyError(f"policy: required image {name} must be an object")
        require_keys(
            image,
            {"base", "expected_components", "local_reference"},
            f"policy.required_images.{name}",
        )
        if image["base"] not in images:
            raise PolicyError(f"policy: required image {name} has unknown base")
        if (
            not isinstance(image["expected_components"], list)
            or not image["expected_components"]
        ):
            raise PolicyError(f"policy: required image {name} has no component checks")

    vulnerability = policy["vulnerability_policy"]
    if not isinstance(vulnerability, dict):
        raise PolicyError("policy: vulnerability_policy must be an object")
    require_keys(
        vulnerability,
        {
            "fail_severities",
            "maximum_database_age_hours",
            "maximum_exception_days",
            "review_severities",
            "unfixed_critical_still_fails",
        },
        "policy.vulnerability_policy",
    )
    if vulnerability.get("fail_severities") != ["Critical"]:
        raise PolicyError("policy: every Critical vulnerability must fail")
    if vulnerability.get("review_severities") != ["High"]:
        raise PolicyError("policy: High vulnerabilities must remain review evidence")
    if vulnerability.get("unfixed_critical_still_fails") is not True:
        raise PolicyError("policy: unfixed Critical vulnerabilities must fail")
    age = vulnerability.get("maximum_database_age_hours")
    days = vulnerability.get("maximum_exception_days")
    if not isinstance(age, int) or not 1 <= age <= 168:
        raise PolicyError("policy: vulnerability DB age must be at most seven days")
    if not isinstance(days, int) or not 1 <= days <= 90:
        raise PolicyError("policy: exception lifetime must be at most 90 days")

    evidence = policy["evidence"]
    if not isinstance(evidence, dict):
        raise PolicyError("policy: evidence must be an object")
    require_keys(
        evidence,
        {
            "checksum",
            "forbidden_host_prefixes",
            "forbidden_secret_markers",
            "formats",
            "normalization",
            "required_index_version",
            "retention_days",
        },
        "policy.evidence",
    )
    if evidence["checksum"] != "SHA-256" or evidence["required_index_version"] != 1:
        raise PolicyError("policy: evidence checksum/index contract is invalid")
    if evidence["formats"] != [
        "application/gzip",
        "application/json",
        "application/spdx+json",
        "application/zip",
        "text/plain",
    ]:
        raise PolicyError("policy: evidence format contract is invalid")
    if evidence["normalization"] != (
        "JSON/text are UTF-8 and deterministic; binary application artifacts "
        "retain exact bytes"
    ):
        raise PolicyError("policy: evidence normalization contract is invalid")
    if (
        not isinstance(evidence["retention_days"], int)
        or not 1 <= evidence["retention_days"] <= 30
    ):
        raise PolicyError("policy: evidence retention must be between 1 and 30 days")


def parse_iso_date(value: object, label: str) -> date:
    if not isinstance(value, str):
        raise PolicyError(f"{label}: must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PolicyError(f"{label}: must be an ISO date") from exc


def validate_exceptions(
    document: dict[str, Any],
    kind: str,
    maximum_days: int,
    today: date | None = None,
) -> None:
    if set(document) != {"exceptions", "schema_version"}:
        raise PolicyError(f"{kind} exceptions: unexpected or missing root keys")
    if document["schema_version"] != 1 or not isinstance(document["exceptions"], list):
        raise PolicyError(f"{kind} exceptions: invalid schema")
    current = today or date.today()
    common = {
        "affected",
        "approver",
        "created",
        "expires",
        "identifier",
        "rationale",
        "reference",
        "scope",
    }
    seen: set[tuple[str, str, str]] = set()
    for index, entry in enumerate(document["exceptions"]):
        label = f"{kind} exceptions[{index}]"
        if not isinstance(entry, dict) or set(entry) != common:
            raise PolicyError(f"{label}: fields must match the bounded schema")
        for field in (
            "affected",
            "approver",
            "identifier",
            "rationale",
            "reference",
            "scope",
        ):
            value = entry[field]
            if not isinstance(value, str) or not value.strip():
                raise PolicyError(f"{label}.{field}: must be non-empty")
            if any(character in value for character in "*?[]"):
                raise PolicyError(f"{label}.{field}: wildcards are forbidden")
        if len(entry["rationale"].strip()) < 12:
            raise PolicyError(f"{label}.rationale: must explain the exception")
        if not entry["approver"].startswith("human:"):
            raise PolicyError(f"{label}.approver: must identify a human approver")
        if not re.fullmatch(
            r"https://github\.com/[^\s]+/(?:issues|pull)/\d+", entry["reference"]
        ):
            raise PolicyError(f"{label}.reference: must be an exact GitHub review URL")
        created = parse_iso_date(entry["created"], f"{label}.created")
        expires = parse_iso_date(entry["expires"], f"{label}.expires")
        if expires <= created or (expires - created).days > maximum_days:
            raise PolicyError(f"{label}: expiry exceeds the bounded lifetime")
        if expires < current:
            raise PolicyError(f"{label}: exception is already expired")
        key = (entry["identifier"], entry["affected"], entry["scope"])
        if key in seen:
            raise PolicyError(f"{label}: duplicate exception")
        seen.add(key)


def canonical_image(reference: str) -> str:
    registry, separator, remainder = reference.partition("/")
    if separator and registry in {"ghcr.io", "docker.io"}:
        return reference
    if separator and ("." in registry or ":" in registry or registry == "localhost"):
        return reference
    if not separator:
        return f"docker.io/library/{reference}"
    return f"docker.io/{registry}/{remainder}"


def dependency_name(requirement: str) -> str:
    match = REQUIREMENT_NAME.match(requirement)
    if match is None:
        raise PolicyError(f"invalid Python requirement: {requirement}")
    return normalized_name(match.group(0))


def iter_node_manifests(root: Path) -> list[Path]:
    candidates = [root / "package.json", root / "apps/web/package.json"]
    candidates.extend(sorted((root / "packages").glob("*/package.json")))
    candidates.append(root / "services/browser-worker/package.json")
    return [path for path in candidates if path.is_file()]


def validate_dependency_sources(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_requirements = pyproject.get("project", {}).get("dependencies", [])
    grouped_requirements = [
        requirement
        for requirements in pyproject.get("dependency-groups", {}).values()
        for requirement in requirements
    ]
    for requirement in [*runtime_requirements, *grouped_requirements]:
        lowered = str(requirement).casefold()
        if any(
            marker in lowered
            for marker in ("git+", "http://", "https://", "file:", " @ ", "-e ")
        ):
            raise PolicyError(
                f"pyproject.toml: forbidden dependency source {requirement}"
            )
    for requirement in runtime_requirements:
        if not re.fullmatch(
            r"[A-Za-z0-9_.-]+==\d+\.\d+\.\d+(?:[A-Za-z0-9.+-]*)?",
            str(requirement),
        ):
            raise PolicyError(
                f"pyproject.toml: runtime dependency is not exact: {requirement}"
            )
    uv_lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    registry = policy["sources"]["python_registry"]
    for package in uv_lock.get("package", []):
        source = package.get("source")
        if package.get("name") == "slaif-agent-site":
            if source != {"editable": "."}:
                raise PolicyError(
                    "uv.lock: local project must be the sole editable source"
                )
        elif source != {"registry": registry}:
            raise PolicyError(
                f"uv.lock: {package.get('name')} has an unapproved source"
            )
        for artifact in [package.get("sdist"), *(package.get("wheels") or [])]:
            if artifact is None:
                continue
            if not isinstance(artifact, dict) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", str(artifact.get("hash", ""))
            ):
                raise PolicyError(
                    f"uv.lock: {package.get('name')} has an unhashed artifact"
                )

    denied = tuple(policy["sources"]["denied_hosted_package_prefixes"])
    node_direct: dict[str, dict[str, str]] = {}
    lifecycle = {
        "install",
        "postinstall",
        "postpack",
        "preinstall",
        "prepack",
        "prepare",
        "prepublish",
        "prepublishOnly",
    }
    for path in iter_node_manifests(root):
        manifest = load_json(path)
        scripts = manifest.get("scripts", {})
        if isinstance(scripts, dict) and lifecycle & set(scripts):
            raise PolicyError(
                f"{path.relative_to(root)}: lifecycle scripts are forbidden"
            )
        for field in ("dependencies", "devDependencies", "optionalDependencies"):
            dependencies = manifest.get(field, {})
            if not isinstance(dependencies, dict):
                continue
            for name, version in dependencies.items():
                lower = name.casefold()
                if lower.startswith(denied):
                    raise PolicyError(
                        f"{path.relative_to(root)}: hosted SDK is forbidden: {name}"
                    )
                if not isinstance(version, str) or not (
                    re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version)
                    or re.fullmatch(r"workspace:\d+\.\d+\.\d+", version)
                ):
                    raise PolicyError(
                        f"{path.relative_to(root)}: mutable dependency {name}@{version}"
                    )
                node_direct[name] = {"field": field, "version": version}

    pnpm_text = (root / "pnpm-lock.yaml").read_text(encoding="utf-8")
    for forbidden in (
        "git+",
        "github:",
        "gitlab:",
        "bitbucket:",
        "tarball:",
        "patcheddependencies:",
    ):
        if forbidden in pnpm_text.casefold():
            raise PolicyError(f"pnpm-lock.yaml: forbidden source marker {forbidden}")
    for line in pnpm_text.splitlines():
        if re.search(r"(?:specifier|version):\s*(?:file:|https?:|git\+)", line):
            raise PolicyError("pnpm-lock.yaml: forbidden direct package source")
        if "link:" in line and not (
            re.fullmatch(r"\s+version: link:packages/[a-z0-9-]+", line)
            or line == "        version: link:../../packages/browser-tool-contracts"
        ):
            raise PolicyError(
                "pnpm-lock.yaml: workspace link escapes approved packages"
            )
    for line in pnpm_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("preinstall:", "install:", "postinstall:")):
            raise PolicyError("pnpm-lock.yaml: unapproved install script metadata")

    configured_actions = policy["github_actions"]
    discovered_actions: dict[str, str] = {}
    for workflow in sorted((root / ".github/workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for reference in ACTION.findall(text):
            if reference.startswith("./"):
                continue
            if "@" not in reference:
                raise PolicyError(
                    f"{workflow.relative_to(root)}: unpinned action {reference}"
                )
            action, revision = reference.rsplit("@", 1)
            if not FULL_SHA.fullmatch(revision):
                raise PolicyError(
                    f"{workflow.relative_to(root)}: mutable action {reference}"
                )
            if configured_actions.get(action) != revision:
                raise PolicyError(
                    f"{workflow.relative_to(root)}: unreviewed action {action}"
                )
            discovered_actions[action] = revision
    unused_actions = sorted(set(configured_actions) - set(discovered_actions))
    if unused_actions:
        raise PolicyError(
            f"policy: unused approved actions: {', '.join(unused_actions)}"
        )

    docker_references: set[str] = set()
    for dockerfile in sorted(root.glob("**/Dockerfile")):
        if any(part in {".git", ".next", "node_modules"} for part in dockerfile.parts):
            continue
        for line in dockerfile.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^(?:FROM\s+|COPY\s+--from=)(\S+)", line)
            if match is None:
                continue
            reference = match.group(1)
            if reference in {"builder", "runtime"}:
                continue
            canonical = canonical_image(reference)
            if not IMMUTABLE_IMAGE.fullmatch(canonical):
                raise PolicyError(
                    f"{dockerfile.relative_to(root)}: mutable image {reference}"
                )
            docker_references.add(canonical)
    compose = (root / "compose.yaml").read_text(encoding="utf-8")
    for reference in re.findall(
        r"^\s+image:\s+(\S+@sha256:[0-9a-f]{64})$", compose, re.MULTILINE
    ):
        docker_references.add(canonical_image(reference))
    expected_sources = set(policy["oci_sources"].values())
    if docker_references != expected_sources:
        missing = sorted(expected_sources - docker_references)
        extra = sorted(docker_references - expected_sources)
        raise PolicyError(f"OCI source drift: missing={missing} extra={extra}")

    override_paths = {
        "apache": root / "infra/apache/Dockerfile",
        "backend": root / "services/backend/Dockerfile",
        "nginx": root / "infra/nginx/Dockerfile",
        "postgres": root / "infra/postgres/Dockerfile",
        "web": root / "apps/web/Dockerfile",
    }
    for name, configuration in policy["alpine_package_overrides"]["images"].items():
        dockerfile_text = override_paths[name].read_text(encoding="utf-8")
        for package in configuration["install"]:
            if f"'{package}'" not in dockerfile_text:
                raise PolicyError(f"{name}: missing exact Alpine package {package}")
        for package in configuration["remove"]:
            if package == "npm":
                marker = "find /usr/local/lib/node_modules/npm -depth -delete"
            else:
                marker = f"apk del {package}"
            if marker not in dockerfile_text:
                raise PolicyError(f"{name}: missing Alpine package removal {package}")

    browser_runtime = policy["browser_runtime"]
    worker_dockerfile = (root / "services/browser-worker/Dockerfile").read_text(
        encoding="utf-8"
    )
    worker_manifest = (root / "services/browser-worker/package.json").read_text(
        encoding="utf-8"
    )
    for fact, content in (
        (browser_runtime["chromium_executable"], worker_dockerfile),
        (browser_runtime["chromium_version"], worker_dockerfile),
        (browser_runtime["chromium_archive_url"], worker_dockerfile),
        (browser_runtime["chromium_archive_sha256"], worker_dockerfile),
        (
            f'"playwright-core": "{browser_runtime["playwright_core_version"]}"',
            worker_manifest,
        ),
    ):
        if fact not in content:
            raise PolicyError(f"browser-worker: missing runtime fact {fact}")
    profile = root / "services/browser-worker/seccomp_profile.json"
    if (
        not profile.is_file()
        or hashlib.sha256(profile.read_bytes()).hexdigest()
        != browser_runtime["seccomp_profile_sha256"]
    ):
        raise PolicyError("browser-worker: seccomp profile drift")

    return {
        "github_actions": [
            {
                "name": name,
                "revision": revision,
                "source": f"https://github.com/{name}",
            }
            for name, revision in sorted(discovered_actions.items())
        ],
        "oci_sources": [
            {"name": name, "reference": reference}
            for name, reference in sorted(policy["oci_sources"].items())
        ],
        "python_registry": registry,
        "npm_registry": policy["sources"]["npm_registry"],
    }


def metadata_license(distribution: importlib.metadata.Distribution) -> str | None:
    expression = distribution.metadata.get("License-Expression")
    if expression:
        return normalize_license_expression(expression)
    license_value = distribution.metadata.get("License")
    if license_value and SIMPLE_LICENSE.fullmatch(license_value.strip()):
        return normalize_license_expression(license_value)
    classifiers = distribution.metadata.get_all("Classifier") or []
    known = {
        "License :: OSI Approved :: Apache Software License": "Apache-2.0",
        "License :: OSI Approved :: BSD License": "BSD-3-Clause",
        "License :: OSI Approved :: MIT License": "MIT",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
        "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
    }
    matches = sorted({known[item] for item in classifiers if item in known})
    return normalize_license_expression(" AND ".join(matches)) if matches else None


def metadata_source(
    distribution: importlib.metadata.Distribution, name: str, version: str
) -> str:
    urls = distribution.metadata.get_all("Project-URL") or []
    priorities = ("source", "repository", "homepage", "github")
    for priority in priorities:
        for value in urls:
            label, separator, url = value.partition(",")
            if separator and label.strip().casefold().startswith(priority):
                return url.strip()
    homepage = distribution.metadata.get("Home-page")
    if homepage:
        return homepage.strip()
    return f"https://pypi.org/project/{normalized_name(name)}/{version}/"


def python_inventory(root: Path, policy: dict[str, Any]) -> list[dict[str, Any]]:
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    packages = {
        normalized_name(str(item["name"])): item
        for item in lock.get("package", [])
        if item.get("name") != "slaif-agent-site"
    }
    graph = {
        name: {
            normalized_name(str(dependency["name"]))
            for dependency in item.get("dependencies", [])
            if isinstance(dependency, dict) and "name" in dependency
        }
        for name, item in packages.items()
    }
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_direct = {
        dependency_name(item) for item in pyproject["project"].get("dependencies", [])
    }
    group_direct: dict[str, str] = {}
    for group, requirements in pyproject.get("dependency-groups", {}).items():
        for requirement in requirements:
            group_direct[dependency_name(requirement)] = str(group)
    production: set[str] = set()
    queue = deque(sorted(runtime_direct))
    while queue:
        name = queue.popleft()
        if name in production:
            continue
        production.add(name)
        queue.extend(sorted(graph.get(name, set()) - production))

    installed = {
        normalized_name(str(distribution.metadata["Name"])): distribution
        for distribution in importlib.metadata.distributions()
        if distribution.metadata.get("Name")
    }
    reviews = policy["license_metadata_reviews"]
    entries: list[dict[str, Any]] = []
    for name, package in sorted(packages.items()):
        version = str(package["version"])
        purl = python_purl(name, version)
        distribution = installed.get(name)
        review = reviews.get(purl, {})
        license_expression = review.get("license") or (
            metadata_license(distribution) if distribution is not None else None
        )
        if license_expression:
            license_expression = normalize_license_expression(license_expression)
        source = review.get("source") or (
            metadata_source(distribution, name, version)
            if distribution is not None
            else f"https://pypi.org/project/{name}/{version}/"
        )
        scope = (
            "production"
            if name in production
            else group_direct.get(name, "development")
        )
        entries.append(
            {
                "direct": name in runtime_direct or name in group_direct,
                "ecosystem": "PyPI",
                "license": license_expression or "UNKNOWN",
                "name": name,
                "purl": purl,
                "scope": scope,
                "source": source,
                "version": version,
            }
        )
    return entries


def collect_node_tree(value: object, result: set[tuple[str, str]]) -> None:
    if isinstance(value, list):
        for item in value:
            collect_node_tree(item, result)
    elif isinstance(value, dict):
        name = value.get("name") or value.get("from")
        version = value.get("version")
        if name is None:
            for nested in value.values():
                collect_node_tree(nested, result)
            return
        if (
            isinstance(name, str)
            and isinstance(version, str)
            and not name.startswith("@slaif-agent-site/")
        ):
            result.add((name, version))
        for field in (
            "dependencies",
            "devDependencies",
            "optionalDependencies",
            "unsavedDependencies",
        ):
            collect_node_tree(value.get(field), result)


def run_json(command: list[str], root: Path) -> object:
    completed = subprocess.run(
        command,
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PolicyError(
            f"command returned invalid JSON: {' '.join(command)}"
        ) from exc


def node_inventory(root: Path) -> list[dict[str, Any]]:
    licenses = run_json(["pnpm", "licenses", "list", "--json"], root)
    production_tree = run_json(
        [
            "pnpm",
            "--filter",
            "@slaif-agent-site/web",
            "list",
            "--prod",
            "--depth",
            "Infinity",
            "--json",
        ],
        root,
    )
    production: set[tuple[str, str]] = set()
    collect_node_tree(production_tree, production)
    direct: set[str] = set()
    for path in iter_node_manifests(root):
        manifest = load_json(path)
        for field in ("dependencies", "devDependencies", "optionalDependencies"):
            dependencies = manifest.get(field, {})
            if isinstance(dependencies, dict):
                direct.update(
                    str(name)
                    for name in dependencies
                    if not name.startswith("@slaif-agent-site/")
                )

    if not isinstance(licenses, dict):
        raise PolicyError("pnpm license inventory must be an object")
    entries: list[dict[str, Any]] = []
    for license_expression, components in sorted(licenses.items()):
        if not isinstance(components, list):
            raise PolicyError(f"pnpm license group {license_expression} is malformed")
        for component in components:
            if not isinstance(component, dict):
                raise PolicyError("pnpm license component is malformed")
            name = component.get("name")
            versions = component.get("versions")
            if not isinstance(name, str) or not isinstance(versions, list):
                raise PolicyError("pnpm license component identity is malformed")
            source = component.get("homepage")
            for version in sorted(str(item) for item in versions):
                entries.append(
                    {
                        "direct": name in direct,
                        "ecosystem": "npm",
                        "license": normalize_license_expression(
                            str(license_expression)
                        ),
                        "name": name,
                        "purl": npm_purl(name, version),
                        "scope": "production"
                        if (name, version) in production
                        else "development",
                        "source": source
                        or (
                            "https://www.npmjs.com/package/"
                            f"{quote(name, safe='/')}/v/{version}"
                        ),
                        "version": version,
                    }
                )
    return sorted(entries, key=lambda item: (item["name"].casefold(), item["version"]))


def validate_application_licenses(
    entries: list[dict[str, Any]],
    policy: dict[str, Any],
    exceptions: list[dict[str, Any]] | None = None,
) -> None:
    licenses = policy["application_licenses"]
    approved = set(licenses["automatic"]) | set(licenses["attribution_review"])
    explicitly_reviewed = set(licenses["explicit_review"])
    prohibited = [item.casefold() for item in licenses["prohibited_tokens"]]
    reviews = policy["license_metadata_reviews"]
    exception_keys = {
        (item["identifier"], item["affected"], item["scope"])
        for item in (exceptions or [])
    }
    for entry in entries:
        expression = entry["license"]
        lower = expression.casefold()
        excepted = (expression, entry["purl"], entry["scope"]) in exception_keys
        if any(token in lower for token in prohibited):
            if excepted:
                continue
            raise PolicyError(f"{entry['purl']}: prohibited license {expression}")
        if expression == "UNKNOWN":
            if excepted:
                continue
            if entry["direct"] or licenses["unknown_direct_fails"]:
                raise PolicyError(f"{entry['purl']}: unknown application license")
            continue
        if expression in explicitly_reviewed:
            review = reviews.get(entry["purl"])
            if not isinstance(review, dict) or review.get("license") != expression:
                raise PolicyError(
                    f"{entry['purl']}: license {expression} lacks exact "
                    "component review"
                )
        elif expression not in approved:
            if excepted:
                continue
            review = reviews.get(entry["purl"])
            if not isinstance(review, dict) or review.get("license") != expression:
                raise PolicyError(
                    f"{entry['purl']}: unapproved application license {expression}"
                )


def dependency_inventories(
    root: Path,
    policy: dict[str, Any],
    license_exceptions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    python = python_inventory(root, policy)
    node = node_inventory(root)
    validate_application_licenses(python + node, policy, license_exceptions)
    return {
        "schema_version": 1,
        "python": python,
        "node": node,
    }


def notice_text(inventories: dict[str, Any], policy: dict[str, Any]) -> str:
    components = sorted(
        [*inventories["python"], *inventories["node"]],
        key=lambda item: (
            item["ecosystem"].casefold(),
            item["name"].casefold(),
            item["version"],
        ),
    )
    attribution = policy["attribution_notes"]
    lines = [
        "# Third-Party Notices",
        "",
        "This deterministic inventory is generated from the frozen Python and pnpm",
        "environments by `python tools/supply_chain/policy.py notices`. It is an",
        "engineering attribution record, not legal advice or a complete license",
        "opinion. Container operating-system packages are retained separately in the",
        "CI SBOM evidence bundle.",
        "",
        "| Component | Version | Ecosystem / scope | License / review | "
        "Source | Attribution |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in components:
        note = attribution.get(item["purl"], "—")
        source = str(item["source"]).replace("|", "%7C")
        lines.append(
            f"| `{item['name']}` | `{item['version']}` | "
            f"{item['ecosystem']} / {item['scope']} | `{item['license']}` | "
            f"<{source}> | {note} |"
        )
    lines.extend(
        [
            "",
            "## Required retained attribution",
            "",
            "SLAIF Agent-Site is Apache-2.0 licensed. The MIT-licensed",
            "`agent-cow-postgresql` foundation retains attribution to its upstream",
            "`agent-cow-python` lineage. `caniuse-lite` is CC-BY-4.0 browser",
            "compatibility data and retains its source attribution above. See `NOTICE`",
            "for the project and foundation notice text.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_all(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = load_json(root / POLICY_PATH.relative_to(ROOT))
    validate_policy(policy)
    maximum = policy["vulnerability_policy"]["maximum_exception_days"]
    validate_exceptions(
        load_json(root / LICENSE_EXCEPTIONS_PATH.relative_to(ROOT)),
        "license",
        maximum,
    )
    validate_exceptions(
        load_json(root / VULNERABILITY_EXCEPTIONS_PATH.relative_to(ROOT)),
        "vulnerability",
        maximum,
    )
    source_inventory = validate_dependency_sources(root, policy)
    return policy, source_inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    inventory_parser = subparsers.add_parser("inventory")
    inventory_parser.add_argument("--output", type=Path, required=True)
    notices_parser = subparsers.add_parser("notices")
    notices_parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    try:
        policy, sources = validate_all(root)
        if arguments.command == "validate":
            print("supply-chain-policy: OK")
            return 0
        license_exceptions = load_json(
            root / LICENSE_EXCEPTIONS_PATH.relative_to(ROOT)
        )["exceptions"]
        inventories = dependency_inventories(root, policy, license_exceptions)
        if arguments.command == "inventory":
            output = arguments.output.resolve()
            write_json(output / "application-dependencies.json", inventories)
            write_json(output / "source-provenance.json", sources)
            print(
                "dependency-inventory: OK "
                f"python={len(inventories['python'])} node={len(inventories['node'])}"
            )
            return 0
        generated = notice_text(inventories, policy)
        notices_path = root / NOTICES_PATH.relative_to(ROOT)
        if arguments.check:
            current = (
                notices_path.read_text(encoding="utf-8")
                if notices_path.is_file()
                else ""
            )
            if current != generated:
                raise PolicyError("THIRD_PARTY_NOTICES.md: generated notice drift")
            print(
                "third-party-notices: OK "
                f"components={len(inventories['python']) + len(inventories['node'])}"
            )
        else:
            notices_path.write_text(generated, encoding="utf-8")
            print(f"wrote {notices_path.relative_to(root)}")
    except (PolicyError, subprocess.CalledProcessError) as exc:
        print(f"supply-chain-policy: ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

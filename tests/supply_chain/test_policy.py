"""Negative and deterministic tests for the supply-chain policy model."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools.supply_chain.policy import (
    POLICY_PATH,
    ROOT,
    PolicyError,
    canonical_image,
    load_json,
    notice_text,
    validate_application_licenses,
    validate_dependency_sources,
    validate_exceptions,
    validate_policy,
)


class SupplyChainPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_json(POLICY_PATH)

    def test_repository_policy_and_sources_are_valid(self) -> None:
        validate_policy(self.policy)
        inventory = validate_dependency_sources(ROOT, self.policy)
        self.assertEqual(len(inventory["github_actions"]), 10)
        self.assertEqual(len(inventory["oci_sources"]), 7)

    def test_image_reference_canonicalization_is_structural(self) -> None:
        cases = {
            "ghcr.io/astral-sh/uv:0.12.5@sha256:" + "a" * 64: (
                "ghcr.io/astral-sh/uv:0.12.5@sha256:" + "a" * 64
            ),
            "docker.io/library/nginx:1.29.7@sha256:" + "b" * 64: (
                "docker.io/library/nginx:1.29.7@sha256:" + "b" * 64
            ),
            "registry.example/nginx:1.29.7@sha256:" + "c" * 64: (
                "registry.example/nginx:1.29.7@sha256:" + "c" * 64
            ),
            "nginx:1.29.7@sha256:" + "d" * 64: (
                "docker.io/library/nginx:1.29.7@sha256:" + "d" * 64
            ),
            "anchore/syft:v1.51.0@sha256:" + "e" * 64: (
                "docker.io/anchore/syft:v1.51.0@sha256:" + "e" * 64
            ),
        }
        for reference, expected in cases.items():
            with self.subTest(reference=reference):
                self.assertEqual(canonical_image(reference), expected)

    def test_policy_rejects_mutable_scanner_and_prohibited_allowance(self) -> None:
        mutable = copy.deepcopy(self.policy)
        mutable["scanner_tools"]["syft"]["image"] = "anchore/syft:latest"
        with self.assertRaisesRegex(PolicyError, "scanner syft image is mutable"):
            validate_policy(mutable)

        unpinned_os = copy.deepcopy(self.policy)
        unpinned_os["alpine_package_overrides"]["images"]["backend"]["install"][0] = (
            "libcrypto3"
        )
        with self.assertRaisesRegex(PolicyError, "not exact"):
            validate_policy(unpinned_os)

        prohibited = copy.deepcopy(self.policy)
        prohibited["application_licenses"]["automatic"].append("AGPL-3.0-only")
        with self.assertRaisesRegex(PolicyError, "prohibited license"):
            validate_policy(prohibited)

        incomplete_evidence = copy.deepcopy(self.policy)
        incomplete_evidence["evidence"]["formats"].remove("application/zip")
        with self.assertRaisesRegex(PolicyError, "evidence format contract"):
            validate_policy(incomplete_evidence)

    def test_unknown_prohibited_and_explicit_review_licenses_fail_closed(self) -> None:
        base = {
            "direct": True,
            "ecosystem": "PyPI",
            "name": "example",
            "purl": "pkg:pypi/example@1.0.0",
            "scope": "production",
            "source": "https://pypi.org/project/example/1.0.0/",
            "version": "1.0.0",
        }
        for license_expression, message in (
            ("UNKNOWN", "unknown application license"),
            ("AGPL-3.0-only", "prohibited license"),
            ("MPL-2.0", "lacks exact component review"),
        ):
            with self.subTest(license=license_expression):
                entry = base | {"license": license_expression}
                with self.assertRaisesRegex(PolicyError, message):
                    validate_application_licenses([entry], self.policy)

    def test_exception_schema_rejects_each_governance_escape(self) -> None:
        valid = {
            "schema_version": 1,
            "exceptions": [
                {
                    "affected": "pkg:pypi/example@1.0.0",
                    "approver": "human:security-owner",
                    "created": "2026-08-01",
                    "expires": "2026-08-30",
                    "identifier": "CVE-2026-1234",
                    "rationale": "Reviewed bounded compatibility requirement.",
                    "reference": "https://github.com/example/project/issues/42",
                    "scope": "backend",
                }
            ],
        }
        validate_exceptions(valid, "vulnerability", 90, date(2026, 8, 17))
        mutations = {
            "wildcard": ("affected", "pkg:pypi/*"),
            "missing approver": ("approver", "security-owner"),
            "expired": ("expires", "2026-08-16"),
            "too long": ("expires", "2027-08-30"),
            "missing reference": ("reference", "approval-42"),
        }
        for label, (field, value) in mutations.items():
            with self.subTest(label=label):
                document = copy.deepcopy(valid)
                document["exceptions"][0][field] = value
                with self.assertRaises(PolicyError):
                    validate_exceptions(
                        document, "vulnerability", 90, date(2026, 8, 17)
                    )
        duplicate = copy.deepcopy(valid)
        duplicate["exceptions"].append(copy.deepcopy(duplicate["exceptions"][0]))
        with self.assertRaisesRegex(PolicyError, "duplicate"):
            validate_exceptions(duplicate, "vulnerability", 90, date(2026, 8, 17))

    def test_license_exception_matches_expression_purl_and_scope_exactly(self) -> None:
        entry = {
            "direct": True,
            "ecosystem": "PyPI",
            "license": "AGPL-3.0-only",
            "name": "example",
            "purl": "pkg:pypi/example@1.0.0",
            "scope": "production",
            "source": "https://pypi.org/project/example/1.0.0/",
            "version": "1.0.0",
        }
        exception = {
            "affected": entry["purl"],
            "approver": "human:security-owner",
            "created": "2026-08-01",
            "expires": "2026-08-30",
            "identifier": entry["license"],
            "rationale": "Reviewed bounded compatibility requirement.",
            "reference": "https://github.com/example/project/issues/42",
            "scope": entry["scope"],
        }
        validate_exceptions(
            {"schema_version": 1, "exceptions": [exception]},
            "license",
            90,
            date(2026, 8, 17),
        )
        validate_application_licenses([entry], self.policy, [exception])

        for field, value in (
            ("identifier", "AGPL-3.0-or-later"),
            ("affected", "pkg:pypi/example@1.0.1"),
            ("scope", "development"),
        ):
            with self.subTest(field=field):
                near_miss = copy.deepcopy(exception)
                near_miss[field] = value
                with self.assertRaisesRegex(PolicyError, "prohibited license"):
                    validate_application_licenses([entry], self.policy, [near_miss])

    def test_empty_exception_files_are_valid(self) -> None:
        for name in ("license-exceptions.json",):
            document = load_json(ROOT / "supply-chain" / name)
            validate_exceptions(document, name, 90, date(2026, 8, 17))
            self.assertEqual(document["exceptions"], [])

        vulnerability = load_json(ROOT / "supply-chain/vulnerability-exceptions.json")
        validate_exceptions(vulnerability, "vulnerability", 90, date(2026, 8, 17))
        expected = {
            "CVE-2026-78900",
            "CVE-2026-78904",
            "CVE-2026-78909",
            "CVE-2026-78935",
            "CVE-2026-78937",
            "CVE-2026-78939",
            "CVE-2026-78945",
            "CVE-2026-78948",
            "CVE-2026-78951",
            "CVE-2026-78964",
            "CVE-2026-78985",
            "CVE-2026-79012",
            "CVE-2026-79026",
            "CVE-2026-79043",
            "CVE-2026-79047",
            "CVE-2026-79052",
            "CVE-2026-79056",
            "CVE-2026-79064",
            "CVE-2026-79078",
            "CVE-2026-79091",
            "CVE-2026-79111",
            "CVE-2026-79128",
            "CVE-2026-79129",
            "CVE-2026-79130",
            "CVE-2026-79131",
            "CVE-2026-79140",
            "CVE-2026-79149",
            "CVE-2026-79150",
            "CVE-2026-79152",
            "CVE-2026-79188",
            "CVE-2026-79189",
        }
        self.assertEqual(
            {entry["identifier"] for entry in vulnerability["exceptions"]}, expected
        )
        self.assertEqual(len(vulnerability["exceptions"]), 31)

    def test_notice_generation_is_sorted_and_deterministic(self) -> None:
        component = {
            "direct": True,
            "ecosystem": "PyPI",
            "license": "MIT",
            "name": "zeta",
            "purl": "pkg:pypi/zeta@1.0.0",
            "scope": "production",
            "source": "https://pypi.org/project/zeta/1.0.0/",
            "version": "1.0.0",
        }
        inventories = {"python": [component], "node": []}
        first = notice_text(inventories, self.policy)
        second = notice_text(copy.deepcopy(inventories), self.policy)
        self.assertEqual(first, second)
        self.assertIn("`zeta`", first)
        self.assertNotIn(str(ROOT), first)


class DependencySourceNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.policy = load_json(POLICY_PATH)
        files = [
            ".github/workflows/ci.yml",
            ".github/workflows/codeql.yml",
            "apps/web/Dockerfile",
            "apps/web/package.json",
            "compose.yaml",
            "infra/apache/Dockerfile",
            "infra/nginx/Dockerfile",
            "package.json",
            "pnpm-lock.yaml",
            "pyproject.toml",
            "services/backend/Dockerfile",
            "services/browser-worker/Dockerfile",
            "services/browser-worker/package.json",
            "uv.lock",
        ]
        files.extend(
            path.relative_to(ROOT).as_posix()
            for path in sorted((ROOT / "packages").glob("*/package.json"))
        )
        for relative in files:
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def replace(self, relative: str, old: str, new: str) -> None:
        path = self.root / relative
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assert_source_error(self, message: str) -> None:
        with self.assertRaisesRegex(PolicyError, message):
            validate_dependency_sources(self.root, self.policy)

    def test_rejects_vcs_direct_url_and_unapproved_registry(self) -> None:
        self.replace(
            "uv.lock",
            'source = { registry = "https://pypi.org/simple" }',
            'source = { git = "https://example.invalid/project.git" }',
        )
        self.assert_source_error("unapproved source")

    def test_rejects_mutable_runtime_requirement(self) -> None:
        self.replace("pyproject.toml", "asyncpg==0.31.0", "asyncpg>=0.31")
        self.assert_source_error("runtime dependency is not exact")

    def test_rejects_hosted_sdk_and_npm_range(self) -> None:
        path = self.root / "apps/web/package.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["dependencies"]["@aws-sdk/client-s3"] = "3.0.0"
        path.write_text(json.dumps(document) + "\n", encoding="utf-8")
        self.assert_source_error("hosted SDK")

        document["dependencies"].pop("@aws-sdk/client-s3")
        document["dependencies"]["next"] = "^16.3.1"
        path.write_text(json.dumps(document) + "\n", encoding="utf-8")
        self.assert_source_error("mutable dependency")

    def test_rejects_patch_link_escape_and_install_script(self) -> None:
        lock = self.root / "pnpm-lock.yaml"
        lock.write_text(
            lock.read_text(encoding="utf-8") + "\npatchedDependencies: {}\n",
            encoding="utf-8",
        )
        self.assert_source_error("patcheddependencies")

        shutil.copy2(ROOT / "pnpm-lock.yaml", lock)
        self.replace(
            "pnpm-lock.yaml",
            "version: link:packages/api-client",
            "version: link:../../outside",
        )
        self.assert_source_error("workspace link escapes")

        shutil.copy2(ROOT / "pnpm-lock.yaml", lock)
        path = self.root / "apps/web/package.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["scripts"]["postinstall"] = "node install.js"
        path.write_text(json.dumps(document) + "\n", encoding="utf-8")
        self.assert_source_error("lifecycle scripts")

    def test_rejects_mutable_action_and_image(self) -> None:
        checkout = self.policy["github_actions"]["actions/checkout"]
        self.replace(
            ".github/workflows/ci.yml",
            f"actions/checkout@{checkout}",
            "actions/checkout@main",
        )
        self.assert_source_error("mutable action")

        shutil.copy2(
            ROOT / ".github/workflows/ci.yml", self.root / ".github/workflows/ci.yml"
        )
        self.replace(
            "infra/nginx/Dockerfile",
            "nginx:1.29.7-alpine3.23@sha256:",
            "nginx:latest # removed-digest-",
        )
        self.assert_source_error("mutable image")


if __name__ == "__main__":
    unittest.main()

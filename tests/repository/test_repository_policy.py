"""Isolated unit tests for the repository preparation policy."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.check_repository import (
    APPROVED_ACTIONS,
    FOUNDATION_REGISTRY,
    FOUNDATION_SDIST,
    FOUNDATION_SDIST_SHA256,
    FOUNDATION_VERSION,
    FOUNDATION_WHEEL,
    FOUNDATION_WHEEL_SHA256,
    RepositoryPolicy,
)


class RepositoryPolicyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write(self, relative: str, content: str | bytes = "") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def errors_from(self, method: str, *args: object) -> list[str]:
        policy = RepositoryPolicy(self.root)
        getattr(policy, method)(*args)
        return policy.errors

    def test_oap_accepts_active_without_report_and_complete_history(self) -> None:
        self.write("oap/active", "001-a\n")
        self.write("oap/orders/000-a-history.md")
        self.write("oap/reports/000-a-history.md")
        self.write("oap/orders/001-a-active.md")

        self.assertEqual(self.errors_from("check_oap"), [])

    def test_oap_rejects_missing_historical_report(self) -> None:
        self.write("oap/active", "001-a\n")
        self.write("oap/orders/000-a-history.md")
        self.write("oap/orders/001-a-active.md")
        self.write("oap/reports/.keep", "")

        errors = self.errors_from("check_oap")

        self.assertTrue(
            any("000-a must have exactly one report" in error for error in errors)
        )

    def test_oap_rejects_duplicate_active_artifacts_and_temporary_files(self) -> None:
        self.write("oap/active", "001-a\n")
        self.write("oap/orders/001-a-one.md")
        self.write("oap/orders/001-a-two.md")
        self.write("oap/reports/001-a-one.md")
        self.write("oap/reports/001-a-two.md")
        self.write("oap/reports/.001-a.tmp", "pending")

        errors = self.errors_from("check_oap")

        self.assertTrue(any("2 order files" in error for error in errors))
        self.assertTrue(any("more than one report" in error for error in errors))
        self.assertTrue(any("temporary/publication" in error for error in errors))

    def test_logo_hash_and_safe_shape_pass_then_tampering_fails(self) -> None:
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>\n'
        path = self.write("docs/assets/slaif-logo.svg", svg)
        digest = hashlib.sha256(svg).hexdigest()

        self.assertEqual(self.errors_from("check_logo", digest), [])

        path.write_bytes(svg + b" ")
        errors = self.errors_from("check_logo", digest)
        self.assertTrue(any("SHA-256" in error for error in errors))

    def test_logo_rejects_active_content_and_external_resources(self) -> None:
        svg = (
            b'<svg xmlns="http://www.w3.org/2000/svg" onload="go()">'
            b'<script>go()</script><image href="https://example.test/a.png"/></svg>'
        )
        self.write("docs/assets/slaif-logo.svg", svg)

        errors = self.errors_from("check_logo", hashlib.sha256(svg).hexdigest())

        self.assertTrue(any("event-handler" in error for error in errors))
        self.assertTrue(any("forbidden <script>" in error for error in errors))
        self.assertTrue(any("external resource" in error for error in errors))

    def test_markdown_allows_exactly_two_space_hard_break(self) -> None:
        self.write("example.md", "first line  \nsecond line\n")

        self.assertEqual(self.errors_from("check_text_files"), [])

    def test_trailing_whitespace_rejects_one_three_and_tab(self) -> None:
        for label, ending in (("one", " "), ("three", "   "), ("tab", "\t")):
            with self.subTest(label=label):
                path = self.write("example.md", f"line{ending}\n")
                errors = self.errors_from("check_text_files")
                self.assertTrue(
                    any("invalid trailing whitespace" in error for error in errors)
                )
                path.unlink()

    def test_workflow_accepts_approved_full_sha_and_local_action(self) -> None:
        checkout = APPROVED_ACTIONS["actions/checkout"]
        self.write(
            ".github/workflows/check.yml",
            "jobs:\n"
            "  check:\n"
            "    steps:\n"
            f"      - uses: actions/checkout@{checkout} # v7.0.1\n"
            "      - uses: ./.github/actions/local\n",
        )

        self.assertEqual(self.errors_from("check_workflows"), [])

    def test_workflow_accepts_exact_setup_uv_pin_and_release_comment(self) -> None:
        setup_uv = APPROVED_ACTIONS["astral-sh/setup-uv"]
        self.write(
            ".github/workflows/python.yml",
            "jobs:\n"
            "  check:\n"
            "    steps:\n"
            f"      - uses: astral-sh/setup-uv@{setup_uv} # v10.0.1\n",
        )

        self.assertEqual(self.errors_from("check_workflows"), [])

    def test_workflow_rejects_mutable_and_unapproved_action_revisions(self) -> None:
        self.write(
            ".github/workflows/check.yml",
            "jobs:\n"
            "  check:\n"
            "    steps:\n"
            "      - uses: actions/checkout@main # v7.0.1\n"
            f"      - uses: actions/checkout@{'0' * 40} # v7.0.1\n",
        )

        errors = self.errors_from("check_workflows")

        self.assertTrue(any("not a lowercase full SHA" in error for error in errors))
        self.assertTrue(any("revision is not approved" in error for error in errors))

    def test_workflow_rejects_dangerous_trigger_and_write_permissions(self) -> None:
        self.write(
            ".github/workflows/check.yml",
            "on:\n  pull_request_target:\npermissions:\n  contents: write\n",
        )

        errors = self.errors_from("check_workflows")

        self.assertTrue(any("pull_request_target" in error for error in errors))
        self.assertTrue(any("contents: write" in error for error in errors))

    def make_linked_readme(self) -> None:
        for target in (
            ".github/workflows/ci.yml",
            ".github/workflows/codeql.yml",
            "AGENTS.md",
            "ARCHITECTURE.md",
            "CONTRIBUTING.md",
            "docs/FOUNDATION_INTEGRATION.md",
            "LICENSE",
            "NOTICE",
            "SECURITY.md",
            "docs/assets/README.md",
            "docs/assets/slaif-logo.svg",
        ):
            self.write(target)
        (self.root / "oap").mkdir(exist_ok=True)
        links = "\n".join(
            f"[{target}]({target})"
            for target in (
                ".github/workflows/ci.yml",
                ".github/workflows/codeql.yml",
                "AGENTS.md",
                "ARCHITECTURE.md",
                "CONTRIBUTING.md",
                "docs/FOUNDATION_INTEGRATION.md",
                "LICENSE",
                "NOTICE",
                "SECURITY.md",
                "docs/assets/README.md",
                "oap/",
            )
        )
        self.write(
            "README.md",
            '<a href="https://www.slaif.si">\n'
            '  <img src="docs/assets/slaif-logo.svg" alt="SLAIF logo" width="240">\n'
            "</a>\n"
            f"{links}\n",
        )

    def test_readme_accepts_local_logo_and_resolving_links(self) -> None:
        self.make_linked_readme()

        self.assertEqual(self.errors_from("check_readme"), [])

    def test_readme_rejects_missing_local_target(self) -> None:
        self.make_linked_readme()
        (self.root / "SECURITY.md").unlink()

        errors = self.errors_from("check_readme")

        self.assertTrue(
            any("does not resolve: SECURITY.md" in error for error in errors)
        )

    def test_foundation_exact_registry_requirement_is_allowed(self) -> None:
        self.write("requirements.txt", "agent-cow-postgresql==0.2.0\n")

        self.assertEqual(self.errors_from("check_foundation_dependencies"), [])

    def write_foundation_project(
        self,
        *,
        dependency: str | None = None,
        source: str | None = None,
        wheel_hash: str | None = None,
        sdist_hash: str | None = None,
        source_override: str = "",
    ) -> None:
        selected_dependency = dependency or (
            f"agent-cow-postgresql=={FOUNDATION_VERSION}"
        )
        selected_source = source or f'{{ registry = "{FOUNDATION_REGISTRY}" }}'
        selected_wheel_hash = wheel_hash or f"sha256:{FOUNDATION_WHEEL_SHA256}"
        selected_sdist_hash = sdist_hash or f"sha256:{FOUNDATION_SDIST_SHA256}"
        self.write(
            "pyproject.toml",
            "[project]\n"
            'name = "fixture"\n'
            'version = "0.0.0"\n'
            f'dependencies = ["{selected_dependency}"]\n'
            f"{source_override}",
        )
        self.write(
            "uv.lock",
            'version = 1\nrevision = 1\nrequires-python = ">=3.12,<3.15"\n\n'
            "[[package]]\n"
            'name = "agent-cow-postgresql"\n'
            f'version = "{FOUNDATION_VERSION}"\n'
            f"source = {selected_source}\n"
            "sdist = { "
            f'url = "https://files.pythonhosted.org/packages/{FOUNDATION_SDIST}", '
            f'hash = "{selected_sdist_hash}" }}\n'
            "wheels = [\n"
            "  { "
            f'url = "https://files.pythonhosted.org/packages/{FOUNDATION_WHEEL}", '
            f'hash = "{selected_wheel_hash}" }},\n'
            "]\n",
        )

    def test_foundation_exact_pyproject_and_lock_are_allowed(self) -> None:
        self.write_foundation_project()

        self.assertEqual(self.errors_from("check_foundation_dependencies"), [])

    def test_foundation_pyproject_rejects_version_and_source_override(self) -> None:
        self.write_foundation_project(
            dependency="agent-cow-postgresql>=0.2.0",
            source_override=(
                "\n[tool.uv.sources]\n"
                'agent-cow-postgresql = { git = "https://example.test/repository" }\n'
            ),
        )

        errors = self.errors_from("check_foundation_dependencies")

        self.assertTrue(
            any("exactly 'agent-cow-postgresql==0.2.0'" in error for error in errors)
        )
        self.assertTrue(
            any("source override is forbidden" in error for error in errors)
        )

    def test_foundation_lock_rejects_forbidden_source_forms(self) -> None:
        sources = (
            '{ git = "https://example.test/repository" }',
            '{ path = "../agent-cow-postgresql" }',
            '{ editable = "../agent-cow-postgresql" }',
            '{ url = "https://example.test/package.whl" }',
            '{ registry = "https://packages.example.test/simple" }',
        )
        for source in sources:
            with self.subTest(source=source):
                self.write_foundation_project(source=source)
                errors = self.errors_from("check_foundation_dependencies")
                self.assertTrue(
                    any(
                        "source must be the approved registry" in error
                        for error in errors
                    )
                )

    def test_foundation_lock_rejects_missing_or_wrong_artifact_hashes(self) -> None:
        for label, wheel_hash, sdist_hash, expected in (
            ("wheel", "sha256:" + "0" * 64, None, "wheel"),
            ("sdist", None, "sha256:" + "0" * 64, "sdist"),
        ):
            with self.subTest(label=label):
                self.write_foundation_project(
                    wheel_hash=wheel_hash,
                    sdist_hash=sdist_hash,
                )
                errors = self.errors_from("check_foundation_dependencies")
                self.assertTrue(
                    any(expected in error and "SHA-256" in error for error in errors)
                )

    def test_foundation_lock_rejects_missing_version_and_hashes(self) -> None:
        replacements = (
            (f'version = "{FOUNDATION_VERSION}"\n', "", "version"),
            (f', hash = "sha256:{FOUNDATION_WHEEL_SHA256}"', "", "wheel"),
            (f', hash = "sha256:{FOUNDATION_SDIST_SHA256}"', "", "sdist"),
        )
        for old, new, expected in replacements:
            with self.subTest(expected=expected):
                self.write_foundation_project()
                lock_path = self.root / "uv.lock"
                contents = lock_path.read_text(encoding="utf-8")
                self.assertIn(old, contents)
                lock_path.write_text(contents.replace(old, new), encoding="utf-8")
                errors = self.errors_from("check_foundation_dependencies")
                self.assertTrue(any(expected in error for error in errors))

    def test_foundation_forbidden_dependency_forms_are_rejected(self) -> None:
        forms = (
            "agent-cow-postgresql @ git+https://example.test/repository.git",
            "agent-cow-postgresql @ https://example.test/package.whl",
            "-e file:../agent-cow-postgresql",
            'agent-cow-postgresql = { path = "../agent-cow-postgresql" }',
            'agent-cow-postgresql = { git = "https://example.test/repository" }',
        )
        for index, form in enumerate(forms):
            self.write(f"requirements-{index}.txt", f"{form}\n")

        errors = self.errors_from("check_foundation_dependencies")

        self.assertEqual(
            sum("forbidden foundation" in error for error in errors), len(forms)
        )


if __name__ == "__main__":
    unittest.main()

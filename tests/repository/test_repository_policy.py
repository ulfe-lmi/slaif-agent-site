"""Isolated unit tests for the repository preparation policy."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.check_repository import APPROVED_ACTIONS, RepositoryPolicy


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

        self.assertTrue(any("000-a must have exactly one report" in error for error in errors))

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
                self.assertTrue(any("invalid trailing whitespace" in error for error in errors))
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
            "on:\n"
            "  pull_request_target:\n"
            "permissions:\n"
            "  contents: write\n",
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

        self.assertTrue(any("does not resolve: SECURITY.md" in error for error in errors))

    def test_foundation_exact_registry_requirement_is_allowed(self) -> None:
        self.write("requirements.txt", "agent-cow-postgresql==0.2.0\n")

        self.assertEqual(self.errors_from("check_foundation_dependencies"), [])

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

        self.assertEqual(sum("forbidden foundation" in error for error in errors), len(forms))


if __name__ == "__main__":
    unittest.main()

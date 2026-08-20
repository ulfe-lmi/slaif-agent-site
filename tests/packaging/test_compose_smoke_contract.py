"""Regression tests for the bounded Compose smoke project selector."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SMOKE = ROOT / "tools" / "compose" / "smoke.sh"


class ComposeSmokeContractTests(unittest.TestCase):
    def validate(self, project: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(SMOKE), project, "--validate-project"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_established_safe_project_families_are_accepted(self) -> None:
        for project in ("slaif007ci", "slaif009fixture", "slaif010rsmoke"):
            with self.subTest(project=project):
                result = self.validate(project)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_unsafe_project_names_are_rejected(self) -> None:
        for project in (
            "",
            "SLAIF007CI",
            "slaif007-ci",
            "slaif007_ci",
            "slaif007*",
            "slaif007;true",
            "slaif",
            "unrelated007ci",
        ):
            with self.subTest(project=project):
                result = self.validate(project)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "compose-smoke: unsafe project name\n")


if __name__ == "__main__":
    unittest.main()

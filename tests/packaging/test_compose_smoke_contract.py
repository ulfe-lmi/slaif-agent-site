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

    def test_render_recovery_is_bounded_ordered_and_stable(self) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        self.assertIn('while test "$attempt" -lt 40', source)
        self.assertIn("render-locator-recovery: failed service=", source)
        marker = (
            "render-locator-recovery: restored render=healthy "
            "web=healthy nginx=healthy"
        )
        self.assertEqual(source.count(marker), 1)
        render = source.index("wait_healthy render-api")
        web = source.index("wait_healthy web", render)
        nginx = source.index("wait_healthy nginx", web)
        global_wait = source.index('up --wait >/dev/null', nginx)
        self.assertLess(render, web)
        self.assertLess(web, nginx)
        self.assertLess(nginx, global_wait)
        self.assertGreaterEqual(source.count("--force-recreate --no-deps render-api"), 2)
        self.assertIn('test "$(render_fingerprint)" = "$render_before"', source)
        self.assertIn('test "$(site_fingerprint)" = "$sites_before"', source)


if __name__ == "__main__":
    unittest.main()

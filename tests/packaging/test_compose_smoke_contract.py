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
        for project in (
            "slaif007ci",
            "slaif009fixture",
            "slaif010rsmoke",
            "slaif071a",
        ):
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
            "render-locator-recovery: restored render=healthy web=healthy nginx=healthy"
        )
        self.assertEqual(source.count(marker), 1)
        render = source.index("wait_healthy render-api")
        web = source.index("wait_healthy web", render)
        nginx = source.index("wait_healthy nginx", web)
        global_wait = source.index("up --wait >/dev/null", nginx)
        self.assertLess(render, web)
        self.assertLess(web, nginx)
        self.assertLess(nginx, global_wait)
        self.assertGreaterEqual(
            source.count("--force-recreate --no-deps render-api"), 2
        )
        self.assertIn('test "$(render_fingerprint)" = "$render_before"', source)
        self.assertIn('test "$(site_fingerprint)" = "$sites_before"', source)

    def test_membership_fixtures_are_bounded_to_smoke_and_fail_on_collision(
        self,
    ) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        first = "12000000-0000-4000-8000-000000000001"
        second = "12000000-0000-4000-8000-000000000002"
        precondition, _insert = source.split(
            "INSERT INTO control.user_account", maxsplit=1
        )
        self.assertEqual(source.count("INSERT INTO control.user_account"), 2)
        self.assertIn("agent-browser-http: OK", source)
        self.assertIn("14000000-0000-4000-8000-000000000004", source)
        self.assertIn("unexpected fixture precondition", source)
        self.assertIn("OR EXISTS (SELECT 1 FROM control.user_account)", precondition)
        self.assertNotIn(
            "FROM control.user_account\n          WHERE id IN", precondition
        )
        self.assertIn("https://fixture.invalid", source)
        self.assertIn("identity_kind = 'OIDC'", source)
        self.assertIn("identity_kind = 'LOCAL'", source)
        self.assertIn("password_hash IS NULL", source)
        self.assertIn("password_hash IS NOT NULL", source)
        self.assertIn("SELECT count(*) = 3", source)
        self.assertIn(
            "(SELECT count(*) FROM control.platform_administrator) = 1", source
        )
        self.assertIn("SET ROLE slaif_owner", source)
        self.assertIn("membership_fingerprint", source)
        self.assertGreaterEqual(source.count(first), 4)
        self.assertGreaterEqual(source.count(second), 4)
        for path in (
            ROOT / "compose.yaml",
            ROOT / "services" / "backend" / "src",
            ROOT / "migrations",
        ):
            files = [path] if path.is_file() else list(path.rglob("*"))
            for candidate in files:
                if candidate.is_file():
                    text = candidate.read_text(encoding="utf-8", errors="ignore")
                    self.assertNotIn(first, text, str(candidate))
                    self.assertNotIn(second, text, str(candidate))

    def test_governance_project_orders_all_six_stable_devices(self) -> None:
        config = (ROOT / "playwright.config.ts").read_text(encoding="utf-8")
        self.assertEqual(config.count('name: "governance"'), 1)
        self.assertIn('dependencies: ["setup"]', config)
        self.assertEqual(config.count('dependencies: ["governance"]'), 6)
        for project in (
            "desktop-chromium",
            "desktop-firefox",
            "desktop-webkit",
            "tablet",
            "mobile-chromium",
            "mobile-webkit",
        ):
            self.assertIn(f'name: "{project}"', config)
        governance = (ROOT / "tests/e2e/governance.spec.ts").read_text(encoding="utf-8")
        for marker in (
            "site-create-visible",
            "domain-primary-replace-visible",
            "membership-add-visible",
            "stale-ui-conflict-recovery",
            "crafted-membership-negatives",
            "archive-dialog-keyboard-visible",
            "privacy-csp-edge",
        ):
            self.assertIn(marker, governance)
        smoke = SMOKE.read_text(encoding="utf-8")
        self.assertIn("governance-restart: OK", smoke)
        self.assertIn("domain_fingerprint", smoke)

    def test_browser_worker_proof_is_direct_private_and_does_not_dispatch(self) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        for marker in (
            "browser-worker-runtime-policy: OK",
            "browser-worker-image-policy: OK",
            "browser-worker-direct: OK runs=2 artifacts=6 negatives=5",
            "browser-worker-restart: OK retained-artifacts=3",
            "browser-worker-public-separation: OK durable-runs=2 queued=2",
            "browser-artifact-runtime-policy: OK files=12 artifacts=6",
            "browser-worker-cleanup: OK chromium-children=0",
            "browser-worker-secret-recovery: OK",
        ):
            self.assertEqual(source.count(marker), 1, marker)
        self.assertIn("load_browser_worker_credential", source)
        self.assertIn("load_browser_signing_key", source)
        self.assertIn("last_token.encode() not in content", source)
        self.assertIn(
            "PREVIEW_TOKEN_CONSUMED",
            (
                ROOT
                / "services/backend/src/slaif_agent_site/db/alembic/versions"
                / "036_001_render_browser_preview_authority.py"
            ).read_text(encoding="utf-8"),
        )
        self.assertNotIn("slaif_agent_browser_run_claim", source)
        self.assertNotIn("slaif_agent_browser_run_complete", source)
        self.assertNotIn("slaif_agent_browser_artifact_register", source)


if __name__ == "__main__":
    unittest.main()

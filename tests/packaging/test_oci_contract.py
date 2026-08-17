"""Static qualification of immutable OCI build inputs and runtime stages."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
DOCKERFILES = (
    ROOT / "apps/web/Dockerfile",
    ROOT / "infra/apache/Dockerfile",
    ROOT / "infra/nginx/Dockerfile",
    ROOT / "services/backend/Dockerfile",
    ROOT / "services/browser-worker/Dockerfile",
)
FROM = re.compile(r"^FROM\s+(\S+)", re.MULTILINE)
COPY_FROM = re.compile(r"^COPY\s+--from=(\S+)", re.MULTILINE)
STAGE = re.compile(r"^FROM\s+\S+\s+AS\s+(\S+)", re.MULTILINE | re.IGNORECASE)
DIGEST_PIN = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")


class OciContractTests(unittest.TestCase):
    def test_every_external_base_is_digest_pinned(self) -> None:
        for path in DOCKERFILES:
            with self.subTest(path=path.relative_to(ROOT)):
                images = FROM.findall(path.read_text(encoding="utf-8"))
                self.assertTrue(images)
                self.assertTrue(all(DIGEST_PIN.fullmatch(image) for image in images))

    def test_external_copy_sources_are_stages_or_digest_pinned(self) -> None:
        for path in DOCKERFILES:
            with self.subTest(path=path.relative_to(ROOT)):
                content = path.read_text(encoding="utf-8")
                stages = set(STAGE.findall(content))
                sources = COPY_FROM.findall(content)
                self.assertTrue(
                    all(
                        source in stages or DIGEST_PIN.fullmatch(source)
                        for source in sources
                    )
                )

    def test_backend_runtime_uses_only_frozen_production_environment(self) -> None:
        content = (ROOT / "services/backend/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("uv sync --frozen --no-default-groups --no-editable", content)
        runtime = content.split(" AS runtime", maxsplit=1)[1]
        self.assertIn("USER 10001:10001", runtime)
        self.assertNotIn("uv sync", runtime)
        self.assertNotIn("tests", runtime)

    def test_web_runtime_is_filtered_standalone_and_telemetry_free(self) -> None:
        content = (ROOT / "apps/web/Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "pnpm install --frozen-lockfile --filter @slaif-agent-site/web...",
            content,
        )
        runtime = content.split(" AS runtime", maxsplit=1)[1]
        self.assertIn("NEXT_TELEMETRY_DISABLED=1", runtime)
        self.assertIn("/build/apps/web/.next/standalone", runtime)
        self.assertIn("USER 10001:10001", runtime)
        self.assertNotIn("pnpm install", runtime)

        next_config = (ROOT / "apps/web/next.config.mjs").read_text(encoding="utf-8")
        self.assertIn("images: { unoptimized: true }", next_config)
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        self.assertIn("ignoredOptionalDependencies:\n  - sharp", workspace)
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertNotIn("\n  sharp@", lock)
        self.assertNotIn("\n  '@playwright/test@", lock)

    def test_browser_placeholder_has_no_package_or_browser_install(self) -> None:
        content = (ROOT / "services/browser-worker/Dockerfile").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("pnpm install", content)
        self.assertNotIn("npm install", content)
        self.assertNotIn("playwright install", content.casefold())
        self.assertIn("USER 10001:10001", content)


if __name__ == "__main__":
    unittest.main()

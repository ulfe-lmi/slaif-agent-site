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
    ROOT / "infra/postgres/Dockerfile",
    ROOT / "services/backend/Dockerfile",
    ROOT / "services/browser-worker/Dockerfile",
)
FROM = re.compile(r"^FROM\s+(\S+)", re.MULTILINE)
COPY_FROM = re.compile(r"^COPY\s+--from=(\S+)", re.MULTILINE)
STAGE = re.compile(r"^FROM\s+\S+\s+AS\s+(\S+)", re.MULTILINE | re.IGNORECASE)
DIGEST_PIN = re.compile(r"^[^@\s]+@sha256:[0-9a-f]{64}$")
OCI_LABELS = (
    "org.opencontainers.image.title",
    "org.opencontainers.image.description",
    "org.opencontainers.image.source",
    "org.opencontainers.image.licenses",
    "org.opencontainers.image.version",
    "org.opencontainers.image.revision",
    "org.opencontainers.image.created",
)


class OciContractTests(unittest.TestCase):
    def test_project_images_have_deterministic_metadata_and_oci_labels(self) -> None:
        for path in DOCKERFILES:
            with self.subTest(path=path.relative_to(ROOT)):
                content = path.read_text(encoding="utf-8")
                self.assertIn("ARG SOURCE_DATE_EPOCH=1704067200", content)
                self.assertIn("ARG SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z", content)
                self.assertIn("ARG SLAIF_IMAGE_REVISION=local", content)
                self.assertIn("ARG SLAIF_IMAGE_VERSION=0.0.0", content)
                for label in OCI_LABELS:
                    self.assertEqual(content.count(f"{label}="), 1, label)

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

    def test_postgres_overlay_is_exact_and_does_not_rebuild_postgres(self) -> None:
        content = (ROOT / "infra/postgres/Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "postgres:18.6-alpine3.23@sha256:"
            "697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f",
            content,
        )
        self.assertIn("libcrypto3=3.5.8-r0", content)
        self.assertIn("libssl3=3.5.8-r0", content)
        self.assertIn("https://dl-cdn.alpinelinux.org/alpine/v3.23/main", content)
        self.assertNotIn("apk upgrade", content)
        self.assertNotIn("postgresql-", content)

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
        self.assertIn(
            "generateBuildId: async () => deterministicBuildId()", next_config
        )
        self.assertIn('createHash("sha256")', next_config)
        self.assertIn("return [...new Set(paths)].sort()", next_config)
        self.assertNotIn("Math.random", next_config)
        self.assertNotIn("Date.now", next_config)
        self.assertIn("images: { unoptimized: true }", next_config)
        workspace = (ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8")
        self.assertIn("ignoredOptionalDependencies:\n  - sharp", workspace)
        lock = (ROOT / "pnpm-lock.yaml").read_text(encoding="utf-8")
        self.assertNotIn("\n  sharp@", lock)
        web_importer = lock.split("  apps/web:\n", maxsplit=1)[1].split(
            "\n  packages/", maxsplit=1
        )[0]
        self.assertNotIn("      '@playwright/test':", web_importer)

    def test_browser_runtime_is_exact_and_runtime_install_free(self) -> None:
        content = (ROOT / "services/browser-worker/Dockerfile").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "mcr.microsoft.com/playwright:v1.62.1-noble@sha256:"
            "dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e",
            content,
        )
        self.assertIn("pnpm install --frozen-lockfile", content)
        self.assertNotRegex(content, r"(?:^|\n)RUN npm install")
        self.assertNotIn("playwright install", content.casefold())
        runtime = content.split(" AS runtime", maxsplit=1)[1]
        self.assertNotIn("pnpm install", runtime)
        self.assertIn("rm -rf /ms-playwright/*", runtime)
        self.assertIn("BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=152.0.7977.64", runtime)
        self.assertIn(
            "8b592f066af71f054aab2cc80fc26f73c775c6d44ebb99d16ade924b24756c2e",
            content,
        )
        self.assertIn("USER 10001:10001", content)

    def test_unused_vulnerable_runtime_tools_are_removed(self) -> None:
        nginx = (ROOT / "infra/nginx/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("apk del curl", nginx)
        web = (ROOT / "apps/web/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("find /usr/local/lib/node_modules/npm -depth -delete", web)
        self.assertIn("rm /usr/local/bin/npm /usr/local/bin/npx", web)
        worker = (ROOT / "services/browser-worker/Dockerfile").read_text(
            encoding="utf-8"
        )
        self.assertIn("/usr/lib/node_modules/npm", worker)
        self.assertIn("rm -f /usr/bin/npm /usr/bin/npx /usr/bin/corepack", worker)


if __name__ == "__main__":
    unittest.main()

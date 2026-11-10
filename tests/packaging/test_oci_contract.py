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
        builder = content.split(" AS runtime", maxsplit=1)[0]
        self.assertIn("compileall -q -f /build/.venv/lib", builder)
        self.assertIn("'zlib=1.4-r0'", builder)
        self.assertIn("uv sync --frozen --no-default-groups --no-editable", content)
        self.assertIn(
            "python:3.12.16-alpine3.23@sha256:"
            "a4ad86fc2eaa4f9a5c3153776c9fb56e502dbd8e23dfa855d164308f376a6dd2",
            content,
        )
        self.assertEqual(content.count("python:3.12.16-alpine3.23@"), 2)
        self.assertNotIn("3.12.15", content)
        self.assertIn("pip-25.0.1.dist-info", content)
        self.assertIn("pip-25.0.1-py3-none-any.whl", content)
        runtime = content.split(" AS runtime", maxsplit=1)[1]
        self.assertIn("'zlib=1.4-r0'", runtime)
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
        self.assertIn("libcrypto3=3.5.9-r0", content)
        self.assertIn("libcurl=8.23.0-r0", content)
        self.assertIn("libssl3=3.5.9-r0", content)
        self.assertIn("musl-utils=1.2.5-r24", content)
        self.assertIn("musl=1.2.5-r24", content)
        self.assertIn("zlib=1.4-r0", content)
        self.assertIn(
            "test \"$(awk '/^P:musl-utils$/{found=1} found && "
            "/^V:/{print substr($0,3); exit}' /lib/apk/db/installed)"
            '" = "1.2.5-r24"',
            content,
        )
        self.assertIn(
            "test \"$(awk '/^P:musl$/{found=1} found && "
            "/^V:/{print substr($0,3); exit}' /lib/apk/db/installed)"
            '" = "1.2.5-r24"',
            content,
        )
        self.assertIn(
            "test \"$(awk '/^P:zlib$/{found=1} found && "
            "/^V:/{print substr($0,3); exit}' /lib/apk/db/installed)"
            '" = "1.4-r0"',
            content,
        )
        self.assertIn("https://dl-cdn.alpinelinux.org/alpine/v3.23/main", content)
        self.assertNotIn("apk upgrade", content)
        self.assertNotIn("postgresql-", content)

    def test_apache_qualification_is_exact_and_uses_fixed_ubuntu_packages(self) -> None:
        content = (ROOT / "infra/apache/Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "ubuntu:24.04@sha256:"
            "33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517",
            content,
        )
        for package in (
            "apache2=2.4.58-1ubuntu8.18",
            "apache2-bin=2.4.58-1ubuntu8.18",
            "apache2-data=2.4.58-1ubuntu8.18",
            "apache2-utils=2.4.58-1ubuntu8.18",
            "openssl=3.0.13-0ubuntu3.16",
        ):
            self.assertIn(f"'{package}'", content)
        self.assertNotIn("apt-get update", content)
        self.assertNotIn("apt-get install", content)
        update = content.index("apt-get -o Acquire::Retries=0 update")
        first = content.index("apt-get -o Acquire::Retries=0 install")
        self.assertLess(update, first)
        second = content.index("apt-get -o Acquire::Retries=0 install", first + 1)
        bootstrap = content[first:second]
        first_install = bootstrap.split("&&", 1)[0]
        self.assertIn("'apt=2.8.4ubuntu0.1'", first_install)
        self.assertIn("'libapt-pkg6.0t64=2.8.4ubuntu0.1'", first_install)
        self.assertIn(
            "test \"$(dpkg-query -W -f='${Version}' apt)\" = 2.8.4ubuntu0.1",
            bootstrap,
        )
        self.assertIn(
            "test \"$(dpkg-query -W -f='${Version}' libapt-pkg6.0t64)\" = "
            "2.8.4ubuntu0.1",
            bootstrap,
        )
        self.assertIn("apachectl -t", content)
        self.assertIn('CMD ["apachectl", "-D", "FOREGROUND"]', content)

    def test_web_runtime_is_filtered_standalone_and_telemetry_free(self) -> None:
        content = (ROOT / "apps/web/Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "pnpm install --frozen-lockfile --filter @slaif-agent-site/web...",
            content,
        )
        runtime = content.split(" AS runtime", maxsplit=1)[1]
        builder = content.split(" AS runtime", maxsplit=1)[0]
        self.assertIn("'zlib=1.4-r0'", builder)
        self.assertIn("'zlib=1.4-r0'", runtime)
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
        builder = content.split(" AS runtime", maxsplit=1)[0]
        runtime = content.split(" AS runtime", maxsplit=1)[1]
        self.assertNotIn("pnpm install", runtime)
        self.assertIn("rm -rf /ms-playwright ", runtime)
        self.assertIn("BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=157.0.8103.50", runtime)
        self.assertIn(
            "d17167bc092eb495a3b768c7467f27e35f625aa03834233a1663af67dcb668c9",
            content,
        )
        self.assertIn(
            "eb6728e77c576a35162c122c45ccadf224d89ff00abc8dae46cc2897c6002d7c",
            content,
        )
        self.assertIn("'libbrotli1=1.1.0-2ubuntu0.1'", content)
        self.assertIn("apt-get purge -y nodejs", content)
        self.assertEqual(
            content.count("apt-get purge -y nodejs -o Acquire::Retries=0"),
            2,
        )
        self.assertEqual(
            content.count("libpython3.12-minimal -o Acquire::Retries=0"),
            1,
        )
        self.assertEqual(content.count("apt-get -s purge -y"), 2)
        self.assertEqual(content.count('$1 == "Purg"'), 2)
        self.assertEqual(content.count("$1 ~ /^[A-Z][a-z][a-z][a-z]$/ { bad = 1 }"), 2)
        self.assertNotIn("$1 ~ /^[A-Z][A-Z][A-Z][A-Z]$/ { bad = 1 }", content)
        self.assertEqual(
            content.count(
                "cmp /tmp/python3-purge-actual.txt /tmp/python3-purge-expected.txt"
            ),
            2,
        )
        self.assertEqual(
            content.count(
                "apt-get purge -y \\\n"
                "      python3 python3-minimal libpython3-stdlib \\\n"
            ),
            2,
        )
        self.assertEqual(content.count(" = 3.12.3-0ubuntu2.1"), 6)
        self.assertEqual(content.count(" = 3.12.3-1ubuntu0.15"), 8)
        self.assertEqual(
            content.count(
                "dpkg-query -W -f='${Package} "
                "${db:Status-Status}\\n' > /tmp/python3-known.txt"
            ),
            2,
        )
        self.assertEqual(
            content.count(
                "find /usr /opt \\( -name 'python3*' -o "
                "-name 'libpython3*' \\) -print > /tmp/python3-leftover.txt"
            ),
            2,
        )
        self.assertEqual(
            content.count('test "$(wc -l < /tmp/python3-leftover.txt)" -eq 0'),
            2,
        )
        for stage_name, stage in (("builder", builder), ("runtime", runtime)):
            with self.subTest(stage=stage_name):
                self.assertNotIn("apt-get update", stage)
                self.assertNotIn("apt-get install", stage)
                update = stage.index("apt-get -o Acquire::Retries=0 update")
                first = stage.index("apt-get -o Acquire::Retries=0 install")
                self.assertLess(update, first)
                second = stage.index("apt-get -o Acquire::Retries=0 install", first + 1)
                bootstrap = stage[first:second]
                first_install = bootstrap.split("&&", 1)[0]
                self.assertIn("'apt=2.8.4ubuntu0.1'", first_install)
                self.assertIn("'libapt-pkg6.0t64=2.8.4ubuntu0.1'", first_install)
                self.assertIn(
                    "test \"$(dpkg-query -W -f='${Version}' apt)\" = 2.8.4ubuntu0.1",
                    bootstrap,
                )
                self.assertIn(
                    "test \"$(dpkg-query -W -f='${Version}' libapt-pkg6.0t64)\" = "
                    "2.8.4ubuntu0.1",
                    bootstrap,
                )
        self.assertNotIn("autoremove", content)
        self.assertEqual(content.count('test "$(node --version)" = v24.22.1'), 2)
        self.assertIn("USER 10001:10001", content)

    def test_unused_vulnerable_runtime_tools_removed_and_zlib_pinned(self) -> None:
        nginx = (ROOT / "infra/nginx/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("apk del curl", nginx)
        self.assertIn("'zlib=1.4-r0'", nginx)
        self.assertIn("'libexpat=2.10.0-r0'", nginx)
        self.assertIn(
            "test \"$(awk '/^P:libexpat$/{found=1} found && "
            "/^V:/{print substr($0,3); exit}' /lib/apk/db/installed)"
            '" = "2.10.0-r0"',
            nginx,
        )
        self.assertIn(
            "test \"$(awk '/^P:zlib$/{found=1} found && "
            "/^V:/{print substr($0,3); exit}' /lib/apk/db/installed)"
            '" = "1.4-r0"',
            nginx,
        )
        web = (ROOT / "apps/web/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("find /usr/local/lib/node_modules/npm -depth -delete", web)
        self.assertIn("rm /usr/local/bin/npm /usr/local/bin/npx", web)
        worker = (ROOT / "services/browser-worker/Dockerfile").read_text(
            encoding="utf-8"
        )
        self.assertIn("/usr/lib/node_modules/npm", worker)
        self.assertIn("rm -f /usr/bin/npm /usr/bin/npx /usr/bin/corepack", worker)
        self.assertIn("/usr/local/lib/node_modules/npm", worker)
        self.assertIn("/usr/local/lib/node_modules/corepack", worker)
        self.assertIn("/usr/lib/node_modules/corepack", worker)
        self.assertIn(
            "rm -f /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack",
            worker,
        )


if __name__ == "__main__":
    unittest.main()

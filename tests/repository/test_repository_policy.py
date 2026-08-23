"""Isolated unit tests for the repository preparation policy."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.check_repository import (
    AGENT_ARCHITECTURE_FILE,
    AGENT_FACING_ARCHITECTURE_REFERENCES,
    APPROVED_ACTIONS,
    BACKEND_PROCESS_VALUES,
    FOUNDATION_REGISTRY,
    FOUNDATION_SDIST,
    FOUNDATION_SDIST_SHA256,
    FOUNDATION_VERSION,
    FOUNDATION_WHEEL,
    FOUNDATION_WHEEL_SHA256,
    NODE_SCRIPTS,
    PACKAGE_MANAGER,
    PACKAGE_SCRIPTS,
    PYTHON_DEPENDENCY_GROUPS,
    PYTHON_DIRECT_VERSIONS,
    PYTHON_RUNTIME_DEPENDENCIES,
    REQUIRED_FILES,
    ROOT_NODE_DEV_DEPENDENCIES,
    SCAFFOLD_EXEMPT_PACKAGES,
    WORKSPACE_PACKAGES,
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

    def write_json(self, relative: str, document: object) -> Path:
        return self.write(relative, json.dumps(document, indent=2) + "\n")

    def write_node_workspace(self) -> None:
        self.write_json(
            "package.json",
            {
                "name": "slaif-agent-site",
                "version": "0.0.0",
                "private": True,
                "license": "Apache-2.0",
                "type": "module",
                "engines": {"node": ">=24 <25"},
                "packageManager": PACKAGE_MANAGER,
                "scripts": NODE_SCRIPTS,
                "devDependencies": ROOT_NODE_DEV_DEPENDENCIES,
            },
        )
        self.write(
            "pnpm-workspace.yaml",
            "packages:\n  - apps/*\n  - packages/*\n"
            "  - services/browser-worker\n\nallowBuilds:\n  esbuild: false\n\n"
            "autoInstallPeers: false\n\nignoredOptionalDependencies:\n"
            "  - sharp\n\noverrides:\n  esbuild: 0.28.1\n"
            "  uuid: 11.1.1\n  vite: 7.3.6\n",
        )
        self.write_json(
            "tsconfig.base.json",
            {
                "compilerOptions": {
                    "paths": {"@slaif-agent-site/*": ["./packages/*/src/index.ts"]},
                    "strict": True,
                    "noUncheckedIndexedAccess": True,
                    "exactOptionalPropertyTypes": True,
                    "verbatimModuleSyntax": True,
                    "declaration": True,
                    "declarationMap": True,
                    "sourceMap": True,
                }
            },
        )
        self.write_json(
            "apps/web/package.json",
            {
                "name": "@slaif-agent-site/web",
                "version": "0.0.0",
                "private": True,
                "license": "Apache-2.0",
                "scripts": {
                    "build": "NEXT_TELEMETRY_DISABLED=1 next build --webpack",
                    "lint": "eslint --config eslint.config.mjs . --max-warnings 0",
                    "typecheck": "tsc --noEmit",
                    "test": "node --test tests/*.test.mjs",
                },
                "dependencies": {
                    "@measured/puck": "0.20.2",
                    "@radix-ui/react-dialog": "1.1.23",
                    "next": "16.3.1",
                    "react": "19.2.8",
                    "react-dom": "19.2.8",
                },
                "devDependencies": {
                    "@types/node": "24.13.3",
                    "@types/react": "19.2.18",
                    "@types/react-dom": "19.2.4",
                    "autoprefixer": "10.5.4",
                    "postcss": "8.5.26",
                    "tailwindcss": "3.4.19",
                    "typescript": "6.0.3",
                },
            },
        )
        self.write_json(
            "services/browser-worker/package.json",
            {
                "name": "@slaif-agent-site/browser-worker",
                "version": "0.0.0",
                "private": True,
                "license": "Apache-2.0",
                "type": "module",
                "scripts": {
                    "build": "tsc --project tsconfig.json --noEmit",
                    "typecheck": "tsc --project tsconfig.json --noEmit",
                    "test": "node --test tests/*.test.mjs",
                },
            },
        )
        for slug, package_name in WORKSPACE_PACKAGES.items():
            self.write_json(
                f"packages/{slug}/package.json",
                {
                    "name": package_name,
                    "version": "0.0.0",
                    "private": True,
                    "description": "Unimplemented scaffold boundary.",
                    "license": "Apache-2.0",
                    "type": "module",
                    "files": ["dist"],
                    "exports": {
                        ".": {
                            "types": "./dist/index.d.ts",
                            "import": "./dist/index.js",
                        }
                    },
                    "types": "./dist/index.d.ts",
                    "scripts": PACKAGE_SCRIPTS,
                },
            )
            self.write(
                f"packages/{slug}/src/index.ts",
                "/** Unimplemented scaffold boundary identity only. */\n"
                "export const packageMetadata = Object.freeze({\n"
                f'  name: "{package_name}",\n'
                '  status: "pre-alpha-scaffold",\n'
                '  version: "0.0.0",\n'
                "} as const);\n",
            )
            tsconfig: dict[str, object] = {
                "extends": "../../tsconfig.base.json",
                "compilerOptions": {
                    "outDir": "dist",
                    "tsBuildInfoFile": "dist/.tsbuildinfo",
                },
                "include": ["src/**/*.ts", "tests/**/*.ts"],
            }
            if slug not in SCAFFOLD_EXEMPT_PACKAGES:
                tsconfig["compilerOptions"]["rootDir"] = "src"
                tsconfig["include"] = ["src/**/*.ts"]
            self.write_json(f"packages/{slug}/tsconfig.json", tsconfig)

        workspace_links = "\n".join(
            f"      '{package_name}':\n"
            "        specifier: workspace:0.0.0\n"
            f"        version: link:packages/{slug}"
            for slug, package_name in WORKSPACE_PACKAGES.items()
        )
        importers = (
            f"  .:\n    devDependencies:\n{workspace_links}\n\n"
            "  apps/web: {}\n\n"
            "  services/browser-worker: {}\n\n"
            + "\n".join(f"  packages/{slug}: {{}}" for slug in WORKSPACE_PACKAGES)
        )
        self.write(
            "pnpm-lock.yaml",
            "lockfileVersion: '9.0'\n\n"
            "importers:\n\n"
            f"{importers}\n\n"
            "packages:\n\n"
            "  example@1.0.0:\n"
            "    resolution: {integrity: sha512-YWJjZA==}\n\n"
            "snapshots:\n\n"
            "  example@1.0.0: {}\n",
        )

    def test_local_identity_setup_is_required_repository_surface(self) -> None:
        assert {
            "docs/INSTALLATION_SETUP.md",
            "docs/LOCAL_AUTHENTICATION.md",
            "docs/API.md",
            "services/backend/src/slaif_agent_site/bootstrap/setup_token.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/008_001_installation_state.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/009_001_local_identity.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/011_001_local_authentication.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/012_001_control_auth_http.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/014_001_human_rbac.py",
            "services/backend/src/slaif_agent_site/db/alembic/versions/015_001_admin_read_model.py",
            "services/backend/src/slaif_agent_site/sites/models.py",
            "services/backend/src/slaif_agent_site/sites/normalization.py",
            "services/backend/src/slaif_agent_site/sites/service.py",
            "services/backend/src/slaif_agent_site/human_authorization/catalog.py",
            "services/backend/src/slaif_agent_site/human_authorization/models.py",
            "services/backend/src/slaif_agent_site/human_authorization/service.py",
            "services/backend/src/slaif_agent_site/control_api/auth_http.py",
            "services/backend/src/slaif_agent_site/control_api/current_human_http.py",
            "services/backend/src/slaif_agent_site/control_api/membership_http.py",
            "services/backend/src/slaif_agent_site/control_api/route_policy.py",
            "services/backend/src/slaif_agent_site/control_api/site_http.py",
            "services/backend/tests/integration/test_membership_control_http.py",
            "services/backend/tests/unit/test_route_policy.py",
            "services/backend/tests/integration/test_site_control_http_integration.py",
            "services/backend/src/slaif_agent_site/identity/passwords.py",
            "services/backend/src/slaif_agent_site/identity/authentication.py",
            "services/backend/src/slaif_agent_site/identity/sessions.py",
            "services/backend/tests/integration/test_installation_setup.py",
            "services/backend/tests/integration/test_local_identity.py",
            "services/backend/tests/integration/test_local_authentication.py",
            "services/backend/tests/unit/test_bootstrap_setup_token.py",
            "services/backend/tests/unit/test_identity_password.py",
            "services/backend/tests/unit/test_sessions.py",
            "services/backend/tests/integration/test_human_session.py",
        } <= set(REQUIRED_FILES)

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

    def test_generated_next_directory_is_ignored(self) -> None:
        self.write("apps/web/.next/generated.js", "generated output  \t\n")

        self.assertEqual(self.errors_from("check_text_files"), [])

    def write_agent_architecture_policy_fixture(self) -> None:
        full = b"# Full human architecture\n"
        self.write("ARCHITECTURE.md", full)
        digest = hashlib.sha256(full).hexdigest()
        self.write(
            AGENT_ARCHITECTURE_FILE,
            "# Compact agent architecture\n\n"
            f"**Source SHA-256:** `{digest}`\n\n"
            "Only a direct human/user instruction authorizes loading full "
            "`ARCHITECTURE.md`.\n",
        )
        policy = (
            "Use `ARCHITECTURE-for-agents.md` by default. Only a direct "
            "human/user instruction authorizes loading full `ARCHITECTURE.md`.\n"
        )
        for relative in AGENT_FACING_ARCHITECTURE_REFERENCES:
            self.write(relative, policy)

    def test_agent_architecture_policy_accepts_compact_default(self) -> None:
        self.write_agent_architecture_policy_fixture()

        self.assertEqual(self.errors_from("check_agent_architecture_policy"), [])

    def test_agent_architecture_policy_rejects_source_drift(self) -> None:
        self.write_agent_architecture_policy_fixture()
        self.write("ARCHITECTURE.md", "# Changed full human architecture\n")

        errors = self.errors_from("check_agent_architecture_policy")

        self.assertTrue(any("source SHA-256" in error for error in errors))

    def test_agent_architecture_policy_rejects_legacy_full_default(self) -> None:
        self.write_agent_architecture_policy_fixture()
        self.write(
            "AGENTS.md",
            "Read root `ARCHITECTURE.md` and preserve every "
            "`ARCHITECTURE.md` invariant.\n",
        )

        errors = self.errors_from("check_agent_architecture_policy")

        self.assertTrue(any("by default" in error for error in errors))
        self.assertTrue(any("human/user" in error for error in errors))
        self.assertTrue(any("legacy full-architecture" in error for error in errors))

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
            "docs/CONFIGURATION.md",
            "docs/DATABASE_BOOTSTRAP.md",
            "docs/DATABASE_CONNECTIONS.md",
            "docs/DATABASE_ROLES.md",
            "docs/DEPLOYMENT.md",
            "docs/LICENSE_POLICY.md",
            "docs/OPERATIONS.md",
            "docs/SERVICE_AUTHORITY.md",
            "docs/SUPPLY_CHAIN.md",
            "LICENSE",
            "NOTICE",
            "SECURITY.md",
            "THIRD_PARTY_NOTICES.md",
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
                "docs/CONFIGURATION.md",
                "docs/DATABASE_BOOTSTRAP.md",
                "docs/DATABASE_CONNECTIONS.md",
                "docs/DATABASE_ROLES.md",
                "docs/DEPLOYMENT.md",
                "docs/LICENSE_POLICY.md",
                "docs/OPERATIONS.md",
                "docs/SERVICE_AUTHORITY.md",
                "docs/SUPPLY_CHAIN.md",
                "LICENSE",
                "NOTICE",
                "SECURITY.md",
                "THIRD_PARTY_NOTICES.md",
                "docs/assets/README.md",
                "oap/",
            )
        )
        self.write(
            "README.md",
            '<div style="text-align: center;">\n'
            '  <a href="https://www.slaif.si">\n'
            '    <img src="docs/assets/slaif-logo.svg" alt="SLAIF logo" '
            'width="400" height="400">\n'
            "  </a>\n"
            "</div>\n\n# Fixture\n"
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

    def test_readme_requires_centered_400_square_logo_before_h1(self) -> None:
        self.make_linked_readme()
        readme = self.root / "README.md"
        readme.write_text(
            "# Fixture\n" + readme.read_text(encoding="utf-8"), encoding="utf-8"
        )

        errors = self.errors_from("check_readme")

        self.assertTrue(any("precede the first H1" in error for error in errors))

    def test_markdown_configuration_requires_only_exact_immutable_exceptions(
        self,
    ) -> None:
        self.write(
            ".markdownlint-cli2.jsonc",
            'ignores:\n  - "oap/reports/**"\n',
        )

        errors = self.errors_from("check_markdown_configuration")

        self.assertTrue(
            any("missing exact immutable-report ignore" in error for error in errors)
        )
        self.assertTrue(
            any("must not broadly ignore OAP reports" in error for error in errors)
        )
        self.assertTrue(
            any("missing exact immutable-order ignore" in error for error in errors)
        )

        self.write(
            ".markdownlint-cli2.jsonc",
            "# Immutable strategic prose is retained byte-for-byte.\n"
            "ignores:\n"
            '  - "oap/reports/010-i-qualify-session-finalizer-update.md"\n'
            '  - "oap/orders/011-b-platform-admin-site-http.md"\n'
            '  - "oap/orders/**"\n',
        )
        errors = self.errors_from("check_markdown_configuration")
        self.assertTrue(
            any("must not broadly ignore OAP orders" in error for error in errors)
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

    def test_python_quality_accepts_complete_unexcluded_roots(self) -> None:
        self.write(
            "pyproject.toml",
            "[tool.ruff]\n"
            "line-length = 88\n"
            'target-version = "py312"\n'
            "\n[tool.ruff.lint]\n"
            'select = ["E", "F", "I"]\n',
        )

        self.assertEqual(self.errors_from("check_python_quality_configuration"), [])

    def test_python_quality_rejects_path_exclusion(self) -> None:
        self.write(
            "pyproject.toml",
            '[tool.ruff]\nextend-exclude = ["tests/repository/test_mermaid.py"]\n',
        )

        errors = self.errors_from("check_python_quality_configuration")

        self.assertTrue(any("extend-exclude" in error for error in errors))
        self.assertTrue(any("test_mermaid.py" in error for error in errors))

    def test_python_quality_rejects_force_exclude(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\nforce-exclude = true\n")

        errors = self.errors_from("check_python_quality_configuration")

        self.assertTrue(any("force-exclude" in error for error in errors))

    def test_python_quality_rejects_mermaid_per_file_ignore(self) -> None:
        self.write(
            "pyproject.toml",
            "[tool.ruff]\n"
            "\n[tool.ruff.lint.per-file-ignores]\n"
            '"tools/check_mermaid.py" = ["E501"]\n',
        )

        errors = self.errors_from("check_python_quality_configuration")

        self.assertTrue(any("tools/check_mermaid.py" in error for error in errors))

    def write_python_boundary(self) -> None:
        groups = "\n".join(
            f"{name} = {json.dumps(requirements)}"
            for name, requirements in PYTHON_DEPENDENCY_GROUPS.items()
        )
        self.write(
            "pyproject.toml",
            "[project]\n"
            'name = "fixture"\n'
            'version = "0.0.0"\n'
            f"dependencies = {json.dumps(PYTHON_RUNTIME_DEPENDENCIES)}\n\n"
            "[dependency-groups]\n"
            f"{groups}\n",
        )
        packages = []
        for name, version in PYTHON_DIRECT_VERSIONS.items():
            packages.append(
                "[[package]]\n"
                f'name = "{name}"\n'
                f'version = "{version}"\n'
                f'source = {{ registry = "{FOUNDATION_REGISTRY}" }}\n'
                'sdist = { url = "https://files.pythonhosted.org/example.tar.gz", '
                f'hash = "sha256:{"1" * 64}" }}\n'
                "wheels = [\n"
                '  { url = "https://files.pythonhosted.org/example.whl", '
                f'hash = "sha256:{"2" * 64}" }},\n'
                "]\n"
            )
        self.write(
            "uv.lock",
            'version = 1\nrevision = 1\nrequires-python = ">=3.12,<3.15"\n\n'
            + "\n".join(packages),
        )

    def test_python_dependency_boundary_accepts_exact_runtime_and_test_sets(
        self,
    ) -> None:
        self.write_python_boundary()

        self.assertEqual(self.errors_from("check_python_dependencies"), [])

    def test_python_dependency_boundary_rejects_extra_duplicate_and_bad_lock(
        self,
    ) -> None:
        self.write_python_boundary()
        project_path = self.root / "pyproject.toml"
        project = project_path.read_text(encoding="utf-8")
        project_path.write_text(
            project.replace(
                f"dependencies = {json.dumps(PYTHON_RUNTIME_DEPENDENCIES)}",
                "dependencies = "
                + json.dumps(PYTHON_RUNTIME_DEPENDENCIES + ["boto3==1.0.0"]),
            ).replace(
                'qualification = ["packaging>=24,<26"]',
                'qualification = ["packaging>=24,<26", "asyncpg==0.31.0"]',
            ),
            encoding="utf-8",
        )
        lock_path = self.root / "uv.lock"
        lock = lock_path.read_text(encoding="utf-8")
        lock_path.write_text(
            lock.replace(
                f'source = {{ registry = "{FOUNDATION_REGISTRY}" }}',
                'source = { git = "https://example.test/repository" }',
                1,
            ).replace(f"sha256:{'2' * 64}", "sha256:bad", 1),
            encoding="utf-8",
        )

        errors = self.errors_from("check_python_dependencies")

        self.assertTrue(any("runtime set" in error for error in errors))
        self.assertTrue(any("build/quality/test set" in error for error in errors))
        self.assertTrue(any("approved PyPI registry" in error for error in errors))
        self.assertTrue(any("wheel lacks a SHA-256" in error for error in errors))

    def write_backend_skeleton(self) -> None:
        assignments = "\n".join(
            f'    {value.upper().replace("-", "_")} = "{value}"'
            for value in sorted(BACKEND_PROCESS_VALUES)
        )
        self.write(
            "services/backend/src/slaif_agent_site/authority.py",
            f"from enum import StrEnum\n\nclass ProcessKind(StrEnum):\n{assignments}\n",
        )
        self.write(
            "services/backend/src/slaif_agent_site/application.py",
            'LIVE = "/health/live"\nREADY = "/health/ready"\n',
        )
        self.write(
            "services/backend/src/slaif_agent_site/config.py",
            'ENV_PREFIX = "SLAIF_"\n',
        )
        for package in ("bootstrap", "media_gc", "review_worker", "scheduler"):
            self.write(
                f"services/backend/src/slaif_agent_site/{package}/__main__.py",
                "from ..worker import run_worker_process\n",
            )

    def test_backend_static_boundary_accepts_exact_inventory_and_health_routes(
        self,
    ) -> None:
        self.write_backend_skeleton()

        self.assertEqual(self.errors_from("check_backend_skeleton"), [])

    def test_backend_static_boundary_rejects_process_route_db_and_listener_drift(
        self,
    ) -> None:
        self.write_backend_skeleton()
        authority = self.root / "services/backend/src/slaif_agent_site/authority.py"
        authority.write_text(
            authority.read_text(encoding="utf-8") + '    EXTRA = "extra"\n',
            encoding="utf-8",
        )
        self.write(
            "services/backend/src/slaif_agent_site/application.py",
            'LIVE = "/health/live"\nREADY = "/health/ready"\nAPI = "/api/v1/drift"\n',
        )
        self.write(
            "services/backend/src/slaif_agent_site/config.py",
            "database_url: str\n",
        )
        self.write(
            "services/backend/src/slaif_agent_site/scheduler/__main__.py",
            "import uvicorn\n",
        )

        errors = self.errors_from("check_backend_skeleton")

        self.assertTrue(any("approved ten processes" in error for error in errors))
        self.assertTrue(any("only live/ready routes" in error for error in errors))
        self.assertTrue(any("database connection" in error for error in errors))
        self.assertTrue(any("listener/database" in error for error in errors))

    def test_backend_static_boundary_rejects_identity_authority_in_other_process(
        self,
    ) -> None:
        self.write_backend_skeleton()
        self.write(
            "services/backend/src/slaif_agent_site/scheduler/consumer.py",
            "from slaif_agent_site.identity.passwords import PasswordService\n"
            "operation = 'create_initial_local_administrator'\n",
        )

        errors = self.errors_from("check_backend_skeleton")

        self.assertTrue(any("identity password authority" in error for error in errors))
        self.assertTrue(
            any("initial-administrator consumer" in error for error in errors)
        )

    def test_node_workspace_exact_scaffold_is_allowed(self) -> None:
        self.write_node_workspace()

        self.assertEqual(self.errors_from("check_node_workspace"), [])

    def test_node_workspace_rejects_tool_version_and_public_package(self) -> None:
        self.write_node_workspace()
        root_manifest_path = self.root / "package.json"
        root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
        root_manifest["devDependencies"]["typescript"] = "7.0.2"
        self.write_json("package.json", root_manifest)
        package_path = self.root / "packages/api-client/package.json"
        package_manifest = json.loads(package_path.read_text(encoding="utf-8"))
        package_manifest["private"] = False
        self.write_json("packages/api-client/package.json", package_manifest)

        errors = self.errors_from("check_node_workspace")

        self.assertTrue(any("approved private toolchain" in error for error in errors))
        self.assertTrue(
            any("identity/export/build contract" in error for error in errors)
        )

    def test_node_workspace_rejects_lifecycle_and_hosted_sdk(self) -> None:
        self.write_node_workspace()
        manifest_path = self.root / "package.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["scripts"]["postinstall"] = "node setup.js"
        manifest["devDependencies"]["@sentry/node"] = "10.0.0"
        self.write_json("package.json", manifest)

        errors = self.errors_from("check_node_workspace")

        self.assertTrue(
            any("lifecycle scripts are forbidden" in error for error in errors)
        )
        self.assertTrue(any("forbidden hosted SDK" in error for error in errors))

    def test_node_workspace_rejects_wrong_package_set(self) -> None:
        self.write_node_workspace()
        (self.root / "packages/test-fixtures/package.json").unlink()
        self.write_json(
            "packages/unapproved/package.json",
            {"name": "@slaif-agent-site/unapproved", "private": True},
        )

        errors = self.errors_from("check_node_workspace")

        self.assertTrue(any("workspace package set" in error for error in errors))

    def test_pnpm_lock_rejects_forbidden_sources_and_missing_integrity(self) -> None:
        sources = (
            ("git", "git+https://github.com/example/project.git"),
            ("github-tarball", "https://github.com/example/project/archive/main.tgz"),
            (
                "direct-url",
                "https://registry.npmjs.org/example/-/example-1.0.0.tgz",
            ),
            ("unapproved-registry", "https://packages.example.test/example.tgz"),
            ("file", "file:../example"),
            ("link", "link:../example"),
            ("path", "path:../example"),
            ("patch", "patch:example@1.0.0#fixture.patch"),
            ("workspace", "workspace:../example"),
        )
        for label, source in sources:
            with self.subTest(label=label):
                self.write_node_workspace()
                lock_path = self.root / "pnpm-lock.yaml"
                lock = lock_path.read_text(encoding="utf-8")
                lock_path.write_text(
                    lock.replace(
                        "resolution: {integrity: sha512-YWJjZA==}",
                        f"resolution: {{tarball: {source}, "
                        "integrity: sha512-YWJjZA==}",
                    ),
                    encoding="utf-8",
                )
                self.assertNotEqual(self.errors_from("check_pnpm_lock", lock_path), [])

        self.write_node_workspace()
        lock_path = self.root / "pnpm-lock.yaml"
        lock = lock_path.read_text(encoding="utf-8")
        lock_path.write_text(
            lock.replace(
                "resolution: {integrity: sha512-YWJjZA==}",
                "resolution: {}",
            ),
            encoding="utf-8",
        )
        errors = self.errors_from("check_pnpm_lock", lock_path)
        self.assertTrue(any("lacks sha512 integrity" in error for error in errors))

    def test_pnpm_lock_rejects_forbidden_ui_build_chain(self) -> None:
        for package in (
            "tailwindcss@4.3.3",
            "@tailwindcss/postcss@4.3.3",
            "lightningcss@1.32.0",
            "lightningcss-linux-x64-gnu@1.32.0",
        ):
            with self.subTest(package=package):
                self.write_node_workspace()
                lock_path = self.root / "pnpm-lock.yaml"
                lock_path.write_text(
                    lock_path.read_text(encoding="utf-8") + f"\n  {package}:\n"
                    "    resolution: {integrity: sha512-YWJjZA==}\n",
                    encoding="utf-8",
                )
                errors = self.errors_from("check_pnpm_lock", lock_path)
                self.assertTrue(any("forbidden UI build" in error for error in errors))

    def test_workflow_accepts_exact_pnpm_action_pin(self) -> None:
        setup_pnpm = APPROVED_ACTIONS["pnpm/action-setup"]
        self.write(
            ".github/workflows/node.yml",
            "jobs:\n"
            "  check:\n"
            "    steps:\n"
            f"      - uses: pnpm/action-setup@{setup_pnpm} # v6.0.10\n",
        )

        self.assertEqual(self.errors_from("check_workflows"), [])


if __name__ == "__main__":
    unittest.main()

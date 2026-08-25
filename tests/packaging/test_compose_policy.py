"""Unit tests for the exact Compose topology validator."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


def _load_verifier() -> ModuleType:
    path = Path(__file__).parents[2] / "tools/compose/verify.py"
    spec = importlib.util.spec_from_file_location("compose_verify", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_control_fixture() -> ModuleType:
    path = Path(__file__).parents[2] / "tools/compose/control_readiness.py"
    spec = importlib.util.spec_from_file_location("control_readiness_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = _load_verifier()
CONTROL_FIXTURE = _load_control_fixture()


def _configuration() -> dict[str, object]:
    services: dict[str, object] = {}
    for name in VERIFY.REQUIRED_SERVICES:
        networks = VERIFY.EXPECTED_NETWORKS.get(name, set())
        service: dict[str, object] = {
            "command": VERIFY.EXPECTED_COMMANDS.get(name),
            "cap_drop": ["ALL"],
            "environment": {},
            "healthcheck": (
                {"test": ["CMD", "true"]}
                if name not in {"bootstrap", "secrets-init"}
                else None
            ),
            "image": VERIFY.EXPECTED_IMAGES[name],
            "networks": {network: None for network in networks},
            "read_only": True,
            "restart": (
                "no" if name in {"bootstrap", "secrets-init"} else "unless-stopped"
            ),
            "security_opt": ["no-new-privileges:true"],
            "volumes": [
                {"source": source, "target": target, "read_only": read_only}
                for source, target, read_only in VERIFY.EXPECTED_MOUNTS[name]
            ],
        }
        if name != "secrets-init":
            service["tmpfs"] = ["/tmp:size=16m"]
        if name in VERIFY.LONG_RUNNING_BACKENDS:
            service["environment"] = {
                "SLAIF_MODE": "development",
                "SLAIF_PUBLIC_URL": "http://localhost:8080",
            }
        if name in {"control-api", "editor-api"}:
            service["environment"].update(
                {
                    "SLAIF_CONTROL_DSN_FILE": "/run/slaif-control/control-dsn",
                    "SLAIF_CONTROL_EXPECTED_DATABASE": "slaif",
                    "SLAIF_CONTROL_EXPECTED_LOGIN": "slaif_control_login",
                    "SLAIF_CONTROL_EXPECTED_PRIVILEGE_ROLE": "slaif_control",
                    "SLAIF_CONTROL_MODE": "development",
                }
            )
        if name == "editor-api":
            service["environment"].update(
                {
                    "SLAIF_EDITOR_DSN_FILE": "/run/slaif-editor/editor-dsn",
                    "SLAIF_EDITOR_EXPECTED_DATABASE": "slaif",
                    "SLAIF_EDITOR_EXPECTED_LOGIN": "slaif_editor_login",
                    "SLAIF_EDITOR_EXPECTED_PRIVILEGE_ROLE": "slaif_editor_runtime",
                    "SLAIF_EDITOR_MODE": "development",
                }
            )
        if name == "agent-api":
            service["environment"].update(
                {
                    "SLAIF_AGENT_DSN_FILE": "/run/slaif-agent/agent-dsn",
                    "SLAIF_AGENT_BROWSER_SIGNING_KEY_FILE": (
                        "/run/slaif-browser-signing/signing-key"
                    ),
                    "SLAIF_AGENT_EXPECTED_DATABASE": "slaif",
                    "SLAIF_AGENT_EXPECTED_LOGIN": "slaif_agent_login",
                    "SLAIF_AGENT_EXPECTED_PRIVILEGE_ROLE": "slaif_agent_runtime",
                    "SLAIF_AGENT_MODE": "development",
                }
            )
        if name == "render-api":
            service["environment"].update(
                {
                    "SLAIF_RENDER_DSN_FILE": "/run/slaif-render/render-dsn",
                    "SLAIF_RENDER_BROWSER_SIGNING_KEY_FILE": (
                        "/run/slaif-browser-signing/signing-key"
                    ),
                    "SLAIF_RENDER_PREVIEW_DSN_FILE": (
                        "/run/slaif-render-preview/preview-dsn"
                    ),
                    "SLAIF_RENDER_SERVICE_TOKEN_FILE": (
                        "/run/slaif-render-auth/render-token"
                    ),
                    "SLAIF_RENDER_EXPECTED_DATABASE": "slaif",
                    "SLAIF_RENDER_EXPECTED_LOGIN": "slaif_public_login",
                    "SLAIF_RENDER_EXPECTED_PRIVILEGE_ROLE": "slaif_public_reader",
                    "SLAIF_RENDER_PREVIEW_EXPECTED_LOGIN": "slaif_preview_login",
                    "SLAIF_RENDER_PREVIEW_EXPECTED_PRIVILEGE_ROLE": (
                        "slaif_preview_reader"
                    ),
                    "SLAIF_RENDER_MODE": "development",
                }
            )
        if name == "web":
            service["environment"] = {
                "SLAIF_RENDER_SERVICE_TOKEN_FILE": "/run/slaif-render-auth/render-token"
            }
        if name == "media-service":
            service["environment"].update(
                {
                    "SLAIF_MEDIA_DSN_FILE": "/run/slaif-media/media-dsn",
                    "SLAIF_MEDIA_EXPECTED_DATABASE": "slaif",
                    "SLAIF_MEDIA_EXPECTED_LOGIN": "slaif_media_login",
                    "SLAIF_MEDIA_EXPECTED_PRIVILEGE_ROLE": "slaif_media",
                    "SLAIF_MEDIA_MODE": "development",
                    "SLAIF_MEDIA_ROOT": "/var/lib/slaif/media",
                }
            )
        if name == "bootstrap":
            service["environment"]["SLAIF_BOOTSTRAP_DEMO_SEED"] = "true"
        if name in VERIFY.EXPECTED_CAP_ADD:
            service["cap_add"] = sorted(VERIFY.EXPECTED_CAP_ADD[name])
        if name in VERIFY.EXPECTED_GROUP_ADD:
            service["group_add"] = sorted(VERIFY.EXPECTED_GROUP_ADD[name])
        if name in VERIFY.EXPECTED_BUILD_FILES:
            service["build"] = {
                "args": VERIFY.EXPECTED_BUILD_ARGS.copy(),
                "dockerfile": VERIFY.EXPECTED_BUILD_FILES[name],
            }
        services[name] = service
    services["secrets-init"]["network_mode"] = "none"
    services["nginx"]["ports"] = [
        {"host_ip": "127.0.0.1", "published": "8080", "target": 8080}
    ]
    services["nginx"]["healthcheck"] = {
        "test": [
            "CMD-SHELL",
            "wget /health/ready && wget /api/control/health/ready",
        ]
    }
    return {
        "networks": {
            name: ({"internal": True} if name != "edge" else {})
            for name in ("application", "browser", "database", "edge")
        },
        "services": services,
        "volumes": {
            name: {}
            for name in (
                "agent-secret",
                "browser-signing-secret",
                "control-secret",
                "editor-secret",
                "local-secrets",
                "media-data",
                "media-secret",
                "postgres-data",
                "render-secret",
                "render-preview-secret",
                "render-auth-secret",
            )
        },
    }


class ComposePolicyTests(unittest.TestCase):
    @staticmethod
    def _database_readiness_document(reason: object) -> dict[str, object]:
        return {
            "status": "not_ready",
            "components": [
                {
                    "component": "database",
                    "status": "unavailable",
                    "reason": reason,
                }
            ],
        }

    def test_control_fixture_database_outage_predicate_is_exact(self) -> None:
        self.assertEqual(
            CONTROL_FIXTURE.DATABASE_OUTAGE_REASONS,
            frozenset({"connection_unavailable", "timeout"}),
        )
        for reason in ("connection_unavailable", "timeout"):
            with self.subTest(reason=reason):
                self.assertTrue(
                    CONTROL_FIXTURE.readiness_matches(
                        503,
                        self._database_readiness_document(reason),
                        CONTROL_FIXTURE.DATABASE_OUTAGE_REASONS,
                    )
                )
        for reason in ("probe_error", "shutdown", "unknown", None):
            with self.subTest(reason=reason):
                self.assertFalse(
                    CONTROL_FIXTURE.readiness_matches(
                        503,
                        self._database_readiness_document(reason),
                        CONTROL_FIXTURE.DATABASE_OUTAGE_REASONS,
                    )
                )
        self.assertFalse(
            CONTROL_FIXTURE.readiness_matches(
                200,
                self._database_readiness_document("timeout"),
                CONTROL_FIXTURE.DATABASE_OUTAGE_REASONS,
            )
        )
        self.assertFalse(
            CONTROL_FIXTURE.readiness_matches(
                503,
                {"status": "not_ready", "components": []},
                CONTROL_FIXTURE.DATABASE_OUTAGE_REASONS,
            )
        )
        self.assertFalse(
            CONTROL_FIXTURE.readiness_matches(
                503,
                ["malformed"],
                CONTROL_FIXTURE.DATABASE_OUTAGE_REASONS,
            )
        )
        self.assertFalse(
            CONTROL_FIXTURE.readiness_matches(
                503,
                self._database_readiness_document("timeout"),
                CONTROL_FIXTURE.CONNECTION_UNAVAILABLE,
            )
        )

    def test_control_fixture_diagnostics_are_allowlisted_and_secret_free(self) -> None:
        self.assertEqual(
            CONTROL_FIXTURE.failure_diagnostic(
                "wrong-login", "replace-file", "command-failed"
            ),
            "control-readiness-fixture: FAILED stage=wrong-login "
            "operation=replace-file reason=command-failed",
        )
        unsafe = "postgresql://fixed-login:never-print@example.test/slaif"
        self.assertEqual(
            CONTROL_FIXTURE.failure_diagnostic(unsafe, unsafe, unsafe),
            "control-readiness-fixture: FAILED stage=setup "
            "operation=initialize reason=state-mismatch",
        )
        self.assertNotIn(
            unsafe,
            CONTROL_FIXTURE.failure_diagnostic(unsafe, unsafe, unsafe),
        )
        self.assertEqual(
            CONTROL_FIXTURE.FixtureError(unsafe).reason,
            "state-mismatch",
        )
        self.assertEqual(
            CONTROL_FIXTURE.DIAGNOSTIC_REASONS,
            {
                "command-failed",
                "timeout",
                "malformed-response",
                "state-mismatch",
            },
        )
        source = (
            Path(__file__).parents[2] / "tools/compose/control_readiness.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("print(result.stdout", source)
        self.assertNotIn("print(result.stderr", source)

    def test_control_fixture_recreates_only_the_target_process(self) -> None:
        fixture = CONTROL_FIXTURE.ControlReadinessFixture(
            "slaif009fixture", existing=True
        )
        with patch.object(fixture, "compose") as compose:
            fixture._recreate_control()
        compose.assert_called_once_with(
            "up", "-d", "--force-recreate", "--no-deps", "control-api"
        )

    def test_control_fixture_mode_helper_is_exactly_confined(self) -> None:
        fixture = CONTROL_FIXTURE.ControlReadinessFixture(
            "slaif009fixture", existing=True
        )
        with patch.object(CONTROL_FIXTURE, "_run") as run:
            fixture._set_control_mode(0o000)
        run.assert_called_once_with(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--cap-add",
                "DAC_READ_SEARCH",
                "--cap-add",
                "FOWNER",
                "--user",
                "0:0",
                "--volume",
                "slaif009fixture_control-secret:/secrets",
                "--entrypoint",
                "python",
                CONTROL_FIXTURE.BACKEND_IMAGE,
                "-c",
                "import pathlib;pathlib.Path('/secrets/control-dsn').chmod(0o0)",
            ]
        )

    def test_exact_topology_is_accepted(self) -> None:
        VERIFY.validate_config(_configuration())

    def test_browser_database_path_is_rejected(self) -> None:
        configuration = copy.deepcopy(_configuration())
        configuration["services"]["browser-worker"]["networks"]["database"] = None
        with self.assertRaisesRegex(VERIFY.PolicyError, "network policy"):
            VERIFY.validate_config(configuration)

    def test_owner_secret_on_long_service_is_rejected(self) -> None:
        configuration = copy.deepcopy(_configuration())
        configuration["services"]["web"]["environment"] = {"OWNER_DSN": "fake"}
        with self.assertRaisesRegex(VERIFY.PolicyError, "secret environment"):
            VERIFY.validate_config(configuration)

    def test_control_secret_or_prefix_on_another_service_is_rejected(self) -> None:
        configuration = copy.deepcopy(_configuration())
        configuration["services"]["agent-api"]["environment"]["SLAIF_CONTROL_MODE"] = (
            "development"
        )
        with self.assertRaisesRegex(VERIFY.PolicyError, "foreign Control setting"):
            VERIFY.validate_config(configuration)

    def test_master_secret_mount_on_control_is_rejected(self) -> None:
        configuration = copy.deepcopy(_configuration())
        configuration["services"]["control-api"]["volumes"].append(
            {
                "source": "local-secrets",
                "target": "/run/slaif-secrets",
                "read_only": True,
            }
        )
        with self.assertRaisesRegex(VERIFY.PolicyError, "mount policy"):
            VERIFY.validate_config(configuration)

    def test_nginx_must_follow_control_database_readiness(self) -> None:
        configuration = copy.deepcopy(_configuration())
        configuration["services"]["nginx"]["healthcheck"] = {
            "test": ["CMD", "wget", "/health/ready"]
        }
        with self.assertRaisesRegex(VERIFY.PolicyError, "readiness dependency"):
            VERIFY.validate_config(configuration)

    def test_mutable_build_metadata_is_rejected(self) -> None:
        configuration = copy.deepcopy(_configuration())
        configuration["services"]["web"]["build"]["args"]["SOURCE_DATE_EPOCH"] = "now"
        with self.assertRaisesRegex(VERIFY.PolicyError, "build arguments"):
            VERIFY.validate_config(configuration)

    def test_test_or_false_production_backend_mode_is_rejected(self) -> None:
        for mode in ("test", "production"):
            with self.subTest(mode=mode):
                configuration = copy.deepcopy(_configuration())
                configuration["services"]["agent-api"]["environment"]["SLAIF_MODE"] = (
                    mode
                )
                with self.assertRaisesRegex(
                    VERIFY.PolicyError, "default mode must be development"
                ):
                    VERIFY.validate_config(configuration)


if __name__ == "__main__":
    unittest.main()

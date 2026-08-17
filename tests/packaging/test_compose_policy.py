"""Unit tests for the exact Compose topology validator."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from types import ModuleType


def _load_verifier() -> ModuleType:
    path = Path(__file__).parents[2] / "tools/compose/verify.py"
    spec = importlib.util.spec_from_file_location("compose_verify", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = _load_verifier()


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
        if name in VERIFY.EXPECTED_CAP_ADD:
            service["cap_add"] = sorted(VERIFY.EXPECTED_CAP_ADD[name])
        if name in VERIFY.EXPECTED_BUILD_FILES:
            service["build"] = {"dockerfile": VERIFY.EXPECTED_BUILD_FILES[name]}
        services[name] = service
    services["secrets-init"]["network_mode"] = "none"
    services["nginx"]["ports"] = [
        {"host_ip": "127.0.0.1", "published": "8080", "target": 8080}
    ]
    return {
        "networks": {
            name: ({"internal": True} if name != "edge" else {})
            for name in ("application", "browser", "database", "edge")
        },
        "services": services,
        "volumes": {
            name: {} for name in ("local-secrets", "media-data", "postgres-data")
        },
    }


class ComposePolicyTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

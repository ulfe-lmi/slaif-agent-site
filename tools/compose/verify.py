#!/usr/bin/env python3
"""Verify rendered Compose topology and, optionally, a running test project."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REQUIRED_SERVICES = {
    "agent-api",
    "bootstrap",
    "browser-worker",
    "control-api",
    "editor-api",
    "mcp-adapter",
    "media-gc",
    "media-service",
    "nginx",
    "postgres",
    "render-api",
    "review-worker",
    "scheduler",
    "secrets-init",
    "web",
}
EXPECTED_NETWORKS = {
    "agent-api": {"browser", "database", "edge"},
    "bootstrap": {"database"},
    "browser-worker": {"browser"},
    "control-api": {"database", "edge"},
    "editor-api": {"database", "edge"},
    "mcp-adapter": {"application", "edge"},
    "media-gc": {"database"},
    "media-service": {"database", "edge"},
    "nginx": {"edge"},
    "postgres": {"database"},
    "render-api": {"application", "database"},
    "review-worker": {"database"},
    "scheduler": {"database"},
    "web": {"application", "edge"},
}
EXPECTED_IMAGES = {
    **{
        name: "slaif-agent-site-backend:local"
        for name in (
            "agent-api",
            "bootstrap",
            "control-api",
            "editor-api",
            "mcp-adapter",
            "media-gc",
            "media-service",
            "render-api",
            "review-worker",
            "scheduler",
            "secrets-init",
        )
    },
    "browser-worker": "slaif-agent-site-browser-worker:local",
    "nginx": "slaif-agent-site-nginx:local",
    "postgres": (
        "postgres:18.6-alpine3.23@sha256:"
        "697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f"
    ),
    "web": "slaif-agent-site-web:local",
}
EXPECTED_COMMANDS = {
    "agent-api": ["python", "-m", "slaif_agent_site.agent_api"],
    "bootstrap": ["python", "-m", "slaif_agent_site.bootstrap", "compose"],
    "control-api": ["python", "-m", "slaif_agent_site.control_api"],
    "editor-api": ["python", "-m", "slaif_agent_site.editor_api"],
    "mcp-adapter": ["python", "-m", "slaif_agent_site.mcp_adapter"],
    "media-gc": ["python", "-m", "slaif_agent_site.media_gc"],
    "media-service": ["python", "-m", "slaif_agent_site.media_service"],
    "render-api": ["python", "-m", "slaif_agent_site.render_api"],
    "review-worker": ["python", "-m", "slaif_agent_site.review_worker"],
    "scheduler": ["python", "-m", "slaif_agent_site.scheduler"],
    "secrets-init": [
        "python",
        "/opt/slaif/bin/initialize-local-secrets.py",
        "--directory",
        "/run/slaif-secrets",
    ],
}
EXPECTED_BUILD_FILES = {
    "browser-worker": "services/browser-worker/Dockerfile",
    "nginx": "infra/nginx/Dockerfile",
    "secrets-init": "services/backend/Dockerfile",
    "web": "apps/web/Dockerfile",
}
EXPECTED_BUILD_ARGS = {
    "SOURCE_DATE_EPOCH": "1704067200",
    "SLAIF_IMAGE_CREATED": "2024-01-01T00:00:00Z",
    "SLAIF_IMAGE_REVISION": os.environ.get("GITHUB_SHA", "local"),
    "SLAIF_IMAGE_VERSION": os.environ.get("SLAIF_IMAGE_VERSION", "0.0.0"),
}
EXPECTED_MOUNTS = {
    **{name: set() for name in REQUIRED_SERVICES},
    "bootstrap": {("local-secrets", "/run/slaif-secrets", True)},
    "media-gc": {("media-data", "/var/lib/slaif/media", False)},
    "media-service": {("media-data", "/var/lib/slaif/media", False)},
    "postgres": {
        ("local-secrets", "/run/slaif-secrets", True),
        ("postgres-data", "/var/lib/postgresql/data", False),
    },
    "secrets-init": {("local-secrets", "/run/slaif-secrets", False)},
}
EXPECTED_CAP_ADD = {
    "postgres": {"CHOWN", "DAC_OVERRIDE", "FOWNER", "SETGID", "SETUID"},
    "secrets-init": {"CHOWN", "DAC_READ_SEARCH"},
}
EXPECTED_GROUP_ADD = {
    "bootstrap": {"10002"},
    "postgres": {"10002"},
}
SECRET_MOUNT_SERVICES = {"bootstrap", "postgres", "secrets-init"}
LONG_RUNNING_APPLICATIONS = REQUIRED_SERVICES - {
    "bootstrap",
    "postgres",
    "secrets-init",
}
LONG_RUNNING_BACKENDS = {
    name
    for name in LONG_RUNNING_APPLICATIONS
    if EXPECTED_IMAGES[name] == "slaif-agent-site-backend:local"
}


class PolicyError(RuntimeError):
    """Rendered deployment violates an exact packaging boundary."""


def _fail(condition: bool, message: str) -> None:
    if not condition:
        raise PolicyError(message)


def validate_config(config: dict[str, Any]) -> None:
    _fail(
        bool(
            re.fullmatch(
                r"(?:local|[0-9a-f]{40})", EXPECTED_BUILD_ARGS["SLAIF_IMAGE_REVISION"]
            )
        ),
        "build revision is malformed",
    )
    _fail(
        bool(
            re.fullmatch(
                r"[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}",
                EXPECTED_BUILD_ARGS["SLAIF_IMAGE_VERSION"],
            )
        ),
        "build version is malformed",
    )
    services = config.get("services", {})
    _fail(set(services) == REQUIRED_SERVICES, "service inventory mismatch")
    _fail(
        set(config.get("networks", {}))
        == {"application", "browser", "database", "edge"},
        "network inventory mismatch",
    )
    _fail(
        set(config.get("volumes", {}))
        == {"local-secrets", "media-data", "postgres-data"},
        "volume inventory mismatch",
    )
    networks = config["networks"]
    _fail(not networks["edge"].get("internal", False), "edge network is internal")
    for name in ("application", "browser", "database"):
        _fail(
            networks[name].get("internal") is True, f"{name}: network is not internal"
        )

    published: list[tuple[str, dict[str, Any]]] = []
    for name, service in services.items():
        for port in service.get("ports", []):
            published.append((name, port))
        _fail(service.get("read_only") is True, f"{name}: root filesystem is writable")
        _fail(
            service.get("cap_drop") == ["ALL"], f"{name}: capabilities are not dropped"
        )
        _fail(
            "no-new-privileges:true" in service.get("security_opt", []),
            f"{name}: no-new-privileges missing",
        )
        _fail(service.get("privileged", False) is False, f"{name}: privileged mode set")
        _fail(service.get("image") == EXPECTED_IMAGES[name], f"{name}: image mismatch")
        _fail(
            service.get("restart")
            == ("no" if name in {"bootstrap", "secrets-init"} else "unless-stopped"),
            f"{name}: restart policy mismatch",
        )
        expected_command = EXPECTED_COMMANDS.get(name)
        _fail(service.get("command") == expected_command, f"{name}: command mismatch")
        build = service.get("build")
        expected_build_file = EXPECTED_BUILD_FILES.get(name)
        _fail(
            (build.get("dockerfile") if isinstance(build, dict) else None)
            == expected_build_file,
            f"{name}: build source mismatch",
        )
        if expected_build_file is not None:
            _fail(
                build.get("args") == EXPECTED_BUILD_ARGS,
                f"{name}: deterministic build arguments mismatch",
            )
        if name not in {"secrets-init"}:
            _fail(bool(service.get("tmpfs")), f"{name}: bounded tmpfs missing")
        _fail(
            bool(service.get("healthcheck"))
            == (name not in {"bootstrap", "secrets-init"}),
            f"{name}: healthcheck policy mismatch",
        )
        _fail(
            set(service.get("cap_add", [])) == EXPECTED_CAP_ADD.get(name, set()),
            f"{name}: added capability policy mismatch",
        )
        _fail(
            set(service.get("group_add", [])) == EXPECTED_GROUP_ADD.get(name, set()),
            f"{name}: supplemental group policy mismatch",
        )
        mounts = service.get("volumes", [])
        actual_mounts = {
            (
                mount.get("source"),
                mount.get("target"),
                mount.get("read_only", False),
            )
            for mount in mounts
        }
        _fail(actual_mounts == EXPECTED_MOUNTS[name], f"{name}: mount policy mismatch")
        has_secrets = any(mount.get("source") == "local-secrets" for mount in mounts)
        _fail(
            has_secrets == (name in SECRET_MOUNT_SERVICES),
            f"{name}: secret mount policy mismatch",
        )
        environment = service.get("environment", {})
        if name in LONG_RUNNING_APPLICATIONS:
            serialized = json.dumps(environment).casefold()
            _fail(
                "password" not in serialized and "dsn" not in serialized,
                f"{name}: database secret environment present",
            )
        if name in LONG_RUNNING_BACKENDS:
            _fail(
                environment.get("SLAIF_MODE") == "development",
                f"{name}: default mode must be development",
            )
            _fail(
                environment.get("SLAIF_PUBLIC_URL") == "http://localhost:8080",
                f"{name}: default public URL mismatch",
            )
    _fail(len(published) == 1 and published[0][0] == "nginx", "only nginx may publish")
    port = published[0][1]
    _fail(
        port.get("host_ip") == "127.0.0.1"
        and str(port.get("published")) == "8080"
        and port.get("target") == 8080,
        "nginx port policy mismatch",
    )

    for name, networks in EXPECTED_NETWORKS.items():
        _fail(
            set(services[name].get("networks", {})) == networks,
            f"{name}: network policy mismatch",
        )
    _fail(
        services["secrets-init"].get("network_mode") == "none",
        "secret initializer must have no network",
    )
    for name, service in services.items():
        if name != "secrets-init":
            _fail(
                service.get("network_mode") in {None, ""},
                f"{name}: explicit network mode is forbidden",
            )
    _fail(
        "ports" not in services["browser-worker"],
        "browser worker is externally published",
    )


def rendered_config(root: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    _fail("postgresql://" not in result.stdout, "rendered configuration contains a DSN")
    return json.loads(result.stdout)


def validate_running(root: Path, project: str) -> None:
    result = subprocess.run(
        ["docker", "compose", "-p", project, "ps", "--format", "json"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    rows = [json.loads(line) for line in result.stdout.splitlines() if line]
    running = {row["Service"]: row for row in rows if row["State"] == "running"}
    expected = REQUIRED_SERVICES - {"bootstrap", "secrets-init"}
    _fail(set(running) == expected, "running service inventory mismatch")
    _fail(
        all(row.get("Health") == "healthy" for row in running.values()),
        "a service is not healthy",
    )

    identifiers = subprocess.run(
        ["docker", "compose", "-p", project, "ps", "--all", "-q"],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.split()
    _fail(len(identifiers) == len(REQUIRED_SERVICES), "container inventory mismatch")
    seen: set[str] = set()
    for identifier in identifiers:
        inspected = json.loads(
            subprocess.run(
                ["docker", "inspect", identifier],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout
        )[0]
        labels = inspected["Config"]["Labels"]
        name = labels["com.docker.compose.service"]
        seen.add(name)
        host = inspected["HostConfig"]
        _fail(
            host["ReadonlyRootfs"] is True, f"{name}: runtime root filesystem writable"
        )
        _fail(host["CapDrop"] == ["ALL"], f"{name}: runtime cap-drop mismatch")
        _fail(
            set(host.get("GroupAdd") or []) == EXPECTED_GROUP_ADD.get(name, set()),
            f"{name}: runtime supplemental group mismatch",
        )
        _fail(
            "no-new-privileges:true" in host["SecurityOpt"],
            f"{name}: runtime security option mismatch",
        )
        expected_user = "101:101" if name == "nginx" else "10001:10001"
        if name not in {"postgres", "secrets-init"}:
            _fail(
                inspected["Config"]["User"] == expected_user,
                f"{name}: runtime user mismatch",
            )
        if name in LONG_RUNNING_BACKENDS:
            environment = set(inspected["Config"].get("Env") or [])
            _fail(
                "SLAIF_MODE=development" in environment
                and "SLAIF_MODE=test" not in environment
                and "SLAIF_MODE=production" not in environment,
                f"{name}: runtime mode mismatch",
            )
        _fail(
            not any(mount["Type"] == "bind" for mount in inspected["Mounts"]),
            f"{name}: host bind mount present",
        )
        expected_runtime_networks = (
            {"none"}
            if name == "secrets-init"
            else {
                f"{project}_{network}" for network in EXPECTED_NETWORKS.get(name, set())
            }
        )
        _fail(
            set(inspected["NetworkSettings"]["Networks"]) == expected_runtime_networks,
            f"{name}: runtime network membership mismatch",
        )
        bindings = host.get("PortBindings") or {}
        _fail(
            bool(bindings) == (name == "nginx"), f"{name}: runtime port policy mismatch"
        )
        if name == "nginx":
            _fail(
                bindings == {"8080/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8080"}]},
                "nginx: runtime port binding mismatch",
            )
    _fail(seen == REQUIRED_SERVICES, "runtime service inventory mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--project")
    arguments = parser.parse_args()
    try:
        validate_config(rendered_config(arguments.root))
        if arguments.project:
            validate_running(arguments.root, arguments.project)
    except (
        KeyError,
        OSError,
        PolicyError,
        subprocess.SubprocessError,
        ValueError,
    ) as error:
        print(f"compose-policy: FAILED: {error}", file=sys.stderr)
        return 1
    print("compose-policy: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
        "--control-directory",
        "/run/slaif-control",
        "--agent-directory",
        "/run/slaif-agent",
        "--render-directory",
        "/run/slaif-render",
        "--preview-directory",
        "/run/slaif-render-preview",
        "--render-auth-directory",
        "/run/slaif-render-auth",
        "--browser-signing-directory",
        "/run/slaif-browser-signing",
        "--editor-directory",
        "/run/slaif-editor",
        "--media-directory",
        "/run/slaif-media",
        "--media-root",
        "/var/lib/slaif/media",
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
    "agent-api": {
        ("agent-secret", "/run/slaif-agent", True),
        ("browser-signing-secret", "/run/slaif-browser-signing", True),
    },
    "control-api": {("control-secret", "/run/slaif-control", True)},
    "editor-api": {
        ("control-secret", "/run/slaif-control", True),
        ("editor-secret", "/run/slaif-editor", True),
    },
    "render-api": {
        ("render-secret", "/run/slaif-render", True),
        ("render-preview-secret", "/run/slaif-render-preview", True),
        ("render-auth-secret", "/run/slaif-render-auth", True),
        ("browser-signing-secret", "/run/slaif-browser-signing", True),
    },
    "media-gc": {("media-data", "/var/lib/slaif/media", False)},
    "media-service": {
        ("media-data", "/var/lib/slaif/media", False),
        ("media-secret", "/run/slaif-media", True),
    },
    "postgres": {
        ("local-secrets", "/run/slaif-secrets", True),
        ("postgres-data", "/var/lib/postgresql/data", False),
    },
    "secrets-init": {
        ("agent-secret", "/run/slaif-agent", False),
        ("control-secret", "/run/slaif-control", False),
        ("local-secrets", "/run/slaif-secrets", False),
        ("render-secret", "/run/slaif-render", False),
        ("editor-secret", "/run/slaif-editor", False),
        ("media-secret", "/run/slaif-media", False),
        ("media-data", "/var/lib/slaif/media", False),
        ("render-preview-secret", "/run/slaif-render-preview", False),
        ("render-auth-secret", "/run/slaif-render-auth", False),
        ("browser-signing-secret", "/run/slaif-browser-signing", False),
    },
    "web": {("render-auth-secret", "/run/slaif-render-auth", True)},
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
CONTROL_SECRET_MOUNT_SERVICES = {"control-api", "editor-api", "secrets-init"}
EDITOR_SECRET_MOUNT_SERVICES = {"editor-api", "secrets-init"}
AGENT_SECRET_MOUNT_SERVICES = {"agent-api", "secrets-init"}
RENDER_SECRET_MOUNT_SERVICES = {"render-api", "secrets-init"}
RENDER_PREVIEW_SECRET_MOUNT_SERVICES = {"render-api", "secrets-init"}
RENDER_AUTH_SECRET_MOUNT_SERVICES = {"render-api", "secrets-init", "web"}
BROWSER_SIGNING_SECRET_MOUNT_SERVICES = {
    "agent-api",
    "render-api",
    "secrets-init",
}
MEDIA_SECRET_MOUNT_SERVICES = {"media-service", "secrets-init"}
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
        == {
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
        },
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
        has_control_secret = any(
            mount.get("source") == "control-secret" for mount in mounts
        )
        _fail(
            has_control_secret == (name in CONTROL_SECRET_MOUNT_SERVICES),
            f"{name}: Control secret mount policy mismatch",
        )
        has_editor_secret = any(
            mount.get("source") == "editor-secret" for mount in mounts
        )
        _fail(
            has_editor_secret == (name in EDITOR_SECRET_MOUNT_SERVICES),
            f"{name}: Editor secret mount policy mismatch",
        )
        has_agent_secret = any(
            mount.get("source") == "agent-secret" for mount in mounts
        )
        _fail(
            has_agent_secret == (name in AGENT_SECRET_MOUNT_SERVICES),
            f"{name}: Agent secret mount policy mismatch",
        )
        has_render_secret = any(
            mount.get("source") == "render-secret" for mount in mounts
        )
        _fail(
            has_render_secret == (name in RENDER_SECRET_MOUNT_SERVICES),
            f"{name}: Render secret mount policy mismatch",
        )
        has_render_preview_secret = any(
            mount.get("source") == "render-preview-secret" for mount in mounts
        )
        _fail(
            has_render_preview_secret == (name in RENDER_PREVIEW_SECRET_MOUNT_SERVICES),
            f"{name}: Render preview secret mount policy mismatch",
        )
        has_render_auth_secret = any(
            mount.get("source") == "render-auth-secret" for mount in mounts
        )
        _fail(
            has_render_auth_secret == (name in RENDER_AUTH_SECRET_MOUNT_SERVICES),
            f"{name}: Render auth secret mount policy mismatch",
        )
        has_browser_signing_secret = any(
            mount.get("source") == "browser-signing-secret" for mount in mounts
        )
        _fail(
            has_browser_signing_secret
            == (name in BROWSER_SIGNING_SECRET_MOUNT_SERVICES),
            f"{name}: browser signing secret mount policy mismatch",
        )
        has_media_secret = any(
            mount.get("source") == "media-secret" for mount in mounts
        )
        _fail(
            has_media_secret == (name in MEDIA_SECRET_MOUNT_SERVICES),
            f"{name}: Media secret mount policy mismatch",
        )
        environment = service.get("environment", {})
        if name in LONG_RUNNING_APPLICATIONS:
            safe_environment = {
                key: value
                for key, value in environment.items()
                if (
                    (
                        key == "SLAIF_CONTROL_DSN_FILE"
                        and name in {"control-api", "editor-api"}
                    )
                    or (key == "SLAIF_EDITOR_DSN_FILE" and name == "editor-api")
                    or (key == "SLAIF_AGENT_DSN_FILE" and name == "agent-api")
                    or (
                        key == "SLAIF_AGENT_BROWSER_SIGNING_KEY_FILE"
                        and name == "agent-api"
                    )
                    or (key == "SLAIF_RENDER_DSN_FILE" and name == "render-api")
                    or (key == "SLAIF_RENDER_PREVIEW_DSN_FILE" and name == "render-api")
                    or (
                        key == "SLAIF_RENDER_SERVICE_TOKEN_FILE"
                        and name in {"render-api", "web"}
                    )
                    or (
                        key == "SLAIF_RENDER_BROWSER_SIGNING_KEY_FILE"
                        and name == "render-api"
                    )
                    or (key == "SLAIF_MEDIA_DSN_FILE" and name == "media-service")
                )
            }
            serialized = json.dumps(
                {
                    key: value
                    for key, value in environment.items()
                    if key not in safe_environment
                }
            ).casefold()
            _fail(
                "password" not in serialized and "dsn" not in serialized,
                f"{name}: database secret environment present",
            )
            _fail(
                not any(
                    key.startswith("SLAIF_CONTROL_")
                    for key in environment
                    if name not in {"control-api", "editor-api"}
                ),
                f"{name}: foreign Control setting present",
            )
            _fail(
                not any(
                    key.startswith("SLAIF_AGENT_")
                    for key in environment
                    if name != "agent-api"
                ),
                f"{name}: foreign Agent setting present",
            )
            _fail(
                not any(
                    key.startswith("SLAIF_EDITOR_")
                    for key in environment
                    if name != "editor-api"
                ),
                f"{name}: foreign Editor setting present",
            )
            _fail(
                not any(
                    key.startswith("SLAIF_MEDIA_")
                    for key in environment
                    if name != "media-service"
                ),
                f"{name}: foreign Media setting present",
            )
        if name == "agent-api":
            _fail(
                {
                    key: environment.get(key)
                    for key in (
                        "SLAIF_AGENT_DSN_FILE",
                        "SLAIF_AGENT_BROWSER_SIGNING_KEY_FILE",
                        "SLAIF_AGENT_EXPECTED_DATABASE",
                        "SLAIF_AGENT_EXPECTED_LOGIN",
                        "SLAIF_AGENT_EXPECTED_PRIVILEGE_ROLE",
                        "SLAIF_AGENT_MODE",
                    )
                }
                == {
                    "SLAIF_AGENT_DSN_FILE": "/run/slaif-agent/agent-dsn",
                    "SLAIF_AGENT_BROWSER_SIGNING_KEY_FILE": (
                        "/run/slaif-browser-signing/signing-key"
                    ),
                    "SLAIF_AGENT_EXPECTED_DATABASE": "slaif",
                    "SLAIF_AGENT_EXPECTED_LOGIN": "slaif_agent_login",
                    "SLAIF_AGENT_EXPECTED_PRIVILEGE_ROLE": "slaif_agent_runtime",
                    "SLAIF_AGENT_MODE": "development",
                },
                "agent-api: database configuration mismatch",
            )
        if name == "media-service":
            _fail(
                {
                    key: environment.get(key)
                    for key in (
                        "SLAIF_MEDIA_DSN_FILE",
                        "SLAIF_MEDIA_EXPECTED_DATABASE",
                        "SLAIF_MEDIA_EXPECTED_LOGIN",
                        "SLAIF_MEDIA_EXPECTED_PRIVILEGE_ROLE",
                        "SLAIF_MEDIA_MODE",
                        "SLAIF_MEDIA_ROOT",
                    )
                }
                == {
                    "SLAIF_MEDIA_DSN_FILE": "/run/slaif-media/media-dsn",
                    "SLAIF_MEDIA_EXPECTED_DATABASE": "slaif",
                    "SLAIF_MEDIA_EXPECTED_LOGIN": "slaif_media_login",
                    "SLAIF_MEDIA_EXPECTED_PRIVILEGE_ROLE": "slaif_media",
                    "SLAIF_MEDIA_MODE": "development",
                    "SLAIF_MEDIA_ROOT": "/var/lib/slaif/media",
                },
                "media-service: database configuration mismatch",
            )
        if name in {"control-api", "editor-api"}:
            _fail(
                {
                    key: environment.get(key)
                    for key in (
                        "SLAIF_CONTROL_DSN_FILE",
                        "SLAIF_CONTROL_EXPECTED_DATABASE",
                        "SLAIF_CONTROL_EXPECTED_LOGIN",
                        "SLAIF_CONTROL_EXPECTED_PRIVILEGE_ROLE",
                        "SLAIF_CONTROL_MODE",
                    )
                }
                == {
                    "SLAIF_CONTROL_DSN_FILE": "/run/slaif-control/control-dsn",
                    "SLAIF_CONTROL_EXPECTED_DATABASE": "slaif",
                    "SLAIF_CONTROL_EXPECTED_LOGIN": "slaif_control_login",
                    "SLAIF_CONTROL_EXPECTED_PRIVILEGE_ROLE": "slaif_control",
                    "SLAIF_CONTROL_MODE": "development",
                },
                f"{name}: database configuration mismatch",
            )
        if name == "editor-api":
            _fail(
                {
                    key: environment.get(key)
                    for key in (
                        "SLAIF_EDITOR_DSN_FILE",
                        "SLAIF_EDITOR_EXPECTED_DATABASE",
                        "SLAIF_EDITOR_EXPECTED_LOGIN",
                        "SLAIF_EDITOR_EXPECTED_PRIVILEGE_ROLE",
                        "SLAIF_EDITOR_MODE",
                    )
                }
                == {
                    "SLAIF_EDITOR_DSN_FILE": "/run/slaif-editor/editor-dsn",
                    "SLAIF_EDITOR_EXPECTED_DATABASE": "slaif",
                    "SLAIF_EDITOR_EXPECTED_LOGIN": "slaif_editor_login",
                    "SLAIF_EDITOR_EXPECTED_PRIVILEGE_ROLE": "slaif_editor_runtime",
                    "SLAIF_EDITOR_MODE": "development",
                },
                "editor-api: database configuration mismatch",
            )
        if name == "render-api":
            _fail(
                {
                    key: environment.get(key)
                    for key in (
                        "SLAIF_RENDER_DSN_FILE",
                        "SLAIF_RENDER_BROWSER_SIGNING_KEY_FILE",
                        "SLAIF_RENDER_EXPECTED_DATABASE",
                        "SLAIF_RENDER_EXPECTED_LOGIN",
                        "SLAIF_RENDER_EXPECTED_PRIVILEGE_ROLE",
                        "SLAIF_RENDER_MODE",
                    )
                }
                == {
                    "SLAIF_RENDER_DSN_FILE": "/run/slaif-render/render-dsn",
                    "SLAIF_RENDER_BROWSER_SIGNING_KEY_FILE": (
                        "/run/slaif-browser-signing/signing-key"
                    ),
                    "SLAIF_RENDER_EXPECTED_DATABASE": "slaif",
                    "SLAIF_RENDER_EXPECTED_LOGIN": "slaif_public_login",
                    "SLAIF_RENDER_EXPECTED_PRIVILEGE_ROLE": "slaif_public_reader",
                    "SLAIF_RENDER_MODE": "development",
                },
                "render-api: database configuration mismatch",
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
        services["bootstrap"].get("environment", {}).get("SLAIF_BOOTSTRAP_DEMO_SEED")
        == "true",
        "bootstrap: explicit demo seed is not enabled",
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
    nginx_health = " ".join(services["nginx"]["healthcheck"]["test"])
    _fail(
        "/health/ready" in nginx_health and "/api/control/health/ready" in nginx_health,
        "nginx: Control database readiness dependency missing",
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

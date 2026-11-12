#!/usr/bin/env python3
"""Verify rendered Compose topology and, optionally, a running test project."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
import time
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
    "web": {"application", "browser", "edge"},
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
    "postgres": "slaif-agent-site-postgres:local",
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
        "--browser-worker-directory",
        "/run/slaif-browser-worker",
        "--editor-directory",
        "/run/slaif-editor",
        "--review-worker-directory",
        "/run/slaif-review-worker",
        "--media-directory",
        "/run/slaif-media",
        "--media-root",
        "/var/lib/slaif/media",
        "--browser-artifact-root",
        "/var/lib/slaif/browser-artifacts",
    ],
}
EXPECTED_BUILD_FILES = {
    "browser-worker": "services/browser-worker/Dockerfile",
    "nginx": "infra/nginx/Dockerfile",
    "postgres": "infra/postgres/Dockerfile",
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
        ("browser-worker-secret", "/run/slaif-browser-worker", True),
        ("media-data", "/var/lib/slaif/media", False),
    },
    "browser-worker": {
        ("browser-worker-secret", "/run/slaif-browser-worker", True),
        ("browser-artifacts", "/var/lib/slaif/browser-artifacts", False),
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
    "review-worker": {
        ("review-worker-secret", "/run/slaif-review-worker", True),
        ("media-secret", "/run/slaif-media", True),
        ("media-data", "/var/lib/slaif/media", False),
    },
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
        ("browser-worker-secret", "/run/slaif-browser-worker", False),
        ("browser-artifacts", "/var/lib/slaif/browser-artifacts", False),
        ("review-worker-secret", "/run/slaif-review-worker", False),
    },
    "web": {("render-auth-secret", "/run/slaif-render-auth", True)},
}
EXPECTED_CAP_ADD = {
    "browser-worker": {"SYS_CHROOT"},
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
BROWSER_WORKER_SECRET_MOUNT_SERVICES = {
    "agent-api",
    "browser-worker",
    "secrets-init",
}
BROWSER_ARTIFACT_MOUNT_SERVICES = {"browser-worker", "secrets-init"}
MEDIA_SECRET_MOUNT_SERVICES = {"media-service", "review-worker", "secrets-init"}
REVIEW_WORKER_SECRET_MOUNT_SERVICES = {
    "review-worker",
    "secrets-init",
}
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


RECEIPT_MAX_BYTES = 1024 * 1024
RECEIPT_NAME_MAX_CHARS = 200

# Fixed opt-in lifecycle operations. The CLI dispatches only these named
# verbs; there is no general command proxy or service surface.
LIFECYCLE_PHASES = frozenset(
    {
        "up",
        "recreate-old",
        "recreate-new",
        "recreate2-old",
        "recreate2-new",
        "pre-disposal",
        "negative",
    }
)
# Docker CLI --format is a Go text/template restricted to the CLI's fixed
# function map (json/split/join/replace/truncate...): it has NO dict
# function, so every projection below is a plain allowlisted field
# projection. Fields are separated by the ASCII unit-separator byte, which
# cannot appear in the fixed charset of the allowed metadata. Projections
# emit ONLY the allowed metadata (ID/name, immutable Image plus reference,
# Created, minimal State, Mounts name/source/destination/type/RW, scoped
# project labels); they never emit Config.Env, Args, Cmd, full
# inspect/config, secrets, DSNs, tokens or artifact bytes. A missing map
# lookup may render the template sentinel "<no value>"; for the optional
# fields (mount Name, volume Mountpoint/CreatedAt) the projection maps the
# sentinel and the empty string to None, while every required field rejects
# the sentinel; mount Source additionally accepts the empty string that the
# pinned v1.51 MountPoint schema renders for tmpfs mounts.
_LIFECYCLE_SEP = "\x1f"
CONTAINER_PROJECTION_TEMPLATE = (
    "{{.Id}}"
    + _LIFECYCLE_SEP
    + "{{.Name}}"
    + _LIFECYCLE_SEP
    + "{{.Image}}"
    + _LIFECYCLE_SEP
    + "{{.Config.Image}}"
    + _LIFECYCLE_SEP
    + "{{.Created}}"
    + _LIFECYCLE_SEP
    + "{{.State.Status}}"
    + _LIFECYCLE_SEP
    + "{{.State.Running}}"
    + _LIFECYCLE_SEP
    + "{{.State.ExitCode}}"
    + _LIFECYCLE_SEP
    + "{{.State.StartedAt}}"
    + _LIFECYCLE_SEP
    + "{{.State.FinishedAt}}"
)
CONTAINER_MOUNTS_TEMPLATE = (
    "{{range .Mounts}}{{.Name}}"
    + _LIFECYCLE_SEP
    + "{{.Source}}"
    + _LIFECYCLE_SEP
    + "{{.Destination}}"
    + _LIFECYCLE_SEP
    + "{{.Type}}"
    + _LIFECYCLE_SEP
    + "{{.RW}}\n{{end}}"
)
CONTAINER_PROJECT_LABEL_TEMPLATE = (
    '{{with .Config.Labels}}{{index . "com.docker.compose.project"}}{{end}}'
)
CONTAINER_SERVICE_LABEL_TEMPLATE = (
    '{{with .Config.Labels}}{{index . "com.docker.compose.service"}}{{end}}'
)
VOLUME_PROJECTION_TEMPLATE = (
    "{{.Name}}"
    + _LIFECYCLE_SEP
    + "{{.Driver}}"
    + _LIFECYCLE_SEP
    + "{{.Mountpoint}}"
    + _LIFECYCLE_SEP
    + "{{.CreatedAt}}"
)
NETWORK_PROJECTION_TEMPLATE = (
    "{{.Id}}" + _LIFECYCLE_SEP + "{{.Name}}" + _LIFECYCLE_SEP + "{{.Created}}"
)
TEMPLATE_NO_VALUE = "<no value>"
# The pinned engine's authoritative container State.Status vocabulary;
# any other rendered status is a non-pinned engine or broken capture.
LIFECYCLE_STATE_STATUSES = frozenset(
    {"created", "running", "paused", "restarting", "removing", "exited", "dead"}
)


def _lifecycle_bad(message: str) -> None:
    raise ValueError(message) from None


def _lifecycle_int(value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _lifecycle_bad("lifecycle integer is malformed")
    if value < low or value > high:
        _lifecycle_bad("lifecycle integer is malformed")
    return value


def _lifecycle_full_id(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        _lifecycle_bad("lifecycle id is malformed")
    return value


def _lifecycle_image_digest(value: Any) -> str:
    # The engine reports the creating image as a digest-prefixed ID
    # (sha256:<64hex>); container IDs stay bare 64-hex, so the two
    # identities are validated by different exact patterns.
    if not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        _lifecycle_bad("lifecycle image digest is malformed")
    return value


def _lifecycle_relpath(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*\.json", value)
        or len(value) > RECEIPT_NAME_MAX_CHARS
    ):
        _lifecycle_bad("lifecycle receipt name is malformed")
    return value


def _lifecycle_tag(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]{0,63}", value
    ):
        _lifecycle_bad("lifecycle tag is malformed")
    return value


def _lifecycle_single(value: Any, what: str) -> str:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], str):
        _lifecycle_bad(f"lifecycle {what} must be provided exactly once")
    return value[0]


def _lifecycle_project(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]{0,255}", value
    ):
        _lifecycle_bad("lifecycle project is malformed")
    return value


def _lifecycle_scope(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]{0,255}", value
    ):
        _lifecycle_bad("lifecycle scope is malformed")
    return value


def _lifecycle_run(argv: list[str], root: Path) -> tuple[int, str]:
    """Run one fixed docker query and return (native, stdout text).

    A nonzero child is a data point for the caller, never an exception:
    the caller decides whether the native means absence, failure or a
    genuine body. Spawn failure and non-UTF-8 output are stable errors.
    Stderr is discarded so no payload, path or engine text is retained.
    """
    try:
        result = subprocess.run(
            argv,
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        _lifecycle_bad("lifecycle query spawn failed")
    try:
        text = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        _lifecycle_bad("lifecycle query output is not valid utf8")
    return result.returncode, text


def _lifecycle_query_lines(native: int, text: str, context: str) -> list[str]:
    """Split a successful query into its nonempty output lines.

    A failed query is a stable error here: callers that must distinguish
    absence from failure invoke _lifecycle_run directly.
    """
    if native != 0:
        _lifecycle_bad(f"lifecycle {context} query failed")
    return [line for line in text.splitlines() if line]


def _lifecycle_optional_label(text: str) -> str | None:
    value = text.strip()
    if value in ("", TEMPLATE_NO_VALUE):
        return None
    if len(value) > 512 or not re.fullmatch(r"[A-Za-z0-9._:/-]+", value):
        _lifecycle_bad("lifecycle label is malformed")
    return value


def _lifecycle_required_scalar(value: Any, context: str) -> str:
    # A required projection field must carry real native data: the empty
    # string and the Go template sentinel are absence, never a value.
    if not isinstance(value, str) or value in ("", TEMPLATE_NO_VALUE):
        _lifecycle_bad(f"lifecycle {context} is malformed")
    return value


def _lifecycle_project_mounts(text: str) -> list[dict[str, Any]]:
    # The pinned docker CLI template inspector (docker/cli v28.0.0
    # cli/command/inspect/inspector.go) appends exactly one LF after
    # the rendered template: zero mounts render the footer LF alone;
    # every rendered row carries its own row LF plus that single
    # footer. The footer is framing, never a data line; a missing or
    # duplicated footer, or any blank data line, is malformed.
    if not text.endswith("\n"):
        _lifecycle_bad("lifecycle mount projection is malformed")
    body = text[:-1]
    if body == "":
        return []
    if not body.endswith("\n"):
        _lifecycle_bad("lifecycle mount projection is malformed")
    mounts: list[dict[str, Any]] = []
    for line in body[:-1].split("\n"):
        fields = line.split(_LIFECYCLE_SEP)
        if len(fields) != 5:
            _lifecycle_bad("lifecycle mount projection is malformed")
        name, source, destination, mount_type, read_write = fields
        # Destination/type carry real native data: the empty string and
        # the template sentinel are absence, never a value. Source may be
        # empty (legitimate tmpfs in the pinned v1.51 MountPoint schema),
        # but the sentinel is never a value. Only the mount Name stays
        # honestly optional (None).
        if not isinstance(source, str) or source == TEMPLATE_NO_VALUE:
            _lifecycle_bad("lifecycle mount source is malformed")
        destination = _lifecycle_required_scalar(destination, "mount destination")
        mount_type = _lifecycle_required_scalar(mount_type, "mount type")
        if read_write not in ("true", "false"):
            _lifecycle_bad("lifecycle mount rw is malformed")
        mounts.append(
            {
                "name": name if name not in ("", TEMPLATE_NO_VALUE) else None,
                "source": source,
                "destination": destination,
                "type": mount_type,
                "rw": read_write == "true",
            }
        )
    return mounts


def _lifecycle_project_state(fields: list[str]) -> dict[str, Any]:
    status, running, exit_code, started_at, finished_at = fields
    if status not in LIFECYCLE_STATE_STATUSES:
        _lifecycle_bad("lifecycle state status is malformed")
    if running not in ("true", "false"):
        _lifecycle_bad("lifecycle state running is malformed")
    if not re.fullmatch(r"[0-9]+", exit_code):
        _lifecycle_bad("lifecycle state exit code is malformed")
    started_at = _lifecycle_required_scalar(started_at, "state started at")
    finished_at = _lifecycle_required_scalar(finished_at, "state finished at")
    return {
        "status": status,
        "running": running == "true",
        "exit_code": int(exit_code),
        "started_at": started_at,
        "finished_at": finished_at,
    }


def _lifecycle_container_record(
    fields: list[str],
    mounts: list[dict[str, Any]],
    project: str | None,
    service: str | None,
    source_point: str,
) -> dict[str, Any]:
    """Project one fixed-template inspection to the flat meta schema.

    The scoped ownership (compose project/service labels) is caller-proven:
    scoped containers must carry exactly the caller's project and the
    expected service, helpers must carry neither. Labels are metadata, not
    a deletion authority.
    """
    if len(fields) != 10:
        _lifecycle_bad("lifecycle container projection is malformed")
    raw_id, name, image, image_ref, created = fields[:5]
    container_id = _lifecycle_full_id(raw_id)
    if (
        not isinstance(name, str)
        or not name.startswith("/")
        or len(name) < 2
        or len(name) > 201
        or "/" in name[1:]
    ):
        _lifecycle_bad("lifecycle container name is malformed")
    image_digest = _lifecycle_image_digest(image)
    image_ref = _lifecycle_required_scalar(image_ref, "container image reference")
    if len(image_ref) > 512:
        _lifecycle_bad("lifecycle container image reference is malformed")
    created = _lifecycle_required_scalar(created, "container created")
    return {
        "id": container_id,
        "name": name,
        "image": image_digest,
        "image_ref": image_ref,
        "created": created,
        "state": _lifecycle_project_state(fields[5:]),
        "mounts": mounts,
        "ownership": {"project": project, "service": service},
        "source_point": source_point,
    }


def _lifecycle_volume_record(text: str, source_point: str) -> dict[str, Any]:
    # Volume identity is the actual Name; there is no immutable volume Id.
    volume_name, driver, mountpoint, created = _lifecycle_project_scalar(
        text, "volume", 4
    )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,200}", volume_name):
        _lifecycle_bad("lifecycle volume name is malformed")
    driver = _lifecycle_required_scalar(driver, "volume driver")
    # CreatedAt is optional in the pinned engine response: absence (empty
    # or template sentinel) is honestly unknown, not a failure.
    created = created if created not in ("", TEMPLATE_NO_VALUE) else None
    return {
        "name": volume_name,
        "driver": driver,
        "mountpoint": mountpoint if mountpoint not in ("", TEMPLATE_NO_VALUE) else None,
        "created": created,
        "source_point": source_point,
    }


def _lifecycle_network_record(text: str, source_point: str) -> dict[str, Any]:
    # Network identity is the full native ID plus its Name.
    network_id, network_name, created = _lifecycle_project_scalar(text, "network", 3)
    network_id = _lifecycle_full_id(network_id)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,200}", network_name):
        _lifecycle_bad("lifecycle network name is malformed")
    created = _lifecycle_required_scalar(created, "network created")
    return {
        "id": network_id,
        "name": network_name,
        "created": created,
        "source_point": source_point,
    }


def _lifecycle_preflight_name(project: str) -> str:
    return _lifecycle_relpath(f"preflight-{project}.json")


def _lifecycle_capture_name(project: str, phase: str) -> str:
    return _lifecycle_relpath(f"capture-{project}-{phase}.json")


def _lifecycle_object_name(project: str, phase: str, kind: str, key: str) -> str:
    if kind not in {"c", "v", "n"}:
        _lifecycle_bad("lifecycle object kind is malformed")
    return _lifecycle_relpath(f"capture-{project}-{phase}-{kind}-{key}.json")


def _lifecycle_cleanup_name(project: str) -> str:
    return _lifecycle_relpath(f"cleanup-{project}.json")


def _lifecycle_helper_name(
    tag: str, point: str, container_id: str | None = None
) -> str:
    if point not in {
        "begin",
        "created",
        "created-failed",
        "meta",
        "start",
        "state",
        "removed",
        "absent",
        "complete",
    }:
        _lifecycle_bad("lifecycle helper point is malformed")
    _lifecycle_tag(tag)
    if container_id is not None:
        return _lifecycle_relpath(f"helper-{tag}-{point}-{container_id}.json")
    return _lifecycle_relpath(f"helper-{tag}-{point}.json")


def _lifecycle_expected_names(root: Path, project: str) -> dict[str, list[str]]:
    """Derive exact prospective physical names from the frozen rendered
    compose config. Names are label-independent: they are the physical
    objects compose would render for this project."""
    try:
        config = rendered_config(root)
    except (
        OSError,
        PolicyError,
        RecursionError,
        subprocess.SubprocessError,
        ValueError,
    ):
        _lifecycle_bad("lifecycle rendered config query failed")
    services = config.get("services")
    networks = config.get("networks")
    volumes = config.get("volumes")
    for label, values in (
        ("services", services),
        ("networks", networks),
        ("volumes", volumes),
    ):
        if not isinstance(values, dict) or not values:
            _lifecycle_bad(f"lifecycle rendered {label} are malformed")
        for key in values:
            if not isinstance(key, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", key
            ):
                _lifecycle_bad("lifecycle rendered name is malformed")
    return {
        "containers": [f"{project}-{service}-1" for service in sorted(services)],
        "volumes": [f"{project}_{name}" for name in sorted(volumes)],
        "networks": [f"{project}_{name}" for name in sorted(networks)],
    }


def _lifecycle_anchored_filter(kind: str, name: str) -> list[str]:
    # Anchored exact-name filter. Pinned moby matches the name filter against
    # both the container name and the slash-trimmed form, so the anchored
    # bare name is exact and label-independent; re.escape keeps the filter a
    # literal even for a hypothetical future metacharacter.
    if kind == "container":
        argv = ["docker", "ps", "-a", "--no-trunc"]
        fmt = "{{.ID}}"
    elif kind == "volume":
        argv = ["docker", "volume", "ls"]
        fmt = "{{.Name}}"
    else:
        argv = ["docker", "network", "ls"]
        fmt = "{{.ID}}"
    return [*argv, "--filter", f"name=^{re.escape(name)}$", "--format", fmt]


def _lifecycle_freshness_check(root: Path, kind: str, name: str) -> dict[str, Any]:
    # A failed query is not absence: only a healthy zero native with an
    # empty anchored result proves freshness for this exact physical name.
    native, text = _lifecycle_run(_lifecycle_anchored_filter(kind, name), root)
    if native != 0:
        _lifecycle_bad(f"lifecycle {kind} preflight query failed")
    return {
        "kind": kind,
        "name": name,
        "native": native,
        "listed": [line for line in text.splitlines() if line],
    }


def _lifecycle_preflight(
    root: Path, project: str, scope: str, evidence_dir: Path
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    daemon_native, _ = _lifecycle_run(
        ["docker", "version", "--format", "{{.Server.Version}}"], root
    )
    if daemon_native != 0:
        _lifecycle_bad("lifecycle daemon query failed")
    expected = _lifecycle_expected_names(root, project)
    checks: list[dict[str, Any]] = []
    for kind in ("containers", "volumes", "networks"):
        for name in expected[kind]:
            check = _lifecycle_freshness_check(root, kind[:-1], name)
            if check["listed"]:
                _lifecycle_bad(f"lifecycle {kind[:-1]} namespace is not fresh")
            checks.append(check)
    native, text = _lifecycle_run(
        [
            "docker",
            "ps",
            "-a",
            "--no-trunc",
            "--filter",
            f"label=com.docker.compose.project={project}",
            "--format",
            "{{.ID}}",
        ],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle label preflight query failed")
    label_listed = [line for line in text.splitlines() if line]
    if label_listed:
        _lifecycle_bad("lifecycle label namespace is not fresh")
    _write_evidence_record(
        evidence_dir,
        _lifecycle_preflight_name(project),
        {
            "project": project,
            "invocation": scope,
            "source_point": "preflight",
            "daemon_native": daemon_native,
            "checks": checks,
            "label_check": {"native": native, "listed": label_listed},
        },
    )


def _lifecycle_project_scalar(text: str, context: str, count: int) -> list[str]:
    # One successful projection query renders exactly one line of
    # separator-joined fields; anything else is a non-pinned engine or a
    # broken capture and must fail complete-evidence capture.
    lines = text.splitlines()
    if len(lines) != 1:
        _lifecycle_bad(f"lifecycle {context} projection is malformed")
    fields = lines[0].split(_LIFECYCLE_SEP)
    if len(fields) != count:
        _lifecycle_bad(f"lifecycle {context} projection is malformed")
    return fields


def _lifecycle_helper_labels(
    root: Path, container_id: str
) -> tuple[str | None, str | None]:
    native, project_text = _lifecycle_run(
        [
            "docker",
            "inspect",
            "--format",
            CONTAINER_PROJECT_LABEL_TEMPLATE,
            container_id,
        ],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper label query failed")
    project_label = _lifecycle_optional_label(project_text)
    native, service_text = _lifecycle_run(
        [
            "docker",
            "inspect",
            "--format",
            CONTAINER_SERVICE_LABEL_TEMPLATE,
            container_id,
        ],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper label query failed")
    service_label = _lifecycle_optional_label(service_text)
    return project_label, service_label


def _lifecycle_capture_container(
    root: Path,
    project: str,
    phase: str,
    name: str,
    required: bool,
) -> dict[str, Any] | None:
    expected_service = name[len(project) + 1 : -2]
    native, text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_PROJECTION_TEMPLATE, name], root
    )
    if native != 0:
        if required:
            _lifecycle_bad("lifecycle container capture query failed")
        return None
    native, mounts_text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_MOUNTS_TEMPLATE, name], root
    )
    if native != 0:
        _lifecycle_bad("lifecycle container mounts query failed")
    fields = _lifecycle_project_scalar(text, "container", 10)
    native, project_text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_PROJECT_LABEL_TEMPLATE, name], root
    )
    if native != 0:
        _lifecycle_bad("lifecycle container label query failed")
    native, service_text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_SERVICE_LABEL_TEMPLATE, name], root
    )
    if native != 0:
        _lifecycle_bad("lifecycle container label query failed")
    project_label = _lifecycle_optional_label(project_text)
    service_label = _lifecycle_optional_label(service_text)
    if project_label != project or service_label != expected_service:
        _lifecycle_bad("lifecycle container ownership is not caller-proven")
    record = _lifecycle_container_record(
        fields,
        _lifecycle_project_mounts(mounts_text),
        project,
        expected_service,
        "capture",
    )
    return _lifecycle_object_name(project, phase, "c", record["id"]), record


def _lifecycle_capture(
    root: Path, project: str, phase: str, scope: str, evidence_dir: Path
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    if phase not in LIFECYCLE_PHASES:
        _lifecycle_bad("lifecycle phase is malformed")
    daemon_native, _ = _lifecycle_run(
        ["docker", "version", "--format", "{{.Server.Version}}"], root
    )
    if daemon_native != 0:
        _lifecycle_bad("lifecycle daemon query failed")
    expected = _lifecycle_expected_names(root, project)
    objects: list[dict[str, Any]] = []
    for name in expected["containers"]:
        required = phase != "negative" or name == f"{project}-bootstrap-1"
        captured = _lifecycle_capture_container(root, project, phase, name, required)
        if captured is None:
            continue
        relpath, record = captured
        _write_evidence_record(evidence_dir, relpath, record)
        objects.append(
            {
                "kind": "container",
                "id": record["id"],
                "name": name,
                "service": record["ownership"]["service"],
                "receipt": relpath,
            }
        )
    for name in expected["volumes"]:
        native, text = _lifecycle_run(
            [
                "docker",
                "volume",
                "inspect",
                "--format",
                VOLUME_PROJECTION_TEMPLATE,
                name,
            ],
            root,
        )
        if native != 0:
            _lifecycle_bad("lifecycle volume capture query failed")
        record = _lifecycle_volume_record(text, "capture")
        if record["name"] != name:
            _lifecycle_bad("lifecycle volume identity mismatch")
        relpath = _lifecycle_object_name(project, phase, "v", name)
        _write_evidence_record(evidence_dir, relpath, record)
        objects.append({"kind": "volume", "name": name, "receipt": relpath})
    for name in expected["networks"]:
        native, text = _lifecycle_run(
            [
                "docker",
                "network",
                "inspect",
                "--format",
                NETWORK_PROJECTION_TEMPLATE,
                name,
            ],
            root,
        )
        if native != 0:
            _lifecycle_bad("lifecycle network capture query failed")
        record = _lifecycle_network_record(text, "capture")
        if record["name"] != name:
            _lifecycle_bad("lifecycle network identity mismatch")
        relpath = _lifecycle_object_name(project, phase, "n", record["id"])
        _write_evidence_record(evidence_dir, relpath, record)
        objects.append(
            {"kind": "network", "id": record["id"], "name": name, "receipt": relpath}
        )
    # The inventory is written only after every object receipt is durable, so
    # an inventory can never reference a missing or partial capture.
    _write_evidence_record(
        evidence_dir,
        _lifecycle_capture_name(project, phase),
        {
            "project": project,
            "invocation": scope,
            "phase": phase,
            "source_point": "capture",
            "daemon_native": daemon_native,
            "objects": objects,
        },
    )


def _lifecycle_helper_begin(
    root: Path, project: str, scope: str, tag: str, name: str, evidence_dir: Path
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    _lifecycle_tag(tag)
    if not isinstance(name, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]{0,200}", name
    ):
        _lifecycle_bad("lifecycle helper name is malformed")
    _write_evidence_record(
        evidence_dir,
        _lifecycle_helper_name(tag, "begin"),
        {
            "project": project,
            "tag": tag,
            "invocation": scope,
            "source_point": "helper-begin",
            "name": name,
        },
    )


def _lifecycle_helper_created(
    root: Path,
    project: str,
    scope: str,
    tag: str,
    name: str,
    container_id: str | None,
    create_rc: int,
    evidence_dir: Path,
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    _lifecycle_tag(tag)
    if not isinstance(name, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9-]{0,200}", name
    ):
        _lifecycle_bad("lifecycle helper name is malformed")
    if isinstance(create_rc, bool) or create_rc < 0 or create_rc > 255:
        _lifecycle_bad("lifecycle create native is malformed")
    if container_id is None:
        # Failed create: the native is recorded, its stdout is never adopted
        # as an owned ID, and no later lifecycle point may follow.
        if create_rc == 0:
            _lifecycle_bad("lifecycle create native is malformed")
        _write_evidence_record(
            evidence_dir,
            _lifecycle_helper_name(tag, "created-failed"),
            {
                "project": project,
                "tag": tag,
                "invocation": scope,
                "source_point": "helper-create",
                "name": name,
                "create_rc": create_rc,
            },
        )
        return
    if create_rc != 0:
        _lifecycle_bad("lifecycle create native is malformed")
    _lifecycle_full_id(container_id)
    _write_evidence_record(
        evidence_dir,
        _lifecycle_helper_name(tag, "created", container_id),
        {
            "project": project,
            "tag": tag,
            "invocation": scope,
            "source_point": "helper-create",
            "name": name,
            "create_rc": 0,
        },
    )
    # The full created ID is now durable; capture safe pre-start metadata
    # before any later fallible work.
    native, text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_PROJECTION_TEMPLATE, container_id],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper metadata query failed")
    native, mounts_text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_MOUNTS_TEMPLATE, container_id],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper metadata query failed")
    project_label, service_label = _lifecycle_helper_labels(root, container_id)
    if project_label is not None or service_label is not None:
        _lifecycle_bad("lifecycle helper carries compose labels")
    meta = _lifecycle_container_record(
        _lifecycle_project_scalar(text, "helper metadata", 10),
        _lifecycle_project_mounts(mounts_text),
        None,
        None,
        "helper-created",
    )
    if meta["name"] != f"/{name}":
        _lifecycle_bad("lifecycle helper name binding failed")
    _write_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "meta", container_id), meta
    )


def _lifecycle_helper_start(
    root: Path,
    project: str,
    scope: str,
    tag: str,
    container_id: str,
    start_rc: int,
    evidence_dir: Path,
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    _lifecycle_full_id(container_id)
    if isinstance(start_rc, bool) or start_rc < 0 or start_rc > 255:
        _lifecycle_bad("lifecycle start native is malformed")
    _write_evidence_record(
        evidence_dir,
        _lifecycle_helper_name(tag, "start", container_id),
        {
            "project": project,
            "tag": tag,
            "invocation": scope,
            "source_point": "helper-start",
            "start_rc": start_rc,
        },
    )


def _lifecycle_helper_terminal(
    root: Path,
    project: str,
    scope: str,
    tag: str,
    container_id: str,
    evidence_dir: Path,
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    _lifecycle_full_id(container_id)
    native, text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_PROJECTION_TEMPLATE, container_id],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper terminal query failed")
    native, mounts_text = _lifecycle_run(
        ["docker", "inspect", "--format", CONTAINER_MOUNTS_TEMPLATE, container_id],
        root,
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper terminal query failed")
    project_label, service_label = _lifecycle_helper_labels(root, container_id)
    if project_label is not None or service_label is not None:
        _lifecycle_bad("lifecycle helper carries compose labels")
    state = _lifecycle_container_record(
        _lifecycle_project_scalar(text, "helper terminal", 10),
        _lifecycle_project_mounts(mounts_text),
        None,
        None,
        "helper-terminal",
    )
    _write_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "state", container_id), state
    )


def _lifecycle_helper_remove(
    root: Path,
    project: str,
    scope: str,
    tag: str,
    container_id: str,
    evidence_dir: Path,
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    _lifecycle_full_id(container_id)
    native, _ = _lifecycle_run(["docker", "rm", container_id], root)
    _write_evidence_record(
        evidence_dir,
        _lifecycle_helper_name(tag, "removed", container_id),
        {
            "project": project,
            "tag": tag,
            "invocation": scope,
            "source_point": "helper-remove",
            "rm_rc": native,
        },
    )
    if native != 0:
        _lifecycle_bad("lifecycle helper removal failed")
    # Absence uses the full 64-hex ID as a literal-prefix filter: the
    # audited daemon resolves id= through an exact GetByPrefix lookup, so
    # a still-present container answers with its exact known ID while an
    # anchored ^...$ form would be vacuous. A failed query is not absence.
    native, text = _lifecycle_run(
        [
            "docker",
            "ps",
            "-a",
            "--no-trunc",
            "--filter",
            f"id={container_id}",
            "--format",
            "{{.ID}}",
        ],
        root,
    )
    if native != 0:
        # A failed absence query is not absence: the chain stays incomplete.
        _lifecycle_bad("lifecycle helper absence query failed")
    listed = [line for line in text.splitlines() if line]
    _write_evidence_record(
        evidence_dir,
        _lifecycle_helper_name(tag, "absent", container_id),
        {
            "project": project,
            "tag": tag,
            "invocation": scope,
            "source_point": "helper-absent",
            "ps_rc": native,
            "listed": listed,
        },
    )
    if listed:
        _lifecycle_bad("lifecycle helper is not absent")


def _lifecycle_validate_flat_meta(record: dict[str, Any], source_point: str) -> None:
    if set(record) != {
        "id",
        "name",
        "image",
        "image_ref",
        "created",
        "state",
        "mounts",
        "ownership",
        "source_point",
    }:
        _lifecycle_bad("lifecycle helper metadata is malformed")
    if record["source_point"] != source_point:
        _lifecycle_bad("lifecycle helper metadata point is malformed")
    _lifecycle_full_id(record["id"])
    name = record["name"]
    if (
        not isinstance(name, str)
        or not name.startswith("/")
        or len(name) < 2
        or len(name) > 201
        or "/" in name[1:]
    ):
        _lifecycle_bad("lifecycle helper metadata name is malformed")
    _lifecycle_image_digest(record["image"])
    image_ref = _lifecycle_required_scalar(
        record["image_ref"], "helper metadata image reference"
    )
    if len(image_ref) > 512:
        _lifecycle_bad("lifecycle helper metadata image reference is malformed")
    _lifecycle_required_scalar(record["created"], "helper metadata created")
    state = record["state"]
    if not isinstance(state, dict) or set(state) != {
        "status",
        "running",
        "exit_code",
        "started_at",
        "finished_at",
    }:
        _lifecycle_bad("lifecycle helper metadata state is malformed")
    if state["status"] not in LIFECYCLE_STATE_STATUSES:
        _lifecycle_bad("lifecycle helper metadata state is malformed")
    if not isinstance(state["running"], bool):
        _lifecycle_bad("lifecycle helper metadata state is malformed")
    if isinstance(state["exit_code"], bool) or not isinstance(state["exit_code"], int):
        _lifecycle_bad("lifecycle helper metadata state is malformed")
    if (
        not isinstance(state["started_at"], str)
        or not isinstance(state["finished_at"], str)
        or state["started_at"] in ("", TEMPLATE_NO_VALUE)
        or state["finished_at"] in ("", TEMPLATE_NO_VALUE)
    ):
        _lifecycle_bad("lifecycle helper metadata state is malformed")
    mounts = record["mounts"]
    if not isinstance(mounts, list):
        _lifecycle_bad("lifecycle helper metadata mounts are malformed")
    for mount in mounts:
        if not isinstance(mount, dict) or set(mount) != {
            "name",
            "source",
            "destination",
            "type",
            "rw",
        }:
            _lifecycle_bad("lifecycle helper metadata mount is malformed")
        if mount["name"] is not None and not isinstance(mount["name"], str):
            _lifecycle_bad("lifecycle helper metadata mount is malformed")
        if not isinstance(mount["source"], str) or mount["source"] == TEMPLATE_NO_VALUE:
            _lifecycle_bad("lifecycle helper metadata mount is malformed")
        if not isinstance(mount["destination"], str) or mount["destination"] in (
            "",
            TEMPLATE_NO_VALUE,
        ):
            _lifecycle_bad("lifecycle helper metadata mount is malformed")
        if not isinstance(mount["type"], str) or mount["type"] in (
            "",
            TEMPLATE_NO_VALUE,
        ):
            _lifecycle_bad("lifecycle helper metadata mount is malformed")
        if not isinstance(mount["rw"], bool):
            _lifecycle_bad("lifecycle helper metadata mount is malformed")
    ownership = record["ownership"]
    if not isinstance(ownership, dict) or set(ownership) != {"project", "service"}:
        _lifecycle_bad("lifecycle helper metadata ownership is malformed")
    for key in ("project", "service"):
        value = ownership[key]
        if value is not None and not isinstance(value, str):
            _lifecycle_bad("lifecycle helper metadata ownership is malformed")


def _lifecycle_validate_common(
    record: dict[str, Any],
    expected: set[str],
    source_point: str,
    project: str,
    tag: str,
    scope: str,
) -> None:
    if set(record) != expected:
        _lifecycle_bad("lifecycle helper record is malformed")
    if record["source_point"] != source_point:
        _lifecycle_bad("lifecycle helper record point is malformed")
    if record["project"] != project:
        _lifecycle_bad("lifecycle helper binding is broken")
    if record["tag"] != tag:
        _lifecycle_bad("lifecycle helper binding is broken")
    if record["invocation"] != scope:
        _lifecycle_bad("lifecycle helper binding is broken")


def _lifecycle_audit_helper_chain(
    begin: dict[str, Any],
    created: dict[str, Any],
    meta: dict[str, Any],
    start: dict[str, Any],
    state: dict[str, Any],
    removed: dict[str, Any],
    absent: dict[str, Any],
    project: str,
    tag: str,
    scope: str,
    name: str,
    container_id: str,
    start_rc: int,
    body_exit: int,
) -> None:
    """Pure chain audit. Validating the complete receipts happens before any
    caller may accept the body result as a denial or a value match."""
    _lifecycle_validate_common(
        begin,
        {"project", "tag", "invocation", "source_point", "name"},
        "helper-begin",
        project,
        tag,
        scope,
    )
    if begin["name"] != name:
        _lifecycle_bad("lifecycle helper name binding failed")
    _lifecycle_validate_common(
        created,
        {"project", "tag", "invocation", "source_point", "name", "create_rc"},
        "helper-create",
        project,
        tag,
        scope,
    )
    if created["name"] != name:
        _lifecycle_bad("lifecycle helper name binding failed")
    if created["create_rc"] != 0:
        _lifecycle_bad("lifecycle helper create did not succeed")
    _lifecycle_validate_flat_meta(meta, "helper-created")
    if meta["id"] != container_id:
        _lifecycle_bad("lifecycle helper id binding failed")
    if meta["name"] != f"/{name}":
        _lifecycle_bad("lifecycle helper name binding failed")
    if meta["ownership"] != {"project": None, "service": None}:
        _lifecycle_bad("lifecycle helper ownership is not unknown")
    _lifecycle_validate_common(
        start,
        {"project", "tag", "invocation", "source_point", "start_rc"},
        "helper-start",
        project,
        tag,
        scope,
    )
    if start["start_rc"] != start_rc:
        _lifecycle_bad("lifecycle helper start native mismatch")
    _lifecycle_validate_flat_meta(state, "helper-terminal")
    if state["id"] != container_id:
        _lifecycle_bad("lifecycle helper id binding failed")
    if state["name"] != meta["name"]:
        _lifecycle_bad("lifecycle helper name binding failed")
    if state["image"] != meta["image"]:
        _lifecycle_bad("lifecycle helper image binding failed")
    _lifecycle_validate_common(
        removed,
        {"project", "tag", "invocation", "source_point", "rm_rc"},
        "helper-remove",
        project,
        tag,
        scope,
    )
    if removed["rm_rc"] != 0:
        _lifecycle_bad("lifecycle helper removal did not succeed")
    _lifecycle_validate_common(
        absent,
        {"project", "tag", "invocation", "source_point", "ps_rc", "listed"},
        "helper-absent",
        project,
        tag,
        scope,
    )
    if absent["ps_rc"] != 0:
        _lifecycle_bad("lifecycle helper absence query did not succeed")
    if not isinstance(absent["listed"], list) or absent["listed"] != []:
        _lifecycle_bad("lifecycle helper is not absent")
    # The body result is genuine only when the authoritative terminal state
    # proves the container executed and terminated: a docker-level start
    # failure (for example a 125 native while the container is still
    # created) is infrastructure, while any 0..255 exit of an executed
    # container - including 97 and 125/126/127 - is the body's own result.
    terminal = state["state"]
    if terminal["status"] != "exited":
        _lifecycle_bad("lifecycle body did not reach terminal execution")
    if terminal["exit_code"] != start_rc:
        _lifecycle_bad("lifecycle body native mismatch")
    if start_rc != body_exit:
        _lifecycle_bad("lifecycle body native mismatch")


def _lifecycle_helper_complete(
    root: Path,
    project: str,
    scope: str,
    tag: str,
    name: str,
    container_id: str,
    start_rc: int,
    body_exit: int,
    evidence_dir: Path,
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    _lifecycle_tag(tag)
    _lifecycle_full_id(container_id)
    if isinstance(start_rc, bool) or start_rc < 0 or start_rc > 255:
        _lifecycle_bad("lifecycle start native is malformed")
    if isinstance(body_exit, bool) or body_exit < 0 or body_exit > 255:
        _lifecycle_bad("lifecycle body exit is malformed")
    begin = _read_evidence_record(evidence_dir, _lifecycle_helper_name(tag, "begin"))
    created = _read_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "created", container_id)
    )
    meta = _read_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "meta", container_id)
    )
    start = _read_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "start", container_id)
    )
    state = _read_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "state", container_id)
    )
    removed = _read_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "removed", container_id)
    )
    absent = _read_evidence_record(
        evidence_dir, _lifecycle_helper_name(tag, "absent", container_id)
    )
    _lifecycle_audit_helper_chain(
        begin,
        created,
        meta,
        start,
        state,
        removed,
        absent,
        project,
        tag,
        scope,
        name,
        container_id,
        start_rc,
        body_exit,
    )
    _write_evidence_record(
        evidence_dir,
        _lifecycle_helper_name(tag, "complete"),
        {
            "project": project,
            "tag": tag,
            "invocation": scope,
            "source_point": "helper-complete",
            "id": container_id,
            "name": name,
            "start_rc": start_rc,
            "body_exit": body_exit,
            "rm_rc": removed["rm_rc"],
            "ps_rc": absent["ps_rc"],
        },
    )


def _lifecycle_cleanup_absent(
    root: Path, project: str, scope: str, down_native: int, evidence_dir: Path
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    if isinstance(down_native, bool) or down_native < 0 or down_native > 255:
        _lifecycle_bad("lifecycle removal native is malformed")
    expected = _lifecycle_expected_names(root, project)
    checks: list[dict[str, Any]] = []
    for kind in ("containers", "volumes", "networks"):
        for name in expected[kind]:
            check = _lifecycle_freshness_check(root, kind[:-1], name)
            checks.append(check)
    _write_evidence_record(
        evidence_dir,
        _lifecycle_cleanup_name(project),
        {
            "project": project,
            "invocation": scope,
            "source_point": "cleanup",
            "down_native": down_native,
            "checks": checks,
        },
    )
    if down_native != 0:
        _lifecycle_bad("lifecycle removal native is not zero")
    for check in checks:
        if check["listed"]:
            _lifecycle_bad("lifecycle removal left a residual object")


def _lifecycle_inventory_container_id(
    inventory: dict[str, Any], expected_name: str
) -> str:
    for entry in inventory.get("objects", []):
        if (
            isinstance(entry, dict)
            and entry.get("kind") == "container"
            and entry.get("name") == expected_name
        ):
            return _lifecycle_full_id(entry.get("id"))
    _lifecycle_bad("lifecycle inventory container is missing")


def _lifecycle_recreate_diff(
    root: Path,
    project: str,
    scope: str,
    old_phase: str,
    new_phase: str,
    service: str,
    evidence_dir: Path,
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    if old_phase not in LIFECYCLE_PHASES or new_phase not in LIFECYCLE_PHASES:
        _lifecycle_bad("lifecycle phase is malformed")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", service):
        _lifecycle_bad("lifecycle service is malformed")
    old = _read_evidence_record(
        evidence_dir, _lifecycle_capture_name(project, old_phase)
    )
    new = _read_evidence_record(
        evidence_dir, _lifecycle_capture_name(project, new_phase)
    )
    expected_name = f"{project}-{service}-1"
    old_id = _lifecycle_inventory_container_id(old, expected_name)
    new_id = _lifecycle_inventory_container_id(new, expected_name)
    if old_id == new_id:
        _lifecycle_bad("lifecycle recreate did not replace the container")


def _lifecycle_audit_preflight(
    root: Path, project: str, scope: str, evidence_dir: Path
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    record = _read_evidence_record(evidence_dir, _lifecycle_preflight_name(project))
    if set(record) != {
        "project",
        "invocation",
        "source_point",
        "daemon_native",
        "checks",
        "label_check",
    }:
        _lifecycle_bad("lifecycle preflight record is malformed")
    if record["source_point"] != "preflight":
        _lifecycle_bad("lifecycle preflight point is malformed")
    if record["project"] != project or record["invocation"] != scope:
        _lifecycle_bad("lifecycle preflight binding is broken")
    if record["daemon_native"] != 0:
        _lifecycle_bad("lifecycle preflight daemon query failed")
    expected = _lifecycle_expected_names(root, project)
    seen: dict[str, set[str]] = {"container": set(), "volume": set(), "network": set()}
    checks = record["checks"]
    if not isinstance(checks, list) or not checks:
        _lifecycle_bad("lifecycle preflight checks are malformed")
    for check in checks:
        if not isinstance(check, dict) or set(check) != {
            "kind",
            "name",
            "native",
            "listed",
        }:
            _lifecycle_bad("lifecycle preflight check is malformed")
        kind = check["kind"]
        if kind not in seen:
            _lifecycle_bad("lifecycle preflight check kind is malformed")
        if check["native"] != 0:
            _lifecycle_bad("lifecycle preflight query failed")
        if check["listed"] != []:
            _lifecycle_bad("lifecycle namespace was not fresh")
        if check["name"] not in expected[kind + "s"]:
            _lifecycle_bad("lifecycle preflight name is unexpected")
        seen[kind].add(check["name"])
    if seen["container"] != set(expected["containers"]):
        _lifecycle_bad("lifecycle preflight coverage is incomplete")
    if seen["volume"] != set(expected["volumes"]):
        _lifecycle_bad("lifecycle preflight coverage is incomplete")
    if seen["network"] != set(expected["networks"]):
        _lifecycle_bad("lifecycle preflight coverage is incomplete")
    label = record["label_check"]
    if not isinstance(label, dict) or set(label) != {"native", "listed"}:
        _lifecycle_bad("lifecycle preflight label check is malformed")
    if label["native"] != 0 or label["listed"] != []:
        _lifecycle_bad("lifecycle label namespace was not fresh")


def _lifecycle_audit_capture(
    root: Path, project: str, scope: str, phase: str, evidence_dir: Path
) -> None:
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    if phase not in LIFECYCLE_PHASES:
        _lifecycle_bad("lifecycle phase is malformed")
    inventory = _read_evidence_record(
        evidence_dir, _lifecycle_capture_name(project, phase)
    )
    if set(inventory) != {
        "project",
        "invocation",
        "phase",
        "source_point",
        "daemon_native",
        "objects",
    }:
        _lifecycle_bad("lifecycle capture inventory is malformed")
    if inventory["source_point"] != "capture":
        _lifecycle_bad("lifecycle capture point is malformed")
    if inventory["project"] != project or inventory["invocation"] != scope:
        _lifecycle_bad("lifecycle capture binding is broken")
    if inventory["phase"] != phase:
        _lifecycle_bad("lifecycle capture phase mismatch")
    if inventory["daemon_native"] != 0:
        _lifecycle_bad("lifecycle capture daemon query failed")
    objects = inventory["objects"]
    if not isinstance(objects, list) or not objects:
        _lifecycle_bad("lifecycle capture inventory is empty")
    expected = _lifecycle_expected_names(root, project)
    container_records: dict[str, dict[str, Any]] = {}
    seen_volumes: set[str] = set()
    seen_networks: set[str] = set()
    for entry in objects:
        if not isinstance(entry, dict):
            _lifecycle_bad("lifecycle capture object is malformed")
        kind = entry.get("kind")
        if kind == "container":
            if set(entry) != {"kind", "id", "name", "service", "receipt"}:
                _lifecycle_bad("lifecycle capture object is malformed")
            object_id = _lifecycle_full_id(entry["id"])
            name = entry["name"]
            service = entry["service"]
            receipt = entry["receipt"]
            if (
                not isinstance(name, str)
                or not isinstance(service, str)
                or not isinstance(receipt, str)
            ):
                _lifecycle_bad("lifecycle capture object is malformed")
            if name not in expected["containers"]:
                _lifecycle_bad("lifecycle capture object is unexpected")
            if service != name[len(project) + 1 : -2]:
                _lifecycle_bad("lifecycle capture object service is broken")
            if receipt != _lifecycle_object_name(project, phase, "c", object_id):
                _lifecycle_bad("lifecycle capture receipt binding is broken")
            record = _read_evidence_record(evidence_dir, receipt)
            _lifecycle_validate_flat_meta(record, "capture")
            if record["id"] != object_id or record["name"] != f"/{name}":
                _lifecycle_bad("lifecycle capture object binding is broken")
            if record["ownership"] != {"project": project, "service": service}:
                _lifecycle_bad("lifecycle capture ownership is not caller-proven")
            if name in container_records:
                _lifecycle_bad("lifecycle capture object is duplicated")
            container_records[name] = record
        elif kind == "volume":
            if set(entry) != {"kind", "name", "receipt"}:
                _lifecycle_bad("lifecycle capture object is malformed")
            name = entry["name"]
            receipt = entry["receipt"]
            if not isinstance(name, str) or not isinstance(receipt, str):
                _lifecycle_bad("lifecycle capture object is malformed")
            if name not in expected["volumes"]:
                _lifecycle_bad("lifecycle capture object is unexpected")
            if receipt != _lifecycle_object_name(project, phase, "v", name):
                _lifecycle_bad("lifecycle capture receipt binding is broken")
            record = _read_evidence_record(evidence_dir, receipt)
            if (
                not isinstance(record, dict)
                or set(record)
                != {"name", "driver", "mountpoint", "created", "source_point"}
                or record["source_point"] != "capture"
                or record["name"] != name
            ):
                _lifecycle_bad("lifecycle capture volume is malformed")
            driver = record["driver"]
            mountpoint = record["mountpoint"]
            created = record["created"]
            if (
                not isinstance(driver, str)
                or driver in ("", TEMPLATE_NO_VALUE)
                or mountpoint is not None
                and (
                    not isinstance(mountpoint, str)
                    or mountpoint in ("", TEMPLATE_NO_VALUE)
                )
                or created is not None
                and (not isinstance(created, str) or created in ("", TEMPLATE_NO_VALUE))
            ):
                _lifecycle_bad("lifecycle capture volume is malformed")
            if name in seen_volumes:
                _lifecycle_bad("lifecycle capture object is duplicated")
            seen_volumes.add(name)
        elif kind == "network":
            if set(entry) != {"kind", "id", "name", "receipt"}:
                _lifecycle_bad("lifecycle capture object is malformed")
            object_id = _lifecycle_full_id(entry["id"])
            name = entry["name"]
            receipt = entry["receipt"]
            if not isinstance(name, str) or not isinstance(receipt, str):
                _lifecycle_bad("lifecycle capture object is malformed")
            if name not in expected["networks"]:
                _lifecycle_bad("lifecycle capture object is unexpected")
            if receipt != _lifecycle_object_name(project, phase, "n", object_id):
                _lifecycle_bad("lifecycle capture receipt binding is broken")
            record = _read_evidence_record(evidence_dir, receipt)
            if (
                not isinstance(record, dict)
                or set(record) != {"id", "name", "created", "source_point"}
                or record["source_point"] != "capture"
                or record["id"] != object_id
                or record["name"] != name
            ):
                _lifecycle_bad("lifecycle capture network is malformed")
            created = record["created"]
            if not isinstance(created, str) or created in ("", TEMPLATE_NO_VALUE):
                _lifecycle_bad("lifecycle capture network is malformed")
            if name in seen_networks:
                _lifecycle_bad("lifecycle capture object is duplicated")
            seen_networks.add(name)
        else:
            _lifecycle_bad("lifecycle capture object kind is malformed")
    if seen_volumes != set(expected["volumes"]):
        _lifecycle_bad("lifecycle capture volumes are incomplete")
    if seen_networks != set(expected["networks"]):
        _lifecycle_bad("lifecycle capture networks are incomplete")
    if phase == "negative":
        bootstrap = f"{project}-bootstrap-1"
        if bootstrap not in container_records:
            _lifecycle_bad("lifecycle negative bootstrap is missing")
        state = container_records[bootstrap]["state"]
        if state["status"] != "exited" or state["exit_code"] == 0:
            _lifecycle_bad("lifecycle negative bootstrap is not failed")
        for name in container_records:
            if name not in expected["containers"]:
                _lifecycle_bad("lifecycle capture object is unexpected")
    else:
        if set(container_records) != set(expected["containers"]):
            _lifecycle_bad("lifecycle capture containers are incomplete")


def _lifecycle_audit_helpers(
    project: str, scope: str, evidence_dir: Path, tags: list[str]
) -> None:
    # The caller supplies the complete static tag list of this invocation:
    # every helper tag is unique per invocation and known before any
    # subshell runs, so command-substitution callers cannot omit receipts.
    _lifecycle_project(project)
    _lifecycle_scope(scope)
    if not tags:
        _lifecycle_bad("lifecycle helper audit binding is missing")
    seen: set[str] = set()
    for tag in tags:
        if tag in seen:
            _lifecycle_bad("lifecycle helper audit binding is duplicated")
        seen.add(tag)
        complete = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "complete")
        )
        if set(complete) != {
            "project",
            "tag",
            "invocation",
            "source_point",
            "id",
            "name",
            "start_rc",
            "body_exit",
            "rm_rc",
            "ps_rc",
        }:
            _lifecycle_bad("lifecycle helper complete is malformed")
        if complete["source_point"] != "helper-complete":
            _lifecycle_bad("lifecycle helper complete point is malformed")
        if (
            complete["project"] != project
            or complete["tag"] != tag
            or complete["invocation"] != scope
        ):
            _lifecycle_bad("lifecycle helper binding is broken")
        container_id = _lifecycle_full_id(complete["id"])
        name = complete["name"]
        start_rc = complete["start_rc"]
        body_exit = complete["body_exit"]
        begin = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "begin")
        )
        created = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "created", container_id)
        )
        meta = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "meta", container_id)
        )
        start = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "start", container_id)
        )
        state = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "state", container_id)
        )
        removed = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "removed", container_id)
        )
        absent = _read_evidence_record(
            evidence_dir, _lifecycle_helper_name(tag, "absent", container_id)
        )
        _lifecycle_audit_helper_chain(
            begin,
            created,
            meta,
            start,
            state,
            removed,
            absent,
            project,
            tag,
            scope,
            name,
            container_id,
            start_rc,
            body_exit,
        )
        if (
            complete["rm_rc"] != removed["rm_rc"]
            or complete["ps_rc"] != absent["ps_rc"]
        ):
            _lifecycle_bad("lifecycle helper complete natives are broken")


def _lifecycle_open_dir(evidence_dir: Path) -> list[int]:
    """Open the evidence dir componentwise from the filesystem root.

    Every path component is opened with O_DIRECTORY|O_NOFOLLOW so no
    component, including the final one, may be a symlink. Public
    ancestors need not be private; the final evidence directory must
    be an euid-owned private (0700) directory. Returns every opened
    fd; the caller must close them all. Failures close the fds opened
    so far and raise a stable safe error.
    """
    if not isinstance(evidence_dir, Path) or not evidence_dir.is_absolute():
        _lifecycle_bad("lifecycle evidence dir must be absolute")
    if any(part in (".", "..") for part in evidence_dir.parts):
        _lifecycle_bad("lifecycle evidence dir has unsafe components")
    open_fds: list[int] = []
    try:
        dir_fd = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        _lifecycle_bad("lifecycle evidence dir open failed")
    open_fds.append(dir_fd)
    for component in evidence_dir.parts[1:]:
        try:
            dir_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=dir_fd,
            )
        except OSError:
            _lifecycle_close_all(open_fds)
            _lifecycle_bad("lifecycle evidence dir open failed")
        open_fds.append(dir_fd)
    try:
        st = os.fstat(dir_fd)
    except OSError:
        _lifecycle_close_all(open_fds)
        _lifecycle_bad("lifecycle evidence dir stat failed")
    if (
        not stat.S_ISDIR(st.st_mode)
        or (st.st_mode & 0o7777) != 0o700
        or st.st_uid != os.geteuid()
    ):
        _lifecycle_close_all(open_fds)
        _lifecycle_bad("lifecycle evidence dir is not private")
    return open_fds


def _lifecycle_close_all(open_fds: list[int]) -> None:
    """Close every fd; one stable raise after all attempts if any fail."""
    close_failed = False
    for fd in open_fds:
        try:
            os.close(fd)
        except OSError:
            close_failed = True
    if close_failed:
        _lifecycle_bad("lifecycle close failed")


def _write_evidence_record(
    evidence_dir: Path, relpath: str, record: dict[str, Any]
) -> None:
    """Write one flat exclusive 0600 receipt under a private dir.

    The record must be a dict whose strict JSON/UTF-8 serialization
    succeeds (nonfinite, unserializable, or non-UTF-8 content is
    refused) and whose envelope stays within the size bound before
    any leaf is created. The leaf is created with
    O_CREAT|O_EXCL|O_NOFOLLOW (collisions and symlinks are refused),
    written fully, fsynced, and verified by fstat (regular, 0600,
    euid-owned, exact size). The envelope is sorted JSON with
    utc/time_ns/record plus a trailing newline. Partial evidence is
    retained on failure (never unlinked); errors are stable and carry
    no payload, path, or exception data; every opened descriptor is
    closed even when one close fails.
    """
    _lifecycle_relpath(relpath)
    if not isinstance(record, dict):
        _lifecycle_bad("lifecycle record must be a dict")
    try:
        text = json.dumps(
            {
                "record": record,
                "time_ns": time.time_ns(),
                "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError):
        _lifecycle_bad("lifecycle record is not serializable")
    try:
        payload = (text + "\n").encode("utf-8")
    except UnicodeEncodeError:
        _lifecycle_bad("lifecycle record is not valid utf8")
    if len(payload) > RECEIPT_MAX_BYTES:
        _lifecycle_bad("lifecycle record size exceeds bound")
    open_fds = _lifecycle_open_dir(evidence_dir)
    try:
        try:
            leaf_fd = os.open(
                relpath,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=open_fds[-1],
            )
        except OSError:
            _lifecycle_bad("lifecycle receipt create failed")
        open_fds.append(leaf_fd)
        view = memoryview(payload)
        while view:
            try:
                written = os.write(leaf_fd, view)
            except OSError:
                _lifecycle_bad("lifecycle receipt write failed")
            if written <= 0:
                _lifecycle_bad("lifecycle receipt write failed")
            view = view[written:]
        try:
            os.fsync(leaf_fd)
        except OSError:
            _lifecycle_bad("lifecycle receipt fsync failed")
        try:
            st = os.fstat(leaf_fd)
        except OSError:
            _lifecycle_bad("lifecycle receipt stat failed")
        if (
            not stat.S_ISREG(st.st_mode)
            or (st.st_mode & 0o7777) != 0o600
            or st.st_uid != os.geteuid()
            or st.st_size != len(payload)
        ):
            _lifecycle_bad("lifecycle receipt verify failed")
    finally:
        _lifecycle_close_all(open_fds)


def _strict_json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    if len({key for key, _ in pairs}) != len(pairs):
        _lifecycle_bad("lifecycle receipt has duplicate keys")
    return dict(pairs)


def _strict_json_constant(name: str) -> float:
    _lifecycle_bad("lifecycle receipt has nonfinite constant")


def _read_evidence_record(evidence_dir: Path, relpath: str) -> dict[str, Any]:
    """Read one private flat JSON receipt back under the writer contract.

    The caller supplies the exact known receipt name; no directory
    listing, mtime, or latest-selection happens here. The evidence dir
    is traversed as in the writer (final dir private/euid, no symlink
    components). The leaf is opened read-only with O_NOFOLLOW and
    O_NONBLOCK, must be a regular euid-owned 0600 file within the size
    bound, and the full payload is read under the bound, decoded as
    strict UTF-8, and parsed as the strict envelope: exactly the keys
    utc (nonempty str), time_ns (int, never bool), record (dict).
    Duplicate JSON keys and nonfinite constants are rejected. Errors
    are stable with no payload/path/exception data; every opened
    descriptor is closed even when one close fails.
    """
    _lifecycle_relpath(relpath)
    open_fds = _lifecycle_open_dir(evidence_dir)
    payload = b""
    try:
        try:
            leaf_fd = os.open(
                relpath,
                os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                dir_fd=open_fds[-1],
            )
        except OSError:
            _lifecycle_bad("lifecycle receipt open failed")
        open_fds.append(leaf_fd)
        try:
            st = os.fstat(leaf_fd)
        except OSError:
            _lifecycle_bad("lifecycle receipt stat failed")
        if not stat.S_ISREG(st.st_mode):
            _lifecycle_bad("lifecycle receipt is not regular")
        if st.st_uid != os.geteuid():
            _lifecycle_bad("lifecycle receipt owner is unexpected")
        if (st.st_mode & 0o7777) != 0o600:
            _lifecycle_bad("lifecycle receipt mode is unexpected")
        if st.st_size > RECEIPT_MAX_BYTES:
            _lifecycle_bad("lifecycle receipt size exceeds bound")
        chunks: list[bytes] = []
        total = 0
        while True:
            try:
                chunk = os.read(leaf_fd, 65536)
            except OSError:
                _lifecycle_bad("lifecycle receipt read failed")
            if not chunk:
                break
            total += len(chunk)
            if total > RECEIPT_MAX_BYTES:
                _lifecycle_bad("lifecycle receipt size exceeds bound")
            chunks.append(chunk)
        payload = b"".join(chunks)
    finally:
        _lifecycle_close_all(open_fds)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        _lifecycle_bad("lifecycle receipt is not valid utf8")
    try:
        envelope = json.loads(
            text,
            object_pairs_hook=_strict_json_pairs,
            parse_constant=_strict_json_constant,
        )
    except (ValueError, RecursionError):
        _lifecycle_bad("lifecycle receipt envelope is malformed")
    if not isinstance(envelope, dict) or set(envelope) != {
        "record",
        "time_ns",
        "utc",
    }:
        _lifecycle_bad("lifecycle receipt envelope is malformed")
    if (
        not isinstance(envelope["utc"], str)
        or not envelope["utc"]
        or isinstance(envelope["time_ns"], bool)
        or not isinstance(envelope["time_ns"], int)
        or not isinstance(envelope["record"], dict)
    ):
        _lifecycle_bad("lifecycle receipt envelope is malformed")
    return envelope["record"]


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
            "browser-worker-secret",
            "browser-artifacts",
            "control-secret",
            "editor-secret",
            "local-secrets",
            "media-data",
            "media-secret",
            "postgres-data",
            "render-secret",
            "render-preview-secret",
            "render-auth-secret",
            "review-worker-secret",
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
        has_browser_worker_secret = any(
            mount.get("source") == "browser-worker-secret" for mount in mounts
        )
        _fail(
            has_browser_worker_secret == (name in BROWSER_WORKER_SECRET_MOUNT_SERVICES),
            f"{name}: browser worker secret mount policy mismatch",
        )
        has_browser_artifacts = any(
            mount.get("source") == "browser-artifacts" for mount in mounts
        )
        _fail(
            has_browser_artifacts == (name in BROWSER_ARTIFACT_MOUNT_SERVICES),
            f"{name}: browser artifact mount policy mismatch",
        )
        has_media_secret = any(
            mount.get("source") == "media-secret" for mount in mounts
        )
        _fail(
            has_media_secret == (name in MEDIA_SECRET_MOUNT_SERVICES),
            f"{name}: Media secret mount policy mismatch",
        )
        has_review_worker_secret = any(
            mount.get("source") == "review-worker-secret" for mount in mounts
        )
        _fail(
            has_review_worker_secret == (name in REVIEW_WORKER_SECRET_MOUNT_SERVICES),
            f"{name}: review-worker secret mount policy mismatch",
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
                    or (
                        key
                        in {
                            "SLAIF_AGENT_BROWSER_WORKER_ENDPOINT",
                            "SLAIF_AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE",
                        }
                        and name == "agent-api"
                    )
                    or (
                        key
                        in {
                            "BROWSER_WORKER_ARTIFACT_ROOT",
                            "BROWSER_WORKER_PREVIEW_ORIGIN",
                            "BROWSER_WORKER_SERVICE_CREDENTIAL_FILE",
                        }
                        and name == "browser-worker"
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
                    or (
                        key == "SLAIF_MEDIA_DSN_FILE"
                        and name in {"media-service", "review-worker"}
                    )
                    or (
                        key
                        in {
                            "SLAIF_MEDIA_EXPECTED_DATABASE",
                            "SLAIF_MEDIA_EXPECTED_LOGIN",
                            "SLAIF_MEDIA_EXPECTED_PRIVILEGE_ROLE",
                            "SLAIF_MEDIA_MODE",
                            "SLAIF_MEDIA_ROOT",
                        }
                        and name == "review-worker"
                    )
                    or (
                        key
                        in {
                            "SLAIF_REVIEW_WORKER_DSN_FILE",
                            "SLAIF_REVIEW_WORKER_EXPECTED_DATABASE",
                            "SLAIF_REVIEW_WORKER_EXPECTED_LOGIN",
                            "SLAIF_REVIEW_WORKER_EXPECTED_PRIVILEGE_ROLE",
                            "SLAIF_REVIEW_WORKER_MODE",
                        }
                        and name == "review-worker"
                    )
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
                    if name not in {"media-service", "review-worker"}
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
                        "SLAIF_AGENT_BROWSER_WORKER_ENDPOINT",
                        "SLAIF_AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE",
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
                    "SLAIF_AGENT_BROWSER_WORKER_ENDPOINT": (
                        "http://browser-worker:3100"
                    ),
                    "SLAIF_AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE": (
                        "/run/slaif-browser-worker/worker-token"
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
        if name == "review-worker":
            _fail(
                {
                    key: environment.get(key)
                    for key in (
                        "SLAIF_REVIEW_WORKER_DSN_FILE",
                        "SLAIF_REVIEW_WORKER_EXPECTED_DATABASE",
                        "SLAIF_REVIEW_WORKER_EXPECTED_LOGIN",
                        "SLAIF_REVIEW_WORKER_EXPECTED_PRIVILEGE_ROLE",
                        "SLAIF_REVIEW_WORKER_MODE",
                    )
                }
                == {
                    "SLAIF_REVIEW_WORKER_DSN_FILE": (
                        "/run/slaif-review-worker/review-worker-dsn"
                    ),
                    "SLAIF_REVIEW_WORKER_EXPECTED_DATABASE": "slaif",
                    "SLAIF_REVIEW_WORKER_EXPECTED_LOGIN": "slaif_review_worker_login",
                    "SLAIF_REVIEW_WORKER_EXPECTED_PRIVILEGE_ROLE": (
                        "slaif_review_worker"
                    ),
                    "SLAIF_REVIEW_WORKER_MODE": "development",
                },
                "review-worker: database configuration mismatch",
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
    browser_worker = services["browser-worker"]
    _fail(browser_worker.get("user") == "10001:10001", "browser worker UID mismatch")
    _fail(browser_worker.get("read_only") is True, "browser worker root is writable")
    _fail(
        set(browser_worker.get("cap_drop", [])) == {"ALL"}
        and set(browser_worker.get("cap_add", [])) == {"SYS_CHROOT"},
        "browser worker capability policy mismatch",
    )
    _fail(
        set(browser_worker.get("security_opt", []))
        == {
            "no-new-privileges:true",
            "seccomp=services/browser-worker/seccomp_profile.json",
        },
        "browser worker security profile mismatch",
    )
    _fail(
        browser_worker.get("pids_limit") == 256
        and str(browser_worker.get("mem_limit")) in {"805306368", "768m"}
        and float(browser_worker.get("cpus", 0)) == 1.0
        and str(browser_worker.get("shm_size")) in {"134217728", "128m"},
        "browser worker resource policy mismatch",
    )
    _fail(
        browser_worker.get("environment", {})
        == {
            "BROWSER_WORKER_ARTIFACT_ROOT": "/var/lib/slaif/browser-artifacts",
            "BROWSER_WORKER_PREVIEW_ORIGIN": "http://web:3000",
            "BROWSER_WORKER_SERVICE_CREDENTIAL_FILE": (
                "/run/slaif-browser-worker/worker-token"
            ),
        },
        "browser worker configuration mismatch",
    )
    _fail(
        services["web"].get("environment", {})
        == {
            "SLAIF_BROWSER_PREVIEW_AUTHORITY": "localhost:8080",
            "SLAIF_RENDER_SERVICE_TOKEN_FILE": "/run/slaif-render-auth/render-token",
        },
        "web internal preview authority mismatch",
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


def _lifecycle_dispatch(arguments: argparse.Namespace) -> None:
    operation = arguments.lifecycle_operation
    helper_ops = {
        "helper-begin",
        "helper-created",
        "helper-start",
        "helper-terminal",
        "helper-remove",
        "helper-complete",
    }
    if operation in helper_ops and arguments.tag is not None:
        arguments.tag = _lifecycle_single(arguments.tag, "tag")
    if operation in helper_ops and arguments.id is not None:
        arguments.id = _lifecycle_single(arguments.id, "id")
    root = arguments.root
    if arguments.lifecycle_evidence is None or arguments.scope is None:
        _lifecycle_bad("lifecycle evidence binding is missing")
    evidence_dir = arguments.lifecycle_evidence
    scope = arguments.scope
    project = arguments.project
    project_ops = {
        "preflight",
        "capture",
        "cleanup-absent",
        "recreate-diff",
        "audit-preflight",
        "audit-capture",
    }
    if operation in project_ops and not project:
        _lifecycle_bad("lifecycle project is missing")
    if operation == "preflight":
        _lifecycle_preflight(root, project, scope, evidence_dir)
    elif operation == "capture":
        if not arguments.phase:
            _lifecycle_bad("lifecycle phase is missing")
        _lifecycle_capture(root, project, arguments.phase, scope, evidence_dir)
    elif operation == "cleanup-absent":
        if arguments.down_native is None:
            _lifecycle_bad("lifecycle removal native is missing")
        _lifecycle_cleanup_absent(
            root, project, scope, arguments.down_native, evidence_dir
        )
    elif operation == "recreate-diff":
        if not (arguments.phase_old and arguments.phase_new and arguments.service):
            _lifecycle_bad("lifecycle recreate binding is missing")
        _lifecycle_recreate_diff(
            root,
            project,
            scope,
            arguments.phase_old,
            arguments.phase_new,
            arguments.service,
            evidence_dir,
        )
    elif operation == "audit-preflight":
        _lifecycle_audit_preflight(root, project, scope, evidence_dir)
    elif operation == "audit-capture":
        if not arguments.phase:
            _lifecycle_bad("lifecycle phase is missing")
        _lifecycle_audit_capture(root, project, scope, arguments.phase, evidence_dir)
    elif operation == "audit-helpers":
        tags = arguments.tag or []
        if not tags:
            _lifecycle_bad("lifecycle helper audit binding is missing")
        _lifecycle_audit_helpers(project, scope, evidence_dir, list(tags))
    elif operation == "helper-begin":
        if not (arguments.tag and arguments.name):
            _lifecycle_bad("lifecycle helper binding is missing")
        _lifecycle_helper_begin(
            root, project, scope, arguments.tag, arguments.name, evidence_dir
        )
    elif operation == "helper-created":
        if not (arguments.tag and arguments.name):
            _lifecycle_bad("lifecycle helper binding is missing")
        if arguments.id is not None:
            if arguments.create_rc not in (None, 0):
                _lifecycle_bad("lifecycle create native is malformed")
            _lifecycle_helper_created(
                root,
                project,
                scope,
                arguments.tag,
                arguments.name,
                arguments.id,
                0,
                evidence_dir,
            )
        elif arguments.create_rc is not None:
            _lifecycle_helper_created(
                root,
                project,
                scope,
                arguments.tag,
                arguments.name,
                None,
                arguments.create_rc,
                evidence_dir,
            )
        else:
            _lifecycle_bad("lifecycle helper create result is missing")
    elif operation == "helper-start":
        if not (arguments.tag and arguments.id and arguments.start_rc is not None):
            _lifecycle_bad("lifecycle helper binding is missing")
        _lifecycle_helper_start(
            root,
            project,
            scope,
            arguments.tag,
            arguments.id,
            arguments.start_rc,
            evidence_dir,
        )
    elif operation == "helper-terminal":
        if not (arguments.tag and arguments.id):
            _lifecycle_bad("lifecycle helper binding is missing")
        _lifecycle_helper_terminal(
            root, project, scope, arguments.tag, arguments.id, evidence_dir
        )
    elif operation == "helper-remove":
        if not (arguments.tag and arguments.id):
            _lifecycle_bad("lifecycle helper binding is missing")
        _lifecycle_helper_remove(
            root, project, scope, arguments.tag, arguments.id, evidence_dir
        )
    elif operation == "helper-complete":
        if not (
            arguments.tag
            and arguments.name
            and arguments.id
            and arguments.start_rc is not None
            and arguments.body_exit is not None
        ):
            _lifecycle_bad("lifecycle helper binding is missing")
        _lifecycle_helper_complete(
            root,
            project,
            scope,
            arguments.tag,
            arguments.name,
            arguments.id,
            arguments.start_rc,
            arguments.body_exit,
            evidence_dir,
        )
    else:
        _lifecycle_bad("lifecycle operation is unknown")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--project")
    parser.add_argument("--lifecycle-operation")
    parser.add_argument("--lifecycle-evidence", type=Path)
    parser.add_argument("--scope")
    parser.add_argument("--phase")
    parser.add_argument("--phase-old")
    parser.add_argument("--phase-new")
    parser.add_argument("--tag", action="append")
    parser.add_argument("--id", action="append")
    parser.add_argument("--name")
    parser.add_argument("--create-rc", type=int)
    parser.add_argument("--start-rc", type=int)
    parser.add_argument("--body-exit", type=int)
    parser.add_argument("--down-native", type=int)
    parser.add_argument("--service")
    arguments = parser.parse_args()
    if arguments.lifecycle_operation is None:
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
    try:
        _lifecycle_dispatch(arguments)
    except (
        KeyError,
        OSError,
        PolicyError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        ValueError,
    ) as error:
        print(f"compose-policy: FAILED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

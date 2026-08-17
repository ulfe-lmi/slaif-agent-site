#!/usr/bin/env python3
"""Run the bounded Control credential/pool/readiness Compose fixture."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_IMAGE = "slaif-agent-site-backend:local"
CONTROL_FILE = "/secrets/control-dsn"
CONNECTION_UNAVAILABLE = "connection_unavailable"
CONFIGURATION_INVALID = "configuration_invalid"
MIGRATION_MISMATCH = "migration_mismatch"
ROLE_MISMATCH = "role_mismatch"
UNSAFE_MARKER = "unsafe_marker"
DIAGNOSTIC_STAGES = frozenset(
    {
        "setup",
        "baseline",
        "wrong-login",
        "wrong-role",
        "unreadable-secret",
        "unsafe-marker",
        "migration-mismatch",
        "stopped-postgres",
        "recovery",
        "cleanup",
    }
)
DIAGNOSTIC_OPERATIONS = frozenset(
    {
        "initialize",
        "build-images",
        "start-fixture",
        "await-readiness",
        "await-container",
        "assert-liveness",
        "assert-nginx",
        "assert-mount",
        "stop-control",
        "replace-file",
        "recreate-control",
        "change-role",
        "set-file-mode",
        "change-marker",
        "stop-postgres",
        "start-postgres",
        "restore",
        "cleanup",
    }
)
DIAGNOSTIC_REASONS = frozenset(
    {"command-failed", "timeout", "malformed-response", "state-mismatch"}
)


class FixtureError(RuntimeError):
    """A stable allowlisted fixture failure that carries no child output."""

    def __init__(self, reason: str) -> None:
        safe_reason = reason if reason in DIAGNOSTIC_REASONS else "state-mismatch"
        super().__init__(safe_reason)
        self.reason = safe_reason


def failure_diagnostic(stage: str, operation: str, reason: str) -> str:
    """Return one allowlisted diagnostic without interpolating unsafe input."""

    safe_stage = stage if stage in DIAGNOSTIC_STAGES else "setup"
    safe_operation = operation if operation in DIAGNOSTIC_OPERATIONS else "initialize"
    safe_reason = reason if reason in DIAGNOSTIC_REASONS else "state-mismatch"
    return (
        "control-readiness-fixture: FAILED "
        f"stage={safe_stage} operation={safe_operation} reason={safe_reason}"
    )


def _run(
    command: list[str],
    *,
    check: bool = True,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        raise FixtureError("command-failed") from None
    if check and result.returncode != 0:
        raise FixtureError("command-failed")
    return result


class ControlReadinessFixture:
    def __init__(self, project: str, *, existing: bool) -> None:
        if not re.fullmatch(r"slaif(?:007|009)[a-z0-9]+", project):
            raise FixtureError("state-mismatch")
        self.project = project
        self.existing = existing
        self.diagnostic_stage = "setup"
        self.diagnostic_operation = "initialize"

    def mark(self, stage: str, operation: str) -> None:
        if stage not in DIAGNOSTIC_STAGES or operation not in DIAGNOSTIC_OPERATIONS:
            raise FixtureError("state-mismatch")
        self.diagnostic_stage = stage
        self.diagnostic_operation = operation

    def compose(
        self, *arguments: str, check: bool = True, timeout: float = 120.0
    ) -> subprocess.CompletedProcess[str]:
        return _run(
            ["docker", "compose", "-p", self.project, *arguments],
            check=check,
            timeout=timeout,
        )

    def container(self, service: str) -> str:
        identifier = self.compose("ps", "-q", service).stdout.strip()
        if not identifier:
            raise FixtureError("state-mismatch")
        return identifier

    def inspect(self, service: str) -> dict[str, Any]:
        result = _run(["docker", "inspect", self.container(service)])
        try:
            document = json.loads(result.stdout)
        except json.JSONDecodeError:
            raise FixtureError("malformed-response") from None
        if not isinstance(document, list) or len(document) != 1:
            raise FixtureError("malformed-response")
        inspected = document[0]
        if not isinstance(inspected, dict):
            raise FixtureError("malformed-response")
        return inspected

    def _health_document(self, path: str) -> tuple[int, dict[str, Any]]:
        source = (
            "import json,urllib.error,urllib.request;"
            "url='http://127.0.0.1:8000/" + path + "';"
            "status=0;document={};"
            "\ntry:\n response=urllib.request.urlopen(url,timeout=2)"
            "\nexcept urllib.error.HTTPError as error:\n response=error"
            "\nwith response:\n status=response.status;"
            "document=json.loads(response.read())"
            "\nprint(json.dumps({'status':status,'document':document},sort_keys=True))"
        )
        result = _run(
            [
                "docker",
                "exec",
                self.container("control-api"),
                "python",
                "-c",
                source,
            ],
            check=False,
            timeout=5,
        )
        if result.returncode != 0:
            raise FixtureError("command-failed")
        try:
            payload = json.loads(result.stdout)
            return int(payload["status"]), payload["document"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            raise FixtureError("malformed-response") from None

    def _wait_readiness(self, reason: str | None, *, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                status, document = self._health_document("health/ready")
                components = document.get("components", [])
                database = next(
                    item for item in components if item.get("component") == "database"
                )
                if reason is None:
                    if (
                        status == 200
                        and document.get("status") == "ready"
                        and database
                        == {
                            "component": "database",
                            "status": "ok",
                            "reason": None,
                        }
                    ):
                        return
                elif (
                    status == 503
                    and document.get("status") == "not_ready"
                    and database.get("status") == "unavailable"
                    and database.get("reason") == reason
                ):
                    return
            except (FixtureError, StopIteration):
                pass
            time.sleep(1)
        raise FixtureError("timeout")

    def _assert_liveness(self) -> None:
        status, document = self._health_document("health/live")
        if status != 200 or document != {"service": "control-api", "status": "ok"}:
            raise FixtureError("state-mismatch")

    def _wait_container_health(self, service: str, *, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                health = self.inspect(service).get("State", {}).get("Health", {})
                if health.get("Status") == "healthy":
                    return
            except FixtureError:
                pass
            time.sleep(1)
        raise FixtureError("timeout")

    def _assert_nginx_dependency(self, *, ready: bool) -> None:
        result = _run(
            [
                "docker",
                "exec",
                self.container("nginx"),
                "wget",
                "--quiet",
                "--spider",
                "http://127.0.0.1:8080/api/control/health/ready",
            ],
            check=False,
            timeout=5,
        )
        if (result.returncode == 0) is not ready:
            raise FixtureError("state-mismatch")

    def _psql(self, statement: str) -> None:
        _run(
            [
                "docker",
                "exec",
                self.container("postgres"),
                "psql",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "postgres",
                "-d",
                "slaif",
                "-c",
                statement,
            ]
        )

    def _recreate_control(self) -> None:
        # Deliberately unhealthy Control states must not cause Compose to
        # re-evaluate or recreate the one-shot bootstrap dependency graph.
        self.compose("up", "-d", "--force-recreate", "--no-deps", "control-api")

    def _replace_control_file(self, source_name: str) -> None:
        master_volume = f"{self.project}_local-secrets"
        control_volume = f"{self.project}_control-secret"
        program = (
            "import pathlib;"
            f"source=pathlib.Path('/master/{source_name}');"
            f"target=pathlib.Path('{CONTROL_FILE}');"
            "value=source.read_bytes();target.chmod(0o600);"
            "target.write_bytes(value);"
            "target.chmod(0o400)"
        )
        _run(
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
                "DAC_OVERRIDE",
                "--cap-add",
                "DAC_READ_SEARCH",
                "--cap-add",
                "FOWNER",
                "--user",
                "0:0",
                "--volume",
                f"{master_volume}:/master:ro",
                "--volume",
                f"{control_volume}:/secrets",
                "--entrypoint",
                "python",
                BACKEND_IMAGE,
                "-c",
                program,
            ]
        )

    def _set_control_mode(self, mode: int) -> None:
        control_volume = f"{self.project}_control-secret"
        program = f"import pathlib;pathlib.Path('{CONTROL_FILE}').chmod({mode:#o})"
        _run(
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
                "FOWNER",
                "--user",
                "0:0",
                "--volume",
                f"{control_volume}:/secrets",
                "--entrypoint",
                "python",
                BACKEND_IMAGE,
                "-c",
                program,
            ]
        )

    def _assert_mount_boundary(self) -> None:
        control = self.inspect("control-api")
        mounts = control.get("Mounts", [])
        volume_mounts = {
            (mount.get("Name"), mount.get("Destination"), mount.get("RW"))
            for mount in mounts
            if mount.get("Type") == "volume"
        }
        if volume_mounts != {
            (f"{self.project}_control-secret", "/run/slaif-control", False)
        }:
            raise FixtureError("state-mismatch")
        if any(mount.get("Type") == "bind" for mount in mounts):
            raise FixtureError("state-mismatch")
        environment = control.get("Config", {}).get("Env", [])
        if any("postgresql://" in item for item in environment):
            raise FixtureError("state-mismatch")

        control_id = self.container("control-api")
        check = (
            "import pathlib,stat;root=pathlib.Path('/run/slaif-control');"
            "info=root.stat();assert stat.S_IMODE(info.st_mode)==0o700;"
            "assert info.st_uid==info.st_gid==10001;"
            "path=root/'control-dsn';file_info=path.stat();"
            "assert stat.S_IMODE(file_info.st_mode)==0o400;"
            "assert file_info.st_uid==10001;value=path.read_bytes();"
            "assert value.startswith(b'postgresql://slaif_control_login:');"
            "assert not pathlib.Path('/run/slaif-secrets').exists()"
        )
        _run(["docker", "exec", control_id, "python", "-c", check])

        unrelated = _run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--user",
                "10003:10003",
                "--volume",
                f"{self.project}_control-secret:/secrets:ro",
                "--entrypoint",
                "python",
                BACKEND_IMAGE,
                "-c",
                "import pathlib;pathlib.Path('/secrets/control-dsn').read_bytes()",
            ],
            check=False,
        )
        if unrelated.returncode == 0:
            raise FixtureError("state-mismatch")

    def _restore(self) -> None:
        self.compose("start", "postgres", check=False)
        self._wait_container_health("postgres")
        self._replace_control_file("service-control-dsn")
        self._psql(
            'REVOKE "slaif_reviewer" FROM "slaif_control_login"; '
            'GRANT "slaif_control" TO "slaif_control_login";'
        )
        self.compose("run", "--rm", "bootstrap", check=False, timeout=120)
        self._recreate_control()
        self._wait_readiness(None)

    def run(self) -> None:
        if not self.existing:
            self.mark("setup", "cleanup")
            self.compose("down", "--volumes", "--remove-orphans", check=False)
            self.mark("setup", "build-images")
            self.compose("build", timeout=300)
            self.mark("setup", "start-fixture")
            self.compose("up", "--wait", timeout=240)
        print("control-readiness-stage: baseline", flush=True)
        self.mark("baseline", "await-readiness")
        self._wait_readiness(None)
        self.mark("baseline", "assert-liveness")
        self._assert_liveness()
        self.mark("baseline", "assert-nginx")
        self._assert_nginx_dependency(ready=True)
        self.mark("baseline", "assert-mount")
        self._assert_mount_boundary()

        print("control-readiness-stage: wrong-login", flush=True)
        self.mark("wrong-login", "stop-control")
        self.compose("stop", "control-api")
        self.mark("wrong-login", "replace-file")
        self._replace_control_file("service-reviewer-dsn")
        self.mark("wrong-login", "recreate-control")
        self._recreate_control()
        self.mark("wrong-login", "await-readiness")
        self._wait_readiness(CONFIGURATION_INVALID)
        self.mark("wrong-login", "assert-liveness")
        self._assert_liveness()
        self.mark("wrong-login", "assert-nginx")
        self._assert_nginx_dependency(ready=False)
        self.mark("wrong-login", "stop-control")
        self.compose("stop", "control-api")
        self.mark("wrong-login", "replace-file")
        self._replace_control_file("service-control-dsn")
        self.mark("wrong-login", "recreate-control")
        self._recreate_control()
        self.mark("wrong-login", "await-readiness")
        self._wait_readiness(None)

        print("control-readiness-stage: wrong-role", flush=True)
        self.mark("wrong-role", "change-role")
        self._psql(
            'REVOKE "slaif_control" FROM "slaif_control_login"; '
            'GRANT "slaif_reviewer" TO "slaif_control_login"; '
            "SELECT pg_catalog.pg_terminate_backend(pid) "
            "FROM pg_catalog.pg_stat_activity "
            "WHERE usename = 'slaif_control_login' AND pid <> pg_backend_pid();"
        )
        self.mark("wrong-role", "await-readiness")
        self._wait_readiness(ROLE_MISMATCH)
        self.mark("wrong-role", "assert-liveness")
        self._assert_liveness()
        self.mark("wrong-role", "assert-nginx")
        self._assert_nginx_dependency(ready=False)
        self.mark("wrong-role", "change-role")
        self._psql(
            'REVOKE "slaif_reviewer" FROM "slaif_control_login"; '
            'GRANT "slaif_control" TO "slaif_control_login";'
        )
        self.mark("wrong-role", "await-readiness")
        self._wait_readiness(None)

        print("control-readiness-stage: unreadable-secret", flush=True)
        self.mark("unreadable-secret", "stop-control")
        self.compose("stop", "control-api")
        self.mark("unreadable-secret", "set-file-mode")
        self._set_control_mode(0o000)
        self.mark("unreadable-secret", "recreate-control")
        self._recreate_control()
        self.mark("unreadable-secret", "await-readiness")
        self._wait_readiness(CONFIGURATION_INVALID)
        self.mark("unreadable-secret", "assert-liveness")
        self._assert_liveness()
        self.mark("unreadable-secret", "assert-nginx")
        self._assert_nginx_dependency(ready=False)
        self.mark("unreadable-secret", "stop-control")
        self.compose("stop", "control-api")
        self.mark("unreadable-secret", "set-file-mode")
        self._set_control_mode(0o400)
        self.mark("unreadable-secret", "recreate-control")
        self._recreate_control()
        self.mark("unreadable-secret", "await-readiness")
        self._wait_readiness(None)

        print("control-readiness-stage: unsafe-marker", flush=True)
        self.mark("unsafe-marker", "change-marker")
        self._psql(
            "UPDATE control.bootstrap_readiness SET "
            "readiness_state = 'PENDING', content_object_count = 0, "
            "content_object_fingerprint = NULL, foundation_object_count = 0, "
            "foundation_object_fingerprint = NULL, foundation_hardened = FALSE, "
            "foundation_privileges_validated = FALSE, "
            "product_privileges_validated = FALSE, safe = FALSE WHERE singleton;"
        )
        self.mark("unsafe-marker", "await-readiness")
        self._wait_readiness(UNSAFE_MARKER)
        self.mark("unsafe-marker", "assert-liveness")
        self._assert_liveness()
        self.mark("unsafe-marker", "assert-nginx")
        self._assert_nginx_dependency(ready=False)
        self.mark("unsafe-marker", "restore")
        self.compose("run", "--rm", "bootstrap", timeout=120)
        self.mark("unsafe-marker", "await-readiness")
        self._wait_readiness(None)

        print("control-readiness-stage: migration-mismatch", flush=True)
        self.mark("migration-mismatch", "change-marker")
        self._psql(
            "UPDATE control.bootstrap_readiness "
            "SET migration_revision = '006_001' WHERE singleton;"
        )
        self.mark("migration-mismatch", "await-readiness")
        self._wait_readiness(MIGRATION_MISMATCH)
        self.mark("migration-mismatch", "assert-liveness")
        self._assert_liveness()
        self.mark("migration-mismatch", "assert-nginx")
        self._assert_nginx_dependency(ready=False)
        self.mark("migration-mismatch", "change-marker")
        self._psql(
            "UPDATE control.bootstrap_readiness "
            "SET migration_revision = '007_001' WHERE singleton;"
        )
        self.mark("migration-mismatch", "await-readiness")
        self._wait_readiness(None)

        print("control-readiness-stage: stopped-postgres", flush=True)
        self.mark("stopped-postgres", "stop-postgres")
        self.compose("stop", "postgres")
        self.mark("stopped-postgres", "await-readiness")
        self._wait_readiness(CONNECTION_UNAVAILABLE)
        self.mark("stopped-postgres", "assert-liveness")
        self._assert_liveness()
        self.mark("stopped-postgres", "assert-nginx")
        self._assert_nginx_dependency(ready=False)

        print("control-readiness-stage: recovery", flush=True)
        self.mark("recovery", "start-postgres")
        self.compose("start", "postgres")
        self.mark("recovery", "await-container")
        self._wait_container_health("postgres")
        self.mark("recovery", "await-readiness")
        self._wait_readiness(None)
        self.mark("recovery", "assert-liveness")
        self._assert_liveness()
        self.mark("recovery", "assert-nginx")
        self._assert_nginx_dependency(ready=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--existing", action="store_true")
    arguments = parser.parse_args()
    try:
        fixture = ControlReadinessFixture(
            arguments.project, existing=arguments.existing
        )
    except FixtureError as error:
        print(
            failure_diagnostic("setup", "initialize", error.reason),
            flush=True,
        )
        return 1
    failures: list[tuple[str, str, str]] = []
    try:
        fixture.run()
    except FixtureError as error:
        failures.append(
            (
                fixture.diagnostic_stage,
                fixture.diagnostic_operation,
                error.reason,
            )
        )
    finally:
        if arguments.existing:
            fixture.mark("recovery", "restore")
            try:
                fixture._restore()
            except FixtureError as error:
                failures.append(
                    (
                        fixture.diagnostic_stage,
                        fixture.diagnostic_operation,
                        error.reason,
                    )
                )
        else:
            fixture.mark("cleanup", "cleanup")
            try:
                fixture.compose("down", "--volumes", "--remove-orphans", timeout=120)
            except FixtureError as error:
                failures.append(
                    (
                        fixture.diagnostic_stage,
                        fixture.diagnostic_operation,
                        error.reason,
                    )
                )
    if failures:
        for stage, operation, reason in failures:
            print(failure_diagnostic(stage, operation, reason), flush=True)
        return 1
    print(
        "control-readiness-fixture: OK "
        "mount=isolated identity=exact failures=6 recovery=clean",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

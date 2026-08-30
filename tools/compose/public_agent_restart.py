"""Secret-safe public Control/Agent restart and idempotency proof."""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

BASE_URL = "http://localhost:8080"
WORKSPACE_TITLE = "Compose public Agent restart proof"
WORKSPACE_KEY = "compose-public-agent-restart-workspace"
CAPABILITY_KEY = "compose-public-agent-restart-capability"
FIXTURE_USERNAME = "compose.admin"
FIXTURE_PASSWORD = "fixture-compose-auth-password-123"


class ProofFailure(RuntimeError):
    """A safe, non-secret proof failure reason."""


@dataclass(frozen=True, slots=True)
class PublicResponse:
    status: int
    body: bytes


class PublicClientProtocol(Protocol):
    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> PublicResponse: ...

    def csrf_token(self) -> str | None: ...

    def clear(self) -> None: ...


class PublicClient:
    """Small stdlib client whose only application paths are the public edge."""

    def __init__(self, opener: urllib.request.OpenerDirector | None = None) -> None:
        self._jar = http.cookiejar.CookieJar()
        self._opener = opener or urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._jar)
        )

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> PublicResponse:
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(headers or {})
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            BASE_URL + path,
            data=payload,
            headers=request_headers,
            method=method,
        )
        try:
            response = self._opener.open(request, timeout=10)
        except urllib.error.HTTPError as error:
            return PublicResponse(error.code, error.read())
        except (OSError, urllib.error.URLError) as error:
            raise ProofFailure("public-edge-unavailable") from error
        with response:
            return PublicResponse(response.status, response.read())

    def csrf_token(self) -> str | None:
        for cookie in self._jar:
            if cookie.name in {"slaif_csrf", "__Host-slaif_csrf"}:
                return cookie.value
        return None

    def clear(self) -> None:
        self._jar.clear()


@dataclass(frozen=True, slots=True)
class ProofResult:
    workspace_id: str
    capability_id: str
    initial_agent_status: int
    restarted_agent_status: int
    revoked_agent_status: int

    def safe_line(self) -> str:
        return (
            "public-agent-restart: OK "
            f"workspace={self.workspace_id} capability={self.capability_id} "
            f"agent-before={self.initial_agent_status} "
            f"agent-after-restart={self.restarted_agent_status} "
            f"agent-after-revoke={self.revoked_agent_status}"
        )


ComposeRunner = Callable[..., subprocess.CompletedProcess[str]]


def restart_control_and_agent(
    project: str, *, run: ComposeRunner = subprocess.run
) -> None:
    """Restart exactly the two public-boundary services under test."""
    command = [
        "docker",
        "compose",
        "-p",
        project,
        "restart",
        "control-api",
        "agent-api",
    ]
    try:
        result = run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError as error:
        raise ProofFailure("compose-recreate-unavailable") from error
    if result.returncode != 0:
        raise ProofFailure("compose-recreate-failed")


def _json(response: PublicResponse, *, status: int, label: str) -> dict[str, Any]:
    if response.status != status:
        raise ProofFailure(f"{label}-status-{response.status}")
    try:
        value = json.loads(response.body)
    except (TypeError, ValueError) as error:
        raise ProofFailure(f"{label}-invalid-json") from error
    if not isinstance(value, dict):
        raise ProofFailure(f"{label}-invalid-document")
    return value


def _list(response: PublicResponse, *, status: int, label: str) -> list[dict[str, Any]]:
    if response.status != status:
        raise ProofFailure(f"{label}-status-{response.status}")
    try:
        value = json.loads(response.body)
    except (TypeError, ValueError) as error:
        raise ProofFailure(f"{label}-invalid-json") from error
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ProofFailure(f"{label}-invalid-document")
    return value


def _require_uuid(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ProofFailure(f"{label}-invalid-id")
    try:
        UUID(value)
    except ValueError as error:
        raise ProofFailure(f"{label}-invalid-id") from error
    return value


def _require_public_id(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{16}", value):
        raise ProofFailure("capability-id-invalid")
    return value


def _wait_public_ready(client: PublicClientProtocol) -> None:
    for _attempt in range(30):
        control = client.request("/api/control/health/ready")
        agent = client.request("/api/agent/health/ready")
        if control.status == 200 and agent.status == 200:
            return
        time.sleep(1)
    raise ProofFailure("public-readiness-timeout")


def run_public_restart_proof(
    client: PublicClientProtocol,
    *,
    project: str,
    username: str,
    password: str,
    compose_run: ComposeRunner = subprocess.run,
) -> ProofResult:
    """Exercise only public Control/Agent paths across a real service recreate."""
    token: str | None = None
    capability: dict[str, Any] | None = None
    agent_headers: dict[str, str] | None = None
    human_headers: dict[str, str] | None = None
    capability_headers: dict[str, str] | None = None
    csrf: str | None = None
    try:
        login = client.request(
            "/api/control/v1/login",
            method="POST",
            body={"username": username, "password": password},
        )
        _json(login, status=200, label="login")
        csrf = client.csrf_token()
        if not csrf:
            raise ProofFailure("csrf-cookie-missing")
        _json(
            client.request("/api/control/v1/session"),
            status=200,
            label="session",
        )
        sites = _list(
            client.request("/api/control/v1/me/sites"), status=200, label="sites"
        )
        site = next(
            (item for item in sites if item.get("site_key") == "demo"),
            None,
        )
        if site is None:
            raise ProofFailure("demo-site-missing")
        site_id = _require_uuid(site.get("site_id"), "site")
        workspace_path = f"/api/control/v1/sites/{site_id}/workspaces/"
        workspace_body = {
            "title": WORKSPACE_TITLE,
            "task_description": "Public restart recovery proof",
            "delegation_preset": "L1_CONTENT_EDITOR",
            "duration_hours": 1,
        }
        missing_csrf = client.request(
            workspace_path,
            method="POST",
            body=workspace_body,
            headers={"Idempotency-Key": WORKSPACE_KEY},
        )
        if missing_csrf.status not in {400, 403}:
            raise ProofFailure(f"missing-csrf-status-{missing_csrf.status}")
        human_headers = {
            "X-CSRF-Token": csrf,
            "Idempotency-Key": WORKSPACE_KEY,
        }
        created = _json(
            client.request(
                workspace_path,
                method="POST",
                body=workspace_body,
                headers=human_headers,
            ),
            status=201,
            label="workspace-create",
        )
        workspace_id = _require_uuid(created.get("workspace_id"), "workspace")
        replayed = _json(
            client.request(
                workspace_path,
                method="POST",
                body=workspace_body,
                headers=human_headers,
            ),
            status=200,
            label="workspace-replay",
        )
        if replayed.get("workspace_id") != workspace_id:
            raise ProofFailure("workspace-replay-mismatch")

        capability_path = f"{workspace_path}{workspace_id}/capabilities/"
        capability_headers = {
            "X-CSRF-Token": csrf,
            "Idempotency-Key": CAPABILITY_KEY,
        }
        capability = _json(
            client.request(
                capability_path,
                method="POST",
                headers=capability_headers,
            ),
            status=201,
            label="capability-create",
        )
        raw_token = capability.pop("token", None)
        if not isinstance(raw_token, str) or not raw_token.startswith("sas2_"):
            raise ProofFailure("capability-token-missing")
        token = raw_token
        raw_token = None
        capability_id = _require_public_id(capability.get("capability_id"))
        if capability.get("workspace_id") != workspace_id:
            raise ProofFailure("capability-binding-invalid")
        capability_replay = client.request(
            capability_path,
            method="POST",
            headers=capability_headers,
        )
        replay_document = _json(
            capability_replay, status=200, label="capability-replay"
        )
        if token.encode("ascii") in capability_replay.body:
            raise ProofFailure("capability-token-redisplayed")
        if replay_document.get("capability_id") != capability_id:
            raise ProofFailure("capability-replay-mismatch")

        agent_headers = {"Authorization": f"Bearer {token}"}
        initial_agent = client.request("/api/agent/v1/session", headers=agent_headers)
        initial_document = _json(initial_agent, status=200, label="agent-before")
        if initial_document.get("workspace_id") != workspace_id:
            raise ProofFailure("agent-workspace-binding-invalid")
        if initial_document.get("site_id") != site_id:
            raise ProofFailure("agent-site-binding-invalid")

        restart_control_and_agent(project, run=compose_run)
        _wait_public_ready(client)
        restarted_agent = client.request("/api/agent/v1/session", headers=agent_headers)
        for _attempt in range(5):
            if restarted_agent.status == 200:
                break
            time.sleep(1)
            restarted_agent = client.request(
                "/api/agent/v1/session", headers=agent_headers
            )
        _json(restarted_agent, status=200, label="agent-after-restart")
        workspace_metadata = client.request(workspace_path)
        if token.encode("ascii") in workspace_metadata.body:
            raise ProofFailure("metadata-token-leak")
        workspaces = _list(workspace_metadata, status=200, label="workspace-list")
        matching_workspaces = [
            item for item in workspaces if item.get("workspace_id") == workspace_id
        ]
        if len(matching_workspaces) != 1:
            raise ProofFailure("workspace-persistence-invalid")
        capability_metadata = client.request(capability_path)
        if token.encode("ascii") in capability_metadata.body:
            raise ProofFailure("metadata-token-leak")
        capabilities = _list(capability_metadata, status=200, label="capability-list")
        matching_capabilities = [
            item for item in capabilities if item.get("capability_id") == capability_id
        ]
        if len(matching_capabilities) != 1:
            raise ProofFailure("capability-persistence-invalid")
        for response in (restarted_agent,):
            if token.encode("ascii") in response.body:
                raise ProofFailure("agent-response-token-leak")

        revoke_path = f"{capability_path}{capability_id}/revoke"
        revoked = _json(
            client.request(
                revoke_path,
                method="POST",
                headers={"X-CSRF-Token": csrf},
            ),
            status=200,
            label="capability-revoke",
        )
        if revoked.get("status") != "revoked":
            raise ProofFailure("capability-revoke-invalid")
        after_revoke = client.request("/api/agent/v1/session", headers=agent_headers)
        if after_revoke.status != 401 or token.encode("ascii") in after_revoke.body:
            raise ProofFailure(f"agent-after-revoke-status-{after_revoke.status}")
        final_capabilities = client.request(capability_path)
        if token.encode("ascii") in final_capabilities.body:
            raise ProofFailure("metadata-token-leak")
        final_workspace = client.request(workspace_path)
        if token.encode("ascii") in final_workspace.body:
            raise ProofFailure("metadata-token-leak")
        return ProofResult(
            workspace_id=workspace_id,
            capability_id=capability_id,
            initial_agent_status=initial_agent.status,
            restarted_agent_status=restarted_agent.status,
            revoked_agent_status=after_revoke.status,
        )
    finally:
        if capability is not None:
            capability.clear()
        if agent_headers is not None:
            agent_headers.clear()
        if human_headers is not None:
            human_headers.clear()
        if capability_headers is not None:
            capability_headers.clear()
        token = None
        csrf = None
        password = ""
        client.clear()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="public_agent_restart")
    parser.add_argument("--project", required=True)
    arguments = parser.parse_args(argv)
    try:
        result = run_public_restart_proof(
            PublicClient(),
            project=arguments.project,
            username=FIXTURE_USERNAME,
            password=FIXTURE_PASSWORD,
        )
    except ProofFailure as error:
        print(f"public-agent-restart: FAILED reason={error}", file=sys.stderr)
        return 1
    print(result.safe_line())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

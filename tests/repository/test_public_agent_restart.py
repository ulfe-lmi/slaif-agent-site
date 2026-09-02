from __future__ import annotations

import json
import subprocess
import unittest
from collections.abc import Mapping
from typing import Any
from unittest.mock import patch

from tools.compose.public_agent_restart import (
    CAPABILITY_KEY,
    WORKSPACE_KEY,
    ProofFailure,
    ProofResult,
    PublicResponse,
    _wait_public_ready,
    restart_control_and_agent,
    run_public_restart_proof,
)

SITE_ID = "12000000-0000-4000-8000-000000000002"
WORKSPACE_ID = "12000000-0000-4000-8000-000000000003"
CAPABILITY_ID = "abcdef0123456789"
TOKEN = "sas2_abcdef0123456789_" + "a" * 64


class FakePublicClient:
    def __init__(self) -> None:
        self.calls: list[
            tuple[str, str, Mapping[str, object] | None, Mapping[str, str] | None]
        ] = []
        self.revoked = False
        self.cleared = False
        self.workspace_posts = 0
        self.capability_posts = 0

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        body: Mapping[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> PublicResponse:
        self.calls.append(
            (path, method, body, None if headers is None else dict(headers))
        )
        if path == "/api/control/v1/login":
            return PublicResponse(200, b'{"username":"compose.admin"}')
        if path == "/api/control/v1/session":
            return PublicResponse(200, b'{"user_account_id":"user"}')
        if path == "/api/control/v1/me/sites":
            return PublicResponse(
                200,
                json.dumps([{"site_id": SITE_ID, "site_key": "demo"}]).encode(),
            )
        if path.endswith("/workspaces/") and method == "POST":
            if not headers or "X-CSRF-Token" not in headers:
                return PublicResponse(403, b"csrf denied")
            self.workspace_posts += 1
            status = 201 if self.workspace_posts == 1 else 200
            return PublicResponse(
                status,
                f'{{"workspace_id":"{WORKSPACE_ID}"}}'.encode(),
            )
        if path.endswith("/workspaces/") and method == "GET":
            return PublicResponse(
                200, json.dumps([{"workspace_id": WORKSPACE_ID}]).encode()
            )
        if (
            "/capabilities/" in path
            and path.endswith("/capabilities/")
            and method == "POST"
        ):
            self.capability_posts += 1
            if self.capability_posts == 1:
                return PublicResponse(
                    201,
                    f'{{"capability_id":"{CAPABILITY_ID}","workspace_id":"{WORKSPACE_ID}","token":"{TOKEN}"}}'.encode(),
                )
            return PublicResponse(
                200,
                f'{{"capability_id":"{CAPABILITY_ID}","workspace_id":"{WORKSPACE_ID}"}}'.encode(),
            )
        if "/capabilities/" in path and path.endswith("/capabilities/"):
            return PublicResponse(
                200, json.dumps([{"capability_id": CAPABILITY_ID}]).encode()
            )
        if path.endswith("/revoke"):
            self.revoked = True
            return PublicResponse(200, b'{"status":"revoked"}')
        if path == "/api/agent/v1/session":
            return PublicResponse(
                401 if self.revoked else 200,
                json.dumps(
                    {"workspace_id": WORKSPACE_ID, "site_id": SITE_ID}
                    if not self.revoked
                    else {"detail": "unauthorized"}
                ).encode(),
            )
        if path in {"/api/control/health/ready", "/api/agent/health/ready"}:
            service = "control-api" if "/control/" in path else "agent-api"
            return PublicResponse(
                200,
                json.dumps({"status": "ready", "service": service}).encode(),
            )
        raise AssertionError(f"unexpected public path: {path}")

    def csrf_token(self) -> str | None:
        return "csrf-token"

    def clear(self) -> None:
        self.cleared = True


class PublicAgentRestartTests(unittest.TestCase):
    def test_success_uses_only_public_paths_and_redacts_token(self) -> None:
        client = FakePublicClient()
        commands: list[list[str]] = []

        def compose_run(
            command: list[str], **_: Any
        ) -> subprocess.CompletedProcess[str]:
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        result = run_public_restart_proof(
            client,
            project="slaif-test",
            username="compose.admin",
            password="fixture-password",
            compose_run=compose_run,
        )

        self.assertEqual(
            result,
            ProofResult(WORKSPACE_ID, CAPABILITY_ID, 200, 200, 401),
        )
        self.assertNotIn(TOKEN, result.safe_line())
        self.assertTrue(client.cleared)
        self.assertEqual(
            commands,
            [
                [
                    "docker",
                    "compose",
                    "-p",
                    "slaif-test",
                    "restart",
                    "control-api",
                    "agent-api",
                ]
            ],
        )
        paths = {call[0] for call in client.calls}
        self.assertTrue(paths)
        self.assertTrue(
            all(
                path
                in {
                    "/api/control/health/ready",
                    "/api/agent/health/ready",
                    "/api/control/v1/login",
                    "/api/control/v1/session",
                    "/api/control/v1/me/sites",
                    f"/api/control/v1/sites/{SITE_ID}/workspaces/",
                    f"/api/control/v1/sites/{SITE_ID}/workspaces/{WORKSPACE_ID}/capabilities/",
                    f"/api/control/v1/sites/{SITE_ID}/workspaces/{WORKSPACE_ID}/capabilities/{CAPABILITY_ID}/revoke",
                    "/api/agent/v1/session",
                }
                for path in paths
            )
        )
        self.assertEqual(
            [
                call[3].get("Idempotency-Key")
                for call in client.calls
                if call[3] and call[3].get("Idempotency-Key")
            ],
            [
                WORKSPACE_KEY,
                WORKSPACE_KEY,
                WORKSPACE_KEY,
                CAPABILITY_KEY,
                CAPABILITY_KEY,
            ],
        )

    def test_failure_clears_client_and_never_runs_compose(self) -> None:
        client = FakePublicClient()
        compose_called = False

        def compose_run(*_: Any, **__: Any) -> subprocess.CompletedProcess[str]:
            nonlocal compose_called
            compose_called = True
            return subprocess.CompletedProcess([], 1, stdout="", stderr="")

        original = client.request

        def unauthorized(*args: Any, **kwargs: Any) -> PublicResponse:
            if args and args[0] == "/api/control/v1/login":
                return PublicResponse(401, b"unauthorized")
            return original(*args, **kwargs)

        client.request = unauthorized  # type: ignore[method-assign]
        with self.assertRaisesRegex(ProofFailure, "login-status-401"):
            run_public_restart_proof(
                client,
                project="slaif-test",
                username="compose.admin",
                password="fixture-password",
                compose_run=compose_run,
            )
        self.assertTrue(client.cleared)
        self.assertFalse(compose_called)

    def test_restart_failure_is_safe_and_targets_only_control_and_agent(self) -> None:
        seen: list[list[str]] = []

        def failed_run(
            command: list[str], **_: Any
        ) -> subprocess.CompletedProcess[str]:
            seen.append(command)
            return subprocess.CompletedProcess(
                command, 1, stdout="secretless", stderr="secretless"
            )

        with self.assertRaisesRegex(ProofFailure, "compose-recreate-failed"):
            restart_control_and_agent("slaif-test", run=failed_run)
        self.assertEqual(seen[0][-2:], ["control-api", "agent-api"])

    def test_crosswired_readiness_cannot_masquerade_as_ready(self) -> None:
        client = FakePublicClient()
        original = client.request

        def crosswired(*args: Any, **kwargs: Any) -> PublicResponse:
            path = args[0]
            if path == "/api/control/health/ready":
                return PublicResponse(200, b'{"status":"ready","service":"agent-api"}')
            if path == "/api/agent/health/ready":
                return PublicResponse(
                    200, b'{"status":"ready","service":"control-api"}'
                )
            return original(*args, **kwargs)

        client.request = crosswired  # type: ignore[method-assign]
        with (
            patch("tools.compose.public_agent_restart.time.sleep"),
            self.assertRaisesRegex(ProofFailure, "public-readiness-timeout"),
        ):
            _wait_public_ready(client)


if __name__ == "__main__":
    unittest.main()

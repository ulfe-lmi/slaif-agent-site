"""Contract tests for the capability-bound MCP 2026-07-28 discovery adapter.

The upstream Agent API discovery resource is emulated by a bounded local
HTTP server (stdlib only) so the structurally fixed dispatch, the error
mapping, the bounded timeout, and the invalid-upstream fail-closed behavior
are proven through the real application.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.mcp_adapter import create_app, mcp_http

PROTOCOL_VERSION = "2026-07-28"
SITE_ID = "11111111-1111-1111-1111-111111111111"
WORKSPACE_ID = "22222222-2222-2222-2222-222222222222"
BEARER = "sas2_unitcontract0123456_" + "f" * 64

DISCOVERY_JSON: dict[str, Any] = {
    "site_id": SITE_ID,
    "workspace_id": WORKSPACE_ID,
    "scopes": ["site:read", "composition:read"],
    "component_catalog_version": "component-catalog/v1",
    "composition_schema_version": "composition/v1",
    "content_model_schema_version": "content-model/v1",
    "resource_constraints": {"max_content_types": 4},
    "source_origins": ["https://example.com"],
    "request_quota": 1000,
    "mutation_quota": 500,
    "delete_quota": 100,
    "upload_quota": 100,
}

STATE: dict[str, Any] = {
    "mode": "ok",
    "count": 0,
    "paths": [],
    "methods": [],
    "bearers": [],
    "slow_seconds": 3.0,
}


class _UpstreamHandler(BaseHTTPRequestHandler):
    def log_message(self, *arguments: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        STATE["count"] += 1
        STATE["paths"].append(self.path)
        STATE["methods"].append(self.command)
        authorization = self.headers.get("Authorization", "")
        STATE["bearers"].append(authorization)
        mode = STATE["mode"]
        if mode == "slow":
            time.sleep(float(STATE["slow_seconds"]))
        if mode == "unauthorized":
            self.send_response(401)
            self.end_headers()
            return
        if mode == "quota":
            self.send_response(429)
            self.end_headers()
            return
        if mode == "server_error":
            self.send_response(500)
            self.end_headers()
            return
        if mode == "invalid_json":
            body = b"not-json"
        elif mode == "oversized":
            body = b"x" * (mcp_http.MAX_UPSTREAM_RESPONSE_BYTES + 1024)
        else:
            body = json.dumps(DISCOVERY_JSON).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def upstream_server() -> Iterator[ThreadingHTTPServer]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _UpstreamHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture()
def upstream_state() -> Iterator[None]:
    STATE.update(mode="ok", count=0, paths=[], methods=[], bearers=[], slow_seconds=3.0)
    yield


def _build_app(port: int, *, timeout: float = 1.5) -> tuple[FastAPI, httpx.AsyncClient]:
    app = create_app(
        settings=ServiceSettings.for_test(),
        upstream_base=f"http://127.0.0.1:{port}",
        upstream_timeout_seconds=timeout,
    )
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    )
    return app, client


def _body(
    method: str,
    rpc_id: str | int = 1,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(params or {})
    payload.setdefault(
        "_meta",
        {
            "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientInfo": {
                "name": "unit-client",
                "version": "1.0.0",
            },
            "io.modelcontextprotocol/clientCapabilities": {},
        },
    )
    message: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": payload}
    if rpc_id is not None:
        message["id"] = rpc_id
    return message


def _headers(
    method: str, *, name: str | None = None, bearer: str | None = BEARER
) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
        "Mcp-Method": method,
    }
    if name is not None:
        headers["Mcp-Name"] = name
    if bearer is not None:
        headers["Authorization"] = f"Bearer {bearer}"
    return headers


def _sentinel(name: str) -> str:
    encoded = base64.b64encode(name.encode("utf-8")).decode("ascii")
    return f"=?base64?{encoded}?="


@pytest.mark.usefixtures("upstream_state")
async def test_discover_returns_complete_private_capability_result(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        response = await client.post(
            "/",
            headers=_headers("server/discover"),
            json=_body("server/discover", "discover-1"),
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["jsonrpc"] == "2.0"
    assert payload["id"] == "discover-1"
    result = payload["result"]
    assert result["resultType"] == "complete"
    assert result["supportedVersions"] == [PROTOCOL_VERSION]
    assert result["capabilities"] == {"tools": {}}
    assert result["_meta"]["io.modelcontextprotocol/serverInfo"] == {
        "name": "slaif-agent-site-mcp",
        "version": PROTOCOL_VERSION,
    }
    assert result["ttlMs"] == 0
    assert result["cacheScope"] == "private"
    assert STATE["paths"] == ["/api/agent/v1/session"]
    assert STATE["methods"] == ["GET"]
    assert STATE["bearers"] == [f"Bearer {BEARER}"]


@pytest.mark.usefixtures("upstream_state")
async def test_tools_list_declares_single_closed_read_only_tool(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        response = await client.post(
            "/", headers=_headers("tools/list"), json=_body("tools/list")
        )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["resultType"] == "complete"
    assert result["ttlMs"] == 0
    assert result["cacheScope"] == "private"
    tools = result["tools"]
    assert len(tools) == 1
    tool = tools[0]
    assert tool["name"] == "site.describe"
    assert tool["inputSchema"] == {
        "type": "object",
        "additionalProperties": False,
    }
    assert tool["annotations"]["readOnlyHint"] is True
    assert tool["annotations"]["destructiveHint"] is False
    assert tool["annotations"]["idempotentHint"] is True
    assert tool["annotations"]["openWorldHint"] is False


@pytest.mark.usefixtures("upstream_state")
async def test_call_returns_typed_bounded_structured_result_with_text(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        response = await client.post(
            "/",
            headers=_headers("tools/call", name="site.describe"),
            json=_body("tools/call", params={"name": "site.describe"}),
        )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result["resultType"] == "complete"
    assert result["isError"] is False
    assert result["structuredContent"] == DISCOVERY_JSON
    expected_text = json.dumps(
        DISCOVERY_JSON, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    )
    assert result["content"] == [{"type": "text", "text": expected_text}]


@pytest.mark.usefixtures("upstream_state")
async def test_every_request_dispatches_exactly_once_with_its_own_bearer(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        for method in ("server/discover", "tools/list", "tools/call"):
            params = {"name": "site.describe"} if method == "tools/call" else None
            response = await client.post(
                "/",
                headers=_headers(method, name="site.describe" if params else None),
                json=_body(method, params=params),
            )
            assert response.status_code == 200
    assert STATE["count"] == 3
    assert STATE["paths"] == ["/api/agent/v1/session"] * 3
    assert STATE["methods"] == ["GET"] * 3
    assert STATE["bearers"] == [f"Bearer {BEARER}"] * 3


@pytest.mark.usefixtures("upstream_state")
async def test_upstream_refusals_preserve_authentication_and_rate_limit(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        STATE["mode"] = "unauthorized"
        refused = await client.post(
            "/", headers=_headers("tools/list"), json=_body("tools/list")
        )
        assert refused.status_code == 401
        assert refused.json()["error"]["code"] == -32600
        assert BEARER not in refused.text
        assert refused.headers["www-authenticate"] == "Bearer"
        STATE["mode"] = "quota"
        limited = await client.post(
            "/", headers=_headers("tools/list"), json=_body("tools/list")
        )
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == -32600


@pytest.mark.usefixtures("upstream_state")
async def test_invalid_or_failed_upstream_fails_closed(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        for mode in ("server_error", "invalid_json", "oversized"):
            STATE["mode"] = mode
            response = await client.post(
                "/", headers=_headers("tools/list"), json=_body("tools/list")
            )
            assert response.status_code == 503, mode
            assert response.json()["error"]["code"] == -32603


@pytest.mark.usefixtures("upstream_state")
async def test_bounded_timeout_refuses_slow_upstream(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1], timeout=0.5)
    STATE["mode"] = "slow"
    async with client:
        started = time.monotonic()
        response = await client.post(
            "/", headers=_headers("tools/list"), json=_body("tools/list")
        )
        elapsed = time.monotonic() - started
    assert response.status_code == 503
    assert response.json()["error"]["code"] == -32603
    assert elapsed < 2.0


@pytest.mark.usefixtures("upstream_state")
async def test_origin_present_is_refused_before_any_dispatch(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        response = await client.post(
            "/",
            headers={**_headers("tools/list"), "Origin": "https://evil.example"},
            json=_body("tools/list"),
        )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == -32600
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_non_post_methods_are_not_allowed(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        for method in ("GET", "DELETE", "PUT", "PATCH"):
            response = await client.request(method, "/")
            assert response.status_code == 405, method
            assert response.headers["allow"] == "POST"
            assert response.json()["error"]["code"] == -32600


@pytest.mark.usefixtures("upstream_state")
async def test_legacy_routes_are_unavailable_on_the_service(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        call = await client.post("/v1/call", json={"tool": "site.describe"})
        tools = await client.get("/v1/tools")
        health = await client.get("/v1/health/live")
    assert call.status_code == 404
    assert tools.status_code == 404
    assert health.status_code == 404


@pytest.mark.usefixtures("upstream_state")
async def test_shared_health_routes_remain_available(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        live = await client.get("/health/live")
        ready = await client.get("/health/ready")
    assert live.status_code == 200
    assert live.json() == {"status": "ok", "service": "mcp-adapter"}
    assert ready.status_code == 200


@pytest.mark.usefixtures("upstream_state")
@pytest.mark.parametrize(
    ("header_overrides", "header_list"),
    [
        ({"Authorization": None}, None),
        ({"Authorization": "Bearer"}, None),
        ({"Authorization": "bearer sas2_lowercaseschememustfail000"}, None),
        ({"Authorization": "Bearer has space inside"}, None),
        ({"Authorization": "Bearer " + "x" * 5000}, None),
        ({"Authorization": "Bearer sas2_shortformat"}, None),
        ({"Authorization": "Bearer notacapabilitytoken"}, None),
        (
            None,
            [
                ("Authorization", f"Bearer {BEARER}"),
                ("Authorization", f"Bearer {BEARER}"),
            ],
        ),
    ],
)
async def test_missing_or_malformed_bearer_is_refused_without_dispatch(
    upstream_server: ThreadingHTTPServer,
    header_overrides: dict[str, str | None] | None,
    header_list: list[tuple[str, str]] | None,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    headers = _headers("tools/list")
    if header_overrides is not None:
        for key, value in header_overrides.items():
            if value is None:
                del headers[key]
            else:
                headers[key] = value
    async with client:
        if header_list is None:
            response = await client.post("/", headers=headers, json=_body("tools/list"))
        else:
            response = await client.post(
                "/", headers=[*headers.items(), *header_list], json=_body("tools/list")
            )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == -32600
    assert response.headers["www-authenticate"] == "Bearer"
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
@pytest.mark.parametrize(
    ("header_overrides", "body_params", "expected_code"),
    [
        ({"MCP-Protocol-Version": None}, None, -32020),
        (
            {"MCP-Protocol-Version": PROTOCOL_VERSION},
            {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": "2025-03-26",
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            },
            -32020,
        ),
        (
            {"MCP-Protocol-Version": "2025-03-26"},
            {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": "2025-03-26",
                    "io.modelcontextprotocol/clientCapabilities": {},
                }
            },
            -32022,
        ),
        ({"Mcp-Method": None}, None, -32020),
        ({"Mcp-Method": "tools/list"}, None, -32020),
        ({}, {"_meta": {}}, -32602),
        (
            {},
            {"_meta": {"io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION}},
            -32602,
        ),
        (
            {},
            {
                "_meta": {
                    "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
                    "io.modelcontextprotocol/clientCapabilities": [],
                }
            },
            -32602,
        ),
    ],
)
async def test_metadata_validation_errors_map_to_protocol_codes(
    upstream_server: ThreadingHTTPServer,
    header_overrides: dict[str, str | None],
    body_params: dict[str, Any] | None,
    expected_code: int,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    headers = _headers("server/discover")
    for key, value in header_overrides.items():
        if value is None:
            del headers[key]
        else:
            headers[key] = value
    params = body_params
    if params is None:
        params = _body("server/discover")["params"]
    async with client:
        response = await client.post(
            "/",
            headers=headers,
            json=_body("server/discover", params=params),
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == expected_code
    if expected_code == -32022:
        assert response.json()["error"]["data"] == {
            "supported": [PROTOCOL_VERSION],
            "requested": "2025-03-26",
        }
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_unknown_method_is_404_method_not_found(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        response = await client.post(
            "/",
            headers=_headers("prompts/list"),
            json=_body("prompts/list"),
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == -32601
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_unknown_top_level_fields_are_refused_without_dispatch(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        for extra in ({"notification": True}, {"json": "2.0", "x": 1}):
            body = {**_body("tools/list"), **extra}
            response = await client.post("/", headers=_headers("tools/list"), json=body)
            assert response.status_code == 400, extra
            assert response.json()["error"]["code"] == -32600, extra
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_call_name_header_must_match_body(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        missing = await client.post(
            "/",
            headers=_headers("tools/call"),
            json=_body("tools/call", params={"name": "site.describe"}),
        )
        assert missing.status_code == 400
        assert missing.json()["error"]["code"] == -32020
        mismatched = await client.post(
            "/",
            headers=_headers("tools/call", name="site.other"),
            json=_body("tools/call", params={"name": "site.describe"}),
        )
        assert mismatched.status_code == 400
        assert mismatched.json()["error"]["code"] == -32020
        sentinel = await client.post(
            "/",
            headers=_headers("tools/call", name=_sentinel("site.describe")),
            json=_body("tools/call", params={"name": "site.describe"}),
        )
        assert sentinel.status_code == 200
        broken = await client.post(
            "/",
            headers=_headers("tools/call", name="=?base64?!!!notbase64?="),
            json=_body("tools/call", params={"name": "site.describe"}),
        )
        assert broken.status_code == 400
        assert broken.json()["error"]["code"] == -32020
    assert STATE["count"] == 1


@pytest.mark.usefixtures("upstream_state")
async def test_unexpected_arguments_never_dispatch(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        forbidden = await client.post(
            "/",
            headers=_headers("tools/call", name="site.describe"),
            json=_body(
                "tools/call",
                params={"name": "site.describe", "arguments": {"site_id": SITE_ID}},
            ),
        )
        assert forbidden.status_code == 400
        assert forbidden.json()["error"]["code"] == -32602
        not_object = await client.post(
            "/",
            headers=_headers("tools/call", name="site.describe"),
            json=_body(
                "tools/call", params={"name": "site.describe", "arguments": "nope"}
            ),
        )
        assert not_object.status_code == 400
        assert not_object.json()["error"]["code"] == -32602
        unknown_tool = await client.post(
            "/",
            headers=_headers("tools/call", name="site.list"),
            json=_body("tools/call", params={"name": "site.list"}),
        )
        assert unknown_tool.status_code == 400
        error = unknown_tool.json()["error"]
        assert error["code"] == -32602
        assert error["message"] == "Unknown tool: site.list"
        extra = await client.post(
            "/",
            headers=_headers("server/discover"),
            json=_body(
                "server/discover",
                params={**_body("server/discover")["params"], "cursor": "x"},
            ),
        )
        assert extra.status_code == 400
        assert extra.json()["error"]["code"] == -32602
        cursor = await client.post(
            "/",
            headers=_headers("tools/list"),
            json=_body(
                "tools/list", params={**_body("tools/list")["params"], "cursor": "x"}
            ),
        )
        assert cursor.status_code == 400
        assert cursor.json()["error"]["code"] == -32602
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_malformed_json_and_structure_are_protocol_errors(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        invalid_json = await client.post(
            "/", headers=_headers("tools/list"), content=b"{not json"
        )
        assert invalid_json.status_code == 400
        assert invalid_json.json()["error"]["code"] == -32700
        assert "id" not in invalid_json.json()
        invalid_utf8 = await client.post(
            "/", headers=_headers("tools/list"), content=b"\xff\xfe{invalid}"
        )
        assert invalid_utf8.status_code == 400
        assert invalid_utf8.json()["error"]["code"] == -32700
        deep_nesting = b"[" * 100_000 + b"]" * 100_000
        deep = await client.post(
            "/", headers=_headers("tools/list"), content=deep_nesting
        )
        assert deep.status_code == 400
        assert deep.json()["error"]["code"] == -32700
        array = await client.post(
            "/", headers=_headers("tools/list"), content=b"[1, 2]"
        )
        assert array.status_code == 400
        assert array.json()["error"]["code"] == -32700
        wrong_version = await client.post(
            "/",
            headers=_headers("tools/list"),
            content=json.dumps({**_body("tools/list"), "jsonrpc": "1.0"}).encode(),
        )
        assert wrong_version.status_code == 400
        assert wrong_version.json()["error"]["code"] == -32600
        null_id = await client.post(
            "/",
            headers=_headers("tools/list"),
            content=json.dumps({**_body("tools/list"), "id": None}).encode(),
        )
        assert null_id.status_code == 400
        assert null_id.json()["error"]["code"] == -32600
        float_id = await client.post(
            "/",
            headers=_headers("tools/list"),
            content=json.dumps({**_body("tools/list"), "id": 1.5}).encode(),
        )
        assert float_id.status_code == 400
        assert float_id.json()["error"]["code"] == -32600
        notification = _body("tools/list")
        del notification["id"]
        no_id = await client.post(
            "/",
            headers=_headers("tools/list"),
            content=json.dumps(notification).encode(),
        )
        assert no_id.status_code == 400
        assert no_id.json()["error"]["code"] == -32600
        assert "id" not in no_id.json()
        wrong_content_type = await client.post(
            "/",
            headers={
                **_headers("tools/list"),
                "Content-Type": "text/plain",
            },
            content=json.dumps(_body("tools/list")).encode(),
        )
        assert wrong_content_type.status_code == 400
        assert wrong_content_type.json()["error"]["code"] == -32600
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_oversized_request_body_is_refused(
    upstream_server: ThreadingHTTPServer,
) -> None:
    _, client = _build_app(upstream_server.server_address[1])
    oversized = json.dumps(_body("tools/list"))[:50] + "x" * (
        mcp_http.MAX_REQUEST_BYTES + 1
    )
    async with client:
        response = await client.post(
            "/", headers=_headers("tools/list"), content=oversized.encode()
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == -32700
    assert STATE["count"] == 0


@pytest.mark.usefixtures("upstream_state")
async def test_dispatch_is_structurally_fixed(
    upstream_server: ThreadingHTTPServer,
) -> None:
    with pytest.raises(ValueError):
        create_app(
            settings=ServiceSettings.for_test(),
            upstream_base="http://agent-api:8000/extra",
        )
    with pytest.raises(ValueError):
        create_app(
            settings=ServiceSettings.for_test(),
            upstream_base="https://agent-api:8000",
        )
    with pytest.raises(ValueError):
        create_app(
            settings=ServiceSettings.for_test(),
            upstream_base="http://agent-api",
        )
    with pytest.raises(ValueError):
        create_app(
            settings=ServiceSettings.for_test(),
            upstream_base="http://user:pass@agent-api:8000",
        )


CALLER_MARKER = "CALLER-MARKER-DO-NOT-LOG-77"


@pytest.mark.usefixtures("upstream_state")
async def test_logging_correlates_operation_site_and_workspace_only(
    upstream_server: ThreadingHTTPServer,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The fixed audit event carries the fixed RPC/tool operation, the
    validated site/workspace, the HTTP statuses, and the duration. The
    caller-controlled JSON-RPC id (here an ordinary caller marker), the
    bearer, the payload, and the upstream path never enter the log."""
    caplog.set_level(logging.INFO, logger="slaif_agent_site.mcp_adapter.mcp_http")
    _, client = _build_app(upstream_server.server_address[1])
    async with client:
        await client.post(
            "/",
            headers=_headers("tools/call", name="site.describe"),
            json=_body("tools/call", CALLER_MARKER, params={"name": "site.describe"}),
        )
    records = [
        record
        for record in caplog.records
        if record.name == "slaif_agent_site.mcp_adapter.mcp_http"
    ]
    assert records
    completed = [
        record
        for record in records
        if record.__dict__.get("event_fields", {}).get("mcp_operation")
        == "tools/call:site.describe"
    ]
    assert completed
    fields = completed[0].__dict__["event_fields"]
    assert fields["http_status"] == 200
    assert fields["upstream_status"] == 200
    assert fields["site_id"] == SITE_ID
    assert fields["workspace_id"] == WORKSPACE_ID
    assert isinstance(fields["duration_ms"], int)
    for record in records:
        event_fields = record.__dict__.get("event_fields", {})
        assert CALLER_MARKER not in json.dumps(event_fields)
    captured = caplog.text
    assert BEARER not in captured
    assert CALLER_MARKER not in captured
    assert "/api/agent/v1/session" not in captured
    assert "composition/v1" not in captured
    assert "unit-client" not in captured


@pytest.mark.usefixtures("upstream_state")
async def test_concurrency_slot_is_held_until_cancelled_transport_ends(
    upstream_server: ThreadingHTTPServer,
) -> None:
    """A cancelled handler must not release the slot while its blocking
    stdlib transport is still running, even when the cancellation is
    repeated before the transport finishes; the slot is free again after
    completion."""
    upstream = mcp_http.McpUpstream(
        host="127.0.0.1",
        port=upstream_server.server_address[1],
        timeout_seconds=5.0,
        semaphore=asyncio.Semaphore(1),
    )
    STATE["mode"] = "slow"
    STATE["slow_seconds"] = 0.6
    first = asyncio.create_task(upstream.bounded_get(BEARER))
    await asyncio.sleep(0.15)
    first.cancel()
    first.cancel()
    second_started = time.monotonic()
    second = asyncio.create_task(upstream.bounded_get(BEARER))
    with pytest.raises(asyncio.CancelledError):
        await first
    status, body = await second
    elapsed_second = time.monotonic() - second_started
    assert status == 200
    assert json.loads(body) == DISCOVERY_JSON
    # The slot stayed held for the first transport (~0.6s total), so the
    # second call cannot start before ~0.6s and then needs its own ~0.6s.
    assert elapsed_second >= 0.9
    assert STATE["count"] == 2
    # The slot was released exactly once: a third request runs immediately.
    third_started = time.monotonic()
    status3, _ = await asyncio.wait_for(upstream.bounded_get(BEARER), timeout=3.0)
    assert status3 == 200
    assert time.monotonic() - third_started < 1.2
    assert STATE["count"] == 3

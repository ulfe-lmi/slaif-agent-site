"""MCP adapter: one capability-bound discovery tool over MCP 2026-07-28.

Implements the Streamable HTTP transport (JSON mode) for protocol revision
2026-07-28 with a single read-only tool, ``site.describe``. Every request is
independently authenticated with a pre-issued product capability bearer and
validates the current capability through the one fixed Agent API discovery
resource ``GET /api/agent/v1/session``, consuming that resource's existing
request quota once. The adapter holds no database credentials, no business
logic, and no authorization or response cache. Browser Origins are refused;
native clients only.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import http.client
import json
import logging
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, Response

from ..agent_api.models import AgentDiscoveryResponse
from ..agent_state.capability import validate_token_format

LOGGER = logging.getLogger(__name__)

PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_VERSIONS: tuple[str, ...] = (PROTOCOL_VERSION,)
SERVER_INFO: Mapping[str, str] = {
    "name": "slaif-agent-site-mcp",
    "version": PROTOCOL_VERSION,
}
SUPPORTED_METHODS: frozenset[str] = frozenset(
    {"server/discover", "tools/list", "tools/call"}
)
TOOL_NAME = "site.describe"
TOOL_TITLE = "Site and workspace discovery"
TOOL_DESCRIPTION = (
    "Read the current capability's bound site, workspace, effective scopes, "
    "catalog and schema versions, resource constraints, approved source "
    "origins, and request quotas."
)
TOOL_INPUT_SCHEMA: Mapping[str, Any] = {
    "type": "object",
    "additionalProperties": False,
}
TOOL_ANNOTATIONS: Mapping[str, bool] = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}
DISCOVERY_INSTRUCTIONS = (
    "Read-only discovery for one bound site workspace. Call site.describe "
    "with no arguments to read the current capability's site, workspace, "
    "scopes, and quotas."
)
UPSTREAM_PATH = "/api/agent/v1/session"
DEFAULT_UPSTREAM_BASE = "http://agent-api:8000"
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_UPSTREAM_CONCURRENCY = 16
MAX_REQUEST_BYTES = 1_048_576
MAX_UPSTREAM_RESPONSE_BYTES = 1_048_576
MAX_BEARER_TOKEN_BYTES = 4096

MCP_PROTOCOL_VERSION_HEADER = "mcp-protocol-version"
MCP_METHOD_HEADER = "mcp-method"
MCP_NAME_HEADER = "mcp-name"
PROTOCOL_VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"
SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo"

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
HEADER_MISMATCH = -32020
UNSUPPORTED_PROTOCOL_VERSION = -32022

_BEARER_PREFIX = "Bearer "
_BASE64_SENTINEL = re.compile(r"\A=\?base64\?(?P<b64>.+)\?=\Z", re.DOTALL)
_UPSTREAM_HOST = re.compile(r"\A[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
_UPSTREAM_IPV4 = re.compile(r"\A\d{1,3}(?:\.\d{1,3}){3}\Z")


@dataclass(frozen=True)
class McpUpstream:
    """Structurally fixed Agent API discovery target."""

    host: str
    port: int
    timeout_seconds: float
    semaphore: asyncio.Semaphore

    async def bounded_get(self, bearer: str) -> tuple[int, bytes]:
        """One fixed upstream GET.

        The concurrency slot is held until the blocking transport actually
        ends. The release is registered as a completion callback on the
        executor future, so cancellation of the handler task - even repeated
        before the blocking operation finishes - cannot release the slot
        early or await an already-settled future; the stdlib thread runs to
        completion and the callback releases exactly once. A submission
        failure releases immediately. The cancellation propagates unchanged.
        """
        await self.semaphore.acquire()
        try:
            pending = asyncio.get_running_loop().run_in_executor(
                None,
                _upstream_get,
                self.host,
                self.port,
                self.timeout_seconds,
                bearer,
            )
        except BaseException:
            self.semaphore.release()
            raise

        def release_slot(future: asyncio.Future[Any]) -> None:
            if not future.cancelled():
                future.exception()
            self.semaphore.release()

        pending.add_done_callback(release_slot)
        return await asyncio.shield(pending)


def _rpc_response(status_code: int, payload: Mapping[str, Any]) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=dict(payload),
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )


def _error_response(
    status_code: int,
    code: int,
    message: str,
    rpc_id: str | int | None = None,
    data: Mapping[str, Any] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = dict(data)
    payload: dict[str, Any] = {"jsonrpc": "2.0"}
    if rpc_id is not None:
        payload["id"] = rpc_id
    payload["error"] = error
    return _rpc_response(status_code, payload)


def _unauthenticated(message: str, rpc_id: str | int | None) -> JSONResponse:
    """401 refusal presenting the Bearer challenge, without upstream text."""
    response = _error_response(401, INVALID_REQUEST, message, rpc_id)
    response.headers["WWW-Authenticate"] = "Bearer"
    return response


def _result_response(rpc_id: str | int, result: Mapping[str, Any]) -> JSONResponse:
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "result": dict(result),
    }
    return _rpc_response(200, payload)


def _server_info_meta() -> dict[str, Any]:
    return {SERVER_INFO_META_KEY: dict(SERVER_INFO)}


def _discover_result() -> dict[str, Any]:
    return {
        "resultType": "complete",
        "supportedVersions": list(SUPPORTED_VERSIONS),
        "capabilities": {"tools": {}},
        "_meta": _server_info_meta(),
        "instructions": DISCOVERY_INSTRUCTIONS,
        "ttlMs": 0,
        "cacheScope": "private",
    }


def _list_tools_result() -> dict[str, Any]:
    return {
        "resultType": "complete",
        "tools": [
            {
                "name": TOOL_NAME,
                "title": TOOL_TITLE,
                "description": TOOL_DESCRIPTION,
                "inputSchema": dict(TOOL_INPUT_SCHEMA),
                "annotations": dict(TOOL_ANNOTATIONS),
            }
        ],
        "_meta": _server_info_meta(),
        "ttlMs": 0,
        "cacheScope": "private",
    }


def _call_tool_result(structured: Mapping[str, Any]) -> dict[str, Any]:
    text = json.dumps(
        dict(structured),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return {
        "resultType": "complete",
        "content": [{"type": "text", "text": text}],
        "structuredContent": dict(structured),
        "isError": False,
        "_meta": _server_info_meta(),
    }


def _method_not_allowed() -> JSONResponse:
    response = _error_response(
        405, INVALID_REQUEST, "Only POST is supported on the MCP endpoint."
    )
    response.headers["Allow"] = "POST"
    return response


def _origin_refused() -> JSONResponse:
    return _error_response(403, INVALID_REQUEST, "Origin requests are not accepted.")


def _validate_upstream_base(base: str) -> tuple[str, int]:
    parsed = urlsplit(base)
    if (
        parsed.scheme != "http"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError("the MCP upstream base must be an HTTP host with port")
    host = parsed.hostname or ""
    if not (
        _UPSTREAM_HOST.fullmatch(host) or _UPSTREAM_IPV4.fullmatch(host) or ":" in host
    ):
        raise ValueError("the MCP upstream host is invalid")
    port = parsed.port
    if port is None:
        raise ValueError("the MCP upstream base requires an explicit port")
    return host, port


def _upstream_get(
    host: str, port: int, timeout_seconds: float, bearer: str
) -> tuple[int, bytes]:
    """One fixed GET to the Agent API discovery resource (stdlib, no
    redirects, no cookies, no proxy routing, no credential reuse)."""
    connection_host = f"[{host}]" if ":" in host else host
    connection = http.client.HTTPConnection(
        connection_host, port, timeout=timeout_seconds
    )
    try:
        connection.request(
            "GET",
            UPSTREAM_PATH,
            headers={
                "Authorization": f"{_BEARER_PREFIX}{bearer}",
                "Accept": "application/json",
            },
        )
        response = connection.getresponse()
        body = response.read(MAX_UPSTREAM_RESPONSE_BYTES + 1)
        if len(body) > MAX_UPSTREAM_RESPONSE_BYTES:
            raise ValueError("the upstream response exceeds the bounded size")
        return response.status, body
    finally:
        connection.close()


class _HeaderView(Protocol):
    def getlist(self, key: str) -> list[str]: ...


def _validated_header_value(headers: _HeaderView, name: str) -> str | None:
    values = headers.getlist(name)
    if len(values) != 1:
        return None
    value = values[0]
    if not value:
        return None
    for character in value:
        code = ord(character)
        if character == "\t" or character == " " or 0x21 <= code <= 0x7E:
            continue
        return None
    return value


def _decode_mcp_name(value: str) -> str | None:
    candidate = value.strip()
    match = _BASE64_SENTINEL.fullmatch(candidate)
    if match is None:
        return candidate
    try:
        payload = base64.b64decode(match.group("b64").encode("ascii"), validate=True)
    except (binascii.Error, UnicodeEncodeError, ValueError):
        return None
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _extract_bearer(headers: _HeaderView) -> str | None:
    values = headers.getlist("authorization")
    if len(values) != 1:
        return None
    value = values[0]
    if not value.startswith(_BEARER_PREFIX):
        return None
    token = value[len(_BEARER_PREFIX) :]
    if not token or len(token) > MAX_BEARER_TOKEN_BYTES:
        return None
    if any(character.isspace() for character in token):
        return None
    return token


def _is_valid_request_id(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, str):
        return True
    return isinstance(value, int)


async def _read_bounded_body(request: Request) -> bytes | None:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > MAX_REQUEST_BYTES:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _log_mcp_event(
    operation: str,
    http_status: int,
    *,
    site_id: str | None = None,
    workspace_id: str | None = None,
    upstream_status: int | None = None,
    duration_ms: int | None = None,
) -> None:
    """Fixed-field audit event.

    Only the fixed operation class, the validated site/workspace, the HTTP
    statuses, and the duration are recorded. The caller-controlled JSON-RPC
    id is never logged; the shared JSON formatter already carries the
    service request id. No bearer, request payload, or upstream path ever
    enters the log.
    """
    event_fields: dict[str, Any] = {
        "mcp_operation": operation,
        "http_status": http_status,
    }
    if site_id is not None:
        event_fields["site_id"] = site_id
    if workspace_id is not None:
        event_fields["workspace_id"] = workspace_id
    if upstream_status is not None:
        event_fields["upstream_status"] = upstream_status
    if duration_ms is not None:
        event_fields["duration_ms"] = duration_ms
    LOGGER.info(
        "mcp request processed",
        extra={"event_fields": event_fields},
    )


def _reject_non_finite_constant(name: str) -> float:
    """``json.loads`` hook: JSON has no NaN/Infinity/-Infinity literals."""
    raise ValueError(name)


async def _handle_mcp(request: Request) -> Response:
    started = time.monotonic()

    if request.headers.get("origin") is not None:
        _log_mcp_event("origin-refusal", 403)
        return _origin_refused()

    if request.method != "POST":
        _log_mcp_event("method-not-allowed", 405)
        return _method_not_allowed()

    content_type = request.headers.get("content-type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        _log_mcp_event("invalid-request", 400)
        return _error_response(
            400, INVALID_REQUEST, "Content-Type must be application/json."
        )

    raw = await _read_bounded_body(request)
    if raw is None:
        _log_mcp_event("invalid-request", 400)
        return _error_response(
            400, PARSE_ERROR, "Request body exceeds the bounded size."
        )

    try:
        message = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_non_finite_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        _log_mcp_event("parse-error", 400)
        return _error_response(400, PARSE_ERROR, "Invalid JSON.")

    if not isinstance(message, dict):
        _log_mcp_event("parse-error", 400)
        return _error_response(400, PARSE_ERROR, "Request must be a JSON object.")

    if set(message) - {"jsonrpc", "method", "params", "id"}:
        _log_mcp_event("invalid-request", 400)
        return _error_response(
            400, INVALID_REQUEST, "Request contains unknown top-level fields."
        )

    if message.get("jsonrpc") != "2.0":
        _log_mcp_event("invalid-request", 400)
        return _error_response(400, INVALID_REQUEST, "jsonrpc must be '2.0'.")

    rpc_method = message.get("method")
    if not isinstance(rpc_method, str) or not rpc_method:
        _log_mcp_event("invalid-request", 400)
        return _error_response(
            400, INVALID_REQUEST, "method must be a non-empty string."
        )

    rpc_id: str | int | None = None
    if "id" in message:
        rpc_id = message["id"]
        if not _is_valid_request_id(rpc_id):
            _log_mcp_event("invalid-request", 400)
            return _error_response(
                400, INVALID_REQUEST, "id must be a string or integer."
            )
    else:
        _log_mcp_event("invalid-request", 400)
        return _error_response(
            400, INVALID_REQUEST, "Notifications are not accepted on this transport."
        )

    params = message.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        _log_mcp_event("invalid-request", 400)
        return _error_response(400, INVALID_REQUEST, "params must be an object.")

    headers = request.headers
    protocol_header = _validated_header_value(headers, MCP_PROTOCOL_VERSION_HEADER)
    if protocol_header is None:
        _log_mcp_event("header-mismatch", 400)
        return _error_response(
            400,
            HEADER_MISMATCH,
            "Missing or malformed MCP-Protocol-Version header.",
            rpc_id,
        )

    meta = params.get("_meta")
    if not isinstance(meta, dict):
        _log_mcp_event("invalid-params", 400)
        return _error_response(
            400, INVALID_PARAMS, "params._meta must be an object.", rpc_id
        )
    body_version = meta.get(PROTOCOL_VERSION_META_KEY)
    if not isinstance(body_version, str) or not body_version:
        _log_mcp_event("invalid-params", 400)
        return _error_response(
            400,
            INVALID_PARAMS,
            "params._meta requires io.modelcontextprotocol/protocolVersion.",
            rpc_id,
        )
    if protocol_header.strip() != body_version:
        _log_mcp_event("header-mismatch", 400)
        return _error_response(
            400,
            HEADER_MISMATCH,
            "MCP-Protocol-Version header does not match the request body.",
            rpc_id,
        )
    if body_version not in SUPPORTED_VERSIONS:
        _log_mcp_event("unsupported-version", 400)
        return _error_response(
            400,
            UNSUPPORTED_PROTOCOL_VERSION,
            "Unsupported protocol version.",
            rpc_id,
            data={
                "supported": list(SUPPORTED_VERSIONS),
                "requested": body_version,
            },
        )

    method_header = _validated_header_value(headers, MCP_METHOD_HEADER)
    if method_header is None:
        _log_mcp_event("header-mismatch", 400)
        return _error_response(
            400, HEADER_MISMATCH, "Missing or malformed Mcp-Method header.", rpc_id
        )
    if method_header.strip() != rpc_method:
        _log_mcp_event("header-mismatch", 400)
        return _error_response(
            400,
            HEADER_MISMATCH,
            "Mcp-Method header does not match the request body.",
            rpc_id,
        )

    client_capabilities = meta.get(CLIENT_CAPABILITIES_META_KEY)
    if not isinstance(client_capabilities, dict):
        _log_mcp_event("invalid-params", 400)
        return _error_response(
            400,
            INVALID_PARAMS,
            "params._meta requires io.modelcontextprotocol/clientCapabilities.",
            rpc_id,
        )

    tool_name: str | None = None
    if rpc_method == "tools/call":
        name_value = params.get("name")
        if not isinstance(name_value, str) or not name_value:
            _log_mcp_event("invalid-params", 400)
            return _error_response(
                400, INVALID_PARAMS, "params.name is required for tools/call.", rpc_id
            )
        tool_name = name_value
        name_header = _validated_header_value(headers, MCP_NAME_HEADER)
        if name_header is None:
            _log_mcp_event("header-mismatch", 400)
            return _error_response(
                400, HEADER_MISMATCH, "Missing or malformed Mcp-Name header.", rpc_id
            )
        decoded_name = _decode_mcp_name(name_header)
        if decoded_name is None or decoded_name != tool_name:
            _log_mcp_event("header-mismatch", 400)
            return _error_response(
                400,
                HEADER_MISMATCH,
                "Mcp-Name header does not match the request body.",
                rpc_id,
            )

    if rpc_method not in SUPPORTED_METHODS:
        _log_mcp_event("method-not-found", 404)
        return _error_response(404, METHOD_NOT_FOUND, "Method not found.", rpc_id)

    if rpc_method == "server/discover":
        if set(params) - {"_meta"}:
            _log_mcp_event("invalid-params", 400)
            return _error_response(
                400,
                INVALID_PARAMS,
                "server/discover accepts no extra parameters.",
                rpc_id,
            )
    elif rpc_method == "tools/list":
        if set(params) - {"_meta", "cursor"}:
            _log_mcp_event("invalid-params", 400)
            return _error_response(
                400, INVALID_PARAMS, "tools/list accepts no extra parameters.", rpc_id
            )
        if "cursor" in params:
            _log_mcp_event("invalid-params", 400)
            return _error_response(400, INVALID_PARAMS, "Invalid cursor.", rpc_id)
    else:
        if set(params) - {"_meta", "name", "arguments"}:
            _log_mcp_event("invalid-params", 400)
            return _error_response(
                400,
                INVALID_PARAMS,
                "tools/call accepts no extra parameters.",
                rpc_id,
            )
        if "arguments" in params:
            arguments = params["arguments"]
            if not isinstance(arguments, dict):
                _log_mcp_event("invalid-params", 400)
                return _error_response(
                    400,
                    INVALID_PARAMS,
                    "Invalid params for tools/call: 'arguments' must be an object.",
                    rpc_id,
                )
        else:
            arguments = {}
        if tool_name != TOOL_NAME:
            _log_mcp_event("invalid-params", 400)
            return _error_response(
                400, INVALID_PARAMS, f"Unknown tool: {tool_name}", rpc_id
            )
        if arguments:
            _log_mcp_event("invalid-params", 400)
            return _error_response(
                400,
                INVALID_PARAMS,
                "Invalid params for tools/call: site.describe accepts no arguments.",
                rpc_id,
            )

    # Reuse the pure product capability format check before the fixed
    # dispatch: a structurally invalid token is refused here, without
    # consuming any upstream request quota.
    bearer = _extract_bearer(headers)
    if bearer is None or not validate_token_format(bearer):
        _log_mcp_event("unauthenticated", 401)
        return _unauthenticated("A product capability bearer is required.", rpc_id)

    upstream = request.app.state.mcp_upstream
    try:
        upstream_status, body = await upstream.bounded_get(bearer)
    except (OSError, http.client.HTTPException, ValueError):
        _log_mcp_event("upstream-failure", 503)
        return _error_response(503, INTERNAL_ERROR, "Upstream failure.", rpc_id)

    if upstream_status == 401:
        _log_mcp_event("unauthenticated", 401, upstream_status=401)
        return _unauthenticated(
            "Authentication refused by the product authority.", rpc_id
        )
    if upstream_status == 429:
        _log_mcp_event("quota-exceeded", 429, upstream_status=429)
        return _error_response(429, INVALID_REQUEST, "Request quota exceeded.", rpc_id)
    if upstream_status != 200:
        _log_mcp_event("upstream-failure", 503, upstream_status=upstream_status)
        return _error_response(503, INTERNAL_ERROR, "Upstream failure.", rpc_id)

    try:
        discovery = AgentDiscoveryResponse.model_validate_json(body)
    except (ValueError, UnicodeDecodeError, RecursionError):
        _log_mcp_event("upstream-failure", 503, upstream_status=200)
        return _error_response(
            503, INTERNAL_ERROR, "Invalid upstream response.", rpc_id
        )

    # The audit operation is a fixed server literal chosen in each
    # recognized result branch, so no caller-derived method text can
    # reach the log (closes CodeQL py/log-injection alert #13).
    if rpc_method == "server/discover":
        result = _discover_result()
        operation = "server/discover"
    elif rpc_method == "tools/list":
        result = _list_tools_result()
        operation = "tools/list"
    else:
        result = _call_tool_result(discovery.model_dump(mode="json"))
        operation = f"tools/call:{TOOL_NAME}"
    _log_mcp_event(
        operation,
        200,
        site_id=str(discovery.site_id),
        workspace_id=str(discovery.workspace_id),
        upstream_status=200,
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    return _result_response(rpc_id, result)


router = APIRouter()


@router.post("/")
async def mcp_post(request: Request) -> Response:
    """The single MCP endpoint (Streamable HTTP, JSON mode)."""
    return await _handle_mcp(request)


async def _reject_non_post(request: Request) -> Response:
    """Non-POST methods on the MCP endpoint (the GET stream endpoint was
    removed in 2026-07-28 and protocol-level sessions no longer exist)."""
    if request.headers.get("origin") is not None:
        _log_mcp_event("origin-refusal", 403)
        return _origin_refused()
    _log_mcp_event("method-not-allowed", 405)
    return _method_not_allowed()


@router.get("/")
async def mcp_get_not_supported(request: Request) -> Response:
    return await _reject_non_post(request)


@router.put("/")
async def mcp_put_not_supported(request: Request) -> Response:
    return await _reject_non_post(request)


@router.patch("/")
async def mcp_patch_not_supported(request: Request) -> Response:
    return await _reject_non_post(request)


@router.delete("/")
async def mcp_delete_not_supported(request: Request) -> Response:
    return await _reject_non_post(request)


@router.options("/")
async def mcp_options_not_supported(request: Request) -> Response:
    return await _reject_non_post(request)


def install_mcp_routes(
    app: FastAPI,
    *,
    upstream_base: str | None = None,
    upstream_timeout_seconds: float | None = None,
    max_upstream_concurrency: int | None = None,
) -> None:
    host, port = _validate_upstream_base(upstream_base or DEFAULT_UPSTREAM_BASE)
    timeout = (
        upstream_timeout_seconds
        if upstream_timeout_seconds is not None
        else DEFAULT_UPSTREAM_TIMEOUT_SECONDS
    )
    if not 0.05 <= timeout <= 300.0:
        raise ValueError("the MCP upstream timeout is out of bounds")
    concurrency = (
        max_upstream_concurrency
        if max_upstream_concurrency is not None
        else DEFAULT_MAX_UPSTREAM_CONCURRENCY
    )
    if not 1 <= concurrency <= 128:
        raise ValueError("the MCP upstream concurrency is out of bounds")
    app.state.mcp_upstream = McpUpstream(
        host=host,
        port=port,
        timeout_seconds=timeout,
        semaphore=asyncio.Semaphore(concurrency),
    )
    app.include_router(router)


__all__ = [
    "DEFAULT_MAX_UPSTREAM_CONCURRENCY",
    "DEFAULT_UPSTREAM_BASE",
    "DEFAULT_UPSTREAM_TIMEOUT_SECONDS",
    "PROTOCOL_VERSION",
    "SUPPORTED_VERSIONS",
    "TOOL_NAME",
    "install_mcp_routes",
    "router",
]

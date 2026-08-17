"""Request and trace correlation without trusting product-context headers."""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar
from typing import cast

from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = b"x-request-id"
REQUEST_ID_HEADER_NAME = "X-Request-ID"
MAX_CORRELATION_ID_LENGTH = 64
_SAFE_CALLER_ID = re.compile(rb"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def current_request_id() -> str | None:
    return _request_id.get()


def current_trace_id() -> str | None:
    return _trace_id.get()


def _generated_identifier(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _caller_request_id(scope: Scope) -> str | None:
    headers = cast(list[tuple[bytes, bytes]], scope.get("headers", []))
    values = [value for name, value in headers if name.lower() == REQUEST_ID_HEADER]
    if len(values) != 1:
        return None
    value = values[0]
    if len(value) <= MAX_CORRELATION_ID_LENGTH and _SAFE_CALLER_ID.fullmatch(value):
        return value.decode("ascii")
    return None


class CorrelationMiddleware:
    """Pure ASGI middleware that scopes and always resets correlation context."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _caller_request_id(scope) or _generated_identifier("req")
        trace_id = _generated_identifier("trace")
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        state["trace_id"] = trace_id
        request_token = _request_id.set(request_id)
        trace_token = _trace_id.set(trace_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != REQUEST_ID_HEADER
                ]
                headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            _trace_id.reset(trace_token)
            _request_id.reset(request_token)


__all__ = [
    "CorrelationMiddleware",
    "MAX_CORRELATION_ID_LENGTH",
    "REQUEST_ID_HEADER_NAME",
    "current_request_id",
    "current_trace_id",
]

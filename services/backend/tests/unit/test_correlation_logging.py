"""Concurrent correlation context and recursive log redaction contracts."""

from __future__ import annotations

import asyncio
import json
import logging
import sys

import httpx
from fastapi import Request
from slaif_agent_site.agent_api import create_app
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.correlation import current_request_id, current_trace_id
from slaif_agent_site.logging import JsonLogFormatter, redact_log_value


async def test_request_id_validation_generation_echo_and_context_reset() -> None:
    app = create_app(settings=ServiceSettings.for_test())

    @app.get("/test/observe/{delay}")
    async def observe(
        delay: float, request: Request
    ) -> dict[str, str | list[str] | None]:
        before_request = current_request_id()
        before_trace = current_trace_id()
        await asyncio.sleep(delay)
        assert current_request_id() == before_request
        assert current_trace_id() == before_trace
        return {
            "request_id": before_request,
            "trace_id": before_trace,
            "state_keys": sorted(request.scope["state"]),
        }

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        first, second = await asyncio.gather(
            client.get(
                "/test/observe/0.02",
                headers={
                    "X-Request-ID": "caller-safe-1",
                    "X-Trace-ID": "caller-trace-must-not-be-trusted",
                    "X-Site-ID": "caller-site-must-not-be-trusted",
                    "X-Workspace-ID": "caller-workspace-must-not-be-trusted",
                    "X-Operation-ID": "caller-operation-must-not-be-trusted",
                },
            ),
            client.get("/test/observe/0", headers={"X-Request-ID": "caller-safe-2"}),
        )
        invalid = await client.get(
            "/test/observe/0", headers={"X-Request-ID": "invalid request id"}
        )
        duplicate = await client.get(
            "/test/observe/0",
            headers=[
                ("X-Request-ID", "caller-safe-1"),
                ("X-Request-ID", "caller-safe-2"),
            ],
        )
        overlong = await client.get(
            "/test/observe/0", headers={"X-Request-ID": "a" * 65}
        )

    assert first.json()["request_id"] == "caller-safe-1"
    assert second.json()["request_id"] == "caller-safe-2"
    assert first.headers["X-Request-ID"] == "caller-safe-1"
    assert first.json()["trace_id"].startswith("trace_")
    assert first.json()["trace_id"] != "caller-trace-must-not-be-trusted"
    assert first.json()["trace_id"] != second.json()["trace_id"]
    assert invalid.json()["request_id"].startswith("req_")
    assert duplicate.json()["request_id"].startswith("req_")
    assert overlong.json()["request_id"].startswith("req_")
    assert first.json()["state_keys"] == ["request_id", "trace_id"]
    assert "X-Site-ID" not in first.headers
    assert "X-Workspace-ID" not in first.headers
    assert "X-Operation-ID" not in first.headers
    assert current_request_id() is None
    assert current_trace_id() is None


def test_recursive_redaction_and_bounds() -> None:
    secret = "local-fixture-sensitive-value"
    value = {
        "authorization": f"Bearer {secret}",
        "nested": {
            "password": secret,
            "database_url": f"postgresql://user:{secret}@database/db",
            "safe": f"Bearer {secret}",
        },
        "items": [{"capability_token": secret}],
        "long": "x" * 4000,
    }
    result = redact_log_value(value)
    serialized = json.dumps(result)
    assert secret not in serialized
    assert "postgresql://" not in serialized
    assert "[REDACTED]" in serialized
    assert "[TRUNCATED]" in serialized


def test_every_sensitive_log_key_family_is_redacted() -> None:
    secret = "local-fixture-sensitive-value"
    keys = (
        "authorization",
        "cookie",
        "password",
        "secret",
        "token",
        "capability",
        "database_dsn",
        "session_id",
        "internal_credential",
        "request_body",
        "response_payload",
    )
    serialized = json.dumps(redact_log_value({key: secret for key in keys}))
    assert secret not in serialized
    assert serialized.count("[REDACTED]") == len(keys)


def test_capability_shaped_value_is_redacted_without_complex_matching() -> None:
    shaped_value = "sas2_public-fixture_secret-fixture-value"
    serialized = json.dumps(redact_log_value({"safe_key": shaped_value}))
    assert shaped_value not in serialized
    assert "[REDACTED_CAPABILITY]" in serialized


def test_json_formatter_excludes_exception_and_payload_details() -> None:
    secret = "local-fixture-sensitive-value"
    formatter = JsonLogFormatter("agent-api")
    try:
        raise RuntimeError(f"token={secret}")
    except RuntimeError:
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=f"authorization=Bearer {secret}",
            args=(),
            exc_info=sys.exc_info(),
        )
    record.event_fields = {
        "cookie": secret,
        "request_payload": {"password": secret},
        "safe": "bounded",
    }
    output = formatter.format(record)
    document = json.loads(output)
    assert secret not in output
    assert document["service"] == "agent-api"
    assert document["exception"] == "[REDACTED_EXCEPTION]"
    assert document["fields"]["cookie"] == "[REDACTED]"
    assert document["fields"]["request_payload"] == "[REDACTED]"

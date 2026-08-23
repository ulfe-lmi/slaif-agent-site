"""Server-owned Editor mutation envelope helpers."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from uuid import UUID

from fastapi import Request

from slaif_agent_site.content_model.service import ContentModelService
from slaif_agent_site.errors import ServiceUnavailableError

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{1,128}$")
UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    re.IGNORECASE,
)


async def request_mutation_digest(request: Request) -> tuple[str, str]:
    key = request.headers.get("Idempotency-Key")
    if key is None:
        raise ValueError("missing")
    if not IDEMPOTENCY_KEY_PATTERN.fullmatch(key):
        raise ValueError("invalid")
    body = await request.body()
    digest = hashlib.sha256(
        request.method.encode("ascii")
        + b"\0"
        + request.url.path.encode("utf-8")
        + b"\0"
        + body
    ).hexdigest()
    return key, digest


def response_payload(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    try:
        value = json.loads(body)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {"result": value}


def response_resource_id(
    request: Request, response_body: dict[str, Any], fallback: UUID
) -> UUID:
    for key in ("id", "workspace_id", "page_id", "site_id"):
        value = response_body.get(key)
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                pass
    matches = UUID_PATTERN.findall(request.url.path)
    if matches:
        return UUID(matches[-1])
    return fallback


def resource_type(request: Request) -> str:
    parts = [part for part in request.url.path.split("/") if part]
    try:
        index = parts.index("v1")
    except ValueError:
        return "editor"
    return "editor." + (parts[index + 1] if len(parts) > index + 1 else "resource")


def request_service(request: Request) -> ContentModelService:
    service = getattr(request.state, "content_model_service", None)
    if not isinstance(service, ContentModelService):
        raise ServiceUnavailableError()
    return service


__all__ = [
    "IDEMPOTENCY_KEY_PATTERN",
    "request_mutation_digest",
    "response_payload",
    "response_resource_id",
    "request_service",
    "resource_type",
]

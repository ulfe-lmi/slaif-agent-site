"""Bounded standard-library JSON logging with recursive redaction."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from .correlation import current_request_id, current_trace_id

type JSONScalar = str | int | float | bool | None
type JSONValue = JSONScalar | list[JSONValue] | dict[str, JSONValue]

REDACTED = "[REDACTED]"
MAX_LOG_STRING_LENGTH = 1024
MAX_LOG_COLLECTION_ITEMS = 64
MAX_LOG_DEPTH = 6

_SENSITIVE_KEY = re.compile(
    r"authorization|cookie|password|passwd|secret|token|capability|"
    r"database[_-]?(?:url|dsn)|session|internal[_-]?credential|credential"
    r"|(?:request|response)[_-]?(?:payload|body)|payload|body",
    re.IGNORECASE,
)
_KEY_VALUE_SECRET = re.compile(
    r"(?i)\b(authorization|cookie|password|passwd|secret|token|capability|"
    r"database[_-]?(?:url|dsn)|session|internal[_-]?credential|credential|"
    r"(?:request|response)[_-]?(?:payload|body)|payload|body)"
    r"\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\n,;]+)"
)
_BEARER = re.compile(r"(?i)\bbearer\s+[^\s,;]+")
_DATABASE_URL = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb|redis)://[^\s,;]+"
)
_CAPABILITY = re.compile(r"\bsas2_[A-Za-z0-9_-]{10,512}\b")


def sanitize_log_text(value: str) -> str:
    """Redact recognizable secret forms and bound one log string."""

    sanitized = _KEY_VALUE_SECRET.sub(
        lambda match: f"{match.group(1)}={REDACTED}", value
    )
    sanitized = _BEARER.sub(f"Bearer {REDACTED}", sanitized)
    sanitized = _DATABASE_URL.sub("[REDACTED_DATABASE_URL]", sanitized)
    sanitized = _CAPABILITY.sub("[REDACTED_CAPABILITY]", sanitized)
    if len(sanitized) > MAX_LOG_STRING_LENGTH:
        return sanitized[: MAX_LOG_STRING_LENGTH - 11] + "[TRUNCATED]"
    return sanitized


def redact_log_value(value: object, *, depth: int = 0) -> JSONValue:
    """Convert arbitrary structured data to bounded, redacted JSON values."""

    if depth >= MAX_LOG_DEPTH:
        return "[MAX_DEPTH]"
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return sanitize_log_text(value)
    if isinstance(value, Mapping):
        redacted: dict[str, JSONValue] = {}
        for index, (raw_key, item) in enumerate(value.items()):
            if index >= MAX_LOG_COLLECTION_ITEMS:
                redacted["_truncated"] = True
                break
            key = sanitize_log_text(str(raw_key))[:128]
            redacted[key] = (
                REDACTED
                if _SENSITIVE_KEY.search(key)
                else redact_log_value(item, depth=depth + 1)
            )
        return redacted
    if isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        items = list(value[:MAX_LOG_COLLECTION_ITEMS])
        redacted_items = [redact_log_value(item, depth=depth + 1) for item in items]
        if len(value) > MAX_LOG_COLLECTION_ITEMS:
            redacted_items.append("[TRUNCATED_ITEMS]")
        return redacted_items
    return f"[UNSUPPORTED:{type(value).__name__}]"


class JsonLogFormatter(logging.Formatter):
    """Emit one bounded JSON object without traceback or payload serialization."""

    def __init__(self, service: str) -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        try:
            message = record.getMessage()
        except Exception:
            message = "[UNFORMATTABLE_LOG_MESSAGE]"
        document: dict[str, JSONValue] = {
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "service": self.service,
            "level": record.levelname,
            "message": sanitize_log_text(message),
            "request_id": current_request_id(),
            "trace_id": current_trace_id(),
        }
        event_fields = record.__dict__.get("event_fields")
        if isinstance(event_fields, Mapping):
            sanitized_fields = redact_log_value(event_fields)
            if isinstance(sanitized_fields, dict):
                document["fields"] = sanitized_fields
        if record.exc_info is not None:
            document["exception"] = "[REDACTED_EXCEPTION]"
        return json.dumps(document, ensure_ascii=True, separators=(",", ":"))


def configure_json_logging(*, service: str, level: str) -> None:
    """Configure the process root logger only when an entrypoint is invoked."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter(service))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


__all__ = [
    "JSONValue",
    "JsonLogFormatter",
    "configure_json_logging",
    "redact_log_value",
    "sanitize_log_text",
]

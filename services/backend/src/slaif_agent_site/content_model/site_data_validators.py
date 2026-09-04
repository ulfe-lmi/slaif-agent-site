"""Shared validators for fixed locales, routes, navigation, redirects, and effects."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from ..sites.normalization import (
    SiteInputError,
    normalize_locale,
    normalize_request_path,
    path_is_reserved,
)

_EXECUTABLE_ROUTE_SUFFIXES = (
    ".asp",
    ".aspx",
    ".bash",
    ".cgi",
    ".dll",
    ".exe",
    ".jsp",
    ".jspx",
    ".php",
    ".pl",
    ".sh",
)


def validate_locale_tag(value: str) -> str:
    try:
        return normalize_locale(value)
    except SiteInputError:
        raise ValueError("invalid locale tag") from None


def validate_internal_route(value: str) -> str:
    try:
        normalized = normalize_request_path(value)
    except SiteInputError:
        raise ValueError("invalid route") from None
    if path_is_reserved(normalized):
        raise ValueError("reserved route")
    return normalized


def validate_external_url(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.netloc
        or parts.username is not None
        or parts.password is not None
        or parts.hostname is None
        or any(ch.isspace() or ord(ch) < 32 for ch in value)
    ):
        raise ValueError("unsafe external target")
    return value


def validate_target(kind: str, value: str) -> str:
    if kind == "PAGE":
        try:
            UUID(value)
        except (TypeError, ValueError):
            raise ValueError("page target must be UUID") from None
        return value
    if kind == "INTERNAL":
        return validate_internal_route(value)
    if kind == "EXTERNAL":
        return validate_external_url(value)
    raise ValueError("invalid target kind")


def validate_agent_target(kind: str, value: str) -> str:
    """Validate the stricter target grammar exposed by Agent navigation."""

    if kind == "EXTERNAL":
        value = validate_external_url(value)
        if urlsplit(value).scheme != "https":
            raise ValueError("Agent external targets must use HTTPS")
        return value
    return validate_target(kind, value)


def validate_redirect(source: str, target: str) -> tuple[str, str]:
    normalized_source = validate_redirect_source(source)
    normalized_target = validate_redirect_target(target)
    if normalized_target == normalized_source:
        raise ValueError("redirect loop")
    return normalized_source, normalized_target


def validate_redirect_source(value: str) -> str:
    if len(value.encode("utf-8")) > 512:
        raise ValueError("redirect source is too long")
    normalized = validate_internal_route(value)
    if normalized == "/":
        raise ValueError("redirect source cannot be root")
    if any(
        segment.endswith(_EXECUTABLE_ROUTE_SUFFIXES)
        for segment in normalized.split("/")
    ):
        raise ValueError("executable redirect source")
    return normalized


def validate_redirect_target(value: str) -> str:
    if len(value.encode("utf-8")) > 2048:
        raise ValueError("redirect target is too long")
    if value.startswith("/"):
        return validate_internal_route(value)
    normalized = validate_external_url(value)
    if urlsplit(normalized).scheme != "https":
        raise ValueError("redirect targets must use HTTPS")
    return normalized


def validate_redirect_graph(
    source: str, target: str, existing: Iterable[tuple[str, str]]
) -> None:
    """Reject a redirect that would create a self-loop or chained cycle."""

    routes = {route: destination for route, destination in existing if route != source}
    routes[source] = target
    cursor = source
    visited: set[str] = set()
    for _ in range(16):
        if cursor in visited:
            raise ValueError("redirect cycle")
        visited.add(cursor)
        destination = routes.get(cursor)
        if destination is None or not destination.startswith("/"):
            return
        cursor = destination
    raise ValueError("redirect chain exceeds bound")


def validate_side_effect(kind: str, payload: dict[str, Any]) -> None:
    if kind not in {"analytics_event", "cache_purge"}:
        raise ValueError("side effect kind is not allowlisted")
    try:
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        raise ValueError("side effect payload must be JSON") from None
    if len(encoded.encode("utf-8")) > 16_384:
        raise ValueError("side effect payload too large")
    if any(marker in encoded for marker in (";", "--", "/*", "*/")):
        raise ValueError("side effect payload contains executable content")


__all__ = [
    "validate_agent_target",
    "validate_external_url",
    "validate_internal_route",
    "validate_locale_tag",
    "validate_redirect",
    "validate_redirect_graph",
    "validate_redirect_source",
    "validate_redirect_target",
    "validate_side_effect",
    "validate_target",
]

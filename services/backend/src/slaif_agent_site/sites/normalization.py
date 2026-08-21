"""Deterministic trusted routing and site-profile normalization."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

SITE_KEY_MAX_LENGTH = 63
HOSTNAME_MAX_LENGTH = 253
PATH_PREFIX_MAX_LENGTH = 512
LOCALE_MAX_LENGTH = 35

RESERVED_TOP_LEVEL = frozenset(
    {
        "api",
        "admin",
        "agent",
        "control",
        "editor",
        "health",
        "internal",
        "login",
        "logout",
        "mcp",
        "media",
        "preview",
        "setup",
        "_next",
        "static",
    }
)
_SITE_KEY = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_DNS_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")
_PATH_SEGMENT = re.compile(r"[A-Za-z0-9._~-]+")
_LANGUAGE = re.compile(r"[A-Za-z]{2,3}")
_SCRIPT = re.compile(r"[A-Za-z]{4}")
_REGION = re.compile(r"(?:[A-Za-z]{2}|[0-9]{3})")
_VARIANT = re.compile(r"(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3})")


class SiteInputError(ValueError):
    """One public-safe failure for site/routing normalization."""

    def __init__(self) -> None:
        super().__init__("Invalid site routing input.")


@dataclass(frozen=True, slots=True)
class NormalizedAuthority:
    hostname: str
    port: int | None


def normalize_site_key(value: str) -> str:
    normalized = value.lower()
    if (
        not normalized.isascii()
        or len(normalized) > SITE_KEY_MAX_LENGTH
        or _SITE_KEY.fullmatch(normalized) is None
        or normalized in RESERVED_TOP_LEVEL
    ):
        raise SiteInputError()
    return normalized


def _ascii_hostname(value: str) -> str:
    if not value or any(character.isspace() for character in value):
        raise SiteInputError()
    if value.endswith(".."):
        raise SiteInputError()
    candidate = value[:-1] if value.endswith(".") else value
    try:
        normalized = candidate.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        raise SiteInputError() from None
    if not normalized or len(normalized) > HOSTNAME_MAX_LENGTH:
        raise SiteInputError()
    if normalized == "localhost":
        return normalized
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        pass
    else:
        raise SiteInputError()
    labels = normalized.split(".")
    if len(labels) < 2 or any(_DNS_LABEL.fullmatch(label) is None for label in labels):
        raise SiteInputError()
    return normalized


def normalize_hostname(value: str) -> str:
    if any(marker in value for marker in (":", "/", "@", "?", "#", "[", "]")):
        raise SiteInputError()
    return _ascii_hostname(value)


def normalize_authority(value: str) -> NormalizedAuthority:
    """Normalize a request Host authority while keeping port out of storage."""

    if any(marker in value for marker in ("/", "@", "?", "#", "[", "]")):
        raise SiteInputError()
    hostname = value
    port: int | None = None
    if ":" in value:
        if value.count(":") != 1:
            raise SiteInputError()
        hostname, port_text = value.rsplit(":", 1)
        if not port_text.isascii() or not port_text.isdigit():
            raise SiteInputError()
        port = int(port_text)
        if not 1 <= port <= 65535:
            raise SiteInputError()
    return NormalizedAuthority(_ascii_hostname(hostname), port)


def _split_path(value: str) -> list[str]:
    if (
        not value.startswith("/")
        or len(value) > PATH_PREFIX_MAX_LENGTH
        or any(marker in value for marker in ("?", "#", "\\", "%", "\x00"))
        or "//" in value
    ):
        raise SiteInputError()
    segments = value.split("/")[1:]
    if any(
        not segment
        or segment in {".", ".."}
        or _PATH_SEGMENT.fullmatch(segment) is None
        for segment in segments
    ):
        raise SiteInputError()
    return segments


def normalize_path_prefix(value: str) -> str:
    if value == "/":
        return value
    if value.endswith("/"):
        raise SiteInputError()
    segments = _split_path(value)
    normalized = "/" + "/".join(segment.lower() for segment in segments)
    if segments[0].lower() in RESERVED_TOP_LEVEL or segments[0].lower() == "s":
        raise SiteInputError()
    return normalized


def normalize_request_path(value: str) -> str:
    if value == "/":
        return value
    if value.endswith("/"):
        value = value[:-1]
    segments = _split_path(value)
    return "/" + "/".join(segment.lower() for segment in segments)


def normalize_locale(value: str) -> str:
    if not value or len(value) > LOCALE_MAX_LENGTH or "_" in value:
        raise SiteInputError()
    parts = value.split("-")
    if not parts or _LANGUAGE.fullmatch(parts[0]) is None:
        raise SiteInputError()
    normalized = [parts[0].lower()]
    index = 1
    if index < len(parts) and _SCRIPT.fullmatch(parts[index]):
        normalized.append(parts[index].title())
        index += 1
    if index < len(parts) and _REGION.fullmatch(parts[index]):
        part = parts[index]
        normalized.append(part.upper() if part.isalpha() else part)
        index += 1
    seen: set[str] = set()
    for part in parts[index:]:
        if _VARIANT.fullmatch(part) is None or part.lower() in seen:
            raise SiteInputError()
        seen.add(part.lower())
        normalized.append(part.lower())
    return "-".join(normalized)


def path_is_reserved(path: str) -> bool:
    if path == "/":
        return False
    return path.split("/", 2)[1].lower() in RESERVED_TOP_LEVEL


__all__ = [
    "HOSTNAME_MAX_LENGTH",
    "LOCALE_MAX_LENGTH",
    "PATH_PREFIX_MAX_LENGTH",
    "RESERVED_TOP_LEVEL",
    "SITE_KEY_MAX_LENGTH",
    "NormalizedAuthority",
    "SiteInputError",
    "normalize_authority",
    "normalize_hostname",
    "normalize_locale",
    "normalize_path_prefix",
    "normalize_request_path",
    "normalize_site_key",
    "path_is_reserved",
]

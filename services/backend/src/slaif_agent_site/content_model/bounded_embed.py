"""Versioned bounded-embed policy for the VideoEmbed and MapBlock components.

Pure syntactic allowlist (no I/O, no network, no URL fetching): the policy
can only decide whether a *structured* prop set is canonicalizable and build
the canonical embed URL from it.  Embed loading happens exclusively in the
end user's browser against the pinned provider endpoints, so there is no
server-side SSRF surface.  The policy never emits autoplay, marketing, or
tracking parameters, so autoplay is structurally impossible.

Strategy-recorded design decision (2026-09-19, OAP 078-8-a): the initial
video allowlist is the reduced-tracking embed endpoint of each provider
(``youtube-nocookie``, not ``youtube.com``; ``player.vimeo.com``); a
tracker-class embed (full ``youtube.com``, ad networks, analytics) may not
be added without a separate reviewed policy change.
"""

from __future__ import annotations

import re
from typing import Any

EMBED_POLICY_VERSION = "bounded-embed/v1"

TITLE_MAX_LENGTH = 120

# Reduced-tracking embed endpoints only (see module docstring).
VIDEO_PROVIDER_HOSTS: dict[str, str] = {
    "youtube-nocookie": "www.youtube-nocookie.com",
    "vimeo": "player.vimeo.com",
}
VIDEO_PROVIDER_ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "youtube-nocookie": re.compile(r"[A-Za-z0-9_-]{11}"),
    "vimeo": re.compile(r"[0-9]{6,}"),
}
VIDEO_PROVIDER_PATHS: dict[str, str] = {
    "youtube-nocookie": "/embed/{video_id}",
    "vimeo": "/video/{video_id}",
}

MAP_PROVIDER_HOST = "www.openstreetmap.org"
MAP_PROVIDER_PATH = "/export/embed.html"
MAP_LAYERS: tuple[str, ...] = ("mapnik", "cycle", "transport")
DEFAULT_MAP_LAYER = "mapnik"

BBOX_LONGITUDE_LIMIT = 180.0
BBOX_LATITUDE_LIMIT = 85.05112877

ERROR_PROVIDER_UNKNOWN = "embed.provider-unknown"
ERROR_VIDEO_ID_INVALID = "embed.video-id-invalid"
ERROR_TITLE_MISSING = "embed.title-missing"
ERROR_TITLE_TOO_LONG = "embed.title-too-long"
ERROR_BBOX_MISSING = "embed.bbox-missing"
ERROR_BBOX_OUT_OF_RANGE = "embed.bbox-out-of-range"
ERROR_BBOX_INVALID_ORDER = "embed.bbox-invalid-order"
ERROR_LAYER_UNKNOWN = "embed.layer-unknown"


def _title_error(title: Any) -> str | None:
    if not isinstance(title, str) or not title:
        return ERROR_TITLE_MISSING
    if len(title) > TITLE_MAX_LENGTH:
        return ERROR_TITLE_TOO_LONG
    return None


def canonical_video_embed(provider: str, video_id: str) -> str:
    """Build the canonical https embed URL for a validated provider/id pair.

    Raises ``ValueError`` for any input outside the allowlist; the public
    validators are the decision surface and this builder is only reached
    with already-validated (or defense-in-depth re-validated) values.
    """
    pattern = VIDEO_PROVIDER_ID_PATTERNS.get(provider)
    if pattern is None or not isinstance(video_id, str):
        raise ValueError("embed provider not allowlisted")
    if not pattern.fullmatch(video_id):
        raise ValueError("embed video id not canonical")
    host = VIDEO_PROVIDER_HOSTS[provider]
    path = VIDEO_PROVIDER_PATHS[provider].format(video_id=video_id)
    return f"https://{host}{path}"


def _format_coordinate(value: int | float) -> str:
    """Deterministic coordinate serialization (no exponent notation).

    Integer-valued coordinates serialize as integers; all other values use
    at most 10 fractional digits with trailing zeros stripped.  The rule is
    language-robust so the trusted renderer (TypeScript) can rebuild the
    identical canonical bytes from the same validated values.
    """
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    text = f"{value:.10f}".rstrip("0").rstrip(".")
    if text in ("", "-"):
        return "0"
    return text


def canonical_map_embed(
    bbox: dict[str, int | float], layer: str = DEFAULT_MAP_LAYER
) -> str:
    """Build the canonical https OpenStreetMap embed URL (sorted query keys)."""
    if layer not in MAP_LAYERS:
        raise ValueError("map layer not allowlisted")
    try:
        parts = [
            _format_coordinate(bbox["west"]),
            _format_coordinate(bbox["south"]),
            _format_coordinate(bbox["east"]),
            _format_coordinate(bbox["north"]),
        ]
    except (KeyError, TypeError) as error:
        raise ValueError("map bbox incomplete") from error
    query = {"bbox": ",".join(parts)}
    if layer != DEFAULT_MAP_LAYER:
        query["layer"] = layer
    rendered = "&".join(f"{key}={query[key]}" for key in sorted(query))
    return f"https://{MAP_PROVIDER_HOST}{MAP_PROVIDER_PATH}?{rendered}"


def validate_video_embed_props(props: Any) -> tuple[bool, str | None]:
    """Validate VideoEmbed props against the bounded-embed policy.

    Returns ``(True, None)`` or ``(False, key)`` where ``key`` is one of
    ``embed.provider-unknown``, ``embed.video-id-invalid``,
    ``embed.title-missing``, ``embed.title-too-long``.  Error keys are
    bounded constants and never echo user input.
    """
    if not isinstance(props, dict):
        return False, ERROR_PROVIDER_UNKNOWN
    provider = props.get("provider")
    if not isinstance(provider, str) or provider not in VIDEO_PROVIDER_HOSTS:
        return False, ERROR_PROVIDER_UNKNOWN
    video_id = props.get("video_id")
    pattern = VIDEO_PROVIDER_ID_PATTERNS[provider]
    if not isinstance(video_id, str) or not pattern.fullmatch(video_id):
        return False, ERROR_VIDEO_ID_INVALID
    title_error = _title_error(props.get("title"))
    if title_error is not None:
        return False, title_error
    return True, None


def validate_map_embed_props(props: Any) -> tuple[bool, str | None]:
    """Validate MapBlock props against the bounded-embed policy.

    Returns ``(True, None)`` or ``(False, key)`` where ``key`` is one of
    ``embed.bbox-missing``, ``embed.bbox-out-of-range``,
    ``embed.bbox-invalid-order``, ``embed.layer-unknown``,
    ``embed.title-missing``, ``embed.title-too-long``.  Error keys are
    bounded constants and never echo user input.
    """
    if not isinstance(props, dict):
        return False, ERROR_BBOX_MISSING
    bbox = props.get("bbox")
    if not isinstance(bbox, dict):
        return False, ERROR_BBOX_MISSING
    coordinates: dict[str, float] = {}
    for key, limit in (
        ("west", BBOX_LONGITUDE_LIMIT),
        ("east", BBOX_LONGITUDE_LIMIT),
        ("south", BBOX_LATITUDE_LIMIT),
        ("north", BBOX_LATITUDE_LIMIT),
    ):
        value = bbox.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, ERROR_BBOX_MISSING
        coordinates[key] = float(value)
        if abs(coordinates[key]) > limit:
            return False, ERROR_BBOX_OUT_OF_RANGE
    if coordinates["west"] >= coordinates["east"]:
        return False, ERROR_BBOX_INVALID_ORDER
    if coordinates["south"] >= coordinates["north"]:
        return False, ERROR_BBOX_INVALID_ORDER
    if "layer" in props:
        layer = props.get("layer")
        if not isinstance(layer, str) or layer not in MAP_LAYERS:
            return False, ERROR_LAYER_UNKNOWN
    title_error = _title_error(props.get("title"))
    if title_error is not None:
        return False, title_error
    return True, None


__all__ = [
    "BBOX_LATITUDE_LIMIT",
    "BBOX_LONGITUDE_LIMIT",
    "DEFAULT_MAP_LAYER",
    "EMBED_POLICY_VERSION",
    "ERROR_BBOX_INVALID_ORDER",
    "ERROR_BBOX_MISSING",
    "ERROR_BBOX_OUT_OF_RANGE",
    "ERROR_LAYER_UNKNOWN",
    "ERROR_PROVIDER_UNKNOWN",
    "ERROR_TITLE_MISSING",
    "ERROR_TITLE_TOO_LONG",
    "ERROR_VIDEO_ID_INVALID",
    "MAP_LAYERS",
    "MAP_PROVIDER_HOST",
    "MAP_PROVIDER_PATH",
    "TITLE_MAX_LENGTH",
    "VIDEO_PROVIDER_HOSTS",
    "canonical_map_embed",
    "canonical_video_embed",
    "validate_map_embed_props",
    "validate_video_embed_props",
]

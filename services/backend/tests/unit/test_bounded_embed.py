"""Byte-pinned contracts for the versioned bounded-embed policy (R1)."""

import pytest
from slaif_agent_site.content_model.bounded_embed import (
    EMBED_POLICY_VERSION,
    ERROR_BBOX_INVALID_ORDER,
    ERROR_BBOX_MISSING,
    ERROR_BBOX_OUT_OF_RANGE,
    ERROR_LAYER_UNKNOWN,
    ERROR_PROVIDER_UNKNOWN,
    ERROR_TITLE_MISSING,
    ERROR_TITLE_TOO_LONG,
    ERROR_VIDEO_ID_INVALID,
    MAP_LAYERS,
    TITLE_MAX_LENGTH,
    VIDEO_PROVIDER_HOSTS,
    canonical_map_embed,
    canonical_video_embed,
    validate_map_embed_props,
    validate_video_embed_props,
)

YOUTUBE_HOST = "www.youtube-nocookie.com"
VIMEO_HOST = "player.vimeo.com"
OSM_HOST = "www.openstreetmap.org"


def test_policy_version_and_allowlist_surface() -> None:
    assert EMBED_POLICY_VERSION == "bounded-embed/v1"
    # Reduced-tracking embed endpoints only: no full youtube.com, no ad
    # networks, no analytics, no other provider (strategy-recorded decision).
    assert VIDEO_PROVIDER_HOSTS == {
        "youtube-nocookie": YOUTUBE_HOST,
        "vimeo": VIMEO_HOST,
    }
    assert MAP_LAYERS == ("mapnik", "cyclemap", "transportmap")
    assert TITLE_MAX_LENGTH == 120


def test_canonical_video_embed_urls_are_byte_pinned() -> None:
    assert (
        canonical_video_embed("youtube-nocookie", "dQw4w9WgXcQ")
        == f"https://{YOUTUBE_HOST}/embed/dQw4w9WgXcQ"
    )
    assert canonical_video_embed("vimeo", "123456") == (
        f"https://{VIMEO_HOST}/video/123456"
    )
    # https only: never http, never a tracker-class host.
    for url in (
        canonical_video_embed("youtube-nocookie", "dQw4w9WgXcQ"),
        canonical_video_embed("vimeo", "123456"),
    ):
        assert url.startswith("https://")
        assert "www.youtube.com" not in url
        assert "evil.example" not in url
        assert "autoplay" not in url


def test_canonical_map_embed_urls_are_byte_pinned() -> None:
    base = {"west": -12.5, "south": 55, "east": -12.4, "north": 55.1}
    assert canonical_map_embed(base) == (
        f"https://{OSM_HOST}/export/embed.html?bbox=-12.5,55,-12.4,55.1"
    )
    assert canonical_map_embed(base, layer="mapnik") == (
        f"https://{OSM_HOST}/export/embed.html?bbox=-12.5,55,-12.4,55.1"
    )
    assert canonical_map_embed(base, layer="cyclemap") == (
        f"https://{OSM_HOST}/export/embed.html?bbox=-12.5,55,-12.4,55.1&layer=cyclemap"
    )
    assert canonical_map_embed(base, layer="transportmap") == (
        f"https://{OSM_HOST}/export/embed.html?bbox=-12.5,55,-12.4,55.1&layer=transportmap"
    )
    # Integer-valued coordinates serialize as integers; tiny values keep
    # fixed-point (no exponent notation).
    assert (
        canonical_map_embed({"west": -13, "south": 55, "east": -12, "north": 56})
        == f"https://{OSM_HOST}/export/embed.html?bbox=-13,55,-12,56"
    )
    assert (
        canonical_map_embed({"west": 0.00001, "south": 55, "east": 1.0, "north": 56})
        == f"https://{OSM_HOST}/export/embed.html?bbox=0.00001,55,1,56"
    )
    # No autoplay, marketing, or tracking parameters are ever emitted.
    for url in (
        canonical_map_embed(base),
        canonical_map_embed(base, layer="cyclemap"),
        canonical_map_embed(base, layer="transportmap"),
    ):
        assert url.startswith("https://")
        assert "autoplay" not in url


def test_valid_video_embed_props_pass() -> None:
    assert validate_video_embed_props(
        {"provider": "youtube-nocookie", "video_id": "dQw4w9WgXcQ", "title": "Talk"}
    ) == (True, None)
    assert validate_video_embed_props(
        {"provider": "vimeo", "video_id": "123456", "title": "Talk"}
    ) == (True, None)
    assert validate_video_embed_props(
        {
            "provider": "vimeo",
            "video_id": "123456",
            "title": "x" * TITLE_MAX_LENGTH,
        }
    ) == (True, None)
    # The vimeo id pattern is unbounded per policy; the catalog schema
    # separately bounds video_id length at 64 characters.
    assert validate_video_embed_props(
        {"provider": "vimeo", "video_id": "1" * 64, "title": "T"}
    ) == (True, None)


def test_valid_map_embed_props_pass() -> None:
    bbox = {"west": -12.5, "south": 55, "east": -12.4, "north": 55.1}
    assert validate_map_embed_props({"bbox": bbox, "title": "Map"}) == (True, None)
    assert validate_map_embed_props(
        {"bbox": bbox, "layer": "cyclemap", "title": "Map"}
    ) == (True, None)
    assert validate_map_embed_props(
        {"bbox": bbox, "layer": "transportmap", "title": "M"}
    ) == (True, None)
    # Boundary coordinates are inclusive; integer values are accepted.
    boundary = {
        "west": -180,
        "south": -85.05112877,
        "east": 180,
        "north": 85.05112877,
    }
    assert validate_map_embed_props({"bbox": boundary, "title": "World"}) == (
        True,
        None,
    )


@pytest.mark.parametrize(
    ("props", "key"),
    [
        (
            {"provider": "youtube", "video_id": "dQw4w9WgXcQ", "title": "T"},
            ERROR_PROVIDER_UNKNOWN,
        ),
        (
            {"provider": "youtube.com", "video_id": "dQw4w9WgXcQ", "title": "T"},
            ERROR_PROVIDER_UNKNOWN,
        ),
        (
            {"provider": "evil.example", "video_id": "dQw4w9WgXcQ", "title": "T"},
            ERROR_PROVIDER_UNKNOWN,
        ),
        (
            {"provider": "", "video_id": "dQw4w9WgXcQ", "title": "T"},
            ERROR_PROVIDER_UNKNOWN,
        ),
        (
            {"provider": 5, "video_id": "dQw4w9WgXcQ", "title": "T"},
            ERROR_PROVIDER_UNKNOWN,
        ),
        ({"video_id": "dQw4w9WgXcQ", "title": "T"}, ERROR_PROVIDER_UNKNOWN),
        ({"video_id": "dQw4w9WgXcQ"}, ERROR_PROVIDER_UNKNOWN),
        ({"provider": "youtube-nocookie", "title": "T"}, ERROR_VIDEO_ID_INVALID),
        (
            {"provider": "youtube-nocookie", "video_id": "abc", "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {"provider": "youtube-nocookie", "video_id": "dQw4w9WgXcQ0", "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {"provider": "youtube-nocookie", "video_id": "dQw4w9WgXc", "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {"provider": "youtube-nocookie", "video_id": 12345, "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {"provider": "youtube-nocookie", "video_id": None, "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        # Query injection on the id form.
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "dQw4w9WgXcQ?autoplay=1",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "dQw4w9WgXcQ&x=1",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        # Scheme and host substitution inside the id form.
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "javascript:alert(1)",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "data:text/html,x",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "file:///etc/passwd",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "http://evil.example/x",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {
                "provider": "youtube-nocookie",
                "video_id": "www.youtube.com/x",
                "title": "T",
            },
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {"provider": "vimeo", "video_id": "12345", "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        (
            {"provider": "vimeo", "video_id": "abcdef", "title": "T"},
            ERROR_VIDEO_ID_INVALID,
        ),
        ({"provider": "vimeo", "video_id": "123456", "title": ""}, ERROR_TITLE_MISSING),
        ({"provider": "vimeo", "video_id": "123456", "title": 7}, ERROR_TITLE_MISSING),
        ({"provider": "vimeo", "video_id": "123456"}, ERROR_TITLE_MISSING),
        (
            {
                "provider": "vimeo",
                "video_id": "123456",
                "title": "x" * (TITLE_MAX_LENGTH + 1),
            },
            ERROR_TITLE_TOO_LONG,
        ),
        # Check order: provider before video_id before title.
        ({"provider": "evil", "video_id": "bad", "title": ""}, ERROR_PROVIDER_UNKNOWN),
        ({"provider": "vimeo", "video_id": "abc", "title": ""}, ERROR_VIDEO_ID_INVALID),
    ],
)
def test_video_embed_rejections_carry_exact_keys(
    props: dict[str, object], key: str
) -> None:
    assert validate_video_embed_props(props) == (False, key)


def test_video_embed_builder_rejects_non_canonical_input() -> None:
    with pytest.raises(ValueError):
        canonical_video_embed("youtube-nocookie", "bad id")
    with pytest.raises(ValueError):
        canonical_video_embed("evil.example", "dQw4w9WgXcQ")


def _bbox(**overrides: object) -> dict[str, object]:
    bbox: dict[str, object] = {"west": -12.5, "south": 55, "east": -12.4, "north": 55.1}
    bbox.update(overrides)
    return bbox


@pytest.mark.parametrize(
    ("props", "key"),
    [
        ({"title": "T"}, ERROR_BBOX_MISSING),
        ({"bbox": "west,south,east,north", "title": "T"}, ERROR_BBOX_MISSING),
        ({"bbox": None, "title": "T"}, ERROR_BBOX_MISSING),
        (
            {"bbox": {"west": -12.5, "south": 55, "east": -12.4}, "title": "T"},
            ERROR_BBOX_MISSING,
        ),
        (
            {
                "bbox": {"west": -12.5, "south": 55, "east": -12.4, "north": None},
                "title": "T",
            },
            ERROR_BBOX_MISSING,
        ),
        (
            {
                "bbox": {"west": -12.5, "south": "55", "east": -12.4, "north": 55.1},
                "title": "T",
            },
            ERROR_BBOX_MISSING,
        ),
        (
            {
                "bbox": {"west": -12.5, "south": True, "east": -12.4, "north": 55.1},
                "title": "T",
            },
            ERROR_BBOX_MISSING,
        ),
        ({"bbox": _bbox(west=180.00000001), "title": "T"}, ERROR_BBOX_OUT_OF_RANGE),
        ({"bbox": _bbox(west=-181), "title": "T"}, ERROR_BBOX_OUT_OF_RANGE),
        ({"bbox": _bbox(east=180.5), "title": "T"}, ERROR_BBOX_OUT_OF_RANGE),
        ({"bbox": _bbox(south=-85.05112878), "title": "T"}, ERROR_BBOX_OUT_OF_RANGE),
        ({"bbox": _bbox(north=85.05112878), "title": "T"}, ERROR_BBOX_OUT_OF_RANGE),
        ({"bbox": _bbox(west=-12.4), "title": "T"}, ERROR_BBOX_INVALID_ORDER),
        ({"bbox": _bbox(west=55), "title": "T"}, ERROR_BBOX_INVALID_ORDER),
        ({"bbox": _bbox(north=55), "title": "T"}, ERROR_BBOX_INVALID_ORDER),
        ({"bbox": _bbox(south=55.2), "title": "T"}, ERROR_BBOX_INVALID_ORDER),
        ({"bbox": _bbox(), "layer": "satellite", "title": "T"}, ERROR_LAYER_UNKNOWN),
        ({"bbox": _bbox(), "layer": "Mapnik", "title": "T"}, ERROR_LAYER_UNKNOWN),
        ({"bbox": _bbox(), "layer": 5, "title": "T"}, ERROR_LAYER_UNKNOWN),
        (
            {"bbox": _bbox(), "layer": "https://evil.example", "title": "T"},
            ERROR_LAYER_UNKNOWN,
        ),
        # Legacy provider identifiers are rejected fail-closed: the live OSM
        # embed endpoint silently falls back to mapnik for them, so the
        # product contract must not emit them (078/9 contract repair).
        ({"bbox": _bbox(), "layer": "cycle", "title": "T"}, ERROR_LAYER_UNKNOWN),
        ({"bbox": _bbox(), "layer": "transport", "title": "T"}, ERROR_LAYER_UNKNOWN),
        ({"bbox": _bbox()}, ERROR_TITLE_MISSING),
        ({"bbox": _bbox(), "title": ""}, ERROR_TITLE_MISSING),
        (
            {"bbox": _bbox(), "title": "x" * (TITLE_MAX_LENGTH + 1)},
            ERROR_TITLE_TOO_LONG,
        ),
        # Check order: range before order before layer before title.
        (
            {"bbox": _bbox(west=181, east=-181), "layer": "nope", "title": ""},
            ERROR_BBOX_OUT_OF_RANGE,
        ),
        (
            {"bbox": _bbox(west=55), "layer": "nope", "title": ""},
            ERROR_BBOX_INVALID_ORDER,
        ),
        ({"bbox": _bbox(), "layer": "nope", "title": ""}, ERROR_LAYER_UNKNOWN),
    ],
)
def test_map_embed_rejections_carry_exact_keys(
    props: dict[str, object], key: str
) -> None:
    assert validate_map_embed_props(props) == (False, key)


def test_map_embed_builder_rejects_non_canonical_input() -> None:
    with pytest.raises(ValueError):
        canonical_map_embed({"west": -1, "south": -1, "east": 1}, layer="mapnik")
    with pytest.raises(ValueError):
        canonical_map_embed(
            {"west": -1, "south": -1, "east": 1, "north": 1}, layer="satellite"
        )

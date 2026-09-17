"""Typed site-global region contract validation evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

import pytest
from slaif_agent_site.content_model.region_models import (
    MAX_EXTERNAL_TARGET_LENGTH,
    MAX_HEADER_NAV_ENTRIES,
    AgentUpdateGlobalRegionRequest,
    GlobalRegionContent,
    GlobalRegionRecord,
    RegionEntry,
    RegionTarget,
    UpdateGlobalRegionRequest,
    global_region_content_json,
    global_region_record_from_row,
    validate_region_label,
    validate_region_target,
)

_PAGE_ID = "0d7f4a1e-9b2c-4e6a-8f1d-3c5b7a9e2d40"


def _entry(
    label: str = "Home",
    kind: Literal["page", "internal", "external"] = "internal",
    value: str = "/",
) -> RegionEntry:
    return RegionEntry(label=label, target=RegionTarget(kind=kind, value=value))


def test_valid_targets_pass_their_closed_bounds() -> None:
    assert validate_region_target("page", _PAGE_ID) == _PAGE_ID
    assert validate_region_target("internal", "/") == "/"
    assert (
        validate_region_target("internal", "/news/2026/09/item") == "/news/2026/09/item"
    )
    assert validate_region_target("external", "https://example.org/docs") == (
        "https://example.org/docs"
    )
    assert validate_region_target(
        "external", "https://example.org/" + "a" * (MAX_EXTERNAL_TARGET_LENGTH - 20)
    )
    assert validate_region_label("  x".strip()) == "x"
    assert validate_region_label("x" * 256) == "x" * 256


@pytest.mark.parametrize(
    ("kind", "value"),
    [
        ("page", "not-a-uuid"),
        ("page", _PAGE_ID.upper()),
        ("internal", "/News"),
        ("internal", "news"),
        ("internal", "/a//b"),
        ("internal", "/a/../b"),
        ("internal", "/a%2Fb"),
        ("internal", "/api/x"),
        ("internal", "/admin"),
        ("internal", "/preview/x"),
        ("internal", "/_next/static/x"),
        ("internal", "/" + "a" * 257),
        ("external", "https://user:pass@example.com/"),
        ("external", "ftp://example.com/file"),
        ("external", "javascript:alert(1)"),
        ("external", "https://ex.com/a b"),
        ("external", "https://ex.com/" + "a" * 2034),
        ("external", ""),
    ],
)
def test_targets_reject_out_of_bound_values(kind: str, value: str) -> None:
    with pytest.raises(ValueError):
        validate_region_target(kind, value)  # type: ignore[arg-type]


@pytest.mark.parametrize("label", ["", " x", "x ", "x" * 257])
def test_labels_reject_padding_or_overflow(label: str) -> None:
    with pytest.raises(ValueError):
        validate_region_label(label)


def test_header_content_shape_is_exact_and_bounded() -> None:
    content = GlobalRegionContent(nav=(_entry(),))
    assert content.is_header()
    assert content.document() == {
        "nav": [{"label": "Home", "target": {"kind": "internal", "value": "/"}}]
    }
    with pytest.raises(ValueError):
        GlobalRegionContent(nav=())
    with pytest.raises(ValueError):
        GlobalRegionContent(
            nav=tuple(_entry() for _ in range(MAX_HEADER_NAV_ENTRIES + 1))
        )
    with pytest.raises(ValueError):
        GlobalRegionContent(nav=(_entry(),), note="nope")
    with pytest.raises(ValueError):
        GlobalRegionContent(nav=(_entry(),), links=())


def test_footer_content_shape_allows_empty_links_and_note() -> None:
    content = GlobalRegionContent(links=())
    assert not content.is_header()
    assert content.document() == {"links": []}
    with_note = GlobalRegionContent(links=(), note="x" * 4096)
    assert with_note.document()["note"] == "x" * 4096
    with pytest.raises(ValueError):
        GlobalRegionContent(note="no links list")
    with pytest.raises(ValueError):
        GlobalRegionContent(links=(), note="x" * 4097)
    with pytest.raises(ValueError):
        GlobalRegionContent(nav=(_entry(),), links=())


def test_page_and_external_entries_are_accepted() -> None:
    entry = _entry("About", "page", _PAGE_ID)
    assert entry.target.kind == "page"
    external = _entry("Docs", "external", "https://example.org/docs")
    assert external.target.value.startswith("https://")
    with pytest.raises(ValueError):
        RegionEntry(label="About", target=RegionTarget(kind="internal", value="/api/x"))


def test_content_document_enforces_the_16kib_bound() -> None:
    footer = GlobalRegionContent(
        links=tuple(_entry("x" * 256) for _ in range(16)), note="y" * 4096
    )
    serialized = global_region_content_json(footer)
    assert serialized is not None
    assert len(serialized.encode("utf-8")) <= 16 * 1024
    assert footer.document() == {
        "links": [{"label": "x" * 256, "target": {"kind": "internal", "value": "/"}}]
        * 16,
        "note": "y" * 4096,
    }
    header = GlobalRegionContent(
        nav=tuple(
            _entry("x" * 256, "external", "https://example.org/" + "a" * 2011)
            for _ in range(12)
        )
    )
    # Every field is individually within its bound, but the serialized
    # document exceeds the 16 KiB storage bound, so it must be rejected.
    with pytest.raises(ValueError, match="16 KiB"):
        header.document()


def test_update_requests_require_at_least_one_field() -> None:
    with pytest.raises(ValueError):
        UpdateGlobalRegionRequest()
    with pytest.raises(ValueError):
        UpdateGlobalRegionRequest(expected_row_version=3)
    assert UpdateGlobalRegionRequest(variant="minimal").variant == "minimal"
    assert (
        UpdateGlobalRegionRequest(content=GlobalRegionContent(links=())).content
        is not None
    )
    with pytest.raises(ValueError):
        UpdateGlobalRegionRequest(variant="bogus")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        AgentUpdateGlobalRegionRequest(variant="minimal")  # type: ignore[call-arg]
    agent = AgentUpdateGlobalRegionRequest(variant="minimal", expected_row_version=2)
    assert agent.expected_row_version == 2
    with pytest.raises(ValueError):
        AgentUpdateGlobalRegionRequest(variant="minimal", expected_row_version=0)


def _record_row(
    region_key: str, variant: str, content: dict[str, object]
) -> tuple[object, ...]:
    return (
        uuid4(),
        uuid4(),
        region_key,
        variant,
        content,
        "global-region/v1",
        1,
        datetime.now(UTC),
        datetime.now(UTC),
    )


def test_record_rows_must_match_key_variant_and_shape() -> None:
    row = _record_row(
        "header",
        "institutional",
        {"nav": [{"label": "H", "target": {"kind": "internal", "value": "/"}}]},
    )
    record = global_region_record_from_row(row)
    assert isinstance(record, GlobalRegionRecord)
    assert record.region_key == "header"
    assert record.content.is_header()
    with pytest.raises(ValueError):
        global_region_record_from_row(
            _record_row(
                "header",
                "multi-column",
                {"nav": [{"label": "H", "target": {"kind": "internal", "value": "/"}}]},
            )
        )
    with pytest.raises(ValueError):
        global_region_record_from_row(
            _record_row(
                "footer",
                "single-column",
                {"nav": [{"label": "H", "target": {"kind": "internal", "value": "/"}}]},
            )
        )
    with pytest.raises(ValueError):
        global_region_record_from_row(row[:8])


def test_string_jsonb_rows_are_decoded() -> None:
    row = _record_row("footer", "single-column", {"links": [], "note": ""})
    string_row = (*row[:4], '{"links": [], "note": ""}', *row[5:])
    record = global_region_record_from_row(string_row)
    assert record.content.links == ()
    assert record.content.note == ""
    assert isinstance(record.id, UUID)

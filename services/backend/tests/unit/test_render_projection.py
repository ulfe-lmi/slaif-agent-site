"""Pure projection and service-auth boundary tests."""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Callable, Iterator, Mapping
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from slaif_agent_site.content_model.canonical import canonical_digest
from slaif_agent_site.render_api import frozen_source as fs
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    RenderProjectionService,
    _node_tree,
    _route_parts,
)
from slaif_agent_site.review_worker.snapshot import (
    STATE_VERSION,
    build_snapshot_document,
)
from slaif_agent_site.sites.models import SiteContext

SITE_ID = UUID("11111111-1111-4111-8111-111111111111")


def _context(prefix: str = "/docs") -> SiteContext:
    return SiteContext._from_database(
        (SITE_ID, "docs", "ACTIVE", 3, "en", "example.test", prefix)
    )


def test_projection_route_is_site_prefix_confined() -> None:
    locales = [(uuid4(), SITE_ID, "en", True, True)]
    assert _route_parts(_context(), "/docs/about/", None, locales) == (
        "/about",
        "en",
    )
    assert _route_parts(_context("/"), "/about", None, locales) == (
        "/about",
        "en",
    )
    with pytest.raises(ProjectionError):
        _route_parts(_context(), "/docs-other/about", None, locales)


def test_projection_tree_rejects_unknown_or_dangerous_nodes() -> None:
    with pytest.raises(ProjectionError, match="unknown_component"):
        _node_tree(
            [
                (
                    UUID("22222222-2222-4222-8222-222222222222"),
                    SITE_ID,
                    UUID("33333333-3333-4333-8333-333333333333"),
                    "Unknown",
                    "1",
                    None,
                    "default",
                    0,
                    {},
                )
            ],
            page_id=UUID("33333333-3333-4333-8333-333333333333"),
            site_id=SITE_ID,
        )


def _node(
    component_type: str,
    *,
    node_id: str,
    parent_id: UUID | None = None,
    slot: str = "default",
    props: dict[str, Any] | None = None,
) -> tuple[object, ...]:
    return (
        UUID(node_id),
        SITE_ID,
        UUID("33333333-3333-4333-8333-333333333333"),
        component_type,
        "1",
        parent_id,
        slot,
        0,
        props or {},
    )


def test_projection_tree_uses_parent_slots_and_full_prop_schema() -> None:
    hero_id = UUID("22222222-2222-4222-8222-222222222222")
    heading_id = UUID("44444444-4444-4444-8444-444444444444")
    roots = _node_tree(
        [
            _node(
                "Hero",
                node_id=str(hero_id),
                props={"heading": "Hero", "subheading": "Intro"},
            ),
            _node(
                "Heading",
                node_id=str(heading_id),
                parent_id=hero_id,
                slot="content",
                props={"text": "Nested", "level": 2},
            ),
        ],
        page_id=UUID("33333333-3333-4333-8333-333333333333"),
        site_id=SITE_ID,
    )
    assert roots[0].children[0].id == heading_id

    with pytest.raises(ProjectionError, match="invalid_slot"):
        _node_tree(
            [
                _node(
                    "Hero",
                    node_id=str(hero_id),
                    props={"heading": "Hero"},
                ),
                _node(
                    "Heading",
                    node_id=str(heading_id),
                    parent_id=hero_id,
                    props={"text": "Wrong slot", "level": 2},
                ),
            ],
            page_id=UUID("33333333-3333-4333-8333-333333333333"),
            site_id=SITE_ID,
        )

    with pytest.raises(ProjectionError, match="missing_prop"):
        _node_tree(
            [_node("Heading", node_id=str(heading_id), props={"text": "No level"})],
            page_id=UUID("33333333-3333-4333-8333-333333333333"),
            site_id=SITE_ID,
        )
    with pytest.raises(ProjectionError, match="unsafe_value"):
        _node_tree(
            [
                _node(
                    "Button",
                    node_id=str(heading_id),
                    props={"label": "External", "href": "https://evil.test"},
                )
            ],
            page_id=UUID("33333333-3333-4333-8333-333333333333"),
            site_id=SITE_ID,
        )
    with pytest.raises(ProjectionError, match="executable_prop"):
        _node_tree(
            [
                (
                    UUID("22222222-2222-4222-8222-222222222222"),
                    SITE_ID,
                    UUID("33333333-3333-4333-8333-333333333333"),
                    "Heading",
                    "1",
                    None,
                    "default",
                    0,
                    {"dangerouslySetInnerHTML": "<script>"},
                )
            ],
            page_id=UUID("33333333-3333-4333-8333-333333333333"),
            site_id=SITE_ID,
        )


def test_projection_tree_accepts_only_bounded_design_responsive_values() -> None:
    valid = _node_tree(
        [
            _node(
                "Heading",
                node_id="44444444-4444-4444-8444-444444444444",
                props={
                    "text": "Responsive",
                    "level": 2,
                    "alignment": {"desktop": "start", "mobile": "center"},
                },
            )
        ],
        page_id=UUID("33333333-3333-4333-8333-333333333333"),
        site_id=SITE_ID,
    )
    assert valid[0].props["alignment"] == {
        "desktop": "start",
        "mobile": "center",
    }

    with pytest.raises(ProjectionError, match="prop_type"):
        _node_tree(
            [
                _node(
                    "Heading",
                    node_id="44444444-4444-4444-8444-444444444444",
                    props={
                        "text": "Unsafe",
                        "level": 2,
                        "alignment": {"desktop": "position:fixed"},
                    },
                )
            ],
            page_id=UUID("33333333-3333-4333-8333-333333333333"),
            site_id=SITE_ID,
        )


def test_preview_request_rejects_extra_authority_fields() -> None:
    with pytest.raises(ValueError):
        RenderPageRequest.model_validate(
            {"authority": "example.test", "path": "/", "workspace": "forged"}
        )


# ---------------------------------------------------------------------------
# Frozen v2 admission seam (R7/R8): permanent regressions.
#
# Rows are built with the real capture builder; malformations are applied
# AFTER construction (the builder rejects its own violations), with the
# exact canonical digest recomputed, so each case isolates the seam.
# ---------------------------------------------------------------------------

_FWS = str(UUID(int=1))
_FSITE = str(UUID(int=2))
_FSNA = str(UUID(int=3))
_FNOW = "2026-10-18T12:00:00+00:00"
_FOREIGN_SITE = str(UUID(int=96))
_ZERO_UUID = "00000000-0000-0000-0000-000000000000"

_FDOC: dict[str, Any] = {
    "state_version": STATE_VERSION,
    "workspace_id": _FWS,
    "site_id": _FSITE,
    "site": {
        "site_key": "parity",
        "display_name": "Parity Site",
        "status": "ACTIVE",
        "default_locale": "en",
        "component_catalog_version": "catalog-v1",
        "content_model_revision": 3,
        "created_at": _FNOW,
        "updated_at": _FNOW,
    },
    "base_site_revision": 7,
    "operation_watermark": 2,
    "workspace_versions": {
        "catalog": "catalog-v1",
        "composition_schema": "site-composition/v1",
        "content_model": "content-model/v1",
        "design_system": "design-system/v1",
        "puck": "0.20.2",
        "renderer": "renderer-v1",
    },
    "locales": [
        {
            "id": str(UUID(int=21)),
            "site_id": _FSITE,
            "tag": "en",
            "enabled": True,
            "is_default": True,
            "position": 0,
            "metadata": {},
            "row_version": 1,
            "created_at": _FNOW,
            "updated_at": _FNOW,
        }
    ],
    "theme": {
        "id": str(UUID(int=22)),
        "site_id": _FSITE,
        "schema_version": "1",
        "renderer_version": "renderer-v1",
        "row_version": 1,
        "palette": {"primary": "#123456"},
        "typography": {"base": 16},
        "layout": {"max_width": 1200},
        "shape": {"radius": 4},
        "created_at": _FNOW,
        "updated_at": _FNOW,
    },
    "regions": [],
    "navigation": {"definitions": [], "items": []},
    "redirects": [],
    "pages": [
        {
            "id": str(UUID(int=31)),
            "site_id": _FSITE,
            "slug": "home",
            "title": "Home",
            "status": "PUBLISHED",
            "locale": "en",
            "parent_id": None,
            "route_template": None,
            "effective_route": "/",
            "row_version": 1,
            "created_at": _FNOW,
            "updated_at": _FNOW,
            "deleted_at": None,
            "style_overrides": {},
            "style": None,
            "nodes": [],
        }
    ],
    "page_compositions": [
        {
            "id": str(UUID(int=41)),
            "site_id": _FSITE,
            "page_id": str(UUID(int=31)),
            "component_type": "Heading",
            "schema_version": "1",
            "parent_id": None,
            "slot_key": "default",
            "order_key": 0,
            "props": {"text": "Hello", "level": 1},
            "catalog_version": "catalog-v1",
            "created_at": _FNOW,
            "updated_at": _FNOW,
            "row_version": 1,
        }
    ],
    "content": {
        "types": [],
        "fields": [],
        "items": [],
        "translations": [],
        "relations": [],
        "views": [],
    },
    "proposals": [],
    "media_inventory": [],
    "media": {},
}


def _frow(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    built = build_snapshot_document(
        copy.deepcopy(doc if doc is not None else _FDOC),
        created_by="slaif_review_worker",
    )
    row = dict(built)
    row["workspace_id"] = _FWS
    row["site_id"] = _FSITE
    row["id"] = _FSNA
    row["created_at"] = _FNOW
    return row


def _fmutate_both(
    row: dict[str, Any], mutate: Callable[[dict[str, Any]], None]
) -> dict[str, Any]:
    mutate(row["payload"])
    if row["normalized_state"] is not row["payload"]:
        mutate(row["normalized_state"])
    return row


def _fseal(row: dict[str, Any]) -> dict[str, Any]:
    row["digest"] = canonical_digest(row["payload"])
    return row


def _fadmit(row: dict[str, Any]) -> None:
    fs.admit_frozen_snapshot(
        row,
        expected_snapshot_id=UUID(_FSNA),
        expected_site_id=UUID(_FSITE),
        expected_workspace_id=UUID(_FWS),
    )


def _frefuse(row: dict[str, Any]) -> None:
    with pytest.raises(fs.SurfaceReadError) as caught:
        _fadmit(row)
    assert caught.value.reason == "not_found"


def _frefuse_construction(row: dict[str, Any]) -> None:
    with pytest.raises(fs.SurfaceReadError) as caught:
        fs.FrozenRenderSurface(
            row,
            expected_snapshot_id=UUID(_FSNA),
            expected_site_id=UUID(_FSITE),
            expected_workspace_id=UUID(_FWS),
        )
    assert caught.value.reason == "not_found"


def test_frozen_admission_accepts_genuine_builder_row() -> None:
    row = _frow()
    _fadmit(row)
    surface = fs.FrozenRenderSurface(
        row,
        expected_snapshot_id=UUID(_FSNA),
        expected_site_id=UUID(_FSITE),
        expected_workspace_id=UUID(_FWS),
    )
    assert surface.base_site_revision == 7
    assert surface.site_key == "parity"
    assert surface.site_status == "ACTIVE"


def test_frozen_admission_refuses_foreign_site_deleted_tombstone() -> None:
    doc = copy.deepcopy(_FDOC)
    doc["pages"].append(
        {
            "id": str(UUID(int=32)),
            "site_id": _FSITE,
            "slug": "gone",
            "title": "Gone",
            "status": "PUBLISHED",
            "locale": "en",
            "parent_id": None,
            "route_template": None,
            "effective_route": "/gone",
            "row_version": 1,
            "created_at": _FNOW,
            "updated_at": _FNOW,
            "deleted_at": None,
            "style_overrides": {},
            "style": None,
            "nodes": [],
        }
    )
    row = _frow(doc)

    def mutate(state: dict[str, Any]) -> None:
        page = state["pages"][1]
        page["site_id"] = _FOREIGN_SITE
        page["deleted_at"] = _FNOW

    _fmutate_both(row, mutate)
    _fseal(row)
    _frefuse(row)
    _frefuse_construction(row)


def test_frozen_admission_refuses_divergent_normalized_state() -> None:
    row = _frow()
    # Isolated counterpart: the builder aliases normalized_state to the
    # payload, so the copy diverges on exactly one field while the row
    # digest still matches the untouched payload.
    row["normalized_state"] = copy.deepcopy(row["normalized_state"])
    row["normalized_state"]["base_site_revision"] = 8
    _frefuse(row)
    _frefuse_construction(row)


def test_frozen_admission_refuses_malformed_retained_scalars() -> None:
    def _slug_list(state: dict[str, Any]) -> None:
        page = state["pages"][0]
        page["deleted_at"] = _FNOW
        slug: object = 0
        for _ in range(42):  # the reported defect shape: text slug is a list
            slug = [slug]
        page["slug"] = slug

    def _slug_int(state: dict[str, Any]) -> None:
        page = state["pages"][0]
        page["deleted_at"] = _FNOW
        page["slug"] = 123

    def _proposal_state(state: dict[str, Any]) -> None:
        state["proposals"] = [
            {
                "id": str(UUID(int=76)),
                "site_id": _FSITE,
                "workspace_id": _FWS,
                "kind": "cache_purge",
                "payload": {"key": "k"},
                "state": "PROPOSED",
                "created_at": _FNOW,
                "updated_at": _FNOW,
            }
        ]
        state["proposals"][0]["state"] = 123  # never-projected family

    def _inventory_filename(state: dict[str, Any]) -> None:
        state["media_inventory"] = [
            {
                "id": str(UUID(int=77)),
                "site_id": _FSITE,
                "uploaded_by": None,
                "filename": "a.png",
                "mime_type": "image/png",
                "size_bytes": 12,
                "content_hash": "0" * 64,
                "storage_key": "s/a.png",
                "alt_text": "",
                "metadata": {},
                "created_at": _FNOW,
                "updated_at": _FNOW,
                "public_status": "private",
                "published_at": None,
            }
        ]
        state["media_inventory"][0]["filename"] = []  # never-projected family

    for mutator in (_slug_list, _slug_int, _proposal_state, _inventory_filename):
        row = _frow()
        _fmutate_both(row, mutator)
        _fseal(row)
        _frefuse(row)
        _frefuse_construction(row)


def test_frozen_admission_cross_page_style_refused_own_style_admitted() -> None:
    doc = copy.deepcopy(_FDOC)
    doc["pages"].append(
        {
            "id": str(UUID(int=30)),
            "site_id": _FSITE,
            "slug": "other",
            "title": "Other",
            "status": "PUBLISHED",
            "locale": "en",
            "parent_id": None,
            "route_template": None,
            "effective_route": "/other",
            "row_version": 1,
            "created_at": _FNOW,
            "updated_at": _FNOW,
            "deleted_at": None,
            "style_overrides": {},
            "style": None,
            "nodes": [],
        }
    )
    cross_style = {
        "id": str(UUID(int=45)),
        "page_id": str(UUID(int=31)),
        "site_id": _FSITE,
        "schema_version": "1",
        "row_version": 1,
        "overrides": {"c": "#fff"},
        "resolved": {"c": "#fff"},
        "created_at": _FNOW,
        "updated_at": _FNOW,
    }
    cross_doc = copy.deepcopy(doc)
    cross_doc["pages"][1]["style"] = copy.deepcopy(cross_style)
    _frefuse(_frow(cross_doc))

    own_doc = copy.deepcopy(doc)
    own_doc["pages"][1]["style"] = {
        **cross_style,
        "id": str(UUID(int=46)),
        "page_id": str(UUID(int=30)),
    }
    _fadmit(_frow(own_doc))


def test_frozen_admission_capture_order_menu_preserved() -> None:
    nav = str(UUID(int=70))

    def item(i: int, parent: int | None, pos: int) -> dict[str, Any]:
        return {
            "id": str(UUID(int=80 + i)),
            "site_id": _FSITE,
            "navigation_id": nav,
            "parent_id": str(UUID(int=80 + parent)) if parent is not None else None,
            "page_id": None,
            "target_kind": "INTERNAL",
            "target_value": f"/p{i}",
            "labels": {"en": f"I{i}"},
            "locale": None,
            "position": pos,
            "row_version": 1,
            "created_at": _FNOW,
            "updated_at": _FNOW,
            "parent_key": (
                str(UUID(int=80 + parent)) if parent is not None else _ZERO_UUID
            ),
        }

    doc = copy.deepcopy(_FDOC)
    doc["navigation"]["definitions"] = [
        {
            "id": nav,
            "site_id": _FSITE,
            "key": "main",
            "label": "Main",
            "settings": {},
            "created_at": _FNOW,
            "updated_at": _FNOW,
            "labels": {"en": "Main"},
            "row_version": 1,
        }
    ]
    # capture position order: the child (pos 0 under rootB) precedes
    # its parent rootB (pos 1)
    doc["navigation"]["items"] = [item(0, None, 0), item(2, 1, 0), item(1, None, 1)]
    row = _frow(doc)
    _fadmit(row)
    surface = fs.FrozenRenderSurface(
        row,
        expected_snapshot_id=UUID(_FSNA),
        expected_site_id=UUID(_FSITE),
        expected_workspace_id=UUID(_FWS),
    )
    items = asyncio.run(surface.fetch_navigation_items(site_id=UUID(_FSITE)))
    assert [i[0] for i in items] == [
        UUID(int=80),
        UUID(int=82),
        UUID(int=81),
    ]


def test_frozen_admission_depth_and_width_bounds() -> None:
    def chain(n: int) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        parent = None
        for i in range(n):
            last = i == n - 1
            node: dict[str, Any] = {
                "id": str(UUID(int=700 + i)),
                "site_id": _FSITE,
                "page_id": str(UUID(int=31)),
                "component_type": "RichText" if last else "Section",
                "schema_version": "1",
                "parent_id": parent,
                "slot_key": "default",
                "order_key": i,
                "props": (
                    {"content": {"type": "paragraph", "children": [{"text": "x"}]}}
                    if last
                    else {}
                ),
                "created_at": _FNOW,
                "updated_at": _FNOW,
            }
            if nodes:
                nodes[-1]["children"] = [node]
            else:
                node["children"] = []
            nodes.append(node)
            parent = node["id"]
        return nodes

    doc17 = copy.deepcopy(_FDOC)
    doc17["pages"][0]["nodes"] = chain(17)
    row17 = _frow(doc17)
    _fadmit(row17)  # genuine 17-node chain with a real RichText leaf

    row18 = copy.deepcopy(row17)

    def extend(state: dict[str, Any]) -> None:
        leaf = state["pages"][0]["nodes"][0]
        for _ in range(16):
            leaf = leaf["children"][0]
        leaf["children"] = [
            {
                "id": str(UUID(int=999)),
                "component_type": "Section",
                "schema_version": "1",
                "parent_id": str(UUID(int=516)),
                "slot_key": "default",
                "order_key": 17,
                "props": {},
                "children": [],
            }
        ]

    _fmutate_both(row18, extend)
    _fseal(row18)
    _frefuse(row18)
    _frefuse_construction(row18)

    # post-build malformation: whole-document depth 46 (the builder never
    # emits it); the seam refuses stably, no RecursionError.
    row46 = copy.deepcopy(row17)

    def deepen(state: dict[str, Any]) -> None:
        leaf = state["pages"][0]["nodes"][0]
        for _ in range(16):
            leaf = leaf["children"][0]
        for _ in range(5):
            leaf["props"] = {"w": leaf["props"]}

    _fmutate_both(row46, deepen)
    _fseal(row46)
    _frefuse(row46)
    _frefuse_construction(row46)

    # exact walker boundary, helper-only (crafted shapes, not full rows)
    def crafted(props_levels: int) -> dict[str, Any]:
        props: object = 0
        for _ in range(props_levels):
            props = {"n": props}
        node: dict[str, Any] = {"props": props, "children": []}
        for _ in range(16):
            node = {"props": {}, "children": [node]}
        return {"pages": [{"nodes": [node]}]}

    assert fs._raw_depth_ok(crafted(8), fs.MAX_WHOLE_DOCUMENT_RAW_DEPTH) is True
    assert fs._raw_depth_ok(crafted(9), fs.MAX_WHOLE_DOCUMENT_RAW_DEPTH) is False

    rowwide = _frow()

    def widen(state: dict[str, Any]) -> None:
        state["page_compositions"][0]["props"] = {
            f"k{i}": 1 for i in range(fs.MAX_SINGLE_VALUE_ELEMENT_COUNT + 1)
        }

    _fmutate_both(rowwide, widen)
    _fseal(rowwide)
    _frefuse(rowwide)
    _frefuse_construction(rowwide)


def test_frozen_admission_decimal_render_decode_and_raw_retention() -> None:
    doc = copy.deepcopy(_FDOC)
    doc["page_compositions"][0]["props"] = {
        "text": "N",
        "level": 1,
        "frac": Decimal("1.50"),
        "whole": Decimal("10000000000"),
        "negzero": Decimal("-0.00"),
    }
    row = _frow(doc)
    _fadmit(row)
    surface = fs.FrozenRenderSurface(
        row,
        expected_snapshot_id=UUID(_FSNA),
        expected_site_id=UUID(_FSITE),
        expected_workspace_id=UUID(_FWS),
    )
    compositions = asyncio.run(
        surface.fetch_composition(site_id=UUID(_FSITE), page_id=UUID(int=31))
    )
    props = compositions[0][8]
    assert props["frac"] == 1.5 and isinstance(props["frac"], float)
    assert props["whole"] == 10000000000 and isinstance(props["whole"], int)
    assert props["negzero"] == 0.0 and isinstance(props["negzero"], float)
    raw = row["payload"]["page_compositions"][0]["props"]
    assert raw["frac"] == Decimal("1.50")
    assert raw["whole"] == Decimal("10000000000")
    assert raw["negzero"] == Decimal("-0.00")


# ---------------------------------------------------------------------------
# Shared route/navigation/ancestor port regressions.  The effective
# semantics are the 050 route body, 056 winner selection, 057 PAGE
# validator, 059 locale-neutral navigation and 067 ancestor chain
# (049/052 are immutable initial creates).  These pin the helper
# behavior the differential integration proof starts from, plus the
# per-request route memo's R8 total-work bound and failure hygiene.
# ---------------------------------------------------------------------------


def _pfact(
    slug: str,
    *,
    parent: fs.RenderPageFact | None = None,
    template: str | None = None,
    status: str = "PUBLISHED",
    locale: str = "en",
) -> fs.RenderPageFact:
    return fs.RenderPageFact(
        id=uuid4(),
        site_id=SITE_ID,
        slug=slug,
        title=f"title-{slug}",
        status=status,
        locale=locale,
        parent_id=parent.id if parent else None,
        route_template=template,
        row_version=1,
    )


def _pfacts(*facts: fs.RenderPageFact) -> dict[UUID, fs.RenderPageFact]:
    return {f.id: f for f in facts}


def _pnitem(
    kind: str,
    target_value: str,
    *,
    page_id: UUID | None = None,
    locale: str | None = None,
    position: int = 1,
) -> fs.NavigationItemRawRow:
    return (
        uuid4(),
        SITE_ID,
        uuid4(),
        None,
        page_id,
        kind,
        target_value,
        {},
        locale,
        position,
    )


def _pnavigate(
    facts: Mapping[UUID, fs.RenderPageFact],
    items: list[fs.NavigationItemRawRow],
    memo: fs._RouteMemo | None = None,
) -> tuple[fs.NavigationItemRow, ...]:
    return fs.navigation_resolved_items(
        facts,
        frozenset({"en"}),
        items,
        site_id=SITE_ID,
        locale="en",
        default_locale="en",
        statuses=("PUBLISHED",),
        route_memo=memo,
    )


def _presolve(
    facts: Mapping[UUID, fs.RenderPageFact],
    route: str,
    memo: fs._RouteMemo | None = None,
) -> fs.RenderPageFact | None:
    return fs.resolve_page_route(
        facts,
        site_id=SITE_ID,
        route=route,
        locale="en",
        statuses=("PUBLISHED",),
        default_locale="en",
        enabled_tags=frozenset({"en"}),
        route_memo=memo,
    )


def test_port_route_shape_rejected_before_candidates() -> None:
    dynamic = _pfact("item", template="{slug}")
    facts = _pfacts(dynamic)
    # positive control: a valid dynamic slug resolves
    assert _presolve(facts, "/valid-item") is dynamic
    # the effective 056 rejects these request shapes up front: zero rows
    assert _presolve(facts, "/a..b") is None
    assert _presolve(facts, "//x") is None
    assert _presolve(facts, "/x%20y") is None
    assert _presolve(facts, "no-slash") is None


def test_port_static_dynamic_overlap_and_duplicate_ambiguity() -> None:
    # two static pages with the same effective route
    a1, a2 = _pfact("a"), _pfact("a")
    s1, s2 = _pfact("x", parent=a1), _pfact("x", parent=a2)
    facts = _pfacts(a1, a2, s1, s2)
    with pytest.raises(fs.SurfaceReadError) as caught:
        _presolve(facts, "/a/x")
    assert caught.value.reason == "RENDER_ROUTE_AMBIGUOUS"
    # two dynamic siblings under one parent: same prefix, both match
    parent = _pfact("p")
    d1 = _pfact("c1", parent=parent, template="{slug}")
    d2 = _pfact("c2", parent=parent, template="{slug}")
    dfacts = _pfacts(parent, d1, d2)
    with pytest.raises(fs.SurfaceReadError) as caught:
        _presolve(dfacts, "/p/whatever")
    assert caught.value.reason == "RENDER_ROUTE_AMBIGUOUS"
    # static + dynamic overlap on one route
    q1, q2 = _pfact("q"), _pfact("q")
    dyn = _pfact("d", parent=q1, template="{slug}")
    static_same = _pfact("d", parent=q2)
    ofacts = _pfacts(q1, q2, dyn, static_same)
    with pytest.raises(fs.SurfaceReadError) as caught:
        _presolve(ofacts, "/q/d")
    assert caught.value.reason == "RENDER_ROUTE_AMBIGUOUS"


def test_port_page_branch_uniform_reason() -> None:
    good = _pfact("good")
    dynamic = _pfact("dyn", template="{slug}")
    broken_parent = _pfact("bp", locale="fr")
    broken = _pfact("bc", parent=broken_parent)
    facts = _pfacts(good, dynamic, broken_parent, broken)
    # PAGE on a dynamic page: 057 failure remapped to the 059 code
    with pytest.raises(fs.SurfaceReadError) as caught:
        _pnavigate(facts, [_pnitem("PAGE", str(dynamic.id), page_id=dynamic.id)])
    assert caught.value.reason == "RENDER_NAVIGATION_PAGE_INVALID"
    # PAGE whose hierarchy fails effective-route derivation
    with pytest.raises(fs.SurfaceReadError) as caught:
        _pnavigate(facts, [_pnitem("PAGE", str(broken.id), page_id=broken.id)])
    assert caught.value.reason == "RENDER_NAVIGATION_PAGE_INVALID"
    # PAGE lookup miss: ONE absent ID in both fields (target matches
    # page_id, but no such retained page exists)
    missing = uuid4()
    with pytest.raises(fs.SurfaceReadError) as caught:
        _pnavigate(facts, [_pnitem("PAGE", str(missing), page_id=missing)])
    assert caught.value.reason == "RENDER_NAVIGATION_PAGE_INVALID"
    # id/target mismatch is a separate control, same 059 code
    with pytest.raises(fs.SurfaceReadError) as caught:
        _pnavigate(facts, [_pnitem("PAGE", "mismatch", page_id=good.id)])
    assert caught.value.reason == "RENDER_NAVIGATION_PAGE_INVALID"
    # the valid PAGE item still resolves
    rows = _pnavigate(facts, [_pnitem("PAGE", str(good.id), page_id=good.id)])
    assert rows[0][10] == "/good"


def test_port_internal_gate_locale_neutral_reserved_and_duplicate() -> None:
    root_page = _pfact("home")
    linked = _pfact("linked")
    dup_a, dup_b = _pfact("dup"), _pfact("dup")
    facts = _pfacts(root_page, linked, dup_a, dup_b)
    # NULL item locale is locale-neutral: the target still resolves
    rows = _pnavigate(facts, [_pnitem("INTERNAL", "/linked", locale=None)])
    assert rows[0][10] == "/linked"
    # reserved service prefixes fail closed
    for target in ("/api/x", "/media/1", "/preview/page"):
        with pytest.raises(fs.SurfaceReadError) as caught:
            _pnavigate(facts, [_pnitem("INTERNAL", target, locale=None)])
        assert caught.value.reason == "RENDER_NAVIGATION_TARGET_INVALID"
    # a duplicated effective route fails closed to "no target exists"
    with pytest.raises(fs.SurfaceReadError) as caught:
        _pnavigate(facts, [_pnitem("INTERNAL", "/dup", locale=None)])
    assert caught.value.reason == "RENDER_NAVIGATION_TARGET_INVALID"
    # EXTERNAL targets pass through unchanged
    ext = _pnavigate(
        facts, [_pnitem("EXTERNAL", "https://example.test/x", locale=None)]
    )
    assert ext[0][10] == "https://example.test/x"


def test_port_ancestor_chain_root_first_positions() -> None:
    root = _pfact("root")
    mid = _pfact("mid", parent=root)
    leaf = _pfact("leaf", parent=mid)
    chain = fs.page_ancestor_chain(
        _pfacts(root, mid, leaf), site_id=SITE_ID, page_id=leaf.id
    )
    assert [(position, fact.slug) for position, fact in chain] == [
        (1, "root"),
        (2, "mid"),
    ]
    # the page itself is never in the chain; unknown pages give zero rows
    assert (
        fs.page_ancestor_chain(
            _pfacts(root, mid, leaf), site_id=SITE_ID, page_id=uuid4()
        )
        == ()
    )


class _ScanningFacts(Mapping[UUID, fs.RenderPageFact]):
    """Facts mapping counting FULL candidate scans (values() iterations).

    Cache cardinality alone cannot prove once-per-request execution:
    with per-item full rescans restored, the derivation cache still
    holds 64 entries and every resolved value is correct.  Counting
    actual candidate visits makes that counterfactual fail.
    """

    def __init__(self, inner: dict[UUID, fs.RenderPageFact]) -> None:
        self._inner = inner
        self.scans = 0

    def __getitem__(self, key: UUID) -> fs.RenderPageFact:
        return self._inner[key]

    def __iter__(self) -> Iterator[UUID]:
        self.scans += 1
        return iter(self._inner)

    def __len__(self) -> int:
        return len(self._inner)


def test_port_route_memo_bounded_work_and_failure_hygiene() -> None:
    pages = [_pfact(f"m{i:03d}") for i in range(64)]
    cf = _ScanningFacts(_pfacts(*pages))
    items = [
        _pnitem("INTERNAL", f"/m{i:03d}", locale=None, position=i) for i in range(64)
    ]
    # 64 DISTINCT hrefs: one full scan (the once-built target counts),
    # not one per item
    memo = fs._RouteMemo(cf, default_locale="en", enabled_tags=frozenset({"en"}))
    rows = _pnavigate(cf, items, memo=memo)
    assert len(rows) == 64
    assert len(memo.derived) == 64
    assert cf.scans == 1
    # 64 REPEATED hrefs: the counts are already built, still no rescan
    repeated = [
        _pnitem("INTERNAL", "/m000", locale=None, position=i) for i in range(64)
    ]
    rows = _pnavigate(cf, repeated, memo=memo)
    assert len(rows) == 64
    assert cf.scans == 1
    # repeated resolutions reuse the once-built static index: each
    # call adds only the dynamic-phase candidate pass, never a new
    # static scan
    assert _presolve(cf, "/m000", memo=memo) is pages[0]
    assert _presolve(cf, "/m063", memo=memo) is pages[63]
    assert len(memo.static_indexes) == 1
    assert len(memo.derived) == 64
    assert cf.scans == 4
    # context guard: a memo bound to other locale facts refuses loudly
    with pytest.raises(ValueError):
        _pnavigate(
            cf,
            items,
            memo=fs._RouteMemo(cf, default_locale="en", enabled_tags=frozenset({"fr"})),
        )
    # cached failures: stable reason, fresh exception object each time
    bad_parent = _pfact("bp2", locale="fr")
    bad_child = _pfact("bc2", parent=bad_parent)
    bfacts = _pfacts(bad_parent, bad_child)
    bmemo = fs._RouteMemo(
        bfacts, default_locale="en", enabled_tags=frozenset({"en", "fr"})
    )
    first: fs.SurfaceReadError | None = None
    for _ in range(4):
        with pytest.raises(fs.SurfaceReadError) as caught:
            bmemo.route(bad_child.id)
        assert caught.value.reason == "PAGE_PARENT_INVALID"
        if first is None:
            first = caught.value
        else:
            assert caught.value is not first
    assert first is not None


class _NavTransport:
    """Transport fake for the REAL live read surface: the surface's exact
    SQL dispatch and overflow sentinels execute unchanged; only the
    database round trip is faked (R3 shared-boundary test)."""

    def __init__(self, item_rows: int, page_target: UUID | None = None) -> None:
        self._item_rows = item_rows
        self._page_target = page_target

    async def fetch(self, statement: str, site_id: UUID) -> list[tuple[Any, ...]]:
        if statement.startswith("SELECT id,site_id,key,label,labels,settings"):
            return [(UUID(int=900), site_id, "main", "Main", {"en": "Main"}, {})]
        if "FROM content.navigation_item" in statement:
            nav = UUID(int=900)
            rows: list[tuple[Any, ...]] = []
            for i in range(self._item_rows):
                if self._page_target is not None and i == 0:
                    page_id: UUID | None = self._page_target
                    target_kind = "PAGE"
                    target_value = str(page_id)
                else:
                    page_id = None
                    target_kind = "INTERNAL"
                    target_value = f"/p{i}"
                rows.append(
                    (
                        UUID(int=9000 + i),
                        site_id,
                        nav,
                        None,
                        page_id,
                        target_kind,
                        target_value,
                        {"en": f"I{i}"},
                        None,
                        i,
                    )
                )
            return rows
        raise AssertionError(f"unexpected statement: {statement}")


def _run_navigation(
    surface: fs.DatabaseRenderSurface,
) -> None:
    facts: dict[UUID, fs.RenderPageFact] = {}
    memo = fs.new_route_memo(facts, default_locale="en", enabled_tags=frozenset({"en"}))
    asyncio.run(
        RenderProjectionService._navigation(
            object(),  # type: ignore[arg-type]
            surface,
            facts=facts,
            memo=memo,
            site_id=SITE_ID,
            selected_locale="en",
            default_locale="en",
            statuses=["PUBLISHED"],
            enabled_tags=frozenset({"en"}),
        )
    )


def test_navigation_item_overflow_keeps_the_stable_reason() -> None:
    # over the 4096 item cap: the surface sentinel reason must reach the
    # service unchanged, not be folded into a generic unavailable
    surface = fs.DatabaseRenderSurface(_NavTransport(item_rows=4097))
    with pytest.raises(ProjectionError) as caught:
        _run_navigation(surface)
    assert caught.value.reason == "navigation_too_large"


def test_navigation_target_failure_maps_to_unavailable() -> None:
    # a target failure raised inside the 059 SQL port kept the legacy
    # service mapping (PostgresError -> unavailable)
    missing = uuid4()
    surface = fs.DatabaseRenderSurface(_NavTransport(item_rows=1, page_target=missing))
    with pytest.raises(ProjectionError) as caught:
        _run_navigation(surface)
    assert caught.value.reason == "unavailable"

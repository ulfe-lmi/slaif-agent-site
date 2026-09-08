"""Pure projection and service-auth boundary tests."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    _node_tree,
    _route_parts,
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
    props: dict[str, object] | None = None,
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


def test_preview_request_rejects_extra_authority_fields() -> None:
    with pytest.raises(ValueError):
        RenderPageRequest.model_validate(
            {"authority": "example.test", "path": "/", "workspace": "forged"}
        )

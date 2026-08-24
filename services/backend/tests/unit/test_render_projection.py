"""Pure projection and service-auth boundary tests."""

from __future__ import annotations

from uuid import UUID

import pytest
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    _node_tree,
    _route_slug,
)
from slaif_agent_site.sites.models import SiteContext

SITE_ID = UUID("11111111-1111-4111-8111-111111111111")


def _context(prefix: str = "/docs") -> SiteContext:
    return SiteContext._from_database(
        (SITE_ID, "docs", "ACTIVE", 3, "en", "example.test", prefix)
    )


def test_projection_route_is_site_prefix_confined() -> None:
    assert _route_slug(_context(), "/docs/about/") == "about"
    assert _route_slug(_context("/"), "/about") == "about"
    with pytest.raises(ProjectionError):
        _route_slug(_context(), "/docs-other/about")


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

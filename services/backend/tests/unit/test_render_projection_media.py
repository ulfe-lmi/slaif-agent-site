"""Projection media-descriptor resolution for media lists (079/2) and docs (079/3)."""

import asyncio
import uuid as uuid_module

import pytest
from slaif_agent_site.render_api.projection import (
    DOCUMENT_MIME_CLASSES,
    ProjectionMedia,
    ProjectionNode,
    RenderProjectionService,
    _attach_media,
    _media_descriptor,
)

SITE = uuid_module.UUID("11111111-2222-4333-8444-555555555555")
M_A = uuid_module.UUID("11111111-1111-4111-8111-111111111111")
M_B = uuid_module.UUID("11111111-1111-4111-8111-111111111112")
M_C = uuid_module.UUID("11111111-1111-4111-8111-111111111113")
DIGEST = "aabb" + "1234567890abcdef" * 3 + "fedcba098765"
PREVIEW_URL = f"/media/v1/sites/{SITE}/assets/{M_A}/content"
PUBLIC_URL = f"/media/public/sha256/aa/bb/{DIGEST}"

PNG_PUBLIC = ("image/png", 1234, DIGEST, "public")
PNG_PRIVATE = ("image/png", 1234, DIGEST, "private")
JPEG_PUBLIC = ("image/jpeg", 5678, DIGEST, "public")
SVG_PUBLIC = ("image/svg+xml", 9, DIGEST, "public")
TEXT_PUBLIC = ("text/plain", 9, DIGEST, "public")
PDF_PUBLIC = ("application/pdf", 4321, DIGEST, "public")
PDF_PRIVATE = ("application/pdf", 4321, DIGEST, "private")


def _node(
    node_id: str, component_type: str, props: dict[str, object]
) -> ProjectionNode:
    return ProjectionNode(
        id=uuid_module.UUID(node_id),
        component_type=component_type,
        schema_version="1",
        parent_id=None,
        slot_key="default",
        order_key=0,
        props=props,
    )


def test_preview_descriptor_uses_the_079_preview_url_form() -> None:
    descriptor = _media_descriptor(
        render_mode="preview", site_id=SITE, media_id=M_A, row=PNG_PRIVATE
    )
    assert descriptor == ProjectionMedia(
        url=PREVIEW_URL, mime_type="image/png", size_bytes=1234
    )
    # preview ignores publication status: private assets resolve in preview
    assert descriptor is not None


def test_public_descriptor_uses_the_digest_url_only_when_public() -> None:
    public = _media_descriptor(
        render_mode="public", site_id=SITE, media_id=M_A, row=PNG_PUBLIC
    )
    assert public == ProjectionMedia(
        url=PUBLIC_URL, mime_type="image/png", size_bytes=1234
    )
    private = _media_descriptor(
        render_mode="public", site_id=SITE, media_id=M_A, row=PNG_PRIVATE
    )
    assert private is None


@pytest.mark.parametrize(
    "row",
    [None, SVG_PUBLIC, TEXT_PUBLIC],
)
def test_fail_closed_rows_yield_no_descriptor(row: object) -> None:
    for render_mode in ("preview", "public"):
        assert (
            _media_descriptor(
                render_mode=render_mode, site_id=SITE, media_id=M_A, row=row
            )
            is None
        )


class _FakeConnection:
    def __init__(self, rows: dict[uuid_module.UUID, object]) -> None:
        self.rows = rows
        self.queries: list[uuid_module.UUID] = []

    async def fetchrow(
        self, sql: str, site_id: uuid_module.UUID, media_id: uuid_module.UUID
    ) -> object:
        assert site_id == SITE
        self.queries.append(media_id)
        return self.rows.get(media_id)


def _descriptors(
    nodes: tuple[ProjectionNode, ...],
    rows: dict[uuid_module.UUID, object],
    render_mode: str,
) -> tuple[
    dict[uuid_module.UUID, ProjectionMedia],
    dict[uuid_module.UUID, tuple[ProjectionMedia | None, ...]],
]:
    connection = _FakeConnection(rows)
    return asyncio.run(
        RenderProjectionService._media_descriptors(
            object(),  # type: ignore[arg-type]
            connection,
            nodes=nodes,
            site_id=SITE,
            render_mode=render_mode,
        )
    )


def test_gallery_list_descriptors_mixed_resolved_and_fail_closed() -> None:
    gallery = _node(
        "33333333-0000-4000-8000-000000000001",
        "Gallery",
        {
            "title": "Team",
            "items": [
                {"mediaId": str(M_A), "alt": "a", "aspectRatio": "16:9"},
                {"mediaId": str(M_B), "alt": "b"},
                {"mediaId": str(M_C), "alt": "c"},
                {"alt": "missing reference"},
            ],
        },
    )
    descriptors, list_descriptors = _descriptors(
        (gallery,),
        {M_A: PNG_PUBLIC, M_B: JPEG_PUBLIC},  # M_C absent, M_D absent
        "preview",
    )
    assert descriptors == {}
    media_items = list_descriptors[gallery.id]
    assert len(media_items) == 4
    assert media_items[0] == ProjectionMedia(
        url=f"/media/v1/sites/{SITE}/assets/{M_A}/content",
        mime_type="image/png",
        size_bytes=1234,
    )
    assert media_items[1] is not None
    assert media_items[1].mime_type == "image/jpeg"
    assert media_items[2] is None
    assert media_items[3] is None


def test_gallery_public_mode_marks_non_public_items_fail_closed() -> None:
    gallery = _node(
        "33333333-0000-4000-8000-000000000002",
        "Gallery",
        {
            "items": [
                {"mediaId": str(M_A), "alt": "a"},
                {"mediaId": str(M_B), "alt": "b"},
            ],
        },
    )
    _, list_descriptors = _descriptors(
        (gallery,),
        {M_A: PNG_PUBLIC, M_B: PNG_PRIVATE},
        "public",
    )
    media_items = list_descriptors[gallery.id]
    assert media_items[0] == ProjectionMedia(
        url=PUBLIC_URL, mime_type="image/png", size_bytes=1234
    )
    assert media_items[1] is None


def test_logogrid_and_image_share_the_same_resolution() -> None:
    logogrid = _node(
        "33333333-0000-4000-8000-000000000003",
        "LogoGrid",
        {
            "items": [
                {"mediaId": str(M_A), "name": "Acme"},
                {"mediaId": str(M_B), "name": "Beta"},
            ],
        },
    )
    image = _node(
        "33333333-0000-4000-8000-000000000004",
        "Image",
        {"mediaId": str(M_A), "alt": "solo"},
    )
    descriptors, list_descriptors = _descriptors(
        (logogrid, image),
        {M_A: PNG_PUBLIC, M_B: JPEG_PUBLIC},
        "preview",
    )
    assert descriptors[image.id] == ProjectionMedia(
        url=PREVIEW_URL, mime_type="image/png", size_bytes=1234
    )
    media_items = list_descriptors[logogrid.id]
    assert media_items[0] is not None
    assert media_items[1] is not None


def test_non_list_items_and_other_types_are_untouched() -> None:
    gallery = _node(
        "33333333-0000-4000-8000-000000000005",
        "Gallery",
        {"items": "not-a-list"},
    )
    other = _node(
        "33333333-0000-4000-8000-000000000006",
        "Heading",
        {"text": "no media", "level": 2},
    )
    descriptors, list_descriptors = _descriptors(
        (gallery, other), {M_A: PNG_PUBLIC}, "preview"
    )
    assert descriptors == {}
    assert list_descriptors == {}


def test_attach_media_carries_list_descriptors_to_the_right_node() -> None:
    gallery = _node(
        "33333333-0000-4000-8000-000000000007",
        "Gallery",
        {
            "items": [
                {"mediaId": str(M_A), "alt": "a"},
                {"mediaId": str(M_B), "alt": "b"},
            ],
        },
    )
    image = _node(
        "33333333-0000-4000-8000-000000000008",
        "Image",
        {"mediaId": str(M_A), "alt": "solo"},
    )
    descriptors = {
        image.id: ProjectionMedia(url=PREVIEW_URL, mime_type="image/png", size_bytes=1)
    }
    list_descriptors: dict[uuid_module.UUID, tuple[ProjectionMedia | None, ...]] = {
        gallery.id: (
            ProjectionMedia(url=PREVIEW_URL, mime_type="image/png", size_bytes=1),
            None,
        )
    }
    attached_gallery, attached_image = _attach_media(
        (gallery, image), descriptors, list_descriptors
    )
    assert attached_gallery.id == gallery.id
    assert attached_gallery.media_items == (
        ProjectionMedia(url=PREVIEW_URL, mime_type="image/png", size_bytes=1),
        None,
    )
    assert attached_gallery.media is None
    # the sibling node keeps its single-image descriptor when attached
    assert attached_image.id == image.id
    assert attached_image.media is not None
    assert attached_image.media_items is None


@pytest.mark.parametrize("render_mode", ["preview", "public"])
def test_descriptor_urls_never_leak_media_id_in_public_mode(
    render_mode: str,
) -> None:
    descriptor = _media_descriptor(
        render_mode=render_mode, site_id=SITE, media_id=M_A, row=PNG_PUBLIC
    )
    if descriptor is None:
        return
    if render_mode == "public":
        assert str(M_A) not in descriptor.url
    else:
        assert str(M_A) in descriptor.url


# ------------------------------------------------------------------ 079/3
# DocumentList document-class descriptor resolution.
M_D = uuid_module.UUID("11111111-1111-4111-8111-111111111114")


def test_document_descriptor_resolves_only_the_document_mime_class() -> None:
    preview = _media_descriptor(
        render_mode="preview",
        site_id=SITE,
        media_id=M_A,
        row=PDF_PRIVATE,
        mime_classes=DOCUMENT_MIME_CLASSES,
    )
    assert preview == ProjectionMedia(
        url=PREVIEW_URL, mime_type="application/pdf", size_bytes=4321
    )
    public = _media_descriptor(
        render_mode="public",
        site_id=SITE,
        media_id=M_A,
        row=PDF_PUBLIC,
        mime_classes=DOCUMENT_MIME_CLASSES,
    )
    assert public == ProjectionMedia(
        url=PUBLIC_URL, mime_type="application/pdf", size_bytes=4321
    )
    # non-public document rows fail closed under the canonical render mode
    assert (
        _media_descriptor(
            render_mode="public",
            site_id=SITE,
            media_id=M_A,
            row=PDF_PRIVATE,
            mime_classes=DOCUMENT_MIME_CLASSES,
        )
        is None
    )
    # image-class rows are never document descriptors ...
    assert (
        _media_descriptor(
            render_mode="preview",
            site_id=SITE,
            media_id=M_A,
            row=PNG_PUBLIC,
            mime_classes=DOCUMENT_MIME_CLASSES,
        )
        is None
    )
    # ... and document-class rows are never image descriptors
    assert (
        _media_descriptor(
            render_mode="preview", site_id=SITE, media_id=M_A, row=PDF_PUBLIC
        )
        is None
    )


def _doclist_node(node_id: str, items: list[dict[str, object]]) -> ProjectionNode:
    return _node(node_id, "DocumentList", {"title": "Documents", "items": items})


def test_documentlist_list_descriptors_mixed_resolved_and_fail_closed() -> None:
    doclist = _doclist_node(
        "33333333-0000-4000-8000-000000000010",
        [
            {"mediaId": str(M_A), "label": "a"},
            {"mediaId": str(M_B), "label": "b"},
            {"mediaId": str(M_C), "label": "missing"},
            {"label": "no reference"},
        ],
    )
    descriptors, list_descriptors = _descriptors(
        (doclist,),
        {M_A: PDF_PUBLIC, M_B: PNG_PUBLIC},  # M_B is an image row; M_C absent
        "preview",
    )
    assert descriptors == {}
    media_items = list_descriptors[doclist.id]
    assert len(media_items) == 4
    assert media_items[0] == ProjectionMedia(
        url=f"/media/v1/sites/{SITE}/assets/{M_A}/content",
        mime_type="application/pdf",
        size_bytes=4321,
    )
    assert media_items[1] is None  # image-class row: not the document class
    assert media_items[2] is None  # unresolved reference
    assert media_items[3] is None  # malformed item


def test_documentlist_public_mode_marks_non_public_items_fail_closed() -> None:
    doclist = _doclist_node(
        "33333333-0000-4000-8000-000000000011",
        [
            {"mediaId": str(M_A), "label": "a"},
            {"mediaId": str(M_B), "label": "b"},
        ],
    )
    _, list_descriptors = _descriptors(
        (doclist,),
        {M_A: PDF_PUBLIC, M_B: PDF_PRIVATE},
        "public",
    )
    media_items = list_descriptors[doclist.id]
    assert media_items[0] == ProjectionMedia(
        url=PUBLIC_URL, mime_type="application/pdf", size_bytes=4321
    )
    assert media_items[1] is None


def test_documentlist_descriptor_urls_follow_the_079_url_forms() -> None:
    doclist = _doclist_node(
        "33333333-0000-4000-8000-000000000012",
        [{"mediaId": str(M_A), "label": "a"}],
    )
    for render_mode, expected_url in (
        ("preview", f"/media/v1/sites/{SITE}/assets/{M_A}/content"),
        ("public", PUBLIC_URL),
    ):
        _, list_descriptors = _descriptors((doclist,), {M_A: PDF_PUBLIC}, render_mode)
        (descriptor,) = list_descriptors[doclist.id]
        assert descriptor is not None
        assert descriptor.url == expected_url
        if render_mode == "public":
            assert str(M_A) not in descriptor.url


def test_documentlist_non_list_items_are_untouched() -> None:
    doclist = _node(
        "33333333-0000-4000-8000-000000000013",
        "DocumentList",
        {"items": "not-a-list"},
    )
    descriptors, list_descriptors = _descriptors(
        (doclist,), {M_A: PDF_PUBLIC}, "preview"
    )
    assert descriptors == {}
    assert list_descriptors == {}


def test_image_list_components_never_resolve_document_rows() -> None:
    gallery = _node(
        "33333333-0000-4000-8000-000000000014",
        "Gallery",
        {"items": [{"mediaId": str(M_A), "alt": "pdf in a gallery"}]},
    )
    image = _node(
        "33333333-0000-4000-8000-000000000015",
        "Image",
        {"mediaId": str(M_A), "alt": "pdf as image"},
    )
    descriptors, list_descriptors = _descriptors(
        (gallery, image), {M_A: PDF_PUBLIC}, "preview"
    )
    assert list_descriptors[gallery.id] == (None,)
    assert descriptors == {}

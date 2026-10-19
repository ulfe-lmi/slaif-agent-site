"""Projection media-descriptor resolution for media lists (079/2) and docs (079/3)."""

import asyncio
import uuid as uuid_module

import pytest
from slaif_agent_site.render_api import frozen_source as fs
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
PUBLIC_URL = f"/media/public/sha256/aa/bb/{DIGEST}"
WS = uuid_module.UUID("77777777-8888-4999-8999-000000000077")
WORKSPACE_URL = f"/media/v1/sites/{SITE}/workspaces/{WS}/preview/assets/{M_A}/content"
BOUND_URL = f"/media/v1/browser-preview/assets/{M_A}/content"

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


def test_preview_descriptor_uses_the_workspace_preview_url_form() -> None:
    descriptor = _media_descriptor(
        render_mode="preview",
        site_id=SITE,
        media_id=M_A,
        row=PNG_PRIVATE,
        preview_workspace_id=WS,
    )
    assert descriptor == ProjectionMedia(
        url=WORKSPACE_URL, mime_type="image/png", size_bytes=1234
    )
    # preview ignores publication status: private assets resolve in preview
    assert descriptor is not None


def test_preview_descriptor_without_trusted_context_is_fail_closed() -> None:
    # a preview render that lost its trusted context (neither the
    # authorize-verified workspace nor the bound run) must NOT fall
    # back to a site-wide URL
    for kwargs in ({"preview_workspace_id": None, "preview_bound": False}, {}):
        assert (
            _media_descriptor(
                render_mode="preview",
                site_id=SITE,
                media_id=M_A,
                row=PNG_PRIVATE,
                **kwargs,  # type: ignore[arg-type]
            )
            is None
        )
    assert (
        _media_descriptor(
            render_mode="preview",
            site_id=SITE,
            media_id=M_A,
            row=PDF_PRIVATE,
            mime_classes=DOCUMENT_MIME_CLASSES,
        )
        is None
    )


def test_preview_bound_descriptor_uses_the_bound_run_url() -> None:
    for row in (PNG_PRIVATE, PNG_PUBLIC):
        descriptor = _media_descriptor(
            render_mode="preview",
            site_id=SITE,
            media_id=M_A,
            row=row,
            preview_workspace_id=WS,
            preview_bound=True,
        )
        assert descriptor is not None
        assert descriptor.url == BOUND_URL
        # the bound URL never carries the human workspace
        assert str(WS) not in descriptor.url
        assert str(SITE) not in descriptor.url
    # document class rows resolve under the same bound URL
    document = _media_descriptor(
        render_mode="preview",
        site_id=SITE,
        media_id=M_A,
        row=PDF_PRIVATE,
        mime_classes=DOCUMENT_MIME_CLASSES,
        preview_workspace_id=WS,
        preview_bound=True,
    )
    assert document is not None
    assert document.url == BOUND_URL


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
                render_mode=render_mode,
                site_id=SITE,
                media_id=M_A,
                row=row,
                preview_workspace_id=WS,
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
    *,
    preview_workspace_id: uuid_module.UUID | None = None,
    preview_bound: bool = False,
) -> tuple[
    dict[uuid_module.UUID, ProjectionMedia],
    dict[uuid_module.UUID, tuple[ProjectionMedia | None, ...]],
]:
    surface = fs.DatabaseRenderSurface(_FakeConnection(rows))
    return asyncio.run(
        RenderProjectionService._media_descriptors(
            object(),  # type: ignore[arg-type]
            surface,
            nodes=nodes,
            site_id=SITE,
            render_mode=render_mode,
            preview_workspace_id=preview_workspace_id,
            preview_bound=preview_bound,
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
        preview_workspace_id=WS,
    )
    assert descriptors == {}
    media_items = list_descriptors[gallery.id]
    assert len(media_items) == 4
    assert media_items[0] == ProjectionMedia(
        url=WORKSPACE_URL,
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
        preview_workspace_id=WS,
    )
    assert descriptors[image.id] == ProjectionMedia(
        url=WORKSPACE_URL, mime_type="image/png", size_bytes=1234
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
        (gallery, other), {M_A: PNG_PUBLIC}, "preview", preview_workspace_id=WS
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
        image.id: ProjectionMedia(
            url=WORKSPACE_URL, mime_type="image/png", size_bytes=1
        )
    }
    list_descriptors: dict[uuid_module.UUID, tuple[ProjectionMedia | None, ...]] = {
        gallery.id: (
            ProjectionMedia(url=WORKSPACE_URL, mime_type="image/png", size_bytes=1),
            None,
        )
    }
    attached_gallery, attached_image = _attach_media(
        (gallery, image), descriptors, list_descriptors
    )
    assert attached_gallery.id == gallery.id
    assert attached_gallery.media_items == (
        ProjectionMedia(url=WORKSPACE_URL, mime_type="image/png", size_bytes=1),
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
        render_mode=render_mode,
        site_id=SITE,
        media_id=M_A,
        row=PNG_PUBLIC,
        preview_workspace_id=WS,
    )
    if descriptor is None:
        return
    if render_mode == "public":
        assert str(M_A) not in descriptor.url
    else:
        assert str(M_A) in descriptor.url
        assert str(WS) in descriptor.url


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
        preview_workspace_id=WS,
    )
    assert preview == ProjectionMedia(
        url=WORKSPACE_URL, mime_type="application/pdf", size_bytes=4321
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
        preview_workspace_id=WS,
    )
    assert descriptors == {}
    media_items = list_descriptors[doclist.id]
    assert len(media_items) == 4
    assert media_items[0] == ProjectionMedia(
        url=WORKSPACE_URL,
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
        ("preview", WORKSPACE_URL),
        ("public", PUBLIC_URL),
    ):
        _, list_descriptors = _descriptors(
            (doclist,),
            {M_A: PDF_PUBLIC},
            render_mode,
            preview_workspace_id=WS,
        )
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
        (doclist,), {M_A: PDF_PUBLIC}, "preview", preview_workspace_id=WS
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
        (gallery, image), {M_A: PDF_PUBLIC}, "preview", preview_workspace_id=WS
    )
    assert list_descriptors[gallery.id] == (None,)
    assert descriptors == {}


SNAP = uuid_module.UUID("99999999-8888-4777-8666-555555555555")
REVIEW_URL = f"/media/v1/review/{SNAP}/assets/{M_A}/content"


def test_preview_bound_list_descriptors_use_the_bound_run_url() -> None:
    gallery = _node(
        "33333333-0000-4000-8000-000000000020",
        "Gallery",
        {
            "items": [
                {"mediaId": str(M_A), "alt": "a"},
                {"mediaId": str(M_B), "alt": "b"},
            ]
        },
    )
    doclist = _doclist_node(
        "33333333-0000-4000-8000-000000000021",
        [{"mediaId": str(M_A), "label": "a"}],
    )
    descriptors, list_descriptors = _descriptors(
        (gallery, doclist),
        {M_A: PDF_PRIVATE, M_B: PNG_PRIVATE},
        "preview",
        preview_workspace_id=WS,
        preview_bound=True,
    )
    assert descriptors == {}
    # M_A is a document-class row: the image-class gallery entry fails
    # closed, the M_B image entry resolves under the bound URL
    assert list_descriptors[gallery.id][0] is None
    gallery_image = list_descriptors[gallery.id][1]
    assert gallery_image is not None
    assert gallery_image.url == f"/media/v1/browser-preview/assets/{M_B}/content"
    (doc_item,) = list_descriptors[doclist.id]
    assert doc_item is not None
    assert doc_item.url == BOUND_URL
    assert str(WS) not in doc_item.url


def test_review_descriptor_ignores_preview_context() -> None:
    # the frozen review URL is the only option in review mode: preview
    # context flags must not alter it
    descriptor = _media_descriptor(
        render_mode="review",
        site_id=SITE,
        media_id=M_A,
        row=PNG_PRIVATE,
        snapshot_id=SNAP,
        preview_workspace_id=WS,
        preview_bound=True,
    )
    assert descriptor is not None
    assert descriptor.url == REVIEW_URL


def test_review_descriptor_uses_snapshot_url_for_private_media() -> None:
    descriptor = _media_descriptor(
        render_mode="review",
        site_id=SITE,
        media_id=M_A,
        row=PNG_PRIVATE,
        snapshot_id=SNAP,
    )
    assert descriptor == ProjectionMedia(
        url=REVIEW_URL, mime_type="image/png", size_bytes=1234
    )


def test_review_descriptor_uses_snapshot_url_for_public_media() -> None:
    # public captured media must NOT resolve to the anonymous public
    # digest URL: public byte reads depend on current canonical
    # references, which are not frozen input
    descriptor = _media_descriptor(
        render_mode="review",
        site_id=SITE,
        media_id=M_A,
        row=PNG_PUBLIC,
        snapshot_id=SNAP,
    )
    assert descriptor is not None
    assert descriptor.url == REVIEW_URL
    assert descriptor.url != PUBLIC_URL


def test_review_descriptor_without_snapshot_id_is_fail_closed() -> None:
    for row in (PNG_PRIVATE, PNG_PUBLIC):
        assert (
            _media_descriptor(
                render_mode="review",
                site_id=SITE,
                media_id=M_A,
                row=row,
            )
            is None
        )


def test_review_descriptor_document_class_uses_snapshot_url() -> None:
    descriptor = _media_descriptor(
        render_mode="review",
        site_id=SITE,
        media_id=M_A,
        row=PDF_PRIVATE,
        mime_classes=DOCUMENT_MIME_CLASSES,
        snapshot_id=SNAP,
    )
    assert descriptor is not None
    assert descriptor.url == REVIEW_URL
    assert descriptor.mime_type == "application/pdf"

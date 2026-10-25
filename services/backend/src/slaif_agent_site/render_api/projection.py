"""Bounded, typed Render projections over canonical and COW content views."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Annotated, Any, Literal, Protocol, cast
from uuid import UUID

import asyncpg
from agentcow.postgres import asyncpg_cow_session
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from slaif_agent_site.browser_contracts import normalize_preview_route
from slaif_agent_site.browser_preview_credentials import (
    BrowserPreviewCredentialError,
    BrowserPreviewCredentialSigner,
    BrowserPreviewExpectedBinding,
)
from slaif_agent_site.content_model.bounded_embed import (
    validate_map_embed_props,
    validate_video_embed_props,
)
from slaif_agent_site.content_model.canonical import parse_snapshot_text
from slaif_agent_site.content_model.component_catalog import (
    COMPONENT_BY_TYPE,
    MAX_COMPONENT_DEPTH,
    MAX_COMPONENT_PROPS_BYTES,
    MAX_COMPONENTS_PER_PAGE,
    TRUSTED_COMPONENT_TYPES,
)
from slaif_agent_site.content_model.design_system import (
    validate_agent_component_props,
)
from slaif_agent_site.content_model.query_dsl import (
    MAX_CANDIDATES,
    MAX_PAGE_SIZE,
    matches_filter,
    sort_collection_items,
    validate_query_contract,
)
from slaif_agent_site.content_model.site_data_validators import (
    validate_external_url,
    validate_internal_route,
    validate_redirect_source,
    validate_redirect_target,
)
from slaif_agent_site.content_model.theme import ThemeRecord, theme_record_from_row
from slaif_agent_site.content_model.validators import validate_values
from slaif_agent_site.identity.sessions import digest_secret, parse_session_token
from slaif_agent_site.render_api import frozen_source as fs
from slaif_agent_site.render_api.frozen_source import (
    RenderPageFact,
    navigation_resolved_items,
    new_route_memo,
    page_ancestor_chain,
    resolve_page_route,
)
from slaif_agent_site.sites.models import SiteContext
from slaif_agent_site.sites.normalization import (
    normalize_authority,
    normalize_locale,
    normalize_request_path,
    path_is_reserved,
)

LOGGER = logging.getLogger(__name__)


_REGION_VARIANTS = {
    "header": ("institutional", "minimal"),
    "footer": ("multi-column", "single-column"),
}

_BROWSER_STAGES = frozenset(
    {
        "context",
        "token-binding",
        "authorize-consume",
        "cow-context",
        "authorize-recheck",
        "projection-query",
        "success",
    }
)


def _browser_stage(stage: str, outcome: str) -> None:
    """Emit only the fixed-vocabulary browser-preview diagnosis signal."""

    if stage not in _BROWSER_STAGES or outcome not in {
        "ok",
        "not_found",
        "unavailable",
        "error",
    }:
        return
    LOGGER.info(
        "browser preview stage",
        extra={"event_fields": {"stage": stage, "outcome": outcome}},
    )


def _browser_outcome(error: ProjectionError) -> str:
    return "unavailable" if error.reason == "unavailable" else "not_found"


CATALOG_TYPES = TRUSTED_COMPONENT_TYPES
MAX_NODES = MAX_COMPONENTS_PER_PAGE
MAX_DEPTH = MAX_COMPONENT_DEPTH
MAX_PROPS_BYTES = MAX_COMPONENT_PROPS_BYTES
ALLOWED_SLOTS = {
    item.type: frozenset(item.allowed_slots) for item in COMPONENT_BY_TYPE.values()
}
MAX_CHILDREN = {item.type: item.max_children for item in COMPONENT_BY_TYPE.values()}
COLLECTION_BINDING_TYPES = frozenset(
    {
        "CollectionList",
        "CollectionGrid",
        "CollectionDetail",
        "CollectionSearch",
        "CollectionFilter",
        "RelatedItems",
    }
)
# Bounded client-filtering components: per-component default limits, capped by
# the view pagination limit, bound the pre-fetched items delivered to the
# renderer; the renderer performs no I/O beyond this bounded payload.
BOUND_BINDING_DEFAULT_LIMITS = {
    "CollectionSearch": 50,
    "CollectionFilter": 50,
    "RelatedItems": 8,
}
FILTER_FIELD_DESCRIPTOR_LIMIT = 32


class ProjectionError(RuntimeError):
    """A stable, non-leaking projection failure."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class RenderPageRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    authority: str
    path: str
    locale: str | None = None

    @field_validator("locale")
    @classmethod
    def locale_is_bounded(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            return normalize_locale(value.strip())
        except Exception:
            raise ValueError("invalid locale") from None


class RenderPreviewRequest(RenderPageRequest):
    workspace_id: UUID
    session_token: SecretStr | None = Field(default=None, exclude=True, repr=False)
    browser_token: SecretStr | None = Field(default=None, exclude=True, repr=False)
    browser_route: str | None = None

    @field_validator("browser_route")
    @classmethod
    def browser_route_is_normalized(cls, value: str | None) -> str | None:
        return normalize_preview_route(value) if value is not None else None


class RenderReviewRequest(RenderPageRequest):
    """Faithful frozen review read: one COMPLETE review-snapshot/v2.

    The human session rides the x-slaif-human-session header exactly
    as preview does; the snapshot id identifies the immutable input.
    """

    snapshot_id: UUID
    session_token: SecretStr | None = Field(default=None, exclude=True, repr=False)


class ProjectionMedia(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str
    mime_type: str
    size_bytes: int


class ProjectionNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    component_type: str
    schema_version: str
    parent_id: UUID | None
    slot_key: str
    order_key: int
    props: dict[str, Any]
    media: ProjectionMedia | None = None
    media_items: tuple[ProjectionMedia | None, ...] | None = None
    children: tuple[ProjectionNode, ...] = ()


class ProjectionComposition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str
    catalog_version: str
    nodes: tuple[ProjectionNode, ...]


class ProjectionPage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    site_id: UUID
    slug: str
    title: str
    status: str
    locale: str
    parent_id: UUID | None
    route_template: str | None
    effective_route: str
    row_version: int


class ProjectionSite(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    key: str
    canonical_revision: int


class ProjectionLocale(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    site_id: UUID
    tag: str
    enabled: bool
    is_default: bool
    position: int
    metadata: dict[str, Any]
    switcher_href: str | None = None


class ProjectionNavigationTarget(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["PAGE", "INTERNAL", "EXTERNAL"]
    value: str


class ProjectionNavigationItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    site_id: UUID
    navigation_id: UUID
    parent_id: UUID | None
    page_id: UUID | None
    locale: str | None
    position: int
    label: str
    labels: dict[str, Any]
    target: ProjectionNavigationTarget
    children: tuple[ProjectionNavigationItem, ...] = ()


class ProjectionNavigation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    site_id: UUID
    key: str
    label: str
    labels: dict[str, Any]
    settings: dict[str, Any]
    items: tuple[ProjectionNavigationItem, ...]


class ProjectionRedirect(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str
    target: str
    status_code: Literal[301, 302, 303, 307, 308]
    locale: str | None


class ProjectionRegionEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str
    href: str


class ProjectionRegion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    region_key: Literal["header", "footer"]
    variant: Literal["institutional", "minimal", "multi-column", "single-column"]
    entries: tuple[ProjectionRegionEntry, ...] = ()
    note: str | None = None
    row_version: int


class ProjectionAncestor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    effective_route: str


class RenderPageProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    route_kind: Literal["page"] = "page"
    render_mode: str
    site: ProjectionSite
    requested_path: str
    matched_path: str
    locale: str
    page: ProjectionPage
    route_parameters: dict[str, str] = Field(default_factory=dict)
    composition: ProjectionComposition
    theme: ThemeRecord
    page_style: ThemeRecord
    locales: tuple[ProjectionLocale, ...] = ()
    navigation: tuple[ProjectionNavigation, ...] = ()
    bindings: dict[str, tuple[dict[str, Any], ...]] = Field(default_factory=dict)
    binding_meta: dict[str, dict[str, Any]] = Field(default_factory=dict)
    regions: tuple[ProjectionRegion, ...] = ()
    ancestors: tuple[ProjectionAncestor, ...] = ()
    default_locale: str


class RenderRedirectProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    route_kind: Literal["redirect"] = "redirect"
    render_mode: str
    site: ProjectionSite
    requested_path: str
    matched_path: str
    locale: str
    locales: tuple[ProjectionLocale, ...] = ()
    redirect: ProjectionRedirect


RenderRouteProjection = Annotated[
    RenderPageProjection | RenderRedirectProjection,
    Field(discriminator="route_kind"),
]


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


def _json_value(value: Any) -> Any:
    if isinstance(value, str):
        import json

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ProjectionError("malformed_json") from None
    return value


def _validate_nested(value: Any, *, depth: int = 0) -> None:
    if depth > 8:
        raise ProjectionError("props_depth")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or key.lower() in {
                "innerhtml",
                "dangerouslysetinnerhtml",
                "style",
                "onclick",
                "onload",
                "script",
                "eval",
                "handler",
                "html",
            }:
                raise ProjectionError("executable_prop")
            _validate_nested(child, depth=depth + 1)
    elif isinstance(value, list):
        for child in value:
            _validate_nested(child, depth=depth + 1)
    elif isinstance(value, str) and value.casefold().startswith(
        ("javascript:", "data:", "file:", "vbscript:")
    ):
        raise ProjectionError("unsafe_value")


def _validate_props(component_type: str, props: dict[str, Any]) -> None:
    try:
        validate_agent_component_props(component_type, props, {})
    except ValueError as error:
        message = str(error)
        reason = {
            "unknown prop": "unknown_prop",
            "missing prop": "missing_prop",
            "prop reference": "prop_reference",
            "prop enum": "prop_enum",
            "prop bound": "prop_bound",
            "executable prop": "executable_prop",
            "unsafe value": "unsafe_value",
            "props depth exceeded": "props_depth",
            "props too large": "props_too_large",
        }.get(message, "prop_type")
        raise ProjectionError(reason) from None


MAX_LOCALES = 32
MAX_NAVIGATIONS = 16
MAX_NAVIGATION_ITEMS = 256
MAX_NAVIGATION_DEPTH = 8
MAX_REDIRECTS = 256
MAX_REDIRECT_CHAIN = 16
MAX_JSON_BYTES = 16_384


@asynccontextmanager
async def _repeatable_read_cow(
    pool: Any, *, session_id: UUID, acquire_timeout: float
) -> AsyncIterator[Any]:
    """Start the foundation-owned COW transaction at repeatable-read isolation."""

    async with pool.acquire(timeout=acquire_timeout) as connection:
        await connection.execute(
            "SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL REPEATABLE READ"
        )
        try:
            async with asyncpg_cow_session(connection, session_id=session_id) as cow:
                yield cow
        finally:
            await connection.execute(
                "SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL "
                "READ COMMITTED"
            )


def _bounded_object(value: Any, *, reason: str) -> dict[str, Any]:
    parsed = _json_value(value)
    if not isinstance(parsed, dict):
        raise ProjectionError(reason)
    import json

    if (
        len(json.dumps(parsed, separators=(",", ":"), ensure_ascii=True))
        > MAX_JSON_BYTES
    ):
        raise ProjectionError(reason)
    _validate_nested(parsed)
    return parsed


def _frozen_local_match_prefix(request: RenderPageRequest) -> str | None:
    """The frozen review path's request validation (no addressing).

    The internal review route receives the SITE-LOCAL route (``/``,
    ``/draft``, ...) plus the request authority as plain client
    strings.  The frozen surface carries no domain mappings and the
    076 authorize function has already bound the site/workspace, so
    the authority is never used for identity (R5); both inputs are
    strictly validated - a malformed authority/path or a reserved
    top-level segment is a uniform refusal, never guessed and never
    a live lookup.  The empty prefix tells :func:`_route_parts` to
    use the path verbatim as the local route.
    """
    try:
        normalize_authority(request.authority)
        normalized = normalize_request_path(request.path)
    except Exception:
        raise ProjectionError("not_found") from None
    if path_is_reserved(normalized):
        raise ProjectionError("not_found") from None
    return None


def _route_parts(
    context: SiteContext, path: str, requested_locale: str | None, locales: list[Any]
) -> tuple[str, str]:
    """Return the exact static route and stored locale selected by the path."""

    try:
        normalized = normalize_request_path(path)
        prefix = normalize_request_path(
            (context.matched_path_prefix or "/").rstrip("/") or "/"
        )
    except Exception:
        raise ProjectionError("not_found") from None
    if path_is_reserved(normalized):
        raise ProjectionError("not_found")
    if prefix != "/":
        if normalized != prefix and not normalized.startswith(prefix + "/"):
            raise ProjectionError("not_found")
        normalized = normalized[len(prefix) :] or "/"
    if path_is_reserved(normalized):
        raise ProjectionError("not_found")

    by_lower = {str(row[2]).casefold(): row for row in locales if row[3]}
    default_rows = [row for row in locales if row[3] and row[4]]
    if len(default_rows) != 1:
        raise ProjectionError("locale_state")
    default_tag = str(default_rows[0][2])
    segments = normalized.strip("/").split("/") if normalized != "/" else []
    selected_tag = default_tag
    route = normalized
    if segments and segments[0].casefold() in by_lower:
        selected_tag = str(by_lower[segments[0].casefold()][2])
        if selected_tag.casefold() == default_tag.casefold():
            # Default locales have no prefix in the effective-route contract.
            raise ProjectionError("not_found")
    if requested_locale is not None and (
        requested_locale.casefold() != selected_tag.casefold()
    ):
        raise ProjectionError("not_found")
    return route, selected_tag


def _page_route(row: Any) -> str:
    route = row[8]
    if not isinstance(route, str) or not route.startswith("/"):
        raise ProjectionError("invalid_route")
    if route.endswith("/{slug}"):
        prefix = route[:-6]
        if not prefix.endswith("/"):
            raise ProjectionError("invalid_route")
        try:
            validate_internal_route(prefix[:-1] or "/")
        except ValueError:
            raise ProjectionError("invalid_route") from None
        return route
    try:
        normalized = validate_internal_route(route)
    except ValueError:
        raise ProjectionError("invalid_route") from None
    if normalized.casefold() != route.casefold():
        raise ProjectionError("invalid_route")
    return route


def _redirect_location(
    redirect: ProjectionRedirect,
    *,
    context: SiteContext,
    request: RenderPageRequest,
    render_mode: str,
) -> ProjectionRedirect:
    if not redirect.target.startswith("/"):
        return redirect
    if render_mode == "preview":
        workspace_id = getattr(request, "workspace_id", None)
        if workspace_id is None:
            raise ProjectionError("redirect_state")
        site_prefix = (context.matched_path_prefix or "/").rstrip("/") or "/"
        prefix = f"/preview/{workspace_id}"
        if site_prefix != "/":
            prefix += site_prefix
    else:
        prefix = (context.matched_path_prefix or "/").rstrip("/") or "/"
    target = redirect.target
    location = target if prefix == "/" else prefix + ("" if target == "/" else target)
    return redirect.model_copy(update={"target": location})


def _node_tree(
    rows: list[Any], *, page_id: UUID, site_id: UUID
) -> tuple[ProjectionNode, ...]:
    if len(rows) > MAX_NODES:
        raise ProjectionError("composition_too_large")
    by_id: dict[UUID, dict[str, Any]] = {}
    children: defaultdict[UUID | None, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        node_id = row[0]
        if node_id in by_id or row[1] != site_id or row[2] != page_id:
            raise ProjectionError("composition_scope")
        component_type = str(row[3])
        if component_type not in CATALOG_TYPES or str(row[4]) != "1":
            raise ProjectionError("unknown_component")
        props = _json_value(row[8])
        if not isinstance(props, dict):
            raise ProjectionError("invalid_props")
        import json

        if len(json.dumps(props, separators=(",", ":"))) > MAX_PROPS_BYTES:
            raise ProjectionError("props_too_large")
        forbidden_keys = {
            "innerhtml",
            "dangerouslysetinnerhtml",
            "onclick",
            "onload",
            "script",
            "eval",
        }
        if any(key.lower() in forbidden_keys for key in props):
            raise ProjectionError("executable_prop")
        _validate_props(component_type, props)
        # Defense in depth: re-validate embed props against the bounded policy
        # at projection time so the renderer can never receive an
        # un-canonicalizable embed (R1 is pure and deterministic).
        if component_type == "VideoEmbed":
            ok, _key = validate_video_embed_props(props)
        elif component_type == "MapBlock":
            ok, _key = validate_map_embed_props(props)
        else:
            ok = True
        if not ok:
            raise ProjectionError("embed_props_invalid")
        item = {
            "id": node_id,
            "component_type": component_type,
            "schema_version": str(row[4]),
            "parent_id": row[5],
            "slot_key": str(row[6]),
            "order_key": int(row[7]),
            "props": props,
        }
        by_id[node_id] = item
        children[row[5]].append(item)

    for parent_id, items in children.items():
        if parent_id is not None and parent_id not in by_id:
            raise ProjectionError("missing_parent")
        items.sort(
            key=lambda value: (
                value["slot_key"],
                value["order_key"],
                value["id"].hex,
            )
        )
        if parent_id is not None and len(items) > MAX_CHILDREN.get(
            by_id[parent_id]["component_type"], MAX_NODES
        ):
            raise ProjectionError("too_many_children")
        allowed = (
            frozenset({"default"})
            if parent_id is None
            else ALLOWED_SLOTS.get(by_id[parent_id]["component_type"], frozenset())
        )
        if any(item["slot_key"] not in allowed for item in items):
            raise ProjectionError("invalid_slot")

    visiting: set[UUID] = set()
    visited: set[UUID] = set()

    def build(item: dict[str, Any], depth: int) -> ProjectionNode:
        if depth > MAX_DEPTH or item["id"] in visiting:
            raise ProjectionError("composition_cycle")
        if item["id"] in visited:
            raise ProjectionError("duplicate_node")
        visiting.add(item["id"])
        child_nodes = tuple(build(child, depth + 1) for child in children[item["id"]])
        visiting.remove(item["id"])
        visited.add(item["id"])
        return ProjectionNode(**item, children=child_nodes)

    roots = tuple(build(item, 0) for item in children[None])
    if len(visited) != len(by_id):
        raise ProjectionError("unreachable_node")
    return roots


def _page(row: Any) -> ProjectionPage:
    return ProjectionPage(
        id=row[0],
        site_id=row[1],
        slug=row[2],
        title=row[3],
        status=row[4],
        locale=row[5],
        parent_id=row[6],
        route_template=row[7],
        effective_route=_page_route(row),
        row_version=int(row[9]),
    )


def _page_from_fact(fact: RenderPageFact, effective_route: str) -> ProjectionPage:
    """Build the page projection from a shared-port winner fact.

    The row tuple carries the exact 056 columns the legacy row path
    consumed; ``_page``/``_page_route`` remain the single
    construction/validation point (the service's own route-shape
    invariant is re-checked, never bypassed).
    """
    row = (
        fact.id,
        fact.site_id,
        fact.slug,
        fact.title,
        fact.status,
        fact.locale,
        fact.parent_id,
        fact.route_template,
        effective_route,
        fact.row_version,
    )
    return _page(row)


def _label_map(value: Any) -> dict[str, Any]:
    labels = _bounded_object(value, reason="navigation_labels")
    for key, label in labels.items():
        if not isinstance(key, str) or not isinstance(label, str) or not label.strip():
            raise ProjectionError("navigation_labels")
    return labels


def _flatten(nodes: tuple[ProjectionNode, ...]) -> tuple[ProjectionNode, ...]:
    result: list[ProjectionNode] = []

    def visit(node: ProjectionNode) -> None:
        result.append(node)
        for child in node.children:
            visit(child)

    for node in nodes:
        visit(node)
    return tuple(result)


MEDIA_MIME_CLASSES = frozenset({"image/png", "image/jpeg"})
DOCUMENT_MIME_CLASSES = frozenset({"application/pdf"})


def _media_descriptor(
    *,
    render_mode: str,
    site_id: UUID,
    media_id: UUID,
    row: Any,
    mime_classes: frozenset[str] = MEDIA_MIME_CLASSES,
    snapshot_id: UUID | None = None,
    preview_workspace_id: UUID | None = None,
    preview_bound: bool = False,
) -> ProjectionMedia | None:
    """Pure resolved-row to descriptor classification (079/1 + 079/2 lists +
    079/3 document class, 083/5 frozen review URL).

    Fail-closed: a missing row, a row outside the component's MIME class
    (image class for Image/Gallery/LogoGrid, document class for
    DocumentList), or a non-public row under the canonical render mode
    yields ``None`` so the trusted renderer shows the bounded placeholder
    instead of an ``<img>`` or a document link.

    The frozen review mode uses the snapshot-authorized byte URL for
    BOTH stored publication statuses: the 076 gate binds the human
    session to the snapshot and its stored frozen media map, and the
    anonymous public digest URL is deliberately NOT an option there
    because public byte reads depend on current canonical references
    that are not frozen input.

    The preview mode emits ONLY the byte URL that the trusted preview
    context can actually authorize: the human preview carries the
    authorize-verified workspace id (workspace-scoped 054 preview
    chain) and the confined bound run carries the run-bound token URL
    (the 076 binding gate derives site/workspace from the stored run
    facts).  A preview context without a trusted workspace/binding
    fails closed to the placeholder instead of a site-wide URL, and
    no cookie, agent capability or token ever enters the URL.
    """
    if row is None:
        return None
    mime_type = str(row[0])
    size_bytes = int(row[1])
    content_hash = str(row[2])
    public_status = str(row[3])
    if mime_type not in mime_classes:
        return None
    if render_mode == "review":
        if snapshot_id is None:
            return None
        url = f"/media/v1/review/{snapshot_id}/assets/{media_id}/content"
    elif render_mode == "preview":
        if preview_bound:
            url = f"/media/v1/browser-preview/assets/{media_id}/content"
        elif preview_workspace_id is not None:
            url = (
                f"/media/v1/sites/{site_id}/workspaces/{preview_workspace_id}"
                f"/preview/assets/{media_id}/content"
            )
        else:
            return None
    else:
        if public_status != "public":
            return None
        url = (
            f"/media/public/sha256/{content_hash[:2]}/"
            f"{content_hash[2:4]}/{content_hash}"
        )
    return ProjectionMedia(url=url, mime_type=mime_type, size_bytes=size_bytes)


def _attach_media(
    nodes: tuple[ProjectionNode, ...],
    descriptors: dict[UUID, ProjectionMedia],
    list_descriptors: dict[UUID, tuple[ProjectionMedia | None, ...]],
) -> tuple[ProjectionNode, ...]:
    result: list[ProjectionNode] = []
    for node in nodes:
        attached = _attach_media(node.children, descriptors, list_descriptors)
        result.append(
            node.model_copy(
                update={
                    "children": attached,
                    "media": descriptors.get(node.id),
                    "media_items": list_descriptors.get(node.id),
                }
            )
        )
    return tuple(result)


async def _collection_bindings(
    surface: fs.RenderReadSurface,
    *,
    nodes: tuple[ProjectionNode, ...],
    site_id: UUID,
    render_mode: str,
    selected_locale: str,
    default_locale: str,
    route_parameter: str | None,
) -> tuple[
    dict[str, tuple[dict[str, Any], ...]],
    dict[str, dict[str, Any]],
]:
    bindings: dict[str, tuple[dict[str, Any], ...]] = {}
    binding_meta: dict[str, dict[str, Any]] = {}
    for node in _flatten(nodes):
        if node.component_type not in COLLECTION_BINDING_TYPES:
            continue
        raw_view_id = node.props.get("viewId", node.props.get("view_id"))
        try:
            view_id = UUID(str(raw_view_id))
        except (TypeError, ValueError):
            raise ProjectionError("invalid_collection_view") from None
        try:
            view = await surface.fetch_collection_view(view_id=view_id)
        except fs.SurfaceReadError as exc:
            raise ProjectionError("collection_scope") from exc
        if view is None or view[1] != site_id:
            raise ProjectionError("collection_scope")
        filter_spec = _json_value(view[4])
        sort_spec = _json_value(view[5])
        projection_spec = _json_value(view[6])
        pagination_spec = _json_value(view[7])
        if not all(
            isinstance(value, dict)
            for value in (filter_spec, sort_spec, pagination_spec)
        ):
            raise ProjectionError("unsupported_collection_query")
        try:
            type_row = await surface.fetch_content_type(type_id=view[2])
        except fs.SurfaceReadError as exc:
            raise ProjectionError("collection_scope") from exc
        if type_row is None or type_row[0] != site_id:
            raise ProjectionError("collection_scope")
        if type_row[1] != "ACTIVE":
            raise ProjectionError("collection_scope")
        if type_row[2] != view[8]:
            raise ProjectionError("stale_collection_definition")
        try:
            field_rows = list(await surface.fetch_field_definitions(type_id=view[2]))
        except fs.SurfaceReadError as exc:
            raise ProjectionError("unsupported_collection_query") from exc
        field_defs = [
            SimpleNamespace(
                key=row[0],
                field_type=row[1],
                localized=row[2],
                validation=_json_value(row[3]) or {},
                cardinality=row[4],
                required=row[5],
            )
            for row in field_rows
        ]
        try:
            validate_query_contract(
                filter_spec,
                sort_spec,
                projection_spec,
                pagination_spec,
                field_defs,
                allow_localized_projection=True,
            )
        except (TypeError, ValueError):
            raise ProjectionError("unsupported_collection_query") from None
        projection_fields = (
            projection_spec.get("fields", [])
            if isinstance(projection_spec, dict)
            else projection_spec
        )
        statuses = (
            ["PUBLISHED"] if render_mode == "canonical" else ["PUBLISHED", "DRAFT"]
        )
        requested_status = filter_spec.get("status")
        if requested_status is not None:
            if requested_status not in statuses:
                raise ProjectionError("collection_status")
            statuses = [requested_status]
        default_limit = pagination_spec.get("limit", 24)
        requested_limit = node.props.get(
            "limit",
            BOUND_BINDING_DEFAULT_LIMITS.get(node.component_type, default_limit),
        )
        if (
            isinstance(requested_limit, bool)
            or not isinstance(requested_limit, int)
            or not 1 <= requested_limit <= MAX_PAGE_SIZE
        ):
            raise ProjectionError("collection_limit")
        if node.component_type in BOUND_BINDING_DEFAULT_LIMITS:
            pagination_limit = pagination_spec.get("limit")
            if (
                isinstance(pagination_limit, int)
                and not isinstance(pagination_limit, bool)
                and 1 <= pagination_limit <= MAX_PAGE_SIZE
            ):
                requested_limit = min(requested_limit, pagination_limit)
        offset = pagination_spec.get("offset", 0)
        try:
            candidate_count = await surface.count_content_items(
                site_id=site_id,
                type_id=view[2],
                statuses=statuses,
            )
        except fs.SurfaceReadError as exc:
            raise ProjectionError("query_cost") from exc
        if not isinstance(candidate_count, int) or candidate_count > MAX_CANDIDATES:
            raise ProjectionError("query_cost")
        try:
            rows = list(
                await surface.fetch_content_items(
                    site_id=site_id, type_id=view[2], statuses=statuses
                )
            )
        except fs.SurfaceReadError as exc:
            raise ProjectionError("query_cost") from exc
        if len(rows) > MAX_CANDIDATES:
            raise ProjectionError("query_cost")
        items: list[dict[str, Any]] = []
        for row in rows:
            if row[1] != site_id or row[2] != view[2]:
                raise ProjectionError("collection_scope")
            if int(row[6]) != int(type_row[2]) or int(row[6]) != int(view[8]):
                raise ProjectionError("stale_collection_definition")
            values = _json_value(row[5])
            if not isinstance(values, dict):
                raise ProjectionError("malformed_item")
            try:
                validate_values(values, cast(Any, field_defs))
            except (TypeError, ValueError):
                raise ProjectionError("malformed_item") from None
            if not matches_filter(
                filter_spec, values, slug=str(row[3]), status=str(row[4])
            ):
                continue
            if (
                node.component_type == "CollectionDetail"
                and route_parameter is not None
                and str(row[3]) != route_parameter
            ):
                continue
            if (
                node.component_type == "RelatedItems"
                and route_parameter is not None
                and str(row[3]) == route_parameter
            ):
                continue
            items.append(
                {
                    "id": row[0],
                    "site_id": row[1],
                    "type_id": row[2],
                    "slug": row[3],
                    "status": row[4],
                    # Keep all validated values available to the shared sort
                    # evaluator; projection is applied only after ordering.
                    "values": values,
                }
            )
        if node.component_type == "RelatedItems" and route_parameter is None:
            items = []
        try:
            sort_collection_items(items, sort_spec)
        except (TypeError, ValueError):
            raise ProjectionError("malformed_item") from None
        if (
            node.component_type == "CollectionDetail"
            and route_parameter is not None
            and len(items) != 1
        ):
            raise ProjectionError("not_found")
        if node.component_type == "CollectionDetail" and route_parameter is not None:
            page = items[:1]
        elif node.component_type in BOUND_BINDING_DEFAULT_LIMITS:
            page = items[:requested_limit]
        else:
            page = items[offset : offset + requested_limit]
        translation_by_item: dict[UUID, dict[str, dict[str, Any]]] = defaultdict(dict)
        if page:
            try:
                translation_rows = await surface.fetch_content_item_translations(
                    site_id=site_id,
                    item_ids=[item["id"] for item in page],
                    locales=list(dict.fromkeys((selected_locale, default_locale))),
                )
            except fs.SurfaceReadError as exc:
                raise ProjectionError("malformed_translation") from exc
            for translation in translation_rows:
                item_id = translation[0]
                locale = str(translation[1])
                if locale in translation_by_item[item_id]:
                    raise ProjectionError("translation_ambiguous")
                localized_values = _json_value(translation[2])
                if not isinstance(localized_values, dict):
                    raise ProjectionError("malformed_translation")
                try:
                    validate_values(
                        localized_values, cast(Any, field_defs), localized=True
                    )
                except (TypeError, ValueError):
                    raise ProjectionError("malformed_translation") from None
                translation_by_item[item_id][locale] = localized_values

        projected_items: list[dict[str, Any]] = []
        for item in page:
            selected_values = translation_by_item[item["id"]].get(selected_locale, {})
            default_values = translation_by_item[item["id"]].get(default_locale, {})
            projected_values: dict[str, Any] = {}
            for field in projection_fields:
                definition = next(
                    (candidate for candidate in field_defs if candidate.key == field),
                    None,
                )
                if definition is None:
                    raise ProjectionError("malformed_projection")
                if definition.localized:
                    if field in selected_values:
                        projected_values[field] = selected_values[field]
                    elif field in default_values:
                        projected_values[field] = default_values[field]
                    else:
                        raise ProjectionError("missing_localized_value")
                else:
                    if field not in item["values"]:
                        raise ProjectionError("missing_projection_value")
                    projected_values[field] = item["values"][field]
            projected_items.append({**item, "values": projected_values})
        bindings[str(node.id)] = tuple(projected_items)
        if node.component_type in ("CollectionSearch", "CollectionFilter"):
            binding_meta[str(node.id)] = {
                "filter_fields": [
                    {"key": field.key, "primitive": field.field_type}
                    for field in field_defs[:FILTER_FIELD_DESCRIPTOR_LIMIT]
                ]
            }
    return bindings, binding_meta


def _dynamic_route_parameter(page_route: str, matched_route: str) -> str | None:
    if not page_route.endswith("/{slug}"):
        return None
    prefix = page_route[:-6]
    if not prefix.endswith("/") or not matched_route.casefold().startswith(
        prefix.casefold()
    ):
        raise ProjectionError("not_found")
    parameter = matched_route[len(prefix) :]
    if not parameter or "/" in parameter:
        raise ProjectionError("not_found")
    return parameter


class RenderProjectionService:
    """Project only trusted bounded page data from one Render pool."""

    def __init__(
        self,
        database: Any,
        *,
        browser_verifier: BrowserPreviewCredentialSigner | None = None,
    ) -> None:
        self._database = database
        self._browser_verifier = browser_verifier

    async def _context(self, request: RenderPageRequest) -> SiteContext:
        try:
            return cast(
                SiteContext,
                await self._database.resolver().resolve(
                    request.authority, request.path
                ),
            )
        except Exception as error:
            if getattr(error, "reason", None) == "not_found":
                raise ProjectionError("not_found") from None
            raise ProjectionError("unavailable") from None

    async def _context_on_connection(
        self, connection: Any, request: RenderPageRequest
    ) -> SiteContext:
        try:
            return cast(
                SiteContext,
                await self._database.resolver().resolve_on_connection(
                    connection, request.authority, request.path
                ),
            )
        except Exception as error:
            if getattr(error, "reason", None) == "not_found":
                raise ProjectionError("not_found") from None
            if getattr(error, "reason", None) == "conflict":
                raise ProjectionError("not_found") from None
            raise ProjectionError("unavailable") from None

    async def _locales(
        self, surface: fs.RenderReadSurface, *, site_id: UUID
    ) -> tuple[list[Any], tuple[ProjectionLocale, ...], str]:
        try:
            rows = list(await surface.fetch_locales(site_id=site_id))
        except fs.SurfaceReadError as exc:
            raise ProjectionError("locale_state") from exc
        if not rows or len(rows) > MAX_LOCALES:
            raise ProjectionError("locale_state")
        seen: set[str] = set()
        default_rows: list[Any] = []
        projected: list[ProjectionLocale] = []
        for row in rows:
            if row[1] != site_id:
                raise ProjectionError("locale_scope")
            try:
                tag = normalize_locale(str(row[2]))
            except Exception:
                raise ProjectionError("locale_state") from None
            if tag != row[2] or tag.casefold() in seen:
                raise ProjectionError("locale_state")
            seen.add(tag.casefold())
            metadata = _bounded_object(row[6], reason="locale_metadata")
            if bool(row[4]):
                default_rows.append(row)
            if bool(row[3]):
                projected.append(
                    ProjectionLocale(
                        id=row[0],
                        site_id=row[1],
                        tag=tag,
                        enabled=True,
                        is_default=bool(row[4]),
                        position=int(row[5]),
                        metadata=metadata,
                    )
                )
        if len(default_rows) != 1 or not bool(default_rows[0][3]):
            raise ProjectionError("locale_state")
        if len(projected) != len([row for row in rows if row[3]]):
            raise ProjectionError("locale_state")
        return rows, tuple(projected), str(default_rows[0][2])

    @staticmethod
    def _locale_target_route(
        current_route: str, current_locale: str, default_locale: str, target_locale: str
    ) -> str:
        """Effective-route contract: re-root the current page under the tag.

        Default-locale pages carry no locale prefix; other locales are
        prefixed with their tag.  The target keeps the same site-relative
        path under the target tag.
        """
        rest = current_route
        if current_locale.casefold() != default_locale.casefold():
            # Request routes arrive NORMALIZED (lowercased) while stored
            # locale tags keep their configured casing (for example
            # ``sl-SI``); prefix recognition must therefore compare
            # case-folded exactly like the route resolver, while the
            # re-prefixed target keeps the stored tag verbatim.
            prefix = f"/{current_locale}/"
            if rest.casefold().startswith(prefix.casefold()):
                rest = f"/{rest[len(prefix) :]}"
            elif rest.casefold() == f"/{current_locale}".casefold():
                rest = "/"
        if target_locale.casefold() == default_locale.casefold():
            # Default-locale routes carry no locale prefix.
            return rest
        if rest == "/":
            return f"/{target_locale}"
        return f"/{target_locale}{rest}"

    def _locale_switcher(
        self,
        *,
        facts: dict[UUID, RenderPageFact],
        memo: fs._RouteMemo,
        site_id: UUID,
        locales: tuple[ProjectionLocale, ...],
        current_locale: str,
        default_locale: str,
        current_route: str,
        statuses: list[str],
        enabled_tags: frozenset[str],
    ) -> tuple[ProjectionLocale, ...]:
        resolved: list[ProjectionLocale] = []
        for locale in locales:
            if locale.tag.casefold() == current_locale.casefold():
                resolved.append(locale)
                continue
            target = self._locale_target_route(
                current_route, current_locale, default_locale, locale.tag
            )
            # The resolver validates and matches routes case-insensitively
            # on lowercased input, mirroring normalize_request_path; the
            # stored tag case of the resolved page is what switcher_href
            # reports.  A zero-row result keeps the locale as-is; an
            # ambiguity keeps the legacy outcome and propagates as
            # unavailable (the SQL raised inside the fetch).
            fact = self._resolve_page_fact(
                facts=facts,
                memo=memo,
                site_id=site_id,
                route=target.lower(),
                locale=locale.tag,
                statuses=statuses,
                default_locale=default_locale,
                enabled_tags=enabled_tags,
            )
            if fact is None:
                resolved.append(locale)
                continue
            # The href is the CONCRETE re-rooted route that the resolver
            # just matched: memo.route(fact.id) is the effective route,
            # which carries the ``/{slug}`` template for dynamic pages and
            # would emit brace-bearing inert links for valid counterparts.
            # For static counterparts the two are byte-identical.
            resolved.append(locale.model_copy(update={"switcher_href": target}))
        return tuple(resolved)

    @staticmethod
    def _resolve_page_fact(
        *,
        facts: dict[UUID, RenderPageFact],
        memo: fs._RouteMemo,
        site_id: UUID,
        route: str,
        locale: str,
        statuses: list[str],
        default_locale: str,
        enabled_tags: frozenset[str],
    ) -> RenderPageFact | None:
        """Shared 056 winner selection (the port both paths execute).

        ``None`` is the SQL's zero-row result (not_found at the
        service level); RENDER_ROUTE_AMBIGUOUS / RENDER_ROUTE_INVALID
        keep the legacy outcome - the SQL raised inside the fetch and
        the service mapped that PostgresError to unavailable.
        """
        try:
            fact = resolve_page_route(
                facts,
                site_id=site_id,
                route=route,
                locale=locale,
                statuses=statuses,
                default_locale=default_locale,
                enabled_tags=enabled_tags,
                route_memo=memo,
            )
        except fs.SurfaceReadError as exc:
            raise ProjectionError("unavailable") from exc
        if fact is not None and (
            fact.site_id != site_id or fact.locale.casefold() != locale.casefold()
        ):
            raise ProjectionError("not_found")
        return fact

    async def _redirects(
        self,
        surface: fs.RenderReadSurface,
        *,
        facts: dict[UUID, RenderPageFact],
        memo: fs._RouteMemo,
        site_id: UUID,
        route: str,
        locale: str,
        default_locale: str,
        statuses: list[str],
        enabled_tags: frozenset[str],
    ) -> ProjectionRedirect | None:
        try:
            rows = list(await surface.fetch_redirects(site_id=site_id))
        except fs.SurfaceReadError as exc:
            raise ProjectionError("redirect_state") from exc
        redirects: dict[tuple[str, str | None], ProjectionRedirect] = {}
        try:
            enabled = {
                tag.casefold()
                for (tag,) in await surface.fetch_enabled_locale_tags(site_id=site_id)
            }
        except fs.SurfaceReadError as exc:
            raise ProjectionError("locale_state") from exc
        for row in rows:
            if row[1] != site_id:
                raise ProjectionError("redirect_scope")
            try:
                source = validate_redirect_source(str(row[2]))
                target = validate_redirect_target(str(row[3]))
            except ValueError:
                raise ProjectionError("redirect_state") from None
            if source != row[2] or (target.startswith("/") and target != row[3]):
                raise ProjectionError("redirect_state")
            selected_locale = row[5]
            if selected_locale is not None:
                try:
                    canonical_locale = normalize_locale(str(selected_locale))
                except Exception:
                    raise ProjectionError("redirect_state") from None
                if (
                    canonical_locale != selected_locale
                    or canonical_locale.casefold() not in enabled
                ):
                    raise ProjectionError("redirect_state")
            else:
                canonical_locale = None
            try:
                status_code = int(row[4])
                if status_code not in {301, 302, 303, 307, 308}:
                    raise ValueError
                redirect = ProjectionRedirect(
                    source=source,
                    target=target,
                    status_code=cast(Literal[301, 302, 303, 307, 308], status_code),
                    locale=canonical_locale,
                )
            except Exception:
                raise ProjectionError("redirect_state") from None
            key = (source, canonical_locale)
            if key in redirects:
                raise ProjectionError("redirect_ambiguous")
            redirects[key] = redirect

        for redirect in redirects.values():
            # a zero-row source is the valid case; a found source page
            # makes the redirect ambiguous; an ambiguous/invalid route
            # propagates as unavailable, exactly as the legacy SQL
            # exception inside the fetch did
            source_fact = self._resolve_page_fact(
                facts=facts,
                memo=memo,
                site_id=site_id,
                route=redirect.source,
                locale=redirect.locale or default_locale,
                statuses=statuses,
                default_locale=default_locale,
                enabled_tags=enabled_tags,
            )
            if source_fact is not None:
                raise ProjectionError("redirect_ambiguous")

        async def validate_chain(redirect: ProjectionRedirect) -> None:
            if not redirect.target.startswith("/"):
                return
            chain_locale = redirect.locale or default_locale
            cursor = redirect.target
            visited: set[tuple[str, str | None]] = set()
            for _ in range(MAX_REDIRECT_CHAIN):
                key = (cursor, chain_locale)
                if key in visited:
                    raise ProjectionError("redirect_cycle")
                visited.add(key)
                next_redirect = (
                    redirects.get(key) if redirect.locale is not None else None
                ) or redirects.get((cursor, None))
                if next_redirect is not None:
                    if not next_redirect.target.startswith("/"):
                        return
                    cursor = next_redirect.target
                    continue
                cursor_fact = self._resolve_page_fact(
                    facts=facts,
                    memo=memo,
                    site_id=site_id,
                    route=cursor,
                    locale=chain_locale,
                    statuses=statuses,
                    default_locale=default_locale,
                    enabled_tags=enabled_tags,
                )
                if cursor_fact is None:
                    raise ProjectionError("redirect_dangling")
                return
            raise ProjectionError("redirect_chain")

        for redirect in redirects.values():
            await validate_chain(redirect)
        selected = redirects.get((route, locale)) or redirects.get((route, None))
        return selected

    async def _navigation(
        self,
        surface: fs.RenderReadSurface,
        *,
        facts: dict[UUID, RenderPageFact],
        memo: fs._RouteMemo,
        site_id: UUID,
        selected_locale: str,
        default_locale: str,
        statuses: list[str],
        enabled_tags: frozenset[str],
    ) -> tuple[ProjectionNavigation, ...]:
        try:
            nav_rows = list(await surface.fetch_navigation_definitions(site_id=site_id))
        except fs.SurfaceReadError as exc:
            raise ProjectionError("navigation_too_large") from exc
        if len(nav_rows) > MAX_NAVIGATIONS:
            raise ProjectionError("navigation_too_large")
        # the item-locale check stays casefolded service-side; the
        # exact-case tags drive the shared 059 predicate
        enabled_tags_casefold = {tag.casefold() for tag in enabled_tags}
        nav_by_id: dict[UUID, dict[str, Any]] = {}
        for row in nav_rows:
            if row[1] != site_id or row[0] in nav_by_id:
                raise ProjectionError("navigation_scope")
            base_label = row[3]
            if not isinstance(base_label, str) or not base_label.strip():
                raise ProjectionError("navigation_label")
            labels = _label_map(row[4])
            settings = _bounded_object(row[5], reason="navigation_settings")
            label = labels.get(selected_locale) or labels.get(default_locale)
            if not isinstance(label, str) or not label.strip():
                label = base_label
            nav_by_id[row[0]] = {
                "id": row[0],
                "site_id": row[1],
                "key": row[2],
                "label": label,
                "labels": labels,
                "settings": settings,
            }

        # 059 port over the raw retained items (the shared helper both
        # paths execute): per-item target validation happens here, in
        # item order, before the locale-visibility filtering below.
        try:
            raw_items = await surface.fetch_navigation_items(site_id=site_id)
            item_rows = navigation_resolved_items(
                facts,
                enabled_tags,
                raw_items,
                site_id=site_id,
                locale=selected_locale,
                default_locale=default_locale,
                statuses=statuses,
                route_memo=memo,
            )
        except fs.SurfaceReadError as exc:
            if exc.reason == "navigation_too_large":
                raise ProjectionError("navigation_too_large") from exc
            # a target failure raised inside the SQL port; the legacy
            # service mapped that PostgresError to unavailable
            raise ProjectionError("unavailable") from exc
        if len(item_rows) > MAX_NAVIGATION_ITEMS:
            raise ProjectionError("navigation_too_large")
        all_items: dict[UUID, dict[str, Any]] = {}
        sibling_positions: dict[tuple[UUID, UUID | None], set[int]] = defaultdict(set)
        children: defaultdict[UUID | None, list[dict[str, Any]]] = defaultdict(list)
        for item_row in item_rows:
            if (
                item_row[1] != site_id
                or item_row[2] not in nav_by_id
                or item_row[0] in all_items
                or item_row[3] == item_row[0]
            ):
                raise ProjectionError("navigation_scope")
            item_locale = item_row[8]
            if item_locale is not None and (
                str(item_locale).casefold() not in enabled_tags_casefold
            ):
                raise ProjectionError("navigation_locale")
            position = int(item_row[9])
            sibling_key = (item_row[2], item_row[3])
            if position in sibling_positions[sibling_key]:
                raise ProjectionError("navigation_position")
            sibling_positions[sibling_key].add(position)
            labels = _label_map(item_row[7])
            target_kind = str(item_row[5])
            target_value = str(item_row[10])
            try:
                if target_kind == "EXTERNAL":
                    target_value = validate_external_url(target_value)
                    if not target_value.startswith("https://"):
                        raise ValueError
                elif target_kind == "INTERNAL":
                    target_value = validate_internal_route(target_value)
                elif target_kind == "PAGE":
                    normalized_target = validate_internal_route(target_value)
                    if normalized_target.casefold() != target_value.casefold():
                        raise ValueError
                else:
                    raise ValueError
                target_kind = cast(Literal["PAGE", "INTERNAL", "EXTERNAL"], target_kind)
            except (TypeError, ValueError, ProjectionError):
                raise ProjectionError("navigation_target") from None
            item = {
                "id": item_row[0],
                "site_id": item_row[1],
                "navigation_id": item_row[2],
                "parent_id": item_row[3],
                "page_id": item_row[4],
                "locale": item_locale,
                "position": position,
                "labels": labels,
                "target": ProjectionNavigationTarget(
                    kind=target_kind, value=target_value
                ),
            }
            all_items[item_row[0]] = item
            children[item_row[3]].append(item)

        # Deterministic precedence in corrupted states: every parent
        # binding is validated before any sibling contiguity.  The
        # original 059 FOR loop iterated the unordered physical row
        # set, so this corrupted-state precedence followed row order;
        # the port keeps the fail-closed codes and makes the order
        # stable.
        for navigation_id, parent_id in sibling_positions:
            if parent_id is not None:
                parent = all_items.get(parent_id)
                if parent is None or parent["navigation_id"] != navigation_id:
                    raise ProjectionError("navigation_parent")
        for positions in sibling_positions.values():
            if positions != set(range(len(positions))):
                raise ProjectionError("navigation_position")

        visiting: set[UUID] = set()
        visited: set[UUID] = set()

        def check_tree(item: dict[str, Any], depth: int) -> None:
            item_id = item["id"]
            if depth > MAX_NAVIGATION_DEPTH or item_id in visiting:
                raise ProjectionError("navigation_cycle")
            if item_id in visited:
                raise ProjectionError("navigation_duplicate")
            visiting.add(item_id)
            for child in children[item_id]:
                check_tree(child, depth + 1)
            visiting.remove(item_id)
            visited.add(item_id)

        for navigation_id in nav_by_id:
            roots = [
                item
                for item in children[None]
                if item["navigation_id"] == navigation_id
            ]
            for item in roots:
                check_tree(item, 0)
        if len(visited) != len(all_items):
            raise ProjectionError("navigation_unreachable")

        def project_item(item: dict[str, Any]) -> ProjectionNavigationItem:
            label = item["labels"].get(selected_locale) or item["labels"].get(
                default_locale
            )
            if not isinstance(label, str) or not label.strip():
                raise ProjectionError("navigation_label")
            child_items = tuple(
                project_item(child)
                for child in sorted(
                    children[item["id"]], key=lambda value: value["position"]
                )
                if child["locale"] is None
                or child["locale"].casefold() == selected_locale.casefold()
            )
            if item["parent_id"] is not None and item["parent_id"] not in all_items:
                raise ProjectionError("navigation_parent")
            return ProjectionNavigationItem(
                **{**item, "label": label}, children=child_items
            )

        result: list[ProjectionNavigation] = []
        for navigation_id, navigation in nav_by_id.items():
            projected_roots = tuple(
                project_item(item)
                for item in sorted(children[None], key=lambda value: value["position"])
                if item["navigation_id"] == navigation_id
                and (
                    item["locale"] is None
                    or item["locale"].casefold() == selected_locale.casefold()
                )
            )
            result.append(ProjectionNavigation(**navigation, items=projected_roots))
        return tuple(result)

    async def _regions(
        self,
        surface: fs.RenderReadSurface,
        *,
        facts: dict[UUID, RenderPageFact],
        memo: fs._RouteMemo,
        site_id: UUID,
    ) -> tuple[ProjectionRegion, ...]:
        try:
            rows = list(await surface.fetch_regions(site_id=site_id))
        except fs.SurfaceReadError as exc:
            raise ProjectionError("region_state") from exc
        if len(rows) > 2:
            raise ProjectionError("region_state")
        seen: set[str] = set()
        regions: list[ProjectionRegion] = []
        for row in rows:
            (
                region_id,
                row_site_id,
                region_key,
                variant,
                content,
                _schema_version,
                row_version,
                _created_at,
                _updated_at,
            ) = row
            if row_site_id != site_id:
                raise ProjectionError("region_scope")
            if region_key not in _REGION_VARIANTS or region_key in seen:
                raise ProjectionError("region_state")
            seen.add(str(region_key))
            if variant not in _REGION_VARIANTS[region_key]:
                raise ProjectionError("region_state")
            if not isinstance(row_version, int) or row_version <= 0:
                raise ProjectionError("region_state")
            content = _json_value(content)
            if not isinstance(content, dict):
                raise ProjectionError("region_state")
            note: str | None = None
            if region_key == "header":
                if set(content) != {"nav"} or not isinstance(content["nav"], list):
                    raise ProjectionError("region_state")
                entries_value: list[Any] = content["nav"]
            else:
                if (
                    not {"links"} <= set(content)
                    or set(content) - {"links", "note"}
                    or not isinstance(content["links"], list)
                ):
                    raise ProjectionError("region_state")
                entries_value = content["links"]
                note = content.get("note")
                if note is not None and (not isinstance(note, str) or len(note) > 4096):
                    raise ProjectionError("region_state")
            entries: list[ProjectionRegionEntry] = []
            for entry in entries_value:
                if (
                    not isinstance(entry, dict)
                    or set(entry) != {"label", "target"}
                    or not isinstance(entry["label"], str)
                    or not entry["label"]
                    or len(entry["label"]) > 256
                ):
                    raise ProjectionError("region_state")
                target = entry["target"]
                if not isinstance(target, dict) or set(target) != {"kind", "value"}:
                    raise ProjectionError("region_state")
                kind = target["kind"]
                value = target["value"]
                if not isinstance(value, str) or not value:
                    raise ProjectionError("region_state")
                if kind == "page":
                    try:
                        page_id = UUID(value)
                    except ValueError:
                        raise ProjectionError("region_state") from None
                    try:
                        href = memo.route(page_id)
                    except fs.SurfaceReadError:
                        raise ProjectionError("region_state") from None
                    if not isinstance(href, str) or not href.startswith("/"):
                        raise ProjectionError("region_state")
                elif kind == "internal":
                    try:
                        href = validate_internal_route(value)
                    except ValueError:
                        raise ProjectionError("region_state") from None
                elif kind == "external":
                    try:
                        href = validate_external_url(value)
                    except ValueError:
                        raise ProjectionError("region_state") from None
                else:
                    raise ProjectionError("region_state")
                entries.append(ProjectionRegionEntry(label=entry["label"], href=href))
            if region_key == "header" and not 1 <= len(entries) <= 12:
                raise ProjectionError("region_state")
            if region_key == "footer" and len(entries) > 16:
                raise ProjectionError("region_state")
            regions.append(
                ProjectionRegion(
                    id=region_id,
                    # validated above against _REGION_VARIANTS
                    region_key=cast(Literal["header", "footer"], region_key),
                    variant=cast(
                        Literal[
                            "institutional",
                            "minimal",
                            "multi-column",
                            "single-column",
                        ],
                        variant,
                    ),
                    entries=tuple(entries),
                    note=note,
                    row_version=row_version,
                )
            )
        return tuple(regions)

    @staticmethod
    def _ancestors(
        *,
        facts: dict[UUID, RenderPageFact],
        memo: fs._RouteMemo,
        site_id: UUID,
        page_id: UUID,
    ) -> tuple[ProjectionAncestor, ...]:
        # 067 port: the retained chain (root-to-parent, position 1 at
        # the root side), each row's effective route through the
        # shared memo; a derivation failure keeps the legacy outcome
        # (the SQL raised inside the fetch -> unavailable).
        chain = page_ancestor_chain(facts, site_id=site_id, page_id=page_id)
        rows = []
        for position, ancestor in chain:
            try:
                ancestor_route = memo.route(ancestor.id)
            except fs.SurfaceReadError:
                raise ProjectionError("unavailable") from None
            rows.append(
                (
                    position,
                    ancestor.id,
                    ancestor.site_id,
                    ancestor.title,
                    ancestor.locale,
                    ancestor_route,
                )
            )
        if len(rows) > 64:
            raise ProjectionError("region_state")
        ancestors: list[ProjectionAncestor] = []
        previous_position = 0
        for row in rows:
            (
                position,
                _ancestor_id,
                row_site_id,
                title,
                _locale,
                effective_route,
            ) = row
            if row_site_id != site_id:
                raise ProjectionError("region_scope")
            if (
                not isinstance(title, str)
                or not title
                or not isinstance(effective_route, str)
                or not effective_route.startswith("/")
            ):
                raise ProjectionError("region_state")
            if int(position) != previous_position + 1:
                raise ProjectionError("region_state")
            previous_position = int(position)
            ancestors.append(
                ProjectionAncestor(title=title, effective_route=effective_route)
            )
        return tuple(ancestors)

    async def _media_descriptors(
        self,
        surface: fs.RenderReadSurface,
        *,
        nodes: tuple[ProjectionNode, ...],
        site_id: UUID,
        render_mode: str,
        snapshot_id: UUID | None = None,
        preview_workspace_id: UUID | None = None,
        preview_bound: bool = False,
    ) -> tuple[
        dict[UUID, ProjectionMedia],
        dict[UUID, tuple[ProjectionMedia | None, ...]],
    ]:
        descriptors: dict[UUID, ProjectionMedia] = {}
        list_descriptors: dict[UUID, tuple[ProjectionMedia | None, ...]] = {}
        for node in _flatten(nodes):
            if node.component_type == "Image":
                raw = node.props.get("mediaId")
                if not isinstance(raw, str):
                    continue
                try:
                    media_id = UUID(raw)
                except ValueError:
                    continue
                try:
                    row = await surface.resolve_media(
                        site_id=site_id, media_id=media_id
                    )
                except fs.SurfaceReadError as exc:
                    raise ProjectionError("not_found") from exc
                descriptor = _media_descriptor(
                    render_mode=render_mode,
                    site_id=site_id,
                    media_id=media_id,
                    row=row,
                    snapshot_id=snapshot_id,
                    preview_workspace_id=preview_workspace_id,
                    preview_bound=preview_bound,
                )
                if descriptor is not None:
                    descriptors[node.id] = descriptor
            elif node.component_type in ("Gallery", "LogoGrid"):
                items = node.props.get("items")
                if not isinstance(items, list):
                    continue
                item_descriptors: list[ProjectionMedia | None] = []
                for item in items:
                    raw_media_id = (
                        item.get("mediaId") if isinstance(item, dict) else None
                    )
                    if not isinstance(raw_media_id, str):
                        item_descriptors.append(None)
                        continue
                    try:
                        media_id = UUID(raw_media_id)
                    except ValueError:
                        item_descriptors.append(None)
                        continue
                    try:
                        row = await surface.resolve_media(
                            site_id=site_id, media_id=media_id
                        )
                    except fs.SurfaceReadError as exc:
                        raise ProjectionError("not_found") from exc
                    item_descriptors.append(
                        _media_descriptor(
                            render_mode=render_mode,
                            site_id=site_id,
                            media_id=media_id,
                            row=row,
                            snapshot_id=snapshot_id,
                            preview_workspace_id=preview_workspace_id,
                            preview_bound=preview_bound,
                        )
                    )
                list_descriptors[node.id] = tuple(item_descriptors)
            elif node.component_type == "DocumentList":
                items = node.props.get("items")
                if not isinstance(items, list):
                    continue
                item_descriptors = []
                for item in items:
                    raw_media_id = (
                        item.get("mediaId") if isinstance(item, dict) else None
                    )
                    if not isinstance(raw_media_id, str):
                        item_descriptors.append(None)
                        continue
                    try:
                        media_id = UUID(raw_media_id)
                    except ValueError:
                        item_descriptors.append(None)
                        continue
                    try:
                        row = await surface.resolve_media(
                            site_id=site_id, media_id=media_id
                        )
                    except fs.SurfaceReadError as exc:
                        raise ProjectionError("not_found") from exc
                    item_descriptors.append(
                        _media_descriptor(
                            render_mode=render_mode,
                            site_id=site_id,
                            media_id=media_id,
                            row=row,
                            mime_classes=DOCUMENT_MIME_CLASSES,
                            snapshot_id=snapshot_id,
                            preview_workspace_id=preview_workspace_id,
                            preview_bound=preview_bound,
                        )
                    )
                list_descriptors[node.id] = tuple(item_descriptors)
        return descriptors, list_descriptors

    async def _query(
        self,
        surface: fs.RenderReadSurface,
        *,
        context: SiteContext,
        request: RenderPageRequest,
        render_mode: str,
        snapshot_id: UUID | None = None,
        preview_workspace_id: UUID | None = None,
        preview_bound: bool = False,
    ) -> RenderRouteProjection:
        locales, projected_locales, default_locale = await self._locales(
            surface, site_id=context.site_id
        )
        route, locale = _route_parts(context, request.path, request.locale, locales)
        # canonical: published only.  preview AND frozen review keep the
        # active-preview candidate policy (published + draft): review
        # resolves the captured workspace exactly as the active preview
        # did, with the frozen surface supplying the stored rows.
        statuses = (
            ["PUBLISHED"] if render_mode == "canonical" else ["PUBLISHED", "DRAFT"]
        )
        # ONE per-request shared route memo over the complete retained
        # page facts: every route resolution, navigation item, region
        # href and ancestor row in this request derives each page's
        # effective route at most once (R8 total-work bound).  The
        # frozen review path builds the identical memo over its
        # captured facts.
        try:
            page_rows = await surface.fetch_pages(site_id=context.site_id)
        except fs.SurfaceReadError as exc:
            raise ProjectionError("unavailable") from exc
        facts = {row.id: row for row in page_rows}
        enabled_tags = frozenset(str(row[2]) for row in locales if row[3])
        memo = new_route_memo(
            facts, default_locale=default_locale, enabled_tags=enabled_tags
        )
        redirect = await self._redirects(
            surface,
            facts=facts,
            memo=memo,
            site_id=context.site_id,
            route=route,
            locale=locale,
            default_locale=default_locale,
            statuses=statuses,
            enabled_tags=enabled_tags,
        )
        if redirect is not None:
            redirect = _redirect_location(
                redirect,
                context=context,
                request=request,
                render_mode=render_mode,
            )
            return RenderRedirectProjection(
                render_mode=render_mode,
                site=ProjectionSite(
                    id=context.site_id,
                    key=context.site_key,
                    canonical_revision=context.canonical_revision,
                ),
                requested_path=request.path,
                matched_path=route,
                locale=locale,
                locales=projected_locales,
                redirect=redirect,
            )
        fact = self._resolve_page_fact(
            facts=facts,
            memo=memo,
            site_id=context.site_id,
            route=route,
            locale=locale,
            statuses=statuses,
            default_locale=default_locale,
            enabled_tags=enabled_tags,
        )
        if fact is None:
            raise ProjectionError("not_found")
        page = _page_from_fact(fact, memo.route(fact.id))
        route_parameter = _dynamic_route_parameter(page.effective_route, route)
        # The switcher re-resolves each locale counterpart from the CONCRETE
        # matched route: page.effective_route carries the ``/{slug}`` template
        # for dynamic pages, which would make every counterpart target a
        # non-matching template route and leave valid counterparts with inert
        # locale links.  For static pages the matched route equals the
        # effective route, so supported static/fallback semantics are
        # unchanged.
        projected_locales = self._locale_switcher(
            facts=facts,
            memo=memo,
            site_id=context.site_id,
            locales=projected_locales,
            current_locale=locale,
            default_locale=default_locale,
            current_route=route,
            statuses=statuses,
            enabled_tags=enabled_tags,
        )
        try:
            node_rows = list(
                await surface.fetch_composition(
                    site_id=context.site_id, page_id=page.id
                )
            )
        except fs.SurfaceReadError as exc:
            raise ProjectionError("composition_too_large") from exc
        roots = _node_tree(node_rows, page_id=page.id, site_id=context.site_id)
        media_descriptors, list_descriptors = await self._media_descriptors(
            surface,
            nodes=roots,
            site_id=context.site_id,
            render_mode=render_mode,
            snapshot_id=snapshot_id,
            preview_workspace_id=preview_workspace_id,
            preview_bound=preview_bound,
        )
        if media_descriptors or list_descriptors:
            roots = _attach_media(roots, media_descriptors, list_descriptors)
        detail_nodes = tuple(
            node
            for node in _flatten(roots)
            if node.component_type == "CollectionDetail"
        )
        if page.route_template == "{slug}" and len(detail_nodes) != 1:
            raise ProjectionError("not_found")
        bindings, binding_meta = await _collection_bindings(
            surface,
            nodes=roots,
            site_id=context.site_id,
            render_mode=render_mode,
            selected_locale=locale,
            default_locale=default_locale,
            route_parameter=route_parameter,
        )
        navigation = await self._navigation(
            surface,
            facts=facts,
            memo=memo,
            site_id=context.site_id,
            selected_locale=locale,
            default_locale=default_locale,
            statuses=statuses,
            enabled_tags=enabled_tags,
        )
        try:
            theme_row = await surface.fetch_theme(site_id=context.site_id)
            page_style_row = await surface.fetch_page_style(page_id=page.id)
            catalog_version = await surface.fetch_catalog_version(
                site_id=context.site_id
            )
        except fs.SurfaceReadError as exc:
            raise ProjectionError("not_found") from exc
        if theme_row is None:
            raise ProjectionError("not_found")
        if page_style_row is None:
            raise ProjectionError("not_found")
        page_style_value = _json_value(page_style_row[6])
        if not isinstance(page_style_value, dict):
            raise ProjectionError("page_style_state")
        try:
            page_style = ThemeRecord.model_validate(page_style_value)
        except (TypeError, ValueError):
            raise ProjectionError("page_style_state") from None
        if catalog_version != "catalog-v1":
            raise ProjectionError("catalog_mismatch")
        regions = await self._regions(
            surface,
            facts=facts,
            memo=memo,
            site_id=context.site_id,
        )
        ancestors = self._ancestors(
            facts=facts,
            memo=memo,
            site_id=context.site_id,
            page_id=page.id,
        )
        return RenderPageProjection(
            render_mode=render_mode,
            site=ProjectionSite(
                id=context.site_id,
                key=context.site_key,
                canonical_revision=context.canonical_revision,
            ),
            requested_path=request.path,
            matched_path=route,
            locale=locale,
            route_parameters=(
                {"slug": route_parameter} if route_parameter is not None else {}
            ),
            page=page,
            composition=ProjectionComposition(
                schema_version="site-composition/v1",
                catalog_version=catalog_version,
                nodes=roots,
            ),
            theme=theme_record_from_row(theme_row),
            page_style=page_style,
            locales=projected_locales,
            navigation=navigation,
            bindings=bindings,
            binding_meta=binding_meta,
            regions=regions,
            ancestors=ancestors,
            default_locale=default_locale,
        )

    async def canonical(self, request: RenderPageRequest) -> RenderRouteProjection:
        try:
            async with self._database.public_pool().acquire(
                timeout=self._database.acquire_timeout
            ) as connection:
                async with connection.transaction(
                    isolation="repeatable_read", readonly=True
                ):
                    context = await self._context_on_connection(connection, request)
                    projection = await self._query(
                        fs.DatabaseRenderSurface(connection),
                        context=context,
                        request=request,
                        render_mode="canonical",
                    )
                    return projection
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ProjectionError("unavailable") from None

    async def preview(self, request: RenderPreviewRequest) -> RenderRouteProjection:
        if (request.session_token is None) == (request.browser_token is None):
            raise ProjectionError("not_found")
        if request.browser_token is not None:
            try:
                context = await self._context(request)
            except ProjectionError as error:
                _browser_stage("context", _browser_outcome(error))
                raise
            _browser_stage("context", "ok")
            return await self._browser_preview(request, context=context)
        return await self._human_preview(request)

    async def review(self, request: RenderReviewRequest) -> RenderRouteProjection:
        """Faithful frozen review read (R5: frozen input only).

        The 076 authorize function is the single authority: live
        session ACTIVE/unrevoked/expiry/recency checks, the v2
        supported-format gate and the admin-or-membership binding all
        run in SQL over the trusted control tables.  The snapshot row
        then feeds the shared projection over the frozen surface -
        the exact same common helper both paths execute - with a
        context sealed from the CAPTURED site facts and the locked
        freeze revision.  Every refusal (unknown session, revoked,
        expired, non-v2, non-COMPLETE, foreign site/workspace,
        malformed document) fails closed to one uniform 404;
        infrastructure faults map to unavailable.
        """
        if request.session_token is None:
            raise ProjectionError("not_found")
        try:
            public_id, secret = parse_session_token(
                request.session_token.get_secret_value()
            )
        except Exception:
            raise ProjectionError("not_found") from None
        try:
            # The 076 grants give this read to slaif_preview_reader only;
            # the public reader pool must stay unable to run it.
            async with self._database.preview_pool().acquire(
                timeout=self._database.acquire_timeout
            ) as connection:
                # repeatable-read WITHOUT readonly: the 076 authorize
                # function takes FOR SHARE on the real user_session row,
                # which a read-only transaction refuses (PostgreSQL
                # executor permission check), and the lock is part of
                # the intended authorization.
                async with connection.transaction(isolation="repeatable_read"):
                    authorized = await connection.fetchrow(
                        "SELECT * FROM control.slaif_review_projection_authorize("
                        "$1,$2,$3)",
                        public_id,
                        digest_secret(secret),
                        request.snapshot_id,
                    )
                    if (
                        authorized is None
                        or authorized[0] is None
                        or authorized[1] is None
                    ):
                        raise ProjectionError("not_found")
                    workspace_id = authorized[0]
                    site_id = authorized[1]
                    row = await connection.fetchval(
                        "SELECT control.slaif_review_snapshot_frozen_state($1)",
                        request.snapshot_id,
                    )
                    # The pool installs identity checks, not JSON
                    # codecs: the standard driver returns the jsonb as
                    # text, so it is decoded through the qualified
                    # exact-number path (parse_float=Decimal) that
                    # preserves every retained digit/scale.  Plain
                    # float decoding or a global codec must not enter
                    # this boundary.
                    if row is None:
                        raise ProjectionError("not_found")
                    if isinstance(row, (bytes, bytearray)):
                        try:
                            row_text = row.decode()
                        except UnicodeDecodeError:
                            raise ProjectionError("not_found") from None
                    elif isinstance(row, str):
                        row_text = row
                    else:
                        raise ProjectionError("not_found")
                    try:
                        row = parse_snapshot_text(row_text)
                    except ValueError:
                        raise ProjectionError("not_found") from None
                    if not isinstance(row, dict):
                        raise ProjectionError("not_found")
                    surface = fs.FrozenRenderSurface(
                        row,
                        expected_snapshot_id=request.snapshot_id,
                        expected_site_id=site_id,
                        expected_workspace_id=workspace_id,
                    )
                    context = SiteContext._from_frozen(
                        site_id=site_id,
                        site_key=surface.site_key,
                        status=surface.site_status,
                        base_site_revision=surface.base_site_revision,
                        default_locale=surface.default_locale,
                        matched_path_prefix=_frozen_local_match_prefix(request),
                    )
                    return await self._query(
                        surface,
                        context=context,
                        request=request,
                        render_mode="review",
                        snapshot_id=request.snapshot_id,
                    )
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ProjectionError("unavailable") from None
        except (fs.SurfaceReadError, ValueError):
            # admission refusals and unsealed captured facts are
            # uniform 404s, never a fallback render
            raise ProjectionError("not_found") from None

    async def _human_preview(
        self, request: RenderPreviewRequest
    ) -> RenderRouteProjection:
        context = await self._context(request)
        try:
            if request.session_token is None:
                raise ProjectionError("not_found")
            public_id, secret = parse_session_token(request.session_token)
        except Exception:
            raise ProjectionError("not_found") from None
        try:
            pool = self._database.preview_pool()
            idle_seconds, touch_seconds, recent_auth_seconds = getattr(
                self._database, "preview_policy", (1800, 300, 900)
            )
            async with pool.acquire(
                timeout=self._database.acquire_timeout
            ) as connection:
                authorized = await connection.fetchrow(
                    "SELECT * FROM control.slaif_render_preview_authorize_touch("
                    "$1,$2,$3,$4,$5,$6,$7)",
                    public_id,
                    digest_secret(secret),
                    request.workspace_id,
                    context.site_id,
                    idle_seconds,
                    touch_seconds,
                    recent_auth_seconds,
                )
            if authorized is None or authorized[2] != request.workspace_id:
                raise ProjectionError("not_found")
            trusted_workspace_id = authorized[2]
            async with _repeatable_read_cow(
                pool,
                session_id=trusted_workspace_id,
                acquire_timeout=self._database.acquire_timeout,
            ) as cow:
                await cow.validate_context()
                reauthorized = await cow.native.fetchrow(
                    "SELECT * FROM control.slaif_render_preview_authorize_recheck("
                    "$1,$2,$3,$4,$5,$6,$7)",
                    public_id,
                    digest_secret(secret),
                    trusted_workspace_id,
                    context.site_id,
                    idle_seconds,
                    touch_seconds,
                    recent_auth_seconds,
                )
                if (
                    reauthorized is None
                    or reauthorized[2] != trusted_workspace_id
                    or reauthorized[3] != context.site_id
                ):
                    raise ProjectionError("not_found")
                snapshot_context = await self._context_on_connection(
                    cow.native, request
                )
                if snapshot_context.site_id != context.site_id:
                    raise ProjectionError("not_found")
                return await self._query(
                    fs.DatabaseRenderSurface(cow.native),
                    context=snapshot_context,
                    request=request,
                    render_mode="preview",
                    preview_workspace_id=trusted_workspace_id,
                )
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ProjectionError("unavailable") from None

    async def _browser_preview(
        self, request: RenderPreviewRequest, *, context: SiteContext
    ) -> RenderRouteProjection:
        verifier = self._browser_verifier
        if (
            verifier is None
            or request.browser_token is None
            or request.browser_route is None
        ):
            _browser_stage("token-binding", "not_found")
            raise ProjectionError("not_found")
        try:
            claims = verifier.verify(
                request.browser_token.get_secret_value(),
                now=int(time.time()),
                expected=BrowserPreviewExpectedBinding(
                    site_id=context.site_id,
                    workspace_id=request.workspace_id,
                    route=request.browser_route,
                ),
            )
        except (BrowserPreviewCredentialError, ValueError):
            _browser_stage("token-binding", "not_found")
            raise ProjectionError("not_found") from None
        _browser_stage("token-binding", "ok")
        try:
            pool = self._database.preview_pool()
            async with pool.acquire(
                timeout=self._database.acquire_timeout
            ) as connection:
                # 083/5 trusted run binding: the 036 consume and the
                # binding registrar run in ONE explicit transaction
                # on one connection.  The registrar records the full
                # credential sha256 digest, the verifier-checked
                # expiry and the current attempt as immutable run
                # facts (EXECUTE: slaif_preview_reader only).  A
                # failed or rolled-back consume therefore leaves no
                # usable binding; a media read exists only after a
                # committed authorized consume.
                async with connection.transaction():
                    authorized = await connection.fetchrow(
                        "SELECT * FROM control.slaif_render_browser_preview_authorize("
                        "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                        claims.capability_id,
                        claims.site_id,
                        claims.workspace_id,
                        claims.run_id,
                        claims.route,
                        claims.target.value,
                        [item.value for item in claims.evidence],
                        claims.artifact_bytes_limit,
                        claims.duration_seconds,
                        claims.nonce_digest,
                        True,
                    )
                    if (
                        authorized is not None
                        and authorized[0] == claims.workspace_id
                        and authorized[1] == claims.site_id
                        and authorized[2] == claims.run_id
                    ):
                        await connection.execute(
                            "SELECT control.slaif_browser_preview_binding_register("
                            "$1,$2,$3)",
                            claims.run_id,
                            hashlib.sha256(
                                request.browser_token.get_secret_value().encode("ascii")
                            ).hexdigest(),
                            datetime.fromtimestamp(claims.expires_at, tz=UTC),
                        )
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            _browser_stage("authorize-consume", "unavailable")
            raise ProjectionError("unavailable") from None
        except Exception:
            _browser_stage("authorize-consume", "error")
            raise ProjectionError("unavailable") from None
        _browser_stage(
            "authorize-consume", "ok" if authorized is not None else "not_found"
        )
        if (
            authorized is None
            or authorized[0] != claims.workspace_id
            or authorized[1] != claims.site_id
            or authorized[2] != claims.run_id
        ):
            raise ProjectionError("not_found")
        try:
            async with _repeatable_read_cow(
                pool,
                session_id=claims.workspace_id,
                acquire_timeout=self._database.acquire_timeout,
            ) as cow:
                await cow.validate_context()
                _browser_stage("cow-context", "ok")
                reauthorized = await cow.native.fetchrow(
                    "SELECT * FROM control.slaif_render_browser_preview_authorize("
                    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                    claims.capability_id,
                    claims.site_id,
                    claims.workspace_id,
                    claims.run_id,
                    claims.route,
                    claims.target.value,
                    [item.value for item in claims.evidence],
                    claims.artifact_bytes_limit,
                    claims.duration_seconds,
                    claims.nonce_digest,
                    False,
                )
                _browser_stage(
                    "authorize-recheck",
                    "ok" if reauthorized is not None else "not_found",
                )
                if (
                    reauthorized is None
                    or reauthorized[0] != claims.workspace_id
                    or reauthorized[1] != claims.site_id
                    or reauthorized[2] != claims.run_id
                ):
                    raise ProjectionError("not_found")
                snapshot_context = await self._context_on_connection(
                    cow.native, request
                )
                if snapshot_context.site_id != context.site_id:
                    raise ProjectionError("not_found")
                try:
                    projection = await self._query(
                        fs.DatabaseRenderSurface(cow.native),
                        context=snapshot_context,
                        request=request,
                        render_mode="preview",
                        preview_workspace_id=claims.workspace_id,
                        preview_bound=True,
                    )
                except ProjectionError as error:
                    _browser_stage("projection-query", _browser_outcome(error))
                    raise
                except asyncio.CancelledError:
                    raise
                except (asyncpg.PostgresError, OSError, TimeoutError):
                    _browser_stage("projection-query", "unavailable")
                    raise ProjectionError("unavailable") from None
                except Exception:
                    _browser_stage("projection-query", "error")
                    raise ProjectionError("unavailable") from None
                _browser_stage("projection-query", "ok")
                _browser_stage("success", "ok")
                return projection
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            _browser_stage("cow-context", "unavailable")
            raise ProjectionError("unavailable") from None
        except Exception:
            _browser_stage("cow-context", "error")
            raise ProjectionError("unavailable") from None


__all__ = [
    "ProjectionComposition",
    "ProjectionError",
    "ProjectionLocale",
    "ProjectionNavigation",
    "ProjectionNavigationItem",
    "ProjectionNavigationTarget",
    "ProjectionNode",
    "ProjectionPage",
    "ProjectionRedirect",
    "RenderPageProjection",
    "RenderPageRequest",
    "RenderRedirectProjection",
    "RenderReviewRequest",
    "RenderPreviewRequest",
    "RenderRouteProjection",
    "RenderProjectionService",
]

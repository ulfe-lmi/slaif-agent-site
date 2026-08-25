"""Bounded, typed Render projections over canonical and COW content views."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any, Protocol, cast
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
from slaif_agent_site.identity.sessions import digest_secret, parse_session_token
from slaif_agent_site.sites.models import SiteContext
from slaif_agent_site.sites.normalization import normalize_request_path

CATALOG_TYPES = frozenset(
    {
        "Section",
        "Container",
        "Columns",
        "Grid",
        "Stack",
        "Spacer",
        "Heading",
        "RichText",
        "Image",
        "Button",
        "Quote",
        "CollectionList",
        "CollectionGrid",
        "CollectionDetail",
        "Hero",
        "Statistics",
        "Timeline",
        "FAQ",
        "Header",
        "Footer",
        "Breadcrumbs",
        "LanguageSwitcher",
    }
)
MAX_NODES = 128
MAX_DEPTH = 16
MAX_PROPS_BYTES = 16_384
ALLOWED_SLOTS: dict[str, frozenset[str]] = {
    "Section": frozenset({"default"}),
    "Container": frozenset({"default"}),
    "Columns": frozenset({"col-1", "col-2", "col-3", "col-4"}),
    "Grid": frozenset({"default"}),
    "Stack": frozenset({"default"}),
    "Hero": frozenset({"content"}),
    "Header": frozenset({"nav"}),
    "Footer": frozenset({"links"}),
}
MAX_CHILDREN = {
    "Section": 32,
    "Container": 16,
    "Columns": 4,
    "Grid": 24,
    "Stack": 16,
    "Hero": 8,
    "Header": 12,
    "Footer": 16,
}
PROP_SCHEMA: dict[str, dict[str, dict[str, Any]]] = {
    "Section": {
        "variant": {"type": "enum", "values": ("default", "full", "narrow")},
        "background": {"type": "string"},
    },
    "Container": {"width": {"type": "enum", "values": ("sm", "md", "lg", "xl")}},
    "Columns": {
        "count": {"type": "number", "required": True, "min": 1, "max": 4},
        "gap": {"type": "enum", "values": ("none", "sm", "md", "lg")},
    },
    "Grid": {
        "columns": {"type": "number", "min": 1, "max": 12},
        "gap": {"type": "enum", "values": ("sm", "md", "lg")},
    },
    "Stack": {
        "direction": {"type": "enum", "values": ("vertical", "horizontal")},
        "gap": {"type": "enum", "values": ("none", "sm", "md", "lg")},
    },
    "Spacer": {
        "size": {
            "type": "enum",
            "required": True,
            "values": ("xs", "sm", "md", "lg", "xl"),
        }
    },
    "Heading": {
        "text": {"type": "string", "required": True},
        "level": {"type": "number", "required": True, "min": 1, "max": 6},
    },
    "RichText": {"content": {"type": "object", "required": True}},
    "Image": {
        "mediaId": {"type": "reference", "required": True},
        "alt": {"type": "string", "required": True},
        "aspectRatio": {"type": "enum", "values": ("auto", "16:9", "4:3", "1:1")},
    },
    "Button": {
        "label": {"type": "string", "required": True},
        "href": {"type": "string", "required": True},
        "variant": {"type": "enum", "values": ("primary", "secondary", "ghost")},
    },
    "Quote": {
        "text": {"type": "string", "required": True},
        "attribution": {"type": "string"},
    },
    "CollectionList": {
        "viewId": {"type": "reference", "required": True},
        "limit": {"type": "number", "min": 1, "max": 100},
    },
    "CollectionGrid": {
        "viewId": {"type": "reference", "required": True},
        "columns": {"type": "number", "min": 1, "max": 6},
    },
    "CollectionDetail": {"viewId": {"type": "reference", "required": True}},
    "Hero": {
        "heading": {"type": "string", "required": True},
        "subheading": {"type": "string"},
        "mediaId": {"type": "reference"},
    },
    "Statistics": {"items": {"type": "array", "required": True}},
    "Timeline": {"items": {"type": "array", "required": True}},
    "FAQ": {"items": {"type": "array", "required": True}},
    "Header": {},
    "Footer": {},
    "Breadcrumbs": {},
    "LanguageSwitcher": {},
}


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
        normalized = value.strip().lower()
        if not normalized or len(normalized) > 10 or "/" in normalized:
            raise ValueError("invalid locale")
        return normalized


class RenderPreviewRequest(RenderPageRequest):
    workspace_id: UUID
    session_token: SecretStr | None = Field(default=None, exclude=True, repr=False)
    browser_token: SecretStr | None = Field(default=None, exclude=True, repr=False)
    browser_route: str | None = None

    @field_validator("browser_route")
    @classmethod
    def browser_route_is_normalized(cls, value: str | None) -> str | None:
        return normalize_preview_route(value) if value is not None else None


class ProjectionNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    component_type: str
    schema_version: str
    parent_id: UUID | None
    slot_key: str
    order_key: int
    props: dict[str, Any]
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
    row_version: int


class ProjectionSite(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    key: str
    canonical_revision: int


class RenderPageProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    render_mode: str
    site: ProjectionSite
    requested_path: str
    matched_path: str
    locale: str
    page: ProjectionPage
    composition: ProjectionComposition
    theme: dict[str, Any] = Field(default_factory=dict)
    navigation: tuple[dict[str, Any], ...] = ()
    bindings: dict[str, tuple[dict[str, Any], ...]] = Field(default_factory=dict)


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
        ("javascript:", "data:", "file:")
    ):
        raise ProjectionError("unsafe_value")


def _validate_props(component_type: str, props: dict[str, Any]) -> None:
    schema = PROP_SCHEMA[component_type]
    if set(props) - set(schema):
        raise ProjectionError("unknown_prop")
    for key, rule in schema.items():
        if rule.get("required") and key not in props:
            raise ProjectionError("missing_prop")
    for key, value in props.items():
        rule = schema[key]
        kind = rule["type"]
        if kind == "string" and not isinstance(value, str):
            raise ProjectionError("prop_type")
        if kind == "number" and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise ProjectionError("prop_type")
        if kind == "object" and not isinstance(value, dict):
            raise ProjectionError("prop_type")
        if kind == "array" and not isinstance(value, list):
            raise ProjectionError("prop_type")
        if kind == "reference":
            try:
                UUID(str(value))
            except (TypeError, ValueError):
                raise ProjectionError("prop_reference") from None
        if kind == "enum" and value not in rule["values"]:
            raise ProjectionError("prop_enum")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "min" in rule and value < rule["min"]:
                raise ProjectionError("prop_bound")
            if "max" in rule and value > rule["max"]:
                raise ProjectionError("prop_bound")
    if component_type == "Button":
        href = props["href"]
        if not href.startswith("/") or href.startswith("//"):
            raise ProjectionError("unsafe_value")
    _validate_nested(props)


def _route_slug(context: SiteContext, path: str) -> str:
    try:
        normalized = normalize_request_path(path)
    except Exception:
        raise ProjectionError("not_found") from None
    prefix = (context.matched_path_prefix or "/").rstrip("/") or "/"
    if prefix != "/":
        if normalized != prefix and not normalized.startswith(prefix + "/"):
            raise ProjectionError("not_found")
        normalized = normalized[len(prefix) :] or "/"
    slug = normalized.strip("/")
    if not slug:
        # The current bounded page model has no physical root-page marker. A
        # literal `home` page is the only honest root convention.
        slug = "home"
    return slug


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
        row_version=int(row[7]),
    )


def _flatten(nodes: tuple[ProjectionNode, ...]) -> tuple[ProjectionNode, ...]:
    result: list[ProjectionNode] = []

    def visit(node: ProjectionNode) -> None:
        result.append(node)
        for child in node.children:
            visit(child)

    for node in nodes:
        visit(node)
    return tuple(result)


async def _collection_bindings(
    connection: Any,
    *,
    nodes: tuple[ProjectionNode, ...],
    site_id: UUID,
    render_mode: str,
) -> dict[str, tuple[dict[str, Any], ...]]:
    bindings: dict[str, tuple[dict[str, Any], ...]] = {}
    for node in _flatten(nodes):
        if node.component_type not in {
            "CollectionList",
            "CollectionGrid",
            "CollectionDetail",
        }:
            continue
        raw_view_id = node.props.get("viewId", node.props.get("view_id"))
        try:
            view_id = UUID(str(raw_view_id))
        except (TypeError, ValueError):
            raise ProjectionError("invalid_collection_view") from None
        view = await connection.fetchrow(
            "SELECT id, site_id, type_id, key, filter_spec, sort_spec, "
            "projection_spec, pagination_spec FROM content.collection_view "
            "WHERE id = $1 LIMIT 1",
            view_id,
        )
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
        if (
            set(filter_spec) - {"status", "slug"}
            or set(sort_spec) - {"field", "direction"}
            or set(pagination_spec) - {"limit"}
        ):
            raise ProjectionError("unsupported_collection_query")
        if filter_spec.get("status") is not None and not isinstance(
            filter_spec["status"], str
        ):
            raise ProjectionError("unsupported_collection_query")
        if filter_spec.get("slug") is not None and not isinstance(
            filter_spec["slug"], str
        ):
            raise ProjectionError("unsupported_collection_query")
        if projection_spec in ({}, None):
            projection_fields: list[str] = []
        elif isinstance(projection_spec, list):
            projection_fields = projection_spec
        elif isinstance(projection_spec, dict) and set(projection_spec) == {"fields"}:
            projection_fields = projection_spec["fields"]
        else:
            raise ProjectionError("unsupported_collection_query")
        if len(projection_fields) > 16 or not all(
            isinstance(value, str) and value for value in projection_fields
        ):
            raise ProjectionError("unsupported_collection_query")
        if len(set(projection_fields)) != len(projection_fields) or any(
            field in {"id", "site_id", "type_id", "slug", "status", "values"}
            for field in projection_fields
        ):
            raise ProjectionError("unsupported_collection_query")
        type_row = await connection.fetchrow(
            "SELECT site_id, status FROM content.content_type WHERE id = $1 LIMIT 1",
            view[2],
        )
        if type_row is None or type_row[0] != site_id or type_row[1] != "ACTIVE":
            raise ProjectionError("collection_scope")
        field_rows = await connection.fetch(
            "SELECT key FROM content.field_definition WHERE type_id = $1 "
            'ORDER BY key COLLATE "C"',
            view[2],
        )
        defined_fields = {row[0] for row in field_rows}
        if any(field not in defined_fields for field in projection_fields):
            raise ProjectionError("unknown_projection_field")
        requested_limit = node.props.get("limit", pagination_spec.get("limit", 24))
        if (
            isinstance(requested_limit, bool)
            or not isinstance(requested_limit, int)
            or not 1 <= requested_limit <= 100
        ):
            raise ProjectionError("collection_limit")
        statuses = (
            ["PUBLISHED"] if render_mode == "canonical" else ["PUBLISHED", "DRAFT"]
        )
        if isinstance(filter_spec.get("status"), str):
            if filter_spec["status"] not in statuses:
                raise ProjectionError("collection_status")
            statuses = [filter_spec["status"]]
        rows = await connection.fetch(
            "SELECT id, site_id, type_id, slug, status, values "
            "FROM content.content_item WHERE site_id = $1 AND type_id = $2 "
            'AND status = ANY($3::text[]) ORDER BY slug COLLATE "C", id LIMIT 100',
            site_id,
            view[2],
            statuses,
        )
        items: list[dict[str, Any]] = []
        slug_filter = filter_spec.get("slug")
        for row in rows:
            if row[1] != site_id or row[2] != view[2]:
                raise ProjectionError("collection_scope")
            if slug_filter is not None and row[3] != slug_filter:
                continue
            values = _json_value(row[5])
            if not isinstance(values, dict):
                raise ProjectionError("malformed_item")
            item = {
                "id": row[0],
                "site_id": row[1],
                "type_id": row[2],
                "slug": row[3],
                "status": row[4],
                "values": {
                    field: values[field]
                    for field in projection_fields
                    if field in values
                },
            }
            if any(field not in values for field in projection_fields):
                raise ProjectionError("unknown_projection_field")
            items.append(item)
        field = sort_spec.get("field", "slug")
        if field not in {"slug", "id"}:
            raise ProjectionError("unsupported_collection_query")
        reverse = sort_spec.get("direction", "asc") == "desc"
        if sort_spec.get("direction", "asc") not in {"asc", "desc"}:
            raise ProjectionError("unsupported_collection_query")
        items.sort(key=lambda item: str(item.get(field, "")), reverse=reverse)
        bindings[str(node.id)] = tuple(items[:requested_limit])
    return bindings


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

    async def _query(
        self,
        connection: Any,
        *,
        context: SiteContext,
        request: RenderPageRequest,
        render_mode: str,
    ) -> RenderPageProjection:
        slug = _route_slug(context, request.path)
        locale = request.locale or context.default_locale
        row = await connection.fetchrow(
            "SELECT id, site_id, slug, title, status, locale, parent_id, row_version, "
            "created_at, updated_at FROM content.page "
            "WHERE site_id = $1 AND slug = $2 AND locale = $3 "
            "AND status = ANY($4::text[]) ORDER BY id LIMIT 2",
            context.site_id,
            slug,
            locale,
            ["PUBLISHED", "DRAFT"] if render_mode == "preview" else ["PUBLISHED"],
        )
        if row is None:
            raise ProjectionError("not_found")
        # The query is deliberately bounded; a duplicate indicates corrupt
        # canonical/overlay state and must never pick an arbitrary page.
        duplicate = await connection.fetch(
            "SELECT id FROM content.page WHERE site_id = $1 AND slug = $2 "
            "AND locale = $3 AND status = ANY($4::text[]) ORDER BY id LIMIT 2",
            context.site_id,
            slug,
            locale,
            ["PUBLISHED", "DRAFT"] if render_mode == "preview" else ["PUBLISHED"],
        )
        if len(duplicate) != 1:
            raise ProjectionError("ambiguous_page")
        page = _page(row)
        node_rows = list(
            await connection.fetch(
                "SELECT id, site_id, page_id, component_type, schema_version, "
                "parent_id, slot_key, order_key, props, created_at, updated_at "
                "FROM content.page_composition WHERE site_id = $1 AND page_id = $2 "
                "ORDER BY parent_id NULLS FIRST, slot_key, order_key, id",
                context.site_id,
                page.id,
            )
        )
        roots = _node_tree(node_rows, page_id=page.id, site_id=context.site_id)
        bindings = await _collection_bindings(
            connection,
            nodes=roots,
            site_id=context.site_id,
            render_mode=render_mode,
        )
        nav_rows = await connection.fetch(
            "SELECT id, site_id, key, label, settings FROM content.navigation "
            'WHERE site_id = $1 ORDER BY key COLLATE "C" LIMIT 16',
            context.site_id,
        )
        theme_row = await connection.fetchrow(
            "SELECT palette, typography, layout, shape FROM content.theme "
            "WHERE site_id = $1 LIMIT 1",
            context.site_id,
        )
        catalog_row = await connection.fetchrow(
            "SELECT control.slaif_site_render_catalog($1)", context.site_id
        )
        catalog_version = catalog_row[0] if catalog_row is not None else None
        if catalog_version != "catalog-v1":
            raise ProjectionError("catalog_mismatch")
        return RenderPageProjection(
            render_mode=render_mode,
            site=ProjectionSite(
                id=context.site_id,
                key=context.site_key,
                canonical_revision=context.canonical_revision,
            ),
            requested_path=request.path,
            matched_path=slug,
            locale=locale,
            page=page,
            composition=ProjectionComposition(
                schema_version="site-composition/v1",
                catalog_version=catalog_version,
                nodes=roots,
            ),
            theme=(
                {
                    "palette": _json_value(theme_row[0]),
                    "typography": _json_value(theme_row[1]),
                    "layout": _json_value(theme_row[2]),
                    "shape": _json_value(theme_row[3]),
                }
                if theme_row is not None
                else {}
            ),
            navigation=tuple(
                {
                    "id": row[0],
                    "site_id": row[1],
                    "key": row[2],
                    "label": row[3],
                    "settings": _json_value(row[4]),
                }
                for row in nav_rows
            ),
            bindings=bindings,
        )

    async def canonical(self, request: RenderPageRequest) -> RenderPageProjection:
        context = await self._context(request)
        try:
            async with self._database.public_pool().acquire(
                timeout=self._database.acquire_timeout
            ) as connection:
                return await self._query(
                    connection,
                    context=context,
                    request=request,
                    render_mode="canonical",
                )
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ProjectionError("unavailable") from None

    async def preview(self, request: RenderPreviewRequest) -> RenderPageProjection:
        if (request.session_token is None) == (request.browser_token is None):
            raise ProjectionError("not_found")
        if request.browser_token is not None:
            context = await self._context(request)
            return await self._browser_preview(request, context=context)
        return await self._human_preview(request)

    async def _human_preview(
        self, request: RenderPreviewRequest
    ) -> RenderPageProjection:
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
                    "SELECT * FROM control.slaif_render_preview_authorize("
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
            async with asyncpg_cow_session(
                pool, session_id=trusted_workspace_id
            ) as cow:
                await cow.validate_context()
                reauthorized = await cow.native.fetchrow(
                    "SELECT * FROM control.slaif_render_preview_authorize("
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
                return await self._query(
                    cow.native,
                    context=context,
                    request=request,
                    render_mode="preview",
                )
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ProjectionError("unavailable") from None

    async def _browser_preview(
        self, request: RenderPreviewRequest, *, context: SiteContext
    ) -> RenderPageProjection:
        verifier = self._browser_verifier
        if (
            verifier is None
            or request.browser_token is None
            or request.browser_route is None
        ):
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
            raise ProjectionError("not_found") from None
        try:
            pool = self._database.preview_pool()
            async with pool.acquire(
                timeout=self._database.acquire_timeout
            ) as connection:
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
                authorized is None
                or authorized[0] != claims.workspace_id
                or authorized[1] != claims.site_id
                or authorized[2] != claims.run_id
            ):
                raise ProjectionError("not_found")
            async with asyncpg_cow_session(pool, session_id=claims.workspace_id) as cow:
                await cow.validate_context()
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
                if (
                    reauthorized is None
                    or reauthorized[0] != claims.workspace_id
                    or reauthorized[1] != claims.site_id
                    or reauthorized[2] != claims.run_id
                ):
                    raise ProjectionError("not_found")
                return await self._query(
                    cow.native,
                    context=context,
                    request=request,
                    render_mode="preview",
                )
        except ProjectionError:
            raise
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ProjectionError("unavailable") from None


__all__ = [
    "ProjectionComposition",
    "ProjectionError",
    "ProjectionNode",
    "ProjectionPage",
    "RenderPageProjection",
    "RenderPageRequest",
    "RenderPreviewRequest",
    "RenderProjectionService",
]

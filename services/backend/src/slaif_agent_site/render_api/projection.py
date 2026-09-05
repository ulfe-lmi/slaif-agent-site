"""Bounded, typed Render projections over canonical and COW content views."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
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
from slaif_agent_site.content_model.validators import validate_values
from slaif_agent_site.identity.sessions import digest_secret, parse_session_token
from slaif_agent_site.sites.models import SiteContext
from slaif_agent_site.sites.normalization import (
    normalize_locale,
    normalize_request_path,
    path_is_reserved,
)

LOGGER = logging.getLogger(__name__)

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


class RenderPageProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    route_kind: Literal["page"] = "page"
    render_mode: str
    site: ProjectionSite
    requested_path: str
    matched_path: str
    locale: str
    page: ProjectionPage
    composition: ProjectionComposition
    theme: dict[str, Any] = Field(default_factory=dict)
    locales: tuple[ProjectionLocale, ...] = ()
    navigation: tuple[ProjectionNavigation, ...] = ()
    bindings: dict[str, tuple[dict[str, Any], ...]] = Field(default_factory=dict)


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
        prefix = f"/preview/{workspace_id}"
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
            "projection_spec, pagination_spec, definition_version "
            "FROM content.collection_view WHERE id = $1 LIMIT 1",
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
        type_row = await connection.fetchrow(
            "SELECT site_id, status, definition_version "
            "FROM content.content_type WHERE id = $1 LIMIT 1",
            view[2],
        )
        if type_row is None or type_row[0] != site_id:
            raise ProjectionError("collection_scope")
        if type_row[1] != "ACTIVE":
            raise ProjectionError("collection_scope")
        if type_row[2] != view[8]:
            raise ProjectionError("stale_collection_definition")
        field_rows = await connection.fetch(
            "SELECT key, field_type, localized, validation, cardinality, required "
            "FROM content.field_definition WHERE type_id = $1 "
            'ORDER BY key COLLATE "C"',
            view[2],
        )
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
                filter_spec, sort_spec, projection_spec, pagination_spec, field_defs
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
        requested_limit = node.props.get("limit", pagination_spec.get("limit", 24))
        if (
            isinstance(requested_limit, bool)
            or not isinstance(requested_limit, int)
            or not 1 <= requested_limit <= MAX_PAGE_SIZE
        ):
            raise ProjectionError("collection_limit")
        offset = pagination_spec.get("offset", 0)
        candidate_count = await connection.fetchval(
            "SELECT count(*) FROM content.content_item "
            "WHERE site_id = $1 AND type_id = $2 AND status = ANY($3::text[])",
            site_id,
            view[2],
            statuses,
        )
        if not isinstance(candidate_count, int) or candidate_count > MAX_CANDIDATES:
            raise ProjectionError("query_cost")
        rows = await connection.fetch(
            "SELECT id, site_id, type_id, slug, status, values "
            "FROM content.content_item WHERE site_id = $1 AND type_id = $2 "
            "AND status = ANY($3::text[]) ORDER BY id",
            site_id,
            view[2],
            statuses,
        )
        if len(rows) > MAX_CANDIDATES:
            raise ProjectionError("query_cost")
        items: list[dict[str, Any]] = []
        for row in rows:
            if row[1] != site_id or row[2] != view[2]:
                raise ProjectionError("collection_scope")
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
        try:
            sort_collection_items(items, sort_spec)
        except (TypeError, ValueError):
            raise ProjectionError("malformed_item") from None
        page = items[offset : offset + requested_limit]
        bindings[str(node.id)] = tuple(
            {
                **item,
                "values": {field: item["values"][field] for field in projection_fields},
            }
            for item in page
        )
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
        self, connection: Any, *, site_id: UUID
    ) -> tuple[list[Any], tuple[ProjectionLocale, ...], str]:
        rows = list(
            await connection.fetch(
                'SELECT id,site_id,tag,enabled,is_default,"position",metadata '
                "FROM content.site_locale WHERE site_id=$1 "
                'ORDER BY "position",tag COLLATE "C"',
                site_id,
            )
        )
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

    async def _resolve_page(
        self,
        connection: Any,
        *,
        site_id: UUID,
        route: str,
        locale: str,
        statuses: list[str],
    ) -> Any:
        rows = list(
            await connection.fetch(
                "SELECT * FROM content.slaif_render_page_resolve($1,$2,$3,$4)",
                site_id,
                route,
                locale,
                statuses,
            )
        )
        if len(rows) != 1:
            raise ProjectionError("not_found")
        row = rows[0]
        if row[1] != site_id or str(row[5]).casefold() != locale.casefold():
            raise ProjectionError("not_found")
        return row

    async def _redirects(
        self,
        connection: Any,
        *,
        site_id: UUID,
        route: str,
        locale: str,
        default_locale: str,
        statuses: list[str],
    ) -> ProjectionRedirect | None:
        rows = list(
            await connection.fetch(
                "SELECT id,site_id,source_route,target,status_code,locale "
                "FROM content.redirect WHERE site_id=$1 "
                'ORDER BY source_route COLLATE "C",locale NULLS FIRST',
                site_id,
            )
        )
        if len(rows) > MAX_REDIRECTS:
            raise ProjectionError("redirect_state")
        redirects: dict[tuple[str, str | None], ProjectionRedirect] = {}
        enabled = {
            str(row[0]).casefold()
            for row in await connection.fetch(
                "SELECT tag FROM content.site_locale WHERE site_id=$1 AND enabled",
                site_id,
            )
        }
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
            try:
                await self._resolve_page(
                    connection,
                    site_id=site_id,
                    route=redirect.source,
                    locale=redirect.locale or default_locale,
                    statuses=statuses,
                )
            except ProjectionError as error:
                if error.reason != "not_found":
                    raise ProjectionError("redirect_state") from None
            else:
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
                try:
                    await self._resolve_page(
                        connection,
                        site_id=site_id,
                        route=cursor,
                        locale=chain_locale,
                        statuses=statuses,
                    )
                except ProjectionError:
                    raise ProjectionError("redirect_dangling") from None
                return
            raise ProjectionError("redirect_chain")

        for redirect in redirects.values():
            await validate_chain(redirect)
        selected = redirects.get((route, locale)) or redirects.get((route, None))
        return selected

    async def _navigation(
        self,
        connection: Any,
        *,
        site_id: UUID,
        selected_locale: str,
        default_locale: str,
        statuses: list[str],
    ) -> tuple[ProjectionNavigation, ...]:
        nav_rows = list(
            await connection.fetch(
                "SELECT id,site_id,key,label,labels,settings FROM content.navigation "
                'WHERE site_id=$1 ORDER BY key COLLATE "C"',
                site_id,
            )
        )
        if len(nav_rows) > MAX_NAVIGATIONS:
            raise ProjectionError("navigation_too_large")
        enabled_tags = {
            str(row[0]).casefold()
            for row in await connection.fetch(
                "SELECT tag FROM content.site_locale WHERE site_id=$1 AND enabled",
                site_id,
            )
        }
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

        item_rows = list(
            await connection.fetch(
                "SELECT * FROM content.slaif_render_navigation_items($1,$2,$3)",
                site_id,
                selected_locale,
                statuses,
            )
        )
        if len(item_rows) > MAX_NAVIGATION_ITEMS:
            raise ProjectionError("navigation_too_large")
        all_items: dict[UUID, dict[str, Any]] = {}
        sibling_positions: dict[tuple[UUID, UUID | None], set[int]] = defaultdict(set)
        children: defaultdict[UUID | None, list[dict[str, Any]]] = defaultdict(list)
        for row in item_rows:
            if (
                row[1] != site_id
                or row[2] not in nav_by_id
                or row[0] in all_items
                or row[3] == row[0]
            ):
                raise ProjectionError("navigation_scope")
            item_locale = row[8]
            if item_locale is not None and (
                str(item_locale).casefold() not in enabled_tags
            ):
                raise ProjectionError("navigation_locale")
            position = int(row[9])
            sibling_key = (row[2], row[3])
            if position in sibling_positions[sibling_key]:
                raise ProjectionError("navigation_position")
            sibling_positions[sibling_key].add(position)
            labels = _label_map(row[7])
            label = labels.get(selected_locale) or labels.get(default_locale)
            if not isinstance(label, str) or not label.strip():
                raise ProjectionError("navigation_label")
            target_kind = str(row[5])
            target_value = str(row[10])
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
                "id": row[0],
                "site_id": row[1],
                "navigation_id": row[2],
                "parent_id": row[3],
                "page_id": row[4],
                "locale": item_locale,
                "position": position,
                "label": label,
                "labels": labels,
                "target": ProjectionNavigationTarget(
                    kind=target_kind, value=target_value
                ),
            }
            all_items[row[0]] = item
            children[row[3]].append(item)

        for (navigation_id, parent_id), positions in sibling_positions.items():
            if positions != set(range(len(positions))):
                raise ProjectionError("navigation_position")
            if parent_id is not None:
                parent = all_items.get(parent_id)
                if parent is None or parent["navigation_id"] != navigation_id:
                    raise ProjectionError("navigation_parent")

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
            if item["locale"] is not None and (
                item["locale"].casefold() != selected_locale.casefold()
            ):
                raise ProjectionError("navigation_parent")
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
            return ProjectionNavigationItem(**item, children=child_items)

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

    async def _query(
        self,
        connection: Any,
        *,
        context: SiteContext,
        request: RenderPageRequest,
        render_mode: str,
    ) -> RenderRouteProjection:
        locales, projected_locales, default_locale = await self._locales(
            connection, site_id=context.site_id
        )
        route, locale = _route_parts(context, request.path, request.locale, locales)
        statuses = ["PUBLISHED", "DRAFT"] if render_mode == "preview" else ["PUBLISHED"]
        redirect = await self._redirects(
            connection,
            site_id=context.site_id,
            route=route,
            locale=locale,
            default_locale=default_locale,
            statuses=statuses,
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
        row = await self._resolve_page(
            connection,
            site_id=context.site_id,
            route=route,
            locale=locale,
            statuses=statuses,
        )
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
        navigation = await self._navigation(
            connection,
            site_id=context.site_id,
            selected_locale=locale,
            default_locale=default_locale,
            statuses=statuses,
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
            matched_path=page.effective_route,
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
            locales=projected_locales,
            navigation=navigation,
            bindings=bindings,
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
                        connection,
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
            async with _repeatable_read_cow(
                pool,
                session_id=trusted_workspace_id,
                acquire_timeout=self._database.acquire_timeout,
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
                snapshot_context = await self._context_on_connection(
                    cow.native, request
                )
                if snapshot_context.site_id != context.site_id:
                    raise ProjectionError("not_found")
                return await self._query(
                    cow.native,
                    context=snapshot_context,
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
                        cow.native,
                        context=snapshot_context,
                        request=request,
                        render_mode="preview",
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
    "RenderPreviewRequest",
    "RenderRouteProjection",
    "RenderProjectionService",
]

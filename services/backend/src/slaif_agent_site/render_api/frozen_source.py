"""Shared Render read surface: live database and frozen snapshot adapters.

083/5 R3 seam.  Canonical, active preview and frozen review all execute
the same trusted projection helpers in ``projection.py``.  This module
owns only the data-source boundary:

* ``RenderReadSurface`` - the narrow read protocol.  Adapters provide
  bounded, typed raw rows and COMPLETE candidate sets (every non-deleted
  site page, every raw navigation item, every retained family row); no
  read may silently drop a candidate the shared helpers must consider.
* ``DatabaseRenderSurface`` - the live database implementation.  Every
  statement is the exact trusted SQL the render service always used,
  except where an overflow sentinel is added (documented below).
* ``FrozenRenderSurface`` - the immutable ``review-snapshot/v2``
  implementation.  One ``control.slaif_review_snapshot_frozen_state``
  row (COMPLETE snapshots only) is the sole input.
* ``admit_frozen_snapshot`` - the shared verified admission seam (R7).
  Every frozen row is verified BEFORE any projection work: the exact
  14-column row shape, the expected snapshot/site/workspace identities,
  the exact 18-key payload, the supported state version, the trusted
  six version pins at the row AND payload level, the pinned catalog
  version, payload/normalized-state integrity (canonical-text equal),
  the recomputed canonical digest (mismatch refusal), the sibling
  bindings (validation report, media references, browser evidence,
  created_by/created_at, site profile), the COMPLETE exact
  shape/reference/uniqueness validation of every retained family row
  (deleted page tombstones included; navigation parents bound against
  the complete same-navigation id set; style rows bound to their own
  page) and the bounded-work gates in order before any serialization,
  allocation or family index: raw-value depth (<= 8 on the exact
  fields the 076 capture preflight depth-gates), the valid
  component-tree depth (<= 17 node chain, <= 128 nodes per page), the
  capture row caps, and the derived whole-document depth bound (<=
  45) - each on the payload AND its normalized counterpart.  Any
  malformation is the stable ``not_found`` refusal;
  ``FrozenRenderSurface`` accepts only the seam's verified result.

Digest coverage: the digest is the SHA-256 of the exact canonical
serialization of the stored ``payload`` (``content_model.canonical``,
byte-identical to the SQL canonical form for every supported value);
recomputing it proves the payload bytes are exactly what the trusted
capture produced, and the row id/workspace/site columns bind the
verified document to the authorized snapshot.  The sibling columns
(version pins, validation report, media references, browser evidence)
are shape-checked against the capture emitter; the row/ID identity
guarantee additionally comes from the caller passing the exact
expected snapshot id the read was authorized for.

Live overflow sentinels (honest policy note): ``fetch_pages`` (4097),
``fetch_locales`` (333), ``fetch_enabled_locale_tags`` (33),
``fetch_redirects`` (257), ``fetch_navigation_definitions`` (17),
``fetch_navigation_items`` (4097), ``fetch_composition`` (129),
``fetch_field_definitions`` (65) and ``fetch_content_items`` (1001)
carry a LIMIT of one past the product/capture cap and refuse
fail-closed on overflow.  Under the cap (the only state reachable
through the product write path) the result set and the shared-helper
semantics are byte-for-byte unchanged; an over-cap live site now
refuses with the same stable reason the engine used to raise after
fetching (or, for the page set, ``unavailable`` via the service
mapping) instead of doing unbounded SQL/Python work.  ``fetch_regions``
is structurally bounded (at most header+footer rows).

Numeric boundary: the frozen payload retains exact digits/scale (the
digest is computed over the raw document).  The values the shared
engine consumes are a DERIVED render copy: integer-valued numbers
stay int and fractional numbers become float, exactly the types the
live path receives from asyncpg jsonb decoding of PG canonical numeric
text.  The retained raw document is never mutated and no validator is
widened.

Route, navigation and ancestor resolution (the 050
``slaif_agent_page_effective_route`` effective body, the 056
``slaif_render_page_resolve`` winner selection, the 057
``slaif_navigation_page_target_validate`` PAGE target validator, the
059 ``slaif_render_navigation_items``/
``slaif_render_internal_target_exists`` locale-neutral upgrade and the
067 ``slaif_page_ancestor_chain`` behavior; 049/052 are the initial
creates and immutable history) are ported ONCE into the shared pure
helpers in this module (section below).  The live
(``DatabaseRenderSurface``) and frozen (``FrozenRenderSurface``) paths
execute that identical code over the complete candidate sets these
adapters provide, through the service wiring in ``projection.py``; the
differential proof against the actual effective SQL lives in the
integration tests.  One render request shares a single per-request
route memo, so every retained page's effective route is derived at
most once per request (R8 total-work bound).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Final, Protocol, TypeGuard
from uuid import UUID

from slaif_agent_site.content_model.canonical import (
    CanonicalBudgetExceeded,
    canonical_json_bounded,
)
from slaif_agent_site.content_model.query_dsl import MAX_CANDIDATES

__all__ = [
    "COMPONENT_CATALOG_VERSION",
    "DatabaseRenderSurface",
    "FrozenRenderSurface",
    "MAX_PAGES",
    "RenderPageFact",
    "RenderReadSurface",
    "SurfaceReadError",
    "SUPPORTED_STATE_VERSION",
    "TRUSTED_WORKSPACE_VERSIONS",
    "admit_frozen_snapshot",
    "navigation_resolved_items",
    "new_route_memo",
    "page_ancestor_chain",
    "page_effective_route",
    "resolve_page_route",
]

# ---------------------------------------------------------------------------
# R7 trusted version pins.
#
# The exact literal the 076 trusted constructors stamp into
# ``control.workspace.version_facts`` (and the 076 materializer gate
# compares against) and the exact row-level ``versions`` map the v2
# snapshot builder stores.  Capture, read and approval all compare
# against these constants; a unit test pins them equal to the
# review-worker / design-system / component-catalog constants without a
# cross-service import.
SUPPORTED_STATE_VERSION: Final[str] = "review-snapshot/v2"
COMPONENT_CATALOG_VERSION: Final[str] = "catalog-v1"
TRUSTED_WORKSPACE_VERSIONS: Final[Mapping[str, str]] = {
    "catalog": "catalog-v1",
    "composition_schema": "site-composition/v1",
    "content_model": "content-model/v1",
    "design_system": "design-system/v1",
    "puck": "0.20.2",
    "renderer": "renderer-v1",
}

# ---------------------------------------------------------------------------
# R8 read-side bounds: the exact capture budgets the 076 materializer
# preflights.  Every stored v2 document satisfies them; a malformed or
# forged document violating one is refused at admission, before any
# projection work.  A unit test pins each value equal to the
# review_worker.snapshot capture constant (no cross-service import).
MAX_PAGES: Final[int] = 4096
MAX_COMPOSITIONS_PER_PAGE: Final[int] = 128
MAX_COMPOSITIONS_TOTAL: Final[int] = 131_072
MAX_LOCALES: Final[int] = 32
MAX_REGIONS: Final[int] = 8
MAX_NAVIGATIONS: Final[int] = 16
MAX_NAVIGATION_ITEMS: Final[int] = 4096
MAX_NAVIGATION_ITEMS_PER_GROUP: Final[int] = 256
MAX_REDIRECTS: Final[int] = 256
MAX_MEDIA_INVENTORY: Final[int] = 4096
MAX_PROPOSALS: Final[int] = 10_000
MAX_CONTENT_TYPES: Final[int] = 64
MAX_FIELDS_PER_TYPE: Final[int] = 64
MAX_ITEMS_PER_TYPE: Final[int] = 2000
MAX_TRANSLATIONS_TOTAL: Final[int] = 20_000
MAX_VIEWS_PER_TYPE: Final[int] = 64
MAX_RELATIONS_PER_PAIR: Final[int] = 1000
RAW_VALUE_MAX_DEPTH: Final[int] = 8
MAX_CANONICAL_PAYLOAD_BYTES: Final[int] = 8 * 1024 * 1024

# The builder's exact component-chain gate (MAX_COMPONENT_DEPTH 16 edges
# + 1 node) mirrored locally (no cross-service import; a unit test pins
# the value equal to the review_worker.snapshot constant).
COMPONENT_CHAIN_MAX_NODES: Final[int] = 17

# The maximum whole-document raw container depth of any v2 document the
# trusted capture emits, derived from the capture invariants: the payload
# envelope to a first normalized node (payload -> pages -> row -> nodes ->
# node = 5 containers), the deepest node at the full component chain
# (each further node adds a children list + a node dict), that node's
# gated raw props container, and the RAW_VALUE_MAX_DEPTH containers the
# props depth gate allows.  Every document the capture produces is at or
# below this depth; anything deeper is malformed and is refused BEFORE any
# serialization allocation (bounded-work ordering).
MAX_WHOLE_DOCUMENT_RAW_DEPTH: Final[int] = (
    5 + 2 * (COMPONENT_CHAIN_MAX_NODES - 1) + 1 + RAW_VALUE_MAX_DEPTH - 1
)  # = 45

# Finite element-width bound for the raw-depth walkers: the largest 076
# per-family cost share (items 1572864).  A retained jsonb value cannot
# carry more elements than the byte share of its family (every element
# serializes to at least one byte), so any wider container is malformed
# and refuses BEFORE the walker expands the sibling list onto its stack
# (explicit finite work bound, not an unbounded frontier).
MAX_SINGLE_VALUE_ELEMENT_COUNT: Final[int] = 1_572_864

# The supported site status column values (the frozen site profile must
# carry a captured status the SiteContext can express; the frozen view
# uses the CAPTURED status, never a live re-read).
_SUPPORTED_SITE_STATUSES: Final[frozenset[str]] = frozenset({"ACTIVE", "ARCHIVED"})

_DIGEST_SHAPE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")


class SurfaceReadError(RuntimeError):
    """A stable, non-leaking read-surface refusal.

    ``reason`` is the ``projection.ProjectionError`` vocabulary the
    service maps on (``not_found`` for snapshot/shape refusals, the
    stable engine reason for each bound refusal, ``page_set_too_large``
    for the R8 candidate bound which the service maps to
    ``unavailable``).
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _refusal() -> SurfaceReadError:
    return SurfaceReadError("not_found")


@dataclass(frozen=True, slots=True)
class RenderPageFact:
    """One complete retained page row (the 049/056 port's input fact).

    Mirrors the live ``content.page`` columns the resolution semantics
    consume (any status, non-deleted only); ``effective_route`` is
    computed by the shared port, never stored here.
    """

    id: UUID
    site_id: UUID
    slug: str
    title: str
    status: str
    locale: str
    parent_id: UUID | None
    route_template: str | None
    row_version: int


# ---------------------------------------------------------------------------
# Typed row shapes (exact live SELECT column order; the shared helpers
# consume them by position, unchanged).
# ---------------------------------------------------------------------------
LocaleRow = tuple[UUID, UUID, str, bool, bool, int, Any]
EnabledTagRow = tuple[str,]
PageFactRow = RenderPageFact
RedirectRow = tuple[UUID, UUID, str, str, int, str | None]
NavigationDefinitionRow = tuple[UUID, UUID, str, Any, Any, Any]
NavigationItemRawRow = tuple[
    UUID, UUID, UUID, UUID | None, UUID | None, str, str, Any, str | None, int
]
NavigationItemRow = tuple[
    UUID, UUID, UUID, UUID | None, UUID | None, str, str, Any, str | None, int, str
]
ThemeRow = tuple[UUID, UUID, str, str, int, Any, Any, Any, Any, datetime, datetime]
PageStyleRow = tuple[UUID, UUID, UUID, str, int, Any, Any, Any, Any]
RegionRow = tuple[UUID, UUID, str, str, Any, str, int, Any, Any]
CompositionRow = tuple[UUID, UUID, UUID, str, str, UUID | None, str, int, Any, Any, Any]
MediaRow = tuple[str, int, str, str]
CollectionViewRow = tuple[UUID, UUID, UUID, str, Any, Any, Any, Any, Any]
ContentTypeRow = tuple[UUID, str, Any]
FieldDefinitionRow = tuple[str, str, bool, Any, Any, bool]
ContentItemRow = tuple[UUID, UUID, UUID, str, str, Any, Any]
ContentItemTranslationRow = tuple[UUID, str, Any]
AncestorRow = tuple[int, UUID, UUID, str, str, str]


class RenderReadSurface(Protocol):
    """The 18 named logical reads the shared projection helpers perform."""

    async def fetch_locales(self, *, site_id: UUID) -> tuple[LocaleRow, ...]:
        """All ``content.site_locale`` rows (live: exact trusted SELECT,
        overflow sentinel)."""

    async def fetch_enabled_locale_tags(
        self, *, site_id: UUID
    ) -> tuple[EnabledTagRow, ...]:
        """Enabled locale tags (live: exact trusted SELECT, overflow
        sentinel)."""

    async def fetch_pages(self, *, site_id: UUID) -> tuple[PageFactRow, ...]:
        """COMPLETE candidate set: every non-deleted site page, any
        locale, any status (live: exact trusted SELECT + overflow
        sentinel at the R8 page cap)."""

    async def fetch_redirects(self, *, site_id: UUID) -> tuple[RedirectRow, ...]:
        """All ``content.redirect`` rows (live: exact trusted SELECT,
        overflow sentinel)."""

    async def fetch_navigation_definitions(
        self, *, site_id: UUID
    ) -> tuple[NavigationDefinitionRow, ...]:
        """All ``content.navigation`` rows (live: exact trusted SELECT,
        overflow sentinel)."""

    async def fetch_navigation_items(
        self, *, site_id: UUID
    ) -> tuple[NavigationItemRawRow, ...]:
        """COMPLETE raw ``content.navigation_item`` rows (the 052 port's
        input; live: exact trusted SELECT, no per-item SQL resolution,
        overflow sentinel)."""

    async def fetch_theme(self, *, site_id: UUID) -> ThemeRow | None:
        """``content.slaif_theme_project`` row (live: exact trusted call)."""

    async def fetch_page_style(self, *, page_id: UUID) -> PageStyleRow | None:
        """``content.slaif_page_style_project`` row (live: exact call;
        zero rows for a deleted page -> ``None``)."""

    async def fetch_catalog_version(self, *, site_id: UUID) -> str | None:
        """``control.slaif_site_render_catalog`` (live: exact trusted
        call; the captured site profile fact for the frozen surface)."""

    async def fetch_regions(self, *, site_id: UUID) -> tuple[RegionRow, ...]:
        """``content.slaif_region_list`` rows (live: exact trusted
        call; structurally at most header+footer)."""

    async def fetch_composition(
        self, *, site_id: UUID, page_id: UUID
    ) -> tuple[CompositionRow, ...]:
        """One page's composition rows in the exact live renderer SELECT
        order (parent_id NULLS FIRST, slot_key, order_key, id),
        overflow sentinel at the per-page component cap."""

    async def resolve_media(self, *, site_id: UUID, media_id: UUID) -> MediaRow | None:
        """``content.slaif_render_media_resolve`` row (live: exact
        trusted call; the stored frozen media map entry otherwise)."""

    async def fetch_collection_view(self, *, view_id: UUID) -> CollectionViewRow | None:
        """One ``content.collection_view`` row (live: exact trusted SELECT)."""

    async def fetch_content_type(self, *, type_id: UUID) -> ContentTypeRow | None:
        """One ``content.content_type`` row (live: exact trusted SELECT)."""

    async def fetch_field_definitions(
        self, *, type_id: UUID
    ) -> tuple[FieldDefinitionRow, ...]:
        """``content.field_definition`` rows (live: exact trusted SELECT,
        overflow sentinel at the per-type capture cap)."""

    async def count_content_items(
        self, *, site_id: UUID, type_id: UUID, statuses: Sequence[str]
    ) -> int:
        """Candidate count (live: exact trusted count)."""

    async def fetch_content_items(
        self, *, site_id: UUID, type_id: UUID, statuses: Sequence[str]
    ) -> tuple[ContentItemRow, ...]:
        """COMPLETE candidate items (live: exact trusted SELECT,
        overflow sentinel at the query candidate cap)."""

    async def fetch_content_item_translations(
        self,
        *,
        site_id: UUID,
        item_ids: Sequence[UUID],
        locales: Sequence[str],
    ) -> tuple[ContentItemTranslationRow, ...]:
        """Item translations for the bounded page (live: exact SELECT;
        structurally bounded by the page size x locales)."""


# ---------------------------------------------------------------------------
# Live database adapter.
# ---------------------------------------------------------------------------
class DatabaseRenderSurface:
    """Live read surface: the exact trusted SQL, memoized per request.

    The overflow sentinels are LIMITs of one past the product/capture
    cap with a fail-closed refusal on overflow (see module docstring):
    under the cap the fetched set is byte-for-byte the previous one.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection
        self._cache: dict[tuple[Any, ...], Any] = {}

    async def _fetch(self, key: tuple[Any, ...], statement: str, *args: Any) -> Any:
        if key not in self._cache:
            self._cache[key] = await self._connection.fetch(statement, *args)
        return self._cache[key]

    async def _fetchrow(self, statement: str, *args: Any) -> Any:
        return await self._connection.fetchrow(statement, *args)

    async def fetch_locales(self, *, site_id: UUID) -> tuple[LocaleRow, ...]:
        rows = await self._fetch(
            ("locales", site_id),
            'SELECT id,site_id,tag,enabled,is_default,"position",metadata '
            "FROM content.site_locale WHERE site_id=$1 "
            'ORDER BY "position",tag COLLATE "C" LIMIT 33',
            site_id,
        )
        if len(rows) > MAX_LOCALES:
            raise SurfaceReadError("locale_state")
        return tuple(tuple(row) for row in rows)

    async def fetch_enabled_locale_tags(
        self, *, site_id: UUID
    ) -> tuple[EnabledTagRow, ...]:
        rows = await self._fetch(
            ("locale_tags", site_id),
            "SELECT tag FROM content.site_locale WHERE site_id=$1 AND enabled LIMIT 33",
            site_id,
        )
        if len(rows) > MAX_LOCALES:
            raise SurfaceReadError("locale_state")
        return tuple((str(row[0]),) for row in rows)

    async def fetch_pages(self, *, site_id: UUID) -> tuple[PageFactRow, ...]:
        rows = await self._fetch(
            ("pages", site_id),
            "SELECT id, site_id, slug, title, status, locale, parent_id, "
            "route_template, row_version FROM content.page "
            "WHERE site_id = $1 AND deleted_at IS NULL "
            'ORDER BY locale COLLATE "C", slug COLLATE "C", id LIMIT 4097',
            site_id,
        )
        if len(rows) > MAX_PAGES:
            raise SurfaceReadError("page_set_too_large")
        return tuple(
            RenderPageFact(
                id=row[0],
                site_id=row[1],
                slug=row[2],
                title=row[3],
                status=row[4],
                locale=row[5],
                parent_id=row[6],
                route_template=row[7],
                row_version=int(row[8]),
            )
            for row in rows
        )

    async def fetch_redirects(self, *, site_id: UUID) -> tuple[RedirectRow, ...]:
        rows = await self._fetch(
            ("redirects", site_id),
            "SELECT id,site_id,source_route,target,status_code,locale "
            "FROM content.redirect WHERE site_id=$1 "
            'ORDER BY source_route COLLATE "C",locale NULLS FIRST LIMIT 257',
            site_id,
        )
        if len(rows) > MAX_REDIRECTS:
            raise SurfaceReadError("redirect_state")
        return tuple(tuple(row) for row in rows)

    async def fetch_navigation_definitions(
        self, *, site_id: UUID
    ) -> tuple[NavigationDefinitionRow, ...]:
        rows = await self._fetch(
            ("navigation_definitions", site_id),
            "SELECT id,site_id,key,label,labels,settings FROM content.navigation "
            'WHERE site_id=$1 ORDER BY key COLLATE "C" LIMIT 17',
            site_id,
        )
        if len(rows) > MAX_NAVIGATIONS:
            raise SurfaceReadError("navigation_too_large")
        return tuple(tuple(row) for row in rows)

    async def fetch_navigation_items(
        self, *, site_id: UUID
    ) -> tuple[NavigationItemRawRow, ...]:
        rows = await self._fetch(
            ("navigation_items", site_id),
            "SELECT id, site_id, navigation_id, parent_id, page_id, "
            "target_kind, target_value, labels, locale, position "
            "FROM content.navigation_item WHERE site_id = $1 ORDER BY id "
            "LIMIT 4097",
            site_id,
        )
        if len(rows) > MAX_NAVIGATION_ITEMS:
            raise SurfaceReadError("navigation_too_large")
        return tuple(tuple(row) for row in rows)

    async def fetch_theme(self, *, site_id: UUID) -> ThemeRow | None:
        row = await self._fetchrow(
            "SELECT * FROM content.slaif_theme_project($1)", site_id
        )
        return tuple(row) if row is not None else None

    async def fetch_page_style(self, *, page_id: UUID) -> PageStyleRow | None:
        row = await self._fetchrow(
            "SELECT * FROM content.slaif_page_style_project($1)", page_id
        )
        return tuple(row) if row is not None else None

    async def fetch_catalog_version(self, *, site_id: UUID) -> str | None:
        row = await self._fetchrow(
            "SELECT control.slaif_site_render_catalog($1)", site_id
        )
        return row[0] if row is not None else None

    async def fetch_regions(self, *, site_id: UUID) -> tuple[RegionRow, ...]:
        rows = await self._fetch(
            ("regions", site_id),
            "SELECT * FROM content.slaif_region_list($1)",
            site_id,
        )
        return tuple(tuple(row) for row in rows)

    async def fetch_composition(
        self, *, site_id: UUID, page_id: UUID
    ) -> tuple[CompositionRow, ...]:
        rows = await self._fetch(
            ("composition", site_id, page_id),
            "SELECT id, site_id, page_id, component_type, schema_version, "
            "parent_id, slot_key, order_key, props, created_at, updated_at "
            "FROM content.page_composition WHERE site_id = $1 AND page_id = $2 "
            "ORDER BY parent_id NULLS FIRST, slot_key, order_key, id LIMIT 129",
            site_id,
            page_id,
        )
        if len(rows) > MAX_COMPOSITIONS_PER_PAGE:
            raise SurfaceReadError("composition_too_large")
        return tuple(tuple(row) for row in rows)

    async def resolve_media(self, *, site_id: UUID, media_id: UUID) -> MediaRow | None:
        row = await self._fetchrow(
            "SELECT * FROM content.slaif_render_media_resolve($1,$2)",
            site_id,
            media_id,
        )
        return tuple(row) if row is not None else None

    async def fetch_collection_view(self, *, view_id: UUID) -> CollectionViewRow | None:
        row = await self._fetchrow(
            "SELECT id, site_id, type_id, key, filter_spec, sort_spec, "
            "projection_spec, pagination_spec, definition_version "
            "FROM content.collection_view WHERE id = $1 LIMIT 1",
            view_id,
        )
        return tuple(row) if row is not None else None

    async def fetch_content_type(self, *, type_id: UUID) -> ContentTypeRow | None:
        row = await self._fetchrow(
            "SELECT site_id, status, definition_version "
            "FROM content.content_type WHERE id = $1 LIMIT 1",
            type_id,
        )
        return tuple(row) if row is not None else None

    async def fetch_field_definitions(
        self, *, type_id: UUID
    ) -> tuple[FieldDefinitionRow, ...]:
        rows = await self._fetch(
            ("field_definitions", type_id),
            "SELECT key, field_type, localized, validation, cardinality, "
            "required FROM content.field_definition WHERE type_id = $1 "
            'ORDER BY key COLLATE "C" LIMIT 65',
            type_id,
        )
        if len(rows) > MAX_FIELDS_PER_TYPE:
            raise SurfaceReadError("unsupported_collection_query")
        return tuple(tuple(row) for row in rows)

    async def count_content_items(
        self, *, site_id: UUID, type_id: UUID, statuses: Sequence[str]
    ) -> int:
        return int(
            await self._connection.fetchval(
                "SELECT count(*) FROM content.content_item "
                "WHERE site_id = $1 AND type_id = $2 AND status = ANY($3::text[])",
                site_id,
                type_id,
                statuses,
            )
        )

    async def fetch_content_items(
        self, *, site_id: UUID, type_id: UUID, statuses: Sequence[str]
    ) -> tuple[ContentItemRow, ...]:
        rows = await self._fetch(
            ("content_items", site_id, type_id, tuple(statuses)),
            "SELECT id, site_id, type_id, slug, status, values, "
            "type_definition_version FROM content.content_item "
            "WHERE site_id = $1 AND type_id = $2 AND status = ANY($3::text[]) "
            "ORDER BY id LIMIT 1001",
            site_id,
            type_id,
            statuses,
        )
        if len(rows) > MAX_CANDIDATES:
            # The shared helper enforces the product MAX_CANDIDATES bound
            # on the returned rows; this sentinel refuses a pathological
            # candidate set before any allocation grows, with the same
            # stable reason the helper used to raise.
            raise SurfaceReadError("query_cost")
        return tuple(tuple(row) for row in rows)

    async def fetch_content_item_translations(
        self,
        *,
        site_id: UUID,
        item_ids: Sequence[UUID],
        locales: Sequence[str],
    ) -> tuple[ContentItemTranslationRow, ...]:
        rows = await self._connection.fetch(
            "SELECT item_id, locale, localized_values "
            "FROM content.content_item_translation "
            "WHERE site_id=$1 AND item_id=ANY($2::uuid[]) "
            "AND locale=ANY($3::text[])",
            site_id,
            list(item_ids),
            list(locales),
        )
        return tuple(tuple(row) for row in rows)


# ---------------------------------------------------------------------------
# Frozen (immutable review-snapshot/v2) adapter.
# ---------------------------------------------------------------------------
_FAMILIES: Final[tuple[str, ...]] = (
    "state_version",
    "workspace_id",
    "site_id",
    "site",
    "base_site_revision",
    "operation_watermark",
    "workspace_versions",
    "locales",
    "theme",
    "regions",
    "navigation",
    "redirects",
    "pages",
    "page_compositions",
    "content",
    "proposals",
    "media_inventory",
    "media",
)
_FAMILY_LISTS: Final[tuple[str, ...]] = (
    "locales",
    "regions",
    "redirects",
    "pages",
    "page_compositions",
    "proposals",
    "media_inventory",
)
_FROZEN_ROW_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "workspace_id",
        "site_id",
        "status",
        "revision_watermark",
        "versions",
        "normalized_state",
        "validation_report",
        "media_references",
        "browser_evidence",
        "payload",
        "digest",
        "created_by",
        "created_at",
    }
)
_VALIDATION_REPORT_KEYS: Final[frozenset[str]] = frozenset(
    {"state_version", "pages_validated", "errors", "cancelled_by_freeze"}
)
_MEDIA_REFERENCE_KEYS: Final[frozenset[str]] = frozenset(
    {"id", "mime_type", "size_bytes", "content_hash", "public_status"}
)
_SITE_PROFILE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "site_key",
        "display_name",
        "status",
        "default_locale",
        "component_catalog_version",
        "content_model_revision",
        "created_at",
        "updated_at",
    }
)
_LOCALE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "tag",
        "enabled",
        "is_default",
        "position",
        "metadata",
        "row_version",
        "created_at",
        "updated_at",
    }
)
_THEME_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "schema_version",
        "renderer_version",
        "row_version",
        "palette",
        "typography",
        "layout",
        "shape",
        "created_at",
        "updated_at",
    }
)
_PAGE_STYLE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "page_id",
        "site_id",
        "schema_version",
        "row_version",
        "overrides",
        "resolved",
        "created_at",
        "updated_at",
    }
)
_REGION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "region_key",
        "variant",
        "content",
        "schema_version",
        "row_version",
        "created_at",
        "updated_at",
    }
)
_NAVIGATION_DEFINITION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "key",
        "label",
        "settings",
        "created_at",
        "updated_at",
        "labels",
        "row_version",
    }
)
_NAVIGATION_ITEM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "navigation_id",
        "parent_id",
        "page_id",
        "target_kind",
        "target_value",
        "labels",
        "locale",
        "position",
        "row_version",
        "created_at",
        "updated_at",
        "parent_key",
    }
)
_REDIRECT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "source_route",
        "target",
        "status_code",
        "locale",
        "row_version",
        "created_at",
        "updated_at",
    }
)
_PAGE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "slug",
        "title",
        "status",
        "locale",
        "parent_id",
        "route_template",
        "effective_route",
        "row_version",
        "created_at",
        "updated_at",
        "deleted_at",
        "style_overrides",
        "style",
        "nodes",
    }
)
_COMPOSITION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "page_id",
        "component_type",
        "schema_version",
        "parent_id",
        "slot_key",
        "order_key",
        "props",
        "catalog_version",
        "created_at",
        "updated_at",
        "row_version",
    }
)
_CONTENT_TYPE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "key",
        "labels",
        "slug_pattern",
        "status",
        "definition_version",
        "settings",
        "created_at",
        "updated_at",
    }
)
_FIELD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "type_id",
        "key",
        "label",
        "field_type",
        "required",
        "localized",
        "cardinality",
        "position",
        "validation",
        "ui_options",
        "definition_version",
        "created_at",
        "updated_at",
    }
)
_VIEW_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "type_id",
        "key",
        "filter_spec",
        "sort_spec",
        "projection_spec",
        "pagination_spec",
        "created_at",
        "updated_at",
        "definition_version",
        "row_version",
    }
)
_ITEM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "type_id",
        "slug",
        "status",
        "type_definition_version",
        "values",
        "row_version",
        "created_at",
        "updated_at",
    }
)
_TRANSLATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "item_id",
        "locale",
        "localized_values",
        "row_version",
        "created_at",
        "updated_at",
    }
)
_RELATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "source_item_id",
        "field_definition_id",
        "target_item_id",
        "position",
        "metadata",
        "row_version",
        "created_at",
        "updated_at",
    }
)
_PROPOSAL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "workspace_id",
        "kind",
        "payload",
        "state",
        "created_at",
        "updated_at",
    }
)
_MEDIA_INVENTORY_KEYS: Final[frozenset[str]] = frozenset(
    {
        "id",
        "site_id",
        "uploaded_by",
        "filename",
        "mime_type",
        "size_bytes",
        "content_hash",
        "storage_key",
        "alt_text",
        "metadata",
        "created_at",
        "updated_at",
        "public_status",
        "published_at",
    }
)
_MEDIA_ENTRY_KEYS: Final[frozenset[str]] = frozenset(
    {"id", "mime_type", "size_bytes", "content_hash", "public_status"}
)
_CONTENT_FAMILIES: Final[tuple[str, ...]] = (
    "types",
    "fields",
    "items",
    "translations",
    "relations",
    "views",
)


def _require_keys(value: Any, keys: frozenset[str]) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise _refusal()


def _is_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _int(value: Any) -> int:
    if not _is_int(value):
        raise _refusal()
    return value


def _bool(value: Any) -> bool:
    if not isinstance(value, bool):
        raise _refusal()
    return value


def _uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise _refusal()
    try:
        return UUID(value)
    except ValueError:
        raise _refusal() from None


def _text(value: Any) -> str:
    if not isinstance(value, str):
        raise _refusal()
    return value


def _nonempty_text(value: Any) -> str:
    text = _text(value)
    if not text:
        raise _refusal()
    return text


def _optional_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    return _uuid(value)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return _text(value)


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise _refusal()
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise _refusal() from None


def _optional_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    return _timestamp(value)


def _json_object(value: Any) -> dict[Any, Any]:
    if not isinstance(value, dict):
        raise _refusal()
    return value


def _render_value(value: Any) -> Any:
    """Derived render copy of one retained raw JSON value.

    The retained payload keeps exact digits/scale (the admission digest
    is computed over the raw document); the shared engine must instead
    see the same int/float types the live path always receives from
    asyncpg jsonb decoding of PG canonical numeric text: an
    integer-valued number stays ``int``, a fractional one becomes
    ``float``.  Zero is normalized first (PG jsonb stores ``-0`` as
    ``0``).  No validator is widened and the raw document is never
    mutated.
    """
    if isinstance(value, Decimal):
        if value == 0:
            value = abs(value)
        if value.as_tuple().exponent >= 0:
            return int(value)
        return float(value)
    if isinstance(value, dict):
        return {key: _render_value(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_render_value(child) for child in value]
    return value


def _raw_depth_ok(value: Any, max_depth: int = RAW_VALUE_MAX_DEPTH) -> bool:
    """Bounded raw container depth probe (explicit stack, no recursion).

    The default mirrors the 076 capture gate
    ``slaif_review_value_depth(value, 8) > 8``; the whole-document
    admission pass calls it with ``MAX_WHOLE_DOCUMENT_RAW_DEPTH`` to bound
    the recursive serialization work over ANY retained field, gated or
    not.  Container nesting deeper than ``max_depth`` refuses.
    """
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, dict):
            depth += 1
            if depth > max_depth or len(item) > MAX_SINGLE_VALUE_ELEMENT_COUNT:
                return False
            stack.extend((child, depth) for child in item.values())
        elif isinstance(item, list):
            depth += 1
            if depth > max_depth or len(item) > MAX_SINGLE_VALUE_ELEMENT_COUNT:
                return False
            stack.extend((child, depth) for child in item)
    return True


def _check_payload_raw_depth(payload: Mapping[str, Any]) -> None:
    """The exact raw-value fields the 076 capture preflight depth-gates
    (<= 8), checked before any family structure is built."""
    for row in payload["page_compositions"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("props")):
            raise _refusal()
    for page in payload["pages"]:
        if not isinstance(page, dict):
            raise _refusal()
        if not _raw_depth_ok(page.get("style_overrides")):
            raise _refusal()
        style = page.get("style")
        if style is not None:
            if (
                not isinstance(style, dict)
                or not _raw_depth_ok(style.get("overrides"))
                or not _raw_depth_ok(style.get("resolved"))
            ):
                raise _refusal()
        nodes = page.get("nodes")
        if not isinstance(nodes, list):
            raise _refusal()
        for node in nodes:
            if not isinstance(node, dict) or not _raw_depth_ok(node.get("props")):
                raise _refusal()
    for row in payload["locales"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("metadata")):
            raise _refusal()
    theme = payload["theme"]
    if theme is not None:
        if not isinstance(theme, dict):
            raise _refusal()
        for key in ("palette", "typography", "layout", "shape"):
            if not _raw_depth_ok(theme.get(key)):
                raise _refusal()
    for row in payload["regions"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("content")):
            raise _refusal()
    for row in payload["navigation"]["definitions"]:
        if (
            not isinstance(row, dict)
            or not _raw_depth_ok(row.get("settings"))
            or not _raw_depth_ok(row.get("labels"))
        ):
            raise _refusal()
    for row in payload["navigation"]["items"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("labels")):
            raise _refusal()
    content = payload["content"]
    for row in content["types"]:
        if (
            not isinstance(row, dict)
            or not _raw_depth_ok(row.get("labels"))
            or not _raw_depth_ok(row.get("settings"))
        ):
            raise _refusal()
    for row in content["fields"]:
        if (
            not isinstance(row, dict)
            or not _raw_depth_ok(row.get("validation"))
            or not _raw_depth_ok(row.get("ui_options"))
        ):
            raise _refusal()
    for row in content["items"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("values")):
            raise _refusal()
    for row in content["translations"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("localized_values")):
            raise _refusal()
    for row in content["relations"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("metadata")):
            raise _refusal()
    for row in content["views"]:
        if not isinstance(row, dict):
            raise _refusal()
        for key in (
            "filter_spec",
            "sort_spec",
            "projection_spec",
            "pagination_spec",
        ):
            if not _raw_depth_ok(row.get(key)):
                raise _refusal()
    for row in payload["proposals"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("payload")):
            raise _refusal()
    for row in payload["media_inventory"]:
        if not isinstance(row, dict) or not _raw_depth_ok(row.get("metadata")):
            raise _refusal()


def _check_page_node_chains(payload: Mapping[str, Any]) -> None:
    """The builder's exact component-chain and per-page node gates on the
    retained normalized node trees: at most ``COMPONENT_CHAIN_MAX_NODES``
    nodes on any root-to-leaf path and at most
    ``MAX_COMPOSITIONS_PER_PAGE`` nodes per page (one node per
    composition, the write-side per-page cap).

    Bounded explicit-stack walk: the per-page total node bound caps the
    number of stack entries, so a malformed tree (non-mapping node,
    non-list children, or a self-referencing cycle) refuses with the
    stable refusal instead of looping.  The SEPARATE raw-value depth
    (<= 8 per node props) is checked by ``_check_payload_raw_depth``; this
    gate is the valid component-tree depth semantics.
    """
    for page in payload["pages"]:
        if not isinstance(page, dict):
            raise _refusal()
        nodes = page.get("nodes")
        if not isinstance(nodes, list) or len(nodes) > MAX_COMPOSITIONS_PER_PAGE:
            raise _refusal()
        total = 0
        stack: list[tuple[Any, int]] = [(node, 1) for node in nodes]
        while stack:
            node, count = stack.pop()
            if not isinstance(node, dict):
                raise _refusal()
            if count > COMPONENT_CHAIN_MAX_NODES:
                raise _refusal()
            total += 1
            if total > MAX_COMPOSITIONS_PER_PAGE:
                raise _refusal()
            children = node.get("children") or []
            if not isinstance(children, list):
                raise _refusal()
            # A page's total node count is capped at the per-page
            # composition cap, so any single children list is too; check
            # BEFORE the stack growth (finite work bound).
            if len(children) > MAX_COMPOSITIONS_PER_PAGE:
                raise _refusal()
            for child in reversed(children):
                stack.append((child, count + 1))


def _group_count(counts: dict[Any, int], key: Any) -> None:
    """One count for a grouping key; a non-hashable grouping value is a
    malformed row and refuses stably (never an uncaught TypeError)."""
    try:
        counts[key] = counts.get(key, 0) + 1
    except TypeError:
        raise _refusal() from None


def _group_count_field(
    per_type: dict[Any, dict[str, int]], key: Any, name: str
) -> None:
    try:
        group = per_type.setdefault(key, {})
        group[name] = group.get(name, 0) + 1
    except TypeError:
        raise _refusal() from None


def _check_family_caps(payload: Mapping[str, Any]) -> None:
    """The exact 076 capture row caps, checked before any family
    structure is built (a stored v2 document always satisfies them)."""
    if len(payload["pages"]) > MAX_PAGES:
        raise _refusal()
    compositions = payload["page_compositions"]
    if len(compositions) > MAX_COMPOSITIONS_TOTAL:
        raise _refusal()
    per_page: dict[Any, int] = {}
    for row in compositions:
        if isinstance(row, dict):
            key = row.get("page_id")
            _group_count(per_page, key)
    for count in per_page.values():
        if count > MAX_COMPOSITIONS_PER_PAGE:
            raise _refusal()
    if len(payload["locales"]) > MAX_LOCALES:
        raise _refusal()
    if len(payload["regions"]) > MAX_REGIONS:
        raise _refusal()
    definitions = payload["navigation"]["definitions"]
    items = payload["navigation"]["items"]
    if len(definitions) > MAX_NAVIGATIONS:
        raise _refusal()
    if len(items) > MAX_NAVIGATION_ITEMS:
        raise _refusal()
    per_group: dict[tuple[Any, Any], int] = {}
    for row in items:
        if isinstance(row, dict):
            key = (row.get("navigation_id"), row.get("locale"))
            _group_count(per_group, key)
    for count in per_group.values():
        if count > MAX_NAVIGATION_ITEMS_PER_GROUP:
            raise _refusal()
    if len(payload["redirects"]) > MAX_REDIRECTS:
        raise _refusal()
    if len(payload["media_inventory"]) > MAX_MEDIA_INVENTORY:
        raise _refusal()
    if len(payload["proposals"]) > MAX_PROPOSALS:
        raise _refusal()
    if len(payload["media"]) > MAX_MEDIA_INVENTORY:
        raise _refusal()
    content = payload["content"]
    if len(content["types"]) > MAX_CONTENT_TYPES:
        raise _refusal()
    if len(content["translations"]) > MAX_TRANSLATIONS_TOTAL:
        raise _refusal()
    per_type: dict[Any, dict[str, int]] = {}
    for row in content["fields"]:
        if isinstance(row, dict):
            _group_count_field(per_type, row.get("type_id"), "fields")
    for row in content["items"]:
        if isinstance(row, dict):
            _group_count_field(per_type, row.get("type_id"), "items")
    for row in content["views"]:
        if isinstance(row, dict):
            _group_count_field(per_type, row.get("type_id"), "views")
    for group in per_type.values():
        if group.get("fields", 0) > MAX_FIELDS_PER_TYPE:
            raise _refusal()
        if group.get("items", 0) > MAX_ITEMS_PER_TYPE:
            raise _refusal()
        if group.get("views", 0) > MAX_VIEWS_PER_TYPE:
            raise _refusal()
    per_pair: dict[tuple[Any, Any], int] = {}
    for row in content["relations"]:
        if isinstance(row, dict):
            key = (row.get("source_item_id"), row.get("field_definition_id"))
            _group_count(per_pair, key)
    for count in per_pair.values():
        if count > MAX_RELATIONS_PER_PAIR:
            raise _refusal()


ScalarShapes = tuple[tuple[str, Callable[[Any], Any]], ...]


def _check_row_scalars(raw: Any, shapes: ScalarShapes) -> None:
    if not isinstance(raw, dict):
        raise _refusal()
    for key, check in shapes:
        check(raw.get(key))


_PAGE_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("slug", _text),
    ("title", _text),
    ("status", _text),
    ("locale", _text),
    ("parent_id", _optional_uuid),
    ("route_template", _optional_text),
    ("effective_route", _optional_text),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
    ("deleted_at", _optional_timestamp),
    ("style_overrides", _json_object),
)
_NODE_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("component_type", _text),
    ("schema_version", _text),
    ("parent_id", _optional_uuid),
    ("slot_key", _text),
    ("order_key", _int),
    ("props", _json_object),
)
_PAGE_STYLE_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("page_id", _uuid),
    ("schema_version", _text),
    ("row_version", _int),
    ("overrides", _json_object),
    ("resolved", _json_object),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_LOCALE_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("tag", _text),
    ("enabled", _bool),
    ("is_default", _bool),
    ("position", _int),
    ("metadata", _json_object),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_THEME_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("schema_version", _text),
    ("renderer_version", _text),
    ("row_version", _int),
    ("palette", _json_object),
    ("typography", _json_object),
    ("layout", _json_object),
    ("shape", _json_object),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_REGION_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("region_key", _text),
    ("variant", _text),
    ("content", _json_object),
    ("schema_version", _text),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_NAVIGATION_DEFINITION_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("key", _text),
    ("label", _text),
    ("settings", _json_object),
    ("labels", _json_object),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_NAVIGATION_ITEM_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("navigation_id", _uuid),
    ("parent_id", _optional_uuid),
    ("page_id", _optional_uuid),
    ("target_kind", _text),
    ("target_value", _text),
    ("labels", _json_object),
    ("locale", _optional_text),
    ("position", _int),
    ("row_version", _int),
    ("parent_key", _uuid),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_REDIRECT_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("source_route", _text),
    ("target", _text),
    ("status_code", _int),
    ("locale", _optional_text),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_COMPOSITION_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("page_id", _uuid),
    ("component_type", _text),
    ("schema_version", _text),
    ("parent_id", _optional_uuid),
    ("slot_key", _text),
    ("order_key", _int),
    ("props", _json_object),
    ("catalog_version", _text),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_CONTENT_TYPE_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("key", _text),
    ("labels", _json_object),
    ("slug_pattern", _text),
    ("status", _text),
    ("definition_version", _int),
    ("settings", _json_object),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_FIELD_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("type_id", _uuid),
    ("key", _text),
    ("label", _text),
    ("field_type", _text),
    ("required", _bool),
    ("localized", _bool),
    ("cardinality", _int),
    ("position", _int),
    ("validation", _json_object),
    ("ui_options", _json_object),
    ("definition_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_VIEW_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("type_id", _uuid),
    ("key", _text),
    ("filter_spec", _json_object),
    ("sort_spec", _json_object),
    ("projection_spec", _json_object),
    ("pagination_spec", _json_object),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
    ("definition_version", _int),
    ("row_version", _int),
)
_ITEM_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("type_id", _uuid),
    ("slug", _text),
    ("status", _text),
    ("type_definition_version", _int),
    ("values", _json_object),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_TRANSLATION_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("item_id", _uuid),
    ("locale", _text),
    ("localized_values", _json_object),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_RELATION_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("source_item_id", _uuid),
    ("field_definition_id", _uuid),
    ("target_item_id", _uuid),
    ("position", _int),
    ("metadata", _json_object),
    ("row_version", _int),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_PROPOSAL_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("workspace_id", _uuid),
    ("kind", _text),
    ("payload", _json_object),
    ("state", _text),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
)
_MEDIA_INVENTORY_SCALAR_SHAPES: Final = (
    ("id", _uuid),
    ("site_id", _uuid),
    ("uploaded_by", _optional_uuid),
    ("filename", _text),
    ("mime_type", _text),
    ("size_bytes", _int),
    ("content_hash", _text),
    ("storage_key", _text),
    ("alt_text", _text),
    ("metadata", _json_object),
    ("created_at", _timestamp),
    ("updated_at", _timestamp),
    ("public_status", _text),
    ("published_at", _optional_timestamp),
)


def _check_retained_scalar_shapes(payload: Mapping[str, Any]) -> None:
    """The required scalar/type shape of EVERY retained family row,
    faithful to the actual capture column types.

    Retention does not exempt shape: the lazy construction-time row
    constructors never see non-renderable rows (deleted page tombstones
    are skipped by the 049-ported resolution walk; relations, proposals
    and media inventory are never projected at all), so a malformed
    retained scalar (for example a list in a deleted page's text slug)
    must refuse at the seam instead of surviving past its identifier.
    The exact key sets are proven by the family validation that
    follows; here each row is checked field by field against the stored
    column shape (text vs text-or-null, int, bool, uuid, timestamp,
    jsonb object).
    """
    for raw in payload["pages"]:
        _check_row_scalars(raw, _PAGE_SCALAR_SHAPES)
        style = raw.get("style")
        if style is not None and isinstance(style, dict):
            _check_row_scalars(style, _PAGE_STYLE_SCALAR_SHAPES)
        nodes = raw.get("nodes")
        if not isinstance(nodes, list):
            raise _refusal()
        stack: list[Any] = list(nodes)
        while stack:
            node = stack.pop()
            if not isinstance(node, dict):
                raise _refusal()
            _check_row_scalars(node, _NODE_SCALAR_SHAPES)
            children = node.get("children")
            if children is not None:
                if not isinstance(children, list):
                    raise _refusal()
                stack.extend(children)
    for raw in payload["locales"]:
        _check_row_scalars(raw, _LOCALE_SCALAR_SHAPES)
    theme = payload["theme"]
    if theme is not None:
        _check_row_scalars(theme, _THEME_SCALAR_SHAPES)
    for raw in payload["regions"]:
        _check_row_scalars(raw, _REGION_SCALAR_SHAPES)
    for raw in payload["navigation"]["definitions"]:
        _check_row_scalars(raw, _NAVIGATION_DEFINITION_SCALAR_SHAPES)
    for raw in payload["navigation"]["items"]:
        _check_row_scalars(raw, _NAVIGATION_ITEM_SCALAR_SHAPES)
    for raw in payload["redirects"]:
        _check_row_scalars(raw, _REDIRECT_SCALAR_SHAPES)
    for raw in payload["page_compositions"]:
        _check_row_scalars(raw, _COMPOSITION_SCALAR_SHAPES)
    content = payload["content"]
    for raw in content["types"]:
        _check_row_scalars(raw, _CONTENT_TYPE_SCALAR_SHAPES)
    for raw in content["fields"]:
        _check_row_scalars(raw, _FIELD_SCALAR_SHAPES)
    for raw in content["items"]:
        _check_row_scalars(raw, _ITEM_SCALAR_SHAPES)
    for raw in content["translations"]:
        _check_row_scalars(raw, _TRANSLATION_SCALAR_SHAPES)
    for raw in content["relations"]:
        _check_row_scalars(raw, _RELATION_SCALAR_SHAPES)
    for raw in content["views"]:
        _check_row_scalars(raw, _VIEW_SCALAR_SHAPES)
    for raw in payload["proposals"]:
        _check_row_scalars(raw, _PROPOSAL_SCALAR_SHAPES)
    for raw in payload["media_inventory"]:
        _check_row_scalars(raw, _MEDIA_INVENTORY_SCALAR_SHAPES)


def _validate_family_bindings(
    payload: Mapping[str, Any],
    *,
    site_id: UUID,
    expected_workspace_id: UUID,
) -> None:
    """The exact shape/reference/uniqueness validation of EVERY retained
    family row, executed at the admission seam BEFORE any serialization
    or structure build, so the exported seam's result is fully verified.

    Retention does not exempt validation: deleted page tombstones and the
    never-projected families (relations, proposals, media inventory) carry
    the same site/reference bindings as the rendered rows.  Reference
    checks use the COMPLETE captured id sets, never a partially built one
    - the capture orders navigation items by (navigation_id, locale,
    position, parent_key, id), so a valid child can precede its parent.
    Hierarchy cycle/depth/duplicate/reachability semantics are NOT
    reimplemented here: they live in the shared projection helpers the
    live and frozen read paths both execute (common ownership).
    """
    # The required scalar/type shape of every retained row FIRST: the
    # lazy row constructors never see non-renderable rows, so malformed
    # retained scalars must refuse at the seam (see the helper).
    _check_retained_scalar_shapes(payload)
    page_ids: set[UUID] = set()
    for raw in payload["pages"]:
        if not isinstance(raw, dict) or set(raw) != _PAGE_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        page_id = _uuid(raw.get("id"))
        if page_id in page_ids:
            raise _refusal()
        page_ids.add(page_id)
    for raw in payload["pages"]:
        parent = _optional_uuid(raw.get("parent_id"))
        if parent is not None and parent not in page_ids:
            raise _refusal()
        style = raw.get("style")
        if style is not None:
            if not isinstance(style, dict) or set(style) != _PAGE_STYLE_KEYS:
                raise _refusal()
            if _uuid(style.get("site_id")) != site_id:
                raise _refusal()
            # The inner style row must belong to THIS page, not merely to
            # any captured page; absent styles stay legitimate.
            if _uuid(style.get("page_id")) != _uuid(raw.get("id")):
                raise _refusal()

    locale_ids: set[UUID] = set()
    for raw in payload["locales"]:
        if not isinstance(raw, dict) or set(raw) != _LOCALE_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        locale_id = _uuid(raw.get("id"))
        if locale_id in locale_ids:
            raise _refusal()
        locale_ids.add(locale_id)

    theme_raw = payload["theme"]
    if theme_raw is not None:
        if not isinstance(theme_raw, dict) or set(theme_raw) != _THEME_KEYS:
            raise _refusal()
        if _uuid(theme_raw.get("site_id")) != site_id:
            raise _refusal()

    region_ids: set[UUID] = set()
    for raw in payload["regions"]:
        if not isinstance(raw, dict) or set(raw) != _REGION_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        region_id = _uuid(raw.get("id"))
        if region_id in region_ids:
            raise _refusal()
        region_ids.add(region_id)

    navigation = payload["navigation"]
    nav_def_ids: set[UUID] = set()
    for raw in navigation["definitions"]:
        if not isinstance(raw, dict) or set(raw) != _NAVIGATION_DEFINITION_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        nav_id = _uuid(raw.get("id"))
        if nav_id in nav_def_ids:
            raise _refusal()
        nav_def_ids.add(nav_id)
    # Two passes over the COMPLETE id sets: pass one collects ids and the
    # same-navigation binding, pass two binds each parent against its own
    # navigation's complete item set (order-independent: capture order is
    # not topological, and children must neither be dropped nor require a
    # parent-first storage order).
    nav_item_ids: set[UUID] = set()
    nav_item_ids_by_nav: dict[UUID, set[UUID]] = {}
    for raw in navigation["items"]:
        if not isinstance(raw, dict) or set(raw) != _NAVIGATION_ITEM_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        item_id = _uuid(raw.get("id"))
        if item_id in nav_item_ids:
            raise _refusal()
        nav_id = _uuid(raw.get("navigation_id"))
        if nav_id not in nav_def_ids:
            raise _refusal()
        nav_item_ids.add(item_id)
        nav_item_ids_by_nav.setdefault(nav_id, set()).add(item_id)
    for raw in navigation["items"]:
        parent = _optional_uuid(raw.get("parent_id"))
        if parent is None:
            continue
        nav_id = _uuid(raw.get("navigation_id"))
        if parent not in nav_item_ids_by_nav[nav_id]:
            raise _refusal()

    redirect_ids: set[UUID] = set()
    redirect_keys: set[tuple[str, str | None]] = set()
    for raw in payload["redirects"]:
        if not isinstance(raw, dict) or set(raw) != _REDIRECT_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        redirect_id = _uuid(raw.get("id"))
        if redirect_id in redirect_ids:
            raise _refusal()
        key = (_text(raw.get("source_route")), _optional_text(raw.get("locale")))
        if key in redirect_keys:
            raise _refusal()
        redirect_ids.add(redirect_id)
        redirect_keys.add(key)

    composition_ids: set[UUID] = set()
    for raw in payload["page_compositions"]:
        if not isinstance(raw, dict) or set(raw) != _COMPOSITION_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        composition_id = _uuid(raw.get("id"))
        if composition_id in composition_ids:
            raise _refusal()
        composition_ids.add(composition_id)
        if _uuid(raw.get("page_id")) not in page_ids:
            raise _refusal()

    content = payload["content"]
    type_ids: set[UUID] = set()
    type_keys: set[str] = set()
    for raw in content["types"]:
        if not isinstance(raw, dict) or set(raw) != _CONTENT_TYPE_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        type_id = _uuid(raw.get("id"))
        if type_id in type_ids:
            raise _refusal()
        type_key = _text(raw.get("key"))
        if type_key in type_keys:
            raise _refusal()
        type_ids.add(type_id)
        type_keys.add(type_key)

    field_ids: set[UUID] = set()
    for raw in content["fields"]:
        if not isinstance(raw, dict) or set(raw) != _FIELD_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        field_id = _uuid(raw.get("id"))
        if field_id in field_ids:
            raise _refusal()
        field_ids.add(field_id)
        if _uuid(raw.get("type_id")) not in type_ids:
            raise _refusal()

    item_ids: set[UUID] = set()
    for raw in content["items"]:
        if not isinstance(raw, dict) or set(raw) != _ITEM_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        item_id = _uuid(raw.get("id"))
        if item_id in item_ids:
            raise _refusal()
        item_ids.add(item_id)
        if _uuid(raw.get("type_id")) not in type_ids:
            raise _refusal()

    translation_ids: set[UUID] = set()
    translation_keys: set[tuple[UUID, str]] = set()
    for raw in content["translations"]:
        if not isinstance(raw, dict) or set(raw) != _TRANSLATION_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        translation_id = _uuid(raw.get("id"))
        if translation_id in translation_ids:
            raise _refusal()
        item_id = _uuid(raw.get("item_id"))
        if item_id not in item_ids:
            raise _refusal()
        tkey = (item_id, _text(raw.get("locale")))
        if tkey in translation_keys:
            raise _refusal()
        translation_ids.add(translation_id)
        translation_keys.add(tkey)

    relation_ids: set[UUID] = set()
    for raw in content["relations"]:
        if not isinstance(raw, dict) or set(raw) != _RELATION_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        relation_id = _uuid(raw.get("id"))
        if relation_id in relation_ids:
            raise _refusal()
        relation_ids.add(relation_id)
        if _uuid(raw.get("source_item_id")) not in item_ids:
            raise _refusal()
        if _uuid(raw.get("target_item_id")) not in item_ids:
            raise _refusal()
        if _uuid(raw.get("field_definition_id")) not in field_ids:
            raise _refusal()

    view_ids: set[UUID] = set()
    for raw in content["views"]:
        if not isinstance(raw, dict) or set(raw) != _VIEW_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        view_id = _uuid(raw.get("id"))
        if view_id in view_ids:
            raise _refusal()
        view_ids.add(view_id)
        if _uuid(raw.get("type_id")) not in type_ids:
            raise _refusal()

    proposal_ids: set[UUID] = set()
    for raw in payload["proposals"]:
        if not isinstance(raw, dict) or set(raw) != _PROPOSAL_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        if _uuid(raw.get("workspace_id")) != expected_workspace_id:
            raise _refusal()
        proposal_id = _uuid(raw.get("id"))
        if proposal_id in proposal_ids:
            raise _refusal()
        proposal_ids.add(proposal_id)

    inventory_ids: set[UUID] = set()
    for raw in payload["media_inventory"]:
        if not isinstance(raw, dict) or set(raw) != _MEDIA_INVENTORY_KEYS:
            raise _refusal()
        if _uuid(raw.get("site_id")) != site_id:
            raise _refusal()
        inventory_id = _uuid(raw.get("id"))
        if inventory_id in inventory_ids:
            raise _refusal()
        inventory_ids.add(inventory_id)


def admit_frozen_snapshot(
    row: Any,
    *,
    expected_snapshot_id: UUID,
    expected_site_id: UUID,
    expected_workspace_id: UUID,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The shared verified admission seam (R7) for one frozen row.

    Accepts only a COMPLETE ``control.review_snapshot`` row that (1)
    carries the exact 14-column shape, (2) binds to the expected
    snapshot/site/workspace identities, (3) holds the trusted six-pin
    set at the row level, (4) holds the exact 18-key v2 payload with
    the supported state version, the trusted six pins at the payload
    level, the pinned catalog version and the expected workspace/site,
    (5) has a normalized_state canonically identical to the payload,
    (6) carries a digest that exactly recomputes (SHA-256 of the
    canonical payload text; any mismatch, unsupported value type or
    over-budget canonical size refuses), (7) carries the sibling
    bindings the capture emitter produces (validation report with
    zero errors and the exact page count, media references matching
    the media map field-for-field, browser evidence, created_by and
    created_at, site profile with a supported captured status),
    (8) satisfies the COMPLETE exact shape/reference/uniqueness
    validation of every retained family row (deleted page tombstones
    and the never-projected families included; the required
    scalar/type shape of every retained field; navigation parents
    against the complete same-navigation id set; the style row's
    page id equal to its page), and
    (9) satisfies the bounded-work gates in order BEFORE any
    serialization, allocation or family index: the exact 076
    raw-value depth gate (<= 8), the valid component-tree depth gate
    (<= 17 node chain, <= 128 nodes per page), the exact 076 capture
    row caps, and the derived whole-document depth bound (<= 45) -
    each on the payload AND its normalized counterpart.

    Returns the verified ``(payload, site_profile)``: the complete
    verified admission result the adapters accept.  Every
    malformation is the stable ``not_found`` refusal; no caller may
    treat a partial result as verified because this seam performs the
    full validation.
    """
    if not isinstance(row, Mapping) or set(row) != _FROZEN_ROW_KEYS:
        raise _refusal()
    if row.get("status") != "COMPLETE":
        raise _refusal()
    if _uuid(row.get("id")) != expected_snapshot_id:
        raise _refusal()
    if _uuid(row.get("workspace_id")) != expected_workspace_id:
        raise _refusal()
    if _uuid(row.get("site_id")) != expected_site_id:
        raise _refusal()
    if row.get("versions") != dict(TRUSTED_WORKSPACE_VERSIONS):
        raise _refusal()

    payload = row.get("payload")
    if not isinstance(payload, dict) or set(payload) != set(_FAMILIES):
        raise _refusal()
    if payload.get("state_version") != SUPPORTED_STATE_VERSION:
        raise _refusal()
    if payload.get("workspace_versions") != dict(TRUSTED_WORKSPACE_VERSIONS):
        raise _refusal()
    if _uuid(payload.get("workspace_id")) != expected_workspace_id:
        raise _refusal()
    if _uuid(payload.get("site_id")) != expected_site_id:
        raise _refusal()
    for family in _FAMILY_LISTS:
        if not isinstance(payload.get(family), list):
            raise _refusal()
    navigation = payload.get("navigation")
    if (
        not isinstance(navigation, dict)
        or set(navigation)
        != {
            "definitions",
            "items",
        }
        or not isinstance(navigation["definitions"], list)
        or not isinstance(navigation["items"], list)
    ):
        raise _refusal()
    content = payload.get("content")
    if not isinstance(content, dict) or not all(
        isinstance(content.get(family), list) for family in _CONTENT_FAMILIES
    ):
        raise _refusal()
    base_site_revision = payload.get("base_site_revision")
    operation_watermark = payload.get("operation_watermark")
    if not _is_int(base_site_revision) or base_site_revision < 0:
        raise _refusal()
    if not _is_int(operation_watermark) or operation_watermark < 0:
        raise _refusal()
    revision_watermark = row.get("revision_watermark")
    if not _is_int(revision_watermark) or revision_watermark != (
        base_site_revision + operation_watermark
    ):
        raise _refusal()

    # The normalized counterpart must carry the same family structure
    # before ANY bounded gate or serialization touches it.
    normalized_state = row.get("normalized_state")
    if not isinstance(normalized_state, dict):
        raise _refusal()
    for family in _FAMILY_LISTS:
        if not isinstance(normalized_state.get(family), list):
            raise _refusal()
    normalized_navigation = normalized_state.get("navigation")
    if (
        not isinstance(normalized_navigation, dict)
        or not isinstance(normalized_navigation.get("definitions"), list)
        or not isinstance(normalized_navigation.get("items"), list)
    ):
        raise _refusal()
    normalized_content = normalized_state.get("content")
    if not isinstance(normalized_content, dict) or not all(
        isinstance(normalized_content.get(family), list) for family in _CONTENT_FAMILIES
    ):
        raise _refusal()
    if not isinstance(normalized_state.get("media"), dict):
        raise _refusal()

    # Sibling bindings the capture emitter produces (cheap shape checks,
    # before any serialization or allocation).
    report = row.get("validation_report")
    if not isinstance(report, Mapping) or set(report) != _VALIDATION_REPORT_KEYS:
        raise _refusal()
    if report.get("state_version") != SUPPORTED_STATE_VERSION:
        raise _refusal()
    pages_validated = report.get("pages_validated")
    if (
        not _is_int(pages_validated)
        or pages_validated < 0
        or pages_validated != len(payload["pages"])
    ):
        raise _refusal()
    errors = report.get("errors")
    if not isinstance(errors, list) or errors:
        raise _refusal()
    cancelled = report.get("cancelled_by_freeze")
    if not isinstance(cancelled, list):
        raise _refusal()
    for item in cancelled:
        if (
            not isinstance(item, Mapping)
            or set(item) != {"id", "previous_state"}
            or not isinstance(item.get("id"), str)
            or (
                item.get("previous_state") is not None
                and not isinstance(item.get("previous_state"), str)
            )
        ):
            raise _refusal()

    media_map = payload["media"]
    if not isinstance(media_map, dict):
        raise _refusal()
    media_ids: set[UUID] = set()
    for key, descriptor in media_map.items():
        if not isinstance(key, str):
            raise _refusal()
        try:
            media_id = UUID(key)
        except ValueError:
            raise _refusal() from None
        media_ids.add(media_id)
        if not isinstance(descriptor, Mapping) or set(descriptor) != _MEDIA_ENTRY_KEYS:
            raise _refusal()
        if _uuid(descriptor.get("id")) != media_id:
            raise _refusal()
        if (
            not isinstance(descriptor.get("mime_type"), str)
            or not isinstance(descriptor.get("content_hash"), str)
            or not isinstance(descriptor.get("public_status"), str)
        ):
            raise _refusal()
        size = descriptor.get("size_bytes")
        if not _is_int(size) or size < 0:
            raise _refusal()
    references = row.get("media_references")
    if not isinstance(references, list) or len(references) != len(media_map):
        raise _refusal()
    seen: set[UUID] = set()
    for entry in references:
        if not isinstance(entry, Mapping) or set(entry) != _MEDIA_REFERENCE_KEYS:
            raise _refusal()
        try:
            entry_id = UUID(_text(entry.get("id")))
        except SurfaceReadError:
            raise
        except ValueError:
            raise _refusal() from None
        if entry_id in seen or entry_id not in media_ids:
            raise _refusal()
        seen.add(entry_id)
        descriptor = media_map[_text(entry.get("id"))]
        if (
            entry.get("mime_type") != descriptor["mime_type"]
            or entry.get("size_bytes") != descriptor["size_bytes"]
            or entry.get("content_hash") != descriptor["content_hash"]
            or entry.get("public_status") != descriptor["public_status"]
        ):
            raise _refusal()

    evidence = row.get("browser_evidence")
    if not isinstance(evidence, list):
        raise _refusal()
    for item in evidence:
        if (
            not isinstance(item, Mapping)
            or set(item) != {"id"}
            or not isinstance(item.get("id"), str)
        ):
            raise _refusal()

    if not isinstance(row.get("created_by"), str) or not row["created_by"]:
        raise _refusal()
    _timestamp(row.get("created_at"))

    site_profile = payload["site"]
    if not isinstance(site_profile, dict) or set(site_profile) != _SITE_PROFILE_KEYS:
        raise _refusal()
    _nonempty_text(site_profile.get("site_key"))
    _nonempty_text(site_profile.get("display_name"))
    if site_profile.get("status") not in _SUPPORTED_SITE_STATUSES:
        raise _refusal()
    _nonempty_text(site_profile.get("default_locale"))
    if site_profile.get("component_catalog_version") != COMPONENT_CATALOG_VERSION:
        raise _refusal()
    content_model_revision = site_profile.get("content_model_revision")
    if not _is_int(content_model_revision) or content_model_revision < 0:
        raise _refusal()
    _timestamp(site_profile.get("created_at"))
    _timestamp(site_profile.get("updated_at"))

    # Bounded-work ordering (R8), on BOTH the payload and its normalized
    # counterpart, in this exact order:
    #   1. the exact 076 capture row caps - O(1) family lengths plus the
    #      bounded per-group counts, the cheapest complete checks, run
    #      FIRST (before any index, walk or allocation),
    #   2. the finite depth/width walkers: the exact 076 preflight
    #      raw-value depth gate (<= 8 on the exact captured fields), the
    #      valid component-tree depth gate (<= 17 node chain, <= 128
    #      nodes per page), and the derived whole-document container
    #      depth bound (<= 45) - each walker enforces an explicit finite
    #      element-width bound before it grows its stack,
    # which make the bounded serializer's recursion and every allocation
    # impossible to exceed the budget.  The two depth semantics stay
    # separate: raw-value depth gates the opaque JSON fields, the chain
    # gate gates the normalized node tree.
    for document in (payload, normalized_state):
        _check_family_caps(document)
    for document in (payload, normalized_state):
        _check_payload_raw_depth(document)
        _check_page_node_chains(document)
        if not _raw_depth_ok(document, MAX_WHOLE_DOCUMENT_RAW_DEPTH):
            raise _refusal()

    # COMPLETE family validation (exact shape/reference/uniqueness of
    # every retained row, deleted tombstones included) runs after the
    # cheap caps/walkers: it is the step that builds the complete family
    # id indexes the reference checks need, never before them.
    _validate_family_bindings(
        payload,
        site_id=expected_site_id,
        expected_workspace_id=expected_workspace_id,
    )

    # Payload / normalized-state integrity and the recomputed digest.
    # canonical_json_bounded is byte-identical to canonical_json within
    # the budget, raises CanonicalBudgetExceeded the moment the capture
    # canonical payload budget (8 MiB) would be exceeded, and raises
    # TypeError/ValueError on value types jsonb cannot carry (the
    # retained document must round-trip the trusted store); the digest
    # must be the exact SHA-256 of the canonical payload text.
    digest = row.get("digest")
    if not isinstance(digest, str) or _DIGEST_SHAPE.fullmatch(digest) is None:
        raise _refusal()
    try:
        payload_text = canonical_json_bounded(payload, MAX_CANONICAL_PAYLOAD_BYTES)
        normalized_text = canonical_json_bounded(
            normalized_state, MAX_CANONICAL_PAYLOAD_BYTES
        )
    except (CanonicalBudgetExceeded, TypeError, ValueError):
        raise _refusal() from None
    if normalized_text != payload_text:
        raise _refusal()
    if hashlib.sha256(payload_text.encode("utf-8")).hexdigest() != digest:
        raise _refusal()
    return payload, site_profile


def _locale_row(site_id: UUID, raw: Mapping[str, Any]) -> LocaleRow:
    _require_keys(raw, _LOCALE_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _text(raw["tag"]),
        _bool(raw["enabled"]),
        _bool(raw["is_default"]),
        _int(raw["position"]),
        _render_value(raw["metadata"]),
    )


def _page_fact(site_id: UUID, raw: Mapping[str, Any]) -> RenderPageFact:
    _require_keys(raw, _PAGE_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return RenderPageFact(
        id=_uuid(raw["id"]),
        site_id=site_id,
        slug=_text(raw["slug"]),
        title=_text(raw["title"]),
        status=_text(raw["status"]),
        locale=_text(raw["locale"]),
        parent_id=_optional_uuid(raw["parent_id"]),
        route_template=_optional_text(raw["route_template"]),
        row_version=_int(raw["row_version"]),
    )


def _theme_row(site_id: UUID, raw: Mapping[str, Any]) -> ThemeRow:
    _require_keys(raw, _THEME_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _text(raw["schema_version"]),
        _text(raw["renderer_version"]),
        _int(raw["row_version"]),
        _render_value(raw["palette"]),
        _render_value(raw["typography"]),
        _render_value(raw["layout"]),
        _render_value(raw["shape"]),
        _timestamp(raw["created_at"]),
        _timestamp(raw["updated_at"]),
    )


def _page_style_row(
    site_id: UUID, outer_page_id: UUID, raw: Mapping[str, Any]
) -> PageStyleRow:
    _require_keys(raw, _PAGE_STYLE_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    # The retained style row is page31's style only on page31: the inner
    # page id must equal the outer page row's id (same-site membership
    # alone is insufficient).
    page_id = _uuid(raw["page_id"])
    if page_id != outer_page_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        page_id,
        site_id,
        _text(raw["schema_version"]),
        _int(raw["row_version"]),
        _render_value(raw["overrides"]),
        _render_value(raw["resolved"]),
        _timestamp(raw["created_at"]),
        _timestamp(raw["updated_at"]),
    )


def _region_row(site_id: UUID, raw: Mapping[str, Any]) -> RegionRow:
    _require_keys(raw, _REGION_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _text(raw["region_key"]),
        _text(raw["variant"]),
        _render_value(raw["content"]),
        _text(raw["schema_version"]),
        _int(raw["row_version"]),
        _timestamp(raw["created_at"]),
        _timestamp(raw["updated_at"]),
    )


def _navigation_definition_row(
    site_id: UUID, raw: Mapping[str, Any]
) -> NavigationDefinitionRow:
    _require_keys(raw, _NAVIGATION_DEFINITION_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _text(raw["key"]),
        raw["label"],
        _render_value(raw["labels"]),
        _render_value(raw["settings"]),
    )


def _navigation_item_raw_row(
    site_id: UUID, raw: Mapping[str, Any]
) -> NavigationItemRawRow:
    _require_keys(raw, _NAVIGATION_ITEM_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _uuid(raw["navigation_id"]),
        _optional_uuid(raw["parent_id"]),
        _optional_uuid(raw["page_id"]),
        _text(raw["target_kind"]),
        _text(raw["target_value"]),
        _render_value(raw["labels"]),
        _optional_text(raw["locale"]),
        _int(raw["position"]),
    )


def _redirect_row(site_id: UUID, raw: Mapping[str, Any]) -> RedirectRow:
    _require_keys(raw, _REDIRECT_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _text(raw["source_route"]),
        _text(raw["target"]),
        _int(raw["status_code"]),
        _optional_text(raw["locale"]),
    )


def _composition_row(site_id: UUID, raw: Mapping[str, Any]) -> CompositionRow:
    _require_keys(raw, _COMPOSITION_KEYS)
    if _uuid(raw["site_id"]) != site_id:
        raise _refusal()
    return (
        _uuid(raw["id"]),
        site_id,
        _uuid(raw["page_id"]),
        _text(raw["component_type"]),
        _text(raw["schema_version"]),
        _optional_uuid(raw["parent_id"]),
        _text(raw["slot_key"]),
        _int(raw["order_key"]),
        _render_value(raw["props"]),
        _timestamp(raw["created_at"]),
        _timestamp(raw["updated_at"]),
    )


def _media_entry(key: str, raw: Mapping[str, Any]) -> MediaRow:
    _require_keys(raw, _MEDIA_ENTRY_KEYS)
    try:
        entry_id = UUID(key)
    except ValueError:
        raise _refusal() from None
    if _uuid(raw["id"]) != entry_id:
        raise _refusal()
    return (
        _text(raw["mime_type"]),
        _int(raw["size_bytes"]),
        _text(raw["content_hash"]),
        _text(raw["public_status"]),
    )


def _collection_view_row(raw: Mapping[str, Any]) -> CollectionViewRow:
    _require_keys(raw, _VIEW_KEYS)
    return (
        _uuid(raw["id"]),
        _uuid(raw["site_id"]),
        _uuid(raw["type_id"]),
        _text(raw["key"]),
        _render_value(raw["filter_spec"]),
        _render_value(raw["sort_spec"]),
        _render_value(raw["projection_spec"]),
        _render_value(raw["pagination_spec"]),
        raw["definition_version"],
    )


def _content_type_row(raw: Mapping[str, Any]) -> ContentTypeRow:
    _require_keys(raw, _CONTENT_TYPE_KEYS)
    return (_uuid(raw["site_id"]), _text(raw["status"]), raw["definition_version"])


def _field_row(raw: Mapping[str, Any]) -> FieldDefinitionRow:
    _require_keys(raw, _FIELD_KEYS)
    return (
        _text(raw["key"]),
        _text(raw["field_type"]),
        _bool(raw["localized"]),
        _render_value(raw["validation"]),
        raw["cardinality"],
        _bool(raw["required"]),
    )


def _item_row(raw: Mapping[str, Any]) -> ContentItemRow:
    _require_keys(raw, _ITEM_KEYS)
    return (
        _uuid(raw["id"]),
        _uuid(raw["site_id"]),
        _uuid(raw["type_id"]),
        _text(raw["slug"]),
        _text(raw["status"]),
        _render_value(raw["values"]),
        raw["type_definition_version"],
    )


def _translation_row(raw: Mapping[str, Any]) -> ContentItemTranslationRow:
    _require_keys(raw, _TRANSLATION_KEYS)
    return (
        _uuid(raw["item_id"]),
        _text(raw["locale"]),
        _render_value(raw["localized_values"]),
    )


# ---------------------------------------------------------------------------
# Shared route/navigation/ancestor semantics - the one faithful port of
# the effective content SQL that BOTH read paths execute (R3): the live
# path over ``DatabaseRenderSurface`` rows, the frozen path over
# ``FrozenRenderSurface`` rows.  No second selection engine, no frozen
# shadow resolver, no live SQL winner.
#
# Sources (verbatim effective bodies, /tmp/oap-083-5-a/effective-sql-dump
# .txt): 050 ``slaif_agent_page_effective_route`` (the effective route
# replacement; 049 is the initial create), 056
# ``slaif_render_page_resolve`` (winner selection), 057
# ``slaif_navigation_page_target_validate`` (PAGE target validator),
# 059 ``slaif_render_navigation_items`` +
# ``slaif_render_internal_target_exists`` (the locale-neutral final
# upgrade; 052 is the initial navigation create) and 067
# ``slaif_page_ancestor_chain``.  049/052 remain immutable history.
#
# Faithfulness notes:
# * 056's comment "Exact static routes always win over a dynamic page"
#   does NOT describe effective behavior: once a static match is
#   recorded, a matching dynamic page raises RENDER_ROUTE_AMBIGUOUS,
#   and two matching static (or two matching dynamic) candidates do
#   too.  This port preserves that fail-closed ambiguity and never
#   adopts a static-wins policy.
# * 050 errors are swallowed per candidate inside 056 (CONTINUE) and
#   propagate verbatim from 067's per-row calls.  Inside 059's PAGE
#   branch EVERY failure - the page lookup miss, 057's validator
#   errors and the effective-route failure - is caught (WHEN OTHERS)
#   and re-raised uniformly as RENDER_NAVIGATION_PAGE_INVALID; the
#   port applies that uniform code to the whole PAGE branch.
# * 059's INTERNAL check passes the ITEM's own (possibly NULL) locale
#   into ``slaif_render_internal_target_exists``, but the effective
#   function's page predicate references only the PAGE's own locale
#   (``l.tag = p.locale``) and its ``p_locale`` parameter is unused:
#   the lookup is deliberately locale-neutral, and a NULL item locale
#   behaves exactly like any other.  The port keeps the (unused)
#   parameter for signature fidelity and preserves the neutral lookup.
# * 067's recursive chain has no visited-set guard beyond the depth
#   bound, so a parent cycle yields a depth-64 chain of repeated rows;
#   the port walks the identical bound.
# ---------------------------------------------------------------------------

_ROUTE_SHAPE_RE: Final[re.Pattern[str]] = re.compile(r"^/[a-z0-9._~/-]*$")
_BAD_ROUTE_RE: Final[re.Pattern[str]] = re.compile(r"//|\\|%|\.\.")
_DYNAMIC_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9][a-z0-9._~-]{0,254}$")
_NAV_HREF_RE: Final[re.Pattern[str]] = re.compile(r"^/[A-Za-z0-9._~/-]*$")
_INTERNAL_ROUTE_SHAPE_RE: Final[re.Pattern[str]] = re.compile(
    r"^/[A-Za-z0-9][A-Za-z0-9._~/-]*$"
)
_INTERNAL_RESERVED_RE: Final[re.Pattern[str]] = re.compile(
    r"^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)"
)


class _RouteMemo:
    """One render request's memo of shared 050/059 derivations.

    R8 total-work bound: without it, ``navigation_resolved_items``
    re-derives every retained page's route for every INTERNAL item
    (P pages x N items derivations - 16,777,216 at the 4096/4096
    caps), and the INTERNAL target check would re-scan the whole page
    set once per item even when the derivations were cached.  The
    memo makes each page derive at most ONCE per request AND
    builds the INTERNAL target existence counts (route -> number of
    eligible static pages) at most once per (site, statuses) pair,
    so an INTERNAL item answers in O(1).  Both are exact:
    ``page_effective_route`` is a pure function of (facts, page_id,
    default_locale, enabled_tags) - caching its result, or its exact
    stable reason for failures re-raised as a fresh exception so no
    cached traceback state can grow, changes no outcome - and the
    target counts are
    the same per-page predicates the effective SQL loops per item
    (site + status-eligible + static + derivable route), so
    ``count(target) == 1`` reproduces its ``found``/duplicate
    decision exactly.  One instance per request (the service wiring
    creates it once and shares it through every port call); there is
    no global or cross-request state.
    """

    __slots__ = (
        "default_locale",
        "derived",
        "enabled_tags",
        "facts",
        "failed",
        "static_indexes",
        "target_counts",
    )

    def __init__(
        self,
        facts: Mapping[UUID, RenderPageFact],
        *,
        default_locale: str,
        enabled_tags: frozenset[str],
    ) -> None:
        self.facts = facts
        self.default_locale = default_locale
        self.enabled_tags = enabled_tags
        self.derived: dict[UUID, str] = {}
        self.failed: dict[UUID, str] = {}
        self.static_indexes: dict[
            tuple[UUID, str, frozenset[str]], dict[str, tuple[int, RenderPageFact]]
        ] = {}
        self.target_counts: dict[tuple[UUID, frozenset[str]], dict[str, int]] = {}

    def route(self, page_id: UUID) -> str:
        reason = self.failed.get(page_id)
        if reason is not None:
            # A FRESH exception every time: caching the instance and
            # re-raising it would let its __traceback__ grow on every
            # use (observed 5/7/11/19/35/51 frames after 1/2/4/8/16/24
            # uses).  Only the stable reason string is cached.
            raise SurfaceReadError(reason)
        cached = self.derived.get(page_id)
        if cached is None:
            try:
                cached = page_effective_route(
                    self.facts,
                    page_id=page_id,
                    default_locale=self.default_locale,
                    enabled_tags=self.enabled_tags,
                )
            except SurfaceReadError as exc:
                self.failed[page_id] = exc.reason
                raise
            self.derived[page_id] = cached
        return cached

    def static_route_index(
        self, site_id: UUID, locale: str, status_set: frozenset[str]
    ) -> dict[str, tuple[int, RenderPageFact]]:
        """056 static-phase candidates, derived once per (site, locale, statuses).

        The exact static-loop predicates (same site, exact locale,
        status-eligible, non-dynamic ``route_template``, derivable
        effective route - a derivation failure is skipped exactly as
        the SQL CONTINUE) applied in ONE pass, mapping lowercased
        effective route to (count, candidate).  The winner outcome
        depends only on count/identity: the SQL's second-match
        AMBIGUOUS fires iff count >= 2, independent of table order,
        and a count-1 match IS the unique candidate.  Repeated route
        resolutions in one request therefore stop rescanning the
        whole page set for the static phase.
        """
        key = (site_id, locale, status_set)
        cached = self.static_indexes.get(key)
        if cached is None:
            index: dict[str, tuple[int, RenderPageFact]] = {}
            for fact in self.facts.values():
                if (
                    fact.site_id != site_id
                    or fact.locale != locale
                    or fact.status not in status_set
                    or fact.route_template == "{slug}"
                ):
                    continue
                try:
                    route = self.route(fact.id)
                except SurfaceReadError:
                    continue
                count, candidate = index.get(route.lower(), (0, fact))
                index[route.lower()] = (count + 1, candidate)
            cached = index
            self.static_indexes[key] = cached
        return cached

    def internal_target_counts(
        self, site_id: UUID, status_set: frozenset[str]
    ) -> dict[str, int]:
        """059 INTERNAL target existence counts, built at most once.

        One pass over the retained facts with the EXACT page
        predicates of ``slaif_render_internal_target_exists`` (same
        site, status-eligible, static ``route_template IS NULL``,
        enabled page locale via the memo, derivable effective route -
        unroutable pages skipped, as the SQL's CONTINUE); the result
        maps each effective route to its eligible-page count, so a
        target exists iff its count is exactly 1 (the SQL's
        duplicate-fails-closed rule).
        """
        key = (site_id, status_set)
        cached = self.target_counts.get(key)
        if cached is None:
            counts: dict[str, int] = {}
            for fact in self.facts.values():
                if (
                    fact.site_id != site_id
                    or fact.status not in status_set
                    or fact.route_template is not None
                ):
                    continue
                try:
                    route = self.route(fact.id)
                except SurfaceReadError:
                    continue
                counts[route] = counts.get(route, 0) + 1
            cached = counts
            self.target_counts[key] = cached
        return cached


def _route_memo(
    facts: Mapping[UUID, RenderPageFact],
    default_locale: str,
    enabled_tags: frozenset[str],
    shared: _RouteMemo | None,
) -> _RouteMemo:
    """Bind ``shared`` to this request context or start a fresh memo.

    A passed memo must be bound to the SAME facts object and site
    locale facts; reusing one across contexts would silently serve
    stale routes, so a mismatch is a programming error (ValueError),
    never a stable read reason.
    """
    if shared is None:
        return _RouteMemo(
            facts, default_locale=default_locale, enabled_tags=enabled_tags
        )
    if (
        shared.facts is not facts
        or shared.default_locale != default_locale
        or shared.enabled_tags != enabled_tags
    ):
        raise ValueError("shared route memo is bound to a different request")
    return shared


def new_route_memo(
    facts: Mapping[UUID, RenderPageFact],
    *,
    default_locale: str,
    enabled_tags: frozenset[str],
) -> _RouteMemo:
    """Create the per-request shared route memo (the R8 total-work seam).

    One render request builds exactly one memo over its complete page
    facts and site locale facts and shares it through every port call
    (route resolution, navigation, regions, ancestors).
    """
    return _RouteMemo(facts, default_locale=default_locale, enabled_tags=enabled_tags)


def page_effective_route(
    facts: Mapping[UUID, RenderPageFact],
    *,
    page_id: UUID,
    default_locale: str,
    enabled_tags: frozenset[str],
) -> str:
    """050 port: the effective route of one retained non-deleted page.

    ``facts`` indexes every non-deleted page row of the site (the exact
    input set both surfaces fetch); a deleted or unknown page raises
    PAGE_NOT_FOUND exactly as the live function's ``deleted_at IS NULL``
    lookup does.  ``default_locale``/``enabled_tags`` are the caller's
    already-validated site locale facts (the SQL reads them from
    ``content.site_locale`` inside the function).  Raises
    :class:`SurfaceReadError` with the exact SQL message:
    PAGE_NOT_FOUND / LOCALE_INVALID / PAGE_HIERARCHY_CYCLE /
    PAGE_PARENT_INVALID / PAGE_DYNAMIC_PARENT.
    """
    page = facts.get(page_id)
    if page is None:
        raise SurfaceReadError("PAGE_NOT_FOUND")
    if page.locale not in enabled_tags:
        raise SurfaceReadError("LOCALE_INVALID")
    segments: list[str] = []
    current = page
    depth = 0
    while True:
        depth += 1
        if depth > 64:
            raise SurfaceReadError("PAGE_HIERARCHY_CYCLE")
        # SQL: coalesce(nullif(route_template, ''), slug)
        template = current.route_template
        if template is None or template == "":
            segment: str = current.slug
        else:
            segment = template
        segments.append(segment)
        if current.parent_id is None:
            break
        parent = facts.get(current.parent_id)
        if (
            parent is None
            or parent.site_id != page.site_id
            or parent.locale != page.locale
        ):
            raise SurfaceReadError("PAGE_PARENT_INVALID")
        if parent.route_template == "{slug}":
            raise SurfaceReadError("PAGE_DYNAMIC_PARENT")
        current = parent
    route = ""
    if page.locale != default_locale:
        route = f"/{page.locale}"
    for index in range(len(segments) - 1, -1, -1):
        if index == len(segments) - 1 and segments[index] == "home":
            continue
        route = f"{route}/{segments[index]}"
    return route if route else "/"


def resolve_page_route(
    facts: Mapping[UUID, RenderPageFact],
    *,
    site_id: UUID,
    route: str,
    locale: str,
    statuses: Sequence[str],
    default_locale: str,
    enabled_tags: frozenset[str],
    route_memo: _RouteMemo | None = None,
) -> RenderPageFact | None:
    """056 port: exact route winner selection over retained facts.

    Returns the unique matching page fact, or ``None`` for the SQL's
    zero-row results (no match, or an input shape the function rejects
    up front).  Raises :class:`SurfaceReadError` with
    RENDER_ROUTE_AMBIGUOUS - a second static match, a static/dynamic
    overlap, or two matching dynamic pages - or RENDER_ROUTE_INVALID -
    a dynamic candidate whose effective route is not
    ``<prefix>/{slug}`` - exactly as the live function (see the
    fail-closed ambiguity note above; the two candidate phases run in
    the SQL order, static first).  ``route_memo`` is the shared
    per-request derivation (R8 bound); a fresh memo is started when
    omitted.  The static phase reads the memo's once-built static
    route index (same outcome, no per-call rescan); the dynamic
    phase keeps the SQL's per-candidate checks over memoized
    derivations.
    """
    memo = _route_memo(facts, default_locale, enabled_tags, route_memo)
    if (
        not isinstance(route, str)
        or not _ROUTE_SHAPE_RE.fullmatch(route)
        or _BAD_ROUTE_RE.search(route)
        or not statuses
        or any(status not in ("PUBLISHED", "DRAFT") for status in statuses)
    ):
        return None
    status_set = frozenset(statuses)
    found: RenderPageFact | None = None
    # Static phase over the shared index: the SQL's static loop
    # outcome (none / unique / AMBIGUOUS on the second match) is
    # reproduced exactly by (count, candidate) per lowercased route.
    entry = memo.static_route_index(site_id, locale, status_set).get(route.lower())
    if entry is not None:
        count, found = entry
        if count >= 2:
            raise SurfaceReadError("RENDER_ROUTE_AMBIGUOUS")
    for fact in facts.values():
        if (
            fact.site_id != site_id
            or fact.locale != locale
            or fact.status not in status_set
            or fact.route_template != "{slug}"
        ):
            continue
        try:
            candidate_route = memo.route(fact.id)
        except SurfaceReadError:
            continue
        if candidate_route[-6:] != "{slug}":
            raise SurfaceReadError("RENDER_ROUTE_INVALID")
        prefix = candidate_route[:-6]
        if not prefix.endswith("/"):
            raise SurfaceReadError("RENDER_ROUTE_INVALID")
        if not route.lower().startswith(prefix.lower()):
            continue
        slug = route[len(prefix) :]
        if not _DYNAMIC_SLUG_RE.fullmatch(slug) or "/" in slug:
            continue
        if found is not None:
            raise SurfaceReadError("RENDER_ROUTE_AMBIGUOUS")
        found = fact
    return found


def _internal_target_exists(
    facts: Mapping[UUID, RenderPageFact],
    *,
    site_id: UUID,
    target_value: str | None,
    locale: str | None,
    default_locale: str,
    enabled_tags: frozenset[str],
    statuses: Sequence[str],
    route_memo: _RouteMemo | None = None,
) -> bool:
    """``slaif_render_internal_target_exists`` port (059 INTERNAL gate).

    Exact (case-sensitive) effective-route equality against one and
    only one non-dynamic, enabled-locale, status-eligible page; a
    duplicate route fails closed to False, as does the reserved
    service-prefix list.  ``locale`` is the ITEM's own locale (059
    passes ``item.locale``, which may be NULL) but is intentionally
    UNUSED: the effective page predicate references only the page's
    own locale (``l.tag = p.locale``), so the lookup is neutral and a
    NULL item locale behaves like any other.  ``route_memo`` is the
    shared per-request derivation (R8 bound); a fresh memo is started
    when omitted.
    """
    status_set = frozenset(statuses)
    memo = _route_memo(facts, default_locale, enabled_tags, route_memo)
    if (
        target_value is None
        or not status_set
        or not (target_value == "/" or _INTERNAL_ROUTE_SHAPE_RE.fullmatch(target_value))
        or _BAD_ROUTE_RE.search(target_value)
        or _INTERNAL_RESERVED_RE.search(target_value)
    ):
        return False
    # Same per-page predicates the effective SQL loops per item,
    # derived once per (site, statuses) pair: the target exists iff
    # EXACTLY one eligible static page has this effective route.
    return memo.internal_target_counts(site_id, status_set).get(target_value, 0) == 1


def navigation_resolved_items(
    facts: Mapping[UUID, RenderPageFact],
    enabled_tags: frozenset[str],
    items: Sequence[NavigationItemRawRow],
    *,
    site_id: UUID,
    locale: str | None,
    default_locale: str,
    statuses: Sequence[str],
    route_memo: _RouteMemo | None = None,
) -> tuple[NavigationItemRow, ...]:
    """059 port: complete per-item target validation over raw items.

    ``locale`` is the caller's selected locale; 059 keeps it only as a
    NULL guard up front (zero rows), and the INTERNAL check receives
    the item's own locale but ignores it (locale-neutral gate), which
    the port preserves exactly.  Invalid guard input yields the SQL's
    zero-row result.  Raises :class:`SurfaceReadError` with the exact
    059 messages: RENDER_NAVIGATION_PAGE_INVALID for EVERY PAGE-branch
    failure (the lookup miss, 057's validator errors and the
    effective-route/href-shape checks - 059 catches 057's
    NAVIGATION_PAGE_INVALID and remaps it, so the internal code never
    surfaces) and RENDER_NAVIGATION_TARGET_INVALID (INTERNAL/unknown
    kinds).  ``route_memo`` is the shared per-request derivation
    (R8 bound); a fresh memo is started when omitted.
    """
    if (
        locale is None
        or not statuses
        or any(status not in ("PUBLISHED", "DRAFT") for status in statuses)
    ):
        return ()
    status_set = set(statuses)
    memo = _route_memo(facts, default_locale, enabled_tags, route_memo)
    resolved: list[NavigationItemRow] = []
    for item in items:
        (
            item_id,
            item_site_id,
            navigation_id,
            parent_id,
            page_id,
            target_kind,
            target_value,
            labels,
            item_locale,
            position,
        ) = item
        if target_kind == "PAGE":
            if page_id is None or target_value != str(page_id):
                raise SurfaceReadError("RENDER_NAVIGATION_PAGE_INVALID")
            fact = facts.get(page_id)
            if (
                fact is None
                or fact.site_id != site_id
                or fact.status not in status_set
                or fact.locale not in enabled_tags
            ):
                raise SurfaceReadError("RENDER_NAVIGATION_PAGE_INVALID")
            # 059's PAGE branch: the lookup miss above plus 057's
            # validator (route_template must be NULL, the effective
            # route must exist and be a safe href) all surface as the
            # single 059 code - the internal NAVIGATION_PAGE_INVALID
            # is caught and remapped, never returned verbatim.
            try:
                if fact.route_template is not None:
                    raise SurfaceReadError("NAVIGATION_PAGE_INVALID")
                target = memo.route(fact.id)
                if not _NAV_HREF_RE.fullmatch(target) or _BAD_ROUTE_RE.search(target):
                    raise SurfaceReadError("NAVIGATION_PAGE_INVALID")
            except SurfaceReadError:
                raise SurfaceReadError("RENDER_NAVIGATION_PAGE_INVALID") from None
        elif target_kind == "INTERNAL":
            if page_id is not None or not _internal_target_exists(
                facts,
                site_id=site_id,
                target_value=target_value,
                locale=item_locale,
                default_locale=default_locale,
                enabled_tags=enabled_tags,
                statuses=statuses,
                route_memo=memo,
            ):
                raise SurfaceReadError("RENDER_NAVIGATION_TARGET_INVALID")
            target = target_value
        elif target_kind not in ("INTERNAL", "EXTERNAL") or page_id is not None:
            raise SurfaceReadError("RENDER_NAVIGATION_TARGET_INVALID")
        else:
            target = target_value
        resolved.append(
            (
                item_id,
                item_site_id,
                navigation_id,
                parent_id,
                page_id,
                target_kind,
                target_value,
                labels,
                item_locale,
                position,
                target,
            )
        )
    return tuple(resolved)


def page_ancestor_chain(
    facts: Mapping[UUID, RenderPageFact],
    *,
    site_id: UUID,
    page_id: UUID,
) -> tuple[tuple[int, RenderPageFact], ...]:
    """067 port: the retained ancestor chain, root-to-parent order.

    The SQL's ``max(depth) OVER () - depth + 1`` is computed over the
    WHOLE chain (the page itself at depth 1); the output keeps only
    ``depth > 1`` ordered ``depth DESC``.  The topmost (root-side)
    ancestor therefore comes FIRST at position 1 and the page's
    DIRECT parent is LAST at position ``len(chain) - 1``; this port
    returns exactly that ``(position, fact)`` order.  The recursive
    CTE carries no visited-set guard beyond its depth bound, so a
    parent cycle yields the same repeated rows; the port walks the
    identical 64-level bound.  Unknown/deleted pages yield the SQL's
    zero rows.  The caller computes each ancestor's effective route
    (sharing the request memo) and maps a 050 failure exactly as the
    live SQL's per-row call errors.
    """
    page = facts.get(page_id)
    if page is None or page.site_id != site_id:
        return ()
    chain: list[RenderPageFact] = [page]
    current = page
    while len(chain) < 64:
        parent_id = current.parent_id
        parent = facts.get(parent_id) if parent_id is not None else None
        if (
            parent is None
            or parent.site_id != site_id
            or parent.locale != current.locale
        ):
            break
        chain.append(parent)
        current = parent
    max_depth = len(chain)
    return tuple(
        (max_depth - index, chain[index]) for index in range(max_depth - 1, 0, -1)
    )


class FrozenRenderSurface:
    """The immutable review-snapshot/v2 read surface (R5: frozen input
    only - never live canonical/COW content, live media lookups or an
    active-preview fallback).

    The single input is the COMPLETE ``control.review_snapshot`` row as
    returned by ``control.slaif_review_snapshot_frozen_state`` (jsonb).
    Construction is the shared verified admission seam
    (``admit_frozen_snapshot``); only its verified result is accepted,
    and every family row is then typed with exact key sets, real
    site/type/page/reference bindings and id uniqueness, so the shared
    helpers can never see a partially validated document.
    """

    def __init__(
        self,
        row: Mapping[str, Any],
        *,
        expected_snapshot_id: UUID,
        expected_site_id: UUID,
        expected_workspace_id: UUID,
    ) -> None:
        payload, site_profile = admit_frozen_snapshot(
            row,
            expected_snapshot_id=expected_snapshot_id,
            expected_site_id=expected_site_id,
            expected_workspace_id=expected_workspace_id,
        )
        site_id = expected_site_id
        self._site_id: UUID = site_id
        self._base_site_revision: int = _int(payload["base_site_revision"])
        self._site_key: str = _nonempty_text(site_profile["site_key"])
        self._site_status: str = _text(site_profile["status"])
        self._default_locale: str = _nonempty_text(site_profile["default_locale"])
        self._catalog_version: str = _text(site_profile["component_catalog_version"])
        try:
            self._build_families(
                payload,
                site_id=site_id,
                expected_workspace_id=expected_workspace_id,
            )
        except SurfaceReadError:
            raise
        except (TypeError, ValueError, KeyError):
            raise _refusal() from None

    def _build_families(
        self,
        payload: Mapping[str, Any],
        *,
        site_id: UUID,
        expected_workspace_id: UUID,
    ) -> None:
        pages_raw = payload["pages"]
        page_ids: set[UUID] = set()
        for raw in pages_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            page_id = _uuid(raw.get("id"))
            if page_id in page_ids:
                raise _refusal()
            page_ids.add(page_id)
        # Parent binding against the FULL page id set (deleted parents
        # included): a non-deleted page whose parent is deleted still
        # passes here and is refused at resolution time by the 049
        # port with PAGE_PARENT_INVALID, exactly the SQL behavior.
        for raw in pages_raw:
            parent = _optional_uuid(raw.get("parent_id"))
            if parent is not None and parent not in page_ids:
                raise _refusal()
        # The 049-ported hierarchy walk only traverses non-deleted
        # pages (a deleted parent raises PAGE_PARENT_INVALID, exactly
        # the SQL behavior); retained tombstones stay captured data,
        # never resolution input.
        self._resolution_facts: tuple[RenderPageFact, ...] = tuple(
            _page_fact(site_id, raw)
            for raw in pages_raw
            if raw.get("deleted_at") is None
        )
        self._resolution_by_id: dict[UUID, RenderPageFact] = {
            fact.id: fact for fact in self._resolution_facts
        }
        self._page_styles: dict[UUID, PageStyleRow | None] = {}
        for raw in pages_raw:
            page_id = _uuid(raw["id"])
            style_raw = raw["style"]
            if style_raw is not None:
                if page_id in self._page_styles:
                    raise _refusal()
                self._page_styles[page_id] = _page_style_row(
                    site_id, page_id, style_raw
                )
            elif page_id in self._page_styles:
                raise _refusal()
            else:
                self._page_styles[page_id] = None

        locales_raw = payload["locales"]
        locale_ids: set[UUID] = set()
        for raw in locales_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            locale_id = _uuid(raw.get("id"))
            if locale_id in locale_ids:
                raise _refusal()
            locale_ids.add(locale_id)
        self._locales: tuple[LocaleRow, ...] = tuple(
            _locale_row(site_id, raw) for raw in locales_raw
        )
        self._enabled_tags: tuple[str, ...] = tuple(
            row[2] for row in self._locales if row[3]
        )

        theme_raw = payload["theme"]
        self._theme: ThemeRow | None = (
            None if theme_raw is None else _theme_row(site_id, theme_raw)
        )

        regions_raw = payload["regions"]
        region_ids: set[UUID] = set()
        for raw in regions_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            region_id = _uuid(raw.get("id"))
            if region_id in region_ids:
                raise _refusal()
            region_ids.add(region_id)
        self._regions: tuple[RegionRow, ...] = tuple(
            _region_row(site_id, raw) for raw in regions_raw
        )

        navigation = payload["navigation"]
        nav_definitions_raw = navigation["definitions"]
        nav_defs_by_id: dict[UUID, None] = {}
        for raw in nav_definitions_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            nav_id = _uuid(raw.get("id"))
            if nav_id in nav_defs_by_id:
                raise _refusal()
            nav_defs_by_id[nav_id] = None
        self._navigation_definitions: tuple[NavigationDefinitionRow, ...] = tuple(
            _navigation_definition_row(site_id, raw) for raw in nav_definitions_raw
        )
        nav_items_raw = navigation["items"]
        nav_item_ids: set[UUID] = set()
        for raw in nav_items_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            item_id = _uuid(raw.get("id"))
            if item_id in nav_item_ids:
                raise _refusal()
            if _uuid(raw.get("navigation_id")) not in nav_defs_by_id:
                raise _refusal()
            # Parent binding (complete same-navigation id set,
            # order-independent, with the shared helpers' cycle/depth
            # semantics) is enforced at the admission seam; only
            # uniqueness and the definition binding are re-asserted
            # here.
            nav_item_ids.add(item_id)
        self._navigation_items_raw: tuple[NavigationItemRawRow, ...] = tuple(
            _navigation_item_raw_row(site_id, raw) for raw in nav_items_raw
        )

        redirects_raw = payload["redirects"]
        redirect_ids: set[UUID] = set()
        redirect_keys: set[tuple[str, str | None]] = set()
        for raw in redirects_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            redirect_id = _uuid(raw.get("id"))
            if redirect_id in redirect_ids:
                raise _refusal()
            key = (_text(raw.get("source_route")), _optional_text(raw.get("locale")))
            if key in redirect_keys:
                raise _refusal()
            redirect_ids.add(redirect_id)
            redirect_keys.add(key)
        self._redirects: tuple[RedirectRow, ...] = tuple(
            _redirect_row(site_id, raw) for raw in redirects_raw
        )

        compositions_raw = payload["page_compositions"]
        composition_ids: set[UUID] = set()
        compositions_by_page: dict[UUID, list[CompositionRow]] = {}
        for raw in compositions_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            composition_id = _uuid(raw.get("id"))
            if composition_id in composition_ids:
                raise _refusal()
            composition_ids.add(composition_id)
            page_id = _uuid(raw.get("page_id"))
            if page_id not in page_ids:
                raise _refusal()
            row = _composition_row(site_id, raw)
            compositions_by_page.setdefault(page_id, []).append(row)
        self._compositions_by_page: dict[UUID, tuple[CompositionRow, ...]] = {
            page_id: tuple(
                sorted(
                    rows,
                    key=lambda value: (
                        0 if value[5] is None else 1,
                        value[6],
                        value[7],
                        value[0],
                    ),
                )
            )
            for page_id, rows in compositions_by_page.items()
        }

        self._media: dict[UUID, MediaRow] = {}
        media_map = payload["media"]
        for key, raw in media_map.items():
            if not isinstance(key, str) or not isinstance(raw, Mapping):
                raise _refusal()
            entry = _media_entry(key, raw)
            if UUID(key) in self._media:
                raise _refusal()
            self._media[UUID(key)] = entry

        content = payload["content"]
        types_raw = content["types"]
        self._types: dict[UUID, ContentTypeRow] = {}
        type_keys: set[str] = set()
        for raw in types_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            type_id = _uuid(raw.get("id"))
            if type_id in self._types:
                raise _refusal()
            if _uuid(raw.get("site_id")) != site_id:
                raise _refusal()
            type_key = _text(raw.get("key"))
            if type_key in type_keys:
                raise _refusal()
            type_keys.add(type_key)
            self._types[type_id] = _content_type_row(raw)

        fields_raw = content["fields"]
        fields_by_type: dict[UUID, list[FieldDefinitionRow]] = {}
        field_ids: set[UUID] = set()
        for raw in fields_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            field_id = _uuid(raw.get("id"))
            if field_id in field_ids:
                raise _refusal()
            if _uuid(raw.get("site_id")) != site_id:
                raise _refusal()
            type_id = _uuid(raw.get("type_id"))
            if type_id not in self._types:
                raise _refusal()
            field_ids.add(field_id)
            fields_by_type.setdefault(type_id, []).append(_field_row(raw))
        self._fields_by_type: dict[UUID, tuple[FieldDefinitionRow, ...]] = {
            type_id: tuple(sorted(rows, key=lambda value: value[0]))
            for type_id, rows in fields_by_type.items()
        }
        if len(field_ids) != len(fields_raw):
            raise _refusal()

        items_raw = content["items"]
        item_ids: set[UUID] = set()
        items: list[ContentItemRow] = []
        items_per_type: dict[UUID, int] = {}
        for raw in items_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            item_id = _uuid(raw.get("id"))
            if item_id in item_ids:
                raise _refusal()
            if _uuid(raw.get("site_id")) != site_id:
                raise _refusal()
            type_id = _uuid(raw.get("type_id"))
            if type_id not in self._types:
                raise _refusal()
            item_ids.add(item_id)
            items_per_type[type_id] = items_per_type.get(type_id, 0) + 1
            items.append(_item_row(raw))
        self._items: tuple[ContentItemRow, ...] = tuple(items)

        translations_raw = content["translations"]
        translation_ids: set[UUID] = set()
        translation_keys: set[tuple[UUID, str]] = set()
        for raw in translations_raw:
            if not isinstance(raw, dict):
                raise _refusal()
            translation_id = _uuid(raw.get("id"))
            if translation_id in translation_ids:
                raise _refusal()
            if _uuid(raw.get("site_id")) != site_id:
                raise _refusal()
            item_id = _uuid(raw.get("item_id"))
            if item_id not in item_ids:
                raise _refusal()
            translation_key = (item_id, _text(raw.get("locale")))
            if translation_key in translation_keys:
                raise _refusal()
            translation_ids.add(translation_id)
            translation_keys.add(translation_key)
        self._translations: tuple[ContentItemTranslationRow, ...] = tuple(
            _translation_row(raw) for raw in translations_raw
        )

        # Relations are retained capture data (R1/R2 closure evidence);
        # the shared projection does not render them, so the rows are
        # validated (bindings + uniqueness) but never reprojected.
        relation_ids: set[UUID] = set()
        for raw in content["relations"]:
            if not isinstance(raw, dict):
                raise _refusal()
            _require_keys(raw, _RELATION_KEYS)
            relation_id = _uuid(raw["id"])
            if relation_id in relation_ids:
                raise _refusal()
            if _uuid(raw["site_id"]) != site_id:
                raise _refusal()
            if _uuid(raw["source_item_id"]) not in item_ids:
                raise _refusal()
            if _uuid(raw["target_item_id"]) not in item_ids:
                raise _refusal()
            if _uuid(raw["field_definition_id"]) not in field_ids:
                raise _refusal()
            relation_ids.add(relation_id)

        views_raw = content["views"]
        self._views: dict[UUID, CollectionViewRow] = {}
        for raw in views_raw:
            view_id = _uuid(raw["id"])
            if view_id in self._views:
                raise _refusal()
            if _uuid(raw["site_id"]) != site_id:
                raise _refusal()
            if _uuid(raw["type_id"]) not in self._types:
                raise _refusal()
            self._views[view_id] = _collection_view_row(raw)

        # Proposals and media inventory are retained capture data:
        # validated (shape, site/workspace binding, uniqueness, caps)
        # but never reprojected by the shared engine.
        proposal_ids: set[UUID] = set()
        for raw in payload["proposals"]:
            if not isinstance(raw, dict):
                raise _refusal()
            _require_keys(raw, _PROPOSAL_KEYS)
            proposal_id = _uuid(raw["id"])
            if proposal_id in proposal_ids:
                raise _refusal()
            if _uuid(raw["site_id"]) != site_id:
                raise _refusal()
            if _uuid(raw["workspace_id"]) != expected_workspace_id:
                raise _refusal()
            proposal_ids.add(proposal_id)
        inventory_ids: set[UUID] = set()
        for raw in payload["media_inventory"]:
            if not isinstance(raw, dict):
                raise _refusal()
            _require_keys(raw, _MEDIA_INVENTORY_KEYS)
            inventory_id = _uuid(raw["id"])
            if inventory_id in inventory_ids:
                raise _refusal()
            if _uuid(raw["site_id"]) != site_id:
                raise _refusal()
            inventory_ids.add(inventory_id)

    ...

    @property
    def base_site_revision(self) -> int:
        """The locked freeze revision (the frozen site block's
        ``canonical_revision``)."""

        return self._base_site_revision

    @property
    def site_key(self) -> str:
        return self._site_key

    @property
    def site_status(self) -> str:
        return self._site_status

    @property
    def default_locale(self) -> str:
        return self._default_locale

    async def fetch_locales(self, *, site_id: UUID) -> tuple[LocaleRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._locales

    async def fetch_enabled_locale_tags(
        self, *, site_id: UUID
    ) -> tuple[EnabledTagRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return tuple((tag,) for tag in self._enabled_tags)

    async def fetch_pages(self, *, site_id: UUID) -> tuple[PageFactRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._resolution_facts

    async def fetch_redirects(self, *, site_id: UUID) -> tuple[RedirectRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._redirects

    async def fetch_navigation_definitions(
        self, *, site_id: UUID
    ) -> tuple[NavigationDefinitionRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._navigation_definitions

    async def fetch_navigation_items(
        self, *, site_id: UUID
    ) -> tuple[NavigationItemRawRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._navigation_items_raw

    async def fetch_theme(self, *, site_id: UUID) -> ThemeRow | None:
        if site_id != self._site_id:
            raise _refusal()
        return self._theme

    async def fetch_page_style(self, *, page_id: UUID) -> PageStyleRow | None:
        return self._page_styles.get(page_id)

    async def fetch_catalog_version(self, *, site_id: UUID) -> str | None:
        if site_id != self._site_id:
            raise _refusal()
        return self._catalog_version

    async def fetch_regions(self, *, site_id: UUID) -> tuple[RegionRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._regions

    async def fetch_composition(
        self, *, site_id: UUID, page_id: UUID
    ) -> tuple[CompositionRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        return self._compositions_by_page.get(page_id, ())

    async def resolve_media(self, *, site_id: UUID, media_id: UUID) -> MediaRow | None:
        if site_id != self._site_id:
            raise _refusal()
        return self._media.get(media_id)

    async def fetch_collection_view(self, *, view_id: UUID) -> CollectionViewRow | None:
        return self._views.get(view_id)

    async def fetch_content_type(self, *, type_id: UUID) -> ContentTypeRow | None:
        return self._types.get(type_id)

    async def fetch_field_definitions(
        self, *, type_id: UUID
    ) -> tuple[FieldDefinitionRow, ...]:
        return self._fields_by_type.get(type_id, ())

    async def count_content_items(
        self, *, site_id: UUID, type_id: UUID, statuses: Sequence[str]
    ) -> int:
        if site_id != self._site_id:
            raise _refusal()
        status_set = set(statuses)
        return sum(
            1 for row in self._items if row[2] == type_id and row[4] in status_set
        )

    async def fetch_content_items(
        self, *, site_id: UUID, type_id: UUID, statuses: Sequence[str]
    ) -> tuple[ContentItemRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        status_set = set(statuses)
        rows = [
            row for row in self._items if row[2] == type_id and row[4] in status_set
        ]
        if len(rows) > MAX_CANDIDATES:
            raise SurfaceReadError("query_cost")
        return tuple(sorted(rows, key=lambda value: value[0]))

    async def fetch_content_item_translations(
        self,
        *,
        site_id: UUID,
        item_ids: Sequence[UUID],
        locales: Sequence[str],
    ) -> tuple[ContentItemTranslationRow, ...]:
        if site_id != self._site_id:
            raise _refusal()
        item_set = set(item_ids)
        locale_set = set(locales)
        return tuple(
            row
            for row in self._translations
            if row[0] in item_set and row[1] in locale_set
        )

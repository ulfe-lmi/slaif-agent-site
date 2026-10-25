"""083/5-b RC2/RC8 — actual live-SQL versus common-port parity proof.

RC2: the supported routing / locale / navigation boundary cases are
proven against REAL PostgreSQL: the raw-SQL oracle calls the actual
050 ``slaif_agent_page_effective_route``, 056 ``slaif_render_page_resolve``,
057 ``slaif_navigation_page_target_validate``, 059
``slaif_render_navigation_items`` and 067 ``slaif_page_ancestor_chain``
functions over the same rows the shared Python port consumes, and both
sides must agree on every winner, ambiguity, and stable failure.  The
six collection binding variants (List/Grid/Detail/Search/Filter/
RelatedItems) are proven through the actual common consumer
(``RenderProjectionService.canonical``) with exact binding contents,
localized selection and default fallback.

RC8: a REAL RenderProjectionService request carrying the admitted
maximum navigation group (256 items, the frozen per-group cap) is
instrumented reversibly at the actual work seams and shows: page-
bounded derivations (each of the 17 pages derived at most once),
exactly one winner selection, the static route index and the
INTERNAL target counts each CONSTRUCTED exactly once, the retained
facts walked exactly three times in total (measured iterator
pulls, not cache growth), and one page fetch plus one navigation
fetch for the whole group.  The per-group 255/256/257 boundary is
proven through the real frozen admission seam (build + canonical
digest + admit).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.content_model.canonical import (
    canonical_digest,
    canonical_json,
    parse_snapshot_text,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.render_api import frozen_source as fs
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    ProjectionNode,
    RenderPageRequest,
    RenderProjectionService,
)
from slaif_agent_site.review_worker.snapshot import (
    STATE_VERSION,
    build_snapshot_document,
)
from slaif_agent_site.sites import CreateSiteRequest
from slaif_agent_site.sites.service import SiteService
from test_render_structure_router import _RenderAdapter

PUBLISHED = "PUBLISHED"
DRAFT = "DRAFT"
RESOLVED = (PUBLISHED,)
DRAFT_RESOLVED = (DRAFT, PUBLISHED)
_FROZEN_ARGON2 = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "AAAAAAAAAAAAAAAAAAAAAA$"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
)


def _jsonb_text(value: Any) -> str:
    """Lossless jsonb re-bind for captured rows.

    asyncpg returns jsonb columns as JSON text on the plain owner
    connection, so text passes through unchanged and already
    decoded values are encoded exactly once.  Blind json.dumps on
    a fetched value would double-encode it into a JSON string and
    the *_object check constraints would correctly refuse it.
    """
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _pg_error_message(error: BaseException) -> str:
    """The first line of a Postgres error is the exact stable message."""
    return str(error).strip().splitlines()[0]


async def _sql_effective_route(
    owner: Any, page_id: UUID
) -> tuple[str | None, str | None]:
    """Actual 050 oracle: (route, None) or (None, exact error message)."""
    try:
        row = await owner.fetchrow(
            "SELECT content.slaif_agent_page_effective_route($1) AS route",
            page_id,
        )
    except asyncpg.PostgresError as error:
        return None, _pg_error_message(error)
    if row is None or row["route"] is None:
        return None, None
    return str(row["route"]), None


async def _sql_resolve(
    owner: Any,
    site_id: UUID,
    route: str,
    locale: str,
    statuses: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """Actual 056 oracle: (winner page id, None) or (None, error message)."""
    try:
        rows = await owner.fetch(
            "SELECT id FROM content.slaif_render_page_resolve($1,$2,$3,$4::text[])",
            site_id,
            route,
            locale,
            list(statuses),
        )
    except asyncpg.PostgresError as error:
        return None, _pg_error_message(error)
    if not rows:
        return None, None
    assert len(rows) == 1
    return str(rows[0]["id"]), None


async def _sql_internal_target(
    owner: Any,
    site_id: UUID,
    target: str | None,
    locale: str,
    statuses: tuple[str, ...],
) -> bool:
    """Actual 059 INTERNAL oracle."""
    row = await owner.fetchrow(
        "SELECT content.slaif_render_internal_target_exists"
        "($1,$2,$3,$4::text[]) AS found",
        site_id,
        target,
        locale,
        list(statuses),
    )
    assert row is not None
    return bool(row["found"])


async def _sql_navigation_rows(
    owner: Any,
    site_id: UUID,
    locale: str,
    statuses: tuple[str, ...],
) -> tuple[tuple[Any, ...], ...] | str:
    """Actual 059 oracle: resolved rows, or the exact error message."""
    try:
        rows = await owner.fetch(
            "SELECT * FROM content.slaif_render_navigation_items($1,$2,$3::text[])",
            site_id,
            locale,
            list(statuses),
        )
    except asyncpg.PostgresError as error:
        return _pg_error_message(error)
    return tuple(
        (
            row["id"],
            row["site_id"],
            row["navigation_id"],
            row["parent_id"],
            row["page_id"],
            row["target_kind"],
            row["target_value"],
            row["labels"],
            row["locale"],
            int(row["position"]),
            row["resolved_target"],
        )
        for row in rows
    )


async def _sql_validate_page_target(
    owner: Any, site_id: UUID, page_id: UUID, target: str
) -> str | None:
    """Actual 057 oracle: None when valid, else the exact error message."""
    try:
        await owner.execute(
            "SELECT content.slaif_navigation_page_target_validate($1,$2,$3)",
            site_id,
            page_id,
            target,
        )
    except asyncpg.PostgresError as error:
        return _pg_error_message(error)
    return None


async def _sql_ancestor_chain(
    owner: Any, site_id: UUID, page_id: UUID
) -> tuple[tuple[int, UUID, str, str, str], ...]:
    """Actual 067 oracle rows (position, id, title, locale, route)."""
    rows = await owner.fetch(
        "SELECT * FROM content.slaif_page_ancestor_chain($1,$2)",
        site_id,
        page_id,
    )
    return tuple(
        (
            int(row["chain_position"]),
            row["id"],
            str(row["title"]),
            str(row["locale"]),
            str(row["effective_route"]),
        )
        for row in rows
    )


def _walk_nodes(nodes: tuple[ProjectionNode, ...]) -> Iterator[ProjectionNode]:
    """Depth-first pre-order walk of the composition node tree."""
    for node in nodes:
        yield node
        yield from _walk_nodes(node.children)


def _sorted_by_item(rows: Any) -> Any:
    """Deterministic 059 row order for the live/port comparison."""
    return sorted(rows, key=lambda row: (row[2], row[9], row[0]))


@pytest.mark.asyncio
async def test_live_sql_common_port_route_navigation_differential(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """RC2: every supported boundary case, live SQL versus common port."""
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="par-routediff",
                display_name="Parity Route Diff",
                default_locale="en",
            )
        )
        site_id = site.site_id
        home_id, news_id, detail_id, alpha_id = (uuid4() for _ in range(4))
        overp_id, overd1_id, overd2_id, hidden_id, ghost_id = (
            uuid4() for _ in range(5)
        )
        cyc1_id, cyc2_id, home_sl_id, news_sl_id = (uuid4() for _ in range(4))
        chain64_ids = [uuid4() for _ in range(64)]
        chain65_ids = [uuid4() for _ in range(65)]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($1,'sl-SI',true,false,1) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            page_values = [
                (home_id, "home", PUBLISHED, None, None),
                (news_id, "news", PUBLISHED, home_id, None),
                (detail_id, "detail", PUBLISHED, news_id, "{slug}"),
                (alpha_id, "alpha", PUBLISHED, news_id, None),
                # The schema's active (site, locale, parent, slug)
                # unique index forbids two static pages sharing one
                # slug, so the duplicate effective route is realized
                # the way live rows can carry it: two dynamic
                # siblings under one parent, both effective /over/{slug}.
                (overp_id, "over", PUBLISHED, home_id, None),
                (overd1_id, "d1", PUBLISHED, overp_id, "{slug}"),
                (overd2_id, "d2", PUBLISHED, overp_id, "{slug}"),
                (hidden_id, "hidden", DRAFT, home_id, None),
                (ghost_id, "ghost", PUBLISHED, home_id, None),
                (cyc1_id, "cyc1", PUBLISHED, None, None),
                (cyc2_id, "cyc2", PUBLISHED, None, None),
                (home_sl_id, "home", PUBLISHED, None, None),
                (news_sl_id, "news", PUBLISHED, home_sl_id, None),
            ]
            for page_id, slug, status, parent, template in page_values:
                locale = "sl-SI" if page_id in (home_sl_id, news_sl_id) else "en"
                await owner.execute(
                    "INSERT INTO content.page_base "
                    "(id,site_id,slug,title,status,locale,parent_id,"
                    "route_template) VALUES "
                    "($1,$2,$3,$4,$5,$6,$7,$8)",
                    page_id,
                    site_id,
                    slug,
                    f"parity-{slug}",
                    status,
                    locale,
                    parent,
                    template,
                )
            # Deleted page: the live 050 lookup is deleted_at IS NULL.
            await owner.execute(
                "UPDATE content.page_base SET deleted_at=CURRENT_TIMESTAMP WHERE id=$1",
                ghost_id,
            )
            # Two-cycle parent pair (inserted with NULL parent, then wired).
            await owner.execute(
                "UPDATE content.page_base SET parent_id=$2 WHERE id=$1",
                cyc1_id,
                cyc2_id,
            )
            await owner.execute(
                "UPDATE content.page_base SET parent_id=$2 WHERE id=$1",
                cyc2_id,
                cyc1_id,
            )
            # Depth-bound chains: 64 pages resolve, 65 pages cycle.
            for index, page_id in enumerate(chain64_ids):
                await owner.execute(
                    "INSERT INTO content.page_base "
                    "(id,site_id,slug,title,status,locale,parent_id) VALUES "
                    "($1,$2,$3,$4,$5,'en',$6)",
                    page_id,
                    site_id,
                    f"c{index:02d}",
                    f"Chain 64 {index}",
                    PUBLISHED,
                    None if index == 0 else chain64_ids[index - 1],
                )
            for index, page_id in enumerate(chain65_ids):
                await owner.execute(
                    "INSERT INTO content.page_base "
                    "(id,site_id,slug,title,status,locale,parent_id) VALUES "
                    "($1,$2,$3,$4,$5,'en',$6)",
                    page_id,
                    site_id,
                    f"d{index:02d}",
                    f"Chain 65 {index}",
                    PUBLISHED,
                    None if index == 0 else chain65_ids[index - 1],
                )
            # One navigation with a fully valid item set (the 059 input).
            nav_id = uuid4()
            page_item_id, internal_item_id, external_item_id = (
                uuid4() for _ in range(3)
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'primary','Primary', $3::jsonb, '{}'::jsonb)",
                nav_id,
                site_id,
                '{"en":"Primary"}',
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,"
                "target_kind,target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4::uuid,$5,'PAGE',$6,$7::jsonb,'en',0),"
                "($8,$2,$3,NULL,$9::uuid,NULL,'INTERNAL','/news',"
                "$10::jsonb,NULL,1),"
                "($11,$2,$3,NULL,$9::uuid,NULL,'EXTERNAL',"
                "'https://example.test/docs',$12::jsonb,NULL,2)",
                page_item_id,
                site_id,
                nav_id,
                home_id,
                news_id,
                str(news_id),
                '{"en":"News"}',
                internal_item_id,
                "00000000-0000-0000-0000-000000000000",
                '{"en":"To news"}',
                external_item_id,
                '{"en":"Docs"}',
            )
        adapter = _RenderAdapter(public_pool)
        service = RenderProjectionService(adapter)
        base = "/s/par-routediff"
        async with public_pool.acquire() as connection:
            surface = fs.DatabaseRenderSurface(connection)
            facts = {
                fact.id: fact for fact in await surface.fetch_pages(site_id=site_id)
            }
            raw_items = await surface.fetch_navigation_items(site_id=site_id)
            enabled_tags = frozenset(
                tag
                for (tag,) in await surface.fetch_enabled_locale_tags(site_id=site_id)
            )
            default_locale = "en"

            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                # -------------------------------------------------- 050 diff
                expectations: dict[UUID, str] = {
                    home_id: "/",
                    news_id: "/news",
                    detail_id: "/news/{slug}",
                    alpha_id: "/news/alpha",
                    overp_id: "/over",
                    overd1_id: "/over/{slug}",
                    overd2_id: "/over/{slug}",
                    hidden_id: "/hidden",
                    home_sl_id: "/sl-SI",
                    news_sl_id: "/sl-SI/news",
                    chain64_ids[63]: "/" + "/".join([f"c{i:02d}" for i in range(64)]),
                }
                for page_id in facts:
                    sql_route, sql_error = await _sql_effective_route(owner, page_id)
                    try:
                        port_route = fs.page_effective_route(
                            facts,
                            page_id=page_id,
                            default_locale=default_locale,
                            enabled_tags=enabled_tags,
                        )
                        port_error: str | None = None
                    except fs.SurfaceReadError as error:
                        port_route = None
                        port_error = error.reason
                    assert sql_route == port_route
                    assert sql_error == port_error, (page_id, sql_error, port_error)
                    if page_id in expectations:
                        assert port_route == expectations[page_id]
                for page_id in (ghost_id, cyc1_id, cyc2_id, chain65_ids[64]):
                    sql_route, sql_error = await _sql_effective_route(owner, page_id)
                    try:
                        fs.page_effective_route(
                            facts,
                            page_id=page_id,
                            default_locale=default_locale,
                            enabled_tags=enabled_tags,
                        )
                        raise AssertionError("expected PAGE_HIERARCHY_CYCLE/NOT_FOUND")
                    except fs.SurfaceReadError as error:
                        assert sql_route is None
                        assert sql_error == error.reason

                # -------------------------------------------------- 056 diff
                resolve_cases: list[
                    tuple[str, str, tuple[str, ...], str | None, str | None]
                ] = [
                    ("/", "en", RESOLVED, str(home_id), None),
                    ("/news", "en", RESOLVED, str(news_id), None),
                    ("/news/alpha", "en", RESOLVED, None, "RENDER_ROUTE_AMBIGUOUS"),
                    ("/news/gamma", "en", RESOLVED, str(detail_id), None),
                    ("/news/gamma/", "en", RESOLVED, None, None),
                    ("/over/x", "en", RESOLVED, None, "RENDER_ROUTE_AMBIGUOUS"),
                    ("/hidden", "en", RESOLVED, None, None),
                    ("/a..b", "en", RESOLVED, None, None),
                    ("/api/anything", "en", RESOLVED, None, None),
                    # The service and the frozen Web mirror lowercase every
                    # path segment before resolution (native 0), so the
                    # locale-prefixed positive case uses the normalized
                    # lowercase route while the locale stays stored sl-SI.
                    ("/sl-si/news", "sl-SI", RESOLVED, str(news_sl_id), None),
                    # Raw mixed-case input fails the shared lowercase route
                    # shape on both sides: the SQL RETURNs zero rows and the
                    # port returns None, with no error on either side.
                    ("/sl-SI/news", "sl-SI", RESOLVED, None, None),
                    ("/sl-si/news", "en", RESOLVED, None, None),
                    ("/hidden", "en", DRAFT_RESOLVED, str(hidden_id), None),
                    ("/news/gamma", "en", (DRAFT,), None, None),
                ]
                for route, locale, statuses, want_id, want_error in resolve_cases:
                    sql_id, sql_error = await _sql_resolve(
                        owner, site_id, route, locale, statuses
                    )
                    try:
                        winner = fs.resolve_page_route(
                            facts,
                            site_id=site_id,
                            route=route,
                            locale=locale,
                            statuses=statuses,
                            default_locale=default_locale,
                            enabled_tags=enabled_tags,
                        )
                        port_id: str | None = (
                            str(winner.id) if winner is not None else None
                        )
                        port_error = None
                    except fs.SurfaceReadError as error:
                        port_id, port_error = None, error.reason
                    assert sql_id == port_id, (route, sql_id, port_id)
                    assert sql_error == port_error, (route, sql_error, port_error)
                    assert port_id == want_id
                    assert port_error == want_error

                # --------------------------------------------- 059 gate diff
                internal_cases: list[tuple[str | None, tuple[str, ...], bool]] = [
                    ("/", RESOLVED, True),
                    ("/news", RESOLVED, True),
                    ("/news/alpha", RESOLVED, True),
                    ("/over/x", RESOLVED, False),
                    ("/news/gamma", RESOLVED, False),
                    ("/api/x", RESOLVED, False),
                    ("/media", RESOLVED, False),
                    ("/hidden", RESOLVED, False),
                    ("/hidden", DRAFT_RESOLVED, True),
                    ("/sl-SI/news", RESOLVED, True),
                    (None, RESOLVED, False),
                    ("/news/Alpha", RESOLVED, False),
                ]
                for target, statuses, want in internal_cases:
                    sql_found = await _sql_internal_target(
                        owner, site_id, target, "en", statuses
                    )
                    port_found = fs._internal_target_exists(
                        facts,
                        site_id=site_id,
                        target_value=target,
                        locale="en",
                        default_locale=default_locale,
                        enabled_tags=enabled_tags,
                        statuses=statuses,
                    )
                    assert sql_found == port_found, (target, sql_found, port_found)
                    assert port_found == want

                # ------------------------------------- 059/057 navigation diff
                sql_rows = await _sql_navigation_rows(owner, site_id, "en", RESOLVED)
                assert isinstance(sql_rows, tuple), sql_rows
                port_rows = fs.navigation_resolved_items(
                    facts,
                    enabled_tags,
                    raw_items,
                    site_id=site_id,
                    locale="en",
                    default_locale=default_locale,
                    statuses=RESOLVED,
                )
                assert len(sql_rows) == len(port_rows) == 3
                for sql_row, port_row in zip(
                    _sorted_by_item(sql_rows),
                    _sorted_by_item(port_rows),
                    strict=True,
                ):
                    assert sql_row[:10] == port_row[:10]
                    assert sql_row[10] == port_row[10]
                resolved_targets = {row[6]: row[10] for row in port_rows}
                assert resolved_targets["/news"] == "/news"
                assert resolved_targets[str(news_id)] == "/news"
                assert (
                    resolved_targets["https://example.test/docs"]
                    == "https://example.test/docs"
                )
                # 057 per-page validation: the port re-maps every PAGE
                # branch failure to the single 059 code.
                for page_id in (news_id, home_sl_id, overp_id):
                    assert (
                        await _sql_validate_page_target(
                            owner, site_id, page_id, str(page_id)
                        )
                        is None
                    )
                for page_id in (
                    detail_id,
                    ghost_id,
                    cyc1_id,
                ):
                    sql_message = await _sql_validate_page_target(
                        owner, site_id, page_id, str(page_id)
                    )
                    assert sql_message is not None
                bad_item_sets = {
                    "dynamic page target": (
                        "INSERT INTO content.navigation_item_base "
                        "(id,site_id,navigation_id,parent_id,parent_key,"
                        "page_id,target_kind,target_value,labels,locale,"
                        "position) VALUES ($1,$2,$3,NULL,$4::uuid,$5,'PAGE',"
                        "$6,$7::jsonb,'en',3)",
                        (
                            uuid4(),
                            site_id,
                            nav_id,
                            news_id,
                            detail_id,
                            str(detail_id),
                            '{"en":"Bad"}',
                        ),
                        "RENDER_NAVIGATION_PAGE_INVALID",
                    ),
                    "target value mismatch": (
                        "INSERT INTO content.navigation_item_base "
                        "(id,site_id,navigation_id,parent_id,parent_key,"
                        "page_id,target_kind,target_value,labels,locale,"
                        "position) VALUES ($1,$2,$3,NULL,$4::uuid,$5,'PAGE',"
                        "$6,$7::jsonb,'en',4)",
                        (
                            uuid4(),
                            site_id,
                            nav_id,
                            home_id,
                            news_id,
                            str(home_id),
                            '{"en":"Bad"}',
                        ),
                        "RENDER_NAVIGATION_PAGE_INVALID",
                    ),
                    "duplicate internal target": (
                        "INSERT INTO content.navigation_item_base "
                        "(id,site_id,navigation_id,parent_id,parent_key,"
                        "page_id,target_kind,target_value,labels,locale,"
                        "position) VALUES ($1,$2,$3,NULL,$4::uuid,NULL,"
                        "'INTERNAL',$5,$6::jsonb,NULL,5)",
                        (
                            uuid4(),
                            site_id,
                            nav_id,
                            "00000000-0000-0000-0000-000000000000",
                            "/dup",
                            '{"en":"Bad"}',
                        ),
                        "RENDER_NAVIGATION_TARGET_INVALID",
                    ),
                    "reserved internal target": (
                        "INSERT INTO content.navigation_item_base "
                        "(id,site_id,navigation_id,parent_id,parent_key,"
                        "page_id,target_kind,target_value,labels,locale,"
                        "position) VALUES ($1,$2,$3,NULL,$4::uuid,NULL,"
                        "'INTERNAL',$5,$6::jsonb,NULL,6)",
                        (
                            uuid4(),
                            site_id,
                            nav_id,
                            "00000000-0000-0000-0000-000000000000",
                            "/api/x",
                            '{"en":"Bad"}',
                        ),
                        "RENDER_NAVIGATION_TARGET_INVALID",
                    ),
                }
                for label, (sql, params, want_code) in bad_item_sets.items():
                    bad_id = params[0]
                    await owner.execute(sql, *params)
                    sql_result = await _sql_navigation_rows(
                        owner, site_id, "en", RESOLVED
                    )
                    assert isinstance(sql_result, str)
                    assert sql_result == want_code, label
                    # A fresh surface instance: the live surface memoizes
                    # per request, and this is a new admitted request.
                    fresh_items = await fs.DatabaseRenderSurface(
                        connection
                    ).fetch_navigation_items(site_id=site_id)
                    try:
                        with pytest.raises(fs.SurfaceReadError, match=want_code):
                            fs.navigation_resolved_items(
                                facts,
                                enabled_tags,
                                fresh_items,
                                site_id=site_id,
                                locale="en",
                                default_locale=default_locale,
                                statuses=RESOLVED,
                            )
                    finally:
                        await owner.execute(
                            "DELETE FROM content.navigation_item_base WHERE id=$1",
                            bad_id,
                        )

                # ------------------------------------------------ 067 diff
                ancestor_cases: list[
                    tuple[UUID, tuple[tuple[int, UUID, str, str, str], ...]]
                ] = [
                    (news_id, ((1, home_id, "parity-home", "en", "/"),)),
                    (
                        chain64_ids[63],
                        tuple(
                            (
                                index + 1,
                                chain64_ids[index],
                                f"Chain 64 {index}",
                                "en",
                                "/" + "/".join([f"c{i:02d}" for i in range(index + 1)]),
                            )
                            for index in range(63)
                        ),
                    ),
                ]
                for page_id, expected_rows in ancestor_cases:
                    sql_chain = await _sql_ancestor_chain(owner, site_id, page_id)
                    port_chain = fs.page_ancestor_chain(
                        facts, site_id=site_id, page_id=page_id
                    )
                    assert len(sql_chain) == len(port_chain)
                    assert sql_chain == expected_rows
                    for (
                        sql_pos,
                        sql_page_id,
                        sql_title,
                        sql_locale,
                        sql_route,
                    ), (port_pos, fact) in zip(sql_chain, port_chain, strict=True):
                        assert sql_pos == port_pos
                        assert sql_page_id == fact.id
                        assert sql_title == fact.title
                        assert sql_locale == fact.locale
                        assert sql_route == fs.page_effective_route(
                            facts,
                            page_id=fact.id,
                            default_locale=default_locale,
                            enabled_tags=enabled_tags,
                        )
                # The two-cycle: the live 067 SELECT list calls the 050
                # effective route per row, so the 050 bound failure
                # (PAGE_HIERARCHY_CYCLE) errors the whole query and SQL
                # yields no rows at all.  The port walks the identical
                # 64-level bound with no visited set: its retained rows
                # repeat the two pages, root-side position 1 first, and
                # each row's route derivation fails with the exact same 050
                # reason the live per-row call raises.
                try:
                    await _sql_ancestor_chain(owner, site_id, cyc1_id)
                    raise AssertionError("expected PAGE_HIERARCHY_CYCLE")
                except asyncpg.PostgresError as error:
                    assert _pg_error_message(error) == "PAGE_HIERARCHY_CYCLE"
                port_cycle = fs.page_ancestor_chain(
                    facts, site_id=site_id, page_id=cyc1_id
                )
                assert len(port_cycle) == 63
                assert [fact.id for _position, fact in port_cycle][:4] == [
                    cyc2_id,
                    cyc1_id,
                    cyc2_id,
                    cyc1_id,
                ]
                for _position, fact in port_cycle:
                    with pytest.raises(
                        fs.SurfaceReadError, match="PAGE_HIERARCHY_CYCLE"
                    ):
                        fs.page_effective_route(
                            facts,
                            page_id=fact.id,
                            default_locale=default_locale,
                            enabled_tags=enabled_tags,
                        )
                # Deleted and unknown pages yield the SQL's zero rows.
                assert await _sql_ancestor_chain(owner, site_id, ghost_id) == ()
                assert (
                    fs.page_ancestor_chain(facts, site_id=site_id, page_id=ghost_id)
                    == ()
                )
                assert (
                    fs.page_ancestor_chain(facts, site_id=uuid4(), page_id=news_id)
                    == ()
                )

        # --------------------- service-level (common consumer) boundary
        root = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/")
        )
        assert root.route_kind == "page"
        assert root.page.id == home_id
        assert root.page.effective_route == "/"
        # The 056 diff above already proves the RAW route winner for
        # /news/gamma is detail_id on both sides.  This fixture carries
        # NO compositions, so the full renderer's fail-closed contract
        # applies: a {slug} page requires EXACTLY ONE CollectionDetail
        # node.  The genuine valid dynamic positive (route parameters,
        # detail item, RelatedItems, sl values) is the six-binding
        # test's case; this line pins the missing-composition refusal.
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/news/gamma")
            )
        # A well-shaped route with no matching page is the SQL's
        # zero rows: not_found at the service level.
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/dup")
            )
        # The static/dynamic overlap keeps the legacy service outcome:
        # the shared port raises RENDER_ROUTE_AMBIGUOUS and the service
        # maps it to unavailable, exactly as the live fetch's Postgres
        # error would.
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/news/alpha")
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/a..b")
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE content.site_locale_base SET enabled=false "
                "WHERE site_id=$1 AND tag='sl-SI'",
                site_id,
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/sl-si/news")
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/sl-SI/news")
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "UPDATE content.site_locale_base SET enabled=true "
                "WHERE site_id=$1 AND tag='sl-SI'",
                site_id,
            )
        restored = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/sl-si/news")
        )
        assert restored.route_kind == "page"
        assert restored.page.id == news_sl_id
    finally:
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_common_consumer_collection_binding_variants(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """RC2: all six binding variants through the actual common consumer."""
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="par-bindings",
                display_name="Parity Bindings",
                default_locale="en",
            )
        )
        site_id = site.site_id
        home_id, news_id, detail_id = (uuid4() for _ in range(3))
        home_sl_id, news_sl_id, detail_sl_id, list_sl_id = (uuid4() for _ in range(4))
        list_id, grid_id, search_id = (uuid4() for _ in range(3))
        filter_id, related_host_id = (uuid4() for _ in range(2))
        type_id, view_id = uuid4(), uuid4()
        item_ids = {slug: uuid4() for slug in ("alpha", "beta", "gamma")}
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($1,'sl-SI',true,false,1) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            pages = [
                (home_id, "home", None, "en"),
                (news_id, "news", home_id, "en"),
                (detail_id, "detail", news_id, "en"),
                (list_id, "listp", home_id, "en"),
                (grid_id, "gridp", home_id, "en"),
                (search_id, "searchp", home_id, "en"),
                (filter_id, "filterp", home_id, "en"),
                (related_host_id, "relatedp", home_id, "en"),
                # sl-SI page counterparts: page-locale resolution is
                # exact and translation fallback never grants a
                # page-locale fallback, so the localized positives
                # carry their own sl-SI pages.
                (home_sl_id, "home", None, "sl-SI"),
                (news_sl_id, "news", home_sl_id, "sl-SI"),
                (detail_sl_id, "detail", news_sl_id, "sl-SI"),
                (list_sl_id, "listp", home_sl_id, "sl-SI"),
            ]
            for page_id, slug, parent, locale in pages:
                await owner.execute(
                    "INSERT INTO content.page_base "
                    "(id,site_id,slug,title,status,locale,parent_id,"
                    "route_template) VALUES ($1,$2,$3,$4,'PUBLISHED',$5,"
                    "$6,$7)",
                    page_id,
                    site_id,
                    slug,
                    f"Bindings {slug}",
                    locale,
                    parent,
                    "{slug}" if page_id in (detail_id, detail_sl_id) else None,
                )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,definition_"
                "version,settings) VALUES ($1,$2,'bind-news','{}',"
                "'/news/{slug}','ACTIVE',1,'{}')",
                type_id,
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,"
                "cardinality,position,validation,ui_options,definition_"
                "version) VALUES "
                "($1,$2,'title','Title','short_text',true,true,1,0,"
                "'{}','{}',1),"
                "($3,$2,'summary','Summary','long_text',true,true,1,1,"
                "'{}','{}',1),"
                "($4,$2,'rank','Rank','integer',true,false,1,2,'{}',"
                "'{}',1)",
                uuid4(),
                type_id,
                uuid4(),
                uuid4(),
            )
            values = {
                "alpha": {"rank": 1},
                "beta": {"rank": 2},
                "gamma": {"rank": 3},
            }
            for slug, item_id in item_ids.items():
                await owner.execute(
                    "INSERT INTO content.content_item_base "
                    "(id,site_id,type_id,slug,status,type_definition_version,"
                    "values) VALUES ($1,$2,$3,$4,'PUBLISHED',1,$5::jsonb)",
                    item_id,
                    site_id,
                    type_id,
                    slug,
                    json.dumps(values[slug]),
                )
            translations = {
                "alpha": {
                    "en": {"title": "Alpha en", "summary": "Alpha sum en"},
                    "sl-SI": {"title": "Alfa sl", "summary": "Alfa sl povz"},
                },
                "beta": {
                    "en": {"title": "Beta en", "summary": "Beta sum en"},
                    "sl-SI": {"title": "Beta sl", "summary": "Beta sl povz"},
                },
                # gamma deliberately has NO sl-SI translation: the frozen
                # and active surfaces must both fall back to the en value.
                "gamma": {
                    "en": {"title": "Gamma en", "summary": "Gamma sum en"},
                },
            }
            for slug, item_id in item_ids.items():
                for locale, localized in translations[slug].items():
                    await owner.execute(
                        "INSERT INTO content.content_item_translation_base "
                        "(id,site_id,item_id,locale,localized_values) VALUES "
                        "($1,$2,$3,$4,$5::jsonb)",
                        uuid4(),
                        site_id,
                        item_id,
                        locale,
                        json.dumps(localized),
                    )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,"
                "projection_spec,pagination_spec) VALUES ($1,$2,$3,"
                "'bind-news','{}',$4::jsonb,$5::jsonb,$6::jsonb)",
                view_id,
                site_id,
                type_id,
                '{"field":"rank","direction":"asc"}',
                '{"fields":["title","summary","rank"]}',
                '{"limit":10,"offset":0}',
            )
            nodes = [
                (list_id, "CollectionList", 0),
                (grid_id, "CollectionGrid", 0),
                (search_id, "CollectionSearch", 0),
                (filter_id, "CollectionFilter", 0),
                (detail_id, "CollectionDetail", 0),
                (detail_id, "RelatedItems", 1),
                (related_host_id, "CollectionList", 0),
                (list_sl_id, "CollectionList", 0),
                (detail_sl_id, "CollectionDetail", 0),
            ]
            for page_id, component, order in nodes:
                props: dict[str, Any] = {"viewId": str(view_id)}
                if component == "CollectionFilter":
                    # CollectionFilter's bounded props contract requires the
                    # 1..4 facet array; the view's rank field supplies it.
                    props["facets"] = [
                        {"fieldKey": "rank", "operator": "gte", "value": "1"}
                    ]
                await owner.execute(
                    "INSERT INTO content.page_composition_base "
                    "(site_id,page_id,component_type,schema_version,slot_key,"
                    "order_key,props) VALUES ($1,$2,$3,'1','default',$4,"
                    "$5::jsonb)",
                    site_id,
                    page_id,
                    component,
                    order,
                    json.dumps(props),
                )
        adapter = _RenderAdapter(public_pool)
        service = RenderProjectionService(adapter)
        base = "/s/par-bindings"

        def node_id(route_kind_projection: Any, component: str) -> str:
            for node in _walk_nodes(route_kind_projection.composition.nodes):
                if node.component_type == component:
                    return str(node.id)
            raise AssertionError(component)

        def binding_items(binding: Any) -> list[dict[str, Any]]:
            return [dict(item) for item in binding]

        expected_rank_order = ["alpha", "beta", "gamma"]
        list_route = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/listp")
        )
        assert list_route.route_kind == "page"
        list_node = node_id(list_route, "CollectionList")
        list_binding = binding_items(list_route.bindings[list_node])
        assert [item["slug"] for item in list_binding] == expected_rank_order
        assert [item["values"]["title"] for item in list_binding] == [
            "Alpha en",
            "Beta en",
            "Gamma en",
        ]
        assert [item["values"]["rank"] for item in list_binding] == [1, 2, 3]
        assert all(item["id"] == item_ids[item["slug"]] for item in list_binding)

        grid_route = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/gridp")
        )
        assert grid_route.route_kind == "page"
        grid_node = node_id(grid_route, "CollectionGrid")
        grid_binding = binding_items(grid_route.bindings[grid_node])
        assert [item["slug"] for item in grid_binding] == expected_rank_order

        search_route = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/searchp")
        )
        assert search_route.route_kind == "page"
        search_node = node_id(search_route, "CollectionSearch")
        search_binding = binding_items(search_route.bindings[search_node])
        assert [item["slug"] for item in search_binding] == expected_rank_order
        # Field descriptors are ordered by key COLLATE "C" (the
        # exact trusted SELECT), not by write-time position.
        assert search_route.binding_meta[search_node] == {
            "filter_fields": [
                {"key": "rank", "primitive": "integer"},
                {"key": "summary", "primitive": "long_text"},
                {"key": "title", "primitive": "short_text"},
            ]
        }

        filter_route = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/filterp")
        )
        assert filter_route.route_kind == "page"
        filter_node = node_id(filter_route, "CollectionFilter")
        filter_binding = binding_items(filter_route.bindings[filter_node])
        assert [item["slug"] for item in filter_binding] == expected_rank_order
        assert filter_route.binding_meta[filter_node]["filter_fields"][0] == {
            "key": "rank",
            "primitive": "integer",
        }

        detail_route = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/news/alpha")
        )
        assert detail_route.route_kind == "page"
        assert dict(detail_route.route_parameters) == {"slug": "alpha"}
        detail_node = node_id(detail_route, "CollectionDetail")
        detail_binding = binding_items(detail_route.bindings[detail_node])
        assert [item["slug"] for item in detail_binding] == ["alpha"]
        related_node = node_id(detail_route, "RelatedItems")
        related_binding = binding_items(detail_route.bindings[related_node])
        assert [item["slug"] for item in related_binding] == ["beta", "gamma"]

        # A dynamic detail whose slug matches no item fails closed: the
        # production binding contract requires EXACTLY one match.
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/news/missing")
            )

        # Selected-locale values with the default-locale fallback: gamma
        # has no sl-SI translation, so its values stay the en ones.
        sl_list = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/sl-SI/listp")
        )
        assert sl_list.route_kind == "page"
        sl_list_node = node_id(sl_list, "CollectionList")
        sl_binding = binding_items(sl_list.bindings[sl_list_node])
        assert [item["values"]["title"] for item in sl_binding] == [
            "Alfa sl",
            "Beta sl",
            "Gamma en",
        ]
        assert [item["values"]["summary"] for item in sl_binding] == [
            "Alfa sl povz",
            "Beta sl povz",
            "Gamma sum en",
        ]
        sl_detail = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{base}/sl-SI/news/beta")
        )
        assert sl_detail.route_kind == "page"
        sl_detail_node = node_id(sl_detail, "CollectionDetail")
        sl_detail_binding = binding_items(sl_detail.bindings[sl_detail_node])
        assert [item["slug"] for item in sl_detail_binding] == ["beta"]
        assert sl_detail_binding[0]["values"]["title"] == "Beta sl"
    finally:
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_common_port_admitted_work_bounds(
    agent_site_database: AgentSiteDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RC8: measured work bounds on actual admitted requests.

    (1) The admitted maximum group size - 256 items in ONE
    (navigation, locale) group, the strictest group frozen admission
    can ever carry (MAX_NAVIGATION_ITEMS_PER_GROUP) - is projected by
    a REAL RenderProjectionService request while reversible
    instrumentation counts every effective-route derivation and every
    winner selection: each of the 17 pages derives at most ONCE for
    the whole request and the requested route resolves exactly once,
    no matter how many items the group carries.

    (2) The per-group boundary is proven through the real frozen
    admission seam (build_snapshot_document + canonical digest +
    admit_frozen_snapshot): 255 and 256 items in one group are
    admitted, 257 is refused.  Direct helper success over a group
    larger than the admitted maximum is not admitted-work proof.

    (3) The shared memo is bound to its request facts (narrow unit).
    """
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="par-workbounds",
                display_name="Parity Work Bounds",
                default_locale="en",
            )
        )
        site_id = site.site_id
        home_id = uuid4()
        leaf_ids = [uuid4() for _ in range(16)]
        nav_id = uuid4()
        group_size = fs.MAX_NAVIGATION_ITEMS_PER_GROUP
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id) VALUES "
                "($1,$2,'home','Home','PUBLISHED','en',NULL)",
                home_id,
                site_id,
            )
            for index, leaf_id in enumerate(leaf_ids):
                await owner.execute(
                    "INSERT INTO content.page_base "
                    "(id,site_id,slug,title,status,locale,parent_id) VALUES "
                    "($1,$2,$3,$4,'PUBLISHED','en',$5)",
                    leaf_id,
                    site_id,
                    f"leaf{index:02d}",
                    f"Leaf {index}",
                    home_id,
                )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'primary','Primary', $3::jsonb, '{}'::jsonb)",
                nav_id,
                site_id,
                '{"en":"Primary"}',
            )
            # The admitted maximum: 256 INTERNAL items, ONE (navigation,
            # locale) group, cycling the 16 distinct leaf routes.
            for index in range(group_size):
                await owner.execute(
                    "INSERT INTO content.navigation_item_base "
                    "(id,site_id,navigation_id,parent_id,parent_key,"
                    "page_id,target_kind,target_value,labels,locale,"
                    "position) VALUES ($1,$2,$3,NULL,$4::uuid,NULL,"
                    "'INTERNAL',$5,$6::jsonb,NULL,$7)",
                    uuid4(),
                    site_id,
                    nav_id,
                    home_id,
                    f"/leaf{index % 16:02d}",
                    '{"en":"Leaf"}',
                    index,
                )

        # The retained page facts of the seeded site, measured BEFORE
        # the request instrumentation is installed.
        async with public_pool.acquire() as connection:
            probe = fs.DatabaseRenderSurface(connection)
            page_count = len(await probe.fetch_pages(site_id=site_id))
        assert page_count == 17  # home + 16 admitted leaves

        # Reversible instrumentation of the actual shared work seams:
        # (1) every effective-route derivation resolves
        # frozen_source's page_effective_route global; (2) the winner
        # selection resolves projection's imported resolve_page_route
        # name; (3) every static-index / INTERNAL target-count
        # CONSTRUCTION (a cache miss before the call) is counted;
        # (4) the live DB fetches are counted; (5) every successful
        # PULL from the request's facts iterator is counted through a
        # TEST-OWNED counting mapping: a dict subclass wrapping the
        # request's raw facts once at the new_route_memo seam, with the
        # shared leaf helpers that receive (facts, route_memo)
        # translated to that same mapping so the memo's request-
        # identity check keeps passing.  Cache growth or an estimated
        # len(facts) could not show repeated scans (recomputing and
        # overwriting an existing key leaves the cache length
        # unchanged while the scan still runs).  Observed loops - the
        # only facts.values() scans in the shared ports: the static
        # route index build, the INTERNAL target-count build, and the
        # dynamic candidate phase of the winner selection.
        import slaif_agent_site.render_api.projection as projection_module

        derived = {"n": 0}
        resolved = {"n": 0}
        index_builds = {"n": 0}
        count_builds = {"n": 0}
        fetches = {"pages": 0, "navigation_items": 0}
        fact_pulls = {"n": 0}
        facts_by_proxy_id: dict[int, tuple[Any, Any]] = {}
        real_effective = fs.page_effective_route
        real_resolve = fs.resolve_page_route
        real_new_memo = fs.new_route_memo
        real_nav_items = fs.navigation_resolved_items
        real_internal_target = fs._internal_target_exists
        real_static_index = fs._RouteMemo.static_route_index
        real_target_counts = fs._RouteMemo.internal_target_counts
        real_fetch_pages = fs.DatabaseRenderSurface.fetch_pages
        real_fetch_items = fs.DatabaseRenderSurface.fetch_navigation_items

        class _CountingValues:
            """Iterator wrapper counting every successful facts pull."""

            def __init__(self, inner: Any) -> None:
                self._inner = inner

            def __iter__(self) -> _CountingValues:
                return self

            def __next__(self) -> Any:
                item = next(self._inner)  # StopIteration ends the pass
                fact_pulls["n"] += 1  # only successful pulls count
                return item

        class _CountingFacts(dict[Any, Any]):
            """Test-owned facts mapping counting values() pulls."""

            def __init__(self, raw: dict[Any, Any]) -> None:
                super().__init__(raw)

            def values(self) -> Any:
                return _CountingValues(iter(super().values()))

        def tracking_new_memo(facts: Any, *args: Any, **kwargs: Any) -> Any:
            counted = _CountingFacts(facts)
            facts_by_proxy_id[id(counted)] = (counted, facts)
            return real_new_memo(counted, *args, **kwargs)

        def translated_facts(facts: Any, route_memo: Any) -> Any:
            if route_memo is None:
                return facts
            memo_facts = route_memo.facts
            entry = facts_by_proxy_id.get(id(memo_facts))
            if entry is not None and entry[1] is facts:
                # Same request: hand the leaf helper the counting
                # mapping the memo is bound to (identity preserved).
                return memo_facts
            # Foreign facts: pass through so the memo's identity check
            # refuses exactly as production does.
            return facts

        def counting_effective(*args: Any, **kwargs: Any) -> Any:
            derived["n"] += 1
            return real_effective(*args, **kwargs)

        def counting_resolve(facts: Any, *args: Any, **kwargs: Any) -> Any:
            resolved["n"] += 1
            return real_resolve(
                translated_facts(facts, kwargs.get("route_memo")),
                *args,
                **kwargs,
            )

        def counting_nav_items(facts: Any, *args: Any, **kwargs: Any) -> Any:
            return real_nav_items(
                translated_facts(facts, kwargs.get("route_memo")),
                *args,
                **kwargs,
            )

        def counting_internal_target(facts: Any, *args: Any, **kwargs: Any) -> Any:
            return real_internal_target(
                translated_facts(facts, kwargs.get("route_memo")),
                *args,
                **kwargs,
            )

        # Both production memo call sites pass positionally:
        # static_route_index(site_id, locale, status_set) and
        # internal_target_counts(site_id, status_set).
        def counting_static_index(self: Any, *args: Any, **kwargs: Any) -> Any:
            built = (args[0], args[1], args[2]) not in self.static_indexes
            result = real_static_index(self, *args, **kwargs)
            if built:
                index_builds["n"] += 1
            return result

        def counting_target_counts(self: Any, *args: Any, **kwargs: Any) -> Any:
            built = (args[0], args[1]) not in self.target_counts
            result = real_target_counts(self, *args, **kwargs)
            if built:
                count_builds["n"] += 1
            return result

        async def counting_fetch_pages(self: Any, *args: Any, **kwargs: Any) -> Any:
            fetches["pages"] += 1
            return await real_fetch_pages(self, *args, **kwargs)

        async def counting_fetch_items(self: Any, *args: Any, **kwargs: Any) -> Any:
            fetches["navigation_items"] += 1
            return await real_fetch_items(self, *args, **kwargs)

        monkeypatch.setattr(fs, "page_effective_route", counting_effective)
        monkeypatch.setattr(projection_module, "resolve_page_route", counting_resolve)
        monkeypatch.setattr(projection_module, "new_route_memo", tracking_new_memo)
        monkeypatch.setattr(
            projection_module, "navigation_resolved_items", counting_nav_items
        )
        monkeypatch.setattr(fs, "_internal_target_exists", counting_internal_target)
        monkeypatch.setattr(fs._RouteMemo, "static_route_index", counting_static_index)
        monkeypatch.setattr(
            fs._RouteMemo, "internal_target_counts", counting_target_counts
        )
        monkeypatch.setattr(
            fs.DatabaseRenderSurface, "fetch_pages", counting_fetch_pages
        )
        monkeypatch.setattr(
            fs.DatabaseRenderSurface,
            "fetch_navigation_items",
            counting_fetch_items,
        )

        adapter = _RenderAdapter(public_pool)
        service = RenderProjectionService(adapter)
        projection = await service.canonical(
            RenderPageRequest(authority="localhost", path="/s/par-workbounds/leaf03")
        )
        assert projection.route_kind == "page"
        assert projection.page.id == leaf_ids[3]
        all_items = [item for nav in projection.navigation for item in nav.items]
        assert len(all_items) == group_size
        assert {item.target.value for item in all_items} == {
            f"/leaf{i:02d}" for i in range(16)
        }
        # Measured across the WHOLE request (route + 256-item group +
        # ancestors + locale/region work): page-bounded derivations and
        # exactly one winner selection.
        assert derived["n"] <= 17
        assert resolved["n"] == 1
        # Measured CONSTRUCTIONS (a cache miss before the call): each
        # index is built exactly once over the whole 256-item request,
        # never per item.
        assert index_builds["n"] == 1
        assert count_builds["n"] == 1
        # Measured FACT PULLS: the compliant request walks the 17
        # retained facts exactly three times - one static-index build,
        # one dynamic-phase winner scan, one target-count build.  A
        # per-item rescan by the 256-item group would multiply the
        # pulls by the item count (the isolated counterexample measures
        # 51 -> 4386 when target-count cache misses are forced), so
        # this page-bounded assertion detects that regression.
        assert fact_pulls["n"] == 3 * page_count
        # The DB work is page-bounded too: one page fetch and one
        # navigation fetch carry the whole 256-item group.
        assert fetches["pages"] == 1
        assert fetches["navigation_items"] == 1

        # Counterexample sensitivity (framework non-vacuity): the
        # page-bounded fact-pull bound above MUST detect a per-item
        # rescan regression.  Force the exact condition the isolated
        # pure probe measured (51 -> 4386 pulls when target-count
        # cache misses are forced): leak the INTERNAL target-count
        # cache entry after EVERY construction so each of the 256
        # item lookups re-walks all 17 retained facts, while the
        # static route index and the single winner scan keep their
        # caches.  The same counting mapping is still installed, so
        # the forced request must violate the compliant bound by
        # exactly the (group_size - 1) additional per-item rescans.
        def leaking_target_counts(self: Any, *args: Any, **kwargs: Any) -> Any:
            result = real_target_counts(self, *args, **kwargs)
            self.target_counts.pop((args[0], args[1]), None)
            return result

        monkeypatch.setattr(
            fs._RouteMemo, "internal_target_counts", leaking_target_counts
        )
        fact_pulls["n"] = 0
        forced_projection = await service.canonical(
            RenderPageRequest(authority="localhost", path="/s/par-workbounds/leaf03")
        )
        assert forced_projection.route_kind == "page"
        assert forced_projection.page.id == leaf_ids[3]
        # The regression is REAL and measured, not estimated: one
        # static-index build + one winner scan + 256 per-item
        # target-count rebuilds over the 17 facts (4386 pulls).
        assert fact_pulls["n"] == (2 + group_size) * page_count
        # Sensitivity: the compliant page-bounded bound from above is
        # violated by the forced rescan - the work assertion detects
        # the regression instead of passing silently.
        assert fact_pulls["n"] != 3 * page_count
        assert fact_pulls["n"] > 3 * page_count

        # The per-group boundary through the real frozen admission
        # seam, with a document whose only variable is the group size.
        doc_now = "2026-10-18T12:00:00+00:00"
        workspace_id = uuid4()
        snapshot_id = uuid4()
        zero_uuid = "00000000-0000-0000-0000-000000000000"

        def admission_document(item_count: int) -> dict[str, Any]:
            return {
                "state_version": STATE_VERSION,
                "workspace_id": str(workspace_id),
                "site_id": str(site_id),
                "site": {
                    "site_key": "par-workbounds",
                    "display_name": "Parity Work Bounds",
                    "status": "ACTIVE",
                    "default_locale": "en",
                    "component_catalog_version": "catalog-v1",
                    "content_model_revision": 3,
                    "created_at": doc_now,
                    "updated_at": doc_now,
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
                        "id": str(uuid4()),
                        "site_id": str(site_id),
                        "tag": "en",
                        "enabled": True,
                        "is_default": True,
                        "position": 0,
                        "metadata": {},
                        "row_version": 1,
                        "created_at": doc_now,
                        "updated_at": doc_now,
                    }
                ],
                "theme": None,
                "regions": [],
                "navigation": {
                    "definitions": [
                        {
                            "id": str(nav_id),
                            "site_id": str(site_id),
                            "key": "primary",
                            "label": "Primary",
                            "labels": {"en": "Primary"},
                            "settings": {},
                            "row_version": 1,
                            "created_at": doc_now,
                            "updated_at": doc_now,
                        }
                    ],
                    "items": [
                        {
                            "id": str(uuid4()),
                            "site_id": str(site_id),
                            "navigation_id": str(nav_id),
                            "parent_id": None,
                            "parent_key": zero_uuid,
                            "page_id": None,
                            "target_kind": "INTERNAL",
                            "target_value": "/",
                            "labels": {"en": "Home"},
                            "locale": None,
                            "position": index,
                            "row_version": 1,
                            "created_at": doc_now,
                            "updated_at": doc_now,
                        }
                        for index in range(item_count)
                    ],
                },
                "redirects": [],
                "pages": [
                    {
                        "id": str(home_id),
                        "site_id": str(site_id),
                        "slug": "home",
                        "title": "Home",
                        "status": "PUBLISHED",
                        "locale": "en",
                        "parent_id": None,
                        "route_template": None,
                        "effective_route": "/",
                        "row_version": 1,
                        "created_at": doc_now,
                        "updated_at": doc_now,
                        "deleted_at": None,
                        "style_overrides": {},
                        "style": None,
                        "nodes": [],
                    }
                ],
                "page_compositions": [],
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

        def sealed_row(doc: dict[str, Any]) -> dict[str, Any]:
            row = dict(build_snapshot_document(doc, created_by="slaif_review_worker"))
            row["workspace_id"] = str(workspace_id)
            row["site_id"] = str(site_id)
            row["id"] = str(snapshot_id)
            row["created_at"] = doc_now
            row["digest"] = canonical_digest(row["payload"])
            return row

        for count in (group_size - 1, group_size):
            fs.admit_frozen_snapshot(
                sealed_row(admission_document(count)),
                expected_snapshot_id=snapshot_id,
                expected_site_id=site_id,
                expected_workspace_id=workspace_id,
            )
        with pytest.raises(fs.SurfaceReadError) as overflow:
            fs.admit_frozen_snapshot(
                sealed_row(admission_document(group_size + 1)),
                expected_snapshot_id=snapshot_id,
                expected_site_id=site_id,
                expected_workspace_id=workspace_id,
            )
        assert overflow.value.reason == "not_found"

        # The shared memo is bound to its request facts (narrow unit).
        async with public_pool.acquire() as connection:
            surface = fs.DatabaseRenderSurface(connection)
            facts = {
                fact.id: fact for fact in await surface.fetch_pages(site_id=site_id)
            }
        memo = fs.new_route_memo(
            facts,
            default_locale="en",
            enabled_tags=frozenset({"en"}),
        )
        with pytest.raises(ValueError, match="different request"):
            fs.navigation_resolved_items(
                dict(facts),
                frozenset({"en"}),
                (),
                site_id=site_id,
                locale="en",
                default_locale="en",
                statuses=RESOLVED,
                route_memo=memo,
            )
    finally:
        await public_pool.close()
        await control_pool.close()


def _caps_payload(**overrides: Any) -> dict[str, Any]:
    """A minimal payload carrying every family
    ``fs._check_family_caps`` indexes (the cap gate reads lengths and
    grouping keys only, never row shapes)."""
    payload: dict[str, Any] = {
        "pages": [],
        "page_compositions": [],
        "locales": [],
        "regions": [],
        "navigation": {"definitions": [], "items": []},
        "redirects": [],
        "media_inventory": [],
        "proposals": [],
        "media": {},
        "content": {
            "types": [],
            "fields": [],
            "items": [],
            "translations": [],
            "relations": [],
            "views": [],
        },
    }
    for family, value in overrides.items():
        if family == "navigation":
            payload["navigation"].update(value)
        elif family == "content":
            payload["content"].update(value)
        else:
            payload[family] = value
    return payload


def _caps_refusal(payload: dict[str, Any]) -> None:
    with pytest.raises(fs.SurfaceReadError) as excinfo:
        fs._check_family_caps(payload)
    assert excinfo.value.reason == "not_found"


def test_family_cap_gate_refuses_before_group_allocation() -> None:
    """RC8: the cap GATE itself refuses at the first excess, before an
    unbounded group dict from foreign parent ids can be allocated
    (pure, no DB).  Each refusal vector is the minimal input the old
    ordering fully walked or allocated without refusing; each valid
    maximum must still pass the same gate.  This is gate-level
    regression proof only - the admitted-work qualification stays with
    the real request instrumentation above.
    """
    # -- distinct-group gates ---------------------------------------
    # 65 fields carrying 65 distinct foreign type_ids: the pre-repair
    # checker built all 65 groups and returned WITHOUT refusal.
    _caps_refusal(
        _caps_payload(
            content={
                "fields": [{"type_id": index} for index in range(65)],
            }
        )
    )
    # 4097 compositions carrying 4097 distinct foreign page_ids: the
    # 4097th distinct group is the first excess.
    _caps_refusal(
        _caps_payload(
            page_compositions=[{"page_id": index} for index in range(4097)],
        )
    )
    # 513 distinct (navigation, locale) item groups: limit 16 x 32.
    _caps_refusal(
        _caps_payload(
            navigation={
                "items": [
                    {"navigation_id": index % 16, "locale": index // 16}
                    for index in range(513)
                ]
            }
        )
    )
    # -- per-group / per-pair gates ---------------------------------
    _caps_refusal(
        _caps_payload(
            page_compositions=[{"page_id": 0} for _ in range(129)],
        )
    )
    _caps_refusal(
        _caps_payload(
            navigation={
                "items": [{"navigation_id": 0, "locale": 0} for _ in range(257)]
            }
        )
    )
    _caps_refusal(
        _caps_payload(
            content={
                "relations": [
                    {"source_item_id": 0, "field_definition_id": 0} for _ in range(1001)
                ]
            }
        )
    )
    # -- aggregate length gates (INDEPENDENT negatives: each alone, so
    # one gate can never mask another) --------------------------------
    _caps_refusal(_caps_payload(pages=list(range(4097))))
    _caps_refusal(_caps_payload(content={"fields": [{"type_id": 0}] * 4097}))
    _caps_refusal(_caps_payload(media={index: object() for index in range(4097)}))
    _caps_refusal(_caps_payload(media_inventory=list(range(4097))))
    # The relation length gate (076 relations cost share 262144, object
    # branch charges at least 2 per row): the 131073rd row must refuse
    # at the length cap, before any per-pair allocation exists.
    _caps_refusal(
        _caps_payload(
            content={
                "relations": [
                    {"source_item_id": index, "field_definition_id": 0}
                    for index in range(131073)
                ]
            }
        )
    )
    # -- valid maxima still pass --------------------------------------
    fs._check_family_caps(
        _caps_payload(
            pages=list(range(4096)),
            page_compositions=[{"page_id": 0} for _ in range(128)],
            navigation={
                "items": [{"navigation_id": 0, "locale": 0} for _ in range(256)]
            },
            media={index: object() for index in range(4096)},
            media_inventory=list(range(4096)),
            content={
                "fields": [
                    {"type_id": type_id} for type_id in range(64) for _ in range(64)
                ],
                "relations": [
                    {"source_item_id": index, "field_definition_id": 0}
                    for index in range(131072)
                ],
            },
        )
    )


class _ObservedMediaDescriptor(dict[str, Any]):
    """A test-owned media descriptor counting the admission walk's
    ``descriptor.get(...)`` pulls: every entry the media walk visits
    calls ``get("id")`` at least once, and nothing before the walk
    (the O(1) caps, the bounded walkers, the shape checks) calls
    ``get`` on a media descriptor, so a zero count proves the cap
    gate refused before ANY entry was visited.  Under the pre-repair
    ordering the same input pulled all 4097 entries first."""

    def __init__(self, counter: list[int], **values: Any) -> None:
        super().__init__(**values)
        self._counter = counter

    def get(self, key: Any, default: Any = None) -> Any:
        self._counter[0] += 1
        return super().get(key, default)


def _media_ordering_document(media: dict[str, Any]) -> dict[str, Any]:
    """A genuine minimal v2 document (the builder's exact input shape),
    carrying the caller's media map and nothing else unusual."""
    workspace_id = uuid4()
    site_id = uuid4()
    now = "2026-10-18T12:00:00+00:00"
    zero_uuid = "00000000-0000-0000-0000-000000000000"
    home_id = uuid4()
    nav_id = uuid4()
    return {
        "state_version": STATE_VERSION,
        "workspace_id": str(workspace_id),
        "site_id": str(site_id),
        "site": {
            "site_key": "par-mediaorder",
            "display_name": "Parity Media Ordering",
            "status": "ACTIVE",
            "default_locale": "en",
            "component_catalog_version": "catalog-v1",
            "content_model_revision": 3,
            "created_at": now,
            "updated_at": now,
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
                "id": str(uuid4()),
                "site_id": str(site_id),
                "tag": "en",
                "enabled": True,
                "is_default": True,
                "position": 0,
                "metadata": {},
                "row_version": 1,
                "created_at": now,
                "updated_at": now,
            }
        ],
        "theme": None,
        "regions": [],
        "navigation": {
            "definitions": [
                {
                    "id": str(nav_id),
                    "site_id": str(site_id),
                    "key": "primary",
                    "label": "Primary",
                    "labels": {"en": "Primary"},
                    "settings": {},
                    "row_version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
            "items": [
                {
                    "id": str(uuid4()),
                    "site_id": str(site_id),
                    "navigation_id": str(nav_id),
                    "parent_id": None,
                    "parent_key": zero_uuid,
                    "page_id": None,
                    "target_kind": "INTERNAL",
                    "target_value": "/",
                    "labels": {"en": "Home"},
                    "locale": None,
                    "position": 0,
                    "row_version": 1,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        },
        "redirects": [],
        "pages": [
            {
                "id": str(home_id),
                "site_id": str(site_id),
                "slug": "home",
                "title": "Home",
                "status": "PUBLISHED",
                "locale": "en",
                "parent_id": None,
                "route_template": None,
                "effective_route": "/",
                "row_version": 1,
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
                "style_overrides": {},
                "style": None,
                "nodes": [],
            }
        ],
        "page_compositions": [],
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
        "media": media,
    }


def _sealed_media_row(doc: dict[str, Any]) -> tuple[dict[str, Any], UUID, UUID, UUID]:
    """Seal the builder's row into the exact 14-column admission shape
    (id + created_at are the only row fields the builder does not emit);
    returns the row plus the bound identities."""
    row = dict(build_snapshot_document(doc, created_by="slaif_review_worker"))
    row["id"] = str(uuid4())
    row["created_at"] = "2026-10-18T12:00:00+00:00"
    return (
        row,
        UUID(row["id"]),
        UUID(row["site_id"]),
        UUID(row["workspace_id"]),
    )


def test_media_cross_check_runs_after_cap_gate() -> None:
    """RC8: the allocation-heavy media cross-check of
    ``admit_frozen_snapshot`` runs AFTER the O(1) caps, so a 4097-entry
    media map (one past MAX_MEDIA_INVENTORY) refuses at the cap gate
    with ZERO observed entry visits - matching the root counterexample
    probe, which observed all 4097 entries under the pre-repair
    ordering.  Pure, no DB; a direct ``_check_family_caps`` call could
    not catch a regression moving the media walk back before the caps,
    so this goes through the REAL admission seam.
    """

    # Well-formed descriptor bodies (exactly the admitted key set), so
    # under the pre-repair ordering the walk would complete all 4097
    # entries and only then reach the stable cap refusal.
    def media_entry(index: int, observed_counter: list[int] | None) -> dict[str, Any]:
        media_id = str(UUID(int=index))
        values = {
            "id": media_id,
            "mime_type": "image/png",
            "size_bytes": 1,
            "content_hash": "0" * 64,
            "public_status": "PRIVATE",
        }
        if observed_counter is None:
            return values
        return _ObservedMediaDescriptor(observed_counter, **values)

    # (1) Genuine-builder POSITIVE control: the baseline (2 media
    # entries) is fully admitted through the real admission seam.
    baseline_row, snapshot_id, site_id, workspace_id = _sealed_media_row(
        _media_ordering_document(
            {str(UUID(int=i)): media_entry(i, None) for i in range(2)}
        )
    )
    payload, _site_profile = fs.admit_frozen_snapshot(
        baseline_row,
        expected_snapshot_id=snapshot_id,
        expected_site_id=site_id,
        expected_workspace_id=workspace_id,
    )
    assert len(payload["media"]) == 2

    # (2) The 4097-entry observed media map through the SAME real
    # admission: refused at the MAX_MEDIA_INVENTORY cap gate with ZERO
    # observed pulls.  The digest is recomputed over the injected
    # payload so the row is self-consistent and the refusal is
    # attributable to the cap gate, not a digest mismatch.
    oversized_row, oversized_id, oversized_site, oversized_ws = _sealed_media_row(
        _media_ordering_document(
            {str(UUID(int=i)): media_entry(i, None) for i in range(2)}
        )
    )
    counter: list[int] = [0]
    observed_map: dict[str, Any] = {
        str(UUID(int=index)): media_entry(index, counter) for index in range(4097)
    }
    oversized_row["payload"]["media"] = observed_map
    oversized_row["media_references"] = [
        {
            "id": str(UUID(int=index)),
            "mime_type": "image/png",
            "size_bytes": 1,
            "content_hash": "0" * 64,
            "public_status": "PRIVATE",
        }
        for index in range(4097)
    ]
    oversized_row["digest"] = canonical_digest(oversized_row["payload"])
    with pytest.raises(fs.SurfaceReadError) as excinfo:
        fs.admit_frozen_snapshot(
            oversized_row,
            expected_snapshot_id=oversized_id,
            expected_site_id=oversized_site,
            expected_workspace_id=oversized_ws,
        )
    assert excinfo.value.reason == "not_found"
    # ZERO visited: the cap gate refused before the media walk pulled a
    # single entry (pre-repair ordering: 4097 observed pulls).
    assert counter[0] == 0


async def test_omission_stub_counterfactuals(
    agent_site_database: AgentSiteDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RC5: finite semantic counterfactuals for the actual common consumer.

    Each required item of the live frozen-read contract is omitted or
    stubbed through a REVERSIBLE seam (disposable-fixture row
    mutation with exact restore, or a monkeypatched common-port
    function), and the corresponding positive fact is re-derived to
    show it FAILS for the intended reason: a stable fail-closed
    ProjectionError code where the contract refuses, or the exact
    changed value where the contract legitimately degrades.  After
    every restore the original positive facts are re-derived and must
    be byte-identical (no contamination of later cases or tests; the
    fixture database is disposable per test and monkeypatch restores
    code seams at teardown).  The admitted/number unit vectors remain
    the admission-side boundary proof; this is the semantic
    counterfactual set the order requires, executed against the REAL
    PostgreSQL-backed common consumer.
    Case 9 seals the fully restored retained state through the
    REAL trusted materializer into a review-snapshot/v2 document,
    admits it through the shared frozen admission seam and
    re-proves every counterfactual against the frozen common
    consumer: item/translation/version/binding omissions, the
    retained-relation positive/omission/dangling triple, the
    stubbed winner selection and the frozen raw/resolved style
    revert.
    """
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="par-omission",
                display_name="Parity Omission",
                default_locale="en",
            )
        )
        site_id = site.site_id
        home_id, news_id, detail_id, list_id = (uuid4() for _ in range(4))
        home_sl_id, news_sl_id, list_sl_id = (uuid4() for _ in range(3))
        type_id, view_id = uuid4(), uuid4()
        field_ids = {key: uuid4() for key in ("title", "summary", "rank")}
        item_ids = {slug: uuid4() for slug in ("alpha", "beta", "gamma")}
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($1,'sl-SI',true,false,1) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            # Exact proven hierarchy (the dynamic host is a child of the
            # list-level page, so its template route is /news/{slug},
            # never a root-level dynamic overlap):
            #   en:     home -> news -> detail({slug}), home -> listp
            #   sl-SI:  home -> news, home -> listp (NO detail
            #   counterpart: the fail-closed locale bound in case 8).
            for page_id, slug, parent, locale, template in (
                (home_id, "home", None, "en", None),
                (news_id, "news", home_id, "en", None),
                (detail_id, "detail", news_id, "en", "{slug}"),
                (list_id, "listp", home_id, "en", None),
                (home_sl_id, "home", None, "sl-SI", None),
                (news_sl_id, "news", home_sl_id, "sl-SI", None),
                (list_sl_id, "listp", home_sl_id, "sl-SI", None),
            ):
                await owner.execute(
                    "INSERT INTO content.page_base "
                    "(id,site_id,slug,title,status,locale,parent_id,"
                    "route_template) VALUES ($1,$2,$3,$4,'PUBLISHED',$5,"
                    "$6,$7)",
                    page_id,
                    site_id,
                    slug,
                    f"Omit {slug}",
                    locale,
                    parent,
                    template,
                )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,definition_"
                "version,settings) VALUES ($1,$2,'omit-news','{}',"
                "'/news/{slug}','ACTIVE',1,'{}')",
                type_id,
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,"
                "cardinality,position,validation,ui_options,definition_"
                "version) VALUES "
                "($1,$2,'title','Title','short_text',true,true,1,0,"
                "'{}','{}',1),"
                "($3,$2,'summary','Summary','long_text',true,true,1,1,"
                "'{}','{}',1),"
                "($4,$2,'rank','Rank','integer',true,false,1,2,'{}',"
                "'{}',1)",
                field_ids["title"],
                type_id,
                field_ids["summary"],
                field_ids["rank"],
            )
            # A real reference-type field (its reference
            # validation targets the type itself).  The relation
            # row is created below, after the items exist: the
            # product function resolves source and target
            # through the live item view and refuses a dangling
            # reference.
            related_field_id = uuid4()
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,"
                "cardinality,position,validation,ui_options,definition_"
                "version) VALUES "
                "($1,$2,'related','Related','reference',false,false,1,3,"
                "$3,'{}',1)",
                related_field_id,
                type_id,
                json.dumps({"target_type_id": str(type_id)}),
            )
            values = {"alpha": {"rank": 1}, "beta": {"rank": 2}, "gamma": {"rank": 3}}
            for slug, item_id in item_ids.items():
                await owner.execute(
                    "INSERT INTO content.content_item_base "
                    "(id,site_id,type_id,slug,status,type_definition_version,"
                    "values) VALUES ($1,$2,$3,$4,'PUBLISHED',1,$5::jsonb)",
                    item_id,
                    site_id,
                    type_id,
                    slug,
                    json.dumps(values[slug]),
                )
            # ONE retained relation fact (alpha -> beta through
            # the reference field), seeded into the COW base
            # exactly like every other fixture family (trusted
            # fixture setup, NOT a product write): a valid
            # canonical row per the product's reference rules -
            # reference field, target of the same content type,
            # position 0, object metadata.  The frozen-admission
            # reference validation (case 9c) proves the family is
            # binding-checked, and the common consumer never
            # projects it (no relation-query semantics are
            # asserted).  RC1's actual public Agent AND human
            # Editor relation writes remain separately due in
            # their own scope.
            relation_id = uuid4()
            await owner.execute(
                "INSERT INTO content.item_relation_base "
                "(id, site_id, source_item_id, field_definition_id,"
                " target_item_id, position, metadata) VALUES "
                "($1,$2,$3,$4,$5,0,'{}'::jsonb)",
                relation_id,
                site_id,
                item_ids["alpha"],
                related_field_id,
                item_ids["beta"],
            )
            relation_row = await owner.fetchrow(
                "SELECT * FROM content.item_relation_base WHERE id = $1",
                relation_id,
            )
            assert relation_row is not None
            assert relation_row["source_item_id"] == item_ids["alpha"]
            assert relation_row["target_item_id"] == item_ids["beta"]
            assert relation_row["field_definition_id"] == related_field_id
            translations = {
                "alpha": {
                    "en": {"title": "Alpha en", "summary": "Alpha sum en"},
                    "sl-SI": {"title": "Alfa sl", "summary": "Alfa sl povz"},
                },
                "beta": {
                    "en": {"title": "Beta en", "summary": "Beta sum en"},
                    "sl-SI": {"title": "Beta sl", "summary": "Beta sl povz"},
                },
                "gamma": {
                    "en": {"title": "Gamma en", "summary": "Gamma sum en"},
                },
            }
            for slug, item_id in item_ids.items():
                for locale, localized in translations[slug].items():
                    await owner.execute(
                        "INSERT INTO content.content_item_translation_base "
                        "(id,site_id,item_id,locale,localized_values) VALUES "
                        "($1,$2,$3,$4,$5::jsonb)",
                        uuid4(),
                        site_id,
                        item_id,
                        locale,
                        json.dumps(localized),
                    )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,"
                "projection_spec,pagination_spec) VALUES ($1,$2,$3,"
                "'omit-news','{}',$4::jsonb,$5::jsonb,$6::jsonb)",
                view_id,
                site_id,
                type_id,
                '{"field":"rank","direction":"asc"}',
                '{"fields":["title","summary","rank"]}',
                '{"limit":10,"offset":0}',
            )
            for page_id, component, order in (
                (list_id, "CollectionList", 0),
                (list_sl_id, "CollectionList", 0),
                (detail_id, "CollectionDetail", 0),
                (detail_id, "RelatedItems", 1),
            ):
                await owner.execute(
                    "INSERT INTO content.page_composition_base "
                    "(site_id,page_id,component_type,schema_version,slot_key,"
                    "order_key,props) VALUES ($1,$2,$3,'1','default',$4,"
                    "$5::jsonb)",
                    site_id,
                    page_id,
                    component,
                    order,
                    json.dumps({"viewId": str(view_id)}),
                )

        adapter = _RenderAdapter(public_pool)
        service = RenderProjectionService(adapter)
        base = "/s/par-omission"

        def node_id(projection: Any, component: str) -> str:
            for node in _walk_nodes(projection.composition.nodes):
                if node.component_type == component:
                    return str(node.id)
            raise AssertionError(component)

        def binding_items(projection: Any, component: str) -> list[dict[str, Any]]:
            return [
                dict(item)
                for item in projection.bindings[node_id(projection, component)]
            ]

        async def list_projection() -> Any:
            return await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/listp")
            )

        async def sl_projection() -> Any:
            return await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/sl-SI/listp")
            )

        async def detail_projection() -> Any:
            return await service.canonical(
                RenderPageRequest(authority="localhost", path=f"{base}/news/alpha")
            )

        async def capture_positives() -> dict[str, Any]:
            lp = await list_projection()
            sp = await sl_projection()
            dp = await detail_projection()
            return {
                "list_slugs": [i["slug"] for i in binding_items(lp, "CollectionList")],
                "list_ranks": [
                    i["values"]["rank"] for i in binding_items(lp, "CollectionList")
                ],
                "sl_titles": [
                    i["values"]["title"] for i in binding_items(sp, "CollectionList")
                ],
                "detail_page": str(dp.page.id),
                "detail_params": dict(dp.route_parameters),
                "related": [i["slug"] for i in binding_items(dp, "RelatedItems")],
                "page_style": lp.page_style,
            }

        def sl_titles_positive(positives: dict[str, Any]) -> None:
            # The original selected-locale positive fact, reused
            # unchanged by the case 9b frozen counterfactual as
            # its oracle (baseline PASS, omitted-copy intended
            # FAIL, restored PASS).
            assert positives["sl_titles"] == ["Alfa sl", "Beta sl", "Gamma en"]

        pos = await capture_positives()
        assert pos["list_slugs"] == ["alpha", "beta", "gamma"]
        assert pos["list_ranks"] == [1, 2, 3]
        sl_titles_positive(pos)
        assert pos["detail_page"] == str(detail_id)
        assert pos["detail_params"] == {"slug": "alpha"}
        assert pos["related"] == ["beta", "gamma"]
        assert pos["page_style"].layout.content_width

        # (1) item field omission: the REQUIRED rank value disappears
        # from beta's values; the common consumer must fail closed on
        # the invalid stored values, not silently reorder.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base SET values = values - 'rank' "
                "WHERE id = $1",
                item_ids["beta"],
            )
        with pytest.raises(ProjectionError) as rank_omitted:
            await list_projection()
        assert rank_omitted.value.reason == "malformed_item"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base SET values = "
                "values || '{\"rank\":2}'::jsonb WHERE id = $1",
                item_ids["beta"],
            )
        assert await capture_positives() == pos

        # (2) translation omission: beta's sl-SI translation row is
        # removed; the selected-locale positive must degrade EXACTLY to
        # the default-locale fallback value (no error, changed value).
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # Capture the EXACT original row (id + values) before
            # the omission so the restore is verifiable.
            beta_sl_row = await owner.fetchrow(
                "SELECT id, localized_values FROM "
                "content.content_item_translation_base "
                "WHERE item_id = $1 AND locale = 'sl-SI'",
                item_ids["beta"],
            )
            await owner.execute(
                "DELETE FROM content.content_item_translation_base "
                "WHERE item_id = $1 AND locale = 'sl-SI'",
                item_ids["beta"],
            )
        sl_degraded = await sl_projection()
        assert [
            i["values"]["title"] for i in binding_items(sl_degraded, "CollectionList")
        ] == ["Alfa sl", "Beta en", "Gamma en"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # EXACT restore: the original row id and the original
            # localized_values, then verify the restored row.
            await owner.execute(
                "INSERT INTO content.content_item_translation_base "
                "(id,site_id,item_id,locale,localized_values) VALUES "
                "($1,$2,$3,'sl-SI',$4::jsonb)",
                beta_sl_row["id"],
                site_id,
                item_ids["beta"],
                _jsonb_text(beta_sl_row["localized_values"]),
            )
            restored_sl = await owner.fetchrow(
                "SELECT localized_values FROM content.content_item_translation_base "
                "WHERE id = $1",
                beta_sl_row["id"],
            )
        assert restored_sl["localized_values"] == beta_sl_row["localized_values"]
        assert await capture_positives() == pos

        # (3) view spec corruption: the sort spec references a field
        # that has no definition; the shared query-contract validation
        # must refuse the whole binding.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.collection_view_base SET sort_spec = "
                '\'{"field":"nonexistent","direction":"asc"}\'::jsonb '
                "WHERE id = $1",
                view_id,
            )
        with pytest.raises(ProjectionError) as view_corrupted:
            await list_projection()
        assert view_corrupted.value.reason == "unsupported_collection_query"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.collection_view_base SET sort_spec = "
                '\'{"field":"rank","direction":"asc"}\'::jsonb '
                "WHERE id = $1",
                view_id,
            )
        assert await capture_positives() == pos

        # (4) collection-item omission: the related items (beta,
        # gamma) no longer exist; the RelatedItems positive must
        # become EMPTY while the detail binding itself still
        # resolves alpha.  RelatedItems here is a COLLECTION
        # query (collection-query evidence, NOT relation-family
        # proof; the retained item_relation fact is proven in
        # case 4b and by the frozen counterfactual set at the
        # end of this test).  The live schema keeps the relation
        # referentially closed, so the retained row is removed
        # first and restored with its EXACT id and values below.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # Capture the EXACT original translation rows (ids +
            # values) so the restore is verifiable row for row.
            case4_rows = await owner.fetch(
                "SELECT id, item_id, locale, localized_values FROM "
                "content.content_item_translation_base "
                "WHERE item_id IN ($1, $2)",
                item_ids["beta"],
                item_ids["gamma"],
            )
            # Remove the retained relation row first: the live
            # schema refuses to delete an item that a relation
            # still references (relation_target_fk).
            await owner.execute(
                "DELETE FROM content.item_relation_base WHERE id = $1",
                relation_row["id"],
            )
            await owner.execute(
                "DELETE FROM content.content_item_translation_base "
                "WHERE item_id IN ($1, $2)",
                item_ids["beta"],
                item_ids["gamma"],
            )
            await owner.execute(
                "DELETE FROM content.content_item_base WHERE id IN ($1, $2)",
                item_ids["beta"],
                item_ids["gamma"],
            )
        detail_orphaned = await detail_projection()
        assert [
            i["slug"] for i in binding_items(detail_orphaned, "CollectionDetail")
        ] == ["alpha"]
        assert binding_items(detail_orphaned, "RelatedItems") == []
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            for slug, item_id in (
                ("beta", item_ids["beta"]),
                ("gamma", item_ids["gamma"]),
            ):
                await owner.execute(
                    "INSERT INTO content.content_item_base "
                    "(id,site_id,type_id,slug,status,type_definition_version,"
                    "values) VALUES ($1,$2,$3,$4,'PUBLISHED',1,$5::jsonb)",
                    item_id,
                    site_id,
                    type_id,
                    slug,
                    json.dumps(values[slug]),
                )
            # EXACT restore: the original translation row ids and
            # localized_values, then verify row for row.
            for row in case4_rows:
                await owner.execute(
                    "INSERT INTO content.content_item_translation_base "
                    "(id,site_id,item_id,locale,localized_values) VALUES "
                    "($1,$2,$3,$4,$5::jsonb)",
                    row["id"],
                    site_id,
                    row["item_id"],
                    row["locale"],
                    _jsonb_text(row["localized_values"]),
                )
            # EXACT restore of the retained relation row: same id,
            # same referential values, same COW bookkeeping.
            await owner.execute(
                "INSERT INTO content.item_relation_base "
                "(id,site_id,source_item_id,field_definition_id,"
                "target_item_id,position,metadata,row_version,"
                "created_at,updated_at) VALUES "
                "($1,$2,$3,$4,$5,$6,$7::jsonb,$8,$9,$10)",
                relation_row["id"],
                relation_row["site_id"],
                relation_row["source_item_id"],
                relation_row["field_definition_id"],
                relation_row["target_item_id"],
                relation_row["position"],
                _jsonb_text(relation_row["metadata"]),
                relation_row["row_version"],
                relation_row["created_at"],
                relation_row["updated_at"],
            )
            restored_rows = await owner.fetch(
                "SELECT id, item_id, locale, localized_values FROM "
                "content.content_item_translation_base "
                "WHERE item_id IN ($1, $2)",
                item_ids["beta"],
                item_ids["gamma"],
            )
            restored_relation = await owner.fetchrow(
                "SELECT id, site_id, source_item_id, field_definition_id, "
                "target_item_id, position, metadata, row_version, "
                "created_at, updated_at FROM content.item_relation_base "
                "WHERE id = $1",
                relation_row["id"],
            )
        assert [
            (r["id"], r["item_id"], r["locale"], r["localized_values"])
            for r in sorted(restored_rows, key=lambda r: str(r["id"]))
        ] == [
            (r["id"], r["item_id"], r["locale"], r["localized_values"])
            for r in sorted(case4_rows, key=lambda r: str(r["id"]))
        ]
        assert (
            restored_relation["id"],
            restored_relation["site_id"],
            restored_relation["source_item_id"],
            restored_relation["field_definition_id"],
            restored_relation["target_item_id"],
            restored_relation["position"],
            restored_relation["metadata"],
            restored_relation["row_version"],
            restored_relation["created_at"],
            restored_relation["updated_at"],
        ) == (
            relation_row["id"],
            relation_row["site_id"],
            relation_row["source_item_id"],
            relation_row["field_definition_id"],
            relation_row["target_item_id"],
            relation_row["position"],
            relation_row["metadata"],
            relation_row["row_version"],
            relation_row["created_at"],
            relation_row["updated_at"],
        )
        assert await capture_positives() == pos
        # (4b) retained relation fact: the REAL item_relation row
        # (alpha -> beta through the reference field) exists again
        # in the live retained state; the common consumer never
        # projects the relation family, so the live positive is
        # unchanged - no relation-query semantics are asserted
        # here.  The frozen counterfactual set below proves the
        # retained relation is reference-validated at frozen
        # admission (a dangling retained relation refuses).
        detail_with_relation = await detail_projection()
        assert [
            i["slug"] for i in binding_items(detail_with_relation, "CollectionDetail")
        ] == ["alpha"]
        assert [
            i["slug"] for i in binding_items(detail_with_relation, "RelatedItems")
        ] == ["beta", "gamma"]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            relation_count = await owner.fetchval(
                "SELECT count(*) FROM content.item_relation WHERE site_id = $1",
                site_id,
            )
        assert relation_count == 1

        # (5) raw/resolved page style: the captured NON-DEFAULT raw
        # override is part of the retained state; OMITTING it must
        # make the resolved positive revert EXACTLY to the default
        # (the intended degraded value - observed by re-running the
        # original positive oracle, not an error), and the exact
        # restore must bring the overridden positive back.
        original_style = pos["page_style"]
        assert original_style.layout.content_width != "xl"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.page_base SET style_overrides = "
                '\'{"layout":{"content_width":"xl"}}\'::jsonb '
                "WHERE id = $1",
                list_id,
            )
        styled = await list_projection()
        assert styled.page_style != original_style
        assert styled.page_style.layout.content_width == "xl"
        # OMIT the captured non-default raw override.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.page_base SET style_overrides = '{}'::jsonb "
                "WHERE id = $1",
                list_id,
            )
        degraded_style = await list_projection()
        # The original positive oracle under the omission degrades
        # EXACTLY to the default resolved style (the same value as
        # the first capture, not a new fallback).
        assert degraded_style.page_style == original_style
        assert degraded_style.page_style.layout.content_width == (
            original_style.layout.content_width
        )
        assert await capture_positives() == pos
        # EXACT restore of the captured raw override.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.page_base SET style_overrides = "
                '\'{"layout":{"content_width":"xl"}}\'::jsonb '
                "WHERE id = $1",
                list_id,
            )
        restyled = await list_projection()
        assert restyled.page_style == styled.page_style
        assert restyled.page_style.layout.content_width == "xl"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.page_base SET style_overrides = '{}'::jsonb "
                "WHERE id = $1",
                list_id,
            )
        assert await capture_positives() == pos

        # (6) field definition omission: the projected "summary" field
        # has no definition anymore; the shared query-contract
        # validation must refuse the binding.
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # Capture the EXACT original row id before the
            # omission so the restore is verifiable.
            summary_field_row = await owner.fetchrow(
                "SELECT id FROM content.field_definition_base "
                "WHERE id = $1 AND type_id = $2 AND key = 'summary'",
                field_ids["summary"],
                type_id,
            )
            await owner.execute(
                "DELETE FROM content.field_definition_base "
                "WHERE id = $1 AND type_id = $2 AND key = 'summary'",
                field_ids["summary"],
                type_id,
            )
        with pytest.raises(ProjectionError) as field_omitted:
            await list_projection()
        assert field_omitted.value.reason == "unsupported_collection_query"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # EXACT restore: the original row id (not a fresh
            # UUID), then verify it.
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,"
                "cardinality,position,validation,ui_options,definition_"
                "version) VALUES "
                "($1,$2,'summary','Summary','long_text',true,true,1,1,"
                "'{}','{}',1)",
                summary_field_row["id"],
                type_id,
            )
            restored_field = await owner.fetchrow(
                "SELECT id FROM content.field_definition_base "
                "WHERE id = $1 AND type_id = $2",
                summary_field_row["id"],
                type_id,
            )
        assert restored_field["id"] == summary_field_row["id"]
        assert await capture_positives() == pos

        # (7) common projection execution stub: the shared winner
        # selection (resolve_page_route in the projection module) is
        # stubbed to resolve NOTHING; the dynamic detail positive must
        # fail closed as not_found, exactly the consumer's stable
        # refusal for a zero-row winner.
        import slaif_agent_site.render_api.projection as projection_module

        monkeypatch.setattr(
            projection_module, "resolve_page_route", lambda *a, **k: None
        )
        with pytest.raises(ProjectionError) as stubbed:
            await detail_projection()
        assert stubbed.value.reason == "not_found"
        monkeypatch.setattr(
            projection_module, "resolve_page_route", fs.resolve_page_route
        )
        assert await capture_positives() == pos

        # (8) fail-closed bound of the selected-locale positive: the
        # sl-SI detail route has NO sl-SI counterpart page (only the
        # list page was created localized); page-locale resolution is
        # exact and translation fallback never grants a page-locale
        # fallback, so the shared locale route must be not_found.
        with pytest.raises(ProjectionError) as locale_missing:
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path=f"{base}/sl-SI/news/alpha"
                )
            )
        assert locale_missing.value.reason == "not_found"

        # (9) frozen capture and common-consumer counterfactuals:
        # the trusted materializer - the REAL freeze job's document
        # source - captures the fully restored retained fixture
        # state into a review-snapshot/v2 document; the row is
        # sealed the exact way the capture emitter stores it,
        # admitted through the shared frozen admission seam, and
        # driven through the SAME common projection consumer as
        # the live positives.  Each retained family fact is then
        # omitted or corrupted ONCE inside a private deep copy
        # (payload and its normalized counterpart mutated
        # identically, digest recomputed) and must fail the
        # intended frozen way.  The original sealed row is never
        # touched: re-deriving from it stays identical (no
        # contamination).
        import copy

        from slaif_agent_site.sites.models import SiteContext

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # The genuine NON-DEFAULT style is applied through
            # the real producer in its legitimate context: the
            # supported page-style raw override on the live list
            # page (case 5 proved the live raw->resolved path).
            # The real materializer below captures it into the
            # sealed document (case 9h); the live state reverts
            # to the default immediately after the capture.
            await owner.execute(
                "UPDATE content.page_base SET style_overrides = "
                '\'{"layout":{"content_width":"xl"}}\'::jsonb '
                "WHERE id = $1",
                list_id,
            )
            # A real trusted workspace (the capture unit) with the
            # six pinned version facts, created by a real user
            # row: the sealed document binds real workspace
            # identity.
            frozen_user_id = await owner.fetchval(
                "INSERT INTO control.user_account "
                "(id, identity_kind, local_username, "
                "local_username_normalized, password_hash, display_name,"
                " status) VALUES (gen_random_uuid(), 'LOCAL',"
                " 'ParityFrozen', 'parityfrozen', $1, 'Parity Frozen',"
                " 'ACTIVE') RETURNING id",
                _FROZEN_ARGON2,
            )
            frozen_ws = await owner.fetchrow(
                "SELECT * FROM control.slaif_workspace_create("
                "$1,$2,'par-frozen','omission counterfactual capture',"
                "'L2_SITE_EDITOR','[]'::jsonb,24)",
                site_id,
                frozen_user_id,
            )
            assert frozen_ws is not None
            # The REAL trusted materializer over the retained
            # state INCLUDING the genuine non-default list-page
            # style.  No browser runs were requested for this
            # fixture, so no evidence is claimed.
            doc = await owner.fetchval(
                "SELECT control.slaif_review_workspace_state($1)",
                frozen_ws["id"],
            )
        # Live positive captured WHILE the genuine non-default
        # style is still applied: the frozen common consumer must
        # reproduce this same-state positive exactly; the only
        # difference from the default-captured `pos` is the
        # resolved list-page style.
        pos_xl = await capture_positives()
        assert pos_xl["page_style"].layout.content_width == "xl"
        for _key in pos:
            if _key != "page_style":
                assert pos_xl[_key] == pos[_key]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            # Revert the live page to the default immediately
            # after the capture: the frozen document alone
            # retains the non-default fact.
            await owner.execute(
                "UPDATE content.page_base SET style_overrides = '{}'::jsonb "
                "WHERE id = $1",
                list_id,
            )
        frozen_ws_id: UUID = UUID(str(frozen_ws["id"]))

        row = dict(build_snapshot_document(doc, created_by="slaif_review_worker"))
        row["id"] = str(uuid4())
        row["created_at"] = "2026-10-22T00:00:00+00:00"

        async def frozen_query_of(frozen_row: dict[str, Any], path: str) -> Any:
            surface = fs.FrozenRenderSurface(
                frozen_row,
                expected_snapshot_id=UUID(frozen_row["id"]),
                expected_site_id=site_id,
                expected_workspace_id=frozen_ws_id,
            )
            frozen_ctx = SiteContext._from_frozen(
                site_id=site_id,
                site_key=surface.site_key,
                status=surface.site_status,
                base_site_revision=surface.base_site_revision,
                default_locale=surface.default_locale,
                matched_path_prefix=None,
            )
            return await service._query(
                surface,
                context=frozen_ctx,
                request=RenderPageRequest(authority="localhost", path=path),
                render_mode="review",
                snapshot_id=UUID(frozen_row["id"]),
            )

        async def frozen_positive(frozen_row: dict[str, Any]) -> dict[str, Any]:
            lp = await frozen_query_of(frozen_row, "/listp")
            sp = await frozen_query_of(frozen_row, "/sl-SI/listp")
            dp = await frozen_query_of(frozen_row, "/news/alpha")
            return {
                "list_slugs": [i["slug"] for i in binding_items(lp, "CollectionList")],
                "list_ranks": [
                    i["values"]["rank"] for i in binding_items(lp, "CollectionList")
                ],
                "sl_titles": [
                    i["values"]["title"] for i in binding_items(sp, "CollectionList")
                ],
                "detail_page": str(dp.page.id),
                "detail_params": dict(dp.route_parameters),
                "related": [i["slug"] for i in binding_items(dp, "RelatedItems")],
                "page_style": lp.page_style,
            }

        def mutate_copy(mutate: Any) -> dict[str, Any]:
            # One deep copy of the sealed row.  The builder
            # aliases payload and normalized_state to ONE object
            # and deepcopy preserves that alias, so the mutator
            # runs ONCE on the shared document (a second run
            # would fail closed on an already-applied mutation);
            # the digest is recomputed exactly over the canonical
            # payload, so only the intended fact differs.
            mutated = copy.deepcopy(row)
            assert mutated["payload"] is mutated["normalized_state"]
            mutate(mutated["payload"])
            mutated["digest"] = canonical_digest(mutated["payload"])
            return mutated

        fpos = await frozen_positive(row)
        assert fpos == pos_xl

        # (9a) item field omission: the REQUIRED rank value vanishes
        # from beta's retained values; the common consumer must
        # fail closed on the invalid stored values exactly as live.
        def _drop_beta_rank(payload_: dict[str, Any]) -> None:
            for item in payload_["content"]["items"]:
                if item["id"] == str(item_ids["beta"]):
                    item["values"].pop("rank")

        with pytest.raises(ProjectionError) as frozen_rank:
            await frozen_positive(mutate_copy(_drop_beta_rank))
        assert frozen_rank.value.reason == "malformed_item"

        # (9b) translation omission: beta's sl-SI translation is
        # gone.  The SAME original selected-locale positive
        # oracle (asserted at first capture) is executed under
        # the omission and must fail for the intended reason:
        # the original sl titles no longer hold.  The exact
        # legitimate fallback (case 2 proved this same live
        # degradation) is pinned, the untouched rest of the
        # positive stays, and the restored original positive
        # holds again.
        def _drop_beta_sl_translation(payload_: dict[str, Any]) -> None:
            payload_["content"]["translations"] = [
                t
                for t in payload_["content"]["translations"]
                if not (
                    t["item_id"] == str(item_ids["beta"]) and t["locale"] == "sl-SI"
                )
            ]

        sl_titles_positive(fpos)
        frozen_degraded = await frozen_positive(mutate_copy(_drop_beta_sl_translation))
        with pytest.raises(AssertionError):
            sl_titles_positive(frozen_degraded)
        assert frozen_degraded["sl_titles"] == ["Alfa sl", "Beta en", "Gamma en"]
        degraded = dict(fpos)
        degraded["sl_titles"] = ["Alfa sl", "Beta en", "Gamma en"]
        assert frozen_degraded == degraded
        sl_titles_positive(fpos)

        # (9c) retained relation fact, three ways: the sealed
        # document retains the REAL relation row (alpha -> beta
        # through the reference field); the SAME retained-
        # relation inventory positive passes on the pristine
        # document, fails on the omitted copy for the intended
        # reason, and passes again on the untouched original;
        # OMITTING the retained relation changes NOTHING in the
        # projected positive (the common consumer never projects
        # the relation family - rendering inertness, honestly
        # scoped); and dropping beta while KEEPING the relation
        # makes the document dangling, which frozen admission
        # must refuse by reference validation.
        def retained_relation_positive(doc: dict[str, Any]) -> None:
            # The retained-relation inventory positive: the
            # captured document retains the real relation fact.
            assert any(
                r["source_item_id"] == str(item_ids["alpha"])
                and r["target_item_id"] == str(item_ids["beta"])
                and r["field_definition_id"] == str(related_field_id)
                for r in doc["content"]["relations"]
            )

        retained_relation_positive(row["payload"])

        def _drop_retained_relation(payload_: dict[str, Any]) -> None:
            payload_["content"]["relations"] = []

        assert await frozen_positive(mutate_copy(_drop_retained_relation)) == fpos
        omitted_relation = mutate_copy(_drop_retained_relation)
        with pytest.raises(AssertionError):
            retained_relation_positive(omitted_relation["payload"])
        retained_relation_positive(row["payload"])

        def _drop_beta_keep_relation(payload_: dict[str, Any]) -> None:
            payload_["content"]["items"] = [
                i
                for i in payload_["content"]["items"]
                if i["id"] != str(item_ids["beta"])
            ]
            payload_["content"]["translations"] = [
                t
                for t in payload_["content"]["translations"]
                if t["item_id"] != str(item_ids["beta"])
            ]

        mutated_c = mutate_copy(_drop_beta_keep_relation)
        assert any(
            r["source_item_id"] == str(item_ids["alpha"])
            and r["target_item_id"] == str(item_ids["beta"])
            and r["field_definition_id"] == str(related_field_id)
            for r in mutated_c["payload"]["content"]["relations"]
        )
        with pytest.raises(fs.SurfaceReadError) as dangling:
            fs.FrozenRenderSurface(
                mutated_c,
                expected_snapshot_id=UUID(mutated_c["id"]),
                expected_site_id=site_id,
                expected_workspace_id=frozen_ws_id,
            )
        assert dangling.value.reason == "not_found"

        # (9d) model-version staleness: beta's retained
        # type_definition_version no longer matches the retained
        # content type; the shared consumer must refuse the binding
        # as a stale definition, exactly as live.
        def _stale_beta_version(payload_: dict[str, Any]) -> None:
            for item in payload_["content"]["items"]:
                if item["id"] == str(item_ids["beta"]):
                    item["type_definition_version"] = 99

        with pytest.raises(ProjectionError) as frozen_stale_item:
            await frozen_positive(mutate_copy(_stale_beta_version))
        assert frozen_stale_item.value.reason == "stale_collection_definition"

        # (9e) view-version staleness: the retained view's
        # definition_version no longer matches the retained content
        # type; the same stable refusal.
        def _stale_view_version(payload_: dict[str, Any]) -> None:
            for view in payload_["content"]["views"]:
                if view["id"] == str(view_id):
                    view["definition_version"] = 99

        with pytest.raises(ProjectionError) as frozen_stale_view:
            await frozen_positive(mutate_copy(_stale_view_version))
        assert frozen_stale_view.value.reason == "stale_collection_definition"

        # (9f) binding omission: the list composition loses its
        # REQUIRED viewId prop (required by the component
        # catalog); the shared component-props contract - the
        # first gate of the common consumer path - must refuse
        # the composition as missing_prop (no fallback, no empty
        # list), before the deeper collection-view guard is
        # reached.
        def _strip_list_view(payload_: dict[str, Any]) -> None:
            for comp in payload_["page_compositions"]:
                if (
                    comp["page_id"] == str(list_id)
                    and comp["component_type"] == "CollectionList"
                ):
                    comp["props"] = {}

        with pytest.raises(ProjectionError) as frozen_binding:
            await frozen_positive(mutate_copy(_strip_list_view))
        assert frozen_binding.value.reason == "missing_prop"

        # (9g) common projection execution stub: the shared winner
        # selection resolves NOTHING on the frozen surface too; the
        # dynamic detail positive fails closed as not_found.
        monkeypatch.setattr(
            projection_module, "resolve_page_route", lambda *a, **k: None
        )
        with pytest.raises(ProjectionError) as frozen_stubbed:
            await frozen_query_of(row, "/news/alpha")
        assert frozen_stubbed.value.reason == "not_found"
        monkeypatch.setattr(
            projection_module, "resolve_page_route", fs.resolve_page_route
        )

        # (9h) frozen raw/resolved page style: the sealed
        # document captured the GENUINE non-default style
        # through the real producer (case 9 setup applied the
        # raw override to the live list page before the real
        # materializer ran; the live raw->resolved path is case
        # 5).  The SAME raw/resolved positive passes on the
        # pristine captured document, fails on a copy with the
        # retained style fact reverted to the default for the
        # intended reason, and passes again on the untouched
        # non-default original.
        assert row["payload"]["theme"]["layout"]["content_width"] != "xl"

        def frozen_style_positive(
            doc: dict[str, Any], positives: dict[str, Any]
        ) -> None:
            # The RAW captured override fact in the document and
            # the RESOLVED common-consumer style fact.
            for page in doc["pages"]:
                if page["id"] == str(list_id):
                    assert page["style_overrides"] == {
                        "layout": {"content_width": "xl"}
                    }
                    assert page["style"]["overrides"] == {
                        "layout": {"content_width": "xl"}
                    }
                    assert page["style"]["resolved"]["layout"]["content_width"] == "xl"
            assert positives["page_style"].layout.content_width == "xl"

        def _style_revert_default(payload_: dict[str, Any]) -> None:
            default_width = payload_["theme"]["layout"]["content_width"]
            for page in payload_["pages"]:
                if page["id"] == str(list_id):
                    page["style_overrides"] = {}
                    page["style"]["overrides"] = {}
                    page["style"]["resolved"]["layout"]["content_width"] = default_width

        frozen_style_positive(row["payload"], fpos)
        omitted_style = mutate_copy(_style_revert_default)
        omitted_style_pos = await frozen_positive(omitted_style)
        with pytest.raises(AssertionError):
            frozen_style_positive(omitted_style["payload"], omitted_style_pos)
        for _key in fpos:
            if _key != "page_style":
                assert omitted_style_pos[_key] == fpos[_key]
        frozen_style_positive(row["payload"], await frozen_positive(row))

        # Final no-contamination proof: every positive fact
        # re-derived after ALL restores is identical to the
        # first capture, on BOTH surfaces: the frozen capture
        # re-driven from the ORIGINAL sealed row and the live
        # canonical positives.
        assert await frozen_positive(row) == fpos
        assert await capture_positives() == pos
    finally:
        await public_pool.close()
        await control_pool.close()


async def _site_with_site_owner(
    database: AgentSiteDatabase,
    control_pool: Any,
    *,
    site_key: str,
    display_name: str,
    username: str,
    username_normalized: str,
) -> tuple[UUID, UUID]:
    """A real site plus the ACTIVE LOCAL SITE_OWNER principal.

    The site_membership row is exactly what the freeze gate
    (``workspace:freeze`` through
    ``control.slaif_human_agent_workspace_freeze``) and the 076 review
    authorization (``slaif_effective_human_membership``) both require,
    so the bound cases run through the REAL authority checks with no
    test-side bypass.
    """
    site = await SiteService(control_pool).create(
        CreateSiteRequest(
            site_key=site_key,
            display_name=display_name,
            default_locale="en",
        )
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        user_id = await owner.fetchval(
            "INSERT INTO control.user_account "
            "(id, identity_kind, local_username, "
            "local_username_normalized, password_hash, display_name,"
            " status) VALUES (gen_random_uuid(), 'LOCAL', $1, $2, $3,"
            " $4, 'ACTIVE') RETURNING id",
            username,
            username_normalized,
            _FROZEN_ARGON2,
            display_name,
        )
        await owner.execute(
            "INSERT INTO control.site_membership (site_id,user_account_id,"
            " role_key,delegation_ceiling) VALUES ($1,$2,'SITE_OWNER',4)",
            site.site_id,
            user_id,
        )
    return site.site_id, UUID(str(user_id))


async def _site_owner_workspace(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    user_id: UUID,
    title: str,
    description: str,
) -> UUID:
    """A real trusted workspace row (the freeze/review unit)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        ws = await owner.fetchrow(
            "SELECT * FROM control.slaif_workspace_create("
            "$1,$2,$3,$4,'L2_SITE_EDITOR','[]'::jsonb,24)",
            site_id,
            user_id,
            title,
            description,
        )
    assert ws is not None
    return UUID(str(ws["id"]))


async def _projection_effects(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    workspace_id: UUID,
    session_public_id: str | None = None,
) -> dict[str, Any]:
    """Trusted dimensions a projection read must leave untouched.

    Site revision, the canonical content-item value/count digest, the
    exact canonical page and composition row bytes, promotions, cache
    outbox, workspace status/accepted_at/frozen_at, review jobs, the
    full site media descriptor/status/published_at inventory, the
    workspace browser runs and (when a human session exists) its
    last_seen_at are exactly the mutation/context families the
    read/freeze/accept machinery owns.
    A read path that leaves every one of them identical has no
    effect; the freeze's own bookkeeping (status, frozen_at, the job
    row) is asserted separately by the caller.
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        site_revision = await owner.fetchval(
            "SELECT canonical_revision FROM control.site WHERE id = $1",
            site_id,
        )
        content_digest = await owner.fetchval(
            "SELECT md5(coalesce(string_agg("
            "id::text || '|' || site_id::text || '|' || type_id::text || "
            "'|' || slug || '|' || status || '|' || "
            "type_definition_version::text || '|' || values::text, "
            "',' ORDER BY id), '')) FROM content.content_item "
            "WHERE site_id = $1",
            site_id,
        )
        # NULL-safe element coalescing: one NULL column must not
        # null the whole row contribution out of the digest.
        pages_digest = await owner.fetchval(
            "SELECT md5(coalesce(string_agg("
            "coalesce(id::text, '\\N') || '|' || "
            "coalesce(site_id::text, '\\N') || '|' || "
            "coalesce(slug, '\\N') || '|' || coalesce(title, '\\N') "
            "|| '|' || coalesce(status, '\\N') || '|' || "
            "coalesce(locale, '\\N') || '|' || "
            "coalesce(parent_id::text, '\\N') || '|' || "
            "coalesce(row_version::text, '\\N') || '|' || "
            "coalesce(created_at::text, '\\N') || '|' || "
            "coalesce(updated_at::text, '\\N') || '|' || "
            "coalesce(route_template, '\\N') || '|' || "
            "coalesce(deleted_at::text, '\\N') || '|' || "
            "coalesce(style_overrides::text, '\\N'), "
            "',' ORDER BY id), '')) "
            "FROM content.page WHERE site_id = $1",
            site_id,
        )
        compositions_digest = await owner.fetchval(
            "SELECT md5(coalesce(string_agg("
            "coalesce(id::text, '\\N') || '|' || "
            "coalesce(site_id::text, '\\N') || '|' || "
            "coalesce(page_id::text, '\\N') || '|' || "
            "coalesce(component_type, '\\N') || '|' || "
            "coalesce(schema_version, '\\N') || '|' || "
            "coalesce(parent_id::text, '\\N') || '|' || "
            "coalesce(slot_key, '\\N') || '|' || "
            "coalesce(order_key::text, '\\N') || '|' || "
            "coalesce(props::text, '\\N') || '|' || "
            "coalesce(created_at::text, '\\N') || '|' || "
            "coalesce(updated_at::text, '\\N') || '|' || "
            "coalesce(catalog_version, '\\N') || '|' || "
            "coalesce(row_version::text, '\\N'), "
            "',' ORDER BY id), '')) "
            "FROM content.page_composition WHERE site_id = $1",
            site_id,
        )
        promotions = await owner.fetchval(
            "SELECT count(*) FROM audit.promotion WHERE site_id = $1",
            site_id,
        )
        cache_outbox = await owner.fetchval(
            "SELECT count(*) FROM control.cache_outbox WHERE site_id = $1",
            site_id,
        )
        workspace_status = await owner.fetchval(
            "SELECT status FROM control.workspace WHERE id = $1",
            workspace_id,
        )
        accepted_at = await owner.fetchval(
            "SELECT accepted_at FROM control.workspace WHERE id = $1",
            workspace_id,
        )
        frozen_at = await owner.fetchval(
            "SELECT frozen_at FROM control.workspace WHERE id = $1",
            workspace_id,
        )
        review_jobs = await owner.fetchval(
            "SELECT count(*) FROM control.review_job WHERE workspace_id = $1",
            workspace_id,
        )
        media = await owner.fetchrow(
            "SELECT count(*), "
            "md5(coalesce(string_agg("
            "coalesce(id::text, '\\N') || '|' || "
            "coalesce(site_id::text, '\\N') || '|' || "
            "coalesce(uploaded_by::text, '\\N') || '|' || "
            "coalesce(filename, '\\N') || '|' || "
            "coalesce(mime_type, '\\N') || '|' || "
            "coalesce(size_bytes::text, '\\N') || '|' || "
            "coalesce(content_hash, '\\N') || '|' || "
            "coalesce(storage_key, '\\N') || '|' || "
            "coalesce(alt_text, '\\N') || '|' || "
            "coalesce(metadata::text, '\\N') || '|' || "
            "coalesce(created_at::text, '\\N') || '|' || "
            "coalesce(updated_at::text, '\\N') || '|' || "
            "coalesce(public_status::text, '\\N') || '|' || "
            "coalesce(published_at::text, '\\N'), "
            "',' ORDER BY id), '')) "
            "FROM content.media_asset WHERE site_id = $1",
            site_id,
        )
        browser_runs = await owner.fetchrow(
            "SELECT count(*), max(created_at) FROM control.browser_run "
            "WHERE workspace_id = $1",
            workspace_id,
        )
        last_seen: Any = None
        if session_public_id is not None:
            last_seen = await owner.fetchval(
                "SELECT last_seen_at FROM control.user_session WHERE public_id = $1",
                session_public_id,
            )
    return {
        "site_revision": site_revision,
        "content_digest": content_digest,
        "pages_digest": pages_digest,
        "compositions_digest": compositions_digest,
        "promotions": promotions,
        "cache_outbox": cache_outbox,
        "workspace_status": workspace_status,
        "workspace_accepted_at": accepted_at,
        "workspace_frozen_at": frozen_at,
        "review_jobs": review_jobs,
        "media": (int(media["count"]), media["md5"]),
        "browser_runs": (int(browser_runs["count"]), browser_runs["max"]),
        "session_last_seen_at": last_seen,
    }


NO_EFFECT_DIMENSIONS = (
    "site_revision",
    "content_digest",
    "pages_digest",
    "compositions_digest",
    "promotions",
    "cache_outbox",
    "workspace_accepted_at",
    "review_jobs",
    "media",
    "browser_runs",
    "session_last_seen_at",
)


async def test_query_candidate_bound_admitted_real_surfaces(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """G10: the shared query candidate-set bound on REAL live/frozen reads.

    The product bound is ``query_dsl.MAX_CANDIDATES`` (1000), enforced
    by the common consumer on the CANDIDATE SET it must sort/paginate -
    not the per-type capture cap (2000) and not any job budget.  One
    site carries two content types that differ only in item count:
    exactly 1000 PUBLISHED candidates (the bound itself) and exactly
    1001 (one over), each behind a rank-sorted limit-10 view.

    (1) The trusted effect baseline is captured BEFORE any read.
    (2) LIVE canonical surface: the 1000-candidate list renders its
    exact ten lowest-ranked items; the 1001-candidate list refuses -
    proven BOTH as the uniform HTTP 404 AND as the real common-
    consumer ``query_cost`` reason on the same page, so an omitted
    type/view or any other 404 cannot substitute.
    (3) LIVE preview over the SAME ACTIVE workspace (real human
    session): the same bound, the same two outcomes, the byte-
    identical positive.
    (4) Every read leaves every trusted dimension identical,
    including the fresh session's last_seen_at (inside the 300s touch
    window, so the documented preview touch is provably absent).
    (5) A REAL freeze job (real enqueue, real worker claim, real run)
    ADMITS the complete state; the stored snapshot carries EXACTLY
    1000 items of the admitted type and EXACTLY 1001 of the over
    type (per-type capture counts from the sealed payload).
    (6) The freeze's own bookkeeping is asserted separately
    (status REVIEW, frozen_at set, exactly one more review job,
    accepted_at still NULL) while every no-effect dimension stays at
    the pre-freeze baseline.
    (7) The frozen common consumer over the sealed COMPLETE snapshot
    (admitted through the real R7 seam from the real 076 frozen-
    state read): the 1001 refusal carries the real ``query_cost``
    reason and the 1000 positive holds with the exact ten slugs.
    The frozen review contract is SITE-LOCAL: the 076 authorize
    function already bound the site, so the request path is the
    site-local route (``/admittedlist``), never the site-prefixed
    public path.
    (8) The authorized review HTTP surface: uniform 404 for the over
    list, byte-identical bindings for the admitted list, and the real
    076 authorization (anonymous and wrong-token refusals).
    (9) The authorized review read is effect-neutral: every trusted
    dimension stays at the post-freeze value.
    """
    import secrets

    import httpx
    from fastapi import FastAPI
    from pydantic import SecretStr
    from slaif_agent_site.content_model.query_dsl import MAX_CANDIDATES
    from slaif_agent_site.errors import install_error_handlers
    from slaif_agent_site.identity.sessions import (
        digest_secret,
        format_session_token,
        parse_session_token,
    )
    from slaif_agent_site.render_api.projection import RenderPreviewRequest
    from slaif_agent_site.render_api.site_http import (
        install_render_projection_routes,
    )
    from slaif_agent_site.sites.models import SiteContext
    from test_freeze_review_snapshot import _freeze_claim_run, _worker_pool

    assert MAX_CANDIDATES == 1000
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    worker_pool: Any = None
    try:
        site_id, owner_user_id = await _site_with_site_owner(
            database,
            control_pool,
            site_key="par-qbound",
            display_name="Query Candidate Bound",
            username="ParityQbound",
            username_normalized="parityqbound",
        )
        ws_id = await _site_owner_workspace(
            database,
            site_id=site_id,
            user_id=owner_user_id,
            title="par-qbound",
            description="query candidate bound capture",
        )
        admitted_type_id, over_type_id = uuid4(), uuid4()
        admitted_view_id, over_view_id = uuid4(), uuid4()
        home_id, admitted_page_id, over_page_id = uuid4(), uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,"
                "route_template) VALUES "
                "($1,$2,'home','QBound Home','PUBLISHED','en',NULL,NULL),"
                "($3,$2,'admittedlist','QBound Admitted','PUBLISHED','en',"
                "$1,NULL),"
                "($4,$2,'overlist','QBound Over','PUBLISHED','en',$1,NULL)",
                home_id,
                site_id,
                admitted_page_id,
                over_page_id,
            )
            for type_id, key in (
                (admitted_type_id, "qbound-admitted"),
                (over_type_id, "qbound-over"),
            ):
                await owner.execute(
                    "INSERT INTO content.content_type_base "
                    "(id,site_id,key,labels,slug_pattern,status,definition_"
                    "version,settings) VALUES ($1,$2,$3,'{}',"
                    "'/qb/{slug}','ACTIVE',1,'{}')",
                    type_id,
                    site_id,
                    key,
                )
                await owner.execute(
                    "INSERT INTO content.field_definition_base "
                    "(id,type_id,key,label,field_type,required,localized,"
                    "cardinality,position,validation,ui_options,definition_"
                    "version) VALUES (gen_random_uuid(),$1,'rank','Rank',"
                    "'integer',true,false,1,0,'{}','{}',1)",
                    type_id,
                )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,"
                "projection_spec,pagination_spec) VALUES "
                "($1,$2,$3,'qb-admitted','{}',"
                '\'{"field":"rank","direction":"asc"}\'::jsonb,'
                '\'{"fields":["rank"]}\'::jsonb,'
                '\'{"limit":10,"offset":0}\'::jsonb),'
                "($4,$2,$5,'qb-over','{}',"
                '\'{"field":"rank","direction":"asc"}\'::jsonb,'
                '\'{"fields":["rank"]}\'::jsonb,'
                '\'{"limit":10,"offset":0}\'::jsonb)',
                admitted_view_id,
                site_id,
                admitted_type_id,
                over_view_id,
                over_type_id,
            )
            for page_id, view_id in (
                (admitted_page_id, admitted_view_id),
                (over_page_id, over_view_id),
            ):
                await owner.execute(
                    "INSERT INTO content.page_composition_base "
                    "(site_id,page_id,component_type,schema_version,slot_key,"
                    "order_key,props) VALUES ($1,$2,'CollectionList','1',"
                    "'default',0,$3::jsonb)",
                    site_id,
                    page_id,
                    json.dumps({"viewId": str(view_id)}),
                )
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id,site_id,type_id,slug,status,type_definition_version,"
                "values) SELECT gen_random_uuid(), $1, $2, 'qa-'||g, "
                "'PUBLISHED', 1, jsonb_build_object('rank', g) FROM "
                "generate_series(1, 1000) g",
                site_id,
                admitted_type_id,
            )
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id,site_id,type_id,slug,status,type_definition_version,"
                "values) SELECT gen_random_uuid(), $1, $2, 'qo-'||g, "
                "'PUBLISHED', 1, jsonb_build_object('rank', g) FROM "
                "generate_series(1, 1001) g",
                site_id,
                over_type_id,
            )
            admitted_count = await owner.fetchval(
                "SELECT count(*) FROM content.content_item WHERE site_id=$1 "
                "AND type_id=$2 AND status='PUBLISHED'",
                site_id,
                admitted_type_id,
            )
            over_count = await owner.fetchval(
                "SELECT count(*) FROM content.content_item WHERE site_id=$1 "
                "AND type_id=$2 AND status='PUBLISHED'",
                site_id,
                over_type_id,
            )
        # The fixture IS the bound: exactly the admitted candidate set
        # and exactly one over it (asserted on the real COW view).
        assert admitted_count == MAX_CANDIDATES
        assert over_count == MAX_CANDIDATES + 1

        # The human session: fresh, so its last_seen_at is inside the
        # 300s preview touch window and provably untouched by reads.
        session_public_id = "sas2_" + uuid4().hex[:32]
        session_secret = secrets.token_bytes(32)
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "INSERT INTO control.user_session "
                "(id,public_id,secret_digest,csrf_secret_digest,"
                "user_account_id,created_at,last_seen_at,recent_auth_at,"
                "absolute_expires_at) VALUES (gen_random_uuid(),$1,$2,"
                "$3,$4,now(),now(),now(),now() + interval '1 hour')",
                session_public_id,
                digest_secret(session_secret),
                secrets.token_bytes(32),
                owner_user_id,
            )
        session_token = format_session_token(
            session_public_id, session_secret
        ).get_secret_value()
        # Round-trip proof: the header credential is the stored one.
        round_public_id, round_secret = parse_session_token(session_token)
        assert (round_public_id, round_secret) == (
            session_public_id,
            session_secret,
        )

        adapter = _RenderAdapter(public_pool, preview_pool)
        service = RenderProjectionService(adapter)
        render_app = FastAPI()
        install_error_handlers(render_app)
        install_render_projection_routes(render_app, adapter)

        async def post_page(path: str) -> httpx.Response:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                return await client.post(
                    "/internal/render/v1/page",
                    json={"authority": "localhost", "path": path},
                )

        async def post_preview(path: str, *, token: str) -> httpx.Response:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                return await client.post(
                    "/internal/render/v1/preview",
                    json={
                        "authority": "localhost",
                        "path": path,
                        "workspace_id": str(ws_id),
                    },
                    headers={"x-slaif-human-session": token},
                )

        async def post_review(
            path: str, snapshot_id: UUID, *, token: str | None
        ) -> httpx.Response:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                return await client.post(
                    "/internal/render/v1/review",
                    json={
                        "authority": "localhost",
                        "path": path,
                        "snapshot_id": str(snapshot_id),
                    },
                    headers=(
                        {"x-slaif-human-session": token} if token is not None else {}
                    ),
                )

        def http_list_slugs(body: dict[str, Any]) -> list[str]:
            list_nodes = [
                node
                for node in body["composition"]["nodes"]
                if node["component_type"] == "CollectionList"
            ]
            assert len(list_nodes) == 1
            binding = body["bindings"][list_nodes[0]["id"]]
            return [item["slug"] for item in binding]

        def binding_items(projection: Any, component: str) -> list[dict[str, Any]]:
            def node_id(proj: Any) -> str:
                for node in _walk_nodes(proj.composition.nodes):
                    if node.component_type == component:
                        return str(node.id)
                raise AssertionError(component)

            return [dict(item) for item in projection.bindings[node_id(projection)]]

        # (1) Baseline BEFORE any read: the trusted starting state.
        baseline = await _projection_effects(
            database,
            site_id=site_id,
            workspace_id=ws_id,
            session_public_id=session_public_id,
        )
        assert baseline["workspace_status"] == "ACTIVE"
        assert baseline["workspace_frozen_at"] is None
        assert baseline["workspace_accepted_at"] is None
        assert baseline["review_jobs"] == 0
        assert baseline["promotions"] == 0
        assert baseline["cache_outbox"] == 0
        assert baseline["media"][0] == 0
        assert baseline["browser_runs"][0] == 0
        assert baseline["session_last_seen_at"] is not None

        # (2) LIVE canonical surface: the admitted 1000-candidate
        # bound renders its exact ten lowest-ranked items; the
        # 1001-candidate list refuses as the uniform 404 AND with the
        # real common-consumer query_cost reason on the same page.
        admitted_canonical = await post_page("/s/par-qbound/admittedlist")
        assert admitted_canonical.status_code == 200, admitted_canonical.text
        over_canonical = await post_page("/s/par-qbound/overlist")
        assert over_canonical.status_code == 404, over_canonical.text
        assert "qa-" not in over_canonical.text
        assert "qo-" not in over_canonical.text
        admitted_direct = await service.canonical(
            RenderPageRequest(authority="localhost", path="/s/par-qbound/admittedlist")
        )
        with pytest.raises(ProjectionError) as over_direct:
            await service.canonical(
                RenderPageRequest(authority="localhost", path="/s/par-qbound/overlist")
            )
        assert over_direct.value.reason == "query_cost"
        canonical_slugs = [
            item["slug"] for item in binding_items(admitted_direct, "CollectionList")
        ]
        assert canonical_slugs == [f"qa-{n}" for n in range(1, 11)]
        assert http_list_slugs(admitted_canonical.json()) == canonical_slugs

        # (3) LIVE preview over the SAME ACTIVE workspace with the
        # real human session: the same bound, the same two outcomes,
        # the byte-identical positive.
        admitted_preview = await post_preview(
            "/s/par-qbound/admittedlist", token=session_token
        )
        assert admitted_preview.status_code == 200, admitted_preview.text
        assert (
            admitted_preview.json()["bindings"]
            == (admitted_canonical.json()["bindings"])
        )
        over_preview = await post_preview("/s/par-qbound/overlist", token=session_token)
        assert over_preview.status_code == 404, over_preview.text
        with pytest.raises(ProjectionError) as over_preview_direct:
            await service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/par-qbound/overlist",
                    workspace_id=ws_id,
                    session_token=SecretStr(session_token),
                )
            )
        assert over_preview_direct.value.reason == "query_cost"

        # (4) Every read is effect-neutral, the fresh session
        # included: its last_seen_at never left the baseline.
        assert (
            await _projection_effects(
                database,
                site_id=site_id,
                workspace_id=ws_id,
                session_public_id=session_public_id,
            )
            == baseline
        )

        # (5) REAL freeze over the 2001-item state: the per-type
        # capture cap admits 1001, so the complete state is captured
        # by the real worker run.
        worker_pool = await _worker_pool(database)
        freeze_result, _job_id = await _freeze_claim_run(
            database,
            workspace_id=ws_id,
            site_id=site_id,
            delegator_id=owner_user_id,
            pool=worker_pool,
            claimant="g10-freeze-worker",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result.error
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            snapshots = await owner.fetch(
                "SELECT id, status, created_by FROM control.review_snapshot "
                "WHERE workspace_id = $1",
                ws_id,
            )
        assert len(snapshots) == 1
        assert snapshots[0]["status"] == "COMPLETE"
        assert snapshots[0]["created_by"] == "g10-freeze-worker"
        snapshot_id = UUID(str(snapshots[0]["id"]))

        # (6) The freeze's own bookkeeping, asserted separately:
        # status REVIEW, frozen_at set, exactly one more review job,
        # accepted_at still NULL - and every no-effect dimension at
        # the pre-freeze baseline.
        after_freeze = await _projection_effects(
            database,
            site_id=site_id,
            workspace_id=ws_id,
            session_public_id=session_public_id,
        )
        assert after_freeze["workspace_status"] == "REVIEW"
        assert after_freeze["workspace_frozen_at"] is not None
        assert after_freeze["workspace_accepted_at"] is None
        assert after_freeze["review_jobs"] == baseline["review_jobs"] + 1
        for dimension in NO_EFFECT_DIMENSIONS:
            if dimension == "review_jobs":
                continue
            assert after_freeze[dimension] == baseline[dimension], dimension

        # (7) The sealed snapshot admitted EXACTLY the 2001-item
        # state: per-type captured item counts from the real 076
        # frozen-state read (preview reader) are exactly 1000 and
        # 1001, so an omitted type, view or item set cannot pass.
        async with preview_pool.acquire() as preview_conn:
            frozen_state = await preview_conn.fetchval(
                "SELECT control.slaif_review_snapshot_frozen_state($1)",
                snapshot_id,
            )
        assert isinstance(frozen_state, (str, bytes))
        frozen_row = parse_snapshot_text(
            frozen_state.decode() if isinstance(frozen_state, bytes) else frozen_state
        )
        assert isinstance(frozen_row, dict)
        items_by_type: dict[str, int] = {}
        for item in frozen_row["payload"]["content"]["items"]:
            items_by_type[item["type_id"]] = items_by_type.get(item["type_id"], 0) + 1
        assert items_by_type == {
            str(admitted_type_id): MAX_CANDIDATES,
            str(over_type_id): MAX_CANDIDATES + 1,
        }

        # (8) The frozen common consumer over the sealed COMPLETE
        # snapshot, admitted through the real R7 seam: the 1001
        # refusal carries the real query_cost reason and the 1000
        # positive holds with the exact ten slugs.
        surface = fs.FrozenRenderSurface(
            frozen_row,
            expected_snapshot_id=snapshot_id,
            expected_site_id=site_id,
            expected_workspace_id=ws_id,
        )
        frozen_ctx = SiteContext._from_frozen(
            site_id=site_id,
            site_key=surface.site_key,
            status=surface.site_status,
            base_site_revision=surface.base_site_revision,
            default_locale=surface.default_locale,
            matched_path_prefix=None,
        )
        with pytest.raises(ProjectionError) as frozen_over_direct:
            await service._query(
                surface,
                context=frozen_ctx,
                request=RenderPageRequest(authority="localhost", path="/overlist"),
                render_mode="review",
                snapshot_id=snapshot_id,
            )
        assert frozen_over_direct.value.reason == "query_cost"
        frozen_admitted = await service._query(
            surface,
            context=frozen_ctx,
            request=RenderPageRequest(authority="localhost", path="/admittedlist"),
            render_mode="review",
            snapshot_id=snapshot_id,
        )
        frozen_slugs = [
            item["slug"] for item in binding_items(frozen_admitted, "CollectionList")
        ]
        assert frozen_slugs == canonical_slugs == [f"qa-{n}" for n in range(1, 11)]

        # (9) The authorized review HTTP surface: uniform 404 for
        # the over list, byte-identical bindings for the admitted
        # list, and the real 076 authorization (a missing session
        # header and a well-formed token whose secret never matches
        # the stored digest are both uniform 404s).
        review_ok = await post_review("/admittedlist", snapshot_id, token=session_token)
        assert review_ok.status_code == 200, review_ok.text
        review_body = review_ok.json()
        assert http_list_slugs(review_body) == canonical_slugs
        assert review_body["bindings"] == admitted_canonical.json()["bindings"]
        assert review_body["page"]["id"] == admitted_canonical.json()["page"]["id"]
        review_over = await post_review("/overlist", snapshot_id, token=session_token)
        assert review_over.status_code == 404, review_over.text
        assert "qa-" not in review_over.text
        assert "qo-" not in review_over.text
        anonymous = await post_review("/admittedlist", snapshot_id, token=None)
        assert anonymous.status_code == 404, anonymous.text
        wrong = await post_review(
            "/admittedlist",
            snapshot_id,
            token=format_session_token(
                session_public_id, b"\x01" * 32
            ).get_secret_value(),
        )
        assert wrong.status_code == 404, wrong.text

        # (10) The authorized review read is effect-neutral too:
        # every trusted dimension stays at the post-freeze value.
        assert (
            await _projection_effects(
                database,
                site_id=site_id,
                workspace_id=ws_id,
                session_public_id=session_public_id,
            )
            == after_freeze
        )
    finally:
        if worker_pool is not None:
            await worker_pool.close()
        await public_pool.close()
        await preview_pool.close()
        await control_pool.close()


async def test_sibling_mismatch_recomputed_digest_admission_refusal(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """G11: media_references vs payload.media sibling mismatch refusal.

    The capture emitter seals ONE media map (``payload.media``) and its
    sibling binding (``media_references``); the shared admission seam
    cross-checks the two field-for-field and by length BEFORE the
    digest is trusted.  A trusted workspace (real SITE_OWNER, real
    ``slaif_workspace_create``) carries one real site media asset
    referenced by an Image composition; the REAL 076/075 materializer
    (``control.slaif_review_workspace_state``) captures it through real
    SQL media resolution and ``build_snapshot_document`` seals the
    exact row the capture emitter stores.  The pristine row admits
    with the exact one-asset map on BOTH sides.  Two sealed copies
    then break the sibling binding ONCE each - one reference field
    corrupted while the payload stays byte-identical, and one payload
    media entry dropped while the references stay - and BOTH carry a
    recomputed digest over the (intended) payload, so the digest gate
    passes and only the sibling gate can refuse: both must fail the
    stable ``not_found`` admission refusal.  The original sealed row
    is never touched (re-admission stays identical - no
    contamination), and the seal/admission/refusal sequence leaves
    every trusted dimension untouched.
    The admission controls are then complemented at the REAL
    trusted-SQL completion/store boundary under a valid trusted
    freeze-job context (real control enqueue, real worker claim,
    real materialized row bound in the PG-canonical form the real
    freeze job binds): the SAME two sibling malformations are
    submitted to the actual 076 completion function with a
    recomputed coherent digest each (so the digest gate cannot be
    what refuses), and BOTH must fail the exact stable SQL refusal
    SNAPSHOT_MEDIA_REFERENCES_MISMATCH with no snapshot row, no
    state change and the workspace still FREEZING.  An untampered
    real-constructor positive control on that same valid context
    then completes (server-generated immutable row identity),
    proving the refusals were sibling-specific; the exact stored
    row, the workspace/job bookkeeping and every no-effect
    dimension are asserted, and the untouched original row's both
    sibling sides remain byte-identical.
    """
    import copy

    from test_freeze_review_snapshot import _worker_pool

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    worker_pool: Any = None
    try:
        site_id, owner_user_id = await _site_with_site_owner(
            database,
            control_pool,
            site_key="par-sib",
            display_name="Sibling Mismatch",
            username="ParitySib",
            username_normalized="paritysib",
        )
        ws_id = await _site_owner_workspace(
            database,
            site_id=site_id,
            user_id=owner_user_id,
            title="par-sib",
            description="sibling mismatch seal capture",
        )
        media_id = uuid4()
        content_hash = "ab" * 32
        storage_key = f"sha256/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}"
        home_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.media_asset_base "
                "(id,site_id,uploaded_by,filename,mime_type,size_bytes,"
                "content_hash,storage_key,alt_text,metadata) VALUES "
                "($1,$2,$3,'g11.png','image/png',128,$4,$5,'G11','{}')",
                media_id,
                site_id,
                owner_user_id,
                content_hash,
                storage_key,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,"
                "route_template) VALUES ($1,$2,'home','Sib Home',"
                "'PUBLISHED','en',NULL,NULL)",
                home_id,
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) VALUES ($1,$2,'Image','1','default',0,"
                "$3::jsonb)",
                site_id,
                home_id,
                json.dumps({"mediaId": str(media_id), "alt": "G11"}),
            )
            media_count = await owner.fetchval(
                "SELECT count(*) FROM content.media_asset WHERE site_id = $1",
                site_id,
            )
        assert media_count == 1

        # The trusted SQL seal: the REAL materializer over the
        # workspace, resolved by real SQL media lookup, sealed by the
        # exact capture-emitter document builder.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            doc = await owner.fetchval(
                "SELECT control.slaif_review_workspace_state($1)",
                ws_id,
            )
        row = dict(build_snapshot_document(doc, created_by="g11-seal-worker"))
        row["id"] = str(uuid4())
        row["created_at"] = "2026-10-22T00:00:00+00:00"

        before = await _projection_effects(
            database, site_id=site_id, workspace_id=ws_id
        )
        assert before["workspace_status"] == "ACTIVE"
        assert before["workspace_frozen_at"] is None
        assert before["workspace_accepted_at"] is None
        assert before["media"][0] == 1

        # The pristine sealed row admits through the real R7 seam
        # with the exact one-asset map on BOTH sibling sides.
        payload, site_profile = fs.admit_frozen_snapshot(
            row,
            expected_snapshot_id=UUID(row["id"]),
            expected_site_id=site_id,
            expected_workspace_id=ws_id,
        )
        assert site_profile["site_key"] == "par-sib"
        assert len(payload["media"]) == 1
        assert len(row["media_references"]) == 1
        expected_descriptor = {
            "id": str(media_id),
            "mime_type": "image/png",
            "size_bytes": 128,
            "content_hash": content_hash,
            "public_status": "private",
        }
        assert payload["media"][str(media_id)] == expected_descriptor
        assert row["media_references"] == [expected_descriptor]
        # The builder aliases payload and normalized_state to ONE
        # document; deepcopy preserves the alias, so a payload
        # mutation below keeps the normalized counterpart coherent and
        # isolates the sibling gate.
        assert row["payload"] is row["normalized_state"]

        def sealed_copy(mutate: Any) -> dict[str, Any]:
            mutated = copy.deepcopy(row)
            assert mutated["payload"] is mutated["normalized_state"]
            mutate(mutated)
            mutated["digest"] = canonical_digest(mutated["payload"])
            return mutated

        def _sibling_hash_mismatch(doc: dict[str, Any]) -> None:
            # ONE reference field corrupted; the payload (and its
            # digest) stays byte-identical, so the digest gate passes
            # and only the field-for-field sibling check can refuse.
            doc["media_references"][0]["content_hash"] = "f" * 64

        with pytest.raises(fs.SurfaceReadError) as hash_mismatch:
            fs.admit_frozen_snapshot(
                sealed_copy(_sibling_hash_mismatch),
                expected_snapshot_id=UUID(row["id"]),
                expected_site_id=site_id,
                expected_workspace_id=ws_id,
            )
        assert hash_mismatch.value.reason == "not_found"

        def _drop_media_entry(doc: dict[str, Any]) -> None:
            # ONE payload media entry dropped (the normalized
            # counterpart follows through the builder alias); the
            # references stay, so the length cross-check can refuse.
            doc["payload"]["media"].pop(str(media_id))

        with pytest.raises(fs.SurfaceReadError) as length_mismatch:
            fs.admit_frozen_snapshot(
                sealed_copy(_drop_media_entry),
                expected_snapshot_id=UUID(row["id"]),
                expected_site_id=site_id,
                expected_workspace_id=ws_id,
            )
        assert length_mismatch.value.reason == "not_found"

        # No contamination: the ORIGINAL sealed row still admits with
        # the identical map and sibling binding, and the seal/admission/
        # refusal sequence touched no trusted dimension.
        payload2, site_profile2 = fs.admit_frozen_snapshot(
            row,
            expected_snapshot_id=UUID(row["id"]),
            expected_site_id=site_id,
            expected_workspace_id=ws_id,
        )
        assert payload2 == payload
        assert site_profile2 == site_profile
        assert row["media_references"] == [expected_descriptor]
        assert (
            await _projection_effects(database, site_id=site_id, workspace_id=ws_id)
            == before
        )

        # ---- The REAL trusted-SQL completion/store boundary (the
        # sibling trace at the store seam).  A valid trusted
        # freeze-job context: real control enqueue, real worker
        # claim, and the real materialized row bound in the exact
        # PG-canonical form the real freeze job binds.
        async with control_pool.acquire() as control_conn:
            freeze_rows = await control_conn.fetch(
                "SELECT * FROM control.slaif_human_agent_workspace_freeze($1,$2,$3)",
                ws_id,
                site_id,
                owner_user_id,
            )
        assert len(freeze_rows) == 1
        job_id = UUID(str(freeze_rows[0]["job_id"]))
        after_enqueue = await _projection_effects(
            database, site_id=site_id, workspace_id=ws_id
        )
        assert after_enqueue["workspace_status"] == "FREEZING"
        assert after_enqueue["workspace_frozen_at"] is not None
        assert after_enqueue["review_jobs"] == before["review_jobs"] + 1
        for dimension in NO_EFFECT_DIMENSIONS:
            if dimension == "review_jobs":
                continue
            assert after_enqueue[dimension] == before[dimension], dimension

        worker_pool = await _worker_pool(database)
        async with worker_pool.acquire() as worker_conn:
            claimed = await worker_conn.fetch(
                "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                "g11-sql-worker",
                ["FREEZE", "ACCEPT"],
            )
        assert len(claimed) == 1
        assert UUID(str(claimed[0]["id"])) == job_id
        assert str(claimed[0]["status"]) == "CLAIMED"
        assert str(claimed[0]["claimed_by"]) == "g11-sql-worker"

        async def worker_complete(sealed_row: dict[str, Any]) -> Any:
            async with worker_pool.acquire() as worker_conn:
                return await worker_conn.fetchval(
                    "SELECT control.slaif_review_snapshot_complete($1, $2)",
                    ws_id,
                    canonical_json(sealed_row),
                )

        async def stored_snapshot_count() -> int:
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as owner:
                return int(
                    await owner.fetchval(
                        "SELECT count(*) FROM control.review_snapshot "
                        "WHERE workspace_id = $1",
                        ws_id,
                    )
                )

        media_key = str(media_id)

        def tampered_sibling(mutate: Any) -> dict[str, Any]:
            # The builder emits media_references as FRESH dicts -
            # prove the reference side is not aliased into the
            # payload media map before mutating ONE side only.
            tampered = copy.deepcopy(row)
            assert (
                tampered["media_references"][0]
                is not tampered["payload"]["media"][media_key]
            )
            mutate(tampered)
            # The digest is recomputed exactly over the (intended)
            # payload, so the store's digest gate passes and only
            # the sibling gate can refuse.
            tampered["digest"] = canonical_digest(tampered["payload"])
            return tampered

        def _ref_hash_mismatch(doc: dict[str, Any]) -> None:
            doc["media_references"][0]["content_hash"] = "f" * 64

        def _ref_map_shorter(doc: dict[str, Any]) -> None:
            # The builder aliases payload and normalized_state to
            # ONE document and deepcopy preserves the alias, so the
            # drop follows into both (jsonb value equality holds);
            # the references list is a separate object and stays.
            assert doc["payload"] is doc["normalized_state"]
            doc["payload"]["media"].pop(media_key)

        with pytest.raises(asyncpg.PostgresError) as ref_mismatch:
            await worker_complete(tampered_sibling(_ref_hash_mismatch))
        assert ref_mismatch.value.sqlstate == "P0002"
        assert _pg_error_message(ref_mismatch.value) == (
            "SNAPSHOT_MEDIA_REFERENCES_MISMATCH"
        )
        assert await stored_snapshot_count() == 0
        assert (
            await _projection_effects(database, site_id=site_id, workspace_id=ws_id)
            == after_enqueue
        )

        with pytest.raises(asyncpg.PostgresError) as map_mismatch:
            await worker_complete(tampered_sibling(_ref_map_shorter))
        assert map_mismatch.value.sqlstate == "P0002"
        assert _pg_error_message(map_mismatch.value) == (
            "SNAPSHOT_MEDIA_REFERENCES_MISMATCH"
        )
        assert await stored_snapshot_count() == 0
        assert (
            await _projection_effects(database, site_id=site_id, workspace_id=ws_id)
            == after_enqueue
        )

        # The UNTAMPERED real-constructor positive control on that
        # same valid context completes: the refusal above was the
        # sibling gate, not the context.
        stored_snapshot_id = await worker_complete(row)
        assert stored_snapshot_id is not None
        stored_snapshot_id = UUID(str(stored_snapshot_id))
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            stored = await owner.fetchrow(
                "SELECT id, status, digest, created_by, "
                "media_references, payload, workspace_id, site_id "
                "FROM control.review_snapshot WHERE workspace_id = $1",
                ws_id,
            )
            ws = await owner.fetchrow(
                "SELECT status, review_snapshot_id, accepted_at "
                "FROM control.workspace WHERE id = $1",
                ws_id,
            )
        assert await stored_snapshot_count() == 1
        assert stored is not None
        assert stored["status"] == "COMPLETE"
        assert stored["digest"] == row["digest"]
        assert stored["created_by"] == "g11-seal-worker"
        # The owner connection returns jsonb as text: decode through
        # the exact-number path and assert the stored sibling sides.
        stored_refs = json.loads(stored["media_references"])
        assert stored_refs == [expected_descriptor]
        stored_payload = parse_snapshot_text(stored["payload"])
        assert stored_payload["state_version"] == "review-snapshot/v2"
        assert stored_payload["media"] == {media_key: expected_descriptor}
        assert str(ws["status"]) == "REVIEW"
        assert ws["review_snapshot_id"] == stored_snapshot_id
        assert ws["accepted_at"] is None
        async with worker_pool.acquire() as worker_conn:
            terminal = await worker_conn.fetchval(
                "SELECT control.slaif_review_job_terminal($1, 'SUCCEEDED', NULL)",
                job_id,
            )
        assert terminal is True

        final = await _projection_effects(database, site_id=site_id, workspace_id=ws_id)
        assert final["workspace_status"] == "REVIEW"
        assert final["workspace_frozen_at"] is not None
        assert final["workspace_accepted_at"] is None
        assert final["review_jobs"] == before["review_jobs"] + 1
        for dimension in NO_EFFECT_DIMENSIONS:
            if dimension == "review_jobs":
                continue
            assert final[dimension] == before[dimension], dimension
        # The untouched original row: BOTH sibling sides remain
        # byte-identical after every tampered submission.
        assert row["media_references"] == [expected_descriptor]
        assert row["payload"]["media"][media_key] == expected_descriptor
    finally:
        if worker_pool is not None:
            await worker_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_rc8_captured_chain_raw_depth_and_byte_budget_wiring(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: Any,
) -> None:
    """RC8: the cohesive REAL-capture boundary proof at current source.

    (1) REAL 16-edge/17-node composition chain. Owner-trusted
    ``page_composition`` rows (16 ``Section`` nodes + one ``RichText``
    leaf, slot ``default``, order 0..16) are materialized by the real
    076 SQL materializer and captured by the claimed REAL worker
    freeze (real control enqueue + real job claim + real run).  The
    sealed stored row must retain the RAW composition inventory
    exactly (17 rows, exact props/parents/slots/orders) AND the
    normalized node tree must match that inventory node-by-node: the
    same 17 node ids with parent links isomorphic to the raw
    ``parent_id`` chain, and each normalized node's actual
    type/schema, parent, slot/order and props asserted against the
    independently seeded raw facts (including the exact RichText leaf
    props).  The freeze's bookkeeping and every
    no-effect dimension follow the G10 pattern.
    (2) REAL raw-value depth boundary on a retained raw JSON field:
    ``content_type.settings``, the exact field the 076 1293-1299
    materializer preflight bounds (``content type labels/settings raw
    depth``).  Settings at depth 7 and depth 8 are captured by the
    SAME real freeze with their exact nested values retained in the
    sealed payload.  An owner-inserted depth-9 settings row (trusted
    fixture data that makes the site capture over budget - honestly
    labeled; NOT a public mutation and no public maximum is claimed
    from it) makes a second real worker freeze refuse at the actual
    gate: job FAILED ``SNAPSHOT_OVER_BUDGET``, the materializer's
    stable message + exact branch detail, zero snapshot rows and full
    before/after no-effects.
    (3) FULL frozen admission STRICTER-test-budget wiring on the
    captured stored row, read through the real 076
    ``slaif_review_snapshot_frozen_state`` surface: N is
    independently measured as the canonical UTF-8 byte length of the
    stored payload and cross-checked against the stored digest.
    Isolated STRICTER test budgets (N-1 / N / N+1, with 0 < N+1
    asserted below the production constant before they are used)
    applied by monkeypatching ONLY the ``fs.MAX_CANONICAL_PAYLOAD_
    BYTES`` constant (restored after) must show refusal / positive /
    positive at the caller with the correct site context and the
    sealed row bytes + every trusted dimension exactly unchanged.
    This proves the actual outer wiring of the SAME bounded
    serializer at the admission caller; it is explicitly NOT an
    8 MiB capture maximum and NOT a production quota change - the
    production constant is asserted unchanged before and after.
    (4) ACTUAL production 8 MiB FULL read admission at exactly
    N-1/N/N+1 with N = 8 MiB, at the UNCHANGED production constant:
    three coherent copies of the ACTUAL stored snapshot row, each a
    trusted-owner HOSTILE READ fixture (in-memory corruption only -
    no DB write, no public mutation, NEVER a lawful capture maximum
    or a newly supported public mutation).  Each copy aligns
    payload and normalized_state (canonical-identical), recomputes
    the exact digest over the new canonical text, and retains the
    real row's valid identities, versions and sibling bindings; the
    exact canonical byte size is independently asserted per copy.
    8 MiB-1 and 8 MiB admit; 8 MiB+1 refuses stably - the positive
    and the refusal differ by exactly ONE byte on an otherwise
    valid row, so the byte gate itself is proven to be the decider,
    not another malformed shape/identity guard.
    (5) NARROW direct SQL proof of the REAL cost function's exact
    8 MiB boundary: ``control.slaif_review_value_cost`` at budget
    8388608 returns exactly 8388608 (non-negative: the materializer
    total-gate condition is false) at the exact budget and -1 one
    cost unit over, proven for a scalar string (exact cost 2+L,
    ``slaif_review_string_cost`` asserted == L for pure ASCII) and a
    one-key object document (exact cost 8+L) mirroring the total
    gate's call shape.  Pure IMMUTABLE function reads, zero
    fixture/DB mutation.  Per root's COMPLETE 013 DDL read, the
    control.site profile text is CHECK-constrained (display_name
    1..128 chars + btrim), so full worker total-gate reachability
    via a corrupted profile is NOT claimed here and no guard is
    changed; the rigorous all-constraints reachability audit stays
    with the secondary scratch lane.
    Preserved unchanged by this test: the existing 17-node synthetic
    seam test (test_render_projection), the unit ``_node_chain_depth``
    boundary, and the exact numeric/UTF-8/escape byte unit vectors
    (test_snapshot_v2_canonical).
    """
    import copy as _copy
    import hashlib

    from slaif_agent_site.review_worker.freeze_job import run_freeze_job
    from test_freeze_review_snapshot import (
        _freeze_claim_run,
        _freeze_enqueue_claim,
        _freeze_refusal_state,
        _hostile_effect_snapshot,
        _materializer_refusal_detail,
        _worker_pool,
        _worker_settings,
    )

    def _nested_depth(depth: int, leaf: str = "leaf") -> dict[str, Any]:
        """Exactly ``depth`` nested containers with a scalar leaf."""
        value: Any = leaf
        for level in range(depth):
            value = {f"l{level}": value}
        assert isinstance(value, dict)
        return value

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    preview_pool = await database.role_pool("slaif_preview_reader")
    worker_pool = await _worker_pool(database)
    try:
        site_id, owner_user_id = await _site_with_site_owner(
            database,
            control_pool,
            site_key="par-rc8",
            display_name="RC8 Capture Boundaries",
            username="ParityRc8",
            username_normalized="parityrc8",
        )
        ws_a = await _site_owner_workspace(
            database,
            site_id=site_id,
            user_id=owner_user_id,
            title="par-rc8-a",
            description="rc8 chain and raw depth capture",
        )
        chain_ids = [uuid4() for _ in range(17)]
        leaf_props = {
            "content": {
                "type": "paragraph",
                "children": [{"text": "rc8-chain-leaf"}],
            }
        }
        type7_id, type8_id = uuid4(), uuid4()
        chain_page_id = uuid4()
        nested7, nested8, nested9 = (
            _nested_depth(7),
            _nested_depth(8),
            _nested_depth(9),
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=true, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base (id,site_id,slug,title,"
                "status,locale) VALUES ($1,$2,'chainhome',"
                "'RC8 Chain Home','PUBLISHED','en')",
                chain_page_id,
                site_id,
            )
            # (1) The owner-trusted 17-node chain (16 edges).
            for i, node_id in enumerate(chain_ids):
                is_leaf = i == 16
                parent = None if i == 0 else chain_ids[i - 1]
                await owner.execute(
                    "INSERT INTO content.page_composition_base "
                    "(id,site_id,page_id,component_type,schema_version,"
                    "parent_id,slot_key,order_key,props) VALUES "
                    "($1,$2,$3,$4,'1',$5::uuid,'default',$6,$7)",
                    node_id,
                    site_id,
                    chain_page_id,
                    "RichText" if is_leaf else "Section",
                    parent,
                    i,
                    _jsonb_text(leaf_props) if is_leaf else "{}",
                )
            # (2) The two valid raw-depth settings fixtures (7 and 8,
            # exactly the 076 preflight maximum).
            for type_id, key, settings in (
                (type7_id, "rc8-depth-7", nested7),
                (type8_id, "rc8-depth-8", nested8),
            ):
                await owner.execute(
                    "INSERT INTO content.content_type_base "
                    '(id,site_id,"key",labels,slug_pattern,status,'
                    "definition_version,settings) VALUES "
                    "($1,$2,$3,'{}','/rc8/' || $3,'ACTIVE',1,$4)",
                    type_id,
                    site_id,
                    key,
                    _jsonb_text(settings),
                )
        baseline = await _projection_effects(
            database, site_id=site_id, workspace_id=ws_a
        )

        # The REAL freeze: real control enqueue + real worker claim +
        # real run over the trusted capture state.
        freeze_result, _job_a = await _freeze_claim_run(
            database,
            workspace_id=ws_a,
            site_id=site_id,
            delegator_id=owner_user_id,
            pool=worker_pool,
            claimant="rc8-freeze-worker",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result.error

        # The freeze's own bookkeeping, asserted separately; every
        # no-effect dimension stays at the pre-freeze baseline.
        after_freeze = await _projection_effects(
            database, site_id=site_id, workspace_id=ws_a
        )
        assert after_freeze["workspace_status"] == "REVIEW"
        assert after_freeze["workspace_frozen_at"] is not None
        assert after_freeze["workspace_accepted_at"] is None
        assert after_freeze["review_jobs"] == baseline["review_jobs"] + 1
        for dimension in NO_EFFECT_DIMENSIONS:
            if dimension == "review_jobs":
                continue
            assert after_freeze[dimension] == baseline[dimension], dimension

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            snap = await owner.fetchrow(
                "SELECT * FROM control.review_snapshot WHERE workspace_id = $1",
                ws_a,
            )
        assert snap is not None and snap["status"] == "COMPLETE"
        assert snap["created_by"] == "rc8-freeze-worker"
        snapshot_id = UUID(str(snap["id"]))
        stored_payload: Any = parse_snapshot_text(
            json.dumps(snap["payload"])
            if not isinstance(snap["payload"], str)
            else snap["payload"]
        )
        assert isinstance(stored_payload, dict)

        # (1) RAW composition inventory: exactly the 17 trusted rows,
        # exact props/parents/slots/orders, no row omitted or altered.
        raw_rows = stored_payload["page_compositions"]
        assert isinstance(raw_rows, list)
        assert len(raw_rows) == 17
        raw_by_id = {str(r["id"]): r for r in raw_rows}
        assert set(raw_by_id) == {str(n) for n in chain_ids}
        for i, node_id in enumerate(chain_ids):
            raw = raw_by_id[str(node_id)]
            assert (
                raw["parent_id"] is None
                if i == 0
                else (str(raw["parent_id"]) == str(chain_ids[i - 1]))
            )
            assert raw["slot_key"] == "default"
            assert raw["order_key"] == i
            assert raw["component_type"] == ("RichText" if i == 16 else "Section")
            assert raw["props"] == (leaf_props if i == 16 else {})

        # (1) NORMALIZED nodes matched against the raw inventory: one
        # root, a single-child chain in seeded order, and a parent map
        # isomorphic to the raw parent_id links.
        pages = stored_payload["pages"]
        assert len(pages) == 1
        assert pages[0]["slug"] == "chainhome"
        nodes = pages[0]["nodes"]
        assert len(nodes) == 1
        path: list[str] = []
        norm_nodes: dict[str, dict[str, Any]] = {}

        def _walk(node: dict[str, Any], parent: str | None) -> None:
            path.append(str(node["id"]))
            norm_nodes[str(node["id"])] = node
            assert node["parent_id"] == parent
            children = node.get("children") or []
            assert len(children) <= 1
            for child in children:
                _walk(child, str(node["id"]))

        _walk(nodes[0], None)
        assert path == [str(n) for n in chain_ids]
        # Every normalized node carries its ACTUAL type/schema,
        # parent, slot/order and props - asserted node-by-node
        # against the independently seeded raw facts (especially the
        # exact RichText leaf props), so a normalized tree with the
        # right shape but wrong per-node facts cannot pass.
        for i, node_id in enumerate(chain_ids):
            norm = norm_nodes[str(node_id)]
            raw = raw_by_id[str(node_id)]
            is_leaf = i == 16
            assert (
                norm["component_type"]
                == raw["component_type"]
                == ("RichText" if is_leaf else "Section")
            )
            assert norm["schema_version"] == raw["schema_version"] == "1"
            expected_parent = None if i == 0 else str(chain_ids[i - 1])
            assert norm["parent_id"] == expected_parent
            assert (
                raw["parent_id"] is None
                if i == 0
                else str(raw["parent_id"]) == expected_parent
            )
            assert norm["slot_key"] == raw["slot_key"] == "default"
            assert norm["order_key"] == raw["order_key"] == i
            expected_props = leaf_props if is_leaf else {}
            assert norm["props"] == expected_props == raw["props"]

        vr = snap["validation_report"]
        vr = json.loads(vr) if isinstance(vr, str) else vr
        assert vr["pages_validated"] == 1
        assert vr["errors"] == []
        assert canonical_digest(stored_payload) == str(snap["digest"])

        # (2) The retained raw settings values survived capture at
        # exactly their written depth: 7 and 8, byte-exact values.
        types_by_key = {t["key"]: t for t in stored_payload["content"]["types"]}
        assert types_by_key["rc8-depth-7"]["settings"] == nested7
        assert types_by_key["rc8-depth-8"]["settings"] == nested8

        # (2) The depth-9 owner-trusted fixture row (honestly labeled
        # trusted fixture data, not a public mutation): a second real
        # worker freeze must refuse at the actual materializer gate.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            await owner.execute(
                "INSERT INTO content.content_type_base "
                '(id,site_id,"key",labels,slug_pattern,status,'
                "definition_version,settings) VALUES "
                "(gen_random_uuid(),$1,'rc8-depth-9','{}',"
                "'/rc8/rc8-depth-9','ACTIVE',1,$2)",
                site_id,
                _jsonb_text(nested9),
            )
        ws_b = await _site_owner_workspace(
            database,
            site_id=site_id,
            user_id=owner_user_id,
            title="par-rc8-b",
            description="rc8 raw depth nine refusal",
        )
        job_id_b, job_b = await _freeze_enqueue_claim(
            database,
            workspace_id=ws_b,
            site_id=site_id,
            delegator_id=owner_user_id,
            claimant="rc8-depth9-worker",
        )
        pre = await _hostile_effect_snapshot(
            database, workspace_id=ws_b, site_id=site_id
        )
        result_b = await run_freeze_job(worker_pool, _worker_settings(database), job_b)
        post = await _hostile_effect_snapshot(
            database, workspace_id=ws_b, site_id=site_id
        )
        assert result_b.status == "FAILED"
        assert result_b.error == "SNAPSHOT_OVER_BUDGET"
        message, detail = await _materializer_refusal_detail(
            database, workspace_id=ws_b
        )
        assert message == "REVIEW_SNAPSHOT_OVER_BUDGET"
        assert detail == "content type labels/settings raw depth"
        assert post == pre
        job_row, state = await _freeze_refusal_state(
            database, workspace_id=ws_b, job_id=job_id_b
        )
        assert job_row["status"] == "FAILED"
        assert job_row["error"] == "SNAPSHOT_OVER_BUDGET"
        assert state == "FREEZING/0"

        # (3) FULL frozen admission on the ACTUAL captured stored row,
        # at its independently measured canonical byte size N.
        async with preview_pool.acquire() as preview_conn:
            frozen_state = await preview_conn.fetchval(
                "SELECT control.slaif_review_snapshot_frozen_state($1)",
                snapshot_id,
            )
        assert isinstance(frozen_state, (str, bytes))
        frozen_row: Any = parse_snapshot_text(
            frozen_state.decode() if isinstance(frozen_state, bytes) else frozen_state
        )
        payload_map = frozen_row["payload"]
        canonical_text = canonical_json(payload_map)
        n_bytes = len(canonical_text.encode("utf-8"))
        assert n_bytes > 0
        assert hashlib.sha256(canonical_text.encode("utf-8")).hexdigest() == str(
            frozen_row["digest"]
        )
        # The production boundary stays exactly the 8 MiB constant,
        # and every isolated test budget below stays STRICTER than
        # it: N+1 still below 8 MiB, so none of the test budgets is
        # a production quota change or an 8 MiB capture maximum.
        prod_budget = fs.MAX_CANONICAL_PAYLOAD_BYTES
        assert prod_budget == 8 * 1024 * 1024
        assert 0 < n_bytes - 1 < n_bytes < n_bytes + 1 < prod_budget
        admit_kwargs = dict(
            expected_snapshot_id=snapshot_id,
            expected_site_id=site_id,
            expected_workspace_id=ws_a,
        )
        effect_baseline = await _projection_effects(
            database, site_id=site_id, workspace_id=ws_a
        )

        # STRICTER N-1: the real canonical size exceeds the isolated
        # test budget, so the OUTER wiring refuses at the caller.
        monkeypatch.setattr(fs, "MAX_CANONICAL_PAYLOAD_BYTES", n_bytes - 1)
        with pytest.raises(fs.SurfaceReadError) as over_budget:
            fs.admit_frozen_snapshot(frozen_row, **admit_kwargs)
        assert over_budget.value.reason == "not_found"

        # Exactly N: the measured capture size admits.
        monkeypatch.setattr(fs, "MAX_CANONICAL_PAYLOAD_BYTES", n_bytes)
        admitted_payload, site_profile = fs.admit_frozen_snapshot(
            frozen_row, **admit_kwargs
        )
        assert site_profile["site_key"] == "par-rc8"
        assert canonical_json(admitted_payload) == canonical_text

        # N+1: still positive - the wiring compares sizes, it does not
        # special-case the boundary.
        monkeypatch.setattr(fs, "MAX_CANONICAL_PAYLOAD_BYTES", n_bytes + 1)
        admitted_payload2, _profile2 = fs.admit_frozen_snapshot(
            frozen_row, **admit_kwargs
        )
        assert canonical_json(admitted_payload2) == canonical_text
        monkeypatch.undo()
        assert fs.MAX_CANONICAL_PAYLOAD_BYTES == 8 * 1024 * 1024

        # The admission attempts changed nothing: the sealed row bytes
        # and every trusted dimension are exactly unchanged.
        async with preview_pool.acquire() as preview_conn:
            frozen_state_after = await preview_conn.fetchval(
                "SELECT control.slaif_review_snapshot_frozen_state($1)",
                snapshot_id,
            )
        before_text = (
            frozen_state if isinstance(frozen_state, str) else frozen_state.decode()
        )
        after_text = (
            frozen_state_after
            if isinstance(frozen_state_after, str)
            else frozen_state_after.decode()
        )
        assert after_text == before_text
        assert (
            await _projection_effects(database, site_id=site_id, workspace_id=ws_a)
            == effect_baseline
        )

        # (4) ACTUAL production 8 MiB read admission at N-1/N/N+1,
        # N = 8 MiB, at the UNCHANGED production constant.  The
        # copies are owner-hostile READ fixtures: in-memory
        # corruption of the ACTUAL stored row only - no DB write, no
        # public mutation, never a lawful capture maximum.
        prod_budget = fs.MAX_CANONICAL_PAYLOAD_BYTES
        assert prod_budget == 8 * 1024 * 1024
        base_len = len(canonical_json(frozen_row["payload"]).encode("utf-8"))
        # The base length INCLUDES the real display_name; the pad must
        # replace those exact bytes, not assume a one-char original.
        base_name_bytes = len(
            frozen_row["payload"]["site"]["display_name"].encode("utf-8")
        )

        def _inflated_row(target: int) -> Any:
            corrupted = _copy.deepcopy(frozen_row)
            pad_len = base_name_bytes + (target - base_len)
            assert pad_len > 1
            corrupted["payload"]["site"]["display_name"] = "x" * pad_len
            corrupted["normalized_state"]["site"]["display_name"] = "x" * pad_len
            inflated_text = canonical_json(corrupted["payload"])
            # Independently proved exact canonical byte size.
            assert len(inflated_text.encode("utf-8")) == target
            # Payload / normalized state aligned (canonical-identical).
            assert canonical_json(corrupted["normalized_state"]) == inflated_text
            corrupted["digest"] = hashlib.sha256(
                inflated_text.encode("utf-8")
            ).hexdigest()
            return corrupted

        for target in (prod_budget - 1, prod_budget):
            admitted, profile = fs.admit_frozen_snapshot(
                _inflated_row(target), **admit_kwargs
            )
            assert profile["site_key"] == "par-rc8"
            assert len(canonical_json(admitted).encode("utf-8")) == target
        with pytest.raises(fs.SurfaceReadError) as prod_over_budget:
            fs.admit_frozen_snapshot(_inflated_row(prod_budget + 1), **admit_kwargs)
        assert prod_over_budget.value.reason == "not_found"

        # (5) NARROW direct SQL proof of the REAL cost function's
        # exact 8 MiB boundary (the function the materializer total
        # gate calls as value_cost(doc, 0, 8388608) < 0).  Pure
        # IMMUTABLE reads; zero fixture/DB mutation.  No worker
        # total-gate reachability claim (013 DDL bounds the profile
        # text; the rigorous all-constraints audit is the secondary
        # scratch lane's), and no guard/authority change.
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            at_budget = await owner.fetchval(
                "SELECT control.slaif_review_value_cost("
                " to_jsonb($1::text), 0, 8388608)",
                "x" * (8388608 - 2),
            )
            over_budget = await owner.fetchval(
                "SELECT control.slaif_review_value_cost("
                " to_jsonb($1::text), 0, 8388608)",
                "x" * (8388608 - 1),
            )
            doc_at_budget = await owner.fetchval(
                "SELECT control.slaif_review_value_cost("
                " to_jsonb(json_build_object('k', $1::text)), 0, 8388608)",
                "x" * (8388608 - 8),
            )
            doc_over_budget = await owner.fetchval(
                "SELECT control.slaif_review_value_cost("
                " to_jsonb(json_build_object('k', $1::text)), 0, 8388608)",
                "x" * (8388608 - 7),
            )
            ascii_cost = await owner.fetchval(
                "SELECT control.slaif_review_string_cost($1)",
                "x" * 1000,
            )
        assert at_budget == 8388608
        assert over_budget == -1
        assert doc_at_budget == 8388608
        assert doc_over_budget == -1
        assert ascii_cost == 1000

        # After the production admission trio AND the SQL boundary
        # calls: the original sealed stored row bytes and every
        # trusted dimension are still exactly unchanged.
        async with preview_pool.acquire() as preview_conn:
            frozen_state_final = await preview_conn.fetchval(
                "SELECT control.slaif_review_snapshot_frozen_state($1)",
                snapshot_id,
            )
        final_text = (
            frozen_state_final
            if isinstance(frozen_state_final, str)
            else frozen_state_final.decode()
        )
        assert final_text == before_text
        assert (
            await _projection_effects(database, site_id=site_id, workspace_id=ws_a)
            == effect_baseline
        )
    finally:
        await worker_pool.close()
        await preview_pool.close()
        await control_pool.close()

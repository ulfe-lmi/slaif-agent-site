"""Real PostgreSQL evidence for the bounded static Render structure router."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from fastapi import FastAPI
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.errors import install_error_handlers
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    RenderPreviewRequest,
    RenderProjectionService,
)
from slaif_agent_site.render_api.site_http import install_render_projection_routes
from slaif_agent_site.sites import CreateSiteRequest
from slaif_agent_site.sites.resolver import SiteResolver
from slaif_agent_site.sites.service import SiteService


class _RenderAdapter:
    def __init__(self, pool: Any, preview_pool: Any | None = None) -> None:
        self._pool = pool
        self._preview_pool = preview_pool or pool
        self._resolver = SiteResolver(pool)
        self.acquire_timeout = 3.0

    def resolver(self) -> SiteResolver:
        return self._resolver

    def public_pool(self) -> Any:
        return self._pool

    def preview_pool(self) -> Any:
        return self._preview_pool


def _agent_settings(database: AgentSiteDatabase) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    locator = (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="render-structure-test",
    )


@pytest.mark.asyncio
async def test_static_hierarchy_locale_navigation_and_redirect_projection(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="structure-router",
                display_name="Structure Router",
                default_locale="en",
            )
        )
        home_id, guide_id, sl_home_id, sl_guide_id = (uuid4() for _ in range(4))
        navigation_id = uuid4()
        root_item_id, child_item_id, external_item_id = (uuid4() for _ in range(3))
        en_only_item_id, sl_only_item_id, hidden_parent_child_id = (
            uuid4() for _ in range(3)
        )
        global_internal_item_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($1,'sl-SI',true,false,1) "
                "ON CONFLICT (site_id,tag) DO UPDATE SET enabled=EXCLUDED.enabled, "
                "is_default=EXCLUDED.is_default, position=EXCLUDED.position",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES "
                "($1,$2,'home','Home','PUBLISHED','en',NULL,NULL),"
                "($3,$2,'guide','Guide','PUBLISHED','en',$1,NULL),"
                "($4,$2,'home','Domov','PUBLISHED','sl-SI',NULL,NULL),"
                "($5,$2,'guide','Vodnik','PUBLISHED','sl-SI',$4,NULL)",
                home_id,
                site.site_id,
                guide_id,
                sl_home_id,
                sl_guide_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'primary','Primary', $3::jsonb, '{}'::jsonb)",
                navigation_id,
                site.site_id,
                '{"en":"Primary","sl-SI":"Glavni meni"}',
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$13::uuid,$4,'PAGE',$5,$6::jsonb,NULL,0),"
                "($7,$2,$3,$1,$1,$8,'PAGE',$9,$10::jsonb,NULL,0),"
                "($11,$2,$3,NULL,$13::uuid,NULL,'EXTERNAL','https://example.test/docs',"
                "$12::jsonb,'sl-SI',1)",
                root_item_id,
                site.site_id,
                navigation_id,
                home_id,
                str(home_id),
                '{"en":"Home","sl-SI":"Domov"}',
                child_item_id,
                sl_guide_id,
                str(sl_guide_id),
                '{"en":"Guide","sl-SI":"Vodnik"}',
                external_item_id,
                '{"en":"Docs","sl-SI":"Dokumenti"}',
                "00000000-0000-0000-0000-000000000000",
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4::uuid,NULL,'INTERNAL','/guide',$5::jsonb,'en',2),"
                "($6,$2,$3,NULL,$4::uuid,NULL,'INTERNAL','/sl-SI/guide',"
                "$7::jsonb,'sl-SI',3),"
                "($8,$2,$3,$9,$9::uuid,NULL,'INTERNAL','/sl-SI/guide',"
                "$10::jsonb,'sl-SI',0)",
                en_only_item_id,
                site.site_id,
                navigation_id,
                "00000000-0000-0000-0000-000000000000",
                '{"en":"English only"}',
                sl_only_item_id,
                '{"sl-SI":"Slovenski only"}',
                hidden_parent_child_id,
                en_only_item_id,
                '{"sl-SI":"Hidden child"}',
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4::uuid,NULL,'INTERNAL','/guide',$5::jsonb,NULL,4)",
                global_internal_item_id,
                site.site_id,
                navigation_id,
                "00000000-0000-0000-0000-000000000000",
                '{"en":"Global guide","sl-SI":"Global vodnik"}',
            )
            await owner.execute(
                "INSERT INTO content.redirect_base "
                "(site_id,source_route,target,status_code,locale) "
                "VALUES ($1,'/legacy','/guide',301,NULL)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) VALUES "
                "($1,$2,'Heading','1','default',0,'{\"text\":\"Guide\","
                '"level":2}\'::jsonb)',
                site.site_id,
                guide_id,
            )
        service = RenderProjectionService(_RenderAdapter(public_pool))
        root = await service.canonical(
            RenderPageRequest(authority="localhost", path="/s/structure-router/")
        )
        assert root.route_kind == "page"
        assert root.page.effective_route == "/"
        assert root.page.parent_id is None
        assert root.page.route_template is None
        assert [locale.tag for locale in root.locales] == ["en", "sl-SI"]
        assert root.locale == "en"
        assert root.navigation[0].label == "Primary"
        assert root.navigation[0].items[0].target.value == "/"
        assert root.navigation[0].items[0].children[0].target.value == "/sl-SI/guide"
        assert any(item.target.value == "/guide" for item in root.navigation[0].items)
        root_labels = {item.label for item in root.navigation[0].items}
        assert "English only" in root_labels
        assert "Slovenski only" not in root_labels
        assert "Hidden child" not in root_labels

        nested = await service.canonical(
            RenderPageRequest(authority="localhost", path="/s/structure-router/guide")
        )
        assert nested.route_kind == "page"
        assert nested.page.id == guide_id
        assert nested.page.effective_route == "/guide"

        translated = await service.canonical(
            RenderPageRequest(
                authority="localhost", path="/s/structure-router/sl-si/guide"
            )
        )
        assert translated.route_kind == "page"
        assert translated.page.id == sl_guide_id
        assert translated.page.effective_route == "/sl-SI/guide"
        assert translated.locale == "sl-SI"
        assert translated.navigation[0].label == "Glavni meni"
        translated_labels = {item.label for item in translated.navigation[0].items}
        assert "Slovenski only" in translated_labels
        assert "English only" not in translated_labels
        assert "Hidden child" not in translated_labels
        global_item = next(
            item
            for item in translated.navigation[0].items
            if item.target.value == "/guide"
        )
        assert global_item.label == "Global vodnik"

        redirect = await service.canonical(
            RenderPageRequest(authority="localhost", path="/s/structure-router/legacy")
        )
        assert redirect.route_kind == "redirect"
        assert redirect.redirect.status_code == 301
        assert redirect.redirect.target == "/s/structure-router/guide"

        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/structure-router/guide/item"
                )
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/structure-router/%2e%2e/guide"
                )
            )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.site_locale_base SET enabled=false "
                "WHERE site_id=$1 AND tag='sl-SI'",
                site.site_id,
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/structure-router/sl-si/guide"
                )
            )
    finally:
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_locale_neutral_internal_render_status_and_hostile_targets(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Prove locale-neutral targets retain routes across locales and fail closed."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="internal-render-locale-neutral",
                display_name="Internal Render Locale Neutral",
                default_locale="en-US",
            )
        )
        foreign_site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="internal-render-locale-foreign",
                display_name="Internal Render Locale Foreign",
                default_locale="en-US",
            )
        )
        docs_id, guide_id, draft_id, home_id, duplicate_root_id, deleted_id = (
            uuid4() for _ in range(6)
        )
        duplicate_child_id, dynamic_id, foreign_page_id = (uuid4() for _ in range(3))
        navigation_id, item_id = uuid4(), uuid4()
        preview_user_id, preview_session_id, preview_workspace_id = (
            uuid4(),
            uuid4(),
            uuid4(),
        )
        preview_secret = b"i" * 32
        preview_public_id = f"sas2_{preview_session_id.hex}"
        expires = datetime.now(UTC) + timedelta(hours=1)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en-US',true,true,0),($1,'sl-SI',true,false,1)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en-US',true,true,0)",
                foreign_site.site_id,
            )
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id,identity_kind,oidc_issuer,oidc_subject,display_name) "
                "VALUES ($1,'OIDC','https://issuer.test',$2,'Internal Render Preview')",
                preview_user_id,
                f"subject-{preview_user_id}",
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id,user_account_id,role_key,delegation_ceiling) "
                "VALUES ($1,$2,'SITE_EDITOR',2)",
                site.site_id,
                preview_user_id,
            )
            await owner.execute(
                "INSERT INTO control.user_session "
                "(id,public_id,secret_digest,csrf_secret_digest,user_account_id,"
                "absolute_expires_at) VALUES ($1,$2,$3,$4,$5,$6)",
                preview_session_id,
                preview_public_id,
                hashlib.sha256(preview_secret).digest(),
                b"i" * 32,
                preview_user_id,
                expires,
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id,site_id,created_by,actor_type,title,delegation_preset,"
                "status,expires_at) VALUES ($1,$2,$3,'HUMAN','Internal Render Preview',"
                "'L2_SITE_EDITOR','ACTIVE',$4)",
                preview_workspace_id,
                site.site_id,
                preview_user_id,
                expires,
            )
            await owner.executemany(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
                [
                    (
                        docs_id,
                        site.site_id,
                        "docs",
                        "Docs",
                        "PUBLISHED",
                        "en-US",
                        None,
                        None,
                    ),
                    (
                        guide_id,
                        site.site_id,
                        "guide",
                        "Vodnik",
                        "PUBLISHED",
                        "sl-SI",
                        None,
                        None,
                    ),
                    (
                        draft_id,
                        site.site_id,
                        "draft-target",
                        "Draft",
                        "DRAFT",
                        "en-US",
                        None,
                        None,
                    ),
                    (
                        home_id,
                        site.site_id,
                        "home",
                        "Home",
                        "PUBLISHED",
                        "en-US",
                        None,
                        None,
                    ),
                    (
                        duplicate_root_id,
                        site.site_id,
                        "dupe",
                        "Dupe root",
                        "PUBLISHED",
                        "en-US",
                        None,
                        None,
                    ),
                    (
                        duplicate_child_id,
                        site.site_id,
                        "dupe",
                        "Dupe child",
                        "PUBLISHED",
                        "en-US",
                        home_id,
                        None,
                    ),
                    (
                        deleted_id,
                        site.site_id,
                        "deleted",
                        "Deleted",
                        "PUBLISHED",
                        "en-US",
                        None,
                        None,
                    ),
                    (
                        dynamic_id,
                        site.site_id,
                        "dynamic",
                        "Dynamic",
                        "PUBLISHED",
                        "en-US",
                        None,
                        "{slug}",
                    ),
                    (
                        foreign_page_id,
                        foreign_site.site_id,
                        "foreign",
                        "Foreign",
                        "PUBLISHED",
                        "en-US",
                        None,
                        None,
                    ),
                ],
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'primary','Primary',$3::jsonb,'{}'::jsonb)",
                navigation_id,
                site.site_id,
                '{"en-US":"Primary","sl-SI":"Glavni meni"}',
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4::uuid,NULL,'INTERNAL','/docs',$5::jsonb,NULL,0)",
                item_id,
                site.site_id,
                navigation_id,
                "00000000-0000-0000-0000-000000000000",
                '{"en-US":"Docs","sl-SI":"Dokumenti"}',
            )

        service = RenderProjectionService(_RenderAdapter(public_pool, preview_pool))
        selected_path = "/s/internal-render-locale-neutral/sl-si/guide"
        global_projection = await service.canonical(
            RenderPageRequest(authority="localhost", path=selected_path)
        )
        assert global_projection.route_kind == "page"
        assert global_projection.locale == "sl-SI"
        global_item = global_projection.navigation[0].items[0]
        assert global_item.locale is None
        assert global_item.target.value == "/docs"
        assert global_item.label == "Dokumenti"

        async def set_item(
            target: str, *, locale: str | None = None, page_id: UUID | None = None
        ) -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE content.navigation_item_base SET page_id=$1, "
                    "target_kind='INTERNAL',target_value=$2,locale=$3 WHERE id=$4",
                    page_id,
                    target,
                    locale,
                    item_id,
                )

        await set_item("/sl-SI/guide", locale="sl-SI")
        locale_specific = await service.canonical(
            RenderPageRequest(authority="localhost", path=selected_path)
        )
        assert locale_specific.route_kind == "page"
        assert locale_specific.navigation[0].items[0].target.value == "/sl-si/guide"
        assert locale_specific.navigation[0].items[0].locale == "sl-SI"

        await set_item("/docs")
        preview_request = RenderPreviewRequest(
            authority="localhost",
            path=selected_path,
            workspace_id=preview_workspace_id,
            session_token=format_session_token(preview_public_id, preview_secret),
        )
        await set_item("/draft-target")
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=selected_path)
            )
        draft_preview = await service.preview(preview_request)
        assert draft_preview.route_kind == "page"
        assert any(
            item.target.value == "/draft-target"
            for navigation in draft_preview.navigation
            for item in navigation.items
        )

        await set_item("/deleted")
        deleted_projection = await service.canonical(
            RenderPageRequest(authority="localhost", path=selected_path)
        )
        assert deleted_projection.route_kind == "page"
        assert deleted_projection.locale == "sl-SI"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute("DELETE FROM content.page_base WHERE id=$1", deleted_id)
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=selected_path)
            )

        for hostile_target in ("/absent", "/dupe", "/{slug}", "/admin", "/foreign"):
            await set_item(hostile_target)
            with pytest.raises(ProjectionError, match="unavailable"):
                await service.canonical(
                    RenderPageRequest(authority="localhost", path=selected_path)
                )
        await set_item("/docs", page_id=docs_id)
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=selected_path)
            )

        await set_item("/docs")
        recovered = await service.canonical(
            RenderPageRequest(authority="localhost", path=selected_path)
        )
        assert recovered.route_kind == "page"
        assert recovered.navigation[0].items[0].target.value == "/docs"
        async with public_pool.acquire(timeout=3) as connection:
            assert not connection.is_in_transaction()
            assert await connection.fetchval("SELECT 1") == 1
        async with preview_pool.acquire(timeout=3) as connection:
            assert not connection.is_in_transaction()
            assert await connection.fetchval("SELECT 1") == 1
    finally:
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_dynamic_collection_detail_route_binds_exact_published_item(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Resolve one dynamic page and bind its CollectionDetail item safely."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="dynamic-collection-router",
                display_name="Dynamic Collection Router",
                default_locale="en-US",
            )
        )
        root_id, detail_id = uuid4(), uuid4()
        type_id, title_id, summary_id, rank_id, view_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        published_id, draft_id, archived_id = uuid4(), uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en-US',true,true,0),($1,'sl-SI',true,false,1)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,'news','News','PUBLISHED','en-US',NULL,NULL),"
                "($3,$2,'detail','Detail','PUBLISHED','en-US',$1,'{slug}')",
                root_id,
                site.site_id,
                detail_id,
            )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,definition_version,"
                "settings) "
                "VALUES ($1,$2,'news','{}','/news/{slug}','ACTIVE',1,'{}')",
                type_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,cardinality,"
                "position,validation,ui_options,definition_version) VALUES "
                "($1,$2,'title','Title','short_text',true,true,1,0,'{}','{}',1),"
                "($3,$2,'summary','Summary','long_text',true,true,1,1,'{}','{}',1),"
                "($4,$2,'rank','Rank','integer',true,false,1,2,'{}','{}',1)",
                title_id,
                type_id,
                summary_id,
                rank_id,
            )
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id,site_id,type_id,slug,status,type_definition_version,values) "
                "VALUES ($1,$2,$3,'published-item','PUBLISHED',1,$6::jsonb),"
                "($4,$2,$3,'draft-item','DRAFT',1,$7::jsonb),"
                "($5,$2,$3,'archived-item','ARCHIVED',1,$8::jsonb)",
                published_id,
                site.site_id,
                type_id,
                draft_id,
                archived_id,
                '{"rank":3}',
                '{"rank":2}',
                '{"rank":1}',
            )
            await owner.execute(
                "INSERT INTO content.content_item_translation_base "
                "(site_id,item_id,locale,localized_values) VALUES "
                "($1,$2,'en-US',$5::jsonb),($1,$3,'en-US',$6::jsonb),"
                "($1,$4,'en-US',$7::jsonb)",
                site.site_id,
                published_id,
                draft_id,
                archived_id,
                '{"title":"Published title","summary":"Published summary"}',
                '{"title":"Draft title","summary":"Draft summary"}',
                '{"title":"Archived title","summary":"Archived summary"}',
            )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,"
                "pagination_spec) VALUES ($1,$2,$3,'news', '{}'::jsonb, "
                "$4::jsonb,$5::jsonb,$6::jsonb)",
                view_id,
                site.site_id,
                type_id,
                '{"field":"rank","direction":"desc"}',
                '{"fields":["title","summary","rank"]}',
                '{"limit":10,"offset":0}',
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) "
                "VALUES ($1,$2,'CollectionList','1','default',0,$3::jsonb),"
                "($1,$4,'CollectionDetail','1','default',0,$3::jsonb)",
                site.site_id,
                root_id,
                json.dumps({"viewId": str(view_id)}),
                detail_id,
            )
        service = RenderProjectionService(_RenderAdapter(public_pool))
        listing = await service.canonical(
            RenderPageRequest(
                authority="localhost", path="/s/dynamic-collection-router/news"
            )
        )
        assert listing.route_kind == "page"
        assert listing.page.route_template is None
        assert listing.bindings[next(iter(listing.bindings))][0]["values"] == {
            "title": "Published title",
            "summary": "Published summary",
            "rank": 3,
        }
        detail = await service.canonical(
            RenderPageRequest(
                authority="localhost",
                path="/s/dynamic-collection-router/news/published-item",
            )
        )
        assert detail.route_kind == "page"
        assert detail.route_parameters == {"slug": "published-item"}
        detail_binding = next(iter(detail.bindings.values()))
        assert detail_binding[0]["slug"] == "published-item"
        assert detail_binding[0]["values"]["title"] == "Published title"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base "
                "SET type_definition_version=99 WHERE id=$1",
                published_id,
            )
        with pytest.raises(
            ProjectionError, match="stale_collection_definition|not_found"
        ):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost",
                    path="/s/dynamic-collection-router/news/published-item",
                )
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base "
                "SET type_definition_version=1 WHERE id=$1",
                published_id,
            )
        for slug in ("draft-item", "archived-item", "unknown-item"):
            with pytest.raises(ProjectionError, match="not_found"):
                await service.canonical(
                    RenderPageRequest(
                        authority="localhost",
                        path=f"/s/dynamic-collection-router/news/{slug}",
                    )
                )

        original_query = service._query

        async def run_snapshot_race(
            *,
            path: str,
            resolved_route: str,
            mutate: Any,
        ) -> Any:
            snapshot_established = asyncio.Event()
            release_snapshot = asyncio.Event()

            async def paused_query(connection: Any, **kwargs: Any) -> Any:
                context = kwargs["context"]
                await connection.fetchrow(
                    "SELECT * FROM content.slaif_render_page_resolve($1,$2,$3,$4)",
                    context.site_id,
                    resolved_route,
                    "en-US",
                    ["PUBLISHED"],
                )
                snapshot_established.set()
                await release_snapshot.wait()
                return await original_query(connection, **kwargs)

            monkeypatch.setattr(service, "_query", paused_query)
            task = asyncio.create_task(
                service.canonical(RenderPageRequest(authority="localhost", path=path))
            )
            try:
                await asyncio.wait_for(snapshot_established.wait(), timeout=5)
                await mutate()
                release_snapshot.set()
                return await asyncio.wait_for(task, timeout=5)
            finally:
                release_snapshot.set()
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                monkeypatch.setattr(service, "_query", original_query)

        async def update_item_snapshot() -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE content.content_item_base SET slug='raced-item',"
                    "status='DRAFT' WHERE id=$1",
                    published_id,
                )
                await owner.execute(
                    "UPDATE content.content_item_translation_base "
                    "SET localized_values=$1::jsonb "
                    "WHERE item_id=$2 AND locale='en-US'",
                    json.dumps({"title": "Raced title", "summary": "Raced summary"}),
                    published_id,
                )

        before_item_race = await run_snapshot_race(
            path="/s/dynamic-collection-router/news/published-item",
            resolved_route="/news/published-item",
            mutate=update_item_snapshot,
        )
        assert before_item_race.page.slug == "detail"
        before_item_binding = next(iter(before_item_race.bindings.values()))[0]
        assert before_item_binding["slug"] == "published-item"
        assert before_item_binding["values"]["title"] == "Published title"
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost",
                    path="/s/dynamic-collection-router/news/raced-item",
                )
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base SET slug='published-item',"
                "status='PUBLISHED' WHERE id=$1",
                published_id,
            )
            await owner.execute(
                "UPDATE content.content_item_translation_base "
                "SET localized_values=$1::jsonb "
                "WHERE item_id=$2 AND locale='en-US'",
                json.dumps(
                    {"title": "Published title", "summary": "Published summary"}
                ),
                published_id,
            )

        delete_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id,site_id,type_id,slug,status,type_definition_version,values) "
                "VALUES ($1,$2,$3,'delete-item','PUBLISHED',1,$4::jsonb)",
                delete_id,
                site.site_id,
                type_id,
                json.dumps({"rank": 4}),
            )
            await owner.execute(
                "INSERT INTO content.content_item_translation_base "
                "(site_id,item_id,locale,localized_values) VALUES "
                "($1,$2,'en-US',$3::jsonb)",
                site.site_id,
                delete_id,
                json.dumps({"title": "Delete title", "summary": "Delete summary"}),
            )

        async def delete_item_snapshot() -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "DELETE FROM content.content_item_translation_base "
                    "WHERE item_id=$1",
                    delete_id,
                )
                await owner.execute(
                    "DELETE FROM content.content_item_base WHERE id=$1", delete_id
                )

        before_delete_race = await run_snapshot_race(
            path="/s/dynamic-collection-router/news/delete-item",
            resolved_route="/news/delete-item",
            mutate=delete_item_snapshot,
        )
        assert (
            next(iter(before_delete_race.bindings.values()))[0]["slug"] == "delete-item"
        )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost",
                    path="/s/dynamic-collection-router/news/delete-item",
                )
            )

        async def change_view_snapshot() -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE content.collection_view_base SET projection_spec="
                    "$1::jsonb WHERE id=$2",
                    json.dumps({"fields": ["title", "summary"]}),
                    view_id,
                )

        before_view_race = await run_snapshot_race(
            path="/s/dynamic-collection-router/news",
            resolved_route="/news",
            mutate=change_view_snapshot,
        )
        assert before_view_race.route_kind == "page"
        before_view_values = next(iter(before_view_race.bindings.values()))[0]["values"]
        assert before_view_values["rank"] == 3
        after_view_race = await service.canonical(
            RenderPageRequest(
                authority="localhost", path="/s/dynamic-collection-router/news"
            )
        )
        assert after_view_race.route_kind == "page"
        assert "rank" not in next(iter(after_view_race.bindings.values()))[0]["values"]

        async def change_type_snapshot() -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE content.content_type_base SET definition_version=2 "
                    "WHERE id=$1",
                    type_id,
                )

        before_type_race = await run_snapshot_race(
            path="/s/dynamic-collection-router/news",
            resolved_route="/news",
            mutate=change_type_snapshot,
        )
        assert before_type_race.route_kind == "page"
        assert next(iter(before_type_race.bindings.values()))[0]["slug"] == (
            "published-item"
        )
        with pytest.raises(
            ProjectionError, match="stale_collection_definition|not_found"
        ):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/dynamic-collection-router/news"
                )
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_type_base SET definition_version=1 WHERE id=$1",
                type_id,
            )
            await owner.execute(
                "UPDATE content.collection_view_base SET projection_spec="
                "$1::jsonb WHERE id=$2",
                json.dumps({"fields": ["title", "summary", "rank"]}),
                view_id,
            )

        moved_parent_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,'moved','Moved','PUBLISHED','en-US',NULL,NULL)",
                moved_parent_id,
                site.site_id,
            )

        async def move_page_snapshot() -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE content.page_base SET parent_id=$1 WHERE id=$2",
                    moved_parent_id,
                    detail_id,
                )

        before_page_move = await run_snapshot_race(
            path="/s/dynamic-collection-router/news/published-item",
            resolved_route="/news/published-item",
            mutate=move_page_snapshot,
        )
        assert before_page_move.route_kind == "page"
        assert before_page_move.page.effective_route == "/news/{slug}"
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost",
                    path="/s/dynamic-collection-router/news/published-item",
                )
            )
        moved = await service.canonical(
            RenderPageRequest(
                authority="localhost",
                path="/s/dynamic-collection-router/moved/published-item",
            )
        )
        assert moved.route_kind == "page"
        assert moved.page.effective_route == "/moved/{slug}"

        cancellation_snapshot = asyncio.Event()
        cancellation_release = asyncio.Event()

        async def cancellable_query(connection: Any, **kwargs: Any) -> Any:
            context = kwargs["context"]
            await connection.fetchrow(
                "SELECT * FROM content.slaif_render_page_resolve($1,$2,$3,$4)",
                context.site_id,
                "/moved/published-item",
                "en-US",
                ["PUBLISHED"],
            )
            cancellation_snapshot.set()
            await cancellation_release.wait()
            return await original_query(connection, **kwargs)

        monkeypatch.setattr(service, "_query", cancellable_query)
        cancelled = asyncio.create_task(
            service.canonical(
                RenderPageRequest(
                    authority="localhost",
                    path="/s/dynamic-collection-router/moved/published-item",
                )
            )
        )
        await asyncio.wait_for(cancellation_snapshot.wait(), timeout=5)
        cancelled.cancel()
        with pytest.raises(asyncio.CancelledError):
            await cancelled
        cancellation_release.set()
        monkeypatch.setattr(service, "_query", original_query)
        reusable = await service.canonical(
            RenderPageRequest(
                authority="localhost",
                path="/s/dynamic-collection-router/moved/published-item",
            )
        )
        assert reusable.route_kind == "page"
        assert reusable.page.effective_route == "/moved/{slug}"
    finally:
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_dynamic_detail_hostile_render_matrix_fails_closed(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Exercise every bounded dynamic-detail failure through Render HTTP."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="dynamic-hostile-matrix",
                display_name="Dynamic Hostile Matrix",
                default_locale="en-US",
            )
        )
        foreign_site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="dynamic-hostile-foreign",
                display_name="Dynamic Hostile Foreign",
                default_locale="en-US",
            )
        )
        listing_id, detail_id, selected_listing_id, selected_detail_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        type_id, title_field_id, rank_field_id, view_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        valid_item_id, excluded_item_id, draft_item_id, archived_item_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        hostile_parent_ids = {
            name: uuid4()
            for name in (
                "zero",
                "multiple",
                "non-detail",
                "malformed",
                "wrong-view",
            )
        }
        hostile_page_ids = {name: uuid4() for name in hostile_parent_ids}
        other_type_id, other_view_id, foreign_type_id, foreign_view_id = (
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
        )
        preview_user_id, preview_session_id, preview_workspace_id = (
            uuid4(),
            uuid4(),
            uuid4(),
        )
        preview_secret = b"h" * 32
        preview_public_id = f"sas2_{preview_session_id.hex}"
        expires = datetime.now(UTC) + timedelta(hours=1)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en-US',true,true,0),($1,'sl-SI',true,false,1)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en-US',true,true,0)",
                foreign_site.site_id,
            )
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id,identity_kind,oidc_issuer,oidc_subject,display_name) "
                "VALUES ($1,'OIDC','https://issuer.test',$2,'Hostile Preview User')",
                preview_user_id,
                f"subject-{preview_user_id}",
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id,user_account_id,role_key,delegation_ceiling) "
                "VALUES ($1,$2,'SITE_EDITOR',2)",
                site.site_id,
                preview_user_id,
            )
            await owner.execute(
                "INSERT INTO control.user_session "
                "(id,public_id,secret_digest,csrf_secret_digest,user_account_id,"
                "absolute_expires_at) VALUES ($1,$2,$3,$4,$5,$6)",
                preview_session_id,
                preview_public_id,
                hashlib.sha256(preview_secret).digest(),
                b"h" * 32,
                preview_user_id,
                expires,
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id,site_id,created_by,actor_type,title,delegation_preset,"
                "status,expires_at) VALUES ($1,$2,$3,'HUMAN','Hostile Preview',"
                "'L2_SITE_EDITOR','ACTIVE',$4)",
                preview_workspace_id,
                site.site_id,
                preview_user_id,
                expires,
            )
            await owner.executemany(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,$3,$4,'PUBLISHED',$5,$6,$7)",
                [
                    (listing_id, site.site_id, "news", "News", "en-US", None, None),
                    (
                        detail_id,
                        site.site_id,
                        "detail",
                        "Detail",
                        "en-US",
                        listing_id,
                        "{slug}",
                    ),
                    (
                        selected_listing_id,
                        site.site_id,
                        "news",
                        "Novice",
                        "sl-SI",
                        None,
                        None,
                    ),
                    (
                        selected_detail_id,
                        site.site_id,
                        "detail",
                        "Podrobnosti",
                        "sl-SI",
                        selected_listing_id,
                        "{slug}",
                    ),
                ]
                + [
                    (
                        hostile_parent_ids[name],
                        site.site_id,
                        name,
                        name.title(),
                        "en-US",
                        None,
                        None,
                    )
                    for name in hostile_parent_ids
                ]
                + [
                    (
                        hostile_page_ids[name],
                        site.site_id,
                        "entry",
                        f"{name.title()} entry",
                        "en-US",
                        hostile_parent_ids[name],
                        "{slug}",
                    )
                    for name in hostile_page_ids
                ],
            )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,"
                "definition_version,settings) "
                "VALUES ($1,$2,'news','{}','/news/{slug}','ACTIVE',1,'{}')",
                type_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,cardinality,"
                "position,validation,ui_options,definition_version) VALUES "
                "($1,$2,'title','Title','short_text',true,true,1,0,'{}','{}',1),"
                "($3,$2,'rank','Rank','integer',true,false,1,1,'{}','{}',1)",
                title_field_id,
                type_id,
                rank_field_id,
            )
            await owner.executemany(
                "INSERT INTO content.content_item_base "
                "(id,site_id,type_id,slug,status,type_definition_version,values) "
                "VALUES ($1,$2,$3,$4,$5,1,$6::jsonb)",
                [
                    (
                        valid_item_id,
                        site.site_id,
                        type_id,
                        "valid-item",
                        "PUBLISHED",
                        '{"rank":2}',
                    ),
                    (
                        excluded_item_id,
                        site.site_id,
                        type_id,
                        "excluded-item",
                        "PUBLISHED",
                        '{"rank":1}',
                    ),
                    (
                        draft_item_id,
                        site.site_id,
                        type_id,
                        "draft-item",
                        "DRAFT",
                        '{"rank":3}',
                    ),
                    (
                        archived_item_id,
                        site.site_id,
                        type_id,
                        "archived-item",
                        "ARCHIVED",
                        '{"rank":4}',
                    ),
                ],
            )
            await owner.executemany(
                "INSERT INTO content.content_item_translation_base "
                "(site_id,item_id,locale,localized_values) VALUES ($1,$2,$3,$4::jsonb)",
                [
                    (site.site_id, valid_item_id, "en-US", '{"title":"Valid"}'),
                    (site.site_id, valid_item_id, "sl-SI", '{"title":"Veljaven"}'),
                    (site.site_id, excluded_item_id, "en-US", '{"title":"Excluded"}'),
                    (site.site_id, draft_item_id, "en-US", '{"title":"Draft"}'),
                    (site.site_id, archived_item_id, "en-US", '{"title":"Archived"}'),
                ],
            )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,"
                "pagination_spec) VALUES ($1,$2,$3,'news',$4::jsonb,$5::jsonb,"
                "$6::jsonb,$7::jsonb)",
                view_id,
                site.site_id,
                type_id,
                '{"field":"rank","op":"gte","value":2}',
                '{"field":"rank","direction":"desc"}',
                '{"fields":["title","rank"]}',
                '{"limit":10,"offset":0}',
            )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,"
                "definition_version,settings) "
                "VALUES ($1,$2,'other','{}','/other/{slug}','ACTIVE',1,'{}')",
                other_type_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,"
                "pagination_spec) VALUES ($1,$2,$3,'other','{}','{}','{}',"
                '\'{"limit":10,"offset":0}\')',
                other_view_id,
                site.site_id,
                other_type_id,
            )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,"
                "definition_version,settings) "
                "VALUES ($1,$2,'foreign','{}','/foreign/{slug}','ACTIVE',1,'{}')",
                foreign_type_id,
                foreign_site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,"
                "pagination_spec) VALUES ($1,$2,$3,'foreign','{}','{}','{}',"
                '\'{"limit":10,"offset":0}\')',
                foreign_view_id,
                foreign_site.site_id,
                foreign_type_id,
            )
            view_props = json.dumps({"viewId": str(view_id)})
            await owner.executemany(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) "
                "VALUES ($1,$2,'CollectionDetail','1','default',$3,$4::jsonb)",
                [
                    (site.site_id, detail_id, 0, view_props),
                    (site.site_id, selected_detail_id, 0, view_props),
                    (
                        site.site_id,
                        hostile_page_ids["multiple"],
                        0,
                        view_props,
                    ),
                    (
                        site.site_id,
                        hostile_page_ids["multiple"],
                        1,
                        view_props,
                    ),
                    (site.site_id, hostile_page_ids["malformed"], 0, "{}"),
                    (
                        site.site_id,
                        hostile_page_ids["wrong-view"],
                        0,
                        json.dumps({"viewId": str(uuid4())}),
                    ),
                ],
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) "
                "VALUES ($1,$2,'Heading','1','default',0,$3::jsonb)",
                site.site_id,
                hostile_page_ids["non-detail"],
                '{"text":"Not detail","level":2}',
            )

        service = RenderProjectionService(_RenderAdapter(public_pool, preview_pool))
        render_app = FastAPI()
        install_error_handlers(render_app)
        install_render_projection_routes(
            render_app, _RenderAdapter(public_pool, preview_pool)
        )

        async def assert_http_not_found(
            path: str, *, expected_status: int = 404
        ) -> None:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                response = await client.post(
                    "/internal/render/v1/page",
                    json={"authority": "localhost", "path": path},
                )
            assert response.status_code == expected_status, (path, response.text)
            assert str(site.site_id) not in response.text
            assert str(valid_item_id) not in response.text
            assert "bindings" not in response.text

        valid = await service.canonical(
            RenderPageRequest(
                authority="localhost",
                path="/s/dynamic-hostile-matrix/news/valid-item",
            )
        )
        assert valid.route_kind == "page"
        assert valid.page.id == detail_id
        assert next(iter(valid.bindings.values()))[0]["slug"] == "valid-item"

        corrupt_navigation_id, corrupt_item_id = uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'corrupt','Corrupt','{}','{}')",
                corrupt_navigation_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4,$5,'PAGE',$6,$7,'en-US',0)",
                corrupt_item_id,
                site.site_id,
                corrupt_navigation_id,
                "00000000-0000-0000-0000-000000000000",
                detail_id,
                str(detail_id),
                '{"en-US":"Corrupt"}',
            )
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/valid-item", expected_status=503
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.navigation_item_base WHERE id=$1",
                corrupt_item_id,
            )
            await owner.execute(
                "DELETE FROM content.navigation_base WHERE id=$1",
                corrupt_navigation_id,
            )

        dangling_navigation_id, dangling_item_id = uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'dangling','Dangling','{}','{}')",
                dangling_navigation_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4,NULL,'INTERNAL','/dangling',$5,'en-US',0)",
                dangling_item_id,
                site.site_id,
                dangling_navigation_id,
                "00000000-0000-0000-0000-000000000000",
                '{"en-US":"Dangling"}',
            )
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/valid-item", expected_status=503
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.navigation_item_base WHERE id=$1",
                dangling_item_id,
            )
            await owner.execute(
                "DELETE FROM content.navigation_base WHERE id=$1",
                dangling_navigation_id,
            )
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/excluded-item")
        for name in hostile_parent_ids:
            await assert_http_not_found(f"/s/dynamic-hostile-matrix/{name}/valid-item")

        await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item/extra")
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/%2e%2e")
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/" + "a" * 256)
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/<script>alert(1)</script>"
        )
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/valid-item?query=ignored"
        )

        overlap_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,'valid-item','Overlap','PUBLISHED','en-US',$3,NULL)",
                overlap_id,
                site.site_id,
                listing_id,
            )
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/valid-item", expected_status=503
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute("DELETE FROM content.page_base WHERE id=$1", overlap_id)
        duplicate_dynamic_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,'detail-two','Detail two','PUBLISHED','en-US',$3,"
                "'{slug}')",
                duplicate_dynamic_id,
                site.site_id,
                listing_id,
            )
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/valid-item", expected_status=503
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.page_base WHERE id=$1", duplicate_dynamic_id
            )

        async def update_composition(props: str) -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE content.page_composition_base SET props=$1::jsonb "
                    "WHERE page_id=$2",
                    props,
                    detail_id,
                )

        await update_composition(json.dumps({"viewId": str(foreign_view_id)}))
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item")
        await update_composition(json.dumps({"viewId": str(other_view_id)}))
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item")
        await update_composition(json.dumps({"viewId": str(view_id)}))

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.collection_view_base SET definition_version=99 "
                "WHERE id=$1",
                view_id,
            )
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.collection_view_base SET definition_version=1 "
                "WHERE id=$1",
                view_id,
            )
            await owner.execute(
                "UPDATE content.content_item_base SET type_definition_version=99 "
                "WHERE id=$1",
                valid_item_id,
            )
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base SET type_definition_version=1 "
                "WHERE id=$1",
                valid_item_id,
            )

        for field_name, value in (
            (
                "filter_spec",
                '{"field":"title","op":"eq","value":"Valid"}',
            ),
            (
                "sort_spec",
                '{"field":"title","direction":"asc"}',
            ),
            (
                "projection_spec",
                '{"fields":["title"],"undeclared":"ignored"}',
            ),
        ):
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    f"UPDATE content.collection_view_base SET {field_name}=$1::jsonb "
                    "WHERE id=$2",
                    value,
                    view_id,
                )
            await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item")
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    f"UPDATE content.collection_view_base SET {field_name}=$1::jsonb "
                    "WHERE id=$2",
                    {
                        "filter_spec": '{"field":"rank","op":"gte","value":2}',
                        "sort_spec": '{"field":"rank","direction":"desc"}',
                        "projection_spec": '{"fields":["title","rank"]}',
                    }[field_name],
                    view_id,
                )

        session_token = format_session_token(preview_public_id, preview_secret)

        async def assert_preview_not_found(path: str) -> None:
            with pytest.raises(ProjectionError, match="not_found"):
                await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path=path,
                        workspace_id=preview_workspace_id,
                        session_token=session_token,
                    )
                )

        selected = await service.canonical(
            RenderPageRequest(
                authority="localhost",
                path="/s/dynamic-hostile-matrix/sl-si/news/valid-item",
            )
        )
        assert selected.route_kind == "page"
        assert next(iter(selected.bindings.values()))[0]["values"]["title"] == (
            "Veljaven"
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.content_item_translation_base "
                "WHERE site_id=$1 AND item_id=$2 AND locale='sl-SI'",
                site.site_id,
                valid_item_id,
            )
        fallback = await service.canonical(
            RenderPageRequest(
                authority="localhost",
                path="/s/dynamic-hostile-matrix/sl-si/news/valid-item",
            )
        )
        assert fallback.route_kind == "page"
        assert next(iter(fallback.bindings.values()))[0]["values"]["title"] == "Valid"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.content_item_translation_base "
                "WHERE site_id=$1 AND item_id=$2 AND locale='en-US'",
                site.site_id,
                valid_item_id,
            )
        await assert_http_not_found("/s/dynamic-hostile-matrix/sl-si/news/valid-item")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.content_item_translation_base "
                "(site_id,item_id,locale,localized_values) VALUES "
                "($1,$2,'en-US','{\"title\":\"Valid\"}'::jsonb)",
                site.site_id,
                valid_item_id,
            )
            await owner.execute(
                "INSERT INTO content.content_item_translation_base "
                "(site_id,item_id,locale,localized_values) VALUES "
                "($1,$2,'sl-SI','{\"title\":7}'::jsonb)",
                site.site_id,
                valid_item_id,
            )
        await assert_http_not_found("/s/dynamic-hostile-matrix/sl-si/news/valid-item")

        draft_page_id, draft_navigation_id, draft_item_id = uuid4(), uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,'draft-only','Draft only','DRAFT','en-US',NULL,NULL)",
                draft_page_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'draft-target','Draft target','{}','{}')",
                draft_navigation_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$4,NULL,'INTERNAL','/draft-only',$5,'en-US',0)",
                draft_item_id,
                site.site_id,
                draft_navigation_id,
                "00000000-0000-0000-0000-000000000000",
                '{"en-US":"Draft"}',
            )
        await assert_http_not_found(
            "/s/dynamic-hostile-matrix/news/valid-item", expected_status=503
        )
        preview_with_draft = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path="/s/dynamic-hostile-matrix/news/valid-item",
                workspace_id=preview_workspace_id,
                session_token=session_token,
            )
        )
        assert preview_with_draft.route_kind == "page"
        assert any(
            item.target.value == "/draft-only"
            for navigation in preview_with_draft.navigation
            for item in navigation.items
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "DELETE FROM content.navigation_item_base WHERE id=$1", draft_item_id
            )
            await owner.execute(
                "DELETE FROM content.navigation_base WHERE id=$1", draft_navigation_id
            )
            await owner.execute(
                "DELETE FROM content.page_base WHERE id=$1", draft_page_id
            )

        for slug in ("draft-item", "archived-item", "unknown-item"):
            await assert_http_not_found(f"/s/dynamic-hostile-matrix/news/{slug}")
        await assert_preview_not_found("/s/dynamic-hostile-matrix/news/archived-item")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base SET status='UNKNOWN' WHERE id=$1",
                valid_item_id,
            )
        await assert_http_not_found("/s/dynamic-hostile-matrix/news/valid-item")
        await assert_preview_not_found("/s/dynamic-hostile-matrix/news/valid-item")

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_item_base SET status='PUBLISHED' WHERE id=$1",
                valid_item_id,
            )
            await owner.execute(
                "UPDATE content.content_item_translation_base SET localized_values="
                '\'{"title":"Valid"}\'::jsonb WHERE site_id=$1 AND item_id=$2 '
                "AND locale='en-US'",
                site.site_id,
                valid_item_id,
            )

        async with public_pool.acquire(timeout=3) as connection:
            assert not connection.is_in_transaction()
            assert await connection.fetchval("SELECT 1") == 1
        async with preview_pool.acquire(timeout=3) as connection:
            assert not connection.is_in_transaction()
            assert await connection.fetchval("SELECT 1") == 1
    finally:
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_public_agent_cow_structure_is_visible_only_to_authorized_preview(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drive the structural state through public Agent HTTP before previewing it."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="agent-structure-router",
                display_name="Agent Structure Router",
                default_locale="en",
            )
        )
        other_site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="agent-structure-router-other",
                display_name="Other Structure Router",
                default_locale="en",
            )
        )
        user_id, session_id = uuid4(), uuid4()
        workspace_id = uuid4()
        other_workspace_id = uuid4()
        canonical_navigation_id = uuid4()
        secret = b"r" * 32
        public_id = f"sas2_{session_id.hex}"
        scopes = [
            "site:read",
            "page:create",
            "page:read",
            "page:write",
            "page:delete",
            "page:move",
            "page:restore",
            "route:write",
            "locale:configure",
            "navigation:read",
            "navigation:create",
            "navigation:write",
            "navigation:delete",
            "redirect:create",
        ]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($2,'en',true,true,0) "
                "ON CONFLICT (site_id,tag) DO NOTHING",
                site.site_id,
                other_site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(site_id,slug,title,status,locale) "
                "VALUES ($1,'home','Other home','PUBLISHED','en')",
                other_site.site_id,
            )
            canonical_page_id = await owner.fetchval(
                "INSERT INTO content.page_base "
                "(site_id,slug,title,status,locale) VALUES "
                "($1,'canonical','Canonical before','PUBLISHED','en') "
                "RETURNING id",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'zz-canonical','Canonical', $3::jsonb, '{}'::jsonb)",
                canonical_navigation_id,
                site.site_id,
                '{"en":"Canonical"}',
            )
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id,identity_kind,oidc_issuer,oidc_subject,display_name) "
                "VALUES ($1,'OIDC','https://agent-router.test',$2,"
                "'Agent Router User')",
                user_id,
                str(user_id),
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id,user_account_id,role_key,delegation_ceiling) "
                "VALUES ($1,$2,'SITE_OWNER',4)",
                site.site_id,
                user_id,
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id,user_account_id,role_key,delegation_ceiling) "
                "VALUES ($1,$2,'SITE_OWNER',4)",
                other_site.site_id,
                user_id,
            )
            await owner.execute(
                "INSERT INTO control.user_session "
                "(id,public_id,secret_digest,csrf_secret_digest,user_account_id,"
                "absolute_expires_at) VALUES ($1,$2,$3,$4,$5,$6)",
                session_id,
                public_id,
                hashlib.sha256(secret).digest(),
                b"c" * 32,
                user_id,
                datetime.now(UTC) + timedelta(hours=1),
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id,site_id,created_by,delegator_id,actor_type,title,"
                "delegation_preset,effective_scopes,status,expires_at) VALUES "
                "($1,$2,$3,$3,'AGENT','Agent Router','L4',$4::jsonb,'ACTIVE',$5)",
                workspace_id,
                site.site_id,
                user_id,
                json.dumps(scopes),
                datetime.now(UTC) + timedelta(hours=1),
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id,site_id,created_by,actor_type,title,delegation_preset,"
                "effective_scopes,status,expires_at) VALUES "
                "($1,$2,$3,'HUMAN','Other workspace','L2',"
                "'[\"preview:inspect\"]'::jsonb,'ACTIVE',$4)",
                other_workspace_id,
                other_site.site_id,
                user_id,
                datetime.now(UTC) + timedelta(hours=1),
            )
            token, capability_public_id, digest = generate_capability_token()
            await owner.execute(
                "INSERT INTO control.capability "
                "(workspace_id,public_id,secret_digest,scopes,expires_at,"
                "request_quota,mutation_quota,delete_quota) "
                "VALUES ($1,$2,$3,$4::jsonb,$5,100,100,100)",
                workspace_id,
                capability_public_id,
                digest,
                json.dumps(scopes),
                datetime.now(UTC) + timedelta(minutes=30),
            )
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        headers = {"Authorization": f"Bearer {token}"}
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                locale = await client.post(
                    "/api/agent/v1/locales",
                    headers={**headers, "Idempotency-Key": "router-locale"},
                    json={"tag": "sl-SI", "position": 1},
                )
                assert locale.status_code == 201, locale.text
                root = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "router-root"},
                    json={"slug": "home", "title": "Home", "locale": "en"},
                )
                assert root.status_code == 201, root.text
                root_id = root.json()["record"]["id"]
                nested = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "router-nested"},
                    json={
                        "slug": "guide",
                        "title": "Guide",
                        "locale": "en",
                        "parent_id": root_id,
                    },
                )
                assert nested.status_code == 201, nested.text
                nested_id = nested.json()["record"]["id"]
                sl_root = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "router-sl-root"},
                    json={"slug": "home", "title": "Domov", "locale": "sl-SI"},
                )
                assert sl_root.status_code == 201, sl_root.text
                sl_nested = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "router-sl-nested"},
                    json={
                        "slug": "guide",
                        "title": "Vodnik",
                        "locale": "sl-SI",
                        "parent_id": sl_root.json()["record"]["id"],
                    },
                )
                assert sl_nested.status_code == 201, sl_nested.text
                sl_nested_id = sl_nested.json()["record"]["id"]
                navigation = await client.post(
                    "/api/agent/v1/navigation",
                    headers={**headers, "Idempotency-Key": "router-navigation"},
                    json={
                        "key": "primary",
                        "label": "Primary",
                        "labels": {"sl-SI": "Glavni meni"},
                    },
                )
                assert navigation.status_code == 201, navigation.text
                navigation_id = navigation.json()["record"]["id"]
                first_item = await client.post(
                    f"/api/agent/v1/navigation/{navigation_id}/items",
                    headers={**headers, "Idempotency-Key": "router-nav-first"},
                    json={
                        "target_kind": "PAGE",
                        "target_value": root_id,
                        "page_id": root_id,
                        "labels": {"en": "Home", "sl-SI": "Domov"},
                    },
                )
                assert first_item.status_code == 201, first_item.text
                second_item = await client.post(
                    f"/api/agent/v1/navigation/{navigation_id}/items",
                    headers={**headers, "Idempotency-Key": "router-nav-second"},
                    json={
                        "target_kind": "PAGE",
                        "target_value": nested_id,
                        "page_id": nested_id,
                        "labels": {"en": "Guide", "sl-SI": "Vodnik"},
                    },
                )
                assert second_item.status_code == 201, second_item.text
                moved = await client.post(
                    "/api/agent/v1/navigation-items/"
                    f"{second_item.json()['record']['id']}:move",
                    headers={**headers, "Idempotency-Key": "router-nav-move"},
                    json={
                        "parent_id": None,
                        "before_item_id": first_item.json()["record"]["id"],
                        "expected_row_version": 1,
                    },
                )
                assert moved.status_code == 200, moved.text
                redirect = await client.post(
                    "/api/agent/v1/redirects",
                    headers={**headers, "Idempotency-Key": "router-redirect"},
                    json={
                        "source_route": "/legacy",
                        "target": "/guide",
                        "status_code": 307,
                    },
                )
                assert redirect.status_code == 201, redirect.text
                switched = await client.patch(
                    f"/api/agent/v1/locales/{locale.json()['record']['id']}",
                    headers={**headers, "Idempotency-Key": "router-default"},
                    json={"is_default": True, "expected_row_version": 1},
                )
                assert switched.status_code == 200, switched.text

        service = RenderProjectionService(_RenderAdapter(public_pool, preview_pool))
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/agent-structure-router/"
                )
            )
        preview = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path="/s/agent-structure-router/",
                workspace_id=workspace_id,
                session_token=format_session_token(public_id, secret),
            )
        )
        assert preview.route_kind == "page"
        assert preview.page.title == "Domov"
        assert preview.page.effective_route == "/"
        assert preview.locale == "sl-SI"
        assert [item.position for item in preview.navigation[0].items] == [0, 1]
        nested_preview = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path="/s/agent-structure-router/guide",
                workspace_id=workspace_id,
                session_token=format_session_token(public_id, secret),
            )
        )
        assert nested_preview.route_kind == "page"
        assert nested_preview.page.title == "Vodnik"
        assert nested_preview.page.effective_route == "/guide"
        other_before = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path=f"/s/{other_site.site_key}/",
                workspace_id=other_workspace_id,
                session_token=format_session_token(public_id, secret),
            )
        )
        assert other_before.route_kind == "page"
        assert other_before.page.title == "Other home"
        preview_redirect = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path="/s/agent-structure-router/legacy",
                workspace_id=workspace_id,
                session_token=format_session_token(public_id, secret),
            )
        )
        assert preview_redirect.route_kind == "redirect"
        assert preview_redirect.redirect.status_code == 307
        assert preview_redirect.redirect.target == (
            f"/preview/{workspace_id}/s/agent-structure-router/guide"
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                snapshot_established = asyncio.Event()
                release_snapshot = asyncio.Event()
                original_query = service._query

                async def paused_query(connection: Any, **kwargs: Any) -> Any:
                    context = kwargs["context"]
                    await connection.fetch(
                        "SELECT * FROM content.slaif_render_page_resolve($1,$2,$3,$4)",
                        context.site_id,
                        "/guide",
                        "en",
                        ["PUBLISHED", "DRAFT"],
                    )
                    snapshot_established.set()
                    await release_snapshot.wait()
                    return await original_query(connection, **kwargs)

                monkeypatch.setattr(service, "_query", paused_query)
                snapshot_task = asyncio.create_task(
                    service.preview(
                        RenderPreviewRequest(
                            authority="localhost",
                            path="/s/agent-structure-router/guide",
                            workspace_id=workspace_id,
                            session_token=format_session_token(public_id, secret),
                        )
                    )
                )
                await asyncio.wait_for(snapshot_established.wait(), timeout=5)
                page_task = asyncio.create_task(
                    client.patch(
                        f"/api/agent/v1/pages/{sl_nested_id}",
                        headers={
                            **headers,
                            "Idempotency-Key": "router-snapshot-page",
                        },
                        json={"title": "Vodnik after", "expected_row_version": 1},
                    )
                )
                navigation_task = asyncio.create_task(
                    client.patch(
                        f"/api/agent/v1/navigation/{navigation_id}",
                        headers={
                            **headers,
                            "Idempotency-Key": "router-snapshot-navigation",
                        },
                        json={
                            "labels": {"sl-SI": "Glavni meni after"},
                            "expected_row_version": 1,
                        },
                    )
                )
                redirect_task = asyncio.create_task(
                    client.post(
                        "/api/agent/v1/redirects",
                        headers={
                            **headers,
                            "Idempotency-Key": "router-snapshot-redirect",
                        },
                        json={
                            "source_route": "/after",
                            "target": "/guide",
                            "status_code": 301,
                        },
                    )
                )
                page_update, navigation_update, redirect_after = await asyncio.gather(
                    page_task, navigation_task, redirect_task
                )
                assert page_update.status_code == 200, page_update.text
                assert navigation_update.status_code == 200, navigation_update.text
                assert redirect_after.status_code == 201, redirect_after.text
                release_snapshot.set()
                snapshot_projection = await asyncio.wait_for(snapshot_task, timeout=5)
                assert snapshot_projection.route_kind == "page"
                assert snapshot_projection.page.title == "Vodnik"
                assert snapshot_projection.navigation[0].label == "Glavni meni"
                monkeypatch.setattr(service, "_query", original_query)
                fresh_projection = await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path="/s/agent-structure-router/guide",
                        workspace_id=workspace_id,
                        session_token=format_session_token(public_id, secret),
                    )
                )
                assert fresh_projection.route_kind == "page"
                assert fresh_projection.page.title == "Vodnik after"
                assert fresh_projection.navigation[0].label == "Glavni meni after"
                fresh_redirect = await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path="/s/agent-structure-router/after",
                        workspace_id=workspace_id,
                        session_token=format_session_token(public_id, secret),
                    )
                )
                assert fresh_redirect.route_kind == "redirect"
                assert fresh_redirect.redirect.status_code == 301

                canonical_snapshot_established = asyncio.Event()
                canonical_release_snapshot = asyncio.Event()

                async def paused_canonical_query(connection: Any, **kwargs: Any) -> Any:
                    context = kwargs["context"]
                    await connection.fetchrow(
                        "SELECT "
                        "(SELECT count(*) FROM content.site_locale WHERE site_id=$1),"
                        "(SELECT count(*) FROM content.navigation WHERE site_id=$1),"
                        "(SELECT count(*) FROM content.redirect WHERE site_id=$1),"
                        "(SELECT count(*) FROM content.slaif_render_page_resolve("
                        "$1,'/canonical',$2,$3))",
                        context.site_id,
                        "en",
                        ["PUBLISHED"],
                    )
                    canonical_snapshot_established.set()
                    await canonical_release_snapshot.wait()
                    return await original_query(connection, **kwargs)

                monkeypatch.setattr(service, "_query", paused_canonical_query)
                canonical_snapshot_task = asyncio.create_task(
                    service.canonical(
                        RenderPageRequest(
                            authority="localhost",
                            path="/s/agent-structure-router/canonical",
                        )
                    )
                )
                await asyncio.wait_for(canonical_snapshot_established.wait(), timeout=5)
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    async with owner.transaction():
                        await owner.execute(
                            "UPDATE content.page_base SET title='Canonical after' "
                            "WHERE id=$1",
                            canonical_page_id,
                        )
                        await owner.execute(
                            "UPDATE content.navigation_base "
                            "SET labels=jsonb_set(labels,'{en}',to_jsonb($1::text)) "
                            "WHERE id=$2",
                            "Canonical after",
                            canonical_navigation_id,
                        )
                        await owner.execute(
                            "INSERT INTO content.redirect_base "
                            "(site_id,source_route,target,status_code,locale) "
                            "VALUES ($1,'/canonical-after','/canonical',302,NULL)",
                            site.site_id,
                        )
                canonical_release_snapshot.set()
                canonical_snapshot = await asyncio.wait_for(
                    canonical_snapshot_task, timeout=5
                )
                assert canonical_snapshot.route_kind == "page"
                assert canonical_snapshot.page.title == "Canonical before"
                assert canonical_snapshot.navigation[0].label == "Canonical"
                monkeypatch.setattr(service, "_query", original_query)
                canonical_after = await service.canonical(
                    RenderPageRequest(
                        authority="localhost",
                        path="/s/agent-structure-router/canonical-after",
                    )
                )
                assert canonical_after.route_kind == "redirect"
                assert canonical_after.redirect.status_code == 302

                async with public_pool.acquire() as read_committed:
                    async with read_committed.transaction(isolation="read_committed"):
                        read_before = await read_committed.fetchval(
                            "SELECT title FROM content.page WHERE id=$1",
                            canonical_page_id,
                        )
                        async with owner_connection(
                            database.settings.resolved_owner_dsn(),
                            expected_database=database.name,
                        ) as owner:
                            async with owner.transaction():
                                await owner.execute(
                                    "UPDATE content.page_base "
                                    "SET title='Canonical newest' "
                                    "WHERE id=$1",
                                    canonical_page_id,
                                )
                                await owner.execute(
                                    "UPDATE content.navigation_base "
                                    "SET labels=jsonb_set(labels,'{en}',"
                                    "to_jsonb($1::text)) "
                                    "WHERE id=$2",
                                    "Canonical newest",
                                    canonical_navigation_id,
                                )
                        read_after = await read_committed.fetchval(
                            "SELECT labels->>'en' FROM content.navigation WHERE id=$1",
                            canonical_navigation_id,
                        )
                        assert read_before == "Canonical after"
                        assert read_after == "Canonical newest"
                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        await owner.execute(
                            "UPDATE content.page_base SET title='Canonical before' "
                            "WHERE id=$1",
                            canonical_page_id,
                        )
                        await owner.execute(
                            "UPDATE content.navigation_base "
                            "SET labels=jsonb_set(labels,'{en}',to_jsonb($1::text)) "
                            "WHERE id=$2",
                            "Canonical",
                            canonical_navigation_id,
                        )
                        await owner.execute(
                            "DELETE FROM content.redirect_base "
                            "WHERE site_id=$1 AND source_route='/canonical-after'",
                            site.site_id,
                        )
                section = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "router-section"},
                    json={"slug": "section", "title": "Section", "locale": "en"},
                )
                assert section.status_code == 201, section.text
                section_id = section.json()["record"]["id"]
                moved_page = await client.post(
                    f"/api/agent/v1/pages/{nested_id}:move",
                    headers={**headers, "Idempotency-Key": "router-page-move"},
                    json={"parent_id": section_id, "expected_row_version": 1},
                )
                assert moved_page.status_code == 200, moved_page.text
                moved_preview = await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path="/s/agent-structure-router/en/section/guide",
                        locale="en",
                        workspace_id=workspace_id,
                        session_token=format_session_token(public_id, secret),
                    )
                )
                assert moved_preview.route_kind == "page"
                assert moved_preview.page.id == UUID(nested_id)
                assert moved_preview.page.parent_id == UUID(section_id)
                assert moved_preview.page.effective_route == "/en/section/guide"
                with pytest.raises(ProjectionError, match="not_found"):
                    await service.canonical(
                        RenderPageRequest(
                            authority="localhost",
                            path="/s/agent-structure-router/en/section/guide",
                        )
                    )

                removed_item = await client.request(
                    "DELETE",
                    f"/api/agent/v1/navigation-items/"
                    f"{second_item.json()['record']['id']}",
                    headers={
                        **headers,
                        "Idempotency-Key": "router-nav-delete-before-page",
                    },
                    json={"expected_row_version": 2},
                )
                assert removed_item.status_code == 200, removed_item.text
                deleted = await client.request(
                    "DELETE",
                    f"/api/agent/v1/pages/{nested_id}",
                    headers={**headers, "Idempotency-Key": "router-page-delete"},
                    json={"expected_row_version": 2},
                )
                assert deleted.status_code == 200, deleted.text
                assert deleted.json()["record"]["row_version"] == 3
                with pytest.raises(ProjectionError, match="not_found"):
                    await service.preview(
                        RenderPreviewRequest(
                            authority="localhost",
                            path="/s/agent-structure-router/en/section/guide",
                            locale="en",
                            workspace_id=workspace_id,
                            session_token=format_session_token(public_id, secret),
                        )
                    )
                restored = await client.post(
                    f"/api/agent/v1/pages/{nested_id}:restore",
                    headers={**headers, "Idempotency-Key": "router-page-restore"},
                    json={"expected_row_version": 3},
                )
                assert restored.status_code == 200, restored.text
                assert restored.json()["record"]["row_version"] == 4
                restored_preview = await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path="/s/agent-structure-router/en/section/guide",
                        locale="en",
                        workspace_id=workspace_id,
                        session_token=format_session_token(public_id, secret),
                    )
                )
                assert restored_preview.route_kind == "page"
                assert restored_preview.page.id == UUID(nested_id)
                assert restored_preview.page.effective_route == "/en/section/guide"
                other_after = await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path=f"/s/{other_site.site_key}/",
                        workspace_id=other_workspace_id,
                        session_token=format_session_token(public_id, secret),
                    )
                )
                assert other_after.route_kind == "page"
                assert other_after.page.title == other_before.page.title
                with pytest.raises(ProjectionError, match="not_found"):
                    await service.canonical(
                        RenderPageRequest(
                            authority="localhost",
                            path="/s/agent-structure-router/en/section/guide",
                        )
                    )

                with pytest.raises(ProjectionError, match="not_found"):
                    await service.preview(
                        RenderPreviewRequest(
                            authority="localhost",
                            path="/s/agent-structure-router/",
                            workspace_id=uuid4(),
                            session_token=format_session_token(public_id, secret),
                        )
                    )
    finally:
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_navigation_corruption_fails_closed_without_partial_projection(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="corrupt-navigation-router",
                display_name="Corrupt Navigation Router",
                default_locale="en",
            )
        )
        page_id, navigation_id, item_id = uuid4(), uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) "
                "VALUES ($1,'en',true,true,0)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale) "
                "VALUES ($1,$2,'home','Home','PUBLISHED','en')",
                page_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) "
                "VALUES ($1,$2,'primary','Primary','{\"en\":\"Primary\"}'::jsonb,'{}')",
                navigation_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,"
                "target_kind,target_value,labels,locale,position) "
                "VALUES ($1,$2,$3,NULL,$4::uuid,$5,'PAGE',$6,"
                '\'{"en":"Home"}\'::jsonb,NULL,0)',
                item_id,
                site.site_id,
                navigation_id,
                "00000000-0000-0000-0000-000000000000",
                page_id,
                str(page_id),
            )
        service = RenderProjectionService(_RenderAdapter(public_pool))
        baseline = await service.canonical(
            RenderPageRequest(
                authority="localhost", path="/s/corrupt-navigation-router/"
            )
        )
        assert baseline.route_kind == "page"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.navigation_item_base SET labels='{}'::jsonb "
                "WHERE id=$1",
                item_id,
            )
        with pytest.raises(ProjectionError, match="navigation_label"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/corrupt-navigation-router/"
                )
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.navigation_item_base SET "
                'labels=\'{"en":"Home"}\'::jsonb, '
                "position=1 WHERE id=$1",
                item_id,
            )
        with pytest.raises(ProjectionError, match="navigation_position"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/corrupt-navigation-router/"
                )
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.navigation_item_base SET position=0,"
                "target_kind='INTERNAL',target_value='//unsafe' WHERE id=$1",
                item_id,
            )
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/corrupt-navigation-router/"
                )
            )
    finally:
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_navigation_corruption_matrix_fails_closed(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Corrupt every static structure edge and require a bounded failure."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="corrupt-navigation-matrix",
                display_name="Corrupt Navigation Matrix",
                default_locale="en",
            )
        )
        page_id, other_page_id, dynamic_page_id = uuid4(), uuid4(), uuid4()
        navigation_id, other_navigation_id = uuid4(), uuid4()
        item_id, second_item_id, other_item_id = uuid4(), uuid4(), uuid4()
        depth_ids = [uuid4() for _ in range(10)]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($1,'sl-SI',true,false,1)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,route_template) VALUES "
                "($1,$2,'home','Home','PUBLISHED','en',NULL),"
                "($3,$2,'other','Other','PUBLISHED','en',NULL),"
                "($4,$2,'dynamic','Dynamic','PUBLISHED','en','{slug}')",
                page_id,
                site.site_id,
                other_page_id,
                dynamic_page_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_base "
                "(id,site_id,key,label,labels,settings) VALUES "
                "($1,$2,'primary','Primary','{\"en\":\"Primary\"}'::jsonb,'{}'),"
                "($3,$2,'secondary','Secondary','{\"en\":\"Secondary\"}'::jsonb,'{}')",
                navigation_id,
                site.site_id,
                other_navigation_id,
            )
            await owner.execute(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,NULL,$6::uuid,$4,'PAGE',$5,'{\"en\":\"Home\"}',NULL,0),"
                "($7,$2,$3,NULL,$6::uuid,$8,'PAGE',$9,'{\"en\":\"Other\"}',NULL,1),"
                "($10,$2,$11,NULL,$6::uuid,NULL,'EXTERNAL',"
                "'https://example.test/other','{\"en\":\"Other\"}',NULL,0)",
                item_id,
                site.site_id,
                navigation_id,
                page_id,
                str(page_id),
                "00000000-0000-0000-0000-000000000000",
                second_item_id,
                other_page_id,
                str(other_page_id),
                other_item_id,
                other_navigation_id,
            )
        service = RenderProjectionService(_RenderAdapter(public_pool))
        request = RenderPageRequest(
            authority="localhost", path="/s/corrupt-navigation-matrix/"
        )
        baseline = await service.canonical(request)
        assert baseline.route_kind == "page"

        async def corrupt(sql: str, *args: object) -> None:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(sql, *args)

        await corrupt(
            "ALTER TABLE content.navigation_item_base DROP CONSTRAINT "
            "navigation_item_sibling_position"
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET labels='{}'::jsonb WHERE id=$1",
            item_id,
        )
        with pytest.raises(ProjectionError, match="navigation_label"):
            await service.canonical(request)
        await corrupt(
            'UPDATE content.navigation_item_base SET labels=\'{"en":"Home"}\'::jsonb '
            "WHERE id=$1",
            item_id,
        )

        await corrupt(
            "UPDATE content.navigation_item_base SET position=0 WHERE id=$1",
            second_item_id,
        )
        with pytest.raises(ProjectionError, match="navigation_position"):
            await service.canonical(request)
        await corrupt(
            "UPDATE content.navigation_item_base SET position=1 WHERE id=$1",
            second_item_id,
        )

        await corrupt(
            "UPDATE content.navigation_item_base SET page_id=NULL,target_value=$2 "
            "WHERE id=$1",
            item_id,
            str(uuid4()),
        )
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(request)
        await corrupt(
            "UPDATE content.navigation_item_base SET "
            "page_id=$2::uuid,target_value=$2::text "
            "WHERE id=$1",
            item_id,
            page_id,
        )

        await corrupt(
            "UPDATE content.navigation_item_base SET target_kind='INTERNAL',"
            "page_id=NULL,target_value='//unsafe' WHERE id=$1",
            item_id,
        )
        with pytest.raises(ProjectionError, match="unavailable"):
            await service.canonical(request)
        await corrupt(
            "UPDATE content.navigation_item_base SET target_kind='EXTERNAL',"
            "page_id=NULL,target_value='http://unsafe.test' WHERE id=$1",
            item_id,
        )
        with pytest.raises(ProjectionError, match="navigation_target"):
            await service.canonical(request)
        await corrupt(
            "UPDATE content.navigation_item_base SET target_kind='PAGE',"
            "page_id=$2::uuid,target_value=$2::text WHERE id=$1",
            item_id,
            page_id,
        )

        await corrupt(
            "UPDATE content.navigation_item_base SET parent_id=$2,parent_key=$2 "
            "WHERE id=$1",
            item_id,
            other_item_id,
        )
        with pytest.raises(ProjectionError, match="navigation_parent"):
            await service.canonical(request)
        await corrupt(
            "UPDATE content.navigation_item_base SET parent_id=NULL,parent_key=$2 "
            "WHERE id=$1",
            item_id,
            "00000000-0000-0000-0000-000000000000",
        )

        await corrupt(
            "ALTER TABLE content.navigation_item_base DISABLE TRIGGER "
            "navigation_item_parent_guard"
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET parent_id=$2,parent_key=$2,"
            "position=0 WHERE id=$1",
            item_id,
            second_item_id,
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET parent_id=$2,parent_key=$2,"
            "position=0 WHERE id=$1",
            second_item_id,
            item_id,
        )
        await corrupt(
            "ALTER TABLE content.navigation_item_base ENABLE TRIGGER "
            "navigation_item_parent_guard"
        )
        with pytest.raises(ProjectionError, match="navigation_(cycle|unreachable)"):
            await service.canonical(request)
        await corrupt(
            "ALTER TABLE content.navigation_item_base DISABLE TRIGGER "
            "navigation_item_parent_guard"
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET parent_id=NULL,parent_key=$2 "
            "WHERE id=$1",
            item_id,
            "00000000-0000-0000-0000-000000000000",
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET parent_id=NULL,parent_key=$2 "
            "WHERE id=$1",
            second_item_id,
            "00000000-0000-0000-0000-000000000000",
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET position=1 WHERE id=$1",
            second_item_id,
        )
        await corrupt(
            "ALTER TABLE content.navigation_item_base ENABLE TRIGGER "
            "navigation_item_parent_guard"
        )

        await corrupt(
            "ALTER TABLE content.navigation_item_base DROP CONSTRAINT "
            "navigation_item_labels_bounded"
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET labels=$2::jsonb WHERE id=$1",
            item_id,
            json.dumps({"en": "x" * 17_000}),
        )
        with pytest.raises(ProjectionError, match="navigation_label"):
            await service.canonical(request)
        await corrupt(
            'UPDATE content.navigation_item_base SET labels=\'{"en":"Home"}\'::jsonb '
            "WHERE id=$1",
            item_id,
        )

        await corrupt(
            "UPDATE content.site_locale_base SET enabled=false "
            "WHERE site_id=$1 AND tag='sl-SI'",
            site.site_id,
        )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost", path="/s/corrupt-navigation-matrix/sl-si/"
                )
            )

        await corrupt(
            "UPDATE content.navigation_item_base SET locale='sl-SI' WHERE id=$1",
            item_id,
        )
        await corrupt(
            "UPDATE content.site_locale_base SET enabled=false "
            "WHERE site_id=$1 AND tag='sl-SI'",
            site.site_id,
        )
        with pytest.raises(ProjectionError, match="navigation_locale"):
            await service.canonical(request)
        await corrupt(
            "UPDATE content.site_locale_base SET enabled=true WHERE site_id=$1 "
            "AND tag='sl-SI'",
            site.site_id,
        )
        await corrupt(
            "UPDATE content.navigation_item_base SET locale=NULL WHERE id=$1", item_id
        )

        await corrupt("DROP INDEX content.site_locale_one_default")
        await corrupt(
            "UPDATE content.site_locale_base SET is_default=true "
            "WHERE site_id=$1 AND tag='sl-SI'",
            site.site_id,
        )
        with pytest.raises(ProjectionError, match="locale_state"):
            await service.canonical(request)

        await corrupt(
            "UPDATE content.site_locale_base SET is_default=false "
            "WHERE site_id=$1 AND tag='sl-SI'",
            site.site_id,
        )
        await corrupt(
            "UPDATE content.site_locale_base SET is_default=true "
            "WHERE site_id=$1 AND tag='en'",
            site.site_id,
        )

        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(
                    authority="localhost",
                    path="/s/corrupt-navigation-matrix/dynamic/foo",
                )
            )

        await corrupt(
            "ALTER TABLE content.navigation_item_base DISABLE TRIGGER "
            "navigation_item_parent_guard"
        )
        for index, depth_id in enumerate(depth_ids):
            parent_id = depth_ids[index - 1] if index else None
            parent_key = parent_id or UUID("00000000-0000-0000-0000-000000000000")
            await corrupt(
                "INSERT INTO content.navigation_item_base "
                "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
                "target_value,labels,locale,position) VALUES "
                "($1,$2,$3,$4,$5,NULL,'EXTERNAL','https://example.test/depth',"
                '\'{"en":"Depth"}\'::jsonb,$6,$7)',
                depth_id,
                site.site_id,
                navigation_id,
                parent_id,
                parent_key,
                None,
                2 if index == 0 else 0,
            )
        await corrupt(
            "ALTER TABLE content.navigation_item_base ENABLE TRIGGER "
            "navigation_item_parent_guard"
        )
        with pytest.raises(ProjectionError, match="navigation_(cycle|unreachable)"):
            await service.canonical(request)
        await corrupt(
            "DELETE FROM content.navigation_item_base WHERE id=ANY($1::uuid[])",
            depth_ids,
        )

        await corrupt(
            "INSERT INTO content.navigation_item_base "
            "(id,site_id,navigation_id,parent_id,parent_key,page_id,target_kind,"
            "target_value,labels,locale,position) "
            "SELECT gen_random_uuid(),$1,$2,NULL,$3,NULL,'EXTERNAL',"
            "'https://example.test/count','{\"en\":\"Count\"}'::jsonb,NULL,g "
            "FROM generate_series(2,258) AS g",
            site.site_id,
            navigation_id,
            "00000000-0000-0000-0000-000000000000",
        )
        with pytest.raises(ProjectionError, match="navigation_too_large"):
            await service.canonical(request)
    finally:
        await public_pool.close()
        await control_pool.close()

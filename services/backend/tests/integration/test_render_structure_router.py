"""Real PostgreSQL evidence for the bounded static Render structure router."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    RenderPreviewRequest,
    RenderProjectionService,
)
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
async def test_public_agent_cow_structure_is_visible_only_to_authorized_preview(
    agent_site_database: AgentSiteDatabase,
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
        user_id, session_id = uuid4(), uuid4()
        workspace_id = uuid4()
        secret = b"r" * 32
        public_id = f"sas2_{session_id.hex}"
        scopes = [
            "site:read",
            "page:create",
            "page:read",
            "locale:configure",
            "navigation:read",
            "navigation:create",
            "navigation:write",
            "redirect:create",
        ]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0) ON CONFLICT (site_id,tag) DO NOTHING",
                site.site_id,
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
            token, capability_public_id, digest = generate_capability_token()
            await owner.execute(
                "INSERT INTO control.capability "
                "(workspace_id,public_id,secret_digest,scopes,expires_at,"
                "request_quota,mutation_quota) VALUES ($1,$2,$3,$4::jsonb,$5,100,100)",
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
    finally:
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()

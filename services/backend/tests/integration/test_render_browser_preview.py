"""Real Render proof for one-time run-bound browser preview credentials."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
import slaif_agent_site.render_api.projection as projection_module
from conftest import AgentSiteDatabase, AsyncpgExecutor
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.browser_service import BEGIN_SQL
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.browser_contracts import (
    BrowserEvidence,
    BrowserTarget,
    preview_run_request_digest,
)
from slaif_agent_site.browser_preview_credentials import (
    BrowserPreviewCredentialSigner,
    BrowserSigningKey,
)
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.render_api.app import create_app as create_render_app
from slaif_agent_site.render_api.projection import (
    ProjectionError,
    RenderPageRequest,
    RenderPreviewRequest,
    RenderProjectionService,
)
from slaif_agent_site.sites import CreateSiteRequest
from slaif_agent_site.sites.resolver import SiteResolver
from slaif_agent_site.sites.service import SiteService
from test_agent_browser_http import (
    _capability as _agent_capability,
)
from test_agent_browser_http import (
    _settings as _agent_settings,
)
from test_agent_browser_http import (
    _site as _agent_site,
)
from test_agent_browser_http import (
    _user as _agent_user,
)
from test_agent_browser_http import (
    _workspace as _agent_workspace,
)

ROUTE = "/s/browser-preview"
EVIDENCE = (BrowserEvidence.SCREENSHOT, BrowserEvidence.HEADING_SUMMARY)
ARTIFACT_BYTES = 5_505_024
DURATION_SECONDS = 120
CLAIM_SQL = "SELECT * FROM control.slaif_agent_browser_run_claim($1,$2)"
COMPLETE_SQL = "SELECT control.slaif_agent_browser_run_complete($1,$2,$3,$4,$5,$6)"


class _RenderAdapter:
    def __init__(self, public_pool: Any, preview_pool: Any) -> None:
        self._public_pool = public_pool
        self._preview_pool = preview_pool
        self._resolver = SiteResolver(public_pool)
        self.acquire_timeout = 3.0

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    def resolver(self) -> SiteResolver:
        return self._resolver

    def public_pool(self) -> Any:
        return self._public_pool

    def preview_pool(self) -> Any:
        return self._preview_pool


async def _begin(
    connection: asyncpg.Connection[Any],
    *,
    capability_id: UUID,
    site_id: UUID,
    workspace_id: UUID,
    delegator_id: UUID,
    key: str,
    route: str = ROUTE,
) -> UUID:
    request = {
        "version": "browser-preview/v1",
        "route": route,
        "target": "desktop-chromium",
        "evidence": [item.value for item in EVIDENCE],
    }
    run_id, operation_id = uuid4(), uuid4()
    row = await connection.fetchrow(
        BEGIN_SQL,
        capability_id,
        site_id,
        workspace_id,
        delegator_id,
        key,
        preview_run_request_digest(request),
        operation_id,
        run_id,
        "browser-preview/v1",
        route,
        hashlib.sha256(route.encode()).hexdigest(),
        "desktop-chromium",
        [item.value for item in EVIDENCE],
        1,
        ARTIFACT_BYTES,
        1,
        DURATION_SECONDS,
    )
    assert row is not None and row["result"] == "STARTED"
    return run_id


def _token(
    signer: BrowserPreviewCredentialSigner,
    *,
    capability_id: UUID,
    site_id: UUID,
    workspace_id: UUID,
    run_id: UUID,
    now: int,
    route: str = ROUTE,
    nonce: str | None = None,
    target: BrowserTarget = BrowserTarget.DESKTOP_CHROMIUM,
    evidence: tuple[BrowserEvidence, ...] = EVIDENCE,
    artifact_bytes: int = ARTIFACT_BYTES,
    duration_seconds: int = DURATION_SECONDS,
) -> str:
    return signer.issue(
        capability_id=capability_id,
        site_id=site_id,
        workspace_id=workspace_id,
        run_id=run_id,
        route=route,
        target=target,
        evidence=evidence,
        artifact_bytes_limit=artifact_bytes,
        duration_seconds=duration_seconds,
        now=now,
        ttl_seconds=30,
        nonce=nonce,
    )


@pytest.mark.asyncio
async def test_browser_token_projects_only_bound_overlay_and_is_one_time(
    agent_site_database: AgentSiteDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    agent_pool = await database.role_pool("slaif_agent_runtime")
    signer = BrowserPreviewCredentialSigner(
        BrowserSigningKey("0123456789abcdef", bytes(range(32)))
    )
    try:
        function_signature = (
            "control.slaif_render_browser_preview_authorize("
            "uuid,uuid,uuid,uuid,text,text,text[],bigint,integer,text,boolean)"
        )
        async with preview_pool.acquire() as preview:
            assert await preview.fetchval(
                "SELECT has_function_privilege(current_user,$1,'EXECUTE')",
                function_signature,
            )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await preview.fetch("SELECT * FROM control.browser_run")
        async with agent_pool.acquire() as agent:
            assert not await agent.fetchval(
                "SELECT has_function_privilege(current_user,$1,'EXECUTE')",
                function_signature,
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            function = await owner.fetchrow(
                "SELECT owner.rolname::text,proc.prosecdef,"
                "COALESCE(array_to_string(proc.proconfig,','),'') "
                "FROM pg_catalog.pg_proc proc "
                "JOIN pg_catalog.pg_namespace namespace_ "
                "ON namespace_.oid=proc.pronamespace "
                "JOIN pg_catalog.pg_roles owner ON owner.oid=proc.proowner "
                "WHERE namespace_.nspname='control' "
                "AND proc.proname='slaif_render_browser_preview_authorize'"
            )
            assert tuple(function) == (
                "slaif_owner",
                True,
                "search_path=pg_catalog",
            )
        site = await SiteService(control_pool).create(
            CreateSiteRequest(
                site_key="browser-preview",
                display_name="Browser Preview",
                default_locale="en",
            )
        )
        user_id, workspace_id, capability_id = uuid4(), uuid4(), uuid4()
        dynamic_type_id = uuid4()
        dynamic_item_id = uuid4()
        dynamic_translation_id = uuid4()
        dynamic_view_id = uuid4()
        dynamic_listing_id = uuid4()
        dynamic_detail_id = uuid4()
        expires = datetime.now(UTC) + timedelta(hours=1)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            sl_home_id, sl_guide_id = uuid4(), uuid4()
            await owner.execute(
                "INSERT INTO content.site_locale_base "
                "(site_id,tag,enabled,is_default,position) VALUES "
                "($1,'en',true,true,0),($1,'sl-SI',true,false,1)",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id,identity_kind,oidc_issuer,oidc_subject,display_name) "
                "VALUES ($1,'OIDC','https://issuer.test',$2,'Browser Agent')",
                user_id,
                f"subject-{user_id}",
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id,site_id,created_by,actor_type,title,delegation_preset,"
                "effective_scopes,status,expires_at) VALUES "
                "($1,$2,$3,'AGENT','Browser preview','L1',"
                "'[\"preview:inspect\"]'::jsonb,'ACTIVE',$4)",
                workspace_id,
                site.site_id,
                user_id,
                expires,
            )
            await owner.execute(
                "INSERT INTO control.capability "
                "(id,workspace_id,public_id,secret_digest,scopes,expires_at,"
                "browser_max_concurrent_runs,browser_max_artifact_bytes) "
                "VALUES ($1,$2,$3,$4,'[\"preview:inspect\"]'::jsonb,$5,10,104857600)",
                capability_id,
                workspace_id,
                uuid4().hex,
                "a" * 64,
                expires,
            )
            page_id = await owner.fetchval(
                "INSERT INTO content.page_base "
                "(site_id,slug,title,status,locale) VALUES "
                "($1,'home','Canonical browser page','PUBLISHED','en') RETURNING id",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id) VALUES "
                "($1,$2,'home','Domov','PUBLISHED','sl-SI',NULL),"
                "($3,$2,'guide','Vodnik','PUBLISHED','sl-SI',$1)",
                sl_home_id,
                site.site_id,
                sl_guide_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) "
                "VALUES ($1,$2,'Heading','1','default',0,$3::jsonb)",
                site.site_id,
                page_id,
                '{"text":"Browser preview","level":2}',
            )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id,site_id,key,labels,slug_pattern,status,definition_version,"
                "settings) VALUES ($1,$2,'browser-news','{}',"
                "'/news/{slug}','ACTIVE',1,'{}')",
                dynamic_type_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id,type_id,key,label,field_type,required,localized,cardinality,"
                "position,validation,ui_options,definition_version) VALUES "
                "($1,$2,'title','Title','short_text',true,true,1,0,'{}','{}',1),"
                "($3,$2,'summary','Summary','long_text',true,true,1,1,'{}','{}',1),"
                "($4,$2,'rank','Rank','integer',true,false,1,2,'{}','{}',1)",
                uuid4(),
                dynamic_type_id,
                uuid4(),
                uuid4(),
            )
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id,site_id,type_id,slug,status,type_definition_version,values) "
                "VALUES ($1,$2,$3,'published','PUBLISHED',1,'{\"rank\":1}')",
                dynamic_item_id,
                site.site_id,
                dynamic_type_id,
            )
            await owner.execute(
                "INSERT INTO content.content_item_translation_base "
                "(id,site_id,item_id,locale,localized_values) VALUES "
                "($1,$2,$3,'en',$4::jsonb)",
                dynamic_translation_id,
                site.site_id,
                dynamic_item_id,
                '{"title":"Canonical browser item","summary":"Canonical summary"}',
            )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,"
                "pagination_spec) VALUES ($1,$2,$3,'browser-news','{}',"
                "$4::jsonb,$5::jsonb,$6::jsonb)",
                dynamic_view_id,
                site.site_id,
                dynamic_type_id,
                '{"field":"rank","direction":"desc"}',
                '{"fields":["title","summary","rank"]}',
                '{"limit":10,"offset":0}',
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(id,site_id,slug,title,status,locale,parent_id,route_template) "
                "VALUES ($1,$2,'news','Browser news','PUBLISHED','en',NULL,NULL),"
                "($3,$2,'detail','Browser detail','PUBLISHED','en',$1,'{slug}')",
                dynamic_listing_id,
                site.site_id,
                dynamic_detail_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) VALUES "
                "($1,$2,'CollectionDetail','1','default',0,$3::jsonb)",
                site.site_id,
                dynamic_detail_id,
                json.dumps({"viewId": str(dynamic_view_id)}),
            )
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            await cow.native.execute(
                "UPDATE content.page SET title='Bound localized nested browser draft' "
                "WHERE site_id=$1 AND slug='guide' AND locale='sl-SI'",
                site.site_id,
            )
            await cow.native.execute(
                "UPDATE content.content_item_translation SET localized_values=$1 "
                "WHERE id=$2 AND site_id=$3",
                json.dumps(
                    {
                        "title": "Workspace browser item",
                        "summary": "Workspace summary",
                    }
                ),
                dynamic_translation_id,
                site.site_id,
            )
        preview_route = f"{ROUTE}/sl-si/guide"
        async with agent_pool.acquire() as agent:
            run_id = await _begin(
                agent,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="render-valid",
                route=preview_route,
            )
        adapter = _RenderAdapter(public_pool, preview_pool)
        service = RenderProjectionService(adapter, browser_verifier=signer)
        now = int(time.time())
        token = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=run_id,
            now=now,
            nonce="00112233445566778899aabbccddeeff",
            route=preview_route,
        )
        render_app = create_render_app(
            settings=ServiceSettings.for_test(),
            database=adapter,
            browser_verifier=signer,
        )
        async with render_app.router.lifespan_context(render_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as client:
                response = await client.post(
                    "/internal/render/v1/preview",
                    headers={"X-SLAIF-Browser-Run-Token": token},
                    json={
                        "authority": "localhost",
                        "path": preview_route,
                        "workspace_id": str(workspace_id),
                        "browser_route": preview_route,
                    },
                )
                assert response.status_code == 200
                assert response.json()["route_kind"] == "page"
                assert response.json()["render_mode"] == "preview"
                assert response.json()["page"]["title"] == (
                    "Bound localized nested browser draft"
                )
                assert response.json()["page"]["locale"] == "sl-SI"
                assert response.json()["page"]["effective_route"] == "/sl-SI/guide"
                assert token not in response.text
                replay = await client.post(
                    "/internal/render/v1/preview",
                    headers={"X-SLAIF-Browser-Run-Token": token},
                    json={
                        "authority": "localhost",
                        "path": preview_route,
                        "workspace_id": str(workspace_id),
                        "browser_route": preview_route,
                    },
                )
                assert replay.status_code == 404
        canonical = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{ROUTE}/")
        )
        assert canonical.route_kind == "page"
        assert canonical.page.title == "Canonical browser page"
        canonical_nested = await service.canonical(
            RenderPageRequest(authority="localhost", path=preview_route)
        )
        assert canonical_nested.route_kind == "page"
        assert canonical_nested.page.title == "Vodnik"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            token_state = await owner.fetchrow(
                "SELECT preview_nonce_digest,preview_token_used_at FROM "
                "control.browser_run WHERE id=$1",
                run_id,
            )
            assert (
                token_state[0]
                == hashlib.sha256(b"00112233445566778899aabbccddeeff").hexdigest()
            )
            assert token_state[1] is not None
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.browser_event "
                    "WHERE run_id=$1 AND event_type='PREVIEW_TOKEN_CONSUMED'",
                    run_id,
                )
                == 1
            )
            assert token not in str(tuple(token_state))

        # Internal adapter calls may advance runs for proof, but no production
        # dispatcher is started. A fresh token for a separately terminal run is
        # denied before any nonce is consumed.
        async with agent_pool.acquire() as agent:
            first_lease = uuid4()
            claimed = await agent.fetchrow(CLAIM_SQL, first_lease, 30)
            assert claimed["run_id"] == run_id
            assert (
                await agent.fetchval(
                    COMPLETE_SQL,
                    run_id,
                    first_lease,
                    "COMPLETED",
                    json.dumps({"ok": True}),
                    None,
                    None,
                )
                == "COMPLETED"
            )
            terminal_run_id = await _begin(
                agent,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="render-terminal",
            )
            terminal_lease = uuid4()
            terminal_claim = await agent.fetchrow(CLAIM_SQL, terminal_lease, 30)
            assert terminal_claim["run_id"] == terminal_run_id
            assert (
                await agent.fetchval(
                    COMPLETE_SQL,
                    terminal_run_id,
                    terminal_lease,
                    "COMPLETED",
                    json.dumps({"ok": True}),
                    None,
                    None,
                )
                == "COMPLETED"
            )
        terminal_token = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=terminal_run_id,
            now=int(time.time()),
        )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path=f"{ROUTE}/",
                    workspace_id=workspace_id,
                    browser_route=ROUTE,
                    browser_token=SecretStr(terminal_token),
                )
            )

        # Signed but changed route/site/workspace facts, tamper, and expiry deny
        # before nonce consumption.
        async with agent_pool.acquire() as agent:
            race_run_id = await _begin(
                agent,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="render-race",
            )
        wrong_route = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=race_run_id,
            now=now,
            route="/other",
        )
        tamper_source = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=race_run_id,
            now=now,
            nonce="ffeeddccbbaa99887766554433221100",
        )
        tampered_parts = tamper_source.split(".")
        signature = tampered_parts[-1]
        tampered_parts[-1] = ("A" if signature[0] != "A" else "B") + signature[1:]
        tampered_token = ".".join(tampered_parts)
        for rejected in (
            wrong_route,
            tampered_token,
            _token(
                signer,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=race_run_id,
                now=now - 60,
            ),
            _token(
                signer,
                capability_id=uuid4(),
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=race_run_id,
                now=now,
            ),
            _token(
                signer,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=uuid4(),
                now=now,
            ),
            _token(
                signer,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=race_run_id,
                now=now,
                target=BrowserTarget.TABLET,
            ),
            _token(
                signer,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=race_run_id,
                now=now,
                evidence=(BrowserEvidence.SCREENSHOT,),
            ),
            _token(
                signer,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=race_run_id,
                now=now,
                artifact_bytes=ARTIFACT_BYTES - 1,
            ),
            _token(
                signer,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                run_id=race_run_id,
                now=now,
                duration_seconds=DURATION_SECONDS - 1,
            ),
        ):
            with pytest.raises(ProjectionError, match="not_found"):
                await service.preview(
                    RenderPreviewRequest(
                        authority="localhost",
                        path=f"{ROUTE}/",
                        workspace_id=workspace_id,
                        browser_route=ROUTE,
                        browser_token=SecretStr(rejected),
                    )
                )

        baseline_operations: Any
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            baseline_operations = await get_session_operations(
                AsyncpgExecutor(owner), workspace_id, schema="content"
            )

        # Cancellation after a dynamic detail and translation snapshot rolls back
        # only the read transaction. The separately committed one-use browser
        # authorization remains consumed, and a newly authorized run succeeds.
        dynamic_route = f"{ROUTE}/news/published"
        async with agent_pool.acquire() as agent:
            cancelled_run_id = await _begin(
                agent,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="render-dynamic-cancel",
                route=dynamic_route,
            )
        cancelled_token = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=cancelled_run_id,
            now=int(time.time()),
            route=dynamic_route,
            nonce="11223344556677889900aabbccddeeff",
        )
        original_query = service._query
        dynamic_snapshot = asyncio.Event()
        release_dynamic_snapshot = asyncio.Event()

        async def pause_after_dynamic_snapshot(
            connection: Any,
            *,
            context: Any,
            request: RenderPageRequest,
            render_mode: str,
        ) -> Any:
            projection = await original_query(
                connection,
                context=context,
                request=request,
                render_mode=render_mode,
            )
            if request.path == dynamic_route:
                dynamic_snapshot.set()
                await release_dynamic_snapshot.wait()
            return projection

        monkeypatch.setattr(service, "_query", pause_after_dynamic_snapshot)
        cancelled_task = asyncio.create_task(
            service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path=dynamic_route,
                    workspace_id=workspace_id,
                    browser_route=dynamic_route,
                    browser_token=SecretStr(cancelled_token),
                )
            )
        )
        await asyncio.wait_for(dynamic_snapshot.wait(), timeout=15)
        cancelled_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await cancelled_task
        release_dynamic_snapshot.set()
        monkeypatch.setattr(service, "_query", original_query)
        with pytest.raises(ProjectionError, match="not_found"):
            await service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path=dynamic_route,
                    workspace_id=workspace_id,
                    browser_route=dynamic_route,
                    browser_token=SecretStr(cancelled_token),
                )
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.browser_event "
                    "WHERE run_id=$1 AND event_type='PREVIEW_TOKEN_CONSUMED'",
                    cancelled_run_id,
                )
                == 1
            )
            assert (
                await get_session_operations(
                    AsyncpgExecutor(owner), workspace_id, schema="content"
                )
                == baseline_operations
            )
            cancelled_state = await owner.fetchrow(
                "SELECT preview_token_used_at,preview_nonce_digest "
                "FROM control.browser_run WHERE id=$1",
                cancelled_run_id,
            )
            assert cancelled_state[0] is not None
            assert (
                cancelled_state[1]
                == hashlib.sha256(b"11223344556677889900aabbccddeeff").hexdigest()
            )
        async with preview_pool.acquire(timeout=3) as preview:
            context_values = await preview.fetchrow(
                "SELECT current_setting('app.session_id',true),"
                "current_setting('app.operation_id',true)"
            )
            assert all(value in {None, ""} for value in context_values)
            assert await preview.fetchval("SELECT 1") == 1

        async with agent_pool.acquire() as agent:
            recovery_run_id = await _begin(
                agent,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="render-dynamic-after-cancel",
                route=dynamic_route,
            )
        recovery_token = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=recovery_run_id,
            now=int(time.time()),
            route=dynamic_route,
            nonce="22334455667788990011aabbccddeeff",
        )
        recovered_dynamic = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path=dynamic_route,
                workspace_id=workspace_id,
                browser_route=dynamic_route,
                browser_token=SecretStr(recovery_token),
            )
        )
        assert recovered_dynamic.route_kind == "page"
        assert recovered_dynamic.route_parameters == {"slug": "published"}
        assert next(iter(recovered_dynamic.bindings.values()))[0]["values"] == {
            "rank": 1,
            "summary": "Workspace summary",
            "title": "Workspace browser item",
        }
        canonical_dynamic = await service.canonical(
            RenderPageRequest(authority="localhost", path=dynamic_route)
        )
        assert canonical_dynamic.route_kind == "page"
        assert next(iter(canonical_dynamic.bindings.values()))[0]["values"] == {
            "rank": 1,
            "summary": "Canonical summary",
            "title": "Canonical browser item",
        }
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await get_session_operations(
                    AsyncpgExecutor(owner), workspace_id, schema="content"
                )
                == baseline_operations
            )

        # Pause after the consuming authorization and revoke before the COW
        # transaction's under-lock recheck.
        first_authorized = asyncio.Event()
        resume = asyncio.Event()
        original_cow_session: Any = projection_module.asyncpg_cow_session  # type: ignore[attr-defined]

        @asynccontextmanager
        async def paused_cow_session(
            *args: object, **kwargs: object
        ) -> AsyncIterator[Any]:
            first_authorized.set()
            await resume.wait()
            async with original_cow_session(*args, **kwargs) as cow:
                yield cow

        monkeypatch.setattr(
            projection_module, "asyncpg_cow_session", paused_cow_session
        )
        valid_race_token = _token(
            signer,
            capability_id=capability_id,
            site_id=site.site_id,
            workspace_id=workspace_id,
            run_id=race_run_id,
            now=int(time.time()),
            nonce="ffeeddccbbaa99887766554433221100",
        )
        raced = asyncio.create_task(
            service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path=f"{ROUTE}/",
                    workspace_id=workspace_id,
                    browser_route=ROUTE,
                    browser_token=SecretStr(valid_race_token),
                )
            )
        )
        await asyncio.wait_for(first_authorized.wait(), timeout=15)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET revoked_at=CURRENT_TIMESTAMP "
                "WHERE id=$1",
                capability_id,
            )
        resume.set()
        with pytest.raises(ProjectionError, match="not_found"):
            await raced
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await get_session_operations(
                    AsyncpgExecutor(owner), workspace_id, schema="content"
                )
                == baseline_operations
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.browser_event "
                    "WHERE run_id=$1 AND event_type='PREVIEW_TOKEN_CONSUMED'",
                    race_run_id,
                )
                == 1
            )
    finally:
        await agent_pool.close()
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()


@pytest.mark.asyncio
async def test_public_agent_created_localized_browser_preview_workflow(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """The public Agent structure is the source of a bound browser preview."""

    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    agent_pool = await database.role_pool("slaif_agent_runtime")
    signer = BrowserPreviewCredentialSigner(
        BrowserSigningKey("0123456789abcdef", bytes(range(32)))
    )
    scopes = (
        "site:read",
        "page:create",
        "page:read",
        "locale:configure",
        "navigation:read",
        "navigation:create",
        "navigation:write",
        "redirect:create",
        "preview:inspect",
    )
    suffix = uuid4().hex[:8]
    site_key = f"browser-http-{suffix}"
    route = f"/s/{site_key}/sl-si/guide"
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            user_id = await _agent_user(owner, suffix)
            site_id = await _agent_site(owner, suffix)
            workspace_id = await _agent_workspace(
                owner, site_id=site_id, user_id=user_id, suffix=suffix
            )
            binding = await _agent_capability(
                owner,
                site_id=site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                scopes=scopes,
            )
            await owner.execute(
                "UPDATE control.workspace SET delegation_preset='L4', "
                "effective_scopes=$2::jsonb WHERE id=$1",
                workspace_id,
                json.dumps(scopes),
            )
            await owner.execute(
                "INSERT INTO content.page_base "
                "(site_id,slug,title,status,locale) VALUES "
                "($1,'home','Canonical browser page','PUBLISHED','en-US')",
                site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) SELECT $1,id,'Heading','1','default',0,"
                '\'{"text":"Canonical browser","level":2}\'::jsonb '
                "FROM content.page_base WHERE site_id=$1 AND slug='home' "
                "AND locale='en-US'",
                site_id,
            )
            other_workspace_id = uuid4()
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id,site_id,created_by,delegator_id,actor_type,title,"
                "delegation_preset,effective_scopes,status,expires_at) VALUES "
                "($1,$2,$3,$3,'AGENT','Other browser workspace','L4',$4::jsonb,"
                "'ACTIVE',CURRENT_TIMESTAMP + interval '1 hour')",
                other_workspace_id,
                site_id,
                user_id,
                json.dumps(scopes),
            )
        agent_app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        headers = {"Authorization": f"Bearer {binding.token}"}
        async with agent_app.router.lifespan_context(agent_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=agent_app),
                base_url="http://agent.test",
            ) as client:
                locale = await client.post(
                    "/api/agent/v1/locales",
                    headers={**headers, "Idempotency-Key": "browser-agent-locale"},
                    json={"tag": "sl-SI", "position": 1},
                )
                assert locale.status_code == 201, locale.text
                sl_home = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "browser-agent-home"},
                    json={"slug": "home", "title": "Domov", "locale": "sl-SI"},
                )
                assert sl_home.status_code == 201, sl_home.text
                sl_guide = await client.post(
                    "/api/agent/v1/pages",
                    headers={**headers, "Idempotency-Key": "browser-agent-guide"},
                    json={
                        "slug": "guide",
                        "title": "Vodnik",
                        "locale": "sl-SI",
                        "parent_id": sl_home.json()["record"]["id"],
                    },
                )
                assert sl_guide.status_code == 201, sl_guide.text
                guide_id = sl_guide.json()["record"]["id"]
                navigation = await client.post(
                    "/api/agent/v1/navigation",
                    headers={
                        **headers,
                        "Idempotency-Key": "browser-agent-navigation",
                    },
                    json={
                        "key": "primary",
                        "label": "Primary",
                        "labels": {"sl-SI": "Glavni meni"},
                        "settings": {},
                    },
                )
                assert navigation.status_code == 201, navigation.text
                navigation_id = navigation.json()["record"]["id"]
                item = await client.post(
                    f"/api/agent/v1/navigation/{navigation_id}/items",
                    headers={**headers, "Idempotency-Key": "browser-agent-item"},
                    json={
                        "page_id": guide_id,
                        "target_kind": "PAGE",
                        "target_value": guide_id,
                        "labels": {"sl-SI": "Vodnik"},
                        "locale": "sl-SI",
                    },
                )
                assert item.status_code == 201, item.text
                redirect = await client.post(
                    "/api/agent/v1/redirects",
                    headers={**headers, "Idempotency-Key": "browser-agent-redirect"},
                    json={
                        "source_route": "/browser-after",
                        "target": "/",
                        "status_code": 301,
                    },
                )
                assert redirect.status_code == 201, redirect.text
                run = await client.post(
                    "/api/agent/v1/preview-runs",
                    headers={**headers, "Idempotency-Key": "browser-agent-run"},
                    json={
                        "version": "browser-preview/v1",
                        "route": route,
                        "target": "desktop-chromium",
                        "evidence": ["screenshot", "heading-summary"],
                    },
                )
                assert run.status_code == 202, run.text
                run_id = UUID(run.json()["run_id"])

        async with agent_pool.acquire() as agent:
            claim = await agent.fetchrow(CLAIM_SQL, uuid4(), 30)
            assert claim is not None and claim["run_id"] == run_id
        token = signer.issue(
            capability_id=binding.capability_id,
            site_id=site_id,
            workspace_id=workspace_id,
            run_id=run_id,
            route=route,
            target=BrowserTarget.DESKTOP_CHROMIUM,
            evidence=EVIDENCE,
            artifact_bytes_limit=ARTIFACT_BYTES,
            duration_seconds=DURATION_SECONDS,
            now=int(time.time()),
            ttl_seconds=30,
            nonce="00112233445566778899aabbccddeeff",
        )
        service = RenderProjectionService(
            _RenderAdapter(public_pool, preview_pool), browser_verifier=signer
        )
        projection = await service.preview(
            RenderPreviewRequest(
                authority="localhost",
                path=route,
                workspace_id=workspace_id,
                browser_route=route,
                browser_token=SecretStr(token),
            )
        )
        assert projection.route_kind == "page"
        assert projection.page.title == "Vodnik"
        assert projection.page.effective_route == "/sl-SI/guide"
        assert projection.locale == "sl-SI"
        assert projection.navigation[0].label == "Glavni meni"
        assert token not in repr(projection)
        with pytest.raises(ProjectionError, match="not_found"):
            await service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path=route,
                    workspace_id=workspace_id,
                    browser_route=route,
                    browser_token=SecretStr(token),
                )
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path=route,
                    workspace_id=other_workspace_id,
                    browser_route=route,
                    browser_token=SecretStr(token),
                )
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await service.canonical(
                RenderPageRequest(authority="localhost", path=route)
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            consumed = await owner.fetchrow(
                "SELECT preview_token_used_at FROM control.browser_run WHERE id=$1",
                run_id,
            )
            assert consumed[0] is not None
    finally:
        await agent_pool.close()
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()

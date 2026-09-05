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
) -> UUID:
    request = {
        "version": "browser-preview/v1",
        "route": ROUTE,
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
        ROUTE,
        hashlib.sha256(ROUTE.encode()).hexdigest(),
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
        expires = datetime.now(UTC) + timedelta(hours=1)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
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
                "INSERT INTO content.page_composition_base "
                "(site_id,page_id,component_type,schema_version,slot_key,"
                "order_key,props) "
                "VALUES ($1,$2,'Heading','1','default',0,$3::jsonb)",
                site.site_id,
                page_id,
                '{"text":"Browser preview","level":2}',
            )
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            await cow.native.execute(
                "UPDATE content.page SET title='Bound browser draft' "
                "WHERE site_id=$1 AND slug='home' AND locale='en'",
                site.site_id,
            )
        async with agent_pool.acquire() as agent:
            run_id = await _begin(
                agent,
                capability_id=capability_id,
                site_id=site.site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="render-valid",
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
                        "path": f"{ROUTE}/",
                        "workspace_id": str(workspace_id),
                        "browser_route": ROUTE,
                    },
                )
                assert response.status_code == 200
                assert response.json()["route_kind"] == "page"
                assert response.json()["render_mode"] == "preview"
                assert response.json()["page"]["title"] == "Bound browser draft"
                assert token not in response.text
                replay = await client.post(
                    "/internal/render/v1/preview",
                    headers={"X-SLAIF-Browser-Run-Token": token},
                    json={
                        "authority": "localhost",
                        "path": f"{ROUTE}/",
                        "workspace_id": str(workspace_id),
                        "browser_route": ROUTE,
                    },
                )
                assert replay.status_code == 404
        canonical = await service.canonical(
            RenderPageRequest(authority="localhost", path=f"{ROUTE}/")
        )
        assert canonical.route_kind == "page"
        assert canonical.page.title == "Canonical browser page"
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

"""Real PostgreSQL canonical Render projection evidence."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.render_api.projection import (
    RenderPageRequest,
    RenderPreviewRequest,
    RenderProjectionService,
)
from slaif_agent_site.sites import CreateSiteRequest, DomainMappingRequest
from slaif_agent_site.sites.resolver import SiteResolver
from slaif_agent_site.sites.service import SiteService


class _RenderAdapter:
    def __init__(self, pool: object, preview_pool: object | None = None) -> None:
        self._pool = pool
        self._preview_pool = preview_pool or pool
        self._resolver = SiteResolver(pool)  # type: ignore[arg-type]
        self.acquire_timeout = 3.0

    def resolver(self) -> SiteResolver:
        return self._resolver

    def public_pool(self) -> object:
        return self._pool

    def preview_pool(self) -> object:
        return self._preview_pool


async def test_canonical_projection_is_site_confined_and_typed(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    try:
        control = SiteService(control_pool)
        site = await control.create(
            CreateSiteRequest(site_key="docs", display_name="Docs", default_locale="en")
        )
        context = await control.resolve("localhost", "/s/docs")
        await control.put_domain(
            context, DomainMappingRequest(hostname="example.test", path_prefix="/")
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            page_id = await owner.fetchval(
                "INSERT INTO content.page_base "
                "(site_id, slug, title, status, locale) VALUES "
                "($1, 'home', 'Docs home', 'PUBLISHED', 'en') RETURNING id",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id, page_id, component_type, schema_version, slot_key, "
                "order_key, props) "
                "VALUES ($1, $2, 'Heading', '1', 'default', 0, $3::jsonb)",
                site.site_id,
                page_id,
                '{"text":"Escaped <heading>","level":2}',
            )
        projection = await RenderProjectionService(
            _RenderAdapter(public_pool)
        ).canonical(RenderPageRequest(authority="localhost", path="/s/docs/"))
        assert projection.render_mode == "canonical"
        assert projection.site.id == site.site_id
        assert projection.page.title == "Docs home"
        assert projection.composition.nodes[0].component_type == "Heading"
        assert projection.composition.nodes[0].props["text"] == "Escaped <heading>"
    finally:
        await public_pool.close()
        await control_pool.close()


async def test_preview_projection_requires_authorized_human_session(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    preview_pool = await database.role_pool("slaif_preview_reader")
    editor_pool = await database.role_pool("slaif_editor_runtime")
    site = None
    try:
        control = SiteService(control_pool)
        site = await control.create(
            CreateSiteRequest(
                site_key="staging", display_name="Preview", default_locale="en"
            )
        )
        user_id, session_id, workspace_id = uuid4(), uuid4(), uuid4()
        secret = b"p" * 32
        public_id = f"sas2_{session_id.hex}"
        expires = datetime.now(UTC) + timedelta(hours=1)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://issuer.test', $2, 'Preview User')",
                user_id,
                f"subject-{user_id}",
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id, user_account_id, role_key, delegation_ceiling) "
                "VALUES ($1, $2, 'SITE_EDITOR', 2)",
                site.site_id,
                user_id,
            )
            await owner.execute(
                "INSERT INTO control.user_session "
                "(id, public_id, secret_digest, csrf_secret_digest, user_account_id, "
                "absolute_expires_at) VALUES ($1, $2, $3, $4, $5, $6)",
                session_id,
                public_id,
                hashlib.sha256(secret).digest(),
                b"c" * 32,
                user_id,
                expires,
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id, site_id, created_by, actor_type, title, delegation_preset, "
                "status, expires_at) VALUES ($1, $2, $3, 'HUMAN', 'Preview', "
                "'L2_SITE_EDITOR', 'ACTIVE', $4)",
                workspace_id,
                site.site_id,
                user_id,
                expires,
            )
            page_id = await owner.fetchval(
                "INSERT INTO content.page_base "
                "(site_id, slug, title, status, locale) VALUES "
                "($1, 'home', 'Preview home', 'PUBLISHED', 'en') RETURNING id",
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id, page_id, component_type, schema_version, slot_key, "
                "order_key, props) "
                "VALUES ($1, $2, 'Heading', '1', 'default', 0, $3::jsonb)",
                site.site_id,
                page_id,
                '{"text":"Preview","level":2}',
            )
        async with asyncpg_cow_session(editor_pool, session_id=workspace_id) as cow:
            await cow.native.execute(
                "UPDATE content.page SET title = 'Preview draft' "
                "WHERE site_id = $1 AND slug = 'home' AND locale = 'en'",
                site.site_id,
            )
        adapter = _RenderAdapter(public_pool, preview_pool)
        projection = await RenderProjectionService(adapter).preview(
            RenderPreviewRequest(
                authority="localhost",
                path="/s/staging/",
                workspace_id=workspace_id,
                session_token=format_session_token(public_id, secret),
            )
        )
        assert projection.render_mode == "preview"
        assert projection.page.title == "Preview draft"
        canonical = await RenderProjectionService(adapter).canonical(
            RenderPageRequest(authority="localhost", path="/s/staging/")
        )
        assert canonical.page.title == "Preview home"
    finally:
        await editor_pool.close()
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()

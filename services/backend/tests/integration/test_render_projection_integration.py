"""Real PostgreSQL canonical Render projection evidence."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
import slaif_agent_site.render_api.projection as projection_module
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.render_api.projection import (
    ProjectionError,
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
    agent_site_database: AgentSiteDatabase, monkeypatch: pytest.MonkeyPatch
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
            type_id, field_id, rank_id, view_id, item_id, item_two_id = (
                uuid4(),
                uuid4(),
                uuid4(),
                uuid4(),
                uuid4(),
                uuid4(),
            )
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id, site_id, key, labels, slug_pattern, status, "
                "definition_version, settings) VALUES "
                "($1, $2, 'article', '{}', '/article/{slug}', 'ACTIVE', 1, '{}')",
                type_id,
                site.site_id,
            )
            await owner.execute(
                "INSERT INTO content.field_definition_base "
                "(id, type_id, key, label, field_type, required, localized, "
                "cardinality, position, validation, ui_options, definition_version) "
                "VALUES ($1, $2, 'title', 'Title', 'short_text', true, false, "
                "1, 0, '{}', '{}', 1), "
                "($3, $2, 'secret', 'Secret', 'short_text', false, false, "
                "1, 1, '{}', '{}', 1), "
                "($4, $2, 'rank', 'Rank', 'integer', false, false, "
                "1, 2, '{}', '{}', 1)",
                field_id,
                type_id,
                uuid4(),
                rank_id,
            )
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id, site_id, type_id, slug, status, type_definition_version, values) "
                "VALUES ($1, $2, $3, 'first', 'PUBLISHED', 1, $4::jsonb)",
                item_id,
                site.site_id,
                type_id,
                '{"title":"Visible item","secret":"Private fixture","rank":2}',
            )
            await owner.execute(
                "INSERT INTO content.content_item_base "
                "(id, site_id, type_id, slug, status, type_definition_version, values) "
                "VALUES ($1, $2, $3, 'second', 'PUBLISHED', 1, $4::jsonb)",
                item_two_id,
                site.site_id,
                type_id,
                '{"title":"Second item","secret":"Other fixture","rank":1}',
            )
            await owner.execute(
                "INSERT INTO content.collection_view_base "
                "(id, site_id, type_id, key, filter_spec, sort_spec, "
                "projection_spec, pagination_spec) VALUES "
                "($1, $2, $3, 'articles', $4::jsonb, $5::jsonb, "
                "$6::jsonb, $7::jsonb)",
                view_id,
                site.site_id,
                type_id,
                '{"field":"rank","op":"gte","value":1}',
                '{"field":"rank","direction":"desc"}',
                '{"fields":["title","rank"]}',
                '{"limit":1,"offset":1}',
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
            await owner.execute(
                "INSERT INTO content.page_composition_base "
                "(site_id, page_id, component_type, schema_version, slot_key, "
                "order_key, props) VALUES ($1, $2, 'CollectionList', '1', "
                "'default', 1, $3::jsonb)",
                site.site_id,
                page_id,
                json.dumps({"viewId": str(view_id), "limit": 10}),
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
        collection_items = next(iter(projection.bindings.values()))
        assert collection_items[0]["values"] == {"title": "Second item", "rank": 1}
        assert collection_items[0]["slug"] == "second"
        canonical = await RenderProjectionService(adapter).canonical(
            RenderPageRequest(authority="localhost", path="/s/staging/")
        )
        assert canonical.page.title == "Preview home"
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_type_base SET definition_version = 2 "
                "WHERE id = $1",
                type_id,
            )
        with pytest.raises(ProjectionError, match="stale_collection_definition"):
            await RenderProjectionService(adapter).canonical(
                RenderPageRequest(authority="localhost", path="/s/staging/")
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE content.content_type_base SET definition_version = 1 "
                "WHERE id = $1",
                type_id,
            )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            before_race = await owner.fetchrow(
                "SELECT (SELECT count(*) FROM content.page_changes), "
                "(SELECT count(*) FROM control.human_editor_idempotency), "
                "(SELECT count(*) FROM audit.human_editor_mutation)"
            )
        authorized = asyncio.Event()
        resume = asyncio.Event()
        original_cow_session: Any = projection_module.asyncpg_cow_session  # type: ignore[attr-defined]

        @asynccontextmanager
        async def paused_cow_session(
            *args: object, **kwargs: object
        ) -> AsyncIterator[Any]:
            authorized.set()
            await resume.wait()
            async with original_cow_session(*args, **kwargs) as cow:
                yield cow

        monkeypatch.setattr(
            projection_module, "asyncpg_cow_session", paused_cow_session
        )
        race = asyncio.create_task(
            RenderProjectionService(adapter).preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/staging/",
                    workspace_id=workspace_id,
                    session_token=format_session_token(public_id, secret),
                )
            )
        )
        await asyncio.wait_for(authorized.wait(), timeout=5)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET revoked_at = CURRENT_TIMESTAMP "
                "WHERE id = $1",
                session_id,
            )
        resume.set()
        with pytest.raises(ProjectionError, match="not_found"):
            await race
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            after_race = await owner.fetchrow(
                "SELECT (SELECT count(*) FROM content.page_changes), "
                "(SELECT count(*) FROM control.human_editor_idempotency), "
                "(SELECT count(*) FROM audit.human_editor_mutation)"
            )
        assert tuple(after_race) == tuple(before_race)

        monkeypatch.setattr(
            projection_module, "asyncpg_cow_session", original_cow_session
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET "
                "created_at = CURRENT_TIMESTAMP - interval '31 minutes', "
                "last_seen_at = CURRENT_TIMESTAMP - interval '31 minutes', "
                "recent_auth_at = CURRENT_TIMESTAMP - interval '31 minutes' "
                "WHERE id = $1",
                session_id,
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await RenderProjectionService(adapter).preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/staging/",
                    workspace_id=workspace_id,
                    session_token=format_session_token(public_id, secret),
                )
            )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET last_seen_at = CURRENT_TIMESTAMP, "
                "revoked_at = CURRENT_TIMESTAMP WHERE id = $1",
                session_id,
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await RenderProjectionService(adapter).preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/staging/",
                    workspace_id=workspace_id,
                    session_token=format_session_token(public_id, secret),
                )
            )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET "
                "created_at = CURRENT_TIMESTAMP - interval '2 minutes', "
                "last_seen_at = CURRENT_TIMESTAMP - interval '2 minutes', "
                "recent_auth_at = CURRENT_TIMESTAMP - interval '2 minutes', "
                "absolute_expires_at = CURRENT_TIMESTAMP - interval '1 minute', "
                "revoked_at = NULL WHERE id = $1",
                session_id,
            )
        with pytest.raises(ProjectionError, match="not_found"):
            await RenderProjectionService(adapter).preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/staging/",
                    workspace_id=workspace_id,
                    session_token=format_session_token(public_id, secret),
                )
            )

        agent_workspace_id, import_workspace_id = uuid4(), uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET revoked_at = NULL, "
                "last_seen_at = CURRENT_TIMESTAMP, absolute_expires_at = "
                "CURRENT_TIMESTAMP + interval '1 hour' WHERE id = $1",
                session_id,
            )
            for selected_id, actor_type in (
                (agent_workspace_id, "AGENT"),
                (import_workspace_id, "IMPORT"),
            ):
                await owner.execute(
                    "INSERT INTO control.workspace "
                    "(id, site_id, created_by, actor_type, title, delegation_preset, "
                    "status, expires_at) VALUES ($1, $2, $3, $4, 'Authorized', "
                    "'L2_SITE_EDITOR', 'ACTIVE', CURRENT_TIMESTAMP + "
                    "interval '1 hour')",
                    selected_id,
                    site.site_id,
                    user_id,
                    actor_type,
                )
            other_site_id, other_workspace_id = uuid4(), uuid4()
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, 'other-site', 'Other', 'en', 'catalog-v1')",
                other_site_id,
            )
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id, site_id, created_by, actor_type, title, delegation_preset, "
                "status, expires_at) VALUES ($1, $2, $3, 'HUMAN', 'Other', "
                "'L2_SITE_EDITOR', 'ACTIVE', CURRENT_TIMESTAMP + interval '1 hour')",
                other_workspace_id,
                other_site_id,
                user_id,
            )
        for selected_id in (agent_workspace_id, import_workspace_id):
            authorized_projection = await RenderProjectionService(adapter).preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/staging/",
                    workspace_id=selected_id,
                    session_token=format_session_token(public_id, secret),
                )
            )
            assert authorized_projection.page.title == "Preview home"
        with pytest.raises(ProjectionError, match="not_found"):
            await RenderProjectionService(adapter).preview(
                RenderPreviewRequest(
                    authority="localhost",
                    path="/s/staging/",
                    workspace_id=other_workspace_id,
                    session_token=format_session_token(public_id, secret),
                )
            )
    finally:
        await editor_pool.close()
        await preview_pool.close()
        await public_pool.close()
        await control_pool.close()

"""Real PostgreSQL evidence for the Render public-reader resolver boundary."""

from __future__ import annotations

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.sites import CreateSiteRequest, DomainMappingRequest, SiteService
from slaif_agent_site.sites.resolver import (
    SiteResolver,
    SiteResolverError,
    SiteResolverReason,
)


async def test_public_reader_resolves_only_active_routing_context(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    public_pool = await database.role_pool("slaif_public_reader")
    control = SiteService(control_pool)
    resolver = SiteResolver(public_pool)
    try:
        root = await control.create(
            CreateSiteRequest(site_key="root", display_name="Root", default_locale="en")
        )
        docs = await control.create(
            CreateSiteRequest(
                site_key="docs", display_name="Docs", default_locale="sl-si"
            )
        )
        root_context = await control.resolve("localhost", "/s/root")
        docs_context = await control.resolve("localhost", "/s/docs")
        await control.put_domain(
            root_context,
            DomainMappingRequest(hostname="example.test", path_prefix="/"),
        )
        await control.put_domain(
            docs_context,
            DomainMappingRequest(hostname="example.test", path_prefix="/docs"),
        )

        assert (
            await resolver.resolve("EXAMPLE.TEST:443", "/docs/page/")
        ).site_id == docs.site_id
        assert (
            await resolver.resolve("example.test", "/docs-other")
        ).site_id == root.site_id
        assert (
            await resolver.resolve("localhost:8080", "/s/docs/page")
        ).site_id == docs.site_id

        await control.archive(docs_context)
        for authority, path in (
            ("localhost", "/s/docs"),
            ("example.test", "/api"),
            ("example.test", "/docs/%2e%2e"),
            ("example.test", "/docs\\x"),
        ):
            with pytest.raises(SiteResolverError) as denied:
                await resolver.resolve(authority, path)
            assert denied.value.reason == SiteResolverReason.NOT_FOUND

        async with public_pool.acquire() as connection:
            for query, arguments in (
                ("SELECT * FROM control.site", ()),
                ("SELECT * FROM control.slaif_site_list()", ()),
                ("SELECT * FROM control.slaif_site_get($1)", (root.site_id,)),
                (
                    "SELECT control.slaif_platform_administrator_authorized($1)",
                    (root.site_id,),
                ),
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch(query, *arguments)
    finally:
        await public_pool.close()
        await control_pool.close()

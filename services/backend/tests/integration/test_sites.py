"""Executable site persistence, isolation, quota, and privilege evidence."""

from __future__ import annotations

import asyncio

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.sites import (
    CreateSiteRequest,
    DomainMappingRequest,
    SiteContext,
    SiteRecord,
    SiteService,
    SiteServiceError,
    SiteServiceReason,
    SiteStatus,
    UpdateSiteRequest,
)


async def _site_service(
    database: AgentSiteDatabase,
) -> tuple[asyncpg.Pool[asyncpg.Record], SiteService]:
    pool = await database.role_pool("slaif_control")
    return pool, SiteService(pool)


async def _create(service: SiteService, key: str, locale: str = "en") -> SiteRecord:
    return await service.create(
        CreateSiteRequest(
            site_key=key,
            display_name=f"Site {key.title()}",
            default_locale=locale,
        )
    )


async def _local_context(service: SiteService, key: str) -> SiteContext:
    return await service.resolve("localhost:8080", f"/s/{key}/")


async def test_site_quota_is_atomic_under_concurrent_creates(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.site_policy SET max_sites = 1 WHERE singleton"
        )

    first_pool, first = await _site_service(database)
    second_pool, second = await _site_service(database)
    try:
        results = await asyncio.gather(
            _create(first, "alpha"), _create(second, "beta"), return_exceptions=True
        )
        successes = [result for result in results if not isinstance(result, Exception)]
        failures = [result for result in results if isinstance(result, Exception)]
        assert len(successes) == len(failures) == 1
        assert isinstance(failures[0], SiteServiceError)
        assert failures[0].reason is SiteServiceReason.CONFLICT
        assert len(await first.list()) == 1
    finally:
        await first_pool.close()
        await second_pool.close()


async def test_normalized_uniqueness_primary_reassignment_and_safe_removal(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool, service = await _site_service(database)
    try:
        site = await _create(service, "ALPHA", "sl-si")
        assert site.site_key == "alpha"
        assert site.default_locale == "sl-SI"
        context = await _local_context(service, "alpha")
        first = await service.put_domain(
            context,
            DomainMappingRequest(
                hostname="EXAMPLE.TEST.", path_prefix="/Research", is_primary=True
            ),
        )
        second = await service.put_domain(
            context,
            DomainMappingRequest(
                hostname="www.example.test", path_prefix="/", is_primary=True
            ),
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            rows = await owner.fetch(
                "SELECT id, is_primary FROM control.site_domain "
                "WHERE site_id = $1 ORDER BY hostname",
                site.site_id,
            )
        assert sum(bool(row[1]) for row in rows) == 1
        assert next(row[0] for row in rows if row[1]) == second.domain_id
        with pytest.raises(SiteServiceError) as primary_removal:
            await service.remove_domain(context, second.domain_id)
        assert primary_removal.value.reason is SiteServiceReason.CONFLICT
        await service.remove_domain(context, first.domain_id)
        with pytest.raises(SiteServiceError) as duplicate:
            await service.put_domain(
                context,
                DomainMappingRequest(
                    hostname="WWW.EXAMPLE.TEST", path_prefix="/", is_primary=False
                ),
            )
        assert duplicate.value.reason is SiteServiceReason.CONFLICT
    finally:
        await pool.close()


async def test_two_site_longest_prefix_local_resolution_and_cross_site_denial(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool, service = await _site_service(database)
    try:
        alpha = await _create(service, "alpha")
        beta = await _create(service, "beta", "de-de")
        alpha_context = await _local_context(service, "alpha")
        beta_context = await _local_context(service, "beta")
        alpha_domain = await service.put_domain(
            alpha_context,
            DomainMappingRequest(
                hostname="sites.example.test", path_prefix="/alpha", is_primary=True
            ),
        )
        beta_domain = await service.put_domain(
            beta_context,
            DomainMappingRequest(
                hostname="sites.example.test", path_prefix="/beta", is_primary=True
            ),
        )
        resolved_alpha = await service.resolve(
            "SITES.EXAMPLE.TEST:443", "/alpha/news/item"
        )
        resolved_beta = await service.resolve("sites.example.test", "/beta")
        assert resolved_alpha.site_id == alpha.site_id
        assert resolved_beta.site_id == beta.site_id
        assert (await _local_context(service, "alpha")).site_id == alpha.site_id
        assert (await _local_context(service, "beta")).site_id == beta.site_id
        for path in ("/alpha-other", "/unknown", "/api", "/preview/x"):
            with pytest.raises(SiteServiceError) as denied:
                await service.resolve("sites.example.test", path)
            assert denied.value.reason is SiteServiceReason.NOT_FOUND
        with pytest.raises(SiteServiceError) as substitution:
            await service.put_domain(
                alpha_context,
                DomainMappingRequest(
                    hostname="moved.example.test", path_prefix="/", is_primary=False
                ),
                domain_id=beta_domain.domain_id,
            )
        assert substitution.value.reason is SiteServiceReason.NOT_FOUND
        assert (
            await service.resolve("sites.example.test", "/beta/unchanged")
        ).site_id == beta.site_id
        assert alpha_domain.site_id != beta_domain.site_id
    finally:
        await pool.close()


async def test_archive_is_idempotent_stops_resolution_and_deletes_nothing(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool, service = await _site_service(database)
    try:
        site = await _create(service, "archive-me")
        context = await _local_context(service, "archive-me")
        mapping = await service.put_domain(
            context,
            DomainMappingRequest(
                hostname="archive.example.test", path_prefix="/", is_primary=True
            ),
        )
        archived = await service.archive(context)
        assert archived.status is SiteStatus.ARCHIVED
        assert (await service.archive(context)).status is SiteStatus.ARCHIVED
        for authority, path in (
            ("archive.example.test", "/"),
            ("localhost", "/s/archive-me/"),
        ):
            with pytest.raises(SiteServiceError) as denied:
                await service.resolve(authority, path)
            assert denied.value.reason is SiteServiceReason.NOT_FOUND
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.site WHERE id = $1", site.site_id
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.site_domain WHERE id = $1",
                    mapping.domain_id,
                )
                == 1
            )
    finally:
        await pool.close()


async def test_stale_pre_archive_context_cannot_mutate_profile_or_domains(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool, service = await _site_service(database)
    try:
        site = await _create(service, "stale-context")
        stale = await _local_context(service, site.site_key)
        primary = await service.put_domain(
            stale,
            DomainMappingRequest(
                hostname="stale.example.test", path_prefix="/", is_primary=True
            ),
        )
        secondary = await service.put_domain(
            stale,
            DomainMappingRequest(
                hostname="other.example.test", path_prefix="/", is_primary=False
            ),
        )
        await service.archive(stale)
        operations = (
            service.update(
                stale, UpdateSiteRequest(display_name="Forbidden", default_locale="de")
            ),
            service.put_domain(
                stale,
                DomainMappingRequest(
                    hostname="new.example.test", path_prefix="/", is_primary=False
                ),
            ),
            service.put_domain(
                stale,
                DomainMappingRequest(
                    hostname="changed.example.test",
                    path_prefix="/",
                    is_primary=False,
                ),
                domain_id=secondary.domain_id,
            ),
            service.remove_domain(stale, secondary.domain_id),
        )
        for operation in operations:
            with pytest.raises(SiteServiceError) as denied:
                await operation
            assert denied.value.reason is SiteServiceReason.CONFLICT
        unchanged = await service.get(site.site_id)
        assert unchanged.display_name == "Site Stale-Context"
        assert await service.list_domains(site.site_id) == (secondary, primary)
    finally:
        await pool.close()


async def test_revisions_are_server_owned_and_constraints_rollback_changes(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool, service = await _site_service(database)
    try:
        site = await _create(service, "fixed-revisions")
        context = await _local_context(service, site.site_key)
        updated = await service.update(
            context, UpdateSiteRequest(display_name="Updated", default_locale="fr-fr")
        )
        assert updated.canonical_revision == updated.content_model_revision == 0
        async with pool.acquire() as control:
            for statement in (
                "UPDATE control.site SET canonical_revision = 5 WHERE id = $1",
                "UPDATE control.site SET content_model_revision = -1 WHERE id = $1",
                "DELETE FROM control.site WHERE id = $1",
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await control.execute(statement, site.site_id)
        unchanged = await service.get(site.site_id)
        assert unchanged.canonical_revision == unchanged.content_model_revision == 0
    finally:
        await pool.close()


async def test_cancelled_create_rolls_back_without_consuming_quota(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool, service = await _site_service(database)
    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            transaction = owner.transaction()
            await transaction.start()
            await owner.fetchrow(
                "SELECT * FROM control.site_policy WHERE singleton FOR UPDATE"
            )
            task = asyncio.create_task(_create(service, "cancelled"))
            await asyncio.sleep(0.05)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            await transaction.rollback()
        assert await service.list() == ()
        assert (await _create(service, "after-cancel")).site_key == "after-cancel"
    finally:
        await pool.close()


async def test_exact_function_grants_and_relation_denial_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pools = {role: await database.role_pool(role) for role in ROLE_NAMES[1:]}
    try:
        async with pools["slaif_control"].acquire() as control:
            rows = await control.fetch("SELECT * FROM control.slaif_site_list()")
            assert rows == []
            for relation in (
                "control.site",
                "control.site_domain",
                "control.site_policy",
            ):
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await control.fetch(f"SELECT * FROM {relation}")
        for role, pool in pools.items():
            if role == "slaif_control":
                continue
            async with pool.acquire() as connection:
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch("SELECT * FROM control.slaif_site_list()")
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch("SELECT * FROM control.site")
    finally:
        for pool in pools.values():
            await pool.close()

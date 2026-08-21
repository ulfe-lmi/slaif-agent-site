"""Executable site-scoped membership, RBAC, atomicity, and grant evidence."""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.human_authorization import (
    ROLE_CEILINGS,
    ROLE_DEFAULTS,
    HumanAuthorizationError,
    HumanAuthorizationReason,
    HumanAuthorizationService,
    HumanSiteContext,
    MembershipChange,
    MembershipStatus,
)
from slaif_agent_site.human_authorization.catalog import PERMISSIONS
from slaif_agent_site.sites import CreateSiteRequest, SiteService


async def _user(
    owner: asyncpg.Connection[asyncpg.Record],
    *,
    active: bool = True,
    identifier: UUID | None = None,
) -> UUID:
    selected_identifier = identifier or uuid4()
    await owner.execute(
        "INSERT INTO control.user_account (id, identity_kind, oidc_issuer, "
        "oidc_subject, display_name, status) VALUES ($1, 'OIDC', 'fixture', "
        "$2, 'RBAC fixture', $3)",
        selected_identifier,
        str(selected_identifier),
        "ACTIVE" if active else "DISABLED",
    )
    return selected_identifier


async def _site(service: SiteService, key: str) -> UUID:
    return (
        await service.create(
            CreateSiteRequest(
                site_key=key, display_name=f"Site {key}", default_locale="en"
            )
        )
    ).site_id


async def _wait_for_database_lock(database: AgentSiteDatabase) -> bool:
    for _ in range(200):
        waiting = bool(
            await database.administrator.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_stat_activity "
                "WHERE datname=$1 AND wait_event_type='Lock' "
                "AND query LIKE '%slaif_membership_put%')",
                database.name,
            )
        )
        if waiting:
            return True
        await asyncio.sleep(0.01)
    return False


async def _fixture(
    database: AgentSiteDatabase,
) -> tuple[
    asyncpg.Pool[asyncpg.Record],
    HumanAuthorizationService,
    SiteService,
    UUID,
]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    pool = await database.role_pool("slaif_control")
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        administrator = await _user(owner)
        await owner.execute(
            "INSERT INTO control.platform_administrator (user_account_id) VALUES ($1)",
            administrator,
        )
    return pool, HumanAuthorizationService(pool), SiteService(pool), administrator


async def test_exact_role_matrix_two_site_isolation_and_publish_orthogonality(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    pool, authorization, sites, administrator = await _fixture(database)
    try:
        alpha = await _site(sites, "alpha-rbac")
        beta = await _site(sites, "beta-rbac")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            users = {role: await _user(owner) for role in ROLE_CEILINGS}
        for role, user in users.items():
            context = await authorization.put_membership(
                administrator,
                alpha,
                user,
                MembershipChange(role_key=role, delegation_ceiling=ROLE_CEILINGS[role]),
            )
            assert context.effective_delegation_ceiling == ROLE_CEILINGS[role]
            assert context.effective_permissions == ROLE_DEFAULTS[role]
        catalog = await authorization.catalog()
        assert [item.permission_key for item in catalog] == [
            item.key for item in PERMISSIONS
        ]
        assert len(await authorization.memberships(alpha)) == len(ROLE_CEILINGS)
        assert (await authorization.membership(alpha, users["VIEWER"])).role_key == (
            "VIEWER"
        )

        architect = users["SITE_ARCHITECT"]
        original = await authorization.authorize(
            architect, alpha, "site:read", expected_membership_version=1
        )
        assert original.effective_delegation_ceiling == 4
        assert "site:publish" not in original.effective_permissions
        published = await authorization.put_membership(
            administrator,
            alpha,
            architect,
            MembershipChange(
                role_key="SITE_ARCHITECT",
                delegation_ceiling=4,
                expected_version=1,
                allow_permissions=frozenset({"site:publish"}),
            ),
        )
        assert published.effective_permissions == ROLE_DEFAULTS["SITE_ARCHITECT"] | {
            "site:publish"
        }
        assert published.effective_delegation_ceiling == 4

        owner_user = users["SITE_OWNER"]
        denied_publish = await authorization.put_membership(
            administrator,
            alpha,
            owner_user,
            MembershipChange(
                role_key="SITE_OWNER",
                delegation_ceiling=4,
                expected_version=1,
                deny_permissions=frozenset({"site:publish"}),
            ),
        )
        assert "site:publish" not in denied_publish.effective_permissions
        assert denied_publish.effective_delegation_ceiling == 4
        assert "content-model:write" in denied_publish.effective_permissions

        beta_context = await authorization.put_membership(
            administrator,
            beta,
            architect,
            MembershipChange(role_key="VIEWER", delegation_ceiling=0),
        )
        assert beta_context.role_key == "VIEWER"
        with pytest.raises(HumanAuthorizationError) as crossed:
            await authorization.authorize(
                architect, beta, "content-model:write", expected_membership_version=1
            )
        assert crossed.value.reason is HumanAuthorizationReason.DENIED
    finally:
        await pool.close()


async def test_actor_limits_versions_deactivation_and_failure_atomicity(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    pool, authorization, sites, administrator = await _fixture(database)
    second_pool = await database.role_pool("slaif_control")
    second_authorization = HumanAuthorizationService(second_pool)
    try:
        alpha = await _site(sites, "policy-rbac")
        beta = await _site(sites, "other-rbac")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            owner_user = await _user(owner)
            target = await _user(owner)
            disabled = await _user(owner, active=False)
        await authorization.put_membership(
            administrator,
            alpha,
            owner_user,
            MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4),
        )
        member = await authorization.put_membership(
            owner_user,
            alpha,
            target,
            MembershipChange(role_key="SITE_EDITOR", delegation_ceiling=2),
        )
        assert member.membership_version == 1
        for actor, site, change in (
            (
                target,
                alpha,
                MembershipChange(
                    role_key="SITE_OWNER",
                    delegation_ceiling=4,
                    expected_version=1,
                ),
            ),
            (
                owner_user,
                beta,
                MembershipChange(role_key="VIEWER", delegation_ceiling=0),
            ),
            (
                owner_user,
                alpha,
                MembershipChange(
                    role_key="SITE_EDITOR",
                    delegation_ceiling=2,
                    expected_version=1,
                    allow_permissions=frozenset({"schema:migrate"}),
                ),
            ),
        ):
            with pytest.raises(HumanAuthorizationError) as denied:
                await authorization.put_membership(actor, site, target, change)
            assert denied.value.reason in {
                HumanAuthorizationReason.DENIED,
                HumanAuthorizationReason.NOT_FOUND,
            }
        with pytest.raises(HumanAuthorizationError) as inactive_target:
            await authorization.put_membership(
                administrator,
                alpha,
                disabled,
                MembershipChange(role_key="VIEWER", delegation_ceiling=0),
            )
        assert inactive_target.value.reason is HumanAuthorizationReason.DENIED

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            async with owner.transaction():
                await owner.fetchrow(
                    "SELECT 1 FROM control.site_membership "
                    "WHERE site_id=$1 AND user_account_id=$2 FOR UPDATE",
                    alpha,
                    target,
                )
                blocked = asyncio.create_task(
                    authorization.put_membership(
                        owner_user,
                        alpha,
                        target,
                        MembershipChange(
                            role_key="CONTENT_EDITOR",
                            delegation_ceiling=1,
                            expected_version=1,
                        ),
                    )
                )
                await asyncio.sleep(0.05)
                blocked.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await blocked
        unchanged = await authorization.authorize(
            target, alpha, "site:read", expected_membership_version=1
        )
        assert unchanged.role_key == "SITE_EDITOR"

        async with pool.acquire() as connection:
            with pytest.raises(asyncpg.UniqueViolationError):
                async with connection.transaction():
                    await connection.fetchrow(
                        "SELECT * FROM control.slaif_membership_put("
                        "$1,$2,$3,$4,$5,$6,$7,$8)",
                        owner_user,
                        alpha,
                        target,
                        "CONTENT_EDITOR",
                        1,
                        "ACTIVE",
                        1,
                        ["ALLOW:site:read", "ALLOW:site:read"],
                    )
        assert (
            await authorization.authorize(
                target, alpha, "site:read", expected_membership_version=1
            )
        ).role_key == "SITE_EDITOR"

        first, second = await asyncio.gather(
            second_authorization.put_membership(
                owner_user,
                alpha,
                target,
                MembershipChange(
                    role_key="CONTENT_EDITOR",
                    delegation_ceiling=1,
                    expected_version=1,
                ),
            ),
            authorization.put_membership(
                owner_user,
                alpha,
                target,
                MembershipChange(
                    role_key="VIEWER", delegation_ceiling=0, expected_version=1
                ),
            ),
            return_exceptions=True,
        )
        assert (
            sum(not isinstance(result, BaseException) for result in (first, second))
            == 1
        )
        assert (
            sum(
                isinstance(result, HumanAuthorizationError)
                for result in (first, second)
            )
            == 1
        )
        winner = next(
            result
            for result in (first, second)
            if not isinstance(result, BaseException)
        )
        assert isinstance(winner, HumanSiteContext)
        assert winner.membership_version == 2
        deactivated = await authorization.put_membership(
            owner_user,
            alpha,
            target,
            MembershipChange(
                role_key=winner.role_key,
                delegation_ceiling=winner.explicit_delegation_ceiling,
                status=MembershipStatus.INACTIVE,
                expected_version=2,
            ),
        )
        assert deactivated.membership_version == 3
        assert deactivated.effective_permissions == frozenset()
        with pytest.raises(HumanAuthorizationError) as inactive:
            await authorization.authorize(
                target, alpha, "site:read", expected_membership_version=3
            )
        assert inactive.value.reason is HumanAuthorizationReason.DENIED
    finally:
        await second_pool.close()
        await pool.close()


async def test_catalog_and_membership_relations_are_owner_only(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    relations = (
        "permission",
        "human_role",
        "human_role_permission",
        "site_membership",
        "site_membership_permission_override",
    )
    functions = (
        "slaif_effective_human_membership",
        "slaif_human_authorize",
        "slaif_human_rbac_catalog",
        "slaif_membership_get",
        "slaif_membership_list",
        "slaif_membership_put",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert await owner.fetchval("SELECT count(*) FROM control.permission") == len(
            PERMISSIONS
        )
        for role in ROLE_NAMES[1:]:
            for relation in relations:
                assert not await owner.fetchval(
                    "SELECT has_table_privilege($1, 'control.' || $2, 'SELECT')",
                    role,
                    relation,
                )
            for function in functions:
                allowed = await owner.fetchval(
                    "SELECT has_function_privilege($1, proc.oid, 'EXECUTE') "
                    "FROM pg_catalog.pg_proc proc JOIN pg_catalog.pg_namespace ns "
                    "ON ns.oid=proc.pronamespace WHERE ns.nspname='control' "
                    "AND proc.proname=$2",
                    role,
                    function,
                )
                assert bool(allowed) is (role == "slaif_control")


async def test_actor_authority_revocation_serializes_before_grant(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    pool, authorization, sites, administrator = await _fixture(database)
    try:
        site = await _site(sites, "authority-lock-rbac")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            actors = [await _user(owner) for _ in range(3)]
            targets = [await _user(owner) for _ in range(3)]
        for actor, target in zip(actors, targets, strict=True):
            await authorization.put_membership(
                administrator,
                site,
                actor,
                MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4),
            )
            await authorization.put_membership(
                actor,
                site,
                target,
                MembershipChange(role_key="VIEWER", delegation_ceiling=0),
            )

        statements = (
            (
                "UPDATE control.site_membership SET role_key='CONTENT_EDITOR', "
                "delegation_ceiling=1, version=version+1 WHERE site_id=$1 "
                "AND user_account_id=$2",
                (site, actors[0]),
            ),
            (
                "INSERT INTO control.site_membership_permission_override "
                "(site_id,user_account_id,permission_key,effect) "
                "VALUES ($1,$2,'membership:manage','DENY')",
                (site, actors[1]),
            ),
            (
                "UPDATE control.user_account SET status='DISABLED' WHERE id=$1",
                (actors[2],),
            ),
        )
        for (statement, arguments), actor, target in zip(
            statements, actors, targets, strict=True
        ):
            async with owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as revoker:
                async with revoker.transaction():
                    await revoker.execute(statement, *arguments)
                    grant = asyncio.create_task(
                        authorization.put_membership(
                            actor,
                            site,
                            target,
                            MembershipChange(
                                role_key="SITE_EDITOR",
                                delegation_ceiling=2,
                                expected_version=1,
                            ),
                        )
                    )
                    assert await _wait_for_database_lock(database)
                    assert not grant.done()
                with pytest.raises(HumanAuthorizationError) as denied:
                    await grant
                assert denied.value.reason is HumanAuthorizationReason.DENIED
                unchanged = await authorization.membership(site, target)
                assert unchanged.role_key == "VIEWER"
                assert unchanged.version == 1
    finally:
        await pool.close()


async def test_grant_first_and_reversed_updates_have_serial_outcomes(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    pool, authorization, sites, administrator = await _fixture(database)
    second_pool = await database.role_pool("slaif_control")
    second_authorization = HumanAuthorizationService(second_pool)
    try:
        site = await _site(sites, "serial-order-rbac")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            actor = await _user(
                owner,
                identifier=UUID("10000000-0000-4000-8000-000000000001"),
            )
            target = await _user(
                owner,
                identifier=UUID("f0000000-0000-4000-8000-000000000001"),
            )
            left = await _user(owner)
            right = await _user(owner)
        for user in (actor, left, right):
            await authorization.put_membership(
                administrator,
                site,
                user,
                MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4),
            )
        await authorization.put_membership(
            actor,
            site,
            target,
            MembershipChange(role_key="VIEWER", delegation_ceiling=0),
        )

        async with (
            owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as blocker,
            owner_connection(
                database.settings.resolved_owner_dsn(),
                expected_database=database.name,
            ) as revoker,
        ):
            async with blocker.transaction():
                await blocker.fetchrow(
                    "SELECT 1 FROM control.site_membership WHERE site_id=$1 "
                    "AND user_account_id=$2 FOR UPDATE",
                    site,
                    target,
                )
                grant = asyncio.create_task(
                    second_authorization.put_membership(
                        actor,
                        site,
                        target,
                        MembershipChange(
                            role_key="SITE_EDITOR",
                            delegation_ceiling=2,
                            expected_version=1,
                        ),
                    )
                )
                waiting = await _wait_for_database_lock(database)
                assert not grant.done(), repr(grant.exception())
                assert waiting
                revoke = asyncio.create_task(
                    revoker.execute(
                        "UPDATE control.site_membership SET status='INACTIVE', "
                        "version=version+1 WHERE site_id=$1 AND user_account_id=$2",
                        site,
                        actor,
                    )
                )
                await asyncio.sleep(0.05)
                assert not grant.done()
                assert not revoke.done()
            granted = await grant
            await revoke
        assert granted.role_key == "SITE_EDITOR"
        assert granted.membership_version == 2
        assert (await authorization.membership(site, actor)).status is (
            MembershipStatus.INACTIVE
        )

        first, second = await asyncio.gather(
            authorization.put_membership(
                left,
                site,
                right,
                MembershipChange(
                    role_key="VIEWER", delegation_ceiling=0, expected_version=1
                ),
            ),
            second_authorization.put_membership(
                right,
                site,
                left,
                MembershipChange(
                    role_key="VIEWER", delegation_ceiling=0, expected_version=1
                ),
            ),
            return_exceptions=True,
        )
        outcomes = (first, second)
        assert sum(isinstance(result, HumanSiteContext) for result in outcomes) == 1
        denial = next(
            result for result in outcomes if isinstance(result, HumanAuthorizationError)
        )
        assert denial.reason is HumanAuthorizationReason.DENIED
    finally:
        await second_pool.close()
        await pool.close()


async def test_inactive_context_reports_target_platform_administrator(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    pool, authorization, sites, administrator = await _fixture(database)
    try:
        site = await _site(sites, "target-admin-rbac")
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            owner_user = await _user(owner)
            target_admin = await _user(owner)
            ordinary_target = await _user(owner)
            await owner.execute(
                "INSERT INTO control.platform_administrator (user_account_id) "
                "VALUES ($1)",
                target_admin,
            )
        await authorization.put_membership(
            administrator,
            site,
            owner_user,
            MembershipChange(role_key="SITE_OWNER", delegation_ceiling=4),
        )
        active = await authorization.put_membership(
            owner_user,
            site,
            target_admin,
            MembershipChange(role_key="VIEWER", delegation_ceiling=0),
        )
        assert active.platform_administrator
        inactive = await authorization.put_membership(
            owner_user,
            site,
            target_admin,
            MembershipChange(
                role_key="VIEWER",
                delegation_ceiling=0,
                status=MembershipStatus.INACTIVE,
                expected_version=1,
            ),
        )
        assert inactive.platform_administrator
        ordinary = await authorization.put_membership(
            administrator,
            site,
            ordinary_target,
            MembershipChange(role_key="VIEWER", delegation_ceiling=0),
        )
        assert not ordinary.platform_administrator
    finally:
        await pool.close()

"""Real-role integration coverage for the human AGENT-workspace Editor envelope."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast
from urllib.parse import quote

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_session,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.content_model.service import ContentModelService
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.editor_api.app import create_app
from slaif_agent_site.editor_api.config import (
    EditorDatabaseMode,
    EditorDatabaseSettings,
)
from slaif_agent_site.editor_api.database import EditorDatabase

PERMISSION = "page:create"
DENIAL = "HUMAN_AGENT_EDITOR_WORKSPACE_NOT_ACCESSIBLE"
COW_CONTEXT = "HUMAN_AGENT_EDITOR_COW_CONTEXT_INVALID"


async def _create_agent_workspace(
    pool: asyncpg.Pool[Any],
    *,
    site_id: uuid.UUID,
    delegator_id: uuid.UUID,
    title: str,
    status: str = "ACTIVE",
    expires_offset_hours: int = 1,
) -> uuid.UUID:
    async with pool.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT * FROM control.slaif_human_agent_workspace_create("
            "$1,$2,$3,$4,'L2_SITE_EDITOR',ARRAY['page:create']::text[],"
            "'{}'::jsonb,ARRAY[]::text[],4,2,1,1,1,1)",
            site_id,
            delegator_id,
            title,
            "Integration Agent workspace.",
        )
        assert row is not None
        created = cast(uuid.UUID, row["id"])
        if status != "ACTIVE" or expires_offset_hours != 1:
            await connection.execute(
                "UPDATE control.workspace SET status = $2, "
                "expires_at = CURRENT_TIMESTAMP + make_interval(hours => $3) "
                "WHERE id = $1",
                created,
                status,
                expires_offset_hours,
            )
        return created


async def _resolve_human_workspace(
    pool: asyncpg.Pool[Any], site_id: uuid.UUID, user_id: uuid.UUID
) -> uuid.UUID:
    async with pool.acquire() as connection:
        return cast(
            uuid.UUID,
            await connection.fetchval(
                "SELECT control.slaif_human_editor_workspace_resolve($1, $2)",
                site_id,
                user_id,
            ),
        )


@asynccontextmanager
async def _cow(
    pool: asyncpg.Pool[Any],
    *,
    workspace_id: uuid.UUID,
    operation_id: uuid.UUID,
) -> AsyncIterator[Any]:
    async with asyncpg_cow_session(
        pool, session_id=workspace_id, operation_id=operation_id
    ) as cow:
        yield cow


async def _agent_assert(
    cow: Any,
    *,
    workspace_id: uuid.UUID,
    human_user_id: uuid.UUID,
    site_id: uuid.UUID,
    human_session_id: uuid.UUID,
    permission: str = PERMISSION,
    lock: bool = True,
) -> None:
    await cow.native.fetchrow(
        "SELECT control.slaif_human_agent_workspace_editor_assert($1,$2,$3,$4,$5,$6)",
        workspace_id,
        human_user_id,
        site_id,
        human_session_id,
        permission,
        lock,
    )


def _denial_info(error: BaseException) -> tuple[str, str]:
    assert isinstance(error, asyncpg.PostgresError)
    return (error.sqlstate, str(error))


async def _wait_for_advisory_waiter(
    administrator: asyncpg.Connection[Any], pid: int
) -> None:
    for _ in range(1000):
        row = await administrator.fetchrow(
            "SELECT wait_event_type, wait_event, state "
            "FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
        if row is not None and tuple(row) == ("Lock", "advisory", "active"):
            return
        await asyncio.sleep(0)
    raise AssertionError("Agent Editor assertion did not wait on the shared lock")


@pytest.mark.asyncio
async def test_human_agent_editor_assert_predicate_matrix(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    owner_pool = await database.role_pool("slaif_owner")
    editor_pool = await database.role_pool("slaif_editor_runtime")
    site_id = uuid.uuid4()
    other_site_id = uuid.uuid4()
    delegator_id = uuid.uuid4()
    noncreator_id = uuid.uuid4()
    readall_id = uuid.uuid4()
    lowrole_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    outsider_id = uuid.uuid4()
    other_delegator_id = uuid.uuid4()
    sessions: dict[str, uuid.UUID] = {}
    try:
        async with owner_pool.acquire() as owner:
            for label, user_id in (
                ("Delegator", delegator_id),
                ("NonCreator", noncreator_id),
                ("ReadAll", readall_id),
                ("LowRole", lowrole_id),
                ("Admin", admin_id),
                ("Outsider", outsider_id),
                ("OtherDelegator", other_delegator_id),
            ):
                await owner.execute(
                    "INSERT INTO control.user_account "
                    "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                    "VALUES ($1, 'OIDC', 'https://agent-editor.test', $2, $3)",
                    user_id,
                    str(user_id),
                    label,
                )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, $2, 'Agent Editor Site', 'en', 'catalog-v1'), "
                "($3, $4, 'Other Agent Editor Site', 'en', 'catalog-v1')",
                site_id,
                f"agent-editor-{uuid.uuid4().hex[:12]}",
                other_site_id,
                f"agent-editor-other-{uuid.uuid4().hex[:12]}",
            )
            for user_id, role_key, ceiling in (
                (delegator_id, "SITE_OWNER", 4),
                (noncreator_id, "SITE_EDITOR", 2),
                (readall_id, "SITE_EDITOR", 2),
                (lowrole_id, "VIEWER", 0),
                (admin_id, "VIEWER", 0),
            ):
                await owner.execute(
                    "INSERT INTO control.site_membership "
                    "(site_id, user_account_id, role_key, delegation_ceiling) "
                    "VALUES ($1, $2, $3, $4)",
                    site_id,
                    user_id,
                    role_key,
                    ceiling,
                )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id, user_account_id, role_key, delegation_ceiling) "
                "VALUES ($1, $2, $3, $4)",
                other_site_id,
                other_delegator_id,
                "SITE_OWNER",
                4,
            )
            await owner.execute(
                "INSERT INTO control.site_membership_permission_override "
                "(site_id, user_account_id, permission_key, effect) "
                "VALUES ($1, $2, 'workspace:read-all', 'ALLOW')",
                site_id,
                readall_id,
            )
            await owner.execute(
                "INSERT INTO control.platform_administrator (user_account_id) "
                "VALUES ($1)",
                admin_id,
            )
            for label, user_id in (
                ("Delegator", delegator_id),
                ("NonCreator", noncreator_id),
                ("ReadAll", readall_id),
                ("LowRole", lowrole_id),
                ("Admin", admin_id),
                ("Outsider", outsider_id),
            ):
                session = await owner.fetchrow(
                    "SELECT * FROM control.slaif_create_human_session("
                    "$1,$2,$3,$4,$5,$6,$7,$8)",
                    uuid.uuid4(),
                    f"sas2_{uuid.uuid4().hex}",
                    uuid.uuid4().bytes * 2,
                    uuid.uuid4().bytes * 2,
                    user_id,
                    3600,
                    7200,
                    3600,
                )
                assert session is not None
                sessions[label] = cast(uuid.UUID, session[0])
            await owner.execute(
                "INSERT INTO content.page "
                "(id, site_id, slug, title, status, locale) "
                "VALUES ($1, $2, 'canonical-page', 'Canonical page', 'DRAFT', 'en')",
                uuid.uuid4(),
                site_id,
            )
        await reconcile(database.settings)
        workspace = await _create_agent_workspace(
            owner_pool,
            site_id=site_id,
            delegator_id=delegator_id,
            title="Matrix Agent workspace",
        )
        revoked_workspace = await _create_agent_workspace(
            owner_pool,
            site_id=site_id,
            delegator_id=delegator_id,
            title="Revoked Agent workspace",
            status="REVOKED",
        )
        expired_workspace = await _create_agent_workspace(
            owner_pool,
            site_id=site_id,
            delegator_id=delegator_id,
            title="Expired Agent workspace",
            expires_offset_hours=-1,
        )
        human_workspace = await _resolve_human_workspace(
            owner_pool, site_id, delegator_id
        )

        async def allowed(user: str, workspace_id: uuid.UUID) -> None:
            async with _cow(
                editor_pool,
                workspace_id=workspace_id,
                operation_id=uuid.uuid4(),
            ) as cow:
                await _agent_assert(
                    cow,
                    workspace_id=workspace_id,
                    human_user_id=user_id_for(user),
                    site_id=site_id,
                    human_session_id=sessions[user],
                )

        async def denied(user: str, workspace_id: uuid.UUID) -> tuple[str, str]:
            with pytest.raises(asyncpg.PostgresError) as excinfo:
                async with _cow(
                    editor_pool,
                    workspace_id=workspace_id,
                    operation_id=uuid.uuid4(),
                ) as cow:
                    await _agent_assert(
                        cow,
                        workspace_id=workspace_id,
                        human_user_id=user_id_for(user),
                        site_id=site_id,
                        human_session_id=sessions[user],
                    )
            return _denial_info(excinfo.value)

        def user_id_for(user: str) -> uuid.UUID:
            return {
                "Delegator": delegator_id,
                "NonCreator": noncreator_id,
                "ReadAll": readall_id,
                "LowRole": lowrole_id,
                "Admin": admin_id,
                "Outsider": outsider_id,
            }[user]

        # Allowed: delegator/creator, platform administrator, read-all member.
        await allowed("Delegator", workspace)
        await allowed("Admin", workspace)
        await allowed("ReadAll", workspace)

        # Denied: nonmember, member without read-all who is not the creator,
        # role-ceiling (creator lacking the route permission key).
        for user in ("Outsider", "NonCreator", "LowRole"):
            sqlstate, message = await denied(user, workspace)
            assert sqlstate == "P0002"
            assert DENIAL in message

        # Non-leaking: cross-site, REVOKED, EXPIRED, HUMAN workspace, revoked
        # session, and a nonexistent workspace all raise the identical denial.
        other_workspace = await _create_agent_workspace(
            owner_pool,
            site_id=other_site_id,
            delegator_id=other_delegator_id,
            title="Other site Agent workspace",
        )
        cross_site, cross_message = await denied("Delegator", other_workspace)
        unknown = uuid.uuid4()
        unknown_state, unknown_message = await denied("Delegator", unknown)
        assert (cross_site, cross_message) == (unknown_state, unknown_message)
        for workspace_id in (
            revoked_workspace,
            expired_workspace,
            human_workspace,
        ):
            state, message = await denied("Delegator", workspace_id)
            assert (state, message) == (unknown_state, unknown_message)

        async with owner_pool.acquire() as owner:
            await owner.execute(
                "UPDATE control.user_session SET revoked_at = CURRENT_TIMESTAMP "
                "WHERE id = $1",
                sessions["Delegator"],
            )
        state, message = await denied("Delegator", workspace)
        assert (state, message) == (unknown_state, unknown_message)
        async with owner_pool.acquire() as owner:
            await owner.execute(
                "UPDATE control.user_session SET revoked_at = NULL WHERE id = $1",
                sessions["Delegator"],
            )
        await allowed("Delegator", workspace)

        # COW context integrity: mismatched/absent context is the same internal
        # error class as the HUMAN path (22023), distinct from denial.
        with pytest.raises(asyncpg.PostgresError) as excinfo:
            async with _cow(
                editor_pool,
                workspace_id=uuid.uuid4(),
                operation_id=uuid.uuid4(),
            ) as cow:
                await _agent_assert(
                    cow,
                    workspace_id=workspace,
                    human_user_id=delegator_id,
                    site_id=site_id,
                    human_session_id=sessions["Delegator"],
                )
        assert excinfo.value.sqlstate == "22023"
        assert COW_CONTEXT in str(excinfo.value)
    finally:
        await owner_pool.close()
        await editor_pool.close()


@pytest.mark.asyncio
async def test_human_agent_editor_idempotency_audit_and_lock_serialization(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    owner_pool = await database.role_pool("slaif_owner")
    editor_pool = await database.role_pool("slaif_editor_runtime")
    second_pool = await database.role_pool("slaif_editor_runtime")
    site_id = uuid.uuid4()
    delegator_id = uuid.uuid4()
    reader_id = uuid.uuid4()
    delegator_session = uuid.uuid4()
    reader_session = uuid.uuid4()
    try:
        async with owner_pool.acquire() as owner:
            for user_id, label in (
                (delegator_id, "Delegator"),
                (reader_id, "Reader"),
            ):
                await owner.execute(
                    "INSERT INTO control.user_account "
                    "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                    "VALUES ($1, 'OIDC', 'https://agent-editor.test', $2, $3)",
                    user_id,
                    str(user_id),
                    label,
                )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, $2, 'Agent Editor Site', 'en', 'catalog-v1')",
                site_id,
                f"agent-editor-{uuid.uuid4().hex[:12]}",
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id, user_account_id, role_key, delegation_ceiling) "
                "VALUES ($1, $2, 'SITE_OWNER', 4)",
                site_id,
                delegator_id,
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id, user_account_id, role_key, delegation_ceiling) "
                "VALUES ($1, $2, 'SITE_EDITOR', 2)",
                site_id,
                reader_id,
            )
            await owner.execute(
                "INSERT INTO control.site_membership_permission_override "
                "(site_id, user_account_id, permission_key, effect) "
                "VALUES ($1, $2, 'workspace:read-all', 'ALLOW')",
                site_id,
                reader_id,
            )
            for session_id, user_id in (
                (delegator_session, delegator_id),
                (reader_session, reader_id),
            ):
                session = await owner.fetchrow(
                    "SELECT * FROM control.slaif_create_human_session("
                    "$1,$2,$3,$4,$5,$6,$7,$8)",
                    session_id,
                    f"sas2_{uuid.uuid4().hex}",
                    uuid.uuid4().bytes * 2,
                    uuid.uuid4().bytes * 2,
                    user_id,
                    3600,
                    7200,
                    3600,
                )
                assert session is not None
            await owner.execute(
                "INSERT INTO content.page "
                "(id, site_id, slug, title, status, locale) "
                "VALUES ($1, $2, 'canonical-page', 'Canonical page', 'DRAFT', 'en')",
                uuid.uuid4(),
                site_id,
            )
        await reconcile(database.settings)
        workspace = await _create_agent_workspace(
            owner_pool,
            site_id=site_id,
            delegator_id=delegator_id,
            title="Envelope Agent workspace",
        )

        key = f"page-{uuid.uuid4().hex}"
        digest = "a" * 64
        operation_id = uuid.uuid4()
        created_page_id: uuid.UUID | None = None
        async with _cow(
            editor_pool, workspace_id=workspace, operation_id=operation_id
        ) as cow:
            await _agent_assert(
                cow,
                workspace_id=workspace,
                human_user_id=delegator_id,
                site_id=site_id,
                human_session_id=delegator_session,
            )
            started = await cow.native.fetchrow(
                "SELECT * FROM control.slaif_human_agent_editor_idempotency_begin("
                "$1,$2,$3,$4,$5,$6,$7,$8)",
                workspace,
                delegator_id,
                site_id,
                delegator_session,
                PERMISSION,
                key,
                digest,
                operation_id,
            )
            assert started[0] == "STARTED"
            service = ContentModelService.for_cow_session(cow)
            page = await service.create_page(
                site_id, "agent-overlay-page", "Agent overlay page", "DRAFT", "en"
            )
            created_page_id = page.id
            await cow.native.fetchrow(
                "SELECT control.slaif_human_agent_editor_idempotency_complete("
                "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                workspace,
                delegator_id,
                site_id,
                delegator_session,
                PERMISSION,
                key,
                digest,
                operation_id,
                201,
                json.dumps({"id": str(page.id)}, sort_keys=True),
                "POST /api/editor/v1/pages",
                "page",
                page.id,
            )
        assert created_page_id is not None

        async with owner_pool.acquire() as owner:
            # The mutation landed in the AGENT workspace with the HUMAN actor.
            audit = await owner.fetchrow(
                "SELECT * FROM audit.human_editor_mutation WHERE operation_id = $1",
                operation_id,
            )
            assert audit is not None
            assert audit["human_user_id"] == delegator_id
            assert audit["workspace_id"] == workspace
            assert audit["site_id"] == site_id
            # Canonical is unchanged.
            canonical = await owner.fetch(
                "SELECT * FROM content.slaif_page_list($1)", site_id
            )
            assert {row[2] for row in canonical} == {"canonical-page"}

        # Idempotency replay returns the stored response; mismatch is detected.
        replay_operation = uuid.uuid4()
        async with _cow(
            editor_pool, workspace_id=workspace, operation_id=replay_operation
        ) as cow:
            replay = await cow.native.fetchrow(
                "SELECT * FROM control.slaif_human_agent_editor_idempotency_begin("
                "$1,$2,$3,$4,$5,$6,$7,$8)",
                workspace,
                delegator_id,
                site_id,
                delegator_session,
                PERMISSION,
                key,
                digest,
                replay_operation,
            )
            assert replay[0] == "REPLAY"
            assert replay[2] == 201
            body = replay[3]
            body = json.loads(body) if isinstance(body, str) else body
            assert body["id"] == str(created_page_id)
            mismatch = await cow.native.fetchrow(
                "SELECT * FROM control.slaif_human_agent_editor_idempotency_begin("
                "$1,$2,$3,$4,$5,$6,$7,$8)",
                workspace,
                delegator_id,
                site_id,
                delegator_session,
                PERMISSION,
                key,
                "c" * 64,
                uuid.uuid4(),
            )
            assert mismatch[0] == "MISMATCH"

        # Two concurrent humans on the same Agent workspace serialize on the
        # shared advisory lock 280: human B blocks until human A commits.
        release_holder = asyncio.Event()

        async def wait_idle_in_transaction(pid: int) -> None:
            for _ in range(1000):
                row = await database.administrator.fetchrow(
                    "SELECT state FROM pg_catalog.pg_stat_activity WHERE pid = $1",
                    pid,
                )
                if row is not None and row[0] == "idle in transaction":
                    return
                await asyncio.sleep(0)
            raise AssertionError("holder did not reach idle in transaction")

        async def human_a(connection: asyncpg.Connection[Any]) -> None:
            async with asyncpg_cow_session(
                connection, session_id=workspace, operation_id=uuid.uuid4()
            ) as cow:
                await _agent_assert(
                    cow,
                    workspace_id=workspace,
                    human_user_id=delegator_id,
                    site_id=site_id,
                    human_session_id=delegator_session,
                )
                await release_holder.wait()

        async def human_b(connection: asyncpg.Connection[Any]) -> None:
            async with asyncpg_cow_session(
                connection, session_id=workspace, operation_id=uuid.uuid4()
            ) as cow:
                await _agent_assert(
                    cow,
                    workspace_id=workspace,
                    human_user_id=reader_id,
                    site_id=site_id,
                    human_session_id=reader_session,
                )

        async with (
            editor_pool.acquire() as a_connection,
            second_pool.acquire() as b_connection,
        ):
            task_a = asyncio.create_task(human_a(a_connection))
            await wait_idle_in_transaction(a_connection.get_server_pid())
            task_b = asyncio.create_task(human_b(b_connection))
            await _wait_for_advisory_waiter(
                database.administrator, b_connection.get_server_pid()
            )
            assert not task_a.done()
            assert not task_b.done()
            release_holder.set()
            await task_a
            await task_b
        assert not task_a.cancelled()
        assert not task_b.cancelled()
    finally:
        await owner_pool.close()
        await editor_pool.close()
        await second_pool.close()


def _control_settings(database: AgentSiteDatabase) -> Any:
    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-agent-editor-http-test-control",
    )


def _editor_db_settings(database: AgentSiteDatabase) -> Any:
    login, password = database.credentials["slaif_editor_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return EditorDatabaseSettings(
        mode=EditorDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-agent-editor-http-test-editor",
    )


@pytest.mark.asyncio
async def test_editor_http_workspace_selection_is_server_authoritative(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    owner_pool = await database.role_pool("slaif_owner")
    site_id = uuid.uuid4()
    delegator_id = uuid.uuid4()
    other_id = uuid.uuid4()
    page_id = uuid.uuid4()
    control: ControlDatabase | None = None
    editor: EditorDatabase | None = None
    try:
        async with owner_pool.acquire() as owner:
            for user_id, label in (
                (delegator_id, "Delegator"),
                (other_id, "Other"),
            ):
                await owner.execute(
                    "INSERT INTO control.user_account "
                    "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                    "VALUES ($1, 'OIDC', 'https://agent-editor.test', $2, $3)",
                    user_id,
                    str(user_id),
                    label,
                )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, $2, 'Agent Editor Site', 'en', 'catalog-v1')",
                site_id,
                f"agent-editor-{uuid.uuid4().hex[:12]}",
            )
            for user_id, role_key, ceiling in (
                (delegator_id, "SITE_OWNER", 4),
                (other_id, "SITE_EDITOR", 2),
            ):
                await owner.execute(
                    "INSERT INTO control.site_membership "
                    "(site_id, user_account_id, role_key, delegation_ceiling) "
                    "VALUES ($1, $2, $3, $4)",
                    site_id,
                    user_id,
                    role_key,
                    ceiling,
                )
            await owner.execute(
                "INSERT INTO content.page "
                "(id, site_id, slug, title, status, locale) "
                "VALUES ($1, $2, 'canonical-page', 'Canonical page', 'DRAFT', 'en')",
                page_id,
                site_id,
            )
        await reconcile(database.settings)
        workspace = await _create_agent_workspace(
            owner_pool,
            site_id=site_id,
            delegator_id=delegator_id,
            title="HTTP Agent workspace",
        )
        control = ControlDatabase(_control_settings(database))
        editor = EditorDatabase(_editor_db_settings(database))
        await control.start()
        await editor.start()
        app = create_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )
        delegator_session = await control.human_session_service().create(delegator_id)
        other_session = await control.human_session_service().create(other_id)

        def _headers(session: Any, *, csrf: bool = True) -> dict[str, str]:
            token = session.token.get_secret_value()
            csrf_token = session.csrf_token.get_secret_value()
            value = {
                "cookie": f"slaif_session={token}; slaif_csrf={csrf_token}",
            }
            if csrf:
                value["x-csrf-token"] = csrf_token
            return value

        composition_path = (
            f"/api/editor/v1/sites/{site_id}/pages/{page_id}/composition/"
        )
        component_path = f"{composition_path}components"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://editor.test",
            timeout=30,
        ) as client:
            # Legacy headerless read: byte-identical HUMAN-workspace flow.
            response = await client.get(
                composition_path, headers=_headers(delegator_session)
            )
            assert response.status_code == 200, response.text
            assert response.headers["cache-control"] == "private, no-store"
            human_workspace = await _resolve_human_workspace(
                owner_pool, site_id, delegator_id
            )
            async with owner_pool.acquire() as owner:
                row = await owner.fetchrow(
                    "SELECT actor_type FROM control.workspace WHERE id = $1",
                    human_workspace,
                )
                assert row is not None and row[0] == "HUMAN"
                assert not await owner.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM audit.human_editor_mutation "
                    "WHERE workspace_id = $1)",
                    workspace,
                )

            # Malformed header: safe 400 before any workspace roundtrip.
            response = await client.get(
                composition_path,
                headers={
                    **_headers(delegator_session),
                    "x-editor-workspace": "not-a-uuid",
                },
            )
            assert response.status_code == 400, response.text
            assert response.json()["error"]["code"] == "MALFORMED_REQUEST"
            async with owner_pool.acquire() as owner:
                assert not await owner.fetchval(
                    "SELECT EXISTS (SELECT 1 FROM control.human_editor_idempotency "
                    "WHERE workspace_id = $1)",
                    workspace,
                )

            # Non-leaking denials: HUMAN workspace, foreign (unknown) workspace,
            # and an unauthorized member all yield the identical safe error.
            async def safe_denial(
                workspace_value: str, headers: dict[str, str]
            ) -> dict[str, str]:
                denied = await client.get(
                    composition_path,
                    headers={**headers, "x-editor-workspace": workspace_value},
                )
                assert denied.status_code == 503, denied.text
                error = denied.json()["error"]
                return {"code": error["code"], "message": error["message"]}

            unknown_error = await safe_denial(
                str(uuid.uuid4()), _headers(delegator_session)
            )
            assert (
                await safe_denial(str(human_workspace), _headers(delegator_session))
                == unknown_error
            )
            assert (
                await safe_denial(str(workspace), _headers(other_session))
                == unknown_error
            )

            # CSRF failure on a mutation stays fail-closed.
            csrf_response = await client.post(
                component_path,
                headers=_headers(delegator_session, csrf=False)
                | {
                    "content-type": "application/json",
                    "idempotency-key": f"csrf-{uuid.uuid4().hex}",
                    "x-editor-workspace": str(workspace),
                },
                json={
                    "component_type": "Section",
                    "slot_key": "default",
                    "order_key": 0,
                    "props": {},
                },
            )
            assert csrf_response.status_code == 403, csrf_response.text

            # Authorized AGENT-workspace read and mutation with the header.
            response = await client.get(
                composition_path,
                headers={
                    **_headers(delegator_session),
                    "x-editor-workspace": str(workspace),
                },
            )
            assert response.status_code == 200, response.text
            idempotency_key = f"component-{uuid.uuid4().hex}"
            body = {
                "component_type": "Section",
                "slot_key": "default",
                "order_key": 0,
                "props": {},
            }
            mutation_headers = {
                **_headers(delegator_session),
                "content-type": "application/json",
                "idempotency-key": idempotency_key,
                "x-editor-workspace": str(workspace),
            }
            response = await client.post(
                component_path, headers=mutation_headers, json=body
            )
            assert response.status_code == 201, response.text
            created = response.json()
            assert created["site_id"] == str(site_id)

            # Idempotency replay returns the stored response unchanged.
            replay = await client.post(
                component_path, headers=mutation_headers, json=body
            )
            assert replay.status_code == 201, replay.text
            assert replay.json() == created

            # The mutation landed in the AGENT workspace, HUMAN audit actor.
            async with owner_pool.acquire() as owner:
                audit = await owner.fetch(
                    "SELECT * FROM audit.human_editor_mutation WHERE workspace_id = $1",
                    workspace,
                )
                assert len(audit) == 1
                assert audit[0]["human_user_id"] == delegator_id
                assert audit[0]["site_id"] == site_id
                # Canonical base is untouched.
                assert (
                    await owner.fetchval(
                        "SELECT count(*) FROM content.page_composition_base "
                        "WHERE site_id = $1",
                        site_id,
                    )
                    == 0
                )
                # The overlay is visible in the workspace session.
                assert (
                    await owner.fetchval(
                        "SELECT count(*) FROM content.page_composition_changes "
                        "WHERE site_id = $1",
                        site_id,
                    )
                    == 1
                )
    finally:
        if control is not None:
            await control.stop()
        if editor is not None:
            await editor.stop()
        await owner_pool.close()

"""Disposable PostgreSQL proof for the opaque human-session foundation."""

from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.control_api.config import ControlDatabaseSettings
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.privileges import verify_database_privileges
from slaif_agent_site.db.readiness import ReadinessState
from slaif_agent_site.identity.sessions import (
    HumanSessionContext,
    HumanSessionError,
    HumanSessionPolicy,
    HumanSessionService,
)


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    from urllib.parse import quote

    from pydantic import SecretStr
    from slaif_agent_site.control_api.config import ControlDatabaseMode

    login, password = database.credentials["slaif_control"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    locator = (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/"
        f"{quote(database.name, safe='')}"
    )
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        application_name="slaif-session-test",
    )


@pytest.mark.asyncio
async def test_human_session_lifecycle_security_and_concurrency(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    user_id = uuid4()
    fake_password_hash = "$argon2id$v=19$m=65536,t=3,p=4$" + "A" * 22 + "$" + "B" * 43
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.user_account ("
            "id, identity_kind, local_username, local_username_normalized, "
            "password_hash, display_name, status) "
            "VALUES ($1, 'LOCAL', $2, $2, $3, $4, 'ACTIVE')",
            user_id,
            "session-user",
            fake_password_hash,
            "Session User",
        )
        validation = await verify_database_privileges(
            owner, readiness_state=ReadinessState.EMPTY_SAFE
        )
        assert validation.safe, validation.violations

    control_pool = await database.role_pool("slaif_control")
    policy = HumanSessionPolicy(
        touch_interval_seconds=1,
        idle_timeout_seconds=2,
        absolute_lifetime_seconds=8,
        recent_auth_window_seconds=4,
    )
    values = iter(bytes([index]) * 32 for index in range(1, 80))
    service = HumanSessionService(
        control_pool,
        policy=policy,
        random_bytes=lambda _size: next(values),
        id_factory=lambda: uuid4(),
    )
    try:
        issued = await service.create(user_id)
        assert issued.public_id.startswith("sas2_")
        assert "token=<redacted>" in repr(issued)
        assert issued.token.get_secret_value() not in repr(issued)
        safe = await service.authenticate(issued.token)
        assert safe.user_account_id == user_id
        assert safe.recent_auth is True
        with pytest.raises(HumanSessionError):
            await service.authenticate_state_changing(issued.token, "")
        stateful = await service.authenticate_state_changing(
            issued.token, issued.csrf_token
        )
        assert stateful.user_account_id == user_id

        async def session_snapshot(session_id: object) -> asyncpg.Record:
            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                row = await owner.fetchrow(
                    "SELECT secret_digest, csrf_secret_digest, last_seen_at, "
                    "absolute_expires_at, recent_auth_at, revoked_at "
                    "FROM control.user_session WHERE id = $1",
                    session_id,
                )
            assert row is not None
            return row

        snapshot_before = await session_snapshot(issued.session_id)
        wrong_secret = issued.token.get_secret_value().replace(
            issued.token.get_secret_value()[-43:], "B" * 43
        )
        with pytest.raises(HumanSessionError):
            await service.authenticate(wrong_secret)
        with pytest.raises(HumanSessionError):
            await service.authenticate_state_changing(
                issued.token, "sas2_csrf_" + "A" * 43
            )
        with pytest.raises(HumanSessionError):
            await service.authenticate("sas2_session_" + "f" * 32 + "_" + "A" * 43)
        snapshot_after = await session_snapshot(issued.session_id)
        assert tuple(snapshot_after) == tuple(snapshot_before)

        second = await service.create(user_id)
        with pytest.raises(HumanSessionError):
            await service.authenticate_state_changing(issued.token, second.csrf_token)

            async with owner_connection(
                database.settings.resolved_owner_dsn(), expected_database=database.name
            ) as owner:
                await owner.execute(
                    "UPDATE control.user_session SET created_at = current_timestamp - "
                    "interval '10 seconds', recent_auth_at = current_timestamp - "
                    "interval '10 seconds' WHERE id = $1",
                    issued.session_id,
                )
        assert (await service.authenticate(issued.token)).recent_auth is False

        before_touch = await session_snapshot(second.session_id)
        await service.authenticate(second.token)
        after_no_touch = await session_snapshot(second.session_id)
        assert after_no_touch[2] == before_touch[2]
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET last_seen_at = current_timestamp - "
                "interval '2 seconds' WHERE id = $1",
                second.session_id,
            )
        before_touch = await session_snapshot(second.session_id)
        touched = await service.authenticate(second.token)
        after_touch = await session_snapshot(second.session_id)
        assert after_touch[2] > before_touch[2]
        assert touched.absolute_expires_at == after_touch[3]
        assert after_touch[4] == before_touch[4]

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.user_session SET last_seen_at = current_timestamp - "
                "interval '3 seconds' WHERE id = $1",
                second.session_id,
            )
            await owner.execute(
                "UPDATE control.user_session SET absolute_expires_at = "
                "current_timestamp "
                "- interval '1 second' WHERE id = $1",
                second.session_id,
            )
        with pytest.raises(HumanSessionError):
            await service.authenticate(second.token)

        race = await service.create(user_id)
        with pytest.raises(HumanSessionError):
            await service.revoke(race.token, second.csrf_token)
        assert (await session_snapshot(race.session_id))[5] is None
        outcomes = await asyncio.gather(
            *(service.authenticate(race.token) for _ in range(4)),
            service.revoke(race.token, race.csrf_token),
            return_exceptions=True,
        )
        assert any(isinstance(item, HumanSessionContext) for item in outcomes)
        await service.revoke(race.token, race.csrf_token)
        with pytest.raises(HumanSessionError):
            await service.authenticate(race.token)

        cancelled = await service.create(user_id)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            async with owner.transaction():
                await owner.execute(
                    "SELECT id FROM control.user_session WHERE id = $1 FOR UPDATE",
                    cancelled.session_id,
                )
                blocked = asyncio.create_task(service.authenticate(cancelled.token))
                await asyncio.sleep(0.05)
                blocked.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await blocked
        assert isinstance(
            await service.authenticate(cancelled.token), HumanSessionContext
        )

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            revoked_at = await owner.fetchval(
                "SELECT revoked_at FROM control.user_session WHERE id = $1",
                race.session_id,
            )
            assert isinstance(revoked_at, datetime)
            assert revoked_at.tzinfo is not None
            await owner.execute(
                "UPDATE control.user_account SET status = 'DISABLED' WHERE id = $1",
                user_id,
            )
        with pytest.raises(HumanSessionError):
            await service.authenticate(cancelled.token)
        for role in (
            "slaif_editor_runtime",
            "slaif_agent_runtime",
            "slaif_reviewer",
            "slaif_public_reader",
        ):
            pool = await database.role_pool(role)
            try:
                async with pool.acquire() as connection:
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetch("SELECT * FROM control.user_session")
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetch(
                            "SELECT * FROM control.slaif_resolve_human_session("
                            "$1, $2, $3, 2, 1, 4)",
                            issued.public_id,
                            b"x" * 32,
                            b"y" * 32,
                        )
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetch(
                            "SELECT * FROM control.slaif_revoke_human_session("
                            "$1, $2, $3)",
                            issued.public_id,
                            b"x" * 32,
                            b"y" * 32,
                        )
            finally:
                await pool.close()
    finally:
        await control_pool.close()

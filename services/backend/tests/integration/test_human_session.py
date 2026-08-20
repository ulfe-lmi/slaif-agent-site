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
    values = iter(bytes([index]) * 32 for index in range(1, 20))
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
        resolved = await service.resolve(issued.token, issued.csrf_token)
        assert resolved.user_account_id == user_id
        assert resolved.recent_auth is True

        snapshot_before = await database.administrator.fetchrow(
            "SELECT secret_digest, csrf_secret_digest, last_seen_at, "
            "absolute_expires_at, recent_auth_at, revoked_at "
            "FROM control.user_session WHERE id = $1",
            issued.session_id,
        )
        assert snapshot_before is not None
        with pytest.raises(HumanSessionError):
            await service.resolve(
                issued.token.get_secret_value().replace(
                    "sas2_session_", "sas2_session_"
                ),
                "sas2_csrf_" + "A" * 43,
            )
        malformed = "sas2_session_not-a-token"
        with pytest.raises(HumanSessionError):
            await service.resolve(malformed, issued.csrf_token)
        snapshot_after = await database.administrator.fetchrow(
            "SELECT secret_digest, csrf_secret_digest, last_seen_at, "
            "absolute_expires_at, recent_auth_at, revoked_at "
            "FROM control.user_session WHERE id = $1",
            issued.session_id,
        )
        assert tuple(snapshot_after) == tuple(snapshot_before)

        concurrent = await asyncio.gather(
            *(service.resolve(issued.token, issued.csrf_token) for _ in range(4))
        )
        assert {item.user_account_id for item in concurrent} == {user_id}
        await service.revoke(issued.token)
        await service.revoke(issued.token)
        with pytest.raises(HumanSessionError):
            await service.resolve(issued.token, issued.csrf_token)

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            revoked_at = await owner.fetchval(
                "SELECT revoked_at FROM control.user_session WHERE id = $1",
                issued.session_id,
            )
            assert isinstance(revoked_at, datetime)
            assert revoked_at.tzinfo is not None
            await owner.execute(
                "UPDATE control.user_account SET status = 'DISABLED' WHERE id = $1",
                user_id,
            )
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
            finally:
                await pool.close()
    finally:
        await control_pool.close()

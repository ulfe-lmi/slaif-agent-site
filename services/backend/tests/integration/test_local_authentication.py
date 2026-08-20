"""Control-only local credential lookup and verification integration tests."""

from __future__ import annotations

from urllib.parse import quote
from uuid import uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import (
    ControlDatabase,
    LocalAuthenticationError,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.identity.authentication import LocalLoginRequest
from slaif_agent_site.identity.passwords import PasswordService


def _settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
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
        application_name="slaif-auth-test",
    )


@pytest.mark.asyncio
async def test_local_authentication_actual_dummy_and_denial_paths(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    password = SecretStr("fixture-authentication-password-123")
    encoded = (
        PasswordService()
        .hash_password(password, normalized_username="local.admin")
        .get_secret_value()
    )
    user_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "INSERT INTO control.user_account ("
            "id, identity_kind, local_username, local_username_normalized, "
            "password_hash, display_name, status) "
            "VALUES ($1, 'LOCAL', $2, $3, $4, $5, 'ACTIVE')",
            user_id,
            "Local.Admin",
            "local.admin",
            encoded,
            "Local Administrator",
        )

    adapter = ControlDatabase(_settings(database))
    await adapter.start()
    try:
        result = await adapter.authenticate_local_login(
            LocalLoginRequest(username="LOCAL.ADMIN", password=password)
        )
        assert result.user_account_id == user_id
        assert result.username == "local.admin"
        assert result.rehashed is False
        for request in (
            LocalLoginRequest(
                username="local.admin", password=SecretStr("wrong-password")
            ),
            LocalLoginRequest(username="unknown.user", password=password),
        ):
            with pytest.raises(
                LocalAuthenticationError, match="^Local login failed\\.$"
            ):
                await adapter.authenticate_local_login(request)
    finally:
        await adapter.stop()


@pytest.mark.asyncio
async def test_local_authentication_function_is_control_only(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    pools = {
        role: await database.role_pool(role)
        for role in ("slaif_control", "slaif_agent_runtime", "slaif_scheduler")
    }
    try:
        async with pools["slaif_control"].acquire() as connection:
            assert (
                await connection.fetchrow(
                    "SELECT * FROM control.slaif_lookup_local_login($1)", "missing"
                )
                is None
            )
        for role in ("slaif_agent_runtime", "slaif_scheduler"):
            async with pools[role].acquire() as connection:
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetchrow(
                        "SELECT * FROM control.slaif_lookup_local_login($1)", "missing"
                    )
    finally:
        for pool in pools.values():
            await pool.close()

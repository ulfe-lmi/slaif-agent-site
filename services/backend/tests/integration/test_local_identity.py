"""Local identity schema and atomic initial-administrator integration tests."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.bootstrap.service import (
    ensure_setup_token,
    reconcile,
    revoke_setup_token,
    rotate_setup_token,
    upgrade,
    validate,
)
from slaif_agent_site.bootstrap.setup_token import (
    digest_setup_token,
    generate_setup_token,
)
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase, InitialSetupError
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.identity.models import (
    InitialLocalAdministratorRequest,
    InitialLocalAdministratorResult,
)
from slaif_agent_site.identity.passwords import PasswordService


def _token(seed: int) -> SecretStr:
    return generate_setup_token(lambda size: bytes([seed]) * size)


def _password(seed: str) -> SecretStr:
    return SecretStr("fixture-" + seed + "-" + "p" * 20)


def _request(
    token: SecretStr,
    *,
    username: str = "Local.Admin",
    password_seed: str = "primary",
) -> InitialLocalAdministratorRequest:
    return InitialLocalAdministratorRequest(
        username=username,
        password=_password(password_seed),
        display_name="Local Administrator",
        email=username.lower().replace(".", "-") + "@example.test",
        setup_token=token,
    )


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
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
        pool_min_size=1,
        pool_max_size=3,
        application_name="slaif-identity-test",
    )


async def _adapter(
    database: AgentSiteDatabase,
    *,
    uuid_factory: Callable[[], UUID] = uuid4,
    after_setup_lock: Callable[[], Awaitable[None]] | None = None,
) -> ControlDatabase:
    adapter = ControlDatabase(
        _control_settings(database),
        uuid_factory=uuid_factory,
        after_setup_lock=after_setup_lock,
    )
    await adapter.start()
    assert (await adapter.readiness()).reason is None
    return adapter


async def _installation_snapshot(database: AgentSiteDatabase) -> tuple[Any, ...]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        row = await connection.fetchrow(
            "SELECT initialized_at, setup_token_digest, setup_token_issued_at, "
            "setup_token_expires_at, setup_token_generation, "
            "(SELECT count(*) FROM control.user_account), "
            "(SELECT count(*) FROM control.platform_administrator) "
            "FROM control.installation_state WHERE singleton"
        )
    assert row is not None
    return tuple(row)


async def test_identity_migration_objects_grants_denials_and_oidc_key(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    marker = await reconcile(database.settings)
    assert marker.safe
    _marker, privilege_validation = await validate(database.settings)
    assert privilege_validation.safe, privilege_validation.violations

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        relations = await connection.fetch(
            "SELECT tablename::text, tableowner::text FROM pg_catalog.pg_tables "
            "WHERE schemaname = 'control' AND tablename IN ("
            "'platform_administrator', 'user_account') ORDER BY tablename"
        )
        assert [tuple(row) for row in relations] == [
            ("platform_administrator", "slaif_owner"),
            ("user_account", "slaif_owner"),
        ]
        functions = await connection.fetch(
            "SELECT proc.proname::text, "
            "pg_catalog.pg_get_function_identity_arguments(proc.oid), "
            "owner.rolname::text, proc.prosecdef, proc.provolatile::text, "
            "proc.proparallel::text, "
            "COALESCE(array_to_string(proc.proconfig, ','), ''), "
            "EXISTS (SELECT 1 FROM pg_catalog.aclexplode(proc.proacl) acl "
            "WHERE acl.grantee = 0 AND acl.privilege_type = 'EXECUTE') "
            "FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "JOIN pg_catalog.pg_roles owner ON owner.oid = proc.proowner "
            "WHERE namespace_.nspname = 'control' "
            "AND proc.proname = ANY($1::text[]) ORDER BY proc.proname",
            [
                "slaif_complete_initial_local_administrator",
                "slaif_initial_setup_lock",
            ],
        )
        assert len(functions) == 2
        assert all(
            row[2:] == ("slaif_owner", True, "v", "u", "search_path=pg_catalog", False)
            for row in functions
        )
        assert functions[0][1] == (
            "p_expected_generation bigint, p_presented_digest bytea, "
            "p_user_account_id uuid, p_local_username text, "
            "p_local_username_normalized text, p_password_hash text, "
            "p_display_name text, p_email text"
        )
        assert functions[1][1] == ""
        grants = await connection.fetch(
            "SELECT proc.proname::text, grantee.rolname::text, "
            "acl.privilege_type::text, acl.is_grantable "
            "FROM pg_catalog.pg_proc proc "
            "JOIN pg_catalog.pg_namespace namespace_ "
            "ON namespace_.oid = proc.pronamespace "
            "CROSS JOIN LATERAL pg_catalog.aclexplode(proc.proacl) acl "
            "JOIN pg_catalog.pg_roles grantee ON grantee.oid = acl.grantee "
            "WHERE namespace_.nspname = 'control' "
            "AND proc.proname = ANY($1::text[]) "
            "ORDER BY proc.proname, grantee.rolname",
            [
                "slaif_complete_initial_local_administrator",
                "slaif_initial_setup_lock",
            ],
        )
        assert [tuple(row) for row in grants] == [
            (
                "slaif_complete_initial_local_administrator",
                "slaif_control",
                "EXECUTE",
                False,
            ),
            (
                "slaif_complete_initial_local_administrator",
                "slaif_owner",
                "EXECUTE",
                False,
            ),
            ("slaif_initial_setup_lock", "slaif_control", "EXECUTE", False),
            ("slaif_initial_setup_lock", "slaif_owner", "EXECUTE", False),
        ]

        first_oidc_id = uuid4()
        second_oidc_id = uuid4()
        await connection.execute(
            "INSERT INTO control.user_account ("
            "id, identity_kind, oidc_issuer, oidc_subject, display_name) "
            "VALUES ($1, 'OIDC', $2, $3, $4), ($5, 'OIDC', $2, $6, $7)",
            first_oidc_id,
            "https://issuer.example.test",
            "stable-subject-one",
            "Future One",
            second_oidc_id,
            "stable-subject-two",
            "Future Two",
        )
        with pytest.raises(asyncpg.UniqueViolationError):
            async with connection.transaction():
                await connection.execute(
                    "INSERT INTO control.user_account ("
                    "id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                    "VALUES ($1, 'OIDC', $2, $3, $4)",
                    uuid4(),
                    "https://issuer.example.test",
                    "stable-subject-one",
                    "Duplicate",
                )
        oidc_rows = await connection.fetch(
            "SELECT oidc_issuer, oidc_subject, email, local_username, password_hash "
            "FROM control.user_account WHERE identity_kind = 'OIDC' "
            "ORDER BY oidc_subject"
        )
        assert len(oidc_rows) == 2
        assert all(row[2:] == (None, None, None) for row in oidc_rows)

    pools = {role: await database.role_pool(role) for role in ROLE_NAMES[1:]}
    try:
        for role, pool in pools.items():
            async with pool.acquire() as connection:
                for relation in ("user_account", "platform_administrator"):
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetch(f"SELECT * FROM control.{relation}")
                if role == "slaif_control":
                    row = await connection.fetchrow(
                        "SELECT * FROM control.slaif_initial_setup_lock()"
                    )
                    assert row is not None and row[0] is False
                else:
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetchrow(
                            "SELECT * FROM control.slaif_initial_setup_lock()"
                        )
    finally:
        for pool in pools.values():
            await pool.close()


async def test_valid_setup_creates_one_local_platform_administrator_atomically(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(31)
    )
    assert issued.setup_token is not None
    request = _request(issued.setup_token)
    adapter = await _adapter(database)
    try:
        result = await adapter.create_initial_local_administrator(request)
    finally:
        await adapter.stop()
    assert isinstance(result, InitialLocalAdministratorResult)
    assert result.username == "Local.Admin" and result.status == "ACTIVE"
    assert "password" not in result.model_dump_json()
    assert "digest" not in result.model_dump_json()

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        row = await connection.fetchrow(
            "SELECT account.id, account.identity_kind, account.local_username, "
            "account.local_username_normalized, account.password_hash, "
            "account.oidc_issuer, account.oidc_subject, account.email, "
            "account.display_name, account.status, assignment.user_account_id "
            "FROM control.user_account account "
            "JOIN control.platform_administrator assignment "
            "ON assignment.user_account_id = account.id"
        )
        state = await connection.fetchrow(
            "SELECT initialized_at, setup_token_digest, setup_token_issued_at, "
            "setup_token_expires_at, setup_token_generation "
            "FROM control.installation_state WHERE singleton"
        )
    assert row is not None and state is not None
    assert row[0] == result.user_account_id == row[10]
    assert tuple(row[1:4]) == ("LOCAL", "Local.Admin", "local.admin")
    assert row[5:7] == (None, None)
    assert tuple(row[7:10]) == (
        "local-admin@example.test",
        "Local Administrator",
        "ACTIVE",
    )
    assert PasswordService().verify_password(SecretStr(row[4]), request.password)
    assert request.password.get_secret_value() not in row[4]
    assert state[0] is not None
    assert tuple(state[1:4]) == (None, None, None)
    assert state[4] == 1


async def test_completion_function_rejects_null_malformed_wrong_and_stale_proof(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(39)
    )
    assert issued.setup_token is not None
    correct_digest = digest_setup_token(issued.setup_token)
    original = await _installation_snapshot(database)
    generation = original[4]
    assert isinstance(generation, int) and generation == 1
    assert original[0] is None and original[1] == correct_digest
    assert original[5:] == (0, 0)

    password_hash = PasswordService().hash_password(
        _password("direct-proof"), normalized_username="proof.admin"
    )
    completion_sql = (
        "SELECT * FROM control.slaif_complete_initial_local_administrator("
        "$1::bigint, $2::bytea, $3::uuid, $4::text, $5::text, $6::text, "
        "$7::text, $8::text)"
    )
    adversarial_proofs: tuple[tuple[int | None, bytes | None], ...] = (
        (None, correct_digest),
        (generation, None),
        (generation, b"x" * 31),
        (generation, b"x" * 33),
        (generation, b"x" * 32),
        (generation - 1, correct_digest),
    )

    control_pool = await database.role_pool("slaif_control")
    try:
        async with control_pool.acquire() as control:
            for expected_generation, presented_digest in adversarial_proofs:
                with pytest.raises(asyncpg.PostgresError) as context:
                    await control.fetchrow(
                        completion_sql,
                        expected_generation,
                        presented_digest,
                        uuid4(),
                        "Proof.Admin",
                        "proof.admin",
                        password_hash.get_secret_value(),
                        "Proof Administrator",
                        "proof-admin@example.test",
                    )
                assert context.value.sqlstate == "P0001"
                assert await _installation_snapshot(database) == original
    finally:
        await control_pool.close()

    adapter = await _adapter(database)
    try:
        result = await adapter.create_initial_local_administrator(
            _request(issued.setup_token, username="Proof.Admin")
        )
    finally:
        await adapter.stop()
    assert result.username == "Proof.Admin"
    completed = await _installation_snapshot(database)
    assert completed[0] is not None
    assert completed[1:4] == (None, None, None)
    assert completed[4:] == (generation, 1, 1)


async def test_invalid_expired_revoked_and_replayed_tokens_share_one_failure(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(32)
    )
    assert issued.setup_token is not None
    initial = await _installation_snapshot(database)
    adapter = await _adapter(database)
    try:
        failures: list[str] = []
        for presented in (SecretStr("malformed"), _token(33)):
            with pytest.raises(InitialSetupError) as context:
                await adapter.create_initial_local_administrator(_request(presented))
            failures.append(str(context.value))
            assert await _installation_snapshot(database) == initial

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as connection:
            await connection.execute(
                "UPDATE control.installation_state SET "
                "setup_token_issued_at = CURRENT_TIMESTAMP - interval '2 seconds', "
                "setup_token_expires_at = CURRENT_TIMESTAMP - interval '1 second' "
                "WHERE singleton"
            )
        expired_state = await _installation_snapshot(database)
        with pytest.raises(InitialSetupError) as context:
            await adapter.create_initial_local_administrator(
                _request(issued.setup_token)
            )
        failures.append(str(context.value))
        assert await _installation_snapshot(database) == expired_state

        rotated = await rotate_setup_token(
            database.settings, token_factory=lambda: _token(34)
        )
        assert rotated.setup_token is not None
        await revoke_setup_token(database.settings)
        revoked_state = await _installation_snapshot(database)
        with pytest.raises(InitialSetupError) as context:
            await adapter.create_initial_local_administrator(
                _request(rotated.setup_token)
            )
        failures.append(str(context.value))
        assert await _installation_snapshot(database) == revoked_state

        replacement = await ensure_setup_token(
            database.settings, token_factory=lambda: _token(35)
        )
        assert replacement.setup_token is not None
        await adapter.create_initial_local_administrator(
            _request(replacement.setup_token)
        )
        completed = await _installation_snapshot(database)
        with pytest.raises(InitialSetupError) as context:
            await adapter.create_initial_local_administrator(
                _request(replacement.setup_token, username="Other.Admin")
            )
        failures.append(str(context.value))
        assert await _installation_snapshot(database) == completed
    finally:
        await adapter.stop()
    assert failures == ["Initial setup failed."] * 5


async def test_concurrent_valid_attempts_create_exactly_one_administrator(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(36)
    )
    assert issued.setup_token is not None
    adapter = await _adapter(database)
    try:
        results = await asyncio.gather(
            adapter.create_initial_local_administrator(
                _request(
                    issued.setup_token, username="First.Admin", password_seed="one"
                )
            ),
            adapter.create_initial_local_administrator(
                _request(
                    issued.setup_token, username="Second.Admin", password_seed="two"
                )
            ),
            return_exceptions=True,
        )
    finally:
        await adapter.stop()
    assert (
        sum(isinstance(result, InitialLocalAdministratorResult) for result in results)
        == 1
    )
    failures = [result for result in results if isinstance(result, InitialSetupError)]
    assert len(failures) == 1 and str(failures[0]) == "Initial setup failed."
    state = await _installation_snapshot(database)
    assert state[0] is not None and state[1:4] == (None, None, None)
    assert state[5:] == (1, 1)


async def test_uniqueness_failure_rolls_back_and_valid_retry_succeeds(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(37)
    )
    assert issued.setup_token is not None
    existing_hash = PasswordService().hash_password(
        _password("existing"), normalized_username="taken.admin"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "INSERT INTO control.user_account ("
            "id, identity_kind, local_username, local_username_normalized, "
            "password_hash, display_name) VALUES ($1, 'LOCAL', $2, $3, $4, $5)",
            uuid4(),
            "Taken.Admin",
            "taken.admin",
            existing_hash.get_secret_value(),
            "Existing Account",
        )
    before = await _installation_snapshot(database)
    adapter = await _adapter(database)
    try:
        with pytest.raises(InitialSetupError) as context:
            await adapter.create_initial_local_administrator(
                _request(issued.setup_token, username="TAKEN.ADMIN")
            )
        assert str(context.value) == "Initial setup failed."
        assert await _installation_snapshot(database) == before
        result = await adapter.create_initial_local_administrator(
            _request(issued.setup_token, username="Available.Admin")
        )
        assert result.username == "Available.Admin"
    finally:
        await adapter.stop()
    state = await _installation_snapshot(database)
    assert state[0] is not None and state[5:] == (2, 1)


async def test_cancellation_after_lock_rolls_back_without_consuming_token(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    issued = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(38)
    )
    assert issued.setup_token is not None
    before = await _installation_snapshot(database)
    locked = asyncio.Event()
    release = asyncio.Event()

    async def pause_after_lock() -> None:
        locked.set()
        await release.wait()

    adapter = await _adapter(database, after_setup_lock=pause_after_lock)
    task = asyncio.create_task(
        adapter.create_initial_local_administrator(_request(issued.setup_token))
    )
    await asyncio.wait_for(locked.wait(), timeout=10)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    release.set()
    await adapter.stop()
    assert await _installation_snapshot(database) == before

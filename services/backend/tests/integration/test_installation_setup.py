"""Installation-state migration, owner lifecycle, and denial integration tests."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    SetupTokenAction,
    ensure_setup_token,
    reconcile,
    revoke_setup_token,
    rotate_setup_token,
    setup_token_status,
    upgrade,
    validate,
)
from slaif_agent_site.bootstrap.setup_token import (
    digest_setup_token,
    generate_setup_token,
    setup_token_matches,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.roles import ROLE_NAMES


def _token(seed: int) -> SecretStr:
    return generate_setup_token(lambda size: bytes([seed]) * size)


async def test_migration_constraints_owner_and_zero_runtime_access(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        columns = await connection.fetch(
            "SELECT column_name::text, data_type::text, is_nullable::text "
            "FROM information_schema.columns WHERE table_schema = 'control' "
            "AND table_name = 'installation_state' ORDER BY ordinal_position"
        )
        assert [tuple(row) for row in columns] == [
            ("singleton", "boolean", "NO"),
            ("initialized_at", "timestamp with time zone", "YES"),
            ("setup_token_digest", "bytea", "YES"),
            ("setup_token_issued_at", "timestamp with time zone", "YES"),
            ("setup_token_expires_at", "timestamp with time zone", "YES"),
            ("setup_token_generation", "bigint", "NO"),
            ("updated_at", "timestamp with time zone", "NO"),
        ]
        assert (
            await connection.fetchval(
                "SELECT pg_get_userbyid(relowner)::text FROM pg_catalog.pg_class "
                "WHERE oid = 'control.installation_state'::regclass"
            )
            == "slaif_owner"
        )
        assert (
            await connection.fetchval(
                "SELECT count(*) FROM control.installation_state WHERE singleton"
            )
            == 1
        )
        with pytest.raises(asyncpg.CheckViolationError):
            async with connection.transaction():
                await connection.execute(
                    "UPDATE control.installation_state SET setup_token_digest = $1 "
                    "WHERE singleton",
                    b"short",
                )
        with pytest.raises(asyncpg.UniqueViolationError):
            async with connection.transaction():
                await connection.execute(
                    "INSERT INTO control.installation_state (singleton) VALUES (TRUE)"
                )

    for role in ROLE_NAMES[1:]:
        pool = await database.role_pool(role)
        try:
            async with pool.acquire() as connection:
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.fetch("SELECT * FROM control.installation_state")
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await connection.execute(
                        "UPDATE control.installation_state "
                        "SET setup_token_generation = 0 WHERE singleton"
                    )
        finally:
            await pool.close()

    marker = await reconcile(database.settings)
    assert marker.safe
    _marker, privileges = await validate(database.settings)
    assert privileges.safe, privileges.violations
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "GRANT SELECT ON control.installation_state TO slaif_control"
        )
    _marker, privileges = await validate(database.settings)
    assert not privileges.safe
    assert any("installation_state" in item for item in privileges.violations)


async def test_issue_repeat_rotate_expire_revoke_and_initialized_lifecycle(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    first = await ensure_setup_token(database.settings, token_factory=lambda: _token(1))
    assert first.action is SetupTokenAction.ISSUED
    assert first.setup_token is not None
    first_plaintext = first.setup_token.get_secret_value()
    first_digest = digest_setup_token(first.setup_token)
    assert first.status.generation == 1
    assert first.status.token_present and not first.status.token_expired
    assert first_plaintext not in repr(first)
    assert first_plaintext not in first.model_dump_json()

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        row = await connection.fetchrow(
            "SELECT setup_token_digest, setup_token_generation, initialized_at "
            "FROM control.installation_state WHERE singleton"
        )
        assert row is not None
        assert bytes(row[0]) == first_digest
        assert row[1] == 1 and row[2] is None
        assert first_plaintext not in repr(tuple(row))

    def randomness_must_not_run() -> SecretStr:
        raise AssertionError("repeated ensure generated randomness")

    repeated = await ensure_setup_token(
        database.settings, token_factory=randomness_must_not_run
    )
    assert repeated.action is SetupTokenAction.EXISTING
    assert repeated.setup_token is None
    assert repeated.status.generation == 1

    rotated = await rotate_setup_token(
        database.settings, token_factory=lambda: _token(2)
    )
    assert rotated.action is SetupTokenAction.ROTATED
    assert rotated.setup_token is not None
    assert rotated.status.generation == 2
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        rotated_digest = bytes(
            await connection.fetchval(
                "SELECT setup_token_digest FROM control.installation_state "
                "WHERE singleton"
            )
        )
        assert not setup_token_matches(first.setup_token, rotated_digest)
        assert setup_token_matches(rotated.setup_token, rotated_digest)
        await connection.execute(
            "UPDATE control.installation_state SET "
            "setup_token_issued_at = CURRENT_TIMESTAMP - interval '2 seconds', "
            "setup_token_expires_at = CURRENT_TIMESTAMP - interval '1 second' "
            "WHERE singleton"
        )

    expired_replacement = await ensure_setup_token(
        database.settings, token_factory=lambda: _token(3)
    )
    assert expired_replacement.action is SetupTokenAction.ISSUED
    assert expired_replacement.status.generation == 3

    revoked = await revoke_setup_token(database.settings)
    assert revoked.action is SetupTokenAction.REVOKED
    assert not revoked.status.token_present
    repeated_revoke = await revoke_setup_token(database.settings)
    assert repeated_revoke.status == revoked.status
    status = await setup_token_status(database.settings)
    assert not status.initialized and not status.token_present
    assert status.generation == 3
    assert "digest" not in status.model_dump_json()

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        await connection.execute(
            "UPDATE control.installation_state SET "
            "initialized_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP "
            "WHERE singleton"
        )
    with pytest.raises(BootstrapStateError):
        await ensure_setup_token(database.settings)
    with pytest.raises(BootstrapStateError):
        await rotate_setup_token(database.settings)
    with pytest.raises(BootstrapStateError):
        await revoke_setup_token(database.settings)
    initialized = await setup_token_status(database.settings)
    assert initialized.initialized and not initialized.token_present


async def test_concurrent_ensure_issues_exactly_once(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    results = await asyncio.gather(
        ensure_setup_token(database.settings, token_factory=lambda: _token(4)),
        ensure_setup_token(database.settings, token_factory=lambda: _token(5)),
    )
    assert {result.action for result in results} == {
        SetupTokenAction.ISSUED,
        SetupTokenAction.EXISTING,
    }
    assert sum(result.setup_token is not None for result in results) == 1
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as connection:
        row = await connection.fetchrow(
            "SELECT setup_token_digest, setup_token_generation "
            "FROM control.installation_state WHERE singleton"
        )
    assert row is not None and len(row[0]) == 32 and row[1] == 1


async def test_setup_token_cli_plaintext_once_then_bounded_existing_and_revoke(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    owner_file = tmp_path / "owner-dsn"
    locator = database.settings.resolved_owner_dsn().get_secret_value()
    owner_file.write_text(locator + "\n", encoding="utf-8")
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("SLAIF_BOOTSTRAP_")
    }
    environment.update(
        {
            "SLAIF_BOOTSTRAP_MODE": "production",
            "SLAIF_BOOTSTRAP_EXPECTED_DATABASE": database.name,
            "SLAIF_BOOTSTRAP_OWNER_DSN_FILE": str(owner_file),
            "SLAIF_BOOTSTRAP_SETUP_URL": "https://example.test/setup",
        }
    )

    def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "slaif_agent_site.bootstrap", *arguments],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )

    issued = invoke("setup-token")
    assert issued.returncode == 0 and issued.stderr == ""
    secret_lines = [
        line
        for line in issued.stdout.splitlines()
        if line.startswith("setup-token-secret: ")
    ]
    assert len(secret_lines) == 1
    plaintext = secret_lines[0].removeprefix("setup-token-secret: ")
    assert plaintext not in issued.stdout.replace(secret_lines[0], "")
    assert "setup-url: https://example.test/setup" in issued.stdout

    existing = invoke("setup-token")
    status = invoke("setup-token", "--status")
    revoked = invoke("setup-token", "--revoke")
    for completed in (existing, status, revoked):
        assert completed.returncode == 0 and completed.stderr == ""
        assert plaintext not in completed.stdout
        assert "setup-token-secret:" not in completed.stdout
        assert "digest" not in completed.stdout
        assert locator not in completed.stdout
    assert "--rotate" in existing.stdout
    assert "token-present=true" in status.stdout
    assert "token-present=false" in revoked.stdout

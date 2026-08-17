"""Programmatic Alembic execution on an injected owner-only connection."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool

from .roles import OWNER_ROLE

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
ALEMBIC_INI = REPOSITORY_ROOT / "alembic.ini"
PACKAGED_SCRIPT_LOCATION = Path(__file__).resolve().parent / "alembic"
MigrationCommand = Literal["upgrade", "downgrade"]


def alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI)) if ALEMBIC_INI.is_file() else Config()
    config.set_main_option("script_location", str(PACKAGED_SCRIPT_LOCATION))
    config.set_main_option("path_separator", "os")
    return config


def migration_heads() -> tuple[str, ...]:
    return tuple(ScriptDirectory.from_config(alembic_config()).get_heads())


def migration_history() -> tuple[str, ...]:
    revisions = ScriptDirectory.from_config(alembic_config()).walk_revisions()
    return tuple(revision.revision for revision in revisions)


def _asyncpg_url(dsn: SecretStr) -> str:
    value = dsn.get_secret_value()
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        return "postgresql+asyncpg://" + value.removeprefix("postgresql://")
    if value.startswith("postgres://"):
        return "postgresql+asyncpg://" + value.removeprefix("postgres://")
    raise ValueError("setup-owner locator must use PostgreSQL")


async def _validate_and_activate_owner(
    connection: AsyncConnection, *, expected_database: str
) -> None:
    result = await connection.exec_driver_sql(
        "SELECT current_database()::text, current_user::text, "
        "pg_has_role(current_user, 'slaif_owner', 'MEMBER')"
    )
    database_name, login_name, owner_member = result.one()
    if database_name != expected_database or not (
        login_name == OWNER_ROLE or owner_member
    ):
        raise PermissionError("setup-owner authority validation failed")
    await connection.exec_driver_sql('SET ROLE "slaif_owner"')
    active = await connection.exec_driver_sql("SELECT current_user::text")
    if active.scalar_one() != OWNER_ROLE:
        raise PermissionError("setup-owner authority activation failed")


async def run_migration(
    dsn: SecretStr,
    *,
    expected_database: str,
    operation: MigrationCommand,
    revision: str,
) -> None:
    """Run one explicit migration command without retaining a connection pool."""

    engine = create_async_engine(
        _asyncpg_url(dsn),
        hide_parameters=True,
        poolclass=NullPool,
    )
    try:
        async with engine.begin() as connection:
            await _validate_and_activate_owner(
                connection, expected_database=expected_database
            )
            if operation == "upgrade":
                await connection.exec_driver_sql(
                    'CREATE SCHEMA IF NOT EXISTS "control" AUTHORIZATION "slaif_owner"'
                )

            def invoke(sync_connection: Any) -> None:
                config = alembic_config()
                config.attributes["connection"] = sync_connection
                runner: Callable[[Config, str], None] = (
                    command.upgrade if operation == "upgrade" else command.downgrade
                )
                runner(config, revision)

            await connection.run_sync(invoke)
    finally:
        await engine.dispose()


__all__ = [
    "ALEMBIC_INI",
    "alembic_config",
    "migration_heads",
    "migration_history",
    "run_migration",
]

"""Metadata-free Alembic environment for trusted owner-only migrations."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection

VERSION_SCHEMA = "control"
VERSION_TABLE = "alembic_version"

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Render deterministic PostgreSQL SQL without opening a connection."""

    context.configure(
        dialect_name="postgresql",
        literal_binds=True,
        target_metadata=None,
        transaction_per_migration=True,
        version_table=VERSION_TABLE,
        version_table_schema=VERSION_SCHEMA,
    )
    with context.begin_transaction():
        context.execute(
            'CREATE SCHEMA IF NOT EXISTS "control" AUTHORIZATION "slaif_owner"'
        )
        context.run_migrations()


def run_migrations_online() -> None:
    """Use only the owner-validated connection injected by bootstrap code."""

    connection = config.attributes.get("connection")
    if not isinstance(connection, Connection):
        raise RuntimeError("Alembic requires an injected trusted connection")
    context.configure(
        connection=connection,
        target_metadata=None,
        transaction_per_migration=True,
        version_table=VERSION_TABLE,
        version_table_schema=VERSION_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

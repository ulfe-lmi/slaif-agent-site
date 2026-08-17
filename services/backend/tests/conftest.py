"""Disposable PostgreSQL fixtures for foundation qualification."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import asyncpg
import pytest_asyncio
from pydantic import SecretStr
from slaif_agent_site.agent_state.foundation import (
    deploy_cow_functions,
    enable_cow_schema,
    harden_cow_schema,
    validate_cow_schema_privileges,
)
from slaif_agent_site.bootstrap.config import BootstrapMode, BootstrapSettings
from slaif_agent_site.bootstrap.service import provision
from slaif_agent_site.db.roles import ROLE_NAMES, quote_identifier


class AsyncpgExecutor:
    """Adapt one caller-owned asyncpg connection to the public Executor protocol."""

    def __init__(self, connection: asyncpg.Connection[Any]) -> None:
        self._connection = connection

    async def execute(self, sql: str) -> list[tuple[Any, ...]]:
        return [tuple(row) for row in await self._connection.fetch(sql)]


@dataclass(frozen=True, slots=True)
class FoundationDatabase:
    """Distinct credentials and resources for one disposable qualification run."""

    schema: str
    table: str
    setup: asyncpg.Connection[Any]
    runtime_pool: asyncpg.Pool[Any]
    reviewer_pool: asyncpg.Pool[Any]
    runtime_role: str

    @property
    def relation(self) -> str:
        return f'"{self.schema}"."{self.table}"'

    @property
    def canonical_relation(self) -> str:
        return f'"{self.schema}"."{self.table}_base"'


@dataclass(frozen=True, slots=True)
class AgentSiteDatabase:
    """One disposable database with exact privilege roles and fake principals."""

    name: str
    settings: BootstrapSettings
    administrator: asyncpg.Connection[Any]
    connection_parameters: dict[str, str | int]
    credentials: dict[str, tuple[str, str]]

    async def role_pool(self, role: str) -> asyncpg.Pool[Any]:
        login, password = self.credentials[role]

        async def activate(connection: asyncpg.Connection[Any]) -> None:
            await connection.execute(f"SET ROLE {quote_identifier(role)}")

        return await asyncpg.create_pool(
            **{
                key: value
                for key, value in self.connection_parameters.items()
                if key != "database"
            },
            database=self.name,
            user=login,
            password=password,
            min_size=1,
            max_size=1,
            setup=activate,
        )


def _connection_parameters() -> dict[str, str | int]:
    return {
        "host": os.environ.get("PGHOST", "127.0.0.1"),
        "port": int(os.environ.get("PGPORT", "5432")),
        "database": os.environ.get("PGDATABASE", "postgres"),
    }


def _dsn(
    *, parameters: dict[str, str | int], database: str, user: str, password: str
) -> str:
    host = quote(str(parameters["host"]), safe="[]:.")
    return (
        f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@"
        f"{host}:{parameters['port']}/{quote(database, safe='')}"
    )


@pytest_asyncio.fixture
async def agent_site_database() -> AsyncIterator[AgentSiteDatabase]:
    """Provision the exact product role boundary in a disposable database."""

    parameters = _connection_parameters()
    admin_user = os.environ.get("PGUSER", "postgres")
    admin_password = os.environ.get("PGPASSWORD", "qualification-admin")
    administrator = await asyncpg.connect(
        **parameters,
        user=admin_user,
        password=admin_password,
    )
    suffix = uuid.uuid4().hex[:10]
    database = f"slaif_test_{suffix}"
    credentials: dict[str, tuple[str, str]] = {}
    login_roles: list[str] = []
    try:
        await administrator.execute(f"CREATE DATABASE {quote_identifier(database)}")
        provisioner_dsn = _dsn(
            parameters=parameters,
            database=database,
            user=admin_user,
            password=admin_password,
        )
        provisional = BootstrapSettings(
            mode=BootstrapMode.TEST,
            expected_database=database,
            provisioner_dsn=SecretStr(provisioner_dsn),
        )
        await provision(provisional)

        for role in ROLE_NAMES:
            login = f"fixture_{role.removeprefix('slaif_')}_{suffix}"
            password = f"fixture-{role.removeprefix('slaif_')}-{suffix}"
            login_roles.append(login)
            credentials[role] = (login, password)
            await administrator.execute(
                f"CREATE ROLE {quote_identifier(login)} LOGIN PASSWORD "
                f"'{password}' NOSUPERUSER NOCREATEDB NOCREATEROLE "
                "INHERIT NOREPLICATION NOBYPASSRLS"
            )
            await administrator.execute(
                f"GRANT {quote_identifier(role)} TO {quote_identifier(login)}"
            )

        owner_login, owner_password = credentials["slaif_owner"]
        owner_dsn = _dsn(
            parameters=parameters,
            database=database,
            user=owner_login,
            password=owner_password,
        )
        settings = BootstrapSettings(
            mode=BootstrapMode.TEST,
            expected_database=database,
            provisioner_dsn=SecretStr(provisioner_dsn),
            owner_dsn=SecretStr(owner_dsn),
        )
        yield AgentSiteDatabase(
            database,
            settings,
            administrator,
            parameters,
            credentials,
        )
    finally:
        await administrator.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_catalog.pg_stat_activity "
            "WHERE datname = $1 AND pid <> pg_backend_pid()",
            database,
        )
        await administrator.execute(
            f"DROP DATABASE IF EXISTS {quote_identifier(database)}"
        )
        for login in reversed(login_roles):
            await administrator.execute(
                f"DROP ROLE IF EXISTS {quote_identifier(login)}"
            )
        for role in reversed(ROLE_NAMES):
            await administrator.execute(f"DROP ROLE IF EXISTS {quote_identifier(role)}")
        await administrator.close()


@pytest_asyncio.fixture(scope="session")
async def foundation_database() -> AsyncIterator[FoundationDatabase]:
    """Provision ordinary setup/runtime/reviewer roles in a disposable database."""

    parameters = _connection_parameters()
    administrator = await asyncpg.connect(
        **parameters,
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "qualification-admin"),
    )
    suffix = uuid.uuid4().hex[:12]
    schema = f"qualification_{suffix}"
    setup_role = f"qualification_setup_{suffix}"
    runtime_role = f"qualification_runtime_{suffix}"
    reviewer_role = f"qualification_reviewer_{suffix}"
    setup_password = f"qualification-setup-{suffix}"
    runtime_password = f"qualification-runtime-{suffix}"
    reviewer_password = f"qualification-reviewer-{suffix}"
    roles = (setup_role, runtime_role, reviewer_role)

    setup: asyncpg.Connection[Any] | None = None
    runtime_pool: asyncpg.Pool[Any] | None = None
    reviewer_pool: asyncpg.Pool[Any] | None = None
    try:
        await administrator.execute(
            f"CREATE ROLE \"{setup_role}\" LOGIN PASSWORD '{setup_password}' "
            "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
        )
        await administrator.execute(
            f"CREATE ROLE \"{runtime_role}\" LOGIN PASSWORD '{runtime_password}' "
            "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
        )
        await administrator.execute(
            f"CREATE ROLE \"{reviewer_role}\" LOGIN PASSWORD '{reviewer_password}' "
            "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
        )
        database = str(parameters["database"]).replace('"', '""')
        await administrator.execute(
            f'GRANT CREATE ON DATABASE "{database}" TO "{setup_role}"'
        )
        await administrator.execute(
            f'CREATE SCHEMA "{schema}" AUTHORIZATION "{setup_role}"'
        )

        setup = await asyncpg.connect(
            **parameters,
            user=setup_role,
            password=setup_password,
        )
        async with setup.transaction():
            await setup.execute(
                f'CREATE TABLE "{schema}".items ('
                "id integer PRIMARY KEY, title text NOT NULL)"
            )
            await setup.execute(
                f"INSERT INTO \"{schema}\".items (id, title) VALUES (1, 'canonical')"
            )
            executor = AsyncpgExecutor(setup)
            await deploy_cow_functions(executor)
            enabled = await enable_cow_schema(
                executor,
                schema=schema,
                allow_unsafe_canonical_writes=False,
            )
            assert enabled == ["items"]
            hardened = await harden_cow_schema(
                executor,
                schema=schema,
                runtime_roles=[runtime_role],
                reviewer_roles=[reviewer_role],
            )
            assert hardened["safe"], hardened["violations"]
            validation = await validate_cow_schema_privileges(
                executor,
                schema=schema,
                runtime_roles=[runtime_role],
                reviewer_roles=[reviewer_role],
            )
            assert validation["safe"], validation["violations"]

        runtime_pool = await asyncpg.create_pool(
            **parameters,
            user=runtime_role,
            password=runtime_password,
            min_size=1,
            max_size=1,
        )
        reviewer_pool = await asyncpg.create_pool(
            **parameters,
            user=reviewer_role,
            password=reviewer_password,
            min_size=1,
            max_size=1,
        )
        yield FoundationDatabase(
            schema=schema,
            table="items",
            setup=setup,
            runtime_pool=runtime_pool,
            reviewer_pool=reviewer_pool,
            runtime_role=runtime_role,
        )
    finally:
        if reviewer_pool is not None:
            await reviewer_pool.close()
        if runtime_pool is not None:
            await runtime_pool.close()
        if setup is not None:
            await setup.close()
        for role in reversed(roles):
            await administrator.execute(f'DROP OWNED BY "{role}" CASCADE')
        for role in reversed(roles):
            await administrator.execute(f'DROP ROLE IF EXISTS "{role}"')
        await administrator.close()

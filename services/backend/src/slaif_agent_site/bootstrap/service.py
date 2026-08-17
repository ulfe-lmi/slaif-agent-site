"""One-shot migration, COW reconciliation, and readiness operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from slaif_agent_site.agent_state.foundation import (
    FOUNDATION_DISTRIBUTION,
    FOUNDATION_VERSION,
    deploy_cow_functions,
    enable_cow_schema,
    harden_cow_schema,
    validate_cow_schema_privileges,
)
from slaif_agent_site.db.connections import owner_connection, provisioner_connection
from slaif_agent_site.db.executor import AsyncpgExecutor
from slaif_agent_site.db.migrations import migration_heads, run_migration
from slaif_agent_site.db.privileges import (
    PrivilegeValidation,
    apply_product_privileges,
    revoke_public_foundation_access,
    verify_database_privileges,
)
from slaif_agent_site.db.roles import (
    REVIEWER_ROLES,
    RUNTIME_ROLES,
    provision_database_roles,
)

from .config import BootstrapSettings

FailurePoint = Literal["after-harden", "before-marker"]


class BootstrapStateError(RuntimeError):
    """A bootstrap invariant failed without carrying credential material."""


@dataclass(frozen=True, slots=True)
class BootstrapStatus:
    revision: str | None
    cow_deployed: bool
    cow_hardened: bool
    privileges_validated: bool
    safe: bool


async def provision(settings: BootstrapSettings) -> None:
    async with provisioner_connection(
        settings.resolved_provisioner_dsn(),
        expected_database=settings.expected_database,
    ) as connection:
        async with connection.transaction():
            await provision_database_roles(
                connection, expected_database=settings.expected_database
            )


async def upgrade(settings: BootstrapSettings) -> None:
    await run_migration(
        settings.resolved_owner_dsn(),
        expected_database=settings.expected_database,
        operation="upgrade",
        revision="head",
    )


async def downgrade(settings: BootstrapSettings) -> None:
    await run_migration(
        settings.resolved_owner_dsn(),
        expected_database=settings.expected_database,
        operation="downgrade",
        revision="base",
    )


async def rebuild(settings: BootstrapSettings) -> None:
    await downgrade(settings)
    await upgrade(settings)


async def status(settings: BootstrapSettings) -> BootstrapStatus:
    async with owner_connection(
        settings.resolved_owner_dsn(), expected_database=settings.expected_database
    ) as connection:
        revision = await connection.fetchval(
            "SELECT version_num::text FROM control.alembic_version"
        )
        row = await connection.fetchrow(
            "SELECT cow_deployed, cow_hardened, privileges_validated, safe "
            "FROM control.bootstrap_readiness WHERE singleton"
        )
        if row is None:
            raise BootstrapStateError("bootstrap readiness marker is missing")
        return BootstrapStatus(revision, *map(bool, row))


async def _mark_not_safe(connection: Any, *, deployed: bool = False) -> None:
    await connection.execute(
        "UPDATE control.bootstrap_readiness SET "
        "migration_revision = $1, foundation_distribution = $2, "
        "foundation_version = $3, cow_deployed = $4, cow_hardened = FALSE, "
        "privileges_validated = FALSE, safe = FALSE, updated_at = CURRENT_TIMESTAMP "
        "WHERE singleton",
        migration_heads()[0],
        FOUNDATION_DISTRIBUTION,
        FOUNDATION_VERSION,
        deployed,
    )


async def reconcile(
    settings: BootstrapSettings, *, failure_point: FailurePoint | None = None
) -> BootstrapStatus:
    """Reconcile COW and grants; publish `safe` only as the last transaction step."""

    expected_head = migration_heads()
    if len(expected_head) != 1:
        raise BootstrapStateError("the migration graph does not have one head")

    async with owner_connection(
        settings.resolved_owner_dsn(), expected_database=settings.expected_database
    ) as connection:
        current = await connection.fetchval(
            "SELECT version_num::text FROM control.alembic_version"
        )
        if current != expected_head[0]:
            raise BootstrapStateError("the database is not at the required migration")

        async with connection.transaction():
            await _mark_not_safe(connection)

        async with connection.transaction():
            executor = AsyncpgExecutor(connection)
            await deploy_cow_functions(executor)
            await revoke_public_foundation_access(connection)
            await _mark_not_safe(connection, deployed=True)

        async with connection.transaction():
            executor = AsyncpgExecutor(connection)
            await enable_cow_schema(
                executor,
                schema="content",
                allow_deferred_fks=True,
                allow_unsafe_canonical_writes=False,
            )
            try:
                hardened = await harden_cow_schema(
                    executor,
                    schema="content",
                    runtime_roles=list(RUNTIME_ROLES),
                    reviewer_roles=list(REVIEWER_ROLES),
                )
            except ValueError as error:
                if str(error) != "Schema 'content' has no COW-enabled tables":
                    raise BootstrapStateError(
                        "foundation hardening rejected the configured state"
                    ) from error
                raise BootstrapStateError(
                    "content has no COW-enabled table; hardening cannot be truthful"
                ) from error
            if not hardened["safe"]:
                raise BootstrapStateError("foundation hardening validation failed")
            if failure_point == "after-harden":
                raise BootstrapStateError("injected failure after hardening")

            await apply_product_privileges(connection)
            foundation = await validate_cow_schema_privileges(
                executor,
                schema="content",
                runtime_roles=list(RUNTIME_ROLES),
                reviewer_roles=list(REVIEWER_ROLES),
            )
            product = await verify_database_privileges(connection)
            if not foundation["safe"] or not product.safe:
                violations = [
                    *(str(item) for item in foundation["violations"]),
                    *product.violations,
                ]
                raise BootstrapStateError(
                    "database privilege validation failed: " + "; ".join(violations)
                )
            if failure_point == "before-marker":
                raise BootstrapStateError("injected failure before readiness marker")

            await connection.execute(
                "UPDATE control.bootstrap_readiness SET "
                "migration_revision = $1, foundation_distribution = $2, "
                "foundation_version = $3, cow_deployed = TRUE, "
                "cow_hardened = TRUE, privileges_validated = TRUE, safe = TRUE, "
                "updated_at = CURRENT_TIMESTAMP WHERE singleton",
                expected_head[0],
                FOUNDATION_DISTRIBUTION,
                FOUNDATION_VERSION,
            )

    return await status(settings)


async def validate(
    settings: BootstrapSettings,
) -> tuple[BootstrapStatus, PrivilegeValidation]:
    async with owner_connection(
        settings.resolved_owner_dsn(), expected_database=settings.expected_database
    ) as connection:
        marker = await status_on_connection(connection)
        product = await verify_database_privileges(
            connection, expect_clean_content=not marker.cow_hardened
        )
        executor = AsyncpgExecutor(connection)
        foundation = await validate_cow_schema_privileges(
            executor,
            schema="content",
            runtime_roles=list(RUNTIME_ROLES),
            reviewer_roles=list(REVIEWER_ROLES),
        )
        if not foundation["safe"]:
            product = PrivilegeValidation(
                safe=False,
                violations=product.violations + ("foundation/privileges/unsafe",),
            )
        if marker.safe != product.safe:
            product = PrivilegeValidation(
                safe=False,
                violations=product.violations + ("marker/safe/state-mismatch",),
            )
        return marker, product


async def status_on_connection(connection: Any) -> BootstrapStatus:
    revision = await connection.fetchval(
        "SELECT version_num::text FROM control.alembic_version"
    )
    row = await connection.fetchrow(
        "SELECT cow_deployed, cow_hardened, privileges_validated, safe "
        "FROM control.bootstrap_readiness WHERE singleton"
    )
    if row is None:
        raise BootstrapStateError("bootstrap readiness marker is missing")
    return BootstrapStatus(revision, *map(bool, row))


__all__ = [
    "BootstrapStateError",
    "BootstrapStatus",
    "downgrade",
    "provision",
    "rebuild",
    "reconcile",
    "status",
    "upgrade",
    "validate",
]

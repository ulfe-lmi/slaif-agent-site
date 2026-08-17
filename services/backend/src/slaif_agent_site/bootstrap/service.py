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
    content_inventory_fingerprint,
    content_object_inventory,
    foundation_object_inventory,
    revoke_public_foundation_access,
    verify_database_privileges,
)
from slaif_agent_site.db.readiness import ReadinessState
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
    state: ReadinessState
    content_object_count: int
    content_object_fingerprint: str | None
    foundation_object_count: int
    foundation_object_fingerprint: str | None
    foundation_deployed: bool
    foundation_hardened: bool
    foundation_privileges_validated: bool
    product_privileges_validated: bool
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
            "SELECT readiness_state, content_object_count, "
            "content_object_fingerprint, foundation_object_count, "
            "foundation_object_fingerprint, foundation_deployed, foundation_hardened, "
            "foundation_privileges_validated, product_privileges_validated, safe "
            "FROM control.bootstrap_readiness WHERE singleton"
        )
        if row is None:
            raise BootstrapStateError("bootstrap readiness marker is missing")
        return BootstrapStatus(
            revision,
            ReadinessState(row[0]),
            int(row[1]),
            row[2],
            int(row[3]),
            row[4],
            *map(bool, row[5:]),
        )


async def _mark_pending(connection: Any, *, deployed: bool = False) -> None:
    await connection.execute(
        "UPDATE control.bootstrap_readiness SET "
        "migration_revision = $1, foundation_distribution = $2, "
        "foundation_version = $3, readiness_state = 'PENDING', "
        "content_object_count = 0, content_object_fingerprint = NULL, "
        "foundation_object_count = 0, foundation_object_fingerprint = NULL, "
        "foundation_deployed = $4, foundation_hardened = FALSE, "
        "foundation_privileges_validated = FALSE, "
        "product_privileges_validated = FALSE, safe = FALSE, "
        "updated_at = CURRENT_TIMESTAMP "
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
            await _mark_pending(connection)

        async with connection.transaction():
            executor = AsyncpgExecutor(connection)
            await deploy_cow_functions(executor)
            await revoke_public_foundation_access(connection)
            await _mark_pending(connection, deployed=True)

        async with connection.transaction():
            executor = AsyncpgExecutor(connection)
            await enable_cow_schema(
                executor,
                schema="content",
                allow_deferred_fks=True,
                allow_unsafe_canonical_writes=False,
            )
            inventory = await content_object_inventory(connection)
            foundation_inventory = await foundation_object_inventory(connection)
            if not foundation_inventory:
                raise BootstrapStateError("foundation deployment inventory is empty")
            if not inventory:
                await apply_product_privileges(
                    connection, readiness_state=ReadinessState.EMPTY_SAFE
                )
                product = await verify_database_privileges(
                    connection, readiness_state=ReadinessState.EMPTY_SAFE
                )
                if not product.safe:
                    raise BootstrapStateError(
                        "safe-empty privilege validation failed: "
                        + "; ".join(product.violations)
                    )
                final_state = ReadinessState.EMPTY_SAFE
                final_inventory = inventory
                foundation_hardened = False
                foundation_validated = False
            else:
                try:
                    hardened = await harden_cow_schema(
                        executor,
                        schema="content",
                        runtime_roles=list(RUNTIME_ROLES),
                        reviewer_roles=list(REVIEWER_ROLES),
                    )
                except ValueError as error:
                    raise BootstrapStateError(
                        "foundation hardening rejected non-empty content"
                    ) from error
                if not hardened["safe"]:
                    raise BootstrapStateError("foundation hardening validation failed")
                if failure_point == "after-harden":
                    raise BootstrapStateError("injected failure after hardening")

                await apply_product_privileges(
                    connection, readiness_state=ReadinessState.HARDENED
                )
                foundation = await validate_cow_schema_privileges(
                    executor,
                    schema="content",
                    runtime_roles=list(RUNTIME_ROLES),
                    reviewer_roles=list(REVIEWER_ROLES),
                )
                product = await verify_database_privileges(
                    connection, readiness_state=ReadinessState.HARDENED
                )
                if not foundation["safe"] or not product.safe:
                    violations = [
                        *(str(item) for item in foundation["violations"]),
                        *product.violations,
                    ]
                    raise BootstrapStateError(
                        "database privilege validation failed: " + "; ".join(violations)
                    )
                final_state = ReadinessState.HARDENED
                final_inventory = await content_object_inventory(connection)
                if not final_inventory:
                    raise BootstrapStateError(
                        "hardened content inventory is unexpectedly empty"
                    )
                foundation_hardened = True
                foundation_validated = True

            if failure_point == "before-marker":
                raise BootstrapStateError("injected failure before readiness marker")

            await connection.execute(
                "UPDATE control.bootstrap_readiness SET "
                "migration_revision = $1, foundation_distribution = $2, "
                "foundation_version = $3, readiness_state = $4, "
                "content_object_count = $5, content_object_fingerprint = $6, "
                "foundation_object_count = $7, foundation_object_fingerprint = $8, "
                "foundation_deployed = TRUE, foundation_hardened = $9, "
                "foundation_privileges_validated = $10, "
                "product_privileges_validated = TRUE, safe = TRUE, "
                "updated_at = CURRENT_TIMESTAMP WHERE singleton",
                expected_head[0],
                FOUNDATION_DISTRIBUTION,
                FOUNDATION_VERSION,
                final_state.value,
                len(final_inventory),
                (
                    content_inventory_fingerprint(final_inventory)
                    if final_inventory
                    else None
                ),
                len(foundation_inventory),
                content_inventory_fingerprint(foundation_inventory),
                foundation_hardened,
                foundation_validated,
            )

    return await status(settings)


async def validate(
    settings: BootstrapSettings,
) -> tuple[BootstrapStatus, PrivilegeValidation]:
    async with owner_connection(
        settings.resolved_owner_dsn(), expected_database=settings.expected_database
    ) as connection:
        marker = await status_on_connection(connection)
        if marker.state is ReadinessState.PENDING:
            return marker, PrivilegeValidation(
                safe=False, violations=("marker/readiness-state/pending",)
            )

        product = await verify_database_privileges(
            connection, readiness_state=marker.state
        )
        marker_metadata = await connection.fetchrow(
            "SELECT migration_revision, foundation_distribution, foundation_version "
            "FROM control.bootstrap_readiness WHERE singleton"
        )
        metadata_matches = marker_metadata is not None and tuple(marker_metadata) == (
            marker.revision,
            FOUNDATION_DISTRIBUTION,
            FOUNDATION_VERSION,
        )
        inventory = await content_object_inventory(connection)
        foundation_inventory = await foundation_object_inventory(connection)
        inventory_matches = marker.content_object_count == len(
            inventory
        ) and marker.content_object_fingerprint == (
            content_inventory_fingerprint(inventory) if inventory else None
        )
        foundation_inventory_matches = marker.foundation_object_count == len(
            foundation_inventory
        ) and marker.foundation_object_fingerprint == (
            content_inventory_fingerprint(foundation_inventory)
            if foundation_inventory
            else None
        )
        if (
            not metadata_matches
            or not inventory_matches
            or not foundation_inventory_matches
        ):
            product = PrivilegeValidation(
                safe=False,
                violations=product.violations
                + tuple(
                    violation
                    for matches, violation in (
                        (
                            metadata_matches,
                            "marker/version-metadata/state-mismatch",
                        ),
                        (
                            inventory_matches,
                            "marker/content-object-inventory/state-mismatch",
                        ),
                        (
                            foundation_inventory_matches,
                            "marker/foundation-object-inventory/state-mismatch",
                        ),
                    )
                    if not matches
                ),
            )
        if marker.state is ReadinessState.HARDENED:
            executor = AsyncpgExecutor(connection)
            foundation_violations: tuple[str, ...]
            try:
                foundation_validation = await validate_cow_schema_privileges(
                    executor,
                    schema="content",
                    runtime_roles=list(RUNTIME_ROLES),
                    reviewer_roles=list(REVIEWER_ROLES),
                )
            except (RuntimeError, ValueError):
                foundation_violations = ("validation-rejected-current-content",)
            else:
                foundation_violations = tuple(
                    str(item) for item in foundation_validation["violations"]
                )
                if not foundation_validation["safe"] and not foundation_violations:
                    foundation_violations = ("unsafe",)
            if foundation_violations:
                product = PrivilegeValidation(
                    safe=False,
                    violations=product.violations
                    + tuple(
                        f"foundation/privileges/{item}"
                        for item in foundation_violations
                    ),
                )
        facts_match = (
            marker.foundation_deployed
            and marker.product_privileges_validated
            and metadata_matches
            and inventory_matches
            and foundation_inventory_matches
            and (
                (
                    marker.state is ReadinessState.EMPTY_SAFE
                    and not marker.foundation_hardened
                    and not marker.foundation_privileges_validated
                )
                or (
                    marker.state is ReadinessState.HARDENED
                    and marker.foundation_hardened
                    and marker.foundation_privileges_validated
                )
            )
        )
        if not facts_match or marker.safe != product.safe:
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
        "SELECT readiness_state, content_object_count, content_object_fingerprint, "
        "foundation_object_count, foundation_object_fingerprint, "
        "foundation_deployed, foundation_hardened, "
        "foundation_privileges_validated, product_privileges_validated, safe "
        "FROM control.bootstrap_readiness WHERE singleton"
    )
    if row is None:
        raise BootstrapStateError("bootstrap readiness marker is missing")
    return BootstrapStatus(
        revision,
        ReadinessState(row[0]),
        int(row[1]),
        row[2],
        int(row[3]),
        row[4],
        *map(bool, row[5:]),
    )


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

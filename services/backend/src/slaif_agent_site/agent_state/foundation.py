"""Qualified public surface of the PostgreSQL copy-on-write foundation.

This module centralizes imports that future Agent-State implementations may use.
It deliberately does not wrap transactions or add product authorization policy.
"""

from agentcow.postgres import (  # noqa: F401, I001
    CowConflict as CowConflict,
    CowConflictError as CowConflictError,
    CowPostgresConfig as CowPostgresConfig,
    CowPrivilegeValidation as CowPrivilegeValidation,
    CowReviewer as CowReviewer,
    CowSession as CowSession,
    DiscardResult as DiscardResult,
    PromotionResult as PromotionResult,
    asyncpg_cow_reviewer as asyncpg_cow_reviewer,
    asyncpg_cow_session as asyncpg_cow_session,
    deploy_cow_functions as deploy_cow_functions,
    enable_cow_schema as enable_cow_schema,
    get_cow_conflicts as get_cow_conflicts,
    get_operation_dependencies as get_operation_dependencies,
    get_session_operations as get_session_operations,
    harden_cow_schema as harden_cow_schema,
    validate_cow_schema_privileges as validate_cow_schema_privileges,
)

FOUNDATION_DISTRIBUTION = "agent-cow-postgresql"
FOUNDATION_VERSION = "0.2.0"

QUALIFIED_PUBLIC_API = (
    "CowConflict",
    "CowConflictError",
    "CowPostgresConfig",
    "CowPrivilegeValidation",
    "CowReviewer",
    "CowSession",
    "DiscardResult",
    "PromotionResult",
    "asyncpg_cow_reviewer",
    "asyncpg_cow_session",
    "deploy_cow_functions",
    "enable_cow_schema",
    "get_cow_conflicts",
    "get_operation_dependencies",
    "get_session_operations",
    "harden_cow_schema",
    "validate_cow_schema_privileges",
)

__all__ = [
    "FOUNDATION_DISTRIBUTION",
    "FOUNDATION_VERSION",
    "QUALIFIED_PUBLIC_API",
    "CowConflict",
    "CowConflictError",
    "CowPostgresConfig",
    "CowPrivilegeValidation",
    "CowReviewer",
    "CowSession",
    "DiscardResult",
    "PromotionResult",
    "asyncpg_cow_reviewer",
    "asyncpg_cow_session",
    "deploy_cow_functions",
    "enable_cow_schema",
    "get_cow_conflicts",
    "get_operation_dependencies",
    "get_session_operations",
    "harden_cow_schema",
    "validate_cow_schema_privileges",
]

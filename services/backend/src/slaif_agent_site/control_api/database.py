"""Control-owned bounded asyncpg pool and database readiness adapter."""

# ruff: noqa: E501 -- fixed SQL signatures remain inspectable

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Awaitable, Callable
from contextlib import suppress
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID, uuid4

import asyncpg

from slaif_agent_site.agent_api.models import (
    AgentCapabilityContext as _AgentCapabilityContext,
)
from slaif_agent_site.agent_state.capability_auth import (
    CONTROL_CAPABILITY_AUTHENTICATION_SQL,
    CapabilityAuthenticationUnavailableError,
    authenticate_capability,
)
from slaif_agent_site.agent_state.foundation import (
    FOUNDATION_DISTRIBUTION,
    FOUNDATION_VERSION,
)
from slaif_agent_site.bootstrap.setup_token import (
    digest_setup_token,
    setup_token_matches,
)
from slaif_agent_site.content_model.service import ContentModelService
from slaif_agent_site.db.migrations import migration_heads
from slaif_agent_site.db.roles import ROLE_NAMES
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.human_authorization import HumanAuthorizationService
from slaif_agent_site.identity.authentication import (
    LocalAuthenticationError,
    LocalAuthenticationResult,
    LocalAuthenticationService,
    LocalLoginRequest,
)
from slaif_agent_site.identity.models import (
    InitialLocalAdministratorRequest,
    InitialLocalAdministratorResult,
)
from slaif_agent_site.identity.passwords import PasswordService
from slaif_agent_site.identity.sessions import (
    HumanSessionError,
    HumanSessionPolicy,
    HumanSessionService,
)
from slaif_agent_site.sites.service import SiteService

from .config import ControlDatabaseConfigurationError, ControlDatabaseSettings

READINESS_SQL = (
    "SELECT schema_revision, marker_revision, readiness_state, safe, "
    "foundation_distribution, foundation_version "
    'FROM "control"."slaif_control_readiness"()'
)
SETUP_STATUS_SQL = (
    'SELECT initialized, setup_available FROM "control"."slaif_setup_status"()'
)
INITIAL_SETUP_LOCK_SQL = (
    "SELECT initialized, setup_token_expires_at, setup_token_generation, "
    "setup_token_digest FROM control.slaif_initial_setup_lock()"
)
INITIAL_SETUP_COMPLETE_SQL = (
    "SELECT user_account_id, local_username, display_name, email, status, "
    "created_at FROM control.slaif_complete_initial_local_administrator("
    "$1, $2, $3, $4, $5, $6, $7, $8)"
)
PLATFORM_ADMINISTRATOR_SQL = (
    "SELECT control.slaif_platform_administrator_authorized($1)"
)
HUMAN_EDITOR_WORKSPACE_RESOLVE_SQL = (
    "SELECT control.slaif_human_editor_workspace_resolve($1,$2)"
)
HUMAN_AGENT_WORKSPACE_CREATE_SQL = "SELECT * FROM control.slaif_human_agent_workspace_create($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)"
HUMAN_AGENT_WORKSPACE_GET_SQL = (
    "SELECT * FROM control.slaif_human_agent_workspace_get($1,$2,$3)"
)
HUMAN_AGENT_WORKSPACE_LIST_SQL = (
    "SELECT * FROM control.slaif_human_agent_workspace_list($1,$2)"
)
HUMAN_AGENT_WORKSPACE_CREATE_IDEMPOTENT_SQL = (
    "SELECT * FROM control.slaif_human_agent_workspace_create_idempotent("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)"
)
HUMAN_AGENT_CAPABILITY_CREATE_IDEMPOTENT_SQL = (
    "SELECT * FROM control.slaif_human_agent_capability_create_idempotent("
    "$1,$2,$3,$4,$5,$6,$7)"
)
HUMAN_AGENT_CAPABILITY_CREATE_SQL = (
    "SELECT * FROM control.slaif_human_agent_capability_create($1,$2,$3,$4,$5)"
)
HUMAN_AGENT_CAPABILITY_REVOKE_SQL = (
    "SELECT control.slaif_human_agent_capability_revoke($1,$2,$3,$4)"
)
HUMAN_AGENT_CAPABILITY_LIST_SQL = (
    "SELECT * FROM control.slaif_human_agent_capability_list($1,$2,$3)"
)


class ControlDatabaseReason(StrEnum):
    CONNECTION_UNAVAILABLE = "connection_unavailable"
    CONFIGURATION_INVALID = "configuration_invalid"
    FOUNDATION_MISMATCH = "foundation_mismatch"
    IDENTITY_MISMATCH = "identity_mismatch"
    MIGRATION_MISMATCH = "migration_mismatch"
    ROLE_MISMATCH = "role_mismatch"
    SHUTDOWN = "shutdown"
    TIMEOUT = "timeout"
    UNSAFE_MARKER = "unsafe_marker"


class ControlDatabaseError(RuntimeError):
    """A stable classified failure with no driver or locator detail."""

    def __init__(self, reason: ControlDatabaseReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class InitialSetupError(RuntimeError):
    """The one constant external-safe initial-setup failure."""

    def __init__(self) -> None:
        super().__init__("Initial setup failed.")


class _UnstartedPool:
    """Fail closed without exposing driver or locator details."""

    def acquire(self, *, timeout: float) -> Any:
        del timeout
        raise TimeoutError()


class ControlDatabaseAdapter(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def readiness(self) -> ProbeResult: ...

    async def setup_status(self) -> tuple[bool, bool]: ...

    async def create_initial_local_administrator(
        self, request: InitialLocalAdministratorRequest
    ) -> InitialLocalAdministratorResult: ...

    def human_session_service(self) -> HumanSessionService: ...

    async def authenticate_local_login(
        self, request: LocalLoginRequest
    ) -> LocalAuthenticationResult: ...

    async def authorize_platform_administrator(self, user_account_id: UUID) -> bool: ...

    def site_service(self) -> SiteService: ...

    def human_authorization_service(self) -> HumanAuthorizationService: ...

    def content_model_service(self) -> Any: ...

    async def resolve_human_editor_workspace(
        self, site_id: UUID, human_user_id: UUID
    ) -> UUID: ...


PoolFactory = Callable[..., Awaitable[Any]]
AfterSetupLock = Callable[[], Awaitable[None]]
UuidFactory = Callable[[], UUID]
RandomBytes = Callable[[int], bytes]


class ControlDatabase:
    """Own exactly one Control pool for exactly one application lifespan."""

    def __init__(
        self,
        settings: ControlDatabaseSettings,
        *,
        pool_factory: PoolFactory = asyncpg.create_pool,
        password_service: PasswordService | None = None,
        uuid_factory: UuidFactory = uuid4,
        session_random_bytes: RandomBytes | None = None,
        after_setup_lock: AfterSetupLock | None = None,
    ) -> None:
        self._settings = settings
        self._pool_factory = pool_factory
        self._password_service = password_service or PasswordService()
        self._uuid_factory = uuid_factory
        self._session_random_bytes = session_random_bytes
        self._after_setup_lock = after_setup_lock
        self._pool: asyncpg.Pool[Any] | None = None
        self._failure_reason: ControlDatabaseReason | None = None
        self._stopped = False

    async def _initialize_connection(self, connection: asyncpg.Connection[Any]) -> None:
        row = await connection.fetchrow(
            "SELECT current_database()::text, session_user::text, "
            "current_user::text, ARRAY("
            "SELECT target.rolname::text FROM pg_catalog.pg_roles target "
            "WHERE target.rolname = ANY($1::text[]) "
            "AND pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
            "ORDER BY target.rolname)",
            list(ROLE_NAMES),
        )
        if row is None or tuple(row[:3]) != (
            self._settings.expected_database,
            self._settings.expected_login,
            self._settings.expected_login,
        ):
            raise ControlDatabaseError(ControlDatabaseReason.IDENTITY_MISMATCH)
        if tuple(row[3]) != (self._settings.expected_privilege_role,):
            raise ControlDatabaseError(ControlDatabaseReason.ROLE_MISMATCH)

    async def start(self) -> None:
        """Create and verify the pool without propagating credential details."""

        if self._pool is not None:
            return
        self._stopped = False
        self._failure_reason = None
        try:
            dsn = self._settings.resolved_dsn()
            pool = await self._pool_factory(
                dsn=dsn.get_secret_value(),
                min_size=self._settings.pool_min_size,
                max_size=self._settings.pool_max_size,
                timeout=self._settings.connect_timeout_seconds,
                command_timeout=self._settings.command_timeout_seconds,
                max_inactive_connection_lifetime=(
                    self._settings.max_inactive_connection_lifetime_seconds
                ),
                server_settings=self._settings.server_settings,
                init=self._initialize_connection,
            )
        except asyncio.CancelledError:
            self._stopped = True
            raise
        except ControlDatabaseConfigurationError:
            self._failure_reason = ControlDatabaseReason.CONFIGURATION_INVALID
        except ControlDatabaseError as error:
            self._failure_reason = error.reason
        except TimeoutError:
            self._failure_reason = ControlDatabaseReason.TIMEOUT
        except (OSError, asyncpg.PostgresError):
            self._failure_reason = ControlDatabaseReason.CONNECTION_UNAVAILABLE
        except Exception:
            self._failure_reason = ControlDatabaseReason.CONNECTION_UNAVAILABLE
        else:
            self._pool = pool

    async def _close_pool(self, pool: asyncpg.Pool[Any]) -> None:
        close_task = asyncio.create_task(pool.close())
        try:
            await asyncio.wait_for(
                asyncio.shield(close_task),
                timeout=self._settings.shutdown_timeout_seconds,
            )
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(
                    asyncio.shield(close_task),
                    timeout=self._settings.shutdown_timeout_seconds,
                )
            except TimeoutError:
                pool.terminate()
                close_task.cancel()
                with suppress(asyncio.CancelledError):
                    await close_task
            raise
        except TimeoutError:
            pool.terminate()
            close_task.cancel()
            with suppress(asyncio.CancelledError):
                await close_task

    async def stop(self) -> None:
        """Close the owned pool exactly once and fail readiness closed."""

        self._stopped = True
        self._failure_reason = ControlDatabaseReason.SHUTDOWN
        pool, self._pool = self._pool, None
        if pool is not None:
            await self._close_pool(pool)

    @staticmethod
    def _result_for_row(row: asyncpg.Record | None) -> ProbeResult:
        if row is None:
            return ProbeResult.unavailable(ControlDatabaseReason.UNSAFE_MARKER.value)
        expected_heads = migration_heads()
        if (
            len(expected_heads) != 1
            or row[0] != expected_heads[0]
            or row[1] != expected_heads[0]
        ):
            return ProbeResult.unavailable(
                ControlDatabaseReason.MIGRATION_MISMATCH.value
            )
        if row[2] not in {"EMPTY_SAFE", "HARDENED"} or row[3] is not True:
            return ProbeResult.unavailable(ControlDatabaseReason.UNSAFE_MARKER.value)
        if row[4] != FOUNDATION_DISTRIBUTION or row[5] != FOUNDATION_VERSION:
            return ProbeResult.unavailable(
                ControlDatabaseReason.FOUNDATION_MISMATCH.value
            )
        return ProbeResult.ready()

    async def readiness(self) -> ProbeResult:
        pool = self._pool
        if pool is None:
            reason = (
                ControlDatabaseReason.SHUTDOWN
                if self._stopped
                else self._failure_reason
                or ControlDatabaseReason.CONNECTION_UNAVAILABLE
            )
            return ProbeResult.unavailable(reason.value)
        try:
            async with pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                row = await connection.fetchrow(READINESS_SQL)
            return self._result_for_row(row)
        except asyncio.CancelledError:
            raise
        except ControlDatabaseError as error:
            return ProbeResult.unavailable(error.reason.value)
        except TimeoutError:
            return ProbeResult.unavailable(ControlDatabaseReason.TIMEOUT.value)
        except asyncpg.UndefinedFunctionError:
            return ProbeResult.unavailable(
                ControlDatabaseReason.MIGRATION_MISMATCH.value
            )
        except (OSError, asyncpg.PostgresError):
            return ProbeResult.unavailable(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE.value
            )
        except Exception:
            return ProbeResult.unavailable(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE.value
            )

    async def setup_status(self) -> tuple[bool, bool]:
        pool = self._pool
        if pool is None:
            raise ControlDatabaseError(
                self._failure_reason or ControlDatabaseReason.CONNECTION_UNAVAILABLE
            )
        try:
            async with pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                row = await connection.fetchrow(SETUP_STATUS_SQL)
            if row is None:
                raise ControlDatabaseError(ControlDatabaseReason.UNSAFE_MARKER)
            return bool(row[0]), bool(row[1])
        except asyncio.CancelledError:
            raise
        except ControlDatabaseError:
            raise
        except (TimeoutError, asyncpg.PostgresError, OSError):
            raise ControlDatabaseError(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None
        except Exception:
            raise ControlDatabaseError(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None

    async def create_initial_local_administrator(
        self, request: InitialLocalAdministratorRequest
    ) -> InitialLocalAdministratorResult:
        """Consume setup proof and create the first administrator atomically."""

        pool = self._pool
        if pool is None:
            raise InitialSetupError()
        try:
            presented_digest = digest_setup_token(request.setup_token)
            password_hash = self._password_service.hash_password(
                request.password,
                normalized_username=request.normalized_username,
            )
            user_account_id = self._uuid_factory()
            async with pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                async with connection.transaction():
                    installation = await connection.fetchrow(INITIAL_SETUP_LOCK_SQL)
                    if (
                        installation is None
                        or installation[0] is not False
                        or installation[2] < 1
                        or installation[3] is None
                        or not setup_token_matches(
                            request.setup_token, bytes(installation[3])
                        )
                    ):
                        raise InitialSetupError()
                    if self._after_setup_lock is not None:
                        await self._after_setup_lock()
                    row = await connection.fetchrow(
                        INITIAL_SETUP_COMPLETE_SQL,
                        int(installation[2]),
                        presented_digest,
                        user_account_id,
                        request.username,
                        request.normalized_username,
                        password_hash.get_secret_value(),
                        request.display_name,
                        request.email,
                    )
                    if row is None:
                        raise InitialSetupError()
                    return InitialLocalAdministratorResult(
                        user_account_id=row[0],
                        username=row[1],
                        display_name=row[2],
                        email=row[3],
                        status=row[4],
                        created_at=row[5],
                    )
        except asyncio.CancelledError:
            raise
        except InitialSetupError:
            raise
        except Exception:
            raise InitialSetupError() from None

    def human_session_service(
        self, policy: HumanSessionPolicy | None = None
    ) -> HumanSessionService:
        """Return the Control-only session adapter for this owned pool."""

        if self._pool is None:
            raise HumanSessionError()
        return HumanSessionService(
            self._pool,
            policy=policy,
            random_bytes=self._session_random_bytes or secrets.token_bytes,
        )

    def content_model_service(self) -> Any:
        """Return the semantic content-model adapter for this owned pool."""

        return ContentModelService(
            self._pool or _UnstartedPool(),
            acquire_timeout=self._settings.acquire_timeout_seconds,
        )

    async def resolve_human_editor_workspace(
        self, site_id: UUID, human_user_id: UUID
    ) -> UUID:
        pool = self._pool
        if pool is None:
            raise ControlDatabaseError(
                self._failure_reason or ControlDatabaseReason.CONNECTION_UNAVAILABLE
            )
        try:
            async with pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                async with connection.transaction():
                    workspace_id = await connection.fetchval(
                        HUMAN_EDITOR_WORKSPACE_RESOLVE_SQL,
                        site_id,
                        human_user_id,
                    )
            if not isinstance(workspace_id, UUID):
                raise ControlDatabaseError(ControlDatabaseReason.UNSAFE_MARKER)
            return workspace_id
        except asyncio.CancelledError:
            raise
        except ControlDatabaseError:
            raise
        except (TimeoutError, OSError, asyncpg.PostgresError):
            raise ControlDatabaseError(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None
        except Exception:
            raise ControlDatabaseError(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None

    async def authenticate_agent_capability(self, auth_header: str) -> Any:
        """Validate one bearer capability and return its trusted context."""

        pool = self._pool
        if pool is None:
            raise ControlDatabaseError(ControlDatabaseReason.CONNECTION_UNAVAILABLE)
        try:
            record = await authenticate_capability(
                pool,
                acquire_timeout=self._settings.acquire_timeout_seconds,
                auth_header=auth_header,
                query=CONTROL_CAPABILITY_AUTHENTICATION_SQL,
            )
        except asyncio.CancelledError:
            raise
        except CapabilityAuthenticationUnavailableError:
            raise ControlDatabaseError(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None
        if record is None:
            return None
        return _AgentCapabilityContext(
            capability_id=record.capability_id,
            site_id=record.site_id,
            workspace_id=record.workspace_id,
            delegator_id=record.delegator_id,
            scopes=record.scopes,
            created_at=record.created_at,
            expires_at=record.expires_at,
            browser_limits=record.browser_limits,
            resource_constraints=record.resource_constraints,
            source_origins=record.source_origins,
            request_quota=record.request_quota,
            mutation_quota=record.mutation_quota,
            delete_quota=record.delete_quota,
            upload_quota=record.upload_quota,
        )

    async def _human_agent_call(self, sql: str, *arguments: Any) -> list[Any]:
        if self._pool is None:
            raise ControlDatabaseError(ControlDatabaseReason.CONNECTION_UNAVAILABLE)
        try:
            async with self._pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                return list(await connection.fetch(sql, *arguments))
        except asyncio.CancelledError:
            raise
        except (TimeoutError, OSError, asyncpg.PostgresError) as error:
            raise error

    async def human_agent_workspace_create(self, *arguments: Any) -> Any:
        rows = await self._human_agent_call(
            HUMAN_AGENT_WORKSPACE_CREATE_SQL, *arguments
        )
        return rows[0] if rows else None

    async def human_agent_workspace_get(self, *arguments: Any) -> Any:
        rows = await self._human_agent_call(HUMAN_AGENT_WORKSPACE_GET_SQL, *arguments)
        return rows[0] if rows else None

    async def human_agent_workspace_list(self, *arguments: Any) -> list[Any]:
        return await self._human_agent_call(HUMAN_AGENT_WORKSPACE_LIST_SQL, *arguments)

    async def human_agent_workspace_create_idempotent(self, *arguments: Any) -> Any:
        rows = await self._human_agent_call(
            HUMAN_AGENT_WORKSPACE_CREATE_IDEMPOTENT_SQL, *arguments
        )
        return rows[0] if rows else None

    async def human_agent_capability_create(self, *arguments: Any) -> Any:
        rows = await self._human_agent_call(
            HUMAN_AGENT_CAPABILITY_CREATE_SQL, *arguments
        )
        return rows[0] if rows else None

    async def human_agent_capability_create_idempotent(self, *arguments: Any) -> Any:
        rows = await self._human_agent_call(
            HUMAN_AGENT_CAPABILITY_CREATE_IDEMPOTENT_SQL, *arguments
        )
        return rows[0] if rows else None

    async def human_agent_capability_revoke(self, *arguments: Any) -> Any:
        rows = await self._human_agent_call(
            HUMAN_AGENT_CAPABILITY_REVOKE_SQL, *arguments
        )
        return bool(rows and rows[0][0])

    async def human_agent_capability_list(self, *arguments: Any) -> list[Any]:
        return await self._human_agent_call(HUMAN_AGENT_CAPABILITY_LIST_SQL, *arguments)

    async def authenticate_local_login(
        self, request: LocalLoginRequest
    ) -> LocalAuthenticationResult:
        """Verify one local credential through the Control-only boundary."""

        if self._pool is None:
            raise LocalAuthenticationError()
        return await LocalAuthenticationService(
            self._pool,
            acquire_timeout=self._settings.acquire_timeout_seconds,
            password_service=self._password_service,
        ).authenticate(request)

    async def authorize_platform_administrator(self, user_account_id: UUID) -> bool:
        """Check one fixed active installation-authority assignment."""

        pool = self._pool
        if pool is None:
            raise ControlDatabaseError(ControlDatabaseReason.CONNECTION_UNAVAILABLE)
        try:
            async with pool.acquire(
                timeout=self._settings.acquire_timeout_seconds
            ) as connection:
                return bool(
                    await connection.fetchval(
                        PLATFORM_ADMINISTRATOR_SQL, user_account_id
                    )
                )
        except asyncio.CancelledError:
            raise
        except (TimeoutError, asyncpg.PostgresError, OSError):
            raise ControlDatabaseError(
                ControlDatabaseReason.CONNECTION_UNAVAILABLE
            ) from None

    def site_service(self) -> SiteService:
        """Return the Control-only semantic site adapter for this pool."""

        if self._pool is None:
            raise ControlDatabaseError(ControlDatabaseReason.CONNECTION_UNAVAILABLE)
        return SiteService(
            self._pool, acquire_timeout=self._settings.acquire_timeout_seconds
        )

    def human_authorization_service(self) -> HumanAuthorizationService:
        """Return the Control-only membership/RBAC service for this pool."""

        if self._pool is None:
            raise ControlDatabaseError(ControlDatabaseReason.CONNECTION_UNAVAILABLE)
        return HumanAuthorizationService(
            self._pool, acquire_timeout=self._settings.acquire_timeout_seconds
        )


__all__ = [
    "INITIAL_SETUP_COMPLETE_SQL",
    "INITIAL_SETUP_LOCK_SQL",
    "PLATFORM_ADMINISTRATOR_SQL",
    "READINESS_SQL",
    "ControlDatabase",
    "ControlDatabaseAdapter",
    "ControlDatabaseError",
    "ControlDatabaseReason",
    "InitialSetupError",
    "LocalAuthenticationError",
    "LocalAuthenticationResult",
    "LocalLoginRequest",
]

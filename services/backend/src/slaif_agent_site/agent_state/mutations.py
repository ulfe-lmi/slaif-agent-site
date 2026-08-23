"""Trusted Agent COW mutation executor and durable idempotency boundary.

This module is the only Agent HTTP mutation path.  It accepts a capability
context selected by the authenticated server, opens one foundation COW
session on the Agent pool, invokes only agent-specific semantic wrappers, and
records the result through narrow owner-defined control functions.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg

from slaif_agent_site.agent_api.models import (
    AgentCapabilityContext,
    AgentMutationResponse,
)
from slaif_agent_site.agent_state.foundation import (
    CowSession,
    asyncpg_cow_session,
)
from slaif_agent_site.content_model.composition_models import (
    CompositionNodeRecord,
    CreateCompositionNodeRequest,
)
from slaif_agent_site.content_model.item_models import (
    ContentItemRecord,
    CreateContentItemRequest,
)
from slaif_agent_site.content_model.models import (
    ContentTypeRecord,
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    FieldDefinitionRecord,
)
from slaif_agent_site.content_model.page_models import CreatePageRequest, PageRecord
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
    _ci,
    _cmp,
    _ct,
    _fd,
    _pg,
)

BEGIN_IDEMPOTENCY_SQL = (
    "SELECT * FROM control.slaif_agent_idempotency_begin($1,$2,$3,$4,$5)"
)
COMPLETE_IDEMPOTENCY_SQL = (
    "SELECT control.slaif_agent_idempotency_complete($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)"
)

AGENT_CONTENT_TYPE_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_type_create($1,$2,$3,$4,$5)"
)
AGENT_FIELD_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_field_definition_create("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)"
)
AGENT_ITEM_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_create($1,$2,$3,$4,$5,$6)"
)
AGENT_PAGE_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_page_create($1,$2,$3,$4,$5,$6)"
)
AGENT_COMPONENT_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_composition_node_add($1,$2,$3,$4,$5,$6,$7)"
)

_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._~-]{1,128}$")


class AgentMutationUnavailableError(RuntimeError):
    """A durable idempotency or COW dependency could not complete."""


class AgentMutationConflictError(RuntimeError):
    """The active COW operation encountered a semantic conflict."""


class IdempotencyMismatchError(RuntimeError):
    """The capability reused a key with a different request digest."""


class MissingIdempotencyKeyError(ValueError):
    """The mutation omitted its required retry key."""


class InvalidIdempotencyKeyError(ValueError):
    """The mutation supplied a malformed retry key."""


@dataclass(frozen=True, slots=True)
class IdempotencyReservation:
    state: str
    operation_id: UUID
    status_code: int | None
    response_body: dict[str, Any] | None


def validate_idempotency_key(key: str | None) -> str:
    if key is None:
        raise MissingIdempotencyKeyError()
    if not _IDEMPOTENCY_KEY.fullmatch(key):
        raise InvalidIdempotencyKeyError()
    return key


def mutation_digest(*, method: str, path: str, body: dict[str, Any]) -> str:
    from slaif_agent_site.agent_state.idempotency import compute_request_digest

    return compute_request_digest({"method": method, "path": path, "body": body})


class AgentCowContentModelService(ContentModelService):
    """Semantic service bound to one COW connection and agent wrappers."""

    def __init__(
        self, cow_session: CowSession, *, acquire_timeout: float = 3.0
    ) -> None:
        super().__init__(
            None,
            acquire_timeout=acquire_timeout,
            cow_session=cow_session,
        )

    async def create_type(
        self, site_id: UUID, request: CreateContentTypeRequest
    ) -> ContentTypeRecord:
        row = await self._fetchrow(
            AGENT_CONTENT_TYPE_CREATE_SQL,
            site_id,
            request.key,
            json.dumps(request.labels, sort_keys=True),
            request.slug_pattern,
            json.dumps(request.settings, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _ct(row)

    async def create_field_for_site(
        self,
        site_id: UUID,
        type_id: UUID,
        request: CreateFieldDefinitionRequest,
    ) -> FieldDefinitionRecord:
        row = await self._fetchrow(
            AGENT_FIELD_CREATE_SQL,
            site_id,
            type_id,
            request.key,
            request.label,
            request.field_type,
            request.required,
            request.localized,
            request.cardinality,
            request.position,
            json.dumps(request.validation, sort_keys=True),
            json.dumps(request.ui_options, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _fd(row)

    async def create_item_for_site(
        self,
        site_id: UUID,
        type_id: UUID,
        request: CreateContentItemRequest,
    ) -> ContentItemRecord:
        row = await self._fetchrow(
            AGENT_ITEM_CREATE_SQL,
            site_id,
            type_id,
            request.slug,
            request.status,
            json.dumps(request.values, sort_keys=True),
            1,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return cast(ContentItemRecord, _ci(row))

    async def create_page_for_site(
        self, site_id: UUID, request: CreatePageRequest
    ) -> PageRecord:
        row = await self._fetchrow(
            AGENT_PAGE_CREATE_SQL,
            site_id,
            request.slug,
            request.title,
            request.status,
            request.locale,
            request.parent_id,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return cast(PageRecord, _pg(row))

    async def add_component_for_site(
        self,
        site_id: UUID,
        page_id: UUID,
        request: CreateCompositionNodeRequest,
    ) -> CompositionNodeRecord:
        parent_id = UUID(request.parent_id) if request.parent_id else None
        row = await self._fetchrow(
            AGENT_COMPONENT_CREATE_SQL,
            site_id,
            page_id,
            request.component_type,
            parent_id,
            request.slot_key,
            request.order_key,
            json.dumps(request.props, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return cast(CompositionNodeRecord, _cmp(row))


async def _cow_fetchrow(cow: CowSession, sql: str, *arguments: object) -> Any:
    await cow.validate_context()
    return await cow.native.fetchrow(sql, *arguments)


async def _reserve(
    cow: CowSession,
    *,
    context: AgentCapabilityContext,
    key: str,
    digest: str,
    operation_id: UUID,
) -> IdempotencyReservation:
    try:
        row = await _cow_fetchrow(
            cow,
            BEGIN_IDEMPOTENCY_SQL,
            context.capability_id,
            context.workspace_id,
            key,
            digest,
            operation_id,
        )
    except asyncio.CancelledError:
        raise
    except (asyncpg.PostgresError, OSError, TimeoutError) as error:
        raise AgentMutationUnavailableError() from error
    if row is None:
        raise AgentMutationUnavailableError()
    response_body = row[3]
    if isinstance(response_body, str):
        try:
            decoded = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise AgentMutationUnavailableError() from error
        if not isinstance(decoded, dict):
            raise AgentMutationUnavailableError()
        response_body = decoded
    return IdempotencyReservation(
        state=str(row[0]),
        operation_id=row[1],
        status_code=row[2],
        response_body=response_body,
    )


async def _complete(
    cow: CowSession,
    *,
    context: AgentCapabilityContext,
    key: str,
    digest: str,
    operation_id: UUID,
    response: AgentMutationResponse,
    resource_type: str,
) -> None:
    try:
        await _cow_fetchrow(
            cow,
            COMPLETE_IDEMPOTENCY_SQL,
            context.capability_id,
            context.workspace_id,
            key,
            digest,
            operation_id,
            201,
            json.dumps(response.model_dump(mode="json"), sort_keys=True),
            resource_type,
            UUID(str(response.record["id"])),
            context.site_id,
        )
    except asyncio.CancelledError:
        raise
    except (asyncpg.PostgresError, OSError, TimeoutError) as error:
        raise AgentMutationUnavailableError() from error


Mutation = Callable[[AgentCowContentModelService], Awaitable[Any]]


async def execute_agent_mutation(
    *,
    database: Any,
    context: AgentCapabilityContext,
    key: str,
    digest: str,
    mutate: Mutation,
    resource_type: str,
) -> AgentMutationResponse:
    """Reserve, execute, audit, and complete one atomic Agent mutation."""

    operation_id = uuid4()
    try:
        pool = database.cow_pool()
    except Exception as error:
        raise AgentMutationUnavailableError() from error
    try:
        async with asyncpg_cow_session(
            pool,
            session_id=context.workspace_id,
            operation_id=operation_id,
        ) as cow:
            reservation = await _reserve(
                cow,
                context=context,
                key=key,
                digest=digest,
                operation_id=operation_id,
            )
            if reservation.state == "MISMATCH":
                raise IdempotencyMismatchError()
            if reservation.state == "REPLAY":
                if reservation.response_body is None:
                    raise AgentMutationUnavailableError()
                return AgentMutationResponse.model_validate(reservation.response_body)
            if reservation.state != "STARTED":
                raise AgentMutationUnavailableError()

            service = AgentCowContentModelService(cow)
            record = await mutate(service)
            record_body = record.model_dump(mode="json")
            response = AgentMutationResponse(
                record=record_body,
                operation_id=reservation.operation_id,
            )
            await _complete(
                cow,
                context=context,
                key=key,
                digest=digest,
                operation_id=reservation.operation_id,
                response=response,
                resource_type=resource_type,
            )
            return response
    except asyncio.CancelledError:
        raise
    except IdempotencyMismatchError:
        raise
    except AgentMutationUnavailableError:
        raise
    except ContentModelServiceError:
        raise
    except asyncpg.UniqueViolationError as error:
        raise AgentMutationConflictError() from error
    except (asyncpg.PostgresError, OSError, TimeoutError, TypeError) as error:
        raise AgentMutationUnavailableError() from error


__all__ = [
    "AgentCowContentModelService",
    "AgentMutationConflictError",
    "AgentMutationUnavailableError",
    "IdempotencyMismatchError",
    "InvalidIdempotencyKeyError",
    "MissingIdempotencyKeyError",
    "execute_agent_mutation",
    "mutation_digest",
    "validate_idempotency_key",
]

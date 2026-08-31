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
    AgentUpdateContentItemRequest,
    ContentItemRecord,
    CreateContentItemRequest,
    DeleteContentItemRequest,
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
COMPLETE_SEMANTIC_IDEMPOTENCY_SQL = (
    "SELECT control.slaif_agent_idempotency_complete("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)"
)
CONSUME_MUTATION_QUOTA_SQL = (
    "SELECT control.slaif_agent_quota_consume($1,$2,'mutation')"
)

AGENT_CONTENT_TYPE_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_type_create($1,$2,$3,$4,$5)"
)
AGENT_FIELD_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_field_definition_create("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)"
)
AGENT_CONTENT_TYPE_UPDATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_type_update($1,$2,$3,$4,$5,$6)"
)
AGENT_CONTENT_TYPE_DELETE_SQL = (
    "SELECT * FROM content.slaif_agent_content_type_delete($1,$2,$3)"
)
AGENT_FIELD_UPDATE_SQL = (
    "SELECT * FROM content.slaif_agent_field_definition_update("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)"
)
AGENT_FIELD_DELETE_SQL = (
    "SELECT * FROM content.slaif_agent_field_definition_delete($1,$2,$3,$4)"
)
AGENT_ITEM_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_create($1,$2,$3,$4,$5)"
)
AGENT_ITEM_GET_SQL = "SELECT * FROM content.slaif_agent_content_item_get($1,$2)"
AGENT_ITEM_UPDATE_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_update($1,$2,$3,$4,$5,$6)"
)
AGENT_ITEM_DELETE_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_delete($1,$2,$3)"
)
AGENT_TYPE_GET_SQL = "SELECT * FROM content.slaif_agent_content_type_get($1,$2)"
AGENT_FIELD_LIST_SQL = "SELECT * FROM content.slaif_agent_field_definition_list($1,$2)"
AGENT_PAGE_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_page_create($1,$2,$3,$4,$5,$6)"
)
AGENT_COMPONENT_CREATE_SQL = (
    "SELECT * FROM content.slaif_agent_composition_node_add($1,$2,$3,$4,$5,$6,$7)"
)

_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._~-]{1,128}$")


class AgentMutationUnavailableError(RuntimeError):
    """A durable idempotency or COW dependency could not complete."""


AGENT_SEMANTIC_CONTRACTS = {
    "CONTENT_TYPE_CREATED": ("content_type", "POST", 201, "mutation"),
    "CONTENT_TYPE_UPDATED": ("content_type", "PATCH", 200, "mutation"),
    "CONTENT_TYPE_DELETED": ("content_type", "DELETE", 200, "delete"),
    "FIELD_DEFINITION_CREATED": (
        "field_definition",
        "POST",
        201,
        "mutation",
    ),
    "FIELD_DEFINITION_UPDATED": (
        "field_definition",
        "PATCH",
        200,
        "mutation",
    ),
    "FIELD_DEFINITION_DELETED": (
        "field_definition",
        "DELETE",
        200,
        "delete",
    ),
    "CONTENT_ITEM_CREATED": ("content_item", "POST", 201, "mutation"),
    "CONTENT_ITEM_UPDATED": ("content_item", "PATCH", 200, "mutation"),
    "CONTENT_ITEM_DELETED": ("content_item", "DELETE", 200, "delete"),
}
AGENT_SEMANTIC_ACTIONS = frozenset(AGENT_SEMANTIC_CONTRACTS)


class AgentQuotaExceededError(RuntimeError):
    """The immutable capability mutation budget is exhausted."""


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

    async def update_type_for_site(
        self, site_id: UUID, type_id: UUID, request: Any
    ) -> ContentTypeRecord:
        row = await self._fetchrow(
            AGENT_CONTENT_TYPE_UPDATE_SQL,
            site_id,
            type_id,
            json.dumps(request.labels, sort_keys=True)
            if request.labels is not None
            else None,
            request.slug_pattern,
            json.dumps(request.settings, sort_keys=True)
            if request.settings is not None
            else None,
            request.expected_definition_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ct(row)

    async def delete_type_for_site(
        self, site_id: UUID, type_id: UUID, expected: int
    ) -> ContentTypeRecord:
        row = await self._fetchrow(
            AGENT_CONTENT_TYPE_DELETE_SQL, site_id, type_id, expected
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ct(row)

    async def update_field_for_site(
        self, site_id: UUID, type_id: UUID, field_id: UUID, request: Any
    ) -> FieldDefinitionRecord:
        row = await self._fetchrow(
            AGENT_FIELD_UPDATE_SQL,
            site_id,
            type_id,
            field_id,
            request.label,
            request.required,
            request.localized,
            request.cardinality,
            request.position,
            json.dumps(request.validation, sort_keys=True)
            if request.validation is not None
            else None,
            json.dumps(request.ui_options, sort_keys=True)
            if request.ui_options is not None
            else None,
            request.expected_definition_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _fd(row)

    async def delete_field_for_site(
        self, site_id: UUID, type_id: UUID, field_id: UUID, expected: int
    ) -> FieldDefinitionRecord:
        row = await self._fetchrow(
            AGENT_FIELD_DELETE_SQL, site_id, type_id, field_id, expected
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _fd(row)

    async def create_item_for_site(
        self,
        site_id: UUID,
        type_id: UUID,
        request: CreateContentItemRequest,
    ) -> ContentItemRecord:
        content_type = await self._fetchrow(AGENT_TYPE_GET_SQL, site_id, type_id)
        if content_type is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        fields = await self._fetch(AGENT_FIELD_LIST_SQL, site_id, type_id)
        self._validate_item_values(
            request.values, tuple(_fd(field) for field in fields)
        )
        row = await self._fetchrow(
            AGENT_ITEM_CREATE_SQL,
            site_id,
            type_id,
            request.slug,
            request.status,
            json.dumps(request.values, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return cast(ContentItemRecord, _ci(row))

    async def get_item_for_site(
        self, site_id: UUID, item_id: UUID
    ) -> ContentItemRecord:
        row = await self._fetchrow(AGENT_ITEM_GET_SQL, site_id, item_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return cast(ContentItemRecord, _ci(row))

    async def update_item_for_site(
        self,
        site_id: UUID,
        item_id: UUID,
        request: AgentUpdateContentItemRequest,
    ) -> ContentItemRecord:
        current = await self.get_item_for_site(site_id, item_id)
        content_type = await self._fetchrow(
            AGENT_TYPE_GET_SQL, site_id, current.type_id
        )
        if content_type is None or current.type_definition_version != content_type[6]:
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        if request.values is not None:
            fields = await self._fetch(AGENT_FIELD_LIST_SQL, site_id, current.type_id)
            self._validate_item_values(
                request.values, tuple(_fd(field) for field in fields)
            )
        row = await self._fetchrow(
            AGENT_ITEM_UPDATE_SQL,
            site_id,
            item_id,
            request.slug,
            request.status,
            json.dumps(request.values, sort_keys=True)
            if request.values is not None
            else None,
            request.expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return cast(ContentItemRecord, _ci(row))

    async def delete_item_for_site(
        self, site_id: UUID, item_id: UUID, request: DeleteContentItemRequest
    ) -> ContentItemRecord:
        row = await self._fetchrow(
            AGENT_ITEM_DELETE_SQL, site_id, item_id, request.expected_row_version
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
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
    status_code: int,
    action: str | None,
    method: str | None,
    quota_kind: str,
) -> None:
    try:
        completion_sql = (
            COMPLETE_SEMANTIC_IDEMPOTENCY_SQL
            if action is not None
            else COMPLETE_IDEMPOTENCY_SQL
        )
        arguments: tuple[object, ...] = (
            context.capability_id,
            context.workspace_id,
            key,
            digest,
            operation_id,
            status_code,
            json.dumps(response.model_dump(mode="json"), sort_keys=True),
            resource_type,
            UUID(str(response.record["id"])),
            context.site_id,
        )
        if action is not None:
            if method is None or AGENT_SEMANTIC_CONTRACTS.get(action) != (
                resource_type,
                method,
                status_code,
                quota_kind,
            ):
                raise AgentMutationUnavailableError()
            arguments += (action, method, quota_kind)
        await _cow_fetchrow(
            cow,
            completion_sql,
            *arguments,
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
    status_code: int = 201,
    quota_kind: str = "mutation",
    action: str | None = None,
    method: str | None = None,
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
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(context.capability_id),
            )
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

            # Content-model wrappers own their resource quota reservation.
            # Page/component wrappers retain the legacy executor-owned path.
            if resource_type not in {
                "content_type",
                "field_definition",
                "content_item",
            }:
                try:
                    mutation_allowed = await cow.native.fetchval(
                        "SELECT control.slaif_agent_quota_consume($1,$2,$3)",
                        context.capability_id,
                        context.workspace_id,
                        quota_kind,
                    )
                except (asyncpg.PostgresError, OSError, TimeoutError) as error:
                    raise AgentMutationUnavailableError() from error
                if mutation_allowed is not True:
                    raise AgentQuotaExceededError()

            service = AgentCowContentModelService(cow)
            record = await mutate(service)
            record_body = record.model_dump(mode="json")
            if action is not None and (
                action not in AGENT_SEMANTIC_ACTIONS
                or method is None
                or AGENT_SEMANTIC_CONTRACTS[action]
                != (resource_type, method, status_code, quota_kind)
            ):
                raise AgentMutationUnavailableError()
            response = AgentMutationResponse(
                record=record_body,
                operation_id=reservation.operation_id,
                action=action,
            )
            await _complete(
                cow,
                context=context,
                key=key,
                digest=digest,
                operation_id=reservation.operation_id,
                response=response,
                resource_type=resource_type,
                status_code=status_code,
                action=action,
                method=method,
                quota_kind=quota_kind,
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
    "AgentQuotaExceededError",
    "IdempotencyMismatchError",
    "InvalidIdempotencyKeyError",
    "MissingIdempotencyKeyError",
    "execute_agent_mutation",
    "mutation_digest",
    "validate_idempotency_key",
]

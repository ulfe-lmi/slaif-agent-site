"""Content model persistence and query service (Editor API only)."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

import asyncpg

from .models import (
    ContentTypeRecord,
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    FieldDefinitionRecord,
    UpdateContentTypeRequest,
    UpdateFieldDefinitionRequest,
)

CT_CREATE_SQL = "SELECT * FROM content.slaif_content_type_create($1,$2,$3,$4,$5)"
CT_LIST_SQL = "SELECT * FROM content.slaif_content_type_list($1)"
CT_GET_SQL = "SELECT * FROM content.slaif_content_type_get($1)"
CT_UPDATE_SQL = "SELECT * FROM content.slaif_content_type_update($1,$2,$3,$4)"
CT_DELETE_SQL = "SELECT content.slaif_content_type_delete($1)"

FD_CREATE_SQL = (
    "SELECT * FROM content.slaif_field_definition_create("
    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10)"
)
FD_LIST_SQL = "SELECT * FROM content.slaif_field_definition_list($1)"
FD_GET_SQL = "SELECT * FROM content.slaif_field_definition_get($1)"
FD_UPDATE_SQL = (
    "SELECT * FROM content.slaif_field_definition_update($1,$2,$3,$4,$5,$6,$7,$8)"
)
FD_DELETE_SQL = "SELECT content.slaif_field_definition_delete($1)"


class ContentModelServiceReason(StrEnum):
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"


class ContentModelServiceError(RuntimeError):
    def __init__(self, reason: ContentModelServiceReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


def _ct(row: Any) -> ContentTypeRecord:
    import json

    return ContentTypeRecord(
        id=row[0],
        site_id=row[1],
        key=row[2],
        labels=json.loads(row[3]) if isinstance(row[3], str) else row[3],
        slug_pattern=row[4],
        status=row[5],
        definition_version=row[6],
        settings=json.loads(row[7]) if isinstance(row[7], str) else row[7],
        created_at=row[8],
        updated_at=row[9],
    )


def _fd(row: Any) -> FieldDefinitionRecord:
    import json

    return FieldDefinitionRecord(
        id=row[0],
        type_id=row[1],
        key=row[2],
        label=row[3],
        field_type=row[4],
        required=row[5],
        localized=row[6],
        cardinality=row[7],
        position=row[8],
        validation=json.loads(row[9]) if isinstance(row[9], str) else row[9],
        ui_options=json.loads(row[10]) if isinstance(row[10], str) else row[10],
        definition_version=row[11],
        created_at=row[12],
        updated_at=row[13],
    )


class ContentModelService:
    """Perform semantic content model operations via SECURITY DEFINER functions."""

    def __init__(self, pool: _Pool, *, acquire_timeout: float = 3.0) -> None:
        self._pool = pool
        self._acquire_timeout = acquire_timeout

    async def _fetchrow(self, sql: str, *arguments: object) -> Any:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                async with connection.transaction():
                    return await connection.fetchrow(sql, *arguments)
        except asyncio.CancelledError:
            raise
        except asyncpg.UniqueViolationError:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT) from None
        except asyncpg.RaiseError:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT) from None
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ContentModelServiceError(
                ContentModelServiceReason.UNAVAILABLE
            ) from None

    async def _fetch(self, sql: str, *arguments: object) -> list[Any]:
        try:
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                return list(await connection.fetch(sql, *arguments))
        except asyncio.CancelledError:
            raise
        except (asyncpg.PostgresError, OSError, TimeoutError):
            raise ContentModelServiceError(
                ContentModelServiceReason.UNAVAILABLE
            ) from None

    # -- Content Type CRUD --

    async def create_type(
        self, site_id: UUID, request: CreateContentTypeRequest
    ) -> ContentTypeRecord:
        row = await self._fetchrow(
            CT_CREATE_SQL,
            site_id,
            request.key,
            request.labels,
            request.slug_pattern,
            request.settings,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _ct(row)

    async def list_types(self, site_id: UUID) -> tuple[ContentTypeRecord, ...]:
        rows = await self._fetch(CT_LIST_SQL, site_id)
        return tuple(_ct(row) for row in rows)

    async def get_type(self, type_id: UUID) -> ContentTypeRecord:
        row = await self._fetchrow(CT_GET_SQL, type_id)
        if row is None or row[5] == "DELETED":
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ct(row)

    async def update_type(
        self, type_id: UUID, request: UpdateContentTypeRequest
    ) -> ContentTypeRecord:
        row = await self._fetchrow(
            CT_UPDATE_SQL,
            type_id,
            request.labels,
            request.slug_pattern,
            request.settings,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ct(row)

    async def delete_type(self, type_id: UUID) -> None:
        await self._fetchrow(CT_DELETE_SQL, type_id)

    # -- Field Definition CRUD --

    async def create_field(
        self, type_id: UUID, request: CreateFieldDefinitionRequest
    ) -> FieldDefinitionRecord:
        row = await self._fetchrow(
            FD_CREATE_SQL,
            type_id,
            request.key,
            request.label,
            request.field_type,
            request.required,
            request.localized,
            request.cardinality,
            request.position,
            request.validation,
            request.ui_options,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _fd(row)

    async def list_fields(self, type_id: UUID) -> tuple[FieldDefinitionRecord, ...]:
        rows = await self._fetch(FD_LIST_SQL, type_id)
        return tuple(_fd(row) for row in rows)

    async def get_field(self, field_id: UUID) -> FieldDefinitionRecord:
        row = await self._fetchrow(FD_GET_SQL, field_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _fd(row)

    async def update_field(
        self, field_id: UUID, request: UpdateFieldDefinitionRequest
    ) -> FieldDefinitionRecord:
        row = await self._fetchrow(
            FD_UPDATE_SQL,
            field_id,
            request.label,
            request.required,
            request.localized,
            request.cardinality,
            request.position,
            request.validation,
            request.ui_options,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _fd(row)

    async def delete_field(self, field_id: UUID) -> None:
        await self._fetchrow(FD_DELETE_SQL, field_id)

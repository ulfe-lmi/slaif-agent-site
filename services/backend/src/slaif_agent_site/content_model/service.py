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


class CollectionViewMixin:
    _fetchrow: Any
    _fetch: Any

    async def create_view(
        self,
        type_id: UUID,
        key: str,
        filter_spec: dict[str, Any],
        sort_spec: dict[str, Any],
        projection_spec: dict[str, Any],
        pagination_spec: dict[str, Any],
    ) -> Any:
        row = await self._fetchrow(
            CV_CREATE_SQL,
            type_id,
            key,
            filter_spec,
            sort_spec,
            projection_spec,
            pagination_spec,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _cv(row)

    async def list_views(self, type_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(CV_LIST_SQL, type_id)
        return tuple(_cv(row) for row in rows)

    async def get_view(self, view_id: UUID) -> Any:
        row = await self._fetchrow(CV_GET_SQL, view_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _cv(row)

    async def update_view(
        self,
        view_id: UUID,
        filter_spec: dict[str, Any] | None,
        sort_spec: dict[str, Any] | None,
        projection_spec: dict[str, Any] | None,
        pagination_spec: dict[str, Any] | None,
    ) -> Any:
        row = await self._fetchrow(
            CV_UPDATE_SQL,
            view_id,
            filter_spec,
            sort_spec,
            projection_spec,
            pagination_spec,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _cv(row)

    async def delete_view(self, view_id: UUID) -> None:
        await self._fetchrow(CV_DELETE_SQL, view_id)


class ContentItemMixin:
    _fetchrow: Any
    _fetch: Any

    async def create_item(
        self,
        site_id: UUID,
        type_id: UUID,
        slug: str,
        status: str,
        values: dict[str, Any],
        type_definition_version: int,
    ) -> Any:
        row = await self._fetchrow(
            CI_CREATE_SQL,
            site_id,
            type_id,
            slug,
            status,
            values,
            type_definition_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _ci(row)

    async def list_items(self, site_id: UUID, type_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(CI_LIST_SQL, site_id, type_id)
        return tuple(_ci(row) for row in rows)

    async def get_item(self, item_id: UUID) -> Any:
        row = await self._fetchrow(CI_GET_SQL, item_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ci(row)

    async def update_item(
        self,
        item_id: UUID,
        slug: str | None,
        status: str | None,
        values: dict[str, Any] | None,
        expected_row_version: int | None,
    ) -> Any:
        row = await self._fetchrow(
            CI_UPDATE_SQL, item_id, slug, status, values, expected_row_version, None
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ci(row)

    async def delete_item(
        self, item_id: UUID, expected_row_version: int | None
    ) -> None:
        await self._fetchrow(CI_DELETE_SQL, item_id, expected_row_version)


class ContentModelService(ContentItemMixin, CollectionViewMixin):
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


# -- Content Item SQL constants --
CI_CREATE_SQL = "SELECT * FROM content.slaif_content_item_create($1,$2,$3,$4,$5,$6)"
CI_LIST_SQL = "SELECT * FROM content.slaif_content_item_list($1,$2)"
CI_GET_SQL = "SELECT * FROM content.slaif_content_item_get($1)"
CI_UPDATE_SQL = "SELECT * FROM content.slaif_content_item_update($1,$2,$3,$4,$5,$6)"
CI_DELETE_SQL = "SELECT content.slaif_content_item_delete($1,$2)"


def _ci(row: Any) -> Any:
    import json

    from .item_models import ContentItemRecord

    return ContentItemRecord(
        id=row[0],
        site_id=row[1],
        type_id=row[2],
        slug=row[3],
        status=row[4],
        type_definition_version=row[5],
        values=json.loads(row[6]) if isinstance(row[6], str) else row[6],
        row_version=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


CV_CREATE_SQL = "SELECT * FROM content.slaif_collection_view_create($1,$2,$3,$4,$5,$6)"
CV_LIST_SQL = "SELECT * FROM content.slaif_collection_view_list($1)"
CV_GET_SQL = "SELECT * FROM content.slaif_collection_view_get($1)"
CV_UPDATE_SQL = "SELECT * FROM content.slaif_collection_view_update($1,$2,$3,$4,$5)"
CV_DELETE_SQL = "SELECT content.slaif_collection_view_delete($1)"


def _cv(row: Any) -> Any:
    import json

    from .view_models import CollectionViewRecord

    return CollectionViewRecord(
        id=row[0],
        site_id=row[1],
        type_id=row[2],
        key=row[3],
        filter_spec=json.loads(row[4]) if isinstance(row[4], str) else row[4],
        sort_spec=json.loads(row[5]) if isinstance(row[5], str) else row[5],
        projection_spec=json.loads(row[6]) if isinstance(row[6], str) else row[6],
        pagination_spec=json.loads(row[7]) if isinstance(row[7], str) else row[7],
        created_at=row[8],
        updated_at=row[9],
    )

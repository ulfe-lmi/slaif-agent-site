"""Content model persistence and query service.

The normal service owns a pool acquisition.  Agent mutations bind a small
specialized service instance to an already-open public ``CowSession`` so the
semantic functions run inside the trusted COW transaction and never acquire a
second ordinary connection.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID

import asyncpg

from .models import (
    ContentTypeRecord,
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    CreateRelationRequest,
    CreateTranslationRequest,
    FieldDefinitionRecord,
    RelationRecord,
    TranslationRecord,
    UpdateContentTypeRequest,
    UpdateFieldDefinitionRequest,
    UpdateRelationRequest,
    UpdateTranslationRequest,
)
from .query_dsl import validate_query_contract
from .site_data_models import (
    CreateLocaleRequest,
    CreateNavigationItemRequest,
    CreateProposedSideEffectRequest,
    CreateRedirectRequest,
    LocaleRecord,
    NavigationItemRecord,
    ProposedSideEffectRecord,
    RedirectRecord,
    UpdateLocaleRequest,
    UpdateNavigationItemRequest,
    UpdateRedirectRequest,
)
from .site_data_validators import (
    validate_redirect,
    validate_redirect_graph,
    validate_side_effect,
    validate_target,
)
from .validators import validate_values

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
    VALIDATION = "validation"
    QUOTA = "quota"
    AUTHORIZATION = "authorization"


class ContentModelServiceError(RuntimeError):
    def __init__(
        self, reason: ContentModelServiceReason, *, code: str | None = None
    ) -> None:
        super().__init__(reason.value)
        self.reason = reason
        self.code = code


def _semantic_database_error_code(error: asyncpg.PostgresError) -> str | None:
    """Preserve only stable, non-sensitive dependency denial identifiers."""

    message = getattr(error, "message", str(error)).split("\n", 1)[0]
    if message in {"FIELD_DEPENDENCIES", "TYPE_DEPENDENCIES"}:
        return message
    return None


class _Pool(Protocol):
    def acquire(self, *, timeout: float) -> Any: ...


class _CowSession(Protocol):
    native: Any

    async def validate_context(self) -> None: ...


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

    offset = 1 if len(row) >= 15 else 0
    return FieldDefinitionRecord(
        id=row[0],
        site_id=row[1] if offset else UUID(int=0),
        type_id=row[1 + offset],
        key=row[2 + offset],
        label=row[3 + offset],
        field_type=row[4 + offset],
        required=row[5 + offset],
        localized=row[6 + offset],
        cardinality=row[7 + offset],
        position=row[8 + offset],
        validation=json.loads(row[9 + offset])
        if isinstance(row[9 + offset], str)
        else row[9 + offset],
        ui_options=json.loads(row[10 + offset])
        if isinstance(row[10 + offset], str)
        else row[10 + offset],
        definition_version=row[11 + offset],
        created_at=row[12 + offset],
        updated_at=row[13 + offset],
    )


class CollectionViewMixin:
    _fetchrow: Any
    _fetch: Any
    get_type: Any
    list_fields: Any

    async def create_view(
        self,
        site_id: UUID,
        type_id: UUID,
        key: str,
        filter_spec: dict[str, Any],
        sort_spec: dict[str, Any],
        projection_spec: dict[str, Any],
        pagination_spec: dict[str, Any],
        definition_version: int | None = None,
    ) -> Any:
        content_type = await self.get_type(type_id)
        if content_type.site_id != site_id or (
            definition_version is not None
            and definition_version != content_type.definition_version
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        try:
            validate_query_contract(
                filter_spec,
                sort_spec,
                projection_spec,
                pagination_spec,
                await self.list_fields(type_id),
            )
        except (ValueError, TypeError):
            raise ContentModelServiceError(
                ContentModelServiceReason.VALIDATION
            ) from None
        row = await self._fetchrow(
            CV2_CREATE_SQL,
            site_id,
            type_id,
            key,
            json.dumps(filter_spec, sort_keys=True),
            json.dumps(sort_spec, sort_keys=True),
            json.dumps(projection_spec, sort_keys=True),
            json.dumps(pagination_spec, sort_keys=True),
            content_type.definition_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _cv(row)

    async def list_views(self, site_id: UUID, type_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(CV2_LIST_SQL, site_id, type_id)
        return tuple(_cv(row) for row in rows)

    async def get_view(self, site_id: UUID, view_id: UUID) -> Any:
        row = await self._fetchrow(CV2_GET_SQL, site_id, view_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _cv(row)

    async def update_view(
        self,
        site_id: UUID,
        view_id: UUID,
        filter_spec: dict[str, Any] | None,
        sort_spec: dict[str, Any] | None,
        projection_spec: dict[str, Any] | None,
        pagination_spec: dict[str, Any] | None,
        expected_row_version: int,
        definition_version: int | None = None,
    ) -> Any:
        current = await self.get_view(site_id, view_id)
        if (
            definition_version is not None
            and definition_version != current.definition_version
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        values = {
            "filter": filter_spec if filter_spec is not None else current.filter_spec,
            "sort": sort_spec if sort_spec is not None else current.sort_spec,
            "projection": projection_spec
            if projection_spec is not None
            else current.projection_spec,
            "pagination": pagination_spec
            if pagination_spec is not None
            else current.pagination_spec,
        }
        try:
            validate_query_contract(
                values["filter"],
                values["sort"],
                values["projection"],
                values["pagination"],
                await self.list_fields(current.type_id),
            )
        except (ValueError, TypeError):
            raise ContentModelServiceError(
                ContentModelServiceReason.VALIDATION
            ) from None
        row = await self._fetchrow(
            CV2_UPDATE_SQL,
            site_id,
            view_id,
            json.dumps(filter_spec, sort_keys=True)
            if filter_spec is not None
            else None,
            json.dumps(sort_spec, sort_keys=True) if sort_spec is not None else None,
            json.dumps(projection_spec, sort_keys=True)
            if projection_spec is not None
            else None,
            json.dumps(pagination_spec, sort_keys=True)
            if pagination_spec is not None
            else None,
            expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _cv(row)

    async def delete_view(
        self, site_id: UUID, view_id: UUID, expected_row_version: int
    ) -> None:
        await self._fetchrow(CV2_DELETE_SQL, site_id, view_id, expected_row_version)


class PageMixin:
    _fetchrow: Any
    _fetch: Any

    async def create_page(
        self, site_id: UUID, slug: str, title: str, status: str, locale: str
    ) -> Any:
        row = await self._fetchrow(PG_CREATE_SQL, site_id, slug, title, status, locale)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _pg(row)

    async def list_pages(self, site_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(PG_LIST_SQL, site_id)
        return tuple(_pg(row) for row in rows)

    async def get_page(self, page_id: UUID) -> Any:
        row = await self._fetchrow(PG_GET_SQL, page_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _pg(row)

    async def update_page(
        self,
        page_id: UUID,
        slug: str | None,
        title: str | None,
        status: str | None,
        expected_row_version: int | None,
    ) -> Any:
        row = await self._fetchrow(
            PG_UPDATE_SQL, page_id, slug, title, status, expected_row_version
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _pg(row)

    async def delete_page(self, page_id: UUID) -> None:
        await self._fetchrow(PG_DELETE_SQL, page_id)


class NavThemeMixin:
    _fetchrow: Any
    _fetch: Any

    async def create_navigation(
        self, site_id: UUID, key: str, label: str, settings: dict[str, Any]
    ) -> Any:
        row = await self._fetchrow(
            NV_CREATE_SQL, site_id, key, label, json.dumps(settings, sort_keys=True)
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _nv(row)

    async def list_navigation(self, site_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(NV_LIST_SQL, site_id)
        return tuple(_nv(row) for row in rows)

    async def get_navigation(self, nav_id: UUID) -> Any:
        row = await self._fetchrow(NV_GET_SQL, nav_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _nv(row)

    async def update_navigation(
        self, nav_id: UUID, label: str | None, settings: dict[str, Any] | None
    ) -> Any:
        row = await self._fetchrow(
            NV_UPDATE_SQL,
            nav_id,
            label,
            json.dumps(settings, sort_keys=True) if settings is not None else None,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _nv(row)

    async def delete_navigation(self, nav_id: UUID) -> None:
        await self._fetchrow(NV_DELETE_SQL, nav_id)

    async def get_theme(self, site_id: UUID) -> Any:
        row = await self._fetchrow(TH_GET_SQL, site_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _th(row)

    async def update_theme(
        self,
        site_id: UUID,
        palette: dict[str, Any] | None,
        typography: dict[str, Any] | None,
        layout: dict[str, Any] | None,
        shape: dict[str, Any] | None,
    ) -> Any:
        row = await self._fetchrow(
            TH_UPDATE_SQL, site_id, palette, typography, layout, shape
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _th(row)


class MediaMixin:
    _fetchrow: Any
    _fetch: Any

    async def create_media(
        self,
        site_id: UUID,
        uploaded_by: UUID | None,
        filename: str,
        mime_type: str,
        size_bytes: int,
        content_hash: str,
        storage_key: str,
        alt_text: str,
        metadata: dict[str, Any],
    ) -> Any:
        row = await self._fetchrow(
            MD_CREATE_SQL,
            site_id,
            uploaded_by,
            filename,
            mime_type,
            size_bytes,
            content_hash,
            storage_key,
            alt_text,
            json.dumps(metadata, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _md(row)

    async def list_media(self, site_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(MD_LIST_SQL, site_id)
        return tuple(_md(row) for row in rows)

    async def get_media(self, media_id: UUID) -> Any:
        row = await self._fetchrow(MD_GET_SQL, media_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _md(row)

    async def update_media(
        self, media_id: UUID, alt_text: str | None, metadata: dict[str, Any] | None
    ) -> Any:
        row = await self._fetchrow(
            MD_UPDATE_SQL,
            media_id,
            alt_text,
            json.dumps(metadata, sort_keys=True) if metadata is not None else None,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _md(row)

    async def delete_media(self, media_id: UUID) -> None:
        await self._fetchrow(MD_DELETE_SQL, media_id)


class CompositionMixin:
    _fetchrow: Any
    _fetch: Any

    async def add_composition_node(
        self,
        site_id: UUID,
        page_id: UUID,
        component_type: str,
        parent_id: UUID | None,
        slot_key: str,
        order_key: int,
        props: dict[str, Any],
    ) -> Any:
        row = await self._fetchrow(
            CMP_ADD_SQL,
            site_id,
            page_id,
            component_type,
            parent_id,
            slot_key,
            order_key,
            json.dumps(props, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _cmp(row)

    async def update_composition_node(
        self,
        node_id: UUID,
        props: dict[str, Any] | None,
        slot_key: str | None,
        order_key: int | None,
    ) -> Any:
        row = await self._fetchrow(
            CMP_UPDATE_SQL,
            node_id,
            json.dumps(props, sort_keys=True) if props is not None else None,
            slot_key,
            order_key,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _cmp(row)

    async def move_composition_node(
        self,
        node_id: UUID,
        new_parent_id: UUID | None,
        new_slot_key: str | None,
        new_order_key: int,
    ) -> Any:
        row = await self._fetchrow(
            CMP_MOVE_SQL, node_id, new_parent_id, new_slot_key, new_order_key
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _cmp(row)

    async def delete_composition_node(self, node_id: UUID) -> None:
        await self._fetchrow(CMP_DELETE_SQL, node_id)

    async def list_composition(self, page_id: UUID) -> tuple[Any, ...]:
        rows = await self._fetch(CMP_LIST_SQL, page_id)
        return tuple(_cmp(row) for row in rows)


class ContentItemMixin:
    _fetchrow: Any
    _fetch: Any
    get_type: Any
    list_fields: Any

    async def _assert_item_definition_current(self, item: Any) -> None:
        content_type = await self.get_type(item.type_id)
        if item.type_definition_version != content_type.definition_version:
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)

    @staticmethod
    def _validate_item_values(
        values: dict[str, Any], fields: Iterable[FieldDefinitionRecord]
    ) -> None:
        try:
            validate_values(values, fields)
        except (ValueError, TypeError):
            raise ContentModelServiceError(
                ContentModelServiceReason.VALIDATION
            ) from None

    async def create_item(
        self,
        site_id: UUID,
        type_id: UUID,
        slug: str,
        status: str,
        values: dict[str, Any],
        type_definition_version: int,
    ) -> Any:
        content_type = await self.get_type(type_id)
        if (
            content_type.site_id != site_id
            or type_definition_version != content_type.definition_version
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        self._validate_item_values(values, await self.list_fields(type_id))
        row = await self._fetchrow(
            CI_CREATE_SQL,
            site_id,
            type_id,
            slug,
            status,
            json.dumps(values, sort_keys=True),
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
        current = await self.get_item(item_id)
        await self._assert_item_definition_current(current)
        if values is not None:
            self._validate_item_values(values, await self.list_fields(current.type_id))
        row = await self._fetchrow(
            CI_UPDATE_SQL,
            item_id,
            slug,
            status,
            json.dumps(values, sort_keys=True) if values is not None else None,
            expected_row_version,
            None,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ci(row)

    async def delete_item(
        self, item_id: UUID, expected_row_version: int | None
    ) -> None:
        await self._fetchrow(CI_DELETE_SQL, item_id, expected_row_version)


class EditableDomainMixin:
    _fetchrow: Any
    _fetch: Any
    get_item: Any
    list_fields: Any
    get_field: Any
    _assert_item_definition_current: Any

    async def _validate_relation_target(
        self,
        site_id: UUID,
        source_item_id: UUID,
        field_definition_id: UUID,
        target_item_id: UUID,
    ) -> None:
        source = await self.get_item(source_item_id)
        field = await self.get_field(field_definition_id)
        target = await self.get_item(target_item_id)
        await self._assert_item_definition_current(source)
        await self._assert_item_definition_current(target)
        if source.site_id != site_id or target.site_id != site_id:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        if field.site_id != site_id or field.type_id != source.type_id:
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        if field.field_type not in ("reference", "multi_reference"):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        allowed = field.validation.get("target_type_id")
        if allowed is not None and str(target.type_id) != str(allowed):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)

    async def create_translation(
        self, site_id: UUID, item_id: UUID, request: CreateTranslationRequest
    ) -> TranslationRecord:
        item = await self.get_item(item_id)
        if item.site_id != site_id:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        await self._assert_item_definition_current(item)
        try:
            validate_values(
                request.localized_values,
                await self.list_fields(item.type_id),
                localized=True,
            )
        except (ValueError, TypeError):
            raise ContentModelServiceError(
                ContentModelServiceReason.VALIDATION
            ) from None
        row = await self._fetchrow(
            TR_CREATE_SQL,
            site_id,
            item_id,
            request.locale,
            json.dumps(request.localized_values, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        if row[0] is None:
            row = await self._fetchrow(TR_EXACT_SQL, site_id, item_id, request.locale)
            if row is None:
                raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _tr(row)

    async def list_translations(
        self, site_id: UUID, item_id: UUID
    ) -> tuple[TranslationRecord, ...]:
        item = await self.get_item(item_id)
        if item.site_id != site_id:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return tuple(
            _tr(row) for row in await self._fetch(TR_LIST_SQL, site_id, item_id)
        )

    async def get_translation(
        self, site_id: UUID, translation_id: UUID
    ) -> TranslationRecord:
        row = await self._fetchrow(TR_GET_SQL, site_id, translation_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _tr(row)

    async def update_translation(
        self, site_id: UUID, translation_id: UUID, request: UpdateTranslationRequest
    ) -> TranslationRecord:
        current = await self.get_translation(site_id, translation_id)
        await self._assert_item_definition_current(await self.get_item(current.item_id))
        if request.localized_values is not None:
            item = await self.get_item(current.item_id)
            await self._assert_item_definition_current(item)
            try:
                validate_values(
                    request.localized_values,
                    await self.list_fields(item.type_id),
                    localized=True,
                )
            except (ValueError, TypeError):
                raise ContentModelServiceError(
                    ContentModelServiceReason.VALIDATION
                ) from None
        row = await self._fetchrow(
            TR_UPDATE_SQL,
            site_id,
            translation_id,
            request.locale,
            json.dumps(request.localized_values, sort_keys=True)
            if request.localized_values is not None
            else None,
            request.expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _tr(row)

    async def delete_translation(
        self, site_id: UUID, translation_id: UUID, expected_row_version: int
    ) -> None:
        await self._fetchrow(
            TR_DELETE_SQL, site_id, translation_id, expected_row_version
        )

    async def create_relation(
        self, site_id: UUID, source_item_id: UUID, request: CreateRelationRequest
    ) -> RelationRecord:
        await self._validate_relation_target(
            site_id, source_item_id, request.field_definition_id, request.target_item_id
        )
        row = await self._fetchrow(
            REL_CREATE_SQL,
            site_id,
            source_item_id,
            request.field_definition_id,
            request.target_item_id,
            request.position,
            json.dumps(request.metadata, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        if row[0] is None:
            row = await self._fetchrow(
                REL_EXACT_SQL,
                site_id,
                source_item_id,
                request.field_definition_id,
                request.target_item_id,
                request.position,
            )
            if row is None:
                raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _rel(row)

    async def list_relations(
        self, site_id: UUID, source_item_id: UUID
    ) -> tuple[RelationRecord, ...]:
        source = await self.get_item(source_item_id)
        if source.site_id != site_id:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return tuple(
            _rel(row)
            for row in await self._fetch(REL_LIST_SQL, site_id, source_item_id)
        )

    async def get_relation(self, site_id: UUID, relation_id: UUID) -> RelationRecord:
        row = await self._fetchrow(REL_GET_SQL, site_id, relation_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _rel(row)

    async def update_relation(
        self, site_id: UUID, relation_id: UUID, request: UpdateRelationRequest
    ) -> RelationRecord:
        current = await self.get_relation(site_id, relation_id)
        await self._assert_item_definition_current(
            await self.get_item(current.source_item_id)
        )
        await self._validate_relation_target(
            site_id,
            current.source_item_id,
            current.field_definition_id,
            request.target_item_id or current.target_item_id,
        )
        row = await self._fetchrow(
            REL_UPDATE_SQL,
            site_id,
            relation_id,
            request.target_item_id,
            request.position,
            json.dumps(request.metadata, sort_keys=True)
            if request.metadata is not None
            else None,
            request.expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _rel(row)

    async def delete_relation(
        self, site_id: UUID, relation_id: UUID, expected_row_version: int
    ) -> None:
        await self._fetchrow(REL_DELETE_SQL, site_id, relation_id, expected_row_version)


class SiteDataMixin:
    """Semantic CRUD for the fixed site-data substrate."""

    _fetchrow: Any
    _fetch: Any

    async def _validate_navigation_parent(
        self,
        site_id: UUID,
        navigation_id: UUID,
        item_id: UUID | None,
        parent_id: UUID | None,
    ) -> None:
        if parent_id is None:
            return
        if item_id == parent_id:
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        rows = await self.list_navigation_items(site_id, navigation_id)
        parents = {row.id: row.parent_id for row in rows}
        cursor: UUID | None = parent_id
        depth = 0
        while cursor is not None:
            if cursor == item_id or depth >= 8:
                raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
            cursor = parents.get(cursor)
            depth += 1
        if parent_id not in parents:
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)

    async def create_locale(
        self, site_id: UUID, request: CreateLocaleRequest
    ) -> LocaleRecord:
        existing = await self.list_locales(site_id)
        if (not existing and not request.is_default) or (
            request.is_default and not request.enabled
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        row = await self._fetchrow(
            LOCALE_CREATE_SQL,
            site_id,
            request.tag,
            request.enabled,
            request.is_default,
            request.position,
            json.dumps(request.metadata, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        if row[0] is None:
            row = await self._fetchrow(LOCALE_EXACT_SQL, site_id, request.tag)
            if row is None:
                raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _locale(row)

    async def list_locales(self, site_id: UUID) -> tuple[LocaleRecord, ...]:
        return tuple(
            _locale(row) for row in await self._fetch(LOCALE_LIST_SQL, site_id)
        )

    async def get_locale(self, site_id: UUID, locale_id: UUID) -> LocaleRecord:
        row = await self._fetchrow(LOCALE_GET_SQL, site_id, locale_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        if row[0] is None:
            return await self.get_locale(site_id, locale_id)
        return _locale(row)

    async def update_locale(
        self, site_id: UUID, locale_id: UUID, request: UpdateLocaleRequest
    ) -> LocaleRecord:
        current = await self.get_locale(site_id, locale_id)
        if current.is_default and (not request.is_default or not request.enabled):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        row = await self._fetchrow(
            LOCALE_UPDATE_SQL,
            site_id,
            locale_id,
            request.tag,
            request.enabled,
            request.is_default,
            request.position,
            json.dumps(request.metadata, sort_keys=True),
            request.expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        if row[0] is None:
            return await self.get_locale(site_id, locale_id)
        return _locale(row)

    async def delete_locale(
        self, site_id: UUID, locale_id: UUID, expected_row_version: int
    ) -> None:
        await self._fetchrow(
            LOCALE_DELETE_SQL, site_id, locale_id, expected_row_version
        )

    async def create_navigation_item(
        self, site_id: UUID, request: CreateNavigationItemRequest
    ) -> NavigationItemRecord:
        validate_target(request.target_kind, request.target_value)
        await self._validate_navigation_parent(
            site_id, request.navigation_id, None, request.parent_id
        )
        if request.locale is not None and not any(
            locale.tag == request.locale and locale.enabled
            for locale in await self.list_locales(site_id)
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        if any(
            row.parent_id == request.parent_id and row.position == request.position
            for row in await self.list_navigation_items(site_id, request.navigation_id)
        ):
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        row = await self._fetchrow(
            NAV_ITEM_CREATE_SQL,
            site_id,
            request.navigation_id,
            request.parent_id,
            request.page_id,
            request.target_kind,
            request.target_value,
            json.dumps(request.labels, sort_keys=True),
            request.locale,
            request.position,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        # COW's INSTEAD OF INSERT trigger may return a sparse NEW record for
        # server defaults.  Resolve it by the exact caller-owned identity,
        # never by an arbitrary latest/last row.
        if row[0] is None:
            row = await self._fetchrow(
                NAV_ITEM_EXACT_SQL,
                site_id,
                request.navigation_id,
                request.parent_id,
                request.target_kind,
                request.target_value,
                request.position,
            )
            if row is None:
                raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _nav_item(row)

    async def list_navigation_items(
        self, site_id: UUID, navigation_id: UUID
    ) -> tuple[NavigationItemRecord, ...]:
        return tuple(
            _nav_item(row)
            for row in await self._fetch(NAV_ITEM_LIST_SQL, site_id, navigation_id)
        )

    async def get_navigation_item(
        self, site_id: UUID, item_id: UUID
    ) -> NavigationItemRecord:
        row = await self._fetchrow(NAV_ITEM_GET_SQL, site_id, item_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        if row[0] is None:
            return await self.get_navigation_item(site_id, item_id)
        return _nav_item(row)

    async def update_navigation_item(
        self, site_id: UUID, item_id: UUID, request: UpdateNavigationItemRequest
    ) -> NavigationItemRecord:
        validate_target(request.target_kind, request.target_value)
        current = await self.get_navigation_item(site_id, item_id)
        await self._validate_navigation_parent(
            site_id, current.navigation_id, item_id, request.parent_id
        )
        if request.locale is not None and not any(
            locale.tag == request.locale and locale.enabled
            for locale in await self.list_locales(site_id)
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        row = await self._fetchrow(
            NAV_ITEM_UPDATE_SQL,
            site_id,
            item_id,
            request.parent_id,
            request.page_id,
            request.target_kind,
            request.target_value,
            json.dumps(request.labels, sort_keys=True),
            request.locale,
            request.position,
            request.expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _nav_item(row)

    async def delete_navigation_item(
        self, site_id: UUID, item_id: UUID, expected_row_version: int
    ) -> None:
        await self._fetchrow(
            NAV_ITEM_DELETE_SQL, site_id, item_id, expected_row_version
        )

    async def move_navigation_item(
        self,
        site_id: UUID,
        item_id: UUID,
        parent_id: UUID | None,
        position: int,
        expected_row_version: int,
    ) -> NavigationItemRecord:
        current = await self.get_navigation_item(site_id, item_id)
        await self._validate_navigation_parent(
            site_id, current.navigation_id, item_id, parent_id
        )
        request = UpdateNavigationItemRequest(
            navigation_id=current.navigation_id,
            parent_id=parent_id,
            page_id=current.page_id,
            target_kind=current.target_kind,
            target_value=current.target_value,
            labels=current.labels,
            locale=current.locale,
            position=position,
            expected_row_version=expected_row_version,
        )
        return await self.update_navigation_item(site_id, item_id, request)

    async def create_redirect(
        self, site_id: UUID, request: CreateRedirectRequest
    ) -> RedirectRecord:
        source, target = validate_redirect(request.source_route, request.target)
        validate_redirect_graph(
            source,
            target,
            [
                (row.source_route, row.target)
                for row in await self.list_redirects(site_id)
            ],
        )
        if request.locale is not None and not any(
            locale.tag == request.locale and locale.enabled
            for locale in await self.list_locales(site_id)
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        row = await self._fetchrow(
            REDIRECT_CREATE_SQL,
            site_id,
            source,
            target,
            request.status_code,
            request.locale,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        if row[0] is None:
            row = await self._fetchrow(
                REDIRECT_EXACT_SQL, site_id, source, request.locale
            )
            if row is None:
                raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _redirect(row)

    async def list_redirects(self, site_id: UUID) -> tuple[RedirectRecord, ...]:
        return tuple(
            _redirect(row) for row in await self._fetch(REDIRECT_LIST_SQL, site_id)
        )

    async def get_redirect(self, site_id: UUID, redirect_id: UUID) -> RedirectRecord:
        row = await self._fetchrow(REDIRECT_GET_SQL, site_id, redirect_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        if row[0] is None:
            return await self.get_redirect(site_id, redirect_id)
        return _redirect(row)

    async def update_redirect(
        self, site_id: UUID, redirect_id: UUID, request: UpdateRedirectRequest
    ) -> RedirectRecord:
        source, target = validate_redirect(request.source_route, request.target)
        validate_redirect_graph(
            source,
            target,
            [
                (row.source_route, row.target)
                for row in await self.list_redirects(site_id)
                if row.id != redirect_id
            ],
        )
        if request.locale is not None and not any(
            locale.tag == request.locale and locale.enabled
            for locale in await self.list_locales(site_id)
        ):
            raise ContentModelServiceError(ContentModelServiceReason.VALIDATION)
        row = await self._fetchrow(
            REDIRECT_UPDATE_SQL,
            site_id,
            redirect_id,
            source,
            target,
            request.status_code,
            request.locale,
            request.expected_row_version,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _redirect(row)

    async def delete_redirect(
        self, site_id: UUID, redirect_id: UUID, expected_row_version: int
    ) -> None:
        await self._fetchrow(
            REDIRECT_DELETE_SQL, site_id, redirect_id, expected_row_version
        )

    async def create_proposed_side_effect(
        self, site_id: UUID, request: CreateProposedSideEffectRequest
    ) -> ProposedSideEffectRecord:
        validate_side_effect(request.kind, request.payload)
        row = await self._fetchrow(
            EFFECT_CREATE_SQL,
            site_id,
            request.workspace_id,
            request.kind,
            json.dumps(request.payload, sort_keys=True),
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT)
        return _effect(row)

    async def list_proposed_side_effects(
        self, site_id: UUID, workspace_id: UUID
    ) -> tuple[ProposedSideEffectRecord, ...]:
        return tuple(
            _effect(row)
            for row in await self._fetch(EFFECT_LIST_SQL, site_id, workspace_id)
        )


class ContentModelService(
    ContentItemMixin,
    EditableDomainMixin,
    SiteDataMixin,
    CollectionViewMixin,
    NavThemeMixin,
    PageMixin,
    CompositionMixin,
    MediaMixin,
):
    """Perform semantic content model operations via SECURITY DEFINER functions."""

    def __init__(
        self,
        pool: _Pool | None,
        *,
        acquire_timeout: float = 3.0,
        cow_session: _CowSession | None = None,
    ) -> None:
        if pool is None and cow_session is None:
            raise ValueError("content service requires a pool or COW session")
        if pool is not None and cow_session is not None:
            raise ValueError("content service cannot own pool and COW session")
        self._pool = pool
        self._acquire_timeout = acquire_timeout
        self._cow_session = cow_session

    @classmethod
    def for_cow_session(
        cls, cow_session: _CowSession, *, acquire_timeout: float = 3.0
    ) -> ContentModelService:
        """Bind semantic calls to one active, trusted COW transaction."""

        return cls(
            None,
            acquire_timeout=acquire_timeout,
            cow_session=cow_session,
        )

    async def _fetchrow(self, sql: str, *arguments: object) -> Any:
        try:
            if self._cow_session is not None:
                await self._cow_session.validate_context()
                return await self._cow_session.native.fetchrow(sql, *arguments)
            assert self._pool is not None
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                async with connection.transaction():
                    return await connection.fetchrow(sql, *arguments)
        except asyncio.CancelledError:
            raise
        except asyncpg.UniqueViolationError:
            raise ContentModelServiceError(ContentModelServiceReason.CONFLICT) from None
        except asyncpg.PostgresError as error:
            if getattr(error, "sqlstate", None) == "P0002":
                raise ContentModelServiceError(
                    ContentModelServiceReason.NOT_FOUND
                ) from None
            if getattr(error, "sqlstate", None) == "P0003":
                raise ContentModelServiceError(
                    ContentModelServiceReason.VALIDATION,
                    code=_semantic_database_error_code(error),
                ) from None
            if getattr(error, "sqlstate", None) == "P0004":
                raise ContentModelServiceError(
                    ContentModelServiceReason.CONFLICT
                ) from None
            if getattr(error, "sqlstate", None) == "P0005":
                raise ContentModelServiceError(
                    ContentModelServiceReason.QUOTA
                ) from None
            if getattr(error, "sqlstate", None) == "P0006":
                raise ContentModelServiceError(
                    ContentModelServiceReason.QUOTA
                ) from None
            if getattr(error, "sqlstate", None) == "P0007":
                raise ContentModelServiceError(
                    ContentModelServiceReason.AUTHORIZATION
                ) from None
            if getattr(error, "sqlstate", None) == "P0001" or isinstance(
                error, asyncpg.RaiseError
            ):
                raise ContentModelServiceError(
                    ContentModelServiceReason.CONFLICT
                ) from None
            raise ContentModelServiceError(
                ContentModelServiceReason.UNAVAILABLE
            ) from None
        except (OSError, TimeoutError):
            raise ContentModelServiceError(
                ContentModelServiceReason.UNAVAILABLE
            ) from None

    async def _fetch(self, sql: str, *arguments: object) -> list[Any]:
        try:
            if self._cow_session is not None:
                await self._cow_session.validate_context()
                return list(await self._cow_session.native.fetch(sql, *arguments))
            assert self._pool is not None
            async with self._pool.acquire(timeout=self._acquire_timeout) as connection:
                return list(await connection.fetch(sql, *arguments))
        except asyncio.CancelledError:
            raise
        except asyncpg.PostgresError as error:
            if getattr(error, "sqlstate", None) == "P0002":
                raise ContentModelServiceError(
                    ContentModelServiceReason.NOT_FOUND
                ) from None
            if getattr(error, "sqlstate", None) == "P0003":
                raise ContentModelServiceError(
                    ContentModelServiceReason.VALIDATION,
                    code=_semantic_database_error_code(error),
                ) from None
            if getattr(error, "sqlstate", None) == "P0004":
                raise ContentModelServiceError(
                    ContentModelServiceReason.CONFLICT
                ) from None
            if getattr(error, "sqlstate", None) in {"P0005", "P0006"}:
                raise ContentModelServiceError(
                    ContentModelServiceReason.QUOTA
                ) from None
            if getattr(error, "sqlstate", None) == "P0007":
                raise ContentModelServiceError(
                    ContentModelServiceReason.AUTHORIZATION
                ) from None
            raise ContentModelServiceError(
                ContentModelServiceReason.UNAVAILABLE
            ) from None
        except (OSError, TimeoutError):
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
            json.dumps(request.labels, sort_keys=True),
            request.slug_pattern,
            json.dumps(request.settings, sort_keys=True),
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
            json.dumps(request.labels, sort_keys=True)
            if request.labels is not None
            else None,
            request.slug_pattern,
            json.dumps(request.settings, sort_keys=True)
            if request.settings is not None
            else None,
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
            json.dumps(request.validation, sort_keys=True),
            json.dumps(request.ui_options, sort_keys=True),
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
            json.dumps(request.validation, sort_keys=True)
            if request.validation is not None
            else None,
            json.dumps(request.ui_options, sort_keys=True)
            if request.ui_options is not None
            else None,
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _fd(row)

    async def delete_field(self, field_id: UUID) -> None:
        await self._fetchrow(FD_DELETE_SQL, field_id)


# -- Editable domain SQL constants --
TR_CREATE_SQL = (
    "SELECT * FROM content.slaif_content_item_translation_create($1,$2,$3,$4)"
)
TR_EXACT_SQL = (
    "SELECT * FROM content.content_item_translation WHERE site_id=$1 "
    "AND item_id=$2 AND locale=$3 ORDER BY id DESC LIMIT 1"
)
TR_LIST_SQL = "SELECT * FROM content.slaif_content_item_translation_list($1,$2)"
TR_GET_SQL = "SELECT * FROM content.slaif_content_item_translation_get($1,$2)"
TR_UPDATE_SQL = (
    "SELECT * FROM content.slaif_content_item_translation_update($1,$2,$3,$4,$5)"
)
TR_DELETE_SQL = "SELECT content.slaif_content_item_translation_delete($1,$2,$3)"
REL_CREATE_SQL = "SELECT * FROM content.slaif_item_relation_create($1,$2,$3,$4,$5,$6)"
REL_EXACT_SQL = (
    "SELECT * FROM content.item_relation WHERE site_id=$1 AND source_item_id=$2 "
    "AND field_definition_id=$3 AND target_item_id=$4 AND position=$5 "
    "ORDER BY id DESC LIMIT 1"
)
REL_LIST_SQL = "SELECT * FROM content.slaif_item_relation_list($1,$2)"
REL_GET_SQL = "SELECT * FROM content.slaif_item_relation_get($1,$2)"
REL_UPDATE_SQL = "SELECT * FROM content.slaif_item_relation_update($1,$2,$3,$4,$5,$6)"
REL_DELETE_SQL = "SELECT content.slaif_item_relation_delete($1,$2,$3)"


def _tr(row: Any) -> TranslationRecord:
    return TranslationRecord(
        id=row[0],
        site_id=row[1],
        item_id=row[2],
        locale=row[3],
        localized_values=json.loads(row[4]) if isinstance(row[4], str) else row[4],
        row_version=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def _rel(row: Any) -> RelationRecord:
    return RelationRecord(
        id=row[0],
        site_id=row[1],
        source_item_id=row[2],
        field_definition_id=row[3],
        target_item_id=row[4],
        position=row[5],
        metadata=json.loads(row[6]) if isinstance(row[6], str) else row[6],
        row_version=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


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


CV2_CREATE_SQL = (
    "SELECT * FROM content.slaif_collection_view_v2_create($1,$2,$3,$4,$5,$6,$7,$8)"
)
CV2_LIST_SQL = "SELECT * FROM content.slaif_collection_view_v2_list($1,$2)"
CV2_GET_SQL = "SELECT * FROM content.slaif_collection_view_v2_get($1,$2)"
CV2_UPDATE_SQL = (
    "SELECT * FROM content.slaif_collection_view_v2_update($1,$2,$3,$4,$5,$6,$7)"
)
CV2_DELETE_SQL = "SELECT content.slaif_collection_view_v2_delete($1,$2,$3)"


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
        definition_version=row[10] if len(row) > 10 else 1,
        row_version=row[11] if len(row) > 11 else 1,
    )


NV_CREATE_SQL = "SELECT * FROM content.slaif_navigation_create($1,$2,$3,$4)"
NV_LIST_SQL = "SELECT * FROM content.slaif_navigation_list($1)"
NV_GET_SQL = "SELECT * FROM content.slaif_navigation_get($1)"
NV_UPDATE_SQL = "SELECT * FROM content.slaif_navigation_update($1,$2,$3)"
NV_DELETE_SQL = "SELECT content.slaif_navigation_delete($1)"
TH_GET_SQL = "SELECT * FROM content.slaif_theme_get($1)"
TH_UPDATE_SQL = "SELECT * FROM content.slaif_theme_update($1,$2,$3,$4,$5)"

LOCALE_CREATE_SQL = "SELECT * FROM content.slaif_locale_create($1,$2,$3,$4,$5,$6)"
LOCALE_LIST_SQL = "SELECT * FROM content.slaif_locale_list($1)"
LOCALE_GET_SQL = "SELECT * FROM content.slaif_locale_get($1,$2)"
LOCALE_EXACT_SQL = (
    "SELECT * FROM content.site_locale WHERE site_id=$1 AND tag=$2 "
    "ORDER BY id DESC LIMIT 1"
)
LOCALE_UPDATE_SQL = "SELECT * FROM content.slaif_locale_update($1,$2,$3,$4,$5,$6,$7,$8)"
LOCALE_DELETE_SQL = "SELECT content.slaif_locale_delete($1,$2,$3)"
NAV_ITEM_CREATE_SQL = (
    "SELECT * FROM content.slaif_navigation_item_create($1,$2,$3,$4,$5,$6,$7,$8,$9)"
)
NAV_ITEM_LIST_SQL = "SELECT * FROM content.slaif_navigation_item_list($1,$2)"
NAV_ITEM_GET_SQL = "SELECT * FROM content.slaif_navigation_item_get($1,$2)"
NAV_ITEM_EXACT_SQL = (
    "SELECT * FROM content.navigation_item WHERE site_id=$1 AND navigation_id=$2 "
    "AND parent_id IS NOT DISTINCT FROM $3 AND target_kind=$4 "
    "AND target_value=$5 AND position=$6 ORDER BY id DESC LIMIT 1"
)
NAV_ITEM_UPDATE_SQL = (
    "SELECT * FROM content.slaif_navigation_item_update($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)"
)
NAV_ITEM_DELETE_SQL = "SELECT content.slaif_navigation_item_delete($1,$2,$3)"
REDIRECT_CREATE_SQL = "SELECT * FROM content.slaif_redirect_create($1,$2,$3,$4,$5)"
REDIRECT_LIST_SQL = "SELECT * FROM content.slaif_redirect_list($1)"
REDIRECT_GET_SQL = "SELECT * FROM content.slaif_redirect_get($1,$2)"
REDIRECT_EXACT_SQL = (
    "SELECT * FROM content.redirect WHERE site_id=$1 AND source_route=$2 "
    "AND locale IS NOT DISTINCT FROM $3 ORDER BY id DESC LIMIT 1"
)
REDIRECT_UPDATE_SQL = (
    "SELECT * FROM content.slaif_redirect_update($1,$2,$3,$4,$5,$6,$7)"
)
REDIRECT_DELETE_SQL = "SELECT content.slaif_redirect_delete($1,$2,$3)"
EFFECT_CREATE_SQL = (
    "SELECT * FROM content.slaif_proposed_side_effect_create($1,$2,$3,$4)"
)
EFFECT_LIST_SQL = "SELECT * FROM content.slaif_proposed_side_effect_list($1,$2)"


def _locale(row: Any) -> LocaleRecord:
    return LocaleRecord(
        id=row[0],
        site_id=row[1],
        tag=row[2],
        enabled=row[3],
        is_default=row[4],
        position=row[5],
        metadata=json.loads(row[6]) if isinstance(row[6], str) else row[6],
        row_version=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


def _nav_item(row: Any) -> NavigationItemRecord:
    return NavigationItemRecord(
        id=row[0],
        site_id=row[1],
        navigation_id=row[2],
        parent_id=row[3],
        page_id=row[4],
        target_kind=row[5],
        target_value=row[6],
        labels=json.loads(row[7]) if isinstance(row[7], str) else row[7],
        locale=row[8],
        position=row[9],
        row_version=row[10],
        created_at=row[11],
        updated_at=row[12],
    )


def _redirect(row: Any) -> RedirectRecord:
    return RedirectRecord(
        id=row[0],
        site_id=row[1],
        source_route=row[2],
        target=row[3],
        status_code=row[4],
        locale=row[5],
        row_version=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def _effect(row: Any) -> ProposedSideEffectRecord:
    return ProposedSideEffectRecord(
        id=row[0],
        site_id=row[1],
        workspace_id=row[2],
        kind=row[3],
        payload=json.loads(row[4]) if isinstance(row[4], str) else row[4],
        state=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def _nv(row: Any) -> Any:
    import json

    from .nav_models import NavigationRecord

    return NavigationRecord(
        id=row[0],
        site_id=row[1],
        key=row[2],
        label=row[3],
        settings=json.loads(row[4]) if isinstance(row[4], str) else row[4],
        created_at=row[5],
        updated_at=row[6],
    )


def _th(row: Any) -> Any:
    import json

    from .nav_models import ThemeRecord

    return ThemeRecord(
        id=row[0],
        site_id=row[1],
        palette=json.loads(row[2]) if isinstance(row[2], str) else row[2],
        typography=json.loads(row[3]) if isinstance(row[3], str) else row[3],
        layout=json.loads(row[4]) if isinstance(row[4], str) else row[4],
        shape=json.loads(row[5]) if isinstance(row[5], str) else row[5],
        created_at=row[6],
        updated_at=row[7],
    )


PG_CREATE_SQL = "SELECT * FROM content.slaif_page_create($1,$2,$3,$4,$5)"
PG_LIST_SQL = "SELECT * FROM content.slaif_page_list($1)"
PG_GET_SQL = "SELECT * FROM content.slaif_page_get($1)"
PG_UPDATE_SQL = "SELECT * FROM content.slaif_page_update($1,$2,$3,$4,$5)"
PG_DELETE_SQL = "SELECT content.slaif_page_delete($1)"


def _pg(row: Any) -> Any:
    from .page_models import PageRecord

    return PageRecord(
        id=row[0],
        site_id=row[1],
        slug=row[2],
        title=row[3],
        status=row[4],
        locale=row[5],
        parent_id=row[6],
        row_version=row[7],
        created_at=row[8],
        updated_at=row[9],
    )


CMP_ADD_SQL = "SELECT * FROM content.slaif_composition_node_add($1,$2,$3,$4,$5,$6,$7)"
CMP_UPDATE_SQL = "SELECT * FROM content.slaif_composition_node_update($1,$2,$3,$4)"
CMP_MOVE_SQL = "SELECT * FROM content.slaif_composition_node_move($1,$2,$3,$4)"
CMP_DELETE_SQL = "SELECT content.slaif_composition_node_delete($1)"
CMP_LIST_SQL = "SELECT * FROM content.slaif_composition_list($1)"


def _cmp(row: Any) -> Any:
    import json

    from .composition_models import CompositionNodeRecord

    return CompositionNodeRecord(
        id=row[0],
        site_id=row[1],
        page_id=row[2],
        component_type=row[3],
        schema_version=row[4],
        parent_id=row[5],
        slot_key=row[6],
        order_key=row[7],
        props=json.loads(row[8]) if isinstance(row[8], str) else row[8],
        created_at=row[9],
        updated_at=row[10],
    )


MD_CREATE_SQL = "SELECT * FROM content.slaif_media_create($1,$2,$3,$4,$5,$6,$7,$8,$9)"
MD_LIST_SQL = "SELECT * FROM content.slaif_media_list($1)"
MD_GET_SQL = "SELECT * FROM content.slaif_media_get($1)"
MD_UPDATE_SQL = "SELECT * FROM content.slaif_media_update($1,$2,$3)"
MD_DELETE_SQL = "SELECT content.slaif_media_delete($1)"


def _md(row: Any) -> Any:
    import json

    from .media_models import MediaAssetRecord

    return MediaAssetRecord(
        id=row[0],
        site_id=row[1],
        uploaded_by=row[2],
        filename=row[3],
        mime_type=row[4],
        size_bytes=row[5],
        content_hash=row[6],
        storage_key=row[7],
        alt_text=row[8],
        metadata=json.loads(row[9]) if isinstance(row[9], str) else row[9],
        created_at=row[10],
        updated_at=row[11],
    )

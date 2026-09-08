"""Capability-bound Agent semantic reads in one request-scoped COW session.

Agent reads deliberately do not use the ordinary application content service.
The authenticated capability selects the workspace, the foundation owns the
request transaction/context, and narrow Agent read wrappers own the database
site/resource boundary.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, cast
from uuid import UUID

import asyncpg

from slaif_agent_site.agent_api.models import AgentCapabilityContext
from slaif_agent_site.agent_state.foundation import CowSession, asyncpg_cow_session
from slaif_agent_site.content_model.composition_models import CompositionNodeRecord
from slaif_agent_site.content_model.item_models import ContentItemRecord
from slaif_agent_site.content_model.media_models import MediaAssetRecord
from slaif_agent_site.content_model.models import (
    ContentTypeRecord,
    FieldDefinitionRecord,
    RelationRecord,
    TranslationRecord,
)
from slaif_agent_site.content_model.page_models import PageRecord
from slaif_agent_site.content_model.service import (
    ContentModelServiceError,
    ContentModelServiceReason,
    _agent_nav,
    _ci,
    _cmp,
    _ct,
    _cv,
    _fd,
    _locale,
    _md,
    _nav_item,
    _pg,
    _redirect,
    _rel,
    _tr,
)
from slaif_agent_site.content_model.site_data_models import (
    AgentNavigationRecord,
    LocaleRecord,
    NavigationItemRecord,
    RedirectRecord,
)
from slaif_agent_site.content_model.view_models import CollectionViewRecord

AGENT_CONTENT_TYPE_LIST_SQL = "SELECT * FROM content.slaif_agent_content_type_list($1)"
AGENT_CONTENT_TYPE_GET_SQL = "SELECT * FROM content.slaif_agent_content_type_get($1,$2)"
AGENT_FIELD_DEFINITION_LIST_SQL = (
    "SELECT * FROM content.slaif_agent_field_definition_list($1,$2)"
)
AGENT_CONTENT_ITEM_LIST_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_list($1,$2)"
)
AGENT_CONTENT_ITEM_GET_SQL = "SELECT * FROM content.slaif_agent_content_item_get($1,$2)"
AGENT_TRANSLATION_LIST_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_translation_list($1,$2)"
)
AGENT_TRANSLATION_GET_SQL = (
    "SELECT * FROM content.slaif_agent_content_item_translation_get($1,$2,$3)"
)
AGENT_RELATION_LIST_SQL = "SELECT * FROM content.slaif_agent_item_relation_list($1,$2)"
AGENT_RELATION_GET_SQL = "SELECT * FROM content.slaif_agent_item_relation_get($1,$2,$3)"
AGENT_COLLECTION_VIEW_LIST_SQL = (
    "SELECT * FROM content.slaif_agent_collection_view_list($1,$2)"
)
AGENT_COLLECTION_VIEW_GET_SQL = (
    "SELECT * FROM content.slaif_agent_collection_view_get($1,$2)"
)
AGENT_PAGE_LIST_SQL = "SELECT * FROM content.slaif_agent_page_list($1)"
AGENT_PAGE_GET_SQL = "SELECT * FROM content.slaif_agent_page_get($1,$2)"
AGENT_COMPOSITION_LIST_SQL = "SELECT * FROM content.slaif_agent_composition_list($1,$2)"
AGENT_MEDIA_LIST_SQL = "SELECT * FROM content.slaif_agent_media_list($1)"
AGENT_LOCALE_LIST_SQL = "SELECT * FROM content.slaif_agent_locale_list($1)"
AGENT_LOCALE_GET_SQL = "SELECT * FROM content.slaif_agent_locale_get($1,$2)"
AGENT_NAVIGATION_LIST_SQL = "SELECT * FROM content.slaif_agent_navigation_list($1)"
AGENT_NAVIGATION_GET_SQL = "SELECT * FROM content.slaif_agent_navigation_get($1,$2)"
AGENT_NAVIGATION_ITEM_LIST_SQL = (
    "SELECT * FROM content.slaif_agent_navigation_item_list($1,$2)"
)
AGENT_NAVIGATION_ITEM_GET_SQL = (
    "SELECT * FROM content.slaif_agent_navigation_item_get($1,$2)"
)
AGENT_REDIRECT_LIST_SQL = "SELECT * FROM content.slaif_agent_redirect_list($1)"
AGENT_REDIRECT_GET_SQL = "SELECT * FROM content.slaif_agent_redirect_get($1,$2)"

AgentRead = Callable[["AgentSemanticReadService"], Awaitable[Any]]


class AgentSemanticReadService:
    """Run only the narrow Agent read wrappers on an existing COW session."""

    def __init__(self, cow_session: CowSession) -> None:
        self._cow_session = cow_session

    async def _fetch(self, sql: str, *arguments: object) -> list[Any]:
        try:
            await self._cow_session.validate_context()
            return list(await self._cow_session.native.fetch(sql, *arguments))
        except asyncio.CancelledError:
            raise
        except asyncpg.PostgresError as error:
            if getattr(error, "sqlstate", None) == "P0002":
                raise ContentModelServiceError(
                    ContentModelServiceReason.NOT_FOUND
                ) from None
            if getattr(error, "sqlstate", None) == "P0003":
                raise ContentModelServiceError(
                    ContentModelServiceReason.VALIDATION
                ) from None
            if getattr(error, "sqlstate", None) in {"P0004", "P0005", "P0006"}:
                raise ContentModelServiceError(
                    ContentModelServiceReason.CONFLICT
                    if getattr(error, "sqlstate", None) == "P0004"
                    else ContentModelServiceReason.QUOTA
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

    async def _fetchrow(self, sql: str, *arguments: object) -> Any:
        try:
            await self._cow_session.validate_context()
            return await self._cow_session.native.fetchrow(sql, *arguments)
        except asyncio.CancelledError:
            raise
        except asyncpg.PostgresError as error:
            if getattr(error, "sqlstate", None) == "P0002":
                raise ContentModelServiceError(
                    ContentModelServiceReason.NOT_FOUND
                ) from None
            if getattr(error, "sqlstate", None) == "P0003":
                raise ContentModelServiceError(
                    ContentModelServiceReason.VALIDATION
                ) from None
            if getattr(error, "sqlstate", None) in {"P0004", "P0005", "P0006"}:
                raise ContentModelServiceError(
                    ContentModelServiceReason.CONFLICT
                    if getattr(error, "sqlstate", None) == "P0004"
                    else ContentModelServiceReason.QUOTA
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

    async def list_types(self, site_id: UUID) -> tuple[ContentTypeRecord, ...]:
        rows = await self._fetch(AGENT_CONTENT_TYPE_LIST_SQL, site_id)
        return tuple(_ct(row) for row in rows)

    async def get_type(self, site_id: UUID, type_id: UUID) -> ContentTypeRecord:
        row = await self._fetchrow(AGENT_CONTENT_TYPE_GET_SQL, site_id, type_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _ct(row)

    async def list_fields(
        self, site_id: UUID, type_id: UUID
    ) -> tuple[FieldDefinitionRecord, ...]:
        rows = await self._fetch(AGENT_FIELD_DEFINITION_LIST_SQL, site_id, type_id)
        return tuple(_fd(row) for row in rows)

    async def get_field(
        self, site_id: UUID, type_id: UUID, field_id: UUID
    ) -> FieldDefinitionRecord:
        for field in await self.list_fields(site_id, type_id):
            if field.id == field_id:
                return field
        raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)

    async def get_item(self, site_id: UUID, item_id: UUID) -> ContentItemRecord:
        row = await self._fetchrow(AGENT_CONTENT_ITEM_GET_SQL, site_id, item_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return cast(ContentItemRecord, _ci(row))

    async def list_items(
        self, site_id: UUID, type_id: UUID
    ) -> tuple[ContentItemRecord, ...]:
        rows = await self._fetch(AGENT_CONTENT_ITEM_LIST_SQL, site_id, type_id)
        return tuple(_ci(row) for row in rows)

    async def list_translations_for_site(
        self, site_id: UUID, item_id: UUID
    ) -> tuple[TranslationRecord, ...]:
        rows = await self._fetch(AGENT_TRANSLATION_LIST_SQL, site_id, item_id)
        return tuple(_tr(row) for row in rows)

    async def get_translation_for_site(
        self, site_id: UUID, item_id: UUID, translation_id: UUID
    ) -> TranslationRecord:
        row = await self._fetchrow(
            AGENT_TRANSLATION_GET_SQL, site_id, item_id, translation_id
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _tr(row)

    async def list_relations_for_site(
        self, site_id: UUID, source_item_id: UUID
    ) -> tuple[RelationRecord, ...]:
        rows = await self._fetch(AGENT_RELATION_LIST_SQL, site_id, source_item_id)
        return tuple(_rel(row) for row in rows)

    async def get_relation_for_site(
        self, site_id: UUID, source_item_id: UUID, relation_id: UUID
    ) -> RelationRecord:
        row = await self._fetchrow(
            AGENT_RELATION_GET_SQL, site_id, source_item_id, relation_id
        )
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _rel(row)

    async def list_views_for_site(
        self, site_id: UUID, type_id: UUID
    ) -> tuple[CollectionViewRecord, ...]:
        rows = await self._fetch(AGENT_COLLECTION_VIEW_LIST_SQL, site_id, type_id)
        return tuple(_cv(row) for row in rows)

    async def get_view_for_site(
        self, site_id: UUID, view_id: UUID
    ) -> CollectionViewRecord:
        row = await self._fetchrow(AGENT_COLLECTION_VIEW_GET_SQL, site_id, view_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return cast(CollectionViewRecord, _cv(row))

    async def list_pages(self, site_id: UUID) -> tuple[PageRecord, ...]:
        rows = await self._fetch(AGENT_PAGE_LIST_SQL, site_id)
        return tuple(_pg(row) for row in rows)

    async def get_page(self, site_id: UUID, page_id: UUID) -> PageRecord:
        row = await self._fetchrow(AGENT_PAGE_GET_SQL, site_id, page_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return cast(PageRecord, _pg(row))

    async def list_redirects_for_site(
        self, site_id: UUID
    ) -> tuple[RedirectRecord, ...]:
        rows = await self._fetch(AGENT_REDIRECT_LIST_SQL, site_id)
        return tuple(_redirect(row) for row in rows)

    async def get_redirect_for_site(
        self, site_id: UUID, redirect_id: UUID
    ) -> RedirectRecord:
        row = await self._fetchrow(AGENT_REDIRECT_GET_SQL, site_id, redirect_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _redirect(row)

    async def list_composition(
        self, site_id: UUID, page_id: UUID
    ) -> tuple[CompositionNodeRecord, ...]:
        rows = await self._fetch(AGENT_COMPOSITION_LIST_SQL, site_id, page_id)
        return tuple(_cmp(row) for row in rows)

    async def list_media(self, site_id: UUID) -> tuple[MediaAssetRecord, ...]:
        rows = await self._fetch(AGENT_MEDIA_LIST_SQL, site_id)
        return tuple(_md(row) for row in rows)

    async def list_locales(self, site_id: UUID) -> tuple[LocaleRecord, ...]:
        rows = await self._fetch(AGENT_LOCALE_LIST_SQL, site_id)
        return tuple(_locale(row) for row in rows)

    async def get_locale(self, site_id: UUID, locale_id: UUID) -> LocaleRecord:
        row = await self._fetchrow(AGENT_LOCALE_GET_SQL, site_id, locale_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _locale(row)

    async def list_navigation(self, site_id: UUID) -> tuple[AgentNavigationRecord, ...]:
        rows = await self._fetch(AGENT_NAVIGATION_LIST_SQL, site_id)
        return tuple(_agent_nav(row) for row in rows)

    async def get_navigation(
        self, site_id: UUID, navigation_id: UUID
    ) -> AgentNavigationRecord:
        row = await self._fetchrow(AGENT_NAVIGATION_GET_SQL, site_id, navigation_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _agent_nav(row)

    async def list_navigation_items(
        self, site_id: UUID, navigation_id: UUID
    ) -> tuple[NavigationItemRecord, ...]:
        rows = await self._fetch(AGENT_NAVIGATION_ITEM_LIST_SQL, site_id, navigation_id)
        return tuple(_nav_item(row) for row in rows)

    async def get_navigation_item(
        self, site_id: UUID, item_id: UUID
    ) -> NavigationItemRecord:
        row = await self._fetchrow(AGENT_NAVIGATION_ITEM_GET_SQL, site_id, item_id)
        if row is None:
            raise ContentModelServiceError(ContentModelServiceReason.NOT_FOUND)
        return _nav_item(row)


async def execute_agent_read(
    *,
    database: Any,
    context: AgentCapabilityContext,
    read: AgentRead,
) -> Any:
    """Execute one read on the Agent pool without durable mutation state."""

    try:
        pool = database.cow_pool()
        async with asyncpg_cow_session(pool, session_id=context.workspace_id) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(context.capability_id),
            )
            return await read(AgentSemanticReadService(cow))
    except asyncio.CancelledError:
        raise
    except ContentModelServiceError:
        raise
    except Exception as error:
        raise ContentModelServiceError(ContentModelServiceReason.UNAVAILABLE) from error


__all__ = ["AgentSemanticReadService", "execute_agent_read"]

"""Fixed-login production wiring and public Editor HTTP evidence."""

from __future__ import annotations

from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from pydantic import SecretStr
from slaif_agent_site.agent_state.foundation import get_session_operations
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import EnvironmentMode, ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.roles import quote_identifier
from slaif_agent_site.editor_api.app import create_app
from slaif_agent_site.editor_api.config import (
    EditorDatabaseMode,
    EditorDatabaseSettings,
)
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.health import ComponentStatus

CONTROL_LOGIN = "slaif_control_login"
EDITOR_LOGIN = "slaif_editor_login"
CONTROL_ROLE = "slaif_control"
EDITOR_ROLE = "slaif_editor_runtime"
CONTROL_PASSWORD = "fake-production-control-password-068-d"
EDITOR_PASSWORD = "fake-production-editor-password-068-d"


def _dsn(database: AgentSiteDatabase, login: str, password: str) -> SecretStr:
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return SecretStr(
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=_dsn(database, CONTROL_LOGIN, CONTROL_PASSWORD),
        dsn_file=None,
        expected_database=database.name,
        expected_login=CONTROL_LOGIN,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-production-control-http-test",
    )


def _editor_settings(database: AgentSiteDatabase) -> EditorDatabaseSettings:
    return EditorDatabaseSettings(
        mode=EditorDatabaseMode.TEST,
        dsn=_dsn(database, EDITOR_LOGIN, EDITOR_PASSWORD),
        dsn_file=None,
        expected_database=database.name,
        expected_login=EDITOR_LOGIN,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-production-editor-http-test",
    )


def _cookie(session: str, csrf: str | None = None) -> str:
    value = f"slaif_session={session}"
    return value if csrf is None else f"{value}; slaif_csrf={csrf}"


def _assert_private(response: httpx.Response) -> None:
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-robots-tag"] == "noindex, nofollow, noarchive"
    assert len(response.headers.get_list("x-request-id")) == 1


def _mutation_headers(session: str, csrf: str, key: str) -> dict[str, str]:
    return {
        "cookie": _cookie(session, csrf),
        "x-csrf-token": csrf,
        "idempotency-key": key,
    }


@pytest.mark.asyncio
async def test_fixed_production_logins_run_public_editor_http_chain(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    owner_pool = await database.role_pool("slaif_owner")
    site_id = uuid4()
    human_id = uuid4()
    canonical_id = uuid4()
    site_key = f"production-editor-{uuid4().hex[:12]}"
    fixed_logins = (
        (CONTROL_LOGIN, CONTROL_PASSWORD, CONTROL_ROLE),
        (EDITOR_LOGIN, EDITOR_PASSWORD, EDITOR_ROLE),
    )
    control: ControlDatabase | None = None
    editor: EditorDatabase | None = None

    try:
        async with owner_pool.acquire() as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://production-editor.test', $2, "
                "'Production Editor Human')",
                human_id,
                str(human_id),
            )
            await owner.execute(
                "INSERT INTO control.platform_administrator (user_account_id) "
                "VALUES ($1)",
                human_id,
            )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) VALUES ($1, $2, 'Production Editor', "
                "'en', 'catalog-v1')",
                site_id,
                site_key,
            )
            await owner.execute(
                "INSERT INTO content.page "
                "(id, site_id, slug, title, status, locale) "
                "VALUES ($1, $2, 'canonical', 'Canonical title', 'DRAFT', 'en')",
                canonical_id,
                site_id,
            )
        await reconcile(database.settings)

        for login, password, role in fixed_logins:
            password_literal = await database.administrator.fetchval(
                "SELECT pg_catalog.quote_literal($1::text)", password
            )
            await database.administrator.execute(
                f"CREATE ROLE {quote_identifier(login)} LOGIN PASSWORD "
                f"{password_literal} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT "
                "NOREPLICATION NOBYPASSRLS"
            )
            await database.administrator.execute(
                f"GRANT {quote_identifier(role)} TO {quote_identifier(login)}"
            )

        for login, password, role in fixed_logins:
            connection = await asyncpg.connect(
                host=database.connection_parameters["host"],
                port=database.connection_parameters["port"],
                database=database.name,
                user=login,
                password=password,
            )
            try:
                identity = await connection.fetchrow(
                    "SELECT session_user::text, current_user::text, "
                    "pg_has_role(session_user, $1, 'MEMBER')",
                    role,
                )
                assert tuple(identity) == (login, login, True)
                if login == CONTROL_LOGIN:
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetchval("SELECT count(*) FROM content.page")
                else:
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await connection.fetchval(
                            "SELECT count(*) FROM control.workspace"
                        )
            finally:
                await connection.close()

        control = ControlDatabase(_control_settings(database))
        editor = EditorDatabase(_editor_settings(database))
        app = create_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )

        async with app.router.lifespan_context(app):
            assert (await control.readiness()).status is ComponentStatus.OK
            assert (await editor.readiness()).status is ComponentStatus.OK
            issued = await control.human_session_service().create(human_id)
            session = issued.token.get_secret_value()
            csrf = issued.csrf_token.get_secret_value()
            pages_path = f"/api/editor/v1/sites/{site_id}/pages/"
            composition_path = (
                f"/api/editor/v1/sites/{site_id}/pages/{{page_id}}/composition/"
            )
            read_headers = {"cookie": _cookie(session, csrf)}

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://public-editor.test",
            ) as client:
                initial = await client.get(pages_path, headers=read_headers)
                assert initial.status_code == 200
                _assert_private(initial)
                assert [row["slug"] for row in initial.json()] == ["canonical"]

                canonical_update = await client.patch(
                    f"{pages_path}{canonical_id}",
                    headers=_mutation_headers(session, csrf, "canonical-update"),
                    json={
                        "title": "Overlay canonical title",
                        "expected_row_version": 1,
                    },
                )
                assert canonical_update.status_code == 200
                _assert_private(canonical_update)
                assert canonical_update.json()["title"] == "Overlay canonical title"
                canonical_read = await client.get(
                    f"{pages_path}{canonical_id}", headers=read_headers
                )
                assert canonical_read.status_code == 200
                assert canonical_read.json()["title"] == "Overlay canonical title"

                created = await client.post(
                    pages_path,
                    headers=_mutation_headers(session, csrf, "overlay-create"),
                    json={
                        "slug": "overlay",
                        "title": "Overlay page",
                        "status": "DRAFT",
                        "locale": "en",
                    },
                )
                assert created.status_code == 201
                _assert_private(created)
                overlay_id = UUID(created.json()["id"])
                replay = await client.post(
                    pages_path,
                    headers=_mutation_headers(session, csrf, "overlay-create"),
                    json={
                        "slug": "overlay",
                        "title": "Overlay page",
                        "status": "DRAFT",
                        "locale": "en",
                    },
                )
                assert replay.status_code == 201
                assert replay.json() == created.json()
                mismatch = await client.post(
                    pages_path,
                    headers=_mutation_headers(session, csrf, "overlay-create"),
                    json={
                        "slug": "different",
                        "title": "Mismatch",
                        "status": "DRAFT",
                        "locale": "en",
                    },
                )
                assert mismatch.status_code == 409

                listed = await client.get(pages_path, headers=read_headers)
                assert {row["slug"] for row in listed.json()} == {
                    "canonical",
                    "overlay",
                }
                composition = composition_path.format(page_id=overlay_id)
                first = await client.post(
                    f"{composition}components",
                    headers=_mutation_headers(session, csrf, "component-one"),
                    json={"component_type": "Section", "order_key": 0, "props": {}},
                )
                assert first.status_code == 201
                first_id = UUID(first.json()["id"])
                second = await client.post(
                    f"{composition}components",
                    headers=_mutation_headers(session, csrf, "component-two"),
                    json={"component_type": "Section", "order_key": 0, "props": {}},
                )
                assert second.status_code == 201
                second_id = UUID(second.json()["id"])
                update = await client.patch(
                    f"{composition}components/{first_id}",
                    headers=_mutation_headers(session, csrf, "component-update"),
                    json={"props": {"variant": "narrow"}},
                )
                assert update.status_code == 200
                moved = await client.post(
                    f"{composition}components/{first_id}/move",
                    headers=_mutation_headers(session, csrf, "component-move"),
                    json={
                        "new_parent_id": None,
                        "new_slot_key": "default",
                        "new_order_key": 1,
                    },
                )
                assert moved.status_code == 200
                composition_read = await client.get(composition, headers=read_headers)
                assert composition_read.status_code == 200
                nodes = {UUID(row["id"]): row for row in composition_read.json()}
                assert nodes[first_id]["order_key"] == 1
                assert nodes[first_id]["props"] == {"variant": "narrow"}
                assert nodes[second_id]["order_key"] == 0

                delete_second = await client.delete(
                    f"{composition}components/{second_id}",
                    headers=_mutation_headers(session, csrf, "component-delete-two"),
                )
                assert delete_second.status_code == 204
                delete_first = await client.delete(
                    f"{composition}components/{first_id}",
                    headers=_mutation_headers(session, csrf, "component-delete-one"),
                )
                assert delete_first.status_code == 204
                delete_page = await client.delete(
                    f"{pages_path}{overlay_id}",
                    headers=_mutation_headers(session, csrf, "overlay-delete"),
                )
                assert delete_page.status_code == 204
                final = await client.get(pages_path, headers=read_headers)
                assert [row["slug"] for row in final.json()] == ["canonical"]
                assert final.json()[0]["title"] == "Overlay canonical title"

                before_get = await client.get(pages_path, headers=read_headers)
                assert before_get.status_code == 200
                after_get = await client.get(pages_path, headers=read_headers)
                assert after_get.status_code == 200
                assert after_get.json() == before_get.json()

        async with owner_pool.acquire() as owner:
            canonical = await owner.fetchrow(
                "SELECT id, slug, title FROM content.page WHERE id = $1",
                canonical_id,
            )
            assert tuple(canonical) == (canonical_id, "canonical", "Canonical title")
            counts = await owner.fetchrow(
                "SELECT (SELECT count(*) FROM control.human_editor_idempotency), "
                "(SELECT count(*) FROM audit.human_editor_mutation), "
                "(SELECT count(*) FROM control.human_editor_idempotency "
                "WHERE status_code IS NULL), "
                "(SELECT count(*) FROM audit.human_editor_mutation "
                "WHERE response_status NOT BETWEEN 200 AND 299)"
            )
            assert tuple(counts) == (9, 9, 0, 0)
            operations = await get_session_operations(
                AsyncpgExecutor(owner),
                await owner.fetchval(
                    "SELECT id FROM control.workspace WHERE site_id = $1 "
                    "AND created_by = $2 ORDER BY created_at DESC, id DESC LIMIT 1",
                    site_id,
                    human_id,
                ),
                schema="content",
            )
            assert len(operations) == 9

            grants = await owner.fetch(
                "SELECT rolname::text, "
                "has_schema_privilege(rolname, 'content', 'USAGE'), "
                "has_table_privilege(rolname, 'content.page_base', 'SELECT') "
                "FROM pg_roles WHERE rolname IN ($1, $2) ORDER BY rolname",
                CONTROL_LOGIN,
                EDITOR_LOGIN,
            )
            assert [tuple(row) for row in grants] == [
                (CONTROL_LOGIN, False, False),
                (EDITOR_LOGIN, True, False),
            ]
    finally:
        await owner_pool.close()
        for login, _, role in fixed_logins:
            await database.administrator.execute(
                f"REVOKE {quote_identifier(role)} FROM {quote_identifier(login)}"
            )
            await database.administrator.execute(
                f"DROP ROLE IF EXISTS {quote_identifier(login)}"
            )


@pytest.mark.asyncio
async def test_editor_http_translations_relations_are_versioned_and_site_confined(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Exercise the new substrate through authenticated public Editor routes."""
    database = agent_site_database
    await upgrade(database.settings)
    owner_pool = await database.role_pool("slaif_owner")
    site_id, human_id = uuid4(), uuid4()
    site_key = f"domain-proof-{uuid4().hex[:12]}"
    fixed_logins = (
        (CONTROL_LOGIN, CONTROL_PASSWORD, CONTROL_ROLE),
        (EDITOR_LOGIN, EDITOR_PASSWORD, EDITOR_ROLE),
    )
    editor: EditorDatabase | None = None
    try:
        async with owner_pool.acquire() as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://domain-proof.test', $2, 'Domain Human')",
                human_id,
                str(human_id),
            )
            await owner.execute(
                "INSERT INTO control.platform_administrator "
                "(user_account_id) VALUES ($1)",
                human_id,
            )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, $2, 'Domain Proof', 'en', 'catalog-v1')",
                site_id,
                site_key,
            )
        await reconcile(database.settings)
        for login, password, role in fixed_logins:
            password_literal = await database.administrator.fetchval(
                "SELECT pg_catalog.quote_literal($1::text)", password
            )
            await database.administrator.execute(
                f"CREATE ROLE {quote_identifier(login)} LOGIN PASSWORD "
                f"{password_literal} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION "
                "NOBYPASSRLS"
            )
            await database.administrator.execute(
                f"GRANT {quote_identifier(role)} TO {quote_identifier(login)}"
            )
        control = ControlDatabase(_control_settings(database))
        editor = EditorDatabase(_editor_settings(database))
        app = create_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )
        async with app.router.lifespan_context(app):
            issued = await control.human_session_service().create(human_id)
            session = issued.token.get_secret_value()
            csrf = issued.csrf_token.get_secret_value()
            root = f"/api/editor/v1/sites/{site_id}"
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://domain-proof.test",
            ) as client:
                read = {"cookie": _cookie(session, csrf)}

                def mutation(key: str) -> dict[str, str]:
                    return _mutation_headers(session, csrf, key)

                type_response = await client.post(
                    f"{root}/content-model/types",
                    headers=mutation("domain-type"),
                    json={
                        "key": "article",
                        "labels": {"en": "Article"},
                        "slug_pattern": "/article/{slug}",
                        "settings": {},
                    },
                )
                assert type_response.status_code == 201, type_response.text
                type_id = type_response.json()["id"]
                localized = await client.post(
                    f"{root}/content-model/types/{type_id}/fields",
                    headers=mutation("domain-title"),
                    json={
                        "key": "title",
                        "label": "Title",
                        "field_type": "short_text",
                        "localized": True,
                    },
                )
                assert localized.status_code == 201, localized.text
                relation_field = await client.post(
                    f"{root}/content-model/types/{type_id}/fields",
                    headers=mutation("domain-related"),
                    json={
                        "key": "related",
                        "label": "Related",
                        "field_type": "reference",
                    },
                )
                assert relation_field.status_code == 201, relation_field.text
                field_id = relation_field.json()["id"]
                source = await client.post(
                    f"{root}/content-items/",
                    headers=mutation("domain-source"),
                    json={"type_id": type_id, "slug": "source", "values": {}},
                )
                target = await client.post(
                    f"{root}/content-items/",
                    headers=mutation("domain-target"),
                    json={"type_id": type_id, "slug": "target", "values": {}},
                )
                assert source.status_code == target.status_code == 201
                source_id, target_id = source.json()["id"], target.json()["id"]
                translation_path = f"{root}/content-items/{source_id}/translations"
                translation = await client.post(
                    translation_path,
                    headers=mutation("domain-translation"),
                    json={"locale": "en", "localized_values": {"title": "Hello"}},
                )
                assert translation.status_code == 201, translation.text
                translation_replay = await client.post(
                    translation_path,
                    headers=mutation("domain-translation"),
                    json={"locale": "en", "localized_values": {"title": "Hello"}},
                )
                assert translation_replay.status_code == 201
                assert translation_replay.json() == translation.json()
                translation_id = translation.json()["id"]
                translation_update = await client.patch(
                    f"{translation_path}/{translation_id}",
                    headers=mutation("domain-translation-update"),
                    json={
                        "localized_values": {"title": "Updated"},
                        "expected_row_version": 1,
                    },
                )
                assert translation_update.status_code == 200
                stale_translation = await client.patch(
                    f"{translation_path}/{translation_id}",
                    headers=mutation("domain-translation-stale"),
                    json={
                        "localized_values": {"title": "Stale"},
                        "expected_row_version": 1,
                    },
                )
                assert stale_translation.status_code == 409
                relation_path = f"{root}/content-items/{source_id}/relations"
                relation = await client.post(
                    relation_path,
                    headers=mutation("domain-relation"),
                    json={"field_definition_id": field_id, "target_item_id": target_id},
                )
                assert relation.status_code == 201, relation.text
                relation_id = relation.json()["id"]
                relation_update = await client.patch(
                    f"{relation_path}/{relation_id}",
                    headers=mutation("domain-relation-update"),
                    json={"metadata": {"kind": "related"}, "expected_row_version": 1},
                )
                assert relation_update.status_code == 200
                stale_relation = await client.patch(
                    f"{relation_path}/{relation_id}",
                    headers=mutation("domain-relation-stale"),
                    json={"metadata": {}, "expected_row_version": 1},
                )
                assert stale_relation.status_code == 409
                view_path = f"{root}/collection-views/types/{type_id}"
                view = await client.post(
                    view_path,
                    headers=mutation("domain-view"),
                    json={
                        "type_id": type_id,
                        "key": "published",
                        "filter_spec": {"status": "DRAFT"},
                        "sort_spec": {"field": "slug", "direction": "asc"},
                        "projection_spec": {},
                        "pagination_spec": {"limit": 10, "offset": 0},
                        "definition_version": 1,
                    },
                )
                assert view.status_code == 201, view.text
                view_id = view.json()["id"]
                view_update = await client.patch(
                    f"{root}/collection-views/{view_id}",
                    headers=mutation("domain-view-update"),
                    json={
                        "pagination_spec": {"limit": 5, "offset": 0},
                        "expected_row_version": 1,
                    },
                )
                assert view_update.status_code == 200
                stale_view = await client.patch(
                    f"{root}/collection-views/{view_id}",
                    headers=mutation("domain-view-stale"),
                    json={"expected_row_version": 1},
                )
                assert stale_view.status_code == 409
                assert (
                    await client.delete(
                        f"{translation_path}/{translation_id}?expected_row_version=2",
                        headers=mutation("domain-translation-delete"),
                    )
                ).status_code == 204
                assert (
                    await client.delete(
                        f"{root}/collection-views/{view_id}?expected_row_version=2",
                        headers=mutation("domain-view-delete"),
                    )
                ).status_code == 204
                assert (
                    await client.delete(
                        f"{relation_path}/{relation_id}?expected_row_version=2",
                        headers=mutation("domain-relation-delete"),
                    )
                ).status_code == 204
                assert (await client.get(translation_path, headers=read)).json() == []
                assert (await client.get(relation_path, headers=read)).json() == []
        async with owner_pool.acquire() as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_item WHERE site_id=$1 "
                    "AND slug IN ('source','target')",
                    site_id,
                )
                == 0
            )
            counts = await owner.fetchrow(
                "SELECT (SELECT count(*) FROM control.human_editor_idempotency "
                "WHERE site_id=$1), "
                "(SELECT count(*) FROM audit.human_editor_mutation WHERE site_id=$1)",
                site_id,
            )
            assert tuple(counts) == (14, 14)

    finally:
        if editor is not None:
            await editor.stop()
        await owner_pool.close()
        for login, _, role in fixed_logins:
            await database.administrator.execute(
                f"REVOKE {quote_identifier(role)} FROM {quote_identifier(login)}"
            )
            await database.administrator.execute(
                f"DROP ROLE IF EXISTS {quote_identifier(login)}"
            )


@pytest.mark.asyncio
async def test_editor_http_site_data_substrate_is_cow_and_versioned(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Exercise locales, navigation items, and redirects through public Editor HTTP."""
    database = agent_site_database
    await upgrade(database.settings)
    owner_pool = await database.role_pool("slaif_owner")
    site_id, human_id = uuid4(), uuid4()
    site_key = f"site-data-{uuid4().hex[:12]}"
    fixed_logins = (
        (CONTROL_LOGIN, CONTROL_PASSWORD, CONTROL_ROLE),
        (EDITOR_LOGIN, EDITOR_PASSWORD, EDITOR_ROLE),
    )
    editor: EditorDatabase | None = None
    try:
        async with owner_pool.acquire() as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://site-data.test', $2, 'Site Data Human')",
                human_id,
                str(human_id),
            )
            await owner.execute(
                "INSERT INTO control.platform_administrator "
                "(user_account_id) VALUES ($1)",
                human_id,
            )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, $2, 'Site Data', 'en', 'catalog-v1')",
                site_id,
                site_key,
            )
        await reconcile(database.settings)
        for login, password, role in fixed_logins:
            password_literal = await database.administrator.fetchval(
                "SELECT pg_catalog.quote_literal($1::text)", password
            )
            await database.administrator.execute(
                f"CREATE ROLE {quote_identifier(login)} LOGIN "
                f"PASSWORD {password_literal} "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION NOBYPASSRLS"
            )
            await database.administrator.execute(
                f"GRANT {quote_identifier(role)} TO {quote_identifier(login)}"
            )
        control = ControlDatabase(_control_settings(database))
        editor = EditorDatabase(_editor_settings(database))
        app = create_app(
            settings=ServiceSettings(mode=EnvironmentMode.TEST),
            database=control,
            editor_database=editor,
        )
        async with app.router.lifespan_context(app):
            issued = await control.human_session_service().create(human_id)
            session = issued.token.get_secret_value()
            csrf = issued.csrf_token.get_secret_value()
            root = f"/api/editor/v1/sites/{site_id}"
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://site-data.test"
            ) as client:

                def mutation(key: str) -> dict[str, str]:
                    return _mutation_headers(session, csrf, key)

                locales = f"{root}/locales"
                primary = await client.post(
                    locales,
                    headers=mutation("site-locale-en"),
                    json={
                        "tag": "en",
                        "is_default": True,
                        "position": 0,
                        "metadata": {},
                    },
                )
                assert primary.status_code == 201, primary.text
                primary_id = primary.json()["id"]
                secondary = await client.post(
                    locales,
                    headers=mutation("site-locale-sl"),
                    json={"tag": "sl-SI", "position": 1, "metadata": {}},
                )
                assert secondary.status_code == 201, secondary.text
                secondary_id = secondary.json()["id"]
                listed_locales = await client.get(
                    locales, headers={"cookie": _cookie(session, csrf)}
                )
                assert listed_locales.status_code == 200, listed_locales.text
                assert [row["tag"] for row in listed_locales.json()] == [
                    "en",
                    "sl-SI",
                ]
                stale_locale = await client.patch(
                    f"{locales}/{secondary_id}",
                    headers=mutation("site-locale-stale"),
                    json={
                        "tag": "de",
                        "position": 1,
                        "metadata": {},
                        "expected_row_version": 1,
                    },
                )
                assert stale_locale.status_code == 200
                assert (
                    await client.patch(
                        f"{locales}/{secondary_id}",
                        headers=mutation("site-locale-stale-2"),
                        json={
                            "tag": "fr",
                            "position": 1,
                            "metadata": {},
                            "expected_row_version": 1,
                        },
                    )
                ).status_code == 409
                assert (
                    await client.delete(
                        f"{locales}/{primary_id}?expected_row_version=1",
                        headers=mutation("site-locale-default-delete"),
                    )
                ).status_code == 422
                assert (
                    await client.delete(
                        f"{locales}/{secondary_id}?expected_row_version=2",
                        headers=mutation("site-locale-delete"),
                    )
                ).status_code == 204

                nav = await client.post(
                    f"{root}/navigation",
                    headers=mutation("site-navigation"),
                    json={"key": "main", "label": "Main", "settings": {}},
                )
                assert nav.status_code == 201, nav.text
                navigation_id = nav.json()["id"]
                items = f"{root}/navigation/{navigation_id}/items"
                parent = await client.post(
                    items,
                    headers=mutation("site-nav-parent"),
                    json={
                        "navigation_id": navigation_id,
                        "target_kind": "INTERNAL",
                        "target_value": "/home",
                        "labels": {"en": "Home"},
                        "position": 0,
                    },
                )
                assert parent.status_code == 201, parent.text
                parent_id = parent.json()["id"]
                child = await client.post(
                    items,
                    headers=mutation("site-nav-child"),
                    json={
                        "navigation_id": navigation_id,
                        "parent_id": parent_id,
                        "target_kind": "EXTERNAL",
                        "target_value": "https://example.test/news",
                        "labels": {"en": "News"},
                        "position": 1,
                    },
                )
                assert child.status_code == 201, child.text
                child_id = child.json()["id"]
                cycle = await client.post(
                    f"{root}/navigation-items/{parent_id}/move",
                    headers=mutation("site-nav-cycle"),
                    json={
                        "parent_id": child_id,
                        "position": 0,
                        "expected_row_version": 1,
                    },
                )
                assert cycle.status_code == 422, cycle.text
                moved = await client.post(
                    f"{root}/navigation-items/{child_id}/move",
                    headers=mutation("site-nav-move"),
                    json={"parent_id": None, "position": 2, "expected_row_version": 1},
                )
                assert moved.status_code == 200, moved.text
                assert (
                    len(
                        (
                            await client.get(
                                items, headers={"cookie": _cookie(session, csrf)}
                            )
                        ).json()
                    )
                    == 2
                )
                assert (
                    await client.delete(
                        f"{root}/navigation-items/{child_id}?expected_row_version=2",
                        headers=mutation("site-nav-child-delete"),
                    )
                ).status_code == 204
                assert (
                    await client.delete(
                        f"{root}/navigation-items/{parent_id}?expected_row_version=1",
                        headers=mutation("site-nav-parent-delete"),
                    )
                ).status_code == 204

                redirects = f"{root}/redirects"
                redirect = await client.post(
                    redirects,
                    headers=mutation("site-redirect"),
                    json={"source_route": "/old", "target": "/new", "status_code": 301},
                )
                assert redirect.status_code == 201, redirect.text
                redirect_id = redirect.json()["id"]
                stale_redirect = await client.patch(
                    f"{redirects}/{redirect_id}",
                    headers=mutation("site-redirect-update"),
                    json={
                        "source_route": "/old",
                        "target": "/newer",
                        "status_code": 302,
                        "expected_row_version": 1,
                    },
                )
                assert stale_redirect.status_code == 200
                assert (
                    await client.delete(
                        f"{redirects}/{redirect_id}?expected_row_version=2",
                        headers=mutation("site-redirect-delete"),
                    )
                ).status_code == 204
        async with owner_pool.acquire() as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.navigation_item WHERE site_id=$1",
                    site_id,
                )
                == 0
            )
    finally:
        if editor is not None:
            await editor.stop()
        await owner_pool.close()
        for login, _, role in fixed_logins:
            await database.administrator.execute(
                f"REVOKE {quote_identifier(role)} FROM {quote_identifier(login)}"
            )
            await database.administrator.execute(
                f"DROP ROLE IF EXISTS {quote_identifier(login)}"
            )

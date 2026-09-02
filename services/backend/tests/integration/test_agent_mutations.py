"""Real PostgreSQL proof for the bounded Agent COW mutation surface."""

from __future__ import annotations

import asyncio
import contextlib
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_reviewer,
)
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_session as _asyncpg_cow_session,
)
from slaif_agent_site.agent_state.mutations import (
    execute_agent_mutation,
    mutation_digest,
)
from slaif_agent_site.agent_state.reads import execute_agent_read
from slaif_agent_site.bootstrap.service import reconcile, status, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.content_model.models import (
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    DeleteDefinitionRequest,
    UpdateContentTypeRequest,
    UpdateFieldDefinitionRequest,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration

_TEST_CAPABILITY_BY_WORKSPACE: dict[UUID, UUID] = {}


@asynccontextmanager
async def asyncpg_cow_session(*args: Any, **kwargs: Any) -> Any:
    """Give direct wrapper proofs the same authenticated cap context as HTTP."""
    async with _asyncpg_cow_session(*args, **kwargs) as cow:
        workspace_id = kwargs.get("session_id")
        if workspace_id is not None:
            capability_id = _TEST_CAPABILITY_BY_WORKSPACE.get(UUID(str(workspace_id)))
            if capability_id is not None:
                await cow.native.execute(
                    "SELECT set_config('app.capability_id',$1,true)",
                    str(capability_id),
                )
        yield cow


def _agent_settings(database: AgentSiteDatabase) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    locator = (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="slaif-agent-mutation-test",
    )


async def _seed(database: AgentSiteDatabase) -> tuple[str, dict[str, UUID]]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        delegator_id = await owner.fetchval(
            """
            INSERT INTO control.user_account (
                id, identity_kind, local_username, local_username_normalized,
                password_hash, display_name, status
            ) VALUES (
                gen_random_uuid(), 'LOCAL', 'Agent.Mutation.Delegator',
                'agent.mutation.delegator',
                '$argon2id$v=19$m=65536,t=3,p=4$'
                'AAAAAAAAAAAAAAAAAAAAAA$'
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
                'Agent Mutation Delegator', 'ACTIVE'
            ) RETURNING id
            """
        )
        site_id = await owner.fetchval(
            """
            INSERT INTO control.site (
                site_key, display_name, default_locale, component_catalog_version
            ) VALUES ('agent-mutation', 'Agent Mutation', 'en-US', 'catalog-v1')
            RETURNING id
            """
        )
        site_b_id = await owner.fetchval(
            """
            INSERT INTO control.site (
                site_key, display_name, default_locale, component_catalog_version
            ) VALUES (
                'agent-mutation-other', 'Other Agent Mutation', 'en-US',
                'catalog-v1'
            )
            RETURNING id
            """
        )
        await owner.execute(
            "INSERT INTO control.site_membership("
            "site_id,user_account_id,role_key,delegation_ceiling) "
            "VALUES ($1,$2,'SITE_OWNER',4),($3,$2,'SITE_OWNER',4)",
            site_id,
            delegator_id,
            site_b_id,
        )
        type_b_id = uuid4()
        page_b_id = uuid4()
        await owner.execute(
            """
            INSERT INTO content.content_type_base (
                id, site_id, "key", labels, slug_pattern, status,
                definition_version, settings
            ) VALUES ($1, $2, 'other-type', '{"en":"Other"}'::jsonb,
                      '/other/{slug}', 'ACTIVE', 1, '{}'::jsonb)
            """,
            type_b_id,
            site_b_id,
        )
        await owner.execute(
            """
            INSERT INTO content.page_base (
                id, site_id, slug, title, status, locale
            ) VALUES ($1, $2, 'other-page', 'Other page', 'DRAFT', 'en')
            """,
            page_b_id,
            site_b_id,
        )
        workspace_id = await owner.fetchval(
            """
            INSERT INTO control.workspace (
                site_id, created_by, delegator_id, title, delegation_preset,
                effective_scopes, status, expires_at
            ) VALUES (
                $1, $2, $2, 'Agent Mutation Workspace', 'L4',
                '["site:read","content-model:create","field-definition:create","content-model:read",
                  "content-item:create","content-item:read","page:create",
                  "page:read","composition:read","media:read",
                  "component-structure:create"]'::jsonb,
                'ACTIVE', now() + interval '1 hour'
            ) RETURNING id
            """,
            site_id,
            delegator_id,
        )
        token, public_id, digest = generate_capability_token()
        await owner.execute(
            """
            INSERT INTO control.capability (
                workspace_id, public_id, secret_digest, scopes, expires_at
            ) VALUES ($1, $2, $3, $4::jsonb, $5)
            """,
            workspace_id,
            public_id,
            digest,
            '["site:read","content-model:create","field-definition:create","content-model:read","content-item:create","content-item:read","page:create","page:read","composition:read","media:read","component-structure:create"]',
            datetime.now(UTC) + timedelta(minutes=30),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    _TEST_CAPABILITY_BY_WORKSPACE[workspace_id] = capability_id
    return token, {
        "capability_id": capability_id,
        "delegator_id": delegator_id,
        "site_id": site_id,
        "workspace_id": workspace_id,
        "site_b_id": site_b_id,
        "type_b_id": type_b_id,
        "page_b_id": page_b_id,
    }


async def _capability_with_scopes(
    database: AgentSiteDatabase,
    seeded: dict[str, UUID],
    scopes: list[str],
) -> str:
    async with owner_connection(
        database.settings.resolved_owner_dsn(),
        expected_database=database.name,
    ) as owner:
        token, public_id, digest = generate_capability_token()
        await owner.execute(
            """
            INSERT INTO control.capability (
                workspace_id, public_id, secret_digest, scopes, expires_at
            ) VALUES ($1, $2, $3, $4::jsonb, $5)
            """,
            seeded["workspace_id"],
            public_id,
            digest,
            json.dumps(scopes),
            datetime.now(UTC) + timedelta(minutes=30),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id=$1", public_id
        )
    _TEST_CAPABILITY_BY_WORKSPACE[seeded["workspace_id"]] = capability_id
    return token


async def _workspace_capability(
    database: AgentSiteDatabase,
    seeded: dict[str, UUID],
    scopes: list[str],
    title: str,
) -> tuple[str, UUID]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        workspace_id = await owner.fetchval(
            """
            INSERT INTO control.workspace (
                site_id, created_by, delegator_id, title, delegation_preset,
                effective_scopes, status, expires_at
            ) VALUES ($1, $2, $2, $3, 'L4', $4::jsonb, 'ACTIVE',
                      now() + interval '1 hour')
            RETURNING id
            """,
            seeded["site_id"],
            seeded["delegator_id"],
            title,
            json.dumps(scopes),
        )
        token, public_id, digest = generate_capability_token()
        await owner.execute(
            """
            INSERT INTO control.capability (
                workspace_id, public_id, secret_digest, scopes, expires_at
            ) VALUES ($1, $2, $3, $4::jsonb, now() + interval '30 minutes')
            """,
            workspace_id,
            public_id,
            digest,
            json.dumps(scopes),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id=$1", public_id
        )
    _TEST_CAPABILITY_BY_WORKSPACE[workspace_id] = capability_id
    return token, workspace_id


async def _set_resource_constraints(
    database: AgentSiteDatabase,
    workspace_id: UUID,
    constraints: dict[str, Any],
) -> None:
    encoded = json.dumps(constraints, sort_keys=True)
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.workspace SET resource_constraints=$2::jsonb WHERE id=$1",
            workspace_id,
            encoded,
        )
        await owner.execute(
            "UPDATE control.capability SET resource_constraints=$2::jsonb "
            "WHERE workspace_id=$1",
            workspace_id,
            encoded,
        )


@pytest.mark.asyncio
async def test_agent_create_type_is_cow_only_and_durablely_idempotent(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    token, seeded = await _seed(database)
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    body: dict[str, Any] = {
        "key": "article",
        "labels": {"en": "Article"},
        "slug_pattern": "/articles/{slug}",
        "settings": {"editor": "bounded"},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "article-create-1",
    }
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                created = await client.post(
                    "/api/agent/v1/content-model/types",
                    json=body,
                    headers=headers,
                )
                assert created.status_code == 201, created.text
                result = created.json()
                assert UUID(result["operation_id"])
                assert result["record"]["key"] == "article"

                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    operations_before_replay = await reviewer.operations(
                        seeded["workspace_id"], schema="content"
                    )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    durable_before_replay = await owner.fetchrow(
                        "SELECT "
                        "(SELECT count(*) FROM control.agent_idempotency "
                        "WHERE capability_id = $1) "
                        "AS idempotency_count, "
                        "(SELECT count(*) FROM audit.agent_mutation "
                        "WHERE capability_id = $1) "
                        "AS audit_count",
                        seeded["capability_id"],
                    )

                replay = await client.post(
                    "/api/agent/v1/content-model/types",
                    json=body,
                    headers=headers,
                )
                assert replay.status_code == 201
                assert replay.json() == result

                mismatch = await client.post(
                    "/api/agent/v1/content-model/types",
                    json={**body, "key": "different"},
                    headers=headers,
                )
                assert mismatch.status_code == 409
                assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_MISMATCH"

                missing_key = await client.post(
                    "/api/agent/v1/content-model/types",
                    json=body,
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert missing_key.status_code == 400
                assert missing_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"

                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    operations_after_replay = await reviewer.operations(
                        seeded["workspace_id"], schema="content"
                    )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    durable_after_mismatch = await owner.fetchrow(
                        "SELECT "
                        "(SELECT count(*) FROM control.agent_idempotency "
                        "WHERE capability_id = $1) "
                        "AS idempotency_count, "
                        "(SELECT count(*) FROM audit.agent_mutation "
                        "WHERE capability_id = $1) "
                        "AS audit_count",
                        seeded["capability_id"],
                    )
                assert operations_after_replay == operations_before_replay
                assert tuple(durable_after_mismatch) == tuple(durable_before_replay)

        type_id = UUID(result["record"]["id"])
        async with agent_pool.acquire() as agent_connection:
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await agent_connection.fetch("SELECT * FROM content.content_type_base")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await agent_connection.fetch(
                    "SELECT * FROM content.content_type_changes"
                )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await agent_connection.fetch(
                    "SELECT * FROM control.slaif_workspace_get($1)",
                    seeded["workspace_id"],
                )
            with pytest.raises(asyncpg.PostgresError):
                await agent_connection.fetchrow(
                    "SELECT * FROM content.slaif_agent_content_type_create("
                    "$1,$2,$3,$4,$5)",
                    seeded["site_id"],
                    "outside-cow",
                    '{"en":"Outside"}',
                    "/outside",
                    "{}",
                )
        async with asyncpg_cow_session(
            agent_pool,
            session_id=seeded["workspace_id"],
            operation_id=uuid4(),
        ) as cow:
            workspace_record = await cow.execute(
                "SELECT id, site_id, key FROM content.content_type "
                "WHERE id = '" + str(type_id) + "'::uuid"
            )
            assert workspace_record == [(type_id, seeded["site_id"], "article")]
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_type_base WHERE id = $1",
                    type_id,
                )
                == 0
            )
            audit = await owner.fetchrow(
                "SELECT operation_id, workspace_id, resource_type, resource_id "
                "FROM audit.agent_mutation WHERE operation_id = $1",
                UUID(result["operation_id"]),
            )
            assert tuple(audit) == (
                UUID(result["operation_id"]),
                seeded["workspace_id"],
                "content_type",
                type_id,
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.agent_idempotency "
                    "WHERE capability_id = $1 AND operation_id = $2",
                    seeded["capability_id"],
                    UUID(result["operation_id"]),
                )
                == 1
            )

        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations = await reviewer.operations(
                seeded["workspace_id"], schema="content"
            )
            assert UUID(result["operation_id"]) in operations
            discarded = await reviewer.discard_session(
                seeded["workspace_id"], schema="content"
            )
            assert not discarded.no_op

        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_type_base WHERE id = $1",
                    type_id,
                )
                == 0
            )
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_create_routes_cover_field_item_page_and_component(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    token, seeded = await _seed(database)
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
        ) as client:
            type_response = await client.post(
                "/api/agent/v1/content-model/types",
                json={
                    "key": "route-test",
                    "labels": {"en": "Route test"},
                    "slug_pattern": "/route-test/{slug}",
                    "settings": {},
                },
                headers={**headers, "Idempotency-Key": "route-type"},
            )
            assert type_response.status_code == 201, type_response.text
            type_id = type_response.json()["record"]["id"]

            field_response = await client.post(
                f"/api/agent/v1/content-model/types/{type_id}/fields",
                json={
                    "key": "title",
                    "label": "Title",
                    "field_type": "short_text",
                },
                headers={**headers, "Idempotency-Key": "route-field"},
            )
            assert field_response.status_code == 201, field_response.text
            assert field_response.json()["record"]["key"] == "title"

            item_response = await client.post(
                f"/api/agent/v1/content-items/types/{type_id}",
                json={
                    "type_id": type_id,
                    "slug": "route-item",
                    "status": "DRAFT",
                    "values": {"title": "bounded"},
                },
                headers={**headers, "Idempotency-Key": "route-item"},
            )
            assert item_response.status_code == 201, item_response.text
            assert item_response.json()["record"]["slug"] == "route-item"

            page_response = await client.post(
                "/api/agent/v1/pages/",
                json={
                    "slug": "route-page",
                    "title": "Route page",
                    "status": "DRAFT",
                    "locale": "en",
                },
                headers={**headers, "Idempotency-Key": "route-page"},
            )
            assert page_response.status_code == 201, page_response.text
            page_id = page_response.json()["record"]["id"]

            component_response = await client.post(
                f"/api/agent/v1/pages/{page_id}/components",
                json={
                    "component_type": "Heading",
                    "slot_key": "default",
                    "order_key": 0,
                    "props": {"text": "bounded"},
                },
                headers={**headers, "Idempotency-Key": "route-component"},
            )
            assert component_response.status_code == 201, component_response.text
            assert component_response.json()["record"]["page_id"] == page_id

            listed_types = await client.get(
                "/api/agent/v1/content-model/types", headers=headers
            )
            assert listed_types.status_code == 200, listed_types.text
            assert any(item["id"] == type_id for item in listed_types.json())

            read_type = await client.get(
                f"/api/agent/v1/content-model/types/{type_id}", headers=headers
            )
            assert read_type.status_code == 200, read_type.text
            assert read_type.json()["key"] == "route-test"

            read_fields = await client.get(
                f"/api/agent/v1/content-model/types/{type_id}/fields",
                headers=headers,
            )
            assert read_fields.status_code == 200, read_fields.text
            assert [field["key"] for field in read_fields.json()] == ["title"]

            read_items = await client.get(
                f"/api/agent/v1/content-items/types/{type_id}", headers=headers
            )
            assert read_items.status_code == 200, read_items.text
            assert [item["slug"] for item in read_items.json()] == ["route-item"]

            read_pages = await client.get("/api/agent/v1/pages/", headers=headers)
            assert read_pages.status_code == 200, read_pages.text
            assert any(page["id"] == page_id for page in read_pages.json())

            read_components = await client.get(
                f"/api/agent/v1/pages/{page_id}/components", headers=headers
            )
            assert read_components.status_code == 200, read_components.text
            assert read_components.json()[0]["page_id"] == page_id

            read_media = await client.get("/api/agent/v1/media/", headers=headers)
            assert read_media.status_code == 200, read_media.text
            assert read_media.json() == []


@pytest.mark.asyncio
async def test_agent_content_item_crud_is_strict_idempotent_and_tombstoned(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "field-definition:create",
        "content-item:create",
        "content-item:read",
        "content-item:write",
        "content-item:delete",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Strict Content Item Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=20, "
            "delete_quota=2 WHERE id=$1",
            capability_id,
        )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
        ) as client:
            created_type = await client.post(
                "/api/agent/v1/content-model/types",
                headers={**headers, "Idempotency-Key": "item-type"},
                json={
                    "key": "item-crud",
                    "labels": {"en": "Item CRUD"},
                    "slug_pattern": "/item-crud/{slug}",
                    "settings": {},
                },
            )
            assert created_type.status_code == 201, created_type.text
            type_id = UUID(created_type.json()["record"]["id"])
            await _set_resource_constraints(
                database,
                workspace_id,
                {
                    "allowed_type_ids": [str(type_id)],
                    "allowed_type_keys": ["item-crud"],
                },
            )
            created_field = await client.post(
                f"/api/agent/v1/content-model/types/{type_id}/fields",
                headers={**headers, "Idempotency-Key": "item-field"},
                json={"key": "title", "label": "Title", "field_type": "short_text"},
            )
            assert created_field.status_code == 201, created_field.text
            item_path = f"/api/agent/v1/content-items/types/{type_id}"
            created_item = await client.post(
                item_path,
                headers={**headers, "Idempotency-Key": "item-create"},
                json={
                    "type_id": str(type_id),
                    "slug": "first-item",
                    "status": "DRAFT",
                    "values": {"title": "First"},
                },
            )
            assert created_item.status_code == 201, created_item.text
            created_record = created_item.json()["record"]
            item_id = UUID(created_record["id"])
            assert created_record["type_definition_version"] == 2
            assert created_record["row_version"] == 1

            exact = await client.get(
                f"/api/agent/v1/content-items/{item_id}", headers=headers
            )
            assert exact.status_code == 200, exact.text
            assert exact.json() == created_record

            update_body = {
                "slug": "updated-item",
                "values": {"title": "Updated"},
                "expected_row_version": 1,
            }
            updated = await client.patch(
                f"/api/agent/v1/content-items/{item_id}",
                headers={**headers, "Idempotency-Key": "item-update"},
                json=update_body,
            )
            assert updated.status_code == 200, updated.text
            updated_result = updated.json()
            assert updated_result["action"] == "CONTENT_ITEM_UPDATED"
            assert updated_result["record"]["row_version"] == 2
            replay = await client.patch(
                f"/api/agent/v1/content-items/{item_id}",
                headers={**headers, "Idempotency-Key": "item-update"},
                json=update_body,
            )
            assert replay.status_code == 200
            assert replay.json() == updated_result
            stale = await client.patch(
                f"/api/agent/v1/content-items/{item_id}",
                headers={**headers, "Idempotency-Key": "item-stale"},
                json={"values": {"title": "Stale"}, "expected_row_version": 1},
            )
            assert stale.status_code == 409, stale.text

            deleted = await client.request(
                "DELETE",
                f"/api/agent/v1/content-items/{item_id}",
                headers={**headers, "Idempotency-Key": "item-delete"},
                json={"expected_row_version": 2},
            )
            assert deleted.status_code == 200, deleted.text
            deleted_result = deleted.json()
            assert deleted_result["action"] == "CONTENT_ITEM_DELETED"
            assert deleted_result["record"]["status"] == "DRAFT"
            assert deleted_result["record"]["row_version"] == 2
            delete_replay = await client.request(
                "DELETE",
                f"/api/agent/v1/content-items/{item_id}",
                headers={**headers, "Idempotency-Key": "item-delete"},
                json={"expected_row_version": 2},
            )
            assert delete_replay.status_code == 200
            assert delete_replay.json() == deleted_result
            assert (await client.get(item_path, headers=headers)).json() == []
            assert (
                await client.get(
                    f"/api/agent/v1/content-items/{item_id}", headers=headers
                )
            ).status_code == 404

    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        actions = await owner.fetch(
            "SELECT action, http_method, quota_kind FROM audit.agent_mutation "
            "WHERE workspace_id=$1 ORDER BY occurred_at, operation_id",
            workspace_id,
        )
        assert [tuple(row) for row in actions][-3:] == [
            ("CONTENT_ITEM_CREATED", "POST", "mutation"),
            ("CONTENT_ITEM_UPDATED", "PATCH", "mutation"),
            ("CONTENT_ITEM_DELETED", "DELETE", "delete"),
        ]
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM content.content_item_base WHERE id=$1", item_id
            )
            == 0
        )
        assert (
            await owner.fetchval(
                "SELECT mutation_used FROM control.capability WHERE id=$1",
                capability_id,
            )
            == 4
        )
        assert (
            await owner.fetchval(
                "SELECT delete_used FROM control.capability WHERE id=$1", capability_id
            )
            == 1
        )


@pytest.mark.asyncio
async def test_agent_content_item_translation_crud_is_strict_and_cow_bound(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "field-definition:create",
        "content-item:create",
        "content-item:read",
        "translation:read",
        "translation:write",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Translation Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=20, "
            "delete_quota=1 WHERE id=$1",
            capability_id,
        )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                parent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "translation-parent"},
                    json={
                        "key": "translation-parent",
                        "labels": {"en": "Translation parent"},
                        "slug_pattern": "/translation-parent/{slug}",
                        "settings": {},
                    },
                )
                assert parent.status_code == 201, parent.text
                parent_id = UUID(parent.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(parent_id)],
                        "allowed_type_keys": ["translation-parent"],
                        "delete_enabled": True,
                    },
                )
                for key, localized, idem in (
                    ("title", False, "translation-title"),
                    ("headline", True, "translation-headline"),
                ):
                    field = await client.post(
                        f"/api/agent/v1/content-model/types/{parent_id}/fields",
                        headers={**headers, "Idempotency-Key": idem},
                        json={
                            "key": key,
                            "label": key.title(),
                            "field_type": "short_text",
                            "localized": localized,
                            "required": localized,
                        },
                    )
                    assert field.status_code == 201, field.text

                item = await client.post(
                    f"/api/agent/v1/content-items/types/{parent_id}",
                    headers={**headers, "Idempotency-Key": "translation-item"},
                    json={
                        "type_id": str(parent_id),
                        "slug": "translation-item",
                        "status": "DRAFT",
                        "values": {"title": "Base title"},
                    },
                )
                assert item.status_code == 201, item.text
                item_id = UUID(item.json()["record"]["id"])
                translation_path = f"/api/agent/v1/content-items/{item_id}/translations"

                wrong_scope = await _capability_with_scopes(
                    database, seeded, ["translation:read"]
                )
                denied = await client.post(
                    translation_path,
                    headers={
                        "Authorization": f"Bearer {wrong_scope}",
                        "Idempotency-Key": "translation-denied",
                    },
                    json={"locale": "en-US", "localized_values": {"headline": "No"}},
                )
                assert denied.status_code == 403, denied.text

                invalid_locale = await client.post(
                    translation_path,
                    headers={
                        **headers,
                        "Idempotency-Key": "translation-invalid-locale",
                    },
                    json={
                        "locale": "not a locale",
                        "localized_values": {"headline": "No"},
                    },
                )
                assert invalid_locale.status_code == 422, invalid_locale.text
                invalid_nonlocalized = await client.post(
                    translation_path,
                    headers={
                        **headers,
                        "Idempotency-Key": "translation-invalid-nonlocalized",
                    },
                    json={"locale": "en-US", "localized_values": {"title": "No"}},
                )
                assert invalid_nonlocalized.status_code == 422, (
                    invalid_nonlocalized.text
                )

                created = await client.post(
                    translation_path,
                    headers={**headers, "Idempotency-Key": "translation-create"},
                    json={
                        "locale": "en-US",
                        "localized_values": {"headline": "Hello"},
                    },
                )
                assert created.status_code == 201, created.text
                created_result = created.json()
                assert created_result["action"] == "CONTENT_ITEM_TRANSLATION_CREATED"
                created_record = created_result["record"]
                translation_id = UUID(created_record["id"])
                assert created_record["row_version"] == 1

                replay = await client.post(
                    translation_path,
                    headers={**headers, "Idempotency-Key": "translation-create"},
                    json={
                        "locale": "en-US",
                        "localized_values": {"headline": "Hello"},
                    },
                )
                assert replay.status_code == 201
                assert replay.json() == created_result
                mismatch = await client.post(
                    translation_path,
                    headers={**headers, "Idempotency-Key": "translation-create"},
                    json={
                        "locale": "en-US",
                        "localized_values": {"headline": "Changed"},
                    },
                )
                assert mismatch.status_code == 409
                assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_MISMATCH"

                listed = await client.get(translation_path, headers=headers)
                assert listed.status_code == 200, listed.text
                assert listed.json() == [created_record]
                exact = await client.get(
                    f"{translation_path}/{translation_id}", headers=headers
                )
                assert exact.status_code == 200, exact.text
                assert exact.json() == created_record
                wrong_parent = await client.get(
                    f"/api/agent/v1/content-items/{uuid4()}/translations/{translation_id}",
                    headers=headers,
                )
                assert wrong_parent.status_code == 404, wrong_parent.text

                updated = await client.patch(
                    f"{translation_path}/{translation_id}",
                    headers={**headers, "Idempotency-Key": "translation-update"},
                    json={
                        "localized_values": {"headline": "Updated"},
                        "expected_row_version": 1,
                    },
                )
                assert updated.status_code == 200, updated.text
                updated_result = updated.json()
                assert updated_result["action"] == "CONTENT_ITEM_TRANSLATION_UPDATED"
                assert updated_result["record"]["row_version"] == 2
                stale = await client.patch(
                    f"{translation_path}/{translation_id}",
                    headers={**headers, "Idempotency-Key": "translation-stale"},
                    json={
                        "localized_values": {"headline": "Stale"},
                        "expected_row_version": 1,
                    },
                )
                assert stale.status_code == 409, stale.text

                second = await client.post(
                    translation_path,
                    headers={**headers, "Idempotency-Key": "translation-create-second"},
                    json={
                        "locale": "sl-SI",
                        "localized_values": {"headline": "Živjo"},
                    },
                )
                assert second.status_code == 201, second.text
                second_record = second.json()["record"]
                second_id = UUID(second_record["id"])

                # Two real Agent application instances must serialize on the
                # translation row lock, with one winner and one stale conflict.
                app_two = create_agent_app(
                    settings=ServiceSettings.for_test(),
                    database_settings=_agent_settings(database),
                )
                async with app_two.router.lifespan_context(app_two):
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app_two),
                        base_url="http://agent-two.test",
                    ) as client_two:
                        race_responses = await asyncio.gather(
                            client.patch(
                                f"{translation_path}/{second_id}",
                                headers={
                                    **headers,
                                    "Idempotency-Key": "translation-race-one",
                                },
                                json={
                                    "localized_values": {"headline": "Race one"},
                                    "expected_row_version": 1,
                                },
                            ),
                            client_two.patch(
                                f"{translation_path}/{second_id}",
                                headers={
                                    **headers,
                                    "Idempotency-Key": "translation-race-two",
                                },
                                json={
                                    "localized_values": {"headline": "Race two"},
                                    "expected_row_version": 1,
                                },
                            ),
                        )
                assert sorted(response.status_code for response in race_responses) == [
                    200,
                    409,
                ], [response.text for response in race_responses]
                raced_record = next(
                    response.json()["record"]
                    for response in race_responses
                    if response.status_code == 200
                )
                assert raced_record["row_version"] == 2

                deleted = await client.request(
                    "DELETE",
                    f"{translation_path}/{translation_id}",
                    headers={**headers, "Idempotency-Key": "translation-delete"},
                    json={"expected_row_version": 2},
                )
                assert deleted.status_code == 200, deleted.text
                deleted_result = deleted.json()
                assert deleted_result["action"] == "CONTENT_ITEM_TRANSLATION_DELETED"
                assert deleted_result["record"] == updated_result["record"]
                delete_replay = await client.request(
                    "DELETE",
                    f"{translation_path}/{translation_id}",
                    headers={**headers, "Idempotency-Key": "translation-delete"},
                    json={"expected_row_version": 2},
                )
                assert delete_replay.status_code == 200
                assert delete_replay.json() == deleted_result
                remaining = await client.get(translation_path, headers=headers)
                assert remaining.status_code == 200
                assert remaining.json() == [raced_record]

                quota_denied = await client.request(
                    "DELETE",
                    f"{translation_path}/{second_id}",
                    headers={**headers, "Idempotency-Key": "translation-delete-second"},
                    json={"expected_row_version": 2},
                )
                assert quota_denied.status_code == 429, quota_denied.text
                assert (await client.get(translation_path, headers=headers)).json() == [
                    raced_record
                ]

                changed_field = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "translation-new-field"},
                    json={
                        "key": "later-field",
                        "label": "Later field",
                        "field_type": "short_text",
                    },
                )
                assert changed_field.status_code == 201, changed_field.text
                stale_definition = await client.patch(
                    f"{translation_path}/{second_id}",
                    headers={
                        **headers,
                        "Idempotency-Key": "translation-stale-definition",
                    },
                    json={
                        "localized_values": {"headline": "Rejected"},
                        "expected_row_version": 1,
                    },
                )
                assert stale_definition.status_code == 422, stale_definition.text

        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations = await reviewer.operations(workspace_id, schema="content")
            assert UUID(created_result["operation_id"]) in operations
            assert UUID(updated_result["operation_id"]) in operations
            assert UUID(deleted_result["operation_id"]) in operations
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            actions = await owner.fetch(
                "SELECT action, http_method, quota_kind FROM audit.agent_mutation "
                "WHERE workspace_id=$1 AND resource_type='content_item_translation' "
                "ORDER BY occurred_at, operation_id",
                workspace_id,
            )
            assert [tuple(row) for row in actions] == [
                (
                    "CONTENT_ITEM_TRANSLATION_CREATED",
                    "POST",
                    "mutation",
                ),
                (
                    "CONTENT_ITEM_TRANSLATION_UPDATED",
                    "PATCH",
                    "mutation",
                ),
                (
                    "CONTENT_ITEM_TRANSLATION_CREATED",
                    "POST",
                    "mutation",
                ),
                (
                    "CONTENT_ITEM_TRANSLATION_UPDATED",
                    "PATCH",
                    "mutation",
                ),
                (
                    "CONTENT_ITEM_TRANSLATION_DELETED",
                    "DELETE",
                    "delete",
                ),
            ]
            assert (
                await owner.fetchval(
                    "SELECT delete_used FROM control.capability WHERE id=$1",
                    capability_id,
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_item_translation_base "
                    "WHERE item_id=$1",
                    item_id,
                )
                == 0
            )
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_046_047_migration_round_trip_preserves_contract_and_state(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-item:create",
        "content-item:read",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Migration Round Trip Workspace"
    )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                created_type = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "migration-type",
                    },
                    json={
                        "key": "migration-type",
                        "labels": {"en": "Migration type"},
                        "slug_pattern": "/migration/{slug}",
                        "settings": {},
                    },
                )
                assert created_type.status_code == 201, created_type.text
                type_id = UUID(created_type.json()["record"]["id"])
                created_item = await client.post(
                    f"/api/agent/v1/content-items/types/{type_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "migration-item",
                    },
                    json={
                        "type_id": str(type_id),
                        "slug": "migration-item",
                        "status": "DRAFT",
                        "values": {},
                    },
                )
                assert created_item.status_code == 201, created_item.text
                item_id = UUID(created_item.json()["record"]["id"])

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="046_001",
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT version_num::text FROM control.alembic_version"
                )
                == "046_001"
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_require_capability(uuid)",
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_require_capability(uuid,text)",
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "content.slaif_agent_content_item_translation_list(uuid,uuid)",
            )
            actions = await owner.fetch(
                "SELECT action FROM audit.agent_mutation WHERE workspace_id=$1 "
                "ORDER BY occurred_at, operation_id",
                workspace_id,
            )
            assert [row[0] for row in actions] == [
                "CONTENT_TYPE_CREATED",
                "CONTENT_ITEM_CREATED",
            ]
            constraint = await owner.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid='audit.agent_mutation'::regclass "
                "AND conname='agent_mutation_semantic_shape'"
            )
            assert "CONTENT_ITEM_TRANSLATION_CREATED" not in constraint
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            assert (
                await cow.native.fetchval(
                    "SELECT count(*) FROM content.content_item WHERE id=$1", item_id
                )
                == 1
            )

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="upgrade",
            revision="head",
        )
        await reconcile(database.settings)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT version_num::text FROM control.alembic_version"
                )
                == "048_001"
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_require_capability(uuid,text)",
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_require_capability(uuid)",
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "content.slaif_agent_content_item_translation_list(uuid,uuid)",
            )
            constraint = await owner.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid='audit.agent_mutation'::regclass "
                "AND conname='agent_mutation_semantic_shape'"
            )
            assert "CONTENT_ITEM_TRANSLATION_CREATED" in constraint
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            assert (
                await cow.native.fetchval(
                    "SELECT count(*) FROM content.content_item WHERE id=$1", item_id
                )
                == 1
            )
    finally:
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_048_data_bearing_round_trip_preserves_relations_views_and_audit(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """A 048 workspace survives a real 048 -> 047 -> 048 transition."""

    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "content-model:create",
        "content-model:read",
        "field-definition:create",
        "content-item:create",
        "content-item:read",
        "relationship:write",
        "collection-view:read",
        "collection-view:create",
        "collection-view:write",
        "collection-view:delete",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent 048 Data Round Trip Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=100, "
            "delete_quota=20 WHERE id=$1",
            capability_id,
        )

    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}

    async def cow_rows() -> tuple[tuple[Any, ...], tuple[Any, ...]]:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            relations = tuple(
                tuple(row)
                for row in await cow.native.fetch(
                    "SELECT id,site_id,source_item_id,field_definition_id,"
                    "target_item_id,position,metadata,row_version "
                    "FROM content.item_relation ORDER BY id"
                )
            )
            views = tuple(
                tuple(row)
                for row in await cow.native.fetch(
                    "SELECT id,site_id,type_id,key,filter_spec,sort_spec,"
                    "projection_spec,pagination_spec,definition_version,row_version "
                    "FROM content.collection_view ORDER BY id"
                )
            )
        return relations, views

    async def durable_rows() -> tuple[tuple[Any, ...], tuple[Any, ...]]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            idempotency = tuple(
                tuple(row)
                for row in await owner.fetch(
                    "SELECT idempotency_key,operation_id,request_digest,status_code,"
                    "resource_type,resource_id,response_body::text "
                    "FROM control.agent_idempotency WHERE workspace_id=$1 "
                    "ORDER BY idempotency_key",
                    workspace_id,
                )
            )
            audit = tuple(
                tuple(row)
                for row in await owner.fetch(
                    "SELECT operation_id,capability_id,workspace_id,site_id,"
                    "resource_type,resource_id,request_digest,response_status,action,"
                    "http_method,quota_kind FROM audit.agent_mutation "
                    "WHERE workspace_id=$1 ORDER BY operation_id",
                    workspace_id,
                )
            )
        return idempotency, audit

    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                type_response = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "roundtrip-type"},
                    json={
                        "key": "roundtrip-relations",
                        "labels": {"en": "Round trip relations"},
                        "slug_pattern": "/roundtrip/{slug}",
                        "settings": {},
                    },
                )
                assert type_response.status_code == 201, type_response.text
                type_id = UUID(type_response.json()["record"]["id"])
                field_response = await client.post(
                    f"/api/agent/v1/content-model/types/{type_id}/fields",
                    headers={**headers, "Idempotency-Key": "roundtrip-field"},
                    json={
                        "key": "related",
                        "label": "Related",
                        "field_type": "reference",
                    },
                )
                assert field_response.status_code == 201, field_response.text
                field_id = UUID(field_response.json()["record"]["id"])

                async def create_item(slug: str) -> UUID:
                    response = await client.post(
                        f"/api/agent/v1/content-items/types/{type_id}",
                        headers={**headers, "Idempotency-Key": f"roundtrip-{slug}"},
                        json={
                            "type_id": str(type_id),
                            "slug": slug,
                            "status": "DRAFT",
                            "values": {},
                        },
                    )
                    assert response.status_code == 201, response.text
                    return UUID(response.json()["record"]["id"])

                source_id = await create_item("source")
                target_id = await create_item("target")
                relation_path = f"/api/agent/v1/content-items/{source_id}/relations"
                relation_payload = {
                    "field_definition_id": str(field_id),
                    "target_item_id": str(target_id),
                }
                relation_response = await client.post(
                    relation_path,
                    headers={**headers, "Idempotency-Key": "roundtrip-relation"},
                    json=relation_payload,
                )
                assert relation_response.status_code == 201, relation_response.text
                relation_result = relation_response.json()
                relation_id = UUID(relation_result["record"]["id"])
                relation_operation_id = UUID(relation_result["operation_id"])

                view_path = f"/api/agent/v1/collection-views/types/{type_id}"
                view_payload = {
                    "type_id": str(type_id),
                    "key": "roundtrip",
                    "filter_spec": {},
                    "sort_spec": {"field": "slug", "direction": "asc"},
                    "projection_spec": {},
                    "pagination_spec": {"limit": 10, "offset": 0},
                }
                view_response = await client.post(
                    view_path,
                    headers={**headers, "Idempotency-Key": "roundtrip-view"},
                    json=view_payload,
                )
                assert view_response.status_code == 201, view_response.text
                view_result = view_response.json()
                view_id = UUID(view_result["record"]["id"])

        content_before = await cow_rows()
        durable_before = await durable_rows()
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations_before = tuple(
                sorted(await reviewer.operations(workspace_id, schema="content"))
            )

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="047_001",
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT version_num::text FROM control.alembic_version"
                )
                == "047_001"
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_require_capability(uuid,text)",
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_require_capability(uuid)",
            )
            for signature in (
                "content.slaif_agent_item_relation_create(uuid,uuid,uuid,uuid,integer,jsonb)",
                "content.slaif_agent_collection_view_create(uuid,uuid,text,jsonb,jsonb,jsonb,jsonb,integer)",
                "content.slaif_agent_relation_assert(uuid,uuid,uuid,uuid,text,boolean)",
                "content.slaif_agent_collection_view_query_validate(uuid,jsonb,jsonb,jsonb,jsonb)",
            ):
                assert not await owner.fetchval("SELECT to_regprocedure($1)", signature)
            constraint = await owner.fetchval(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid='audit.agent_mutation'::regclass "
                "AND conname='agent_mutation_semantic_shape'"
            )
            assert "ITEM_RELATION_CREATED" in constraint
            assert "COLLECTION_VIEW_CREATED" in constraint
            assert "CONTENT_ITEM_TRANSLATION_CREATED" in constraint

        assert await cow_rows() == content_before
        assert await durable_rows() == durable_before
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert (
                tuple(sorted(await reviewer.operations(workspace_id, schema="content")))
                == operations_before
            )

        relation_audit = next(
            row for row in durable_before[1] if row[0] == relation_operation_id
        )
        invalid_response = {
            "record": {"id": str(relation_id)},
            "operation_id": str(relation_operation_id),
            "action": "ITEM_RELATION_CREATED",
        }
        with pytest.raises(asyncpg.PostgresError, match="INVALID_SEMANTIC_COMPLETION"):
            async with agent_pool.acquire() as connection:
                await connection.fetchval(
                    "SELECT control.slaif_agent_idempotency_complete("
                    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                    capability_id,
                    workspace_id,
                    relation_audit[0].hex,
                    relation_audit[6],
                    relation_operation_id,
                    201,
                    json.dumps(invalid_response),
                    "item_relation",
                    relation_id,
                    seeded["site_id"],
                    "ITEM_RELATION_CREATED",
                    "POST",
                    "mutation",
                )
        assert await durable_rows() == durable_before

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="upgrade",
            revision="head",
        )
        await reconcile(database.settings)
        final_status = await status(database.settings)
        assert final_status.revision == "048_001"
        assert final_status.state.value == "HARDENED"
        assert final_status.safe
        assert await cow_rows() == content_before
        assert await durable_rows() == durable_before
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            for signature in (
                "content.slaif_agent_item_relation_create(uuid,uuid,uuid,uuid,integer,jsonb)",
                "content.slaif_agent_collection_view_create(uuid,uuid,text,jsonb,jsonb,jsonb,jsonb,integer)",
            ):
                grant = await owner.fetchrow(
                    "SELECT pg_get_userbyid(proowner), "
                    "has_function_privilege('slaif_agent_runtime',$1,'EXECUTE'), "
                    "has_function_privilege('public',$1,'EXECUTE') "
                    "FROM pg_proc WHERE oid=$1::regprocedure",
                    signature,
                )
                assert tuple(grant) == ("slaif_owner", True, False)
            for signature in (
                "content.slaif_agent_relation_assert(uuid,uuid,uuid,uuid,text,boolean)",
                "content.slaif_agent_collection_view_query_validate(uuid,jsonb,jsonb,jsonb,jsonb)",
            ):
                assert not await owner.fetchval(
                    "SELECT has_function_privilege('slaif_agent_runtime',$1,'EXECUTE')",
                    signature,
                )

        app_after = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app_after.router.lifespan_context(app_after):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app_after),
                base_url="http://agent-after-migration.test",
            ) as client:
                relation_item_path = f"{relation_path}/{relation_id}"
                assert (await client.get(relation_path, headers=headers)).json() == [
                    relation_result["record"]
                ]
                assert (
                    await client.get(relation_item_path, headers=headers)
                ).json() == relation_result["record"]
                assert (
                    await client.get(
                        f"/api/agent/v1/collection-views/{view_id}",
                        headers=headers,
                    )
                ).json() == view_result["record"]
                assert (
                    await client.post(
                        relation_path,
                        headers={
                            **headers,
                            "Idempotency-Key": "roundtrip-relation",
                        },
                        json=relation_payload,
                    )
                ).json() == relation_result
                assert (
                    await client.post(
                        view_path,
                        headers={**headers, "Idempotency-Key": "roundtrip-view"},
                        json=view_payload,
                    )
                ).json() == view_result
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_model_and_translation_wrappers_require_exact_scopes(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:write",
        "content-model:delete",
        "field-definition:create",
        "field-definition:write",
        "field-definition:delete",
        "content-item:create",
        "content-item:read",
        "content-item:write",
        "content-item:delete",
        "translation:read",
        "translation:write",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Exact Scope Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        full_capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                parent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "scope-parent",
                    },
                    json={
                        "key": "scope-parent",
                        "labels": {"en": "Scope parent"},
                        "slug_pattern": "/scope/{slug}",
                        "settings": {},
                    },
                )
                assert parent.status_code == 201, parent.text
                type_id = UUID(parent.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(type_id)],
                        "allowed_type_keys": ["scope-parent"],
                    },
                )
                field = await client.post(
                    f"/api/agent/v1/content-model/types/{type_id}/fields",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "scope-field",
                    },
                    json={
                        "key": "scope-title",
                        "label": "Scope title",
                        "field_type": "short_text",
                    },
                )
                assert field.status_code == 201, field.text
                field_id = UUID(field.json()["record"]["id"])
                item = await client.post(
                    f"/api/agent/v1/content-items/types/{type_id}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "scope-item",
                    },
                    json={
                        "type_id": str(type_id),
                        "slug": "scope-item",
                        "status": "DRAFT",
                        "values": {"scope-title": "Scope"},
                    },
                )
                assert item.status_code == 201, item.text
                item_id = UUID(item.json()["record"]["id"])

                async def issue_capability(
                    capability_scopes: list[str],
                ) -> tuple[str, UUID]:
                    issued_token, public_id, digest = generate_capability_token()
                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        issued_id = await owner.fetchval(
                            """
                            INSERT INTO control.capability (
                                workspace_id, public_id, secret_digest, scopes,
                                expires_at
                            ) VALUES (
                                $1, $2, $3, $4::jsonb,
                                now() + interval '30 minutes'
                            )
                            RETURNING id
                            """,
                            workspace_id,
                            public_id,
                            digest,
                            json.dumps(capability_scopes),
                        )
                    return issued_token, issued_id

                _wrong_token, wrong_capability_id = await issue_capability(
                    ["site:read"]
                )

                async def denied(sql: str, *arguments: object) -> None:
                    async with asyncpg_cow_session(
                        agent_pool, session_id=workspace_id, operation_id=uuid4()
                    ) as cow:
                        await cow.native.execute(
                            "SELECT set_config('app.capability_id',$1,true)",
                            str(wrong_capability_id),
                        )
                        with pytest.raises(
                            asyncpg.PostgresError, match="AGENT_SCOPE_DENIED"
                        ):
                            await cow.native.fetch(sql, *arguments)
                        await cow.rollback()

                denied_calls: tuple[tuple[str, tuple[object, ...]], ...] = (
                    (
                        "SELECT * FROM content.slaif_agent_content_type_list($1)",
                        (seeded["site_id"],),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_type_get($1,$2)",
                        (seeded["site_id"], type_id),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_field_definition_list("
                        "$1,$2)",
                        (seeded["site_id"], type_id),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_item_list($1,$2)",
                        (seeded["site_id"], type_id),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_item_get($1,$2)",
                        (seeded["site_id"], item_id),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_type_create("
                        "$1,$2,$3,$4,$5)",
                        (seeded["site_id"], "denied", "{}", "/denied", "{}"),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_type_update("
                        "$1,$2,$3,$4,$5,$6)",
                        (seeded["site_id"], type_id, None, None, None, 1),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_type_delete("
                        "$1,$2,$3)",
                        (seeded["site_id"], type_id, 2),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_field_definition_create("
                        "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                        (
                            seeded["site_id"],
                            type_id,
                            "denied-field",
                            "Denied",
                            "short_text",
                            False,
                            False,
                            1,
                            0,
                            "{}",
                            "{}",
                        ),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_field_definition_update("
                        "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                        (
                            seeded["site_id"],
                            type_id,
                            field_id,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            1,
                        ),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_field_definition_delete("
                        "$1,$2,$3,$4)",
                        (seeded["site_id"], type_id, field_id, 1),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_item_create("
                        "$1,$2,$3,$4,$5)",
                        (seeded["site_id"], type_id, "denied-item", "DRAFT", "{}"),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_item_update("
                        "$1,$2,$3,$4,$5,$6)",
                        (seeded["site_id"], item_id, None, None, None, 1),
                    ),
                    (
                        "SELECT * FROM content.slaif_agent_content_item_delete("
                        "$1,$2,$3)",
                        (seeded["site_id"], item_id, 1),
                    ),
                    (
                        "SELECT * FROM content."
                        "slaif_agent_content_item_translation_fields_for_write("
                        "$1,$2)",
                        (seeded["site_id"], item_id),
                    ),
                    (
                        "SELECT * FROM content."
                        "slaif_agent_content_item_translation_list("
                        "$1,$2)",
                        (seeded["site_id"], item_id),
                    ),
                    (
                        "SELECT * FROM content."
                        "slaif_agent_content_item_translation_get("
                        "$1,$2,$3)",
                        (seeded["site_id"], item_id, uuid4()),
                    ),
                    (
                        "SELECT * FROM content."
                        "slaif_agent_content_item_translation_create("
                        "$1,$2,$3,$4)",
                        (seeded["site_id"], item_id, "en-US", "{}"),
                    ),
                    (
                        "SELECT * FROM content."
                        "slaif_agent_content_item_translation_update("
                        "$1,$2,$3,$4,$5,$6)",
                        (seeded["site_id"], item_id, uuid4(), None, None, 1),
                    ),
                    (
                        "SELECT * FROM content."
                        "slaif_agent_content_item_translation_delete("
                        "$1,$2,$3,$4)",
                        (seeded["site_id"], item_id, uuid4(), 1),
                    ),
                )
                for sql, arguments in denied_calls:
                    await denied(sql, *arguments)

                _malformed_token, malformed_capability_id = await issue_capability(
                    ["content-model:read"]
                )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.capability SET scopes='{}'::jsonb WHERE id=$1",
                        malformed_capability_id,
                    )
                async with asyncpg_cow_session(
                    agent_pool, session_id=workspace_id, operation_id=uuid4()
                ) as cow:
                    await cow.native.execute(
                        "SELECT set_config('app.capability_id',$1,true)",
                        str(malformed_capability_id),
                    )
                    with pytest.raises(
                        asyncpg.PostgresError, match="AGENT_SCOPE_DENIED"
                    ):
                        await cow.native.fetch(
                            "SELECT * FROM content.slaif_agent_content_type_list($1)",
                            seeded["site_id"],
                        )
                    await cow.rollback()

                async with asyncpg_cow_session(
                    agent_pool, session_id=workspace_id, operation_id=uuid4()
                ) as cow:
                    await cow.native.execute(
                        "SELECT set_config('app.capability_id',$1,true)",
                        str(full_capability_id),
                    )
                    # The full-scope capability is proven by the HTTP calls; this
                    # direct call proves the scope check permits its exact read.
                    rows = await cow.native.fetch(
                        "SELECT * FROM content.slaif_agent_content_type_list($1)",
                        seeded["site_id"],
                    )
                    assert any(row[0] == type_id for row in rows)
    finally:
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_canonical_item_delete_is_a_real_cow_delete_and_isolated(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    canonical_type_id = UUID("00000000-0000-0000-0000-0000000007a1")
    canonical_item_id = UUID("00000000-0000-0000-0000-0000000007a2")
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            """
            INSERT INTO content.content_type_base (
                id, site_id, "key", labels, slug_pattern, status,
                definition_version, settings
            ) VALUES (
                $1, $2, 'canonical-delete-type',
                '{"en":"Canonical delete"}'::jsonb,
                '/canonical-delete/{slug}', 'ACTIVE', 1, '{}'::jsonb
            )
            """,
            canonical_type_id,
            seeded["site_id"],
        )
        await owner.execute(
            """
            INSERT INTO content.content_item_base (
                id, site_id, type_id, slug, status, type_definition_version,
                "values", row_version
            ) VALUES ($1, $2, $3, 'canonical-delete-item', 'DRAFT', 1,
                      '{}'::jsonb, 1)
            """,
            canonical_item_id,
            seeded["site_id"],
            canonical_type_id,
        )
    scopes_a = [
        "site:read",
        "content-model:read",
        "content-model:delete",
        "content-item:read",
        "content-item:delete",
    ]
    scopes_b = ["site:read", "content-model:read", "content-item:read"]
    token_a, workspace_a = await _workspace_capability(
        database, seeded, scopes_a, "Canonical Delete Workspace A"
    )
    token_b, workspace_b = await _workspace_capability(
        database, seeded, scopes_b, "Canonical Delete Workspace B"
    )
    for workspace in (workspace_a, workspace_b):
        await _set_resource_constraints(
            database,
            workspace,
            {
                "allowed_type_ids": [str(canonical_type_id)],
                "allowed_type_keys": ["canonical-delete-type"],
                "delete_enabled": True,
            },
        )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.capability SET delete_quota=2 WHERE workspace_id=$1",
            workspace_a,
        )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                item_path = f"/api/agent/v1/content-items/{canonical_item_id}"
                list_path = f"/api/agent/v1/content-items/types/{canonical_type_id}"
                before = await client.get(
                    item_path, headers={"Authorization": f"Bearer {token_a}"}
                )
                assert before.status_code == 200, before.text
                assert before.json()["id"] == str(canonical_item_id)

                deleted = await client.request(
                    "DELETE",
                    item_path,
                    headers={
                        "Authorization": f"Bearer {token_a}",
                        "Idempotency-Key": "canonical-item-delete",
                    },
                    json={"expected_row_version": 1},
                )
                assert deleted.status_code == 200, deleted.text
                deleted_result = deleted.json()
                assert deleted_result["action"] == "CONTENT_ITEM_DELETED"
                assert deleted_result["record"] == before.json()
                replay = await client.request(
                    "DELETE",
                    item_path,
                    headers={
                        "Authorization": f"Bearer {token_a}",
                        "Idempotency-Key": "canonical-item-delete",
                    },
                    json={"expected_row_version": 1},
                )
                assert replay.status_code == 200
                assert replay.json() == deleted_result
                assert (
                    await client.get(
                        item_path, headers={"Authorization": f"Bearer {token_a}"}
                    )
                ).status_code == 404
                assert (
                    await client.get(
                        list_path, headers={"Authorization": f"Bearer {token_a}"}
                    )
                ).json() == []

                other_workspace_item = await client.get(
                    item_path, headers={"Authorization": f"Bearer {token_b}"}
                )
                assert other_workspace_item.status_code == 200
                assert other_workspace_item.json() == before.json()

                type_deleted = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{canonical_type_id}",
                    headers={
                        "Authorization": f"Bearer {token_a}",
                        "Idempotency-Key": "canonical-type-delete",
                    },
                    json={"expected_definition_version": 1},
                )
                assert type_deleted.status_code == 200, type_deleted.text
                assert type_deleted.json()["record"]["status"] == "DELETED"
                still_other_type = await client.get(
                    f"/api/agent/v1/content-model/types/{canonical_type_id}",
                    headers={"Authorization": f"Bearer {token_b}"},
                )
                assert still_other_type.status_code == 200
                assert still_other_type.json()["status"] == "ACTIVE"

        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations = await reviewer.operations(workspace_a, schema="content")
            assert UUID(deleted_result["operation_id"]) in operations
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_item_base WHERE id=$1",
                    canonical_item_id,
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_type_base WHERE id=$1",
                    canonical_type_id,
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT delete_used FROM control.capability WHERE workspace_id=$1",
                    workspace_a,
                )
                == 2
            )
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_relation_and_collection_view_crud_is_cow_bound_and_audited(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "content-model:create",
        "content-model:read",
        "field-definition:create",
        "content-item:create",
        "content-item:read",
        "relationship:write",
        "collection-view:read",
        "collection-view:create",
        "collection-view:write",
        "collection-view:delete",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Relation View Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=20, "
            "delete_quota=10 WHERE id=$1",
            capability_id,
        )
    await _set_resource_constraints(
        database,
        workspace_id,
        {"delete_enabled": True},
    )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                created_type = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "relation-view-type"},
                    json={
                        "key": "relation-view-type",
                        "labels": {"en": "Relation view type"},
                        "slug_pattern": "/relation-view/{slug}",
                        "settings": {},
                    },
                )
                assert created_type.status_code == 201, created_type.text
                type_id = UUID(created_type.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(type_id)],
                        "allowed_type_keys": ["relation-view-type"],
                        "delete_enabled": True,
                    },
                )
                field = await client.post(
                    f"/api/agent/v1/content-model/types/{type_id}/fields",
                    headers={**headers, "Idempotency-Key": "relation-view-field"},
                    json={
                        "key": "related",
                        "label": "Related",
                        "field_type": "reference",
                    },
                )
                assert field.status_code == 201, field.text
                field_id = UUID(field.json()["record"]["id"])

                async def create_item(key: str) -> UUID:
                    response = await client.post(
                        f"/api/agent/v1/content-items/types/{type_id}",
                        headers={**headers, "Idempotency-Key": f"relation-view-{key}"},
                        json={
                            "type_id": str(type_id),
                            "slug": key,
                            "status": "DRAFT",
                            "values": {},
                        },
                    )
                    assert response.status_code == 201, response.text
                    return UUID(response.json()["record"]["id"])

                source_id = await create_item("source")
                target_id = await create_item("target")
                relation_path = f"/api/agent/v1/content-items/{source_id}/relations"
                relation = await client.post(
                    relation_path,
                    headers={**headers, "Idempotency-Key": "relation-create"},
                    json={
                        "field_definition_id": str(field_id),
                        "target_item_id": str(target_id),
                    },
                )
                assert relation.status_code == 201, relation.text
                relation_result = relation.json()
                assert relation_result["action"] == "ITEM_RELATION_CREATED"
                relation_id = UUID(relation_result["record"]["id"])
                assert relation_result["record"]["row_version"] == 1
                assert (
                    await client.post(
                        relation_path,
                        headers={**headers, "Idempotency-Key": "relation-create"},
                        json={
                            "field_definition_id": str(field_id),
                            "target_item_id": str(target_id),
                        },
                    )
                ).json() == relation_result
                assert (await client.get(relation_path, headers=headers)).json() == [
                    relation_result["record"]
                ]
                relation_item_path = f"{relation_path}/{relation_id}"
                assert (
                    await client.get(relation_item_path, headers=headers)
                ).json() == relation_result["record"]
                relation_update = await client.patch(
                    relation_item_path,
                    headers={**headers, "Idempotency-Key": "relation-update"},
                    json={"metadata": {"kind": "related"}, "expected_row_version": 1},
                )
                assert relation_update.status_code == 200, relation_update.text
                assert relation_update.json()["record"]["row_version"] == 2
                stale_relation = await client.patch(
                    relation_item_path,
                    headers={**headers, "Idempotency-Key": "relation-stale"},
                    json={"metadata": {}, "expected_row_version": 1},
                )
                assert stale_relation.status_code == 409, stale_relation.text

                view_path = f"/api/agent/v1/collection-views/types/{type_id}"
                view = await client.post(
                    view_path,
                    headers={**headers, "Idempotency-Key": "view-create"},
                    json={
                        "type_id": str(type_id),
                        "key": "published",
                        "filter_spec": {"status": "DRAFT"},
                        "sort_spec": {"field": "slug", "direction": "asc"},
                        "projection_spec": {},
                        "pagination_spec": {"limit": 10, "offset": 0},
                    },
                )
                assert view.status_code == 201, view.text
                view_result = view.json()
                assert view_result["action"] == "COLLECTION_VIEW_CREATED"
                view_id = UUID(view_result["record"]["id"])
                view_item_path = f"/api/agent/v1/collection-views/{view_id}"
                assert (await client.get(view_path, headers=headers)).json() == [
                    view_result["record"]
                ]
                assert (
                    await client.get(view_item_path, headers=headers)
                ).json() == view_result["record"]
                view_update = await client.patch(
                    view_item_path,
                    headers={**headers, "Idempotency-Key": "view-update"},
                    json={
                        "pagination_spec": {"limit": 5, "offset": 0},
                        "expected_row_version": 1,
                    },
                )
                assert view_update.status_code == 200, view_update.text
                assert view_update.json()["record"]["row_version"] == 2
                app_two = create_agent_app(
                    settings=ServiceSettings.for_test(),
                    database_settings=_agent_settings(database),
                )
                async with app_two.router.lifespan_context(app_two):
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app_two),
                        base_url="http://agent-two.test",
                    ) as client_two:
                        view_race_responses = await asyncio.gather(
                            client.patch(
                                view_item_path,
                                headers={
                                    **headers,
                                    "Idempotency-Key": "view-race-one",
                                },
                                json={
                                    "pagination_spec": {"limit": 4, "offset": 0},
                                    "expected_row_version": 2,
                                },
                            ),
                            client_two.patch(
                                view_item_path,
                                headers={
                                    **headers,
                                    "Idempotency-Key": "view-race-two",
                                },
                                json={
                                    "pagination_spec": {"limit": 3, "offset": 0},
                                    "expected_row_version": 2,
                                },
                            ),
                        )
                assert sorted(
                    response.status_code for response in view_race_responses
                ) == [200, 409], [response.text for response in view_race_responses]
                final_view_result = next(
                    response.json()
                    for response in view_race_responses
                    if response.status_code == 200
                )
                assert final_view_result["record"]["row_version"] == 3
                stale_view = await client.patch(
                    view_item_path,
                    headers={**headers, "Idempotency-Key": "view-stale"},
                    json={"expected_row_version": 1},
                )
                assert stale_view.status_code == 409, stale_view.text

                deleted_view = await client.request(
                    "DELETE",
                    view_item_path,
                    headers={**headers, "Idempotency-Key": "view-delete"},
                    json={"expected_row_version": 3},
                )
                assert deleted_view.status_code == 200, deleted_view.text
                assert deleted_view.json()["record"] == final_view_result["record"]
                assert (
                    await client.request(
                        "DELETE",
                        view_item_path,
                        headers={**headers, "Idempotency-Key": "view-delete"},
                        json={"expected_row_version": 3},
                    )
                ).json() == deleted_view.json()

                deleted_relation = await client.request(
                    "DELETE",
                    relation_item_path,
                    headers={**headers, "Idempotency-Key": "relation-delete"},
                    json={"expected_row_version": 2},
                )
                assert deleted_relation.status_code == 200, deleted_relation.text
                assert (
                    deleted_relation.json()["record"]
                    == relation_update.json()["record"]
                )
                assert (await client.get(relation_path, headers=headers)).json() == []

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            actions = await owner.fetch(
                "SELECT action,resource_type,http_method,quota_kind "
                "FROM audit.agent_mutation WHERE workspace_id=$1 "
                "ORDER BY occurred_at,operation_id",
                workspace_id,
            )
            assert [
                tuple(row)
                for row in actions
                if row[1] in {"item_relation", "collection_view"}
            ] == [
                ("ITEM_RELATION_CREATED", "item_relation", "POST", "mutation"),
                ("ITEM_RELATION_UPDATED", "item_relation", "PATCH", "mutation"),
                ("COLLECTION_VIEW_CREATED", "collection_view", "POST", "mutation"),
                ("COLLECTION_VIEW_UPDATED", "collection_view", "PATCH", "mutation"),
                ("COLLECTION_VIEW_UPDATED", "collection_view", "PATCH", "mutation"),
                ("COLLECTION_VIEW_DELETED", "collection_view", "DELETE", "delete"),
                ("ITEM_RELATION_DELETED", "item_relation", "DELETE", "delete"),
            ]
    finally:
        pass


@pytest.mark.asyncio
async def test_agent_relation_and_view_hostile_matrix_and_races(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Prove relation/view wrappers deny hostile inputs without residue."""

    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "content-model:create",
        "content-model:read",
        "content-model:write",
        "field-definition:create",
        "field-definition:write",
        "content-item:create",
        "content-item:read",
        "relationship:write",
        "collection-view:read",
        "collection-view:create",
        "collection-view:write",
        "collection-view:delete",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Relation View Hostile Matrix Workspace"
    )
    other_token, other_workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Relation View Other Workspace"
    )
    read_only_token, _read_only_workspace_id = await _workspace_capability(
        database,
        seeded,
        ["content-item:read", "collection-view:read"],
        "Agent Relation View Read Only Workspace",
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        other_capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1",
            other_workspace_id,
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=500, mutation_quota=200, "
            "delete_quota=100 WHERE id=$1",
            capability_id,
        )
        foreign_item_id = uuid4()
        await owner.execute(
            "INSERT INTO content.content_item_base "
            '(id,site_id,type_id,slug,status,type_definition_version,"values") '
            "VALUES ($1,$2,$3,'foreign-target','DRAFT',1,'{}'::jsonb)",
            foreign_item_id,
            seeded["site_b_id"],
            seeded["type_b_id"],
        )

    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    app_one = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    app_two = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}

    async def relation_ids(source_id: UUID) -> tuple[UUID, ...]:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return tuple(
                row[0]
                for row in await cow.native.fetch(
                    "SELECT id FROM content.item_relation "
                    "WHERE source_item_id=$1 ORDER BY id",
                    source_id,
                )
            )

    async def durable_state() -> tuple[int, int, int, int]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                "WHERE workspace_id=$1),"
                "(SELECT count(*) FROM audit.agent_mutation "
                "WHERE workspace_id=$1),"
                "(SELECT mutation_used FROM control.capability WHERE id=$2),"
                "(SELECT delete_used FROM control.capability WHERE id=$2)",
                workspace_id,
                capability_id,
            )
        return tuple(row)

    async def assert_rejected_without_residue(
        response: httpx.Response,
        *,
        expected_status: int | tuple[int, ...],
        source_id: UUID,
        relations_before: tuple[UUID, ...],
        durable_before: tuple[int, int, int, int],
    ) -> None:
        expected = (
            (expected_status,) if isinstance(expected_status, int) else expected_status
        )
        assert response.status_code in expected, response.text
        assert await relation_ids(source_id) == relations_before
        assert await durable_state() == durable_before

    try:
        async with app_one.router.lifespan_context(app_one):
            async with app_two.router.lifespan_context(app_two):
                async with (
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app_one),
                        base_url="http://agent-one.test",
                    ) as client_one,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app_two),
                        base_url="http://agent-two.test",
                    ) as client_two,
                ):

                    async def create_type(
                        client: httpx.AsyncClient,
                        auth_token: str,
                        key: str,
                        idempotency_key: str,
                    ) -> UUID:
                        response = await client.post(
                            "/api/agent/v1/content-model/types",
                            headers={
                                "Authorization": f"Bearer {auth_token}",
                                "Idempotency-Key": idempotency_key,
                            },
                            json={
                                "key": key,
                                "labels": {"en": key},
                                "slug_pattern": f"/{key}/{{slug}}",
                                "settings": {},
                            },
                        )
                        assert response.status_code == 201, response.text
                        return UUID(response.json()["record"]["id"])

                    async def create_item(
                        client: httpx.AsyncClient,
                        auth_token: str,
                        type_id: UUID,
                        slug: str,
                        idempotency_key: str,
                    ) -> UUID:
                        response = await client.post(
                            f"/api/agent/v1/content-items/types/{type_id}",
                            headers={
                                "Authorization": f"Bearer {auth_token}",
                                "Idempotency-Key": idempotency_key,
                            },
                            json={
                                "type_id": str(type_id),
                                "slug": slug,
                                "status": "DRAFT",
                                "values": {},
                            },
                        )
                        assert response.status_code == 201, response.text
                        return UUID(response.json()["record"]["id"])

                    source_type_id = await create_type(
                        client_one, token, "matrix-source", "matrix-source-type"
                    )
                    target_type_id = await create_type(
                        client_one, token, "matrix-target", "matrix-target-type"
                    )
                    related_field_response = await client_one.post(
                        f"/api/agent/v1/content-model/types/{source_type_id}/fields",
                        headers={
                            **headers,
                            "Idempotency-Key": "matrix-related-field",
                        },
                        json={
                            "key": "related",
                            "label": "Related",
                            "field_type": "reference",
                            "validation": {"target_type_id": str(target_type_id)},
                        },
                    )
                    assert related_field_response.status_code == 201, (
                        related_field_response.text
                    )
                    related_field_id = UUID(
                        related_field_response.json()["record"]["id"]
                    )
                    plain_field_response = await client_one.post(
                        f"/api/agent/v1/content-model/types/{source_type_id}/fields",
                        headers={**headers, "Idempotency-Key": "matrix-plain-field"},
                        json={
                            "key": "plain",
                            "label": "Plain",
                            "field_type": "short_text",
                        },
                    )
                    assert plain_field_response.status_code == 201, (
                        plain_field_response.text
                    )
                    _plain_field_id = UUID(plain_field_response.json()["record"]["id"])
                    localized_field_response = await client_one.post(
                        f"/api/agent/v1/content-model/types/{source_type_id}/fields",
                        headers={
                            **headers,
                            "Idempotency-Key": "matrix-localized-field",
                        },
                        json={
                            "key": "localized",
                            "label": "Localized",
                            "field_type": "short_text",
                            "localized": True,
                        },
                    )
                    assert localized_field_response.status_code == 201, (
                        localized_field_response.text
                    )
                    target_field_response = await client_one.post(
                        f"/api/agent/v1/content-model/types/{target_type_id}/fields",
                        headers={
                            **headers,
                            "Idempotency-Key": "matrix-target-field",
                        },
                        json={
                            "key": "target-only",
                            "label": "Target only",
                            "field_type": "short_text",
                        },
                    )
                    assert target_field_response.status_code == 201, (
                        target_field_response.text
                    )
                    target_field_id = UUID(target_field_response.json()["record"]["id"])

                    source_id = await create_item(
                        client_one,
                        token,
                        source_type_id,
                        "source",
                        "matrix-source-item",
                    )
                    probe_source_id = await create_item(
                        client_one, token, source_type_id, "probe", "matrix-probe-item"
                    )
                    race_source_id = await create_item(
                        client_one, token, source_type_id, "race", "matrix-race-item"
                    )
                    stale_source_id = await create_item(
                        client_one, token, source_type_id, "stale", "matrix-stale-item"
                    )
                    target_one_id = await create_item(
                        client_one,
                        token,
                        target_type_id,
                        "target-one",
                        "matrix-target-one",
                    )
                    target_two_id = await create_item(
                        client_one,
                        token,
                        target_type_id,
                        "target-two",
                        "matrix-target-two",
                    )
                    target_three_id = await create_item(
                        client_one,
                        token,
                        target_type_id,
                        "target-three",
                        "matrix-target-three",
                    )
                    wrong_target_id = await create_item(
                        client_one,
                        token,
                        source_type_id,
                        "wrong-target",
                        "matrix-wrong-target",
                    )

                    other_type_id = await create_type(
                        client_two,
                        other_token,
                        "other-workspace-type",
                        "other-workspace-type",
                    )
                    other_item_id = await create_item(
                        client_two,
                        other_token,
                        other_type_id,
                        "other-workspace-item",
                        "other-workspace-item",
                    )

                    relation_path = f"/api/agent/v1/content-items/{source_id}/relations"
                    relation_payload = {
                        "field_definition_id": str(related_field_id),
                        "target_item_id": str(target_one_id),
                    }
                    relation_response = await client_one.post(
                        relation_path,
                        headers={**headers, "Idempotency-Key": "matrix-valid-relation"},
                        json=relation_payload,
                    )
                    assert relation_response.status_code == 201, relation_response.text
                    relation_result = relation_response.json()
                    relation_id = UUID(relation_result["record"]["id"])

                    async def reject_relation(
                        key: str,
                        payload: dict[str, Any],
                        source: UUID = probe_source_id,
                    ) -> None:
                        before_relations = await relation_ids(source)
                        before_durable = await durable_state()
                        response = await client_one.post(
                            f"/api/agent/v1/content-items/{source}/relations",
                            headers={**headers, "Idempotency-Key": key},
                            json=payload,
                        )
                        await assert_rejected_without_residue(
                            response,
                            expected_status=(403, 404, 422),
                            source_id=source,
                            relations_before=before_relations,
                            durable_before=before_durable,
                        )

                    await reject_relation(
                        "matrix-wrong-field",
                        {
                            "field_definition_id": str(target_field_id),
                            "target_item_id": str(target_one_id),
                        },
                    )
                    await reject_relation(
                        "matrix-wrong-target-type",
                        {
                            "field_definition_id": str(related_field_id),
                            "target_item_id": str(wrong_target_id),
                        },
                    )
                    await reject_relation(
                        "matrix-invalid-position",
                        {
                            **relation_payload,
                            "position": -1,
                        },
                    )
                    await reject_relation(
                        "matrix-metadata-array",
                        {
                            **relation_payload,
                            "metadata": [],
                        },
                    )
                    await reject_relation(
                        "matrix-metadata-marker",
                        {
                            **relation_payload,
                            "metadata": {"constructor": "prototype"},
                        },
                    )
                    await reject_relation(
                        "matrix-metadata-size",
                        {
                            **relation_payload,
                            "metadata": {"blob": "x" * 5000},
                        },
                    )
                    await reject_relation(
                        "matrix-cross-site-target",
                        {
                            **relation_payload,
                            "target_item_id": str(foreign_item_id),
                        },
                    )
                    await reject_relation(
                        "matrix-cross-workspace-target",
                        {
                            **relation_payload,
                            "target_item_id": str(other_item_id),
                        },
                    )

                    before_relations = await relation_ids(source_id)
                    before_durable = await durable_state()
                    cardinality = await client_one.post(
                        relation_path,
                        headers={**headers, "Idempotency-Key": "matrix-cardinality"},
                        json={
                            **relation_payload,
                            "target_item_id": str(target_two_id),
                        },
                    )
                    await assert_rejected_without_residue(
                        cardinality,
                        expected_status=(403, 422),
                        source_id=source_id,
                        relations_before=before_relations,
                        durable_before=before_durable,
                    )
                    before_relations = await relation_ids(source_id)
                    before_durable = await durable_state()
                    mismatch = await client_one.post(
                        relation_path,
                        headers={
                            **headers,
                            "Idempotency-Key": "matrix-valid-relation",
                        },
                        json={**relation_payload, "target_item_id": str(target_two_id)},
                    )
                    assert mismatch.status_code == 409, mismatch.text
                    assert await relation_ids(source_id) == before_relations
                    assert await durable_state() == before_durable
                    wrong_relation_path = (
                        f"/api/agent/v1/content-items/{target_one_id}"
                        f"/relations/{relation_id}"
                    )
                    wrong_relation_get = await client_one.get(
                        wrong_relation_path, headers=headers
                    )
                    assert wrong_relation_get.status_code == 404, (
                        wrong_relation_get.text
                    )

                    await _set_resource_constraints(
                        database,
                        workspace_id,
                        {
                            "allowed_type_ids": [str(target_type_id)],
                            "allowed_type_keys": ["matrix-target"],
                        },
                    )
                    denied_before = await durable_state()
                    denied_source = await client_one.get(relation_path, headers=headers)
                    assert denied_source.status_code == 403, denied_source.text
                    assert await durable_state() == denied_before
                    await _set_resource_constraints(
                        database,
                        workspace_id,
                        {
                            "allowed_type_ids": [str(source_type_id)],
                            "allowed_type_keys": ["matrix-source"],
                        },
                    )
                    denied_before = await durable_state()
                    denied_target = await client_one.post(
                        f"/api/agent/v1/content-items/{probe_source_id}/relations",
                        headers={**headers, "Idempotency-Key": "matrix-target-denied"},
                        json=relation_payload,
                    )
                    assert denied_target.status_code == 403, denied_target.text
                    assert await durable_state() == denied_before

                    await _set_resource_constraints(database, workspace_id, {})
                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        await owner.execute(
                            "UPDATE control.capability SET "
                            "mutation_quota=mutation_used "
                            "WHERE id=$1",
                            capability_id,
                        )
                    exhausted_before = await durable_state()
                    exhausted = await client_one.post(
                        f"/api/agent/v1/content-items/{probe_source_id}/relations",
                        headers={
                            **headers,
                            "Idempotency-Key": "matrix-mutation-exhausted",
                        },
                        json=relation_payload,
                    )
                    await assert_rejected_without_residue(
                        exhausted,
                        expected_status=429,
                        source_id=probe_source_id,
                        relations_before=(),
                        durable_before=exhausted_before,
                    )
                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        await owner.execute(
                            "UPDATE control.capability SET mutation_quota=200 "
                            "WHERE id=$1",
                            capability_id,
                        )

                    view_path = f"/api/agent/v1/collection-views/types/{source_type_id}"
                    valid_view_payload = {
                        "type_id": str(source_type_id),
                        "key": "matrix-valid-view",
                        "filter_spec": {"field": "plain", "op": "eq", "value": "ok"},
                        "sort_spec": {"field": "slug", "direction": "asc"},
                        "projection_spec": {"fields": ["plain"]},
                        "pagination_spec": {"limit": 10, "offset": 0},
                    }
                    valid_view_response = await client_one.post(
                        view_path,
                        headers={**headers, "Idempotency-Key": "matrix-valid-view"},
                        json=valid_view_payload,
                    )
                    assert valid_view_response.status_code == 201, (
                        valid_view_response.text
                    )
                    valid_view_result = valid_view_response.json()
                    view_id = UUID(valid_view_result["record"]["id"])

                    async def reject_view(
                        key: str, payload: dict[str, Any], expected_status: int = 422
                    ) -> None:
                        before = await durable_state()
                        response = await client_one.post(
                            view_path,
                            headers={**headers, "Idempotency-Key": key},
                            json={**valid_view_payload, **payload, "key": key},
                        )
                        assert response.status_code == expected_status, response.text
                        assert await durable_state() == before

                    await reject_view(
                        "matrix-view-unknown-field",
                        {"filter_spec": {"field": "missing", "op": "eq", "value": "x"}},
                    )
                    await reject_view(
                        "matrix-view-localized",
                        {
                            "filter_spec": {
                                "field": "localized",
                                "op": "eq",
                                "value": "x",
                            }
                        },
                    )
                    await reject_view(
                        "matrix-view-operator",
                        {"filter_spec": {"field": "plain", "op": "gt", "value": "x"}},
                    )
                    await reject_view(
                        "matrix-view-value-type",
                        {"filter_spec": {"field": "plain", "op": "eq", "value": 1}},
                    )
                    await reject_view(
                        "matrix-view-sql",
                        {
                            "filter_spec": {
                                "field": "plain",
                                "op": "eq",
                                "value": "x; SELECT 1",
                            }
                        },
                    )
                    await reject_view(
                        "matrix-view-prototype",
                        {
                            "filter_spec": {
                                "field": "plain",
                                "op": "eq",
                                "value": "__proto__",
                            }
                        },
                    )
                    await reject_view(
                        "matrix-view-clauses",
                        {
                            "filter_spec": {
                                "or": [{"status": "DRAFT"}] * 33,
                            }
                        },
                    )
                    deep_filter: dict[str, Any] = {"status": "DRAFT"}
                    for _ in range(6):
                        deep_filter = {"and": [deep_filter]}
                    await reject_view("matrix-view-depth", {"filter_spec": deep_filter})
                    await reject_view(
                        "matrix-view-size",
                        {
                            "filter_spec": {
                                "field": "plain",
                                "op": "eq",
                                "value": "x" * 5000,
                            }
                        },
                    )
                    await reject_view(
                        "matrix-view-limit",
                        {"pagination_spec": {"limit": 101, "offset": 0}},
                    )
                    await reject_view(
                        "matrix-view-offset",
                        {"pagination_spec": {"limit": 10, "offset": 10001}},
                    )
                    await reject_view(
                        "matrix-view-float-pagination",
                        {"pagination_spec": {"limit": 1.5, "offset": 0}},
                    )
                    await reject_view(
                        "matrix-view-projection-duplicate",
                        {"projection_spec": {"fields": ["plain", "plain"]}},
                    )
                    await reject_view(
                        "matrix-view-projection-localized",
                        {"projection_spec": {"fields": ["localized"]}},
                    )
                    await reject_view(
                        "matrix-view-projection-unknown",
                        {"projection_spec": {"fields": ["missing"]}},
                    )
                    duplicate_before = await durable_state()
                    duplicate = await client_one.post(
                        view_path,
                        headers={**headers, "Idempotency-Key": "matrix-view-duplicate"},
                        json=valid_view_payload,
                    )
                    assert duplicate.status_code == 409, duplicate.text
                    assert await durable_state() == duplicate_before

                    await _set_resource_constraints(
                        database, workspace_id, {"delete_enabled": False}
                    )
                    delete_disabled_before = await durable_state()
                    delete_disabled = await client_one.request(
                        "DELETE",
                        f"/api/agent/v1/content-items/{source_id}/relations/{relation_id}",
                        headers={
                            **headers,
                            "Idempotency-Key": "matrix-delete-disabled",
                        },
                        json={"expected_row_version": 1},
                    )
                    assert delete_disabled.status_code == 403, delete_disabled.text
                    assert await durable_state() == delete_disabled_before
                    await _set_resource_constraints(
                        database,
                        workspace_id,
                        {"delete_enabled": True, "max_deletes": 0},
                    )
                    delete_limit_before = await durable_state()
                    delete_limited = await client_one.request(
                        "DELETE",
                        f"/api/agent/v1/content-items/{source_id}/relations/{relation_id}",
                        headers={**headers, "Idempotency-Key": "matrix-delete-limited"},
                        json={"expected_row_version": 1},
                    )
                    assert delete_limited.status_code == 429, delete_limited.text
                    assert await durable_state() == delete_limit_before
                    await _set_resource_constraints(database, workspace_id, {})

                    read_only_create = await client_one.post(
                        f"/api/agent/v1/content-items/{source_id}/relations",
                        headers={
                            "Authorization": f"Bearer {read_only_token}",
                            "Idempotency-Key": "matrix-read-only-relation",
                        },
                        json=relation_payload,
                    )
                    assert read_only_create.status_code == 403, read_only_create.text
                    read_only_view = await client_one.post(
                        view_path,
                        headers={
                            "Authorization": f"Bearer {read_only_token}",
                            "Idempotency-Key": "matrix-read-only-view",
                        },
                        json=valid_view_payload,
                    )
                    assert read_only_view.status_code == 403, read_only_view.text

                    direct_calls: tuple[tuple[str, tuple[object, ...]], ...] = (
                        (
                            "SELECT * FROM content.slaif_agent_item_relation_list("
                            "$1,$2)",
                            (seeded["site_id"], source_id),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_item_relation_get("
                            "$1,$2,$3)",
                            (seeded["site_id"], source_id, relation_id),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_item_relation_create("
                            "$1,$2,$3,$4,$5,$6)",
                            (
                                seeded["site_id"],
                                probe_source_id,
                                related_field_id,
                                target_two_id,
                                0,
                                "{}",
                            ),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_item_relation_update("
                            "$1,$2,$3,$4,$5,$6,$7)",
                            (
                                seeded["site_id"],
                                source_id,
                                relation_id,
                                target_two_id,
                                0,
                                "{}",
                                1,
                            ),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_item_relation_delete("
                            "$1,$2,$3,$4)",
                            (seeded["site_id"], source_id, relation_id, 1),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_list("
                            "$1,$2)",
                            (seeded["site_id"], source_type_id),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_get("
                            "$1,$2)",
                            (seeded["site_id"], view_id),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_create("
                            "$1,$2,$3,$4,$5,$6,$7,$8)",
                            (
                                seeded["site_id"],
                                source_type_id,
                                "direct-view",
                                "{}",
                                "{}",
                                "{}",
                                "{}",
                                1,
                            ),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_current("
                            "$1,$2,$3)",
                            (seeded["site_id"], view_id, "collection-view:write"),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_fields("
                            "$1,$2,$3)",
                            (
                                seeded["site_id"],
                                source_type_id,
                                "collection-view:create",
                            ),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_update("
                            "$1,$2,$3,$4,$5,$6,$7,$8)",
                            (
                                seeded["site_id"],
                                view_id,
                                "{}",
                                "{}",
                                "{}",
                                "{}",
                                1,
                                1,
                            ),
                        ),
                        (
                            "SELECT * FROM content.slaif_agent_collection_view_delete("
                            "$1,$2,$3)",
                            (seeded["site_id"], view_id, 1),
                        ),
                    )
                    for sql, arguments in direct_calls:
                        async with _asyncpg_cow_session(
                            agent_pool,
                            session_id=workspace_id,
                            operation_id=uuid4(),
                        ) as cow:
                            with pytest.raises(
                                asyncpg.PostgresError,
                                match="AGENT_CAPABILITY_CONTEXT_REQUIRED",
                            ):
                                await cow.native.fetch(sql, *arguments)
                            await cow.rollback()

                    async with agent_pool.acquire() as connection:
                        with pytest.raises(asyncpg.InsufficientPrivilegeError):
                            await connection.fetch(
                                "SELECT * FROM content.slaif_agent_relation_assert("
                                "$1,$2,$3,$4,$5,$6)",
                                seeded["site_id"],
                                source_id,
                                related_field_id,
                                target_one_id,
                                "relationship:write",
                                True,
                            )
                        with pytest.raises(asyncpg.InsufficientPrivilegeError):
                            await connection.fetch(
                                "SELECT * FROM content.slaif_agent_collection_view_"
                                "query_validate("
                                "$1,$2,$3,$4,$5)",
                                source_type_id,
                                "{}",
                                "{}",
                                "{}",
                                "{}",
                            )
                        await connection.execute(
                            "SELECT set_config('app.session_id',$1,true)",
                            str(workspace_id),
                        )
                        await connection.execute(
                            "SELECT set_config('app.operation_id',$1,true)",
                            str(uuid4()),
                        )
                        await connection.execute(
                            "SELECT set_config('app.capability_id',$1,true)",
                            str(other_capability_id),
                        )
                        with pytest.raises(asyncpg.PostgresError):
                            await connection.fetch(
                                "SELECT * FROM content.slaif_agent_item_relation_list("
                                "$1,$2)",
                                seeded["site_id"],
                                source_id,
                            )

                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        neutral_type_id = uuid4()
                        _neutral_field_id = uuid4()
                        await owner.execute(
                            "INSERT INTO content.content_type_base "
                            '(id,site_id,"key",labels,slug_pattern,status,'
                            "definition_version,settings) "
                            "VALUES ($1,$2,'neutral-query',$3::jsonb,"
                            "'/neutral/{slug}','ACTIVE',1,'{}'::jsonb)",
                            neutral_type_id,
                            seeded["site_id"],
                            json.dumps({"en": "Neutral query"}),
                        )
                        await owner.execute(
                            "INSERT INTO content.field_definition_base "
                            '(id,site_id,type_id,"key",label,field_type,required,'
                            'localized,cardinality,"position",validation,ui_options,'
                            "definition_version) "
                            "VALUES ($1,$2,$3,'neutral','Neutral','short_text',"
                            "false,false,1,0,'{}'::jsonb,'{}'::jsonb,1)",
                            _neutral_field_id,
                            seeded["site_id"],
                            neutral_type_id,
                        )
                        await owner.fetchval(
                            "SELECT content.slaif_agent_collection_view_"
                            "query_validate("
                            "$1,$2::jsonb,$3::jsonb,$4::jsonb,$5::jsonb)",
                            neutral_type_id,
                            '{"field":"neutral","op":"eq","value":"ok"}',
                            '{"field":"slug","direction":"asc"}',
                            "{}",
                            '{"limit":10,"offset":0}',
                        )
                        with pytest.raises(
                            asyncpg.PostgresError, match="QUERY_FILTER_VALUE"
                        ):
                            await owner.fetchval(
                                "SELECT content.slaif_agent_collection_view_"
                                "query_validate("
                                "$1,$2::jsonb,$3::jsonb,$4::jsonb,$5::jsonb)",
                                neutral_type_id,
                                '{"field":"neutral","op":"eq","value":1}',
                                '{"field":"slug"}',
                                "{}",
                                '{"limit":10,"offset":0}',
                            )
                        with pytest.raises(
                            asyncpg.PostgresError, match="QUERY_PAGINATION"
                        ):
                            await owner.fetchval(
                                "SELECT content.slaif_agent_collection_view_"
                                "query_validate("
                                "$1,$2::jsonb,$3::jsonb,$4::jsonb,$5::jsonb)",
                                neutral_type_id,
                                "{}",
                                "{}",
                                "{}",
                                '{"limit":1.5,"offset":0}',
                            )

                    lock_context = _asyncpg_cow_session(
                        agent_pool, session_id=workspace_id, operation_id=uuid4()
                    )
                    lock_holder = await lock_context.__aenter__()
                    try:
                        await lock_holder.native.fetchval(
                            "SELECT pg_advisory_xact_lock(hashtextextended($1,994))",
                            f"{workspace_id}:{race_source_id}:{related_field_id}_item_relation",
                        )
                        cancellation_before = await durable_state()
                        cancellation_task = asyncio.create_task(
                            client_one.post(
                                f"/api/agent/v1/content-items/{race_source_id}/relations",
                                headers={
                                    **headers,
                                    "Idempotency-Key": "matrix-cancelled-relation",
                                },
                                json={
                                    "field_definition_id": str(related_field_id),
                                    "target_item_id": str(target_one_id),
                                },
                            )
                        )
                        await asyncio.sleep(0.2)
                        assert not cancellation_task.done()
                        cancellation_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await cancellation_task
                    finally:
                        await lock_context.__aexit__(None, None, None)
                    assert await relation_ids(race_source_id) == ()
                    assert await durable_state() == cancellation_before

                    race_path = (
                        f"/api/agent/v1/content-items/{race_source_id}/relations"
                    )
                    race_responses = await asyncio.gather(
                        client_one.post(
                            race_path,
                            headers={
                                **headers,
                                "Idempotency-Key": "matrix-race-create-one",
                            },
                            json={
                                "field_definition_id": str(related_field_id),
                                "target_item_id": str(target_two_id),
                            },
                        ),
                        client_two.post(
                            race_path,
                            headers={
                                **headers,
                                "Idempotency-Key": "matrix-race-create-two",
                            },
                            json={
                                "field_definition_id": str(related_field_id),
                                "target_item_id": str(target_three_id),
                            },
                        ),
                    )
                    assert [response.status_code for response in race_responses].count(
                        201
                    ) == 1, [response.text for response in race_responses]
                    assert (
                        sum(
                            response.status_code in {409, 422}
                            for response in race_responses
                        )
                        == 1
                    ), [response.text for response in race_responses]
                    race_relation_id = UUID(
                        next(
                            response.json()["record"]["id"]
                            for response in race_responses
                            if response.status_code == 201
                        )
                    )
                    assert len(await relation_ids(race_source_id)) == 1
                    before_update_race = await durable_state()
                    update_race = await asyncio.gather(
                        client_one.patch(
                            f"{race_path}/{race_relation_id}",
                            headers={
                                **headers,
                                "Idempotency-Key": "matrix-race-update-one",
                            },
                            json={
                                "metadata": {"winner": "one"},
                                "expected_row_version": 1,
                            },
                        ),
                        client_two.patch(
                            f"{race_path}/{race_relation_id}",
                            headers={
                                **headers,
                                "Idempotency-Key": "matrix-race-update-two",
                            },
                            json={
                                "metadata": {"winner": "two"},
                                "expected_row_version": 1,
                            },
                        ),
                    )
                    assert sorted(response.status_code for response in update_race) == [
                        200,
                        409,
                    ], [response.text for response in update_race]
                    winning_update = next(
                        response.json()
                        for response in update_race
                        if response.status_code == 200
                    )
                    assert winning_update["record"]["row_version"] == 2
                    after_update_race = await durable_state()
                    assert after_update_race == (
                        before_update_race[0] + 1,
                        before_update_race[1] + 1,
                        before_update_race[2] + 1,
                        before_update_race[3],
                    )
                    async with owner_connection(
                        database.settings.resolved_owner_dsn(),
                        expected_database=database.name,
                    ) as owner:
                        actions = await owner.fetch(
                            "SELECT action,http_method,response_status,quota_kind "
                            "FROM audit.agent_mutation WHERE workspace_id=$1 "
                            "AND resource_id=$2 ORDER BY operation_id",
                            workspace_id,
                            race_relation_id,
                        )
                        assert [tuple(row) for row in actions] == [
                            ("ITEM_RELATION_CREATED", "POST", 201, "mutation"),
                            ("ITEM_RELATION_UPDATED", "PATCH", 200, "mutation"),
                        ]

                    later_field = await client_one.post(
                        f"/api/agent/v1/content-model/types/{source_type_id}/fields",
                        headers={**headers, "Idempotency-Key": "matrix-later-field"},
                        json={
                            "key": "later",
                            "label": "Later",
                            "field_type": "short_text",
                        },
                    )
                    assert later_field.status_code == 201, later_field.text
                    stale_relation = await client_one.post(
                        f"/api/agent/v1/content-items/{stale_source_id}/relations",
                        headers={**headers, "Idempotency-Key": "matrix-stale-relation"},
                        json=relation_payload,
                    )
                    assert stale_relation.status_code == 422, stale_relation.text

                    stale_view_before = await durable_state()
                    stale_view = await client_one.patch(
                        f"/api/agent/v1/collection-views/{view_id}",
                        headers={**headers, "Idempotency-Key": "matrix-stale-view"},
                        json={
                            "pagination_spec": {"limit": 9, "offset": 0},
                            "expected_row_version": 1,
                        },
                    )
                    assert stale_view.status_code == 422, stale_view.text
                    assert await durable_state() == stale_view_before
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_stale_dependencies_are_discoverable_and_deletable_via_rest(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "content-model:create",
        "content-model:read",
        "content-model:delete",
        "field-definition:create",
        "field-definition:delete",
        "content-item:create",
        "content-item:read",
        "content-item:delete",
        "translation:read",
        "translation:write",
        "relationship:write",
        "collection-view:read",
        "collection-view:create",
        "collection-view:write",
        "collection-view:delete",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Agent Stale Cleanup Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=30, "
            "delete_quota=20 WHERE id=$1",
            capability_id,
        )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                created_type = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "stale-type"},
                    json={
                        "key": "stale-cleanup",
                        "labels": {"en": "Stale cleanup"},
                        "slug_pattern": "/stale/{slug}",
                        "settings": {},
                    },
                )
                assert created_type.status_code == 201, created_type.text
                type_id = UUID(created_type.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(type_id)],
                        "allowed_type_keys": ["stale-cleanup"],
                        "delete_enabled": True,
                    },
                )
                relation_field = await client.post(
                    f"/api/agent/v1/content-model/types/{type_id}/fields",
                    headers={**headers, "Idempotency-Key": "stale-relation-field"},
                    json={
                        "key": "related",
                        "label": "Related",
                        "field_type": "reference",
                    },
                )
                title_field = await client.post(
                    f"/api/agent/v1/content-model/types/{type_id}/fields",
                    headers={**headers, "Idempotency-Key": "stale-title-field"},
                    json={
                        "key": "title",
                        "label": "Title",
                        "field_type": "short_text",
                        "localized": True,
                    },
                )
                assert relation_field.status_code == title_field.status_code == 201
                relation_field_id = UUID(relation_field.json()["record"]["id"])
                title_field_id = UUID(title_field.json()["record"]["id"])

                async def create_item(slug: str) -> UUID:
                    response = await client.post(
                        f"/api/agent/v1/content-items/types/{type_id}",
                        headers={**headers, "Idempotency-Key": f"stale-item-{slug}"},
                        json={
                            "type_id": str(type_id),
                            "slug": slug,
                            "status": "DRAFT",
                            "values": {},
                        },
                    )
                    assert response.status_code == 201, response.text
                    return UUID(response.json()["record"]["id"])

                source_id = await create_item("source")
                target_id = await create_item("target")
                relation_path = f"/api/agent/v1/content-items/{source_id}/relations"
                relation = await client.post(
                    relation_path,
                    headers={**headers, "Idempotency-Key": "stale-relation"},
                    json={
                        "field_definition_id": str(relation_field_id),
                        "target_item_id": str(target_id),
                    },
                )
                assert relation.status_code == 201, relation.text
                relation_id = UUID(relation.json()["record"]["id"])
                translation_path = (
                    f"/api/agent/v1/content-items/{source_id}/translations"
                )
                translation = await client.post(
                    translation_path,
                    headers={**headers, "Idempotency-Key": "stale-translation"},
                    json={
                        "locale": "en",
                        "localized_values": {"title": "Before change"},
                    },
                )
                assert translation.status_code == 201, translation.text
                translation_id = UUID(translation.json()["record"]["id"])
                view_path = f"/api/agent/v1/collection-views/types/{type_id}"
                view = await client.post(
                    view_path,
                    headers={**headers, "Idempotency-Key": "stale-view"},
                    json={
                        "type_id": str(type_id),
                        "key": "all",
                        "filter_spec": {},
                        "sort_spec": {"field": "slug"},
                        "projection_spec": {},
                        "pagination_spec": {"limit": 10, "offset": 0},
                    },
                )
                assert view.status_code == 201, view.text
                view_id = UUID(view.json()["record"]["id"])

                later_field = await client.post(
                    f"/api/agent/v1/content-model/types/{type_id}/fields",
                    headers={**headers, "Idempotency-Key": "stale-later-field"},
                    json={
                        "key": "later",
                        "label": "Later",
                        "field_type": "short_text",
                    },
                )
                assert later_field.status_code == 201, later_field.text

                stale_items = await client.get(
                    f"/api/agent/v1/content-items/types/{type_id}", headers=headers
                )
                assert stale_items.status_code == 200
                assert {record["id"] for record in stale_items.json()} == {
                    str(source_id),
                    str(target_id),
                }
                assert (await client.get(relation_path, headers=headers)).json()[0][
                    "id"
                ] == str(relation_id)
                assert (await client.get(translation_path, headers=headers)).json()[0][
                    "id"
                ] == str(translation_id)
                assert (await client.get(view_path, headers=headers)).json()[0][
                    "id"
                ] == str(view_id)

                deleted_relation = await client.request(
                    "DELETE",
                    f"{relation_path}/{relation_id}",
                    headers={**headers, "Idempotency-Key": "stale-relation-delete"},
                    json={"expected_row_version": 1},
                )
                deleted_translation = await client.request(
                    "DELETE",
                    f"{translation_path}/{translation_id}",
                    headers={
                        **headers,
                        "Idempotency-Key": "stale-translation-delete",
                    },
                    json={"expected_row_version": 1},
                )
                deleted_view = await client.request(
                    "DELETE",
                    f"/api/agent/v1/collection-views/{view_id}",
                    headers={**headers, "Idempotency-Key": "stale-view-delete"},
                    json={"expected_row_version": 1},
                )
                assert (
                    deleted_relation.status_code,
                    deleted_translation.status_code,
                    deleted_view.status_code,
                ) == (200, 200, 200)

                for item_id, key in ((source_id, "source"), (target_id, "target")):
                    deleted_item = await client.request(
                        "DELETE",
                        f"/api/agent/v1/content-items/{item_id}",
                        headers={**headers, "Idempotency-Key": f"stale-delete-{key}"},
                        json={"expected_row_version": 1},
                    )
                    assert deleted_item.status_code == 200, deleted_item.text

                for field_id, key in (
                    (relation_field_id, "related"),
                    (title_field_id, "title"),
                    (UUID(later_field.json()["record"]["id"]), "later"),
                ):
                    deleted_field = await client.request(
                        "DELETE",
                        f"/api/agent/v1/content-model/types/{type_id}/fields/{field_id}",
                        headers={**headers, "Idempotency-Key": f"stale-field-{key}"},
                        json={"expected_definition_version": 1},
                    )
                    assert deleted_field.status_code == 200, deleted_field.text
                current_type = await client.get(
                    f"/api/agent/v1/content-model/types/{type_id}", headers=headers
                )
                assert current_type.status_code == 200
                deleted_type = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{type_id}",
                    headers={**headers, "Idempotency-Key": "stale-type-delete"},
                    json={
                        "expected_definition_version": current_type.json()[
                            "definition_version"
                        ]
                    },
                )
                assert deleted_type.status_code == 200, deleted_type.text
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_item_base WHERE site_id=$1",
                    seeded["site_id"],
                )
                == 0
            )
    finally:
        pass


@pytest.mark.asyncio
async def test_agent_semantic_reads_use_cow_overlay_fallback_and_isolation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    token, seeded = await _seed(database)
    canonical_type_id = UUID("00000000-0000-0000-0000-000000000691")
    tombstone_type_id = UUID("00000000-0000-0000-0000-000000000692")
    canonical_field_id = UUID("00000000-0000-0000-0000-000000000694")
    canonical_item_id = UUID("00000000-0000-0000-0000-000000000695")
    canonical_page_id = UUID("00000000-0000-0000-0000-000000000696")
    canonical_node_id = UUID("00000000-0000-0000-0000-000000000697")
    canonical_media_id = UUID("00000000-0000-0000-0000-000000000698")
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            """
            INSERT INTO content.content_type_base (
                id, site_id, "key", labels, slug_pattern, status,
                definition_version, settings
            ) VALUES ($1, $2, 'canonical-type', $3::jsonb, '/canonical/{slug}',
                      'ACTIVE', 1, '{}'::jsonb)
            """,
            canonical_type_id,
            seeded["site_id"],
            json.dumps({"en": "Canonical"}),
        )
        await owner.execute(
            """
            INSERT INTO content.content_type_base (
                id, site_id, "key", labels, slug_pattern, status,
                definition_version, settings
            ) VALUES ($1, $2, 'tombstone-type', $3::jsonb, '/tombstone/{slug}',
                      'ACTIVE', 1, '{}'::jsonb)
            """,
            tombstone_type_id,
            seeded["site_id"],
            json.dumps({"en": "Tombstone canonical"}),
        )
        await owner.execute(
            """
            INSERT INTO content.field_definition_base (
                id, type_id, "key", label, field_type, required, localized,
                cardinality, "position", validation, ui_options, definition_version
            ) VALUES ($1, $2, 'canonical-title', 'Canonical title', 'short_text',
                      false, false, 1, 0, '{}'::jsonb, '{}'::jsonb, 1)
            """,
            canonical_field_id,
            canonical_type_id,
        )
        await owner.execute(
            """
            INSERT INTO content.content_item_base (
                id, site_id, type_id, slug, status, type_definition_version,
                "values", row_version
            ) VALUES ($1, $2, $3, 'canonical-item', 'DRAFT', 1,
                      '{"canonical-title":"Canonical value"}'::jsonb, 1)
            """,
            canonical_item_id,
            seeded["site_id"],
            canonical_type_id,
        )
        await owner.execute(
            """
            INSERT INTO content.page_base (
                id, site_id, slug, title, status, locale, row_version
            ) VALUES ($1, $2, 'canonical-page', 'Canonical page', 'DRAFT', 'en', 1)
            """,
            canonical_page_id,
            seeded["site_id"],
        )
        await owner.execute(
            """
            INSERT INTO content.page_composition_base (
                id, site_id, page_id, component_type, schema_version,
                parent_id, slot_key, order_key, props
            ) VALUES ($1, $2, $3, 'Heading', '1', NULL, 'default', 0,
                      '{"text":"Canonical heading"}'::jsonb)
            """,
            canonical_node_id,
            seeded["site_id"],
            canonical_page_id,
        )
        await owner.execute(
            """
            INSERT INTO content.media_asset_base (
                id, site_id, uploaded_by, filename, mime_type, size_bytes,
                content_hash, storage_key, alt_text, metadata
            ) VALUES ($1, $2, NULL, 'canonical.png', 'image/png', 4,
                      'canonical-hash', 'staging/canonical.png',
                      'Canonical image', '{}'::jsonb)
            """,
            canonical_media_id,
            seeded["site_id"],
        )

    read_scopes = [
        "site:read",
        "content-model:read",
        "content-item:read",
        "page:read",
        "composition:read",
        "media:read",
    ]
    token_b, workspace_b = await _workspace_capability(
        database, seeded, read_scopes, "Agent Read Workspace B"
    )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    workspace_a = seeded["workspace_id"]
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}
                type_response = await client.post(
                    "/api/agent/v1/content-model/types",
                    json={
                        "key": "workspace-type",
                        "labels": {"en": "Workspace type"},
                        "slug_pattern": "/workspace/{slug}",
                        "settings": {},
                    },
                    headers={**headers, "Idempotency-Key": "read-chain-type"},
                )
                assert type_response.status_code == 201, type_response.text
                workspace_type_id = type_response.json()["record"]["id"]
                field_response = await client.post(
                    f"/api/agent/v1/content-model/types/{workspace_type_id}/fields",
                    json={
                        "key": "title",
                        "label": "Title",
                        "field_type": "short_text",
                    },
                    headers={**headers, "Idempotency-Key": "read-chain-field"},
                )
                assert field_response.status_code == 201, field_response.text
                item_response = await client.post(
                    f"/api/agent/v1/content-items/types/{workspace_type_id}",
                    json={
                        "type_id": workspace_type_id,
                        "slug": "workspace-item",
                        "values": {"title": "Workspace item"},
                    },
                    headers={**headers, "Idempotency-Key": "read-chain-item"},
                )
                assert item_response.status_code == 201, item_response.text
                page_response = await client.post(
                    "/api/agent/v1/pages/",
                    json={"slug": "workspace-page", "title": "Workspace page"},
                    headers={**headers, "Idempotency-Key": "read-chain-page"},
                )
                assert page_response.status_code == 201, page_response.text
                workspace_page_id = page_response.json()["record"]["id"]
                component_response = await client.post(
                    f"/api/agent/v1/pages/{workspace_page_id}/components",
                    json={"component_type": "Heading", "props": {"text": "Workspace"}},
                    headers={
                        **headers,
                        "Idempotency-Key": "read-chain-component",
                    },
                )
                assert component_response.status_code == 201, component_response.text

                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    durable_before_reads = tuple(
                        await owner.fetchrow(
                            "SELECT "
                            "(SELECT count(*) FROM control.agent_idempotency "
                            "WHERE workspace_id = $1), "
                            "(SELECT count(*) FROM audit.agent_mutation "
                            "WHERE workspace_id = $1)",
                            workspace_a,
                        )
                    )

                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    operations_before_reads = await reviewer.operations(
                        workspace_a, schema="content"
                    )

                async with asyncpg_cow_session(
                    agent_pool, session_id=workspace_a, operation_id=uuid4()
                ) as cow:
                    await cow.validate_context()
                    await cow.native.execute(
                        "UPDATE content.content_type SET labels = $1::jsonb "
                        "WHERE id = $2",
                        json.dumps({"en": "Overlay"}),
                        canonical_type_id,
                    )

                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    operations_after_overlay = await reviewer.operations(
                        workspace_a, schema="content"
                    )

                async with asyncpg_cow_session(
                    agent_pool, session_id=workspace_a, operation_id=uuid4()
                ) as cow:
                    await cow.validate_context()
                    await cow.native.execute(
                        "DELETE FROM content.content_type WHERE id = $1",
                        tombstone_type_id,
                    )

                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    operations_after_tombstone = await reviewer.operations(
                        workspace_a, schema="content"
                    )

                listed_types = await client.get(
                    "/api/agent/v1/content-model/types", headers=headers
                )
                assert listed_types.status_code == 200, listed_types.text
                listed_type_ids = {item["id"] for item in listed_types.json()}
                assert str(canonical_type_id) in listed_type_ids
                assert workspace_type_id in listed_type_ids
                assert str(tombstone_type_id) not in listed_type_ids
                assert all(
                    item["site_id"] == str(seeded["site_id"])
                    for item in listed_types.json()
                )

                overlay_type = await client.get(
                    f"/api/agent/v1/content-model/types/{canonical_type_id}",
                    headers=headers,
                )
                assert overlay_type.status_code == 200, overlay_type.text
                assert overlay_type.json()["labels"] == {"en": "Overlay"}

                tombstone_from_a = await client.get(
                    f"/api/agent/v1/content-model/types/{tombstone_type_id}",
                    headers=headers,
                )
                assert tombstone_from_a.status_code == 404, tombstone_from_a.text
                assert tombstone_from_a.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

                tombstone_from_b = await client.get(
                    f"/api/agent/v1/content-model/types/{tombstone_type_id}",
                    headers={"Authorization": f"Bearer {token_b}"},
                )
                assert tombstone_from_b.status_code == 200, tombstone_from_b.text
                assert tombstone_from_b.json()["labels"] == {
                    "en": "Tombstone canonical"
                }

                fields = await client.get(
                    f"/api/agent/v1/content-model/types/{canonical_type_id}/fields",
                    headers=headers,
                )
                assert fields.status_code == 200, fields.text
                assert fields.json()[0]["id"] == str(canonical_field_id)

                items = await client.get(
                    f"/api/agent/v1/content-items/types/{canonical_type_id}",
                    headers=headers,
                )
                assert items.status_code == 200, items.text
                assert items.json()[0]["id"] == str(canonical_item_id)

                pages = await client.get("/api/agent/v1/pages/", headers=headers)
                assert pages.status_code == 200, pages.text
                assert str(canonical_page_id) in {page["id"] for page in pages.json()}

                components = await client.get(
                    f"/api/agent/v1/pages/{canonical_page_id}/components",
                    headers=headers,
                )
                assert components.status_code == 200, components.text
                assert components.json()[0]["id"] == str(canonical_node_id)

                media = await client.get("/api/agent/v1/media/", headers=headers)
                assert media.status_code == 200, media.text
                assert media.json()[0]["id"] == str(canonical_media_id)

                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    assert await owner.fetchval(
                        'SELECT labels = \'{"en":"Canonical"}\'::jsonb '
                        "FROM content.content_type_base WHERE id = $1",
                        canonical_type_id,
                    )
                    assert await owner.fetchval(
                        'SELECT labels = \'{"en":"Tombstone canonical"}\'::jsonb '
                        "FROM content.content_type_base WHERE id = $1",
                        tombstone_type_id,
                    )
                    durable_after_reads = tuple(
                        await owner.fetchrow(
                            "SELECT "
                            "(SELECT count(*) FROM control.agent_idempotency "
                            "WHERE workspace_id = $1), "
                            "(SELECT count(*) FROM audit.agent_mutation "
                            "WHERE workspace_id = $1)",
                            workspace_a,
                        )
                    )
                assert durable_after_reads == durable_before_reads
                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    assert (
                        await reviewer.operations(workspace_a, schema="content")
                        == operations_after_tombstone
                    )
                    assert operations_after_overlay != operations_before_reads
                    assert operations_after_tombstone != operations_after_overlay

                foreign_fields = await client.get(
                    f"/api/agent/v1/content-model/types/{seeded['type_b_id']}/fields",
                    headers=headers,
                )
                foreign_type = await client.get(
                    f"/api/agent/v1/content-model/types/{seeded['type_b_id']}",
                    headers=headers,
                )
                foreign_items = await client.get(
                    f"/api/agent/v1/content-items/types/{seeded['type_b_id']}",
                    headers=headers,
                )
                foreign_components = await client.get(
                    f"/api/agent/v1/pages/{seeded['page_b_id']}/components",
                    headers=headers,
                )
                for response in (
                    foreign_type,
                    foreign_fields,
                    foreign_items,
                    foreign_components,
                ):
                    assert response.status_code == 404, response.text
                    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
                    assert str(seeded["site_b_id"]) not in response.text

                workspace_b_type_id = UUID("00000000-0000-0000-0000-000000000693")
                async with asyncpg_cow_session(
                    agent_pool, session_id=workspace_b, operation_id=uuid4()
                ) as cow:
                    await cow.validate_context()
                    await cow.native.execute(
                        "INSERT INTO content.content_type "
                        '(id, site_id, "key", labels, slug_pattern) '
                        "VALUES ($1, $2, 'workspace-type', $3::jsonb, '/b/{slug}')",
                        workspace_b_type_id,
                        seeded["site_id"],
                        json.dumps({"en": "B only"}),
                    )

                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    workspace_b_operations = await reviewer.operations(
                        workspace_b, schema="content"
                    )
                types_from_a = await client.get(
                    "/api/agent/v1/content-model/types", headers=headers
                )
                assert not any(
                    item["labels"] == {"en": "B only"} for item in types_from_a.json()
                )
                types_from_b = await client.get(
                    "/api/agent/v1/content-model/types",
                    headers={"Authorization": f"Bearer {token_b}"},
                )
                assert types_from_b.status_code == 200, types_from_b.text
                workspace_b_type = next(
                    item
                    for item in types_from_b.json()
                    if item["key"] == "workspace-type"
                )
                assert workspace_b_type["labels"] == {"en": "B only"}
                workspace_b_from_a = await client.get(
                    f"/api/agent/v1/content-model/types/{workspace_b_type_id}",
                    headers=headers,
                )
                assert workspace_b_from_a.status_code == 404, workspace_b_from_a.text
                workspace_b_from_b = await client.get(
                    f"/api/agent/v1/content-model/types/{workspace_b_type_id}",
                    headers={"Authorization": f"Bearer {token_b}"},
                )
                assert workspace_b_from_b.status_code == 200, workspace_b_from_b.text
                assert workspace_b_from_b.json()["labels"] == {"en": "B only"}
                async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
                    assert (
                        await reviewer.operations(workspace_b, schema="content")
                        == workspace_b_operations
                    )

                insufficient = await _capability_with_scopes(
                    database, seeded, ["site:read"]
                )
                insufficient_headers = {"Authorization": f"Bearer {insufficient}"}
                read_paths = (
                    "/api/agent/v1/content-model/types",
                    f"/api/agent/v1/content-model/types/{canonical_type_id}",
                    f"/api/agent/v1/content-model/types/{canonical_type_id}/fields",
                    f"/api/agent/v1/content-items/types/{canonical_type_id}",
                    "/api/agent/v1/pages/",
                    f"/api/agent/v1/pages/{canonical_page_id}/components",
                    "/api/agent/v1/media/",
                )
                for path in read_paths:
                    denied = await client.get(path, headers=insufficient_headers)
                    assert denied.status_code == 403, (path, denied.text)
                    assert denied.json()["error"]["code"] == "AUTHORIZATION_DENIED"

                for path in (
                    "/api/agent/v1/content-model/types/not-a-uuid/fields",
                    "/api/agent/v1/pages/not-a-uuid/components",
                ):
                    malformed = await client.get(path, headers=headers)
                    assert malformed.status_code == 422, malformed.text

                async with agent_pool.acquire() as agent:
                    with pytest.raises(asyncpg.PostgresError):
                        await agent.fetch(
                            "SELECT * FROM content.slaif_agent_content_type_list($1)",
                            seeded["site_id"],
                        )
                    assert not await agent.fetchval(
                        "SELECT has_function_privilege(current_user, "
                        "'content.slaif_content_type_list(uuid)', 'EXECUTE')"
                    )
                    assert not await agent.fetchval(
                        "SELECT has_function_privilege(current_user, "
                        "'control.slaif_agent_require_cow_site(uuid)', 'EXECUTE')"
                    )
                    with pytest.raises(asyncpg.InsufficientPrivilegeError):
                        await agent.fetch("SELECT * FROM content.content_type_base")

                forged_session_id = uuid4()
                async with asyncpg_cow_session(
                    agent_pool, session_id=forged_session_id, operation_id=uuid4()
                ) as cow:
                    await cow.validate_context()
                    with pytest.raises(asyncpg.PostgresError):
                        await cow.native.fetch(
                            "SELECT * FROM content.slaif_agent_content_type_list($1)",
                            seeded["site_id"],
                        )
                    await cow.rollback()
                async with agent_pool.acquire() as agent:
                    forged_context = await agent.fetchrow(
                        "SELECT current_setting('app.session_id', true), "
                        "current_setting('app.operation_id', true), "
                        "current_setting('app.visible_operations', true)"
                    )
                    assert all(value in (None, "") for value in forged_context)

                async with asyncpg_cow_session(
                    agent_pool, session_id=workspace_a, operation_id=uuid4()
                ) as cow:
                    await cow.validate_context()
                    with pytest.raises(asyncpg.PostgresError):
                        await cow.native.fetch(
                            "SELECT * FROM content.slaif_agent_content_type_list($1)",
                            seeded["site_b_id"],
                        )
                    await cow.rollback()

                grant_signatures = (
                    "content.slaif_agent_content_type_list(uuid)",
                    "content.slaif_agent_content_type_get(uuid,uuid)",
                    "content.slaif_agent_field_definition_list(uuid,uuid)",
                    "content.slaif_agent_content_item_list(uuid,uuid)",
                    "content.slaif_agent_page_list(uuid)",
                    "content.slaif_agent_composition_list(uuid,uuid)",
                    "content.slaif_agent_media_list(uuid)",
                )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    for signature in grant_signatures:
                        grant = await owner.fetchrow(
                            "SELECT pg_get_userbyid(proc.proowner), "
                            "has_function_privilege("
                            "'slaif_agent_runtime', proc.oid, 'EXECUTE'), "
                            "has_function_privilege("
                            "'slaif_editor_runtime', proc.oid, 'EXECUTE'), "
                            "has_function_privilege("
                            "'slaif_control', proc.oid, 'EXECUTE'), "
                            "EXISTS (SELECT 1 FROM aclexplode(COALESCE(proc.proacl, "
                            "acldefault('f', proc.proowner))) acl "
                            "WHERE acl.grantee = 0 AND acl.privilege_type = 'EXECUTE') "
                            "FROM pg_proc proc WHERE proc.oid = $1::regprocedure",
                            signature,
                        )
                        assert tuple(grant) == (
                            "slaif_owner",
                            True,
                            False,
                            False,
                            False,
                        )

                async with app.state.database.cow_pool().acquire() as connection:
                    expected_login = database.credentials["slaif_agent_runtime"][0]
                    authority_roles = [
                        "slaif_owner",
                        "slaif_control",
                        "slaif_editor_runtime",
                        "slaif_agent_runtime",
                        "slaif_public_reader",
                        "slaif_preview_reader",
                        "slaif_reviewer",
                        "slaif_scheduler",
                        "slaif_media",
                        "slaif_gc",
                    ]
                    identity = await connection.fetchrow(
                        "SELECT current_database()::text, session_user::text, "
                        "current_user::text, ARRAY(SELECT target.rolname::text "
                        "FROM pg_catalog.pg_roles target "
                        "WHERE target.rolname = ANY($1::text[]) "
                        "AND pg_catalog.pg_has_role("
                        "session_user, target.oid, 'MEMBER') "
                        "ORDER BY target.rolname)",
                        authority_roles,
                    )
                    assert tuple(identity) == (
                        database.name,
                        expected_login,
                        expected_login,
                        ["slaif_agent_runtime"],
                    )
                    assert not connection.is_in_transaction()

                started = asyncio.Event()
                keep_open = asyncio.Event()

                async def wait_for_cancellation(_service: Any) -> Any:
                    started.set()
                    await keep_open.wait()
                    return None

                context = await app.state.database.authenticate_agent_capability(
                    f"Bearer {token}"
                )
                assert context is not None
                read_task = asyncio.create_task(
                    execute_agent_read(
                        database=app.state.database,
                        context=context,
                        read=wait_for_cancellation,
                    )
                )
                await asyncio.wait_for(started.wait(), timeout=5)
                read_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await read_task

                revoked_token = await _capability_with_scopes(
                    database, seeded, read_scopes
                )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.capability SET revoked_at = now() "
                        "WHERE public_id = $1",
                        revoked_token.split("_")[1],
                    )
                revoked = await client.get(
                    "/api/agent/v1/content-model/types",
                    headers={"Authorization": f"Bearer {revoked_token}"},
                )
                assert revoked.status_code == 401, revoked.text

                expired_token = await _capability_with_scopes(
                    database, seeded, read_scopes
                )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.capability SET expires_at = "
                        "now() - interval '1 minute' "
                        "WHERE public_id = $1",
                        expired_token.split("_")[1],
                    )
                expired = await client.get(
                    "/api/agent/v1/content-model/types",
                    headers={"Authorization": f"Bearer {expired_token}"},
                )
                assert expired.status_code == 401, expired.text

                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.workspace SET status = 'REVOKED' WHERE id = $1",
                        workspace_a,
                    )
                inactive = await client.get(
                    "/api/agent/v1/content-model/types", headers=headers
                )
                assert inactive.status_code == 401, inactive.text

            async with app.state.database.cow_pool().acquire() as connection:
                assert not connection.is_in_transaction()
                context_values = await connection.fetchrow(
                    "SELECT current_setting('app.session_id', true), "
                    "current_setting('app.operation_id', true), "
                    "current_setting('app.visible_operations', true)"
                )
                assert all(value in (None, "") for value in context_values)
    finally:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            await reviewer.discard_session(workspace_a, schema="content")
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            await reviewer.discard_session(workspace_b, schema="content")
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_agent_rejects_wrong_site_scope_and_malformed_mutations(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    token, seeded = await _seed(database)
    scope_token = await _capability_with_scopes(database, seeded, ["site:read"])
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    headers = {"Authorization": f"Bearer {token}"}
    other_type = str(seeded["type_b_id"])
    other_page = str(seeded["page_b_id"])
    reviewer_pool = await database.role_pool("slaif_reviewer")
    agent_pool = await database.role_pool("slaif_agent_runtime")
    failed_keys = (
        "wrong-site-field",
        "wrong-site-item",
        "wrong-site-parent",
        "wrong-site-component",
        "body-path-mismatch",
        "malformed-extra",
        "malformed-path",
    )
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                wrong_site_field = await client.post(
                    f"/api/agent/v1/content-model/types/{other_type}/fields",
                    json={"key": "wrong", "label": "Wrong", "field_type": "short_text"},
                    headers={**headers, "Idempotency-Key": failed_keys[0]},
                )
                assert wrong_site_field.status_code == 404
                assert wrong_site_field.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

                wrong_site_item = await client.post(
                    f"/api/agent/v1/content-items/types/{other_type}",
                    json={
                        "type_id": other_type,
                        "slug": "wrong-site",
                        "status": "DRAFT",
                        "values": {},
                    },
                    headers={**headers, "Idempotency-Key": failed_keys[1]},
                )
                assert wrong_site_item.status_code == 404

                wrong_site_parent = await client.post(
                    "/api/agent/v1/pages/",
                    json={
                        "slug": "wrong-parent",
                        "title": "Wrong parent",
                        "parent_id": other_page,
                    },
                    headers={**headers, "Idempotency-Key": failed_keys[2]},
                )
                assert wrong_site_parent.status_code == 404

                wrong_site_component = await client.post(
                    f"/api/agent/v1/pages/{other_page}/components",
                    json={"component_type": "Heading"},
                    headers={**headers, "Idempotency-Key": failed_keys[3]},
                )
                assert wrong_site_component.status_code == 404

                body_path_mismatch = await client.post(
                    f"/api/agent/v1/content-items/types/{other_type}",
                    json={
                        "type_id": str(seeded["type_b_id"]),
                        "slug": "path-mismatch",
                        "status": "DRAFT",
                        "values": {},
                    },
                    headers={**headers, "Idempotency-Key": failed_keys[4]},
                )
                assert body_path_mismatch.status_code == 404

                malformed_extra = await client.post(
                    "/api/agent/v1/content-model/types",
                    json={
                        "key": "malformed",
                        "slug_pattern": "/malformed",
                        "unknown": True,
                    },
                    headers={**headers, "Idempotency-Key": failed_keys[5]},
                )
                assert malformed_extra.status_code == 422
                assert malformed_extra.json()["error"]["code"] == "VALIDATION_ERROR"

                malformed_path = await client.post(
                    "/api/agent/v1/pages/not-a-uuid/components",
                    json={"component_type": "Heading"},
                    headers={**headers, "Idempotency-Key": failed_keys[6]},
                )
                assert malformed_path.status_code == 422
                assert malformed_path.json()["error"]["code"] == "VALIDATION_ERROR"

                insufficient_scope_requests = (
                    (
                        "/api/agent/v1/content-model/types",
                        {
                            "key": "scope-type",
                            "slug_pattern": "/scope-type",
                        },
                        "scope-type",
                    ),
                    (
                        f"/api/agent/v1/content-model/types/{other_type}/fields",
                        {
                            "key": "scope-field",
                            "label": "Scope",
                            "field_type": "short_text",
                        },
                        "scope-field",
                    ),
                    (
                        f"/api/agent/v1/content-items/types/{other_type}",
                        {
                            "type_id": other_type,
                            "slug": "scope-item",
                            "status": "DRAFT",
                            "values": {},
                        },
                        "scope-item",
                    ),
                    (
                        "/api/agent/v1/pages/",
                        {"slug": "scope-page", "title": "Scope page"},
                        "scope-page",
                    ),
                    (
                        f"/api/agent/v1/pages/{other_page}/components",
                        {"component_type": "Heading"},
                        "scope-component",
                    ),
                )
                for path, payload, key in insufficient_scope_requests:
                    denied = await client.post(
                        path,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {scope_token}",
                            "Idempotency-Key": key,
                        },
                    )
                    assert denied.status_code == 403
                    assert denied.json()["error"]["code"] == "AUTHORIZATION_DENIED"

        async with asyncpg_cow_session(
            agent_pool,
            session_id=seeded["workspace_id"],
            operation_id=uuid4(),
        ) as cow:
            try:
                await cow.native.fetchrow(
                    "SELECT * FROM content.slaif_agent_content_type_create("
                    "$1,$2,$3,$4,$5)",
                    seeded["site_b_id"],
                    "direct-wrong-site",
                    '{"en":"Wrong"}',
                    "/direct-wrong-site",
                    "{}",
                )
            except asyncpg.PostgresError:
                await cow.rollback()
            else:
                raise AssertionError(
                    "wrong-site wrapper invocation unexpectedly succeeded"
                )

        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert (
                await reviewer.operations(seeded["workspace_id"], schema="content")
                == []
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.agent_idempotency "
                    "WHERE workspace_id = $1",
                    seeded["workspace_id"],
                )
                == 0
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.agent_mutation WHERE workspace_id = $1",
                    seeded["workspace_id"],
                )
                == 0
            )
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_cancelled_agent_mutation_rolls_back_reservation_and_cleans_pool(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    token, seeded = await _seed(database)
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    started = asyncio.Event()
    keep_open = asyncio.Event()
    reviewer_pool = await database.role_pool("slaif_reviewer")
    async with app.router.lifespan_context(app):
        context = await app.state.database.authenticate_agent_capability(
            f"Bearer {token}"
        )
        assert context is not None

        async def wait_for_cancellation(_service: Any) -> Any:
            started.set()
            await keep_open.wait()
            raise AssertionError("cancellation fixture should remain pending")

        task = asyncio.create_task(
            execute_agent_mutation(
                database=app.state.database,
                context=context,
                key="cancelled-operation",
                digest=mutation_digest(
                    method="POST",
                    path="/api/agent/v1/content-model/types",
                    body={"key": "cancelled"},
                ),
                mutate=wait_for_cancellation,
                resource_type="content_type",
            )
        )
        await asyncio.wait_for(started.wait(), timeout=5)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        async with app.state.database.cow_pool().acquire() as connection:
            assert not connection.is_in_transaction()

    try:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert (
                await reviewer.operations(seeded["workspace_id"], schema="content")
                == []
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.agent_idempotency "
                    "WHERE capability_id = $1",
                    seeded["capability_id"],
                )
                == 0
            )
    finally:
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_content_type_create_resource_limits_are_db_serialized(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = ["site:read", "content-model:create", "content-model:read"]
    _, other_workspace = await _workspace_capability(
        database, seeded, scopes, "Resource Isolation Workspace"
    )
    _, race_workspace = await _workspace_capability(
        database, seeded, scopes, "Resource Race Workspace"
    )
    http_token, http_workspace = await _workspace_capability(
        database, seeded, scopes, "Resource HTTP Race Workspace"
    )
    _, roundtrip_workspace = await _workspace_capability(
        database, seeded, scopes, "Resource Migration Workspace"
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    second_agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")

    async def create_type(pool: asyncpg.Pool[Any], workspace_id: UUID, key: str) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_content_type_create($1,$2,$3,$4,$5)",
                seeded["site_id"],
                key,
                json.dumps({"en": key}),
                f"/{key}/{{slug}}",
                "{}",
            )

    async def update_type(
        pool: asyncpg.Pool[Any], workspace_id: UUID, type_id: UUID, expected: int
    ) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_content_type_update("
                "$1,$2,$3,$4,$5,$6)",
                seeded["site_id"],
                type_id,
                None,
                None,
                json.dumps({"roundtrip": True}),
                expected,
            )

    async def create_field(
        pool: asyncpg.Pool[Any], workspace_id: UUID, type_id: UUID, key: str
    ) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_field_definition_create("
                "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                seeded["site_id"],
                type_id,
                key,
                key,
                "short_text",
                False,
                False,
                1,
                0,
                "{}",
                "{}",
            )

    async def visible_type_keys(
        pool: asyncpg.Pool[Any], workspace_id: UUID
    ) -> set[str]:
        async with asyncpg_cow_session(
            pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return {
                str(row[0])
                for row in await cow.native.fetch(
                    "SELECT key FROM content.content_type "
                    "WHERE site_id=$1 AND status='ACTIVE' ORDER BY key",
                    seeded["site_id"],
                )
            }

    async def operation_count(workspace_id: UUID) -> int:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            return len(await reviewer.operations(workspace_id, schema="content"))

    try:
        async with agent_pool.acquire() as agent:
            assert not await agent.fetchval(
                "SELECT has_function_privilege(current_user, "
                "'control.slaif_agent_resource_constraints(uuid)', 'EXECUTE')"
            )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await agent.fetchrow(
                    "SELECT * FROM control.slaif_agent_resource_constraints($1)",
                    seeded["site_id"],
                )

        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {"allowed_type_keys": ["allowed"], "max_content_types": 2},
        )
        assert (await create_type(agent_pool, seeded["workspace_id"], "allowed"))[
            "key"
        ] == "allowed"
        operations_after_allowed = await operation_count(seeded["workspace_id"])
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_KEY_DENIED"
        ):
            await create_type(agent_pool, seeded["workspace_id"], "blocked")
        assert await operation_count(seeded["workspace_id"]) == operations_after_allowed
        assert await visible_type_keys(agent_pool, seeded["workspace_id"]) == {
            "allowed"
        }

        await _set_resource_constraints(
            database,
            seeded["workspace_id"],
            {
                "allowed_type_keys": ["allowed", "second", "third"],
                "max_content_types": 2,
            },
        )
        assert (await create_type(agent_pool, seeded["workspace_id"], "second"))[
            "key"
        ] == "second"
        operations_at_limit = await operation_count(seeded["workspace_id"])
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_CONTENT_TYPE_LIMIT"
        ):
            await create_type(agent_pool, seeded["workspace_id"], "third")
        assert await operation_count(seeded["workspace_id"]) == operations_at_limit
        assert await visible_type_keys(agent_pool, seeded["workspace_id"]) == {
            "allowed",
            "second",
        }
        assert await visible_type_keys(agent_pool, other_workspace) == set()

        await _set_resource_constraints(
            database,
            race_workspace,
            {
                "allowed_type_keys": ["race-one", "race-two"],
                "max_content_types": 1,
            },
        )
        race_ready = asyncio.Event()
        race_guard = asyncio.Lock()
        race_arrivals = 0

        async def race_create(pool: asyncpg.Pool[Any], key: str) -> tuple[str, str]:
            nonlocal race_arrivals
            try:
                async with asyncpg_cow_session(
                    pool, session_id=race_workspace, operation_id=uuid4()
                ) as cow:
                    async with race_guard:
                        race_arrivals += 1
                        if race_arrivals == 2:
                            race_ready.set()
                    await asyncio.wait_for(race_ready.wait(), timeout=5)
                    row = await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_content_type_create("
                        "$1,$2,$3,$4,$5)",
                        seeded["site_id"],
                        key,
                        json.dumps({"en": key}),
                        f"/{key}/{{slug}}",
                        "{}",
                    )
                    return "created", str(row["key"])
            except asyncpg.PostgresError as error:
                return "denied", str(error)

        race_results = await asyncio.gather(
            race_create(agent_pool, "race-one"),
            race_create(second_agent_pool, "race-two"),
        )
        assert [result[0] for result in race_results].count("created") == 1
        assert [result[0] for result in race_results].count("denied") == 1
        denied_result = next(result for result in race_results if result[0] == "denied")
        assert "AGENT_RESOURCE_CONTENT_TYPE_LIMIT" in denied_result[1]
        race_keys = await visible_type_keys(agent_pool, race_workspace)
        assert len(race_keys) == 1
        assert race_keys <= {"race-one", "race-two"}
        assert await operation_count(race_workspace) == 1
        assert not race_keys.intersection(
            await visible_type_keys(agent_pool, seeded["workspace_id"])
        )

        await _set_resource_constraints(
            database,
            http_workspace,
            {
                "allowed_type_keys": ["http-one", "http-two"],
                "max_content_types": 1,
            },
        )
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {http_token}"}
                http_responses = await asyncio.gather(
                    client.post(
                        "/api/agent/v1/content-model/types",
                        headers={**headers, "Idempotency-Key": "http-race-one"},
                        json={
                            "key": "http-one",
                            "labels": {"en": "HTTP one"},
                            "slug_pattern": "/http-one/{slug}",
                            "settings": {},
                        },
                    ),
                    client.post(
                        "/api/agent/v1/content-model/types",
                        headers={**headers, "Idempotency-Key": "http-race-two"},
                        json={
                            "key": "http-two",
                            "labels": {"en": "HTTP two"},
                            "slug_pattern": "/http-two/{slug}",
                            "settings": {},
                        },
                    ),
                )
        statuses = [response.status_code for response in http_responses]
        assert statuses.count(201) == 1, [response.text for response in http_responses]
        assert sum(status in {409, 429} for status in statuses) == 1, [
            response.text for response in http_responses
        ]
        assert len(await visible_type_keys(agent_pool, http_workspace)) == 1
        assert await operation_count(http_workspace) == 1

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.content_type_base "
                    "WHERE site_id=$1 AND key = ANY($2::text[])",
                    seeded["site_id"],
                    [
                        "allowed",
                        "second",
                        "race-one",
                        "race-two",
                        "http-one",
                        "http-two",
                    ],
                )
                == 0
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM control.agent_idempotency "
                    "WHERE workspace_id=$1",
                    http_workspace,
                )
                == 1
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM audit.agent_mutation WHERE workspace_id=$1",
                    http_workspace,
                )
                == 1
            )

        await _set_resource_constraints(
            database,
            roundtrip_workspace,
            {
                "allowed_type_keys": ["downgrade-create", "upgrade-denied"],
                "max_content_types": 0,
            },
        )
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="043_001",
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT to_regprocedure("
                    "'control.slaif_agent_resource_constraints(uuid)')"
                )
                is None
            )
            function_definition = await owner.fetchval(
                "SELECT pg_get_functiondef("
                "'content.slaif_agent_content_type_create("
                "uuid,text,jsonb,text,jsonb)'::regprocedure)"
            )
            assert "slaif_agent_require_cow_site" in function_definition
            assert "slaif_agent_unchecked_content_type_create" in function_definition
            assert "slaif_agent_resource_constraints" not in function_definition
            assert await owner.fetchval(
                "SELECT has_function_privilege('slaif_agent_runtime', "
                "'content.slaif_agent_content_type_create("
                "uuid,text,jsonb,text,jsonb)', 'EXECUTE')"
            )
            assert not await owner.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_proc proc, "
                "aclexplode(COALESCE(proc.proacl, "
                "acldefault('f', proc.proowner))) acl "
                "WHERE proc.oid='content.slaif_agent_content_type_create("
                "uuid,text,jsonb,text,jsonb)'::regprocedure "
                "AND acl.grantee=0 AND acl.privilege_type='EXECUTE')"
            )
            for signature in (
                "content.slaif_agent_field_definition_update("
                "uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer)",
                "content.slaif_agent_field_definition_delete(uuid,uuid,uuid,integer)",
            ):
                function_definition = await owner.fetchval(
                    "SELECT pg_get_functiondef($1::regprocedure)", signature
                )
                assert "slaif_agent_require_cow_site" in function_definition
                assert "slaif_agent_resource_constraints" not in function_definition
                assert await owner.fetchval(
                    "SELECT has_function_privilege('slaif_agent_runtime', $1, "
                    "'EXECUTE')",
                    signature,
                )
                assert await owner.fetchval(
                    "SELECT has_function_privilege('public', $1, 'EXECUTE')",
                    signature,
                )
            field_signature = (
                "content.slaif_agent_field_definition_create("
                "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)"
            )
            field_definition = await owner.fetchval(
                "SELECT pg_get_functiondef($1::regprocedure)", field_signature
            )
            assert "slaif_agent_require_cow_site" in field_definition
            assert "slaif_agent_resource_constraints" not in field_definition
            assert await owner.fetchval(
                "SELECT has_function_privilege('slaif_agent_runtime', $1, 'EXECUTE')",
                field_signature,
            )
            assert await owner.fetchval(
                "SELECT has_function_privilege('public', $1, 'EXECUTE')",
                field_signature,
            )
        downgrade_created = await create_type(
            agent_pool, roundtrip_workspace, "downgrade-create"
        )
        assert downgrade_created["key"] == "downgrade-create"

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="upgrade",
            revision="044_001",
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT to_regprocedure("
                    "'control.slaif_agent_resource_constraints(uuid)')"
                )
                is not None
            )
            assert await owner.fetchval(
                "SELECT has_function_privilege('slaif_agent_runtime', "
                "'content.slaif_agent_content_type_create("
                "uuid,text,jsonb,text,jsonb)', 'EXECUTE')"
            )
            assert not await owner.fetchval(
                "SELECT has_function_privilege('slaif_agent_runtime', "
                "'control.slaif_agent_resource_constraints(uuid)', 'EXECUTE')"
            )
            for signature in (
                "content.slaif_agent_content_type_update("
                "uuid,uuid,jsonb,text,jsonb,integer)",
                "content.slaif_agent_content_type_delete(uuid,uuid,integer)",
                "content.slaif_agent_field_definition_create("
                "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)",
            ):
                function_definition = await owner.fetchval(
                    "SELECT pg_get_functiondef($1::regprocedure)", signature
                )
                assert "slaif_agent_resource_constraints" in function_definition
                assert await owner.fetchval(
                    "SELECT has_function_privilege('slaif_agent_runtime', $1, "
                    "'EXECUTE')",
                    signature,
                )
            for signature in (
                "content.slaif_agent_content_type_update("
                "uuid,uuid,jsonb,text,jsonb,integer)",
                "content.slaif_agent_content_type_delete(uuid,uuid,integer)",
                "content.slaif_agent_field_definition_create("
                "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)",
                "content.slaif_agent_field_definition_update("
                "uuid,uuid,uuid,text,boolean,boolean,integer,integer,jsonb,jsonb,integer)",
                "content.slaif_agent_field_definition_delete(uuid,uuid,uuid,integer)",
            ):
                assert not await owner.fetchval(
                    "SELECT has_function_privilege('public', $1, 'EXECUTE')",
                    signature,
                )
            assert not await owner.fetchval(
                "SELECT has_function_privilege('public', $1, 'EXECUTE')",
                "content.slaif_agent_field_definition_create("
                "uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb)",
            )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_CONTENT_TYPE_LIMIT"
        ):
            await create_type(agent_pool, roundtrip_workspace, "upgrade-denied")
        await _set_resource_constraints(
            database,
            roundtrip_workspace,
            {
                "allowed_type_ids": [str(downgrade_created["id"])],
                "allowed_type_keys": ["downgrade-create"],
            },
        )
        upgraded = await update_type(
            agent_pool,
            roundtrip_workspace,
            downgrade_created["id"],
            1,
        )
        assert upgraded["definition_version"] == 2
        await _set_resource_constraints(
            database,
            roundtrip_workspace,
            {
                "allowed_type_ids": [str(downgrade_created["id"])],
                "allowed_type_keys": ["downgrade-create"],
                "delete_enabled": False,
                "max_fields_per_type": 0,
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_FIELD_DEFINITION_LIMIT"
        ):
            await create_field(
                agent_pool,
                roundtrip_workspace,
                downgrade_created["id"],
                "upgrade-denied-field",
            )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_DELETE_DISABLED"
        ):
            async with asyncpg_cow_session(
                agent_pool, session_id=roundtrip_workspace, operation_id=uuid4()
            ) as cow:
                await cow.native.fetchrow(
                    "SELECT * FROM content.slaif_agent_content_type_delete($1,$2,$3)",
                    seeded["site_id"],
                    downgrade_created["id"],
                    2,
                )
    finally:
        await reviewer_pool.close()
        await second_agent_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_field_update_delete_resources_are_db_enforced_and_concurrency_safe(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:delete",
        "field-definition:create",
        "field-definition:write",
        "field-definition:delete",
        "content-item:create",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Update Delete Workspace"
    )
    other_token, other_workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Update Delete Other Workspace"
    )
    deleted_token, deleted_workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Update Delete Deleted Parent Workspace"
    )
    race_token, race_workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Update Delete Race Workspace"
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    second_agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "UPDATE control.capability SET delete_quota=2 "
            "WHERE workspace_id = ANY($1::uuid[])",
            [workspace_id, deleted_workspace_id],
        )

    async def operation_count(workspace: UUID) -> int:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            return len(await reviewer.operations(workspace, schema="content"))

    async def durable_counts(workspace: UUID) -> tuple[int, int, int, int]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                " WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1), "
                "(SELECT mutation_used FROM control.capability "
                " WHERE workspace_id=$1), "
                "(SELECT delete_used FROM control.capability "
                " WHERE workspace_id=$1)",
                workspace,
            )
        return tuple(row)

    async def direct_update(
        pool: asyncpg.Pool[Any],
        workspace: UUID,
        site_id: UUID,
        type_id: UUID,
        field_id: UUID,
        expected: int,
        label: str = "Direct update",
    ) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_field_definition_update("
                "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                site_id,
                type_id,
                field_id,
                label,
                None,
                None,
                None,
                None,
                None,
                None,
                expected,
            )

    async def direct_delete(
        pool: asyncpg.Pool[Any],
        workspace: UUID,
        site_id: UUID,
        type_id: UUID,
        field_id: UUID,
        expected: int,
    ) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_field_definition_delete("
                "$1,$2,$3,$4)",
                site_id,
                type_id,
                field_id,
                expected,
            )

    async def visible_field(workspace: UUID, field_id: UUID) -> Any:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT id, key, label, definition_version "
                "FROM content.field_definition WHERE id=$1",
                field_id,
            )

    try:
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}
                parent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "field-update-parent"},
                    json={
                        "key": "field-update-parent",
                        "labels": {"en": "Field update parent"},
                        "slug_pattern": "/field-update-parent/{slug}",
                        "settings": {},
                    },
                )
                assert parent.status_code == 201, parent.text
                parent_id = UUID(parent.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(parent_id)],
                        "allowed_type_keys": ["field-update-parent"],
                    },
                )
                field = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "field-update-field"},
                    json={
                        "key": "managed-field",
                        "label": "Managed field",
                        "field_type": "short_text",
                    },
                )
                assert field.status_code == 201, field.text
                field_id = UUID(field.json()["record"]["id"])
                before_update = await durable_counts(workspace_id)
                operations_before_update = await operation_count(workspace_id)
                update_body = {
                    "label": "Managed field v2",
                    "required": True,
                    "expected_definition_version": 1,
                }
                updated = await client.patch(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields/{field_id}",
                    headers={**headers, "Idempotency-Key": "field-update"},
                    json=update_body,
                )
                assert updated.status_code == 200, updated.text
                update_result = updated.json()
                assert update_result["action"] == "FIELD_DEFINITION_UPDATED"
                assert update_result["record"]["id"] == str(field_id)
                assert update_result["record"]["type_id"] == str(parent_id)
                assert update_result["record"]["label"] == "Managed field v2"
                assert update_result["record"]["definition_version"] == 2
                replay = await client.patch(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields/{field_id}",
                    headers={**headers, "Idempotency-Key": "field-update"},
                    json=update_body,
                )
                assert replay.status_code == 200
                assert replay.json() == update_result
                mismatch = await client.patch(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields/{field_id}",
                    headers={**headers, "Idempotency-Key": "field-update"},
                    json={**update_body, "label": "Changed body"},
                )
                assert mismatch.status_code == 409
                assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_MISMATCH"
                after_update = await durable_counts(workspace_id)
                assert after_update == (
                    before_update[0] + 1,
                    before_update[1] + 1,
                    before_update[2] + 1,
                    before_update[3],
                )
                assert (
                    await operation_count(workspace_id) == operations_before_update + 1
                )

                other_parent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {other_token}",
                        "Idempotency-Key": "other-field-parent",
                    },
                    json={
                        "key": "other-field-parent",
                        "labels": {"en": "Other field parent"},
                        "slug_pattern": "/other-field-parent/{slug}",
                        "settings": {},
                    },
                )
                assert other_parent.status_code == 201, other_parent.text
                other_parent_id = UUID(other_parent.json()["record"]["id"])
                other_field = await client.post(
                    f"/api/agent/v1/content-model/types/{other_parent_id}/fields",
                    headers={
                        "Authorization": f"Bearer {other_token}",
                        "Idempotency-Key": "other-field",
                    },
                    json={
                        "key": "other-managed-field",
                        "label": "Other managed field",
                        "field_type": "short_text",
                    },
                )
                assert other_field.status_code == 201, other_field.text
                other_field_id = UUID(other_field.json()["record"]["id"])

                deleted_parent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {deleted_token}",
                        "Idempotency-Key": "deleted-parent",
                    },
                    json={
                        "key": "deleted-field-parent",
                        "labels": {"en": "Deleted field parent"},
                        "slug_pattern": "/deleted-field-parent/{slug}",
                        "settings": {},
                    },
                )
                assert deleted_parent.status_code == 201, deleted_parent.text
                deleted_parent_id = UUID(deleted_parent.json()["record"]["id"])
                deleted_field = await client.post(
                    f"/api/agent/v1/content-model/types/{deleted_parent_id}/fields",
                    headers={
                        "Authorization": f"Bearer {deleted_token}",
                        "Idempotency-Key": "deleted-field",
                    },
                    json={
                        "key": "deleted-parent-field",
                        "label": "Deleted parent field",
                        "field_type": "short_text",
                    },
                )
                assert deleted_field.status_code == 201, deleted_field.text
                deleted_field_id = UUID(deleted_field.json()["record"]["id"])
                deleted_parent_request = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{deleted_parent_id}",
                    headers={
                        "Authorization": f"Bearer {deleted_token}",
                        "Idempotency-Key": "delete-parent",
                    },
                    json={"expected_definition_version": 2},
                )
                assert deleted_parent_request.status_code == 200, (
                    deleted_parent_request.text
                )

        before_denials = await operation_count(workspace_id)
        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(uuid4())],
                "allowed_type_keys": ["field-update-parent"],
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_ID_DENIED"
        ):
            await direct_update(
                agent_pool,
                workspace_id,
                seeded["site_id"],
                parent_id,
                field_id,
                2,
            )
        assert await operation_count(workspace_id) == before_denials

        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(parent_id)],
                "allowed_type_keys": ["different-parent"],
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_KEY_DENIED"
        ):
            await direct_update(
                agent_pool,
                workspace_id,
                seeded["site_id"],
                parent_id,
                field_id,
                2,
            )
        assert await operation_count(workspace_id) == before_denials

        await _set_resource_constraints(database, workspace_id, {})
        for expected_error, type_id, field_uuid, site_id in (
            ("STALE_DEFINITION", parent_id, uuid4(), seeded["site_id"]),
            ("STALE_DEFINITION", seeded["type_b_id"], field_id, seeded["site_id"]),
            ("COW_SITE_MISMATCH", seeded["type_b_id"], field_id, seeded["site_b_id"]),
            (
                "STALE_DEFINITION",
                other_parent_id,
                other_field_id,
                seeded["site_id"],
            ),
        ):
            with pytest.raises(asyncpg.PostgresError, match=expected_error):
                await direct_update(
                    agent_pool,
                    workspace_id,
                    site_id,
                    type_id,
                    field_uuid,
                    2,
                )
            assert await operation_count(workspace_id) == before_denials

        deleted_before = await operation_count(deleted_workspace_id)
        with pytest.raises(asyncpg.PostgresError, match="STALE_DEFINITION"):
            await direct_update(
                agent_pool,
                deleted_workspace_id,
                seeded["site_id"],
                deleted_parent_id,
                deleted_field_id,
                1,
            )
        assert await operation_count(deleted_workspace_id) == deleted_before

        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}
                dependent = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "dependent-field"},
                    json={
                        "key": "dependent-field",
                        "label": "Dependent field",
                        "field_type": "short_text",
                    },
                )
                assert dependent.status_code == 201, dependent.text
                dependent_id = UUID(dependent.json()["record"]["id"])
                item = await client.post(
                    f"/api/agent/v1/content-items/types/{parent_id}",
                    headers={**headers, "Idempotency-Key": "dependent-item"},
                    json={
                        "type_id": str(parent_id),
                        "slug": "dependent-item",
                        "status": "DRAFT",
                        "values": {
                            "managed-field": "present",
                            "dependent-field": "used",
                        },
                    },
                )
                assert item.status_code == 201, item.text
                deletable = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "deletable-field"},
                    json={
                        "key": "deletable-field",
                        "label": "Deletable field",
                        "field_type": "short_text",
                    },
                )
                assert deletable.status_code == 201, deletable.text
                deletable_id = UUID(deletable.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(parent_id)],
                        "allowed_type_keys": ["field-update-parent"],
                        "delete_enabled": False,
                    },
                )
                before_disabled = await durable_counts(workspace_id)
                operations_before_disabled = await operation_count(workspace_id)
                disabled = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{parent_id}/fields/{deletable_id}",
                    headers={**headers, "Idempotency-Key": "delete-disabled"},
                    json={"expected_definition_version": 1},
                )
                assert disabled.status_code == 403, disabled.text
                assert await durable_counts(workspace_id) == before_disabled
                assert await operation_count(workspace_id) == operations_before_disabled

                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(parent_id)],
                        "allowed_type_keys": ["field-update-parent"],
                        "delete_enabled": True,
                    },
                )
                with pytest.raises(asyncpg.PostgresError, match="FIELD_DEPENDENCIES"):
                    await direct_delete(
                        agent_pool,
                        workspace_id,
                        seeded["site_id"],
                        parent_id,
                        dependent_id,
                        1,
                    )
                assert await operation_count(workspace_id) == operations_before_disabled
                before_delete = await durable_counts(workspace_id)
                deleted = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{parent_id}/fields/{deletable_id}",
                    headers={**headers, "Idempotency-Key": "delete-enabled"},
                    json={"expected_definition_version": 1},
                )
                assert deleted.status_code == 200, deleted.text
                deleted_result = deleted.json()
                assert deleted_result["action"] == "FIELD_DEFINITION_DELETED"
                assert deleted_result["record"]["id"] == str(deletable_id)
                replay_delete = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{parent_id}/fields/{deletable_id}",
                    headers={**headers, "Idempotency-Key": "delete-enabled"},
                    json={"expected_definition_version": 1},
                )
                assert replay_delete.status_code == 200
                assert replay_delete.json() == deleted_result
                after_delete = await durable_counts(workspace_id)
                assert after_delete == (
                    before_delete[0] + 1,
                    before_delete[1] + 1,
                    before_delete[2],
                    before_delete[3] + 1,
                )
                assert await visible_field(workspace_id, deletable_id) is None
                assert await visible_field(other_workspace_id, deletable_id) is None

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.field_definition_base WHERE id=$1",
                    deletable_id,
                )
                == 0
            )

        race_app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with race_app.router.lifespan_context(race_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=race_app),
                base_url="http://agent.test",
            ) as client:
                race_parent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {race_token}",
                        "Idempotency-Key": "field-race-parent",
                    },
                    json={
                        "key": "field-race-parent",
                        "labels": {"en": "Field race parent"},
                        "slug_pattern": "/field-race-parent/{slug}",
                        "settings": {},
                    },
                )
                assert race_parent.status_code == 201, race_parent.text
                race_parent_id = UUID(race_parent.json()["record"]["id"])
                race_field = await client.post(
                    f"/api/agent/v1/content-model/types/{race_parent_id}/fields",
                    headers={
                        "Authorization": f"Bearer {race_token}",
                        "Idempotency-Key": "field-race-field",
                    },
                    json={
                        "key": "field-race",
                        "label": "Field race",
                        "field_type": "short_text",
                    },
                )
                assert race_field.status_code == 201, race_field.text
                race_field_id = UUID(race_field.json()["record"]["id"])

        await _set_resource_constraints(
            database,
            race_workspace_id,
            {
                "allowed_type_ids": [str(race_parent_id)],
                "allowed_type_keys": ["field-race-parent"],
            },
        )
        race_operations = await operation_count(race_workspace_id)
        ready = asyncio.Event()
        arrival_lock = asyncio.Lock()
        arrivals = 0

        async def racing_update(pool: asyncpg.Pool[Any], label: str) -> tuple[str, str]:
            nonlocal arrivals
            try:
                async with asyncpg_cow_session(
                    pool, session_id=race_workspace_id, operation_id=uuid4()
                ) as cow:
                    async with arrival_lock:
                        arrivals += 1
                        if arrivals == 2:
                            ready.set()
                    await asyncio.wait_for(ready.wait(), timeout=5)
                    row = await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_field_definition_update("
                        "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                        seeded["site_id"],
                        race_parent_id,
                        race_field_id,
                        label,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        1,
                    )
                    return "updated", str(row[4])
            except asyncpg.PostgresError as error:
                return "denied", str(error)

        race_results = await asyncio.gather(
            racing_update(agent_pool, "Race one"),
            racing_update(second_agent_pool, "Race two"),
        )
        assert [result[0] for result in race_results].count("updated") == 1, (
            race_results
        )
        assert [result[0] for result in race_results].count("denied") == 1, race_results
        assert "STALE_DEFINITION" in next(
            result[1] for result in race_results if result[0] == "denied"
        )
        race_visible = await visible_field(race_workspace_id, race_field_id)
        assert race_visible[2] in {"Race one", "Race two"}
        assert race_visible[3] == 2
        assert await operation_count(race_workspace_id) == race_operations + 1
        async with asyncpg_cow_session(
            agent_pool, session_id=race_workspace_id, operation_id=uuid4()
        ) as cow:
            assert (
                await cow.native.fetchval(
                    "SELECT definition_version FROM content.content_type WHERE id=$1",
                    race_parent_id,
                )
                == 3
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.field_definition_base WHERE id=$1",
                    race_field_id,
                )
                == 0
            )
    finally:
        await reviewer_pool.close()
        await second_agent_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_content_type_update_resources_are_db_enforced_and_idempotent(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:write",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Update Resource Workspace"
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")

    async def operation_count() -> int:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            return len(await reviewer.operations(workspace_id, schema="content"))

    async def direct_update(site_id: UUID, type_id: UUID, expected_version: int) -> Any:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_content_type_update("
                "$1,$2,$3,$4,$5,$6)",
                site_id,
                type_id,
                json.dumps({"en": "direct"}),
                None,
                None,
                expected_version,
            )

    try:
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}
                created = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "update-create"},
                    json={
                        "key": "managed",
                        "labels": {"en": "Managed"},
                        "slug_pattern": "/managed/{slug}",
                        "settings": {},
                    },
                )
                assert created.status_code == 201, created.text
                created_record = created.json()["record"]
                type_id = UUID(created_record["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(type_id)],
                        "allowed_type_keys": ["managed"],
                    },
                )

                update_body = {
                    "labels": {"en": "Managed v2"},
                    "slug_pattern": "/managed-v2/{slug}",
                    "settings": {"revision": 2},
                    "expected_definition_version": 1,
                }
                updated = await client.patch(
                    f"/api/agent/v1/content-model/types/{type_id}",
                    headers={**headers, "Idempotency-Key": "update-type"},
                    json=update_body,
                )
                assert updated.status_code == 200, updated.text
                update_result = updated.json()
                assert update_result["action"] == "CONTENT_TYPE_UPDATED"
                assert update_result["record"]["id"] == str(type_id)
                assert update_result["record"]["key"] == "managed"
                assert update_result["record"]["status"] == "ACTIVE"
                assert update_result["record"]["definition_version"] == 2

                replay = await client.patch(
                    f"/api/agent/v1/content-model/types/{type_id}",
                    headers={**headers, "Idempotency-Key": "update-type"},
                    json=update_body,
                )
                assert replay.status_code == 200
                assert replay.json() == update_result

                mismatch = await client.patch(
                    f"/api/agent/v1/content-model/types/{type_id}",
                    headers={**headers, "Idempotency-Key": "update-type"},
                    json={**update_body, "labels": {"en": "changed"}},
                )
                assert mismatch.status_code == 409
                assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_MISMATCH"

        before_denials = await operation_count()
        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(uuid4())],
                "allowed_type_keys": ["managed"],
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_ID_DENIED"
        ):
            await direct_update(seeded["site_id"], type_id, 2)
        assert await operation_count() == before_denials

        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(type_id)],
                "allowed_type_keys": ["different"],
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_KEY_DENIED"
        ):
            await direct_update(seeded["site_id"], type_id, 2)
        assert await operation_count() == before_denials

        await _set_resource_constraints(database, workspace_id, {})
        with pytest.raises(asyncpg.PostgresError, match="STALE_DEFINITION"):
            await direct_update(seeded["site_id"], type_id, 1)
        assert await operation_count() == before_denials

        with pytest.raises(asyncpg.PostgresError, match="STALE_DEFINITION"):
            await direct_update(seeded["site_id"], seeded["type_b_id"], 1)
        assert await operation_count() == before_denials

        with pytest.raises(asyncpg.PostgresError, match="COW_SITE_MISMATCH"):
            await direct_update(seeded["site_b_id"], seeded["type_b_id"], 1)
        assert await operation_count() == before_denials

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            counts = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                "WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1 AND action='CONTENT_TYPE_UPDATED')",
                workspace_id,
            )
            assert tuple(counts) == (2, 2, 1)
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_content_type_delete_resource_and_dependency_guards_are_atomic(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:delete",
        "content-item:create",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Delete Resource Workspace"
    )
    _, other_workspace_id = await _workspace_capability(
        database, seeded, ["site:read", "content-model:read"], "Delete Observer"
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")

    async def operation_count() -> int:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            return len(await reviewer.operations(workspace_id, schema="content"))

    async def direct_delete(type_id: UUID, expected_version: int) -> Any:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_content_type_delete($1,$2,$3)",
                seeded["site_id"],
                type_id,
                expected_version,
            )

    async def visible_type(pool: asyncpg.Pool[Any], type_id: UUID) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT status, definition_version FROM content.content_type "
                "WHERE id=$1",
                type_id,
            )

    try:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "UPDATE control.capability SET delete_quota=1 WHERE workspace_id=$1",
                workspace_id,
            )
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}

                deletable = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "delete-create"},
                    json={
                        "key": "deletable",
                        "labels": {"en": "Deletable"},
                        "slug_pattern": "/deletable/{slug}",
                        "settings": {},
                    },
                )
                assert deletable.status_code == 201, deletable.text
                deletable_id = UUID(deletable.json()["record"]["id"])

                dependent = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "dependency-create"},
                    json={
                        "key": "dependent",
                        "labels": {"en": "Dependent"},
                        "slug_pattern": "/dependent/{slug}",
                        "settings": {},
                    },
                )
                assert dependent.status_code == 201, dependent.text
                dependent_id = UUID(dependent.json()["record"]["id"])
                item = await client.post(
                    f"/api/agent/v1/content-items/types/{dependent_id}",
                    headers={**headers, "Idempotency-Key": "dependency-item"},
                    json={
                        "type_id": str(dependent_id),
                        "slug": "dependent-item",
                        "status": "DRAFT",
                        "values": {},
                    },
                )
                assert item.status_code == 201, item.text

                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(deletable_id)],
                        "allowed_type_keys": ["deletable"],
                        "delete_enabled": False,
                    },
                )
                before_disabled = await operation_count()
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    before_counts = await owner.fetchrow(
                        "SELECT "
                        "(SELECT count(*) FROM control.agent_idempotency "
                        " WHERE workspace_id=$1), "
                        "(SELECT count(*) FROM audit.agent_mutation "
                        " WHERE workspace_id=$1), "
                        "(SELECT mutation_used FROM control.capability "
                        " WHERE workspace_id=$1), "
                        "(SELECT delete_used FROM control.capability "
                        " WHERE workspace_id=$1)",
                        workspace_id,
                    )

                denied = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{deletable_id}",
                    headers={**headers, "Idempotency-Key": "delete-disabled"},
                    json={"expected_definition_version": 1},
                )
                assert denied.status_code == 403, denied.text
                assert await operation_count() == before_disabled
                with pytest.raises(
                    asyncpg.PostgresError, match="AGENT_RESOURCE_DELETE_DISABLED"
                ):
                    await direct_delete(deletable_id, 1)
                assert await operation_count() == before_disabled

                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(deletable_id)],
                        "allowed_type_keys": ["deletable"],
                        "delete_enabled": True,
                    },
                )
                deleted = await client.request(
                    "DELETE",
                    f"/api/agent/v1/content-model/types/{deletable_id}",
                    headers={**headers, "Idempotency-Key": "delete-enabled"},
                    json={"expected_definition_version": 1},
                )
                assert deleted.status_code == 200, deleted.text
                deleted_result = deleted.json()
                assert deleted_result["action"] == "CONTENT_TYPE_DELETED"
                assert deleted_result["record"]["id"] == str(deletable_id)
                assert deleted_result["record"]["status"] == "DELETED"
                assert deleted_result["record"]["definition_version"] == 2

        same_workspace = await visible_type(agent_pool, deletable_id)
        assert tuple(same_workspace) == ("DELETED", 2)
        async with asyncpg_cow_session(
            agent_pool, session_id=other_workspace_id, operation_id=uuid4()
        ) as cow:
            assert (
                await cow.native.fetchrow(
                    "SELECT id FROM content.content_type "
                    "WHERE id=$1 AND status='ACTIVE'",
                    deletable_id,
                )
                is None
            )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            after_counts = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                " WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1), "
                "(SELECT mutation_used FROM control.capability "
                " WHERE workspace_id=$1), "
                "(SELECT delete_used FROM control.capability "
                " WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1 AND action='CONTENT_TYPE_DELETED'), "
                "(SELECT count(*) FROM content.content_type_base WHERE id=$2)",
                workspace_id,
                deletable_id,
            )
            assert tuple(after_counts[:2]) == (
                before_counts[0] + 1,
                before_counts[1] + 1,
            )
            assert tuple(after_counts[2:4]) == (before_counts[2], before_counts[3] + 1)
            assert after_counts[4] == 1
            assert after_counts[5] == 0

        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(dependent_id)],
                "allowed_type_keys": ["dependent"],
                "delete_enabled": True,
            },
        )
        before_dependency_denial = await operation_count()
        with pytest.raises(asyncpg.PostgresError, match="TYPE_DEPENDENCIES"):
            await direct_delete(dependent_id, 1)
        assert await operation_count() == before_dependency_denial
        assert tuple(await visible_type(agent_pool, dependent_id)) == ("ACTIVE", 1)
    finally:
        await reviewer_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_content_type_update_version_lock_allows_one_racing_operation(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:write",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Update Race Workspace"
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    second_agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")

    try:
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                created = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Idempotency-Key": "race-create",
                    },
                    json={
                        "key": "race-type",
                        "labels": {"en": "Race"},
                        "slug_pattern": "/race/{slug}",
                        "settings": {},
                    },
                )
                assert created.status_code == 201, created.text
                type_id = UUID(created.json()["record"]["id"])

        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(type_id)],
                "allowed_type_keys": ["race-type"],
            },
        )
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            operations_before_race = len(
                await reviewer.operations(workspace_id, schema="content")
            )
        ready = asyncio.Event()
        arrival_lock = asyncio.Lock()
        arrivals = 0

        async def racing_update(pool: asyncpg.Pool[Any], label: str) -> tuple[str, str]:
            nonlocal arrivals
            try:
                async with asyncpg_cow_session(
                    pool, session_id=workspace_id, operation_id=uuid4()
                ) as cow:
                    async with arrival_lock:
                        arrivals += 1
                        if arrivals == 2:
                            ready.set()
                    await asyncio.wait_for(ready.wait(), timeout=5)
                    row = await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_content_type_update("
                        "$1,$2,$3,$4,$5,$6)",
                        seeded["site_id"],
                        type_id,
                        json.dumps({"en": label}),
                        None,
                        None,
                        1,
                    )
                    return "success", str(row["labels"])
            except asyncpg.PostgresError as error:
                return "denied", str(error)

        results = await asyncio.gather(
            racing_update(agent_pool, "first"),
            racing_update(second_agent_pool, "second"),
        )
        assert [result[0] for result in results].count("success") == 1, results
        assert [result[0] for result in results].count("denied") == 1, results
        denied = next(result for result in results if result[0] == "denied")
        assert "STALE_DEFINITION" in denied[1]

        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            assert (
                len(await reviewer.operations(workspace_id, schema="content"))
                == operations_before_race + 1
            )
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            final = await cow.native.fetchrow(
                "SELECT labels, definition_version FROM content.content_type "
                "WHERE id=$1",
                type_id,
            )
        assert final["definition_version"] == 2
        assert json.loads(final["labels"]) in ({"en": "first"}, {"en": "second"})
    finally:
        await reviewer_pool.close()
        await second_agent_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_field_create_resources_are_db_enforced_and_concurrency_safe(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "field-definition:create",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Resource Workspace"
    )
    other_token, other_workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Other Workspace"
    )
    race_token, race_workspace_id = await _workspace_capability(
        database, seeded, scopes, "Field Race Workspace"
    )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    second_agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")

    async def operation_count(workspace: UUID) -> int:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            return len(await reviewer.operations(workspace, schema="content"))

    async def direct_create(
        pool: asyncpg.Pool[Any],
        workspace: UUID,
        type_id: UUID,
        key: str,
        site_id: UUID | None = None,
    ) -> Any:
        async with asyncpg_cow_session(
            pool, session_id=workspace, operation_id=uuid4()
        ) as cow:
            return await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_field_definition_create("
                "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                site_id or seeded["site_id"],
                type_id,
                key,
                key,
                "short_text",
                False,
                False,
                1,
                0,
                "{}",
                "{}",
            )

    async def visible_field_keys(workspace: UUID, type_id: UUID) -> set[str]:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace, operation_id=uuid4()
        ) as cow:
            return {
                str(row[0])
                for row in await cow.native.fetch(
                    "SELECT key FROM content.field_definition "
                    "WHERE site_id=$1 AND type_id=$2 ORDER BY key",
                    seeded["site_id"],
                    type_id,
                )
            }

    async def durable_counts(workspace: UUID) -> tuple[int, int, int]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                " WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1), "
                "(SELECT mutation_used FROM control.capability "
                " WHERE workspace_id=$1)",
                workspace,
            )
        return tuple(row)

    try:
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}
                parent_response = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={**headers, "Idempotency-Key": "field-parent"},
                    json={
                        "key": "field-parent",
                        "labels": {"en": "Field parent"},
                        "slug_pattern": "/field-parent/{slug}",
                        "settings": {},
                    },
                )
                assert parent_response.status_code == 201, parent_response.text
                parent_id = UUID(parent_response.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(parent_id)],
                        "allowed_type_keys": ["field-parent"],
                        "max_fields_per_type": 2,
                    },
                )
                first = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "field-one"},
                    json={
                        "key": "one",
                        "label": "One",
                        "field_type": "short_text",
                    },
                )
                assert first.status_code == 201, first.text
                first_result = first.json()
                assert first_result["action"] == "FIELD_DEFINITION_CREATED"
                assert first_result["record"]["type_id"] == str(parent_id)
                assert first_result["record"]["key"] == "one"
                first_replay = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "field-one"},
                    json={
                        "key": "one",
                        "label": "One",
                        "field_type": "short_text",
                    },
                )
                assert first_replay.status_code == 201
                assert first_replay.json() == first_result
                second = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "field-two"},
                    json={
                        "key": "two",
                        "label": "Two",
                        "field_type": "short_text",
                    },
                )
                assert second.status_code == 201, second.text
                counts_before_rejection = await durable_counts(workspace_id)
                operations_before_rejection = await operation_count(workspace_id)
                third = await client.post(
                    f"/api/agent/v1/content-model/types/{parent_id}/fields",
                    headers={**headers, "Idempotency-Key": "field-three"},
                    json={
                        "key": "three",
                        "label": "Three",
                        "field_type": "short_text",
                    },
                )
                assert third.status_code == 429, third.text
                assert third.json()["error"]["code"] == "QUOTA_EXCEEDED"
                assert await durable_counts(workspace_id) == counts_before_rejection
                assert (
                    await operation_count(workspace_id) == operations_before_rejection
                )
                assert await visible_field_keys(workspace_id, parent_id) == {
                    "one",
                    "two",
                }

                other_parent_response = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {other_token}",
                        "Idempotency-Key": "other-parent",
                    },
                    json={
                        "key": "other-parent",
                        "labels": {"en": "Other parent"},
                        "slug_pattern": "/other-parent/{slug}",
                        "settings": {},
                    },
                )
                assert other_parent_response.status_code == 201, (
                    other_parent_response.text
                )
                other_parent_id = UUID(other_parent_response.json()["record"]["id"])
                other_field = await client.post(
                    f"/api/agent/v1/content-model/types/{other_parent_id}/fields",
                    headers={
                        "Authorization": f"Bearer {other_token}",
                        "Idempotency-Key": "other-field",
                    },
                    json={
                        "key": "unrestricted",
                        "label": "Unrestricted",
                        "field_type": "short_text",
                    },
                )
                assert other_field.status_code == 201, other_field.text

        before_allowlist_denials = await operation_count(workspace_id)
        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(uuid4())],
                "allowed_type_keys": ["field-parent"],
                "max_fields_per_type": 99,
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_ID_DENIED"
        ):
            await direct_create(agent_pool, workspace_id, parent_id, "id-denied")
        assert await operation_count(workspace_id) == before_allowlist_denials

        await _set_resource_constraints(
            database,
            workspace_id,
            {
                "allowed_type_ids": [str(parent_id)],
                "allowed_type_keys": ["different-parent"],
                "max_fields_per_type": 99,
            },
        )
        with pytest.raises(
            asyncpg.PostgresError, match="AGENT_RESOURCE_TYPE_KEY_DENIED"
        ):
            await direct_create(agent_pool, workspace_id, parent_id, "key-denied")
        assert await operation_count(workspace_id) == before_allowlist_denials

        await _set_resource_constraints(database, workspace_id, {})
        with pytest.raises(asyncpg.PostgresError, match="FIELD_TYPE_SITE_NOT_FOUND"):
            await direct_create(
                agent_pool, workspace_id, seeded["type_b_id"], "foreign-type"
            )
        assert await operation_count(workspace_id) == before_allowlist_denials
        with pytest.raises(asyncpg.PostgresError, match="COW_SITE_MISMATCH"):
            await direct_create(
                agent_pool,
                workspace_id,
                seeded["type_b_id"],
                "wrong-site",
                seeded["site_b_id"],
            )
        assert await operation_count(workspace_id) == before_allowlist_denials
        with pytest.raises(asyncpg.PostgresError, match="FIELD_TYPE_SITE_NOT_FOUND"):
            await direct_create(
                agent_pool, workspace_id, other_parent_id, "other-workspace-parent"
            )
        assert await operation_count(workspace_id) == before_allowlist_denials

        deleted_parent_id = uuid4()
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            await owner.execute(
                "INSERT INTO content.content_type_base "
                "(id, site_id, key, labels, slug_pattern, status, "
                "definition_version, settings) "
                "VALUES ($1,$2,'deleted-parent','{}'::jsonb,'/deleted/{slug}',"
                "'DELETED',1,'{}'::jsonb)",
                deleted_parent_id,
                seeded["site_id"],
            )
        with pytest.raises(asyncpg.PostgresError, match="FIELD_TYPE_SITE_NOT_FOUND"):
            await direct_create(
                agent_pool, workspace_id, deleted_parent_id, "deleted-parent-field"
            )
        assert await operation_count(workspace_id) == before_allowlist_denials

        race_parent_response: Any
        app = create_agent_app(
            settings=ServiceSettings.for_test(),
            database_settings=_agent_settings(database),
        )
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                race_parent_response = await client.post(
                    "/api/agent/v1/content-model/types",
                    headers={
                        "Authorization": f"Bearer {race_token}",
                        "Idempotency-Key": "race-field-parent",
                    },
                    json={
                        "key": "race-field-parent",
                        "labels": {"en": "Race field parent"},
                        "slug_pattern": "/race-field-parent/{slug}",
                        "settings": {},
                    },
                )
        assert race_parent_response.status_code == 201, race_parent_response.text
        race_parent_id = UUID(race_parent_response.json()["record"]["id"])
        await _set_resource_constraints(
            database,
            race_workspace_id,
            {
                "allowed_type_ids": [str(race_parent_id)],
                "allowed_type_keys": ["race-field-parent"],
                "max_fields_per_type": 1,
            },
        )
        operations_before_race = await operation_count(race_workspace_id)
        ready = asyncio.Event()
        arrival_lock = asyncio.Lock()
        arrivals = 0

        async def racing_create(pool: asyncpg.Pool[Any], key: str) -> tuple[str, str]:
            nonlocal arrivals
            try:
                async with asyncpg_cow_session(
                    pool, session_id=race_workspace_id, operation_id=uuid4()
                ) as cow:
                    async with arrival_lock:
                        arrivals += 1
                        if arrivals == 2:
                            ready.set()
                    await asyncio.wait_for(ready.wait(), timeout=5)
                    row = await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_field_definition_create("
                        "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
                        seeded["site_id"],
                        race_parent_id,
                        key,
                        key,
                        "short_text",
                        False,
                        False,
                        1,
                        0,
                        "{}",
                        "{}",
                    )
                    return "created", str(row[2])
            except asyncpg.PostgresError as error:
                return "denied", str(error)

        race_results = await asyncio.gather(
            racing_create(agent_pool, "race-one"),
            racing_create(second_agent_pool, "race-two"),
        )
        assert [result[0] for result in race_results].count("created") == 1, (
            race_results
        )
        assert [result[0] for result in race_results].count("denied") == 1, race_results
        assert "AGENT_RESOURCE_FIELD_DEFINITION_LIMIT" in next(
            result[1] for result in race_results if result[0] == "denied"
        )
        assert await visible_field_keys(race_workspace_id, race_parent_id) in (
            {"race-one"},
            {"race-two"},
        )
        assert await operation_count(race_workspace_id) == operations_before_race + 1
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.field_definition_base "
                    "WHERE site_id=$1 AND type_id=$2",
                    seeded["site_id"],
                    race_parent_id,
                )
                == 0
            )
    finally:
        await reviewer_pool.close()
        await second_agent_pool.close()
        await agent_pool.close()


@pytest.mark.asyncio
async def test_semantic_audit_contract_is_strict_and_reversible(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:write",
        "content-model:delete",
        "field-definition:create",
        "field-definition:write",
        "field-definition:delete",
        "content-item:create",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Strict Semantic Audit Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=20, "
            "delete_quota=4 WHERE id=$1",
            capability_id,
        )
    agent_pool = await database.role_pool("slaif_agent_runtime")

    async def audit_row(operation_id: UUID) -> Any:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT capability_id, workspace_id, site_id, resource_type, "
                "resource_id, request_digest, action, http_method, "
                "response_status, quota_kind FROM audit.agent_mutation "
                "WHERE operation_id=$1",
                operation_id,
            )
        return None if row is None else tuple(row)

    async def assert_semantic_result(
        response: httpx.Response,
        *,
        model: Any,
        method: str,
        path: str,
        action: str,
        resource_type: str,
        expected_status: int,
    ) -> tuple[dict[str, Any], UUID]:
        assert response.status_code == expected_status, response.text
        result = response.json()
        operation_id = UUID(result["operation_id"])
        record_id = UUID(result["record"]["id"])
        assert result["action"] == action
        assert await audit_row(operation_id) == (
            capability_id,
            workspace_id,
            seeded["site_id"],
            resource_type,
            record_id,
            mutation_digest(
                method=method,
                path=path,
                body=model.model_dump(mode="json"),
            ),
            action,
            method,
            expected_status,
            "delete" if method == "DELETE" else "mutation",
        )
        return result, operation_id

    async def owner_counts() -> tuple[int, int, int, int]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                " WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1), "
                "(SELECT mutation_used FROM control.capability "
                " WHERE workspace_id=$1), "
                "(SELECT delete_used FROM control.capability "
                " WHERE workspace_id=$1)",
                workspace_id,
            )
        return tuple(row)

    async def strict_complete(arguments: list[object]) -> Any:
        async with agent_pool.acquire() as connection:
            return await connection.fetchval(
                "SELECT control.slaif_agent_idempotency_complete("
                "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
                *arguments,
            )

    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    semantic_requests: list[
        tuple[str, str, dict[str, Any], Any, str, dict[str, Any]]
    ] = []
    parent_id: UUID
    field_id: UUID
    try:
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
            ) as client:
                headers = {"Authorization": f"Bearer {token}"}
                parent_path = "/api/agent/v1/content-model/types"
                parent_body = {
                    "key": "strict-parent",
                    "labels": {"en": "Strict parent"},
                    "slug_pattern": "/strict-parent/{slug}",
                    "settings": {},
                }
                parent_model = CreateContentTypeRequest.model_validate(parent_body)
                parent_response = await client.post(
                    parent_path,
                    headers={**headers, "Idempotency-Key": "strict-parent"},
                    json=parent_body,
                )
                parent_result, _ = await assert_semantic_result(
                    parent_response,
                    model=parent_model,
                    method="POST",
                    path=parent_path,
                    action="CONTENT_TYPE_CREATED",
                    resource_type="content_type",
                    expected_status=201,
                )
                parent_id = UUID(parent_result["record"]["id"])

                legacy_type_body = {
                    "key": "legacy-holder",
                    "labels": {"en": "Legacy holder"},
                    "slug_pattern": "/legacy-holder/{slug}",
                    "settings": {},
                }
                legacy_type_response = await client.post(
                    parent_path,
                    headers={**headers, "Idempotency-Key": "legacy-holder"},
                    json=legacy_type_body,
                )
                assert legacy_type_response.status_code == 201, (
                    legacy_type_response.text
                )
                legacy_type_id = UUID(legacy_type_response.json()["record"]["id"])
                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {
                        "allowed_type_ids": [str(parent_id), str(legacy_type_id)],
                        "allowed_type_keys": ["strict-parent", "legacy-holder"],
                        "delete_enabled": True,
                    },
                )
                field_path = f"{parent_path}/{parent_id}/fields"
                field_body = {
                    "key": "strict-field",
                    "label": "Strict field",
                    "field_type": "short_text",
                }
                field_model = CreateFieldDefinitionRequest.model_validate(field_body)
                field_response = await client.post(
                    field_path,
                    headers={**headers, "Idempotency-Key": "strict-field"},
                    json=field_body,
                )
                field_result, _ = await assert_semantic_result(
                    field_response,
                    model=field_model,
                    method="POST",
                    path=field_path,
                    action="FIELD_DEFINITION_CREATED",
                    resource_type="field_definition",
                    expected_status=201,
                )
                field_id = UUID(field_result["record"]["id"])

                type_update_path = f"{parent_path}/{parent_id}"
                type_update_body = {
                    "labels": {"en": "Strict parent v2"},
                    "expected_definition_version": 2,
                }
                type_update_model = UpdateContentTypeRequest.model_validate(
                    type_update_body
                )
                type_updated = await client.patch(
                    type_update_path,
                    headers={**headers, "Idempotency-Key": "strict-type-update"},
                    json=type_update_body,
                )
                type_update_result, _ = await assert_semantic_result(
                    type_updated,
                    model=type_update_model,
                    method="PATCH",
                    path=type_update_path,
                    action="CONTENT_TYPE_UPDATED",
                    resource_type="content_type",
                    expected_status=200,
                )

                field_update_path = f"{field_path}/{field_id}"
                field_update_body = {
                    "label": "Strict field v2",
                    "required": True,
                    "expected_definition_version": 1,
                }
                field_update_model = UpdateFieldDefinitionRequest.model_validate(
                    field_update_body
                )
                field_updated = await client.patch(
                    field_update_path,
                    headers={**headers, "Idempotency-Key": "strict-field-update"},
                    json=field_update_body,
                )
                field_update_result, _ = await assert_semantic_result(
                    field_updated,
                    model=field_update_model,
                    method="PATCH",
                    path=field_update_path,
                    action="FIELD_DEFINITION_UPDATED",
                    resource_type="field_definition",
                    expected_status=200,
                )

                field_delete_body = {"expected_definition_version": 2}
                field_delete_model = DeleteDefinitionRequest.model_validate(
                    field_delete_body
                )
                field_deleted = await client.request(
                    "DELETE",
                    field_update_path,
                    headers={**headers, "Idempotency-Key": "strict-field-delete"},
                    json=field_delete_body,
                )
                field_delete_result, _ = await assert_semantic_result(
                    field_deleted,
                    model=field_delete_model,
                    method="DELETE",
                    path=field_update_path,
                    action="FIELD_DEFINITION_DELETED",
                    resource_type="field_definition",
                    expected_status=200,
                )

                type_delete_body = {"expected_definition_version": 5}
                type_delete_model = DeleteDefinitionRequest.model_validate(
                    type_delete_body
                )
                type_deleted = await client.request(
                    "DELETE",
                    type_update_path,
                    headers={**headers, "Idempotency-Key": "strict-type-delete"},
                    json=type_delete_body,
                )
                type_delete_result, _ = await assert_semantic_result(
                    type_deleted,
                    model=type_delete_model,
                    method="DELETE",
                    path=type_update_path,
                    action="CONTENT_TYPE_DELETED",
                    resource_type="content_type",
                    expected_status=200,
                )
                semantic_requests = [
                    (
                        "POST",
                        parent_path,
                        parent_body,
                        parent_model,
                        "strict-parent",
                        parent_result,
                    ),
                    (
                        "POST",
                        field_path,
                        field_body,
                        field_model,
                        "strict-field",
                        field_result,
                    ),
                    (
                        "PATCH",
                        type_update_path,
                        type_update_body,
                        type_update_model,
                        "strict-type-update",
                        type_update_result,
                    ),
                    (
                        "PATCH",
                        field_update_path,
                        field_update_body,
                        field_update_model,
                        "strict-field-update",
                        field_update_result,
                    ),
                    (
                        "DELETE",
                        field_update_path,
                        field_delete_body,
                        field_delete_model,
                        "strict-field-delete",
                        field_delete_result,
                    ),
                    (
                        "DELETE",
                        type_update_path,
                        type_delete_body,
                        type_delete_model,
                        "strict-type-delete",
                        type_delete_result,
                    ),
                ]
                before_replays = await owner_counts()
                for method, path, body, _model, key, original in semantic_requests:
                    replay = await client.request(
                        method,
                        path,
                        headers={**headers, "Idempotency-Key": key},
                        json=body,
                    )
                    assert replay.status_code == (201 if method == "POST" else 200)
                    assert replay.json() == original
                mismatch = await client.patch(
                    type_update_path,
                    headers={**headers, "Idempotency-Key": "strict-type-update"},
                    json={**type_update_body, "labels": {"en": "changed"}},
                )
                assert mismatch.status_code == 409
                assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_MISMATCH"
                assert await owner_counts() == before_replays

        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            strict_signature = (
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text,text,text)"
            )
            old_semantic_signature = (
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text)"
            )
            assert await owner.fetchval("SELECT to_regprocedure($1)", strict_signature)
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)", old_semantic_signature
            )
            strict_owner = await owner.fetchval(
                "SELECT pg_get_userbyid(proowner) FROM pg_proc "
                "WHERE oid=$1::regprocedure",
                strict_signature,
            )
            assert strict_owner == "slaif_owner"
            assert await owner.fetchval(
                "SELECT has_function_privilege('slaif_agent_runtime',$1,'EXECUTE')",
                strict_signature,
            )
            assert not await owner.fetchval(
                "SELECT has_function_privilege('public',$1,'EXECUTE')",
                strict_signature,
            )

        counts_before_direct = await owner_counts()
        valid_operation_id = uuid4()
        valid_action = "CONTENT_TYPE_CREATED"
        valid_body = {
            "record": {"id": str(parent_id)},
            "operation_id": str(valid_operation_id),
            "action": valid_action,
        }
        valid_arguments: list[object] = [
            capability_id,
            workspace_id,
            "direct-strict",
            "0" * 64,
            valid_operation_id,
            201,
            json.dumps(valid_body),
            "content_type",
            parent_id,
            seeded["site_id"],
            valid_action,
            "POST",
            "mutation",
        ]
        mismatch_arguments: list[tuple[str, dict[int, object]]] = [
            ("action", {10: "FIELD_DEFINITION_CREATED"}),
            ("resource", {7: "field_definition"}),
            ("method", {11: "PATCH"}),
            ("status", {5: 200}),
            ("quota", {12: "delete"}),
        ]
        for _label, changes in mismatch_arguments:
            arguments = list(valid_arguments)
            for index, value in changes.items():
                arguments[index] = value
            with pytest.raises(
                asyncpg.PostgresError, match="INVALID_SEMANTIC_COMPLETION"
            ):
                await strict_complete(arguments)

        for _label, body_changes in (
            ("body-action", {"action": "FIELD_DEFINITION_CREATED"}),
            ("body-operation", {"operation_id": str(uuid4())}),
            ("body-record", {"record": {"id": str(uuid4())}}),
        ):
            body = dict(valid_body)
            body.update(body_changes)
            arguments = list(valid_arguments)
            arguments[6] = json.dumps(body)
            with pytest.raises(
                asyncpg.PostgresError, match="INVALID_SEMANTIC_COMPLETION"
            ):
                await strict_complete(arguments)

        legacy_arguments = list(valid_arguments[:10])
        with pytest.raises(
            asyncpg.PostgresError, match="INVALID_IDEMPOTENCY_COMPLETION"
        ):
            async with agent_pool.acquire() as connection:
                await connection.fetchval(
                    "SELECT control.slaif_agent_idempotency_complete("
                    "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
                    *legacy_arguments,
                )
        async with agent_pool.acquire() as connection:
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await connection.fetch("SELECT * FROM audit.agent_mutation")
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await connection.execute(
                    "UPDATE audit.agent_mutation SET response_status=200"
                )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await connection.execute("DELETE FROM audit.agent_mutation")
        assert await owner_counts() == counts_before_direct

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="044_001",
        )
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT version_num::text FROM control.alembic_version"
                )
                == "044_001"
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM information_schema.columns "
                    "WHERE table_schema='audit' AND table_name='agent_mutation' "
                    "AND column_name IN ('http_method','quota_kind')"
                )
                == 0
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text)",
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text,text,text)",
            )
            assert "max_deletes" not in await owner.fetchval(
                "SELECT pg_get_functiondef($1::regprocedure)",
                "control.slaif_agent_quota_consume(uuid,uuid,text)",
            )

        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="upgrade",
            revision="head",
        )
        await reconcile(database.settings)
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            assert (
                await owner.fetchval(
                    "SELECT version_num::text FROM control.alembic_version"
                )
                == "048_001"
            )
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM information_schema.columns "
                    "WHERE table_schema='audit' AND table_name='agent_mutation' "
                    "AND column_name IN ('http_method','quota_kind')"
                )
                == 2
            )
            assert await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text,text,text)",
            )
            assert not await owner.fetchval(
                "SELECT to_regprocedure($1)",
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text)",
            )
            marker = await owner.fetchrow(
                "SELECT readiness_state, foundation_hardened, "
                "foundation_privileges_validated FROM control.bootstrap_readiness "
                "WHERE singleton"
            )
            assert tuple(marker) == ("HARDENED", True, True)
            for signature in (
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid)",
                "control.slaif_agent_idempotency_complete(uuid,uuid,text,text,"
                "uuid,integer,jsonb,text,uuid,uuid,text,text,text)",
                "control.slaif_agent_quota_consume(uuid,uuid,text)",
            ):
                assert (
                    await owner.fetchval(
                        "SELECT pg_get_userbyid(proowner) FROM pg_proc "
                        "WHERE oid=$1::regprocedure",
                        signature,
                    )
                    == "slaif_owner"
                )
                assert await owner.fetchval(
                    "SELECT has_function_privilege('slaif_agent_runtime',$1,'EXECUTE')",
                    signature,
                )
                assert not await owner.fetchval(
                    "SELECT has_function_privilege('public',$1,'EXECUTE')",
                    signature,
                )
    finally:
        await agent_pool.close()


@pytest.mark.asyncio
async def test_max_deletes_is_the_transactional_delete_quota_bound(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _token, seeded = await _seed(database)
    scopes = [
        "site:read",
        "content-model:create",
        "content-model:read",
        "content-model:delete",
    ]
    token, workspace_id = await _workspace_capability(
        database, seeded, scopes, "Bounded Delete Workspace"
    )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id=$1", workspace_id
        )
        await owner.execute(
            "UPDATE control.capability SET request_quota=100, mutation_quota=20, "
            "delete_quota=2 WHERE id=$1",
            capability_id,
        )
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")

    async def durable_counts() -> tuple[int, int, int, int]:
        async with owner_connection(
            database.settings.resolved_owner_dsn(), expected_database=database.name
        ) as owner:
            row = await owner.fetchrow(
                "SELECT "
                "(SELECT count(*) FROM control.agent_idempotency "
                " WHERE workspace_id=$1), "
                "(SELECT count(*) FROM audit.agent_mutation "
                " WHERE workspace_id=$1), "
                "(SELECT mutation_used FROM control.capability WHERE id=$2), "
                "(SELECT delete_used FROM control.capability WHERE id=$2)",
                workspace_id,
                capability_id,
            )
        return tuple(row)

    async def operation_count() -> int:
        async with asyncpg_cow_reviewer(reviewer_pool) as reviewer:
            return len(await reviewer.operations(workspace_id, schema="content"))

    async def create_type(client: httpx.AsyncClient, key: str) -> UUID:
        response = await client.post(
            "/api/agent/v1/content-model/types",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": f"bounded-create-{key}",
            },
            json={
                "key": key,
                "labels": {"en": key},
                "slug_pattern": f"/{key}/{{slug}}",
                "settings": {},
            },
        )
        assert response.status_code == 201, response.text
        return UUID(response.json()["record"]["id"])

    app_one = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    app_two = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    try:
        async with app_one.router.lifespan_context(app_one):
            async with app_two.router.lifespan_context(app_two):
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app_one),
                    base_url="http://agent.test",
                ) as client_one:
                    type_one_id = await create_type(client_one, "bounded-one")
                    type_two_id = await create_type(client_one, "bounded-two")
                    type_zero_id = await create_type(client_one, "bounded-zero")
                    type_fallback_id = await create_type(client_one, "bounded-fallback")
                    await _set_resource_constraints(
                        database,
                        workspace_id,
                        {
                            "allowed_type_ids": [
                                str(type_one_id),
                                str(type_two_id),
                                str(type_zero_id),
                                str(type_fallback_id),
                            ],
                            "allowed_type_keys": [
                                "bounded-one",
                                "bounded-two",
                                "bounded-zero",
                                "bounded-fallback",
                            ],
                            "delete_enabled": True,
                            "max_deletes": 1,
                        },
                    )
                    before_race = await durable_counts()
                    operations_before_race = await operation_count()
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=app_two),
                        base_url="http://agent.test",
                    ) as client_two:
                        responses = await asyncio.gather(
                            client_one.request(
                                "DELETE",
                                f"/api/agent/v1/content-model/types/{type_one_id}",
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "Idempotency-Key": "bounded-delete-one",
                                },
                                json={"expected_definition_version": 1},
                            ),
                            client_two.request(
                                "DELETE",
                                f"/api/agent/v1/content-model/types/{type_two_id}",
                                headers={
                                    "Authorization": f"Bearer {token}",
                                    "Idempotency-Key": "bounded-delete-two",
                                },
                                json={"expected_definition_version": 1},
                            ),
                        )
                        assert [response.status_code for response in responses].count(
                            200
                        ) == 1, [response.text for response in responses]
                        assert [response.status_code for response in responses].count(
                            429
                        ) == 1, [response.text for response in responses]
                        losing_response = next(
                            response
                            for response in responses
                            if response.status_code == 429
                        )
                        assert losing_response.json()["error"]["code"] == (
                            "QUOTA_EXCEEDED"
                        )
                        winning_response = next(
                            response
                            for response in responses
                            if response.status_code == 200
                        )
                        winning_key = (
                            "bounded-delete-one"
                            if responses[0].status_code == 200
                            else "bounded-delete-two"
                        )
                        winning_client = (
                            client_one
                            if responses[0].status_code == 200
                            else client_two
                        )
                        winning_path = (
                            f"/api/agent/v1/content-model/types/{type_one_id}"
                            if responses[0].status_code == 200
                            else f"/api/agent/v1/content-model/types/{type_two_id}"
                        )
                        winning_body = {"expected_definition_version": 1}
                        winning_result = winning_response.json()

                        after_race = await durable_counts()
                        assert after_race == (
                            before_race[0] + 1,
                            before_race[1] + 1,
                            before_race[2],
                            before_race[3] + 1,
                        )
                        assert await operation_count() == operations_before_race + 1
                        async with owner_connection(
                            database.settings.resolved_owner_dsn(),
                            expected_database=database.name,
                        ) as owner:
                            assert (
                                await owner.fetchval(
                                    "SELECT count(*) FROM control.agent_idempotency "
                                    "WHERE workspace_id=$1 AND idempotency_key IN "
                                    "('bounded-delete-one','bounded-delete-two')",
                                    workspace_id,
                                )
                                == 1
                            )
                            audit = await owner.fetchrow(
                                "SELECT action, http_method, response_status, "
                                "quota_kind "
                                "FROM audit.agent_mutation WHERE operation_id=$1",
                                UUID(winning_result["operation_id"]),
                            )
                            assert tuple(audit) == (
                                "CONTENT_TYPE_DELETED",
                                "DELETE",
                                200,
                                "delete",
                            )

                        replay = await winning_client.request(
                            "DELETE",
                            winning_path,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Idempotency-Key": winning_key,
                            },
                            json=winning_body,
                        )
                        assert replay.status_code == 200
                        assert replay.json() == winning_result
                        assert await durable_counts() == after_race
                        assert await operation_count() == operations_before_race + 1

                        await _set_resource_constraints(
                            database,
                            workspace_id,
                            {
                                "allowed_type_ids": [
                                    str(type_one_id),
                                    str(type_two_id),
                                    str(type_zero_id),
                                ],
                                "allowed_type_keys": [
                                    "bounded-one",
                                    "bounded-two",
                                    "bounded-zero",
                                ],
                                "delete_enabled": True,
                                "max_deletes": 0,
                            },
                        )
                        before_zero = await durable_counts()
                        zero_response = await client_one.request(
                            "DELETE",
                            f"/api/agent/v1/content-model/types/{type_zero_id}",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Idempotency-Key": "bounded-delete-zero",
                            },
                            json={"expected_definition_version": 1},
                        )
                        assert zero_response.status_code == 429
                        assert zero_response.json()["error"]["code"] == "QUOTA_EXCEEDED"
                        assert await durable_counts() == before_zero
                        assert await operation_count() == operations_before_race + 1

                        await _set_resource_constraints(
                            database,
                            workspace_id,
                            {
                                "allowed_type_ids": [
                                    str(type_zero_id),
                                    str(type_fallback_id),
                                ],
                                "allowed_type_keys": [
                                    "bounded-zero",
                                    "bounded-fallback",
                                ],
                                "delete_enabled": True,
                            },
                        )
                        fallback = await client_one.request(
                            "DELETE",
                            f"/api/agent/v1/content-model/types/{type_fallback_id}",
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Idempotency-Key": "bounded-delete-fallback",
                            },
                            json={"expected_definition_version": 1},
                        )
                        assert fallback.status_code == 200, fallback.text
                        assert (await durable_counts())[3] == 2

                await _set_resource_constraints(
                    database,
                    workspace_id,
                    {"max_deletes": "malformed", "delete_enabled": True},
                )
                before_malformed = await durable_counts()
                with pytest.raises(
                    asyncpg.PostgresError, match="INVALID_RESOURCE_CONSTRAINTS"
                ):
                    async with asyncpg_cow_session(
                        agent_pool,
                        session_id=workspace_id,
                        operation_id=uuid4(),
                    ) as cow:
                        await cow.native.fetchval(
                            "SELECT control.slaif_agent_quota_consume($1,$2,'delete')",
                            capability_id,
                            workspace_id,
                        )
                assert await durable_counts() == before_malformed
    finally:
        await reviewer_pool.close()
        await agent_pool.close()

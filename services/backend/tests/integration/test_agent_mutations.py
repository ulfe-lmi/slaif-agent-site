"""Real PostgreSQL proof for the bounded Agent COW mutation surface."""

from __future__ import annotations

import asyncio
import contextlib
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
    asyncpg_cow_session,
)
from slaif_agent_site.agent_state.mutations import (
    execute_agent_mutation,
    mutation_digest,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection


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
        workspace_id = await owner.fetchval(
            """
            INSERT INTO control.workspace (
                site_id, created_by, title, delegation_preset,
                effective_scopes, status, expires_at
            ) VALUES (
                $1, $2, 'Agent Mutation Workspace', 'L4',
                '["site:read","content-model:create","content-model:read",
                  "content-item:create","page:create",
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
            '["site:read","content-model:create","content-model:read","content-item:create","page:create","component-structure:create"]',
            datetime.now(UTC) + timedelta(minutes=30),
        )
        capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE public_id = $1", public_id
        )
    return token, {
        "capability_id": capability_id,
        "site_id": site_id,
        "workspace_id": workspace_id,
    }


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

    type_id = UUID(result["record"]["id"])
    agent_pool = await database.role_pool("slaif_agent_runtime")
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
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
    token, _seeded = await _seed(database)
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
                    "component_type": "Text",
                    "slot_key": "default",
                    "order_key": 0,
                    "props": {"text": "bounded"},
                },
                headers={**headers, "Idempotency-Key": "route-component"},
            )
            assert component_response.status_code == 201, component_response.text
            assert component_response.json()["record"]["page_id"] == page_id


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

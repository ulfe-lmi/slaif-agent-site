"""Real PostgreSQL proof for the bounded Agent COW mutation surface."""

from __future__ import annotations

import asyncio
import contextlib
import json
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
    return token


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
                    "component_type": "Heading",
                    "slot_key": "default",
                    "order_key": 0,
                    "props": {"text": "bounded"},
                },
                headers={**headers, "Idempotency-Key": "route-component"},
            )
            assert component_response.status_code == 201, component_response.text
            assert component_response.json()["record"]["page_id"] == page_id


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

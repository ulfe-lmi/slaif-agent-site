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
from slaif_agent_site.agent_state.reads import execute_agent_read
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration


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
            },
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

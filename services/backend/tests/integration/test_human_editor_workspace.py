"""Real-role integration coverage for the human Editor COW envelope."""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import asyncpg
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.content_model.service import ContentModelService

PERMISSION = "page:create"


async def _resolve(
    pool: asyncpg.Pool[Any], site_id: uuid.UUID, user_id: uuid.UUID
) -> uuid.UUID:
    async with pool.acquire() as connection:
        return cast(
            uuid.UUID,
            await connection.fetchval(
                "SELECT control.slaif_human_editor_workspace_resolve($1, $2)",
                site_id,
                user_id,
            ),
        )


@asynccontextmanager
async def _cow(
    pool: asyncpg.Pool[Any],
    *,
    workspace_id: uuid.UUID,
    operation_id: uuid.UUID,
) -> AsyncIterator[Any]:
    async with asyncpg_cow_session(
        pool, session_id=workspace_id, operation_id=operation_id
    ) as cow:
        yield cow


async def _assert_workspace(
    cow: Any,
    *,
    workspace_id: uuid.UUID,
    human_user_id: uuid.UUID,
    site_id: uuid.UUID,
    human_session_id: uuid.UUID,
    permission: str = PERMISSION,
) -> None:
    await cow.native.fetchrow(
        "SELECT control.slaif_human_editor_workspace_assert($1,$2,$3,$4,$5,$6)",
        workspace_id,
        human_user_id,
        site_id,
        human_session_id,
        permission,
        True,
    )


async def _begin(
    cow: Any,
    *,
    workspace_id: uuid.UUID,
    human_user_id: uuid.UUID,
    site_id: uuid.UUID,
    human_session_id: uuid.UUID,
    permission: str,
    key: str,
    digest: str,
    operation_id: uuid.UUID,
) -> Any:
    return await cow.native.fetchrow(
        "SELECT * FROM control.slaif_human_editor_idempotency_begin("
        "$1,$2,$3,$4,$5,$6,$7,$8)",
        workspace_id,
        human_user_id,
        site_id,
        human_session_id,
        permission,
        key,
        digest,
        operation_id,
    )


async def _complete(
    cow: Any,
    *,
    workspace_id: uuid.UUID,
    human_user_id: uuid.UUID,
    site_id: uuid.UUID,
    human_session_id: uuid.UUID,
    permission: str,
    key: str,
    digest: str,
    operation_id: uuid.UUID,
    resource_id: uuid.UUID,
) -> None:
    await cow.native.fetchrow(
        "SELECT control.slaif_human_editor_idempotency_complete("
        "$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
        workspace_id,
        human_user_id,
        site_id,
        human_session_id,
        permission,
        key,
        digest,
        operation_id,
        201,
        json.dumps({"id": str(resource_id)}, sort_keys=True),
        "POST /api/editor/v1/pages",
        "page",
        resource_id,
    )


async def test_human_editor_envelope_uses_real_control_and_editor_roles(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    owner_pool = await database.role_pool("slaif_owner")
    control_pools = [await database.role_pool("slaif_control") for _ in range(2)]
    editor_pool = await database.role_pool("slaif_editor_runtime")
    site_id = uuid.uuid4()
    other_site_id = uuid.uuid4()
    human_user_id = uuid.uuid4()
    other_human_id = uuid.uuid4()
    human_session_id = uuid.uuid4()
    forged_session_id = uuid.uuid4()
    session_public_id = f"sas2_{uuid.uuid4().hex}"
    secret_digest = b"h" * 32
    csrf_digest = b"c" * 32
    site_key = f"editor-envelope-{uuid.uuid4().hex[:12]}"
    other_site_key = f"editor-other-{uuid.uuid4().hex[:12]}"

    try:
        await upgrade(database.settings)
        async with owner_pool.acquire() as owner:
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
                "VALUES ($1, 'OIDC', 'https://editor.test', $2, 'Editor Human'), "
                "($3, 'OIDC', 'https://editor.test', $4, 'Other Human')",
                human_user_id,
                str(human_user_id),
                other_human_id,
                str(other_human_id),
            )
            await owner.execute(
                "INSERT INTO control.site "
                "(id, site_key, display_name, default_locale, "
                "component_catalog_version) "
                "VALUES ($1, $2, 'Editor Site', 'en', 'catalog-v1'), "
                "($3, $4, 'Other Site', 'en', 'catalog-v1')",
                site_id,
                site_key,
                other_site_id,
                other_site_key,
            )
            await owner.execute(
                "INSERT INTO control.site_membership "
                "(site_id, user_account_id, role_key, delegation_ceiling) "
                "VALUES ($1, $2, 'SITE_EDITOR', 2)",
                site_id,
                human_user_id,
            )
            session = await owner.fetchrow(
                "SELECT * FROM control.slaif_create_human_session("
                "$1,$2,$3,$4,$5,$6,$7,$8)",
                human_session_id,
                session_public_id,
                secret_digest,
                csrf_digest,
                human_user_id,
                3600,
                7200,
                3600,
            )
            assert session is not None
            await owner.execute(
                "INSERT INTO content.page "
                "(id, site_id, slug, title, status, locale) "
                "VALUES ($1, $2, 'canonical-page', 'Canonical page', 'DRAFT', 'en')",
                uuid.uuid4(),
                site_id,
            )

        await reconcile(database.settings)

        async with control_pools[0].acquire() as control:
            assert (
                await control.fetchval("SELECT current_user::text") == "slaif_control"
            )
        async with editor_pool.acquire() as editor:
            assert (
                await editor.fetchval("SELECT current_user::text")
                == "slaif_editor_runtime"
            )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await editor.fetchval(
                    "SELECT count(*) FROM control.human_editor_idempotency"
                )

        workspace_ids = await asyncio.gather(
            *(_resolve(pool, site_id, human_user_id) for pool in control_pools)
        )
        assert workspace_ids[0] == workspace_ids[1]
        workspace_id = workspace_ids[0]

        key = f"page-{uuid.uuid4().hex}"
        digest = "a" * 64
        operation_id = uuid.uuid4()
        async with _cow(
            editor_pool, workspace_id=workspace_id, operation_id=operation_id
        ) as cow:
            await _assert_workspace(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
            )
            started = await _begin(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission=PERMISSION,
                key=key,
                digest=digest,
                operation_id=operation_id,
            )
            assert started[0] == "STARTED"
            service = ContentModelService.for_cow_session(cow)
            overlay = await service.create_page(
                site_id, "overlay-page", "Overlay page", "DRAFT", "en"
            )
            await _complete(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission=PERMISSION,
                key=key,
                digest=digest,
                operation_id=operation_id,
                resource_id=overlay.id,
            )

        composition_key = f"composition-{uuid.uuid4().hex}"
        composition_digest = "b" * 64
        composition_operation = uuid.uuid4()
        async with _cow(
            editor_pool,
            workspace_id=workspace_id,
            operation_id=composition_operation,
        ) as cow:
            await _assert_workspace(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission="component-structure:create",
            )
            started = await _begin(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission="component-structure:create",
                key=composition_key,
                digest=composition_digest,
                operation_id=composition_operation,
            )
            assert started[0] == "STARTED"
            service = ContentModelService.for_cow_session(cow)
            node = await service.add_composition_node(
                site_id, overlay.id, "Section", None, "default", 0, {}
            )
            visible_pages = await service.list_pages(site_id)
            assert {page.slug for page in visible_pages} == {
                "canonical-page",
                "overlay-page",
            }
            visible_nodes = await service.list_composition(overlay.id)
            assert [item.id for item in visible_nodes] == [node.id]
            await _complete(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission="component-structure:create",
                key=composition_key,
                digest=composition_digest,
                operation_id=composition_operation,
                resource_id=node.id,
            )

        async with owner_pool.acquire() as owner:
            canonical_pages = await owner.fetch(
                "SELECT * FROM content.slaif_page_list($1)", site_id
            )
            assert {row[2] for row in canonical_pages} == {"canonical-page"}

        replay_operation = uuid.uuid4()
        async with _cow(
            editor_pool, workspace_id=workspace_id, operation_id=replay_operation
        ) as cow:
            replay = await _begin(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission=PERMISSION,
                key=key,
                digest=digest,
                operation_id=replay_operation,
            )
            assert replay[0] == "REPLAY"
            assert replay[2] == 201
            replay_body = (
                json.loads(replay[3]) if isinstance(replay[3], str) else replay[3]
            )
            assert replay_body["id"] == str(overlay.id)

        mismatch_operation = uuid.uuid4()
        async with _cow(
            editor_pool, workspace_id=workspace_id, operation_id=mismatch_operation
        ) as cow:
            mismatch = await _begin(
                cow,
                workspace_id=workspace_id,
                human_user_id=human_user_id,
                site_id=site_id,
                human_session_id=human_session_id,
                permission=PERMISSION,
                key=key,
                digest="c" * 64,
                operation_id=mismatch_operation,
            )
            assert mismatch[0] == "MISMATCH"

        rollback_operation = uuid.uuid4()
        rollback_key = f"rollback-{uuid.uuid4().hex}"
        with pytest.raises(RuntimeError, match="forced rollback"):
            async with _cow(
                editor_pool, workspace_id=workspace_id, operation_id=rollback_operation
            ) as cow:
                await _assert_workspace(
                    cow,
                    workspace_id=workspace_id,
                    human_user_id=human_user_id,
                    site_id=site_id,
                    human_session_id=human_session_id,
                )
                assert (
                    await _begin(
                        cow,
                        workspace_id=workspace_id,
                        human_user_id=human_user_id,
                        site_id=site_id,
                        human_session_id=human_session_id,
                        permission=PERMISSION,
                        key=rollback_key,
                        digest="d" * 64,
                        operation_id=rollback_operation,
                    )
                )[0] == "STARTED"
                await ContentModelService.for_cow_session(cow).create_page(
                    site_id, "rolled-back", "Rolled back", "DRAFT", "en"
                )
                raise RuntimeError("forced rollback")

        invalid_contexts = (
            (other_human_id, site_id, human_session_id, PERMISSION),
            (human_user_id, other_site_id, human_session_id, PERMISSION),
            (human_user_id, site_id, human_session_id, "schema:migrate"),
        )
        for (
            invalid_human,
            invalid_site,
            invalid_session,
            invalid_permission,
        ) in invalid_contexts:
            with pytest.raises(asyncpg.PostgresError):
                async with _cow(
                    editor_pool,
                    workspace_id=workspace_id,
                    operation_id=uuid.uuid4(),
                ) as cow:
                    await _assert_workspace(
                        cow,
                        workspace_id=workspace_id,
                        human_user_id=invalid_human,
                        site_id=invalid_site,
                        human_session_id=invalid_session,
                        permission=invalid_permission,
                    )

        with pytest.raises(asyncpg.PostgresError):
            async with _cow(
                editor_pool,
                workspace_id=workspace_id,
                operation_id=uuid.uuid4(),
            ) as cow:
                await _assert_workspace(
                    cow,
                    workspace_id=workspace_id,
                    human_user_id=human_user_id,
                    site_id=site_id,
                    human_session_id=forged_session_id,
                )

        async with owner_pool.acquire() as owner:
            await owner.execute(
                "UPDATE control.site_membership SET status = 'INACTIVE' "
                "WHERE site_id = $1 AND user_account_id = $2",
                site_id,
                human_user_id,
            )
        with pytest.raises(asyncpg.PostgresError):
            async with _cow(
                editor_pool, workspace_id=workspace_id, operation_id=uuid.uuid4()
            ) as cow:
                await _assert_workspace(
                    cow,
                    workspace_id=workspace_id,
                    human_user_id=human_user_id,
                    site_id=site_id,
                    human_session_id=human_session_id,
                )

        async with owner_pool.acquire() as owner:
            await owner.execute(
                "UPDATE control.user_session SET revoked_at = now() WHERE id = $1",
                human_session_id,
            )
        with pytest.raises(asyncpg.PostgresError):
            async with _cow(
                editor_pool, workspace_id=workspace_id, operation_id=uuid.uuid4()
            ) as cow:
                await _assert_workspace(
                    cow,
                    workspace_id=workspace_id,
                    human_user_id=human_user_id,
                    site_id=site_id,
                    human_session_id=human_session_id,
                )

        async with owner_pool.acquire() as owner:
            await owner.execute(
                "UPDATE control.workspace SET expires_at = now() - interval '1 second' "
                "WHERE id = $1",
                workspace_id,
            )
            counts = await owner.fetchrow(
                "SELECT (SELECT count(*) FROM control.human_editor_idempotency), "
                "(SELECT count(*) FROM audit.human_editor_mutation), "
                "(SELECT count(*) FROM control.workspace WHERE id = $1)",
                workspace_id,
            )
            assert counts[0] == 2
            assert counts[1] == 2
            assert counts[2] == 1
    finally:
        await editor_pool.close()
        for pool in control_pools:
            await pool.close()
        await owner_pool.close()

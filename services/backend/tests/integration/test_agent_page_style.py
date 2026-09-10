"""Focused PostgreSQL proof for page-style/v1 inheritance and authority."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.config import ServiceSettings
from test_agent_mutations import (
    _agent_settings,
    _capability_with_scopes,
    _seed,
    _set_resource_constraints,
    asyncpg_cow_session,
)


@asynccontextmanager
async def _agent_client(
    database: AgentSiteDatabase,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database),
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://agent.test"
        ) as client:
            yield client


@pytest.mark.asyncio
async def test_page_style_is_typed_inherited_resettable_and_scope_bound(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(
        database,
        seeded,
        [
            "site:read",
            "page:create",
            "page:read",
            "page-style:write",
            "theme:read",
            "theme-tokens:write",
        ],
    )
    read_token = await _capability_with_scopes(
        database, seeded, ["site:read", "page:read"]
    )
    await _set_resource_constraints(
        database,
        seeded["workspace_id"],
        {
            "allowed_theme_palette_presets": ["ocean", "meadow", "ember"],
            "allowed_theme_typography_families": ["system", "serif"],
            "allowed_theme_tokens": [
                "palette.preset",
                "typography.family",
                "typography.scale",
                "typography.weight",
                "layout.content_width",
                "layout.spacing",
                "layout.grid_gap",
                "shape.radius",
                "shape.shadow",
            ],
        },
    )
    async with _agent_client(database) as client:
        created = await client.post(
            "/api/agent/v1/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-page-create",
            },
            json={"slug": "styled", "title": "Styled", "locale": "en-US"},
        )
        assert created.status_code == 201, created.text
        page_id = UUID(created.json()["record"]["id"])

        initial = await client.get(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert initial.status_code == 200, initial.text
        assert initial.json()["overrides"] == {}
        assert initial.json()["resolved"]["palette"]["preset"] == "ocean"
        assert initial.json()["row_version"] == 1

        equal_inherited = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-explicit-inherited-value",
            },
            json={
                "expected_row_version": 1,
                "typography": {"family": "system"},
            },
        )
        assert equal_inherited.status_code == 200, equal_inherited.text
        assert equal_inherited.json()["record"]["row_version"] == 2
        assert equal_inherited.json()["record"]["overrides"] == {
            "typography": {"family": "system"}
        }

        changed_body = {
            "expected_row_version": 2,
            "palette": {"preset": "meadow"},
            "typography": {
                "family": "serif",
                "scale": "spacious",
                "weight": "bold",
            },
            "layout": {
                "content_width": "xl",
                "spacing": "lg",
                "grid_gap": "sm",
            },
            "shape": {"radius": "lg", "shadow": "md"},
            "reset_tokens": [],
        }
        changed = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-all-groups",
            },
            json=changed_body,
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["action"] == "PAGE_STYLE_UPDATED"
        assert changed.json()["record"]["row_version"] == 3
        assert changed.json()["record"]["overrides"]["layout"] == {
            "content_width": "xl",
            "grid_gap": "sm",
            "spacing": "lg",
        }

        replay = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-all-groups",
            },
            json=changed_body,
        )
        assert replay.status_code == 200
        assert replay.content == changed.content

        mismatch = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-all-groups",
            },
            json={**changed_body, "palette": {"preset": "ember"}},
        )
        assert mismatch.status_code == 409, mismatch.text

        stale = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-stale-version",
            },
            json={
                "expected_row_version": 2,
                "palette": {"preset": "ember"},
            },
        )
        assert stale.status_code == 409, stale.text

        read_no_effect = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-read-no-effect",
            },
            json={
                "expected_row_version": 3,
                "palette": {"preset": "meadow"},
            },
        )
        assert read_no_effect.status_code == 200, read_no_effect.text
        assert read_no_effect.json()["action"] is None
        assert read_no_effect.json()["record"]["row_version"] == 3

        denied = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {read_token}",
                "Idempotency-Key": "page-style-read-change",
            },
            json={
                "expected_row_version": 3,
                "palette": {"preset": "ember"},
            },
        )
        assert denied.status_code == 403, denied.text

        reset = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-reset-palette",
            },
            json={
                "expected_row_version": 3,
                "reset_tokens": ["palette.preset"],
            },
        )
        assert reset.status_code == 200, reset.text
        assert reset.json()["record"]["row_version"] == 4
        assert "palette" not in reset.json()["record"]["overrides"]
        assert reset.json()["record"]["resolved"]["palette"]["preset"] == "ocean"

        theme_token = await _capability_with_scopes(
            database,
            seeded,
            ["site:read", "page:read", "theme:read", "theme-tokens:write"],
        )
        theme = await client.patch(
            "/api/agent/v1/theme",
            headers={
                "Authorization": f"Bearer {theme_token}",
                "Idempotency-Key": "page-style-site-theme",
            },
            json={"expected_row_version": 1, "palette": {"preset": "ember"}},
        )
        assert theme.status_code == 200, theme.text
        follows_theme = await client.get(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert follows_theme.json()["resolved"]["palette"]["preset"] == "ember"
        assert follows_theme.json()["resolved"]["typography"]["family"] == "serif"

        invalid = await client.patch(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": "page-style-invalid-overlap",
            },
            json={
                "expected_row_version": 4,
                "palette": {"preset": "meadow"},
                "reset_tokens": ["palette.preset"],
            },
        )
        assert invalid.status_code == 422, invalid.text

        agent_pool = await database.role_pool("slaif_agent_runtime")
        try:
            async with asyncpg_cow_session(
                agent_pool,
                session_id=seeded["workspace_id"],
                operation_id=uuid4(),
            ) as cow:
                with pytest.raises(asyncpg.PostgresError, match="PAGE_STYLE_"):
                    await cow.native.fetchrow(
                        "SELECT * FROM content.slaif_agent_page_style_update("
                        "$1,$2,$3,$4::jsonb,$5::jsonb,$6::jsonb,$7::jsonb,$8)",
                        seeded["site_id"],
                        page_id,
                        4,
                        '{"preset":null}',
                        None,
                        None,
                        None,
                        [],
                    )
                await cow.rollback()
        finally:
            await agent_pool.close()

        foreign = await client.get(
            f"/api/agent/v1/pages/{seeded['page_b_id']}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert foreign.status_code == 404, foreign.text

        final = await client.get(
            f"/api/agent/v1/pages/{page_id}/style",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert final.status_code == 200
        assert final.json()["row_version"] == 4
        assert final.json()["overrides"]["typography"] == {
            "family": "serif",
            "scale": "spacious",
            "weight": "bold",
        }

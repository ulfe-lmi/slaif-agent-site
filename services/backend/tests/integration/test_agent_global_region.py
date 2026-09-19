"""Focused PostgreSQL proof for the site-global region (header/footer) plane."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.app import create_app as create_control_app
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from sqlalchemy.exc import DBAPIError
from test_agent_mutations import (
    _agent_settings,
    _capability_with_scopes,
    _seed,
    _workspace_capability,
)
from test_human_agent_session_control import _control_settings

READ_SCOPES = ["site:read", "global-region:read"]
WRITE_SCOPES = [
    "site:read",
    "global-region:read",
    "global-region:write",
    "header-footer:write",
]


def _region_id(site_id: UUID, region_key: str) -> UUID:
    return UUID(bytes=hashlib.md5(f"{site_id}:{region_key}".encode()).digest())


@asynccontextmanager
async def _agent_client(
    database: AgentSiteDatabase,
    *,
    lock_timeout_ms: int = 500,
    statement_timeout_ms: int = 2000,
    command_timeout_seconds: float = 2,
    timeout: float = 30.0,
) -> AsyncIterator[httpx.AsyncClient]:
    database_settings = _agent_settings(database).model_copy(
        update={
            "lock_timeout_ms": lock_timeout_ms,
            "statement_timeout_ms": statement_timeout_ms,
            "command_timeout_seconds": command_timeout_seconds,
        }
    )
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=database_settings,
    )
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://agent.test",
            timeout=timeout,
        ) as client:
            yield client


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _base_rows(
    database: AgentSiteDatabase, site_id: UUID
) -> list[tuple[Any, ...]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return list(
            await owner.fetch(
                "SELECT id,region_key,variant,content::text,row_version "
                "FROM content.site_global_region_base WHERE site_id=$1 "
                "ORDER BY region_key",
                site_id,
            )
        )


async def _overlay_rows(
    database: AgentSiteDatabase, site_id: UUID
) -> list[tuple[Any, ...]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return list(
            await owner.fetch(
                "SELECT id,region_key,variant,content::text,row_version "
                "FROM content.site_global_region_changes WHERE site_id=$1 "
                "ORDER BY region_key",
                site_id,
            )
        )


async def _audit_rows(
    database: AgentSiteDatabase, workspace_id: UUID
) -> list[tuple[Any, ...]]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return list(
            await owner.fetch(
                "SELECT operation_id,resource_type,resource_id,action,http_method,"
                "response_status,quota_kind "
                "FROM audit.agent_mutation "
                "WHERE workspace_id=$1 AND action='GLOBAL_REGION_UPDATED' "
                "ORDER BY operation_id",
                workspace_id,
            )
        )


@pytest.mark.asyncio
async def test_global_region_defaults_are_lazy_deterministic_and_replay_is_noop(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(database, seeded, WRITE_SCOPES)
    header_id = _region_id(seeded["site_id"], "header")
    footer_id = _region_id(seeded["site_id"], "footer")

    async with _agent_client(database) as client:
        listed = await client.get("/api/agent/v1/global-regions", headers=_auth(token))
        assert listed.status_code == 200, listed.text
        records = {record["region_key"]: record for record in listed.json()}
        assert set(records) == {"header", "footer"}
        header, footer = records["header"], records["footer"]
        assert header["id"] == str(header_id)
        assert footer["id"] == str(footer_id)
        assert header["site_id"] == str(seeded["site_id"])
        assert header["variant"] == "institutional"
        assert header["content"] == {
            "nav": [
                {
                    "label": "agent-mutation",
                    "target": {"kind": "internal", "value": "/"},
                }
            ]
        }
        assert footer["variant"] == "single-column"
        assert footer["content"] == {"links": [], "note": ""}
        assert header["schema_version"] == "global-region/v1"
        assert header["row_version"] == 1
        assert footer["row_version"] == 1
        # Defaults are virtual: nothing is materialized until a real write.
        assert await _base_rows(database, seeded["site_id"]) == []

        replay = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={
                **_auth(token),
                "Idempotency-Key": "region-replay-noop",
            },
            json={
                "expected_row_version": 1,
                "variant": "institutional",
                "content": header["content"],
            },
        )
        assert replay.status_code == 200, replay.text
        assert replay.json()["record"]["row_version"] == 1
        assert await _base_rows(database, seeded["site_id"]) == []
        assert await _audit_rows(database, seeded["workspace_id"]) == []

        unknown = await client.patch(
            "/api/agent/v1/global-regions/" + str(uuid4()),
            headers={
                **_auth(token),
                "Idempotency-Key": "region-replay-unknown",
            },
            json={"expected_row_version": 1, "variant": "institutional"},
        )
        assert unknown.status_code == 404, unknown.text


@pytest.mark.asyncio
async def test_global_region_write_authority_is_deferred_and_level_bound(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    read_only_token = await _capability_with_scopes(database, seeded, READ_SCOPES)
    no_header_footer_token = await _capability_with_scopes(
        database,
        seeded,
        ["site:read", "global-region:read", "global-region:write"],
    )
    header_id = _region_id(seeded["site_id"], "header")
    new_content = {
        "nav": [
            {"label": "Home", "target": {"kind": "internal", "value": "/"}},
            {
                "label": "Docs",
                "target": {"kind": "external", "value": "https://docs.example.org/"},
            },
        ]
    }

    async with _agent_client(database) as client:
        # A read-only capability can read but not change anything.
        listed = await client.get(
            "/api/agent/v1/global-regions", headers=_auth(read_only_token)
        )
        assert listed.status_code == 200
        denied_read_only = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={**_auth(read_only_token), "Idempotency-Key": "region-read-only"},
            json={"expected_row_version": 1, "content": new_content},
        )
        assert denied_read_only.status_code == 403, denied_read_only.text

        # A variant change additionally requires header-footer:write.
        denied_variant = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={
                **_auth(no_header_footer_token),
                "Idempotency-Key": "region-variant-denied",
            },
            json={"expected_row_version": 1, "variant": "minimal"},
        )
        assert denied_variant.status_code == 403, denied_variant.text

        # A content-only change needs only global-region:write.
        content_only = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={
                **_auth(no_header_footer_token),
                "Idempotency-Key": "region-content-only",
            },
            json={"expected_row_version": 1, "content": new_content},
        )
        assert content_only.status_code == 200, content_only.text
        assert content_only.json()["record"]["row_version"] == 2
        assert content_only.json()["record"]["variant"] == "institutional"

        # A lower delegation level cannot use the L4 region write scopes:
        # the trusted workspace creator filters effective scopes by the
        # preset's delegation level, so the L4 scopes never enter the L3
        # workspace or its capabilities.
        control_adapter = ControlDatabase(_control_settings(database))
        await control_adapter.start()
        try:
            control_app = create_control_app(
                settings=ServiceSettings.for_test(), database=control_adapter
            )
            l3_session = await control_adapter.human_session_service().create(
                seeded["delegator_id"]
            )
            l3_headers = {
                "cookie": (
                    f"slaif_session={l3_session.token.get_secret_value()}; "
                    f"slaif_csrf={l3_session.csrf_token.get_secret_value()}"
                ),
                "X-CSRF-Token": l3_session.csrf_token.get_secret_value(),
            }
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=control_app),
                base_url="http://control.test",
            ) as control:
                created = await control.post(
                    f"/api/control/v1/sites/{seeded['site_id']}/workspaces/",
                    json={
                        "title": "Region L3 Workspace",
                        "delegation_preset": "L3_SITE_DESIGNER",
                    },
                    headers={
                        **l3_headers,
                        "Idempotency-Key": "region-l3-workspace",
                    },
                )
                assert created.status_code == 201, created.text
                l3_workspace = UUID(created.json()["workspace_id"])
                assert "global-region:write" not in created.json()["effective_scopes"]
                assert "header-footer:write" not in created.json()["effective_scopes"]
                l3_capability = await control.post(
                    f"/api/control/v1/sites/{seeded['site_id']}/workspaces/"
                    f"{l3_workspace}/capabilities/",
                    headers={
                        **l3_headers,
                        "Idempotency-Key": "region-l3-capability",
                    },
                )
                assert l3_capability.status_code == 201, l3_capability.text
                l3_token = l3_capability.json()["token"]
        finally:
            await control_adapter.stop()
        # The L3 workspace sees only the canonical row (its overlay is
        # empty): probe that state so the trusted L3 workspace's missing
        # L4 region write scope is the deciding denial (P0007).
        l3_denied = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={**_auth(l3_token), "Idempotency-Key": "region-l3-denied"},
            json={"expected_row_version": 1, "variant": "minimal"},
        )
        # The trusted L3 workspace never held the L4 region write scope, so
        # the SQL scope barrier denies the mutation (P0007).
        assert l3_denied.status_code == 403, l3_denied.text
        assert l3_workspace != seeded["workspace_id"]


@pytest.mark.asyncio
async def test_global_region_rejects_hostile_documents_and_foreign_sites(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(database, seeded, WRITE_SCOPES)
    header_id = _region_id(seeded["site_id"], "header")
    footer_id = _region_id(seeded["site_id"], "footer")
    other_site_header = _region_id(seeded["site_b_id"], "header")

    nav_entry = {"label": "N", "target": {"kind": "internal", "value": "/x"}}
    hostile = [
        ("header", {"expected_row_version": 1}),
        ("header", {"expected_row_version": 1, "variant": "bogus"}),
        (
            "header",
            {"expected_row_version": 1, "content": {"nav": []}},
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {"nav": [dict(nav_entry) for _ in range(13)]},
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {"nav": [{"label": " x", "target": nav_entry["target"]}]},
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {
                    "nav": [
                        {
                            "label": "X",
                            "target": {"kind": "internal", "value": "/api/x"},
                        }
                    ]
                },
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {
                    "nav": [
                        {
                            "label": "X",
                            "target": {
                                "kind": "external",
                                "value": "javascript:alert(1)",
                            },
                        }
                    ]
                },
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {
                    "nav": [
                        {
                            "label": "X",
                            "target": {
                                "kind": "external",
                                "value": "https://user:pass@example.com/",
                            },
                        }
                    ]
                },
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {
                    "nav": [
                        {
                            "label": "X",
                            "target": {
                                "kind": "page",
                                "value": str(seeded["page_b_id"]),
                            },
                        }
                    ]
                },
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {
                    "nav": [
                        {"label": "X", "target": {"kind": "page", "value": "no-uuid"}}
                    ]
                },
            },
        ),
        (
            "header",
            {
                "expected_row_version": 1,
                "content": {
                    "nav": [
                        {
                            "label": "X",
                            "target": {"kind": "internal", "value": "/x", "raw": "<b>"},
                        }
                    ]
                },
            },
        ),
        (
            "footer",
            {
                "expected_row_version": 1,
                "content": {
                    "links": [dict(nav_entry) for _ in range(17)],
                },
            },
        ),
        (
            "footer",
            {"expected_row_version": 1, "content": {"links": [], "note": "y" * 4097}},
        ),
        (
            "header",
            {"expected_row_version": 1, "content": {"nav": [], "links": []}},
        ),
    ]
    async with _agent_client(database) as client:
        for index, (_target, body) in enumerate(hostile):
            region_id = header_id if _target == "header" else footer_id
            response = await client.patch(
                f"/api/agent/v1/global-regions/{region_id}",
                headers={
                    **_auth(token),
                    "Idempotency-Key": f"region-hostile-{index}",
                },
                json=body,
            )
            assert response.status_code == 422, (
                f"case {index} {body}: {response.status_code} {response.text}"
            )
        # The rejected writes must not have moved the region state.
        unchanged = await client.get(
            "/api/agent/v1/global-regions", headers=_auth(token)
        )
        unchanged_records = {
            record["region_key"]: record for record in unchanged.json()
        }
        assert unchanged_records["header"]["row_version"] == 1
        assert unchanged_records["footer"]["row_version"] == 1

        foreign = await client.patch(
            f"/api/agent/v1/global-regions/{other_site_header}",
            headers={**_auth(token), "Idempotency-Key": "region-other-site"},
            json={"expected_row_version": 1, "variant": "minimal"},
        )
        assert foreign.status_code == 404, foreign.text

        stale = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={**_auth(token), "Idempotency-Key": "region-stale-version"},
            json={"expected_row_version": 9, "variant": "minimal"},
        )
        assert stale.status_code == 409, stale.text
        missing_version = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={**_auth(token), "Idempotency-Key": "region-missing-version"},
            json={"variant": "minimal"},
        )
        assert missing_version.status_code == 422, missing_version.text


@pytest.mark.asyncio
async def test_global_region_idempotent_replay_is_bounded_and_audited_once(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(database, seeded, WRITE_SCOPES)
    footer_id = _region_id(seeded["site_id"], "footer")
    content = {
        "links": [
            {"label": "Legal", "target": {"kind": "internal", "value": "/legal"}}
        ],
        "note": "bounded",
    }
    body = {"expected_row_version": 1, "content": content}

    async with _agent_client(database) as client:
        first = await client.patch(
            f"/api/agent/v1/global-regions/{footer_id}",
            headers={**_auth(token), "Idempotency-Key": "region-once"},
            json=body,
        )
        assert first.status_code == 200, first.text
        first_operation = first.json()["operation_id"]

        replay = await client.patch(
            f"/api/agent/v1/global-regions/{footer_id}",
            headers={**_auth(token), "Idempotency-Key": "region-once"},
            json=body,
        )
        assert replay.status_code == 200, replay.text
        assert replay.json()["operation_id"] == first_operation
        assert replay.json()["record"]["row_version"] == 2

        changed = await client.patch(
            f"/api/agent/v1/global-regions/{footer_id}",
            headers={**_auth(token), "Idempotency-Key": "region-once"},
            json={"expected_row_version": 2, "content": {"links": [], "note": "other"}},
        )
        assert changed.status_code == 409, changed.text

        # Replaying the successful digest again stays bounded: one audit row.
        again = await client.patch(
            f"/api/agent/v1/global-regions/{footer_id}",
            headers={**_auth(token), "Idempotency-Key": "region-once"},
            json=body,
        )
        assert again.status_code == 200, again.text
        audits = await _audit_rows(database, seeded["workspace_id"])
        assert len(audits) == 1
        (
            _operation_id,
            resource_type,
            resource_id,
            action,
            http_method,
            response_status,
            quota_kind,
        ) = audits[0]
        assert resource_type == "global_region"
        assert UUID(str(resource_id)) == footer_id
        assert action == "GLOBAL_REGION_UPDATED"
        assert http_method == "PATCH"
        assert response_status == 200
        assert quota_kind == "mutation"
        assert str(_operation_id) == first_operation


@pytest.mark.asyncio
async def test_global_region_two_waiters_serialize_deterministically(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(database, seeded, WRITE_SCOPES)
    header_id = _region_id(seeded["site_id"], "header")

    async with _agent_client(
        database,
        lock_timeout_ms=8000,
        statement_timeout_ms=20000,
        command_timeout_seconds=30,
    ) as client:
        async with owner_connection(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
        ) as blocker:
            async with blocker.transaction():
                lock_key = await blocker.fetchval(
                    "SELECT hashtextextended($1, 996)",
                    f"{seeded['workspace_id']}:{seeded['site_id']}:global-region",
                )
                await blocker.fetchval(
                    "SELECT pg_advisory_xact_lock($1::bigint)", lock_key
                )
                tasks = [
                    asyncio.create_task(
                        client.patch(
                            f"/api/agent/v1/global-regions/{header_id}",
                            headers={
                                **_auth(token),
                                "Idempotency-Key": f"region-waiter-{index}",
                            },
                            json={
                                "expected_row_version": 1,
                                "content": {
                                    "nav": [
                                        {
                                            "label": f"W{index}",
                                            "target": {
                                                "kind": "internal",
                                                "value": "/",
                                            },
                                        }
                                    ]
                                },
                            },
                        )
                    )
                    for index in range(2)
                ]
                # Both requests must be in flight: the first waiter parks on
                # the region advisory lock while the second parks on the
                # capability quota row held by the first waiter's open
                # transaction.  Releasing the blocker then lets exactly one
                # commit ahead of the other.
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    overlapping = await blocker.fetchval(
                        "SELECT EXISTS ("
                        "SELECT 1 FROM pg_locks a "
                        "JOIN pg_locks t ON t.pid <> a.pid "
                        "WHERE a.locktype='advisory' AND NOT a.granted "
                        "AND a.objsubid=1 "
                        "AND a.classid::bigint = (($1::bigint >> 32) "
                        "& 4294967295) "
                        "AND a.objid::bigint = ($1::bigint & 4294967295) "
                        "AND t.locktype='transactionid' AND NOT t.granted)",
                        lock_key,
                    )
                    if overlapping:
                        break
                    await asyncio.sleep(0.01)
                else:
                    for task in tasks:
                        task.cancel()
                    raise AssertionError(
                        "expected overlapping waiters on the region lock"
                    )
        responses = await asyncio.gather(*tasks)
    statuses = sorted(response.status_code for response in responses)
    assert statuses == [200, 409], [f"{r.status_code} {r.text}" for r in responses]
    winner = next(r for r in responses if r.status_code == 200)
    assert winner.json()["record"]["row_version"] == 2
    audits = await _audit_rows(database, seeded["workspace_id"])
    assert len(audits) == 1


@pytest.mark.asyncio
async def test_global_region_cow_overlay_is_isolated_and_persists_across_restart(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(database, seeded, WRITE_SCOPES)
    header_id = _region_id(seeded["site_id"], "header")

    async with _agent_client(database) as client:
        changed = await client.patch(
            f"/api/agent/v1/global-regions/{header_id}",
            headers={**_auth(token), "Idempotency-Key": "region-overlay"},
            json={
                "expected_row_version": 1,
                "variant": "minimal",
                "content": {
                    "nav": [
                        {"label": "W", "target": {"kind": "internal", "value": "/"}}
                    ]
                },
            },
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["record"]["row_version"] == 2

        # The change lives in the workspace overlay, not in canonical base.
        base = await _base_rows(database, seeded["site_id"])
        assert base == []
        overlay = await _overlay_rows(database, seeded["site_id"])
        assert len(overlay) == 1
        assert overlay[0][0] == header_id
        assert overlay[0][1] == "header"
        assert overlay[0][2] == "minimal"

        # A second workspace on the same site sees the virtual default.
        second_token, second_workspace = await _workspace_capability(
            database, seeded, READ_SCOPES, "Region Second Workspace"
        )
        listed = await client.get(
            "/api/agent/v1/global-regions", headers=_auth(second_token)
        )
        assert listed.status_code == 200, listed.text
        second_header = next(
            record for record in listed.json() if record["region_key"] == "header"
        )
        assert second_header["variant"] == "institutional"
        assert second_header["row_version"] == 1
        assert second_workspace != seeded["workspace_id"]
    # Application restart: the same capability still observes its overlay.
    async with _agent_client(database) as restarted:
        seen = await restarted.get("/api/agent/v1/global-regions", headers=_auth(token))
        assert seen.status_code == 200, seen.text
        header = next(
            record for record in seen.json() if record["region_key"] == "header"
        )
        assert header["variant"] == "minimal"
        assert header["row_version"] == 2


@pytest.mark.asyncio
async def test_global_region_downgrade_refuses_region_data_and_audit(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    token = await _capability_with_scopes(database, seeded, WRITE_SCOPES)
    footer_id = _region_id(seeded["site_id"], "footer")
    async with _agent_client(database) as client:
        changed = await client.patch(
            f"/api/agent/v1/global-regions/{footer_id}",
            headers={**_auth(token), "Idempotency-Key": "region-downgrade-data"},
            json={
                "expected_row_version": 1,
                "content": {"links": [], "note": "keep me"},
            },
        )
        assert changed.status_code == 200, changed.text

    # Unreviewed workspace state in the overlay blocks any region DDL.
    with pytest.raises(DBAPIError, match="REGION_MIGRATION_PENDING_COW"):
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="066_001",
        )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM content.site_global_region_changes "
                "WHERE site_id=$1",
                seeded["site_id"],
            )
            == 1
        )
        await owner.execute(
            "DELETE FROM content.site_global_region_changes WHERE site_id=$1",
            seeded["site_id"],
        )
        await owner.execute(
            "INSERT INTO content.site_global_region_base ("
            "id, site_id, region_key, variant, content, schema_version,"
            " row_version, created_at, updated_at) VALUES "
            "($1, $2, 'header', 'institutional', $3::jsonb, "
            "'global-region/v1', 1, now(), now())",
            _region_id(seeded["site_id"], "header"),
            seeded["site_id"],
            json.dumps(
                {
                    "nav": [
                        {
                            "label": "agent-mutation",
                            "target": {"kind": "internal", "value": "/"},
                        }
                    ]
                }
            ),
        )
        assert (
            await owner.fetchval(
                "SELECT count(*) FROM content.site_global_region_base WHERE site_id=$1",
                seeded["site_id"],
            )
            == 1
        )
    with pytest.raises(DBAPIError, match="REGION_MIGRATION_DATA_PRESENT"):
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="066_001",
        )
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "DELETE FROM content.site_global_region_base WHERE site_id=$1",
            seeded["site_id"],
        )
    with pytest.raises(DBAPIError, match="REGION_MIGRATION_AUDIT_PRESENT"):
        await run_migration(
            database.settings.resolved_owner_dsn(),
            expected_database=database.name,
            operation="downgrade",
            revision="066_001",
        )

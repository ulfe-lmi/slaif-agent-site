"""Focused C3 + P6 semantics for the 078_001 trusted mutation completion journal.

Private candidate for PRIMARY integration into tests/integration.  It asserts
the DESIRED durable behavior of ``audit.mutation_completion`` through the real
HTTP surfaces and the real fixture roles; it is a bounded subset of the 078
verification criteria (not a claim that all C1..C6 are proved here):

1. Agent explicit no-effect (read-only theme request): HTTP 200 with
   ``action`` None, exactly one journal row with disposition ``no_effect``
   and the actual principal, NO ``audit.agent_mutation`` row for the
   operation, no new pending foundation operation, an exact same-key/same-body
   replay adding no second journal row, and a changed-body same-key request
   keeping the actual 409 without journal growth.
2. Canonical same-hash media dedupe (human and agent re-uploads): HTTP 201
   with the original canonical record, zero new pending operations in both
   workspaces, the canonical row untouched, but ORDINARY ``completed`` journal
   rows plus their family audit rows (a normal completion may legitimately
   have zero COW rows), and stable same-key replays.
3. P6 request-identity privacy: the client-supplied idempotency key is a
   fake secret-shaped sentinel; the journal stores only the opaque 64-hex
   SHA-256 ``request_identity`` and NO raw sentinel bytes, while the existing
   raw-key control ledger row is unchanged.

All reads of ``audit.mutation_completion`` and the control ledgers go through
the trusted OWNER fixture connection (the journal table is deliberately
denied to every runtime role); pending-operation probes use the public
foundation ``get_session_operations`` surface via the reviewer role pool,
AFTER each request has committed.  Helpers are reused from the existing
integration modules; nothing is mocked or stubbed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.media_service.app import create_app as create_media_app
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.store import MediaStore
from test_agent_mutations import _capability_with_scopes, _seed
from test_agent_theme_boundaries import _agent_client, _theme_state
from test_media_security_lifecycle import (
    _control_settings,
    _headers,
    _media_settings,
)
from test_media_service import _agent_settings as _media_agent_settings
from test_media_workspace_existing_assets import (
    CANONICAL_PNG,
    _assert_authoritative_workspace,
    _canonical_row,
    _content_operations,
    _record_original,
    _seed_canonical_media,
)
from test_media_workspace_isolation import _seed_agent_fixture

# A fake capability-shaped client key.  It is valid per the public
# idempotency-key grammar and never represents a real credential; it exists
# to prove the journal keeps only the opaque SHA-256 identity of such keys.
SENTINEL_IDEMPOTENCY_KEY = "secret-sentinel-083-11-a.token-abc"

_THEME_READ_SCOPES = ["site:read", "theme:read"]


async def _owner(database: AgentSiteDatabase) -> Any:
    return owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    )


async def _journal_row(database: AgentSiteDatabase, operation_id: UUID) -> Any:
    """Fetch the journal identity row for one completed operation (owner)."""
    async with await _owner(database) as owner:
        return await owner.fetchrow(
            "SELECT family, site_id, workspace_id, capability_id, "
            "human_user_id, request_identity, request_digest, resource_type, "
            "resource_id, disposition, schema_version "
            "FROM audit.mutation_completion WHERE operation_id = $1",
            operation_id,
        )


async def _journal_count(database: AgentSiteDatabase, operation_id: UUID) -> int:
    async with await _owner(database) as owner:
        count: int = await owner.fetchval(
            "SELECT count(*) FROM audit.mutation_completion WHERE operation_id = $1",
            operation_id,
        )
        return count


def _key_identity(key: str) -> str:
    """The journal's bounded request identity for a raw client key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _assert_sentinel_absent(row: Any) -> None:
    """P6: no raw client-key bytes anywhere in the durable journal row."""
    for value in row.values():
        assert value is None or SENTINEL_IDEMPOTENCY_KEY not in str(value)


@pytest.mark.asyncio
async def test_agent_theme_explicit_no_effect_journal_and_replay(
    agent_site_database: AgentSiteDatabase,
) -> None:
    """Case 1 + 3: explicit no-effect journal, replay/409, key privacy."""
    database = agent_site_database
    _unused_token, seeded = await _seed(database)
    read_token = await _capability_with_scopes(
        database, seeded, list(_THEME_READ_SCOPES)
    )
    reviewer_pool = await database.role_pool("slaif_reviewer")
    try:
        async with await _owner(database) as owner:
            capability_id = await owner.fetchval(
                "SELECT id FROM control.capability "
                "WHERE workspace_id = $1 AND scopes = $2::jsonb",
                seeded["workspace_id"],
                json.dumps(_THEME_READ_SCOPES),
            )
        baseline = await _theme_state(database, seeded, reviewer_pool)
        body = {"expected_row_version": 1, "palette": {"preset": "ocean"}}

        async with _agent_client(database) as client:
            no_effect = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": SENTINEL_IDEMPOTENCY_KEY,
                },
                json=body,
            )
            assert no_effect.status_code == 200, no_effect.text
            response = no_effect.json()
            assert response["action"] is None
            assert response["record"]["row_version"] == 1
            operation_id = UUID(response["operation_id"])
            resource_id = UUID(response["record"]["id"])

            row = await _journal_row(database, operation_id)
            assert row is not None, "explicit no-effect must be journaled"
            assert row["family"] == "agent"
            assert row["site_id"] == seeded["site_id"]
            assert row["workspace_id"] == seeded["workspace_id"]
            assert row["capability_id"] == capability_id
            assert row["human_user_id"] is None
            assert row["request_identity"] == _key_identity(SENTINEL_IDEMPOTENCY_KEY)
            assert len(row["request_digest"]) == 64
            assert row["resource_type"] == "theme"
            assert row["resource_id"] == resource_id
            assert row["disposition"] == "no_effect"
            assert row["schema_version"] == "mutation-completion/v1"
            _assert_sentinel_absent(row)
            assert SENTINEL_IDEMPOTENCY_KEY not in no_effect.text

            # The existing raw-key control ledger row is unchanged behavior.
            async with await _owner(database) as owner:
                ledger_key = await owner.fetchval(
                    "SELECT idempotency_key FROM control.agent_idempotency "
                    "WHERE operation_id = $1",
                    operation_id,
                )
                family_audit_count = await owner.fetchval(
                    "SELECT count(*) FROM audit.agent_mutation WHERE operation_id = $1",
                    operation_id,
                )
            assert ledger_key == SENTINEL_IDEMPOTENCY_KEY
            assert family_audit_count == 0

            # No canonical/COW/quota/audit/watermark/pending-op movement.
            after = await _theme_state(database, seeded, reviewer_pool)
            assert after[0] == baseline[0]
            assert after[1] == baseline[1]
            assert after[2][0] == baseline[2][0]
            assert after[2][2] == baseline[2][2]
            assert after[3] == baseline[3]
            assert after[4] == baseline[4]
            assert after[2][1] == baseline[2][1] + 1

            replay = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": SENTINEL_IDEMPOTENCY_KEY,
                },
                json=body,
            )
            assert replay.status_code == 200, replay.text
            assert replay.content == no_effect.content
            assert await _journal_count(database, operation_id) == 1
            assert (await _theme_state(database, seeded, reviewer_pool))[2][1] == (
                baseline[2][1] + 1
            )

            mismatch = await client.patch(
                "/api/agent/v1/theme",
                headers={
                    "Authorization": f"Bearer {read_token}",
                    "Idempotency-Key": SENTINEL_IDEMPOTENCY_KEY,
                },
                json={"expected_row_version": 1, "palette": {"preset": "ember"}},
            )
            assert mismatch.status_code == 409, mismatch.text
            assert await _journal_count(database, operation_id) == 1
            assert (await _theme_state(database, seeded, reviewer_pool))[2][1] == (
                baseline[2][1] + 1
            )
    finally:
        await reviewer_pool.close()


@pytest.mark.asyncio
async def test_media_same_hash_dedupe_completed_journal_zero_ops(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
) -> None:
    """Case 2: ordinary dedupe completions journal with zero COW ops."""
    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    store = MediaStore(tmp_path / "media")
    content_hash = hashlib.sha256(CANONICAL_PNG).hexdigest()
    asset_id = uuid4()
    await _seed_canonical_media(
        database,
        store,
        site_id=ids["site_a"],
        uploaded_by=ids["user_a"],
        asset_id=asset_id,
        content_hash=content_hash,
        public_status="public",
    )
    baseline_row = await _canonical_row(database, asset_id)
    await _assert_authoritative_workspace(
        database, ids["site_a"], ids["user_a"], ids["workspace_a"]
    )
    ops_a_before = await _content_operations(database, ids["workspace_a"])
    ops_agent_before = await _content_operations(database, ids["agent_workspace"])
    async with await _owner(database) as owner:
        agent_capability_id = await owner.fetchval(
            "SELECT id FROM control.capability WHERE workspace_id = $1",
            ids["agent_workspace"],
        )

    control = ControlDatabase(_control_settings(database))
    media_database = MediaDatabase(_media_settings(database, store.root))
    media_app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_database.settings,
        database=media_database,
        store=store,
    )
    agent_app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_media_agent_settings(database, store.root),
    )
    await control.start()
    try:
        async with media_app.router.lifespan_context(media_app):
            async with agent_app.router.lifespan_context(agent_app):
                session_a = await control.human_session_service().create(ids["user_a"])
                async with (
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=agent_app),
                        base_url="http://completion-dedupe-agent.test",
                    ) as agent_client,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=media_app),
                        base_url="http://completion-dedupe.test",
                    ) as media_client,
                ):
                    upload_url = f"/v1/sites/{ids['site_a']}/assets"

                    human = await media_client.post(
                        upload_url,
                        headers=_headers(session_a, "dedupe-journal-human"),
                        data={
                            "alt_text": "H dedupe alt",
                            "metadata": json.dumps({"origin": "h"}),
                        },
                        files={"file": ("h.png", CANONICAL_PNG, "image/png")},
                    )
                    assert human.status_code == 201, human.text
                    assert human.headers.get("x-media-replay") == "false"
                    _record_original(human.json()["record"], asset_id, content_hash)
                    human_op = UUID(human.json()["operation_id"])

                    row = await _journal_row(database, human_op)
                    assert row is not None, "dedupe upload must be journaled"
                    assert row["family"] == "media"
                    assert row["site_id"] == ids["site_a"]
                    assert row["workspace_id"] == ids["workspace_a"]
                    assert row["capability_id"] is None
                    assert row["human_user_id"] == ids["user_a"]
                    assert row["request_identity"] == _key_identity(
                        "dedupe-journal-human"
                    )
                    assert len(row["request_digest"]) == 64
                    assert row["resource_type"] == "media_asset"
                    assert row["resource_id"] == asset_id
                    assert row["disposition"] == "completed"
                    assert row["schema_version"] == "mutation-completion/v1"
                    async with await _owner(database) as owner:
                        family_audit_count = await owner.fetchval(
                            "SELECT count(*) FROM audit.media_mutation "
                            "WHERE operation_id = $1",
                            human_op,
                        )
                        ledger_key = await owner.fetchval(
                            "SELECT idempotency_key FROM control.media_idempotency "
                            "WHERE operation_id = $1",
                            human_op,
                        )
                    assert family_audit_count == 1
                    assert ledger_key == "dedupe-journal-human"

                    human_replay = await media_client.post(
                        upload_url,
                        headers=_headers(session_a, "dedupe-journal-human"),
                        data={
                            "alt_text": "H dedupe alt",
                            "metadata": json.dumps({"origin": "h"}),
                        },
                        files={"file": ("h.png", CANONICAL_PNG, "image/png")},
                    )
                    assert human_replay.status_code == 201, human_replay.text
                    assert human_replay.headers.get("x-media-replay") == "true"
                    _record_original(
                        human_replay.json()["record"], asset_id, content_hash
                    )
                    assert await _journal_count(database, human_op) == 1

                    agent = await agent_client.post(
                        "/api/agent/v1/media/assets",
                        headers={
                            "Authorization": (f"Bearer {ids['capability_token']}"),
                            "Idempotency-Key": "dedupe-journal-agent",
                        },
                        data={
                            "alt_text": "A dedupe alt",
                            "metadata": json.dumps({"origin": "agent"}),
                        },
                        files={"file": ("a.png", CANONICAL_PNG, "image/png")},
                    )
                    assert agent.status_code == 201, agent.text
                    assert agent.json()["action"] == "MEDIA_UPLOADED"
                    _record_original(agent.json()["record"], asset_id, content_hash)
                    agent_op = UUID(agent.json()["operation_id"])

                    row = await _journal_row(database, agent_op)
                    assert row is not None
                    assert row["family"] == "agent"
                    assert row["site_id"] == ids["site_a"]
                    assert row["workspace_id"] == ids["agent_workspace"]
                    assert row["capability_id"] == agent_capability_id
                    assert row["human_user_id"] is None
                    assert row["request_identity"] == _key_identity(
                        "dedupe-journal-agent"
                    )
                    assert len(row["request_digest"]) == 64
                    assert row["resource_type"] == "media_asset"
                    assert row["resource_id"] == asset_id
                    assert row["disposition"] == "completed"
                    assert row["schema_version"] == "mutation-completion/v1"
                    async with await _owner(database) as owner:
                        family_audit_count = await owner.fetchval(
                            "SELECT count(*) FROM audit.agent_mutation "
                            "WHERE operation_id = $1",
                            agent_op,
                        )
                    assert family_audit_count == 1

                    agent_replay = await agent_client.post(
                        "/api/agent/v1/media/assets",
                        headers={
                            "Authorization": (f"Bearer {ids['capability_token']}"),
                            "Idempotency-Key": "dedupe-journal-agent",
                        },
                        data={
                            "alt_text": "A dedupe alt",
                            "metadata": json.dumps({"origin": "agent"}),
                        },
                        files={"file": ("a.png", CANONICAL_PNG, "image/png")},
                    )
                    assert agent_replay.status_code == 201, agent_replay.text
                    _record_original(
                        agent_replay.json()["record"], asset_id, content_hash
                    )
                    assert await _journal_count(database, agent_op) == 1

                    # Honest zero-op dedupe: no foundation work in either
                    # previously empty workspace; canonical row untouched.
                    assert (
                        await _content_operations(database, ids["workspace_a"])
                        == ops_a_before
                    )
                    assert (
                        await _content_operations(database, ids["agent_workspace"])
                        == ops_agent_before
                    )
                    assert await _canonical_row(database, asset_id) == baseline_row
    finally:
        await control.stop()

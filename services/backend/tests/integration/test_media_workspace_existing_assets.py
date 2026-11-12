"""077_001 workspace-isolated media: EXISTING canonical asset regressions.

Author-only A2 companion (round 083-10-a) to
``test_media_workspace_isolation.py`` (fresh pending uploads, already
green) and PRIMARY's A3 human-Editor-on-AGENT case.  These cases cover
the other side of the 077_001 contract: media whose bytes and record
ALREADY exist in the immutable canonical base (``media_asset_base``),
i.e. assets lawfully promoted/published by the reviewer path before the
workspace edit or re-upload happened.

1. ``test_existing_canonical_media_workspace_edit_and_delete``
   (private/public): an editorial metadata PATCH and a reference DELETE
   in human workspace A are workspace-pending COW changes (first-touch
   baseline / tombstone).  A sees the edit and then the tombstone;
   same-site workspace B and the exact canonical base row keep the
   original record and bytes throughout, and the sessionless public
   digest gate retains its prior state (private 404 / public 200 exact
   immutable bytes) before, during, and after the pending changes.
2. ``test_existing_canonical_media_same_hash_dedupe`` (private/public):
   a human or agent upload of bytes that already exist canonically is
   an honest no-op dedupe: the stable canonical record identity is
   returned, supplied upload metadata is NOT silently applied to the
   canonical row or any workspace, no new foundation operation appears
   in the previously empty workspace (public ``get_session_operations``
   probe), same-key replays are stable, and public authorization/bytes
   are unchanged.

Provenance and limits:
- the canonical row and immutable bytes are seeded by an explicit
  trusted OWNER fixture (bootstrap-grade setup data) through the real
  store staging/publish interface plus one owner INSERT; the seed is
  fixture data and is never reviewer-publication proof;
- workspace identity is verified against the authoritative resolver
  predicate (the exact ``control.slaif_human_editor_workspace_resolve``
  selection), not invented client session state; no client-side PG
  session/role selection is faked anywhere;
- ``CANONICAL_PNG`` is a signature-only pseudo PNG: these cases prove
  byte/privacy behavior, not image decoding, dimensions, or public
  NGINX wire behavior;
- this module is AUTHOR-ONLY: the product TEST app locators reject the
  peer endpoint, so PRIMARY must execute all four collected cases on a
  valid owned endpoint (full A8) before acceptance.  Collection and
  linting here are not behavior passes.

Helpers reused byte-exact from the companion modules (no local
re-implementation): ``_seed_agent_fixture`` (upgrade+reconcile; site_a
with SITE_OWNER user_a + SITE_EDITOR user_b, human workspaces A/B and
one AGENT workspace + capability), and the 070-b
``_headers``/``_cookie``/``_control_settings``/``_editor_settings``/
``_media_settings`` plus ``AGENT_SCOPES``/``_agent_settings``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import httpx
import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_state.foundation import get_session_operations
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.media_service.app import create_app as create_media_app
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.store import MediaStore, StagedMedia
from test_media_security_lifecycle import (
    _control_settings,
    _cookie,
    _editor_settings,
    _headers,
    _media_settings,
)
from test_media_service import _agent_settings
from test_media_workspace_isolation import _seed_agent_fixture

CANONICAL_PNG = b"\x89PNG\r\n\x1a\nexisting-canonical-media"
_ORIGINAL_ALT = "Existing canonical alt"
_ORIGINAL_METADATA = {"origin": "canonical"}

_CANONICAL_ROW_SQL = (
    "SELECT alt_text, metadata, public_status::text, published_at, "
    "size_bytes, storage_key, uploaded_by, site_id, content_hash "
    "FROM content.media_asset_base WHERE id = $1"
)
# Read-only mirror of the control.slaif_human_editor_workspace_resolve
# selection predicate (028_001): the authoritative workspace for a
# headerless human editor/media context is the newest ACTIVE,
# non-expired HUMAN workspace the user created on the ACTIVE site.
_RESOLVED_WORKSPACE_SQL = (
    "SELECT count(*) FROM control.workspace AS workspace "
    "JOIN control.site AS site ON site.id = workspace.site_id "
    "JOIN control.user_account AS account "
    "ON account.id = workspace.created_by "
    "WHERE workspace.site_id = $1 "
    "AND workspace.created_by = $2 "
    "AND workspace.actor_type = 'HUMAN' "
    "AND workspace.status = 'ACTIVE' "
    "AND workspace.expires_at > CURRENT_TIMESTAMP "
    "AND site.status = 'ACTIVE' "
    "AND account.status = 'ACTIVE' "
    "AND workspace.id = $3"
)


def _storage_key(content_hash: str) -> str:
    return f"sha256/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}"


def _public_url(content_hash: str) -> str:
    return f"/v1/public/sha256/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}"


async def _seed_canonical_media(
    database: AgentSiteDatabase,
    store: MediaStore,
    *,
    site_id: UUID,
    uploaded_by: UUID,
    asset_id: UUID,
    content_hash: str,
    public_status: str,
) -> str:
    """Explicit trusted OWNER fixture: canonical base row + immutable bytes.

    The bytes go through the real store staging/publish interface (the
    same interface the upload path uses), then one owner INSERT places
    the canonical record.  Fixture data only: this is not a reviewer
    publication and proves nothing about the accept path.
    """
    writer = store.create_staging_writer()
    try:
        writer.stream.write(CANONICAL_PNG)
        writer.stream.close()
        storage_key = store.publish(
            StagedMedia(
                staging_path=writer.path,
                digest=content_hash,
                size_bytes=len(CANONICAL_PNG),
                mime_type="image/png",
                stream=None,
            )
        )
    except BaseException:
        store.discard_staged(
            StagedMedia(
                staging_path=writer.path,
                digest=content_hash,
                size_bytes=len(CANONICAL_PNG),
                mime_type="image/png",
                stream=None,
            )
        )
        raise
    assert storage_key == _storage_key(content_hash)
    assert store.object_path(storage_key).read_bytes() == CANONICAL_PNG
    if public_status == "public":
        # The public digest route serves the separate verified public
        # namespace (open_public_verified); the private publish above
        # does not create it.  Prepare the real public bytes through the
        # existing store method (the same one finalization phase 1 uses).
        # Fixture preparation only: the explicit owner seed that follows
        # still is not reviewer-publication proof.
        public_key = store.publish_public(storage_key, content_hash, len(CANONICAL_PNG))
        assert public_key == f"public/{storage_key}"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.media_asset_base "
            "(id, site_id, uploaded_by, filename, mime_type, size_bytes, "
            "content_hash, storage_key, alt_text, metadata, public_status, "
            "published_at) "
            "VALUES ($1,$2,$3,'canonical.png','image/png',$4,$5,$6,"
            f"'{_ORIGINAL_ALT}',$7::jsonb,$8, "
            "CASE WHEN $9 = 'public' THEN now() ELSE NULL END)",
            asset_id,
            site_id,
            uploaded_by,
            len(CANONICAL_PNG),
            content_hash,
            storage_key,
            json.dumps(_ORIGINAL_METADATA, sort_keys=True),
            public_status,
            public_status,
        )
    return storage_key


async def _canonical_row(database: AgentSiteDatabase, asset_id: UUID) -> dict[str, Any]:
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        row = await owner.fetchrow(_CANONICAL_ROW_SQL, asset_id)
    assert row is not None
    record = {key: row[key] for key in row.keys()}
    # owner_connection is a raw asyncpg connection without a JSON codec,
    # so the jsonb metadata column arrives as its catalog text form;
    # decode it here so the exact-equality oracle compares the fixture
    # representation (test-only, not product behavior).
    raw_metadata = record["metadata"]
    if isinstance(raw_metadata, (bytes, str)):
        record["metadata"] = json.loads(
            raw_metadata.decode("utf-8")
            if isinstance(raw_metadata, bytes)
            else raw_metadata
        )
    return record


def _original_canonical_row(
    asset_id: UUID,
    site_id: UUID,
    uploaded_by: UUID,
    content_hash: str,
    storage_key: str,
    public_status: str,
    published_at: Any,
) -> dict[str, Any]:
    return {
        "alt_text": _ORIGINAL_ALT,
        "metadata": dict(_ORIGINAL_METADATA),
        "public_status": public_status,
        "published_at": published_at,
        "size_bytes": len(CANONICAL_PNG),
        "storage_key": storage_key,
        "uploaded_by": uploaded_by,
        "site_id": site_id,
        "content_hash": content_hash,
    }


async def _assert_authoritative_workspace(
    database: AgentSiteDatabase, site_id: UUID, user_id: UUID, workspace_id: UUID
) -> None:
    """Verify the server-side headerless context resolves to workspace_id.

    Uses the resolver's exact selection predicate as a read-only count:
    the target must be the user's unique ACTIVE non-expired HUMAN
    workspace on the ACTIVE site, so every headerless editor/media call
    in this case runs in that workspace by authoritative resolution.
    """
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        unique = await owner.fetchval(
            _RESOLVED_WORKSPACE_SQL, site_id, user_id, workspace_id
        )
        foreign = await owner.fetchval(
            "SELECT count(*) FROM control.workspace "
            "WHERE site_id = $1 AND created_by = $2 "
            "AND actor_type = 'HUMAN' AND status = 'ACTIVE' "
            "AND expires_at > CURRENT_TIMESTAMP AND id <> $3",
            site_id,
            user_id,
            workspace_id,
        )
    assert int(unique) == 1
    assert int(foreign) == 0


async def _content_operations(database: AgentSiteDatabase, workspace_id: UUID) -> Any:
    """Public foundation session-operation probe (supported SDK surface)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return await get_session_operations(
            AsyncpgExecutor(owner), workspace_id, schema="content"
        )


async def _public_read(
    client: httpx.AsyncClient, content_hash: str, public_status: str
) -> int:
    response = await client.get(_public_url(content_hash))
    expected = 200 if public_status == "public" else 404
    assert response.status_code == expected, (
        f"public digest must stay {expected} while pending, "
        f"observed {response.status_code}"
    )
    if expected == 200:
        assert response.content == CANONICAL_PNG
    return response.status_code


def _record_original(record: dict[str, Any], asset_id: UUID, content_hash: str) -> None:
    assert UUID(record["id"]) == asset_id
    assert record["alt_text"] == _ORIGINAL_ALT
    assert record["metadata"] == _ORIGINAL_METADATA
    assert record["content_hash"] == content_hash
    assert record["storage_key"] == _storage_key(content_hash)
    assert str(record["size_bytes"]) == str(len(CANONICAL_PNG))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "public_status", ["private", "public"], ids=["private", "public"]
)
async def test_existing_canonical_media_workspace_edit_and_delete(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
    public_status: str,
) -> None:
    """Case 1: A's PATCH/DELETE is workspace-pending; B + canonical unchanged."""

    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    store = MediaStore(tmp_path / "media")
    content_hash = hashlib.sha256(CANONICAL_PNG).hexdigest()
    asset_id = uuid4()
    storage_key = await _seed_canonical_media(
        database,
        store,
        site_id=ids["site_a"],
        uploaded_by=ids["user_a"],
        asset_id=asset_id,
        content_hash=content_hash,
        public_status=public_status,
    )
    baseline = await _canonical_row(database, asset_id)
    expected_row = _original_canonical_row(
        asset_id,
        ids["site_a"],
        ids["user_a"],
        content_hash,
        storage_key,
        public_status,
        baseline["published_at"],
    )
    assert baseline == expected_row, baseline
    # Authoritative headerless context for user_a is exactly workspace_a.
    await _assert_authoritative_workspace(
        database, ids["site_a"], ids["user_a"], ids["workspace_a"]
    )

    control = ControlDatabase(_control_settings(database))
    editor = EditorDatabase(_editor_settings(database))
    media_database = MediaDatabase(_media_settings(database, store.root))
    editor_app = create_editor_app(
        settings=ServiceSettings.for_test(), database=control, editor_database=editor
    )
    media_app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_database.settings,
        database=media_database,
        store=store,
    )
    media_url = f"/api/editor/v1/sites/{ids['site_a']}/media/{asset_id}"
    bytes_url = f"/v1/sites/{ids['site_a']}/assets/{asset_id}/content"
    await control.start()
    try:
        async with editor_app.router.lifespan_context(editor_app):
            async with media_app.router.lifespan_context(media_app):
                session_a = await control.human_session_service().create(ids["user_a"])
                session_b = await control.human_session_service().create(ids["user_b"])
                async with (
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=editor_app),
                        base_url="http://existing-media-editor.test",
                    ) as editor_client,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=media_app),
                        base_url="http://existing-media.test",
                    ) as media_client,
                ):
                    # Pre-change: both authorized workspaces see the
                    # original record and the immutable bytes.
                    before_a = await editor_client.get(
                        media_url, headers=_headers(session_a, "existing-before-a")
                    )
                    assert before_a.status_code == 200, before_a.text
                    _record_original(before_a.json(), asset_id, content_hash)
                    before_b = await editor_client.get(
                        media_url, headers=_headers(session_b, "existing-before-b")
                    )
                    assert before_b.status_code == 200, before_b.text
                    _record_original(before_b.json(), asset_id, content_hash)
                    bytes_a = await media_client.get(
                        bytes_url, headers={"cookie": _cookie(session_a)}
                    )
                    assert bytes_a.status_code == 200
                    assert bytes_a.content == CANONICAL_PNG
                    bytes_b = await media_client.get(
                        bytes_url, headers={"cookie": _cookie(session_b)}
                    )
                    assert bytes_b.status_code == 200
                    assert bytes_b.content == CANONICAL_PNG
                    await _public_read(media_client, content_hash, public_status)

                    # Human Editor PATCH in A: a workspace-pending edit.
                    patch = await editor_client.patch(
                        media_url,
                        headers=_headers(session_a, "existing-patch-a"),
                        json={"alt_text": "A pending alt", "metadata": {"origin": "a"}},
                    )
                    assert patch.status_code == 200, patch.text
                    assert patch.json()["alt_text"] == "A pending alt"
                    assert patch.json()["metadata"] == {"origin": "a"}
                    assert patch.json()["content_hash"] == content_hash

                    # A sees the pending edit; B and the canonical row do not.
                    after_a = await editor_client.get(
                        media_url, headers=_headers(session_a, "existing-patched-a")
                    )
                    assert after_a.status_code == 200, after_a.text
                    assert after_a.json()["alt_text"] == "A pending alt"
                    assert after_a.json()["metadata"] == {"origin": "a"}
                    after_b = await editor_client.get(
                        media_url, headers=_headers(session_b, "existing-patched-b")
                    )
                    assert after_b.status_code == 200, after_b.text
                    _record_original(after_b.json(), asset_id, content_hash)
                    bytes_b2 = await media_client.get(
                        bytes_url, headers={"cookie": _cookie(session_b)}
                    )
                    assert bytes_b2.status_code == 200
                    assert bytes_b2.content == CANONICAL_PNG
                    assert (await _canonical_row(database, asset_id)) == expected_row
                    await _public_read(media_client, content_hash, public_status)

                    # Reference DELETE in A: a workspace-pending tombstone.
                    deleted = await editor_client.delete(
                        media_url, headers=_headers(session_a, "existing-delete-a")
                    )
                    assert deleted.status_code == 204, deleted.text
                    after_delete_a = await editor_client.get(
                        media_url, headers=_headers(session_a, "existing-after-a")
                    )
                    assert after_delete_a.status_code == 404
                    bytes_a_after = await media_client.get(
                        bytes_url, headers={"cookie": _cookie(session_a)}
                    )
                    assert bytes_a_after.status_code == 404
                    after_delete_b = await editor_client.get(
                        media_url, headers=_headers(session_b, "existing-after-b")
                    )
                    assert after_delete_b.status_code == 200, after_delete_b.text
                    _record_original(after_delete_b.json(), asset_id, content_hash)
                    bytes_b3 = await media_client.get(
                        bytes_url, headers={"cookie": _cookie(session_b)}
                    )
                    assert bytes_b3.status_code == 200
                    assert bytes_b3.content == CANONICAL_PNG
                    assert (await _canonical_row(database, asset_id)) == expected_row
                    await _public_read(media_client, content_hash, public_status)
    finally:
        await control.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "public_status", ["private", "public"], ids=["private", "public"]
)
async def test_existing_canonical_media_same_hash_dedupe(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
    public_status: str,
) -> None:
    """Case 2: human/agent same-hash re-uploads dedupe to the canonical id."""

    database = agent_site_database
    ids = await _seed_agent_fixture(database)
    store = MediaStore(tmp_path / "media")
    content_hash = hashlib.sha256(CANONICAL_PNG).hexdigest()
    asset_id = uuid4()
    storage_key = await _seed_canonical_media(
        database,
        store,
        site_id=ids["site_a"],
        uploaded_by=ids["user_a"],
        asset_id=asset_id,
        content_hash=content_hash,
        public_status=public_status,
    )
    baseline = await _canonical_row(database, asset_id)
    expected_row = _original_canonical_row(
        asset_id,
        ids["site_a"],
        ids["user_a"],
        content_hash,
        storage_key,
        public_status,
        baseline["published_at"],
    )
    assert baseline == expected_row, baseline
    await _assert_authoritative_workspace(
        database, ids["site_a"], ids["user_a"], ids["workspace_a"]
    )
    # Both re-upload workspaces start with an honest empty operation set.
    ops_a_before = await _content_operations(database, ids["workspace_a"])
    ops_agent_before = await _content_operations(database, ids["agent_workspace"])

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
        database_settings=_agent_settings(database, store.root),
    )
    await control.start()
    try:
        async with media_app.router.lifespan_context(media_app):
            async with agent_app.router.lifespan_context(agent_app):
                session_a = await control.human_session_service().create(ids["user_a"])
                session_b = await control.human_session_service().create(ids["user_b"])
                async with (
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=agent_app),
                        base_url="http://existing-dedupe-agent.test",
                    ) as agent_client,
                    httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=media_app),
                        base_url="http://existing-dedupe.test",
                    ) as media_client,
                ):
                    upload_url = f"/v1/sites/{ids['site_a']}/assets"
                    agent_headers = {
                        "Authorization": f"Bearer {ids['capability_token']}",
                    }

                    # Human upload of the canonical bytes with DIFFERENT
                    # supplied metadata: an honest no-op dedupe.
                    human = await media_client.post(
                        upload_url,
                        headers=_headers(session_a, "existing-dedupe-human"),
                        data={
                            "alt_text": "H dedupe alt",
                            "metadata": json.dumps({"origin": "h"}),
                        },
                        files={"file": ("h.png", CANONICAL_PNG, "image/png")},
                    )
                    assert human.status_code == 201, human.text
                    assert human.headers.get("x-media-replay") == "false"
                    _record_original(human.json()["record"], asset_id, content_hash)

                    # Same-key replay of the identical request.
                    human_replay = await media_client.post(
                        upload_url,
                        headers=_headers(session_a, "existing-dedupe-human"),
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

                    # Agent upload of the same canonical bytes: same
                    # stable identity, supplied metadata not applied.
                    agent = await agent_client.post(
                        "/api/agent/v1/media/assets",
                        headers={
                            **agent_headers,
                            "Idempotency-Key": "existing-dedupe-agent",
                        },
                        data={
                            "alt_text": "A dedupe alt",
                            "metadata": json.dumps({"origin": "agent"}),
                        },
                        files={"file": ("a.png", CANONICAL_PNG, "image/png")},
                    )
                    assert agent.status_code == 201, agent.text
                    _record_original(agent.json()["record"], asset_id, content_hash)
                    agent_replay = await agent_client.post(
                        "/api/agent/v1/media/assets",
                        headers={
                            **agent_headers,
                            "Idempotency-Key": "existing-dedupe-agent",
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

                    # No fabricated foundation work in either previously
                    # empty workspace (honest no-op dedupe).
                    assert (
                        await _content_operations(database, ids["workspace_a"])
                        == ops_a_before
                    )
                    assert (
                        await _content_operations(database, ids["agent_workspace"])
                        == ops_agent_before
                    )

                    # Canonical row untouched; public authorization/bytes
                    # unchanged; positive reads intact for both workspaces.
                    assert (await _canonical_row(database, asset_id)) == expected_row
                    await _public_read(media_client, content_hash, public_status)
                    bytes_a = await media_client.get(
                        f"/v1/sites/{ids['site_a']}/assets/{asset_id}/content",
                        headers={"cookie": _cookie(session_a)},
                    )
                    assert bytes_a.status_code == 200
                    assert bytes_a.content == CANONICAL_PNG
                    bytes_b = await media_client.get(
                        f"/v1/sites/{ids['site_a']}/assets/{asset_id}/content",
                        headers={"cookie": _cookie(session_b)},
                    )
                    assert bytes_b.status_code == 200
                    assert bytes_b.content == CANONICAL_PNG
    finally:
        await control.stop()

"""Real PostgreSQL and local-filesystem proof for the private Media service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import (
    AgentDatabaseMode,
    AgentDatabaseSettings,
)
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.browser_contracts import (
    BrowserEvidence,
    BrowserTarget,
    normalize_preview_route,
    preview_run_request_digest,
)
from slaif_agent_site.browser_preview_credentials import (
    BrowserPreviewCredentialSigner,
    BrowserSigningKey,
)
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.identity.sessions import format_session_token
from slaif_agent_site.media_service.app import create_app
from slaif_agent_site.media_service.config import MediaDatabaseMode, MediaSettings
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.media_http import get_asset_content
from slaif_agent_site.media_service.store import MediaStore, StagedMedia
from slaif_agent_site.render_api.app import create_app as create_render_app
from slaif_agent_site.review_worker.discard_job import run_discard_job
from slaif_agent_site.review_worker.freeze_job import run_freeze_job
from slaif_agent_site.sites import CreateSiteRequest, SiteService
from starlette.requests import Request
from test_freeze_review_snapshot import (
    _CURRENT_VERSION_FACTS,
    _ConnExecutor,
    _control_call,
    _freeze,
    _snapshot_row,
    _walk_nodes,
    _worker_call,
    _worker_pool,
    _worker_settings,
)
from test_render_projection_integration import _RestartableRenderAdapter

PNG = b"\x89PNG\r\n\x1a\nmedia-fixture"
CANONICAL_PNG = b"\x89PNG\r\n\x1a\ncanonical-fixture"


def _locator(database: AgentSiteDatabase, role: str) -> str:
    login, password = database.credentials[role]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return (
        f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
        f"{host}:{database.connection_parameters['port']}/{database.name}"
    )


def _control_settings(database: AgentSiteDatabase) -> ControlDatabaseSettings:
    login, _password = database.credentials["slaif_control"]
    return ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(_locator(database, "slaif_control")),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="media-control-fixture",
    )


def _media_settings(database: AgentSiteDatabase, root: Path) -> MediaSettings:
    login, _password = database.credentials["slaif_media"]
    return MediaSettings(
        mode=MediaDatabaseMode.TEST,
        dsn=SecretStr(_locator(database, "slaif_media")),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        media_root=root,
        pool_min_size=1,
        pool_max_size=2,
        application_name="media-fixture",
    )


def _cookie(session: str, csrf: str) -> str:
    return f"slaif_session={session}; slaif_csrf={csrf}"


@pytest.mark.asyncio
async def test_media_upload_store_read_dedupe_and_canonical_fallback(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    user_id = uuid4()
    site_id = uuid4()
    canonical_id = uuid4()
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO control.user_account "
            "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
            "VALUES ($1, 'OIDC', 'https://media.test', $2, 'Media Human')",
            user_id,
            str(user_id),
        )
        await owner.execute(
            "INSERT INTO control.site "
            "(id, site_key, display_name, default_locale, component_catalog_version) "
            "VALUES ($1, 'media-site', 'Media Site', 'en', 'catalog-v1')",
            site_id,
        )
        await owner.execute(
            "INSERT INTO control.site_membership "
            "(site_id, user_account_id, role_key, delegation_ceiling) "
            "VALUES ($1, $2, 'SITE_EDITOR', 2)",
            site_id,
            user_id,
        )
        workspace_id = await owner.fetchval(
            "INSERT INTO control.workspace "
            "(site_id, created_by, actor_type, title, delegation_preset, "
            "effective_scopes, status, expires_at) "
            "VALUES ($1, $2, 'HUMAN', 'Media workspace', 'L2_SITE_EDITOR', "
            "'[]'::jsonb, 'ACTIVE', now() + interval '1 hour') RETURNING id",
            site_id,
            user_id,
        )

    store = MediaStore(tmp_path / "media")
    canonical_staging = store.create_staging_path()
    canonical_staging.write_bytes(CANONICAL_PNG)
    canonical_key = store.publish(
        StagedMedia(
            canonical_staging,
            "".join(f"{byte:02x}" for byte in hashlib.sha256(CANONICAL_PNG).digest()),
            len(CANONICAL_PNG),
            "image/png",
        )
    )
    canonical_digest = canonical_key.rsplit("/", 1)[-1]
    upload_digest = hashlib.sha256(PNG).hexdigest()
    upload_key = f"sha256/{upload_digest[:2]}/{upload_digest[2:4]}/{upload_digest}"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.media_asset_base "
            "(id, site_id, uploaded_by, filename, mime_type, size_bytes, "
            "content_hash, storage_key, alt_text, metadata) "
            "VALUES ($1, $2, $3, 'canonical.png', 'image/png', $4, $5, $6, "
            "'Canonical', '{\"source\":\"canonical\"}'::jsonb)",
            canonical_id,
            site_id,
            user_id,
            len(CANONICAL_PNG),
            canonical_digest,
            canonical_key,
        )

    control = ControlDatabase(_control_settings(database))
    media_settings = _media_settings(database, tmp_path / "media")
    media_database = MediaDatabase(media_settings)
    app = create_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_settings,
        database=media_database,
        store=store,
    )
    await control.start()
    try:
        async with app.router.lifespan_context(app):
            async with media_database.cow_pool().acquire() as media_connection:
                identity = await media_connection.fetchrow(
                    "SELECT current_database()::text, session_user::text, "
                    "current_user::text, ARRAY(SELECT target.rolname::text "
                    "FROM pg_catalog.pg_roles target "
                    "WHERE target.rolname = ANY($1::text[]) "
                    "AND pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
                    "ORDER BY target.rolname)",
                    [
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
                    ],
                )
                assert tuple(identity) == (
                    database.name,
                    database.credentials["slaif_media"][0],
                    database.credentials["slaif_media"][0],
                    ["slaif_media"],
                )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await media_connection.fetch("SELECT * FROM control.workspace")
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await media_connection.fetch(
                        "SELECT * FROM content.media_asset_base"
                    )
                with pytest.raises(asyncpg.PostgresError):
                    await media_connection.fetch(
                        "SELECT * FROM content.slaif_media_asset_get("
                        "$1,$2,$3,$4,$5,$6)",
                        site_id,
                        canonical_id,
                        user_id,
                        uuid4(),
                        "media:read",
                        workspace_id,
                    )
            async with asyncpg_cow_session(
                media_database.cow_pool(), session_id=workspace_id, operation_id=uuid4()
            ) as media_cow:
                with pytest.raises(asyncpg.PostgresError):
                    await media_cow.native.fetch(
                        "SELECT * FROM content.slaif_media_asset_get("
                        "$1,$2,$3,$4,$5,$6)",
                        uuid4(),
                        canonical_id,
                        user_id,
                        uuid4(),
                        "media:read",
                        workspace_id,
                    )
                await media_cow.rollback()
            issued = await control.human_session_service().create(user_id)
            session = issued.token.get_secret_value()
            csrf = issued.csrf_token.get_secret_value()
            headers = {
                "cookie": _cookie(session, csrf),
                "x-csrf-token": csrf,
                "Idempotency-Key": "media-upload-1",
            }
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://media.test"
            ) as client:
                uploaded = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers=headers,
                    data={
                        "alt_text": "Uploaded image",
                        "metadata": json.dumps({"caption": "hello"}),
                    },
                    files={"file": ("uploaded.png", PNG, "image/png")},
                )
                assert uploaded.status_code == 201, uploaded.text
                record = uploaded.json()["record"]
                media_id = UUID(record["id"])
                assert record["site_id"] == str(site_id)
                assert record["uploaded_by"] == str(user_id)
                assert record["filename"] == "uploaded.png"
                assert record["mime_type"] == "image/png"
                assert record["size_bytes"] == len(PNG)
                assert record["content_hash"] == upload_digest
                assert record["storage_key"] == upload_key
                assert record["metadata"] == {"caption": "hello"}
                assert store.object_path(upload_key).is_file()
                assert store.object_path(upload_key).stat().st_mode & 0o777 == 0o600

                read_headers = {"cookie": _cookie(session, csrf)}
                canonical_content = await client.get(
                    f"/v1/sites/{site_id}/assets/{canonical_id}/content",
                    headers=read_headers,
                )
                assert canonical_content.status_code == 200
                assert canonical_content.content == CANONICAL_PNG
                content = await client.get(
                    f"/v1/sites/{site_id}/assets/{media_id}/content",
                    headers=read_headers,
                )
                assert content.status_code == 200
                assert content.content == PNG
                assert content.headers["content-type"] == "image/png"
                assert content.headers["content-length"] == str(len(PNG))
                assert content.headers["etag"] == f'"{upload_digest}"'
                assert content.headers["x-content-type-options"] == "nosniff"
                assert content.headers["cache-control"] == "private, no-store"

                closed: list[int] = []
                original_close = os.close

                def record_close(descriptor: int) -> None:
                    closed.append(descriptor)
                    original_close(descriptor)

                async def disconnected() -> dict[str, object]:
                    return {"type": "http.disconnect"}

                streaming_request = Request(
                    {
                        "type": "http",
                        "method": "GET",
                        "path": f"/v1/sites/{site_id}/assets/{media_id}/content",
                        "headers": [
                            (b"cookie", _cookie(session, csrf).encode()),
                        ],
                        "app": app,
                    },
                    disconnected,
                )
                with patch(
                    "slaif_agent_site.media_service.media_http.os.close",
                    side_effect=record_close,
                ):
                    stream_response = await get_asset_content(
                        site_id, media_id, streaming_request
                    )
                    iterator = cast(
                        AsyncGenerator[bytes, None], stream_response.body_iterator
                    )
                    assert await anext(iterator) == PNG
                    await iterator.aclose()
                assert closed

                same_key_replay = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers=headers,
                    data={
                        "alt_text": "Uploaded image",
                        "metadata": '{"caption":"hello"}',
                    },
                    files={"file": ("uploaded.png", PNG, "image/png")},
                )
                assert same_key_replay.status_code == 201
                assert same_key_replay.json() == uploaded.json()
                assert same_key_replay.headers["x-media-replay"] == "true"

                replay = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers={**headers, "Idempotency-Key": "media-upload-replay"},
                    data={
                        "alt_text": "Uploaded image",
                        "metadata": '{"caption":"hello"}',
                    },
                    files={"file": ("uploaded.png", PNG, "image/png")},
                )
                assert replay.status_code == 201
                assert replay.json()["record"]["id"] == str(media_id)

                concurrent = await asyncio.gather(
                    *(
                        client.post(
                            f"/v1/sites/{site_id}/assets",
                            headers={
                                **headers,
                                "Idempotency-Key": f"media-concurrent-{index}",
                            },
                            data={
                                "alt_text": f"Concurrent {index}",
                                "metadata": json.dumps({"index": index}),
                            },
                            files={"file": ("concurrent.png", PNG, "image/png")},
                        )
                        for index in range(2)
                    )
                )
                assert [response.status_code for response in concurrent] == [201, 201]
                assert {response.json()["record"]["id"] for response in concurrent} == {
                    str(media_id)
                }
                assert {
                    response.json()["record"]["storage_key"] for response in concurrent
                } == {upload_key}

                mismatch = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers=headers,
                    data={"alt_text": "different", "metadata": "{}"},
                    files={"file": ("uploaded.png", PNG + b"different", "image/png")},
                )
                assert mismatch.status_code == 409
                assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_MISMATCH"

                missing_key = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers={"cookie": _cookie(session, csrf), "x-csrf-token": csrf},
                    files={"file": ("uploaded.png", PNG, "image/png")},
                )
                assert missing_key.status_code == 400
                assert missing_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"

                spoofed = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers={**headers, "Idempotency-Key": "media-spoofed"},
                    files={"file": ("spoofed.jpg", PNG, "image/jpeg")},
                )
                assert spoofed.status_code == 422
                svg = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers={**headers, "Idempotency-Key": "media-svg"},
                    files={"file": ("image.svg", b"<svg></svg>", "image/svg+xml")},
                )
                assert svg.status_code == 422
                traversal = await client.post(
                    f"/v1/sites/{site_id}/assets",
                    headers={**headers, "Idempotency-Key": "media-traversal"},
                    files={"file": ("../escape.png", PNG, "image/png")},
                )
                assert traversal.status_code == 422
                assert list(store.staging_root.iterdir()) == []

                foreign = await client.get(
                    f"/v1/sites/{uuid4()}/assets/{media_id}/content",
                    headers=read_headers,
                )
                assert foreign.status_code in {403, 404}
                assert str(media_id) not in foreign.text

                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    # Site-scoped base-write media record (068 media
                    # publication core): the upload lands in
                    # media_asset_base directly — media is
                    # content-addressed and immutable, so the COW overlay
                    # stays empty and the record is visible to every
                    # authorized session of the site.
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM content.media_asset_base "
                            "WHERE id = $1",
                            media_id,
                        )
                        == 1
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM content.media_asset_base "
                            "WHERE id = $1",
                            canonical_id,
                        )
                        == 1
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM control.media_idempotency "
                            "WHERE workspace_id = $1",
                            workspace_id,
                        )
                        == 4
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM audit.media_mutation "
                            "WHERE workspace_id = $1",
                            workspace_id,
                        )
                        == 4
                    )
    finally:
        await media_database.stop()
        await control.stop()


# ---------------------------------------------------------------------------
# 083/5 R2: Agent private IMAGE + DOCUMENT bytes — actual human active
# preview, actual confined bound worker, frozen review after discard.
# ---------------------------------------------------------------------------

PNG_BYTES = b"\x89PNG\r\n\x1a\nprivate-media-fixture-image"
PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]>> endobj\n"
    b"trailer <</Root 1 0 R>>\n"
    b"%%EOF\n"
)
SIGNER = BrowserPreviewCredentialSigner(
    BrowserSigningKey("0123456789abcdef", bytes(range(32)))
)
NONCE_A = "00112233445566778899aabbccddeeff"
NONCE_B = "aabbccddeeff00112233445566778899"
NONCE_C = "ffeeddccbbaa99887766554433221100"
AGENT_SCOPES = (
    "preview:inspect",
    "media:upload",
    "media:read",
    "page:create",
    "page:read",
    "composition:read",
    "component-structure:create",
)
EVIDENCE = (BrowserEvidence.SCREENSHOT, BrowserEvidence.HEADING_SUMMARY)
BEGIN_RUN_SQL = (
    "SELECT * FROM control.slaif_agent_browser_run_begin"
    "($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)"
)
CLAIM_RUN_SQL = "SELECT * FROM control.slaif_agent_browser_run_claim($1,$2)"
COMPLETE_RUN_SQL = "SELECT control.slaif_agent_browser_run_complete($1,$2,$3,$4,$5,$6)"


def _agent_settings(
    database: AgentSiteDatabase, media_root: Path
) -> AgentDatabaseSettings:
    login, password = database.credentials["slaif_agent_runtime"]
    host = quote(str(database.connection_parameters["host"]), safe="[]:.")
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(
            f"postgresql://{quote(login, safe='')}:{quote(password, safe='')}@"
            f"{host}:{database.connection_parameters['port']}/{database.name}"
        ),
        dsn_file=None,
        media_root=media_root,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=2,
        application_name="media-bytes-agent-fixture",
    )


async def _insert_session(
    owner: Any, user_id: UUID, *, revoked: bool = False, expired: bool = False
) -> tuple[UUID, str, bytes]:
    """One coherent 010 session row; isolated guard fixtures for negatives."""

    session_id = uuid4()
    public_id = f"sas2_{session_id.hex}"
    secret = uuid4().bytes + uuid4().bytes
    digest = hashlib.sha256(secret).digest()
    if expired:
        # Not idle and recently authenticated; only the absolute expiry
        # has lapsed, so the expiry disjunct fires in isolation.
        await owner.execute(
            "INSERT INTO control.user_session "
            "(id, public_id, secret_digest, csrf_secret_digest, user_account_id,"
            " created_at, last_seen_at, recent_auth_at, absolute_expires_at)"
            " VALUES ($1,$2,$3,$4,$5, now() - interval '20 minutes',"
            "  now() - interval '20 minutes', now() - interval '20 minutes',"
            "  now() - interval '5 minutes')",
            session_id,
            public_id,
            digest,
            hashlib.sha256(f"media-bytes-expired-{session_id.hex}".encode()).digest(),
            user_id,
        )
    elif revoked:
        # Fresh and unexpired; only the revocation disjunct fires.
        await owner.execute(
            "INSERT INTO control.user_session "
            "(id, public_id, secret_digest, csrf_secret_digest, user_account_id,"
            " created_at, last_seen_at, recent_auth_at, absolute_expires_at,"
            " revoked_at)"
            " VALUES ($1,$2,$3,$4,$5, now() - interval '5 minutes',"
            "  now() - interval '5 minutes', now() - interval '5 minutes',"
            "  now() + interval '1 hour', now() - interval '1 minute')",
            session_id,
            public_id,
            digest,
            hashlib.sha256(f"media-bytes-revoked-{session_id.hex}".encode()).digest(),
            user_id,
        )
    else:
        await owner.execute(
            "INSERT INTO control.user_session "
            "(id, public_id, secret_digest, csrf_secret_digest, user_account_id,"
            " created_at, last_seen_at, recent_auth_at, absolute_expires_at)"
            " VALUES ($1,$2,$3,$4,$5, now() - interval '5 minutes',"
            "  now() - interval '5 minutes', now() - interval '5 minutes',"
            "  now() + interval '1 hour')",
            session_id,
            public_id,
            digest,
            hashlib.sha256(f"media-bytes-csrf-{session_id.hex}".encode()).digest(),
            user_id,
        )
    return session_id, public_id, secret


async def _begin_browser_run(
    agent: Any,
    *,
    capability_id: UUID,
    site_id: UUID,
    workspace_id: UUID,
    delegator_id: UUID,
    key: str,
    route: str,
) -> UUID:
    request = {
        "version": "browser-preview/v1",
        "route": route,
        "target": "desktop-chromium",
        "evidence": [item.value for item in EVIDENCE],
    }
    run_id, operation_id = uuid4(), uuid4()
    row = await agent.fetchrow(
        BEGIN_RUN_SQL,
        capability_id,
        site_id,
        workspace_id,
        delegator_id,
        key,
        preview_run_request_digest(request),
        operation_id,
        run_id,
        "browser-preview/v1",
        route,
        hashlib.sha256(route.encode()).hexdigest(),
        "desktop-chromium",
        [item.value for item in EVIDENCE],
        1,
        5_505_024,
        1,
        120,
    )
    assert row is not None and row["result"] == "STARTED"
    return run_id


def _issue_token(
    *,
    capability_id: UUID,
    site_id: UUID,
    workspace_id: UUID,
    run_id: UUID,
    route: str,
    nonce: str,
    now: int,
    ttl_seconds: int = 30,
) -> str:
    return SIGNER.issue(
        capability_id=capability_id,
        site_id=site_id,
        workspace_id=workspace_id,
        run_id=run_id,
        route=route,
        target=BrowserTarget.DESKTOP_CHROMIUM,
        evidence=EVIDENCE,
        artifact_bytes_limit=5_505_024,
        duration_seconds=120,
        now=now,
        ttl_seconds=ttl_seconds,
        nonce=nonce,
    )


async def _claim_run(agent: Any, expected_run_id: UUID) -> tuple[UUID, int]:
    lease = uuid4()
    claimed = await agent.fetchrow(CLAIM_RUN_SQL, lease, 60)
    assert claimed is not None
    assert claimed["run_id"] == expected_run_id
    assert claimed["lease_id"] == lease
    return claimed["lease_id"], int(claimed["attempt"])


async def _complete_run(agent: Any, run_id: UUID, lease_id: UUID) -> None:
    assert (
        await agent.fetchval(
            COMPLETE_RUN_SQL,
            run_id,
            lease_id,
            "COMPLETED",
            json.dumps({"ok": True}),
            None,
            None,
        )
        == "COMPLETED"
    )


async def _release_run(agent: Any, run_id: UUID, lease_id: UUID) -> None:
    assert await agent.fetchval(
        "SELECT control.slaif_agent_browser_run_release($1,$2)",
        run_id,
        lease_id,
    ) in {"QUEUED", "FAILED"}


@pytest.mark.asyncio
async def test_private_media_bytes_human_preview_bound_worker_frozen_review(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    """R2 actual private bytes: Agent IMAGE + DOCUMENT, three real readers.

    The Agent uploads one PNG and one PDF through the real Agent HTTP API
    (media:upload; site-scoped immutable base rows, not public).  The
    exact bytes must be readable BEFORE freeze by (a) the authorized
    human active preview (full 054 chain, no session touch) and (b) the
    actual confined bound worker (real 036 consume and 076 binding
    registrar in ONE Render transaction; the media service only ever
    hashes the presented token).  The public digest route and the
    canonical render refuse private content.  The real freeze captures
    both assets in the immutable v2 snapshot typed media closure; after
    the real terminal discard and pending cleanup, the frozen review
    read returns the same bytes.  Credential-shape failures are 401;
    every authorization/reference denial is one uniform 404; the read
    surfaces touch nothing.
    """
    database = agent_site_database
    await upgrade(database.settings)
    await reconcile(database.settings)
    control_pool = await database.role_pool("slaif_control")
    agent_pool = await database.role_pool("slaif_agent_runtime")
    owner_dsn = database.settings.resolved_owner_dsn()
    site = await SiteService(control_pool).create(
        CreateSiteRequest(
            site_key=f"media-bytes-{uuid4().hex[:10]}",
            display_name="Media Bytes",
            default_locale="en-US",
        )
    )
    site_id = site.site_id
    route = f"/s/{site.site_key}/"
    user_id, user2_id, user3_id = uuid4(), uuid4(), uuid4()
    workspace_id, workspace2_id, workspace3_id = uuid4(), uuid4(), uuid4()
    capability_id = uuid4()
    capability_token, capability_public, capability_digest = generate_capability_token()
    expires = datetime.now(UTC) + timedelta(minutes=30)
    session_public: str
    session_secret: bytes
    session2_public: str
    session2_secret: bytes
    session3_public: str
    session3_secret: bytes
    revoked_public: str
    revoked_secret: bytes
    expired_public: str
    expired_secret: bytes
    before_last_seen: Any
    async with owner_connection(owner_dsn, expected_database=database.name) as owner:
        for account, username in (
            (user_id, "Media.Bytes.Owner"),
            (user2_id, "Media.Bytes.Editor"),
            (user3_id, "Media.Bytes.Stranger"),
        ):
            await owner.execute(
                "INSERT INTO control.user_account "
                "(id, identity_kind, oidc_issuer, oidc_subject, display_name)"
                " VALUES ($1,'OIDC','https://media-bytes.test',$2,$3)",
                account,
                f"subject-{account}",
                username,
            )
        await owner.execute(
            "INSERT INTO control.site_membership "
            "(site_id, user_account_id, role_key, delegation_ceiling)"
            " VALUES ($1,$2,'SITE_OWNER',4), ($1,$3,'SITE_EDITOR',2)",
            site_id,
            user_id,
            user2_id,
        )
        await owner.execute(
            "INSERT INTO content.site_locale_base "
            "(site_id, tag, enabled, is_default, position)"
            " VALUES ($1,'en-US',true,true,0)",
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.theme_base "
            "(id, site_id, schema_version, renderer_version, palette,"
            " typography, layout, shape) VALUES"
            " (gen_random_uuid(), $1, 'theme-schema/v1', 'renderer-v1',"
            ' \'{"preset":"ocean"}\'::jsonb,'
            ' \'{"family":"system","scale":"balanced","weight":"regular"}\'::jsonb,'
            ' \'{"content_width":"md","spacing":"md","grid_gap":"md"}\'::jsonb,'
            ' \'{"radius":"md","shadow":"sm"}\'::jsonb)',
            site_id,
        )
        await owner.execute(
            "INSERT INTO control.workspace "
            "(id, site_id, created_by, delegator_id, actor_type, title,"
            " delegation_preset, effective_scopes, version_facts, status,"
            " expires_at) VALUES ($1,$2,$3,$3,'AGENT',"
            " 'Media bytes agent workspace','L4',$4::jsonb,"
            + _CURRENT_VERSION_FACTS
            + ", 'ACTIVE', now() + interval '2 hours')",
            workspace_id,
            site_id,
            user_id,
            json.dumps(list(AGENT_SCOPES)),
        )
        for other_id, other_user, preset in (
            (workspace2_id, user2_id, "L2"),
            (workspace3_id, user3_id, "L1"),
        ):
            await owner.execute(
                "INSERT INTO control.workspace "
                "(id, site_id, created_by, delegator_id, actor_type, title,"
                " delegation_preset, effective_scopes, version_facts, status,"
                " expires_at) VALUES ($1,$2,$3,$3,'HUMAN',"
                " 'Media bytes control workspace', $4,"
                " '[\"preview:inspect\"]'::jsonb,"
                + _CURRENT_VERSION_FACTS
                + ", 'ACTIVE', now() + interval '2 hours')",
                other_id,
                site_id,
                other_user,
                preset,
            )
        await owner.execute(
            "INSERT INTO control.capability "
            "(id, workspace_id, public_id, secret_digest, scopes,"
            " request_quota, mutation_quota, delete_quota, upload_quota,"
            " expires_at, browser_max_concurrent_runs, browser_max_artifact_bytes)"
            " VALUES ($1,$2,$3,$4,$5::jsonb,1000,500,100,50,$6,10,104857600)",
            capability_id,
            workspace_id,
            capability_public,
            capability_digest,
            json.dumps(list(AGENT_SCOPES)),
            expires,
        )
        _, session_public, session_secret = await _insert_session(owner, user_id)
        _, session2_public, session2_secret = await _insert_session(owner, user2_id)
        _, session3_public, session3_secret = await _insert_session(owner, user3_id)
        _, revoked_public, revoked_secret = await _insert_session(
            owner, user_id, revoked=True
        )
        _, expired_public, expired_secret = await _insert_session(
            owner, user_id, expired=True
        )
        before_last_seen = await owner.fetchval(
            "SELECT array_agg(last_seen_at ORDER BY id::text) FROM "
            "control.user_session WHERE user_account_id = ANY($1::uuid[])",
            [user_id, user2_id, user3_id],
        )
    media_settings = _media_settings(database, tmp_path / "media")
    media_database = MediaDatabase(media_settings)
    store = MediaStore(tmp_path / "media")
    media_app = create_app(
        settings=ServiceSettings.for_test(),
        media_settings=media_settings,
        database=media_database,
        store=store,
    )
    agent_app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(database, tmp_path / "media"),
    )
    render_adapter = _RestartableRenderAdapter(database)
    await render_adapter.start()
    render_app = create_render_app(
        settings=ServiceSettings.for_test(),
        database=render_adapter,
        browser_verifier=SIGNER,
    )
    png_hash = hashlib.sha256(PNG_BYTES).hexdigest()
    pdf_hash = hashlib.sha256(PDF_BYTES).hexdigest()

    def session_cookie(public_id: str, secret: bytes) -> dict[str, str]:
        return {
            "cookie": f"slaif_session="
            f"{format_session_token(public_id, secret).get_secret_value()}"
        }

    png_id: UUID
    pdf_id: UUID
    page_id: UUID
    run_a: UUID
    run_b: UUID
    run_c: UUID
    token_a: str
    now_a: int
    token_c: str
    snapshot_id: UUID
    review_body: dict[str, Any]
    try:
        # -- Phase 1: the Agent produces the private IMAGE + DOCUMENT. --
        async with agent_app.router.lifespan_context(agent_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=agent_app),
                base_url="http://agent.test",
            ) as agent_client:
                agent_headers = {"Authorization": f"Bearer {capability_token}"}
                uploaded_png = await agent_client.post(
                    "/api/agent/v1/media/assets",
                    headers={
                        **agent_headers,
                        "Idempotency-Key": "media-bytes-png",
                    },
                    data={"alt_text": "Private photo", "metadata": "{}"},
                    files={"file": ("photo.png", PNG_BYTES, "image/png")},
                )
                assert uploaded_png.status_code == 201, uploaded_png.text
                png_record = uploaded_png.json()["record"]
                png_id = UUID(png_record["id"])
                assert png_record["content_hash"] == png_hash
                assert png_record["mime_type"] == "image/png"
                assert png_record["size_bytes"] == len(PNG_BYTES)
                uploaded_pdf = await agent_client.post(
                    "/api/agent/v1/media/assets",
                    headers={
                        **agent_headers,
                        "Idempotency-Key": "media-bytes-pdf",
                    },
                    data={"alt_text": "Private document", "metadata": "{}"},
                    files={"file": ("document.pdf", PDF_BYTES, "application/pdf")},
                )
                assert uploaded_pdf.status_code == 201, uploaded_pdf.text
                pdf_record = uploaded_pdf.json()["record"]
                pdf_id = UUID(pdf_record["id"])
                assert pdf_record["content_hash"] == pdf_hash
                assert pdf_record["mime_type"] == "application/pdf"
                assert pdf_record["size_bytes"] == len(PDF_BYTES)
                created_page = await agent_client.post(
                    "/api/agent/v1/pages",
                    headers={
                        **agent_headers,
                        "Idempotency-Key": "media-bytes-page",
                    },
                    json={"slug": "home", "title": "Private home", "locale": "en-US"},
                )
                assert created_page.status_code == 201, created_page.text
                page_id = UUID(created_page.json()["record"]["id"])
                added_image = await agent_client.post(
                    f"/api/agent/v1/pages/{page_id}/components",
                    headers={
                        **agent_headers,
                        "Idempotency-Key": "media-bytes-image",
                    },
                    json={
                        "component_type": "Image",
                        "props": {"mediaId": str(png_id), "alt": "Private photo"},
                    },
                )
                assert added_image.status_code == 201, added_image.text
                added_documents = await agent_client.post(
                    f"/api/agent/v1/pages/{page_id}/components",
                    headers={
                        **agent_headers,
                        "Idempotency-Key": "media-bytes-docs",
                    },
                    json={
                        "component_type": "DocumentList",
                        "props": {
                            "title": "Private documents",
                            "items": [
                                {
                                    "mediaId": str(pdf_id),
                                    "label": "Private document",
                                }
                            ],
                        },
                    },
                )
                assert added_documents.status_code == 201, added_documents.text
                # The Agent reads back its own uploaded bytes pre-freeze.
                for media_id, expected in ((png_id, PNG_BYTES), (pdf_id, PDF_BYTES)):
                    read_back = await agent_client.get(
                        f"/api/agent/v1/media/assets/{media_id}/content",
                        headers=agent_headers,
                    )
                    assert read_back.status_code == 200, read_back.text
                    assert read_back.content == expected
        async with (
            media_app.router.lifespan_context(media_app),
            render_app.router.lifespan_context(render_app),
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=media_app),
                base_url="http://media.test",
            ) as media_client:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=render_app),
                    base_url="http://render.test",
                ) as render_client:
                    # -- Phase 2: public surfaces refuse private content. --
                    public_key = f"sha256/{png_hash[:2]}/{png_hash[2:4]}/{png_hash}"
                    public = await media_client.get(f"/v1/public/{public_key}")
                    assert public.status_code == 404
                    canonical = await render_client.post(
                        "/internal/render/v1/page",
                        json={"authority": "localhost", "path": route},
                    )
                    assert canonical.status_code == 404, canonical.text
                    # -- Phase 3: human active preview, exact bytes. --
                    preview_url = (
                        f"/v1/sites/{site_id}/workspaces/{workspace_id}/preview/assets"
                    )
                    preview = None
                    for media_id, expected in (
                        (png_id, PNG_BYTES),
                        (pdf_id, PDF_BYTES),
                    ):
                        preview = await media_client.get(
                            f"{preview_url}/{media_id}/content",
                            headers=session_cookie(session_public, session_secret),
                        )
                        assert preview.status_code == 200, preview.text
                        assert preview.content == expected
                    assert preview is not None
                    assert preview.headers["cache-control"] == "private, no-store"
                    assert (
                        preview.headers["x-robots-tag"]
                        == "noindex, nofollow, noarchive"
                    )
                    # Positive control: the other creator previews their
                    # own workspace (base rows are site-scoped).
                    control_read = await media_client.get(
                        f"/v1/sites/{site_id}/workspaces/{workspace2_id}"
                        f"/preview/assets/{png_id}/content",
                        headers=session_cookie(session2_public, session2_secret),
                    )
                    assert control_read.status_code == 200, control_read.text
                    assert control_read.content == PNG_BYTES
                    # Human preview negative matrix.
                    no_cookie = await media_client.get(
                        f"{preview_url}/{png_id}/content"
                    )
                    assert no_cookie.status_code == 401
                    malformed = await media_client.get(
                        f"{preview_url}/{png_id}/content",
                        headers={"cookie": "slaif_session=not-a-session-token"},
                    )
                    assert malformed.status_code == 401
                    unknown_secret = uuid4().bytes + uuid4().bytes
                    unknown = await media_client.get(
                        f"{preview_url}/{png_id}/content",
                        headers=session_cookie(f"sas2_{uuid4().hex}", unknown_secret),
                    )
                    assert unknown.status_code == 404
                    revoked = await media_client.get(
                        f"{preview_url}/{png_id}/content",
                        headers=session_cookie(revoked_public, revoked_secret),
                    )
                    assert revoked.status_code == 404
                    expired = await media_client.get(
                        f"{preview_url}/{png_id}/content",
                        headers=session_cookie(expired_public, expired_secret),
                    )
                    assert expired.status_code == 404
                    foreign_workspace = await media_client.get(
                        f"{preview_url}/{png_id}/content",
                        headers=session_cookie(session2_public, session2_secret),
                    )
                    assert foreign_workspace.status_code == 404
                    no_permission = await media_client.get(
                        f"/v1/sites/{site_id}/workspaces/{workspace3_id}"
                        f"/preview/assets/{png_id}/content",
                        headers=session_cookie(session3_public, session3_secret),
                    )
                    assert no_permission.status_code == 404
                    foreign_media = await media_client.get(
                        f"{preview_url}/{uuid4()}/content",
                        headers=session_cookie(session_public, session_secret),
                    )
                    assert foreign_media.status_code == 404
                    # -- Phase 4: the confined bound worker, exact bytes. --
                    # The real dispatcher leases the run (QUEUED ->
                    # RUNNING, attempt 1) before the worker renders: the
                    # 076 registrar records run.attempt_count, which the
                    # binding shape check requires to be at least one.
                    # The run row carries the model-normalized route, so
                    # the token and the render browser_route carry that
                    # exact normalized route; the page-resolution path
                    # keeps the full requested route.
                    bound_route = normalize_preview_route(route)
                    async with agent_pool.acquire() as agent:
                        run_a = await _begin_browser_run(
                            agent,
                            capability_id=capability_id,
                            site_id=site_id,
                            workspace_id=workspace_id,
                            delegator_id=user_id,
                            key="media-bytes-run-a",
                            route=bound_route,
                        )
                        lease_a, attempt_a = await _claim_run(agent, run_a)
                        assert attempt_a == 1
                        run_b = await _begin_browser_run(
                            agent,
                            capability_id=capability_id,
                            site_id=site_id,
                            workspace_id=workspace_id,
                            delegator_id=user_id,
                            key="media-bytes-run-b",
                            route=bound_route,
                        )
                    now_a = int(time.time())
                    token_a = _issue_token(
                        capability_id=capability_id,
                        site_id=site_id,
                        workspace_id=workspace_id,
                        run_id=run_a,
                        route=bound_route,
                        nonce=NONCE_A,
                        now=now_a,
                    )
                    bound_prefix = "/v1/browser-preview/assets"
                    render_body = {
                        "authority": "localhost",
                        "path": route,
                        "workspace_id": str(workspace_id),
                        "browser_route": bound_route,
                    }
                    # Counterfactual: a valid signed token with no
                    # committed consume+binding cannot read private bytes.
                    pre_consume = await media_client.get(
                        f"{bound_prefix}/{png_id}/content",
                        headers={"x-slaif-browser-preview": token_a},
                    )
                    assert pre_consume.status_code == 404
                    bound_document = await render_client.post(
                        "/internal/render/v1/preview",
                        headers={"X-SLAIF-Browser-Run-Token": token_a},
                        json=render_body,
                    )
                    assert bound_document.status_code == 200, bound_document.text
                    assert token_a not in bound_document.text
                    bound_nodes = _walk_nodes(
                        bound_document.json()["composition"]["nodes"]
                    )
                    image_node = next(
                        node
                        for node in bound_nodes
                        if node.get("component_type") == "Image"
                    )
                    assert image_node["props"]["mediaId"] == str(png_id)
                    assert image_node["media"] == {
                        "url": f"/media/v1/browser-preview/assets/{png_id}/content",
                        "mime_type": "image/png",
                        "size_bytes": len(PNG_BYTES),
                    }
                    document_node = next(
                        node
                        for node in bound_nodes
                        if node.get("component_type") == "DocumentList"
                    )
                    assert document_node["media_items"] == [
                        {
                            "url": (
                                f"/media/v1/browser-preview/assets/{pdf_id}/content"
                            ),
                            "mime_type": "application/pdf",
                            "size_bytes": len(PDF_BYTES),
                        }
                    ]
                    for media_id, expected in (
                        (png_id, PNG_BYTES),
                        (pdf_id, PDF_BYTES),
                    ):
                        bound_bytes = await media_client.get(
                            f"{bound_prefix}/{media_id}/content",
                            headers={"x-slaif-browser-preview": token_a},
                        )
                        assert bound_bytes.status_code == 200, bound_bytes.text
                        assert bound_bytes.content == expected
                    # Bound negative matrix (uniform 404, no oracle).
                    token_b = _issue_token(
                        capability_id=capability_id,
                        site_id=site_id,
                        workspace_id=workspace_id,
                        run_id=run_b,
                        route=bound_route,
                        nonce=NONCE_B,
                        now=int(time.time()),
                    )
                    tampered_a = token_a[:-4] + (
                        "0000" if token_a[-4:] != "0000" else "1111"
                    )
                    assert tampered_a != token_a
                    for case, expected_status in (
                        ({"x-slaif-browser-preview": token_b}, 404),
                        ({"x-slaif-browser-preview": tampered_a}, 404),
                        ({"x-slaif-browser-preview": "sbp1.aaaa.bbbb.cccc"}, 404),
                    ):
                        refused = await media_client.get(
                            f"{bound_prefix}/{png_id}/content",
                            headers=case,
                        )
                        assert refused.status_code == expected_status, refused.text
                    no_header = await media_client.get(
                        f"{bound_prefix}/{png_id}/content"
                    )
                    assert no_header.status_code == 404
                    doubled = await media_client.get(
                        f"{bound_prefix}/{png_id}/content",
                        headers=[
                            ("x-slaif-browser-preview", token_a),
                            ("x-slaif-browser-preview", token_a),
                        ],
                    )
                    assert doubled.status_code == 404
        # Runs: the binding facts are asserted outside the HTTP clients.
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            binding = await owner.fetchrow(
                "SELECT preview_credential_digest,"
                " preview_credential_nonce_digest,"
                " preview_credential_expires_at,"
                " preview_credential_attempt, preview_nonce_digest,"
                " preview_token_used_at FROM control.browser_run WHERE id=$1",
                run_a,
            )
            assert binding is not None
            assert binding[0] == hashlib.sha256(token_a.encode()).hexdigest()
            assert (
                binding[1] == hashlib.sha256(NONCE_A.encode()).hexdigest() == binding[4]
            )
            assert binding[2] == datetime.fromtimestamp(now_a + 30, tz=UTC)
            assert binding[3] == 1
            assert binding[5] is not None
            consumed = await owner.fetchval(
                "SELECT count(*) FROM audit.browser_event WHERE run_id=$1"
                " AND event_type='PREVIEW_TOKEN_CONSUMED'",
                run_a,
            )
            assert consumed == 1
            events = await owner.fetch(
                "SELECT * FROM audit.browser_event WHERE run_id=$1", run_a
            )
            assert token_a not in json.dumps([dict(row) for row in events], default=str)
        # Terminal run: the bound read dies with the run, and the render
        # preview itself rejects the one-time token replay.
        async with agent_pool.acquire() as agent:
            await _complete_run(agent, run_a, lease_a)
        async with media_app.router.lifespan_context(media_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=media_app),
                base_url="http://media.test",
            ) as media_client:
                terminal = await media_client.get(
                    f"/v1/browser-preview/assets/{png_id}/content",
                    headers={"x-slaif-browser-preview": token_a},
                )
                assert terminal.status_code == 404
        async with render_app.router.lifespan_context(render_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as render_client:
                replay = await render_client.post(
                    "/internal/render/v1/preview",
                    headers={"X-SLAIF-Browser-Run-Token": token_a},
                    json=render_body,
                )
                assert replay.status_code == 404
        # Credential-expiry lapse of a committed binding: B is claimed
        # (A terminal -> B oldest QUEUED), C is begun and claimed while
        # B holds a live lease.
        async with agent_pool.acquire() as agent:
            lease_b, attempt_b = await _claim_run(agent, run_b)
            assert attempt_b == 1
            run_c = await _begin_browser_run(
                agent,
                capability_id=capability_id,
                site_id=site_id,
                workspace_id=workspace_id,
                delegator_id=user_id,
                key="media-bytes-run-c",
                route=bound_route,
            )
            lease_c, attempt_c = await _claim_run(agent, run_c)
            assert attempt_c == 1
        token_c = _issue_token(
            capability_id=capability_id,
            site_id=site_id,
            workspace_id=workspace_id,
            run_id=run_c,
            route=bound_route,
            nonce=NONCE_C,
            now=int(time.time()),
            ttl_seconds=2,
        )
        async with render_app.router.lifespan_context(render_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=render_app),
                base_url="http://render.test",
            ) as render_client:
                bound_c = await render_client.post(
                    "/internal/render/v1/preview",
                    headers={"X-SLAIF-Browser-Run-Token": token_c},
                    json=render_body,
                )
                assert bound_c.status_code == 200, bound_c.text
        # The committed binding outlives nothing: once the credential
        # expiry lapses the bound read is refused even though the run
        # is still authorized.  (TTL 2s, then 2.5s: a 1s TTL would let
        # a second-boundary rollover between issue and verify flake.)
        await asyncio.sleep(2.5)
        async with media_app.router.lifespan_context(media_app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=media_app),
                base_url="http://media.test",
            ) as media_client:
                expired_token = await media_client.get(
                    f"/v1/browser-preview/assets/{png_id}/content",
                    headers={"x-slaif-browser-preview": token_c},
                )
                assert expired_token.status_code == 404
        # Release B and C back to QUEUED (A stays terminal): the
        # pre-freeze run shape for Phases 5-8.
        async with agent_pool.acquire() as agent:
            await _release_run(agent, run_b, lease_b)
            await _release_run(agent, run_c, lease_c)
        # -- Phase 5: real freeze captures both private assets. --
        seeded = {
            "delegator_id": user_id,
            "site_id": site_id,
            "workspace_id": workspace_id,
        }
        job_id, _ = await _freeze(database, seeded)
        worker_pool = await _worker_pool(database)
        try:
            rows = await _worker_call(
                database,
                "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                "media-bytes-worker",
                ["FREEZE"],
            )
            assert len(rows) == 1
            assert str(rows[0]["id"]) == str(job_id)
            result = await run_freeze_job(
                worker_pool, _worker_settings(database), dict(rows[0])
            )
            assert result.status == "SUCCEEDED", result.error
        finally:
            await worker_pool.close()
        snapshot = await _snapshot_row(database, workspace_id)
        assert snapshot is not None and snapshot["status"] == "COMPLETE"
        snapshot_id = UUID(str(snapshot["id"]))
        stored_payload = json.loads(snapshot["payload"])
        assert set(stored_payload["media"].keys()) == {str(png_id), str(pdf_id)}
        assert stored_payload["media"][str(png_id)] == {
            "id": str(png_id),
            "mime_type": "image/png",
            "size_bytes": len(PNG_BYTES),
            "content_hash": png_hash,
            "public_status": "private",
        }
        assert stored_payload["media"][str(pdf_id)] == {
            "id": str(pdf_id),
            "mime_type": "application/pdf",
            "size_bytes": len(PDF_BYTES),
            "content_hash": pdf_hash,
            "public_status": "private",
        }
        inventory = {
            row["id"]: row
            for row in stored_payload["media_inventory"]
            if isinstance(row, dict)
        }
        assert set(inventory) == {str(png_id), str(pdf_id)}
        # -- Phase 6: frozen review read serves the same bytes. --
        review_token = format_session_token(
            session_public, session_secret
        ).get_secret_value()
        # The internal review route is addressed with the SITE-LOCAL
        # route (the Web review-page contract); the site is bound by
        # the trusted authorize row, never by the request authority.
        review_request = {
            "authority": "localhost",
            "path": "/",
            "snapshot_id": str(snapshot_id),
        }
        async with (
            media_app.router.lifespan_context(media_app),
            render_app.router.lifespan_context(render_app),
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=media_app),
                base_url="http://media.test",
            ) as media_client:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=render_app),
                    base_url="http://render.test",
                ) as render_client:
                    review_response = await render_client.post(
                        "/internal/render/v1/review",
                        headers={"X-SLAIF-Human-Session": review_token},
                        json=review_request,
                    )
                    assert review_response.status_code == 200, review_response.text
                    review_body = review_response.json()
                    review_nodes = _walk_nodes(review_body["composition"]["nodes"])
                    review_image = next(
                        node
                        for node in review_nodes
                        if node.get("component_type") == "Image"
                    )
                    assert review_image["media"] == {
                        "url": (
                            f"/media/v1/review/{snapshot_id}/assets/{png_id}/content"
                        ),
                        "mime_type": "image/png",
                        "size_bytes": len(PNG_BYTES),
                    }
                    review_documents = next(
                        node
                        for node in review_nodes
                        if node.get("component_type") == "DocumentList"
                    )
                    assert review_documents["media_items"] == [
                        {
                            "url": (
                                f"/media/v1/review/{snapshot_id}"
                                f"/assets/{pdf_id}/content"
                            ),
                            "mime_type": "application/pdf",
                            "size_bytes": len(PDF_BYTES),
                        }
                    ]
                    for media_id, expected in (
                        (png_id, PNG_BYTES),
                        (pdf_id, PDF_BYTES),
                    ):
                        frozen = await media_client.get(
                            f"/v1/review/{snapshot_id}/assets/{media_id}/content",
                            headers=session_cookie(session_public, session_secret),
                        )
                        assert frozen.status_code == 200, frozen.text
                        assert frozen.content == expected
                    for negative_headers, expected_status in (
                        ({}, 401),
                        (
                            session_cookie(expired_public, expired_secret),
                            404,
                        ),
                    ):
                        refused = await media_client.get(
                            f"/v1/review/{snapshot_id}/assets/{png_id}/content",
                            headers=negative_headers,
                        )
                        assert refused.status_code == expected_status
                    unknown_snapshot = await media_client.get(
                        f"/v1/review/{uuid4()}/assets/{png_id}/content",
                        headers=session_cookie(session_public, session_secret),
                    )
                    assert unknown_snapshot.status_code == 404
                    unknown_media = await media_client.get(
                        f"/v1/review/{snapshot_id}/assets/{uuid4()}/content",
                        headers=session_cookie(session_public, session_secret),
                    )
                    assert unknown_media.status_code == 404
        # -- Phase 7: real terminal discard + pending cleanup. --
        discard_rows = await _control_call(
            database,
            "SELECT * FROM control.slaif_human_agent_workspace_discard($1,$2,$3)",
            workspace_id,
            site_id,
            user_id,
        )
        assert len(discard_rows) == 1
        discard_job_id = UUID(str(discard_rows[0]["job_id"]))
        discard_pool = await _worker_pool(database)
        try:
            discard_claimed = await _worker_call(
                database,
                "SELECT * FROM control.slaif_review_job_claim($1, $2)",
                "media-bytes-worker-discard",
                ["DISCARD"],
            )
            assert len(discard_claimed) == 1
            assert str(discard_claimed[0]["id"]) == str(discard_job_id)
            discard_result = await run_discard_job(
                discard_pool, _worker_settings(database), dict(discard_claimed[0])
            )
            assert discard_result.status == "SUCCEEDED", discard_result.error
        finally:
            await discard_pool.close()
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            discarded = await owner.fetchrow(
                "SELECT status, discarded_at FROM control.workspace WHERE id=$1",
                workspace_id,
            )
            assert str(discarded["status"]) == "DISCARDED"
            assert discarded["discarded_at"] is not None
            pending_operations = await get_session_operations(
                _ConnExecutor(owner), workspace_id, schema="content"
            )
        assert pending_operations == []
        # -- Phase 8: frozen bytes survive discard and pending cleanup. --
        async with (
            media_app.router.lifespan_context(media_app),
            render_app.router.lifespan_context(render_app),
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=media_app),
                base_url="http://media.test",
            ) as media_client:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=render_app),
                    base_url="http://render.test",
                ) as render_client:
                    after_discard = await render_client.post(
                        "/internal/render/v1/review",
                        headers={"X-SLAIF-Human-Session": review_token},
                        json=review_request,
                    )
                    assert after_discard.status_code == 200, after_discard.text
                    assert after_discard.json() == review_body
                    for media_id, expected in (
                        (png_id, PNG_BYTES),
                        (pdf_id, PDF_BYTES),
                    ):
                        still_frozen = await media_client.get(
                            f"/v1/review/{snapshot_id}/assets/{media_id}/content",
                            headers=session_cookie(session_public, session_secret),
                        )
                        assert still_frozen.status_code == 200, still_frozen.text
                        assert still_frozen.content == expected
        async with owner_connection(
            owner_dsn, expected_database=database.name
        ) as owner:
            # Site-scoped base media rows survive the workspace discard.
            assert (
                await owner.fetchval(
                    "SELECT count(*) FROM content.media_asset_base"
                    " WHERE site_id=$1 AND content_hash = ANY($2::text[])",
                    site_id,
                    [png_hash, pdf_hash],
                )
                == 2
            )
            # No effects: the read surfaces touched nothing.
            after_last_seen = await owner.fetchval(
                "SELECT array_agg(last_seen_at ORDER BY id::text) FROM "
                "control.user_session WHERE user_account_id = ANY($1::uuid[])",
                [user_id, user2_id, user3_id],
            )
            assert after_last_seen == before_last_seen
            assert (
                await owner.fetchval("SELECT count(*) FROM audit.human_editor_mutation")
                == 0
            )
    finally:
        await render_adapter.stop()
        await media_database.stop()
        await control_pool.close()
        await agent_pool.close()

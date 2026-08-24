"""Real PostgreSQL and local-filesystem proof for the private Media service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase
from pydantic import SecretStr
from slaif_agent_site.agent_state.foundation import asyncpg_cow_session
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.media_service.app import create_app
from slaif_agent_site.media_service.config import MediaDatabaseMode, MediaSettings
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.media_http import get_asset_content
from slaif_agent_site.media_service.store import MediaStore, StagedMedia
from starlette.requests import Request

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
                    iterator = stream_response.body_iterator
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
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM content.media_asset_base "
                            "WHERE id = $1",
                            media_id,
                        )
                        == 0
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

"""070-b ordinary-human, isolation, lock-race, and orphan evidence."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import asyncpg
import httpx
import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from pydantic import SecretStr
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import reconcile, upgrade
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.control_api.config import (
    ControlDatabaseMode,
    ControlDatabaseSettings,
)
from slaif_agent_site.control_api.database import ControlDatabase
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.editor_api.app import create_app as create_editor_app
from slaif_agent_site.editor_api.config import (
    EditorDatabaseMode,
    EditorDatabaseSettings,
)
from slaif_agent_site.editor_api.database import EditorDatabase
from slaif_agent_site.media_service.app import create_app as create_media_app
from slaif_agent_site.media_service.config import MediaDatabaseMode, MediaSettings
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.store import MediaStore

PNG = b"\x89PNG\r\n\x1a\nordinary-human-media"
ORPHAN_PNG = b"\x89PNG\r\n\x1a\norphan-after-db-failure"


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
        pool_max_size=3,
        application_name="media-070b-control",
    )


def _editor_settings(database: AgentSiteDatabase) -> EditorDatabaseSettings:
    login, _password = database.credentials["slaif_editor_runtime"]
    return EditorDatabaseSettings(
        mode=EditorDatabaseMode.TEST,
        dsn=SecretStr(_locator(database, "slaif_editor_runtime")),
        dsn_file=None,
        expected_database=database.name,
        expected_login=login,
        pool_min_size=1,
        pool_max_size=3,
        application_name="media-070b-editor",
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
        pool_max_size=3,
        application_name="media-070b",
    )


def _cookie(session: Any) -> str:
    return (
        f"slaif_session={session.token.get_secret_value()}; "
        f"slaif_csrf={session.csrf_token.get_secret_value()}"
    )


def _headers(session: Any, key: str, *, csrf: str | None = None) -> dict[str, str]:
    csrf_value = csrf or session.csrf_token.get_secret_value()
    return {
        "cookie": _cookie(session),
        "x-csrf-token": csrf_value,
        "Idempotency-Key": key,
    }


async def _seed_ordinary_fixture(database: AgentSiteDatabase) -> dict[str, UUID]:
    await upgrade(database.settings)
    await reconcile(database.settings)
    ids = {
        "user_a": uuid4(),
        "user_b": uuid4(),
        "viewer": uuid4(),
        "site_a": uuid4(),
        "site_b": uuid4(),
    }
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.executemany(
            "INSERT INTO control.user_account "
            "(id, identity_kind, oidc_issuer, oidc_subject, display_name) "
            "VALUES ($1, 'OIDC', 'https://070b.test', $2, $3)",
            [
                (ids["user_a"], str(ids["user_a"]), "Ordinary A"),
                (ids["user_b"], str(ids["user_b"]), "Ordinary B"),
                (ids["viewer"], str(ids["viewer"]), "Viewer"),
            ],
        )
        await owner.executemany(
            "INSERT INTO control.site "
            "(id, site_key, display_name, default_locale, component_catalog_version) "
            "VALUES ($1, $2, $3, 'en', 'catalog-v1')",
            [
                (ids["site_a"], f"070b-a-{ids['site_a'].hex[:10]}", "Site A"),
                (ids["site_b"], f"070b-b-{ids['site_b'].hex[:10]}", "Site B"),
            ],
        )
        await owner.executemany(
            "INSERT INTO control.site_membership "
            "(site_id, user_account_id, role_key, delegation_ceiling) "
            "VALUES ($1, $2, $3, $4)",
            [
                (ids["site_a"], ids["user_a"], "SITE_EDITOR", 2),
                (ids["site_a"], ids["user_b"], "SITE_EDITOR", 2),
                (ids["site_b"], ids["user_b"], "SITE_EDITOR", 2),
                (ids["site_a"], ids["viewer"], "VIEWER", 0),
            ],
        )
        for workspace_name, site_key, user_key in (
            ("workspace_a", "site_a", "user_a"),
            ("workspace_b", "site_a", "user_b"),
            ("workspace_c", "site_b", "user_b"),
            ("workspace_viewer", "site_a", "viewer"),
        ):
            ids[workspace_name] = await owner.fetchval(
                "INSERT INTO control.workspace "
                "(site_id, created_by, actor_type, title, delegation_preset, "
                "effective_scopes, status, expires_at) "
                "VALUES ($1, $2, 'HUMAN', $3, 'L2_SITE_EDITOR', '[]'::jsonb, "
                "'ACTIVE', now() + interval '1 hour') RETURNING id",
                ids[site_key],
                ids[user_key],
                workspace_name,
            )
    return ids


@pytest.mark.asyncio
async def test_media_ordinary_rbac_isolation_editor_delete_and_orphan(
    agent_site_database: AgentSiteDatabase, tmp_path: Path
) -> None:
    database = agent_site_database
    ids = await _seed_ordinary_fixture(database)
    store = MediaStore(tmp_path / "media")
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

    async with editor_app.router.lifespan_context(editor_app):
        async with media_app.router.lifespan_context(media_app):
            session_a = await control.human_session_service().create(ids["user_a"])
            session_b = await control.human_session_service().create(ids["user_b"])
            viewer = await control.human_session_service().create(ids["viewer"])
            async with (
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=media_app),
                    base_url="http://media-070b.test",
                ) as media_client,
                httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=editor_app),
                    base_url="http://editor-070b.test",
                ) as editor_client,
            ):
                missing_auth = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{uuid4()}/content"
                )
                assert missing_auth.status_code == 401

                wrong_csrf = await media_client.post(
                    f"/v1/sites/{ids['site_a']}/assets",
                    headers=_headers(
                        session_a,
                        "ordinary-wrong-csrf",
                        csrf="sas2_csrf_" + "A" * 43,
                    ),
                    files={"file": ("wrong.png", PNG, "image/png")},
                )
                assert wrong_csrf.status_code == 403

                viewer_read = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{uuid4()}/content",
                    headers={"cookie": _cookie(viewer)},
                )
                assert viewer_read.status_code in {403, 404}
                viewer_upload = await media_client.post(
                    f"/v1/sites/{ids['site_a']}/assets",
                    headers=_headers(viewer, "viewer-upload-denied"),
                    files={"file": ("viewer.png", PNG, "image/png")},
                )
                assert viewer_upload.status_code in {403, 404}
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM control.media_idempotency "
                            "WHERE workspace_id = $1",
                            ids["workspace_viewer"],
                        )
                        == 0
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM audit.media_mutation "
                            "WHERE workspace_id = $1",
                            ids["workspace_viewer"],
                        )
                        == 0
                    )

                uploaded = await media_client.post(
                    f"/v1/sites/{ids['site_a']}/assets",
                    headers=_headers(session_a, "ordinary-site-a"),
                    data={
                        "alt_text": "A private alt",
                        "metadata": json.dumps({"site": "a"}),
                    },
                    files={"file": ("a.png", PNG, "image/png")},
                )
                assert uploaded.status_code == 201, uploaded.text
                record_a = uploaded.json()["record"]
                media_a = UUID(record_a["id"])

                foreign_workspace = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{media_a}/content",
                    headers={"cookie": _cookie(session_b)},
                )
                assert foreign_workspace.status_code in {403, 404}
                assert str(media_a) not in foreign_workspace.text

                second_site = await media_client.post(
                    f"/v1/sites/{ids['site_b']}/assets",
                    headers=_headers(session_b, "ordinary-site-b"),
                    data={
                        "alt_text": "B private alt",
                        "metadata": json.dumps({"site": "b"}),
                    },
                    files={"file": ("b.png", PNG, "image/png")},
                )
                assert second_site.status_code == 201, second_site.text
                record_b = second_site.json()["record"]
                media_b = UUID(record_b["id"])
                assert media_b != media_a
                assert record_b["storage_key"] == record_a["storage_key"]

                cross_site = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{media_b}/content",
                    headers={"cookie": _cookie(session_a)},
                )
                assert cross_site.status_code in {403, 404}
                assert str(media_b) not in cross_site.text

                patch = await editor_client.patch(
                    f"/api/editor/v1/sites/{ids['site_a']}/media/{media_a}",
                    headers=_headers(session_a, "editor-media-patch"),
                    json={"alt_text": "A patched alt", "metadata": {"patched": True}},
                )
                assert patch.status_code == 200, patch.text
                assert patch.json()["alt_text"] == "A patched alt"
                assert patch.json()["metadata"] == {"patched": True}
                assert patch.json()["content_hash"] == record_a["content_hash"]
                assert patch.json()["storage_key"] == record_a["storage_key"]

                editor_b = await editor_client.get(
                    f"/api/editor/v1/sites/{ids['site_b']}/media/{media_b}",
                    headers={"cookie": _cookie(session_b)},
                )
                assert editor_b.status_code == 200
                assert editor_b.json()["alt_text"] == "B private alt"
                assert editor_b.json()["metadata"] == {"site": "b"}

                deleted = await editor_client.delete(
                    f"/api/editor/v1/sites/{ids['site_a']}/media/{media_a}",
                    headers=_headers(session_a, "editor-media-delete"),
                )
                assert deleted.status_code == 204
                deleted_read = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{media_a}/content",
                    headers={"cookie": _cookie(session_a)},
                )
                assert deleted_read.status_code == 404
                object_path = store.object_path(record_a["storage_key"])
                assert object_path.read_bytes() == PNG
                retained = await media_client.get(
                    f"/v1/sites/{ids['site_b']}/assets/{media_b}/content",
                    headers={"cookie": _cookie(session_b)},
                )
                assert retained.status_code == 200
                assert retained.content == PNG

                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.workspace SET status = 'REVOKED' WHERE id = $1",
                        ids["workspace_a"],
                    )
                revoked_workspace = await media_client.post(
                    f"/v1/sites/{ids['site_a']}/assets",
                    headers=_headers(session_a, "revoked-workspace"),
                    files={"file": ("revoked.png", PNG, "image/png")},
                )
                assert revoked_workspace.status_code in {403, 404}
                assert list(store.staging_root.iterdir()) == []
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM control.media_idempotency "
                            "WHERE workspace_id = $1 AND idempotency_key = $2",
                            ids["workspace_a"],
                            "revoked-workspace",
                        )
                        == 0
                    )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.workspace SET status = 'ACTIVE' WHERE id = $1",
                        ids["workspace_a"],
                    )
                    await owner.execute(
                        "UPDATE control.workspace SET expires_at = now() - "
                        "interval '1 second' "
                        "WHERE id = $1",
                        ids["workspace_a"],
                    )
                expired_workspace = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{media_a}/content",
                    headers={"cookie": _cookie(session_a)},
                )
                assert expired_workspace.status_code in {403, 404}
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.workspace SET expires_at = now() + "
                        "interval '1 hour' "
                        "WHERE id = $1",
                        ids["workspace_a"],
                    )
                    await owner.execute(
                        "UPDATE control.site SET status = 'ARCHIVED' WHERE id = $1",
                        ids["site_a"],
                    )
                inactive_site = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{media_a}/content",
                    headers={"cookie": _cookie(session_a)},
                )
                assert inactive_site.status_code in {403, 404}
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    await owner.execute(
                        "UPDATE control.site SET status = 'ACTIVE' WHERE id = $1",
                        ids["site_a"],
                    )

                await control.human_session_service().revoke(
                    session_b.token, session_b.csrf_token
                )
                revoked_session = await media_client.get(
                    f"/v1/sites/{ids['site_b']}/assets/{media_b}/content",
                    headers={"cookie": _cookie(session_b)},
                )
                assert revoked_session.status_code in {401, 403, 404}

                class FailingRegistrationDatabase(MediaDatabase):
                    async def register(self, **kwargs: object) -> Any:
                        raise RuntimeError("injected_registration_failure")

                failing_database = FailingRegistrationDatabase(media_database.settings)
                failing_app = create_media_app(
                    settings=ServiceSettings.for_test(),
                    media_settings=failing_database.settings,
                    database=failing_database,
                    store=store,
                )
                orphan_bytes = ORPHAN_PNG
                orphan_digest = hashlib.sha256(orphan_bytes).hexdigest()
                orphan_key = (
                    f"sha256/{orphan_digest[:2]}/{orphan_digest[2:4]}/{orphan_digest}"
                )
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    before_orphan_counts = await owner.fetchrow(
                        "SELECT "
                        "(SELECT count(*) FROM content.media_asset_base "
                        " WHERE content_hash = $1), "
                        "(SELECT count(*) FROM control.media_idempotency "
                        " WHERE workspace_id = $2), "
                        "(SELECT count(*) FROM audit.media_mutation "
                        " WHERE workspace_id = $2)",
                        orphan_digest,
                        ids["workspace_a"],
                    )
                    before_orphan_operations = await get_session_operations(
                        AsyncpgExecutor(owner), ids["workspace_a"], schema="content"
                    )
                async with failing_app.router.lifespan_context(failing_app):
                    async with httpx.AsyncClient(
                        transport=httpx.ASGITransport(app=failing_app),
                        base_url="http://media-070b-failing.test",
                    ) as failing_client:
                        orphan = await failing_client.post(
                            f"/v1/sites/{ids['site_a']}/assets",
                            headers=_headers(session_a, "injected-db-failure"),
                            data={"alt_text": "orphan", "metadata": "{}"},
                            files={"file": ("orphan.png", orphan_bytes, "image/png")},
                        )
                        assert orphan.status_code == 503
                assert store.object_path(orphan_key).read_bytes() == orphan_bytes
                assert list(store.staging_root.iterdir()) == []
                async with owner_connection(
                    database.settings.resolved_owner_dsn(),
                    expected_database=database.name,
                ) as owner:
                    after_orphan_counts = await owner.fetchrow(
                        "SELECT "
                        "(SELECT count(*) FROM content.media_asset_base "
                        " WHERE content_hash = $1), "
                        "(SELECT count(*) FROM control.media_idempotency "
                        " WHERE workspace_id = $2), "
                        "(SELECT count(*) FROM audit.media_mutation "
                        " WHERE workspace_id = $2)",
                        orphan_digest,
                        ids["workspace_a"],
                    )
                    assert tuple(after_orphan_counts) == tuple(before_orphan_counts)
                    assert (
                        await get_session_operations(
                            AsyncpgExecutor(owner),
                            ids["workspace_a"],
                            schema="content",
                        )
                        == before_orphan_operations
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM control.media_idempotency "
                            "WHERE workspace_id = $1 AND idempotency_key = $2",
                            ids["workspace_a"],
                            "injected-db-failure",
                        )
                        == 0
                    )
                guessed = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{uuid4()}/content",
                    headers={"cookie": _cookie(session_a)},
                )
                assert guessed.status_code == 404

                await control.human_session_service().revoke(
                    viewer.token, viewer.csrf_token
                )
                revoked = await media_client.get(
                    f"/v1/sites/{ids['site_a']}/assets/{media_a}/content",
                    headers={"cookie": _cookie(viewer)},
                )
                assert revoked.status_code in {401, 403, 404}


async def _wait_for_advisory_waiter(database: AgentSiteDatabase, pid: int) -> None:
    for _ in range(1000):
        row = await database.administrator.fetchrow(
            "SELECT wait_event_type, wait_event, state "
            "FROM pg_catalog.pg_stat_activity WHERE pid = $1",
            pid,
        )
        if row is not None and tuple(row) == ("Lock", "advisory", "active"):
            return
        await asyncio.sleep(0)
    raise AssertionError("Media assertion did not wait on the shared workspace lock")


@pytest.mark.asyncio
async def test_media_workspace_assertion_waits_for_revoke(
    agent_site_database: AgentSiteDatabase,
) -> None:
    database = agent_site_database
    ids = await _seed_ordinary_fixture(database)
    control = ControlDatabase(_control_settings(database))
    media_database = MediaDatabase(
        _media_settings(database, Path("/tmp") / f"media-{uuid4()}")
    )
    await control.start()
    await media_database.start()
    try:
        session = await control.human_session_service().create(ids["user_a"])
        async with media_database.cow_pool().acquire() as blocked_connection:
            blocked_pid = blocked_connection.get_server_pid()
            operation_id = uuid4()

            async def blocked_assertion() -> None:
                async with asyncpg_cow_session(
                    blocked_connection,
                    session_id=ids["workspace_a"],
                    operation_id=operation_id,
                ) as cow:
                    await cow.native.fetchrow(
                        "SELECT control.slaif_media_workspace_assert("
                        "$1,$2,$3,$4,$5,$6)",
                        ids["workspace_a"],
                        ids["user_a"],
                        ids["site_a"],
                        session.session_id,
                        "media:upload",
                        operation_id,
                    )

            owner_pool = await database.role_pool("slaif_owner")
            try:
                async with owner_pool.acquire() as owner:
                    async with owner.transaction():
                        await owner.fetchval(
                            "SELECT pg_advisory_xact_lock(hashtextextended($1, 280))",
                            str(ids["workspace_a"]),
                        )
                        baseline = await get_session_operations(
                            AsyncpgExecutor(owner),
                            ids["workspace_a"],
                            schema="content",
                        )
                        blocked = asyncio.create_task(blocked_assertion())
                        await asyncio.sleep(0)
                        await owner.execute(
                            "UPDATE control.site_membership SET status = 'INACTIVE' "
                            "WHERE site_id = $1 AND user_account_id = $2",
                            ids["site_a"],
                            ids["user_a"],
                        )
                        await _wait_for_advisory_waiter(database, blocked_pid)
                        assert not blocked.done()
                with pytest.raises(asyncpg.PostgresError):
                    await blocked
                async with owner_pool.acquire() as owner:
                    await owner.execute(
                        "UPDATE control.site_membership SET status = 'ACTIVE' "
                        "WHERE site_id = $1 AND user_account_id = $2",
                        ids["site_a"],
                        ids["user_a"],
                    )
                    assert (
                        await get_session_operations(
                            AsyncpgExecutor(owner),
                            ids["workspace_a"],
                            schema="content",
                        )
                        == baseline
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM control.media_idempotency "
                            "WHERE workspace_id = $1",
                            ids["workspace_a"],
                        )
                        == 0
                    )
                    assert (
                        await owner.fetchval(
                            "SELECT count(*) FROM audit.media_mutation "
                            "WHERE workspace_id = $1",
                            ids["workspace_a"],
                        )
                        == 0
                    )
            finally:
                await owner_pool.close()
    finally:
        await media_database.stop()
        await control.stop()

"""079/1 media publication core: store, finalization, and HTTP error keys.

Unit evidence for R1/R2/R3/R5 (R8).  No network and no real database:
the record boundary is stubbed exactly at the narrow repository surface
the finalization primitive orchestrates over, and the HTTP matrices run
the real routes against a real on-disk store with a stub record
database.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from slaif_agent_site.agent_api.app import create_app as create_agent_app
from slaif_agent_site.agent_api.config import (
    AgentDatabaseMode,
    AgentDatabaseSettings,
)
from slaif_agent_site.agent_api.models import AgentCapabilityContext
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.health import ProbeResult
from slaif_agent_site.identity.sessions import (
    format_csrf_token,
    format_session_token,
    make_session_public_id,
)
from slaif_agent_site.media_service.app import create_app as create_media_app
from slaif_agent_site.media_service.config import MediaDatabaseMode, MediaSettings
from slaif_agent_site.media_service.database import (
    MediaAuthContext,
    MediaRecord,
)
from slaif_agent_site.media_service.finalize import (
    FinalizationError,
    FinalizationRepositoryError,
    finalize_media_for_promotion,
)
from slaif_agent_site.media_service.store import (
    MediaStore,
    MediaStoreError,
    StagedMedia,
)

PNG = b"\x89PNG\r\n\x1a\npublic-core-fixture"
JPEG = b"\xff\xd8\xff\xe0jpeg-public-core-fixture"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _public_key(digest: str) -> str:
    return "public/sha256/" + digest[:2] + "/" + digest[2:4] + "/" + digest


def _publish(store: MediaStore, payload: bytes, mime_type: str) -> str:
    staging = store.create_staging_path()
    staging.write_bytes(payload)
    return store.publish(
        StagedMedia(staging, _digest(payload), len(payload), mime_type)
    )


def _record(
    media_id: UUID,
    site_id: UUID,
    *,
    payload: bytes,
    mime_type: str,
    storage_key: str,
    public_status: str = "private",
) -> MediaRecord:
    now = datetime.now(UTC)
    return MediaRecord(
        id=media_id,
        site_id=site_id,
        uploaded_by=uuid4(),
        filename="fixture",
        mime_type=mime_type,
        size_bytes=len(payload),
        content_hash=_digest(payload),
        storage_key=storage_key,
        alt_text="fixture",
        metadata={},
        created_at=now,
        updated_at=now,
        public_status=public_status,
        published_at=now if public_status == "public" else None,
    )


class FakeRepository:
    """The narrow record boundary the primitive orchestrates over."""

    def __init__(
        self,
        records: dict[tuple[UUID, UUID], MediaRecord],
        *,
        fetch_failures: dict[UUID, str] | None = None,
        mark_failures: dict[UUID, str] | None = None,
    ) -> None:
        self._records = records
        self._fetch_failures = fetch_failures or {}
        self._mark_failures = mark_failures or {}
        self.marked: list[tuple[UUID, UUID, UUID]] = []

    async def fetch_media(self, site_id: UUID, media_id: UUID) -> MediaRecord | None:
        if media_id in self._fetch_failures:
            raise FinalizationRepositoryError(self._fetch_failures[media_id])
        return self._records.get((site_id, media_id))

    async def mark_public(
        self, site_id: UUID, media_id: UUID, workspace_id: UUID
    ) -> None:
        if media_id in self._mark_failures:
            raise FinalizationRepositoryError(self._mark_failures[media_id])
        self.marked.append((site_id, media_id, workspace_id))


# --- R1: public namespace store behavior -------------------------------


def test_publish_public_is_idempotent_and_digest_verified(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    key = _publish(store, PNG, "image/png")
    digest = _digest(PNG)
    public_key = store.publish_public(key, digest, len(PNG))
    assert public_key == _public_key(digest)
    again = store.publish_public(key, digest, len(PNG))
    assert again == public_key
    public_path = store.public_root / "sha256" / digest[:2] / digest[2:4] / digest
    assert public_path.read_bytes() == PNG
    # The private object keeps the store invariant (nlink == 1).
    assert store.object_path(key).stat().st_nlink == 1
    descriptor, size = store.open_public_verified(digest, len(PNG))
    try:
        data = b""
        while chunk := os.read(descriptor, 1024 * 1024):
            data += chunk
    finally:
        os.close(descriptor)
    assert data == PNG
    assert size == len(PNG)


def test_publish_public_rejects_bad_inputs(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    key = _publish(store, PNG, "image/png")
    digest = _digest(PNG)
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.publish_public(key, digest, len(PNG) + 1)
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.publish_public("sha256/bad", digest, len(PNG))
    with pytest.raises(MediaStoreError, match="storage_unavailable"):
        store.publish_public(key, "Z" * 64, len(PNG))
    with pytest.raises(MediaStoreError, match="media_missing"):
        store.open_public_verified(digest, len(PNG))


def test_publish_public_detects_corrupt_destination(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    key = _publish(store, PNG, "image/png")
    digest = _digest(PNG)
    store.publish_public(key, digest, len(PNG))
    destination = store.public_root / "sha256" / digest[:2] / digest[2:4] / digest
    with destination.open("r+b") as handle:
        handle.write(b"x")
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.publish_public(key, digest, len(PNG))
    # The corrupt destination is never overwritten or truncated.
    assert destination.read_bytes()[0] == 0x78


def test_open_public_verified_rejects_corrupt_object(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    key = _publish(store, PNG, "image/png")
    digest = _digest(PNG)
    store.publish_public(key, digest, len(PNG))
    public_path = store.public_root / "sha256" / digest[:2] / digest[2:4] / digest
    with public_path.open("r+b") as handle:
        handle.write(b"x")
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.open_public_verified(digest, len(PNG))


# --- R2: finalization primitive ----------------------------------------


async def test_finalization_happy_path_mixed_and_deterministic(
    tmp_path: Path,
) -> None:
    site_id = uuid4()
    workspace_id = uuid4()
    first = UUID(int=1)
    second = UUID(int=2)
    store = MediaStore(tmp_path / "media")
    first_key = _publish(store, PNG, "image/png")
    second_key = _publish(store, JPEG, "image/jpeg")
    first_digest = _digest(PNG)
    second_digest = _digest(JPEG)
    repository = FakeRepository(
        {
            (site_id, first): _record(
                first,
                site_id,
                payload=PNG,
                mime_type="image/png",
                storage_key=first_key,
                public_status="public",
            ),
            (site_id, second): _record(
                second,
                site_id,
                payload=JPEG,
                mime_type="image/jpeg",
                storage_key=second_key,
            ),
        }
    )
    # The already-public entry is pre-published to prove idempotency.
    store.publish_public(first_key, first_digest, len(PNG))
    # Input order is hostile (reversed + duplicated); the manifest must be
    # deterministic and deduplicated.
    manifest = await finalize_media_for_promotion(
        site_id,
        workspace_id,
        [second, first, second, first],
        store=store,
        repository=repository,
    )
    assert manifest.to_list() == [
        {
            "media_id": str(first),
            "digest": first_digest,
            "public_key": _public_key(first_digest),
        },
        {
            "media_id": str(second),
            "digest": second_digest,
            "public_key": _public_key(second_digest),
        },
    ]
    assert repository.marked == [
        (site_id, first, workspace_id),
        (site_id, second, workspace_id),
    ]


async def test_finalization_store_failure_manifest_exact(
    tmp_path: Path,
) -> None:
    site_id = uuid4()
    workspace_id = uuid4()
    first = UUID(int=1)
    second = UUID(int=2)
    store = MediaStore(tmp_path / "media")
    first_key = _publish(store, PNG, "image/png")
    # The second private object is corrupt: digest verification fails.
    second_key = _publish(store, JPEG, "image/jpeg")
    second_object = store.object_path(second_key)
    with second_object.open("r+b") as handle:
        handle.write(b"x")
    first_digest = _digest(PNG)
    repository = FakeRepository(
        {
            (site_id, first): _record(
                first,
                site_id,
                payload=PNG,
                mime_type="image/png",
                storage_key=first_key,
            ),
            (site_id, second): _record(
                second,
                site_id,
                payload=JPEG,
                mime_type="image/jpeg",
                storage_key=second_key,
            ),
        }
    )
    with pytest.raises(FinalizationError) as excinfo:
        await finalize_media_for_promotion(
            site_id,
            workspace_id,
            [first, second],
            store=store,
            repository=repository,
        )
    error = excinfo.value
    assert error.reason == "store_unavailable"
    # Exactly the bytes made public: the first asset, never the second.
    assert error.manifest.to_list() == [
        {
            "media_id": str(first),
            "digest": first_digest,
            "public_key": _public_key(first_digest),
        }
    ]
    assert repository.marked == [(site_id, first, workspace_id)]


async def test_finalization_mark_failure_includes_published_bytes(
    tmp_path: Path,
) -> None:
    site_id = uuid4()
    workspace_id = uuid4()
    first = UUID(int=1)
    second = UUID(int=2)
    store = MediaStore(tmp_path / "media")
    first_key = _publish(store, PNG, "image/png")
    second_key = _publish(store, JPEG, "image/jpeg")
    first_digest = _digest(PNG)
    second_digest = _digest(JPEG)
    repository = FakeRepository(
        {
            (site_id, first): _record(
                first,
                site_id,
                payload=PNG,
                mime_type="image/png",
                storage_key=first_key,
            ),
            (site_id, second): _record(
                second,
                site_id,
                payload=JPEG,
                mime_type="image/jpeg",
                storage_key=second_key,
            ),
        },
        mark_failures={second: "media_not_workspace_referenced"},
    )
    with pytest.raises(FinalizationError) as excinfo:
        await finalize_media_for_promotion(
            site_id,
            workspace_id,
            [first, second],
            store=store,
            repository=repository,
        )
    error = excinfo.value
    assert error.reason == "media_not_workspace_referenced"
    # The second asset's bytes WERE made public before the mark failed, so
    # the manifest must list both, in deterministic order.
    assert error.manifest.to_list() == [
        {
            "media_id": str(first),
            "digest": first_digest,
            "public_key": _public_key(first_digest),
        },
        {
            "media_id": str(second),
            "digest": second_digest,
            "public_key": _public_key(second_digest),
        },
    ]


async def test_finalization_not_found_and_repository_errors(tmp_path: Path) -> None:
    site_id = uuid4()
    workspace_id = uuid4()
    missing = uuid4()
    store = MediaStore(tmp_path / "media")
    with pytest.raises(FinalizationError) as excinfo:
        await finalize_media_for_promotion(
            site_id,
            workspace_id,
            [missing],
            store=store,
            repository=FakeRepository({}),
        )
    assert excinfo.value.reason == "media_not_found"
    assert excinfo.value.manifest.to_list() == []
    failing = uuid4()
    with pytest.raises(FinalizationError) as excinfo:
        await finalize_media_for_promotion(
            site_id,
            workspace_id,
            [failing],
            store=store,
            repository=FakeRepository(
                {}, fetch_failures={failing: "repository_unavailable"}
            ),
        )
    assert excinfo.value.reason == "repository_unavailable"


# --- R3/R4: public digest route + preview authorization matrix ---------


class StubMediaDatabase:
    def __init__(
        self,
        *,
        context: MediaAuthContext | None,
        record: MediaRecord | None,
        public_record: Any = None,
    ) -> None:
        self._context = context
        self._record = record
        self._public_record = public_record

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    async def authorize(self, **_kwargs: Any) -> MediaAuthContext | None:
        return self._context

    async def get(self, **_kwargs: Any) -> MediaRecord | None:
        return self._record

    async def get_public(self, *, content_hash: str) -> Any:
        if self._public_record is None:
            return None
        return self._public_record


class SelectingPublicDatabase(StubMediaDatabase):
    """Record-boundary stub keyed by content hash."""

    def __init__(self, records: dict[str, Any]) -> None:
        super().__init__(context=None, record=None)
        self._records = records

    async def get_public(self, *, content_hash: str) -> Any:
        return self._records.get(content_hash)


def _media_settings(root: Path) -> MediaSettings:
    return MediaSettings(
        mode=MediaDatabaseMode.TEST,
        dsn=SecretStr("postgresql://slaif_media_login:unit@127.0.0.1:5432/slaif"),
        dsn_file=None,
        expected_database="slaif",
        expected_login="slaif_media_login",
        media_root=root,
        pool_min_size=1,
        pool_max_size=2,
        application_name="media-public-core-unit",
    )


def _context(site_id: UUID, workspace_id: UUID) -> MediaAuthContext:
    return MediaAuthContext(
        session_id=uuid4(),
        human_user_id=uuid4(),
        site_id=site_id,
        workspace_id=workspace_id,
        permission="media:read",
    )


def _cookie(session_secret: bytes, csrf_secret: bytes) -> dict[str, str]:
    public_id = make_session_public_id()
    session = format_session_token(public_id, session_secret).get_secret_value()
    csrf = format_csrf_token(csrf_secret).get_secret_value()
    return {"slaif_session": session, "slaif_csrf": csrf}


def _media_client(
    store: MediaStore, database: StubMediaDatabase, tmp_path: Path
) -> TestClient:
    app = create_media_app(
        settings=ServiceSettings.for_test(),
        media_settings=_media_settings(tmp_path),
        database=database,  # type: ignore[arg-type]
        store=store,
    )
    return TestClient(app)


def test_public_digest_route_serves_byte_identical_bytes_with_headers(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media")
    key = _publish(store, PNG, "image/png")
    digest = _digest(PNG)
    store.publish_public(key, digest, len(PNG))
    public_record = type("P", (), {})()
    public_record.content_hash = digest
    public_record.mime_type = "image/png"
    public_record.size_bytes = len(PNG)
    public_record.public_status = "public"
    client = _media_client(
        store,
        StubMediaDatabase(context=None, record=None, public_record=public_record),
        tmp_path,
    )
    url = f"/v1/public/sha256/{digest[:2]}/{digest[2:4]}/{digest}"
    response = client.get(url)
    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"
    assert response.headers["content-length"] == str(len(PNG))
    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
    # The public digest URL is edge-exposed: the edge (NGINX/Apache) owns
    # X-Content-Type-Options on the public surface, so the app must not
    # also set it (the edge add_header would otherwise duplicate it).
    assert "x-content-type-options" not in response.headers


def test_public_digest_route_fail_closed_shapes_and_states(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media")
    key = _publish(store, PNG, "image/png")
    digest = _digest(PNG)
    store.publish_public(key, digest, len(PNG))
    public_record = type("P", (), {})()
    public_record.content_hash = digest
    public_record.mime_type = "image/png"
    public_record.size_bytes = len(PNG)
    public_record.public_status = "public"
    client = _media_client(
        store,
        StubMediaDatabase(context=None, record=None, public_record=public_record),
        tmp_path,
    )
    other = "ab" * 32
    # Absent digest (unknown to the record boundary): 404, never 403.
    assert (
        client.get(f"/v1/public/sha256/{other[:2]}/{other[2:4]}/{other}").status_code
        == 404
    )
    # Hostile path shapes: 404.
    assert client.get(f"/v1/public/sha256/{digest[:2]}/zz/{digest}").status_code == 404
    assert (
        client.get(f"/v1/public/sha256/{digest[:3]}/{digest[3:5]}/{digest}").status_code
        == 404
    )
    assert (
        client.get(
            f"/v1/public/sha256/{digest[:2]}/{digest[2:4]}/{digest.upper()}"
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/v1/public/sha256/{digest[:2]}/{digest[2:4]}/{digest}extra"
        ).status_code
        == 404
    )
    # Digest known to the record boundary but no public object on disk.
    missing_digest = _digest(JPEG)
    known_record = type("P", (), {})()
    known_record.content_hash = missing_digest
    known_record.mime_type = "image/jpeg"
    known_record.size_bytes = len(JPEG)
    known_record.public_status = "public"
    database = SelectingPublicDatabase(
        {digest: public_record, missing_digest: known_record}
    )
    client = _media_client(store, database, tmp_path)
    assert (
        client.get(
            f"/v1/public/sha256/{missing_digest[:2]}/{missing_digest[2:4]}/{missing_digest}"
        ).status_code
        == 404
    )
    # Corrupt public object: 503 (storage unavailable), never bytes.
    corrupt_payload = b"\x89PNG\r\n\x1a\ncorrupt-fixture"
    corrupt_key = _publish(store, corrupt_payload, "image/png")
    corrupt_digest = _digest(corrupt_payload)
    store.publish_public(corrupt_key, corrupt_digest, len(corrupt_payload))
    corrupt_path = (
        store.public_root
        / "sha256"
        / corrupt_digest[:2]
        / corrupt_digest[2:4]
        / corrupt_digest
    )
    with corrupt_path.open("r+b") as handle:
        handle.write(b"x")
    corrupt_record = type("P", (), {})()
    corrupt_record.content_hash = corrupt_digest
    corrupt_record.mime_type = "image/png"
    corrupt_record.size_bytes = len(corrupt_payload)
    corrupt_record.public_status = "public"
    client = _media_client(
        store,
        SelectingPublicDatabase({corrupt_digest: corrupt_record}),
        tmp_path,
    )
    response = client.get(
        f"/v1/public/sha256/{corrupt_digest[:2]}/{corrupt_digest[2:4]}/{corrupt_digest}"
    )
    assert response.status_code == 503


def _preview_client(
    tmp_path: Path, database: StubMediaDatabase
) -> tuple[TestClient, str]:
    store = MediaStore(tmp_path / "media")
    payload = PNG
    key = _publish(store, payload, "image/png")
    media_id = uuid4()
    site_id = uuid4()
    record = _record(
        media_id, site_id, payload=payload, mime_type="image/png", storage_key=key
    )
    database._record = record
    client = _media_client(store, database, tmp_path)
    url = f"/v1/sites/{site_id}/assets/{media_id}/content"
    return client, url


def test_preview_read_authorization_matrix(tmp_path: Path) -> None:
    site_id = uuid4()
    # Member: 200 + exact private bytes.
    database = StubMediaDatabase(context=_context(site_id, uuid4()), record=None)
    client, url = _preview_client(tmp_path, database)
    secret = b"\x01" * 32
    csrf = b"\x02" * 32
    response = client.get(url, cookies=_cookie(secret, csrf))
    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["cache-control"] == "private, no-store"
    # No session cookie: 401.
    assert client.get(url).status_code == 401
    # Malformed session credential: the unmodified media auth boundary
    # maps an unparseable token to 503 SERVICE_UNAVAILABLE (fail-closed,
    # never bytes) - pinned as pre-existing behavior of
    # media_service/auth.py, which R4 verifies but does not redesign.
    malformed = client.get(url, headers={"cookie": "slaif_session=sas2_bogus"})
    assert malformed.status_code == 503
    assert malformed.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert malformed.content != PNG
    # Revoked session / non-member / foreign site: authorize returns None
    # -> 404, never 403 and never bytes.
    denied = StubMediaDatabase(context=None, record=None)
    client2, url2 = _preview_client(tmp_path, denied)
    response = client2.get(url2, cookies=_cookie(secret, csrf))
    assert response.status_code == 404
    assert response.content != PNG
    # Direct .staging / artifact paths are not routable at all (the route
    # only accepts UUID media ids): a traversal-shaped id is rejected.
    assert client.get(
        f"/v1/sites/{site_id}/assets/..%2F.staging%2Ftmp/content"
    ).status_code in {404, 422}
    assert client.get("/v1/.staging/tmp").status_code == 404


# --- R5: bounded agent error keys ---------------------------------------


class StubAgentDatabase:
    def __init__(
        self,
        context: AgentCapabilityContext | None,
        *,
        request_allowed: bool = True,
    ) -> None:
        self._context = context
        self._request_allowed = request_allowed

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    def cow_pool(self) -> None:
        return None

    async def authenticate_agent_capability(
        self, _auth_header: str
    ) -> AgentCapabilityContext | None:
        return self._context

    async def consume_agent_quota(self, _context: Any, _kind: str) -> bool:
        return self._request_allowed


def _agent_context(*, scopes: frozenset[str]) -> AgentCapabilityContext:
    return AgentCapabilityContext(
        capability_id=uuid4(),
        site_id=uuid4(),
        workspace_id=uuid4(),
        delegator_id=uuid4(),
        scopes=scopes,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC).replace(minute=59, second=59),
        request_quota=10,
        mutation_quota=10,
        delete_quota=1,
        upload_quota=2,
    )


def _agent_settings() -> AgentDatabaseSettings:
    return AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr("postgresql://slaif_agent_login:unit@127.0.0.1:5432/slaif"),
        dsn_file=None,
        expected_database="slaif",
        expected_login="slaif_agent_login",
        dispatcher_enabled=False,
        application_name="agent-public-core-unit",
    )


def _agent_client(
    database: StubAgentDatabase, tmp_path: Path | None = None
) -> TestClient:
    app = create_agent_app(
        settings=ServiceSettings.for_test(),
        database_settings=_agent_settings(),
        database=database,
        browser_signer=None,
        browser_worker_client=None,
    )
    if tmp_path is not None:
        from slaif_agent_site.media_service.store import MediaStore

        app.state.media_store = MediaStore(tmp_path / "agent-media")
    return TestClient(app)


# The bearer-header gate runs before the stub capability lookup.
_AUTH = {"Authorization": "Bearer sas2_unit-test-token"}


def test_agent_upload_bounded_error_keys(tmp_path: Path) -> None:
    # Missing idempotency key: 400 with the exact bounded key.
    client = _agent_client(
        StubAgentDatabase(
            _agent_context(scopes=frozenset({"media:upload", "media:read"}))
        ),
        tmp_path,
    )
    response = client.post("/api/agent/v1/media/assets", headers=_AUTH)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"
    # Invalid key shape: 400.
    response = client.post(
        "/api/agent/v1/media/assets",
        headers={**_AUTH, "Idempotency-Key": "bad key!"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_INVALID"
    # Unknown capability (db lookup returns None): 401.
    denied = _agent_client(StubAgentDatabase(None), tmp_path)
    response = denied.post(
        "/api/agent/v1/media/assets",
        headers={**_AUTH, "Idempotency-Key": "k-1"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    # Authenticated capability without the media:upload scope: 403.
    no_scope = _agent_client(
        StubAgentDatabase(_agent_context(scopes=frozenset({"media:read"}))),
        tmp_path,
    )
    response = no_scope.post(
        "/api/agent/v1/media/assets",
        headers={**_AUTH, "Idempotency-Key": "k-1"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTHORIZATION_DENIED"
    # Store unavailable (no media_root wired): 503, after auth+scope pass.
    no_store = _agent_client(
        StubAgentDatabase(
            _agent_context(scopes=frozenset({"media:upload", "media:read"}))
        )
    )
    response = no_store.post(
        "/api/agent/v1/media/assets",
        headers={**_AUTH, "Idempotency-Key": "k-1"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_agent_media_read_requires_media_read_scope(tmp_path: Path) -> None:
    no_read = _agent_client(
        StubAgentDatabase(_agent_context(scopes=frozenset({"media:upload"}))),
        tmp_path,
    )
    response = no_read.get(
        f"/api/agent/v1/media/assets/{uuid4()}/content", headers=_AUTH
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTHORIZATION_DENIED"


def test_agent_upload_rejects_unsupported_mime(tmp_path: Path) -> None:
    client = _agent_client(
        StubAgentDatabase(
            _agent_context(scopes=frozenset({"media:upload", "media:read"}))
        ),
        tmp_path,
    )
    boundary = "b-test"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="x.svg"\r\n'
        "Content-Type: image/svg+xml\r\n\r\n"
        "<svg></svg>\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    response = client.post(
        "/api/agent/v1/media/assets",
        headers={
            **_AUTH,
            "Idempotency-Key": "k-svg",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        content=body,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DOMAIN_VALIDATION_FAILED"

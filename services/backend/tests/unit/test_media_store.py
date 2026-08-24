"""Pure local MediaStore and signature-boundary tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from slaif_agent_site.media_service.store import (
    MediaStore,
    MediaStoreError,
    StagedMedia,
    sniff_mime,
)

PNG = b"\x89PNG\r\n\x1a\nfixture"


def test_sniffer_requires_actual_supported_signature() -> None:
    assert sniff_mime(PNG, "image/png") == "image/png"
    assert sniff_mime(b"\xff\xd8\xfffixture", "image/jpeg") == "image/jpeg"
    with pytest.raises(MediaStoreError):
        sniff_mime(PNG, "image/jpeg")
    with pytest.raises(MediaStoreError):
        sniff_mime(b"<svg>", "image/svg+xml")


def test_store_publishes_digest_only_private_object_and_reuses_it(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media")
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    digest = hashlib.sha256(PNG).hexdigest()
    key = store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    assert key == f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
    object_path = store.object_path(key)
    assert object_path.read_bytes() == PNG
    assert object_path.stat().st_mode & 0o777 == 0o600
    assert not staging.exists()

    second = store.create_staging_path()
    second.write_bytes(PNG)
    assert store.publish(StagedMedia(second, digest, len(PNG), "image/png")) == key
    assert not second.exists()


def test_store_rejects_corrupt_existing_digest_without_overwrite(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media")
    digest = hashlib.sha256(PNG).hexdigest()
    key = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
    destination = store.object_path(key)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"x" * len(PNG))
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    assert destination.read_bytes() == b"x" * len(PNG)
    assert not staging.exists()

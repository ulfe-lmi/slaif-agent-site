"""Pure local MediaStore and signature-boundary tests."""

from __future__ import annotations

import hashlib
import os
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
    for directory in (
        store.root,
        store.root / "sha256",
        store.root / "sha256" / digest[:2],
        destination.parent,
    ):
        directory.chmod(0o700)
    destination.write_bytes(b"x" * len(PNG))
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    assert destination.read_bytes() == b"x" * len(PNG)
    assert not staging.exists()


@pytest.mark.parametrize("kind", ["sha256", "prefix", "final"])
def test_store_rejects_symlinked_digest_path_without_following(
    tmp_path: Path, kind: str
) -> None:
    store = MediaStore(tmp_path / "media")
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    digest = hashlib.sha256(PNG).hexdigest()
    root = store.root
    if kind == "sha256":
        (root / "outside").mkdir()
        (root / "sha256").symlink_to(root / "outside", target_is_directory=True)
    else:
        (root / "sha256").mkdir(mode=0o700)
        (root / "sha256").chmod(0o700)
        if kind == "prefix":
            (root / "sha256" / digest[:2]).symlink_to(root, target_is_directory=True)
        else:
            prefix = root / "sha256" / digest[:2]
            prefix.mkdir(mode=0o700)
            prefix.chmod(0o700)
            (prefix / digest[2:4]).mkdir(mode=0o700)
            (prefix / digest[2:4]).chmod(0o700)
            (prefix / digest[2:4] / digest).symlink_to(root / "missing")
    with pytest.raises(MediaStoreError):
        store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    assert not staging.exists()


@pytest.mark.parametrize("object_type", ["directory", "fifo"])
def test_store_rejects_non_regular_final_object(
    tmp_path: Path, object_type: str
) -> None:
    store = MediaStore(tmp_path / "media")
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    digest = hashlib.sha256(PNG).hexdigest()
    destination = store.object_path(f"sha256/{digest[:2]}/{digest[2:4]}/{digest}")
    destination.parent.mkdir(parents=True, mode=0o700)
    for directory in (
        store.root,
        store.root / "sha256",
        store.root / "sha256" / digest[:2],
        destination.parent,
    ):
        directory.chmod(0o700)
    if object_type == "directory":
        destination.mkdir(mode=0o700)
    else:
        os.mkfifo(destination, 0o600)
    with pytest.raises(MediaStoreError, match="storage_corrupt"):
        store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    assert not staging.exists()


def test_store_rejects_wrong_read_contract_and_closes_returned_descriptor(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media")
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    digest = hashlib.sha256(PNG).hexdigest()
    key = store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    with pytest.raises(MediaStoreError):
        store.open_verified(key, digest, len(PNG) + 1)
    with pytest.raises(MediaStoreError):
        store.open_verified("sha256/00/00/" + digest, digest, len(PNG))
    descriptor, size = store.open_verified(key, digest, len(PNG))
    assert size == len(PNG)
    assert os.read(descriptor, size) == PNG
    os.close(descriptor)
    with pytest.raises(OSError):
        os.fstat(descriptor)


@pytest.mark.asyncio
async def test_store_readiness_fails_closed_for_replaced_root(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir(mode=0o700)
    root.chmod(0o755)
    assert not await MediaStore(root).readiness()


def test_store_records_durable_publication_fsyncs(tmp_path: Path) -> None:
    events: list[str] = []

    def record(descriptor: int) -> None:
        events.append(os.readlink(f"/proc/self/fd/{descriptor}"))
        os.fsync(descriptor)

    store = MediaStore(tmp_path / "media", fsync=record)
    staging = store.create_staging_path()
    staging.write_bytes(PNG)
    digest = hashlib.sha256(PNG).hexdigest()
    store.publish(StagedMedia(staging, digest, len(PNG), "image/png"))
    assert len(events) >= 5
    assert any(".staging" in event for event in events)
    assert any(digest[2:4] in event for event in events)

"""Pure local MediaStore and signature-boundary tests."""

from __future__ import annotations

import hashlib
import os
import threading
import time
import zlib
from pathlib import Path

import pytest
from slaif_agent_site.media_service.pdf_policy import PDF_MAX_BYTES
from slaif_agent_site.media_service.store import (
    MediaStore,
    MediaStoreError,
    StagedMedia,
    sniff_mime,
)

PNG = b"\x89PNG\r\n\x1a\nfixture"


def make_pdf(pages: int, compress: bool = False) -> bytes:
    """Deterministic minimal PDF fixture with exactly ``pages`` page objects."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            b"<< /Type /Pages /Kids ["
            + b" ".join(f"{i} 0 R".encode() for i in range(3, 3 + pages))
            + b"] /Count "
            + str(pages).encode()
            + b" >>"
        ),
    ]
    for _ in range(pages):
        if compress:
            stream = zlib.compress(
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"
            )
            objects.append(
                b"<< /Filter /FlateDecode /Length "
                + str(len(stream)).encode()
                + b" >> stream\n"
                + stream
                + b"\nendstream"
            )
        else:
            objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>")
    out = bytearray(b"%PDF-1.4\n")
    for number, body in enumerate(objects, start=1):
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    out += b"%%EOF"
    return bytes(out)


def test_sniffer_requires_actual_supported_signature() -> None:
    assert sniff_mime(PNG, "image/png") == "image/png"
    assert sniff_mime(b"\xff\xd8\xfffixture", "image/jpeg") == "image/jpeg"
    assert sniff_mime(b"%PDF-1.4", "application/pdf") == "application/pdf"
    with pytest.raises(MediaStoreError, match="media_signature_mismatch"):
        sniff_mime(PNG, "image/jpeg")
    with pytest.raises(MediaStoreError, match="unsupported_media"):
        sniff_mime(b"<svg>", "image/svg+xml")
    with pytest.raises(MediaStoreError, match="media_signature_mismatch"):
        sniff_mime(b"PK\x03\x04", "application/pdf")


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


def test_independent_store_instances_serialize_winner_in_progress(
    tmp_path: Path,
) -> None:
    root = tmp_path / "media"
    digest = hashlib.sha256(PNG).hexdigest()
    other = b"\x89PNG\r\n\x1a\nother-digest"
    other_digest = hashlib.sha256(other).hexdigest()
    assert digest[:4] != other_digest[:4]
    store_a = MediaStore(root)
    store_b = MediaStore(root)
    stage_a = store_a.create_staging_path()
    stage_a.write_bytes(PNG)
    stage_b = store_b.create_staging_path()
    stage_b.write_bytes(PNG)
    other_store = MediaStore(root)
    other_stage = other_store.create_staging_path()
    other_stage.write_bytes(other)
    key = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
    linked = threading.Event()
    release = threading.Event()
    results: dict[str, str] = {}
    errors: list[BaseException] = []

    def fsync_a(descriptor: int) -> None:
        os.fsync(descriptor)
        if store_a.object_path(key).exists() and stage_a.exists():
            linked.set()
            if not release.wait(3):
                raise OSError("test winner pause timed out")

    def publish_a() -> None:
        try:
            results["a"] = store_a.publish(
                StagedMedia(stage_a, digest, len(PNG), "image/png")
            )
        except BaseException as error:
            errors.append(error)

    def publish_b() -> None:
        try:
            results["b"] = store_b.publish(
                StagedMedia(stage_b, digest, len(PNG), "image/png")
            )
        except BaseException as error:
            errors.append(error)

    store_a._fsync = fsync_a
    first = threading.Thread(target=publish_a)
    second = threading.Thread(target=publish_b)
    first.start()
    assert linked.wait(3)
    second.start()
    time.sleep(0.05)
    assert second.is_alive()

    other_result: list[str] = []

    def publish_other() -> None:
        other_result.append(
            other_store.publish(
                StagedMedia(other_stage, other_digest, len(other), "image/png")
            )
        )

    unrelated = threading.Thread(target=publish_other)
    unrelated.start()
    unrelated.join(2)
    assert not unrelated.is_alive()
    release.set()
    first.join(3)
    second.join(3)
    assert not first.is_alive() and not second.is_alive()
    assert errors == []
    assert results == {"a": key, "b": key}
    assert other_result == [
        f"sha256/{other_digest[:2]}/{other_digest[2:4]}/{other_digest}"
    ]
    assert store_a.object_path(key).read_bytes() == PNG
    assert store_a.object_path(key).stat().st_nlink == 1
    assert not stage_a.exists() and not stage_b.exists() and not other_stage.exists()


def test_store_lock_timeout_is_bounded_and_cleans_only_loser_stage(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media", lock_timeout_seconds=0.05)
    stage = store.create_staging_path()
    stage.write_bytes(PNG)
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
    holder = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    import fcntl

    fcntl.flock(holder, fcntl.LOCK_EX)
    started = time.monotonic()
    try:
        with pytest.raises(MediaStoreError, match="storage_unavailable"):
            store.publish(StagedMedia(stage, digest, len(PNG), "image/png"))
    finally:
        fcntl.flock(holder, fcntl.LOCK_UN)
        os.close(holder)
    assert time.monotonic() - started < 1
    assert not stage.exists()


def test_staging_writer_rejects_replaced_path_without_following(
    tmp_path: Path,
) -> None:
    store = MediaStore(tmp_path / "media")
    staged_file = store.create_staging_writer()
    staged_file.stream.write(PNG)
    staged_file.stream.flush()
    staged_file.path.unlink()
    staged_file.path.symlink_to(store.root / "outside")
    digest = hashlib.sha256(PNG).hexdigest()
    staged = StagedMedia(
        staged_file.path,
        digest,
        len(PNG),
        "image/png",
        stream=staged_file.stream,
    )
    with pytest.raises(MediaStoreError):
        store.publish(staged)
    assert not store.object_path(f"sha256/{digest[:2]}/{digest[2:4]}/{digest}").exists()


# --------------------------------------------------------------------- 079/3
# Bounded document-class (PDF) policy at the shared store enforcement point:
# every rejection happens before any staging publish and discards the stage.


def test_store_accepts_one_page_pdf(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = make_pdf(1)
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    key = store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert key == f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
    assert store.object_path(key).read_bytes() == document
    assert not staging.exists()


def test_store_accepts_exactly_200_page_pdf(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = make_pdf(200)
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    key = store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert key.startswith("sha256/")
    assert not staging.exists()


def test_store_accepts_flate_compressed_page_objects(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = make_pdf(4, compress=True)
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    key = store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert key.startswith("sha256/")
    assert not staging.exists()


def test_store_publishes_pdf_from_an_unflushed_staging_writer(tmp_path: Path) -> None:
    # The HTTP upload path (parse_upload) hands publish() the still-buffered
    # staging writer; the bounded PDF policy must observe the complete bytes
    # and publish normally (regression for the 079-3-a E2E 503).
    store = MediaStore(tmp_path / "media")
    document = make_pdf(2)
    staged_file = store.create_staging_writer()
    staged_file.stream.write(document)
    # Deliberately NOT flushed: publish must flush before policy enforcement.
    digest = hashlib.sha256(document).hexdigest()
    staged = StagedMedia(
        staged_file.path,
        digest,
        len(document),
        "application/pdf",
        stream=staged_file.stream,
    )
    key = store.publish(staged)
    assert key.startswith("sha256/")
    assert not staged_file.path.exists()
    assert (store.root / key).read_bytes() == document


def test_store_rejects_pdf_from_an_unflushed_staging_writer(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = make_pdf(201)
    staged_file = store.create_staging_writer()
    staged_file.stream.write(document)
    digest = hashlib.sha256(document).hexdigest()
    staged = StagedMedia(
        staged_file.path,
        digest,
        len(document),
        "application/pdf",
        stream=staged_file.stream,
    )
    with pytest.raises(MediaStoreError, match="media-pdf-too-many-pages"):
        store.publish(staged)
    assert not staged_file.path.exists()
    assert not (store.root / "sha256").exists()


def test_store_rejects_201_page_pdf_before_publish(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = make_pdf(201)
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    with pytest.raises(MediaStoreError, match="media-pdf-too-many-pages"):
        store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert not staging.exists()
    assert not (store.root / "sha256").exists()


def test_store_rejects_pdf_above_20_mib_before_publish(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = make_pdf(1) + b"0" * 1024  # under the generic 100 MiB limit
    oversized = len(document) + PDF_MAX_BYTES
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    with pytest.raises(MediaStoreError, match="media-pdf-too-large"):
        store.publish(StagedMedia(staging, digest, oversized, "application/pdf"))
    assert not staging.exists()
    assert not (store.root / "sha256").exists()


def test_store_rejects_undetermined_pdf_structure(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    document = b"%PDF-1.4\nno page objects\n%%EOF"
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    with pytest.raises(MediaStoreError, match="media-pdf-structure-invalid"):
        store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert not staging.exists()
    assert not (store.root / "sha256").exists()


def test_store_rejects_pdf_decompression_bomb(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media")
    bomb_stream = zlib.compress(b" " * (50 * 1024 * 1024 + 1))
    document = (
        b"%PDF-1.4\n1 0 obj\n<< /Filter /FlateDecode /Length "
        + str(len(bomb_stream)).encode()
        + b" >> stream\n"
        + bomb_stream
        + b"\nendstream\n%%EOF"
    )
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    with pytest.raises(MediaStoreError, match="media-pdf-structure-invalid"):
        store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert not staging.exists()
    assert not (store.root / "sha256").exists()


def test_pdf_bounds_are_independent_of_generic_upload_limit(tmp_path: Path) -> None:
    store = MediaStore(tmp_path / "media", max_upload_bytes=PDF_MAX_BYTES + 1)
    document = make_pdf(1)
    staging = store.create_staging_path()
    staging.write_bytes(document)
    digest = hashlib.sha256(document).hexdigest()
    key = store.publish(StagedMedia(staging, digest, len(document), "application/pdf"))
    assert key.startswith("sha256/")
    assert not staging.exists()

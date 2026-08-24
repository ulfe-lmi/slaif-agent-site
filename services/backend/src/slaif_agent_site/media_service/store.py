"""Private immutable local content-addressed media storage."""

from __future__ import annotations

import asyncio
import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path


class MediaStoreError(RuntimeError):
    """Stable media-store failure without filesystem details."""


@dataclass(frozen=True, slots=True)
class StagedMedia:
    staging_path: Path
    digest: str
    size_bytes: int
    mime_type: str


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8\xff"
SUPPORTED_MIME = frozenset({"image/png", "image/jpeg"})


def sniff_mime(prefix: bytes, declared: str) -> str:
    if declared not in SUPPORTED_MIME:
        raise MediaStoreError("unsupported_media")
    if declared == "image/png" and prefix.startswith(PNG_SIGNATURE):
        return declared
    if declared == "image/jpeg" and prefix.startswith(JPEG_SIGNATURE):
        return declared
    raise MediaStoreError("media_signature_mismatch")


class MediaStore:
    """Filesystem boundary with digest-only object keys and private staging."""

    def __init__(
        self, root: Path, *, max_upload_bytes: int = 100 * 1024 * 1024
    ) -> None:
        if not root.is_absolute() or max_upload_bytes < 1:
            raise ValueError("invalid media store configuration")
        self.root = root
        self.max_upload_bytes = max_upload_bytes
        self.staging_root = root / ".staging"

    def _ensure_directory(self, path: Path) -> None:
        try:
            if path.exists() and path.is_symlink():
                raise MediaStoreError("storage_unavailable")
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
            info = path.stat(follow_symlinks=False)
            if not stat.S_ISDIR(info.st_mode):
                raise MediaStoreError("storage_unavailable")
            os.chmod(path, 0o700)
        except (OSError, MediaStoreError):
            raise MediaStoreError("storage_unavailable") from None

    async def readiness(self) -> bool:
        try:
            await asyncio.to_thread(self._ensure_directory, self.root)
            await asyncio.to_thread(self._ensure_directory, self.staging_root)
            probe = self.staging_root / ".readiness"
            await asyncio.to_thread(probe.touch, mode=0o600, exist_ok=False)
            await asyncio.to_thread(probe.unlink)
            return True
        except (OSError, MediaStoreError):
            return False

    def create_staging_path(self) -> Path:
        self._ensure_directory(self.root)
        self._ensure_directory(self.staging_root)
        try:
            descriptor, name = None, ""
            while descriptor is None:
                candidate = self.staging_root / f"upload-{os.urandom(16).hex()}.part"
                try:
                    descriptor = os.open(
                        candidate,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                    )
                    name = str(candidate)
                except FileExistsError:
                    continue
            os.close(descriptor)
            return Path(name)
        except OSError:
            raise MediaStoreError("storage_unavailable") from None

    def remove_staging(self, path: Path) -> None:
        try:
            if path.parent != self.staging_root or path.is_symlink():
                return
            path.unlink(missing_ok=True)
        except OSError:
            return

    def publish(self, staged: StagedMedia) -> str:
        digest = staged.digest
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise MediaStoreError("storage_unavailable")
        key = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        destination = self.root / key
        self._ensure_directory(destination.parent)
        try:
            existing = destination.lstat() if destination.exists() else None
            if existing is not None:
                if not stat.S_ISREG(existing.st_mode) or destination.is_symlink():
                    raise MediaStoreError("storage_corrupt")
                if existing.st_size != staged.size_bytes:
                    raise MediaStoreError("storage_corrupt")
                if self._digest_file(destination) != digest:
                    raise MediaStoreError("storage_corrupt")
                self.remove_staging(staged.staging_path)
                return key
            os.link(staged.staging_path, destination, follow_symlinks=False)
            os.chmod(destination, 0o600)
            self.remove_staging(staged.staging_path)
            return key
        except FileExistsError:
            return self.publish(staged)
        except MediaStoreError:
            self.remove_staging(staged.staging_path)
            raise
        except OSError:
            self.remove_staging(staged.staging_path)
            raise MediaStoreError("storage_unavailable") from None

    @staticmethod
    def _digest_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def open_verified(self, key: str, digest: str, size_bytes: int) -> tuple[int, int]:
        expected = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        if key != expected:
            raise MediaStoreError("storage_corrupt")
        path = self.root / key
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_size != size_bytes:
                os.close(descriptor)
                raise MediaStoreError("storage_corrupt")
            digest_check = hashlib.sha256()
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                digest_check.update(chunk)
            if digest_check.hexdigest() != digest:
                os.close(descriptor)
                raise MediaStoreError("storage_corrupt")
            os.lseek(descriptor, 0, os.SEEK_SET)
            return descriptor, info.st_size
        except MediaStoreError:
            raise
        except OSError:
            raise MediaStoreError("media_missing") from None

    def object_path(self, key: str) -> Path:
        """Return only for test/operator inspection; callers never expose it."""

        return self.root / key


__all__ = [
    "JPEG_SIGNATURE",
    "MediaStore",
    "MediaStoreError",
    "PNG_SIGNATURE",
    "SUPPORTED_MIME",
    "StagedMedia",
    "sniff_mime",
]

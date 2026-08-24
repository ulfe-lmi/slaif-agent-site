"""Private immutable local content-addressed media storage."""

from __future__ import annotations

import asyncio
import errno
import hashlib
import os
import stat
from collections.abc import Callable
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
_PRIVATE_MODE = 0o700
_OBJECT_MODE = 0o600
_OPEN_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def sniff_mime(prefix: bytes, declared: str) -> str:
    if declared not in SUPPORTED_MIME:
        raise MediaStoreError("unsupported_media")
    if declared == "image/png" and prefix.startswith(PNG_SIGNATURE):
        return declared
    if declared == "image/jpeg" and prefix.startswith(JPEG_SIGNATURE):
        return declared
    raise MediaStoreError("media_signature_mismatch")


class MediaStore:
    """Descriptor-confined filesystem boundary for immutable media objects."""

    def __init__(
        self,
        root: Path,
        *,
        max_upload_bytes: int = 100 * 1024 * 1024,
        fsync: Callable[[int], None] = os.fsync,
    ) -> None:
        if not root.is_absolute() or max_upload_bytes < 1:
            raise ValueError("invalid media store configuration")
        self.root = root
        self.max_upload_bytes = max_upload_bytes
        self.staging_root = root / ".staging"
        self._fsync = fsync

    @staticmethod
    def _check_directory(descriptor: int) -> None:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(info.st_mode)
            or stat.S_IMODE(info.st_mode) != _PRIVATE_MODE
            or info.st_uid != os.geteuid()
        ):
            raise MediaStoreError("storage_unavailable")

    def _open_root(self, *, create: bool) -> int:
        if create:
            try:
                self.root.mkdir(mode=_PRIVATE_MODE, parents=True, exist_ok=True)
            except OSError:
                raise MediaStoreError("storage_unavailable") from None
        try:
            descriptor = os.open(self.root, _OPEN_DIRECTORY)
        except OSError:
            raise MediaStoreError("storage_unavailable") from None
        try:
            self._check_directory(descriptor)
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def _open_child_directory(self, parent: int, name: str, *, create: bool) -> int:
        if not name or name in {".", ".."} or "/" in name or "\\" in name:
            raise MediaStoreError("storage_unavailable")
        created = False
        if create:
            try:
                os.mkdir(name, _PRIVATE_MODE, dir_fd=parent)
                created = True
            except FileExistsError:
                pass
            except OSError:
                raise MediaStoreError("storage_unavailable") from None
        try:
            descriptor = os.open(name, _OPEN_DIRECTORY, dir_fd=parent)
        except OSError as error:
            if not create and error.errno == errno.ENOENT:
                raise MediaStoreError("media_missing") from None
            if not create and error.errno in {errno.ELOOP, errno.ENOTDIR}:
                raise MediaStoreError("storage_corrupt") from None
            raise MediaStoreError("storage_unavailable") from None
        try:
            self._check_directory(descriptor)
            if created:
                self._sync(parent)
            return descriptor
        except MediaStoreError as error:
            os.close(descriptor)
            if not create:
                raise MediaStoreError("storage_corrupt") from None
            raise error
        except BaseException:
            os.close(descriptor)
            raise

    def _open_staging_directory(self, root: int) -> int:
        return self._open_child_directory(root, ".staging", create=True)

    def _open_object_directory(self, root: int, digest: str, *, create: bool) -> int:
        sha_directory = self._open_child_directory(root, "sha256", create=create)
        try:
            prefix_one = self._open_child_directory(
                sha_directory, digest[:2], create=create
            )
        finally:
            os.close(sha_directory)
        try:
            return self._open_child_directory(prefix_one, digest[2:4], create=create)
        finally:
            os.close(prefix_one)

    def _sync(self, descriptor: int) -> None:
        try:
            self._fsync(descriptor)
        except OSError:
            raise MediaStoreError("storage_unavailable") from None

    @staticmethod
    def _validate_digest(digest: str) -> None:
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise MediaStoreError("storage_unavailable")

    @staticmethod
    def _validate_staging_path(path: Path, staging_root: Path) -> str:
        if path.parent != staging_root or path.name in {"", ".", ".."}:
            raise MediaStoreError("storage_unavailable")
        if "/" in path.name or "\\" in path.name:
            raise MediaStoreError("storage_unavailable")
        return path.name

    @staticmethod
    def _verify_object(directory: int, name: str, digest: str, size_bytes: int) -> None:
        try:
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
        except OSError:
            raise MediaStoreError("storage_corrupt") from None
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != _OBJECT_MODE
            or info.st_size != size_bytes
        ):
            raise MediaStoreError("storage_corrupt")
        descriptor = -1
        try:
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            actual = MediaStore._digest_descriptor(descriptor)
        except OSError:
            raise MediaStoreError("storage_corrupt") from None
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if actual != digest:
            raise MediaStoreError("storage_corrupt")

    @staticmethod
    def _digest_descriptor(descriptor: int) -> str:
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)

    async def readiness(self) -> bool:
        root = -1
        staging = -1
        try:
            root = await asyncio.to_thread(self._open_root, create=True)
            staging = await asyncio.to_thread(self._open_staging_directory, root)
            await asyncio.to_thread(self._sync, staging)
            return True
        except (OSError, MediaStoreError):
            return False
        finally:
            if staging >= 0:
                os.close(staging)
            if root >= 0:
                os.close(root)

    def create_staging_path(self) -> Path:
        root = -1
        staging = -1
        descriptor = -1
        try:
            root = self._open_root(create=True)
            staging = self._open_staging_directory(root)
            for _ in range(8):
                name = f"upload-{os.urandom(16).hex()}.part"
                try:
                    descriptor = os.open(
                        name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        _OBJECT_MODE,
                        dir_fd=staging,
                    )
                    return self.staging_root / name
                except FileExistsError:
                    continue
            raise MediaStoreError("storage_unavailable")
        except OSError:
            raise MediaStoreError("storage_unavailable") from None
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if staging >= 0:
                os.close(staging)
            if root >= 0:
                os.close(root)

    def remove_staging(self, path: Path) -> None:
        root = -1
        staging = -1
        try:
            name = self._validate_staging_path(path, self.staging_root)
            root = self._open_root(create=False)
            staging = self._open_staging_directory(root)
            try:
                os.unlink(name, dir_fd=staging)
            except FileNotFoundError:
                return
            self._sync(staging)
        except (OSError, MediaStoreError):
            return
        finally:
            if staging >= 0:
                os.close(staging)
            if root >= 0:
                os.close(root)

    def publish(self, staged: StagedMedia) -> str:
        digest = staged.digest
        self._validate_digest(digest)
        staging_name = self._validate_staging_path(
            staged.staging_path, self.staging_root
        )
        key = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        root = -1
        staging = -1
        objects = -1
        stage_descriptor = -1
        try:
            root = self._open_root(create=False)
            staging = self._open_staging_directory(root)
            objects = self._open_object_directory(root, digest, create=True)
            stage_descriptor = os.open(
                staging_name,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=staging,
            )
            stage_info = os.fstat(stage_descriptor)
            if (
                not stat.S_ISREG(stage_info.st_mode)
                or stage_info.st_nlink != 1
                or stat.S_IMODE(stage_info.st_mode) != _OBJECT_MODE
                or stage_info.st_size != staged.size_bytes
            ):
                raise MediaStoreError("storage_corrupt")
            if self._digest_descriptor(stage_descriptor) != digest:
                raise MediaStoreError("storage_corrupt")
            os.lseek(stage_descriptor, 0, os.SEEK_SET)
            self._sync(stage_descriptor)

            for _ in range(2):
                try:
                    try:
                        os.stat(digest, dir_fd=objects, follow_symlinks=False)
                    except FileNotFoundError:
                        pass
                    else:
                        self._verify_object(objects, digest, digest, staged.size_bytes)
                        os.unlink(staging_name, dir_fd=staging)
                        self._sync(staging)
                        return key
                    os.link(
                        staging_name,
                        digest,
                        src_dir_fd=staging,
                        dst_dir_fd=objects,
                        follow_symlinks=False,
                    )
                    object_descriptor = os.open(
                        digest,
                        os.O_RDONLY | os.O_NOFOLLOW,
                        dir_fd=objects,
                    )
                    try:
                        os.fchmod(object_descriptor, _OBJECT_MODE)
                        self._sync(object_descriptor)
                    finally:
                        os.close(object_descriptor)
                    self._sync(objects)
                    os.unlink(staging_name, dir_fd=staging)
                    self._sync(staging)
                    return key
                except FileExistsError:
                    self._verify_object(objects, digest, digest, staged.size_bytes)
                    os.unlink(staging_name, dir_fd=staging)
                    self._sync(staging)
                    return key
            raise MediaStoreError("storage_unavailable")
        except MediaStoreError:
            self.remove_staging(staged.staging_path)
            raise
        except OSError:
            self.remove_staging(staged.staging_path)
            raise MediaStoreError("storage_unavailable") from None
        finally:
            if stage_descriptor >= 0:
                os.close(stage_descriptor)
            if objects >= 0:
                os.close(objects)
            if staging >= 0:
                os.close(staging)
            if root >= 0:
                os.close(root)

    def open_verified(self, key: str, digest: str, size_bytes: int) -> tuple[int, int]:
        self._validate_digest(digest)
        expected = f"sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        if key != expected or size_bytes < 1:
            raise MediaStoreError("storage_corrupt")
        root = -1
        objects = -1
        descriptor = -1
        try:
            root = self._open_root(create=False)
            objects = self._open_object_directory(root, digest, create=False)
            descriptor = os.open(
                digest,
                os.O_RDONLY | os.O_NOFOLLOW,
                dir_fd=objects,
            )
            info = os.fstat(descriptor)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != _OBJECT_MODE
                or info.st_size != size_bytes
            ):
                raise MediaStoreError("storage_corrupt")
            if self._digest_descriptor(descriptor) != digest:
                raise MediaStoreError("storage_corrupt")
            os.lseek(descriptor, 0, os.SEEK_SET)
            result = descriptor, info.st_size
            descriptor = -1
            return result
        except MediaStoreError:
            raise
        except OSError:
            raise MediaStoreError("media_missing") from None
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if objects >= 0:
                os.close(objects)
            if root >= 0:
                os.close(root)

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

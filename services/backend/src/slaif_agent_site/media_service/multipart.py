"""Bounded streaming multipart upload parsing for the Media service."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, BinaryIO

from fastapi import Request

from .store import MediaStore, MediaStoreError, StagedMedia, sniff_mime


class MultipartUploadError(ValueError):
    """A bounded, safe multipart request failure."""


@dataclass(frozen=True, slots=True)
class ParsedUpload:
    staged: StagedMedia
    filename: str
    alt_text: str
    metadata: dict[str, Any]


_BOUNDARY = re.compile(r"(?:^|;)\s*boundary=(?:\"([^\"]+)\"|([^;\s]+))")
_DISPOSITION = re.compile(r'(?:^|;)\s*name="([^"]+)"')
_FILENAME = re.compile(r'(?:^|;)\s*filename="([^"]*)"')
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _header_value(headers: list[bytes], name: str) -> str:
    if len(headers) != 1:
        raise MultipartUploadError("malformed_multipart")
    try:
        return headers[0].decode("ascii")
    except UnicodeDecodeError:
        raise MultipartUploadError("malformed_multipart") from None


def _filename(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).strip()
    if (
        not normalized
        or len(normalized) > 255
        or "/" in normalized
        or "\\" in normalized
        or ".." in normalized
        or _CONTROL.search(normalized)
    ):
        raise MultipartUploadError("invalid_filename")
    return normalized


def _bounded_json(value: Any, depth: int = 8) -> Any:
    if depth < 0:
        raise MultipartUploadError("invalid_metadata")
    if isinstance(value, dict):
        if len(value) > 64:
            raise MultipartUploadError("invalid_metadata")
        return {str(key): _bounded_json(item, depth - 1) for key, item in value.items()}
    if isinstance(value, list):
        if len(value) > 128:
            raise MultipartUploadError("invalid_metadata")
        return [_bounded_json(item, depth - 1) for item in value]
    if isinstance(value, str) and len(value) > 4096:
        raise MultipartUploadError("invalid_metadata")
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise MultipartUploadError("invalid_metadata")


async def parse_upload(request: Request, store: MediaStore) -> ParsedUpload:
    raw_content_type = request.headers.get("content-type", "")
    if not raw_content_type.lower().startswith("multipart/form-data"):
        raise MultipartUploadError("multipart_required")
    boundary_match = _BOUNDARY.search(raw_content_type)
    if boundary_match is None:
        raise MultipartUploadError("malformed_multipart")
    boundary = (boundary_match.group(1) or boundary_match.group(2)).encode("ascii")
    if not 1 <= len(boundary) <= 70 or any(
        byte < 33 or byte > 126 for byte in boundary
    ):
        raise MultipartUploadError("malformed_multipart")

    content_length = request.headers.get("content-length")
    max_request = store.max_upload_bytes + 256 * 1024
    if content_length is not None:
        try:
            if int(content_length) > max_request:
                raise MultipartUploadError("upload_too_large")
        except ValueError:
            raise MultipartUploadError("malformed_multipart") from None

    staging_path = store.create_staging_path()
    buffer = bytearray()
    marker = b"\r\n--" + boundary
    opening = b"--" + boundary + b"\r\n"
    final = b"--" + boundary + b"--"
    started = False
    finished = False
    total = 0
    current: dict[str, Any] | None = None
    fields: dict[str, str] = {}
    file_name: str | None = None
    file_declared: str | None = None
    file_digest = hashlib.sha256()
    file_size = 0
    file_prefix = bytearray()
    file_stream: BinaryIO | None = None
    headers_pending = True

    def finish_part() -> None:
        nonlocal current, file_stream, file_name, file_declared
        if current is None:
            return
        if current["filename"] is not None:
            if file_stream is None or file_name is not None:
                raise MultipartUploadError("duplicate_file")
            file_name = _filename(current["filename"])
            file_declared = current["content_type"]
            file_stream.close()
            file_stream = None
        else:
            value = bytes(current["value"])
            try:
                decoded = value.decode("utf-8")
            except UnicodeDecodeError:
                raise MultipartUploadError("malformed_multipart") from None
            name = current["name"]
            if name not in {"alt_text", "metadata"} or name in fields:
                raise MultipartUploadError("unexpected_field")
            if len(decoded) > 16384:
                raise MultipartUploadError("field_too_large")
            fields[name] = decoded
        current = None

    def emit(data: bytes) -> None:
        nonlocal file_size
        if current is None:
            raise MultipartUploadError("malformed_multipart")
        if current["filename"] is not None:
            file_size += len(data)
            if file_size > store.max_upload_bytes:
                raise MultipartUploadError("upload_too_large")
            file_digest.update(data)
            if len(file_prefix) < 64:
                file_prefix.extend(data[: 64 - len(file_prefix)])
            if file_stream is None:
                raise MultipartUploadError("malformed_multipart")
            file_stream.write(data)
        else:
            current["value"].extend(data)

    try:
        async for chunk in request.stream():
            if not isinstance(chunk, bytes):
                raise MultipartUploadError("malformed_multipart")
            total += len(chunk)
            if total > max_request:
                raise MultipartUploadError("upload_too_large")
            buffer.extend(chunk)
            while buffer:
                if finished:
                    break
                if current is None:
                    if not started:
                        if len(buffer) < len(opening) and opening.startswith(buffer):
                            break
                        if not buffer.startswith(opening):
                            raise MultipartUploadError("malformed_multipart")
                        del buffer[: len(opening)]
                        started = True
                    elif not headers_pending:
                        if len(buffer) < len(final) and final.startswith(buffer):
                            break
                        if not buffer.startswith(final):
                            raise MultipartUploadError("malformed_multipart")
                        del buffer[: len(final)]
                        if buffer.startswith(b"\r\n"):
                            del buffer[:2]
                        finished = True
                        break
                    if not headers_pending and not buffer.startswith(b"\r\n"):
                        break

                    header_end = buffer.find(b"\r\n\r\n")
                    if header_end < 0:
                        if len(buffer) > 16384:
                            raise MultipartUploadError("headers_too_large")
                        break
                    header_lines = bytes(buffer[:header_end]).split(b"\r\n")
                    del buffer[: header_end + 4]
                    parsed: dict[str, str] = {}
                    for line in header_lines:
                        if b":" not in line:
                            raise MultipartUploadError("malformed_multipart")
                        name, value = line.split(b":", 1)
                        try:
                            key = name.decode("ascii").lower()
                            text = value.decode("ascii").strip()
                        except UnicodeDecodeError:
                            raise MultipartUploadError("malformed_multipart") from None
                        parsed[key] = text
                    disposition = parsed.get("content-disposition", "")
                    name_match = _DISPOSITION.search(disposition)
                    if name_match is None:
                        raise MultipartUploadError("malformed_multipart")
                    filename_match = _FILENAME.search(disposition)
                    filename = filename_match.group(1) if filename_match else None
                    if filename is not None:
                        if file_stream is not None or file_name is not None:
                            raise MultipartUploadError("duplicate_file")
                        file_stream = staging_path.open("wb")
                    current = {
                        "name": name_match.group(1),
                        "filename": filename,
                        "content_type": parsed.get("content-type", ""),
                        "value": bytearray(),
                    }
                    headers_pending = False
                else:
                    boundary_index = buffer.find(marker)
                    if boundary_index < 0:
                        safe = max(0, len(buffer) - len(marker))
                        if safe:
                            emit(bytes(buffer[:safe]))
                            del buffer[:safe]
                        break
                    emit(bytes(buffer[:boundary_index]))
                    del buffer[: boundary_index + len(marker)]
                    if buffer.startswith(b"--"):
                        del buffer[:2]
                        finished = True
                        finish_part()
                        break
                    if not buffer.startswith(b"\r\n"):
                        raise MultipartUploadError("malformed_multipart")
                    del buffer[:2]
                    headers_pending = True
                    finish_part()
        if (
            not finished
            or current is not None
            or file_name is None
            or file_stream is not None
        ):
            raise MultipartUploadError("malformed_multipart")
        try:
            alt_text = fields.get("alt_text", "")
            if len(alt_text) > 512 or _CONTROL.search(alt_text):
                raise MultipartUploadError("invalid_alt_text")
            metadata_raw = fields.get("metadata", "{}")
            metadata = _bounded_json(json.loads(metadata_raw))
            if not isinstance(metadata, dict):
                raise MultipartUploadError("invalid_metadata")
        except json.JSONDecodeError:
            raise MultipartUploadError("invalid_metadata") from None
        declared = file_declared or ""
        mime_type = sniff_mime(bytes(file_prefix), declared)
        return ParsedUpload(
            staged=StagedMedia(
                staging_path=staging_path,
                digest=file_digest.hexdigest(),
                size_bytes=file_size,
                mime_type=mime_type,
            ),
            filename=file_name,
            alt_text=alt_text,
            metadata=metadata,
        )
    except (MultipartUploadError, MediaStoreError):
        if file_stream is not None:
            file_stream.close()
        store.remove_staging(staging_path)
        raise
    except Exception:
        if file_stream is not None:
            file_stream.close()
        store.remove_staging(staging_path)
        raise MultipartUploadError("malformed_multipart") from None


__all__ = ["MultipartUploadError", "ParsedUpload", "parse_upload"]

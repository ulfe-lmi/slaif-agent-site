"""Human-authenticated private immutable media HTTP surface."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, StreamingResponse

from slaif_agent_site.errors import (
    DomainValidationError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    RequestTooLargeError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)

from .auth import authorize_media_request
from .database import MediaDatabase, MediaIdempotencyMismatchError, record_to_dict
from .multipart import MultipartUploadError, parse_upload
from .store import MediaStore, MediaStoreError

router = APIRouter(prefix="/v1")
_KEY = re.compile(r"^[A-Za-z0-9._~-]{1,128}$")


def _key(request: Request) -> str:
    value = request.headers.get("Idempotency-Key")
    if value is None:
        raise IdempotencyKeyRequiredError()
    if _KEY.fullmatch(value) is None:
        raise IdempotencyKeyInvalidError()
    return value


def _digest(request: Request, key: str, parsed: Any) -> str:
    payload = {
        "method": request.method,
        "path": request.url.path,
        "key": key,
        "digest": parsed.staged.digest,
        "filename": parsed.filename,
        "mime_type": parsed.staged.mime_type,
        "size_bytes": parsed.staged.size_bytes,
        "alt_text": parsed.alt_text,
        "metadata": parsed.metadata,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _database(request: Request) -> MediaDatabase:
    return cast(MediaDatabase, request.app.state.media_database)


def _store(request: Request) -> MediaStore:
    return cast(MediaStore, request.app.state.media_store)


@router.post("/sites/{site_id}/assets", status_code=201)
async def upload_asset(site_id: UUID, request: Request) -> JSONResponse:
    context = await authorize_media_request(
        request,
        _database(request),
        request.app.state.settings,
        site_id,
        "media:upload",
        state_changing=True,
    )
    key = _key(request)
    try:
        parsed = await parse_upload(request, _store(request))
        storage_key = _store(request).publish(parsed.staged)
        record, operation_id, replay = await _database(request).register(
            context=context,
            idempotency_key=key,
            request_digest=_digest(request, key, parsed),
            filename=parsed.filename,
            mime_type=parsed.staged.mime_type,
            size_bytes=parsed.staged.size_bytes,
            content_hash=parsed.staged.digest,
            storage_key=storage_key,
            alt_text=parsed.alt_text,
            metadata=parsed.metadata,
        )
        return JSONResponse(
            {"record": record_to_dict(record), "operation_id": str(operation_id)},
            status_code=201,
            headers={"X-Media-Replay": "true" if replay else "false"},
        )
    except MultipartUploadError as error:
        if error.args[0] == "upload_too_large":
            raise RequestTooLargeError() from None
        raise DomainValidationError() from None
    except MediaStoreError as error:
        if error.args[0] in {"unsupported_media", "media_signature_mismatch"}:
            raise DomainValidationError() from None
        raise ServiceUnavailableError() from None
    except MediaIdempotencyMismatchError:
        raise IdempotencyMismatchError() from None
    except IdempotencyKeyRequiredError:
        raise
    except IdempotencyKeyInvalidError:
        raise
    except ResourceConflictError:
        raise
    except Exception:
        raise ServiceUnavailableError() from None


@router.get("/sites/{site_id}/assets/{media_id}/content")
async def get_asset_content(
    site_id: UUID, media_id: UUID, request: Request
) -> StreamingResponse:
    context = await authorize_media_request(
        request,
        _database(request),
        request.app.state.settings,
        site_id,
        "media:read",
        state_changing=False,
    )
    try:
        record = await _database(request).get(context=context, media_id=media_id)
        if record is None:
            raise ResourceNotFoundError()
        descriptor, size = _store(request).open_verified(
            record.storage_key, record.content_hash, record.size_bytes
        )
    except ResourceNotFoundError:
        raise
    except MediaStoreError as error:
        if error.args[0] in {"media_missing", "storage_corrupt"}:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    except Exception:
        raise ServiceUnavailableError() from None

    async def body() -> AsyncIterator[bytes]:
        try:
            while True:
                chunk = await __import__("asyncio").to_thread(
                    os.read, descriptor, 1024 * 1024
                )
                if not chunk:
                    break
                yield chunk
        finally:
            os.close(descriptor)

    return StreamingResponse(
        body(),
        media_type=record.mime_type,
        headers={
            "Content-Length": str(size),
            "ETag": f'"{record.content_hash}"',
            "Content-Disposition": "inline",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


__all__ = ["router"]

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
    AuthenticationError,
    AuthorizationError,
    DomainValidationError,
    IdempotencyKeyInvalidError,
    IdempotencyKeyRequiredError,
    IdempotencyMismatchError,
    RequestTooLargeError,
    ResourceConflictError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.identity.sessions import (
    SessionCredentialError,
    digest_secret,
    parse_session_token,
)

from .auth import _cookies, authorize_media_request
from .database import (
    MediaDatabase,
    MediaIdempotencyMismatchError,
    record_to_dict,
)
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


def _read_credentials(request: Request, settings: Any) -> tuple[str, bytes]:
    """Strict session cookie parsing for the read-only byte routes.

    Mirrors ``authorize_media_request`` credential handling exactly
    (same strict cookie grammar, same cookie-name exclusivity); read
    routes take no CSRF proof because they are state_changing=false.
    Credential/parse failures propagate for the caller's existing
    error mapping; a well-formed cookie with an unknown session
    yields a uniform 404 downstream, never an existence oracle.
    """
    names = _cookies(request)
    session_name = (
        "__Host-slaif_session" if settings.secure_cookies else "slaif_session"
    )
    alternate = (
        {"slaif_session", "slaif_csrf"}
        if settings.secure_cookies
        else {"__Host-slaif_session", "__Host-slaif_csrf"}
    )
    if alternate & names.keys():
        raise AuthenticationError()
    token = names.get(session_name)
    if not token:
        raise AuthenticationError()
    public_id, secret = parse_session_token(token)
    return public_id, digest_secret(secret)


def _stream_response(
    descriptor: int, size: int, *, mime_type: str, content_hash: str
) -> StreamingResponse:
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
        media_type=mime_type,
        headers={
            "Content-Length": str(size),
            "ETag": f'"{content_hash}"',
            "Content-Disposition": "inline",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
        },
    )


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
    parsed = None
    published = False
    try:
        parsed = await parse_upload(request, _store(request))
        storage_key = _store(request).publish(parsed.staged)
        published = True
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
        if error.args[0] in {
            "unsupported_media",
            "media_signature_mismatch",
            "media-pdf-too-large",
            "media-pdf-structure-invalid",
            "media-pdf-too-many-pages",
        }:
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
    finally:
        if parsed is not None and not published:
            _store(request).discard_staged(parsed.staged)


_PUBLIC_DIGEST = re.compile(r"^[0-9a-f]{64}$")


@router.get("/public/sha256/{prefix1}/{prefix2}/{digest}")
async def get_public_digest(
    prefix1: str, prefix2: str, digest: str, request: Request
) -> StreamingResponse:
    """Unauthenticated content-addressed public read (immutable bytes).

    The URL carries only the exact public object form; no media id, site
    id, or cookie is accepted.  A digest that is not public or absent is a
    404, never a 403.
    """
    if (
        _PUBLIC_DIGEST.fullmatch(digest) is None
        or len(prefix1) != 2
        or len(prefix2) != 2
        or prefix1 != digest[:2]
        or prefix2 != digest[2:4]
    ):
        raise ResourceNotFoundError()
    try:
        record = await _database(request).get_public(content_hash=digest)
        if record is None:
            raise ResourceNotFoundError()
        descriptor, size = await __import__("asyncio").to_thread(
            _store(request).open_public_verified, digest, record.size_bytes
        )
    except ResourceNotFoundError:
        raise
    except MediaStoreError as error:
        if error.args[0] == "media_missing":
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
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


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


@router.get(
    "/sites/{site_id}/workspaces/{workspace_id}/preview/assets/{media_id}/content"
)
async def get_preview_asset_content(
    site_id: UUID, workspace_id: UUID, media_id: UUID, request: Request
) -> StreamingResponse:
    """Authorized ACTIVE preview byte read in the selected workspace.

    The full 054 preview chain (active account/site/workspace,
    freshness, creator or workspace:read-all, preview:inspect /
    platform-admin, no session touch) is trusted SQL; the byte read
    happens in the authorized workspace's COW overlay, so Agent
    pending private media is reachable before freeze.  Fail-closed to
    a uniform 404; the store re-verifies key/digest/size/bytes.
    """
    settings = request.app.state.settings
    try:
        public_id, session_digest = _read_credentials(request, settings)
    except (AuthenticationError, AuthorizationError):
        raise
    except SessionCredentialError:
        # Explicit credential-shape failure: a constant 401, never a
        # 503/locator leak (the 030 state-changing path keeps its
        # historical mapping; this new read surface maps it safely).
        raise AuthenticationError() from None
    except Exception:
        raise ServiceUnavailableError() from None
    try:
        record = await _database(request).read_preview_bytes(
            public_id=public_id,
            session_digest=session_digest,
            site_id=site_id,
            workspace_id=workspace_id,
            media_id=media_id,
        )
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
    return _stream_response(
        descriptor,
        size,
        mime_type=record.mime_type,
        content_hash=record.content_hash,
    )


@router.get("/browser-preview/assets/{media_id}/content")
async def get_bound_preview_asset_content(
    media_id: UUID, request: Request
) -> StreamingResponse:
    """Confined run-bound private byte read BEFORE freeze.

    The only credential is the existing bound-run preview token
    (``x-slaif-browser-preview``), injected by the browser worker for
    the exact bound media subresource; the worker strips cookies and
    every other credential header before forwarding.  The service
    receives the token only to hash it (sha256): the trusted 076
    gate derives every fact from the stored binding row and re-runs
    the actual 036 no-consume authorizer with the original binding
    nonce, so the read exists only for the bound run after the
    authorized bound document.  No signing key, human session or
    agent capability is involved; authorization and reference
    denials are a uniform 404 (infrastructure failures remain 503).
    """
    raw_values = [
        value
        for name, value in request.scope.get("headers", [])
        if name.lower() == b"x-slaif-browser-preview"
    ]
    if len(raw_values) != 1:
        raise ResourceNotFoundError()
    try:
        token = raw_values[0].decode("ascii")
    except UnicodeDecodeError:
        raise ResourceNotFoundError() from None
    if not 1 <= len(token.encode("utf-8")) <= 4096 or any(
        character.isspace() for character in token
    ):
        raise ResourceNotFoundError()
    credential_digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    try:
        record = await _database(request).read_bound_preview_bytes(
            credential_digest=credential_digest, media_id=media_id
        )
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
    return _stream_response(
        descriptor,
        size,
        mime_type=record.mime_type,
        content_hash=record.content_hash,
    )


@router.get("/review/{snapshot_id}/assets/{media_id}/content")
async def get_review_asset_content(
    snapshot_id: UUID, media_id: UUID, request: Request
) -> StreamingResponse:
    """Frozen review byte read from the immutable snapshot.

    The 076 trusted gate binds the session, the snapshot's site
    membership, snapshot COMPLETE and the media id's membership in the
    stored frozen media map; the bytes are then opened
    content-addressed (exact publish layout) and self-proved by
    ``open_verified``.  No live media_asset row is read, so the bytes
    survive discard and pending cleanup.  Uniform 404 fail-closed.
    """
    settings = request.app.state.settings
    try:
        public_id, session_digest = _read_credentials(request, settings)
    except (AuthenticationError, AuthorizationError):
        raise
    except SessionCredentialError:
        # Explicit credential-shape failure: a constant 401, never a
        # 503/locator leak (the 030 state-changing path keeps its
        # historical mapping; this new read surface maps it safely).
        raise AuthenticationError() from None
    except Exception:
        raise ServiceUnavailableError() from None
    try:
        descriptor = await _database(request).read_frozen_bytes(
            public_id=public_id,
            session_digest=session_digest,
            snapshot_id=snapshot_id,
            media_id=media_id,
        )
        if descriptor is None:
            raise ResourceNotFoundError()
        content_hash = descriptor.content_hash
        if not _PUBLIC_DIGEST.fullmatch(content_hash):
            raise ResourceNotFoundError()
        storage_key = f"sha256/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}"
        file_descriptor, size = _store(request).open_verified(
            storage_key, content_hash, descriptor.size_bytes
        )
    except ResourceNotFoundError:
        raise
    except MediaStoreError as error:
        if error.args[0] in {"media_missing", "storage_corrupt"}:
            raise ResourceNotFoundError() from None
        raise ServiceUnavailableError() from None
    except Exception:
        raise ServiceUnavailableError() from None
    return _stream_response(
        file_descriptor,
        size,
        mime_type=descriptor.mime_type,
        content_hash=content_hash,
    )


__all__ = ["router"]

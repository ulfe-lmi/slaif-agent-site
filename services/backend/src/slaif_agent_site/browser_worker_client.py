"""Bounded internal browser-worker protocol owned by trusted Agent code only."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any, Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from .browser_contracts import (
    BrowserEvidence,
    BrowserRunError,
    BrowserTarget,
    normalize_preview_route,
)

BROWSER_WORKER_CONTRACT_VERSION = "browser-worker/v1"
BROWSER_WORKER_DEPLOYMENT = "slaif-agent-site"
BROWSER_WORKER_AUTHENTICATION_HEADER = "X-SLAIF-Browser-Worker-Token"
BROWSER_WORKER_RESPONSE_ALGORITHM = "HS256"
BROWSER_WORKER_RESPONSE_TYPE = "SLAIF-BROWSER-WORKER-RESULT"
BROWSER_WORKER_SERVICE_CREDENTIAL_FILE = Path("/run/slaif-browser-worker/worker-token")
BROWSER_WORKER_ENDPOINT = "http://browser-worker:3100"
BROWSER_WORKER_SUBMIT_PATH = "/internal/browser/v1/attempts"
BROWSER_WORKER_INSPECT_PATH = "/internal/browser/v1/attempts/inspect"
BROWSER_WORKER_RETRIEVE_PATH = "/internal/browser/v1/artifacts/retrieve"
MAX_WORKER_REQUEST_BYTES = 32_768
MAX_WORKER_RESULT_BYTES = 262_144
MAX_WORKER_ARTIFACT_BYTES = 8_388_608
_CREDENTIAL = re.compile(r"^sbws1:([0-9a-f]{16}):([A-Za-z0-9_-]{43})$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SIGNATURE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_PREVIEW = re.compile(r"^sbp1(?:\.[A-Za-z0-9_-]+){3}$")


def _exact_digest(value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise ValueError("digest is invalid")
    return value


class BrowserWorkerClientError(RuntimeError):
    """A stable failure without worker credentials, bindings, or response data."""


class _WorkerModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        alias_generator=lambda name: (
            name.split("_")[0] + "".join(part.title() for part in name.split("_")[1:])
        ),
    )


class BrowserWorkerCredential(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key_id: str
    secret: SecretStr
    wire_value: SecretStr

    @field_validator("key_id")
    @classmethod
    def key_id_is_exact(cls, value: str) -> str:
        if re.fullmatch(r"[0-9a-f]{16}", value) is None:
            raise ValueError("worker credential is invalid")
        return value


class BrowserWorkerSubmitRequest(_WorkerModel):
    version: Literal["browser-worker/v1"] = "browser-worker/v1"
    deployment: Literal["slaif-agent-site"] = "slaif-agent-site"
    request_id: UUID
    run_id: UUID
    site_id: UUID
    workspace_id: UUID
    capability_id: UUID
    operation_id: UUID
    lease_id: UUID
    attempt: Annotated[int, Field(ge=1, le=5)]
    route: Annotated[str, Field(min_length=1, max_length=2048)]
    route_digest: str
    target: BrowserTarget
    evidence: tuple[BrowserEvidence, ...]
    artifact_bytes_limit: Annotated[int, Field(ge=1, le=16_777_216)]
    duration_seconds: Annotated[int, Field(ge=5, le=120)]
    issued_at: Annotated[int, Field(ge=0, le=4_102_444_800)]
    expires_at: Annotated[int, Field(ge=0, le=4_102_444_800)]
    preview_credential: SecretStr

    _route = field_validator("route")(normalize_preview_route)

    @field_validator("route_digest")
    @classmethod
    def digest_is_exact(cls, value: str) -> str:
        return _exact_digest(value)

    @field_validator("evidence")
    @classmethod
    def evidence_is_bounded(
        cls, value: tuple[BrowserEvidence, ...]
    ) -> tuple[BrowserEvidence, ...]:
        if not value or len(value) > 9 or len(set(value)) != len(value):
            raise ValueError("evidence is invalid")
        return value

    @field_validator("preview_credential")
    @classmethod
    def preview_is_opaque_and_bounded(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if len(raw.encode("utf-8")) > 4096 or _PREVIEW.fullmatch(raw) is None:
            raise ValueError("preview credential is invalid")
        return value

    @model_validator(mode="after")
    def bindings_are_exact(self) -> Self:
        if (
            hashlib.sha256(self.route.encode("utf-8")).hexdigest() != self.route_digest
            or self.expires_at <= self.issued_at
            or self.expires_at - self.issued_at > 60
        ):
            raise ValueError("worker request binding is invalid")
        return self


class BrowserWorkerArtifactMetadata(_WorkerModel):
    version: Literal["browser-worker/v1"]
    artifact_id: UUID
    run_id: UUID
    site_id: UUID
    workspace_id: UUID
    kind: BrowserEvidence
    mime_type: Literal["image/png", "application/json", "text/plain"]
    sha256: str
    size_bytes: Annotated[int, Field(ge=1, le=MAX_WORKER_ARTIFACT_BYTES)]
    target: BrowserTarget
    route_digest: str
    created_at: Annotated[int, Field(ge=0, le=4_102_444_800)]
    expires_at: Annotated[int, Field(ge=0, le=4_102_444_800)]
    visibility: Literal["PRIVATE"]

    _sha = field_validator("sha256", "route_digest")(_exact_digest)


class BrowserWorkerResult(_WorkerModel):
    version: Literal["browser-worker/v1"]
    deployment: Literal["slaif-agent-site"]
    request_id: UUID
    request_digest: str
    run_id: UUID
    site_id: UUID
    workspace_id: UUID
    capability_id: UUID
    operation_id: UUID
    lease_id: UUID
    attempt: Annotated[int, Field(ge=1, le=5)]
    route_digest: str
    target: BrowserTarget
    state: Literal["COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"]
    summary: dict[str, Any]
    error: BrowserRunError | None
    artifacts: tuple[BrowserWorkerArtifactMetadata, ...]
    started_at: Annotated[int, Field(ge=0, le=4_102_444_800)]
    completed_at: Annotated[int, Field(ge=0, le=4_102_444_800)]
    expires_at: Annotated[int, Field(ge=0, le=4_102_444_800)]

    _digests = field_validator("request_digest", "route_digest")(_exact_digest)

    @model_validator(mode="after")
    def result_shape(self) -> Self:
        if (
            (self.state == "COMPLETED") is (self.error is not None)
            or (self.state == "COMPLETED" and not self.artifacts)
            or (self.state != "COMPLETED" and self.artifacts)
            or self.completed_at < self.started_at
            or self.expires_at <= self.completed_at
            or self.expires_at - self.completed_at > 60
            or len(self.artifacts) > 16
            or len(_canonical_json(self.summary).encode("utf-8")) > 65_536
        ):
            raise ValueError("worker result is invalid")
        return self


class SignedBrowserWorkerResult(_WorkerModel):
    version: Literal["browser-worker/v1"]
    algorithm: Literal["HS256"]
    type: Literal["SLAIF-BROWSER-WORKER-RESULT"]
    key_id: str
    result: BrowserWorkerResult
    signature: str

    @field_validator("key_id")
    @classmethod
    def result_key_id(cls, value: str) -> str:
        if re.fullmatch(r"[0-9a-f]{16}", value) is None:
            raise ValueError("worker result is invalid")
        return value

    @field_validator("signature")
    @classmethod
    def result_signature(cls, value: str) -> str:
        if _SIGNATURE.fullmatch(value) is None:
            raise ValueError("worker result is invalid")
        return value


class BrowserWorkerArtifactRetrievalRequest(_WorkerModel):
    version: Literal["browser-worker/v1"] = "browser-worker/v1"
    deployment: Literal["slaif-agent-site"] = "slaif-agent-site"
    request_id: UUID
    run_id: UUID
    site_id: UUID
    workspace_id: UUID
    artifact_id: UUID
    kind: BrowserEvidence
    target: BrowserTarget
    route_digest: str
    sha256: str
    size_bytes: Annotated[int, Field(ge=1, le=MAX_WORKER_ARTIFACT_BYTES)]

    _digests = field_validator("route_digest", "sha256")(_exact_digest)


class BrowserWorkerInspection(_WorkerModel):
    version: Literal["browser-worker/v1"]
    request_id: UUID
    state: Literal["RUNNING"]
    started_at: Annotated[int, Field(ge=0, le=4_102_444_800)]


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _request_document(request: BrowserWorkerSubmitRequest) -> dict[str, Any]:
    document = request.model_dump(mode="json", by_alias=True)
    document["previewCredential"] = request.preview_credential.get_secret_value()
    return document


def browser_worker_request_digest(request: BrowserWorkerSubmitRequest) -> str:
    return hashlib.sha256(
        _canonical_json(_request_document(request)).encode("utf-8")
    ).hexdigest()


def load_browser_worker_credential(path: Path) -> BrowserWorkerCredential:
    if not path.is_absolute() or path.name != "worker-token":
        raise BrowserWorkerClientError("browser worker credential is unavailable")
    directory_fd = -1
    file_fd = -1
    try:
        directory_fd = os.open(
            path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        directory = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(directory.st_mode)
            or stat.S_IMODE(directory.st_mode) != 0o700
            or directory.st_uid != os.geteuid()
        ):
            raise ValueError
        file_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd)
        info = os.fstat(file_fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o400
            or info.st_uid != os.geteuid()
            or info.st_nlink != 1
            or info.st_size != 66
        ):
            raise ValueError
        raw = os.read(file_fd, 70)
        if len(raw) != info.st_size:
            raise ValueError
        wire = raw.decode("ascii")
        match = _CREDENTIAL.fullmatch(wire)
        if match is None:
            raise ValueError
        secret = base64.urlsafe_b64decode(match.group(2) + "=")
        if len(secret) != 32 or base64.urlsafe_b64encode(secret).rstrip(b"=").decode(
            "ascii"
        ) != match.group(2):
            raise ValueError
        return BrowserWorkerCredential(
            key_id=match.group(1),
            secret=SecretStr(secret.hex()),
            wire_value=SecretStr(wire),
        )
    except (OSError, UnicodeError, ValueError):
        raise BrowserWorkerClientError(
            "browser worker credential is unavailable"
        ) from None
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if directory_fd >= 0:
            os.close(directory_fd)


def _credential_secret(credential: BrowserWorkerCredential) -> bytes:
    return bytes.fromhex(credential.secret.get_secret_value())


def verify_browser_worker_result(
    envelope: SignedBrowserWorkerResult,
    request: BrowserWorkerSubmitRequest,
    credential: BrowserWorkerCredential,
    *,
    now: int,
) -> BrowserWorkerResult:
    result_document = envelope.result.model_dump(mode="json", by_alias=True)
    expected_signature = hmac.digest(
        _credential_secret(credential),
        _canonical_json(result_document).encode("utf-8"),
        "sha256",
    )
    try:
        actual_signature = base64.urlsafe_b64decode(envelope.signature + "=")
    except ValueError:
        actual_signature = b""
    if (
        envelope.key_id != credential.key_id
        or base64.urlsafe_b64encode(actual_signature).rstrip(b"=").decode("ascii")
        != envelope.signature
        or len(actual_signature) != 32
        or not hmac.compare_digest(actual_signature, expected_signature)
        or envelope.result.request_digest != browser_worker_request_digest(request)
        or envelope.result.request_id != request.request_id
        or envelope.result.run_id != request.run_id
        or envelope.result.site_id != request.site_id
        or envelope.result.workspace_id != request.workspace_id
        or envelope.result.capability_id != request.capability_id
        or envelope.result.operation_id != request.operation_id
        or envelope.result.lease_id != request.lease_id
        or envelope.result.attempt != request.attempt
        or envelope.result.route_digest != request.route_digest
        or envelope.result.target != request.target
        or envelope.result.expires_at <= now
    ):
        raise BrowserWorkerClientError("browser worker result is invalid")
    return envelope.result


class BrowserWorkerClient:
    """Fixed-origin internal client; no route or task invokes it in this round."""

    def __init__(
        self,
        *,
        endpoint: str,
        credential: BrowserWorkerCredential,
        timeout_seconds: float = 125,
    ) -> None:
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "http"
            or parsed.hostname is None
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.port != 3100
        ):
            raise BrowserWorkerClientError("browser worker client is unavailable")
        self._host = parsed.hostname
        self._port = parsed.port
        self._credential = credential
        self._timeout_seconds = timeout_seconds

    async def _request(
        self, path: str, document: Mapping[str, Any]
    ) -> tuple[int, dict[str, str], bytes]:
        body = _canonical_json(dict(document)).encode("utf-8")
        if len(body) > MAX_WORKER_REQUEST_BYTES:
            raise BrowserWorkerClientError("browser worker request is invalid")
        writer: asyncio.StreamWriter | None = None
        try:
            reader, connected_writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=min(self._timeout_seconds, 5),
            )
            writer = connected_writer
            request = (
                f"POST {path} HTTP/1.1\r\nHost: browser-worker:3100\r\n"
                f"{BROWSER_WORKER_AUTHENTICATION_HEADER}: "
                f"{self._credential.wire_value.get_secret_value()}\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
            ).encode("ascii") + body
            connected_writer.write(request)
            await connected_writer.drain()
            status_line = await asyncio.wait_for(
                reader.readline(), timeout=self._timeout_seconds
            )
            match = re.fullmatch(
                rb"HTTP/1\.1 ([0-9]{3}) [^\r\n]{0,64}\r\n", status_line
            )
            if match is None:
                raise ValueError
            headers: dict[str, str] = {}
            for _ in range(32):
                line = await reader.readline()
                if line == b"\r\n":
                    break
                name, separator, value = line.partition(b":")
                lowered = name.decode("ascii").casefold()
                if (
                    not separator
                    or lowered in headers
                    or len(line) > 8192
                    or not re.fullmatch(r"[a-z0-9-]+", lowered)
                ):
                    raise ValueError
                headers[lowered] = value.strip().decode("ascii")
            else:
                raise ValueError
            if "transfer-encoding" in headers:
                raise ValueError
            length = int(headers.get("content-length", "-1"))
            maximum = max(MAX_WORKER_RESULT_BYTES, MAX_WORKER_ARTIFACT_BYTES)
            if length < 0 or length > maximum:
                raise ValueError
            response_body = await reader.readexactly(length)
            if await reader.read(1) != b"":
                raise ValueError
            connected_writer.close()
            await connected_writer.wait_closed()
            return int(match.group(1)), headers, response_body
        except (
            OSError,
            UnicodeError,
            ValueError,
            TimeoutError,
            asyncio.IncompleteReadError,
        ):
            raise BrowserWorkerClientError("browser worker is unavailable") from None
        finally:
            if writer is not None and not writer.is_closing():
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass

    async def submit(
        self, request: BrowserWorkerSubmitRequest, *, now: int
    ) -> BrowserWorkerResult:
        status, headers, body = await self._request(
            BROWSER_WORKER_SUBMIT_PATH, _request_document(request)
        )
        if (
            status != 200
            or headers.get("content-type") != "application/json; charset=utf-8"
            or len(body) > MAX_WORKER_RESULT_BYTES
        ):
            raise BrowserWorkerClientError("browser worker rejected the request")
        try:
            envelope = SignedBrowserWorkerResult.model_validate_json(body)
        except ValueError:
            raise BrowserWorkerClientError("browser worker result is invalid") from None
        return verify_browser_worker_result(
            envelope, request, self._credential, now=now
        )

    async def inspect(self, request_id: UUID) -> BrowserWorkerInspection | None:
        document = {
            "deployment": BROWSER_WORKER_DEPLOYMENT,
            "requestId": str(request_id),
            "version": BROWSER_WORKER_CONTRACT_VERSION,
        }
        status, headers, body = await self._request(
            BROWSER_WORKER_INSPECT_PATH, document
        )
        if status == 404:
            return None
        if (
            status != 200
            or headers.get("content-type") != "application/json; charset=utf-8"
            or len(body) > 4096
        ):
            raise BrowserWorkerClientError("browser worker inspection is invalid")
        try:
            inspection = BrowserWorkerInspection.model_validate_json(body)
        except ValueError:
            raise BrowserWorkerClientError(
                "browser worker inspection is invalid"
            ) from None
        if inspection.request_id != request_id:
            raise BrowserWorkerClientError("browser worker inspection is invalid")
        return inspection

    async def retrieve(
        self,
        request_id: UUID,
        metadata: BrowserWorkerArtifactMetadata,
    ) -> bytes:
        request = BrowserWorkerArtifactRetrievalRequest(
            request_id=request_id,
            run_id=metadata.run_id,
            site_id=metadata.site_id,
            workspace_id=metadata.workspace_id,
            artifact_id=metadata.artifact_id,
            kind=metadata.kind,
            target=metadata.target,
            route_digest=metadata.route_digest,
            sha256=metadata.sha256,
            size_bytes=metadata.size_bytes,
        )
        status, headers, body = await self._request(
            BROWSER_WORKER_RETRIEVE_PATH,
            request.model_dump(mode="json", by_alias=True),
        )
        if (
            status != 200
            or len(body) != metadata.size_bytes
            or headers.get("content-type") != metadata.mime_type
            or headers.get("x-slaif-artifact-sha256") != metadata.sha256
            or hashlib.sha256(body).hexdigest() != metadata.sha256
        ):
            raise BrowserWorkerClientError("browser artifact is unavailable")
        return body


__all__ = [
    "BROWSER_WORKER_AUTHENTICATION_HEADER",
    "BROWSER_WORKER_CONTRACT_VERSION",
    "BROWSER_WORKER_DEPLOYMENT",
    "BROWSER_WORKER_ENDPOINT",
    "BROWSER_WORKER_RESPONSE_ALGORITHM",
    "BROWSER_WORKER_RESPONSE_TYPE",
    "BROWSER_WORKER_SERVICE_CREDENTIAL_FILE",
    "BrowserWorkerArtifactMetadata",
    "BrowserWorkerClient",
    "BrowserWorkerClientError",
    "BrowserWorkerCredential",
    "BrowserWorkerInspection",
    "BrowserWorkerResult",
    "BrowserWorkerSubmitRequest",
    "SignedBrowserWorkerResult",
    "browser_worker_request_digest",
    "load_browser_worker_credential",
    "verify_browser_worker_result",
]

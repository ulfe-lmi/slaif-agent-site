"""Run-bound, file-keyed browser preview credential contract.

The signer and verifier are shared trusted code. Tokens are never database
credentials, Agent capabilities, human sessions, URLs, or public responses.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .browser_contracts import (
    MAX_ARTIFACT_BYTES,
    MAX_DURATION_SECONDS,
    BrowserEvidence,
    BrowserTarget,
    normalize_preview_route,
)

BROWSER_SIGNING_KEY_FILE = Path("/run/slaif-browser-signing/signing-key")
BROWSER_PREVIEW_TOKEN_PREFIX = "sbp1"
BROWSER_PREVIEW_TOKEN_ALGORITHM = "HS256"
BROWSER_PREVIEW_TOKEN_TYPE = "SLAIF-BROWSER-PREVIEW"
BROWSER_PREVIEW_AUDIENCE = "slaif-render-browser-preview"
BROWSER_PREVIEW_DEPLOYMENT = "slaif-agent-site"
BROWSER_PREVIEW_HEADER = "X-SLAIF-Browser-Preview"
BROWSER_RENDER_HEADER = "X-SLAIF-Browser-Run-Token"
MAX_TOKEN_BYTES = 4096
MAX_TOKEN_TTL_SECONDS = 60
MAX_CLOCK_SKEW_SECONDS = 5
_KEY_PATTERN = re.compile(r"^sbk1:([0-9a-f]{16}):([A-Za-z0-9_-]{43})$")
_ENCODED_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
_NONCE_PATTERN = re.compile(r"^[0-9a-f]{32}$")
_KEY_ID_PATTERN = re.compile(r"^[0-9a-f]{16}$")


class BrowserPreviewCredentialError(RuntimeError):
    """A stable failure that never includes key, token, or binding material."""


@dataclass(frozen=True, slots=True)
class BrowserSigningKey:
    key_id: str
    secret: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if _KEY_ID_PATTERN.fullmatch(self.key_id) is None or len(self.secret) != 32:
            raise BrowserPreviewCredentialError("browser signing key is invalid")


class BrowserPreviewCredentialClaims(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    deployment: Literal["slaif-agent-site"] = "slaif-agent-site"
    audience: Literal["slaif-render-browser-preview"] = "slaif-render-browser-preview"
    contract_version: Literal["browser-preview/v1"] = "browser-preview/v1"
    capability_id: UUID
    site_id: UUID
    workspace_id: UUID
    run_id: UUID
    route: str
    target: BrowserTarget
    evidence: tuple[BrowserEvidence, ...]
    artifact_bytes_limit: Annotated[int, Field(ge=0, le=MAX_ARTIFACT_BYTES)]
    duration_seconds: Annotated[int, Field(ge=5, le=MAX_DURATION_SECONDS)]
    issued_at: int
    expires_at: int
    nonce: str
    key_id: str

    _route = field_validator("route")(normalize_preview_route)

    @field_validator("evidence")
    @classmethod
    def evidence_is_unique(
        cls, value: tuple[BrowserEvidence, ...]
    ) -> tuple[BrowserEvidence, ...]:
        if not value or len(value) > 9 or len(set(value)) != len(value):
            raise ValueError("evidence must be unique and bounded")
        return value

    @field_validator("nonce")
    @classmethod
    def nonce_is_exact(cls, value: str) -> str:
        if _NONCE_PATTERN.fullmatch(value) is None:
            raise ValueError("nonce is malformed")
        return value

    @field_validator("key_id")
    @classmethod
    def key_id_is_exact(cls, value: str) -> str:
        if _KEY_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("key ID is malformed")
        return value

    @model_validator(mode="after")
    def lifetime_is_short(self) -> Self:
        if (
            self.issued_at < 0
            or self.expires_at <= self.issued_at
            or self.expires_at - self.issued_at > MAX_TOKEN_TTL_SECONDS
        ):
            raise ValueError("credential lifetime is invalid")
        return self

    @property
    def nonce_digest(self) -> str:
        return hashlib.sha256(self.nonce.encode("ascii")).hexdigest()


class BrowserPreviewExpectedBinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: UUID | None = None
    site_id: UUID | None = None
    workspace_id: UUID | None = None
    run_id: UUID | None = None
    route: str | None = None
    target: BrowserTarget | None = None

    @field_validator("route")
    @classmethod
    def route_is_normalized(cls, value: str | None) -> str | None:
        return normalize_preview_route(value) if value is not None else None

    def matches(self, claims: BrowserPreviewCredentialClaims) -> bool:
        return all(
            expected is None or expected == actual
            for expected, actual in (
                (self.capability_id, claims.capability_id),
                (self.site_id, claims.site_id),
                (self.workspace_id, claims.workspace_id),
                (self.run_id, claims.run_id),
                (self.route, claims.route),
                (self.target, claims.target),
            )
        )


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str, *, maximum: int) -> bytes:
    if not value or len(value) > maximum or _ENCODED_PATTERN.fullmatch(value) is None:
        raise BrowserPreviewCredentialError("browser credential is malformed")
    padding = "=" * (-len(value) % 4)
    try:
        decoded = base64.b64decode(value + padding, altchars=b"-_", validate=True)
    except (ValueError, UnicodeError):
        raise BrowserPreviewCredentialError("browser credential is malformed") from None
    if len(decoded) > maximum:
        raise BrowserPreviewCredentialError("browser credential is malformed")
    return decoded


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BrowserPreviewCredentialError("browser credential is malformed")
        result[key] = value
    return result


def _json_object(value: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(value.decode("utf-8"), object_pairs_hook=_unique_object)
    except (BrowserPreviewCredentialError, UnicodeError, ValueError):
        raise BrowserPreviewCredentialError("browser credential is malformed") from None
    if not isinstance(parsed, dict):
        raise BrowserPreviewCredentialError("browser credential is malformed")
    return parsed


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def generate_browser_signing_key() -> str:
    """Generate one file representation; callers write it exactly once."""

    return f"sbk1:{secrets.token_hex(8)}:{_b64encode(secrets.token_bytes(32))}"


def load_browser_signing_key(path: Path) -> BrowserSigningKey:
    """Read one key through directory-relative no-follow descriptors."""

    if not path.is_absolute() or path.name != "signing-key":
        raise BrowserPreviewCredentialError("browser signing key is unavailable")
    directory_fd = -1
    file_fd = -1
    try:
        directory_fd = os.open(
            path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        directory_info = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(directory_info.st_mode)
            or stat.S_IMODE(directory_info.st_mode) != 0o700
            or directory_info.st_uid != os.geteuid()
        ):
            raise BrowserPreviewCredentialError("browser signing key is unavailable")
        file_fd = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
        file_info = os.fstat(file_fd)
        if (
            not stat.S_ISREG(file_info.st_mode)
            or stat.S_IMODE(file_info.st_mode) != 0o400
            or file_info.st_uid != os.geteuid()
            or not 48 <= file_info.st_size <= 128
        ):
            raise BrowserPreviewCredentialError("browser signing key is unavailable")
        value = os.read(file_fd, 129)
        if len(value) != file_info.st_size:
            raise BrowserPreviewCredentialError("browser signing key is unavailable")
        text = value.decode("ascii")
    except (BrowserPreviewCredentialError, OSError, UnicodeError):
        raise BrowserPreviewCredentialError(
            "browser signing key is unavailable"
        ) from None
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if directory_fd >= 0:
            os.close(directory_fd)
    match = _KEY_PATTERN.fullmatch(text)
    if match is None:
        raise BrowserPreviewCredentialError("browser signing key is unavailable")
    secret = _b64decode(match.group(2), maximum=64)
    return BrowserSigningKey(key_id=match.group(1), secret=secret)


class BrowserPreviewCredentialSigner:
    """Issue and verify one fixed HMAC credential format."""

    def __init__(self, key: BrowserSigningKey) -> None:
        self._key = key

    @property
    def key_id(self) -> str:
        return self._key.key_id

    def issue(
        self,
        *,
        capability_id: UUID,
        site_id: UUID,
        workspace_id: UUID,
        run_id: UUID,
        route: str,
        target: BrowserTarget,
        evidence: tuple[BrowserEvidence, ...],
        artifact_bytes_limit: int,
        duration_seconds: int,
        now: int,
        ttl_seconds: int = 30,
        nonce: str | None = None,
    ) -> str:
        claims = BrowserPreviewCredentialClaims(
            capability_id=capability_id,
            site_id=site_id,
            workspace_id=workspace_id,
            run_id=run_id,
            route=route,
            target=target,
            evidence=evidence,
            artifact_bytes_limit=artifact_bytes_limit,
            duration_seconds=duration_seconds,
            issued_at=now,
            expires_at=now + ttl_seconds,
            nonce=nonce or secrets.token_hex(16),
            key_id=self._key.key_id,
        )
        header = {
            "alg": BROWSER_PREVIEW_TOKEN_ALGORITHM,
            "kid": self._key.key_id,
            "typ": BROWSER_PREVIEW_TOKEN_TYPE,
            "version": BROWSER_PREVIEW_TOKEN_PREFIX,
        }
        header_part = _b64encode(_canonical(header))
        payload_part = _b64encode(_canonical(claims.model_dump(mode="json")))
        signed = f"{BROWSER_PREVIEW_TOKEN_PREFIX}.{header_part}.{payload_part}"
        signature = hmac.digest(self._key.secret, signed.encode("ascii"), "sha256")
        return f"{signed}.{_b64encode(signature)}"

    def verify(
        self,
        token: str,
        *,
        now: int,
        expected: BrowserPreviewExpectedBinding | None = None,
    ) -> BrowserPreviewCredentialClaims:
        if (
            not isinstance(token, str)
            or not 1 <= len(token.encode("utf-8")) <= MAX_TOKEN_BYTES
            or any(character.isspace() for character in token)
        ):
            raise BrowserPreviewCredentialError("browser credential is invalid")
        parts = token.split(".")
        if len(parts) != 4 or parts[0] != BROWSER_PREVIEW_TOKEN_PREFIX:
            raise BrowserPreviewCredentialError("browser credential is invalid")
        header_part, payload_part, signature_part = parts[1:]
        signature = _b64decode(signature_part, maximum=64)
        signed = ".".join(parts[:3]).encode("ascii")
        expected_signature = hmac.digest(self._key.secret, signed, "sha256")
        if len(signature) != 32 or not hmac.compare_digest(
            signature, expected_signature
        ):
            raise BrowserPreviewCredentialError("browser credential is invalid")
        header = _json_object(_b64decode(header_part, maximum=512))
        if header != {
            "alg": BROWSER_PREVIEW_TOKEN_ALGORITHM,
            "kid": self._key.key_id,
            "typ": BROWSER_PREVIEW_TOKEN_TYPE,
            "version": BROWSER_PREVIEW_TOKEN_PREFIX,
        }:
            raise BrowserPreviewCredentialError("browser credential is invalid")
        try:
            claims = BrowserPreviewCredentialClaims.model_validate(
                _json_object(_b64decode(payload_part, maximum=3072))
            )
        except (BrowserPreviewCredentialError, ValueError):
            raise BrowserPreviewCredentialError(
                "browser credential is invalid"
            ) from None
        if (
            claims.key_id != self._key.key_id
            or claims.issued_at > now + MAX_CLOCK_SKEW_SECONDS
            or claims.expires_at <= now
            or expected is not None
            and not expected.matches(claims)
        ):
            raise BrowserPreviewCredentialError("browser credential is invalid")
        return claims


__all__ = [
    "BROWSER_PREVIEW_AUDIENCE",
    "BROWSER_PREVIEW_DEPLOYMENT",
    "BROWSER_PREVIEW_HEADER",
    "BROWSER_PREVIEW_TOKEN_ALGORITHM",
    "BROWSER_PREVIEW_TOKEN_PREFIX",
    "BROWSER_RENDER_HEADER",
    "BROWSER_SIGNING_KEY_FILE",
    "BrowserPreviewCredentialClaims",
    "BrowserPreviewCredentialError",
    "BrowserPreviewCredentialSigner",
    "BrowserPreviewExpectedBinding",
    "BrowserSigningKey",
    "generate_browser_signing_key",
    "load_browser_signing_key",
]

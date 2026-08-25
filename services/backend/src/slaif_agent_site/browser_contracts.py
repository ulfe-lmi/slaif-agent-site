"""Versioned, bounded data contracts for private preview browser runs.

The module contains no route wiring, credential signing, worker connection,
browser command, artifact filesystem, or publication behavior.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BROWSER_CONTRACT_VERSION = "browser-preview/v1"
MAX_ROUTE_BYTES = 2048
MAX_EVIDENCE_ITEMS = 9
MAX_SUMMARY_PROPERTIES = 32
MAX_SUMMARY_BYTES = 16_384
MAX_ERROR_CODE_CHARACTERS = 64
MAX_ERROR_MESSAGE_CHARACTERS = 512
MAX_ARTIFACT_ITEMS = 16
MAX_ARTIFACT_BYTES = 1_073_741_824
MAX_DURATION_SECONDS = 600
MAX_ATTEMPTS = 5


class BrowserTarget(StrEnum):
    DESKTOP_CHROMIUM = "desktop-chromium"
    TABLET = "tablet"
    MOBILE_CHROMIUM = "mobile-chromium"


class BrowserEvidence(StrEnum):
    SCREENSHOT = "screenshot"
    ACCESSIBILITY_SUMMARY = "accessibility-summary"
    STRUCTURE_SUMMARY = "structure-summary"
    HEADING_SUMMARY = "heading-summary"
    LINK_SUMMARY = "link-summary"
    MEDIA_SUMMARY = "media-summary"
    OVERFLOW_SUMMARY = "overflow-summary"
    CONSOLE_SUMMARY = "console-summary"
    FAILED_REQUEST_SUMMARY = "failed-request-summary"


class BrowserRunState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class BrowserTerminalState(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


BROWSER_TARGETS = tuple(target.value for target in BrowserTarget)
BROWSER_EVIDENCE = tuple(evidence.value for evidence in BrowserEvidence)
BROWSER_RUN_STATES = tuple(state.value for state in BrowserRunState)
BROWSER_TERMINAL_STATES = tuple(state.value for state in BrowserTerminalState)
BROWSER_CONTRACT_BOUNDS = {
    "routeBytes": MAX_ROUTE_BYTES,
    "evidenceItems": MAX_EVIDENCE_ITEMS,
    "summaryProperties": MAX_SUMMARY_PROPERTIES,
    "summaryBytes": MAX_SUMMARY_BYTES,
    "errorCodeCharacters": MAX_ERROR_CODE_CHARACTERS,
    "errorMessageCharacters": MAX_ERROR_MESSAGE_CHARACTERS,
    "artifactItems": MAX_ARTIFACT_ITEMS,
    "artifactBytes": MAX_ARTIFACT_BYTES,
    "durationSeconds": MAX_DURATION_SECONDS,
    "attempts": MAX_ATTEMPTS,
}

_SAFE_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_MALFORMED_ESCAPE = re.compile(r"%(?![0-9a-fA-F]{2})")
_ENCODED_SEPARATOR = re.compile(r"%(?:2f|5c)", re.IGNORECASE)
_QUERY_CREDENTIAL = re.compile(
    r"token|secret|credential|password|cookie|authorization|apikey|accesskey|signature"
)
_CAPABILITY_SHAPE = re.compile(r"sas2_[0-9a-f]+_", re.IGNORECASE)


def normalize_preview_route(value: str) -> str:
    """Validate one origin-relative, credential-free normalized route."""

    if not isinstance(value, str):
        raise ValueError("route must be a string")
    size = len(value.encode("utf-8"))
    if size == 0 or size > MAX_ROUTE_BYTES:
        raise ValueError("route is empty or oversized")
    if not value.startswith("/") or value.startswith("//"):
        raise ValueError("route must be an origin-relative path")
    if "#" in value or any(ord(character) <= 0x20 for character in value):
        raise ValueError("route contains a fragment or unsafe character")
    if "\\" in value or "\x7f" in value:
        raise ValueError("route contains an unsafe path character")
    if _MALFORMED_ESCAPE.search(value) or _ENCODED_SEPARATOR.search(value):
        raise ValueError("route contains unsafe escaping")
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise ValueError("route contains an origin, authority, or fragment")
    try:
        decoded_path = unquote(parsed.path, errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("route contains malformed escaping") from error
    segments = decoded_path.split("/")
    if any(segment in {".", ".."} for segment in segments) or "//" in decoded_path:
        raise ValueError("route contains traversal or duplicate separators")
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    for key, query_value in query_pairs:
        normalized_key = re.sub(r"[^a-z0-9]", "", key.casefold())
        if _QUERY_CREDENTIAL.search(normalized_key) or _CAPABILITY_SHAPE.search(
            query_value
        ):
            raise ValueError("route query contains credential-shaped data")
    canonical_query = urlencode(sorted(query_pairs))
    return parsed.path + (f"?{canonical_query}" if canonical_query else "")


def _validate_evidence(
    value: tuple[BrowserEvidence, ...],
) -> tuple[BrowserEvidence, ...]:
    if not value or len(value) > MAX_EVIDENCE_ITEMS or len(set(value)) != len(value):
        raise ValueError("evidence must be a unique bounded allowlisted list")
    return value


def _bounded_summary(value: dict[str, Any]) -> dict[str, Any]:
    if len(value) > MAX_SUMMARY_PROPERTIES:
        raise ValueError("summary has too many properties")
    try:
        serialized = json.dumps(
            value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("summary must be JSON serializable") from error
    if len(serialized) > MAX_SUMMARY_BYTES:
        raise ValueError("summary is oversized")
    return value


class BrowserCapabilityLimits(BaseModel):
    """Immutable trusted browser limit facts returned by capability auth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_runs: Annotated[int, Field(ge=0, le=2000)] = 20
    max_concurrent_runs: Annotated[int, Field(ge=0, le=32)] = 2
    max_screenshots: Annotated[int, Field(ge=0, le=10_000)] = 50
    max_artifact_bytes: Annotated[int, Field(ge=0, le=MAX_ARTIFACT_BYTES)] = 104_857_600
    max_routes_per_run: Annotated[int, Field(ge=0, le=10)] = 10
    max_evidence_per_run: Annotated[int, Field(ge=0, le=MAX_EVIDENCE_ITEMS)] = 9
    max_duration_seconds: Annotated[int, Field(ge=5, le=MAX_DURATION_SECONDS)] = 120
    max_attempts: Annotated[int, Field(ge=1, le=MAX_ATTEMPTS)] = 3
    allowed_targets: frozenset[BrowserTarget] = frozenset(BrowserTarget)

    @field_validator("allowed_targets")
    @classmethod
    def allowed_targets_are_nonempty(
        cls, value: frozenset[BrowserTarget]
    ) -> frozenset[BrowserTarget]:
        if not value or len(value) > len(BrowserTarget):
            raise ValueError("allowed_targets must be a nonempty approved set")
        return value

    @model_validator(mode="after")
    def concurrent_limit_does_not_exceed_total(self) -> BrowserCapabilityLimits:
        if self.max_concurrent_runs > self.max_runs:
            raise ValueError("max_concurrent_runs cannot exceed max_runs")
        return self


class PreviewRunCreateRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    route: str
    target: BrowserTarget
    evidence: tuple[BrowserEvidence, ...]

    _route = field_validator("route")(normalize_preview_route)
    _evidence = field_validator("evidence")(_validate_evidence)


class PreviewRunStatus(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    run_id: UUID
    state: BrowserRunState
    route: str
    target: BrowserTarget
    evidence: tuple[BrowserEvidence, ...]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime

    _route = field_validator("route")(normalize_preview_route)
    _evidence = field_validator("evidence")(_validate_evidence)


class BrowserRunError(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: Annotated[
        str, Field(min_length=1, max_length=MAX_ERROR_MESSAGE_CHARACTERS)
    ]

    @field_validator("code")
    @classmethod
    def code_is_bounded(cls, value: str) -> str:
        if _SAFE_ERROR_CODE.fullmatch(value) is None:
            raise ValueError("error code is malformed")
        return value


class PrivateBrowserArtifactMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    artifact_id: UUID
    run_id: UUID
    kind: BrowserEvidence
    mime_type: Literal["image/png", "application/json", "text/plain"]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    size_bytes: Annotated[int, Field(ge=1, le=MAX_ARTIFACT_BYTES)]
    target: BrowserTarget
    route_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    created_at: datetime
    expires_at: datetime
    visibility: Literal["PRIVATE"]


class PreviewRunResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    run_id: UUID
    state: BrowserTerminalState
    summary: dict[str, Any]
    error: BrowserRunError | None
    artifacts: Annotated[
        tuple[PrivateBrowserArtifactMetadata, ...],
        Field(max_length=MAX_ARTIFACT_ITEMS),
    ]
    completed_at: datetime

    _summary = field_validator("summary")(_bounded_summary)

    @model_validator(mode="after")
    def completion_shape_is_consistent(self) -> PreviewRunResult:
        if (self.state is BrowserTerminalState.COMPLETED) is (self.error is not None):
            raise ValueError(
                "completed results omit errors; other terminal results require one"
            )
        return self


class InternalPreviewRunSpecification(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    run_id: UUID
    operation_id: UUID
    site_id: UUID
    workspace_id: UUID
    capability_id: UUID
    delegator_id: UUID
    route: str
    route_digest: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    target: BrowserTarget
    evidence: tuple[BrowserEvidence, ...]
    reserved_screenshots: Annotated[int, Field(ge=0, le=1)]
    reserved_artifact_bytes: Annotated[int, Field(ge=0, le=MAX_ARTIFACT_BYTES)]
    max_duration_seconds: Annotated[int, Field(ge=5, le=MAX_DURATION_SECONDS)]
    attempt: Annotated[int, Field(ge=1, le=MAX_ATTEMPTS)]

    _route = field_validator("route")(normalize_preview_route)
    _evidence = field_validator("evidence")(_validate_evidence)


class BrowserRunLease(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    run_id: UUID
    lease_id: UUID
    attempt: Annotated[int, Field(ge=1, le=MAX_ATTEMPTS)]
    expires_at: datetime


class BrowserRunCompletion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    version: Literal["browser-preview/v1"]
    run_id: UUID
    lease_id: UUID
    state: BrowserTerminalState
    summary: dict[str, Any]
    error: BrowserRunError | None

    _summary = field_validator("summary")(_bounded_summary)

    @model_validator(mode="after")
    def completion_shape_is_consistent(self) -> BrowserRunCompletion:
        if (self.state is BrowserTerminalState.COMPLETED) is (self.error is not None):
            raise ValueError(
                "completed results omit errors; other terminal results require one"
            )
        return self


def canonical_serialize_preview_run_request(
    value: PreviewRunCreateRequest | dict[str, Any],
) -> str:
    request = (
        value
        if isinstance(value, PreviewRunCreateRequest)
        else PreviewRunCreateRequest.model_validate(value)
    )
    ordered_evidence = sorted(
        request.evidence, key=lambda item: BROWSER_EVIDENCE.index(item.value)
    )
    return json.dumps(
        {
            "evidence": [item.value for item in ordered_evidence],
            "route": request.route,
            "target": request.target.value,
            "version": request.version,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def preview_run_request_digest(
    value: PreviewRunCreateRequest | dict[str, Any],
) -> str:
    return hashlib.sha256(
        canonical_serialize_preview_run_request(value).encode("utf-8")
    ).hexdigest()


__all__ = [
    "BROWSER_CONTRACT_BOUNDS",
    "BROWSER_CONTRACT_VERSION",
    "BROWSER_EVIDENCE",
    "BROWSER_RUN_STATES",
    "BROWSER_TARGETS",
    "BROWSER_TERMINAL_STATES",
    "BrowserCapabilityLimits",
    "BrowserEvidence",
    "BrowserRunCompletion",
    "BrowserRunError",
    "BrowserRunLease",
    "BrowserRunState",
    "BrowserTarget",
    "BrowserTerminalState",
    "InternalPreviewRunSpecification",
    "PreviewRunCreateRequest",
    "PreviewRunResult",
    "PreviewRunStatus",
    "PrivateBrowserArtifactMetadata",
    "canonical_serialize_preview_run_request",
    "normalize_preview_route",
    "preview_run_request_digest",
]

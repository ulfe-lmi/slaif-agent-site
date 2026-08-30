"""Workspace lifecycle models."""

# ruff: noqa: E501 -- compact validation declarations

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _bounded_text(value: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > max_length or "\x00" in normalized:
        raise ValueError(f"text must be 1-{max_length} characters")
    return normalized


def canonicalize_origin(value: str) -> str:
    """Accept only a canonical HTTP(S) origin, without user-controlled paths."""
    if (
        not isinstance(value, str)
        or not value
        or any(character.isspace() or ord(character) < 0x20 for character in value)
    ):
        raise ValueError("origin is malformed")
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("origin is malformed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("origin credentials are forbidden")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("origin must not include a path or fragment")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("origin port is malformed") from error
    host = parsed.hostname.lower().rstrip(".")
    if not host or any(
        character not in "abcdefghijklmnopqrstuvwxyz0123456789.-:" for character in host
    ):
        raise ValueError("origin host is malformed")
    scheme = parsed.scheme.lower()
    if port is None or port == (443 if scheme == "https" else 80):
        port_part = ""
    else:
        port_part = f":{port}"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"{scheme}://{host}{port_part}"


class WorkspaceStatus(StrEnum):
    CREATING = "CREATING"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    FREEZING = "FREEZING"
    REVIEW = "REVIEW"
    ACCEPT_QUEUED = "ACCEPT_QUEUED"
    SELECTIVE_ACCEPT_QUEUED = "SELECTIVE_ACCEPT_QUEUED"
    DISCARD_QUEUED = "DISCARD_QUEUED"
    PROMOTING = "PROMOTING"
    ACCEPTED = "ACCEPTED"
    CONFLICTED = "CONFLICTED"
    DISCARDING = "DISCARDING"
    DISCARDED = "DISCARDED"
    FAILED = "FAILED"


class DelegationPreset(StrEnum):
    L1_CONTENT_EDITOR = "L1_CONTENT_EDITOR"
    L2_SITE_EDITOR = "L2_SITE_EDITOR"
    L3_SITE_DESIGNER = "L3_SITE_DESIGNER"
    L4_SITE_ARCHITECT = "L4_SITE_ARCHITECT"


class CreateWorkspaceRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    task_description: str = ""
    delegation_preset: DelegationPreset
    duration_hours: int = 1
    requested_scopes: frozenset[str] | None = None
    resource_constraints: dict[str, object] = Field(default_factory=dict)
    source_origins: tuple[str, ...] = ()
    request_quota: int = 1000
    mutation_quota: int = 500
    delete_quota: int = 100
    upload_quota: int = 100
    browser_quota: int = 20

    @field_validator("title")
    @classmethod
    def title_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 128)

    @field_validator("task_description")
    @classmethod
    def description_is_bounded(cls, value: str) -> str:
        return _bounded_text(value, 2048)

    @field_validator("duration_hours")
    @classmethod
    def duration_is_bounded(cls, value: int) -> int:
        if not 1 <= value <= 8:
            raise ValueError("workspace duration must be 1-8 hours")
        return value

    @field_validator("requested_scopes", mode="before")
    @classmethod
    def scopes_are_bounded(cls, value: object) -> frozenset[str] | None:
        if value is None:
            return None
        if not isinstance(value, (list, tuple, set, frozenset)):
            raise ValueError("workspace scopes are bounded")
        raw = list(value)
        if any(not isinstance(scope, str) for scope in raw):
            raise ValueError("workspace scopes are bounded")
        if len(raw) != len(set(raw)):
            raise ValueError("workspace scopes must be unique")
        value = frozenset(raw)
        if len(value) > 128 or any(len(scope) > 96 or not scope for scope in value):
            raise ValueError("workspace scopes are bounded")
        return value

    @field_validator("resource_constraints")
    @classmethod
    def constraints_are_bounded(cls, value: dict[str, object]) -> dict[str, object]:
        if len(value) > 32:
            raise ValueError("workspace constraints are bounded")
        return value

    @field_validator("source_origins")
    @classmethod
    def origins_are_bounded(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) > 16 or any(len(origin) > 2048 for origin in value):
            raise ValueError("workspace source origins are bounded")
        canonical = tuple(canonicalize_origin(origin) for origin in value)
        if len(set(canonical)) != len(canonical):
            raise ValueError("workspace source origins must be unique")
        return canonical

    @field_validator("request_quota")
    @classmethod
    def quotas_are_bounded(cls, value: int) -> int:
        if value < 1 or value > 10000:
            raise ValueError("workspace quota is bounded")
        return value

    @field_validator("mutation_quota", "delete_quota")
    @classmethod
    def mutation_quotas_are_bounded(cls, value: int) -> int:
        if value < 0 or value > 5000:
            raise ValueError("workspace quota is bounded")
        return value

    @field_validator("upload_quota", "browser_quota")
    @classmethod
    def transfer_quotas_are_bounded(cls, value: int) -> int:
        if value < 0 or value > 1000:
            raise ValueError("workspace quota is bounded")
        return value


class WorkspaceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    site_id: UUID
    created_by: UUID
    actor_type: str
    title: str
    task_description: str
    delegation_preset: str
    effective_scopes: tuple[str, ...]
    status: str
    base_site_revision: int
    operation_watermark: int
    created_at: datetime
    expires_at: datetime
    frozen_at: datetime | None
    accepted_at: datetime | None
    discarded_at: datetime | None


__all__ = [
    "CreateWorkspaceRequest",
    "canonicalize_origin",
    "DelegationPreset",
    "WorkspaceRecord",
    "WorkspaceStatus",
]

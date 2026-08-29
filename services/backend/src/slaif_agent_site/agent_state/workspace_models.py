"""Workspace lifecycle models."""

# ruff: noqa: E501 -- compact validation declarations

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _bounded_text(value: str, max_length: int) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > max_length or "\x00" in normalized:
        raise ValueError(f"text must be 1-{max_length} characters")
    return normalized


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
    requested_scopes: frozenset[str] = frozenset()
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

    @field_validator("requested_scopes")
    @classmethod
    def scopes_are_bounded(cls, value: frozenset[str]) -> frozenset[str]:
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
        if len(value) > 16 or any(
            not origin
            or len(origin) > 2048
            or not (origin.startswith("https://") or origin.startswith("http://"))
            or any(character.isspace() for character in origin)
            for origin in value
        ):
            raise ValueError("workspace source origins are bounded")
        return value

    @field_validator(
        "request_quota",
        "mutation_quota",
        "delete_quota",
        "upload_quota",
        "browser_quota",
    )
    @classmethod
    def quotas_are_bounded(cls, value: int) -> int:
        if value < 0 or value > 10000:
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
    "DelegationPreset",
    "WorkspaceRecord",
    "WorkspaceStatus",
]

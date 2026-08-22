"""Workspace lifecycle models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .models import _bounded_json, _bounded_text


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

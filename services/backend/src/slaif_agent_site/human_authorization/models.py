"""Immutable trusted human-site authorization models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .catalog import PERMISSION_BY_KEY, ROLE_CEILINGS


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class OverrideEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class MembershipChange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role_key: str
    delegation_ceiling: int
    status: MembershipStatus = MembershipStatus.ACTIVE
    expected_version: int | None = None
    allow_permissions: frozenset[str] = frozenset()
    deny_permissions: frozenset[str] = frozenset()

    @field_validator("role_key")
    @classmethod
    def role_is_builtin(cls, value: str) -> str:
        if value not in ROLE_CEILINGS:
            raise ValueError("unknown built-in role")
        return value

    @field_validator("delegation_ceiling")
    @classmethod
    def ceiling_is_bounded(cls, value: int) -> int:
        if not 0 <= value <= 4:
            raise ValueError("invalid delegation ceiling")
        return value

    @field_validator("expected_version")
    @classmethod
    def version_is_positive(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("invalid membership version")
        return value

    @model_validator(mode="after")
    def overrides_are_disjoint_and_known(self) -> MembershipChange:
        if self.delegation_ceiling > ROLE_CEILINGS[self.role_key]:
            raise ValueError("ceiling exceeds built-in role")
        if self.allow_permissions & self.deny_permissions:
            raise ValueError("permission override conflict")
        if not (self.allow_permissions | self.deny_permissions) <= set(
            PERMISSION_BY_KEY
        ):
            raise ValueError("unknown permission")
        return self


class PermissionCatalogRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    permission_key: str
    category: str
    agent_delegation_level: int | None
    site_assignable: bool
    installation_only: bool
    system_only: bool
    role_keys: tuple[str, ...]


class RoleCatalogRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role_key: str
    label: str
    description: str
    default_delegation_ceiling: int
    default_permissions: tuple[str, ...]


class MembershipRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    site_id: UUID
    user_account_id: UUID
    role_key: str
    delegation_ceiling: int
    status: MembershipStatus
    version: int
    allow_permissions: frozenset[str]
    deny_permissions: frozenset[str]
    effective_delegation_ceiling: int
    effective_permissions: frozenset[str]
    platform_administrator: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True, init=False)
class HumanSiteContext:
    """Trusted server-created human authority for one active site."""

    user_account_id: UUID
    site_id: UUID
    role_key: str
    membership_version: int
    explicit_delegation_ceiling: int
    effective_delegation_ceiling: int
    effective_permissions: frozenset[str]
    platform_administrator: bool

    def __new__(cls) -> HumanSiteContext:
        raise TypeError("HumanSiteContext is created only from trusted persistence")

    @classmethod
    def _from_database(cls, row: Any) -> HumanSiteContext:
        instance = object.__new__(cls)
        object.__setattr__(instance, "user_account_id", row[0])
        object.__setattr__(instance, "site_id", row[1])
        object.__setattr__(instance, "role_key", row[2])
        object.__setattr__(instance, "membership_version", row[3])
        object.__setattr__(instance, "explicit_delegation_ceiling", row[4])
        object.__setattr__(instance, "effective_delegation_ceiling", row[5])
        object.__setattr__(instance, "effective_permissions", frozenset(row[6]))
        object.__setattr__(instance, "platform_administrator", row[7])
        return instance


__all__ = [
    "HumanSiteContext",
    "MembershipChange",
    "MembershipRecord",
    "MembershipStatus",
    "OverrideEffect",
    "PermissionCatalogRecord",
    "RoleCatalogRecord",
]

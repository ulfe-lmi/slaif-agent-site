"""Immutable semantic site and trusted routing models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from .normalization import (
    normalize_hostname,
    normalize_locale,
    normalize_path_prefix,
    normalize_site_key,
)


class SiteStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class CreateSiteRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    site_key: str
    display_name: str
    default_locale: str

    @field_validator("site_key")
    @classmethod
    def site_key_is_normalized(cls, value: str) -> str:
        return normalize_site_key(value)

    @field_validator("display_name")
    @classmethod
    def display_name_is_bounded(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 128 or "\x00" in normalized:
            raise ValueError("invalid site profile")
        return normalized

    @field_validator("default_locale")
    @classmethod
    def locale_is_normalized(cls, value: str) -> str:
        return normalize_locale(value)


class UpdateSiteRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    display_name: str
    default_locale: str

    @field_validator("display_name")
    @classmethod
    def display_name_is_bounded(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or len(normalized) > 128 or "\x00" in normalized:
            raise ValueError("invalid site profile")
        return normalized

    @field_validator("default_locale")
    @classmethod
    def locale_is_normalized(cls, value: str) -> str:
        return normalize_locale(value)


class DomainMappingRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    hostname: str
    path_prefix: str = "/"
    is_primary: bool = False

    @field_validator("hostname")
    @classmethod
    def hostname_is_normalized(cls, value: str) -> str:
        return normalize_hostname(value)

    @field_validator("path_prefix")
    @classmethod
    def prefix_is_normalized(cls, value: str) -> str:
        return normalize_path_prefix(value)


class SiteRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_id: UUID
    site_key: str
    display_name: str
    status: SiteStatus
    canonical_revision: int
    default_locale: str
    component_catalog_version: str
    content_model_revision: int
    created_at: datetime
    updated_at: datetime


class DomainMapping(BaseModel):
    model_config = ConfigDict(frozen=True)

    domain_id: UUID
    site_id: UUID
    hostname: str
    path_prefix: str
    is_primary: bool
    created_at: datetime


@dataclass(frozen=True, slots=True, init=False)
class SiteContext:
    """Server-owned identity derived only from trusted persistence results."""

    site_id: UUID
    site_key: str
    status: SiteStatus
    canonical_revision: int
    default_locale: str
    matched_hostname: str | None
    matched_path_prefix: str | None

    def __new__(cls) -> SiteContext:
        raise TypeError("SiteContext is created only by the trusted resolver")

    @classmethod
    def _from_database(cls, row: Any) -> SiteContext:
        instance = object.__new__(cls)
        object.__setattr__(instance, "site_id", row[0])
        object.__setattr__(instance, "site_key", row[1])
        object.__setattr__(instance, "status", SiteStatus(row[2]))
        object.__setattr__(instance, "canonical_revision", row[3])
        object.__setattr__(instance, "default_locale", row[4])
        object.__setattr__(instance, "matched_hostname", row[5])
        object.__setattr__(instance, "matched_path_prefix", row[6])
        return instance


__all__ = [
    "CreateSiteRequest",
    "DomainMapping",
    "DomainMappingRequest",
    "SiteContext",
    "SiteRecord",
    "SiteStatus",
    "UpdateSiteRequest",
]

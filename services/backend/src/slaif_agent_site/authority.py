"""Static process identities and database privilege-role boundaries.

These descriptors document dependency and credential classes. They do not
contain credentials and do not replace database grants, network policy, or
service authentication.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final


class ProcessKind(StrEnum):
    """Every Python backend process that can be started independently."""

    CONTROL_API = "control-api"
    EDITOR_API = "editor-api"
    AGENT_API = "agent-api"
    RENDER_API = "render-api"
    MCP_ADAPTER = "mcp-adapter"
    MEDIA_SERVICE = "media-service"
    REVIEW_WORKER = "review-worker"
    SCHEDULER = "scheduler"
    MEDIA_GC = "media-gc"
    BOOTSTRAP = "bootstrap"


class AuthorityClass(StrEnum):
    """One narrow conceptual dependency/credential class per process."""

    CONTROL = "control"
    EDITOR_COW_RUNTIME = "editor-cow-runtime"
    AGENT_COW_RUNTIME = "agent-cow-runtime"
    RENDER_READER = "render-reader"
    INTERNAL_HTTP_CLIENT = "internal-http-client"
    MEDIA = "media"
    REVIEWER = "reviewer"
    SCHEDULER = "scheduler"
    MEDIA_GC = "media-gc"
    SETUP_OWNER = "setup-owner"


class DatabaseAuthority(StrEnum):
    """Exact non-login PostgreSQL privilege role, never a locator."""

    CONTROL = "slaif_control"
    EDITOR_COW_RUNTIME = "slaif_editor_runtime"
    AGENT_COW_RUNTIME = "slaif_agent_runtime"
    PUBLIC_READER = "slaif_public_reader"
    PREVIEW_READER = "slaif_preview_reader"
    MEDIA_METADATA = "slaif_media"
    REVIEWER = "slaif_reviewer"
    SCHEDULER = "slaif_scheduler"
    MEDIA_GC = "slaif_gc"
    SETUP_OWNER = "slaif_owner"


class ListenerExposure(StrEnum):
    """Whether a process has an HTTP listener and how it may be exposed."""

    EDGE_ROUTED = "edge-routed"
    INTERNAL_ONLY = "internal-only"
    NONE = "none"


class LifecycleKind(StrEnum):
    """The start/stop shape of a process."""

    HTTP = "http"
    WORKER = "worker"
    ONE_SHOT = "one-shot"


@dataclass(frozen=True, slots=True)
class AuthorityDescriptor:
    """Immutable, non-secret description of one process boundary."""

    process: ProcessKind
    authority_class: AuthorityClass
    database_authorities: tuple[DatabaseAuthority, ...]
    listener: ListenerExposure
    lifecycle: LifecycleKind

    @property
    def has_listener(self) -> bool:
        return self.listener is not ListenerExposure.NONE

    @property
    def agent_facing(self) -> bool:
        return self.process in {ProcessKind.AGENT_API, ProcessKind.MCP_ADAPTER}

    @property
    def setup_owner(self) -> bool:
        return self.authority_class is AuthorityClass.SETUP_OWNER

    @property
    def reviewer(self) -> bool:
        return self.authority_class is AuthorityClass.REVIEWER

    @property
    def has_database_credential(self) -> bool:
        return bool(self.database_authorities)


AUTHORITY_BY_PROCESS: Final[Mapping[ProcessKind, AuthorityDescriptor]] = (
    MappingProxyType(
        {
            ProcessKind.CONTROL_API: AuthorityDescriptor(
                ProcessKind.CONTROL_API,
                AuthorityClass.CONTROL,
                (DatabaseAuthority.CONTROL,),
                ListenerExposure.EDGE_ROUTED,
                LifecycleKind.HTTP,
            ),
            ProcessKind.EDITOR_API: AuthorityDescriptor(
                ProcessKind.EDITOR_API,
                AuthorityClass.EDITOR_COW_RUNTIME,
                (DatabaseAuthority.EDITOR_COW_RUNTIME,),
                ListenerExposure.EDGE_ROUTED,
                LifecycleKind.HTTP,
            ),
            ProcessKind.AGENT_API: AuthorityDescriptor(
                ProcessKind.AGENT_API,
                AuthorityClass.AGENT_COW_RUNTIME,
                (DatabaseAuthority.AGENT_COW_RUNTIME,),
                ListenerExposure.EDGE_ROUTED,
                LifecycleKind.HTTP,
            ),
            ProcessKind.RENDER_API: AuthorityDescriptor(
                ProcessKind.RENDER_API,
                AuthorityClass.RENDER_READER,
                (
                    DatabaseAuthority.PUBLIC_READER,
                    DatabaseAuthority.PREVIEW_READER,
                ),
                ListenerExposure.INTERNAL_ONLY,
                LifecycleKind.HTTP,
            ),
            ProcessKind.MCP_ADAPTER: AuthorityDescriptor(
                ProcessKind.MCP_ADAPTER,
                AuthorityClass.INTERNAL_HTTP_CLIENT,
                (),
                ListenerExposure.EDGE_ROUTED,
                LifecycleKind.HTTP,
            ),
            ProcessKind.MEDIA_SERVICE: AuthorityDescriptor(
                ProcessKind.MEDIA_SERVICE,
                AuthorityClass.MEDIA,
                (DatabaseAuthority.MEDIA_METADATA,),
                ListenerExposure.EDGE_ROUTED,
                LifecycleKind.HTTP,
            ),
            ProcessKind.REVIEW_WORKER: AuthorityDescriptor(
                ProcessKind.REVIEW_WORKER,
                AuthorityClass.REVIEWER,
                (DatabaseAuthority.REVIEWER,),
                ListenerExposure.NONE,
                LifecycleKind.WORKER,
            ),
            ProcessKind.SCHEDULER: AuthorityDescriptor(
                ProcessKind.SCHEDULER,
                AuthorityClass.SCHEDULER,
                (DatabaseAuthority.SCHEDULER,),
                ListenerExposure.NONE,
                LifecycleKind.WORKER,
            ),
            ProcessKind.MEDIA_GC: AuthorityDescriptor(
                ProcessKind.MEDIA_GC,
                AuthorityClass.MEDIA_GC,
                (DatabaseAuthority.MEDIA_GC,),
                ListenerExposure.NONE,
                LifecycleKind.WORKER,
            ),
            ProcessKind.BOOTSTRAP: AuthorityDescriptor(
                ProcessKind.BOOTSTRAP,
                AuthorityClass.SETUP_OWNER,
                (DatabaseAuthority.SETUP_OWNER,),
                ListenerExposure.NONE,
                LifecycleKind.ONE_SHOT,
            ),
        }
    )
)


def authority_for(process: ProcessKind) -> AuthorityDescriptor:
    """Return the one immutable descriptor selected by trusted process code."""

    return AUTHORITY_BY_PROCESS[process]


__all__ = [
    "AUTHORITY_BY_PROCESS",
    "AuthorityClass",
    "AuthorityDescriptor",
    "DatabaseAuthority",
    "LifecycleKind",
    "ListenerExposure",
    "ProcessKind",
    "authority_for",
]

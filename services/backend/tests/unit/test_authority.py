"""Authority inventory and prohibited-combination contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest
from slaif_agent_site.application import create_http_application
from slaif_agent_site.authority import (
    AUTHORITY_BY_PROCESS,
    AuthorityClass,
    DatabaseAuthority,
    LifecycleKind,
    ListenerExposure,
    ProcessKind,
    authority_for,
)
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.db.roles import DATABASE_ROLES, ROLE_NAMES

EXPECTED_PROCESSES = {
    "control-api",
    "editor-api",
    "agent-api",
    "render-api",
    "mcp-adapter",
    "media-service",
    "review-worker",
    "scheduler",
    "media-gc",
    "bootstrap",
}


def test_exact_process_inventory_and_one_descriptor_per_process() -> None:
    assert {process.value for process in ProcessKind} == EXPECTED_PROCESSES
    assert set(AUTHORITY_BY_PROCESS) == set(ProcessKind)
    assert len(AUTHORITY_BY_PROCESS) == 10
    assert all(authority_for(process).process is process for process in ProcessKind)
    assert len({item.authority_class for item in AUTHORITY_BY_PROCESS.values()}) == 10


def test_descriptors_are_immutable_non_secret_metadata() -> None:
    descriptor = authority_for(ProcessKind.AGENT_API)
    assert {field.name for field in fields(descriptor)} == {
        "process",
        "authority_class",
        "database_authorities",
        "listener",
        "lifecycle",
    }
    with pytest.raises(FrozenInstanceError):
        descriptor.listener = ListenerExposure.NONE  # type: ignore[misc]
    with pytest.raises(TypeError):
        AUTHORITY_BY_PROCESS[ProcessKind.AGENT_API] = descriptor  # type: ignore[index]


def test_setup_reviewer_and_agent_facing_authority_never_combine() -> None:
    setup = [item for item in AUTHORITY_BY_PROCESS.values() if item.setup_owner]
    reviewers = [item for item in AUTHORITY_BY_PROCESS.values() if item.reviewer]
    assert [item.process for item in setup] == [ProcessKind.BOOTSTRAP]
    assert [item.process for item in reviewers] == [ProcessKind.REVIEW_WORKER]
    assert all(not item.agent_facing for item in setup + reviewers)

    agent = authority_for(ProcessKind.AGENT_API)
    assert agent.authority_class is AuthorityClass.AGENT_COW_RUNTIME
    assert agent.database_authorities == (DatabaseAuthority.AGENT_COW_RUNTIME,)
    assert not agent.setup_owner
    assert not agent.reviewer


def test_editor_agent_mcp_and_narrow_service_classes_are_separate() -> None:
    editor = authority_for(ProcessKind.EDITOR_API)
    agent = authority_for(ProcessKind.AGENT_API)
    mcp = authority_for(ProcessKind.MCP_ADAPTER)
    assert editor.authority_class is AuthorityClass.EDITOR_COW_RUNTIME
    assert agent.authority_class is AuthorityClass.AGENT_COW_RUNTIME
    assert editor.authority_class.value != agent.authority_class.value
    assert mcp.authority_class is AuthorityClass.INTERNAL_HTTP_CLIENT
    assert mcp.database_authorities == ()
    assert not mcp.has_database_credential

    expected = {
        ProcessKind.CONTROL_API: AuthorityClass.CONTROL,
        ProcessKind.RENDER_API: AuthorityClass.RENDER_READER,
        ProcessKind.MEDIA_SERVICE: AuthorityClass.MEDIA,
        ProcessKind.SCHEDULER: AuthorityClass.SCHEDULER,
        ProcessKind.MEDIA_GC: AuthorityClass.MEDIA_GC,
    }
    assert {
        process: authority_for(process).authority_class for process in expected
    } == expected


def test_exact_database_role_mapping_and_database_free_mcp() -> None:
    mapped = {
        role
        for descriptor in AUTHORITY_BY_PROCESS.values()
        for role in descriptor.database_authorities
    }
    assert {role.value for role in mapped} == {
        "slaif_owner",
        "slaif_control",
        "slaif_editor_runtime",
        "slaif_agent_runtime",
        "slaif_public_reader",
        "slaif_preview_reader",
        "slaif_reviewer",
        "slaif_scheduler",
        "slaif_media",
        "slaif_gc",
    }
    assert authority_for(ProcessKind.RENDER_API).database_authorities == (
        DatabaseAuthority.PUBLIC_READER,
        DatabaseAuthority.PREVIEW_READER,
    )
    assert authority_for(ProcessKind.MCP_ADAPTER).database_authorities == ()


def test_database_role_manifest_is_exact_password_free_and_immutable() -> None:
    assert ROLE_NAMES == (
        "slaif_owner",
        "slaif_control",
        "slaif_editor_runtime",
        "slaif_agent_runtime",
        "slaif_public_reader",
        "slaif_preview_reader",
        "slaif_reviewer",
        "slaif_scheduler",
        "slaif_media",
        "slaif_gc",
    )
    assert tuple(role.name for role in DATABASE_ROLES) == ROLE_NAMES
    assert [role.name for role in DATABASE_ROLES if not role.service_credential] == [
        "slaif_owner"
    ]
    assert all(
        "password" not in {field.name for field in fields(role)}
        for role in DATABASE_ROLES
    )
    with pytest.raises(FrozenInstanceError):
        DATABASE_ROLES[0].purpose = "changed"  # type: ignore[misc]


def test_only_http_processes_have_listeners() -> None:
    listening = {
        process
        for process, descriptor in AUTHORITY_BY_PROCESS.items()
        if descriptor.has_listener
    }
    assert listening == {
        ProcessKind.CONTROL_API,
        ProcessKind.EDITOR_API,
        ProcessKind.AGENT_API,
        ProcessKind.RENDER_API,
        ProcessKind.MCP_ADAPTER,
        ProcessKind.MEDIA_SERVICE,
    }
    assert (
        authority_for(ProcessKind.RENDER_API).listener is ListenerExposure.INTERNAL_ONLY
    )
    assert all(
        descriptor.lifecycle is not LifecycleKind.HTTP
        and descriptor.listener is ListenerExposure.NONE
        for descriptor in AUTHORITY_BY_PROCESS.values()
        if not descriptor.has_listener
    )


def test_worker_authority_cannot_be_wired_to_http_factory() -> None:
    for process in (
        ProcessKind.REVIEW_WORKER,
        ProcessKind.SCHEDULER,
        ProcessKind.MEDIA_GC,
        ProcessKind.BOOTSTRAP,
    ):
        with pytest.raises(ValueError, match="no HTTP listener"):
            create_http_application(process, settings=ServiceSettings.for_test())

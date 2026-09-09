"""Deterministic contracts for human Agent-session inputs and one-time bounds."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from slaif_agent_site.agent_api.models import AgentCapabilityContext
from slaif_agent_site.agent_state.workspace_models import (
    CreateWorkspaceRequest,
    DelegationPreset,
    canonicalize_origin,
)


def test_origins_are_canonical_and_default_ports_are_removed() -> None:
    assert canonicalize_origin("HTTPS://Example.COM:443/") == "https://example.com"
    assert canonicalize_origin("http://[::1]:8080") == "http://[::1]:8080"
    with pytest.raises(ValueError):
        canonicalize_origin("https://user:password@example.com")
    with pytest.raises(ValueError):
        canonicalize_origin("https://example.com/path")
    with pytest.raises(ValueError):
        canonicalize_origin("ftp://example.com")


def test_workspace_rejects_duplicate_normalized_origins_and_unbounded_quota() -> None:
    with pytest.raises(ValidationError):
        CreateWorkspaceRequest(
            title="Agent",
            delegation_preset=DelegationPreset.L1_CONTENT_EDITOR,
            source_origins=("HTTPS://EXAMPLE.COM", "https://example.com/"),
        )
    with pytest.raises(ValidationError):
        CreateWorkspaceRequest(
            title="Agent",
            delegation_preset=DelegationPreset.L1_CONTENT_EDITOR,
            request_quota=10001,
        )


def test_component_constraints_are_bounded() -> None:
    common: dict[str, Any] = {
        "capability_id": uuid4(),
        "site_id": uuid4(),
        "workspace_id": uuid4(),
        "delegator_id": uuid4(),
        "scopes": frozenset({"component-structure:create"}),
        "created_at": datetime.now(UTC),
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
    }
    context = AgentCapabilityContext(
        **common,
        resource_constraints={
            "allowed_component_types": ["Heading", "Quote"],
            "max_components_per_page": 8,
            "max_visible_components": 8,
            "max_component_depth": 4,
        },
    )
    assert context.resource_constraints["max_component_depth"] == 4
    with pytest.raises(ValidationError):
        AgentCapabilityContext(
            **common,
            resource_constraints={"allowed_component_types": [""]},
        )
    with pytest.raises(ValidationError):
        AgentCapabilityContext(
            **common,
            resource_constraints={"max_components_per_page": -1},
        )

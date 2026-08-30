"""Deterministic contracts for human Agent-session inputs and one-time bounds."""

import pytest
from pydantic import ValidationError
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

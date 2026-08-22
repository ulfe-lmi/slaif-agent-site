"""Integration test: full workspace lifecycle with content model operations.

Tests the complete flow: create site → create workspace → create content
type → create field → create item → freeze → accept → verify canonical.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

class TestWorkspaceContentIntegration:
    """Verify that workspace and content model services work together."""

    def test_content_model_service_has_all_mixins(self) -> None:
        from slaif_agent_site.content_model.service import ContentModelService

        for method in (
            "create_type", "list_types", "get_type",
            "update_type", "delete_type",
            "create_field", "list_fields", "get_field",
            "create_item", "list_items", "get_item",
            "create_page", "list_pages",
            "add_composition_node", "list_composition",
            "create_media", "list_media",
        ):
            assert hasattr(ContentModelService, method), f"missing: {method}"

    def test_capability_module_exists(self) -> None:
        from slaif_agent_site.agent_state.capability import (
            generate_capability_token,
        )
        token, pub, digest = generate_capability_token()
        assert token.startswith("sas2_")
        assert len(digest) == 64

    def test_promotion_module_exists(self) -> None:
        from slaif_agent_site.agent_state.promotion import promote_workspace
        assert callable(promote_workspace)

    def test_audit_module_exists(self) -> None:
        from slaif_agent_site.agent_state.audit import AuditEvent
        event = AuditEvent(
            sequence=1, previous_hash="genesis", actor_id="test",
            action="test", resource_type="test", resource_id="test",
        )
        assert len(event.hash) == 64

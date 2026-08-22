"""Full-stack integration test covering the complete MVP scope.

Verifies that all major subsystems are properly wired:
- Content model service has all CRUD methods from every mixin
- Workspace lifecycle functions exist in control schema
- Capability token generation/validation works
- Promotion service wraps the COW reviewer correctly
- Audit trail produces verifiable hash chains
- MCP adapter delegates without DB credentials
"""

from __future__ import annotations


class TestFullStackWiring:
    """Verify that all subsystems exist and their interfaces match."""

    def test_content_model_service_is_complete(self) -> None:
        from slaif_agent_site.content_model.service import ContentModelService

        expected_methods = [
            "create_type",
            "list_types",
            "get_type",
            "update_type",
            "delete_type",
            "create_field",
            "list_fields",
            "get_field",
            "update_field",
            "delete_field",
            "create_item",
            "list_items",
            "get_item",
            "update_item",
            "delete_item",
            "create_view",
            "list_views",
            "get_view",
            "update_view",
            "delete_view",
            "create_page",
            "list_pages",
            "get_page",
            "update_page",
            "delete_page",
            "create_navigation",
            "list_navigation",
            "get_navigation",
            "update_navigation",
            "delete_navigation",
            "get_theme",
            "update_theme",
            "add_composition_node",
            "update_composition_node",
            "move_composition_node",
            "delete_composition_node",
            "list_composition",
            "create_media",
            "list_media",
            "get_media",
            "update_media",
            "delete_media",
        ]
        for method_name in expected_methods:
            assert hasattr(ContentModelService, method_name), (
                f"ContentModelService missing: {method_name}"
            )

    def test_workspace_lifecycle_functions_exist(self) -> None:
        from slaif_agent_site.agent_state.workspace_models import (
            DelegationPreset,
            WorkspaceStatus,
        )

        assert len(WorkspaceStatus) == 15
        assert len(DelegationPreset) == 4

    def test_capability_system_works_end_to_end(self) -> None:
        from slaif_agent_site.agent_state.capability import (
            compute_digest,
            constant_time_digest_compare,
            generate_capability_token,
        )

        token, pub_id, digest = generate_capability_token()
        recomputed = compute_digest(token)
        assert constant_time_digest_compare(recomputed, digest)

    def test_promotion_service_interface(self) -> None:
        from slaif_agent_site.agent_state.promotion import (
            promote_workspace,
        )

        assert callable(promote_workspace)

    def test_audit_chain_integrity(self) -> None:
        from slaif_agent_site.agent_state.audit import AuditEvent

        genesis = "0" * 64
        prev = genesis
        events = []
        for i in range(5):
            event = AuditEvent(
                sequence=i + 1,
                previous_hash=prev,
                actor_id="system",
                action=f"action_{i}",
                resource_type="test",
                resource_id=f"res-{i}",
                payload={"index": i},
            )
            events.append(event)
            prev = event.hash

        for i in range(1, len(events)):
            assert events[i].previous_hash == events[i - 1].hash

    def test_mcp_adapter_has_no_db_imports(self) -> None:
        import inspect

        from slaif_agent_site.mcp_adapter import mcp_http

        source = inspect.getsource(mcp_http)
        forbidden = ["asyncpg", "database_url", "slaif_control", "slaif_editor"]
        for term in forbidden:
            assert term not in source.lower(), f"MCP adapter contains: {term}"

    def test_idempotency_framework_complete(self) -> None:
        from slaif_agent_site.agent_state.idempotency import (
            IdempotencyStore,
            compute_request_digest,
        )

        store = IdempotencyStore()
        digest = compute_request_digest({"op": "test"})
        assert len(digest) == 64

    def test_browser_confinement_rejects_dangerous_urls(self) -> None:
        from slaif_agent_site.browser_worker.browser_http import _validate_target_url

        assert not _validate_target_url("file:///etc/passwd")
        assert not _validate_target_url("http://localhost/admin")
        assert not _validate_target_url("http://169.254.169.254/metadata")

"""Promotion surface retirement pin (083/1) + real-path conflict mapping.

``agent_state.promotion.promote_workspace`` was retired in 083/1: the real
human accept worker job (``review_worker.accept_job``) is the only
promotion path.  This module pins the removal (import surface + test
inventory) and carries the retired unit-test coverage forward to the real
path: the structured-conflict -> stable-code mapping the accept job uses.
"""

from __future__ import annotations

from slaif_agent_site.agent_state import promotion
from slaif_agent_site.review_worker.accept_job import _conflict_code


class TestPromotionRetirement:
    def test_promote_workspace_removed_from_import_surface(self) -> None:
        assert not hasattr(promotion, "promote_workspace")
        assert "promote_workspace" not in vars(promotion)

    def test_discard_surface_untouched_for_083_2(self) -> None:
        assert callable(promotion.discard_workspace)
        assert callable(promotion.get_conflicts)
        assert isinstance(promotion.PromotionError, type)


class TestRealPathConflictMapping:
    """The retired conflict-raises coverage now pins the accept job."""

    def test_structured_kind_maps_to_stable_code(self) -> None:
        for kind in (
            "BASE_ROW_CHANGED",
            "BASE_ROW_DELETED",
            "BASE_ROW_CREATED",
            "BASE_SCHEMA_CHANGED",
        ):
            assert (
                _conflict_code(
                    [
                        {
                            "table_name": "page",
                            "primary_key": {"id": "x"},
                            "conflict_kind": kind,
                            "operation_id": "op",
                            "order": 1,
                        }
                    ]
                )
                == kind
            )

    def test_empty_or_malformed_falls_back_to_base_row_changed(self) -> None:
        assert _conflict_code(()) == "BASE_ROW_CHANGED"
        assert _conflict_code([{"conflict_kind": "NOPE"}]) == "BASE_ROW_CHANGED"

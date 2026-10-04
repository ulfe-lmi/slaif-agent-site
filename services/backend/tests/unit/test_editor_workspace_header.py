"""Unit coverage for the X-Editor-Workspace selection parsing contract."""

from __future__ import annotations

from uuid import UUID

import pytest
from slaif_agent_site.editor_api.mutations import (
    validate_editor_workspace_header,
)

VALID = "123e4567-e89b-42d3-a456-426614174000"


def test_absent_header_selects_the_legacy_human_path() -> None:
    assert validate_editor_workspace_header(None) is None


@pytest.mark.parametrize(
    "raw",
    [
        VALID,
        VALID.upper(),
    ],
)
def test_well_formed_uuid_is_accepted(raw: str) -> None:
    assert validate_editor_workspace_header(raw) == UUID(VALID)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "not-a-uuid",
        "123e4567e89b42d3a456426614174000",
        "123e4567-e89b-42d3-a456-42661417400",
        "123e4567-e89b-42d3-a456-4266141740001",
        "123e4567-e89b-92d3-a456-426614174000",
        f"{VALID} ",
        f" {VALID}",
        f"{VALID}\n",
        "123e4567-e89b-42d3-a456-426614174000-x",
        "123e4567-e89b-42d3-a456-42661417400",
        "00000000-0000-0000-0000-00000000000000",
        "g23e4567-e89b-42d3-a456-426614174000",
    ],
)
def test_malformed_selection_is_rejected_before_any_db_access(raw: str) -> None:
    with pytest.raises(ValueError):
        validate_editor_workspace_header(raw)

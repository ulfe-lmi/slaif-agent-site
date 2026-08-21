"""Unit tests for the bounded field primitive enumeration."""

from __future__ import annotations

import pytest
from slaif_agent_site.content_model.primitives import (
    FieldPrimitive,
    FieldPrimitiveError,
)

EXPECTED_MEMBERS = {
    "short_text",
    "long_text",
    "rich_text",
    "integer",
    "decimal",
    "boolean",
    "date",
    "datetime",
    "url",
    "email",
    "enum",
    "media",
    "document",
    "reference",
    "multi_reference",
    "location",
    "object",
}


class TestFieldPrimitiveMembers:
    def test_exact_member_set(self) -> None:
        assert {m.value for m in FieldPrimitive} == EXPECTED_MEMBERS

    def test_member_count(self) -> None:
        assert len(FieldPrimitive) == 17

    @pytest.mark.parametrize("value", sorted(EXPECTED_MEMBERS), ids=lambda v: v)
    def test_from_value_roundtrip(self, value: str) -> None:
        member = FieldPrimitive.from_value(value)
        assert isinstance(member, FieldPrimitive)
        assert member.value == value


class TestFieldPrimitiveSafety:
    @pytest.mark.parametrize("value", sorted(EXPECTED_MEMBERS), ids=lambda v: v)
    def test_no_executable_primitives(self, value: str) -> None:
        assert FieldPrimitive.is_executable(value) is False

    def test_unknown_value_is_not_executable(self) -> None:
        assert FieldPrimitive.is_executable("eval") is False
        assert FieldPrimitive.is_executable("javascript") is False

    def test_empty_string_is_not_executable(self) -> None:
        assert FieldPrimitive.is_executable("") is False


class TestFieldPrimitiveErrors:
    def test_unknown_value_raises(self) -> None:
        with pytest.raises(FieldPrimitiveError):
            FieldPrimitive.from_value("nonexistent")

    def test_error_message_contains_value(self) -> None:
        with pytest.raises(FieldPrimitiveError, match="bogus"):
            FieldPrimitive.from_value("bogus")

"""Bounded field primitive enumeration for the configurable content model.

Architecture reference: ARCHITECTURE-for-agents.md §7 (bounded structured
primitives) and §10 (field definition model). Every member is a safe data
shape; executable code is never a valid primitive. Future executable
primitives must be explicitly opted in by modifying source code — there is
no runtime path to make :meth:`FieldPrimitive.is_executable` return True.
"""

from __future__ import annotations

from enum import StrEnum


class FieldPrimitiveError(ValueError):
    """Raised when a string does not match any known field primitive."""


class FieldPrimitive(StrEnum):
    """The 17 bounded field data shapes available to content models."""

    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    RICH_TEXT = "rich_text"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    URL = "url"
    EMAIL = "email"
    ENUM = "enum"
    MEDIA = "media"
    DOCUMENT = "document"
    REFERENCE = "reference"
    MULTI_REFERENCE = "multi_reference"
    LOCATION = "location"
    OBJECT = "object"

    @classmethod
    def from_value(cls, value: str) -> FieldPrimitive:
        """Return the matching member or raise :class:`FieldPrimitiveError`."""
        for member in cls:
            if member.value == value:
                return member
        raise FieldPrimitiveError(f"unknown field primitive: {value!r}")

    @classmethod
    def is_executable(cls, value: str) -> bool:
        """Return True only if *value* maps to an executable primitive.

        All current members are inert data shapes; this method always returns
        False. Future executable primitives must be explicitly opted in by
        modifying this method and adding corresponding validation.
        """
        _EXECUTABLE_PRIMITIVES: frozenset[str] = frozenset()
        return value in _EXECUTABLE_PRIMITIVES

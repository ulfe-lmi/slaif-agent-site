"""Configurable content model domain primitives and contracts."""

from .models import (
    CreateRelationRequest,
    CreateTranslationRequest,
    RelationRecord,
    TranslationRecord,
    UpdateRelationRequest,
    UpdateTranslationRequest,
)
from .primitives import FieldPrimitive, FieldPrimitiveError

__all__ = [
    "FieldPrimitive",
    "FieldPrimitiveError",
    "CreateRelationRequest",
    "CreateTranslationRequest",
    "RelationRecord",
    "TranslationRecord",
    "UpdateRelationRequest",
    "UpdateTranslationRequest",
]

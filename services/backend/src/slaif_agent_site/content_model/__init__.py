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
from .query_dsl import validate_query_contract

__all__ = [
    "FieldPrimitive",
    "FieldPrimitiveError",
    "CreateRelationRequest",
    "CreateTranslationRequest",
    "RelationRecord",
    "TranslationRecord",
    "UpdateRelationRequest",
    "UpdateTranslationRequest",
    "validate_query_contract",
]

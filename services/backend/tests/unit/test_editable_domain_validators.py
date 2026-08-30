from datetime import UTC, datetime
from uuid import uuid4

import pytest
from slaif_agent_site.content_model.models import FieldDefinitionRecord
from slaif_agent_site.content_model.validators import validate_values


def _field(**changes: object) -> FieldDefinitionRecord:
    values: dict[str, object] = {
        "id": uuid4(),
        "site_id": uuid4(),
        "type_id": uuid4(),
        "key": "title",
        "label": "Title",
        "field_type": "short_text",
        "required": True,
        "localized": False,
        "cardinality": 1,
        "position": 0,
        "validation": {},
        "ui_options": {},
        "definition_version": 1,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    values.update(changes)
    return FieldDefinitionRecord.model_validate(values)


def test_values_reject_unknown_and_missing_required_fields() -> None:
    with pytest.raises(ValueError):
        validate_values({}, [_field()])
    with pytest.raises(ValueError):
        validate_values({"unknown": "x"}, [_field()])


def test_values_enforce_primitive_and_cardinality() -> None:
    field = _field(required=False, cardinality=2)
    validate_values({"title": ["one", "two"]}, [field])
    with pytest.raises(ValueError):
        validate_values({"title": ["one", "two", "three"]}, [field])

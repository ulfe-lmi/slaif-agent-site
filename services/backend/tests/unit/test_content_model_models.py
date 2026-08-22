"""Unit tests for content model request/response models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from slaif_agent_site.content_model.models import (
    CreateContentTypeRequest,
    CreateFieldDefinitionRequest,
    UpdateContentTypeRequest,
)


class TestCreateContentTypeRequest:
    def test_valid(self) -> None:
        req = CreateContentTypeRequest(
            key="news", labels={"en": "News"}, slug_pattern="/{slug}", settings={}
        )
        assert req.key == "news"

    def test_empty_key_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateContentTypeRequest(key="", labels={}, slug_pattern="/{slug}")

    def test_key_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateContentTypeRequest(key="a" * 64, labels={}, slug_pattern="/x")

    def test_null_byte_in_slug_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateContentTypeRequest(key="x", labels={}, slug_pattern="/a\x00b")

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateContentTypeRequest(
                key="x",
                labels={},
                slug_pattern="/x",
                unknown_field=True,  # type: ignore[call-arg]
            )

    def test_labels_bounded(self) -> None:
        with pytest.raises(ValidationError):
            CreateContentTypeRequest(
                key="x",
                labels={str(i): "v" for i in range(17)},
                slug_pattern="/x",
            )


class TestCreateFieldDefinitionRequest:
    def test_valid_short_text(self) -> None:
        req = CreateFieldDefinitionRequest(
            key="title", label="Title", field_type="short_text"
        )
        assert req.field_type == "short_text"
        assert req.required is False

    def test_invalid_primitive_rejected(self) -> None:
        with pytest.raises(ValidationError, match="field_type"):
            CreateFieldDefinitionRequest(
                key="x", label="X", field_type="executable_code"
            )

    def test_cardinality_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateFieldDefinitionRequest(
                key="x", label="X", field_type="short_text", cardinality=0
            )

    def test_all_17_primitives_accepted(self) -> None:
        from slaif_agent_site.content_model.primitives import FieldPrimitive

        for p in FieldPrimitive:
            req = CreateFieldDefinitionRequest(key="f", label="F", field_type=p.value)
            assert req.field_type == p.value


class TestUpdateModels:
    def test_partial_update_ok(self) -> None:
        req = UpdateContentTypeRequest(slug_pattern="/new")
        assert req.labels is None
        assert req.slug_pattern == "/new"

    def test_no_change_ok(self) -> None:
        req = UpdateContentTypeRequest()
        assert req.labels is None

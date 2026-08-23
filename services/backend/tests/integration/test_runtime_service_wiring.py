"""Integration proof that runtime apps expose the semantic content service."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from slaif_agent_site.agent_api import create_app as create_agent_app
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.content_model.service import (
    ContentModelService,
    ContentModelServiceError,
    ContentModelServiceReason,
)
from slaif_agent_site.editor_api import create_app as create_editor_app


async def test_content_model_service_is_reachable_from_runtime_apps() -> None:
    apps: dict[str, FastAPI] = {
        "editor": create_editor_app(settings=ServiceSettings.for_test()),
        "agent": create_agent_app(settings=ServiceSettings.for_test()),
    }
    for process, app in apps.items():
        service = app.state.content_model_service
        assert isinstance(service, ContentModelService), process
        with pytest.raises(ContentModelServiceError) as unavailable:
            await service.list_types(uuid4())
        assert unavailable.value.reason is ContentModelServiceReason.UNAVAILABLE
        for method in ("get_type", "list_items", "get_item"):
            assert hasattr(service, method), f"{process}: missing {method}"

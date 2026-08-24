"""Integration proof that Editor owns the ordinary semantic service."""

from __future__ import annotations

from fastapi import FastAPI
from slaif_agent_site.agent_api import create_app as create_agent_app
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.editor_api import create_app as create_editor_app


async def test_agent_does_not_expose_an_ordinary_semantic_service() -> None:
    apps: dict[str, FastAPI] = {
        "editor": create_editor_app(settings=ServiceSettings.for_test()),
        "agent": create_agent_app(settings=ServiceSettings.for_test()),
    }
    for process, app in apps.items():
        if process == "editor":
            assert hasattr(app.state, "editor_database")
            assert not hasattr(app.state, "content_model_service")
            continue
        assert not hasattr(app.state, "content_model_service"), process

"""Deterministic public Agent OpenAPI contract tests."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slaif_agent_site.agent_api.app import create_app, public_agent_openapi_bytes
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.content_model.design_system import (
    component_property_scope_metadata,
)
from slaif_agent_site.health import ProbeResult

from tools.contracts.generate_agent_openapi import CONTRACT_PATH, generate_agent_openapi


class ContractDatabase:
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    def cow_pool(self) -> None:
        return None

    async def authenticate_agent_capability(self, _auth_header: str) -> None:
        return None


def _app() -> FastAPI:
    return create_app(
        settings=ServiceSettings.for_test(),
        database_settings=AgentDatabaseSettings(mode=AgentDatabaseMode.TEST),
        database=ContractDatabase(),
    )


def test_committed_contract_matches_live_generator_byte_for_byte() -> None:
    generated = generate_agent_openapi()
    assert CONTRACT_PATH.read_bytes() == generated
    assert generated == public_agent_openapi_bytes(_app())
    assert generated.endswith(b"\n")
    assert json.loads(generated) == json.loads(public_agent_openapi_bytes(_app()))


def test_public_contract_has_scopes_headers_errors_and_no_internal_paths() -> None:
    document = json.loads(generate_agent_openapi())
    assert document["openapi"] == "3.1.0"
    assert document["paths"]
    assert all(path.startswith("/api/agent/v1/") for path in document["paths"])
    assert document["paths"]["/api/agent/v1/openapi.json"]["get"]["security"] == []
    permissions = document["paths"]["/api/agent/v1/permissions"]["get"]
    assert permissions["security"] == [{"AgentCapability": []}]
    assert permissions["x-slaif-required-scopes"] == ["site:read"]
    assert permissions["x-slaif-mutation"] is False
    assert permissions["x-slaif-idempotency"] == "not-applicable"
    mutation = document["paths"]["/api/agent/v1/content-model/types"]["post"]
    assert mutation["x-slaif-mutation"] is True
    assert mutation["x-slaif-idempotency"] == "required"
    header = next(
        parameter
        for parameter in mutation["parameters"]
        if parameter["name"] == "Idempotency-Key"
    )
    assert header["required"] is True
    assert set(mutation["responses"]) >= {
        "201",
        "400",
        "401",
        "403",
        "404",
        "409",
        "413",
        "422",
        "429",
        "503",
    }
    assert mutation["responses"]["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorEnvelope"
    }
    page_patch = document["paths"]["/api/agent/v1/pages/{page_id}"]["patch"]
    assert page_patch["x-slaif-required-scopes"] == ["page:write"]
    assert page_patch["x-slaif-conditional-scopes"] == [
        {
            "when_fields": ["slug", "locale", "route_template"],
            "required_scopes": ["route:write"],
        }
    ]
    move = document["components"]["schemas"]["MovePageRequest"]
    assert set(move["properties"]) == {"parent_id", "expected_row_version"}
    assert "deleted_at" in document["components"]["schemas"]["PageRecord"]["properties"]
    restore = document["paths"]["/api/agent/v1/pages/{page_id}:restore"]["post"]
    restore_schema = restore["requestBody"]["content"]["application/json"]["schema"]
    assert restore["requestBody"]["required"] is True
    assert restore_schema == {"$ref": "#/components/schemas/RestorePageRequest"}
    assert "LivenessResponse" not in document["components"]["schemas"]
    assert "ReadinessResponse" not in document["components"]["schemas"]


def test_theme_contract_is_closed_and_has_separate_token_scope() -> None:
    document = json.loads(generate_agent_openapi())
    schema_path = document["paths"]["/api/agent/v1/theme-schema"]["get"]
    theme_path = document["paths"]["/api/agent/v1/theme"]["get"]
    patch_path = document["paths"]["/api/agent/v1/theme"]["patch"]
    assert schema_path["x-slaif-required-scopes"] == ["theme:read"]
    assert theme_path["x-slaif-required-scopes"] == ["theme:read"]
    assert patch_path["x-slaif-required-scopes"] == ["theme-tokens:write"]
    assert patch_path["x-slaif-mutation"] is True
    assert (
        document["components"]["schemas"]["ThemeRecord"]["additionalProperties"]
        is False
    )
    assert (
        document["components"]["schemas"]["AgentThemeSchemaResponse"][
            "additionalProperties"
        ]
        is False
    )
    assert (
        document["components"]["schemas"]["AgentThemeMutationResponse"][
            "additionalProperties"
        ]
        is False
    )
    request = document["components"]["schemas"]["AgentUpdateThemeRequest"]
    assert request["additionalProperties"] is False
    assert set(request["properties"]) == {
        "expected_row_version",
        "palette",
        "typography",
        "layout",
        "shape",
    }


def test_component_catalog_contract_is_closed_and_agent_create_has_no_raw_rank() -> (
    None
):
    document = json.loads(generate_agent_openapi())
    schemas = document["components"]["schemas"]
    for name in (
        "AgentComponentCatalogResponse",
        "AgentComponentDescriptor",
        "AgentComponentPropDescriptor",
        "AgentComponentSchemaNode",
    ):
        assert schemas[name]["additionalProperties"] is False
    create = schemas["AgentCreateCompositionNodeRequest"]
    assert "order_key" not in create["properties"]
    component_path = document["paths"]["/api/agent/v1/component-catalog"]["get"]
    assert component_path["x-slaif-required-scopes"] == ["component-catalog:read"]


def test_design_system_contract_is_typed_and_site_catalog_bound() -> None:
    document = json.loads(generate_agent_openapi())
    design_path = document["paths"]["/api/agent/v1/design-system"]["get"]
    assert design_path["x-slaif-required-scopes"] == ["theme:read"]
    assert design_path["x-slaif-mutation"] is False
    schema = document["components"]["schemas"]["AgentDesignSystemResponse"]
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {
        "catalog_version",
        "components",
        "composition_schema_version",
        "renderer_version",
        "responsive_fallback",
        "responsive_labels",
        "responsive_scope",
        "tokens",
        "version",
    }
    tokens = document["components"]["schemas"]["AgentDesignTokenSet"]
    assert tokens["additionalProperties"] is False
    assert tokens["properties"]["columns"]["items"]["type"] == "integer"
    component_patch = document["paths"]["/api/agent/v1/components/{component_id}"][
        "patch"
    ]
    assert component_patch["x-slaif-required-scopes"] == []
    assert component_patch["x-slaif-component-property-scopes"] == (
        component_property_scope_metadata()
    )
    image_aspect = next(
        item
        for item in component_patch["x-slaif-conditional-scopes"]
        if item["component_types"] == ["Image"]
        and item["when_fields"] == ["props.aspectRatio"]
    )
    assert image_aspect["required_scopes"] == ["component-props:write"]


def test_public_edge_endpoint_returns_the_same_canonical_bytes() -> None:
    with TestClient(_app()) as client:
        response = client.get("/api/agent/v1/openapi.json")
    assert response.status_code == 200
    assert response.content == CONTRACT_PATH.read_bytes()

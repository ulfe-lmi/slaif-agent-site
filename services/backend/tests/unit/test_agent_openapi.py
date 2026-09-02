"""Deterministic public Agent OpenAPI contract tests."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slaif_agent_site.agent_api.app import create_app, public_agent_openapi_bytes
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.config import ServiceSettings
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
    mutation = document["paths"]["/api/agent/v1/content-model/types"]["post"]
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
    assert "LivenessResponse" not in document["components"]["schemas"]
    assert "ReadinessResponse" not in document["components"]["schemas"]


def test_public_edge_endpoint_returns_the_same_canonical_bytes() -> None:
    with TestClient(_app()) as client:
        response = client.get("/api/agent/v1/openapi.json")
    assert response.status_code == 200
    assert response.content == CONTRACT_PATH.read_bytes()

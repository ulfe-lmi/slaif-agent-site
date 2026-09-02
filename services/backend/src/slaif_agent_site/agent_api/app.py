"""Agent API application factory."""

from __future__ import annotations

import argparse
import copy
import json
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response

from ..application import create_http_application
from ..authority import ProcessKind
from ..browser_preview_credentials import (
    BrowserPreviewCredentialError,
    BrowserPreviewCredentialSigner,
    load_browser_signing_key,
)
from ..browser_worker_client import (
    BrowserWorkerClient,
    BrowserWorkerClientError,
    load_browser_worker_credential,
)
from ..config import ConfigurationError, ServiceSettings
from ..control_api.route_policy import (
    RouteMutationClass,
    route_policies_for,
    validate_route_policy_coverage,
)
from ..errors import ErrorEnvelope
from ..health import ProbeResult, ReadinessProbe
from ..logging import configure_json_logging
from .agent_http import router as agent_router
from .browser_http import router as browser_router
from .browser_service import AgentBrowserRunService
from .config import AgentDatabaseConfigurationError, AgentDatabaseSettings
from .database import AgentDatabase, AgentDatabaseAdapter
from .dispatcher import AgentBrowserDispatcher

_AGENT_HTTP_METHODS = ("get", "post", "patch", "delete")
_AGENT_ERROR_RESPONSES = {
    "400": "Malformed request or missing/invalid idempotency key.",
    "401": "Authentication is required.",
    "403": "The capability scope or resource constraint is not sufficient.",
    "404": "The resource is not available to this capability.",
    "409": "The request conflicts with current state or idempotency.",
    "413": "The request exceeds the bounded body limit.",
    "422": "The request failed domain validation.",
    "429": "The request exceeds an enforced quota.",
    "503": "The service is temporarily unavailable.",
}
_IDEMPOTENCY_HEADER_SCHEMA = {
    "type": "string",
    "minLength": 1,
    "maxLength": 128,
    "pattern": "^[A-Za-z0-9._~-]+$",
    "title": "Idempotency-Key",
}


def _sorted_json(value: object) -> object:
    if isinstance(value, dict):
        return {key: _sorted_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_json(item) for item in value]
    return value


def build_public_agent_openapi_document(app: FastAPI) -> dict[str, object]:
    """Build the one deterministic public Agent contract from live handlers."""
    raw = copy.deepcopy(app.openapi())
    paths = {
        path: operations
        for path, operations in raw.get("paths", {}).items()
        if path.startswith("/api/agent/v1/")
    }
    policies = {
        (policy.method, policy.path_template): policy
        for policy in route_policies_for(ProcessKind.AGENT_API)
    }
    document: dict[str, object] = {
        "openapi": "3.1.0",
        "info": {
            "title": "SLAIF Agent API",
            "version": "v1",
            "description": "Capability-authenticated semantic Agent contract.",
        },
        "paths": paths,
        "components": raw.get("components", {}),
    }
    components = document["components"]
    if not isinstance(components, dict):
        components = {}
        document["components"] = components
    schemas = components.setdefault("schemas", {})
    if not isinstance(schemas, dict):
        schemas = {}
        components["schemas"] = schemas
    error_schema = ErrorEnvelope.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    definitions = error_schema.pop("$defs", {})
    if isinstance(definitions, dict):
        schemas.update(definitions)
    schemas["ErrorEnvelope"] = error_schema
    components["securitySchemes"] = {
        "AgentCapability": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "sas2_",
        }
    }

    typed_paths = document["paths"]
    assert isinstance(typed_paths, dict)
    for path, operations in typed_paths.items():
        if not isinstance(operations, dict):
            raise RuntimeError(f"Agent OpenAPI path is malformed: {path}")
        for method in _AGENT_HTTP_METHODS:
            operation = operations.get(method)
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            policy = policies.get((method.upper(), path))
            if policy is None:
                raise RuntimeError(
                    f"Agent OpenAPI route has no policy: {method.upper()} {path}"
                )
            scopes = list(policy.required_scopes)
            operation["x-slaif-required-scopes"] = scopes
            if path == "/api/agent/v1/openapi.json":
                operation["security"] = []
            else:
                # OpenAPI bearer values are empty arrays; exact operation scopes
                # are published separately in the stable extension above.
                operation["security"] = [{"AgentCapability": []}]
            if policy.mutation_class is RouteMutationClass.MUTATION:
                parameters = operation.setdefault("parameters", [])
                if not isinstance(parameters, list):
                    raise RuntimeError(
                        f"Agent OpenAPI parameters are malformed: {path}"
                    )
                header = next(
                    (
                        parameter
                        for parameter in parameters
                        if isinstance(parameter, dict)
                        and parameter.get("in") == "header"
                        and parameter.get("name") == "Idempotency-Key"
                    ),
                    None,
                )
                if header is None:
                    header = {"in": "header", "name": "Idempotency-Key"}
                    parameters.append(header)
                header["required"] = True
                header["schema"] = copy.deepcopy(_IDEMPOTENCY_HEADER_SCHEMA)
            if (
                path == "/api/agent/v1/preview-runs/{run_id}/artifacts/{artifact_id}"
                and method == "get"
            ):
                operation.setdefault("responses", {})["200"] = {
                    "description": "Private browser artifact bytes",
                    "content": {
                        "application/octet-stream": {
                            "schema": {"type": "string", "format": "binary"}
                        }
                    },
                }
            responses = operation["responses"]
            if not isinstance(responses, dict):
                raise RuntimeError(f"Agent OpenAPI responses are malformed: {path}")
            for status, description in _AGENT_ERROR_RESPONSES.items():
                responses[status] = {
                    "description": description,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorEnvelope"}
                        }
                    },
                }
    # Only schemas reachable from the public Agent paths are exposed. This
    # removes health/internal models from the product contract.
    referenced: set[str] = set()
    pending = [typed_paths]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "$ref" and isinstance(child, str):
                    prefix = "#/components/schemas/"
                    if child.startswith(prefix):
                        name = child.removeprefix(prefix)
                        if name not in referenced:
                            referenced.add(name)
                            if name in schemas:
                                pending.append(schemas[name])
                else:
                    pending.append(child)
        elif isinstance(value, list):
            pending.extend(value)
    components["schemas"] = {
        name: schemas[name] for name in sorted(referenced) if name in schemas
    }
    return _sorted_json(document)  # type: ignore[return-value]


def public_agent_openapi_bytes(app: FastAPI) -> bytes:
    """Serialize the public Agent contract with stable bytes and newline."""
    return (
        json.dumps(
            build_public_agent_openapi_document(app),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n"
    ).encode("utf-8")


def create_app(
    *,
    settings: ServiceSettings | None = None,
    database_settings: AgentDatabaseSettings | None = None,
    database: AgentDatabaseAdapter | None = None,
    browser_signer: BrowserPreviewCredentialSigner | None = None,
    browser_worker_client: BrowserWorkerClient | None = None,
    readiness_probes: Sequence[ReadinessProbe] = (),
) -> FastAPI:
    selected_database_settings = database_settings or AgentDatabaseSettings.load()
    selected_database = database or AgentDatabase(settings=selected_database_settings)
    test_mode = (
        getattr(getattr(settings, "mode", None), "value", None) == "test"
        or selected_database_settings.mode.value == "test"
    )
    selected_signer = browser_signer
    if selected_signer is None and not test_mode:
        try:
            selected_signer = BrowserPreviewCredentialSigner(
                load_browser_signing_key(
                    selected_database_settings.browser_signing_key_file
                )
            )
        except BrowserPreviewCredentialError:
            selected_signer = None
    selected_worker_client = browser_worker_client
    if selected_worker_client is None and not test_mode:
        try:
            selected_worker_client = BrowserWorkerClient(
                endpoint=selected_database_settings.browser_worker_endpoint,
                credential=load_browser_worker_credential(
                    selected_database_settings.browser_worker_service_credential_file
                ),
            )
        except BrowserWorkerClientError:
            selected_worker_client = None

    async def browser_signing_readiness() -> ProbeResult:
        if selected_signer is None:
            return ProbeResult.unavailable("signing_key_unavailable")
        return ProbeResult.ready()

    async def browser_worker_client_readiness() -> ProbeResult:
        if selected_worker_client is None:
            return ProbeResult.unavailable("worker_credential_unavailable")
        return ProbeResult.ready()

    dispatcher = AgentBrowserDispatcher(
        database=selected_database,
        signer=selected_signer,
        worker_client=selected_worker_client,
        settings=selected_database_settings.dispatcher_settings,
    )

    @asynccontextmanager
    async def database_lifespan(_app: FastAPI) -> AsyncIterator[None]:
        await selected_database.start()
        await dispatcher.start()
        try:
            yield
        finally:
            await dispatcher.stop()
            await selected_database.stop()

    app = create_http_application(
        ProcessKind.AGENT_API,
        settings=settings,
        readiness_probes=(
            ReadinessProbe("database", selected_database.readiness),
            *(
                (ReadinessProbe("browser-signing-key", browser_signing_readiness),)
                if not test_mode or browser_signer is not None
                else ()
            ),
            *(
                (
                    ReadinessProbe(
                        "browser-worker-client", browser_worker_client_readiness
                    ),
                )
                if not test_mode or browser_worker_client is not None
                else ()
            ),
            *(
                (ReadinessProbe("browser-dispatcher", dispatcher.readiness),)
                if not test_mode
                else ()
            ),
            *readiness_probes,
        ),
        lifespan_factory=database_lifespan,
    )
    app.state.database = selected_database
    app.state.browser_run_service = AgentBrowserRunService(
        selected_database, worker_client=selected_worker_client
    )
    app.state.browser_preview_signer = selected_signer
    app.state.browser_worker_client = selected_worker_client
    app.state.browser_dispatcher = dispatcher
    app.include_router(agent_router)
    app.include_router(browser_router)

    @app.get("/api/agent/v1/openapi.json")
    async def agent_openapi() -> Response:
        """Return the stable, versioned public Agent contract only."""
        return Response(
            content=public_agent_openapi_bytes(app),
            media_type="application/json",
        )

    validate_route_policy_coverage(app, ProcessKind.AGENT_API)
    return app


def run_agent_process(*, argv: Sequence[str] | None = None) -> int:
    """Validate settings and run the complete Agent API application."""

    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.agent_api")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration without opening a database connection",
    )
    arguments = parser.parse_args(argv)
    try:
        service_settings = ServiceSettings.load()
        database_settings = AgentDatabaseSettings.load()
        app = create_app(
            settings=service_settings,
            database_settings=database_settings,
        )
    except (ConfigurationError, AgentDatabaseConfigurationError) as error:
        parser.exit(2, f"{error}\n")

    if arguments.check:
        print("agent-api: CHECK_OK")
        return 0

    configure_json_logging(
        service=ProcessKind.AGENT_API.value,
        level=service_settings.log_level.value,
    )
    uvicorn.run(
        app,
        host=service_settings.bind_host,
        port=service_settings.bind_port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=service_settings.shutdown_timeout_seconds,
    )
    return 0


__all__ = ["create_app", "run_agent_process"]

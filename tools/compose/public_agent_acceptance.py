"""Public-edge acceptance proof for the bounded Agent content contract."""

# ruff: noqa: E501 -- public proof calls keep route and assertion details visible

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

from public_agent_restart import (
    ProofFailure,
    PublicClient,
    _is_ready_service,
    _json,
    _list,
    _require_uuid,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_USERNAME = "compose.admin"
FIXTURE_PASSWORD = "fixture-compose-auth-password-123"
FIELD_PRIMITIVES = {
    "short_text",
    "long_text",
    "rich_text",
    "integer",
    "decimal",
    "boolean",
    "date",
    "datetime",
    "url",
    "email",
    "enum",
    "media",
    "document",
    "reference",
    "multi_reference",
    "location",
    "object",
}

_CAPABILITY_CONTEXTS: dict[str, tuple[str, str, str]] = {}
_EXPECTED_SEMANTIC_AUDIT: list[dict[str, str | int | bool]] = []


def _semantic_contract(
    path: str, method: str, status: int
) -> tuple[str, str, str] | None:
    """Return the exact audit identity for a successful semantic route."""

    segments = path.rstrip("/").split("/")
    if len(segments) >= 6 and segments[:5] == [
        "",
        "api",
        "agent",
        "v1",
        "content-model",
    ]:
        if segments[5] == "types":
            if len(segments) == 6 and method == "POST":
                return "content_type", "CONTENT_TYPE_CREATED", "mutation"
            if len(segments) == 7 and method in {"PATCH", "DELETE"}:
                return (
                    "content_type",
                    "CONTENT_TYPE_UPDATED"
                    if method == "PATCH"
                    else "CONTENT_TYPE_DELETED",
                    "mutation" if method == "PATCH" else "delete",
                )
            if len(segments) == 8 and segments[7] == "fields":
                if method == "POST":
                    return "field_definition", "FIELD_DEFINITION_CREATED", "mutation"
            if len(segments) == 9 and segments[7] == "fields":
                if method in {"PATCH", "DELETE"}:
                    return (
                        "field_definition",
                        "FIELD_DEFINITION_UPDATED"
                        if method == "PATCH"
                        else "FIELD_DEFINITION_DELETED",
                        "mutation" if method == "PATCH" else "delete",
                    )
    if len(segments) >= 4 and segments[:4] == [
        "",
        "api",
        "agent",
        "v1",
    ]:
        if (
            len(segments) == 7
            and segments[4] == "content-items"
            and segments[5] == "types"
        ):
            if method == "POST":
                return "content_item", "CONTENT_ITEM_CREATED", "mutation"
        if len(segments) == 6 and segments[4] == "content-items":
            if method in {"PATCH", "DELETE"}:
                return (
                    "content_item",
                    "CONTENT_ITEM_UPDATED"
                    if method == "PATCH"
                    else "CONTENT_ITEM_DELETED",
                    "mutation" if method == "PATCH" else "delete",
                )
        if (
            len(segments) == 7
            and segments[4] == "content-items"
            and segments[6]
            in {
                "translations",
                "relations",
            }
        ):
            resource_type = (
                "content_item_translation"
                if segments[6] == "translations"
                else "item_relation"
            )
            prefix = (
                "CONTENT_ITEM_TRANSLATION"
                if resource_type == "content_item_translation"
                else "ITEM_RELATION"
            )
            if method == "POST":
                return resource_type, f"{prefix}_CREATED", "mutation"
        if (
            len(segments) == 8
            and segments[4] == "content-items"
            and segments[6]
            in {
                "translations",
                "relations",
            }
        ):
            resource_type = (
                "content_item_translation"
                if segments[6] == "translations"
                else "item_relation"
            )
            prefix = (
                "CONTENT_ITEM_TRANSLATION"
                if resource_type == "content_item_translation"
                else "ITEM_RELATION"
            )
            if method in {"PATCH", "DELETE"}:
                return (
                    resource_type,
                    f"{prefix}_{'UPDATED' if method == 'PATCH' else 'DELETED'}",
                    "mutation" if method == "PATCH" else "delete",
                )
        if (
            len(segments) == 7
            and segments[4] == "collection-views"
            and segments[5] == "types"
        ):
            if method == "POST":
                return "collection_view", "COLLECTION_VIEW_CREATED", "mutation"
        if len(segments) == 6 and segments[4] == "collection-views":
            if method in {"PATCH", "DELETE"}:
                return (
                    "collection_view",
                    "COLLECTION_VIEW_UPDATED"
                    if method == "PATCH"
                    else "COLLECTION_VIEW_DELETED",
                    "mutation" if method == "PATCH" else "delete",
                )
        if len(segments) == 5 and segments[4] == "pages" and method == "POST":
            return "page", "PAGE_CREATED", "mutation"
    return None


def _record_semantic_audit_expectation(
    *,
    token: str,
    path: str,
    method: str,
    body: dict[str, Any],
    key: str,
    status: int,
    document: dict[str, Any],
) -> None:
    contract = _semantic_contract(path, method, status)
    if contract is None:
        return
    context = _CAPABILITY_CONTEXTS.get(token)
    if context is None:
        raise ProofFailure("semantic-audit-capability-context-missing")
    resource_type, action, quota_kind = contract
    record = document.get("record")
    if not isinstance(record, dict):
        raise ProofFailure("semantic-audit-record-missing")
    operation_id = _require_uuid(document.get("operation_id"), f"{key}-operation")
    resource_id = _require_uuid(record.get("id"), f"{key}-resource")
    digest_payload = json.dumps(
        {
            "method": method,
            "path": path,
            "body": _canonical_request_body(path, method, body),
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(digest_payload.encode("utf-8")).hexdigest()
    workspace_id, capability_id, site_id = context
    _EXPECTED_SEMANTIC_AUDIT.append(
        {
            "capability_id": capability_id,
            "workspace_id": workspace_id,
            "site_id": site_id,
            "operation_id": operation_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "request_digest": digest,
            "response_status": status,
            "action": action,
            "http_method": method,
            "quota_kind": quota_kind,
            "idempotency_key": key,
        }
    )


def _canonical_request_body(
    path: str, method: str, body: dict[str, Any]
) -> dict[str, Any]:
    """Mirror the production Pydantic model defaults used for request digests."""

    normalized = dict(body)
    contract = _semantic_contract(path, method, 200)
    if contract is None:
        return normalized
    resource_type, action, _quota_kind = contract
    defaults: dict[str, Any] = {}
    if action == "FIELD_DEFINITION_CREATED":
        defaults = {
            "required": False,
            "localized": False,
            "cardinality": 1,
            "position": 0,
            "validation": {},
            "ui_options": {},
        }
    elif action == "ITEM_RELATION_CREATED":
        defaults = {"position": 0, "metadata": {}}
    elif action == "COLLECTION_VIEW_CREATED":
        defaults = {"definition_version": None}
    elif action == "CONTENT_TYPE_UPDATED":
        defaults = {"slug_pattern": None, "settings": None}
    elif action == "FIELD_DEFINITION_UPDATED":
        defaults = {
            "required": None,
            "localized": None,
            "cardinality": None,
            "position": None,
            "validation": None,
            "ui_options": None,
            "expected_row_version": None,
        }
    elif action == "CONTENT_ITEM_UPDATED":
        defaults = {"status": None, "values": None}
    elif action == "CONTENT_ITEM_TRANSLATION_UPDATED":
        defaults = {"locale": None}
    elif action == "ITEM_RELATION_UPDATED":
        defaults = {"target_item_id": None}
    elif action == "COLLECTION_VIEW_UPDATED":
        defaults = {
            "filter_spec": None,
            "sort_spec": None,
            "projection_spec": None,
            "definition_version": None,
        }
    if resource_type == "content_type" and action == "CONTENT_TYPE_CREATED":
        defaults = {"labels": {}, "settings": {}}
    if resource_type == "content_item" and action == "CONTENT_ITEM_CREATED":
        defaults = {"status": "DRAFT", "values": {}}
    if resource_type == "page" and action == "PAGE_CREATED":
        defaults = {
            "status": "DRAFT",
            "locale": "en",
            "parent_id": None,
            "route_template": None,
        }
    if (
        resource_type == "content_item_translation"
        and action == "CONTENT_ITEM_TRANSLATION_CREATED"
    ):
        defaults = {"localized_values": {}}
    for key, value in defaults.items():
        normalized.setdefault(key, value)
    return normalized


def _mutation(
    client: PublicClient,
    token: str,
    path: str,
    body: dict[str, Any],
    key: str,
    *,
    status: int = 201,
) -> dict[str, Any]:
    response = client.request(
        path,
        method="POST",
        body=body,
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
    )
    document = _json(response, status=status, label=key)
    record = document.get("record")
    if not isinstance(record, dict):
        raise ProofFailure(f"{key}-record-missing")
    _require_uuid(record.get("id"), f"{key}-record")
    _require_uuid(document.get("operation_id"), f"{key}-operation")
    _record_semantic_audit_expectation(
        token=token,
        path=path,
        method="POST",
        body=body,
        key=key,
        status=status,
        document=document,
    )
    return document


def _request_mutation(
    client: PublicClient,
    token: str,
    path: str,
    body: dict[str, Any],
    key: str,
    *,
    method: str = "PATCH",
    status: int = 200,
) -> dict[str, Any]:
    response = client.request(
        path,
        method=method,
        body=body,
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key},
    )
    document = _json(response, status=status, label=key)
    record = document.get("record")
    if not isinstance(record, dict):
        raise ProofFailure(f"{key}-record-missing")
    _require_uuid(record.get("id"), f"{key}-record")
    _require_uuid(document.get("operation_id"), f"{key}-operation")
    _record_semantic_audit_expectation(
        token=token,
        path=path,
        method=method,
        body=body,
        key=key,
        status=status,
        document=document,
    )
    return document


def _agent_request(
    client: PublicClient,
    token: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    key: str | None = None,
    status: int = 200,
    label: str,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return _json(
        client.request(path, method=method, body=body, headers=headers),
        status=status,
        label=label,
    )


def _agent_list(
    client: PublicClient, token: str, path: str, *, label: str
) -> list[dict[str, Any]]:
    return _list(
        client.request(path, headers={"Authorization": f"Bearer {token}"}),
        status=200,
        label=label,
    )


def _create_workspace(
    client: PublicClient,
    site_id: str,
    csrf: str,
    body: dict[str, Any],
    key: str,
) -> str:
    response = client.request(
        f"/api/control/v1/sites/{site_id}/workspaces/",
        method="POST",
        body=body,
        headers={"X-CSRF-Token": csrf, "Idempotency-Key": key},
    )
    return _require_uuid(
        _json(response, status=201, label=key).get("workspace_id"), key
    )


def _issue_capability(
    client: PublicClient,
    site_id: str,
    workspace_id: str,
    csrf: str,
    key: str,
) -> tuple[str, str]:
    path = f"/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/capabilities/"
    response = client.request(
        path,
        method="POST",
        headers={"X-CSRF-Token": csrf, "Idempotency-Key": key},
    )
    document = _json(response, status=201, label=key)
    token = document.get("token")
    if not isinstance(token, str) or not token.startswith("sas2_"):
        raise ProofFailure(f"{key}-token-missing")
    capability_id = document.get("capability_id")
    if not isinstance(capability_id, str) or not re.fullmatch(
        r"[0-9a-f]{16}", capability_id
    ):
        raise ProofFailure(f"{key}-id-invalid")
    _CAPABILITY_CONTEXTS[token] = (workspace_id, capability_id, site_id)
    return token, capability_id


def _revoke_capability(
    client: PublicClient,
    site_id: str,
    workspace_id: str,
    capability_id: str,
) -> None:
    response = client.request(
        f"/api/control/v1/sites/{site_id}/workspaces/{workspace_id}/capabilities/{capability_id}/revoke",
        method="POST",
        headers={"X-CSRF-Token": client.csrf_token() or ""},
    )
    document = _json(response, status=200, label="capability-revoke")
    if document.get("status") != "revoked":
        raise ProofFailure("capability-revoke-invalid")


def _compose(project: str, action: str, service: str) -> None:
    try:
        result = subprocess.run(
            ["docker", "compose", "-p", project, action, service],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError as error:
        raise ProofFailure("compose-action-unavailable") from error
    if result.returncode != 0:
        raise ProofFailure(f"compose-{action}-{service}-failed")


def _sql(project: str, query: str) -> str:
    try:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-p",
                project,
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "postgres",
                "-d",
                "slaif",
                "-Atqc",
                query,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise ProofFailure("neutral-sql-unavailable") from error
    if result.returncode != 0:
        raise ProofFailure("neutral-sql-assertion-failed")
    return result.stdout.strip()


def _assert_exact_semantic_audit(project: str) -> None:
    """Check every successful semantic mutation and its durable siblings."""

    workspaces = sorted({context[0] for context in _CAPABILITY_CONTEXTS.values()})
    if not workspaces or not _EXPECTED_SEMANTIC_AUDIT:
        raise ProofFailure("semantic-audit-expectations-empty")
    if any(not re.fullmatch(r"[0-9a-f-]{36}", value) for value in workspaces):
        raise ProofFailure("semantic-audit-workspace-invalid")
    workspace_sql = ",".join(f"'{value}'::uuid" for value in workspaces)
    actual_raw = _sql(
        project,
        "SELECT coalesce(json_agg(json_build_object("
        "'capability_id',c.public_id,"
        "'workspace_id',a.workspace_id::text,"
        "'site_id',a.site_id::text,"
        "'operation_id',a.operation_id::text,"
        "'resource_type',a.resource_type,"
        "'resource_id',a.resource_id::text,"
        "'request_digest',a.request_digest,"
        "'response_status',a.response_status,"
        "'action',a.action,"
        "'http_method',a.http_method,"
        "'quota_kind',a.quota_kind,"
        "'idempotency_key',i.idempotency_key,"
        "'idempotency_completed',i.status_code IS NOT NULL,"
        "'cow_operation',exists(SELECT 1 FROM agentcow.get_cow_session_operations("
        "'content',a.workspace_id) AS cow(operation_id) "
        "WHERE cow.operation_id=a.operation_id)"
        ") ORDER BY a.occurred_at,a.operation_id),'[]'::json) "
        f"FROM audit.agent_mutation a "
        f"JOIN control.capability c ON c.id=a.capability_id "
        f"JOIN control.agent_idempotency i ON i.capability_id=a.capability_id "
        f"AND i.workspace_id=a.workspace_id AND i.operation_id=a.operation_id "
        f"WHERE a.workspace_id IN ({workspace_sql}) AND a.http_method IS NOT NULL",
    )
    try:
        actual = json.loads(actual_raw or "[]")
    except json.JSONDecodeError as error:
        raise ProofFailure("semantic-audit-json-invalid") from error
    if not isinstance(actual, list):
        raise ProofFailure("semantic-audit-result-invalid")
    expected = [
        {**event, "idempotency_completed": True, "cow_operation": True}
        for event in _EXPECTED_SEMANTIC_AUDIT
    ]

    def canonical(event: object) -> str:
        return json.dumps(event, sort_keys=True, separators=(",", ":"))

    if Counter(canonical(event) for event in actual) != Counter(
        canonical(event) for event in expected
    ):
        actual_counts = Counter(canonical(event) for event in actual)
        expected_counts = Counter(canonical(event) for event in expected)

        def summary(event: str) -> str:
            decoded = json.loads(event)
            return ":".join(
                str(decoded.get(key))
                for key in (
                    "action",
                    "http_method",
                    "quota_kind",
                    "idempotency_key",
                )
            )

        missing = sorted(
            summary(event) for event in (expected_counts - actual_counts).elements()
        )
        extra = sorted(
            summary(event) for event in (actual_counts - expected_counts).elements()
        )
        raise ProofFailure(
            "semantic-audit-exact-multiset-mismatch"
            f" expected={len(expected)} actual={len(actual)}"
            f" missing={','.join(missing)} extra={','.join(extra)}"
        )


def _wait_agent_ready(client: PublicClient) -> None:
    for _attempt in range(30):
        try:
            response = client.request("/api/agent/health/ready")
        except ProofFailure:
            response = None
        if response is not None and _is_ready_service(response, "agent-api"):
            return
        time.sleep(1)
    raise ProofFailure("agent-readiness-timeout")


def _wait_public_outage(client: PublicClient, path: str, label: str) -> None:
    for _attempt in range(15):
        try:
            response = client.request(path)
        except ProofFailure:
            return
        if response.status in {502, 503, 504}:
            return
        time.sleep(1)
    raise ProofFailure(f"{label}-still-available")


def run_acceptance(project: str) -> None:
    if not re.fullmatch(r"slaif(?:007|009|010|071)[a-z0-9]+", project):
        raise ProofFailure("unsafe-project-name")
    _CAPABILITY_CONTEXTS.clear()
    _EXPECTED_SEMANTIC_AUDIT.clear()
    client = PublicClient()
    agent_outage = False
    nginx_outage = False
    tag = uuid4().hex[:12]
    primary_workspace = primary_capability = observer_workspace = (
        observer_capability
    ) = ""
    lower_workspace = lower_capability = constrained_workspace = (
        constrained_capability
    ) = ""
    quota_workspace = quota_capability = quota_recovery_capability = ""
    primary_token = observer_token = lower_token = constrained_token = ""
    quota_token = quota_recovery_token = ""
    try:
        _json(
            client.request(
                "/api/control/v1/login",
                method="POST",
                body={"username": FIXTURE_USERNAME, "password": FIXTURE_PASSWORD},
            ),
            status=200,
            label="login",
        )
        csrf = client.csrf_token()
        if not csrf:
            raise ProofFailure("csrf-cookie-missing")
        sites = _list(
            client.request("/api/control/v1/me/sites"), status=200, label="sites"
        )
        demo = next((item for item in sites if item.get("site_key") == "demo"), None)
        other = next((item for item in sites if item.get("site_key") != "demo"), None)
        if demo is None or other is None:
            raise ProofFailure("demo-or-other-site-missing")
        site_id = _require_uuid(demo.get("site_id"), "demo-site")
        other_site_id = _require_uuid(other.get("site_id"), "other-site")
        sites_before = json.dumps(sites, sort_keys=True, separators=(",", ":"))
        other_workspaces_path = f"/api/control/v1/sites/{other_site_id}/workspaces/"
        other_workspaces_before = _list(
            client.request(other_workspaces_path),
            status=200,
            label="other-workspaces-before",
        )

        contract_path = ROOT / "contracts/openapi/agent-v1.json"
        contract_bytes = contract_path.read_bytes()
        contract_response = client.request("/api/agent/v1/openapi.json")
        if contract_response.status != 200 or contract_response.body != contract_bytes:
            raise ProofFailure("public-openapi-bytes-drift")
        contract = json.loads(contract_bytes)
        required_paths = {
            "/api/agent/v1/session",
            "/api/agent/v1/permissions",
            "/api/agent/v1/content-model/primitives",
            "/api/agent/v1/content-model/types",
            "/api/agent/v1/content-items/types/{type_id}",
            "/api/agent/v1/content-items/{item_id}/translations",
            "/api/agent/v1/content-items/{item_id}/relations",
            "/api/agent/v1/collection-views/types/{type_id}",
            "/api/agent/v1/pages/",
        }
        if not required_paths <= set(contract["paths"]):
            raise ProofFailure("public-openapi-route-inventory-incomplete")

        primary_body = {
            "title": f"OAP 076-y public acceptance {tag}",
            "task_description": "Bounded public Agent acceptance proof",
            "delegation_preset": "L4_SITE_ARCHITECT",
            "duration_hours": 1,
            "request_quota": 1000,
            "mutation_quota": 200,
            "delete_quota": 50,
            "upload_quota": 5,
            "browser_quota": 5,
            "resource_constraints": {"delete_enabled": True, "max_deletes": 50},
        }
        primary_workspace = _create_workspace(
            client, site_id, csrf, primary_body, f"oap-076y-primary-{tag}"
        )
        primary_token, primary_capability = _issue_capability(
            client,
            site_id,
            primary_workspace,
            csrf,
            f"oap-076y-primary-cap-{tag}",
        )
        replay = client.request(
            f"/api/control/v1/sites/{site_id}/workspaces/{primary_workspace}/capabilities/",
            method="POST",
            headers={
                "X-CSRF-Token": csrf,
                "Idempotency-Key": f"oap-076y-primary-cap-{tag}",
            },
        )
        replay_document = _json(replay, status=200, label="capability-replay")
        if "token" in replay_document:
            raise ProofFailure("capability-token-redisplayed")

        observer_body = {
            "title": f"OAP 076-y observer {tag}",
            "task_description": "Bounded unchanged-workspace observer",
            "delegation_preset": "L4_SITE_ARCHITECT",
            "duration_hours": 1,
            "request_quota": 500,
            "mutation_quota": 20,
            "delete_quota": 5,
            "upload_quota": 0,
            "browser_quota": 0,
        }
        observer_workspace = _create_workspace(
            client, site_id, csrf, observer_body, f"oap-076y-observer-{tag}"
        )
        observer_token, observer_capability = _issue_capability(
            client,
            site_id,
            observer_workspace,
            csrf,
            f"oap-076y-observer-cap-{tag}",
        )

        session = _agent_request(
            client, primary_token, "/api/agent/v1/session", label="session"
        )
        if (
            session.get("site_id") != site_id
            or session.get("workspace_id") != primary_workspace
        ):
            raise ProofFailure("session-binding-invalid")
        permissions = _agent_request(
            client, primary_token, "/api/agent/v1/permissions", label="permissions"
        )
        required_scopes = {
            "site:read",
            "content-model:create",
            "content-model:read",
            "content-model:write",
            "content-model:delete",
            "field-definition:create",
            "field-definition:write",
            "field-definition:delete",
            "content-item:create",
            "content-item:read",
            "content-item:write",
            "content-item:delete",
            "translation:read",
            "translation:write",
            "relationship:write",
            "collection-view:read",
            "collection-view:create",
            "collection-view:write",
            "collection-view:delete",
            "page:create",
            "page:read",
            "composition:read",
            "component-structure:create",
            "validation:read",
        }
        if not required_scopes <= set(permissions.get("scopes", [])):
            raise ProofFailure("permissions-incomplete")
        primitives = _list(
            client.request(
                "/api/agent/v1/content-model/primitives",
                headers={"Authorization": f"Bearer {primary_token}"},
            ),
            status=200,
            label="primitives",
        )
        if {item.get("primitive") for item in primitives} != FIELD_PRIMITIVES or any(
            item.get("executable") is not False for item in primitives
        ):
            raise ProofFailure("primitive-discovery-invalid")

        baseline_types = _agent_list(
            client,
            primary_token,
            "/api/agent/v1/content-model/types",
            label="baseline-types",
        )
        observer_baseline_types = _agent_list(
            client,
            observer_token,
            "/api/agent/v1/content-model/types",
            label="observer-baseline",
        )
        if baseline_types != observer_baseline_types:
            raise ProofFailure("workspace-baseline-drift")

        target_key = f"oap-target-{tag}"
        source_key = f"oap-source-{tag}"
        target_type_body = {
            "key": target_key,
            "labels": {"en": "OAP target"},
            "slug_pattern": f"/{target_key}/{{slug}}",
            "settings": {},
        }
        target_create = _mutation(
            client,
            primary_token,
            "/api/agent/v1/content-model/types",
            target_type_body,
            f"oap-type-target-{tag}",
        )
        target_type_id = _require_uuid(target_create["record"]["id"], "target-type")
        replay_create = client.request(
            "/api/agent/v1/content-model/types",
            method="POST",
            body=target_type_body,
            headers={
                "Authorization": f"Bearer {primary_token}",
                "Idempotency-Key": f"oap-type-target-{tag}",
            },
        )
        if _json(replay_create, status=201, label="type-replay") != target_create:
            raise ProofFailure("type-replay-mismatch")
        mismatch = client.request(
            "/api/agent/v1/content-model/types",
            method="POST",
            body={**target_type_body, "labels": {"en": "changed"}},
            headers={
                "Authorization": f"Bearer {primary_token}",
                "Idempotency-Key": f"oap-type-target-{tag}",
            },
        )
        if mismatch.status != 409:
            raise ProofFailure(f"type-idempotency-mismatch-{mismatch.status}")

        source_create = _mutation(
            client,
            primary_token,
            "/api/agent/v1/content-model/types",
            {
                "key": source_key,
                "labels": {"en": "OAP source"},
                "slug_pattern": f"/{source_key}/{{slug}}",
                "settings": {},
            },
            f"oap-type-source-{tag}",
        )
        source_type_id = _require_uuid(source_create["record"]["id"], "source-type")
        target_field = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{target_type_id}/fields",
            {"key": "title", "label": "Title", "field_type": "short_text"},
            f"oap-field-target-{tag}",
        )
        target_field_id = _require_uuid(target_field["record"]["id"], "target-field")
        source_title = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{source_type_id}/fields",
            {
                "key": "title",
                "label": "Title",
                "field_type": "short_text",
                "localized": True,
            },
            f"oap-field-source-title-{tag}",
        )
        source_title_id = _require_uuid(
            source_title["record"]["id"], "source-title-field"
        )
        source_reference = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{source_type_id}/fields",
            {
                "key": "related",
                "label": "Related",
                "field_type": "reference",
                "validation": {"target_type_id": target_type_id},
            },
            f"oap-field-source-reference-{tag}",
        )
        source_reference_id = _require_uuid(
            source_reference["record"]["id"], "source-reference-field"
        )
        target_item = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-items/types/{target_type_id}",
            {
                "type_id": target_type_id,
                "slug": f"target-{tag}",
                "status": "DRAFT",
                "values": {"title": "Target"},
            },
            f"oap-item-target-{tag}",
        )
        target_item_id = _require_uuid(target_item["record"]["id"], "target-item")
        source_item = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-items/types/{source_type_id}",
            {
                "type_id": source_type_id,
                "slug": f"source-{tag}",
                "status": "DRAFT",
                "values": {},
            },
            f"oap-item-source-{tag}",
        )
        source_item_id = _require_uuid(source_item["record"]["id"], "source-item")

        translation_path = f"/api/agent/v1/content-items/{source_item_id}/translations"
        translation = _mutation(
            client,
            primary_token,
            translation_path,
            {"locale": "en-US", "localized_values": {"title": "Source"}},
            f"oap-translation-create-{tag}",
        )
        translation_id = _require_uuid(translation["record"]["id"], "translation")
        _agent_list(client, primary_token, translation_path, label="translation-list")
        _agent_request(
            client,
            primary_token,
            f"{translation_path}/{translation_id}",
            label="translation-get",
        )
        translation_update = _request_mutation(
            client,
            primary_token,
            f"{translation_path}/{translation_id}",
            {
                "localized_values": {"title": "Updated source"},
                "expected_row_version": 1,
            },
            f"oap-translation-update-{tag}",
        )
        if translation_update["record"].get("row_version") != 2:
            raise ProofFailure("translation-version-invalid")

        relation_path = f"/api/agent/v1/content-items/{source_item_id}/relations"
        relation = _mutation(
            client,
            primary_token,
            relation_path,
            {
                "field_definition_id": source_reference_id,
                "target_item_id": target_item_id,
            },
            f"oap-relation-create-{tag}",
        )
        relation_id = _require_uuid(relation["record"]["id"], "relation")
        _agent_list(client, primary_token, relation_path, label="relation-list")
        _agent_request(
            client,
            primary_token,
            f"{relation_path}/{relation_id}",
            label="relation-get",
        )
        relation_update = _request_mutation(
            client,
            primary_token,
            f"{relation_path}/{relation_id}",
            {
                "position": 1,
                "metadata": {"proof": "updated"},
                "expected_row_version": 1,
            },
            f"oap-relation-update-{tag}",
        )
        if relation_update["record"].get("row_version") != 2:
            raise ProofFailure("relation-version-invalid")

        view_path = f"/api/agent/v1/collection-views/types/{target_type_id}"
        view = _mutation(
            client,
            primary_token,
            view_path,
            {
                "type_id": target_type_id,
                "key": "all",
                "filter_spec": {},
                "sort_spec": {"field": "slug", "direction": "asc"},
                "projection_spec": {},
                "pagination_spec": {"limit": 10, "offset": 0},
            },
            f"oap-view-create-{tag}",
        )
        view_id = _require_uuid(view["record"]["id"], "view")
        _agent_list(client, primary_token, view_path, label="view-list")
        _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/collection-views/{view_id}",
            label="view-get",
        )
        view_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/collection-views/{view_id}",
            {"pagination_spec": {"limit": 5, "offset": 0}, "expected_row_version": 1},
            f"oap-view-update-{tag}",
        )
        if view_update["record"].get("row_version") != 2:
            raise ProofFailure("view-version-invalid")

        page = _mutation(
            client,
            primary_token,
            "/api/agent/v1/pages/",
            {
                "slug": f"oap-{tag}",
                "title": "OAP acceptance",
                "status": "DRAFT",
                "locale": "en",
            },
            f"oap-page-create-{tag}",
        )
        page_id = _require_uuid(page["record"]["id"], "page")
        component = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{page_id}/components",
            {
                "component_type": "Heading",
                "slot_key": "default",
                "order_key": 0,
                "props": {"text": "OAP acceptance", "level": 2},
            },
            f"oap-component-create-{tag}",
        )
        component_id = _require_uuid(component["record"]["id"], "component")
        current_types = _agent_list(
            client,
            primary_token,
            "/api/agent/v1/content-model/types",
            label="type-list",
        )
        if not {target_type_id, source_type_id} <= {
            item.get("id") for item in current_types
        }:
            raise ProofFailure("type-list-missing-created")
        source_fields = _agent_list(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{source_type_id}/fields",
            label="field-list",
        )
        if {source_title_id, source_reference_id} - {
            item.get("id") for item in source_fields
        }:
            raise ProofFailure("field-list-missing-created")
        _agent_list(
            client,
            primary_token,
            f"/api/agent/v1/content-items/types/{source_type_id}",
            label="item-list",
        )
        _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/content-items/{source_item_id}",
            label="item-get",
        )
        _agent_list(client, primary_token, "/api/agent/v1/pages/", label="page-list")
        components = _agent_list(
            client,
            primary_token,
            f"/api/agent/v1/pages/{page_id}/components",
            label="component-list",
        )
        if component_id not in {item.get("id") for item in components}:
            raise ProofFailure("component-list-missing-created")

        source_item_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-items/{source_item_id}",
            {"slug": f"source-updated-{tag}", "expected_row_version": 1},
            f"oap-item-update-{tag}",
        )
        if source_item_update["record"].get("row_version") != 2:
            raise ProofFailure("item-version-invalid")
        stale_item = client.request(
            f"/api/agent/v1/content-items/{source_item_id}",
            method="PATCH",
            body={"slug": f"stale-{tag}", "expected_row_version": 1},
            headers={
                "Authorization": f"Bearer {primary_token}",
                "Idempotency-Key": f"oap-item-stale-{tag}",
            },
        )
        if stale_item.status != 409:
            raise ProofFailure(f"stale-item-status-{stale_item.status}")

        source_title_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{source_type_id}/fields/{source_title_id}",
            {"label": "Updated title", "expected_definition_version": 1},
            f"oap-field-update-{tag}",
        )
        source_title_version = source_title_update["record"].get("definition_version")
        if source_title_version != 2:
            raise ProofFailure("field-definition-version-invalid")
        source_type = _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{source_type_id}",
            label="source-type",
        )
        source_type_version = source_type.get("definition_version")
        if not isinstance(source_type_version, int):
            raise ProofFailure("type-definition-version-missing")
        source_item_after_schema = _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/content-items/{source_item_id}",
            label="item-schema-version",
        )
        if (
            source_item_after_schema.get("type_definition_version", source_type_version)
            >= source_type_version
        ):
            raise ProofFailure("item-definition-invalidation-missing")
        type_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{source_type_id}",
            {
                "labels": {"en": "Updated OAP source"},
                "expected_definition_version": source_type_version,
            },
            f"oap-type-update-{tag}",
        )
        if type_update["record"].get("definition_version") != source_type_version + 1:
            raise ProofFailure("type-definition-update-invalid")

        # Authorization, identity, path, resource, dependency, and public-edge negatives.
        lower_body = {
            "title": f"OAP 076-y lower {tag}",
            "task_description": "Bounded lower-scope negative proof",
            "delegation_preset": "L1_CONTENT_EDITOR",
            "duration_hours": 1,
            "request_quota": 100,
            "mutation_quota": 10,
            "delete_quota": 1,
            "upload_quota": 0,
            "browser_quota": 0,
        }
        lower_workspace = _create_workspace(
            client, site_id, csrf, lower_body, f"oap-076y-lower-{tag}"
        )
        lower_token, lower_capability = _issue_capability(
            client, site_id, lower_workspace, csrf, f"oap-076y-lower-cap-{tag}"
        )
        lower_create = client.request(
            "/api/agent/v1/content-model/types",
            method="POST",
            body={
                "key": f"oap-denied-{tag}",
                "labels": {"en": "Denied"},
                "slug_pattern": "/denied/{slug}",
                "settings": {},
            },
            headers={
                "Authorization": f"Bearer {lower_token}",
                "Idempotency-Key": f"oap-lower-denied-{tag}",
            },
        )
        if lower_create.status != 403:
            raise ProofFailure(f"lower-scope-status-{lower_create.status}")
        constrained_body = {
            **primary_body,
            "title": f"OAP 076-y constrained {tag}",
            "resource_constraints": {
                "allowed_type_ids": [target_type_id],
                "allowed_type_keys": [target_key],
                "delete_enabled": True,
                "max_deletes": 10,
            },
        }
        constrained_workspace = _create_workspace(
            client, site_id, csrf, constrained_body, f"oap-076y-constrained-{tag}"
        )
        constrained_token, constrained_capability = _issue_capability(
            client,
            site_id,
            constrained_workspace,
            csrf,
            f"oap-076y-constrained-cap-{tag}",
        )
        quota_body = {
            "title": f"OAP 076-y quota {tag}",
            "task_description": "Bounded public quota proof",
            "delegation_preset": "L4_SITE_ARCHITECT",
            "duration_hours": 1,
            "request_quota": 100,
            "mutation_quota": 2,
            "delete_quota": 2,
            "upload_quota": 0,
            "browser_quota": 0,
            "resource_constraints": {"delete_enabled": True, "max_deletes": 1},
        }
        quota_workspace = _create_workspace(
            client, site_id, csrf, quota_body, f"oap-076y-quota-{tag}"
        )
        quota_token, quota_capability = _issue_capability(
            client, site_id, quota_workspace, csrf, f"oap-076y-quota-cap-{tag}"
        )
        quota_type_body = {
            "labels": {"en": "Quota proof"},
            "slug_pattern": "/quota/{slug}",
            "settings": {},
        }
        quota_one = _mutation(
            client,
            quota_token,
            "/api/agent/v1/content-model/types",
            {"key": f"oap-quota-one-{tag}", **quota_type_body},
            f"oap-quota-type-one-{tag}",
        )
        quota_one_id = _require_uuid(quota_one["record"]["id"], "quota-type-one")
        quota_two = _mutation(
            client,
            quota_token,
            "/api/agent/v1/content-model/types",
            {"key": f"oap-quota-two-{tag}", **quota_type_body},
            f"oap-quota-type-two-{tag}",
        )
        quota_two_id = _require_uuid(quota_two["record"]["id"], "quota-type-two")
        quota_mutation_exceeded = client.request(
            "/api/agent/v1/content-model/types",
            method="POST",
            body={"key": f"oap-quota-three-{tag}", **quota_type_body},
            headers={
                "Authorization": f"Bearer {quota_token}",
                "Idempotency-Key": f"oap-quota-type-three-{tag}",
            },
        )
        if quota_mutation_exceeded.status != 429:
            raise ProofFailure(
                f"mutation-quota-status-{quota_mutation_exceeded.status}"
            )
        _request_mutation(
            client,
            quota_token,
            f"/api/agent/v1/content-model/types/{quota_one_id}",
            {"expected_definition_version": 1},
            f"oap-quota-delete-one-{tag}",
            method="DELETE",
        )
        quota_delete_exceeded = client.request(
            f"/api/agent/v1/content-model/types/{quota_two_id}",
            method="DELETE",
            body={"expected_definition_version": 1},
            headers={
                "Authorization": f"Bearer {quota_token}",
                "Idempotency-Key": f"oap-quota-delete-two-{tag}",
            },
        )
        if quota_delete_exceeded.status != 429:
            raise ProofFailure(
                f"max-delete-quota-status-{quota_delete_exceeded.status}"
            )
        quota_recovery_token, quota_recovery_capability = _issue_capability(
            client,
            site_id,
            quota_workspace,
            csrf,
            f"oap-076y-quota-recovery-cap-{tag}",
        )
        _request_mutation(
            client,
            quota_recovery_token,
            f"/api/agent/v1/content-model/types/{quota_two_id}",
            {"expected_definition_version": 1},
            f"oap-quota-recovery-delete-two-{tag}",
            method="DELETE",
        )
        wrong_resource = client.request(
            f"/api/agent/v1/content-model/types/{source_type_id}",
            headers={"Authorization": f"Bearer {constrained_token}"},
        )
        if wrong_resource.status != 403:
            raise ProofFailure(f"resource-constraint-status-{wrong_resource.status}")
        if client.request("/api/control/v1/session").status != 200:
            raise ProofFailure("authenticated-control-session-lost")
        anonymous = PublicClient().request("/api/control/v1/session")
        if anonymous.status != 401:
            raise ProofFailure(f"anonymous-control-status-{anonymous.status}")
        if client.request("/api/agent/v1/session").status != 401:
            raise ProofFailure("missing-agent-auth-not-rejected")
        if (
            client.request(
                "/api/agent/v1/content-model/types/not-a-uuid",
                headers={"Authorization": f"Bearer {primary_token}"},
            ).status
            != 422
        ):
            raise ProofFailure("malformed-uuid-not-rejected")
        if (
            client.request(
                f"/api/agent/v1/content-model/types/{other_site_id}",
                headers={"Authorization": f"Bearer {primary_token}"},
            ).status
            != 404
        ):
            raise ProofFailure("wrong-site-uuid-not-confined")
        if (
            client.request(
                "/api/agent/v1/publish",
                headers={"Authorization": f"Bearer {primary_token}"},
            ).status
            != 404
        ):
            raise ProofFailure("publication-route-exposed")
        target_type_before_dependency = _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{target_type_id}",
            label="dependency-type-read",
        )
        dependency = client.request(
            f"/api/agent/v1/content-model/types/{target_type_id}",
            method="DELETE",
            body={
                "expected_definition_version": target_type_before_dependency[
                    "definition_version"
                ]
            },
            headers={
                "Authorization": f"Bearer {primary_token}",
                "Idempotency-Key": f"oap-dependent-type-delete-{tag}",
            },
        )
        if dependency.status != 422:
            raise ProofFailure(f"dependency-delete-status-{dependency.status}")
        try:
            dependency_document = json.loads(dependency.body)
        except json.JSONDecodeError as error:
            raise ProofFailure("dependency-delete-response-invalid") from error
        if dependency_document.get("error", {}).get("code") != "TYPE_DEPENDENCIES":
            raise ProofFailure("dependency-delete-error-code-invalid")

        _compose(project, "restart", "agent-api")
        agent_outage = False
        _wait_agent_ready(client)
        _agent_request(
            client,
            primary_token,
            "/api/agent/v1/session",
            label="agent-restart-session",
        )
        _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/content-model/types/{target_type_id}",
            label="agent-restart-read",
        )
        _compose(project, "stop", "nginx")
        nginx_outage = True
        _wait_public_outage(client, "/api/agent/health/ready", "nginx-outage")
        _compose(project, "start", "nginx")
        nginx_outage = False
        _wait_agent_ready(client)
        _agent_request(
            client,
            primary_token,
            "/api/agent/v1/session",
            label="nginx-recovery-session",
        )

        # Dependency-safe deletion and tombstone reads.
        for path, body, key in (
            (
                f"{relation_path}/{relation_id}",
                {"expected_row_version": 2},
                f"oap-relation-delete-{tag}",
            ),
            (
                f"/api/agent/v1/collection-views/{view_id}",
                {"expected_row_version": 2},
                f"oap-view-delete-{tag}",
            ),
            (
                f"{translation_path}/{translation_id}",
                {"expected_row_version": 2},
                f"oap-translation-delete-{tag}",
            ),
            (
                f"/api/agent/v1/content-items/{source_item_id}",
                {"expected_row_version": 2},
                f"oap-source-item-delete-{tag}",
            ),
            (
                f"/api/agent/v1/content-items/{target_item_id}",
                {"expected_row_version": 1},
                f"oap-target-item-delete-{tag}",
            ),
        ):
            _request_mutation(client, primary_token, path, body, key, method="DELETE")
        for type_id in (source_type_id, target_type_id):
            fields = _agent_list(
                client,
                primary_token,
                f"/api/agent/v1/content-model/types/{type_id}/fields",
                label="delete-field-list",
            )
            for field in fields:
                field_id = _require_uuid(field.get("id"), "delete-field")
                _request_mutation(
                    client,
                    primary_token,
                    f"/api/agent/v1/content-model/types/{type_id}/fields/{field_id}",
                    {"expected_definition_version": field["definition_version"]},
                    f"oap-field-delete-{tag}-{field_id}",
                    method="DELETE",
                )
            current_type = _agent_request(
                client,
                primary_token,
                f"/api/agent/v1/content-model/types/{type_id}",
                label="delete-type-read",
            )
            _request_mutation(
                client,
                primary_token,
                f"/api/agent/v1/content-model/types/{type_id}",
                {"expected_definition_version": current_type["definition_version"]},
                f"oap-type-delete-{tag}-{type_id}",
                method="DELETE",
            )
            if (
                client.request(
                    f"/api/agent/v1/content-model/types/{type_id}",
                    headers={"Authorization": f"Bearer {primary_token}"},
                ).status
                != 404
            ):
                raise ProofFailure("deleted-type-tombstone-visible")
        final_types = _agent_list(
            client,
            primary_token,
            "/api/agent/v1/content-model/types",
            label="final-types",
        )
        if final_types != baseline_types:
            raise ProofFailure("canonical-workspace-content-drift")
        if (
            _agent_list(
                client,
                observer_token,
                "/api/agent/v1/content-model/types",
                label="observer-final",
            )
            != observer_baseline_types
        ):
            raise ProofFailure("other-workspace-content-drift")
        sites_after = _list(
            client.request("/api/control/v1/me/sites"), status=200, label="sites-after"
        )
        if (
            json.dumps(sites_after, sort_keys=True, separators=(",", ":"))
            != sites_before
        ):
            raise ProofFailure("site-list-drift")
        if (
            _list(
                client.request(other_workspaces_path),
                status=200,
                label="other-workspaces-after",
            )
            != other_workspaces_before
        ):
            raise ProofFailure("other-site-workspace-drift")

        ids = ",".join(
            f"'{value}'::uuid"
            for value in (
                target_type_id,
                source_type_id,
                target_field_id,
                source_title_id,
                source_reference_id,
                target_item_id,
                source_item_id,
            )
        )
        for table in (
            "content_type_base",
            "field_definition_base",
            "content_item_base",
        ):
            if (
                _sql(
                    project, f"SELECT count(*) FROM content.{table} WHERE id IN ({ids})"
                )
                != "0"
            ):
                raise ProofFailure(f"canonical-{table}-changed")
        _assert_exact_semantic_audit(project)
        semantic_count_before_revoke = _sql(
            project,
            f"SELECT count(*) FROM audit.agent_mutation WHERE workspace_id='{primary_workspace}'::uuid",
        )
        idempotency_count_before_revoke = _sql(
            project,
            f"SELECT count(*) FROM control.agent_idempotency WHERE workspace_id='{primary_workspace}'::uuid",
        )
        _revoke_capability(client, site_id, primary_workspace, primary_capability)
        revoked = client.request(
            "/api/agent/v1/session",
            headers={"Authorization": f"Bearer {primary_token}"},
        )
        if revoked.status != 401:
            raise ProofFailure(f"revoked-capability-status-{revoked.status}")
        if (
            _sql(
                project,
                f"SELECT count(*) FROM audit.agent_mutation WHERE workspace_id='{primary_workspace}'::uuid",
            )
            != semantic_count_before_revoke
            or _sql(
                project,
                f"SELECT count(*) FROM control.agent_idempotency WHERE workspace_id='{primary_workspace}'::uuid",
            )
            != idempotency_count_before_revoke
        ):
            raise ProofFailure("revoked-capability-left-residue")
        _revoke_capability(client, site_id, observer_workspace, observer_capability)
        _revoke_capability(client, site_id, lower_workspace, lower_capability)
        _revoke_capability(
            client, site_id, constrained_workspace, constrained_capability
        )
        _revoke_capability(client, site_id, quota_workspace, quota_capability)
        _revoke_capability(client, site_id, quota_workspace, quota_recovery_capability)
        print(
            "public-agent-acceptance: OK "
            f"workspace={primary_workspace} types=2 fields=3 items=2 "
            "translations=1 relations=1 views=1 pages=1 components=1 "
            "openapi=exact restart=verified nginx-outage=verified "
            "crud=public quotas=mutation-429,max-delete-429 "
            "dependency-delete=422 tombstones=verified"
        )
    finally:
        if agent_outage:
            _compose(project, "start", "agent-api")
        if nginx_outage:
            _compose(project, "start", "nginx")
        primary_token = observer_token = lower_token = constrained_token = ""
        quota_token = quota_recovery_token = ""
        client.clear()
        _CAPABILITY_CONTEXTS.clear()
        _EXPECTED_SEMANTIC_AUDIT.clear()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="public_agent_acceptance")
    parser.add_argument("--project", required=True)
    arguments = parser.parse_args(argv)
    try:
        run_acceptance(arguments.project)
    except (OSError, ProofFailure, ValueError, KeyError) as error:
        print(f"public-agent-acceptance: FAILED reason={error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

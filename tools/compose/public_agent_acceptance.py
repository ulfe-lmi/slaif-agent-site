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
        if len(segments) == 6 and segments[4] == "pages":
            if method == "PATCH":
                return "page", "PAGE_UPDATED", "mutation"
            if method == "DELETE":
                return "page", "PAGE_DELETED", "delete"
            if segments[5].endswith(":move") and method == "POST":
                return "page", "PAGE_MOVED", "mutation"
            if segments[5].endswith(":restore") and method == "POST":
                return "page", "PAGE_RESTORED", "mutation"
        if len(segments) == 5 and segments[4] == "redirects" and method == "POST":
            return "redirect", "REDIRECT_CREATED", "mutation"
        if len(segments) == 6 and segments[4] == "redirects":
            if method == "PATCH":
                return "redirect", "REDIRECT_UPDATED", "mutation"
            if method == "DELETE":
                return "redirect", "REDIRECT_DELETED", "delete"
        if len(segments) == 5 and segments[4] == "locales" and method == "POST":
            return "locale", "LOCALE_CREATED", "mutation"
        if len(segments) == 6 and segments[4] == "locales":
            if method == "PATCH":
                return "locale", "LOCALE_UPDATED", "mutation"
            if method == "DELETE":
                return "locale", "LOCALE_DELETED", "delete"
        if len(segments) == 5 and segments[4] == "navigation" and method == "POST":
            return "navigation", "NAVIGATION_CREATED", "mutation"
        if len(segments) == 6 and segments[4] == "navigation":
            if method == "PATCH":
                return "navigation", "NAVIGATION_UPDATED", "mutation"
            if method == "DELETE":
                return "navigation", "NAVIGATION_DELETED", "delete"
        if (
            len(segments) == 7
            and segments[4] == "navigation"
            and segments[6] == "items"
            and method == "POST"
        ):
            return "navigation_item", "NAVIGATION_ITEM_CREATED", "mutation"
        if len(segments) == 6 and segments[4] == "navigation-items":
            if method == "PATCH":
                return "navigation_item", "NAVIGATION_ITEM_UPDATED", "mutation"
            if method == "DELETE":
                return "navigation_item", "NAVIGATION_ITEM_DELETED", "delete"
            if segments[5].endswith(":move") and method == "POST":
                return "navigation_item", "NAVIGATION_ITEM_MOVED", "mutation"
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
    elif action == "LOCALE_CREATED":
        defaults = {
            "enabled": True,
            "is_default": False,
            "position": 0,
            "metadata": {},
        }
    elif action == "LOCALE_UPDATED":
        defaults = {
            "enabled": None,
            "is_default": None,
            "position": None,
            "metadata": None,
        }
    elif action == "NAVIGATION_CREATED":
        defaults = {"labels": {}, "settings": {}}
    elif action == "NAVIGATION_UPDATED":
        defaults = {"label": None, "labels": None, "settings": None}
    elif action == "NAVIGATION_ITEM_CREATED":
        defaults = {
            "navigation_id": None,
            "parent_id": None,
            "page_id": None,
            "target_kind": "INTERNAL",
            "target_value": "/",
            "labels": {},
            "locale": None,
            "before_item_id": None,
            "after_item_id": None,
        }
    elif action == "NAVIGATION_ITEM_UPDATED":
        defaults = {
            "page_id": None,
            "target_kind": None,
            "target_value": None,
            "labels": None,
            "locale": None,
        }
    elif action == "NAVIGATION_ITEM_MOVED":
        defaults = {"parent_id": None, "before_item_id": None, "after_item_id": None}
    elif action == "REDIRECT_CREATED":
        defaults = {"status_code": 302, "locale": None}
    elif action == "REDIRECT_UPDATED":
        defaults = {
            "source_route": None,
            "target": None,
            "status_code": None,
            "locale": None,
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
    if resource_type == "page" and action == "PAGE_UPDATED":
        defaults = {
            "slug": None,
            "title": None,
            "status": None,
            "locale": None,
            "route_template": None,
        }
    if resource_type == "page" and action == "PAGE_MOVED":
        defaults = {"parent_id": None}
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


def _wait_public_not_found(client: PublicClient, path: str, label: str) -> None:
    for _attempt in range(30):
        try:
            response = client.request(path)
        except ProofFailure:
            response = None
        if response is not None and response.status == 404:
            return
        time.sleep(1)
    raise ProofFailure(f"{label}-not-404")


def _wait_preview_html(client: PublicClient, path: str, label: str) -> bytes:
    last_status: int | None = None
    for _attempt in range(30):
        try:
            response = client.request(path)
        except ProofFailure:
            response = None
        if response is not None and response.status == 200:
            return response.body
        if response is not None:
            last_status = response.status
        time.sleep(1)
    raise ProofFailure(f"{label}-not-ready-status-{last_status or 0}")


def _wait_browser_run(
    client: PublicClient, token: str, run_id: str, label: str
) -> None:
    for _attempt in range(180):
        response = client.request(
            f"/api/agent/v1/preview-runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        document = _json(response, status=200, label=label)
        state = document.get("state")
        if state in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}:
            if state != "COMPLETED":
                raise ProofFailure(f"{label}-terminal")
            return
        time.sleep(1)
    raise ProofFailure(f"{label}-timeout")


def _assert_preview_html(
    body: bytes,
    *,
    label: str,
    expected: tuple[str, ...],
    forbidden: tuple[str, ...],
    known_ids: tuple[tuple[str, str], ...],
) -> None:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ProofFailure(f"{label}-invalid-html") from error
    if 'data-component="Collection' not in text:
        raise ProofFailure(f"{label}-trusted-renderer-missing")
    for value in expected:
        if value not in text:
            raise ProofFailure(f"{label}-expected-text-missing")
    for value in forbidden:
        if value in text:
            raise ProofFailure(f"{label}-forbidden-text-present")
    for id_label, value in known_ids:
        if value and value in text:
            raise ProofFailure(f"{label}-{id_label}-id-leak")
    if re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        text,
        re.IGNORECASE,
    ):
        raise ProofFailure(f"{label}-uuid-leak")
    if any(marker in text for marker in ("sas2_", "sbp1.", "sbws1:")):
        raise ProofFailure(f"{label}-credential-leak")


def _canonical_stable_bytes(body: bytes) -> bytes:
    """Ignore only Next's per-response CSP nonce in canonical HTML bytes."""

    normalized = re.sub(
        rb'nonce":"[A-Za-z0-9_-]+"',
        b'nonce":"<request-nonce>"',
        body,
    )
    return re.sub(
        rb'nonce="[A-Za-z0-9_-]+"',
        b'nonce="<request-nonce>"',
        normalized,
    )


def _run_dynamic_news_edge_journey(
    client: PublicClient, site_id: str, csrf: str, project: str, tag: str
) -> None:
    """Prove the Agent-created dynamic News result through the public edge."""

    workspace = capability = token = ""
    workspace_body = {
        "title": f"OAP 077-u News {tag}",
        "task_description": "Bounded dynamic News edge proof",
        "delegation_preset": "L4_SITE_ARCHITECT",
        "duration_hours": 1,
        "request_quota": 1000,
        "mutation_quota": 200,
        "delete_quota": 50,
        "upload_quota": 0,
        "browser_quota": 5,
        "resource_constraints": {"delete_enabled": True, "max_deletes": 50},
    }
    workspace = _create_workspace(
        client, site_id, csrf, workspace_body, f"oap-077u-news-workspace-{tag}"
    )
    token, capability = _issue_capability(
        client,
        site_id,
        workspace,
        csrf,
        f"oap-077u-news-capability-{tag}",
    )
    try:
        locales = _agent_list(
            client, token, "/api/agent/v1/locales", label="news-locales"
        )
        default_locale = next(
            (row.get("tag") for row in locales if row.get("is_default") is True), None
        )
        if not isinstance(default_locale, str):
            raise ProofFailure("news-default-locale-missing")
        selected_locale = "sl-SI"
        if not any(
            str(row.get("tag", "")).casefold() == selected_locale.casefold()
            for row in locales
        ):
            _mutation(
                client,
                token,
                "/api/agent/v1/locales",
                {
                    "tag": selected_locale,
                    "enabled": True,
                    "is_default": False,
                    "position": len(locales),
                    "metadata": {},
                },
                f"oap-077u-news-locale-{tag}",
            )

        news_slug = f"news-{tag}"
        news_type = _mutation(
            client,
            token,
            "/api/agent/v1/content-model/types",
            {
                "key": f"oap_news_{tag}",
                "labels": {default_locale: "News"},
                "slug_pattern": f"/{news_slug}/{{slug}}",
                "settings": {},
            },
            f"oap-077u-news-type-{tag}",
        )
        type_id = _require_uuid(news_type["record"]["id"], "news-type")
        for key, label, field_type, localized, position in (
            ("title", "Title", "short_text", True, 0),
            ("summary", "Summary", "long_text", True, 1),
            ("rank", "Rank", "integer", False, 2),
        ):
            _mutation(
                client,
                token,
                f"/api/agent/v1/content-model/types/{type_id}/fields",
                {
                    "key": key,
                    "label": label,
                    "field_type": field_type,
                    "localized": localized,
                    "required": True,
                    "position": position,
                },
                f"oap-077u-news-field-{key}-{tag}",
            )
        items: dict[str, tuple[str, str, str]] = {}
        for slug, status, rank in (
            ("published", "PUBLISHED", 3),
            ("draft", "DRAFT", 2),
            ("archived", "ARCHIVED", 1),
        ):
            item = _mutation(
                client,
                token,
                f"/api/agent/v1/content-items/types/{type_id}",
                {
                    "type_id": type_id,
                    "slug": slug,
                    "status": status,
                    "values": {"rank": rank},
                },
                f"oap-077u-news-item-{slug}-{tag}",
            )
            item_id = _require_uuid(item["record"]["id"], f"news-{slug}-item")
            translations: dict[str, str] = {}
            for locale, title, summary in (
                (
                    default_locale,
                    f"{status.title()} title",
                    f"{status.title()} summary",
                ),
                (
                    selected_locale,
                    f"{status.title()} naslov",
                    f"{status.title()} povzetek",
                ),
            ):
                translation = _mutation(
                    client,
                    token,
                    f"/api/agent/v1/content-items/{item_id}/translations",
                    {
                        "locale": locale,
                        "localized_values": {"title": title, "summary": summary},
                    },
                    f"oap-077u-news-translation-{slug}-{locale}-{tag}",
                )
                translations[locale] = _require_uuid(
                    translation["record"]["id"], f"news-{slug}-translation"
                )
            items[slug] = (
                item_id,
                translations[default_locale],
                translations[selected_locale],
            )

        view = _mutation(
            client,
            token,
            f"/api/agent/v1/collection-views/types/{type_id}",
            {
                "type_id": type_id,
                "key": f"oap-news-{tag}",
                "filter_spec": {},
                "sort_spec": {"field": "rank", "direction": "desc"},
                "projection_spec": {"fields": ["title", "summary", "rank"]},
                "pagination_spec": {"limit": 10, "offset": 0},
            },
            f"oap-077u-news-view-{tag}",
        )
        view_id = _require_uuid(view["record"]["id"], "news-view")
        pages: dict[str, str] = {}
        for locale, suffix, title in (
            (default_locale, "default", "News"),
            (selected_locale, "selected", "Novice"),
        ):
            listing = _mutation(
                client,
                token,
                "/api/agent/v1/pages/",
                {
                    "slug": news_slug,
                    "title": title,
                    "status": "PUBLISHED",
                    "locale": locale,
                },
                f"oap-077u-news-listing-{suffix}-{tag}",
            )
            listing_id = _require_uuid(
                listing["record"]["id"], f"news-{suffix}-listing"
            )
            pages[locale] = listing_id
            detail = _mutation(
                client,
                token,
                "/api/agent/v1/pages/",
                {
                    "slug": "detail",
                    "title": "News detail" if suffix == "default" else "Podrobnosti",
                    "status": "PUBLISHED",
                    "locale": locale,
                    "parent_id": listing_id,
                    "route_template": "{slug}",
                },
                f"oap-077u-news-detail-{suffix}-{tag}",
            )
            detail_id = _require_uuid(detail["record"]["id"], f"news-{suffix}-detail")
            _mutation(
                client,
                token,
                f"/api/agent/v1/pages/{listing_id}/components",
                {
                    "component_type": "CollectionList",
                    "slot_key": "default",
                    "order_key": 0,
                    "props": {"viewId": view_id},
                },
                f"oap-077u-news-list-node-{suffix}-{tag}",
            )
            _mutation(
                client,
                token,
                f"/api/agent/v1/pages/{detail_id}/components",
                {
                    "component_type": "CollectionDetail",
                    "slot_key": "default",
                    "order_key": 0,
                    "props": {"viewId": view_id},
                },
                f"oap-077u-news-detail-node-{suffix}-{tag}",
            )
        navigation = _mutation(
            client,
            token,
            "/api/agent/v1/navigation",
            {
                "key": f"oap-news-{tag}",
                "label": "News",
                "labels": {default_locale: "News", selected_locale: "Novice"},
                "settings": {},
            },
            f"oap-077u-news-navigation-{tag}",
        )
        navigation_id = _require_uuid(navigation["record"]["id"], "news-navigation")
        _mutation(
            client,
            token,
            f"/api/agent/v1/navigation/{navigation_id}/items",
            {
                "navigation_id": navigation_id,
                "page_id": pages[default_locale],
                "target_kind": "PAGE",
                "target_value": pages[default_locale],
                "labels": {default_locale: "News", selected_locale: "Novice"},
            },
            f"oap-077u-news-navigation-item-{tag}",
        )

        canonical_root = client.request("/s/demo")
        if canonical_root.status != 200:
            raise ProofFailure("news-canonical-baseline-status")
        canonical_root_bytes = canonical_root.body
        default_route = f"/{news_slug}"
        selected_route = f"/{selected_locale.casefold()}/{news_slug}"
        default_preview = f"/preview/{workspace}/s/demo{default_route}"
        selected_preview = f"/preview/{workspace}/s/demo{selected_route}"
        if client.request(f"/s/demo{default_route}").status != 404:
            raise ProofFailure("news-canonical-workspace-leak")
        default_listing_body = _wait_preview_html(
            client, default_preview, "news-default-listing"
        )
        _assert_preview_html(
            default_listing_body,
            label="news-default-listing",
            expected=("Published title", "Draft title", "Published summary"),
            forbidden=("Archived title", "sas2_", "internal"),
            known_ids=(
                ("workspace", workspace),
                ("site", site_id),
                ("type", type_id),
                ("view", view_id),
                *[
                    (f"{slug}-item-or-translation", value)
                    for slug, item in items.items()
                    for value in item
                ],
            ),
        )
        if default_listing_body.find(b"Published title") > default_listing_body.find(
            b"Draft title"
        ):
            raise ProofFailure("news-default-sort-invalid")
        default_detail = _wait_preview_html(
            client, f"{default_preview}/published?query=kept", "news-default-detail"
        )
        _assert_preview_html(
            default_detail,
            label="news-default-detail",
            expected=("Published title", "Published summary"),
            forbidden=("Draft title", "Archived title"),
            known_ids=(
                ("workspace", workspace),
                ("site", site_id),
                ("type", type_id),
                ("view", view_id),
                *[
                    ("published-item-or-translation", value)
                    for value in items["published"]
                ],
            ),
        )
        selected_detail = _wait_preview_html(
            client, f"{selected_preview}/published", "news-selected-detail"
        )
        _assert_preview_html(
            selected_detail,
            label="news-selected-detail",
            expected=("Published naslov", "Published povzetek"),
            forbidden=("Published title", "Archived naslov"),
            known_ids=(
                ("workspace", workspace),
                ("site", site_id),
                ("type", type_id),
                ("view", view_id),
                *[
                    ("published-item-or-translation", value)
                    for value in items["published"]
                ],
            ),
        )
        browser_response = client.request(
            "/api/agent/v1/preview-runs",
            method="POST",
            body={
                "version": "browser-preview/v1",
                "route": f"/s/demo{default_route}/published",
                "target": "desktop-chromium",
                "evidence": ["heading-summary", "structure-summary"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": f"oap-077u-news-browser-run-{tag}",
            },
        )
        browser_document = _json(
            browser_response, status=202, label="news-browser-run-create"
        )
        browser_run_id = _require_uuid(
            browser_document.get("run_id"), "news-browser-run"
        )
        if any(
            key in browser_document
            for key in ("workspace_id", "capability_id", "token")
        ):
            raise ProofFailure("news-browser-run-secret-disclosure")
        _wait_browser_run(client, token, browser_run_id, "news-browser-run")
        for invalid in (
            f"{default_preview}/archived",
            f"{default_preview}/unknown",
            f"{default_preview}/published/extra",
            f"{default_preview}/published%2Fextra",
        ):
            if client.request(invalid).status != 404:
                raise ProofFailure("news-invalid-detail-route-visible")

        published_item, default_translation, _selected_translation = items["published"]
        renamed = _request_mutation(
            client,
            token,
            f"/api/agent/v1/content-items/{published_item}",
            {"slug": "renamed", "expected_row_version": 1},
            f"oap-077u-news-rename-{tag}",
        )
        if renamed["record"].get("slug") != "renamed":
            raise ProofFailure("news-rename-response-invalid")
        _request_mutation(
            client,
            token,
            f"/api/agent/v1/content-items/{published_item}/translations/{default_translation}",
            {
                "localized_values": {
                    "title": "Published title updated",
                    "summary": "Published summary updated",
                },
                "expected_row_version": 1,
            },
            f"oap-077u-news-translation-update-{tag}",
        )
        if client.request(f"{default_preview}/published").status != 404:
            raise ProofFailure("news-old-slug-still-visible")
        renamed_body = _wait_preview_html(
            client, f"{default_preview}/renamed", "news-renamed-detail"
        )
        _assert_preview_html(
            renamed_body,
            label="news-renamed-detail",
            expected=("Published title updated", "Published summary updated"),
            forbidden=('Published title"><', "Archived title"),
            known_ids=(
                ("workspace", workspace),
                ("site", site_id),
                ("type", type_id),
                ("view", view_id),
                *[
                    ("published-item-or-translation", value)
                    for value in items["published"]
                ],
            ),
        )
        _request_mutation(
            client,
            token,
            f"/api/agent/v1/content-items/{published_item}",
            {"status": "ARCHIVED", "expected_row_version": 2},
            f"oap-077u-news-archive-{tag}",
        )
        if client.request(f"{default_preview}/renamed").status != 404:
            raise ProofFailure("news-archived-detail-visible")
        canonical_after = client.request("/s/demo")
        canonical_before_stable = _canonical_stable_bytes(canonical_root_bytes)
        canonical_after_stable = _canonical_stable_bytes(canonical_after.body)
        if (
            canonical_after.status != 200
            or canonical_after_stable != canonical_before_stable
        ):
            first_difference = next(
                (
                    index
                    for index, (before, after) in enumerate(
                        zip(
                            canonical_before_stable,
                            canonical_after_stable,
                            strict=False,
                        )
                    )
                    if before != after
                ),
                min(len(canonical_before_stable), len(canonical_after_stable)),
            )
            raise ProofFailure(
                "news-canonical-bytes-changed-"
                f"before={len(canonical_before_stable)}-after={len(canonical_after_stable)}-"
                f"diff={first_difference}-"
                f"before-sha={hashlib.sha256(canonical_before_stable).hexdigest()[:12]}-"
                f"after-sha={hashlib.sha256(canonical_after_stable).hexdigest()[:12]}"
            )
        _compose(project, "restart", "agent-api")
        _wait_agent_ready(client)
        _compose(project, "restart", "render-api")
        _wait_preview_html(client, default_preview, "news-render-restart")
        _compose(project, "restart", "web")
        _wait_preview_html(client, default_preview, "news-web-restart")
        print(
            "public-agent-news-edge: OK "
            f"workspace={workspace} routes=default,non-default detail=exact "
            "listing-sort=verified status-slug-translation=verified "
            "canonical-isolation=byte-identical restart=agent,render,web "
            "html=uuid-token-json-free"
        )
    finally:
        if workspace and capability:
            _revoke_capability(client, site_id, workspace, capability)


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
            "/api/agent/v1/locales",
            "/api/agent/v1/locales/{locale_id}",
            "/api/agent/v1/redirects",
            "/api/agent/v1/redirects/{redirect_id}",
            "/api/agent/v1/navigation",
            "/api/agent/v1/navigation/{navigation_id}",
            "/api/agent/v1/navigation/{navigation_id}/items",
            "/api/agent/v1/navigation-items/{item_id}",
            "/api/agent/v1/navigation-items/{item_id}:move",
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
            "page:write",
            "page:move",
            "page:delete",
            "page:restore",
            "route:write",
            "composition:read",
            "component-structure:create",
            "validation:read",
            "locale:configure",
            "navigation:read",
            "navigation:create",
            "navigation:write",
            "navigation:delete",
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

        _run_dynamic_news_edge_journey(client, site_id, csrf, project, tag)

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

        internal_page = _mutation(
            client,
            primary_token,
            "/api/agent/v1/pages/",
            {
                "slug": f"docs-{tag}",
                "title": "Documentation",
                "status": "DRAFT",
                "locale": "en",
            },
            f"oap-navigation-internal-page-{tag}",
        )
        internal_page_id = _require_uuid(
            internal_page["record"]["id"], "navigation-internal-page"
        )
        internal_target = internal_page["record"].get("effective_route")
        if not isinstance(internal_target, str) or not internal_target.startswith("/"):
            raise ProofFailure("navigation-internal-page-route-missing")
        redirect = _mutation(
            client,
            primary_token,
            "/api/agent/v1/redirects",
            {
                "source_route": f"/oap-redirect-{tag}",
                "target": internal_target,
                "status_code": 301,
            },
            f"oap-redirect-create-{tag}",
        )
        redirect_id = _require_uuid(redirect["record"]["id"], "redirect")
        if redirect["record"].get("row_version") != 1:
            raise ProofFailure("redirect-version-invalid")
        _agent_list(
            client, primary_token, "/api/agent/v1/redirects", label="redirect-list"
        )
        _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/redirects/{redirect_id}",
            label="redirect-get",
        )
        redirect_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/redirects/{redirect_id}",
            {"status_code": 302, "expected_row_version": 1},
            f"oap-redirect-update-{tag}",
        )
        if redirect_update["record"].get("row_version") != 2:
            raise ProofFailure("redirect-update-version-invalid")
        _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/redirects/{redirect_id}",
            {"expected_row_version": 2},
            f"oap-redirect-delete-{tag}",
            method="DELETE",
        )

        lifecycle_slug = f"oap-lifecycle-{tag}"
        lifecycle_path = f"/s/demo/{lifecycle_slug}"
        lifecycle = _mutation(
            client,
            primary_token,
            "/api/agent/v1/pages/",
            {
                "slug": lifecycle_slug,
                "title": "OAP lifecycle",
                "status": "PUBLISHED",
                "locale": "en",
                "parent_id": page_id,
            },
            f"oap-page-lifecycle-create-{tag}",
        )
        lifecycle_id = _require_uuid(lifecycle["record"]["id"], "lifecycle-page")
        if client.request(lifecycle_path).status != 404:
            raise ProofFailure("workspace-page-visible-on-canonical-edge")
        lifecycle_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{lifecycle_id}",
            {"title": "OAP lifecycle updated", "expected_row_version": 1},
            f"oap-page-lifecycle-update-{tag}",
        )
        if lifecycle_update["record"].get("row_version") != 2:
            raise ProofFailure("page-version-invalid")
        lifecycle_move = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{lifecycle_id}:move",
            {"parent_id": None, "expected_row_version": 2},
            f"oap-page-lifecycle-move-{tag}",
            method="POST",
        )
        if lifecycle_move["record"].get("row_version") != 3:
            raise ProofFailure("page-move-version-invalid")
        if client.request(lifecycle_path).status != 404:
            raise ProofFailure("workspace-moved-page-visible-on-canonical-edge")
        lifecycle_delete = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{lifecycle_id}",
            {"expected_row_version": 3},
            f"oap-page-lifecycle-delete-{tag}",
            method="DELETE",
        )
        if (
            lifecycle_delete["record"].get("deleted_at") is None
            or lifecycle_delete["record"].get("row_version") != 4
        ):
            raise ProofFailure("page-tombstone-invalid")
        if (
            client.request(
                f"/api/agent/v1/pages/{lifecycle_id}",
                headers={"Authorization": f"Bearer {primary_token}"},
            ).status
            != 404
            or client.request(lifecycle_path).status != 404
        ):
            raise ProofFailure("page-tombstone-visible")
        if lifecycle_id in {
            item.get("id")
            for item in _agent_list(
                client,
                primary_token,
                "/api/agent/v1/pages/",
                label="page-list-after-delete",
            )
        }:
            raise ProofFailure("page-tombstone-in-list")
        lifecycle_restore = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{lifecycle_id}:restore",
            {"expected_row_version": 4},
            f"oap-page-lifecycle-restore-{tag}",
            method="POST",
        )
        if (
            lifecycle_restore["record"].get("id") != lifecycle_id
            or lifecycle_restore["record"].get("deleted_at") is not None
            or lifecycle_restore["record"].get("row_version") != 5
        ):
            raise ProofFailure("page-restore-invalid")
        if client.request(lifecycle_path).status != 404:
            raise ProofFailure("restored-workspace-page-visible-on-canonical-edge")
        lifecycle_delete_again = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{lifecycle_id}",
            {"expected_row_version": 5},
            f"oap-page-lifecycle-delete-again-{tag}",
            method="DELETE",
        )
        if lifecycle_delete_again["record"].get("row_version") != 6:
            raise ProofFailure("page-second-tombstone-version-invalid")
        replacement = _mutation(
            client,
            primary_token,
            "/api/agent/v1/pages/",
            {
                "slug": lifecycle_slug,
                "title": "OAP replacement",
                "status": "PUBLISHED",
                "locale": "en",
            },
            f"oap-page-replacement-create-{tag}",
        )
        replacement_id = _require_uuid(replacement["record"]["id"], "replacement-page")
        if replacement_id == lifecycle_id:
            raise ProofFailure("tombstone-reused-page-id")
        restore_conflict = client.request(
            f"/api/agent/v1/pages/{lifecycle_id}:restore",
            method="POST",
            body={"expected_row_version": 6},
            headers={
                "Authorization": f"Bearer {primary_token}",
                "Idempotency-Key": f"oap-page-lifecycle-restore-conflict-{tag}",
            },
        )
        if restore_conflict.status != 409:
            raise ProofFailure(
                f"page-restore-conflict-status-{restore_conflict.status}"
            )
        _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{replacement_id}",
            {"expected_row_version": 1},
            f"oap-page-replacement-delete-{tag}",
            method="DELETE",
        )
        baseline_locales = _agent_list(
            client, primary_token, "/api/agent/v1/locales", label="locale-baseline"
        )
        default_locale = next(
            (locale for locale in baseline_locales if locale.get("is_default")), None
        )
        if default_locale is None:
            raise ProofFailure("locale-default-missing")
        locale_create = _mutation(
            client,
            primary_token,
            "/api/agent/v1/locales",
            {
                "tag": "sl-SI",
                "enabled": True,
                "is_default": False,
                "position": 1,
                "metadata": {},
            },
            f"oap-locale-create-{tag}",
        )
        locale_id = _require_uuid(locale_create["record"]["id"], "locale")
        localized_home = _mutation(
            client,
            primary_token,
            "/api/agent/v1/pages/",
            {
                "slug": "home",
                "title": "Slovenian home",
                "status": "DRAFT",
                "locale": "sl-SI",
            },
            f"oap-locale-home-create-{tag}",
        )
        localized_home_id = _require_uuid(
            localized_home["record"]["id"], "localized-home-page"
        )
        locale_default = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/locales/{locale_id}",
            {"is_default": True, "expected_row_version": 1},
            f"oap-locale-default-{tag}",
        )
        if (
            locale_default["record"].get("is_default") is not True
            or locale_default["record"].get("row_version") != 2
        ):
            raise ProofFailure("locale-default-invalid")
        if (
            _agent_request(
                client,
                primary_token,
                f"/api/agent/v1/locales/{locale_id}",
                label="locale-get",
            ).get("tag")
            != "sl-SI"
        ):
            raise ProofFailure("locale-read-invalid")
        refreshed_internal_page = _agent_request(
            client,
            primary_token,
            f"/api/agent/v1/pages/{internal_page_id}",
            label="navigation-internal-page-after-locale",
        )
        internal_target = refreshed_internal_page.get("effective_route")
        if not isinstance(internal_target, str) or not internal_target.startswith("/"):
            raise ProofFailure("navigation-internal-page-route-after-locale-missing")
        navigation_create = _mutation(
            client,
            primary_token,
            "/api/agent/v1/navigation",
            {
                "key": f"oap-nav-{tag}",
                "label": "Primary navigation",
                "labels": {"sl-SI": "Glavni meni"},
                "settings": {},
            },
            f"oap-navigation-create-{tag}",
        )
        navigation_id = _require_uuid(navigation_create["record"]["id"], "navigation")
        if navigation_create["record"].get("row_version") != 1:
            raise ProofFailure("navigation-version-invalid")
        page_item = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation/{navigation_id}/items",
            {
                "navigation_id": navigation_id,
                "page_id": page_id,
                "target_kind": "PAGE",
                "target_value": page_id,
                "labels": {"sl-SI": "Domov"},
                "locale": "sl-SI",
                "before_item_id": None,
                "after_item_id": None,
            },
            f"oap-navigation-page-item-{tag}",
        )
        page_item_id = _require_uuid(page_item["record"]["id"], "page-item")
        child_item = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation/{navigation_id}/items",
            {
                "navigation_id": navigation_id,
                "parent_id": page_item_id,
                "target_kind": "INTERNAL",
                "target_value": internal_target,
                "labels": {"sl-SI": "Dokumentacija"},
                "locale": "sl-SI",
                "before_item_id": None,
                "after_item_id": None,
            },
            f"oap-navigation-child-item-{tag}",
        )
        child_item_id = _require_uuid(child_item["record"]["id"], "child-item")
        external_item = _mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation/{navigation_id}/items",
            {
                "navigation_id": navigation_id,
                "target_kind": "EXTERNAL",
                "target_value": "https://example.test/docs",
                "labels": {"en": "External docs", "sl-SI": "Zunanje povezave"},
                "before_item_id": None,
                "after_item_id": None,
            },
            f"oap-navigation-external-item-{tag}",
        )
        external_item_id = _require_uuid(external_item["record"]["id"], "external-item")
        navigation_items = _agent_list(
            client,
            primary_token,
            f"/api/agent/v1/navigation/{navigation_id}/items",
            label="navigation-item-list",
        )
        if {item.get("id") for item in navigation_items} != {
            page_item_id,
            child_item_id,
            external_item_id,
        }:
            raise ProofFailure("navigation-item-list-invalid")
        if (
            next(
                item for item in navigation_items if item.get("id") == child_item_id
            ).get("parent_id")
            != page_item_id
        ):
            raise ProofFailure("navigation-parent-invalid")
        navigation_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation/{navigation_id}",
            {"label": "Primary navigation updated", "expected_row_version": 1},
            f"oap-navigation-update-{tag}",
        )
        if navigation_update["record"].get("row_version") != 2:
            raise ProofFailure("navigation-update-version-invalid")
        navigation_move = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation-items/{external_item_id}:move",
            {
                "parent_id": None,
                "before_item_id": page_item_id,
                "expected_row_version": 1,
            },
            f"oap-navigation-move-{tag}",
            method="POST",
        )
        if (
            navigation_move["record"].get("position") != 0
            or navigation_move["record"].get("row_version") != 2
        ):
            raise ProofFailure("navigation-move-invalid")
        navigation_item_update = _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation-items/{page_item_id}",
            {
                "labels": {"sl-SI": "Domov updated"},
                "expected_row_version": 2,
            },
            f"oap-navigation-item-update-{tag}",
        )
        if navigation_item_update["record"].get("row_version") != 3:
            raise ProofFailure("navigation-item-update-version-invalid")
        _compose(project, "restart", "agent-api")
        agent_outage = False
        _wait_agent_ready(client)
        if (
            _agent_request(
                client,
                primary_token,
                f"/api/agent/v1/pages/{page_id}",
                label="page-restart-read",
            ).get("id")
            != page_id
            or client.request(lifecycle_path).status != 404
        ):
            raise ProofFailure("page-canonical-independence-after-agent-restart")
        if (
            _agent_request(
                client,
                primary_token,
                f"/api/agent/v1/navigation/{navigation_id}",
                label="navigation-restart-read",
            ).get("label")
            != "Primary navigation updated"
            or _agent_request(
                client,
                primary_token,
                f"/api/agent/v1/locales/{locale_id}",
                label="locale-restart-read",
            ).get("is_default")
            is not True
        ):
            raise ProofFailure("locale-navigation-restart-persistence-invalid")
        for path, body, key in (
            (
                f"/api/agent/v1/navigation-items/{child_item_id}",
                {"expected_row_version": 1},
                f"oap-navigation-child-delete-{tag}",
            ),
            (
                f"/api/agent/v1/navigation-items/{external_item_id}",
                {"expected_row_version": 2},
                f"oap-navigation-external-delete-{tag}",
            ),
            (
                f"/api/agent/v1/navigation-items/{page_item_id}",
                {"expected_row_version": 4},
                f"oap-navigation-page-item-delete-{tag}",
            ),
        ):
            _request_mutation(client, primary_token, path, body, key, method="DELETE")
        _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/navigation/{navigation_id}",
            {"expected_row_version": 2},
            f"oap-navigation-delete-{tag}",
            method="DELETE",
        )
        internal_page_before_delete = client.request(
            f"/api/agent/v1/pages/{internal_page_id}",
            headers={"Authorization": f"Bearer {primary_token}"},
        )
        if internal_page_before_delete.status != 200:
            raise ProofFailure(
                "oap-navigation-internal-page-before-delete-status-"
                f"{internal_page_before_delete.status}"
            )
        internal_page_document = _json(
            internal_page_before_delete,
            status=200,
            label="navigation-internal-page-before-delete",
        )
        if internal_page_document.get("row_version") != 1:
            raise ProofFailure(
                "oap-navigation-internal-page-before-delete-row-version-"
                f"{internal_page_document.get('row_version')}"
            )
        internal_redirect_targets = _sql(
            project,
            "SELECT count(*) FROM content.redirect "
            f"WHERE site_id='{site_id}'::uuid AND target='{internal_target}'",
        )
        if internal_redirect_targets != "0":
            raise ProofFailure(
                "oap-navigation-internal-page-redirect-dependency-count-"
                f"{internal_redirect_targets}"
            )
        internal_navigation_dependencies = _sql(
            project,
            "SELECT count(*) FROM content.navigation_item "
            f"WHERE site_id='{site_id}'::uuid AND page_id='{internal_page_id}'::uuid",
        )
        if internal_navigation_dependencies != "0":
            raise ProofFailure(
                "oap-navigation-internal-page-navigation-dependency-count-"
                f"{internal_navigation_dependencies}"
            )
        internal_page_delete_key = f"oap-navigation-internal-page-delete-{tag}"
        internal_page_delete_response = client.request(
            f"/api/agent/v1/pages/{internal_page_id}",
            method="DELETE",
            body={"expected_row_version": 1},
            headers={
                "Authorization": f"Bearer {primary_token}",
                "Idempotency-Key": internal_page_delete_key,
            },
        )
        if internal_page_delete_response.status != 200:
            try:
                error_document = json.loads(internal_page_delete_response.body)
                error_code = error_document.get("error", {}).get("code", "unknown")
            except (TypeError, ValueError, AttributeError):
                error_code = "invalid-json"
            raise ProofFailure(
                f"{internal_page_delete_key}-status-"
                f"{internal_page_delete_response.status}-code-{error_code}"
            )
        internal_page_delete_document = _json(
            internal_page_delete_response,
            status=200,
            label=internal_page_delete_key,
        )
        _record_semantic_audit_expectation(
            token=primary_token,
            path=f"/api/agent/v1/pages/{internal_page_id}",
            method="DELETE",
            body={"expected_row_version": 1},
            key=internal_page_delete_key,
            status=200,
            document=internal_page_delete_document,
        )
        _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/locales/{default_locale['id']}",
            {"is_default": True, "expected_row_version": 2},
            f"oap-locale-restore-default-{tag}",
        )
        _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/pages/{localized_home_id}",
            {"expected_row_version": 1},
            f"oap-locale-home-delete-{tag}",
            method="DELETE",
        )
        _request_mutation(
            client,
            primary_token,
            f"/api/agent/v1/locales/{locale_id}",
            {"expected_row_version": 3},
            f"oap-locale-delete-{tag}",
            method="DELETE",
        )
        _compose(project, "restart", "render-api")
        _wait_public_not_found(client, lifecycle_path, "render-restart-page")
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
        if (
            _sql(
                project,
                f"SELECT count(*) FROM content.navigation_base WHERE id='{navigation_id}'::uuid",
            )
            != "0"
        ):
            raise ProofFailure("canonical-navigation-changed")
        if (
            _sql(
                project,
                f"SELECT count(*) FROM content.site_locale_base WHERE id='{locale_id}'::uuid",
            )
            != "0"
        ):
            raise ProofFailure("canonical-locale-changed")
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
            "locales=1 redirects=1 navigations=1 navigation-items=3 "
            "openapi=exact restart=verified nginx-outage=verified "
            "crud=public quotas=mutation-429,max-delete-429 "
            "dependency-delete=422 page-delete-restore=verified "
            "canonical-independence=verified render-restart=verified"
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

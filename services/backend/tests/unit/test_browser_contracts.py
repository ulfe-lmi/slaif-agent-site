"""Python/TypeScript parity and bounded browser-contract unit evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from slaif_agent_site.agent_state.capability import generate_capability_token
from slaif_agent_site.agent_state.capability_auth import (
    CAPABILITY_AUTHENTICATION_SQL,
    authenticate_capability,
)
from slaif_agent_site.browser_contracts import (
    BROWSER_CONTRACT_BOUNDS,
    BROWSER_CONTRACT_VERSION,
    BROWSER_EVIDENCE,
    BROWSER_RUN_STATES,
    BROWSER_TARGETS,
    BROWSER_TERMINAL_STATES,
    BrowserCapabilityLimits,
    BrowserRunCompletion,
    PreviewRunCreateRequest,
    PreviewRunStatus,
    canonical_serialize_preview_run_request,
    preview_run_request_digest,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_FACTS = (
    REPOSITORY_ROOT
    / "packages"
    / "browser-tool-contracts"
    / "src"
    / "browser-preview-v1.json"
)


def _valid_request() -> dict[str, object]:
    return {
        "version": BROWSER_CONTRACT_VERSION,
        "route": "/news?locale=en",
        "target": "desktop-chromium",
        "evidence": ["screenshot", "heading-summary"],
    }


def test_language_neutral_facts_match_python_exactly() -> None:
    facts = json.loads(CONTRACT_FACTS.read_text(encoding="utf-8"))
    assert facts == {
        "contractVersion": BROWSER_CONTRACT_VERSION,
        "targets": list(BROWSER_TARGETS),
        "evidence": list(BROWSER_EVIDENCE),
        "runStates": list(BROWSER_RUN_STATES),
        "terminalStates": list(BROWSER_TERMINAL_STATES),
        "visibility": "PRIVATE",
        "bounds": BROWSER_CONTRACT_BOUNDS,
    }


def test_request_canonical_serialization_and_digest_are_deterministic() -> None:
    first = _valid_request()
    second = {**first, "evidence": ["heading-summary", "screenshot"]}
    expected = (
        '{"evidence":["screenshot","heading-summary"],'
        '"route":"/news?locale=en","target":"desktop-chromium",'
        '"version":"browser-preview/v1"}'
    )
    assert canonical_serialize_preview_run_request(first) == expected
    assert canonical_serialize_preview_run_request(second) == expected
    assert preview_run_request_digest(first) == preview_run_request_digest(second)
    assert preview_run_request_digest(first) == (
        "6ee9d361a4433878c18c6aa645c6872afae8bd31ac0e628e88f3d0eefa3405f4"
    )


@pytest.mark.parametrize(
    "update",
    (
        {"version": "browser-preview/v2"},
        {"target": "desktop-firefox"},
        {"evidence": []},
        {"evidence": ["screenshot", "screenshot"]},
        {"evidence": ["raw-dom"]},
        {"route": "https://outside.invalid/"},
        {"route": "//outside.invalid/"},
        {"route": "/a/../private"},
        {"route": "/a/%2e%2e/private"},
        {"route": "/news#private"},
        {"route": "/news?access_token=secret"},
        {"route": "/news?next=sas2_0123_secret"},
        {"viewport": {"width": 1200, "height": 800}},
        {"capability_id": str(uuid4())},
        {"headers": {"authorization": "secret"}},
        {"javascript": "document.body"},
    ),
)
def test_external_create_rejects_unsafe_or_authority_bearing_input(
    update: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        PreviewRunCreateRequest.model_validate({**_valid_request(), **update})


def test_capability_limits_and_completion_are_frozen_extra_forbid() -> None:
    limits = BrowserCapabilityLimits()
    assert limits.max_runs == 20
    assert {target.value for target in limits.allowed_targets} == set(BROWSER_TARGETS)
    with pytest.raises(ValidationError):
        BrowserCapabilityLimits.model_validate(
            {
                **limits.model_dump(),
                "max_runs": 1,
                "max_concurrent_runs": 2,
            }
        )
    with pytest.raises(ValidationError):
        BrowserCapabilityLimits.model_validate(
            {**limits.model_dump(), "allowed_targets": ["desktop-firefox"]}
        )
    with pytest.raises(ValidationError):
        BrowserRunCompletion.model_validate(
            {
                "version": BROWSER_CONTRACT_VERSION,
                "run_id": str(uuid4()),
                "lease_id": str(uuid4()),
                "state": "COMPLETED",
                "summary": {},
                "error": {"code": "UNEXPECTED", "message": "not allowed"},
            }
        )
    with pytest.raises(ValidationError):
        PreviewRunStatus.model_validate(
            {
                "version": BROWSER_CONTRACT_VERSION,
                "run_id": str(uuid4()),
                "state": "UNKNOWN",
                "route": "/",
                "target": "desktop-chromium",
                "evidence": ["screenshot"],
                "created_at": datetime.now(UTC),
                "started_at": None,
                "completed_at": None,
                "expires_at": datetime.now(UTC) + timedelta(minutes=1),
            }
        )


class _FakeConnection:
    def __init__(self, row: dict[str, object]) -> None:
        self.row = row

    async def fetchrow(self, query: str, public_id: str) -> dict[str, object]:
        assert query == CAPABILITY_AUTHENTICATION_SQL
        assert public_id == self.row["public_id"]
        return self.row


class _FakeAcquire:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> _FakeConnection:
        return self.connection

    async def __aexit__(self, *_arguments: object) -> None:
        return None


class _FakePool:
    def __init__(self, row: dict[str, object]) -> None:
        self.connection = _FakeConnection(row)

    def acquire(self, *, timeout: float) -> _FakeAcquire:
        assert timeout > 0
        return _FakeAcquire(self.connection)


@pytest.mark.asyncio
async def test_capability_authentication_reads_validated_limits_and_fails_closed() -> (
    None
):
    token, public_id, digest = generate_capability_token()
    now = datetime.now(UTC)
    row: dict[str, Any] = {
        "id": uuid4(),
        "public_id": public_id,
        "secret_digest": digest,
        "workspace_id": uuid4(),
        "site_id": uuid4(),
        "created_by": uuid4(),
        "scopes": ["preview:inspect"],
        "created_at": now,
        "expires_at": now + timedelta(minutes=30),
        "revoked_at": None,
        "browser_max_runs": 20,
        "browser_max_concurrent_runs": 2,
        "browser_max_screenshots": 50,
        "browser_max_artifact_bytes": 104_857_600,
        "browser_max_routes_per_run": 10,
        "browser_max_evidence_per_run": 9,
        "browser_max_duration_seconds": 120,
        "browser_max_attempts": 3,
        "browser_allowed_targets": [
            "desktop-chromium",
            "tablet",
            "mobile-chromium",
        ],
    }
    authenticated = await authenticate_capability(
        _FakePool(row), acquire_timeout=1.0, auth_header=f"Bearer {token}"
    )
    assert authenticated is not None
    assert authenticated.browser_limits.max_runs == 20
    assert {
        target.value for target in authenticated.browser_limits.allowed_targets
    } == set(BROWSER_TARGETS)

    for field, malformed in (
        ("browser_max_runs", None),
        ("browser_max_concurrent_runs", 21),
        ("browser_allowed_targets", ["desktop-firefox"]),
        ("browser_allowed_targets", None),
    ):
        invalid = {**row, field: malformed}
        assert (
            await authenticate_capability(
                _FakePool(invalid),
                acquire_timeout=1.0,
                auth_header=f"Bearer {token}",
            )
            is None
        )

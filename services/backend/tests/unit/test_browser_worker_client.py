"""Agent-side browser-worker protocol, credential, and result proof."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.browser_worker_client import (
    BROWSER_WORKER_AUTHENTICATION_HEADER,
    BROWSER_WORKER_CONTRACT_VERSION,
    BROWSER_WORKER_DEPLOYMENT,
    BROWSER_WORKER_RESPONSE_ALGORITHM,
    BROWSER_WORKER_RESPONSE_TYPE,
    BrowserWorkerClientError,
    BrowserWorkerCredential,
    BrowserWorkerResult,
    BrowserWorkerSubmitRequest,
    SignedBrowserWorkerResult,
    browser_worker_request_digest,
    load_browser_worker_credential,
    verify_browser_worker_result,
)

ROOT = Path(__file__).resolve().parents[4]
KEY_ID = "0123456789abcdef"
KEY_BYTES = bytes(range(32))
WIRE = f"sbws1:{KEY_ID}:{base64.urlsafe_b64encode(KEY_BYTES).rstrip(b'=').decode()}"
IDS = {
    "request_id": UUID("00000000-0000-4000-8000-000000000001"),
    "run_id": UUID("00000000-0000-4000-8000-000000000002"),
    "site_id": UUID("00000000-0000-4000-8000-000000000003"),
    "workspace_id": UUID("00000000-0000-4000-8000-000000000004"),
    "capability_id": UUID("00000000-0000-4000-8000-000000000005"),
    "operation_id": UUID("00000000-0000-4000-8000-000000000006"),
    "lease_id": UUID("00000000-0000-4000-8000-000000000007"),
}


def _request() -> BrowserWorkerSubmitRequest:
    route = "/s/demo/?a=1&b=2"
    return BrowserWorkerSubmitRequest.model_validate(
        {
            **IDS,
            "attempt": 1,
            "route": route,
            "route_digest": hashlib.sha256(route.encode()).hexdigest(),
            "target": "desktop-chromium",
            "evidence": ("screenshot", "heading-summary"),
            "artifact_bytes_limit": 8_388_608,
            "duration_seconds": 30,
            "issued_at": 1_800_000_000,
            "expires_at": 1_800_000_030,
            "preview_credential": SecretStr("sbp1.a.b.c"),
        }
    )


def _credential() -> BrowserWorkerCredential:
    return BrowserWorkerCredential(
        key_id=KEY_ID,
        secret=SecretStr(KEY_BYTES.hex()),
        wire_value=SecretStr(WIRE),
    )


def _result(request: BrowserWorkerSubmitRequest) -> BrowserWorkerResult:
    return BrowserWorkerResult.model_validate(
        {
            "version": BROWSER_WORKER_CONTRACT_VERSION,
            "deployment": BROWSER_WORKER_DEPLOYMENT,
            "request_id": request.request_id,
            "request_digest": browser_worker_request_digest(request),
            "run_id": request.run_id,
            "site_id": request.site_id,
            "workspace_id": request.workspace_id,
            "capability_id": request.capability_id,
            "operation_id": request.operation_id,
            "lease_id": request.lease_id,
            "attempt": request.attempt,
            "route_digest": request.route_digest,
            "target": request.target,
            "state": "FAILED",
            "summary": {},
            "error": {
                "code": "BROWSER_FAILED",
                "message": "browser attempt failed",
            },
            "artifacts": (),
            "started_at": 1_800_000_010,
            "completed_at": 1_800_000_011,
            "expires_at": 1_800_000_041,
        }
    )


def _envelope(result: BrowserWorkerResult) -> SignedBrowserWorkerResult:
    document = result.model_dump(mode="json", by_alias=True)
    canonical = json.dumps(
        document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    signature = base64.urlsafe_b64encode(
        hmac.digest(KEY_BYTES, canonical.encode(), "sha256")
    ).rstrip(b"=")
    return SignedBrowserWorkerResult.model_validate(
        {
            "version": BROWSER_WORKER_CONTRACT_VERSION,
            "algorithm": BROWSER_WORKER_RESPONSE_ALGORITHM,
            "type": BROWSER_WORKER_RESPONSE_TYPE,
            "key_id": KEY_ID,
            "result": result,
            "signature": signature.decode(),
        }
    )


def test_neutral_worker_facts_and_request_digest_are_exact() -> None:
    facts = json.loads(
        (ROOT / "packages/browser-tool-contracts/src/browser-worker-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert facts == {
        "contractVersion": BROWSER_WORKER_CONTRACT_VERSION,
        "deployment": BROWSER_WORKER_DEPLOYMENT,
        "authenticationHeader": BROWSER_WORKER_AUTHENTICATION_HEADER,
        "responseAlgorithm": BROWSER_WORKER_RESPONSE_ALGORITHM,
        "responseType": BROWSER_WORKER_RESPONSE_TYPE,
        "routes": {
            "submit": "/internal/browser/v1/attempts",
            "inspect": "/internal/browser/v1/attempts/inspect",
            "retrieve": "/internal/browser/v1/artifacts/retrieve",
        },
        "bounds": {
            "requestBytes": 32768,
            "resultBytes": 262144,
            "artifactBytes": 8388608,
            "totalArtifactBytes": 16777216,
            "summaryBytes": 65536,
            "outputItems": 64,
            "outputStringCharacters": 512,
            "activeAttempts": 1,
            "queueDepth": 0,
            "durationSeconds": 120,
            "previewCredentialBytes": 4096,
            "responseTtlSeconds": 60,
            "artifactRetentionSeconds": 3600,
        },
    }
    request = _request()
    assert browser_worker_request_digest(request) == (
        "3fbd4b9094738aed2e17ddbf961c776a58c59d13c5e2aae763a2888e815c2051"
    )
    assert "sbp1.a.b.c" not in repr(request)
    assert "sbp1.a.b.c" not in request.model_dump_json()
    with pytest.raises(ValidationError):
        BrowserWorkerSubmitRequest.model_validate(
            {**request.model_dump(mode="json", by_alias=True), "viewport": {}}
        )


def test_descriptor_confined_worker_credential(tmp_path: Path) -> None:
    directory = tmp_path / "worker"
    directory.mkdir(mode=0o700)
    path = directory / "worker-token"
    path.write_text(WIRE, encoding="ascii")
    path.chmod(0o400)
    credential = load_browser_worker_credential(path)
    assert credential.key_id == KEY_ID
    assert WIRE not in repr(credential)

    wrong_mode = tmp_path / "wrong"
    wrong_mode.mkdir(mode=0o700)
    wrong_file = wrong_mode / "worker-token"
    wrong_file.write_text(WIRE, encoding="ascii")
    wrong_file.chmod(0o600)
    link_directory = tmp_path / "link"
    link_directory.mkdir(mode=0o700)
    os.symlink(path, link_directory / "worker-token")
    for candidate in (wrong_file, link_directory / "worker-token"):
        with pytest.raises(BrowserWorkerClientError) as error:
            load_browser_worker_credential(candidate)
        assert WIRE not in str(error.value)


def test_signed_result_binding_and_canonical_signature_fail_closed() -> None:
    request = _request()
    result = _result(request)
    envelope = _envelope(result)
    assert (
        verify_browser_worker_result(
            envelope, request, _credential(), now=1_800_000_020
        )
        == result
    )

    changed = _envelope(
        result.model_copy(
            update={"run_id": UUID("00000000-0000-4000-8000-000000000009")}
        )
    )
    for candidate in (
        changed,
        envelope.model_copy(update={"signature": "A" + envelope.signature[1:]}),
        envelope.model_copy(update={"signature": envelope.signature[:-1] + "1"}),
    ):
        with pytest.raises(BrowserWorkerClientError):
            verify_browser_worker_result(
                candidate, request, _credential(), now=1_800_000_020
            )

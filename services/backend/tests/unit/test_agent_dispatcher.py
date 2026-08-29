"""Agent-owned durable browser dispatcher contract proofs."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError
from slaif_agent_site.agent_api.config import AgentDispatcherSettings
from slaif_agent_site.agent_api.dispatcher import (
    AgentBrowserDispatcher,
    BrowserDispatchClaim,
)
from slaif_agent_site.browser_contracts import (
    BrowserEvidence,
    BrowserTarget,
    InternalPreviewRunSpecification,
)
from slaif_agent_site.browser_preview_credentials import (
    BrowserPreviewCredentialSigner,
    BrowserSigningKey,
)
from slaif_agent_site.browser_worker_client import (
    BrowserWorkerClient,
    BrowserWorkerSubmitRequest,
)

RUN_ID = UUID("00000000-0000-4000-8000-000000000004")
OPERATION_ID = UUID("00000000-0000-4000-8000-000000000005")
SITE_ID = UUID("00000000-0000-4000-8000-000000000002")
WORKSPACE_ID = UUID("00000000-0000-4000-8000-000000000003")
CAPABILITY_ID = UUID("00000000-0000-4000-8000-000000000001")
DELEGATOR_ID = UUID("00000000-0000-4000-8000-000000000006")
LEASE_ID = UUID("00000000-0000-4000-8000-000000000007")
NOW = 1_800_000_000


def _claim() -> BrowserDispatchClaim:
    route = "/"
    return BrowserDispatchClaim(
        specification=InternalPreviewRunSpecification(
            version="browser-preview/v1",
            run_id=RUN_ID,
            operation_id=OPERATION_ID,
            site_id=SITE_ID,
            workspace_id=WORKSPACE_ID,
            capability_id=CAPABILITY_ID,
            delegator_id=DELEGATOR_ID,
            route=route,
            route_digest=hashlib.sha256(route.encode()).hexdigest(),
            target=BrowserTarget.DESKTOP_CHROMIUM,
            evidence=(BrowserEvidence.SCREENSHOT, BrowserEvidence.HEADING_SUMMARY),
            reserved_screenshots=1,
            reserved_artifact_bytes=5_505_024,
            max_duration_seconds=120,
            attempt=1,
        ),
        lease_id=LEASE_ID,
        lease_expires_at=datetime.now(UTC) + timedelta(seconds=30),
    )


def _dispatcher() -> AgentBrowserDispatcher:
    return AgentBrowserDispatcher(
        database=object(),
        signer=BrowserPreviewCredentialSigner(
            BrowserSigningKey("0123456789abcdef", bytes(range(32)))
        ),
        worker_client=cast(BrowserWorkerClient, object()),
        settings=AgentDispatcherSettings(worker_timeout_seconds=60),
    )


def test_request_is_run_bound_and_short_lived() -> None:
    request = _dispatcher()._request(_claim(), NOW)

    assert isinstance(request, BrowserWorkerSubmitRequest)
    assert request.run_id == RUN_ID
    assert request.lease_id == LEASE_ID
    assert request.route == "/"
    assert request.expires_at - request.issued_at == 30
    assert request.artifact_bytes_limit == 5_505_024
    assert request.preview_credential.get_secret_value().startswith("sbp1.")


def test_dispatcher_settings_keep_renewal_before_lease() -> None:
    with pytest.raises(ValidationError, match="renewal interval"):
        AgentDispatcherSettings(lease_seconds=10, renewal_interval_seconds=10)


async def test_disabled_dispatcher_does_not_start() -> None:
    dispatcher = AgentBrowserDispatcher(
        database=object(),
        signer=None,
        worker_client=None,
        settings=AgentDispatcherSettings(enabled=False),
    )
    await dispatcher.start()
    assert dispatcher.enabled is False
    await dispatcher.stop()

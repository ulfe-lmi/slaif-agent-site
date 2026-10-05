"""Unit contracts for the durable review worker (082-a)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import asyncpg
import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.review_worker import freeze_job as freeze_job_module
from slaif_agent_site.review_worker import worker as worker_module
from slaif_agent_site.review_worker.config import (
    REVIEW_WORKER_DSN_FILE,
    REVIEW_WORKER_LOGIN,
    REVIEW_WORKER_PRIVILEGE_ROLE,
    REVIEW_WORKER_PUCK_VERSION_PIN,
    REVIEW_WORKER_STATE_VERSION,
    ReviewWorkerConfigurationError,
    ReviewWorkerDatabaseMode,
    ReviewWorkerSettings,
)
from slaif_agent_site.review_worker.freeze_job import (
    JobResult,
    _terminal_code_for,
    run_job,
)
from slaif_agent_site.review_worker.snapshot import (
    SnapshotBuildError,
    build_snapshot_document,
    canonical_digest,
    canonical_json,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _clear_worker_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("SLAIF_REVIEW_WORKER_"):
            monkeypatch.delenv(name)


def _test_settings(**overrides: Any) -> ReviewWorkerSettings:
    values: dict[str, Any] = {
        "mode": ReviewWorkerDatabaseMode.TEST,
        "dsn": SecretStr(
            "postgresql://slaif_review_worker_login:fake-worker-password"
            "@127.0.0.1:5432/slaif"
        ),
        "dsn_file": None,
    }
    values.update(overrides)
    return ReviewWorkerSettings(**values)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------


def test_worker_settings_use_the_fixed_narrow_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_worker_env(monkeypatch)
    settings = ReviewWorkerSettings.load()
    assert settings.dsn_file == REVIEW_WORKER_DSN_FILE
    assert settings.expected_login == REVIEW_WORKER_LOGIN
    assert settings.expected_privilege_role == REVIEW_WORKER_PRIVILEGE_ROLE
    assert settings.mode is ReviewWorkerDatabaseMode.DEVELOPMENT
    assert settings.staleness_seconds == 60.0
    assert settings.drain_lock_timeout_seconds == 30.0
    assert settings.evidence_deadline_seconds == 120.0
    assert settings.heartbeat_interval_seconds == 20.0
    assert settings.batch_size == 1


def test_worker_settings_fail_fast_without_locator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_worker_env(monkeypatch)
    settings = ReviewWorkerSettings(
        mode=ReviewWorkerDatabaseMode.DEVELOPMENT,
        dsn_file=REVIEW_WORKER_DSN_FILE,
    )
    with pytest.raises(ReviewWorkerConfigurationError):
        settings.resolved_dsn()
    monkeypatch.setenv("SLAIF_REVIEW_WORKER_MODE", "test")
    monkeypatch.setenv("SLAIF_REVIEW_WORKER_DSN_FILE", "")
    with pytest.raises(ReviewWorkerConfigurationError):
        ReviewWorkerSettings.load().resolved_dsn()


def _dev_file_settings(tmp_path: Path) -> ReviewWorkerSettings:
    dsn_file = tmp_path / "review-worker-dsn"
    dsn_file.write_text(
        "postgresql://slaif_review_worker_login:fake-password@not-postgres:5432/slaif"
    )
    dsn_file.chmod(0o400)
    return ReviewWorkerSettings(
        mode=ReviewWorkerDatabaseMode.DEVELOPMENT, dsn_file=dsn_file
    )


def test_worker_settings_reject_wrong_identity_and_host(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_worker_env(monkeypatch)
    with pytest.raises(ReviewWorkerConfigurationError):
        ReviewWorkerSettings(
            mode=ReviewWorkerDatabaseMode.TEST,
            dsn=SecretStr(
                "postgresql://slaif_control_login:fake-password@127.0.0.1:5432/slaif"
            ),
            dsn_file=None,
        ).resolved_dsn()
    with pytest.raises(ReviewWorkerConfigurationError):
        _test_settings(
            dsn=SecretStr(
                "postgresql://slaif_review_worker_login:fake-password"
                "@192.0.2.1:5432/slaif"
            )
        ).resolved_dsn()
    with pytest.raises(ReviewWorkerConfigurationError):
        _dev_file_settings(tmp_path).resolved_dsn()
    with pytest.raises(ValidationError):
        _test_settings(dsn_file="relative/worker-dsn")


def test_puck_pin_matches_the_web_package_pin() -> None:
    web_package = json.loads(
        (REPOSITORY_ROOT / "apps" / "web" / "package.json").read_text()
    )
    assert (
        REVIEW_WORKER_PUCK_VERSION_PIN == web_package["dependencies"]["@measured/puck"]
    )
    assert REVIEW_WORKER_STATE_VERSION == "review-snapshot/v1"


# ---------------------------------------------------------------------
# Canonical digest and snapshot document
# ---------------------------------------------------------------------


def _valid_doc() -> dict[str, Any]:
    site_id = uuid.uuid4()
    page_id = uuid.uuid4()
    section_id = uuid.uuid4()
    heading_id = uuid.uuid4()
    return {
        "state_version": "review-snapshot/v1",
        "workspace_id": str(uuid.uuid4()),
        "site_id": str(site_id),
        "site": {
            "site_key": "unit-site",
            "display_name": "Unit Site",
            "default_locale": "en-US",
            "component_catalog_version": "catalog-v1",
        },
        "base_site_revision": 7,
        "operation_watermark": 3,
        "locales": [
            {"tag": "en-US", "enabled": True, "is_default": True, "position": 0}
        ],
        "theme": {
            "schema_version": "theme-schema/v1",
            "renderer_version": "renderer-v1",
        },
        "regions": [],
        "navigation": {"definitions": [], "items": []},
        "redirects": [],
        "pages": [
            {
                "id": str(page_id),
                "site_id": str(site_id),
                "slug": "home",
                "title": "Home",
                "status": "PUBLISHED",
                "locale": "en-US",
                "parent_id": None,
                "route_template": None,
                "effective_route": "/home",
                "row_version": 1,
                "nodes": [
                    {
                        "id": str(section_id),
                        "site_id": str(site_id),
                        "page_id": str(page_id),
                        "component_type": "Section",
                        "schema_version": "1",
                        "parent_id": None,
                        "slot_key": "default",
                        "order_key": 0,
                        "props": {},
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    },
                    {
                        "id": str(heading_id),
                        "site_id": str(site_id),
                        "page_id": str(page_id),
                        "component_type": "Heading",
                        "schema_version": "1",
                        "parent_id": str(section_id),
                        "slot_key": "default",
                        "order_key": 0,
                        "props": {"level": 1, "text": "Caf\u00e9 \U0001f600"},
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-01T00:00:00Z",
                    },
                ],
            }
        ],
        "media": {},
    }


def test_canonical_digest_is_recomputable_and_tamper_sensitive() -> None:
    doc = _valid_doc()
    row = build_snapshot_document(doc, created_by="unit-worker")
    payload = row["payload"]
    expected = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
    ).hexdigest()
    assert row["digest"] == expected
    assert canonical_digest(payload) == expected
    tampered = json.loads(json.dumps(payload))
    tampered["pages"][0]["title"] = "Tampered"
    assert canonical_digest(tampered) != expected
    assert canonical_json({"b": 1, "a": [True, None]}) == '{"a":[true,null],"b":1}'


def test_snapshot_row_shape_and_versions() -> None:
    doc = _valid_doc()
    run_id = uuid.uuid4()
    cancelled_run = uuid.uuid4()
    row = build_snapshot_document(
        doc,
        created_by="unit-worker",
        browser_evidence=[{"id": str(run_id)}],
        cancelled_runs=[
            {"id": str(cancelled_run), "previous_state": "RUNNING", "route": "/home"}
        ],
    )
    assert row["status"] == "COMPLETE"
    assert row["workspace_id"] == doc["workspace_id"]
    assert row["site_id"] == doc["site_id"]
    assert row["revision_watermark"] == 10  # base 7 + operations 3
    assert row["created_by"] == "unit-worker"
    assert row["versions"] == {
        "catalog": "catalog-v1",
        "design_system": "design-system/v1",
        "composition_schema": "site-composition/v1",
        "renderer": "renderer-v1",
        "puck": REVIEW_WORKER_PUCK_VERSION_PIN,
        "content_model": "content-model/v1",
    }
    assert row["browser_evidence"] == [{"id": str(run_id)}]
    assert row["validation_report"]["cancelled_by_freeze"] == [
        {"id": str(cancelled_run), "previous_state": "RUNNING"}
    ]
    assert row["validation_report"]["errors"] == []
    assert row["validation_report"]["pages_validated"] == 1
    assert row["normalized_state"] == row["payload"]
    # The payload carries the renderer-normalized node tree.
    root = row["payload"]["pages"][0]["nodes"][0]
    assert root["component_type"] == "Section"
    child = root["children"][0]
    assert child["component_type"] == "Heading"
    assert child["props"] == {"level": 1, "text": "Caf\u00e9 \U0001f600"}
    assert child["parent_id"] == root["id"]
    assert row["media_references"] == []


def test_snapshot_media_references_are_digest_objects_only() -> None:
    doc = _valid_doc()
    media_id = uuid.uuid4()
    doc["media"] = {
        str(media_id): {
            "id": str(media_id),
            "mime_type": "image/png",
            "size_bytes": 100,
            "content_hash": "a" * 64,
            "public_status": "private",
        }
    }
    row = build_snapshot_document(doc, created_by="unit-worker")
    assert row["media_references"] == [
        {
            "id": str(media_id),
            "mime_type": "image/png",
            "size_bytes": 100,
            "content_hash": "a" * 64,
            "public_status": "private",
        }
    ]


def test_snapshot_build_rejects_invalid_documents() -> None:
    broken = _valid_doc()
    broken["state_version"] = "review-snapshot/v2"
    with pytest.raises(SnapshotBuildError, match="SNAPSHOT_VALIDATION_FAILED"):
        build_snapshot_document(broken, created_by="unit-worker")

    missing_key = _valid_doc()
    del missing_key["media"]
    with pytest.raises(SnapshotBuildError, match="SNAPSHOT_VALIDATION_FAILED"):
        build_snapshot_document(missing_key, created_by="unit-worker")

    unknown_component = _valid_doc()
    unknown_component["pages"][0]["nodes"][0]["component_type"] = "Evil"
    with pytest.raises(SnapshotBuildError, match="SNAPSHOT_VALIDATION_FAILED"):
        build_snapshot_document(unknown_component, created_by="unit-worker")

    foreign_site_page = _valid_doc()
    foreign_site_page["pages"][0]["site_id"] = str(uuid.uuid4())
    with pytest.raises(SnapshotBuildError, match="SNAPSHOT_VALIDATION_FAILED"):
        build_snapshot_document(foreign_site_page, created_by="unit-worker")

    bad_media = _valid_doc()
    media_id = uuid.uuid4()
    bad_media["media"] = {str(media_id): {"id": str(media_id), "size_bytes": "100"}}
    with pytest.raises(SnapshotBuildError, match="SNAPSHOT_VALIDATION_FAILED"):
        build_snapshot_document(bad_media, created_by="unit-worker")

    with pytest.raises(SnapshotBuildError, match="SNAPSHOT_VALIDATION_FAILED"):
        build_snapshot_document("not-a-doc", created_by="unit-worker")


# ---------------------------------------------------------------------
# Error mapping and job dispatch
# ---------------------------------------------------------------------


class _FakeSqlError:
    def __init__(self, message: str) -> None:
        self.message = message


def test_terminal_code_maps_domain_errors_and_phases() -> None:
    assert (
        _terminal_code_for(_FakeSqlError("REVIEW_WORKSPACE_NOT_FOUND"), "drain")
        == "STATE_DRIFT"
    )
    assert (
        _terminal_code_for(_FakeSqlError("REVIEW_SITE_NOT_ACTIVE"), "materialize")
        == "STATE_DRIFT"
    )
    assert (
        _terminal_code_for(_FakeSqlError("SNAPSHOT_DIGEST_MISMATCH"), "complete")
        == "SNAPSHOT_COMPLETE_FAILED"
    )
    assert (
        _terminal_code_for(_FakeSqlError("WORKSPACE_NOT_FREEZING"), "complete")
        == "SNAPSHOT_COMPLETE_FAILED"
    )
    assert (
        _terminal_code_for(_FakeSqlError("some other failure"), "materialize")
        == "SNAPSHOT_MATERIALIZE_FAILED"
    )
    assert (
        _terminal_code_for(_FakeSqlError("some other failure"), "complete")
        == "SNAPSHOT_COMPLETE_FAILED"
    )


class _FakeConnection:
    def __init__(self, store: FakePoolStore) -> None:
        self._store = store

    async def fetchrow(self, sql: str, *args: Any) -> Any:
        if "slaif_review_job_claim" in sql:
            self._store.claims.append(args)
            if self._store.claim_error is not None:
                error = self._store.claim_error
                self._store.claim_error = None
                raise error
            return self._store.claims_queue.pop(0) if self._store.claims_queue else None
        raise AssertionError(f"unexpected fetchrow: {sql}")

    async def fetchval(self, sql: str, *args: Any) -> Any:
        if "slaif_review_job_heartbeat" in sql:
            self._store.heartbeats.append(args)
            return True
        if "slaif_review_job_terminal" in sql:
            self._store.terminals.append(args)
            return True
        raise AssertionError(f"unexpected fetchval: {sql}")

    async def fetch(self, sql: str, *args: Any) -> list[Any]:
        raise AssertionError(f"unexpected fetch: {sql}")

    async def execute(self, sql: str, *args: Any) -> None:
        raise AssertionError(f"unexpected execute: {sql}")


class FakePoolStore:
    def __init__(self) -> None:
        self.claims_queue: list[Any] = []
        self.claims: list[tuple[Any, ...]] = []
        self.heartbeats: list[tuple[Any, ...]] = []
        self.terminals: list[tuple[Any, ...]] = []
        self.claim_error: Exception | None = None


class FakePool:
    def __init__(self) -> None:
        self.store = FakePoolStore()
        self.closed = False

    def acquire(self) -> Any:
        @asynccontextmanager
        async def _acquired() -> Any:
            yield _FakeConnection(self.store)

        return _acquired()

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_run_job_dispatches_freeze_only() -> None:
    pool = FakePool()
    settings = _test_settings()
    job_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    calls: list[dict[str, Any]] = []

    async def fake_freeze_job(
        pool_: Any, settings_: ReviewWorkerSettings, job_: dict[str, Any]
    ) -> JobResult:
        calls.append(job_)
        return JobResult("SUCCEEDED")

    with patch.object(freeze_job_module, "run_freeze_job", fake_freeze_job):
        result = await run_job(
            pool,
            settings,
            {
                "id": str(job_id),
                "job_kind": "FREEZE",
                "workspace_id": str(workspace_id),
            },
        )
    assert result == JobResult("SUCCEEDED")
    assert len(calls) == 1

    from slaif_agent_site.review_worker import accept_job as accept_job_module

    async def fake_accept_job(
        pool_: Any,
        settings_: ReviewWorkerSettings,
        job_: dict[str, Any],
        media: Any = None,
    ) -> JobResult:
        calls.append(job_)
        assert media is not None
        return JobResult("SUCCEEDED")

    with patch.object(accept_job_module, "run_accept_job", fake_accept_job):
        result = await run_job(
            pool,
            settings,
            {
                "id": str(job_id),
                "job_kind": "ACCEPT",
                "workspace_id": str(workspace_id),
            },
        )
    assert result == JobResult("SUCCEEDED")
    assert len(calls) == 2
    assert calls[1]["job_kind"] == "ACCEPT"

    # DISCARD is not implemented in this increment (083/2): unsupported.
    for kind in ("DISCARD", "OTHER"):
        result = await run_job(pool, settings, {"id": str(job_id), "job_kind": kind})
        assert result == JobResult("FAILED", "JOB_KIND_UNSUPPORTED")
        assert pool.store.terminals
        assert pool.store.terminals[-1][1:] == ("FAILED", "JOB_KIND_UNSUPPORTED")


# ---------------------------------------------------------------------
# Claim/execute loop
# ---------------------------------------------------------------------


class _JobRow:
    def __init__(self, job: dict[str, Any]) -> None:
        self._job = job

    def __getitem__(self, key: str) -> Any:
        return self._job[key]

    def keys(self) -> Any:
        return self._job.keys()

    def __iter__(self) -> Iterator[str]:
        return iter(self._job)


@pytest.mark.asyncio
async def test_worker_loop_claims_executes_and_stops() -> None:
    pool = FakePool()
    settings = _test_settings(poll_interval_seconds=0.1)
    stop = asyncio.Event()
    job_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    job = {
        "id": str(job_id),
        "job_kind": "FREEZE",
        "workspace_id": str(workspace_id),
        "site_id": str(uuid.uuid4()),
        "attempt_count": 1,
        "max_attempts": 3,
        "claimed_by": "review-worker-test",
    }
    pool.store.claims_queue = [_JobRow(job)]

    executed: list[str] = []

    async def stopping_job(
        pool_: Any, settings_: Any, job_: dict[str, Any]
    ) -> JobResult:
        executed.append(str(job_["id"]))
        stop.set()
        return JobResult("SUCCEEDED")

    with patch.object(worker_module, "run_job", stopping_job):
        task = asyncio.create_task(worker_module._worker_loop(pool, settings, stop))
        await asyncio.wait_for(task, timeout=5)
    assert executed == [str(job_id)]
    assert len(pool.store.claims) == 1


@pytest.mark.asyncio
async def test_worker_loop_survives_claim_and_job_failures() -> None:
    pool = FakePool()
    settings = _test_settings(poll_interval_seconds=0.1)
    stop = asyncio.Event()
    job_id = uuid.uuid4()
    job = {
        "id": str(job_id),
        "job_kind": "FREEZE",
        "workspace_id": str(uuid.uuid4()),
        "site_id": str(uuid.uuid4()),
        "attempt_count": 1,
        "max_attempts": 3,
        "claimed_by": "review-worker-test",
    }
    pool.store.claim_error = asyncpg.ConnectionDoesNotExistError()
    pool.store.claims_queue = [_JobRow(job)]

    state = {"jobs": 0}

    async def flaky_run_job(
        pool_: Any, settings_: Any, job_: dict[str, Any]
    ) -> JobResult:
        state["jobs"] += 1
        stop.set()
        if state["jobs"] == 1:
            raise RuntimeError("boom")
        return JobResult("SUCCEEDED")

    with patch.object(worker_module, "run_job", flaky_run_job):
        task = asyncio.create_task(worker_module._worker_loop(pool, settings, stop))
        await asyncio.wait_for(task, timeout=5)
    assert state["jobs"] == 1  # the crash did not stop the loop
    assert len(pool.store.claims) == 2  # one failed claim + one job claim


@pytest.mark.asyncio
async def test_worker_loop_heartbeats_a_long_job() -> None:
    pool = FakePool()
    settings = _test_settings(poll_interval_seconds=0.1, heartbeat_interval_seconds=1.0)
    stop = asyncio.Event()
    job_id = uuid.uuid4()
    job = {
        "id": str(job_id),
        "job_kind": "FREEZE",
        "workspace_id": str(uuid.uuid4()),
        "site_id": str(uuid.uuid4()),
        "attempt_count": 1,
        "max_attempts": 3,
        "claimed_by": "review-worker-test",
    }
    pool.store.claims_queue = [_JobRow(job)]

    async def slow_run_job(
        pool_: Any, settings_: Any, job_: dict[str, Any]
    ) -> JobResult:
        await asyncio.sleep(1.4)
        stop.set()
        return JobResult("SUCCEEDED")

    with patch.object(worker_module, "run_job", slow_run_job):
        task = asyncio.create_task(worker_module._worker_loop(pool, settings, stop))
        await asyncio.wait_for(task, timeout=10)
    assert pool.store.heartbeats
    assert all(args[0] == str(job_id) for args in pool.store.heartbeats)

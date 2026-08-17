"""Import, check-mode, and non-listening lifecycle process contracts."""

from __future__ import annotations

import asyncio
import importlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from slaif_agent_site.application import run_http_process
from slaif_agent_site.authority import LifecycleKind, ProcessKind, authority_for
from slaif_agent_site.worker import run_worker_process, serve_worker

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
MODULE_BY_PROCESS = {
    ProcessKind.CONTROL_API: "control_api",
    ProcessKind.EDITOR_API: "editor_api",
    ProcessKind.AGENT_API: "agent_api",
    ProcessKind.RENDER_API: "render_api",
    ProcessKind.MCP_ADAPTER: "mcp_adapter",
    ProcessKind.MEDIA_SERVICE: "media_service",
    ProcessKind.REVIEW_WORKER: "review_worker",
    ProcessKind.SCHEDULER: "scheduler",
    ProcessKind.MEDIA_GC: "media_gc",
    ProcessKind.BOOTSTRAP: "bootstrap",
}


@pytest.mark.parametrize("process", tuple(ProcessKind))
def test_all_process_packages_import_without_startup_side_effect(
    process: ProcessKind,
) -> None:
    module = importlib.import_module(f"slaif_agent_site.{MODULE_BY_PROCESS[process]}")
    descriptor = authority_for(process)
    if descriptor.lifecycle is LifecycleKind.HTTP:
        app = module.create_app()
        assert isinstance(app, FastAPI)
        assert app.state.process_kind is process
    else:
        assert not hasattr(module, "create_app")


@pytest.mark.parametrize("process", tuple(ProcessKind))
def test_all_module_check_entrypoints_exit_without_listener_or_work(
    process: ProcessKind,
) -> None:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("SLAIF_")
    }
    environment["SLAIF_MODE"] = "test"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            f"slaif_agent_site.{MODULE_BY_PROCESS[process]}",
            "--check",
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0
    assert completed.stdout.strip() == f"{process.value}: CHECK_OK"
    assert completed.stderr == ""


def test_http_check_does_not_call_uvicorn_and_normal_run_passes_app_object() -> None:
    with patch("slaif_agent_site.application.uvicorn.run") as uvicorn_run:
        assert run_http_process(ProcessKind.AGENT_API, argv=["--check"]) == 0
        uvicorn_run.assert_not_called()

        assert run_http_process(ProcessKind.AGENT_API, argv=[]) == 0
        uvicorn_run.assert_called_once()
        assert isinstance(uvicorn_run.call_args.args[0], FastAPI)
        assert uvicorn_run.call_args.kwargs["host"] == "127.0.0.1"
        assert uvicorn_run.call_args.kwargs["port"] == 8000


@pytest.mark.parametrize(
    "process",
    (
        ProcessKind.REVIEW_WORKER,
        ProcessKind.SCHEDULER,
        ProcessKind.MEDIA_GC,
        ProcessKind.BOOTSTRAP,
    ),
)
async def test_non_listening_lifecycle_runs_injected_placeholder_once(
    process: ProcessKind,
) -> None:
    calls = 0

    async def runner(stop: asyncio.Event) -> None:
        nonlocal calls
        calls += 1
        stop.set()

    await serve_worker(process, runner)
    assert calls == 1


async def test_http_authority_cannot_use_worker_lifecycle() -> None:
    async def runner(stop: asyncio.Event) -> None:
        stop.set()

    with pytest.raises(ValueError, match="cannot use the worker lifecycle"):
        await serve_worker(ProcessKind.AGENT_API, runner)


def test_bootstrap_normal_mode_is_one_shot_and_non_mutating() -> None:
    assert run_worker_process(ProcessKind.BOOTSTRAP, argv=[]) == 0


def test_worker_check_does_not_call_injected_runner() -> None:
    called = False

    async def runner(stop: asyncio.Event) -> None:
        nonlocal called
        called = True
        stop.set()

    assert (
        run_worker_process(
            ProcessKind.REVIEW_WORKER,
            argv=["--check"],
            runner=runner,
        )
        == 0
    )
    assert called is False


def test_worker_packages_and_shared_lifecycle_have_no_uvicorn_or_database_use() -> None:
    source_root = REPOSITORY_ROOT / "services/backend/src/slaif_agent_site"
    paths = [source_root / "worker.py"]
    for process in (
        ProcessKind.REVIEW_WORKER,
        ProcessKind.SCHEDULER,
        ProcessKind.MEDIA_GC,
        ProcessKind.BOOTSTRAP,
    ):
        package = source_root / MODULE_BY_PROCESS[process]
        paths.extend(sorted(package.glob("*.py")))
        assert not (package / "app.py").exists()
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "uvicorn" not in source.casefold()
    assert "asyncpg" not in source.casefold()
    assert "database_url" not in source.casefold()

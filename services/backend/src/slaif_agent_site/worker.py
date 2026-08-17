"""Cancellation-aware lifecycle for non-listening worker/bootstrap skeletons."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable, Sequence

from .authority import LifecycleKind, ProcessKind, authority_for
from .config import ConfigurationError, ServiceSettings
from .logging import configure_json_logging

LOGGER = logging.getLogger(__name__)
WorkerRunner = Callable[[asyncio.Event], Awaitable[None]]


async def idle_placeholder(stop: asyncio.Event) -> None:
    """Wait efficiently for shutdown; no job or database behavior exists yet."""

    await stop.wait()


async def one_shot_placeholder(stop: asyncio.Event) -> None:
    """Return without migration/setup mutation for the bootstrap skeleton."""

    stop.set()


async def serve_worker(process: ProcessKind, runner: WorkerRunner) -> None:
    """Run one injected placeholder with deterministic signal cleanup."""

    descriptor = authority_for(process)
    if descriptor.has_listener or descriptor.lifecycle is LifecycleKind.HTTP:
        raise ValueError("HTTP processes cannot use the worker lifecycle")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    installed: list[signal.Signals] = []
    for selected_signal in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(selected_signal, stop.set)
            installed.append(selected_signal)
        except (NotImplementedError, RuntimeError, ValueError):
            continue

    LOGGER.warning(
        "worker skeleton is idle",
        extra={
            "event_fields": {
                "process": process.value,
                "status": "NOT_IMPLEMENTED",
            }
        },
    )
    try:
        await runner(stop)
    finally:
        for selected_signal in installed:
            loop.remove_signal_handler(selected_signal)
        LOGGER.info(
            "worker skeleton stopped",
            extra={"event_fields": {"process": process.value}},
        )


def run_worker_process(
    process: ProcessKind,
    *,
    argv: Sequence[str] | None = None,
    runner: WorkerRunner | None = None,
) -> int:
    """Check or start a process that can never bind an HTTP listener."""

    module_name = process.value.replace("-", "_")
    parser = argparse.ArgumentParser(prog=f"python -m slaif_agent_site.{module_name}")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate configuration and authority without running work",
    )
    args = parser.parse_args(argv)
    descriptor = authority_for(process)
    if descriptor.has_listener or descriptor.lifecycle is LifecycleKind.HTTP:
        parser.error("selected process is not a worker/bootstrap process")
    try:
        settings = ServiceSettings.load()
    except ConfigurationError as exc:
        parser.exit(2, f"{exc}\n")

    if args.check:
        print(f"{process.value}: CHECK_OK")
        return 0

    configure_json_logging(service=process.value, level=settings.log_level.value)
    selected_runner = runner
    if selected_runner is None:
        selected_runner = (
            one_shot_placeholder
            if descriptor.lifecycle is LifecycleKind.ONE_SHOT
            else idle_placeholder
        )
    asyncio.run(serve_worker(process, selected_runner))
    return 0


__all__ = [
    "WorkerRunner",
    "idle_placeholder",
    "one_shot_placeholder",
    "run_worker_process",
    "serve_worker",
]

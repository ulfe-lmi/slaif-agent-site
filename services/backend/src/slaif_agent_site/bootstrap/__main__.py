"""Explicit command-line boundary for database bootstrap operations."""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

from .config import BootstrapSettings
from .service import (
    compose_bootstrap,
    downgrade,
    provision,
    rebuild,
    reconcile,
    status,
    upgrade,
    validate,
)

SAFE_FAILURE = "Database bootstrap failed."


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.bootstrap")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the local command boundary without loading database settings",
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("provision", help="reconcile password-free privilege roles")
    commands.add_parser("upgrade", help="upgrade owner migrations to head")
    commands.add_parser("bootstrap", help="upgrade and reconcile COW privileges")
    commands.add_parser(
        "compose", help="provision and validate the local Compose database"
    )
    commands.add_parser("validate", help="validate marker and effective privileges")
    commands.add_parser("current", help="show the current migration and safe state")
    for name in ("downgrade", "rebuild"):
        command = commands.add_parser(name, help=f"disposable database {name}")
        command.add_argument("--confirm-disposable", action="store_true")
    return parser


async def _run(command: str, settings: BootstrapSettings) -> str:
    if command == "provision":
        await provision(settings)
        return "provision: OK"
    if command == "upgrade":
        await upgrade(settings)
        return "upgrade: OK"
    if command == "bootstrap":
        await upgrade(settings)
        bootstrap_status = await reconcile(settings)
        return (
            f"bootstrap: OK revision={bootstrap_status.revision} "
            f"state={bootstrap_status.state.value} "
            f"safe={str(bootstrap_status.safe).lower()}"
        )
    if command == "compose":
        compose_status = await compose_bootstrap(settings)
        return (
            f"compose-bootstrap: OK revision={compose_status.revision} "
            f"state={compose_status.state.value} safe=true"
        )
    if command == "validate":
        marker, validation = await validate(settings)
        if not validation.safe:
            raise RuntimeError("database privilege validation failed")
        return (
            f"validate: OK revision={marker.revision} "
            f"state={marker.state.value} safe=true"
        )
    if command == "current":
        current_status = await status(settings)
        return (
            f"current: revision={current_status.revision} "
            f"state={current_status.state.value} "
            f"safe={str(current_status.safe).lower()}"
        )
    if command == "downgrade":
        await downgrade(settings)
        return "downgrade: OK"
    if command == "rebuild":
        await rebuild(settings)
        return "rebuild: OK"
    raise ValueError("unknown bootstrap command")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    if arguments.check:
        if arguments.command is not None:
            parser.error("--check cannot be combined with a database command")
        print("bootstrap: CHECK_OK")
        return 0
    if arguments.command is None:
        parser.print_usage(sys.stderr)
        return 2
    if (
        arguments.command in {"downgrade", "rebuild"}
        and not arguments.confirm_disposable
    ):
        parser.error("disposable database confirmation is required")
    try:
        settings = BootstrapSettings.load()
        output = asyncio.run(_run(arguments.command, settings))
    except Exception:
        print(SAFE_FAILURE, file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

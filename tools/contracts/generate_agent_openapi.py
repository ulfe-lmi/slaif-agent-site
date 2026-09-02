"""Generate and verify the canonical public Agent OpenAPI contract."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from slaif_agent_site.agent_api.app import create_app, public_agent_openapi_bytes
from slaif_agent_site.agent_api.config import AgentDatabaseMode, AgentDatabaseSettings
from slaif_agent_site.config import ServiceSettings
from slaif_agent_site.health import ProbeResult

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "contracts/openapi/agent-v1.json"


class _ContractDatabase:
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def readiness(self) -> ProbeResult:
        return ProbeResult.ready()

    def cow_pool(self) -> None:
        return None

    async def authenticate_agent_capability(self, _auth_header: str) -> None:
        return None


def generate_agent_openapi() -> bytes:
    app = create_app(
        settings=ServiceSettings.for_test(),
        database_settings=AgentDatabaseSettings(mode=AgentDatabaseMode.TEST),
        database=_ContractDatabase(),
    )
    return public_agent_openapi_bytes(app)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate_agent_openapi")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    generated = generate_agent_openapi()
    if arguments.check:
        if not CONTRACT_PATH.is_file() or CONTRACT_PATH.read_bytes() != generated:
            parser.error(f"contract drift: {CONTRACT_PATH.relative_to(ROOT)}")
        print(f"agent-openapi: OK {CONTRACT_PATH.relative_to(ROOT)}")
        return 0
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_bytes(generated)
    print(f"agent-openapi: WROTE {CONTRACT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

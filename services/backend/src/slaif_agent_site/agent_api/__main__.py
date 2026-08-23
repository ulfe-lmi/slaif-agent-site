"""Start the Agent API process."""

from .app import run_agent_process


def main() -> int:
    return run_agent_process()


if __name__ == "__main__":
    raise SystemExit(main())

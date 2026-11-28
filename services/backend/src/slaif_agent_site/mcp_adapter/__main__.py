"""Start the MCP adapter process."""

from .app import run_mcp_process


def main() -> int:
    return run_mcp_process()


if __name__ == "__main__":
    raise SystemExit(main())

"""Start the MCP adapter process."""

from ..application import run_http_process
from ..authority import ProcessKind


def main() -> int:
    return run_http_process(ProcessKind.MCP_ADAPTER)


if __name__ == "__main__":
    raise SystemExit(main())

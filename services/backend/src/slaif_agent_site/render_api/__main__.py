"""Start the internal Render API process."""

from ..application import run_http_process
from ..authority import ProcessKind


def main() -> int:
    return run_http_process(ProcessKind.RENDER_API)


if __name__ == "__main__":
    raise SystemExit(main())

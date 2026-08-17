"""Start the one-shot, non-mutating bootstrap skeleton."""

from ..authority import ProcessKind
from ..worker import run_worker_process


def main() -> int:
    return run_worker_process(ProcessKind.BOOTSTRAP)


if __name__ == "__main__":
    raise SystemExit(main())

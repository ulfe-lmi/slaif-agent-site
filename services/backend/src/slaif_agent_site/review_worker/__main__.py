"""Start the non-listening review-worker skeleton."""

from ..authority import ProcessKind
from ..worker import run_worker_process


def main() -> int:
    return run_worker_process(ProcessKind.REVIEW_WORKER)


if __name__ == "__main__":
    raise SystemExit(main())

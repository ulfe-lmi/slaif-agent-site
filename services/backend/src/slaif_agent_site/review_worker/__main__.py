"""Start the durable review-worker process."""

from ..authority import ProcessKind
from ..worker import run_worker_process
from .worker import run_review_worker


def main() -> int:
    return run_worker_process(ProcessKind.REVIEW_WORKER, runner=run_review_worker)


if __name__ == "__main__":
    raise SystemExit(main())

"""Start the non-listening media-GC skeleton."""

from ..authority import ProcessKind
from ..worker import run_worker_process


def main() -> int:
    return run_worker_process(ProcessKind.MEDIA_GC)


if __name__ == "__main__":
    raise SystemExit(main())

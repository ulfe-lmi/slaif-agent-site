"""Start the Control API process through its package-local database lifespan."""

from .app import run_control_process


def main() -> int:
    return run_control_process()


if __name__ == "__main__":
    raise SystemExit(main())

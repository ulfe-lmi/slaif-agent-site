"""Start the Editor API process."""

from .app import run_editor_process


def main() -> int:
    return run_editor_process()


if __name__ == "__main__":
    raise SystemExit(main())

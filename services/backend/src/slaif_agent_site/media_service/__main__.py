"""Start the authenticated Media service process."""

from .app import run_media_process


def main() -> int:
    return run_media_process()


if __name__ == "__main__":
    raise SystemExit(main())

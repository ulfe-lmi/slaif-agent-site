"""Start the internal Render API process."""

import argparse

import uvicorn

from ..authority import ProcessKind
from ..config import ConfigurationError, ServiceSettings
from ..logging import configure_json_logging
from .app import create_app
from .config import (
    RenderDatabaseConfigurationError,
    RenderDatabaseSettings,
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m slaif_agent_site.render_api")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        settings = ServiceSettings.load()
        database_settings = RenderDatabaseSettings.load()
        app = create_app(settings=settings, database_settings=database_settings)
    except (ConfigurationError, RenderDatabaseConfigurationError) as error:
        parser.exit(2, f"{error}\n")
    if args.check:
        print("render-api: CHECK_OK")
        return 0
    configure_json_logging(
        service=ProcessKind.RENDER_API.value, level=settings.log_level.value
    )
    uvicorn.run(
        app,
        host=settings.bind_host,
        port=settings.bind_port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=settings.shutdown_timeout_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

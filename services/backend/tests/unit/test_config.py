"""Typed settings, secret source, and production failure contracts."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import HttpUrl, SecretStr, ValidationError
from slaif_agent_site.config import (
    ConfigurationError,
    EnvironmentMode,
    LogLevel,
    ServiceSettings,
)

STRONG_TEST_SECRET = "local-fixture-value-with-32-plus-unique-chars"


def test_deterministic_test_settings_have_no_production_secret() -> None:
    first = ServiceSettings.for_test()
    second = ServiceSettings.for_test()
    assert first == second
    assert first.mode is EnvironmentMode.TEST
    assert first.app_secret is None
    assert first.app_secret_file is None
    assert first.resolved_app_secret() is None
    assert "database" not in " ".join(ServiceSettings.model_fields).casefold()


def test_slaif_environment_and_explicit_development_file(tmp_path: Path) -> None:
    env_file = tmp_path / "development.env"
    env_file.write_text(
        "SLAIF_LOG_LEVEL=DEBUG\nSLAIF_BIND_PORT=8123\n",
        encoding="utf-8",
    )
    environment = {
        "SLAIF_MODE": "development",
        "SLAIF_ENV_FILE": str(env_file),
        "SLAIF_BIND_HOST": "127.0.0.2",
    }
    with patch.dict(os.environ, environment, clear=True):
        settings = ServiceSettings.load()

    assert settings.mode is EnvironmentMode.DEVELOPMENT
    assert settings.log_level is LogLevel.DEBUG
    assert settings.bind_port == 8123
    assert settings.bind_host == "127.0.0.2"
    assert settings.env_file == env_file


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, "production secret"),
        ({"public_url": "http://example.test"}, "HTTPS"),
        ({"secure_cookies": False}, "secure cookies"),
        ({"app_secret": SecretStr("change-me")}, "weak"),
    ],
)
def test_production_fails_closed(overrides: dict[str, object], expected: str) -> None:
    values: dict[str, object] = {
        "mode": EnvironmentMode.PRODUCTION,
        "public_url": "https://example.test",
        "secure_cookies": True,
        "app_secret": SecretStr(STRONG_TEST_SECRET),
    }
    if not overrides:
        values.pop("app_secret")
    else:
        values.update(overrides)
    with pytest.raises(ValidationError, match=expected):
        ServiceSettings.model_validate(values)


def test_valid_production_secret_is_masked_in_repr_and_json() -> None:
    settings = ServiceSettings(
        mode=EnvironmentMode.PRODUCTION,
        public_url=HttpUrl("https://example.test"),
        secure_cookies=True,
        app_secret=SecretStr(STRONG_TEST_SECRET),
    )
    assert settings.resolved_app_secret() is not None
    assert STRONG_TEST_SECRET not in repr(settings)
    assert STRONG_TEST_SECRET not in settings.model_dump_json()


def test_absolute_mounted_secret_file_is_supported(tmp_path: Path) -> None:
    secret_file = tmp_path / "app-secret"
    secret_file.write_text(STRONG_TEST_SECRET + "\n", encoding="utf-8")
    settings = ServiceSettings(
        mode=EnvironmentMode.PRODUCTION,
        public_url=HttpUrl("https://example.test"),
        secure_cookies=True,
        app_secret_file=secret_file,
    )
    resolved = settings.resolved_app_secret()
    assert resolved is not None
    assert resolved.get_secret_value() == STRONG_TEST_SECRET
    assert STRONG_TEST_SECRET not in repr(settings)


def test_secret_sources_and_file_modes_are_restricted(tmp_path: Path) -> None:
    relative = Path("relative-secret")
    with pytest.raises(ValidationError, match="absolute"):
        ServiceSettings(app_secret_file=relative)
    with pytest.raises(ValidationError, match="one secret source"):
        ServiceSettings(
            app_secret=SecretStr(STRONG_TEST_SECRET),
            app_secret_file=tmp_path / "secret",
        )
    with pytest.raises(ValidationError, match="development-only"):
        ServiceSettings(mode=EnvironmentMode.TEST, env_file=tmp_path / "test.env")


def test_public_url_bind_and_bounds_validation() -> None:
    invalid_values = (
        {"public_url": "https://user:password@example.test"},
        {"public_url": "https://example.test/?token=value"},
        {"bind_host": "bad host"},
        {"bind_port": 0},
        {"readiness_timeout_seconds": 31},
        {"shutdown_timeout_seconds": 121},
        {"log_format": "text"},
    )
    for values in invalid_values:
        with pytest.raises(ValidationError):
            ServiceSettings.model_validate(values)


def test_load_error_is_constant_and_does_not_expose_secret() -> None:
    unsafe_value = "password=local-fixture-do-not-expose"
    environment = {
        "SLAIF_MODE": "production",
        "SLAIF_PUBLIC_URL": "https://example.test",
        "SLAIF_SECURE_COOKIES": "true",
        "SLAIF_APP_SECRET": unsafe_value,
    }
    with patch.dict(os.environ, environment, clear=True):
        with pytest.raises(ConfigurationError) as context:
            ServiceSettings.load()
    assert str(context.value) == "Invalid SLAIF service configuration."
    assert unsafe_value not in str(context.value)

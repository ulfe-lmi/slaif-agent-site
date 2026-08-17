"""Control-only database settings and secret-redaction contracts."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.control_api.config import (
    CONTROL_LOGIN,
    CONTROL_PRIVILEGE_ROLE,
    ControlDatabaseConfigurationError,
    ControlDatabaseMode,
    ControlDatabaseSettings,
)


def _direct_locator(
    *, host: str = "example.test", login: str = CONTROL_LOGIN, database: str = "slaif"
) -> str:
    return f"postgresql://{login}:fake-control-password@{host}:5432/{database}"


def _write_locator(path: Path, value: str) -> None:
    path.write_text(value, encoding="ascii")
    path.chmod(0o400)


def test_test_mode_allows_only_one_direct_fake_locator_and_masks_it() -> None:
    locator = _direct_locator()
    settings = ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
    )
    assert settings.resolved_dsn().get_secret_value() == locator
    assert locator not in repr(settings)
    assert locator not in settings.model_dump_json()
    assert settings.expected_login == CONTROL_LOGIN
    assert settings.expected_privilege_role == CONTROL_PRIVILEGE_ROLE

    with pytest.raises(ValidationError, match="mounted file"):
        ControlDatabaseSettings(
            mode=ControlDatabaseMode.DEVELOPMENT,
            dsn=SecretStr(locator),
            dsn_file=None,
        )
    with pytest.raises(ValidationError, match="one Control"):
        ControlDatabaseSettings(
            mode=ControlDatabaseMode.TEST,
            dsn=SecretStr(locator),
            dsn_file=Path("/run/control-dsn"),
        )


def test_file_locator_requires_absolute_owned_regular_mode_0400(tmp_path: Path) -> None:
    locator_file = tmp_path / "control-dsn"
    locator = _direct_locator(host="postgres")
    _write_locator(locator_file, locator)
    settings = ControlDatabaseSettings(
        mode=ControlDatabaseMode.DEVELOPMENT,
        dsn_file=locator_file,
    )
    assert settings.resolved_dsn().get_secret_value() == locator

    locator_file.chmod(0o600)
    with pytest.raises(ControlDatabaseConfigurationError) as context:
        settings.resolved_dsn()
    assert str(context.value) == "Invalid SLAIF Control database configuration."
    assert locator not in str(context.value)

    with pytest.raises(ValidationError, match="absolute"):
        ControlDatabaseSettings(dsn_file=Path("relative-control-dsn"))


def test_production_requires_verify_full_and_root_certificate(tmp_path: Path) -> None:
    locator_file = tmp_path / "control-dsn"
    secure_locator = (
        _direct_locator(host="database.example.test")
        + "?sslmode=verify-full&sslrootcert=%2Frun%2Ftls%2Froot.pem"
        + "&target_session_attrs=read-write"
    )
    _write_locator(locator_file, secure_locator)
    settings = ControlDatabaseSettings(
        mode=ControlDatabaseMode.PRODUCTION,
        dsn_file=locator_file,
    )
    assert settings.resolved_dsn().get_secret_value() == secure_locator

    locator_file.chmod(0o600)
    _write_locator(locator_file, _direct_locator(host="database.example.test"))
    with pytest.raises(ControlDatabaseConfigurationError):
        settings.resolved_dsn()

    locator_file.chmod(0o600)
    _write_locator(
        locator_file,
        _direct_locator(host="database.example.test")
        + "?sslmode=verify-full&sslrootcert=root.pem"
        + "&target_session_attrs=read-write",
    )
    with pytest.raises(ControlDatabaseConfigurationError):
        settings.resolved_dsn()


@pytest.mark.parametrize(
    "locator",
    (
        "postgresql://other:fake@example.test:5432/slaif",
        _direct_locator(database="other"),
        _direct_locator() + "?options=-csearch_path%3Dpublic",
        _direct_locator() + "?target_session_attrs=any",
        _direct_locator(host="external.invalid"),
    ),
)
def test_locator_identity_options_and_fake_host_fail_closed(locator: str) -> None:
    settings = ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
    )
    with pytest.raises(ControlDatabaseConfigurationError) as context:
        settings.resolved_dsn()
    assert locator not in str(context.value)


@pytest.mark.parametrize(
    "values",
    (
        {"pool_min_size": 3, "pool_max_size": 2},
        {"pool_max_size": 17},
        {"acquire_timeout_seconds": 0},
        {"command_timeout_seconds": 31},
        {"connect_timeout_seconds": 31},
        {"shutdown_timeout_seconds": 31},
        {"max_inactive_connection_lifetime_seconds": 0},
        {"statement_timeout_ms": 49},
        {"lock_timeout_ms": 9},
        {"idle_transaction_timeout_ms": 49},
        {"application_name": "INVALID application"},
        {"expected_database": "bad-name"},
    ),
)
def test_pool_timeout_identity_and_application_bounds(
    values: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ControlDatabaseSettings.model_validate(values)


def test_non_test_identity_is_fixed_but_test_login_can_be_a_fixture() -> None:
    with pytest.raises(ValidationError, match="fixed authority"):
        ControlDatabaseSettings(expected_login="other_login")
    fixture = ControlDatabaseSettings(
        mode=ControlDatabaseMode.TEST,
        dsn=SecretStr(
            _direct_locator(login="fixture_control", database="fixture_database")
        ),
        dsn_file=None,
        expected_database="fixture_database",
        expected_login="fixture_control",
    )
    assert fixture.expected_privilege_role == CONTROL_PRIVILEGE_ROLE


def test_load_uses_only_control_prefix_and_failure_is_constant() -> None:
    environment = {
        "SLAIF_CONTROL_MODE": "test",
        "SLAIF_CONTROL_DSN": _direct_locator(),
        "SLAIF_CONTROL_POOL_MIN_SIZE": "2",
        "SLAIF_CONTROL_POOL_MAX_SIZE": "3",
        "SLAIF_MODE": "production",
    }
    with patch.dict(os.environ, environment, clear=True):
        settings = ControlDatabaseSettings.load()
    assert settings.mode is ControlDatabaseMode.TEST
    assert settings.pool_min_size == 2
    assert settings.pool_max_size == 3

    unsafe = "postgresql://slaif_control_login:do-not-print@example.test/bad-name"
    with patch.dict(
        os.environ,
        {
            "SLAIF_CONTROL_MODE": "test",
            "SLAIF_CONTROL_DSN": unsafe,
            "SLAIF_CONTROL_EXPECTED_DATABASE": "bad-name",
        },
        clear=True,
    ):
        with pytest.raises(ControlDatabaseConfigurationError) as context:
            ControlDatabaseSettings.load()
    assert str(context.value) == "Invalid SLAIF Control database configuration."
    assert unsafe not in str(context.value)

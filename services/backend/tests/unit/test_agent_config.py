"""Least-privilege Agent database settings contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.agent_api.config import (
    AGENT_APPLICATION_NAME,
    AGENT_BROWSER_SIGNING_KEY_FILE,
    AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE,
    AGENT_DSN_FILE,
    AGENT_LOGIN,
    AGENT_PRIVILEGE_ROLE,
    AgentDatabaseConfigurationError,
    AgentDatabaseMode,
    AgentDatabaseSettings,
)


def _locator(
    *, host: str = "example.test", login: str = AGENT_LOGIN, database: str = "slaif"
) -> str:
    return f"postgresql://{login}:fake-agent-password@{host}:5432/{database}"


def test_agent_settings_are_fixed_and_secret_safe() -> None:
    locator = _locator()
    settings = AgentDatabaseSettings(
        mode=AgentDatabaseMode.TEST,
        dsn=SecretStr(locator),
        dsn_file=None,
    )
    assert settings.resolved_dsn().get_secret_value() == locator
    assert settings.expected_login == AGENT_LOGIN
    assert settings.expected_privilege_role == AGENT_PRIVILEGE_ROLE
    assert settings.application_name == AGENT_APPLICATION_NAME
    assert AGENT_DSN_FILE == Path("/run/slaif-agent/agent-dsn")
    assert AGENT_BROWSER_SIGNING_KEY_FILE == Path(
        "/run/slaif-browser-signing/signing-key"
    )
    assert AGENT_BROWSER_WORKER_SERVICE_CREDENTIAL_FILE == Path(
        "/run/slaif-browser-worker/worker-token"
    )
    assert settings.browser_worker_endpoint == "http://browser-worker:3100"
    assert locator not in repr(settings)
    assert locator not in settings.model_dump_json()

    with pytest.raises(ValidationError, match="fixed authority"):
        AgentDatabaseSettings(expected_login="slaif_control_login")
    with pytest.raises(ValidationError, match="privilege role is fixed"):
        AgentDatabaseSettings(expected_privilege_role="slaif_control")
    with pytest.raises(ValidationError, match="absolute"):
        AgentDatabaseSettings(browser_signing_key_file=Path("relative-key"))
    with pytest.raises(ValidationError, match="absolute"):
        AgentDatabaseSettings(
            browser_worker_service_credential_file=Path("relative-worker-token")
        )
    with pytest.raises(ValidationError, match="endpoint is fixed"):
        AgentDatabaseSettings(browser_worker_endpoint="http://agent-api:3100")


def test_agent_production_requires_secure_mounted_locator(tmp_path: Path) -> None:
    locator_file = tmp_path / "agent-dsn"
    secure_locator = (
        _locator(host="database.example.test")
        + "?sslmode=verify-full&sslrootcert=%2Frun%2Ftls%2Froot.pem"
        + "&target_session_attrs=read-write"
    )
    locator_file.write_text(secure_locator, encoding="ascii")
    locator_file.chmod(0o400)
    settings = AgentDatabaseSettings(
        mode=AgentDatabaseMode.PRODUCTION,
        dsn_file=locator_file,
    )
    assert settings.resolved_dsn().get_secret_value() == secure_locator

    with pytest.raises(ValidationError, match="absolute"):
        AgentDatabaseSettings(dsn_file=Path("relative-agent-dsn"))


def test_agent_locator_rejects_wrong_identity_and_host() -> None:
    for locator in (
        _locator(login="slaif_control_login"),
        _locator(database="other"),
        _locator(host="external.invalid"),
    ):
        settings = AgentDatabaseSettings(
            mode=AgentDatabaseMode.TEST,
            dsn=SecretStr(locator),
            dsn_file=None,
        )
        with pytest.raises(AgentDatabaseConfigurationError) as error:
            settings.resolved_dsn()
        assert locator not in str(error.value)

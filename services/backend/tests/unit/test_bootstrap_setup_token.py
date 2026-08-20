"""Setup-token cryptography, configuration, result, and CLI unit contracts."""

from __future__ import annotations

import argparse
import hashlib
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.bootstrap import __main__ as bootstrap_cli
from slaif_agent_site.bootstrap.config import BootstrapMode, BootstrapSettings
from slaif_agent_site.bootstrap.service import (
    SetupTokenAction,
    SetupTokenResult,
    SetupTokenStatus,
)
from slaif_agent_site.bootstrap.setup_token import (
    SETUP_TOKEN_PREFIX,
    SETUP_TOKEN_RANDOM_BYTES,
    InvalidSetupToken,
    digest_setup_token,
    generate_setup_token,
    setup_token_matches,
)


def _token(seed: int = 7) -> SecretStr:
    return generate_setup_token(lambda size: bytes([seed]) * size)


def _settings(**updates: object) -> BootstrapSettings:
    values: dict[str, object] = {
        "mode": BootstrapMode.TEST,
        "expected_database": "qualification",
        "owner_dsn": SecretStr("postgresql://fixture/qualification"),
    }
    values.update(updates)
    return BootstrapSettings.model_validate(values)


def _status(*, token_present: bool = True) -> SetupTokenStatus:
    return SetupTokenStatus(
        initialized=False,
        token_present=token_present,
        token_expired=False,
        expires_at=datetime.now(UTC) + timedelta(minutes=30) if token_present else None,
        generation=1,
    )


def test_token_format_entropy_and_digest_are_deterministic() -> None:
    requested: list[int] = []

    def deterministic_random(size: int) -> bytes:
        requested.append(size)
        return bytes(range(size))

    token = generate_setup_token(deterministic_random)
    plaintext = token.get_secret_value()
    assert requested == [SETUP_TOKEN_RANDOM_BYTES]
    assert plaintext.startswith(SETUP_TOKEN_PREFIX)
    assert len(plaintext.removeprefix(SETUP_TOKEN_PREFIX)) == 43
    assert (
        digest_setup_token(token) == hashlib.sha256(plaintext.encode("ascii")).digest()
    )


def test_token_shape_rejection_and_constant_time_comparison() -> None:
    token = _token()
    digest = digest_setup_token(token)
    with patch(
        "slaif_agent_site.bootstrap.setup_token.secrets.compare_digest",
        wraps=__import__("secrets").compare_digest,
    ) as compare:
        assert setup_token_matches(token, digest)
        compare.assert_called_once()
    assert not setup_token_matches(_token(8), digest)
    assert not setup_token_matches("malformed", digest)
    assert not setup_token_matches(token, b"short")
    for malformed in ("", SETUP_TOKEN_PREFIX, "wrong_v1_" + "a" * 43, "é" * 58):
        with pytest.raises(InvalidSetupToken) as context:
            digest_setup_token(malformed)
        assert str(context.value) == "Invalid setup token."
        if malformed:
            assert malformed not in str(context.value)


def test_invalid_randomness_boundary_fails_without_exposing_material() -> None:
    with pytest.raises(InvalidSetupToken) as context:
        generate_setup_token(lambda _size: b"too-short")
    assert str(context.value) == "Invalid setup token."


def test_result_masks_and_excludes_plaintext_from_serialization() -> None:
    token = _token()
    plaintext = token.get_secret_value()
    result = SetupTokenResult(
        action=SetupTokenAction.ISSUED,
        status=_status(),
        setup_token=token,
    )
    assert plaintext not in repr(result)
    assert plaintext not in result.model_dump_json()
    assert "setup_token" not in result.model_dump()
    assert "setup_token_digest" not in result.model_dump_json()


@pytest.mark.parametrize("ttl", (4, 61))
def test_setup_token_ttl_is_bounded(ttl: int) -> None:
    with pytest.raises(ValidationError):
        _settings(setup_token_ttl_minutes=ttl)
    assert _settings().setup_token_ttl_minutes == 30


@pytest.mark.parametrize(
    "url",
    (
        "https://example.test/other",
        "https://example.test/setup?token=value",
        "https://example.test/setup#fragment",
        "https://operator:secret@example.test/setup",
        "ftp://example.test/setup",
    ),
)
def test_setup_url_is_absolute_bounded_and_never_a_token_carrier(url: str) -> None:
    with pytest.raises(ValidationError):
        _settings(setup_url=url)
    assert str(_settings(setup_url="https://example.test/setup").setup_url) == (
        "https://example.test/setup"
    )


async def test_cli_existing_status_and_revoke_outputs_are_bounded() -> None:
    settings = _settings()
    existing = SetupTokenResult(
        action=SetupTokenAction.EXISTING,
        status=_status(),
    )
    revoked = SetupTokenResult(
        action=SetupTokenAction.REVOKED,
        status=_status(token_present=False),
    )
    with patch.object(bootstrap_cli, "ensure_setup_token", return_value=existing):
        output = await bootstrap_cli._run(
            "setup-token",
            settings,
            argparse.Namespace(status=False, revoke=False, rotate=False),
        )
    joined = "\n".join(output)
    assert "setup-token-secret:" not in joined
    assert "digest" not in joined
    assert "--rotate" in joined

    with patch.object(bootstrap_cli, "setup_token_status", return_value=_status()):
        output = await bootstrap_cli._run(
            "setup-token",
            settings,
            argparse.Namespace(status=True, revoke=False, rotate=False),
        )
    assert "secret" not in "\n".join(output)
    assert "digest" not in "\n".join(output)

    with patch.object(bootstrap_cli, "revoke_setup_token", return_value=revoked):
        output = await bootstrap_cli._run(
            "setup-token",
            settings,
            argparse.Namespace(status=False, revoke=True, rotate=False),
        )
    assert output[0].startswith("setup-token: revoked ")
    assert "secret" not in output[0]


async def test_cli_unwraps_a_fresh_secret_once_on_its_own_line() -> None:
    token = _token()
    result = SetupTokenResult(
        action=SetupTokenAction.ISSUED,
        status=_status(),
        setup_token=token,
    )
    with patch.object(bootstrap_cli, "ensure_setup_token", return_value=result):
        output = await bootstrap_cli._run(
            "setup-token",
            _settings(),
            argparse.Namespace(status=False, revoke=False, rotate=False),
        )
    plaintext = token.get_secret_value()
    assert sum(plaintext in line for line in output) == 1
    assert output[-1] == f"setup-token-secret: {plaintext}"
    assert "token=" not in next(
        line for line in output if line.startswith("setup-url:")
    )


def test_cli_setup_actions_are_mutually_exclusive() -> None:
    with pytest.raises(SystemExit):
        bootstrap_cli._parser().parse_args(["setup-token", "--rotate", "--revoke"])


@pytest.mark.parametrize("initialized", (False, True))
async def test_compose_bootstrap_issues_once_or_closes(initialized: bool) -> None:
    token = _token()
    status = _status(token_present=False).model_copy(
        update={"initialized": initialized}
    )
    result = SetupTokenResult(
        action=SetupTokenAction.ISSUED, status=_status(), setup_token=token
    )
    compose = SimpleNamespace(revision="head", state=SimpleNamespace(value="HARDENED"))
    with (
        patch.object(bootstrap_cli, "compose_bootstrap", return_value=compose),
        patch.object(bootstrap_cli, "setup_token_status", return_value=status),
        patch.object(
            bootstrap_cli, "ensure_setup_token", return_value=result
        ) as ensure,
    ):
        output = await bootstrap_cli._run("compose", _settings(), argparse.Namespace())
    joined = "\n".join(output)
    if initialized:
        ensure.assert_not_called()
        assert "installation is initialized" in joined
        assert token.get_secret_value() not in joined
    else:
        ensure.assert_awaited_once()
        assert joined.count(token.get_secret_value()) == 1
        assert "setup-url:" in joined


async def test_compose_bootstrap_preserves_existing_token_without_plaintext() -> None:
    existing = SetupTokenResult(action=SetupTokenAction.EXISTING, status=_status())
    compose = SimpleNamespace(revision="head", state=SimpleNamespace(value="HARDENED"))
    with (
        patch.object(bootstrap_cli, "compose_bootstrap", return_value=compose),
        patch.object(bootstrap_cli, "setup_token_status", return_value=_status()),
        patch.object(bootstrap_cli, "ensure_setup_token", return_value=existing),
    ):
        output = await bootstrap_cli._run("compose", _settings(), argparse.Namespace())
    joined = "\n".join(output)
    assert "token already available" in joined
    assert "--rotate" in joined
    assert "setup-token-secret" not in joined

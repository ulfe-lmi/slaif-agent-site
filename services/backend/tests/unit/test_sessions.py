"""Secret-safe session, CSRF, timeout, and cookie-policy contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr, ValidationError
from slaif_agent_site.identity.sessions import (
    HumanSessionContext,
    HumanSessionError,
    HumanSessionPolicy,
    HumanSessionService,
    SessionCookiePolicy,
    SessionCredentialError,
    constant_time_digest_equal,
    digest_secret,
    format_csrf_token,
    format_session_token,
    parse_csrf_token,
    parse_session_token,
    session_cookie_policy,
)


class _Transaction:
    async def __aenter__(self) -> _Transaction:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


class _Connection:
    def __init__(self, rows: list[tuple[object, ...]]) -> None:
        self.rows = iter(rows)

    def transaction(self) -> _Transaction:
        return _Transaction()

    async def fetchrow(self, *_args: object) -> tuple[object, ...]:
        return next(self.rows)


class _Acquire:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection

    async def __aenter__(self) -> _Connection:
        return self.connection

    async def __aexit__(self, *_args: object) -> None:
        return None


class _Pool:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection

    def acquire(self) -> _Acquire:
        return _Acquire(self.connection)


def test_versioned_credentials_round_trip_and_masked_repr() -> None:
    public_id = "sas2_" + ("a" * 32)
    secret = bytes(range(32))
    csrf = bytes(reversed(range(32)))
    session_token = format_session_token(public_id, secret)
    csrf_token = format_csrf_token(csrf)
    assert parse_session_token(session_token) == (public_id, secret)
    assert parse_csrf_token(csrf_token) == csrf
    assert secret.hex() not in repr(session_token)
    assert csrf.hex() not in repr(csrf_token)
    assert session_token.get_secret_value().startswith("sas2_session_")
    assert csrf_token.get_secret_value().startswith("sas2_csrf_")


@pytest.mark.parametrize(
    "value",
    (
        "",
        "sas1_session_" + "a" * 32 + "_" + "A" * 43,
        "sas2_session_bad_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "sas2_csrf_" + "A" * 42,
    ),
)
def test_malformed_credentials_are_constant(value: str) -> None:
    with pytest.raises(SessionCredentialError) as context:
        parse_session_token(value)
    assert str(context.value) == "Invalid session credential."
    if value:
        assert value not in str(context.value)


def test_digest_is_fixed_and_constant_time_helper_is_explicit() -> None:
    secret = b"x" * 32
    digest = digest_secret(secret)
    assert len(digest) == 32
    assert constant_time_digest_equal(digest, digest)
    assert not constant_time_digest_equal(digest, b"y" * 32)
    with pytest.raises(SessionCredentialError):
        digest_secret(b"short")


def test_session_policy_ordering_and_cookie_variants() -> None:
    policy = HumanSessionPolicy()
    assert policy.validate_ordering() is policy
    local = session_cookie_policy(production=False, policy=policy)
    production = session_cookie_policy(production=True, policy=policy)
    assert local == SessionCookiePolicy(
        name="slaif_session",
        http_only=True,
        secure=False,
        same_site="lax",
        path="/",
        domain=None,
        max_age_seconds=policy.absolute_lifetime_seconds,
    )
    assert production.name == "__Host-slaif_session"
    assert production.secure is True
    with pytest.raises((ValidationError, ValueError)):
        HumanSessionPolicy(
            touch_interval_seconds=1800,
            idle_timeout_seconds=1800,
        ).validate_ordering()


def test_cookie_policy_rejects_domain_and_non_host_secure_name() -> None:
    with pytest.raises(ValueError):
        SessionCookiePolicy(
            name="session",
            http_only=True,
            secure=True,
            same_site="lax",
            path="/",
            domain=None,
            max_age_seconds=1,
        )
    with pytest.raises(ValueError):
        SessionCookiePolicy(
            name="session",
            http_only=True,
            secure=False,
            same_site="lax",
            path="/",
            domain="example.test",
            max_age_seconds=1,
        )


def test_context_shape_has_no_credential_fields() -> None:
    from slaif_agent_site.identity.sessions import HumanSessionContext

    context = HumanSessionContext(
        session_id=uuid4(),
        user_account_id=uuid4(),
        public_id="sas2_" + ("b" * 32),
        recent_auth=True,
        last_seen_at=datetime.now(UTC),
        absolute_expires_at=datetime.now(UTC),
    )
    assert "token" not in repr(context)
    assert "csrf" not in repr(context)
    assert isinstance(context.session_id, UUID)
    assert isinstance(SecretStr("fake").get_secret_value(), str)
    assert HumanSessionError.__name__ == "HumanSessionError"


@pytest.mark.asyncio
async def test_real_service_paths_call_constant_time_digest_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime.now(UTC)
    user_id = uuid4()
    session_id = uuid4()
    secret = b"s" * 32
    csrf = b"c" * 32
    calls: list[tuple[bytes, bytes]] = []

    def spy(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return left == right

    monkeypatch.setattr(
        "slaif_agent_site.identity.sessions.constant_time_digest_equal", spy
    )
    service = HumanSessionService(
        _Pool(
            _Connection(
                [
                    (
                        session_id,
                        user_id,
                        "sas2_" + "a" * 32,
                        True,
                        now,
                        now,
                        digest_secret(secret),
                    ),
                    (
                        session_id,
                        user_id,
                        "sas2_" + "a" * 32,
                        True,
                        now,
                        now,
                        digest_secret(secret),
                        digest_secret(csrf),
                    ),
                    (True, digest_secret(secret), digest_secret(csrf)),
                ]
            )
        ),
        random_bytes=lambda size: b"x" * size,
    )
    token = format_session_token("sas2_" + "a" * 32, secret)
    csrf_token = format_csrf_token(csrf)
    assert isinstance(await service.authenticate(token), HumanSessionContext)
    assert isinstance(
        await service.authenticate_state_changing(token, csrf_token),
        HumanSessionContext,
    )
    await service.revoke(token, csrf_token)
    expected = [
        (digest_secret(secret), digest_secret(secret)),
        (digest_secret(secret), digest_secret(secret)),
        (digest_secret(csrf), digest_secret(csrf)),
        (digest_secret(secret), digest_secret(secret)),
        (digest_secret(csrf), digest_secret(csrf)),
    ]
    assert calls == expected

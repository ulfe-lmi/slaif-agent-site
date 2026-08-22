"""Tests for capability token generation and validation."""

from __future__ import annotations

from slaif_agent_site.agent_state.capability import (
    compute_digest,
    constant_time_digest_compare,
    generate_capability_token,
    validate_token_format,
)


class TestCapabilityToken:
    def test_generates_valid_format(self) -> None:
        token, pub, digest = generate_capability_token()
        assert token.startswith("sas2_")
        assert len(digest) == 64  # SHA-256 hex
        assert pub in token

    def test_unique_tokens(self) -> None:
        t1, _, _ = generate_capability_token()
        t2, _, _ = generate_capability_token()
        assert t1 != t2

    def test_secret_is_256_bit(self) -> None:
        token, _, _ = generate_capability_token()
        parts = token.split("_")
        assert len(parts[2]) == 64

    def test_validate_rejects_bad_formats(self) -> None:
        assert not validate_token_format("")
        assert not validate_token_format("not_a_token")
        assert not validate_token_format("sas2_ab_short")

    def test_digest_is_deterministic(self) -> None:
        d1 = compute_digest("test-token")
        d2 = compute_digest("test-token")
        assert d1 == d2

    def test_constant_time_compare(self) -> None:
        assert constant_time_digest_compare("abc", "abc")
        assert not constant_time_digest_compare("abc", "abd")

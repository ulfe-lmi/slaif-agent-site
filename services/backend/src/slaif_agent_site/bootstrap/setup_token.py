"""Setup-token generation and comparison without plaintext persistence."""

from __future__ import annotations

import base64
import hashlib
import re
import secrets
from collections.abc import Callable

from pydantic import SecretStr

SETUP_TOKEN_PREFIX = "slaif_setup_v1_"
SETUP_TOKEN_RANDOM_BYTES = 32
_TOKEN_PATTERN = re.compile(rf"{re.escape(SETUP_TOKEN_PREFIX)}[A-Za-z0-9_-]{{43}}")


class InvalidSetupToken(ValueError):
    """A constant, public-safe setup-token validation failure."""


def generate_setup_token(
    random_bytes: Callable[[int], bytes] = secrets.token_bytes,
) -> SecretStr:
    """Create a versioned token containing 256 bits of cryptographic randomness."""

    entropy = random_bytes(SETUP_TOKEN_RANDOM_BYTES)
    if len(entropy) != SETUP_TOKEN_RANDOM_BYTES:
        raise InvalidSetupToken("Invalid setup token.")
    encoded = base64.urlsafe_b64encode(entropy).rstrip(b"=").decode("ascii")
    return SecretStr(f"{SETUP_TOKEN_PREFIX}{encoded}")


def digest_setup_token(token: SecretStr | str) -> bytes:
    """Validate and digest a token for database storage."""

    plaintext = token.get_secret_value() if isinstance(token, SecretStr) else token
    try:
        encoded = plaintext.encode("ascii")
    except UnicodeEncodeError:
        raise InvalidSetupToken("Invalid setup token.") from None
    if _TOKEN_PATTERN.fullmatch(plaintext) is None:
        raise InvalidSetupToken("Invalid setup token.")
    return hashlib.sha256(encoded).digest()


def setup_token_matches(token: SecretStr | str, expected_digest: bytes) -> bool:
    """Compare a presented token to a stored digest in constant time."""

    if len(expected_digest) != hashlib.sha256().digest_size:
        return False
    try:
        presented_digest = digest_setup_token(token)
    except InvalidSetupToken:
        return False
    return secrets.compare_digest(presented_digest, expected_digest)


__all__ = [
    "InvalidSetupToken",
    "SETUP_TOKEN_PREFIX",
    "SETUP_TOKEN_RANDOM_BYTES",
    "digest_setup_token",
    "generate_setup_token",
    "setup_token_matches",
]

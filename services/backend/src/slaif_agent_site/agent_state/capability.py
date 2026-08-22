"""Agent capability token generation and validation.

Architecture reference: ARCHITECTURE-for-agents.md §6 (capability,
authorization, idempotency). Token format: ``sas2_<public-id>_<secret>``
with at least 256-bit random secret. Only the HMAC-SHA256 digest is stored;
the plaintext is shown exactly once and never persisted or logged.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_capability_token() -> tuple[str, str, str]:
    """Generate a new capability token.

    Returns:
        A tuple of (plaintext_token, public_id, secret_digest).
        The plaintext token is shown once; only the digest is stored.
    """
    public_id = secrets.token_hex(8)
    secret = secrets.token_hex(32)  # 256-bit
    plaintext = f"sas2_{public_id}_{secret}"
    digest = compute_digest(plaintext)
    return plaintext, public_id, digest


def compute_digest(token: str) -> str:
    """Compute the SHA-256 digest of a capability token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def validate_token_format(token: str) -> bool:
    """Check that a token has the expected sas2_ prefix and structure."""
    if not token.startswith("sas2_"):
        return False
    parts = token.split("_")
    if len(parts) != 3:
        return False
    _prefix, public_id, secret = parts
    return len(public_id) >= 8 and len(secret) >= 64


def constant_time_digest_compare(presented_digest: str, stored_digest: str) -> bool:
    """Compare two digests in constant time to prevent timing attacks."""
    return hmac.compare_digest(
        presented_digest.encode("utf-8"), stored_digest.encode("utf-8")
    )

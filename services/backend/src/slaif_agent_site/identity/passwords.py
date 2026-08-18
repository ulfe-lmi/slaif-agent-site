"""Bounded Argon2id password hashing for local human identities."""

from __future__ import annotations

from typing import Protocol

from argon2 import PasswordHasher
from argon2.profiles import RFC_9106_LOW_MEMORY
from pydantic import SecretStr

PASSWORD_MIN_CHARACTERS = 12
PASSWORD_MAX_CHARACTERS = 1024
PASSWORD_MAX_UTF8_BYTES = 4096


class PasswordPolicyError(ValueError):
    """A constant password-policy failure without rejected input."""


class PasswordServiceError(RuntimeError):
    """A constant hashing failure without library detail."""


class PasswordHasherProtocol(Protocol):
    def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str: ...

    def verify(self, hash: str | bytes, password: str | bytes) -> bool: ...

    def check_needs_rehash(self, hash: str | bytes) -> bool: ...


class PasswordService:
    """Apply the fixed production profile or an explicit test-owned hasher."""

    def __init__(self, hasher: PasswordHasherProtocol | None = None) -> None:
        self._hasher = hasher or PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)

    @staticmethod
    def validate_password(password: SecretStr, *, normalized_username: str) -> str:
        plaintext = password.get_secret_value()
        try:
            byte_length = len(plaintext.encode("utf-8"))
        except UnicodeEncodeError:
            raise PasswordPolicyError("Invalid local password.") from None
        if (
            len(plaintext) < PASSWORD_MIN_CHARACTERS
            or len(plaintext) > PASSWORD_MAX_CHARACTERS
            or byte_length > PASSWORD_MAX_UTF8_BYTES
            or "\x00" in plaintext
            or plaintext.casefold() == normalized_username
        ):
            raise PasswordPolicyError("Invalid local password.")
        return plaintext

    def hash_password(
        self, password: SecretStr, *, normalized_username: str
    ) -> SecretStr:
        plaintext = self.validate_password(
            password, normalized_username=normalized_username
        )
        try:
            return SecretStr(self._hasher.hash(plaintext))
        except Exception:
            raise PasswordServiceError("Local password operation failed.") from None

    def verify_password(self, encoded_hash: SecretStr, password: SecretStr) -> bool:
        try:
            return bool(
                self._hasher.verify(
                    encoded_hash.get_secret_value(), password.get_secret_value()
                )
            )
        except Exception:
            return False

    def check_needs_rehash(self, encoded_hash: SecretStr) -> bool:
        try:
            return bool(
                self._hasher.check_needs_rehash(encoded_hash.get_secret_value())
            )
        except Exception:
            return True


__all__ = [
    "PASSWORD_MAX_CHARACTERS",
    "PASSWORD_MAX_UTF8_BYTES",
    "PASSWORD_MIN_CHARACTERS",
    "PasswordPolicyError",
    "PasswordService",
    "PasswordServiceError",
]

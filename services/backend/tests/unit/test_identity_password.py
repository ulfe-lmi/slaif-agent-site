"""Local identity input and Argon2id password service contracts."""

from __future__ import annotations

import re

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type
from argon2.profiles import RFC_9106_LOW_MEMORY
from pydantic import SecretStr, ValidationError
from slaif_agent_site.identity.models import (
    IdentityInputError,
    InitialLocalAdministratorRequest,
    normalize_local_username,
)
from slaif_agent_site.identity.passwords import (
    PASSWORD_MAX_CHARACTERS,
    PASSWORD_MAX_UTF8_BYTES,
    PASSWORD_MIN_CHARACTERS,
    PasswordPolicyError,
    PasswordService,
    PasswordServiceError,
)


def _password(seed: str = "a") -> SecretStr:
    return SecretStr("fixture-" + seed + "-" + "x" * 20)


def _test_hasher() -> PasswordHasher:
    return PasswordHasher(
        time_cost=1,
        memory_cost=8,
        parallelism=1,
        hash_len=16,
        salt_len=8,
        type=Type.ID,
    )


def test_production_profile_is_explicit_rfc_9106_low_memory() -> None:
    service = PasswordService()
    assert isinstance(service._hasher, PasswordHasher)
    assert service._hasher.time_cost == RFC_9106_LOW_MEMORY.time_cost
    assert service._hasher.memory_cost == RFC_9106_LOW_MEMORY.memory_cost == 65536
    assert service._hasher.parallelism == RFC_9106_LOW_MEMORY.parallelism == 4
    assert service._hasher.hash_len == 32
    assert service._hasher.salt_len == 16
    assert service._hasher.type is Type.ID


def test_production_hash_shape_verify_random_salt_and_rehash_contract() -> None:
    service = PasswordService()
    password = _password()
    first = service.hash_password(password, normalized_username="operator")
    second = service.hash_password(password, normalized_username="operator")
    assert first.get_secret_value() != second.get_secret_value()
    pattern = (
        r"\$argon2id\$v=19\$m=65536,t=3,p=4\$"
        r"[A-Za-z0-9+/]{22}\$[A-Za-z0-9+/]{43}"
    )
    assert re.fullmatch(pattern, first.get_secret_value())
    assert service.verify_password(first, password)
    assert not service.verify_password(first, _password("wrong"))
    assert not service.check_needs_rehash(first)


def test_test_owned_cheaper_hasher_is_injected_without_global_override() -> None:
    service = PasswordService(_test_hasher())
    encoded = service.hash_password(_password(), normalized_username="operator")
    assert "$m=8,t=1,p=1$" in encoded.get_secret_value()
    assert service.verify_password(encoded, _password())
    assert not service.check_needs_rehash(encoded)
    assert RFC_9106_LOW_MEMORY.memory_cost == 65536


@pytest.mark.parametrize(
    "value",
    (
        "x" * (PASSWORD_MIN_CHARACTERS - 1),
        "x" * (PASSWORD_MAX_CHARACTERS + 1),
        "operator",
        "safe-prefix-" + "\x00" + "suffix",
        "🙂" * ((PASSWORD_MAX_UTF8_BYTES // 4) + 1),
    ),
)
def test_password_policy_is_bounded_without_character_class_rules(value: str) -> None:
    with pytest.raises(PasswordPolicyError) as context:
        PasswordService.validate_password(
            SecretStr(value), normalized_username="operator"
        )
    assert str(context.value) == "Invalid local password."
    assert value not in str(context.value)


def test_valid_unicode_password_with_no_mandatory_classes_is_accepted() -> None:
    plaintext = "enotna-dolga-gesla-🙂"
    assert (
        PasswordService.validate_password(
            SecretStr(plaintext), normalized_username="operator"
        )
        == plaintext
    )


class FailingHasher:
    def hash(self, password: str | bytes, *, salt: bytes | None = None) -> str:
        raise RuntimeError("must-not-leak-" + str(password))

    def verify(self, hash: str | bytes, password: str | bytes) -> bool:
        raise RuntimeError("must-not-leak-" + str(password) + str(hash))

    def check_needs_rehash(self, hash: str | bytes) -> bool:
        raise RuntimeError("must-not-leak-" + str(hash))


def test_library_failures_are_stable_and_secret_safe() -> None:
    service = PasswordService(FailingHasher())
    password = _password()
    with pytest.raises(PasswordServiceError) as context:
        service.hash_password(password, normalized_username="operator")
    assert str(context.value) == "Local password operation failed."
    assert password.get_secret_value() not in str(context.value)
    encoded = SecretStr("not-an-encoded-hash")
    assert not service.verify_password(encoded, password)
    assert service.check_needs_rehash(encoded)


def test_username_normalization_and_secret_safe_request_serialization() -> None:
    assert normalize_local_username("Local.Admin-1") == "local.admin-1"
    with pytest.raises(IdentityInputError):
        normalize_local_username("not unicode 🙂")
    password = _password()
    token = SecretStr("not-a-real-token")
    request = InitialLocalAdministratorRequest(
        username="Local.Admin-1",
        password=password,
        display_name="  Local Administrator  ",
        email=" Admin@Example.Test ",
        setup_token=token,
    )
    assert request.normalized_username == "local.admin-1"
    assert request.display_name == "Local Administrator"
    assert request.email == "admin@example.test"
    serialized = request.model_dump_json()
    assert "password" not in serialized and "setup_token" not in serialized
    assert password.get_secret_value() not in repr(request)
    assert token.get_secret_value() not in repr(request)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("username", "ab"),
        ("username", "bad space"),
        ("display_name", " "),
        ("email", "not-an-email"),
    ),
)
def test_identity_profile_fields_are_bounded(field: str, value: str) -> None:
    values: dict[str, object] = {
        "username": "operator",
        "password": _password(),
        "display_name": "Operator",
        "email": "operator@example.test",
        "setup_token": SecretStr("shape-validated-by-service"),
    }
    values[field] = value
    with pytest.raises(ValidationError):
        InitialLocalAdministratorRequest.model_validate(values)

"""Run-bound browser preview credential and key-file unit proof."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from uuid import UUID

import pytest
from slaif_agent_site.browser_contracts import BrowserEvidence, BrowserTarget
from slaif_agent_site.browser_preview_credentials import (
    BROWSER_PREVIEW_AUDIENCE,
    BROWSER_PREVIEW_DEPLOYMENT,
    BROWSER_PREVIEW_HEADER,
    BROWSER_PREVIEW_TOKEN_ALGORITHM,
    BROWSER_PREVIEW_TOKEN_PREFIX,
    BROWSER_RENDER_HEADER,
    BrowserPreviewCredentialError,
    BrowserPreviewCredentialSigner,
    BrowserPreviewExpectedBinding,
    BrowserSigningKey,
    generate_browser_signing_key,
    load_browser_signing_key,
)

KEY_ID = "0123456789abcdef"
KEY_BYTES = bytes(range(32))
CAPABILITY_ID = UUID("00000000-0000-4000-8000-000000000001")
SITE_ID = UUID("00000000-0000-4000-8000-000000000002")
WORKSPACE_ID = UUID("00000000-0000-4000-8000-000000000003")
RUN_ID = UUID("00000000-0000-4000-8000-000000000004")
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _signer() -> BrowserPreviewCredentialSigner:
    return BrowserPreviewCredentialSigner(BrowserSigningKey(KEY_ID, KEY_BYTES))


def _issue(
    *,
    now: int = 1_800_000_000,
    ttl: int = 30,
    nonce: str = "00112233445566778899aabbccddeeff",
) -> str:
    return _signer().issue(
        capability_id=CAPABILITY_ID,
        site_id=SITE_ID,
        workspace_id=WORKSPACE_ID,
        run_id=RUN_ID,
        route="/news?b=2&a=1",
        target=BrowserTarget.DESKTOP_CHROMIUM,
        evidence=(BrowserEvidence.SCREENSHOT, BrowserEvidence.HEADING_SUMMARY),
        artifact_bytes_limit=5_505_024,
        duration_seconds=120,
        now=now,
        ttl_seconds=ttl,
        nonce=nonce,
    )


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(
        value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
    )


def _resign_components(header_part: str, payload_part: str) -> str:
    signed = f"sbp1.{header_part}.{payload_part}"
    return f"{signed}.{_b64(hmac.digest(KEY_BYTES, signed.encode(), 'sha256'))}"


def _noncanonical_pad_alias(value: str) -> str:
    decoded = _b64decode(value)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    for character in alphabet:
        candidate = value[:-1] + character
        if candidate != value and _b64decode(candidate) == decoded:
            return candidate
    raise AssertionError("component has no discarded base64url pad bits")


def _signed_token(header: str, payload: str) -> str:
    return _resign_components(_b64(header.encode()), _b64(payload.encode()))


def _assert_invalid(token: str) -> None:
    with pytest.raises(BrowserPreviewCredentialError) as caught:
        _signer().verify(token, now=1_800_000_010)
    assert str(caught.value) == "browser credential is invalid"


def test_deterministic_vector_and_exact_binding() -> None:
    token = _issue()
    assert hashlib.sha256(token.encode()).hexdigest() == (
        "133725d1ed391c0c36dafee52c5cfa9b92ef0dbd731eccf8447eeb7da54593db"
    )
    claims = _signer().verify(
        token,
        now=1_800_000_010,
        expected=BrowserPreviewExpectedBinding(
            capability_id=CAPABILITY_ID,
            site_id=SITE_ID,
            workspace_id=WORKSPACE_ID,
            run_id=RUN_ID,
            route="/news?a=1&b=2",
            target=BrowserTarget.DESKTOP_CHROMIUM,
        ),
    )
    assert claims.route == "/news?a=1&b=2"
    assert claims.audience == BROWSER_PREVIEW_AUDIENCE
    assert claims.deployment == BROWSER_PREVIEW_DEPLOYMENT
    assert (
        claims.nonce_digest
        == hashlib.sha256(b"00112233445566778899aabbccddeeff").hexdigest()
    )
    assert token not in repr(claims)


def test_neutral_verifier_contract_matches_python_facts() -> None:
    facts = json.loads(
        (
            REPOSITORY_ROOT
            / "packages/browser-tool-contracts/src/browser-preview-credential-v1.json"
        ).read_text(encoding="utf-8")
    )
    assert facts == {
        "tokenVersion": BROWSER_PREVIEW_TOKEN_PREFIX,
        "algorithm": BROWSER_PREVIEW_TOKEN_ALGORITHM,
        "type": "SLAIF-BROWSER-PREVIEW",
        "audience": BROWSER_PREVIEW_AUDIENCE,
        "deployment": BROWSER_PREVIEW_DEPLOYMENT,
        "browserHeader": BROWSER_PREVIEW_HEADER,
        "renderHeader": BROWSER_RENDER_HEADER,
        "maxTokenBytes": 4096,
        "maxTtlSeconds": 60,
        "claims": [
            "deployment",
            "audience",
            "contract_version",
            "capability_id",
            "site_id",
            "workspace_id",
            "run_id",
            "route",
            "target",
            "evidence",
            "artifact_bytes_limit",
            "duration_seconds",
            "issued_at",
            "expires_at",
            "nonce",
            "key_id",
        ],
    }


@pytest.mark.parametrize(
    "expected",
    (
        BrowserPreviewExpectedBinding(capability_id=UUID(int=99)),
        BrowserPreviewExpectedBinding(site_id=UUID(int=99)),
        BrowserPreviewExpectedBinding(workspace_id=UUID(int=99)),
        BrowserPreviewExpectedBinding(run_id=UUID(int=99)),
        BrowserPreviewExpectedBinding(route="/other"),
        BrowserPreviewExpectedBinding(target=BrowserTarget.TABLET),
    ),
)
def test_changed_binding_is_rejected(expected: BrowserPreviewExpectedBinding) -> None:
    with pytest.raises(BrowserPreviewCredentialError):
        _signer().verify(_issue(), now=1_800_000_010, expected=expected)


def test_signature_lifetime_and_malformed_tokens_fail_closed() -> None:
    token = _issue()
    parts = token.split(".")
    tampered = ".".join([*parts[:2], parts[2][:-1] + "A", parts[3]])
    for candidate, now in (
        (tampered, 1_800_000_010),
        (_issue(), 1_800_000_030),
        (_issue(now=1_800_000_100), 1_800_000_000),
        ("", 1_800_000_000),
        ("sbp1.bad", 1_800_000_000),
        ("x" * 4097, 1_800_000_000),
        (token + "\n", 1_800_000_010),
    ):
        with pytest.raises(BrowserPreviewCredentialError):
            _signer().verify(candidate, now=now)
    other = BrowserPreviewCredentialSigner(
        BrowserSigningKey("fedcba9876543210", b"z" * 32)
    )
    with pytest.raises(BrowserPreviewCredentialError):
        other.verify(token, now=1_800_000_010)


def test_noncanonical_signature_pad_bits_are_rejected() -> None:
    token = _issue(nonce="00000000000000000000000000000005")
    parts = token.split(".")
    assert parts[3][-1] == "0"
    signature = _b64decode(parts[3])

    for final_character in "123":
        aliased_signature = parts[3][:-1] + final_character
        assert aliased_signature != parts[3]
        assert _b64decode(aliased_signature) == signature
        _assert_invalid(".".join([*parts[:3], aliased_signature]))

    significant_tamper = parts[3][:-2] + ("A" if parts[3][-2] != "A" else "B") + "0"
    assert _b64decode(significant_tamper) != signature
    _assert_invalid(".".join([*parts[:3], significant_tamper]))


def test_noncanonical_header_and_payload_components_are_rejected() -> None:
    parts = _issue().split(".")
    header_with_trailing_space = _b64(_b64decode(parts[1]) + b" ")
    aliased_header = _noncanonical_pad_alias(header_with_trailing_space)
    aliased_payload = _noncanonical_pad_alias(parts[2])

    assert _b64decode(aliased_header) == _b64decode(header_with_trailing_space)
    assert _b64decode(aliased_payload) == _b64decode(parts[2])
    _assert_invalid(_resign_components(aliased_header, parts[2]))
    _assert_invalid(_resign_components(parts[1], aliased_payload))


def test_signed_unknown_and_duplicate_facts_are_rejected() -> None:
    valid_header = {
        "alg": "HS256",
        "kid": KEY_ID,
        "typ": "SLAIF-BROWSER-PREVIEW",
        "version": "sbp1",
    }
    valid_payload = json.loads(
        base64.urlsafe_b64decode(_issue().split(".")[2] + "==").decode()
    )
    candidates = (
        ({**valid_header, "alg": "none"}, valid_payload),
        ({**valid_header, "version": "sbp2"}, valid_payload),
        ({**valid_header, "kid": "fedcba9876543210"}, valid_payload),
        (valid_header, {**valid_payload, "audience": "other"}),
        (valid_header, {**valid_payload, "contract_version": "browser-preview/v2"}),
    )
    for header, payload in candidates:
        with pytest.raises(BrowserPreviewCredentialError):
            _signer().verify(
                _signed_token(
                    json.dumps(header, separators=(",", ":"), sort_keys=True),
                    json.dumps(payload, separators=(",", ":"), sort_keys=True),
                ),
                now=1_800_000_010,
            )
    duplicate_payload = json.dumps(valid_payload, separators=(",", ":"))[:-1]
    duplicate_payload += ',"nonce":"00112233445566778899aabbccddeeff"}'
    with pytest.raises(BrowserPreviewCredentialError):
        _signer().verify(
            _signed_token(
                json.dumps(valid_header, separators=(",", ":"), sort_keys=True),
                duplicate_payload,
            ),
            now=1_800_000_010,
        )


def _write_key(directory: Path, value: str, *, mode: int = 0o400) -> Path:
    directory.mkdir(mode=0o700)
    path = directory / "signing-key"
    path.write_text(value, encoding="ascii")
    path.chmod(mode)
    return path


def test_descriptor_confined_key_file_and_generation(tmp_path: Path) -> None:
    value = f"sbk1:{KEY_ID}:{_b64(KEY_BYTES)}"
    path = _write_key(tmp_path / "valid", value)
    loaded = load_browser_signing_key(path)
    assert loaded.key_id == KEY_ID
    assert loaded.secret == KEY_BYTES
    generated = generate_browser_signing_key()
    assert generated.startswith("sbk1:")
    assert len(generated) == len(value)

    wrong_mode = _write_key(tmp_path / "wrong-mode", value, mode=0o600)
    symlink_dir = tmp_path / "symlink"
    symlink_dir.mkdir(mode=0o700)
    os.symlink(path, symlink_dir / "signing-key")
    wrong_name = tmp_path / "other-key"
    wrong_name.write_text(value, encoding="ascii")
    wrong_name.chmod(0o400)
    newline = _write_key(tmp_path / "newline", value + "\n")
    for candidate in (wrong_mode, symlink_dir / "signing-key", wrong_name, newline):
        with pytest.raises(BrowserPreviewCredentialError):
            load_browser_signing_key(candidate)

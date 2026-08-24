"""Cookie/CSRF parsing and Media-specific human authorization."""

from __future__ import annotations

import secrets
from re import compile as compile_pattern
from typing import Any
from uuid import UUID

from fastapi import Request

from slaif_agent_site.errors import (
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ServiceUnavailableError,
)
from slaif_agent_site.identity.sessions import (
    digest_secret,
    parse_csrf_token,
    parse_session_token,
)

from .database import MediaAuthContext, MediaDatabase

_COOKIE_NAME = compile_pattern(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_COOKIE_VALUE = compile_pattern(r"^[\x21\x23-\x2B\x2D-\x3A\x3C-\x5B\x5D-\x7E]*$")
_ZERO_DIGEST = b"\x00" * 32


def _cookies(request: Request) -> dict[str, str]:
    values: dict[str, str] = {}
    raw = [
        value
        for name, value in request.scope.get("headers", [])
        if name.lower() == b"cookie"
    ]
    if len(raw) != 1:
        raise AuthenticationError()
    try:
        text = raw[0].decode("ascii")
    except UnicodeDecodeError:
        raise AuthenticationError() from None
    for part in text.split(";"):
        pair = part.strip()
        if not pair or pair.count("=") != 1:
            raise AuthenticationError()
        name, value = pair.split("=", 1)
        if (
            not _COOKIE_NAME.fullmatch(name)
            or not _COOKIE_VALUE.fullmatch(value)
            or name in values
        ):
            raise AuthenticationError()
        values[name] = value
    return values


async def authorize_media_request(
    request: Request,
    database: MediaDatabase,
    settings: Any,
    site_id: UUID,
    permission: str,
    *,
    state_changing: bool,
) -> MediaAuthContext:
    names = _cookies(request)
    session_name = (
        "__Host-slaif_session" if settings.secure_cookies else "slaif_session"
    )
    csrf_name = "__Host-slaif_csrf" if settings.secure_cookies else "slaif_csrf"
    alternate = (
        {"slaif_session", "slaif_csrf"}
        if settings.secure_cookies
        else {"__Host-slaif_session", "__Host-slaif_csrf"}
    )
    if alternate & names.keys():
        raise AuthenticationError()
    token = names.get(session_name)
    if not token:
        raise AuthenticationError()
    try:
        public_id, secret = parse_session_token(token)
        csrf_value = names.get(csrf_name, "")
        header = request.headers.get("x-csrf-token", "")
        if state_changing:
            if (
                not csrf_value
                or not header
                or not secrets.compare_digest(csrf_value, header)
            ):
                raise AuthorizationError()
            csrf_digest = digest_secret(parse_csrf_token(csrf_value))
        else:
            csrf_digest = _ZERO_DIGEST
        context = await database.authorize(
            public_id=public_id,
            session_digest=digest_secret(secret),
            csrf_digest=csrf_digest,
            site_id=site_id,
            permission=permission,
            state_changing=state_changing,
        )
    except (AuthenticationError, AuthorizationError):
        raise
    except Exception:
        raise ServiceUnavailableError() from None
    if context is None:
        raise ResourceNotFoundError()
    return context


__all__ = ["authorize_media_request"]

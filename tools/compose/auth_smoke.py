"""Secret-safe disposable authentication journey through the public edge."""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://localhost:8080"
PASSWORD = "fixture-compose-auth-password-123"


def _request(
    opener: urllib.request.OpenerDirector,
    path: str,
    *,
    body: dict[str, object] | None = None,
    csrf: str | None = None,
) -> tuple[int, bytes, list[str]]:
    headers = {"Content-Type": "application/json"}
    if csrf is not None:
        headers["X-CSRF-Token"] = csrf
    request = urllib.request.Request(
        BASE + path,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers=headers,
        method="GET" if body is None else "POST",
    )
    try:
        response = opener.open(request, timeout=10)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), error.headers.get_all("Set-Cookie") or []
    with response:
        return (
            response.status,
            response.read(),
            response.headers.get_all("Set-Cookie") or [],
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token-file", type=Path, required=True)
    arguments = parser.parse_args()
    token = arguments.token_file.read_text(encoding="utf-8").strip()
    if not token:
        parser.error("token file is empty")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    status, page, _ = _request(opener, "/setup")
    assert status == 200 and b"Create the first administrator" in page
    status, body, _ = _request(opener, "/api/control/v1/setup/status")
    assert status == 200 and json.loads(body) == {
        "initialized": False,
        "setup_available": True,
    }
    status, body, cookies = _request(
        opener,
        "/api/control/v1/setup",
        body={
            "setup_token": token,
            "username": "Compose.Admin",
            "password": PASSWORD,
            "display_name": "Compose Administrator",
            "email": "compose@example.test",
        },
    )
    assert status == 200 and token.encode() not in body and len(cookies) == 2
    status, body, _ = _request(opener, "/api/control/v1/session")
    assert status == 200 and b"csrf" not in body.lower()
    csrf = next(cookie.value for cookie in jar if cookie.name == "slaif_csrf")
    status, body, cookies = _request(
        opener, "/api/control/v1/logout", body={}, csrf=csrf
    )
    assert status == 204 and body == b"" and len(cookies) == 2

    status, body, cookies = _request(
        opener,
        "/api/control/v1/login",
        body={"username": "compose.admin", "password": PASSWORD},
    )
    assert status == 200 and PASSWORD.encode() not in body and len(cookies) == 2
    status, body, cookies = _request(
        opener,
        "/api/control/v1/login",
        body={"username": "compose.admin", "password": "wrong-password"},
    )
    assert status == 401 and PASSWORD.encode() not in body and not cookies
    status, body, cookies = _request(
        opener, "/api/control/v1/logout", body={}, csrf="wrong-csrf"
    )
    assert status == 403 and token.encode() not in body and not cookies
    print("compose-auth-smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

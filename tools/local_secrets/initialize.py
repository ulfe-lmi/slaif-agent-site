#!/usr/bin/env python3
"""Create or validate the private, file-backed local database credentials."""

from __future__ import annotations

import argparse
import os
import secrets
import stat
from pathlib import Path
from urllib.parse import quote

DATABASE = "slaif"
DATABASE_HOST = "postgres"
POSTGRES_UID = 999
APPLICATION_UID = 10001
CONTROL_DIRECTORY_UID = APPLICATION_UID
CONTROL_DIRECTORY_GID = APPLICATION_UID
MARKER_UID = 0
DIRECTORY_UID = 0
SECRET_DIRECTORY_GID = 10002
SECRET_MODE = 0o400
DIRECTORY_MODE = 0o710
CONTROL_DIRECTORY_MODE = 0o700
CONTROL_DSN_FILE = "control-dsn"
MARKER = ".initialized-v1"
LOGINS = (
    ("bootstrap", "slaif_bootstrap_login"),
    ("control", "slaif_control_login"),
    ("editor", "slaif_editor_login"),
    ("agent", "slaif_agent_login"),
    ("public", "slaif_public_login"),
    ("preview", "slaif_preview_login"),
    ("reviewer", "slaif_reviewer_login"),
    ("scheduler", "slaif_scheduler_login"),
    ("media", "slaif_media_login"),
    ("gc", "slaif_gc_login"),
)


class SecretInitializationError(RuntimeError):
    """A stable, secret-free local initialization failure."""


def _validate_directory(directory: Path, *, mode: int, uid: int, gid: int) -> None:
    info = directory.stat(follow_symlinks=False)
    if (
        not stat.S_ISDIR(info.st_mode)
        or stat.S_IMODE(info.st_mode) != mode
        or info.st_uid != uid
        or info.st_gid != gid
    ):
        raise SecretInitializationError("private secret directory policy mismatch")


def _prepare_directory(directory: Path, *, mode: int, uid: int, gid: int) -> None:
    if not directory.exists():
        directory.mkdir(mode=mode, parents=True)
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(directory_fd)
        if stat.S_IMODE(info.st_mode) != mode:
            os.fchmod(directory_fd, mode)
        if info.st_uid != uid or info.st_gid != gid:
            os.fchown(directory_fd, uid, gid)
    finally:
        os.close(directory_fd)
    _validate_directory(directory, mode=mode, uid=uid, gid=gid)


def _read_secret(path: Path, *, uid: int) -> str:
    try:
        info = path.stat(follow_symlinks=False)
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != SECRET_MODE
            or info.st_uid != uid
        ):
            raise SecretInitializationError("secret file policy mismatch")
        value = path.read_text(encoding="ascii")
    except (OSError, UnicodeError):
        raise SecretInitializationError("secret file is unavailable") from None
    if len(value) < 43 or "\n" in value or "\r" in value:
        raise SecretInitializationError("secret file content is invalid")
    return value


def _write_once(path: Path, value: str, *, uid: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, SECRET_MODE)
    except FileExistsError:
        _read_secret(path, uid=uid)
        return
    try:
        os.fchmod(descriptor, SECRET_MODE)
        os.fchown(descriptor, uid, uid)
        with os.fdopen(descriptor, "w", encoding="ascii", closefd=False) as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _dsn(user: str, password: str) -> str:
    encoded_user = quote(user, safe="")
    encoded_password = quote(password, safe="")
    return (
        f"postgresql://{encoded_user}:{encoded_password}@{DATABASE_HOST}:5432/"
        f"{DATABASE}"
    )


def initialize(
    directory: Path,
    *,
    control_directory: Path | None = None,
    validate_only: bool = False,
) -> int:
    if not directory.is_absolute():
        raise SecretInitializationError("secret directory must be absolute")
    if control_directory is not None and not control_directory.is_absolute():
        raise SecretInitializationError("Control secret directory must be absolute")
    if not directory.exists():
        if validate_only:
            raise SecretInitializationError("secret directory is unavailable")
    _prepare_directory(
        directory,
        mode=DIRECTORY_MODE,
        uid=DIRECTORY_UID,
        gid=SECRET_DIRECTORY_GID,
    )

    password_files = {
        "postgres": (directory / "postgres-password", POSTGRES_UID),
        **{
            stem: (directory / f"login-{stem}-password", APPLICATION_UID)
            for stem, _login in LOGINS
        },
    }
    if not validate_only:
        for path, uid in password_files.values():
            if not path.exists():
                _write_once(path, secrets.token_urlsafe(48), uid=uid)
    passwords = {
        name: _read_secret(path, uid=uid)
        for name, (path, uid) in password_files.items()
    }

    dsn_files = {
        "provisioner-dsn": _dsn("postgres", passwords["postgres"]),
        "owner-dsn": _dsn("slaif_bootstrap_login", passwords["bootstrap"]),
        **{
            f"service-{stem}-dsn": _dsn(login, passwords[stem])
            for stem, login in LOGINS
            if stem != "bootstrap"
        },
    }
    if not validate_only:
        for filename, value in dsn_files.items():
            path = directory / filename
            if not path.exists():
                _write_once(path, value, uid=APPLICATION_UID)
    for filename in dsn_files:
        _read_secret(directory / filename, uid=APPLICATION_UID)

    isolated_files = 0
    if control_directory is not None:
        if not control_directory.exists() and validate_only:
            raise SecretInitializationError("Control secret directory is unavailable")
        _prepare_directory(
            control_directory,
            mode=CONTROL_DIRECTORY_MODE,
            uid=CONTROL_DIRECTORY_UID,
            gid=CONTROL_DIRECTORY_GID,
        )
        control_file = control_directory / CONTROL_DSN_FILE
        expected_control_dsn = dsn_files["service-control-dsn"]
        if not validate_only and not control_file.exists():
            _write_once(control_file, expected_control_dsn, uid=APPLICATION_UID)
        actual_control_dsn = _read_secret(control_file, uid=APPLICATION_UID)
        if not secrets.compare_digest(actual_control_dsn, expected_control_dsn):
            raise SecretInitializationError("isolated Control locator mismatch")
        control_fd = os.open(
            control_directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            os.fsync(control_fd)
        finally:
            os.close(control_fd)
        isolated_files = 1

    marker = directory / MARKER
    if not validate_only and not marker.exists():
        _write_once(marker, "initialized-v1:" + ("0" * 48), uid=MARKER_UID)
    _read_secret(marker, uid=MARKER_UID)
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return len(password_files) + len(dsn_files) + 1 + isolated_files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path("/run/slaif-secrets"))
    parser.add_argument(
        "--control-directory",
        type=Path,
        default=Path("/run/slaif-control"),
    )
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    try:
        count = initialize(
            arguments.directory,
            control_directory=arguments.control_directory,
            validate_only=arguments.validate_only,
        )
    except (OSError, SecretInitializationError):
        print("local-secrets: FAILED", flush=True)
        return 1
    print(f"local-secrets: READY files={count}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

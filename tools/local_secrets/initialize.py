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
AGENT_DSN_FILE = "agent-dsn"
RENDER_DSN_FILE = "render-dsn"
EDITOR_DSN_FILE = "editor-dsn"
MEDIA_DSN_FILE = "media-dsn"
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
    agent_directory: Path | None = None,
    render_directory: Path | None = None,
    editor_directory: Path | None = None,
    media_directory: Path | None = None,
    validate_only: bool = False,
) -> int:
    if not directory.is_absolute():
        raise SecretInitializationError("secret directory must be absolute")
    if control_directory is not None and not control_directory.is_absolute():
        raise SecretInitializationError("Control secret directory must be absolute")
    if agent_directory is not None and not agent_directory.is_absolute():
        raise SecretInitializationError("Agent secret directory must be absolute")
    if render_directory is not None and not render_directory.is_absolute():
        raise SecretInitializationError("Render secret directory must be absolute")
    if editor_directory is not None and not editor_directory.is_absolute():
        raise SecretInitializationError("Editor secret directory must be absolute")
    if media_directory is not None and not media_directory.is_absolute():
        raise SecretInitializationError("Media secret directory must be absolute")
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
        control_file = control_directory / CONTROL_DSN_FILE
        expected_control_dsn = dsn_files["service-control-dsn"]
        initialize_control_file = not control_file.exists()
        if initialize_control_file:
            if validate_only:
                raise SecretInitializationError(
                    "Control secret directory is unavailable"
                )
            if control_directory.exists() and any(control_directory.iterdir()):
                raise SecretInitializationError(
                    "Control secret directory policy mismatch"
                )
            # A new named volume is an existing root-owned mount. Keep it owned by
            # the initializer until the only file has been created, then transfer
            # the final directory; no broad DAC_OVERRIDE capability is required.
            _prepare_directory(
                control_directory,
                mode=CONTROL_DIRECTORY_MODE,
                uid=DIRECTORY_UID,
                gid=DIRECTORY_UID,
            )
            _write_once(control_file, expected_control_dsn, uid=APPLICATION_UID)
        _prepare_directory(
            control_directory,
            mode=CONTROL_DIRECTORY_MODE,
            uid=CONTROL_DIRECTORY_UID,
            gid=CONTROL_DIRECTORY_GID,
        )
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

    if agent_directory is not None:
        agent_file = agent_directory / AGENT_DSN_FILE
        expected_agent_dsn = dsn_files["service-agent-dsn"]
        initialize_agent_file = not agent_file.exists()
        if initialize_agent_file:
            if validate_only:
                raise SecretInitializationError("Agent secret directory is unavailable")
            if agent_directory.exists() and any(agent_directory.iterdir()):
                raise SecretInitializationError(
                    "Agent secret directory policy mismatch"
                )
            _prepare_directory(
                agent_directory,
                mode=CONTROL_DIRECTORY_MODE,
                uid=DIRECTORY_UID,
                gid=DIRECTORY_UID,
            )
            _write_once(agent_file, expected_agent_dsn, uid=APPLICATION_UID)
        _prepare_directory(
            agent_directory,
            mode=CONTROL_DIRECTORY_MODE,
            uid=CONTROL_DIRECTORY_UID,
            gid=CONTROL_DIRECTORY_GID,
        )
        if {path.name for path in agent_directory.iterdir()} != {AGENT_DSN_FILE}:
            raise SecretInitializationError("Agent secret directory policy mismatch")
        actual_agent_dsn = _read_secret(agent_file, uid=APPLICATION_UID)
        if not secrets.compare_digest(actual_agent_dsn, expected_agent_dsn):
            raise SecretInitializationError("isolated Agent locator mismatch")
        agent_fd = os.open(
            agent_directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            os.fsync(agent_fd)
        finally:
            os.close(agent_fd)
        isolated_files += 1

    if editor_directory is not None:
        editor_file = editor_directory / EDITOR_DSN_FILE
        expected_editor_dsn = dsn_files["service-editor-dsn"]
        initialize_editor_file = not editor_file.exists()
        if initialize_editor_file:
            if validate_only:
                raise SecretInitializationError(
                    "Editor secret directory is unavailable"
                )
            if editor_directory.exists() and any(editor_directory.iterdir()):
                raise SecretInitializationError(
                    "Editor secret directory policy mismatch"
                )
            _prepare_directory(
                editor_directory,
                mode=CONTROL_DIRECTORY_MODE,
                uid=DIRECTORY_UID,
                gid=DIRECTORY_UID,
            )
            _write_once(editor_file, expected_editor_dsn, uid=APPLICATION_UID)
        _prepare_directory(
            editor_directory,
            mode=CONTROL_DIRECTORY_MODE,
            uid=CONTROL_DIRECTORY_UID,
            gid=CONTROL_DIRECTORY_GID,
        )
        if {path.name for path in editor_directory.iterdir()} != {EDITOR_DSN_FILE}:
            raise SecretInitializationError("Editor secret directory policy mismatch")
        actual_editor_dsn = _read_secret(editor_file, uid=APPLICATION_UID)
        if not secrets.compare_digest(actual_editor_dsn, expected_editor_dsn):
            raise SecretInitializationError("isolated Editor locator mismatch")
        editor_fd = os.open(
            editor_directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            os.fsync(editor_fd)
        finally:
            os.close(editor_fd)
        isolated_files += 1

    if render_directory is not None:
        render_file = render_directory / RENDER_DSN_FILE
        expected_render_dsn = dsn_files["service-public-dsn"]
        initialize_render_file = not render_file.exists()
        if initialize_render_file:
            if validate_only:
                raise SecretInitializationError(
                    "Render secret directory is unavailable"
                )
            if render_directory.exists() and any(render_directory.iterdir()):
                raise SecretInitializationError(
                    "Render secret directory policy mismatch"
                )
            _prepare_directory(
                render_directory,
                mode=CONTROL_DIRECTORY_MODE,
                uid=DIRECTORY_UID,
                gid=DIRECTORY_UID,
            )
            _write_once(render_file, expected_render_dsn, uid=APPLICATION_UID)
        _prepare_directory(
            render_directory,
            mode=CONTROL_DIRECTORY_MODE,
            uid=APPLICATION_UID,
            gid=APPLICATION_UID,
        )
        if {path.name for path in render_directory.iterdir()} != {RENDER_DSN_FILE}:
            raise SecretInitializationError("Render secret directory policy mismatch")
        actual_render_dsn = _read_secret(render_file, uid=APPLICATION_UID)
        if not secrets.compare_digest(actual_render_dsn, expected_render_dsn):
            raise SecretInitializationError("isolated Render locator mismatch")
        render_fd = os.open(
            render_directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            os.fsync(render_fd)
        finally:
            os.close(render_fd)
        isolated_files += 1

    if media_directory is not None:
        media_file = media_directory / MEDIA_DSN_FILE
        expected_media_dsn = dsn_files["service-media-dsn"]
        initialize_media_file = not media_file.exists()
        if initialize_media_file:
            if validate_only:
                raise SecretInitializationError("Media secret directory is unavailable")
            if media_directory.exists() and any(media_directory.iterdir()):
                raise SecretInitializationError(
                    "Media secret directory policy mismatch"
                )
            _prepare_directory(
                media_directory,
                mode=CONTROL_DIRECTORY_MODE,
                uid=DIRECTORY_UID,
                gid=DIRECTORY_UID,
            )
            _write_once(media_file, expected_media_dsn, uid=APPLICATION_UID)
        _prepare_directory(
            media_directory,
            mode=CONTROL_DIRECTORY_MODE,
            uid=CONTROL_DIRECTORY_UID,
            gid=CONTROL_DIRECTORY_GID,
        )
        if {path.name for path in media_directory.iterdir()} != {MEDIA_DSN_FILE}:
            raise SecretInitializationError("Media secret directory policy mismatch")
        actual_media_dsn = _read_secret(media_file, uid=APPLICATION_UID)
        if not secrets.compare_digest(actual_media_dsn, expected_media_dsn):
            raise SecretInitializationError("isolated Media locator mismatch")
        media_fd = os.open(
            media_directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        )
        try:
            os.fsync(media_fd)
        finally:
            os.close(media_fd)
        isolated_files += 1

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
    parser.add_argument(
        "--agent-directory",
        type=Path,
        default=Path("/run/slaif-agent"),
    )
    parser.add_argument(
        "--render-directory",
        type=Path,
        default=Path("/run/slaif-render"),
    )
    parser.add_argument(
        "--editor-directory",
        type=Path,
        default=Path("/run/slaif-editor"),
    )
    parser.add_argument(
        "--media-directory",
        type=Path,
        default=Path("/run/slaif-media"),
    )
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    try:
        count = initialize(
            arguments.directory,
            control_directory=arguments.control_directory,
            agent_directory=arguments.agent_directory,
            render_directory=arguments.render_directory,
            editor_directory=arguments.editor_directory,
            media_directory=arguments.media_directory,
            validate_only=arguments.validate_only,
        )
    except (OSError, SecretInitializationError):
        print("local-secrets: FAILED", flush=True)
        return 1
    print(f"local-secrets: READY files={count}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Local credential generator tests without exposing generated values."""

from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


def _load_initializer() -> ModuleType:
    path = Path(__file__).parents[2] / "tools/local_secrets/initialize.py"
    spec = importlib.util.spec_from_file_location("local_secret_initializer", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INITIALIZER = _load_initializer()


class LocalSecretTests(unittest.TestCase):
    def test_generation_is_distinct_restrictive_and_idempotent(self) -> None:
        INITIALIZER.POSTGRES_UID = os.getuid()
        INITIALIZER.APPLICATION_UID = os.getuid()
        INITIALIZER.MARKER_UID = os.getuid()
        INITIALIZER.DIRECTORY_UID = os.getuid()
        INITIALIZER.SECRET_DIRECTORY_GID = os.getgid()
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "secrets"
            count = INITIALIZER.initialize(directory)
            initial = {path.name: path.read_bytes() for path in directory.iterdir()}
            self.assertEqual(INITIALIZER.initialize(directory), count)
            self.assertEqual(
                initial,
                {path.name: path.read_bytes() for path in directory.iterdir()},
            )
            passwords = [
                value
                for name, value in initial.items()
                if name == "postgres-password" or name.startswith("login-")
            ]
            self.assertEqual(len(passwords), 11)
            self.assertEqual(len(set(passwords)), 11)
            info = directory.stat()
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o710)
            self.assertEqual(info.st_uid, os.getuid())
            self.assertEqual(info.st_gid, os.getgid())
            for path in directory.iterdir():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)

    def test_incomplete_secret_is_rejected_without_replacement(self) -> None:
        INITIALIZER.POSTGRES_UID = os.getuid()
        INITIALIZER.APPLICATION_UID = os.getuid()
        INITIALIZER.MARKER_UID = os.getuid()
        INITIALIZER.DIRECTORY_UID = os.getuid()
        INITIALIZER.SECRET_DIRECTORY_GID = os.getgid()
        with tempfile.TemporaryDirectory() as parent:
            directory = Path(parent) / "secrets"
            directory.mkdir(mode=0o710)
            broken = directory / "postgres-password"
            broken.touch(mode=0o400)
            with self.assertRaises(INITIALIZER.SecretInitializationError):
                INITIALIZER.initialize(directory)
            self.assertEqual(broken.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()

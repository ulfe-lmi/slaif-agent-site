"""Bounded Chrome-for-Testing archive extractor proof."""

from __future__ import annotations

import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
EXTRACTOR = ROOT / "services/browser-worker/extract-zip.mjs"


def _entry(name: str, *, mode: int = 0o100644) -> zipfile.ZipInfo:
    value = zipfile.ZipInfo(name)
    value.create_system = 3
    value.external_attr = mode << 16
    return value


class BrowserArchiveExtractorTests(unittest.TestCase):
    def run_extractor(
        self, archive: Path, destination: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", str(EXTRACTOR), str(archive), str(destination)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_exact_safe_inventory_extracts_with_executable_mode(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent)
            archive = root / "safe.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr(_entry("chrome-linux64/", mode=0o40755), b"")
                bundle.writestr(
                    _entry("chrome-linux64/chrome", mode=0o100755), b"safe-browser"
                )
                bundle.writestr(_entry("chrome-linux64/resource.pak"), b"safe-resource")
            destination = root / "output"
            result = self.run_extractor(archive, destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            executable = destination / "chrome-linux64/chrome"
            self.assertEqual(executable.read_bytes(), b"safe-browser")
            self.assertEqual(stat.S_IMODE(executable.stat().st_mode), 0o755)

    def test_traversal_duplicate_and_crc_corruption_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent)
            traversal = root / "traversal.zip"
            with zipfile.ZipFile(traversal, "w", zipfile.ZIP_STORED) as bundle:
                bundle.writestr(_entry("chrome-linux64/chrome", mode=0o100755), b"ok")
                bundle.writestr(_entry("chrome-linux64/../private"), b"escape")
            self.assertNotEqual(
                self.run_extractor(traversal, root / "traversal-output").returncode,
                0,
            )

            duplicate = root / "duplicate.zip"
            with self.assertWarns(UserWarning):
                with zipfile.ZipFile(duplicate, "w", zipfile.ZIP_STORED) as bundle:
                    bundle.writestr(
                        _entry("chrome-linux64/chrome", mode=0o100755), b"first"
                    )
                    bundle.writestr(
                        _entry("chrome-linux64/chrome", mode=0o100755), b"second"
                    )
            self.assertNotEqual(
                self.run_extractor(duplicate, root / "duplicate-output").returncode,
                0,
            )

            corrupt = root / "corrupt.zip"
            with zipfile.ZipFile(corrupt, "w", zipfile.ZIP_STORED) as bundle:
                bundle.writestr(
                    _entry("chrome-linux64/chrome", mode=0o100755), b"safe-browser"
                )
            value = corrupt.read_bytes()
            marker = value.index(b"safe-browser")
            corrupt.write_bytes(value[:marker] + b"X" + value[marker + 1 :])
            self.assertNotEqual(
                self.run_extractor(corrupt, root / "corrupt-output").returncode,
                0,
            )


if __name__ == "__main__":
    unittest.main()

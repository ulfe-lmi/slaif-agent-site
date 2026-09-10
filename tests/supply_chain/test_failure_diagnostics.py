"""Tests for incomplete supply-chain diagnostic retention."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.supply_chain.failure_diagnostics import (
    retain_failure_diagnostics,
    validate_failure_diagnostics,
)


class FailureDiagnosticsTests(unittest.TestCase):
    def test_retains_safe_raw_outputs_and_marks_bundle_unqualified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            temporary_root = root / "temporary"
            evidence = root / "evidence"
            temporary_root.mkdir()
            (evidence / "scan-sboms").mkdir(parents=True)
            (temporary_root / "browser-worker.raw.grype.json").write_text(
                '{"matches":[{"vulnerability":{"id":"CVE-TEST"}]}\n',
                encoding="utf-8",
            )
            (evidence / "scan-sboms/browser-worker.syft.json").write_text(
                '{"artifacts":[]}\n', encoding="utf-8"
            )
            (temporary_root / "unsafe.raw.syft.json").write_text(
                "postgresql://must-not-be-retained\n", encoding="utf-8"
            )

            destination = retain_failure_diagnostics(temporary_root, evidence, 1)
            validate_failure_diagnostics(destination)
            status = json.loads((destination / "STATUS.json").read_text())

            self.assertEqual(status["status"], "INCOMPLETE")
            self.assertEqual(status["qualification"], "UNQUALIFIED")
            self.assertEqual(status["success_manifest"], "ABSENT")
            self.assertEqual(status["original_exit_status"], 1)
            self.assertTrue((destination / "browser-worker.raw.grype.json").exists())
            self.assertTrue(
                (destination / "normalized-browser-worker.syft.json").exists()
            )
            self.assertFalse((destination / "unsafe.raw.syft.json").exists())
            self.assertFalse((destination / "index.json").exists())
            self.assertFalse((destination / "SUMMARY.txt").exists())


if __name__ == "__main__":
    unittest.main()

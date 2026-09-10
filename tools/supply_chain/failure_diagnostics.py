#!/usr/bin/env python3
"""Retain bounded, secret-safe diagnostics when supply-chain validation fails."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from tools.supply_chain.policy import POLICY_PATH, ROOT, load_json

RAW_FILE = re.compile(r"^[a-z0-9-]+\.raw\.(?:spdx|syft|grype)\.json$")
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
STATUS_NAME = "STATUS.json"
CHECKSUMS_NAME = "SHA256SUMS"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _forbidden_markers() -> tuple[bytes, ...]:
    try:
        evidence = load_json(ROOT / POLICY_PATH.relative_to(ROOT))["evidence"]
        markers = evidence["forbidden_secret_markers"]
        prefixes = evidence["forbidden_host_prefixes"]
        values = [*markers, *prefixes]
    except (KeyError, TypeError, OSError, ValueError):
        values = [
            "BEGIN PRIVATE KEY",
            "postgresql://",
            "ghp_",
            "github_pat_",
            "AKIA",
            "/home/runner/",
            "/home/ubuntu/",
            "/Users/",
            "C:\\\\Users\\\\",
        ]
    return tuple(str(value).casefold().encode("utf-8") for value in values)


def _safe_bytes(data: bytes, markers: tuple[bytes, ...]) -> bool:
    lowered = data.lower()
    return not any(marker in lowered for marker in markers) and not re.search(
        rb"-----begin [a-z ]*private key-----", lowered
    )


def retain_failure_diagnostics(
    temporary_root: Path, evidence_root: Path, exit_status: int
) -> Path:
    """Copy only scanner JSON into an explicitly incomplete diagnostic bundle."""

    destination = evidence_root / "failure-diagnostics"
    destination.mkdir(parents=True, exist_ok=True)
    markers = _forbidden_markers()
    retained: list[str] = []
    omitted: list[dict[str, str]] = []
    total_bytes = 0

    candidates = sorted(
        path
        for path in temporary_root.rglob("*")
        if path.is_file() and RAW_FILE.fullmatch(path.name)
    )
    scan_sboms = evidence_root / "scan-sboms"
    candidates.extend(
        sorted(path for path in scan_sboms.glob("*.syft.json") if path.is_file())
    )
    for source in candidates:
        name = source.name
        if source.parent == scan_sboms:
            name = f"normalized-{name}"
        data_size = source.stat().st_size
        if data_size > MAX_FILE_BYTES:
            omitted.append({"file": name, "reason": "file-size-limit"})
            continue
        if total_bytes + data_size > MAX_TOTAL_BYTES:
            omitted.append({"file": name, "reason": "total-size-limit"})
            continue
        data = source.read_bytes()
        if not _safe_bytes(data, markers):
            omitted.append({"file": name, "reason": "safety-filter"})
            continue
        target = destination / name
        shutil.copyfile(source, target)
        retained.append(name)
        total_bytes += data_size

    status = {
        "diagnostic_files": sorted(retained),
        "omitted_files": sorted(omitted, key=lambda item: item["file"]),
        "original_exit_status": exit_status,
        "qualification": "UNQUALIFIED",
        "schema_version": 1,
        "status": "INCOMPLETE",
        "success_manifest": "ABSENT",
    }
    (destination / STATUS_NAME).write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    files = sorted(path for path in destination.iterdir() if path.is_file())
    (destination / CHECKSUMS_NAME).write_text(
        "".join(
            f"{sha256_file(path)}  {path.name}\n"
            for path in files
            if path.name != CHECKSUMS_NAME
        ),
        encoding="utf-8",
    )
    return destination


def validate_failure_diagnostics(root: Path) -> None:
    status = json.loads((root / STATUS_NAME).read_text(encoding="utf-8"))
    if status != {
        "diagnostic_files": status["diagnostic_files"],
        "omitted_files": status["omitted_files"],
        "original_exit_status": status["original_exit_status"],
        "qualification": "UNQUALIFIED",
        "schema_version": 1,
        "status": "INCOMPLETE",
        "success_manifest": "ABSENT",
    }:
        raise ValueError("failure diagnostics status is not explicitly incomplete")
    checksums = (root / CHECKSUMS_NAME).read_text(encoding="utf-8").splitlines()
    recorded = {}
    for line in checksums:
        digest, name = line.split("  ", 1)
        recorded[name] = digest
    actual = {
        path.name: sha256_file(path)
        for path in sorted(root.iterdir())
        if path.is_file() and path.name != CHECKSUMS_NAME
    }
    if recorded != actual:
        raise ValueError("failure diagnostics checksums do not match")
    if "index.json" in recorded or "SUMMARY.txt" in recorded:
        raise ValueError("failure diagnostics contain a success artifact")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    retain = subparsers.add_parser("retain")
    retain.add_argument("--temporary-root", type=Path, required=True)
    retain.add_argument("--evidence", type=Path, required=True)
    retain.add_argument("--exit-status", type=int, required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.command == "retain":
        retain_failure_diagnostics(
            arguments.temporary_root, arguments.evidence, arguments.exit_status
        )
    else:
        validate_failure_diagnostics(arguments.root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

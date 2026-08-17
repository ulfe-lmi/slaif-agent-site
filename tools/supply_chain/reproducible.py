#!/usr/bin/env python3
"""Prove deterministic Python and Node application-artifact contracts."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from tools.supply_chain.policy import (
    POLICY_PATH,
    ROOT,
    PolicyError,
    load_json,
    write_json,
)

PYTHON_INPUTS = (
    "LICENSE",
    "NOTICE",
    "README.md",
    "alembic.ini",
    "migrations",
    "pyproject.toml",
    "services/backend/src",
    "uv.lock",
)
NODE_OUTPUTS = (
    "apps/web/.next/standalone",
    "apps/web/.next/static",
    "apps/web/public",
)
BROWSER_RUNTIME = (
    "services/browser-worker/package.json",
    "services/browser-worker/src",
)
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], cwd: Path, environment: dict[str, str]) -> None:
    completed = subprocess.run(command, cwd=cwd, env=environment, check=False)
    if completed.returncode:
        raise PolicyError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
        )


def copy_python_source(root: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative in PYTHON_INPUTS:
        source = root / relative
        target = destination / relative
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def artifact_manifest(directory: Path) -> list[dict[str, Any]]:
    artifacts = [
        {
            "name": path.name,
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
        for path in sorted(directory.iterdir(), key=lambda item: item.name)
        if path.is_file()
        and (path.name.endswith(".whl") or path.name.endswith(".tar.gz"))
    ]
    if len(artifacts) != 2:
        raise PolicyError("Python build must produce exactly one wheel and one sdist")
    return artifacts


def clean_node_outputs(root: Path) -> None:
    targets = [root / "apps/web/.next"]
    targets.extend(sorted((root / "packages").glob("*/dist")))
    for target in targets:
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)


def tree_manifest(root: Path, relative_paths: tuple[str, ...]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for relative in relative_paths:
        target = root / relative
        candidates = (
            [target] if target.is_file() or target.is_symlink() else target.rglob("*")
        )
        for path in candidates:
            path_relative = path.relative_to(root)
            if any(part in IGNORED_PARTS for part in path_relative.parts):
                continue
            metadata = path.lstat()
            if stat.S_ISDIR(metadata.st_mode):
                continue
            entry: dict[str, Any] = {
                "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
                "path": path_relative.as_posix(),
                "size": metadata.st_size,
                "type": "file",
            }
            if stat.S_ISLNK(metadata.st_mode):
                entry["type"] = "symlink"
                entry["target"] = os.readlink(path)
            elif stat.S_ISREG(metadata.st_mode):
                entry["sha256"] = sha256_file(path)
            else:
                raise PolicyError(f"unsupported build output type: {path_relative}")
            entries.append(entry)
    return sorted(entries, key=lambda item: item["path"])


def workspace_output_paths(root: Path) -> tuple[str, ...]:
    return tuple(
        path.relative_to(root).as_posix()
        for path in sorted((root / "packages").glob("*/dist"))
    )


def find_generated_contracts(root: Path) -> list[str]:
    found: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        lower = path.name.casefold()
        if lower in {"openapi.json", "openapi.yaml", "openapi.yml"}:
            found.append(relative.as_posix())
    return sorted(found)


def reproduce(root: Path, output: Path) -> dict[str, Any]:
    policy = load_json(root / POLICY_PATH.relative_to(ROOT))
    epoch = str(policy["source_date_epoch"])
    environment = os.environ.copy()
    environment.update(
        {
            "NEXT_TELEMETRY_DISABLED": "1",
            "SOURCE_DATE_EPOCH": epoch,
            "UV_FROZEN": "1",
            "UV_NO_PROGRESS": "1",
            "UV_OFFLINE": "1",
        }
    )
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="slaif-supply-repro-") as temporary:
        temporary_root = Path(temporary)
        python_manifests: list[list[dict[str, Any]]] = []
        python_outputs: list[Path] = []
        for attempt in (1, 2):
            source = temporary_root / f"python-source-{attempt}"
            distributions = temporary_root / f"python-dist-{attempt}"
            copy_python_source(root, source)
            distributions.mkdir()
            run(
                ["uv", "build", "--offline", "--out-dir", str(distributions)],
                source,
                environment,
            )
            python_manifests.append(artifact_manifest(distributions))
            python_outputs.append(distributions)
        if python_manifests[0] != python_manifests[1]:
            raise PolicyError("Python wheel/sdist outputs are not byte-identical")
        retained_python = output / "artifacts/python"
        retained_python.mkdir(parents=True)
        for artifact in sorted(python_outputs[0].iterdir()):
            if not (
                artifact.name.endswith(".whl") or artifact.name.endswith(".tar.gz")
            ):
                continue
            shutil.copy2(artifact, retained_python / artifact.name)

        node_attempts: list[dict[str, Any]] = []
        for _attempt in (1, 2):
            clean_node_outputs(root)
            run(["pnpm", "--recursive", "run", "build"], root, environment)
            build_id = (
                (root / "apps/web/.next/BUILD_ID").read_text(encoding="ascii").strip()
            )
            if not re_full_hex(build_id, 32):
                raise PolicyError("Next.js deterministic build ID is malformed")
            node_attempts.append(
                {
                    "browser_runtime": tree_manifest(root, BROWSER_RUNTIME),
                    "build_id": build_id,
                    "web_distribution": tree_manifest(root, NODE_OUTPUTS),
                    "workspace_outputs": tree_manifest(
                        root, workspace_output_paths(root)
                    ),
                }
            )
        if node_attempts[0] != node_attempts[1]:
            raise PolicyError("Web/browser normalized output manifests differ")

    generated_contracts = find_generated_contracts(root)
    if generated_contracts:
        raise PolicyError(
            "generated OpenAPI/product contracts are not approved: "
            + ", ".join(generated_contracts)
        )
    result = {
        "browser_worker": {
            "build_output": "none-by-design",
            "runtime_source_manifest": node_attempts[0]["browser_runtime"],
        },
        "generated_openapi_or_product_contracts": [],
        "next_build_id": node_attempts[0]["build_id"],
        "python_artifacts": python_manifests[0],
        "schema_version": 1,
        "source_date_epoch": int(epoch),
        "web_distribution_manifest": node_attempts[0]["web_distribution"],
        "workspace_output_manifest": node_attempts[0]["workspace_outputs"],
    }
    write_json(output / "reproducibility.json", result)
    return result


def re_full_hex(value: str, length: int) -> bool:
    return len(value) == length and all(
        character in "0123456789abcdef" for character in value
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        result = reproduce(arguments.root.resolve(), arguments.output.resolve())
    except (OSError, PolicyError) as exc:
        print(f"reproducibility: ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        "reproducibility: OK "
        f"python-artifacts={len(result['python_artifacts'])} "
        f"next-build-id={result['next_build_id']} "
        "browser-output=source-contract"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

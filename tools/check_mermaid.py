#!/usr/bin/env python3
"""Extract and render every Mermaid fence in repository Markdown.

Usage:
    python tools/check_mermaid.py [--root PATH]

The exact Mermaid CLI is obtained transiently through ``npx --yes``. Inputs
and rendered outputs exist only in a system temporary directory; this command
does not create a Node manifest or write generated files into the repository.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

MERMAID_CLI_VERSION = "11.16.0"
MERMAID_PACKAGE = f"@mermaid-js/mermaid-cli@{MERMAID_CLI_VERSION}"
RENDER_TIMEOUT_SECONDS = 300
MAX_RENDERER_OUTPUT = 2_000
SKIP_DIRS = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "env",
    "generated",
    "htmlcov",
    "node_modules",
    "out",
    "target",
    "vendor",
    "venv",
}
FENCE_OPEN = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class MermaidBlock:
    """One extracted Mermaid block and its source diagnostic location."""

    source: Path
    opening_line: int
    content: str


class MermaidExtractionError(ValueError):
    """Raised when a Mermaid fence is opened but never closed."""

    def __init__(self, source: Path, opening_line: int) -> None:
        self.source = source
        self.opening_line = opening_line
        super().__init__(f"{source.as_posix()}:{opening_line}: unclosed Mermaid fence")


@dataclass(frozen=True)
class RenderFailure:
    """Bounded renderer failure tied back to Markdown source."""

    block: MermaidBlock
    reason: str
    stdout: str = ""
    stderr: str = ""


Runner = Callable[..., subprocess.CompletedProcess[str]]


def discover_markdown(root: Path) -> list[Path]:
    """Return repository Markdown files in stable relative-path order."""

    root = root.resolve()
    paths = [
        path
        for path in root.rglob("*.md")
        if path.is_file()
        and not any(part in SKIP_DIRS for part in path.relative_to(root).parts)
    ]
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def extract_mermaid_blocks(path: Path, root: Path) -> list[MermaidBlock]:
    """Extract exact ``mermaid`` info-string fences from one Markdown file."""

    root = root.resolve()
    source = path.resolve().relative_to(root)
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[MermaidBlock] = []
    fence_character: str | None = None
    fence_length = 0
    is_mermaid = False
    opening_line = 0
    content: list[str] = []

    for line_number, line in enumerate(lines, start=1):
        if fence_character is None:
            match = FENCE_OPEN.match(line)
            if match is None:
                continue
            fence = match.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            is_mermaid = match.group("info").strip() == "mermaid"
            opening_line = line_number
            content = []
            continue

        closing = re.fullmatch(
            rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
            line,
        )
        if closing is not None:
            if is_mermaid:
                blocks.append(
                    MermaidBlock(
                        source=source,
                        opening_line=opening_line,
                        content="\n".join(content) + "\n",
                    )
                )
            fence_character = None
            fence_length = 0
            is_mermaid = False
            opening_line = 0
            content = []
        elif is_mermaid:
            content.append(line)

    if fence_character is not None and is_mermaid:
        raise MermaidExtractionError(source, opening_line)
    return blocks


def build_renderer_command(input_path: Path, output_path: Path) -> list[str]:
    """Build the exact-version, no-shell renderer argument list."""

    return [
        "npx",
        "--yes",
        MERMAID_PACKAGE,
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    ]


def bounded_output(value: str | bytes | None, temporary_root: Path) -> str:
    """Normalize random temporary paths and bound captured renderer output."""

    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = value
    normalized = text.replace(str(temporary_root), "<temporary>").strip()
    if len(normalized) > MAX_RENDERER_OUTPUT:
        normalized = normalized[:MAX_RENDERER_OUTPUT] + "\n[output truncated]"
    return normalized


def render_blocks(
    blocks: Sequence[MermaidBlock],
    repository_root: Path,
    runner: Runner = subprocess.run,
) -> list[RenderFailure]:
    """Render blocks in a temporary directory and return stable diagnostics."""

    if not blocks:
        return []
    repository_root = repository_root.resolve()
    failures: list[RenderFailure] = []
    with tempfile.TemporaryDirectory(prefix="slaif-mermaid-") as temporary_name:
        temporary_root = Path(temporary_name).resolve()
        if (
            temporary_root == repository_root
            or repository_root in temporary_root.parents
        ):
            raise RuntimeError(
                "temporary Mermaid output directory is inside repository root"
            )
        for index, block in enumerate(blocks, start=1):
            input_path = temporary_root / f"diagram-{index:03d}.mmd"
            output_path = temporary_root / f"diagram-{index:03d}.svg"
            input_path.write_text(block.content, encoding="utf-8")
            command = build_renderer_command(input_path, output_path)
            try:
                result = runner(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=RENDER_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                failures.append(
                    RenderFailure(
                        block=block,
                        reason=(
                            f"renderer timed out after {RENDER_TIMEOUT_SECONDS} seconds"
                        ),
                        stdout=bounded_output(exc.stdout, temporary_root),
                        stderr=bounded_output(exc.stderr, temporary_root),
                    )
                )
                continue
            except OSError as exc:
                failures.append(
                    block_failure(block, f"renderer could not start: {exc}")
                )
                continue

            stdout = bounded_output(result.stdout, temporary_root)
            stderr = bounded_output(result.stderr, temporary_root)
            if result.returncode != 0:
                failures.append(
                    RenderFailure(
                        block=block,
                        reason=f"renderer exited with status {result.returncode}",
                        stdout=stdout,
                        stderr=stderr,
                    )
                )
            elif not output_path.is_file():
                failures.append(
                    RenderFailure(
                        block=block,
                        reason="renderer succeeded without creating its output",
                        stdout=stdout,
                        stderr=stderr,
                    )
                )
    return failures


def block_failure(block: MermaidBlock, reason: str) -> RenderFailure:
    """Construct a renderer failure without captured process output."""

    return RenderFailure(block=block, reason=reason)


def emit_failure(failure: RenderFailure, stream: TextIO) -> None:
    """Print one source-bound, bounded failure diagnostic."""

    location = f"{failure.block.source.as_posix()}:{failure.block.opening_line}"
    print(f"ERROR {location}: {failure.reason}", file=stream)
    if failure.stderr:
        print(f"STDERR {location}: {failure.stderr}", file=stream)
    if failure.stdout:
        print(f"STDOUT {location}: {failure.stdout}", file=stream)


def run_check(
    root: Path,
    runner: Runner = subprocess.run,
    stream: TextIO = sys.stdout,
) -> int:
    """Discover, extract, render, and report a deterministic check result."""

    root = root.resolve()
    markdown_files = discover_markdown(root)
    blocks: list[MermaidBlock] = []
    extraction_errors: list[str] = []
    for path in markdown_files:
        try:
            blocks.extend(extract_mermaid_blocks(path, root))
        except MermaidExtractionError as exc:
            extraction_errors.append(str(exc))
        except (OSError, UnicodeError) as exc:
            source = path.relative_to(root).as_posix()
            extraction_errors.append(f"{source}: cannot read Markdown ({exc})")

    if extraction_errors:
        for error in sorted(extraction_errors):
            print(f"ERROR {error}", file=stream)
        print(
            f"FAIL Mermaid extraction ({len(extraction_errors)} error(s))", file=stream
        )
        return 1

    failures = render_blocks(blocks, root, runner=runner)
    if failures:
        for failure in failures:
            emit_failure(failure, stream)
        print(f"FAIL Mermaid rendering ({len(failures)} error(s))", file=stream)
        return 1

    diagram_files = len({block.source for block in blocks})
    print(
        "PASS Mermaid rendering: "
        f"{len(blocks)} diagram(s) in {diagram_files} file(s); "
        f"{len(markdown_files)} Markdown file(s) scanned; CLI {MERMAID_CLI_VERSION}",
        file=stream,
    )
    return 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of this tool's directory)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return run_check(args.root)


if __name__ == "__main__":
    sys.exit(main())

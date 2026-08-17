"""Isolated tests for deterministic Mermaid extraction and rendering."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.check_mermaid import (
    MAX_RENDERER_OUTPUT,
    MERMAID_PACKAGE,
    MermaidBlock,
    MermaidExtractionError,
    build_renderer_command,
    discover_markdown,
    extract_mermaid_blocks,
    render_blocks,
    run_check,
)


class MermaidCheckTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_extracts_multiple_fences_with_source_lines(self) -> None:
        path = self.write(
            "docs/diagrams.md",
            "# Diagrams\n"
            "```mermaid\n"
            "flowchart LR\n"
            "    A --> B\n"
            "```\n"
            "text\n"
            "  ~~~~  mermaid  \n"
            "sequenceDiagram\n"
            "    A->>B: message\n"
            "~~~~\n",
        )

        blocks = extract_mermaid_blocks(path, self.root)

        self.assertEqual([block.opening_line for block in blocks], [2, 7])
        self.assertEqual([block.source.as_posix() for block in blocks], ["docs/diagrams.md"] * 2)
        self.assertEqual(blocks[0].content, "flowchart LR\n    A --> B\n")
        self.assertEqual(blocks[1].content, "sequenceDiagram\n    A->>B: message\n")

    def test_discovery_excludes_generated_cache_and_environment_directories(self) -> None:
        self.write("README.md", "# Included\n")
        self.write("docs/guide.md", "# Included\n")
        for directory in (".cache", ".git", ".venv", "build", "generated", "node_modules", "vendor"):
            self.write(f"{directory}/excluded.md", "# Excluded\n")

        discovered = [path.relative_to(self.root).as_posix() for path in discover_markdown(self.root)]

        self.assertEqual(discovered, ["README.md", "docs/guide.md"])

    def test_ignores_non_mermaid_and_non_exact_info_strings(self) -> None:
        path = self.write(
            "mixed.md",
            "```python\n"
            "```mermaid\n"
            "```\n"
            "```\n"
            "```Mermaid\n"
            "flowchart LR\n"
            "```\n"
            "```mermaid extra\n"
            "flowchart LR\n"
            "```\n",
        )

        self.assertEqual(extract_mermaid_blocks(path, self.root), [])

    def test_unclosed_mermaid_fence_reports_source_line(self) -> None:
        path = self.write("broken.md", "intro\n\n```mermaid\nflowchart LR\n")

        with self.assertRaises(MermaidExtractionError) as context:
            extract_mermaid_blocks(path, self.root)

        self.assertEqual(context.exception.source, Path("broken.md"))
        self.assertEqual(context.exception.opening_line, 3)
        self.assertIn("broken.md:3: unclosed Mermaid fence", str(context.exception))

    def test_no_diagrams_succeeds_without_invoking_renderer(self) -> None:
        self.write("README.md", "# No diagrams\n\n```text\nplain\n```\n")
        stream = StringIO()

        def unexpected_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            self.fail("renderer must not run when there are no Mermaid blocks")

        status = run_check(self.root, runner=unexpected_runner, stream=stream)

        self.assertEqual(status, 0)
        self.assertIn("0 diagram(s) in 0 file(s); 1 Markdown file(s) scanned", stream.getvalue())

    def test_renderer_command_uses_exact_package_and_argument_list(self) -> None:
        command = build_renderer_command(Path("input.mmd"), Path("output.svg"))

        self.assertEqual(
            command,
            [
                "npx",
                "--yes",
                MERMAID_PACKAGE,
                "--input",
                "input.mmd",
                "--output",
                "output.svg",
            ],
        )
        self.assertIn("@11.16.0", command[2])

    def test_renderer_success_is_confined_and_sources_are_unchanged(self) -> None:
        source = self.write(
            "diagram.md",
            "```mermaid\nflowchart LR\n    A --> B\n```\n",
        )
        original = source.read_bytes()
        block = extract_mermaid_blocks(source, self.root)[0]
        observed_paths: list[Path] = []

        def successful_runner(
            command: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            input_path = Path(command[command.index("--input") + 1])
            output_path = Path(command[command.index("--output") + 1])
            observed_paths.extend((input_path, output_path))
            self.assertTrue(input_path.is_file())
            self.assertEqual(input_path.read_text(encoding="utf-8"), block.content)
            output_path.write_text("<svg/>\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="rendered", stderr="")

        failures = render_blocks([block], self.root, runner=successful_runner)

        self.assertEqual(failures, [])
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(len(observed_paths), 2)
        for path in observed_paths:
            self.assertNotIn(self.root.resolve(), path.resolve().parents)
            self.assertFalse(path.exists())

    def test_renderer_failure_has_source_line_and_bounded_normalized_output(self) -> None:
        source = self.write(
            "docs/failure.md",
            "intro\n```mermaid\nflowchart LR\n```\n",
        )
        captured_temporary_path = ""

        def failing_runner(
            command: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            nonlocal captured_temporary_path
            input_path = Path(command[command.index("--input") + 1])
            captured_temporary_path = str(input_path.parent)
            return subprocess.CompletedProcess(
                command,
                2,
                stdout="x" * (MAX_RENDERER_OUTPUT + 100),
                stderr=f"parse failed in {input_path}",
            )

        stream = StringIO()
        status = run_check(self.root, runner=failing_runner, stream=stream)
        output = stream.getvalue()

        self.assertEqual(status, 1)
        self.assertIn("ERROR docs/failure.md:2: renderer exited with status 2", output)
        self.assertIn("<temporary>/diagram-001.mmd", output)
        self.assertIn("[output truncated]", output)
        self.assertNotIn(captured_temporary_path, output)

    def test_renderer_success_without_output_is_a_failure(self) -> None:
        block = MermaidBlock(Path("diagram.md"), 4, "flowchart LR\n")

        def outputless_runner(
            command: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        failures = render_blocks([block], self.root, runner=outputless_runner)

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].reason, "renderer succeeded without creating its output")

    def test_extraction_failure_prevents_renderer_invocation(self) -> None:
        self.write("broken.md", "```mermaid\nflowchart LR\n")
        stream = StringIO()

        def unexpected_runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
            self.fail("renderer must not run after extraction failure")

        status = run_check(self.root, runner=unexpected_runner, stream=stream)

        self.assertEqual(status, 1)
        self.assertIn("ERROR broken.md:1: unclosed Mermaid fence", stream.getvalue())
        self.assertIn("FAIL Mermaid extraction (1 error(s))", stream.getvalue())


if __name__ == "__main__":
    unittest.main()

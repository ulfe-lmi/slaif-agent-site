"""D1 split Foundation PostgreSQL CI jobs: structure and hostile behavior.

Proves, from the workflow source without any YAML parser dependency:
- the two child jobs keep the complete PG14..18 matrices with isolated
  disposable PostgreSQL services and the unchanged five exact commands,
  split 85 (generic + 19-file bootstrap/privilege) and 45 (component +
  theme + page-style) per version; group B additionally appends the
  public whole-session promotion qualification module as a fourth exact
  pytest command (Q; no -k selection), making B 45+Q;
- the five exact required names are supplied by an aggregator that
  depends on BOTH child job IDs with JOB-level always();
- the ACTUAL extracted aggregate script is fail-closed: only the
  cross-value pair (success, success) exits 0; failure/cancelled/skipped/
  missing/unknown/neutral/stuck in either slot refuse.
Omitting or mutating a group, a matrix leg, a needs ID, or weakening the
result check is rejected for those semantic reasons, not by literal
spelling alone.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

PG_MATRIX = 'postgresql: ["14", "15", "16", "17", "18"]'
CHECKOUT = "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_PYTHON = "uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
SETUP_UV = "uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d"
SYNC = "uv sync --frozen --all-groups"

GENERIC = (
    "uv run --frozen pytest "
    "services/backend/tests/integration/test_foundation_postgres.py"
)
_BOOTSTRAP = [
    "test_database_bootstrap.py",
    "test_local_identity.py",
    "test_human_session.py",
    "test_local_authentication.py",
    "test_control_database_integration.py",
    "test_control_auth_http_integration.py",
    "test_sites.py",
    "test_site_control_http_integration.py",
    "test_render_site_resolution.py",
    "test_human_rbac.py",
    "test_membership_control_http.py",
    "test_current_human_control_http.py",
    "test_capability_authentication.py",
    "test_human_agent_session_control.py",
    "test_browser_run_control_plane.py",
    "test_agent_browser_http.py",
    "test_render_browser_preview.py",
    "test_render_projection_integration.py",
    "test_render_preview_session_lock.py",
]
BOOTSTRAP = "uv run --frozen pytest " + " ".join(
    f"services/backend/tests/integration/{name}" for name in _BOOTSTRAP
)
COMPONENT = (
    "uv run --frozen pytest "
    "services/backend/tests/integration/test_agent_mutations.py -k component"
)
THEME = (
    "uv run --frozen pytest "
    "services/backend/tests/integration/test_agent_theme_boundaries.py"
)
PAGE_STYLE = (
    "uv run --frozen pytest services/backend/tests/integration/test_agent_page_style.py"
)
WHOLE_SESSION = (
    "uv run --frozen pytest "
    "services/backend/tests/integration/test_foundation_whole_session_qualification.py"
)


def _job_block(text: str, job_id: str) -> str:
    lines = text.split("\n")
    start = lines.index(f"  {job_id}:")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if re.match(r"^  [a-z][a-z0-9-]*:$", lines[i]):
            end = i
            break
    return "\n".join(lines[start:end])


def _run_values(block: str) -> list[str]:
    values: list[str] = []
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        match = re.match(r"^        run: (.*)$", lines[i])
        if not match:
            i += 1
            continue
        first = match.group(1).strip()
        if first in (">-", ">"):
            parts: list[str] = []
            j = i + 1
            while j < len(lines) and (
                not lines[j].strip() or lines[j].startswith("          ")
            ):
                if lines[j].strip():
                    parts.append(lines[j].strip())
                j += 1
            values.append(" ".join(parts))
            i = j
        else:
            values.append(first)
            i += 1
    return values


def _aggregate_script(block: str) -> str:
    match = re.search(r"^        run: \|\n((?:^          .*$\n?)*)", block, re.M)
    if match is None:
        raise AssertionError("aggregator fail-closed script block missing")
    return "\n".join(
        line[10:] if line.strip() else "" for line in match.group(1).split("\n")
    ).strip("\n")


def _needs_ids(block: str) -> list[str]:
    match = re.search(r"^    needs:\n((?:^      - .*$\n?)*)", block, re.M)
    if match is None:
        raise AssertionError("aggregator needs block missing")
    return re.findall(r"^      - ([a-z0-9-]+)$", match.group(1), re.M)


def _run_aggregate(script: str, group_a: str, group_b: str) -> int:
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
        handle.write(script)
        path = handle.name
    env = {
        "PATH": "/usr/bin:/bin",
        "GROUP_A_RESULT": group_a,
        "GROUP_B_RESULT": group_b,
    }
    return subprocess.run(
        ["/bin/bash", path], env=env, capture_output=True, text=True
    ).returncode


AGGREGATE_NEGATIVES: tuple[tuple[str, str], ...] = (
    ("failure", "success"),
    ("success", "failure"),
    ("cancelled", "success"),
    ("success", "cancelled"),
    ("skipped", "success"),
    ("success", "skipped"),
    ("", "success"),
    ("success", ""),
    ("unknown", "success"),
    ("success", "unknown"),
    ("neutral", "success"),
    ("success", "neutral"),
    ("stuck", "success"),
    ("timed_out", "success"),
    ("success", "timed_out"),
)


def _assert_fail_closed(script: str) -> None:
    assert _run_aggregate(script, "success", "success") == 0
    for group_a, group_b in AGGREGATE_NEGATIVES:
        assert _run_aggregate(script, group_a, group_b) == 1, (group_a, group_b)


def _foundation_blocks(text: str) -> tuple[str, str, str]:
    return (
        _job_block(text, "foundation-pg-group-a"),
        _job_block(text, "foundation-pg-group-b"),
        _job_block(text, "foundation-postgresql"),
    )


def _assert_required_names(text: str) -> None:
    assert text.count("    name: Foundation PostgreSQL ${{ matrix.postgresql }}") == 1


def _assert_exact_commands(text: str) -> None:
    job_a, job_b, _gate = _foundation_blocks(text)
    assert _run_values(job_a) == [SYNC, GENERIC, BOOTSTRAP]
    assert _run_values(job_b) == [SYNC, COMPONENT, THEME, PAGE_STYLE, WHOLE_SESSION]


def _assert_complete_matrices(text: str) -> None:
    for block in _foundation_blocks(text):
        assert PG_MATRIX in block
        assert "fail-fast: false" in block
        assert re.search(r"^\s*(include|exclude):", block, re.M) is None


def _assert_skip_conditions(text: str) -> None:
    job_a, job_b, job_gate = _foundation_blocks(text)
    for block in (job_a, job_b):
        assert re.search(r"^\s+if:", block, re.M) is None
    gate_ifs = re.findall(r"^\s+if: (.*)$", job_gate, re.M)
    assert sorted(gate_ifs) == sorted(["always()", "${{ always() }}"])


def _assert_needs_and_env(text: str) -> None:
    job_gate = _job_block(text, "foundation-postgresql")
    assert _needs_ids(job_gate) == ["foundation-pg-group-a", "foundation-pg-group-b"]
    assert "\n    if: always()" in job_gate
    assert "GROUP_A_RESULT: ${{ needs.foundation-pg-group-a.result }}" in job_gate
    assert "GROUP_B_RESULT: ${{ needs.foundation-pg-group-b.result }}" in job_gate
    assert "\n        if: ${{ always() }}" in job_gate


def _assert_no_weakening(text: str) -> None:
    assert "continue-on-error" not in text
    assert "retries:" not in text


class FoundationCiSplitTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.job_a = _job_block(self.text, "foundation-pg-group-a")
        self.job_b = _job_block(self.text, "foundation-pg-group-b")
        self.job_gate = _job_block(self.text, "foundation-postgresql")

    def test_required_names_and_complete_pg_matrices(self) -> None:
        self.assertEqual(
            self.text.count("    name: Foundation PostgreSQL ${{ matrix.postgresql }}"),
            1,
        )
        for block in (self.job_a, self.job_b, self.job_gate):
            self.assertIn(PG_MATRIX, block)
            self.assertIn("fail-fast: false", block)

    def test_child_isolation_setup_and_unchanged_toolchain(self) -> None:
        for block in (self.job_a, self.job_b):
            self.assertIn("timeout-minutes: 15", block)
            self.assertIn("image: postgres:${{ matrix.postgresql }}", block)
            self.assertIn("POSTGRES_DB: qualification", block)
            self.assertIn("POSTGRES_USER: postgres", block)
            self.assertIn("POSTGRES_PASSWORD: qualification-admin", block)
            self.assertIn("- 5432:5432", block)
            self.assertIn(
                '--health-cmd "pg_isready -U postgres -d qualification"', block
            )
            self.assertIn("PGHOST: 127.0.0.1", block)
            self.assertIn('PGPORT: "5432"', block)
            self.assertIn("PGDATABASE: qualification", block)
            self.assertIn("PGUSER: postgres", block)
            self.assertIn("PGPASSWORD: qualification-admin", block)
            self.assertIn(CHECKOUT, block)
            self.assertIn(SETUP_PYTHON, block)
            self.assertIn(SETUP_UV, block)

    def test_exact_five_commands_split_85_plus_45_plus_q(self) -> None:
        self.assertEqual(_run_values(self.job_a), [SYNC, GENERIC, BOOTSTRAP])
        self.assertEqual(
            _run_values(self.job_b),
            [SYNC, COMPONENT, THEME, PAGE_STYLE, WHOLE_SESSION],
        )

    def test_aggregator_depends_on_both_child_jobs_with_job_level_always(self) -> None:
        self.assertIn("\n    if: always()", self.job_gate)
        self.assertEqual(
            _needs_ids(self.job_gate),
            ["foundation-pg-group-a", "foundation-pg-group-b"],
        )
        self.assertIn(
            "GROUP_A_RESULT: ${{ needs.foundation-pg-group-a.result }}",
            self.job_gate,
        )
        self.assertIn(
            "GROUP_B_RESULT: ${{ needs.foundation-pg-group-b.result }}",
            self.job_gate,
        )
        self.assertIn("\n        if: ${{ always() }}", self.job_gate)

    def test_no_scheduling_weakening_anywhere(self) -> None:
        self.assertNotIn("continue-on-error", self.text)
        self.assertNotIn("retries:", self.text)
        timeouts = re.findall(r"^    timeout-minutes: (\d+)$", self.text, re.M)
        # Exact original multiset (10,15,15,15,45,60,10,15,10) plus exactly
        # one new 5-minute aggregator and one additional 15-minute child:
        # no timeout raised, no cap removed.
        self.assertEqual(
            sorted(timeouts),
            ["10", "10", "10", "15", "15", "15", "15", "15", "45", "5", "60"],
            timeouts,
        )
        self.assertIn("    timeout-minutes: 5", self.job_gate)

    def test_extracted_aggregate_script_is_fail_closed(self) -> None:
        _assert_fail_closed(_aggregate_script(self.job_gate))

    def test_baseline_positive_controls(self) -> None:
        _assert_required_names(self.text)
        _assert_exact_commands(self.text)
        _assert_complete_matrices(self.text)
        _assert_skip_conditions(self.text)
        _assert_needs_and_env(self.text)
        _assert_no_weakening(self.text)

    def test_aggregate_script_refuses_unset_environment(self) -> None:
        script = _aggregate_script(self.job_gate)
        for partial in (
            {"GROUP_A_RESULT": "success"},
            {"GROUP_B_RESULT": "success"},
            {},
        ):
            with self.subTest(present=sorted(partial)):
                env = {"PATH": "/usr/bin:/bin", **partial}
                with tempfile.NamedTemporaryFile(
                    "w", suffix=".sh", delete=False
                ) as handle:
                    handle.write(script)
                    path = handle.name
                result = subprocess.run(
                    ["/bin/bash", path], env=env, capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 1)

    def test_mutation_omitted_group_a_command_fails(self) -> None:
        _assert_exact_commands(self.text)
        needle = (
            "\n          uv run --frozen pytest\n"
            "          services/backend/tests/integration/"
            "test_foundation_postgres.py"
        )
        self.assertEqual(self.text.count(needle), 1)
        mutated = self.text.replace(needle, "", 1)
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_exact_commands(mutated)

    def test_mutation_omitted_group_b_command_fails(self) -> None:
        _assert_exact_commands(self.text)
        needle = (
            "\n          uv run --frozen pytest\n"
            "          services/backend/tests/integration/"
            "test_agent_theme_boundaries.py"
        )
        self.assertEqual(self.text.count(needle), 1)
        mutated = self.text.replace(needle, "", 1)
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_exact_commands(mutated)

    def test_mutation_omitted_whole_session_command_fails(self) -> None:
        _assert_exact_commands(self.text)
        needle = (
            "\n          uv run --frozen pytest\n"
            "          services/backend/tests/integration/"
            "test_foundation_whole_session_qualification.py"
        )
        self.assertEqual(self.text.count(needle), 1)
        mutated = self.text.replace(needle, "", 1)
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_exact_commands(mutated)

    def test_mutation_whole_session_selection_added_fails(self) -> None:
        _assert_exact_commands(self.text)
        needle = (
            "          services/backend/tests/integration/"
            "test_foundation_whole_session_qualification.py"
        )
        self.assertEqual(self.text.count(needle), 1)
        mutated = self.text.replace(needle, needle + " -k component", 1)
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_exact_commands(mutated)

    def test_mutation_omitted_matrix_leg_fails(self) -> None:
        _assert_complete_matrices(self.text)
        mutated = self.text.replace(
            PG_MATRIX, 'postgresql: ["14", "15", "16", "17"]', 1
        )
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_complete_matrices(mutated)

    def test_mutation_partial_matrix_via_exclude_fails(self) -> None:
        _assert_complete_matrices(self.text)
        needle = '        postgresql: ["14", "15", "16", "17", "18"]\n'
        self.assertEqual(self.text.count(needle), 3)
        mutated = self.text.replace(
            needle, needle + '        exclude:\n          - postgresql: "18"\n', 1
        )
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_complete_matrices(mutated)

    def test_mutation_omitted_needs_id_fails(self) -> None:
        _assert_needs_and_env(self.text)
        needle = "- foundation-pg-group-b\n"
        self.assertEqual(self.text.count(needle), 1)
        mutated = self.text.replace(needle, "", 1)
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_needs_and_env(mutated)

    def test_mutation_child_job_if_condition_fails(self) -> None:
        _assert_skip_conditions(self.text)
        needle = (
            "    name: Foundation PG Group A PostgreSQL "
            "${{ matrix.postgresql }}\n    runs-on: ubuntu-24.04\n"
            "    timeout-minutes: 15\n"
        )
        self.assertEqual(self.text.count(needle), 1)
        mutated = self.text.replace(needle, needle + "    if: ${{ success() }}\n", 1)
        self.assertNotEqual(mutated, self.text)
        with self.assertRaises(AssertionError):
            _assert_skip_conditions(mutated)

    def test_mutation_weakened_result_guard_fails(self) -> None:
        _assert_fail_closed(_aggregate_script(self.job_gate))
        old_guard = 'if [ "$result" != "success" ]; then'
        new_guard = 'if [ "$result" = "cancelled" ]; then'
        self.assertEqual(self.text.count(old_guard), 1)
        mutated = self.text.replace(old_guard, new_guard, 1)
        self.assertNotEqual(mutated, self.text)
        script = _aggregate_script(_job_block(mutated, "foundation-postgresql"))
        self.assertEqual(_run_aggregate(script, "failure", "success"), 0)
        with self.assertRaises(AssertionError):
            _assert_fail_closed(script)


if __name__ == "__main__":
    unittest.main()

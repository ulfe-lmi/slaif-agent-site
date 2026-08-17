# OAP Work Order — 003-b

## Objective

Amend objective `003` PR `#4` to close an unintended Python quality-gate blind
spot before accepting the foundation baseline. Remove the Ruff exclusions for
the existing Mermaid checker/test, make all tracked Python under the declared
quality paths pass lint and format, remove the observed redundant assignment,
and preserve every foundation/package/PostgreSQL behavior from `003-a`.

## GitHub objective state

- Numeric objective: `003`
- Execution round: `003-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#4`
- Existing PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/4`
- Required head branch: `oap/003-foundation-python-baseline`
- Base branch: `main`
- Verified starting PR head:
  `f2441602dc1258101d565877b88172e83f3f8edd`
- Verified `003-a` implementation head:
  `a90c3eb52ca9f856e86c658ab077520eadfec9a7`
- Verified state: open, non-draft, mergeable, clean, no auto-merge
- Verified final `003-a` checks: sixteen successful, zero open CodeQL alerts

## Strategic review finding

The Python quality job runs:

```bash
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
```

but `pyproject.toml` currently contains:

```toml
[tool.ruff]
extend-exclude = [
  "tests/repository/test_mermaid.py",
  "tools/check_mermaid.py",
]
force-exclude = true
```

`force-exclude` applies to both commands, so those two files are not actually
checked despite appearing in the command line. This contradicts the intended
repository-wide Python baseline and makes the CI/report wording misleading.

Focused review also found a behavior-neutral duplicate line in
`tools/check_mermaid.py`:

```python
stdout = bounded_output(result.stdout, temporary_root)
stdout = bounded_output(result.stdout, temporary_root)
```

The correction must bring both pre-existing files under the quality gate,
remove the duplicate, and change nothing else in behavior.

## Current verified state

- PR `#4` final `003-a` head is the report-only `SELF` commit with the reported
  implementation parent and exactly twenty changed paths.
- Exact foundation PyPI source/version/hashes, Python 3.12–3.14, PostgreSQL
  14–18, package artifacts, unit/policy tests, and all GitHub checks passed.
- Adapter source contains only public `agentcow.postgres` imports and no SQL,
  private storage, credentials, or transaction wrapper.
- Architecture and objectives `000`–`002` remain unchanged.
- PR body still says GitHub CI/CodeQL are pending, although final checks are
  now complete; stable current wording is required.

## Required final tracked paths

The final PR diff against `main` must contain exactly the original twenty
`003-a` paths plus these four append-only/quality paths, twenty-four total:

```text
.github/dependabot.yml
.github/workflows/ci.yml
AGENTS.md
CONTRIBUTING.md
NOTICE
README.md
docs/FOUNDATION_INTEGRATION.md
oap/active
oap/orders/003-a-foundation-qualification-and-python-baseline.md
oap/orders/003-b-close-python-quality-exclusions.md
oap/reports/003-a-foundation-qualification-and-python-baseline.md
oap/reports/003-b-close-python-quality-exclusions.md
pyproject.toml
services/backend/src/slaif_agent_site/__init__.py
services/backend/src/slaif_agent_site/agent_state/__init__.py
services/backend/src/slaif_agent_site/agent_state/foundation.py
services/backend/tests/conftest.py
services/backend/tests/integration/test_foundation_postgres.py
services/backend/tests/unit/test_foundation_contract.py
tests/repository/test_mermaid.py
tests/repository/test_repository_policy.py
tools/check_mermaid.py
tools/check_repository.py
uv.lock
```

## Scope

1. Verify the existing PR/head/branch and preserve immutable `003-a` order/
   report bytes.
2. Commit this strategic-authored `003-b` order and `oap/active` unchanged.
3. Remove the Ruff `extend-exclude`/`force-exclude` blind spot from
   `pyproject.toml`.
4. Apply only the minimal Ruff lint/format changes needed to
   `tools/check_mermaid.py` and `tests/repository/test_mermaid.py` while
   preserving their public behavior and test intent.
5. Remove the duplicate `stdout = bounded_output(...)` assignment.
6. Add a focused repository/contract assertion preventing the declared quality
   paths from silently excluding these tracked Python files again, using an
   already allowed test file if needed.
7. Update PR body to stable present-tense final validation wording without a
   literal latest SHA or future-report promise.
8. Run the complete `003-a` local and GitHub matrix again; publish a new
   immutable `003-b` report in a final report-only `SELF` commit.

## Non-goals

- No foundation dependency/version/lock/artifact/public API change.
- No adapter, package behavior, PostgreSQL qualification semantics, build
  backend, Python range, development dependency, CI job/matrix, docs, NOTICE,
  README, AGENTS, CONTRIBUTING, Dependabot, or workflow change except the
  quality configuration and files explicitly named above.
- No broad refactor or new linter rule.
- No application service/schema/API/UI/Compose work.
- No edit to immutable `003-a` or earlier OAP artifacts.
- No new PR/branch, merge, auto-merge, issue, release, tag, or setting change.

## Requirements

### Complete Python quality coverage

- `ruff check services/backend tests/repository tools` and
  `ruff format --check services/backend tests/repository tools` must actually
  inspect every tracked `.py` file under those roots.
- Use `ruff check --show-files` or an equivalent deterministic assertion to
  enumerate expected files and fail if an in-scope tracked Python file is
  absent.
- Do not replace `force-exclude` with a different hidden/per-file/global ignore
  for the same files.
- Preserve strict mypy coverage for backend source/tests; repository tools need
  not be added to mypy in this correction unless already clean and explicitly
  justified.

### Behavior preservation

- Mermaid extraction/render command, version, timeouts, temp confinement,
  diagnostics, sandboxed CI Chrome behavior, and all ten Mermaid unit tests
  must remain semantically unchanged.
- Repository policy behavior and all existing positive/negative tests remain
  green.
- Foundation adapter/tests/lock/package artifacts remain byte-unchanged unless
  a test-only assertion in an already scoped test file is strictly required;
  explain any such change.

### Final evidence

The `003-b` report must explicitly record:

- removed exclusion settings;
- complete Ruff enumerated file list/count;
- duplicate assignment removal;
- 24-test repository suite plus foundation unit/integration results;
- unchanged lock/foundation artifacts and `003-a` hashes;
- every final-head CI/CodeQL matrix result;
- exact twenty-four-path final scope and report-only topology.

## Acceptance criteria

1. PR `#4` remains the unique objective `003` PR on the same branch/base,
   open/non-draft/mergeable, with no auto-merge.
2. Final diff contains exactly the twenty-four allowed paths.
3. Ruff configuration has no exclusion that omits an in-scope tracked Python
   file; lint and format enumerate and pass every file under the three command
   roots.
4. The duplicate `stdout` assignment is removed and Mermaid behavior/tests/
   render CI remain unchanged and green.
5. Foundation `pyproject` dependency, `uv.lock` source/hashes, adapter public
   API, package artifacts, and PostgreSQL 14–18 qualification remain unchanged
   and successful.
6. All unit/repository/integration/build/metadata/docs checks pass on all
   selected Python/PostgreSQL versions.
7. PR body accurately reflects completed validation without stale pending text.
8. Every final-head check succeeds and CodeQL open alerts are reported.
9. `oap/active` is `003-b`; unique `003-a`/`003-b` order/report correlation
   holds and previous artifacts are byte-unchanged.
10. Final remote head is the `003-b` report-only `SELF` commit with the literal
    implementation head as first parent.
11. No secret, production access, hosted dependency, product behavior,
    architecture drift, or unrelated change occurs.

## Verification required

Run and report exact outcomes for:

```bash
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check --show-files services/backend tests/repository tools
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv run --frozen pytest services/backend/tests/integration
uv build
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Repeat the required Python 3.12–3.14 and PostgreSQL 14–18 GitHub matrices on
both implementation and report heads. Verify lock/artifact hashes, package
contents, immutable `003-a` hashes, no alternate ignore, exact scope, secret
scan, PR identity/body, every final check, CodeQL alerts, report parent/delta,
and clean synchronized worktree.

## Safety / security constraints

- Use only fake disposable test resources; no production or real credential.
- Do not weaken Ruff, tests, workflows, dependency policy, browser sandbox, or
  foundation authority to make checks pass.
- Preserve OAP immutability and no-merge authority.

## Local execution capability

Routine formatting/testing/PostgreSQL/CI diagnosis belongs to the coding agent
inside its disposable VM. Do not transfer it to the human/strategic model.

## GitHub workflow

Amend PR `#4` only, commit the unchanged order/active pointer with the bounded
implementation, push, update the stable PR body, run/repair all checks, then
atomically publish and push the report-only `SELF` commit. Never create another
PR, merge, enable auto-merge, or choose `004-a`.

## Required report

Atomically publish exactly:

```text
oap/reports/003-b-close-python-quality-exclusions.md
```

Use the complete protocol 1.2 format and include every correction, enumerated
file, preserved hash/API/artifact, local/matrix result, final GitHub state,
scope/safety confirmation, and limitation. Signal exact FIFO `OK` only after
the report commit is the verified remote PR head.

# OAP Work Order — 011-g

## Objective and exact state

Amend objective-011 PR #23 by applying Ruff-format to exactly
`tests/packaging/test_compose_smoke_contract.py`, accepting its complete current
three-change formatting result, then obtain final 20/20 current-head evidence.

- Numeric objective: `011`; round: `011-g`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23)
- Base/head: `main` / `oap/011-sites-trusted-resolution`
- Required starting remote head:
  `1596c519d83075c04b824c5a8c5eb9ea4f80e250`
- 011-f implementation parent:
  `6cc7c012dd7fd4fd45ed0dbb0c086d5d87a18ee1`
- Verified failure: Python 3.12/3.13/3.14 pass Ruff check and fail only Ruff-
  format on this one file; every other check, including authoritative Compose,
  is successful on the implementation head.

Fetch and verify the exact open ready PR/head. Amend only PR #23; never create a
PR, merge, close, auto-merge, or workflow-rerun.

## Authorized implementation

Run the repository's frozen formatter on exactly:

```text
uv run --frozen ruff format tests/packaging/test_compose_smoke_contract.py
```

The complete expected semantic-neutral result is:

1. retain 011-f's multi-line `assertGreaterEqual` call;
2. collapse the two adjacent literal strings assigned to `marker` into the same
   single literal value; and
3. normalize the `global_wait` search literal from single to double quotes.

No expression value, expected count, marker text, search text, assertion,
control flow, test name, smoke behavior, or product code may change. No other
file may be formatted or edited except the strategic-owned transcript files.

Verify before push:

```text
uv run --frozen ruff check tests/packaging/test_compose_smoke_contract.py
uv run --frozen ruff format --check tests/packaging/test_compose_smoke_contract.py
python -m unittest tests.packaging.test_compose_smoke_contract
git diff --check
```

Inspect the diff and require exactly the formatter output above. Do not run
local Compose, Playwright, Node, PostgreSQL, images, Mermaid, or SBOM.

## Workflow, acceptance, and report

Target 8 minutes; hard stop 20 minutes. Push exactly one implementation commit
after all four local commands pass. Keep PR #23 ready and inspect its one fresh
complete GitHub generation; no second generation and no rerun. Acceptance
requires 20/20 successful current-head checks and a correct report-only commit.

Commit this order and `oap/active` byte-identically. Atomically publish exactly:

```text
oap/reports/011-g-format-entire-recovery-contract.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
the exact formatter diff, four local passes, PR/head/draft state, all 20 checks,
skips/hashes, and explicit no-new-PR/no-rerun/no-merge. Signal FIFO `OK` only
after report and claimed remote state exist.

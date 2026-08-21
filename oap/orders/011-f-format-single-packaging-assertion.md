# OAP Work Order — 011-f

## Objective and authoritative state

Amend objective-011 PR #23 to reformat the single Ruff E501 assertion at
`tests/packaging/test_compose_smoke_contract.py:64`, without changing test or
product behavior, and obtain final current-head green evidence.

- Numeric objective: `011`; round: `011-f`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23)
- Base/head: `main` / `oap/011-sites-trusted-resolution`
- Required starting remote head:
  `7265910d540a4d2745f085a0ea2c3a9a06834d2f`
- 011-e implementation parent:
  `a724ed04ddfd7d82cf6539c838ff701412f4c062`
- Verified failure: Python 3.12, 3.13, and 3.14 each report only
  `E501 Line too long (89 > 88)` on line 64. Objective-011's authoritative
  Compose recovery and Node behavior passed on the implementation head.

Fetch and verify this exact open ready PR/head. Amend only PR #23; never create
a PR, merge, close, auto-merge, or workflow-rerun.

## Scope and requirements

Allowed implementation file:

```text
tests/packaging/test_compose_smoke_contract.py
```

Reformat the existing `assertGreaterEqual` call across conventional lines so it
passes Ruff and Ruff-format while preserving the exact expression, expected
count, test name, recovery marker/order/fingerprint assertions, and runtime
behavior. Do not edit `tools/compose/smoke.sh`, product code, Web copy, Compose,
docs, configuration, tests beyond that one statement, dependencies, locks, or
any prior OAP artifact.

Run exactly the relevant local proof before push:

```text
uv run --frozen ruff check tests/packaging/test_compose_smoke_contract.py
uv run --frozen ruff format --check tests/packaging/test_compose_smoke_contract.py
python -m unittest tests.packaging.test_compose_smoke_contract
git diff --check
```

Also verify the diff contains only the mechanical assertion formatting plus the
strategic-owned transcript files. Do not run local Compose, Playwright, Node,
PostgreSQL, images, Mermaid, or SBOM; the prior behavioral evidence is unchanged
and GitHub will run all established checks once on the new commit.

## Acceptance and workflow

Target 8 minutes; hard stop 20 minutes. Push exactly one mechanical
implementation commit after local green, keep PR #23 ready, and inspect the
fresh complete GitHub check generation. Do not press rerun or make a second code
generation. All 20 required checks must become successful; report `PARTIAL` if
anything remains failed/pending at the hard boundary.

Commit this order and `oap/active` byte-identically. Atomically publish exactly:

```text
oap/reports/011-f-format-single-packaging-assertion.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
the exact one-statement diff, four local results, PR/head/draft state, final
20-check state, skips, hashes, and explicit no-new-PR/no-rerun/no-merge. Signal
FIFO `OK` only after report and claimed remote state exist.

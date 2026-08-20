# OAP Work Order — 010-d

## Objective

Amend PR `#15` once to reconcile its accepted objective-010 work with current
remote `main` after the compact-governance sequence and PR `#22`. Resolve the
known governance/policy conflicts without beginning any product feature.

This is a governance-only transition round. Server-side sessions, CSRF, HTTP
authentication, UI, Compose wiring, and E2E remain for later `010-e` onward.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-d`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Current remote `main`: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR head: `3ff9202842d974d68987e39ec7ff7f0332736a11`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`
- PR `#15` is the unique objective PR and is currently conflicting with main.

Do not create another PR, rebase, force-push, merge, close, or enable
auto-merge. Do not act on unrelated PRs.

## Strategic context and pre-positioned governance

PR `#22` merged the agent-oriented architecture transition into `main` at
`c37da1e26ee7dad38545511ca7c2e07c63adcff9`. The full human architecture
remains byte-identical with SHA-256
`813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`.

The shared checkout has these human-authorized, uncommitted governance files
pre-positioned so this turn starts under current instructions:

```text
AGENTS.md
OAP-COMMUNICATION-coding-agent.md
ARCHITECTURE-for-agents.md
```

`AGENTS.md` equals current-main compact governance except that it preserves the
objective-010 direct dependency fact `argon2-cffi==25.1.0`. The communication
protocol and agent architecture must match current main exactly. Treat these
bytes as strategic input, not unrelated local edits. Do not load full
`ARCHITECTURE.md`; this order does not authorize it.

Current merge analysis identifies conflicts in at least:

```text
AGENTS.md
tests/repository/test_repository_policy.py
tools/check_repository.py
```

Recheck the actual merge result rather than assuming that list is exhaustive.

## Allowed scope

The normal merge of current `origin/main` may introduce all already-reviewed
mainline governance commits. Manual resolution or new content is limited to:

```text
AGENTS.md
OAP-COMMUNICATION-coding-agent.md
ARCHITECTURE-for-agents.md
oap/strategic-instructions/AGENTS-coding-agent.md
tests/repository/test_repository_policy.py
tools/check_repository.py
oap/active
oap/orders/010-d-reconcile-compact-governance.md
oap/reports/010-d-reconcile-compact-governance.md
```

If another path conflicts, preserve both accepted main and objective-010
semantics with the minimum resolution and identify it explicitly in the report.
Do not make product behavior changes.

## Requirements

1. Fetch and verify the exact main/head/PR state above, then merge
   `origin/main` into the existing objective branch with a normal merge commit.
   Do not rebase or rewrite any existing objective commit.
2. Preserve every activated `010-a` through `010-c` order/report byte-for-byte
   and retain all accepted installation/setup/local-identity behavior and tests.
3. Resolve `AGENTS.md` to the compact current-main coding constitution while
   retaining `argon2-cffi==25.1.0` in the exact direct-runtime dependency list.
4. Make `oap/strategic-instructions/AGENTS-coding-agent.md` an exact mirror of
   the resolved root coding constitution, including the Argon2 fact. Preserve
   the strategic constitution archive and all other governance archives from
   main unchanged.
5. Preserve current-main `OAP-COMMUNICATION-coding-agent.md` and
   `ARCHITECTURE-for-agents.md` exactly. Preserve full `ARCHITECTURE.md` bytes
   and source hash; never edit or load it.
6. Resolve `tools/check_repository.py` and
   `tests/repository/test_repository_policy.py` additively: retain every
   objective-010 dependency/migration/identity policy and test, and every
   mainline compact-architecture required-file/source-hash/human-access policy
   and test. Do not delete, weaken, skip, rename away, or duplicate a guard.
7. Ensure repository policy proves the compact architecture is required,
   records the full source hash, defaults live agent-facing references to it,
   and ignores immutable historical OAP orders/reports for that reference rule.
8. Preserve the complete PR #15 product diff and all mainline governance. Add
   no dependency, migration, route, session, cookie, CSRF, UI, Compose, browser,
   site, membership, capability, publication, or adjacent feature work.
9. Commit the merge/resolution and this activated order/active pointer, push the
   existing branch, allow exactly one new GitHub check generation, and publish
   the immutable report as the final report-only `SELF` commit.

## Observable acceptance criteria

1. PR `#15` remains the only objective-010 PR, open/non-draft, based on `main`,
   and becomes mergeable after a normal merge of `c37da1e...`; history is not
   rewritten.
2. Root and archived coding constitutions are byte-identical and contain both
   compact-architecture/human-only-full-access governance and the Argon2 direct
   dependency fact.
3. Compact communication/architecture match main; full architecture remains at
   SHA-256 `813f57c...` and is absent from the diff against main.
4. Both sets of repository policy behavior and regressions pass; no accepted
   objective-010 test or policy disappears.
5. Diff against current main contains objective-010 product/transcript work plus
   only the explicitly authorized dependency-baseline mirror adjustment and
   this round's transcript. No product feature starts.
6. All 20 GitHub checks on the report head are successful, with none missing,
   failed, cancelled, skipped, or pending; no workflow rerun is used.

## Verification required

Run once after conflict resolution:

```bash
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
uv run --frozen ruff check services/backend tests/repository tools migrations
uv run --frozen ruff format --check services/backend tests/repository tools migrations
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
git diff --check
```

Also prove exact constitution mirror hashes, compact governance hashes, full
architecture hash, prior OAP artifact hashes, merge parents, allowed manual
paths, and no conflict markers. Do not run PostgreSQL integration, Compose,
supply-chain/image, Node, or browser suites locally; unchanged GitHub gates
cover them once.

If a required local check or the single CI generation fails, diagnose and
report `PARTIAL` with exact evidence. Do not rerun workflows or begin repeated
fix/check generations in this governance round.

## Documentation and safety

No behavior documentation change is expected. Never expose secrets or use
production resources. Preserve human-only publication, server-owned context,
role separation, fail-safe conflicts, immutable history, and all accepted
security tests. Routine local tooling belongs to the executor VM.

## Required report

Atomically publish exactly:

```text
oap/reports/010-d-reconcile-compact-governance.md
```

Follow protocol 1.2 completely. Include starting/main/head/merge SHAs and merge
parents; every conflict and resolution; exact root/archive/compact/full hashes;
proof that prior orders/reports and product behavior remain; manual/diff paths;
commands/results; all 20 check states; no-rerun/no-new-PR/no-merge confirmation;
literal implementation head; and `Report publication commit: SELF`.

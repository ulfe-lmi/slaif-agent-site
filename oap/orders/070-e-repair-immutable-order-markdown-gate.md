# OAP Work Order — 070-e

## Objective and exact state

Continue Objective 070 on the existing PR #61 solely to repair the required
Markdown gate caused by immutable strategy-authored 070-d prose. Use the
repository's established exact-path, single-rule override mechanism. Preserve
the substantive 070-d implementation unchanged, obtain a fully successful
current-head check matrix, publish the continuation report, and do not merge.

- Numeric objective: `070`; round: `070-e`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #61 on
  `oap/070-immutable-media-store`. Create no new PR.
- Required starting remote head:
  `675609624b71bf8551b7dba36a2010226958cd0d`.
- That head is the report-only 070-d commit; its sole parent is substantive
  implementation head `50f1f95fb39e0d1eeeaef35521d8bc7361262d9c`
  and its sole changed path is
  `oap/reports/070-d-media-cross-worker-publication-race-proof.md`.
- Remote main remains
  `76fee6d3e233a3909b8ab303d7f563216d86e468`.
- PR #61 is open, non-draft, mergeable, and has exactly one failed required
  check: `Markdown`. Every other current report-head check is successful,
  including Python 3.12–3.14, PostgreSQL 14–18, Compose/edge, supply-chain,
  Node, repository policy, Mermaid, dependency review, and CodeQL.
- The Markdown job fails only at
  `oap/orders/070-d-media-cross-worker-publication-race-proof.md:161:1` with
  `MD018/no-missing-space-atx` because the immutable prose line begins with the
  literal issue/PR notation `#61,`.
- The 070-d order and report are immutable. Their current SHA-256 values are:
  order `70c94cff55d7e357aa67bd1a4fd1dd68e403ccc144db341d2ca6224e180a2f9c`;
  report `9bc0d3a2522d567f2011acba8ae2b05053ccbf5500ae7c4d6579bdd248a9192d`.
- Strategic review confirms this is a strategy-artifact/governance failure,
  not an implementation failure. The substantive bounded cross-worker lock,
  pinned staging descriptor, deterministic race/timeout tests, and Media
  contracts require no reimplementation or amendment in this round.
- Repository precedent is Objective 013-m: immutable transcript prose that
  cannot be rewritten is handled by a per-file Markdownlint override disabling
  only the offending rule. The existing `.markdownlint-cli2.jsonc` already
  supports this mechanism.

## Required bounded correction

Add exactly one override entry to `.markdownlint-cli2.jsonc`:

```jsonc
{
  "filter": ["oap/orders/070-d-media-cross-worker-publication-race-proof.md"],
  "config": { "MD018": false },
  "combine": "merge"
}
```

The override must apply only to that exact immutable order path and only to
rule `MD018`. Preserve all other global rules, globs, ignores, overrides, and
repository lint behavior.

## Immutability and non-goals

- Do not edit, rename, delete, replace, regenerate, or reformat any prior order
  or report, especially 070-d. Prove the two SHA-256 values above remain exact.
- Do not add the 070-d path to the broad `ignores` list. Do not disable MD018
  globally or for a directory/glob. Do not weaken the Markdown workflow.
- Do not change `tools/check_repository.py`, repository-policy tests, CI,
  workflow files, product code, Media code/tests/docs, migrations, grants,
  dependencies, locks, Compose, edge configuration, or architecture. If the
  exact override unexpectedly fails an existing policy gate, report the exact
  result rather than expanding scope.
- Do not rerun or rewrite the Media implementation merely because this is a new
  continuation. No refactor, cleanup, hardening, documentation enhancement,
  feature, or adjacent Objective 070 work is authorized.
- Do not create, close, merge, or enable auto-merge on any PR. Strategic alone
  accepts and merges after independent final review.

## Verification

Before committing, run and report:

1. SHA-256 verification of the immutable 070-d order and report before and
   after the config change;
2. Markdownlint over the full repository with the pinned project command,
   proving zero issues and proving the 070-d file is handled only by the exact
   MD018 override;
3. `python -m compileall -q tools tests/repository`;
4. `python -m unittest discover -s tests/repository -p 'test_*.py'`;
5. `python tools/check_repository.py`;
6. `git diff --check` and an exact final diff proving only
   `.markdownlint-cli2.jsonc`, the strategy-authored 070-e order/active
   transcript, and the later 070-e report changed in this round.

Push the non-report correction to the same branch and wait for every fresh
implementation-head GitHub check. All required checks must be successful and
none pending, failed, cancelled, or missing before publishing the report.
Product suites and Compose are expected to run in fresh CI; do not make product
changes in response unless an actual new failure contradicts the verified
strategy-artifact-only diagnosis. If any non-Markdown check fails, inspect and
report it; do not broaden the round without another strategic continuation.

## Acceptance criteria

- The 070-d order/report bytes and hashes remain unchanged.
- `.markdownlint-cli2.jsonc` gains only the exact-path MD018 override above;
  no broad ignore or rule/policy weakening occurs.
- Full-repository Markdownlint reports zero issues.
- Repository policy and its tests pass without source/test modification.
- No substantive implementation, test, documentation, migration, dependency,
  authority, or architecture file changes in 070-e.
- PR #61 remains the sole Objective 070 PR and all fresh required checks on the
  implementation head are successful.

## GitHub workflow and report

Commit/push the exact strategic 070-e order and `oap/active` bytes unchanged on
the existing branch, then commit/push only the exact lint-config correction.
Do not merge.

Publish exactly
`oap/reports/070-e-repair-immutable-order-markdown-gate.md` as one report-only
child with `Report publication commit: SELF`. Its first parent must be the
literal reported implementation-head SHA; verify the remote path, blob, parent,
and PR head before signaling exact FIFO `OK`.

The report must state `COMPLETE|PARTIAL|BLOCKED|FAILED`; PR/base/branch and all
SHAs; exact config diff; before/after immutable hashes; local command results;
all implementation-head GitHub check states; files changed; no product/code/
test/docs/dependency/migration/authority change; no new PR; no merge; and any
remaining blocker. A fresh report-head CI run is expected after publication and
will be independently gated by strategy.

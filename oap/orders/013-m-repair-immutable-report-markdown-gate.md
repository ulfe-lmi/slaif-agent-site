# OAP Work Order — 013-m

## Objective and exact state

Amend PR #25 to repair the sole current-head Markdown failure caused by the
immutable 013-l report's list formatting, then obtain a fully successful
current-head check matrix.

- Numeric objective: `013`; round: `013-m`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Required starting head:
  `b63a0c6ef00e33307c85e03652a672789eaad248`
- 013-l implementation parent:
  `568186c4c3896e34d0a62d4136151b748d03d290`

Verified state: all functional and CI checks except `Markdown` pass. The
Markdown job fails only at
`oap/reports/013-l-diagnose-modal-containment-timeout.md:79`, MD032,
“Lists should be surrounded by blank lines.” The report is immutable; do not
edit or rewrite it.

Fetch/verify exact PR/head. Amend only PR #25; never create a PR, merge, close,
auto-merge, or workflow-rerun.

## Required bounded correction

Add a repository lint configuration exception narrowly scoped to the exact
immutable report path for rule `MD032` only. Do not broaden glob coverage, do
not disable other rules, do not change any prior order/report bytes, and do not
alter product behavior.

## Verification

Run local Markdown lint and prove zero issues. Run focused Node/shell/
packaging/repository gates if their inputs changed (this correction should
change only lint configuration and OAP transcript artifacts). Then verify all
20 current-head GitHub checks are successful and none is pending.

## Acceptance and report

Target 15 minutes; hard stop 30 minutes. Publish honest `PARTIAL` at hard stop.
Preserve prior transcript bytes and atomically publish:

```text
oap/reports/013-m-repair-immutable-report-markdown-gate.md
```

The report-only `SELF` commit must parent the literal implementation SHA.
Report exact config diff/lint evidence/check states/scope/hashes and explicit
no-new-PR/no-rerun/no-merge confirmations. Signal FIFO `OK` only after report
and claimed remote state exist.

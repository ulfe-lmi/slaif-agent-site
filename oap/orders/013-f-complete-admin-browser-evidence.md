# OAP Work Order — 013-f

## Objective and exact state

Amend objective-013 PR #25 to correct the governance role-option selector from
the nonexistent `Site Architect` label to the actual stable catalog label
`Architect`, then complete the entire governance, six-device, crafted-negative,
privacy/CSP, and restart evidence that 013-e could not reach.

- Numeric objective: `013`; round: `013-f`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `b289afe048c5d28888979066f4aad9ae3d599155`
- 013-e implementation parent:
  `8623450a3de52d4cc2f89630c9ab124e287e4475`
- Verified failure: current implementation-head CI is 19/20; only Compose and
  edge packaging failed at `tests/e2e/governance.spec.ts:127` because the test
  expected `Site Architect`, while `/roles` intentionally derives and returns
  `Architect`. Six stable projects and later governance/restart checks did not
  run due the dependency failure.

Fetch and verify this exact PR/head. Amend only PR #25; never create another PR,
merge, close, auto-merge, or workflow-rerun.

## Scope and requirements

Start by changing only the affected selector/expectation to the exact stable
runtime label `Architect`; do not change the catalog, API, role key, product UI
label, or weaken the assertion to a partial/regex match.

Then run the full static/Node gates and one clean Compose generation. The run
must complete—not merely pass the corrected line—and prove:

- setup → governance → all six stable projects in exact dependency order;
- visible site/profile/locale/domain/primary/remove workflows;
- visible membership add/edit/publication allow/deny/deactivate workflows;
- stale conflict, CSRF, self, system scope, ceiling, cross-site/non-member and
  unknown/archived crafted negatives with no state change;
- archive, logout/relogin, keyboard/focus/dialog/320 px/device checks;
- strict CSP, private headers, request ID, no URL/DOM/storage/log/artifact
  credential leakage; and
- stop/start site/domain/membership fingerprints plus all established Render,
  secret, setup, and broken-bootstrap gates.

If this full run exposes a new concrete synchronization, selector, or UI defect
within the already ordered workflow, diagnose and fix the minimum cause rather
than stopping at the first new line. One additional clean local generation and
one corrective pushed generation are allowed. Do not change backend/API/schema/
permissions/dependencies/Compose topology or weaken expected behavior.

Allowed paths are only existing 013-e Playwright/support/reporter/smoke contract
files and minimum diagnosed admin UI/CSS/source tests, plus docs if evidence
wording changes and OAP transcript files. No new feature or dependency.

Run full pnpm lint/format/type/test/build/licenses, shell syntax, packaging/
repository/supply policy, Playwright project list, changed Markdown/report lint,
`git diff --check`, and secret/CSP/storage scans before clean Compose. Do not run
local PostgreSQL matrices, browser-worker/source experiments, images, Mermaid,
or broad SBOM.

## Acceptance and report

Acceptance requires the complete governance flow, all six stable projects,
restart/security/privacy/accessibility evidence, and all 20 current-head checks
successful. Target 40 minutes; hard stop 70 minutes. Never workflow-rerun;
publish honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and amend only PR #25. Atomically publish:

```text
oap/reports/013-f-complete-admin-browser-evidence.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
the exact root cause/fix, complete project/workflow/negative/device/restart
matrices, exact commands/timings, all 20 checks, corrections/skips/scope/hashes,
and no-new-PR/no-rerun/no-merge. Signal FIFO `OK` only after report and claimed
remote state exist.

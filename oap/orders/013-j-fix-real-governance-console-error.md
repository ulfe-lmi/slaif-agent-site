# OAP Work Order — 013-j

## Objective and state

Amend PR #25 to diagnose the remaining real same-origin static-source browser
console error in the disposable fake-data governance run, repair its source,
remove temporary diagnostics, and complete governance, six-device, and restart
evidence.

- Numeric objective: `013`; round: `013-j`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Required starting head:
  `630f1e3576fbd8a9f2ab61a286e2d6ce8befa4a3`
- 013-i implementation parent:
  `3eda619b34ef397718ed697dd7ab967307375f3c`
- Verified failure: 19/20 checks succeed; one `same-origin-static` /
  `other-browser-error` remains after full functional governance. It persisted
  after removing the deliberate unknown-authority browser fetch, so it must not
  be allowlisted as that 404. Six stable projects/restart remain blocked.

Fetch/verify the exact PR/head. Amend only PR #25; never create a PR, merge,
close, auto-merge, or workflow-rerun.

## Authorized transient diagnosis

For one disposable local clean run only, temporarily emit the raw console error
source/message to the local terminal so the actual defect can be identified.
Before doing so, confirm the run contains only repository fixtures/fake local
credentials and disable shell tracing. Do not print cookies, setup/session/CSRF/
password values, request/response bodies, storage, DOM, headers, database
locators, or stacks. If the message unexpectedly contains credential-like data,
stop, redact, and report without publishing it.

The raw diagnostic must never be committed, pushed, placed in the OAP report,
CI annotation, screenshot/trace/video, or retained file. Remove it before the
implementation commit and keep the fixed-vocabulary durable reporter/contracts.

Repair the concrete application/UI/test source of the error. Do not suppress,
allowlist, downgrade, or broadly match a real console error. Add a focused
regression contract for the diagnosed defect where practical.

Then run a fresh clean generation proving governance, all six stable projects,
accessibility/privacy/CSP, archive/relogin, and stop/start fingerprints plus all
established gates. Up to two clean generations and one corrective pushed
generation are allowed after diagnosis. No backend/API/schema/permission/
dependency/Compose topology/product feature change unless the diagnosed UI
defect itself requires a minimum existing-surface fix.

Allowed paths: existing admin UI/source tests and 013-e–i E2E observer/reporter/
governance/support/smoke contracts, plus OAP artifacts. Run full Node, shell,
packaging/repository/supply, project-list, Markdown/diff/CSP/storage/secret gates.
Do not run local PostgreSQL matrices, browser-worker/source experiments, images,
Mermaid, or broad SBOM.

## Acceptance and report

Target 35 minutes; hard stop 65 minutes. Acceptance requires zero unexpected
console errors, complete governance/six-device/restart evidence, no diagnostic
leak, and all 20 current-head checks successful. Never workflow-rerun or weaken
evidence; publish honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and atomically publish:

```text
oap/reports/013-j-fix-real-governance-console-error.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
only a safe paraphrased root cause/fix, confirmation temporary raw diagnostics
were removed/not retained, complete matrices/commands/timings/checks/scope/
hashes, and no-new-PR/no-rerun/no-merge. Signal FIFO `OK` only after report and
claimed remote state exist.

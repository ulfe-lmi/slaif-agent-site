# OAP Work Order — 013-l

## Objective and exact state

Amend PR #25 to identify and fix the exact waiting operation inside the shared
CSP-safe modal containment browser helper, then complete all four dialogs,
governance, six stable projects, and restart evidence.

- Numeric objective: `013`; round: `013-l`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Required starting head:
  `7ee2e063b621e4de262e4e704388c0f428ea7c0b`
- 013-k implementation parent:
  `ff3b8797b1b9fdddc02dcb0dd763591de01437d6`
- Verified state: modal primitive/source gates pass, but governance times out
  during the first site-switcher `expectModalContained` call in local and CI;
  safe output does not identify the exact substep. Current CI is 19/20.

Fetch/verify exact PR/head. Amend only PR #25; never create a PR, merge, close,
auto-merge, or workflow-rerun.

## Diagnosis and correction

Add bounded fixed-vocabulary step annotations to the shared helper (for example
`modal-aria-inert`, `tab-forward`, `tab-reverse`, `background-dom-focus`,
`background-pointer`, `escape-cleanup`, `trigger-return`). Emit no selector,
URL, content, UUID, count-derived private data, or raw error. Add contracts for
the exact vocabulary.

Run one clean generation, identify the last completed step, and fix the concrete
test or modal primitive boundary. Preserve all required assertions:

- background inert and `aria-modal`;
- more forward/reverse Tab steps than dialog controls, always inside;
- programmatic and pointer attempts cannot move focus behind;
- Escape closes, inert clears, trigger focus returns;
- successful submit/unmount cleanup; and
- no inline style/CSP error or console suppression.

Use deterministic DOM evaluation rather than Playwright actionability waits for
intentionally inert background elements where appropriate, but do not replace
behavior proof with source-only assertions. Remove diagnostic annotations if no
longer useful, or retain only fixed safe stage labels.

Then run the full setup/governance/four-dialog/six-device/restart smoke and all
established gates. One additional clean generation and one corrective push are
allowed after concrete diagnosis. No backend/API/schema/permission/dependency/
Compose topology/product feature change.

Allowed paths: modal primitive/consumers/source tests and existing E2E/support/
reporter/smoke contracts plus OAP artifacts. Run full Node, shell, packaging/
repository/supply, project-list, Markdown/diff/CSP/storage/secret gates. Do not
run local PostgreSQL matrices, browser-worker/source experiments, images,
Mermaid, or broad SBOM.

## Acceptance and report

Target 30 minutes; hard stop 60 minutes. Acceptance requires exact timeout root
cause, all containment assertions in all four consumers, complete governance/
six-device/restart matrix, and all 20 checks successful. Never workflow-rerun or
weaken evidence; report honest `PARTIAL` at the hard stop.

Preserve transcript bytes and atomically publish:

```text
oap/reports/013-l-diagnose-modal-containment-timeout.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
safe step/root cause/fix, containment and full matrices, commands/timings/checks/
scope/hashes, and no-new-PR/no-rerun/no-merge. Signal FIFO `OK` only after report
and claimed remote state exist.

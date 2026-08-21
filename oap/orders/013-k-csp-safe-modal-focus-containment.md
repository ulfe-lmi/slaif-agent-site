# OAP Work Order — 013-k

## Objective and exact state

Amend PR #25 to restore true modal keyboard/accessibility semantics without
reintroducing Radix's CSP-incompatible runtime body-style mutation, then rerun
the complete governance/six-device/restart matrix.

- Numeric objective: `013`; round: `013-k`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Required starting head:
  `497f08142f2e7bdc83866c1028b2c98af1ae57a8`
- 013-j implementation parent:
  `27e98331b0172b25cfda9cd0d192ce0dc74e335d`
- Verified implementation evidence: all 20 checks and the full functional/
  six-device/restart matrix pass. Strategic gap: all four full-screen Radix
  dialogs use `modal={false}` to satisfy strict CSP. Radix then does not trap
  focus or hide/inert outside content; current tests press Tab only once and do
  not prove focus cannot escape behind the dialog.

Fetch/verify exact PR/head. Amend only PR #25; never create a PR, merge, close,
auto-merge, or workflow-rerun.

## Required CSP-safe modal primitive

Create one product-owned reusable wrapper/hook around the existing non-modal
Radix Dialog behavior and use it for all four administration dialogs. Without
inline style or a new dependency it must:

- expose correct labelled `role=dialog` and `aria-modal=true` semantics;
- move initial focus into the open dialog;
- make the administration background inert while open and restore its exact
  prior inert state on close/unmount/error;
- explicitly contain forward Tab from the last focusable control to the first
  and Shift-Tab from first to last, including a safe fallback when no focusable
  child exists;
- keep pointer interaction behind the overlay unavailable;
- close on Escape and return focus to the exact trigger;
- support nested route/unmount cleanup without leaving the page inert; and
- preserve strict CSP with no runtime `style` mutation, unsafe-inline/eval,
  raw HTML, or broad console suppression.

Use stable semantic selectors/root ownership, not arbitrary global element
mutation. Preserve all site switcher, edit, deactivate, archive content/actions
and Radix Dialog dependency. No new package.

## Executable evidence

Add source/unit contracts for the single reusable implementation and all four
consumers. In Playwright, for site switcher and each governance dialog:

- assert background root is inert and dialog is aria-modal while open;
- repeatedly Tab through more steps than the number of dialog controls and
  prove focus always remains inside;
- repeatedly Shift-Tab across the reverse boundary;
- prove background controls cannot receive programmatic/user focus while inert;
- Escape closes, inert is removed, and trigger regains focus;
- successful submit/route change also removes inert and leaves the page usable;
  and
- zero unexpected console errors under strict CSP.

Run the entire setup → governance → six stable projects → restart smoke path and
all established privacy/security/fingerprint gates. One additional clean
generation and one corrective push are allowed after a concrete diagnosis.

Allowed paths: one new/existing admin UI primitive, four existing dialog
consumers, source tests, existing E2E/support/smoke contracts, docs if semantics
need correction, and OAP artifacts. No backend/API/schema/permission/dependency/
Compose topology/product feature change.

Run full Node, shell, packaging/repository/supply, project-list, Markdown/diff/
CSP/storage/secret gates before Compose. Do not run local PostgreSQL matrices,
browser-worker/source experiments, images, Mermaid, or broad SBOM.

## Acceptance and report

Target 40 minutes; hard stop 70 minutes. Acceptance requires modal focus/inert
semantics in all relevant browsers, full governance/six-device/restart evidence,
and all 20 current-head checks successful. Never workflow-rerun or weaken tests;
publish honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and atomically publish:

```text
oap/reports/013-k-csp-safe-modal-focus-containment.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
primitive semantics, four-consumer and browser focus matrices, full project/
restart evidence, commands/timings/checks/scope/hashes, and no-new-PR/no-rerun/
no-merge. Signal FIFO `OK` only after report and claimed remote state exist.

# OAP Work Order — 013-g

## Objective and exact state

Amend PR #25 to fix the final archive-dialog Playwright sequencing defect and
complete every still-unproven objective-013 browser/restart gate.

- Numeric objective: `013`; round: `013-g`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `f8d8604866890158404937b8825a9a588a7db2ed`
- 013-f implementation parent:
  `b8eebca7851c93e10b5aec3f5d194d70878524d3`
- Verified failure: 19/20 checks succeed; Compose alone fails at governance
  line 364 because the test seeks page-level `Site archived. Routing is
  disabled.` while the successful archive modal still correctly hides outside
  content. Archive response, later six projects, and restart were not completed.

Fetch/verify the exact PR/head. Amend only PR #25; never create a PR, merge,
close, auto-merge, or workflow-rerun.

## Required fix and proof

In the existing governance spec, synchronize the exact archive POST response,
assert its expected success status and private headers, then close or await
unmount of the archive dialog before asserting the exact page-level archived
notice. Preserve the visible UI action, named confirmation, recent-auth gate,
Escape/focus tests, catalog/API/product behavior, and exact notice; do not weaken
to a partial selector, hide the modal, or change the UI merely for the test.

Then complete one full clean Compose generation proving:

- archive state, disabled routing, safe unknown/archived navigation;
- logout/relogin;
- all six stable desktop/tablet/mobile projects and their H1/landmark/skip-link/
  focus/target/overflow/reduced-motion checks;
- strict CSP/private headers/request IDs and no URL/DOM/storage/log/artifact
  credential leakage; and
- stop/start site/domain/membership fingerprints plus all established setup,
  Render, secret, and broken-bootstrap gates.

If the full run reveals one new concrete synchronization/selector defect in the
already ordered flow, apply the minimum correction and use at most one further
clean generation/one corrective pushed generation. No backend/API/schema/
permission/dependency/Compose topology or new feature.

Allowed paths: existing 013-e/f governance/support/reporter/auth/setup/smoke
contract files and minimum diagnosed admin UI/CSS/source test only, plus OAP
artifacts. Run full Node, shell, packaging/repository/supply, project-list,
Markdown, diff, CSP/storage/secret scans before Compose. Do not run local
PostgreSQL matrices, browser-worker/source experiments, images, Mermaid, or
broad SBOM.

## Acceptance and report

Acceptance requires complete governance, all six stable projects, archive/
relogin/restart/privacy/accessibility evidence, and all 20 current-head checks
successful. Target 35 minutes; hard stop 60 minutes. Never workflow-rerun or
weaken tests; publish honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and atomically publish:

```text
oap/reports/013-g-close-archive-browser-evidence.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
exact response/modal fix, full project/workflow/device/restart matrices,
commands/timings/checks/corrections/skips/scope/hashes, and no-new-PR/no-rerun/
no-merge. Signal FIFO `OK` only after report and claimed remote state exist.

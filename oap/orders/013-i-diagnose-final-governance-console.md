# OAP Work Order — 013-i

## Objective and exact state

Amend PR #25 to safely classify and diagnose the sole final governance console
event, then narrowly match it only if it is caused by the already asserted
deliberate unknown-authority 404—or repair its concrete source otherwise—and
complete governance, six-device, and restart evidence.

- Numeric objective: `013`; round: `013-i`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `7aaf9844ea3a16e2c6d6bd8eaeda3734ee735ac6`
- 013-h implementation parent:
  `6ad41f0532de9a76d4e13a113d77a76d1bd866fa`
- Verified state: 19/20 checks successful; Compose fails only with one
  `governance-console` category after all functional governance actions. The
  exact expected authority response 404 is correctly allowlisted, but the
  console event does not match the current exact URL+text predicate. Six stable
  projects and restart remain blocked.

Fetch/verify exact PR/head. Amend only PR #25; never create a PR, merge, close,
auto-merge, or workflow-rerun.

## Safe diagnosis and correction

Extend the existing safe reporter/observer with bounded enumerated diagnostics
for unexpected console events—never raw message text, full URL, query, UUID,
credential, stack, DOM, or payload. Useful classes may include source origin
class (`empty`, same-origin Control, same-origin page/static, other) and message
class (`failed-resource-404`, other browser error), plus count. Add unit/source
contracts proving only the fixed vocabulary can be emitted.

Run one clean generation to identify the class. Then:

- if it is Chromium's failed-resource console event caused by the exact fixed
  unknown-authority request whose 404/status/private headers are independently
  asserted, add the narrowest predicate using the proven source/message classes
  and exact request correlation available; do not admit other 404s/errors;
- otherwise repair the actual UI/test source and keep it unexpected.

Do not broadly ignore console errors, empty-source errors, 404s, Control routes,
or arbitrary same-origin events. Preserve the final empty observation assertion.

Complete a fresh clean run proving governance, all six stable device projects,
accessibility/privacy/CSP, archive/relogin, and stop/start fingerprints plus all
established gates. One additional clean generation and one corrective pushed
generation are allowed after concrete diagnosis.

Allowed paths: existing E2E observer/reporter/governance/support/smoke contracts
and minimum diagnosed admin UI source/test, plus OAP artifacts. No backend/API/
schema/permission/dependency/Compose topology/product feature change. Run full
Node, shell, packaging/repository/supply, project-list, Markdown/diff/CSP/
storage/secret gates. Do not run local PostgreSQL matrices, browser-worker/
source experiments, images, Mermaid, or broad SBOM.

## Acceptance and report

Target 35 minutes; hard stop 65 minutes. Acceptance requires a specifically
explained console disposition, complete governance and six-device/restart
matrix, and all 20 current-head checks successful. Never workflow-rerun or
weaken evidence; report honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and atomically publish:

```text
oap/reports/013-i-diagnose-final-governance-console.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
safe diagnostic vocabulary/result, exact correction predicate or source fix,
complete matrices/commands/timings/checks/corrections/skips/scope/hashes, and
no-new-PR/no-rerun/no-merge. Signal FIFO `OK` only after report and claimed
remote state exist.

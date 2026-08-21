# OAP Work Order — 013-h

## Objective and exact state

Amend PR #25 to classify the deliberate unknown-site `my-authority` 404 as the
exact expected negative it is, then complete clean governance, all six stable
browser/device projects, and stop/start persistence.

- Numeric objective: `013`; round: `013-h`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `153cb9db2cf513aa4ec19d0d98214c49d5fc1d1f`
- 013-g implementation parent:
  `151aa76e84cf29b203a1609e45c0d7cd2b2d7526`
- Verified failure: 19/20 checks succeed; governance completes all functional
  actions but final observation records the intentional unknown-site
  `/api/control/v1/sites/{uuid}/my-authority` 404 and corresponding browser
  failed-resource console event because that exact route is absent from the
  expected-failure matcher. Dependants/restart therefore do not run.

Fetch/verify the exact PR/head. Amend only PR #25; never create a PR, merge,
close, auto-merge, or workflow-rerun.

## Required change and proof

Add only the exact anchored unknown-site `my-authority` URL pattern used by the
governance negative to its observation allowlist. It must match that intentional
request only—not arbitrary Control 404s, site paths, console failures, or
network errors. Preserve the request, expected 404/private-header assertions,
and final clean-observation requirement.

Run the entire setup → governance → six stable projects → restart smoke path.
Acceptance requires:

- governance observation set empty except explicitly matched negatives;
- desktop Chromium/Firefox/WebKit, tablet, mobile Chromium/WebKit all pass
  read-only admin login/navigation/site/settings/membership/logout checks;
- H1/landmarks/skip link/focus/44 px/320 px/reduced-motion assertions pass;
- strict CSP/private headers/request IDs and secret/storage/privacy checks pass;
- archive/relogin/unknown/archived navigation pass; and
- stop/start site/domain/membership fingerprints and all established Render,
  setup, secret, and broken-bootstrap gates pass.

If one new concrete synchronization/selector defect appears later in this
already ordered path, fix only that cause and use at most one additional clean
generation/one corrective push. No backend/API/schema/permission/dependency/
Compose topology/product feature change or broad allowlist.

Allowed files are existing 013-e–g E2E/support/reporter/smoke contracts and
minimum diagnosed admin UI source/test, plus OAP artifacts. Run full Node,
shell, packaging/repository/supply, project-list, Markdown, diff, CSP/storage/
secret gates before Compose. Do not run local PostgreSQL matrices,
browser-worker/source experiments, images, Mermaid, or broad SBOM.

## Acceptance and report

Target 30 minutes; hard stop 55 minutes. Acceptance requires the full matrix and
all 20 current-head checks successful. Never workflow-rerun or weaken evidence;
publish honest `PARTIAL` at the hard stop.

Preserve prior transcript bytes and atomically publish:

```text
oap/reports/013-h-complete-device-restart-evidence.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
the exact matcher, complete project/device/governance/restart matrices,
commands/timings/checks/corrections/skips/scope/hashes, and no-new-PR/no-rerun/
no-merge. Signal FIFO `OK` only after report and claimed remote state exist.

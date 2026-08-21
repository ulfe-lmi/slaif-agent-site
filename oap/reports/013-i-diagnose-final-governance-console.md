# OAP Coding-Agent Report — 013-i

## Work order

- Identifier: `013-i`
- Work-order file: `oap/orders/013-i-diagnose-final-governance-console.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented fixed-vocabulary console diagnostics with executable leakage
contracts. The first clean generation classified the sole event as
`same-origin-page-static` / `other-browser-error`; a refined vocabulary then
proved `same-origin-static` / `other-browser-error`. It was therefore not safely
classifiable as Chromium's standard failed-resource event.

Repaired the suspected source instead of suppressing it: unknown site selection
now uses the already server-filtered authorized-site list and does not issue the
doomed browser authority fetch. The test independently asserts the exact unknown
authority `404` and private headers. The corrective GitHub generation still
reported the identical `same-origin-static` / `other-browser-error`, proving it
is not caused solely by that deliberate fetch. No broad exception, further push,
or workflow rerun was made after the order's budget was exhausted. Current-head
CI is 19/20 successful; acceptance is incomplete.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `7aaf9844ea3a16e2c6d6bd8eaeda3734ee735ac6`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `3eda619b34ef397718ed697dd7ab967307375f3c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  - `3eda619b34ef397718ed697dd7ab967307375f3c`
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Changes made

- Added dependency-free source and message classifiers emitting fixed labels
  only; raw URL, query, UUID, message, credential, stack, DOM, and payload data
  cannot enter the stage annotation.
- Added executable contracts covering every vocabulary member and malicious
  URL/message examples containing private-looking data.
- Kept all console errors unexpected; removed 013-h's unused optional exact
  console exception interface and matcher.
- Changed `AdminShell` to call `loadAuthority` only when the selected UUID is in
  the server-filtered authorized-site list; absent sites receive the same safe
  unavailable state without a doomed browser API request.
- Added an explicit request-context assertion that the fixed unknown
  `my-authority` request returns `404` with private/no-store/noindex/request-ID
  headers before visible unknown-site navigation.
- Added a source contract for the authorized-site membership check.

## Safe diagnostic vocabulary and results

Final source vocabulary:

- `empty`
- `same-origin-control`
- `same-origin-admin-site`
- `same-origin-static`
- `same-origin-page-other`
- `other`

Final message vocabulary:

- `failed-resource-404`
- `failed-resource-other`
- `uncaught`
- `other-browser-error`

Results:

| Generation | Safe result |
| --- | --- |
| Local diagnostic 1 | `same-origin-page-static` / `other-browser-error` |
| Local diagnostic 2 | `same-origin-static` / `other-browser-error` |
| Corrective GitHub | `same-origin-static` / `other-browser-error` |

No raw diagnostic value was emitted. The corrective result persisted after the
unknown authority browser fetch was removed, so no exception was justified.

## Files changed

- `apps/web/src/admin/shell.tsx`
- `apps/web/tests/surface.test.mjs`
- `oap/active`
- `oap/orders/013-i-diagnose-final-governance-console.md`
- `tests/contracts/e2e-observation.test.ts`
- `tests/e2e/governance.spec.ts`
- `tests/e2e/observation.ts`
- `tests/e2e/support.ts`
- `oap/reports/013-i-diagnose-final-governance-console.md` (report only)

## Acceptance-criteria evidence

### Project/device matrix

| Project | Local result | GitHub result |
| --- | --- | --- |
| `setup` | PASSED in both clean generations | PASSED |
| `governance` | FAILED at final safe console class | FAILED at final safe console class |
| `desktop-chromium` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `desktop-firefox` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `desktop-webkit` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `tablet` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `mobile-chromium` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `mobile-webkit` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |

The static project list passed with exactly setup, governance, and the six stable
browser/device names in required dependency order.

### Governance and security matrix

| Evidence | Result |
| --- | --- |
| Functional governance actions | Reached before final observation |
| Archive/relogin/archived/unknown navigation | Reached before final observation |
| Unknown authority `404` and private headers | Independently asserted |
| Raw diagnostic leakage | NONE; fixed labels only, contracts passed |
| Broad console/404/network suppression | NOT ADDED |
| Final page/response/network cleanliness | No category reported |
| Final console cleanliness | FAILED with one safe classified category |
| Six-device accessibility/responsive/privacy/CSP | NOT RUN |
| Stop/start persistence and established restart gates | NOT RUN |

## Local verification

- `pnpm install --frozen-lockfile`: PASSED — pnpm `11.22.0`, unchanged.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: initially FAILED because the DOM-free contract project
  imported Playwright support; diagnosed and corrected by extracting the pure
  classifier module. Full reruns then PASSED.
- `pnpm test`: PASSED — web 8/8, browser worker 1/1, contracts 4/4.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED with non-empty `/tmp` output only.
- Ruff check and format gates: PASSED — 141 formatted files.
- Repository tests: PASSED — 53 tests.
- Packaging tests: PASSED — 33 tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python tools/check_repository.py`: PASSED.
- `python -m tools.supply_chain.policy validate`: PASSED.
- `bash -n tools/compose/e2e.sh tools/compose/smoke.sh`: PASSED.
- `pnpm exec playwright test --list`: PASSED — exact eight-project topology.
- Order-only Markdown lint: PASSED — 0 issues.
- `git diff --check`: PASSED.
- Targeted CSP/storage/secret/diagnostic scans: PASSED; no secret literal was
  introduced and established checks remain present.
- `sudo tools/compose/smoke.sh slaif010i` clean generation 1: FAILED — setup
  passed; governance safe result was
  `same-origin-page-static-other-browser-error`; cleanup ran.
- Focused classifier lint/typecheck/contracts: PASSED after refinement.
- `sudo tools/compose/smoke.sh slaif010i` clean generation 2: FAILED — setup
  passed; governance safe result was
  `same-origin-static-other-browser-error`; cleanup ran.
- Full Node and static gates were rerun after the final source repair and PASSED.
- Further local generation: NOT RUN — additional-generation budget exhausted.
- Local PostgreSQL matrices, browser-worker/source experiments, images,
  Mermaid, and broad SBOM: NOT RUN as prohibited by the order.

## GitHub CI / required checks

Observed for implementation head
`3eda619b34ef397718ed697dd7ab967307375f3c`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 40s |
| Analyze (javascript-typescript) | SUCCESS | 53s |
| Analyze (python) | SUCCESS | 51s |
| CodeQL | SUCCESS | 3s |
| Compose and edge packaging | FAILURE | 2m40s; final safe console class at line 399 |
| Dependency review | SUCCESS | 16s |
| Detect supported languages | SUCCESS | 6s |
| Foundation PostgreSQL 14 | SUCCESS | 1m39s |
| Foundation PostgreSQL 15 | SUCCESS | 2m30s |
| Foundation PostgreSQL 16 | SUCCESS | 1m41s |
| Foundation PostgreSQL 17 | SUCCESS | 1m41s |
| Foundation PostgreSQL 18 | SUCCESS | 1m46s |
| Markdown | SUCCESS | 7s |
| Mermaid | SUCCESS | 1m4s |
| Node contracts | SUCCESS | 1m13s |
| Python 3.12 quality and package | SUCCESS | 26s |
| Python 3.13 quality and package | SUCCESS | 32s |
| Python 3.14 quality and package | SUCCESS | 36s |
| Repository policy | SUCCESS | 7s |
| Supply-chain evidence | SUCCESS | 6m10s; evidence uploaded |

- Result: 19/20 successful, 1/20 failed, none pending/missing/cancelled.
- All required checks green at report drafting: no.
- No workflow rerun occurred; the corrective implementation push generated one
  fresh automatic CI and CodeQL generation.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used existing qualified Node/pnpm/uv toolchains and passwordless `sudo` for
  disposable Compose resources.
- No package, production dependency, lockfile, browser, image, service, network,
  volume, or durable host configuration was added.
- Harness cleanup ran after both clean local generations. No screenshot, trace,
  video, raw URL, raw console text, or secret-bearing artifact was retained.

## Documentation

- No durable product documentation change was required; behavior remains the
  same safe unavailable state for unknown sites.
- No certification or broader readiness claim was added.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets, systems, or data accessed: no.
- Required tests skipped/not run: yes — six stable projects and restart proof
  were blocked by governance.
- Backend/API/schema/migration/permission/dependency/Compose changes: no.
- Broad allowlist, empty-source suppression, or weakened assertion: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `32f637800d2d8e5bb55b7d906af80e504a2b7db7c80ec9f64d31e36586e86470`
  - work order: `dce1858e4eb3dffbc9c774615f1813477a7ba54133c774ba3ceb1277e18bae73`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- One same-origin static-source, non-failed-resource, non-uncaught browser error
  remains at the final governance observation.
- Its raw content remains intentionally undisclosed, and it persisted after the
  deliberate unknown authority browser fetch was removed.
- Six stable browser/device projects and stop/start persistence remain unproven.
- Current-head GitHub CI is not green; Compose and edge packaging failed.
- Acceptance remains unmet, so this report is `PARTIAL`.

## Recommended strategic follow-up

Activate a continuation only if strategy chooses: extend the fixed message
taxonomy with bounded semantic classes for likely framework, accessibility, and
application errors without emitting content, then identify and repair the actual
same-origin static-source error. Do not correlate it to the authority 404 unless
new evidence proves that relation. Run a fresh clean/current-head generation for
governance, all six stable projects, and restart. Coding does not select or
activate that continuation.

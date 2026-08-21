# OAP Coding-Agent Report — 013-f

## Work order

- Identifier: `013-f`
- Work-order file: `oap/orders/013-f-complete-admin-browser-evidence.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Corrected the exact role option expectation from nonexistent `Site Architect`
to stable runtime label `Architect`. Two bounded clean local generations then
exposed and diagnosed Radix modal accessibility sequencing: successful
membership PATCH responses completed while the open modal correctly hid the
page-level live region. The three membership edit/conflict flows now await exact
PATCH status/private headers, close the modal, and then assert the exact visible
notice.

The corrective GitHub generation proved setup and the governance workflow
through site/domain, membership add/edit/allow/deny, stale conflict, crafted
negatives, cross-site membership, deactivation, and privacy/CSP checks. It then
failed at the same sequencing pattern in the archive dialog: the test sought the
page-level archive notice while that modal remained open. The order's one
additional local generation and one corrective pushed generation were exhausted,
so no further implementation push or workflow rerun was made. Current-head CI is
19/20 successful; acceptance is not complete.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `b289afe048c5d28888979066f4aad9ae3d599155`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `b8eebca7851c93e10b5aec3f5d194d70878524d3`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  - `b8eebca7851c93e10b5aec3f5d194d70878524d3`
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Changes made

- Changed only the ordered role option expectation to exact accessible name
  `Architect`; the catalog, role key, API, and UI label are unchanged.
- Added exact PATCH response synchronization and `200` plus private-header
  assertions for publication grant/deny membership edits.
- Added exact PATCH response synchronization and `409` plus private-header
  assertions for the stale-version conflict.
- Moved exact membership success/conflict live-region assertions after closing
  their Radix edit dialog so outside content is no longer correctly hidden.
- Generalized the existing private-header helper to accept both Playwright
  browser `Response` and request-context `APIResponse` without changing its
  assertions.

## Files changed

- `oap/active`
- `oap/orders/013-f-complete-admin-browser-evidence.md`
- `tests/e2e/governance.spec.ts`
- `tests/e2e/support.ts`
- `oap/reports/013-f-complete-admin-browser-evidence.md` (report only)

## Acceptance-criteria evidence

### Project/device matrix

| Project | Local result | GitHub result |
| --- | --- | --- |
| `setup` | PASSED in both clean generations | PASSED |
| `governance` | FAILED at membership modal notice | FAILED later at archive modal notice |
| `desktop-chromium` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `desktop-firefox` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `desktop-webkit` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `tablet` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `mobile-chromium` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `mobile-webkit` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |

The static project list passed with exactly setup, governance, and the six stable
browser/device names in the required dependency order.

### Governance workflow matrix

| Workflow | Current-head evidence |
| --- | --- |
| Dashboard/setup | PASSED through visible controls |
| Site create/profile/locale | PASSED before the reported failure |
| Domain add/primary replace/remove/routes | PASSED before the reported failure |
| Membership catalog/add/edit role/ceiling | PASSED before the reported failure |
| Publication allow and deny | PASSED with exact PATCH `200` and private headers |
| Stale-version conflict/recovery | PASSED with exact PATCH `409` and private headers |
| CSRF/self/system/ceiling/unknown/cross-site negatives | PASSED before the reported failure |
| Cross-site fixture membership | PASSED before the reported failure |
| Semantic deactivation | PASSED before the reported failure |
| Archive dialog keyboard/Escape | Reached; FAILED asserting outside live region while modal remained open |
| Logout/relogin after archive | NOT RUN because archive stage failed |
| Stop/start persistence | NOT RUN because browser stage failed before restart |

### Security/privacy/accessibility/restart matrix

| Evidence | Result |
| --- | --- |
| Exact request ID, strict CSP, private/no-store/noindex | PASSED before archive failure |
| No unsafe-inline/eval or remote CSP origin | PASSED before archive failure |
| Empty browser storage and no secret in URL/DOM/request URLs | PASSED before archive failure |
| Membership negative state preservation | PASSED before archive failure |
| Archive dialog keyboard focus/Escape return | PASSED before final archive action |
| Six-device H1/landmark/focus/44 px/320 px/reduced motion | NOT RUN; dependency failed |
| Unknown/archived navigation after archive | NOT RUN after archive notice failure |
| Restart site/domain/membership fingerprints | NOT RUN; restart stage not reached |

### Exact root causes and corrections

- 013-e root cause: runtime catalog derives `SITE_ARCHITECT` label as
  `Architect`; changed the exact expected accessible name accordingly.
- Local generation 1 reached a successful membership update but failed seeking
  the page-level live region while the edit modal remained open.
- Local generation 2 added response evidence and proved the PATCH returned
  `200` with exact private headers; the notice remained inaccessible because
  Radix correctly hides outside content for an open modal.
- Corrected all three membership edit/conflict sequences by awaiting the exact
  response, closing the dialog, then asserting the exact notice.
- GitHub advanced through all those flows and failed at the analogous archive
  ordering at `tests/e2e/governance.spec.ts:364`: the page-level archive notice
  was sought before the archive dialog closed/unmounted.

## Local verification

- `pnpm install --frozen-lockfile`: PASSED — pnpm `11.22.0`, no changes.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 8/8, browser worker 1/1, contracts 2/2.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED; non-empty output retained only under
  `/tmp`.
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED — 141 files.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  53 tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED —
  33 tests.
- `python tools/check_repository.py`: PASSED.
- `python -m tools.supply_chain.policy validate`: PASSED.
- `bash -n tools/compose/e2e.sh tools/compose/smoke.sh`: PASSED.
- `pnpm exec playwright test --list`: PASSED — exact eight-project topology.
- `npx --yes markdownlint-cli2@0.23.2 --no-globs oap/orders/013-f-complete-admin-browser-evidence.md`: PASSED — 0 issues.
- `git diff --check`: PASSED.
- Targeted secret/CSP/storage scans: PASSED — no credential pattern found;
  exact CSP/storage/secret assertions present.
- `sudo tools/compose/smoke.sh slaif013f`: NOT A GENERATION — rejected before
  resource creation by the project-name allowlist.
- `sudo tools/compose/smoke.sh slaif010f` clean generation 1: FAILED — setup
  passed; governance failed at membership update notice line 152; cleanup ran.
- `pnpm exec tsc --project tests/e2e/tsconfig.json --noEmit`: PASSED after adding
  browser-response synchronization.
- `sudo tools/compose/smoke.sh slaif010f` clean generation 2: FAILED — setup
  passed; membership PATCH returned `200` with private headers; outside live
  region remained hidden by open modal at line 160; cleanup ran.
- Further local clean generation: NOT RUN — the one additional generation budget
  was exhausted.

## GitHub CI / required checks

Observed for implementation head
`b8eebca7851c93e10b5aec3f5d194d70878524d3`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 41s |
| Analyze (javascript-typescript) | SUCCESS | 58s |
| Analyze (python) | SUCCESS | 1m0s |
| CodeQL | SUCCESS | 2s |
| Compose and edge packaging | FAILURE | 2m45s; archive dialog/live-region ordering at line 364 |
| Dependency review | SUCCESS | 17s |
| Detect supported languages | SUCCESS | 6s |
| Foundation PostgreSQL 14 | SUCCESS | 1m53s |
| Foundation PostgreSQL 15 | SUCCESS | 1m37s |
| Foundation PostgreSQL 16 | SUCCESS | 1m45s |
| Foundation PostgreSQL 17 | SUCCESS | 1m46s |
| Foundation PostgreSQL 18 | SUCCESS | 1m37s |
| Markdown | SUCCESS | 7s |
| Mermaid | SUCCESS | 56s |
| Node contracts | SUCCESS | 1m32s |
| Python 3.12 quality and package | SUCCESS | 31s |
| Python 3.13 quality and package | SUCCESS | 30s |
| Python 3.14 quality and package | SUCCESS | 35s |
| Repository policy | SUCCESS | 6s |
| Supply-chain evidence | SUCCESS | artifacts, SBOMs, scans, evidence, and upload completed |

- Result: 19/20 successful, 1/20 failed, none pending/missing/cancelled.
- All required checks green at report drafting: no.
- No workflow rerun occurred; the one corrective implementation push generated
  a fresh automatic run.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing qualified Node/pnpm/uv toolchains and passwordless `sudo` for
  disposable Compose resources.
- No package, production dependency, lockfile, browser, image, service, network,
  volume, or durable host configuration was added.
- Harness cleanup ran after both clean local generations. No local screenshot,
  trace, or video artifact was retained.

## Documentation

- No durable documentation change was required; 013-e documentation already
  describes the intended topology, evidence, and limitations accurately.
- No certification or broader readiness claim was added.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets, systems, or data accessed: no.
- Required tests skipped/not run: yes — six stable projects, post-archive
  navigation, and restart proof were blocked by governance failure.
- Scope deviation: no. The rejected project name created no resources and was
  corrected from the harness's explicit allowlist.
- Backend/API/schema/migration/permission/catalog/dependency/Compose topology
  changes: no.
- Assertions weakened or failures hidden: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `ee00b1845f1935eca2e121f06c433f025b423a7dd26dbfb837904ba66e5a1f24`
  - work order: `f0bf0ac492f7c02164a8720d113daa4177c3a75ef368278aa48cfc4ca0d7a84c`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- The archive confirmation sequence still asserts the outside live region while
  its modal hides outside content. Archive completion, archived/unknown route
  evidence, logout/relogin, all six stable projects, and stop/start persistence
  are therefore not proven on this head.
- Current-head GitHub CI is not green; Compose and edge packaging failed.
- Acceptance remains unmet, so this report is `PARTIAL`.

## Recommended strategic follow-up

Activate a continuation only if strategy chooses: synchronize the exact archive
POST response, close or verify unmount of the archive dialog, then assert the
exact `Site archived. Routing is disabled.` notice. Run one fresh clean
Compose/current-head generation to prove archive, all six stable projects, and
restart persistence. Coding does not select or activate that continuation.

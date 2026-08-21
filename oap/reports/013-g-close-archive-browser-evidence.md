# OAP Coding-Agent Report — 013-g

## Work order

- Identifier: `013-g`
- Work-order file: `oap/orders/013-g-close-archive-browser-evidence.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Closed the archive confirmation sequencing defect by awaiting the exact archive
POST, asserting status and private headers, closing the modal, and then asserting
the exact notice. Navigating back to the overview proved the `ARCHIVED` state,
and waiting for logout navigation removed a relogin race.

The corrective GitHub generation completed the full functional governance flow,
including archive, archived and unknown-site navigation, logout, and relogin. Its
final clean-observation assertion failed because the deliberately unknown site's
expected `/my-authority` 404 was not in the harness allowlist and was recorded as
both a response and console failure. The order's additional local generation and
corrective pushed generation were exhausted, so no further implementation push
or workflow rerun was made. Current-head CI is 19/20 successful; acceptance is
not complete.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `f8d8604866890158404937b8825a9a588a7db2ed`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `151aa76e84cf29b203a1609e45c0d7cd2b2d7526`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  - `151aa76e84cf29b203a1609e45c0d7cd2b2d7526`
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Changes made

- Awaited the exact archive POST and asserted `200` plus private response
  headers before closing the archive modal and checking the exact visible notice.
- Navigated through the visible `Back to overview` control before asserting the
  site's `ARCHIVED` status.
- Waited for the exact `/login` URL after sign-out before beginning relogin.
- Did not change backend behavior, APIs, schemas, migrations, permissions,
  dependencies, catalogs, or Compose topology.

## Files changed

- `oap/active`
- `oap/orders/013-g-close-archive-browser-evidence.md`
- `tests/e2e/governance.spec.ts`
- `oap/reports/013-g-close-archive-browser-evidence.md` (report only)

## Acceptance-criteria evidence

### Project/device matrix

| Project | Local result | GitHub result |
| --- | --- | --- |
| `setup` | PASSED in both clean generations | PASSED |
| `governance` | FAILED after archive at two successively later assertions | FAILED only at final clean-observation assertion |
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
| Dashboard, site, domain, membership, negatives | PASSED before archive |
| Archive POST | PASSED with exact `200` and private headers |
| Archive modal close and exact notice | PASSED |
| Overview archived status | PASSED with exact `ARCHIVED` state |
| Archived public route | PASSED with expected `404` |
| Logout and relogin | PASSED |
| Unknown-site safe navigation | Functional navigation PASSED; expected authority `404` was not observation-allowlisted |
| Final console/response cleanliness | FAILED on that expected `/my-authority` `404` pair |
| Stop/start persistence | NOT RUN because governance dependency failed |

### Security/privacy/accessibility/restart matrix

| Evidence | Result |
| --- | --- |
| Exact request ID, strict CSP, private/no-store/noindex | PASSED through the functional flow |
| Empty storage and no secret in URL/DOM/request URLs | PASSED through the functional flow |
| Archive keyboard focus/Escape return | PASSED |
| Archive response and private headers | PASSED |
| Archived and unknown-site safe navigation | Reached; unknown authority `404` misclassified by harness |
| Six-device H1/landmark/focus/44 px/320 px/reduced motion | NOT RUN; dependency failed |
| Restart site/domain/membership fingerprints | NOT RUN; restart stage not reached |

### Exact root causes and corrections

- Local generation 1 completed archive and notice handling, then expected the
  overview-only `ARCHIVED` badge while still on settings. The test now uses the
  visible overview navigation first.
- Local generation 2 reached logout but raced a pending redirect by immediately
  navigating to login. The test now waits for exact `/login` before relogin.
- The corrective GitHub generation completed all functional governance actions.
  At the final observation assertion, the intentional unknown-site request to
  `/api/control/v1/sites/{unknown}/my-authority` returned `404`; unlike the other
  expected negative URLs, this route was absent from `expectedFailures`, so the
  response and its browser failed-resource console event remained recorded.

## Local verification

- `pnpm install --frozen-lockfile`: PASSED — pnpm `11.22.0`, no changes.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 8/8, browser worker 1/1, contracts 2/2.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED — 141 files.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 53 tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 33 tests.
- `python tools/check_repository.py`: PASSED.
- `python -m tools.supply_chain.policy validate`: PASSED.
- `bash -n tools/compose/e2e.sh tools/compose/smoke.sh`: PASSED.
- `pnpm exec playwright test --list`: PASSED — exact eight-project topology.
- Order-only Markdown lint: PASSED — 0 issues.
- `git diff --check`: PASSED.
- Targeted secret/CSP/storage scans: PASSED.
- `sudo tools/compose/smoke.sh slaif010g` clean generation 1: FAILED — setup
  passed; archive completed; test sought overview `ARCHIVED` state on settings;
  cleanup ran.
- `sudo tools/compose/smoke.sh slaif010g` clean generation 2: FAILED — setup
  passed; archive and overview state passed; logout navigation raced the next
  login navigation; cleanup ran.
- Further local clean generation: NOT RUN — the one additional generation budget
  was exhausted.
- Local Mermaid rendering and broad SBOM build: NOT RUN; authoritative GitHub
  Mermaid and supply-chain jobs both passed on the implementation head.

## GitHub CI / required checks

Observed for implementation head
`151aa76e84cf29b203a1609e45c0d7cd2b2d7526`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 39s |
| Analyze (javascript-typescript) | SUCCESS | 1m4s |
| Analyze (python) | SUCCESS | 52s |
| CodeQL | SUCCESS | 3s |
| Compose and edge packaging | FAILURE | 3m9s; final console/response assertion |
| Dependency review | SUCCESS | 16s |
| Detect supported languages | SUCCESS | 4s |
| Foundation PostgreSQL 14 | SUCCESS | 1m40s |
| Foundation PostgreSQL 15 | SUCCESS | 1m37s |
| Foundation PostgreSQL 16 | SUCCESS | 1m47s |
| Foundation PostgreSQL 17 | SUCCESS | 1m56s |
| Foundation PostgreSQL 18 | SUCCESS | 1m36s |
| Markdown | SUCCESS | 9s |
| Mermaid | SUCCESS | 1m0s |
| Node contracts | SUCCESS | 2m0s |
| Python 3.12 quality and package | SUCCESS | 34s |
| Python 3.13 quality and package | SUCCESS | 34s |
| Python 3.14 quality and package | SUCCESS | 33s |
| Repository policy | SUCCESS | 7s |
| Supply-chain evidence | SUCCESS | 6m32s; evidence uploaded |

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

- No durable documentation change was required; this round changed only test
  synchronization and navigation evidence.
- No certification or broader readiness claim was added.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets, systems, or data accessed: no.
- Required tests skipped/not run: yes — six stable projects and restart proof
  were blocked by the governance final-observation failure.
- Scope deviation: no.
- Assertions weakened or failures hidden: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `3ba6e1a6884b568722c5db9295b237c1e8d15d73ad50b5b3896a076720c54365`
  - work order: `bf06f36fce4510033d8e53f532d8575170a3c3b9ee302b582cf6385c5043a680`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- The expected unknown-site `/my-authority` `404` is not registered as an
  expected negative in the observation harness, leaving one response and one
  failed-resource console record at the final assertion.
- Six stable browser/device projects and stop/start persistence remain unproven
  because governance is their dependency.
- Current-head GitHub CI is not green; Compose and edge packaging failed.
- Acceptance remains unmet, so this report is `PARTIAL`.

## Recommended strategic follow-up

Activate a continuation only if strategy chooses: add the exact unknown-site
`/api/control/v1/sites/{site}/my-authority` negative route to the existing
expected-failure matcher without broadening it, then run a fresh clean Compose
and current-head CI generation to prove a clean governance observation set, all
six stable projects, and restart persistence. Coding does not select or activate
that continuation.

# OAP Coding-Agent Report — 013-h

## Work order

- Identifier: `013-h`
- Work-order file: `oap/orders/013-h-complete-device-restart-evidence.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Added the exact anchored URL matcher for the deliberate fixed-fixture
`my-authority` 404. This removed the unexpected response category, while the
browser still emitted one console error whose source did not match that request
URL. The one allowed additional clean generation confirmed the repository's safe
reporter does not expose raw console source or text.

The corrective implementation added a two-dimensional exception requiring both
the exact fixed unknown-site admin URL and Chromium's exact 404 failed-resource
message. All static gates passed, but the corrective GitHub generation still
failed only with `governance-console`; therefore the console event has a different
source, text, or both. No broad console exception, further push, or workflow
rerun was made after the order's generation budget was exhausted. Current-head
CI is 19/20 successful; acceptance is not complete.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `153cb9db2cf513aa4ec19d0d98214c49d5fc1d1f`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `6ad41f0532de9a76d4e13a113d77a76d1bd866fa`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  - `6ad41f0532de9a76d4e13a113d77a76d1bd866fa`
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Changes made

- Added the anchored expected-response pattern
  `/api/control/v1/sites/12000000-0000-4000-8000-000000000099/my-authority$`.
- Preserved the unknown-site request, its `404` behavior, private-header
  assertions, and the final clean-observation assertion.
- Extended the observer with an optional typed console matcher requiring both
  source and message text.
- Added one such matcher requiring the exact fixed unknown-site admin URL and
  exact Chromium `404 (Not Found)` failed-resource text.
- Did not admit other site UUIDs, Control routes, statuses, console messages,
  page errors, request failures, or network errors.

## Files changed

- `oap/active`
- `oap/orders/013-h-complete-device-restart-evidence.md`
- `tests/e2e/governance.spec.ts`
- `tests/e2e/support.ts`
- `oap/reports/013-h-complete-device-restart-evidence.md` (report only)

## Acceptance-criteria evidence

### Project/device matrix

| Project | Local result | GitHub result |
| --- | --- | --- |
| `setup` | PASSED in both clean generations | PASSED |
| `governance` | FAILED only with `governance-console` | FAILED only with `governance-console` |
| `desktop-chromium` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `desktop-firefox` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `desktop-webkit` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `tablet` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `mobile-chromium` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |
| `mobile-webkit` | NOT RUN; governance dependency failed | NOT RUN; governance dependency failed |

The static project list passed with exactly setup, governance, and the six stable
browser/device names in required dependency order.

### Governance workflow matrix

| Workflow | Current-head evidence |
| --- | --- |
| Setup and clean initial observation | PASSED |
| Dashboard/site/domain/membership workflows | Reached before final observation |
| Archive/relogin/archived navigation | Reached before final observation |
| Unknown-site response classification | Corrected; response category absent |
| Unknown-site visible safe state | Reached before final observation |
| Final response/page/network cleanliness | PASSED; no such category reported |
| Final console cleanliness | FAILED with sole `console` category |
| Six stable projects | NOT RUN due governance dependency |
| Stop/start persistence | NOT RUN due governance dependency |

The safe reporter exposes only project, contract, sanitized stage category, and
line/column. It reported no raw console source or text, so the remaining event
cannot honestly be identified more precisely from this generation.

### Security/privacy/accessibility/restart matrix

| Evidence | Result |
| --- | --- |
| Exact request ID, CSP, private/no-store/noindex | Reached before final observation |
| Storage, URL, DOM, and request-URL secret checks | Reached before final observation |
| Archive/relogin/unknown/archived navigation | Reached before final observation |
| Unknown authority `404` exact response allowlist | PASSED; response category absent |
| Arbitrary console/network suppression | NOT ADDED |
| Six-device H1/landmark/skip/focus/44 px/320 px/reduced motion | NOT RUN |
| Restart fingerprints and established restart gates | NOT RUN |

## Local verification

- `pnpm install --frozen-lockfile`: PASSED — pnpm `11.22.0`, no changes.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 8/8, browser worker 1/1, contracts 2/2.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED with non-empty output under `/tmp` only.
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
- Targeted matcher/CSP/storage/secret scans: PASSED; no literal credential was
  found in the diff and established assertions remain present.
- `sudo tools/compose/smoke.sh slaif010h` clean generation 1: FAILED — setup
  passed; governance completed functional actions; exact unknown authority
  response was accepted but one console category remained; cleanup ran.
- Temporary diagnostic output plus E2E formatting/typecheck: PASSED locally,
  but the safe reporter intentionally emitted only the fixed category.
- `sudo tools/compose/smoke.sh slaif010h` clean generation 2: FAILED — setup
  passed; governance again failed only with `governance-console`; cleanup ran.
- Full Node lint/format/typecheck/test/build was rerun after the final observer
  contract and PASSED.
- Further local generation: NOT RUN — additional-generation budget exhausted.
- Local PostgreSQL matrices, browser-worker/source experiments, images,
  Mermaid, and broad SBOM: NOT RUN as prohibited by the order.

## GitHub CI / required checks

Observed for implementation head
`6ad41f0532de9a76d4e13a113d77a76d1bd866fa`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 34s |
| Analyze (javascript-typescript) | SUCCESS | 1m1s |
| Analyze (python) | SUCCESS | 1m8s |
| CodeQL | SUCCESS | 3s |
| Compose and edge packaging | FAILURE | 7m39s; governance console at line 405 |
| Dependency review | SUCCESS | 21s |
| Detect supported languages | SUCCESS | 5s |
| Foundation PostgreSQL 14 | SUCCESS | 1m35s |
| Foundation PostgreSQL 15 | SUCCESS | 1m37s |
| Foundation PostgreSQL 16 | SUCCESS | 1m36s |
| Foundation PostgreSQL 17 | SUCCESS | 1m47s |
| Foundation PostgreSQL 18 | SUCCESS | 1m35s |
| Markdown | SUCCESS | 7s |
| Mermaid | SUCCESS | 59s |
| Node contracts | SUCCESS | 2m2s |
| Python 3.12 quality and package | SUCCESS | 35s |
| Python 3.13 quality and package | SUCCESS | 33s |
| Python 3.14 quality and package | SUCCESS | 37s |
| Repository policy | SUCCESS | 6s |
| Supply-chain evidence | SUCCESS | 6m23s; evidence uploaded |

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
  video, or raw secret-bearing artifact was retained.

## Documentation

- No durable product documentation change was required; this round changed only
  bounded E2E observation classification.
- No certification or broader readiness claim was added.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets, systems, or data accessed: no.
- Required tests skipped/not run: yes — six stable projects and restart proof
  were blocked by governance.
- Scope deviation: no.
- Backend/API/schema/migration/permission/dependency/Compose changes: no.
- Broad allowlist or weakened final assertion: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `c4155cdad6af44551674c3c66123b8f2eed15e52c6e784555ac9d9588a904334`
  - work order: `916ca63cc3bbc1e8e82be1d86fe36f38dbbc3ea6bf725f531bad8d2c313e6acd`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- One console error remains at the final governance observation. Its raw source
  and message are intentionally absent from the safe reporter output, and the
  exact fixed-page/exact-404 predicate did not match it.
- Six stable browser/device projects and stop/start persistence remain unproven.
- Current-head GitHub CI is not green; Compose and edge packaging failed.
- Acceptance remains unmet, so this report is `PARTIAL`.

## Recommended strategic follow-up

Activate a continuation only if strategy chooses: add a bounded safe diagnostic
classification to the reporter (for example, enumerated source class and message
class without raw URLs or text), identify the remaining console event, then match
only the proven deliberate failure or repair its concrete source. Run one fresh
clean Compose/current-head generation to prove governance, all six stable
projects, and restart. Coding does not select or activate that continuation.

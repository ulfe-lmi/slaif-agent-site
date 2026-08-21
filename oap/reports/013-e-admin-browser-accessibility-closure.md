# OAP Coding-Agent Report — 013-e

## Work order

- Identifier: `013-e`
- Work-order file: `oap/orders/013-e-admin-browser-accessibility-closure.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented the ordered setup/governance/six-device Playwright topology, visible
site/domain/membership/archive governance flow, crafted negative checks,
responsive/keyboard/privacy assertions, restart persistence assertions, concise
markers, packaging contracts, and durable documentation. Browser evidence found
and fixed a real admin response-validation defect: valid READ permissions use
delegation level `0`.

The bounded round did not reach acceptance. Two permitted local clean Compose
generations failed before the six stable projects could run. The corrective
GitHub generation then reached governance but failed because the test expected
role option label `Site Architect`; the runtime catalog intentionally derives
`SITE_ARCHITECT` as `Architect`. The order permitted only one corrective pushed
generation, so no third implementation push or workflow rerun was made. Current
head CI is 19/20 successful; Compose and edge packaging is failed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `e72a8baa39bc4bef1e2d9027d7f0dce3b945db75`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `8623450a3de52d4cc2f89630c9ab124e287e4475`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report:
  - `1b9d10bfac0b214ceec8cf8dd2a83045ebbe1bf6` — implementation
  - `8623450a3de52d4cc2f89630c9ab124e287e4475` — diagnosed Ruff correction
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Changes made

- Added one Chromium `governance` project after `setup`; made the six exact
  stable browser/device projects read-only dependants of governance.
- Split setup initialization from visible governance mutation and added UI-led
  site creation, profile, locale, domain, membership, stale-conflict,
  deactivation, archive, logout/relogin, and safe unknown-route coverage.
- Added server-negative requests for CSRF, self-target, system scope, ceiling,
  unknown/non-member, and cross-site boundaries without using direct API calls
  for normal success workflows.
- Added shared responsive/admin usability, private-header, browser-observation,
  secret, storage, focus, target-size, reduced-motion, and overflow assertions.
- Added domain and governance persistence fingerprints to the stop/start smoke
  path and updated marker/project-order packaging contracts.
- Corrected the admin permission response validator to accept architecturally
  valid READ delegation level `0`, with a static regression assertion.
- Updated administration, testing, security, operations, and README claims and
  limitations without claiming certification.

## Files changed

- `README.md`
- `apps/web/src/admin/api.ts`
- `apps/web/tests/surface.test.mjs`
- `docs/ADMIN.md`
- `docs/OPERATIONS.md`
- `docs/SECURITY.md`
- `docs/TESTING.md`
- `oap/active`
- `oap/orders/013-e-admin-browser-accessibility-closure.md`
- `playwright.config.ts`
- `tests/e2e/auth.spec.ts`
- `tests/e2e/governance.spec.ts`
- `tests/e2e/reporter.mjs`
- `tests/e2e/setup.spec.ts`
- `tests/e2e/support.ts`
- `tests/packaging/test_compose_smoke_contract.py`
- `tools/compose/e2e.sh`
- `tools/compose/smoke.sh`
- `oap/reports/013-e-admin-browser-accessibility-closure.md` (report only)

## Acceptance-criteria evidence

### Project and device matrix

| Project | Intended role | Local result | GitHub result |
| --- | --- | --- | --- |
| `setup` | Desktop/320 setup and initialization | PASSED twice | PASSED |
| `governance` | Single Chromium state writer | FAILED before completion | FAILED at membership catalog label selector |
| `desktop-chromium` | Read-only responsive/admin checks | NOT RUN; dependency failed | NOT RUN; dependency failed |
| `desktop-firefox` | Read-only responsive/admin checks | NOT RUN; dependency failed | NOT RUN; dependency failed |
| `desktop-webkit` | Read-only responsive/admin checks | NOT RUN; dependency failed | NOT RUN; dependency failed |
| `tablet` | Read-only responsive/admin checks | NOT RUN; dependency failed | NOT RUN; dependency failed |
| `mobile-chromium` | Read-only responsive/admin checks | NOT RUN; dependency failed | NOT RUN; dependency failed |
| `mobile-webkit` | Read-only responsive/admin checks | NOT RUN; dependency failed | NOT RUN; dependency failed |

The configured list contains exactly these eight projects and preserves all six
required stable names.

### Governance workflow matrix

| Workflow | Evidence result |
| --- | --- |
| Setup/dashboard | PASSED locally and on GitHub through visible controls |
| Site create/profile/locale | Reached before the reported GitHub failure; no complete-round claim |
| Domain add/primary replace/remove/routes | First local run exposed missing success synchronization; corrected; no complete-round claim |
| Membership catalog/add/edit/allow/deny/deactivate | BLOCKED at catalog option-label assertion before mutation |
| Stale conflict and crafted server negatives | NOT RUN because governance stopped earlier |
| Archive/logout/relogin | NOT RUN because governance stopped earlier |
| Stop/start persistence | NOT RUN because browser stage failed before restart stage |

### Responsive, accessibility, privacy, CSP, and restart matrix

| Evidence | Result |
| --- | --- |
| Source/contract assertions and TypeScript compilation | PASSED |
| One H1, landmarks, skip link, labelled controls, focus, Escape return | IMPLEMENTED; full six-project browser proof NOT RUN |
| 44 px targets, 320 px overflow, reduced motion | IMPLEMENTED; full six-project browser proof NOT RUN |
| Request ID, strict CSP, private/no-store/noindex headers | IMPLEMENTED; complete browser proof NOT RUN |
| URL/DOM/storage/console/network/artifact secret checks | IMPLEMENTED; complete browser proof NOT RUN |
| Direct unknown/non-member/archived safe failures | IMPLEMENTED; complete browser proof NOT RUN |
| Restart site/membership/domain fingerprints | IMPLEMENTED; runtime restart proof NOT RUN |

### Diagnosed defects and corrections

- Local generation 1 failed at broad `domains-visible`; dependent domain actions
  lacked explicit success synchronization. Added exact success waits and
  credential-free granular stages.
- Local generation 2 failed loading membership administration. The frontend
  validator incorrectly rejected valid READ permission delegation level `0`;
  corrected `delegationLevel >= 1` to `>= 0` and added a regression assertion.
- Initial GitHub generation failed all three Python quality jobs because Ruff
  required one packaging expression on a single line. Applied only canonical
  Ruff formatting and pushed the one corrective generation.
- Corrective GitHub generation failed governance at line 127: expected option
  `Site Architect`, actual catalog label `Architect`. This is a diagnosed test
  selector defect. It remains intentionally unfixed because a further pushed
  generation is outside the order's retry budget.

## Local verification

- `node --version`: PASSED — Node `24.14.1`.
- `pnpm --version`: PASSED — pnpm `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 8/8, browser worker 1/1, contracts 2/2.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED; output was non-empty and retained only in
  `/tmp`.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  53 tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED —
  33 tests, including 5 focused Compose smoke contracts.
- `python tools/check_repository.py`: PASSED.
- `python -m tools.supply_chain.policy validate`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED after diagnosed formatting correction.
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations`: PASSED — 141 files formatted.
- `npx --yes markdownlint-cli2@0.23.2 --no-globs README.md docs/ADMIN.md docs/OPERATIONS.md docs/SECURITY.md docs/TESTING.md oap/orders/013-e-admin-browser-accessibility-closure.md`: PASSED — 0 issues.
- `bash -n tools/compose/e2e.sh tools/compose/smoke.sh`: PASSED.
- `pnpm exec playwright test --list`: PASSED — exact eight-project topology.
- `git diff --check`: PASSED.
- `sudo tools/compose/smoke.sh slaif010e` generation 1: FAILED — setup passed;
  governance failed at `domains-visible`. Cleanup passed.
- `sudo tools/compose/smoke.sh slaif010e` generation 2: FAILED — setup passed;
  governance failed at `membership-catalog-visible`; diagnosed delegation-level
  validator defect. Cleanup passed.
- Third local clean Compose generation: NOT RUN — expressly prohibited after the
  two bounded generations.
- `python tools/check_mermaid.py`: FAILED for all diagrams because transient
  Mermaid CLI returned `[object Object]`; a minimal two-node external temporary
  input failed identically while both cached browsers launched independently.
  This command was not requested and was expressly outside local scope; no file
  was changed and no passing claim is made.

## GitHub CI / required checks

Observed for implementation head
`8623450a3de52d4cc2f89630c9ab124e287e4475`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 39s |
| Analyze (javascript-typescript) | SUCCESS | 55s |
| Analyze (python) | SUCCESS | 44s |
| CodeQL | SUCCESS | 3s |
| Compose and edge packaging | FAILURE | 2m41s; governance line 127 option-label selector |
| Dependency review | SUCCESS | 24s |
| Detect supported languages | SUCCESS | 6s |
| Foundation PostgreSQL 14 | SUCCESS | 1m41s |
| Foundation PostgreSQL 15 | SUCCESS | 2m39s |
| Foundation PostgreSQL 16 | SUCCESS | 1m48s |
| Foundation PostgreSQL 17 | SUCCESS | 1m43s |
| Foundation PostgreSQL 18 | SUCCESS | 1m30s |
| Markdown | SUCCESS | 8s |
| Mermaid | SUCCESS | 47s |
| Node contracts | SUCCESS | 1m53s |
| Python 3.12 quality and package | SUCCESS | 40s |
| Python 3.13 quality and package | SUCCESS | 31s |
| Python 3.14 quality and package | SUCCESS | 33s |
| Repository policy | SUCCESS | 9s |
| Supply-chain evidence | SUCCESS | reproducible artifacts/evidence and upload completed |

- Result: 19/20 successful, 1/20 failed, none pending/missing/cancelled.
- All required checks green at report drafting: no.
- No failed workflow was rerun. The corrective commit created a fresh automatic
  current-head generation.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing qualified Node/pnpm/uv toolchains and passwordless `sudo` for
  the disposable local Compose stack.
- No production dependency, lockfile, service, image, network, volume, browser,
  or durable host configuration was added.
- Compose cleanup completed after both local generations. No local Playwright
  screenshots, traces, or videos were retained.

## Documentation

- Updated `README.md` and `docs/ADMIN.md`, `docs/TESTING.md`,
  `docs/SECURITY.md`, and `docs/OPERATIONS.md` with the implemented sequencing,
  workflows, security/privacy checks, device/keyboard intent, restart evidence,
  and honest limitations.
- Documentation does not call automated checks a security or accessibility
  certification and continues to defer identity creation, content/Puck,
  workspace/capability, review, and publication execution.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems or data accessed: no.
- Real external application services accessed: no; GitHub publication/CI only.
- Required tests skipped/not run: yes — governance dependency failure prevented
  six stable projects, later governance checks, and restart proof.
- Scope deviation: yes — `python tools/check_mermaid.py` was run despite the
  order excluding local Mermaid work; it failed transiently and changed nothing.
- New production dependencies or lockfile changes: no.
- Backend/API/schema/migration/role/permission/edge/Compose service changes: no.
- Browser evidence weakened or failure hidden: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with the implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `8e9747f7a92d060c4ef341f0ebfef50faf4a951da6641ae8630bd74797d1ab29`
  - work order: `4c1dfd5d2f9adf135b9f7ba7768b3fafa707773a493d44e7020192294ac9859c`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- Governance stops at the incorrect option-label assertion, so the membership
  mutation/negative/archive sequence, six stable device/browser projects, and
  stop/start persistence evidence are not proven on this head.
- Current-head GitHub CI is not green: Compose and edge packaging failed.
- Acceptance therefore remains unmet and this report is `PARTIAL`.

## Recommended strategic follow-up

Activate a continuation only if strategy chooses: change the governance catalog
assertion from `Site Architect` to the actual stable label `Architect`, then run
one fresh clean Compose/current-head CI generation and close the still-unproven
membership, negative, six-device, privacy/CSP, and restart matrices. Coding does
not select or activate that continuation.

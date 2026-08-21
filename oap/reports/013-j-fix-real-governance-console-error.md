# OAP Coding-Agent Report — 013-j

## Work order

- Identifier: `013-j`
- Work-order file: `oap/orders/013-j-fix-real-governance-console-error.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Diagnosed the remaining same-origin static console error in one authorized,
fixture-only local run. A Radix modal dialog attempted a runtime inline body-style
mutation that the product's strict `style-src 'self'` CSP correctly rejected.
Changed the four existing administration dialogs to Radix non-modal behavior,
while retaining their product-owned full-screen overlays, focus behavior, Escape
closure, and fixed-vocabulary observation contracts. The temporary raw diagnostic
was removed and was never committed, pushed, placed in this report, or retained
as a file or browser artifact.

The first post-diagnosis clean generation proved setup and the full governance
workflow, then exposed latent administration-shell assertions. Settings and
membership pages now use the shared authenticated shell, and the mobile
site-switcher is exposed as administration navigation. A second clean generation
proved governance and all three desktop engines; its later tablet/mobile runs
stalled at the initial unauthenticated redirect. The automatically triggered
current-head GitHub generation then passed setup, governance, all six stable
projects, restart persistence, and the final Compose smoke. All 20 GitHub checks
are successful.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `630f1e3576fbd8a9f2ab61a286e2d6ce8befa4a3`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `27e98331b0172b25cfda9cd0d192ce0dc74e335d`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  - `27e98331b0172b25cfda9cd0d192ce0dc74e335d`
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Changes made

- Set all four existing administration `Dialog.Root` instances to `modal={false}`
  so Radix does not attempt the CSP-incompatible body pointer-style mutation.
- Retained the existing full-screen overlay, dialog semantics, Escape closure,
  trigger focus restoration, and strict final console assertion.
- Wrapped settings and membership workflows in the existing `AdminShell`, so
  those routes retain the authenticated header, navigation, skip link, and
  responsive layout.
- Changed the responsive site-switcher container to a labelled administration
  `nav`, supplying the mobile landmark when the desktop sidebar is hidden.
- Removed nested `main` elements from the membership workflow after placing it
  inside the shared shell's single `main` landmark.
- Added source contracts requiring exactly four CSP-safe dialog roots, shared
  shell ownership for settings/membership routes, and mobile administration
  navigation.

## Files changed

- `apps/web/app/admin/sites/[siteId]/memberships/page.tsx`
- `apps/web/app/admin/sites/[siteId]/settings/page.tsx`
- `apps/web/src/admin/membership-workflows.tsx`
- `apps/web/src/admin/shell.tsx`
- `apps/web/src/admin/site-workflows.tsx`
- `apps/web/tests/surface.test.mjs`
- `oap/active`
- `oap/orders/013-j-fix-real-governance-console-error.md`
- `oap/reports/013-j-fix-real-governance-console-error.md` (report only)

## Acceptance-criteria evidence

### Project/device matrix

| Project | Local evidence | GitHub current-head result |
| --- | --- | --- |
| `setup` | PASSED in both post-diagnosis generations | PASSED |
| `governance` | PASSED in both post-diagnosis generations | PASSED |
| `desktop-chromium` | PASSED in generation 2 | PASSED |
| `desktop-firefox` | PASSED in generation 2 | PASSED |
| `desktop-webkit` | PASSED in generation 2 | PASSED |
| `tablet` | Generation 2 stalled at initial redirect | PASSED |
| `mobile-chromium` | Generation 2 stalled at initial redirect | PASSED |
| `mobile-webkit` | Generation 2 stalled at initial redirect | PASSED |

GitHub reported `compose-e2e: OK projects=8 setup=1 governance=1
stable-devices=6 artifacts=disabled` on the literal implementation head.

### Governance, security, and restart matrix

| Evidence | Result |
| --- | --- |
| Full functional governance workflow | PASSED locally and on GitHub |
| Zero unexpected console/page/network/response categories | PASSED on GitHub |
| Strict CSP retained without broad exception | PASSED |
| Exact request ID, private/no-store/noindex behavior | PASSED |
| Storage, URL, DOM, and request-URL secret checks | PASSED |
| Archive, relogin, archived navigation, and unknown-site behavior | PASSED |
| Six-device H1/landmark/skip/focus/44 px/320 px/reduced motion | PASSED on GitHub |
| Stop/start persisted archived site, inactive membership, and primary domain | PASSED on GitHub |
| Setup remained closed and fixtures retained after restart | PASSED on GitHub |
| Screenshot, trace, video, or raw diagnostic artifact retained | NO |

GitHub's restart assertion reported the archived site, inactive membership,
primary domain, retained fixtures, and closed setup state, followed by
`compose-smoke: OK`.

## Diagnostic handling

- Confirmed shell tracing was disabled and the disposable run used only
  repository fixtures, fake local credentials, and non-production origins.
- Two pre-browser attempts failed during the container package fetch because of
  transient registry DNS resolution. No diagnostic browser generation occurred
  in those attempts; the user authorized retry after the disconnect.
- Used the one authorized raw console diagnostic only in the local terminal.
- The diagnostic contained no credential-like data and was not copied into a
  report, annotation, trace, screenshot, video, request body, or retained file.
- Removed the diagnostic immediately after identifying the CSP conflict.
- Scans confirmed no raw-diagnostic marker remains; durable output still uses
  only fixed source/message vocabulary.

## Local verification

- `pnpm install --frozen-lockfile`: PASSED — pnpm `11.22.0`, no changes.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — web 8/8, browser worker 1/1, contracts 4/4.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED with non-empty output under `/tmp` only.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 130 files.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  53 tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED —
  33 tests.
- `python tools/check_repository.py`: PASSED.
- `uv run --frozen python -m tools.supply_chain.policy validate`: PASSED.
- `bash -n tools/compose/smoke.sh`: PASSED.
- `pnpm exec playwright test --list`: PASSED — exact eight-project topology.
- Repository Markdown lint with dependency/build trees excluded: PASSED —
  150 files, 0 issues.
- `git diff --check`: PASSED.
- CSP/storage/raw-diagnostic/secret-focused scans: PASSED.
- `sudo tools/compose/smoke.sh slaif010j`: FAILED after setup and governance
  passed; all six projects exposed the shared-shell/mobile-navigation defects.
- `sudo tools/compose/smoke.sh slaif010j2`: FAILED after setup, governance, and
  three desktop engines passed; tablet/mobile stalled at the initial redirect.
- Further unpushed clean generation: NOT RUN — the two-generation allowance was
  exhausted.
- Local PostgreSQL matrices, browser-worker/source experiments, images,
  Mermaid, and broad SBOM: NOT RUN as prohibited by the order.
- Automatic corrective pushed generation: PASSED on GitHub — setup,
  governance, six stable projects, restart, and final smoke.

## GitHub CI / required checks

Observed for implementation head
`27e98331b0172b25cfda9cd0d192ce0dc74e335d`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 34s |
| Analyze (javascript-typescript) | SUCCESS | 58s |
| Analyze (python) | SUCCESS | 54s |
| CodeQL | SUCCESS | 3s |
| Compose and edge packaging | SUCCESS | 6m21s; complete browser/restart proof |
| Dependency review | SUCCESS | 18s |
| Detect supported languages | SUCCESS | 5s |
| Foundation PostgreSQL 14 | SUCCESS | 1m47s |
| Foundation PostgreSQL 15 | SUCCESS | 1m48s |
| Foundation PostgreSQL 16 | SUCCESS | 1m35s |
| Foundation PostgreSQL 17 | SUCCESS | 1m49s |
| Foundation PostgreSQL 18 | SUCCESS | 1m41s |
| Markdown | SUCCESS | 6s |
| Mermaid | SUCCESS | 39s |
| Node contracts | SUCCESS | 2m5s |
| Python 3.12 quality and package | SUCCESS | 32s |
| Python 3.13 quality and package | SUCCESS | 33s |
| Python 3.14 quality and package | SUCCESS | 38s |
| Repository policy | SUCCESS | 9s |
| Supply-chain evidence | SUCCESS | 5m59s |

- Result: 20/20 successful; none pending, missing, failed, or cancelled.
- All required checks green at report drafting: yes.
- No workflow rerun occurred; the implementation push triggered the one fresh
  automatic current-head CI and CodeQL generation.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing qualified Node/pnpm/uv toolchains and passwordless `sudo`
  for disposable Compose resources.
- No production dependency, lockfile, package, browser, service, topology,
  network, volume, image reference, or durable host configuration was added.
- Compose cleanup ran after every attempted clean generation.

## Documentation

- No durable product documentation change was required; behavior is covered by
  existing admin source contracts and the immutable OAP report.
- No architecture, certification, compatibility, or readiness claim was added.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets, systems, credentials, or data accessed: no.
- Required tests skipped/not run: no; the current-head GitHub generation ran and
  passed every required browser/device/restart contract.
- Scope deviation: no.
- Backend/API/schema/migration/permission/dependency/Compose change: no.
- Console suppression, allowlist, downgrade, or broad matcher added: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `248135f4205fa52ed75161ed73f8914653605a0eab9edfde4bf08f7294d27668`
  - work order: `abc635bdacb29e665173a36a4de748725ab66b4c422b1c9d4161e2fb01633fdb`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- None for the activated work order.
- `COMPLETE` records execution evidence only; it is not strategic acceptance or
  merge authority.

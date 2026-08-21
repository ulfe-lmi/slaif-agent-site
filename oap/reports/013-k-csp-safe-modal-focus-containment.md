# OAP Coding-Agent Report — 013-k

## Work order

- Identifier: `013-k`
- Work-order file: `oap/orders/013-k-csp-safe-modal-focus-containment.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Added one product-owned CSP-safe modal primitive and migrated all four
administration dialogs to it. The primitive keeps Radix Dialog in non-modal mode
to avoid its CSP-incompatible body-style mutation, while adding explicit
`aria-modal`, stable admin-root inert ownership and exact restoration, initial
focus, forward/reverse Tab boundary wrapping, outside-focus redirection, overlay
pointer blocking, Escape closure, trigger focus restoration, and unmount cleanup.
Successful route changes and mutations close their dialog before continuing.

Source, type, unit, build, repository, packaging, supply-policy, Markdown, and
security scans pass. The first clean browser generation found that the inert
effect could run before Radix's portal content ref mounted; tracking that mount
fixed the concrete defect. The allowed post-diagnosis generation then timed out
inside the first site-switcher containment helper because Playwright's
actionability-aware focus operation waited on the intentionally inert background
control. That assertion was corrected to invoke DOM focus directly.

The one authorized corrective push produced 19/20 successful GitHub checks, but
Compose again timed out in the first site-switcher containment stage without a
narrower safe line or category. Governance, the four-consumer matrix, six stable
projects, and restart therefore remain incomplete. No workflow rerun, weaker
assertion, second corrective push, or additional local generation was made after
the order's allowance was exhausted.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head branches: `main` / `oap/013-responsive-admin`
- Starting remote PR SHA: `497f08142f2e7bdc83866c1028b2c98af1ae57a8`
- Starting remote `main` SHA: `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA: `ff3b8797b1b9fdddc02dcb0dd763591de01437d6`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commit pushed before report:
  - `ff3b8797b1b9fdddc02dcb0dd763591de01437d6`
- Report parent equals implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #25 only
- Merge, close, auto-merge, review acceptance, or workflow rerun performed: no

## Primitive semantics

- Uses the existing Radix Dialog dependency with `modal={false}` and no new
  package.
- Emits labelled `role=dialog` through Radix and explicit `aria-modal=true`.
- Resolves only the stable `[data-admin-background-root]` owner, records its
  prior inert property and attribute state, applies inert while open, and
  restores the exact prior state synchronously on close and during cleanup.
- Tracks portal content mount explicitly before applying inert/focus behavior.
- Moves initial focus to the first visible enabled focusable child, or the
  dialog fallback when none exists.
- Wraps forward Tab from the last control to first and Shift-Tab from first to
  last; a `focusin` guard redirects outside focus.
- Uses the existing fixed full-screen overlay to intercept pointer input and
  explicitly prevents overlay pointer-down default behavior.
- Preserves Radix Escape handling and trigger restoration after synchronous
  inert removal.
- Closes before successful site navigation, membership edit/deactivation, or
  archive completion; unsuccessful mutations keep their dialog open.
- Performs no runtime style mutation, raw HTML insertion, CSP relaxation,
  storage write, or console suppression.

## Four-consumer matrix

| Consumer | Source contract | Browser result |
| --- | --- | --- |
| Site switcher | Migrated to `CspModal`; route closes | Timed out in first containment helper |
| Membership edit | Migrated; success closes | NOT RUN due governance failure |
| Membership deactivate | Migrated; success closes | NOT RUN due governance failure |
| Site archive | Migrated; success closes | NOT RUN due governance failure |

The shared browser helper asserts inert/`aria-modal`, more forward and reverse
Tab steps than the dialog control count, programmatic and pointer attempts on a
background control, Escape cleanup, and exact trigger focus restoration. Its
first site-switcher invocation did not finish within the contract timeout in the
final local or GitHub generation.

## Files changed

- `apps/web/src/admin/csp-modal.tsx`
- `apps/web/src/admin/membership-workflows.tsx`
- `apps/web/src/admin/shell.tsx`
- `apps/web/src/admin/site-workflows.tsx`
- `apps/web/tests/surface.test.mjs`
- `tests/e2e/auth.spec.ts`
- `tests/e2e/governance.spec.ts`
- `tests/e2e/support.ts`
- `oap/active`
- `oap/orders/013-k-csp-safe-modal-focus-containment.md`
- `oap/reports/013-k-csp-safe-modal-focus-containment.md` (report only)

## Project and restart evidence

| Project/evidence | Final local result | GitHub result |
| --- | --- | --- |
| `setup` | PASSED | PASSED |
| `governance` | FAILED: site-switcher helper timeout | FAILED: same stage timeout |
| `desktop-chromium` | NOT RUN | NOT RUN |
| `desktop-firefox` | NOT RUN | NOT RUN |
| `desktop-webkit` | NOT RUN | NOT RUN |
| `tablet` | NOT RUN | NOT RUN |
| `mobile-chromium` | NOT RUN | NOT RUN |
| `mobile-webkit` | NOT RUN | NOT RUN |
| Stop/start fingerprints | NOT RUN | NOT RUN |

The static Playwright project list passed with setup, governance, and all six
stable browser/device projects in the established dependency order.

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
- Repository Markdown lint: PASSED — 152 files, 0 issues.
- `git diff --check`: PASSED.
- CSP/style/storage/raw-HTML/secret-focused scans: PASSED.
- Initial `slaif013k` project-name invocation: rejected before setup by the
  smoke harness's project-name validator; not a browser generation.
- `sudo tools/compose/smoke.sh slaif010k`: FAILED — setup passed; governance
  failed at the inert assertion because portal content mount was not tracked.
- Post-diagnosis Node lint/format/typecheck/test/build: PASSED.
- `sudo tools/compose/smoke.sh slaif010k2`: FAILED — setup passed; governance
  timed out in the first site-switcher containment helper.
- Final full static/policy gate after direct DOM-focus correction: PASSED.
- Additional local generation: NOT RUN — generation allowance exhausted.
- Local PostgreSQL matrices, browser-worker/source experiments, images,
  Mermaid, and broad SBOM: NOT RUN as prohibited by the order.

## GitHub CI / required checks

Observed for implementation head
`ff3b8797b1b9fdddc02dcb0dd763591de01437d6`:

| Check | State | Duration/detail |
| --- | --- | --- |
| Analyze (actions) | SUCCESS | 43s |
| Analyze (javascript-typescript) | SUCCESS | 1m0s |
| Analyze (python) | SUCCESS | 59s |
| CodeQL | SUCCESS | 3s |
| Compose and edge packaging | FAILURE | 3m29s; site-switcher stage timeout |
| Dependency review | SUCCESS | 19s |
| Detect supported languages | SUCCESS | 4s |
| Foundation PostgreSQL 14 | SUCCESS | 1m44s |
| Foundation PostgreSQL 15 | SUCCESS | 1m41s |
| Foundation PostgreSQL 16 | SUCCESS | 1m38s |
| Foundation PostgreSQL 17 | SUCCESS | 1m35s |
| Foundation PostgreSQL 18 | SUCCESS | 1m28s |
| Markdown | SUCCESS | 8s |
| Mermaid | SUCCESS | 59s |
| Node contracts | SUCCESS | 2m13s |
| Python 3.12 quality and package | SUCCESS | 34s |
| Python 3.13 quality and package | SUCCESS | 32s |
| Python 3.14 quality and package | SUCCESS | 35s |
| Repository policy | SUCCESS | 6s |
| Supply-chain evidence | SUCCESS | 6m24s |

- Result: 19/20 successful, 1/20 failed; none pending, missing, or cancelled.
- All required checks green at report drafting: no.
- No workflow rerun occurred; the one corrective implementation push triggered
  a fresh automatic CI and CodeQL generation.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- Used the existing qualified Node/pnpm/uv toolchains and passwordless `sudo`
  for disposable Compose resources.
- No package, dependency, lockfile, browser, service, image reference, topology,
  network, volume, or durable host configuration was added.
- Compose cleanup ran after both browser generations; no screenshot, trace, or
  video was retained.

## Documentation

- No durable product documentation change was required; source contracts and
  this immutable report describe the bounded semantic change.
- No architecture, compatibility, certification, or readiness claim was added.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets, systems, credentials, or data accessed: no.
- Required tests skipped/not run: yes — governance timeout blocked the four
  complete consumer proofs, six stable projects, and restart proof.
- Scope deviation: no.
- Backend/API/schema/migration/permission/dependency/Compose change: no.
- Inline style, unsafe CSP source, raw HTML, global arbitrary mutation, broad
  matcher, or console suppression added: no.
- Activated order or `oap/active` edited by coding agent: no; exact
  strategic-published bytes were committed with implementation.
- Activated artifact hashes preserved:
  - `oap/active`: `3c7921706420920e2ccba5f2f9297adc5fc9ef92e67b76731f7d4730574f24c5`
  - work order: `6d524ee5d95f12fbf2e4635ea1c7b3dbd992c8fdd9b27fa8ff7fd90c461dc3c8`
- Previous orders/reports rewritten: no.
- Extra objective PR: no.
- Coding-agent merge, close, auto-merge, acceptance, or review: no.
- Workflow rerun: no.
- Report commit changes only this report: yes.

## Known limitations / blockers

- The first site-switcher containment helper exceeds the 30-second governance
  contract timeout in the final local and GitHub generations. Safe output does
  not identify which remaining helper operation waits.
- The other three dialog consumers, six stable projects, and restart persistence
  remain blocked behind governance.
- Current-head GitHub CI is 19/20, so acceptance is unmet and this report is
  `PARTIAL`.

## Recommended strategic follow-up

Activate a continuation only if strategy chooses: add bounded fixed-vocabulary
step annotations inside the shared containment helper, identify the exact wait
without weakening inert/focus assertions, correct that concrete test or product
boundary, and run one fresh complete current-head generation. Coding does not
select or activate that continuation.

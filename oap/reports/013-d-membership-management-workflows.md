# OAP Coding-Agent Report — 013-d

## Work order

- Identifier: `013-d`
- Work-order file: `oap/orders/013-d-membership-management-workflows.md`
- Numeric objective: `013`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

PR #25 now includes a responsive membership administration workflow for
existing user UUIDs. It uses the seven existing Control API/catalog routes,
strictly validates and reconciles their responses, keeps role ceilings and
publication authority separate, replaces complete permission override sets,
uses optimistic versions for edit/deactivation, and refreshes conflict-safe
server state. It adds no backend route, database change, identity workflow, or
dependency. All ordered local gates and all 20 GitHub checks passed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #25, <https://github.com/ulfe-lmi/slaif-agent-site/pull/25>, `OPEN`
- Base/head: `main` / `oap/013-responsive-admin`
- Starting remote SHA: `d605642d7069309599d35700725ea0de9667d6fe`
- Implementation head SHA: `49a27296fd4cd2aa123657ff9ff50e37148b7d9c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation commit pushed before report:
  `49a27296fd4cd2aa123657ff9ff50e37148b7d9c`
- The report publication commit has the implementation SHA as its first parent.
- New PR this turn: NO
- Existing PR amended this turn: YES
- Workflow rerun: NO
- Merge or auto-merge performed: NO

## Changes made

- Added canonical `/admin/sites/{site_id}/memberships` navigation and page.
- Added strict role, permission, membership, session UUID, integer, category,
  catalog uniqueness, same-site, role-ceiling, and override reconciliation
  validation. Invalid or cross-catalog responses fail closed.
- Added same-origin GET/POST/PATCH/DELETE clients using the existing exact CSRF
  cookie helper and documented request bodies only.
- Added deterministic UUID-sorted membership cards with status, explicit and
  effective ceiling, version, global Platform Administrator fact, and concise
  override/effective-permission counts.
- Added existing-user UUID assignment with built-in role selection, role-bounded
  ceiling choices, complete allow/deny replacement, and no identity/invitation
  claim.
- Added a separate publication override control. Architect ceiling 4 remains
  non-publishing by default.
- Grouped assignable overrides by server-returned category and exposed
  installation/system scopes as visible non-submit-capable facts.
- Added prefilled versioned editing, semantic deactivation confirmation,
  current-human self-control suppression, duplicate-submit ref guard,
  stale-response sequence guard, conflict refresh, stable errors, and error
  focus.
- Added responsive card/dialog/form rules for 320 px use, 44 px controls,
  wrapping, visible focus, and the existing reduced-motion behavior.
- Updated durable administration, API, authorization, site, and status docs
  while preserving explicit deferred-product boundaries.

## Files changed

- `README.md`
- `apps/web/app/admin/sites/[siteId]/memberships/page.tsx`
- `apps/web/app/styles.css`
- `apps/web/src/admin/api.ts`
- `apps/web/src/admin/membership-workflows.tsx`
- `apps/web/src/admin/shell.tsx`
- `apps/web/tests/surface.test.mjs`
- `docs/ADMIN.md`
- `docs/API.md`
- `docs/AUTHORIZATION.md`
- `docs/SITES.md`
- `oap/active` (strategic bytes committed unchanged)
- `oap/orders/013-d-membership-management-workflows.md` (strategic bytes
  committed unchanged)

## Acceptance-criteria evidence

### Criterion 1 — Strict client contracts and authority

- Result: PASSED.
- The client validates UUIDs, integer bounds, fixed permission categories,
  booleans, arrays, membership status, catalog uniqueness, same-site rows,
  built-in role references, role ceilings, assignable disjoint overrides, and
  effective permission references.
- All calls use `credentials: "same-origin"`, `cache: "no-store"`, and the
  existing `csrfCookie` helper for mutations. No browser storage is used.
- Controls require either the server-returned Platform Administrator fact or
  both `membership:manage` and `role:manage`; the UI states that server policy
  remains authoritative. Session UUID is used only to suppress self controls.

### Criterion 2 — Responsive membership workflow

- Result: PASSED.
- Route/method/body matrix:

  | Action | Method and path | Client-owned request fields |
  | --- | --- | --- |
  | Load | `GET /roles`, `/permissions`, `/session`, site authority and membership list | none |
  | Add | `POST /sites/{site}/memberships` | target UUID, role, ceiling, complete allow/deny sets |
  | Edit | `PATCH /sites/{site}/memberships/{user}` | expected version, current status, role, ceiling, complete allow/deny sets |
  | Deactivate | `DELETE /sites/{site}/memberships/{user}?expected_version=N` | expected version query only |

- Memberships are sorted by UUID and all required facts remain visible in
  responsive cards. Role changes clamp invalid ceiling choices but do not alter
  override selections. Publication has a dedicated inherit/allow/deny control.
- Radix dialogs provide labelled description, Escape, focus trapping, and focus
  return. Error containers receive focus. CSS converts three-column cards and
  two-column permission groups to one column below 760 px and permits UUID
  wrapping without horizontal overflow.
- Pending ref and disabled controls prevent duplicate submission. A monotonic
  sequence prevents stale loads from overwriting current data. A 409 refreshes
  current server state before another edit.

### Criterion 3 — Security and semantic evidence

- Result: PASSED.
- Web contract tests assert exact routes, methods, fields, validators,
  permission-driven controls, publication separation, complete override
  replacement, semantic deactivation wording, self suppression, pending and
  stale-response guards, error focus/states, Radix semantics, responsive CSS,
  and absence of storage, raw HTML, remote origins, or forbidden identity
  fields.
- Existing comprehensive backend tests
  `test_catalog_membership_lifecycle_authority_and_site_isolation` and
  `test_membership_http_error_validation_csrf_and_atomic_state` remain the
  authoritative crafted-request evidence for Platform Administrator, Owner,
  bounded manager, Architect/Viewer/non-member, self target, cross-site UUID,
  active/inactive/unknown member, duplicate create, stale version, CSRF,
  ceiling/system-scope escape, publication add/remove, complete replacement,
  and semantic deactivation. GitHub ran those gates on PostgreSQL 14–18 and all
  five jobs passed.
- No client request accepts actor, trusted site context, effective authority,
  administrator fact, result version, timestamp, identity profile, or hard
  delete field.

### Criterion 4 — Documentation

- Result: PASSED.
- README and ADMIN/API/AUTHORIZATION/SITES docs describe existing-user UUID
  limits, built-in roles and ceilings, separate publication, complete
  overrides, conflict refresh, semantic deactivation, accessibility/error
  states, and server authority.
- Invitations, identity CRUD, custom roles, content/Puck, workspaces,
  capabilities, review, and publication execution remain explicitly deferred.

## Local verification

- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED — all 10 workspace projects already
  locked and up to date.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — production build, 8/8 Web tests, 1/1 browser-worker
  test, and 2/2 Vitest contract tests.
- `pnpm build`: PASSED — all packages built and the membership route appeared
  in the Next production route inventory.
- `pnpm licenses list --json > /tmp/013-d-node-licenses.json`: PASSED.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  53 tests.
- `python tools/check_repository.py`: PASSED.
- `uv run --frozen python -m tools.supply_chain.policy validate`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 --no-globs README.md docs/ADMIN.md docs/API.md docs/AUTHORIZATION.md docs/SITES.md oap/orders/013-d-membership-management-workflows.md`:
  PASSED — 0 issues.
- `git diff --check`: PASSED.
- Ordered CSP/storage/remote-origin and secret-pattern scans: PASSED — no
  matches in the membership client/page/test surface.
- Two intermediate `pnpm test` runs failed only in newly added static assertions:
  one expected a sentence on a single physical line after Prettier wrapping and
  one treated the required explanatory word “password” as a forbidden request
  field. Both assertions were corrected to test their intended contract; the
  unchanged implementation then passed, followed by two clean full test/build
  runs.
- Local PostgreSQL, Compose, Playwright/browser, image, Mermaid, and broad SBOM
  commands: NOT RUN — explicitly prohibited for this round; corresponding
  unchanged GitHub gates passed where applicable.

## GitHub CI / required checks

- State observed for implementation head
  `49a27296fd4cd2aa123657ff9ff50e37148b7d9c`: 20/20 SUCCESS.
- `Analyze (actions)`: SUCCESS.
- `Analyze (javascript-typescript)`: SUCCESS.
- `Analyze (python)`: SUCCESS.
- `CodeQL`: SUCCESS.
- `Compose and edge packaging`: SUCCESS.
- `Dependency review`: SUCCESS (advisory pre-existing OpenSSF scorecard
  annotations only; no dependency changed).
- `Detect supported languages`: SUCCESS.
- `Foundation PostgreSQL 14`: SUCCESS.
- `Foundation PostgreSQL 15`: SUCCESS.
- `Foundation PostgreSQL 16`: SUCCESS.
- `Foundation PostgreSQL 17`: SUCCESS.
- `Foundation PostgreSQL 18`: SUCCESS.
- `Markdown`: SUCCESS.
- `Mermaid`: SUCCESS.
- `Node contracts`: SUCCESS.
- `Python 3.12 quality and package`: SUCCESS.
- `Python 3.13 quality and package`: SUCCESS.
- `Python 3.14 quality and package`: SUCCESS.
- `Repository policy`: SUCCESS.
- `Supply-chain evidence`: SUCCESS.
- All required green at drafting: YES.
- No workflow was rerun. Report-only commit checks may be pending after
  publication; the strategic model independently verifies SELF.

## Local setup / dependencies

- No package, browser, database, service, or sudo setup was required.
- No dependency, manifest, or lockfile changed.

## Documentation

- Updated README plus ADMIN, API, AUTHORIZATION, and SITES guides.
- Claims remain pre-alpha and distinguish implemented membership administration
  from deferred identity, editorial, workspace, review, and publication work.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Backend/API/schema/migration/route-policy changed: NO.
- Production secrets accessed: NO.
- Production systems or data accessed: NO.
- Required tests skipped or not run: NO. Order-prohibited local infrastructure
  suites were not run and are reported above.
- Scope deviation: NO.
- New production dependency: NO.
- Extra objective PR: NO.
- Coding-agent merge, close, or auto-merge: NO.
- Workflow rerun: NO.
- Activated order or `oap/active` edited by coding agent: NO; exact strategic
  bytes were committed unchanged. Their SHA-256 values were respectively
  `edf0a5e2a92c3a4670e3a0882b3d70f0f21d8a2f68a3aee770ca7b2a5ab4cf33`
  and `50b22d45de90f53a8bf082c40feaeabd5b1ee776fbd0bb052558a41c4f002c91`.
- Report commit changes only this report: YES.

## Known limitations / blockers

- No blocker.
- The UI manages only already-provisioned user UUIDs. It has no user directory,
  invitation, email, password-reset, login, OIDC, custom-role, or identity-edit
  workflow.
- UI visibility is not authority; all mutation policy remains server-enforced.
- Browser/device accessibility and security closure remains explicitly assigned
  to 013-e; no browser claim is made from this round's static responsive tests.
- Content/Puck, workspaces/capabilities, review, and publication execution remain
  deferred.

## Recommended strategic follow-up

Independently verify this report-only SELF topology and PR #25, then select only
the continuation explicitly intended by the roadmap.

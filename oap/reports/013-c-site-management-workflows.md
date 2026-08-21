# OAP Coding-Agent Report — 013-c

## Work order

- Identifier: `013-c`
- Work-order file: `oap/orders/013-c-site-management-workflows.md`
- Numeric objective: `013`
- PR mode: `AMEND_EXISTING_PR`
- Delivery mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

Amended only objective-013 PR #25 with server-authorized responsive site
governance. One reusable Control helper authenticates once, derives current
Platform Administrator or exact-site membership authority, fetches the current
membership version, and calls the existing database permission function before
site operations. Reads require `site:read`, profile writes require
`site-policy:manage`, and domain writes require `site-domain:manage`. Creation
and archive remain Platform-Administrator-only; archive additionally requires
the server-authenticated session to be recent.

Added strict same-origin Web validation/CSRF helpers and URL-owned site list,
create, overview, profile/domain settings, primary replacement/removal, and
explicit archive-confirmation flows. Controls use only server-returned global
and permission facts. No schema, migration, dependency, membership workflow,
content/Puck, workspace, review, publication, DNS automation, or deletion was
added.

The literal implementation head passed all 20 GitHub CI/CodeQL checks,
including PostgreSQL 14–18, clean Compose/browser packaging, Mermaid, and
supply-chain evidence. No corrective generation or workflow rerun was used.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: `#25` — `https://github.com/ulfe-lmi/slaif-agent-site/pull/25`
- State: `OPEN`, non-draft, merge-state `CLEAN`
- Base/head: `main` / `oap/013-responsive-admin`
- Starting remote SHA: `377016298b6e37659b0a9eae6f640a7685fe3c88`
- Implementation head SHA: `d6714929fc01bd52f6c69875557f2f5b8ec6ca11`
- Report publication commit: `SELF`
- Implementation commit pushed:
  - `d6714929fc01bd52f6c69875557f2f5b8ec6ca11` — `Add responsive site governance workflows`
- Report commit first parent: same as Implementation head SHA
- New PR/additional objective PR: `NO`
- Merge, close, auto-merge, acceptance, release, or tag: `NO`

## Authority and route matrix

| Route | Platform Administrator | Active site membership |
| --- | --- | --- |
| `GET /sites/{id}` | allowed, including truthful archived detail | `site:read`, active site only |
| `PATCH /sites/{id}` | allowed | `site-policy:manage`, active site only |
| `GET /sites/{id}/domains` | allowed | `site:read`, active site only |
| domain POST/PUT/DELETE | allowed | `site-domain:manage`, active site only |
| `POST /sites` | allowed | denied |
| `POST /sites/{id}/archive` | allowed with recent auth | denied |

Mutations use the existing atomic session-plus-CSRF decision. The request
cannot provide actor/site authority, role, permission, membership version, or a
recent-auth override. Inactive, disabled, stale, archived-for-member, unknown,
and cross-site authority fails closed. Unauthorized profile/domain attempts in
real PostgreSQL tests left the profile and domain inventory unchanged. A valid
but non-recent administrator session received stable 403 and the site remained
active. Archive remains idempotent for a current recent-auth administrator and
deletes no row.

## UI, form, and state matrix

- `/admin/sites` uses the server-filtered list, reports status/role/global
  facts, has loading/empty/error states, and keeps site selection in the URL.
- `/admin/sites/new` exposes key/name/locale creation only when the server list
  returns Platform Administrator authority and navigates to the created UUID.
- `/admin/sites/{site_id}` reports status, local public route, revision, locale,
  and authority with a settings link.
- `/admin/sites/{site_id}/settings` loads validated site, authority, domains,
  and session state. It provides permission-driven profile and domain controls,
  including primary replacement, and otherwise renders read-only text.
- Archive is global-only, names the site, explains preservation, uses Radix
  Dialog Escape/focus-return semantics, requires explicit confirmation, and
  disables confirmation when recent-auth is false. Server 403 remains truth.
- Stable UI classifications cover unauthenticated, denied/not-found, conflict,
  validation, unavailable, and invalid-response states. Request sequencing
  prevents stale refresh overwrites and a synchronous pending guard prevents
  duplicate mutation submission.
- Forms have labels, descriptions/status text, visible repository focus rules,
  44 px targets, reduced motion, 320 px wrapping, and no raw HTML, inline style,
  remote asset/origin, or browser storage.

## Changes and files

- Backend authority/routes: `site_authority.py`, `site_http.py`, and
  `route_policy.py`.
- Backend evidence/package manifest: site and membership HTTP integration tests
  plus the exact distribution-content allowlist.
- Web: typed `admin/api.ts`, `site-workflows.tsx`, admin shell, create/settings
  pages, responsive styles, landing claims, and surface tests.
- Documentation: `README.md`, `docs/ADMIN.md`, `docs/API.md`,
  `docs/AUTHORIZATION.md`, `docs/SECURITY.md`, and `docs/SITES.md`.
- Transcript: committed the strategic `oap/active` and activated order without
  editing their published bytes.

## Local verification

Passed:

```text
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
python -m compileall -q tools tests/repository services/backend/src
python -m unittest discover -s tests/repository -p 'test_*.py'
  53 passed
uv run --frozen pytest services/backend/tests/unit tests/repository -q
  339 passed, 26 subtests passed
PG... uv run --frozen pytest test_site_control_http_integration.py test_membership_control_http.py -q
  4 passed (final focused run; owner/architect/viewer/non-member/cross-site/
  CSRF/recent-auth and no-mutation evidence)
PG... uv run --frozen pytest test_foundation_postgres.py -q
  4 passed after local PostgreSQL restart
uv build --out-dir /tmp/slaif-agent-site-distributions
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
  web 7/7; browser worker 1/1; contracts 2/2
pnpm build
  successful Next production builds and all packages
pnpm licenses list --json
python tools/check_repository.py
  PASS repository policy
npx --yes markdownlint-cli2@0.23.2 --no-globs <changed docs/order>
  0 issues
git diff --check
CSP/storage/remote-origin/credential/private-key scans
```

The long combined local Agent-Site integration selection was not claimed as
passing. It reproducibly caused the VM's PostgreSQL 16 TCP listener to close
new SSL connections while Unix-socket health, disk, and memory remained
healthy. Direct TCP `psql` reproduced the reset; restarting the disposable
cluster restored TCP and the isolated foundation gate passed, after which the
long sequence reproduced the listener failure. Focused changed-path real
PostgreSQL tests passed twice before this VM condition. GitHub's isolated
PostgreSQL 14, 15, 16, 17, and 18 jobs all passed the complete defined
foundation and Agent-Site integration gates.

Local Mermaid rendering returned the same renderer `[object Object]` failure
for all 12 existing diagrams, including untouched architecture diagrams.
GitHub Mermaid passed. Local Compose and Playwright were not run, as prohibited
for 013-c; GitHub's unchanged Compose/edge/browser job passed. No skipped,
failed, pending, or not-run item is represented as local passing evidence.

## GitHub current-head checks

All 20 checks on `d6714929fc01bd52f6c69875557f2f5b8ec6ca11`
completed successfully:

1. Repository policy
2. Detect supported languages
3. Node contracts
4. Analyze (actions)
5. Analyze (python)
6. Analyze (javascript-typescript)
7. Python 3.12 quality and package
8. Python 3.13 quality and package
9. Python 3.14 quality and package
10. Foundation PostgreSQL 14
11. Foundation PostgreSQL 15
12. Foundation PostgreSQL 16
13. Foundation PostgreSQL 17
14. Foundation PostgreSQL 18
15. Compose and edge packaging
16. Supply-chain evidence
17. Markdown
18. Mermaid
19. Dependency review
20. CodeQL

No workflow was manually rerun and no corrective implementation generation was
published.

## Scope, transcript, dependencies, and safety

- No dependency, lockfile, schema, migration, CI workflow, Compose/edge
  topology, browser test, media, capability, content, workspace, membership UI,
  review, publication, DNS automation, or site deletion changed.
- One package allowlist assertion was mechanically extended for the explicitly
  allowed new `site_authority.py` distribution module.
- Documentation states domain rows do not automate DNS, archive does not
  delete, membership UI remains 013-d, and browser/accessibility closure remains
  013-e.
- Setup used the existing exact toolchains, disposable local PostgreSQL, and
  passwordless sudo only to set the fake local password and restart that local
  cluster. No production resource, Docker socket, external service, or secret
  was accessed. No credential or private data was committed or printed.
- `oap/active` SHA-256:
  `bb4e16135ecf9229e06f5c799071e4b40488bda0d14f0c0948bcb0560e37f7bb`
- Activated-order SHA-256:
  `57ee3073347d34f30ea16af0c00b3e1049daf90ec9e73ccd0c9613ec4fedcda1`
- Governing files and all prior orders/reports remained byte-immutable.
- No extra PR, workflow rerun, merge, auto-merge, close, acceptance, issue,
  release, or tag was performed.

## Limitations and blockers

Membership management is reserved for 013-d. Full Playwright/accessibility
closure is reserved for 013-e. Content/Puck, workspaces/capabilities, review,
publication, DNS automation, and site deletion remain absent. These are planned
boundaries, not blockers for 013-c. `COMPLETE` means delivered for strategic
review, not accepted or merged.

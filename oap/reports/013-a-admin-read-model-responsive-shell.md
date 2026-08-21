# OAP Coding-Agent Report — 013-a

## Work order

- Identifier: `013-a`
- Work-order file:
  `oap/orders/013-a-admin-read-model-responsive-shell.md`
- Numeric objective: `013`
- PR mode: `CREATE_NEW_PR`
- Delivery mode: `CREATED_NEW_PR`

## Status

`COMPLETE`

## Executive summary

Created the sole objective-013 branch and ready PR from authoritative remote
`main`. Added two server-owned current-human Control read routes backed by
fixed-search-path, owner-controlled PostgreSQL functions with exact Control
grants and no direct relation access. Platform Administrators receive all
sites, including archived sites, without a synthetic membership; ordinary
humans receive active authorized memberships only. Site authority lookup is
constant-404 for unavailable and cross-site objects.

Added a responsive, read-only administration dashboard and canonical
`/admin/sites/{site_id}` overview. Site selection remains URL-owned, data is
loaded same-origin with no-store semantics after session authentication, and
no token, permission, or site claim enters browser storage. The mobile/site
switcher uses Radix Dialog for focus trapping, Escape dismissal, focus return,
and strict-CSP-compatible CSS positioning. Tailwind and PostCSS are compiled
locally; there is no CDN, remote font, telemetry, or hosted runtime service.

All required local gates passed. The selected real-PostgreSQL suite passed 34
tests, the final focused FastAPI/PostgreSQL route test passed, and the complete
unit/repository suite passed 338 tests plus 22 subtests. Frozen Node lint,
format, typecheck, tests, two production builds, and license inventory passed.
The literal implementation head passed all 20 GitHub CI/CodeQL checks,
including PostgreSQL 14–18, Compose/browser packaging, supply-chain evidence,
and three CodeQL language analyses.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `25`
- PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/25`
- PR state at report time: `OPEN`
- PR title: `[OAP 013] Build responsive administration workflows`
- PR readiness: non-draft (`draft: false`)
- Mergeability: `MERGEABLE`; merge-state status `CLEAN`
- Base branch: `main`
- Head branch: `oap/013-responsive-admin`
- Starting remote `main` SHA:
  `bea5894a48f3d57666b87194df0c76cdb091f215`
- Implementation head SHA:
  `603aafb0aab0bd5e53eaf699757a6040ff0ee934`
- Report publication commit: `SELF`
- Implementation commits pushed before the report commit:
  - `893093cb16eca02cb4208f90673b6250ebfc80ba` — `Build responsive
    administration read shell`
  - `603aafb0aab0bd5e53eaf699757a6040ff0ee934` — `Align Node license gate
    with reviewed policy`
- Report commit first parent: same as Implementation head SHA
- Created a new PR: yes, exactly PR `#25`
- Additional objective PR: none
- Auto-merge request: none (`autoMergeRequest: null`)
- Merge performed: `NO`

## Changes and files

- Added migration `015_001_admin_read_model.py` after `014_001` with
  `slaif_current_human_sites(uuid)` and
  `slaif_current_human_authority(uuid, uuid)`. Both are Security Definer,
  owner-controlled, fixed-search-path, `PUBLIC`-revoked, and granted only to
  `slaif_control`.
- Added typed `CurrentHumanSite` and `CurrentHumanAuthority` models, exact SQL
  adapters, and authenticated GET routes:
  - `/api/control/v1/me/sites`
  - `/api/control/v1/sites/{site_id}/my-authority`
- Added exact private/no-store headers for `/me/sites` and preserved route
  policy actual/declaration equality.
- Added real PostgreSQL and ASGI HTTP evidence for global administrator,
  owner, viewer, archived, disabled, cross-site, malformed UUID, response
  ordering, private headers, and least privilege.
- Added exact self-hosted dependencies: `@radix-ui/react-dialog@1.1.23`,
  `tailwindcss@4.3.3`, `@tailwindcss/postcss@4.3.3`, and
  `postcss@8.5.26`.
- Added locally compiled Tailwind/PostCSS, in-repository UI primitives,
  responsive admin tokens/layout, dashboard, site overview, planned-section
  navigation, loading/empty/error/archived states, skip link, logout, and
  accessible site-switcher dialog.
- Added source-contract coverage for same-origin/no-store reads, strict
  response validation, URL ownership, storage/remote-origin absence,
  responsive 320 px behavior, and focus-managed Radix usage.
- Qualified Lightning CSS 1.32.0 and its Linux native artifact under the
  repository's explicit MPL-2.0 review and regenerated notices.
- Updated README and `docs/{ADMIN,API,AUTHORIZATION,CONFIGURATION,SECURITY,
  TESTING}.md` with implemented versus deferred behavior.
- Updated CI, migration/grant inventories, repository policy, and the
  PostgreSQL 14–18 integration list without changing established check names.
- Committed the strategic-authored `oap/active` and activated order unchanged.

The implementation-head diff contains 40 authorized paths. `SELF` adds only
this report as the final path.

## API response and authority matrix

| Caller | `/me/sites` | `/sites/{id}/my-authority` |
| --- | --- | --- |
| Platform Administrator | All sites, including archived; null membership fields | Any existing site; global flag; no synthetic membership |
| Active ordinary member | Active member sites only, deterministic order | Exact active site membership and effective permissions |
| Cross-site/non-member | No substituted site | Constant `404 RESOURCE_NOT_FOUND` |
| Disabled human | Empty | Constant 404 |
| Unauthenticated | 401 | 401 |
| Malformed site UUID | Not applicable | Typed 422 with private headers |

Trusted server session context selects the human UUID. The path selects only a
candidate site UUID; the database function rechecks current global/site
authority. Neither route accepts a caller user UUID, capability, permission,
membership, or site claim.

## Dependency and CSP evidence

| Package | Version | Scope | License | Registry integrity |
| --- | --- | --- | --- | --- |
| `@radix-ui/react-dialog` | 1.1.23 | runtime | MIT | `sha512-Ksw4WeROkO4rC9k/onilX/Ao2Cr1ku1unMNH+XSCcP4jSXYu7HDsg9n4ojMjVb22XpYjAQ9qfrFlVbru1vXDUA==` |
| `tailwindcss` | 4.3.3 | build/dev | MIT | exact lockfile artifact |
| `@tailwindcss/postcss` | 4.3.3 | build/dev | MIT | exact lockfile artifact |
| `postcss` | 8.5.26 | build/dev | MIT | exact lockfile artifact |
| `lightningcss` and Linux native artifact | 1.32.0 | transitive build | MPL-2.0 | exact lockfile artifacts; explicit policy review |

- `pnpm-lock.yaml` SHA-256:
  `00c0ec759fbeb42372c572e1a24f7140330d522ef92e52ad92aac3c0f49f1b24`
- `apps/web/package.json` SHA-256:
  `f1505b96ffdd8792f1f1cc7a6cdaf5a2df1d9798a6a5a9184bc777e8a85daec3`
- `supply-chain/policy.json` SHA-256:
  `9a46d4f83a55157cfddf2e443f945a9bed717ea3897e43ffcd4d4ae62342f8e9`
- Radix Dropdown was rejected during local CSP audit because Popper supplies
  inline positioning. Radix Dialog replaced it; position, dimensions, overlay,
  and animation are compiled CSS, with no `unsafe-inline` or remote origin.
- Source scans found no local/session storage, service worker, external origin,
  unsafe-inline/eval token, or telemetry reference in the admin surface.

## Local verification

Passed:

```text
uv lock --check
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
  52 passed
uv run --frozen pytest services/backend/tests/unit tests/repository
  338 passed (final concise run also reported 22 subtests)
uv run --frozen pytest services/backend/tests/integration/test_current_human_control_http.py services/backend/tests/integration/test_human_rbac.py services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_control_database_integration.py
  34 passed in 228.01s
uv run --frozen pytest services/backend/tests/integration/test_current_human_control_http.py -q
  1 passed in 4.92s after final HTTP/header corrections
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
  web 7/7; browser worker 1/1; contracts 2/2
pnpm build
  production Web/Next webpack build passed; all packages built
pnpm licenses list --json
python tools/check_repository.py
uv run --frozen python -m tools.supply_chain.policy validate
npx --yes markdownlint-cli2@0.23.2 --no-globs <changed Markdown/order>
git diff --check
dependency, secret, remote-origin, telemetry, storage, and CSP source scans
```

The final focused web correction gate also passed web lint, typecheck, seven
source tests, and production build. Local Compose, Playwright/browser, images,
and broad SBOM were not run, exactly as deferred/forbidden by this order;
GitHub's clean Compose/browser and supply-chain jobs supplied that evidence.
No skipped or pending local command is claimed as passing.

## GitHub current-head checks

All 20 checks on `603aafb0aab0bd5e53eaf699757a6040ff0ee934`
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

No workflow was manually rerun. Current-head Compose/browser passed in 5m59s;
supply-chain evidence passed in 5m55s.

## Corrections, failures, and diagnosis

- Corrected exact migration/file/count inventories after adding revision 015
  and the two routes; no requirement or test was weakened.
- Corrected the PostgreSQL fixture sequence so membership exists before an
  account is disabled.
- A broad local PostgreSQL run saw one connection reset while opening a fresh
  owner connection. PostgreSQL remained healthy with no crash/restart log; the
  isolated test passed, and the unchanged complete 34-test selection later
  passed.
- Next 16.3.1 Turbopack's PostCSS child exited before connecting on this VM.
  Direct PostCSS compilation succeeded; the supported `next build --webpack`
  path compiled twice locally and in GitHub. The exact build command is guarded
  by repository policy.
- The first GitHub Node job rejected reviewed MPL-2.0 packages because its
  legacy inline allowlist did not mirror the central explicit-review policy.
  The single final corrective commit aligned the CI inventory with the existing
  package-specific review; final Node and supply-chain jobs passed.
- Compose/browser then exposed two preserved-flow regressions from replacing
  the old admin session page: missing session/account confirmation and an
  unnecessary concurrent `/me/sites` request after session revocation. The
  corrective commit was amended to preserve the truthful labels and sequence
  session authentication before site loading. Final Compose/browser passed.
- One GitHub status poll had a transient API connection error. No workflow or
  job was rerun.

## Documentation, scope, and safety confirmations

- Documentation truthfully states this round is read-only. Site and membership
  mutations remain API-only until 013-b/c. User creation/invitations/custom
  roles are absent. Content, Puck, workspaces, review, and publication remain
  unimplemented.
- No site/domain/archive or membership mutation UI, content/model/page/Puck,
  workspace/capability, agent/review/audit/publication feature, Compose topology
  change, demo seed, OIDC/MFA, hosted service, remote asset, telemetry, or
  unrelated dependency upgrade entered scope.
- No production system, production data, Docker socket, or protected secret was
  accessed. Test credentials were disposable/fake and no secret was committed
  or printed.
- Governing hashes remained unchanged:
  - `AGENTS.md`: `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
  - `OAP-COMMUNICATION-coding-agent.md`: `00bdd82fcec0afaf65d2fbc2a2f9fa43a7d4e9e254d7a262bea0c5bae3be6b8a`
  - `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
  - `oap/active`: `e96d03c20505ff74b87acb2beaf745fc6b40df9338b0d57925ec33724ebbd989`
  - activated order: `be47f3acd852e63387af45acc93222568a34e958a3e6e062c573c020ed2a76f2`
- Previous OAP orders/reports were not edited. Unrelated PRs/work were not
  modified. Exactly one objective-013 PR exists. No merge, close, acceptance,
  auto-merge, issue, release, or tag action was performed.

## Limitations and blockers

None for work order 013-a. `COMPLETE` means delivered for independent strategic
review; it does not mean accepted or merged.

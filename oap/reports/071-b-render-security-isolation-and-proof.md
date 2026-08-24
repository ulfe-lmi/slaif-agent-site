# OAP Coding-Agent Report — 071-b

## Work order

- Identifier: `071-b`
- Work-order file: `oap/orders/071-b-render-security-isolation-and-proof.md`
- Numeric objective: `071`; round: `071-b`
- PR mode: `AMENDED_EXISTING_PR`
- Scope: repair the concrete Render preview authorization, projection
  integrity, route/error, credential-loading, media-reference, and proof gaps
  identified after 071-a, without adding lifecycle or publication scope.

## Status

COMPLETE

## Executive summary

Objective 071-b is implemented on the existing PR #62. Preview authorization
now applies the established idle, absolute-expiry, revocation, account/site,
membership, workspace, touch, and recent-auth semantics for HUMAN, AGENT, and
IMPORT workspaces. It is reasserted on the COW connection under the workspace
shared advisory lock before any content query, so mutable authority cannot be
revoked between authorization and projection.

Render service credentials are startup-resolved and immutable. Both Render and
Web validate the process-owned secret directory/file policy; Render rejects
missing, empty, malformed, duplicate, wrong, or unconfigured credentials, and
Web reads the validated file through an `O_NOFOLLOW` handle to close the file
system race identified by fresh CodeQL.

The projection now enforces the trusted catalogue's component prop schemas,
parent-owned slots and child limits, current catalogue version, bounded nested
values, same-origin links, and collection field projections under an explicit
`values` namespace. Public routing attempts canonical root projection first,
uses the routing shell only at an exact matched site root, and returns 404 for
deeper unknown/unpublished paths. Image rendering uses an honest placeholder;
public media finalization remains out of scope.

Real PostgreSQL expiry/revocation/race, multi-site/workspace, AGENT/IMPORT,
collection-reserved-field, HTTP, Compose, and authenticated Playwright preview
evidence passes. No review snapshot, promotion, publication, browser-worker,
public-media-finalization, new dependency, extra PR, or merge was introduced.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#62](https://github.com/ulfe-lmi/slaif-agent-site/pull/62)
- State: `OPEN`, non-draft, `MERGEABLE`
- Base/head: `main` / `oap/071-render-api-page-preview`
- Starting remote SHA for this continuation:
  `36f7007d761a41af143f6239792077a7671ea94b`
- Strategic activation commit:
  `7e50486478750874e3ff64c63d7f1b214ec32bff`
- Initial 071-b implementation commit:
  `a6efa340bc5eacb1d1bfa5742bcc22fab5705eb1`
- In-scope CodeQL file-race repair commit:
  `eab228ce583169ce9eebf52ae62ceef11ddc49cf`
- Implementation head SHA: `eab228ce583169ce9eebf52ae62ceef11ddc49cf`
- Remote PR head before report publication:
  `eab228ce583169ce9eebf52ae62ceef11ddc49cf`
- Existing PR amended: YES; new PR: NO
- Merge or auto-merge: NO

The current transcript bytes are preserved unchanged:

- `oap/active` is exactly `071-b\n`; SHA-256:
  `20141da2f5912e2d74b91d19a47672a7316c9b36fe47837509d60d036c34ae1d`.
- `oap/orders/071-b-render-security-isolation-and-proof.md` SHA-256:
  `1e878bb9d710eaf11e47b283a148f2a8fdf4d823b94a8ddd614b6032fc3292fc`.
- The immutable 071-a order remains SHA-256:
  `01c514da0ea25bd693b65ef669258ac1545e211d03d209bdea7ed2c40ca6752e`.
- The immutable 071-a report remains SHA-256:
  `7fe0e1abe9d90ce3c440fba5d807659e5bef8e17b86cb04da80d546f1302abdd`.

## Changes made

### Preview authorization and COW isolation

- Added forward-only Alembic migration `033_001_render_preview_recheck.py`.
  It replaces the narrow 032 function with an owner-defined, fixed-signature
  Render wrapper that validates session digest, active account/site,
  absolute expiry, idle expiry, revocation, workspace site binding, actor
  type, active/unexpired workspace state, creator or `workspace:read-all`,
  and `preview:inspect`/Platform Administrator authority.
- The wrapper preserves touch and recent-auth semantics and acquires the
  workspace shared advisory transaction lock before returning trusted values.
- Preview first derives trusted workspace/site values, then starts the COW
  transaction on the separate preview pool and reasserts the complete
  mutable authorization on that same connection before `_query` reads page,
  composition, collection, navigation, theme, or catalogue data.
- Preview pool cleanup remains owned by the COW context on success, denial,
  exception, cancellation, timeout, and disconnect paths.
- Exact privilege mappings and catalog metadata execution grants were added;
  no generic session-finalizer, table DML, migration, reviewer, setup, agent,
  editor, or publication authority was granted to the preview role.

### Fail-closed Render/Web credential boundary

- Render settings now validate bounded preview policy values and the
  file-backed Web-to-Render credential's regular-file, no-symlink, exact
  mode, owner, directory mode/owner, nonempty ASCII, and length policy.
- Render resolves the credential during app construction/startup and passes
  immutable bytes into middleware. Middleware does not read an environment
  path per request and rejects zero, duplicate, empty, malformed, wrong, and
  missing credentials before body handling; there is no empty-secret compare.
- Web validates its credential once at module startup and reads the secret
  using an `O_NOFOLLOW` descriptor, checking the opened handle rather than
  reopening a previously checked path.
- Compose retains isolated `render-secret`, `render-preview-secret`, and
  `render-auth-secret` mounts; Web receives only the Render call credential.

### Projection, routing, renderer, and media honesty

- Parent catalogue slots now own validation; root/default behavior, parent
  max-children, deterministic order, cycle/depth/count, scope, reachability,
  schema version, required fields, types, enums, numeric bounds, references,
  nested depth, executable keys, and unsafe schemes are bounded and fail
  closed.
- The actual site component catalogue version is read through the narrow
  owner-defined catalog function and must equal the trusted `catalog-v1`.
- Collection views validate same-site active type and declared fields,
  allowlisted projection syntax, reserved metadata names, filter/sort/
  pagination shapes, result bounds, and cross-site scope. Editorial values
  are returned only in `item.values`, so values named `id`, `slug`, `status`,
  `site_id`, `type_id`, or `values` cannot overwrite metadata.
- Public root resolution attempts canonical projection for non-loopback
  authorities. The shell is returned only when the request exactly matches
  the resolved site root; deeper unknown, malformed, deleted, draft-only, or
  unpublished routes return 404.
- The server-only Web client distinguishes internal 404 from 401/503 instead
  of collapsing every failure into a shell or null result.
- Button links are same-origin product-relative paths only. Image nodes render
  a labelled non-broken placeholder until a future public-media projection
  explicitly marks bytes public. Duplicate static Hero IDs were removed.

### Real browser and repository proof

- Added an authenticated Playwright preview project to the clean Compose E2E
  sequence. A disposable COW workspace updates the demo title and Heading;
  Playwright navigates the actual preview route, proves overlay DOM order,
  private/no-store/noindex headers, strict CSP, no session token in URL/DOM/
  browser-readable cookies/storage, no console/request failures, and then
  proves canonical navigation remains unchanged.
- Updated the existing route E2E expectation to prove exact custom-site-root
  shell behavior and deeper-route 404 behavior.
- Added real PostgreSQL evidence for idle, absolute-expired, revoked, and
  post-authorization revocation race denial with unchanged page-change,
  idempotency, and audit counts; HUMAN, AGENT, and IMPORT workspace preview;
  wrong-site workspace denial; collection field projection and metadata
  spoofing resistance; and current catalog/prop/tree contracts.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/033_001_render_preview_recheck.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/render_api/{app,config,database,projection,site_http}.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/src/slaif_agent_site/sites/service.py`
- `apps/web/app/page.tsx`
- `apps/web/app/[...sitePath]/page.tsx`
- `apps/web/src/sites/{render,service-auth}.ts`
- `apps/web/src/renderer/components.tsx`
- `apps/web/tests/surface.test.mjs`
- `tests/e2e/{governance.spec.ts,preview.spec.ts}` and `playwright.config.ts`
- focused backend unit/integration and catalog-version fixtures
- `tools/compose/{e2e.sh,smoke.sh}`
- `docs/{API,DEPLOYMENT,SECURITY,TESTING}.md`

## Acceptance-criteria evidence

### Exact session semantics and race-safe preview reads

PASSED. Real PostgreSQL proves valid preview, idle-expired denial,
absolute-expired denial, revoked denial, AGENT/IMPORT authorized preview,
wrong-site workspace denial, and a deterministic pause-after-initial-
authorization race. The race revokes the session before the COW recheck;
preview returns the non-leaking denial and page-change/idempotency/audit counts
remain unchanged. The recheck and subsequent projection are held under the
workspace shared advisory lock.

### Fail-closed service authentication

PASSED. Unit tests cover missing, empty, wrong, duplicate, and correct headers,
including an unconfigured middleware instance. File tests cover missing,
regular-file mode, directory mode, symlink, owner, nonempty, and bounded ASCII
policy. The final clean Compose/Playwright path proves the correct credential
is required for the real Web-to-Render preview. Fresh CodeQL initially found
the Web path-reopen race; commit `eab228c` changed it to same-handle
`O_NOFOLLOW` validation and fresh CodeQL passed.

### Catalogue, props, slots, and versions

PASSED. Unit tests cover valid `Hero.content`, invalid parent slot, required
and unsafe props, exact schema version, and bounded values. Real PostgreSQL
projection reads the site's `catalog-v1` rather than hardcoding a response
fact. Existing TypeScript catalog/Puck/renderer contract tests remain green.

### Collection projection integrity

PASSED. Real PostgreSQL fixture values include reserved metadata spoof names
and an unprojected sensitive field. The projection returns only the declared
title beneath `values`, preserves immutable `id`/`slug` metadata, and the
renderer consumes only that explicit namespace.

### Routes, errors, media, and renderer honesty

PASSED. Exact site roots use the shell only when no page exists; deeper custom
routes are 404; non-loopback `/` attempts canonical projection first. The
server-only client preserves 404 versus 401/503. Public image output contains
no nonexistent `/media/{uuid}` URL. Clean browser/edge evidence proves strict
CSP, private preview headers, canonical/preview separation, escaped content,
and no credential/session leakage.

### Real proof matrix and regression safety

PASSED. The final local Compose smoke reports `compose-smoke: OK`, including
authenticated preview E2E `projects=9`, all six stable device projects,
secret-file policies, edge/header/body policies, direct-route denial, role and
database-login negatives, locator failure/recovery, negative bootstrap,
Apache syntax, and packaging tests. The full backend integration suite and
all prior unit/repository suites are green.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED; 216 files formatted.
- `uv run --frozen mypy`: PASSED; 204 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED; 437 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 106
  tests in 439.02 seconds on the final broad run.
- Focused final
  `uv run --frozen pytest services/backend/tests/integration/test_render_projection_integration.py -vv`:
  PASSED; 2 tests in 10.02 seconds, including expiry, race, AGENT/IMPORT,
  multi-site, collection, and reserved-field evidence.
- `uv run --frozen pytest services/backend/tests/integration/test_control_database_integration.py services/backend/tests/integration/test_render_projection_integration.py services/backend/tests/integration/test_render_site_resolution.py`:
  PASSED; 7 tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED;
  54 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED; 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 222 files.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED; source
  distribution and wheel built.
- Process `--check` smoke for all ten declared backend processes: PASSED.
- Node `v24.14.1`, pnpm `11.22.0`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED, including E2E TypeScript.
- `pnpm test`: PASSED; Web/package builds, tests, and contracts.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `sudo sh tools/compose/smoke.sh slaif071b`: PASSED; final output
  `compose-smoke: OK`, including `compose-e2e: OK projects=9`, authenticated
  preview overlay/canonical isolation, six device projects, `106`-suite
  browser governance, edge, secret, role, recovery, negative-bootstrap,
  Apache, and packaging evidence.

## GitHub CI / required checks

Fresh checks were observed for literal implementation head
`eab228ce583169ce9eebf52ae62ceef11ddc49cf`:

- SUCCESS: Repository policy
- SUCCESS: Detect supported languages
- SUCCESS: Analyze (actions)
- SUCCESS: Analyze (python)
- SUCCESS: Analyze (javascript-typescript)
- SUCCESS: CodeQL
- SUCCESS: Node contracts
- SUCCESS: Python 3.12 quality and package
- SUCCESS: Python 3.13 quality and package
- SUCCESS: Python 3.14 quality and package
- SUCCESS: Foundation PostgreSQL 14, 15, 16, 17, and 18
- SUCCESS: Compose and edge packaging
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review

All checks were observed `COMPLETED/SUCCESS` for the implementation head;
none were pending, failed, cancelled, missing, or skipped at report drafting.

The initial implementation head `a6efa34` triggered one fresh high-severity
CodeQL alert (`js/file-system-race`) at the Web credential reader's path
reopen. This was a safe in-scope implementation repair, not a policy waiver:
`eab228c` opens the file with `O_NOFOLLOW`, validates the opened handle, reads
through that handle, and closes it. The fresh `eab228c` CodeQL and complete CI
matrix are green. Earlier 071-a evidence is retained in its immutable report:
its first CI attempt failed only on three fixture line-length diagnostics,
fixed by `bd4679a`; an initial local browser run exposed stale demo-page and
fixture-project expectations, repaired within 071-a before its final green
head. No prior failure was hidden or weakened.

## Local setup / dependencies

Routine local Docker/Compose, PostgreSQL, package, and Playwright setup ran
through the repository's existing passwordless privileged path (`sudo sh`)
because the shell user lacks direct Docker-socket permission. No production
system, production credential, host credential store, or unrelated data was
accessed. No dependency or lockfile change was made.

## Documentation

Updated API, deployment, security, and testing documentation for the exact
preview session policy, COW recheck, route fallback, collection `values`
shape, credential validation, and honest media placeholder. The 071-a report,
all earlier reports, activated orders, and `oap/active` were not edited.

## Safety and scope confirmations

- Unrelated files changed: NO; all 33 implementation/report-support paths are
  within the activated 071-b scope.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: NO for the claimed local and fresh CI sets.
  The initial exploratory nonexistent test path
  `services/backend/tests/unit/test_render_database.py` collected zero tests;
  it was corrected to the repository's actual Render unit files and is not
  claimed as evidence.
- Scope deviation: NO.
- Extra objective PR: NO; PR #62 remains the sole Objective 071 PR.
- Merge/auto-merge: NO.
- Activated order/active edited: NO.
- Report commit changes only this new report: YES.

## Known limitations / blockers

None for the bounded 071-b acceptance criteria. Review snapshots, freeze,
accept/discard/promotion, publication, browser-worker automation, and public
media finalization remain intentionally outside Objective 071 and are not
claimed here.

## Recommended strategic follow-up

Strategy should independently review the final diff, immutable transcript,
report ancestry, PR checks, and acceptance evidence, then choose whether to
accept/merge PR #62. Coding does not merge or choose the next objective.

## Report publication

Implementation head SHA: `eab228ce583169ce9eebf52ae62ceef11ddc49cf`

Report publication commit: SELF

The report-only commit must have the implementation head above as its sole
first parent, contain only this report, be pushed to PR #62, be verified as
the remote PR head, and only then signal the exact response FIFO `OK`.

RESULT=COMPLETE

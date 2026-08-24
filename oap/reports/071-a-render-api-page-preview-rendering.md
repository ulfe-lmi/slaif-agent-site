# OAP Coding-Agent Report — 071-a

## Work order

- Identifier: `071-a`
- Work-order file: `oap/orders/071-a-render-api-page-preview-rendering.md`
- Numeric objective: `071`; round: `071-a`
- PR mode: `CREATED_NEW_PR`
- Scope: typed canonical and HUMAN workspace-preview projections, separate
  Render reader pools, internal Web-to-Render authentication, one trusted SSR
  renderer, public/preview routes, strict headers, and proof through NGINX.

## Status

COMPLETE

## Executive summary

Objective 071-a is implemented on new PR #62. Render now returns bounded typed
canonical or authorized workspace-overlay JSON; Web owns HTML and uses one
trusted React catalogue renderer for public SSR, active preview, and Puck
previews. Preview authorization is performed before COW context selection, and
the preview pool is separate from the canonical public-reader pool.

The clean local Compose/browser smoke and fresh remote CI/CodeQL evidence pass.
No review snapshot, promotion, publication, browser-worker automation, public
media finalization, or unrelated architecture scope was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#62](https://github.com/ulfe-lmi/slaif-agent-site/pull/62)
- State: `OPEN`, non-draft, `MERGEABLE`, `CLEAN`
- Base/head: `main` / `oap/071-render-api-page-preview`
- Starting remote main: `88decb8f59894672d4c63cc7434196749b424647`
- Strategic transcript commit: `7eb79adb46fbf34c78980151972bcc9548c48690`
- Substantive implementation commit: `e2148f9dfca38c0c9eb0046af5afa17e9312ec36`
- CI fixture-format repair commit: `bd4679aa3ee78f41dc54b9270a5b28e2951e0091`
- Implementation head SHA: `bd4679aa3ee78f41dc54b9270a5b28e2951e0091`
- Remote PR head: `bd4679aa3ee78f41dc54b9270a5b28e2951e0091`
- New PR this round: YES; exactly one Objective 071 PR
- Merge or auto-merge: NO

## Strategic governance and transcript evidence

The first commit preserves the human-authorized governance correction and the
exact active order bytes:

- `oap/active` is exactly `071-a\n`; SHA-256:
  `9fd1b25523559bfc5403d4e59c46a9c39065c9bd64579eed5a5c63afce11410c`.
- `oap/orders/071-a-render-api-page-preview-rendering.md` SHA-256:
  `01c514da0ea25bd693b65ef669258ac1545e211d03d209bdea7ed2c40ca6752e`.
- Human-authorized corrected 070-d order SHA-256:
  `ba7b2ccba238d65d9ff96c0d1ddba8dfc85feb57e9d057ccf9ab65220ea2500c`.
- Human-authorized `.markdownlint-cli2.jsonc` SHA-256:
  `796ac74a922107b0d8ddefbf5cf1bf842f6feda2e103b33841f540e1135e8ea0`.
- Prior 070-d report and all earlier strategic reports remain unchanged.

The obsolete 070-d exact-path MD018 override was removed as authorized. The
historical 070-d prose correction and override removal were not mixed with
product implementation policy.

## Implemented request flow

```text
browser -> public NGINX -> Web route
        -> file-backed authenticated Web-to-Render request
        -> public or preview Render reader
        -> trusted site/page/workspace projection JSON
        -> shared trusted React catalogue renderer
        -> complete escaped HTML
```

Render remains internal-only. NGINX and Apache reject `/internal/`; no Render
upstream is exposed at the edge. Web never receives a database locator.

## Backend implementation

- Added typed `POST /internal/render/v1/page` canonical projection and
  `POST /internal/render/v1/preview` active-preview projection while retaining
  the site-context endpoint.
- Canonical resolution derives the active site and matched route from the
  trusted authority/path resolver and returns only published page rows.
- Preview accepts an untrusted workspace UUID only after the human session
  proof is checked by `control.slaif_render_preview_authorize`; it then opens a
  single `asyncpg_cow_session` with the authorized workspace UUID.
- Added bounded page metadata, normalized composition nodes, deterministic
  child ordering, catalogue/schema/slot/depth/count/prop checks, safe URL/value
  rejection, navigation/theme projection, and bounded same-site collection
  list/grid/detail bindings. Malformed data fails closed.
- Added migration `032_001_render_preview_authorization.py` with fixed
  `preview:inspect` and `workspace:read-all` authorization semantics, owner,
  fixed search path, public revoke, and exact preview-role execution grant.
- Render starts separate public and preview pools and validates exact
  `slaif_public_login`/`slaif_public_reader` and
  `slaif_preview_login`/`slaif_preview_reader` memberships.
- Added a high-entropy file-backed Web-to-Render credential. Middleware checks
  exactly one credential header in constant time before projection handling.

## Web/renderer implementation

- Public catch-all routes render canonical projections and retain the safe
  routing-context shell when no page projection exists.
- Added `/preview/{workspace_id}/{site_path...}`. It reads the HTTP-only human
  session cookie only on the server, returns login-safe redirect when absent,
  and sends the proof only over the internal Web-to-Render request.
- Replaced the partial renderer with one pure trusted implementation for every
  current catalogue component, including layout, basic, collection,
  institutional, and global components. Unknown/malformed components fail
  closed; rich text uses an explicit safe structured allowlist and never raw
  HTML.
- Public, preview, and Puck use the same renderer and catalogue code. Puck
  receives a bounded fallback only for incomplete editor props.
- Preview responses carry `Cache-Control: private, no-store`, `Pragma:
  no-cache`, and `X-Robots-Tag: noindex, nofollow, noarchive` through both
  edge adapters. Public CSP remains strict.

## Identities, mounts, and edge evidence

- `render-secret`: only `render-dsn` for the canonical reader.
- `render-preview-secret`: only `preview-dsn` for the preview reader.
- `render-auth-secret`: only `render-token`, mounted read-only to Web and
  Render; no database locator is mounted to Web.
- Secret directories/files retain the existing `0700`/`0400`, UID 10001
  ownership, no-symlink, one-shot initialization, and unrelated-UID denial
  contracts.
- Only NGINX publishes host port 8080. Direct Render/internal paths are
  rejected; Apache syntax and the same confinement policy pass.

## Acceptance-criteria evidence

### Canonical and preview isolation

- PASSED locally with real PostgreSQL roles. A published base page renders via
  the public reader. A HUMAN COW title update is visible through preview but
  the canonical reader continues returning the original title.
- PASSED locally for missing/invalid workspace/session and site-prefix
  confinement. The preview function requires active account/session/site,
  active unexpired HUMAN workspace, `preview:inspect`, and creator or
  `workspace:read-all` authority.
- PASSED locally that the preview pool cannot directly inspect base/change
  tables or perform DML; the public reader remains canonical-only.

### Projection and renderer safety

- PASSED unit tests for route boundaries, unknown component rejection,
  executable prop rejection, extra request fields, deterministic trees,
  bounded collection query subset, and safe structured rich text.
- PASSED clean browser evidence for complete demo HTML through public NGINX,
  escaped text/order, page title, strict headers/CSP, preview privacy, and no
  browser-visible internal URL or credential.
- PASSED all existing Puck round-trip, editor, Media, authentication, and
  responsive browser scenarios.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- CI-scope `uv run --frozen ruff check services/backend tests/repository
  tests/packaging tests/supply_chain tools migrations`: PASSED.
- CI-scope `uv run --frozen ruff format --check services/backend
  tests/repository tests/packaging tests/supply_chain tools migrations`:
  PASSED; 226 files formatted.
- `uv run --frozen mypy`: PASSED; 203 source files.
- Backend unit suite: PASSED; 380 tests.
- Backend integration suite: PASSED; 106 tests in 446.55 seconds.
- Repository unittest suite: PASSED; 54 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED; 16 diagrams in 3 files.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-071a-final`:
  PASSED; source distribution and wheel built.
- Process `--check` smoke for Control, Editor, Agent, Render, MCP, Media,
  Review, Scheduler, Media-GC, and Bootstrap: PASSED through frozen `uv`.
- `pnpm install --frozen-lockfile`: PASSED with Node `v24.14.1`, pnpm
  `11.22.0`.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED; build, Web/package tests, and contract tests.
- `pnpm build`: PASSED; preview route included in the dynamic route output.
- `pnpm licenses list --json`: PASSED.
- `docker compose config --quiet`: PASSED.
- Clean `slaif071a` Compose build/start, verifier, and smoke: PASSED. The
  final smoke reported `compose-smoke: OK`, 8 browser projects, 39 compose
  policy tests, Render public/preview/auth secret policies, role policy,
  recovery, negative bootstrap, Apache syntax, and edge checks.
- The disposable `slaif071a` containers/networks/volumes were removed after
  evidence collection.

## GitHub CI / required checks

Fresh implementation-head CI run `32766580091` and CodeQL run `32766580103`
were observed for literal head `bd4679aa3ee78f41dc54b9270a5b28e2951e0091`.
All completed checks are successful, with none pending, failed, cancelled,
skipped, or missing:

- SUCCESS: Repository policy
- SUCCESS: Detect supported languages
- SUCCESS: Analyze (actions), Analyze (python), Analyze (javascript-typescript),
  and CodeQL aggregate
- SUCCESS: Node contracts
- SUCCESS: Python 3.12, 3.13, and 3.14 quality/package
- SUCCESS: Foundation PostgreSQL 14, 15, 16, 17, and 18
- SUCCESS: Compose and edge packaging
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review

The first CI attempt at `e2148f9…` failed only on three fixture line-length
diagnostics in `tests/packaging/test_compose_policy.py`. The bounded
format-only repair is `bd4679a…`; the fresh full-head rerun is green. One
initial local browser run exposed stale E2E expectations for the new canonical
demo page and a test-fixture project allowlist; both were repaired within the
071-a test/edge scope, and the final local smoke passed.

## Documentation and dependencies

Updated README, API, deployment, security, database connection/role, and
testing documentation to distinguish implemented canonical/preview rendering
from planned review/promotion/publication/browser-worker/media-finalization
work. No production dependency, lockfile, hosted service, migration before
032, or license policy change was introduced.

## Scope and safety confirmations

- Product scope: bounded 071-a only.
- Review snapshots/freeze/accept/discard/promotion/publication: NOT implemented.
- Browser-worker automation/source inspection/screenshots/responsive sweeps:
  NOT implemented.
- Public media finalization, Media GC, dynamic News vertical, nested route or
  broad localization claims: NOT implemented.
- Extra objective PR: NO; PR #62 is the sole Objective 071 PR.
- Secrets, cookies, session proofs, capabilities, and database locators were
  not printed or committed.
- Production systems/data: NOT accessed.
- Merge/auto-merge: NO.
- Worktree: CLEAN after implementation push; the only later report file will
  be added as the report-only child.

## Report publication

Implementation head SHA: `bd4679aa3ee78f41dc54b9270a5b28e2951e0091`

Report publication commit: SELF

The report-only commit must have the implementation head above as its sole
first parent, contain only this report, be pushed to PR #62, and be verified as
the remote PR head before the exact response FIFO `OK` is sent.

RESULT=COMPLETE

# OAP Coding-Agent Report — 068-c

## Work order

- Identifier: `068-c`; work-order file: `oap/orders/068-c-minimum-editor-style-csp-and-proof.md`
- Numeric objective: `068`
- PR mode: `CONTINUE_SAME_PR`
- Objective PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59)

## Status

COMPLETE

`RESULT=COMPLETE`

## Executive summary

Completed the human-approved 068-c continuation on PR #59. The authenticated
Puck editor now receives the minimum observed style-only CSP exception,
limited to the exact site/page editor route; scripts remain nonce-bound and
public/unrelated surfaces remain strict. The real Compose browser path creates
an empty page through the API only, adds Sections through the visible Puck
drawer, visibly reorders them, saves through the visible button, reloads, and
proves normalized persisted records. The Editor client now supplies
idempotency keys for those visible mutations.

The PostgreSQL boundary now carries and rechecks the route permission key in
every Editor COW mutation transaction. Workspace resolution is serialized for
concurrent site/human requests. New real-role integration coverage proves
overlay/canonical behavior, replay/mismatch, rollback, wrong-site/human,
forged/revoked/expired context, cleanup, and exact privilege boundaries.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#59](https://github.com/ulfe-lmi/slaif-agent-site/pull/59) — `OPEN`
- Base/head: `main` / `oap/068-puck-editor`
- Starting remote 068-b report head: `82790bd4692c0f2d80c4f70062687ace5900a069`
- Implementation head SHA: `04fffbe03dd1cbf6b1a3c43d7dad412f7b0c7008`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (to be verified via GitHub)
- Implementation commit pushed before report: `04fffbe03dd1cbf6b1a3c43d7dad412f7b0c7008`
- Implementation first parent: `82790bd4692c0f2d80c4f70062687ace5900a069`
- New objective PR this turn: `NO`; existing PR amended: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Added the scoped NGINX `map` and Apache `LocationMatch` editor policy with
  `style-src-attr 'unsafe-inline'` and
  `style-src-elem 'self' 'unsafe-inline'`; retained nonce-bound self-only
  `script-src` and strict public/unrelated policy.
- Reworked the real Puck E2E path to use visible drawer and pointer gestures,
  explicit save/reload, strict CSP assertions, and the existing zero-error
  browser observer. No component API add/move calls remain in that path.
- Added Editor idempotency keys to the web mutation helper.
- Added permission-key arguments and database-side rechecks to the HUMAN
  workspace assertion, idempotency begin, and idempotency completion
  functions; added deterministic resolver serialization.
- Added real PostgreSQL integration coverage using actual `slaif_control` and
  `slaif_editor_runtime` role pools.
- Updated API, role, deployment, security, and testing documentation to
  distinguish the authenticated Puck style exception from strict public
  rendering.

## Files changed

- `apps/web/src/admin/api.ts`
- `docs/API.md`; `docs/DATABASE_ROLES.md`; `docs/DEPLOYMENT.md`;
  `docs/SECURITY.md`; `docs/TESTING.md`
- `infra/nginx/nginx.conf`; `infra/apache/slaif-agent-site.conf`
- `oap/active`; `oap/orders/068-c-minimum-editor-style-csp-and-proof.md`
- `services/backend/src/slaif_agent_site/control_api/site_authority.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/028_001_human_editor_workspace_envelope.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/editor_api/database.py`
- `services/backend/tests/integration/test_human_editor_workspace.py`
- `tests/e2e/governance.spec.ts`; `tests/packaging/test_edge_contract.py`

## Acceptance-criteria evidence

### Criterion 1 — Minimum authenticated-editor CSP

- PASS. The exact editor route receives only the two observed style directives:
  `style-src-attr 'unsafe-inline'` and
  `style-src-elem 'self' 'unsafe-inline'`.
- PASS. `script-src` remains self plus the request nonce; no `unsafe-eval`,
  wildcard, remote origin, report-only policy, raw CSS, or public-renderer
  relaxation was added.
- PASS. Edge contract tests and the final Compose edge checks verify public,
  API, 404, and unrelated admin policy remains strict.

### Criterion 2 — Real visible Puck add/move/save/reload proof

- PASS. The governance browser contract creates only the empty page through
  the API, then uses the visible Puck drawer and pointer drag to add two
  trusted Sections and the visible canvas to reorder them.
- PASS. It saves once after the first add and again after the add/reorder,
  waits for successful Editor responses, GETs the normalized composition,
  checks two root Sections with order keys `[0, 1]`, reloads, and verifies both
  components remain visible.
- PASS. The observer reports no CSP console violation, unexpected console or
  page error, failed network request, or HTTP error across the editor path.

### Criterion 3 — HUMAN workspace, permission, idempotency, and COW proof

- PASS. Real-role integration uses concurrent Control resolution and proves a
  single active HUMAN workspace; COW context uses the workspace UUID, while a
  forged authentication-session UUID is rejected.
- PASS. Permission, human, site, session, active/expiry, and operation context
  are rechecked inside the database transaction. Revoked membership/session,
  wrong human/site, missing permission, expired workspace, and direct Editor
  table access are rejected.
- PASS. The Editor role writes a workspace overlay while canonical content is
  unchanged; canonical fallback and overlay visibility are both checked.
  Idempotency replay and digest mismatch, forced rollback, and two completed
  HUMAN audit/idempotency records are verified.
- PASS. Final Compose smoke proves one active HUMAN workspace and four-plus
  successful audited/idempotent Editor mutations through the edge path.

### Criterion 4 — Scope and documentation

- PASS. No Agent authority, reviewer/publication authority, canonical
  promotion, physical editorial schema migration, hosted dependency, or extra
  objective PR was added.
- PASS. Durable API, database-role, deployment, security, and testing docs
  record the implemented behavior and the exact CSP exception.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED (`196 files`).
- `uv run --frozen mypy`: PASSED (`184 source files`).
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED (`411 tests`).
- `uv run --frozen pytest services/backend/tests/integration`: PASSED
  (`99 tests`, `424.10s`).
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED; source and
  wheel distributions built.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED
  (`53 tests`).
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED (`16 diagrams`, `202 Markdown files`).
- `npx --yes markdownlint-cli2@0.23.2 '**/*.md'`: PASSED (`0 issues`).
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED
  (`37 tests`).
- The literal system-interpreter process commands `python -m
  slaif_agent_site.* --check` could not import the repository's `src/` package
  from `/usr/bin/python`; the configured frozen equivalents
  `uv run --frozen python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check`
  all PASSED with `CHECK_OK`.
- `node --version`: PASSED (`v24.14.1`).
- `pnpm --version`: PASSED (`11.22.0`).
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED; recursive build, package tests, and contract tests
  passed.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `sudo -n tools/compose/smoke.sh slaif009p`: PASSED end to end, including
  setup/governance/stable-device browser projects, human-editor evidence,
  edge headers/CSP, role and secret policies, Control readiness failure and
  recovery, restart persistence, negative bootstrap, Apache/NGINX syntax, and
  packaging tests.

## GitHub CI / required checks

Observed on implementation head `04fffbe03dd1cbf6b1a3c43d7dad412f7b0c7008`
before report publication:

- SUCCESS: Analyze (actions)
- SUCCESS: Analyze (javascript-typescript)
- SUCCESS: Analyze (python)
- SUCCESS: CodeQL
- SUCCESS: Dependency review
- SUCCESS: Detect supported languages
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Python 3.12 quality and package
- SUCCESS: Python 3.13 quality and package
- SUCCESS: Python 3.14 quality and package
- SUCCESS: Repository policy
- PENDING: Compose and edge packaging
- PENDING: Foundation PostgreSQL 14
- PENDING: Foundation PostgreSQL 15
- PENDING: Foundation PostgreSQL 16
- PENDING: Foundation PostgreSQL 17
- PENDING: Foundation PostgreSQL 18
- PENDING: Node contracts
- PENDING: Supply-chain evidence

All required checks green at report drafting: `NO`; no remote check failure
was observed. The report-only commit will trigger a fresh remote check set;
strategy must verify that SELF before acceptance.

## Local setup / dependencies

- Used uv `0.12.5` through the frozen project environment, Node `24.14.1`,
  and pnpm `11.22.0`.
- Used passwordless sudo only for disposable local Compose and PostgreSQL
  verification because the executor user lacks Docker-socket group access.
- No production systems, credentials, capabilities, cookies, or real secrets
  were accessed. No dependency or hosted service was added.

## Documentation

Updated `docs/API.md`, `docs/DATABASE_ROLES.md`, `docs/DEPLOYMENT.md`,
`docs/SECURITY.md`, and `docs/TESTING.md` with the implemented workspace,
permission, audit/idempotency, visible Puck, and scoped CSP behavior.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production secrets accessed: `NO`.
- Production systems/data accessed: `NO`.
- Required tests skipped/not run: `NO`; the system-interpreter process
  invocation failed only because it did not load the repository `src/`
  environment, and every process check passed through the frozen environment.
- Scope deviation: `NO`.
- Extra objective PR: `NO`.
- Coding-agent merge: `NO`.
- Activated order/active edited by coding: `NO`; strategic bytes were committed
  unchanged (`oap/active` is exactly `068-c\n`).
- Report commit changes only this report: `YES`.

## Known limitations / blockers

- Remote CI checks listed as PENDING above were not complete when this report
  was drafted; their GitHub result remains authoritative.
- The plain system `python` executable is not configured with this `src/`
  package on the executor; the frozen uv invocation is the passing local
  process-check path.

## Recommended strategic follow-up

Verify the fresh GitHub checks on the report publication commit and perform
the independent strategy review. This coding agent did not merge or select a
next order.

# OAP Coding-Agent Report — 072-d

## Work order

- Identifier: `072-d`; numeric objective: `072`.
- Work-order file:
  `oap/orders/072-d-agent-browser-routes-and-preview-credential.md`.
- PR mode: `AMENDED_EXISTING_PR`.

## Status

PARTIAL

The bounded 072-d Agent-route and browser-preview-credential slice is complete
and verified. Numeric Objective 072 remains PARTIAL because no dispatcher,
worker execution, Playwright worker dependency/image, artifact byte store,
artifact byte retrieval, browser egress confinement, source tooling, or browser
execution E2E exists yet.

## Executive summary

Added capability-authenticated public Agent create/status/artifact-metadata
routes backed by migration 035's durable functions. Create is idempotent,
quota-reserving, and truthfully returns a durable `QUEUED` run; reads are
side-effect free and artifact-byte retrieval is a reserved non-leaking 404.
The fabricated unauthenticated Python browser-worker router was removed.

Added a descriptor-confined file-backed HMAC credential shared only by Agent
and Render, an immutable fully bound short-lived run-token contract, and
migration 036's narrow Render authorization/one-time-nonce function. Web accepts
the credential only in a dedicated browser-preview header and forwards it
server-side under a distinct Render header. Render verifies the signature and
all bindings, consumes/rechecks the nonce under the shared workspace lock, then
projects only the bound COW overlay. Existing human preview and canonical
rendering remain unchanged.

Compose creates the key once and mounts it read-only only into Agent and Render.
Real PostgreSQL tests cover two sites/workspaces/capabilities, revocation and
shared-lock races, exact residue, one-time use, tamper/expiry/binding denial,
and overlay/canonical isolation. PostgreSQL 14–18, clean Compose/edge regression,
supply-chain evidence, and all 20 fresh implementation-head GitHub checks
passed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #66, <https://github.com/ulfe-lmi/slaif-agent-site/pull/66>.
- PR state at report drafting: `OPEN`, non-draft, `MERGEABLE`.
- Base branch: `main`; head branch:
  `oap/072-browser-worker-real-playwright`.
- Starting remote objective head:
  `449eeca6ded72be9f7059443c9a9a2989ebfee24`.
- Starting authoritative remote main:
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- Implementation head SHA:
  `d5bb47107d45435c5bd02973c6b7f0f47622b474`.
- Report publication commit: SELF.
- Remote PR head after report publication: SELF (literal derived and verified
  after publication).
- Implementation commit pushed before report:
  `d5bb47107d45435c5bd02973c6b7f0f47622b474`
  (`feat(browser): wire queued routes and preview credentials`).
- Report parent must equal implementation SHA: yes; verified after publication.
- New PR this turn: no. Existing PR amended: yes. Merge performed: NO.

## Changes made

### Capability-authenticated Agent routes

- Added `POST /api/agent/v1/preview-runs`, `GET
  /api/agent/v1/preview-runs/{run_id}`, and `GET
  /api/agent/v1/preview-runs/{run_id}/artifacts`.
- Reserved `GET
  /api/agent/v1/preview-runs/{run_id}/artifacts/{artifact_id}` but made it return
  a confined 404 even for exact metadata because no byte store exists.
- Required real capability authentication, `preview:inspect`, a bounded
  `Idempotency-Key`, and the extra-forbid `browser-preview/v1` request. Site,
  workspace, delegator, capability limits, operation UUID, run UUID, and
  request digest are trusted/server-derived.
- Added a typed service around migration 035 begin/get/artifact-list functions.
  Reservation is deterministic: screenshot evidence reserves 5 MiB and each
  summary reserves 256 KiB, within capability limits.
- Mapped malformed/key to 400, authentication to 401, scope to 403, invisible
  records to 404, idempotency mismatch to 409, schema/route/target to 422,
  quota/concurrency to 429, and database unavailability to 503.
- Public responses are private/no-store and omit capability/workspace/delegator
  IDs, request digests, tokens, leases, SQL, roles, worker URLs, and foreign
  facts.
- Removed Agent's fabricated `/internal/browser/v1` router and deleted
  `browser_worker/browser_http.py`. No worker route, dispatcher, claim, or
  completion path was added. Production-created runs remain `QUEUED`.

### Run-bound preview credential

- Added an immutable `sbp1` token with fixed HS256 HMAC, audience
  `slaif-render-browser-preview`, type `SLAIF-BROWSER-PREVIEW`, deployment,
  capability/site/workspace/run IDs, normalized route, target, evidence,
  artifact-byte and duration limits, issued-at/expiry, nonce, and key ID.
- Used canonical JSON/base64url serialization, SHA-256 HMAC, and
  `hmac.compare_digest`. Maximum token length is 4096 bytes and maximum lifetime
  is 60 seconds.
- Verifier rejects missing, duplicate, malformed, oversized, unknown algorithm/
  type/version/key/audience, future/expired, wrong-signature, and changed-binding
  tokens. Only a SHA-256 nonce digest is persisted; plaintext credentials are
  never returned or stored.
- Added a neutral committed verifier-facts contract and matching TypeScript
  export. Deterministic token SHA-256 vector is
  `133725d1ed391c0c36dafee52c5cfa9b92ef0dbd731eccf8447eeb7da54593db`.
- Added descriptor-confined `O_NOFOLLOW` key loading. The directory must be
  owned by the service UID and mode 0700; the regular key file must be owned by
  that UID and mode 0400 with exact bounded ASCII key format.
- Agent loads signer readiness, and Render loads verifier readiness. Public
  create does not mint or return a run token; minting remains for a future
  trusted dispatcher immediately before worker submission.

### Migration 036 and Render authorization

- Added only forward migration `036_001_render_browser_preview_authority.py`;
  migrations 006–035 were not edited. Migration 036 is the sole head and
  downgrades to 035.
- Added paired `preview_nonce_digest`/`preview_token_used_at` fields to durable
  browser runs and allowed the append-only `PREVIEW_TOKEN_CONSUMED` audit event.
- Added exact owner-defined, fixed-search-path, `SECURITY DEFINER`
  `control.slaif_render_browser_preview_authorize(...)`, with PUBLIC execution
  revoked and execution granted only to the preview runtime role.
- Under the shared workspace advisory transaction lock, the function rechecks
  exact capability/site/workspace/run/route/target/evidence/artifact/duration
  bindings, active/unexpired `preview:inspect` authority, and `QUEUED|RUNNING`
  state. Consume mode stores one nonce digest/event; projection recheck mode
  requires that same digest within the COW transaction.
- Terminal, foreign, revoked, expired, mismatched, and second-use tokens deny
  without COW residue. Agent, browser worker, and other service roles receive
  no new Render-preview function or relation authority.

### Web, Render, secrets, and Compose

- Web accepts a browser credential only through
  `X-SLAIF-Browser-Preview`, rejects malformed/duplicate credentials and any
  simultaneous human-preview cookie, canonicalizes the full path/query, and
  forwards the token only server-side as `X-SLAIF-Browser-Run-Token`.
- Render requires exactly one human or browser-preview mode. Browser mode
  verifies the expected site/workspace/route binding before database authority
  consumption and COW projection. Human preview semantics are unchanged.
- Extended the one-shot local-secret initializer with an exact browser-signing
  directory/file boundary. Compose's `browser-signing-secret` volume is
  writable only by the initializer and read-only only in Agent and Render.
- Web, browser worker, NGINX, Control, Editor, MCP, Media, Reviewer, Scheduler,
  Media GC, and Bootstrap receive no signing-key mount. The worker remains
  health-only, DB-less, key-less, and unchanged.
- Missing/bad key makes Agent and Render readiness fail closed while canonical
  public rendering remains available; restoring the exact key recovers both.

## Files changed

- CI/Compose: `.github/workflows/ci.yml`, `compose.yaml`,
  `tools/compose/smoke.sh`, `tools/compose/verify.py`, and
  `tools/local_secrets/initialize.py`.
- Web: `apps/web/app/preview/[workspaceId]/[[...sitePath]]/page.tsx`,
  `apps/web/src/sites/render.ts`, and `apps/web/tests/surface.test.mjs`.
- Shared contracts: `packages/browser-tool-contracts/src/index.ts`,
  `packages/browser-tool-contracts/src/browser-preview-credential-v1.json`,
  `packages/browser-tool-contracts/tests/index.test.ts`, and
  `services/backend/src/slaif_agent_site/browser_contracts.py`.
- Agent/backend: `services/backend/src/slaif_agent_site/agent_api/app.py`,
  `agent_api/browser_http.py`, `agent_api/browser_service.py`,
  `agent_api/config.py`, `agent_api/database.py`,
  `browser_preview_credentials.py`, and `errors.py`; deleted
  `browser_worker/browser_http.py`.
- Database/Render: `services/backend/src/slaif_agent_site/db/alembic/versions/036_001_render_browser_preview_authority.py`,
  `db/privileges.py`, `render_api/app.py`, `render_api/config.py`,
  `render_api/projection.py`, and `render_api/site_http.py`.
- Backend tests: new `test_agent_browser_http.py`,
  `test_render_browser_preview.py`, and `test_browser_preview_credentials.py`;
  updated browser-control, bootstrap, control-database, full-stack, Agent-config,
  foundation-contract, health-app, and Render API tests.
- Packaging tests: `tests/packaging/test_compose_policy.py`,
  `test_compose_smoke_contract.py`, and `test_local_secrets.py`.
- Documentation: `docs/API.md`, `docs/AUTHORIZATION.md`,
  `docs/CONFIGURATION.md`, `docs/DATABASE_BOOTSTRAP.md`,
  `docs/DATABASE_CONNECTIONS.md`, `docs/DATABASE_ROLES.md`,
  `docs/DEPLOYMENT.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`,
  `docs/SERVICE_AUTHORITY.md`, `docs/TESTING.md`, and
  `migrations/alembic/README.md`.
- Strategic transcript committed unchanged:
  `oap/orders/072-d-agent-browser-routes-and-preview-credential.md` and
  `oap/active`.
- Dependency and lock files changed: none.

## Acceptance-criteria evidence

### Criterion 1 — Durable public Agent routes

- Result: PASSED.
- Real HTTP created one `QUEUED` run with exact counts `(run=1,
  idempotency=1, artifact=0, event=1)`. Same-key/same-body replay returned the
  byte-equivalent public body and retained those counts; changed-body replay
  returned 409 and retained the same counts.
- Missing/invalid key returned 400, unknown request fields returned 422,
  missing scope returned 403, and quota denial returned 429 with exact zero
  residue `(0,0,0,0)`.
- Status remained `QUEUED` across a fresh Agent app lifespan. Status and empty
  artifact-list reads did not change counts. Artifact byte retrieval returned
  404. Revoking the capability changed subsequent status to the current auth
  failure without mutating the retained run.
- Two sites/workspaces/capabilities, random/foreign runs and artifacts, expired
  capability, revoked/expired workspace, and archived site were exercised.
  Foreign capability denial and same-workspace foreign binding both retained
  `(0,0,0,0)`.
- A create blocked behind the shared workspace lock, observed revocation after
  lock acquisition, returned non-leaking 404, and left exact zero residue.
- Agent public-route reads produced no browser event, idempotency record, quota
  mutation, or foundation COW operation. The fake internal browser routes return
  404.

### Criterion 2 — Truthful no-worker behavior

- Result: PASSED.
- Production app wiring starts no dispatcher/background task, performs no
  claim/complete call, and cannot mark a public run RUNNING or terminal.
- Public and clean-Compose create/poll journeys both observed durable `QUEUED`,
  including after Agent restart. Artifact metadata remained empty and byte
  retrieval remained 404.
- Agent health/readiness describes Agent plus signer/database readiness and does
  not claim browser-worker execution readiness.

### Criterion 3 — Bound file-backed credential

- Result: PASSED.
- Deterministic signer/verifier tests covered exact vector/parity, signature,
  each changed binding, future/expiry/TTL, unknown/duplicate facts, oversized
  and malformed tokens, and descriptor-confined key generation/loading.
- The public create body/headers/response and persisted browser rows contain no
  plaintext token. Database proof records only one nonce digest and one
  consumption timestamp/event.
- Compose proves directory mode 0700, file mode 0400, exact key format, and
  denial to an unrelated UID. Mount-policy tests prove initializer-only write
  and Agent/Render-only read-only access.

### Criterion 4 — Web/Render browser-preview verification

- Result: PASSED.
- A real signed browser token projected only its bound workspace overlay through
  Render; canonical content remained unchanged. Existing human preview still
  projects through its existing cookie/session path.
- One-time use produced exactly one nonce digest and one
  `PREVIEW_TOKEN_CONSUMED` event. Replay, terminal run, tamper, expiry, changed
  capability/run/route/target/evidence/artifact/duration, foreign workspace/
  site, and wrong/mutually-exclusive Web headers deny without leakage.
- Revocation between initial consume and the COW transaction recheck waited on
  the shared workspace lock, failed closed, and left no COW change or operation
  residue. The token authorizes no Control/Editor/Agent/Media endpoint.

### Criterion 5 — Exact secret and service boundary

- Result: PASSED.
- Static and clean runtime inspection prove the isolated signing volume is
  absent from every service except initializer, Agent, and Render; it is
  read-only in the two runtime services. Existing DB/service secret mounts and
  the NGINX-only published-port boundary remain intact.
- Renaming the key and restarting produced 503 readiness for Agent and Render
  while canonical `/` remained 200. Restoring the key recovered both readiness
  endpoints.
- Browser worker source/image/package, dependency set, DB-less authority,
  health-only behavior, and key/artifact-volume absence remain unchanged.

## Local verification

- `uv --version`: PASSED — exact `uv 0.12.5`.
- `uv lock --check`: PASSED — no lock change.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 239 files formatted.
- `uv run --frozen mypy`: PASSED — 216 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 471 tests in 16.03 seconds.
- `uv run --frozen pytest services/backend/tests/integration`: final PASSED —
  111 tests in 526.61 seconds.
- First full-integration attempt: FAILED — 110 passed/1 failed because the new
  tamper test changed only insignificant base64 padding bits. The test was fixed
  to change a significant signature character; the complete 111-test rerun
  passed. Product validation was not weakened.
- Focused Render browser-preview integration test after adding explicit terminal
  run denial: PASSED.
- Local PostgreSQL browser/Agent/Render matrix: final PASSED — 29 focused tests
  per version on PostgreSQL 14–18. Successful durations were PostgreSQL 14
  289.16 seconds, 15 265.60 seconds, 16 284.01 seconds, 17 236.64 seconds, and
  18 221.65 seconds.
- First matrix attempt: PostgreSQL 14/15/16/17 passed; PostgreSQL 18 had 28
  passed/1 failed because a pre-existing lease test used a fixed 1.1-second
  sleep under parallel load. It was changed to wait for the database's actual
  `lease_expires_at <= CURRENT_TIMESTAMP` fact.
- Matrix retry: PostgreSQL 14/16/17/18 passed; PostgreSQL 15 had 28 passed/1
  failed because a 30-second test token was minted before parallel negative
  cases and expired before the intended lock wait. The race token is now minted
  immediately before that race; an isolated PostgreSQL 15 rerun passed all 29.
  Production token TTL and verification were unchanged.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — wheel and
  sdist.
- `node --version`: PASSED — Node 24.x.
- `pnpm --version`: PASSED — exact `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED.
- `pnpm test`: PASSED — browser contract package 22 tests and Web 9 tests; all
  other workspace/root tests passed.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED — inventory produced; no dependency
  change.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED — 54
  tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED — 40
  tests.
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: PASSED —
  29 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files; 237
  Markdown files scanned.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 231 Markdown files,
  zero issues.
- `uv run --frozen python -m slaif_agent_site.<process> --check` for Control,
  Editor, Agent, Render, MCP, Media, Review Worker, Scheduler, Media GC, and
  Bootstrap: PASSED — all ten returned `CHECK_OK`; no listener or mutation was
  started.
- `python tools/compose/verify.py --root .`: PASSED.
- `python -m tools.supply_chain.policy validate`: PASSED.
- `sudo env PATH="$PATH" sh tools/compose/smoke.sh slaif071oap072d`: PASSED —
  clean 15-service stack, all nine existing Playwright projects, exact secret/
  mount/topology checks, public NGINX capability create/poll, exact 1:1:1
  run/idempotency/event count, restart-stable `QUEUED`, missing-key readiness
  failure/canonical survival/recovery, Apache/NGINX syntax, existing human
  preview/media/login/recovery regression, and full disposable cleanup.
- Final `sh tools/supply_chain/run.sh <temporary>/evidence`: PASSED —
  reproducibility, inventory/notices, six image SBOM/scan sets, checksums, zero
  critical and 51 policy-accepted high findings. Evidence:
  `/tmp/tmp.YYlaELNuVu/evidence`.
- During the final supply-chain run, the second Web image build attempt hit a
  transient socket failure; the existing bounded retry succeeded on attempt
  2/3 and the complete evidence gate passed. No output or policy was skipped.

## GitHub CI / required checks

State observed for implementation head
`d5bb47107d45435c5bd02973c6b7f0f47622b474`: all 20 reported checks completed
successfully; all required checks green at drafting: yes.

- `Repository policy`: SUCCESS.
- `Node contracts`: SUCCESS.
- `Python 3.12 quality and package`: SUCCESS.
- `Python 3.13 quality and package`: SUCCESS.
- `Python 3.14 quality and package`: SUCCESS.
- `Foundation PostgreSQL 14`: SUCCESS.
- `Foundation PostgreSQL 15`: SUCCESS.
- `Foundation PostgreSQL 16`: SUCCESS.
- `Foundation PostgreSQL 17`: SUCCESS.
- `Foundation PostgreSQL 18`: SUCCESS.
- `Compose and edge packaging`: SUCCESS.
- `Supply-chain evidence`: SUCCESS.
- `Markdown`: SUCCESS.
- `Mermaid`: SUCCESS.
- `Dependency review`: SUCCESS.
- `Detect supported languages`: SUCCESS.
- `Analyze (actions)`: SUCCESS.
- `Analyze (python)`: SUCCESS.
- `Analyze (javascript-typescript)`: SUCCESS.
- `CodeQL`: SUCCESS.

The report-only SELF commit may trigger fresh checks; strategy independently
verifies SELF.

## Local setup / dependencies

- Used the exact existing uv 0.12.5, Node 24.x, pnpm 11.22.0, PostgreSQL
  14–18, Docker, and existing Playwright toolchain.
- Used passwordless sudo only for disposable Docker matrix/Compose access.
  Disposable PostgreSQL containers, Compose services, networks, and volumes
  were removed.
- No production dependency, Python lock, Node lock, browser-worker package,
  Playwright dependency/binary, hosted service, account-bound runtime, artifact
  store, or worker runtime image was added.

## Documentation

Updated API, authorization, configuration, database bootstrap/connections/roles,
deployment, operations, security, service-authority, testing, and Alembic docs.
They distinguish the implemented Agent routes and Render credential verifier
from deferred dispatch, worker execution, Playwright, artifact bytes/retrieval,
network confinement, source tools, and browser execution E2E.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no. Production systems/data accessed: no.
- Real capability, cookie, DB URL, signing key, plaintext run token, nonce,
  artifact URL, or private preview credential printed/committed: no; tests and
  Compose use fake disposable values.
- Required tests skipped/not run: no. All observed failures and retries are
  recorded above.
- Scope deviation: no. Browser-worker source/image/package, Playwright,
  dispatch/claim, artifact volume/bytes/retrieval, browser networks, source
  crawling, review/promotion/publication, and browser execution were not added.
- Extra objective PR: NO. Coding-agent merge/auto-merge/close: NO.
- Activated order/active edited by coding agent: NO; exact strategy-authored
  bytes were committed unchanged.
- Earlier migrations/orders/reports edited: no.
- Report commit changes only this report: yes (verified after commit).

## Known limitations / blockers

- Browser worker remains a health-only, DB-less stub with no signing key,
  Playwright dependency/browser binary, internal execution route, artifact
  volume, or dispatch input.
- Agent creates durable runs but no production component claims them, so they
  remain truthfully `QUEUED`. Artifact metadata stays empty and byte retrieval
  stays 404 until a future ordered worker/artifact implementation.
- The signing and Web/Render verification boundary is implemented and proven,
  but production token minting is deliberately not wired because the future
  trusted dispatcher does not yet exist.
- No source crawling, network confinement, responsive sweep, browser execution
  E2E, publication, or artifact GC exists in this round.
- Numeric Objective 072 therefore remains PARTIAL by order. The bounded 072-d
  slice has no blocker.

## Recommended strategic follow-up

Strategy may independently review this route/credential/Render-lock boundary
and choose whether a later same-PR Objective 072 order should implement the
confined dispatcher/real Playwright worker and private artifact bytes. Coding
makes no next-order, acceptance, merge, or release decision.

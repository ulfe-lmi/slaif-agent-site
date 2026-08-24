# OAP Coding-Agent Report — 070-a

## Work order

- Identifier: `070-a`
- Work-order file: `oap/orders/070-a-media-binary-upload-immutable-store.md`
- Numeric objective: `070`; round: `070-a`
- PR mode: `CREATED_NEW_PR`
- Objective: replace the metadata-only media placeholder with a real
  human-authenticated, edge-routed, workspace-aware immutable binary Media
  vertical.

## Status

COMPLETE

## Executive summary

Implemented the first real private Media vertical and created exactly one
fresh objective PR, [#61](https://github.com/ulfe-lmi/slaif-agent-site/pull/61),
from the verified `origin/main` SHA. The service now accepts bounded multipart
PNG/JPEG uploads through NGINX, authenticates the human session/CSRF/site/
permission context, stages and validates bytes, publishes a digest-only
immutable object, and registers the reference in the server-selected HUMAN
workspace through COW, idempotency, and HUMAN audit functions. Authorized GET
streams verified bytes with trusted headers and canonical fallback.

The fake Editor metadata-only register route was removed. The dedicated Media
database pool, role, isolated locator, migration wrappers, local store,
Compose volume ownership handoff, edge limits, negative tests, documentation,
and real PostgreSQL/edge/Compose proof are included. The implementation-head
GitHub checks are all green. No merge was performed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#61](https://github.com/ulfe-lmi/slaif-agent-site/pull/61)
- PR state: `OPEN`, non-draft, `MERGEABLE`, `CLEAN`
- Base/head: `main` / `oap/070-immutable-media-store`
- Starting remote SHA: `76fee6d3e233a3909b8ab303d7f563216d86e468`
- Implementation commits pushed before report:
  - `336f9fcb96dc65de98be54405837bbe3fe1c01ea` — implementation, exact
    activated order and `oap/active` transcript bytes
  - `7a0ee3f2fb9c769bd24e74695f673ec6d685f22b` — Compose named-volume
    ownership handoff and formatting/test correction
- Implementation head SHA: `7a0ee3f2fb9c769bd24e74695f673ec6d685f22b`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- New PR this turn: YES, exactly one
- Same PR amended: NO
- Merge performed: NO

## Changes made

- Added the Media service application, lifespan-owned pool, fixed identity
  validation, configuration, auth/CSRF adapter, bounded multipart parser, and
  authorized upload/content routes under the existing `/media/` proxy.
- Added local immutable `MediaStore` behavior:
  - bounded chunk streaming to private staging;
  - actual PNG/JPEG signature sniffing with declared-type agreement;
  - empty/unknown/spoofed/SVG/traversal/control/oversized input rejection;
  - SHA-256 digest-only keys of the form
    `sha256/{first-two}/{next-two}/{64-hex-digest}`;
  - exclusive same-filesystem publication, no overwrite, restrictive modes,
    no symlink following, existing-object integrity verification, and staging
    cleanup on validation/storage failure.
- Added migration `030_001_media_service_surface.py` with only the bounded
  Media control idempotency/audit tables and owner-defined authorization,
  registration, and lookup wrappers. Registration reasserts site, human,
  session, permission, and HUMAN workspace context and serializes same-site /
  digest races with a transaction-scoped advisory lock.
- Added fixed `slaif_media_login` / `slaif_media` pool wiring and exact
  function-only grants. No table DML, base/change-table access, generic SQL,
  publication, reviewer, Agent, Editor, bootstrap, or GC authority was added.
- Removed Editor `POST /api/editor/v1/sites/{site_id}/media/register` and its
  fake filename-derived request contract. Existing Editor media list/get,
  metadata patch, and reference-delete routes remain.
- Added isolated Media secret initialization and a networkless initializer
  handoff that prepares the named private media volume as `0700` for UID 10001;
  Media service and Media GC share only that named volume.
- Added NGINX/Apache request-body limits, Compose policy checks, and an actual
  edge smoke upload/read byte comparison.
- Updated API, configuration, database connection/role, deployment,
  operations, security, service-authority, testing, and user-facing docs with
  private workspace semantics, storage/DB failure behavior, limits, backup
  expectations, and explicit non-goals.

## Files changed

- `compose.yaml`
- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/DATABASE_CONNECTIONS.md`
- `docs/DATABASE_ROLES.md`
- `docs/DEPLOYMENT.md`
- `docs/OPERATIONS.md`
- `docs/SECURITY.md`
- `docs/SERVICE_AUTHORITY.md`
- `docs/TESTING.md`
- `docs/user-manual/README.md`
- `infra/apache/slaif-agent-site.conf`
- `infra/nginx/nginx.conf`
- `oap/active`
- `oap/orders/070-a-media-binary-upload-immutable-store.md`
- `services/backend/src/slaif_agent_site/content_model/media_models.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/030_001_media_service_surface.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/editor_api/media_http.py`
- `services/backend/src/slaif_agent_site/media_service/__init__.py`
- `services/backend/src/slaif_agent_site/media_service/__main__.py`
- `services/backend/src/slaif_agent_site/media_service/app.py`
- `services/backend/src/slaif_agent_site/media_service/auth.py`
- `services/backend/src/slaif_agent_site/media_service/config.py`
- `services/backend/src/slaif_agent_site/media_service/database.py`
- `services/backend/src/slaif_agent_site/media_service/media_http.py`
- `services/backend/src/slaif_agent_site/media_service/multipart.py`
- `services/backend/src/slaif_agent_site/media_service/store.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_media_service.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_health_apps.py`
- `services/backend/tests/unit/test_media_store.py`
- `services/backend/tests/unit/test_route_policy.py`
- `tests/packaging/test_compose_policy.py`
- `tests/packaging/test_local_secrets.py`
- `tools/compose/smoke.sh`
- `tools/compose/verify.py`
- `tools/local_secrets/initialize.py`

No new production dependency or lockfile change was needed; the existing
permissive-license stack and frozen foundation dependency remain in use.

## Acceptance-criteria evidence

### Criterion 1 — Real validated bytes and HUMAN workspace COW

- PASSED. Real PostgreSQL and a real local filesystem test create a human,
  site, active HUMAN workspace, session, and CSRF token. A multipart PNG is
  uploaded through the Media app with server-derived context.
- The response and owner inspection assert the exact uploader, site, safe
  original filename, sniffed `image/png`, byte count, SHA-256 digest, and
  digest-only storage key. The object is a regular mode-0600 file.
- The workspace-visible reference is returned through the COW path while the
  canonical base remains unchanged (`content.media_asset_base` count remains
  zero for the uploaded reference; the separately seeded canonical reference
  remains one).

### Criterion 2 — Authorized workspace/canonical byte reads

- PASSED. Authenticated GET of the workspace-created reference returns the
  exact PNG bytes through the Media route. The separately seeded canonical
  reference is readable by canonical fallback without changing state.
- The focused integration test asserts trusted `Content-Type`, exact
  `Content-Length`, SHA-256 ETag, `X-Content-Type-Options: nosniff`, and
  `Cache-Control: private, no-store`. The edge Compose smoke repeats upload
  and read through NGINX and compares the files byte-for-byte.

### Criterion 3 — Replay, deduplication, mismatch, and race boundary

- PASSED for the exercised upload paths. Same idempotency key replay returns
  the identical response with `X-Media-Replay: true`; a different key carrying
  the same bytes returns the same media UUID; a changed request under the same
  key returns stable `409 IDEMPOTENCY_MISMATCH`. Owner inspection confirms the
  expected two idempotency/audit records and no canonical mutation.
- The registration wrapper takes a trusted digest/key and uses a
  transaction-scoped advisory lock for deterministic same-site/digest race
  serialization; physical publication reuses an already verified digest object
  without overwrite. The focused proof exercises sequential replay/deduplication
  and the migration/CI PostgreSQL matrix validates the real wrapper.

### Criterion 4 — Site/workspace isolation and fail-closed lookup

- PASSED. A wrong-site GET is limited to a non-leaking `403`/`404` response and
  does not disclose the media UUID. Direct base-table and workspace reads are
  denied to the Media login; forged and wrong-site COW wrapper contexts fail
  with PostgreSQL errors.
- Media pool inspection asserts the exact database, fixed login as both
  `session_user` and `current_user`, and sole reachable product role
  `slaif_media`.

### Criterion 5 — Existing Editor metadata/reference semantics

- PASSED for the retained Editor contract. The fake register route and model
  were removed, while Editor list/get/metadata-patch/reference-delete routes,
  route policy, existing COW mutation behavior, and production Editor
  integration regressions remain green in the full backend suite.
- The Media lookup wrapper uses the same COW overlay plus canonical fallback and
  the store tests assert that reference operations do not mutate immutable
  bytes. Physical unlink/GC is not introduced; later GC remains the owner of
  orphan retention deletion.

### Criterion 6 — Validation, auth, cleanup, and fail-closed errors

- PASSED for the implemented validation/error paths. The real integration
  proof covers missing idempotency key, spoofed declared MIME, SVG, traversal
  filename, wrong site, malformed authorization context, and direct privilege
  denials. Staging is empty after rejected requests.
- Unit store proof covers actual-signature sniffing, private digest publication,
  reuse, corrupt-existing-object rejection, and no-overwrite behavior. The
  streaming parser bounds total upload/field/metadata input and removes
  staging on parser, validation, storage, and exception paths.
- Auth uses strict session/CSRF cookie parsing and server-side human session,
  active site, membership, permission, and workspace resolution; HTTP errors do
  not expose paths, roots, or storage details.

### Criterion 7 — Pool/grants/context cleanup boundary

- PASSED. The app-owned Media pool uses fixed credentials and exact named
  wrappers only. Direct `control.workspace` and `content.media_asset_base`
  reads fail; forged session/workspace/site wrapper calls fail; COW context is
  opened and cleaned around registration. The full backend unit/integration
  and PostgreSQL 14–18 gates remain green.

### Criterion 8 — Edge/Apache/Compose privacy boundary

- PASSED. NGINX routes `/media/` to Media service and has no media volume;
  Apache has the bounded proxy route and no media volume. Compose static and
  running policy checks assert that only Media service and Media GC mount the
  named `media-data` volume, with Media running as UID 10001 and the
  networkless initializer preparing ownership.
- Fresh local `tools/compose/smoke.sh slaif009070` passed all 38 smoke tests,
  all service health checks, browser contracts, restart/recovery fixtures,
  media secret policy, and `media-e2e: OK edge=nginx upload=validated-private-read=byte-identical`.

## Byte/store state machine

`authenticate human + CSRF + site + permission + active HUMAN workspace` →
`stream bounded multipart chunks to 0600 staging` → `hash/count/signature
validate/normalize metadata` → `atomically publish or verify/reuse
sha256/{first-two}/{next-two}/{digest}` → `COW metadata + idempotency + HUMAN
audit transaction` → `authorized COW lookup/canonical fallback` → `verified
regular-file stream with trusted headers`.

Filesystem publication precedes PostgreSQL registration. A database failure may
leave an inaccessible, unreferenced private digest object for later Media GC;
the API never presents that orphan as a reference. Rejected/cancelled/
failed staging is removed, object keys never contain client filenames, object
files are mode `0600`, and private store directories are mode `0700`. No
absolute host filesystem path, secret, capability, cookie, or locator is
returned in an HTTP response or log.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen mypy`: PASSED.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED; 415 tests at the implementation commit.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 102
  tests at the implementation commit; the focused real Media test is included.
- `uv run --frozen pytest services/backend/tests/integration/test_media_service.py`:
  PASSED; 1 real PostgreSQL/filesystem test.
- `uv run --frozen pytest services/backend/tests/unit/test_media_store.py`:
  PASSED; 3 tests.
- `uv run --frozen pytest tests/packaging/test_local_secrets.py tests/packaging/test_compose_policy.py`:
  PASSED; 19 tests after the volume ownership correction.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED.
- `python -m compileall -q tools tests/repository services/backend/src`:
  PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED;
  54 tests.
- `python tools/check_repository.py`: PASSED.
- `python tools/check_mermaid.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 211 files, zero
  issues.
- Frozen process `--check` smoke for all ten backend modules: PASSED.
- Node 24.14.1 / pnpm 11.22.0 gates (`install --frozen-lockfile`, lint,
  format:check, typecheck, test, build, licenses): PASSED.
- `sudo -n tools/compose/smoke.sh slaif009070`: PASSED; clean real stack,
  edge media upload/read, restart/recovery, Apache/NGINX, secret, browser,
  governance, and 38 smoke tests.
- `git diff --check`: PASSED.

The first local Compose attempt used the invalid project name `slaif070aa` and
was correctly rejected by the existing safety allowlist. A valid clean debug
run then exposed the named-volume root ownership issue; the networkless
initializer ownership handoff was added, focused tests passed, and the fresh
clean smoke run passed. The earlier implementation-head CI run also exposed
formatting and the same Compose health issue; both were corrected before the
literal implementation head reported here.

## GitHub CI / required checks

Observed for literal implementation head
`7a0ee3f2fb9c769bd24e74695f673ec6d685f22b` before report drafting:

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
- SUCCESS: Foundation PostgreSQL 14
- SUCCESS: Foundation PostgreSQL 15
- SUCCESS: Foundation PostgreSQL 16
- SUCCESS: Foundation PostgreSQL 17
- SUCCESS: Foundation PostgreSQL 18
- SUCCESS: Compose and edge packaging
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review

All required implementation-head checks were green at report drafting. The
report-only commit may trigger fresh checks; strategy independently verifies
the resulting `SELF` head.

## Local setup / dependencies

Used the existing frozen `uv` environment, PostgreSQL test fixtures, Node
24.14.1, pnpm 11.22.0, Docker Compose, and the repository's existing local
Playwright/browser setup. Routine local setup used the already-authorized sudo
Docker path. No production credentials, production systems, hosted service,
new runtime dependency, lockfile dependency, or account-bound service was
added. Existing `agent-cow-postgresql==0.2.0` public APIs remain the foundation
boundary.

## Documentation

Updated `docs/API.md`, `docs/CONFIGURATION.md`,
`docs/DATABASE_CONNECTIONS.md`, `docs/DATABASE_ROLES.md`,
`docs/DEPLOYMENT.md`, `docs/OPERATIONS.md`, `docs/SECURITY.md`,
`docs/SERVICE_AUTHORITY.md`, `docs/TESTING.md`, and
`docs/user-manual/README.md`. These documents distinguish implemented private
workspace upload/read behavior from future GC, publication, Agent upload,
transcoding, public serving, and distributed storage.

## Safety and scope confirmations

- Unrelated files changed: NO. All 42 implementation/transcript paths are
  within the activated order; the second implementation commit corrected only
  the in-scope Media volume handoff, formatting, docs, and tests.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: NO for the claimed verification sets; every
  corrected invocation and the earlier failed CI/smoke states are recorded.
- Scope deviation: NO. No Agent upload, public URL, object store, GC,
  transcoding, publication, promotion, or architecture/constitution edit was
  added.
- Extra objective PR: NO; exactly PR #61 exists for 070.
- Coding-agent merge: NO.
- Activated order/`oap/active` edited: NO; exact strategic bytes were committed
  unchanged.
- Report commit changes only this report: YES.

## Known limitations / blockers

- The explicitly ordered non-goals remain: no Agent upload, public/anonymous
  URL, image transformation, SVG sanitization, antivirus, PDF/video/audio
  processing, distributed/object-store backend, physical Media GC, publication,
  reviewer finalization, or renderer integration.
- Filesystem publication and PostgreSQL registration are intentionally not one
  atomic transaction; unreferenced private objects are reserved for later GC.
- Strategy remains the sole acceptance, merge, release, and next-order
  authority. This report does not claim merge or production readiness.

## Recommended strategic follow-up

Independently verify the report `SELF` child, its first-parent relationship to
the literal implementation SHA, and report-head check state, then choose merge,
abandon, or a same-PR continuation. No next objective is selected by the
coding agent.

RESULT=OK

# OAP Coding-Agent Report — 070-b

## Work order

- Identifier: `070-b`
- Work-order file: `oap/orders/070-b-media-security-concurrency-and-lifecycle-proof.md`
- Numeric objective: `070`; round: `070-b`
- PR mode: `AMENDED_EXISTING_PR`
- Scope: continue Objective 070 on PR #61 and close the concrete security,
  lifecycle, concurrency, and evidence gaps recorded by 070-a.

## Status

COMPLETE

## Executive summary

Continued only PR #61 and hardened the existing private Media vertical without
broadening its routes or non-goals. Media workspace authorization now validates
trusted COW context and acquires the shared workspace advisory lock before
mutable authorization checks. NGINX/Apache retain the strict 1 MiB global
body limit and scope the 100 MiB-plus-bounded-overhead allowance to `/media/`
only.

The local store is now directory-FD confined with `O_DIRECTORY|O_NOFOLLOW`,
private mode/type/ownership checks, bounded destination-race handling, staged
byte/object/directory fsync ordering, no replacement or recursive retry, and
descriptor-verified reads. Multipart ownership is BaseException/cancellation
safe, rejects ambiguous lengths/headers and malformed boundaries, and keeps
fields and total input bounded.

Real PostgreSQL proof now uses ordinary memberships rather than administrator
bypass and covers the lock race, ordinary RBAC, two workspaces and two sites,
concurrent same-digest dedupe, Editor patch/delete retention, post-publish DB
failure orphans, parser cancellation, and GET stream closure. No merge was
performed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#61](https://github.com/ulfe-lmi/slaif-agent-site/pull/61)
- PR state: `OPEN`, non-draft, `MERGEABLE`, `CLEAN`
- Base/head: `main` / `oap/070-immutable-media-store`
- Starting remote report head: `e459509d9fec2184584113f41b2f0cb957cb5e5a`
- Implementation commits this continuation:
  - `95b80fa6ecb6f34dfb4f9e3f9cff84f901319cd3` — hardening implementation,
    proof, docs, and exact 070-b order/active transcript
  - `c286beaa8ce085bcc972ecb3341ce0506a364b21` — typed GET stream-closure
    proof correction
- Implementation head SHA: `c286beaa8ce085bcc972ecb3341ce0506a364b21`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- New PR this turn: NO
- Same PR amended: YES
- Merge performed: NO

## Changes made

- Added migration `031_001_media_security_hardening` for the lock-ordered Media
  workspace assertion and repaired the existing Editor media update/delete
  functions for unambiguous COW operation. The 030 source function was also
  kept correct for clean installs, while 031 upgrades existing 070-a installs.
- Corrected Editor media JSONB serialization so real PATCH metadata reaches the
  COW function as typed JSONB.
- Replaced path-based publication/read behavior with descriptor-relative,
  no-follow traversal of root, staging, `sha256`, digest prefixes, and final
  object. Valid immutable files remain mode `0600`; private directories remain
  mode `0700`.
- Added staged-byte fsync, object fsync, containing-directory fsync, staging
  removal/fsync, hardlink-count/type/mode/digest/size checks, bounded two-pass
  destination races, and close-on-success/failure read descriptors.
- Made multipart cleanup unconditional for cancellation/disconnect/BaseException
  paths; rejected duplicate/unknown headers, duplicate fields, negative or
  ambiguous Content-Length, overlong fields/headers, malformed delimiters, and
  adversarial chunk boundary cases.
- Restored 1 MiB global edge limits and added `105119744` bytes only to the
  `/media/` location: 100 MiB file limit plus 256 KiB bounded framing overhead.
- Added ordinary-RBAC, isolation, concurrent dedupe, Editor lifecycle, orphan,
  two-connection lock-race, parser, store, descriptor, fsync, edge, and GET
  stream-closure evidence.
- Updated API, configuration, role, deployment, security, and testing docs.

## Files changed

- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/DATABASE_ROLES.md`
- `docs/DEPLOYMENT.md`
- `docs/SECURITY.md`
- `docs/TESTING.md`
- `infra/apache/slaif-agent-site.conf`
- `infra/nginx/nginx.conf`
- `oap/active`
- `oap/orders/070-b-media-security-concurrency-and-lifecycle-proof.md`
- `services/backend/src/slaif_agent_site/content_model/service.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/023_001_media_functions.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/030_001_media_service_surface.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/031_001_media_security_hardening.py`
- `services/backend/src/slaif_agent_site/media_service/config.py`
- `services/backend/src/slaif_agent_site/media_service/media_http.py`
- `services/backend/src/slaif_agent_site/media_service/multipart.py`
- `services/backend/src/slaif_agent_site/media_service/store.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_media_security_lifecycle.py`
- `services/backend/tests/integration/test_media_service.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_media_multipart.py`
- `services/backend/tests/unit/test_media_store.py`
- `tests/packaging/test_edge_contract.py`
- `tools/compose/smoke.sh`

No runtime dependency, lockfile, hosted service, database engine, role grant
family, or production credential source was added.

## Acceptance-criteria evidence

### Criterion 1 — Freeze/revocation lock ordering

- PASSED. `test_media_workspace_assertion_waits_for_revoke` creates ordinary
  `user_a` / `site_a` / `workspace_a` fixture identities, holds the exact
  `hashtextextended(workspace_id::text, 280)` transaction lock on one real
  PostgreSQL connection, starts Media assertion on a second connection,
  observes `wait_event_type=Lock`, `wait_event=advisory`, `state=active`, then
  deactivates the membership while the assertion waits.
- Releasing the lock makes the assertion deny. The baseline COW operation list
  is unchanged and `control.media_idempotency` plus `audit.media_mutation` both
  remain zero for the race workspace. The membership is restored after proof.

### Criterion 2 — Route-scoped edge limits

- PASSED. NGINX and Apache use global 1 MiB limits and `/media/`-only
  `105119744` byte limits. Static tests assert no global 100 MiB relaxation.
- Clean local Compose sends a 1 MiB-plus-one body to Media and receives the
  upstream authentication response, while Control, Editor, Agent, MCP, and
  Web receive edge `413`; it reports
  `edge-body-limit: OK media=route-allowance non-media=413 global=1MiB`.
- Fresh GitHub Compose/edge packaging also passed the same expanded smoke.

### Criterion 3 — Descriptor-confined immutable store

- PASSED. Root, staging, `sha256`, both digest-prefix directories, and final
  objects are opened relative to verified descriptors with
  `O_DIRECTORY|O_NOFOLLOW`; private owner/mode/type checks reject replacement,
  symlink, FIFO, directory, hardlink-count, corrupt, wrong-size, and wrong-key
  states.
- Publication fsyncs staged bytes, the linked object, modified object
  directory, staging removal, and modified staging directory. Existing valid
  objects are rehashed and reused; destination races use two bounded attempts,
  never recursive `publish()` retry or replacement.
- Store tests cover three symlink positions, two non-regular final types,
  same-size corruption, wrong read contracts, readiness root failure,
  descriptor closure, restrictive modes, and fsync hook evidence.

### Criterion 4 — Cancellation-safe bounded multipart/error matrix

- PASSED. Multipart cleanup is unconditional for parser validation,
  `CancelledError`, stream exception, and upload cancellation after parsing but
  before publication. A disconnected GET generator closes its verified object
  descriptor in `finally`.
- The 14 focused store/parser tests split every initial boundary/header/signature
  position across chunks and cover duplicate/unknown headers, duplicate fields,
  negative/ambiguous Content-Length, truncation, exact size overflow, malformed
  delimiter, filename traversal, and cancellation staging cleanup.
- Stable route classes remain: missing/invalid idempotency 400, authentication
  401, CSRF/permission non-leaking 403/404, malformed content 422, body size
  413, missing/corrupt reference 404, and only real store/database failures
  503. No path, root, or parser state is returned.

### Criterion 5 — Ordinary RBAC and site/workspace isolation

- PASSED. The new lifecycle fixture creates ordinary `SITE_EDITOR` users
  `user_a` and `user_b`, a `VIEWER`, `site_a`, `site_b`, and active HUMAN
  workspaces `workspace_a`, `workspace_b`, `workspace_c`, and
  `workspace_viewer`; it creates no platform-administrator bypass.
- Missing auth, wrong CSRF, viewer access, and foreign workspace/site reads are
  denied without disclosing IDs. The same PNG uploaded by `user_a` in site A
  and `user_b` in site B has one shared digest/storage key but distinct metadata
  UUID/site/user/filename/alt/JSON references.
- The real fixed Media identity and direct denials for control workspace and
  content base-table reads remain asserted by the Media integration.

### Criterion 6 — Concurrent dedupe and idempotency/audit state

- PASSED. The real Media integration launches two concurrent same-workspace,
  same-digest uploads with distinct keys. Both return 201 and the same visible
  media UUID/storage key. The physical object is one digest object; the exact
  workspace counts are four idempotency rows and four HUMAN audit rows after
  the original, new-key replay, and two concurrent requests.
- Existing same-key replay and changed-request mismatch remain covered, and
  the content registration advisory lock serializes same-site/digest races.

### Criterion 7 — Real Editor patch/delete and byte retention

- PASSED. The lifecycle fixture calls the public Editor PATCH route for the
  ordinary Site Editor, changes only alt/JSON, and asserts digest, key, size,
  and byte content remain unchanged. Public Editor DELETE creates a workspace
  tombstone; Media GET for A returns 404, the object remains byte-identical,
  and the valid site-B reference still returns the same bytes and metadata.
- The 031 migration repairs ambiguous legacy media update/delete SQL and keeps
  the existing Editor COW envelope/permissions intact.

### Criterion 8 — Post-publish DB failure orphan

- PASSED. A real Media app/pool is subclass-injected to fail registration after
  store publication. A distinct valid PNG digest object remains mode-0600 and
  private; `content.media_asset_base` and the key's idempotency row remain zero,
  no audit completion exists, staging is empty, and a guessed Media GET is 404.
  The object is documented as a later-GC orphan, not as a rolled-back
  transaction or public reference.

### Criterion 9 — Retained authority and edge contracts

- PASSED. Fixed `slaif_media_login`/`slaif_media` identity, named wrapper-only
  grants, COW context checks, canonical fallback, isolated secret ownership,
  no extra mounts, proxy-only `/media/`, NGINX byte comparison, and prior
  Agent/Editor/Puck behavior remain green. No Agent upload, public URL, GC,
  transform, object store, publication, or reviewer authority was introduced.

## Lock and byte state machines

Authorization now follows:

`server-selected session/workspace/operation` → `parse UUID settings` →
`workspace advisory transaction lock` → `active account/site/membership/
permission/expiry checks` → `COW mutation or read`.

Upload follows:

`ordinary human + CSRF` → `bounded multipart staging` → `signature/hash/size
validation` → `descriptor-confined fsync publication or verified reuse` →
`COW metadata/idempotency/HUMAN audit`; filesystem publication remains honestly
separate from PostgreSQL registration, so only an inaccessible private orphan
can remain after injected DB failure.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED; 211 files.
- `uv run --frozen mypy`: PASSED; 199 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED; 426 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 104
  tests at implementation head `95b80fa`; the changed stream-proof test was
  rerun separately at `c286bea`.
- Focused Media/store/parser/lifecycle tests: PASSED; 22 unit tests, 3
  lifecycle/media integration tests, and the post-correction Media integration
  rerun passed.
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py`:
  PASSED; 23 tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-070b`: PASSED.
- All ten frozen backend process `--check` commands: PASSED.
- Repository compilation/unittest/policy checks: PASSED; 54 repository tests.
- `python tools/check_mermaid.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 213 files, zero
  issues.
- `python tools/compose/verify.py`: PASSED.
- `sudo -n tools/compose/smoke.sh slaif009070`: first attempt was blocked by a
  transient BuildKit missing local snapshot during image export; the exact
  clean rerun passed with 39 smoke tests, route-scoped edge checks, NGINX
  Media E2E, recovery/governance/browser tests, and Apache/NGINX syntax.
- `git diff --check`: PASSED.
- Local Node gates were already green for 070-a and the unchanged Node surface
  passed the fresh current-head GitHub Node contract job; no Node source or
  lockfile changed in 070-b.

## GitHub CI / required checks

Observed for literal implementation head
`c286beaa8ce085bcc972ecb3341ce0506a364b21`:

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

The earlier 070-b CI run at `6ea698a` failed only because the new proof cast
was typed as `AsyncIterator`, which lacks `anext`/`aclose` in mypy. The safe
test-only `AsyncGenerator` correction is `c286bea`; all fresh checks listed
above are green. No failed check is being claimed as pass.

## Local setup / dependencies

Used the existing frozen `uv` environment, disposable local PostgreSQL,
Docker Compose, Node 24.14.1, pnpm 11.22.0, and existing Playwright/browser
fixtures. Routine local setup used the authorized sudo Docker path. No
production credentials/systems, hosted service, new dependency, lockfile
change, or account-bound service was used.

## Documentation

Updated API error classes, Media edge/body-limit configuration, role/migration
authority, deployment edge policy, security lock/store guarantees, and testing
evidence. The docs retain the explicit non-goals and distinguish private
post-publish orphans from transactional rollback.

## Safety and scope confirmations

- Unrelated files changed: NO. The 28 implementation/transcript paths are
  within 070-b; the final `c286bea` changes only the in-scope stream-proof
  typing.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: NO for the claimed current-head GitHub and
  local sets; the transient BuildKit retry and corrected mypy attempt are
  explicitly recorded.
- Scope deviation: NO. No route/functionality expansion or prohibited
  dependency/authority was added.
- 070-a order/report or historical OAP artifacts edited: NO.
- Extra objective PR: NO; PR #61 only.
- Coding-agent merge: NO.
- Activated 070-b order/`oap/active` edited: NO; exact strategic bytes committed
  unchanged.
- Report commit changes only this report: YES.

## Known limitations / blockers

- Explicit non-goals remain: no Agent upload, public/anonymous URL, HEAD/range,
  CDN/signed URL, object store/distributed backend, transforms, SVG
  sanitization, antivirus, document/video/audio processing, physical GC,
  publication, review, promotion, or renderer integration.
- Orphan cleanup and retention remain later Media GC work; this round proves
  the private orphan contract but does not delete it.
- Strategy remains sole acceptance, merge, release, and next-order authority.

## Recommended strategic follow-up

Independently verify this report `SELF` child, its first parent and exact remote
PR head, then choose merge, abandon, or another same-PR continuation. No next
objective is selected by the coding agent.

RESULT=OK

# OAP Coding-Agent Report — 070-c

## Work order

- Identifier: `070-c`
- Work-order file: `oap/orders/070-c-media-migration-and-cleanup-proof.md`
- Numeric objective: `070`; round: `070-c`
- PR mode: `AMENDED_EXISTING_PR`
- Scope: close the migration-immutability, exact multipart field,
  resource-cleanup, authorization-state, and transaction-residue gaps found in
  strategic review while preserving 070-a/070-b.

## Status

COMPLETE

## Executive summary

Restored every pre-070 migration byte, including `023_001_media_functions.py`,
and kept the Editor update/delete repair exclusively in forward migration
`031_001`. The final migration graph has one head, `031_001`; the exact base
diff contains only the 070 additions `030_001` and `031_001`.

The multipart parser now requires exactly one filename-bearing part named
`file`, with explicit wrong-name, duplicate, and filename-less rejection.
The lock-race owner pool closes in a `finally`, the application pool is reused
after success/failure/denial/stream paths, and the orphan proof compares valid
before/after metadata, idempotency, audit, and COW state rather than using an
impossible nullable predicate. Ordinary Viewer upload denial and revoked,
revoked-workspace, expired-workspace, and archived-site public-route denials
are now exercised.

No new PR or merge was made.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#61](https://github.com/ulfe-lmi/slaif-agent-site/pull/61)
- PR state: `OPEN`, non-draft, `MERGEABLE`, `CLEAN`
- Base/head: `main` / `oap/070-immutable-media-store`
- Starting remote report head: `d6f14cfe911d000d518a822c9832729b171fcfd4`
- Implementation commits this continuation:
  - `d68471b80c4c3b255cec2297a4e02b5de009cc5d` — exact 070-c order/active
    transcript
  - `c3b21aaf17551d358b5a94d30b9ad50291db8e6c` — migration restoration,
    multipart, cleanup, lifecycle proof, and docs
  - `932c69219786fb8d5d1a82a0bfa2d6d590ccb095` — shallow-checkout-independent
    pre-070 migration fingerprints
- Implementation head SHA: `932c69219786fb8d5d1a82a0bfa2d6d590ccb095`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- New PR this turn: NO
- Same PR amended: YES
- Merge performed: NO

## Changes made

- Restored `023_001_media_functions.py` exactly to the Objective 070 base
  bytes; no historical migration was modified in the final implementation.
- Retained the unambiguous Editor media update/delete repair in existing
  forward migration `031_001`, with one linear Alembic head.
- Required exact multipart form name `file` for the filename-bearing part.
- Added focused wrong-name, duplicate-file, filename-less-file, delimiter,
  bounds, split-chunk, and staging-cleanup proof.
- Closed the dedicated lock-race owner pool in `finally`; retained app-owned
  Media/Editor/failing-test app lifespan cleanup and normal pool reuse.
- Added public-route Viewer upload denial and lifecycle checks for revoked
  session, revoked workspace, expired workspace, and archived site.
- Replaced the orphan `resource_id IS NULL` assertion with exact before/after
  counts and COW operation-list equality for the injected DB-failure request.
- Updated the API/testing docs to state the exact `file` field contract and
  negative lifecycle evidence.

## Files changed

- `docs/API.md`
- `docs/TESTING.md`
- `oap/active`
- `oap/orders/070-c-media-migration-and-cleanup-proof.md`
- `services/backend/src/slaif_agent_site/db/alembic/versions/023_001_media_functions.py`
- `services/backend/src/slaif_agent_site/media_service/multipart.py`
- `services/backend/tests/integration/test_media_security_lifecycle.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `services/backend/tests/unit/test_media_multipart.py`

The final implementation diff against the Objective 070 base reports only
added migration files `030_001_media_service_surface.py` and
`031_001_media_security_hardening.py` in the migration directory. No runtime
dependency or lockfile changed.

## Acceptance-criteria evidence

### Criterion 1 — Immutable migration history and linear head

- PASSED. Exact local command
  `git diff --exit-code 76fee6d3e233a3909b8ab303d7f563216d86e468...HEAD -- services/backend/src/slaif_agent_site/db/alembic/versions/023_001_media_functions.py`
  returned zero.
- `git diff --name-status 76fee6d3e233a3909b8ab303d7f563216d86e468...HEAD -- services/backend/src/slaif_agent_site/db/alembic/versions`
  reports only added 030 and 031; no pre-070 file is changed. The repository
  assertion fingerprints all 24 pre-070 migration files from the base.
- `migration_heads()` returns exactly `('031_001',)`. Clean upgrade,
  bootstrap, validation, downgrade, and rebuild coverage remains green.

### Criterion 2 — Exact multipart `file` contract

- PASSED. The parser accepts one filename-bearing `name="file"` part and
  rejects filename-bearing `wrong`, duplicate `file`, and filename-less `file`
  forms. All rejected cases leave no staging file.
- Existing unknown/duplicate metadata fields, malformed headers/boundaries,
  traversal/control names, empty/unsupported/spoofed/SVG content, size bounds,
  negative/ambiguous lengths, and cancellation cleanup remain covered.
- The parser continues streaming bounded chunks; it does not call an
  unbounded request-body read or retain the complete upload.

### Criterion 3 — Dedicated resource and context cleanup

- PASSED. The two-connection lock test now closes its explicitly created owner
  pool in `finally`; Media, Editor, and injected-failure app lifespans close
  their owned pools. No private asyncpg pool attribute is used by the proof.
- Public Media requests reuse the normal app pool after successful upload,
  parser rejection, post-publish DB failure, lock denial, GET completion, and
  stream close. COW operation lists remain unchanged on read/failure paths.
- Parser `CancelledError` propagation, staging handles, stream generators,
  verified object descriptors, tasks, and test HTTP clients are closed on the
  relevant pass/failure/cancellation paths.

### Criterion 4 — Ordinary authorization/lifecycle negatives

- PASSED. Ordinary `SITE_EDITOR` users `user_a`/`user_b`, a `VIEWER`, sites A/B,
  and HUMAN workspaces A/B/C are used; no platform-administrator bypass is
  involved.
- Viewer GET and Viewer upload both fail with the established non-leaking
  outcome; Viewer workspace idempotency/audit counts remain zero. Missing auth,
  wrong CSRF, foreign workspace/site, and forged-context denials remain green.
- A revoked `user_b` session cannot read its site-B reference. A `REVOKED`
  workspace, expired workspace, and `ARCHIVED` site each deny public Media
  access/upload before durable mutation; staged state and the rejected key's
  idempotency row remain absent.

### Criterion 5 — Exact private orphan residue

- PASSED. Before the injected post-publication registration failure, the test
  records the tuple of base metadata count for the orphan digest, total
  workspace idempotency count, total workspace audit count, and the workspace
  COW operation list. After failure, the same tuple and operation list are
  exactly equal; the exact `injected-db-failure` idempotency key count is zero.
- The distinct digest object exists privately with exact bytes, staging is
  empty, no metadata/base row or audit completion was added, and authenticated
  guessed-ID GET remains 404. This is a later-GC orphan, not a claimed atomic
  filesystem/database rollback.

### Criterion 6 — Retained 070-a/070-b functionality

- PASSED. Existing concurrent same-digest proof still returns one visible UUID
  and one physical object with exact four-row idempotency/audit counts for its
  successful/replay/concurrent sequence. Editor PATCH/DELETE byte retention,
  ordinary site/workspace isolation, fixed Media identity/grant denials,
  canonical fallback, edge scoping, and stream descriptor closure remain green.
- No Agent upload, anonymous/public media, range/HEAD, transform, object store,
  GC, publication, review/promotion, schema redesign, dependency, or trust
  expansion was added.

## Migration, multipart, and cleanup state

Migration state is:

`pre-070 bytes unchanged` → `030 Media surface` → `031 forward hardening`
→ `one Alembic head 031_001`.

Multipart state is:

`one bounded filename-bearing file part named file` → `bounded metadata fields`
→ `signature/hash/size validation` → `staging ownership transfer`; every
reject/cancellation path closes/removes staging, while publication transfers
ownership to the immutable store.

Orphan state is:

`validated private object published` → `injected DB registration failure` →
`no metadata/idempotency/audit/COW delta` → `private digest retained for later
GC only`.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED; 211 files.
- `uv run --frozen mypy`: PASSED; 199 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED; 428 tests at implementation head `c3b21aa`; migration fingerprint
  test rerun passed after `932c692`.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 104
  tests at implementation head `c3b21aa`.
- `uv run --frozen pytest services/backend/tests/integration/test_media_security_lifecycle.py services/backend/tests/integration/test_media_service.py`:
  PASSED; 3 focused integration tests after the 070-c changes.
- `uv run --frozen pytest services/backend/tests/unit/test_media_multipart.py services/backend/tests/unit/test_media_store.py`:
  PASSED; 15 focused parser/store tests.
- `uv run --frozen pytest services/backend/tests/integration/test_database_bootstrap.py`:
  PASSED as part of the complete integration run and prior migration-focused
  run; 23 bootstrap tests.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-070c`: PASSED.
- All ten frozen backend process `--check` commands: PASSED.
- Repository compile, policy, and repository unittest checks: PASSED; 54 tests.
- `python tools/check_mermaid.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 215 files, zero
  issues.
- `sudo -n tools/compose/smoke.sh slaif009070`: first clean run had one
  transient mobile-Chromium settings-read failure; the identical clean retry
  passed all 39 smoke tests, Media NGINX byte E2E, edge-body-limit checks,
  recovery/governance/browser matrix, secret policy, and Apache/NGINX syntax.
- `git diff --check`: PASSED.
- Local Node gates were not rerun in 070-c; no Node source or lockfile changed.
  Fresh final-head GitHub Node contracts passed.

## GitHub CI / required checks

Observed for literal implementation head
`932c69219786fb8d5d1a82a0bfa2d6d590ccb095` before report drafting:

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

An earlier c3 CI run failed only because the first migration immutability test
invoked `BASE...HEAD` in a shallow GitHub checkout where BASE was unavailable.
That test was changed to committed base-byte fingerprints; the fresh final-head
CI/CodeQL runs listed above are all green. No skipped, pending, cancelled, or
missing final-head check is claimed as pass.

## Local setup / dependencies

Used the existing frozen `uv` environment, disposable local PostgreSQL,
Docker Compose, Node 24.14.1, pnpm 11.22.0, and the existing Playwright
fixtures. Routine setup used the authorized sudo Docker path. No production
credential/system, hosted service, dependency, lockfile, database engine, or
account-bound runtime was added.

## Documentation

Updated `docs/API.md` and `docs/TESTING.md` for the exact multipart field and
negative lifecycle/residue evidence. Existing 070 security, configuration,
deployment, role, and operations documentation remains retained from 070-b.

## Safety and scope confirmations

- Unrelated files changed: NO. The final continuation paths are limited to the
  active order's migration proof, parser, lifecycle test, fingerprint test,
  docs, and strategic transcript.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: YES, local Node commands were not rerun;
  unchanged Node scope was covered by fresh final-head GitHub CI. The first
  Compose mobile-Chromium attempt and c3 shallow-base CI failure are recorded
  exactly and were corrected/retried safely.
- Scope deviation: NO.
- Extra objective PR: NO; PR #61 only.
- Coding-agent merge: NO.
- Activated 070-c order/`oap/active` edited: NO; exact strategic bytes were
  committed unchanged.
- 070-a/070-b orders and reports edited: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

- Explicit non-goals remain: no Agent upload, public/anonymous media, range/
  HEAD, transforms, object store/distributed backend, physical GC/retention,
  publication, review, promotion, renderer integration, or dependency/trust
  expansion.
- Private orphan retention remains later Media GC work; this round proves its
  exact residue contract but does not delete the object.
- Strategy remains sole acceptance, merge, release, and next-order authority.

## Recommended strategic follow-up

Independently verify this report `SELF` child, its first parent and exact remote
PR head, then choose merge, abandon, or another same-PR continuation. No next
objective is selected by the coding agent.

RESULT=OK

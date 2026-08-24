# OAP Coding-Agent Report — 070-d

## Work order

- Identifier: `070-d`
- Work-order file: `oap/orders/070-d-media-cross-worker-publication-race-proof.md`
- Numeric objective: `070`; round: `070-d`
- PR mode: `AMENDED_EXISTING_PR`
- Scope: close the genuine cross-worker same-digest publication race and the
  related production staging-descriptor reopen gap.

## Status

BLOCKED

## Executive summary

Implemented the bounded 070-d Media fix and deterministic proof on PR #61.
Publication now takes an exclusive POSIX advisory lock on the verified digest
prefix directory with a bounded two-second timeout. Independent MediaStore
instances publishing the same digest wait for the winner to finish staging
unlink/fsync, then verify and reuse the one-link object. Different digest
prefixes progress independently. Production multipart parsing now owns an
`O_CREAT|O_EXCL|O_NOFOLLOW` read/write staging descriptor from creation through
publication, with inode/path revalidation and explicit transfer/discard
ownership.

The focused 21-test store/parser/Media suite passes, and local lint/mypy and
the implementation-relevant checks pass. The round is blocked from
`COMPLETE` because the immutable strategic order itself contains a Markdown
lint defect at line 161 (`#61, then...` is parsed as an invalid ATX heading).
The final GitHub Markdown check fails on that exact order line. Coding cannot
edit activated order bytes or weaken the repository lint policy; strategy must
repair/reissue the strategic artifact in a subsequent handoff.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#61](https://github.com/ulfe-lmi/slaif-agent-site/pull/61)
- PR state: `OPEN`, non-draft, `MERGEABLE`; final CI state is not clean because
  the required Markdown check fails on the activated order
- Base/head: `main` / `oap/070-immutable-media-store`
- Starting remote report head: `4a0109f5fea1c7d482c4c31659f971e4fa347bb2`
- Implementation commits this round:
  - `73d3ae3b91e23bb12f4a72da123215f071d1c618` — exact 070-d order/active
    transcript
  - `50f1f95fb39e0d1eeeaef35521d8bc7361262d9c` — bounded publication lock,
    descriptor-owned staging, focused tests, and docs
- Implementation head SHA: `50f1f95fb39e0d1eeeaef35521d8bc7361262d9c`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after push)
- New PR this turn: NO
- Same PR amended: YES
- Merge performed: NO

## Changes made

- Added a per-digest-prefix `fcntl.flock(LOCK_EX|LOCK_NB)` critical section
  with a bounded two-second acquisition timeout. The verified directory itself
  is the lock primitive, so there is no persistent lock artifact or stale lock
  cleanup path. The lock is released before database registration.
- Rechecked final object presence only after lock acquisition. A missing final
  is linked without replacement, fsynced, and staging is unlinked/fsynced. A
  valid winner is rehashed/verified with mode/link/size/type checks and the
  caller's staging is removed. Suspect states remain fail-closed.
- Added `StagingFile` descriptor ownership. Production multipart writes through
  the pinned descriptor and returns it in `StagedMedia`; publication flushes,
  validates descriptor/path device+inode identity, hashes from the readable
  descriptor, and closes it on every path. Upload cancellation discards the
  transferred staging object safely.
- Added deterministic independent-store threaded race proof, unrelated-prefix
  progress proof, bounded lock timeout, staging path replacement rejection,
  valid reuse, fsync/order, symlink/non-regular/corruption, parser, and
  descriptor cleanup tests.
- Updated security/testing documentation with lock scope/timeout and staging
  ownership semantics.

## Files changed

- `docs/SECURITY.md`
- `docs/TESTING.md`
- `oap/active`
- `oap/orders/070-d-media-cross-worker-publication-race-proof.md`
- `services/backend/src/slaif_agent_site/media_service/media_http.py`
- `services/backend/src/slaif_agent_site/media_service/multipart.py`
- `services/backend/src/slaif_agent_site/media_service/store.py`
- `services/backend/tests/unit/test_media_multipart.py`
- `services/backend/tests/unit/test_media_store.py`

No migration, route, grant, role, dependency, lockfile, service, database, or
trust-boundary change was made.

## Acceptance-criteria evidence

### Criterion 1 — Cross-worker publication race

- PASSED locally for the implementation. Two independent `MediaStore` objects
  open separate staging/directory descriptors and publish the same digest from
  separate threads. Worker A is paused by the existing fsync injection after
  final-link visibility and before staging unlink; worker B remains alive on
  the prefix-directory flock. Releasing A lets both return the same key.
- The final bytes are exact, the final inode has `st_nlink == 1`, both staging
  paths are gone, and a different digest with a different first four digest
  characters completes while A is paused. The lock timeout test returns
  `storage_unavailable` in under one second with only the losing stage removed.
- This is concrete separate-store/descriptor evidence, not the prior single
  asyncio event-loop HTTP gather. A separate checkout replay against old
  `932c692...` was not run; the source-level old defect is the documented
  immediate `st_nlink == 2` loser verification before the winner unlink.

### Criterion 2 — Pinned staging descriptor

- PASSED locally. `create_staging_writer()` opens the random staging entry with
  `O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW` under the verified staging dirfd. Parser
  writes never call `Path.open` for production staging. Publication reopens the
  path only for no-follow inode comparison against the pinned descriptor and
  rejects replacement/symlink mismatch without creating a final object.
- `StagedMedia` ownership transfers exactly once to publication; parser errors,
  cancellation, upload cancellation, publication failure, and normal success
  close/discard the writer appropriately.

### Criterion 3 — Integrity, fsync, and bounded failure behavior

- PASSED in focused tests. Existing final/ancestor symlink, FIFO/directory,
  same-size corruption, wrong digest/key/size, valid reuse, mode, fsync hook,
  descriptor closure, readiness failure, and staging cleanup tests remain green.
- Publication holds only the verified prefix-directory lock, never crosses
  database registration, has no recursive retry, and fails closed on lock
  timeout or suspect object state.

### Criterion 4 — Retained Objective 070 contracts

- PASSED in focused integration and prior accepted suites: exact human auth,
  workspace COW, idempotency/audit, ordinary RBAC, two-site/workspace
  isolation, Editor patch/delete retention, orphan behavior, edge body scoping,
  fixed Media identity/grants, Agent/Editor/Puck behavior, and private local
  storage remain unchanged.
- The final clean local Compose run was not rerun after this small store-only
  amendment; the prior 070-c clean Compose run was not claimed as final-head
  evidence. Fresh final-head GitHub Compose remains pending at report drafting.

## State transitions

`create verified root/staging dirfd` → `open exclusive O_NOFOLLOW read/write
stage descriptor` → `stream bounded bytes` → `flush/hash/revalidate pinned
inode` → `flock verified digest-prefix dir <= 2s` → `link no-replace or verify
winner` → `fsync object/dir` → `unlink+fsync caller stage` → `unlock before DB`.

The lock has no filesystem artifact and process exit releases it. The bounded
timeout prevents a hung worker from producing an indefinite request wait.

## Local verification

- `uv run --frozen pytest services/backend/tests/unit/test_media_store.py services/backend/tests/unit/test_media_multipart.py services/backend/tests/integration/test_media_service.py services/backend/tests/integration/test_media_security_lifecycle.py`:
  PASSED; 21 focused tests.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
  for the implementation-relevant scope.
- `uv run --frozen mypy`: PASSED; 199 source files.
- `git diff --check`: PASSED.
- Prior 070-c full unit/integration and clean Compose evidence remains retained
  but is not reclassified as final 070-d Compose evidence.
- Local Node, full backend integration, and final-head full Compose were NOT
  rerun after the store-only amendment; fresh final-head GitHub jobs are the
  authoritative verification in progress.

## GitHub CI / required checks

Observed for literal implementation head
`50f1f95fb39e0d1eeeaef35521d8bc7361262d9c` at report drafting:

- SUCCESS: Repository policy
- SUCCESS: Detect supported languages / CodeQL analyses
- SUCCESS: Node contracts
- SUCCESS: Python 3.12 quality and package
- SUCCESS: Python 3.13 quality and package
- SUCCESS: Python 3.14 quality and package
- SUCCESS: Foundation PostgreSQL 14
- SUCCESS: Foundation PostgreSQL 15
- SUCCESS: Foundation PostgreSQL 16
- SUCCESS: Foundation PostgreSQL 17
- SUCCESS: Foundation PostgreSQL 18
- SUCCESS: Dependency review
- SUCCESS: Mermaid
- FAILURE: Markdown — immutable order line 161, `MD018/no-missing-space-atx`
  for `#61, then the bounded implementation and verification.`
- PENDING: Compose and edge packaging
- PENDING: Supply-chain evidence

The Markdown failure is a strategic transcript/policy blocker, not an
implementation failure. Coding cannot edit the activated order or weaken the
lint gate. No final-head pending check is claimed as pass.

## Local setup / dependencies

Used the existing frozen `uv` environment, disposable PostgreSQL fixtures,
Node/Playwright/Docker setup, and the authorized sudo Docker path. No
production secrets/systems, hosted service, new dependency, lockfile, or
account-bound runtime was accessed or added.

## Documentation

Updated `docs/SECURITY.md` and `docs/TESTING.md` with the per-prefix lock,
bounded timeout, no-artifact semantics, and pinned staging-descriptor proof.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets accessed: NO.
- Production systems/data accessed: NO.
- Required tests skipped/not run: YES — final-head full Compose, Node/local
  full backend rerun, and the old-code checkout replay are recorded as not run;
  current final-head remote jobs are separately marked pending/success/failure.
- Scope deviation: NO.
- Extra objective PR: NO; PR #61 only.
- Coding-agent merge: NO.
- Activated 070-d order/`oap/active` edited: NO; exact strategic bytes committed
  unchanged.
- 070-a/070-b/070-c orders and reports edited: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

- BLOCKER: strategy-authored `oap/orders/070-d-media-cross-worker-publication-race-proof.md`
  line 161 is invalid under the repository’s required Markdownlint policy.
  The exact repair must be made by strategy in immutable orchestration content;
  coding will not alter the activated order or bypass the required check.
- Explicit non-goals remain: no Agent upload, public media, transforms, object
  store, GC/retention, publication, review/promotion, or renderer work.

## Recommended strategic follow-up

Repair or republish the malformed strategic 070-d order line while preserving
its intended bytes/scope, then issue the next exact control handoff. Strategy
should independently review the bounded implementation and this BLOCKED
report before deciding whether to continue, accept the evidence, or abandon the
round. No next objective is selected by the coding agent.

RESULT=BLOCKED

# OAP Work Order — 070-c

## Objective

Continue Objective 070 on PR #61. Preserve the accepted 070-a/070-b Media
vertical and close only the concrete migration-immutability, multipart field,
resource-cleanup, authorization-state, and transaction-residue proof gaps found
in strategic review. Restore every pre-objective migration byte, keep the repair
in the new forward migration, strengthen the missing negative evidence, and do
not broaden Media functionality. Do not merge.

## Verified starting state and strategic findings

- Numeric objective: `070`; round: `070-c`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #61 on
  `oap/070-immutable-media-store`. Do not create another PR.
- Begin from verified remote 070-b report head
  `d6f14cfe911d000d518a822c9832729b171fcfd4`; its only parent is final
  implementation head `c286beaa8ce085bcc972ecb3341ce0506a364b21` and it
  changes only
  `oap/reports/070-b-media-security-concurrency-and-lifecycle-proof.md`.
- PR #61 is open, non-draft, mergeable, based on remote main
  `76fee6d3e233a3909b8ab303d7f563216d86e468`; reconcile live GitHub and
  all report/commit identities before editing. Some report-head CI was still
  pending at strategic review; do not treat prior green implementation-head CI
  as fresh evidence for this round.
- 070-b is genuine progress and must be retained: shared workspace lock before
  mutable checks, route-scoped edge limits, descriptor-confined immutable
  storage and fsync, cancellation-safe bounded multipart parsing, ordinary
  membership fixtures, concurrent digest dedupe, real Editor patch/delete,
  private orphan behavior, cross-workspace/site tests, and stream descriptor
  closure.
- Finding 1 — 070-b modified already-merged migration
  `services/backend/src/slaif_agent_site/db/alembic/versions/023_001_media_functions.py`
  to qualify update/delete columns even though new forward migration 031 also
  contains the appropriate repair. Historical migration bytes are immutable;
  the repair belongs only in 031.
- Finding 2 — the real lock-race test creates a dedicated `slaif_owner` pool
  without a robust close path. This can leak a pool on pass or failure and makes
  the cleanup claim incomplete.
- Finding 3 — the multipart parser requires one filename-bearing part but does
  not require that part's form name to be exactly `file`; a differently named
  filename part can be accepted despite the stated contract.
- Finding 4 — ordinary RBAC proof denies Viewer GET but does not explicitly
  deny Viewer upload, and the new lifecycle evidence does not exercise the
  representative expired/revoked-session and inactive/expired workspace/site
  authority states claimed by 070-b.
- Finding 5 — the post-publication DB-failure orphan audit assertion uses an
  impossible `resource_id IS NULL` predicate against a non-null column. It does
  not establish that audit/idempotency/COW state stayed unchanged for that
  exact operation/digest. Cleanup/pool-context assertions should use direct
  before/after evidence, not an impossible predicate or private pool internals.

## Bounded scope and non-goals

Change only the existing Objective 070 migration, Media parser/store/service,
focused test, and directly necessary documentation paths needed to close the
findings above. Preserve all exact routes, fixed identities, grants, private
digest store, PNG/JPEG support, COW metadata, edge scoping, and 070-a/070-b
non-goals.

- No Agent upload, anonymous/public media, renderer integration, range/HEAD,
  transformations, object store, retention/GC implementation, publication,
  review/promotion, schema redesign, dependency addition, new service, or trust
  expansion.
- No broad database grants, credential sharing, client-selected COW context,
  raw SQL endpoint, executable content, or extra edge volume mount.
- Do not edit activated 070-a/070-b orders or their published reports. Do not
  rewrite or amend report commits.
- No extra PR and no merge.

## 1. Restore immutable migration history

- Restore
  `023_001_media_functions.py` byte-for-byte to the current remote-main/base
  version. Do not merely make its behavior equivalent.
- Keep the update/delete ambiguity repair exclusively in the new forward
  Objective 070 migration 031. If 031 needs adjustment, preserve one linear
  Alembic head and repeat clean upgrade/current/downgrade-upgrade coverage.
- Add a deterministic repository/migration assertion that the PR diff has zero
  changes to every migration that existed on Objective 070's base; new 030/031
  remain the only migration additions for this objective. At minimum report the
  exact `git diff --exit-code 76fee6d...HEAD -- .../023_001_media_functions.py`
  result and the migration-head result.
- Do not generate a corrective migration for any unrelated historical file.

## 2. Exact multipart `file` contract

- Require exactly one multipart form part named `file`, with a valid filename,
  in addition to the existing metadata contract. A filename-bearing part under
  any other name is an unknown field and must fail closed with the established
  non-leaking malformed-input response.
- Continue rejecting duplicate `file` parts, filename-less `file`, duplicate or
  unknown form fields, malformed headers/boundaries, and all existing invalid
  content cases. Do not buffer the complete request body.
- Add focused tests for a filename-bearing wrong-name part, duplicate `file`,
  filename-less `file`, and valid chunk-split `file`; prove staging closure and
  zero persistent state for all rejected cases.

## 3. Deterministic pool, stream, and context cleanup

- Close every explicitly created test pool, especially the lock-race owner
  pool, in robust `finally`/async-context cleanup that also runs on assertion,
  cancellation, and database failure. Do not reach into asyncpg private
  attributes to manufacture evidence.
- Prove the application-owned Media pool remains reusable after representative
  upload success, parser rejection, post-publish DB failure, lock/revocation
  denial, GET completion, and GET cancellation/disconnect. A fresh checkout
  must observe no open transaction and no retained COW
  site/workspace/operation setting.
- Keep `CancelledError` propagation unchanged; close request streams, staging
  handles, object descriptors, responses, tasks, and pools on every path. Tests
  must not leave pending tasks, unclosed response bodies, or unclosed pools.

## 4. Missing authorization/lifecycle negative proof

Using real PostgreSQL, real public Media HTTP routes, fixed `slaif_media`
identity, and ordinary non-administrator memberships:

- prove a Viewer or otherwise ordinary user lacking `media:upload` cannot
  upload and leaves zero metadata/COW/idempotency/audit state;
- prove a representative revoked or expired human session cannot upload or
  read, as applicable;
- prove inactive/expired workspace and inactive site are denied, with the
  shared-lock ordering retained and zero durable residue;
- retain missing authentication, wrong/missing CSRF, missing read permission,
  wrong workspace/site, forged context, and two-workspace/two-site isolation
  proof without relying on platform-administrator bypass.

Use the product's established non-leaking status outcomes. These tests must
exercise the public application routes, not call owner functions as a
substitute for request authorization.

## 5. Exact private-orphan and residue evidence

- Replace the impossible orphan audit predicate with direct before/after counts
  and exact operation/idempotency/resource correlation. After an induced DB
  registration failure occurring strictly after object publication, prove:
  the exact digest object exists privately; no Media metadata row or COW change
  exists for the operation; no completed idempotency row exists; no audit event
  was added; staging is empty; and authenticated or guessed GET cannot resolve
  the digest without a valid metadata UUID/reference.
- Make the assertion meaningful against actual table constraints. Record exact
  pre/post counts (and operation/idempotency keys where safe) in the report.
- Retain successful upload/concurrent-dedupe exact counts and actual Editor
  PATCH/DELETE byte-retention behavior. Do not implement physical GC.

## 6. Optional race test only if needed for honest coverage

If no deterministic test currently executes the store's bounded
`FileExistsError` publication race branch, add one by controlled syscall/store
injection and prove bounded valid-object reuse with no recursion, overwrite, or
staging leak. Do not introduce production hooks solely for testing if existing
concurrent filesystem evidence genuinely covers the branch; state the exact
evidence either way.

## Acceptance criteria

- The PR has no byte change to migration 023 or any other pre-070 migration;
  the needed behavior is supplied by forward migration 031 with one valid head.
- Multipart accepts exactly one filename-bearing part named `file` and rejects
  alternate/duplicate/missing filename forms without resource or DB residue.
- Every dedicated pool/stream/task/descriptor is closed on pass, failure, and
  cancellation; the app Media pool is reusable with no transaction/COW bleed.
- Ordinary missing-upload permission, revoked/expired session, inactive/
  expired workspace, and inactive site fail closed through public Media routes.
- The private-orphan test proves exact unchanged metadata/audit/idempotency/COW
  state using valid predicates and exact before/after counts.
- All accepted 070-a/070-b functionality, edge isolation, fixed identity/grant
  denials, multi-site/workspace isolation, Editor patch/delete, prior Agent/
  Editor/Puck contracts, and strict non-goals remain green.

## Verification and workflow

Run and report exact focused multipart/store/service tests; real Media lifecycle
and PostgreSQL tests; migration immutability/head/clean upgrade tests; edge and
Compose Media E2E; complete backend integration/quality/package/repository/
privilege/process/security/docs/Node/license gates; PostgreSQL 14–18; and every
fresh GitHub required check on the final report head. Mark every failure,
retry, reused result, skip, and not-run item honestly.

Before implementation, commit/push the exact strategic 070-c order and active
bytes unchanged on the same PR. After implementation and local verification,
commit/push an implementation head. Publish exactly
`oap/reports/070-c-media-migration-and-cleanup-proof.md` as one report-only child
with `Report publication commit: SELF`; verify its literal parent is the
reported implementation-head SHA and the remote path/blob/head match. Signal
exact FIFO `OK` only after the report and claimed remote state exist. Do not
merge.

The immutable report must state result/status, PR/base/branch/all SHAs,
production changes, exact historical-migration diff and Alembic heads,
multipart field matrix, each pool/stream/context cleanup path, ordinary RBAC and
lifecycle outcomes, exact orphan before/after metadata/audit/idempotency/COW
counts, files/dependencies/docs, every local and CI result/intermediate failure,
limitations/non-goals, and no merge/extra PR.

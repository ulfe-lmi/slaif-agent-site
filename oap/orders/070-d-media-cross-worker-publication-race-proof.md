# OAP Work Order — 070-d

## Objective

Continue Objective 070 on PR #61. Preserve the accepted 070-a through 070-c
Media vertical and close one concrete strategic-review blocker: immutable
same-digest publication is not safe under a genuine cross-worker
`FileExistsError` race. Add the smallest production fix and deterministic proof
that independent workers publishing the same valid digest both succeed without
overwrite, corruption, recursion, staging leakage, or an unbounded wait. Also
close the directly related staging-descriptor reopen gap. Do not broaden Media
functionality. Do not merge.

## Verified starting state and source evidence

- Numeric objective: `070`; round: `070-d`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #61 on
  `oap/070-immutable-media-store`. Do not create another PR.
- Begin from verified remote 070-c report head
  `4a0109f5fea1c7d482c4c31659f971e4fa347bb2`; its sole parent is final
  070-c implementation head
  `932c69219786fb8d5d1a82a0bfa2d6d590ccb095` and its sole changed path
  is `oap/reports/070-c-media-migration-and-cleanup-proof.md`.
- PR #61 remains open, non-draft, mergeable, based on remote main
  `76fee6d3e233a3909b8ab303d7f563216d86e468`; report-head CI was still
  running when this continuation was selected. Reconcile live GitHub before
  editing.
- 070-c is genuine and retained: migration 023 is byte-identical to base; 030
  and 031 are the only new migrations; multipart requires exact field `file`;
  ordinary Viewer/lifecycle denials, valid orphan before/after counts, pool
  cleanup, local suites, clean Compose retry, and final implementation-head CI
  are established.
- Hard blocker — `MediaStore.publish()` tests destination absence and creates
  it with `os.link(staging, digest)`. Until the winning worker unlinks staging,
  the valid final inode has `st_nlink == 2`. A losing independent worker that
  receives `FileExistsError` immediately calls `_verify_object()`, which
  requires `st_nlink == 1`, so it can raise `storage_corrupt`/HTTP 503 even
  though the winner is completing a valid publication. The two-iteration loop
  does not retry this path: every branch returns or raises.
- Evidence gap — existing concurrent HTTP requests share one event loop and
  call synchronous `store.publish()` serially; the store unit suite contains no
  deterministic `FileExistsError`/winner-in-progress test. It therefore does
  not falsify the cross-worker race.
- Related confinement gap — production multipart parsing calls
  `create_staging_path()`, which securely creates and closes an exclusive
  descriptor, then reopens the path with ordinary `Path.open("wb")`. The parser
  should write through a descriptor opened under the verified staging dir with
  no symlink following, rather than close and path-reopen the security boundary.

## Bounded scope and non-goals

Change only `media_service/store.py`, the directly coupled multipart/upload
call path if needed, focused Media store/parser tests, and exact documentation
needed to describe publication synchronization. Preserve all routes, database
schema/functions/grants, fixed identities, private volume, object key format,
PNG/JPEG limits, COW/idempotency/audit semantics, edge policy, and prior
Objective 070 behavior.

- No database migration, grant, role, dependency, lockfile, new service,
  object-store backend, GC/retention, public media, transforms, Agent upload,
  publication/review, or renderer work.
- No global process lock, client-controlled lock key, overwrite, recursive
  retry, acceptance of corrupt/hardlinked/symlinked objects, or indefinite
  wait.
- Do not edit activated 070-a/070-b/070-c orders or reports.
- No extra PR and no merge.

## 1. Safe bounded cross-worker publication

- Serialize only the minimum filesystem critical section needed for one digest
  (or at most its verified digest-prefix directory) across independent
  processes/`MediaStore` instances sharing the same private root. A POSIX
  descriptor lock or equivalently strong local-filesystem primitive is
  acceptable; it must be server-derived, confined under/opened from verified
  directory descriptors, and released automatically or robustly on every
  success, exception, cancellation, and process exit.
- Bound acquisition/retry by a documented short timeout/attempt budget. A hung
  live worker must cause a stable private storage-unavailable outcome, not an
  indefinitely blocked request. Do not busy-spin or add recursive retry.
- Once synchronized, recheck the final entry. If absent, publish atomically
  without replacement, fsync object and modified directories, unlink/fsync
  staging, and return. If a valid winner already published it, verify exact
  regular type, owner/mode, final `st_nlink == 1`, size, and digest, remove/fsync
  the loser staging file, and return the identical key.
- Continue failing closed for final/ancestor symlinks, FIFO/device/directory,
  wrong mode/owner/link count/size/digest/key, stale or malformed lock state,
  replaced root, and real storage errors. Never overwrite or repair a suspect
  final object silently.
- If the chosen primitive can leave a lock artifact, prove it cannot become a
  public media object, cannot be redirected by symlink, has private ownership/
  mode, and has safe stale/crash semantics. Prefer no persistent artifact where
  practical.
- Do not hold a filesystem lock across database registration, HTTP streaming,
  or any unrelated digest operation.

## 2. Descriptor-owned staging writes

- Replace the production create-close-path-reopen sequence with a staging
  writer/descriptor opened using the already verified root/staging directory
  descriptor, `O_CREAT|O_EXCL|O_NOFOLLOW`, private mode, and bounded random-name
  collision handling.
- Multipart streaming must write to that pinned descriptor, transfer ownership
  exactly once to publication, and close/remove it on parse error,
  cancellation, disconnect, size/MIME rejection, publication error, or normal
  completion. No raw descriptor/path is exposed in an HTTP response or log.
- Publication must revalidate the staging entry and descriptor/inode contract
  under verified dirfds before final creation. A replaced staging path,
  symlink, hardlink surprise, or descriptor/path inode mismatch must fail closed
  without traversal or overwrite.
- Test/operator helpers may remain ergonomic, but the production parser must
  not use ordinary path-following `Path.open` for the staging write.

## 3. Deterministic race and failure proof

Add focused tests using two independent store instances and separate directory
opens, with threads or processes as needed:

1. deterministically pause worker A after its final entry becomes visible but
   before staging unlink/final `st_nlink == 1`;
2. start worker B with the same bytes/digest and prove it reaches the genuine
   contention path rather than being serialized by one asyncio event loop;
3. release A and prove both calls succeed with the same key, exact bytes/mode,
   one final inode/link, no overwrite, and empty staging;
4. prove a different digest under an unrelated lock scope can still progress;
5. prove bounded timeout/peer-stall behavior returns the stable storage failure
   and cleans only the caller-owned staging file; and
6. retain/retest corrupt final, extra hardlink that does not settle, symlinked
   staging/final/ancestor, FileExists injection, winner crash/release as
   practical, fsync ordering, descriptor closure, valid reuse, and no recursive
   call.

The test must fail against implementation head `932c692...` for the stated
race, or otherwise supply equally concrete evidence of the old defect. Do not
claim the ordinary `asyncio.gather` HTTP test alone is cross-worker proof.

## Acceptance criteria

- Two independent workers publishing the same valid digest cannot produce a
  spurious corruption/503 outcome; both deterministically return the same key.
- Final object creation remains no-replace, private, digest-verified, durably
  synced, one-link, and free of staging residue.
- Lock/retry behavior is narrowly scoped, bounded, crash/release safe, and does
  not weaken corrupt-object or symlink rejection.
- Production multipart writes through a pinned no-follow staging descriptor and
  all ownership/cleanup paths are explicit and tested.
- No schema/grant/dependency/route/trust change occurs; all 070-a through 070-c
  identity, authorization, COW, edge, parser, lifecycle, orphan, Editor, Agent,
  and Puck contracts remain green.

## Verification and workflow

Run and report exact focused store/parser race, symlink, timeout, cancellation,
fsync, and descriptor tests; complete Media integration/lifecycle tests;
complete backend unit/repository/integration/quality/mypy/package/process/
migration/privilege/docs gates; clean Compose/NGINX Media E2E; PostgreSQL
14–18; and every fresh GitHub required check on the final report head. Record
all failures, controlled old-code proof, retries, skips, and not-run items
honestly.

Commit/push the exact strategic 070-d order and active bytes unchanged on
PR #61, then the bounded implementation and verification. Publish exactly
`oap/reports/070-d-media-cross-worker-publication-race-proof.md` as one
report-only child with `Report publication commit: SELF`; verify its literal
parent is the reported implementation head and remote path/blob/head match.
Signal exact FIFO `OK` only after that state exists. Do not merge.

The report must state result/status, PR/base/branch/all SHAs, old race
chronology and controlled reproduction, chosen synchronization state machine
and bounds, staging descriptor ownership transitions, two-worker outcomes,
corrupt/stall/symlink/fsync/cleanup evidence, files/dependencies/docs, every
local/CI result and intermediate failure, limitations/non-goals, and no
merge/extra PR.

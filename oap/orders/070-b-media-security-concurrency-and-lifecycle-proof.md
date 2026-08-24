# OAP Work Order — 070-b

## Objective

Continue Objective 070 on PR #61. Preserve 070-a's real private Media vertical
and close the concrete security, lifecycle, concurrency, and evidence gaps that
remain in its report. Harden path/cancellation/lock/edge behavior and prove the
ordinary-human, multi-workspace/site, concurrent dedupe, Editor patch/delete,
and private-orphan contracts. Do not broaden Media functionality. Do not merge.

## Verified starting state and findings

- Numeric objective: `070`; round: `070-b`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #61 on
  `oap/070-immutable-media-store`. Do not create another PR.
- Begin from verified remote 070-a report head
  `e459509d9fec2184584113f41b2f0cb957cb5e5a`; its only parent is
  implementation head `7a0ee3f2fb9c769bd24e74695f673ec6d685f22b` and it
  changes only `oap/reports/070-a-media-binary-upload-immutable-store.md`.
- PR #61 remains open, non-draft, mergeable, based on main
  `76fee6d3e233a3909b8ab303d7f563216d86e468`; reconcile live GitHub before
  editing.
- 070-a is genuine progress: fixed Media login/pool/secret, dedicated wrappers,
  human auth/CSRF, workspace COW registration, idempotency/audit, PNG/JPEG
  streaming/hash/sniff, digest storage, authenticated GET, fake-register
  removal, real PostgreSQL proof, NGINX upload/read, and full CI are retained.
- Finding 1 — `slaif_media_workspace_assert` does not acquire the accepted
  shared workspace advisory transaction lock before mutable authorization
  checks, so upload metadata can race freeze/revocation.
- Finding 2 — NGINX `client_max_body_size` and Apache `LimitRequestBody` were
  raised globally to 100 MiB. This weakens every non-media route and still does
  not admit a full 100 MiB file plus bounded multipart overhead.
- Finding 3 — `MediaStore` uses path-based parent creation and only final-entry
  `O_NOFOLLOW`. A symlink in `sha256`, digest-prefix ancestors, or a dangling
  final symlink is not safely handled; the dangling final case can recurse on
  `FileExistsError`. Publication lacks the ordered file/directory fsync proof
  required by the order.
- Finding 4 — `parse_upload` cleans only `Exception` and selected validation
  errors. `asyncio.CancelledError` is a `BaseException`, so cancellation can
  leave an open stream/staging file. Duplicate headers/file field naming and
  malformed/negative length ambiguity are not explicitly rejected/proved.
- Finding 5 — 070-a's integration fixture uses platform-administrator bypass,
  not an ordinary active membership with exact `media:upload`/`media:read`.
  It does not execute concurrent same-digest requests, second workspace/site
  isolation, real Editor PATCH/DELETE retention behavior, private-orphan DB
  failure, empty/oversized/auth/CSRF/permission/cancellation cases, or symlink
  tests, despite reporting those broader properties as passed/source-backed.

## Bounded scope and non-goals

Change only the existing 070 Media/store/parser/migration/edge/test/docs paths
needed for these findings. Preserve exact routes, PNG/JPEG-only support,
private local storage, fixed Media authority, workspace metadata semantics, and
all 070-a non-goals.

- No Agent upload, public/anonymous media, HEAD/range/CDN/signed URLs, object
  store/distributed backend, transforms/thumbnails/transcoding, PDF/video/audio,
  SVG sanitization, antivirus, browser artifacts, physical GC/retention,
  publication/review/promotion, or renderer integration.
- No generic table/function grant, raw SQL, client workspace/path/key, Editor/
  Control/Agent/reviewer credential in Media, or direct edge volume alias.
- Do not edit activated 070-a order/report or historical OAP artifacts.
- No extra PR and no merge.

## 1. Workspace freeze/revocation lock order

- Make the Media workspace assertion parse/validate trusted COW session and
  operation UUIDs, take the same product workspace shared advisory transaction
  lock used by accepted Editor/Agent mutations, and only then evaluate mutable
  workspace/site/session/account/membership/permission/expiry state.
- Keep lock ownership transaction-scoped and server-owned; no client lock key.
- Add a deterministic two-connection real-PostgreSQL race: hold the exclusive
  workspace lock, start Media registration/assertion and prove it waits, revoke
  or deactivate the relevant human authority while waiting, release the lock,
  then prove denial with zero media metadata/idempotency/audit/COW residue and
  no private object exposed through a reference.
- Preserve normal upload and GET behavior; read locking must not create durable
  state.

## 2. Route-scoped edge body limits

- Restore the strict existing global NGINX/Apache request-body limit for every
  non-media route.
- Add a `/media/`-only limit equal to configured default max file size plus the
  documented bounded multipart overhead (large enough for an exact 100 MiB file,
  not unlimited). Keep timeout/header/body buffering policies fail closed.
- Static and running NGINX plus Apache tests must prove: large Media multipart
  reaches Media service; the same oversized body to representative Control,
  Editor, Agent, MCP, Web, and unrelated routes remains edge-rejected; no route
  outside `/media/` inherits the relaxation.

## 3. Directory-FD-confined immutable store

Refactor the local store as needed so every untrusted/corrupt filesystem state
is confined under a verified root:

- pin/open the configured root and each digest-key directory component with
  directory descriptors, `O_DIRECTORY|O_NOFOLLOW` (or an equivalently strong
  platform primitive), checking regular directory ownership/mode/type; never
  follow `sha256`, prefix-directory, staging, or final-object symlinks;
- use bounded iterative race handling, never recursive `publish()` retry;
- reject non-regular/hardlink-count surprises where relevant, dangling/final/
  ancestor symlinks, FIFOs/devices/directories, corrupt same-size objects, wrong
  key/digest/size, and root replacement; never overwrite or traverse them;
- fsync staged bytes before publication, atomically create the final digest
  entry without replacement, set restrictive immutable object mode (document
  the chosen `0400` or justified `0600`), fsync the object and every modified
  containing directory in safe order, then remove/fsync staging. Existing valid
  objects are rehashed/verified and reused;
- descriptor-based authorized reads must verify regular type, size, digest,
  confinement, and close descriptors on success, failure, disconnect, and
  cancellation.

Add deterministic unit tests for final and dangling symlink, each ancestor
symlink, directory/FIFO/non-regular object, same-size corruption, existing
valid reuse, concurrent `FileExists` race, wrong key/digest/size, readiness root
failure, staging cleanup, mode, fsync hooks/order (without making tests
filesystem-specific), and descriptor closure.

## 4. Cancellation-safe bounded multipart and stable errors

- Put staging stream closure/removal in an unconditional `finally`/BaseException-
  safe ownership pattern; re-raise `CancelledError` unchanged. A disconnected
  stream must also clean staging and never create metadata/audit/idempotency.
- Require exactly one multipart part named `file`; reject duplicate file/form
  fields, duplicate/ambiguous security-relevant headers, malformed boundaries/
  final delimiter, negative/non-numeric/conflicting lengths, unknown fields,
  overlong headers/fields/deep JSON, empty file, exact-over-limit file, spoofed
  PNG/JPEG, unknown MIME, SVG, and traversal/control filename.
- Keep buffer/memory bounded across adversarial chunk boundaries; add tests
  that split every boundary/header/signature position and stream a file larger
  than memory prefix/chunk size without unbounded `request.body()`/read.
- Map client errors stably: missing/invalid idempotency 400, auth 401, CSRF/
  permission 403 or the established non-leaking outcome, malformed/invalid MIME
  422, oversize 413, foreign/missing reference 404, and only real storage/DB
  failures 503. No byte/path/parser-state detail in responses/logs.

## 5. Real ordinary-human, isolation, concurrency, delete, and orphan proof

Extend real PostgreSQL/filesystem/public HTTP evidence:

1. Replace platform-administrator bypass with an ordinary active user/site
   membership/role containing exactly the required Media read/upload (and the
   exact Editor metadata permissions for the patch/delete sub-proof). Prove a
   user lacking each permission is denied; prove missing auth, missing/wrong
   CSRF, revoked/expired session, inactive/expired workspace/site/membership.
2. Create two active HUMAN workspaces/users on one site and a second site. Prove
   workspace/site A cannot read B-only overlay UUIDs. Upload the same digest in
   another site: physical object is shared by digest, metadata UUID/site/user/
   alt/JSON are distinct and non-leaking.
3. Launch genuinely concurrent same-site/workspace same-digest uploads with
   distinct idempotency keys. Prove advisory serialization, one visible metadata
   UUID/row and one physical object, deterministic successful responses, no
   duplicate COW rows, and exact documented idempotency/audit counts.
4. Through the real public Editor PATCH route, change only alt/JSON and prove
   digest/key/bytes unchanged. Through real Editor DELETE, create a workspace
   tombstone; Media GET in that workspace returns 404, object remains, and the
   other valid site/workspace reference still reads byte-for-byte.
5. Inject/induce DB registration failure only after successful object publish.
   Prove the digest object remains private/unreferenced, no metadata/audit/
   completed idempotency/COW row is committed, and no guessed Media GET can
   retrieve it. Document it as a later-GC orphan.
6. Prove upload/parser cancellation/disconnect and GET-stream cancellation clean
   staging/descriptors and pool COW settings. After success and every failure,
   reuse the app-owned pool with no transaction/session/operation bleed.
7. Retain exact fixed Media app identity, wrapper ownership/search path/grants,
   base/change/generic/control/reviewer denials, forged/missing/wrong-site COW
   denials, canonical fallback, NGINX byte comparison, secret modes, one-shot
   networkless ownership handoff, and no long-running extra mounts.

## Acceptance criteria

- Media metadata cannot race freeze/revocation past the shared workspace lock.
- Only `/media/` receives bounded large-body allowance; all other surfaces keep
  the strict edge limit.
- No configured-root/digest ancestor/final symlink or non-regular object is
  followed, overwritten, or recursively retried; publication is durably fsynced
  and reads reverify content.
- Cancellation/disconnect/invalid input leave no staging or DB/COW residue and
  return stable non-leaking outcomes.
- Ordinary RBAC, workspace/site isolation, actual concurrent dedupe, Editor
  metadata/delete byte retention, and private DB-failure orphan behavior are
  proved through real APIs/identities.
- All accepted 070-a and prior Agent/Editor/Puck contracts remain green with no
  broader authority/dependency/trust change.

## Verification and workflow

Run and report exact focused store/parser/error/config tests; real Media/
Editor/PostgreSQL lock-race, auth, isolation, concurrency, delete/orphan tests;
edge-limit static/running tests; complete backend integration/quality/migration/
privilege/repository/packaging/process/Node/license/docs gates; clean Compose
NGINX media E2E; PostgreSQL 14–18 and every fresh GitHub check. Mark every
failure/retry/reused/not-run item honestly.

Update docs only where mode, edge limits, lock ordering, ordinary-RBAC proof,
store durability, or orphan semantics become more precise. Do not mutate the
immutable 070-a report; 070-b must explicitly identify which 070-a claims were
source-only/unproved and are newly established here.

Commit/push only this continuation plus exact strategic order/active bytes on
PR #61. Do not merge. Publish exactly
`oap/reports/070-b-media-security-concurrency-and-lifecycle-proof.md` as one
report-only child with `Report publication commit: SELF`, verify literal parent,
remote path/blob/head, then signal exact FIFO `OK`.

The report must state status/result, PR/base/branch/SHAs, production changes,
lock-race chronology, scoped edge limits, store descriptor/fsync state machine,
parser cancellation/chunk-boundary/error matrix, ordinary RBAC/site/workspace/
concurrency/delete/orphan IDs and counts, exact identity/grants/denials/context
cleanup, files/dependencies/docs, every local/CI result/intermediate failure,
limitations/non-goals, and no merge/extra PR.

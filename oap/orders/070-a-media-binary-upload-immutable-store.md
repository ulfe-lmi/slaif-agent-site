# OAP Work Order — 070-a

## Objective

Replace the metadata-only media placeholder with the first real immutable media
vertical: an edge-routed, human-authenticated Media service that streams and
validates uploads into a private local content-addressed `MediaStore`, records
the media reference inside the server-selected HUMAN workspace through COW,
and serves bytes only after an authorized workspace-aware metadata lookup.

## GitHub objective state

- Numeric objective: `070`; round: `070-a`.
- Mode: `CREATE_NEW_PR`; create exactly one new objective PR from verified
  remote `main` SHA `76fee6d3e233a3909b8ab303d7f563216d86e468`, produced by
  merged Objective 069 / PR #60.
- No Objective 070 PR or report exists at activation. Reconcile live GitHub and
  stop/report any difference before implementation.
- Use a fresh branch such as `oap/070-immutable-media-store`; never amend PR #60
  and never merge.

## Verified current state

- `content.media_asset` is COW-enabled metadata with CRUD functions and a
  site/hash uniqueness constraint. Editor routes list/get/patch/delete metadata
  inside the accepted human workspace envelope.
- `POST /api/editor/v1/sites/{site_id}/media/register` is a placeholder: it
  trusts client filename/MIME/size, hashes only the filename, synthesizes a
  storage key, writes no bytes, and falsely says bytes are uploaded separately.
- `media-service` is health-only. Its edge `/media/` route and private
  `media-data:/var/lib/slaif/media` volume already exist; NGINX does not mount
  or directly expose that volume.
- `slaif_media` has no database object grants and there is no fixed media login
  secret/pool wiring, local `MediaStore`, streaming parser, content sniffer,
  authorized byte route, or binary integration proof.
- `media-gc` is health-only and shares the private media volume, but physical
  garbage collection is intentionally later scope.
- Architecture requires immutable content-addressed bytes, local volume by
  default, every online editorial metadata write in a workspace, server-owned
  context, authenticated authorized reads, and harmless private precommit
  orphans rather than pretending filesystem and PostgreSQL commit atomically.

## Required public surface

Implement the exact edge-routed Media service surface under the existing
`/media/` proxy, with stable OpenAPI/error contracts:

- `POST /media/v1/sites/{site_id}/assets`
  - multipart upload with one file plus bounded `alt_text` and optional bounded
    JSON metadata;
  - authenticated human session, CSRF, active site membership,
    `media:upload`, server-resolved current HUMAN workspace, and required
    `Idempotency-Key`;
  - returns `201` for newly registered metadata and a documented successful
    replay/deduplication result without creating a second reference.
- `GET /media/v1/sites/{site_id}/assets/{media_id}/content`
  - authenticated human session and `media:read`;
  - resolves metadata through the same server-selected workspace COW overlay
    plus canonical fallback, then streams the immutable object;
  - foreign site/workspace, tombstoned/missing reference, missing/corrupt object,
    and unauthorized access fail closed without leaking path or existence.
- Add `HEAD` only if it shares the exact GET authorization/lookup path and is
  useful to the web client; do not broaden public/anonymously readable media.

Remove the fake Editor `POST .../media/register` route and its contract/docs so
there is no way to create metadata that claims nonexistent bytes. Retain the
existing Editor list/get/metadata-patch/reference-delete routes and their human
COW envelope unless a narrow compatibility adjustment is required.

## Media service authority and workspace design

1. Give the Media service one owned lifespan pool using the fixed production
   `slaif_media_login` with exactly `slaif_media`, mounted from a dedicated
   local secret file/volume initialized by the existing one-shot secrets flow.
   Validate database, `session_user == current_user == slaif_media_login`, and
   exact sole product-role membership on every physical connection, as Agent
   and Editor pools do.
2. Reuse shared typed human session/site authorization semantics, but grant
   `slaif_media` only the exact owner-defined read/auth functions and dedicated
   media mutation/read wrappers needed here. It must not gain Control/Editor/
   Agent/reviewer/bootstrap authority, generic content functions, table DML,
   base/change-table access, arbitrary SQL/DDL, user management, or publication.
3. Site/workspace/user/session/permission/idempotency context is server-derived.
   No header/query/path/body/form field may choose a workspace, operation UUID,
   database setting, storage root, or storage key.
4. Reassert active workspace/site/human session/membership/permission inside the
   metadata transaction under the accepted shared workspace lock. Use the
   existing human mutation envelope semantics or an equivalently narrow
   media-specific wrapper: metadata COW mutation, idempotency result, HUMAN
   audit, and response payload commit or roll back together.
5. The Media service may use a fresh server operation UUID internally. GET/HEAD
   create no idempotency/audit/COW operation state. Upload replay/mismatch and
   cancellation must clean transaction-local context before pool release.
6. Metadata `uploaded_by` is the authenticated human user. The metadata row's
   `site_id`, digest, MIME, size, and storage key come from trusted upload
   processing, never client claims.

## Local immutable `MediaStore`

Implement a small typed `MediaStore` boundary with a local-filesystem default:

- production root defaults to `/var/lib/slaif/media`; a validated absolute
  configuration and configurable default 100 MiB upload limit are supported;
  invalid/unwritable roots fail readiness without leaking paths in HTTP errors;
- stream bounded chunks to an exclusive staging file while incrementally
  computing SHA-256 and byte count; never call an unbounded file/body read and
  never retain the entire upload in memory;
- sniff actual bytes from a bounded prefix. Support only an explicitly tested
  initial safe MIME set (at minimum PNG and JPEG; GIF/WebP may be included).
  Reject empty, unknown, spoofed declared MIME, polyglot/invalid signatures
  where the validator can detect them, and SVG (`image/svg+xml`) rather than
  serving active markup. Do not trust extensions or client Content-Type;
- normalize/sanitize the original filename for metadata only. It must never
  participate in a filesystem path and traversal/control/oversized names fail;
- publish to a digest-only key such as
  `sha256/{digest[0:2]}/{digest[2:4]}/{digest}` using same-filesystem atomic
  creation/rename/link semantics, restrictive permissions, file and directory
  fsync where supported, no symlink following, and no overwrite of an existing
  digest object;
- if the digest already exists, verify it is a regular immutable object with
  the expected size/content contract and reuse it; corruption/type/symlink
  mismatch fails closed and is never overwritten;
- always remove staging files on validation failure, size overflow,
  cancellation, disconnect, or storage error. Do not recursively delete broad
  paths or follow attacker-controlled links.

Filesystem publication and PostgreSQL cannot be one atomic transaction. Use the
honest safe order: authenticate/authorize; stage+validate; atomically publish
the private immutable object; then transact metadata/idempotency/audit. A DB
failure may leave an unreferenced private digest object for later Media GC; it
must be inaccessible through the authorized read API without metadata and must
never be described as rolled back or publicly exposed.

## Metadata registration, deduplication, and deletion semantics

- Add the smallest site/workspace-bound media registration and lookup wrappers.
  Registration takes trusted digest/MIME/size/key and returns an existing
  visible same-site/workspace reference for the digest or inserts exactly one
  COW metadata row. Serialize same-site/digest races with a transaction-scoped
  advisory lock or an equally deterministic database mechanism; never rely
  only on a base-table uniqueness constraint that may not constrain COW change
  rows.
- Same bytes uploaded twice in one workspace return the same media UUID and do
  not create a second metadata row or physical object. Same bytes in another
  site may share the digest object but require a distinct authorized metadata
  reference and must not leak the other site's filename/alt/metadata.
- Metadata alt text and bounded JSON remain editable through the existing
  Editor route. Editing metadata never mutates bytes or digest/storage key.
- Existing Editor delete creates a workspace reference tombstone only. It does
  not unlink bytes. A deleted/tombstoned reference makes Media GET return 404
  in that workspace; other valid references remain readable. Physical orphan/
  retention deletion belongs to later `media-gc` work.

## Authorized byte response

- Stream from a verified regular digest object; do not read the entire object
  into memory and do not expose absolute paths/storage roots.
- Return the sniffed trusted `Content-Type`, exact `Content-Length`, strong ETag
  derived from SHA-256, `X-Content-Type-Options: nosniff`, safe disposition, and
  a private/no-store cache policy for this authenticated workspace surface.
- Do not add permissive CORS, executable HTML/SVG serving, content-type
  reflection, public URL guessing, directory listing, or NGINX aliasing to the
  volume.

## Required real proof

Use real PostgreSQL, production Media application wiring/identity, real local
filesystem staging/object directories, human session+CSRF+RBAC, and public
NGINX/edge HTTP where repository infrastructure permits. Prove at minimum:

1. A human with `media:upload` in a server-selected active HUMAN workspace
   uploads a chunked valid PNG/JPEG through multipart. The stored digest,
   sniffed MIME, size, safe original filename, digest-only key, uploader, and
   metadata are exact; metadata exists only in workspace overlay and canonical
   base remains unchanged.
2. Authenticated GET through Media service reads the workspace-created asset
   immediately and returns byte-for-byte data plus exact security/cache headers.
   Unchanged canonical metadata/object is visible as fallback.
3. Same bytes + new idempotency key deduplicate to one object and one visible
   metadata UUID; same key replay returns the recorded response; same key with
   different bytes/metadata returns stable mismatch. Concurrent same-digest
   uploads cannot create duplicate visible metadata.
4. Another workspace/site/user cannot read or mutate the first workspace's
   reference. A deliberately colliding digest in a second site has separate
   metadata. Wrong site/ID responses are non-leaking.
5. Existing Editor metadata patch changes only alt/JSON; reference delete
   tombstones metadata in that workspace, Media GET then returns 404, bytes
   remain on disk, and another valid reference to the digest still reads.
6. Missing auth, CSRF, permission, idempotency key, inactive/expired workspace
   or session, wrong site, malformed IDs/metadata, empty/oversized/truncated
   body, unsupported/spoofed MIME, SVG, traversal filename, disconnect/
   cancellation, unwritable/corrupt/symlink storage all fail closed with staging
   cleanup and no metadata/audit/idempotency/COW residue beyond documented
   private orphan behavior after object publication.
7. Exact Media app pool identity and grants/denials are asserted. Direct wrapper
   calls with missing/forged/wrong-site COW context fail. Pool reuse after
   success/failure/cancellation has no transaction or COW setting bleed.
8. NGINX and Apache route `/media/` only to Media service; neither edge process
   mounts/directly serves `media-data`. Compose uses one shared named volume only
   for Media service and Media GC, with least-privilege users and no host path.

## Acceptance criteria

- Real validated bytes—not filename-derived metadata—are immutably stored and
  authorized-read through the Media service.
- Human upload metadata is a real workspace COW mutation with exact
  idempotency/audit and canonical isolation.
- Content/MIME/size/path/race/deduplication behavior is deterministic and
  fail-closed; SVG and arbitrary active content remain disabled.
- Bytes remain private and immutable; reference deletion never physically
  deletes a still-retained object.
- Media service holds only `slaif_media`; no broader database/trust authority or
  hosted/non-permissive dependency is introduced.
- Existing Agent reads/mutations and Editor/Puck behavior remain green.

## Explicit non-goals

- No Agent media upload route yet; do not grant `media:upload` handling to Agent
  API in this objective.
- No image resize, thumbnail, optimization, EXIF rewriting, transcoding, PDF/
  video/audio processing, SVG sanitization, antivirus service, or arbitrary
  document rendering.
- No public/anonymous media URL, CDN, object-store/S3 backend, shared/distributed
  filesystem protocol, signed external URL, browser artifact storage, import/
  batch manifest, or source reconstruction.
- No physical Media GC, retention policy, reviewer finalization, publication,
  promotion, freeze/snapshot, or canonical renderer integration.
- No raw SQL endpoint, client-selected workspace/path/key, direct NGINX file
  serving, or weakening of CSP/auth/site boundaries.

## Verification, documentation, and workflow

Run and report exact focused store/sniffer/config/unit tests; Media HTTP/auth/
COW/idempotency/privilege real-PostgreSQL integration; Editor metadata/delete
regressions; edge/Compose multipart upload→read→delete evidence; full backend
quality/integration/migration/privilege/repository/packaging/process/Node/
license/supply-chain/docs gates; PostgreSQL 14–18 CI; and `git diff --check`.
Mark every skipped, reused, not-run, pending, failure, and corrected invocation
honestly.

Update API, configuration, database roles/connections, service authority,
security, deployment/operations/backup, testing, and user-facing upload docs so
the private workspace semantics, MIME/size limits, storage layout (without host
path leakage), DB-vs-filesystem failure model, backup requirement, and explicit
non-goals are accurate. Do not claim public serving, GC, transcoding,
distributed storage, Agent upload, promotion, or production readiness.

Create exactly one fresh 070 branch/PR from the verified main SHA, implement
only this order, push, and never merge. Commit this activated order and exact
`oap/active` unchanged. Publish
`oap/reports/070-a-media-binary-upload-immutable-store.md` as the final
report-only commit with `Report publication commit: SELF`; verify its first
parent is the literal implementation head and remote PR head is that report
commit before signaling exact FIFO `OK`.

The report must state `COMPLETE` or `BLOCKED`, `RESULT=OK|PARTIAL|BLOCKED|FAILED`,
base/branch/PR/SHAs, exact routes, byte/store state machine, MIME validators,
filesystem keys/permissions without absolute-path leakage, workspace/auth/
identity/grants, transaction/idempotency/audit trace, object-orphan semantics,
dedupe/race/delete/isolation evidence, files/dependencies/licenses, every test/
CI result, intermediate failures, limitations/non-goals, and no merge/extra PR.

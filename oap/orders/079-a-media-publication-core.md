# OAP Work Order — 079-a (media publication core + real Image +
Agent media references)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-09-20 to `oap/orders/079-a-media-publication-core.md`
> with `oap/active` = `079-a`, per the human owner's decisions of
> 2026-09-20 (D1: 078/079 seam ratification with 078 staying PARTIAL;
> D2: sequence approved with the first 079 increment using the legacy
> flat ID `079-a`) and after the 078/8 MapBlock OSM layer contract
> repair (`078-9-a`) was accepted, merged, and independently verified
> on remote `main`. The coding agent executes under the normal OAP
> execution contract; strategy remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-a` (historical legacy flat round ID, first round of the
  first semantic increment of numeric Objective 079). Per the 2026-09-14
  ID-namespace amendment and the human directive of 2026-09-20 (D2),
  the first increment of Objective 079 uses the legacy flat namespace
  (`079-a`); the second increment will use `079-2-a` and the third
  `079-3-a`. Do not use an increment-qualified first-increment ID.
- Mode: CREATE_NEW_PR.
- Branch: `oap/079-a-media-publication-core`, created from verified
  current `main` = `d8b1d360add9d583fa2cc64c451dd5d6faad8730` (verified
  against live GitHub 2026-09-20 at activation).
- Expected PR number: next available (GitHub assigns; create exactly one
  PR; do not create, amend, or touch any other PR).
- The preplanned inert file `079-a-agent-media-semantics.md` (legacy
  flat ID, never activated) is SUPERSEDED as planning reference by this
  order. The `078-9-a` maintenance increment retires it from
  `oap/orders/` to `oap/governance/superseded-preplanned/` (content
  unchanged) so that the `079-a` activation keeps a unique
  identifier-to-order mapping (enforced by
  `tools/check_repository.py`). Do not edit or activate it; do not
  reference it as authority. Its narrower scope (Agent media semantics
  only, public media deferred to 083) is refined by the dependency audit
  recorded in the 2026-09-19 scope audit: the public/preview media core
  and real Image rendering are 079/1 because 079/2-079/3 (real
  Gallery/LogoGrid/DocumentList rendering) and 081 (exact Agent-workspace
  Puck preview) depend on them, while 083 retains only the promotion-time
  call and the accept-bound public rendering.

## 2. Verified current state (strategy-verified 2026-09-20 at
activation against live GitHub; base = post-078/9 merge main)

- Activation verification (2026-09-20, live GitHub): remote `main` =
  `d8b1d360add9d583fa2cc64c451dd5d6faad8730` (merge commit for PR #89 /
  078/9, `mergedAt` 2026-09-20T13:33:57Z); post-merge checks on
  `d8b1d36` are 18/18 `completed/success` with `Dependency review`
  skipped exactly as at the previous main merge commit (`ddd1559`).
  The media source facts below were baseline-verified 2026-09-19 at
  `ddd1559`; 078/9 changed only the MapBlock layer allowlist,
  bounded-embed tests, the preview.spec.ts embed pins, and
  current-truth docs — it does not touch the media core, store, media
  routes, projection, or the media scope facts below; re-verify them
  against `d8b1d36` before coding.
- Objective 078 increments accepted and merged (verified merge facts):
  078/1 PR #77 at `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`; 078/2 PR
  #79 at `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`; 078/3 PR #80 at
  `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`; 078/4 PR #81 at
  `26cafc1c0c91de5eee8406e8d477c50ea0208058`; 078-z (governance
  transition, not a product increment) PR #82 at
  `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba` on 2026-09-17; 078/5 PR #85
  at `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`; 078/6 PR #86 at
  `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`; 078/7 PR #87 at
  `d9a7555662a976483b9716e41863de8ecd00decf`; 078/8 PR #88 at
  `ddd1559f021762316f5a64989a307355acb4aab2`; 078/9 PR #89 at
  `d8b1d360add9d583fa2cc64c451dd5d6faad8730` on 2026-09-20 (MapBlock
  OSM layer contract repair; maintenance increment, no media impact).
- No product OAP PR is open. Dependabot PRs #83, #84, and #75 are open
  and are EXPLICITLY OUT OF SCOPE: do not merge, refresh, rebase, bump,
  or reference them.
- The 078/079 seam is human-ratified (2026-09-20, D1): all
  architecture-owned Objective-078 contracts that do not require 079
  media semantics are accepted and merged; the remaining catalog types
  (`Gallery`, `LogoGrid`, `DocumentList`) and real `Image` rendering are
  079-bound by dependency audit, not by convenience. Per D1, numeric 078
  remains PARTIAL until those 079-bound requirements are implemented and
  proven; it is reclassified COMPLETE only after independent
  verification of the resulting evidence.
- Component catalog: 29 of 32 architecture-minimum types. This increment
  delivers real `Image` rendering (no catalog type changes); `Gallery`
  and `LogoGrid` are 079/2; `DocumentList` is 079/3 (do not implement).
- Media state at `ddd1559` (source-verified 2026-09-19; media-neutral
  at `d8b1d36` — 078/9 touched no media surface; re-verify against the
  base before coding):
  - `media_service`: `LocalVolumeMediaStore` (volume root + `.staging` +
    content-addressed object directory `sha256/<2>/<2>/<digest>`),
    bounded streaming upload with SHA-256, content-MIME sniffing (not
    filename), `open_verified(key, digest, size)` reads, atomic
    `publish(staged) -> storage_key`.
  - Media HTTP (edge `/media/` proxies `slaif_media_service`): `POST
    /v1/sites/{site_id}/assets` (upload, 201) and `GET
    /v1/sites/{site_id}/assets/{media_id}/content` (authenticated
    `media:read` streaming read). Both PRIVATE API routes.
  - `MediaAssetRecord`: id, site_id, uploaded_by, filename, mime_type,
    size_bytes, content_hash, storage_key, alt_text, metadata,
    timestamps. NO public-visibility state, NO public URL field.
  - Editor API: human media CRUD (list/get/patch/delete) in
    `editor_api/media_http.py`; human permissions `media:read`,
    `media-metadata:write`, `media:upload`, `media-reference:delete`
    (route-policy-verified). Agent API: `GET /api/agent/v1/media/`
    (list, `media:read`) only — no upload, no byte read, no reference
    write.
  - Scope facts (verified in `human_authorization/catalog.py` and
    `_PRESET_SCOPES` in `control_api/workspace_http.py`): agent
    capabilities carry `READ_SCOPES | L1..L4_SCOPES` by preset;
    `media:read` is in `READ_SCOPES`; `media:upload` is in
    `L1_SCOPES`; the capability record already carries
    `upload_quota` / `upload_used`. R5 needs no new scope string.
  - Catalog `Image` (verified in `catalog-v1.json`): props
    `mediaId` (reference/uuid, required), `alt` (localized string,
    max 4096), `aspectRatio` (enum `auto|16:9|4:3|1:1`, optional);
    `binding_kind: media_asset`; leaf (no slots, no children).
  - Store API (verified in `media_service/store.py`): `publish(
    staged: StagedMedia) -> str` returning the storage key
    `sha256/<2>/<2>/<digest>`; `open_verified(key, digest,
    size_bytes)` digest-verified read; atomic staging -> object
    directory.
  - Smoke expectation (verified, `tools/compose/smoke.sh` line 307):
    `media-e2e: OK edge=nginx upload=validated-private-read=byte-
    identical`, plus the 8-audit-row COW check — the line R8
    extends.
  - Renderer: `Image` is a placeholder `div.renderer-image-placeholder`
    (validates `mediaId` UUID shape; renders no `<img>`).
  - `media_gc` process exists (process-smoke green); public-namespace
    retention semantics are out of scope here (083/089-bound).
  - Public CSP `img-src 'self' data:` — a public digest route served
    under the same origin is `'self'`-compatible; verify in evidence.
- `oap/active` currently contains `078-9-a` (last activated round;
  protocol-correct idle state, not in flight).
- Flake history (documented Puck-drag VM flake class, `governance.spec.ts`
  `dragUntil`): recurred at 078-7-b's superseded-adjacent CI, 078-8-a's
  first SELF CI run 35453903907, 078-8-a local smoke4, and the post-merge
  main run 35455820388 (closed by the single permitted re-run,
  `completed/success` 2026-09-19T17:06:43Z). That single re-run is
  CONSUMED; 078-9-a separately consumed its own per-order documented
  re-run on a transient `astral-sh/setup-uv` runner network failure at
  its superseded first head (2026-09-20, before any code step ran);
  that budget is historical. This order re-declares the policy in
  R10.
- Required checks: the established 20 (Repository policy, Node contracts,
  Python 3.12/3.13/3.14, Foundation PostgreSQL 14-18, Compose and edge
  packaging, Supply-chain evidence, Markdown, Mermaid, Dependency review,
  Detect supported languages, CodeQL, Analyze actions/python/
  javascript-typescript).
- Current truth surfaces at `d8b1d36` (post-078/9, verified at
  activation 2026-09-20; requirement R9 works from exactly this text):
  - `oap/INCREMENTS.md` 078/8 row, state cell: "Accepted and merged in
    PR #88 at `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19;
    078/8 is closed".
  - `oap/INCREMENTS.md` in-flight row (name cell "078/9: MapBlock OSM
    layer contract repair"): "Opened at `078-9-a` from verified remote
    main `ddd1559f021762316f5a64989a307355acb4aab2`; PR pending;
    strategy owns acceptance and merge. No further ordinary 078
    product increments are planned. The 078-bound catalog types
    (Gallery, LogoGrid, DocumentList, real Image) are 079 increments
    per the human directive of 2026-09-20. Numeric 078 remains PARTIAL
    until they are implemented and proven; reclassification to COMPLETE
    occurs only after independent verification of the resulting
    evidence."
  - `oap/INCREMENTS.md` preamble: "Increments 078/1 through 078/4 are
    accepted and merged; increment 078/5 is accepted and merged in PR #85
    at `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` on 2026-09-19 under the
    2026-09-14 increment-qualified round-ID amendment."
  - `oap/MVP-PROGRESS.md` "Active and remaining sequence" paragraph
    ends: "...increment 078/8 is accepted and merged in PR #88 at
    `ddd1559f021762316f5a64989a307355acb4aab2` on
    2026-09-19. Acceptance and containment in `main` are
    determined by OAP and GitHub state, not this document; GitHub
    remains authoritative for live acceptance and merge state. All
    later order files remain inert until strategy selects and signals
    them."
  - `oap/MVP-PROGRESS.md` status table row 078 ends: "...increment
    078/8 is accepted and merged in PR #88 at
    `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19; the
    078-bound catalog remainder (Gallery, LogoGrid, DocumentList, real
    Image) is 079-bound per the human directive of 2026-09-20, so
    numeric 078 remains PARTIAL until it is implemented and proven".
  - `oap/MVP-PROGRESS.md` status table row 079: "| 079 | Agent media
    semantics and references | PARTIAL |".
  - `README.md` capability row "Objective-078/4 page-style data plane
    (merged)" ends: "...increment 078/8 (bounded embed family) is
    accepted and merged in PR #88 at
    `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19; GitHub is
    authoritative for live acceptance and merge state."
  - `oap/MVP-CONTRACT-AUDIT.md` media row (row 42): "Objective 070 proves
    immutable human upload/CAS safety; Agent upload/reference semantics,
    anonymous canonical-reference-gated bytes, real image rendering and
    promotion finalization are absent | PARTIAL | Agent media in 079;
    public finalization/rendering and rollback in 083".
  - `CRITICAL.md`: carries the historical-record banner (PRs #28-#54
    only); verify it contains no current-state media/078/079 claims;
    edit only if a stale claim is actually found (durable wording).

## 3. Strategic context

Objective 078 is closed at the 078/079 seam with 078/1-078/8 merged;
numeric 078 remains PARTIAL by architecture until the three 079-bound
catalog types land (079/2-079/3). This increment is 079/1: the media
publication core. It delivers the public namespace and visibility state,
the promotion-callable finalization primitive, the unauthenticated public
digest route with immutable caching, the authorized preview read path,
real Agent media create/reference semantics over the existing immutable
store, and the real `Image` renderer. Everything later depends on it:
079/2-079/3 render real media; 081's exact Agent-workspace Puck previews
real media; 082's snapshot references finalized media; 083's promotion
transaction calls the finalization primitive and binds public rendering
to the accepted revision. Per the 2026-09-14 review-unit governance this
is one bounded semantic family (media publication core) plus its ordered
evidence; the flake stabilization (R10) is a disclosed, predeclared
test-infrastructure supporting item, not a new product family.

## 4. Bounded scope

Exactly: the public object namespace and public-visibility state (one
downgrade-safe migration); the promotion-callable finalization
primitive; the public unauthenticated digest route with immutable cache
headers in both edge adapters; the authorized preview read path; Agent
media upload/read and composition media-reference validation; the real
`Image` renderer replacing the placeholder; the OpenAPI delta; the
current-truth doc updates (durable wording); the dragUntil flake
stabilization (test infrastructure only); and full evidence per R8.
Nothing else.

## 5. Explicit non-goals

- No `Gallery`, `LogoGrid`, or `DocumentList` catalog types (079/2,
  079/3); no catalog type additions or prop-shape changes in this PR
  (no `060_001` baked-catalog change, no design-system change).
- No promotion pipeline, freeze, review snapshot, accept/discard, or
  publication behavior (082/083); the finalization primitive is
  promotion-callable but NOT called by any promotion path in this PR.
- No anonymous public rendering bound to an accepted revision (083);
  before 083, public bytes exist only because the E2E invokes the
  primitive directly as the promotion-boundary call.
- No public byte deletion, public retention/GC semantics, or backup
  policy work (083/089/090); the existing `media_gc` process is
  unchanged.
- No browser-artifact namespace changes; no MCP changes; no source
  tools; no global-region/header-footer/theme changes (078/5 closed
  contract); no collection-semantics changes (078/7 closed contract).
- No store-backend change: `LocalVolumeMediaStore` stays; no
  shared-filesystem or object-store integration.
- No new dependency or lockfile change; NO changes under
  `tools/supply_chain/`, `tests/supply_chain/`, or `.github/workflows/`
  (hard constraint; if new code ever caused a supply-chain or
  reproducibility failure, STOP and report BLOCKED with byte-level
  analysis for separate strategic adjudication).
- No runtime-configurable public route, cache policy, or MIME/size
  bounds (code-defined, versioned, deterministic).
- No Dependabot PR work; no changes to the preview flight-free contract
  (`clientState={false}`); no new human RBAC role or preset.

## 6. Requirements

### R1 - Public namespace and public-visibility state

- Migration (one new Alembic revision, downgrade-safe): add to
  `content.media_asset` a `public_status` column (`ENUM('private','public')`,
  NOT NULL, default `'private'`) and a `published_at` timestamptz NULL
  column. Downgrade drops both columns. No other schema change.
- `LocalVolumeMediaStore`: add a public object namespace as a sibling of
  the private object directory: `<volume-root>/public/sha256/<2>/<2>/
  <digest>`. Add `publish_public(storage_key, digest, size) -> str`
  (returns the public storage key): idempotent hard-link when possible,
  copy fallback; verify SHA-256 of the destination byte range equals
  `digest` before and after; atomic via temp name + rename inside the
  public namespace; NEVER link/copy into or out of `.staging` or
  browser-artifact directories; failure leaves at most an unreferenced
  public object (GC-able), never a partial one.
- `MediaAssetRecord`: expose `public_status` / `published_at` (model +
  repository mapping). Only the finalization primitive (R2) may set
  `public_status='public'`.
- `media_gc` remains unchanged and must remain green.

### R2 - Promotion-callable finalization primitive (new module, pure
orchestration over the store)

- New `media_service/finalize.py` (no HTTP, no DB session parameter
  beyond what the record repository needs; no browser; no network):
  `finalize_media_for_promotion(site_id, workspace_id, media_ids) ->
  FinalizationManifest`.
- Behavior: enumerate exactly the referenced media (input `media_ids`,
  validated as site-owned and workspace-referenced); for each: verify
  the private object exists, digest-verify via `open_verified`,
  idempotently `publish_public`, set `public_status='public'` +
  `published_at` (already-public entries are no-ops recorded in the
  manifest); return the manifest `{media_id, digest, public_key}`
  entries in deterministic order.
- Failure semantics: a mid-run failure leaves only (a) previously
  public assets untouched and (b) at most unreferenced public objects
  for GC; the manifest returned on failure lists exactly which bytes
  were made public; no partial "some references public, some not"
  metadata state for the same promotion batch (metadata marks are
  applied per-asset and the manifest is the audit of truth).
- Unit-test the primitive directly (this is the exact call 083 will
  make inside the reviewer boundary, before commit).

### R3 - Public unauthenticated digest route (edge + media service)

- New media-service route: `GET /v1/public/sha256/<2>/<2>/<digest>` —
  unauthenticated, stream the public object, exact headers:
  `Content-Type` from the validated record's `mime_type`,
  `Content-Length` from `size_bytes`, `Cache-Control: public,
  max-age=31536000, immutable`. 404 (not 403) when the digest is not
  public or absent. No redirects. No media-id, site-id, or cookie in
  the URL or handling.
- Edge: expose the route through the existing `/media/` proxy in BOTH
  adapters (`infra/nginx/nginx.conf`, `infra/apache/slaif-agent-site.
  conf`); the staging and browser-artifact directories must remain
  unrouteable (extend `tests/packaging/test_edge_contract.py` to assert
  the exact new public line in both adapters and a negative probe that
  `.staging`/artifact paths are not reachable under `/media/`).
- The public URL form is the canonical renderer public URL (R6).
- Exact path form: edge `/media/public/sha256/<2>/<2>/<digest>`
  proxies to the media-service `GET /v1/public/sha256/<2>/<2>/
  <digest>`. The route is unauthenticated end to end; any service-
  level internal auth does not apply to this route; the service port
  remains non-public.

### R4 - Authorized preview media read path

- The existing authenticated `GET /v1/sites/{site_id}/assets/{media_id}/
  content` route is the preview read path: verify and pin (do not
  redesign) its authorization = authorized human session with the
  `media:read` scope, exact site binding, workspace-visible reference
  check where the caller context provides one, and fail-closed
  negatives (foreign site, revoked session, direct `.staging`/artifact
  path, non-member).
- Preview render payload (R6) emits this route's URL for preview
  context; public render payload emits the R3 digest URL. No preview
  token may read another site's assets.

### R5 - Agent media semantics (create/read/reference)

Verified scope facts (NO new scope strings): `media:read` is in
`READ_SCOPES` (all presets) and `media:upload` is in `L1_SCOPES` (L1
and above) in `human_authorization/catalog.py`; preset scopes are
`READ_SCOPES | L1..L4_SCOPES` (`_PRESET_SCOPES`,
`control_api/workspace_http.py`); the capability record already
carries `upload_quota` / `upload_used`.

- Agent API additions (capability-authenticated; site/workspace
  derived only from the trusted capability context, never from path
  or body; idempotency-keyed; semantically audited in the COW
  transaction; bounded error keys; no user-input echo):
  - `POST /api/agent/v1/media/assets` — scope `media:upload`; bounded
    streaming upload through the same store path as the human route
    (SHA-256, content-MIME sniffing, size bounds); enforces the
    capability `upload_quota` via the existing `upload_used`
    accounting.
  - `GET /api/agent/v1/media/assets/{media_id}/content` — scope
    `media:read`; agent byte read with the same digest-verified
    streaming as the human route.
- `control_api/route_policy.py` additions exactly: `("POST",
  "/api/agent/v1/media/assets", ("media:upload",))` and `("GET",
  "/api/agent/v1/media/assets/{media_id}/content", ("media:read",
  ))` — same agent authority class as the existing agent routes
  (capability authentication, no CSRF).
- Existing `GET /api/agent/v1/media/` (list, `media:read`): unchanged.
- Composition media-reference validation: when an Agent (or Editor)
  mutation sets the `Image.mediaId` prop (catalog `reference/uuid`,
  `binding_kind: media_asset`), validate: exists, same site, MIME
  class compatible with the component; preview references are legal
  for private assets (`public_status`-independent). Bounded 422 on
  the Agent path with the exact error key; Editor path equivalent
  rejection; row version, idempotency, and audit semantics unchanged
  on rejection.

### R6 - Real `Image` renderer (replace the placeholder)

Verified current code (`apps/web/src/renderer/components.tsx`):
`Image({props})` validates `props.mediaId` against
`/^[0-9a-f-]{36}$/i` (throws on mismatch) and renders
`div.renderer-image-placeholder` with `role="img"`, `aria-label`
from `props.alt`, and the existing `designClasses(props.
aspectRatio, ...)` aspect-token classes (`auto`, `16:9`, `4:3`,
`1:1`).

- Media descriptor resolution in projection
  (`render_api/projection.py`): for each `Image` node the render
  payload carries a resolved media descriptor `{url, mime_type,
  size_bytes}` or a fail-closed marker. Preview context: `url` is the
  R4 authenticated preview URL (the browser fetch carries the preview
  session cookie). Public context: `url` is the R3 digest URL ONLY
  when the asset is `public_status='public'`; otherwise the fail-
  closed marker (no public URL is ever derived for a private asset).
  The renderer never fetches media itself and never resolves a raw
  mediaId.
- `apps/web/src/renderer/components.tsx` (+ `renderer-v1.css`): for a
  resolved descriptor `Image` emits `<img class="sl-image" src="
  <descriptor.url>" alt="<escaped alt>" loading="lazy"
  referrerpolicy="no-referrer"></img>`; the aspect token stays on the
  wrapper via the existing `designClasses` mapping (no inline style
  attributes).
- Fail-closed: keep the current throw for a wrong-shape `mediaId`
  (format defense in depth; catalog validation already prevents
  persistence). Descriptor fail-closed marker (asset missing, foreign
  site, or MIME class mismatch) renders the existing
  `div.renderer-image-placeholder` pattern (same class, role, and
  aria-label semantics) — NEVER an `<img>` with an unvalidated URL.
- Deterministic attribute order; no JS/event handlers; preview and
  public markup identical except the `src` form (documented + byte-
  pinned in evidence).
- Public CSP `img-src 'self' data:` already covers same-origin digest
  URLs — verify in the edge-contract evidence, change nothing.

### R7 - OpenAPI (exact delta)

- Regenerate `contracts/openapi/agent-v1.json`. The diff against base
  must contain ONLY: the two new media paths (R5) with their request/
  response schemas and the existing scope strings. No existing path
  semantics change; no new scope strings; no new path beyond R5;
  `x-slaif-*` extension keys per the existing pattern. The drift gate
  must pass.

### R8 - Evidence (all actually executed, honestly reported)

- Unit (new `services/backend/tests/unit/test_media_public_core.py`):
  `publish_public` idempotency/digest-verify/failure modes; finalization
  manifest positive (mixed already-public + fresh) and mid-run failure
  (exact manifest of bytes made public, no partial metadata); preview
  authorization matrix (member/non-member, foreign site, revoked
  session, staging/artifact path probes); R5 bounded error keys.
- Renderer (extend `apps/web/tests/renderer-behavior.test.ts`): exact
  `<img>` markup pins (preview URL form and public digest URL
  form, alt text, lazy loading, referrerpolicy), forbidden-
  attribute absence (no inline style, no event handler),
  fail-closed placeholder for invalid/foreign references.
- E2E (new `media-publication` spec within the tests/e2e budget, real
  browser through public NGINX): human upload + agent upload; preview
  page renders the real `<img>` from the preview URL (byte-identical
  fetch); the finalization primitive is invoked DIRECTLY as the
  promotion-boundary call (the exact call 083 will make); the public
  digest URL then serves byte-identical bytes with the exact immutable
  `Cache-Control` header; preview/public renderer parity (markup
  identical except src form); hostile suite (>= 12 cases): cross-site
  asset, forged/unknown digest, path traversal into `.staging` and
  artifact dirs, SVG upload (disabled by policy: rejected, not
  sanitized), oversized/dimension-bound upload, corrupt-digest read,
  revoked capability 401, missing idempotency key, foreign-mediaId
  component prop rejection, non-member preview denial; COW audit rows
  exact for agent upload + reference mutation; restart: public bytes
  survive service restart and require no re-finalization; edge
  contract: `.staging`/artifact unrouteable, exact public header set.
- Full local gate (Python gate, Node gate, all generator `--check`
  gates, process smokes) and full Compose smoke
  `sh tools/compose/smoke.sh slaif0075a` rc=0 with the `media-e2e`
  contract expectation extended to the post-finalization public read
  (update the expectation line accordingly).

### R9 - Current-truth documentation (durable wording; verified merge
facts only; no live-state claims)

Exactly six surfaces, minimal edits, no other prose restructuring. All
edits use the actual post-078/9 text quoted in Section 2.

- (a) `oap/INCREMENTS.md` 078/8 row: already "Accepted and merged in
  PR #88 at `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19;
  078/8 is closed" — verify it; edit only if a residual "PR pending" /
  "opened at `078-8-a`" claim survives (adversarial sweep).
- (b) `oap/INCREMENTS.md` in-flight row (currently the 078/9 row, name
  cell "078/9: MapBlock OSM layer contract repair"): state cell ->
  "Accepted and merged in PR #89 at
  `d8b1d360add9d583fa2cc64c451dd5d6faad8730` on 2026-09-20; 078/9 is
  closed" (the 079-bound sentence currently in that row is preserved in
  the replacement row below).
- (c) `oap/INCREMENTS.md`: add one final table row after the 078/9
  row: name cell "079/1: media publication core", state cell:
  "Opened at `079-a` from verified remote main
  `d8b1d360add9d583fa2cc64c451dd5d6faad8730`; PR pending; strategy
  owns acceptance and merge. No further ordinary 078 product
  increments are planned. Objective 078 is closed at the 078/079 seam
  (all non-media 078 contracts accepted and merged, including the
  078/9 layer-contract repair); the 078-bound catalog types (Gallery,
  LogoGrid, DocumentList) and real Image rendering proceed under
  Objective 079 (079/1, 079/2, 079/3); numeric 078 remains PARTIAL
  until 079/3 lands and is independently verified; strategy selects
  the next bounded increment per
  [`governance/2026-09-14-increment-qualified-round-ids.md`](governance/
  2026-09-14-increment-qualified-round-ids.md)".
- (d) `oap/INCREMENTS.md` preamble: extend the merge-fact sentence to
  "Increments 078/1 through 078/9 are accepted and merged (verified
  merge facts in the table below); the 078/079 seam is acknowledged —
  the three remaining catalog types and real Image rendering are
  079-bound by dependency audit".
- (e) `oap/MVP-PROGRESS.md`: "Active and remaining sequence" paragraph
  — after the 078/8 merged clause append "increment 078/9 is accepted
  and merged in PR #89 at `d8b1d360add9d583fa2cc64c451dd5d6faad8730`
  on 2026-09-20; increment 079/1 is opened at `079-a` (PR #NN)" (NN =
  actual PR number); keep the OAP/GitHub-authoritative sentences.
  Status table row 078 — after the 078/8 merged clause append "and
  increment 078/9 is accepted and merged in PR #89 at
  `d8b1d360add9d583fa2cc64c451dd5d6faad8730` on 2026-09-20". Status
  table row 079: "PARTIAL" -> "PARTIAL — 079/1 is opened at `079-a`
  (PR #NN)".
- (f) `README.md` capability row "Objective-078/4 page-style data plane
  (merged)": before the final GitHub-authoritative sentence, insert
  "increment 078/9 (MapBlock OSM layer contract repair) is accepted
  and merged in PR #89 at `d8b1d360add9d583fa2cc64c451dd5d6faad8730`
  on 2026-09-20; the 078/079 seam is acknowledged with the remaining
  catalog types 079-bound; increment 079/1 (media publication core) is
  opened at `079-a` (PR #NN);". Keep the GitHub-authoritative
  sentence.
- (g) `oap/MVP-CONTRACT-AUDIT.md` media row (42): Next cell -> "079/1:
  Agent media create/reference, public/preview media core,
  promotion-callable finalization primitive, real Image rendering;
  083: promotion-time finalization call, anonymous public reads gated
  on the accepted revision, rollback". Leave the evidence cell
  unchanged at this head (079/1 is in flight; the next increment's
  order carries the evidence update).
- (h) `CRITICAL.md`: verify-only (historical banner already in
  place); edit only if a current-state media/078/079 claim is actually
  found, minimal durable wording.
- Durable-wording rule: no "pending", "still open", "in flight", or
  present-tense live-state claims outside the standard in-flight row
  form; GitHub remains authoritative for live state; the next merge
  must not make committed truth false.

### R10 - dragUntil flake stabilization (test infrastructure only)

Disclosed, predeclared test-infrastructure supporting item (not a
product family). Context: the documented Puck-drag VM flake class
(`tests/e2e` governance project, `dragUntil`) recurred four times
across 078/7-078/8 and consumed the 078-8 re-run budget. This PR's
E2E suite runs the same governance project; the flake must be
stabilized at the test-infrastructure level before the new
`media-publication` spec lands.

- Allow (test files/helpers only, e.g. `governance.spec.ts` and its
  drag helper module): deterministic drag mechanics (bounded
  intermediate mouse steps with waits on deterministic element state),
  explicit bounded waits/timeouts where a race was observed, and
  environment-hardening within the existing Playwright configuration.
- Forbid (any violation = BLOCKED, not a fix): removing, weakening, or
  reordering any contract assertion; skipping or `test.fixme`-ing any
  contract; unbounded retries; changes to product code, the renderer,
  the Puck adapter, or any non-test file to chase the flake.
- Acceptance: the full local E2E gate (all projects) green without
  re-runs; the `puck-editor-round-trip-through-human-editor-api`
  contract's assertions are byte-identical in meaning (same scenarios,
  same assertions; mechanics may differ).
- Flake policy for this order: after R10 lands, at most ONE documented
  unmodified re-run of the CI run is permitted, and only if the
  documented flake class (same contract, same failure signature)
  recurs; every other failure must be fixed in code, not re-run.

### R11 - Hard constraints (all of 078-8-a apply unchanged)

No `tools/supply_chain/`, `tests/supply_chain/`, `.github/workflows/`
changes; `uv.lock`/`pnpm-lock.yaml` byte-identical to base; no new
dependency; no new migration beyond R1's single revision; no new
endpoint beyond R3/R5; no new scope string; no secrets in diff or
report; no deployment/trust change.

## 7. Acceptance criteria (observable)

1. Migration up/down clean on PG14-18; `content.media_asset.
   public_status` / `published_at` present; `060_001` and all catalog artifacts
   byte-identical to base (no catalog change).
2. `publish_public` + finalization unit suite green: idempotency,
   digest verification, exact failure manifests, GC-able-only failure
   residue.
3. Public digest route: unauthenticated byte-identical read with the
   exact `Cache-Control: public, max-age=31536000, immutable` header;
   404 (not 403) for non-public/absent digests; exact public line in
   both edge adapters; `.staging`/artifact paths unrouteable
   (negative probes green).
4. Preview read authorization matrix green (member/foreign-site/
   revoked/session-less/staging-path all fail-closed); agent upload +
   byte read green with COW audit rows exact.
5. Real `Image` renderer: markup pins green including fail-closed
   placeholder; preview/public parity byte-pinned; no inline styles or
   event handlers.
6. Hostile E2E suite (>= 12 cases) green with exact bounded error keys;
   SVG upload rejected; dimension/size bounds enforced; restart proof
   green.
7. OpenAPI diff exactly the R7 delta; drift gate green.
8. All five R9 surfaces updated with durable wording; an adversarial
   sweep for stale live-state claims ("078/8 is opened", "PR pending"
   for 078/8, "Agent media in 079" as the sole plan) over README,
   INCREMENTS, MVP-PROGRESS, MVP-CONTRACT-AUDIT, CRITICAL.md returns
   nothing.
9. `dragUntil` stabilization within R10 bounds; full local E2E gate
   green without re-runs; assertion set unchanged in meaning.
10. No R11 constraint violated (lockfiles byte-identical, no gate
    changes, no new dependency/scope/migration).
11. CI: all 20 required checks successful on the exact report-only head
    (strategy verifies independently).

## 8. Verification and workflow

- Local authority as usual (packages, browsers, databases, services,
  tests, CI logs are yours).
- GitHub: create branch + PR (next available number; GitHub assigns;
  exactly one PR) from verified `main`; push every
  commit; on completion commit the activated order, `oap/active`
  (= `079-a`), and the report to the PR branch WITHOUT changing
  strategic-owned order/active content; the report publication commit
  is report-only with `Report publication commit: SELF`; its parent is
  the literal implementation-head SHA.
- Do not merge; strategy is the only merger.
- Flake policy per R10 (one documented unmodified re-run, flake class
  only).

## 9. Report requirements

`oap/reports/079-a-media-publication-core.md`: work-order file +
sha256, `oap/active` bytes, PR/branch/head SHAs (base, start,
implementation head, SELF), per-requirement evidence (R1-R11) with
exact command outputs for the gates and the smoke final status lines,
the public-route byte-identity + header pins, the hostile-suite results
table, honest status (COMPLETE only if every requirement's named
evidence actually ran — otherwise PARTIAL/BLOCKED with the exact gap),
cumulative base->head size table grouped per 2026-09-14 review-unit
governance Section 2 (base =
`d8b1d360add9d583fa2cc64c451dd5d6faad8730`), predeclared-budget check,
safety/scope confirmations (no endpoints/scopes/migrations beyond
R1/R3/R5, no deps, no gate changes; no secrets in diff/report), and the
exact CI state at the implementation head.

## 10. Predeclared review budget (2026-09-14 review-unit governance
Section 1)

- Production/config: at most 14 files (`media_service/store.py`;
  `media_service/media_http.py`; `media_service/finalize.py` new;
  `MediaAssetRecord` model + repository mapping;
  `agent_api/agent_http.py`; `control_api/route_policy.py`; the
  composition media-reference validation integration point;
  `render_api/projection.py`;
  `apps/web/src/renderer/components.tsx`; `renderer-v1.css`;
  `nginx.conf`; `slaif-agent-site.conf`).
- Migrations: 1 (R1, downgrade-safe).
- Tests/evidence: at most 7 files (`test_media_public_core.py` new;
  `test_edge_contract.py`; `renderer-behavior.test.ts`; the new
  `media-publication` E2E spec; the `smoke.sh` expectation line; the
  `dragUntil` helper/governance spec stabilization; the
  `media-e2e` contract extension if it lives in a separate file).
- Generated artifacts: at most 2 (`agent-v1.json`; none other — no
  catalog/design-system change).
- Docs: at most 5 files (README, INCREMENTS, MVP-PROGRESS,
  MVP-CONTRACT-AUDIT; CRITICAL.md only if R9(g) finds a stale claim).
- OAP transcript: order + active + report.
- Substantive implementation-line scale: at most 2.0k.
- This is a fresh single-family PR (media publication core) plus the
  disclosed R10 test-infrastructure item. The ~20-30 implementation-
  file / several-thousand-substantive-line threshold remains a REVIEW
  TRIGGER, not a quota. If the cumulative trigger is crossed mid-round,
  the PR enters CLOSURE_ONLY per Section 3 of the same amendment: no
  new semantic family, only finite defects/evidence.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Every strategic review of this PR calculates base -> current head
  CUMULATIVE size, grouped per Section 2.
- If strategy rejects a completion claim after substantive
  implementation, or the cumulative trigger is crossed, the PR enters
  CLOSURE_ONLY (Section 3) — no new semantic family, no adjacent
  feature, no opportunistic scope.
- On rejection, strategy publishes one finite checklist of unresolved
  criteria with the exact executable evidence for each (Section 4). A
  later report may claim COMPLETE only if every named criterion was
  actually executed.
- Separable functionality starts from verified merged main in another
  PR (Section 5).

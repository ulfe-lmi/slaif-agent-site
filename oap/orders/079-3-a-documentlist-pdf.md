# OAP Work Order — 079-3-a (document class: PDF policy + DocumentList)

> Strategic work order. Executor: coding agent. Reviewer/acceptor/merger:
> strategic model. This order is IMMUTABLE once activated; corrections,
> if ever needed, use the next letter (079-3-b) and a new order.

## 1. Identifier and mode

- Round ID: `079-3-a` (increment-qualified; first round of semantic
  increment 3 of numeric Objective 079; the FINAL increment of numeric
  079).
- Objective: 079 (079/3 — document class: bounded PDF policy + DocumentList).
- PR mode: CREATE_NEW_PR.
- Branch: `oap/079-3-a-documentlist-pdf`, created from verified current
  `main` = `c149c39e66978c9ee53a7d92300a64e4297cfa56` (the 079/2 merge
  commit, re-verified against live GitHub at activation).
- Expected PR number: next available (GitHub assigns; create exactly one
  PR; do not create, amend, or touch any other PR; dependabot PRs
  #83/#90/#94 are out of scope).
- Depends on 079/1 (public digest route, preview read path, descriptor
  mechanism, finalization primitive) and 079/2 (list-valued media-
  reference descriptor resolution, per-item MIME-class mutation
  validation, 31-type catalog).

## 2. Verified current state (strategy-verified 2026-10-04 against live
GitHub and the local checkout at this exact head)

- Remote `main` = `c149c39e66978c9ee53a7d92300a64e4297cfa56` (the 079/2
  merge commit; remote post-merge `CI` and `CodeQL` runs both successful
  at this head).
- PR #92 (079/1): MERGED at `577509e7bc990d85a10af5954bee3c6f7c888a4f`
  (2026-09-22). PR #93 (079/2): MERGED at
  `c149c39e66978c9ee53a7d92300a64e4297cfa56` (2026-10-04). No OAP
  product PR is currently open.
- Delivered by 079/1: public namespace,
  `content.media_asset.public_status` + `published_at`,
  `finalize_media_for_promotion(site_id, workspace_id, media_ids)` in
  `media_service/finalize.py`, public digest route
  `GET /v1/public/sha256/<2>/<2>/<digest>` (edge
  `/media/public/sha256/<2>/<2>/<digest>`, `Content-Type` from the
  validated record, `Cache-Control: public, max-age=31536000,
  immutable`, 404 when not public), preview read via the existing
  authenticated `GET /v1/sites/{site_id}/assets/{media_id}/content`,
  Agent media create/byte-read, real `Image` renderer with projection
  media-descriptor resolution. Delivered by 079/2: `Gallery` +
  `LogoGrid` (catalog 31), projection descriptor resolution for
  list-valued media-reference props, per-item image-class validation in
  the component-props validation integration point, `dragUntil`
  stabilization.
- Media: `SUPPORTED_MIME = frozenset({"image/png", "image/jpeg"})`
  (`media_service/store.py`), `sniff_mime(prefix, declared)` content-
  signature check, default `max_upload_bytes` 100 MiB; table
  `content.media_asset` (023_001); NO public-namespace GC/retention
  semantics (that remains the 083 contract).
- Component catalog: 31 types (verified at this head in both generated
  `catalog-v1.json` files). `DocumentList` is the ONLY missing
  architecture type (category table: institutional); absent from the
  renderer. `Gallery` and `LogoGrid` present; `MapBlock` carries the
  corrected `mapnik`/`cyclemap`/`transportmap` layer contract (078/9).
- Precedents: catalog type addition pattern from 078/7 and 078/8:
  declaration in `component_catalog.py`, deterministic in-place `060_001`
  baked-catalog regeneration + `CATALOG_V1_REVIEWED_SHA256`, OpenAPI
  diff `x-slaif-*`-only (strip-identity rule), Puck consumes the
  generated catalog config (no Puck adapter code changes). Count pins
  (mechanical-ripple class, four files): `test_component_catalog.py`
  (`len(COMPONENT_CATALOG)`), `tools/compose/public_agent_acceptance.py`
  (`len(catalog["components"])`), and the two generated
  `catalog-v1.json` files (`packages/component-catalog`,
  `packages/composition-schema`) via the generator `--check` gates.
- OpenAPI: 47 paths at this head; strip-identity rule per 078/7-078/8.
- `oap/active` = `079-2-h` (last activated round of the merged 079/2;
  protocol-correct idle state until this activation).
- Flake policy: 079/1's R10 stabilized `dragUntil`; this order
  re-declares: at most ONE documented unmodified CI re-run, and only
  for the documented flake class with its exact failure signature; any
  other recurrence is a real failure — fix in code or report BLOCKED.

## 3. Strategic context

This is the final increment of numeric 079 and closes the last 078-bound
catalog type (`DocumentList`) together with the architecture's document-
class serving boundary (Section 14: size/signature/PDF-page bounds;
Section 12: bounded document class). After it merges: catalog 32/32 and
the last 078-bound catalog type is closed; numeric 078 REMAINS PARTIAL
until strategy independently verifies the 079/3 evidence post-merge
(human decision D1: the numeric-078 COMPLETE reclassification is
post-merge strategy bookkeeping, never a claim inside this PR); numeric
079 then becomes COMPLETE for its scoped gaps (the public-namespace
unreferenced-deletion/retention semantics remain the 083 contract per
the dependency-graph reassessment, because they require promotion,
retention clearance, and the backup policy). Next per the safety-
critical path: 081 exact Agent-workspace Puck. One bounded semantic
family (document class: upload policy + reference component +
rendering); no new routes; no migration.

## 4. Bounded scope

Exactly: the bounded PDF upload policy (MIME + signature + size + page
count, stdlib only, R1); the `DocumentList` catalog type with bounded
document-reference list props (R2); document-class mutation/editor
validation including the image-class regression negatives (R3); the
projection descriptor resolution for document-class list props; the
trusted `DocumentList` renderer; regenerated generated artifacts
(R5); the five current-truth doc updates (durable wording, R6); and
full evidence per R7. Nothing else.

## 5. Explicit non-goals

- No new server route or route change: the 079/1 public digest route and
  preview route serve PDFs with the record's `mime_type`; no route is
  added or modified.
- No migration file (in-place `060_001` baked-catalog regeneration
  only, 078/7-078/8 precedent; no physical schema change).
- No new OpenAPI path or scope string (catalog delta is `x-slaif-*`-
  only; strip-identity rule).
- No changes to `finalize_media_for_promotion`, `media_gc`, or public-
  namespace retention/deletion (083 contract).
- No changes to `Gallery`/`LogoGrid`/`Image` behavior beyond the
  REQUIRED regression-negative coverage of R3: if a post-079/2 check
  gap is found (an image-class component accepting a PDF reference),
  that is a bounded defect of this family, fixed and disclosed in this
  PR.
- No non-PDF document MIME class (PDF is the document class of this
  increment; adding other document classes is a future increment only
  if architecture ever requires it — it does not).
- No data binding, collection views, or generic data-driven behavior.
- No Puck adapter code changes (Puck consumes the generated catalog
  config); no global-region/header-footer/theme changes (078/5 closed
  contract); no collection-semantics changes (078/7 closed contract).
- No new dependency (stdlib only: `zlib`, `re`); NO changes under
  `tools/supply_chain/`, `tests/supply_chain/`, or
  `.github/workflows/`; no lockfile change; no Dependabot PR work; no
  preview flight-free contract change (`clientState={false}`).

## 6. Requirements

### R1 - Bounded PDF policy (media store, stdlib only)

- New module `media_service/pdf_policy.py` (no HTTP, no DB, no
  dependency):
  - Constants: `PDF_MAX_PAGES = 200`, `PDF_MAX_BYTES = 20 * 1024 * 1024`
    (independent of the generic `max_upload_bytes`), `PDF_SIGNATURE =
    b"%PDF-"`.
  - `pdf_page_count(data: bytes) -> int | None` — bounded page count:
    count word-boundary occurrences of the `/Type /Page` token (NOT
    matching `/Type /Pages`) in the raw bytes; additionally, for each
    `stream ... endstream` segment with a FlateDecode filter, zlib-
    decompress under a hard decompressed-length cap (50 MiB; exceeding
    it aborts with `None`) and count occurrences in the decompressed
    content; stop counting after 201 total matches (return the 201
    sentinel); return `None` (undetermined) when no page objects are
    found in raw or decompressed content or on any structural failure.
- `media_service/store.py`:
  - Extend `SUPPORTED_MIME` with `application/pdf`.
  - `sniff_mime`: declared `application/pdf` accepted only when the
    prefix starts with `PDF_SIGNATURE`; all other classes unchanged.
  - Upload path, after the size/signature/MIME checks pass, for
    declared `application/pdf`: size above `PDF_MAX_BYTES` -> reject
    with exact key `media-pdf-too-large`; `pdf_page_count` returns
    `None` -> reject `media-pdf-structure-invalid` (fail-closed);
    count above `PDF_MAX_PAGES` -> reject `media-pdf-too-many-pages`.
    Every rejection happens BEFORE any staging publish; no partial
    artifacts. The human edge route and the Agent upload share this one
    store enforcement point (no per-route policy logic).
  - The existing image path and its existing bounded error keys are
    unchanged.
- Unit (new `services/backend/tests/unit/test_pdf_policy.py` plus store
  upload extension):
  - Accept: 1-page PDF; exactly 200-page PDF (generated fixture);
    Flate-compressed page-object PDF; mixed raw + compressed objects.
  - Reject: 201 pages (`media-pdf-too-many-pages`); above 20 MiB
    (`media-pdf-too-large`); declared PDF with a non-`%PDF-` prefix
    (existing signature-mismatch key); undetermined structure
    (`media-pdf-structure-invalid`); decompression bomb (decompressed
    above 50 MiB -> undetermined -> `media-pdf-structure-invalid`).

### R2 - DocumentList catalog type (31 -> 32)

In `services/backend/src/slaif_agent_site/content_model/
component_catalog.py`, following the established entry pattern exactly:

- `DocumentList` (category `institutional`, authority_class
  `content`, binding_kind `media_asset`, leaf: `max_children` 0, no
  slots):
  - `title`: authority `content`, localized true, optional, 1..120,
    type string.
  - `items`: authority `content`, required, 1..12 objects, each
    EXACTLY:
    - `mediaId`: reference/uuid, required.
    - `label`: string, required, 1..120 (item-level pattern: no item-
      level localization, consistent with the merged Statistics/
      Timeline/FAQ item entries).
- No item or component prop exposes raw `url`, `href`, `html`,
  `style`, `class`, or script-like input; `mediaId` references are the
  ONLY document input, and renderers get resolved descriptors (R4).
- Deterministic migration: N/A (new type, no existing instances) —
  state this in the catalog entry metadata exactly as 078/7 did.
- Regenerate ALL generated artifacts (catalog-v1.json in
  `packages/component-catalog` and `packages/composition-schema`,
  in-place `060_001` baked-catalog JSON + SHA guard, agent-
  openapi); all generator `--check` gates zero-diff afterwards.
- Count pins (mechanical-ripple class, disclosed per file):
  `test_component_catalog.py` 31 -> 32; `public_agent_acceptance.py`
  31 -> 32; the two generated catalog-v1.json files via regeneration.

### R3 - Document-class mutation and editor enforcement

Wire document-class item validation into the component-props validation
path used by BOTH the Agent mutation path and the human Editor/Puck API
path (the 078/7 integration point as extended by 079/1 R5 composition
media-reference validation and 079/2 per-item validation). Per
DocumentList item: `mediaId` exists, same site, `mime_type` is
`application/pdf` (document class). Bounded error keys:
`doclist.item-missing`, `doclist.item-foreign-site`,
`doclist.item-not-pdf`, `doclist.items-out-of-range`. Invalid input ->
bounded 422 on the Agent path with the exact error key (no user-input
echo); equivalent Editor rejection. Tree unchanged, row version
unchanged, idempotency/audit unchanged.

- REQUIRED regression negatives (R1 makes PDFs uploadable): Gallery
  items, LogoGrid items, and the Image `mediaId` prop must reject
  references to `application/pdf` assets with their exact existing
  image-class keys (`gallery.item-not-image`, `logogrid.item-not-
  image`, and the 079/1 Image-class key). Cover with unit + E2E
  negatives. If any of these checks is missing or wrong on the
  post-079/2 main, that is a bounded defect of this family: fix it in
  this PR and disclose it in the report.

### R4 - Projection and trusted renderers

- `render_api/projection.py`: extend 079/2's list-valued media-
  reference descriptor resolution to the document class: each
  DocumentList item `mediaId` resolves to `{url, mime_type,
  size_bytes}` (preview: 079/1 preview URL; public: 079/1 digest URL
  only when `public_status='public'`, else fail-closed marker) — same
  mechanism, document-class MIME check. Re-validate props at
  projection time (defense in depth, 078/8 pattern).
- `apps/web/src/renderer/components.tsx` (+ `renderer-v1.css`),
  deterministic attribute order, no JS/event handlers, no inline style
  attributes, no `target`/`sandbox` attributes (same-origin URLs):
  - `DocumentList`: `<section class="sl-doclist">` containing an
    optional `<h3>` for `title` and `<ul class="sl-doclist__items">`
    with one `<li>` per item; each resolved item renders
    `<li><a class="sl-doclist__link" href="<descriptor.url>"><span
    class="sl-doclist__label"><escaped label></span></a></li>`; each
    fail-closed item renders the 079/1 placeholder pattern in the same
    `<li>` (same class, role, and aria-label semantics).
  - CSS: document-list styling (label links, CSS-only hover state),
    responsive desktop/tablet/phone; no remote assets.
- The PDF is served by the 079/1 public digest route (exact
  `Content-Type: application/pdf` from the record + immutable cache
  headers — verify in evidence) and the 079/1 preview route. No new
  routes.
- Preview and public render the identical markup except the `href`
  form (079/1 parity rule; byte-pinned).
- No CSP change required (same-origin navigation, not embed); verify
  the public CSP is unchanged in the edge-contract evidence.

### R5 - OpenAPI (exact delta)

Regenerate `contracts/openapi/agent-v1.json`. Diff against base:
`x-slaif-*` extension keys ONLY (catalog change documented under the
existing component-content extension keys); after stripping all
`x-slaif-*` keys the canonical JSON is byte-identical to base; 47 paths
unchanged (078/7-078/8 decision-8 adjudication rule); no new scope
strings. Drift gate green.

### R6 - Current-truth documentation (durable wording; verified merge
facts only; no live-state claims)

Exactly five surfaces, minimal edits. Verified immutable facts to use
(strategy-verified against GitHub at activation): 079/2 accepted and
merged in PR #93 at `c149c39e66978c9ee53a7d92300a64e4297cfa56` on
2026-10-04. `PR #NN` below = the PR number GitHub assigns to THIS PR at
creation time (record it exactly in the report and in every doc line
that uses it).

- (a) `oap/INCREMENTS.md`: flip the 079/2 row to "Accepted and merged
  in PR #93 at `c149c39e66978c9ee53a7d92300a64e4297cfa56` on
  2026-10-04; 079/2 is closed". Add the 079/3 row in the standard
  in-flight form used for the 079/2 row ("Opened at `079-3-a` from
  verified remote main
  `c149c39e66978c9ee53a7d92300a64e4297cfa56`; PR pending; strategy owns
  acceptance and merge"). The `Next` row already carries the correct
  durable wording ("079/3 (DocumentList and document serving) closes
  the last 078-bound catalog type (32/32); numeric 078 remains PARTIAL
  until 079/3 lands and is independently verified; strategy selects the
  next bounded increment per
  `governance/2026-09-14-increment-qualified-round-ids.md`") — VERIFY
  it only; do not rewrite it.
- (b) `oap/MVP-PROGRESS.md`: (1) "Active and remaining sequence"
  paragraph — replace "increment 079/2 (Gallery + LogoGrid) is opened
  at `079-2-a` (PR #93)" with "increment 079/2 (Gallery + LogoGrid) is
  accepted and merged in PR #93 at
  `c149c39e66978c9ee53a7d92300a64e4297cfa56` on 2026-10-04; increment
  079/3 (DocumentList + document class) is opened at `079-3-a`
  (PR #NN)". (2) 078 status row — replace "Gallery and LogoGrid are
  delivered by 079/2 in flight at `079-2-a`; DocumentList remains
  079/3" with "Gallery and LogoGrid are delivered by 079/2 accepted and
  merged in PR #93 at
  `c149c39e66978c9ee53a7d92300a64e4297cfa56`; DocumentList is opened at
  `079-3-a` (PR #NN)"; keep "numeric 078 remains PARTIAL until 079/3
  lands". (3) 079 status row — replace "079/2 is opened at `079-2-a`
  (PR #93)" with "079/2 is accepted and merged in PR #93 at
  `c149c39e66978c9ee53a7d92300a64e4297cfa56` on 2026-10-04; 079/3 is
  opened at `079-3-a` (PR #NN)". Keep the OAP/GitHub-authoritative
  sentences. Numeric 078 stays PARTIAL in every row.
- (c) `README.md` capability row: replace "increment 079/2 (Gallery +
  LogoGrid) is opened at `079-2-a` (PR #93)" with "increment 079/2
  (Gallery + LogoGrid) is accepted and merged in PR #93 at
  `c149c39e66978c9ee53a7d92300a64e4297cfa56` on 2026-10-04; increment
  079/3 (DocumentList + document class) is opened at `079-3-a`
  (PR #NN)"; keep the closing "GitHub is authoritative for live
  acceptance and merge state."
- (d) `oap/MVP-CONTRACT-AUDIT.md` media row (42): evidence cell — after
  the verified 079/1 clause, append "079/2 is accepted and merged in PR
  #93 at `c149c39e66978c9ee53a7d92300a64e4297cfa56` on 2026-10-04
  (catalog 31 with Gallery + LogoGrid); 079/3 is opened at `079-3-a`
  (PR #NN): document class (bounded PDF policy + DocumentList, catalog
  32 at PR head; E2E evidence in PR, acceptance strategy-owned)". Next
  cell — replace "079/2: Gallery + LogoGrid (in flight); 079/3:
  DocumentList + document serving;" with "079/3: DocumentList +
  document serving (in flight at `079-3-a`, PR #NN);" and append
  "public-namespace retention/GC" to the 083 clause. Do NOT state that
  079/3 is accepted, merged, or E2E-proven as of merge, and do NOT
  reclassify numeric 078 or 079 in any row (human decision D1:
  reclassification is post-merge strategy bookkeeping after
  independent verification).
- (e) `CRITICAL.md`: verify-only (historical banner present; entries
  annotated); edit only if an un-annotated current-state claim is
  actually found (durable wording).
- Durable-wording rule per 079/1 R9 (no live-state claims outside the
  standard in-flight row form; GitHub authoritative; the next merge
  must not make committed truth false).

### R7 - Evidence (all actually executed, honestly reported)

- Unit: R1 pdf_policy matrix (accept/reject with exact keys, 200-page
  boundary, 20 MiB boundary, bomb cap, fail-closed undetermined);
  DocumentList props validation positive/negative (bounds, exact error
  keys, foreign-site, non-PDF reference, duplicate items allowed,
  label bounds); projection document-class resolution (mixed resolved
  and fail-closed markers; public only when public; foreign-site
  marker); regression negatives (Gallery/LogoGrid/Image reject PDF
  references with the exact image-class keys).
- Renderer (extend `apps/web/tests/renderer-behavior.test.ts`): exact
  markup pins for DocumentList (title present/absent; resolved +
  fail-closed items), including forbidden-attribute absence (no inline
  style, no event handler, no `target`/`sandbox`).
- E2E (real browser through public NGINX, within the tests/e2e budget —
  extend the 079/1 media-publication spec or add one): upload a real
  2-page PDF; upload rejects (non-PDF declared as pdf, above 20 MiB,
  above 200 pages from a generated fixture, undetermined structure);
  composition with a DocumentList of real PDFs renders at
  desktop/tablet/phone; preview/public markup parity (identical except
  the href form); after 079/1-style direct finalization, public
  DocumentList links serve the PDF from the digest URLs byte-identical
  with `Content-Type: application/pdf` and the immutable cache
  headers; hostile Agent PATCH suite (>= 10 cases from the R3 error-
  key list) -> 422 with exact keys, tree/row-version unchanged; Editor
  path rejects the same; image-class negatives (Gallery/LogoGrid/Image
  referencing a PDF) rejected at composition.
- Catalog: generator `--check` gates zero-diff; in-place `060_001`
  consistent; count pins at 32 in all four places (disclosed per
  file).
- Full local gate (Python, Node, generator `--check`, process smokes)
  and full Compose smoke `sh tools/compose/smoke.sh slaif0075a` rc=0
  (extend the smoke expectation line for the document class if the
  079/1/079/2 pattern extended it).

### R8 - Hard constraints (079/1 R11 applies unchanged)

No supply-chain/workflow/lockfile changes; no new dependency (stdlib
only); no new migration file; no new endpoint/scope; no secrets in diff
or report.

## 7. Acceptance criteria (observable)

1. Catalog has exactly 32 types including DocumentList with the R2 prop
   contracts; all generator `--check` gates zero-diff; in-place
   `060_001` consistent; all four catalog-count pins updated.
2. PDF policy unit matrix green (200-page boundary accept; 201 reject;
   above-20 MiB reject; undetermined fail-closed; bomb cap; exact
   keys).
3. Upload rejects green on BOTH the human and Agent paths
   (`media-pdf-too-large`, `media-pdf-too-many-pages`,
   `media-pdf-structure-invalid`; existing signature keys unchanged).
4. Mutation/Editor validation green with every exact R3 key; no
   tree/version change on rejection; image-class regression negatives
   green.
5. Projection document-class descriptor resolution green (preview/
   public rules; fail-closed markers).
6. Renderer markup pins green including forbidden-attribute absence and
   fail-closed items; preview/public parity byte-pinned.
7. E2E green: real PDF render at three viewports, hostile rejections,
   public byte-identity + exact headers after finalization.
8. OpenAPI strip-identity proven (sha256 both sides after stripping
   `x-slaif-*`); drift gate green; 47 paths unchanged.
9. All five R6 doc surfaces updated with durable wording; numeric 078
   remains PARTIAL in every row (no COMPLETE reclassification);
   adversarial sweep for stale 079/2 in-flight wording returns
   nothing.
10. No R8 constraint violated (lockfiles byte-identical, no gate
    changes, no new dependency/scope/migration/route).
11. CI: all 20 required checks successful on the exact report-only head
    (strategy verifies independently).

## 8. Verification and workflow

- Local authority as usual (packages, browsers, databases, services,
  tests, CI logs are yours).
- GitHub: create branch + PR from verified `main` (post-079/2); push
  every commit; on completion commit the activated order, `oap/active`
  (= `079-3-a`), and the report to the PR branch WITHOUT changing
  strategic-owned order/active content; the report publication commit
  is report-only with `Report publication commit: SELF`; its parent is
  the literal implementation-head SHA.
- Do not merge; strategy is the only merger.
- Flake policy per Section 2 (one documented unmodified re-run,
  documented flake class only).

## 9. Report requirements

`oap/reports/079-3-a-documentlist-pdf.md`: work-order file + sha256,
`oap/active` bytes, PR/branch/head SHAs (base, start, implementation
head, SELF), per-requirement evidence (R1-R8) with exact command
outputs, the OpenAPI strip-identity proof (sha256 both sides), honest
status (COMPLETE only if every requirement's named evidence actually
ran — otherwise PARTIAL/BLOCKED with the exact gap), cumulative
base->head size table grouped per 2026-09-14 review-unit governance
Section 2 (base = the verified post-079/2 main SHA
`c149c39e66978c9ee53a7d92300a64e4297cfa56`), predeclared-budget check,
safety/scope confirmations, and the exact CI state at the
implementation head.

## 10. Predeclared review budget (2026-09-14 review-unit governance
Section 1)

- Production/config: at most 10 files (`pdf_policy.py` new;
  `store.py`; `component_catalog.py`; `projection.py`; the component-
  props validation integration point; `components.tsx`;
  `renderer-v1.css`; in-place `060_001` regeneration;
  `public_agent_acceptance.py` count pin).
- Migrations: 0 (in-place `060_001` baked-catalog regeneration only).
- Tests/evidence: at most 5 files (new `test_pdf_policy.py`; unit
  validation extension; `renderer-behavior.test.ts` extension; the E2E
  spec extension; `test_component_catalog.py` count pin).
- Generated artifacts: at most 4 (catalog-v1.json x2, agent-v1.json,
  in-place 060_001).
- Docs: at most 5 files (README, INCREMENTS, MVP-PROGRESS,
  MVP-CONTRACT-AUDIT; CRITICAL.md only if R6(e) finds a stale claim).
- OAP transcript: order + active + report.
- Substantive implementation-line scale: at most 1.2k.
- Fresh single-family PR; the ~20-30 file / several-thousand-line
  threshold remains a REVIEW TRIGGER, not a quota; CLOSURE_ONLY per
  Section 3 of the amendment if the trigger is crossed or a completion
  claim is rejected.

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

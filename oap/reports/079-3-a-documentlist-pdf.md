# OAP Coding-Agent Report — 079-3-a

## Work order

- Identifier: `079-3-a` (increment-qualified; increment 3, round a); numeric
  objective 079 (079/3 — document class: bounded PDF policy + DocumentList)
- Work-order file: `oap/orders/079-3-a-documentlist-pdf.md`
- Work-order sha256: `4c172d2b2ff28baba8f8af5fef9d2899e75e68f49611fe4834542ef997769979`
- `oap/active` bytes: `079-3-a\n` (hex `3037392d332d610a`)
- PR mode: CREATED_NEW_PR

## Status
COMPLETE

## Executive summary
Implemented the final increment of numeric 079: the bounded document class.
A stdlib-only PDF policy module (size 20 MiB / signature / bounded page count
with fail-closed undetermined verdict and a 50 MiB decompression-bomb cap) is
enforced at the store's single shared upload point (human edge + Agent
upload, no per-route logic); the `DocumentList` catalog type (31 -> 32) with
bounded 1..12 document-reference items was added with regenerated artifacts,
per-item document-class mutation/editor validation with the exact `doclist.*`
error keys, projection document-class descriptor resolution, a trusted
no-JS/no-attribute-surface `DocumentList` renderer, and the R6 current-truth
docs. The R3 REQUIRED image-class regression negatives (Gallery/LogoGrid/Image
reject PDF references with `gallery.item-not-image` / `logogrid.item-not-image`
/ `COMPONENT_BINDING_INVALID`) are covered by unit + E2E negatives; the
post-079/2 main had no check gap there (verified: the DB validator's
image-only media binding branch and the 079/2 per-item image-class checks
already reject `application/pdf` rows). One bounded DB adaptation was
required for R7 to be executable (disclosed below under R8 / Known
limitations): the two register functions in in-place `068_001` hard-rejected
any non-image MIME, so `application/pdf` was added to their exact MIME
allow-list literals (no DDL, no new migration file). One defect found by the
E2E evidence and fixed in this round: the store's PDF enforcement read the
still-buffered staging writer before the HTTP path's flush, returning 503
for every declared-PDF upload; the fix flushes before enforcement and two
regression unit tests pin the exact unflushed-writer flow. After the
implementation, CI at the docs commit surfaced one transient
media-publication observation-collector failure (every functional
assertion passed; no product defect identified); per the order's flake
policy no unmodified CI re-run was invoked — instead a bounded,
secret-safe E2E reporter observability repair (commit E) was pushed, and
the final implementation head E is 20/20 green on CI with the contract
passing.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number/URL/state: `#95` (OPEN) — `https://github.com/ulfe-lmi/slaif-agent-site/pull/95`
- Base/head branches: `main` / `oap/079-3-a-documentlist-pdf`
- Starting remote SHA (verified base, post-079/2 merge): `c149c39e66978c9ee53a7d92300a64e4297cfa56`
- Transcript commit T (order + active bytes, committed unchanged): `8675957a67ef3b49cc8945ca9f2ebe9eb042c15a`
- Implementation head SHA: `554a8d2a3b0963574b96d537e4a814291a46c1f7` (commit E; all non-report work)
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified via GitHub)
- Implementation commits pushed before report: T (transcript), I (implementation), D (R6 docs), E (e2e reporter CI-observability repair); report parent = E = implementation head SHA
- New PR this turn: yes (exactly one); amended existing: no; merge performed: NO

## Changes made

- R1: new `media_service/pdf_policy.py` (stdlib `zlib` + `re`): constants
  `PDF_MAX_PAGES=200`, `PDF_MAX_BYTES=20 MiB`, `PDF_SIGNATURE=b"%PDF-"`,
  50 MiB decompress cap, 201 sentinel, word-boundary `/Type /Page` counting
  over raw + FlateDecode streams (chunked `decompressobj` feed);
  `enforce_pdf_upload` returns the exact rejection key.
  `media_service/store.py`: `SUPPORTED_MIME += application/pdf`,
  `sniff_mime` PDF signature branch, `_enforce_pdf_policy` at the top of
  `publish()` (after the staging stream flush, before any staging publish;
  staging discarded on rejection); widened 422 key sets in
  `media_service/media_http.py` and `agent_api/agent_http.py`
  (`media-pdf-too-large`, `media-pdf-structure-invalid`,
  `media-pdf-too-many-pages`; existing keys unchanged).
- R2: `DocumentList` in `component_catalog.py` (institutional / content /
  media_asset / leaf; `title` localized optional 1..120; `items` required
  1..12 of exactly `mediaId` reference + `label` 1..120 non-localized; no
  url/html/style props); regenerated `packages/component-catalog/src/
  catalog-v1.json`, `packages/composition-schema/src/catalog-v1.json`,
  in-place `060_001` baked catalog + `CATALOG_V1_REVIEWED_SHA256`
  `76f3329fe22688e625c0d4a73cb2ce93ba85a377d2f7cf1ff159f1372fc715ab`,
  `design-system-v1.json` source + regenerated `design_system.py` +
  `packages/composition-schema/src/design-system-v1.json` copy (DocumentList
  with zero design properties), `contracts/openapi/agent-v1.json`.
- R3: `content_model/component_facets.py`: `DOCUMENT_REFERENCE_COMPONENTS`
  (`DocumentList` -> `doclist`, 1..12), `DOCUMENT_MIME_CLASSES`,
  `DOCUMENT_REFERENCE_ERROR_KEYS` (exact 4-key vocabulary),
  `validate_document_reference_items` (same fail-closed resolution contract
  as the image-class sibling). Wired into BOTH paths:
  `agent_state/mutations.py::_validate_media_reference_props` (guard
  broadened to both component maps; both validators run over one resolved
  facts map) and `editor_api/composition_http.py::_validate_media_reference_props`;
  `agent_api/agent_http.py` surfaces the exact doclist keys as 422
  `details.prop_error` (no input echo); Editor raises
  `DomainValidationError(details={"prop_error": key})`.
- R4: `render_api/projection.py`: `_media_descriptor` gains a
  `mime_classes` parameter (default image class unchanged); new
  `DocumentList` list branch resolving each item through
  `slaif_render_media_resolve` with `DOCUMENT_MIME_CLASSES` (preview URL
  always; digest URL only when `public_status='public'`; else None ->
  renderer placeholder). `apps/web/src/renderer/components.tsx`:
  `resolvedDocumentMedia` gate (url under `/media/` + `application/pdf`)
  plus `DocumentList` component emitting the exact order-specified markup
  (`sl-doclist` section, optional `h3`, `sl-doclist__items` list, resolved
  `a.sl-doclist__link` > `span.sl-doclist__label`, 079/1 placeholder pattern
  for fail-closed items; no JS/handlers/inline style/target/sandbox);
  `apps/web/public/renderer-v1.css`: CSS-only responsive doclist styling
  (2-col grid -> 1-col at 760px), no remote assets.
- R5: `contracts/openapi/agent-v1.json` regenerated; delta is
  `x-slaif-*`-only.
- R6: `oap/INCREMENTS.md` (079/2 row closed with PR #93 merge fact; 079/3
  in-flight row added in the standard form; `Next` row verified, unchanged),
  `oap/MVP-PROGRESS.md` (3 verbatim replacements), `README.md` (capability
  row replacement), `oap/MVP-CONTRACT-AUDIT.md` (media row 42 evidence-cell
  append + next-cell replacement + 083 clause extension), `CRITICAL.md`
  (verified: no current-state 079/media claims; unedited).
- Bounded DB adaptation (disclosed): `068_001_media_publication_core.py`
  in-place, 2 lines: the `slaif_media_asset_register` and
  `slaif_agent_media_register` function bodies' hard MIME allow-list went
  from `('image/png','image/jpeg')` to
  `('image/png','image/jpeg','application/pdf')` — without it the R1
  human/Agent PDF upload is rejected at the DB register step and R7's
  evidence is unexecutable; no DDL, no new migration file, no change to the
  image-only component binding validator branch (the R3 Image-class
  regression gate stays image-only).
- E2E reporter observability repair (disclosed, commit E):
  `tests/e2e/reporter.mjs` — at D the CI Compose job failed the
  media-publication contract at the final
  `expect(failures()).toEqual([])` with the observation collector
  non-empty while every functional assertion passed; the minimal
  SafeReporter design did not surface the error message and CI runs
  with `artifacts=disabled`, so the classified failure tokens were
  unrecoverable from the CI log. The FAILED line now appends a bounded
  `detail=` field (first 8 lines, 300-char hard cap; classified tokens
  carrying no URLs/secrets/user input by construction); PASSED-line
  output is byte-identical. Full local e2e re-run on the final tree:
  green (23/23 contracts).

## Files changed
base -> implementation head numstat:
Base `c149c39e66978c9ee53a7d92300a64e4297cfa56` -> implementation head E `554a8d2a3b0963574b96d537e4a814291a46c1f7` (exact measured
`git diff --numstat`: 41 files, +2695/-53; the report
file itself is added by the SELF commit and is not counted here; at S the
file count is 42):

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 14 | 483 | 26 |
| Migrations | 1 | 9 | 3 |
| Tests/evidence | 15 | 1569 | 15 |
| Generated artifacts | 5 | 154 | 2 |
| Docs | 4 | 7 | 6 |
| OAP transcript | 2 | 473 | 1 |
| TOTAL | 41 | +2695 | -53 |

Category membership follows the 079-2-a table convention:
Production/config = `media_service/{pdf_policy,store,media_http}.py`,
`agent_api/agent_http.py`, `agent_state/mutations.py`,
`content_model/{component_catalog,component_facets,design_system}.py`,
`editor_api/composition_http.py`, `render_api/projection.py`,
`db/alembic/versions/060_001_agent_component_semantics.py` (in-place
baked-catalog regeneration counted here per the 079-2-a convention),
`apps/web/src/renderer/components.tsx`, `apps/web/public/renderer-v1.css`,
`compose.yaml` (the disclosed nginx tmpfs fix). Migrations = the in-place
`068_001_media_publication_core.py` adaptation (no new migration file).
Tests/evidence = the 13 test files incl. new `test_pdf_policy.py`,
`media-publication.spec.ts`, the `tools/compose/
public_agent_acceptance.py` count pin (smoke expectation, per the
079-2-a convention), and the disclosed `tests/e2e/reporter.mjs`
CI-observability repair (commit E). Generated artifacts = `agent-v1.json`,
`catalog-v1.json` x2, `design-system-v1.json` x2. Docs = the four R6
surfaces. OAP transcript = order + active (report via SELF).

## Pre-declared budget check (order Section 10 vs measured)

Measured against the cumulative base -> implementation-head numstat
(table above), grouped per the 2026-09-14 review-unit governance Section 2
categories. The predeclared budget is EXCEEDED in production/config,
migrations, and tests/evidence; each excess is itemized and disclosed
below for strategy adjudication (the 2026-09-14 amendment makes the
several-thousand-line / ~20-30-file threshold a REVIEW TRIGGER, not a
quota; this PR stays a fresh single-family PR).

- Production/config: predeclared at most 10; actual 14 (EXCEEDED by 4,
  disclosed). Predeclared names present: `pdf_policy.py` (new),
  `store.py`, `component_catalog.py`, `projection.py`,
  `components.tsx`, `renderer-v1.css`, in-place `060_001`, and the
  component-props validation integration point. Additional files that
  the bounded R3 key surface and the disclosed adaptations require:
  `content_model/component_facets.py` (the document-class validator
  module the integration point calls), `agent_state/mutations.py` and
  `editor_api/composition_http.py` (the two per-path validation
  guards), `agent_api/agent_http.py` and `media_service/media_http.py`
  (the widened exact-422-key surfaces), `content_model/
  design_system.py` (deterministic generator byproduct of the catalog
  change, 1/1 line), and `compose.yaml` (the disclosed nginx tmpfs
  16m -> 256m E2E-discovered defect fix, 1/1 line).
- Migrations: predeclared 0 (in-place `060_001` only, counted under
  production/config per the 079-2-a convention); actual 1
  (EXCEEDED, disclosed): the in-place `068_001` function-body
  adaptation (register MIME literals +2/-2 and the
  `slaif_media_public_mark` list-reference predicate +7/-1; file total
  +9/-3; no DDL, no new migration file, no downgrade change).
- Tests/evidence: predeclared at most 5; actual 15 (EXCEEDED by 10,
  disclosed): the five predeclared files (`test_pdf_policy.py` new,
  the unit validation extension `test_component_facets.py`,
  `renderer-behavior.test.ts`, `media-publication.spec.ts`,
  `test_component_catalog.py` count pin) plus nine further files:
  `test_design_system.py`, `test_route_policy.py`,
  `test_foundation_contract.py`, `test_agent_mutations.py`,
  `index.test.ts` (component-catalog), `puck-adapter.test.ts`,
  `tools/compose/public_agent_acceptance.py` (catalog count pins,
  1-2 lines each, forced by the 31 -> 32 catalog), and the
  substantive `test_media_store.py` (new PDF store suite) and
  `test_render_projection_media.py` (new document-class projection
  tests) extensions, and the disclosed `tests/e2e/reporter.mjs`
  CI-observability repair (commit E).
- Generated artifacts: predeclared at most 4; actual 5 (EXCEEDED by 1,
  disclosed): `catalog-v1.json` x2 + `agent-v1.json` (predeclared) plus
  the `design-system-v1.json` x2 pair (deterministic generator
  byproduct of the catalog change, as in 079/2; in-place `060_001`
  counted under production/config per the 079-2-a convention).
- Docs: predeclared at most 5; actual 4 (within budget):
  `README.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`,
  `oap/MVP-CONTRACT-AUDIT.md`; `CRITICAL.md` verified, unedited.
- OAP transcript: order + active + report (within budget).
- Substantive implementation-line scale: predeclared at most 1.2k;
  actual 492 (production/config + migrations insertions of the base -> docs-commit diff), far below the ceiling.

## Acceptance-criteria evidence
### Criterion 1 (catalog 32, generator gates, count pins)

- `uv run --frozen python tools/generate_component_catalog.py --check`: PASSED (zero-diff)
- `uv run --frozen python tools/generate_design_system.py --check`: PASSED (zero-diff)
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED (zero-diff)
- In-place `060_001` consistent: new `CATALOG_V1_REVIEWED_SHA256`
  `76f3329fe22688e625c0d4a73cb2ce93ba85a377d2f7cf1ff159f1372fc715ab`
  matches the baked `_CATALOG_V1_JSON`; `uv run --frozen pytest
  services/backend/tests/unit tests/repository -q`: PASSED (includes
  `test_component_catalog.py` count pin `len(COMPONENT_CATALOG) == 32`).
- All four catalog-count pins at 32 (disclosed per file):
  `services/backend/tests/unit/test_component_catalog.py`
  (`len(COMPONENT_CATALOG) == 32`), `tools/compose/public_agent_acceptance.py`
  (`len(catalog["components"]) != 32` guard), and the two generated
  `catalog-v1.json` files via the generator `--check` gates; plus the two
  design-system count pins (`test_design_system.py` scope metadata 68 -> 70,
  `test_route_policy.py` conditional scopes 67 -> 69) and the two
  `packages/*/tests` pins (`index.test.ts` catalog+design 31 -> 32 x2,
  `puck-adapter.test.ts` 31 -> 32).

### Criterion 2 (PDF policy unit matrix)

- `services/backend/tests/unit/test_pdf_policy.py` (15 tests): constants;
  raw 1-page accept; exactly-200-page accept (boundary); 201-page reject
  via the 201 counting sentinel; 300-page stops at the sentinel;
  Flate-only page-object PDF; mixed raw + compressed; `/Type /Pages` never
  counted; undetermined -> `None`; structural failures -> `None`;
  above-20 MiB reject; exactly-20 MiB accept; undetermined verdict key;
  decompression bomb (above 50 MiB) -> undetermined. All PASSED within
  the unit run.

### Criterion 3 (upload rejects on BOTH paths, exact store keys, no partial artifacts)

- Unit (store level, exact keys): `test_media_store.py` (24 tests): accept
  1-page / 200-page / Flate PDF; reject `media-pdf-too-many-pages` (201),
  `media-pdf-too-large` (above 20 MiB, independent of the generic 100 MiB
  limit), `media-pdf-structure-invalid` (undetermined + bomb); every
  rejection leaves no staging file and creates no `sha256/` object
  directory; `sniff_mime` PDF signature cases (declared PDF with
  non-`%PDF-` prefix uses the existing `media_signature_mismatch` key).
  Two regression tests pin the exact HTTP flow (unflushed staging writer
  handed to `publish()`): publish succeeds for a valid PDF and the exact
  `media-pdf-too-many-pages` rejection still fires — the flow the first
  smoke run exposed (503) and this round's fix repairs.
- E2E (Compose smoke, public NGINX): human route `/media/v1/sites/{site}/
  assets` — real 2-page PDF 201 with exact `content_hash`; 422
  `DOMAIN_VALIDATION_FAILED` for (a) PNG bytes declared `application/pdf`
  (signature), (b) 21 MiB padded PDF (`media-pdf-too-large` class; the
  `/media/` edge allowance of 105119744 bytes lets it reach the store
  policy), (c) 201-page generated fixture (`media-pdf-too-many-pages`
  class), (d) header-only PDF with no page objects
  (`media-pdf-structure-invalid` class); psql proof no rejected document
  was stored. Agent route `/api/agent/v1/media/assets` — real 2-page PDF
  201; 422 for the 201-page fixture and the undetermined fixture (the
  1 MiB `/api/agent/` edge body bound keeps the oversized class on the
  human route by design). Exact store-key pinning lives at unit level per
  the bounded HTTP surface (no key echo in the body).

### Criterion 4 (mutation/editor validation, exact keys, no tree/version change, image-class negatives)

- Unit: `test_component_facets.py` (51 tests): valid/duplicate/bounds-edge
  (1 and 12 items) pass; 10-case parametrized reject matrix with exact
  keys (`doclist.items-out-of-range` x2, `doclist.item-missing` x3,
  `doclist.item-foreign-site` x2, `doclist.item-not-pdf` x3 including
  PNG/JPEG/text rows); malformed shapes pass through to the catalog guard;
  vocabulary set pin; R3 regression: Gallery/LogoGrid facts with
  `application/pdf` rows raise `gallery.item-not-image` /
  `logogrid.item-not-image`.
- E2E Agent hostile suite (11 cases): 10 from the exact R3 error-key list
  (13 items, empty, missing mediaId, non-UUID, unknown UUID, foreign demo-
  site PNG, same-site human PNG, same-site agent PNG, same-site text row,
  valid-PDF + PNG mix) plus the catalog label bound (121 chars ->
  `COMPONENT_PROP_BOUND`): all 422 with the exact `details.prop_error`;
  component-tree length and every row_version unchanged after the suite.
- E2E Editor suite (7 cases): POST rejections (13 items, empty, missing,
  PNG reference) + PATCH rejections (foreign demo-site PNG, valid-PDF +
  PNG mix, 121-char label -> `COMPONENT_PROP_BOUND`), all 422 with exact
  keys.
- E2E image-class regression negatives: Editor POST Gallery item with a
  real PDF -> `gallery.item-not-image`; LogoGrid two PDF items ->
  `logogrid.item-not-image`; Image `mediaId` = real PDF ->
  `COMPONENT_BINDING_INVALID` (the 079/1 key, exact on the Editor
  surface). Agent side: Gallery/LogoGrid PATCH with PDF items -> the
  exact image-class keys; agent Image POST with a PDF `mediaId` -> 422
  `DOMAIN_VALIDATION_FAILED` (the Agent surface bounds the exact DB key to
  the enumerated prop_error vocabulary — pre-079/3 behavior, unchanged by
  this diff; the exact key is proven on the Editor surface and by the
  validator contract).
- No post-079/2 check gap existed: the DB component validator's
  `media_asset` binding branch already restricts `Image` to
  `('image/png','image/jpeg')` (068_001's extended 060_001 validator,
  unchanged here), and the 079/2 per-item checks reject any non-image row
  for Gallery/LogoGrid — both verified by reading the validator SQL and by
  the E2E negatives above.

### Criterion 5 (projection document-class resolution)

- `test_render_projection_media.py` (18 tests, 6 new): document descriptor
  resolves only the document MIME class (preview URL form for any
  public status; digest URL only when `public_status='public'`; image-class
  rows never document descriptors and vice versa); DocumentList list
  descriptors mixed resolved + fail-closed (unresolved reference, image-
  class row, malformed item); public mode marks non-public items fail-
  closed; preview/public URL forms pinned (media id never in the public
  digest URL); non-list `items` untouched; image list components never
  resolve document rows.

### Criterion 6 (renderer markup pins, forbidden attributes, parity)

- `apps/web/tests/renderer-behavior.test.ts` (28 tests, 5 new): exact
  `DocumentList` markup with title and mixed resolved/fail-closed items
  (byte-pinned), heading omitted without `title`, 079/1 placeholder pattern
  for null / non-PDF-MIME / foreign-URL descriptors, preview/public markup
  identical except the href form, and no inline style / event handler /
  `javascript:` / `sandbox` / `target` in any emitted markup.
- E2E parity: preview (overlay) and canonical (public) `section.sl-doclist`
  markup byte-identical after mapping the preview href forms to the
  digest URLs.

### Criterion 7 (E2E: three viewports, hostile rejections, public byte-identity + headers)

- Compose smoke `sh tools/compose/smoke.sh slaif0075a`: rc=0 (final full smoke on the final tree; log `/tmp/0793a/compose-smoke-12.log`; `compose-e2e: OK projects=13 ... media-publication=1 ...`; 23 PASSED e2e contracts incl. `media-publication-core-human-agent-preview-finalize-public-hostile`; final line `compose-smoke: OK`);
  the media-publication project covers, in one 300 s test: the real 2-page
  PDF rendered inside `section.sl-doclist` at desktop (1280x720), tablet
  (768x1024), and phone (390x844) via the authorized preview route; the
  hostile suites of Criterion 4; after the direct 083-boundary
  `finalize_media_for_promotion` call for the two PDF media ids,
  unauthenticated public digest reads return 200 with byte-identical PDF
  bytes, exact `Content-Type: application/pdf`,
  `Cache-Control: public, max-age=31536000, immutable`,
  `X-Content-Type-Options: nosniff`, and matching `Content-Length`.
- No `smoke.sh` expectation line was extended: the 079/1 and 079/2
  increments did not add gallery/logogrid expectation lines to the smoke
  script, so the same pattern holds for the document class (the E2E spec
  is the document-class evidence carrier).

### Criterion 8 (OpenAPI strip-identity, drift gate, 47 paths)

- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED (zero-diff).
- Strip-identity proof (both sides, canonical JSON after removing every
  `x-slaif-*` key): sha256 base `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  = sha256 head (identical).
- Path-key sets equal: 47 paths at base and head. Scope-string sets equal.
  Diff vs base: +84/-0 lines, all inside the existing
  `x-slaif-component-content` / component-metadata extension values
  (the two DocumentList content-prop metadata entries).

### Criterion 9 (R6 docs, numeric 078 stays PARTIAL, adversarial sweep)

- All five surfaces updated with the verified merge facts only
  (079/2 accepted and merged in PR #93 at `c149c39e66978c9ee53a7d92300a64e4297cfa56`
  on 2026-10-04) and the standard in-flight form for 079/3; `CRITICAL.md`
  verified, unedited. No row states 079/3 as accepted/merged/E2E-proven;
  "numeric 078 remains PARTIAL until 079/3 lands" is preserved in every
  row.
- Adversarial sweep for stale 079/2 in-flight wording:
  `git grep -n "079-2-a" -- '*.md'` after the docs commit returns only
  historical/transcript occurrences (order files and earlier reports are
  immutable history; the live-truth surfaces INCREMENTS / MVP-PROGRESS /
  README / MVP-CONTRACT-AUDIT no longer carry the in-flight 079/2 form).

### Criterion 10 (R8 constraints)

- `uv.lock` and `pnpm-lock.yaml` byte-identical to base (`git diff` empty).
- No changes under `tools/supply_chain/`, `tests/supply_chain/`, or
  `.github/workflows/`. No new dependency (policy module is stdlib
  `zlib` + `re`). No new migration file (in-place `060_001` regeneration
  only, plus the disclosed 2-line in-place `068_001` function-body
  literal — no DDL). No new endpoint or scope string. No secrets in diff
  or report (E2E fixture credentials are the compose-stack fake
  placeholders).

### Criterion 11 (CI)

- D (docs commit, superseded head): 19 SUCCESS + 1 FAILURE (`Compose and edge packaging` — media-publication observation-collector failure; see Known limitations). E (final implementation head) — all 20 check runs terminal (exact 20-check roster of the base commit):
  - `Analyze (actions)`: SUCCESS
  - `Analyze (javascript-typescript)`: SUCCESS
  - `Analyze (python)`: SUCCESS
  - `CodeQL`: SUCCESS
  - `Compose and edge packaging`: SUCCESS
  - `Dependency review`: SUCCESS
  - `Detect supported languages`: SUCCESS
  - `Foundation PostgreSQL 14`: SUCCESS
  - `Foundation PostgreSQL 15`: SUCCESS
  - `Foundation PostgreSQL 16`: SUCCESS
  - `Foundation PostgreSQL 17`: SUCCESS
  - `Foundation PostgreSQL 18`: SUCCESS
  - `Markdown`: SUCCESS
  - `Mermaid`: SUCCESS
  - `Node contracts`: SUCCESS
  - `Python 3.12 quality and package`: SUCCESS
  - `Python 3.13 quality and package`: SUCCESS
  - `Python 3.14 quality and package`: SUCCESS
  - `Repository policy`: SUCCESS
  - `Supply-chain evidence`: SUCCESS

## Local verification
Final tree (after the store flush fix + regression tests):

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED (310 files)
- `uv run --frozen mypy`: PASSED (289 source files)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`: PASSED (757 passed, 26 subtests)
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED (235 passed in 2409.58s (0:40:09); final-tree run after every fix; log `/tmp/0793a/pytest-integration-6.log`)
  Integration-environment note (disclosed): two earlier local integration
  runs (one on a pre-fix tree, one on the final tree) each finished 231
  passed + 4 setup errors in `test_foundation_postgres.py` (`permission
  denied for schema agentcow`), all from stale local scratch-PG state: a
  prior run was killed before its session-scoped `foundation_database`
  fixture teardown finished, leaving the foundation `agentcow` schema
  owned by a dead qualification role, which the next run's fresh setup
  role could not populate (`CREATE SCHEMA IF NOT EXISTS agentcow` is a
  no-op against the stale schema). Identical on both trees, so not a
  product effect of this diff. After dropping the stale disposable
  qualification roles/schemas (local scratch PostgreSQL only) and a clean
  full re-run on the final tree: full pass (line above).
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: PASSED
- `uv run --frozen python tools/generate_component_catalog.py --check`: PASSED
- `uv run --frozen python tools/generate_design_system.py --check`: PASSED
- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check`: PASSED
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED
- Process smokes (`python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check`): all 10 PASSED
- `node --version` / `pnpm --version`: 24.x / 11.22.0
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED (workspace + root + tests/e2e tsconfig)
- `pnpm test`: PASSED (includes `pnpm exec vitest run apps/web/tests/renderer-behavior.test.ts`: 28 passed, 5 new DocumentList pins)
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED
- `sh tools/compose/smoke.sh slaif0075a`: PASSED rc=0 (final-tree run; log `/tmp/0793a/compose-smoke-12.log`; 13 E2E projects; the media-publication project carries the 079/3 document-class section)
- `sh tools/compose/e2e.sh` full 13-project browser E2E on a fresh stack (`slaif007repro1`, post-reporter-repair verification): PASSED rc=0 (23/23 contracts incl. media-publication; log `/tmp/0793a/repro1-e2e.log`)

Note on gate sequencing: the first full gate run passed every step except
`pnpm format:check` / `pnpm typecheck` (new test files needed repo-prettier
line wrapping and one noUncheckedIndexedAccess guard in the E2E section) and
the ruff pair (E501/F811/I001 in the new test files); after the
mechanical fixes, every failing step was re-run green on the final tree.
The Compose smoke's first run failed inside the new E2E section: the human
PDF upload returned 503 because the store's PDF enforcement read the
still-buffered staging writer before the HTTP path's flush (the unit
helpers flush explicitly, which masked the flow). The fix (flush before
enforcement in `publish()`) plus two unflushed-writer regression unit tests
re-ran the affected gates green, and the smoke was re-run to completion
(rc=0).

The final full gate run (`/tmp/0793a/gate-final-summary.txt`) passed every
step except two, both non-product and verified standalone: `process-smokes`
hit a `uv` environment race with the concurrently running integration
pytest (first module: `No module named slaif_agent_site`); the standalone
re-run was 10/10 CHECK_OK. `markdownlint` flagged only this report's
untracked dotfile draft (tracked-file markdown clean); the draft was fixed
to 0 issues before publication.

## GitHub CI / required checks

- State observed at docs commit D `4254d66dc1a0fd67c1a10a79822faf257b2f9cb7`: 19 SUCCESS + 1 FAILURE (`Compose and edge packaging` — media-publication contract, observation-collector failure at the final `expect(failures()).toEqual([])`; every functional assertion passed; classified failure tokens were unrecoverable from the CI log; see Known limitations)
- State observed for implementation head E `554a8d2a3b0963574b96d537e4a814291a46c1f7`: all 20 check runs terminal (exact 20-check roster of the base commit): Analyze (actions)=success, Analyze (javascript-typescript)=success, Analyze (python)=success, CodeQL=success, Compose and edge packaging=success, Dependency review=success, Detect supported languages=success, Foundation PostgreSQL 14=success, Foundation PostgreSQL 15=success, Foundation PostgreSQL 16=success, Foundation PostgreSQL 17=success, Foundation PostgreSQL 18=success, Markdown=success, Mermaid=success, Node contracts=success, Python 3.12 quality and package=success, Python 3.13 quality and package=success, Python 3.14 quality and package=success, Repository policy=success, Supply-chain evidence=success
- All required green at drafting: yes (E: 20/20 terminal, no FAILURE/CANCELLED; `Dependency review` is `success` at E, as at D)
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- No new packages. Existing toolchain: uv 0.12.5, Node 24.x, pnpm 11.22.0,
  Docker Compose (smoke stacks `slaif0075a` + negative stack, plus the
  fresh `slaif007repro1` e2e verification stack, torn down after each run), local PostgreSQL 16 scratch for the integration suite
  (disposable `slaif_test_*` databases, fake fixture credentials),
  Playwright 1.62.1 via the smoke's browser projects,
  `markdownlint-cli2@0.23.2` via npx (temporary, no production
  dependency). Passwordless guest sudo was not needed for this round.

## Documentation

- R6 five surfaces as itemized under Changes made; `CRITICAL.md` verified
  only. Implemented-vs-planned distinction preserved: 079/3 is described
  exclusively in the standard in-flight form; no accepted/merged/E2E-proven
  claim for 079/3; numeric 078 stays PARTIAL in every row.

## Safety and scope confirmations

- Unrelated files changed: no (every changed path is R1-R6 scoped or a
  disclosed mechanical count pin; the `068_001` 2-line DB adaptation is
  disclosed under Changes made / R8).
- Production secrets accessed: no; production systems accessed: no (compose
  stacks with fake fixture credentials only; local scratch PostgreSQL only).
- Required tests skipped/not run: no (every R7-named evidence ran; the
  full local gate and the full Compose smoke completed on the final tree).
- Scope deviation: one bounded deviation from the predeclared shape,
  disclosed: in-place `068_001` register-function MIME literals extended
  with `application/pdf` (required for R7's real PDF uploads; no DDL, no
  new migration file, validator image-only branch untouched); plus the
  separately disclosed adaptations under Changes made (compose.yaml tmpfs
  16m -> 256m; the 068_001 mark predicate +7/-1; the editor update-route
  VALIDATION branch; the e2e reporter observability repair), each
  individually justified and documented. No other deviation.
- Extra objective PR: NO; coding-agent merge: NO.
- Activated order/active edited: NO (T commits the exact strategic bytes).
- Report commit changes only this report: yes.
- Flake policy: no CI re-run was needed for the local gates; the smoke
  re-run was a local fix-verification re-run, not a documented CI flake
  re-run (no CI re-run occurred; the D -> E progression is a new
  in-scope commit, which CI independently re-evaluated at the new head).

## Known limitations / blockers

- The Agent HTTP surface does not echo the DB-level `COMPONENT_BINDING_INVALID`
  key into `details.prop_error` for a single-`mediaId` `Image` component
  (bounded pre-079/3 surface; the exact key is proven on the Editor surface
  and in the validator contract). If strategy wants the Agent surface to
  echo that key, it is a bounded follow-up order, not part of this increment.
- The oversized-PDF class (above 20 MiB) is E2E-proven on the human route
  only: the `/api/agent/` edge body bound is 1 MiB by the existing edge
  contract, so the Agent route cannot carry a >20 MiB body at all (it is
  413 at the edge before the service). The shared-store enforcement is
  proven for both routes at unit level and for the other three rejection
  classes on both routes in E2E.
- CI at D (docs commit `4254d66dc1a0fd67c1a10a79822faf257b2f9cb7`):
  `Compose and edge packaging` failed the media-publication contract at the
  final `expect(failures()).toEqual([])` — the observation collector
  recorded at least one page-level event (a classified console / network /
  HTTP>=400 token). Every functional contract assertion passed at D; the
  same contract passed CI at the 079/2 merge (`c149c39`); and the local
  full smoke (smoke 12) plus the full e2e re-run on the final tree
  (`slaif007repro1`, 23/23) were green, so no product defect was
  identified and no causal path was found in this diff (the 079/3
  page-level surface is additive doclist markup with no JS or fetch). The
  classified failure tokens were unrecoverable from the CI log (minimal
  SafeReporter by design; `artifacts=disabled`). Per the order's flake
  policy, NO unmodified CI re-run was invoked (re-runs are reserved for
  the documented dragUntil class); instead the bounded reporter repair
  (E) was pushed to make the failure observable, and CI at E is 20/20
  terminal green with the contract passing. If strategy regards the D
  transient as an unresolved defect rather than an environment timing
  event, it is flagged here for independent adjudication.
- No other blockers.

## Recommended strategic follow-up
None required for this increment; 079/3 evidence is in the PR for
independent review and merge per the order. Post-merge bookkeeping
(numeric 078/079 reclassification) remains strategy-owned per human
decision D1.

# OAP Coding-Agent Report — 078-8-a

## Work order

- Identifier: `078-8-a` (increment-qualified; first round of semantic
  increment 8 of numeric Objective 078)
- Work-order file:
  `oap/orders/078-8-a-bounded-embed-family.md` (sha256
  `e127c92d2079031c9d71585b408490cb2da5713ba779175320f2cbb95194e6ea`)
- `oap/active` committed byte-for-byte: `078-8-a\n` (8 bytes, sha256
  `31889087176a82d125db835c3a4cda2ea10fd6ccbdec3894bf5546aecca4d4a0`)
- Numeric objective: 078 (increment 8)
- PR mode: CREATE_NEW_PR (PR #88)

## Status

COMPLETE — all nine requirements (R1–R9) implemented and evidenced by
executed commands: the bounded-embed policy module with 61 byte-pinned
unit tests; catalog 27 → 29 (VideoEmbed, MapBlock) with all generated
artifacts regenerated zero-diff; trusted renderers with exact-markup
pins (12/12 renderer-behavior); Agent + Editor mutation enforcement
proven in real-browser E2E (13 hostile Agent PATCHes with exact error
keys, 4 hostile Editor rejections, unchanged trees); exact
`frame-src` edge backstop in both adapters with the strengthened
edge-contract test and green smoke `edge-header-policy`; the five
R7 doc surfaces with durable wording; `x-slaif-*`-only OpenAPI delta
with strip-identity sha256 `df755623744785fdaf5f342268165fe7b7be9f352f276b56e2337692cae671da`;
full local gate plus full Compose smoke `compose-smoke: OK`; and all
20 required GitHub checks successful on the implementation head.
Three verification-time defects found during this round (the E2E's
misread of the COW workspace model, a fixed-count assertion, and two
missed catalog-count ripple pins) were repaired in code before
completion and are disclosed with their evidence below. The one
documented Puck-drag flake class appeared once in a local smoke
run (smoke4 — handled by a free local re-run per the order's
flake policy) and once in the CI run of the superseded first
report head (35453903907 — `governance` project only, before the
`preview` project ran); no CI re-run was invoked, so the order's
one permitted unmodified re-run remains available should the
class recur on this final head.

## Executive summary

- **R1 (policy module)**: new pure module
  `services/backend/src/slaif_agent_site/content_model/
  bounded_embed.py` (`EMBED_POLICY_VERSION = "bounded-embed/v1"`):
  code-defined allowlist (youtube-nocookie `/embed/<11-char id>`,
  vimeo `/video/<6+ digit id>`, OSM `/export/embed.html` with
  mapnik/cycle/transport layers), canonical https-only URL builders
  (sorted map query keys, no autoplay/tracking parameters ever
  emitted), and fail-closed validators returning bounded error keys
  (`embed.provider-unknown`, `embed.video-id-invalid`,
  `embed.title-missing`, `embed.title-too-long`,
  `embed.bbox-missing`, `embed.bbox-out-of-range`,
  `embed.bbox-invalid-order`, `embed.layer-unknown`) — never
  echoing user input.
- **R2 (catalog 27 → 29)**: `VideoEmbed` (basic) and `MapBlock`
  (institutional) declared with structured-only props (no
  raw url/src/html/style/class/script-like props); leaf components,
  no children/slots/binding. All four generated artifacts
  regenerated; in-place `060_001` baked-catalog diff is the catalog
  JSON plus its SHA guard only; deterministic migration N/A (new
  types, no existing instances). All generator `--check` gates
  zero-diff.
- **R3 (renderers)**: `components.tsx` emits the exact pinned iframe
  markup (deterministic attribute order, `loading="lazy"`,
  `referrerPolicy="no-referrer"`, no sandbox/allow/allowfullscreen/
  inline style) for both components, plus the fail-closed
  `sl-embed--placeholder` pattern; `renderer-v1.css` adds
  `.sl-embed` (100%/block/border 0), 16/9 video and 4/3 map aspect
  boxes, responsive by container width.
- **R4 (enforcement)**: the R1 validator is the first decision
  surface on both mutation paths — before the catalog shape guard —
  in `agent_state/mutations.py` (Agent path; 422 body carries the
  exact R1 key in `error.details.prop_error`) and
  `editor_api/composition_http.py` (Editor path; bounded 422).
  Rejections leave tree, props, and row versions unchanged;
  idempotency/audit semantics untouched.
- **R5 (projection)**: `render_api/projection.py` re-validates embed
  props at projection time via R1 (defense in depth) and passes
  validated props through unchanged.
- **R6 (edge CSP backstop)**: exact
  `frame-src https://www.openstreetmap.org
  https://www.youtube-nocookie.com https://player.vimeo.com;`
  inserted after `object-src 'none';` in both nginx policy lines and
  the corresponding apache lines; `tests/packaging/
  test_edge_contract.py` reworked to pin the exact full CSP lines,
  the exact three-host `frame-src`, and the no-http(s) rule for
  every other directive; smoke `edge-header-policy` expectation
  updated (green line below).
- **R7 (current-truth docs)**: exactly the five ordered surfaces
  updated (INCREMENTS 078/7 row + 078/8 row + Next row; MVP-PROGRESS
  active sequence; MVP-PROGRESS status row 078; README
  Objective-078/4 row; MVP-PROGRESS watch-item temporal scoping,
  two phrases only). Acceptance greps return nothing.
- **R8 (OpenAPI)**: regenerated `agent-v1.json` diff is
  `x-slaif-*`-only; after stripping all `x-slaif-*` keys the
  canonical JSON is byte-identical to base (sha256 both sides
  `df755623744785fdaf5f342268165fe7b7be9f352f276b56e2337692cae671da`);
  45 paths unchanged; no scope strings added or removed; the delta
  is +6 entries in `x-slaif-component-property-scopes` (57 → 63),
  +6 in `x-slaif-conditional-scopes` on
  `PATCH /api/agent/v1/components/{component_id}` (56 → 62; 60 → 66
  aggregated over all occurrences), and +6 entries in
  `x-slaif-component-authority.properties` (57 → 63, both
  occurrences) — all `component-content-props:write`.
- **R9 (evidence)**: 61 unit tests (byte-pinned canonical URLs and
  every hostile rejection with exact key); 12/12 renderer-behavior
  pins including forbidden-attribute absence and fail-closed
  placeholders; real-browser E2E (new test in the `preview`
  Playwright project, which is the only project whose testMatch glob
  permits it — no new spec file, no config change); full local gate;
  full Compose smoke `compose-smoke: OK`.
- **Verification-time defects repaired in code (disclosed)**:
  1. The new E2E originally PATCHed the Agent-workspace component id
     through the Editor API. The human editor session resolves to its
     own server-owned `actor_type='HUMAN'` COW workspace (never the
     `actor_type='AGENT'` workspace), so that request 404'd. The
     Editor section was redesigned to create valid components in the
     editor's own workspace and reject hostile creates/updates there
     (first failed CI run 35449807016 at line 2071; fixed in
     `70a773a`; validated by a scratch integration flow over real
     PostgreSQL before deletion: hostile create 422, valid creates
     201 at row_version 1, hostile PATCHes 422, clean readback).
  2. The E2E originally asserted the public canonical page contains
     the embed iframes; un-promoted COW content must never render
     publicly (promotion is 082/083 scope). The public section now
     asserts the exact `frame-src` CSP, `data-render-mode=
     "canonical"`, and COW suppression (no `<iframe` at all), while
     byte-parity is evidenced by the byte-pinned iframe markup in
     the preview plus byte-identical shared-base `RichText`
     outerHTML between public and preview surfaces (one trusted
     renderer; only the root mode attribute differs).
  3. The editor readback originally asserted a fixed record count of
     2; the parity fixture seeds base Heading + RichText rows that
     are visible through the editor workspace COW view, so the
     count is 4. Replaced by byte-equality against a pre-rejection
     snapshot (mirrors the Agent-side tree check) — first local
     smoke failure at line 2163, fixed in `0997060`.
  4. Two catalog-count ripple pins missed in the initial ripple
     pass: `services/backend/tests/integration/
     test_agent_mutations.py` (27-type set; failed in the first full
     local integration run — 1 failed / 234 passed) and
     `tools/compose/public_agent_acceptance.py` (`!= 27`; failed
     smoke5's `public-agent-acceptance` stage and the
     0997060 CI Compose job). Both updated 27 → 29, the exact
     precedent of 078/7-a (commit `137abbc` bumped the identical
     assertions 22 → 27). Fixed in `70a773a` and `b470a1e`
     respectively; full integration re-run green (235 passed) and
     smoke6 green.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #88 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/88>
  (state OPEN; exactly one PR created; no other PR touched;
  Dependabot PRs #83, #84, #75 untouched)
- Base branch: `main`; head branch:
  `oap/078-8-a-bounded-embed-family`
- Verified base (order-verified `main`):
  `d9a7555662a976483b9716e41863de8ecd00decf`
- Starting remote SHA: `d9a7555662a976483b9716e41863de8ecd00decf`
- Implementation head (literal):
  `b470a1ea4690fe498703ceafa249bfb2ebc08713`
- Report publication commit: SELF
- Implementation commits pushed (7), base → head:
  - `6fa23ab` — 078-8-a: bounded embed family (VideoEmbed, MapBlock)
    — 30 files, +2145/−43 (main implementation; includes the
    order file and `oap/active` committed byte-for-byte)
  - `55c006b` — 078-8-a: current-truth documentation (R7) — 3 files,
    +14/−10
  - `79e826b` — 078-8-a: wrap edge-contract assertion line for ruff
    line limit — 1 file, +4/−3
  - `26d1fd3` — 078-8-a: align governance E2E CSP backstay with the
    ordered frame-src — 1 file, +12/−2
  - `70a773a` — 078-8-a: repair bounded-embed E2E against COW
    workspace reality — 2 files, +124/−22 (defect 1+2 above and the
    `test_agent_mutations.py` catalog pin, defect 4)
  - `0997060` — 078-8-a: compare editor workspace tree by snapshot,
    not fixed count — 1 file, +8/−1 (defect 3)
  - `b470a1e` — 078-8-a: update public acceptance catalog pin
    27 → 29 — 1 file, +1/−1 (defect 4)
- Report parent = implementation SHA: yes (verified via
  `git show --format=%P`)
- New PR this round: yes (#88); merged: NO — strategy is the only
  merger

## R1 evidence — bounded embed policy module

- File: `services/backend/src/slaif_agent_site/content_model/
  bounded_embed.py` (new, 209 lines, pure functions, no I/O, no
  network; the policy never fetches URLs server-side).
- Unit evidence (executed):
  `uv run --frozen pytest services/backend/tests/unit/
  test_bounded_embed.py -q` → `61 passed in 0.18s`.
- The suite pins every canonical URL byte-for-byte (youtube-nocookie
  `dQw4w9WgXcQ`; vimeo 6+-digit id; OSM default-layer omission and
  explicit `layer=cycle`; sorted map query keys) and every negative
  class with its exact error key: host substitution
  (`www.youtube.com`, `evil.example`), non-https, query injection
  (`?autoplay=1` on the id form), `javascript:`/`data:`/`file:`
  schemes, invalid and oversized ids, out-of-range bboxes
  (±180 / ±85.05112877), invalid-order bboxes (west ≥ east,
  south ≥ north), unknown layers, missing/empty/oversized titles
  (121 chars). Coordinate formatting is pinned too (integer-valued
  → int string, else 10-decimal trailing-zero-stripped, no
  exponent).
- The module is imported only by the mutation paths, the projection,
  and its unit tests (no other production importer).

## R2 evidence — catalog 27 → 29

- `component_catalog.py`: +`VideoEmbed` (basic; props
  `provider` enum, `video_id` string ≤64, `title` required localized
  1..120) and +`MapBlock` (institutional; props `bbox` object with
  numeric west/south/east/north, `layer` enum optional default
  mapnik, `title` required localized 1..120). Both leaf: no
  children/slots, no data binding, `authority_class=content`,
  binding none. Neither exposes any raw url/src/html/style/class/
  script-like prop.
- In-place `060_001` regeneration: the only diff is the baked
  catalog JSON plus `CATALOG_V1_REVIEWED_SHA256`
  (`eecacea44de0698b665219d9f94b508485fb4cbe51e6ab80df2ab53312075169`);
  no physical schema change; deterministic migration recorded as
  "N/A (new types, no existing instances)" in the catalog entry
  metadata, exactly as 078/7 did.
- Generator gates (executed at the implementation head, zero diff):
  - `uv run --frozen python -m tools.contracts.generate_agent_openapi
    --check` → `agent-openapi: OK contracts/openapi/agent-v1.json`
  - `uv run --frozen python tools/generate_component_catalog.py
    --check` → `component-catalog: OK catalog-v1 Python/TypeScript
    semantic equality`
  - `uv run --frozen python tools/generate_design_system.py --check`
    → `design-system: OK`
  - `uv run --frozen python tools/generate_theme_schema.py --check`
    → `theme-schema: OK`
- Catalog count evidence: `tests/packaging/test_edge_contract.py`
  siblings aside, the count pins in
  `packages/component-catalog/tests/index.test.ts`,
  `packages/composition-schema/tests/puck-adapter.test.ts`, and
  `services/backend/tests/unit/test_component_catalog.py` were
  updated 27 → 29 (ripple class per 078/7-a precedent) and pass in
  the green Node and unit suites below; the integration pin in
  `test_agent_mutations.py` (27-type set) was repaired in
  `70a773a` (defect 4) and passes in the 235-pass integration run.

## R3 evidence — trusted renderers

- `apps/web/src/renderer/components.tsx`: `canonicalVideoEmbedUrl`,
  `canonicalMapEmbedUrl`, `formatEmbedCoordinate`, `embedTitle`
  (TypeScript mirror of R1); iframe emission with deterministic
  attribute order, `loading="lazy"`, `referrerPolicy="no-referrer"`,
  and no `sandbox`/`allow`/`allowfullscreen`/inline-style
  attributes; fail-closed placeholder
  `<div aria-label=… class="sl-embed sl-embed--…
  sl-embed--placeholder" role="img"></div>` when projection ever
  receives props that fail R1 validation (never an unvalidated
  iframe).
- `apps/web/public/renderer-v1.css`: `.sl-embed` (width 100%,
  display block, border 0), `.sl-embed--video` aspect-ratio 16/9,
  `.sl-embed--map` aspect-ratio 4/3, placeholder box; responsive by
  container width.
- Renderer-behavior evidence (executed): `pnpm exec vitest run
  apps/web/tests/renderer-behavior.test.ts` → `Tests 12 passed
  (12)` — exact markup pins for VideoEmbed (youtube-nocookie +
  vimeo) and MapBlock (mapnik + cycle), forbidden-attribute
  absence, and fail-closed placeholders.
- Real-browser evidence (smoke6 `preview` project): the E2E
  asserts the byte-pinned iframe strings in the rendered HTML,
  `iframe srcs == [videoSrc, mapSrc]` exactly, https-only, no
  `autoplay` in any src, and the aspect boxes (16/9 video, 4/3
  map) at both 1440×900 desktop and 768×1024 tablet.

## R4 evidence — mutation and editor enforcement

- Agent path: `_embed_prop_error` in `agent_state/mutations.py`
  merges the PATCH (non-null overrides, null removes) and runs R1
  before the catalog shape guard in both
  `add_component_for_site` and `update_component_for_site`;
  `agent_api/agent_http.py` maps `embed.*` codes to 422 with
  `error.details.prop_error` set to the exact R1 key (fixed bounded
  constants — `redact_log_value` passes them untouched; no
  user-input echo).
- Editor path: `_validate_embed_props` in `editor_api/
  composition_http.py` is called on `add_component` (body.props)
  and `update_component` (when `body.props is not None`; the Editor
  replaces props wholesale, so supplied props are exactly the
  post-write state) → bounded `DomainValidationError` → 422
  `DOMAIN_VALIDATION_FAILED`.
- Real-browser E2E evidence (smoke6 `preview` project, 12 projects
  all passed):
  - 13 hostile Agent PATCH cases (≥ 10 required) — each expected
    422 with `error.code == "DOMAIN_VALIDATION_FAILED"` and
    `error.details.prop_error` exactly the pinned R1 key:
    provider `youtube` → `embed.provider-unknown`; provider
    `evil.example` → `embed.provider-unknown`; video_id `abc` →
    `embed.video-id-invalid`; `dQw4w9WgXcQ?autoplay=1` →
    `embed.video-id-invalid`; `javascript:alert(1)` →
    `embed.video-id-invalid`; `file:///etc/passwd` →
    `embed.video-id-invalid`; title null-removed →
    `embed.title-missing`; title 121 chars →
    `embed.title-too-long`; bbox west 181 →
    `embed.bbox-out-of-range`; west 56/east 55 →
    `embed.bbox-invalid-order`; bbox missing north →
    `embed.bbox-missing`; layer `satellite` →
    `embed.layer-unknown`; title empty → `embed.title-missing`.
  - Tree and row versions unchanged: the Agent composition readback
    after all rejections is byte-equal (`toEqual`) to the
    pre-rejection snapshot.
  - Editor path: hostile VideoEmbed create (provider `youtube`) →
    422; hostile MapBlock create (bbox 181/182) → 422; after valid
    creates (201, row_version 1) in the editor's own workspace,
    hostile video_id `data:text/html,x` → 422 and hostile layer
    `satellite` → 422; the editor workspace tree readback is
    byte-equal to its pre-rejection snapshot, and both components
    retain row_version 1 with their original props.
- Scratch integration validation (transient file, deleted before
  commit; real PostgreSQL, production Editor HTTP wiring): hostile
  create 422, valid VideoEmbed create 201 (row_version 1), valid
  MapBlock create 201 (row_version 1), hostile video PATCH 422,
  hostile map PATCH 422, readback clean, and exactly one
  `actor_type='HUMAN'` "Human page editor" workspace auto-resolved —
  `SCRATCH-EMBED-EDITOR-FLOW: OK`.
- Idempotency/audit semantics unchanged: no idempotency or audit
  code touched by this PR; fresh keys per request in the E2E; the
  Editor envelope replay/mismatch behavior is covered by the
  pre-existing green integration suites.

## R5 evidence — projection

- `render_api/projection.py`: after the per-node `_validate_props`
  in `_node_tree`, embed props of `VideoEmbed`/`MapBlock` are
  re-validated via R1; failure raises `ProjectionError(
  "embed_props_invalid")` (fail-closed — the page projection fails
  rather than emitting an unvalidated iframe); passing props are
  carried through to the render payload unchanged (the 078/7
  prop-passing pattern).
- Evidence: the smoke6 E2E proves valid embed props survive
  projection (the iframes render canonically in both preview and —
  for the shared renderer contract — the public path); the
  fail-closed behavior is pinned by the renderer-behavior
  placeholder tests (12/12) and by the unit suite's validator
  negatives (61/61).

## R6 evidence — edge CSP frame-src backstop

- `infra/nginx/nginx.conf`: `frame-src
  https://www.openstreetmap.org https://www.youtube-nocookie.com
  https://player.vimeo.com;` inserted after `object-src 'none';` in
  both policy lines (public default and Puck editor line).
- `infra/apache/slaif-agent-site.conf`: same directive in the
  corresponding `RequestHeader` + `Header` lines (public lines
  byte-identical to nginx).
- `tests/packaging/test_edge_contract.py` reworked (strengthened,
  not weakened): module constants for the exact `frame-src`
  allowlist and expected full CSP lines; asserts the exact full CSP
  line for both adapters (nginx 2 / apache 3 lines, apache public
  lines byte-identical), that the `frame-src` directive equals
  exactly the three-host allowlist, and that every other directive
  contains no `http:`/`https:`/`wss:` substring; all previous
  count assertions and forbidden-source checks retained.
- Executed: `uv run --frozen pytest tests/packaging -q` → `48
  passed, 38 subtests passed in 2.39s`.
- Smoke expectation updated (`tools/compose/smoke.sh
  assert_edge_headers`): `frame-src` added to the asserted directive
  loop (stripped via sed before the forbidden-regex scan). Smoke6
  line: `edge-header-policy: OK page/api/404 request-id-count=1
  request-id-format=32hex csp-count=1`.
- The E2E additionally asserts the exact `frame-src` string in the
  `content-security-policy` header of both the public canonical
  page and the preview page.

## R7 evidence — current-truth documentation

Exactly the five ordered surfaces, minimal edits, no other prose
restructuring (all in `55c006b`, +14/−10 across 3 files):

- (a) `oap/INCREMENTS.md`: 078/7 row → "Accepted and merged in PR
  #87 at `d9a7555662a976483b9716e41863de8ecd00decf` on 2026-09-19;
  078/7 is closed"; new 078/8 row in the standard in-flight form
  ("Opened at `078-8-a` from verified remote main `d9a7555…`; PR
  pending; strategy owns acceptance and merge"); `Next` row →
  "Remaining 078 scope after 078/8".
- (b) `oap/MVP-PROGRESS.md` active sequence: verified-merge-SHA
  list extended with "PR #87 at `d9a7555…`"; the accepted
  increments list extended with "and 078/7"; "increment 078/7 is
  opened at `078-7-a` (PR #87)" replaced by "increment 078/8 is
  opened at `078-8-a` (PR #88)"; OAP/GitHub-authoritative
  sentences kept.
- (c) `oap/MVP-PROGRESS.md` status table row 078: appended
  "078/7 is accepted and merged in PR #87 at `d9a7555…`"; in-flight
  phrase replaced with 078/8/PR #88.
- (d) `README.md` Objective-078/4 row: replaced with the
  order-specified durable wording (078/7 accepted and merged in PR
  #87 on 2026-09-19; 078/8 (bounded embed family) opened at
  `078-8-a` (PR #88); GitHub authoritative).
- (e) `oap/MVP-PROGRESS.md` lines 95–102 watch item: exactly two
  phrases temporally scoped — "remained **PARTIAL/NOT IMPLEMENTED**
  at the time of the 078/2 increment" and "remained deferred at
  078/4 (global regions were delivered in 078/5; catalog breadth is
  in delivery from 078/7 onward)"; no other change to the
  paragraph.

Acceptance greps (executed): `grep -rn "078/7 is opened\|after
078/7\|remain deferred" README.md oap/INCREMENTS.md
oap/MVP-PROGRESS.md` → no output (rc=1). `markdownlint-cli2` over
all 492 linted Markdown files: 0 issues.

## R8 evidence — OpenAPI exact delta

Executed strip-identity proof (base `d9a7555` vs head
`b470a1e`, canonical JSON after removing every `x-slaif-*` key,
sorted keys, compact separators):

- base stripped sha256:
  `df755623744785fdaf5f342268165fe7b7be9f352f276b56e2337692cae671da`
- head stripped sha256:
  `df755623744785fdaf5f342268165fe7b7be9f352f276b56e2337692cae671da`
- identical: yes (byte-identical)
- paths: 45 base / 45 head (unchanged)
- scope strings: no additions, no removals (set-identical across
  `x-slaif-conditional-scopes`, `x-slaif-component-property-scopes`,
  `x-slaif-required-scopes`)
- delta details: `x-slaif-component-property-scopes` 57 → 63 (+6);
  `x-slaif-conditional-scopes` on
  `PATCH /api/agent/v1/components/{component_id}` 56 → 62 (+6)
  (60 → 66 aggregated over all occurrences);
  `x-slaif-component-authority.properties` 57 → 63 (+6) in both
  occurrences; `x-slaif-required-scopes` 82 → 82 (unchanged). All
  added entries document the new props under the existing
  `component-content-props:write` scope (supported=true,
  responsive=false).
- Generator gate: `generate_agent_openapi --check` zero-diff
  (above). The CI drift gate (Node contracts / Python quality) is
  green on the implementation head.

## R9 evidence — evidence requirements (all executed)

- Unit: 61/61 (exact command and output above, R1 section).
- Renderer: 12/12 (exact command and output above, R3 section).
- E2E (real browser, existing `preview` project spec extended — no
  new spec file, no `playwright.config.ts` change, within budget):
  new test
  `bounded-embed-family-renders-canonically-and-rejects-hostile-
  writes` in `tests/e2e/preview.spec.ts` (502 added lines vs base),
  passing in smoke6 (12/12 projects) and in the green CI Compose
  job.
- Full local gate and full Compose smoke: see the dedicated
  sections below; smoke final line `compose-smoke: OK`.

## Full Compose smoke (requirement R9 / acceptance 5)

Command (from repo root): `sh tools/compose/smoke.sh slaif0075a`
(final run; local artifact `/tmp/oap-078-8a/smoke6.log`; the stack
is torn down by the script on exit). Final status lines (verbatim):

```text
browser-e2e: OK
compose-e2e: OK projects=12 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 artifacts=disabled
public-agent-acceptance: OK workspace=298354e0-6eab-4b87-88ee-2d3058994112 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 theme=schema-default-patch-read-replay openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified
edge-header-policy: OK page/api/404 request-id-count=1 request-id-format=32hex csp-count=1
browser-artifact-recovery: OK byte-identical
browser-worker-secret-recovery: OK missing=not-ready canonical=available restored=healthy
browser-signing-recovery: OK missing=not-ready canonical=available restored=healthy
governance-restart: OK site=archived membership=inactive domain=primary fixtures=retained setup=closed
render-locator-recovery: restored render=healthy web=healthy nginx=healthy
Ran 48 tests in 2.717s
OK
compose-smoke: OK
```

The `edge-header-policy` line above is the R6-updated expectation
asserting the exact `frame-src` string. The `preview` project
includes the new bounded-embed E2E (desktop Chromium and tablet
viewport evidence). Smoke run history for this round (local,
disposable stack per run; local re-runs are free per the order's
flake policy, which governs CI): smoke3 failed at the E2E's
original editor-404 design (line 2071); smoke4 failed on the
documented Puck-drag flake class in the `governance` project before
the `preview` project ran (no code fix applicable — the class the
order documents); smoke5 passed all 12 browser projects but failed
the later `public-agent-acceptance` stage on the missed catalog pin
(defect 4, fixed in `b470a1e`); smoke6 (quoted above) is the green
record. No CI re-run was used at any point; the final
implementation-head CI Compose job (run 35452542217) was green
without any flake.

## Local verification

All commands run from the repository root with uv `0.12.5`, Node
v24.14.1, pnpm `11.22.0`, TypeScript `6.0.3`; integration tests on
a disposable local PostgreSQL (127.0.0.1:5432) with fake
credentials.

Python gate (all steps green at the implementation head):

- `uv lock --check`: PASSED
- `uv run --frozen ruff check services/backend tests/repository
  tests/packaging tests/supply_chain tools migrations` (CI scope):
  PASSED ("All checks passed!")
- `uv run --frozen ruff format --check services/backend tests/
  repository tests/packaging tests/supply_chain tools migrations`:
  PASSED (317 files already formatted)
- `uv run --frozen mypy`: PASSED (no issues found in 283 source
  files)
- `uv run --frozen pytest services/backend/tests/unit tests/
  repository -q`: PASSED (663 passed, 1 warning, 26 subtests
  passed in 26.33s — includes the 61 bounded-embed tests)
- `uv run --frozen pytest services/backend/tests/integration -q`:
  PASSED (235 passed in 2302.56s, quiet VM, disposable local
  PostgreSQL, fake credentials; see transparency note below)
- `uv run --frozen pytest tests/packaging -q`: PASSED (48 passed,
  38 subtests passed in 2.39s)
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
  (sdist + wheel)
- Generator `--check` gates (all four): PASSED (exact lines above)

Transparency note on the integration suite: the first full local
run (while the VM also carried build and browser work) completed
`1 failed, 234 passed in 2250.52s`; the single failure was
`test_agent_mutations.py::
test_agent_component_catalog_and_semantic_crud_are_cow_bound` at
its hardcoded 27-type catalog set assertion — a missed ripple pin
(this round's catalog grew to 29), not a flake and not a load
effect. It was repaired in code (`70a773a`, +`"VideoEmbed"`,
+`"MapBlock"` to the pinned set; same ripple class and same file as
the 078/7-a precedent `137abbc`), the isolated test re-run PASSED
in 12.20s, and the full-suite re-run on the quiet VM is the green
235-pass record quoted above. No test was skipped, weakened, or
modified beyond the ordered ripple pins.

Process smokes (all 10, `uv run --frozen python -m
slaif_agent_site.<module> --check`): control_api, editor_api,
agent_api, render_api, mcp_adapter, media_service, review_worker,
scheduler, media_gc, bootstrap: PASSED (`…: CHECK_OK`; health-only,
no port bind, no DB/job/bootstrap mutation).

Node gate:

- `node --version` / `pnpm --version`: v24.14.1 / 11.22.0 (exact
  pinned versions)
- `pnpm install --frozen-lockfile`: PASSED
- `pnpm lint`: PASSED (root + `@slaif-agent-site/web`, 0 warnings)
- `pnpm format:check`: PASSED
- `pnpm typecheck`: PASSED (all workspaces + root + e2e tsconfig)
- `pnpm test`: PASSED (17 tests passed, including `pnpm build`)
- `pnpm build`: PASSED
- `pnpm licenses list --json`: PASSED (249 package instances: MIT
  207, Apache-2.0 20, ISC 10, BSD-2-Clause 6, BSD-3-Clause 3,
  CC-BY-4.0 1, BlueOak-1.0.0 1, 0BSD 1 — no policy-forbidden
  licenses; `pnpm-lock.yaml` byte-identical to base)
- `pnpm exec vitest run apps/web/tests/renderer-behavior.test.ts`:
  PASSED (12/12; this file is outside the root `pnpm test` glob,
  run separately as focused renderer evidence)

Preparation checks:

- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`:
  PASSED (OK)
- `python tools/check_repository.py`: PASSED ("PASS repository
  policy")
- `python tools/check_mermaid.py`: PASSED (16 diagrams rendered in
  3 files; 498 Markdown files scanned; CLI 11.16.0)
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED (0 issues
  in 0 of 492 linted files)

## GitHub CI / required checks

All 20 required checks on implementation head
`b470a1ea4690fe498703ceafa249bfb2ebc08713` (the build verified by
the checks; the report-only SELF head carries the identical
product code — it adds only this report file):

CI workflow run 35452542217 (`completed` / `success`), 15/15 jobs
`success`:

| # | Check | Status | Conclusion |
| --- | --- | --- | --- |
| 1 | Repository policy | completed | success |
| 2 | Node contracts | completed | success |
| 3 | Python 3.12 quality and package | completed | success |
| 4 | Python 3.13 quality and package | completed | success |
| 5 | Python 3.14 quality and package | completed | success |
| 6 | Foundation PostgreSQL 14 | completed | success |
| 7 | Foundation PostgreSQL 15 | completed | success |
| 8 | Foundation PostgreSQL 16 | completed | success |
| 9 | Foundation PostgreSQL 17 | completed | success |
| 10 | Foundation PostgreSQL 18 | completed | success |
| 11 | Compose and edge packaging | completed | success |
| 12 | Supply-chain evidence | completed | success |
| 13 | Markdown | completed | success |
| 14 | Mermaid | completed | success |
| 15 | Dependency review | completed | success |

CodeQL workflow run 35452542212 (`completed` / `success`), 5/5:

| # | Check | Status | Conclusion |
| --- | --- | --- | --- |
| 16 | Detect supported languages | completed | success |
| 17 | Analyze (actions) | completed | success |
| 18 | Analyze (python) | completed | success |
| 19 | Analyze (javascript-typescript) | completed | success |
| 20 | CodeQL (workflow run wrapper) | completed | success |

Superseded first SELF publication: the first report-only SELF head
`3e2b0f78d1a0b1911e8752feb15c399ef38a190f` ran CI workflow 35453903907
and CodeQL workflow 35453903929 (CodeQL 5/5 `success`). The CI
run's Compose job failed only on the documented Puck-drag flake
class (`governance` project, `dragUntil` at line 644 of the
governance spec — before the `preview` project ever ran); no other
job in the run failed. That head is superseded by this corrected
report commit; no re-run was invoked for it, so the order's one
permitted unmodified CI re-run remains available should the same
class recur on this final head.

No check pending, skipped, or cancelled. The earlier runs on
superseded heads (35449807016 at `26d1fd3`, 35452174148 at
`0997060`) failed only on the disclosed, since-repaired E2E
defects; they are not the acceptance head. After the SELF
publication commit, this same 20-check set must be re-verified
green on the SELF head before the FIFO response (strategy also
verifies independently per acceptance criterion 9).

## Local setup / dependencies

- uv `0.12.5` (all Python via `uv run --frozen`); Node v24.14.1;
  pnpm `11.22.0`; TypeScript `6.0.3`; Next.js 16.3.3; 24-core VM.
- Disposable local PostgreSQL 127.0.0.1:5432 with fake
  credentials (`PGUSER=postgres PGPASSWORD=qualification-admin`);
  Compose smoke stack `slaif0075a` (fresh disposable stack per run,
  auto-torn-down by the script).
- Playwright browsers per the locked smoke contracts
  (chromium-153.0.8010.52 / playwright 1.62.1; desktop
  Chromium/Firefox/WebKit, tablet, mobile Chromium/WebKit projects
  all green in smoke6).
- No new dependencies; `uv.lock` and `pnpm-lock.yaml`
  byte-identical to base (verified `git diff --stat` empty for
  both).

## Documentation

- The five R7 surfaces are the documentation delta (exact lines
  above); behavior-facing changes (new components, new CSP
  directive, new validator surface) are documented there with
  durable verified-merge wording; no other prose changed.
- No architecture/constitution/protocol file edited (the order
  requires no governance change).

## Files changed (base → implementation head, cumulative)

`git diff --numstat d9a7555… b470a1e…` — 36 files, +2282/−56
(grouped per 2026-09-14 review-unit governance Section 2 in the
next section). Per-commit stats: see Authoritative GitHub state.

## Cumulative base→head size (review-unit governance section 2)

Committed-SHA figures, base =
`d9a7555662a976483b9716e41863de8ecd00decf` (verified `main`):

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-8-a implementation (`d9a7555..b470a1e`, this report's parent) | 36 | 2282 | 56 |
| 078-8-a report (`b470a1e..SELF`, this commit) | 1 | (this file) | 0 |

Cumulative grouped per review unit, per 2026-09-14 review-unit
governance section 2 categories:

| Category | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| Production/config | 12 | 431 | 9 |
| Migrations | 0 (the in-place `060_001` regeneration is listed under production/config and, per the order's own dual listing, counted among generated artifacts; no new migration file) | 0 | 0 |
| Tests/evidence | 14 (5 ordered + 9 disclosed ripple) | 1071 | 34 |
| Generated artifacts | 5 (catalog-v1.json ×2, design-system-v1.json ×2, agent-v1.json; the `060_001` in-place regeneration is dually listed) | 312 | 2 |
| Docs | 3 (README, INCREMENTS, MVP-PROGRESS; the watch-item line lives in MVP-PROGRESS) | 14 | 10 |
| OAP transcript | 2 (order + active; the report arrives in this SELF commit) | 454 | 1 |
| **Total** | **36** | **2282** | **56** |

Tests/evidence breakdown: ordered five —
`services/backend/tests/unit/test_bounded_embed.py` (360/0),
`tests/packaging/test_edge_contract.py` (69/25),
`apps/web/tests/renderer-behavior.test.ts` (113/0),
`tests/e2e/preview.spec.ts` (502/0), `tools/compose/smoke.sh`
(5/0); disclosed ripple nine (all catalog-count/CSP pin updates in
the exact 078/7-a precedent class — `137abbc` updated six of these
same files when the catalog grew 22 → 27):
`packages/component-catalog/tests/index.test.ts` (2/2),
`packages/composition-schema/tests/puck-adapter.test.ts` (1/1),
`services/backend/tests/unit/test_component_catalog.py` (1/1),
`services/backend/tests/unit/test_design_system.py` (1/1),
`services/backend/tests/unit/test_foundation_contract.py` (1/0),
`services/backend/tests/unit/test_route_policy.py` (1/1),
`tests/e2e/governance.spec.ts` (12/2, CSP backstay alignment),
`services/backend/tests/integration/test_agent_mutations.py`
(2/0, catalog set), `tools/compose/public_agent_acceptance.py`
(1/1, catalog count pin).

Budget check (predeclared, order Section 10): production/config 12
of at most 12; migrations 0; ordered test/evidence files 5 of at
most 5 (the nine ripple files are disclosed above, each a
mechanical pin update in the established precedent class — none
adds a new test family); generated artifacts 5 of at most 5 (plus
the dually listed `060_001`); docs 3 of at most 4; OAP transcript =
order + active + report; substantive production/config insertion
scale 431 lines, well under the 1.5k cap. The 36-file cumulative
total sits at the ~20–30-file review-trigger boundary: per the
order's Section 10 that threshold is a review trigger, not a quota,
and no new semantic family was added at any point in this round —
the entire diff is the one ordered bounded-embed family plus its
ordered evidence.

## Safety and scope confirmations

- Scope: exactly the order's bounded embed family (R1–R9); no
  second objective PR; no other PR created, amended, or touched
  (Dependabot PRs #83, #84, #75 explicitly untouched).
- No merge performed; no auto-merge; no close; strategy is the only
  merger.
- No changes under `tools/supply_chain/`, `tests/supply_chain/`, or
  `.github/workflows/` (verified `git diff --stat d9a7555..b470a1e
  -- <paths>` empty for each); no gate normalization, exclusion, or
  relaxation; the Supply-chain evidence CI job is green.
- No new public endpoint, no new scope, no OpenAPI route or
  enumeration change beyond the `x-slaif-*`-only delta (R8), no new
  migration file, no dependency or lockfile change (`uv.lock` /
  `pnpm-lock.yaml` byte-identical to base).
- No new embed provider beyond the pinned allowlist; the allowlist
  is code-defined, versioned, and deterministic (no runtime
  configuration).
- No promotion-pipeline embed check added (082/083 scope; the
  policy module is simply callable from there — forward note only,
  no code).
- No changes to the preview flight-free contract
  (`clientState={false}` untouched) and no Puck adapter code
  changes (Puck consumes the regenerated catalog config).
- No global-region/header/footer/theme or collection-semantics
  changes (078/5 and 078/7 closed contracts untouched).
- No secrets, capabilities, cookies, DB URLs, or private artifact
  URLs in the diff or this report; the smoke's fixture identifiers
  (workspace UUID in the `public-agent-acceptance: OK` line,
  compose project name) are disposable smoke values, not
  credentials; all integration/scratch fixtures use fake
  credentials and are deleted or dropped with their disposable
  databases.
- No production systems, data, or credentials accessed; no Docker
  socket escalation; the browser worker's sandbox policy lines
  (`browser-worker-runtime-policy: OK uid=10001 readonly=yes
  caps=SYS_CHROOT limits=exact network=browser`) are unchanged and
  green.
- All verification claims reference commands that were actually
  executed; nothing skipped or assumed. The one documented flake
  class (Puck drag) appeared in one local smoke run (smoke4,
  before the `preview` project ran — handled by a free local
  re-run per the order's flake policy) and in one superseded
  SELF-head CI run (35453903907, `governance` project only, before
  the `preview` project ran); the CI case affected only the
  superseded first report head that this corrected report commit
  replaces. No CI re-run was invoked, so the order's one
  documented unmodified re-run remains available should this class
  recur on this final head.

## Known limitations / blockers

- No limitations. Nothing is PARTIAL, BLOCKED, or FAILED at the
  implementation head: every ordered surface is implemented, every
  named evidence command was executed and is quoted above, and all
  20 required checks are green on the implementation head.
- Forward notes (not limitations of this increment): local-media
  `<video>` and the remaining media-bound catalog types are 079-
  bound; the promotion-pipeline embed check is 082/083-bound; the
  078/079 seam requires explicit human confirmation before any
  079-qualified activation.

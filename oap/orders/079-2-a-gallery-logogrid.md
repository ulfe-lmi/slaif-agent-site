# OAP Work Order — 079-2-a (catalog breadth: Gallery + LogoGrid)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-09-22 to `oap/orders/079-2-a-gallery-logogrid.md` with
> `oap/active` = `079-2-a`, per the human owner's decisions of
> 2026-09-20 (D2: 079 sequence approved — 079/1 at `079-a`, 079/2 at
> `079-2-a`, 079/3 at `079-3-a`) and after 079/1 (media publication
> core) was accepted, merged, and independently verified on remote
> `main` (PR #92, merge commit
> `577509e7bc990d85a10af5954bee3c6f7c888a4f`, 2026-09-22T20:41:13Z).
> The coding agent executes under the normal OAP execution contract;
> strategy remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-2-a` (increment-qualified round ID: first round of semantic
  increment 2 of numeric Objective 079).
- Mode: CREATE_NEW_PR.
- Branch: `oap/079-2-a-gallery-logogrid`, created from verified current
  `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f` (verified against
  live GitHub 2026-09-22 at activation).
- Expected PR number: next available (GitHub assigns; create exactly one
  PR; do not create, amend, or touch any other PR).
- Depends on 079/1 (media publication core): Gallery/LogoGrid items are
  media references rendered through 079/1's projection media-descriptor
  resolution and preview/public URLs.

## 2. Verified current state (strategy-verified 2026-09-22 at
activation against live GitHub; base = post-079/1 merge main)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f`
  (post-079/1 merge commit; 079/1 delivered: public namespace +
  `content.media_asset.public_status`/`published_at`, finalization
  primitive, public digest route
  `/media/public/sha256/<2>/<2>/<digest>`, preview read path, Agent
  media upload/byte-read, real `Image` renderer with projection media
  descriptor resolution, `dragUntil` stabilization; accepted and merged
  in PR #92 at `577509e7bc990d85a10af5954bee3c6f7c888a4f` on
  2026-09-22).
- Component catalog: 29 types. This increment adds `Gallery` (Basic)
  and `LogoGrid` (Institutional) per the architecture's initial trusted
  catalog minimum; after it, 31 of 32 (`DocumentList` remains 079/3).
- Media: uploads accept `image/png` and `image/jpeg` only
  (`SUPPORTED_MIME`, content-signature verified); preview/public URLs
  per 079/1. Gallery/LogoGrid item props reference these assets.
- 079/1's media-descriptor pattern in `render_api/projection.py`
  (descriptor `{url, mime_type, size_bytes}` or fail-closed marker) is
  the established resolution mechanism; this increment extends it to
  list-valued media-reference props.
- Precedents: catalog type addition pattern from 078/7 (5 content/
  collection components) and 078/8 (2 embed components): declaration in
  `component_catalog.py`, deterministic in-place `060_001` baked-
  catalog regeneration + `CATALOG_V1_REVIEWED_SHA256`, OpenAPI diff
  `x-slaif-*`-only (strip-identity rule), Puck consumes the generated
  catalog config (no Puck adapter code changes).
- `oap/active` = `079-a` (last activated round of the merged 079/1;
  protocol-correct idle state).
- Flake policy: 079/1's R10 stabilized `dragUntil`; this order
  re-declares: at most ONE documented unmodified CI re-run, and only
  for the documented flake class with its exact failure signature; any
  other recurrence is a real failure — fix in code or report BLOCKED.

## 3. Strategic context

Objective 079 continues its catalog-broadening sequence: 079/1 (media
core) -> 079/2 (this: Gallery + LogoGrid) -> 079/3 (DocumentList +
document serving). This increment is one bounded semantic family
(media-reference list components) plus its ordered evidence; it closes
two of the three 078-bound catalog types. No new server media routes,
no migration, no new scope; the family reuses 079/1's descriptor
resolution, the 078/7 mutation-validation integration point, and the
deterministic catalog/060_001 regeneration pattern.

## 4. Bounded scope

Exactly: two new catalog component types with bounded media-reference
list props (contract pinned in R2); their trusted renderers; the
projection descriptor resolution for list-valued media-reference props;
mutation/editor validation wiring (existing media references, site-
scope, MIME class); regenerated generated artifacts (catalog, in-place
`060_001`, OpenAPI `x-slaif-*`-only); the five current-truth doc
updates (durable wording); and full evidence per R8. Nothing else.

## 5. Explicit non-goals

- No `DocumentList` or document/PDF policy work (079/3).
- No changes to 079/1's media core: no new media routes, no store
  changes, no `SUPPORTED_MIME` change, no finalization changes.
- No new migration (in-place `060_001` baked-catalog regeneration only,
  078/7 precedent; no physical schema change).
- No new OpenAPI path or scope string (catalog delta is `x-slaif-*`-
  only; strip-identity rule per 078/7-078/8).
- No data binding, collection views, or generic data-driven behavior.
- No Puck adapter code changes (Puck consumes the generated catalog
  config); no global-region/header/footer/theme changes (078/5 closed
  contract); no collection-semantics changes (078/7 closed contract).
- No new dependency or lockfile change; NO changes under
  `tools/supply_chain/`, `tests/supply_chain/`, or
  `.github/workflows/`; no Dependabot PR work; no preview flight-free
  contract change (`clientState={false}`).

## 6. Requirements

### R1 - Catalog: +2 types (29 -> 31)

In `services/backend/src/slaif_agent_site/content_model/
component_catalog.py`, following the 078/7 declaration pattern exactly
(JSON Schemas per the architecture's catalog-entry definition):

- `Gallery` (category `basic`; leaf: `max_children` 0, no slots, no
  data binding):
  - `title`: localized string, optional, 1..120.
  - `items`: list, 1..12 objects, each EXACTLY:
    - `mediaId`: reference/uuid, required.
    - `alt`: string, required, 1..4096 (item-level strings follow
      the established item pattern; no item-level localization).
    - `aspectRatio`: enum `auto|16:9|4:3|1:1`, optional, default
      `auto`.
  - `columns`: enum `2|3|4`, optional, default `3`.
- `LogoGrid` (category `institutional`; leaf):
  - `title`: localized string, optional, 1..120.
  - `items`: list, 2..24 objects, each EXACTLY:
    - `mediaId`: reference/uuid, required.
    - `name`: string, required, 1..120 (aria/alt text; item-level
      pattern, no item-level localization).
- No item or component prop exposes raw `url`, `src`, `html`, `style`,
  `class`, or script-like input; `mediaId` references are the ONLY
  media input, and renderers get resolved descriptors (R3).
- Deterministic migration: N/A (new types, no existing instances) —
  state this in the catalog entry metadata exactly as 078/7 did.
- Regenerate ALL generated artifacts (catalog-v1.json in both
  packages, in-place `060_001` baked-catalog JSON + SHA guard, agent-
  openapi); all generator `--check` gates zero-diff afterwards.

### R2 - Mutation and editor enforcement

Wire list-item validation into the component-props validation path used
by BOTH the Agent mutation path (the 078/7 `component_facets.py`
integration point) and the human Editor/Puck API path. Per item:
`mediaId` exists, same site, `mime_type` in `image/png|image/jpeg`
(bounded error keys: `gallery.item-missing`, `gallery.item-foreign-
site`, `gallery.item-not-image`, `logogrid.item-missing`,
`logogrid.item-foreign-site`, `logogrid.item-not-image`, plus the list
bounds keys `gallery.items-out-of-range`, `logogrid.items-out-of-
range`). Invalid input -> bounded 422 on the Agent path with the exact
error key (no user-input echo); equivalent Editor rejection. Tree
unchanged, row version unchanged, idempotency/audit unchanged.

### R3 - Projection and trusted renderers

- `render_api/projection.py`: extend 079/1's media-descriptor
  resolution to list-valued media-reference props: each `mediaId`
  resolves to `{url, mime_type, size_bytes}` (preview: 079/1 preview
  URL; public: 079/1 digest URL only when `public_status='public'`,
  else fail-closed marker) or the fail-closed marker. Re-validate
  props at projection time (defense in depth, 078/8 pattern).
- `apps/web/src/renderer/components.tsx` (+ `renderer-v1.css`),
  deterministic attribute order, no JS/event handlers, no inline
  style attributes:
  - `Gallery`: `<section class="sl-gallery sl-gallery--<columns>
    cols">` containing an optional `<h3>` for `title` and
    `<ul class="sl-gallery__items">` with one `<li>` per item; each
    resolved item renders the 079/1 `sl-image` `<img>` pattern (alt,
    loading=lazy, referrerpolicy=no-referrer, aspect via the existing
    `designClasses` tokens on the `<li>`); each fail-closed item
    renders the 079/1 placeholder pattern in the same `<li>`.
  - `LogoGrid`: `<section class="sl-logogrid">` with optional `<h3>`
    and `<ul class="sl-logogrid__items">`; each resolved item
    `<li><img class="sl-logogrid__logo" src="<descriptor.url>"
    alt="<escaped name>" loading="lazy"
    referrerpolicy="no-referrer"></img></li>`; fail-closed items
    render the 079/1 placeholder pattern.
  - CSS: responsive grid (CSS grid, `columns` token), logo grid
    uniform square boxes, desktop/tablet/phone; no remote assets.
- Preview and public render the identical markup except the `src` form
  (079/1 parity rule).

### R4 - OpenAPI (exact delta)

Regenerate `contracts/openapi/agent-v1.json`. Diff against base:
`x-slaif-*` extension keys ONLY (catalog change documented under the
existing component-content extension keys); after stripping all
`x-slaif-*` keys the canonical JSON is byte-identical to base; 45 paths
unchanged (078/7-078/8 decision-8 adjudication rule); no new scope
strings. Drift gate green.

### R5 - Current-truth documentation (durable wording; verified merge
facts only; no live-state claims)

Exactly five surfaces, minimal edits:

- (a) `oap/INCREMENTS.md`: 079/1 row -> "Accepted and merged in PR
  #92 at `577509e7bc990d85a10af5954bee3c6f7c888a4f` on 2026-09-22;
  079/1 is closed" (verified GitHub facts, restated here by strategy). Add the
  079/2 row in the standard in-flight form ("Opened at `079-2-a`
  from verified remote main `<base SHA>`; PR pending; strategy owns
  acceptance and merge").
  `Next` row -> "Remaining 079 scope after 079/2: 079/3 (DocumentList
  and document serving) closes the last 078-bound catalog type
  (32/32); numeric 078 remains PARTIAL until 079/3 lands".
- (b) `oap/MVP-PROGRESS.md`: "Active and remaining sequence" — add
  079/1 to the merged list with verified facts; replace the 079/1
  in-flight clause with the 079/1 merged clause (PR #92 at
  `577509e7bc990d85a10af5954bee3c6f7c888a4f` on 2026-09-22) +
  "increment 079/2 is opened at `079-2-a`"; status table row 078 and
  079 updated to match (078: "079/1 merged per the ledger; Gallery and
  LogoGrid delivered by 079/2 in flight"; 079: "PARTIAL — 079/1 is
  accepted and merged in PR #92 at
  `577509e7bc990d85a10af5954bee3c6f7c888a4f`; 079/2 is opened at
  `079-2-a`"). Keep the OAP/GitHub-authoritative sentences.
- (c) `README.md` capability row "Objective-078/4 page-style data
  plane (merged)": replace the 079/1 in-flight clause with "increment
  079/1 (media publication core) is accepted and merged in PR #92 at
  `577509e7bc990d85a10af5954bee3c6f7c888a4f` on 2026-09-22; increment
  079/2 (Gallery + LogoGrid) is opened at `079-2-a`; GitHub is
  authoritative for live acceptance and merge state."
- (d) `oap/MVP-CONTRACT-AUDIT.md` media row (42): evidence cell —
  append the verified 079/1 merge facts (catalog 29 with real Image;
  public/preview core E2E-proven); Next cell -> "079/2: Gallery +
  LogoGrid (in flight); 079/3: DocumentList + document serving; 083:
  promotion-time finalization call, anonymous public reads gated on
  the accepted revision, rollback".
- (e) `CRITICAL.md`: verify-only (historical banner); edit only if a
  current-state claim is actually found (durable wording).
- PR number: use the actual number GitHub assigns to this PR in the
  docs (do not guess).
- Durable-wording rule per 079/1 R9 (no live-state claims outside the
  standard in-flight row form; GitHub authoritative; the next merge
  must not make committed truth false).

### R6 - Evidence (all actually executed, honestly reported)

- Unit (extend `services/backend/tests/unit/`): list-props validation
  positive/negative (bounds, exact error keys, foreign-site, non-image
  MIME, duplicate items allowed, alt/name bounds); projection
  descriptor resolution for list props (mixed resolved + fail-closed
  markers; public only when public; foreign-site marker).
- Renderer (extend `apps/web/tests/renderer-behavior.test.ts`): exact
  markup pins for Gallery (2/3/4 columns; title present/absent; mixed
  resolved + fail-closed items) and LogoGrid (resolved + fail-closed),
  including forbidden-attribute absence (no inline style, no event
  handler, no `sandbox`/`target`).
- E2E (real browser through public NGINX, within the tests/e2e budget —
  extend an existing spec or add one): composition with Gallery +
  LogoGrid of real uploaded media renders at desktop/tablet; preview/
  public markup parity (identical except src form); hostile Agent PATCH
  suite (>= 10 cases from the R2 error-key list) -> 422 with exact
  keys, tree/row-version unchanged; Editor path rejects the same;
  after 079/1-style direct finalization, public rendering serves the
  items from the digest URLs byte-identical.
- Catalog: generator `--check` gates zero-diff; in-place `060_001`
  consistent; catalog count 31 in all four existing count pins (update
  the pins as the 078/7/078/8 mechanical-ripple class, disclosed per
  file).
- Full local gate (Python, Node, generator `--check`, process smokes)
  and full Compose smoke `sh tools/compose/smoke.sh slaif0075a` rc=0.

### R7 - Hard constraints (079/1 R11 applies unchanged)

No supply-chain/workflow/lockfile changes; no new dependency; no new
migration file; no new endpoint/scope; no secrets in diff or report.

## 7. Acceptance criteria (observable)

1. Catalog has exactly 31 types including Gallery + LogoGrid with the
   R1 prop contracts; all generator `--check` gates zero-diff; in-place
   `060_001` consistent; all four catalog-count pins updated.
2. Mutation/Editor validation unit suite green with every exact error
   key; no tree/version change on rejection.
3. Projection list-descriptor resolution green (preview/public rules;
   fail-closed markers for missing/foreign/non-image).
4. Renderer markup pins green including forbidden-attribute absence and
   fail-closed items; preview/public parity byte-pinned.
5. E2E green: real render at three viewports, hostile rejections,
   public byte-identity after finalization.
6. OpenAPI strip-identity proven (sha256 both sides after stripping
   `x-slaif-*`); drift gate green.
7. All five R5 doc surfaces updated with durable wording; adversarial
   sweep for stale 079/1 in-flight wording returns nothing.
8. No R7 constraint violated (lockfiles byte-identical, no gate
   changes, no new dependency/scope/migration).
9. CI: all 20 required checks successful on the exact report-only head
   (strategy verifies independently).

## 8. Verification and workflow

- Local authority as usual (packages, browsers, databases, services,
  tests, CI logs are yours).
- GitHub: create branch + PR from verified `main` (post-079/1); push
  every commit; on completion commit the activated order, `oap/active`
  (= `079-2-a`), and the report to the PR branch WITHOUT changing
  strategic-owned order/active content; the report publication commit
  is report-only with `Report publication commit: SELF`; its parent is
  the literal implementation-head SHA.
- Do not merge; strategy is the only merger.
- Flake policy per Section 2 (one documented unmodified re-run,
  documented flake class only).

## 9. Report requirements

`oap/reports/079-2-a-gallery-logogrid.md`: work-order file + sha256,
`oap/active` bytes, PR/branch/head SHAs (base, start, implementation
head, SELF), per-requirement evidence (R1-R7) with exact command
outputs, the OpenAPI strip-identity proof (sha256 both sides), honest
status (COMPLETE only if every requirement's named evidence actually
ran — otherwise PARTIAL/BLOCKED with the exact gap), cumulative
base->head size table grouped per 2026-09-14 review-unit governance
Section 2 (base = the verified post-079/1 main SHA), predeclared-
budget check, safety/scope confirmations, and the exact CI state at
the implementation head.

## 10. Predeclared review budget (2026-09-14 review-unit governance
Section 1)

- Production/config: at most 10 files (`component_catalog.py`;
  `design_system.py` only if a token is needed; `projection.py`; the
  component-props validation integration point; `components.tsx`;
  `renderer-v1.css`; in-place `060_001` regeneration; the four
  catalog-count pin files if they are not counted under tests).
- Migrations: 0 (in-place `060_001` baked-catalog regeneration only).
- Tests/evidence: at most 5 files (unit validation extension;
  `renderer-behavior.test.ts`; the E2E spec extension; any count-pin
  files not counted above; smoke expectation only if changed).
- Generated artifacts: at most 4 (catalog-v1.json x2, agent-v1.json,
  in-place 060_001).
- Docs: at most 5 files (README, INCREMENTS, MVP-PROGRESS,
  MVP-CONTRACT-AUDIT; CRITICAL.md only if R5(e) finds a stale claim).
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

# OAP Work Order — 078-8-a (bounded embed family: VideoEmbed + MapBlock)

## 1. Identifier and mode

- ID: `078-8-a` (increment-qualified round ID per the 2026-09-14
  ID-namespace amendment: first round of semantic increment 8 of
  numeric Objective 078).
- Mode: CREATE_NEW_PR.
- Branch: `oap/078-8-a-bounded-embed-family`, created from verified
  current `main`.
- Expected PR number: #88 (GitHub assigns; create exactly one PR; do
  not create, amend, or touch any other PR).

## 2. Verified current state (strategy-verified 2026-09-19; re-verify
at turn start against live GitHub before any edit)

- Remote `main` = `d9a7555662a976483b9716e41863de8ecd00decf`
  (merge commit for PR #87 / 078/7, merged 2026-09-19T13:03:12Z,
  parents `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` +
  `4388fa8589f7de7efacc22e02fb6d5e9b9d07005`).
- 078/1 through 078/7 are all accepted and merged: PR #77 at
  `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`, PR #79 at
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`, PR #80 at
  `fe31c9f30a7797d0916ad7f8fb56344bc61526f3`, PR #81 at
  `26cafc1c0c91de5eee8406e8d477c50ea0208058`, PR #85 at
  `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`, PR #86 at
  `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`, PR #87 at
  `d9a7555662a976483b9716e41863de8ecd00decf`.
- No product OAP PR is open. Dependabot PRs #83, #84, and #75 are
  open and are EXPLICITLY OUT OF SCOPE: do not merge, refresh,
  rebase, bump, or reference them.
- Component catalog: 27 types (verified against
  `packages/component-catalog/src/catalog-v1.json`). Remaining
  architecture-minimum types: `VideoEmbed` and `MapBlock` (this
  increment); `Gallery`, `LogoGrid`, `DocumentList`, and real
  `Image` rendering are Objective-079 media-bound (do not implement).
- Media state: upload plus private authenticated read only
  (`media_service/media_http.py`: `POST /v1/sites/{site_id}/assets`,
  `GET /v1/sites/{site_id}/assets/{media_id}/content`). No public
  media serving/finalization exists (Objective 079). Therefore this
  increment's `VideoEmbed` is external-allowlisted embed only; a
  local-media `<video>` variant is explicitly 079-bound.
- Edge CSP (both adapters, `infra/nginx/nginx.conf` line 59-62 and
  `infra/apache/slaif-agent-site.conf`) currently contains NO
  `frame-src`; external iframes are blocked by `default-src 'self'`.
  `tests/packaging/test_edge_contract.py` asserts the exact CSP
  policy lines and forbids `http:`/`https:` substrings in them.
- Build determinism: 078/7-b added the fail-closed canonical
  client-reference-manifest plugin to
  `apps/web/next.config.mjs`; the Supply-chain reproducibility gate
  is green at `d9a7555`.
- `oap/active` currently contains `078-7-b` (last activated round;
  protocol-correct, not in flight).
- Current truth surfaces at `d9a7555` (exact quoted text you will
  edit under requirement 7):
  - `oap/INCREMENTS.md` 078/7 row: "Opened at `078-7-a` from
    verified remote main `2746c9f08c00fd84dff59bfd1536ce7319e16ff9`;
    PR pending; strategy owns acceptance and merge"; `Next` row:
    "Remaining 078 scope after 078/7".
  - `oap/MVP-PROGRESS.md` "Active and remaining sequence": ends with
    "...PR #86 at `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`);
    increment 078/7 is opened at `078-7-a` (PR #87). Acceptance and
    containment in `main` are determined by OAP and GitHub state,
    not this document; GitHub remains authoritative for live
    acceptance and merge state. ..."
  - `oap/MVP-PROGRESS.md` status table row 078 ends: "...078/6 is
    accepted and merged in PR #86 at
    `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`; increment 078/7 is
    opened at `078-7-a` (PR #87)".
  - `README.md` Objective-078/4 capability row ends: "...global
    regions were delivered by increment 078/5, accepted and merged
    in PR #85 at `2746c9f08c00fd84dff59bfd1536ce7319e16ff9` on
    2026-09-19, and the catalog increment 078/7 is opened at
    `078-7-a` (PR #87); GitHub is authoritative for live acceptance
    and merge state."
  - `oap/MVP-PROGRESS.md` lines 95-102 (historical narrative about
    the 078/2 era) currently reads in part: "Site-global theme
    precedence, global regions, exact-workspace Puck, review,
    promotion, and publication remain **PARTIAL/NOT IMPLEMENTED**"
    and "global regions and catalog expansion remain deferred."
    These two phrases are a strategy-identified non-material watch
    item (tense ambiguity in a historical paragraph) that this
    order repairs minimally (requirement 7e).

## 3. Strategic context

Objective 078 is PARTIAL with 078/1-078/7 merged. This increment
closes the bounded external embed/URL-safety family of the
architecture catalog minimum: `VideoEmbed` (basic) and `MapBlock`
(institutional), implementing the architecture rules "reject raw
CSS/style/JS/event handlers/arbitrary iframe/template/package/
source/executable prop" (Section 7) and "URLs allow https,
policy-approved http, mailto, tel, relative; reject javascript,
file, and data" (Section 14), with no autoplay (Section 7
promotion-check clause) and no third-party tracker-class embeds.
After 078/8, all remaining Objective-078 catalog types are
079-media-bound; the 078/079 seam requires explicit human
confirmation before any 079-qualified activation.

## 4. Bounded scope

Exactly: a versioned code-defined bounded-embed policy; two new
catalog component types with structured (non-URL-string) props;
their trusted renderers; mutation/editor/projection enforcement;
the exact edge CSP `frame-src` backstop in both adapters with the
strengthened edge-contract test; regenerated generated artifacts;
the five current-truth doc updates (durable wording); and full
evidence per Section 9. Nothing else.

## 5. Explicit non-goals

- No local-media `<video>` variant or any media prop (079-bound).
- No `Gallery`, `LogoGrid`, `DocumentList`, or `Image` changes
  (079-bound).
- No new Alembic migration (in-place `060_001` baked-catalog
  regeneration only, precedent 078/7; no physical schema change).
- No new public route, scope, or OpenAPI path; no dependency or
  lockfile change; no new embed provider beyond the pinned
  allowlist; no runtime-configurable allowlist (code-defined,
  versioned, deterministic).
- NO changes under `tools/supply_chain/`, `tests/supply_chain/`,
  or `.github/workflows/` (hard constraint; do not modify any gate,
  normalization entry, or exclusion; if new renderer code ever
  caused a reproducibility failure, STOP and report BLOCKED with
  byte-level analysis for separate strategic adjudication).
- No global-region/header/footer/theme changes (078/5 closed
  contract); no collection-semantics changes (078/7 closed
  contract); no announcement bar.
- No promotion-pipeline embed check (promotion is 082/083 scope;
  the policy module is designed to be callable from there -
  forward note only, no code).
- No Dependabot PR work; no changes to the preview flight-free
  contract (`clientState={false}`); no Puck adapter code changes
  (Puck consumes the generated catalog config).

## 6. Requirements

### R1 - Bounded embed policy module (new, pure)

Create `services/backend/src/slaif_agent_site/content_model/
bounded_embed.py` (pure functions, no I/O, no network):

- `EMBED_POLICY_VERSION = "bounded-embed/v1"`.
- Code-defined allowlist constants, exactly:
  - Video providers:
    - `youtube-nocookie`: host exactly `www.youtube-nocookie.com`,
      path exactly matching `^/embed/[A-Za-z0-9_-]{11}$`.
    - `vimeo`: host exactly `player.vimeo.com`, path exactly
      matching `^/video/[0-9]{6,}$`.
  - Map provider:
    - `osm`: host exactly `www.openstreetmap.org`, path exactly
      `/export/embed.html`.
- Canonical URL builders (https only; no fragment; no query
  parameters for video; sorted query keys for map; never emit any
  autoplay, marketing, or tracking parameter):
  - `canonical_video_embed(provider, video_id) -> str` producing
    `https://www.youtube-nocookie.com/embed/<id>` or
    `https://player.vimeo.com/video/<id>`.
  - `canonical_map_embed(bbox, layer) -> str` producing
    `https://www.openstreetmap.org/export/embed.html?bbox=<west>,
    <south>,<east>,<north>` with optional `&layer=<layer>`.
- Prop validators with bounded error keys (never echo user input):
  - `validate_video_embed_props(props)` -> `(True, None)` or
    `(False, key)` with keys in
    `{embed.provider-unknown, embed.video-id-invalid,
    embed.title-missing, embed.title-too-long}`.
  - `validate_map_embed_props(props)` -> `(True, None)` or
    `(False, key)` with keys in
    `{embed.bbox-missing, embed.bbox-out-of-range,
    embed.bbox-invalid-order, embed.layer-unknown,
    embed.title-missing, embed.title-too-long}`.
- Validation rules: `title` required localized string, 1..120
  characters (localized pattern per existing catalog text props).
  Map `bbox` = object with numeric `west`, `south`, `east`,
  `north`: west/east in [-180, 180], south/north in
  [-85.05112877, 85.05112877], west < east, south < north.
  `layer` optional, default `mapnik`, in `{mapnik, cycle,
  transport}`.
- The policy NEVER fetches URLs server-side (pure syntactic
  allowlist; no SSRF surface; embed loads occur only in the end
  user's browser).
- Strategy-recorded design decision (do not deviate): the initial
  video allowlist is the reduced-tracking embed endpoint of each
  provider (`youtube-nocookie`, not `youtube.com`; `player.vimeo.
  com`); no tracker-class embed (full youtube.com, ad networks,
  analytics) may be added without a separate reviewed policy
  change. Autoplay is structurally impossible (no autoplay
  parameter is ever emitted).

### R2 - Catalog: +2 types (27 -> 29)

In `services/backend/src/slaif_agent_site/content_model/
component_catalog.py` (plus `design_system.py` only if a token is
needed), following the 078/7 declaration pattern exactly:

- `VideoEmbed` (basic): props `provider` (enum
  {youtube-nocookie, vimeo}), `video_id` (string, pattern per
  provider), `title` (required localized string 1..120). Leaf
  component; no children/slots; no data binding.
- `MapBlock` (institutional): props `bbox` (object
  {west, south, east, north}, numbers), `layer` (enum
  {mapnik, cycle, transport}, default mapnik), `title` (required
  localized string 1..120). Leaf component; no children/slots; no
  data binding.
- Neither component exposes any raw `url`, `src`, `html`, `style`,
  `class`, or script-like prop: the structured props above are the
  ONLY input, and renderers rebuild URLs canonically from them.
- Accessibility: the iframe `title` is mandatory (R3).
- Deterministic migration: N/A (new types, no existing instances);
  state this in the catalog entry metadata exactly as 078/7 did.
- Regenerate ALL generated artifacts (catalog-v1.json,
  design-system-v1.json in both packages, agent-openapi, in-place
  `060_001` baked-catalog JSON + SHA guard); all generator
  `--check` gates must pass with zero diff afterwards.

### R3 - Trusted renderers (exact markup contract)

In `apps/web/src/renderer/components.tsx` (plus
`apps/web/public/renderer-v1.css`), deterministic attribute order,
no JS/event handlers, no inline style attributes (CSP
`style-src 'self'`), no `sandbox`, no `allow`, no
`allowfullscreen`:

- `VideoEmbed`:
  `<iframe class="sl-embed sl-embed--video" src="<canonical-url
  from provider+video_id>" title="<escaped title>" loading="lazy"
  referrerpolicy="no-referrer"></iframe>`
- `MapBlock`:
  `<iframe class="sl-embed sl-embed--map" src="<canonical-url from
  bbox(+layer)>" title="<escaped title>" loading="lazy"
  referrerpolicy="no-referrer"></iframe>`
- CSS (bundled, hashed, self-hosted): `.sl-embed` width 100%,
  display block, border 0; `.sl-embed--video` aspect-ratio 16/9;
  `.sl-embed--map` aspect-ratio 4/3; responsive by container
  width (desktop/tablet/phone).
- Fail-closed: if projection ever receives props that fail R1
  validation, render the existing bounded error/placeholder
  pattern - NEVER an iframe with an unvalidated URL.
- Preview and public render the identical markup (same
  projection; preview stays flight-free).

### R4 - Mutation and editor enforcement

Wire the R1 validators into the component-props validation path
used by BOTH the Agent mutation path (the same integration point
as 078/7's `component_facets.py` validation) and the human
Editor/Puck API path. Invalid embed props -> bounded 422 on the
Agent path carrying exactly the R1 error key (no user-input echo);
equivalent rejection on the Editor path. Tree unchanged, row
version unchanged, idempotency/audit semantics unchanged.

### R5 - Projection

`services/backend/src/slaif_agent_site/render_api/projection.py`:
pass the validated embed props through to the render payload using
the 078/7 prop-passing pattern, re-validating via R1 at projection
time (defense in depth).

### R6 - Edge CSP frame-src backstop (exact)

- Add to BOTH policy lines in `infra/nginx/nginx.conf` (public
  default and the Puck editor line) and the corresponding lines in
  `infra/apache/slaif-agent-site.conf`, after `object-src
  'none';`:
  `frame-src https://www.openstreetmap.org
  https://www.youtube-nocookie.com https://player.vimeo.com;`
- Rework `tests/packaging/test_edge_contract.py` to pin this
  strengthened contract (strengthen, do not weaken): assert the
  exact full CSP line for both adapters (nginx/apache parity as
  today), assert the `frame-src` directive equals EXACTLY the
  three-host allowlist, and assert that every OTHER directive
  still contains no `http:` or `https:` substring.
- Update the Compose smoke `edge-header-policy` expectation to
  assert the new `frame-src` (exact string).

### R7 - Current-truth documentation (durable wording; verified
merge facts only; no live-state claims)

Exactly five surfaces, minimal edits, no other prose
restructuring:

- (a) `oap/INCREMENTS.md`: 078/7 row -> "Accepted and merged in
  PR #87 at `d9a7555662a976483b9716e41863de8ecd00decf` on
  2026-09-19; 078/7 is closed". Add the 078/8 row in the standard
  in-flight form: "Opened at `078-8-a` from verified remote main
  `d9a7555662a976483b9716e41863de8ecd00decf`; PR pending;
  strategy owns acceptance and merge". `Next` row -> "Remaining
  078 scope after 078/8" (rest of the row unchanged).
- (b) `oap/MVP-PROGRESS.md` "Active and remaining sequence":
  extend the verified-merge-SHA list with "PR #87 at
  `d9a7555662a976483b9716e41863de8ecd00decf`", change "078/1,
  078/2, 078/3, 078/4, 078/5, and 078/6" to include "and 078/7",
  and replace "increment 078/7 is opened at `078-7-a` (PR #87)"
  with "increment 078/8 is opened at `078-8-a` (PR #NN)" where NN
  is the actual PR number; keep the OAP/GitHub-authoritative
  sentences.
- (c) `oap/MVP-PROGRESS.md` status table row 078: append "078/7 is
  accepted and merged in PR #87 at
  `d9a7555662a976483b9716e41863de8ecd00decf`"; replace
  "increment 078/7 is opened at `078-7-a` (PR #87)" with
  "increment 078/8 is opened at `078-8-a` (PR #NN)".
- (d) `README.md` Objective-078/4 row: replace "and the catalog
  increment 078/7 is opened at `078-7-a` (PR #87); GitHub is
  authoritative..." with "; the catalog increment 078/7 is
  accepted and merged in PR #87 at
  `d9a7555662a976483b9716e41863de8ecd00decf` on 2026-09-19;
  increment 078/8 (bounded embed family) is opened at `078-8-a`
  (PR #NN); GitHub is authoritative for live acceptance and merge
  state."
- (e) `oap/MVP-PROGRESS.md` lines 95-102 (watch item): minimal
  temporal scoping, two phrases only - "remain **PARTIAL/NOT
  IMPLEMENTED**" -> "remained **PARTIAL/NOT IMPLEMENTED** at the
  time of the 078/2 increment", and "global regions and catalog
  expansion remain deferred" -> "remained deferred at 078/4
  (global regions were delivered in 078/5; catalog breadth is in
  delivery from 078/7 onward)". No other change to that paragraph.

### R8 - OpenAPI (exact delta)

Regenerate `contracts/openapi/agent-v1.json`. The diff against
base must be `x-slaif-*` extension keys ONLY (the 078/7
decision-8 adjudication rule): after stripping all `x-slaif-*`
keys, the canonical JSON must be byte-identical to the base
version; 45 paths unchanged; no new scope strings; the new props
documented under the existing patch-path extension keys using the
existing `component-content-props:write` scope.

### R9 - Evidence (all actually executed, honestly reported)

- Unit: new `services/backend/tests/unit/test_bounded_embed.py` -
  positive (byte-pinned canonical URLs for all three provider/
  layer variants) and negative (host substitution
  `www.youtube.com`, `evil.example`; non-https; query injection
  `?autoplay=1` on the id form; `javascript:`, `data:`, `file:`;
  invalid/oversized ids; out-of-range and invalid-order bboxes;
  unknown layers; missing/oversized titles - each mapped to the
  exact error key).
- Renderer: extend `apps/web/tests/renderer-behavior.test.ts` with
  the exact markup pins (VideoEmbed youtube-nocookie + vimeo,
  MapBlock mapnik + cycle) including the ABSENCE of
  sandbox/allow/allowfullscreen/inline-style attributes.
- E2E (real browser, add a spec within the tests/e2e budget or
  extend an existing one): a page containing MapBlock +
  VideoEmbed renders the exact pinned markup at desktop and
  tablet; hostile Agent PATCH suite (>= 10 cases from the unit
  negative list) -> 422 with exact error keys and unchanged tree
  (row version unchanged); Editor path rejects the same inputs;
  preview vs public markup byte-identical for both components;
  public-page CSP header contains the exact `frame-src`
  allowlist; no autoplay parameter appears in any emitted iframe
  src.
- Full local gate (Python gate, Node gate, all generator
  `--check` gates, process smokes) and full Compose smoke
  `sh tools/compose/smoke.sh slaif0075a` rc=0 (the
  `edge-header-policy` expectation updated per R6).

## 7. Acceptance criteria (observable)

1. Catalog has exactly 29 types including the two new entries;
   all generator `--check` gates zero-diff; in-place `060_001`
   regeneration consistent.
2. `bounded_embed.py` unit tests green, including every pinned
   canonical URL and every hostile rejection with exact error key.
3. Renderer markup pins green (renderer-behavior suite) including
   forbidden-attribute absence.
4. Agent + Editor mutation rejection E2E green; no tree/version
   change on rejection; preview/public byte-parity.
5. Both adapters carry the exact `frame-src`; strengthened edge
   contract test green; Compose smoke `edge-header-policy` line
   green with the new expectation.
6. OpenAPI diff is `x-slaif-*`-only and byte-identical to base
   after stripping those keys; drift gate green.
7. All five R7 doc surfaces updated with durable wording; a grep
   for stale "078/7 is opened" / "after 078/7" / "remain deferred"
   (in the repaired sense) returns nothing in README, INCREMENTS,
   MVP-PROGRESS.
8. No changes under `tools/supply_chain/`, `tests/supply_chain/`,
   `.github/workflows/`; `uv.lock`/`pnpm-lock.yaml` byte-identical
   to base; no new migration file.
9. CI: all 20 required checks successful on the exact report-only
   head (strategy verifies independently).

## 8. Verification and workflow

- Local authority as usual (packages, browsers, databases,
  services, tests, CI logs are yours).
- GitHub: create branch + PR #88 from verified `main`; push every
  commit; on completion commit the activated order, `oap/active`
  (= `078-8-a`), and the report to the PR branch WITHOUT changing
  strategic-owned order/active content; report publication commit
  is report-only with `Report publication commit: SELF`; its
  parent is the literal implementation-head SHA.
- Do not merge; strategy is the only merger.
- Flake policy: the documented Puck drag flake class
  (`governance.spec.ts` `dragUntil` sections) allows at most ONE
  documented unmodified re-run; every other failure must be fixed
  in code, not re-run.

## 9. Report requirements

`oap/reports/078-8-a-bounded-embed-family.md`: work-order file +
sha256, `oap/active` bytes, PR/branch/head SHAs (base, start,
implementation head, SELF), per-requirement evidence (R1-R9) with
exact command outputs for the gates and the smoke final status
lines, the OpenAPI strip-identity proof (sha256 both sides),
honest status (COMPLETE only if every requirement's named
evidence actually ran - otherwise PARTIAL/BLOCKED with the exact
gap), cumulative base->head size table grouped per 2026-09-14
review-unit governance Section 2 (base = `d9a7555662a976483b9716e41863de8ecd00decf`), predeclared-budget check, safety/scope
confirmations (no endpoints/scopes/migrations/deps/gate
changes; no secrets in diff/report), and the exact CI state at
the implementation head.

## 10. Predeclared review budget (2026-09-14 review-unit
governance Section 1)

- Production/config: at most 12 files
  (`bounded_embed.py`; `component_catalog.py`; `design_system.py`
  only if needed; `projection.py`; the agent-mutation validation
  integration point; `components.tsx`; `renderer-v1.css`;
  `nginx.conf`; `slaif-agent-site.conf`; `060_001` in-place
  regeneration).
- Migrations: 0.
- Tests/evidence: at most 5 files
  (`test_bounded_embed.py`; `test_edge_contract.py`;
  `renderer-behavior.test.ts`; the E2E spec; the smoke
  expectation line).
- Generated artifacts: at most 5 (catalog-v1.json;
  design-system-v1.json x2; agent-v1.json; in-place 060_001).
- Docs: at most 4 files (INCREMENTS, MVP-PROGRESS, README; the
  watch-item line lives in MVP-PROGRESS).
- OAP transcript: order + active + report.
- Substantive implementation-line scale: at most 1.5k.
- This is a fresh single-family PR; the ~20-30 file /
  several-thousand-line threshold remains a REVIEW TRIGGER, not a
  quota. If the cumulative trigger is crossed mid-round, the PR
  enters CLOSURE_ONLY per Section 3 of the same amendment: no new
  semantic family, only finite defects/evidence.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Every strategic review of this PR calculates base -> current
  head CUMULATIVE size, grouped per Section 2.
- If strategy rejects a completion claim after substantive
  implementation, or the cumulative trigger is crossed, the PR
  enters CLOSURE_ONLY (Section 3) - no new semantic family, no
  adjacent feature, no opportunistic scope.
- On rejection, strategy publishes one finite checklist of
  unresolved criteria with the exact executable evidence for
  each (Section 4). A later report may claim COMPLETE only if
  every named criterion was actually executed.
- Separable functionality starts from verified merged main in
  another PR (Section 5).

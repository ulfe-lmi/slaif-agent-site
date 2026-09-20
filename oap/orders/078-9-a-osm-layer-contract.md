# OAP Work Order — 078-9-a (MapBlock OSM layer contract repair)

> **STATUS: DRAFT — inert strategic preparation.** This file lives in the
> strategic workspace and is NOT an activated order. It becomes operative
> only when strategy atomically publishes it to
> `oap/orders/078-9-a-osm-layer-contract.md`, sets `oap/active` to
> `078-9-a`, and signals the coding agent. Nothing in this file changes
> repository state.

## 1. Identifier and mode

- ID: `078-9-a` (increment-qualified round ID: first round of semantic
  increment 9 of numeric Objective 078; the bounded maintenance
  increment designated by the human directive of 2026-09-20, D1).
- Mode: CREATE_NEW_PR.
- Branch: `oap/078-9-a-osm-layer-contract`, created from verified
  current `main` (exact base SHA re-verified against live GitHub at
  activation and stated in the published order).
- Expected PR number: next available (GitHub assigns; create exactly one
  PR; do not create, amend, or touch any other PR).

## 2. Verified current state (strategy-verified 2026-09-20 against live
GitHub and the live OSM provider; re-verify at activation)

- Remote `main` = `ddd1559f021762316f5a64989a307355acb4aab2` (PR #88 /
  078/8, merged 2026-09-19; post-merge checks all successful, none
  pending).
- Product layer allowlist, three surfaces, all currently
  `{"mapnik", "cycle", "transport"}`:
  - `services/backend/src/slaif_agent_site/content_model/bounded_embed.
    py` `MAP_LAYERS` (server canonical-URL builder).
  - `apps/web/src/renderer/components.tsx` `EMBED_MAP_LAYERS`.
  - Catalog `MapBlock` `layer` enum in `component_catalog.py`, the
    in-place `060_001` baked catalog, the two generated
    `catalog-v1.json` files, and the OpenAPI `x-slaif-*` extension.
- Embed URL form: `https://www.openstreetmap.org/export/embed.html?
  bbox=<west>,<south>,<east>,<north>` with optional `&layer=<layer>`
  (default `mapnik` emits no layer parameter).
- Live provider finding (strategy observation 2026-09-20; the executor
  must re-verify with its own probes in the report): the live OSM
  embed endpoint's JS selects the layer from a registry,
  `r = i[(t.get("layer")||"").replaceAll(" ","")] || i.mapnik` —
  UNKNOWN VALUES SILENTLY FALL BACK TO `mapnik`. Registry keys observed:
  `mapnik`, `cyclosm`, `cyclemap`, `transportmap`, `hot`,
  `shortbread`. Therefore `cycle` and `transport` are NOT supported
  provider layer values: today's `layer=cycle` / `layer=transport`
  iframes silently render the standard map.
- Live probes (2026-09-20, Ljubljana tile z12): `mapnik` tile 200
  image/png from `tile.openstreetmap.org`; `cyclemap` tile 200
  image/png (256x256) from `api.thunderforest.com/cycle/...` (OSM-
  supplied key in the provider's own bundle); `transportmap` style 200
  application/json from `api.thunderforest.com/styles/transport/
  style.json`. The corrected three-value allowlist is live-proven.
- Root cause: the immutable 078-8-a order pinned `{mapnik, cycle,
  transport}`, and the 078/8 E2E was hermetic (provider hosts
  route-mocked; "the evidence is the emitted markup, never live
  provider state"), so the provider contract was never observed. The
  078/8 order/report/acceptance remain immutable historical evidence;
  this increment repairs the contract forward.
- Stale post-merge current-truth surfaces (078/8 merged, docs still say
  opened/pending): `oap/INCREMENTS.md` 078/8 row ("PR pending"),
  `README.md` capability row ("increment 078/8 ... opened at
  `078-8-a` (PR #88)"), `oap/MVP-PROGRESS.md` sequence sentence and 078
  status row (same). Correct facts: PR #88 merged at
  `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19 (verify
  against live GitHub at activation).
- Tooling facts (`tools/check_repository.py`): every `.md` in
  `oap/orders/` must start with a valid `NNN-L`/`NNN-I-L` identifier
  and each identifier may appear in exactly ONE order file; the active
  identifier must have exactly one order; `INERT_PLANNED_OAP_
  IDENTIFIERS` = 074-a..091-a (report exemption); `oap/governance/` is
  the dated-governance-document location. The inert preplanned file
  `oap/orders/079-a-agent-media-semantics.md` would collide with the
  next activation (`079-a`, per the human directive of 2026-09-20,
  D2) and must be retired before that activation.
- `oap/active` = `078-8-a` (last activated round; protocol-correct idle
  state).
- Flake policy: at most ONE documented unmodified CI re-run, and only
  for the documented flake class with its exact failure signature; any
  other recurrence is a real failure — fix in code or report BLOCKED.

## 3. Strategic context

Bounded maintenance increment for 078/8: correct the MapBlock provider
contract to the layer values the live OSM embed endpoint actually
supports, close the hermetic-evidence gap with a live provider
observation, repair the post-merge current-truth drift, and retire the
inert `079-a` preplanned file so the next activation keeps a unique
ID-to-order mapping. No new product functionality. After this merges,
no further ordinary 078 product implementation is planned; the
078-bound catalog types (Gallery, LogoGrid, DocumentList, real Image)
are 079 increments per the human directive of 2026-09-20 (D1); numeric
078 remains PARTIAL until those are implemented and proven, and is
reclassified COMPLETE only after independent verification of the
resulting evidence (D1).

## 4. Bounded scope

Exactly: the corrected three-value layer allowlist in the three product
surfaces plus regenerated artifacts (R1); fail-closed rejection of the
old values (R1); updated hermetic contract tests (R2); the live
provider observation spec executed locally as report evidence (R3);
five current-truth doc repairs with durable wording (R4); retirement of
the inert `079-a` preplanned file plus a short governance note (R5);
full evidence per Section 7. Nothing else.

## 5. Explicit non-goals

- No new layer values: `cyclosm`, `hot`, `shortbread` (and any other
  registry entries) are OUT of scope — smallest proven allowlist per
  the human directive; the product keeps its three layers (standard,
  cycling, transport) with corrected identifiers.
- No changes to the VideoEmbed contract or any other embed-family
  behavior (host allowlist, CSP `frame-src` unchanged — the layer
  values do not affect CSP).
- No new route, endpoint, scope string, migration file, dependency,
  lockfile, or supply-chain/workflow change.
- No physical data migration or content-model change (content models
  are bounded workspace data; the no-persistence proof in R1 replaces
  any data work).
- No rewriting of the immutable 078-8 order, report, or acceptance
  records; no editing of the moved preplanned file's content.
- No Dependabot PR work; no Puck/global-region/theme/collection
  changes.

## 6. Requirements

### R1 - Corrected provider contract (three-value allowlist)

- `bounded_embed.py`: `MAP_LAYERS = ("mapnik", "cyclemap",
  "transportmap")`; default remains `mapnik`; `canonical_map_embed`
  URL form unchanged.
- `components.tsx`: `EMBED_MAP_LAYERS = new Set(["mapnik",
  "cyclemap", "transportmap"])`.
- Catalog: `MapBlock` `layer` enum -> `["mapnik", "cyclemap",
  "transportmap"]` in `component_catalog.py`; deterministic in-place
  `060_001` regeneration + `CATALOG_V1_REVIEWED_SHA256`; regenerate ALL
  generated artifacts (catalog-v1.json in `packages/component-catalog`
  and `packages/composition-schema`, agent openapi); generator
  `--check` gates zero-diff afterwards; the four catalog-count pins are
  UNCHANGED (29 types; disclosed per file as verified-unchanged).
- Fail-closed: after the enum change, persisted or submitted values
  `cycle` / `transport` are rejected by catalog validation on BOTH the
  Agent and Editor paths (existing bounded rejection semantics; unit
  negatives with exact error keys).
- No-persistence proof: repository-wide grep of fixtures/seeds for the
  old layer values (expect zero after the R2 test updates, disclosed);
  runtime scan of the Compose environment's stored component props for
  `layer` in `{cycle, transport}` (expected 0 on the fresh volume);
  report both results. No content migration is performed.

### R2 - Hermetic contract tests (CI, values corrected)

- `services/backend/tests/unit/test_bounded_embed.py`: `MAP_LAYERS`
  pin updated; canonical-URL pins for `cyclemap` and `transportmap`
  (and default `mapnik` with no layer parameter); negatives:
  `cycle` / `transport` rejected.
- Renderer behavior tests: `EMBED_MAP_LAYERS` and exact markup pins
  with the corrected values (mapnik default emits no `layer`
  parameter; the two corrected values emit the exact query form).
- `tests/e2e/preview.spec.ts`: update the hermetic embed pins (the map
  iframe `src` pins and the MapBlock fixture creations that use
  `layer: "cycle"` — exact lines identified at activation); the
  hermetic provider-fixture contract itself is UNCHANGED.
- OpenAPI: `x-slaif-*`-only delta, strip-identity byte-identical after
  stripping, 45 paths unchanged, drift gate green.

### R3 - Live provider observation (required local evidence; NOT part
of the 20 CI checks)

- New spec `tests/e2e/live-osm-provider.spec.ts` with a header
  documenting the provider dependency; NOT referenced by any
  `testMatch` project in the Playwright config and NOT invoked by
  `smoke.sh` (the deterministic CI contract stays hermetic per the
  078/8 design; this spec is local-execution evidence).
- Spec behavior (real Compose environment, real network, no route
  mocking of `www.openstreetmap.org`):
  1. Compose a preview page with a `MapBlock` for each of `mapnik`,
     `cyclemap`, `transportmap` (follow the existing
     `preview.spec.ts` embed-creation pattern).
  2. Load each page; assert the OSM iframe actually loads (frame
     document title `OpenStreetMap Embedded`).
  3. Assert layer-specific upstream requests observed from the iframe:
     `mapnik` -> host `tile.openstreetmap.org`; `cyclemap` -> host
     `api.thunderforest.com` with path prefix `/cycle/`;
     `transportmap` -> host `api.thunderforest.com` with path prefix
     `/styles/transport/`.
  4. Provider-level negative control: load the bare URL
     `https://www.openstreetmap.org/export/embed.html?bbox=<valid
     bbox>&layer=cycle` directly and observe
     `tile.openstreetmap.org` requests (mapnik fallback) — documents
     that the legacy values silently fell back.
  5. Save a screenshot per layer under the test-results artifacts.
- The spec must NOT embed or reference any provider API key (assert
  hosts/paths only).
- The executor actually runs this spec and records in the report the
  exact observed request evidence and screenshot paths. If the
  provider is unavailable, the report is PARTIAL/BLOCKED with same-
  host probe output — never a silent skip.

### R4 - Current-truth reconciliation (durable wording; verified
merge facts only)

Exactly five surfaces, minimal edits:

- (a) `oap/INCREMENTS.md` 078/8 row -> "Accepted and merged in PR #88
  at `ddd1559f021762316f5a64989a307355acb4aab2` on 2026-09-19; 078/8
  is closed" (exact facts re-verified against GitHub at activation).
- (b) `oap/INCREMENTS.md` `Next` row -> the standard in-flight form
  for `078-9-a` ("Opened at `078-9-a` from verified remote main
  `<base SHA>`; PR pending; strategy owns acceptance and merge") plus:
  "No further ordinary 078 product increments are planned. The
  078-bound catalog types (Gallery, LogoGrid, DocumentList, real
  Image) are 079 increments per the human directive of 2026-09-20.
  Numeric 078 remains PARTIAL until they are implemented and proven;
  reclassification to COMPLETE occurs only after independent
  verification of the resulting evidence."
- (c) `README.md` capability row: replace "increment 078/8 (bounded
  embed family) is opened at `078-8-a` (PR #88)" with the merged
  wording (exact verified facts); keep the GitHub-authoritative
  sentence.
- (d) `oap/MVP-PROGRESS.md`: sequence sentence and 078 status row —
  replace the 078/8 "opened at `078-8-a` (PR #88)" clause with the
  merged wording; 078 status stays PARTIAL with the 079-bound-
  remainder clause.
- (e) `oap/MVP-CONTRACT-AUDIT.md` and `CRITICAL.md`: verify-only
  (no embed-layer claims currently present); edit only if a stale
  current-state claim is actually found (durable wording).
- Durable-wording rule per 079/1 R9: no live-state claims outside the
  standard in-flight row form; the merge-fact consistency checker must
  stay green; the next merge must not make committed truth false.

### R5 - Governance hygiene: retire the inert preplanned 079-a file

- `git mv oap/orders/079-a-agent-media-semantics.md oap/governance/
  superseded-preplanned/079-a-agent-media-semantics.md` (content byte-
  identical; the move IS the supersession marker — do not edit the
  file's content).
- New `oap/governance/superseded-preplanned/README.md` (short): why
  the file moved (unique order-identifier-per-file enforcement in
  `tools/check_repository.py`; the next activation is `079-a` per the
  human directive of 2026-09-20, D2; this preplanned content is
  superseded by the 079 order to be published when `079-a` is
  activated) and that the other preplanned orders (080-a..091-a)
  remain inert in `oap/orders/`.
- Do not touch `080-a`..`091-a` or any other inert preplanned file.

### R6 - Hard constraints

No new dependency; no supply-chain/workflow/lockfile changes; no new
route/port/scope; no Alembic migration; no CSP change; no provider
keys or secrets in the diff or report; no Dependabot PR work.

## 7. Acceptance criteria (observable)

1. The three-value allowlist present in all three product surfaces;
   all generated artifacts regenerated; generator `--check` zero-diff;
   all four count pins verified unchanged (29).
2. Old values `cycle` / `transport` rejected fail-closed on the Agent
   and Editor paths (exact bounded rejection semantics; unit
   negatives).
3. No-persistence proof recorded (repo grep + Compose runtime scan,
   expected 0; disclosed).
4. Hermetic unit + renderer + E2E suites green with the corrected
   values and exact pins.
5. Live provider spec actually executed in the real environment: all
   three layers show layer-specific upstream requests; the `cycle`
   negative control shows the mapnik fallback; screenshot evidence
   present in the report — or PARTIAL/BLOCKED with same-host probe
   output.
6. OpenAPI strip-identity proven (sha256 both sides); 45 paths
   unchanged; drift gate green.
7. All R4 surfaces updated with durable wording; the merge-fact
   checker green; adversarial sweep for "PR pending" / "opened at
   `078-8-a`" 078/8 claims returns nothing.
8. The `079-a` file moved byte-identical; the repository checker green
   (orders-directory uniqueness; active exactly one order); the
   governance note present.
9. No R6 constraint violated (lockfiles byte-identical, no gate
   changes, no new route/scope/migration/dependency).
10. CI: all 20 required checks successful on the exact report-only
    head (strategy verifies independently).

## 8. Verification and workflow

- Local authority as usual (packages, browsers, databases, services,
  tests, CI logs are yours).
- GitHub: create branch + PR from verified `main`; push every commit;
  on completion commit the activated order, `oap/active` (=
  `078-9-a`), and the report to the PR branch WITHOUT changing
  strategic-owned order/active content; the report publication commit
  is report-only with `Report publication commit: SELF`; its parent is
  the literal implementation-head SHA.
- Do not merge; strategy is the only merger.
- Flake policy per Section 2 (one documented unmodified re-run,
  documented flake class only).

## 9. Report requirements

`oap/reports/078-9-a-osm-layer-contract.md`: work-order file + sha256,
`oap/active` bytes, PR/branch/head SHAs (base, start, implementation
head, SELF), per-requirement evidence (R1-R6) with exact command
outputs, the live provider evidence (observed request list per layer,
the negative-control observation, screenshot paths, and the
executor's own fresh provider probes), the OpenAPI strip-identity
proof (sha256 both sides), honest status (COMPLETE only if every
requirement's named evidence actually ran — otherwise PARTIAL/BLOCKED
with the exact gap), cumulative base->head size table grouped per
2026-09-14 review-unit governance Section 2 (base = the verified main
SHA at activation), predeclared-budget check, safety/scope
confirmations, and the exact CI state at the implementation head.

## 10. Predeclared review budget (2026-09-14 review-unit governance
Section 1)

- Production/config: at most 4 files (`bounded_embed.py`;
  `components.tsx`; `component_catalog.py`; in-place `060_001`
  regeneration).
- Migrations: 0.
- Tests/evidence: at most 4 files (`test_bounded_embed.py`; the
  renderer behavior test file; `preview.spec.ts`; new
  `live-osm-provider.spec.ts`).
- Generated artifacts: at most 4 (catalog-v1.json x2, agent-v1.json,
  in-place 060_001).
- Docs: at most 4 files (INCREMENTS, README, MVP-PROGRESS, new
  `oap/governance/superseded-preplanned/README.md`; MVP-CONTRACT-
  AUDIT/CRITICAL only if R4(e) finds a stale claim).
- OAP transcript: order + active + report.
- Substantive implementation-line scale: at most 600.
- Fresh single-family maintenance PR; the ~20-30 file / several-
  thousand-line threshold remains a REVIEW TRIGGER, not a quota;
  CLOSURE_ONLY per Section 3 of the amendment if the trigger is
  crossed or a completion claim is rejected.

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

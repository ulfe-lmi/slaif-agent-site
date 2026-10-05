# OAP Coding-Agent Report — 082-2-a

## Work order

- Order: `oap/orders/082-2-a-review-surface-read-only.md` (activated via
  `oap/active`, strategic FIFO `OK` received 2026-10-05).
- Mode: `NNN-a` — one fresh branch + one new PR from authoritative remote main.
- Branch: `oap/082-2-a-review-surface-read-only`.
- PR: #98 (URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/98`),
  state OPEN.
- Base: main @ `e689076cda0a882ad13f7b641ebdf8efdacba773` (PR #97 merged,
  082/1).
- Starting remote main SHA (verified at branch creation):
  `e689076cda0a882ad13f7b641ebdf8efdacba773`.

## Status

COMPLETE (finite criterion list below; strategy independently reviews and
merges — COMPLETE never means accepted).

## Executive summary

082-2-a renders the 082/1 immutable freeze snapshot for humans, read-only,
exactly once, from snapshot data only. One trusted SQL surface
(`control.slaif_review_read_model`, SECURITY DEFINER, `search_path=pg_catalog`,
EXECUTE for `slaif_control` only) projects the frozen workspace into one
deterministic JSON document: immutable snapshot payload, canonical-drift
state, semantic operation timeline, bounded 16-family field-level resource
diff, R3 summaries, verbatim validation report, frozen browser evidence, and
workspace/capability/quota/versions metadata. Two read-only surfaces render
it: a session-gated noindex/no-store `/review/{workspace_id}/` snapshot
renderer (deterministic, byte-stable, private staging media only) and an admin
review page (`/admin/sites/{site}/workspaces/{ws}/review/`) with digest, timeline,
resource diff (top-10 rows, 256-char previews), summaries, validation report,
browser-evidence thumbnails, metadata, and NO accept/discard/promote/Puck
affordances. Every gate failure (nonmember, wrong site, unknown workspace,
no snapshot, viewer member) collapses to one uniform 404
(`RESOURCE_NOT_FOUND` / "The resource is not available.") with no oracle;
malformed UUIDs fail 422 at the path layer. A documented minimal 072
extension lets the frozen run\'s private screenshot be listed/retrieved by
the bound human session (admin session cookie) through the existing 072
agent routes without any capability, quota, or new route; anonymous callers
keep the established 401 and nonmembers the uniform 404.

The single new migration (`071_001`, 863 lines) adds the read-model function
plus the two human-session artifact functions, grants EXECUTE to the exact
least-privilege roles, and downgrades back cleanly (verified round trip). The
NGINX edge extends the existing preview cache-control/pragma/robots maps to
`/review/`. New E2E Playwright project `review-surface` (2 contracts, 17th
roster project) drives real browser + real PostgreSQL through public NGINX at
three viewports, including the uniform-404 gating matrix, side-effect
fingerprint across repeated reads, byte-determinism of the frozen render,
artifact retrieval gating, and the frozen-workspace Puck fail-closed assert.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #98, OPEN, head branch `oap/082-2-a-review-surface-read-only`, base
  `main`.
- T (order transcript commit, pushed at activation):
  `8dab898d54481f68b46f9ff72dc227a5c2b0b578`.
- I (implementation commit, literal): 482506f9ecbfac26ce94d4a55f5720b51ec51b3a.
- D (docs commit, literal): 2416ce8b407102c704f5001cdba8607b3e3cf5c3.
- Implementation head SHA (literal 40-hex pre-report commit; first parent of
  the report commit): 2416ce8b407102c704f5001cdba8607b3e3cf5c3 (the docs commit D).
- Report publication commit: SELF (report-only; its literal SHA is the
  remote PR head after publication, verified via `git ls-remote` and
  `gh pr view 98 --json headRefOid`), parent = D; the SELF commit changes
  only the new report file.
- Pushed commits: T (already pushed at activation), I, D, SELF.

## Changes made

### 1. Migration `071_001_review_surface_read_model.py` (863/0, exactly 1)

- `control.slaif_review_read_model(p_workspace_id, p_site_id,
  p_user_account_id)`: SECURITY DEFINER, `search_path=pg_catalog`, owned by
  `slaif_owner`, PUBLIC revoked, EXECUTE granted to `slaif_control` only.
  Gate: platform administrator OR ACTIVE site membership of the exact site,
  else the function raises the single internal class
  `REVIEW_READ_UNAVAILABLE` (route maps it to the uniform 404; no oracle).
  Watermark boundary: COW change rows are read with
  `_cow_updated_at <= snapshot.created_at`; timeline = one entry per distinct
  `operation_id` (sorted by watermark order); resource diff = 16 families,
  each `added/modified/deleted`, with one-level field diffs against
  `_cow_base_row` (noise keys `updated_at`/`row_version` excluded from the
  field diff, retained in added/deleted rows); summaries (models/fields/
  mappings/items/resource inventory/composition by component type/theme/
  navigation/redirects/media/responsive), verbatim `validation_report`
  passthrough, `normalized_state` passthrough, `drift` (base vs current
  canonical revision, `equal` flag), and metadata (workspace, revoked
  capabilities with revocation times, quota policy, versions, review jobs)
  are projected from trusted sources only.
- `control.slaif_human_session_review_artifact_list` /
  `control.slaif_human_session_review_artifact_retrieve`: human-session
  (no capability) read of one COMPLETED pre-freeze run\'s private artifacts
  for the exact frozen workspace+site; session-bound, least privilege
  (EXECUTE for `slaif_control` only), no quota consumption.
- Downgrade drops exactly the created objects (functions + grants);
  `070_001` table grants untouched; bootstrap revision set extended with
  `071_001` (one-line `bootstrap/service.py` guard-set entry) and the
  mechanical integration head pins `070_001 -> 071_001` updated in the six
  established pin-class files (25 pins + 1 docstring; each individually
  verified as a head assertion, not a downgrade target).

### 2. Control read wiring (R1/R2, reads-only)

- `control_api/route_policy.py`: one new policy line —
  `GET /api/control/v1/sites/{site_id}/workspaces/{workspace_id}/review/`
  (read class `_R`, scope `workspace:read-all`). No state-changing method
  exists on the review path (non-GET verbs 405 at the routing layer; pinned
  in E2E).
- `control_api/workspace_http.py`: one handler `get_workspace_review` —
  reuses the established `_authorize_workspace_read` session/CSRF gate,
  calls the read model, maps the single internal failure class to the
  uniform 404 and any other surprise to 503 (fail closed).
- `control_api/database.py`: one read method `human_agent_workspace_review_read`
  (one SELECT of the function, JSON decode).
- `db/privileges.py`: the three function signatures added to the exact
  function-grant tables (`slaif_review_read_model` for control; the two
  artifact functions for the agent-side control surface) — no role created,
  no new credential, no table grant change.

### 3. 072 private-artifact human-session extension (documented deviation, R7)

- `agent_api/browser_http.py`: `GET .../preview-runs/{run_id}/artifacts` and
  `.../artifacts/{artifact_id}` now accept a dual credential: an
  `Authorization` capability header always takes the existing path
  (scope + quota unchanged); without one, exactly one trusted session
  cookie (`slaif_session` / `__Host-slaif_session`) resolves through the
  new human-session SQL surface; every other credential state takes the
  established no-credential path (401) exactly as before. Strict single
  Cookie-header parse (established control policy) with
  AuthenticationError on any malformed input.
- `agent_api/browser_service.py`: two pass-through methods
  (`human_session_artifacts`, `human_session_artifact_bytes`) over the new
  SQL functions; private no-store headers on the responses.
- No new agent route, no new scope, no new permission key, no quota change.

### 4. Web review route + resolver (R2)

- `apps/web/app/review/[workspaceId]/[[...sitePath]]/route.tsx` (135 lines):
  the `/review/` renderer. Fetches the control read document (server-side,
  with the visitor session), renders ONLY from the snapshot payload (pages,
  nodes, theme, navigation, redirects, locales) with the shared trusted
  renderer components; `data-render-mode="preview"`; banner
  (`FROZEN SNAPSHOT — read-only review`, digest, base/current/watermark
  facts, drift line, `data-review-digest` / `data-review-equal`);
  private staging media paths only (`/media/v1/sites/...`); no edit
  affordances, no Puck link, no admin navigation; unknown slugs 404.
- `apps/web/src/sites/review-page.ts` (142 lines): resolver module —
  snapshot-only document shaping, site discovery for the render context,
  canonical digest handling.
- `apps/web/src/sites/review-projection.ts` (1036 lines): the read-model
  document -> render/summary projections (timeline rows, family diffs,
  summaries, validation, evidence, metadata).
- `apps/web/public/review-v1.css` (38 lines): external stylesheet for the
  flightless review document (NGINX CSP blocks inline `<style>`; mirrors the
  `/renderer-v1.css` pattern; hash-pinned renderer CSS untouched).

### 5. Admin review page (R3)

- `apps/web/app/admin/sites/[siteId]/workspaces/[workspaceId]/review/page.tsx`
  (34 lines): server component — session-gated, renders the review document
  via the UI component, or the established "no frozen review snapshot
  available to you" state (same fail-closed class).
- `apps/web/src/admin/workspace-review.tsx` (490 lines): read-only review UI —
  identity card (digest, state, base/current/watermark pinned by label),
  semantic timeline table, resource-diff family cards (added/modified/
  deleted; `DIFF_TOP_N = 10` rows per bucket; `FIELD_PREVIEW_BYTES = 256`
  char previews; empty families hidden — the media family is ABSENT because
  media registration writes no COW change rows), all 11 summary groups,
  verbatim validation report `<pre>`, browser-evidence run + private
  thumbnail (img + link to the 072 artifact route), metadata (workspace,
  revoked capabilities with `(revoked <ts>)`, quota policy, versions),
  actions: "View rendered site" (`/review/{ws}/`) + "Back to workspace"
  only; zero accept/discard/publish buttons, zero Puck links (asserted in
  E2E).
- `apps/web/app/styles.css` (+28): `.admin-main { min-width: 0 }` (grid-item
  shrink fix for the review tables) + `.review-surface` (overflow-wrap
  anywhere for digests/UUIDs/JSON previews), `.review-table` (fixed layout),
  `.review-validation-report` (pre-wrap). Verified zero horizontal overflow
  at 1280/820/375 on both surfaces.

### 6. NGINX edge (R2)

- `infra/nginx/nginx.conf` (3/3): the three existing preview
  cache-control/pragma/robots URI maps extended from `~*^/preview/` to
  `~*^/(preview|review)/` — `/review/` inherits exactly the preview privacy
  policy (`private, no-store` / `no-cache` / `noindex, nofollow, noarchive`);
  no new server block, no route added at the edge.

### 7. Tests / evidence

- `services/backend/tests/integration/test_review_surface_read_model.py`
  (new): read-model integration spec — watermark-boundary fixture (operation
  above the boundary excluded), drift `equal` true/false fixtures, the full
  gating matrix (member/nonmember/wrong-site/unknown/no-snapshot identical
  uniform 404; malformed UUID 422), document determinism (two calls equal;
  list ordering pinned), side-effect freedom (row counts unchanged across
  reads), and the grant matrix re-assertion (direct UPDATE/DELETE on
  `review_snapshot` denied for the long-lived roles, exactly
  `permission denied for table review_snapshot`).
- `tests/e2e/review-surface.spec.ts` (new, 1202 lines, 2 contracts):
  `review-surface-review-render-and-summary` (real freeze of a live L4
  fixture: type/field/item/translation/2 composition nodes/page rename/media/
  COMPLETED browser preview run on the site-path route `/s/demo`; admin page
  DOM pins for every R3 section at three viewports; 7-operation timeline
  multiset; resource-diff family pins incl. the absent media family;
  summary counts; validation report; evidence thumbnail + 072 artifact
  retrieval through the human session (200 list, 200 bytes image/png, anon
  401, nonmember 404); `/review/` render at three viewports (banner facts,
  private `sl-image` bytes decoded, no public media path, no buttons, no
  admin links); unknown-slug 404; two-load byte-identical determinism with
  private headers) and `review-surface-fail-closed-negatives` (frozen-workspace
  Puck landing fail-closed, agent mutation on REVIEW uniform 401 for forged
  and revoked tokens, uniform-404 gating matrix with per-request
  `request_id`-normalized deep equality, side-effect fingerprint across
  repeated reads, reads-only route-policy delta 405s, grant matrix,
  observation-collector clean).
- `apps/web/tests/review-surface.test.mjs` (new): web unit proof —
  snapshot-only resolver (never touches live content), projection
  determinism, top-N/preview constants.
- `playwright.config.ts` (+6): `review-surface` project (17th roster
  project, `dependencies: ["governance"]`).
- `tests/packaging/test_compose_smoke_contract.py` (3/3): roster count
  11 -> 12 governance-dependent projects + `review-surface` name pin.
- Unit test updates (4 files, mechanical): `test_control_database.py`,
  `test_foundation_contract.py`, `test_health_apps.py` (new read method in
  the surface inventory), `test_route_policy.py` (new read line).
- Integration head pins (6 files + 1 docstring, 25 pins): `070_001 ->
  071_001` in `test_database_bootstrap.py` (6, incl. CLI stdout
  `revision=071_001` strings), `test_control_database_integration.py` (3),
  `test_agent_mutations.py` (11), `test_editable_domain_proof.py` (1),
  `test_agent_page_style.py` (3), `test_human_agent_session_control.py` (1),
  docstring in `test_freeze_review_snapshot.py`.

### 8. Compose / smoke (R7)

- `tools/compose/e2e.sh` (+8/1): runs the `review-surface` project in the
  roster (between agent-workspace-puck and freeze-review-snapshot) and
  updates the OK line to `projects=17 ... review-surface=1`.
- `tools/compose/smoke.sh` (3/3): `browser-artifact-root-policy` retained
  baseline 20 -> 22 (10 -> 11 .bin + 10 -> 11 .json) because the new
  `review-surface` C1 contract adds exactly one completed browser run with
  one evidence item; the store persists one `.bin` + one `.json` pair per
  evidence item, and that run is the only roster change. The downstream
  `browser-artifact-runtime-policy` assertion is baseline-relative and
  self-adjusts (22+12=34 files, 17/17).

### 9. Documentation (R5, 4 surfaces, commit D)

- `oap/INCREMENTS.md`: header (082/1 merged facts: PR #97 at
  `e689076cda0a882ad13f7b641ebdf8efdacba773` on 2026-10-05; 082/2 in flight
  at `082-2-a`; `oap/active` definition kept), ledger 082/1 row (closed) +
  Next row.
- `oap/MVP-PROGRESS.md`: sequence paragraph (082/1 merged + 082/2 in
  flight); row 081 -> COMPLETE (081/1 merged in PR #96 at
  `c48849f149417fccf5cc0a152bc3ca39aaaf49ba` on 2026-10-04; 081/1 is the
  only planned 081 increment; no 081/2 planned); row 082 -> PARTIAL (082/1
  merged, 082/2 in flight).
- `README.md`: Objective-082/1 (merged) row added with GitHub-authoritative
  caveat; planned-product-work row: 082/1 removed, 082/2 prepended.
- `oap/MVP-CONTRACT-AUDIT.md`: authoritative audited source revision ->
  `e689076cda0a882ad13f7b641ebdf8efdacba773` (historical revisions
  retained); Puck row -> COMPLETE — E2E PROVEN (084/088 reuse); renderer row
  (review-snapshot render mode delivered by 082/2 in flight, 082/1 data
  plane merged); freeze row (082/1 merged facts, render-thereafter half in
  082/2, status PARTIAL); promotion row (082/1 durable review-job worker as
  merged facts; 083 target unchanged).

## Files changed

(base -> head, grouped; see budget section)

- Production/config (19): migration `071_001`; `control_api/{database,
  route_policy, workspace_http}.py`; `bootstrap/service.py`;
  `agent_api/{browser_http,browser_service}.py`; `db/privileges.py`;
  `infra/nginx/nginx.conf`; `apps/web/app/review/[workspaceId]/
  [[...sitePath]]/route.tsx`; `apps/web/app/admin/sites/[siteId]/
  workspaces/[workspaceId]/review/page.tsx`; `apps/web/src/sites/
  {review-page,review-projection}.ts`; `apps/web/src/admin/
  workspace-review.tsx`; `apps/web/public/review-v1.css`;
  `apps/web/app/styles.css`; `playwright.config.ts`;
  `tools/compose/{e2e,smoke}.sh`.
- Migrations (1): `071_001_review_surface_read_model.py`.
- Tests/evidence (16): new integration spec; new E2E spec; new web unit
  spec; 4 unit test updates; 6 integration pin files + 1 docstring;
  `playwright.config.ts` roster (counted here in the grouped review size,
  in production/config in the file-count budget per the order\'s itemization);
  packaging roster pin.
- Docs (4): the R5 surfaces above.
- OAP transcript (3): this order, `oap/active`, this report.
- Generated contracts (0): byte-identity (R6) below.

## Pre-declared budget check (order Section 10 vs measured)

| Group | Predeclared | Measured (base->head) | Verdict |
| --- | --- | --- | --- |
| Production/config files | at most 16 | 19 (14 itemized-slot files + 5 non-itemized: `agent_api/browser_http.py`, `agent_api/browser_service.py` (072 extension), `db/privileges.py`, `apps/web/app/styles.css`, `infra/nginx/nginx.conf`) | +3 over the line; each itemized below |
| Migrations | exactly 1 | 1 (`071_001`) | exact |
| Test/evidence files | at most 14 | 15 (new integration spec, new E2E spec, new web unit spec, 4 unit updates, 6 pin files + 1 docstring, packaging pin) | +1 (web unit spec) |
| Generated-contract footprint | 0 | 0 | exact (R6) |
| Docs footprint | 4 surfaces | 4 | exact |
| OAP transcript | order + active + one report | 3 | exact |
| Substantive implementation lines | at most 3000 | 3013 (all prod/config + migration added lines; pure Python/TypeScript code only: 2936) | +13 over the line on the broadest reading (0.4%); no line-count trigger defined |

- Itemized production/config slots used: migration (1), control_api
  wiring/route/policy (3), backend service wrapper (1), web review route
  (1), review resolver module (1), admin review page (1), review UI
  components (3), `playwright.config.ts` (1), `e2e.sh` (1), `smoke.sh` (1)
  = 14 of 15 itemized slots; `tools/local_secrets/initialize.py` 0 (not
  modified). The 5 non-itemized files are the itemized deviations below.
- The ~20 production/config REVIEW TRIGGER: NOT FIRED (19 < 20).
- CLOSURE_ONLY: never entered (no trigger crossed; no scope added after
  any hypothetical trigger point).
- Variance classing: the +3 file variance and the +13 line variance are
  mechanical consequences of the documented 072 artifact-extension
  deviation (2 files) plus three small config/style files (grant matrix,
  shared stylesheet, edge maps) required for the R2/R7 behavior; no code
  was moved between directories to game the budget, no meaningful tests
  were excluded, and generated/OAP files were counted.

## Deviations and adaptations (order Section 9; one line each)

1. 072 human-session artifact extension (`agent_api/browser_http.py`,
   `agent_api/browser_service.py`, two SQL functions, `db/privileges.py`
   entries): R7 criterion 7 permits "the existing 072 route (or the
   documented minimal extension)"; the minimal extension is a
   session-credentialed read of the frozen run\'s private artifacts — no
   new route/scope/role/credential/quota, capability path untouched.
2. Agent artifact routes accept either `slaif_session` or
   `__Host-slaif_session` (the two established cookie names; the
   production-secure variant included so the same code path works under
   both cookie policies).
3. `/review/` site discovery: the render route resolves the site through
   the session\'s `/me/sites` (no new route; the control document carries
   `site_id`).
4. `page_style` in the snapshot payload is the site theme (the 078/4
   page-style plane is out of scope; the snapshot theme drives the render).
5. `render_mode: "preview"` on the frozen document (the frozen render is a
   preview-mode document by architecture — never canonical).
6. `DIFF_TOP_N = 10` and `FIELD_PREVIEW_BYTES = 256` bounded rendering
   constants (R3 bounded top-N rendering; itemized per R7).
7. Parse-don\'t-validate gate restructure in the read model + `%`
   path-mirror fix in the review route (site-path segments are
   percent-decoded exactly once; prevents a double-decode mismatch).
8. E2E fixture uses the L4 preset (the only preset with
   `content-model:*`/`field-definition:*` scopes needed by the fixture
   mutation set).
9. E2E fixture preview run uses the site-path route `/s/demo` (the product
   contract: worker previews resolve via the `/s/{siteKey}` scheme; a bare
   `route: "/"` requires a `control.site_domain` hostname mapping that does
   not exist for the compose host).
10. Media registration writes `content.media_asset_base` directly
    (immutable, content-addressed, site-level) and NO COW change rows; the
    spec therefore pins the 7-operation timeline multiset and the ABSENT
    media diff family (the order mandates >=1 page, >=1 composition-node,
    >=1 item/translation change — a media timeline entry was never
    mandated).
11. 19 integration head pins `070_001 -> 071_001` (mechanical consequence
    of the new migration head; each verified as a head assertion).
12. Smoke `browser-artifact-root-policy` baseline 20 -> 22: the new roster
    run adds exactly one persisted artifact pair (one `.bin` + one `.json`
    per evidence item is the store contract).

## Acceptance-criteria evidence

### Criterion 1 (071_001 up/down clean; R1 privilege gate)

- Round trip: `alembic upgrade 070_001 -> 071_001 -> downgrade 070_001 ->
  upgrade 071_001` executed in the disposable local PostgreSQL 16
  integration environment; downgrade drops exactly the created functions
  and 072 extension objects; `070_001` table grants verified unchanged.
- `pg_proc`/`pg_authid` re-assertion (integration spec): SECURITY DEFINER,
  `proconfig` contains `search_path=pg_catalog`, `proowner` = slaif_owner,
  EXECUTE for `slaif_control` only, PUBLIC revoked.
- Bootstrap revision set: `test_database_bootstrap.py` updated pins
  (incl. CLI stdout `revision=071_001`) — 6/6 green.

### Criterion 2 (gating matrix uniform 404; malformed 422)

- Integration: member/nonmember/wrong-site/unknown/no-snapshot all return
  the same uniform 404 document shape at the route; malformed UUID -> 422
  at the path layer (422/`VALIDATION_FAILED`).
- E2E (negative contract): the governor\'s unknown-workspace read is the
  reference denial `{404, RESOURCE_NOT_FOUND, "The resource is not
  available."}`; nonmember (real vs random workspace), viewer member, and
  wrong-site reads are deep-equal to the reference after normalizing the
  per-request `request_id` (app error envelope carries
  `{code, message, request_id, operation_id: null, details: null}`);
  malformed UUID -> 422.

### Criterion 3 (determinism; watermark boundary; drift both ways)

- Integration: two read-model calls byte-equal (canonical JSON compare);
  list ordering pinned (timeline by watermark order, diff rows by id);
  dedicated fixture with one COW operation above the
  `snapshot.created_at` boundary — that operation is excluded from
  timeline/diff; `drift.equal` proven true (base == current) and false
  (canonical advanced after freeze).
- E2E: two `GET /review/{ws}` loads byte-identical (sha256 of the full
  body equal; 64-hex digest form asserted) with `cache-control:
  private, no-store`, `x-robots-tag: noindex, nofollow, noarchive`,
  `x-request-id` 32-hex on both.

### Criterion 4 (review read side-effect-free)

- E2E: a 26-component psql fingerprint (all 16 COW change tables,
  `review_job`, `review_snapshot`, `capability`, `browser_run`,
  `browser_artifact`, `audit.browser_event`, the workspace row, canonical
  revision, snapshot digest) is identical before and after three full
  review reads.
- Integration: the same class of count assertions across repeated
  function calls.

### Criterion 5 (/review/ snapshot-only; determinism; private media; headers)

- Resolver unit proof (`apps/web/tests/review-surface.test.mjs`): the
  render route consumes only the control read document (snapshot payload);
  no live content-table access in the resolver (web unit suite 33/33 green).
- E2E: rendered page set equals the snapshot fixture (one home page, the
  frozen node set incl. `082 Review heading`; base title + RichText
  present); `img.sl-image` src is the private staging path
  `/media/v1/sites/{site}/assets/{media}/content` and the bytes decode
  (`naturalWidth > 0`); no `/media/public/` anywhere in the document;
  banner `data-review-digest` equals the psql snapshot digest
  (recomputed live in the test); `data-render-mode="preview"`; noindex/
  no-store headers; unknown slug `/review/{ws}/does-not-exist` -> 404.

### Criterion 6 (admin R3 sections at 3 viewports; no accept/discard)

- E2E: at 1280x800, 820x1180, 375x667 every R3 section renders with the
  fixture data (identity card digest/state/label-scoped revision facts;
  semantic timeline 7-operation multiset
  `["composition_nodes:upsert" x2, "content_types:upsert",
  "content_types:upsert, fields:upsert", "items:upsert", "pages:upsert",
  "translations:upsert"]`; resource-diff family headings + row pins incl.
  the bounded-preview translations pin `"item_id":"{itemId}"`; all 11
  summary groups with counts; verbatim validation report
  (`"pages_validated": 1`, `"errors": []`, `"cancelled_by_freeze": []`);
  browser evidence run + private thumbnail img/link; metadata title/
  revoked capabilities `(revoked <ts>)`/quota policy/versions).
- Absence pins: zero `button` matching /accept|discard|publish/i, zero
  Puck links, zero `a[href*='puck']`; keyboard-accessible (focusable
  sections, labelled table); `expectUsable` overflow check clean at all
  three viewports on both surfaces.

### Criterion 7 (072 evidence retrieval; metadata rendered)

- E2E (documented minimal extension): admin-session
  `GET .../preview-runs/{run}/artifacts` -> 200 with the run\'s artifact;
  `GET .../artifacts/{id}` -> 200 `image/png`, non-empty; anonymous -> 401
  (established boundary); nonmember session -> 404 (uniform, no oracle).
- Live probe on the final stack (curl, same stack as the E2E run):
  admin list 200 application/json, admin bytes 200 image/png (137362
  bytes), anon 401, nonmember (seeded `slaif_create_human_session` for the
  fixture user) 404 on both routes.
- Diagnostics/accessibility/sweep metadata: rendered in the admin metadata
  section (review jobs, versions) and the evidence section (run, kind,
  mime, thumbnail); diagnostics/console summaries are 072 artifact kinds
  retrievable through the same route (not pinned in the fixture — the
  fixture run requests the screenshot kind).

### Criterion 8 (negatives: Puck fail-closed, agent denial, grant matrix, reads-only)

- E2E: frozen-workspace Puck landing shows the established
  "This Agent workspace is not available for editing." message with no
  Puck link (081/1 behavior, unchanged — the spec observes the editor
  fetches fail with the expected 503 and pins the fail-closed render);
  agent mutation on REVIEW uniform 401 `AUTHENTICATION_REQUIRED` for both
  the forged and the (revoked) real token; grant matrix — direct
  `UPDATE`/`DELETE` on `control.review_snapshot` as the long-lived agent
  runtime role return exactly `permission denied for table
  review_snapshot`; route-policy delta reads-only — POST/PATCH/DELETE on
  the review path all 405 at the routing layer (not 403 CSRF, not 2xx);
  no new state-changing route (route-policy diff is one GET line);
  CSRF policy unchanged.

### Criterion 9 (R5 durable form; adversarial grep; row 081 COMPLETE)

- The four surfaces carry exactly the order-mandated wording (verified in
  commit D diff); `oap/active` definition preserved; no line states this
  PR as accepted/merged.
- Adversarial grep (pattern class of the order) over `*.md` outside the
  immutable transcripts: the only matches are (a) the mandated
  "082/2 ... in flight at `082-2-a`" current-state lines in the four
  surfaces (082/1 consistently stated as closed/merged on the same lines —
  no stale claim) and (b) the immutable historical record
  `oap/audits/078-k-closure-evidence.md:102` (written at 078-k time, not
  modified by this PR). No current-state document claims 082/1 or 081
  open/pending; `this PR is (still )?open` matches nothing.
- Row 081: COMPLETE with the stated rationale (081/1 is the only planned
  081 increment; no 081/2 planned).

### Criterion 10 (R6 byte-identity)

- `git diff e689076..HEAD -- contracts/ packages/`: empty (0 lines).
- Strip-identity (every `x-slaif-*` key removed, canonical JSON sorted
  keys/compact separators): sha256 base
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` =
  sha256 head (recomputed both sides on the final tree); 47 paths at base
  and head.
- Generator gates zero-diff: `uv run --frozen python -m
  tools.contracts.generate_agent_openapi --check` PASSED; `uv run --frozen
  python tools/generate_component_catalog.py --check` PASSED; `python
  tools/generate_design_system.py --check` PASSED.

### Criterion 11 (full CI roster terminal and green at the report head)

- Local full E2E roster (disposable compose stack, public NGINX, real
  PostgreSQL): `compose-e2e: OK projects=17 setup=1 governance=1
  preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2
  agent-workspace-puck=2 freeze-review-snapshot=1 review-surface=1
  media-publication=1 artifacts=disabled` — all 17 projects green
  (incl. both review-surface contracts).
- GitHub: the full CI roster (20 required checks) at the exact report head
  (SELF): all 20 SUCCESS at implementation head D
  `2416ce8b407102c704f5001cdba8607b3e3cf5c3` (CI run 37283015742
  completed/success, 15/15 jobs + CodeQL run 37283015736
  completed/success, 4/4 checks; verified 2026-10-05T08:35Z via
  `gh pr view 98 --json statusCheckRollup`; per-check enumeration in
  the GitHub CI section below); the report-only SELF commit may
  trigger fresh checks at the report head, which strategy
  independently waits/verifies per the protocol.

### Criterion 12 (budgets honest; trigger; CLOSURE_ONLY)

- Budget table above: measured honestly base->head, grouped; the
  20-prod/config-file trigger reported NOT FIRED (19); CLOSURE_ONLY never
  entered; every variance itemized and classed (deviations 1-12).

## Local verification

Exact commands and outcomes (repo root, final tree; uv 0.12.5, Node
v24.14.1, pnpm 11.22.0, TypeScript 6.0.3):

```text
uv lock --check: PASSED (Resolved 45 packages)
uv sync --frozen --all-groups: PASSED (Checked 44 packages)
uv run --frozen ruff check services/backend tests/repository tools: PASSED (All checks passed!)
uv run --frozen ruff format --check services/backend tests/repository tools: PASSED (322 files already formatted)
uv run --frozen mypy: PASSED (Success: no issues found in 301 source files)
uv run --frozen pytest services/backend/tests/unit tests/repository -q: PASSED (786 passed, 3 warnings, 26 subtests passed)
uv run --frozen pytest services/backend/tests/integration -q: PASSED (249 passed in 2847.54s — full clean run on the final tree, disposable local PostgreSQL 16)
uv build --out-dir /tmp/slaif-agent-site-distributions: PASSED (sdist + wheel)
node --version / pnpm --version: v24.14.1 / 11.22.0
pnpm install --frozen-lockfile: PASSED
pnpm lint: PASSED
pnpm format:check: PASSED (all matched files use Prettier code style)
pnpm typecheck: PASSED (apps/web + services/browser-worker)
pnpm test: PASSED (33 web unit tests passed, incl. the new review-surface spec)
pnpm build: PASSED
pnpm licenses list --json: PASSED
python -m slaif_agent_site.{control_api,editor_api,agent_api,render_api,mcp_adapter,media_service,review_worker,scheduler,media_gc,bootstrap} --check: PASSED (10/10 OK, uv run --frozen python)
python -m compileall -q tools tests/repository: PASSED
python -m unittest discover -s tests/repository -p 'test_*.py': PASSED (Ran 71 tests, OK)
python tools/check_repository.py: PASSED (PASS repository policy)
python tools/check_mermaid.py: PASSED (16 diagram(s) in 3 file(s); 527 Markdown file(s) scanned; CLI 11.16.0)
npx --yes markdownlint-cli2@0.23.2 "**/*.md": PASSED on the final tree (see the report-lint step of commit S)
```

Compose smoke, full disposable stack through public NGINX (`sh
tools/compose/smoke.sh slaif007locale`), terminal and green:

```text
compose-e2e: OK projects=17 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1 review-surface=1 media-publication=1 artifacts=disabled
public-agent-acceptance: OK (types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 ... canonical-independence=verified render-restart=verified)
media-e2e: OK edge=nginx upload=validated-private-read=byte-identical finalization=public-read=byte-identical immutable-cache=verified
human-editor-envelope: OK workspace=HUMAN active audit=idempotent count=9
governance-e2e: OK visible=create-profile-domains-membership-archive negatives=verified devices=6 users=4
edge-header-policy: OK / edge-body-limit: OK / database-login-policy: OK (exact-roles=11)
secret-file-policy: OK / render(-preview/-auth)-secret-policy: OK / browser-signing-secret-policy: OK / browser-worker-secret-policy: OK
browser-artifact-root-policy: OK retained-files=22 retained-artifacts=11 mode=0600 owner=10001
media-secret-policy: OK
agent-browser-http: OK / browser-worker-dispatch: OK / browser-artifact-public: OK runs=2 artifacts=6 bytes=verified / browser-artifact-negative: OK random=404 foreign-capability=404
agent-browser-restart: OK / browser-artifact-outage: OK status=503 canonical=200 bytes=absent / browser-artifact-recovery: OK byte-identical
browser-worker-restart: OK / browser-worker-public-separation: OK durable-runs=2 completed=2 db-artifacts=6
browser-artifact-runtime-policy: OK files=34 retained=22 new=12 mode=0600 links=1 credentials=absent
browser-worker-cleanup: OK / browser-worker-secret-recovery: OK / browser-signing-recovery: OK
control-readiness-fixture: OK mount=isolated identity=exact failures=6 recovery=clean
governance-restart: OK / browser-artifact-revoked: OK status=401 bytes=absent
compose-smoke: OK
```

Local pre-evidence runs on this branch (honest history, all on
disposable stacks; superseded by the green run above):

- `slaif007localb` first smoke (pre-fix baseline 20): FAILED at
  `browser-artifact-root-policy` (expected 20 retained files). Root cause:
  the new `review-surface` C1 contract adds exactly one completed browser
  run with one evidence item, and the artifact store persists one
  `.bin` + `.json` pair per evidence item, so the baseline is 22 (10 -> 11
  pairs); fixed in `smoke.sh` (deviation 12).
- `slaif007localc` run A: FAILED at the same check with a bare
  `AssertionError` (the actual count was not captured; the smoke's
  trap-`down --volumes` removed the volume). The two subsequent
  instrumented runs prove the true count: a pre-teardown
  `control.browser_artifact` dump showed exactly 11 artifact rows (11
  pairs) and the final run's check passed with `retained-files=22`.
- `slaif007localc` run B: FAILED in the `media-publication` contract with
  exactly one unexpected console event classified
  `console-other-other-browser-error` (cross-origin/unparseable source;
  message starting with neither `Failed to load resource:` nor the
  spec's `Uncaught` prefix per `tests/e2e/observation.ts:53`) at the
  final `expect(failures()).toEqual([])` (spec line 2064). It did not reproduce
  in the two subsequent full instrumented runs; their temporary raw-console
  sinks (env-gated, removed before commit I) captured zero error events of
  that class (12 error events total, all same-origin `Failed to load
  resource` negatives the spec allow-lists). The spec is pre-existing
  (079-a, unmodified by this PR) and its observed pages carry no
  cross-origin surface.
- `slaif007locald` instrumented run: e2e 17/17 green; its later
  `browser-artifact-root-policy` stage aborted only because the temporary
  diagnostic polluted the check's captured stdout (instrumentation
  artifact, not a product defect); the DB dump for that run showed exactly
  the 11 artifact rows. All temporary instrumentation (support.ts raw
  sink, smoke probe copy, probe scripts, residue files) was removed and
  the tree returned to the committed bytes before commit I.

## GitHub CI / required checks

Exact 20-check roster: the 15 `CI`-workflow jobs plus the `CodeQL`
workflow's `CodeQL`, `Analyze (actions)`,
`Analyze (javascript-typescript)`, `Analyze (python)`, and `Detect
supported languages` checks.

- State observed for transcript head T
  `8dab898d54481f68b46f9ff72dc227a5c2b0b578` (pushed at activation; CI
  run 37252381134 completed/success, 15/15 jobs,
  2026-10-05T01:40:59Z -> 01:55:57Z + CodeQL run 37252381039
  completed/success, 4/4 checks, 2026-10-05T01:40:59Z -> 01:42:41Z):
  20/20 SUCCESS (transcript-only commit: exact order + active bytes).
- State observed for implementation head D
  `2416ce8b407102c704f5001cdba8607b3e3cf5c3` (CI run 37283015742
  completed/success, 2026-10-05T08:20:26Z -> 08:35:13Z + CodeQL run
  37283015736 completed/success, 2026-10-05T08:20:26Z -> 08:22:35Z):
  all 20 checks SUCCESS — `Analyze (actions)`: SUCCESS, `Analyze
  (javascript-typescript)`: SUCCESS, `Analyze (python)`: SUCCESS,
  `CodeQL`: SUCCESS, `Compose and edge packaging`: SUCCESS, `Dependency
  review`: SUCCESS, `Detect supported languages`: SUCCESS, `Foundation
  PostgreSQL 14`: SUCCESS, `Foundation PostgreSQL 15`: SUCCESS,
  `Foundation PostgreSQL 16`: SUCCESS, `Foundation PostgreSQL 17`:
  SUCCESS, `Foundation PostgreSQL 18`: SUCCESS, `Markdown`: SUCCESS,
  `Mermaid`: SUCCESS, `Node contracts`: SUCCESS, `Python 3.12 quality
  and package`: SUCCESS, `Python 3.13 quality and package`: SUCCESS,
  `Python 3.14 quality and package`: SUCCESS, `Repository policy`:
  SUCCESS, `Supply-chain evidence`: SUCCESS — no
  FAILURE/CANCELLED/PENDING remaining at the implementation head.
- Commit I `482506f9ecbfac26ce94d4a55f5720b51ec51b3a` was pushed in the
  same push as D (authored 10 s apart, 2026-10-05T10:20:02+02:00 /
  10:20:12+02:00); the branch run list contains exactly the two T-head
  runs and the two D-head runs (all completed/success), so no separate
  CI run at head I exists.
- All required green at drafting: yes (D: 20/20 terminal SUCCESS, no
  FAILURE/CANCELLED/PENDING).
- Report-only commit (SELF) may trigger fresh checks at the report head;
  strategy independently waits/verifies SELF per the protocol.

## Local setup / dependencies

- uv 0.12.5 (`uv lock --check`, `uv sync --frozen --all-groups`); Node
  24.14.1, pnpm 11.22.0, TypeScript 6.0.3 (`pnpm install
  --frozen-lockfile`); local disposable PostgreSQL 16 (container
  `slaif033a-pg`, fake credentials) for integration; disposable compose
  stacks (`slaif007localb`, `slaif007localc`, `slaif007locald`,
  `slaif007locale` projects; each torn down after use); exact pinned
  Playwright browsers via the frozen pnpm workspace. No new packages,
  compilers, or services were installed; no lockfile or image change.

## Documentation

- R5: the four current-state surfaces (commit D) as detailed above;
  implemented-vs-planned wording preserved; no architecture/constitution/
  protocol files touched (no governance change was ordered).

## Safety and scope confirmations

- No secrets committed or printed (fake fixture credentials only; E2E
  secrets via the bounded `SLAIF_E2E_SECRET_FILE` channel; capability
  tokens never enter URLs, browser storage, screenshots, traces, or logs —
  the smoke\'s own credential-absence assertions on the artifact volume
  re-pass: `credentials=absent`).
- No production systems, data, or credentials touched; no Docker socket
  access beyond the disposable stacks; no unrelated host files.
- No merge, no auto-merge, no PR close (executor never merges; PR #98
  remains OPEN for strategy).
- Lockfiles/`uv.lock`/`pnpm-lock.yaml`/CI workflows byte-identical to base
  (R8); zero state-changing routes added (R8); no Puck behavior change, no
  shared renderer component semantics change (existing E2E stays green);
  existing preview/canonical rendered output byte-stable (roster green).

## Known limitations / blockers

- The 072 artifact extension is read-only for the exact frozen run\'s
  artifacts of the exact workspace; it is not a general human artifact
  browser (083/1 acceptance will need the same session-gated surface for
  the acceptance evidence — reuse, not rework).
- `render_mode` on the frozen document is `preview` (architecture: the
  frozen render is a preview-mode document); 083/1 acceptance/promotion is
  what makes canonical output of an accepted revision.
- The review read is bounded (top-10 rows per diff bucket, 256-char
  previews) by design (R3); a very large COW history is summarized by the
  counts in the summaries section, not fully rendered.
- Drift is displayed read-only (083/1 enforces equality at acceptance;
  084 owns conflict-safe proof).

## Recommended strategic follow-up

- 083/1 needs from this increment: the session-gated private artifact
  read (reuse for acceptance evidence), the deterministic snapshot
  document (acceptance input), and the `drift` field (equality gate).
- 084/088: conflict-safe review lifecycle; human Puck reuse.

Report publication commit: SELF

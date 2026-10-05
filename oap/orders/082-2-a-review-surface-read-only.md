# OAP Work Order — 082-2-a: human review surface (read-only) (082/2)

## 1. Identifier and mode

- Round ID: `082-2-a` (increment-qualified form: the SECOND semantic
  increment of numeric Objective 082 uses the qualified `NNN-I-L` namespace
  per `oap/governance/2026-09-14-increment-qualified-round-ids.md`; the first
  increment 082/1 retained the legacy flat round `082-a`, which remains
  immutable history).
- Objective: 082 (082/2 — human review surface, read-only).
- Mode: CREATE_NEW_PR — one fresh PR from verified main; one bounded
  semantic family (the human read-only review surface). Strategy anticipates
  a single round; if a completion claim is rejected, the SAME PR continues
  at `082-2-b` with a new order.
- Branch: `oap/082-2-a-review-surface-read-only`, created from verified
  remote main `e689076cda0a882ad13f7b641ebdf8efdacba773`.
- PR title: `OAP 082-2-a: human review surface (read-only) (082/2)`.
- PR number: whatever GitHub assigns at creation (expected #98; report the
  actual number; never assume it in documentation — reference the increment,
  branch, and SHAs, and the PR number as GitHub reports it).
- The dependabot PRs #83/#90/#94 are out of scope and are never touched.

## 2. Verified current state (strategy-verified 2026-10-05 against live
GitHub)

- Remote `main` = `e689076cda0a882ad13f7b641ebdf8efdacba773` (the 082/1
  merge; parents `c48849f149417fccf5cc0a152bc3ca39aaaf49ba` +
  `812e3e31aa0f4d8589cb3e7838958ce96b54575a` verified). Post-merge checks at
  e689076: 18 success + 1 skipped (Dependency review) + none
  failed/cancelled/pending.
- 082/1 (PR #97) accepted and merged 2026-10-05 at `e689076`: migration head
  is `070_001`; `control.review_job` + `control.review_snapshot` exist
  (worker-only DML on the job; snapshot INSERT/SELECT for
  `slaif_review_worker` only; REVOKE ALL on PUBLIC; NO long-lived role has
  UPDATE/DELETE on the snapshot and NO long-lived role has raw SELECT);
  rebuilt `slaif_workspace_freeze` (ACTIVE-only, revoke ALL capabilities,
  idempotent enqueue, never REVIEW directly); narrow `slaif_review_worker`
  with durable claim/heartbeat/stale-recovery; control route
  `POST /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/freeze/`
  (202; session+CSRF+`workspace:freeze`+exact binding; uniform 404;
  WORKSPACE_NOT_ACTIVE→409); control route policy = 194 keys (control 32).
- Snapshot document shape (verified in
  `review_worker/snapshot.py` + `070_001`): `normalized_state` keys =
  `state_version, workspace_id, site_id, site, base_site_revision,
  operation_watermark, locales, theme, regions, navigation, redirects,
  pages, media` (pages carry normalized `nodes` with the 11-column renderer
  composition order); top-level row = `status=COMPLETE,
  revision_watermark, versions, normalized_state, validation_report,
  media_references, browser_evidence, payload, digest` (digest = sha256 of
  the canonical JSON of `normalized_state`; recomputable in DB via
  `control.slaif_canonical_jsonb_text`), `created_by`. The per-operation
  timeline is NOT in the snapshot (watermark only) — the read model sources
  it from workspace-scoped operation/audit rows, which are frozen while the
  workspace is out of ACTIVE (all capabilities revoked, mutations denied).
- 081/1 (PR #96, `c48849f`, 2026-10-04): human Puck editing in the exact
  Agent workspace (migration `069_001`; the editor envelope asserts
  workspace ACTIVE — a frozen/REVIEW workspace MUST fail closed for Puck);
  admin workspace edit page exists at
  `apps/web/app/admin/sites/[siteId]/workspaces/[workspaceId]/edit/page.tsx`.
- 071 preview pattern (mirror target):
  `apps/web/app/preview/[workspaceId]/[[...sitePath]]/route.tsx` —
  Next.js route handler, `force-dynamic`, flight-free SSR via
  `renderToReadableStream` + `PageProjectionShell`
  (basePath `/preview/{workspaceId}/s/{siteKey}`), `resolveWorkspacePreview`
  resolution kinds (login→307 /login, not_found, redirect, render),
  noindex/no-store.
- 072 artifact retrieval: session-scoped private browser-artifact routes
  exist (verify in source at branch time; the review UI evidence section
  links through them; if a frozen-run artifact is not retrievable through
  the existing route, a MINIMAL read-only gating extension is permitted —
  document as an adaptation).
- Agent OpenAPI: 47 paths; strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`.
  Component catalog 32/32. E2E roster = 16 projects (`tools/compose/e2e.sh`
  final echo: `projects=16 setup=1 governance=1 preview=1
  preview-filtering=1 stable-devices=6 agent-sessions=2
  agent-workspace-puck=2 freeze-review-snapshot=1 media-publication=1
  artifacts=disabled`). Local secrets/roles manifests exact.
- Current doc surfaces carry STALE wording that this order's R5 repairs
  (verified text at e689076): `oap/INCREMENTS.md` header + Next row still
  say 082/1 "is in flight at `082-a` (PR #97)" (now merged) and the ledger
  has no 082/1 row; `oap/MVP-PROGRESS.md` sequence paragraph + row 082 carry
  the same in-flight wording, and row 081 reads
  "PARTIAL — 081/1 is accepted and merged in PR #96 at
  `c48849f149417fccf5cc0a152bc3ca39aaaf49ba` on 2026-10-04" (stale status:
  081/1 is the only planned 081 increment and no 081/2 is planned anywhere,
  so numeric 081 is complete); `README.md` planned-product-work row still
  lists 082/1 as planned/in-flight; `oap/MVP-CONTRACT-AUDIT.md` freeze row
  still says "NOT IMPLEMENTED ... Until it merges, the `review_snapshot`
  table/job/worker do not exist on `main`", the renderer row and promotion
  row carry 082/1 in-flight wording, and the Puck row body still describes
  the pre-081/1 separate-HUMAN-workspace gap with PARTIAL status.
- `oap/active` = `082-a` (last activated round; protocol-correct idle
  state until this activation).
- Local checkout is on `main` at e689076 (synced); one harmless untracked
  residue `.081-a-report-draft.md` remains (081-a leftover; do NOT commit
  it).

## 3. Strategic context

- Architecture (ARCHITECTURE-for-agents.md, Review UI paragraph, read in
  full by strategy): "Review UI shows rendered site; model/field/mapping,
  item/relation, resource, composition/theme/navigation/responsive/media
  summaries; semantic timeline and resource diff; screenshots/diagnostics/
  accessibility/sweep/Puck link; warnings/deterministic validation;
  conflicts; permission/quota and agent/source/browser metadata;
  accept/selective/discard. Active artifacts are not approval." This order
  delivers the READ-ONLY half: rendered site from the snapshot, the
  summaries, the semantic timeline + resource diff, evidence, warnings/
  validation, drift/conflict display, and metadata. Accept/selective/
  discard belong to 083/1 (and later) and are EXCLUDED here.
- Human decision D5 (2026-09-20) approved the split direction 082 = 082/1
  (freeze → immutable snapshot, done) + 082/2 (read-only review surface).
  This order is 082/2 only, from verified post-082/1 main.
- 082/1 residual risks carried into this increment (from its acceptance
  record ADJ-5): none of the four carried limitations are implemented here;
  they remain documented. The 072 preview 308-redirect root-cause fix is
  NOT folded into this increment (the review render mode is a separate
  `/review/` route, not the preview route; root-cause repair stays a
  separable maintenance increment).
- Concentrated OAP: one semantic family (human read-only review surface:
  trusted read model + snapshot-only render mode + responsive review UI +
  fail-closed negatives). No accept/discard semantics may enter — the
  moment a state-changing review decision enters, this increment is wrong.

## 4. Bounded scope

Exactly one semantic family — the human read-only review surface:

1. New migration `071_001`: one trusted, read-only review read-model
   function (deterministic review document: snapshot identity + drift +
   semantic timeline + bounded resource diff + summaries + frozen
   validation + evidence + metadata), EXECUTE for `slaif_control` only, no
   table-grant changes, no DML (R1).
2. Human Control read route: `GET .../workspaces/{workspaceId}/review/`
   (session auth, read-only, no CSRF, uniform 404, established path-layer
   422), registered in the route policy as a read (R1).
3. Review render mode: `/review/[workspaceId]/[[...sitePath]]` mirroring
   the 071 preview route pattern, fed ONLY by the snapshot normalized state
   (never live COW, never canonical), private-staging media, review banner
   with digest + drift, noindex/no-store, deterministic byte output (R2).
4. Responsive read-only review UI page in the admin app (all sections from
   the read-model document; no accept/discard; "View rendered site" link;
   evidence thumbnails via existing 072 retrieval) (R3).
5. Fail-closed negatives + immutability + side-effect-free proof
   (integration + new E2E project `review-surface`, 2 contracts) (R4).
6. Current-truth documentation flips in durable wording (R5), contract
   byte-identity (R6), evidence (R7), hard constraints (R8).

## 5. Explicit non-goals

- No accept, no discard, no selective acceptance, no promotion, no
  publication (083/1, 083/2, 083/3). No state-changing control route of
  ANY kind in this increment.
- No media finalization, no anonymous public media reads, no public
  namespace writes (083/3).
- No conflict-resolution or rebase behavior; the drift display is
  read-only (083/1 enforces equality at acceptance; 084 owns
  conflict-safe proof).
- No scheduler work, no media-GC work, no MCP changes, no source tools.
- No new agent routes, no new scopes, no new permission keys, no new
  database roles, no new credentials, no new dependencies, no lockfile or
  supply-chain changes, no infrastructure changes beyond existing services.
- No Puck behavior changes (the frozen-workspace fail-closed is EXISTING
  081/1 behavior — pin it in negatives, do not change it). No changes to
  shared renderer component semantics; existing preview/canonical rendered
  output must remain byte-stable (existing E2E stays green).
- No changes to `contracts/openapi/agent-v1.json` or generated catalog /
  design-system artifacts (byte-identity required, R6).
- No dependabot PR activity of any kind.
- No 072 preview 308-redirect root-cause fix (separable; not here).

## 6. Requirements

### R1 - Migration `071_001`: trusted read-only review read model

Create
`services/backend/src/slaif_agent_site/db/alembic/versions/071_001_review_surface_read_model.py`
(reversible downgrade: drop exactly what this migration creates):

1. `control.slaif_review_read_model(p_workspace_id uuid, p_site_id uuid,
   p_user_account_id uuid) RETURNS jsonb`, `LANGUAGE plpgsql SECURITY
   DEFINER SET search_path = pg_catalog`.
   - Gating (fail-closed, NO oracle): the site exists, `p_user_account_id`
     is a site member (the established control-plane membership predicate
     used by the existing control routes), the workspace exists, and
     `workspace.site_id = p_site_id`; then a COMPLETE
     `control.review_snapshot` row must exist for the workspace. ANY
     failure raises the same stable internal class (distinct error code
     inside the DB is acceptable; the HTTP layer maps EVERY gate failure
     uniformly — no observable difference between "not a member",
     "unknown id", "wrong site", and "no snapshot").
   - Returns ONE deterministic jsonb document (all lists in a fixed order —
     operations by their deterministic sequence, resource entries by stable
     id; no wall-clock nondeterminism inside lists):
     - `snapshot`: `{id, digest, state_version, revision_watermark,
       base_site_revision, status, created_at, created_by, versions}`.
     - `drift`: `{current_site_revision, base_site_revision, equal}` where
       `current_site_revision` is the current canonical site revision read
       from the control site-revision state (read-only).
     - `timeline`: the workspace-scoped operations up to and including the
       snapshot watermark (the set is frozen — no mutation can enter an
       out-of-ACTIVE workspace): `[{operation_id, operation_type, resource,
       created_at}]` in deterministic order. Operations above the watermark
       are excluded (proof fixture required in integration).
     - `resource_diff`: per touched resource family (pages, composition
       nodes, items, fields, mappings, translations, relations, collection
       views, theme, navigation, redirects, media references):
       `{added: [...], modified: [{id, fields: {name: {before, after}}}],
       deleted: [...]}` — bounded FIELD-LEVEL diff of the stored JSONB
       (one level; no deep recursive diff), deterministic ordering, sourced
       from the COW change tables under the trusted workspace context.
     - `summaries`: model/field/mapping counts; item/relation counts;
       resource inventory; composition counts grouped by component type
       (the 32-type catalog taxonomy); theme summary (token groups
       present); navigation count; redirect count; media summary (counts by
       class + reference count, using the established reference forms —
       never raw private byte paths); responsive/theme-cascade summary from
       the snapshot.
     - `validation`: the snapshot `validation_report` verbatim (frozen)
       plus a derived `warnings` array (deterministic).
     - `evidence`: the snapshot `browser_evidence` verbatim (run ids) and
       the artifact references in the established 072 retrieval form.
     - `metadata`: workspace `{id, title, actor_type, status}`; site
       `{id, key}`; capability state (the revoked set after freeze —
       metadata only, NEVER tokens or secrets); quota policy summary;
       agent/session/browser metadata from the snapshot versions and the
       job row.
   - The function performs NO DML of any kind (SELECT only). If a short
     shared advisory lock is required for a consistent COW read, it is
     permitted and must be documented in the report (no exclusive lock,
     ever).
   - Grants: `REVOKE ALL ON FUNCTION ... FROM PUBLIC`;
     `GRANT EXECUTE ... TO slaif_control` only. NO changes to the `070_001`
     table grants (`control.review_snapshot` keeps no long-lived raw
     SELECT). Update the bootstrap revision set (the established pattern).
2. Control API route `GET
   /api/control/v1/sites/{siteId}/workspaces/{workspaceId}/review/` in
   `control_api` (typed `UUID` path parameters exactly like the sibling
   routes; human session auth via the existing control auth; READ route —
   no CSRF requirement, no state change; registered in the route policy
   exactly like the existing control read routes — read-only kind).
   - Response: the read-model document as JSON (no capability tokens, no
     secrets, bounded size — truncate any unbounded string fields with a
     documented bound if needed).
   - Error mapping: uniform `404 RESOURCE_NOT_FOUND` for every gate
     failure (member/unknown/cross-site/no-snapshot indistinguishable);
     malformed path UUIDs → `422 VALIDATION_ERROR` at the framework
     path layer (established uniform control-plane pattern — the 082/1
     order's "400" line was adjudicated an order correction in favor of
     this pattern); catch-all → `503` from `None` (no leaking internals).
3. Python wiring: a thin typed service wrapper following the existing
   `control_api` database/service pattern (one module or inlined — keep
   the budget honest).

### R2 - Review render mode (Web; snapshot only, never live)

- New route `apps/web/app/review/[workspaceId]/[[...sitePath]]/route.tsx`
  mirroring the 071 preview route pattern: Next.js route handler,
  `export const dynamic = "force-dynamic"`, flight-free SSR via
  `renderToReadableStream` + `PageProjectionShell` with
  basePath `/review/{workspaceId}/s/{siteKey}`, same head shape (lang,
  viewport, title).
- New resolution `resolveWorkspaceReview` (new module, e.g.
  `apps/web/src/sites/review-page.ts`) with the same resolution-kind
  contract as preview: `login` → 307 `/login`; `not_found` → 404 (uniform,
  no oracle); `redirect` → the snapshot's frozen redirect set (bounded,
  same status semantics as preview); render → projection built from the
  SNAPSHOT `normalized_state` ONLY (pages/nodes, theme, locales, regions,
  navigation, redirects, media) via the R1 read path. The resolver must
  never read live COW or canonical state (unit-level proof: the resolver's
  content source is the read-model document).
- Media: private staging bytes through the trusted session-scoped media
  resolution (never a public URL; an unresolvable reference renders a
  deterministic placeholder — never a raw error page, never a 500).
- Review overlay banner (server-rendered, no client JS): "FROZEN SNAPSHOT
  — read-only review" plus digest, `base_site_revision`, current revision
  with an explicit drift warning line when `equal` is false, and
  `revision_watermark`. No edit affordances, no Puck link inside the
  rendered document.
- Response headers: `noindex` + `no-store` (match preview).
- Determinism: the same snapshot renders byte-identical HTML across loads
  (E2E hash pin); the existing preview/canonical rendered output is
  unchanged (existing preview E2E contracts stay green unmodified).

### R3 - Review UI page (admin; responsive; read-only)

- New page
  `apps/web/app/admin/sites/[siteId]/workspaces/[workspaceId]/review/page.
  tsx` (admin session auth exactly like the existing workspace edit page;
  responsive per admin conventions; keyboard-accessible; three viewports
  in E2E). Server-rendered or minimally client-bound per admin patterns —
  no new framework, no new dependencies.
- Content (ALL from the R1 document; read-only):
  - Header: workspace/site titles, workspace status, snapshot identity
    (digest, `revision_watermark`, `base_site_revision`, created at/by,
    `state_version`), versions block (catalog/composition/renderer/
    content-model/Puck).
  - Drift banner: `equal` true → "Canonical unchanged since freeze";
    false → explicit "Canonical drifted after freeze — acceptance is
    blocked until re-freeze (enforced at 083/1); the frozen review remains
    visible."
  - Semantic timeline section (the `timeline` array, deterministic order).
  - Resource diff section: per family — added / modified / deleted with
    field-level before/after; bounded rendering (a documented top-N per
    family plus exact counts; N fixed and pinned in the report).
  - Summaries section (model/field/mapping, item/relation, resource,
    composition-by-type, theme, navigation, redirects, media, responsive).
  - Validation section: the frozen `validation_report` + derived warnings.
  - Evidence section: screenshots from `browser_evidence` runs through the
    EXISTING 072 session-scoped artifact retrieval (thumbnails + links);
    diagnostics/accessibility/sweep metadata from the snapshot evidence.
    If a frozen-run artifact is not retrievable through the existing
    route, make the minimal read-only gating extension and document it as
    an adaptation.
  - Metadata section: revoked capability set (metadata only, no tokens),
    quota policy summary, agent/session/browser metadata.
- Actions: "View rendered site" (primary, → `/review/{workspaceId}/...`)
  and "Back to workspace". NO accept/discard controls of any kind
  (083/1). NO Puck launch from the review page.

### R4 - Negatives, immutability, and side-effect freedom

- New E2E project `review-surface` (exactly 2 contracts), added to
  `playwright.config.ts` and the `tools/compose/e2e.sh` roster (projects
  16 → 17; final echo updated accordingly) + smoke roster/pin updates
  (the mechanical pin class established in 081/1 and 082/1):
  1. `review-surface-review-render-and-summary`: fixture site + workspace;
     create known content before freeze (at least one page, one
     composition node change, one item/translation change); freeze via the
     082/1 route and wait for REVIEW. Then: load the review UI at three
     viewports (assert every section renders with the fixture's expected
     entries — timeline entries, diff added/modified/deleted with
     before/after, summaries, frozen validation, evidence, metadata,
     digest displayed); load the `/review/` render at three viewports (the
     rendered page set/slug/effective_route/nodes equal the snapshot
     fixture; private staging media renders; public `/media/public/`
     absent; banner shows digest equal to the psql-recomputed canonical
     digest via `control.slaif_canonical_jsonb_text`; drift section shows
     "equal"); evidence screenshots retrievable via the existing route;
     determinism: two loads of the same render → identical HTML hash;
     observation collector clean.
  2. `review-surface-fail-closed-negatives`: uniform 404 — nonmember
     (fixture user one) real vs random workspace id (indistinguishable),
     wrong-site binding real vs random (indistinguishable), a fresh ACTIVE
     workspace WITHOUT a snapshot (indistinguishable), cross-site;
     malformed/crafted UUIDs → 422 (path layer, pinned); the `/review/`
     render route with no snapshot → uniform 404 (no oracle, no login
     leak); Puck launch on the frozen workspace fails closed (the 081/1
     ACTIVE assert — no editor surface, stable error); an Agent mutation
     against the REVIEW workspace is denied (the established uniform 401
     / 409 pins); the review read is side-effect-free (before/after psql:
     zero new rows in operation/audit/browser_event tables, canonical site
     revision unchanged, workspace row unchanged); the route-policy delta
     is reads-only (no new state-changing route; CSRF policy unchanged);
     snapshot immutability re-asserted in the grant matrix (no long-lived
     role holds UPDATE/DELETE on `control.review_snapshot`).
- Integration (new spec file, e.g.
  `services/backend/tests/integration/test_review_surface_read_model.py`):
  the gating matrix (member/nonmember/wrong-site/unknown/no-snapshot →
  uniform failure, no oracle); document shape + key inventory; watermark
  boundary (operations above the watermark excluded — dedicated fixture);
  `drift.equal` true and false fixtures; determinism (two calls → equal);
  side-effect-free (row counts unchanged across a full document read,
  including the COW change tables).
- Unit: route-policy registry 194 → 195 (control 32 → 33); health-app
  typed route list for control (+1 read route); foundation-contract file
  pins (+`071_001`, +new web/backend modules); revision pins
  `070_001` → `071_001` (the same mechanical pin class as 082/1 — every
  occurrence updated, assertions otherwise untouched); packaging
  roster/pin updates (e2e.sh projects=17 + `review-surface=1`, smoke
  pins). NO error-shape or behavior change in any pre-existing test —
  pin/topology updates only (strategy verifies every modified test file).

### R5 - Current-truth documentation (durable wording)

Update exactly the four current-state surfaces, in the standard durable
form used since 078-z (identify increment/PR + source revision; state
GitHub is authoritative for live acceptance/merge state; record immutable
merge facts only when already known; `oap/active` = last activated round
until next activation; NO wording that becomes false the instant this PR
merges):

1. `oap/INCREMENTS.md`: header — replace the stale "082/1 ... in flight
   at `082-a` (PR #97)" with the merged facts (PR #97, merge commit
   `e689076cda0a882ad13f7b641ebdf8efdacba773`, 2026-10-05) and state the
   next bounded increment 082/2 (human review surface, read-only) is in
   flight at `082-2-a`; keep the `oap/active` definition. Ledger — add the
   082/1 row (accepted and merged in PR #97 at the full e689076 SHA on
   2026-10-05; 082/1 closed) and update the Next row (082 after 082/1;
   082/2 in flight at `082-2-a`).
2. `oap/MVP-PROGRESS.md`: sequence paragraph (082/1 merged facts + 082/2
   in flight); row 081 → "COMPLETE — 081/1 is accepted and merged in PR
   #96 at `c48849f149417fccf5cc0a152bc3ca39aaaf49ba` on 2026-10-04; numeric
   081 complete (081/1 is the only planned 081 increment; no 081/2 is
   planned)" (post-merge strategy bookkeeping after independent evidence
   verification — the 081/1 acceptance record); row 082 → "PARTIAL —
   082/1 is accepted and merged in PR #97 at
   `e689076cda0a882ad13f7b641ebdf8efdacba773` on 2026-10-05; 082/2
   (read-only review surface) is in flight at `082-2-a`".
3. `README.md`: delivery-sequence — add the "Objective-082/1 freeze and
   review snapshot (merged)" row (082/1 merged facts + GitHub-authoritative
   caveat); planned-product-work row — remove the 082/1 entry (now
   delivered) and prepend "the read-only human review surface (082/2, in
   flight at `082-2-a`)"; keep the remaining entries.
4. `oap/MVP-CONTRACT-AUDIT.md`: authoritative audited source revision →
   `e689076cda0a882ad13f7b641ebdf8efdacba773` "as of the 082/2
   current-truth reconciliation (2026-10-05), with the 078-z, 081, and
   082/1 reconciliation revisions retained as historical". Puck row —
   update the body (081/1 closed the separate-HUMAN-workspace gap: human
   Puck now edits the exact Agent workspace under server policy) and set
   status to "COMPLETE — E2E PROVEN" (action column: 084/088 reuse for
   human adjustment). Freeze row — update the body with the 082/1 merged
   facts (race-safe freeze with capability revocation, durable review job
   with stale-claim recovery, immutable complete review snapshot with
   recomputable canonical digest, bounded browser-run drain; E2E-proven on
   the exact head) and note the render-thereafter half follows in 082/2 in
   flight; status remains PARTIAL until 082/2 merges. Renderer row — "the
   review-snapshot render mode is delivered by 082/2 in flight at
   `082-2-a` (the 082/1 immutable snapshot data plane is merged at
   e689076)". Promotion row — 082/1 landed the durable review-job worker
   (freeze jobs only) as merged facts; the 083 target line is unchanged.

- An adversarial grep for stale live-state claims (pattern class:
  `082/1.*(open|pending|in flight)`, `081.*(open|pending|in flight|
  opened)`, `this PR is (still )?open`, `pending strategic (merge|
  acceptance)` outside immutable transcripts) must return nothing in
  current-state documents.

### R6 - OpenAPI and generated contracts (byte-identity)

- `contracts/openapi/agent-v1.json` byte-identical to base (47 paths;
  strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  unchanged) — the new route is a human control read route and adds no
  agent surface (same class as the 082/1 freeze route).
- `git diff <base>..<head> -- contracts/ packages/` empty; no generated
  catalog / design-system artifact changes.

### R7 - Evidence (all actually executed, honestly reported)

- Every run of CI at every head with exact run IDs, pass counts, and any
  failure with its exact signature and disposition.
- Integration + unit counts (collected and executed); the new integration
  spec's fixture details (watermark boundary, drift fixtures, gating
  matrix).
- E2E roster run with the `review-surface` project (both contracts), three
  viewports, the determinism HTML hash, the psql digest recompute, the
  side-effect-free before/after counts, the grant-matrix re-assertion.
- The bounded top-N rendering constant (R3) and any 072 retrieval gating
  adaptation, itemized.
- Honest pass/fail/skip/not-run/pending for every named item.

### R8 - Hard constraints

- Zero state-changing routes; zero new agent routes/scopes/permission
  keys; zero new roles/credentials; zero new dependencies; lockfiles,
  supply-chain evidence, workflows, and compose topology byte-identical
  except the documented roster/pin script lines (R4).
- No Puck behavior change; no shared-renderer component change; existing
  preview/canonical rendered output byte-stable (existing E2E contracts
  green unmodified).
- No scheduler/MCP/GC/source-tool changes; no dependabot activity; no
  secrets in any new surface (the read-model document is audited for token
  / credential / private-path leakage in the report).

## 7. Acceptance criteria (observable)

1. `071_001` upgrades cleanly from `070_001` and downgrades back (round
   trip, exact drop set); the function is `SECURITY DEFINER`,
   `search_path = pg_catalog`, EXECUTE for `slaif_control` only, PUBLIC
   revoked; `070_001` table grants unchanged; bootstrap revision set
   updated.
2. The read-model gating matrix: member/nonmember/wrong-site/unknown/
   no-snapshot all produce the SAME uniform 404 at the route (E2E +
   integration); malformed UUID → 422 path layer.
3. The document is deterministic (two calls → equal; list ordering
   pinned); the watermark boundary excludes operations above the watermark
   (dedicated fixture); `drift.equal` true/false both proven.
4. The review read is side-effect-free (psql row counts unchanged across
   a full read, including COW change tables; canonical revision unchanged).
5. `/review/` renders ONLY from the snapshot (resolver unit proof + E2E:
   rendered page set equals the snapshot fixture; private staging media;
   public paths absent; banner digest equals the psql-recomputed digest;
   noindex/no-store; byte-identical across two loads).
6. The admin review page renders every R3 section with the fixture data at
   three viewports (DOM pins); keyboard-accessible; no accept/discard
   controls present (assert absence).
7. Evidence screenshots retrievable through the existing 072 route (or the
   documented minimal extension); diagnostics/accessibility/sweep metadata
   rendered.
8. Negatives: Puck on the frozen workspace fails closed (081/1 assert,
   stable error, no editor surface); Agent mutation on REVIEW denied
   (uniform 401/409 pins); snapshot UPDATE/DELETE denied for every
   long-lived role (matrix); the route-policy delta is reads-only; no new
   state-changing route; CSRF policy unchanged.
9. R5: the four surfaces match the required durable form exactly; the
   adversarial grep returns nothing in current-state documents; row 081 is
   COMPLETE with the stated rationale; no "this PR merged" wording.
10. R6: `git diff base..head -- contracts/ packages/` empty; strip-identity
    sha256 re-proven at both base and head (strategy recomputes both
    sides).
11. Full CI roster (17 projects) terminal and green at the exact report
    head: all 20 required checks successful, none failed/cancelled/pending;
    first attempt or one documented flake-class re-run max.
12. Predeclared budgets (section 10) honest; cumulative review size
    computed base→head and grouped; the 20 prod/config-file trigger
    reported explicitly fired/not-fired; CLOSURE_ONLY state (expected:
    never entered) reported; any variance itemized and classed.

## 8. Verification and workflow

- Strategy activates this order atomically with `oap/active` = `082-2-a`.
- The executor creates the branch from verified main
  `e689076cda0a882ad13f7b641ebdf8efdacba773` and pushes the transcript
  commit T first (order file + `oap/active` bytes exactly as published;
  nothing else in T beyond the standard transcript bytes).
- Implementation commits follow (I, ...); a docs commit (D) with the R5
  flips precedes the report commit (S, report-only, parent =
  implementation head).
- Local authority: the executor owns packages, browsers, databases,
  services, compose stacks, and test execution in the disposable VM
  (passwordless sudo); strategy never performs that labor.
- GitHub workflow: push the branch, open the unique objective PR
  (title per section 1), report the PR number/URL/branch/SHAs in the
  report. No merge by the executor — only strategy merges.
- Flake policy: at most ONE documented unmodified CI re-run, and only for
  the documented flake class with its exact failure signature; any other
  recurrence is a real failure — fix in code or report BLOCKED.
- The full CI roster must reach the terminal roster at the exact report
  head; do not re-run unmodified heads except the single documented
  flake-class allowance.

## 9. Report requirements

`oap/reports/082-2-a-review-surface-read-only.md` must contain, at minimum:

- Order identity (round, objective, PR, branch, base, every commit
  T/I/.../D/S with SHAs), the exact report-publication convention
  (`Report publication commit: SELF`; the remote PR head must be that
  report-only commit whose parent is the literal implementation-head SHA).
- Authoritative GitHub state at report time (PR number, head SHA, check
  state per run).
- Honest CI history (every run, every failure, every re-run with the exact
  flake signature if the allowance is used).
- Budget table vs the predeclared budget (production/config; migrations;
  test/evidence; generated; docs; OAP transcript; substantive lines) with
  the cumulative base→head grouped size and the explicit trigger
  fired/not-fired determination.
- Every R7 evidence item with its actual executed output (counts, SHAs,
  psql baselines, hashes, viewport list, the top-N constant, any
  adaptation itemized with rationale).
- Deviations from this order (if any) with rationale; known limitations;
  residual risks and what 083/1 needs from this increment.
- Confirmation of R8 hard constraints (lockfiles/workflows/supply-chain
  byte-identity; zero state-changing routes; no Puck/renderer behavior
  change; secrets audit of the new surfaces).
- `Report publication commit: SELF`.

## 10. Predeclared review budget (2026-09-14 review-unit governance
in force)

- Production/config files: at most 16 (migration `071_001`; control_api
  read wiring/route/route policy ≤ 3; backend service wrapper ≤ 1; web
  review route 1; review resolver module 1; admin review page 1; review UI
  components ≤ 3; `playwright.config.ts` 1; `tools/compose/e2e.sh` 1;
  `tools/compose/smoke.sh` 1; `tools/local_secrets/initialize.py` 0).
- Migrations: exactly 1 (`071_001`).
- Test/evidence files: at most 14 (new integration spec; new E2E spec;
  unit route-policy/health-app/foundation-contract updates; integration
  revision pins — the established mechanical pin class; packaging
  roster/pin updates).
- Generated-contract footprint: 0 (byte-identity, R6).
- Docs footprint: 4 surfaces (R5).
- OAP transcript footprint: this order + `active` + one report.
- Substantive implementation-line scale: at most 3000 lines.
- The ~20-30 production/config file threshold remains a REVIEW TRIGGER,
  not a quota: if the honest cumulative count crosses 20, the PR enters
  CLOSURE_ONLY — no new semantic family may enter after that point.
- Do not game the budget by moving code between directories, excluding
  meaningful tests, or treating generated/OAP files as if they do not
  exist.

## 11. Review-unit governance (2026-09-14 amendment, in force)

- Cumulative review size is computed base→head (not latest-round delta),
  grouped: production/config; migrations; tests/evidence; generated
  artifacts; docs; OAP transcript.
- CLOSURE_ONLY mode (if triggered): no new semantic family, no adjacent
  feature, no opportunistic scope, no next-objective work; only finite
  defects/evidence required to make already-added behavior safe, correct,
  and reviewable. Separable functionality starts from verified merged main
  in another PR.
- If Strategy rejects COMPLETE, one finite checklist of unresolved
  criteria with the executable evidence required for each; a later
  report may claim COMPLETE only if every named criterion was actually
  executed; an omitted required browser/PostgreSQL/concurrency/public-
  boundary proof makes the report PARTIAL/BLOCKED, never COMPLETE.
- If remaining work is semantically separable, it is split BEFORE being
  added to this PR.

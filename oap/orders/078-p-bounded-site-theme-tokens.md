# OAP Work Order — 078-p: bounded site-theme token increment

Verified baseline: PR #77 is MERGED at
`3cae3d6cef2a92e7068856d21bc9a47b8190c22e`, merged 2026-09-09T10:46:52Z,
contained in current remote main. Final PR head `502679c` passed all 20 checks;
post-merge CI `34342055129` and CodeQL `34342055263` are SUCCESS with all
applicable jobs passed (Dependency review is PR-only and skipped on main).
Current active is 078-o, whose report-only parent/path was independently verified.
No existing theme-increment branch or PR was found; start from this verified main.

## Identity, scope and authority

- Objective 078; increment 078/2; round 078-p; mode CREATE_NEW_PR.
- Repository `ulfe-lmi/slaif-agent-site`; base verified current remote `main`.
- New branch `oap/078-2-site-theme-tokens`; exactly one NEW PR for this increment.
- PR #77 is closed to additional product scope. Do not amend or reopen it.
- The human-approved `oap/governance/2026-09-09-bounded-semantic-pr-increments.md`
  prospectively permits continuing 078 letters across sequential PRs. Explicit
  mode controls delivery; the historical letter/PR rule is superseded.

Deliver one independently acceptable site-theme token data plane: closed schema,
Agent discovery/read/PATCH, trusted database enforcement, and actual shared
Render/Web plus existing human Editor/Puck consumption. Nothing else in remaining
078 belongs to this PR. Numeric 078 remains PARTIAL after this increment.

## Concrete implementation anchors and deliberate reuse

The deferred theme implementation `567973e1897ff0ec1cc5017704dd7b914a88d6da`
and report `127d7f13c6e7e139af94792739e46ffe57cf843a` remain in history.
Reuse useful product changes after inspecting them against fresh main, NOT a
blind whole-commit cherry-pick. Never restore old orders/active/status, regress
component design authority, or overwrite newer migrations. Its report is an
evidence index, not accepted proof for this rebased increment.

Inspect `services/backend/src/slaif_agent_site/`:

- `db/alembic/versions/020_001_nav_theme_functions.py`: existing theme singleton,
  shallow JSON, and `slaif_theme_get(uuid)` declared STABLE despite INSERT;
- `content_model/nav_models.py`, `content_model/service.py` and
  `editor_api/nav_theme_http.py`: existing theme DTOs/read/update and human
  `theme:read` / `theme-global:write` permission boundary;
- `render_api/projection.py`: current palette/typography/layout/shape projection;
- existing Agent mutation/read executor, trusted resource helper, route policy,
  idempotency/lifecycle locks and component ADD/CHANGE/REMOVE/create authority.

Retained main migrations end at 064. The old theme migration named 062 MUST
become an append-only new migration after the verified head (expected 065).
Do not edit migrations 060–064 or earlier. Reuse public foundation APIs only.
Inspect existing `apps/web/src/admin/composition-editor.tsx`, trusted renderer,
CSS, normalized Puck adapter and current schema generators before adapting reuse.

## Product contract

Expose exactly GET `/api/agent/v1/theme-schema`, GET `/api/agent/v1/theme` and
PATCH `/api/agent/v1/theme`. Reads require `theme:read`; an actually changed
PATCH requires exact `theme-tokens:write` (L3), never substitution by
`theme-global:write` or an unrelated L4 scope. A valid, current-version no-effect
PATCH requires bound `theme:read`, but no additional write authority and no
mutation effect. Express this changed-value condition exactly in OpenAPI,
rather than claiming write authority is required merely when a field is supplied.
Use closed typed request/result/OpenAPI schemas and exact
handler/route-policy/canonical-OpenAPI bidirectional drift checking.

One deterministic `theme-schema/v1` authority defines useful bounded enum keys
and defaults for four groups: accessible palette preset/roles; approved local
typography family/scale/weight; content width/spacing/grid gap; radius/shadow.
Reuse compatible component design tokens. Publish schema/renderer versions,
defaults, role-contrast validation and exact allowed vocabulary. No arbitrary
CSS, colors, selectors, custom properties, font URLs, breakpoints, JS, executable
input, unknown keys, or caller-created primitives. Do not alter catalog-v1.

Theme is a site singleton visible through the bound workspace, with stable ID,
immutable site association, positive optimistic version and deterministic
schema/renderer continuity. Reads MUST be truly read-only: no row materialization,
COW operation, audit, mutation quota, timestamp or version change. For an absent
theme, a documented deterministic pure default projection is permitted, with
stable identity/version and first materialization ONLY through an authorized
COW mutation; no canonical write on GET. Existing valid state is migrated
losslessly or rejected with actionable diagnostics, never silently discarded.
Prove existing-site and newly-created-site defaults without broadening Control
content DML. Pending/incompatible COW state must fail a migration safely.

PATCH partially merges supplied group/token fields, with positive expected row
version and Idempotency-Key. Trusted SQL independently validates the final state,
capability/site/workspace/state/scope/resource constraints and actual changed
keys, including removals/resets if supported. Schema-derived resource allowlists
must apply at DB and HTTP, not just UI. No direct runtime helper bypass.

Changed success is exactly one version increment, mutation quota charge, COW
operation, idempotency completion and semantic audit identity:
`THEME_UPDATED / theme / PATCH / 200 / mutation`. Replay returns the exact stored
response without another effect; same key/different request is 409. Preserve
existing no-effect least privilege/accounting, cancellation rollback and trusted
context. Failed/stale/denied/invalid/quota paths have no durable residue beyond
explicitly documented existing read/request accounting conventions.

Use deterministic transaction locks after the existing lifecycle lock. Two
same-version updates, including first materialization, yield exactly one winner
and one conflict with one durable effect. Independent workspaces/sites stay
isolated; canonical is unchanged before future human promotion.

## Actual renderer and human editor proof

Render projects the exact visible normalized theme/version. Trusted static
classes/assets implement every advertised token, using the shared renderer for
canonical and authenticated workspace preview; no unsafe inline CSS or remote
font acquisition. Theme changes must have measurable computed-style effects
across representative palette, typography, layout and shape components, not
only classes or JSON. Check default/reset behavior and compatibility with
component-local overrides/responsive fallback already accepted in PR77.

Existing human Editor/Puck theme controls derive from the same schema and save
through existing authorized HUMAN-workspace/COW semantics. Preserve the current
human permission boundary and reject crafted invalid/unauthorized Editor calls.
No exact-Agent-workspace Puck selection feature, publication or canonical write.

## Required acceptance evidence

Use human-issued real capabilities through public Agent HTTP with PostgreSQL,
plus targeted direct `slaif_agent_runtime` hostile calls. Reuse the existing
public NGINX acceptance fixture; do not seed the theme outcome with owner SQL
or privileged internal/test-only substitutes. Prove:

1. Read-pure schema/default discovery, then L3 changed PATCH/read and authorized
   same-workspace Render/browser result for all four groups; canonical/foreign
   workspace/site remain unchanged. Existing and absent/default themes covered.
2. L1/L2, missing/narrowed scope/resource, unrelated-L4 substitution, wrong
   site/workspace, expired/revoked/frozen and quota denial, with exact errors.
3. Unknown keys/version/enum, raw CSS/font URL/executable input, invalid palette
   contrast and out-of-vocabulary layout/shape rejection at HTTP AND trusted SQL.
4. Exact no-effect/replay/mismatch/stale/audit/quota effects, deterministic
   concurrent same-version and first-materialization races using real DB
   barriers/lock observations, never timing sleeps as proof; cancellation and
   reconnect/restart leave expected isolated durable state.
5. Existing Editor/Puck round-trip and real browser computed-style assertions
   for every declared token family, including precedence/default resets and
   private no-store/noindex preview. No source regex substitutes.
6. Data-bearing upgrade/downgrade/re-upgrade preserving valid legacy state and
   exact prior function/grant restoration. Invalid/incompatible/pending-state
   migration fails without data loss; setup/runtime/reviewer separation remains.
7. Closed OpenAPI and schema drift, all required existing current-head CI and
   supply-chain gates; preserve Next16.3.3 and all unrelated dependency pins.

Add focused theme tests in a dedicated integration file if useful for review;
wire actual focused PostgreSQL coverage into CI. Do not mechanically refactor
the large component suite. Run focused proof before broad CI; expensive existing
CI can supply broader matrix/Compose evidence without redundant local reruns.
Every pass/fail/skip/not-run/pending claim must name its revision and boundary.

## Reviewability and non-goals

The preserved patch touched 48 files, but that includes generated OpenAPI,
tests, status/version bookkeeping. Its production changes cross a single
schema/DB/API/renderer pipeline. Reuse is not permission to accumulate scope:
report production/migration/test/generated/docs counts and substantive line
totals separately. At roughly 20–30 implementation files or several thousand
substantive lines, explicitly reassess and explain the coherent merge unit;
stop expansion and request strategy if another semantic layer is needed.

No global regions/header-footer architecture, per-page style, catalog expansion,
new media, MCP, exact-workspace Puck, lifecycle/publication, reconstruction,
cleanup/refactor, dependency upgrade, exception, gate weakening or full-078/MVP
completion claim. No historical orders/reports rewritten. Existing coder only;
routine safe tools/DB/Docker/browser setup belongs to its passwordless-sudo VM,
not the human. No production resources or secrets.

## Documentation, GitHub delivery and report

Commit the strategic record `oap/audits/078-1-merge-acceptance.md` unchanged.
First reconcile current `oap/INCREMENTS.md`, MVP progress/audit and API/testing
docs: PR77 accepted/merged at the verified SHA, 078/2 active separately, numeric
078 PARTIAL. Preserve earlier audit/report history. The NEW PR description must
describe the whole bounded theme increment and exact supported public behavior,
not only the last repair. Record deferred global/page-style/catalog scope.

Fetch current main, preserve prior work, create the new named branch and exactly
one new theme-increment PR. Commit unchanged order and active078-p, implement,
verify, push and reasonably repair in-scope failures. Never merge/auto-merge.
Publish `oap/reports/078-p-bounded-site-theme-tokens.md` as the report-only SELF
child of a literal pushed implementation SHA. Include PR/URL/branch/base,
reused/deferred commit identity, exact files/size, each acceptance proof,
commands/results/CI URLs, migration/privilege evidence, skips/limits/risks and
no broader completion claim. Report only after remote PR exists. Lint Markdown
before publication. Send exact FIFO OK, then wait for strategic acceptance.

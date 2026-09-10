# OAP Work Order — 078-v: bounded per-page style overrides

Verified baseline: remote main is
`fe31c9f30a7797d0916ad7f8fb56344bc61526f3`, the accepted PR80 maintenance merge
at2026-09-10T11:26:36Z. Its pre-merge20checks passed; post-merge CI34471315393
and CodeQL34471315385 are SUCCESS with all applicable jobs successful (only
PR-only Dependency review skipped by its existing event condition). Chrome153
is now measured and actually scanned, zero unexcepted Critical, no exceptions.
PR77 and PR79 are accepted component/local-design and site-theme increments.
No page-style branch or PR exists. Start the new branch from this verified main.

## Identity and bounded contract

- Objective078; increment078/4; round078-v; mode CREATE_NEW_PR.
- Start verified current remote main; new branch `oap/078-4-page-style-overrides`.
- Exactly one NEW PR. PR77, PR79 and PR80 are accepted closed increments; do not
  amend/reopen them or replay their old active pointers.
- Human amendment `oap/governance/2026-09-09-bounded-semantic-pr-increments.md`
  controls explicit mode and sequential PRs with continuing078letters.

Implement only bounded page-style overrides over the now-accepted site theme:
public Agent read/update, trusted DB authority, inheritance/reset, shared
Render/Web and existing human Editor/Puck preservation. This is the next small
dependency-correct design layer. Global regions/header-footer architecture and
catalog breadth remain separate future increments. Numeric078 stays PARTIAL.

## Concrete anchors and model

Inspect current `content_model/page_models.py`, `content_model/theme.py`,
Agent page/theme handlers and mutation/read executor, structural/lifecycle lock
helpers, Render projection, Web theme classes, Editor/Puck adapter/controls,
and migrations021/022/049/060–065. `content.page` owns page lifecycle/version;
`content.page_composition` holds component nodes, not a singleton page root.
Do not hide page styles inside SEO, arbitrary component props or opaque Puck JSON.

Reuse the exact accepted theme token vocabulary for palette, typography,
content width/spacing/grid gap and radius/shadow. Add no new colors, font
families, CSS, breakpoints, tokens or catalog primitives. Store explicit
page-owned overrides separately from inherited site defaults; default empty
overrides. Use a closed deterministic `page-style/v1` schema and exact typed
records with immutable site/page identity, schema version and optimistic version.
Prefer a normalized field on the existing page record when safe; any alternative
must preserve page deletion/restore/dependency/COW semantics without orphan rows.

GET/PATCH `/api/agent/v1/pages/{page_id}/style` are the bounded public operations.
GET requires `page:read`; PATCH requires `page:read`, plus `page-style:write`
only when stored override/inheritance state changes. Use a positive expected
version and Idempotency-Key. No page:write, theme-tokens:write or unrelated L4
scope substitutes for page-style:write or is unnecessarily added to a narrowed
style capability. Canonical OpenAPI/route policy/handlers must match both ways.

PATCH uses closed partial token groups plus an explicit bounded reset-to-inherit
mechanism, e.g. a unique enum `reset_tokens` list using the nine theme token keys.
Reject update/reset overlap, unknown keys, null-as-silent-ignore, wrong types,
raw style/URL/code and unbounded input at HTTP AND trusted SQL. Read pure defaults
must not materialize data, increment versions, consume mutation quota or audit.

No-effect means no change to RAW stored override/inheritance state. Setting an
explicit value equal to today's inherited value is still a meaningful change
(future site-theme changes will no longer flow through it) and requires write
authority. Resetting an explicit value to inherit is similarly a real change.
Do not classify no-effect merely by comparing today's computed pixels.

## Authority, transaction and lifecycle

Use existing trusted SiteContext, capability/workspace rechecks and exact
page/subtree/route/locale resource confinement. Trusted SQL checks identity,
scope, complete final schema and raw ADD/CHANGE/REMOVE/reset transitions under
deterministic locks; Python-only enforcement is insufficient.
Existing theme token/palette/family allowlists also constrain changed page-style
selections, including a reset's resolved destination; this must not become an
alternate route around those bounds. Apply write constraints to changed keys,
not to mere reads/no-effect of already-visible inherited state.

Reuse lifecycle-before-structural/resource/COW lock ordering. Do not create
row-lock conversion deadlocks. One changed operation atomically gives one
version increment, mutation quota charge, COW operation, idempotency result and
named semantic audit event such as PAGE_STYLE_UPDATED. Exact replay has no
second effect; same key/different request409; stale version409; no-effect has
no mutation/audit/COW effect; cancellation rolls back all durable effects.

Page-style state follows page archive/delete/restore exactly. A deleted/invisible
page cannot be read or styled; restore preserves its valid style. Existing page
CRUD, routes, navigation and component semantics must not break. Concurrency
with page move/delete/update must yield an architecturally valid serialized
result, not orphan style state or a rendered page inconsistent with its metadata.
If using page's existing version, style changes participate in its optimistic
version contract; make response/version semantics explicit and test them.

Use an append-only migration after verified head065 only if needed. Preserve
all existing data/FKs/functions/return shapes/grants and COW hardening. Changing
page columns must not break legacy SELECT-star wrappers. Require safe rejection
of incompatible/pending COW, no CASCADE loss, and genuine fresh-baseline
data-bearing upgrade/downgrade/re-upgrade with exact replaced-function metadata.

## Shared rendering and human editing

Resolve defaults in a single trusted shared path:
site theme → explicit page overrides → explicit component-local/responsive
values. Inherited tokens follow site-theme changes; explicit overrides do not.
Reset resumes inheritance. Preserve raw site theme and raw page styles as
distinct records; publish exact resolved values/versions internally for Render,
not raw private projections or IDs in visitor HTML. Only fixed trusted CSS/assets.

Existing human Editor/Puck controls use the same schema and HUMAN-workspace
policy; a minimal per-page control surface is sufficient. Crafted unauthorized
Editor writes are denied. Component save/move must preserve page style state.
No Objective081 exact-Agent-workspace Puck selection or publication feature.

## Required production-boundary proof

Use actual public Agent APIs with human-issued narrowed capabilities and real
PostgreSQL; direct runtime tests supplement, never replace the passing path.

1. Discover/read inherited defaults, set representative overrides in all four
   groups, read exact raw/resolved state and versions, and observe actual SAME
   Agent workspace preview DOM/computed styles through NGINX. No DOM/class
   injection or owner-seeding of claimed outcomes. Assert canonical, another
   page, workspace and site unchanged. Negative sensitivity control must detect
   a deliberately wrong default-only render; restore and pass real output.
2. Change site theme through its separately authorized public operation: inherited
   page values follow, explicit page values remain; reset then follows. Local
   component/responsive overrides retain their accepted precedence.
3. Read-only/L1/L2 denial of changed styles, narrowed L3 success, unrelated-scope
   substitution denial, foreign page/site/workspace and resource filters,
   expired/revoked/frozen/deleted-page/quota denial; invalid types/null/reset/
   executable data at HTTP and trusted SQL, with exact errors/no residue.
4. Distinguish real inheritance changes from no-effect, exact replay/mismatch/
   stale responses and audit identity/quota/COW accounting. Real DB barriers
   prove same-version competing changes and style-versus-page deletion/update;
   cancellation and actual service restart preserve correct isolated state.
5. Human Editor/Puck round-trip/permission preservation and actual renderer
   inheritance/reset/precedence, plus full data-bearing migration continuity.

Run focused proof before broad CI; wire focused page-style PG tests into CI.
Reuse the accepted theme tests/generators and public preview fixture. Do not
expand a monolithic test file with unrelated refactors. Existing required CI
can supply broader matrix/Compose coverage without redundant local full suites.
Every claim maps to named assertions; screenshots/classes alone are insufficient
when a wrong rendered output would still pass.

## Size, safety, documentation and delivery

Aim for one small schema/API/DB/renderer increment; reassess at20–30production
files or several thousand substantive lines. Report production/migration/test/
generated/docs counts separately. No new semantic family, dependencies, security
exceptions, weaker gates, raw browser tool, globals/header-footer, catalog,
media/MCP, lifecycle/publication/reconstruction or unrelated cleanup.
Routine safe setup belongs to the existing coder's passwordless-sudo VM.

Commit the supplied `oap/audits/078-3-strategic-acceptance.md` unchanged.
Reconcile current increment/MVP/API/testing docs with PR79/80's actual merges and
this new bounded PR; preserve all historical orders/reports. Verify the PR
description by reading it back from GitHub; do not claim an update after a
failed CLI call (the REST PR API is an available fallback).

Fetch main, create the new branch and exactly one PR; commit exact order and
`oap/active=078-v` unchanged, implement/verify/push and repair concrete in-scope
defects. Never merge/auto-merge or launch/replace an agent. Publish
`oap/reports/078-v-bounded-page-style-overrides.md` as a final report-only SELF
child of a literal pushed implementation SHA, with exact identity, scope/size,
assertion-based evidence, checks and honest limitations. Lint Markdown before
publication. Send exact responseFIFO OK, then wait on a REAL byte-reading
control listener, not open-only exec. Strategy alone accepts/merges.

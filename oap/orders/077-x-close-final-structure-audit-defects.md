# OAP Work Order — 077-x

## Objective and frozen PR state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`f9843388264753ccd0379495f8f51ef101bd4c4c`, whose sole parent is 077-w
implementation `6c264b1c876f5467a6b8e57a4f81051fd5e20b18`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

PR #74 is feature-frozen. Strategic hostile audit found one production
structural-integrity defect and missing explicit 077-t hostile evidence. Repair
only these existing Objective-077 requirements. Do not add a feature. Round
077-y is reserved for final audit/truth-document reconciliation; do not perform
that reconciliation here.

## 1. Prevent navigation-to-dynamic-page state that Render cannot use

Current `content.slaif_agent_navigation_validate_target` accepts a `PAGE`
target whenever `slaif_agent_page_accessible` is true. That predicate permits
the terminal `{slug}` page itself. Render later resolves a PAGE navigation
target through `slaif_agent_page_effective_route`, then rejects `/news/{slug}`
as a concrete internal link. The public mutation can therefore succeed while
making the same workspace's Render projection fail.

Enforce at the trusted PostgreSQL mutation boundary that a `PAGE` navigation
item references an exact, concrete, site-bound, visible page route. A terminal
dynamic template is not a concrete navigation destination because the item
contains no slug binding; reject it. Preserve valid static PAGE targets and
existing safe INTERNAL/EXTERNAL semantics.

Also prevent a referenced static page from being PATCHed into `{slug}` while a
navigation item targets it. Keep allowed static route/move changes coherent:
the navigation item's PAGE identity should resolve to the new concrete route.
The rule must cover create and update of navigation items, page route-template
PATCH, and any equivalent trusted path—not an HTTP-only precheck.

Use a new exact reversible migration/helper replacement if needed; do not
rewrite earlier migration history merely to hide the repair. Preserve owners,
`search_path`, PUBLIC/runtime grants, COW hardening and exact downgrade. Update
bootstrap head/compatibility tests accordingly.

Add real public-Agent/PostgreSQL tests for:

- navigation create/update targeting a dynamic page is rejected without quota,
  idempotency, audit or COW residue;
- static PAGE target remains renderable after an allowed page move/route change;
- static referenced page -> dynamic PATCH is rejected with all state unchanged;
- deterministic concurrent navigation-create versus static->dynamic page PATCH
  under the structural lock yields exactly one coherent terminal state:
  static+navigation or dynamic+no-navigation; and
- owner-seeded corrupt dynamic PAGE navigation still makes Render fail closed
  without leaking identifiers or returning partial navigation.

No timing sleeps are concurrency evidence. Assert exact final page,
navigation, route, audit, idempotency and quota state.

## 2. Complete the already-required dynamic-detail hostile matrix

077-t explicitly required negative evidence that is not present in the current
focused dynamic tests. Add one bounded real-PostgreSQL Render matrix, using
neutral owner corruption only for states public APIs correctly prevent, that
proves:

- a detail item excluded by the stored bounded collection-view filter is 404;
- a dynamic page with zero, multiple, non-CollectionDetail, malformed, or
  wrong-view detail bindings is wholly 404/fail closed;
- static/dynamic effective-route overlap and multiple matching dynamic
  candidates fail closed deterministically rather than UUID-order selection;
- foreign-site, deleted/tombstoned, wrong-type or stale view/type/item
  associations cannot render;
- missing, duplicate/corrupt, wrong-site or invalid required translations fail
  closed, while the valid selected/default fallback proven by 077-v remains;
- canonical DRAFT/ARCHIVED/unknown and preview ARCHIVED/unknown remain 404;
- undeclared projection, localized filter/sort, extra/encoded/overlong slug,
  extra segment, query-string and SQL/JS/template payload attempts never widen
  selection or execute behavior; and
- a failure returns no partial page/binding/navigation state and leaves all
  pools reusable.

Tests must hit the production `RenderProjectionService`/HTTP behavior and the
real PostgreSQL functions. Source inspection or simply asserting helper
existence is not evidence. Do not create a new public route or query operator.
If a matrix case reveals a production defect, repair the smallest shared
trusted resolver/binding path in this same round and report it precisely.

## 3. Continuity, verification and report

Preserve every accepted 077-a through 077-w behavior: public page/locale/
navigation/redirect APIs, scopes/resources/quotas/idempotency/audit, structural
locks, COW/canonical/site/workspace isolation, exact OpenAPI/route-policy drift,
dynamic list/detail/localization, browser evidence, preview cancellation,
renderer CSS/locale/privacy parity, migration 055/056 restoration, restart and
zero-Critical supply chain.

Run focused navigation/page/dynamic hostile/concurrency/migration/privilege/
Render tests, then full Python quality/unit/integration and PG14–18, Node and
renderer/browser tests, repository/Markdown/Mermaid, clean Compose public
acceptance, all six-image zero-Critical evidence, and every current-head GitHub
check. Pending/skipped/superseded is not pass.

Do not modify final MVP truth ledgers or PR body yet; do not add 078+ behavior,
composition/design/Puck, media, MCP, freeze/review/promotion, source/sweep,
dependencies/images/exceptions/architecture, or general cleanup. Preserve
Chrome `152.0.7977.82`, empty exceptions and open issue #67.

Commit this exact order and `oap/active` unchanged, amend only PR #74, create no
PR and never merge. Publish exactly
`oap/reports/077-x-close-final-structure-audit-defects.md` as a report-only
child of the literal implementation SHA with `Report publication commit:
SELF`. Report exact functions/migration/grants/downgrade; each navigation and
dynamic hostile result; concurrency barriers/final state; residue/pool/
isolation evidence; commands/counts/skips/current checks; scope/no-secret/no-
extra-PR/no-merge; and the strongest remaining reason not to accept Objective
077.

Do not return early for ordinary implementation/test/CI failure or task size.
`PARTIAL`/`BLOCKED` requires a concrete external outage or unresolved product/
architecture decision. No post-report push; signal exact FIFO `OK`, then wait.

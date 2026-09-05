# OAP Work Order — 077-k

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`a51e5d278ac0505a4fc770f75e82af49a3f3693d`, whose sole parent is accepted
077-j implementation `f4a8a5a2c0663ef5fae5c44666e1b45e03face1b`.
Remote `main` remains Objective 076 merge
`067676314e0d9664d40cb8514ea549b966a4eb2d`.

077-j is closed for progression. This round is the next dependency-correct
Objective 077 slice: replace the Render service's obsolete flat-slug lookup
with the trusted static information-architecture router, and project the
workspace's locale/navigation/redirect structure coherently. It deliberately
does not implement `{slug}` collection-detail matching; that remains the next
077 slice. Preserve every valid 077-a through 077-j behavior.

## 1. One authoritative static route decision

Current `render_api/projection.py` strips the domain prefix, turns the entire
remaining path into one slug, and queries `content.page.slug`. That cannot
resolve the hierarchy and locale routes now enforced by migrations 049–051.

Implement one bounded trusted route-resolution path used by canonical, human
preview, and browser preview:

- resolve by the same effective page route semantics as the production page
  model, including `/`=`home`, ancestors, enabled locale state, and the
  non-default locale prefix;
- use `content.site_locale` inside the selected canonical/COW read context as
  locale truth; do not use stale canonical `SiteContext.default_locale` to
  override a workspace default-locale change;
- normalize and strip only the trusted domain/path mapping; reject encoded
  separators, dot/control/query tricks, reserved application paths, and any
  inconsistent explicit locale rather than selecting another page;
- return only `PUBLISHED` canonical pages and only `PUBLISHED`/`DRAFT` active-
  preview pages; deleted, disabled-locale, foreign-site, foreign-workspace, and
  unknown pages are 404;
- match a static route exactly and fail closed on corrupt ambiguity instead of
  ordering by UUID; and
- keep a terminal `{slug}` page unresolved/404 in this round. Do not implement
  a partial dynamic match without its collection binding and item-status proof.

Do not reproduce route derivation independently in Python and SQL. Reuse the
authoritative effective-route function behind a narrow Render resolver, or
factor one shared trusted helper with exact grants. Never expose an arbitrary
page-ID SECURITY DEFINER oracle to public callers. Render readers remain
read-only and gain only the minimum resolver EXECUTE/SELECT authority.

The page projection must expose its parent, route template, and exact effective
route so the caller can observe the same hierarchy/route it created through the
Agent API. Preserve the existing composition/catalog/theme contract.

## 2. Locale and navigation projection

Replace untyped container-only navigation output with a bounded typed
projection of the complete visible site navigation structure:

- include enabled locales in deterministic configured order, identify exactly
  one default locale, and return the route-selected locale in its stored
  canonical tag form;
- include each navigation container plus all its items, parent/child structure,
  deterministic dense sibling order, locale visibility, resolved label, and
  safe resolved target;
- a container label resolves as requested-locale label, then default-locale
  label, then its bounded base label; an item is visible only when its optional
  locale is null or the selected locale, and its label resolves requested then
  default. Preserve the bounded raw label map if needed, but never invent a
  label or leak another site's data;
- `PAGE` targets resolve from their site-bound page ID to that page's current
  effective route; `INTERNAL` targets remain normalized declared site routes;
  `EXTERNAL` targets remain validated HTTPS values; and
- fail closed on dangling/foreign pages, disabled locales, cycles, duplicate
  IDs/positions, excessive depth/count/JSON, executable values, or any state
  that disagrees with the selected page/router snapshot.

Use documented product bounds and the existing trusted schemas. A Render
projection is not capability-filtered—the authorized preview represents the
whole selected workspace—but it is strictly site/workspace confined.

This is projection/router work, not new Agent navigation mutation behavior and
not Objective 078 composition/design work. Do not add a new generic query,
template, component, CSS, Puck, or arbitrary layout mechanism.

## 3. Redirects must affect the real route

Make the redirects already created by Agent/Editor operations observable at the
trusted Render/Web route boundary:

- resolve exact source route for the selected locale, preferring an exact
  locale row over the locale-neutral fallback deterministically;
- emit the configured safe target and exact allowed HTTP status
  `301|302|303|307|308`; do not render a page at a redirect source and do not
  convert every redirect to one framework-default status;
- preserve the trusted site path prefix for canonical internal targets and
  preserve `/preview/<workspace-id>/...` for preview internal targets, so a
  preview redirect cannot escape into canonical content; external HTTPS targets
  remain external;
- never expose internal service URLs, credentials, workspace state, or raw
  database errors in the redirect response; and
- retain migration 051's transactional graph validation as write-time truth,
  while the read path still fails closed on any corrupt collision, ambiguity,
  dangling edge, cycle, overlong chain, unsafe target, or cross-site reference.

Use a typed discriminated Render route result (or an equivalently strict
contract) so Web cannot mistake redirects for pages. The public NGINX→Web path,
not only a direct Python service call, must demonstrate the actual status and
`Location`. Preserve private/no-store/noindex headers on preview and internal
Render traffic and the existing canonical cache behavior; no token may enter a
URL, body projection, HTML, log, or redirect target.

## 4. Coherent read snapshot and isolation

Canonical page, route, locale, navigation, composition, theme, and bindings
must come from one coherent read-only database snapshot. Preview must obtain the
same projection through one authorized COW session/snapshot after its existing
authorization/recheck. A concurrent committed structural mutation may yield
the complete before-state or complete after-state, never a page from one state
with navigation/locale/redirect from another. Cancellation must close/rollback
the read transaction and return the pool connection cleanly.

Do not acquire mutation authority, consume Agent quota/idempotency, write audit,
or take a long-lived structure lock for ordinary rendering. Preserve public
canonical isolation, other-workspace isolation, site confinement, browser-run
credential binding/one-time use, human session authorization, service-to-
service authentication, pool identities, and fail-closed error mapping.

## Acceptance evidence

Add focused real-PostgreSQL production-boundary tests. A real human-issued
capability must use public Agent FastAPI operations—not direct mutation helpers
or owner DML—to create/mutate a nested static page tree, switch/add locale
state, create/reorder localized navigation, and create a redirect. Then prove:

1. authorized human and browser preview resolve `/`, nested routes, and a
   non-default locale route with exact page/effective-route/locale/navigation;
2. move, navigation reorder, locale default change, delete and restore become
   visible in that same workspace Render projection while canonical and a
   second workspace/site remain unchanged;
3. canonical rendering continues to resolve its published hierarchy and never
   sees unpromoted Agent state;
4. the public NGINX/Web path returns the configured redirect status and safe
   location, including a preview-internal redirect that stays in the preview;
5. unknown, deleted, disabled-locale, malformed/reserved, ambiguous/corrupt,
   foreign, and dynamic-template paths fail closed without identifier/token/
   state leakage;
6. navigation includes all ordered nested items and rejects/fails closed on
   seeded corrupt dangling/cyclic/cross-site/excess-bound state;
7. deterministic PostgreSQL transaction/event barriers prove concurrent
   structure commit versus Render produces only a coherent before/after
   snapshot, never mixed state; no timing sleep is concurrency evidence; and
8. cancellation and Render restart leave no connection/context residue and the
   same active workspace still renders.

Neutral owner SQL may seed canonical state, deliberately corrupt negative
fixtures, coordinate barriers, and assert isolation; it cannot perform the
claimed Agent behavior. Direct projection tests are supplemental, not a
substitute for Agent HTTP → authorized Render/preview → public Web evidence.

Run focused Render/site-router/navigation/redirect/auth/COW tests; complete
Render and Agent integration regressions; Python quality/unit/integration;
Node renderer/Web contracts; route-policy and canonical Agent OpenAPI drift
checks (the Agent public surface must remain exactly unchanged); migration
upgrade/downgrade/re-upgrade and Render-role privilege proof if SQL changes;
PG14–18; repository/Markdown/Mermaid/supply-chain gates; and clean Compose
public acceptance. Push before observing current-head CI and repair only
in-scope failures. Do not weaken or skip a gate.

## Boundaries and report

No dynamic `{slug}` item selection or localized collection-detail binding yet;
no new Agent mutation route; no 078 composition/design/Puck; no media/MCP;
no freeze/review/promotion; no source/sweep; no 076 reopening; no dependency,
image, exception, architecture, historical-order/report, general refactor,
issue-closure, production-access, release, or unrelated cleanup change. Preserve
Chrome `152.0.7977.82`, zero current Critical findings, and the empty exception
set. GitHub issue #67 remains open until the containing Objective 077 commit is
merged to verified `main`.

Commit this exact order and `oap/active` unchanged with the bounded change,
push only the existing branch, create no PR, never merge/auto-merge, and repair
in-scope current-head failures before reporting. Publish exactly
`oap/reports/077-k-render-structure-router.md` as the final report-only child of
a literal implementation SHA with `Report publication commit: SELF`. Include
exact commits/files/migrations/helpers/grants/contracts; route/locale/nav/
redirect decisions; Agent→preview/public evidence; isolation/snapshot/
cancellation/restart results; commands/counts/skips/current checks; unchanged
Agent OpenAPI inventory; no secret/private authority/scope drift/extra PR/
merge; remaining dynamic-detail and final Objective 077 scope; and the strongest
reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker with
exact attempted evidence. Do not return because implementation/tests/CI are
long. No post-report push. Signal exact FIFO `OK`, then wait for strategic
review.

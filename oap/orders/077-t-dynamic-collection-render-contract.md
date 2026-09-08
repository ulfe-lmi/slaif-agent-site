# OAP Work Order — 077-t

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`a12bd51f22a70f10f0851d524695a96bd097941e`, whose sole parent is accepted-
for-progression 077-s implementation
`0d72cc2b61d235b119e569b22e7c2f53e5388103`. Remote `main` remains
`067676314e0d9664d40cb8514ea549b966a4eb2d`.

077-s closes the static Render/race/security recovery slice. This round
implements the final missing substantive Objective 077 feature: bounded dynamic
collection listing/detail routing such as `/news/{slug}`, created as workspace
data through the public Agent API and observed through the same trusted Render/
Web preview. Also correct the exact 055 downgrade restoration defect found by
strategic review. A later round will perform the final hostile whole-objective
audit; do not claim Objective 077 merged or closed here.

## 0. Correct migration 055 downgrade restoration

Current 055 downgrade drops
`content.slaif_redirect_page_target_dependency(uuid,text,uuid)` and does not
recreate migration 051's implementation; it also leaves the 055 shared-mode
`control.slaif_human_editor_workspace_assert` installed at revision 054 instead
of restoring the prior function. The comment claiming a preceding migration
will recreate the helper is false for a one-step 055→054 downgrade.

Make 055 downgrade restore both exact 054-state function definitions, owners,
`search_path`, PUBLIC/runtime grants and lock mode. Add a real 054→055→054→055
function-definition/privilege/data round trip. Preserve pre-070 migration bytes,
fresh-install semantics and 055's production behavior at head. No `CASCADE` or
silent dependent-object loss.

## 1. Trusted dynamic route resolution

Extend the one Render route resolver used by canonical, human preview and
browser preview. Preserve exact static and redirect behavior, then support only
the already-valid page contract whose terminal `route_template` is literal
`{slug}`.

- Match the fixed effective prefix plus exactly one nonempty terminal item-slug
  segment. Reject extra segments, repeated/renamed placeholders, wildcards,
  encoded separators, dot/control/query/fragment tricks, reserved paths and
  unsafe/noncanonical slugs. Use a bounded ASCII route-segment grammar such as
  `^[a-z0-9][a-z0-9._~-]{0,254}$`; unsafe content-item slugs remain unroutable.
- Resolve the page in the selected enabled locale using the same hierarchy/
  default-locale semantics as static routing. Dynamic pages remain leaves.
- Static exact match has deterministic precedence, but any corrupt static/
  dynamic overlap or multiple dynamic candidates fails closed; never order by
  UUID and pick one.
- Return a typed route parameter (`slug`) and actual matched path while retaining
  the page's template effective route. Do not accept type/view/item/query/site/
  workspace IDs from the public path or query string.
- Keep route resolution inside the same canonical/COW repeatable-read snapshot
  as page/composition/content/navigation/theme projection and preserve
  read-only Render grants.

Use one narrow trusted database resolver or a shared authoritative helper; do
not duplicate divergent route grammar across Python/SQL/Web. Exact migration
upgrade/downgrade and reader-role privileges are required.

## 2. CollectionDetail must bind exactly the routed item

A dynamic page is routable only when its normalized composition contains
exactly one trusted `CollectionDetail` node. That node's `viewId` is the sole
declarative binding authority:

- resolve a same-site ACTIVE collection view and ACTIVE content type with exact
  definition version;
- validate its existing bounded filter/sort/projection/pagination DSL; no raw
  SQL, operator registration, callback, template, expression, arbitrary query
  parameter or execution behavior;
- select only the unique same-site/same-type content item whose exact slug is
  the route parameter and which passes the view filter;
- canonical accepts only `PUBLISHED`; preview accepts `PUBLISHED` and `DRAFT`;
  `ARCHIVED`, deleted, unknown, wrong-type, cross-site, stale-definition, or
  filter-excluded detail returns 404 for the whole route, not an empty detail
  shell; and
- bind exactly one item to the detail node. Listing/grid components retain
  bounded sort/pagination and never inherit the detail route parameter.

Projection may include localized fields. Extend the declarative collection
projection contract to permit a declared localized field while continuing to
forbid localized filter/sort. Validate base nonlocalized values and translation
values against their field definitions. Resolve localized output as exact
selected-locale translation, then explicit default-locale fallback when the
selected locale differs; never merge another arbitrary locale. Missing required
localized output, duplicate/corrupt translation, executable content or invalid
field/type/version fails closed. Return only declared projection fields plus
the stable item metadata already in the binding—no hidden fields or internal
rows.

Use the same validated binding implementation for `CollectionList`,
`CollectionGrid` and `CollectionDetail`; detail mode may optimize the exact
slug lookup but cannot bypass DSL/type/site/status/version/translation checks.
Enforce existing candidate/result/query/JSON/time bounds and deterministic
ordering.

## 3. Public Agent → same-workspace Render proof

A real human-issued L4 capability must build a News fixture entirely through
the public Agent FastAPI surface:

1. create the `news` content type as data, including at least one nonlocalized
   sortable field and localized `title`/`summary` fields;
2. create `PUBLISHED`, `DRAFT`, and `ARCHIVED` items plus exact/default locale
   translations;
3. create a collection view with bounded filter/sort/projection/pagination,
   including the localized fields;
4. create `/news` and its leaf detail-template page, using the existing public
   page API and literal `{slug}` template;
5. add existing trusted `CollectionList` and `CollectionDetail` nodes through
   the existing public component-create operation—do not add component update/
   move/design semantics belonging to 078; and
6. add the listing page to navigation through the public Agent API.

Then prove through authorized human preview, run-bound browser preview and the
public NGINX→Web renderer:

- `/news` renders a bounded sorted localized listing;
- `/news/published-item` and `/news/draft-item` render the exact localized
  detail in preview; archived/unknown/filter-excluded are 404;
- actual HTML uses the trusted CollectionList/CollectionDetail React renderer
  and contains expected title/summary without tokens/internal IDs/raw JSON;
- item slug/status/translation changes through Agent HTTP move availability to
  the exact new route/content, with old/unpublished routes 404;
- canonical remains byte/semantically unchanged and does not see any Agent-
  created route/item/component/navigation before later human promotion;
- a separately authorized same-site workspace and another site see none of the
  overlay; wrong human/browser workspace/site/route credentials are
  indistinguishable from absent; and
- Render/Agent/Web restart preserves the workspace result and isolation.

Neutral owner SQL may create identity, membership, canonical comparison
fixtures and negative corruption. It may not perform any claimed Agent model/
item/translation/view/page/component/navigation write. A direct projection
test is supplemental, not a substitute for public Agent writes and intended
Render/Web interfaces.

## 4. Negative, concurrency and cancellation evidence

Cover at least:

- malformed/unsafe/overlong item slugs and dynamic paths; extra path segment;
  static/dynamic ambiguity; zero/multiple/wrong component detail binding;
- foreign/stale/deleted view/type/item/translation/component association;
  missing required translation and deterministic default fallback;
- canonical DRAFT/ARCHIVED/unknown 404 and preview ARCHIVED/unknown 404;
- filter-excluded detail 404; projection of undeclared fields denied;
  localized filter/sort denied; hostile SQL/JS/template/query/query-string
  attempts never execute or change selection;
- bounded candidate/result/projection/translation/JSON/query complexity;
- concurrent item slug/status/translation update versus detail Render using a
  real snapshot/event barrier: one complete before or after result only;
- detail Render racing item delete, view/type definition change, or route move:
  only coherent before/after/404 outcomes, never mismatched page/item/view;
- cancellation during exact detail selection/translation projection closes the
  transaction/COW context, leaves pools clean, consumes no mutation quota/audit,
  and permits a later render; browser token semantics remain exact.

No timing sleep is concurrency evidence. Preserve lifecycle shared locks,
structural/type dependency locks, 054 touch/recheck, all page/locale/nav/
redirect invariants and canonical isolation.

## 5. Contracts, docs, verification and boundaries

No new public Agent route is expected. If public schemas change because
localized collection projection is now valid, regenerate canonical Agent
OpenAPI from production handlers and preserve handler↔route-policy↔OpenAPI
bidirectional drift checks. There must be no schema-only or undocumented route.
Update API/Render/content-model/testing/MVP status docs only for behavior now
implemented; keep Objective 077 open until strategic final audit/merge.

Run focused dynamic route/list/detail/localization/status/filter/security/
isolation/concurrency/cancellation/migration tests; full Agent/Editor/Render/
bootstrap integration; Node trusted renderer and browser E2E; exact public
NGINX journey; OpenAPI/route policy; PG14–18; Python quality/unit/integration;
repository/Markdown/Mermaid; clean Compose/restart/recovery; complete zero-
Critical supply chain; then all current-head CI. Push before observing CI and
repair only in-scope failures. No pending/skipped/superseded result is pass.

No component update/move/delete or design/Puck work from 078; no media 079; no
MCP 080; no exact Agent-workspace Puck 081; no freeze/review/promotion 082+;
no source/sweep 087; no new primitive/operator/executable code input; no broad
refactor, dependency/image/exception/architecture/historical order/report/
production/release/issue-closure change. Preserve all six zero-Critical images,
Chrome `152.0.7977.82`, empty exceptions and GitHub issue #67 until verified
Objective 077 merge.

Commit this exact order and `oap/active` unchanged, push only the existing PR,
create no PR, never merge. Publish exactly
`oap/reports/077-t-dynamic-collection-render-contract.md` as the final report-
only child of a correct literal implementation SHA with
`Report publication commit: SELF`. Include exact migration/functions/grants/
route result/binding/localization/status design; public Agent operation and
OpenAPI inventories; listing/detail HTML and 404 cases; workspace/site/
canonical/restart isolation; races/cancellation; 055 downgrade round trip;
commands/counts/skips/all current checks; security/no secret/no extra PR/merge;
remaining final hostile 077 audit; strongest reason not to accept.

Do not return early for ordinary code/test/CI failures or task size. `PARTIAL`/
`BLOCKED` requires a genuine external DB/GitHub/tool outage or an architectural
product decision that cannot be resolved from this order. No post-report push;
signal exact FIFO `OK`, then wait for strategic review.

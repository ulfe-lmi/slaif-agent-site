# OAP Work Order — 077-l

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`a24d9367b7668734605dab01c7310a4307d00e98`, whose sole parent is 077-k
implementation `1682327b78a83ef1eed2cde1312ee7def5c7e2c2`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

077-k delivered the static Render/router production substrate and all current-
head CI is green, but independent review does not accept that round yet. Its
report claims materially broader acceptance evidence than exists, and one
locale-filtering defect can make an unrelated locale unrenderable. Close these
specific static Render defects and proof gaps. This is not the dynamic `{slug}`
slice; do not begin that work here.

## 1. Fix locale-hidden navigation before projection validation

Current `_navigation` resolves and requires a selected/default-locale label for
every navigation item before applying item locale visibility. A valid item with
`locale="sl-SI"` and labels only for `sl-SI` therefore makes an `en` render fail,
although that item must be absent from the `en` projection.

Make locale visibility structural and deterministic:

- validate the complete stored tree for IDs, site/navigation association,
  parent integrity, cycles, depth, dense sibling positions, target safety and
  enabled locale references;
- apply selected-locale visibility before requiring selected/default display
  labels or resolving display-only data;
- emit only items whose own locale is null or selected, and never promote a
  visible child through a hidden parent; a selected-locale child under a hidden
  parent is omitted with that subtree or rejected by one documented invariant,
  but cannot leak or float to another position;
- require a usable selected/default label only for an item actually projected;
  do not invent or leak another-locale text; and
- retain fail-closed behavior for a visible item without a usable label and for
  all corrupt graph/target/bound states.

Add a regression with an `en`-only item and a `sl-SI`-only item (each lacking
the other/default label) proving each locale renders only its intended item and
that a locale-hidden subtree cannot break or leak into the other locale.

## 2. Prove every real redirect status and preview safety header

The order required the real public NGINX→Web boundary to preserve every allowed
status. Existing new evidence exercises only a preview `301`; direct Python
projection checks `301` and `307` but do not prove Web response handling.

At the actual public boundary, table-drive canonical and authorized human-
preview redirects for `301`, `302`, `303`, `307`, and `308`, with redirect
following disabled. Prove exact status and exact safe `Location` for internal
and external targets. Every preview-internal target must retain
`/preview/<workspace-id>` and the trusted site prefix. Every preview redirect
response itself—not merely the preceding page response—must carry private
`no-store` and `X-Robots-Tag: noindex, nofollow, noarchive`; retain CSP and other
edge security headers. No browser/human/capability/service token may appear in
the location, body, HTML, log, or response headers.

Do not rely on undocumented `next/dist/...` imports without pin-scoped contract
tests that fail if Next no longer honors the exact statuses. Prefer a stable
Web boundary if one exists. The Proxy must not pre-consume a one-time browser-
preview credential; prove the browser path still performs exactly one Render
authorization/consumption and returns its page or redirect correctly.

## 3. Supply the missing ordered production-boundary evidence

The 077-k report says its tests cover move/delete/restore, browser preview,
other-workspace/site isolation, coherent concurrent snapshots, cancellation,
restart, and corrupt navigation. The new `test_render_structure_router.py`
does not: its Agent journey creates pages/locales/navigation/redirects and
reorders one item, then performs direct human-preview projection. It has no
page move/delete/restore, no browser credential, no second workspace/site, no
concurrency/cancellation/restart barrier, and almost no corrupt-navigation
matrix. Existing Render tests changed only for the new `route_kind` field and
cannot be relabelled as new proof of these requirements.

Add focused, maintainable real-PostgreSQL evidence through the production
interfaces:

1. A real capability uses public Agent HTTP to move a nested page, delete and
   restore it, switch the default locale, and reorder localized navigation.
   Authorized Render preview must observe each exact hierarchy/route/locale/
   navigation transition; canonical remains unchanged throughout.
2. The same state is denied to a human/browser credential bound to a foreign
   workspace or site, while a separately authorized second workspace sees only
   its own overlay. Responses must not reveal IDs or distinguish foreign from
   absent state.
3. A genuine run-bound browser-preview credential renders the Agent-created
   nested route and localized navigation, remains site/workspace/route-bound,
   is consumed exactly once, and cannot be replayed. Do not substitute a human
   session or direct unprotected service call.
4. With deterministic PostgreSQL transaction/event barriers, pause a real
   canonical and preview Render after its repeatable-read snapshot is
   established while a public Agent/Editor structural mutation commits. The
   result may be the complete before-state or complete after-state only—never
   page/locale/navigation/redirect data from mixed states. No timing sleep is
   ordering evidence.
5. Cancel canonical and preview Render while the snapshot/projection is in
   flight. Prove the transaction/context is closed, the preview connection's
   isolation/session state is restored, the pool remains usable, no credential
   is accidentally consumed twice, and a subsequent authorized render works.
6. Restart the Render application/process boundary and show the same durable
   authorized workspace state still resolves while canonical remains isolated.
7. Seed only negative corruption fixtures with owner authority and prove
   dangling/foreign PAGE target, unsafe INTERNAL/EXTERNAL target, duplicate or
   non-dense position, missing/cross-navigation parent, cycle, excessive depth/
   count/JSON, disabled/unknown locale, duplicate default, and visible missing
   label all fail closed without partial projection or details. Also prove one
   corrupt/dynamic unrelated page cannot become an arbitrary match.

Instrumentation may expose deterministic test events around production query
stages; it may not mock away route, authorization, COW, transaction, database,
or projection behavior. Owner SQL is permitted only for canonical/identity/
credential fixtures, explicit corruption, barriers, and after-state assertions;
it cannot perform the claimed Agent mutations.

## 4. Migration, privilege, and scope continuity

Retain the narrow migration 052 resolver contract, exact public/preview reader
grants, COW-aware behavior, and downgrade/re-upgrade data/privilege proof. Check
that reader roles cannot DML, call Agent/reviewer/base/change functions, use the
resolver as a foreign-site arbitrary-page oracle, or select another workspace
by a supplied UUID. Do not broaden status/route parameters or trusted reader
authority to make tests easier.

Preserve one coherent repeatable-read snapshot, canonical/preview/browser auth,
no-store/noindex behavior, site/domain/path-prefix resolution, composition/
theme/collection-list behavior, route policy, and the unchanged canonical Agent
OpenAPI. Fix only concrete defects exposed by this review.

Run the focused regressions first, then the complete Render/Agent/Editor and
bootstrap integration coverage, Python quality/unit/integration, Node contracts,
actual public NGINX/Web redirect tests, migration/privilege checks, PG14–18,
repository/Markdown/Mermaid/supply-chain checks, clean Compose, and all current-
head CI. Push before observing CI; repair only in-scope failures. No skipped,
cancelled, inferred, or superseded result counts as pass.

## Boundaries and immutable report

No dynamic `{slug}` matching or collection-detail selection; no new Agent
route/mutation semantics except exercising existing page/locale/navigation/
redirect operations; no 078 composition/design/Puck; no media/MCP/freeze/
review/promotion/source/sweep/076 work; no dependency/image/exception/
architecture/historical-order/report/general-refactor/issue-closure/production/
release change. Preserve Chrome `152.0.7977.82`, zero current Critical findings,
and empty exceptions. GitHub issue #67 remains open until Objective 077 reaches
verified `main`.

Commit this exact order and `oap/active` unchanged, push only the existing PR
branch, create no PR, and never merge/auto-merge. Publish exactly
`oap/reports/077-l-close-static-render-gaps.md` as the final report-only child
of a literal implementation SHA with `Report publication commit: SELF`.
Report exact commits/files/tests/counts/current checks; before/after code defect;
all five public redirect outcomes and headers; Agent/human/browser/interface
paths; workspace/site/canonical isolation; snapshot barrier outcomes;
cancellation/pool/restart evidence; corruption matrix; migration/grants; no
secret/scope drift/extra PR/merge; remaining dynamic-detail and final 077 scope;
and the strongest reason not to accept. Do not claim a criterion from an older
test unless its exact current body proves that criterion and you cite it.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker and exact
attempted evidence. Do not return because implementation/tests/CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.

# OAP Work Order — 077-y

## Objective and frozen PR state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`452c938f7b0f4575afc85f93f9378fef6287849a`, whose sole parent is 077-x
implementation `f7627ce794db80f3e6d735648ada5cbf9b9b01a2`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

PR #74 is feature-frozen. This is the final permitted defect-repair round
before protocol-final 077-z audit/truth reconciliation. Do not add feature
scope. If this bounded repair exposes a fundamental unresolved issue, report it
precisely; do not manufacture a round after `z`.

## Defect

An Agent/trusted navigation `INTERNAL` target is accepted only when
`content.slaif_locale_route_exists` finds a concrete static page at that fixed
route. Unlike a `PAGE` target, it deliberately stores no page identity and
therefore does not follow a page move.

Current page route-affecting operations do not revalidate those stored fixed
routes. A page slug/locale/parent/template change, ancestor move, or delete can
commit while leaving one or more INTERNAL navigation items pointing to a route
that no longer exists. Current Render also syntax-validates INTERNAL targets
without proving they resolve in its selected canonical/preview status set.
This violates Objective 077's requirements against dangling navigation,
hidden deletion dependencies, and page/navigation/Render disagreement.

## Required production repair

Establish one trusted, bounded static INTERNAL-navigation graph validator and
apply it transactionally under the existing site/workspace structural lock.

- INTERNAL navigation targets must remain normalized, nonreserved, concrete
  static routes in the same site and current workspace graph; dynamic template
  placeholders and arbitrary undeclared paths remain invalid.
- After every Agent or human Editor page operation that can change an effective
  route or remove/restore a page—including slug/locale/template PATCH, move of
  a page or ancestor subtree, delete and equivalent trusted mutations—validate
  all affected fixed INTERNAL navigation targets before commit. If any would
  dangle, reject and roll back the complete operation.
- Preserve `PAGE` identity semantics from 057: valid PAGE targets follow static
  route moves, and dynamic PAGE targets remain rejected.
- Navigation create/update must use the same authoritative route-existence law,
  not a divergent copy.
- Render must fail closed on owner-corrupt/dangling INTERNAL navigation state
  and must not return a partial page/navigation projection. Its check must
  respect the Render status set so canonical output never emits an INTERNAL
  link whose only target is an unpublished/deleted page.
- Locale/default-locale operations already invoke the complete graph validator;
  preserve and unify that behavior rather than weakening it.

Use an append-only exact reversible migration/helper replacement as needed.
Preserve owners, `SECURITY DEFINER`, `search_path`, PUBLIC/runtime grants, COW
hardening, migration-head compatibility and exact downgrade/re-upgrade. Do not
rewrite 049–057 history.

## Required observable evidence

Through real public Agent HTTP and real PostgreSQL, prove:

1. create a valid fixed INTERNAL navigation item to a static page;
2. page slug/locale/template change, direct move, ancestor move and delete that
   would orphan that route are each rejected with page/subtree/navigation state
   unchanged and no quota/idempotency/audit/COW residue;
3. removing or retargeting the INTERNAL item permits the otherwise valid page
   operation, while a `PAGE` navigation item continues to follow a static move;
4. navigation create/update to absent, dynamic, foreign, wrong-workspace,
   reserved or unpublished-for-the-relevant-Render-context targets is denied or
   fails closed according to the exact existing mutation/preview/canonical
   boundary;
5. a deterministic concurrent INTERNAL-navigation-create versus page move/
   route-template/delete race yields exactly one coherent terminal graph, with
   no timing sleeps and exact durable audit/idempotency/quota state;
6. an INTERNAL item targeting a descendant blocks an ancestor move that would
   orphan it, proving subtree coverage; and
7. owner-seeded corrupt/dangling INTERNAL targets make production Render HTTP
   fail closed with no identifier, partial page, binding or navigation leakage,
   after which pools remain reusable.

Exercise the human Editor page/navigation functions or production HTTP path
where their existing route mutation can create the same inconsistency. Neutral
owner SQL is allowed only for corruption fixtures/barriers/assertions, never as
a substitute for claimed Agent behavior.

## Continuity, verification and report

Preserve all accepted 077-a through 077-x behavior, especially 057 PAGE-target
rules, route locks, dynamic hostile matrix, OpenAPI/policy continuity, COW/
canonical/site/workspace isolation, renderer/browser/privacy evidence,
migration restoration and zero-Critical supply chain.

Run focused Agent/Editor page-navigation dependency, concurrency, Render,
migration and privilege tests; full Python quality/unit/integration and PG14–18;
Node/browser/renderer; repository/Markdown/Mermaid; clean Compose public
acceptance; six-image zero-Critical supply-chain; and all current-head GitHub
checks. Pending/skipped/superseded is not pass.

Do not modify final MVP truth ledgers or PR body; add no 078+ behavior,
composition/design/Puck, media, MCP, freeze/review/promotion, source/sweep,
public route, dependency/image/exception/architecture, or general cleanup.
Preserve Chrome `152.0.7977.82`, empty exceptions and open issue #67.

Commit this exact order and `oap/active` unchanged, amend only PR #74, create no
PR and never merge. Publish exactly
`oap/reports/077-y-close-internal-navigation-dependencies.md` as a report-only
child of the literal implementation SHA with `Report publication commit:
SELF`. Report exact migration/functions/grants/downgrade; each Agent/Editor/
Render/concurrency result and terminal graph; residue/pool/isolation evidence;
commands/counts/skips/current checks; scope/no-secret/no-extra-PR/no-merge; and
the strongest remaining reason not to accept Objective 077.

Do not return early for ordinary implementation/test/CI failure or task size.
`PARTIAL`/`BLOCKED` requires a concrete external outage or unresolved product/
architecture decision. No post-report push; signal exact FIFO `OK`, then wait.

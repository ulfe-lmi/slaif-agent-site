# OAP Work Order — 077-a

## Contract and bounded first slice

Begin Objective 077, the contractual Agent information-architecture objective,
with its dependency-first production slice: exact public Agent page semantics,
page hierarchy, and derived route integrity. This round establishes the page/
route substrate on which later same-PR rounds will add locale, navigation,
redirect, dynamic collection-detail Render behavior, and final cross-surface
acceptance. A `COMPLETE` 077-a report closes only this named slice; it does not
close numeric Objective 077.

Architecture: `ARCHITECTURE-for-agents.md` §§3, 5–11, 14, 17–19, especially
page/route/locale, authorization, COW, audit, idempotency, quotas, structural
limits, rendering, and verification. Objective 076 is merged through PR #72 as
`067676314e0d9664d40cb8514ea549b966a4eb2d`.

## GitHub objective state and verified baseline

- Numeric objective `077`, round `077-a`, mode `CREATE_NEW_PR`.
- Create exactly one new Objective 077 PR from remote `main`
  `067676314e0d9664d40cb8514ea549b966a4eb2d`; no Objective 077 PR exists.
  Suggested branch: `oap/077-agent-site-structure-semantics`.
- PR #72 is merged; current remote `main` is its merge commit. No later product
  commit has superseded it. Existing unrelated Dependabot PRs are not in scope.
- Current Agent production surface has capability-bound page list and create,
  plus component list/create. It has no exact page GET, PATCH, DELETE, move, or
  restore route. `agent_http.py`, `route_policy.py`, and canonical
  `contracts/openapi/agent-v1.json` reflect that limited surface.
- Page creation currently reaches `slaif_agent_page_create` through
  `AgentCowContentModelService`; current page reads use
  `slaif_agent_page_list`. Page functions originate in migrations 021/025/026/
  027/029, while migration 042 provides fixed locale/navigation/redirect data.
  The current page record exposes a slug and parent but no reliable derived
  route contract. Render currently performs flat slug equality in
  `render_api/projection.py`.
- Objective 076's generalized COW/idempotency/quota/semantic-audit machinery is
  the mandatory mutation path. Page create still uses its legacy nonsemantic
  action path; this round must bring all page mutations onto the strict current
  contract rather than introduce a parallel executor.

## Objective 077 acceptance contract (reserved across 077-a..z)

Objective 077 is not complete until a real capability through the public Agent
API can inspect and mutate pages/hierarchy/routes, locale state, navigation
containers/items and redirects; create and use collection listing and bounded
dynamic detail routes such as `/news/{slug}`; observe the same active workspace
through the trusted Render/preview path; and prove canonical state unchanged.
The final objective proof must include wrong/lower scopes, foreign site/
workspace/resource, duplicate/reserved routes, cycles/depth/bounds, redirect
loops, stale versions, non-ACTIVE state, quota, replay/mismatch, malformed
templates, unknown/unpublished detail 404, arbitrary query/execution denial,
concurrency, cancellation, audit, and restart evidence. Production handlers,
route policy, and canonical OpenAPI must agree bidirectionally.

Do not claim this full contract from the narrower 077-a evidence.

## Required production behavior for 077-a

### 1. Exact public Agent page API

Implement typed production operations, preserving compatible trailing-slash
aliases only where they do not create ambiguous schema/policy entries:

```text
GET    /api/agent/v1/pages
POST   /api/agent/v1/pages
GET    /api/agent/v1/pages/{page_id}
PATCH  /api/agent/v1/pages/{page_id}
DELETE /api/agent/v1/pages/{page_id}
POST   /api/agent/v1/pages/{page_id}:move
POST   /api/agent/v1/pages/{page_id}:restore
```

List and exact read return only pages visible in the capability's site-bound
workspace. Mutations return the standard typed Agent mutation envelope with
server-owned operation ID and exact semantic action. PATCH uses an explicit
positive expected row version; it may change ordinary page metadata and the
bounded slug/route declaration, but never executable layout/query/code.

Move expresses semantic parent/relative placement intent, not a raw rank. It
updates one page's parent and atomically recalculates/validates the effective
route of that page and descendants. The response exposes enough normalized
hierarchy and effective-route data for a caller to observe the result.

DELETE creates a reviewable COW/domain deletion in this workspace: the page and
route become absent from Agent reads and active preview while canonical and
other workspaces remain unchanged. `:restore` reverses that pending deletion
for the same immutable page identity and prior hierarchy/route data. A safe
explicit domain tombstone is acceptable if it produces those exact external
semantics and can later promote/discard correctly; an unreviewable hard delete,
API-only hidden row, or fixture-only restore is not. Define and test exact
behavior for both a canonical page deleted in the workspace and a page created
then deleted in that workspace. Child/component/navigation dependencies must
not become hidden/dangling: reject deletion with a stable domain error unless
the operation atomically and explicitly handles the complete dependency.

### 2. Hierarchy and derived-route contract

- Treat a page slug as a normalized segment and derive its effective path from
  site, locale, and ancestors. Root/home convention and locale-prefix behavior
  must be deterministic and reflected in records/tests. No caller supplies a
  trusted effective route or site/workspace/session/operation identifier.
- Reject duplicate effective routes per workspace-visible site+locale,
  self/ancestor cycles, excessive depth, missing/foreign parent, reserved
  application paths, dot/empty/control/encoded separator tricks, and any route
  declaration that could be interpreted as regex, URL, query, filesystem path,
  SQL, JavaScript, or arbitrary execution.
- Keep the model forward-compatible with the Objective 077 dynamic detail
  contract: the only dynamic segment eventually permitted is the bounded
  literal terminal placeholder `{slug}`. Reject malformed/renamed/repeated/
  nonterminal placeholders, wildcards and catch-alls now. Define deterministic
  static-versus-detail precedence or reject overlap; never pick an arbitrary
  matching page. Do not implement Render detail projection in this round.
- Route-affecting PATCH requires both `page:write` and `route:write`; move
  requires `page:move` and `route:write`; create requires `page:create` and
  route validation; delete and restore require `page:delete` and
  `page:restore`, respectively. Any optional old-route redirect proposal must
  be explicit and additionally require `redirect:write`; it may remain for a
  later 077 round rather than being simulated here.

### 3. Trusted resource, lifecycle, quota, audit, and idempotency enforcement

- Extend the bounded capability constraint schema and trusted PostgreSQL helper
  only as needed for pages: allowed locales, route prefix/subtree restriction,
  page-root/subtree restriction, maximum visible pages, and maximum page depth.
  Unknown or malformed constraints fail closed. Enforce the same immutable
  constraints at the trusted DB mutation boundary; an HTTP-only check is not
  sufficient. Preserve existing type constraints unchanged.
- Every page mutation uses the generalized Objective 076 executor with one COW
  transaction, product workspace shared lock/state recheck, capability-derived
  site/workspace, server operation UUID, durable idempotency, wrapper-owned
  quota charge, and same-transaction semantic audit. Add strict actions such as
  `PAGE_CREATED`, `PAGE_UPDATED`, `PAGE_DELETED`, `PAGE_MOVED`, and
  `PAGE_RESTORED` with exact resource/method/status/quota mappings. Delete uses
  delete quota and existing `delete_enabled`/`max_deletes`; all others use the
  appropriate mutation/create bound. Replay consumes no second quota/audit/COW
  operation; same key with different request returns stable 409.
- Missing/wrong scope, foreign or invisible IDs, stale row version, invalid
  route/hierarchy, exhausted resource/quota, revoked/expired capability, lost
  delegator authority, and non-ACTIVE/frozen workspace fail before durable
  mutation completion and leave no unintended COW, audit, idempotency or quota
  residue. Cancellation rolls the complete transaction back.
- Preserve site-immutable composite relationships and current foundation public
  API boundary. Agent runtime receives only narrow trusted wrapper EXECUTE;
  `PUBLIC`, Agent, Editor, and Control gain no base/change/reviewer/schema/raw
  SQL authority. New or replaced SQL functions use deterministic ownership,
  `search_path`, grants, exact upgrade behavior, and exact downgrade restoration.

### 4. Transactional structural integrity

All route/hierarchy decisions must be authoritative inside PostgreSQL, not a
read-then-write Python race. Introduce one documented deterministic transaction
advisory-lock/order convention for the workspace-visible site structure after
the existing workspace lifecycle lock. Every page create/route update/move/
delete/restore that can affect the same effective route or tree participates.
Concurrent same-workspace operations must not create duplicate effective
routes, cycles, over-depth descendants, or orphaned dependencies. Independent
sites/workspaces remain isolated; different workspaces may legitimately propose
conflicting future changes for later review rather than seeing one another.

Use real PostgreSQL multi-connection tests with deterministic barriers/lock
coordination, never timing sleeps, for at least duplicate-create and competing
move/route-update races. Exactly one valid serialized outcome may win where
appropriate; the loser is a stable conflict/domain denial and final visible
tree/routes are coherent. Also prove cancellation while blocked/inside a
mutation leaves no residue and subsequent use succeeds.

### 5. OpenAPI and documentation continuity

Update the generated canonical Agent OpenAPI and route policies from the actual
production handlers. Preserve the bidirectional handler ↔ route-policy ↔
canonical-operation drift gate, exact bearer security/scopes, mutation and
Idempotency-Key metadata, typed request/success schemas, stable error envelope,
and public exact-byte endpoint. There must be no undocumented production route,
schema-only route, generic docs exposure, or internal COW/DB credential model.

Update `docs/API.md`, security/architecture-facing implementation notes, and
contract indexes only for behavior actually implemented in this round. State
that locale/navigation/redirect/Render dynamic-detail completion remains within
open Objective 077; do not claim all information architecture complete.

## Acceptance evidence for this round

A focused real-PostgreSQL test must obtain a real human-issued capability and
exercise the production Agent FastAPI handlers—not direct service/SQL helpers—to:

1. list and exact-read a canonical page through its workspace overlay;
2. create parent/child/detail-template pages, update a page, move a subtree and
   observe normalized hierarchy/effective routes;
3. delete and restore while proving exact workspace visibility and stable IDs;
4. restart the Agent service/process boundary and observe the same overlay;
5. prove canonical, a second workspace, and a second site unchanged;
6. prove exact idempotent replay/mismatch, strict audit/operation identity,
   wrapper-owned quota accounting, and cancellation rollback;
7. prove lower-preset/wrong-scope, route-prefix/page-subtree/locale limits,
   duplicate/reserved/malformed dynamic paths, foreign parent/page/site,
   cycle/depth, stale version, dependency, delete quota, and non-ACTIVE denials;
8. run the deterministic concurrent PostgreSQL races above.

Neutral owner SQL may seed canonical/site/control fixtures and assert isolation;
it may not perform any claimed Agent behavior. Mocks, test-only handlers,
Editor routes, direct mutation-service calls, or direct SQL calls are not
substitutes for public Agent semantic proof. Direct wrapper tests are additional
defense-in-depth only.

Run focused page/route/API/PostgreSQL/migration/privilege/concurrency tests,
then the complete Agent mutation/OpenAPI/route-policy regressions, full Python
quality/unit/integration and PG14–18 matrices as locally practical, repository
policy, and one relevant clean Compose/edge acceptance if the public journey is
extended in this slice. Push first; observe current-head CI and repair in-scope
failures within the turn. Report pending CI honestly; do not weaken tests,
checks, permissions, supply-chain evidence, or architecture to finish.

## Explicit non-goals and human risk decision

- No Agent locale/navigation/redirect surface yet except page dependency guards;
  no Render dynamic projection yet. Those are later substantive 077 rounds on
  this same PR, not omissions to disguise.
- No 078 composition/design/Puck work; no 079 media; no 080 MCP; no 081 exact
  Agent-workspace Puck; no 082+ freeze/review/promotion; no 087 source or
  responsive-sweep behavior; no broad cleanup/refactor or adjacent feature.
- Do not modify architecture, prior orders/reports, dependencies, image policy,
  release claims, or production systems/secrets/data.
- The human owner explicitly directs that Chrome/Chrome-for-Testing
  vulnerability-exception expiration and GitHub issue #67 are not to be
  addressed, investigated, refreshed, remediated, extended, or used to block
  Objective 077. Do not inspect newer Chrome versions or create/change an
  exception merely because of its date. Actually executed required CI/security
  checks remain authoritative; diagnose a concrete new failure normally. This
  decision does not authorize weakening any gate or suppressing other findings.

Routine packages, PostgreSQL instances, Docker/Compose, browsers, and test tools
belong to the disposable coding environment; passwordless sudo is available.
Do not transfer routine setup to the human.

## GitHub workflow and immutable report

Fetch/reconcile GitHub, preserve the complete activated order and `oap/active`,
and create the fresh objective branch from the exact verified remote `main`.
Implement only this slice; commit intended code/tests/docs plus the activated
transcript, push, and create exactly one new Objective 077 PR targeting `main`.
Never merge and never create another PR. Do not modify strategic-owned order or
active bytes.

Publish exactly `oap/reports/077-a-agent-site-structure-semantics.md` as the
last report-only commit and push it before signaling. Include outcome; exact
order hash; PR number/URL/state/base/head; branch; literal 40-hex implementation
SHA; `Report publication commit: SELF`; commits/files/migration/function/grant/
route/OpenAPI inventories; requirement-by-requirement evidence; exact local
commands/counts/results/skips; current-head checks; data-bearing upgrade/
downgrade evidence; concurrency/cancellation method and outcomes; audit/quota/
idempotency/COW/canonical/site/workspace proof; docs; scope/security/no-secret/
no-extra-PR/no-merge confirmations; known limitations; strongest reason not to
accept this slice; and the explicitly remaining Objective 077 scope.

`PARTIAL` or `BLOCKED` is permissible only for a concrete external/technical
blocker with exact attempted evidence. Do not return merely because the work or
tests are long. Do not write a no-op report. No post-report push. Signal exact
FIFO `OK` only after the immutable report and claimed remote state exist, then
wait for strategic review.

# OAP Work Order — 078-a

## Objective and verified GitHub baseline

Begin Objective 078 with its dependency-first production slice: complete the
capability-bound Agent normalized component data plane and one authoritative
trusted component-catalog contract. This round creates exactly one new PR. It
does not yet implement theme/global-region/header-footer/design-token or broad
responsive-design mutation; those remain later 078 continuations on the same
PR.

- Numeric objective: `078`; round: `078-a`; mode: `CREATE_NEW_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Start from verified remote `main`
  `ae3a4a681bb888260192b7bb1b2a337b4906828d`, the accepted Objective-077
  merge commit. PR #74 is merged and its accepted head is contained in main.
- No Objective-078 branch or PR exists. Create one fresh branch, suggested
  `oap/078-agent-composition-design-semantics`, and exactly one new PR targeting
  `main`.
- GitHub issue #67 is closed after the verified 077 merge; Chrome for Testing
  is `152.0.7977.82`, the exception set is empty, and all six accepted images
  have zero Critical findings. Preserve that state.

Current production Agent behavior lists and creates composition nodes under a
page. It has no exact component read, PATCH, DELETE, or move operation. Create
still uses a legacy untyped SQL wrapper, executor-owned quota, null semantic
audit action, raw integer ordering, no row version, and shallow duplicated
component allowlists. Human Puck/Editor has broader legacy mutation functions,
while Render and the TypeScript catalog independently encode catalog rules.
File presence and Puck UX are not Agent product proof.

## Objective-078 boundary

Objective 078 ultimately completes Agent composition and bounded design
semantics. This initial slice closes only:

1. a single versioned trusted catalog authority consumed/drift-checked by
   backend validation, Render, TypeScript/Puck and Agent discovery;
2. exact Agent component list/read/create/content-update/move/delete semantics;
3. transactional component-tree, binding, COW, scope, quota, idempotency and
   audit integrity; and
4. same-workspace Render/Web observation and hostile/concurrent evidence.

Later same-PR rounds add design-system/theme schema, variants/layout/responsive
props, theme/global regions/header/footer and final cross-surface audit. Do not
claim numeric Objective 078 complete from `078-a`.

## 1. One trusted component-catalog authority

Replace the currently drifting component/type/slot/prop rule copies with one
product-owned, versioned, machine-readable `catalog-v1` authority or an
equivalently strict generated source. It must be committed, deterministic,
permissively licensed product data/code, and consumed or exact-drift-checked by:

- Python Agent request/domain validation;
- trusted PostgreSQL mutation validation;
- Render projection validation;
- the TypeScript component catalog and Puck adapter; and
- generated public Agent discovery/OpenAPI contracts.

The authority must describe exact component type, category, schema version,
allowed parent slots, maximum children, prop names/types/requiredness/enums/
bounds/localization, binding kind, and mutation-authority class. No Agent/user
can add or alter catalog definitions, renderers, schemas, primitives, code or
packages.

Add capability-bound discovery:

```text
GET /api/agent/v1/component-catalog
```

It returns the exact active site catalog version and bounded definitions using
`component-catalog:read`; no filesystem/internal implementation path or code is
exposed. Existing session/catalog version continuity remains exact.

## 2. Exact public Agent component API

Preserve existing page-scoped list/create and add:

```text
GET    /api/agent/v1/components/{component_id}
PATCH  /api/agent/v1/components/{component_id}
POST   /api/agent/v1/components/{component_id}/move
DELETE /api/agent/v1/components/{component_id}
```

All return typed stable records/envelopes with site/page/component identity,
catalog/schema version, parent/slot/dense order, validated props, positive row
version and timestamps. Exact read returns only the capability's site/workspace
overlay and requires `composition:read`.

Bring existing create and every new mutation onto the generalized strict Agent
executor. Use exact semantic actions and method/status/quota mappings:

```text
COMPONENT_CREATED  composition_node POST   201 mutation
COMPONENT_UPDATED  composition_node PATCH  200 mutation
COMPONENT_MOVED    composition_node POST   200 mutation
COMPONENT_DELETED  composition_node DELETE 200 delete
```

Create requires `component-structure:create`; move requires
`component-structure:move`; delete requires `component-structure:delete` plus
existing delete policy/quota. This slice's PATCH is limited to catalog-declared
content props and requires `component-content-props:write`. Variant/layout/
responsive/theme/design prop changes must fail closed until later 078 scopes
and behavior are implemented; do not silently grant L1/L2 design authority.

PATCH and move require an explicit positive expected row version. Move accepts
semantic destination parent/slot plus at most one before/after sibling anchor;
the server assigns/rebalances dense order. Do not expose a trusted raw rank.
Define delete as leaf-only with a stable dependency error when children exist,
unless an equally explicit bounded subtree result/audit/dependency contract is
implemented and proved. A missing/foreign/wrong-page node is 404.

## 3. Trusted write-time catalog, tree and binding enforcement

At the PostgreSQL mutation boundary—not only Pydantic/Puck/UI—enforce:

- active site catalog `catalog-v1`, exact component schema version and known
  type;
- same-site/workspace page, parent and sibling identities;
- parent slot allowlist, child count, total components, depth, no cycles,
  unique IDs and dense deterministic sibling order;
- bounded JSON bytes/depth/items and exact prop schema/types/required fields/
  enums/numeric bounds/localization/authority class;
- rejection of unknown keys, raw style/CSS/classes, HTML/innerHTML, scripts,
  handlers, JavaScript/data/file URLs, callback/template/expression/query/code/
  package input and prototype keys at any nesting depth;
- collection components bind only an exact same-site visible collection view
  with active type/version and declared bounded query/projection; and
- existing media-reference props, where accepted in this slice, bind only an
  exact same-site visible immutable media record. No media upload/bytes/public
  finalization belongs here; otherwise reject those component creates until
  Objective 079 rather than accepting an unchecked UUID.

Use the same validator on create, PATCH, move final tree, Render and human
Editor/Puck server paths where applicable. Puck permissions remain UX only.
Do not let a crafted Agent or Editor request persist state Render later rejects.

Extend immutable resource constraints only as needed: allowed component types,
page/subtree/route restrictions inherited from 077, maximum visible components,
maximum components per page and maximum component depth. Unknown/malformed
constraints fail closed. The trusted wrapper, not Python, owns resource/count/
delete/mutation quota consumption.

## 4. Transactional COW and structural integrity

Every mutation must use server-derived site/workspace/operation context, the
existing workspace shared lifecycle lock/state recheck, COW transaction,
durable idempotency, wrapper-owned quota and same-transaction semantic audit.
Replay consumes no second quota/audit/COW operation; same key with another
request is 409. Cancellation rolls everything back and returns pools/context
clean.

Serialize page/composition dependency decisions before the COW statement
snapshot using the established structural lock ordering so races cannot create
cycles, duplicate/dangling positions, cross-page parents, excess bounds, or
page deletion with a newly added component. Preserve concurrency across
independent workspaces/sites and 077's page/navigation/redirect locks.

Use real PostgreSQL event/advisory-lock barriers—not timing sleeps—for at least:

- concurrent creates at the same semantic position;
- competing moves, including a would-be cycle;
- stale concurrent PATCH;
- leaf delete versus child create/move; and
- page delete versus component create.

Assert exact winner/loser responses and final durable tree, row versions,
quota/idempotency/audit/COW operations. Do not accept a broad set of statuses
without checking terminal state.

## 5. Production-boundary acceptance

A real human-issued capability must exercise public Agent HTTP, preferably
through NGINX in the clean Compose proof, to:

1. inspect the exact catalog and existing normalized composition;
2. create a nested trusted Section/Container/Heading or equivalent tree;
3. exact-read and update content props with L1-compatible authority;
4. move/reorder nodes through semantic anchors and observe dense order;
5. render the same workspace through authenticated human preview and run-bound
   browser preview/Web HTML using the shared trusted renderer;
6. delete leaves and observe their absence;
7. restart Agent, Render and Web and observe identical workspace state; and
8. prove canonical, a second workspace and a second site remain unchanged.

Negative evidence must cover L1 structural denial, L2 design-prop denial,
missing/wrong scope, foreign site/workspace/page/node/parent/sibling/view/media,
stale version, frozen/revoked/expired capability, resource and quota exhaustion,
replay/mismatch, invalid catalog/schema/type/slot/props/bindings, cycles/depth/
count/order, dependency deletion, cancellation and the concurrency cases above.
No capability/internal UUID/secret/raw projection JSON may leak into visitor
HTML, browser artifacts or logs.

Neutral owner SQL may create identity/canonical/corruption/barrier fixtures and
assert isolation. It may not perform any claimed Agent component mutation.
Direct service/SQL/helper tests supplement but never replace public Agent and
intended preview/Render/Web evidence.

## 6. Contracts, migration, documentation and verification

Update production handlers, route-policy entries and canonical generated Agent
OpenAPI bidirectionally. No schema-only or undocumented route; exact bearer
scopes, Idempotency-Key, conditional scope metadata, request/response/error
schemas and public OpenAPI bytes are required.

Use append-only migrations from head `059_001`; add row version/constraints/
helpers/grants safely with clean install and data-bearing downgrade/re-upgrade.
Preserve existing composition rows, Puck/Editor compatibility, foundation COW
hardening, public/preview readers, setup/reviewer separation and exact owners/
`search_path`/PUBLIC/runtime privileges. No `CASCADE` data loss or historical
migration rewrite.

Update API, composition/catalog, testing and MVP progress documentation only
for this implemented component slice. Keep Objective 078 open and the MVP not
complete.

Run focused catalog/component/props/binding/tree/auth/resource/idempotency/
audit/COW/concurrency/cancellation/migration/privilege/Render tests; full Agent
and Editor integration; generated OpenAPI/policy; Node catalog/Puck/renderer;
clean Compose/NGINX/browser/restart; Python quality/unit/integration and
PostgreSQL 14–18; repository/Markdown/Mermaid; all six zero-Critical images;
then all current-head GitHub checks. Pending/skipped/superseded is not pass.

## Explicit non-goals and safety

- No broad theme/design-system/global-region/header-footer/responsive-design
  mutation yet; no 079 media byte upload/finalization; no 080 MCP; no 081 exact-
  Agent-workspace Puck workflow; no 082+ freeze/review/promotion; no 087 source/
  sweep; no site reset in this slice.
- No executable component/prop/code/CSS/JS/HTML/template/query/primitive/plugin,
  dependency/image/architecture/exception change, general refactor or release
  claim.
- Do not reopen issue #67 or weaken Chrome/supply-chain/security/Markdown/tests.
- No production system/data/credential. Routine tools, PostgreSQL, browsers and
  Compose belong to the passwordless-sudo disposable executor environment.

## GitHub workflow and immutable report

Fetch/reconcile GitHub; start from exact remote main; create the fresh 078
branch and exactly one new PR. Commit the exact activated order and
`oap/active` unchanged with implementation. Push before observing CI, repair
only in-scope failures, create no extra PR, never merge/auto-merge.

Publish exactly `oap/reports/078-a-agent-component-semantics.md` as the final
report-only child of a literal implementation SHA with `Report publication
commit: SELF`. Include exact PR/branch/base/head/commits/files; catalog source/
drift consumers; route/OpenAPI/actions/scopes; migrations/functions/grants/
downgrade; public Agent/preview/browser/restart/isolation; negative/concurrency/
cancellation terminal state; local commands/counts/skips/current checks;
docs; safety/no-secret/no-extra-PR/no-merge; remaining 078 scope; and strongest
reason not to accept this slice.

Do not return early for ordinary implementation/test/CI failures or task size.
`PARTIAL`/`BLOCKED` requires a concrete external outage or unresolved product/
architecture decision. No post-report push; signal exact FIFO `OK`, then wait.

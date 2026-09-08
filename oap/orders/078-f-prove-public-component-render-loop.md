# OAP Work Order — 078-f

## Objective and authoritative state

Close the 078-a component-data-plane acceptance layer on the existing
Objective-078 PR with one clean deployed public Agent -> shared preview/Web ->
real browser-worker -> restart/isolation proof, then align component/API/testing
and MVP status documentation. This round proves existing component semantics;
it does not add the remaining Objective-078 design/theme/global feature scope.

- Numeric objective: `078`; round: `078-f`; mode: `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77),
  `main` <- `oap/078-agent-composition-design-semantics`; create no new PR.
- Verified remote `main`: `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Required starting PR head: report-only commit
  `cf466626f9fdd5e940beed3567dca7aed2437edd`; its sole changed path is the
  immutable 078-e report and its parent is implementation commit
  `fd63f0e0fac627a08e51bda660c2598e7b3a12af`.
- Preserve the accepted 078-b through 078-e catalog, typed contract, strict
  nested validation, Render/Puck behavior, sequential ordering/versions/
  resources, concurrency/cancellation, legacy Editor and security posture.
- Numeric Objective 078 remains open and PR #77 must not be merged this round.

## Required clean public workflow

Extend the existing clean Compose acceptance harness rather than creating a
parallel mocked/internal-only demo. Start from clean isolated Compose volumes
through the repository's normal one-command smoke path. Only NGINX may be used
as the public HTTP boundary; do not call internal Agent/Render/browser ports or
perform claimed component mutations with owner SQL.

A real authenticated human control flow must create/select the site/workspace
and issue the bounded capability used below. Through that capability and public
Agent HTTP:

1. fetch the exact canonical Agent OpenAPI bytes, session/permissions,
   catalog-v1 and the initial page composition;
2. create a page and a nested `Section -> Container -> Heading` tree plus a
   second content leaf supported by catalog-v1, using only semantic anchors;
3. exact-read the nodes, update Heading content props through the L1-compatible
   scope, move/reorder leaves through before/after anchors, and list the exact
   dense IDs/order/positive versions;
4. fetch the same workspace through authenticated human preview at the public
   NGINX/Web route and assert the updated visible text, hierarchy/component
   markers and safe rendering—not merely Render JSON or HTTP 200;
5. request a normal run-bound Agent preview browser job for that route, await
   the real browser worker, retrieve its private artifact(s), and assert the
   same updated text/structure plus no console/network/heading failure as
   appropriate;
6. while the tree still exists, restart `agent-api`, `render-api`, and `web`
   using the existing Compose restart helper and readiness waits; after each
   relevant restart re-read through public Agent/preview and prove IDs, props,
   hierarchy/order/versions and rendered meaning are identical;
7. delete content leaves and then parents in dependency-correct order through
   public Agent DELETE, prove exact-read/list 404/absence and preview removal;
   replay one delete key and prove no second effect; and
8. prove the canonical site, another workspace on the same site, and another
   site remain unchanged before/after mutation, restart and deletion.

Use unique data markers and exact expected HTML/artifact content. The browser
job must be the product's bounded preview operation with a run-bound internal
credential; no agent capability or human cookie may enter URL, HTML, browser
storage, artifact metadata/bytes, logs or screenshot/trace content.

## Hostile public-boundary negatives

Within the same clean deployment, prove at least:

- a human-issued L1/otherwise lower-scope capability cannot create, move or
  delete structure, while its authorized content-prop update on a visible
  existing component follows the defined resource/workspace rules;
- an L2/no-design capability cannot create or PATCH catalog-declared design
  props;
- a missing/wrong scope and a foreign workspace/site/page/node/parent/sibling
  substitution fail closed without disclosing the foreign record;
- stale row version, invalid slot/type/schema/nested prop, dependency delete,
  raw `order_key`, same idempotency key with a different request, and exhausted
  component mutation/delete/resource budget produce their exact stable errors
  and no partial state;
- a revoked/frozen or otherwise non-active capability cannot continue component
  writes (reuse the clean harness's existing lifecycle proof where it already
  exercises the exact same public executor; do not duplicate expensive setup
  for prose); and
- visitor/public rendering remains canonical while only the authenticated
  preview/browser run observes workspace component changes.

Each negative must assert the relevant component rows/versions and durable
quota/idempotency/audit/COW state remain unchanged. Reuse existing acceptance
helpers and baseline digests; do not weaken earlier model/page/navigation/
browser acceptance.

## Restart, isolation, and audit truth

Record exact semantic actions `COMPONENT_CREATED`, `COMPONENT_UPDATED`,
`COMPONENT_MOVED`, `COMPONENT_DELETED` and their expected method/status/quota
kind from the same public workflow. Assert one audit/idempotency/foundation
operation per committed request and no second event/quota on replay. Verify the
public HTML and browser artifacts contain no workspace/capability/internal
credential/raw projection JSON leakage.

The final clean run must leave the broader existing acceptance harness green,
including NGINX topology, browser confinement, service-role boundaries,
OpenAPI drift, restart durability, supply-chain evidence and zero-Critical
image policy.

## Documentation

Update durable documentation to describe only implemented evidence:

- `docs/API.md`: exact catalog and component GET/POST/PATCH/move/DELETE paths,
  scopes, semantic anchors, expected versions, stable errors and design-scope
  boundary; remove stale create-only/raw-order wording.
- `docs/TESTING.md`: focused catalog/renderer/concurrency coverage and the new
  clean NGINX/browser/restart/isolation workflow.
- `README.md` where its current implemented/deferred wording still calls the
  proven bounded component data plane absent; keep design/theme/media/review
  limitations explicit.
- `oap/MVP-PROGRESS.md` and `oap/MVP-CONTRACT-AUDIT.md`: preserve historical
  evidence and record the current source-revision component slice as E2E proven
  on open PR #77, while Objective 078 and the contractual MVP remain partial.

Do not describe the open PR as merged, Objective 078 as complete, or the product
as production-ready.

## Verification

Run the complete clean `tools/compose/smoke.sh` workflow under a fresh unique
Compose project, not only its Python helper against old volumes. Report exact
command, elapsed time and terminal proof summary. Also run focused modified
acceptance/helper tests, generated catalog/OpenAPI drift, Python unit/repository
and Node suites, formatting/type/Markdown/Mermaid checks, and all current-head
GitHub checks. Pending/skipped/superseded is not pass. Do not repeatedly rerun
the expensive clean workflow after an unrelated documentation-only correction;
repair focused failures first and rerun only when the behavior under test or
clean-deployment result could have changed.

## Non-goals and continuing scope

- No new catalog breadth, component variant/design/layout/responsive mutation,
  design-system/theme/global-region/header-footer behavior. Those remain later
  Objective-078 rounds after this component slice is accepted.
- No media upload/bytes/finalization (079), MCP (080), exact-Agent-workspace
  Puck (081), freeze/review/promotion (082+), source/sweep (087), site reset,
  release claim, dependency/image/architecture/security exception, broad
  refactor or production access.
- No historical order/report edit, test/Markdown/security weakening, new PR,
  merge or auto-merge. Preserve issue #67 closure and zero-Critical policy.

Routine Docker/Compose/PostgreSQL/Playwright tooling belongs to the
passwordless-sudo disposable executor environment; do not transfer it to the
human.

## GitHub workflow and immutable report

Fetch and verify the exact existing PR/branch/head, then amend only PR #77.
Commit this order and exact `oap/active` unchanged with the bounded acceptance
and documentation, push, inspect and repair only in-scope CI failures, create
no PR and never merge.

Publish exactly
`oap/reports/078-f-prove-public-component-render-loop.md` as the final
report-only child of a literal pushed implementation SHA with `Report
publication commit: SELF`. Report exact PR/SHAs/files; human capability issue;
every public Agent request/action/status; preview HTML and real browser artifact
evidence; restart and isolation digests; hostile negative/unchanged-state and
audit/idempotency/quota/COW results; clean Compose command/elapsed/summary;
docs; current checks/skips; scope/safety; remaining design work; and the
strongest reason Objective 078 is not yet acceptable. Make no post-report push,
signal exact FIFO `OK`, then wait.

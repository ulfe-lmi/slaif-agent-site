# OAP Work Order — 077-d

## Objective and verified PR state

Repair the concrete strategic-review defects in the 077-a page/hierarchy/route
slice. Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; no new PR and no
merge. Required starting remote report head:
`ba6edf7a07156db0748c860b1264c903a436a01d`, whose sole parent is 077-c
implementation `242b572dca0500d67c8a4b449db377045bc41def`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

All 20 required checks on the 077-c report head are terminal success. The
human-authorized historical-order correction is exact and closed. Preserve the
accepted 077-b MVP-ledger and Chrome `152.0.7977.82` qualification changes.
GitHub issue 67 remains open until the containing PR is eventually accepted,
merged, and verified on remote `main`.

This is a production page-contract repair, not a prose/evidence-only round.
Do not add Agent locale, navigation, redirect, or dynamic Render routing yet.

## Why 077-a is not accepted

Independent review identified five concrete defects:

1. `slaif_agent_page_restore` queries `content.page_changes` and its private
   `_cow_*` columns directly. Product migrations/functions may use only the
   documented public `agentcow.postgres` foundation boundary; private base/
   change tables are not a product API.
2. `slaif_agent_page_ensure_locale` inserts a missing `content.site_locale`
   row. A page-capable Level-2/narrow capability therefore mutates locale
   configuration without Level-4 `locale:configure` authority.
3. route-affecting PATCH dynamically requires `route:write` in the handler,
   while route policy and canonical OpenAPI advertise only `page:write`.
   The public contract is incomplete and cannot be audited bidirectionally.
4. `MovePageRequest` publicly accepts `before_page_id`/`after_page_id`, but the
   database only validates those values and persists no sibling ordering. A
   successful request must never silently ignore semantic input.
5. 077-a added only duplicate-create concurrency proof. It omitted the ordered
   competing move/route-update race, page-specific cancellation proof, and
   trustworthy data-bearing migration/downgrade evidence required by its order.

Repair all five without weakening the page/route contract or bypassing COW.

## Required production repair

### 1. Product-owned reviewable deletion and restore

Remove every production dependency on `content.page_changes`, `_cow_deleted`,
`_cow_order`, or any other private foundation relation/column. Assertion-only
owner tests may inspect COW internals solely to prove isolation; application
code, runtime SQL and migration functions may not use them for behavior.

Implement page deletion/restoration as an explicit, bounded product-owned soft
tombstone within the COW-enabled `content.page` domain model. The exact column
shape is implementation-owned, but the contract is mandatory:

- DELETE requires visible same-site page, exact positive row version,
  `page:delete`, delete permission/quota, dependency safety and ACTIVE context;
  it atomically marks the page deleted, increments row version, records the
  semantic event/idempotency result, and returns a typed reviewable deleted
  record.
- Normal Agent list/get, effective-route conflict detection, and active Render
  projection treat a tombstoned page as absent. Canonical and other workspaces
  remain unchanged before promotion.
- Restore requires `page:restore` and the exact tombstone row version, clears
  the tombstone, increments row version, and revalidates locale, parent,
  subtree depth, resource constraints and effective-route uniqueness. If the
  route was reused or the parent became invalid, restore fails atomically with
  stable conflict/domain semantics and leaves the tombstone intact.
- A canonical page and a workspace-created page can each be delete/restored
  with the same immutable ID. Replay does not increment version or charge/
  audit twice; mismatch is 409. Repeated delete/restore and stale versions fail
  deterministically.
- An accepted future promotion may retain a canonical soft tombstone; public
  and preview renderers must treat it as absent. Do not fake foundation DELETE
  or invent a hidden non-COW restore store.

Repair unreleased migration 049 in place rather than adding an avoidable 050
head. Reconcile explicit human Editor projections/functions and every COW
column/privilege/bootstrap contract affected by the new product column.

### 2. Locale authority must remain Level 4

Replace implicit locale creation with validation only. Every page create,
route-affecting update, move, delete/restore validation and read projection must
require an already existing, enabled, same-site `content.site_locale` selected
through the workspace overlay. Page authority can never insert, enable,
disable, default, reorder, rename or delete a locale.

A real L2/narrow page capability attempting an unknown or disabled locale must
receive a stable domain/authorization denial with no locale/page/quota/audit/
idempotency/COW residue. Prove the same for a capability with `page:create` but
without `locale:configure`; possessing page authority never implies locale
authority. Existing valid locales continue to work. Agent locale configuration
itself remains a later Objective 077 slice.

### 3. Honest route-template and move contracts

The page slug remains the ordinary normalized static segment. A separate route
template may be only null or the exact terminal literal `{slug}`; remove the
unnecessary alternate-static-template form. Reject all malformed, renamed,
repeated, wildcard, nonterminal, encoded, URL/query/regex/executable variants at
both schema and trusted database boundaries.

Page move is required to change hierarchy/derived routes, not to fabricate a
page-ordering feature. Resolve the ignored relative targets in one of two
honest ways:

- remove `before_page_id` and `after_page_id` from the request schema, handler,
  wrapper, OpenAPI and tests, leaving an exact parent move; or
- add a genuine bounded persisted page sibling-order model and prove the
  relative move result.

Prefer the smaller parent-only contract unless an existing architectural
requirement proves page sibling ordering necessary. Do not retain an accepted
field that has no observable effect. Navigation-item reordering is separate
and remains required later in Objective 077.

### 4. Conditional route-write policy and OpenAPI

Preserve metadata-only page PATCH under `page:write`; slug, locale or
route-template changes additionally require `route:write`. Make that condition
machine-auditable rather than a handler-only secret:

- extend the bounded route-policy representation with an exact conditional
  scope declaration tied to the named request fields;
- emit an explicit deterministic canonical OpenAPI extension describing the
  trigger fields and additional `route:write` requirement;
- make the bidirectional production-handler/route-policy/OpenAPI drift test
  fail if the condition, fields, scope, handler enforcement or schema diverges;
- prove a capability with only `page:write` can update title/status but cannot
  change any route field, while a capability with both scopes can.

Do not solve this by granting route authority implicitly, omitting the
condition from OpenAPI, trusting generated clients, or requiring unrelated
scopes. Preserve exact bearer/idempotency/error/success metadata.

### 5. Transaction, race, cancellation and migration proof

Preserve the deterministic workspace+site structural advisory-lock order after
the product workspace lifecycle lock. All page create/update/move/delete/
restore operations affecting hierarchy or routes must participate.

Add real multi-connection PostgreSQL tests with deterministic database/event
barriers and no timing sleeps for:

- route-affecting PATCH racing a move whose descendant effective route would
  conflict or exceed depth;
- competing moves capable of producing a cycle or duplicate effective route;
- restore racing route reuse; and
- cancellation while blocked on the structural lock, followed by proof of no
  page/tombstone/quota/audit/idempotency/COW residue and a successful later
  request.

Each race must have a coherent serialized outcome, stable loser error and final
tree/route/tombstone state. Test isolation across another workspace and site.

Add real PostgreSQL migration evidence for 048→049 fresh and data-bearing
upgrade, current 049 bootstrap/reconcile, and 049 downgrade behavior. An exact
048-compatible database must downgrade and re-upgrade with data, grants,
owners/functions and COW hardening intact. If 049-only route-template,
tombstone or PAGE-audit data cannot be represented safely in 048, downgrade
must preflight and fail before any DDL/data/privilege mutation with a clear
operator error; never lose append-only audit or partially tear down COW. Prove
that failure is atomic and the 049 database remains usable.

## Public acceptance and anti-bypass

Extend focused real-PostgreSQL production Agent HTTP tests—not direct service/
SQL substitutes—to prove exact get/create/update/move/delete/restore through a
real human-issued capability. Cover canonical/other-workspace/site isolation,
valid existing locale, unknown/disabled locale no-mutation, conditional scope,
parent-only or genuinely ordered move, tombstone visibility in Agent and active
Render, route reuse/restore conflict, dependencies, stale versions, quotas,
strict semantic audit/operation identity, replay/mismatch, cancellation and all
races above.

Neutral owner SQL may seed canonical/control fixtures and assert outcomes only.
Direct wrapper tests are additional defense, never product proof. Ensure the
test would fail if the public handler, trusted wrapper, tombstone filter,
conditional route policy, structural lock, or audit completion were removed.

Regenerate `contracts/openapi/agent-v1.json`; update `docs/API.md` only for the
corrected page contract. Extend the public Compose Agent acceptance where
needed to prove deletion/restore and canonical independence through NGINX,
including service restart. Run focused tests, full Agent mutation/OpenAPI/
route-policy/migration/privilege integration, Python quality/unit/integration,
PG14–18, repository/Markdown/Mermaid, Node, clean relevant Compose, and current
required CI. Preserve the qualified Chrome `.82` zero-Critical policy and empty
exception set; rerun full supply-chain only where the required gate does.

## Non-goals and safety

No Agent locale CRUD, navigation container/item, redirect, dynamic detail
Render, composition/design/Puck/media/MCP/freeze/review/promotion/source/sweep
or 078+ work. No unrelated refactor, dependency/image/exception/architecture/
historical-order/report change, production/release claim, issue closure, or
production system/data/secret access. Do not reopen 076. Routine packages,
PostgreSQL, Docker and test infrastructure belong to the executor; passwordless
sudo is available.

## GitHub workflow and immutable report

Verify and update only the named PR/branch. Commit this exact activated order
and `oap/active` unchanged with the bounded production/test/docs repair; push;
create no PR; never merge or enable auto-merge. Inspect and repair in-scope CI
failures within the turn.

Publish exactly
`oap/reports/077-d-repair-page-authority-and-structure-proof.md` as a final
report-only child of a literal 40-hex implementation SHA with `Report
publication commit: SELF`. Include exact PR/base/head/commits/files; repaired
migration/functions/schema/owners/grants; proof of no private foundation
dependency or implicit locale write; deletion/restore/version behavior;
conditional policy/OpenAPI inventory; move contract; deterministic race and
cancellation mechanisms/outcomes; migration/downgrade atomicity; public HTTP/
Render/NGINX/canonical/audit/quota/idempotency evidence; commands/counts/skips;
all current checks; no scope drift/new PR/merge/secret/exception; remaining 077
scope; and strongest reason not to accept this page slice.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker and exact
attempted evidence. Do not return early because implementation/tests/CI are
long. No post-report push. Signal exact FIFO `OK`, then wait for strategic
review.

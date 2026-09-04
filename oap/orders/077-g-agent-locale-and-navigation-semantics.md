# OAP Work Order — 077-g

## Objective and verified PR state

Implement the next dependency-correct Objective 077 production slice: public
Agent locale configuration plus navigation container/item CRUD and semantic
move/reorder, integrated with the accepted page/route contract. Amend only
[PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`8a7aea39211d1555baf9703cfe82ea8f99e0874c`, whose sole parent is 077-f
implementation `0943df0b46a8bbeeafbfbedf1cd331987cf44beb`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Preserve all 077-a through 077-f page, ledger, Chrome, protocol and bootstrap
repairs. The page/hierarchy slice is accepted for progression, but Objective
077 remains open. GitHub issue 67 remains open until eventual merge to verified
remote `main`.

## Required public Agent operations

Use typed production handlers under `/api/agent/v1` with the established
capability/COW/idempotency/audit/error contract:

```text
GET    /locales
POST   /locales
GET    /locales/{locale_id}
PATCH  /locales/{locale_id}
DELETE /locales/{locale_id}

GET    /navigation
POST   /navigation
GET    /navigation/{navigation_id}
PATCH  /navigation/{navigation_id}
DELETE /navigation/{navigation_id}
GET    /navigation/{navigation_id}/items
POST   /navigation/{navigation_id}/items
GET    /navigation-items/{item_id}
PATCH  /navigation-items/{item_id}
POST   /navigation-items/{item_id}:move
DELETE /navigation-items/{item_id}
```

Compatible aliases are permitted only if route policy and canonical OpenAPI
declare them exactly. Reads require `site:read` for locales and
`navigation:read` for navigation. Locale mutations require Level-4
`locale:configure`; navigation container create/update/delete require the exact
`navigation:create`/`navigation:write`/`navigation:delete` scope; item create,
update and move require `navigation:write`, and item delete requires
`navigation:delete`. Lower presets and narrowed capabilities fail closed.

Every mutation requires `Idempotency-Key`, returns the standard typed Agent
mutation envelope with server operation UUID, uses exact positive optimistic
row version where modifying/deleting an existing resource, charges one wrapper-
owned mutation/delete quota, and emits one strict same-transaction semantic
action/resource/method/status/quota audit event. Add exact LOCALE, NAVIGATION
and NAVIGATION_ITEM create/update/move/delete action contracts. Replays return
the stored result without a second version, charge, audit or COW operation;
same key/different request is stable 409.

## Locale configuration contract

- `content.site_locale`, not non-COW `control.site.default_locale`, is the
  workspace-editable locale/default truth. Exactly one visible enabled default
  locale must exist per site/workspace. Page effective-route/default-locale
  decisions must use the visible COW locale default so a workspace can preview
  a proposed default without changing canonical control state.
- Locale tags are normalized, immutable identifiers after creation. PATCH may
  change bounded enabled/default/position/metadata plus expected row version,
  but not silently rename a tag and strand references. Setting a new default
  atomically clears the old visible default; a default cannot be disabled or
  deleted, and no operation may leave zero or multiple defaults.
- Delete/disable rejects a locale referenced by any visible active page,
  navigation item, redirect, content-item translation, or other localized
  structure relevant to the current model. Use exact structural references,
  not substring matching. Do not cascade or rewrite unrelated content silently.
- Extend bounded resource constraints at both immutable context validation and
  trusted PostgreSQL boundary for allowed locale tags and maximum visible
  locales. Unknown/malformed constraints fail closed. Locale creation at the
  limit and concurrent creates/default switches serialize deterministically.
- L2 page authority still cannot create/configure a locale. Locale changes are
  COW-only; canonical `control.site.default_locale`, canonical locale rows,
  other workspaces and other sites remain unchanged before later promotion.

## Navigation contract

- Navigation containers have immutable site association, stable key, bounded
  localized/ordinary label and settings, timestamps, and positive row version.
  Keys are unique per visible site/workspace. Update cannot change identity;
  delete rejects nonempty containers unless the API performs and audits an
  explicit all-or-nothing bounded cascade. Prefer dependency denial.
- Navigation items have immutable site/container association, optional parent,
  optional locale, target kind, target, bounded localized labels, server-owned
  sibling order and row version. A PAGE target references an existing visible,
  non-tombstoned same-site page. INTERNAL targets are normalized safe site
  routes; EXTERNAL targets use the architecture URL allowlist. No executable,
  protocol-relative, credential-bearing, control/internal/preview or cross-site
  target is accepted.
- Create and `:move` express relative semantic placement with optional
  `before_item_id` or `after_item_id`, never caller-owned raw storage ranks.
  The server assigns/rebalances positions transactionally and returns observable
  deterministic order. Reject both before+after, foreign/different-container/
  different-parent anchors, self/descendant parents, cycles, excessive depth,
  duplicate sibling positions and dangling references.
- PATCH changes bounded labels/locale/target and expected version, not container
  or site identity. Delete rejects an item with children unless a documented
  bounded atomic cascade is deliberately implemented. Page deletion must remain
  blocked while any visible navigation item references it.
- Extend trusted resource constraints for allowed navigation keys/IDs as needed,
  maximum visible containers, maximum visible items, and maximum navigation
  depth. Enforce under PostgreSQL, not only HTTP. Preserve route-prefix,
  allowed-locale, page-subtree, max-delete and ordinary request/mutation quotas.

## Coupled transactional integrity

Page, locale and navigation decisions are coupled. Replace separate page/
navigation/locale advisory namespaces with one documented deterministic
workspace+site structural lock acquired after the existing workspace lifecycle
shared lock. Every page route/move/delete/restore, locale create/update/delete,
navigation container mutation and navigation-item mutation that can affect a
reference participates in the same order.

Authoritative PostgreSQL checks must make concurrent operations serialize so
they cannot create duplicate navigation keys/order, cycles, excessive depth,
dangling page references, a missing/multiple default locale, disabled referenced
locale, or cross-site/container relationships. Do not rely on Python list-then-
write validation, unique-violation luck, timing sleeps, or later Render cleanup.

Add real multi-connection PostgreSQL/public Agent HTTP races with deterministic
barriers for at least:

- page delete versus navigation-item create/reference;
- locale disable/delete versus page or navigation-item create/update;
- two concurrent default-locale switches;
- navigation-item move versus competing move/cycle creation; and
- sibling reorder/create collisions.

Each race has one coherent serialized outcome, stable loser error, no deadlock,
and final referential/default/order integrity. Cancellation while blocked and
inside reorder/default mutation must roll back row changes, quota, idempotency,
audit and COW operations; a later request succeeds.

## Database, migration and authority

Reuse the fixed COW tables and existing Editor substrate where sound. Add the
minimum new migration after 049 or safely repair an unreleased appropriate
surface; do not rewrite merged migrations. Preserve data-bearing upgrade,
public COW disable/downgrade/re-upgrade, exact function owner/search path/grants,
and privilege hardening. Agent runtime receives only narrow wrapper EXECUTE and
COW view CRUD needed by the foundation; no base/change/reviewer/control-schema/
DDL/raw-SQL authority. Product behavior must not name private foundation
relations or functions.

Do not change Editor behavior accidentally. If adding row versions or semantic
ordering to legacy navigation tables, keep Editor projections typed and make
stale writes fail rather than silently overwrite. Migration downgrade must
preserve compatible data or refuse before mutation when new state cannot be
represented; never lose append-only audit.

## Public acceptance, OpenAPI and documentation

A real human-issued capability through production Agent HTTP must configure a
second locale/default, create/update/read/delete a navigation container, create
page/internal/external items, form a bounded hierarchy, move/reorder items, and
observe exact order and locale/default state from the same workspace. Prove
canonical, another workspace and another site unchanged, Agent restart
persistence, audit identity, quota/idempotency, cancellation and races.

Negative evidence covers lower preset/wrong scope, allowed-locale/navigation
constraints, foreign site/workspace/container/page/item/anchor, stale versions,
duplicate keys/order, cycle/depth/item/container/locale limits, default
invariants, referenced locale/page/container deletion, unsafe targets,
non-ACTIVE/revoked/expired/delegator-loss state, quota exhaustion, replay
mismatch and zero residue. Neutral owner SQL may seed/assert only; no Editor,
direct service/wrapper/SQL/test-only substitute may perform claimed Agent work.

Update route policy and generated canonical Agent OpenAPI bidirectionally for
every operation, with exact scopes, conditional scopes if any, bearer security,
idempotency, request/success/error schemas/statuses, and no schema-only or
undocumented route. Update `docs/API.md` and implementation/security notes only
for delivered behavior. Extend public NGINX/Compose acceptance for the real
locale/navigation journey and restart; it must fail if a production handler,
wrapper, audit action, structural lock or canonical-isolation check is removed.

Run focused locale/navigation/model/PostgreSQL/concurrency/cancellation/
migration/privilege/OpenAPI tests; full Agent mutation, integration and Python
quality/unit; PG14–18; repository/Markdown/Mermaid; Node; clean Compose public
acceptance; and all current required CI. Preserve qualified Chrome
`152.0.7977.82`, zero current Critical findings and empty exceptions.

## Non-goals and immutable report

No redirect Agent API yet, no dynamic collection-detail Render/router behavior,
and no composition/design/Puck/media/MCP/freeze/review/promotion/source/sweep or
078+ work. No dependency/image/exception/architecture/historical artifact/
general refactor/issue closure/production/release claim or production access.
Do not reopen 076.

Verify/update only PR #74 and its branch. Commit this exact order and
`oap/active` unchanged with the bounded implementation/tests/docs; push; create
no PR; never merge/auto-merge; repair only in-scope current-head failures.

Publish exactly `oap/reports/077-g-agent-locale-and-navigation-semantics.md` as
the final report-only child of a literal implementation SHA with `Report
publication commit: SELF`. Include exact PR/commits/files/migration/functions/
tables/indexes/triggers/owners/grants/routes/OpenAPI; locale/default/navigation/
ordering/dependency behavior; resource/scope/quota/idempotency/audit/COW/
canonical isolation; deterministic race/cancellation outcomes; upgrade/
downgrade; public NGINX/restart; commands/counts/skips/current checks; no private
foundation dependency/scope drift/new PR/merge/exception/secret; remaining 077
scope; and strongest reason not to accept this slice.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker with exact
attempted evidence. Do not return early because implementation/tests/CI are
long. No post-report push. Signal exact FIFO `OK`, then wait for strategic
review.

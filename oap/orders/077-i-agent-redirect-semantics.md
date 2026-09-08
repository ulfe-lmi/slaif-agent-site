# OAP Work Order — 077-i

## Objective and verified PR state

Implement the next Objective 077 production slice: complete public Agent
redirect semantics integrated transactionally with page routes, locales and the
shared site-structure lock. Amend only
[PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`c27b25da904bf76bf8a58617607d36825072d573`, whose sole parent is 077-h
implementation `ec4414feea10549b2bfbfdc9c21ea085e01d9cfe`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

All 20 required checks on the 077-h report head are terminal success. Preserve
all accepted page, locale, navigation, Chrome, ledger, bootstrap and protocol
work from 077-a through 077-h. Objective 077 remains open; dynamic Render
routing is a later slice. GitHub issue 67 remains open until eventual merge to
verified remote `main`.

## Public Agent redirect contract

Implement typed production operations under `/api/agent/v1`:

```text
GET    /redirects
POST   /redirects
GET    /redirects/{redirect_id}
PATCH  /redirects/{redirect_id}
DELETE /redirects/{redirect_id}
```

Reads require `redirect:read`; create/update/delete require exact
`redirect:create`, `redirect:write`, and `redirect:delete`. Every mutation
requires `Idempotency-Key`; update/delete require an exact positive row version;
responses use the standard typed Agent mutation envelope and server-owned
operation UUID. Add strict `REDIRECT_CREATED`, `REDIRECT_UPDATED`, and
`REDIRECT_DELETED` semantic contracts with exact resource/method/status/quota
identity. Delete uses delete quota and `delete_enabled`/`max_deletes`; replay
adds no second version/quota/audit/COW effect; mismatch is stable 409.

Expose immutable site association, normalized source route, safe target,
allowed status code, optional locale, row version and timestamps. PATCH changes
only explicitly supplied mutable fields and rejects an empty body. It must not
silently clear locale/target or accept ignored input.

## Route, target and locale semantics

- Source is one normalized absolute site path, not a URL. Reject root if policy
  cannot support it safely; reject reserved API/admin/preview/internal/static
  paths, repeated/dot/encoded separators, query/fragment, backslash, wildcard,
  template token, control/space or executable syntax. Source is unique per
  visible site+locale; define deterministic semantics for locale-null versus
  locale-specific redirects and prevent ambiguous effective matches.
- A redirect source must not equal or overlap an active static page route or an
  instance space covered by a dynamic `{slug}` page template in the same
  locale. Conversely page create/route PATCH/move/restore must reject a route
  colliding with a visible redirect source. Do not pick an arbitrary winner.
- INTERNAL target is a normalized safe site path resolving to one visible
  non-tombstoned static page route or to another visible redirect source in the
  same locale/fallback contract. EXTERNAL target is HTTPS only until an explicit
  site policy exists. Reject HTTP, protocol-relative, credential-bearing,
  malformed, reserved-control, executable or cross-context targets.
- A redirect cannot target itself. Follow the prospective visible graph under
  a strict bounded maximum (initially 16 unless existing architecture policy is
  stricter) and reject direct/indirect cycles, ambiguous locale fallback,
  dangling targets, or chains exceeding the bound. Use exact graph traversal,
  not substring matching.
- Locale must be an existing enabled same-site visible locale and satisfy the
  capability allowlist. Locale disable/delete treats redirects as references.
  Changing workspace default locale must not make redirect selection ambiguous.
- Apply `route_prefix` to source and internal target, plus a trusted
  `max_visible_redirects` resource bound. Add it to immutable capability
  validation and PostgreSQL resource parsing; count only capability-visible
  redirects. Unknown/malformed constraints fail closed. A restricted capability
  cannot infer or mutate hidden redirects.

## Dependency and deletion safety

Redirect strings create real structural dependencies even without a physical
FK. Under the same transaction/lock:

- page delete or route-changing update/move/restore rejects if a visible
  redirect source would collide or an internal redirect target would become
  dangling; the caller must update/delete the redirect explicitly first;
- redirect delete rejects while another visible redirect targets its source,
  unless a documented bounded atomic rewrite/cascade is deliberately
  implemented and audited; prefer dependency denial;
- redirect update revalidates all incoming/outgoing dependencies and the whole
  affected graph; and
- foreign-site/workspace/locale targets and hidden dependencies are never
  followed or leaked.

Do not automatically propose a redirect on page route change in this slice.
If any existing optional proposal behavior is exposed, it must be explicit and
require `redirect:write`; otherwise leave it absent and documented.

## Transactional concurrency and cross-interface integrity

All Agent and Editor redirect create/update/delete functions must acquire the
same application-owned workspace+site structural lock used by page/locale/
navigation after the workspace lifecycle shared lock. Remove obsolete
site-only `_redirects` lock behavior from current production definitions.
Preserve separate Agent capability and Editor human authorization/audit paths;
share serialization only.

All graph, route-collision, target, locale, quota and dependency checks are
authoritative inside PostgreSQL in the mutation transaction. Add deterministic
real multi-connection PostgreSQL races, with production Agent HTTP and cross-
interface Editor HTTP where applicable, for at least:

- concurrent `A→B` and `B→A` redirect creation/update;
- page create/route move/restore versus redirect-source creation;
- page delete/route update versus redirect internal target;
- redirect delete versus another redirect targeting it;
- concurrent create at the maximum-visible redirect limit; and
- cancellation while waiting on the structural lock and while mutating a
  graph, followed by successful retry.

No timing sleeps. Exactly one coherent serialized outcome may win; the loser
has a stable domain/conflict/quota error and zero unintended redirect/page/
quota/idempotency/audit/COW residue. Final graph is acyclic, bounded,
non-dangling and site/locale confined, with no deadlock.

## Database, migration, OpenAPI and public proof

Reuse the fixed COW redirect table and existing validators only where they meet
this contract. Add the minimum migration after 050 or repair the current
unmerged surface safely; preserve existing canonical data and Editor
projections. Every function has exact owner/search path/grants; Agent runtime
gets only narrow wrapper EXECUTE and no private foundation/control/reviewer/
DDL/raw-SQL authority. Public COW disable/downgrade/re-upgrade must preserve
compatible data or refuse before mutation for unrepresentable 051 state; never
lose audit or leave readiness falsely safe.

Regenerate canonical Agent OpenAPI and route policy for exact handler inventory,
scopes, bearer security, required idempotency, typed request/success/error
schemas/statuses and no schema-only/undocumented route. Update `docs/API.md`
and testing/security notes only for delivered redirect behavior.

A real human-issued capability through public Agent HTTP/NGINX must create,
read, update and delete locale-specific and fallback redirects, build a bounded
valid chain, exercise page route dependencies, persist across Agent restart,
and prove canonical/other-workspace/site state unchanged. Negative proof covers
lower preset/wrong scope, foreign/hidden redirect/page/site/workspace/locale,
stale version, duplicate/ambiguous/reserved/unsafe source, HTTP/executable/
dangling target, loop/chain bound, route collision, dependencies, resource/
delete/request/mutation quota, non-ACTIVE/revoked/expired/delegator-loss state,
replay/mismatch, cancellation and every race above. Neutral owner SQL may seed
and assert only; direct service/SQL/Editor substitution cannot perform claimed
Agent behavior.

Run focused redirect/graph/route/dependency/resource/concurrency/cancellation/
migration/privilege tests; full Agent and Editor integration, Python quality/
unit, OpenAPI/route-policy, PG14–18, repository/Markdown/Mermaid, Node, clean
Compose public acceptance, and all current required CI. Preserve Chrome
`152.0.7977.82`, zero current Critical and the empty exception set.

## Non-goals and immutable report

No dynamic collection listing/detail Render/router or final route resolution
yet; no composition/design/Puck/media/MCP/freeze/review/promotion/source/sweep
or 078+ work. No dependency/image/exception/architecture/historical artifact/
general refactor/issue closure/production/release claim or production access.
Do not reopen 076.

Verify/update only PR #74 and its branch. Commit this exact order and
`oap/active` unchanged with bounded implementation/tests/docs; push; create no
PR; never merge/auto-merge; repair only in-scope current-head failures.

Publish exactly `oap/reports/077-i-agent-redirect-semantics.md` as the final
report-only child of a literal implementation SHA with `Report publication
commit: SELF`. Include exact PR/commits/files/migration/functions/indexes/
owners/grants/routes/OpenAPI; source/target/locale/fallback/graph/dependency
semantics; page collision guards; resources/scopes/quotas/idempotency/audit/COW/
isolation; Agent/Editor race/cancellation/downgrade/public NGINX/restart proof;
commands/counts/skips/current checks; no private dependency/scope drift/new PR/
merge/exception/secret; remaining 077 scope; and strongest reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker with exact
attempted evidence. Do not return early because tests or CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.

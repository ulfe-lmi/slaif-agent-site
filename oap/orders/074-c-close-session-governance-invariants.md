# OAP Work Order — 074-c

## Objective and verified state

Amend only PR #70 / `oap/074-human-agent-session-control-plane`; no new PR or
merge. Required starting report head
`3686d5acebc6f839f4170947b38c129983e7a6ce`, sole parent
`09d538d967e6749cff1f5b8ddbb22872d8013030`; `main` remains
`74d9c189fe241356fbe03f2632197ecbb1ce53a3`; all 20 checks are green.
074-b fixed context propagation, quota accounting, listing, audit, source
normalization and added real tests, but final hostile review found remaining
governance/replay/migration/evidence blockers.

## Required invariant repairs

1. **Delegator authority remains valid.** Capability lookup, request quota
   consume, mutation idempotency/shared transaction recheck, and direct Agent
   wrapper guard must require either a currently active site membership whose
   effective delegation ceiling still permits the workspace preset, or current
   active Platform Administrator authority. Deactivated/removed membership or
   lowered ceiling invalidates new requests and loses a race before mutation;
   inactive account/site/workspace/revoke/expiry remain fail-closed. Do not
   silently recalculate or widen the immutable delegated scopes.
2. **No scope widening.** Distinguish omitted `requested_scopes` (use full
   bounded preset intersection) from explicitly empty (persist empty). Exact
   requested set must remain requested ∩ delegator scopes ∩ site/system policy.
   Duplicate/unknown/above-preset/above-ceiling scopes fail without residue.
3. **Control mutation idempotency.** Require bounded `Idempotency-Key` and
   durable request digest for workspace create and capability issue. Same-key/
   same-body retry creates no second workspace/capability. Capability replay
   returns safe metadata with no token (or a stable one-time-already-delivered
   conflict), never stores/reconstructs plaintext and never leaves multiple
   unknown live tokens. Same key/different body returns 409. UI handles lost/
   replay response and supports revoke/reissue deliberately.
4. **Exact validation/error contract.** Align Pydantic and SQL bounds for every
   quota/TTL/origin/constraint; request quota cannot be zero. Map malformed/
   bounded-input `P0001` to stable 422, authority denial to non-leaking 403/404,
   exhausted Agent quota to 429 and infrastructure failure to 503.
5. **Site governance and audit actor.** Creator can inspect own workspace;
   authorized site governors with `workspace:read-all`, `capability:create` or
   `capability:revoke` can govern another delegator's Agent workspace as policy
   permits. Owner-defined DB functions independently recheck that permission.
   Security audit records the actual authenticated human actor for create/
   issue/revoke, not always the original delegator, and remains secret-free.
6. **UI truth.** After reload, list exact workspaces/capabilities and show
   ACTIVE/expired/revoked status truthfully; expired capability is not labeled
   active. Clear the displayed token on dismiss and revoke. Show all four
   presets but server ceiling remains authoritative.
7. **Migration reversibility.** Because 038/039 are still unmerged, make their
   downgrade chain truthfully restore the 037 authentication function/grants/
   defaults and remove only their added tables/triggers/functions/columns/
   constraints as appropriate. A downgrade-to-037/upgrade-to-head proof must
   pass privilege/readiness/authentication checks; no 038/039 behavior may
   masquerade under revision 037.

## Required public and database evidence

- Real PostgreSQL tests cover creator and distinct Site Owner governor, all four
  presets, omitted versus explicit-empty/narrow scopes, lowered ceiling and
  membership deactivate/remove races, Platform Administrator path, CSRF/non-
  member/cross-site/foreign IDs, exact validation statuses, idempotent create/
  issue replay+mismatch, quota accounting/replay/exhaustion, actual audit actor,
  grants/direct-role denial, rollback/no residue, restart, and full migration
  downgrade/upgrade.
- Public NGINX Playwright runs in desktop and phone projects: create/use L1 and
  L4 with exact expected scopes/limits; dismiss token; reload and rediscover;
  restart Control and Agent; inspect/use/revoke after restart; prove 401; prove
  no token in URL, DOM after dismiss/revoke, cookies, storage, later responses,
  logs or retained artifacts. Exercise at least nonmember/ceiling/CSRF denial
  through public product surfaces.
- Test must fail if Control routes/functions, actual context, request/mutation
  accounting, active-membership recheck, idempotency, security audit, durable
  list/revoke UI, or Agent call is removed. Fixture SQL is neutral setup and
  assertions only.
- Run full Python quality/unit/integration, Node, repository/Markdown/Mermaid,
  migration/privilege, focused reproducibility test, one clean Compose with
  exact restart/public E2E and every current GitHub check. Report exact commands,
  counts, environment, skipped/not-run items and first failing evidence.

## Scope and immutable report

No semantic-domain expansion, freeze/review/promotion, MCP/source/publication,
new dependency/hosted service, architecture/constitution/prior report edit,
production/release. Preserve supply-chain normalization except in-scope test
repair. Publish exactly
`oap/reports/074-c-close-session-governance-invariants.md` as immutable report-
only child of literal implementation SHA, with exact PR/base/head/commits/files,
all invariant evidence, migration history, E2E/restart/leak proof, checks/skips/
risks, no extra PR/merge and SELF.

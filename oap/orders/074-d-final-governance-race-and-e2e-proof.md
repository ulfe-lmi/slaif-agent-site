# OAP Work Order — 074-d

## Objective and verified state

Amend only PR #70 / `oap/074-human-agent-session-control-plane`; no new PR/
merge. Required starting report head
`29b7c74d3d2021ece8cf6c2d05db6e1828bde2d1`, sole parent
`20def0472b625d85d8b09ff402364e104e6a0de5`; `main` is
`74d9c189fe241356fbe03f2632197ecbb1ce53a3`; all 20 checks are green.
074-c fixed most governance defects, but inspection proves four exact residual
gaps. Close only these gaps and publish decisive evidence.

## Exact code repairs

1. Final 039 `slaif_human_agent_workspace_list` must allow the creator, active
   Platform Administrator, or an active site member whose effective permissions
   include `workspace:read-all`; it currently allows creator/platform only.
   Capability list/get/create/revoke functions must consistently honor their
   named active permissions and exact site/workspace without leaking foreign
   existence. Audit records the actual governor.
2. Replace/guard `control.slaif_agent_require_cow_site` at the 039 head so every
   semantic wrapper rechecks current active account/site/workspace plus active
   delegator membership/current ceiling or Platform Administrator immediately
   before semantic DML. The idempotency-begin check alone leaves a race window.
   Preserve site binding, trusted GUCs and zero residue. Restore the prior 026
   wrapper in 039 downgrade.
3. Make the 039→038→037 downgrade path explicit and testable: at 037, 038/039
   columns/indexes/triggers/tables/functions are absent, the exact 037
   `slaif_agent_capability_authenticate(text)` return contract/body/owner/PUBLIC
   revoke/Agent grant is restored, readiness/migration truth is 037, and a
   subsequent upgrade+reconcile to head restores 039 safely.
4. Do not edit earlier reports. The 074-d report must explicitly correct the
   074-c claims that all four presets, membership authority, restart and the
   requested downgrade-to-037 proof were already complete.

## Decisive evidence

- Real PostgreSQL tests with different humans: a Site Architect creates a
  workspace; a distinct Site Owner with `workspace:read-all` lists/gets it,
  issues/revokes a capability under exact permissions, and audit names the Site
  Owner. Deny missing permission, inactive membership and foreign site.
- Deterministic authority race: authenticate/reserve or pause at the existing
  boundary, then deactivate/remove membership or lower the ceiling before the
  semantic wrapper. The public/executor mutation must fail, and COW operation,
  semantic audit, idempotency completion and canonical state remain unchanged.
  Platform Administrator control case succeeds. Source/grant inspection alone
  is not proof.
- Test omitted scopes versus explicit empty and narrow scopes, duplicate/
  above-ceiling rejection, and all four preset exact effective scope ceilings.
- Add a targeted Alembic downgrade `039→038→037`, inspect columns/functions/
  grants and authenticate with the 037 contract, then upgrade/reconcile to 039
  and rerun privilege/auth checks. Full-base downgrade is not a substitute.
- Extend public NGINX Playwright/Compose evidence to create and use both L1 and
  L4, verify returned exact scopes/constraints/limits, dismiss, reload and
  rediscover, then revoke. After an actual Control+Agent service restart, rerun
  a recovery phase that finds the persisted workspace/capability metadata,
  uses any still-authorized test capability without logging it, revokes, and
  proves 401. Exercise public missing-CSRF, nonmember/low-ceiling denial on
  desktop/phone. Assert token absent after dismiss/revoke from URL, DOM,
  cookies, storage, later responses and retained test artifacts/log fields.
- Run focused tests first, then full Python quality/unit/integration, Node,
  repository/Markdown/Mermaid, migration/privilege, one clean Compose with both
  Agent-session projects plus restart recovery, supply-chain and every required
  GitHub check. Record exact commands/counts/skips; no generic claims.

## Scope and report

Only the functions/handlers/tests/Compose/docs necessary for the four gaps,
exact 074-d order/active and report. No new domain semantics, dependency,
freeze/review/promotion/MCP/source/publication, architecture/prior artifact,
production/release. Publish exactly
`oap/reports/074-d-final-governance-race-and-e2e-proof.md` as immutable report-
only child of literal implementation SHA, with exact commits/files/tests/
migration/race/public restart evidence/checks/skips/risks/no extra PR/no merge,
and SELF.

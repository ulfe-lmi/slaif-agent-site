# OAP Work Order — 074-b

## Objective and verified GitHub state

Amend only PR #70,
<https://github.com/ulfe-lmi/slaif-agent-site/pull/70>, branch
`oap/074-human-agent-session-control-plane`; no new PR/merge. Required starting
report head `2ec5de3978f4bb80d89e863ab453f90c05f60773`, sole parent
implementation `1d381ea644b5eaaf18a903b037343674a60648d0`; base/main
`74d9c189fe241356fbe03f2632197ecbb1ce53a3`. All 20 checks are green,
but green CI did not exercise the new product path and strategic review found
material contract/report gaps.

## Why 074-a is insufficient

1. `AgentCapabilityContext` declares resource and request/mutation/delete/
   upload quota fields, but migration 038's authentication function,
   `CapabilityAuthenticationRecord`, Agent/Control adapters and constructors do
   not return/populate them. They silently default to empty/zero. Source origins
   are likewise not carried. No general request quota is consumed, and the five
   existing Agent creates do not enforce the issued mutation quota.
2. No test calls the new Control workspace/capability functions/routes or uses
   the AI Sessions UI through public NGINX. Existing test edits cover route
   inventory/migration head and legacy 401s only. The order-required desktop/
   phone/restart/token-leak E2E is absent.
3. AI Sessions hardcodes Level 4/default quotas and keeps only one transient
   workspace ID. It provides no four-preset choice or durable session list, so
   reload loses monitoring/revocation access. “status/list” is not delivered.
4. Approved source values are merely prefix-checked strings; an approved origin
   must be canonical scheme/host/port with no credentials/path/query/fragment.
5. Capability/workspace create/revoke has no durable security audit.
6. The 074-a report omits exact files, commands, skips, branch/head and its two
   supply-chain normalizer changes; this correction must append truth without
   editing that immutable report.

## Required production repair

- Extend the fixed authentication record/SQL and all adapters so the exact
  immutable resource constraints, normalized source origins, and request/
  mutation/delete/upload/browser limits issued by Control reach every trusted
  Agent context without permissive defaults. Preserve the existing browser
  limits contract.
- Add atomic durable request-use accounting after secret validation and enforce
  request quota for reads/discovery/browser/mutations. Enforce mutation quota
  for the existing five create routes now; later delete/upload routes will use
  the carried limits. Replays must not double-consume mutation budget; invalid
  secrets/public-ID guessing must not consume a legitimate capability.
- Add site-scoped AGENT workspace listing and metadata/capability rediscovery
  after reload, with creator and `workspace:read-all`/governance semantics;
  authorized `capability:revoke` must work after restart. Never redisplay token.
- UI lets the human choose all four documented presets and bounded TTL/quotas;
  optional advanced source origin/resource restrictions remain understandable.
  Show token once with an explicit dismiss/copy workflow; no local/session
  storage, URL, cookie, later response or logs retain it.
- Parse/canonicalize approved origins and reject userinfo, non-http(s), path
  beyond `/`, query, fragment, whitespace/control, duplicates and malformed
  ports/hosts. Egress/private-address enforcement remains Objective 087.
- Add append-only secret-free security audit for workspace creation,
  capability issuance and revoke, transactionally coupled to each Control
  action and unavailable to Agent UPDATE/DELETE.
- Either add focused deterministic tests for the in-scope Next app-path
  manifest normalization in `tools/supply_chain/{evidence,reproducible}.py` and
  report why the new route required it, or revert those changes if unnecessary.
  Do not broaden normalization or hide executable differences.

## Required evidence and anti-bypass

1. Real PostgreSQL integration invokes every new owner function through the
   exact `slaif_control`/Agent roles and proves preset/ceiling/scope/site/CSRF/
   expiry/revoke/list/audit/quota behavior plus direct-role denials and zero
   unauthorized residue.
2. Public NGINX Playwright E2E on desktop and phone: login as real Site Owner;
   select each preset (at least L1 and L4 full creation); create workspace;
   receive token once; use that exact token on Agent session and one existing
   semantic create/read; verify exact scopes/constraints/quotas; reload UI and
   rediscover session without token; revoke; Agent returns 401; restart Control/
   Agent and repeat metadata/revocation proof. Inspect URL, DOM after dismiss,
   cookies, local/session storage, response bodies and captured logs/artifacts
   for token absence. Nonmember, insufficient ceiling/permissions, missing
   CSRF, foreign IDs, bad origin, TTL/quota overflow and exhausted quota fail.
3. Tests must fail if routes/UI/functions/context propagation/accounting/audit
   are removed. Direct SQL may seed neutral users/sites and assert DB state but
   cannot perform claimed human/Agent actions.
4. Run full Python quality/unit/integration, Node, repository/Markdown/Mermaid,
   focused supply-chain normalization, one clean Compose/public E2E, restart,
   privilege/secret checks and every required GitHub check. Report exact
   commands/counts and any skipped/not-run work; no vague “targeted suites.”

## Scope, safety and report

No new dependency/hosted service, semantic domain expansion, freeze/review/
promotion, MCP/source/publication, architecture/constitution/prior report edit,
production access/release. Keep one PR. Publish exactly
`oap/reports/074-b-complete-session-authority-and-proof.md` as immutable report-
only child of literal implementation SHA, with exact PR/base/head/commits/files,
074-a corrections, migrations/grants/audit/quota semantics, E2E/log-leak proof,
commands/checks/skips/risks, supply-chain explanation, no extra PR/merge, SELF.

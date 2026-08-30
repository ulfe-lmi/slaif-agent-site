# OAP Work Order — 075-g

## Objective and verified state

Amend only PR #71 / `oap/075-editable-domain-substrate`; no new PR/merge.
Required starting report head
`6442388b53da0bdd261772877339aefa377461af`, sole parent
`6e65d58e2925c9e4555a3d53aaf4827baff29d94`; main/base
`ef456e63abadddfc7d90794c03be3a63677c87f9`; all 20 checks are green.
075-f closes its production-upgrade/site-data scope. Close exactly three
remaining hostile-audit defects, then Objective 075 is merge-ready.

## Three required repairs

1. **Restore Agent COW/site binding in 040.** Every recreated
   `slaif_agent_field_definition_create/list` SECURITY DEFINER function in the
   040 upgrade and its downgrade-restored contract must call
   `control.slaif_agent_require_cow_site(p_site_id)` before any lookup/DML and
   retain fixed search path/PUBLIC revoke/Agent-only grant. A site-A bound Agent
   session passing site B/type B must fail before disclosure or mutation.
2. **Reject stale content-definition writes.** `update_item`, translation
   create/update, and relation create/update must compare each affected item's
   persisted `type_definition_version` to the exact current active
   `content_type.definition_version`; relation field/source/target definitions
   must be current where applicable. A definition bump without an approved
   declarative mapping makes those writes 422 and leaves COW/audit/idempotency/
   canonical state unchanged. Do not silently rewrite the stored version.
3. **Reject localized collection projection misuse.** The shared query
   validator must reject localized fields in projection just as it rejects them
   for filter/sort, because Render item `values` contains only nonlocalized
   data. Editor cannot persist such a view; Render must fail closed on a
   malicious/legacy stored localized projection rather than crash or emit an
   incomplete result. Locale-aware collection projection is later explicit
   work, not implicit fallback.

## Decisive evidence

- Real least-privilege Agent/COW test invokes the public create/list route or
  exact wrapper with a site-B type under a site-A capability/session and proves
  stable non-leaking denial, no field, no operation, no audit/idempotency and
  canonical unchanged. Inspect upgrade and downgrade function definitions/
  owner/grants; 040→039→040 retains the guard.
- Real Editor/Agent COW tests create valid item/translation/relation, bump the
  content-type definition, then attempt item update plus translation and
  relation create/update. Every stale write is 422/no residue; a current-
  version control succeeds. Include cross-site and mapping-not-provided cases.
- Shared validator unit tests and real Editor+Render integration reject a
  localized projection before persistence; owner-injected malformed legacy
  view yields stable Render failure with no private/cross-site data. A
  nonlocalized projection control still renders exactly.
- Run focused tests then full Python quality/unit/integration/PG14–18,
  Editor/Agent/Render/Puck, migration/privilege, Node, clean relevant Compose,
  repository/Markdown/Mermaid/supply-chain and all 20 checks. Exact commands/
  counts/skips; no pending/failure.

## Scope and report

No other 075 behavior, new entity/API, navigation/redirect/locale/effect change,
Agent CRUD expansion, MCP, freeze/publication, dependency, architecture/prior
report edit, production/release. This is the final Objective 075 correction.

Publish exactly
`oap/reports/075-g-close-agent-binding-definition-and-localization.md` once as
immutable report-only child of literal 40-hex implementation SHA. Include exact
PR/base/head/commits/files/function definitions/tests/checks/skips/risks/no
extra PR/no merge and SELF. No post-report push.

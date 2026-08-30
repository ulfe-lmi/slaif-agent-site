# OAP Work Order — 075-f

## Objective and verified state

Amend only PR #71 / `oap/075-editable-domain-substrate`; no new PR/merge.
Required starting report head
`ed3e2b6f852bdee2084023d393204ca3d9026510`, sole parent
`ecb1265fb8d2b5dab6f5c0377bb4c4bbc771b6e9`; main/base
`ef456e63abadddfc7d90794c03be3a63677c87f9`; all 20 checks are green.
All intended 075 data families now exist, but final review found production-
upgrade and relational-integrity gaps. Repair only these and close Objective 075.

## Production COW upgrade invariant

Current tests fresh-install head, reconcile, then downgrade. They do not prove
the real upgrade path: deploy through 039, reconcile/harden so existing content
names are COW views, then upgrade through 040/041/042. Those migrations alter
`field_definition`, `collection_view`, `navigation` and `page` by logical names
and may be operating on views.

- Implement/test an architecture-compliant maintenance upgrade using only the
  foundation's documented public APIs: require no pending/active COW work,
  safely prepare/teardown the COW schema where required, run Alembic 040–042,
  redeploy/enable/harden/validate, and preserve canonical rows, sequences,
  indexes, functions and grants. Do not depend on private foundation tables or
  undocumented SQL.
- Add a staged real PostgreSQL proof: install/reconcile/harden at 039 with
  representative canonical type/field/item/view/page/navigation/media/theme;
  prove runtime names are views; run the actual product upgrade/reconcile to
  042; verify every canonical row, new backfill, COW triplet, privilege and
  runtime operation; then exercise downgrade/upgrade in the supported empty-
  pending maintenance state. Pending COW operations must make upgrade fail
  before destructive preparation.

## Site-data integrity repairs

1. Backfill exactly one canonical `site_locale` for every existing active site
   from `control.site.default_locale` during 042 upgrade, with deterministic
   normalized tag/default state. Enforce one enabled default in the visible
   site projection and later-update consistency without writing Control from
   Editor. Add composite locale references (or equally strong validated DB
   constraints compatible with COW) for page, navigation-item and redirect;
   cross-site/missing/disabled locale cannot be persisted.
2. Add composite `(workspace_id,site_id)` FK/binding for
   `proposed_side_effect`. The create function derives or strictly equals the
   trusted current COW `app.session_id`, requires that ACTIVE workspace/site,
   and cannot accept a caller-selected foreign workspace. It remains inert and
   nonpublic.
3. Navigation target consistency: PAGE requires a same-site `page_id` and
   `target_value` derived/equal to it; INTERNAL/EXTERNAL require `page_id=NULL`.
   Parent must share site+navigation. Sibling positions are unique or assigned
   transactionally with deterministic move/rebalance; concurrent moves/creates
   serialize on the navigation and cannot create duplicate order/cycle/depth.
   Remove all “row missing → return last existing row” fallbacks; absence is a
   failure, never another resource.
4. Redirect create and update use the same validation: only 301/302/303/307/308,
   normalized unique source+locale, safe target, reserved exclusions, no self or
   indirect loop/unsafe chain. Serialize per-site redirect mutations so
   concurrent A→B/B→A cannot commit a cycle. Stable 409/422 and zero residue.
5. Ensure locale/default, nav target/order, redirect loop/status and side-effect
   constraints are enforced in shared service/validator plus strongest
   practical DB functions/triggers, not UI only. Update/deletion retains
   optimistic row versions and clear/unset semantics.

## Required evidence

- Real staged 039-hardened→042 production upgrade and pending-work rejection as
  above, across the PG matrix where CI supports it.
- Authenticated Editor COW tests for default-locale backfill/constraints,
  PAGE/INTERNAL/EXTERNAL targets, sibling concurrency, cycle/depth, exact create
  identity, redirect statuses/indirect/concurrent loops, and proposed-effect
  foreign/current-session binding. Prove canonical/other-site unchanged,
  promotion/discard, audit/idempotency and no effect execution.
- Negative direct-role/function/grant, FK, stale version, cancellation/pool and
  zero-residue matrix. Tests must fail if DB constraints/serialization or shared
  validation is removed; fixture SQL is setup/assertion only.
- Run focused tests then full Python quality/unit/integration/PG14–18, Node,
  Editor/Puck/Render/Agent, clean Compose, repository/Markdown/Mermaid/supply-
  chain and all 20 checks. Exact commands/counts/skips; no pending/failure.

## Scope and final report

No new entity/API family, Agent REST/OpenAPI/MCP, dynamic detail, composition/
design/media, side-effect executor, freeze/publication, dependency/hosted
service, architecture/prior report edit, production/release. This is the final
Objective 075 remediation; merge only if all 075-a..f behavior/evidence is sound.

Publish exactly
`oap/reports/075-f-production-upgrade-and-site-data-integrity.md` once as an
immutable report-only child of literal 40-hex implementation SHA, with exact
PR/base/head/commits/files/upgrade/migration/schema/grants/concurrency/tests/
checks/skips/risks/no extra PR/no merge and SELF. No post-report push.

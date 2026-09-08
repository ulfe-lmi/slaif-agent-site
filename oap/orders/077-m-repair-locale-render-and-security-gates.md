# OAP Work Order — 077-m

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`ced67e819a101ea01dda92bdba649cc838ddd6cf`, whose sole parent is blocked
077-l implementation `92706355de37b38d6eda10ed8c0447415ca234b8`. Remote
`main` remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

077-l made valid static Render improvements but is not accepted. Repair its
concrete Agent/structure failure, finish the evidence it still lacks, and clear
the newly failing Apache supply-chain gate without an exception. Dynamic
`{slug}` collection-detail behavior remains strictly out of scope.

## 1. Diagnose the exact page-delete failure in the COW transaction

The failing public journey reads the Agent-created `internal_page_id` as 200/
row-version 1, then DELETE returns 404. The added owner diagnostics query the
canonical view without `app.session_id`; they cannot prove dependencies or
redirect state inside the Agent workspace.

Capture the exact SQLSTATE, safe semantic database code, route/default-locale,
and complete workspace-visible dependency counts through a trusted test COW
session or an equivalent non-secret diagnostic. Do not expose raw SQL/database
details in the public response or retain temporary diagnostics in production.

The likely triggering sequence must be tested rather than assumed: 077-l adds
canonical/preview redirects targeting `/`; the Agent journey then makes
`sl-SI` default without creating a `sl-SI` home page. That changes effective
routes and can leave `/` dangling. A later page mutation invokes migration
051's complete redirect guard. Establish the actual cause and report it.

## 2. Make locale changes preserve complete route/redirect integrity

Locale creation/update/default-switch/disable/delete can change effective page
routes and redirect/navigation resolution. They must participate in the same
workspace+site structural serialization and complete post-mutation validation
as pages, navigation and redirects.

- Keep requested-locale authorization/resource checks at the capability
  boundary, but validate the complete resulting workspace page/locale/
  navigation/redirect graph under the shared structural lock.
- A default switch or disable/delete that would create a duplicate/unreachable
  page route, dangling PAGE/INTERNAL navigation target, redirect source
  collision, dangling redirect target, ambiguous fallback, loop or chain
  overflow must roll back atomically with one stable non-leaking domain
  conflict.
- A structurally valid switch with a home/static target for the new default
  must succeed and update every affected locale row version exactly once.
- Preserve capability/site/workspace authority, COW isolation, row versions,
  quota/idempotency/audit rollback, same-key retry, cancellation, and exact
  downgrade restoration/grants. Agent and Editor locale/structure writes must
  not use different locks or validators.
- Do not paper over the problem by deleting the new redirect cases, changing
  them all to external targets, bypassing the graph guard, or weakening the
  page DELETE expectation. Make the public journey structurally valid—for
  example, create the required `sl-SI` home through public Agent HTTP before
  switching default, then clean it up dependency-correctly—and retain the
  negative invalid-switch case separately.

Add deterministic real-PostgreSQL tests for invalid and valid default switches,
Agent locale switch racing Editor/Agent redirect or page mutation, cancellation
after tentative locale change, retry with the same idempotency key, and the
original page delete/restore after a valid switch. Use lock/event barriers, not
timing sleeps. Prove canonical/other-workspace/site state is unchanged.

## 3. Finish the still-missing 077-l Render evidence

Do not relabel old authorization-lock tests as proof of new snapshot behavior.
At current head, the structure-router test now covers Agent page move and one
random foreign-workspace denial, but still does not prove all ordered cases.
Close them directly:

1. Through public Agent HTTP, delete and restore the moved page and observe
   exact absence/restoration/effective route in authorized Render preview,
   while canonical and a separately authorized second workspace/site remain
   unchanged.
2. Use a genuine run-bound browser-preview credential on the Agent-created
   nested/localized structure; prove site/workspace/route binding, one-time
   consumption, no token projection, and replay denial.
3. Add a deterministic production-query barrier after canonical/preview
   repeatable-read snapshot establishment; concurrently commit a public
   Agent/Editor page/locale/navigation/redirect mutation and prove the Render
   result is a complete before-state or complete after-state, never mixed.
4. Cancel canonical and preview projection while in flight; prove transaction
   closure, restored preview connection isolation/session context, usable pool,
   correct one-time credential handling, and successful subsequent render.
5. Restart the Render app/process boundary and resolve the same durable
   authorized workspace state with canonical isolation intact.
6. Expand the corruption matrix beyond the current three cases to cover a
   dangling/foreign PAGE target, unsafe INTERNAL and EXTERNAL targets,
   duplicate and non-dense positions, missing/cross-navigation parent, cycle,
   excessive depth/count/JSON, disabled/unknown locale, duplicate default,
   visible missing label, and unrelated corrupt/dynamic page ambiguity.

The locale-hidden label regression and public all-status redirect evidence from
077-l must remain. At the public NGINX/Web boundary, keep exact 301/302/303/307/
308 statuses and Locations for canonical and human preview, preview internal-
route confinement, external HTTPS targets, preview response no-store/noindex/
CSP headers, and browser-token single consumption. Tests may use deterministic
instrumentation around production stages but may not mock away DB, COW, auth,
route or projection behavior.

## 4. Clear the new Apache Critical gate without an exception

The current vulnerability database reports eight unexcepted Critical findings
for the Apache image (`CVE-2026-10536`, `CVE-2026-11564`, `CVE-2026-11856`,
`CVE-2026-8924`, `CVE-2026-8925`, `CVE-2026-8926`, `CVE-2026-8927`,
`CVE-2026-9079`). This is a real current-head required-check failure.

Official state independently observed on 2026-09-06: Apache's current GA is
still 2.4.68; Docker Official Image publishes
`httpd:2.4.68-alpine3.24` with multi-platform index digest
`sha256:1b766f17b84026429b7cb243317b142921b24432336e798bc881c43f45ed9567`.

- Inspect the exact Grype matches, packages, installed/fixed versions and
  reachability; record them without suppressing findings.
- Qualify the current official 2.4.68 Alpine 3.24 image and update the Apache
  base/pins/policy/docs/tests/lock evidence consistently only if the exact
  digest and rebuilt final image pass all Apache behavior, reproducibility,
  SBOM, license and zero-unexcepted-Critical gates.
- Adjust Alpine package pins to versions actually supplied/fixed by 3.24; do
  not use mutable tags in committed runtime references.
- Do not modify other images merely for version uniformity, do not downgrade
  Apache, and do not create/extend a vulnerability exception. If Alpine 3.24
  still has an unfixable Critical finding and no qualified official fixed
  image/package exists, report the exact upstream blocker; never weaken the
  scanner or policy.

Preserve Chrome `152.0.7977.82`, its completed qualification, the empty current
exception set, and all unrelated security/license gates. GitHub issue #67 stays
open until the containing Objective 077 result is merged to verified `main`.

## Verification and boundaries

Run focused locale/redirect/page-delete, Render snapshot/cancellation/browser/
corruption, and all-status edge tests first; full Agent/Editor/Render/bootstrap
integration; migration upgrade/downgrade/re-upgrade and privilege checks;
Python quality/unit/integration; Node contracts; PG14–18; repository/Markdown/
Mermaid; a clean Compose public journey; reproducible Apache builds and complete
supply-chain evidence; then all current-head CI. Push before observing CI and
repair only in-scope failures. Superseded, skipped, pending or cancelled checks
are not passes.

No dynamic `{slug}` or collection-detail implementation; no new Agent public
route; no 078 composition/design/Puck; no media/MCP/freeze/review/promotion/
source/sweep/076; no architecture/historical-order/report/general-refactor/
production/release change; no exception or issue closure. Do not remove or
weaken any test merely to clear Compose.

Commit this exact order and `oap/active` unchanged, push only the existing PR
branch, create no PR, and never merge/auto-merge. Publish exactly
`oap/reports/077-m-repair-locale-render-and-security-gates.md` as the final
report-only child of a literal implementation SHA with
`Report publication commit: SELF`. Include the exact page-delete root cause and
SQLSTATE; migration/functions/grants; valid/invalid locale graph outcomes;
race/cancellation/retry/audit/quota/COW results; every missing Render case above;
all five public redirect/header outcomes; exact Apache package/CVE before/after,
official tag/index/final digest, SBOM/scan/reproducibility/license evidence;
commands/counts/skips/current checks; no secret/scope/extra PR/merge/exception;
remaining dynamic-detail/final 077 scope; and strongest reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker with
exact attempted evidence. Do not return merely because tests/Compose/CI are
long. No post-report push. Signal exact FIFO `OK`, then wait for strategic
review.

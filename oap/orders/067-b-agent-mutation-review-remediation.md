# OAP Work Order — 067-b

## Objective

Remediate the strategic review findings for objective 067 on the existing
Agent mutation PR. Preserve the bounded five-route COW mutation surface while
adding the missing wrong-site/resource, scope, replay-state, and direct
wrapper-boundary proof required by 067-a.

## GitHub objective state

- Numeric objective: `067`; round: `067-b`
- Mode: `AMEND_EXISTING_PR`; continue PR #58 on branch
  `oap/067-agent-mutations`
- Current report-head SHA: `2bc1213a31f179bfaaf4231b837edbbb19cba76a`
- Current base: `main` at `e647fb850f963bf0e9793273b28fccf6e8811bc7`
- Current report-head required checks are green and PR state is `CLEAN`.
- Do not create a second PR and do not merge.

## Strategic review findings

1. The report claims wrong-site/resource and validation coverage, but the
   integration tests only exercise successful route creation and generic
   privilege negatives. They do not prove a capability for site A cannot use
   a type/page/parent from site B, nor do they prove insufficient mutation
   scope and malformed mutation requests through HTTP.
2. The five `SECURITY DEFINER` Agent content wrappers check that COW settings
   are non-empty but accept `p_site_id` independently of the workspace/session
   context. The server route currently passes trusted context, but the
   runtime role can execute these narrow wrappers directly. The database
   boundary must fail closed and bind the supplied site to the workspace
   represented by `current_setting('app.session_id')`; do not rely only on the
   Python caller for this invariant.
3. The replay test checks equality of the stored response but does not assert
   that replay leaves the set/count of pending COW operations unchanged. The
   mismatch test likewise needs an explicit unchanged-state assertion.

## Required changes

1. Keep exactly the five bounded create routes from 067-a and the existing
   capability-derived `site_id`, `workspace_id`, scopes, and operation
   identity. Do not broaden the Agent API or add lifecycle/publication routes.
2. Harden every Agent content wrapper in revision `025_001` (or a minimal
   follow-up migration if the existing migration is already applied in the
   supported workflow) so its `p_site_id` must equal the active workspace's
   site, using fully qualified control-plane lookup from the trusted COW
   session setting. Require valid active COW context and preserve owner,
   `SECURITY DEFINER`, fixed `search_path`, and least-privilege grants.
3. Map wrapper-level not-found/resource validation failures to the existing
   stable HTTP error envelope and appropriate not-found/conflict semantics;
   do not turn a client-addressable wrong-site/type/page/parent rejection into
   an opaque false-success or an avoidable generic 503. Preserve fail-closed
   behavior for unavailable infrastructure and missing COW context.
4. Add real PostgreSQL integration coverage using the actual Agent runtime
   role and capability-authenticated HTTP route for:
   - a site-A capability attempting a field/component/parent operation against
     a canonical resource belonging to site B, with rejection and no COW or
     idempotency residue;
   - a capability lacking each relevant create scope receiving the stable
     authorization error;
   - malformed body/path combinations and wrong parent/type relationships;
   - direct runtime-role invocation of an Agent wrapper with a valid COW
     session for the wrong site, proving the database boundary rejects it;
   - same-key replay leaving exactly the original operation set/count and
     returning the identical stored response and operation UUID; and
   - changed-digest mismatch leaving operation, overlay, canonical, audit,
     and idempotency state unchanged.
5. Retain and rerun the existing success, canonical-isolation, cancellation,
   pool-cleanup, audit, base/change-table, reviewer, and lifecycle-boundary
   evidence. Do not weaken tests to accommodate implementation details.
6. Update only truthful API/security/test documentation if behavior or error
   semantics changed. Do not claim promotion, publication, hostile-public-SaaS
   isolation, or production readiness.

## Acceptance criteria

- No second objective PR exists; PR #58 remains the unique objective PR.
- All five 067-a routes still return valid semantic records and one durable
  operation UUID on successful COW-backed creation.
- Site/workspace/operation context is server-owned and database-enforced;
  wrong-site direct wrapper use fails closed.
- Wrong-site resources, wrong parents/types, missing mutation scopes, and
  malformed requests have explicit, tested stable outcomes with no mutation
  residue.
- Replay equality is accompanied by proof of no second pending COW operation;
  mismatch is accompanied by proof of unchanged durable and overlay state.
- Canonical tables remain unchanged; Agent runtime retains no base/change-table,
  reviewer, lifecycle, arbitrary SQL/DDL, or direct control-table DML authority.

## Verification and report contract

Run and report exact focused HTTP/unit/route-policy/idempotency tests, real
PostgreSQL integration tests, backend quality and repository-required policy,
security, packaging, documentation, and `git diff --check` checks. Rerun the
full relevant suite after fixes and report every status honestly.

Commit implementation changes on the existing PR branch, push them, and
publish a new immutable `067-b` report-only commit whose first parent is the
implementation head. Verify remote PR identity/head/base and report parent
before signaling. The report must include `Report publication commit: SELF`,
all evidence, limitations, and `RESULT=OK|PARTIAL|BLOCKED|FAILED`.

Never edit the activated `067-a` order or report, never merge, and do not
activate objective 068 until strategy independently accepts and merges 067.

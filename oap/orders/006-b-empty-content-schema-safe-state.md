# OAP Work Order — 006-b

## Objective

Amend the existing objective `006` pull request so the clean, intentionally
table-free `content` schema has an explicit and truthful ready state:
**safe-empty / foundation hardening not applicable**. It must never be labeled
hardened, and the first real content table must still require successful public
foundation hardening and validation before readiness can be true.

Also close any other review defects found while implementing this narrow state
transition and ensure every final report-head GitHub check succeeds. Do not add
a placeholder/domain table, patch or fork the foundation, or weaken a
privilege invariant.

## GitHub objective state

- Numeric objective: `006`
- Execution round: `006-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#9`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/9>
- Required head branch: `oap/006-postgres-cow-bootstrap`
- Base branch: `main`
- Required PR title: `[OAP 006] Add PostgreSQL role and COW bootstrap baseline`
- Repository: `ulfe-lmi/slaif-agent-site`
- Current remote PR head:
  `1f07ca4b53144c1045b6117cf0439afe3c707c1e`
- Previous implementation head:
  `65f8430be15780d3e7abcf804bd92ce1bb0f5c5e`
- Required delivery: amend PR `#9`; creating another PR is prohibited.

## Strategic review of 006-a

The first round correctly implemented the role, migration, bootstrap,
privilege, packaging, documentation, and PostgreSQL-matrix baseline and
reported `PARTIAL` rather than inventing evidence. The representative-table
path passes. The clean path remains unsafe only because public
`agent-cow-postgresql==0.2.0` deliberately raises when
`harden_cow_schema(...)` is called without any enabled table.

There is no newer non-yanked foundation release on PyPI at this review point;
`0.2.0` remains the sole release. Adding a dummy table, pulling unpublished
foundation source, or prematurely implementing a domain table would violate
the architecture and current objective.

The final `006-a` report head also has one GitHub CodeQL JavaScript/TypeScript
job failure caused solely by GitHub returning HTTP 429 while downloading the
pinned CodeQL action during job setup. Python/actions analyses succeeded and
there is no open code-scanning alert. The continuation push will create fresh
checks; every final report-head check must be successful before the turn may be
accepted.

## Strategic decision

Treat hardening as **not applicable only when the product independently proves
that `content` is exactly empty and uncreatable by every non-owner role**.

This is not a waiver and not foundation-validation success. Persist a typed
content/COW readiness state with at least these meanings:

```text
PENDING       migration/reconcile incomplete or unsafe
EMPTY_SAFE    content has no user objects; hardening is not applicable
HARDENED      one or more COW tables exist and foundation hardening plus
              foundation and product privilege validation succeeded
```

Equivalent stable names are acceptable, but booleans must not imply that
foundation hardening or foundation privilege validation ran in `EMPTY_SAFE`.
Overall `safe=true` may be published only for `EMPTY_SAFE` or `HARDENED` after
the corresponding evidence below succeeds.

## Scope

Change only existing objective-006 paths needed for the marker/state machine,
reconcile/validate logic, privilege verifier/grants, tests, documentation,
repository policy, and the new OAP order/report. Preserve the original 006-a
allowed-path boundary. Do not add a new dependency, migration head, product
table, process, route, pool, Compose/edge file, or unrelated refactor.

Because no accepted deployment can yet exist, revise the unmerged `006_001`
baseline in place and retain exactly one migration head rather than adding a
repair migration solely for this pre-merge correction. Do not rewrite Git
history or modify the immutable 006-a report.

## Requirements

### A. Detect empty state without private or brittle foundation knowledge

- Keep calling public `deploy_cow_functions(...)` and
  `enable_cow_schema(...)` with deferred FKs enabled and unsafe canonical
  writes disabled.
- Do not catch or compare the literal foundation exception string
  `Schema 'content' has no COW-enabled tables` as control flow.
- After enablement, determine whether `content` is empty through generic
  PostgreSQL catalog/object inventory owned by Agent-Site. Do not decide from
  the return list alone because repeat enablement may return no newly enabled
  table even when previously enabled COW objects exist.
- `EMPTY_SAFE` requires no user relation, view, materialized view, sequence,
  function/procedure, or other product-created executable/data object in
  `content`. Any unknown object makes the state unsafe; do not guess that it is
  harmless.
- If any content object exists, invoke public `harden_cow_schema(...)` and
  `validate_cow_schema_privileges(...)`; failure remains fatal and the marker
  remains `PENDING`/unsafe.

### B. Truthful marker and state transitions

- Replace the misleading all-boolean completion constraint with an explicit,
  typed, database-constrained readiness state. `EMPTY_SAFE` must leave
  hardening/foundation-validation evidence explicitly not-applicable or false,
  never true.
- Store enough separate facts to distinguish foundation deployment, product
  privilege validation, foundation hardening/validation, and overall
  readiness without contradictory combinations.
- Database constraints must reject impossible combinations, including
  `safe=true` with `PENDING`, `HARDENED` without both foundation checks, or
  `EMPTY_SAFE` while claiming hardening ran.
- Reconcile always makes the marker unsafe first. Publish the final state only
  as the last action after the applicable transaction and all independent
  checks succeed.
- `current` and `validate` output/report the stable state without revealing
  credentials or internal exception text.

### C. Safe-empty privilege proof

For `EMPTY_SAFE`, apply/reconcile product revokes and independently prove:

- the clean product-object inventory is exact;
- `content` is owned by `slaif_owner` and contains no user object;
- `PUBLIC` and every non-owner product role lack `USAGE`/`CREATE` or any
  relation/function/sequence authority not explicitly allowed;
- Agent, Editor, Reviewer, readers, Control, Scheduler, Media, and GC have no
  effective content DML/ownership/setup/reviewer surface in an empty schema;
- Reviewer has no residual foundation function grant merely because such a
  grant would be valid after hardening;
- no direct or inherited over-grant, combined service principal, or unexpected
  product-schema object exists;
- the foundation deployment exists and its schema/functions are protected
  from `PUBLIC` and non-applicable service roles.

The product verifier must treat reviewer foundation functions statefully:
zero reviewer execution is expected in `EMPTY_SAFE`; the exact controlled
reviewer surface is required and checked by foundation validation in
`HARDENED`.

### D. Hardened non-empty path

- Preserve the fully passing representative-table path.
- A first run with a real table must enable, harden, foundation-validate,
  product-validate, and publish `HARDENED` atomically.
- A repeat run over already enabled COW objects must remain `HARDENED` even if
  public enablement reports zero newly enabled tables.
- If an object appears after an `EMPTY_SAFE` marker, `validate` fails closed
  until reconcile performs successful enable/harden/full validation.
- Removing/renaming or over-granting a managed object must make validation and
  readiness fail; no automatic downgrade to `EMPTY_SAFE` is permitted unless
  the schema is truly object-free and all safe-empty checks pass.

### E. Failure, validation, and idempotence

- Exercise failure injection in both state paths before final marker
  publication; each failure must roll back the applicable changes, retain an
  unsafe marker, and permit a safe retry.
- `bootstrap` on the clean baseline must now exit successfully with
  `safe=true` and the explicit `EMPTY_SAFE` state.
- `validate` on that baseline must independently reproduce the empty proof and
  succeed. It must not call or claim successful foundation table-privilege
  validation when there are no COW tables.
- Repeated clean bootstrap/validate remains a no-op apart from any intentionally
  documented marker timestamp behavior; migration head/object/grant state must
  not drift.
- Preserve constant CLI errors, mounted secret-file behavior, transaction/
  cancellation/pool cleanup evidence, and no import-time side effect.

### F. Tests

Add/adjust tests that would fail under the 006-a implementation and prove:

1. clean migration plus bootstrap yields `EMPTY_SAFE` and overall safe, while
   foundation hardening/validation are explicitly not claimed;
2. exact empty object/ACL/function inventory and zero reviewer function grant;
3. clean `current`, `validate`, repeat bootstrap, downgrade, and rebuild;
4. an unexpected table/view/sequence/function in `content` prevents
   `EMPTY_SAFE` validation;
5. an object added after the safe-empty marker invalidates it until successful
   full reconcile;
6. representative first-time and repeat COW-table reconcile yields
   `HARDENED` with public foundation and product validators safe;
7. direct/inherited/reviewer/public over-grants are detected in the correct
   state;
8. injected failures cannot publish either ready state prematurely;
9. source contains no exact-message exception control flow, dummy/placeholder
   production table, or private foundation import/object dependency;
10. PostgreSQL 14–18, Python 3.12–3.14, packaging, and repository gates remain
    green with no skipped required test.

### G. Documentation and report honesty

Update database bootstrap/role/current-status documentation to explain the two
valid readiness states and the mandatory transition to full hardening when the
first trusted content table arrives. Remove wording that clean bootstrap is an
unresolved failure. Keep the limitation that no product-domain table or online
database path exists.

Record the previous external CodeQL 429 accurately if relevant, but do not
represent it as a code defect or as a passing final check. The final report
must be `COMPLETE` only if every objective criterion is met and every fresh
report-head check is successful/present; otherwise report the exact remaining
state.

## Non-goals

- No foundation version/source change, fork, monkey patch, private import, or
  upstream repository modification.
- No dummy/sentinel/placeholder/domain content table, user/site/auth/workspace/
  capability/job/content/page/audit data, online service pool, readiness route,
  Compose, container, NGINX/Apache, or deployment credential wiring.
- No relaxation of role attributes, memberships, PUBLIC revocation, base/
  change protection, reviewer separation, or unsafe canonical-write policy.
- No second PR, merge, auto-merge, force-push/history rewrite, action on PR
  `#5`/`#7`, new objective, release, issue, or GitHub setting change.

## Acceptance criteria

1. PR `#9` remains the unique non-draft objective-006 PR on the required
   branch/base/title and receives only continuation commits plus the immutable
   006-b report-only `SELF` commit.
2. The clean production baseline has no `content` object and bootstraps to a
   database-constrained `EMPTY_SAFE` state with overall readiness true but no
   false hardening/foundation-validation claim.
3. Safe-empty validation proves exact object absence, owner/schema/PUBLIC/role
   boundaries, no reviewer foundation surface, no over-grant, and protected
   deployed foundation objects.
4. Any content object invalidates `EMPTY_SAFE`; a real representative table
   reaches `HARDENED` only after public enable/harden/foundation validation and
   independent product validation all succeed.
5. First and repeated empty/non-empty runs, validation, failures, retry,
   downgrade/rebuild, cancellation, and pool cleanup remain deterministic and
   truthful on PostgreSQL 14–18.
6. No brittle foundation exception-text branch, placeholder table, private API,
   new dependency, second driver, scope expansion, secret leak, or weaker
   privilege exists.
7. Documentation and CLI/status output explain exact state semantics and
   future migration obligations without overclaiming product readiness.
8. All local gates and every final report-head GitHub CI/CodeQL check succeed;
   no CodeQL alert remains open.
9. `oap/active` is `006-b`, both 006 orders/reports correlate uniquely, prior
   artifacts remain immutable, and the final remote head is report-only
   `SELF` with the literal implementation parent recorded.

## Verification required

Run the complete 006-a verification set again, including exact uv/frozen
dependency, Ruff/format/mypy, unit/repository, both PostgreSQL integration
suites, package/clean-wheel, Alembic head/history/offline SQL, Node, Markdown,
Mermaid, diff, scope, protected hashes, secret/private-API scan, and PostgreSQL
14–18 GitHub matrix.

Additionally report exact empty and hardened state rows, object/ACL/function
inventories, first/repeat/failure/retry transitions, unexpected-object and
over-grant negative results, and proof that no clean content table exists.
Required tests may not be skipped or reclassified as not applicable except the
foundation *table* hardening/validation operation represented explicitly as
not applicable in a proven `EMPTY_SAFE` state.

## Safety / security constraints

Use only disposable PostgreSQL and fake test credentials. Never print a DSN or
password. Fail closed on an unknown marker/state/object/grant. Do not broaden
authority to make a test pass. A safe-empty state is valid only because there
is no mutable/readable content object and no role can create one.

## Local execution capability

Routine database recreation, migration, role/ACL inspection, local
PostgreSQL/container setup, dependency work, and CI diagnosis remain the coding
agent's responsibility in its disposable VM. Do not transfer them to the
human/strategic model.

## GitHub workflow

Fetch GitHub, verify PR `#9` is open and unchanged in identity, check out
`oap/006-postgres-cow-bootstrap`, and amend that same PR. Commit the unchanged
activated 006-b order and `oap/active` with the implementation. Push, run and
inspect final checks, and repair safe in-scope defects on the same branch.
Never create a replacement PR or merge.

## Required report

Atomically publish exactly:

```text
oap/reports/006-b-empty-content-schema-safe-state.md
```

Use protocol 1.2 in full. Include the prior partial finding, strategic
resolution, exact state schema/constraints/transitions, empty/non-empty
privilege evidence, tests/matrices/checks/alerts, dependency and scope
confirmation, PR identity, immutable 006-a evidence, limitations, and the
literal implementation head plus `Report publication commit: SELF`. The final
report-only commit must change only that report and be the verified remote PR
head before FIFO `OK`.

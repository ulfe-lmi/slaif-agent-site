# OAP Work Order — 010-i

## Objective

Close the entire bounded human-session foundation on PR `#15` in this round.
Qualify the known ambiguous touch-update columns, audit the complete session
migration/runtime/test slice for the same defect class and any remaining
directly related failure, and continue correcting that slice until the complete
local lifecycle/session suite and all 20 GitHub checks are green. Add no new
behavior or adjacent feature.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-i`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `d02d3218ce8cf7132233a22150dbeeda3c119f20`
- `010-h` implementation head:
  `27bf6378af12b906c85aff383614e1f03cc46882`
- Required PR title:
  `[OAP 010] Establish secure installation and local authentication`

No new PR, rebase, force-push, merge, close, auto-merge, or unrelated action.

## Verified root cause and allowed scope

GitHub PostgreSQL job `96523977631` records:

```text
column reference "absolute_expires_at" is ambiguous
PL/pgSQL function control.slaif_finalize_human_session(...) line 44
```

The touch `UPDATE control.user_session` uses unqualified `revoked_at` and
`absolute_expires_at`, while the `RETURNS TABLE` contract creates PL/pgSQL
output variables with overlapping names. Apply an explicit target-table alias
and qualify every update predicate/assignment reference in both safe and
state-changing finalizers. Inspect the adjacent revoke function for the same
class, but change it only if an actual overlapping identifier exists.

Manual changes remain limited to the bounded session/verification slice:

```text
services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/tests/integration/test_human_session.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/unit/test_sessions.py
.github/workflows/ci.yml
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
docs/LOCAL_AUTHENTICATION.md
docs/DATABASE_ROLES.md
docs/OPERATIONS.md
oap/active
oap/orders/010-i-qualify-session-finalizer-update.md
oap/reports/010-i-qualify-session-finalizer-update.md
```

Use only paths actually required by an observed session/lifecycle/CI defect.
Do not edit dependencies, lockfiles, routes, middleware, UI, another migration,
or any adjacent product feature.

## Closure budget and retry discipline

- Target: 30 minutes; hard stop: 60 minutes.
- Do not repeat an unchanged failing command. Every retry must follow a concrete
  diagnosis and an in-scope code/test correction.
- Do not stop merely because a correctable session-slice defect appears. Audit,
  fix, and rerun the focused lifecycle/session evidence until it passes or the
  hard stop/genuine external boundary is reached.
- Push only after the complete focused local evidence is green.
- One initial GitHub implementation generation is expected. If that generation
  alone exposes a PostgreSQL-version/clean-environment defect not reproducible
  locally, one in-scope corrective commit/generation is allowed; never click or
  invoke workflow rerun.
- Local Compose is required only if Compose/session-readiness paths change or
  CI identifies a Compose regression. No broad supply-chain/image, Node, or
  browser work.

## Requirements and acceptance

1. Alias the `user_session` touch target and qualify `last_seen_at`, `id`,
   `revoked_at`, and `absolute_expires_at` references so no PL/pgSQL output
   variable can shadow a column in either finalizer.
2. Before the first DB run, inspect every statement in all five session
   functions for output-variable/parameter/column ambiguity, create/drop
   asymmetry, invalid return shape, and unqualified mutation predicates. Fix
   every occurrence of the same defect class in this migration at once.
3. Preserve inspect → application `compare_digest` → finalizer/revoke order,
   row locks, state/digest/active-user/expiry rechecks, touch throttling,
   immutable recent-auth, CSRF split, role grants, and downgrade symmetry.
4. Extend static/package regression to prove the qualified update contract and
   reject the ambiguous unqualified predicate form in both finalizers.
5. Fresh migration rebuild/privilege lifecycle and complete
   `test_human_session.py` must pass locally after the fix, reaching every
   negative/expiry/recent-auth/touch/race/cancellation/role assertion.
6. Treat a failing focused assertion or fixture as unfinished work, not an
   automatic `PARTIAL` result. Correct it when it tests the ordered contract;
   never weaken constraints, remove assertions, skip cases, or mask errors.
7. The already-wired PostgreSQL 14–18 jobs must each run and pass bootstrap plus
   session tests; Compose and every other required check must also pass.
8. No adjacent feature, dependency, fixture weakening, timeout increase,
   skipped check, or scope drift.
9. Exactly PR #15 is amended; report-head total is 20 successful, zero
   failed/cancelled/skipped/pending, no workflow rerun; report-only `SELF` is
   correct.

## Verification required

Prepare the full migration audit, SQL qualifications, and static assertions
first. Run affected Ruff/format/mypy/compile/static/unit/repository checks and
complete disposable-PostgreSQL bootstrap lifecycle plus
`test_human_session.py`. Diagnose and correct any in-scope failure, then rerun
the focused evidence until it passes. Record every materially distinct attempt
and correction. Run exact path/prior hashes, no conflict markers, secret/log
scan, and `git diff --check`.

Do not run a full local DB matrix, supply-chain/image, Node, browser, or
generated-tree Markdown. GitHub runs the complete 20-check gate; no workflow
rerun. A corrective code push is allowed only under the closure rule above.

## Safety, workflow, and report

Use fake data/disposable PostgreSQL only and expose no secret, digest,
password/hash, cookie, DSN, raw driver error, or private URL. Preserve all
governance, architecture, OAP, setup/identity/session, and role boundaries.

Amend only the existing branch with one implementation commit. Atomically
publish exactly:

```text
oap/reports/010-i-qualify-session-finalizer-update.md
```

The report-only `SELF` commit must parent the literal implementation head.
Report the complete audit, exact SQL/static/runtime/test changes, every
materially distinct local/CI failure and correction, successful complete local
session/lifecycle results, all five matrix jobs and 20 report-head checks,
path/hash/skip evidence, no-workflow-rerun/no-new-PR/no-merge state, and
`Report publication commit: SELF`.

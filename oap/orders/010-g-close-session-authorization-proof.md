# OAP Work Order — 010-g

## Objective

Amend PR `#15` to close the remaining human-session authorization and evidence
defects: put application constant-time comparison before any authenticated
touch/mutation, repair the unreachable/invalid integration fixtures, run that
session test in every PostgreSQL CI job, and repair Compose recovery to the
current `010_001` migration head.

This remains a session-foundation repair. Do not add HTTP routes, middleware,
UI, login lookup/rate limiting, OIDC, sites, memberships, capabilities,
publication, dependencies, or another product feature.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-g`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Current remote `main`: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `3818eb071151177d4c8a1e2e8130c3b459916e84`
- `010-f` implementation head:
  `238ccf060d7c863c4e55859a1b7b1dc8be23e8cc`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` remains the unique objective PR. No new PR, rebase, force-push,
merge, close, auto-merge, or unrelated PR action.

## Strategic findings

1. GitHub PostgreSQL jobs run only `test_database_bootstrap.py`; they do not
   run new `test_human_session.py`. Their green state proves inventories, not
   the session lifecycle assertions claimed by the report.
2. In `test_human_session.py`, the owner update intended to age
   `recent_auth_at` is indented after an awaited call that must raise inside
   `pytest.raises`; it is unreachable. The following false-recent-auth
   assertion therefore is not valid proof.
3. The absolute-expiry fixture can violate `user_session_time_order` by moving
   `absolute_expires_at` before a newer `last_seen_at`; it must create a valid
   expired row rather than weaken the constraint.
4. The database authenticate/resolve functions filter by presented digest and
   can update `last_seen_at` before Python receives the stored digest. Thus
   `secrets.compare_digest` is not the primary comparison for wrong secrets and
   occurs after authenticated state mutation for valid secrets. An unused or
   post-filter comparison is insufficient.
5. Compose readiness recovery hard-codes marker `009_001` after deliberately
   injecting a mismatch. The current application head is `010_001`, so the
   fixture times out waiting for readiness.

## Hard execution budget

- Target duration: 40 minutes; hard stop at 65 minutes.
- Complete post-fix focused session PostgreSQL invocations: 2 maximum.
- Targeted local Compose readiness smoke: 1 maximum.
- Implementation commits/check generations: 1 maximum before report.
- Workflow reruns: 0.
- No broad supply-chain/image, Node, browser, or full local DB matrix.

Prepare the complete fix and static review before consuming the attempts. On a
failure, diagnose once within scope; do not repeatedly rerun unchanged work.

## Allowed scope

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
migrations/alembic/README.md
oap/active
oap/orders/010-g-close-session-authorization-proof.md
oap/reports/010-g-close-session-authorization-proof.md
```

Use the minimum subset. No other migration, dependency, lockfile, API route,
web, edge configuration, or product path may change.

## Requirements

### 1. Correct transaction order for constant-time authorization

Within one Control transaction and one row-lock boundary, use this semantic
order for every syntactically valid session public ID:

```text
lock/inspect candidate by public ID only without touch/revoke/authority
return fixed-size stored defense digests to Control application code
run secrets.compare_digest for presented session digest
run secrets.compare_digest for CSRF digest when state-changing/revoke
only after successful application comparisons, call a narrow finalize/revoke
function that rechecks digests, active user, revocation, expiry, and row identity
then touch or revoke and return minimal context
commit transaction
```

For a syntactically valid unknown public ID, execute a comparison against a
fixed dummy 32-byte digest before returning the same constant error, so the
application path does not skip its constant-time primitive. Malformed token
shape may fail before DB access.

The inspect function must not touch `last_seen_at`, refresh recent-auth,
revoke, or return authority. The finalize function must not be callable by an
untrusted route directly; it remains Control-only and rechecks every database
condition under the still-held lock. Safe finalization checks session only;
state-changing finalization and revoke check both session and CSRF. Public
Python methods remain unambiguous: safe authenticate, state-changing
authenticate, CSRF-bound revoke.

Preserve owner/fixed `pg_catalog` search path/full qualification/`PUBLIC`
revoke/exact `slaif_control` execute grants and direct-table denial. Update
strict function inventories and downgrade order. Do not weaken constraints or
expose plaintext/stored digests outside the Control service boundary.

### 2. Repair and complete the focused integration test

Move the recent-auth aging update out of the `pytest.raises` block and make all
fixture timestamps satisfy `user_session_time_order`. Avoid arbitrary sleeps
except the bounded cancellation scheduling point.

The focused test must actually reach and pass all `010-f` required assertions:
safe authentication; state-changing+CSRF; malformed/unknown/wrong session;
wrong/cross-session CSRF; unchanged state after denial; disabled/revoked/idle/
absolute expiry; recent-auth true→false; touch throttle/advance without
overextension or recent-auth refresh; wrong-CSRF no revoke; idempotent correct
revoke; concurrent resolve/touch/revoke terminal state; cancellation rollback;
role/table/function denials; no secret leakage.

Add unit spies proving call order: inspect → constant-time compare(s) →
finalize/revoke, and proving finalize/mutation is never called after a failed
comparison or unknown candidate.

### 3. Put session proof in the PostgreSQL matrix

Update each PostgreSQL 14–18 job's Agent-Site integration command to run both
the strict bootstrap/privilege test and `test_human_session.py`. Do not replace
or skip existing foundation/bootstrap tests. Keep one job/generation per
supported PostgreSQL version; no duplicate matrix or workflow rerun.

### 4. Repair Compose readiness recovery

The migration-mismatch fixture must restore
`control.bootstrap_readiness.migration_revision` to the actual current head
`010_001` before waiting for readiness. Keep the deliberate mismatch at
`006_001`, exact failure reason, liveness/NGINX denial, recovery, and all other
negative stages. Prefer one explicit tested current-head constant or safe
package-derived value consistent with existing fixture style; do not bypass
the readiness check or increase timeout to hide failure.

### 5. Preserve scope and documentation honesty

Update only the transaction-order/session-proof wording needed. Continue to
state that HTTP/session-cookie emission, middleware, setup/login/logout routes,
UI, OIDC, MFA, security-event persistence, sites, memberships, capabilities,
and publication do not exist yet.

## Observable acceptance criteria

1. Wrong/unknown credentials reach application constant-time comparison but
   never finalize, touch, revoke, or return authority; valid credentials are
   compared before final DB mutation and rechecked under the same lock.
2. The full focused session integration test passes locally after all fixture
   repairs and on PostgreSQL 14, 15, 16, 17, and 18 in CI.
3. Tests explicitly prove every negative/expiry/recent-auth/touch/race/
   cancellation/role case rather than relying on source presence.
4. Compose migration-mismatch stage fails for the deliberate mismatch and
   recovers at `010_001` without timeout or weakened checks.
5. All strict relation/function/grant/migration inventories pass; no accepted
   prior behavior or security boundary regresses.
6. No adjacent feature/dependency/scope enters.
7. Exactly PR #15 is amended; all 20 report-head checks pass with no rerun;
   report-only `SELF` publication is correct.

## Verification required

Run focused unit/static tests, then at most two complete post-fix invocations of
`test_human_session.py` against disposable PostgreSQL. Run the strict database
bootstrap/privilege test in the same bounded environment and one targeted
Compose readiness smoke. Also run affected Ruff/format/mypy/compile,
repository/packaging policy tests, secret/log/repr scans, explicit changed-doc
Markdownlint with `--no-globs`, exact paths/prior hashes, no conflict markers,
and `git diff --check`.

Do not run broad supply-chain/image, Node, browser, or full local PostgreSQL
matrix. GitHub must run the updated complete 20-check gate exactly once across
PostgreSQL 14–18. No rerun.

## Safety and report

Use fake generated secrets and disposable services only; never print token,
digest, password/hash, cookie, DSN, private URL, or raw driver error. Preserve
governance, architectures, OAP history, setup/identity/Argon2, and role
separation.

Amend only the existing branch with one implementation commit; never create,
merge, close, or auto-merge a PR. Atomically publish exactly:

```text
oap/reports/010-g-close-session-authorization-proof.md
```

The report-only `SELF` commit must parent the literal implementation head.
Report function/grant/call-order changes; every local/matrix/Compose case and
attempt; all current-head checks; paths/hashes/skips; no-rerun/no-new-PR/
no-merge state; and `Report publication commit: SELF`.

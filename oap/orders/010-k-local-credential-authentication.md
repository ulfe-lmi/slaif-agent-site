# OAP Work Order — 010-k

## Objective

Amend PR `#15` with the bounded local-credential authentication service that
future login HTTP handlers will call: Control-only local identity lookup,
Argon2 verification with an equal-cost dummy path, stable non-enumerating
failure, safe compare-and-set password rehash, and complete PostgreSQL tests.

Do not create sessions from credentials yet and do not add HTTP routes,
cookies, middleware, UI, OIDC, MFA, login audit persistence, sites,
memberships, capabilities, publication, or another feature.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-k`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `c534cdec5ef44add7cf2b0f35e54eba7b1459e71`
- Required PR title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective PR. No new PR, rebase, force-push, merge,
close, auto-merge, or unrelated action.

## Current state and strategic boundary

Local identity/password persistence and first-administrator creation are proven
through revision `009_001`; server-side sessions/CSRF are proven through
`010_001`. `PasswordService` uses fixed RFC 9106 LOW_MEMORY Argon2id and exposes
`verify_password` plus `check_needs_rehash`. No online or semantic login lookup
exists. Control has no direct identity-table SELECT/UPDATE grant.

This round creates the narrow semantic credential boundary only. It may return
a trusted active local user identity to future internal login orchestration;
it must never return password hash/token material to an HTTP response or log.

## Moderate autonomy and completion rule

- Target: 40 minutes; hard stop: 65 minutes.
- Audit the complete credential migration/service/test slice before DB runs.
- Diagnose and fix any in-scope failure until focused local evidence is green;
  no arbitrary attempt cap and no unchanged blind reruns.
- Push only after complete focused evidence passes.
- One initial CI generation; one corrective code generation allowed only for
  an in-scope clean-environment/version defect; never workflow-rerun.
- No broad local supply-chain/image, Node, browser, or full DB matrix.

## Allowed scope

```text
services/backend/src/slaif_agent_site/db/alembic/versions/011_001_local_authentication.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/src/slaif_agent_site/identity/models.py
services/backend/src/slaif_agent_site/identity/passwords.py
services/backend/src/slaif_agent_site/identity/authentication.py
services/backend/src/slaif_agent_site/identity/__init__.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/tests/unit/test_identity_authentication.py
services/backend/tests/unit/test_identity_password.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/integration/test_local_authentication.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_control_database_integration.py
.github/workflows/ci.yml
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
tools/check_repository.py
tests/repository/test_repository_policy.py
migrations/alembic/README.md
docs/LOCAL_AUTHENTICATION.md
docs/DATABASE_ROLES.md
docs/CONFIGURATION.md
docs/OPERATIONS.md
oap/active
oap/orders/010-k-local-credential-authentication.md
oap/reports/010-k-local-credential-authentication.md
```

Use the minimum subset. Equivalent focused module/test names are acceptable.
No dependency, lockfile, web/Next.js, route, edge configuration, Compose file,
or unrelated migration path may change.

## Requirements

### 1. Forward migration and least-privilege functions

Add deterministic revision `011_001` after `010_001`; never rewrite accepted
migrations. Create only narrow owner-controlled functions needed to:

- look up one normalized local login candidate and return minimal internal
  `user_account_id`, encoded Argon2 hash, and status to `slaif_control`;
- compare-and-set a newly produced current-profile hash only when the account is
  active/local and its existing hash exactly matches the expected old hash.

Use fixed `pg_catalog` search path, fully qualified objects, owner
`slaif_owner`, `PUBLIC` revoke, exact `slaif_control` execute, no direct table
grant, strict input/hash-shape checks, deterministic downgrade symmetry, and
stable no-row/false behavior. No password plaintext reaches PostgreSQL.

Update exact object/grant/relation inventories. Ensure the Compose readiness
fixture restores the actual packaged migration head without another fragile
hard-coded old revision; use one tested source of truth consistent with its
runtime boundary rather than incrementing a literal every future migration.

### 2. Secret-safe input/result and authentication service

Add frozen typed local-login input with bounded username and masked/excluded
`SecretStr` password. The external-safe error must be one constant message for
unknown, wrong-password, disabled, non-local, malformed internal result,
database error, and failed rehash race. Result exposes only trusted user ID,
normalized username, and whether a rehash was performed; never hash/plaintext.

For every syntactically valid login attempt:

```text
controlled candidate lookup
actual Argon2 verify for an active LOCAL candidate
same production-profile Argon2 verify against a valid fixed dummy hash when
  candidate is absent/inactive/invalid
constant external failure for every denial
on valid password, check_needs_rehash
if needed, hash with current profile and compare-and-set old→new
return trusted internal identity only after successful CAS or no rehash needed
```

The dummy encoded hash is non-secret but must be a valid current-profile
Argon2id value, immutable, source-reviewed, never generated per request, and
not configurable to a cheaper profile. Unknown and disabled users must execute
the password verifier; tests use spies rather than timing claims. Do not claim
perfect network timing equality.

Do not validate a login password using the new-account password policy; an
existing valid account remains login-capable even if policy later changes.
Only Argon2 verify decides credential correctness. Catch library mismatch/
malformed-hash errors safely without leaking candidate state.

### 3. Transaction, concurrency, cancellation, and rehash

Credential lookup and optional CAS rehash use Control authority only. Avoid
holding a DB transaction during the memory-hard Argon2 operation. CAS must
recheck user ID, local identity, active status, and expected old hash so a
concurrent password/status change cannot be overwritten. A CAS miss fails the
login rather than returning authority.

Prove correct password/no-rehash, correct password/rehash, wrong password,
unknown username, disabled user, OIDC row, malformed stored hash, concurrent
rehash/password change, database failure, and cancellation. Failed paths make
no identity/session mutation. No session is issued in this round.

### 4. CI and documentation

Add focused local-auth integration to every PostgreSQL 14–18 Agent-Site job
without removing bootstrap/session/foundation coverage. Preserve exactly 20
checks. Update docs for implemented credential lookup/verification/rehash,
Argon2 cost and enumeration limitations, and deliberate absence of session
issuance/HTTP/rate limiting/audit/UI/OIDC/MFA.

## Observable acceptance criteria

1. Control is the only runtime role able to execute lookup/CAS; no service role
   can read/update identity/password tables directly.
2. Actual and dummy Argon2 paths are executable and proven; all denials share
   one external result and expose no existence/status/hash detail.
3. Correct credentials return minimal trusted identity; safe CAS rehash cannot
   overwrite concurrent password/status changes and no plaintext enters DB.
4. Every negative/concurrency/cancellation/database case leaves identity and
   session state unchanged.
5. Fresh migration rebuild and focused auth/session/bootstrap tests pass
   locally and on PostgreSQL 14–18; Compose recovers at packaged head.
6. No HTTP/session issuance/rate-limit/audit/UI/adjacent feature enters.
7. Exactly PR #15 is amended; report head is 20/20 green, no workflow rerun,
   and report-only `SELF` parentage is correct.

## Verification required

Run affected unit/static/policy checks and complete disposable-PostgreSQL
bootstrap/session/local-auth integration. Diagnose/fix in-scope failures until
green. Run affected Ruff/format/mypy/compile, strict create/drop/grant inventory,
secret/repr/log scan, explicit changed-doc Markdownlint with `--no-globs`, exact
paths/prior hashes, no conflict markers, and `git diff --check`.

Do not run broad supply-chain/image, Node, browser, or full local DB matrix.
Run local Compose readiness only if its packaged-head change requires proof.
GitHub runs the full updated matrix and all 20 checks. Before report
publication, lint the exact complete report content per protocol.

## Safety, workflow, and report

Fake passwords/users and disposable PostgreSQL only; no production credential,
system, token, cookie, DSN, hash, or raw driver error in output. Preserve all
architecture/governance/OAP/setup/session/role boundaries.

Amend only the existing PR branch. Atomically publish exactly:

```text
oap/reports/010-k-local-credential-authentication.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report function/grant/service contracts; dummy/actual/rehash proof;
negative/concurrency/cancellation cases; local and five-version CI results;
attempts/corrections/paths/hashes/skips; no-rerun/no-new-PR/no-merge state; and
`Report publication commit: SELF`.

# OAP Work Order — 010-l

## Objective

Amend PR `#15` to close every known local-credential proof regression before
HTTP work: reconcile the existing local-identity integration with forward
session/auth migrations, exclude login password input from serialization/repr,
add the missing disabled/OIDC/malformed-result/rehash-CAS/race/database/
cancellation proofs, and run all identity/session/auth integration in the
PostgreSQL 14–18 matrix.

Do not add HTTP routes, session issuance from credentials, cookies, middleware,
rate limiting, audit persistence, UI, OIDC flow, MFA, or another feature.

## GitHub objective state

- Numeric objective/round: `010` / `010-l`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `48ca419c7b28fdd705e4f4ad40de61cbcbc6ab7f`
- `010-k` implementation head:
  `fb19554bc91fdab2966750cfce5ba7f6a1582b6e`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

No new PR, rebase, force-push, merge, close, auto-merge, or unrelated action.

## Strategic findings

1. The ordered local command found `test_local_identity.py` failing because its
   whole-control-schema relation/function inventory still assumes revision
   `009_001`; the PR itself added later relations/functions. This is not
   out-of-scope or pre-existing—it is a regression caused by this PR.
2. GitHub PostgreSQL jobs run bootstrap, session, and new local-auth tests but
   omit `test_local_identity.py`, so green CI does not cover that regression.
3. `LocalLoginRequest.password` is `SecretStr` but lacks the explicit
   `Field(exclude=True, repr=False)` contract already used for setup inputs.
4. Unit coverage contains only unknown-dummy and valid-no-rehash cases.
   Integration covers valid, wrong, unknown, and function denial. There is no
   executable disabled user, OIDC row, malformed internal candidate, actual
   rehash/CAS success, CAS miss/concurrent change, database failure, or
   cancellation evidence claimed by the report.
5. The prior round used two corrective CI generations after the initial one,
   exceeding its one-correction allowance, while still pushing with a known
   local failure. This round must complete local evidence before its first push.

## Moderate autonomy and completion rule

- Target: 35 minutes; hard stop: 60 minutes.
- No arbitrary local attempt cap. Diagnose and correct in-scope failures until
  all focused local evidence passes; never repeat an unchanged command.
- A failure in any test affected by this PR cannot be labeled out-of-scope.
- Do not push while any required local identity/session/auth/bootstrap test is
  known failing.
- One initial CI generation; one corrective code generation only for a genuine
  clean-environment/version-only defect; never workflow-rerun.
- No broad local supply-chain/image, Node, browser, or full DB matrix.

## Allowed scope

```text
services/backend/src/slaif_agent_site/identity/authentication.py
services/backend/src/slaif_agent_site/identity/passwords.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/tests/unit/test_identity_authentication.py
services/backend/tests/unit/test_identity_password.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/integration/test_local_authentication.py
services/backend/tests/integration/test_local_identity.py
services/backend/tests/integration/test_control_database_integration.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_human_session.py
.github/workflows/ci.yml
docs/LOCAL_AUTHENTICATION.md
oap/active
oap/orders/010-l-close-credential-proof-regressions.md
oap/reports/010-l-close-credential-proof-regressions.md
```

Use the minimum subset. Do not edit migrations, grants, dependencies, lockfiles,
Compose, web/edge, or adjacent product paths unless a failing executable proof
shows a direct defect in the already-added `011_001` contract; report before
broadening beyond this list.

## Requirements

### 1. Reconcile the historical identity test correctly

Preserve strict proof of the `009_001` objects without assuming no later
forward migration exists. Scope identity-specific catalog queries to the exact
two identity functions/tables they own, or explicitly assert the full current
inventory consistently with the global bootstrap inventory. Do not weaken to a
vague subset, remove grants/denials, or skip the test. The global strict object
inventory remains owned by bootstrap/privilege tests.

Add `test_local_identity.py` to every PostgreSQL 14–18 Agent-Site job alongside
bootstrap, session, and local authentication. Preserve the foundation gate and
exactly 20 check names.

### 2. Secret-safe request contract

Declare `LocalLoginRequest.password` with explicit serialization exclusion and
repr suppression. Prove model dump/JSON/repr/errors never contain plaintext,
password hash, or even a serialized password field. Preserve `SecretStr` and
bounded normalized username behavior.

### 3. Complete actual/dummy/denial unit evidence

Use deterministic spies/fakes to prove:

- valid ACTIVE LOCAL candidate uses its actual encoded hash exactly once;
- unknown, DISABLED, OIDC/non-local, malformed hash, malformed row/status, and
  lookup/database failure use the fixed current-cost dummy verifier where the
  service can safely do so and always return the one constant failure;
- wrong password fails without CAS;
- cancellation propagates without a second verifier/CAS/mutation;
- `check_needs_rehash=false` returns minimal identity;
- `check_needs_rehash=true` hashes only after successful verify and invokes CAS
  with exact user/old/new values;
- successful CAS reports `rehashed=true`; CAS false/exception/concurrent change
  returns constant failure and never returns authority; and
- hash/rehash library failures expose no candidate/password/hash detail.

Do not assert network-level timing equality. Assert actual control flow and
equal-cost dummy profile.

### 4. Complete disposable-PostgreSQL evidence

Extend focused integration to prove actual success, wrong/unknown, disabled
LOCAL, OIDC identity, Control-only function access, safe CAS update and stale-
expected-hash refusal, and no session rows created by credential verification.
Use injectable test-owned hasher/service only when needed to force a rehash
decision while still producing schema-valid current-profile hashes; do not
weaken production hash constraints.

Run together on a fresh database:

```text
test_database_bootstrap.py
test_local_identity.py
test_human_session.py
test_local_authentication.py
test_control_database_integration.py
```

Every test must pass locally before push and in each PostgreSQL CI job.

### 5. Preserve scope and claims

Keep docs explicit that credential authentication does not issue a session and
that HTTP/rate-limit/audit/OIDC/MFA/UI remain unimplemented. Preserve all
setup/session/constant-time/role/migration behavior and no plaintext DB input.

## Observable acceptance criteria

1. All five focused integration files pass together locally and on PostgreSQL
   14–18; no known PR-caused test failure remains omitted from CI.
2. Login password is absent from repr and serialization, not merely masked.
3. Actual/dummy/disabled/OIDC/malformed/database/cancellation/rehash/CAS-race
   branches have executable evidence matching one constant external failure.
4. Rehash CAS cannot overwrite concurrent password/status changes and no
   credential verification creates a session.
5. No existing assertion, constraint, grant, test, or architecture boundary is
   weakened to obtain green.
6. No HTTP/adjacent feature or dependency enters.
7. Exactly PR #15 is amended; report head is 20/20 green, no workflow rerun,
   report-only `SELF` is correct.

## Verification required

Run complete affected unit tests, then the five-file disposable-PostgreSQL set
above until green after concrete fixes. Run Ruff/format/mypy/compile,
repository/packaging policy, explicit changed-doc Markdownlint `--no-globs`,
secret/repr/log scan, exact paths/prior hashes, no conflict markers, and
`git diff --check`. Do not run broad supply-chain/image, Node, browser, or full
local version matrix. GitHub runs the full updated matrix and 20 checks.

Lint the exact completed report before publication per protocol.

## Safety, workflow, and report

Fake users/passwords and disposable PostgreSQL only; expose no plaintext/hash/
session/cookie/DSN/raw driver error/private URL. Preserve governance,
architecture, OAP history, roles, setup, session, and migration contracts.

Amend only the existing PR. Atomically publish exactly:

```text
oap/reports/010-l-close-credential-proof-regressions.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report the identity-test reconciliation, every actual/dummy/rehash/race/
failure proof, complete five-file local and five-version CI results, all
material corrections, paths/hashes/skips, no-workflow-rerun/no-new-PR/no-merge
state, and `Report publication commit: SELF`.

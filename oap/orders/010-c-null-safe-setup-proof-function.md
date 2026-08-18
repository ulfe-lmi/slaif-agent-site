# OAP Work Order — 010-c

## Objective

Amend PR `#15` to close the database-side NULL bypass in the initial setup
completion function. Make generation and digest proof comparisons null-safe,
add direct-function regressions, and preserve every accepted 010-a/010-b
boundary.

This is a security repair only. Do not begin sessions, routes, UI, or other
planned objective work.

## Revised planned objective rounds

```text
010-a  accepted: installation state + token issuance
010-b  reviewed: identity/Argon2 + atomic consumer; security repair required
010-c  active: null-safe setup-proof function and regression evidence
010-d  planned: server-side sessions + cookies + CSRF + expiry + recent-auth
010-e  planned: setup/login/logout HTTP/UI/Compose/NGINX/E2E + closure
```

All rounds amend the same PR. No merge is authorized in 010-c.

## Hard execution budget

- Target duration: 20 minutes; hard stop at 30 minutes.
- Focused PostgreSQL integration invocations: 1 maximum.
- Implementation commits/check generations: 1 maximum.
- GitHub workflow reruns: 0.
- Local broad supply-chain/image/Compose/matrix/Node/browser runs: 0.

If the single focused run or one GitHub generation fails, publish `PARTIAL`
with exact evidence and stop. Do not make a second fix/run/generation.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-c`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Current remote/report head:
  `f1abade214bbb10c951d9e089ff63e23f574b5cf`
- 010-b implementation head:
  `85a21636a97f33a5c3c5816fc7939c08250db49c`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` remains the unique objective PR. Preserve 010-a/010-b orders and
reports exactly. Do not create a new PR, force-push, merge, close, enable
auto-merge, or act on PR `#12`/`#13`.

## Strategic finding

The completion function currently contains:

```sql
installation.setup_token_generation <> p_expected_generation
OR installation.setup_token_digest <> p_presented_digest
```

PostgreSQL comparisons with `NULL` return SQL `NULL`, not `TRUE`. In a PL/pgSQL
`IF`, a condition that is `NULL` does not enter the failure branch. A caller
with execute authority could therefore pass the current generation and a NULL
digest (or analogous nullable proof) and bypass the function's independent
token guard, even though the typed application never sends NULL.

This violates 010-b's requirement that a compromised/buggy Control caller
cannot invoke completion without matching current proof. Green CI did not
cover direct NULL arguments, so the slice is not strategically accepted.

## Allowed scope

Change only:

```text
services/backend/src/slaif_agent_site/db/alembic/versions/009_001_local_identity.py
services/backend/tests/integration/test_local_identity.py
services/backend/tests/unit/test_foundation_contract.py   # only if exact packaged migration text is asserted
docs/LOCAL_AUTHENTICATION.md                              # only if clarification is necessary
docs/INSTALLATION_SETUP.md                               # only if clarification is necessary
oap/active
oap/orders/010-c-null-safe-setup-proof-function.md
oap/reports/010-c-null-safe-setup-proof-function.md
```

No other path may change.

## Requirements

1. Keep the same migration revision/signature/object inventory because the
   migration is unmerged. Change only the completion function's proof guard.
2. Reject `NULL` expected generation, `NULL` presented digest, and a presented
   digest not exactly 32 bytes before any insert/update.
3. Compare generation and digest with explicit null-safe semantics, preferably
   `IS DISTINCT FROM`, while retaining stored-token presence, expiry, and
   initialized-state checks.
4. Retain the application's `secrets.compare_digest` check as the primary
   constant-time comparison. Database equality remains defense-in-depth and a
   race/invariant guard.
5. Preserve the same constant database/application failure, transaction,
   row-lock, ownership, fixed search path, `PUBLIC` revoke, and exact
   `slaif_control` execute grant.
6. Do not add dynamic SQL, another function, relation, grant, dependency, or
   input parameter.

## Direct-function regression evidence

Using the disposable PostgreSQL fixture and the actual `slaif_control` role,
call `control.slaif_complete_initial_local_administrator` directly after a
valid setup token has been issued. Prove each of these independently fails
before mutation:

- NULL expected generation with the correct digest;
- current generation with NULL digest;
- current generation with a 31-byte digest;
- current generation with a 33-byte digest;
- current generation with a wrong 32-byte digest;
- stale generation with the correct digest.

After every failure, prove:

```text
user_account count = 0
platform_administrator count = 0
initialized_at remains NULL
original setup digest/issued/expiry/generation remain unchanged
```

Then prove the ordinary typed adapter path with the valid token still creates
one administrator and clears setup material atomically. Preserve existing
replay/concurrency/rollback/cancellation tests.

Also add a source/static assertion that the packaged function guard contains
null-safe comparison and explicit proof-length/non-null checks so a future
test double cannot hide regression.

## Acceptance criteria

1. PR `#15` is amended once on its existing branch; no extra PR, force push,
   merge, close, auto-merge, or unrelated action occurs.
2. The completion function rejects NULL/malformed/wrong/stale proof with
   null-safe semantics before mutation and retains exact ownership/grants.
3. Direct calls as `slaif_control` prove every adversarial case leaves all
   identity/admin/installation/token state unchanged.
4. The valid typed path remains green, including application-side
   constant-time comparison and atomic success.
5. No other migration object, product source, dependency, docs contract, role,
   session, route, UI, Compose, or planned feature changes.
6. All 20 GitHub checks pass with zero open CodeQL alerts and immutable report
   publication follows protocol 1.2.

## Verification required

Run the directly affected migration/static test and exactly one invocation of
the focused local-identity PostgreSQL integration set, plus affected
Ruff/format/mypy/compile, migration/package/repository checks,
`git diff --check`, and exact allowed-path/prior-artifact checks.

Do not run locally full supply-chain/image/Compose smoke, full Python or
PostgreSQL matrices, Node, or Playwright. GitHub runs the unchanged complete
gate once. No rerun is authorized.

## Documentation required

No documentation change is expected because intended behavior does not
change. If a clarification is essential, keep it to the null-safe database
defense-in-depth statement and do not expand scope or readiness claims.

## Safety constraints

Use only generated fake tokens/password hashes and disposable PostgreSQL.
Never print proof material or database errors. Do not weaken application
constant-time comparison, Argon2, transactionality, token expiry, grants,
negative tests, or other architecture boundaries.

## GitHub workflow

Fetch/verify PR `#15`, amend only its existing branch with one implementation
commit, commit this order and `oap/active` unchanged, and never create or merge
a PR. Publish the report as the final report-only `SELF` commit.

## Required report

Atomically publish exactly:

```text
oap/reports/010-c-null-safe-setup-proof-function.md
```

Use protocol 1.2 in full. Include the exact SQL correction, every direct NULL/
length/wrong/stale case and unchanged-state proof, valid typed success,
single-attempt/generation timing, checks/alerts, path/prior-artifact integrity,
later-round exclusions, literal implementation head, and
`Report publication commit: SELF`.

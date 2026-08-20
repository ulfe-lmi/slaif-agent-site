# OAP Work Order — 010-f

## Objective

Amend PR `#15` to repair and prove the `010-e` human-session foundation. Fix
the CI relation inventory, make constant-time application digest comparison
part of the real authorization path, separate ordinary session authentication
from CSRF enforcement for state-changing requests, and complete the missing
expiry/substitution/concurrency/cancellation evidence.

This is a same-feature repair only. Do not add HTTP routes, middleware, UI,
Compose/NGINX wiring, login lookup/rate limiting, OIDC, sites, memberships,
capabilities, publication, or another product feature.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-f`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Current remote `main`: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `ac246252d7bdc2c09af299732cfd045befa2d305`
- `010-e` implementation head:
  `1d74623e069515bb9a8574ed0bf58d64a77fb9c2`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` remains the unique objective PR. Do not create another PR, rebase,
force-push, merge, close, or enable auto-merge.

## Strategic findings

The `010-e` report correctly declared `PARTIAL`: both permitted focused
PostgreSQL invocations failed before the resolver ambiguity correction, so the
current correction has no successful local integration proof. GitHub CI run
`32394634119` independently confirms PostgreSQL 14–18 fail in the database
bootstrap/privilege gate, and Compose packaging fails downstream, because the
pre-existing exact relation inventory omits `control.user_session`.

Independent code review found additional acceptance gaps:

1. `constant_time_digest_equal` exists and has a unit test but the actual
   `HumanSessionService.resolve`/revoke authorization path never calls it;
   authorization relies only on SQL bytea equality.
2. `resolve(token, csrf_token)` requires CSRF for every session resolution.
   The architecture requires CSRF for state-changing cookie-authenticated
   Control requests, not safe reads. Future HTTP code needs an explicit safe
   authentication path and an explicit state-changing authentication+CSRF path.
3. Revoke currently accepts only the session token. Future logout is a
   state-changing cookie-authenticated action and must require the bound CSRF
   proof without leaking whether a session exists.
4. The integration test does not yet prove wrong/unknown session secrets,
   cross-session CSRF substitution, disabled-user denial, idle expiry,
   absolute expiry, recent-auth expiry, touch throttling, revoke/touch race,
   cancellation rollback, or no revival/no overextension.

## Hard execution budget

- Target duration: 35 minutes; hard stop at 60 minutes.
- Focused PostgreSQL integration invocations after the complete repair: 2 max.
- Implementation commits/check generations: 1 maximum before report.
- GitHub workflow reruns: 0.
- Broad local Compose, supply-chain/image, Node, browser, or full matrix: 0.

Prepare the complete repair before consuming the focused DB attempts. If the
bounded attempts or single new CI generation fail, publish `PARTIAL` and stop;
do not repeat unchanged runs.

## Allowed scope

```text
services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py
services/backend/src/slaif_agent_site/identity/sessions.py
services/backend/src/slaif_agent_site/identity/__init__.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/tests/integration/test_human_session.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_control_database_integration.py
services/backend/tests/unit/test_sessions.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/unit/test_foundation_contract.py
tests/repository/test_repository_policy.py
tools/check_repository.py
docs/LOCAL_AUTHENTICATION.md
docs/DATABASE_ROLES.md
docs/OPERATIONS.md
migrations/alembic/README.md
oap/active
oap/orders/010-f-repair-session-proof-and-ci.md
oap/reports/010-f-repair-session-proof-and-ci.md
```

Use the minimum subset. No dependency, lockfile, unrelated migration, web,
edge, Compose, or Node path may change.

## Requirements

### 1. Repair complete migration/packaging inventories

Update every exact expected relation/object/grant inventory affected by the
new `control.user_session` table and lifecycle functions. Preserve strictness:
do not weaken an equality assertion to subset/contains, skip a check, or make
the inventory dynamic. The complete migration lifecycle and privilege gate
must pass on a fresh disposable database and GitHub PostgreSQL 14–18. The
downstream Compose smoke must then pass without a Compose-specific bypass.

### 2. Put constant-time comparison in the real path

Keep PostgreSQL equality as a defense-in-depth/race guard, but make
`secrets.compare_digest` (through the typed helper) execute on the stored and
presented fixed-size session digest before authority is returned. For
state-changing resolution and revoke, do the same for the CSRF digest.

Use a narrow owner-created Control-only lock/lookup/finalize function contract
or an equivalently atomic design. Any stored digest returned to application
code is non-secret defense material visible only to `slaif_control`; direct
table access remains denied. The application comparison and database recheck
must occur in one transaction/row-lock boundary so revoke/state/expiry cannot
race between them. Preserve fixed search path, owner, `PUBLIC` revoke, exact
Control execute grant, and stable external failure.

Do not merely add another unused helper/test assertion. Prove with an injected
comparison spy or equivalent unit contract that the production semantic
resolve and revoke paths call the constant-time primitive for the required
digests.

### 3. Separate safe authentication from state-changing CSRF

Expose explicit semantic operations:

```text
resolve/authenticate session token for safe/read requests
resolve/authenticate session token + bound CSRF for state-changing requests
revoke/logout with session token + bound CSRF
```

Safe resolution must not require or accept a CSRF token. State-changing
resolution must require both and reject missing/malformed/wrong/cross-session
CSRF. Revoke must require both, remain idempotent externally, and never reveal
unknown/revoked/session/user state. Do not create an ambiguous optional-CSRF
public method where a caller can accidentally omit enforcement for a declared
state-changing operation.

### 4. Complete deterministic integration evidence

Using the actual `slaif_control` role and owner inspection only for test setup/
assertions, prove independently:

- valid safe resolve succeeds without CSRF;
- valid state-changing resolve succeeds only with its bound CSRF;
- malformed/unknown public ID, wrong session secret, wrong CSRF, and CSRF from
  a second valid session all fail with one constant result and no mutation;
- disabled user, revoked session, idle-expired session, and absolute-expired
  session fail; recent-auth transitions true to false using DB state/time;
- touch before threshold does not write; touch after threshold advances
  `last_seen_at` but never beyond absolute expiry or refreshes recent-auth;
- correct-CSRF revoke is idempotent, wrong-CSRF revoke does not revoke, and no
  later resolve/touch can revive the session;
- concurrent resolve/touch/revoke ends revoked with monotonic timestamps and
  no post-revoke authority; and
- cancellation while blocked/in transaction rolls back and leaves the complete
  session row unchanged.

Manipulate test rows/database locks deterministically instead of wall-clock
sleeps where practical. Never weaken constraints to make fixtures pass.

### 5. Preserve bounded scope and documentation truth

Retain all `010-e` token/cookie/policy/config semantics and accepted earlier
rounds. Update docs only where the safe-vs-state-changing split, constant-time
transaction, or proven behavior changes. Continue to state that no HTTP route,
middleware, browser cookie, UI, OIDC flow, MFA, security-event persistence,
site, membership, capability, or publication exists yet.

## Observable acceptance criteria

1. Fresh migration/bootstrap/privilege lifecycle passes locally and on
   PostgreSQL 14–18; exact inventories include all session objects.
2. The actual safe resolve, state-changing resolve, and revoke paths use
   application constant-time comparison plus a same-transaction DB recheck.
3. Safe requests authenticate without CSRF; state-changing/revoke operations
   cannot proceed without the correct session-bound CSRF proof.
4. Every negative/expiry/recent-auth/touch/race/cancellation case above has
   executable unchanged-state/terminal-state evidence.
5. No session can be revived, extended beyond absolute expiry, or have
   recent-auth refreshed by resolve/touch/revoke.
6. No adjacent feature/dependency/schema outside the repaired session slice is
   introduced.
7. Exactly one existing PR is amended; all 20 checks on the report head pass,
   no rerun is used, and immutable report publication follows protocol 1.2.

## Verification required

Run affected unit/static/config/database tests, then at most two post-repair
invocations of the focused `test_human_session.py` integration set. Run the
fresh migration lifecycle/privilege set once within that bounded DB evidence if
possible, plus affected Ruff/format/mypy/compile, repository policy, secret/log/
repr scan, exact allowed paths/prior hashes, no conflict markers, and
`git diff --check`.

Do not locally run full PostgreSQL matrices, Compose, supply-chain/image, Node,
Playwright, or generated-tree Markdown. Lint only explicitly changed Markdown
with `--no-globs`. GitHub runs the full 20-check gate once; no rerun.

## Safety constraints

Use generated fake secrets and disposable PostgreSQL only. Never print token,
digest, password/hash, cookie, DSN, driver error, or private URL. Preserve full
and compact architecture, constitutions, OAP history, Argon2/setup/identity
security, role separation, and every prior regression.

## GitHub workflow and required report

Verify the exact starting head, amend only the existing PR branch with one
implementation commit, commit this order/active unchanged, push, and never
create/merge/close another PR. Observe the single CI/CodeQL generation without
rerun. Atomically publish exactly:

```text
oap/reports/010-f-repair-session-proof-and-ci.md
```

The final report-only `SELF` commit must have the literal implementation head
as first parent. Report every function/grant/API change, proof that constant-
time comparison is called, all required integration cases and exact attempts,
CI jobs, scope/prior hashes, skipped work, no-rerun/no-new-PR/no-merge state,
and `Report publication commit: SELF`.

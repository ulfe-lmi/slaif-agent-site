# OAP Work Order — 010-e

## Objective

Amend PR `#15` with the server-side human-session foundation only: opaque
digest-only session and CSRF secrets, bounded cookie policy, database-clock
idle/absolute expiry, recent-auth state, revocation, controlled touch, and
least-privilege persistence.

Do not add setup/login/logout HTTP routes, web UI, NGINX/Compose wiring, OIDC
flow, sites, memberships, capabilities, or publication. Those remain later
rounds on this same PR.

This activates the session/persistence slice of inert proposal
`workorders/009-a-setup-local-auth-sessions-csrf.md` as live round `010-e`.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-e`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Current remote `main`: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `f34bd92462173c3d70c923576a2f2f1cb8d5b882`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective PR, open, non-draft, mergeable, and clean.
Do not create another PR, rebase, force-push, merge, close, or enable
auto-merge.

## Verified current state and prior-round disposition

Rounds `010-a` through `010-c` establish setup-token, local identity, Argon2id,
and atomic first-administrator persistence. Round `010-d` normally merged
current main and compact governance without feature changes. Its report was
truthfully `PARTIAL` only because the exact local Markdown command traversed
generated `.venv`, `node_modules`, and `.next` trees; independent tracked-source
checks and all 20 checks on the exact report head are successful. No source
remediation is required for that environmental result.

Current code intentionally has no server-side human-session relation or
semantic session service and no online authentication route. `ServiceSettings`
already enforces production HTTPS, a strong app secret, and secure-cookie mode.
Revision `009_001` owns local identity and is unmerged; this round adds one new
forward revision rather than rewriting accepted migrations.

## Hard execution budget

- Target duration: 45 minutes; hard stop at 75 minutes.
- Focused PostgreSQL integration invocations: 2 maximum.
- Implementation commits/check generations: 1 maximum before the report.
- GitHub workflow reruns: 0.
- Broad local Compose, supply-chain/image, Node, browser, or full DB matrix: 0.

If the bounded attempts or single GitHub generation fail, publish `PARTIAL`
with exact evidence and stop. Diagnose before acting; do not repeatedly rerun
unchanged failures.

## Allowed scope

Expected implementation paths:

```text
services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py
services/backend/src/slaif_agent_site/identity/**
services/backend/src/slaif_agent_site/control_api/config.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/tests/unit/**session**
services/backend/tests/unit/test_control_config.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/integration/test_human_session.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_control_database_integration.py
migrations/alembic/README.md
docs/CONFIGURATION.md
docs/LOCAL_AUTHENTICATION.md
docs/DATABASE_ROLES.md
docs/OPERATIONS.md
tests/repository/test_repository_policy.py
tools/check_repository.py
oap/active
oap/orders/010-e-human-session-csrf-foundation.md
oap/reports/010-e-human-session-csrf-foundation.md
```

Use the minimum subset. A differently named focused session module/test is
acceptable when consistent with repository structure. No web/Node/Compose/edge
path may change.

## Requirements

### 1. Forward migration and persisted session model

Add revision `010_001` after `009_001`. Create a non-COW
`control.user_session` model sufficient to enforce:

```text
session UUID / opaque public lookup identifier
secret digest only (exactly 32 bytes)
CSRF secret digest only (exactly 32 bytes)
user_account_id with explicit lifecycle FK policy
created_at
last_seen_at
absolute_expires_at
recent_auth_at
revoked_at nullable
```

Use database-clock timestamps, bounded/checkable ordering constraints, unique
lookup/digest constraints, and expiry/user indexes. Plaintext session or CSRF
tokens must never enter PostgreSQL. The table is not COW-enabled.

Owner-created, fixed-search-path, fully qualified `SECURITY DEFINER` functions
must provide only the operations needed to create, resolve/touch, and revoke a
session. Revoke `PUBLIC`; grant exact execution only to `slaif_control`; deny
direct relation access to Control and every runtime/reviewer role. Update
privilege validation and migration/package policy accordingly.

### 2. Opaque secrets

Implement typed session/CSRF secret helpers using `secrets`, at least 256 bits
of entropy per secret, explicit versioned formats, SHA-256 or app-secret HMAC
digest, strict parsing/length bounds, and `secrets.compare_digest`. Public IDs
may support indexed lookup but reveal no user, expiry, or authority.

Plaintext values may exist only at issuance/request boundaries. Exclude them
from repr, serialization, exceptions, logs, traces, URLs, database parameters
other than their digests, and normal test output. Never store a recoverable
secret. Use generated fake values only in tests.

### 3. Session lifecycle semantics

Provide a typed Control session service/adapter that can:

- create a session for a trusted, already-authenticated active local user;
- resolve a presented session token to the minimal internal user/session
  context only after digest/state/user/idle/absolute checks;
- validate the separately presented CSRF token against that session;
- touch `last_seen_at` with bounded write amplification and database time;
- revoke/logout idempotently; and
- report recent-auth as a server-derived boolean/window, never caller-selected.

Creation sets `recent_auth_at` from database time because the caller boundary is
trusted authentication code; callers cannot submit timestamps. Resolution must
fail closed when session/user is unknown, disabled, revoked, idle-expired,
absolute-expired, malformed, or secret-mismatched. Failure surfaces are stable,
constant, and do not reveal whether username/user/session exists.

Idle timeout, absolute lifetime, recent-auth window, and touch interval must be
typed, bounded configuration with safe defaults and validation:

```text
0 < touch interval < idle timeout < absolute lifetime
0 < recent-auth window <= absolute lifetime
```

Use database time for authorization. Application wall-clock injection is
allowed only for pure format/unit tests, not DB expiry decisions.

### 4. Cookie and CSRF policy contract

Define/test the cookie attributes later HTTP handlers must use:

- HTTP-only session cookie;
- production `Secure` and `__Host-` semantics (Path `/`, no Domain);
- `SameSite=Lax` or stricter;
- bounded Max-Age no greater than absolute session lifetime;
- development-local cookie variant that does not overclaim HTTPS security;
- no browser local/session storage; and
- CSRF token delivered separately from the HTTP-only session secret and
  required for every future state-changing cookie-authenticated Control call.

This round implements policy/value objects and semantic validation only, not
an HTTP response/cookie or route.

### 5. Concurrency, cancellation, and security behavior

Prove deterministic behavior for concurrent resolves/touches/revokes, revoke
racing touch, cancellation/transaction rollback, replay after revoke, and
database failure. Touch must never revive/extend an expired or revoked session,
extend beyond absolute expiry, or refresh `recent_auth_at`.

Do not add a password-login lookup, login rate limiter, setup/login/logout
route, auth middleware, browser cookie, UI, security-event table, OIDC client,
MFA, membership, invitation, or user-management behavior in this round.

## Observable acceptance criteria

1. Revision `010_001` is deterministic/reversible, adds only the bounded
   session objects/functions, and retains exact role separation/hardening.
2. Database stores only 32-byte session/CSRF digests; plaintext never appears
   in schema, audit/log output, repr, serialized models, or exceptions.
3. Create/resolve/CSRF/touch/revoke enforce active user, revocation, idle and
   absolute expiry, recent-auth, bounded touch, and constant external failure.
4. Unknown/malformed/wrong/expired/revoked/cross-session tokens and CSRF
   substitution fail before authority is returned; state remains unchanged.
5. Concurrency and cancellation cannot revive, overextend, or partially mutate
   a session.
6. Cookie-policy tests prove production and local behavior without adding an
   HTTP route or browser storage.
7. No adjacent feature/dependency/schema outside this session slice changes.
8. Exactly one existing PR is amended; all 20 checks on the report head pass,
   no rerun is used, and immutable report publication follows protocol 1.2.

## Verification required

Run focused secret/session/config/database unit tests first, then at most two
invocations of the focused disposable-PostgreSQL human-session integration
set. Run affected Ruff/format/mypy/compile, migration graph/package,
repository-policy, secret/log/repr scans, `git diff --check`, exact allowed-path,
prior-artifact hash, and no-feature checks.

Do not locally run full PostgreSQL matrices, Compose, supply-chain/image, Node,
Playwright, or the generated-tree Markdown glob. If tracked documentation
changed, lint only its explicit changed paths with Markdownlint `--no-globs`.
GitHub must run the complete unchanged 20-check gate once.

## Documentation required

Update local-auth/config/database-role/operations/migration documentation for
implemented persistence, opaque-token/CSRF/cookie policy, timeout/recent-auth
semantics, resource cost, and deliberate absence of HTTP/UI/OIDC/MFA/audit
events. Keep implemented-versus-planned wording exact.

## Safety constraints

Use only fake generated secrets and disposable PostgreSQL. Never print tokens,
digests, hashes, passwords, cookies, DSNs, or driver errors. Preserve Argon2,
setup, identity, Control-role, full/compact architecture, OAP history, and all
prior tests. No production or protected resource access.

## GitHub workflow

Fetch/verify the exact open PR and starting head, amend only its existing
branch with one implementation commit, commit this order and active pointer
unchanged, push, and never create/merge/close another PR. Observe the single
CI/CodeQL generation without rerun. Publish the report last as a report-only
`SELF` commit whose first parent is the literal implementation head.

## Required report

Atomically publish exactly:

```text
oap/reports/010-e-human-session-csrf-foundation.md
```

Follow protocol 1.2 in full. Include schema/function/grant inventory; token and
cookie formats without secrets; lifecycle/time semantics; every negative/
concurrency/cancellation case; exact local attempts; docs; allowed-path/prior
artifact hashes; all current-head checks; skipped/prohibited work; literal
implementation SHA; and `Report publication commit: SELF`.

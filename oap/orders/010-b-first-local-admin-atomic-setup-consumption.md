# OAP Work Order — 010-b

## Objective

Amend PR `#15` with the first local human identity/password boundary and an
atomic setup-token consumer that creates exactly one initial Platform
Administrator, clears the setup token, and closes installation setup in one
transaction.

Do not add HTTP routes, login sessions, cookies, CSRF, recent-auth, UI, sites,
memberships, capabilities, publication, default Compose setup issuance, or an
OIDC client/flow in this round.

## Planned objective context

Objective 010 remains one PR with bounded rounds:

```text
010-a  accepted slice: installation state + owner-only token issuance
010-b  active: first local identity/password + atomic token consumption
010-c  planned: server-side sessions + cookies + CSRF + expiry + recent-auth
010-d  planned: setup/login/logout HTTP/UI/Compose/NGINX/responsive E2E + closure
```

Only 010-b is active. Do not pre-implement 010-c or 010-d. Do not merge PR
`#15` even if this slice is complete and green.

## Hard execution budget

- Target executor duration: 45 minutes; hard stop at 60 minutes.
- Focused disposable PostgreSQL integration invocations: at most 2.
- Implementation commits/check generations: at most 2; a second is permitted
  only for one directly evidenced, in-scope correction.
- GitHub workflow reruns on an unchanged head: at most 1, only for a proven
  external runner/service failure.
- Local full supply-chain/image/SBOM/Grype run: 0.
- Local full Compose smoke: 0.
- Local full Python/PostgreSQL matrix: 0.
- Node/Playwright run: 0.

At cap exhaustion or hard stop, publish `PARTIAL`. Do not continue a failing
loop or broaden scope.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Current remote/report head:
  `aec0f719042494b9c63a9496204e41fd19326767`
- 010-a implementation head:
  `179e347e57f9e9544a1dc3dcc799b90b6cbf01ac`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective-010 PR. Its current report-head 20-check set
is green with zero open code-scanning alerts. Preserve 010-a order/report and
all earlier OAP artifacts exactly. Do not create a new PR, force-push, merge,
close, enable auto-merge, or act on Dependabot PRs `#12`/`#13`.

## Strategic context

010-a created owner-only `control.installation_state` plus transactional
ensure/rotate/revoke/status issuance. It stores only a SHA-256 digest of a
uniform 256-bit setup token and deliberately has no consumer or initializer.

Architecture Sections 18, 32, 33, Appendix B, and the original setup/auth
proposal require local authentication without permanent default credentials,
the first Platform Administrator created only by a valid one-use setup token,
memory-hard password hashing, and optional OIDC identity represented by stable
`(issuer, subject)` rather than email. Site roles remain separate and belong
to later live objectives.

The selected password dependency is the current verified PyPI release:

```text
argon2-cffi==25.1.0
license: MIT
Python: >=3.8, including 3.12–3.14
profile: RFC_9106_LOW_MEMORY / Argon2id
```

Use the PyPI registry and committed `uv.lock` artifact hashes only. No Git,
direct URL, local path, editable source, hosted identity service, or password
API is allowed.

## Bounded scope

Expected areas are limited to:

```text
pyproject.toml
uv.lock
AGENTS.md                         # direct dependency baseline line only
services/backend/src/slaif_agent_site/identity/**
services/backend/src/slaif_agent_site/control_api/config.py
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/control_api/app.py
services/backend/src/slaif_agent_site/db/alembic/versions/009_001_local_identity.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/tests/unit/test_identity_*.py
services/backend/tests/unit/test_control_*.py
services/backend/tests/integration/test_installation_setup.py
services/backend/tests/integration/test_local_identity.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_control_database_integration.py
tests/repository/test_repository_policy.py
tools/check_repository.py
tools/compose/control_readiness.py
migrations/alembic/README.md
docs/INSTALLATION_SETUP.md
docs/LOCAL_AUTHENTICATION.md
docs/DATABASE_CONNECTIONS.md
docs/DATABASE_BOOTSTRAP.md
docs/CONFIGURATION.md
docs/OPERATIONS.md
supply-chain/**                   # only generated/policy evidence required by dependency change
THIRD_PARTY_NOTICES.md            # only if the existing generator requires it
oap/active
oap/orders/010-b-first-local-admin-atomic-setup-consumption.md
oap/reports/010-b-first-local-admin-atomic-setup-consumption.md
```

Revision-exact tests/tools may be adjusted directly. Do not touch every listed
path mechanically. Any path exception must be necessary for this exact
identity/dependency boundary and reported explicitly.

## Explicit non-goals

- No `/setup`, `/login`, `/logout`, user-management, site, workspace, editor,
  agent, publication, OpenAPI, or other HTTP route.
- No browser session table, cookie, session token, CSRF token, recent-auth,
  login throttling, password reset, email invitation, MFA, or logout behavior.
- No Next.js/React/TypeScript/UI/Playwright change.
- No Compose, NGINX, Apache, Dockerfile, workflow, service mount, or default
  startup behavior change.
- No OIDC discovery, network call, client secret, redirect/callback, token
  validation, or login flow. Only the persistence constraint for a future
  `(issuer, subject)` identity may be established.
- No site membership, site role, delegation ceiling, custom role, capability,
  agent preset, or publish permission.
- No plaintext password or setup token in database, logs, errors, repr,
  serialization, URLs, cookies, environment, fixtures, or committed output.
- No direct table access for Control or another runtime/reviewer role.
- No generic SQL/native pool exposure and no caller-selectable database
  identity.

## Requirements

### A. Qualified memory-hard password dependency

Add exact runtime dependency `argon2-cffi==25.1.0`, regenerate `uv.lock`, and
verify frozen installation on Python 3.12–3.14 and in the existing Alpine OCI
build through GitHub. Preserve registry source URLs and hashes; reject any
VCS/direct/local/editable fallback.

Update the exact direct-dependency baseline and generated license/provenance
evidence required by repository policy. Verify the direct MIT metadata and all
new transitive application licenses. Do not add a second password library.

### B. Password policy and hash service

Create a product-owned identity module using
`PasswordHasher.from_parameters(RFC_9106_LOW_MEMORY)` so the pinned release's
Argon2id profile is explicit. Do not use the testing-only `CHEAPEST` profile in
production source.

The service must:

- accept plaintext only as `SecretStr` at the semantic boundary;
- require a bounded local password length (minimum at least 12 characters,
  maximum no more than 1024 characters and a bounded UTF-8 byte length);
- reject NUL and equality to the normalized username; avoid brittle mandatory
  character-class rules;
- create self-describing Argon2id hashes with random salts;
- verify correct and incorrect passwords through one stable boolean/result
  contract without leaking library exception text;
- expose `check_needs_rehash` for later login-time upgrades;
- use constant public-safe errors and exclude plaintext from repr,
  serialization, logs, and database parameters after hashing;
- make tests fast only by injecting an explicitly test-owned hasher/profile;
  never lower the production profile globally or through environment input.

Document the pinned profile values and operational memory implication. Make no
claim that immutable Python strings can be securely wiped.

### C. Identity persistence

Add exactly one Alembic revision `009_001` after `008_001`. It may create only
the minimum identity/initial-installation objects:

```text
control.user_account
control.platform_administrator
narrow setup-lock/read and setup-completion functions
```

`user_account` must support a constrained identity kind:

- `LOCAL`: bounded ASCII username plus deterministic normalized username,
  Argon2id hash, no OIDC issuer/subject;
- `OIDC`: future `(oidc_issuer, oidc_subject)` identity, no local username or
  password hash;
- email/display name are mutable profile fields and never immutable identity;
- status is bounded and the first local administrator begins active;
- UUID and all semantic input are application-owned, not generated from
  caller database context.

Enforce unique normalized local username and unique non-null OIDC
`(issuer,subject)` using deterministic constraints/indexes. Restrict the first
round's username to a clearly documented ASCII grammar so database and Python
normalization agree exactly. Password-hash constraints must accept only the
selected Argon2id version/profile shape, without storing plaintext.

`platform_administrator` is a separate installation-level assignment. Do not
put site roles or a global site-role field on `user_account`.

All new relations/functions are owned by `slaif_owner`; revoke `PUBLIC` and
all direct runtime/reviewer relation access. No agent/editor/reader/reviewer/
scheduler/media/GC role may read password hashes, setup digests, or user rows.

### D. Narrow Control transaction; no raw pool

Extend the Control-owned database adapter with one semantic operation for
initial local-administrator setup. Do not expose its asyncpg pool, connection,
native SQL, or generic execute/fetch surface.

Use narrow owner-created `SECURITY DEFINER` functions with exact fixed
`search_path=pg_catalog`, fully qualified objects, no dynamic SQL, `PUBLIC`
revoke, and execute granted only to `slaif_control` where needed.

The operation must:

1. validate username/display/profile/password/token shape before database DML;
2. hash the password outside the locked transaction using the production
   Argon2id service;
3. open one Control pool connection and transaction;
4. call a narrow function that locks the installation singleton and returns
   only initialized/token expiry/generation plus the stored high-entropy
   digest to the trusted Control process;
5. compare the presented setup token with `secrets.compare_digest` through the
   010-a helper;
6. call a narrow completion function in the same transaction, passing the
   expected generation and presented digest as defense-in-depth race guards;
7. insert exactly one local user plus one platform-administrator assignment;
8. set `initialized_at` with the database clock and clear all setup-token
   material atomically;
9. return a bounded identity result without password hash or setup digest.

The completion function must itself lock/recheck uninitialized state, token
presence/expiry, generation, and digest. A compromised caller cannot invoke it
without possession of a matching current setup token. Application constant-
time comparison is primary; the database equality is an invariant/race guard.

Use one constant external-safe failure for malformed/invalid/expired/replayed/
initialized/conflicting setup. Do not disclose which check failed. Preserve
`CancelledError`; roll back fully on cancellation or any insert/update failure.

### E. Atomicity, replay, and concurrency tests

Add focused unit and one-major PostgreSQL integration/concurrency evidence for:

- production Argon2id profile/encoded hash shape, random salts, correct/wrong
  verify, rehash detection, bounded policy, test-only cheaper injection, and
  no plaintext/exception leakage;
- migration upgrade/repeat/downgrade/rebuild, exact objects/owners/search paths,
  `PUBLIC` revoke, exact Control execute grants, and all-role denial;
- valid token creates exactly one active LOCAL user and one installation-admin
  assignment, clears token fields, sets initialized once, and returns no hash/
  digest;
- malformed, wrong, expired, revoked, or replayed token yields the same bounded
  failure and leaves user/admin/installation/token state unchanged as expected;
- two concurrent valid attempts create exactly one administrator; the loser
  receives the same bounded failure;
- a forced uniqueness/constraint/error after the lock rolls back user/admin,
  initialization, and token consumption together so a valid retry can succeed;
- cancellation rolls back and does not consume the setup token;
- OIDC-shaped rows obey `(issuer,subject)` uniqueness but no OIDC behavior or
  network call exists;
- Control adapter public surface remains semantic and no other process imports
  identity password or setup-consumer authority;
- no route/session/cookie/CSRF/site/member/publish behavior exists.

Use fake runtime secrets. Do not commit a valid setup token or plaintext
password literal matching production format; construct deterministic test
material in memory and suppress it from normal test output.

## Acceptance criteria for 010-b

1. PR `#15` remains the unique objective-010 PR and is amended only on its
   existing branch; no merge, extra PR, force push, close, auto-merge, or
   Dependabot action occurs.
2. `argon2-cffi==25.1.0` resolves only from PyPI with frozen hashes, approved
   license/transitive inventory, and passing Python 3.12–3.14/Alpine builds.
3. Passwords use explicit RFC 9106 low-memory Argon2id parameters, random salt,
   bounded policy, stable verify/rehash behavior, and never persist or leak as
   plaintext.
4. Migration `009_001` adds only constrained identity/admin/narrow setup
   functions, with exact ownership/grants and zero direct runtime table access.
5. A valid current setup token creates one local Platform Administrator and
   closes setup atomically; invalid/expired/replayed/concurrent/failing/
   cancelled attempts preserve fail-closed state and reveal no reason detail.
6. OIDC persistence uses stable `(issuer,subject)` and email is not identity;
   no OIDC flow/network/configuration is implemented.
7. No session/cookie/CSRF/recent-auth/route/UI/site/membership/capability/
   publication/Compose behavior exists; those remain later rounds.
8. Documentation is exact, all required checks are successful with zero open
   CodeQL alerts, and the 010-b report/transcript follows protocol 1.2.

## Verification required

Run only focused password/identity/setup/config/database unit tests; at most
two invocations of directly affected integration/concurrency tests on one
local PostgreSQL major; frozen lock/install and package/license policy checks
needed for the new dependency; affected Ruff/format/mypy/compile; migration
head/history; repository and Markdown checks; secret/authority/no-route scans;
`docker compose config --quiet` if unchanged; and `git diff --check`.

Do not run locally:

```text
tools/supply_chain/run.sh
full OCI image/SBOM/Grype/reproducibility gate
full Compose smoke
all PostgreSQL majors
full Python version matrix
pnpm or Playwright
```

GitHub runs the complete current gate, including Python 3.12–3.14,
PostgreSQL 14–18, Alpine Compose packaging, dependency/license/SBOM evidence,
and CodeQL. Respect the generation/rerun caps.

## Documentation required

Create/update the local-authentication, installation-setup, database,
configuration, operations, migration, dependency, and attribution docs needed
for implemented behavior. State explicitly:

- the first local administrator can now be created atomically only through the
  semantic Control adapter in code/tests;
- no HTTP setup/login route or default startup issuance exists yet;
- no browser session/CSRF/recent-auth exists until 010-c;
- no UI/NGINX/Compose operator flow exists until 010-d;
- no OIDC authentication exists; only the future identity-key constraint is
  represented.

Do not claim local authentication is usable from a browser.

## Safety / security constraints

Use only disposable PostgreSQL and fake generated test values. Never access
production resources. Never print or commit a password, setup token, token
digest, password hash tied to a real secret, locator, cookie, or private URL.
Preserve all existing Control/COW/role/readiness/Compose/supply-chain
boundaries. Do not weaken Argon2 parameters, database checks, or negative tests
to manufacture completion.

## Local execution capability

Passwordless sudo/local PostgreSQL/Docker are available. Routine dependency
resolution and test setup belong to the coding agent. Do not ask the human or
strategic model to operate the environment.

## GitHub workflow

Fetch and verify PR `#15`, update its existing branch only, commit the exact
010-b order and `oap/active` unchanged with implementation, and never create a
new PR or merge. Inspect GitHub within caps. Publish the report as the final
report-only `SELF` commit whose parent is the literal implementation head.

## Required report

Atomically publish exactly:

```text
oap/reports/010-b-first-local-admin-atomic-setup-consumption.md
```

Use protocol 1.2 in full. Include dependency version/source/hashes/license,
Argon2 profile and policy facts, schema/functions/grants, atomic success/
rollback/replay/concurrency/cancellation evidence, intentional secret handling,
attempt/check-generation timestamps/durations, path/prior-artifact integrity,
later-round exclusions, GitHub checks/alerts, exact PR identity, literal
implementation head, and `Report publication commit: SELF`.

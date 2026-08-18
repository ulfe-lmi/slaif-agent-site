# OAP Work Order — 010-a

## Objective

Create the single objective-010 PR and implement only the owner-controlled
installation-state and setup-token issuance foundation. Persist installation
state, generate a high-entropy expiring setup token, store only its digest,
and provide an explicit one-shot bootstrap CLI lifecycle for initial issue,
status/recovery, rotation, and revocation.

Do not implement users, password hashing, token consumption, initialization,
sessions, cookies, CSRF, HTTP routes, UI, OIDC, sites, memberships, or Compose
startup wiring in this round.

## Planned objective-010 rounds

Objective 010 intentionally spans one PR through bounded execution rounds:

```text
010-a  installation state + owner-only setup-token issuance lifecycle
010-b  first local identity/password + atomic token consumption/initialization
010-c  server-side human sessions + cookies + CSRF + expiry + recent-auth
010-d  setup/login/logout HTTP surfaces, NGINX/Compose wiring, responsive E2E,
       final documentation and objective acceptance
```

Only `010-a` is active. Do not pre-implement later rounds. A successful 010-a
report does not authorize merge; the strategic model will review it and, if
satisfactory, activate 010-b on the same PR.

## Hard execution budget

- Target executor duration: 45 minutes; hard stop at 60 minutes.
- Focused disposable PostgreSQL integration invocations: at most 2.
- Implementation commits/check generations: at most 2; use the second only
  for one directly evidenced in-scope correction.
- GitHub workflow reruns on an unchanged head: at most 1 and only for a proven
  external runner/service failure.
- Local full supply-chain/Image/SBOM/Grype runs: 0.
- Local full Compose smoke: 0.
- Local full Python/PostgreSQL matrices: 0.
- Node install/build/Playwright runs: 0.

At the hard stop or after caps are exhausted, publish a truthful `PARTIAL`
report. Do not turn this slice into another open-ended CI/debugging campaign.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective-010 PR: none
- Required branch: `oap/010-installation-local-auth`
- Base branch: `main`
- Verified remote main:
  `d4d1c7b7fd27ad2245f0b1224792a252d5274b5c`
- Required PR title:
  `[OAP 010] Establish secure installation and local authentication`
- Proposal source:
  `workorders/009-a-setup-local-auth-sessions-csrf.md` in the strategic
  workspace, deliberately split across 010-a through 010-d

PRs `#12` and `#13` are unrelated Dependabot PRs. Do not modify, close, merge,
rebase, comment on, or otherwise act on them.

## Strategic context

Objective 009 established one isolated Control credential, exact login/role
verification, a bounded asyncpg pool, and sanitized database readiness. It did
not add setup, authentication, users, sessions, sites, or product routes.

Architecture Sections 14.2, 32.1–32.4, 41.9, 46, 52.1, and Appendix B require
a random expiring one-use installation token whose plaintext is shown only to
the operator, whose database representation is digest-only, and whose eventual
consumption atomically creates the first Platform Administrator and closes
setup. This round builds only the owner-side persistence and issuance half;
010-b will add the atomic first-user consumption boundary.

## Current verified state

- Remote `main` is the merged objective-009 commit above and its CI/CodeQL are
  green.
- Alembic has one head, `007_001`.
- `control.bootstrap_readiness` and the narrow
  `control.slaif_control_readiness()` function are the only Control database
  objects beyond Alembic metadata.
- The one-shot bootstrap owns migrations/reconciliation through setup-owner
  authority. Control has no direct table access and no generic SQL surface.
- No application user, installation-state, setup-token, session, CSRF, or
  authentication implementation exists.
- The repository remains pre-alpha, fresh-install-only, and uses no hosted
  identity provider or account-bound service.

## Bounded scope

Expected paths are limited to:

```text
services/backend/src/slaif_agent_site/bootstrap/__main__.py
services/backend/src/slaif_agent_site/bootstrap/config.py
services/backend/src/slaif_agent_site/bootstrap/service.py
services/backend/src/slaif_agent_site/bootstrap/setup_token.py
services/backend/src/slaif_agent_site/db/alembic/versions/008_001_installation_state.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/tests/unit/test_bootstrap_*.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_installation_setup.py
tests/repository/test_repository_policy.py
tools/check_repository.py
migrations/alembic/README.md
docs/INSTALLATION_SETUP.md
docs/DATABASE_BOOTSTRAP.md
docs/CONFIGURATION.md
docs/OPERATIONS.md
oap/active
oap/orders/010-a-installation-state-setup-token-foundation.md
oap/reports/010-a-installation-state-setup-token-foundation.md
```

Use existing test files when that is clearer; do not touch every listed path
mechanically. Any path outside this list requires a direct, reported reason
and must remain within this exact lower-layer scope.

## Explicit non-goals

- No `control.user_account`, password hash, login/logout, browser session,
  cookie, CSRF, recent-auth, OIDC, or human authentication code.
- No `/setup`, `/login`, `/logout`, user, site, workspace, agent, editor,
  publication, or other product route.
- No Next.js/React/TypeScript/Puck/Playwright/UI change.
- No Compose, NGINX, Apache, Dockerfile, workflow, dependency, lockfile,
  package, image, secret-volume, or service-authority change.
- No setup token in an environment variable, URL, query string, fragment,
  cookie, log field, exception, repr, committed fixture, or database plaintext.
- No direct Control/runtime role access to the installation-state table.
- No function that marks the installation initialized before first-user
  creation exists; 010-b owns the eventual atomic consume-and-create boundary.
- No permanent demo administrator, fixed setup token, hosted identity service,
  invitation/email, MFA, site membership, role assignment, or publication.

## Requirements

### A. Installation-state migration

Add exactly one Alembic revision `008_001` after `007_001`. It may create only
the minimum singleton `control.installation_state` relation and seed its one
uninitialized row. It must include at least:

```text
singleton
initialized_at
setup_token_digest
setup_token_issued_at
setup_token_expires_at
setup_token_generation
updated_at
```

Enforce database constraints so:

- exactly one logical singleton row is possible;
- the digest is exactly SHA-256 length when present;
- token digest/issued/expiry are all null or all non-null;
- expiry is later than issuance;
- an initialized installation cannot retain setup-token material;
- generation is non-negative and monotonically advanced by the service;
- timestamps are timezone-aware database timestamps.

Revoke `PUBLIC`. Do not grant table DML or SELECT to Control, Agent, Editor,
readers, Reviewer, Scheduler, Media, GC, or unrelated roles. Update product
privilege inventory/validation so the new relation is expected in both
`EMPTY_SAFE` and future `HARDENED` states while still reporting any unintended
role access.

Upgrade, repeat-upgrade, downgrade, rebuild, one-head, ownership, schema,
default-privilege, and denial behavior must be tested. The migration must not
create a user/session/site table or function.

### B. Cryptographic token contract

Define one versioned token format with a non-secret fixed prefix and at least
256 bits of randomness from Python's cryptographic `secrets` module. Use a
plain SHA-256 digest only because the token is uniformly high entropy; this is
not the future password-hashing path.

The token implementation must:

- return plaintext only in an explicitly secret-safe value such as
  `pydantic.SecretStr` inside the one-shot process;
- expose a pure digest function suitable for constant-time verification in
  010-b;
- never include plaintext in dataclass/model repr, serialization, exception,
  structured logging, audit metadata, or persisted rows;
- validate the fixed prefix/shape before digesting presented material;
- use `secrets.compare_digest` for any comparison helper;
- make tests deterministic by injecting/patching the randomness boundary,
  never by weakening production randomness.

Do not add a dependency for token generation or hashing.

### C. Owner-only issuance lifecycle

Implement the lifecycle through a small bootstrap-owned service using
`owner_connection`; do not give the long-running Control pool table access.
Every state change must use one PostgreSQL transaction and lock the singleton
row before deciding.

Required actions:

1. **Ensure/issue:** if uninitialized and no unexpired token exists, generate
   one, store only its digest/timestamps, increment generation, and return the
   plaintext once. If an unexpired token already exists, return only bounded
   status/expiry/generation and no plaintext.
2. **Rotate:** only while uninitialized, replace the digest atomically,
   increment generation, invalidate the old digest, and return the new
   plaintext once.
3. **Revoke:** only while uninitialized, clear digest/issued/expiry atomically
   without marking initialized; repeated revoke is idempotent.
4. **Status:** return only initialized/token-present/expiry/generation facts,
   never the digest or token.
5. **Initialized:** owner-side issue/rotate must fail closed once
   `initialized_at` is non-null; no round-010-a command may set that field.

Use the database clock for issuance and expiry decisions. Bound configured TTL
to 5–60 minutes with a 30-minute default. Do not use sleeps in tests; set test
state or inject time through the database fixture deliberately.

### D. Explicit bootstrap CLI

Add one explicit `setup-token` bootstrap command with mutually exclusive
ensure/default, `--rotate`, `--revoke`, and bounded status behavior. It must:

- preserve `python -m slaif_agent_site.bootstrap --check` as no-DB,
  no-randomness, no-mutation, no-secret output;
- print plaintext only when a fresh token is issued/rotated, to the operator's
  stdout, on its own labeled line;
- print the setup URL separately without putting the token in it;
- on existing unexpired state, print only bounded recovery guidance and require
  explicit `--rotate` to obtain a new plaintext token;
- use constant public failure text on stderr and never print database/driver
  errors or stored digest;
- refuse dangerous argument combinations and initialized-state rotation.

The setup URL is configuration, not a token carrier. Validate a bounded
absolute HTTP(S) `/setup` URL suitable for localhost or production; it may be
documented as not yet served until planned 010-d.

Do not wire this command into default Compose startup in 010-a. That final
operator experience belongs to 010-d, after the atomic consumer and route
exist.

### E. Tests and evidence

Add focused unit and one-major PostgreSQL integration/concurrency coverage for:

- token format/entropy, deterministic digest, constant-time comparison helper,
  secret-safe repr/serialization/error behavior, and malformed token rejection;
- initial issue stores digest only and returns plaintext once;
- concurrent ensure calls produce one issuance and one existing-token result,
  with one active database digest/generation;
- repeated ensure does not rotate or reveal plaintext;
- explicit rotation changes digest/increments generation and invalidates the
  prior digest;
- expiry permits a new issue without sleeping;
- revoke clears token material, is idempotent, and does not initialize;
- initialized state blocks issue/rotate and retains no token material;
- status/CLI existing/revoke/failure paths reveal no token/digest;
- no role except setup owner can read or mutate the relation;
- migration lifecycle and privilege validator remain fail-closed;
- no user/session/site/auth route or product table was introduced.

Tests must use fake/disposable secrets and must not print generated plaintext
into normal test output or committed snapshots.

## Acceptance criteria for 010-a

1. Exactly one new objective-010 PR/branch exists from verified remote main,
   with no action on PR `#12` or `#13`, no force push, merge, close, or
   auto-merge.
2. Migration `008_001` adds only the constrained singleton installation-state
   relation; its ownership, lifecycle, and zero-runtime-access denial matrix
   are proven on one local PostgreSQL major and GitHub PostgreSQL 14–18.
3. Token generation uses a versioned prefix plus at least 256 cryptographic
   random bits; only a SHA-256 digest is stored and plaintext is returned once
   only by the explicit one-shot owner process.
4. Ensure, concurrency, expiry, rotate, revoke, status, and initialized-state
   fail-closed behavior are transactional and tested without sleeps.
5. No token/digest/locator/driver text leaks through repr, serialization,
   logs, errors, URLs, committed fixtures, or database plaintext; the one
   intentional operator stdout disclosure is isolated and tested.
6. `--check` remains side-effect-free; no token consumer, user/password,
   session/CSRF, route/UI, Compose wiring, or later-round behavior exists.
7. Documentation describes implemented 010-a behavior and explicitly marks
   token consumption, first administrator, HTTP setup, and default startup
   wiring as planned 010-b/010-d, not current functionality.
8. All current GitHub checks are successful with zero open CodeQL alerts, and
   the final report/transcript satisfies protocol 1.2.

## Verification required

Run only focused bootstrap/token/config/migration/privilege unit tests; at most
two invocations of the directly affected integration set on one disposable
local PostgreSQL major; affected Ruff/format/mypy; `python -m compileall` or
targeted compile; bootstrap `--check`; repository and Markdown checks;
`docker compose config --quiet` only if Compose remains unchanged; migration
head/history/static policy; secret/leak scans; and `git diff --check`.

Do not run locally:

```text
tools/supply_chain/run.sh
full image/SBOM/Grype gate
full Compose smoke
all PostgreSQL majors
full Python version matrix
pnpm install/build/test
Playwright/browser projects
```

GitHub runs the unchanged complete required check set, including PostgreSQL
14–18, Compose/edge packaging, supply-chain evidence, dependency review, and
CodeQL. Respect the generation/rerun caps above.

## Documentation required

Create `docs/INSTALLATION_SETUP.md` and update only directly affected
configuration/bootstrap/operations/migration documentation. State precisely:

- the token is an operator bootstrap secret, not a human session or agent
  capability;
- plaintext is displayed only on issue/rotation and cannot be recovered from
  the digest;
- explicit rotation is the recovery path if initial stdout is lost;
- 010-a has no consumer, first administrator, `/setup` handler, or default
  Compose issuance yet;
- those later behaviors remain in 010-b and 010-d on the same unmerged PR.

Do not claim authentication or installation initialization is complete.

## Safety / security constraints

Use only disposable local PostgreSQL and fake tokens. Never access production
systems/data/secrets. Never print or commit real database locators, passwords,
setup tokens, digests, cookies, or private URLs. Do not weaken current role,
Control credential, migration, readiness, Compose, supply-chain, or
architecture boundaries to make tests pass.

## Local execution capability

Passwordless sudo and local PostgreSQL/Docker capability are available. The
coding agent owns ordinary test setup and cleanup. No new package should be
necessary; do not transfer routine setup to the human or strategic model.

## GitHub workflow

Fetch authoritative GitHub state, start the required fresh branch from
`origin/main`, commit the exact activated order and `oap/active` unchanged with
the implementation, push, and create exactly one non-draft PR with the
required title. Inspect CI within the hard caps. Never create a second
objective-010 PR, merge, close, enable auto-merge, or touch Dependabot PRs.

## Required report

Atomically publish exactly:

```text
oap/reports/010-a-installation-state-setup-token-foundation.md
```

Use protocol 1.2 in full. Include exact PR/branch/commit identity, migration
objects/constraints/grants, token format and entropy proof, ensure/rotate/
revoke/concurrency/expiry evidence, intentional stdout and non-leak evidence,
attempt/check-generation ledger with timestamps/durations, local setup/cleanup,
all skipped/not-run work, path/scope/prior-artifact integrity, no-later-round
confirmation, GitHub checks/alerts, literal implementation head, and
`Report publication commit: SELF`.

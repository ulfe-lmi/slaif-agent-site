# Local skeleton operations

## Render resolver

Render startup resolves its private database locator, validates the fixed
public-reader identity, and fails readiness closed on configuration,
connectivity, role, or migration mismatch. Shutdown drains the pool within the
configured bound and terminates it on timeout. `python -m
slaif_agent_site.render_api --check` performs no locator read or connection.
Reference Compose derives a one-file `render-secret` volume from the master
public-reader locator and mounts it read-only only in Render. Web calls the
fixed internal resolver URL and has no database credential. The endpoint is
never edge-routed. Removing or corrupting the locator makes Render unhealthy,
Web readiness return 503, and NGINX become unhealthy; restore the coordinated
secret rather than adding a fallback.

The Control process is the only online authority for local credential lookup
and compare-and-set password rehash. It uses fixed-cost Argon2id and an
equal-cost dummy verification path for unknown or disabled identities. Budget
roughly 64 MiB per concurrent Argon2 operation. Backend HTTP login and session
issuance and the local setup/login/admin UI exist; rate limiting, durable login
audit, OIDC, and MFA remain absent. Capability-bound Agent preview-run queue/
status metadata, run-token Render verification, and direct confined worker
execution/private artifact retrieval are implemented. The Agent API now owns a
bounded durable dispatcher: it claims migration-035 leases, mints run-bound
preview credentials, submits and renews attempts, verifies signed results,
retrieves bytes, and atomically registers private artifact metadata with
terminal completion. Restart and transient failures remain safely retryable;
public artifact bytes and artifact GC remain absent. Local
authentication and administration are qualified by one setup project, one
single-writer governance project, and six read-only Playwright browser/device
projects.

## Browser worker

Browser-worker readiness validates the descriptor-confined service credential
and artifact root, fixed Web origin, immutable target table, exact Chromium
executable/version, real sandboxed launch, and hostile-origin interception
self-check. A 503 means the worker must not receive attempts. Restore the exact
secret/root/image/network/security policy; do not add `--no-sandbox`, a fallback
origin, a plaintext credential, or a broader network.

Each accepted direct attempt owns one fresh Chromium/browser context/page and
closes it on success, failure, timeout, disconnect, cancellation, or SIGTERM.
The fixed runtime admits one active attempt and no queue. Overload is therefore
an immediate internal 429. The Agent dispatcher starts and stops with the
Agent API lifespan, uses the existing Agent pool and fixed worker credential,
and is bounded by the dispatcher settings in `docs/CONFIGURATION.md`. It never
exposes worker credentials or artifact bytes through public HTTP. Lease loss,
cancellation, shutdown, and worker/database failures fail closed; expired
leases are recovered by the control-plane claim function.

Private artifacts live only in the `browser-artifacts` volume. Files are mode
`0600`, immutable, digest-checked, and internally retrievable by exact signed
metadata after worker restart. No physical GC exists. Operators may inspect
counts/modes with an offline, read-only UID-0 maintenance container, but must
not edit, rename, relink, or expose files. `docker compose down --volumes`
removes the local store; ordinary `down` preserves it.

Revision `014_001` upgrades and downgrades deterministically with its complete
built-in authorization catalogs. Catalog defaults change only through
migrations. Membership rows are deactivated, not hard-deleted; optimistic
versions and explicit overrides remain inspectable history.

Control now serves authenticated catalog and membership routes. A 401 points to
session lifecycle, 403 to CSRF/current authority/self-or-beyond-authority
policy, 404 to an invisible active-site/user/membership boundary, 409 to
duplicate or expected-version conflict, 422 to typed input, and 503 to the
Control pool. Do not diagnose these by querying relations from the runtime
role. The immutable route-policy registry is checked against actual Control and
Editor handlers in CI; adding a handler requires an exact declaration plus real
enforcement, not a blanket exemption.

These commands operate the default Compose project in a local, non-production
environment. Use an explicit `-p NAME` for disposable tests so cleanup targets
cannot overlap an operator's persistent project.

## Authentication browser qualification

Install the exact test dependency and matching local browser builds, then run
the combined disposable deployment gate:

```bash
pnpm install --frozen-lockfile
pnpm exec playwright install --with-deps chromium firefox webkit
sudo tools/compose/smoke.sh slaif009auth
```

The smoke first renders `/s/demo/` at desktop and 320-pixel phone viewports,
then runs setup. A single Chromium `governance` project creates and administers
a disposable site and existing-user membership through visible controls. Only
after it completes do `desktop-chromium`, `desktop-firefox`, `desktop-webkit`,
`tablet`, `mobile-chromium`, and `mobile-webkit` perform read-only responsive,
keyboard, and logout checks. It retains no trace, screenshot, video, HTML
report, storage state, or credential file. A later stop/start compares site,
domain, membership, secret, and Render fingerprints and verifies setup remains
closed without fixture or demo recreation.

## Lifecycle commands

```bash
docker compose up --build
docker compose up --build --wait
docker compose ps
docker compose logs --tail 200 nginx web control-api bootstrap postgres
docker compose down --remove-orphans
```

The final command preserves named data and secrets. `docker compose stop`
followed by `docker compose up --wait` reuses all five volumes and revalidates
the same generated credentials. Bootstrap must print exactly a safe result
shaped as:

```text
compose-bootstrap: OK revision=011_001 state=EMPTY_SAFE safe=true
```

Do not publish or archive complete logs without reviewing them. The
implementation suppresses database locators and password values, but logs are
still deployment-private operational data.

## Installation setup-token boundary

After an owner migration, an operator may explicitly issue the one-shot setup
token foundation with mounted owner credentials:

```bash
python -m slaif_agent_site.bootstrap setup-token
python -m slaif_agent_site.bootstrap setup-token --status
python -m slaif_agent_site.bootstrap setup-token --rotate
python -m slaif_agent_site.bootstrap setup-token --revoke
```

Compose bootstrap automatically ensures this token on first start. A freshly
issued or rotated plaintext is shown once on its own stdout line; the setup URL is a
separate line and never carries the token. Repeated default issuance returns
only expiry/generation facts and directs the operator to explicit rotation.
The atomic consumer is exposed through the bounded Control backend and existing
default edge route. The operator UI and Compose smoke include the ordered
setup/governance/six-device Playwright E2E. Store real
output only in an operator-approved secret channel and see
[installation setup](INSTALLATION_SETUP.md) for the exact boundary.

## Volumes, backup, and cleanup

The default named volumes are `postgres-data`, `media-data`, `local-secrets`,
`control-secret`, `agent-secret`, `editor-secret`, `media-secret`, and
`render-secret`, prefixed by the Compose project name. PostgreSQL data, master
local secrets, derived online secrets, and referenced private media objects
must be backed up and restored together. Media bytes are immutable digest-keyed
objects; an unreferenced private object can remain after a database failure and
is removed only by a later retention-aware Media GC objective.

Media backup/restore must preserve digest paths, regular-file mode `0600`,
directory confinement, and the metadata digest/MIME/size/key contract. Never
restore media under a public web alias or substitute bytes under an existing
digest. A missing or corrupt referenced object blocks authorized reads and
requires restore/reupload of the matching digest.

There is no automated credential rotation yet. Replacing only password or DSN
files can desynchronize PostgreSQL principals and make bootstrap fail closed.
For a persistent installation, plan and test a coordinated database backup,
role-password update, secret-file replacement, and recovery before attempting
rotation.

For a deliberately disposable test project only, resolve and type its exact
name and then remove only its containers, networks, and volumes:

```bash
PROJECT=slaif007localtest
docker compose -p "$PROJECT" down --volumes --remove-orphans
```

Never use a broad Docker prune as an Agent-Site cleanup procedure. Normal
shutdown omits `--volumes` so local credentials and data survive.

## Failure diagnosis

### Secret initialization

`secrets-init` prints only `READY` or `FAILED`. Failure commonly means a
partial/corrupt file, unexpected mode/owner, or inaccessible volume. It never
overwrites an invalid existing credential. Preserve a real installation for
recovery; remove the exact secret volume only for a known disposable project.

### PostgreSQL

If PostgreSQL is unhealthy, inspect its bounded logs and data-volume capacity.
The administrator password is read from a file and must not be copied into a
shell command or support transcript. A database failure blocks bootstrap and
all dependent services.

### Bootstrap

Bootstrap failure is intentionally reported as `Database bootstrap failed.`.
It can indicate target/authority, migration, COW deployment, privilege,
login-membership, inventory, or readiness-marker failure. NGINX cannot start
until bootstrap exits zero with an independently validated safe-empty marker.
Use the documented one-shot commands and database integration tests for a
disposable diagnosis; do not weaken a grant or marker to bypass the failure.
The clean smoke captures the intentionally broken-bootstrap output and prints
one `negative-bootstrap: correctly blocked` marker. Demo seeding is enabled
only by reference Compose: before setup an exact existing seed is idempotent,
any other site state fails and rolls back, and after setup it is ignored.

### Upstream health

Use `docker compose ps` to identify an unhealthy process, then inspect that
service's bounded log. Control alone has a database pool. Its liveness remains
200 while readiness returns a bounded `database` reason such as
`configuration_invalid`, `connection_unavailable`, `identity_mismatch`,
`role_mismatch`, `migration_mismatch`, `unsafe_marker`,
`foundation_mismatch`, `timeout`, or `shutdown`. It never returns driver text
or a locator. NGINX health checks Control readiness as a dependency. Every
other long-running service remains database-free.

An unreadable Control file, wrong login/role, stopped PostgreSQL, stale
migration, or unsafe marker is not repaired by the online process. Restore the
correct file/role/database state or run the separately authorized one-shot
bootstrap operation, then recreate Control if its startup did not establish a
pool. Do not copy a locator into an environment variable or grant marker-table
`SELECT` as a workaround.

### Port conflict

The default binds `127.0.0.1:8080`. Stop the unrelated local listener or use a
separately reviewed override; do not publish an internal service directly as a
workaround.

### Site resolution and quota

Site creation fails safely when the owner-managed `max_sites` quota is reached,
including concurrent attempts. Operators may archive a site but there is no
online delete operation. Domain mappings are exact normalized host plus path
prefix pairs; resolution selects the unique longest matching prefix and only
returns active sites. The primary mapping cannot be removed until another
mapping is made primary. Local development additionally resolves only the
reserved `/s/<site-key>` form on `localhost`; callers cannot provide a site
UUID or revision override. Diagnose mapping data through the Control semantic
service and disposable integration tests—never by granting relation access to
an online role.

The Control site API is available only to an authenticated active Platform
Administrator. State changes require the session-bound CSRF proof. Archive is
idempotent, irreversible through the online API, and prevents every later
profile/domain mutation even if a caller retained a prior active context.
There is no online site deletion, DNS automation, invitation, custom-role
design, content/workspace/capability, or publication operation in this round.
The implemented membership UI manages existing UUIDs only.

The clean Compose verification creates two non-authenticatable OIDC fixture
accounts directly in its disposable database before setup, exercises visible
site/domain/membership governance plus crafted denials through NGINX, checks
persistence across stop/start, and removes the database volume during normal cleanup. These are test
harness records, not demo users, bootstrap seed data, or a user provisioning
mechanism. A collision or non-fresh installation state fails the smoke instead of
overwriting data.

## Verification

The destructive packaging smoke uses only a validated explicit project name:

```bash
sudo tools/compose/smoke.sh slaif007localtest
```

On a runner whose user can access the test Docker daemon, omit `sudo`. The
script verifies clean startup, routes and 404s, development-mode inventory,
runtime hardening, network and mount topology, the isolated Control mount and
read-denial boundary, empty-safe marker, exact login authority, Control
wrong-login/role/secret/marker/migration/database failure behavior, restart
idempotence, fail-closed bootstrap, Apache syntax, single
request-ID and CSP headers on page/API/404 responses, secret absence in
configuration/history/logs, the implemented visible governance lifecycle, and
exact-project cleanup. It also runs the real sandboxed product Chromium against
the COW preview, verifies signed results/private artifacts/restart retrieval,
hostile-token denial, worker-secret recovery, and continued public `QUEUED`
state. It does not claim durable dispatch, DB artifact registration, source
browsing, review, or publication execution.

## Supply-chain evidence

Run the complete build-only gate into a new temporary destination:

```bash
tools/supply_chain/run.sh /tmp/slaif-supply-chain-evidence
python -m tools.supply_chain.evidence validate-bundle \
  --evidence /tmp/slaif-supply-chain-evidence
```

The runner performs two clean application and project-image builds, creates
six SPDX and symbol-aware scan SBOMs, updates one public Grype database, scans
with network disabled, checks Critical and High evidence, rejects secret/host
markers, and writes `SHA256SUMS`. A pre-existing destination is rejected so an
old or partial bundle cannot be mistaken for current evidence.

Registry and database access are external availability dependencies of this
CI/build check, not runtime services. Exact image pulls and builds retry at most
three times with 30-second delays. A failed or stale vulnerability database is
a failed gate; operators must not substitute an old result. The narrowly
scoped Chrome exception is governed by the exact current exception file,
issue #67, and its 2026-09-04 removal deadline.

CI retains the checksummed directory for 14 days. It contains package and
vulnerability metadata and should remain CI-private even though it is scanned
for configured credential and host-path markers. It does not contain local
Compose secrets, database volumes, logs, site content, or browser artifacts.
See the [supply-chain guide](SUPPLY_CHAIN.md) for file layout, update procedure,
and limitations.

## Production boundary

This pre-alpha stack has backend login/setup routes, cookie emission, a setup
UI, and a clean local browser journey, but no service authentication, production TLS automation,
database-backed product use, backup automation, automated rotation, browser
sandbox/egress implementation, or publication path. The identity and
opaque-session schemas plus semantic consumers do not make local authentication
a proven human-facing journey.
Passing health and packaging checks proves only the stated deployment
skeleton. It is not a production readiness, security certification, or
feature-completeness claim.

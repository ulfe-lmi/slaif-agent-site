# Local skeleton operations

These commands operate the default Compose project in a local, non-production
environment. Use an explicit `-p NAME` for disposable tests so cleanup targets
cannot overlap an operator's persistent project.

## Lifecycle commands

```bash
docker compose up --build
docker compose up --build --wait
docker compose ps
docker compose logs --tail 200 nginx web control-api bootstrap postgres
docker compose down --remove-orphans
```

The final command preserves named data and secrets. `docker compose stop`
followed by `docker compose up --wait` reuses all four volumes and revalidates
the same generated credentials. Bootstrap must print exactly a safe result
shaped as:

```text
compose-bootstrap: OK revision=010_001 state=EMPTY_SAFE safe=true
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

This command is deliberately not wired into Compose startup. A freshly issued
or rotated plaintext is shown once on its own stdout line; the setup URL is a
separate line and never carries the token. Repeated default issuance returns
only expiry/generation facts and directs the operator to explicit rotation.
The atomic consumer now exists only as a typed Control operation exercised in
code/tests; no command or HTTP endpoint invokes it for an operator. Therefore
the token still cannot be used from the default stack or a browser. Store real
output only in an operator-approved secret channel and see
[installation setup](INSTALLATION_SETUP.md) for the exact boundary.

## Volumes, backup, and cleanup

The default named volumes are `postgres-data`, `media-data`, `local-secrets`,
and `control-secret`, prefixed by the Compose project name. PostgreSQL data,
master local secrets, and the derived Control secret must be backed up and
restored together. The media volume is only a placeholder in this slice; no
media behavior exists.

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
configuration/history/logs, and exact-project cleanup. It does not test product
workflows because they do not exist.

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
a failed gate; operators must not substitute an old result or exception.

CI retains the checksummed directory for 14 days. It contains package and
vulnerability metadata and should remain CI-private even though it is scanned
for configured credential and host-path markers. It does not contain local
Compose secrets, database volumes, logs, site content, or browser artifacts.
See the [supply-chain guide](SUPPLY_CHAIN.md) for file layout, update procedure,
and limitations.

## Production boundary

This pre-alpha stack has no usable login or setup route, cookie emission, setup
UI, service authentication, production TLS automation,
database-backed product use, backup automation, automated rotation, browser
sandbox/egress implementation, or publication path. The identity and
opaque-session schemas plus semantic consumers do not make local authentication
browser-usable; no HTTP route consumes them yet.
Passing health and packaging checks proves only the stated deployment
skeleton. It is not a production readiness, security certification, or
feature-completeness claim.

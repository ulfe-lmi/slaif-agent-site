# Local skeleton operations

These commands operate the default Compose project in a local, non-production
environment. Use an explicit `-p NAME` for disposable tests so cleanup targets
cannot overlap an operator's persistent project.

## Lifecycle commands

```bash
docker compose up --build
docker compose up --build --wait
docker compose ps
docker compose logs --tail 200 nginx web bootstrap postgres
docker compose down --remove-orphans
```

The final command preserves named data and secrets. `docker compose stop`
followed by `docker compose up --wait` reuses all three volumes and revalidates
the same generated credentials. Bootstrap must print exactly a safe result
shaped as:

```text
compose-bootstrap: OK revision=006_001 state=EMPTY_SAFE safe=true
```

Do not publish or archive complete logs without reviewing them. The
implementation suppresses database locators and password values, but logs are
still deployment-private operational data.

## Volumes, backup, and cleanup

The default named volumes are `postgres-data`, `media-data`, and
`local-secrets`, prefixed by the Compose project name. PostgreSQL data and local
secrets must be backed up and restored together. The media volume is only a
placeholder in this slice; no media behavior exists.

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
service's bounded log. Current long services have health-only behavior and no
database pool. A failed required upstream keeps NGINX from becoming healthy.

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
runtime hardening, network and mount topology, empty-safe marker, exact login
authority, restart idempotence, fail-closed bootstrap, Apache syntax, single
request-ID and CSP headers on page/API/404 responses, secret absence in
configuration/history/logs, and exact-project cleanup. It does not test product
workflows because they do not exist.

## Production boundary

This pre-alpha stack has no authentication, setup administrator, service
authentication, production TLS, online application database use, backup
automation, automated rotation, browser sandbox/egress implementation, or
publication path. Passing health and packaging checks proves only the stated
deployment skeleton. It is not a production readiness, security certification,
or feature-completeness claim.

# OAP Work Order — 007-a

## Objective

Create exactly one new GitHub pull request that turns the accepted language,
process, and database bootstrap foundations into the first complete
one-command deployment skeleton:

```bash
docker compose up --build
```

The default stack must generate local database credentials, initialize and
validate the accepted `EMPTY_SAFE` database baseline, start every planned
process placeholder behind explicit networks/credentials, expose only NGINX at
`http://localhost:8080`, and present an honest pre-alpha Next.js landing page.
Provide an equivalent Apache HTTP Server 2.4 reference adapter and packaging/
network/security tests.

This objective proves deployability and authority topology, not website
features. It must not implement authentication, first-user setup, sites,
workspaces, semantic routes, Playwright browsing, publication, or product data.

## GitHub objective state

- Numeric objective: `007`
- Execution round: `007-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective PR: N/A
- Required head branch: `oap/007-compose-edge-skeleton`
- Base branch: `main`
- Required PR title: `[OAP 007] Add one-command Compose and edge skeleton`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`

## Strategic context

Objectives `003`–`006` are accepted and merged. The repository now has:

- exact Python and Node toolchains;
- ten separately startable backend process identities;
- typed health/config/error/logging primitives;
- exact PostgreSQL privilege roles;
- a one-head Alembic baseline;
- explicit cluster-provisioner/setup-owner separation;
- public-foundation COW deployment and safe `PENDING`/`EMPTY_SAFE`/
  `HARDENED` readiness semantics.

Nothing packages those pieces into OCI images or connects them through the
reference deployment. Architecture Sections 6.2, 11, 13, 45–47, Appendix F,
and Phase 1 require a clone-and-run skeleton before identity/product work.

At activation, remote `main` is:

```text
ad1f5253aaaf1e0905043d58589c8563950ccd3e
```

Objective `006` PR `#9` is merged with its complete two-round transcript.
`oap/active` currently contains the merged identifier `006-b`; this activation
changes it to `007-a`. Unrelated Dependabot PR `#7` remains open and PR `#5`
remains closed without merge. Do not act on either.

The current official npm releases selected for the minimal web surface are:

```text
next==16.3.1
react==19.2.8
react-dom==19.2.8
@types/react==19.2.18
@types/react-dom==19.2.4
```

They are MIT packages and compatible with the existing Node 24/pnpm 11.22.0
baseline. Reverify registry availability, peer compatibility, integrity, and
license at execution time. Do not silently substitute versions or add
Tailwind, Puck, shadcn/ui, Radix, Playwright, telemetry, analytics, or a hosted
SDK in this deployment slice.

## Allowed path scope

Keep changes within these paths/families plus the required OAP transcript:

```text
.dockerignore
.github/workflows/ci.yml
.gitignore
AGENTS.md
CONTRIBUTING.md
README.md
apps/web/**
compose.yaml
docs/CONFIGURATION.md
docs/DATABASE_BOOTSTRAP.md
docs/DATABASE_ROLES.md
docs/DEPLOYMENT.md
docs/OPERATIONS.md
docs/SERVICE_AUTHORITY.md
infra/apache/**
infra/nginx/**
package.json
pnpm-lock.yaml
pnpm-workspace.yaml
services/backend/Dockerfile
services/backend/src/slaif_agent_site/bootstrap/**
services/backend/src/slaif_agent_site/db/roles.py
services/backend/tests/integration/**
services/backend/tests/unit/**
services/browser-worker/**
tests/packaging/**
tests/repository/test_repository_policy.py
tools/check_repository.py
tools/compose/**
tools/local_secrets/**
tsconfig.json
uv.lock
pyproject.toml
oap/active
oap/orders/007-a-compose-oci-edge-one-command-skeleton.md
oap/reports/007-a-compose-oci-edge-one-command-skeleton.md
```

Do not edit `ARCHITECTURE.md`, `SECURITY.md`, `NOTICE`, either OAP protocol,
accepted migration/readiness/privilege semantics except the narrowly required
local login-principal provisioning extension, foundation adapters, existing
contract packages, or prior OAP artifacts. No environment/secret/generated
file may be committed. If an indispensable path is missing, report it rather
than expanding scope silently.

## Scope and requirements

### A. Exact default service inventory

The default Compose project must include these architecture processes, plus
one bounded local-secret initializer:

```text
secrets-init
postgres
bootstrap
control-api
editor-api
agent-api
render-api
mcp-adapter
media-service
review-worker
scheduler
media-gc
browser-worker
web
nginx
```

Use the accepted backend process commands. `bootstrap` is one-shot and must
complete the role/principal provisioning, migration, public foundation
deployment, privilege reconciliation, and `EMPTY_SAFE safe=true` validation
before dependent services can start. Review/scheduler/GC remain honest idle
`NOT_IMPLEMENTED` processes. Six backend HTTP services expose health only.

Do not combine processes into one all-authority container and do not make
bootstrap, PostgreSQL, Render, browser worker, or any worker externally
reachable.

### B. Generated local database secrets and login principals

One command must work without a checked-in `.env`, default database password,
or manual secret-generation step.

- Add a minimal, standard-library-only one-shot initializer that writes
  cryptographically random local database passwords and DSN files to a named
  private volume on first use and reuses them idempotently on restart.
- Do not print secret bytes, put them in Compose environment values, bake them
  into images/layers, expose them through health output, or copy them to a host
  bind mount.
- Use restrictive ownership/modes and mount the secret volume only into the
  initializer, PostgreSQL where its administrator password file is required,
  and the one-shot bootstrap path. Long-running services still have no online
  DB pool and must not receive owner/provisioner DSNs in this objective.
- Production/institutional deployment must be able to replace this local
  generator with externally managed secret files without changing the product
  role model.

Extend the explicit one-shot provisioning boundary to create distinct local
login principals, each granted exactly one accepted password-free privilege
role:

```text
slaif_bootstrap_login   -> slaif_owner
slaif_control_login     -> slaif_control
slaif_editor_login      -> slaif_editor_runtime
slaif_agent_login       -> slaif_agent_runtime
slaif_public_login      -> slaif_public_reader
slaif_preview_login     -> slaif_preview_reader
slaif_reviewer_login    -> slaif_reviewer
slaif_scheduler_login   -> slaif_scheduler
slaif_media_login       -> slaif_media
slaif_gc_login          -> slaif_gc
```

Names may be represented through one immutable manifest, but not made caller-
selectable at runtime. Every login is non-superuser, non-createdb,
non-createrole, non-replication, and non-bypass-RLS; it has only the one role
membership. Only the one-shot bootstrap login/DSN is used after provisioning
in this PR. Service DSNs may be generated for future wiring but are not mounted
into services that have no implemented pool.

The database administrator remains separate and is used only by PostgreSQL
initialization/explicit provision. No permanent application process receives
it. Use parameter-safe password handling; never interpolate an unescaped
secret into shell output, logs, reports, or a SQL identifier.

### C. Backend OCI image

Create one multi-stage backend image used with different commands for the ten
Python processes.

- Use Python 3.12, exact uv 0.12.5, `uv.lock`, and a frozen production install.
- Resolve every base/tool image to a reviewed immutable digest while retaining
  a readable version tag/comment. Report repository, version, digest, license,
  platform support, and update procedure.
- Build/install the qualified project wheel or frozen environment without
  development/test tools in the runtime stage.
- Run as a non-root application UID/GID with a read-only root filesystem,
  bounded writable tmpfs where required, dropped Linux capabilities, and
  `no-new-privileges` where Compose/runtime supports them.
- Use one command per process; no shell supervisor, Docker socket, repository
  bind mount, or setup-owner secret in long-running containers.
- Container imports/startup must create no DB pool because that behavior is
  still deferred.

### D. Minimal Next.js web skeleton

Add `apps/web` as a private pnpm workspace using only the exact selected
Next.js/React dependencies and the existing exact TypeScript/toolchain.

Implement:

- one responsive, accessible pre-alpha landing page using the existing SLAIF
  design/logo asset and plain project-owned CSS;
- clear implemented/deferred wording and links to repository documentation;
- internal `/health/live` and `/health/ready` route handlers with stable,
  bounded responses and no product/database claim;
- Next standalone production output and a multi-stage, digest-pinned Node 24
  image running as non-root;
- no external font, telemetry, analytics, image optimizer network dependency,
  server action, authentication, admin/setup/product route, Puck, or hosted
  integration.

The page is a deployment skeleton status surface, not the contractual first-
run Platform Administrator flow scheduled for objective `009`.

### E. Browser-worker placeholder

Add a private TypeScript `services/browser-worker` workspace and a minimal
non-root OCI process with only bounded internal liveness/readiness endpoints.

- Use Node's standard HTTP/runtime surface where practical; add no Playwright
  or general browser/MCP dependency yet.
- Expose no browser command, arbitrary URL, evaluation, file, artifact, DB,
  content-write, reviewer, Docker-socket, or host-mount behavior.
- Bind only inside its isolated Compose network; NGINX must not route it.
- State explicitly that Playwright, browser binaries, sandbox/egress policy,
  and visual tools remain unimplemented until their dedicated objective.

### F. Compose network and authority topology

Use named networks that make future intended paths visible without granting
credentials merely by network membership. At minimum separate:

```text
edge/presentation     NGINX to Web and externally routed API processes
application/internal Web to Render; Agent to browser-worker as needed
database/internal     only processes whose architecture may later use DB
browser/internal      browser-worker and the narrow requesting service only
```

The browser worker must have no route to PostgreSQL, bootstrap, reviewer
control, Docker socket, host filesystem, or unrestricted host network. Web and
MCP have no database network/credential. NGINX has no database/browser-worker
network. Do not use `network_mode: host`, `privileged`, broad host mounts, or
the Docker socket.

Only NGINX publishes a host port, exactly loopback/all-local `8080` according
to documented demo behavior. PostgreSQL and every internal/listening service
may use `expose`/container ports but no other `ports` mapping. Use named data,
media-placeholder, and secret volumes; no source-code bind mount in the
default profile.

Add health checks and long-form `depends_on` conditions so:

1. secret initialization completes;
2. PostgreSQL becomes healthy;
3. bootstrap completes successfully with `EMPTY_SAFE safe=true` and a live
   validation recheck;
4. service health becomes available;
5. NGINX starts only when its upstream skeletons are healthy.

A failed role grant, migration, COW deployment, privilege check, or marker
validation must make bootstrap fail nonzero and prevent NGINX/default-stack
readiness. Restart remains idempotent and preserves PostgreSQL/media data and
generated secrets.

### G. NGINX Open Source reference edge

Add a version/digest-pinned NGINX Open Source runtime and complete local
routing for current skeleton endpoints:

```text
/                       -> web
/api/control/           -> control-api, prefix stripped
/api/editor/            -> editor-api, prefix stripped
/api/agent/             -> agent-api, prefix stripped
/mcp/                   -> mcp-adapter, prefix stripped
/media/                 -> media-service, prefix stripped
```

Render and browser worker remain internal-only. Configure request IDs,
forwarded host/proto/address, bounded body/timeouts, streaming-compatible
proxy settings where appropriate, compression, and baseline security headers.
Do not implement authentication, site/capability/session selection,
publication, preview policy, or product authorization in NGINX.

Use a non-root listen port inside the container if needed and map host 8080 to
it. Unknown product/API paths must remain honest 404 responses rather than a
fake success page. Do not expose NGINX status/admin controls publicly.

### H. Apache HTTP Server 2.4 alternative

Provide a documented, syntax-tested Apache 2.4 example using standard
open-source modules and the same route/prefix/header/streaming contract. It is
not a default Compose service and must not contain security semantics absent
from the application. Include exact module requirements, TLS placeholder
guidance, and trusted-proxy cautions without shipping a certificate/key.

### I. Packaging and topology tests

Add deterministic tests/scripts that prove, from a clean disposable Compose
project:

- `docker compose config` succeeds without `.env` or host-specific paths;
- every required image builds from frozen locks and reviewed base digests;
- `docker compose up --build --wait` (or equivalent bounded sequence) reaches
  healthy state from empty named volumes;
- `http://localhost:8080/` renders the honest landing surface;
- all externally routed health paths work and product paths remain absent;
- Render, browser worker, PostgreSQL, workers, and bootstrap are not externally
  reachable and only 8080 is published;
- container network memberships exactly match policy and browser has no
  database/host/Docker-socket path;
- process users, read-only filesystems, cap drops, security options, tmpfs, and
  secret/data mounts match the declared hardening profile;
- bootstrap marker is `EMPTY_SAFE safe=true`, exact role/login membership is
  present, service credentials are distinct, and no long-running container has
  admin/owner secret mounts or variables;
- startup fails closed under a deliberately broken bootstrap privilege/secret
  fixture and NGINX never becomes ready;
- stop/start is idempotent, then a fully bounded destructive test cleanup uses
  only its exact Compose project/volumes;
- NGINX and Apache syntax and route-equivalence policy pass;
- image history/config, tracked files, rendered Compose config, and logs contain
  no generated password or raw DSN.

Tests must use a unique project name and exact cleanup targets. They may not
delete unrelated Docker resources, volumes, or networks.

### J. CI and durable documentation

Extend CI with a bounded Compose/edge packaging job on Ubuntu. Keep all
existing Python 3.12–14, PostgreSQL 14–18, Node, repository, Markdown,
Mermaid, dependency review, and CodeQL checks. Do not replace matrix evidence
with the Compose smoke.

Add `docs/DEPLOYMENT.md` and `docs/OPERATIONS.md` covering:

- exact prerequisites and one-command startup/shutdown/status/log commands;
- first/returning startup sequence and expected URLs/status;
- service/image/network/volume/credential inventory;
- local secret persistence, replacement, backup, rotation limitation, and safe
  exact-project cleanup;
- NGINX default and Apache alternative;
- failure diagnosis for secret init, PostgreSQL, bootstrap, upstream health,
  and port conflicts;
- what is implemented versus deferred;
- why current container/network/credential boundaries are defense in depth and
  not a production certification.

Update README, configuration, database/bootstrap/role/service-authority,
AGENTS, and CONTRIBUTING only as needed. Continue to label the project
pre-alpha and state that first-user setup/auth/site/product behavior is absent.

## Explicit non-goals

- No permanent or demo human administrator, installation-state/user/session/
  site/domain/membership/workspace/capability/content/job/media/browser data,
  product migration, route, API, MCP tool, publication, review action, or UI.
- No Puck, Tailwind, shadcn/ui, Radix, Playwright/browser binaries, raw browser
  endpoint, source browsing, E2E product workflow, or responsive-product claim.
- No production TLS automation, DNS, wildcard host, ingress controller,
  Kubernetes, Helm, Swarm, NGINX Plus, Apache as default, Redis/RabbitMQ/Kafka,
  hosted DB/object/browser/identity service, telemetry, analytics, or cloud SDK.
- No production release, SBOM/vulnerability-policy completion (objective 008),
  default password, checked-in secret, host Docker socket, privileged container,
  or broad host mount.
- No action on PR `#5`/`#7`, second objective PR, merge, auto-merge, release,
  tag, deployment, issue, or GitHub setting change.

## Acceptance criteria

1. Exactly one non-draft objective-007 PR exists with required title/branch/
   base and complete versioned OAP transcript; the coding agent does not merge.
2. A clean Linux clone with a supported OCI/Compose runtime reaches a healthy
   default skeleton through `docker compose up --build` with no `.env`, manual
   package install, hosted account, API key, or manual secret generation.
3. Only NGINX publishes host port 8080; PostgreSQL, Render, browser worker,
   bootstrap, workers, and direct APIs are externally unreachable, and network
   memberships preserve DB/browser/edge trust boundaries.
4. Local secrets are high entropy, persistent/idempotent, file-backed,
   unlogged, absent from images/config/environment/Git, and mounted only where
   currently required. Exact distinct login principals each hold one privilege
   role; no long-running service receives owner/provisioner authority.
5. Bootstrap runs explicitly once per startup dependency chain, reaches and
   live-validates `EMPTY_SAFE safe=true`, and any migration/COW/role/privilege/
   secret failure prevents NGINX/default readiness.
6. One digest-pinned non-root backend image starts all ten correct commands;
   one digest-pinned standalone Next image serves an honest accessible landing
   page and health; one isolated browser-worker placeholder serves health only
   with no Playwright/DB/browser command authority.
7. NGINX Open Source routing, forwarded/request headers, limits, streaming,
   compression, security headers, and 404 behavior pass through the public
   endpoint; the Apache 2.4 example is syntax-tested and contract-equivalent.
8. Containers use reviewed base images, frozen Python/Node installs, non-root/
   read-only/cap-drop/no-new-privileges controls where technically applicable,
   named volumes, health checks, and no Docker socket/source bind/host network.
9. Clean start, negative bootstrap, published-port/network/secret inspection,
   restart/idempotence, bounded cleanup, NGINX/Apache syntax, and package tests
   pass locally and in CI without skips.
10. Existing dependency/quality/foundation/PostgreSQL/Node/docs/CodeQL gates
    remain green; exact new dependency versions/licenses/integrities and base
    image tags/digests are reported with zero open CodeQL alert.
11. Documentation accurately describes the deployable skeleton, credentials,
    networks, operations, limitations, and deferred product behavior without a
    production-ready or feature-complete claim.
12. `oap/active` is `007-a`, unique order/report correlation holds, prior OAP
    artifacts remain immutable, and final remote head is the report-only
    `SELF` commit whose first parent is the reported implementation head.

## Verification required

Run and report the existing complete frozen Python/Node/repository/Markdown/
Mermaid/build/PostgreSQL gates plus at least:

```bash
docker compose version
docker compose config --quiet
docker compose build --pull
docker compose up --build --wait
docker compose ps
curl --fail --show-error http://localhost:8080/
curl --fail --show-error http://localhost:8080/api/control/health/live
curl --fail --show-error http://localhost:8080/api/editor/health/ready
curl --fail --show-error http://localhost:8080/api/agent/health/live
curl --fail --show-error http://localhost:8080/mcp/health/ready
curl --fail --show-error http://localhost:8080/media/health/live
docker compose down --remove-orphans
```

Use an exact unique Compose project for destructive test teardown and include
`--volumes` only for the explicitly disposable clean-start/failure fixture, not
the operator's normal persistent stack.

Also report:

- service/image digest, user, command, health, restart, filesystem, capability,
  security-option, network, port, mount, and secret inventory;
- generated file modes/owners and role/login/marker truth without secret
  values;
- host published-port and negative direct-connect evidence;
- browser network/credential/host/Docker-socket negative evidence;
- NGINX config test and route/header/404 checks;
- Apache image/config syntax test and route-equivalence static check;
- clean first start, unchanged-volume restart, deliberate bootstrap failure,
  recovery, and bounded cleanup;
- Next/browser package build/type/lint/test and runtime health;
- image/config/history/log/Git secret scans;
- exact npm dependency integrity/license and OCI base digest provenance;
- PR identity/scope, prior transcript/protected hashes, all final checks,
  CodeQL alerts, report-only parent/delta, and synchronized clean worktree.

A pending/skipped packaging or negative security test is not passing evidence.
Product auth/site/workspace/content/browser/publication behavior is
`NOT IMPLEMENTED/NOT RUN`, not a success claim.

## Safety / security constraints

- All databases, passwords, principals, containers, networks, and volumes used
  for tests are fake and disposable. Never access production or unrelated
  Docker resources.
- Resolve destructive Compose project/volume targets exactly and never use a
  broad prune command.
- Do not log/echo generated secret values or include them in the OAP report.
- Fail closed rather than broadening a network, grant, mount, listener,
  filesystem, capability, or container privilege.
- Base-image download is a build dependency, not permission to add an
  account-bound runtime service.

## Local execution capability

Routine Docker/Compose, image, package, Node/Python, PostgreSQL, port,
filesystem-permission, Apache/NGINX, test, and CI diagnosis belongs to the
coding agent in the disposable VM. Passwordless `sudo` is available. Do not
transfer ordinary setup work to the human or strategic model.

## GitHub workflow

Create `oap/007-compose-edge-skeleton` from current remote `main`. Preserve
the activated order and pointer bytes, implement only this deployment
skeleton, run all gates, push, and create exactly one non-draft PR with the
required title. Repair safe in-scope failures on the same PR. Never touch PR
`#5`/`#7`, create another objective PR, merge, enable auto-merge, deploy, or
choose `008-a`.

## Required report

Atomically publish exactly:

```text
oap/reports/007-a-compose-oci-edge-one-command-skeleton.md
```

Use protocol 1.2 in full. Include exact dependency and base-image provenance;
service/network/port/user/mount/secret/role inventories; bootstrap marker and
failure behavior; clean/restart/negative/cleanup evidence; edge syntax/routes/
headers/404s; all local and GitHub tests/checks/alerts; deferred behavior;
scope/security/no-merge confirmations; literal implementation head; and
`Report publication commit: SELF`. Push and verify the report-only head and
parent before FIFO `OK`.

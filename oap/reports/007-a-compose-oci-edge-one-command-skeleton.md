# OAP Coding-Agent Report — 007-a

## Work order

- Identifier: 007-a
- Work-order file:
  `oap/orders/007-a-compose-oci-edge-one-command-skeleton.md`
- Numeric objective: 007
- PR mode: CREATED_NEW_PR
- Report drafted: 2026-08-17T15:57:54Z

## Status

COMPLETE

## Executive summary

Added the first clone-and-run deployment skeleton for SLAIF Agent-Site. The
default Compose graph has exactly 15 services and starts from a clean clone
with `docker compose up --build`, without an `.env`, hosted account, API key,
manual package installation, or manual credential generation. Only NGINX
publishes loopback port 8080. Database, browser, application, and edge network
memberships preserve the planned trust boundaries.

The one-shot initializer creates 23 persistent, file-backed local credential
artifacts without printing their values. The one-shot bootstrap creates ten
fixed login principals, gives each exactly one privilege-role membership,
runs the existing migration/COW/privilege sequence, and independently proves
`revision=006_001 state=EMPTY_SAFE safe=true` before any online process or
NGINX can become ready. A failed bootstrap prevents the public edge from
starting.

The stack uses digest-pinned OCI inputs, frozen Python and Node installs,
non-root product images, read-only filesystems, dropped capabilities,
`no-new-privileges`, narrow tmpfs mounts, named volumes, and no source bind,
Docker socket, host network, or unplanned host port. It includes an honest,
accessible standalone Next.js status page, a health-only browser-worker
placeholder, NGINX Open Source routing, and a syntax-tested Apache 2.4
alternative.

All local gates and all 19 GitHub checks passed for implementation head
`94702b5420b15be0a63171d678c3de56f8a3a31f`. Initial GitHub runs encountered
external action-download HTTP 429/503 failures. The first CodeQL run also
identified world traversal on the secret directory. The implementation was
hardened from `0711` to `0710` with dedicated supplemental GID 10002, runtime
policy tests now prove that only PostgreSQL/bootstrap can traverse it and an
unrelated UID cannot read a secret, the CodeQL thread is resolved, and there
are zero open repository or branch code-scanning alerts.

This is deliberately a deployment and authority skeleton. Product identity,
sites, workspaces, editing, browser automation, review, publication, and
external side effects are NOT IMPLEMENTED and NOT RUN.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: 10
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/10>
- PR state at report time: OPEN
- PR readiness at report time: non-draft
- PR merge state at report time: CLEAN and MERGEABLE
- Base branch: `main`
- Head branch: `oap/007-compose-edge-skeleton`
- Starting authoritative remote/base SHA:
  `ad1f5253aaaf1e0905043d58589c8563950ccd3e`
- Implementation head SHA: `94702b5420b15be0a63171d678c3de56f8a3a31f`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal SHA derived from
  GitHub)
- Implementation commits pushed before the report commit:
  - `3e26240c23c7a29b1898abdd5123f91704d797fd` —
    `feat: add Compose and edge deployment skeleton`
  - `94702b5420b15be0a63171d678c3de56f8a3a31f` —
    `fix: restrict local secret directory traversal`
- Report commit first parent: same as Implementation head SHA
- Created a new PR this turn: yes
- Amended an existing objective PR mode this turn: no
- Other objective-007 PRs found: none
- Merge performed: NO
- Auto-merge enabled: NO
- PR #5 modified: NO; it was already closed without merge at
  `2026-08-17T12:09:30Z`.
- PR #7 modified: NO. The work order described it as open, but authoritative
  GitHub state showed it already closed without merge at
  `2026-08-17T12:44:52Z`; no action was taken.

## Changes made

- Added `compose.yaml` with the exact initializer, PostgreSQL, bootstrap, six
  backend HTTP, three backend worker, browser-worker, Web, and NGINX process
  identities.
- Added a network-disabled, idempotent local secret initializer using
  cryptographic randomness, exclusive file creation, fixed names, restrictive
  ownership/modes, directory/file fsync, and stable secret-free output.
- Added fixed local PostgreSQL login provisioning. Trusted code selects all
  login names and grants; password values are parameter-bound and quoted by
  PostgreSQL before use in fixed `ALTER ROLE` statements.
- Added role/login reconciliation for attributes, outgoing memberships,
  incoming delegation edges, sole expected grants, and absent admin options;
  bootstrap performs an independent final login and readiness validation.
- Added digest-pinned multi-stage backend and standalone Next.js images,
  plus minimal browser-worker, NGINX, and Apache reference images.
- Added an honest responsive status page, process-only health endpoints,
  app-local TypeScript/TSX linting, frozen build/test coverage, and disabled
  Next telemetry/image optimization behavior that would require an unused
  native optional dependency.
- Added NGINX prefix routing, request/forwarded headers, request IDs, bounded
  limits/timeouts, streaming-compatible proxy behavior, compression, security
  response headers, and natural 404 behavior. Added a statically equivalent,
  syntax-tested Apache 2.4 adapter.
- Added static and live Compose topology verification plus a clean-start smoke
  covering service inventory, image/user/command/health/restart/security,
  networks, ports, mounts, secret facts, roles, edge routes, restart,
  deliberate bootstrap failure, scans, and exact cleanup.
- Added a bounded Compose CI job and packaging tests while retaining every
  existing repository, Python, PostgreSQL, Node, Markdown, Mermaid,
  dependency-review, and CodeQL gate.
- Added deployment and operations guides and updated durable configuration,
  database, authority, contribution, and root documentation without making a
  production-ready or feature-complete claim.

## Files changed

- Root/build/workflow: `.dockerignore`, `.github/workflows/ci.yml`,
  `.gitignore`, `compose.yaml`, `package.json`, `pnpm-lock.yaml`, and
  `pnpm-workspace.yaml`.
- Web: `apps/web/Dockerfile`, `apps/web/eslint.config.mjs`,
  `apps/web/next-env.d.ts`, `apps/web/next.config.mjs`,
  `apps/web/package.json`, `apps/web/tsconfig.json`,
  `apps/web/app/layout.tsx`, `apps/web/app/page.tsx`,
  `apps/web/app/styles.css`, `apps/web/app/health/live/route.ts`,
  `apps/web/app/health/ready/route.ts`, and
  `apps/web/tests/surface.test.mjs`.
- Backend: `services/backend/Dockerfile`,
  `services/backend/src/slaif_agent_site/bootstrap/__main__.py`,
  `services/backend/src/slaif_agent_site/bootstrap/config.py`,
  `services/backend/src/slaif_agent_site/bootstrap/service.py`,
  `services/backend/src/slaif_agent_site/db/roles.py`,
  `services/backend/tests/integration/test_database_bootstrap.py`,
  `services/backend/tests/unit/test_config.py`, and
  `services/backend/tests/unit/test_local_roles.py`.
- Browser placeholder: `services/browser-worker/Dockerfile`,
  `services/browser-worker/package.json`,
  `services/browser-worker/tsconfig.json`,
  `services/browser-worker/src/responses.ts`,
  `services/browser-worker/src/server.ts`, and
  `services/browser-worker/tests/health.test.mjs`.
- Edge: `infra/nginx/Dockerfile`, `infra/nginx/nginx.conf`,
  `infra/apache/Dockerfile`, and `infra/apache/slaif-agent-site.conf`.
- Deployment tooling/tests: `tools/local_secrets/initialize.py`,
  `tools/compose/verify.py`, `tools/compose/smoke.sh`,
  `tests/packaging/compose.broken-bootstrap.yaml`,
  `tests/packaging/test_compose_policy.py`,
  `tests/packaging/test_edge_contract.py`,
  `tests/packaging/test_local_secrets.py`, and
  `tests/packaging/test_oci_contract.py`.
- Repository policy: `tools/check_repository.py` and
  `tests/repository/test_repository_policy.py`.
- Documentation: `README.md`, `CONTRIBUTING.md`,
  `docs/CONFIGURATION.md`, `docs/DATABASE_BOOTSTRAP.md`,
  `docs/DATABASE_ROLES.md`, `docs/DEPLOYMENT.md`,
  `docs/OPERATIONS.md`, and `docs/SERVICE_AUTHORITY.md`.
- Strategic transcript, preserved exactly:
  `oap/active` and
  `oap/orders/007-a-compose-oci-edge-one-command-skeleton.md`.
- This SELF publication adds only
  `oap/reports/007-a-compose-oci-edge-one-command-skeleton.md`.

## Runtime service, network, port, and mount inventory

Every service has `read_only: true`, `cap_drop: [ALL]`, and
`no-new-privileges:true`. Every long-running service uses
`restart: unless-stopped` and a health check; `secrets-init` and `bootstrap`
are one-shot `restart: no` dependencies that must complete successfully.
All processes needing scratch space receive bounded `noexec`, `nosuid`,
`nodev` tmpfs storage. No service is privileged or uses a bind mount, Docker
socket, or host network.

| Service | Runtime user and command | Networks | Named mounts / host port |
| --- | --- | --- | --- |
| `secrets-init` | `0:0`; `python /opt/slaif/bin/initialize-local-secrets.py --directory /run/slaif-secrets`; only `CHOWN,DAC_READ_SEARCH` re-added | network mode `none` | `local-secrets:/run/slaif-secrets` RW; no port |
| `postgres` | official entrypoint starts with image default authority and drops the server to PostgreSQL UID 999; `postgres`; only `CHOWN,DAC_OVERRIDE,FOWNER,SETGID,SETUID` re-added; supplemental GID 10002 | database | `postgres-data:/var/lib/postgresql/data` RW; `local-secrets:/run/slaif-secrets` RO; no host port |
| `bootstrap` | `10001:10001`; `python -m slaif_agent_site.bootstrap compose`; supplemental GID 10002 | database | `local-secrets:/run/slaif-secrets` RO; no port |
| `control-api` | `10001:10001`; `python -m slaif_agent_site.control_api` | database, edge | none; internal expose only |
| `editor-api` | `10001:10001`; `python -m slaif_agent_site.editor_api` | database, edge | none; internal expose only |
| `agent-api` | `10001:10001`; `python -m slaif_agent_site.agent_api` | browser, database, edge | none; internal expose only |
| `render-api` | `10001:10001`; `python -m slaif_agent_site.render_api` | application, database | none; internal expose only |
| `mcp-adapter` | `10001:10001`; `python -m slaif_agent_site.mcp_adapter` | application, edge | none; internal expose only |
| `media-service` | `10001:10001`; `python -m slaif_agent_site.media_service` | database, edge | `media-data:/var/lib/slaif/media` RW; no host port |
| `review-worker` | `10001:10001`; `python -m slaif_agent_site.review_worker` | database | none; no port |
| `scheduler` | `10001:10001`; `python -m slaif_agent_site.scheduler` | database | none; no port |
| `media-gc` | `10001:10001`; `python -m slaif_agent_site.media_gc` | database | `media-data:/var/lib/slaif/media` RW; no port |
| `browser-worker` | `10001:10001`; image CMD `node src/server.ts` | browser only | none; internal expose only |
| `web` | `10001:10001`; image CMD `node apps/web/server.js` | application, edge | none; internal expose only |
| `nginx` | `101:101`; `nginx -g daemon off;` | edge only | no mount; sole host binding `127.0.0.1:8080:8080/tcp` |

Network memberships were inspected from live Docker objects. `edge` is the
only non-internal network. `application`, `database`, and `browser` are
`internal: true`. Docker `PortBindings` was empty for every container except
NGINX, proving negative direct-host reachability independently of Compose
source. The browser worker had only the browser network, no secret/DB/media
mount or credential environment, no host port, no bind/Docker-socket path,
and no browser/Playwright command authority.

## OCI and package provenance

The final locally built/tested image IDs were:

| Image | Local immutable image ID | Config user / default command |
| --- | --- | --- |
| `slaif-agent-site-backend:local` | `sha256:d217404ffd5411a984e1b69edd206b9689280ec5a25b52b6ce9ec57bb5f5cd95` | `10001:10001`; Control API default, overridden by trusted Compose service definitions |
| `slaif-agent-site-browser-worker:local` | `sha256:833f87732b94c828c849feadf21c27a551ae943f730f653860daa5450a3f89ed` | `10001:10001`; `node src/server.ts` |
| `slaif-agent-site-web:local` | `sha256:efbbc1743727776e5aafda33d071c6491303a2c11406e8a056c383c8c5bf2b18` | `10001:10001`; `node apps/web/server.js` |
| `slaif-agent-site-nginx:local` | `sha256:d516855244a077409cc4d858a8ba2a496012ca34811a585307b665fc0c930ded` | `101:101`; `nginx -g daemon off;` |
| `slaif-agent-site-apache:test` | `sha256:2086f7faeb1d76bce63aafd8282f99b3ee4c7811152219ce77fa84ee82be6056` | official image default; test-only `httpd-foreground` image |
| PostgreSQL | `sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941` | official entrypoint; `postgres` |

All build inputs retain readable versions beside immutable top-level digests:

| Repository/version | Digest | License / reviewed platform basis |
| --- | --- | --- |
| `docker.io/library/python:3.12.12-slim-bookworm` | `sha256:593bd06efe90efa80dc4eee3948be7c0fde4134606dd40d8dd8dbcade98e669c` | PSF; official amd64/arm64 and additional targets |
| `ghcr.io/astral-sh/uv:0.12.5` | `sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` | Apache-2.0 OR MIT; amd64/arm64 |
| `docker.io/library/node:24.14.1-bookworm-slim` | `sha256:b506e7321f176aae77317f99d67a24b272c1f09f1d10f1761f2773447d8da26c` | MIT; amd64/arm64/ppc64le/s390x |
| `docker.io/library/postgres:18.6-trixie` | `sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941` | PostgreSQL; official multi-platform index |
| `docker.io/library/nginx:1.29.6-alpine3.23` | `sha256:f46cb72c7df02710e693e863a983ac42f6a9579058a59a35f1ae36c9958e4ce0` | two-clause BSD; official multi-platform index |
| `docker.io/library/httpd:2.4.66-alpine3.23` | `sha256:968c8b4098fcecb473762b45f6c541a3b2b2cfab2caccb1edbd2cece071ef160` | Apache-2.0; official multi-platform index |

The new exact Web dependencies and lockfile integrity values are:

| Package | License | npm integrity |
| --- | --- | --- |
| `next@16.3.1` | MIT | `sha512-hsAp0i7Rh+/dhe7DGIeN2YlpLM1DP4MNxti9EtDMtqcO612X81MvvEj388/oTce9U1EcEIOWDlGq0zRwrBKvuA==` |
| `react@19.2.8` | MIT | `sha512-PWaYA1L/q9u2u7xYQi+Y3L3Yfnie7XyLeaJICV1MGD6LprsBxcAqGjYyr0eY3p+QdsA+x/Irkt4Qif8D63+Sbw==` |
| `react-dom@19.2.8` | MIT | `sha512-rVprimfGBG3DR+Tq0IQG2DT5PxKth1WIGDmj5yPmlzr4YBe7uyE+Du4oVqTDXZSHGGGXRtTJEGSSePyQCMBglQ==` |
| `@types/react@19.2.18` | MIT | `sha512-AnzbBERsrLKtk2XSfTbYRLjQPdy116Sty4q+T+Bp3IC4l6jNBvreVPAHmpq9qhXQM7CXZPjLVmGMw9sy+hxQ3w==` |
| `@types/react-dom@19.2.4` | MIT | `sha512-Bsc+QHgp+P/F02XDzNCY9jnZNCUuLki36KT7VKrTXXLdHf+vHMNZnW1rVu5DNW/rCK+fya3DATySbLM4yhtKUw==` |

The frozen Node inventory had 307 packages in ten workspaces and only the
approved `0BSD`, `Apache-2.0`, `BlueOak-1.0.0`, `BSD-2-Clause`,
`BSD-3-Clause`, `CC-BY-4.0`, `ISC`, and `MIT` groups. `caniuse-lite` is
attribution-bearing CC-BY-4.0 compatibility data and `tslib` is 0BSD. The
denied unused `sharp` optional dependency and LGPL libvips bundle were absent.
Playwright remained optional peer metadata only and was not installed. The
Python foundation remains the unchanged registry dependency
`agent-cow-postgresql==0.2.0` with exact frozen hashes.

## Secret, role, and bootstrap inventory

The private named volume contains exactly 23 files, all mode `0400`, beneath a
root-owned directory mode `0710`, group 10002:

- one `postgres-password`, owned by UID 999;
- ten distinct `login-*-password` files, owned by UID 10001;
- `provisioner-dsn` and `owner-dsn`, owned by UID 10001;
- nine future `service-*-dsn` files, owned by UID 10001; and
- one `.initialized-v1` marker, owned by UID 0.

The eleven generated password values were proven pairwise distinct and at
least 43 ASCII characters, but no value, DSN, or fingerprint of a value is
included here. Only initializer, PostgreSQL, and bootstrap mount the volume.
PostgreSQL and bootstrap alone receive supplemental GID 10002; a live
unrelated UID 10003 read attempt failed. No long-running service receives a
DSN or provisioner/owner authority.

The fixed login-to-privilege mapping is:

| Login | Sole privilege role |
| --- | --- |
| `slaif_bootstrap_login` | `slaif_owner` |
| `slaif_control_login` | `slaif_control` |
| `slaif_editor_login` | `slaif_editor_runtime` |
| `slaif_agent_login` | `slaif_agent_runtime` |
| `slaif_public_login` | `slaif_public_reader` |
| `slaif_preview_login` | `slaif_preview_reader` |
| `slaif_reviewer_login` | `slaif_reviewer` |
| `slaif_scheduler_login` | `slaif_scheduler` |
| `slaif_media_login` | `slaif_media` |
| `slaif_gc_login` | `slaif_gc` |

Every login was live-authenticated in integration tests and reconciled to
`LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT NOREPLICATION
NOBYPASSRLS`, exactly one membership without admin option, and no delegated
members. Every privilege role remains password-free `NOLOGIN`, `NOINHERIT`,
and fail-closed. Tests injected unsafe login attributes, quote/backslash
password material, extra outgoing membership, incoming delegation, and admin
option drift; reconciliation safely repaired them.

Bootstrap dependency order was proven as initializer success, PostgreSQL
health, bootstrap completion, application health, then NGINX health. The
bootstrap command provisions/reconciles roles, upgrades the sole migration,
deploys/enables/hardens or validates COW as appropriate, reconciles product
privileges, and independently revalidates both the marker and logins. The
observed final database fact was:

```text
compose-bootstrap: OK revision=006_001 state=EMPTY_SAFE safe=true
```

The database row independently returned `EMPTY_SAFE safe=true`, and all ten
login principals met the exact attribute/membership contract. A deliberate
broken-bootstrap overlay exited nonzero and left NGINX absent from the running
set. Reusing the unchanged secret/data volumes reproduced the same successful
state and byte-identical secret fingerprint.

## Acceptance-criteria evidence

### Criterion 1

- Result: PASSED.
- Evidence: PR #10 is the unique objective-007 PR, open and non-draft, with
  exact title `[OAP 007] Add one-command Compose and edge skeleton`, base
  `main`, and head `oap/007-compose-edge-skeleton`. The full order, active
  pointer, implementation commits, and this report are versioned on it. No
  merge or auto-merge occurred.

### Criterion 2

- Result: PASSED.
- Evidence: clean unique projects reached a healthy stack through the exact
  smoke wrapper around `docker compose build --pull` and
  `docker compose up --build --wait`. No `.env`, host-specific path, account,
  API key, package install, or manual secret action was used. The same job
  passed from a fresh GitHub checkout.

### Criterion 3

- Result: PASSED.
- Evidence: live Docker inspection found exactly one `PortBindings` entry:
  NGINX `127.0.0.1:8080:8080/tcp`. All other containers had none. Exact live
  memberships matched the four-network inventory; internal application,
  database, and browser networks preserved PostgreSQL/browser/edge separation.

### Criterion 4

- Result: PASSED.
- Evidence: the 23-file inventory, owners, `0400` modes, `0710` directory,
  dedicated traversal group, distinct high-entropy passwords, idempotence,
  fixed mounts, ten logins, sole grants, absence of admin/delegation drift,
  and unrelated-UID read denial all passed. Image/config/environment/history/
  log/Git scans exposed no credential. No long-running service received a
  secret mount or database locator.

### Criterion 5

- Result: PASSED.
- Evidence: bootstrap is an explicit one-shot `service_completed_successfully`
  gate on every online process and NGINX. It reached and live-validated
  `006_001 EMPTY_SAFE safe=true`. A forced bootstrap failure kept the edge
  unavailable, and the subsequent normal clean fixture recovered.

### Criterion 6

- Result: PASSED.
- Evidence: one digest-pinned non-root backend image ran the exact ten backend
  process commands; one digest-pinned non-root standalone Next image served
  the tested landing page/health surface; the non-root browser placeholder
  served only health with no Playwright, database, browser command, or write
  authority. All image IDs and commands are inventoried above.

### Criterion 7

- Result: PASSED.
- Evidence: NGINX config syntax passed. Public curl checks passed for `/`, Web
  live/ready, and all five routed backend health prefixes. Prefix stripping,
  Host/forwarded/request headers, loopback request ID response, one-megabyte
  body limit, timeouts, streaming setting, compression, security headers, and
  unknown-path 404s were checked statically/runtime. The Apache image built,
  `httpd -t` returned `Syntax OK`, and static route-equivalence tests passed.

### Criterion 8

- Result: PASSED.
- Evidence: all base refs are readable-tag plus immutable digest. Frozen
  Python/Node installs and reviewed licenses passed. Live inspection proved
  read-only root filesystems, cap-drop, narrow cap-add, no-new-privileges,
  users, bounded tmpfs, health/restart policies, named mounts, no bind/socket/
  host network, and exact group additions.

### Criterion 9

- Result: PASSED.
- Evidence: clean start, 15-container inventory, positive route/health,
  negative bootstrap, port/network/secret inspection, unrelated-UID denial,
  unchanged-volume restart, recovery, NGINX/Apache syntax, scans, and bounded
  cleanup passed locally and in the successful GitHub Compose job without a
  skip. No test container, network, or volume with a final smoke project name
  remained afterward.

### Criterion 10

- Result: PASSED.
- Evidence: all 19 implementation-head GitHub checks completed successfully,
  including every Python, PostgreSQL, Node, docs, dependency, Compose, and
  CodeQL gate. Repository and branch open code-scanning alert counts were both
  zero. Exact dependencies/integrities/licenses and base tags/digests are
  recorded above.

### Criterion 11

- Result: PASSED.
- Evidence: durable docs describe startup, credentials, roles, network/process
  authority, routes, lifecycle, failure diagnosis, backups/cleanup, base and
  package provenance, limitations, and deferred behavior. They call the stack
  pre-alpha and explicitly deny product-readiness claims.

### Criterion 12

- Result: PASSED by this publication commit.
- Evidence: `oap/active` is exact `007-a\n` (hex `3030372d610a`) with SHA-256
  `660897a2c1890d6c5c5564cadb6a24793daab165296ba4890bda998634c61050`.
  The unique order SHA-256 is
  `70a101558d37aeccb38881bde3557913976f6912c2105c96f20d95fc862acc32`.
  Before this report, the objective-wide OAP diff contained only that pointer
  and order. This SELF commit adds only this report and has literal
  implementation-head first parent
  `94702b5420b15be0a63171d678c3de56f8a3a31f`.

## Local verification

- `sudo docker compose version`: PASSED — Docker Compose
  `2.40.3+ds1-0ubuntu1~24.04.1`; Docker Engine `29.1.3`.
- `sudo docker compose config --quiet`: PASSED without an `.env` or
  host-specific source path.
- `sudo python tools/compose/verify.py --root .`: PASSED — exact static
  service/image/command/build/network/port/mount/secret/security policy.
- `sudo sh tools/compose/smoke.sh slaif007codeqlfix2`: PASSED — final-tree
  `compose-smoke: OK`; clean build/start, all 15 containers, all 13
  long-running services healthy, two one-shots successful, runtime topology,
  edge curls/headers/404s, DB marker/roles, secret facts and read denial,
  unchanged-volume restart, deliberate failure, recovery, scans, both edge
  syntax checks, packaging tests, and exact disposable cleanup.
- Required commands inside that wrapper — `docker compose build --pull`,
  `docker compose -p slaif007codeqlfix2 up --build --wait`, live
  `docker compose ps` inspection, required public `curl --fail --show-error`
  routes, and `down --volumes --remove-orphans` only for the exact disposable
  positive/negative projects: PASSED.
- `docker run --rm ... --user 10003:10003 ... read_bytes()`: PASSED as a
  negative test — returned nonzero and could not read the PostgreSQL password.
- `docker run --rm slaif-agent-site-nginx:local -t` with deterministic
  test-only upstream host mappings: PASSED — syntax successful.
- `docker build -f infra/apache/Dockerfile -t slaif-agent-site-apache:test .`
  and `docker run --rm slaif-agent-site-apache:test httpd -t`: PASSED — image
  built and `Syntax OK`.
- `uv --version`: PASSED — `uv 0.12.5`.
- `uv lock --check`: PASSED — resolved 41 packages.
- `uv sync --frozen --all-groups`: PASSED — checked 40 packages.
- `uv run --frozen ruff check services/backend tests/repository tests/packaging tools migrations`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tools migrations`:
  PASSED — 72 files formatted.
- `uv run --frozen mypy`: PASSED — no issues in 60 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 134 passed, none skipped, on local Python 3.12.
- `python -m compileall -q tools tests/repository tests/packaging` and
  `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  45 repository tests.
- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: PASSED —
  12 packaging tests.
- `python tools/check_repository.py`: PASSED.
- `uv build --out-dir <disposable-temporary-directory>`: PASSED — source and
  wheel distributions built from the frozen tree; the later CodeQL repair
  changed no packaged backend source or dependency input.
- Disposable local PostgreSQL matrix using fake `qualification` credentials
  and `uv run --frozen pytest -q services/backend/tests/integration`: PASSED —
  26 tests each on PostgreSQL 14, 15, 16, 17, and 18; after strengthening the
  membership-drift assertion, PostgreSQL 18 was repeated with 26 passed.
  GitHub then ran the final exact test on all five versions.
- `pnpm install --frozen-lockfile`: PASSED — ten workspaces and frozen
  lockfile.
- `pnpm check`: PASSED — root and app-local ESLint, Prettier, TypeScript
  typechecks, builds, two Web tests, one browser-placeholder test, and two
  contract tests; none skipped. Next `16.3.1` produced `/`, `/_not-found`,
  `/health/live`, and `/health/ready` routes.
- `pnpm licenses list --json` with the CI allowlist plus
  `pnpm list --recursive --depth Infinity`: PASSED — 307 packages, only the
  eight approved license groups listed above.
- Clean-index `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 42
  repository Markdown files, zero issues.
- `PUPPETEER_EXECUTABLE_PATH=<cached-chrome> python tools/check_mermaid.py`:
  PASSED — Mermaid CLI 11.16.0 rendered 12 diagrams in two files while
  scanning 42 Markdown files.
- Focused image/config/environment/history/log/Git private-key/token/cloud-key/
  credential-URI and generated-secret scans: PASSED. Expected secret filename,
  bootstrap-only locator, placeholder, and source-code DSN-construction
  references were reviewed without exposing a value.
- `git diff --check`: PASSED before both implementation commits.
- Allowed-path audit: PASSED — 57 implementation paths, all within the work
  order allowlist; no unstaged/untracked drift at implementation head.
- Disposable-resource audit with exact `slaif007*` Docker filters: PASSED — no
  test containers, volumes, or networks remained.
- Protected governance SHA-256 values remained exact:
  - `AGENTS.md`:
    `9b5995dd14574f853b34c08c0378c901d6b197a3073556c779c6588bd4ac4e38`
  - `ARCHITECTURE.md`:
    `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
  - `OAP-COMMUNICATION-coding-agent.md`:
    `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
  - `SECURITY.md`:
    `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
  - `LICENSE`:
    `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`
  - `NOTICE`:
    `c50dc6e712465adef910044e64e3d6faea618333f0803f7028ad68dcbd68a3c9`
- Prior OAP artifact diff against starting main: PASSED — no prior order,
  report, or OAP README changed. Immediate predecessor hashes remained:
  - 006-a order:
    `67cf1ab81382094795261e3a121f10f81b7bbb41e9aba10ae710a36f31fe3c5c`
  - 006-a report:
    `58c9589ee7e4c68155b70de911a379903413b6d9e0b89eecfc72833fb30bc17e`
  - 006-b order:
    `c0ca11222d5f4cfc114f79ffcf910f8ec8a6c768dc7a4cb531d6fc4bf8be0a82`
  - 006-b report:
    `19032eea54aba8c32a2031da79c0d947bc56cc02394979b1f93f948331044fda`

Product authentication, site/workspace confinement, content editing,
browser automation, accessibility-browser execution, review/promotion,
publication, and external-side-effect behavior are explicitly NOT IMPLEMENTED
and NOT RUN. Process health, curl, static accessibility, and deployment tests
are not presented as evidence for those future behaviors.

## GitHub CI / required checks

- Check state observed for implementation head:
  `94702b5420b15be0a63171d678c3de56f8a3a31f`.
- Final CI workflow run `32043518500`, attempt 2: SUCCESS.
- Final CodeQL workflow run `32043518457`, attempt 2: SUCCESS.
- Repository policy: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427239229>.
- Node contracts: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427245803>.
- Python 3.12 quality and package: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224184>.
- Python 3.13 quality and package: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224824>.
- Python 3.14 quality and package: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224816>.
- Foundation PostgreSQL 14: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224814>.
- Foundation PostgreSQL 15: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224250>.
- Foundation PostgreSQL 16: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224220>.
- Foundation PostgreSQL 17: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427242643>.
- Foundation PostgreSQL 18: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224345>.
- Compose and edge packaging: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224786>.
- Markdown: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224512>.
- Mermaid: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427246984>.
- Dependency review: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518500/job/95427224779>.
- CodeQL Detect supported languages: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518457/job/95427227333>.
- CodeQL Analyze (actions): SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518457/job/95427227608>.
- CodeQL Analyze (javascript-typescript): SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518457/job/95427227161>.
- CodeQL Analyze (python): SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/32043518457/job/95427227989>.
- CodeQL aggregate: SUCCESS —
  <https://github.com/ulfe-lmi/slaif-agent-site/runs/95427016131>.
- Open repository CodeQL/code-scanning alerts at report drafting: 0.
- Open objective-branch CodeQL/code-scanning alerts at report drafting: 0.
- Review state: one GitHub Advanced Security COMMENTED review for the original
  `0711` finding; its sole thread is resolved. Human reviews, human issue
  comments, and unresolved review threads: none.
- GitHub branch-protection required-status contexts: none configured; the
  order-required complete workflow/security set above nevertheless passed.
- All order-required checks green for the implementation head at report
  drafting: yes — 19 successful, zero failed, cancelled, skipped, pending, or
  missing.
- Initial implementation runs had external GitHub HTTP 429/503 action-download
  failures. Attempt 2 reran the failed jobs and succeeded; no workflow pin or
  repository policy was weakened to accommodate transient infrastructure.
- Report-only commit may trigger fresh checks: the strategic model must verify
  the `SELF` commit without rewriting this immutable report.

## Local setup / dependencies

- Packages/tools/services installed or configured: Docker Engine 29.1.3,
  Compose 2.40.3, uv 0.12.5, Python 3.12, Node 24.14.1, pnpm 11.22.0,
  transient markdownlint-cli2 0.23.2, Mermaid CLI 11.16.0, cached Chrome for
  Testing 152.0.7977.42, and disposable PostgreSQL 14–18 containers.
- `sudo`-level setup performed: installed local Chromium snap
  151.0.7922.108 for browser-capable tooling and used the local Docker daemon
  for only explicitly named fake/disposable projects, networks, volumes, and
  images. No broad prune was run.
- Durable setup changes committed/documented: Compose/OCI definitions,
  NGINX/Apache configs, generator/bootstrap extensions, policy/smoke tests, CI,
  and deployment/operations documentation.
- New production dependencies: exact Next/React packages listed above, within
  explicit order scope, frozen in `pnpm-lock.yaml`, license/integrity reviewed,
  build/test covered. No hosted SDK, cloud client, telemetry, Playwright,
  Puck, Tailwind, shadcn/ui, Radix, queue, database driver, or foundation
  source change was added.

## Documentation

Added `docs/DEPLOYMENT.md` and `docs/OPERATIONS.md` for prerequisites,
one-command startup, exact service/image/security/secret/network inventory,
route behavior, version/digest/license provenance, lifecycle, logs, backup,
failure diagnosis, safe exact cleanup, and limitations. Updated the README,
contribution guide, configuration, database bootstrap/roles, and service
authority records to match the implemented skeleton and local login model.

Documentation consistently labels this a pre-alpha skeleton. It explicitly
states that health is process evidence rather than product/publication
authority and that identity, site/workspace/content, browser automation,
review, publication, production TLS, rotation, and release-policy work remain
deferred.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production secrets printed or committed: no.
- Production systems/data/credentials accessed: no.
- External/production database accessed: no.
- Required tests skipped/not run: no. Future product behaviors explicitly
  outside this work order are identified as NOT IMPLEMENTED/NOT RUN, not as
  skipped passing tests.
- Scope deviation: no. Every implementation path is within the activated
  allowlist; `.markdownlint-cli2.yaml` and root `eslint.config.mjs` were left
  unchanged after the pre-commit scope audit.
- Security controls weakened to pass a test: no. The CodeQL response narrowed
  secret traversal and added a negative unauthorized-UID runtime test.
- Foundation dependency/version/source changed or private foundation API used:
  no.
- Docker socket, host filesystem, host network, source bind, real external
  service, or cloud account used by the product stack: no.
- Broad or unrelated destructive Docker action performed: no. Cleanup named
  only exact `slaif007*` disposable projects and their three fixture volumes.
- Prior OAP artifacts changed: no.
- Extra PR created for the same numeric objective: NO.
- PR merged by coding agent: NO.
- Auto-merge enabled by coding agent: NO.
- PR #5 or #7 modified by coding agent: NO.
- Activated order and `oap/active` edited by coding agent: NO; their strategic
  bytes were committed unchanged.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- No blocker remains for work order 007-a.
- The six Python HTTP identities expose only existing process health and 404
  behavior. No online service pool or service DSN is wired yet.
- The browser worker is a health-only placeholder. Playwright, navigation,
  screenshots, accessibility-browser execution, confinement enforcement, and
  artifact handling are not implemented.
- Product setup, authentication, identity administration, sites, configurable
  content models, Puck editing, workspaces/capabilities, review snapshots,
  promotion/discard, media behavior, and publication are not implemented.
- The default edge is loopback HTTP. Production TLS/proxy trust, service-to-
  service authentication, enforceable egress policy, backups, credential
  rotation, metrics, SBOM/vulnerability release policy, and scale-out storage
  remain deferred. The Apache adapter is a reference image, not a second
  Compose edge.
- `EMPTY_SAFE` proves the existing empty database/COW/privilege state only; it
  is not website readiness or publication authority.

## Recommended strategic follow-up

Independently verify the `SELF` commit parent/path, PR #10 identity, final
report-head checks, CodeQL alert count, and the service/secret/role evidence.
Only the strategic model may decide whether objective 007 is accepted, merged,
amended, abandoned, or followed by another activated work order.

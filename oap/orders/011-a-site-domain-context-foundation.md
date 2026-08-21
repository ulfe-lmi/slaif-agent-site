# OAP Work Order — 011-a

## Objective

Create the unique PR for live objective `011` and implement its persistence/
domain foundation: site and trusted domain/path data, default-locale and
installation site-quota primitives, deterministic normalization, immutable
server-owned `SiteContext`, least-privilege Control services, and exhaustive
multi-site/cross-site resolver constraints.

This activates the foundation slice of inert proposal
`workorders/010-a-sites-domains-locales-trusted-resolution.md` under the live
number mapping documented in the roadmap. Authenticated HTTP site-management,
public/admin resolution routes, demo seeding, and Compose/NGINX multi-site proof
remain planned for `011-b` on this same PR.

## GitHub objective state

- Numeric objective: `011`
- Execution round: `011-a`
- PR mode: `CREATE_NEW_PR`
- Existing PR: none
- Base branch: `main`
- Verified remote main:
  `ffe9c868353e521dffed88dc623ea9704a7c813c`
- Required new branch: `oap/011-sites-trusted-resolution`
- Required PR title:
  `[OAP 011] Establish sites and trusted resolution`

PR `#15` for objective 010 is merged and remote main contains it. Create exactly
one new PR for objective 011. Never reuse/modify PR #15, create a second
objective-011 PR, merge, close, or enable auto-merge.

## Current state and boundaries

Current main has secure installation/local administrator/session/CSRF and
Control HTTP foundations through migration `012_001`, with six-project auth
E2E. It has no `site`, `site_domain`, trusted site resolver, membership, or
site-owned product relation.

Multi-site in this objective means site-confined institutional deployment. It
does not claim hostile tenant isolation, RLS, per-tenant encryption, or public
SaaS. Domain/path selection identifies a site; it never grants human membership
or agent authority. Membership/RBAC is live objective 012; no site-content
tables exist until later phases.

## Moderate autonomy and completion rule

- Target: 50 minutes; hard stop: 75 minutes.
- Audit schema/normalization/resolution/privilege invariants before DB runs.
- No arbitrary local attempt cap. Diagnose/fix in-scope failures until focused
  local evidence is green; no unchanged blind reruns.
- Do not push/open the PR with a known failing affected test.
- One initial CI generation; one corrective code generation only for a genuine
  clean-environment/PostgreSQL-version issue; never workflow-rerun.
- No local browser/Playwright or broad supply-chain/image work.

## Allowed scope

```text
services/backend/src/slaif_agent_site/db/alembic/versions/013_001_site_foundation.py
services/backend/src/slaif_agent_site/db/privileges.py
services/backend/src/slaif_agent_site/sites/**
services/backend/src/slaif_agent_site/control_api/database.py
services/backend/src/slaif_agent_site/control_api/config.py
services/backend/tests/unit/test_sites.py
services/backend/tests/unit/test_control_database.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/integration/test_sites.py
services/backend/tests/integration/test_database_bootstrap.py
services/backend/tests/integration/test_control_database_integration.py
.github/workflows/ci.yml
tools/compose/control_readiness.py
tests/packaging/test_compose_policy.py
tools/check_repository.py
tests/repository/test_repository_policy.py
migrations/alembic/README.md
docs/API.md
docs/CONFIGURATION.md
docs/DATABASE_ROLES.md
docs/OPERATIONS.md
docs/SITES.md
README.md
oap/active
oap/orders/011-a-site-domain-context-foundation.md
oap/reports/011-a-site-domain-context-foundation.md
```

Use the minimum subset; equivalent focused module/test names are acceptable.
No web/Next.js, NGINX/Apache, Compose topology, dependency/lock, auth/session
semantics, memberships/roles, content/COW tables, RLS, deletion, or adjacent
product module may change.

## Requirements

### 1. Forward site foundation migration

Add deterministic revision `013_001` after `012_001`. Add non-COW Control
objects sufficient for:

```text
site:
  UUID primary key
  normalized stable key/slug and display name
  ACTIVE|ARCHIVED status
  canonical_revision bigint starting 0, never negative
  normalized default locale
  component catalog version placeholder owned by platform policy
  content model revision starting 0
  created_at / updated_at

site_domain:
  UUID primary key
  immutable site_id FK with explicit delete policy
  normalized ASCII hostname
  normalized path prefix (root or bounded canonical prefix)
  is_primary
  created_at

installation site quota:
  bounded max-sites policy associated with the installation singleton
```

Use exact unique/check/partial-primary constraints and indexes so two mappings
cannot ambiguously claim the same normalized `(hostname,path_prefix)`, each
active site has at most one primary mapping, revisions are monotonic/bounded,
and archived sites do not resolve as active. Do not add site deletion or cascade
that could silently erase future content. Do not place these tables under COW.

Owner-created Control-only `SECURITY DEFINER` functions may create/read/update/
archive and resolve foundation data for the semantic service, but this round
does not expose them over HTTP. Functions use fixed `pg_catalog` search path,
fully qualified objects, server-generated IDs, `PUBLIC` revoke, exact
`slaif_control` execute, stable no-row/conflict behavior, deterministic
downgrade, and no direct Control/runtime relation grants.

Site creation must enforce the installation max-sites quota transactionally.
Do not accept caller-selected canonical revision, status, object UUID, or
catalog/content-model revision.

### 2. Normalization contracts

Implement one shared typed normalization boundary used before every write and
lookup:

- site key: lowercase ASCII slug, bounded length, no leading/trailing/repeated
  hyphen, not a reserved product segment;
- hostname: lowercase IDNA ASCII, no scheme/userinfo/path/query/fragment,
  normalized single trailing dot policy, explicit port handling outside stored
  value, bounded labels/total length, safe localhost policy, and reject invalid
  IP/host ambiguity;
- path prefix: canonical leading slash, no query/fragment/backslash/dot segment/
  percent-decoding ambiguity/repeated slash/trailing slash except root, bounded
  segments/length, and no collision with reserved platform namespaces;
- locale: bounded canonical BCP47-like product subset with deterministic case
  normalization; no arbitrary locale library/service dependency.

Reserved top-level namespaces include at least API/control/editor/agent, health,
admin, setup, login, logout, MCP, media, preview, and internal/static framework
paths. `/s/<site-key>` is the local-development mapping convention and is
derived/validated by trusted code rather than accepting a body `site_id`.

Add table-driven/property-style tests across Unicode/IDNA, case, trailing dot,
ports, IPv4/IPv6, encoded/dot/backslash, prefix-boundary, reserved, malformed,
overlong, and normalization-equivalence cases. Do not add Hypothesis or another
dependency.

### 3. Server-owned SiteContext and resolver

Add an immutable typed `SiteContext` containing only trusted site identity and
bounded routing facts needed downstream, including site UUID/key/status,
canonical revision, default locale, and matched normalized hostname/prefix.
It must not be constructible from an unvalidated request DTO through a public
shortcut.

Resolver input is trusted request-routing material (host authority plus path),
not a caller body/query/header `site_id`. It must:

- normalize host/path once;
- consider only ACTIVE sites/mappings;
- use exact host plus deterministic longest path-prefix boundary match;
- distinguish `/site` from `/site-other` and reject ambiguous equal matches;
- support local `/s/<key>/...` through persisted active site key/context;
- return one constant not-found/conflict result without cross-site data; and
- never infer authorization, membership, capability, or publication rights.

Every new site repository/service method must require or produce trusted
`SiteContext`; no method may query a site-owned identifier without the context
parameter once such identifiers exist. Since no site-owned content exists yet,
prove the API shape and two-site resolver isolation now.

### 4. Semantic Control service

Add internal typed service/adapter operations for create, bounded profile
update, archive, get/list, add/update/remove domain mapping, and resolve. They
are callable only from trusted Control application code; HTTP authorization is
deliberately deferred to `011-b`.

Use server UUID generation, explicit idempotent/conflict behavior, database
transactions, row locks for quota/primary mapping/archive changes, database
time, stable public-safe errors, and secret-free results. No physical DNS
change, site deletion, membership, role, or content operation.

### 5. Executable persistence/security evidence

Using disposable PostgreSQL and actual `slaif_control`, prove:

- create up to quota and fail the next atomically under concurrency;
- normalized key/domain/prefix/locale equivalence and uniqueness;
- primary-domain invariant and safe reassignment/removal rules;
- two active sites resolve only their own host/prefix/local `/s/<key>` context;
- forged body/query site IDs are absent from resolver/service APIs;
- host/path prefix ambiguity, reserved paths, archived site, unknown host/key,
  and cross-site mapping substitution fail closed;
- canonical/content-model revisions cannot be caller-written or decreased;
- archive prevents resolution without deleting rows;
- Control has only exact functions, while agent/editor/public/reviewer/scheduler
  cannot access relations/functions; and
- cancellation/constraint/database failure rolls back quota/site/domain state.

Run bootstrap, existing auth/session integration, and new site integration
together. Add `test_sites.py` to every PostgreSQL 14–18 job without removing any
existing file; preserve exactly 20 check names. Packaged migration-head Compose
readiness must remain green without a hard-coded revision update.

### 6. Documentation and future split

Document schema, normalization, trusted resolver, local `/s/<key>`, quota,
archive/no-delete, role boundaries, and institutional-tenancy limitation. State
that no HTTP site CRUD, membership/RBAC, UI, content, DNS automation, hostile
tenancy, or seeded demo site exists until later rounds/objectives.

## Observable acceptance criteria

1. Deterministic non-COW site/domain/quota schema and exact privileges migrate,
   downgrade/rebuild, and validate safely.
2. All writes/lookups use one normalization contract; equivalent/ambiguous/
   reserved inputs cannot create or select competing sites.
3. Trusted resolver returns exactly one immutable active `SiteContext` through
   hostname/path/local-key matching and never grants authorization.
4. Two-site/cross-site/quota/concurrency/archive/cancellation/role negative
   tests prove fail-closed state and no deletion.
5. Existing auth/Compose/Playwright behavior remains unchanged and green; no
   route/UI/membership/content/dependency scope enters.
6. One new objective-011 PR is created from current remote main, and only one;
   report head is 20/20 green, no workflow rerun, report-only `SELF` correct.

## Verification required

Run focused normalization/site/service unit tests, then complete disposable-
PostgreSQL bootstrap/auth/site integration until green after concrete fixes.
Run Ruff/format/mypy/compile, strict migration/create-drop/grant/inventory,
repository/packaging checks, changed-doc/report Markdownlint `--no-globs`,
exact paths/main/prior hashes, no conflict markers, and `git diff --check`.

Do not run local Playwright/browser or broad supply-chain/image. Run local
Compose only if migration-head readiness changes require diagnosis. GitHub runs
the complete existing 20 checks plus the new site test in the unchanged matrix.
Lint the exact report before publication.

## GitHub workflow and report

Fetch current remote main and verify objective 010 is merged. Preserve the
strategic order/active bytes, create the fresh required branch from remote
main, implement, commit, push, and create exactly one ready/non-draft PR with
the required title and a concise honest body. Never merge.

Atomically publish exactly:

```text
oap/reports/011-a-site-domain-context-foundation.md
```

The linted report-only `SELF` commit must parent the literal implementation
head. Report PR/branch/base/head; schema/function/grant inventory; normalization
corpus; resolver/context/two-site/quota/concurrency/cancellation evidence;
local/five-version/20-check results; corrections/paths/hashes/skips; no-workflow-
rerun/no-extra-PR/no-merge state; and `Report publication commit: SELF`.

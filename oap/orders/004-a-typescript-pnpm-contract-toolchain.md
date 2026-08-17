# OAP Work Order — 004-a

## Objective

Create exactly one new GitHub pull request that establishes the reproducible
Node 24/TypeScript/pnpm workspace and the seven shared contract-package
boundaries defined by the architecture, without implementing the web app,
browser worker, or product domain contracts prematurely.

## GitHub objective state

- Numeric objective: `004`
- Execution round: `004-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective PR: N/A
- Required head branch: `oap/004-typescript-workspace`
- Base branch: `main`
- Required PR title: `[OAP 004] Add TypeScript workspace and contract toolchain`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`

## Strategic context

Objective `003` is merged and provides the qualified PyPI COW foundation,
Python backend package baseline, exact `uv.lock`, Python 3.12–3.14 quality/
package gates, and PostgreSQL 14–18 adoption matrix. Architecture Phase 1 next
requires the TypeScript side of the monorepo so later web, Puck, browser-worker,
and generated contract work has one reproducible foundation.

This objective creates package/tooling boundaries only. It must not implement
Next.js pages, React components, Puck, Playwright, HTTP clients, browser
authority, content/composition schemas, or application behavior assigned to
later work orders.

## Current verified state

The strategic model independently verified before activation:

- Remote `main` SHA:
  `916945f9438c0bbc7ce20ce108142c79f9ab40aa`
- Objective `003` PR `#4` is merged; remote `main` contains its complete
  `003-a`/`003-b` OAP history.
- `main` CI and CodeQL push runs are successful.
- Current merged OAP active identifier: `003-b`.
- There is one unrelated automated Dependabot PR `#5`, titled
  `Bump the python-dependencies group with 2 updates`. It is not an OAP
  objective, must not be reused, amended, closed, merged, or otherwise acted on
  by this coding turn.
- No objective `004` PR exists.
- Repository has no root Node manifest, pnpm workspace/lock, TypeScript config,
  JavaScript/TypeScript source, shared package directories, or contract
  toolchain.
- Existing setup-node v7.0.0 action pin is already approved by repository
  policy; pnpm/action-setup is not yet approved.

Current compatible toolchain selected after registry/upstream verification:

```text
Node runtime: 24.x (CI exact major 24)
pnpm: 11.22.0, MIT, requires Node >=22.13
pnpm package integrity:
  sha512-H/hwxMYTPf2I+yr8Rt0T1H8JyXlLQ4xv20fKmMrzvBY4HuC+k6CRuOOCTPAfiJ9G19niCRD7C+GrD7W6qA3WIQ==
TypeScript: 6.0.3, Apache-2.0
ESLint: 10.8.1, MIT
@eslint/js: 10.0.1, MIT
typescript-eslint: 8.67.0, MIT; peer TypeScript >=4.8.4,<6.1.0
Prettier: 3.9.6, MIT
Vitest: 4.1.10, MIT
@types/node: 24.13.3, MIT
pnpm/action-setup:
  0977fd99725f1db4007ccb2928dbb4e90d06cc86 # v6.0.10
actions/setup-node:
  820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
```

TypeScript 7.0.2 is newer but is deliberately not selected because the current
qualified typescript-eslint peer range excludes it. Do not suppress peer
warnings or use an unsupported compiler/linter pairing.

Reverify npm metadata and remote `main` at execution time. Patch-level changes
do not authorize silent version substitution; report and preserve this bounded
selection unless a real incompatibility requires strategic review.

## Required final tracked paths

The final PR diff against `main` must contain exactly these forty-one paths:

```text
.github/dependabot.yml
.github/workflows/ci.yml
.gitignore
AGENTS.md
CONTRIBUTING.md
README.md
contracts/README.md
eslint.config.mjs
oap/active
oap/orders/004-a-typescript-pnpm-contract-toolchain.md
oap/reports/004-a-typescript-pnpm-contract-toolchain.md
package.json
packages/api-client/package.json
packages/api-client/src/index.ts
packages/api-client/tsconfig.json
packages/browser-tool-contracts/package.json
packages/browser-tool-contracts/src/index.ts
packages/browser-tool-contracts/tsconfig.json
packages/component-catalog/package.json
packages/component-catalog/src/index.ts
packages/component-catalog/tsconfig.json
packages/composition-schema/package.json
packages/composition-schema/src/index.ts
packages/composition-schema/tsconfig.json
packages/content-model-schema/package.json
packages/content-model-schema/src/index.ts
packages/content-model-schema/tsconfig.json
packages/scope-catalog/package.json
packages/scope-catalog/src/index.ts
packages/scope-catalog/tsconfig.json
packages/test-fixtures/package.json
packages/test-fixtures/src/index.ts
packages/test-fixtures/tsconfig.json
pnpm-lock.yaml
pnpm-workspace.yaml
prettier.config.mjs
tests/contracts/workspace-contracts.test.ts
tests/repository/test_repository_policy.py
tools/check_repository.py
tsconfig.base.json
tsconfig.json
```

Do not add `node_modules`, `.pnpm-store`, generated `dist`, coverage, caches,
temporary contract output, apps/web, browser-worker, runtime package, or any
additional package/config file.

## Scope

### A. Root Node/pnpm workspace

Add a private root `package.json` that:

- identifies `slaif-agent-site` version `0.0.0`, Apache-2.0, ESM/private;
- requires Node `>=24,<25`;
- pins package manager exactly to `pnpm@11.22.0` (include Corepack integrity
  metadata if the current standard mechanism supports it deterministically);
- pins all direct dev dependencies exactly to the selected versions above;
- defines stable scripts for `lint`, `format:check`, `typecheck`, `test`,
  `build`, `check`, and license/inventory inspection as appropriate;
- contains no lifecycle install script, product/runtime dependency, hosted
  SDK, CDN, telemetry, publish configuration, or external-service credential.

Add:

- `pnpm-workspace.yaml` with only `packages/*` for this objective;
- exact `pnpm-lock.yaml` generated by pnpm 11.22.0 from the public npm registry;
- `tsconfig.base.json` with strict modern ESM/bundler-safe settings,
  `noUncheckedIndexedAccess`, declarations/source maps for package builds, and
  no unsafe relaxation;
- root `tsconfig.json` that typechecks all package source and contract tests
  while package build configs remain composable;
- flat `eslint.config.mjs` using exact compatible @eslint/js and
  typescript-eslint with type-aware rules where practical;
- deterministic `prettier.config.mjs`;
- `.gitignore` entries for Node/pnpm/build/test artifacts without hiding source,
  manifests, locks, or generated-contract drift that policy should inspect.

### B. Architecture package boundaries

Create exactly these private workspace packages:

```text
@slaif-agent-site/composition-schema
@slaif-agent-site/component-catalog
@slaif-agent-site/content-model-schema
@slaif-agent-site/scope-catalog
@slaif-agent-site/browser-tool-contracts
@slaif-agent-site/api-client
@slaif-agent-site/test-fixtures
```

Each package must have only:

- private `package.json` at version `0.0.0`, Apache-2.0, ESM, explicit exports/
  types/files/build/typecheck scripts and no runtime dependency;
- a small `src/index.ts` exporting package identity/status/version placeholders
  or minimal generic typing needed to prove the boundary;
- a package `tsconfig.json` extending the root base with deterministic `dist`
  output.

Placeholder rules:

- Clearly label product contracts as scaffolding/unimplemented.
- Do not invent field primitives, scopes, component props, composition nodes,
  browser tools, HTTP endpoints, or fixtures assigned to later objectives.
- Do not export `any`, executable callback/plugin hooks, arbitrary JSON claims,
  or a false stable compatibility promise.
- Do not make packages publishable or add cross-package dependencies merely to
  demonstrate a graph.

### C. Contract conventions and smoke tests

Add `contracts/README.md` documenting:

- source-of-truth ownership by product domain packages;
- versioned JSON Schema/OpenAPI/MCP/generated directories planned by
  Architecture Section 12;
- deterministic generation/check policy once real schemas exist;
- generated artifacts are never manually edited and are not added yet;
- Python/TypeScript schema parity will be implemented with domain contracts,
  not inferred from duplicated handwritten models;
- current packages are boundaries only, not implemented product APIs.

Add `tests/contracts/workspace-contracts.test.ts` that imports every package
through its declared workspace/package boundary and verifies:

- all seven identities are unique and exact;
- versions/statuses are deterministic and explicitly scaffold/pre-alpha;
- package exports are serializable/side-effect-free where applicable;
- no package unexpectedly exports product-domain behavior;
- package manifests are private, exact-versioned, Apache-2.0, dependency-free,
  and have valid export/build/type contracts.

Avoid snapshot tests that bless incidental compiler output.

### D. Repository policy and negative fixtures

Extend `tools/check_repository.py` and its isolated tests to:

- require every listed root/package/contract file;
- approve exact `pnpm/action-setup` SHA with `# v6.0.10` comment;
- validate root `private`, version, Node engine, exact package manager, direct
  dependency allowlist/versions, scripts, workspace package set;
- validate all workspace package manifests are private/license/version/source-
  boundary correct and dependency-free;
- inspect `pnpm-lock.yaml` for public npm registry/integrity and reject Git,
  GitHub tarball, direct URL, local/file/link, patch, workspace escape, missing
  integrity, or unapproved registry for external packages;
- forbid lifecycle scripts and required hosted/account-bound SDKs;
- use positive/negative temporary fixtures and remain extensible for later
  deliberate package additions.

Do not implement a home-grown full YAML/npm-license parser. Use standard JSON,
bounded text/YAML structure checks, pnpm commands, and explicit limitations.

### E. CI and dependency automation

Add one required CI job named `Node contracts` that:

- runs on `ubuntu-24.04`, explicit timeout, contents-read-only;
- checks out with credentials disabled;
- sets up exact pnpm through the approved full-SHA action and exact version;
- sets up Node 24 through the existing approved full-SHA action with pnpm cache
  keyed by `pnpm-lock.yaml` if safe;
- runs frozen install, lint, format check, typecheck, unit tests, package builds,
  direct license/inventory check, and tracked/generated diff check;
- uses no secret, write permission, `pull_request_target`, mutable action,
  publish step, artifact upload, or external service.

Preserve all existing Python/PostgreSQL/repository/Markdown/Mermaid/Dependency
Review/CodeQL checks. CodeQL language detection must now add and successfully
analyze `javascript-typescript` in addition to `actions` and `python`.

Add weekly grouped `npm` Dependabot updates at `/` with bounded PR count while
retaining GitHub Actions and pip entries. Dependabot proposals never bypass
frozen lock/CI/strategic review.

### F. Durable guidance

Update:

- `AGENTS.md` and `CONTRIBUTING.md` with exact Node/pnpm frozen install/lint/
  format/typecheck/test/build commands and the compatible TypeScript choice;
- `README.md` current status/repository map/CI/delivery sequence to state the
  TypeScript contract scaffold exists while Next/React/Puck/browser/product
  contracts remain unimplemented.

Do not change `ARCHITECTURE.md`, foundation documentation/NOTICE, Python
dependency/lock, product readiness language, or prior OAP artifacts.

## Non-goals

- No Next.js, React, Tailwind, shadcn/ui, Radix, Puck, Playwright, FastAPI,
  API client behavior, HTTP call, browser worker, application schema/model,
  component catalog content, scope list, composition model, test fixture data,
  code generation, Docker/Compose, or service process.
- No runtime dependency in any Node package.
- No TypeScript 7 or unsupported compiler/linter peer combination.
- No npm/pnpm package publication, changeset/release tooling, monorepo task
  orchestrator, hosted registry, telemetry, or account-bound tool.
- No edit/action on unrelated Dependabot PR `#5`.
- No extra branch/PR, merge, auto-merge, issue, release, tag, or setting change.

## Acceptance criteria

1. Exactly one non-draft objective `004` PR exists with required base/head/
   title; final diff contains exactly the forty-one allowed paths.
2. Exact pnpm 11.22.0 frozen install succeeds from a clean store on Node 24;
   lock is unchanged and every external package has public registry integrity.
3. Lint, format, strict typecheck, tests, and all seven package builds pass;
   no tracked/generated drift remains.
4. Root and seven package manifests are private, exact-versioned/licensed,
   dependency/scope compliant and contain no lifecycle/hosted/publish behavior.
5. Contract smoke test imports all seven declared boundaries and proves only
   honest scaffolding—not invented product behavior.
6. Repository-policy negatives reject mutable/unapproved actions, package
   versions, registries, Git/direct/local/path/patch links, missing integrity,
   lifecycle scripts, hosted SDKs, wrong workspace package set, and public
   package manifests.
7. CI adds one safe `Node contracts` gate; CodeQL successfully analyzes
   `javascript-typescript`, `actions`, and `python`; all existing matrices stay
   green.
8. Direct/transitive package licenses are permissive and recorded in report;
   no runtime dependency or non-permissive package exists.
9. README/AGENTS/CONTRIBUTING accurately state what is scaffolded and what
   remains planned; Python foundation files and architecture are unchanged.
10. `oap/active` is `004-a`; unique order/report correlation holds and all
    prior OAP artifacts are byte-unchanged.
11. Final remote head is the report-only `SELF` commit whose first parent is
    the literal implementation head.
12. Unrelated Dependabot PR `#5` remains untouched; no secret, production
    access, hosted runtime, product behavior, or architecture drift occurs.

## Verification required

Run and report exact outcomes for:

```bash
node --version
pnpm --version
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm licenses list --json
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen pytest services/backend/tests/unit tests/repository
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Also verify clean pnpm store install, lock registries/integrities, package
manifest/export/build contents, exact direct versions/licenses/peer
compatibility, no lifecycle scripts/runtime deps/hosted SDKs, deterministic
build outputs, action pins, Node CI logs, CodeQL three-language matrix, full
existing Python/PostgreSQL checks, exact path scope, prior-file hashes, focused
secret scan, unique PR identity/body/draft/auto-merge, report parent/delta, and
clean synchronized worktree.

No application/runtime/browser/database product test exists in this objective;
report those as not implemented/not run, never passed.

## Safety / security constraints

- Use only public npm registry and exact reviewed versions/integrities.
- Never execute unreviewed lifecycle hooks, publish, use a token/secret, or
  access production/external services for tests.
- Do not weaken existing CI, Python foundation, CodeQL, or OAP boundaries.
- Keep all tool installation/cache/build output in the disposable environment
  and out of Git.

## Local execution capability

Routine Node/pnpm/tool installation, clean-store testing, license inspection,
and CI diagnosis belong to the coding agent. Do not transfer them to the human
or strategic model.

## GitHub workflow

Create `oap/004-typescript-workspace` from current remote main, preserving the
pre-published order/active pointer. Stage only the forty allowed pre-report
paths, run all checks, push and create one non-draft PR, then repair all
in-scope failures on that PR. Atomically publish the report as the forty-first
path in a final report-only `SELF` commit. Never touch PR `#5`, merge,
auto-merge, create another PR, or choose `005-a`.

## Required report

Atomically publish exactly:

```text
oap/reports/004-a-typescript-pnpm-contract-toolchain.md
```

Use the full protocol 1.2 structure. Include exact PR/commit/path identity;
Node/pnpm/tool versions/integrities/licenses/peer compatibility; workspace and
package inventory; lock source/integrity audit; manifest/script/exports;
contract smoke evidence; clean install/lint/format/typecheck/test/build/license
results; repository-policy negative fixtures; Python regression checks; all
final GitHub/CodeQL states; setup performed; unimplemented product behavior;
and every scope/secret/production/Dependabot/no-merge confirmation.

Publish atomically, commit the report alone, push it, verify remote
head/first-parent/report-only delta, then send exact two-byte FIFO `OK`.

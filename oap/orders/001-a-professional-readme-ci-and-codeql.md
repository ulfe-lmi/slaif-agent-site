# OAP Work Order — 001-a

## Objective

Create exactly one new GitHub pull request that turns the architecture-only
SLAIF Agent-Site repository into a professional, honest, security-aware project
front door by delivering:

1. a complete root `README.md` derived from `ARCHITECTURE.md`;
2. locally vendored official SLAIF branding with provenance;
3. contributor, security, notice, and pull-request guidance;
4. deterministic repository-policy validation with tests;
5. SHA-pinned GitHub CI and dependency review;
6. advanced CodeQL scanning for GitHub Actions, Python, and—when source is
   present—JavaScript/TypeScript;
7. Dependabot maintenance for GitHub Actions; and
8. the complete versioned OAP order/active/report transcript for objective
   `001`.

This is preparation work. It must improve project credibility without
pretending that the Agent-Site application, Compose stack, or product tests
already exist.

## GitHub objective state

- Numeric objective: `001`
- Execution round: `001-a`
- PR mode: `CREATE_NEW_PR`
- Existing PR: N/A
- Required head branch: `oap/001-readme-ci-codeql`
- Base branch: `main`
- Required PR title: `[OAP 001] Add professional README, CI, and CodeQL`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`
- Repository URL: `https://github.com/ulfe-lmi/slaif-agent-site`

## Strategic context

Objective `000` was accepted and merged through PR `#1`. It established the
canonical architecture, the coding-agent constitution/protocol, and an
append-only versioned OAP transcript. Objective `001` is the first normal new
PR after that bootstrap.

The human explicitly requested a full README based on the architecture, SLAIF
branding from the SLAIF API Gateway README, CodeQL, CI, and professional-grade
project preparation.

The referenced source README is:

```text
https://github.com/ulfe-lmi/slaif-api-gateway/blob/main/README.md
```

It displays the official SLAIF SVG from:

```text
https://slaif.si/img/logos/SLAIF_logo_ANG_barve.svg
```

The Gateway repository also vendors byte-identical content at:

```text
app/slaif_gateway/web/static/img/slaif-logo.svg
```

Both copies were independently verified as SHA-256:

```text
0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08
```

Use that exact SVG as a local repository asset. Do not make the README's brand
identity depend on a remote image request.

GitHub's current official CodeQL guidance supports advanced setup in public
repositories and defines the language identifiers `actions`, `python`, and
`javascript-typescript`. CodeQL Action v4 is the current major generation.
The workflow must use advanced setup, least privilege, `build-mode: none`, and
the `security-extended` query suite.

## Current verified state

The strategic model independently verified immediately before activation:

- Remote default branch: `main`
- Remote `main` SHA:
  `3e54c65a798ab5c2df6f2498f2197a19cb60520b`
- Remote `main` contains the merge commit for objective `000`, including all
  prior OAP commits and `SELF` relationships.
- Open pull requests: none
- Existing branches: `main` and the retained objective `000` branch only
- Root README: two lines containing only the project name and short
  description
- GitHub Actions: enabled
- Allowed Actions policy: all actions allowed; repository-level SHA pinning is
  not enforced, so this PR must enforce SHA pinning in repository policy
- CodeQL default setup: `not-configured`
- CodeQL databases: none
- Existing workflows: none
- Classic branch protection/rulesets: none
- GitHub secret scanning and push protection: currently disabled; changing
  repository settings is outside this work order
- Current repository state is documentation/governance only; there is no
  application source, dependency manifest, Compose file, or product test suite
- Current merged active OAP identifier: `000-b`

If GitHub differs materially at execution time, stop scope expansion and
report the exact discrepancy. Do not create a duplicate PR or silently alter
repository security settings.

## Approved external action revisions

Use these independently verified immutable full commit SHAs with the shown
release comments. A `uses:` reference must never use only a branch or mutable
major tag.

```text
actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
github/codeql-action/*@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd # v4.37.7
actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0
DavidAnson/markdownlint-cli2-action@21c1be1b93ad9ed58fa840aacc3f279cde2a72ff # v24.2.0
```

`markdownlint-cli2-action` v24.2.0 embeds
`markdownlint-cli2==0.23.2`; use that exact CLI version for local parity.

## Required final tracked paths

The final PR diff against `main` must contain exactly these seventeen paths:

```text
.github/dependabot.yml
.github/pull_request_template.md
.github/workflows/ci.yml
.github/workflows/codeql.yml
.markdownlint-cli2.yaml
AGENTS.md
CONTRIBUTING.md
NOTICE
README.md
SECURITY.md
docs/assets/README.md
docs/assets/slaif-logo.svg
oap/active
oap/orders/001-a-professional-readme-ci-and-codeql.md
oap/reports/001-a-professional-readme-ci-and-codeql.md
tests/repository/test_repository_policy.py
tools/check_repository.py
```

Do not add generated caches, package manifests, package lockfiles, coverage,
SARIF, downloaded action code, or temporary files.

## Scope

### A. Professional project presentation

- Replace the minimal root README with a complete architecture-derived README.
- Vendor and use the exact official SLAIF logo.
- Add logo provenance documentation and an Apache-style project `NOTICE`.
- Add practical `CONTRIBUTING.md`, `SECURITY.md`, and a PR template.
- Update `AGENTS.md` only to add the new preparation validation commands and
  workflow expectations; preserve its role and product rules.

### B. Repository quality automation

- Add a standard-library-only repository-policy checker.
- Add focused unit tests for that checker.
- Add Markdown lint configuration that passes existing intentional project
  conventions without disabling lint wholesale.
- Add CI for policy checks, tests, Markdown lint, and dependency review.
- Add Dependabot maintenance for GitHub Actions.

### C. CodeQL

- Add an advanced CodeQL workflow with a dynamic supported-language matrix.
- Analyze `actions` and Python immediately because this PR adds workflows and
  a Python policy checker.
- Add `javascript-typescript` automatically when JavaScript or TypeScript
  source files later exist.

### D. OAP/GitHub publication

- Create the required new branch and exactly one new non-draft PR.
- Commit the strategic-authored active order and pointer unchanged.
- Publish the immutable `001-a` report in a final report-only `SELF` commit.
- Inspect final-head CI/CodeQL results; the strategic model will independently
  enforce the merge gate.

## Non-goals

- Do not create the application monorepo skeleton, backend, frontend, browser
  worker, migrations, Compose stack, containers, or product tests.
- Do not add `pyproject.toml`, `package.json`, `uv.lock`, `pnpm-lock.yaml`, or
  any application/runtime dependency.
- Do not claim that `docker compose up --build` works today.
- Do not claim any planned endpoint, UI, security property, or test as already
  implemented.
- Do not edit `ARCHITECTURE.md`.
- Do not edit any objective `000` order or report.
- Do not copy feature/status text from SLAIF API Gateway into Agent-Site; it is
  a different product. Use the source only for SLAIF branding/design cues and
  the verified logo asset.
- Do not hotlink the README logo.
- Do not change GitHub repository settings, Actions policy, branch protection,
  rulesets, secret scanning, push protection, collaborators, secrets,
  environments, releases, or deployments.
- Do not enable CodeQL default setup through the API; the committed advanced
  workflow is the selected setup.
- Do not create a second branch, PR, issue, release, or tag.
- Do not merge or enable auto-merge.

## Requirements

### 1. Vendor and document SLAIF branding

Create `docs/assets/slaif-logo.svg` with exact byte content and SHA-256:

```text
0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08
```

Verify the SVG is well-formed XML and contains no script, event-handler
attribute, external resource reference, or unexpected embedded raster payload.
Do not optimize or reformat it because byte identity is the provenance check.

Create `docs/assets/README.md` recording:

- the official SLAIF source URL;
- the source path in `ulfe-lmi/slaif-api-gateway`;
- the exact SHA-256;
- retrieval/verification date `2026-08-17`;
- that the Gateway repository is Apache-2.0;
- a conservative note that license terms do not grant trademark rights and
  that the SLAIF identity must not imply unauthorized endorsement.

The root README must render the local asset, centered, linked to
`https://www.slaif.si`, with meaningful `alt` text and width only.

### 2. Write the full root README

The README must be useful to a technical evaluator, future contributor,
institutional operator, and product stakeholder. It must synthesize the
architecture rather than copy it wholesale.

Required content:

1. Local SLAIF logo and `# SLAIF Agent-Site` title.
2. Working badges for this repository's `CI` and `CodeQL` workflows, plus an
   Apache-2.0 license badge/link if used.
3. The canonical one-sentence product description.
4. A prominent **Current status** section saying the repository is
   architecture/pre-implementation or pre-alpha, listing what exists now, and
   saying the runnable product stack is not implemented yet.
5. The problem Agent-Site solves and why isolated workspaces matter.
6. The non-negotiable promise: agent-only authority cannot write canonical
   content, manage identities, run SQL/Alembic, alter executable code or
   infrastructure, or publish.
7. The three layers: Agent-Site, Agent-State, and the PyPI dependency
   `agent-cow-postgresql==0.2.0`, frozen with hashes and never a Git/VCS
   production dependency.
8. A concise architecture/workflow diagram showing delegation, isolated
   editing, shared rendering/visual evidence, freeze/review, and human-only
   promotion.
9. Planned capabilities: multi-site administration, site-scoped RBAC,
   configurable content models, normalized composition/Puck, semantic
   REST/OpenAPI and MCP, immutable media, confined Playwright feedback,
   review/promotion, audit, and self-hosted operations.
10. A compact table for the four delegation presets and the hard ceiling that
    no level can publish or edit executable code.
11. The selected technology stack and self-hosting/licensing principles.
12. A clearly labeled **target startup contract—not implemented yet** showing
    the future `docker compose up --build` contract without presenting it as a
    current quickstart.
13. Architecture phases or near-term sequence, clearly separating completed
    preparation from planned product work.
14. A current repository map and a concise planned-monorepo pointer to
    Architecture Section 12.
15. Governance links to `AGENTS.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
    `SECURITY.md`, and `oap/`.
16. CI/CodeQL explanation, including dynamic languages and the fact that green
    preparation checks do not prove product readiness.
17. Self-hosting, privacy, permissive-license, and no-required-hosted-service
    commitments.
18. Apache-2.0 licensing, the EC/EuroHPC JU and Slovenian Ministry of HESI
    acknowledgement for SLAIF grant `101254461`, and the SLAIF project link.

README honesty rules:

- Use present tense only for artifacts actually in the repository.
- Use “planned,” “target,” or equivalent for unimplemented product behavior.
- Do not call the project production-ready, beta, runnable, or feature-complete.
- Do not label currently failing setup commands as a working quickstart.
- Retain the trusted institutional multi-site limitation; do not claim hostile
  public-SaaS isolation.
- Do not claim CodeQL or CI is certification.
- Do not invent maintainers, support SLAs, compatibility, releases, or dates.
- Keep the README materially shorter than `ARCHITECTURE.md` and point there
  for normative detail.
- All relative links and image paths must resolve on the PR head.

### 3. Add security, contribution, notice, and PR guidance

`SECURITY.md` must state the pre-alpha/pre-implementation status, that no
version is production-supported, and that reports should use a private GitHub
Security Advisory at
`https://github.com/ulfe-lmi/slaif-agent-site/security/advisories/new` with
`janez.pers@fe.uni-lj.si` as the public-material fallback. It must prohibit
real credentials/personal or production data, avoid a response SLA, and avoid
claiming certification or penetration testing.

`CONTRIBUTING.md` must cover architecture-first work, mandatory governance
reading, issue/PR and no-direct-main workflow, focused scope, tests/docs,
security, dependency/license review, exact preparation checks, honest skipped
test reporting, no secrets/production access, OAP artifact ownership, and the
current absence of an application setup.

`NOTICE` must identify the project and Apache-2.0 license, record logo
provenance and the conservative trademark/endorsement boundary, record the
planned MIT foundation attribution without claiming it is installed, and
retain the SLAIF funding acknowledgement. Do not invent legal claims.

`.github/pull_request_template.md` must prompt for summary/objective, scope and
non-goals, architecture/security impact, exact validation statuses,
documentation, dependencies/licenses, secrets/production confirmation, an OAP
identifier when applicable, and confirmation that a coding agent never merges
its own OAP PR.

### 4. Add deterministic repository-policy tooling

Create `tools/check_repository.py` using only the Python standard library. It
must have a documented CLI, deterministic output, nonzero status on policy
failure, and focused checks for at least:

- required preparation/workflow files;
- UTF-8 and no merge-conflict markers in tracked preparation text;
- no trailing whitespace except exactly two spaces as Markdown hard breaks;
- exact logo hash and safe well-formed SVG/XML shape;
- README local logo use and resolving required internal links;
- `oap/active` syntax and exactly one matching order;
- at most one report for the active identifier so pre-report CI can pass, and
  exactly one report for each non-active historical order;
- no OAP temporary/publication files;
- every external workflow `uses:` pinned to lowercase 40-hex SHA, while local
  actions remain allowed;
- no `pull_request_target`, `write-all`, or unbounded default write permission;
- once manifests exist, no Git/VCS, direct-URL, local-path, or editable
  `agent-cow-postgresql` dependency.

Do not hardcode `001-a`, a permanent architecture hash, a fixed count of OAP
rounds, or a forever-static repository tree. Document that the checker is not
a complete secret scanner, YAML validator, Markdown parser, or legal analyzer.

Create `tests/repository/test_repository_policy.py` with standard-library
`unittest` and isolated temporary directories. Cover important passing and
failing cases for OAP correlation, logo tampering, Markdown hard breaks versus
invalid trailing whitespace, pinned/unpinned actions, prohibited workflow
triggers/permissions, README links, and forbidden foundation dependency forms.
Tests must not mutate the real repository.

### 5. Add Markdown lint configuration

Create `.markdownlint-cli2.yaml`, keep default rules enabled, and make only
narrowly justified compatibility choices for line length, exact two-space hard
breaks, canonical architecture appendix headings, repeated headings in
separate sections, and the small logo HTML allowlist. Do not disable lint
globally. Local parity command:

```bash
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
```

Do not create a Node manifest or lockfile for this check.

### 6. Add professional CI

Create `.github/workflows/ci.yml` with `pull_request`, `push` to `main`, and
`workflow_dispatch`; workflow-level `contents: read`; concurrency by
workflow/ref with cancellation; `ubuntu-24.04`; explicit timeouts;
`persist-credentials: false`; approved SHA-pinned actions; no secrets; and no
`pull_request_target`.

Required jobs:

1. **Repository policy:** checkout, Python 3.12, compile checker/tests, run
   repository unit tests, then run `python tools/check_repository.py`.
2. **Markdown:** checkout and SHA-pinned markdownlint-cli2 action for all
   `**/*.md`.
3. **Dependency review:** PR-only, approved official SHA-pinned action, fail on
   at least moderate known vulnerability severity, and least-privilege reads.

Do not add placeholder product/database/browser/Compose jobs. README and
contributing guidance must say CI expands with the product skeleton.

### 7. Add advanced CodeQL

Create `.github/workflows/codeql.yml` with `pull_request`, `push` to `main`, a
weekly schedule, and `workflow_dispatch`; least-privilege `contents: read`,
`actions: read`, `packages: read`, and `security-events: write` only where
needed; concurrency; timeouts; `ubuntu-24.04`; and approved SHA pins.

Add a deterministic detection job emitting a JSON matrix from a fixed
allowlist:

- always `actions` while workflow files exist;
- add `python` when `.py` files exist outside generated/vendor directories;
- add `javascript-typescript` when JS/TS source extensions exist outside
  generated/vendor directories.

Analyze the matrix with `fail-fast: false`, `build-mode: none`,
`security-extended` queries, and a distinct category per language. Do not
autobuild, install application dependencies, use secrets, or call external
services. This PR's first run must analyze at least `actions` and `python`.

### 8. Add Dependabot and update AGENTS

Create `.github/dependabot.yml` version 2 with weekly `github-actions` updates
from `/`, sensible grouping, and a bounded PR limit. Do not configure pip/npm
before their manifests exist.

Add a concise preparation-check section to `AGENTS.md` listing:

```bash
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
```

State that GitHub CI and CodeQL on the current PR head are authoritative and
that future product work extends rather than replaces these checks. Preserve
all existing role, architecture, OAP, and no-merge rules.

### 9. Versioned OAP transcript

- Commit this activated order and `oap/active` unchanged with implementation.
- `oap/active` contains logical value `001-a` only.
- Do not edit objective `000` artifacts.
- Atomically publish `oap/reports/001-a-professional-readme-ci-and-codeql.md`.
- The final report-only commit records the literal implementation head and
  `Report publication commit: SELF`, changes only the new report, and is the PR
  head when the coding agent sends FIFO `OK`.

## Acceptance criteria

1. Exactly one new non-draft PR exists with the required title, base, and head;
   no extra branch/PR, issue, release, tag, merge, or auto-merge exists.
2. The final diff contains exactly the seventeen required paths.
3. `ARCHITECTURE.md` and all objective `000` artifacts remain unchanged.
4. The README is comprehensive, architecture-faithful, locally branded, and
   unambiguous about pre-implementation status.
5. All README local links resolve, and CI/CodeQL badge targets are correct.
6. Security, contribution, notice, provenance, and PR guidance are
   professional and mutually consistent.
7. The logo has the required exact hash and passes XML/safety checks.
8. The standard-library policy checker passes and its positive/negative unit
   tests pass without mutating the repository.
9. Markdown lint passes all repository Markdown without blanket disablement.
10. Every external action is pinned to an approved full SHA with release
    comment; CI has least privilege, timeouts, concurrency, and safe triggers.
11. Dependabot maintains GitHub Actions only.
12. CodeQL advanced setup scans `actions` and `python` now and dynamically adds
    `javascript-typescript` when source exists.
13. All CI and CodeQL checks on the final report-containing head are successful
    before strategic merge; none is failed, cancelled, missing, or pending.
14. `oap/active` is `001-a`; unique order/report correlation holds.
15. The final remote head is the report-only `SELF` commit with the reported
    implementation head as first parent.
16. No secret, production access, hosted runtime dependency, product code,
    unapproved license, or architecture drift is introduced.

## Verification required

Run locally and report exact outcomes for:

```bash
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
sha256sum docs/assets/slaif-logo.svg
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
git ls-files .github docs/assets tools tests/repository
```

Also verify Markdown parsing/fences, README links/image, SVG safety, approved
action pins, workflow triggers/permissions/concurrency/timeouts/matrix/queries,
OAP correlation, unchanged objective `000` hashes, focused secret scan, unique
PR identity, PR body/base/head/draft/auto-merge, final report parent/delta, and
a clean synchronized worktree.

Use GitHub itself for workflow syntax and execution. Fix in-scope workflow
failures on the same branch before reporting when possible. If a failure
appears only after the immutable report commit, report truthfully and let the
strategic model issue `001-b`; never rewrite the report or create another PR.

Application/runtime tests are `NOT RUN — not present in this preparation
objective`, never passed.

## Documentation required

Deliver the full README, contributing/security/notice files, logo provenance,
PR template, focused AGENTS update, and immutable OAP transcript. All must
agree on current status and planned versus implemented behavior.

## Safety / security constraints

- Never commit or print real secrets, tokens, cookies, database URLs, private
  keys, personal data, or production data.
- Never use `pull_request_target`, broad workflow permissions, mutable action
  refs, privileged execution of untrusted PR code, or production systems.
- Do not change GitHub settings outside committed workflow/config files.
- Preserve architecture, OAP ownership, no-merge rules, and unrelated work.

## Local execution capability

- Routine local setup and validation are the coding agent's responsibility.
- Passwordless `sudo` is available in the disposable execution VM.
- Safe local Python, Node/npm, workflow, and validation tools may be installed.
- Do not transfer ordinary setup or CI-log inspection to the human/strategic
  model.

## GitHub workflow

1. Verify `origin/main` and objective `000` merge state.
2. Preserve the pre-published order/active pointer.
3. Create `oap/001-readme-ci-codeql` from current `origin/main`.
4. Implement only required preparation files and stage explicit paths only.
5. Run local verification, commit/push implementation, and create exactly one
   non-draft PR.
6. Inspect/fix CI and CodeQL on the same branch.
7. Record the literal implementation head and atomically publish the report.
8. Commit only the report, push, and verify the final `SELF` head/parent.
9. Inspect final-head checks and wait when practical without rewriting the
   report.
10. Send exact FIFO `OK`; never merge or enable auto-merge.

## Required report

Atomically publish exactly:

```text
oap/reports/001-a-professional-readme-ci-and-codeql.md
```

Use the full protocol 1.2 structure. Include exact PR identity, one-PR
evidence, literal implementation head and `SELF`, commit/path scope, README
section/evidence and status honesty, logo provenance/hash/safety, policy tool
and tests, Markdown lint, every action pin, CI/CodeQL configuration and exact
final-head check states, dependency review/Dependabot, all local commands,
application tests as absent/not run, local setup, docs/security/license impact,
scope/safety confirmations, and limitations or pending checks.

Publish atomically, commit the report alone, push it, verify the remote
head/first-parent/report-only delta, then send exactly two ASCII bytes `OK` to
`response.fifo` with no newline.

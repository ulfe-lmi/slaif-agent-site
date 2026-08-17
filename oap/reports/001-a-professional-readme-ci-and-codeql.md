# OAP Coding-Agent Report — 001-a

## Work order

- Identifier: `001-a`
- Work-order file: `oap/orders/001-a-professional-readme-ci-and-codeql.md`
- Numeric objective: `001`
- PR mode: `CREATED_NEW_PR`

## Status

`PARTIAL`

## Executive summary

Created the single required objective `001` branch and PR with the complete
seventeen-path preparation deliverable: architecture-faithful project
documentation, the byte-exact local SLAIF logo and provenance, deterministic
standard-library repository policy and isolated tests, Markdown lint,
SHA-pinned CI, dynamic advanced CodeQL, and GitHub Actions Dependabot.

All required local checks passed. GitHub repository-policy and Markdown jobs
passed, and advanced CodeQL successfully analyzed both `actions` and `python`.
The official dependency-review action failed because the repository Dependency
Graph is disabled. Enabling it is a GitHub repository-setting change expressly
outside this work order, and hiding or weakening the failed action would
violate the merge-gate policy. Acceptance criterion 13 is therefore not met;
the PR remains open and unmerged for strategic resolution.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `2`
- PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/2`
- PR state at report drafting: `OPEN`
- Draft: `false`
- Merge state at report drafting: `UNSTABLE`
- Base branch: `main`
- Head branch: `oap/001-readme-ci-codeql`
- Starting remote SHA: `3e54c65a798ab5c2df6f2498f2197a19cb60520b`
- Implementation head SHA: `4a6f600ca9103fb7bc4c63fab184d83a562e5f9d`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (the literal containing SHA is derived from GitHub)
- Report commit first parent: `4a6f600ca9103fb7bc4c63fab184d83a562e5f9d`
- Implementation commit pushed before the report commit:
  - `4a6f600ca9103fb7bc4c63fab184d83a562e5f9d` — `[OAP 001-a] Add professional repository preparation`
- Created a new PR this turn: yes, exactly PR `#2`
- Amended an existing PR this turn: no
- Additional branch created: no
- Auto-merge enabled: no (`autoMergeRequest: null`)
- Merge performed: `NO`
- Issues created: none
- Releases created: none
- Tags created: none

At the instant this round sends FIFO `OK`, `SELF` is the current remote PR
head. The report commit changes only this report and has the literal
implementation head above as its first parent.

## Changes made

- Replaced the two-line README with a locally branded, materially condensed
  architecture overview for evaluators, contributors, operators, and product
  stakeholders.
- Made pre-alpha/pre-implementation status prominent, separated current
  preparation artifacts from planned product behavior, and retained the
  trusted-institution multi-site limitation.
- Documented the three planned layers, delegation presets and hard ceiling,
  trusted rendering/review flow, selected stack, future startup contract,
  delivery sequence, current repository map, governance, self-hosting,
  privacy, licensing, and funding acknowledgement.
- Vendored the exact official SVG with source, date, hash, Apache-2.0
  provenance, and a conservative trademark/endorsement boundary.
- Added contribution, private vulnerability-reporting, notice, and pull
  request guidance consistent with the architecture and present repository
  state.
- Added a Python standard-library checker for preparation files, UTF-8,
  conflict markers, Markdown trailing whitespace, logo digest/XML safety,
  README logo/links, OAP correlation/publication hygiene, workflow pins and
  permissions, and forbidden foundation dependency forms.
- Added fourteen temporary-directory unit tests covering the checker's
  positive and negative policy cases without mutating the real repository.
- Added Markdown lint configuration with defaults enabled and narrowly
  documented compatibility choices for immutable governance formatting.
- Added SHA-pinned, least-privilege CI for repository policy, Markdown, and
  pull-request dependency review.
- Added advanced CodeQL with fixed-allowlist language detection, no-build
  analysis, `security-extended` queries, and distinct `actions`/`python`
  categories on this head, plus future `javascript-typescript` detection.
- Added weekly GitHub Actions-only Dependabot configuration.
- Added the exact preparation commands to `AGENTS.md` without changing its
  role, product, security, OAP, or no-merge rules.
- Committed strategic-authored `oap/active` and the activated order unchanged.
- Updated the PR body after the implementation-head runs to state the exact
  successes and Dependency Graph blocker rather than leaving checks pending.

## Files changed

The final PR diff contains exactly these seventeen paths:

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

The implementation head contains the first sixteen paths. `SELF` adds only
this report as path seventeen.

## Acceptance-criteria evidence

### Criterion 1 — one correct non-draft PR

- Result: `PASSED`
- Evidence: `gh pr view 2` reported title `[OAP 001] Add professional README,
  CI, and CodeQL`, state `OPEN`, draft `false`, base `main`, head
  `oap/001-readme-ci-codeql`, and `autoMergeRequest: null`. The unique
  head-filtered all-state PR query returned only PR `#2`.

### Criterion 2 — exact seventeen-path final diff

- Result: `PASSED` under the self-containing publication convention
- Evidence: the implementation-head diff lists exactly the sixteen authorized
  pre-report paths. The staged and committed `SELF` delta contains only the
  required report, producing the exact seventeen-path final diff.

### Criterion 3 — immutable architecture and objective 000

- Result: `PASSED`
- Evidence: `git diff --exit-code origin/main --` across `ARCHITECTURE.md`,
  `OAP-COMMUNICATION-coding-agent.md`, and all objective `000` orders/reports
  exited `0`. Preserved SHA-256 values are:
  - architecture: `a6e05a2aa67dcb43d7a4c94ada7037b33a4d1f0202f5f919cc780b2900e390a0`;
  - `000-a` order: `ee63bf4b45f3b5205cb50a843ec4409823fdd0cd1a1a0e476dcf795b303a3f64`;
  - `000-b` order: `5cf4efdb58c6f582e4ccd5e885e0ec95f1374f3dc0b438b3e08a85abffb182e9`;
  - `000-a` report: `35bb5610c8e3a353cc5efc198f89f7a991734d2970e5d6894c2022722fda4cef`;
  - `000-b` report: `3ca1db888c7c66850240590194eb4ef5860a400a6ab94bb601ebc2d8d12aa2ff`.

### Criterion 4 — comprehensive, honest README

- Result: `PASSED`
- Evidence: the 221-line README begins with the canonical product sentence
  and a prominent pre-alpha/pre-implementation section. Present tense is used
  for current preparation artifacts; the runtime, APIs, stack, startup
  contract, and product capabilities are consistently labeled planned or
  target. The README is materially shorter than the 5,965-line architecture.

### Criterion 5 — links, image, and badges

- Result: `PASSED`
- Evidence: repository policy resolved every README local link/image and
  required governance target. The centered image uses
  `docs/assets/slaif-logo.svg`, meaningful alt text, width only, and links to
  `https://www.slaif.si`. CI and CodeQL badge links target the two committed
  workflows in this repository.

### Criterion 6 — professional guidance consistency

- Result: `PASSED`
- Evidence: `CONTRIBUTING.md`, `SECURITY.md`, `NOTICE`, logo provenance, and
  the PR template agree on current status, architecture-first work, private
  reporting, dependency/license review, OAP ownership, exact validation
  statuses, and the no-production/no-secret boundary.

### Criterion 7 — exact safe logo

- Result: `PASSED`
- Evidence: SHA-256 is
  `0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08`.
  XML parsing found an `svg` root and 63 elements, with no script, event
  attribute, embedded raster element, unsafe URI scheme, CSS import, or
  external resource reference.

### Criterion 8 — policy checker and isolated tests

- Result: `PASSED`
- Evidence: compile, fourteen `unittest` cases, and the real-repository policy
  command all exited `0`. Tests used `TemporaryDirectory` fixtures and did not
  mutate the repository.

### Criterion 9 — Markdown lint

- Result: `PASSED`
- Evidence: `markdownlint-cli2` version `0.23.2` with markdownlint `0.41.1`
  linted all fourteen implementation-head Markdown files with zero issues.
  The final report content also passed lint before atomic publication.

### Criterion 10 — pinned safe workflows

- Result: `PASSED`
- Evidence: repository policy accepted every external `uses:` reference only
  at its approved lowercase 40-hex SHA with a release comment. Workflows use
  safe triggers, workflow/job least privilege, cancellation concurrency,
  `ubuntu-24.04`, explicit timeouts, and `persist-credentials: false`; neither
  contains `pull_request_target`, secrets, broad writes, or mutable refs.

Approved revisions present are:

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`
- `github/codeql-action/init@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd # v4.37.7`
- `github/codeql-action/analyze@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd # v4.37.7`
- `actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0`
- `DavidAnson/markdownlint-cli2-action@21c1be1b93ad9ed58fa840aacc3f279cde2a72ff # v24.2.0`

### Criterion 11 — GitHub Actions-only Dependabot

- Result: `PASSED`
- Evidence: `.github/dependabot.yml` is version 2, weekly at `/`, grouped,
  and bounded to five open PRs. It contains no pip or npm ecosystem.

### Criterion 12 — dynamic advanced CodeQL

- Result: `PASSED`
- Evidence: detection and both `Analyze (actions)` and `Analyze (python)` jobs
  succeeded on the implementation head. The deterministic allowlist adds
  `javascript-typescript` only for recognized JS/TS source extensions outside
  generated/vendor directories. Analysis uses `fail-fast: false`,
  `build-mode: none`, `security-extended`, distinct categories, and no
  autobuild or dependency installation.

### Criterion 13 — every final-head CI/CodeQL check successful

- Result: `BLOCKED`
- Evidence: implementation-head Repository policy, Markdown, CodeQL language
  detection, actions analysis, python analysis, and the aggregate CodeQL check
  succeeded. Dependency review failed with GitHub error `Dependency review is
  not supported on this repository. Please ensure that Dependency graph is
  enabled`. The repository SBOM endpoint also returned HTTP `404`. The work
  order forbids changing GitHub settings; no skip, `continue-on-error`, or
  weakened substitute was introduced.

### Criterion 14 — active OAP correlation

- Result: `PASSED`
- Evidence: `oap/active` is exactly logical value `001-a` with SHA-256
  `1615a1a18dcf328b6d268c2dc0d9dabaa16493412b8b57bf9d03de6901422099`.
  The unique activated order has SHA-256
  `c2dfe932b2bf8d448436226aa122e2ececdd88e1372bfc91a9adb9c211863b27`.
  Repository policy accepts at most one active report and exactly one report
  for every historical order; atomic publication creates the one active
  report.

### Criterion 15 — final report-only remote SELF

- Result: `PASSED` under the self-containing publication convention
- Evidence: `SELF` is created with implementation head
  `4a6f600ca9103fb7bc4c63fab184d83a562e5f9d` as first parent and only this
  report in its delta. It is pushed and verified as remote PR head before FIFO
  signaling.

### Criterion 16 — scope and safety

- Result: `PASSED`
- Evidence: no secret-pattern match, production access, hosted runtime
  dependency, product code, manifest, lockfile, unapproved license,
  architecture drift, issue, release, tag, extra branch/PR, merge, or
  auto-merge was introduced.

## Local verification

- `python -m compileall -q tools tests/repository`: `PASSED` (exit `0`).
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: `PASSED`
  (exit `0`; fourteen tests).
- `python tools/check_repository.py`: `PASSED` (exit `0`; `PASS repository policy`).
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: `PASSED` (exit `0`;
  implementation head: fourteen files and zero issues).
- `sha256sum docs/assets/slaif-logo.svg`: `PASSED`; returned the required
  digest `0760613aca18ace80d559686e98ec640f9f85caa163c5338c28e73b57b9c7a08`.
- `git diff --check origin/main...HEAD`: `PASSED` (exit `0`; no output).
- `git diff --name-only origin/main...HEAD`: `PASSED`; listed exactly sixteen
  implementation paths, with `SELF` adding the required report as path
  seventeen.
- `git ls-files .github docs/assets tools tests/repository`: `PASSED`; listed
  the eight expected paths under those roots.
- `pandoc --from=gfm --to=html --output=/dev/null <file>` for every repository
  Markdown file: `PASSED` (exit `0`).
- Ruby standard-library YAML load for both workflows, Dependabot, and
  Markdown lint configuration: `PASSED` (exit `0`). GitHub independently
  parsed and executed both workflows.
- XML-aware logo safety script: `PASSED`; `svg` root, 63 elements, no unsafe
  elements, handlers, references, schemes, CSS import, or external CSS URL.
- Workflow contract assertions for triggers, permissions, concurrency,
  timeouts, dynamic matrix, queries, forbidden constructs, and Dependabot
  ecosystems: `PASSED` (exit `0`).
- Exact staged-scope assertion before implementation commit: `PASSED`; sixteen
  authorized paths.
- `git diff --exit-code origin/main -- <immutable-governance-and-000-paths>`:
  `PASSED` (exit `0`).
- Focused AWS/GitHub-token/private-key/credential-URL diff scan: `PASSED`
  (no match; `rg` exit `1` inside the successful negative assertion).
- `gh pr view 2` and unique head-filtered PR query: `PASSED`; exact title,
  open/non-draft state, base/head, SHA, and null auto-merge; one objective PR.
- Repository issue/release/tag counts: `PASSED`; zero issues, releases, or
  tags were created or present.
- Final `git status --short --branch --untracked-files=all`: verified after
  `SELF` as clean and synchronized before FIFO signaling.
- Application/runtime tests: `NOT RUN — not present in this preparation
  objective`; no product code or application suite exists.

Earlier development iterations were resolved before the implementation
commit: the first unit run found a missing logo fixture in the README-link
test; the corrected fixture produced fourteen passing tests. Markdown lint
first encountered pre-existing root-owned npm cache entries, then identified
immutable-governance compatibility cases; ownership was repaired and narrow
documented rule configuration produced zero issues. A first auxiliary SVG
regex treated the standard W3C namespace URI as an external resource; the
policy check and corrected XML-aware inspection both passed without changing
the byte-exact SVG.

## GitHub CI / required checks

Check state observed for implementation head
`4a6f600ca9103fb7bc4c63fab184d83a562e5f9d`:

- `Repository policy`: `SUCCESS` in CI run `32015503108` (6 seconds).
- `Markdown`: `SUCCESS` in CI run `32015503108` (6 seconds).
- `Dependency review`: `FAILURE` in CI run `32015503108` (4 seconds) because
  the repository Dependency Graph is disabled.
- `Detect supported languages`: `SUCCESS` in CodeQL run `32015502953`
  (4 seconds).
- `Analyze (actions)`: `SUCCESS` in CodeQL run `32015502953` (39 seconds).
- `Analyze (python)`: `SUCCESS` in CodeQL run `32015502953` (43 seconds).
- Aggregate `CodeQL`: `SUCCESS`.
- Overall CI workflow: `FAILURE` solely from Dependency review.
- Overall CodeQL workflow: `SUCCESS`.
- Branch protection required-status configuration: `MISSING`; GitHub returned
  `404 Branch not protected` for `main`.
- All work-order-required checks green for the implementation head: `NO`.
- Report-only commit triggers fresh checks: the strategic model must verify
  `SELF` without rewriting this immutable report. The known Dependency Graph
  condition is expected to keep Dependency review non-successful until an
  authorized repository administrator changes that external setting.

## Local setup / dependencies

- Installed Debian package `python-is-python3` version `3.11.4-1` with `sudo`
  so the work order's literal `python` commands use preinstalled Python
  `3.12.3`.
- Repaired ownership of the exact `/home/ubuntu/.npm` cache tree from the
  root-owned entries reported by npm to local user/group `1000:1000`.
- `npx` `11.14.1` fetched transient `markdownlint-cli2@0.23.2`; no Node
  manifest, lockfile, production dependency, or committed cache was created.
- Preinstalled tools used: Node `24.14.1`, pandoc `3.1.3`, and Ruby `3.2.3`.
- Services started: none.
- Durable setup changes committed/documented: only the ordered preparation
  commands and repository configuration.

## Documentation

Replaced the root README and added contribution, security, notice, provenance,
and PR guidance. Updated only the authorized preparation-check subsection of
`AGENTS.md`. Documentation consistently distinguishes current repository
evidence from the planned runtime, preserves architecture/security claims as
requirements rather than certification, and records logo/license/funding
attribution. `ARCHITECTURE.md` and the OAP protocol are unchanged.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Required tests skipped/not run: application/runtime tests only — `NOT RUN`
  because the preparation-only order prohibits product code and no such suite
  exists. No requested preparation validation was skipped.
- Scope deviation: no.
- New production dependencies: no.
- Hosted/account-bound runtime dependency introduced: no.
- Unapproved license introduced: no.
- Real external service used for tests: no; only GitHub publication/checks and
  official logo-source retrieval were used at their intended boundaries.
- `ARCHITECTURE.md` edited: `NO`.
- Objective `000` artifact edited: `NO`.
- Activated order and `oap/active` edited by coding agent: `NO`.
- Existing report overwritten: `NO`.
- Extra branch created for objective `001`: `NO`.
- Extra PR created for objective `001`: `NO`.
- PR merged by coding agent: `NO`.
- Auto-merge enabled by coding agent: `NO`.
- Report-publication commit changes only this report file: `YES`.

## Known limitations / blockers

- The repository Dependency Graph is disabled. The SHA-pinned official
  dependency-review action therefore fails before it can review the PR. This
  is an external repository-setting blocker, not a dependency finding.
- The coding agent is explicitly forbidden by this work order from changing
  GitHub settings. It also did not mark the step `continue-on-error`, skip the
  action, or substitute a weaker check merely to make CI green.
- Acceptance criterion 13 and the complete execution status remain unmet
  until Dependency review succeeds on the report-containing head. A green
  local suite or CodeQL run is not a substitute.
- The product runtime and all application/database/browser/Compose tests
  remain absent by design in this preparation objective.

## Recommended strategic follow-up

Have an authorized repository administrator decide whether to enable the
GitHub Dependency Graph. If enabled, activate `001-b` so the coding agent can
reconcile the same PR, verify Dependency review and all report-head checks,
and append a correction/completion report without rewriting this immutable
round. Independently verify `SELF`, its first parent and report-only delta;
do not merge while any required check is failed, pending, cancelled, or
missing.

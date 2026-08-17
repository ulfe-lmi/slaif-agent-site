# OAP Coding-Agent Report — 002-a

## Work order

- Identifier: `002-a`
- Work-order file: `oap/orders/002-a-fix-mermaid-diagrams-and-add-render-validation.md`
- Numeric objective: `002`
- PR mode: `CREATED_NEW_PR`

## Status

`COMPLETE`

## Executive summary

Created the single required objective `002` branch and PR from accepted remote
`main`. Repaired the two broken architecture sequence diagrams through exactly
three syntax-only `;` to `#59;` encodings, preserving rendered message text and
every Architecture Revision 2.1 decision. Added a deterministic
standard-library checker that finds and renders every repository Mermaid fence
with exact Mermaid CLI `11.16.0` entirely in temporary storage.

Added ten isolated Mermaid tests, extended repository action/path policy, and
added a dedicated least-privilege CI job using Node 24 and the approved
setup-node pin. The first hosted-runner attempt exposed that Puppeteer's
downloaded headless shell lacked a usable sandbox under Ubuntu 24.04. The
in-scope repair selects the runner's preinstalled sandboxed Google Chrome; it
does not use `--no-sandbox`. The implementation-head CI rerun then rendered all
twelve repository diagrams successfully, and every CI/CodeQL check passed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `3`
- PR URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/3`
- PR state at report drafting: `OPEN`
- Draft: `false`
- Mergeable: `MERGEABLE`
- Merge state at report drafting: `CLEAN`
- Base branch: `main`
- Head branch: `oap/002-fix-mermaid-rendering`
- Starting remote SHA: `644e3a091936fd6e245c22a2d1d7642f86cb922d`
- Implementation head SHA: `d268534a21b99f07759fbe1e555120127de34757`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF` (the literal containing SHA is derived from GitHub)
- Report commit first parent: `d268534a21b99f07759fbe1e555120127de34757`
- Implementation commits pushed before the report commit:
  - `6fbb4e92c4aad97dd66393def48db54f23906a91` — `[OAP 002-a] Validate Mermaid rendering`
  - `d268534a21b99f07759fbe1e555120127de34757` — `[OAP 002-a] Use sandboxed runner Chrome`
- Created a new PR this turn: yes, exactly PR `#3`
- Amended an existing PR this turn: no
- Additional branch created: no
- Auto-merge enabled: no (`autoMergeRequest: null`)
- Merge performed: `NO`
- Issue, release, tag, or deployment created: no

At the instant this round sends FIFO `OK`, `SELF` is the current remote PR
head. Its first parent and single-report-path delta are verified before
signaling.

## Changes made

- Replaced the three literal sequence-message semicolons at architecture
  Mermaid opening-fence regions 16.7/16.8 with `#59;` entities:
  - `AC->>C: assert capability still active#59; consume budget`
  - `CAPI->>C: revoke capability#59; mark FREEZING`
  - `W->>C: increment site revision#59; mark ACCEPTED#59; audit snapshot digest`
- Added `tools/check_mermaid.py`, which discovers repository Markdown with
  generated/cache/environment exclusions, extracts exact normalized
  `mermaid` fences with source-line locations, rejects unclosed fences before
  rendering, and uses argument-list subprocess invocation without a shell.
- The checker transiently invokes
  `npx --yes @mermaid-js/mermaid-cli@11.16.0`, writes `.mmd` inputs and `.svg`
  outputs only beneath an automatically removed system temporary directory,
  bounds/normalizes renderer diagnostics, and produces a stable success
  summary.
- Added ten `TemporaryDirectory`-based tests for discovery exclusions,
  multiple-fence extraction and line numbers, non-Mermaid exclusion, unclosed
  fences, no-diagram behavior, exact command construction, renderer success,
  renderer failures and bounded diagnostics, missing output, temporary
  confinement, and source immutability.
- Extended repository policy with the new required tool/test and approved
  `actions/setup-node` SHA.
- Added the separate `Mermaid` CI job with read-only inherited permissions,
  `ubuntu-24.04`, a 15-minute timeout, pinned checkout/setup-python/setup-node,
  Python 3.12, Node 24, no credentials persistence, and no cache/artifact or
  write action.
- Pointed Puppeteer on the hosted runner to `/usr/bin/google-chrome`, the
  runner-image-provided sandboxed browser, after the downloaded headless shell
  proved incompatible with the runner's AppArmor/user-namespace policy.
- Added the exact durable command to `AGENTS.md` and `CONTRIBUTING.md`, and
  documented its transient/no-output/no-production-dependency behavior.
- Updated only the README CI paragraph to include exact-version Mermaid
  rendering while preserving pre-implementation honesty.
- Committed strategic-authored `oap/active` and the activated order unchanged.

## Files changed

The final PR diff against `main` contains exactly these eleven paths:

```text
.github/workflows/ci.yml
AGENTS.md
ARCHITECTURE.md
CONTRIBUTING.md
README.md
oap/active
oap/orders/002-a-fix-mermaid-diagrams-and-add-render-validation.md
oap/reports/002-a-fix-mermaid-diagrams-and-add-render-validation.md
tests/repository/test_mermaid.py
tools/check_mermaid.py
tools/check_repository.py
```

The implementation head contains the first ten paths. `SELF` adds only this
report as path eleven.

## Architecture repair and render evidence

Byte construction from `git show origin/main:ARCHITECTURE.md` applied only the
three required old/new byte pairs and exactly matched the working
`ARCHITECTURE.md`. The Git numstat is three insertions and three deletions.
Original architecture SHA-256 is
`a6e05a2aa67dcb43d7a4c94ada7037b33a4d1f0202f5f919cc780b2900e390a0`;
repaired SHA-256 is
`813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`.

Revision remains `2.1` and date remains `2026-08-17`. Participants, arrows,
messages, prose, title, decisions, and revision history are unchanged. After
removing the three `#59;` entity tokens for measurement, raw semicolon count
inside all Mermaid content is zero.

Exact Mermaid CLI `11.16.0` successfully rendered every architecture fence:

- `ARCHITECTURE.md:477`: `PASSED`
- `ARCHITECTURE.md:624`: `PASSED`
- `ARCHITECTURE.md:652`: `PASSED`
- `ARCHITECTURE.md:1023`: `PASSED`
- `ARCHITECTURE.md:1301`: `PASSED`
- `ARCHITECTURE.md:1749` (Section 16.7): `PASSED`
- `ARCHITECTURE.md:1775` (Section 16.8): `PASSED`
- `ARCHITECTURE.md:1904`: `PASSED`
- `ARCHITECTURE.md:2806`: `PASSED`
- `ARCHITECTURE.md:3912`: `PASSED`
- `ARCHITECTURE.md:5396`: `PASSED`

The same every-fence repository gate also rendered `README.md:58`: `PASSED`.
Thus all eleven architecture diagrams and all twelve current repository
diagrams passed. GitHub's cold-run Mermaid log independently printed:
`PASS Mermaid rendering: 12 diagram(s) in 2 file(s); 18 Markdown file(s)
scanned; CLI 11.16.0`.

## Mermaid package evidence

`npm view @mermaid-js/mermaid-cli@11.16.0 version license engines
dist.integrity dist.tarball --json` returned:

- version: `11.16.0`
- license: `MIT`
- Node engine: `^18.19 || >=20.0`
- integrity:
  `sha512-0InK2nbVIMtzVzCugmdvPkAuvS6wRUqU6Utntff1n8c7lgfRZAdhKY6PSKvcIK9nFmuOUzAgB5+x/XWcroZ7Zg==`
- tarball:
  `https://registry.npmjs.org/@mermaid-js/mermaid-cli/-/mermaid-cli-11.16.0.tgz`

The package is an approved transient MIT-licensed documentation-validation
tool. No Node manifest, lockfile, package tree, browser, cache, or rendered
output is tracked, and it is not a product/runtime dependency.

## Acceptance-criteria evidence

### Criterion 1 — exactly one correct new PR

- Result: `PASSED`
- Evidence: PR `#3` is the only all-state PR for the objective head, `OPEN`,
  non-draft, `MERGEABLE`, and `CLEAN`, with exact title, base `main`, head
  `oap/002-fix-mermaid-rendering`, and `autoMergeRequest: null`.

### Criterion 2 — exact eleven-path final diff

- Result: `PASSED` under the self-containing publication convention
- Evidence: implementation head has exactly ten pre-report paths. `SELF` adds
  only this report, producing exactly the eleven ordered paths.

### Criterion 3 — exact syntax-only architecture diff

- Result: `PASSED`
- Evidence: byte-level reconstruction and `git diff` show only the three
  mandated `;` to `#59;` replacements in Sections 16.7/16.8. Revision, date,
  semantics, wording, participants, arrows, prose, and history are unchanged.

### Criterion 4 — no raw Mermaid semicolon

- Result: `PASSED`
- Evidence: standard-library extraction found twelve repository Mermaid
  blocks; after excluding the three required entity terminators, raw
  semicolon count is zero.

### Criterion 5 — all architecture diagrams render

- Result: `PASSED`
- Evidence: local and GitHub exact-version runs rendered all eleven
  architecture diagrams. The repository-wide gate also rendered the README
  diagram, twelve total.

### Criterion 6 — diagnostic quality and temporary confinement

- Result: `PASSED`
- Evidence: tests verify path/opening-line extraction, unclosed-fence
  preflight, source-bound renderer errors, bounded output with random temp
  paths normalized, output existence, source byte immutability, paths outside
  the repository, and automatic cleanup. Focused scans found no repository
  `.mmd`, output SVG beyond the pre-existing logo, Node tree, manifest, or
  lockfile.

### Criterion 7 — Mermaid and repository tests

- Result: `PASSED`
- Evidence: ten new Mermaid tests and fourteen existing repository-policy
  tests ran under normal discovery; all 24 passed.

### Criterion 8 — safe pinned Mermaid CI

- Result: `PASSED`
- Evidence: the dedicated `Mermaid` job succeeded on GitHub with Node 24,
  Python 3.12, `ubuntu-24.04`, 15-minute timeout, inherited `contents: read`,
  `persist-credentials: false`, sandboxed system Chrome, and exact
  `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0`.
  Existing jobs and pins remain mandatory and unchanged.

### Criterion 9 — durable honest guidance

- Result: `PASSED`
- Evidence: README, AGENTS, and contributing guidance document the exact
  rendering check, transient exact CLI, temporary outputs, and absence of a
  production dependency. Product readiness is not claimed.

### Criterion 10 — every implementation-head CI/CodeQL check

- Result: `PASSED`
- Evidence: Repository policy, Markdown, Mermaid, Dependency review, Detect
  supported languages, Analyze (actions), Analyze (python), and aggregate
  CodeQL all completed with `SUCCESS`. Report-only checks are inspected after
  immutable publication without rewriting this report.

### Criterion 11 — CodeQL alerts

- Result: `PASSED`
- Evidence: the open code-scanning-alert API query returned count `0` after
  successful actions/python analysis.

### Criterion 12 — active OAP and immutable history

- Result: `PASSED`
- Evidence: `oap/active` is logical `002-a` with SHA-256
  `08c07120a52c62f5de320c046b90d8a1a313ded310c8bd8c0b3b7c2f9daeb904`.
  The unique order SHA-256 is
  `ea2439569ed87baf6a74816f2da8f9571796c81f0bc12ed8b35ae1bf2ca80e8c`.
  Focused diffs prove all objective `000`/`001` orders and reports plus the
  OAP communication protocol unchanged; policy accepts complete correlation.

### Criterion 13 — final report-only SELF

- Result: `PASSED` under the self-containing publication convention
- Evidence: `SELF` is created with implementation head
  `d268534a21b99f07759fbe1e555120127de34757` as first parent and only this
  report in its delta. It is pushed and verified as remote PR head before FIFO
  signaling.

### Criterion 14 — scope and safety

- Result: `PASSED`
- Evidence: no secret, production access, product dependency, manifest,
  lockfile, committed render/browser/cache output, license drift, architecture
  drift, unrelated change, extra PR/branch, issue, release, tag, deployment,
  merge, auto-merge, or setting change occurred.

## Local verification

- `python -m compileall -q tools tests/repository`: `PASSED` (exit `0`).
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: `PASSED`
  (exit `0`; 24 tests).
- `python tools/check_repository.py`: `PASSED` (exit `0`; `PASS repository policy`).
- `python tools/check_mermaid.py`: `PASSED` (exit `0`; twelve diagrams in two
  files, eighteen Markdown files scanned, CLI `11.16.0`).
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: `PASSED` (exit `0`;
  eighteen files, zero issues).
- `git diff --check origin/main...HEAD`: `PASSED` (exit `0`; no output).
- `git diff --name-only origin/main...HEAD`: `PASSED`; exactly ten
  implementation paths, with `SELF` adding only the required report.
- `npm view @mermaid-js/mermaid-cli@11.16.0 version license engines dist.integrity dist.tarball --json`:
  `PASSED`; exact metadata is recorded above.
- Exact architecture byte-reconstruction, three-pair replacement, 3/3
  numstat, revision/date, eleven-fence, twelve-repository-fence, and zero-raw-
  semicolon assertions: `PASSED`.
- `pandoc --from=gfm --to=html --output=/dev/null <file>` for every repository
  Markdown file: `PASSED`.
- Ruby standard-library YAML parse for the amended CI workflow: `PASSED`.
- Workflow contract assertions for Mermaid name/image/timeout, Node 24,
  setup-node SHA, read-only permissions, credential confinement, sandboxed
  Chrome, and absence of `--no-sandbox`, `pull_request_target`,
  `continue-on-error`, cache/artifact actions, broad writes, and secrets:
  `PASSED`.
- Exact staged-scope assertion: `PASSED`; ten pre-report paths.
- Focused prior-OAP/protocol immutable diff: `PASSED` (exit `0`).
- Temporary/artifact scan: `PASSED`; no surviving renderer temporary
  directory, repository `.mmd`, Node tree, manifest, or lockfile; only the
  pre-existing vendored SLAIF logo SVG exists.
- Focused AWS/GitHub-token/private-key/credential-URL diff scan: `PASSED`
  (no match; `rg` exit `1` inside the successful negative assertion).
- PR identity/uniqueness/body/base/head/draft/auto-merge and issue/release/tag
  counts: `PASSED`; exactly PR `#3`, and zero issues/releases/tags.
- Final `git status --short --branch --untracked-files=all`: verified after
  `SELF` as clean and synchronized before FIFO signaling.
- Application/runtime tests: `NOT RUN — not present`; Mermaid rendering is
  documentation validation, not product testing.

Two development failures were resolved before this report. The first cold
local render used a 60-second per-render timeout; npm was still obtaining the
exact CLI/Puppeteer package, so two renders timed out and the killed transient
npx directory caused ten later `ENOENT` failures. That exact cache directory
was moved to a system-temporary quarantine, the cold-start allowance was
bounded at five minutes, and repeated clean runs passed all twelve diagrams.
No repository artifact was created.

The first GitHub Mermaid job (CI run `32018551098`, job `95353120596`) then
failed all twelve browser launches with `No usable sandbox` because the
downloaded headless shell could not use Ubuntu 24.04's restricted user
namespaces. The repair selected the official hosted runner image's
preinstalled `/usr/bin/google-chrome`; no browser sandbox was disabled. The
next cold-run job passed all twelve renders in 38 seconds.

## GitHub CI / required checks

Check state observed for implementation head
`d268534a21b99f07759fbe1e555120127de34757`:

- CI run `32018692716`: `SUCCESS`.
- `Repository policy`: `SUCCESS`, job `95353534217`, 6 seconds.
- `Markdown`: `SUCCESS`, job `95353534257`, 5 seconds.
- `Mermaid`: `SUCCESS`, job `95353534304`, 38 seconds.
- `Dependency review`: `SUCCESS`, job `95353534340`, 7 seconds.
- CodeQL run `32018692612`: `SUCCESS`.
- `Detect supported languages`: `SUCCESS`, job `95353533572`, 5 seconds.
- `Analyze (actions)`: `SUCCESS`, job `95353565710`, 41 seconds.
- `Analyze (python)`: `SUCCESS`, job `95353565688`, 46 seconds.
- Aggregate `CodeQL`: `SUCCESS`, 3 seconds.
- Open CodeQL alerts: `0`.
- All work-order-required checks green for the implementation head: `YES`.
- Report-only commit triggers fresh checks: those are inspected to completion
  before FIFO signaling, without rewriting this immutable report. The
  strategic model must independently verify literal `SELF` checks before
  acceptance or merge.

## Action pins and CI contract

- `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
- `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0`
- `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0`
- `DavidAnson/markdownlint-cli2-action@21c1be1b93ad9ed58fa840aacc3f279cde2a72ff # v24.2.0`
- `actions/dependency-review-action@a1d282b36b6f3519aa1f3fc636f609c47dddb294 # v5.0.0`
- `github/codeql-action/init@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd # v4.37.7`
- `github/codeql-action/analyze@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd # v4.37.7`

Repository policy accepted every external action at its approved full SHA and
release comment. Existing CI and CodeQL triggers, permissions, concurrency,
timeouts, language matrix, queries, and dependency review remain unchanged;
the new job adds no write permission, secret, cache action, artifact upload,
or mutable reference.

## Local setup / dependencies

- Packages installed with the system package manager: none.
- `sudo`-level setup performed: none.
- `npx` transiently obtained Mermaid CLI `11.16.0`, its npm dependencies, and
  Puppeteer browser data in user caches outside the repository. No package was
  installed into or declared by the project.
- The incomplete exact npx cache directory from the killed first cold install
  was moved to
  `/tmp/slaif-mermaid-npx-quarantine.sljDTu/bf675e4b8f9df2c5`; it is disposable,
  outside the repository, and not used by successful verification.
- Preinstalled tools used: Python `3.12.3`, Node `24.14.1`, npm/npx `11.14.1`,
  markdownlint-cli2 `0.23.2`, pandoc `3.1.3`, and Ruby `3.2.3`.
- GitHub used its hosted `ubuntu-24.04` image, setup Node 24, transient npx
  package data, and preinstalled sandboxed Google Chrome; no output artifact
  or cache action was configured.
- New production dependency, manifest, lockfile, committed browser/cache, or
  service: none.

## Documentation

Made the minimal syntax-only architecture render repair without revising
Revision 2.1 history. Added the exact durable Mermaid command and transient
behavior to AGENTS/contributing guidance, and added Mermaid rendering to the
README CI description without changing readiness claims. Added the immutable
order and this report. No other product, security, architecture, setup, or
operations documentation changed.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- GitHub setting changed: no.
- Required tests skipped/not run: application/runtime tests only — `NOT RUN`
  because no such product code/suite exists; no documentation validation was
  skipped.
- Scope deviation: only the in-scope workflow browser selection required by a
  real hosted-runner failure; it preserved rather than disabled sandboxing.
- Architecture semantics/revision/date changed: no.
- New product dependency/manifest/lockfile/license drift: no.
- Browser sandbox disabled: no.
- Rendered output, npm cache, browser download, or temporary extraction file
  committed: no.
- Existing workflow/check weakened or removed: no.
- Objective `000`/`001` artifact or OAP protocol edited: no.
- Activated order or `oap/active` edited by coding agent: no.
- Existing report overwritten: no.
- Extra branch or PR created: no.
- Issue, release, tag, deployment, merge, or auto-merge created/performed:
  `NO`.
- Report-publication commit changes only this report file: `YES`.

## Known limitations / blockers

- The runnable product and application/database/browser/Compose tests remain
  absent by design. Mermaid rendering is a documentation syntax/render gate,
  not product readiness or security certification.
- Transient npm/Puppeteer downloads occur in the runner/user cache and are not
  reproducible project installations; package identity is fixed by exact
  version and verified registry integrity, with no manifest or lockfile by
  explicit work-order design.
- Report-head checks run only after immutable `SELF` publication. They are
  inspected before FIFO signaling and must be successful before strategic
  acceptance or merge.

## Recommended strategic follow-up

Resolve `SELF` to the literal remote PR head, verify its first parent is
`d268534a21b99f07759fbe1e555120127de34757`, confirm the report-only delta and
exact eleven-path final scope, independently inspect every report-head CI and
CodeQL check plus zero open alerts, and then decide acceptance or merge. The
coding agent did not merge or enable auto-merge.

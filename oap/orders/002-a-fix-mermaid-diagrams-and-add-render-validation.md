# OAP Work Order — 002-a

## Objective

Create exactly one new GitHub pull request that fixes the two broken Mermaid
sequence diagrams in `ARCHITECTURE.md` and makes Mermaid rendering a permanent,
deterministic CI gate for every Mermaid block in repository Markdown.

The architecture semantics and Revision 2.1 designation must not change. The
diagram repair is a syntax-only encoding of three literal semicolons using the
Mermaid-required `#59;` entity.

## GitHub objective state

- Numeric objective: `002`
- Execution round: `002-a`
- PR mode: `CREATE_NEW_PR`
- Existing PR: N/A
- Required head branch: `oap/002-fix-mermaid-rendering`
- Base branch: `main`
- Required PR title: `[OAP 002] Fix architecture diagrams and validate Mermaid`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`
- Repository URL: `https://github.com/ulfe-lmi/slaif-agent-site`

## Strategic context

The human observed GitHub rich-display parse failures in:

- Section 16.7, “Transaction flow for an agent write”; and
- Section 16.8, “Transaction flow for promotion.”

GitHub reported the first parse failures immediately after message-text
semicolons. Mermaid sequence-diagram grammar permits semicolons as statement
separators, so Mermaid's official documentation requires a literal semicolon
inside message text to be encoded as:

```text
#59;
```

An independent scan found exactly three raw semicolons inside all Mermaid
blocks, all in the two reported sequence diagrams:

```text
AC->>C: assert capability still active; consume budget
CAPI->>C: revoke capability; mark FREEZING
W->>C: increment site revision; mark ACCEPTED; audit snapshot digest
```

The third semicolon-bearing line in the promotion flow would fail after the
earlier parser error was removed, so all three message-text semicolons must be
escaped in one correction.

GitHub supports Mermaid fenced diagrams in Markdown, but repository CI did not
previously parse/render them. This objective adds a regression gate using the
current exact Mermaid CLI package version.

## Current verified state

The strategic model independently verified before activation:

- Remote default branch: `main`
- Remote `main` SHA:
  `644e3a091936fd6e245c22a2d1d7642f86cb922d`
- Objective `001` PR `#2` is merged and remote `main` contains its accepted
  README, CI, CodeQL, policy tooling, and complete OAP transcript.
- Open pull requests: none
- Post-merge `main` CI: success
- Post-merge `main` CodeQL: success for `actions` and `python`
- Initial Dependabot update run: success
- Open CodeQL alerts: zero
- Current merged OAP active identifier: `001-b`
- `ARCHITECTURE.md` contains eleven Mermaid fenced blocks.
- Exactly three raw semicolons occur inside Mermaid fences, at current lines
  1763, 1785, and 1805; all are sequence-diagram message text in Sections
  16.7/16.8.
- No Mermaid rendering job or Mermaid-specific repository tool/test exists.

If remote state changes materially, reconcile without broadening scope and
never create a duplicate objective PR.

## Approved tool and action revisions

Use:

```text
@mermaid-js/mermaid-cli@11.16.0
```

Verified package metadata on 2026-08-17:

```text
license: MIT
Node engines: ^18.19 or >=20.0
integrity: sha512-0InK2nbVIMtzVzCugmdvPkAuvS6wRUqU6Utntff1n8c7lgfRZAdhKY6PSKvcIK9nFmuOUzAgB5+x/XWcroZ7Zg==
tarball: https://registry.npmjs.org/@mermaid-js/mermaid-cli/-/mermaid-cli-11.16.0.tgz
```

Add this approved immutable action reference to CI and repository policy:

```text
actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0
```

Retain every existing action pin unchanged unless a real incompatibility is
proven and reported.

## Required final tracked paths

The final PR diff against `main` must contain exactly these eleven paths:

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

Do not commit rendered SVG/PNG outputs, npm caches, package manifests,
lockfiles, browser downloads, coverage, or temporary extraction files.

## Scope

1. Fix the three literal semicolons in the two failing architecture diagrams
   with Mermaid entity encoding.
2. Add a standard-library Python tool that extracts and renders all Mermaid
   fences through an exact-version Mermaid CLI in a temporary directory.
3. Add isolated unit tests for extraction, diagnostics, and renderer handling.
4. Extend repository policy for the new tool/test and approved setup-node pin.
5. Add a dedicated Mermaid CI job.
6. Document the exact Mermaid validation command in AGENTS, contributing
   guidance, and the README's CI description.
7. Publish the complete versioned OAP transcript and create exactly one new
   non-draft PR.

## Non-goals

- Do not change architecture meaning, requirements, decisions, revision
  number, date, title, prose, diagram participants, arrows, or message wording.
- Do not replace semicolons with “and” or punctuation that changes displayed
  text; use `#59;` so rendered labels retain literal semicolons.
- Do not edit any Mermaid block other than the three exact message-text
  replacements unless the pinned renderer reveals another actual syntax
  failure; if it does, report and make only the smallest syntax-preserving fix.
- Do not edit objective `000` or `001` orders/reports.
- Do not change application architecture, CI security posture, CodeQL,
  Dependency Review, Dependabot, license policy, or GitHub settings.
- Do not add application/runtime code or dependencies.
- Do not add a Node package manifest or lockfile for this transient CI tool.
- Do not create a second branch/PR, issue, release, tag, deployment, merge, or
  auto-merge.

## Requirements

### 1. Minimal architecture syntax repair

Make exactly these semantic-preserving source replacements:

```text
AC->>C: assert capability still active#59; consume budget
CAPI->>C: revoke capability#59; mark FREEZING
W->>C: increment site revision#59; mark ACCEPTED#59; audit snapshot digest
```

Acceptance for the architecture diff:

- exactly three raw `;` characters inside Mermaid fences are replaced with
  `#59;`;
- no other architecture byte changes;
- no raw semicolon remains inside a Mermaid fenced block;
- all eleven Mermaid blocks render successfully;
- Revision remains `2.1` and date remains `2026-08-17`.

### 2. Add `tools/check_mermaid.py`

Implement a deterministic standard-library Python CLI that:

- discovers Markdown files under a configurable repository root while
  excluding `.git`, caches, generated/build output, virtual environments,
  `node_modules`, and vendor directories;
- extracts every fenced block whose info string is exactly `mermaid` after
  normal fence/whitespace normalization;
- records source Markdown path and opening line for diagnostics;
- detects and reports an unclosed Mermaid fence before invoking a renderer;
- writes extracted `.mmd` inputs and renderer outputs only in a temporary
  directory outside tracked source;
- invokes exact `@mermaid-js/mermaid-cli@11.16.0` through `npx --yes` without a
  project package manifest;
- validates every block and returns nonzero if extraction or any render fails;
- includes the source file/line and bounded renderer stderr/stdout in failures;
- returns a concise deterministic success summary including files and diagram
  count;
- supports `--root PATH` and a unit-testable separation between discovery,
  extraction, command construction, and execution;
- does not use shell interpolation for subprocess arguments;
- does not leave output/cache files in the repository.

The renderer is authoritative for syntax. The tool may additionally detect raw
sequence-message semicolons as a clearer preflight diagnostic, but must not
implement a misleading partial Mermaid grammar.

### 3. Add isolated tests

Create `tests/repository/test_mermaid.py` using standard-library `unittest`,
temporary directories, and subprocess mocking/fakes where appropriate.

Cover at least:

- extraction of multiple Mermaid fences with correct source line numbers;
- ignoring non-Mermaid fences;
- unclosed Mermaid fence failure;
- no-diagram behavior;
- deterministic command using exact version `11.16.0` and argument list;
- renderer success and failure diagnostics;
- output confined to a temporary directory;
- no mutation of source Markdown or the real repository.

The normal repository unittest discovery command must include these tests.

### 4. Extend `tools/check_repository.py`

- Add `tools/check_mermaid.py` and
  `tests/repository/test_mermaid.py` to required preparation files.
- Add `actions/setup-node` at the exact approved SHA to `APPROVED_ACTIONS`.
- Preserve existing checks and tests.
- Do not make the general repository-policy checker invoke npm/Chromium; the
  dedicated Mermaid CI job owns external rendering.

### 5. Add the Mermaid CI job

Extend `.github/workflows/ci.yml` with a separate job named `Mermaid` that:

- runs on `ubuntu-24.04` with an explicit reasonable timeout;
- inherits/read-confines `contents: read`;
- uses existing SHA-pinned checkout with `persist-credentials: false`;
- uses existing SHA-pinned setup-python for Python 3.12;
- uses the approved SHA-pinned setup-node v7 for Node 24;
- runs `python tools/check_mermaid.py`;
- uses no secret, write permission, cache write, `pull_request_target`,
  artifact upload, or committed render output.

The existing Repository policy, Markdown, and Dependency review jobs remain
mandatory and unchanged except where repository policy legitimately needs the
new approved action/tool paths.

### 6. Update durable contributor guidance

Add the exact command:

```bash
python tools/check_mermaid.py
```

to the preparation-check lists in `AGENTS.md` and `CONTRIBUTING.md`. Explain
that it transiently obtains the exact Mermaid CLI version and renders every
Mermaid fence; it does not add a production dependency or commit outputs.

Update the README's CI paragraph to say CI validates Mermaid rendering. Keep
the README's pre-implementation honesty and all architecture/security claims
unchanged.

### 7. Versioned OAP transcript

- Commit this order and strategic `oap/active` unchanged.
- `oap/active` contains logical value `002-a` only.
- Atomically publish exactly
  `oap/reports/002-a-fix-mermaid-diagrams-and-add-render-validation.md`.
- Record the literal implementation head and
  `Report publication commit: SELF`.
- The final report commit changes only the report and is the remote PR head
  when exact FIFO `OK` is sent.

## Acceptance criteria

1. Exactly one new non-draft PR exists with the required title, base, and head;
   no extra branch/PR, merge, or auto-merge is created.
2. Final PR diff contains exactly the eleven required paths.
3. The architecture diff is exactly three `;` to `#59;` replacements inside
   Sections 16.7/16.8 and no semantic/revision/date change.
4. No raw semicolon remains in any Mermaid fence.
5. All eleven current Mermaid blocks render successfully with exact
   Mermaid CLI `11.16.0`.
6. The checker reports useful source-file/line diagnostics and leaves no
   repository artifacts.
7. Mermaid unit tests cover positive and negative behavior and all repository
   policy tests pass.
8. CI contains a safe, least-privilege, SHA-pinned `Mermaid` job using Node 24
   and setup-node v7.0.0 at the approved commit.
9. README, AGENTS, and contributing guidance document the new durable check
   without claiming product readiness or a runtime dependency.
10. Every final-head CI check succeeds, including Repository policy,
    Markdown, Mermaid, Dependency review, CodeQL detection, Actions analysis,
    Python analysis, and aggregate CodeQL.
11. Open CodeQL alerts are reported honestly.
12. `oap/active` is `002-a`, with unique order/report correlation and all
    earlier OAP artifacts unchanged.
13. Final remote head is the report-only `SELF` commit with the report's
    implementation head as first parent.
14. No secret, production access, product dependency, manifest, lockfile,
    committed render output, license drift, or architecture drift occurs.

## Verification required

Run locally and report exact outcomes for:

```bash
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
git diff --check origin/main...HEAD
git diff --name-only origin/main...HEAD
```

Also verify and report:

- npm metadata for Mermaid CLI version/license/engine/integrity;
- exact three-line architecture diff and absence of other architecture bytes;
- Mermaid fence count and raw-semicolon count;
- all rendered diagram outputs created only under a temporary directory and
  removed automatically;
- setup-node and all existing action pins/comments;
- workflow triggers/permissions/concurrency/timeouts and no forbidden
  constructs;
- Markdown parsing and fence balance;
- OAP active/correlation and immutable prior artifacts;
- focused secret scan;
- PR uniqueness/body/base/head/draft/auto-merge;
- every final-head GitHub check and CodeQL alert state;
- final report commit parent/report-only delta;
- clean synchronized working tree.

Application/runtime tests remain `NOT RUN — not present`; Mermaid rendering is
documentation validation, not product testing.

## Documentation required

- Minimal `ARCHITECTURE.md` syntax repair.
- README CI description update.
- AGENTS and contribution check-command updates.
- Immutable OAP order/report.

Do not update architecture revision history for a syntax-only render repair.

## Safety / security constraints

- Never commit secrets, credentials, cookies, database URLs, private keys,
  personal data, browser profiles, npm caches, or downloaded browser binaries.
- Use exact package/action versions and no mutable workflow refs.
- Do not grant workflow write permission or access production systems.
- Do not weaken existing CI/CodeQL/Dependency Review/OAP boundaries.
- Preserve unrelated work and all prior immutable evidence.

## Local execution capability

- Routine Node/Python/Chromium setup and rendering are the coding agent's
  responsibility in the disposable VM.
- Passwordless `sudo` is available when safe and necessary.
- Do not transfer ordinary setup, Mermaid validation, or CI-log inspection to
  the human or strategic model.

## GitHub workflow

1. Verify current `origin/main`, no existing objective `002` PR, and clean
   accepted objective `001` state.
2. Preserve the pre-published order/active pointer and create the required new
   branch from current remote main.
3. Make only the allowed changes and stage explicit paths.
4. Run all local checks, commit/push implementation, and create exactly one
   non-draft PR.
5. Inspect/fix every CI and CodeQL failure on the same branch.
6. Record the literal implementation head and atomically publish the report.
7. Commit only the report, push it, verify `SELF`, and inspect final-head
   checks before exact FIFO `OK`.
8. Never merge, auto-merge, or create another PR.

## Required report

Use the full protocol 1.2 report structure. Include exact PR/commit/path
identity; the three architecture replacements; all eleven render results;
Mermaid CLI version/license/engine/integrity; extractor/test/tool behavior;
action pins and CI contract; local commands; final-head CI/CodeQL results;
OAP hashes/correlation; application tests as absent/not run; setup performed;
documentation/license impact; and every scope/safety/no-extra-PR/no-merge
confirmation.

Publish atomically, commit the report alone, push it, verify the remote
head/first-parent/report-only delta, then send exactly two ASCII bytes `OK` to
`response.fifo` with no newline.

# OAP Work Order — 010-j

## Objective

Amend PR `#15` to restore a fully green report head and implement the human's
README logo request. Match the SLAIF API Gateway README's logo positioning and
size while retaining the local reviewed asset, add one exact lint exclusion for
the already-published malformed `010-i` report without editing it, and make
pre-publication report linting a durable coding-agent protocol requirement.

This is Markdown/OAP governance and README presentation only. Do not change
session/product behavior, dependencies, migrations, routes, UI application,
Compose, or another feature.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-j`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch/base: `oap/010-installation-local-auth` / `main`
- Current main: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `ce7d5998482d25bf09621f7d61cd9100181fcf8d`
- `010-i` implementation head:
  `239a135394492f3dac3a665ddd6fb844a708d6f1`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective PR. No new PR, rebase, force-push, merge,
close, auto-merge, or unrelated action.

## Verified state and reference

The `010-i` implementation head is fully green, including the complete local
session/lifecycle proof, PostgreSQL 14–18, and Compose. Its immutable report
commit fails only GitHub Markdown because the report omitted blank lines after
headings. OAP immutability forbids editing that published report.

The requested reference is the default-branch README of
`ulfe-lmi/slaif-api-gateway`, fetched at blob
`bbb06a732fee5cb92eedb3d88ce913646c21f889`. Its opening structure is:

```html
<div style="text-align: center;">
  <a href="https://www.slaif.si">
    <img ... width="400" height="400">
  </a>
</div>

# Project title
```

Agent-Site must match that position, centering mechanism, and `400×400` size,
but keep `docs/assets/slaif-logo.svg` and its meaningful alt text; do not switch
to a remote image.

## Allowed scope

```text
README.md
.markdownlint-cli2.yaml
OAP-COMMUNICATION-coding-agent.md
oap/strategic-instructions/OAP-COMMUNICATION-coding-agent.md
tools/check_repository.py
tests/repository/test_repository_policy.py
oap/active
oap/orders/010-j-readme-logo-and-report-lint-guard.md
oap/reports/010-j-readme-logo-and-report-lint-guard.md
```

Use the minimum subset. Do not edit any earlier order/report, including
`oap/reports/010-i-qualify-session-finalizer-update.md`.

## Moderate autonomy and completion rule

- Target: 25 minutes; hard stop: 45 minutes.
- Diagnose and correct in-scope Markdown/policy/test failures until the complete
  local checks pass; no arbitrary attempt cap and no unchanged blind reruns.
- One initial GitHub implementation generation is expected. One corrective
  code push/generation is allowed only for an in-scope clean-checkout issue;
  never invoke workflow rerun.
- Do not publish the report until its own final Markdown content passes the
  repository rules locally.

## Requirements

### 1. README logo layout

Move the logo block before the `# SLAIF Agent-Site` heading. Use exact centered
wrapper semantics `<div style="text-align: center;">`, retain the SLAIF link,
local `docs/assets/slaif-logo.svg`, and meaningful alt text, and set both
`width="400"` and `height="400"`. Keep badges and all remaining README content
in their existing order after the H1. Do not alter the SVG bytes/hash.

Update the repository checker and tests to require: local logo asset; SLAIF
link; meaningful alt; exact 400×400 dimensions; centered div wrapper; logo
before first H1; no external image. Preserve link-resolution and asset hash/
active-content checks.

Update Markdownlint's allowed HTML elements narrowly for the new `div`, `a`,
and `img` structure; remove the now-unused root-logo `p` allowance if no other
tracked source requires it.

### 2. Preserve immutable report and restore lint

Do not edit the malformed published `010-i` report. Add exactly its repository
path to `.markdownlint-cli2.yaml` `ignores`, with a comment explaining the OAP
immutability exception. Do not ignore `oap/reports/**`, all OAP files, a glob,
or any other report. Add a repository-policy regression that rejects a broad
reports ignore and requires the single exact historical exception while it is
needed.

### 3. Prevent recurrence before report publication

Update root `OAP-COMMUNICATION-coding-agent.md` and its archived mirror
byte-for-byte to require this sequence before atomic report publication:

```text
finish complete report content in a same-filesystem temporary file
run Markdownlint --no-globs on that exact temporary/final-content path
correct every finding before atomic rename
only then publish, commit, push, and signal
```

A known-failing report may not be published merely because later strategy can
repair CI. Historical immutable-report exceptions require an explicit
strategic order and exact-path ignore; coding agent never adds one itself.

The `010-j` report itself must include proper blank lines after every heading
and pass this new pre-publication check before rename/commit.

## Observable acceptance criteria

1. GitHub renders a centered local SLAIF logo before the H1 at 400×400, matching
   the referenced positioning/size while retaining alt text and local asset.
2. Full `ARCHITECTURE.md`, compact architecture, SVG, and all historical OAP
   bytes except no file at all are unchanged; specifically `010-i` remains
   byte-identical.
3. Markdownlint ignores exactly the one immutable malformed report, not a
   directory/glob; full clean-checkout Markdown CI passes.
4. Repository policy/tests enforce the new logo contract and narrow historical
   exception without weakening other checks.
5. Root/archive coding communication files are byte-identical and require
   report lint before publication.
6. No product/session/dependency/migration/route/UI/Compose behavior changes.
7. Exactly PR #15 is amended; all 20 checks on the new report head pass, no
   workflow rerun, and report-only `SELF` parentage is correct.

## Verification required

Run repository unittest/policy, Markdownlint on all tracked clean-checkout
sources or an equivalent clean worktree, explicit `--no-globs` lint of the
future report content, link/logo policy tests, SVG hash/safety, compile,
`git diff --check`, exact allowed paths, protocol-mirror hash, prior-report hash,
and architecture/SVG hashes. Run no DB, Compose, supply-chain/image, Node, or
browser locally; GitHub runs the complete gate.

## Safety, workflow, and report

No secrets/production resources. Preserve all governance/architecture/OAP and
product code. Amend only the existing PR branch; never merge or create another
PR. Atomically publish exactly:

```text
oap/reports/010-j-readme-logo-and-report-lint-guard.md
```

Lint its exact completed content before publication. The report-only `SELF`
commit must parent the literal implementation head. Report markup/policy/
protocol diffs, exact immutable hashes, local checks, all 20 report-head checks,
any materially distinct corrections, no-workflow-rerun/no-new-PR/no-merge
state, and `Report publication commit: SELF`.

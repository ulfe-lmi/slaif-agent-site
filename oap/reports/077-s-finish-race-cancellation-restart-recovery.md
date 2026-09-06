# OAP Coding-Agent Report — 077-s

## Work order

- Identifier: `077-s`
- Work-order file: `oap/orders/077-s-finish-race-cancellation-restart-recovery.md`
- Work-order SHA-256: `37398b417331a870bc38a7ec4d367149c71b618febdf71a6602633d376d01d98`
- Active SHA-256: `520d2bea544ae1b28e797b3ab7962a61113690f4d348f017d0d4189f3bb99552`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The 077-r structural race, post-tentative locale cancellation, actual Render
lifespan restart, causal snapshot, and dependency-lock repairs are complete.
The substantive failure was a transient `P0002` escaping from
`content.slaif_redirect_page_target_dependency` while it iterated a COW-hidden
or tombstoned candidate row. The exception was translated as
`RESOURCE_NOT_FOUND` for the page delete even though the page remained at
workspace row version 1 and a fresh trusted COW transaction could delete it.

Migration 055 now skips only that hidden/tombstoned iterator row on
`P0002`, while genuine page absence and other validation failures remain
fail-closed. The pre-070 migration history is byte-immutable; the shared human
editor lifecycle-lock replacement is applied by migration 055. No broad
exception handling or public diagnostic leakage was added.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `eb82a11ae7cc98a981e63c4d4fd9adf0234159a1`
- Literal implementation head SHA:
  `0d72cc2b61d235b119e569b22e7c2f53e5388103`
- Implementation parent:
  `f2466ddaf6168606042e94596080a5ed645479b2`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Preserved the completed common workspace lifecycle and structural/type
  dependency pre-locking, including the shared human-editor lifecycle lock.
- Added the 055 redirect dependency helper repair for COW-hidden/tombstoned
  iterator rows and preserved owner-only function execution.
- Added the post-tentative locale cancellation proof using the production Agent
  HTTP executor, including same-key retry.
- Added the real Render app/database-adapter stop/start proof through the
  internal HTTP routes, with authorization, no-store/noindex, site/workspace
  confinement, and clean connection-context assertions.
- Corrected the causal preview proof to execute an actual page-resolution query
  before pausing, await all durable Agent commits, then release the snapshot;
  retained the canonical and `READ COMMITTED` negative controls.
- Added deterministic page/redirect serialization-order proofs:
  redirect-update-first gives page-delete `200`; page-delete-first gives
  `409`, then redirect update `200`, with the page retained.
- Updated bounded migration-head, readiness, and distribution-file contracts;
  restored the immutable pre-070 migration byte hash and added the shared-lock
  replacement in migration 055.

## Acceptance-criteria evidence

### Structural page/redirect race

- Exact originating failure: `P0002` from
  `content.slaif_agent_page_effective_route`, called by
  `content.slaif_redirect_page_target_dependency` while examining a
  concurrently hidden/tombstoned COW iterator row.
- Root cause: the iterator-row exception escaped as top-level page absence,
  producing `404 RESOURCE_NOT_FOUND` although the page change still existed.
- Repair: migration `055_001_redirect_dependency_cow_tombstone.py` catches
  only `SQLSTATE P0002` inside that candidate-row loop and continues; it does
  not catch genuine top-level absence or unrelated exceptions.
- Deterministic redirect-first order: redirect update `200`, page delete
  `200`.
- Deterministic page-delete-first order: page delete `409`, redirect update
  `200`, page remains readable `200`.
- Existing cross-interface structural suite and the final focused production
  test passed; no dangling redirect edge, hidden identifier, or invalid winner
  is accepted.

### Causal snapshot and negative controls

- Actual paused page-resolution query runs before the durable Agent page,
  navigation, and redirect commits are awaited.
- The repeatable-read preview returns the complete before-state; fresh preview
  returns the complete after-state and redirect.
- Canonical snapshot remains before-state, then observes the committed redirect.
- The explicit `READ COMMITTED` control observes the staged mixed state and is
  retained only as a negative control.

### Cancellation and restart

- Post-tentative locale cancellation occurs after the production locale SQL
  wrapper and graph validation return, before generic idempotency completion
  and audit.
- Cancellation leaves target/former-default locale state, effective routes,
  navigation, redirects, quotas, idempotency, audit, and COW residue at the
  exact pre-request counts/state; retry with the identical key returns `200`
  exactly once with the expected row versions and audit/quota effects.
- The Render integration uses real public/preview PostgreSQL pools and two
  separate production app/database-adapter lifespan instances. Both starts
  render the durable human-authorized overlay and canonical page through the
  internal HTTP route; connection state is clean after stop/restart.

### Security and packaging preservation

- No capability, cookie, credential, internal URL, or production data was
  exposed.
- Pre-070 migration byte hash for `028_001_human_editor_workspace_envelope.py`
  remains
  `9a3083fe2bcba7e871c4fddbb560f154181ba0968884f2c11205246d9d870eb3`.
- Supply-chain evidence: 6 images, 0 Critical, 42 High; checksum,
  reproducibility, clean Compose images, Ubuntu Apache parity, Postgres
  `libcurl=8.22.0-r0`, and immutable scanner-image checks passed.

## Verification

- Focused structural order test: `1 passed in 15.08s`.
- Full backend integration at final production head before the final test-only
  assertion addition: `170 passed in 1405.68s (0:23:25)`.
- Python unit/repository suite: `522 passed`, one existing Starlette deprecation
  warning.
- `uv lock --check`: passed.
- `uv sync --frozen --all-groups`: passed.
- Ruff check/format, mypy: passed; mypy checked 255 source files.
- Python build: wheel and sdist passed bounded distribution contracts.
- Repository preparation: 58 repository unit tests passed; repository policy
  passed; 16 Mermaid diagrams in 3 files rendered; Markdownlint 397 files,
  0 issues.
- Node: Node `v24.14.1`, pnpm `11.22.0`; frozen install, lint, format check,
  typecheck, tests, build, and license inventory passed.
- Local supply-chain policy/evidence tests: 35 passed; full evidence gate
  passed with `images=6 critical=0 high=42`.
- Current PR head `0d72cc2b61d235b119e569b22e7c2f53e5388103` required checks:
  Repository policy, Node contracts, Python 3.12/3.13/3.14, Foundation
  PostgreSQL 14/15/16/17/18, Compose and edge packaging, Supply-chain
  evidence, Markdown, Mermaid, Dependency review, and CodeQL all `SUCCESS`.
  PR merge state is `CLEAN`; PR remains open and unmerged.

## Scope, safety, and completion boundary

- No strategy order, active file, historical report, architecture document, or
  constitution was rewritten; the new order and active bytes are committed
  unchanged with the implementation.
- No new PR, merge, auto-merge, release, issue closure, feature, cleanup,
  refactor, media/MCP/freeze/review/promotion work, 078 work, or unrelated
  hardening was performed.
- No exception, scanner suppression, severity override, weakened validation,
  or broad lock-policy weakening was used.
- Implementation is complete and the coding agent will not merge PR #74.

Objective 077 / PR #74 is eligible for strategic completion only when the
strategy independently reviews this report and accepts the bounded evidence;
the PR must remain at the verified green head, and strategy must perform any
authorized merge decision. The coding agent has completed the exact 077-s
order and has no remaining implementation blocker.

No extra PR was created. No merge or auto-merge was performed.

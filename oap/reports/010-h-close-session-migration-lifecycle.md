# OAP Coding-Agent Report — 010-h

## Work order

- Identifier: `010-h`
- Work-order file: `oap/orders/010-h-close-session-migration-lifecycle.md`
- Numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Added the missing deterministic downgrade of
`control.slaif_revoke_human_session(text, bytea, bytea)` and a static symmetry
regression covering all five created functions. The fresh migration lifecycle
now completes locally through rebuild and upgrade. The focused session proof
reaches the inspect/compare/finalizer path but fails inside the safe finalizer;
the service intentionally converts the underlying database error to the stable
`HumanSessionError`. GitHub reproduces that failure on PostgreSQL 14–18. The
order’s two database invocations and one implementation commit are exhausted,
so this round is truthfully `PARTIAL`.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- State: `OPEN`, non-draft, `MERGEABLE`, merge state `UNSTABLE`
- Base/head: `main` / `oap/010-installation-local-auth`
- Starting remote PR/report head: `4d05eb07f7984b5d538833e003af630a018c5b91`
- Implementation head SHA: `27bf6378af12b906c85aff383614e1f03cc46882`
- Report publication commit: SELF
- No merge, force-push, auto-merge, close, or extra PR performed.

## Changes made

- Added the missing revoke-function drop to `010_001.downgrade()` before the
  session table drop.
- Added strict static coverage that every one of the five created session
  functions has a corresponding downgrade drop.
- Corrected disposable focused-test timing fixtures and added explicit idle
  expiry coverage; no runtime semantics were changed in this round.

## Acceptance-criteria evidence

1. **Downgrade symmetry:** local lifecycle portion passed in the first combined
   invocation; the stale-function defect is fixed in the pushed implementation.
2. **Fresh lifecycle and privilege validation:** first combined command ran the
   bootstrap lifecycle and session test; bootstrap completed successfully. The
   session test then failed in the finalizer. Static privilege/inventory tests
   passed.
3. **Complete session proof:** exactly two post-fix session invocations were
   used. The first failed at the touch fixture before the final fixture repair;
   the second reached `authenticate()` and failed at the safe finalizer’s
   redacted database error. No third invocation was made.
4. **CI matrix:** updated PostgreSQL 14–18 jobs all ran both bootstrap and
   session tests. All five failed at the same safe-finalizer
   `HumanSessionError`; no rerun occurred.
5. **Scope:** only the ordered migration, static regression, focused fixture,
   order, active pointer, and report changed. Compose, CI wiring, runtime
   semantics, dependencies, routes, UI, and docs were untouched.

## Local verification

- `uv run --frozen ruff format --check ...`: PASSED.
- `uv run --frozen ruff check ...`: PASSED.
- `uv run --frozen mypy`: PASSED — 80 files.
- `uv run --frozen pytest -q services/backend/tests/unit/test_foundation_contract.py services/backend/tests/unit/test_sessions.py services/backend/tests/unit/test_control_database.py`: PASSED — 38 tests.
- `uv run --frozen pytest -q services/backend/tests/integration/test_database_bootstrap.py services/backend/tests/integration/test_human_session.py`: one combined invocation; bootstrap lifecycle passed, session failed at finalizer.
- Second and final `uv run --frozen pytest -q services/backend/tests/integration/test_human_session.py`: FAILED at the same finalizer error; no further database invocation permitted.
- Compile, repository policy, Markdownlint, broad Compose, Node, browser, and
  supply-chain checks: NOT RUN in this order unless covered by GitHub.
- `git diff --check`: PASSED.

## GitHub CI / required checks

Single authorized generation: CI `32399482661`, CodeQL `32399482776`; no
workflow rerun.

- SUCCESS: Python 3.12/3.13/3.14 quality/package, Node contracts, Repository
  policy, Markdown, Mermaid, Dependency review, Supply-chain evidence, Compose
  and edge packaging, and CodeQL.
- FAILURE: Foundation PostgreSQL 14, 15, 16, 17, and 18. Each ran 23 passing
  bootstrap tests and then failed the session test with
  `HumanSessionError: Human session unavailable` from the safe finalizer path.
- All jobs completed; no pending/cancelled job is presented as passing.

## Documentation and setup

No dependencies or packages were installed or changed. No documentation was
needed for this migration-only correction; prior session documentation remains
unchanged and accurate about absent HTTP/UI/authentication routes.

## Hashes and protocol evidence

- Activated order SHA256: `133a3964e0782f43d2a7a8ae34daca73154350496af396ab9124e445e131a9c0`
- Root `AGENTS.md`: `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`: `ffa3e2bf7998c1274543dc76f22f4b19655d2d209fdbde2a020eff8fa47d83b8`
- `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Full `ARCHITECTURE.md` source hash (not loaded): `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- Prior 010-g implementation/report preserved: implementation
  `e133a090b7271983679ce5369f9c4155bdb2c89a`, report
  `4d05eb07f7984b5d538833e003af630a018c5b91`.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production systems/credentials/secrets/capability tokens/cookies/private
  URLs: NOT accessed or committed.
- Extra objective PR: NO. Coding-agent merge/acceptance: NO.
- Active pointer and order content: committed unchanged.
- Final report commit: changes only this report and has implementation SHA as
  its first parent.

## Limitation / strategic follow-up

The remaining blocker is the redacted database error raised by
`slaif_finalize_human_session` after a successful inspect and constant-time
comparison. A continuation must diagnose that SQL/finalizer result shape or
privilege issue with the permitted database evidence; no further attempt or
implementation commit was authorized in this round.

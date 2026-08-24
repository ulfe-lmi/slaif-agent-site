# OAP Coding-Agent Report — 071-c

## Work order

- Identifier: `071-c`
- Work-order file: `oap/orders/071-c-render-session-lock-and-recent-auth.md`
- Numeric objective: `071`; round: `071-c`
- PR mode: `AMENDED_EXISTING_PR`
- Scope: one forward migration and direct PostgreSQL proof correcting Render
  preview touch semantics and workspace lock chronology.

## Status

COMPLETE

## Executive summary

Objective 071-c is complete on the existing PR #62. Migration `034_001`
replaces only the Render preview authorization function. It acquires the
shared workspace advisory transaction lock immediately after bounded argument
validation and before inspecting or locking session/workspace/account/site or
membership state. It then preserves all prior authority checks under that
lock.

Preview touch now updates only `last_seen_at`. It never renews, extends,
synthesizes, or changes `recent_auth_at`; the returned `recent_auth` result is
computed from the persisted timestamp and configured recent-auth window.

Real PostgreSQL proof demonstrates stale touch remains non-recent across
repeated reads, genuinely recent auth remains unchanged and recent, revocation
can commit while preview waits on the exclusive workspace lock without a row
lock inversion, the resumed authorization denies, and the COW projection holds
the shared lock through response completion. Full backend, Node, Compose,
PostgreSQL 14–18, CodeQL, and supply-chain gates are green. No merge was
performed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#62](https://github.com/ulfe-lmi/slaif-agent-site/pull/62)
- State: `OPEN`, non-draft, `MERGEABLE`
- Base/head: `main` / `oap/071-render-api-page-preview`
- Starting remote report head:
  `536d175703e4ba52814d5a216bf4998ca1fc80d6`
- Implementation head SHA: `f4bdc795d31b3eee980df50c250300997c46a248`
- Implementation parent: `536d175703e4ba52814d5a216bf4998ca1fc80d6`
- Remote PR head before report publication:
  `f4bdc795d31b3eee980df50c250300997c46a248`
- Existing PR amended: YES; extra PR: NO
- Merge or auto-merge: NO

Transcript bytes committed unchanged in the implementation commit:

- `oap/active` is exactly `071-c\n`; SHA-256:
  `059bdb41bf3fba15cce6ea02ac5e6ea8ed9cf7627c684b0587188a93f826e8cc`.
- `oap/orders/071-c-render-session-lock-and-recent-auth.md` SHA-256:
  `e48e9a27ed9e16848a7d5fb068b08b9bca6206186a2d6822f46887ddc98feba7`.
- The immutable 071-b report remains unchanged; SHA-256:
  `20d2bb163de6dbf2c978da0a650e86952d6e205994b3d412907340155a540eec`.

## Changes made

### Migration 034

- Added `034_001_render_preview_lock_order.py`, down-revising from
  `033_001`, with one linear Alembic head.
- The new function keeps the exact seven-argument signature, owner,
  `SECURITY DEFINER`, fixed `search_path`, `PUBLIC` revoke, and
  `slaif_preview_reader` execute grant.
- It rejects null/invalid IDs, digest shape, session policy values, and public
  ID shape before taking the workspace shared advisory transaction lock.
- It validates active account/site/session/workspace, idle and absolute expiry,
  revocation, HUMAN/AGENT/IMPORT actor type, creator/read-all, and
  preview-inspect authority only after the shared lock is held.
- Touch updates only `last_seen_at`; the downgrade body intentionally restores
  the prior 033 behavior for migration reversibility.
- Prior migrations 006–033 were not edited.

### Deterministic real-role proof

Added `test_render_preview_session_lock.py` with real PostgreSQL, owner,
preview-reader, public-reader, and COW connections:

1. A stale session has `last_seen_at` older than the touch interval and
   `recent_auth_at` older than the recent-auth window. Preview succeeds,
   advances `last_seen_at`, leaves `recent_auth_at` exactly equal, and returns
   `recent_auth = false`. A repeated preview remains false and unchanged.
2. A genuinely recent session remains byte/time identical while returning
   `recent_auth = true`.
3. One owner connection holds the exclusive workspace advisory transaction
   lock. Preview authorization waits in `pg_stat_activity` on an advisory
   lock. A second owner connection successfully revokes the session while the
   preview is waiting, demonstrating no session-row lock inversion. Releasing
   the exclusive lock makes preview deny, with page-change, dirty-table,
   idempotency, and audit counts unchanged.
4. A real `RenderProjectionService` preview is paused inside projection after
   in-transaction reauthorization. An owner exclusive-lock request is observed
   waiting; it completes only after projection response completion releases
   the shared COW transaction lock.

The existing 071-b preview expiry, post-authorization race, AGENT/IMPORT,
multi-site, collection, route, service-secret, and browser proofs remain
unchanged and green.

## Files changed

- `oap/active`
- `oap/orders/071-c-render-session-lock-and-recent-auth.md`
- `services/backend/src/slaif_agent_site/db/alembic/versions/034_001_render_preview_lock_order.py`
- `services/backend/tests/integration/test_render_preview_session_lock.py`
- migration-head/readiness expectations in the existing database tests
- `docs/API.md`, `docs/DATABASE_CONNECTIONS.md`, and `docs/SECURITY.md`

No production dependency, lockfile, renderer, route, browser, media, or
privilege-surface redesign was made.

## Acceptance-criteria evidence

### Preview reads cannot renew recent authentication

PASSED. The real preview role/wrapper test records exact timestamps before and
after stale and recent reads. Stale reads return false repeatedly and preserve
the same `recent_auth_at`; recent reads return true and also preserve the same
timestamp. Only `last_seen_at` advances when its touch interval requires it.

### Lock-first mutable authorization

PASSED. The explicit advisory waiter is observed before session inspection.
While preview waits, a second owner connection commits revocation without
waiting on the session row. After the exclusive lock releases, preview
returns no authorization row. This test fails the old row-first chronology
rather than relying on timing-only sleeps.

### COW lock lifetime and residue

PASSED. The real projection is paused after the shared-lock recheck; an owner
exclusive lock is observed waiting until projection completes. The denial
path leaves page changes, COW dirty tables, editor idempotency, and audit
counts unchanged. Existing pool cleanup and cancellation/exception tests
remain green.

### Least privilege and regression

PASSED. The seven-argument function identity and exact grants remain intact;
the migration graph has sole head `034_001`. Existing canonical/preview,
workspace, media, editor, agent, route, browser, and package contracts remain
green.

## Local verification

- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED; 218 files formatted.
- `uv run --frozen mypy`: PASSED; 206 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED; 437 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED; 107
  tests in 446.46 seconds.
- Focused Render/control/lock integration suite: PASSED; 8 tests.
- Focused lock proof: PASSED; 1 test in 5.48 seconds.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`:
  PASSED; 54 tests.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python tools/check_mermaid.py`: PASSED; 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED; 224 files.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-071c`: PASSED;
  source distribution and wheel built.
- All ten backend process `--check` commands: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED, including E2E TypeScript.
- `pnpm test`: PASSED.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `uv run --frozen python -m tools.supply_chain.reproducible`:
  PASSED locally; `reproducibility: OK`.
- `sudo sh tools/compose/smoke.sh slaif071c`: PASSED; final
  `compose-smoke: OK`, `compose-e2e: OK projects=9`, preview browser proof,
  all six stable devices, edge/secret/role/readiness/recovery/negative
  bootstrap/Apache/packaging checks.

## GitHub CI / required checks

Fresh checks were observed for implementation head
`f4bdc795d31b3eee980df50c250300997c46a248`:

- SUCCESS: Repository policy
- SUCCESS: Detect supported languages
- SUCCESS: Analyze (actions), Analyze (python), Analyze (javascript-typescript)
- SUCCESS: CodeQL
- SUCCESS: Node contracts
- SUCCESS: Python 3.12, 3.13, and 3.14 quality/package
- SUCCESS: Foundation PostgreSQL 14, 15, 16, 17, and 18
- SUCCESS: Compose and edge packaging
- SUCCESS: Supply-chain evidence
- SUCCESS: Markdown
- SUCCESS: Mermaid
- SUCCESS: Dependency review

All checks were completed successfully; none were pending, failed, cancelled,
missing, or skipped at report drafting. CI workflow `32776639083` first
reported a Supply-chain reproducibility failure (`Web/browser normalized
output manifests differ`) after the functional matrix passed. Local exact
reproduction passed, and rerunning only the failed CI job completed SUCCESS
after 6m09s. The first local Compose attempt failed before containers due to a
Docker snapshot export error (`parent snapshot ... does not exist`); the clean
retry passed. The first focused test run caught an unqualified PL/pgSQL touch
column ambiguity; the test proof initially also used the wrong
`agentcow.cow_dirty_tables` schema and released a blocked preview connection
before awaiting it. Those bounded implementation/test corrections were fixed
and the final focused/full suites passed. No failure was hidden or weakened.

## Local setup / dependencies

Routine PostgreSQL, Docker/Compose, package, and browser setup used the
existing passwordless privileged path (`sudo sh`) because the shell user lacks
direct Docker-socket permission. No production system, production credential,
host credential store, or unrelated data was accessed. No dependency or
lockfile change was made.

## Documentation

Updated API, database-connection, and security documentation to state the
lock-first chronology and that preview touch updates only `last_seen_at`.
071-a/071-b orders and reports remain immutable.

## Safety and scope confirmations

- Unrelated files changed: NO.
- Production secrets/systems accessed: NO.
- Required tests skipped/not run: NO for the claimed final local and CI sets.
- Scope deviation: NO.
- Extra objective PR: NO; PR #62 is the sole Objective 071 PR.
- Merge/auto-merge: NO.
- Activated order/active edited: NO; exact strategic bytes were committed.
- Report commit changes only this new report: YES.

## Known limitations / blockers

None for 071-c. Review/freeze/promotion/publication, browser-worker
automation, and public-media finalization remain outside this order.

## Recommended strategic follow-up

Strategy should independently review the migration, lock chronology,
immutable transcript, report ancestry, PR checks, and evidence, then decide
whether to accept/merge PR #62. Coding does not merge or choose the next
objective.

## Report publication

Implementation head SHA: `f4bdc795d31b3eee980df50c250300997c46a248`

Report publication commit: SELF

The report-only commit must have the implementation head above as its sole
first parent, contain only this report, be pushed to PR #62, verified as the
remote PR head, and only then signal the exact response FIFO `OK`.

RESULT=COMPLETE

# 083-13-b — bind heading effects to a completed operation and prove the write boundary

- Order: `oap/orders/083-13-b-complete-heading-effect-binding.md`
  (8611B, SHA256 `af4644cf392b8d6e7c5b60db06e6582cbd6af2350cdafc04a582421073214293`,
  committed byte-exact with this round's `oap/active` = `083-13-b`).
- Mode: `AMENDED_EXISTING_PR` — PR 119
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/119> (OPEN/DRAFT),
  branch `oap/083-13-a-heading-row-facts`, base `main`
  `eadca4e2c279d2e1dda8917a24058841a2ed9f93` (PR #118 merge).
- Starting remote head: `c0c2c7d2417a9447de4d09a329582c8dfd39fecb`
  (the immutable 083-13-a report commit, verified via
  `git ls-remote` before mutation; its sole implementation parent is
  `fd084fa777c0a0e88366399c9db595c44c4e2d87`, carried byte-exact).
- Implementation head SHA: `93ac0160ab540b4538d3e63f49fdc8ac3b3d422c`
- Report publication commit: SELF
- Result: COMPLETE for the 083-13-b contract: all four required
  corrections are implemented and natively proven on the explicitly
  owned disposable PostgreSQL 18 fixture, every frozen local gate is
  native-pass at the implementation head, and the full GitHub CI
  matrix on the implementation head is green (subjects identified
  exactly below).

## Pushed commits

1. `87d5a124e43cd339d198e35ec14deb2d99258c41` — 083-13-a
   implementation (carried unchanged).
2. `fd084fa777c0a0e88366399c9db595c44c4e2d87` — 083-13-a
   bounded 063-final re-emission repair (carried unchanged).
3. `93ac0160ab540b4538d3e63f49fdc8ac3b3d422c` — `oap(083-13-b): bind heading effects to completed 078 operations and prove the real write, rollback, race, and scoping boundaries` (this round's bounded changes: unmerged 080 migration, the two focused test files, the narrowly affected docs, and the b order + active bytes; sole parent the starting report head, whose sole implementation parent is the carried a head).

## Cumulative diff vs base (26 paths, +4302/-61), grouped by actual purpose

The 26 implementation paths are the 25 a implementation
paths (net +4153/-61 vs base) plus this round's b order file
(+149 lines, byte-for-byte the activated order). For comparison,
the b order cites the a branch head as "26 paths, 2705
insertions and 61 deletions" — that figure additionally counts
the 342-line a report file (2363+342=2705).

All a paths remain (a report, unchanged); the b contributions,
grouped by purpose, are:

- **Commit-time completion binding (product, 1 path)**
  `services/backend/src/slaif_agent_site/db/alembic/versions/080_001_heading_row_effect.py`:
  the new owner-only, `SECURITY DEFINER`,
  `search_path = pg_catalog` deferred check
  `control.slaif_heading_row_effect_completion_check()` plus the
  `DEFERRABLE INITIALLY DEFERRED` `AFTER INSERT` constraint trigger
  `heading_row_effect_completion_binding` on `audit.heading_row_effect`.
  At COMMIT (not at insert time) the exact new fact must be bound to a
  genuine completed 078 `audit.mutation_completion` row with matching
  operation/family/site/workspace/resource type and ID and completed
  disposition, the exact family audit row
  (`audit.agent_mutation` / `audit.human_editor_mutation`), and the
  exact completed reservation evidence
  (`control.agent_idempotency.status_code` /
  `control.human_editor_idempotency.status_code`); agent rows require
  the capability-bound `human_user_id IS NULL` pairing and
  `composition_node`, editor rows the `capability_id IS NULL` +
  matching human pairing and the `editor.sites` family resource
  classifier. Any missing or mismatched completion raises
  `HEADING_EFFECT_COMPLETION_UNBOUND` (`P0001`) and rolls back the
  entire staged bundle (COW change, family audit, completion, fact).
  No EXECUTE grant is added; no runtime role gains any direct access
  to the fact or its image input. The editor writer re-emission is
  additionally scoped to item 4 below. All earlier a bytes of the
  migration (facts table, record helper, grants, ratchet) are
  preserved.
- **Pilot-scope record correction (same product path)**: the editor
  branch records a heading props fact only when the same-statement
  `props_before IS DISTINCT FROM props_after` (an actual distinct
  pair), and only for the session's own `actor_type = 'AGENT'` COW
  workspace (Human-on-Agent); the earlier validation snapshot is no
  longer the record/no-record oracle, and the ordinary Human
  workspace path's legacy behavior is untouched.
- **Focused integration module (test, 1 path)**
  `services/backend/tests/integration/test_heading_row_effects.py`:
  four new real native tests
  (`test_missing_completion_refuses_commit_and_leaves_no_residue`,
  `test_agent_late_failure_rolls_back_staged_write_and_fact`,
  `test_editor_late_cancellation_rolls_back_staged_write_and_fact`,
  `test_editor_unchanged_props_and_structural_only_record_no_fact`),
  and the two first-write race tests
  (`test_agent_first_write_race_real_command`,
  `test_editor_first_write_race_real_command`) replaced by real
  in-command race witnesses that observe the exact native blocking
  edge and the resolved publication order (item 3 evidence below).
  Module total: 12 tests.
- **Direct-call authority test repair (test, 1 path)**
  `services/backend/tests/integration/test_agent_mutations.py`: the
  runtime-authority test's direct definer Heading call now performs
  the real trusted completion
  (`control.slaif_agent_idempotency_complete`) in the same
  transaction and asserts the committed fact is bound to that exact
  completed 078 operation; the pre-b positive path (commit with an
  in-progress reservation) is precisely what the deferred binding now
  refuses.
- **Durable docs (1+1 paths)**: `docs/SECURITY.md` (the commit-time
  completion binding: deferred constraint-trigger mechanism, exact
  binding tuple, refusal/rollback semantics, no new authority) and
  `docs/TESTING.md` (the four new proofs, the real-command race
  design with the observed native lock edge, and the bounded
  negative-path phrasing).
- **OAP carry-forward (2 paths)**: `oap/active` (`083-13-b`) and the
  b order byte-for-byte.
- **Carried a paths (unchanged by b)**: the a product/test/docs/oap
  paths listed in the a report.

## Contract evidence

### 1. Exact trusted completion required at commit (b item 1)

- The old direct-authority test's positive path (commit a reserved
  heading change without completing the journal) now fails closed by
  construction: the deferred constraint trigger fires on the
  `audit.heading_row_effect` insert at COMMIT, and the check function
  requires, on the same locked transaction state, the exact completed
  078 journal row, the exact family audit row, and the exact
  completed reservation — per family, per the resource classifier
  (`composition_node` for Agent, `editor.sites` for the Editor
  route) and principal pairing described in the diff section. The
  check is `SECURITY DEFINER` owner-only with no EXECUTE surface, so
  no runtime role can read, write, or bypass the fact's binding
  inputs.
- `test_missing_completion_refuses_commit_and_leaves_no_residue`
  (native pass): a real Agent HTTP mutation stages the COW write and
  the heading fact, the trusted completion is withheld, and the real
  COMMIT is refused with `HEADING_EFFECT_COMPLETION_UNBOUND`
  (`P0001`); the bounded test observation is that every durable
  state (COW view, pending operations, heading facts, family audit,
  completion journal, reservation) is byte-for-byte the pre-state —
  no residue — after which the same body and idempotency key
  completes exactly once with the real completion. The mismatched
  completion shape is refused by the same check (exact
  operation/family/site/workspace/resource/principal/disposition
  tuple), and the ordinary HTTP sequence and no-effect behavior are
  unchanged (a carried a test re-passed in the module run).
- The repaired direct-call authority test (item 1's "correct the old
  direct-authority test's positive path") performs the real
  completion where applicable and is green in the full run.

### 2. Rollback after a real write and evidence insertion (b item 2)

- Both late-failure tests witness, through the ACTUAL HTTP mutation
  envelope, a successful staged COW write and heading fact inside the
  uncommitted transaction, then a real late completion failure or
  cancellation at the trusted journal boundary. The fixture
  instrumentation is owner-only and committed before the request: a
  `control.h13b_completion_barrier` table, an AFTER INSERT trigger on
  the completion journal, and a fixture-held rendezvous session lock
  the trigger waits on; with no barrier row the trigger is a no-op,
  so the same app instance serves the exactly-once retry. No
  production test interface is added.
- `test_agent_late_failure_rolls_back_staged_write_and_fact`
  (native pass): the barrier fails the completion after the staged
  write and fact are visible in-transaction; the real COMMIT is
  refused; before/after comparison of the exact durable state (view
  values, pending operations, heading facts, family audit,
  completion, reservation) shows byte-for-byte rollback; retrying
  the same body and idempotency key completes exactly once with
  exactly one completed fact and one family event; an ordinary
  replay of the successful result stays inert.
- `test_editor_late_cancellation_rolls_back_staged_write_and_fact`
  (native pass): the same witness through the Human-on-Agent Editor
  envelope with a real cancellation instead of a raised failure;
  identical durable-state rollback and exactly-once retry
  observations. The existing 409 stale/no-effect coverage is
  preserved (carried a tests green in the module run).

### 3. Actual command across a sibling publication (b item 3)

Design: both first-write races now run the REAL Agent
(`PATCH /api/agent/v1/components/...`) and REAL Human-on-Agent
(`POST .../components/{id}` composition update) commands, each
parked INSIDE its deployed writer, after the real in-command read
and before its UPDATE, by a fixture-only wrapper around the actual
design validator (the wrapper preserves the real validator call,
then parks the named request on a fixture-held advisory lock; the
parked command's open transaction keeps every structural,
workspace, and site lock it had already taken). A second workspace
runs the real freeze job and human acceptance in that interval.
The test does not treat the ten-second product lock budget as the
oracle: it first observes the exact native blocking edge in
`pg_locks` (the review job's real reviewer backend holding a
non-granted `transactionid` ShareLock on the parked backend's open
transaction id — the native display of the blocked site-row
`FOR UPDATE` in the 076 workspace-state materializer
`control.slaif_review_workspace_state`), then releases the real
command, then asserts the actual outcome and the sibling's real
publication in the resolved order.

- **Agent route** (`test_agent_first_write_race_real_command`,
  native pass, 14.61s): the parked agent command's transaction
  (open xid) holds the pre-park site-row `FOR SHARE` (taken by the
  039 `slaif_agent_require_cow_site` authorize step) plus the 050
  structural locks; the sibling freeze's materializer
  (`SELECT canonical_revision, status FROM control.site ... FOR
  UPDATE`, executed inside `control.slaif_review_workspace_state`)
  is observed blocked on the exact parked xid; the canonical
  projection is still the pre-publication row; after release the
  parked command's DML lands on the pre-publication row (HTTP 200,
  record `row_version=2`, props `W1stale`) — the DML-before-publication
  order the real product locks enforce on this route — the freeze
  then completes SUCCEEDED and the human acceptance publishes the
  second workspace; tail state: fact before/after = A rv1 /
  W1stale rv2 (family `agent`), one completed journal row, one
  idempotency row, the COW view at the pre-publication image, and
  exactly ONE typed `BASE_ROW_CHANGED` conflict for the heading
  component — the stale first write leaves no false heading
  evidence beyond its own real COW row and conflict.
- **Editor route** (`test_editor_first_write_race_real_command`,
  native pass, 13.32s): the parked Human-on-Agent editor takes no
  page-structure lock, but its 028 `control.human_editor_idempotency`
  insert (`site_id UUID NOT NULL REFERENCES control.site(id)`) holds
  the site row's `FOR KEY SHARE` referential-integrity lock until
  the command's own commit; the same materializer `FOR UPDATE` is
  observed blocked on the parked xid; after release the editor's
  unversioned UPDATE lands (constant wire `row_version=1`, merged
  props), the freeze + acceptance publish the sibling, and the
  recorded fact carries the ACTUAL same-statement before/after image
  pair (A props rv1 / merged props rv2) even though the earlier
  validation read saw a different version; exactly ONE typed
  `BASE_ROW_CHANGED` conflict for the editor operation; the normal
  unversioned wire contract is intact.
- **Native edge witnesses (preserved artifacts)**:
  `b2-park-lockgraph-B.csv` captured while the agent race was live
  shows the exact edge — reviewer pid `1837660`
  (`fixture_review_worker_...`) with `locktype=transactionid,
  mode=ShareLock, granted=f, transactionid=183326`, and the parked
  agent pid `1837663` (inside
  `SELECT * FROM content.slaif_agent_component_update($1,$2,$3,$4)`)
  holding `transactionid, ExclusiveLock, granted=t,
  transactionid=183326`. The owned PG18 server log at
  `2026-11-25 23:10:10.919 UTC` records the parked agent's own
  10s lock-timeout cancellation
  (`canceling statement due to lock timeout ... PL/pgSQL function
  content.slaif_agent_component_validate_design ... line 8 at PERFORM
  ... SELECT * FROM content.slaif_agent_component_update($1,$2,$3,$4)`)
  and at `23:10:11.076 UTC` the materializer completion
  `duration: 9714.036 ms  execute ...: SELECT control.slaif_review_workspace_state($1)`
  — 157ms after the parked transaction ended — the real wait and
  resolved sequence, not a fixture-deadline assertion.
- The working two-first-touch conflict control
  (`test_first_touch_conflict_control_case`) is preserved and
  re-passed; the separately replayed-copies design from round a is
  gone from both race tests. Only supported COW views, public
  foundation inspection (`pg_locks`), and real product lifecycle
  operations (enqueue/claim/run freeze, human acceptance) are used.

### 4. Recorded effect kept within pilot scope (b item 4)

- The editor branch now requires an actual distinct props pair:
  `props_before IS DISTINCT FROM props_after` on the same-statement
  images gates the fact insert, and the effect is scoped to the
  session's own `actor_type = 'AGENT'` COW workspace; unchanged-props
  and structural-only editor writes keep their legacy behavior with
  no heading props fact. The mixed-change behavior (accurate props
  pair recorded, no claim about structural history) is the documented
  pilot position.
- `test_editor_unchanged_props_and_structural_only_record_no_fact`
  (native pass): real unchanged-props editor writes and a
  structural-only write are bounded test observations of zero
  heading facts with the legacy wire responses intact; the ordinary
  Human workspace path is untouched.
- The 063 design-aware validator correction and the 080
  operator-refusal-before-destructive-downgrade ratchet are intact
  (a-carry tests, including
  `test_facts_authority_boundaries_and_downgrade_ratchet`, re-passed
  natively in the module run).

## Diagnostic evidence (preserved, honest)

All runs on the explicitly owned disposable PG18 fixture
(`[::1]:5432`, single runner; every run under a distinct log path in
`/tmp/oap-083-13-b-control/logs/`):

- `b1-heading-module-run2.log` (native 1): 3 failed, 9 passed in
  127.89s — the first full module run: agent race (budget
  assertion), editor race (early park-anchor defect since fixed),
  and the unchanged-props case (since fixed).
- `b1-retry3..6.log` (native 1 each): the two race tests failing on
  the published-first expectation that this round's root-cause work
  replaced.
- `b2-race-park-budget.log` / `b2-race-agent-breakdown.log`
  (native 1): the agent race failing the fixture-pause budget
  assertion with the then-mislabeled windows
  (`freeze=0.63s accept=9.90s`); `b2-park-lockgraph-A/B.csv` and the
  lock dump/profile/relname probes captured the real lock state that
  identified the freeze's materializer — not the acceptance — as the
  blocked statement, with the parked command's own 10s
  lock-timeout cancellation as the resolver (server-log pair above).
- `b3-race-agent-resolved.log` (native 1): first resolved-order
  attempt failed on a `pg_locks` database-filter defect in the
  observer (transactionid rows carry `database=0`).
- `b3-race-agent-resolved2.log` (native 1): the observer then saw
  the freeze blocked, but the parked xid read raced the park's own
  10s cancellation (xid gone before the edge was asserted).
- `b3-diag-editor-locks.log` / `-locks2.log`: full parked-editor
  `pg_locks` inventory plus a bounded site-`FOR UPDATE` probe whose
  pending request was the parked transaction id, with
  `pg_blocking_pids` naming the parked editor backend.
- `b3-diag-editor-bisect2..6.log`: DDL-surgery bisection — the
  parked editor was stopped at each of six named points inside the
  real writer (`X_assert`, `B_idempotency_begin`, `C1_page_get`,
  `C2_comp_list`, `C_definer`, `D_validator`) while a bounded probe
  attempted the site-row `FOR UPDATE`: ACQUIRED at `X_assert` and
  `B_idempotency_begin` (before the idempotency function body),
  BLOCKED at `C1_page_get`, `C2_comp_list`, `C_definer`, and
  `D_validator` — proving the site-row lock is taken by the 028
  `control.human_editor_idempotency` INSERT itself (`FOR KEY SHARE`
  via the `site_id` FK), not a page-structure lock. The temporary diagnostic test was deleted after use; its DDL
  restores ran in `finally` and its fixtures were dropped.
- `b3-race-editor.log` (native 1): first editor attempt under the
  superseded published-first design (parked transaction died at the
  10s budget).
- Passing subjects: `b3-race-agent-resolved3.log` (agent race,
  native 0, 14.61s), `b3-race-editor2.log` (editor race, native 0,
  13.32s), `b3-heading-module-full.log` (all 12 module tests,
  native 0, 127.26s), `b3-design-authority.log` (the repaired
  direct-authority test, native 0, 12.34s).
- Environmental residue: the aborted first full-suite launch of
  this session left one fixture database
  (`slaif_test_4c6341d755`) plus its 11 suffixed login roles and the
  11 bare product roles on the owned cluster; after verifying zero
  active backends and exact suffix/name attribution, only those
  exact objects were removed (cluster back to postgres/template
  only) before the full-suite relaunch. No foreign DB, Docker, or
  fixture was touched.

## Local verification (final implementation SHA `93ac0160ab540b4538d3e63f49fdc8ac3b3d422c`)

Owned resources only; every command at the implementation head:

| Gate | Result |
| --- | --- |
| `uv lock --check` | native 0 |
| `uv sync --frozen --all-groups` | native 0 |
| `uv run --frozen ruff check services/backend tests/repository tools` | native 0 (all checks passed) |
| `uv run --frozen ruff format --check services/backend tests/repository tools` | native 0 (357 files already formatted) |
| `uv run --frozen mypy` | native 0 (335 source files) |
| `uv run --frozen pytest services/backend/tests/unit tests/repository` | native 0 — `902 passed` (32.69s, 29 subtests) |
| `PGHOST='::1' PGPORT=5432 PGUSER=postgres uv run --frozen pytest services/backend/tests/integration -v` | native 0 — `465 passed in 4669.37s (1:17:49)` — zero failures, including all 12 `test_heading_row_effects.py` tests and the repaired direct-authority test |
| `uv build --out-dir /tmp/slaif-agent-site-distributions` | native 0 (sdist + wheel) |
| `python -m compileall -q tools tests/repository` | native 0 |
| `python -m unittest discover -s tests/repository -p 'test_*.py'` | native 0 (94 tests OK) |
| `python tools/check_repository.py` | native 0 (PASS repository policy) |
| `python tools/check_mermaid.py` | native 0 (16 diagrams, 652 files scanned; exact CLI via `npx --yes`) |
| `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` | native 0 (0 issues in 644 files) |
| ten process smokes (`uv run --frozen python -m slaif_agent_site.<module> --check`) | native 0 each: control_api, editor_api, agent_api, render_api, mcp_adapter, media_service, review_worker, scheduler, media_gc, bootstrap |
| `pnpm install --frozen-lockfile` | native 0 (frozen lockfile verified, all 10 workspace projects, pnpm 11.22.0) |
| `pnpm lint` | native 0 (root eslint + web filter, 0 warnings) |
| `pnpm format:check` | native 0 (all matched files Prettier-clean) |
| `pnpm typecheck` | native 0 (web, browser-worker, and root/e2e tsc) |
| `pnpm test` | native 0 (root build + all recursive package tests + 36 contract tests) |
| `pnpm build` | native 0 (full recursive build) |
| `pnpm licenses list --json` | native 0 (JSON license inventory captured) |

Note: the peer-provided Node 24.22.1 tool's bundled npm launcher was
incomplete (`bin/npm-cli.js` missing, so `npx`/`npm` could not
start). The repair used a local shim directory
(`/tmp/oap-083-13-b-node-tools/bin`) that drives the same pinned
`npm/lib/cli.js` (npm 11.19.1, node v24.22.1) without modifying the
peer tool; the exact CLIs (markdownlint-cli2 0.23.2, the approved
mermaid CLI) are the frozen repository gate versions. The initial
adverse runs are preserved at
`b4-light-gates.log` / `b4-light-gates2.log`.

## GitHub CI evidence

Against implementation head `93ac0160ab540b4538d3e63f49fdc8ac3b3d422c`
(pushed `c0c2c7d..93ac016` to the same draft PR #119 branch; no
second PR, no merge):

- **CI run 45742574555**
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/45742574555>:
  `completed / success` — all 25 job runs successful
  (02:27:44Z–02:46:34Z UTC):
  - the ten actual PostgreSQL matrix children: Foundation PG Group
    A PostgreSQL 14/15/16/17/18 (jobs 139650909139, 139650909122,
    139650909185, 139650909143, 139650909097) and Foundation PG
    Group B PostgreSQL 14/15/16/17/18 (jobs 139650909092,
    139650909020, 139650909124, 139650909176, 139650909250) —
    Group B runs the trusted mutation-completion (TC) command that
    carries the 12-test heading module and the native regressions
    on each actual PG14–18 instance — plus the five fast
    Foundation PostgreSQL 14–18 children (jobs 139657594162,
    139657594133, 139657594137, 139657594182, 139657594165); all
    successful.
  - Compose and edge packaging (job 139650909085, 14m20s):
    successful through the public NGINX path with all 19 projects,
    six device/browser profiles, real media acceptance, and
    isolated workers.
  - Supply-chain evidence (job 139650909073, 9m29s): fresh
    six-image scan with checksum verification and zero exceptions.
  - Python 3.12/3.13/3.14 quality and package (jobs 139650909100,
    139650909074, 139650909088), Node contracts (139650909179),
    Repository policy (139650908895), Markdown (139650909127),
    Mermaid (139650909075), Dependency review (139650909089).
- **CodeQL run 45742574554**
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/45742574554>:
  `completed / success` — Detect supported languages
  (139650908801), Analyze (actions) (139650947570), Analyze
  (javascript-typescript) (139650947642), Analyze (python)
  (139650947671), and the CodeQL rollup (139651205008) all
  successful.
- PR 119 check rollup at the implementation head (verified
  02:48Z UTC): `gh pr checks 119` reports 30 check runs, all
  `pass`, with zero failures or pending; the PR merge state is
  `CLEAN` and the PR remains OPEN/DRAFT — acceptance and merge
  belong to ROOT alone.

## Scope, secrets, production, skips, extra PR, merge

- Scope: the bounded 083-13-b increment only — the unmerged 080
  migration, the two focused test files, the narrowly affected docs,
  and the b order + active bytes. No new API, scope, dependency,
  foundation release, or private foundation SQL; no merged migration
  touched; the a order/report preserved untouched.
- Secrets: native fixture credentials exist only in the test process
  environment; no literal credential values appear in tool inputs,
  argv, pane output, logs, this report, or commits;
  `[redacted-fixture]` is the scope marker where a value would
  otherwise surface. Negative paths are described as bounded test
  observations throughout.
- Production: no production system, data, or credential access; no
  foreign fixture, Docker, or infrastructure operation (only the
  explicitly owned PG18 fixture and its verified residue).
- Skips: none; every gate above ran.
- Extra PR: none — one draft PR #119, amended; no merge,
  auto-merge, force push beyond the round-b branch amendment,
  history rewrite, or a-signal replay.

## Known limitations

- The race proofs establish the observed native wait and resolved
  order on PG18 at the tested statement level (the freeze's
  materializer site-row `FOR UPDATE` blocked by the parked command's
  site-row `FOR SHARE` / FK `FOR KEY SHARE`); they are witnesses of
  the real product locks on the two supported first-write routes, not
  a general COW concurrency theorem, and the shared statement
  snapshots expose neither a general CTE evaluation-order guarantee
  nor the foundation's first-touch bytes.
- The item-2 rollback witnesses use fixture-owned journal-boundary
  instrumentation (owner objects, committed before the request,
  removed in `finally`); the production writer has no test
  interface.
- The heading effect pilot remains scoped to Agent and
  Human-on-Agent composition_node heading writes under the existing
  byte limits; other families, structural history, and retained
  review projections are outside this increment.
- Final SELF still receives its own independent CI verification per
  the order; this report's CI section reflects the implementation
  head at publication time.

# OAP 083-14-b — enforce the retained Heading byte limit before
# aggregation

- Order: `oap/orders/083-14-b-enforce-retained-heading-byte-limit.md`
  (5186 bytes, SHA256
  `32d4eebf12939f37165e7ba5ba899a8ad01906f7e3a7446930fc10760517150b`),
  published byte-exact with `oap/active` = `083-14-b`.
- PR mode: `AMEND_EXISTING_PR`
- PR: #123 <https://github.com/ulfe-lmi/slaif-agent-site/pull/123>
  (ONE draft PR, branch
  `oap/083-14-a-retained-heading-review-facts`, base `main`, state
  OPEN/draft; amends the 083-14-a implementation on the same branch)
- Result: COMPLETE for the 083-14-b contract: both bounded findings
  are implemented and tested; a pre-report blocking source finding
  (the first b design computed the total and the array in one
  statement, so PostgreSQL built the oversized array before the
  refusal) was corrected in this same turn before publication, and
  the full required evidence was re-run at the FINAL implementation
  subject: every local gate is native-pass, and the fresh GitHub CI
  (20 matching-app required checks, ten real PG14–18 matrix jobs,
  Compose public-edge proof, fresh six-image supply-chain, CodeQL)
  on the final implementation head is fully successful (exact run
  and job identities below).
- Repo: `https://github.com/ulfe-lmi/slaif-agent-site`
- Verified base: `1a633f57d828b099111b7b3dc3dc4ceafb9982b0`
  (verified remote main, as named by the order)
- Verified a heads: a report-only head
  `8fbfc236be77a7057618ddbb794971a1f59765d7` with sole
  implementation parent
  `f4e1a7109c8db5dd6cb1cf23cd5e6f045ca8141f` (both byte-verified
  before mutation; the a order and a report are immutable and
  preserved)
- Implementation head SHA: `608e2bf8921048b59219d4845e2aef5259dfe76a`
  (`oap(083-14-b): measure the retained heading byte total before
  the aggregation`, sole parent = intermediate b commit
  `da048c647d143a78d0920cc566283f9e23a5c9b0`)
- Report publication commit: SELF
- Pushed commits: the two b implementation commits (intermediate
  `da048c6` + the pre-report correction `608e2bf8921048b59219d4845e2aef5259dfe76a`) + the
  report-only SELF commit recorded below

## Pushed commits

1. `da048c647d143a78d0920cc566283f9e23a5c9b0` — `oap(083-14-b): enforce the retained
   heading byte limit before aggregation` (sole parent: a report-only
   head `8fbfc236be77a7057618ddbb794971a1f59765d7`).
2. `608e2bf8921048b59219d4845e2aef5259dfe76a` — `oap(083-14-b): measure the retained heading byte
   total before the aggregation` (sole parent: commit 1). The
   pre-report blocking source correction: the record shape moves
   into the migration-local `_RECORD_PROJECTION_SQL` constant
   consumed by two separate statements with the refusal between
   them (commit 1 measured and aggregated in one statement, which
   PostgreSQL evaluates fully before the refusal).
3. The report-only SELF commit recorded by this publication (sole
   parent: commit 2; changes only this report).

## Changed files

1. `oap/orders/083-14-b-enforce-retained-heading-byte-limit.md`
   (new, order bytes)
2. `oap/active` (`083-14-b`)
3. `services/backend/src/slaif_agent_site/db/alembic/versions/081_001_retained_heading_review_facts.py`
4. `services/backend/tests/integration/test_retained_heading_review_facts.py`
5. `docs/SECURITY.md`
6. `docs/TESTING.md`

No other path changed: the b diff against the a implementation head
touches only these paths, so every 083-14-a byte (order, report,
product, docs, CI wiring) is preserved. Commit 2 (the pre-report correction) touches only paths 3 and 5 of this list (the 081 migration and docs/SECURITY.md).

## What this round implements

### Finding 1 — the exact byte budget, enforced before aggregation, on a shared record projection

The a-round first total-byte check compared the 1 MiB ceiling with
the sum of the UTF-8 codepoint counts of each selected fact's two
props JSON texts — an estimate that omits every other retained-record
field, all JSON syntax and canonical escaping, so a selected set can
pass it and then exceed the encoded array limit, where the a-round
first authoritative check only followed `jsonb_agg`.

The 081 capture definer now enforces the EXACT canonical UTF-8 byte
limit of the selected record array BEFORE aggregation, in strict
statement order:

- The exact 9-field record shape is written ONCE as the
  migration-local constant `_RECORD_PROJECTION_SQL` and consumed by
  TWO separate SELECT statements (the same record shape and the
  same 070 canonical serialization contract as the stored facts),
  in strict order:
  1. MEASURE — `SELECT coalesce(sum(octet_length(convert_to(control.slaif_canonical_jsonb_text(rows.rec), 'UTF8'))), 0) + 2 + GREATEST(coalesce(count(*), 0) - 1, 0) INTO n FROM (the shared projection) AS rows` — measurement only; the 070 canonical array
     encoding is exactly the two brackets, one comma between every
     pair of adjacent records, and each record's own canonical
     serialization (the recursive serializer renders a value
     identically at any depth), so this sum IS the exact
     pre-assembly encoded size: no estimate, and no loose bound
     that could reject an in-budget set.
  2. REFUSE — `IF n > 1048576 THEN` refuse
     (`HEADING_RETENTION_OVER_BUDGET`, `P0001`) `END IF;` — the
     over-ceiling set is rejected before any aggregation is
     computed at all.
  3. AGGREGATE — `SELECT coalesce(jsonb_agg(rows.rec ORDER BY ...), '[]'::jsonb) INTO facts FROM (the same shared projection) AS rows` — the aggregation runs ONLY after the exact
     total has passed, over the identical record shape and ordering
     inputs, so the two measures cannot drift.
  No temporary table, no new database grant, no runtime API.
- After the aggregation: the preserved 079-style cheap
  conservative lower-bound pre-check, then the preserved
  authoritative exact canonical measurement of the assembled array.
- Definitive post-assembly equality invariant: the assembled
  array's canonical size must equal the shared pre-assembly total
  exactly (`facts_bytes <> n` → same stable `P0001` budget code);
  a divergence is a broken measurement invariant, refused with one
  terminal refusal and the whole locked transaction rolled back.
- Stable ordering (per-row transition order, native UUID
  tie-break), the compact error behavior (all
  `HEADING_RETENTION_*` → worker `HEADING_RETENTION_FAILED`),
  full rollback, the phase-aware grants and the downgrade ratchet
  are unchanged; the record and per-value budgets, the binding
  checks and the authorized read are unchanged.

Design history (both rejected shapes preserved as diagnostic
evidence under "Diagnostic evidence"): (1) the first b design
shared the projection through a session-scoped `CREATE TEMP TABLE
... ON COMMIT DROP`; the focused real run proved that shape FAILS
in the fixture: the worker role has no TEMP privilege in the
fixture database (raw error captured by a disposable owner-only
probe, since removed: `permission denied to create temporary
tables`), and the order forbids new grants. (2) The next design
computed the total and the `jsonb_agg` in ONE `SELECT ... INTO n,
facts`; the pre-report source review found that PostgreSQL
computes both output expressions before the following `IF`, so the
oversized array was built before rejection. The final design — the
migration-local record-shape constant interpolated into two
separate statements with the refusal between them — is the
grant-free form that keeps the shared shape and the required
measure-before-aggregate order; the source order was verified on
the rendered definer (total → refusal → aggregation → equality,
with no `jsonb_agg` anywhere before the refusal) and re-proved
behaviorally by the real in-cap over/under cases at the final
subject (below).

### Finding 2 — read-time negative evidence through the authorized
human read

`test_budget_and_binding_refusals_leave_no_partial_state` gains a
third part (c): after the owner-seeded companion-identity
divergence (the stored `principal_id` corrupted, the capture
refusing and the retained row verified unchanged), the AUTHORIZED
HUMAN READ of the same bounded fixture is called with the same
mismatched persisted identity and must answer the uniform 404
(`REVIEW_READ_UNAVAILABLE` mapping, no oracle, no partial state);
the owner then restores the EXACT stored identities and the same
read succeeds with the envelope byte-identical to the pre-corruption
captured set (status `captured`, `snapshot_id`, `fact_count`,
`facts_bytes`, `facts_digest` and `facts` all equal). The
instrumentation is owner-only SQL on the fixture connection,
disposable, and restores the immutable production row on every exit.
The existing atomic late-failure test is
`test_freeze_fault_after_manifest_staging_rolls_back_atomically`
(unchanged, re-passed).

Actual test identifiers and scopes (all in
`services/backend/tests/integration/test_retained_heading_review_facts.py`):

- Finding 1: `test_preassembly_canonical_byte_budget_enforced_before_aggregation`
  (new; real Agent workspace per case, real 34-edit over-ceiling
  case and real 24-edit under-ceiling case on the same seeded
  heading; owner-only measurement oracle; real freeze worker runs
  against both cases).
- Finding 2: `test_budget_and_binding_refusals_leave_no_partial_state`
  (existing test, extended with part (c) through the authorized
  human HTTP read of the same fixture).
- All a criteria re-verified:
  `test_real_lifecycle_retains_exact_heading_facts`,
  `test_pre_feature_unavailable_and_captured_empty`,
  `test_freeze_fault_after_manifest_staging_rolls_back_atomically`,
  `test_retention_authority_boundaries_and_downgrade_ratchet`
  (all re-passed on the final subject; the full native integration
  suite below re-runs the complete a surface).

## Contract evidence per finding

### 1. Exact pre-aggregation byte budget (bounded native case)

The fixture shape: each edit sets the Heading `text` prop to 2726
repetitions of U+754C plus a distinct decimal suffix. The binding
per-prop bound is the Agent API's 16384-byte `ensure_ascii` JSON
props cap: each U+754C costs 6 escaped bytes, so 2726 repetitions
plus a 1–2 digit suffix keep every props image at 16378–16379
escaped bytes (under the cap), under the 4096-codepoint schema
`max_length`, and the stored 080 image at 8203–8204 native octets
(under the 16384-octet per-value cap). The 070 canonical serializer
ASCII-escapes each U+754C to a 6-byte `\u` sequence, so the EXACT
canonical encoded array total of 34 same-heading records crosses
the 1048576-byte ceiling while the a-round codepoint estimate of
the two props texts still passes — every other gate (256-record
count on the whole fact set, per-value octet cap, codepoint
estimate, lower-bound pre-check) is provably unable to fire, so the
real freeze is refused AT the pre-aggregation check. The legal
24-edit set stays well under the ceiling.

- Over case: the oracle (owner-only, the same 9-field record shape
  and 070 serializer) measures `records = 34 < 256`,
  `value_octets_max ≤ 16384`, `pre_total > 1048576` and
  `codepoint_estimate < 1048576` on the persisted facts BEFORE the
  freeze; the real worker freeze then returns `FAILED` /
  `HEADING_RETENTION_FAILED`, and no partial freeze or review state
  exists: zero snapshot rows for the workspace, zero retention
  rows globally, the workspace still `FREEZING`, all 34 mutation
  facts intact, the job row `FAILED` with the same error.
- Under case: the real freeze `SUCCEEDED`; the retention row's
  `fact_count = 24`, `facts_bytes ≤ 1048576`, and
  `facts_bytes == pre_total` EXACTLY (the new post-assembly
  equality invariant, independently measured by the oracle on the
  same record shape); the stored `facts_digest` re-verifies over
  the 070 canonical serialization of the stored bytes, and every
  stored record matches the product-owned 080 facts field-for-field
  in the deterministic per-row transition order.

### 2. Read-time identity divergence, uniform unavailable, exact
restore

As described under "What this round implements" → Finding 2: the
authorized human read answers the uniform 404 while the persisted
identity is mismatched (no oracle, no partial state, production row
untouched), and the exact restore serves the unchanged captured set
byte-for-byte. This is the read-time complement of the capture
definer's refusal; together they prove the served set is re-checked
against the companion's completion identities on every read.

## Local verification

All commands from the repository root, owned disposable resources
only (owned PG18 on `[::1]:5432`, owned Node toolchain); every log
path below is under `/tmp/oap-083-14-a-control/logs/`, preserved
byte-exact. "native N" is the exact process exit code (a pytest
summary line with no failed/error counts is the native-0 result).

Two subjects are distinguished: the intermediate implementation
subject `da048c6` (single-statement shared projection) and the
FINAL implementation subject `608e2bf8921048b59219d4845e2aef5259dfe76a` (the pre-report
measure-before-aggregate correction). The order's evidence
requirements are stated for the FINAL subject; the intermediate
subject's full battery is preserved and cited as its own evidence.

### Intermediate subject `da048c6` (diagnostic for that subject)

- `uv run --frozen pytest services/backend/tests/integration/test_retained_heading_review_facts.py -v`
  on the owned PG18 → **6 passed in 98.24s, native 0**
  (`b-focused-module-2.log`)
- `uv run --frozen pytest services/backend/tests/integration -q`
  on the owned PG18 → **471 passed in 4664.62s (1:17:44),
  native 0** (`b-full-integration-1.log`; 471 = the 470-test
  083-14-a native surface plus the one new b byte-budget test)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`
  → **910 passed, 29 subtests passed, native 0** (`b2-unit.log`)
- ruff check/format, mypy (337 files), `uv build`, ten process
  smokes, compileall/unittest/check_repository/check_mermaid,
  markdownlint (652 files, 0 issues), frozen Node gates (v24.22.1,
  pnpm 11.22.0: install/frozen, lint, format:check, typecheck,
  test, build, licenses list --json — all native 0,
  `b-node-all.log`) — all native 0 at this subject
  (`b2-mypy.log`, `b2-build.log`, `b2-smokes.log`, `b2-prep.log`,
  `b2-markdownlint.log`, plus the initial ruff pass)

### FINAL implementation subject `608e2bf8921048b59219d4845e2aef5259dfe76a`

Order-mandated focused first, then the full battery, all at the
final bytes:

- `uv run --frozen pytest services/backend/tests/integration/test_retained_heading_review_facts.py -v`
  on the owned PG18 → **6 passed in 124.12s (0:02:04), native 0**
  (`b3b-focused-module-1.log`). The same module also passed as a
  standalone focused run on the two-statement source before the
  final docstring-format line landed (`b3-focused-module-1.log`,
  6 passed in 121.78s, native 0) and is re-proved inside the final
  full run below. The real in-cap over/under cases (34-edit
  refusal with no partial state; 24-edit capture with the stored
  `facts_bytes` exactly equal to the independently measured
  pre-assembly total) are the behavioral proof of the corrected
  source order, alongside the extended read-time divergence part
  (c) and the four a-surface module tests.
- `uv run --frozen pytest services/backend/tests/integration -q`
  on the owned PG18 → **471 passed in 4559.63s (1:15:59), native 0**
  (`b3-full-integration-2.log`) — the complete 471-test native
  surface (all retained lifecycle and read criteria of a plus the
  new b test) at the final bytes. (The first final-subject attempt,
  `b3-full-integration-1.log`, was stopped by the executor after
  the final docstring-format line landed so the full run matches
  the committed bytes exactly; its interrupted log is preserved
  with an executor note.)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`
  → **910 passed, 29 subtests passed, native 0** (`b3b-unit.log`)
- `uv run --frozen ruff check services/backend tests/repository tools`
  → `All checks passed!`, native 0; `uv run --frozen ruff format
  --check services/backend tests/repository tools` → `359 files
  already formatted`, native 0 (re-confirmed at the final bytes)
- `uv run --frozen mypy` → `Success: no issues found in 337 source
  files`, native 0; `uv build --out-dir
  /tmp/slaif-agent-site-distributions` → sdist + wheel built,
  native 0; all ten `uv run --frozen python -m
  slaif_agent_site.<module> --check` process smokes → every check
  `CHECK_OK`, native 0 (all three in `b3b-static.log`)
- `python -m compileall -q tools tests/repository` native 0;
  `python -m unittest discover -s tests/repository -p 'test_*.py'`
  → `Ran 102 tests ... OK`, native 0; `python
  tools/check_repository.py` → `PASS repository policy`, native 0;
  `python tools/check_mermaid.py` → `PASS Mermaid rendering: 16
  diagram(s) in 3 file(s); 660 Markdown file(s) scanned`, native 0
  (`b3b-prep.log`)
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` → `Linting: 652
  files / Summary: 0 issues in 0 files`, native 0 (`b3b-prep.log`)
- Frozen Node gates: the Node subject (package manifests, lockfile,
  app sources) is unchanged by the b bytes, so the intermediate
  subject's frozen Node run (`b-node-all.log`, all seven commands
  native 0) is the Node evidence; the Markdown subject was
  re-linted at the final bytes above.

Source-order proof of the measure-before-aggregate fix: the
rendered 081 definer was checked programmatically at the final
subject — the record shape occurs once in the source (the
`_RECORD_PROJECTION_SQL` constant), both statements embed the
identical rendered projection, and the statement order is total
measurement (`INTO n`) → ceiling refusal → aggregation (`INTO
facts`) → exact equality, with no `jsonb_agg` anywhere before the
refusal.

## Diagnostic evidence (preserved)

- `b-focused-module-1.log` — the FIRST focused run, against the
  abandoned session-temp-table shared-projection design: **6 failed
  in 47.75s, native 1** (diagnostic for that subject, not a passing
  run). The new byte-budget test's first real Agent edit was refused
  `422 DOMAIN_VALIDATION_FAILED` (the original 4094-repetition
  fixture exceeded the Agent API's 16384-byte `ensure_ascii` props
  cap — the shape that led to the 2726-repetition fixture above);
  the five pre-existing module tests failed at the real freeze with
  `HEADING_RETENTION_FAILED`, whose raw database cause the
  disposable owner-only probe captured as `permission denied to
  create temporary tables` (the fixture database grants no TEMP and
  the order forbids new grants). Both failure classes motivated the
  shared-projection design, re-verified by native-0 focused runs on
  the two later subjects.
- Intermediate subject `da048c6` (single-statement design): its
  full local battery above passed, and its GitHub CI (run
  46049903405, main matrix, and run 46049903267, CodeQL; both
  `success`) ran on that subject. It is superseded by the
  pre-report correction and cited only as evidence for that
  subject. The blocking finding itself is a source-order review,
  recorded under "What this round implements" → Finding 1 (design
  history (2)): the single `SELECT ... INTO n, facts` computes
  both output expressions before the following `IF`, so the
  oversized array was built before rejection. The correction
  (commit 2) re-proves the real in-cap over/under cases at the
  final subject.

## GitHub CI evidence (final implementation subject)

All at the final implementation head
`608e2bf8921048b59219d4845e2aef5259dfe76a` (the PR head at run
start; the report-only commit changes no product bytes):

- CI run 46061636270 (`CI` workflow): **completed success** — all
  26 jobs `pass`: Foundation PG Group A PostgreSQL
  14/15/16/17/18, Foundation PG Group B PostgreSQL
  14/15/16/17/18 (the ten actual matrix children; Group B carries
  the 9-module native command including the 081 retained-heading
  module), Foundation PostgreSQL 14/15/16/17/18 aggregators,
  Compose and edge packaging, Supply-chain evidence, Python
  3.12/3.13/3.14 quality and package, Markdown, Mermaid, Node
  contracts, Repository policy, Dependency review.
- Compose public-edge proof (job 140717042549, log preserved at
  `b3-ci-compose-job.log`): 41 `browser-e2e: PASSED` entries across
  all 19 projects (the six named profiles included), among them
  `browser-e2e: PASSED project=review-surface contract=review-surface-retained-heading-effects`
  — the existing authorized retained Heading read through the
  public NGINX edge — real media publication and isolated worker
  runs, and the Apache config check (`Syntax OK`).
- Supply-chain evidence (job 140717042793, log preserved at
  `b3-ci-supply-job.log`): fresh six-image build/scan,
  `supply-chain-evidence: OK images=6 critical=0 high=134`, zero
  exceptions (policy gate passed).
- CodeQL run 46061636233: **completed success** — Detect supported
  languages, Analyze (actions), Analyze
  (javascript-typescript), Analyze (python) all pass.
- PR 123 check rollup at the final head: `gh pr view 123` reports
  30 check runs, all `SUCCESS`, zero failures or pending; the PR
  remains OPEN/DRAFT — acceptance and merge belong to ROOT alone.

### Limits (GitHub)

- This report records the state observed for the literal final
  implementation head before the report commit; the report push
  may trigger fresh CI on the report head, which strategy
  independently waits/verifies. Pending/missing/cancelled/failed
  is never reported as success.
- The intermediate subject's CI (runs 46049903405/46049903267,
  both success) is cited only as evidence for that subject.
- The Compose, supply-chain and matrix subjects above are the
  exact run and job identities at the final implementation head;
  ROOT independently verifies them on final SELF.

## Scope, secrets and confirmations

- Scope: only the six paths above changed; the unmerged 081
  migration, the focused test module, the matching
  security/testing docs and the b transcript. All merged
  migrations, prior-round bytes, the existing approved snapshot and
  acceptance semantics, the exact authorized read, and all security
  and supply policies are preserved. No new API, dependency,
  maintenance, generalized history, conflict-lifecycle, foundation
  or release change; no new grant (the shared projection is a
  migration-local constant over already-held tables; the test
  oracle is owner-only fixture verification). No process IDs, handles, FIFO
  or lock inodes, or prompt digests appear in this report.
- Secrets: none committed; fixture credentials live only in the
  test process environment; negative-path assertions use test
  voice.
- No merge, no force push, no second PR, no later round; the a
  order and a report remain immutable and untouched. ROOT alone
  reviews, accepts and merges.
- The report-only push may trigger a fresh CI run on the report
  head; that run is not the implementation subject and strategy
  verifies independently.

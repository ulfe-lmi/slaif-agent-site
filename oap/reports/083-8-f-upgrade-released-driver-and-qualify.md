# OAP execution report — 083-8-f: upgrade released asyncpg driver and qualify

- Order: `oap/orders/083-8-f-upgrade-released-driver-and-qualify.md` (266L, SHA256
  `741283266cacc7bba4cf4e0a38cc7af560e706f7947c1aba4f064e8a55de6c97`, immutable)
- PR mode: `AMENDED_EXISTING_PR` — PR #112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state `open`
- Status: `PARTIAL`
- Branch: `oap/083-8-a-qualify-public-whole-session`; base `main`
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`
- Starting remote SELF: S_e `5873c94c917382cb8cb45765211e6d6c971645d6`
  (tree `0dc84145c422983d6272e9f09a3d253e93478df9`), the 083-8-e report-only
  commit; root-verified remote at activation
- Literal implementation SHA: I_f
  `0f63e82d28ce714470577af998d2dca3df835a34` (tree
  `5badebced51b59259914586632bc6f4ab8c87db0`), sole parent S_e, exactly 13
  changed paths (section 2), commit `2026-10-27T15:17:35Z` per
  `root-If-remote-commit.json`; root-verified complete 1128->1129 leaf maps,
  gate clean; frozen product module 1844L
  `45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8`
  byte-unchanged; no production function/schema/authority source change
  this round (the driver runtime version itself DID change: 0.31.0 ->
  0.32.0 released pin, section 2)
- Report publication commit: `SELF` — the single report-only commit whose
  sole parent is I_f and whose sole changed path is this report; its SHA is
  the verified remote PR head (section 10)
- Pushed commits this round: I_f (sole implementation commit; exact
  f-order + `oap/active` bytes included in its 13 paths), then this
  report-only SELF commit
- Cumulative PR paths (measured): 19 at S_e; 30 at I_f (11 new paths);
  31 at SELF (section 10)

## 1. What this round did (driver upgrade + qualification gates)

f upgraded the released driver `asyncpg 0.31.0 -> 0.32.0` in the exact
dependency/lock/metadata/notices/SBOM/doc surface (13 paths, section 2) and
then drove the ordered qualification gates at I_f. Actual outcomes:

- NONDB stage: exact 31 named commands + 3 additional NONDB commands, all
  actual native 0 (section 3).
- CI at I_f: 30/30 required checks SUCCESS after ONE approved exact
  packaging-job rerun (section 4).
- Q gate (Q80): 5 x fresh owned PG14..18, 16/16 each, child native 0,
  safe owned cleanup, ROOT-verified (section 5).
- FULL gate: attempt 1 ACTUAL FAILURE (budget exhaustion; ROOT planning
  error, preserved) and attempt 2 (budget-corrected source revision)
  ACTUAL PASS 363/363 (sections 6.1-6.3).
- P7 diagnostic: ONE bare exec, child native 0, print-only
  characterization of the public `reviewer.dependencies()` result on a legal
  mixed-FK fixture (section 7).

Status `PARTIAL` because: (a) the current documentation contains a FALSE
source explanation (FOUNDATION_INTEGRATION.md lines 226..228 PK/ordinal
claim, corrected interpretation section 7.3) whose doc-only repair is
planned for 083-8-g (NOT activated); (b) fresh LOCALWHOLE and LOCAL6 are
NOT RUN; (c) final SELF acceptance/merge remains with ROOT alone. This
report is an index of actual evidence; nothing here is acceptance.

No production function/schema/authority source change: the driver runtime
version DID change (0.31.0 -> 0.32.0 released pin, section 2), while the
frozen 1844L generic Q module and the other two frozen qualification
test/CI paths (section 5.3) are byte-unchanged at I_f. Zero
secret/production access; no extra PR; no merge.

## 2. Implementation I_f — exact 13 paths (sole parent S_e)

| Path | Git blob SHA1 (S_e -> I_f) | I_f content SHA256 | Change |
| --- | --- | --- | --- |
| `AGENTS.md` | `4d71a5ac` -> `ab59bef6` | `ff9f4d76` | `asyncpg==0.32.0` in the current exact direct runtime deps |
| `CONTRIBUTING.md` | `62b0c166` -> `16478f41` | `3911a020` | dependency-list reconciliation |
| `THIRD_PARTY_NOTICES.md` | `6f2d7581` -> `a09dc1d4` | `2cfe4ec7` | asyncpg 0.32.0 Apache-2.0 attribution |
| `docs/DATABASE_CONNECTIONS.md` | `f2a0bd59` -> `d8c39e58` | `adb592fe` | driver-version note reconciliation |
| `docs/TESTING.md` | `722d0718` -> `dd2aa4a7` | `d3339a18` | driver-version note reconciliation |
| `oap/active` | `976bd5ff` -> `5fa47422` | `e66dd779` | exact f activation bytes |
| `oap/orders/083-8-f-upgrade-released-driver-and-qualify.md` | NEW -> `e38eeebf` | `74128326` | the immutable f order (266L) |
| `pyproject.toml` | `c06e7369` -> `ead50cfd` | `d332be1d` | qualified `asyncpg==0.32.0` |
| `sbom.json` | `715c9b39` -> `a2c404e3` | `4a439bb8` | asyncpg 0.32.0 component reconciliation |
| `services/backend/tests/unit/test_foundation_contract.py` | `b1970312` -> `14fa32dc` | `42d1555f` | pinned-version contract assertion 0.32.0 |
| `tests/supply_chain/test_policy.py` | `fb211caf` -> `8ed69059` | `5bac1fa1` | policy reconciliation for the released pin |
| `tools/check_repository.py` | `4568d09c` -> `1a9e891b` | `24e891a3` | expected dependency metadata update |
| `uv.lock` | `90cfd9a3` -> `9a1404d6` | `9b6124bc` | committed hashed lock; asyncpg/root requirement only |

Hash-kind note (factual correction to this report's earlier draft): the
first draft column `Blob (S_e -> I_f)` actually mixed the CURRENT I_f git
blob SHA1 with the CURRENT I_f file content SHA256 (e.g. AGENTS.md
`ab59bef6` is the I_f git blob and `ff9f4d76` the same file's SHA256; the
NEW order's git blob `e38eeebf` and its SHA256 `74128326` are the same
bytes under two algorithms). The table now carries the actual old/new git
blob pairs from `git diff --raw S_e..I_f` (ROOT raw, native 0, retained in
`root-f-report-draft-hash-kind-factual-correction.txt`) plus the
separately labeled I_f content SHA256; no software delta is inferred from
mixed-algorithm hashes. Full 40/64-char values: `f-hashes-I_f.txt` (I_f
git blob + content SHA256 per path) in the f scratch.

Lock evidence (ROOT-full-parsed working `uv.lock`, 15:14:34Z): 45 total
lock packages — 43 unchanged (the foundation entire entry INCLUDED among
the unchanged; foundation is NOT a 46th) + 2 changed (asyncpg + the root
requirement entry); all 37 new asyncpg locked artifact URLs/hashes/sizes
checked non-yanked and matching the saved official registry metadata;
original 3 CI/module hashes exact; not all 82 registry artifacts of the
lock are installed. Foundation frozen `agent-cow-postgresql==0.2.0`
(registry pypi.org), unchanged: wheel
`agent_cow_postgresql-0.2.0-py3-none-any.whl` 106280B SHA256
`c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1` +
sdist 107970B SHA256
`eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c`
(re-verified in the I_f uv.lock text). Registry: asyncpg 0.32.0
Apache-2.0 non-yanked; metadata artifacts retained in the f scratch.
Upstream lead (NOT proof of any observed defect here): official asyncpg
issue 1307 / MERGED PR 1324 (commit
`4a83cc2f2eb2f3445aa181d2d0da9e9559e08aa6`, released v0.32.0) addresses a
protocol-abort pool deadlock; retained artifacts
`upstream-1307-issue.json`, `upstream-1324-{pr,files,commit}.json`,
`upstream-latest-release.json`. NO alternate driver version, NO SDK
private patch, NO standalone functional trial, NO protocol-abort
experiment beyond the ordered work. The ordered tests/process checks DID
import the pinned 0.32.0 SDK during normal execution (all31 commands 6
and 8-17; Q/FULL/P7 pytest runs), and a standalone version-metadata
observation (upstream artifact fetches) also occurred — both retained in
EV. `uv sync --frozen` and `pnpm install --frozen-lockfile` at I_f
changed installed deps as ordered (only ordered frozen install/setup; no
input/source/env mutation during the live gates). No NEW package family
was added; the driver dependency version WAS updated.

Grouped-scope accounting (independently reviewed by ROOT; overlapping
summaries, not disjoint additive groups): the 11 non-oap paths carry the
10 actual allowed identities, 111 gross lines vs S_e (within the 450
cap), of which `docs/DATABASE_CONNECTIONS.md` belongs to this 111 family
and `docs/TESTING.md` (9 gross) belongs to the original five-docs
cumulative group (157 gross vs main, within 500); strategic f-order +
active = 268 gross. Total non-report I_f-vs-S_e: 13 paths, 388 gross =
111 + 9 + 268. `git diff --shortstat S_e..I_f`: non-oap 11 files +66/-54
(already INCLUDES docs 2 files +13/-5); oap 2 files +267/-1 (order 266L +
active). Cumulative `main..I_f`: 30 files, +6616/-78 (docs gross
included).

## 3. NONDB stage at I_f (exact 31 + 3 additional)

Frozen corrected `all31-runner.sh` (122L, SHA256 `49f12b17...`, exact 31
argv unchanged from the reviewed copy) executed at clean gate-wt I_f; all
31 actual natives 0 with END source-clean, independently verified by ROOT
(31 individual 0). Three additional approved NONDB commands (exact reuse of
the reviewed observation/guard/failure-STOP pattern, 100L cap, one
`bash -n`) actual native 0; supply-chain suite 43 passed. EV retained in
`all31-I-0f63e82/` and `additional-I-0f63e82/`. These are LOCAL
verification only (not CI replacement, not acceptance). Agent OpenAPI
zero-diff is ALREADY covered by fresh ALL31 command 6 at I_f
(`test_agent_openapi.py` 7 pass; actual generator byte-equality assertion;
overall 869 pass / native 0 per ROOT reconciliation) — no separate
generator/CLI/test rerun performed or needed.

### 3.1 Exact 31 argv (all actual native 0)

Frozen runner `all31-runner.sh` 122L, full SHA256
`49f12b179a91fa276ad15b5a02639f258aef7aa89f5f2900a25d417a405576dc`
(byte-identical 31 argv to the reviewed legacy copy). The exact 31 argv,
in run order: `uv lock --check`; `uv sync --frozen --all-groups`;
`uv run --frozen ruff check services/backend tests/repository tools`;
`uv run --frozen ruff format --check services/backend tests/repository
tools`; `uv run --frozen mypy`; `uv run --frozen pytest
services/backend/tests/unit tests/repository` (869 collected / 869 passed
/ 3 warnings, including `test_agent_openapi.py` 7 pass); `uv build
--out-dir /tmp/slaif-agent-site-distributions`; the 10 `python -m
slaif_agent_site.<module> --check` smokes (control_api, editor_api,
agent_api, render_api, mcp_adapter, media_service, review_worker,
scheduler, media_gc, bootstrap); `node --version`; `pnpm --version`;
`pnpm install --frozen-lockfile`; `pnpm lint`; `pnpm format:check`;
`pnpm typecheck`; `pnpm test`; `pnpm build`; `pnpm licenses list --json`;
`python -m compileall -q tools tests/repository`; `python -m unittest
discover -s tests/repository -p 'test_*.py'`; `python
tools/check_repository.py`; `python tools/check_mermaid.py`; `npx --yes
markdownlint-cli2@0.23.2 '**/*.md'`. Per-command argv files + START/END
clocks + `EXIT=0` lines: `all31-I-0f63e82/cmds/cmd*.argv` +
`summary.txt` (68-file EV). ROOT completed-logs + source review of the
exact 31 entries: `root-all31-completed-logs-and-source-review.json` (f
scratch).

### 3.2 Exact 3 additional argv (all actual native 0)

Frozen runner `additional-runner.sh` 92L, full SHA256
`505181b94aede718dcb74bef1888f1aa52192aca0846353d7a9740a6779e4707`
(exact reuse of the reviewed obs/guard/failure-STOP pattern):

- A: `uv run --frozen pytest tests/supply_chain` — 43 passed in 0.77s
- B: `uv run --frozen ruff check services/backend tests/repository tests/packaging tests/supply_chain tools migrations` — All checks passed!
- C: `uv run --frozen ruff format --check services/backend tests/repository tests/packaging tests/supply_chain tools migrations` — 352 files already formatted

Per-command clocks: `additional-I-0f63e82/summary.txt` (12-file EV).

### 3.3 Tool provenance (actual, from all31 EV `provenance.txt`)

uv 0.12.5 (x86_64-unknown-linux-gnu); Python 3.13.14
(`/tmp/oap-083-8-a/gate-wt/.venv/bin/python`); Node v24.22.0; pnpm
11.22.0; pytest 9.1.1 / pluggy 1.6.0 / pytest-asyncio 1.4.0 /
anyio 4.14.2 (cmd6 session header). The suites overlap (unit +
repository + supply-chain + CI-scope ruff); reported per command, NOT
summed into an invented grand total.

## 4. CI at I_f (authoritative, with one approved packaging rerun)

- Attempt 1: run `40529575762` (#976). Packaging job `122278377396`
  CANCELLED at 16:03:29Z against the exact 45m workflow limit annotation;
  raw logs show Ubuntu apt downloads under the Playwright install; smoke
  NOT STARTED. Attempt 1 raw evidence RETAINED (not relabeled).
- ONE approved exact cancelled-job rerun at I_f (no whole-workflow/source/
  settings/timeout/mirror changes): packaging job `122310687564`
  SUCCESS 16:29:12Z, raw 320186B SHA256
  `e27a8e28d4f33ff5ad015d5f62782ebffde57337b4eeeae21920874dbf8ab26b`;
  actual 40 browser PASSED cases / 19 projects + 49 packaging/compose-smoke
  OK. No further retry; no acceptance.
- Current I_f checks API (observed 16:36:38Z): 30/30 SUCCESS, where the
  STRICT required set is the 20 exact named apps in 4.1 and the 10 actual
  PG children in 4.2 are additional actual children — 30 is the observed
  total, NOT 30 strict required names. Proofs (f scratch):
  `root-If-after-retry-required20-proof.json`,
  `root-If-CI-retry-packaging-evidence-review.json`.

### 4.1 The 20 strict required apps (all completed/success at I_f)

| App | Job ID |
| --- | --- |
| Repository policy | 122310690782 |
| Node contracts | 122310747526 |
| Python 3.12 quality and package | 122310791093 |
| Python 3.13 quality and package | 122310752890 |
| Python 3.14 quality and package | 122310774822 |
| Foundation PostgreSQL 14 | 122310693127 |
| Foundation PostgreSQL 15 | 122310693719 |
| Foundation PostgreSQL 16 | 122310693628 |
| Foundation PostgreSQL 17 | 122310693761 |
| Foundation PostgreSQL 18 | 122310693292 |
| Compose and edge packaging | 122310687564 |
| Supply-chain evidence | 122310788026 |
| Markdown | 122310689776 |
| Mermaid | 122310762933 |
| Dependency review | 122310788869 |
| Detect supported languages | 122278375212 |
| Analyze (actions) | 122278457751 |
| Analyze (python) | 122278457835 |
| Analyze (javascript-typescript) | 122278457694 |
| CodeQL (app 57789; all other rows app 15368) | 122278775665 |

### 4.2 The 10 actual PG children (app 15368, all success)

| Child job | Name |
| --- | --- |
| 122310743366 | Foundation PG Group A PostgreSQL 14 |
| 122310762085 | Foundation PG Group A PostgreSQL 15 |
| 122310692083 | Foundation PG Group A PostgreSQL 16 |
| 122310742582 | Foundation PG Group A PostgreSQL 17 |
| 122310750464 | Foundation PG Group A PostgreSQL 18 |
| 122310690587 | Foundation PG Group B PostgreSQL 14 |
| 122310782371 | Foundation PG Group B PostgreSQL 15 |
| 122310742252 | Foundation PG Group B PostgreSQL 16 |
| 122310692169 | Foundation PG Group B PostgreSQL 17 |
| 122310691376 | Foundation PG Group B PostgreSQL 18 |

### 4.3 Current I_f PG raw logs (attempt 1 run, retained, not rerun)

`root-current-If-PG-raw-log-review.json` (observed 16:00:24Z): all 10
complete A/B raw job logs + 3 index files (13-file manifest, all hashes
equal; `source_Q_sha256` = frozen `45cf...` exact; all expected argv and
checkout exact). Per PG: group A = 2 exact-argv pytest invocations
(4 + 81 = 85 passed, 0 deselected); group B = 4 exact-argv invocations
(component 24 passed / 50 by-design deselected + theme 9 + pagestyle 12 +
Q 16 = 61 passed). Totals: 6x5 = 730 passed, 250 by-design component
deselected (NOT Q skips; no skips/xfails in any actual summary). Retained
limitation: DOT mode has no per-test IDs — P6 attribution = frozen 16
source inventory + complete unfiltered 16 pass per job. These are the
ACTUAL PG executions of attempt 1 run `40529575762`; the attempt 2 API
records 24 old execution times carried — NOT new PG/SBOM executions.

### 4.4 CI checkout identity (actual)

CI actual checkout merge `ca8046fdb13ca2548525d3b17c98d809d56b4abe`
(parents `d18b6e4c...` main + `0f63e82d...` I_f; tree EXACT I_f
`5badebced51b...`; message "Merge 0f63e82d... into d18b6e4c..."); the run
`head_sha` is I_f, not the literal checkout ref.
`root-If-CI-merge-ref-commit.json`.

### 4.5 Actual I_f six-image supply artifact (attempt 1 supply job, retained)

Supply job `122278377654` / attempt 1 artifact `12745463821`: ZIP 8914585B
SHA256 `7c12a86c42589044d782a21771fcf362b42877bc4a2deb6b374bfcfcde99d339`
(digest equals API); 54 ZIP members; SHA256SUMS 53 payload manifest
hashes (excludes itself), all matched; 58 raw index hashes all match; six
image rows (apache, backend, browser-worker, nginx, postgres, web) each
with all 3 digest cross-checks true (sbom / scan_sbom / scan — the "18
bindings" shorthand is these 6x3 cross-checks, not a JSON key); all 6
scans Critical 0 / ignored 0 / exception lists empty; actual severities
High 19 — full 6-tuples equal the accepted baseline; DB actual built
2026-10-27T06:30:41Z / checksum `16a91637...` / valid true (age 8.975h at
validation; URL filename 00:30:54Z is the archive name, not build time);
exception counts license 0 / vulnerability 0; revision `ca8046fd...`.
`root-peer-If-supply-artifact-adjudication.json` + the pane21-If-supply
raw index. The inventory includes MPL2/CC-BY-4.0 items — reviewed
individually, NOT a blanket all-permissive claim. CfT 156.0.8078.47 in CI
vs host Chromium 151 are distinct toolchains. This is the IMPLEMENTATION
I_f CI artifact, NOT a fresh LOCAL6 or final SELF artifact.

## 5. Q gate — Q80 at I_f (fresh generic qualification module, 5 versions)

Sealed runner `qpg-serial-f.sh` 759L SHA256
`3779bcbe64ad4909ba2e10731b54cebb26014578e632db18d4bdfd9521f0701d`
(corrected copy through the ROOT-reviewed 424->548->565->647->656->676->
699->701->749->759 source repair chain; all prior findings repaired and
verified at 759). Direct bare exec launch 19:10:57.201Z, SAME primary
handle terminal native 0 at 19:12:09.692Z. One fresh owned PG per version:
PG14.24 / 15.19 / 16.15 / 17.11 / 18.6, each 16 collected / 16 passed, no
skips/xfails/deselected, IDENTITY_OK, child native 0. Controller-owned
disposal: stops/rms native 0, no forced mode, 3-resource-per-case exact
raw 0B absence proofs, healthy-daemon query natives 0; 271-file EV
manifest `qpg-I-0f63e82-attempt1/`. ROOT independently verified (Q80).
This qualifies the fresh generic Q at I_f; it is NOT a single-fix causal
proof and NOT acceptance.

### 5.1 Per-case index (every case child native 0, pytest_outcome 0, wait_cli 0, inspect exited/0, 16/16)

| Case | PG image | PG container (12) | runner (12) | volume (12) | log B | log SHA256 (12) | CASE_END (UTC) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pg14 | postgres:14-alpine | `fee67a9affd3` | `2475d67769fa` | `d5ea58335f4a` | 1645 | `85a22192f86f` | 19:11:11.731232 |
| pg15 | postgres:15-alpine | `d905b0ad1ae2` | `0154c0f97544` | `1e4a2e46854e` | 1645 | `daf4e803daa1` | 19:11:26.443457 |
| pg16 | postgres:16-alpine | `301eeb3dcb81` | `dd7304c19288` | `595f2fde8801` | 1645 | `3100f08764df` | 19:11:40.944551 |
| pg17 | postgres:17-alpine | `4c83219b3ee9` | `c518ec5110df` | `a9664dc3995f` | 1645 | `52cdea7e47d5` | 19:11:55.040684 |
| pg18 | postgres:18-alpine | `2ca4e5a8789c` | `522f72fb07c2` | `4ab1ad538999` | 1642 | `d8f02ac84eed` | 19:12:09.538880 |

Container names `qpgf-pgNN-0f63` / `qpgf-runner-pgNN-0f63`; owned label
`oap-owned=083-8f/qpg/I-0f63e82/attempt1`; runner image pinned ID
`sha256:70729b46c69b4f1e...` (same for all 5). Full 64-char IDs, per-case
TEST_T0/T1 and the 10 cap2 natives: `ledger.txt` + `cap2-natives.txt` in
the 271-file EV.

### 5.2 P1-P6 criterion -> frozen Q source / actual 80 pass index

16 test functions per version x 5 versions = actual 80 pass (all child
native 0); the 16 names are exactly the frozen module's functions (also
the CI `test_functions` list in 4.3):

- P1 (1): `test_p1_frozen_020_anchors_are_public_and_uv_lock_pinned` — frozen 0.2.0 registry anchors public + uv.lock pinned.
- P2 (1): `test_p2_mixed_table_whole_session_promotion` — real row values, site isolation, in-window + post-scope whole commit, no pending (representative P2 families: page, model/content_type, field, item, relation).
- P3 (4): `test_p3_empty_session_is_no_op`; `test_p3_same_value_update_preserves_canonical`; `test_p3_repeated_writes_coalesce_to_last_value`; `test_p3_insert_delete_net_zero`.
- P4 (2): `test_p4_row_conflict_refusal_preserves_pending` (actual first touch before A commit); `test_p4_schema_conflict_refusal_restores_and_promotes` (row/schema drift).
- P5 (5): `test_p5_deferred_cycle_commit_succeeds`; `test_p5_nondeferred_cycle_refused_before_promotion`; `test_p5_dangling_deferred_state_refused_at_immediate_stage`; `test_p5_dangling_composite_fk_deferred_refused`; `test_p5_write_time_refusal_is_distinct` (final FK refusal vs write time).
- P6 (3): `test_p6_escaped_postcondition_rolls_back_promotion`; `test_p6_task_cancel_rolls_back_promotion`; `test_p6_reviewer_termination_rolls_back_promotion` (original 30s deadline; rollback/pending/locks/GUC/replacement checks; bounded pool close).

Generic fixture only: NOT an actual product audit/revision/outbox/
publication. No new tests; nothing claimed stronger than the source
assertions.

### 5.3 The 3 frozen qualification paths (test + CI; byte-unchanged S_e -> I_f)

Per f-order "Exact allowed footprint" (these are the three qualification
PATHS, not "three test files"):

1. `services/backend/tests/integration/test_foundation_whole_session_qualification.py` — 1844L; git blob `88acdb3c...`; content SHA256 `45cf79671261212c19143315daeaecfc1b01b1e48d0b3c2cdf9e85cf881563a8`.
2. `tests/repository/test_foundation_ci.py` — git blob `236bd142f76247892d3d2a32c95c10b4cf6f6ff7`.
3. `.github/workflows/ci.yml` — git blob `331cfa94e841e32af4b2f182e7c008ecd21586f1`.

## 6. FULL gate — unfiltered backend integration directory, ONE owned PG18

### 6.1 Attempt 1 (ACTUAL FAILURE, preserved)

Sealed 793L `59e7b065...` direct exec; SAME primary handle terminal native
1 at 20:28:56.495Z: `docker-wait` bounded deadline (wait CLI 124) after the
1800s test budget; 363 collected, 179 partial progress dots, zero F/E/s
markers in the partial prefix, no final pytest summary; runner exited 137
during owned disposal (preserved; stop/rm rc 0 is disposal evidence, not
graceful-SDK proof); PG stop 0; all 3 owned resources proven absent raw 0B;
CLEANUP_RC=0. ROOT budget planning ERROR: the prior actual FULL347 (083-7-b)
passed in 3647.81s (1:00:47, raw 51689B SHA `a90bc6cd...`), so the 1800s
budget was below the known baseline (`root-FULL-budget-miscalibration-
historical-evidence.json`). No test/product assertion failure; no cause
claim beyond observed budget exhaustion/early cutoff. FULL1 EV (64 files)
and sealed source snapshot retained, not relabeled, not rerun.

### 6.2 Budget-corrected source revision (SOURCE ONLY, then approved)

Eight-line diff vs sealed 793 (`f-full-attempt2-diff-vs-sealed-793.txt`):
`WAIT_S=1800 -> 5400`, both nominal-budget header lines, EV
`full-I-0f63e82-attempt2`, owner label/value `083-8f/fullf/I-0f63e82/
attempt2`, PG/runner names `...-0f63-attempt2`. All other control bytes
exact; whole candidate measured in memory before write; one changed
`bash -n` native 0 at 20:35:51Z. New revision 793L/47586B
`af08faf73e1bb8a3dc03102e583f2dd51b371fe13f8a04b8f0899cafad64612e`.

### 6.3 Attempt 2 (ACTUAL PASS)

Approved ONE corrected execution. Launch 20:40:36.950Z (ROOT-observed;
printed 20:40:36.977Z), SAME primary handle 4782, terminal
21:44:18.710768512Z, actual `FULL2_PARENT_NATIVE=0` marker. **argv
deviation (preserved, not repaired after the fact):** the actual exec
string was `date ... && bash full-integration-f.sh; echo
FULL2_PARENT_NATIVE=$? && date ...` rather than the approved bare
command: the script bash ran WITHIN that compound (not as a separate bare
invocation). The `;`-separated marker records the AND-list native, which
equals the script native in THIS run because script start proves the
leading date succeeded; the outer tool exit (final date/echo) is not sole
proof of script success and is reported separately. Receipt
`full2-exec-argv-deviation-receipt.txt` (written 20:45:21Z after ROOT
observed the deviation). Result: `child_native=0`,
`pytest_outcome=0` (identity_ok=1, session_marker=1, wait_cli=0, terminal
inspect exited/0), **363 passed in 3809.48s (1:03:29)**; actual count
parser `COUNT=OK`: passed=363 total=363 failed=0 errors=0 skipped=0
xfailed=0 xpassed=0 deselected=0 warnings=0; `ACTUAL_MATCH=True` vs
historical 347+Q16=363 (claimed only because actually measured). pytest
reported duration 3809.48s (3809.48/3647.81 = 1.044x the FULL347
baseline); the host monotonic test phase was 3814.097s (1.046x, reported
distinct); remaining wait headroom 5400-3814.1 = 1585.9s inside the fixed
5400s wait (finite bound, not a guarantee; no deadline reset). Cleanup:
runner predelete State.Running=false (normal exit; stop skipped, actual
State recorded, not inferred) rm rc=0; PG stop rc=0 (mode=stopped) rm -v
rc=0; volume absent-proven; all 6 cap2 natives 0; no RESIDUAL/forced.
`END_HEAD/END_TREE` = I_f, raw status 0 lines, `CLEANUP_RC=0`,
`OVERALL=0 FULL_DONE`, `FINAL_EXIT=0 PRIMARY_RC=0 CLEANUP_RC=0
INTERRUPTED=0`. True post-cleanup source facts 21:46:20Z (all natives 0,
all 5 source hashes unchanged). One bounded read-only progress snapshot at
21:13:25Z (native 0, 2195B partial raw; no pass/stall claim from it)
retained in `full2-progress1-*`. PG stderr 428268B ALL hashed +
prefix/shutdown-tail reviewed (not all SQL lines human-read; SQL ERROR !=
pytest failure). EV `full-I-0f63e82-attempt2/` (63-file manifest) retained.

### 6.4 EV key-file index (FULL gate)

- Attempt 2 (63-file EV `full-I-0f63e82-attempt2/`): `full.log` 7126B SHA256 `b938d2aef7a127002854663636b7521e2d4f2cf8c3cf2dc480327a382f4c0a3c` (final pytest summary + ACTUAL_MATCH line); `summary.txt` (per-phase facts, CLEANUP_RC=0, FINAL_EXIT=0); `ledger.txt` (owned container/volume IDs); `cap2-natives.txt` (6 checked natives 0); `cleanup.log` + 3 absent-proof file sets (raw 0B).
- Progress-only snapshot (retained, no pass/stall claim): `full2-progress1-logs.2026-10-27T211325Z.stdout` 2195B SHA256 `59c96bd7052fca4e68c878a7db91c84385a7b63eed590470b1108a1f313cdb1c`.
- Attempt 1 (64-file EV `full-I-0f63e82-attempt1/`): `full.log` SHA256 `113425d559c92ee34437924fc139ce263c3254be2c7ee7f0f6cd9ebd19983ae1` (partial 179/363 dots, no final summary) + the same cleanup/absence structure.
- Post-cleanup true source facts: `full2-post-cleanup-facts.txt` (21:46:20Z).

## 7. P7 diagnostic — public dependencies() characterization, ONE bare exec

### 7.1 Sealed source

Wrapper `p7-diagnostic-f.sh` 771L/45846B
`b56265e79cefc3007e97d746da3184b3bb5e751c8739f14a6fab149acb842c24`,
derived from sealed Q759 with ONLY the permitted differences (stage
identity/EV/labels, singleton PG18, wait 600s, exact command
`uv run --frozen python $IDENT 2>&1 && uv run --frozen python $SCRATCH`,
ONE added `$SCRATCH:ro` mount, SCRATCH SHA START + guarded all-exit END,
P7 marker/wording, single-log footer, P7_DONE OVERALL). Revision history:
742 -> 757 (guarded all-exit END moved into on_exit) -> 771 (final safety
followup: `w` (exit-95 hazard after `trap - EXIT`) replaced by the
non-exiting `wl` writer; every missing-START/missing-file/read-fail/
malformed/write-fail/mismatch branch leaves explicit evidence AND (where
the conditional holds) latches `CLEANUP_RC` so the wrapper final exit is
nonzero — the missing-START latch is conditional on otherwise-clean state,
not every branch latches on all failures, and only the normal exit path
executed in the actual run. The actual child native/trace is retained
separately in the EV; the wrapper OVERALL may aggregate 1, so the first
nonzero code is NOT universally preserved (per ROOT correction)). Body `p7-scratch-f.py` 186L/7716B
`494df78a00a0572c85606aa30720c9431d38fa9df61fd5138fa8a743f5abd403` =
exact legacy 160L `915c3e2a...` + 26 print-only metadata lines (session/
site/field/item/relation IDs, four operation IDs, expected-pending set,
explicit TYPE_P6, actual observed op set) inserted before the public
`dependencies()` call; ALL fixture/unwrap/operations/dependencies/
expected-pair semantics, uncaught real failure, and cleanup preserved.
Statics: wrapper `bash -n` native 0 at 21:08:26Z; body target 3.13.14
`py_compile` native 0 at 20:56:06Z (syntax-only; no import/selftest/DB).
Caps honored: wrapper 771<=777 (reserve 790)<=800; body 186<=186;
aggregate 1564<=1600; new-3-path 1750<=1780; DB-runtime inputs 2571<=2601.
ROOT sealed both at 21:10:37Z.

### 7.2 Actual run (ONE bare exec)

`bash /tmp/oap-083-8-f/p7-diagnostic-f.sh` — EXACT bare command, no
leading date/echo/pipe (FULL2 deviation lesson applied). Direct terminal
native 0: P7_START_UTC 21:48:57.596Z, RUN_END_UTC 21:49:09.338Z (~11.7s,
warm daemon; test phase 4.0s of the nominal 600s wait). `child_native=0`
(composite identity&&p7-diagnostic), `p7_outcome=0`, wait_cli=0, terminal
inspect exited/0, `P7_CHILD_EXIT=0`. IDENTITY_OK (PG18.6); legal fixture:
`ops_in_session=4` with all metadata emitted, including
`meta_type_p6=33333333-0006-4000-8000-000000000006` and actual ops equal
to the expected set. Owned resources: runner `384a6cdb...`, PG
`6a9ca407...`, volume `2b0290a0...` — all normal terminal exit 0 /
stop-rm 0 / native healthy 0 / exact raw 0B absence proven;
`SCRATCH_SHA256_END` written via the new guarded all-exit post-cleanup
path (normal zero-exit branch exercised; the missing-START/missing-file/
malformed/failure branches are NOT counterfactually covered at runtime);
RUNNER/IDENT/SCRATCH SHA START == END. `FINAL_EXIT=0 PRIMARY_RC=0
CLEANUP_RC=0 INTERRUPTED=0`; END source clean at I_f; true post-cleanup
source facts 21:50:34Z (all natives 0, hashes unchanged). EV
`p7-I-0f63e82-attempt1/` retained (root 63-file manifest).

### 7.3 RESULT + CRITICAL source-interpretation erratum (documentary, not runtime)

Actual returned pairs (print-only characterization, NOT pass/fail
qualification, NOT pytest/P1-P6 success): exactly three op-UUID pairs,
each `(referenced_op, op_rel)` — i.e. `(op_item_x, op_rel)`,
`(op_item_y, op_rel)`, `(op_fd, op_rel)`. The scratch's own expected-pair
block printed `oriented_present=False reversed_present=True` against its
EXPECTED orientation `(op_rel, referenced_op)`.

**Erratum 1 (pair direction):** the public source defines pairs as
`(depends_on, operation_id)` — core.py 1428..1440 + operations.py
575..584, SQL RETURNS matching (1716). The three actual pairs are the
CORRECT documented direction. The scratch expectation used the opposite
convention, so its `reversed_present=True` output is an artifact of the
scratch expectation, NOT a reversed-API defect. No desired-bug assert, no
rerun; raw preserved. Peer audit adjudication
(`root-peer-P7-direction-PK-audit-adjudication.json`) concurs.

**Erratum 2 (false PK/ordinal claim in current docs + scratch printed
prose):** the scratch printed characterization prose (and
`docs/FOUNDATION_INTEGRATION.md` lines 226..228) claims the dependencies
"skip 1-2 column PK tables at ordinal_position >= 3". FALSE. Actual
source: cow_sql_functions.py 529..543 creates CHANGE-table PRIMARY KEY
`(session_id, operation_id, ORIGINAL_PK...)`; `_cow_dirty_changes_tables`
(1599..1613) returns CHANGE-table names; the `ordinal_position >= 3` rule
strips the TWO COW bookkeeping prefixes from the change-table PK — it does
NOT skip original 1-2 column PK tables. This is a documentary / source-
interpretation error, not a failed P1-P6 and not a newly observed SDK bug;
the doc-only repair is planned for 083-8-g (NOT activated). The immutable
executed scratch and this history are preserved; no edit hides the old
claim.

**Erratum 3 (no over-claim):** the fixture's FKs are the frozen fixture's
COMPOSITE `(site_id, id)` foreign keys (fixture lines 224..232 / 253..266)
— the peer's "single-column FK fixture" characterization is NOT copied.
Three correct pairs on this 4-operation legal fixture do NOT prove full
graph completeness, no UUID/TEXT SQL exception occurred here, and the FK
metadata `kcu`/`ccu` lacking ordinal pairing / single-column UNION remains
a SEPARATE source lead — none of that is demonstrated, cured, or claimed by
this print-only diagnostic.

### 7.4 EV key-file index (P7)

63-file EV `p7-I-0f63e82-attempt1/`: `p7.log` 2958B SHA256
`b8dea48191f80362d76b8da864f49c3fc698511d1e99cef6258101f2c3bb9402`
(metadata + dependencies() output); `summary.txt`; `ledger.txt`;
`cap2-natives.txt`; `cleanup.log` + 3 absent-proof file sets (raw 0B);
true post-cleanup source facts `p7-post-cleanup-facts.txt` (21:50:34Z).

## 8. Deviations and errata (complete, honestly preserved)

1. FULL2 actual argv (leading date + `;`-separated marker echo) vs approved
   bare command — section 6.3; actual script native captured by the marker;
   outer native = final date/echo; no repair/rerun.
2. FULL1 actual budget failure + ROOT 1800s planning error (baseline
   3647.81s) — preserved as history, section 6.1.
3. QPG 205L `.draft` written despite the 193 prewrite cap (procedural
   deviation disclosed, no retroapproval, no delete/pack) and the full
   424->759 ROOT-reviewed repair chain.
4. CI packaging attempt 1 CANCELLED at the 45m limit; ONE approved exact
   job rerun (attempt 1 retained), section 4.
5. P7 builder prewrite assertion failures (21-line block before write;
   count-assertion typos) retained as mechanical prewrite evidence, not
   runtime attempts; the 20:44:13 two-comment-line join to fit 180 was a
   packing deviation, later superseded by the natural 186 (ROOT arithmetic
   180+TYPE1+actualprint4+unpack1=186) — chronology preserved.
6. P7 wrapper 742->757->771 revisions: `w`-exit-95 hazard in the all-exit
   block replaced by `wl` latch per ROOT final safety followup; BUDGETS
   provenance wording corrected to nominal + bookkeeping.
7. Launch-deviation receipt written 20:45:21Z (not at launch); the
   universal "leading date cannot fail" claim corrected to observed fact.
8. SBOM generator during the f source phase wrote 112 components before
   its own rollback (record deviation; final committed sbom.json is as
   reviewed); initial SYNC/PUSH natives UNKNOWN (piped tail) recorded as
   such; no receipt-only rerun.
9. ROOT response-listener recovery: old 13469/PID2379501 disappeared
   (cause UNKNOWN, no successful receipt, original receipt archived);
   exactly one same-source replacement listener 59318/PID2771170 on the
   same response FIFO; no control replay; exactly one future OK.
10. ROOT's first read-only evidence parser had a missing `re.M` /
    AttributeError BEFORE writing the P7 review; corrected on the SAME raw
    parser — no diagnostic/SDK/test rerun.
11. P7 pair-direction + PK/ordinal documentary errors (section 7.3),
    including the scratch's printed prose and the current
    FOUNDATION_INTEGRATION.md lines 226..228.
12. QPG volume labels were null: reported exact known-resource absence,
    not a global label-volume claim.

## 9. NOT RUN / pending (explicit)

- LOCALWHOLE: NOT RUN (old carry VOID). Historical actual baseline
  WHOLE 1098.056061s (~18m18) retained as prospective budget evidence only.
  Fresh plan requirements digested (fresh-namespace positive/negative
  proof, pre-disposal owned ID/mount/volume/label capture without secret
  exposure, tool native kept separate from child results, actual post-
  cleanup absence via native-checked healthy query/raw bytes, honest
  internal retries, stop-on-actual-final-failure to ROOT; SHA256SUMS
  excludes itself; smoke captures both streams; no broad new framework).
  Complete source/forecast/finite approval required first.
- LOCAL6: NOT RUN (old carry VOID). Historical actual baseline LOCAL6
  1653.453885s (~27m33) retained as prospective budget evidence only; same
  planning requirements; fresh evidence (scanner DB actual
  built/checksum/valid/age + six actual scan bindings) required.
- Final SELF acceptance / merge: outstanding; ROOT alone accepts.
- 083-8-g: intended for the truth-doc repair (FOUNDATION_INTEGRATION.md
  226..228) + remaining fresh gates; NOT activated; no source/doc edit
  performed under f.
- Full generic/product acceptance (true-U, audit, causal closure,
  publication, release): unchanged and unapproved.

## 10. Publication mechanics (report-only SELF)

Prepared as TEMP inside `oap/reports` (same filesystem), linted with the
repository markdownlint config + CLI 0.23.2 `--no-globs` on that same
complete file (native 0, one file, zero issues; any edit re-linted),
same-inode atomic rename + parent fsync, then a single report-only commit
with sole parent I_f and sole changed path
`oap/reports/083-8-f-upgrade-released-driver-and-qualify.md`, pushed and
verified as the remote PR #112 head. The publication receipt (UTC,
raw-ns, pre-rename hash/inode/size, the commit SHA — which IS the SELF SHA
per protocol, never pre-invented inside this commit — and the actual
remote head/parent/path/bytes proof) is recorded at
`/tmp/oap-083-8-f/f-report-publication-receipt.txt` (f scratch).

## 11. Confirmations

- Scope: only I_f (13 paths, section 2) and this report. No production
  function/schema/authority source change (the driver runtime version DID
  change, 0.31.0 -> 0.32.0 released pin). The 3 frozen qualification
  test/CI paths byte-unchanged (section 5.3). Only ordered frozen
  install/setup at I_f (`uv sync --frozen` / `pnpm install
  --frozen-lockfile`); no input/source/env mutation during the live
  gates; no new package family (driver dependency version updated).
- Secrets: none committed or printed; fake test credentials only
  (`qualification-admin`) in owned disposable containers; no capability,
  cookie, or source-internal preview credential in any artifact.
- Production: no production system/data/credential access; Docker used
  only for ordered owned disposable PG/runner containers, all disposed
  with exact absence proofs.
- Skips: none in Q80/FULL2 actual runs (skipped=0 both); the NOT RUN list
  in section 9 is explicit, never relabeled as pass.
- Extra PR: none; PR #112 only; no merge/auto-merge/close.
- Next ID: none chosen; 083-8-g belongs to strategy.
- `COMPLETE`/`OK` never means accepted: strategy alone independently
  reviews and merges; this PARTIAL report is an evidence index.

## 12. Historical index (immutable prior rounds — referenced, not repeated)

Old 0.31.0-era P6 contract failure (the one f upgrades away): frozen
I3-era CI PG15 job `122039337259` + PG16 job `122039337087` —
`test_p6_reviewer_termination...` with p6-restored-pending-enter 30s +
pool.close 30s, each 16 collected / 15 passed / 1 failed + 1 teardown
error / native 1; reproduced identically at I on PG17 job
`122057296148` + PG18 job `122057295646`. At I_f (0.32.0), all Q16
including the three P6 tests pass locally (Q80, section 5) and in CI (Q
16 per PG job, 4.3); the upstream closed-holder change (issue 1307 / PR
1324) is a consistent source lead, NOT a proven causal closure of every
old failure.

0.31.0-era diagnostic rounds (immutable reports + ROOT reviews; no
history rerun in f): b harness failure before the runner — ZERO SDK
cases; c driver case 0 then SDK case 1 actual child 5 + unsafe 7, cases
2,3 PREVENTED; d ONE SDK case NO_REPRODUCTION (codes []), not a cure; e
case 1 actual child 5 + unsafe 7 (pool.close 30s FAILED), the before-
cancel acquire frame was `Queue.get` BEFORE any holder acquire/connect,
cases 2,3 PREVENTED; controller safe disposal 0/absence != SDK qualified
cleanup. Full records: `oap/reports/083-8-{b,c,d,e}-*.md` + the b/c/d/e
scratch ROOT reviews.

Standing f reporting errata (retained, indexed not repeated): e-report
MD018 fix; f initial wrong-cwd lint; SBOM 112 write before own rollback;
initial SYNC/PUSH natives UNKNOWN (piped tail); listener recovery
13469 -> 59318; QPG 205L `.draft` prewrite-cap deviation; FULL1 1800s
budget error (ROOT's); FULL2 argv deviation. Indexes:
`f-evidence-records-v2.txt` + the root provenance/review files (f
scratch).

## 13. Round chronology (actual UTC clocks, 2026-10-27)

| Event | UTC |
| --- | --- |
| f order prelint + same-inode atomic active; ONE control OK closed | 14:46:56; 14:47:08 |
| ROOT full-parsed working `uv.lock`; I_f commit | 15:14:34; 15:17:35 |
| ALL31 (31 cmds, all 0) / additional (3 cmds, all 0) | 15:57:21 -> 16:10:27 |
| CI packaging attempt 1 CANCELLED (45m); exact job rerun SUCCESS; 30/30 observed | 16:03:29; 16:29:12; 16:36:38 |
| Q80 5 cases (terminal native 0) | 19:10:57 -> 19:12:09 |
| FULL1 (terminal native 1); FULL2 `bash -n` 0; FULL2 launch -> terminal; FULL2 post facts | 19:58:38 -> 20:28:56; 20:35:51; 20:40:36 -> 21:44:18; 21:46:20 |
| P7 ROOT seal; P7 ONE bare exec (child 0); P7 post facts | 21:10:37; 21:48:57 -> 21:49:09; 21:50:34 |
| ROOT f-PARTIAL publication decision | 21:56:57 |
| publication receipt clocks | in the publication receipt (section 10) |

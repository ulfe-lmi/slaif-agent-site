# OAP Execution Report — 083-3-e: structural race assertion closure

- ID: `083-3-e`; Objective 083, semantic increment 3; CLOSURE_ONLY.
- Mode: `AMENDED_EXISTING_PR`.
- Status: `COMPLETE`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#102](https://github.com/ulfe-lmi/slaif-agent-site/pull/102), state OPEN, branch
  `oap/083-3-a-cache-outbox-consumer`, base `main`.
- Starting report-only S-d:
  `69d43347cb9f7060bee2edac0de94d58513b3fee`; S-d first parent / d
  implementation head (I-d): `fe79b3af3a345df869e20fbfa0557e6b03ce7c9f`;
  verified main `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`
  (2026-10-18T02:55:37Z).
- Transcript T-e: `cea30efc99cc84a2f23abf747f9dcb80d63fb906` (activated
  order and `oap/active` bytes only, unchanged).
- Implementation head SHA (I-e): `f459ad38f7379adb7f48d5fb55f1d06b1c81b2a8`.
- Report publication commit: SELF.
- Pushed commits this round: T-e `cea30ef`, I-e `f459ad3`.
- Activated order: `oap/orders/083-3-e-race-assertion-closure.md`,
  SHA-256 `3f46c3344f39159ac226ce699e7b93fee991d66bb1c51eee0e235807a6d20f64`.
- Active file bytes: `083-3-e\n`, hex `3038332d332d650a` (verified by xxd).
- Control FIFO OK: exact `4f4b` (2 ASCII bytes, no LF) received
  2026-10-18T03:03:48Z by the persistent foreground reader (receipt-4,
  open wait 324.050 s); `active` reread and matched this order exactly
  before execution.

## 1. Preflight, identity and reconciliation

GitHub reconciled read-only: PR #102 open on the required branch with base
`main`; S-d is the exact starting head and its first parent is I-d; exactly
one open PR on the branch (no duplicate increment PR); no existing `083-3-e`
report. T-e committed and pushed first with byte-identical order and active
content (2 files, +188/−1). At 02:54:52Z I-d carried 20 COMPLETED/SUCCESS
checks (CI `39087639095` and CodeQL `39087639081` both attempt 1); that does
not prove the full local integration collection, and this round's acceptance
criteria are evaluated at the e heads.

## 2. Exact change set (one non-transcript file, two assertion hunks)

| File | Change |
| --- | --- |
| `services/backend/tests/integration/test_human_editor_production_http.py` | Two assertion expressions only: the `restore` vs `redirect-create` race assertion and the `redirect-delete` vs `dependent-create` race assertion. Each `sorted((a, b)) in ([...])` form was replaced by the endpoint-ordered tuple membership `assert (a, b) in (...)`. Test name, fixture, setup, calls, payloads, barrier/lock mechanism, all later cases and assertions, and the response-body diagnostics in each assertion message are preserved. |

`git diff --stat` against T-e: 1 file, +8/−9 (fewer than 20 substantive
changed lines, per the predeclared budget). The file was last modified before
the PR base (`d2bc4fb`, Objective 078-x, an ancestor of main `214909f`); no
other file in the PR differs. `uv run --frozen ruff format` normalized the
two hunks; `ruff format --check` and `ruff check` on the file are clean.

## 3. Reproduction of the predicate mismatch from retained d evidence

Retained d evidence (archived by strategy):

- `/tmp/oap-083-3-d/integration-final.log`, SHA-256
  `5f94be98b491434ed67b05f99743d19c5cefd89a965d0c9cab910bf3c74e63b7`:
  `1 failed, 319 passed in 4081.34s`, failed node
  `test_human_editor_production_http.py::test_editor_agent_structural_races_share_workspace_site_lock`;
  observed endpoint-ordered result at the first corrected site:
  `restore=409` (`RESOURCE_CONFLICT`), `redirect-create=201`
  (`REDIRECT_CREATED`); `sorted((409, 201))` is `[201, 409]`, which the old
  assertion rejected because its second alternative `[409, 201]` is an
  unreachable sorted output.
- `/tmp/oap-083-3-d/integration-single-retest.log` (d isolated single-node
  diagnostic, `RETEST_EXIT:1`, identical assertion and identical ordered
  pair). This isolated diagnostic remains distinct from the failed complete
  run; neither is aggregated with any e result.
- The second site (redirect deletion vs dependent redirect creation, lines
  1581-1586 in the pre-fix file) carried the same unreachable `[409, 201]`
  sorted alternative; it was not reached in the failed run because the
  first assertion aborted the test.

Both complete surrounding test cases were read. The corrected assertions
accept exactly the ordered endpoint pairs the order names:

1. `(restore, redirect_create) in {(200, 409), (409, 201)}`
2. `(delete, dependent_create) in {(200, 409), (200, 422), (409, 201)}`

Swapped endpoint meanings, double success, double conflict, 5xx or any other
status remains rejected; response-body diagnostics are preserved in both
assertion messages. No application code, fixture, role/grant, capability,
lock function, timeout/barrier helper, filter/skip/xfail, dependency,
lockfile, pin, policy, scanner, workflow, generated contract, documentation
or other test changed: `git diff T-e..I-e --stat` shows the single test file
only. The test corrects its representation of existing allowed outcomes; it
changes no product authority (agent context remains server-owned and
site/workspace-bound; publication human-only and reviewer-atomic; media
immutable; artifacts private; browser observational and confined; foundation
registry-only 0.2.0 with exact uv.lock hashes).

## 4. Focused race test to completion (all later assertions included)

Command `uv run --frozen pytest
"services/backend/tests/integration/test_human_editor_production_http.py::test_editor_agent_structural_races_share_workspace_site_lock"
-q`, `set -o pipefail`, `${PIPESTATUS[0]}`, fresh fixture database, no
concurrent load, tree `f459ad38`:

- START 2026-10-18T03:09:07Z, `1 passed in 34.97s`,
  `RACE_TEST_EXIT:0 2026-10-18T03:09:43Z`
  (`/tmp/oap-083-3-e/race-test.log`).

The test ran to completion including every case after the first corrected
assertion, reaching and passing the second corrected assertion.

## 5. Definitive full integration directory (isolated, unfiltered)

Command `uv run --frozen pytest services/backend/tests/integration -q`,
`set -o pipefail`, `${PIPESTATUS[0]}`, disposable PostgreSQL
`slaif-integration-pg-0833b`, fresh per-test fixture databases, no
concurrent smoke/build/pytest load (the focused race test had completed at
03:09:43Z before this run started; the clean-copy gates started only after
this run finished), tree `f459ad38`, log
`/tmp/oap-083-3-e/integration-final-e.log`:

- START 2026-10-18T03:09:49Z,
  **`320 passed in 3962.01s (1:06:02)`**,
  **`INTEG_E_EXIT:0 2026-10-18T04:15:56Z`** — 320 PASSED, 0
  failed/errors/skips, actual exit 0. No filtering, no reduced collection,
  no xfail; no aggregate 319+1 substitute: this single completed run is the
  result.
- The previously failing node
  `test_human_editor_production_http.py::test_editor_agent_structural_races_share_workspace_site_lock`
  passed in this run, with the race outcome landing on the previously
  unreachable (now accepted) branch or the restore-winning branch; both are
  exact allowed endpoint-ordered pairs.
- The d round's failed complete run (section 3) and d isolated diagnostic
  remain distinct historical records; nothing is aggregated across rounds.
- No child process was killed or left running; the session exited with its
  real exit 0.

## 6. Standing checks on a clean tracked verification copy (I-e tree)

Fresh copy created by `git archive` of
`f459ad38f7379adb7f48d5fb55f1d06b1c81b2a8` into `/tmp/slaif-verify-e`.
Identity: tracked tree hash `c19d293535e9d8c6a6c33fa204c092680346ab57`;
1083 tracked files; pre-gate content manifest (path + SHA-256) SHA-256
`48fdb2b70c79e78cf24df609ed20ad456c31ba7c61daeac0bda62df066b6fe9d`
(`/tmp/oap-083-3-e/verify-e-content-manifest.txt`); file list byte-matches
`git ls-tree -r` of I-e; no untracked runtime artifacts present. All 31
standing commands exited 0 (log `/tmp/oap-083-3-e/verify-e-gates.log`,
START 2026-10-18T04:16:02Z, END 04:21:25Z — started only after the full
integration run finished):

- Python: `uv lock --check`; `uv sync --frozen --all-groups`;
  `uv run --frozen ruff check services/backend tests/repository tools`
  (All checks passed); `ruff format --check` (same paths, clean);
  `uv run --frozen mypy` (Success, 310 source files);
  `uv run --frozen pytest services/backend/tests/unit tests/repository -q`
  (788 passed, 3 warnings, 26 subtests passed in 29.15 s);
  `uv build --out-dir /tmp/slaif-agent-site-distributions-e`
  (sdist + wheel built).
- Process smoke: all ten `python -m slaif_agent_site.<module> --check`
  commands exit 0.
- Node: `node --version` (v24.22.0), `pnpm --version` (11.22.0),
  `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm format:check`,
  `pnpm typecheck`, `pnpm test` (33 project tests + 8/8/24/19 package
  tests, all passed), `pnpm build`, `pnpm licenses list --json` (full JSON
  retained at `/tmp/oap-083-3-e/verify-e-licenses.json`).
- Preparation: `python -m compileall -q tools tests/repository`;
  `python -m unittest discover -s tests/repository -p 'test_*.py'`
  (71 tests, OK); `python tools/check_repository.py` (PASS);
  `python tools/check_mermaid.py` (16 diagrams in 3 files, 541 Markdown
  files scanned, CLI 11.16.0, exit 0 under a temporary
  `kernel.apparmor_restrict_unprivileged_userns=0` relaxation; original
  value 1 restored and verified on every exit path:
  `SYSCTL_BEFORE: 1` / `SYSCTL_RESTORED: 1`);
  `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` (535 files, 0 issues).

## 7. Adopted d evidence (byte-identical unaffected inputs)

I-e differs from I-d by exactly one test file; every production, build,
package, runtime and security input is byte-identical to the tested I-d
(diff `fe79b3af..f459ad38` = the single test file). The following d results
are adopted — not rerun and not relabeled — with the tested head, hashes and
exact outcomes named:

- Six-image qualification pipeline (tested at I-d `fe79b3af`):
  `PIPELINE_EXIT:0`, `supply-chain-evidence: OK images=6 critical=0 high=43`,
  checksum and gate OK; `index.json` SHA-256
  `88c675d3fbc5dcbef26ca82cd08f0471a947adb1e5122af9146b2b37b3046da0`;
  per-image scan/SBOM hashes, scanner and Grype v6.1.10 provenance as
  recorded in the immutable d report section 5; strategy's independent
  bundle review exit 0. Reproducibility as characterized in the d report:
  normalized application/package-level equality across the double builds
  within the pre-existing OCI layer-timestamp boundary; the images are not
  bit-identical.
- Candidate-8 matrix record and `test_policy.py` assertions (tested at I-d):
  `image_digest sha256:3d66c69ff3bc28b86f5781f4bb5a1af6d90c92b7d94766614cddc2834a903007`,
  `1719` browser-worker matches, `43` high review findings,
  `checksum_validation PASS`; post-edit `tests/supply_chain tests/packaging`
  86 passed + 54 subtests, exit 0.
- Complete 19-project Compose smoke (tested at I-d): `SMOKE_D_EXIT:0`
  (2026-10-18T01:15:34Z to 01:33:29Z), all six images built fresh, six
  stable devices, Apache adapter build and `apachectl -t` Syntax OK,
  `browser-worker-image-policy: OK ... cft_revision=1697595
  chromium=155.0.8059.84`.
- Backend runtime evidence from the fresh d smoke image (tested at I-d):
  `Python 3.12.15`, `/usr/local/bin/python3.12` SHA-256
  `bbe1110dea5ad4c33d3a74cac9ba40e3a8c0831b17d18aba7431fd4931bdfaa7`...
- Contracts and packages remain byte-identical (not in the I-d..I-e diff);
  the recursively stripped OpenAPI digest (all `x-slaif-` keys removed at
  every nesting level, lists recursed, `sort_keys=True` compact separators,
  default ASCII, UTF-8, no trailing newline) recomputed by this round at
  I-e on `contracts/openapi/agent-v1.json` equals
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  exactly. No generated change.
- No new local security exception or pin in this round; no rerun of the
  six-image qualification is claimed. Adopted results name tested I-d;
  nothing failed in d is adopted as PASS.

## 8. GitHub required checks at I-e `f459ad38`

| Check | Run ID | State at I-e |
| --- | --- | --- |
| Analyze (actions) | 117572360883 | SUCCESS |
| Analyze (javascript-typescript) | 117572360894 | SUCCESS |
| Analyze (python) | 117572360895 | SUCCESS |
| CodeQL | 117572419689 | SUCCESS |
| Compose and edge packaging | 117572355228 | SUCCESS |
| Dependency review | 117572355415 | SUCCESS |
| Detect supported languages | 117572343451 | SUCCESS |
| Foundation PostgreSQL 14 | 117572355611 | SUCCESS |
| Foundation PostgreSQL 15 | 117572355411 | SUCCESS |
| Foundation PostgreSQL 16 | 117572355450 | SUCCESS |
| Foundation PostgreSQL 17 | 117572355395 | SUCCESS |
| Foundation PostgreSQL 18 | 117572355442 | SUCCESS |
| Markdown | 117572355352 | SUCCESS |
| Mermaid | 117572355482 | SUCCESS |
| Node contracts | 117572355435 | SUCCESS |
| Python 3.12 quality and package | 117572355490 | SUCCESS |
| Python 3.13 quality and package | 117572355477 | SUCCESS |
| Python 3.14 quality and package | 117572355467 | SUCCESS |
| Repository policy | 117572355478 | SUCCESS |
| Supply-chain evidence | 117572355507 | SUCCESS |

All twenty required names terminal SUCCESS at
`CI_ALL_TERMINAL 2026-10-18T03:24:31Z`; every check run's `head_sha` is
`f459ad38f7379adb7f48d5fb55f1d06b1c81b2a8` (per-check IDs in the table;
per-check detail retained at
`/tmp/oap-083-3-e/ci-attempts-e.txt` and `ci-raw-d.json`).

First-attempt evidence at workflow level (authoritative for reruns; the
check-run API exposes no attempt field): workflow run
`39092599457` (CI) — completed/success, `run_attempt=1`, head `f459ad38`,
started 2026-10-18T03:09:04Z, updated 03:24:10Z; workflow run
`39092599407` (CodeQL) — completed/success, `run_attempt=1`, head
`f459ad38`, started 03:09:04Z, updated 03:10:34Z. Independently reverified
by this round via the actions API (retained
`/tmp/oap-083-3-e/ci-workflow-runs-e.json`) and matching strategy's
independent source `I-e-checks-independent.json` (saved 03:26:52Z), whose
PR status-check rollup references only these two runs' jobs. No
deterministic rerun performed; the single documented CI-flake allowance
remains unused (all prior a/b/c/d I/S CI and CodeQL runs verified at
run_attempt=1).

## 9. PR description update (e4.7 metadata correction)

PATCHed via REST (first patch 2026-10-18T04:16:51Z; corrected wording
patch 04:22:36Z, remote `updated_at`), final body retained at
`/tmp/oap-083-3-e/pr-body-final.md`. The d wording that
conflated the surface distinctions is corrected:

- Public content: public site HTML is stated as rendered dynamically with
  the existing `private`/`no-store` cache headers and explicitly not
  immutable; only content-addressed public media
  (`/media/public/sha256/...`) is stated as digest-verified and immutable.
- Private surfaces: human workspace and review access is stated as using
  human authentication and RBAC (human-only review, reviewer-atomic
  promotion) — not capability-scoped; the Agent API is stated as using
  workspace-bound agent capabilities (one site, one workspace, fixed
  scopes/TTL/quotas, site-confined lookups).
- The e round's complete local suite result and the two-assertion
  correction are described truthfully; the d failure history is attributed
  to the immutable d report. No new issue, comment or PR; no
  predicted-green language; no broad MVP-completion claim (the existing
  bounded-increment limitation is retained).

## 10. Budget (recomputed against the verified d baseline)

This round (e): 0 production/config, 0 migrations, 1 tests/evidence
(`services/backend/tests/integration/test_human_editor_production_http.py`),
0 generated, 0 docs, 3 transcript paths (order-e, report-e, active overlap).
Only the two local assertion hunks; 17 changed lines total (+8/−9), under the
predeclared 20.

Cumulative base `214909f` to S-e: 52 unique files = 12 production/config +
1 existing migration, 19 tests/evidence, 0 generated, 9 docs, 11 transcript —
exactly the order's expected values; zero variance. Itemization at S-e (51 at
I-e; the report adds the 52nd transcript path):

- 12 production/config: `infra/apache/Dockerfile`,
  `services/backend/Dockerfile`,
  `services/backend/src/slaif_agent_site/bootstrap/service.py`,
  `services/backend/src/slaif_agent_site/db/privileges.py`,
  `services/backend/src/slaif_agent_site/review_worker/config.py`,
  `services/backend/src/slaif_agent_site/review_worker/outbox_consumer.py`,
  `services/backend/src/slaif_agent_site/review_worker/worker.py`,
  `services/browser-worker/Dockerfile`, `supply-chain/policy.json`,
  `tools/compose/smoke.sh`, `tools/supply_chain/evidence.py`,
  `tools/supply_chain/policy.py`.
- 1 migration:
  `services/backend/src/slaif_agent_site/db/alembic/versions/074_001_cache_outbox_consumer.py`.
- 19 tests/evidence: 10 integration tests (the d nine plus
  `test_human_editor_production_http.py`, changed first in this PR by e),
  3 unit tests, 2 e2e specs, `tests/packaging/test_oci_contract.py`,
  2 `tests/supply_chain` tests,
  `supply-chain/browser-worker-critical-matrix.json`.
- 9 docs: `README.md`, 5 `docs/*.md`, `oap/INCREMENTS.md`,
  `oap/MVP-CONTRACT-AUDIT.md`, `oap/MVP-PROGRESS.md`.
- 11 transcript: `oap/active`, 5 orders (a-e), 5 reports (a-e).

Production review trigger remains NOT_FIRED at 13 (12 production/config +
1 migration); CLOSURE_ONLY remains in force.

## 11. Scope, security and completion confirmations

- Diff from starting head changes only the single named test file plus
  order/active/report transcript bytes; untracked `.codex/`,
  `CODEX-SESSIONS.md`, `codex.sh` preserved and never staged.
- No application code, vulnerability/license exception, gate weakening,
  dependency, lockfile, workflow, role, migration or topology change;
  foundation remains registry `agent-cow-postgresql==0.2.0` with frozen
  hashes.
- No new PR, no merge, no auto-merge, no PR closure; no edits to earlier
  orders or reports (all earlier reports unchanged; only current PR metadata
  corrected).
- No secrets, production systems or protected resources touched; all local
  setup (Node 24 toolchain PATH, uv 0.12.5, disposable PostgreSQL container,
  temporary Mermaid sysctl relaxation restored) is routine executor
  authority.
- No repository mutation follows S-e.

## Limitations and open items

- Checks newly started by the report-only S-e push are honestly pending in
  this report; strategy verifies all twenty independently at S-e.
- The d round's historical attribution of the stale foundation fixture
  residue to a specific earlier round (b) is inferential timing analysis,
  not a retained session-identifier match; the established cause is an
  earlier interrupted fixture session whose teardown never ran (d report
  section 4), and this report does not upgrade that inference.
- Four Medium browser-worker CVE-2026-19445 distribution matches remain
  disclosed (Critical-only policy; no exception; no browser OS repair
  authorized).
- The C-1 final 20/20 acceptance obligation at the final report-only head,
  and strategy's independent all-round review, remain with strategy; this
  round claims no acceptance and no whole-product readiness.

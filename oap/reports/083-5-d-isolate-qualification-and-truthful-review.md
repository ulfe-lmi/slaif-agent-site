# OAP 083-5-d execution report — isolate qualification and close truthful review gates

## 0. Status

| Field | Value |
| --- | --- |
| Round | 083-5-d (numeric objective 083, increment 5, round letter d) — CLOSURE_ONLY |
| Order | `oap/orders/083-5-d-isolate-qualification-and-truthful-review.md` (307 lines, committed unchanged with the first d implementation commit) |
| Order SHA-256 | `bbead3616e462283ae7a00ff9f4adb3a359fe0795271ba771ff8bf2f045887a4` |
| `oap/active` bytes | `083-5-d\n` (8 bytes: `3038332d352d640a`) |
| PR mode | AMEND_EXISTING_PR (PR #107, no new PR, never merged) |
| Status | PARTIAL — D1/D2 executed and CI-verified at I `43cd5454`; local G1 ALL31 (31/31 native 0) and G4 OpenAPI (native 0) QUALIFIED at clean I; G2 FULL did not complete (first-module 503 pattern, cause UNKNOWN, stopped per strategic close); G3 fresh WHOLE and G5 fresh six-image BLOCKED by the measured upstream libcurl 3.23 index drift (section 9); current I CI terminal 18/20 required names SUCCESS with Compose + Supply-chain FAILED on that single measured root cause. No acceptance; the bounded libcurl repin is explicitly outside d and goes to the next letter with full original acceptance unchanged. |
| c report | `oap/reports/083-5-c-close-security-and-final-gates.md` at `11c8d7783c9b8f7b2018bf15007e735e7fedd233` (file SHA-256 `a91762e06142452c4438828fe38ec90032d5879eff1a242b2281d4963160faed`) — IMMUTABLE, never edited; its seven evidence-map corrections are applied in section 4 of this report only. |
| Report publication commit | SELF (this report; sole path; first parent exactly I `43cd5454a440bd2bc341d0ddf204868cdf2fe22e`) |

## 1. Identity, control handshake, protocol incident

- ID: 083-5-d, numeric objective 083, increment 5, CLOSURE_ONLY, AMEND_EXISTING_PR.

- Order (read FULL, immutable): oap/orders/083-5-d-isolate-qualification-and-truthful-review.md, 307L,
  SHA256 bbead3616e462283ae7a00ff9f4adb3a359fe0795271ba771ff8bf2f045887a4.

- Active: oap/active = "083-5-d" + LF, 8 bytes, hex 3038332d352d640a.

- This round's NEW control FIFO OK consumed 2026-10-25T15:18:15Z (payload 4f4b, 2 bytes, no LF).
  c handshake is complete and was never replayed.

- PROTOCOL INCIDENT (recorded per root correction): at 15:18:22Z the primary wrote an early
  "OK" (2 bytes) to the strategic response FIFO immediately after consuming the control OK,
  i.e. BEFORE the d report-only S existed. That write was an INVALID EARLY ACK. Root consumed
  it 15:18:28Z, preserved the receipt, and confirmed no d report and unchanged c S at that
  time. The primary has NOT written the response FIFO again since; the single valid response
  OK is sent exactly once after the final d report-only S is pushed and remotely verified.

- Strategic handoff review read FULL:
  workorders/083-5c-handoff-review-and-083-5d-prospective-decision-2026-10-25.md (90L).
  Its seven c-report corrections are applied in this report (section 4); immutable c report
  (SHA a91762e06142452c4438828fe38ec90032d5879eff1a242b2281d4963160faed, S 11c8d778) was
  never edited.

## 2. PR and source identities

- PR #107 (OPEN), branch oap/083-5-a-faithful-frozen-review, base main
  4bf74fdc8e74323045a7f8830cf393493e75fe0d (independently verified unchanged).

- Starting remote S (c report-only): 11c8d7783c9b8f7b2018bf15007e735e7fedd233.

- Pushed d implementation commits (first-parent chain from starting S):
  - b00b709 — D1: ci.yml split + tests/repository/test_foundation_ci.py + d order + active (4 paths)
  - 1705c3f — D2: truthful retained-review/drift copy in 4 named files (4 paths)
  - 1384944 — format repair of the new repository test after CI E501 (1 path)
  - c4e6606 — integrate audited CI-proof additions: matrix/skip/needs predicates, unset-env,
    timed_out, seven mutation rejections (1 path)
  - 43cd545 — replace tautological guard-mutation raise with the real fail-closed
    qualification predicate (1 path)

- LITERAL IMPLEMENTATION I: 43cd5454a440bd2bc341d0ddf204868cdf2fe22e
  (tree recorded in the final-gate manifest; no source change after the gates below).

- Report publication commit: SELF (report-only; first parent exactly I).

## 3. Status

PARTIAL.

Qualified at literal I 43cd5454: D1 (source + repository proof + live CI execution of all
10 internal children and the 5 required aggregator names), D2 (copy + statics), G1 ALL31
(31/31, actual child exits, immutable worktree, section 7), G4 OpenAPI (native 0, section
7). NOT qualified: G2 FULL unfiltered integration did not complete (systematic first-module
503 pattern, cause UNKNOWN, stopped per strategic close — section 7), and the coherent RC7
sub-proof (proven inside the FULL suite) therefore also remains NOT RUN fresh at I. BLOCKED
by the measured upstream Alpine 3.23 libcurl index drift (section 9): G3 fresh WHOLE and
G5 fresh local six-image, and the two current CI required names Compose + Supply-chain. All
original a/b/c criteria remain FULL and carry forward; this report is not acceptance and no
merge occurs.

## 4. c-report corrections (required in d; c never edited)

Per the strategic handoff review, the c report contains these transcription/wording defects,
each corrected here:

1. c section 7.1 command-31 row transcribed an escaped triple-star wildcard. The actual
   required/executed literal is `npx --yes markdownlint-cli2@0.23.2` with the single-quoted
   argument `**/*.md`. Root independently matched the ALL31 manifest argv at I5. Report
   transcription error, not a changed gate.

2. I1 e7dcbd81 GitHub author/committer timestamp is 12:55:19Z, not c section 3's 13:01Z; it
   predates the actual I1 all31 start 12:57:45. I5 actual 14:19:44Z; c S actual 15:09:57Z.
   Distinct publication/test/commit timestamps are preserved.

3. c sections 6a/11 PG-version wording over-generalized. Actual: bS 14/15/18 cancelled;
   J2 ONLY 14/15 cancelled; I2 ONLY 14/16 cancelled; I5 14/15/18 cancelled. I2 PG14 only
   118 selected completed with the final 12-case summary absent; I2 PG16 printed 130 but the
   job was CANCELLED; I5 PG14 only 118; I5 PG15/18 printed 130 yet jobs CANCELLED. Successful
   sibling jobs are not erased.

4. The literal 22-file artifact baseline had run successfully on earlier a/main-era source;
   the newly added b parity fixture makes it unreachable on the later fixture map. The
   "never exercised" wording is scoped to the new b/c fixture map and the failed attempts
   discussed, not to all of PR 083/5.

5. The concurrent foreign-project process is PRIMARY-observed metadata, not independently
   verified cause. Root observed the first .E.E by 14:48:01Z; the reported other-process
   start 14:48:04Z cannot alone explain earlier errors. Shared-cluster role/dependency
   contamination remains a hypothesis, not attribution to another project. That other repo
   was not inspected or operated.

6. The c report's shared-cluster cleanup instruction is superseded prospectively: d uses a
   fresh dedicated CLUSTER (container slaif-integration-pg-18-0835d, 127.0.0.1:55443,
   postgres@sha256:697c180d..., PostgreSQL 18.6); no other project's DBs/roles/connections
   were deleted, terminated or operated. Existing no-connection DBs remain not proved inert.

7. Current I5 CI artifact 12601849629 was independently verified after reporting: 8945755B,
   ZIP sha256 686a842306d152bf1ca61823f2feb80819df58a97a48a0231e887d81c354cbb6, 53
   checksums, all 6 raw scans Critical 0, 19 High full tuples inherited from the prior FAILED
   ea586 census, no exceptions; actual merge 8f3071ad50fe7f06fd3e873a85661f7ca7dc78b0
   parents main 4bf74fdc + I5 d88ceaa2, tree exactly I5. Scoped CI evidence only — NOT new
   literal I or fresh local six-image qualification. Local J2 identities stay separate.

## 5. D1 — isolated CI groups with fail-closed required checks

Source: .github/workflows/ci.yml, +100/-2 = 102 GROSS (within the recorded 120..260 estimate;
favorable variance).

- The old single `foundation-postgresql` job was replaced by two explicit child job IDs
  (`foundation-pg-group-a`, `foundation-pg-group-b`) and a new aggregator job that keeps the
  exact required name `Foundation PostgreSQL ${{ matrix.postgresql }}` (exactly once; derives
  the five required names for PG 14..18).

- Each child: PG14..18 matrix, fail-fast:false, its own disposable PostgreSQL 18.6-alpine3.23
  service on loopback 5432, same setup/credentials/pinned actions (checkout@3d3c42e5,
  setup-python@5fda3b95, setup-uv@20cfd1bf), timeout-minutes:15, no job/step `if:`, no
  include/exclude, no continue-on-error/retries anywhere.

- Group A runs the EXACT generic foundation command then the EXACT 19-file
  bootstrap/privilege command (4+81=85 per version). Group B runs the EXACT component
  (`-k component`) then EXACT theme then EXACT page-style commands (24+9+12=45 per version).
  All five command argvs are byte-identical to the pre-split job (parsed comparison).

- Aggregator: `needs: [foundation-pg-group-a, foundation-pg-group-b]` (explicit job IDs,
  GitHub needs address JOB IDs, not matrix children), JOB-level `if: always()` plus step-level
  `if: ${{ always() }}`, fixed needs results passed via environment
  (GROUP_A_RESULT/GROUP_B_RESULT = `${{ needs.<id>.result }}`), and a fail-closed shell script
  that exits 0 ONLY when both are exactly `success`; missing/empty/unknown/failure/cancelled/
  skipped/timed_out/other refuse. The 5-minute aggregator timeout is a NEW tighter budget
  (no existing timeout raised).

- Deliberate conservative cross-PG barrier: any failed child blocks ALL FIVE required
  Foundation names (documented in the file).

- Repository proof: tests/repository/test_foundation_ci.py (398L at I, stdlib-only, no parser
  dependency): 15 tests — exact required names + complete PG matrices; child isolation
  (services/env/pins/timeouts); exact five-command split 85+45 via folded-scalar extraction;
  aggregator needs/ids/job-level always/env; no-scheduling-weakening invariants (timeout
  multiset ["10","10","10","15","15","15","15","15","45","5","60"], no continue-on-error or
  retries); the ACTUAL extracted aggregate script executed with (success,success) as the sole
  positive and 15 negative vectors (failure/cancelled/skipped/empty/unknown/neutral/stuck/
  timed_out in both slots); unset-environment refusals (A-only/B-only/none present, PATH-only
  env); and seven in-memory workflow mutations (omitted group-A command, omitted group-B theme
  command, omitted matrix leg 18, partial matrix via inserted exclude, omitted needs id,
  child job-level `if: ${{ success() }}` inserted, weakened result guard
  `!= "success"` -> `= "cancelled"`) each with a baseline positive control, a count==1
  precondition, and a REQUIRED predicate rejection. For the weakened guard the test first
  proves the mutation is behaviorally real (mutated script exits 0 on (failure,success)) and
  then requires the actual fail-closed qualification predicate `_assert_fail_closed` to refuse
  the mutated workflow (root correction: the earlier tautological `assertRaises` on a
  self-contradicting assert was removed at 43cd545).

- Secondary (pane21) delivered a scratch-only proposal (405L, +166/-0 over the 239L baseline,
  byte-preservation mechanically verified by the primary). The primary reviewed every
  additive line, verified all mutation needles against the actual workflow, applied the
  additions with ruff-normalized blank lines, and made the one root-required predicate fix.
  The v1 draft failure history in the secondary lane is preserved, not credited.

- Harness: the actual extracted script executed over cross-value combos; (success,success) is
  the sole exit 0; all other values exit 1 (15 negatives + 3 unset-env subtests + 7 mutations
  in the committed test; secondary scratch additionally exercised 8x8=64 combos).

CI evidence per head (actual, distinct):

- 1705c3f (attempt I1): Python 3.12/13/14 FAILED on the new test's E501 (line 191, 103>88)
  and ruff-format diff — original 3.12 job 121214014289 preserved
  (/tmp/oap-083-5-d/I1-1705c3f9-python312-job121214014289-original.log). Fixed at 1384944.

- c4e6606 (attempt I3): Python 3.12/3.13/3.14 SUCCESS; CodeQL SUCCESS; Compose job
  121217179034 (run 40209276472) FAILED at the postgres apk stage before the browser phase —
  root-preserved original
  /tmp/oap-083-5-d/I3-c4e66060-compose-job121217179034-original.log (194918B). Cause:
  upstream libcurl index drift, section 9.

- 43cd545 (attempt I, FINAL): terminal — CodeQL 4/4 SUCCESS; CI 22 SUCCESS / 2 FAILURE
  (Compose + Supply-chain, both the measured libcurl apk stage; root-preserved originals
  I4-43cd5454-* in tmp0835d plus the primary-fetched supply-chain original 222125B).
  Root live count 16:31Z: 28/30 checks SUCCESS. Full job-level table: section 10.

## 6. D2 — truthful retained-review and drift guidance

Named files (all four already authorized: README.md + route.tsx via the inherited c map;
workspace-review.tsx + accept-lifecycle.spec.ts via the d prospective names):

1. docs/user-manual/README.md, Review Page section (new in this PR; corrected):
   - "drift blocks acceptance until a re-freeze" -> "Canonical drift blocks acceptance; the
     supported remedy is a fresh or reapplied workspace, with discard where appropriate.
     Re-review and a multiple-snapshot lifecycle are planned, not yet available."
   - "After acceptance or discard the review page no longer resolves" -> "After acceptance or
     discard the immutable snapshot history is retained: the frozen review and its private
     media remain readable under the existing authorization and retention policy and are never
     automatically published."
   - "Media ... and is never published" -> "reviewing itself does not publish" (an authorized
     later acceptance is not misrepresented as impossible).
   - No indefinite-retention claim; no order/implementation IDs.

2. apps/web/app/review/[workspaceId]/[[...sitePath]]/route.tsx public banner drift branch:
   - "acceptance is blocked until re-freeze (enforced at 083/1); the frozen review remains
     visible." -> "acceptance is blocked. The frozen review remains visible." (order ID
     removed; pre-existing main-era copy corrected in place).

3. apps/web/src/admin/workspace-review.tsx admin DriftBanner:
   - "... acceptance is blocked until re-freeze (enforced server-side); the frozen review
     remains visible." -> "... acceptance is blocked. The frozen review remains visible."
     (contiguous "acceptance is blocked" preserved for the E2E contract).

4. tests/e2e/accept-lifecycle.spec.ts drift test:
   - expected text updated from "acceptance is blocked until re-freeze" to the entire new
     stable clause "acceptance is blocked. The frozen review remains visible." (exact:false
     substring, matching the dynamic revision prefix); comment corrected from "re-review
     message" to "blocked-acceptance warning". psql canonical_revision+1 drift injection,
     absent accept button, visible warning, `stopObserving()).toEqual([])` and all other
     assertions preserved unchanged. No assertion removed or broadened.
   - Grep-verified: these four files are the only consumers of the drift guidance copy.
     apps/web/src/admin/accept-action.tsx line 215 ("Re-freeze and accept again.") is a
     pre-existing main-era in-progress-acceptance-failure message, NOT the drift banner, and
     is outside the named D2 scope; recorded as reviewed-not-changed.

Statics on changed files (actual child exits, repo config):

- prettier --check (prettier.config.mjs, printWidth 88): route.tsx, workspace-review.tsx,
  accept-lifecycle.spec.ts all clean (the README is not in the pnpm format:check glob; the
  initial 3-file warning was traced to my edits and fixed).

- tsc (pnpm typecheck, workspace): native 0 (TSC_CHILD_EXIT=0).

- eslint on the three TS/TSX files: native 0.

- markdownlint-cli2@0.23.2 --no-globs --config .markdownlint-cli2.jsonc on README.md:
  "Linting: 1 file", 0 issues, actual child 0.

- Runtime: within the (invalidated, source-mixed) WHOLE attempt the compose-e2e phase
  completed all 19 projects OK, including accept-lifecycle (the new drift assertion against
  the new banner) — scoped evidence from an interrupted mixed-state attempt, recorded as such,
  not a final gate.

## 7. Local final gates at literal I 43cd5454 (clean worktree
/home/janezp/codex-work/slaif-agent-site-i-d-final, derived from git metadata; worktree held
immutable at I for the duration of each live attempt after the two mixed attempts below)

### G1 ALL31 (standing 31 commands, IN ORDER)

Attempt history (preserved, distinct, honest):

1. final-I-all31 at 1705c3f (started 15:47:07Z): CMD 01/02/05/06/07/08 EXIT 0; CMD 03/04
   EXIT 1 (the E501 + ruff-format defect in the new test, same as CI); runner stopped by the
   primary at ~15:48:50Z (wrapper ALL31_WRAPPER_CHILD_EXIT=143); CMD 09 had printed
   "editor-api: CHECK_OK" (log mtime 15:48:18Z) but its manifest EXIT line was never written
   (runner terminated first) and its orphaned python child remained alive until after
   15:57:55Z (root /proc observation), then terminated on its own at an unmeasured time —
   a post-CHECK_OK shutdown hang of unproven cause. The worktree moved (1384944 at ~15:50,
   c4e6606 at ~16:03) while that orphan and later pipelines were live: this attempt is
   source-mixed/failed, never a final all31 PASS.

2. final-I-c4e-all31 (started 15:57:05Z): CMD 01..29 EXIT 0 (including ruff/format at the
   then-current 1384944 test file), stopped by the primary at ~16:14:10Z while CMD 25-29
   were finishing (wrapper 143). The worktree checkout to c4e6606 at ~16:03 (tests file
   only) occurred while this attempt was live: source-mixed, not a final record.
   (Primary execution error recorded: fast-forwarding the worktree while live commands ran.)

3. FINAL final-I-43c-all31 (started 16:14:14Z at I 43cd5454): ALL 31 COMMANDS EXIT 0,
   ALL31_OVERALL_EXIT=0, ALL31_WRAPPER_CHILD_EXIT=0,
   SOURCE_HEAD=43cd5454a440bd2bc341d0ddf204868cdf2fe22e,
   TREE=a05d30ffa7fcfab2fb5f7581a644be6f6193ccf0, WORKTREE_DIRTY=0, finished 16:19:26Z.
   Unique per-command logs in /tmp/oap-083-5-d/final-I-43c-all31/. QUALIFIED at I.

### G2 FULL unfiltered backend integration on the dedicated cluster

Dedicated cluster (section 8). Exact command:
`PGHOST=127.0.0.1 PGPORT=55443 PGUSER=postgres PGPASSWORD=qualification-admin
PGDATABASE=postgres uv run --frozen pytest services/backend/tests/integration`

- Attempt 1 (16:14:16Z): exited 1 in <8s with ZERO output (log = single
  FULL_CHILD_EXIT=1 line). Cause UNKNOWN; suspected start-race with the concurrent ALL31
  `uv sync` on the shared worktree .venv — NOT proven. Preserved.

- Attempt 2 (started ~16:16:30Z): pytest session started cleanly, 347 items collected on the
  dedicated cluster, then systematic early failures: test_agent_browser_http.py "FF",
  test_agent_global_region.py "FFFFFFF", test_agent_mutations.py "FFFF.E..." (progress at
  stop). A targeted single-test diagnosis (test_agent_browser_http.py -x, same cluster)
  completed with the exact traceback: POST /api/agent/v1/preview-runs -> 503 (expected 202)
  in test_public_agent_browser_routes_are_durable_truthful_and_confined. Stopped by the
  primary per strategic close decision (TERM; wrapper FULL_CHILD_EXIT=143; log mtime
  16:20:51Z). Final collected/passed/failed/error/skipped summary: NOT PRODUCED (no
  inference from progress glyphs).

- Findings: (a) the SAME first module (test_agent_browser_http) failed at the same early
  position in c's I5 G2 (.E at 14:48Z); (b) the failure reproduces on a fresh dedicated
  cluster, so shared-cluster role/dependency contamination is NOT the (sole) cause — the
  contamination hypothesis from c is demoted further; (c) the actual 503 cause remains
  UNKNOWN (readiness/service 503 path; no attribution, no flake label, no test weakening).
  This is an open local-runtime finding carried into the next letter.

### G3 WHOLE (sh tools/compose/smoke.sh slaif0835)

- The only d attempt (final-I-c4e-whole, started 15:57:05Z) ran in the worktree that moved
  1384944 -> c4e6606 at ~16:03 mid-run: source-mixed, not final. Its compose-e2e phase
  completed ALL 19 projects OK (including accept-lifecycle with the new D2 drift assertion
  against the new banner text, freeze-review-snapshot, review-surface, media-publication);
  the primary's TERM (~16:14) deferred to the next foreground step, ran the script's cleanup
  trap (compose down), and the following public-agent-acceptance phase then failed with
  "public-edge-unavailable" against the already-torn-down stack — an artifact of the
  interruption, not a product defect (WHOLE_CHILD_EXIT=1 recorded).

- A FRESH WHOLE at I is BLOCKED: compose builds the postgres image from source and hits the
  measured libcurl index drift (section 9). Not run to avoid a predetermined failure with
  no new information beyond the two CI originals.

### G4 generated Agent OpenAPI zero-diff

- `uv run --frozen python -m tools.contracts.generate_agent_openapi --check` at I
  43cd5454 (worktree immutable at I; started ~16:16:41Z, log mtime 2026-10-25T16:16:43Z):
  "component-catalog: OK" + "agent-openapi: OK contracts/openapi/agent-v1.json",
  actual child 0 (log /tmp/oap-083-5-d/final-I-43c-g4/openapi-check.log, exact command in
  log header, unique filename, no overwrite). QUALIFIED at I.
  (c-era lesson applied: module form + node PATH from the first attempt.)

### G5 fresh local ALL6 six-image

- NOT RUN at I: deterministic same-stage failure as CI Compose/Supply-chain (section 9).
  No image built, no scan claimed, no candidate-10 or history entry added.

### RC7 coherent retained-v2-first / separate v1-only restore

- NOT RUN fresh at I: it is proven inside the FULL integration suite (G2), which did not
  complete locally. c's coherent RC7 sub-proof at I5 history remains valid history only.

## 8. Dedicated qualification cluster (fresh, disposable, owned)

- Container slaif-integration-pg-18-0835d
  (451c65f8b0eec3b9e0cc50bb40adfe3a0f556658a8c178277eab292764f82b9e),
  Docker Created 2026-10-25T15:45:53.37144506Z (docker inspect, actual).

- Image sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f
  (= local postgres:18.6-alpine3.23, repo digest postgres@sha256:697c180d...; launched by
  image ID, no pull; image created 2026-08-13T19:17:31Z).

- Binding 127.0.0.1:55443 -> 5432/tcp (loopback only); anonymous local volume
  44f15ff121e7a61328ed10f4635c417069af4f527cd48d56a6ae3672cfcc22b0 ->
  /var/lib/postgresql; restart policy no.

- Identity verified: psql host=127.0.0.1 port=55443 -> "PostgreSQL 18.6 on
  x86_64-pc-linux-musl (Alpine 15.2.0)", inet_server_port()=5432, current_user=postgres;
  wrong-password rejection measured (scram enforced). Credential is the documented fixture
  default constant (conftest PGUSER/PGPASSWORD), not dumped.

- Shared cluster slaif-integration-pg-0833b (127.0.0.1:5432) and all other projects'
  containers/DBs/roles untouched. The two leftover no-connection DBs from c remain not
  proved inert (left in place). Cluster left running for the next letter.

- Provenance receipt (corrected for the initially guessed timestamp):
  /tmp/oap-083-5-d/dedicated-cluster-provenance.json.

## 9. BLOCKER: persistent upstream Alpine 3.23 libcurl index drift

Measured, not inferred. Full receipt: /tmp/oap-083-5-d/libcurl-v323-index-drift-evidence.json.

- CI Compose job 121217179034 (run 40209276472, head c4e66060) failed 2026-10-25T15:59:01Z at
  `[postgres 2/2] RUN apk add ... 'libcurl=8.22.0-r0' ...`:
  "ERROR: unable to select packages: libcurl-8.20.0-r0: breaks: world[libcurl=8.22.0-r0];
  satisfies: .postgresql-rundeps-20260813.191730[so:libcurl.so.4]".

- Source unchanged: infra/postgres/Dockerfile (pin line 23, verification test line 27) is
  byte-identical between I5 d88ceaa2 (whose CI Compose SUCCEEDED ~14:30Z building this exact
  pin) and c4e66060 (git diff empty). Same holds for 43cd545.

- Current index (dl-cdn.alpinelinux.org/alpine/v3.23/main/x86_64/APKINDEX.tar.gz, fetched
  ~16:05Z and re-fetched ~16:07Z; APKINDEX sha256 a9e37a02e9e650f2029891f4e82c13e753751bbd0cb971c2c305034b28f0f6d8
  identical both times) contains libcurl versions: [8.23.0-r0] ONLY. 8.22.0-r0 and
  8.20.0-r0 are absent. The other three pins remain present: brotli-libs 1.2.1-r0,
  libcrypto3 3.5.9-r0, libssl3 3.5.9-r0.

- libcurl 8.23.0-r0 provides `so:libcurl.so.4=4.8.0`, satisfying the postgres shared-object
  dependency at the same soname (ABI-consistent bounded remedy for the next letter).

- Conclusion: between ~15:00Z (I5 Compose success) and 15:59Z (c4e Compose failure) Alpine
  3.23 replaced libcurl 8.22.0-r0 with 8.23.0-r0 in the main index. A re-run at unchanged
  source cannot pass; this is upstream drift, not a flake, not host variance, not a product
  defect.

- d scope: "d pins MUST stay unchanged" (root instruction on this round); no downgrade,
  removal, registry widening, blanket upgrade, or unchanged re-run was performed.

- All three named reference sites for the bounded next-letter repin (8.22.0-r0 ->
  8.23.0-r0): infra/postgres/Dockerfile:23,27; supply-chain/policy.json:143;
  tests/packaging/test_oci_contract.py:83.

- Consequence for d final gates: fresh WHOLE (compose builds the postgres image) and fresh
  local ALL6 six-image (G5) are BLOCKED at the same postgres stage for every d head.
  G1 ALL31 and G2 FULL (dedicated cluster, no image build) are unaffected and were executed.

## 10. GitHub CI at literal I 43cd5454 (terminal, actual job IDs)

CI run 40210504791 (head 43cd5454): 22 SUCCESS / 2 FAILURE. CodeQL run 40210504746: 4/4
SUCCESS.

Required 20 names (current S must have all SUCCESS; here 18 SUCCESS / 2 FAILED):

| name | job ID | result |
|---|---|---|
| Repository policy | 121220520435 | success |
| Node contracts | 121220520151 | success |
| Python 3.12 quality and package | 121220520492 | success |
| Python 3.13 quality and package | 121220520353 | success |
| Python 3.14 quality and package | 121220520473 | success |
| Foundation PostgreSQL 14 | 121222903682 | success |
| Foundation PostgreSQL 15 | 121222903751 | success |
| Foundation PostgreSQL 16 | 121222903702 | success |
| Foundation PostgreSQL 17 | 121222903692 | success |
| Foundation PostgreSQL 18 | 121222903695 | success |
| Compose and edge packaging | 121220520432 | FAILURE (libcurl drift, section 9) |
| Supply-chain evidence | 121220520485 | FAILURE (same libcurl stage, 16:20:50Z; original log preserved 222125B; diagnostics artifact 12605282959) |
| Markdown | 121220520467 | success |
| Mermaid | 121220520447 | success |
| Dependency review | 121220520425 | success |
| Detect supported languages | 121220519850 | success |
| Analyze (actions) | 121220545533 | success |
| Analyze (javascript-typescript) | 121220545552 | success |
| Analyze (python) | 121220545573 | success |
| CodeQL aggregate | 40210504746 (run) | success |

NEW internal 10 child jobs (all must actually run; here all SUCCESS — the aggregate
passing alone is not credited as execution proof):

- Foundation PG Group A PostgreSQL 14..18: 121220520499/121220520500/121220520474/
  121220520404/121220520371 — success (85 cases each version).

- Foundation PG Group B PostgreSQL 14..18: 121220520522/121220520549/121220520528/
  121220520535/121220520428 — success (45 cases each version).

- All five PG versions succeeded with NO cancellations at this head (previous rounds'
  15m cancellations did not recur at 43cd5454).

- The five required aggregator names depend on BOTH full child matrices with job-level
  always(); the conservative cross-PG barrier behaved as designed.

Prior-head CI facts (distinct, preserved): 1705c3f Python 3.12/13/14 FAILED (new-test E501;
original 3.12 job 121214014289 preserved); c4e6606 Python SUCCESS + CodeQL SUCCESS, Compose
job 121217179034 FAILED (first measured libcurl occurrence, 15:59:01Z).

## 11. Footprint, forecasts, variances

Recorded baseline (d order, independently reverified c I5): production 11063/43 +
tests 21285/34 = 32348 GROSS (production+tests counted once); docs 155/12; transcript
1612/6.
Recorded d forecast: remaining 230..592 -> 32578..32940 under unchanged 33000; root's
updated band with the audited proof additions: 32867..32992.
Measured d additions over starting S (disjoint named paths):

- .github/workflows/ci.yml: +100/-2 = 102 GROSS (estimate 120..260; favorable -18).

- tests/repository/test_foundation_ci.py: 398 L new file (estimate 100..200 in the order;
  root-updated 405..430 after the audited additions; actual 398 — favorable, blank-line
  normalization + merged timed_out vectors).

- apps/web/src/admin/workspace-review.tsx: 4 GROSS; tests/e2e/accept-lifecycle.spec.ts:
  6 GROSS (copy repairs 8..24 / E2E 2..8 estimates: within).

- docs/user-manual/README.md: 11 GROSS (docs, separate from the 33000 cap).

- Final-gate repairs in already named families: 0.
Authoritative current inventory (root independent minimal measurement at 43cd5454,
16:31Z, pre-report): production 11173/45 paths + tests 21687/36 paths = 32860 GROSS
(production+tests counted once), under unchanged 33000 (margin 140); docs 160/12. The
measured d additions (510: 102+398+4+6) land the tree inside the recorded forecast band
32578..32940 (and just below the root-updated 32867..32992 band — favorable variance,
because the actual proof file is 398 lines, not 405..430).
Transcript becomes 10 exact paths at S (a/b/c/d orders+reports + active); docs unchanged
identities (12). Named maxima 46prod/36tests/12docs/10transcript not exceeded; individual
caps (160/80/180/16/300) untouched. The primary's raw whole-tree numstat recomputation
(prod 12466/51 + tests 22210/32 = 34676 at I under a naive line method) uses a different
counting method than the root minimal inventory and is reported only as a raw
measurement, not reconciled against or used to override the authoritative 32860.

## 12. Strongest reason not to merge

The two failed required checks (Compose, Supply-chain) at current S 43cd5454 have a measured
single root cause — upstream Alpine 3.23 replaced the pinned libcurl 8.22.0-r0 with
8.23.0-r0 in the main index — but the bounded repin is explicitly outside d, so the
fresh-image gates (Compose/Supply-chain CI, fresh WHOLE, fresh local ALL6, coherent RC7)
remain unqualified at this head, and the local FULL integration (G2) did not complete: the
same first-module 503 pattern that blocked c's G2 reproduces on a clean dedicated cluster,
with cause still UNKNOWN. Merging now would ship an image pipeline that cannot build from
its own committed source against the current public index, with the local full-integration
gate unproven. Root alone accepts/merges after the bounded next letter repins libcurl,
reruns the fresh gates at a new clean I, and independently reviews.

## 13. Confirmations

- AMEND_EXISTING_PR on PR #107 (same branch); no new PR, no semantic increment chosen, no
  merge/auto-merge/close by the primary.

- No pin/dependency/guard/workflow/timeout/policy change beyond the D1-authorized split and
  D2 copy; no product behavior change; no security/license/egress/sandbox/credential/role/
  grant/topology/telemetry change; no foundation/privilege change; no agent authority.

- No secrets in this report or in committed artifacts; fixture credential values are the
  documented test constants; no raw trace/credential file committed; browser artifacts
  private; no capability in any URL/storage/screenshot/log.

- Skips/not-runs recorded explicitly (G3 fresh, G5, RC7 fresh, G2 final summary) — never
  claimed as pass. No unchanged CI re-run of a failed head; no flake/benign labels; no
  inferred pass; no aggregation of partial runs as full.

- Human files .codex/, CODEX-SESSIONS.md, codex.sh untouched and uncommitted.

- Report lint: markdownlint-cli2@0.23.2 with the exact repo config, --no-globs, single
  temporary file, "Linting: 1 file", zero issues, actual child 0, before atomic publish.

- Report publication commit: SELF.

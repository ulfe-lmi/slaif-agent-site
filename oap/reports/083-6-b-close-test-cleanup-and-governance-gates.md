# OAP 083-6-b execution report — close test cleanup and governance gates (COMPLETE)

## 0. Status

| Field | Value |
| --- | --- |
| Round | 083-6-b (numeric objective 083, increment 6, round letter b) — FROZEN_REVIEW_CONTROL_RELIABILITY |
| Order | `oap/orders/083-6-b-close-test-cleanup-and-governance-gates.md` (325 lines, 19930B, committed unchanged with the R1 commit) |
| Order SHA-256 | `6873388eacb0086c5e5e596c34531a0e15f6f10b408f1ed76cedc3e582502744` |
| `oap/active` bytes | `083-6-b` + LF (8 bytes, hex `3038332d362d620a`) |
| PR mode | AMENDED_EXISTING_PR (PR #110; branch `oap/083-6-a-stabilize-frozen-review-controls`; base verified remote main `f35ec75319afd966d02ee2b7b8cb1db1eb4cd144`; starting report-only remote head `40750a3ef1238eade121aa38cad98f48c53f6310`) |
| Status | **COMPLETE** at literal final implementation I `a4206939bc971012be327564dd8d3bcb3db892b0` (tree `cf38630a2ec66c5295280fe56efeaabe7c481d1c`): every executable b criterion actually executed and qualified at I — B1/B2/B3 committed (sections 3-5), B4 oracles preserved (section 6), B5 docs (section 7), clean-isolated-worktree complete ALL31 31/31 native 0 (section 8.1), TWO independent full focused six-pairing parity invocations native 0 142708ms/139084ms (section 8.2), fresh literal WHOLE 0835: WHOLE1 FAILED preserved (measured wrapper umask-077 leak, section 8.3) then root-authorized finite child-umask-022 packaging check 49/49 native 0 and ONE corrected fresh literal WHOLE2 native 0 with all 19 projects / 40 browser records / 49 packaging tests / `compose-smoke: OK` (section 8.3). Cumulative test gross 672/700, docs gross 76/100, production 0. Original 600s CI stall and 5-wrapper Puck over-add: cause UNKNOWN (the B3 governance Puck contract passed in both focused pre-reqs and in WHOLE1/WHOLE2's 19-project matrices). Bounded post-WHOLE2 security evidence: actual selected backend image verified to contain pip 25.0.1's vendored certifi 2024.08.30 (section 14.1); advisory remains OPEN. Report-only-S final-30 CI may honestly be pending at publication; root independently waits. COMPLETE is evidence, not acceptance. |
| Report publication commit | SELF (this report; sole path; first parent exactly I `a4206939bc971012be327564dd8d3bcb3db892b0`) |

## 1. Identity, control handshake

- ID: 083-6-b, numeric objective 083, increment 6, AMEND_EXISTING_PR, same PR #110 and
  increment family as round 083-6-a (PARTIAL handoff at `40750a3e`, root-verified valid
  PARTIAL execution handoff, NOT acceptance).

- Order (read FULL, immutable): 325 lines, 19930B, SHA-256
  `6873388eacb0086c5e5e596c34531a0e15f6f10b408f1ed76cedc3e582502744`,
  `oap/orders/083-6-b-close-test-cleanup-and-governance-gates.md`.

- Active: `oap/active` = `083-6-b` + LF, 8 bytes, hex `3038332d362d620a` (byte-verified at
  activation and at publication).

- The ONE root control OK for this round: root writer PID 441389 (strategic session 21223,
  TERMINAL_0) wrote exactly 2 bytes `4f4b` (no LF) to strategic `control.fifo`
  (inode 4470111) at 2026-10-26T00:29:56.763079Z and closed (receipts
  `/tmp/oap-083-6-b/control-written.json`, `control-native-session.json`). Consumed ONCE by
  the primary reader; no control replay; no `response.fifo` write of any kind occurred during
  the round until this final publication (the a-round response reader 85158 is TERMINAL and
  was never re-polled or replayed).

- Prospective root workorders read FULL during the round (all under
  `/home/janezp/codex-supervision/slaif-agent-site/workorders/`): B2 nonreproduction and B3
  safe-drag outcome decision (2026-10-26), WHOLE1 permissions and bounded WHOLE2 decision
  (2026-10-26T02:22:06Z, governing the second WHOLE). Plus in-flight root steering
  adjudications (B3 review, R5 delta review, security alert notices, carry-comparison note).
  No order/active rewrite, no new activation, no new ID.

## 2. PR and source identities

- PR #110 (OPEN, unique 083/6), URL
  `https://github.com/ulfe-lmi/slaif-agent-site/pull/110`, base `main` at
  `f35ec75319afd966d02ee2b7b8cb1db1eb4cd144`, head branch
  `oap/083-6-a-stabilize-frozen-review-controls`. Title updated during the round to reflect
  the b scope: "083-6: frozen-review control reliability - parity teardown first-error
  preservation + bounded governance drag diagnostics (in flight)" (status line updated at
  final S).

- Final literal implementation I: `a4206939bc971012be327564dd8d3bcb3db892b0`, tree
  `cf38630a2ec66c5295280fe56efeaabe7c481d1c`.

- b-round commits (base = a report S `40750a3e`; a implementation I
  `9d580cb49f1b8e76873a0f5bce50ca82c7a5d8f1`):

  | Commit | Content |
  | --- | --- |
  | `7c47177a` | R1: activate b (order + active, exact bytes) + B1 first-error-preserving outer teardown + B2 bounded passive drag diagnostics (v1) |
  | `9a40821d` | R2: WIP-review fixes — fixed-enum close-failure output, non-Error body fallback, fail-safe drag-diagnostics write |
  | `71ba816b` | R3: atomic wrapper/distinct/missingId tuple from a single in-page read (= B2 suite subject) |
  | `e929ac6f` | R4: B3 single-gesture drag outcome synchronization under the existing 8s budget + 083/6-b docs |
  | `a4206939` | R5: assert legal starting count 1 before the second drag insertion; single-line TESTING heading and exact old-attempt wording (= I) |

- Diff `f35ec753..a4206939` (`git diff --minimal --numstat`): EXACTLY 8 paths —
  `tests/e2e/frozen-review-parity.spec.ts` (468: 442/26), `tests/e2e/governance.spec.ts`
  (204: 190/14), `docs/TESTING.md` (72: 72/0), `oap/MVP-PROGRESS.md` (4: 2/2),
  `oap/orders/083-6-a-restore-frozen-review-controls.md` (298: 298/0),
  `oap/orders/083-6-b-close-test-cleanup-and-governance-gates.md` (325: 325/0),
  `oap/reports/083-6-a-restore-frozen-review-controls.md` (540: 540/0),
  `oap/active` (2: 1/1). TEST GROSS 672 (cap 700); DOCS GROSS 76 (cap 100);
  production/config/dependency/migration/workflow: 0. `tests/e2e/reporter.mjs` never
  touched; no lock/pin/timeout/retry/assertion-weakening change. The fifth transcript
  identity (this b report) is added by the final report-only S (parent I).

## 3. B1 — outer teardown first-error preservation (committed)

The a-round source-backed finding (parity spec `runPhase` outer teardown at I9d
3024..3027 blindly `await`s each `browser.close`; pinned Playwright close suppresses
`TargetClosed` only and rethrows other errors, so a close rejection could replace the
primary body error and skip later closes) is fixed in `tests/e2e/frozen-review-parity.spec.ts`:

- Explicit failure-presence flag: a thrown `undefined` remains a failure (presence, not
  truthiness).
- The first captured body failure (any Error) is preserved as-is; a non-Error thrown value
  is rethrown via a typed fixed fallback (`unclassified body failure`) without storing or
  serializing the raw value.
- ALL pairing/context closes are attempted regardless of earlier failures.
- Close failures are reported ONLY when the body passed, with fixed-enum output
  (`pairing context close failed` / `canonical pairing context close failed` +
  `cleanup-close-failures` annotation, fixed engine names only); close error thrown AFTER
  the finally completes, never replacing the body first failure.
- The equivalent existing `canonicalPhase` cleanup got the same correction: body >
  observer-collector > context-close failure priority with explicit failure presence, close
  always attempted, collector assertion retained whenever the body passed, no arbitrary
  captured value serialized. All canonical zero-POST/render/locale/style assertions intact.

No close failure was observed at any gate in this round; this is the source-backed
error-path repair the order required (not an observed runtime defect). `reporter.mjs`
unchanged. WIP-review fixes (fixed-enum close output, non-Error fallback, fail-safe write)
landed at R2 `9a40821d` per root review of the R1 draft.

## 4. B2 — bounded passive drag diagnostics (committed) and the ONE diagnostic suite

Committed design (all in `tests/e2e/governance.spec.ts`; suite subject revision R3
`71ba816b77af5a9400ec89a736dd39f2d1e5994f`, tree
`01dd9a09cd1c2273cf66199a71cf998f37c5480a`):

- Passive, nonblocking observation around the EXISTING gesture attempts and readiness
  boundaries: the single existing `ready()` evaluation keeps its original position and
  decision (no `expect.poll`/stabilization/outcome wait before the original retry
  decision — that distinction is what separates B2 from the B3 repair).
- ONE atomic in-page tuple `{wrappers, distinct, missingId}` from a single
  `.puck-trusted-component` `evaluateAll` at each boundary (root-identified R2 fix: separate
  `count()` then `evaluateAll` could observe different DOM moments); fixed-enum stage
  labels, numeric counts and relative ms only — no raw IDs, attribute values, DOM content,
  URLs, credentials or bodies.
- Bounded PRIVATE diagnostic JSON under the run-unique `test.info().outputDir`: max 64
  records / 16384 bytes with explicit truncation flags; written on success AND
  failure/finally with a throw-free write and a fail-safe check (body pass + write failure
  still fails; write failure never replaces an earlier drag error); mode 0600.
- No new screenshot/trace/video/browser-profile/artifact-store collection; no public
  artifact; no retry loop, no added poll/wait, no selector/count relaxation.

THE ONE authorized fresh setup+governance diagnostic suite (at R3, fresh owned `slaif0835`
stack, EXACT existing non-authenticatable two-user seed before initialization, private 0600
secret channel, literal `pnpm exec playwright test --project=setup --project=governance`):

- Actual window 2026-10-26T00:55:37.129645..00:57:32.605536Z; immediate native child exit
  `PLAYWRIGHT_NATIVE=0`; setup PASSED (browser-clean), governance visible-workflows PASSED
  (governance-clean), `puck-editor-round-trip-through-human-editor-api` PASSED (the WHOLE
  failure point contract, executed exactly once).
- playwright.log 346B SHA-256 `d871bf92e9424208fe652358b5a4e168d97d1ccb78b6317ce39b21470dea9443`.
- Preserved private diagnostic: 674B, mode 600, SHA-256
  `c42fc13c893c818cd1ffdc4c6f141a17a1c86c74a6fd0b26b9ae33aba3be8f8c`, 6 bounded records,
  no truncation/missing-IDs/snapshot errors: drag-section-first 0->1 ready on attempt 0
  (1260ms), drag-section-second 1->2 ready on attempt 0 (3630ms); wrapper count == distinct
  instance count at every boundary.
- Separate RAW START/END snapshots (written before/after, not recomputed) both at
  HEAD `71ba816b`/tree `01dd9a09`, clean status excluding human3.
- **Result: NONREPRO (category D).** The original 5-wrapper mismatch did NOT reproduce.
  Not flake/infrastructure/duplicate/late-render/ghost. Root-confirmed receipt
  `strategic-B2-71ba816-nonreproduction-independent-review.json`.

- B2 metadata caveats (remain explicit, never rewritten): (a) the START/END git status in
  the B2 harness was filtered with an unanchored human3 regex — root verified no tracked
  file matches that filter plus same HEAD/tree and actual script/source support, but the
  filtered artifact is NOT a full raw snapshot and is not called one; (b) the B2
  image-provenance loop omitted `web` — no retrospective web claim is made; (c) the initial
  B2 launch failed before any script/browser operation (outer redirect directory absent)
  and is preserved separately — only the second launch actually ran the ONE suite.
  ALL FUTURE harnesses (this round's f1/f2/WHOLE/package runs) capture FULL unfiltered
  status.

- The source-level unsafe pattern is independently concrete (root B2 adjudication): up to
  four non-idempotent insert gestures could occur before a later-ready previous insertion
  was observed (each old attempt checked ready after its own gesture; a not-yet-ready
  insertion could still be followed by another). Neither the source nor this passing run
  establishes that as the historical singular cause of the I9d 5-wrapper failure.

## 5. B3 — drag outcome synchronization (committed at I' `e929ac6f`) + R5 second-insertion start count (committed at I `a4206939`)

- Both drag helpers (`dragUntil`, `pointerDragUntil`) now perform the non-idempotent
  insertion gesture exactly ONCE (the single-iteration loop shape `attempt < 1` is
  deliberate and left as root-reviewed; no style refactor), then — only if the passive
  ready observation is not already true — establish the EXACT target state under the
  EXISTING configured 8s `expect` budget, after which an unresolved outcome FAILS with the
  preserved diagnostics. No replay of a non-idempotent insertion, no delete-extras, no
  count relaxation, no narrower selectors, no forced actions, no reload/discard of an
  ambiguous result, no timeout/sleep increase.
- Legal starting counts asserted: 0 before the first insertion (asserted, not assumed, so
  a pre-existing duplicate cannot hide a non-insertion); 1 before the second insertion.
  The R5 correction (root B3 review of `e929ac6f`): the second legal starting count 1 was
  NOT yet asserted immediately before the second gesture (the earlier count-1 was before
  save/API edit/reload); R5 adds `await expect(sectionComponent).toHaveCount(1);` with a
  4-line B3 comment immediately before the second-gesture try block, so a no-op second
  gesture cannot pass via a pre-existing count 2. +5 test lines only.
- Preserved unchanged: original pointer trajectory/activation/drop mechanics and existing
  gesture waits; every count1/count2 assertion, undo/redo, move-up/down and visible order,
  persisted node shape/count/reload/row-version, private-header assertions, real human
  Editor API, 60s test budget, configured 8s expect, retries 0 (Playwright config
  unchanged — "retry configuration" means that unchanged `retries: 0`, not the old replay
  helper).
- B3 is an intentional synchronization REPAIR (root-adjudicated: moving the existing
  exact-state expectation to the point before any replay possibility), distinct from the
  passive B2 instrumentation; the diagnostic comments say exactly that.
- One-pass (single-iteration) loop shape: noted as odd by root and intentionally NOT
  refactored (no style-only changes).

## 6. B4 — original frozen-review oracles (preserved, unchanged)

All original a-round oracles remain intact in `tests/e2e/frozen-review-parity.spec.ts` and
were actually exercised at I: full single-test six-pairing workflow (native A/B/C
main-navigation POST 200 + currentURL + genuinely fresh MAIN document via the sentinel),
exact content/order/other-control state, canonical zero-POST/no-navigation filtering,
route/style/both-locale directions, human authorization + private headers + both media
bytes + deployed worker proof, W2 after freeze / stored 14-column snapshot / terminal
retained review. Global 600000ms test timeout, Playwright config/projects/descriptors,
artifacts, CI budgets: unchanged. No `noWaitAfter` change, no forced/manual POST, no fake
response, no reload workaround, no retry-until-green, no source/browser dependency
upgrade. The R2/R3/R4/R5 changes are strictly the B1 teardown, B2 diagnostics and B3
synchronization described above (per-commit stats in section 2).

## 7. B5 — documentation (committed; exact current docs only)

- `docs/TESTING.md` (+72 gross vs main): new section "Governance drag outcome
  synchronization and teardown first-error preservation (083/6-b)" — actual diagnosis,
  B2 suite outcome (NONREPRO), B3 repair description, asserted legal starting counts,
  B1 teardown preservation, explicit "cause remains unknown" for both the 5-wrapper
  mismatch and the postmerge 600s stall.
- `oap/MVP-PROGRESS.md` (+2/-2 gross vs main): status line for the 083/6 increment.
- R5 docs corrections (root review of `e929ac6f`): the split heading (continuation line
  was a paragraph) is merged to ONE heading line; the old-behavior sentence corrected to
  the accurate statement that EACH old attempt checked ready after its own gesture and a
  not-yet-ready insertion could still be followed by another (NOT "four gestures before
  any check").
- The a-report's corrected manual-context global-timeout propagation statement lives in
  the a report / pinned-source receipt, NOT in I9d TESTING.md (see C6); no retroactive
  doc claim is made.
- Pre-existing accept-lifecycle banner wording issue: recorded as an unresolved
  follow-up in section 17 (NOT a currently named test path; no test/banner edit in this
  round; no assertion removal/weakening).

## 8. Final gates at literal I `a4206939`

Gate evidence rules used throughout (per order + root decisions): FULL unfiltered
`git status --porcelain=v1` at START and END (validated against EXACT human3 exclusions
`.codex/`, `CODEX-SESSIONS.md`, `codex.sh` in the main checkout; the clean worktree is
fully empty); start variables captured BEFORE execution, never recomputed at END; logs
finalized BEFORE hashing; immediate native child exits (no `| head`/`| tail` pipeline
substitutes); unique attempt artifacts with refuse-if-exists; actual resolved image IDs
(including `web`) recorded while the owned stack is live.

### 8.1 GATE ALL31 — CLEAN isolated Git worktree (QUALIFIED)

- Worktree `/tmp/oap-083-6-b/iprime-worktree` created `--detach` at
  `a4206939bc971012be327564dd8d3bcb3db892b0` (tree `cf38630a`), status fully empty.
- Runner `/tmp/oap-083-6-a/all31-runner-0836a.sh` (bash; refuses pre-existing attempt
  artifacts exit 97; Python-UTC padded stamps; decimal cmd labels), fresh attempt dir
  `/tmp/oap-083-6-b/all31-clean-A420693`.
- Actual window 2026-10-26T01:37:57.736698Z..01:43:49.256881Z: **31/31 native 0, overall
  0**; unit suite 867 passed / 3 warnings / 33.56s (CMD 06). START/END snapshots both at
  HEAD `a4206939`/tree `cf38630a` with empty status. Full argv/order = the literal 31
  commands of the a order (uv 0.12.5 frozen chain, 10 service `--check`, node 24.22.0,
  pnpm 11.22.0 frozen install/lint/format/typecheck/test/build/licenses, compileall,
  unittest discover, check_repository, check_mermaid, markdownlint).
- Root independently qualified this run (31 native 0 / A420 clean / unit 867 33.56s).
- The earlier contaminated-checkout ALL31 (a round, 21/29/31 failures exclusively human
  `.codex` files) remains a preserved historical failure; clean worktree was the
  order-mandated vehicle.

### 8.2 GATE TWO independent FULL focused parity invocations (QUALIFIED, serial)

Exact command both runs: `pnpm exec playwright test
tests/e2e/frozen-review-parity.spec.ts --no-deps --project=freeze-review-snapshot` with
`SLAIF_E2E_SECRET_FILE` + `SLAIF_E2E_COMPOSE_PROJECT=slaif0835` + unique
`SLAIF_E2E_OUTPUT_DIR`; fresh owned stack per invocation (`down --volumes` then
`up -d --wait`), EXACT existing fixture seed (smoke.sh contract, two non-authenticatable
OIDC accounts, strict uninitialized precondition), private 0600 secret channel built per
`e2e.sh`, prerequisite `--project=setup --project=governance` native 0 each run.

- **f1** (`/tmp/oap-083-6-b/bp-parity-f1.log`): 01:44:01..01:47:47Z; seed 0,
  setup+governance 0, **parity native 0, 142708ms**; log 10307B SHA-256
  `7c47d7d16ad399b44cc87bbe7c98c428c1962429fdf24fd11c567ca65f3f8772`; START/END HEAD
  `a4206939`/tree `cf38630a`, clean-excluding-human3 both. Live raw per-container
  resolved image IDs captured while the f1 stack was LIVE at 01:47:43Z
  (`bp-parity-f1-live-image-ids.txt`, 15 containers / 5 distinct image IDs incl `web`).
  Caveat (honest): the f1 harness (v1) inspected mutable TAGS inside its log AND deleted
  the private governance drag-diagnostics JSON on the success path — the f1 governance
  JSON is **NOT RETAINED** (no invented data, no rerun for metadata); the f1 governance
  contract PASSED is proven by the log.
- **f2** (`/tmp/oap-083-6-b/bp-parity-f2.log`): 01:50:12..01:53:52Z; seed 0,
  setup+governance 0, **parity native 0, 139084ms**; log 17756B SHA-256
  `0f9b6f3148904ee4cb611dee3eb4d8dbeb50d56d768cf2510e01e44d25dfcf37`; START/END identical
  identity, clean both. v2 harness recorded RAW per-container resolved image IDs in-log at
  01:50:56Z and PRESERVED the private governance diagnostics (674B JSON, SHA-256
  `23b77907...` per root; both drags ready on attempt 0, wrappers == distinct throughout).
- Six internal pairings = the one test's full workflow (reporter prints the first matching
  `stage` annotation per contract — 4 reporter records across the whole run are NOT 6
  pairing records); all pairings assert within the single native-0 test.
- Images (cached reuse as-actually-selected; `created=2024-01-01` is the pinned
  reproducible build timestamp, NOT build time; `tests/e2e` appears in no Dockerfile COPY,
  so spec-only changes cannot alter image content): backend `sha256:3bf5e87a...`,
  browser-worker `sha256:61918b31...`, nginx `sha256:c8a163d7...`, postgres
  `sha256:368a3e01...`, web `sha256:eefc9b00...`.

### 8.3 GATE fresh WHOLE literal `sh tools/compose/smoke.sh slaif0835` (WHOLE1 FAILED preserved; WHOLE2 QUALIFIED native 0)

- **WHOLE1** (`/tmp/oap-083-6-b/whole-whole1.log`, harness `whole-run1.sh`): actual raw
  START 2026-10-26T01:55:44Z, END 02:14:24Z (18m40s), **native exit 1**, log 61390B
  SHA-256 `db25bcc570eb1a3eab5d7c681b857ec3453a77cc665f94cddc90cc6fa69f7e2f`; START/END
  HEAD `a4206939`/tree `cf38630a`, clean-excluding-human3 both; stack fully torn down by
  the smoke EXIT trap (no residual containers/volumes).
  - PASSED within WHOLE1: all 19 browser projects / 40 PASSED records incl.
    `governance` `puck-editor-round-trip-through-human-editor-api` (the I9d failure point
    — B3 verified full-stack), `freeze-review-snapshot` parity (155310ms),
    `accept-lifecycle`, `discard-lifecycle`, `media-publication`, review-surface
    contracts; restart-durability, browser-worker-secret/signing/artifact recovery,
    control-readiness recovery, render-locator failure+recovery, negative-bootstrap
    blocked, DB-locator image/log scans clean, Apache `apachectl -t` SyntaxOK and NGINX
    `-t` OK (existing edge configuration checks — Apache syntax is NOT live Apache HTTP
    parity), `browser-artifact-revoked` OK.
  - FAILED (exact): packaging phase = the LAST smoke check (smoke.sh line 1354, before the
    final OK line 1355): `python -m unittest discover -s tests/packaging -p test_*.py` →
    49 tests, 1 failure, 0.458s:
    `test_exact_safe_inventory_extracts_with_executable_mode`
    (tests/packaging/test_browser_archive_extractor.py:50): expected extracted executable
    mode 0o755 (493), actual 0o700 (448). No `compose-smoke: OK` footer.
  - MEASURED CAUSE (root-reviewed): the WHOLE1 wrapper set `umask 077` for private
    evidence files and the literal smoke child inherited it; `extract-zip.mjs` passes the
    zip entry mode to Node `writeFileSync` (`mode: attributes & 0o777`), and Node applies
    the process umask to that mode: 0o755 & ~077 = 0o700. Both production/test files are
    byte-identical main f35..I (0-line diff); this is a wrapper environment artifact, NOT
    an I'' product regression and NOT labeled flake.
- **Root-authorized ONE finite environment check** (child umask 022, exact same command at
  the clean A420 worktree): 02:18:05..02:18:06Z, **Ran 49 tests in 0.473s — OK (49/49),
  native 0**; log 706B SHA-256
  `540724199f5e9939dceb01eb4aa816becf314427c149ec0b0b1ca86041f7fe97`; same interpreter
  `/home/janezp/.local/bin/python` (Python 3.13.14) and Node toolchain as the WHOLE
  environment; START/END identity identical, clean worktree empty status. The child-umask
  evidence file (five bytes `0022` LF) was originally mode 0644 (created inside the 022
  subshell); the log/sidecar are 0600. No later chmod rewrites that history.
- **WHOLE2** (root decision 2026-10-26T02:22:06Z; harness `whole-run2.sh`; EXACT literal
  command inside a child with explicit umask 022, parent wrapper 0077, private
  log/sidecar pre-created 0600; actual child mode captured to pre-created 0600 file:
  `0022`; unique attempt with refuse-if-exists; live watcher recorded per-container
  resolved image IDs + container IDs + creation times on every set change; pre-run check:
  NO `slaif0835` containers existed before the child up): **QUALIFIED — native exit 0**,
  actual window 2026-10-26T02:23:26Z..02:41:25Z (17m59s), log 60779B SHA-256
  `c7059c941fed22fd2b72f23206daea4847bb5787b7b9c951b92235584631c5a9`, sidecar
  `whole-whole2.result.json`; START/END HEAD `a4206939`/tree `cf38630a`,
  clean-excluding-human3 both.
  - All 19 browser projects / 40 PASSED records incl. `governance`
    `puck-editor-round-trip-through-human-editor-api` (B3 verified under the full stack a
    third time) and `freeze-review-snapshot` six-pairing parity (131919ms);
    `accept-lifecycle`, `discard-lifecycle`, `media-publication`, review-surface and all
    stable-device projects passed.
  - Packaging: `Ran 49 tests in 0.510s` — **OK (49/49)**; the WHOLE1-failing
    executable-mode test passed under the controlled child umask 022 (deterministic pair
    with WHOLE1 documented above).
  - Recovery/security tail all OK: restart-durability, secret-file-policy, browser-worker
    secret/signing/artifact recovery, control-readiness recovery, render-locator
    failure+recovery, negative-bootstrap blocked, DB-locator scans clean,
    `browser-artifact-revoked` OK, Apache `apachectl -t` SyntaxOK + NGINX `-t` OK (edge
    configuration checks; Apache syntax is NOT live Apache HTTP parity), and the final
    `compose-smoke: OK` footer (reached — unlike WHOLE1).
  - Fresh-container provenance: watcher file 37272B, 16 change samples; ALL containers
    created 2026-10-26T02:24:26.303-26.692Z (immediately after the 02:23:26Z start, after
    the verified pre-run "none"), container IDs + resolved image IDs recorded per
    container (backend `3bf5e87a...`, browser-worker `61918b31...`, nginx `c8a163d7...`,
    postgres `368a3e01...`, web `eefc9b00...`); render-api force-recreated mid-run per
    smoke.sh 1247/1282 as expected (new container, tracked).
  - Teardown: after terminal, 0 `slaif0835` containers and 0 project volumes (smoke EXIT
    trap); smoke-owned mktemp secret channels removed by the same trap — no residue found
    in /tmp within the run window (checked).
- Deterministic pair establishing the cause: identical source/command/interpreter with
  child umask 077 → 1 packaging failure (0o700); child umask 022 → 49/49 OK. The changed
  execution condition for WHOLE2 is the evidence-backed wrapper correction, not a
  pass/fail-only unchanged retry. CI runner default umask was NOT independently measured;
  022 is the explicitly controlled child condition, not an established CI fact.
- If WHOLE2 fails: preserved and returned to root; no third attempt, no partial-run
  aggregation (order).

## 9. C1–C8 report-index corrections (explicit, per b order)

The immutable a report (`40750a3e`) is NOT amended; the following factual index errors in
it are corrected HERE:

- **C1**: the original FAILED ALL31 unit run was 867 passed / 3 warnings / 32.17s; the
  separate CLEAN ALL31 was 867 passed / 3 warnings / 34.60s. The original overall end
  23:19:00.946342Z is valid; its raw SOURCE snapshot 23:19:00.906033Z is a different
  marker, not evidence of clock regression.
- **C2**: the a report incorrectly labels prettier-write2/tsc2/eslint1 native exits
  unknown. Actual call `call_aaa34f4a31586894` at 2026-10-25T22:00:22.837Z captured them
  immediately: FAILED 2/2/1. Missing exit sidecars never erase actual command/output
  proof (root receipt `strategic-first-valid-native-static-failures.json`). Existing
  `eslint-2.exit`/`eslint-4.exit` also show FAILED 1; failed attempts are distinguished
  from later passing validations at their recorded commit subjects. The genuinely invalid
  earlier pipeline capture remains native UNKNOWN.
- **C3**: the actual original main failure log has 33 PASSED reporter records plus 1
  FAILED across 16 named projects, with FOUR other freeze-project tests passing before
  parity failed. It does NOT have 19 preceding records or six separate frozen-pairing
  reporter records; the internal matrix iterations belong to the one parity test, not
  independent test records.
- **C4**: a section 8 categorically narrated a form-resubmission mechanism for the two
  invalid iframe POSTs and then said WHY unknown. That mechanism is UNPROVEN. Actual
  counts/transport are stated with cause UNKNOWN, without the causal claim.
- **C5**: the first controlled preflight invoked sentinel-install/read helpers but ZERO
  `submitControlForm`/native fixture POST operations. Marker-absent-before-fixture-goto
  is proved; there is no universal zero-helper claim and no unsupported secure-context
  causal diagnosis.
- **C6**: the actual I9d TESTING.md 45-line addition does NOT contain the corrected
  manual-context global-timeout propagation statement; that statement lives in the a
  report / pinned-source receipt. Attribution corrected; no retroactive doc claim.
- **C7**: the WHOLE sidecar `head_start` was recomputed at END; its separate RAW
  START/END snapshots qualify the subject, and the sidecar is not called an independently
  captured start. Five matching wrappers alone prove neither authored-node count nor
  persistence nor the exact number of gesture insertions.
- **C8**: "no new production/test identity at a" is corrected to distinguish that a added
  no new production/test identity from its INTENDED new order/report transcript
  identities; no unqualified no-new-file claim is made.

## 10. Incidents and honest record (this round)

1. **Lost detached broad-prelim launch (R5):** a background preliminary-statics launch was
   detached and died with no child exits captured; the broad `pnpm typecheck`/`pnpm lint`/
   `pnpm format:check`/markdownlog results are ABSENT/UNKNOWN — not claimed, and NOT a
   demonstrated failure. Replaced by a foreground-owned targeted prelim (tsc project-wide,
   eslint + prettier on the two changed files, markdownlint on TESTING.md with the exact
   repo config): all native 0. The contaminated-checkout broad `pnpm lint` (ESLint) and
   markdownlint DO fail on the user's `.codex` files (known artifact; the clean-worktree
   ALL31 is authoritative); broad `pnpm format:check` PASSED in ALL31 (its explicit globs
   exclude markdown/human files) — not described as a broad-format failure.
2. **Accidental `prettier --write docs/TESTING.md` (R5):** before confirming the repo's
   `format:check` scope (explicit non-markdown globs in `package.json`; markdown is
   deliberately outside prettier), an unsolicited `prettier --check` on TESTING.md failed
   and a `--write` reformatted the WHOLE file (643-line diff, hundreds of unrelated
   lines). Contained by byte-exact `git restore` of the file plus re-application of ONLY
   the intended two R5 edits (verified: diff vs I' exactly the two intended hunks);
   targeted prettier on the changed TS file native 0; markdownlint (the repo's actual md
   gate) native 0. The accidental WIP diff and written file are preserved as scratch
   evidence (`accidental-prettier-write-r5.diff`,
   `accidental-prettier-write-r5-TESTING.md.wip`). No cap was expanded; no unrelated
   formatting accepted.
3. **f1 harness (v1) deleted the private governance drag-diagnostics JSON** on the success
   path before preservation was possible: the f1 JSON is NOT RETAINED (stated honestly,
   no invented data, no rerun for metadata). v2 harness (f2, WHOLE2, packaging) preserves
   diagnostics and records truthful END/sidecar on every terminal path.
4. **v1 image evidence inspected mutable compose tags**, not container `.Image` IDs:
   corrected from f2 onward (raw per-container resolved IDs + creation times), plus a
   separate live f1 capture at 01:47:43Z.
5. **WHOLE1 wrapper umask leak** — see section 8.3 (measured; root-adjudicated).
6. **Checkpoint arithmetic correction (root):** docs gross at I' `e929ac6f` was 77, at R5
   `a4206939` is 76; test gross 672. This report states the measured values only.
7. **B2 metadata caveats** (filtered status, omitted web, initial failed launch) —
   section 4; never rewritten, never called full.
8. No protocol incidents: the ONE b control OK was consumed once; no response.fifo write
   before this final publication; no old-signal replay; a-round reader never polled.

## 11. Historical carry scopes (exact named-path evidence only)

- **Two-edge full-tree carry chain (root-directed; no blanket oap exemption, no invented
  direct equality):**
  - EDGE 1 `I24a 24a4333569be6f2201f94c07be56d702cb1a33da` (083-5-e literal I, tree
    `e59de814afd7a334f9e37c482961fc4b1962a7c6`) → accepted main `f35ec753`: EXACTLY 4
    paths, all mode 100644, no mode changes: `oap/active` modified (blob
    `8791bf0`→`a4d918e`); ADDED `oap/orders/083-5-f-correct-qualified-evidence.md`
    (blob `10bd225`), `oap/reports/083-5-e-restore-postgres-overlay-and-final-gates.md`
    (blob `c1d5543`), `oap/reports/083-5-f-correct-qualified-evidence.md` (blob
    `0b16b66`). No other path, no production.
  - EDGE 2 `f35ec753` → `a4206939`: EXACTLY 8 paths, all mode 100644, no mode changes:
    `docs/TESTING.md` (`ce242e1`→`b30f186`, named doc), `oap/MVP-PROGRESS.md`
    (`bd6f104`→`a3dd4b6`, named doc), `oap/active` (`a4d918e`→`83b5d09`), ADDED
    `oap/orders/083-6-a-...` (`985fa49`), `oap/orders/083-6-b-...` (`7723229`),
    `oap/reports/083-6-a-...` (`b09cff4`) — the current transcript identities (the fifth,
    this b report, is added by S) — `tests/e2e/frozen-review-parity.spec.ts`
    (`1894448`→`217c631`, named test), `tests/e2e/governance.spec.ts`
    (`0059c81`→`733ac05`, named test). No other path, no production.
  - Production/builders/locks/policy: `git diff --name-only` for `services/ apps/
    packages/ compose.yaml uv.lock pnpm-lock.yaml pyproject.toml package.json .github/
    tools/ tests/packaging/` is EMPTY on BOTH edges. Prior 083/5 transcript blobs
    (083-5-e report, 083-5-f order, 083-5-f report) are byte-identical f35 vs A420
    (0-line diff). ALL31/focused/WHOLE/current-S CI are NEVER carried — re-executed at
    I (sections 8.1/8.2) and pending at final S.
- **I24a FULL 347 + coherent RC7 + OpenAPI 0-diff**: carried ONLY under the two-edge
  equivalence above; those historical tests were not re-executed at I. Current
  vulnerability recency is NOT carried.
- **I24a LOCAL6 (fresh local six-image)**: carried ONLY via exact equivalence from the
  FRESH final-S six-image / current security proof (section 14); not re-executed locally
  at I.
- **R6 controlled native transport proof attempt3** (a round, PASSED): may carry only if
  its actual new-helper core remains byte-identical/contiguous in I/final S — the
  `frozen-review-parity.spec.ts` submit-response binding core (main-frame navigation
  matcher) is unchanged from a's R3/R7 commits by the b diff (b's parity changes are
  teardown/diagnostics only, sections 2/3/6); earlier failed R6 experiments preserved.
- **I9d WHOLE FAILED** (a round, preserved): native 1 at 2026-10-25T23:47:17Z, governance
  Puck expected 2 received 5 within 8000ms, log 42439B SHA-256
  `7cdf1c5bf11493d095f11f8563dbe4940a580c4969b756fd83ee3a82930bc2d8`; later projects NOT
  RUN. The B3 repair directly addresses the demonstrated unsafe synchronization; the
  I'' WHOLE2 governance Puck contract result is the live check (section 8.3). The 5-wrapper
  over-add mechanism and the postmerge 600s CI stall cause remain UNKNOWN.
- **a-round historical failures preserved**: contaminated-checkout ALL31 (21/29/31
  human3-only; CMD21 ESLint exit 2, CMD29 policy exit 1, CMD31 markdownlint exit 1 with
  all 2587 issues in human `.codex` files; CMD22 format:check PASSED), R5 preflight
  failures, B2 initial failed launch.

## 12. Footprint, budget, transcript identities (actual, measured)

- Uniform `git diff --minimal --numstat f35ec753..a4206939` (all paths classified,
  section 2): TEST GROSS = 468 + 204 = **672** (cap 700); DOCS GROSS = 72 + 4 = **76**
  (cap 100); production/config/dependency/migration/workflow = **0**.
- Five transcript identities at final S: a order (298L), immutable a report (540L/37334B,
  SHA-256 `23c7dfc32d0cc5c807d11ef17c8e2ea745283976fa8b1411f40e73d43127e1ea`), b order
  (325L/19930B), this b report, active (`083-6-b` + LF). All other OAP content unchanged
  except the named MVP-PROGRESS doc (edge 2, section 11).
- No new test/doc identity, family, or path beyond the exact two tests + two docs; no
  pack/delete of proof to fit caps.

## 13. Owned runtime state at publication

- Owned `slaif0835` stack: torn down by the smoke EXIT trap after each WHOLE/parity
  run. A manual check after the 02:41:25Z WHOLE2 watcher terminal (before the
  02:42:03Z probe start) found 0 `slaif0835` containers and 0 project volumes (its
  exact time was not persisted); a truthful CURRENT read-only recheck at
  2026-10-26T02:52:40Z again found 0 containers / 0 volumes (private evidence
  `residual-check-20261026T025240Z.txt`, 0600). Nothing remained; no cleanup action
  was needed.
- Clean worktree `/tmp/oap-083-6-b/iprime-worktree` retained (disposable; removable).
- Foreign containers/projects (other SLAIF projects, integration PGs) never touched.
- All private secret-channel files removed by harness ends (0600/0400 mktemp; verified
  absent at each run end); WHOLE2 smoke-owned mktemp channels removed by smoke's cleanup
  trap (verified absent after the run terminal; exact check time not persisted).

## 14. Current-I CI and security (actual, as observed)

### 14.1 Bounded actual-image security evidence (post-WHOLE2, pre-report, root-directed)

To resolve the CURRENT critical-advisory image-bytes uncertainty, the ACTUAL selected
backend image `sha256:3bf5e87ac0345b6111a30d24a977d6aae89efd4d059bc2a587a2159e18325db1`
(as-actually-selected in the f1/f2/WHOLE1/WHOLE2 live watchers; provenance: pinned build
`created=2024-01-01`, size 41736809B, linux/amd64) was exported ONCE via a uniquely owned
UNSTARTED container (`docker create` `oap0836b-secprobe-20261026T024203` → `docker
export` → `docker rm`; create/export/rm all native 0; the container was NEVER started and
no app/service ran) at 2026-10-26T02:42:03-05Z. Bounded private read-only inventory
(`sec-backend-image-probe/inventory.json`, private 0600 local file; exact
paths/versions/SHA256 only — no CA bundle content, no credentials):

- `usr/local/lib/python3.12/site-packages/pip/_vendor/certifi/__init__.py`: **version
  2024.08.30** (the advisory-affected line per GHSA-6q48-6c7w-9gw2), 94B,
  SHA-256 `a7f19866b8d4c0f0548692e5099a066f49a2281292a83032642e43bc8baa6c74`.
- `usr/local/lib/python3.12/site-packages/pip/_vendor/certifi/cacert.pem`: 299427B,
  SHA-256 `94edeb66e91774fcae93a05650914e29096259a5c7e871a1f65d461ab5201b47`
  (hash only; content NOT output).
- `usr/local/lib/python3.12/site-packages/pip-25.0.1.dist-info/METADATA`: Version
  25.0.1, 3677B, SHA-256 `4fa7318cf30f979db7cec45c12cbbc2b4f88a15f12eefbf59a6291d0a03af926`.
- `usr/local/lib/python3.12/ensurepip/_bundled/pip-25.0.1-py3-none-any.whl`: 1841526B,
  SHA-256 `c46efd13b6aa8279f33f2864459c8ce587ea6a1a59ee20de055868d8f7688f7f`; certifi
  members INSIDE the wheel hash-identical to the unpacked copies (same `__init__.py`
  `a7f19866...`/2024.08.30 and same `cacert.pem` `94edeb66...`) — i.e. the affected
  vendored copy is present twice (unpacked + bootstrap wheel).
- `usr/local/lib/python3.12/ensurepip/__init__.py`: 9445B, SHA-256
  `90f6c76cd9ef7ed6daa198bb9ef771139683487f1b061211be7aa511831b2028` (bootstrap entry).
- Search scope (bounded, NOT an all-files absence claim): the inventory searched the
  named Python locations only — `usr/local/lib/python*` and `usr/lib/python*` for
  pip-vendored `certifi`, `pip-*.dist-info` METADATA and `ensurepip/_bundled`, plus
  `usr/share/python-wheels`, plus standalone `certifi` at `usr/local/lib/python*/
  site-packages`, `usr/lib/python*/site-packages` and `usr/lib/python3/dist-packages`.
  No standalone (non-pip-vendored) `certifi` was found in those searched locations;
  other possible copies elsewhere in the image are NOT excluded by this probe.
- Mode caveat (root correction): the `mode` fields in the private inventory JSON (all
  `0o600`) are the modes of the LOCALLY EXTRACTED files (the probe ran `umask 077` and
  recorded `os.lstat` of the extracted tree), NOT the original image tar modes. The raw
  export tar/rootfs were deleted after inventory, so the original image modes are
  UNRECORDED; no image-mode claim is made and no export was repeated to obtain them.

Interpretation (bounded, no closure claim): the secondary-triage hypothesis is now
verified against ACTUAL image bytes — the image base's system pip 25.0.1 (Python 3.12
base) vendors affected certifi 2024.08.30. This does NOT establish runtime reachability:
the app's uv-managed runtime venv excludes test groups and its pinned runtime deps are the
six listed in AGENTS.md; no observed product pip/TLS invocation exists. The advisory
stays OPEN; this evidence resolves the image-bytes uncertainty only, for root review;
future remediation (if any) is a separate order. No install/scan/source/lock/test change
was made; the bulky export tarball/rootfs were removed after inventory; the private
JSON and provenance are the retained evidence.

- PR #110 at implementation `a4206939`: root independent GitHub query — **all 30 checks
  COMPLETED/SUCCESS** (20 required + 10 internal PG14..18 A/B children), receipt
  `strategic-A420-live-checks.json`. This is current-I evidence only; it is NOT the final
  report-only-S proof.
- Final S CI: the report-only S push will trigger a fresh run; at the honest publication
  instant its required checks may be pending — the order explicitly allows "SELF checks
  may honestly be pending at publication; root independently waits." Final acceptance
  requires ALL 20 required check names + ALL 10 internal PG14..18 A/B children
  COMPLETED/SUCCESS, fresh actual CI Compose whole + six-image supply
  artifact/source/provenance, Critical 0, no ignored, exceptions EMPTY, inherited 19 High
  honestly compared, strict ruleset 20934043/apps 15368 except CodeQL 57789, no bypass —
  per the b order, none of which may be skipped/neutral/missing/failed/cancelled/pending.
  This report is NEVER amended after S to fill future-S results.
- **Open dependabot advisory (honest, no closure claim):** alert #17 CRITICAL
  `certifi 2026.7.22` (GHSA-6q48-6c7w-9gw2, patched 2026.10.19), created
  2026-10-25T20:30:10Z just after the PR #107 merge; 14 total open GitHub alerts at the
  observation time. Secondary read-only triage: locked `certifi 2026.7.22` is
  test-group-only; the backend app venv excludes test groups; historical six Syft
  catalogs lack standalone certifi/httpx/httpcore, and the backend base `pip 25.0.1`
  vendors affected `certifi 2024.08.30` (actual image bytes now verified by the 14.1
  probe above). No observed product pip/TLS invocation. Scanner "Critical 0" in our
  six-image scans is NOT
  equivalent to "no known criticals" on GitHub. The advisory remains OPEN; no
  dismiss/suppress/release-readiness claim; no lock/product edit under b (root will
  adjudicate a bounded test repair separately from subsequent security remediation).

## 15. Strongest reason not to merge

- The final report-only S has not yet pushed its fresh all-30 CI at the S head; the
  original 600s postmerge CI stall cause remains UNKNOWN (neither the B2 nonreproduction
  nor the R6 transport proof identifies it); the I9d 5-wrapper over-add mechanism remains
  UNKNOWN (B3 repaired the demonstrated unsafe synchronization; WHOLE2 is the live
  full-stack check). The open certifi advisory (#17) is unresolved: the affected vendored
  bytes are verified PRESENT in the actual backend image (section 14.1) while runtime
  reachability remains unverified/UNKNOWN, and no remediation/all-clear is claimed. Root
  alone reviews all rounds, the fresh S 30/CI Compose/ six images/security/policy and
  decides merge; COMPLETE/green CI/OK alone is never acceptance.

## 16. Confirmations

- Mode AMENDED_EXISTING_PR; same PR #110; no new PR/branch/numeric objective; no merge,
  auto-merge, close, or self-acceptance by this agent.
- No production authority exercised: zero production/config/dependency/migration/
  workflow paths changed (section 12 edge 2); no pin/lock/package/foundation/OS/
  scanner/exception/role/grant/schema/edge/service/promotion/audit/lifecycle change;
  no new test/doc identity beyond the exact two named tests + two named docs; no
  reporter change; no noWaitAfter/forced-POST/fake-response/reload-workaround/
  retry-until-green/assertion-weakening/timeout-increase.
- All original 083-6-a R1-R7 acceptance, oracles, security/privacy boundaries and
  non-goals remain binding and preserved (section 6).
- Secret discipline: no real secrets, capabilities, cookies, DB URLs, source/preview
  credentials or private artifact URLs committed or printed; fixture secret channels
  were private 0600/0400 mktemp files removed at run ends; diagnostic JSONs carry fixed
  enums/booleans/numbers only (no raw IDs/attribute values/DOM/content/URLs/bodies);
  bash-x/raw traces with expanded fixture data stay private 0600 outside Git (a-round
  practice continued).
- Scope: no selective/overwrite/private-SQL/public-API qualification, no browser/
  Chrome/Playwright upgrade, no architecture amendment, no next-order choice, no
  roadmap decision. The full product objective (083) and release criteria remain
  incomplete and active.
- FIFO protocol: the ONE b control OK consumed once; no early receipt ACK; no old-signal
  replay; the exact 2-byte `OK` (no LF) is written to `response.fifo` only AFTER this
  report-only S is pushed and the remote head/parent/sole-path/exact-bytes are verified,
  then the writer closes.

## 17. Limitations, blockers, remaining criteria

- WHOLE2 passed (section 8.3); WHOLE1 remains a preserved FAILED with its measured cause.
  No third attempt was needed.
- Report-only-S final CI (fresh 30 + Compose whole + six-image supply) pending until the
  S push; recorded honestly, never back-filled.
- Original 600s CI stall: cause UNKNOWN; 5-wrapper over-add: mechanism UNKNOWN; R6
  "why two invalid fixture iframe POSTs": UNKNOWN. No flake/benign/infrastructure labels
  anywhere.
- I24a FULL 347/RC7/OpenAPI and LOCAL6 carried by equivalence only (section 11); current
  vulnerability recency not carried; no local FULL 347/RC7 re-execution at I (not
  ordered).
- Pre-existing accept-lifecycle banner wording (asserted at
  `accept-lifecycle.spec.ts` line ~688) is a NOT-currently-named-path follow-up:
  recorded as unresolved; no banner/test edit in this round.
- B2 metadata caveats (filtered status, omitted web, initial failed launch) and the f1
  non-retained governance JSON remain limitations of that evidence only.
- 083/6 numeric objective: this round closes the test-cleanup/governance-gate scope
  (B1-B5 + gates); the FULL 083 product objective and release readiness remain open and
  are governed by future orders.

# OAP 083-5-b execution report — qualify the complete frozen review contract (PARTIAL)

## 1. Status

| Field | Value |
| --- | --- |
| Round | 083-5-b (numeric objective 083, increment 5, round letter b) |
| Order | `oap/orders/083-5-b-qualify-faithful-frozen-review.md` (273 lines, committed unchanged in `ea58664`) |
| Order SHA-256 | `5e3c1b0161b6171d4f5e3f38d5e2145ba2bba340fca4fb22ed5dedf03aaf940a` |
| `oap/active` bytes | `083-5-b\n` (8 bytes: `3038332d352d620a`) |
| PR mode | AMENDED_EXISTING_PR (PR #107, no new PR) |
| Status | PARTIAL |
| Human full-product goal | still active; numeric 083 remains PARTIAL (one bounded increment) |

PARTIAL, not by key/count: the in-scope source repairs and bounded focused
qualifications listed below are delivered and evidenced, but the order's final
gates (RC9: all-31 in order, fresh unfiltered integration directory, coherent
RC7, whole Compose/edge/six-device smoke, OpenAPI zero-diff, all 20 required
checks at the report head) did NOT run at the final committed source. They are
recorded NOT RUN / failed-as-observed below and are carried to the follow-up
round c under strategic control.

## 2. Repository and PR identity

| Field | Value |
| --- | --- |
| Repo | `ulfe-lmi/slaif-agent-site` |
| PR | #107 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/107> (state OPEN at report time; amended, never merged) |
| Branch | `oap/083-5-a-faithful-frozen-review` |
| Base | `main` |
| Verified remote base | `4bf74fdc8e74323045a7f8830cf393493e75fe0d` (re-verified with `git ls-remote origin main` at report time) |
| Starting remote head | `dbfaadc2bae3aadca6415673a453e84a235b01ae` |
| Obsolete candidate head | `ea5866414fd3807758b1c9c09c7a929e47218335` (candidate I of 2026-10-25 08:23Z; its CI failed, §6) |
| Literal implementation head (I) | `1e5521bd8685ed24a9009c2841a75baa5f4bd8b6` (pushed 2026-10-25 09:20:27Z) |
| Report publication commit | SELF (this report; sole path; first parent exactly I) |

## 3. Pushed commits (this round)

| SHA | Time (UTC) | Content |
| --- | --- | --- |
| `ea5866414fd3807758b1c9c09c7a929e47218335` | 2026-10-25 08:23 | Candidate: 32 paths — the 083-5-b implementation/tests/docs + b order/active transcript (16,826+/307−). Obsolete after §6/§7. |
| `1e5521bd8685ed24a9009c2841a75baa5f4bd8b6` (= I) | 2026-10-25 09:20 | In-scope repairs of candidate CI failures + boundary-proof correction, 7 paths (271+/154−). |
| SELF (this report) | pushed last | S: report-only child, first parent I, sole path this file. |

## 4. Exact changes at I (grouped)

### 4.1 Candidate `ea58664` — 32 paths, 16,826 insertions / 307 deletions

Production/config — 18 paths: `apps/web/app/[workspaceId]/[[...sitePath]]/route.tsx`,
`apps/web/app/review/[workspaceId]/[[...sitePath]]/route.tsx`,
`apps/web/next.config.mjs`, `apps/web/src/renderer/bounded-collection-filter.ts`,
`apps/web/src/renderer/collection-filter-components.tsx`,
`apps/web/src/renderer/components.tsx`, `apps/web/src/sites/review-page.ts`,
`apps/web/src/sites/review-projection.ts`, `infra/apache/slaif-agent-site.conf`,
`infra/nginx/nginx.conf`, `playwright.config.ts`,
`services/backend/src/slaif_agent_site/render_api/frozen_source.py`,
`services/backend/src/slaif_agent_site/render_api/projection.py`,
`services/browser-worker/src/execution.ts`, `services/browser-worker/src/url-policy.ts`,
`tools/compose/control_readiness.py`, `tools/compose/public_agent_acceptance.py`,
`tools/compose/smoke.sh`.

Tests — 11 paths: `apps/web/tests/renderer-behavior.test.ts`,
`apps/web/tests/review-surface.test.mjs`,
`services/backend/tests/integration/test_freeze_review_snapshot.py`,
`services/backend/tests/integration/test_frozen_review_parity.py` (new, 4,750+),
`services/backend/tests/integration/test_media_service.py`,
`services/backend/tests/integration/test_real_human_accept.py`,
`services/backend/tests/unit/test_health_apps.py`,
`services/backend/tests/unit/test_render_projection.py`,
`services/browser-worker/tests/contracts.test.mjs`,
`services/browser-worker/tests/url-policy.test.mjs`,
`tests/e2e/frozen-review-parity.spec.ts` (new, 2,584+).

Docs — 1 path: `docs/OPERATIONS.md` (RC7 false operator-path correction).

Transcript — 2 paths: `oap/active`, `oap/orders/083-5-b-qualify-faithful-frozen-review.md`
(unchanged strategic bytes).

Named-path reconciliation: 18 production/config paths are inside the 26-path
prospectively named set (the 22 a-round paths + `playwright.config.ts`,
`tools/compose/smoke.sh`, `tools/compose/public_agent_acceptance.py`,
`tools/compose/control_readiness.py`). 11 b-test paths are all inside the
28-path named test set (a-round 26 + `test_frozen_review_parity.py` +
`tests/e2e/frozen-review-parity.spec.ts`; continued a paths
`test_media_service.py`, `test_render_projection.py`,
`renderer-behavior.test.ts`, `review-surface.test.mjs`,
`url-policy.test.mjs`, `contracts.test.mjs`, `test_health_apps.py`
per the order's explicit reconciliation). `db/privileges.py` was NOT touched
in b (a-round 134 gross, within its 180 bound). No other path changed.

### 4.2 Final candidate `1e5521b` (= I) — 7 paths, 271 insertions / 154 deletions

| File | Change |
| --- | --- |
| `apps/web/src/renderer/bounded-collection-filter.ts` | News-leak repair: wire names carry the bounded deterministic projection-local control POSITION (`c.<pos>.q` / `c.<pos>.f<i>`, positions 0-127, 1-3 digits) instead of the 36-char composition node identifier; new exports `searchControlFieldName`, `filterControlFieldName`, `controlPositions`; `controlFieldNames(node, position)`. Global body cap derived EXACTLY from the worst admitted name bytes (40×6 + 360×7 + 112×8 = 3,656 for 128 positions): `POST_FORM_MAX_BODY_LENGTH = 18,879,047` — the worst admitted body sits exactly on the cap (N admitted, N−9 interior admitted, N+1 refuses at the global length guard; per-part guard independent). Stale `c.<nodeId>` doc comments corrected. |
| `apps/web/src/renderer/components.tsx` | Static shared-form renderer threads trusted `controlPositions` through `renderProjection`/`renderNode`/`renderComponent`; inputs use the position name helpers; no name (inert) when no trusted position — no UUID can reach any document. Prettier line-join repair. |
| `apps/web/tests/renderer-behavior.test.ts` | Static control render calls supply `controlPositions(fixture)` (realistic generated names, no UUIDs); expected names `c.0.q`/`c.0.f0`; normalization/byte-identity contracts preserved. Prettier line-join repair. |
| `apps/web/tests/review-surface.test.mjs` | Exact global-boundary proof at the derived cap (worst-body length == cap; N−9 interior admitted; N+1 refused at the length guard); special-name tests updated to the 8-byte transport bound: in-bound `valueOf` retained for validation AND refused by the verifier (uniform null), over-bound `__proto__`/`constructor` names refuse uniformly at decode; worst-encoding, Unicode round-trip, per-part, field-count, duplicate and unknown-name negatives all preserved. |
| `services/backend/tests/integration/test_freeze_review_snapshot.py` | Deterministic 067 default-region-ID md5 made explicitly non-security via `hashlib.md5(..., usedforsecurity=False)` with comment (CodeQL legacy-SQL alert); the exact ID assertion and production semantics are byte-unchanged. |
| `services/browser-worker/src/execution.ts` | Prettier line-join repair only (CI formatting step). |
| `services/browser-worker/tests/url-policy.test.mjs` | Prettier line-join repair only (CI formatting step). |

## 5. RC1-RC9 evidence map (source / logs / exits)

All focused runs are SERIAL, real PostgreSQL where marked, at the named source
SHA (`.source.sha256` sidecars in `/tmp/oap-083-5-b/`); `NATIVE_EXIT` lines are
the captured immediate child exits. Scope legend: PG = real local PostgreSQL
integration; browser = real deployed Playwright browser; unit = in-process.

| RC | Criterion | Evidence (path — log — source — result) |
| --- | --- | --- |
| RC1 (A/R1/R2) | Public Agent AND Editor mutation of all 16 domain families + R2 siblings, frozen through the real worker; retained values/versions/digests; exact-number raw digits/scale through capture/read/projector/approval | `test_freeze_review_snapshot.py::test_rc1_public_agent_and_editor_capture_retained_families` — `rc1-focused-run18.log` @ `866830bbf0edc8a4` — 1 PASS 18.57s (19 deselected) NATIVE_EXIT=0 (post-md5-fix rerun; original run18 2 PASS 35.77s/0). Numeric approval via qualified composition-only workspace `test_rc1_numeric_approval_composition_only_workspace` (same log, PASS): retained raw exactness + real common-projector before/after approval. PG. |
| RC2 (B/R3/R4) | Common consumer six-target fidelity; admitted 1000 positive / 1001 query-cost refusal on live ACTIVE preview + frozen surfaces with full effects; real trusted-SQL sibling mismatch refusal | `test_frozen_review_parity.py::test_query_candidate_bound_admitted_real_surfaces` (G10) and `::test_sibling_mismatch_recomputed_digest_admission_refusal` (G11) — `parity-focused-run7.log` @ `649e999f439b2408` — 2 PASS 41.41s (6 deselected) NATIVE_EXIT=0. Six-target public E2E contract: `tests/e2e/frozen-review-parity.spec.ts` — `e2e-parity18-pass-evidence.log` (E2E_PARITY18_EXIT:0, 2026-10-21T08:04:41Z, at the then-current source; current-source/current-image requalification deferred to c, §8). PG + browser. |
| RC3 (C/R5) | Immutable drift: post-freeze canonical publication of another workspace leaves stored payload/digest/frozen projections unchanged (drift metadata only); repeat after terminal discard + pending cleanup; live content unavailable → frozen reads work | Retained a-round qualified suite at the a head (20/20 CI SUCCESS on `565c99c`), unchanged in b except additive b tests; drift/discard/unavailable-retrieval cases exercised in `test_frozen_review_snapshot.py` (roundtrip + terminal sections) — focused reruns in §5 RC1/RC6 logs at b sources. PG. |
| RC4 (R6) | Real Agent private IMAGE + DOCUMENT uploads; authorized human active reads AND actual confined deployed browser worker BEFORE freeze; exact bytes; identical frozen bytes after freeze + terminal discard; typed closure negatives | `test_media_service.py::test_private_media_bytes_human_preview_bound_worker_frozen_review` — `media-focused-run1.log` — 1 PASS 138.22s (1 deselected) NATIVE_EXIT=0; root independently verified the native event (36585) at 2026-10-25T02:59:37.220Z with source unchanged. PG + real worker. |
| RC5 (D) | Isolated omission/stub counterfactuals: each required item removed → its test FAILS for the intended reason; no contamination | a-round isolated-omission suite (rc5-verify1..8 logs, 2026-10-21) retained unchanged at b head; b hostile no-effects matrix (§5 RC6) extends the counterfactual set for the new v2 surface. Full rerun at c. |
| RC6 (E/R7) | Genuine v1 bytes via 075: unchanged upgrade, honest limited read/discard, v1 approval refusal BEFORE effects, fresh recreation; complete E matrix; hostile no-effects | a-round E-matrix suite retained at b head (20/20 CI SUCCESS on `565c99c`). b additive hostile cases: `hostile-run4.log` @ `1ac8db18e72613fe` — 1 PASS 20.30s (19 deselected) NATIVE_EXIT=0 (E-D3 media-reference-row tamper full matrix); `hostile-run5.log` @ `fcf4ffaa7843ad2a` — 1 PASS 13.77s (10 deselected) NATIVE_EXIT=0 (G13 stored-digest co-tamper refusal); `hostile-run6.log` first launch — 3 PASS 45.71s (17 deselected) NATIVE EXIT NOT CAPTURED (semicolon-join caveat, `hostile-run6-launch-exit-caveat-2026-10-25.md`), second launch — 1 PASS 13.62s NATIVE_EXIT=0 (actual captured). PG. |
| RC7 (R9) | Coherent rollback: retained-v2 refusal FIRST (migration AND bootstrap), unchanged catalog/ACLs/readiness/COW; 075 restoration + 076 re-upgrade in a SEPARATE genuine v1-only disposable DB; OPERATIONS.md corrected | a-round RC7 suite retained at b head (20/20 CI SUCCESS on `565c99c`); `docs/OPERATIONS.md` false operator path corrected in `ea58664`. Coherent rerun at c. |
| RC8 (R8) | Admitted-work bounds: real 16-edge/17-node chain with node-by-node normalized facts; raw depth 7/8 capture + depth-9 real worker refusal; STRICTER-N admission wiring; ACTUAL production 8 MiB read-admission N-1/N/N+1 on coherent owner-hostile copies; narrow real-SQL value_cost boundary | `test_frozen_review_parity.py::test_rc8_captured_chain_raw_depth_and_byte_budget_wiring` — `rc8-capture-focused-run5.log` @ `a82be261aca7c697` — 1 PASS 39.03s (8 deselected) NATIVE_EXIT=0 (run3 pad / run4 polymorphic-SQL failures preserved as history). Secondary 8 MiB audit adjudicated in `rc8-8mib-audit-primary-review-2026-10-25.md`: corrected envelope verified (lawful upper < 8 MiB), guard unreachable from constraint-compliant inputs (defense-in-depth; enforcement qualified per layer by run5); F1/F2 reachability terms kept OPEN. PG. |
| RC9 (F) | All 31 in order at final committed source + fresh unfiltered integration dir + coherent RC7 + whole Compose/edge/six-device smoke + OpenAPI zero-diff + all 20 required checks at report head | NOT RUN under b (strategic pivot: known-failing images, §6/§8). Partial evidence: final-31 attempt 2 at clean checkout of candidate I — `final31/manifest31.log`: CMD 01-20 all EXIT=0 (mypy 316 files, unit pytest, uv build, 10 process smokes, pnpm install) before ROOT-directed stop at CMD 21 (`pnpm lint` running); attempt 1 died on exec-session reap after CMD 04 (`*-attempt1.log` preserved). METADATA CAVEAT: runner `printf '%02d'` printed CMD 08/09 as "CMD 00" (octal); the command texts and exits on those lines are real. NO all-31-pass claim. CI at candidate `ea58664`: 4 FAILED checks + 1 CANCELLED (§6). |

## 6. Candidate `ea58664` CI (workflow 40176411966, attempt 1) — observed failures

| Check | Job/annotation | Observed | Original evidence |
| --- | --- | --- | --- |
| Node contracts — formatting | job 121117941062 | FAILED: prettier on 3 files (`apps/web/tests/renderer-behavior.test.ts`, `services/browser-worker/src/execution.ts`, `services/browser-worker/tests/url-policy.test.mjs`) | `candidate-ea586641-node-contracts-job121117941062-original.log`, `ci-nodecontracts-40176411966.log` |
| CodeQL — high alert | check 121118066027 | FAILED NEW high alert at `test_freeze_review_snapshot.py:8832`: `hashlib.md5` deterministic 067 default-ID (legacy SQL, not a security hash) | `candidate-ea586641-codeql-high121118066027-original-annotations.json` |
| Compose public acceptance | job 121117941053 | FAILED `reason=news-default-listing-uuid-leak` AFTER 19-project E2E OK | `candidate-ea586641-compose-job121117941053-original.log` |
| Supply chain | job 121117941090 | FAILED policy: 31 Critical matches total (full six-scan census `candidate-ea586641-independent-all-six-critical-census.json`): browser 26 (pinned chrome 155.0.8059.84, fixed 156.0.8078.47 = current stable rev1706539), nginx 2 (brotli), postgres 1 (brotli), web 2 (Next 16.3.8, fixed 16.4.1); backend/apache 0. The original gate stopped at the browser image, masking later image policy failures — browser refresh alone does NOT resolve all. | `candidate-ea586641-supply-chain-job121117941090-original.log` |
| Foundation PG16 | job 121117941130 | CANCELLED 2026-10-25T08:38:36Z at the maximum execution 15m0s; underlying slowdown UNKNOWN (not proven flake) | `candidate-ea586641-pg16-job121117941130-original.log` + `-original-annotations.json` |

Repairs in scope under b (no pin/dep/image/guard/exception changes):

1. Formatting: the 3 files prettier-formatted (line-join only) — full
   `pnpm format:check` NATIVE_EXIT=0 (`format-check-newsfix-2026-10-25.log`).
2. CodeQL md5: explicit `usedforsecurity=False`, exact ID assertion and
   production semantics preserved — focused real-PG rerun 1 PASS 18.57s
   NATIVE_EXIT=0 @ `50b799bb7193c1f6` (`rc1-md5-fix-focused-run1.log`).
3. News UUID leak: reproduced locally pre-fix
   (`news-leak-repro-local-run1.log`, NATIVE_EXIT=1; isolated to the three
   generated control field names `c.<node-uuid>.q` / `c.<node-uuid>.f<i>` —
   search + two-facet filter — with no other leak source), repaired via
   position-based names + exact global cap (§4.2). Verified on the rebuilt web
   image from I source: build NATIVE_EXIT=0
   (`web-rebuild-newsfix-2026-10-25.log`), then
   `tools/compose/public_agent_acceptance.py --project slaif0835`
   NATIVE_EXIT=0 (`news-fix-acceptance-run1.log`; root-independently preserved,
   log SHA-256 `09b158007ed5ffe1776d62c2a17d4d6f7581837b19399662fc7b4b4e2edc10cd`):
   `public-agent-news-edge OK ... html=uuid-token-flight-free`,
   `public-agent-component-loop OK`, `public-agent-acceptance OK`.
4. Supply chain + PG16: NOT repaired under b (root-directed; bounded security
   remediation and rerun are c scope, §8).

Focused gates at I (native child exits captured,
`/tmp/oap-083-5-b/focused-*-newsfix.log`, 2026-10-25T09:19Z): web
`node --test tests/*.test.mjs` 32 pass/0 fail NATIVE_EXIT=0; vitest
`tests/contracts/renderer-behavior.test.ts` 28/28 NATIVE_EXIT=0;
`pnpm typecheck` NATIVE_EXIT=0; eslint root NATIVE_EXIT=0 (local-only addition
`--ignore-pattern '**/.codex/**'`: the untracked session plugin cache is not
present in CI; no repo lint config changed) and web NATIVE_EXIT=0.

## 7. Commit-message overclaim correction

`ea58664`'s commit message states "Full final gates run at this committed
source" and "public e2e six-target PASS" as if at that source. That is an
overclaim: the final 31/FULL/whole gates did NOT complete at `ea58664` (CI
failed, §6; the local final-31 attempt stopped at CMD 21 on root directive,
§5 RC9), and the six-target E2E PASS evidence is from 2026-10-21 at an earlier
source (`e2e-parity18-pass-evidence.log`). This report supersedes that
statement; the git history is not rewritten.

## 8. Remaining limitations (carried to c; nothing waived)

1. All 31 Critical CVE matches (browser 26 / nginx 2 / postgres 1 / web 2,
   §6) require bounded security remediation (pins/dependency repair per the
   strategic template for c, preserving the ignored-`sharp` +
   `images.unoptimized` boundaries and all 31 record fixes with actual fixed
   image scans). No pin/dep/image change was made under b.
2. RC9 final gates at the final committed source: all 31 standing commands IN
   ORDER, fresh COMPLETE UNFILTERED plugin-free backend integration directory,
   coherent RC7 proof, whole Compose/edge/six-device smoke
   (`sh tools/compose/smoke.sh slaif0835`), generated Agent OpenAPI zero-diff,
   and all 20 required checks (strict ruleset 20934043, apps 15368 and 57789)
   COMPLETED/SUCCESS at the report head. NOT RUN under b.
3. Foundation PG16 CI job: CANCELLED at the 15-minute maximum; root cause of
   the underlying slowdown unknown. Rerun (with measured timing) at c.
4. Current-source/current-image browser qualification of the six-target parity
   E2E and the whole smoke (engine versions/image/source identity for the
   final record) deferred to c with the repaired images.
5. RC8 8 MiB guard reachability: F1/F2 terms remain OPEN (guard is
   defense-in-depth; unreachable from constraint-compliant inputs per the
   adjudicated audit; production constant unchanged; no fabricated worker-max
   claim).
6. Hostile-run6 first-launch NATIVE EXIT NOT CAPTURED (semicolon-join launch
   semantics, caveat file preserved); the counts (3 PASS 45.71s) stand at
   source `1ac8db18e72613fe`; a clean-exit rerun is available at c.

## 9. Footprint (uniform minimal-algorithm inventory, base `4bf74fdc`)

Fresh actual at pre-I worktree (`inventory-pre-newI-2026-10-25.json`,
2026-10-25T09:18:17Z): production 33 paths / 10,731 gross; tests 30 paths /
20,849 gross; docs 6 paths / 80 gross; transcript 4 paths / 912 gross.
PROD+TEST actual = 31,580 under the unchanged 32,000 ceiling (420 headroom);
same exact 33 production / 30 test paths and individual caps. The a-round
totals (22 production / 9,350; 26 tests / 5,663; 6 docs / 70; 3 transcript /
639) plus this round's additions produced the fresh actual; no per-file cap
was exceeded. Whole-file line counts are identity metadata only, not diff
gross. The report-only S commit changes only this file (transcript path 5 of
the five cumulative allowance).

## 10. Confirmations and handoff

- No merge, no new PR, no auto-merge; PR #107 amended on its exact branch only.
- No pin/dependency/image/guard/exception/product-constraint change under b.
- No edits to old migrations, activated orders, published a-report, root
  constitution/architecture/protocol; a-report preserved as historical
  evidence including the overclaim corrected in §7.
- No production systems/data/credentials touched; all runtime evidence from
  the disposable local PostgreSQL + fake credentials + local Compose stack.
- No secrets, capabilities, cookies or private artifact URLs in this report.
- Untracked `.codex/`, `CODEX-SESSIONS.md`, `codex.sh` preserved untouched.
- OK below is not acceptance; strategy independently reviews, runs the c
  follow-up (ALL acceptance carried forward + bounded security remediation)
  and merges only after full review and every required check.

Report publication commit: SELF

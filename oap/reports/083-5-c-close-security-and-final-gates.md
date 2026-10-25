# OAP 083-5-c execution report — close security findings and final gates

## 1. Status

| Field | Value |
| --- | --- |
| Round | 083-5-c (numeric objective 083, increment 5, round letter c) — CLOSURE_ONLY |
| Order | `oap/orders/083-5-c-close-security-and-final-gates.md` (474 lines, committed unchanged with J) |
| Order SHA-256 | `ed521db8e1306fd235fe3dab0543d7e2b7dc54c02846fcf8a77bd0904c0fbbdb` |
| `oap/active` bytes | `083-5-c\n` (8 bytes: `3038332d352d630a`) |
| PR mode | AMEND_EXISTING_PR (PR #107, no new PR, never merged) |
| Status | PARTIAL — final clean-I gates only partially completed at I5 `d88ceaa`; every gate below is labeled pass/fail/not-run as actually observed (G1 ALL31, G3 WHOLE, G4 OpenAPI passed; G2 FULL interrupted/unqualified; G5 I-bound six-image NOT RUN). The current I5 CI terminal 17 SUCCESS / 3 CANCELLED blocks c acceptance; no claim is made that a future S under d cannot vary. Workflow repair is explicitly outside c; fresh FULL integration, the I-bound six-image run and the user-manual doc correction are carried forward to the prospective bounded d. No source change after I5; this report is the sole c report. |
| b report | `oap/reports/083-5-b-qualify-faithful-frozen-review.md` at `3b664b35ba882431be78713824eafba95a7128b3`, file SHA-256 `f7588f63c3220fcb7da864a9c1d4c0e2e279cf549756753dd44df0d167570a69` — IMMUTABLE, preserved byte-exact, never edited; its eight evidence-map corrections are recorded authoritatively in §10 |

## 2. Repository and PR identity

| Field | Value |
| --- | --- |
| Repo | `ulfe-lmi/slaif-agent-site` |
| PR | #107 — <https://github.com/ulfe-lmi/slaif-agent-site/pull/107> (state OPEN; amended, never merged) |
| Branch | `oap/083-5-a-faithful-frozen-review` |
| Base | `main` |
| Verified remote base | `4bf74fdc8e74323045a7f8830cf393493e75fe0d` (re-verified with `git ls-remote origin main` during this round) |
| Starting remote head | `3b664b35ba882431be78713824eafba95a7128b3` (b report-only S) |
| Intermediate implementation candidates J | J1 `b384f957c63cf4e9e0cd25b11d83ff07ece7fd58` (21 paths, +823/−111) and J2 `d161e9df4ade67a3bc83375a4124eb6e939b6608` (7 paths, +101/−10, repairs the four J1 CI failures; six-image qualification and candidate-9 measurement run at J2) — NEITHER is the final literal I: the recorded candidate-9 history entry, named current-history test restructure, final doc wording and the media-publication repair land in I |
| Intermediate implementation I1 | `e7dcbd81ecfe9d89190ac5f4c13daeb10f84c6e7` (4 paths: candidate-9 matrix entry, candidate-9 test asserts, SUPPLY_CHAIN current-line, approved media diagnostic v2 spec 2788273f +108/−0) — superseded as final literal by I2 after its NEW-SOURCE CI exposed the edge bare-URI 301 loop (§6c) |
| Intermediate implementation I2 | `38b519cadfe5886f6ae9a5a68525bf995834419a` (I1 + 1 path, infra/nginx/nginx.conf +20/−0, exact bare /preview//review edge forwarding; remote-verified; its NEW-SOURCE CI passed all 19 E2E projects + all post-e2e edge/secret phases and then FAILED the stale whole-smoke browser-artifact 22-file baseline — root-caused and repaired at I3, §6d) |
| Intermediate implementation I3 | `d51902d0da8faee5a1e6a571c37c15f6ba423379` (I2 + 1 path, tools/compose/smoke.sh +29/−3: artifact baseline re-derived from the finite first-half fixture map; defects found by root review at I3: invalid nested-aggregate SQL, unclosed kind set, cardinality-over-identity claim) |
| Intermediate implementation I4 | `f96bddba4c45491d8dd1d06154d2519d9acbed16` (I3 + 1 path, same file +15/−9: SQL aliased and validated on live PostgreSQL 18.6, closed exact five-kind set, true volume↔DB stem identity, corrected 082-2-a historical wording) |
| Literal implementation head (I) | `d88ceaa203848200a197af87fb19a42141bedde5` (I4 + 1 path, same file +21/−13: the 0/1 freeze-run optional bound to that run's observed terminal state — missing/duplicate/unknown-state run refuses; root counterexamples (masked loss / ghost pair) now rejected) — remote-verified PR #107 head; PARTIAL final-gate record at clean exact I5: ALL31/WHOLE/OpenAPI passed, FULL integration interrupted (unqualified), I-bound six-image NOT RUN (§7) |
| Report publication commit | SELF (this report; sole path; first parent exactly I) |

## 3. Pushed commits (this round)

| SHA | Time (UTC) | Content |
| --- | --- | --- |
| `b384f957c63cf4e9e0cd25b11d83ff07ece7fd58` (= J1) | 2026-10-25 10:58:46Z | Clean intermediate implementation candidate: 21 paths — c order/active transcript, CodeQL test-only live-region oracle, parity stage instrumentation, Chrome 156.0.8078.47/1706539 pin + identity assertions, NGINX 1.30.6-alpine3.24 (NGINX-ONLY 3.24) + exact per-image registry enforcement, PostgreSQL brotli overlay, Next 16.4.1 + coupled lock + regenerated notices, honest pending-qualification docs (823+/111−). |
| `d161e9df4ade67a3bc83375a4124eb6e939b6608` (= J2) | 2026-10-25 11:15Z (committed 2026-10-25T11:15:36Z); pushed after J1's NEW-SOURCE checks | Repaired clean intermediate: 7 paths (+101/−10) — ruff format of the J1 `test_policy.py` registry block; `tools/compose/smoke.sh` in-image browser identity now `chromium-1706539`/`156.0.8078.47`; authorized Next `16.3.8`→`16.4.1` literal in `tools/check_repository.py` + repository-policy fixture (82L prospective decision, all guards preserved); `pnpm-lock.yaml` omits ONLY the two unrelated deprecation metadata lines (raw resolver history retained); exact narrow `server/preview-props.json` crypto normalization in `tools/supply_chain/evidence.py` + 9 new `tests/supply_chain/test_evidence.py` cases (4 normalized identities, 4 malformed/missing/type/empty refusals, backend raw-byte, non-crypto-field content-diff negative). |
| `e7dcbd81ecfe9d89190ac5f4c13daeb10f84c6e7` (= I1) | 2026-10-25 13:01Z | 4 paths — candidate-9 measured history entry bound to the ONE consistent LOCAL J2 bundle (matrix +57, `supply-chain/browser-worker-critical-matrix.json`, named c production path); named current-history test restructure (`tests/supply_chain/test_policy.py`: 6→7 entries, candidate-7→`[-3]`, candidate-8→`[-2]`, candidate-9 `[-1]` with all measured identity/sbom/scanner/scan asserts); final doc wording after the measured scan (`docs/SUPPLY_CHAIN.md` current-line passages, pending→measured-at-J2); approved media diagnostic v2 (`tests/e2e/media-publication.spec.ts` 2788273f, +108/−0). Focused pretests green (§6b); NEW-SOURCE CI exposed the pre-existing-at-first-reach edge bare-URI loop (§6c). |
| `38b519cadfe5886f6ae9a5a68525bf995834419a` (= I2) | 2026-10-25 13:21Z | 1 path (+20/−0), `infra/nginx/nginx.conf`: exact bare `location = /preview` / `location = /review` edge forwarding (nginx documented bare-URI 301 on trailing-slash prefix + app 308 normalization = loop; app answers bare 404; child envelope/authority/CSP untouched). NEW-SOURCE CI passed all 19 E2E projects + post-e2e edge/secret phases, then failed the stale whole-smoke browser-artifact baseline (§6d). |
| `d51902d0da8faee5a1e6a571c37c15f6ba423379` (= I3) | 2026-10-25 14:03Z | 1 path (+29/−3), `tools/compose/smoke.sh`: whole-smoke browser-artifact baseline re-derived from the finite first-half fixture map (fixed 12 pairs + 0/1 conditional freeze pair; volume↔DB coherence). |
| `f96bddba4c45491d8dd1d06154d2519d9acbed16` (= I4) | 2026-10-25 14:13Z | 1 path (+15/−9), same file: root-reviewed I3 defects fixed — valid aliased histogram SQL (validated on live read-only PostgreSQL 18.6, empty + populated), closed exact five-kind set, true volume↔DB one-to-one stem identity (`v1-<artifact_id>-<sha256>` per artifact-store.ts), 082-2-a wording corrected (20 files/10 artifacts → 22/11). |
| `d88ceaa203848200a197af87fb19a42141bedde5` (= I, final) | 2026-10-25 14:19Z | 1 path (+21/−13), same file: the freeze-run optional bound to the unique `082 E2E freeze %` run's observed terminal state (N = 24 + 2·COMPLETED, screenshot = 3 + COMPLETED, own-artifact count asserted 0/1; missing/duplicate/unknown-state run refuses; masked-loss and ghost-pair counterexamples rejected). PARTIAL final-gate record at clean exact I5 = d88ceaa (§7; no "all gates run" claim). |
| SELF (this report) | pushed last | S: report-only child, first parent I, sole path this file. |

## 4. Exact changes at J (21 paths, grouped)

### 4.1 CodeQL test-only repair (finding 121131460161)

`services/backend/tests/integration/test_freeze_review_snapshot.py` (1 path, +34/−12):
the legacy 067 deterministic footer UUID oracle no longer re-implements the hash
in Python. F3 now performs a real trusted PUBLIC read-back of
`/api/agent/v1/global-regions` BEFORE the freeze (same admission surface the
product uses) and asserts the exact stored footer id against that live trusted
value. The 067 SQL default-id semantics (`md5(site_id||':'||'footer')::uuid`
computed inside PostgreSQL) are untouched production behavior; the test keeps
the exact legacy-ID equality and all closed-shape assertions. Stale
`usedforsecurity=False` comment corrected to the truthful derivation source.

Rejected alternative (preserved, not used): an 189-line custom MD5 oracle
helper (`_legacy_md5_hex_oracle`) replacing the modeled stdlib call — rejected
by root source review as helper obfuscation; attempt + full diff preserved at
`/tmp/oap-083-5-c/rejected-custom-md5-oracle-attempt-309604b6.*` (source
`309604b6`, freeze file 10488 lines at attempt time). Reverted before J with
`git checkout` of that path; all b baseline bytes preserved.

### 4.2 Parity timeout diagnostics (source repair, not a flake waiver)

`tests/e2e/frozen-review-parity.spec.ts` (1 path, +214/−12): a single `stage`
annotation (reporter `reporter.mjs` locates the stage by `find`) is now
replaced in place at every phase boundary with sanitized fields only
(`phase= engine= target= route=<ordinal> action= elapsed=<cumulative ms from
test start>`): setup/login/seed, api capture/preview-media, phaseA/phaseB/
canonical per pairing (combo, route ordinal, controls, locale clicks), worker
run/wait, freeze request/wait, review read, W2 create/theme/freeze/freeze-wait/
reauth/accept/accept-wait, terminal pending-check/discard/cleanup-wait/
post-bytes, cleanup. A `bodyCompleted` guard marks `cleanup` ONLY after
successful body completion, so a thrown error/timeout preserves the last
failing stage marker. NO timeout/retry/config/reporter/coverage change; NO
URLs/IDs/tokens logged; all original ALL6/controls/locale/W2/terminal
assertions preserved. Honest limitation: the marker's `elapsed` is the
stage-ENTRY cumulative elapsed time, not per-phase wall history (phase A/B
wall times remain in the existing `frozen-parity-timings` annotation).

### 4.3 Security pin repairs (production paths, 9)

- `services/browser-worker/Dockerfile` + `supply-chain/policy.json` +
  `tools/supply_chain/policy.py` + `tools/supply_chain/evidence.py` +
  `tools/compose/smoke.sh` + `tests/packaging/test_oci_contract.py`:
  Chrome for Testing `156.0.8078.47` at CfT revision `1706539`
  (archive URL `https://storage.googleapis.com/chrome-for-testing-public/156.0.8078.47/linux64/chrome-linux64.zip`,
  size 200206486, SHA-256
  `e6c94490f0b6b337225aeb2d2a5034858516b7017356980ba94f5176d8774a50`,
  Google official stable manifest observed 2026-10-24T22:16:21.275Z).
  Pretest `docker build --pull --no-cache` NATIVE_EXIT=0
  (`/tmp/oap-083-5-c/browser-worker-c-pretest-build2.log`); in-image identity:
  version string exact, executable SHA-256
  `230f0db8c5086182f46c59c867c0d461eb525d6552dfad226ea6b4d9ec249db2`,
  `/ms-playwright` = `chromium-1706539` only.
- `infra/nginx/Dockerfile` + policy.json/policy.py: NGINX
  `1.30.6-alpine3.24` (NGINX-ONLY 3.24 move; index digest
  `sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951`,
  amd64 manifest `sha256:84ed8c0dd296c188bfc24ed506f46589e9285fb0b11cf3a04d91d524d3067e11`),
  overlay `brotli-libs=1.2.1-r0 libcrypto3=3.5.9-r0 libssl3=3.5.9-r0` with
  installed-version assertions and retained `apk del curl`. Pretest build
  NATIVE_EXIT=0 (first attempt piped through `tail` — wrapper exit, preserved
  honestly as `nginx-c-pretest-build1.log`; second launch is the recorded
  native-0; the `nginx sh` invalid-entrypoint probe is preserved in history).
- `infra/postgres/Dockerfile` + policy.json: digest KEPT
  `sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
  (18.6-alpine3.23); `brotli-libs=1.2.1-r0` added to the existing exact
  overlay with version assertion. Pretest NATIVE_EXIT=0.
- `tools/supply_chain/policy.py`: exact per-image Alpine registry
  enforcement — global registry stays v3.23; nginx MUST state its registry
  explicitly (missing → fail) and must equal the exact v3.24 registry;
  backend/postgres/web must equal v3.23; any foreign/arbitrary registry
  fails closed; Dockerfile `--repository=` cross-check against the effective
  per-image registry.
- `tests/supply_chain/test_policy.py`: 6 meaningful registry negatives
  (missing nginx, nginx→v3.23, nginx→foreign, backend→v3.24, postgres→foreign,
  web→foreign) + source-cross-check nginx tag updated.
- Next.js `16.4.1` (+ `@next/env`, coupled 8 `@next/swc-*` version/integrity
  entries, 2 metadata-only `deprecated:` lines for unchanged packages) via
  the root-reviewed secondary scratch patch
  `2306fefae202426e5a32ae0c2cae3fba6681ff26c53401883edb9a5e2d6a59af` (224
  lines); all three bytes verified against workorder hashes:
  `apps/web/package.json` `f9fa9b0d…15f1c8`, `pnpm-lock.yaml`
  `6262873f…27466b2`, `THIRD_PARTY_NOTICES.md` `1c1c3e57…4a93b`.
  `pnpm install --frozen-lockfile` NATIVE_EXIT=0 (3 packages swapped);
  installed `next` 16.4.1 verified; notices regen byte-identical to the patch,
  `notices --check` NATIVE_EXIT=0 (components=298); `policy validate`
  NATIVE_EXIT=0. `pnpm-workspace.yaml` `ignoredOptionalDependencies: [sharp]`
  and `next.config.mjs` `images.unoptimized: true` untouched; no Sharp,
  libvips, optimizer, license, or other dependency change.

### 4.4 Docs (6 named current docs)

`README.md`, `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`,
`docs/SECURITY.md`, `docs/SUPPLY_CHAIN.md`, `docs/LICENSE_POLICY.md`:
pinned-vs-pending distinction throughout — the 156/1706539 pin is a MEASURED
archive/identity fact; its six-image qualification was PENDING at J1 and was
subsequently measured at J2 (§7.5); the current-line wording updated after that
measurement is part of the pre-I worktree recording (§3); 078-t unqualified coverage gap and 078-u scoped to
`153.0.8010.36` (PR #80, merged 2026-09-10 at `fe31c9f3`); the separate
`155.0.8059.84` (083-3, PR #102) candidate-8 history preserved; DEPLOYMENT
`next@16.4.1` npm integrity row updated
(`sha512-uc657V62E34fOI6W5NtG9IzwsPcms0Z60grz2MJGtglgD+pTFnNt4Yw2PzaU622tfX4vhrDgLZzicE2YlhI20Q==`,
verified against the applied lock).

## 5. Original 31-Critical census → component repair mapping

Original bS `3b664b35` supply-chain scan (all six reports independently
inspected, not only the first policy failure; census artifact
`/tmp/oap-083-5-b/candidate-ea586641-independent-all-six-critical-census.json`):

| Image | Critical matches | Component | Repair (this round) |
| --- | --- | --- | --- |
| browser-worker | 26 | pinned binary chrome `155.0.8059.84` | Chrome for Testing `156.0.8078.47`/rev `1706539` (every match lists fixed `156.0.8078.47`) |
| nginx | 2 | `nginx 1.29.7-r1` CVE-2026-15176 + `brotli-libs 1.2.0-r0` CVE-2026-111497 | `1.30.6-alpine3.24` (vendor: 1.31.7+ OR stable 1.30.6+) + `brotli-libs=1.2.1-r0` overlay |
| postgres | 1 | `brotli-libs 1.2.0-r0` CVE-2026-111497 | digest kept; `brotli-libs=1.2.1-r0` overlay in existing image |
| web | 2 | `next 16.3.8` GHSA-2464-fhr4-w9xw + GHSA-673q-mjm6-r5xr | Next `16.4.1` (maintainer advisories confirm patched version) |
| backend | 0 | — | unchanged |
| apache | 0 | — | unchanged |

31 are MATCHES, not 31 unique CVEs (nginx2 = ONE nginx CVE + ONE brotli).
Vendor labels some medium while the current scanner labels Critical; both
scopes retained, no unapproved dismissal/reclassification. Zero unexcepted
Critical is required across all six measured scans at the final I (§7);
exceptions remain empty.

## 6. bS `3b664b35` terminal CI (honest carry-forward)

14 SUCCESS / 6 non-success. Originals preserved in `/tmp/oap-083-5-c/starting-bS-3b664b35-*`
(`starting-bS-original-failures-independent-summary.json`):

| Check | Job | Observed |
| --- | --- | --- |
| CodeQL | check 121131460161 | FAILED — same md5 high alert at `test_freeze_review_snapshot.py:8832` (legacy SQL 067 default-ID, not a security hash). Repaired in J (§4.1); aggregate SUCCESS required at CURRENT S. |
| Supply chain | job 121131443595 | FAILED — 31 Critical matches (§5). Repaired in J/I; measured at §7. |
| Compose public acceptance | job 121131443570 | FAILED — `frozen-review-parity-six-stable-pairings` 600000ms timeout at 09:47:39Z AFTER four prior freeze cases PASSED. Cause UNKNOWN (not a proven flake); stage instrumentation added in J (§4.2) for attribution in the next authorized run; final WHOLE smoke at I is the required proof. |
| Foundation PG14 | — | CANCELLED at the 15m maximum execution. Root read of the original log: exactly 130 selected tests (4+81+24+9+12) PASS in the job before the teardown boundary; slowdown cause UNKNOWN, no flake claim, job status remains CANCELLED. |
| Foundation PG15 | — | CANCELLED — same 130-pass shape; cause UNKNOWN. |
| Foundation PG18 | — | CANCELLED — same 130-pass shape; cause UNKNOWN. |
| Foundation PG16 / PG17 | — | SUCCESS (full 130 selected passes). |

No unchanged-head rerun of any of these; the NEW-SOURCE checks on J/I are the
useful forward evidence and do NOT replace the final clean-I/local gates or
the 20 required checks at CURRENT S.

## 6a. J1 (`b384f957`) NEW-SOURCE CI — four concrete failures, all repaired at J2

J1 was pushed and its fresh NEW-SOURCE checks ran (never a replacement for the
final clean-I gates). Root independently saved the original job logs
(`J-b384f957-*-original.log`, `J-b384f957-current-checks-independent-20261025T111552Z.json`):

| Check | Job | Observed (J1) | Repair at J2 (`d161e9d`) |
| --- | --- | --- | --- |
| Python 3.12 | job 121149728536 | FAILED — ONLY `ruff format` on the new `tests/supply_chain/test_policy.py` registry block (line 104) | `ruff format` applied; format --check clean |
| Compose public acceptance | job 121149728541 | FAILED — in-image browser assertion still carried the stale `chromium-1697595` / `155.0.8059.84` identity in `tools/compose/smoke.sh:260-261` (the J1 edit had missed this second occurrence) | smoke.sh now asserts `chromium-1706539` + `Google Chrome for Testing 156.0.8078.47` + `cft_revision=1706539 chromium=156.0.8078.47` |
| Repository policy | job 121149728519 | FAILED — `tools/check_repository.py:1377` exact deployment-manifest literal still `next: 16.3.8` (+ matching fixture `tests/repository/test_repository_policy.py:115`); plus two incidental lock deprecation metadata lines flagged by the URL policy | Authorized by prospective named-path decision (workorders/083-5c-repository-pin-reconciliation-2026-10-25.md, 82L): ONLY the pin literal 16.3.8→16.4.1 in both named files, all guards preserved; ONLY the two unrelated deprecation metadata lines omitted from `pnpm-lock.yaml` (raw resolver/patch history retained; frozen install + notices --check byte-identical + policy validate all native 0 afterward) |
| Supply chain | job 121149728560 | FAILED — reproducibility: Next 16.4.1 newly emits `server/preview-props.json` with per-build random preview crypto, first manifest difference `preview-props.json` | Exact narrow normalization added to the existing named `tools/supply_chain/evidence.py` (same three fields already normalized in `prerender-manifest.json`, source-verified against installed next@16.4.1 `build/preview-key-utils.js` + `build/index.js`), fail-closed on any structural deviation; meaningful positive (cross-build equality, 4 normalized identities), 4 malformed/missing/type/empty refusals, backend raw-byte, and a non-crypto-field content-diff negative in `tests/supply_chain/test_evidence.py` |
| CodeQL | check 121149843147 | **SUCCESS at J1** (the §4.1 live-region oracle cleared the finding) | n/a — aggregate SUCCESS still required at CURRENT S |

J2 NEW-SOURCE CI (run 40188115724, originals preserved in
`/tmp/oap-083-5-c/j2-*-original.log` + `j2-checks*.json`): 17 SUCCESS /
1 FAILURE / 2 CANCELLED. CodeQL SUCCESS, Node contracts SUCCESS, Repository
policy SUCCESS, Python 3.12/3.13/3.14 SUCCESS, **Supply-chain evidence
SUCCESS (CI-side six-image qualification at revision M, artifact
12597008202 — root-verified, §7.5)**, PG16/17/18 SUCCESS.
CANCELLED: PG14 + PG15 at the 15m0s maximum execution (annotation verified);
each original log contains exactly 130 selected passes completed before the
teardown boundary (last batch 11:29:3x, cancel 11:30:5x); the `initial setup
failed` lines are the intentional bootstrap-negative server-log probes;
slower-timing cause remains UNKNOWN (PG14/15/18 at bS vs PG14/15 at J2 —
runner variance, no flake claim, no timeout waiver).
The instrumented `frozen-review-parity-six-stable-pairings` PASSED in that
run (69471ms, stage marker `phase=cleanup action=close` — the first measured
pass of the stage-instrumented suite; scoped NEW-SOURCE evidence, not final
acceptance). The single FAILURE is `media-publication` contract line 2069
`expect(failures()).toEqual([])`: one classified
`console-other-other-browser-error` on the NEW images (Next 16.4.1 web /
Chrome 156); raw console text is not logged by design (bucket-only
observation). Root-cause diagnosis: recorded scratch handoff
(`workorders/083-5c-media-diagnostic-scratch-handoff-2026-10-25.md`, 45L,
2026-10-25T11:54Z) — secondary prepares a ONE-FILE diagnostic proposal for
`tests/e2e/media-publication.spec.ts` (baseline J2 `d161e9df`) in isolated
scratch only (sanitized phase/classifier enums, console type, numeric text
length, bounded origin/scheme classification; NO raw message text/URLs/IDs/
tokens; existing classifiers unmodified; all original assertions and the
final `failures()==[]` preserved; E2E page-engine identity to be recorded as
measured evidence, not inferred equal to the product-worker CfT 156).
Primary alone reviews/applies/runs the returned patch serially; no
unknown-error allowance, no test weakening, no assumed-benign fix. Diagnosis
estimate 40..100 gross inside the recorded other-final-repairs bucket.

J1 has NO successful six-image qualification; its real failures are preserved
as-is and were the concrete input to J2. J2 = repaired clean intermediate
(7 paths, +101/−10; verification at J2 worktree: ruff/mypy clean,
tests/supply_chain 39+20 subtests, tests/packaging 49+38 subtests,
tests/repository OK, check_repository.py clean apart from the pre-existing
untracked human `.codex` host cache, reproducibility double build OK with
`next-build-id febb348e081d11bcecfc2364b6853005` and agent-openapi zero-diff
inside the same run). The actual J2 six-image qualification is §7.5.

## 6b. J2 Compose `media-publication` console error — focused diagnostic lane

J2 NEW-SOURCE CI (run 40188115724) failed the `media-publication` contract at
line 2069 `expect(failures()).toEqual([])`: exactly one classified
`console-other-other-browser-error` bucket entry (console source, other type,
other phase; raw text not logged by design) on the NEW images (Next 16.4.1
web / Chrome 156), AFTER the instrumented
`frozen-review-parity-six-stable-pairings` target PASSED (69471ms). Raw console text is not logged by design
(bucket-only observation). Cause at J2 time: UNKNOWN.

**Diagnostic source (approved, applied):** recorded scratch handoff
(`workorders/083-5c-media-diagnostic-scratch-handoff-2026-10-25.md`, 45L,
11:54Z) → secondary isolated-scratch proposal v2 (report
`media-diagnostic-handoff-report-v2.md`; patch
`e06717dafa698e65a4691d8c39ee37847939c7d2731e9e6310e6e01ce82697d6`, +108/−0,
ONE file `tests/e2e/media-publication.spec.ts`, standard a//b/ labels, pure
insertions; scratch statics tsc/eslint/prettier native 0; v1 `fc4495ad`
preserved with its two root-found delivery defects) → root read full v2 +
report and APPROVED → primary applied to the shared repo and verified the
resulting bytes: 2070→2178L, SHA-256
`2788273f55d1c830f923479c8fdd0dc93b02a214e370374d1d4779d21d8bda1b`
(exact approved target). Applied-source statics with immediate child exits
(`media-v2-statics-124540.log`): tsc 0 / eslint 0 / prettier 0.

v2 design (all original steps/assertions and the final `failures()==[]`
byte-identical last line preserved; no timeout/retry/config/reporter/coverage
change): spec-local console listener recording error TYPE only — observed
uncapped counter, stored redacted records capped at 16
`{phase enum (7), source enum, message enum, type, length, scheme class (9)}`;
`expectConsoleClean(label)` rethrows with redacted detail + cause at login,
3 preview navigations, and pre-final. Measured E2E page-engine identity:
Playwright chromium rev 1234 (runner-installed; UNCHANGED by this PR) — the
product-worker CfT 156 is container-local only, so the web-image Next
16.3.8→16.4.1 change is the real runtime variable for the observed page
(engine finding root-accepted).

**Focused attempts (all logs preserved; each attempt-specific; NONE
reproduces the CI console error; no aggregation, no flake/benign label, no
unchanged rerun):**

| ID | Scope | Outcome (honest) |
| --- | --- | --- |
| `focused-media-run1.log` (b era, 12:0x) | sh harness | harness defect: `#!/bin/sh` with bash-only `PIPESTATUS` + tee pipeline — recorded exits are NOT native child exits; two distinct setup failures (missing `SLAIF_E2E_COMPOSE_PROJECT`; then missing parity preview workspace). Preserved. |
| `focused-e2e-run-122011.log` | full e2e.sh driver, fresh volume | setup PASSED; governance FAILED locally at line 733 `.puck-trusted-component` Expected 1 Received 2 (8000ms) on the governance-created site — host browser rev 1234 vs CI runner variance; aborted before media. Recorded as local environment variance, NOT a source defect; no weakening. |
| `focused-media-seq-122624.log` | fresh J2 stack: setup + seed + preview + preview-filtering + media (governance/stable-devices/agent/puck/review-surface/freeze/accept/discard skipped, scratch-confined) | media FAILED line 152 `demoUpload` Expected 201 Received 404 (parity upload 201 in the same run) — a FIXTURE-prerequisite gap, not the CI console error. |
| spawn 124706 (12:47) | first nohup launch of the v2 single-project run | backgrounded chain reaped with the exec session; no log produced, no test executed. Preserved as spawn/harness record. |

**Fixture prerequisite qualified (root cause of the 122624 demo 404):**
`POST /media/v1/sites/{site}/assets` authorizes through
`control.slaif_media_authorize` (030_001_media_service_surface.py:97–127),
which JOINs `workspace.site_id = target AND created_by = account AND
actor_type='HUMAN' AND status='ACTIVE' AND expires_at > now()`; no row →
`None` → uniform 404 (media_service/auth.py:59, media_http.py:136). The
e2e.sh seed creates the pinned HUMAN workspace for the PARITY site only. In
the standing sequence the governance test
`puck-editor-round-trip-through-human-editor-api`
(governance.spec.ts:430–464) performs the first human editor write on the
DEMO site, and every non-agent editor request resolves
`control.slaif_human_editor_workspace_resolve`
(028_001_human_editor_workspace_envelope.py:73–116, via
control_api/site_authority.py:145–148), which materializes the server-owned
HUMAN workspace `Human page editor` (L2_SITE_EDITOR, 8h TTL) when none
exists. DB-verified on the live J2 stack: one human
`GET /api/editor/v1/sites/<demo>/pages/` (HTTP 200) created HUMAN workspace
`5858c41b-200c-4a20-bb1f-6431a4ff5715` (12:44:51Z, ACTIVE, 8h TTL,
created_by compose.admin) — after which the media project PASSED. The
scratch focused driver now materializes this SAME original mechanism
(login + one editor GET, then psql verification) before the media project;
NO product auth/migration/404 change, NO test weakening. Secondary read-only
source index: `/tmp/oap-083-5-c/focused-media-demo404-index.md` (corroborates
the code path; its CI-supplier hypothesis is now DB-verified as to the
mechanism).

**Results with v2 source + complete fixture setup (focused pretests, NOT
final-gate credit):**

- Live J2 stack, single project, pre-existing qualified prerequisite:
  `media-v2-focused-124809.log` — media-publication PASSED,
  `MEDIA_V2_FOCUSED_NATIVE_EXIT=0` 12:48:36Z, source `2788273f…`.
- FRESH J2 volume full focused sequence:
  `focused-media-seq-124938.log` — setup PASSED, seed OK, preview (8) +
  preview-filtering PASSED, prerequisite login/editor HTTP 200/200, HUMAN
  workspace `43cfbc99-1173-4d5e-951e-807308e97dd7` verified present,
  media-publication PASSED, `FOCUSED_MEDIA_SEQ_NATIVE_EXIT=0` 12:51:28Z.

**Honest status:** the original CI console-error cause REMAINS UNKNOWN. It
did not reproduce in either local focused run (minimal sequence state; J2
web image Next 16.4.1; host chromium rev 1234; v2 console instrumentation
active at all five checkpoints + final assert). No unknown-error allowance
or assumed-benign fix was introduced. The final WHOLE gate at clean I
(`sh tools/compose/smoke.sh slaif0835`, all phases in order, both edges,
ALL6, 600s) is the authoritative check: if the error reproduces there, the v2
stage markers + redacted classification identify the phase and a concrete
repair at a NEW I follows; if it does not, the media project qualifies at
the final gate.

**Privacy:** the `bash -x` debug trace and the curl cookie jar used for the
prerequisite contain expanded fixture credentials/session cookies; both are
kept mode 0600 outside the repository, are never published, and only
non-secret attempt metadata (HTTP statuses, workspace UUIDs, native exits,
source hashes) is retained in logs.

## 6c. I Compose failure — edge bare-URI 301 loop (root-caused, repaired at I2)

New-source CI at I `e7dcbd81` (run 40195270664, job 121174645702; original
2723L log preserved by root, `/tmp/oap-083-5-c/I-e7dcbd81-compose-job121174645702-original.log`
SHA `d137de72…`): ALL 19 E2E projects PASSED — including the v2-instrumented
`media-publication` (the J2 console error did NOT reproduce) and
`frozen-review-parity-six-stable-pairings` (66110ms) — and the post-e2e
public-agent/news/component/acceptance/restart/media/human-envelope/
governance phases all OK. The job then exited 1 SILENTLY between the
`governance-e2e: OK` marker (13:04:40.125Z) and the `edge-header-policy: OK`
marker, i.e. inside the smoke.sh lines 515–581 window (7 health GETs, 6
legacy 404 probes, edge-header assertions). CodeQL aggregate for I:
SUCCESS (121174801200, 13:05:21Z); the other 13 I checks SUCCESS at first
terminal read; PG matrix + supply-chain pending at that read.

**Root cause (proven by bounded read-only probes on the existing stack):**
the b-era edge change added nginx prefix locations `^~ /preview/` and
`^~ /review/` (infra/nginx/nginx.conf, base→I +19). nginx documents
(ngx_http_core_module, prefix location ending in a slash with a proxy_pass
target) that a request mapped to such a location by the first part of the
URI alone receives an automatic 301 to the URI with a trailing slash.
Measured at the edge (8080): `/preview` → 301 `Location: …/preview/`, then
the application (Next 16.4.1, unchanged pin) normalizes `/preview/` → 308
`location: /preview` — an infinite 301/308 loop (verified `/review` and
`/media`-analog; `curl -L` max-redirs). The app itself is correct: direct
web:3000 probes (no nginx) return `/preview` 404, `/review` 404,
`/media` 404, `/preview/<uuid>` 307 `/login` with private/no-store +
noindex, on the unchanged 16.4.1 pin. Main (without the b blocks) had no
bare-URI 301 for these paths, so the loop is introduced by this PR's edge
change, NOT by the Next upgrade (Next 16.4.1 pin REMAINS; the 16.4.3
scratch probe in `/home/janezp/codex-work/next1643-probe` — which also
returned bare 404 — was isolated, never transferred to product, and its
evidence is preserved). The 301 had been masked in every prior CI attempt
because each earlier Compose run failed at an earlier phase (bS news
leak; J1 stale browser identity; J2 media console error) — this was the
first run to reach the post-e2e edge assertions.

**Repair at I2 `38b519ca` (1 path, +20, `infra/nginx/nginx.conf` — named
c production path):** two exact bare locations
(`location = /preview`, `location = /review`) that forward the bare URIs
directly to the application (which answers 404 there), placed ahead of the
`^~` blocks. Child paths, the 20 MiB same-path form envelope,
authorization, and response policy are untouched; no assertion weakened;
no Next/pin change. Local verification on the rebuilt live edge (before/
after, read-only probes): the six smoke.sh legacy 404 probes all 404
(incl. `/preview`); `/preview` 404, `/review` 404; `/preview/` → 308 →
404 (loop terminated, 1 redirect); child `/preview/<uuid>` 307 `/login`
with `Cache-Control: private, no-store` + `X-Robots-Tag` intact; 1.5 MiB
POST to a child path passes the edge (404 from app, NOT 413) while
21 MiB is 413 (envelope enforced); 2 MiB POST to the bare URI is 413
(bare keeps the default 1 MiB, fail-closed); `nginx -t` OK; bare `/media`
301 is pre-existing MAIN behavior (unchanged by this PR, outside the
smoke probe set, left as-is).

I `e7dcbd81` is therefore an intermediate identity: its local ALL31
(attempts 1+2, §7.1) and its CI checks remain evidence AT I but the final
clean-I gates run at I2.

## 6d. I2 Compose failure — stale whole-smoke browser-artifact baseline (root-caused, repaired I3→I4→I5)

**Failure.** I2 CI job 121180881653 (run 40197324794) passed all 19 E2E
projects (`compose-e2e: OK projects=19 … media-publication=1`), all
public-agent phases (news-edge, component-loop, acceptance, restart),
media-e2e, human-editor-envelope, governance-e2e, edge-header-policy,
edge-body-limit, database-login-policy, secret-file-policy and every
render/browser secret policy — then failed with a bare `AssertionError`
from the inline `python -c` at smoke.sh:727–732
(`browser-artifact-root-policy`), 13:33:22.85Z. Original 2790-line log
root-preserved `/tmp/oap-083-5-c/I2-38b519ca-compose-job121180881653-
original.log` SHA-256 `790edf2d…` (my copy retained). That check asserts a
hard-coded main-era volume baseline: exactly 22 files (11 `.bin` + 11
`.json` pairs) in the browser-artifacts volume after the first half of the
whole smoke.

**Root cause (source-derived, not a browser/Next effect).** The 19-project
e2e manifest and the 22-file literal are byte-identical to main; every
earlier CI run of this PR (bS parity 600 s timeout, J2 media-publication
console error, I1 edge loop) failed BEFORE this check, so the literal was
never exercised against 083-5 sources. The finite first-half
retained-artifact fixture map is:

| Fixture (one run each unless noted) | Retained artifacts |
| --- | --- |
| `public_agent_acceptance.py` theme proof run | 4 (screenshot, structure-summary, console-summary, failed-request-summary) |
| `public_agent_acceptance.py` news journey run | 2 (heading-summary, structure-summary) |
| `public_agent_acceptance.py` component render-loop run | 4 (heading-summary, structure-summary, console-summary, failed-request-summary) |
| `review-surface.spec.ts` completed run (waits COMPLETED, screenshot) | 1 |
| `frozen-review-parity.spec.ts` completed run (over-quota follow-up refused 429, retains nothing) | 1 — NEW in 083-5, the certain +1 |
| `freeze-review-snapshot.spec.ts` screenshot run — freeze policy leaves it COMPLETED (1) or bounded-CANCELLED (0), both valid (spec 430–455) | 0 or 1 |

Fixed 12 pairs plus the 0/1 conditional freeze pair = **24..26 files**;
the 22-file literal is unreachable. The review-surface run was ALREADY
inside the main-era 11: 082-2-a commit `482506f9` raised the smoke
literal from 20 files/10 artifacts to 22/11 (root git proof); no other
e2e spec dispatches retained browser runs (only the three specs above
reference `/api/agent/v1/preview-runs`).

**Repair, three preserved commits (no amend/rewrite; I3/I4 retained as
history).** Every permission/credential/marker predicate of the baseline
(volume root 0700/uid+gid 10001; per-file 0600/uid 10001/nlink 1/regular/
non-symlink; `sbp1.`/`sbws1:`/`sas2_` byte scan; read-only
`--network none --cap-drop ALL --cap-add DAC_READ_SEARCH` probe) is
preserved verbatim; the downstream `baseline+12` check is unchanged
(deterministic `2:0:6` worker runs; the non-evidencing `AGENT_RUN_ID`
heading run contributes 0 by design).

- **I3 `d51902d`** — first re-derivation (24..26 literal, volume↔DB
  cardinality+histogram). Root review found: (1) the histogram SQL used an
  unaliased `count(*)` outside its inner `GROUP BY` (invalid PostgreSQL);
  (2) the kind set was not closed — an unknown kind could ride along under
  the total; (3) the comment claimed a volume↔DB bijection while only
  cardinality + histogram were checked.
- **I4 `f96bddb`** — aliased histogram SQL, validated on a live read-only
  PostgreSQL 18.6 (empty and 13-row populated scratch schema, then
  dropped; native 0); closed exact five-kind set; true one-to-one
  volume↔DB identity: each volume pair is named `v1-<artifact_id>-<sha256>`
  by the artifact store (`services/browser-worker/src/artifact-store.ts`
  `stem()`) and matched against `control.browser_artifact (id, sha256)`
  stems, so an orphan file or a missing retention row fails; internal
  histogram↔total consistency added. A dry-run harness bug was caught
  before commit (`.json` is 5 chars; stem via `with_suffix('')`), verified
  by a 12-case logic matrix; packaging contract tests 49/49.
- **I5 `d88ceaa`** — root counterexample to the still-unbound 0/1: with
  the freeze run COMPLETED, deleting another required screenshot row+pair
  (13→12) still passed; with CANCELLED, an extra screenshot row+pair
  (12→13) passed. The optional is now BOUND to the observed terminal state
  of the unique `082 E2E freeze %` run (title prefix unique across specs;
  validated live: `NONE:0/0` no-run, `COMPLETED:1/1`, `CANCELLED:0/1`):
  N = 24 + 2·(COMPLETED), screenshot = 3 + (COMPLETED), the run's own
  artifact count asserted exactly 0/1; a missing, duplicate or
  unknown-state freeze run refuses. A physical orphan file still fails the
  identity check and is investigated — never deleted or ignored to fit.
  Final 15-case matrix: both legal branches pass; all 13 negative cases
  (old literal, masked loss, ghost pair, own-count mismatch, no/duplicate
  run, unknown state, unknown kind, orphan/missing stem, broken pairing,
  empty table) refuse.

I5 gross 32348 (production 11063/43 + tests 21285/34; uniform
minimal-diff vs base with the full c allowance map; unmapped 0) under the
unchanged 33000 (headroom 652); same named paths, no new file, no pin or
guard change.

**I2 terminal CI (run 40197324794, authoritative at that identity).**
17 SUCCESS (12 workflow jobs + CodeQL checks incl. aggregate
40197324828) / 1 FAILURE (Compose 121180881653, §6d) / 2 CANCELLED
(PG14 121180881783, PG16 121180881685, 15m maximum; original logs/
annotations root-saved under `/tmp/oap-083-5-c/I2-38b519ca-pg*`), PG15/
17/18 SUCCESS. NOT final S acceptance; the final clean-I gates and the
20 named required checks at CURRENT S remain.

**I2 FULL-integration note (honest).** The I2 347-item FULL integration
run started 13:29:36Z; per the root sequencing decision (the I2 baseline
bug proved I2 cannot be the final I before the repair existed) it was
stopped gracefully at 13:57:10Z at ~48% (test_database_bootstrap);
wrapper-captured `G2_FULL_INTEGRATION_NATIVE_EXIT=143`; log and stop
record preserved (`/tmp/oap-083-5-c/final-I2-g2-full-integration.log`,
`g2-I2-stop-record.txt`); NO PASS is claimed for it; the fresh FULL gate
runs at I5.

## 7. Final gates at clean exact I = I5 `d88ceaa` (filled from actual runs)

### 7.1 ALL 31 standing commands IN ORDER (attempts at I1, I2, then final I5)

Attempt A (clean I1 `e7dcbd81` worktree, 12:57:45–13:03:41Z,
`/tmp/oap-083-5-c/final-I/manifest31.log`): all 31 native 0,
`ALL31_OVERALL_EXIT=0`. HARNESS METADATA DEFECT (disclosed, preserved):
the runner's `printf '%02d'` on string `08`/`09` interpreted octal, so
CMD 08 (control_api --check) and CMD 09 (editor_api --check) were LOGGED
as `CMD 00`; the per-command stdout logs for those two collapsed into a
single `cmd-00.log` (control's stdout overwritten by editor's). The
manifest/exits lines DO show distinct command texts with native 0 for
both; the unique original stdout for those two is lost. Not claimed
metadata-clean; not aggregated as the clean record.

Attempt B (clean I1, fixed v2 runner, 13:04:01–13:08:59Z,
`/tmp/oap-083-5-c/final-I-attempt2/manifest31.log`): all 31 native 0,
`ALL31_OVERALL_EXIT=0`, 31 unique per-command logs with correct decimal
labels (CMD 08 `control-api: CHECK_OK`, CMD 09 `editor-api: CHECK_OK`),
`SOURCE_HEAD=e7dcbd81… TREE=5bef78f9…`, `WORKTREE_DIRTY=0`.

Attempt C (clean I2 `38b519ca` worktree, 13:23:03–13:28:48Z,
`/tmp/oap-083-5-c/final-I2-all31/manifest31.log`): all 31 native 0,
`ALL31_OVERALL_EXIT=0`, `SOURCE_HEAD=38b519ca… TREE=47dd6198…`,
`WORKTREE_DIRTY=0`.

Attempt D (clean final I5 `d88ceaa` worktree, 14:20:09–14:25:57Z,
`/tmp/oap-083-5-c/final-I5-all31/manifest31.log`): all 31 native 0,
`ALL31_OVERALL_EXIT=0` at 14:25:57Z, `ALL31_RUNNER_EXIT=0`,
`SOURCE_HEAD=d88ceaa203848200a197af87fb19a42141bedde5
TREE=be28e7105e03174bfc634c596883555c2b27bb73`, `WORKTREE_DIRTY=0`.
Exit capture law: every command's immediate child exit captured directly
in bash (no pipeline/tail substitution); unique per-command log; v2 runner
decimal labels (`10#` forced). This is the clean final-I record.

| # | Command | Native child exit (A / B / C / D) |
| --- | --- | --- |
| 01 | uv lock --check | 0 / 0 / 0 / 0 |
| 02 | uv sync --frozen --all-groups | 0 / 0 / 0 / 0 |
| 03 | uv run --frozen ruff check services/backend tests/repository tools | 0 / 0 / 0 / 0 |
| 04 | uv run --frozen ruff format --check services/backend tests/repository tools | 0 / 0 / 0 / 0 |
| 05 | uv run --frozen mypy | 0 / 0 / 0 / 0 |
| 06 | uv run --frozen pytest services/backend/tests/unit tests/repository | 0 / 0 / 0 / 0 |
| 07 | uv build --out-dir /tmp/slaif-agent-site-distributions | 0 / 0 / 0 / 0 |
| 08 | python -m slaif_agent_site.control_api --check | 0 / 0 / 0 / 0 (A: labeled "00") |
| 09 | python -m slaif_agent_site.editor_api --check | 0 / 0 / 0 / 0 (A: labeled "00") |
| 10 | python -m slaif_agent_site.agent_api --check | 0 / 0 / 0 / 0 |
| 11 | python -m slaif_agent_site.render_api --check | 0 / 0 / 0 / 0 |
| 12 | python -m slaif_agent_site.mcp_adapter --check | 0 / 0 / 0 / 0 |
| 13 | python -m slaif_agent_site.media_service --check | 0 / 0 / 0 / 0 |
| 14 | python -m slaif_agent_site.review_worker --check | 0 / 0 / 0 / 0 |
| 15 | python -m slaif_agent_site.scheduler --check | 0 / 0 / 0 / 0 |
| 16 | python -m slaif_agent_site.media_gc --check | 0 / 0 / 0 / 0 |
| 17 | python -m slaif_agent_site.bootstrap --check | 0 / 0 / 0 / 0 |
| 18 | node --version | 0 / 0 / 0 / 0 |
| 19 | pnpm --version | 0 / 0 / 0 / 0 |
| 20 | pnpm install --frozen-lockfile | 0 / 0 / 0 / 0 |
| 21 | pnpm lint | 0 / 0 / 0 / 0 |
| 22 | pnpm format:check | 0 / 0 / 0 / 0 |
| 23 | pnpm typecheck | 0 / 0 / 0 / 0 |
| 24 | pnpm test | 0 / 0 / 0 / 0 |
| 25 | pnpm build | 0 / 0 / 0 / 0 |
| 26 | pnpm licenses list --json | 0 / 0 / 0 / 0 |
| 27 | python -m compileall -q tools tests/repository | 0 / 0 / 0 / 0 |
| 28 | python -m unittest discover -s tests/repository -p 'test_*.py' | 0 / 0 / 0 / 0 |
| 29 | python tools/check_repository.py | 0 / 0 / 0 / 0 |
| 30 | python tools/check_mermaid.py | 0 / 0 / 0 / 0 |
| 31 | npx --yes markdownlint-cli2@0.23.2 \*\*\*/\*.md | 0 / 0 / 0 / 0 |

Node 24.22.0 / pnpm 11.22.0; env-only PATH extension (worktree .venv/bin
after CMD 02) so bare `python` resolves the project environment — command
texts unchanged.

### 7.2 Fresh FULL UNFILTERED backend integration (SERIAL)

NOT QUALIFIED at I5 — partial interrupted attempt, honestly recorded:
`/tmp/oap-083-5-c/final-I5-g2-full-integration.log` (902 B, SHA-256
`aee19918637f8e66ecab214592fa36a7ee1bcbdbff9a0b516c0123162e7972e2`;
root receipt `strategic-I5-G2-interruption-independent-review.json`).
14:47:26–14:59:06Z, clean I5 worktree, real local PostgreSQL
(127.0.0.1:5432, `PGPASSWORD=qualification-admin`), exact unfiltered
command `uv run --frozen pytest services/backend/tests/integration`:
`collected 347 items`, then early systematic `.E` error glyphs from the
first module (test_agent_browser_http, test_agent_global_region,
test_agent_mutations), with runs of consecutive `E` near the stop point.
NO pytest final summary or tracebacks were emitted: the launch ignored
SIGINT (root /proc-verified `SigIgn` bit set), so per root sequencing the
owned pytest/uv children received TERM at 14:59:06Z and the wrapper
captured `G2_FULL_INTEGRATION_NATIVE_EXIT=143 2026-10-25T14:59:06Z`; all
three owned PIDs verified absent. Completed pass/error counts are UNKNOWN
(not inferred from progress glyphs). Error cause UNKNOWN. Primary-observed
concurrency (exact /proc evidence, NOT independently root-verified): a
separate process PID 3589951 (lstart 2026-10-25 14:48:04, cwd
`/home/janezp/codex-work/slaif-api-gateway`, argv
`/tmp/slaif192-coding-venv/bin/python -m pytest tests/browser/test_catalog_refresh_report.py tests/browser/test_admin_lazy_throttling.py -m playwright --junit-xml=/tmp/slaif193/browser-report-lazy2.xml -p no:cacheprovider -q`) was running in the same window, and
`pg_stat_activity` on the SAME local cluster (127.0.0.1:5432) showed
`slaif_test_*`/`fixture_*` disposable-fixture connections from client
172.17.0.1 at 14:48-14:5x with DBs created and dropped across checks; the
conftest lifecycle also drops cluster-global product roles per test. This
is consistent with shared-cluster fixture interference but is NOT proven as
the cause and NOT root-verified; no flake/benign label, no waiver. Two
orphaned disposable DBs (`slaif_test_0a125efe76`,
`slaif_test_17a26730d0`) remain on the shared cluster; no active
connections were observed at check time, but they are NOT proved inert —
role/dependency state could still contaminate the conftest
global-role teardown of later runs; left untouched while the cluster is
shared; mandatory cleanup/verification before any further qualification in
d. Distinct identity from the earlier I2 G2
interruption (13:57:10Z, native 143, ~48% reached, §6d) — both preserved.
RC7 coherent rollback sub-proof therefore NOT exercised at I5.

### 7.3 WHOLE literal `sh tools/compose/smoke.sh slaif0835`

ACTUAL at clean I5 worktree, 14:27:39–14:46:31Z (18 min 52 s),
`/tmp/oap-083-5-c/final-I5-g3-whole.log`:
`compose-smoke: OK`, `G3_WHOLE_NATIVE_EXIT=0` (immediate child exit;
setsid-detached, unique log, node on PATH). Fresh stack: policy OK,
down --volumes + build --pull + up --wait.

- `compose-e2e: OK projects=19` — setup=1, governance=1, preview=1,
  preview-filtering=1, stable-devices=6 (desktop chromium/firefox/webkit,
  tablet, mobile chromium/webkit), agent-sessions=2,
  agent-workspace-puck=2, freeze-review-snapshot=1, review-surface=1,
  accept-lifecycle=1, discard-lifecycle=1, media-publication=1,
  artifacts=disabled. 33 browser contracts PASSED, 0 FAILED.
- `frozen-review-parity-six-stable-pairings` PASSED
  `stage=phase=cleanup action=close elapsed=132176ms` — all six stable
  pairings inside the preserved 600s ceiling (this phase TIMED OUT at bS;
  cause still not attributed — it did not recur at I5, stage marker
  honestly scoped: stage-entry cumulative elapsed, not per-phase history).
- `media-publication` PASSED at I5 (the J2 CI console error did NOT
  reproduce; §6b history preserved, no flake/benign label).
- `browser-artifact-root-policy: OK retained-files=24 retained-pairs=12
  freeze-run=CANCELLED:0/1 fixture-map=fixed12plus-state-bound-freeze
  mode=0600 owner=10001` — the I5 state-bound repair exercised for real on
  a fresh volume: the unique `082 E2E freeze %` run reached terminal state
  CANCELLED, so the bound optional contributed 0/1 and the exact fixed-12
  expectation (N=24 files, screenshot=3) matched. The COMPLETED branch
  (0/1→1/1, N=26, screenshot=4) was exercised by the live-PostgreSQL
  validation and the 15-case dry-run matrix at I5 (§6d), not by this
  volume.
- Post-e2e security predicates all OK: `public-agent-news-edge` (exact
  listing, hostile uuid-token-flight-free html, canonical isolation),
  `public-agent-acceptance`, `public-agent-restart`/`-audit`,
  `media-e2e` (byte-identical, immutable-cache), `human-editor-envelope`,
  `governance-e2e` (devices=6), `edge-header-policy: OK page/api/404
  request-id-count=1 request-id-format=32hex csp-count=1`,
  `edge-body-limit: OK media=route-allowance non-media=413 global=1MiB`,
  `database-login-policy: OK public-connect=denied exact-roles=11`,
  `secret-file-policy: OK`, render/browser/browser-signing/browser-worker
  secret policies `files=1 mode=0400 owner=10001`,
  `browser-artifact-runtime-policy: OK files=36 retained=24 new=12
  mode=0600 links=1 credentials=absent`, `browser-artifact-revoked: OK
  status=401 bytes=absent`, `control-readiness-fixture: OK mount=isolated
  identity=exact failures=6 recovery=clean`, `governance-restart: OK`,
  nginx config test `Syntax OK`, packaging unit suite 49 tests OK.

### 7.4 Agent OpenAPI zero-diff

ACTUAL at clean I5 worktree, 14:28:22Z,
`/tmp/oap-083-5-c/final-I5-g4-openapi.log` (final attempt only; see below):
`uv run --frozen python -m tools.contracts.generate_agent_openapi --check`
→ `component-catalog: OK catalog-v1 Python/TypeScript semantic equality`,
`agent-openapi: OK contracts/openapi/agent-v1.json`,
`G4_OPENAPI_NATIVE_EXIT=0` (immediate child exit). HONEST ATTEMPT HISTORY:
two earlier attempts FAILED and were NOT claimed — attempt 1 (bare script
path `python tools/contracts/generate_agent_openapi.py --check`, exit 1,
`ModuleNotFoundError: No module named 'tools'`) and attempt 2 (module form
without node on PATH, exit 1, `FileNotFoundError: 'node'` in
component-catalog check). All three wrote the same log file, so the original
failed outputs were overwritten in place; root recovered them in
`/tmp/oap-083-5-c/strategic-I5-G4-original-tool-output-recovery.json`.
From this point on every attempt uses a unique filename.

### 7.5 Six-image qualification at J (bound history entry) and FRESH at I

**J-bound run: ACTUAL, PASSED, PIPELINE_NATIVE_EXIT=0** (local measured
six-image pipeline on J2 worktree, evidence files 11:18Z–11:41Z 2026-10-25;
log `/tmp/oap-083-5-c/supply-chain-c-qual-J2-run1.log`; evidence dir
`/tmp/oap-083-5-c/evidence-c-qual-J2`; evidence `revision`
`d161e9df4ade67a3bc83375a4124eb6e939b6608`; final log lines
`supply-chain-evidence: OK images=6 critical=0 high=19`,
`supply-chain-evidence-checksum: OK`, `supply-chain-gate: OK`). Per-image
zero unexcepted Critical; 19 High review findings (backend 1 zlib,
browser-worker 4, postgres 7, web 7 — all exactly matching the High
findings of the prior FAILED census/attempt, candidate ea586641 /
artifact 12593246129; no new High id relative to that census; not a
comparison against the prior successful candidate-8 bundle);
0 license/vulnerability exceptions; checksum validation PASS;
Grype 0.117.0 (b5fa92bb) / Syft 1.51.0 (2293641e) on fresh v6.1.10 database
(built 2026-10-25T06:27:34Z, checksum
`sha256:4bdb42924659936a80a73f5df039603dc01734ed6032575b9879745216a713ea`);
browser-worker runtime: image digest
`sha256:2ae551f1f1f2ff82fdb4aab23f45746e57edc7ccc6171609806f697e37be5586`,
executable `/ms-playwright/chromium-1706539/chrome-linux64/chrome`
SHA-256 `230f0db8c5086182f46c59c867c0d461eb525d6552dfad226ea6b4d9ec249db2`,
archive `e6c94490f0b6b337225aeb2d2a5034858516b7017356980ba94f5176d8774a50`;
1806 browser-worker matches (4H/1654M/134L/14N). All 31 original bS Critical
match IDs absent at every severity (measured replacements: chrome
156.0.8078.47; nginx 1.30.6-r1 + brotli-libs 1.2.1-r0; postgres
brotli-libs 1.2.1-r0; next 16.4.1). Root independently reviewed the local
bundle (`strategic-local-J2-independent-six-image-review.json`; source index
EXACT J2).

**Independent CI cross-check (actual identities, NOT relabeled J2/I):**
GitHub supply-chain evidence job 121153129092 (workflow run 40188115724,
J2 NEW-SOURCE run) artifact 12597008202 (zip 8945984 B, SHA-256
`6390cd2be4fb6af0a2babe0a57f15a9a50788bb4482b0ebcdedb5115fc3d35fb`, 53/53
checksums; all six raw scans 0 Critical / 0 exceptions; 19 High all exact
matches of the prior failed bS census/attempt, candidate ea586641) at
actual CI revision M=`be65db43a13917e19a7224b99ec0e8a9c59a1dd6`
(parents `4bf74fdc…` + J2 `d161e9df…`), whose committed tree
`08f3ab8f83026ef18c0076106b5451e0f7c3b1de` is identical to the J2 tree
(verified by primary `git fetch origin pull/107/merge`); root review JSONs
`strategic-J2-artifact-12597008202-*`. The candidate-9 matrix entry binds the
ONE consistent LOCAL J2 bundle; the CI M image set (e.g. browser-worker image
`sha256:1389fbfa…`) is a separate cross-check and its IDs are never mixed
into the entry.

**I-bound fresh run: NOT RUN at I5** — per root sequencing
(2026-10-25 ~15:00Z) no further expensive final qualification launches
under c: the I-bound fresh six-image pipeline (final images/labels/
artifacts bind to I, not guessed equal to J2) is deferred to the
prospective bounded d, which also carries the CI PG-matrix repair.
Preserved pretest/partial history:
local-revision pretest reap-killed mid `next build` (log
`supply-chain-c-qual-run1.log`, partial evidence `evidence-c-qual-partial-run1/`
preserved; session-reap kill, NOT a pipeline failure) and the earlier
`pnpm: not found` PATH failure (`supply-chain-c-run1.log`,
`evidence-c-run1/` preserved).

### 7.6 I5 NEW-SOURCE CI terminal state (run 40201731140, head `d88ceaa`)

TERMINAL: 17 SUCCESS / 3 CANCELLED — the repeated PG14/15/18 cancellation
pattern (bS, J2, I2, now I5) at the 15-minute job maximum:
`Foundation PostgreSQL 14` job 121194240869 CANCELLED
(14:20:27→14:35:42Z), `Foundation PostgreSQL 15` job 121194241062
CANCELLED (14:20:28→14:35:30Z), `Foundation PostgreSQL 18` job
121194241050 CANCELLED (14:20:28→14:35:37Z); PG16 121194241049 and PG17
121194240988 SUCCESS; `Compose and edge packaging` 121194240722 SUCCESS
(14:20:27→14:37:07Z) and `Supply-chain evidence` 121194240928 SUCCESS
(14:20:28→14:32:16Z); CodeQL, Node contracts, Python 3.12/3.13/3.14,
Repository policy, Mermaid, Markdown, Dependency review, Detect supported
languages, and all three Analyze jobs SUCCESS. Underlying slowdown of the
cancelled PG jobs remains UNKNOWN (no flake claim). Per-run root-verified
figures, NOT generalized: bS original five PG logs each show exactly 130
selected passes before the teardown boundary (4+81+24+9+12, root
re-verified); J2 PG14/15 show 130 each; the I2 PG14 original log shows
only 118 selected passes with the final-12 summary line ABSENT.
Workflow/timeout repair is EXPLICITLY OUT OF SCOPE for c; root plans a
bounded d CI repair with all original acceptance carried forward; no claim
that a future S cannot vary.

## 8. Carried focused evidence (b-era, scoped identities preserved)

All runs SERIAL, real PostgreSQL where marked; `NATIVE_EXIT` = captured
immediate child exit; source identities in `/tmp/oap-083-5-b/` sidecars.

| ID | Case / scope | Source | Result |
| --- | --- | --- | --- |
| RC1 original | `test_rc1_public_agent_and_editor_capture_retained_families` (public+Editor all-family capture, typed field closure, numeric approval via qualified composition-only workspace) | `rc1-focused-run18.log` @ `866830bbf0edc8a4` | 2 PASS 35.77s (17 collected / 15 deselected) NATIVE_EXIT=0 (count re-verified from the actual log) |
| RC1 post-md5-fix | same case rerun after the b legacy-md5 test repair | `50b799bb…` (b I pre-report) | 1 PASS 18.57s (19 deselected) NATIVE_EXIT=0 — SEPARATE identity from run18; the numeric-approval case was NOT re-executed by this one-case rerun (no vacuous re-credit) |
| G10/G11 | `test_query_candidate_bound_admitted_real_surfaces` (1000 positive / 1001 query-cost refusal, live ACTIVE preview + frozen, full effects, canonical/accepted/session oracles) + `test_sibling_mismatch_recomputed_digest_admission_refusal` (real trusted-SQL sibling mismatch) | `parity-focused-run7.log` @ `649e999f439b2408` | 2 PASS 41.41s (6 deselected) NATIVE_EXIT=0 |
| RC8 | `test_rc8_captured_chain_raw_depth_and_byte_budget_wiring` (raw depth 7/8 capture, depth-9 real worker refusal + no-effects, STRICTER-N wiring, production 8 MiB N-1/N/N+1 owner-hostile copies, narrow real-SQL value_cost boundary, normalized per-node facts) | `rc8-capture-focused-run5.log` @ `a82be261aca7c697` | 1 PASS 39.03s (8 deselected) NATIVE_EXIT=0; run3 pad + run4 polymorphic-SQL failures preserved as history |
| Media | `test_media_service.py::test_private_media_bytes_human_preview_bound_worker_frozen_review` — real PG/HTTP ASGI with signed/claimed bound credential (NOT the deployed worker); deployed-worker proof is the public run5 below; both kinds preserved | `media-focused-run1.log` | 1 PASS 138.22s (1 deselected) NATIVE_EXIT=0; root-verified native event 36585 at 2026-10-25T02:59:37.220Z |
| Hostile E-D3 | media-reference-row tamper full matrix | `hostile-run4.log` @ `1ac8db18e72613fe` | 1 PASS 20.30s (19 deselected) NATIVE_EXIT=0 |
| G13 | stored-digest co-tamper refusal | `hostile-run5.log` @ `fcf4ffaa7843ad2a` | 1 PASS 13.77s (10 deselected) NATIVE_EXIT=0 |
| Hostile 6 | freeze/accept wrapper matrix | `hostile-run6` first launch 3 PASS 45.71s (17 deselected) NATIVE EXIT NOT CAPTURED (semicolon-join caveat preserved); second launch | 1 PASS 13.62s NATIVE_EXIT=0 |
| Public e2e | `frozen-review-parity.spec.ts` scoped browser run (current source 831cd2d3/2584L) — ALL6 canonical/preview/review, both locale directions, deployed TS worker BOTH private hashes, W2, terminal 14-column invariance, same completed runId | `e2e-parity-run5` 2026-10-25 07:02:56.90179929Z–07:05:57.845334911Z | NATIVE_EXIT=0 (log 216B SHA `c579d2c6…` preserved) — focused pre-new-I evidence; final new-image whole smoke still mandatory |
| Media v2 focused single (c era) | `media-publication` single project on the LIVE J2 stack, v2 diagnostic source + qualified demo HUMAN editor-workspace prerequisite (original resolver mechanism) | `media-v2-focused-124809.log` @ `2788273f55d1…` | PASSED, `MEDIA_V2_FOCUSED_NATIVE_EXIT=0` 12:48:36Z — focused pretest, NOT final-gate credit |
| Media v2 fresh seq (c era) | FRESH J2 volume: setup + parity seed + preview (8) + preview-filtering + demo HUMAN-workspace prerequisite (HTTP 200/200, DB-verified) + media-publication | `focused-media-seq-124938.log` @ `2788273f55d1…` | all PASSED, `FOCUSED_MEDIA_SEQ_NATIVE_EXIT=0` 12:51:28Z — the J2 CI console error did NOT reproduce locally; cause remains UNKNOWN, no flake/benign label |
| final-31 | partial ALL31 at clean candidate-I checkout (b) | `final31/manifest31.log` | attempt 2: CMD 01-20 EXIT=0 before ROOT-directed stop at CMD 21 (`pnpm lint` running); attempt 1 died on exec-session reap after CMD 04 (preserved); METADATA CAVEAT: `printf '%02d'` octal printed CMD 08/09 as "CMD 00" — command texts/exits real; NO all-31-pass claim |

These remain SCOPED focused evidence. No aggregation as FULL; the final
clean-I gates (§7) are the required qualification.

## 9. Size / path forecast, actuals and variances

Uniform inventory algorithm (`/tmp/oap-083-5-b/strategic_inventory.py`,
explicit minimal diff vs base `4bf74fdc`, tracked + untracked-once):

| Checkpoint | production | tests | prod+tests | docs | transcript | ceiling |
| --- | --- | --- | --- | --- | --- | --- |
| b activation actual (root-corrected) | 10731/33 paths | 20849/30 paths | 31580 | — | — | 32000→33000 (c) |
| J1 working tree (root inventory 10:53:45Z) | 10922/41 paths | 21026/32 paths | 31948 | 150/12 | 1612/6 | 33000 |
| J2 HEAD `d161e9df` (primary, canonical minimal algorithm matching root tool; `/tmp/oap-083-5-c/primary-J2-inventory-20261025.json`) | 10940/42 paths | 21109/34 paths | **32049** | 150/12 | 1612/6 | 33000 (headroom 951) |
| pre-I worktree (J2 + candidate-9 matrix +57, test_policy restructure, SUPPLY_CHAIN current-line; `/tmp/oap-083-5-c/primary-preI-worktree-inventory.json`, 2026-10-25 ~12:05Z) | 10997/43 paths | 21177/34 paths | **32174** | 155/12 | 1612/6 | 33000 (headroom 826) |
| post-media-v2 worktree (primary, uniform minimal-diff inventory, 2026-10-25T12:50:12Z; `/tmp/oap-083-5-c/primary-postMediaV2-worktree-inventory.json`) | 10997/43 paths | 21285/34 paths | **32282** | 155/12 | 1612/6 | 33000 (headroom 718) |
| I2 (clean worktree inventory 2026-10-25 ~13:25Z) | 11017/43 paths | 21285/34 paths | **32302** | 155/12 | 1612/6 | 33000 (headroom 698) |
| I3 `d51902d` (committed, uniform minimal-diff vs base + full c map, 2026-10-25 14:04Z) | 11049/43 paths | 21285/34 paths | **32334** | 155/12 | 1612/6 | 33000 (headroom 666) |
| I4 `f96bddb` (committed, same algorithm, 2026-10-25 14:14Z) | 11057/43 paths | 21285/34 paths | **32340** | 155/12 | 1612/6 | 33000 (headroom 660) |
| I5 `d88ceaa` (FINAL I, committed, same algorithm, 2026-10-25 14:20Z) | 11063/43 paths | 21285/34 paths | **32348** | 155/12 | 1612/6 | 33000 (headroom 652) |

Full base→final-I recomputation (not a sum of round deltas): the 33000
ceiling counts ONLY production+tests gross (docs/transcript are separate
named-identity allowances: 12 docs, 7 transcripts; root clarification
2026-10-25 ~12:10Z, FULL 44/34/12/7 path-classification artifact from the
original c order + 82L decision governs — the matrix was always a named c
production path; its absence from the J2 actual inventory only reflects its
zero diff at J2). Pre-I worktree actual was 32174 (production 10997 incl. the
+57 candidate-9 matrix entry, tests 21177); the media diagnostic patch
landed at its upper estimate (+108 gross, actual 21285 tests) → post-media-v2
worktree actual **32282** (measured, not concatenated). Remaining open
buckets: other concrete final-gate repairs 0..100 → projected I
32282..32382 under the unchanged 33000 (headroom ≥618); a 0..200
minimal-media-repair bucket would apply only at a NEW I if the final WHOLE
gate reproduces the J2 console error (no such repair is currently known or
planned). The already-delivered J2 buckets (pin
literals 4, formatter/smoke 4..20, preview-props normalization+tests
40..150) are inside the J2 actual. Whole-file
line counts are identity metadata only, never diff gross. Docs 150 exceeds
the earlier 124..132 estimate (estimate variance, recorded; docs gross is not
a hard cap; no additional doc identities beyond the same 12). No crossing of
33000 is projected; any actual crossing would require a recorded prospective
decision first (none needed as of this report).

## 10. b-report corrections (authoritative record; b report itself IMMUTABLE)

Root source review of the published 226-line b report identified eight
evidence-map errors. The b report is preserved byte-exact (never edited);
these corrections govern this c report and any follow-up:

1. RC1 is TWO distinct identities: run18 @ `866830bb` (2 PASS 35.77s/0) AND
   the post-md5-fix one-case rerun @ `50b799bb` (1 PASS 18.57s/0). The
   numeric-approval case was NOT re-executed by the one-case rerun; no
   re-credit.
2. RC2: the Oct-25 `e2e-parity-run5` (07:02:56.90179929Z–07:05:57.845334911Z,
   native 0, source 831cd2d3/2584L) ACTUALLY passed — ALL6 + both locale
   directions + deployed worker BOTH private hashes + W2 + terminal
   14-column invariance — focused pre-new-I evidence.
3. RC3/5/6/7: the b counterfactuals, genuine 075 legacy and coherent RC7
   v2-FIRST refusal then SEPARATE v1-only restore are b qualifications
   correcting a defect — NOT a/old-20-green proof (a20 success was report
   S `dbfaadc2`, not automatically I `565c99c`).
4. RC4: `test_media_service` = real PG/HTTP ASGI with signed credential, NOT
   the deployed BrowserAttemptExecutor; deployed-worker proof = Oct-25
   public run5; both kinds preserved.
5. RC8: conditional tight-arguments only — no universal
   guard-unreachable, no impossible 8 MiB-max criterion, run5/`a82be261`
   accurately scoped, no worker-firing claim; F1/F2 reachability terms OPEN.
6. First b path omitted `/preview/` (actual
   `apps/web/app/preview/[workspaceId]/[[...sitePath]]/route.tsx`); named
   bounds were 34 production/30 tests, not 26/28.
7. nginx 2 matches = ONE nginx CVE-2026-15176 + ONE brotli CVE-2026-111497;
   31 are matches, not 31 unique CVEs; mode is AMEND_EXISTING_PR.
8. Piped-tail summaries are NOT captured child 0; no invented cause for the
   exec death or PG slowdown; 078-u was `153.0.8010.36` (PR #80), the
   separate 155.0.8059.84 qualification is 083-3/PR #102 candidate-8 — the
   false 155→078-u attribution in J1 docs came from root steering and is
   corrected in this round's docs.

## 11. Limitations and strongest reason not to merge

Limitations, honestly scoped:

1. No measured result in this report is a final acceptance: every gate is
   labeled pass/fail/not-run at the identity actually executed, and the
   final clean-I gates (§7) plus all 20 named required checks at CURRENT S
   are the required qualification. Focused passes remain scoped; no
   aggregation as FULL.
2. The bS six-image scan (31 Critical matches) is original evidence of the
   known-failing state; the J2-bound qualification (§7.5) and the fresh
   I-bound pipeline are the forward proofs. Old image/scan results do not
   become current proof.
3. Stage-instrumentation `elapsed` is stage-ENTRY cumulative, not
   per-phase history. The bS compose-parity 600s timeout did NOT recur at
   the I5 WHOLE run (six pairings completed in 132.2s, §7.3); the timeout
   cause therefore remains UNKNOWN and unattributed — the I5 pass is
   evidence the phase completes at I5, not a root-cause finding.
4. PG14/15/18 CANCELLED at the 15-minute maximum at bS, J2, I2 AND I5
   (run 40201731140 jobs 121194240869/121194241062/121194241050, §7.6)
   retain UNKNOWN underlying slowdown (no flake claim; per-run figures as
   recorded in §7.6: bS 130 each, J2 PG14/15 130 each, I2 PG14 118 with
   the final-12 summary line absent); workflow repair is out of c scope
   (prospective d); no claim that a future S cannot vary.
5. Local worktree `pnpm lint`/`check_repository.py` failures caused by the
   untracked human `.codex/` plugin cache are host artifacts (root-verified
   cause); the exact-31 gates run at clean committed I/I checkouts that
   exclude only `.codex/`, `CODEX-SESSIONS.md`, `codex.sh`.
6. RC8 F1/F2 reachability terms remain OPEN conditional arguments (no
   universal guard-unreachable claim); the withdrawn huge-profile/
   oversized-version fixtures remain withdrawn.
7. The J2 history entry records the J2-bound run only; the final images/
   labels/artifacts bind to I, not guessed equal to J2.
8. The J2 CI `media-publication` console-error cause remains UNKNOWN: it did
   not reproduce in the focused lane with the v2 diagnostic source and
   complete fixture setup (§6b), nor at the I5 WHOLE run (media-publication
   PASSED, §7.3); the fixture 404 seen locally was a distinct,
   DB-qualified missing-demo-HUMAN-workspace prerequisite (original resolver
   mechanism), not the CI cause. No flake/benign label, no unknown-error
   allowance.
9. G2 fresh FULL at I5 is UNQUALIFIED: the only attempt was partially
   interrupted (347 collected; early systematic `.E` error glyphs; no
   final summary/tracebacks; native 143, §7.2). Error cause UNKNOWN; a
   concurrent disposable-fixture pipeline from a separate session on the
   same local cluster is primary-observed (exact PID/time/cwd/argv in
   §7.2; not independently root-verified) but not proven as the cause. The
   RC7 coherent rollback sub-proof was not exercised at I5.
10. Two orphaned disposable DBs from the interrupted activity remain on
    the SHARED local cluster; no active connections were observed at check
    time, but they are NOT proved inert (role/dependency state could
    contaminate conftest global-role teardown); left untouched while the
    cluster is shared; cleanup/verification is mandatory before further
    qualification in d.
11. `docs/user-manual/README.md` (new Review Page section) contains two
    passages contradicted by or beyond this increment's delivered
    behavior: (a) the statement that after acceptance/discard the page no
    longer resolves, while the current E2E terminal retained-page/bytes
    proof (`frozen-review-parity.spec.ts` lines 2561..2615, current
    source) proves the retained frozen page, controls and BOTH bytes
    survive a real discard; (b) the "drift blocks until re-freeze"
    remedy, although re-review/re-freeze is not delivered in this
    increment. Additionally the same misleading review-banner wording
    pre-exists in the route source and is asserted by
    `accept-lifecycle.spec.ts:688`, which is NOT a currently named test
    path. Per root direction NO manual/banner/test edit is made in c;
    the correction (truthful retained-history wording, honest current
    limitation) and the banner reconciliation (only under a complete
    bounded forecast adding the exact names first) are carried to the
    prospective bounded d. No assertion removed or weakened.
12. Known downstream limitation (089/091 territory, recorded per
    root's secondary source observation): the pre-existing
    cancel-after-publish path can orphan private bytes; the current I5
    guard DETECTS such state, it does not PREVENT it. No new GC scope
    added here; no universal orphan-free claim is made.

Strongest reason not to merge (as of this PARTIAL report): c did not
complete its closure at one clean committed identity. At final I5
`d88ceaa`: ALL31 (§7.1), WHOLE (§7.3) and OpenAPI (§7.4) PASSED, but the
fresh FULL unfiltered integration with coherent RC7 (§7.2) is unqualified
(partial interrupted run, cause unknown), the FRESH six-image pipeline at
I (§7.5) was NOT RUN (deferred to d), and I5 CI is terminal
17 SUCCESS / 3 CANCELLED (§7.6) — the current I5 terminal state
blocks c acceptance; the repeated PG14/15/18 15-minute cancellations and
the out-of-scope workflow repair are the reason, with no claim that a
future S under d cannot vary. The user-manual correction
and banner reconciliation remain pending (§11.11). Until the prospective
bounded d (CI repair + truthful doc follow-up + the remaining local
gates) completes all original acceptance at one clean committed identity
and all 20 named required checks at CURRENT S are verified SUCCESS on
remote, this PR must not be accepted or merged. All original criteria
carry forward; none is waived.

## 12. Confirmations

- Mode AMEND_EXISTING_PR; PR #107 only; NO new PR, NO merge, NO
  auto-merge, NO close, NO next-ID selection.
- b report `3b664b35`/file `f7588f63…` IMMUTABLE — not edited, amended,
  retracted or replaced; corrections recorded only here.
- No workflow/timeout/retry/security/coverage/quota guard weakening; no
  exception added (exception sets remain empty); no suppression/dismissal;
  no old-migration edit; no Sharp/libvips/optimizer/hosted dependency.
- No unchanged-head CI rerun; J2/I new-source checks are new evidence only.
- No secrets/capabilities/cookies/DB URLs/private artifact URLs in any
  committed path; preview crypto values are normalized and never logged.
- All pretests, partial runs, rejected attempts and failures preserved
  with native exits/source hashes (§4.1, §6, §6a, §7.5, §8).
- J2 GitHub TERMINAL (run 40188115724): 17 SUCCESS / 1 FAILURE
  (Compose media-publication, §6a) / 2 CANCELLED (PG14 121153129031, PG15
  121153129065, 15m maximum; 130 selected passes each before teardown) —
  NOT final S acceptance; root independently waits for all 20 at CURRENT S.
  CI supply-chain artifact 12597008202 at revision M (tree == J2 tree)
  independently root-qualified (§7.5).
- I5 GitHub TERMINAL (run 40201731140, head `d88ceaa`): 17 SUCCESS /
  3 CANCELLED (PG14 121194240869, PG15 121194241062, PG18 121194241050,
  15-minute maximum; underlying slowdown UNKNOWN, no flake claim;
  per-run selected-pass figures in §7.6; the current terminal state
  blocks c acceptance; no claim that a future S under d cannot vary;
  workflow repair is out of c scope (prospective d).
- G2 fresh FULL at I5: ONE partial interrupted attempt only
  (14:47:26–14:59:06Z, 347 collected, early systematic `.E` glyphs, NO
  final summary, `G2_FULL_INTEGRATION_NATIVE_EXIT=143`, log 902 B SHA
  `aee19918…` root-receipted; error cause UNKNOWN; §7.2). No second
  attempt launched per root sequencing; no pass claim.
- User-manual Review Page correction and review-banner reconciliation
  (incl. non-named `accept-lifecycle.spec.ts:688`): NOT edited in c;
  recorded as pending d follow-up with the honest retained-history
  wording and delivered-lifecycle limitation (§11.11). No assertion
  removed or weakened.
- No source, test, doc, workflow, pin, guard or cap change after final
  I5 `d88ceaa`; no further qualification launches after the root
  strategic sequencing (2026-10-25 ~15:00Z); this c handoff is
  PARTIAL with every original criterion carried forward to d.
- Media diagnostic lane (§6b): approved v2 patch `e06717da…` applied
  byte-exact (spec `2788273f…`, 2178L); applied-source statics tsc/eslint/
  prettier native 0; focused runs with complete fixture setup PASSED native 0
  (`media-v2-focused-124809.log`, `focused-media-seq-124938.log`); failed
  baseline/setup/spawn attempts preserved (122624 fixture 404, 122011
  governance local variance, run1 harness defect, spawn 124706); no product
  auth/migration/404 change, no test weakening, no unknown-error allowance;
  credential-bearing trace/cookie artifacts kept 0600 outside git, never
  published.
- Smoke-baseline repair commits I3 `d51902d` / I4 `f96bddb` / I5
  `d88ceaa` are each preserved as distinct linear commits on PR #107
  (no amend, no rewrite); root-reviewed defects were fixed forward-only;
  all local dry-run matrices, live-PostgreSQL validations, failed CI
  originals and interrupted runs are preserved with native exits.
- Report publication commit SELF: sole new path
  `oap/reports/083-5-c-close-security-and-final-gates.md`, first parent
  exactly literal I (`d88ceaa…`); verified remote bytes before the
  single exact 2-byte OK to the strategic response FIFO; no repo
  mutation after S.

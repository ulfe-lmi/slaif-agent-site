# OAP 083-5-f execution report — correct qualified evidence without product changes

## 0. Identity and status

- ID: 083-5-f (REPORT_CORRECTION_ONLY, CLOSURE_ONLY)
- PR mode: AMENDED_EXISTING_PR — PR #107
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/107>, branch
  `oap/083-5-a-faithful-frozen-review`, NO NEW PR
- Status: COMPLETE (correction deliverable finished; the final fS SELF checks
  are honestly recorded as in-flight/pending at the publication instant in
  section 6 — root independently waits and requires fresh S all-30)
- Base: remote main `4bf74fdc8e74323045a7f8830cf393493e75fe0d` (verified
  unchanged before and during this round)
- Starting remote eS: `af41e747832d2cd9a1d9aaf537db8ccb179daaaa` (sole added
  path: the e report; first parent literal I
  `24a4333569be6f2201f94c07be56d702cb1a33da`, tree
  `e59de814afd7a334f9e37c482961fc4b1962a7c6`)
- Literal J (pre-report commit): `57b91d8d88f36b7967fa2c6b92b9df2420886462`
- Report publication commit: SELF
- Pushed commits this round: J (f order + active, sole change set), then this
  report-only SELF commit (sole path, first/only parent J)

## 1. What this round does (and does not do)

- Corrects ONLY, in this NEW f report, the seven explicit evidence-map
  errors/overclaims (C1–C7) that root identified in the immutable e report.
  No a/b/c/d/e report or order is edited anywhere; historical bytes are
  preserved (section 5).
- Zero changes to product code, migrations, tests, generated contracts,
  dependency locks, workflows, policies, or docs (including
  `oap/MVP-CONTRACT-AUDIT.md` and `oap/MVP-PROGRESS.md`).
- No runtime pipeline of any kind was re-run. Root's prospective gate-carry
  exception (f order, "Narrow prospective gate carry and permitted changes")
  applies because J is byte-identical to tested I24a on every
  product/test/doc path: I24a's qualified local G1 / G2+RC7 / G3 / G4 / G5
  are CARRIED as product evidence at J. Nothing in this report claims those
  commands ran at J or fS; every one is explicitly labeled carried.
- This is not a new semantic family, a reduced product contract, numeric 083/
  MVP/product/release completion, or a release. All original R1–R9 / A–F /
  RC1–RC9 / security / D1 / D2 / e product acceptance remains FULL.

## 2. Incorporated immutable e report (complete inherited evidence index)

- Exact path: `oap/reports/083-5-e-restore-postgres-overlay-and-final-gates.md`
- eS: `af41e747832d2cd9a1d9aaf537db8ccb179daaaa` (remote-verified; root
  scratch copy `/tmp/oap-083-5-e/strategic-e-report-remote-verified.md`)
- Size/identity: 1280 lines / 84885 bytes / SHA-256
  `3f847e25bbdfc42a766ea0ae7bfdae80eeb9cf840ca0dd8a0e5d16fed3e6ddd3`
- The complete inherited evidence index (per-criterion anchors for R1–R9 /
  A–F / RC1–RC9 / security / D1 / D2 / e) is that report, sections 3–10,
  incorporated here by exact path/S/SHA rather than mechanically recopied.
- All original criteria remain as indexed there, with the corrections in
  section 3 prevailing at the cited e lines. Every e claim NOT corrected here
  remains a claim subject to root independent review; this supplement neither
  re-qualifies nor relabels any of them.

## 3. Corrections C1–C7 (dispositions, each verified against actual objects)

### C1 — RC1 focused-run identity conflation (e lines 713–714 and 947–949)

- e said (713–714): "b-era focused `rc1-focused-run18.log` @
  `866830bbf0edc8a4` 1 PASS 18.57s NATIVE_EXIT=0 (original run18 2 PASS
  35.77s pre-md5-fix preserved)"; 947–949 repeated the attribution and added
  "`test_rc1_numeric_approval_composition_only_workspace` PASS in the same
  log".
- Corrected — TWO distinct runs, never conflated:
  - `rc1-focused-run18.log` (897 B, log SHA-256
    `288705609eab785997d78e6023fa347c140c9c3adde6f5de7bcd9d95aac5246c`) at
    source `866830bbf0edc8a4cfb03d43c14f5e4392bdebf117e735f94f3abbee1cb81f84`
    (receipt `rc1-run18-independent-native-and-source-verification-2026-10-25.json`):
    **2 passed**, 15 deselected, 35.77 s, NATIVE_EXIT=0 — BOTH
    `test_rc1_public_agent_and_editor_capture_retained_families` and
    `test_rc1_numeric_approval_composition_only_workspace`.
  - `rc1-md5-fix-focused-run1.log` (763 B, log SHA-256
    `6eb620b66e1370105e390211a69b76946052ea7f58955fa8f2ecc141a3d4b617`) at
    source `50b799bb7193c1f6643a4c55394dc1305250c49d2f623da8d01ed9cec2098cd3`
    (file SHA of `services/backend/tests/integration/test_freeze_review_snapshot.py`):
    **1 passed** (the capture-retained-families case only), 19 deselected,
    18.57 s, NATIVE_EXIT=0.
- The current-I qualification is separate from history: the fresh full G2 -rA
  at 24a passed BOTH RC1 cases (e section 9.7). That current qualification is
  restated unchanged in section 4; the historical b-era log identities above
  replace the conflated e statements.

### C2 — 8 MiB bound claims repeated while F1/F2 remain open (e lines 812, 999)

- e said (both lines): "lawful upper < 8 MiB; guard unreachable from
  constraint-compliant inputs as defense-in-depth; F1/F2 reachability terms
  kept OPEN". The explicit c corrections already forbid repeating the
  universal lawful-upper/unreachable form while the terms are open.
- Corrected — finite admitted-work evidence, stated precisely (verified at I
  from `076_001_faithful_frozen_review.py` per the b-era primary audit
  `rc8-8mib-audit-primary-review-2026-10-25.md`): 13 family row pools with
  per-row value_cost budgets summing to 5,308,416 B; per-page pre-bound of
  128 rows AND `sum(to_jsonb(c)) <= 262,144`; composition total cap 131,072;
  media inventory cap 4,096 entries; final gate
  `slaif_review_value_cost(doc, 0, 8388608) < 0` RAISEs the total canonical
  payload budget; `version_facts` must equal the exact six-pin literal
  (measured 178 B) BEFORE any content read, both fail closed.
- Open conservative terms: F1 (+3 B worst-case per numeric-leaf repr growth)
  and F2 (timestamptz <= 34 B) remain OPEN. Any tight-maximum or guard-
  unreachability argument is therefore CONDITIONAL on those unresolved terms;
  this round makes no unconditional unreachability claim.
- No new maximal 8 MiB worker fixture, per-cap matrix, quota/timeout change,
  or new test requirement is introduced or implied by this correction.

### C3 — universal no-host-port container claim (e line 569)

- e said: "No owned e container ever bound a host port."
- Corrected — narrowed to the actual contexts: the isolated G2 PG/runner
  docker context (owned PostgreSQL only, exposed at 127.0.0.1:5432 INSIDE
  that context; runner container on the same private network) bound NO host
  port. The G3 approved demo NGINX of the compose `slaif0835` stack DID
  publish a host port (localhost:8080) — the approved packaging edge (only
  NGINX publishes a host port) — and ALL G3 live HTTP/browser traffic went
  through that NGINX edge. The older owned 55443 dedicated-cluster context is
  decommissioned (leftover metadata preserved, e section 5.3).
- No false universal-container claim is made; network/security authority is
  unchanged.

### C4 — "both edge headers verified" (e line 461)

- e said: "Both edge headers verified (nginx public edge in all
  e2e/acceptance phases; the 404 + header policy asserted against the edge)."
- Corrected — the literal WHOLE at I establishes live HTTP/browser flows via
  the NGINX edge (all e2e/acceptance traffic over localhost:8080; 404 +
  header policy asserted against it). The Apache side in that run supplied
  build/configuration checks only: `apachectl -t` `Syntax OK` (executed in
  the Apache image build stage) and `nginx -t` `Syntax OK` — both are edge
  CONFIGURATION checks, NOT live Apache HTTP parity. e section 6 (lines
  397–400) already states this correctly; the line-461 summary overstated it,
  and the corrected distinction now applies at every occurrence in this
  report.
- The full Apache HTTP adapter contract remains a final-MVP qualification
  gap (section 7). No new Apache runtime/test work is ordered by this
  correction and no waiver of the original finite smoke is granted.

### C5 — stale name count in the footprint (e line 1223)

- e said: "32868 gross prod+tests / 43+34 names, docs 164/12, unknown 0".
- Corrected (root-measured uniform minimal base-to-I footprint): **11179
  production bytes / 45 paths + 21689 test bytes / 36 paths = 32868 GROSS**
  (production+tests), docs 164/12 separate, unknown 0. The 43+34 name count
  was stale; the measured actual is 45+36 named paths. The allowed maximum is
  46 production (includes the unused reserved preview page); actual is 45.
  Tests are at the maximum: 36/36. The historical variance is preserved as a
  recorded discrepancy, not silently erased (section 7).

### C6 — d-G1 command-start timestamp and d-G4 log-header claim (e lines 1113, 1124)

- e said (1113): "16:14:14→16:19:26Z" presented as the command span; e said
  (1124): d G4 "actual child 0, exact command in log header".
- Corrected:
  - d G1 (final 43cd attempt, `manifest31.log` line 1): 16:14:14 was the
    wrapper/launch instant; the FIRST command (`uv lock --check`) actually
    started at **16:14:20.482563532Z**. The end instant 16:19:26Z stands.
  - d G4: the log (`openapi-check.log`) is a RESULT-ONLY log — two result
    lines (`component-catalog: OK ...`, `agent-openapi: OK ...`) and no
    command header. e section 6 G4 (lines 468–477) already says correctly
    "no command header is claimed inside the log — the call/output supplies
    the argv"; line 1124 contradicted it. The consistent corrected statement:
    argv and native child 0 are proven by the executor function-call record
    (immediate child capture), not by any log header.
- The corrected distinction is applied consistently everywhere in this report
  (no second occurrence of either error).

### C7 — out-of-range `review-page.ts` anchor (e line 783)

- e said: "web legacy view `sites/review-page.ts:253-262`" — the current-I
  file `apps/web/src/sites/review-page.ts` is 151 lines; 253–262 does not
  exist in it.
- Corrected — actual current-I anchors (verified against the I tree):
  - `apps/web/src/sites/review-page.ts:130-138` — the `faithfulProjection`
    gate: `document.snapshot.state_version === REVIEW_STATE_VERSION_V2`
    selects the v2 faithful frozen read (else `null`).
  - `apps/web/src/sites/review-page.ts:139-141` — the selector contract
    comment: "The stored snapshot state version is the single view selector
    (v2 faithful frozen read with no v1 fallback on refusal, v1 legacy
    web-side projection, unknown stored values refused)".
  - `apps/web/src/sites/review-page.ts:142` —
    `selectReviewView(document, faithfulProjection, workspaceId, path)`;
    uniform not_found/refusal handling at 143.
  - The v1 reader anchor `apps/web/src/sites/review-projection.ts:905`
    (`projectionFromReviewDocument`; 1138-line file) remains valid at I.
- Every other anchor/count newly cited in this f report was re-checked
  against the actual I objects (files/lines above; b-era logs; d-era
  manifest/log). No new full-set Medium/Low scan, whole-14-column digest,
  indefinite-retention, generic-publication, or release claim is made. Root/
  helper receipts corroborate but are not independent product execution.

## 4. I24a gate receipts — CARRIED from literal I (not re-run at J or fS)

All five entries below were qualified at literal I
`24a4333569be6f2201f94c07be56d702cb1a33da` (e section 6) with root-
independent receipts; they are carried into J by the exact tree equivalence
of section 5 under root's prospective exception. None was re-run in this
round, and none is claimed to have run at J or fS.

- G1 ALL31 (31 commands in order): qualified at I — 31/31 EXIT=0,
  `ALL31_OVERALL_EXIT=0`, 17:14:28→17:20:22Z, manifest SHA-256
  `4c1335d7c56b14a4fe00ef8748607d972c82dca04f2c59a593024f05839e73b2`; the
  manifest timestamp monotonicity was root-adjudicated (uutils date `%6N`
  variable-width fractions; left-pad 9 ⇒ strictly monotonic; raw manifest
  never rewritten) — receipts `strategic-G1-fraction-format-adjudication.json`
  and `strategic-current-date-fraction-format-probe.json`. CARRIED, not re-run.
- G2 FULL unfiltered 347 (isolated owned context, 127.0.0.1:5432 = owned PG
  only): qualified at I — 347 passed / 0 fail-error-skip, 3688.19 s,
  `G2_CHILD_EXIT=0`, 17:21:44Z.062→18:23:16Z.822, log SHA-256
  `e84be97bbc31ca63bec5aeddab107c062407f736abbb27e2e84e8acb3698ef1a`. BOTH
  coherent RC7 cases PASSED in-run (`fts:2574` retained-v2-FIRST; `fts:3065`
  separate v1-only) ⇒ no redundant standalone RC7 rerun. Root receipt
  `strategic-24a-FULL347-and-RC7-independent-review.json` (23 named
  criterion cases). CARRIED, not re-run.
- G3 WHOLE literal `sh tools/compose/smoke.sh slaif0835`: qualified at I —
  `G3_WHOLE_NATIVE_EXIT=0`, 18:28:37Z.167→18:47:30Z.978, log 65318 B SHA-256
  `94517f6fe1c79ca7881cae8b85c300fb9d64acda73e5f11010bb2987e16e247f`;
  `compose-e2e: OK projects=19`, 40 browser contracts PASSED / 0 FAILED,
  `frozen-review-parity-six-stable-pairings` PASSED 130830 ms (inside the
  preserved 600 s ceiling), packaging 49 tests OK, `compose-smoke: OK`. Edge
  scope per C4: live HTTP/browser via NGINX; `nginx -t` / `apachectl -t`
  are configuration checks only. Root receipt
  `strategic-24a-WHOLE0835-independent-review.json`. CARRIED, not re-run.
- G4 generated Agent OpenAPI zero-diff: qualified at I —
  `component-catalog: OK` + `agent-openapi: OK contracts/openapi/agent-
  v1.json`, actual child 0 (result-only log; argv/exit via the call record,
  per C6). CARRIED, not re-run.
- G5 fresh local ALL6 six-image: qualified at I —
  `G5_PIPELINE_NATIVE_EXIT=0`, 18:49:30Z.656→19:17:41Z.916, log SHA-256
  `72ad0a980a037ebe18d88d36e256efbcdf459d9afa659500ac9dc3e3792ab2c1`;
  `supply-chain-evidence: OK images=6 critical=0 high=19`, `supply-chain-
  gate: OK`, checksums 53/54; the 19 High are the inherited full 6-tuples
  from the prior FAILED census (ea586641 / artifact 12593246129), 0 new; the
  original 31 same-ID+same-pkg Critical matches are ABSENT at ANY severity;
  browser CfT 156.0.8078.47 (exe SHA-256 `230f0db8…` bound to SPDX/scan
  input), PG libcurl 8.23.0-r0, Next 16.4.1, no Sharp, foundation 0.2.0.
  Root receipt `strategic-24a-LOCAL6-independent-review.json`. CARRIED, not
  re-run.

## 5. Exact equivalence proof at J (recorded; root independently verified)

- J = `57b91d8d88f36b7967fa2c6b92b9df2420886462`, single parent eS
  `af41e747832d2cd9a1d9aaf537db8ccb179daaaa`.
- eS→J: EXACTLY two paths — `A oap/orders/083-5-f-correct-qualified-
  evidence.md` (blob `10bd22569bd11b41c948c610b1d2b45ac0a96265`) and
  `M oap/active` (blob `8791bf07…` → `a4d918e0…`).
- Full mode/blob/path comparison of EVERY tracked file (no exclude-all-oap
  shortcut): 1105 tracked at eS → 1106 at J; exactly the two entries above
  differ; all other 1105 tracked files are mode/blob/path identical,
  including `oap/MVP-CONTRACT-AUDIT.md` and `oap/MVP-PROGRESS.md`.
- I24a→J: EXACTLY three paths — the e report (A, already in eS), the f order
  (A), and `oap/active` (M).
- All historical orders/reports (a–e) byte-identical at J (oap/orders +
  oap/reports tree diff: only the f order added; zero other oap changes).
- f order hash at J: `7a8f1961663f4b89c053dc01dd2587bc8fe7fc490a9fe6c013b3075aeccdbe64`
  (identical to the published order); active at J: `083-5-f` + LF, exactly
  8 bytes (`30 38 33 2d 35 2d 66 0a`).
- Source-clean at J: the only untracked entries are `.codex/`,
  `CODEX-SESSIONS.md`, `codex.sh` — the three and only exclusions from
  source-clean accounting; preserved, untouched.
- Pre-J checks: `git diff --check` child 0; markdownlint (exact repo config,
  `--no-globs`) on the complete f order temporary document: Linting: 1 file,
  0 issues, actual child 0.
- Root independent verification: `/tmp/oap-083-5-f/strategic-57b91d8d-pre-
  report-equivalence-review.json` (ALL other path/mode/type/blob equal incl.
  oap/MVP docs; source clean excluding ONLY the human 3).

## 6. Pushed commits and CI observations (actual, at publication instant)

- J pushed to the PR branch (`af41e74..57b91d8`, push child 0); at push the
  PR #107 head became J.
- eS checks terminal observation, recorded as fact after e publication
  (immutable e report NOT amended): runs `40226610405` + `40226610309` both
  completed/success at `af41e74`.
- J CI at the instant of writing: `40228541285` completed/success,
  `40228541301` in progress (metadata-only change set; observed, not
  qualified as final).
- Final fS SELF checks: ALL 20 exact required names plus ALL 10 PG children
  (child groups 85+45) must be COMPLETED/SUCCESS at CURRENT fS, strict
  20934043 / apps 15368+57789 / no bypass. The future-S results are UNKNOWN
  until fS is pushed; this report records the publication-instant
  observations only and is NEVER amended after S_f to fill future-S results.
  No skipped/neutral/missing/pending/failed/cancelled result qualifies for
  merge. Root independently waits and requires fresh S all-30.

## 7. Footprint, variances, remaining full-product roadmap, strongest merge
concern

- Footprint (unchanged by this round; zero production/test/doc/generated
  changes): 32868 GROSS = 11179 production/45 paths + 21689 tests/36 paths;
  docs 164/12 separate; unknown 0. Named maxima 46 production / 36 tests /
  12 docs / 13 transcript; gross cap 33000 (production+tests only) and all
  individual caps unchanged. Transcript: 11 at eS → 12 at J → 13 at final
  fS (orders 6 + reports 6 + active).
- Variances preserved (not erased): the stale "43+34 names" in e line 1223
  (C5) is recorded as superseded by the measured 45+36; the d-G1
  16:14:14 wrapper-start vs 16:14:20.482563532Z first-command-start
  discrepancy (C6) is recorded; the e-report internal inconsistencies
  (sections 6 vs 10) are corrected HERE, not by editing e; all prior
  failed/interrupted attempt history (a–e) remains as recorded.
- Remaining full-product roadmap (NOT waived by this bounded correction
  round):
  - Final-MVP qualification gap: the full Apache HTTP adapter live-HTTP
    contract (C4 — at I only configuration checks qualified).
  - All other unresolved items recorded in e section 11 stand as recorded.
  - Numeric 083 / MVP is not complete; that is not a defect of this bounded
    REPORT_CORRECTION_ONLY increment.
- Strongest merge concern: the current-S all-30 checks must actually be
  green at fS (pending at publication), and root's independent review of
  this supplement must accept the C1–C7 dispositions as faithful. No product
  criterion is waived; no acceptance or merge has occurred.

## 8. Confirmations

- Scope: at J ONLY the new f order + `oap/active` changed (section 5); at
  S_f ONLY this f report changes. Zero product/test/doc/workflow/policy/lock/
  generated changes. No source packing, no proof removal, no empty
  triggering commit, no changed product behavior.
- No new source family/dependency/security/role/authority/topology/edge/pin
  change; no interchangeable identities; no pin changes under f.
- No secrets, credentials, capabilities, or private artifact content in this
  report; no production/protected credential/data/system access; no
  deployment; no production mutation.
- No skip/pending/missing presented as pass; pending S checks are labeled
  pending with the publication-instant observation.
- NO extra PR; NO merge/auto-merge/close; NO self-acceptance. OK/COMPLETE/
  green CI never means acceptance; root alone accepts/merges after
  independent review of a fully green current fS.
- No e control or e response replay; no polling of the terminal e reader;
  no early ACK. The final two-byte OK is written only after S_f is pushed
  and remotely verified.
- Secondary (pane 21) remained scratch READONLY throughout (source/CI/
  artifacts only); no helper hold was required or used. No healthy session
  was restarted.

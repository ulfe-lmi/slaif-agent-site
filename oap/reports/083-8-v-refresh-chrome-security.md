# OAP 083-8-v report: refresh the measured vulnerable Chrome payload

- Round: 083-8-v; order `oap/orders/083-8-v-refresh-chrome-security.md`
  (208L, SHA256 da2f5bb9730415b7b568ba551ed7e2f6098dc6bc7c8b37755619e575b51bc4b1).
- Mode: AMEND_EXISTING_PR; PR #112 (open)
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>; branch
  `oap/083-8-a-qualify-public-whole-session`; base main
  `40cd172109a22ef5f342589b59a4293f35379651`.
- Starting remote SHA (U report-only head):
  `ef04044c0851abd471d32512b5490e1779e68fe7`.
- Implementation head (literal):
  `bd3ac87d668cd2ed335608e857429de1991afba9` (tree
  `e91efeb2af555ddde2e784ae4a70a116b4335dc5`), sole parent the starting
  head.
- Report publication commit: SELF.
- Pushed commits: `bd3ac87` (Iv, 14 files) and this report-only SELF
  commit with sole parent Iv.

## Change (exactly 12 source paths)

Refreshed the browser-worker Chrome payload to the official Chrome for
Testing `157.0.8103.50` (revision `1717349`) - the ROOT re-verified
current Stable, not the scanner's older minimum fix `157.0.8103.38` -
addressing the 29 browser-worker Chrome Critical matches measured in
the retained It artifact (package chrome `156.0.8078.80`).

Archive acquisition (executor; curl --max-time 900 deadline, no
size-limit flag; size verified after download):
`https://storage.googleapis.com/chrome-for-testing-public/157.0.8103.50/linux64/chrome-linux64.zip`,
HTTP 200, 203527334 bytes, window 2026-11-10T21:14:16.896364Z to
21:14:23.554058Z, actual SHA256
`d17167bc092eb495a3b768c7467f27e35f625aa03834233a1663af67dcb668c9`,
independently matched by a peer acquisition.

Changed: services/browser-worker/Dockerfile (archive URL, SHA, version
assertion, comment, executable and COPY revision paths);
supply-chain/policy.json (five Chrome runtime facts);
tools/supply_chain/policy.py (matching five fail-closed facts);
tools/supply_chain/evidence.py (browser payload prefix revision);
tools/compose/smoke.sh (its two browser-image-policy lines only, all
other guards retained); tests/packaging/test_oci_contract.py (Chrome
version/hash assertions plus the minimal pinned-format repair of the
two U zlib-1.4-r0 assertion lines CI exposed); docs/SUPPLY_CHAIN.md,
docs/DEPLOYMENT.md, docs/CONFIGURATION.md, docs/LICENSE_POLICY.md,
docs/SECURITY.md, README.md (exact current bindings; the dated
083-9-b/candidate-10 and older-pin history preserved separately; no
historical scan becomes current evidence). The frozen historical
matrix and its tests are byte-unchanged; Node 24.22.1, Playwright
1.62.1, locks, base digests, the U zlib repair, Apache .18 pins,
package removals, sandbox/seccomp/egress/quotas/auth/renderer
preserved.

## Source size (actual, measured)

- 39 cumulative source paths vs main40cd: 6053 default / 6049 minimal
  (V gross +94; MAX 120 and HARD 6100 satisfied; post-write actual ==
  prewrite forecast).
- Four-file family vs Sg `89ab5ec8...`: 3599 unchanged (HARD 3604).
  The order's "expected 3599->3603" did not materialize: the Sg base
  already differed on those two smoke.sh lines (.47-era at Sg
  L260-261), so the two authorized replacements add no new gross
  against Sg; the other three family files are byte-frozen.
- Five-doc vs D `d18b6e4c...`: 285 -> 289 (HARD 500 satisfied).

## Local verification (Iv byte-equivalent WIP, pre-commit)

1. `uv run --frozen ruff check` (policy.py, evidence.py,
   test_oci_contract.py) -> native 0, "All checks passed!".
2. `uv run --frozen ruff format --check` same three -> native 0,
   "3 files already formatted".
3. `python -m unittest discover -s tests/packaging -p 'test_*.py'` ->
   native 0, 72 tests OK (bare); a first invocation of this same check
   was piped to tail with the unittest native preserved via PIPESTATUS
   (also 0) - duplicate recorded, not hidden.
4. `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`
   -> native 0, 46 tests OK.
5. `python tools/compose/verify.py --root .` -> native 0,
   "compose-policy: OK".
6. `python -m tools.supply_chain.policy validate` -> native 0,
   "supply-chain-policy: OK".

No clean-Iv rerun after commit; no other suites; no Docker, no local
browser/image probes, no private-script work.

## Remote proof and CI (Iv)

- Bare push `ef04044..bd3ac87` native 0. Remote Iv: sole parent Su,
  exact 14 paths, all 14 decoded remote bytes == worktree; PR head ==
  Iv; base main 40cd; local tree clean all-untracked.
- Supply-chain evidence (Iv CI run 42907713548) SUCCESS; ROOT
  23aed2/native0 21:57:53Z verified retained artifact 13805569565
  (ZIP 8248399B, SHA256
  `deb944d7108f4d515bb30302ca13bcb4191190fbfd66e595b4868925d8d7fb5e`,
  78 files / all 77 checksums / 18 bindings; synthetic `12d90750`
  tree == Iv, parents [main40cd, Iv]): all six images Critical 0 /
  ignored 0 / exceptions 0; all 29 Chrome Critical IDs and zlib
  CVE-2026-4738 absent at any severity including related IDs;
  measured browser version "Google Chrome for Testing 157.0.8103.50";
  Full-High accepted 12 -> 25 (11 retained, 1 removed, 14 added);
  all 86 Chrome High findings gone. Targeted evidence, not full
  six-image qualification.
- Compose (job 130149969256) FAILURE at step 8: media-publication
  contract (preview-doclist console). RAM-safe extraction: observed 1
  / stored 1, source=other, message=other-browser-error, length 79,
  scheme=https, originFamily=embed-youtube-nocookie,
  messageFamily=policy-permissions. Browser runtime/image-policy
  receipts PASSED in the same job. Outside V source scope (pinned
  payload only); no retry, no weakening, no source expansion; the
  original browser-policy failure cause remains unknown.
- Terminal Iv CI (ROOT 78b50d/native0): 30 check-runs, 29 SUCCESS /
  1 FAILURE (Compose and edge packaging), all completed, none
  pending; workflow 20 jobs = 19 SUCCESS + Compose FAILURE (an earlier
  "20 other successful" wording is preserved as a count erratum); all
  10 PG children SUCCESS; CodeQL success; apps 15368 verified except
  CodeQL 57789. First dated observation 21:51:01Z: 25 present (20
  SUCCESS, 5 pending, none failed).

## Process qualifications (actual, preserved)

- First forecast constructor (0bb0d9) stopped BEFORE any source write
  on a hard-coded family-equality assumption ("expected 3603"); the
  corrected constructor measured actual base diffs and applied; no
  retrocredit.
- Two remote-proof API attempts failed on client mistakes (top-level
  tree key; commits/{sha}/files endpoint) before the passing
  verification (498ec1).
- The five-doc baseline literal is `d18b6e4c...` (label D18); an
  initial mis-assembled 41-character string was corrected before use.
- ROOT's initial 43546/dad1ee six-image proof failed on a
  bare-version comparison, corrected at 23aed2; no test rerun.
- Peer 17 prepared six documentation candidates as independent review;
  they were not applied; the source is the executor's candidates (ROOT
  candidate review 445a8d).
- Prior q/r/S/T/U process errata and forward qualifications remain
  preserved by reference to the immutable orders/reports and the
  active V order; no history rewrite, no global no-files claim.

## Limitations and remaining work

- Version metadata and local checks do not prove installed inventories,
  a complete successful six-image qualification pipeline, native
  browser identity/compatibility, or Critical-0/ignored-0 as final
  qualification; the 29 Chrome IDs and the new zlib IDs must stay
  absent at any severity in the final artifact.
- The current full 30-check CI at the final implementation AND SELF
  must be all SUCCESS (Compose now failing); private WHOLE/LOCAL6
  qualification remains a separate later order; all prior rounds'
  architecture/privacy/docs/scope/policy review and strategic-only
  merge remain required.
- WHOLE/LOCAL6 private inputs remain INERT/NOT_RUN (whole-j.sh 624L
  `31dc9107...`, local6-j.sh 243L `12a9f36e...`).
- Round is PARTIAL: increment 083/8 not accepted; no merge, release,
  MVP, zero-vulns, or cause-fixed claim; no browser nonrecurrence is
  inferred from this pin refresh.

## Confirmations

- Scope: exactly the 12 ordered source paths plus order and active; no
  other source path, no new helper, no dependency/lock/CI change.
- Secrets: none introduced in this round's source or report; no
  capability, cookie, DB URL or private artifact data in the actual
  checked evidence. Production untouched.
- Skip: none of the ordered checks skipped. Extra PR: none; one PR
  (#112) amended; no merge, auto-merge or acceptance by the executor.

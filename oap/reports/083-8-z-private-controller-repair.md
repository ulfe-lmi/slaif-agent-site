# 083-8-z report: repair private launchers and complete qualification (COMPLETE)

- Order: `oap/orders/083-8-z-private-controller-repair.md` (305L, SHA
  `7365d1087874d8ce78d34e100154fabde75ac4877d51266a076a683ed2082d61`)
- Mode: AMEND_EXISTING_PR
- Status: COMPLETE (round contract met; NOT PR acceptance or merge)
- Repo: ulfe-lmi/slaif-agent-site
- PR: <https://github.com/ulfe-lmi/slaif-agent-site/pull/112> (open)
- Remote head branch: `oap/083-8-a-qualify-public-whole-session`
- Base: main `40cd172109a22ef5f342589b59a4293f35379651`
- Starting head (Y SELF): `1a5f542a9ba893fd5f8e90c65a27b3121f46fe17`
- Implementation SHA: `62640aa43af89faa38890a1159a18744899ce133`
  (tree `260dc0d0e4a216f6708074ae2f55c04fee07f215`; sole parent
  `93a586abd16a4a229d3dbc92aa73344e7fd81d25`)
- Report publication commit: SELF
- Pushed commits: Iz `985bec61542694459d5b4d7b252ee6c7a76687c0` (order + active + docs/TESTING truth
  correction), `178873ce734fcc951956a10ac7929290064a27dc` (helper label fix), `6f45ca087c6a3db0f6f3cec83ec7fb6d0621c738` (media embed
  fixture), `93a586abd16a4a229d3dbc92aa73344e7fd81d25` (embed membership fix), `62640aa43af89faa38890a1159a18744899ce133` (SUPPLY_CHAIN
  revision literal), and SELF (this report only), each sole-parent, all
  via the explicit refspec
  `git push origin HEAD:refs/heads/oap/083-8-a-qualify-public-whole-session`

## Outcome (COMPLETE, round contract)

- WHOLE gate: attempts 1-3 FAILED (preserved), attempt 4 PASSED with
  actual child native 0 on subject 93a586a.
- Bounded nonroot read-only SQLite inventory ran on the freshly built
  backend image after WHOLE4 and before A4 disposal (state ok); the four
  backend SQLite High findings and input-path uncertainty are retained.
- LOCAL6 gate: attempts 1-3 FAILED at preflight (native 4, preserved);
  attempt 4 completed the child (native 0) with all export/scan/bundle
  gates OK, but the controller exited native 5 with
  TRUE_END=RESIDUAL_UNKNOWN; ROOT documents acceptance of the completed
  child plus independently fulfilled supplemental owned-scratch cleanup
  and complete B disposal as qualification evidence. The controller-5
  failure is never relabeled.
- Engine A disposed (partial owner-census qualification permanent);
  Engine B disposed after complete in-scope numeric census.
- PR #112 remains open and unmerged; acceptance/merge are ROOT's alone.
  No D5, MVP, release, or product-completion claim.

## Implementation chain and source boundary

- `985bec6` (Iz): exact Z order + `oap/active` + one docs/TESTING.md
  increment-scope truth correction (sole parent Y SELF).
- `178873c`: cleared inherited compose identity labels in the
  capture-mode helper create path (private controller repair, test
  helper only).
- `6f45ca0`: deterministic media embed provider-route fixtures in
  `tests/e2e/media-publication.spec.ts` (52+/0 vs 178). Natural CI
  TERMINAL FAILURE: the ordered iframe-src assertion at failure line 829
  (shared human-workspace render order is not the fixture purpose).
- `93a586a`: replaced the positional URL expectation with exact
  order-independent membership (25+/10- vs 6f; final spec SHA256
  `6e6df0444fd39ca2fc5b6bb4b8fd92c7481f0a93130950a4a80ec2f88fe0e99d`);
  count 2, both exact anchored provider URLs registered before
  navigation, both scroll + body-marker checks retained; media delta vs
  178 67+/0 (<=100 envelope).
- `62640aa`: single literal `revision-1234` -> `revision-1717349` in
  `docs/SUPPLY_CHAIN.md` (1+/1-; doc 23695B, SHA256
  `25cfb15c401b1835c249f706965b9bbe098065f18cbc20eef7d18365dfa33e9d`);
  same-file sections and current policy/Dockerfile specify
  CfT 1717349/157.0.8103.50.
- Nine frozen input bindings at 93 (`root-membership-source-bindings-93a586a.json`,
  SHA256 `94b13368c1ca093a964df92541e7ce5f82bc625a332ce18f5e49be428e3d800b`):
  ci.yml 23ee9bc9, docs/TESTING.md e144c067, whole-session integration
  test 45cf7967, compose smoke contract b39d41ef, foundation CI test
  56fdc040, control_readiness.py 7ce85330, smoke.sh a7338099,
  verify.py fc4dd4e2, frozen run.sh 8b4a5e88. All nine byte-unchanged at
  626 (ROOT `root-doc-checkpoint-62640aa-source-boundary.json`, SHA256
  `9a53306118dedaf2cfafdcce444bac20cd4ab4cec1803e5b52fb67da8131ec25`).
- WHOLE4/LOCAL64 runtime evidence is actual 93-carried evidence on
  unchanged execution inputs, not fresh 626 runs.

## Scope (measured at 62640aa, exact method)

- Source: 42 paths, 6600 Myers / 6596 minimal gross (BOTH algorithms are
  sum(added+deleted)); exact 52 transcript exclusions
  (`oap/active` + 26 orders + 25 reports; INCREMENTS/MVP-PROGRESS are
  source).
- Four-file compose family vs base
  `89ab5ec85273ebad10f9c6963b98811cdf992c54`: 3825 both algorithms.
- Five-document family vs base
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`: 326 both algorithms.
- This SELF commit adds exactly one transcript leaf (transcript count
  becomes 53); the 42 source paths are unchanged. No blanket oap
  exclusion is used.

## WHOLE gate (owned engine A4) - 4 of 10 used, six remain

- Attempt 1 (Z1) FAILED: child 1 / controller 5, 268s, nginx unhealthy;
  actual root cause UNKNOWN (no later cause retrofitted). TRUE_END
  RESIDUAL_UNKNOWN at 2026-11-11T08:15:24.862060Z; child.log 131144B
  `810a932d...` closed. Record: `/home/janezp/.oap-z/ea/final-record.json`
  (whole_attempt_1).
- Attempt 2 (A2, record prefix `4b39a1ff`) FAILED: child 1 / controller
  5, 280s. Captured NGINX stderr is the ACTUAL
  `open('/etc/nginx/nginx.conf') permission denied`; a later config
  read is NOT_PROVED (container already gone). TRUE_END RESIDUAL_UNKNOWN
  at 12:15:56.978444Z; child.log 132997B `06210f0c...`.
- Attempt 3 (A3, record prefix `49e0e3c0`) FAILED: child 1 / controller
  5, 911s; inherited Compose image/helper-label metadata-compatibility
  failure; a created-never-started secret-policy helper and one owned
  volume were disposed with the engine. NOT a private empty-file or
  startup failure. TRUE_END RESIDUAL_UNKNOWN at 22:06:39.587830Z;
  child.log 144224B `2053991a...`.
- Attempt 4 PASSED (subject 93a586a): controller session 36871 running
  `whole-membership-93a586a-a4.sh` (SHA256
  `2b13a800fbe530e80d2eab401db349fa128063bed0219b37c2b27d5522bbb1d8`,
  2317L/111790B); child 2654862, 02:52:41Z -> 03:15:10Z, recorded
  elapsed 1351s; child native 0, timed_out 0, reaped 1, group_residual
  0, controller rc 0, session terminal native 0. Source boundary
  start/end 9/9 frozen, clean worktree, git_end_rc 0. compose-e2e OK
  projects=19; media-publication browser-e2e PASSED (contract
  media-publication-core-human-agent-preview-finalize-public-hostile);
  77 unit tests OK; final marker `compose-smoke: OK`; image inventory
  new_refs=6 / lost_refs=0 (post sha
  `d9a4fac6...`); volumes 0/0; 7 captures, 32 complete helper chains
  (25 native 0 + 7 expected-denial native 1, both created/terminal
  ownership None), 498 lifecycle metadata files, 2x33 healthy-absence
  cleanup. Closed logs: child.log 181710B
  `975667b09bfe78314cb8a8b88f10ecdd84d0a8a75e851422065a0c6d33d89d3a`,
  runner.log 23606B
  `39efa16b8648b0be32ec1a6cac19106b11b909281d2be49bdc0af230bce09043`.
  ROOT independent review receipt
  `root-WHOLE4-lifecycle-and-closed-log-review-93a586a.json` (SHA256
  `b1f788c05cd889eabb6b1999b11b8d9e6b20d87e2e03c739d4447987d1057eb9`).
- Engine A4: unit `oap-z-engine-a4.service`, invocation
  `7441b83cbbe6429cae24408e6e0bbbd5`, MainPID 2649921 (rootlesskit),
  daemon `405056c3-6f3c-4645-a0e6-96f5361483a5`, engine netns
  `net:[4026533828]`; P2 pinned probe PASS (cpu.max 100000 100000,
  memory.max 268435456, pids.max 64, in-container uid 0); stop native 0
  with same owning session 69305 terminal native 0 (result success,
  runtime 29min 1.869s); five owned PIDs GONE; cgroup/socket absent;
  pidfile unlinked by dockerd; port 8080 REBIND_OK released=True.
- A4 disposal: exact three-target `sudo -n rm` native 0, direct parents
  preserved. Owner inventory is PARTIAL and permanently qualified:
  unprivileged `find` on `data` exited native 1 (130 root-owned 0700
  overlayfs snapshot workdir subtrees unread); raw 29574604B
  `244fc8ea...` + stderr 18554B preserved; the targets are deleted, so
  no post-deletion re-run can prove the omitted subtrees. Draft1
  completeness claim corrected in record v2 (draft1 bytes preserved,
  SHA `998ff9fe...`). A4 final record v2: 40840B, SHA256
  `1cd1a1844b24872d24f0864970c9a568d5548bbb93007a63c0023085e925f263`,
  with separate actual assembler receipt (SHA256
  `e46718abc97ccf2738e951fe47ed3ab9373ddacc24323e7dfdb1bac0729a6c98`).

## Bounded SQLite inventory (WHOLE4, before A4 disposal)

- Probe `z-whole-sqlite-93a586ab` on freshly built backend image
  `sha256:e88eb48ed70c6eb3593cba78d1dcb631c37d2f412939477882cc4a234656db03`
  (revision 93a586a): read-only, no-network, no-host-mount, nonroot;
  state ok; container `0df73697...`; cleanup rm native 0.
- Actuals: sqlite 3.53.4; stdlib extension SHA256
  `c969cf811f3386c9eec5b31ecbeb4322726ed0e382f0d191515a9290bbd76449`;
  loaded `libsqlite3.so.3.53.4` SHA256
  `31cb64c44f413276f9df944b02ba8cc94f68c2c38531e76e61728c06876f5301`;
  no sqlite3 CLI; no sqlite apk package; 7 optional sqlalchemy refs;
  0 product sqlite refs; venv 2117 files with no read errors. Probe
  JSON 3364B, SHA256
  `0eac69f7130942a3534f748222ee42da423d4994c39752c7187daa9fb9ac9a91`.
- Retained: the four backend SQLite Highs
  (CVE-2026-119373/-119374/-119379/-119586, sqlite-libs 3.53.4-r0) plus
  input-path uncertainty; no blanket cause-fix, reachability, or
  GSSAPI-denial claim.

## LOCAL6 gate (owned engine B) - 4 of 10 used, six remain, no fifth

- Engine B: unit `oap-z-engine-b.service`, invocation
  `3c93eb31ca6142f198f2c79802675ff3`, MainPID 2886675 (rootlesskit),
  daemon `44c1b652-6d4c-442d-8438-4cf64cf3110f`, actual owning-tool
  start 03:57:09.353Z (setup.log 03:56:58Z is the launch-cmd log-line
  timestamp, not a proven start); kernel uid_maps captured for the five
  owned PIDs (engine netns `net:[4026533337]`); P2 pinned probe PASS
  (same flags/limits/uid as A4); real `unshare --map-root-user` child
  entry (util-linux 2.41.3); private child TMPDIR.
- Attempt 1 FAILED native 4 at PRE (uv not on PATH before image child;
  BASE1 allocated before the missing tool).
- Attempt 2 FAILED native 4 at PRE (probe image reference malformed;
  quoted bracket interior disabled the intended ranges; pre-comment
  candidate `94f009aa...` preserved, corrected `93aeba82...`).
- Attempt 3 FAILED native 4 at PRE (probe1 in-container uid malformed;
  concatenated payload/uid boundary).
- Attempt 4 (accepted candidate
  `local6-membership-93a586a-a4.sh`, SHA256
  `4a1a1643279b22730f252dd3e34b89f64e3bd09a31a79dea4331ecd1bd609d25`,
  1534L/78610B, restoring the two omitted registrations plus truthful
  comments): child 2973168 native 0, reaped 1, recorded
  controller-origin elapsed 1974s; END emission 05:42:56.821745Z
  contains END utc 05:42:56.735854Z (both stated); child spawn
  05:10:04.985448Z is distinct from the start-log emission. All gates
  passed in-run: 12 exports (12 container IDs, 12 distinct image IDs,
  12 run tags, 2 anonymous volumes), 77-payload SHA256SUMS +
  supply-chain-evidence-checksum OK, frozen validator native 0, marker
  EOF (218482B, final line marker, final LF yes), source boundary
  9/9 pre/post, post-inventory containers 0 / six refs absent 6 /
  run tags absent 12 / volume delta 0. Controller exited native 5 with
  TRUE_END=RESIDUAL_UNKNOWN because child TMPDIR retained
  node-compile-cache and `uv-31d84002c59824f4.lock`; this failure is
  permanent and never turns 0. ROOT documents acceptance of the
  completed child + independently fulfilled supplemental owned-scratch
  cleanup + complete B disposal as qualification evidence (not a
  relabel).
- B stop: stop native 0, unit success ExecMainStatus=0, same owning
  session 53918 terminal native 0 (runtime 1h51m08.279s); cgroup,
  five known PIDs, socket, pidfile all absent; AFTER-disposal strict
  0.0.0.0:8080 bind/listen/close probe native 0 at
  06:05:36.317058Z (the pre-delete `ss|grep` observation was not a
  bind and is not claimed as one).
- B disposal: bounded privileged read-only
  `sudo -n /usr/bin/find -P <three literal roots> -xdev -printf '%U|%p'`
  with DIRECT native 0 BEFORE sorting: 210445 rows, unique, confined,
  0 violations (uid 1001: 173944 + subordinate breakdown
  165536..231071; raw 43723243B `88861480...`, stderr 0B). Exact
  three-root deletion native 0 (`/home/janezp/.oap-z/eb/data`,
  `/home/janezp/.oap-z/eb/exec-run`,
  `/run/user/1001/oap-083-8-z/eb/xdg`), all absent, parents retained.
  ROOT receipt `root-B-disposal-and-preserved-scratch-independent-review.json`
  (SHA256 `8227dac20bb4df827f4437b7c0a1d5aef1979b2465b00e6db7146e78a2a02eb5`).
- Child scratch: 2 residual entries (node-compile-cache tree;
  `uv-31d84002c59824f4.lock` actual mode 666, 0B, not quiet-chmodded);
  41/41 hash-verified preserved copy, then original BASE cleanup
  native 0; the copy inventory is NOT the original per-file pre-delete
  census (permanent). Preserved-copy numeric census: 14 entries,
  numeric UID/GID 1001 (v4 raw
  `092f641730c23a87f11626d9a49f8fb5ea45dad118516e1f7b2e80570c0209c3`).
- Closed log hashes: attempt4 runner 34493B
  `6ed2606dbb40016a201d7ac7926db985d0e883258f4c62b4c53988f6ea4ba4ef`;
  attempt4 child 218482B
  `45a2337ae49feb6d2901aa4a4764abcdc0fccc3562c9ae9624d9179080f9e5be`;
  pre1 681B `2cd118e7...`; pre2 5111B `1cd230bd...`; pre3 6883B
  `b2ba9bee...`; dockerd.log 71783B `d548043d...`; setup.log 763B
  `c9cb86ed...`; daemon.json 219B `c91acd4a...`; identity v2 2417B
  `e884a882...`; identity v1 preserved 2101B `ab374f11...`.
- Final closed B record: V2 94795B, SHA256
  `0bb94d4d9ed6dea1c26c8e62e39e301b8cffe802c8b17a84c3827998acaf0adb`,
  retaining the exact V1 229-payload list and V1 manifest bytes
  (manifest 34784B `4f03cf06...`); V1 89623B `5a773252...` preserved
  with its non-atomic direct-write history (V1 must not be
  retroactively called atomic). Separate actual assembler native 0;
  receipt file SHA256
  `270ccb6f36c29eb3f8b39bc5d94b7e026902b832550543937359d7df2a115949`.
  Acceptance receipt
  `root-B-final-record-v2-acceptance-with-qualifications.json` (SHA256
  `9397caae2a4930aed2a25e98878cb9ba92c27f605658e5196918fd4b338f009c`).
- Binding V2 metadata qualifications (honored in this report): the
  measured runner literal is
  `socket_mode_owner_group=1660 1001 165642` - quote measured 1660
  verbatim including the special-mode bit (UID 1001, group 165642);
  do not restate 0660 as the full mode and no retroactive chmod
  occurred. V2 rename+fsync atomic publication is accepted for this
  single owned fresh-path lineage only; the helper has no independent
  existing-final refusal guard, so no generic no-clobber claim. Mount
  grep no-match is an observation only, not mount-absence proof.
  Manifest comparison covers covered normalized application entries,
  not whole rootfs.

## CI and artifact evidence at 62640aa (current, dated)

- CI `43170631575` and CodeQL `43170631566` completed success (all 25
  workflow jobs). ROOT independently verified all 20 exact required
  check names/apps and all ten actual PG 14-18 Group A/B children
  (receipt `root-doc-62640aa-final-checks.json`, SHA256
  `ac70fb94a518e3838c43c3e85857e7c863fa70ef094d5c456cd72eefbb437a03`).
- Compose job `131022789688` (success): compose-e2e OK projects=19 at
  06:57:55.7075695Z; public-agent-acceptance OK 06:59:04.9223983Z;
  control-readiness-fixture OK (failures=6, mount=isolated,
  identity=exact, recovery=clean) 07:01:41.0868184Z; compose-smoke OK
  07:04:32.2591069Z (all 2026-11-12).
- Supply job `131022789767` (success); artifact `13921469678`:
  ZIP 8266736B, SHA256
  `92a0c2d2fa2a489a32df437a8246c43d1b420aaaf4edf2f96fc75325ef2d5359`;
  synthetic revision `86390f44d49dd5cef46ea18849d712f23daa4c98` with
  exact parents [main 40cd, 62640aa] and 626 tree. ROOT verified 77
  payload hashes, 18 index bindings, 6 retained archive configs, 12
  exports, fixed browser identity, dependencies, and the SQLite
  catalogue library hash `31cb64c4...`; all 61 prior IDs and 10 target
  rows absent at every severity; Critical 0, ignored 0, exceptions 0;
  High 40 UNCHANGED since Iy (13 backend incl. the four SQLite Highs,
  5 browser-worker, 3 nginx, 18 postgres, 1 web); grype DB built
  2026-11-11T06:21:32Z, checksum
  `sha256:47f709e0217cf091eaf8dc57c8cdea33f9ba2c7d5374237c5011871a0c99d24e`,
  age 24.652h under the unchanged 120h policy. Receipt
  `root-six-image-checkpoint-62640aa43af8-43170631575.json`.
- ROOT full 1978-finding comparison of 626 vs 93 artifacts: complete
  match objects equal except exact structured
  `artifact.locations[].layerID` digest values (normalized after shape
  check); every other match field unmasked; non-OCI
  name/version/purl plus all license/copyright/attribution fields
  multiset-identical; all six covered normalized application manifest
  bytes identical (receipt
  `root-doc-62640aa-complete-scanner-license-manifest-comparison.json`,
  SHA256
  `18edcabb4c3c446a6d44a16a8b255fcd9b3641eeaae0db9dad4d763b67a0e944`).
  This CI-vs-CI comparison is distinct from the LOCAL6 cross-env facts
  (exact same entry path set + all bytes except 2 web generated files;
  19 differing permission fields; local first/second normalized
  app/package manifests equal; NO cross-machine rootfs equality; the 2
  web bytes remain unclassified).
- SELF's own natural CI had not started at report time: its state is
  recorded as PENDING / not-yet-run here and is asserted nowhere in
  this report.

## Y attribution erratum (corrected ONLY in this report and PR body)

- The immutable Y report's CI/artifact section mislabels Sx results as
  Iy. Live GitHub confirms Sx `4ba954eb71edd60d89ccea1ad3933ba14d69a79a`
  owns CI `42934782319` / CodeQL `42934782290` / Compose
  `130242026142` / artifact `13818901225` / synthetic merge
  `51f863effc62a14a8b5930f3f54341788b0f96a0`; actual Iy
  `e69529993cace793b6678f4b54251648873db10f` owns CI `42937677372` /
  CodeQL `42937677386` / Compose `130251667793` / artifact
  `13820245435` / synthetic `a93584171bfccf81c697c24317cd4ee2e9625625`.
  Both passed on different subjects; the old Y report is never edited.

## Historical carries (original subjects and limitations; no fresh pass)

- Literal If `0f63e82d28ce714470577af998d2dca3df835a34` FULL363/Q80/P7
  carry with their original subjects and limitations; the P7 reversed
  scratch was wrong; public API qualification does NOT prove complete
  product causal closure.
- SYSTEM containerd needrestart incident (Y S2.1): the install-time
  hook restarted the existing system containerd; existing-workload
  impact UNVERIFIED; no rollback.
- Iz docs/TESTING relative-path edit error and its exact inverse
  restoration (canonical `git diff --exit-code` native 0); limitation
  retained, historical bytes immutable.
- The order's "at most two full attempts per gate" prose remains the
  immutable original text; the standing human correction to ten
  attempts per gate governed the actual runs (WHOLE 4/10, LOCAL6
  4/10); no fifth attempt of either gate was made under this round.

## Protocol and construction incidents (honest, no relabel)

- 2026-11-12 ~06:04Z: the actor executed a global /proc scan during
  evidence correction; recorded as a protocol incident, NOT cited as
  authorized scoped proof, and NOT repeated; known PIDs/PGID only
  thereafter.
- Earlier pre-A4 user-wide pgrep matched its own command line:
  non-proof, qualified as such; absence was proved by scoped
  unit/cgroup/PID identity only.
- `find -printf %N` is unsupported by find 4.10.0 here (literal %N +
  warning); that v1 census is invalid for paths and preserved as
  diagnostic; superseded by valid %p/%U/%G commands.
- LOCAL6 controller construction defects and repaired candidates:
  probe-ref quoting (a2), probe1 uid-boundary separator (a3), rejected
  draft `a92cc37a...` (unquoted inner printf), pre-restoration copy
  `0f7f5d1a...` (missing trap INT/TERM/HUP registration and
  OWN_BASE_READY=1 assignment), pre-comment a2 `94f009aa...`; each
  preserved at the named private paths. First signal-harness run
  failed (harness defect, not runtime pass) and is preserved; the
  corrected finite harness showed actual TERM/INT/HUP parent native 6 /
  child native 143 / reaped 1 / own cleanup. Budget diagnostics ran
  finite cases with actual marker behavior (native 7 semantics).
  Constructor errors (UnicodeDecodeError / AssertionError) retained as
  construction errors, not product attempts.
- Pinned one-file Markdownlint: broken `npx` native 1 preserved as a
  failure; a canary product-repo edit command was auto-review-rejected
  at 06:46:15Z and never executed; the pinned CLI on the literal file
  gave native 0 with "Linting: 1 file" and a summary of 0 files WITH
  issues (per ROOT source proof of the pinned CLI's semantics).

## Limitations and remaining gates

- PR #112 is open and unmerged; nothing in this round accepts or
  merges it. ROOT independently reviews the final implementation, this
  report, SELF's own natural CI (PENDING at report time), policy, and
  artifacts before any strategic acceptance/merge.
- The A4 partial owner-census qualification and the original
  copy-versus-original per-file census gap are permanent; the
  controller-5 / RESIDUAL_UNKNOWN LOCAL6 result is permanent; no
  fifth WHOLE or LOCAL6 attempt exists under this round (six remain
  before a fifth of each).
- No D5 product promotion, causal closure, complete mutation audit, or
  product/MVP completion is claimed; the full product goal remains
  active, and the D5 media precondition remains future work.
- Retained evidence: failed BASEs under `/tmp/oap-083-8-z/`,
  `/home/janezp/.oap-z/ea{,2,3,4}/`,
  `/tmp/oap-083-8-z-control/` (candidates, preflight dirs, final B
  record, receipts), and the LOCAL6 attempt-4 bundle
  `/tmp/oap-083-8-z/local6-membership-93a586a-attempt4`.

## Confirmations

- No secrets, credentials, or private artifact URLs in this report or
  in the diff; safe evidence indexes and hashes only.
- No production access; no new PR; no merge or auto-merge; no
  force/reset/rebase/stash; no executor merge.
- This SELF commit adds exactly one path (this report) with sole
  parent `62640aa43af89faa38890a1159a18744899ce133`; all nine frozen
  inputs and the active order bytes are unchanged.
- The one exact two-byte response OK is sent to the already-verified
  response FIFO (inode 4470112) with the standing sole reader; no new
  reader, no control replay, no duplicate write.
- All failed checks, attempts, construction errors, and private
  candidate history are preserved at the paths named above and remain
  failed/qualified exactly as recorded.

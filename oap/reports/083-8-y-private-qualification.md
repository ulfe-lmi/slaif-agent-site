# 083-8-y report: qualify the unchanged public whole-session increment (PARTIAL)

- Order: `oap/orders/083-8-y-private-qualification.md` (205L, SHA
  `7d8fd48f9a10e08db54380063d72a00284576fafd353f089e448ab4833d96198`)
- Mode: AMEND_EXISTING_PR
- Status: PARTIAL
- Repo: ulfe-lmi/slaif-agent-site
- PR: <https://github.com/ulfe-lmi/slaif-agent-site/pull/112> (open)
- Remote head branch: `oap/083-8-a-qualify-public-whole-session`
- Base: main `40cd172109a22ef5f342589b59a4293f35379651`
- Starting head (Sx): `4ba954eb71edd60d89ccea1ad3933ba14d69a79a`
  (verified X report-only commit)
- Implementation SHA (Iy): `e69529993cace793b6678f4b54251648873db10f`
  (sole parent Sx; tree `3a523538fce0a4fcdebd8b9d27a13ac161f6ee1a`;
  order + active only)
- Report publication commit: SELF
- Pushed commits: Iy (checkpoint: exact order + active bytes) and SELF
  (this report only), both via the explicit refspec
  `git push origin HEAD:refs/heads/oap/083-8-a-qualify-public-whole-session`

## Outcome (PARTIAL)

- The single authorized WHOLE attempt terminated at preflight with
  native 4 before any product child started. Exact cause: GNU stat `%F`
  reports `regular empty file` for a zero-byte regular file, while the
  asserted string was `600 regular file` (M7 lines 215-216) for the
  freshly EXCL-created empty `runner.log`/`child.log`; the files were
  correctly 0600/uid1001/regular/0B and the fd-based S_ISREG/mode/owner
  validation in the same block had already passed.
- A deterministic diagnostic reproduction (217-line controller prefix,
  separate BASE, no product child) also terminated native 4 with the
  trace line `[ 600 regular empty file = 600 regular file ]`; it is
  classified as an additional diagnostic body execution, NOT an
  authorized second WHOLE pass.
- NOT_RUN: frozen smoke child, Compose build, product tests, W13
  SQLite inventory probe (all four backend SQLite scanner findings
  retained), LOCAL6, Engine B (not created).
- The owned rootless Engine A was constructed, identified, verified
  (P1/P2 native 0), ran healthy, then was stopped and fully disposed
  with scoped proofs under the reviewed bounds; the system daemon,
  contexts, and firewall were preserved, with one recorded S2.1
  deviation (below).
- Y does not meet its private qualification gates; acceptance remains
  with ROOT. No cause-fixed, MVP, release, or merge claim.

## Private setup (owned Engine A) — actual attempts and natives

- Five prerequisite packages (uidmap, rootlesskit, slirp4netns plus
  libsubid5/libslirp0) installed under the finite Y setup authority:
  five new, zero upgrades, zero removals; piped apt attempts preserved
  and apt's direct native qualified as unpreserved.
- S2.1 (verbatim): the install-time apt/needrestart hook restarted
  SYSTEM containerd at 2026-11-11T02:09:28Z (PID 1943531 -> 818643,
  active/running/Result success); host dockerd PID 2500 unchanged;
  impact on pre-existing containers UNVERIFIED; no rollback.
- Engine start attempt 1: native 127 —
  `dockerd-rootless.sh:233` `sysctl: not found` under the service
  `PATH=/usr/bin:/bin` (invocation `b5b1b4ee5c534480ade460bb5460a77c`);
  same-engine command-line PATH repair preserved in dockerd.log and
  setup.log.
- File-creation helper: first exclusive-file creation raised EBADF
  (fsync after close); the half-created dockerd.log was replaced by a
  verified owned EXCL 0600 recreation; native 1 history preserved.
- Engine: foreground `systemd-run --user --wait` service
  (`oap-y-engine-a.service`, Type=exec, `Delegate=cpu memory pids`,
  KillMode=control-group, TimeoutStopSec=10, owned 0600 dockerd.log),
  retained as tool session 49894; owned daemon config, private
  DOCKER_CONFIG client dir 0700/uid1001, owned socket/exec/containerd
  state; WHOLE child launch stayed ordinary host-user (no userns).
- P1 (native 0): rootless 29.1.3, ID
  `d23e1c84-a9f1-45b9-892a-d4072368d09b`, storage overlayfs, cgroup
  driver systemd, owned RootDir; unit/MainPID/ControlGroup and
  separate containerd paths verified; existing system daemon PIDs and
  the single global `default` context unchanged (post-properties
  measured).
- P2 (native 0) on pinned image
  `docker.io/library/python:3.12.16-alpine3.23@sha256:a4ad86fc2eaa4f9a5c3153776c9fb56e502dbd8e23dfa855d164308f376a6dd2`:
  exact CPU `100000 100000`, memory `268435456`, pids `64`, probe uid
  0; probe container `y-p2-e6952999`; cleanup verified by healthy
  exact-ID/name inventory empty post-removal.
- Method deviations: readiness used a wall-clock deadline (succeeded
  first poll; not relabeled; monotonic bounds thereafter); initial
  mkdir/stat/python setup calls unwrapped (prompt termination); the
  bea6b9 cleanup-verification call used a global ps scan (rule
  violation, not repeated) and an unexported CG variable in `sh -c`, so
  that failed attempt's cgroup absence is UNPROVEN (limitation, not
  clean proof); socket/pidfile/rk absence remained measured.

## WHOLE controller attempt (single, authorized)

- Source M7 `whole-y.sh`: 1266L/62465B, SHA
  `707c6542e6ccc0ca763dca997819d4c033dc7c6e38ae6f59608ce24b5506215f`,
  `sh -n` native 0; M7 is M6 plus a one-line nested-probe-payload
  quote fix after the M6 embedded-Python compile failure of the nested
  literal (ROOT reviewed the M6->M7 delta; all six outer blocks and
  the nested payload compiled).
- Pre-invocation checks all passed: worktree at Iy with clean
  all-untracked status; nine frozen SHA-256 bindings recomputed 9/9;
  scratch parent own 0700/uid1001; fresh BASE absent; engine session
  49894 polled LIVE (no terminal native).
- Phase limits bound inside M7: PRE 900s (mono start), CHILD 3600s,
  POST 900s, kill grace 5s, poll 5s, every daemon-backed op through
  `bop` with fresh min(own cap, remaining phase) bounds.
- Invocation (foreground, no trailing command masking status):
  terminal native 4 at 2026-11-11T05:27:59Z. Output (complete):
  `pre-alloc phase_pre_init mono_start=2987897 pre_budget=900
  phase_deadline_mono=2988797`; `pre-alloc sudo_shim_owned
  path=/tmp/oap-083-8-y/whole-e695299/bin/sudo refusal_native=126`;
  `whole-j: preflight failure: runner log mode/type wrong`.
- Deterministic reproduction (chunk 63c284, 05:33:23Z): 217-line
  controller prefix (M7 lines 1-44, BASE override, lines 46-216)
  against SEPARATE BASE `/tmp/oap-083-8-y/repro-e695299`; no product
  child; native 4; trace line
  `[ 600 regular empty file = 600 regular file ]`.
- Failed BASE preserved at `/tmp/oap-083-8-y/whole-e695299`:
  `runner.log`/`child.log` 0B (SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`),
  `bin/sudo` shim (SHA `9312a561074d53f6dabb85f1657fb123b8f8db18cca8a5c012d0df2f3a9e8b4a`),
  directories 0700/uid1001. Reproduction evidence preserved at
  `/tmp/oap-083-8-y/repro.sh`, `repro-out.txt`, `repro-trace.txt`.

## Engine A stop and disposal (authorized, verified)

- Pre-stop healthy facts (05:37:36Z): unit active/running,
  MainPID 1057707, Result success,
  ControlGroup `/user.slice/user-1001.slice/user@1001.service/app.slice/oap-y-engine-a.service`;
  measured cgroup.procs: 1057707, 1057720, 1057741, 1057749, 1057778;
  netns `net:[4026531833]` (rootlesskit/slirp4netns) and
  `net:[4026533421]` (dockerd/containerd); socket 1660
  1001:165642; docker inventory: 0 containers, 0 volumes, networks
  bridge/host/none only, single image = P2 pinned image, 0 project
  (slaif007j0838j) resources of any kind.
- Stop (05:38:37Z): `timeout -k 5 45 systemctl --user stop
  oap-y-engine-a.service` native 0. Post-stop `systemctl show`:
  LoadState=not-found (transient unit unloaded/collected by the user
  manager after successful stop; manager-recorded exit properties not
  queryable after unload — recorded as actual not-found state, not
  claimed as an exit receipt). Authoritative terminal receipt: the
  retained `systemd-run --user --wait` tool session 49894 — terminal
  native 0, empty output, EOF.
- Absence proofs (05:39:18Z, scoped to measured facts; no global ps
  scan): measured cgroup path absent; all five owned PIDs absent;
  engine socket absent; netns release scope-qualified (all measured
  netns-owner PIDs absent; no host-global namespace inventory
  performed or claimed); port 8080 `ConnectionRefusedError`;
  `docker.pid` self-removed by dockerd on exit (recorded, not a
  disposal action).
- System baseline: host dockerd PID 2500 and containerd PID 818643
  present (same PIDs as the recorded baselines); global contexts
  single `default` -> `unix:///var/run/docker.sock`, unchanged. The
  T4/T5 `/proc` field-22 auxiliary parse was INVALID (wrong index,
  reported 0) and is not claimed as starttime proof.
- Disposal guards: `exec-run` and `xdg` verified 700/1001:1001
  non-symlink with 700/1001:1001 parents and complete owner-class
  scans (uid {1001}, gid {1001}); `data` created 0700 by setup and
  re-chmodded to 0710 by the owned Docker/containerd rootless
  snapshotter (owner 1001:1001, parent EA 0700 unchanged) — ROOT
  accepted the actual 0710 for this exact verified fresh target; no
  chmod was performed to manufacture the old 700 guard. The
  unprivileged owner scan of `data` was INCOMPLETE (3x
  permission-denied on mode-0 `snapshots/{3,4,5}/work/work` dirs;
  pipeline-masked find natives); the corrected complete privileged
  read-only inventory
  (`/usr/bin/sudo -n /usr/bin/find -P -xdev`, native 0, stderr 0B,
  3465 lines) shows uids {1001} and gids {1001, 165577}, all within
  the authorized classes (1001 or 165536..231071;
  `/etc/subuid`/`/etc/subgid` `janezp:165536:65536`).
- rm operations (trusted absolute `/usr/bin/sudo -n /usr/bin/rm
  --recursive --force --`, literal fresh owned paths only): T7
  (05:42:39Z) removed `exec-run` + `xdg`, native 0; T9 (05:45:49Z)
  removed `data`, native 0. All three targets exact-absent
  immediately after; no `sudo docker`, no system service/context/
  firewall action, no foreign cleanup.
- Retained after disposal: `$EA` contains only `client/` (0700,
  DOCKER_CONFIG), `daemon.json`, `dockerd.log`, `engine-identity.json`,
  `probe-results.json`, `setup.log`, `disposal/` (evidence, 0700);
  the empty `/run/user/1001/oap-083-8-y/{,ea}` 0700 skeleton retained
  (outside the reviewed target list); `/tmp/oap-083-8-y` retains the
  failed controller BASE and reproduction evidence.

## Final metadata record

- First assembler (chunk 14eaed) failed with IndentationError,
  native 1; preserved as an actual failure receipt.
- Repaired private assembler (chunk fb5ef6) succeeded, native 0:
  `final-record.json` (18151B, 0600/1001 regular) at
  `/home/janezp/.oap-y/ea/final-record.json`, SHA-256
  `2652cf441bc08af062bb457a53ace8dfd601b8390ab6235da81b89b1fbabca92`,
  created after disposal as a private 0600 temp file + fsync + atomic
  rename; it binds identity/unit/stop/absence/guards/rm natives and
  retained artifact hashes.
- The subsequent list-index verification one-liners failed
  (verification-command defect, not record defect): the fb5ef6
  verification and the 2fd355 re-verification both exited native 1
  despite the record itself being valid JSON. ROOT independently read
  the complete record and verified it (0a67d8, native 0): all 22
  retained artifact hashes, all 9 frozen source hashes, exact three
  disposal-target absence, 0600/1001 regular identity.

## CI and artifact evidence at Iy (current, dated)

- CI `42934782319` and CodeQL `42934782290` completed successfully;
  ROOT independently verified all 20 strict named/app checks, all ten
  PostgreSQL child checks and all 25 CI workflow jobs at
  2026-11-11T01:11Z.
- Compose job `130242026142` passed its full smoke: browser E2E
  01:04:00Z, Agent acceptance 01:05:15Z, Control fixture success with
  clean recovery 01:08:01Z, full smoke success 01:11:00Z.
- Supply artifact `13818901225` (six-image, bound to the Iy tree and
  synthetic merge revision `51f863effc62a14a8b5930f3f54341788b0f96a0`;
  ZIP SHA-256
  `b54196124f3445924e0add6016e1334a9e4e5d6a0961c57157807b327a485967`):
  77 payload hashes, 18 index bindings, six image configs, 12 export
  receipts; the original 61 IDs and ten exact repair rows absent at
  any severity; no Critical, ignored finding, or exception; all 15
  High rows unchanged since X, including the four backend SQLite
  findings.
- Limitation: this is checkpoint-only evidence. The report commit
  SELF triggers its own natural CI after the push; that run's state is
  not asserted here.

## Process qualifications

- Premature parsing history (7359b3 `sh -n` native 0; 834ce0
  embedded-compile) remains qualified as historical deviations before
  the prospective syntax-diagnostic clarification; no engine or probe
  runtime occurred then.
- The M6 nested-compiler failure and the M7 one-line repair are
  recorded above; M7 bytes are immutable for this round.
- The 217-line prefix reproduction was a diagnostic body execution on
  a separate BASE, not an authorized second WHOLE pass.
- Inert Z successor copies (whole-y-z.sh, local6-y-z.sh) were prepared
  in separate private paths for the prospective Z round; they are not
  an activated repair, were not executed, and LOCAL6 shares the same
  empty-file text-assertion defect at lines 341/342 (ROOT 0d3f2a).

## Scope (measured)

- Iy committed exactly 2 paths (exact order bytes + active) with sole
  parent Sx; ROOT verified the complete remote leaf map (only
  order + active changed), exact parent, changed bytes, clean worktree
  (f87126), and current source bindings.
- This SELF commit adds exactly one path (this report). Product,
  configuration, dependency locks, CI, and documentation bytes and
  modes are frozen at Iy: the nine frozen SHA-256 bindings were
  recomputed 9/9 at 05:38:15Z (T2 pre-stop capture) and the worktree
  HEAD/tree/clean state was re-verified then; the clean source
  footprint (41 paths, 6317/6313 gross) is unchanged from the
  checkpoint facts.

## Limitations and remaining gates

- Y is PARTIAL: the private qualification gates were not met — WHOLE
  NOT_RUN (terminal 4 at preflight before the child), W13 SQLite probe
  NOT_RUN, LOCAL6 NOT_RUN, Engine B not created.
- The four backend SQLite scanner findings remain open (probe
  NOT_RUN) and are retained; no input-path reachability or
  exploitability conclusion is drawn from this round.
- The original Iw timeout cause (CI `42925034990` / Compose
  `130209254438`, `stage=wrong-role operation=await-readiness
  reason=timeout`) remains UNKNOWN: both waits shared that label and
  the exact phase/root cause is unproved.
- The needrestart-triggered system containerd restart (S2.1) and its
  unverified impact on pre-existing containers are recorded; no
  rollback was performed.
- Acceptance requires: the complete private qualification (WHOLE +
  bounded SQLite probe + LOCAL6) under an activated successor round
  with the reviewed controller repairs, complete natural CI on the
  final implementation and SELF, the six-image evidence artifact, and
  ROOT review and merge.

## Confirmations

- No secrets, credentials, or private artifact URLs in this report or
  in the diff; the product child never started, so no raw child or
  browser payload was ever captured.
- No production access; no new PR; no merge or auto-merge; no
  force/reset/rebase/stash.
- No product source change at SELF; no engine restart, no controller
  rerun, no Engine B or LOCAL6 execution under Y.
- Failed scratch, reproduction, and disposal evidence retained at the
  paths named above; the one exact two-byte response OK is sent via
  the standing Y response reader (no new reader added).

# OAP Coding-Agent Report — 079-2-e

## Work order

- Identifier: 079-2-e (increment-qualified round ID: fifth round of
  semantic increment 2 of numeric Objective 079, increment 079/2)
- Work-order file:
  `oap/orders/079-2-e-backend-pyc-determinism.md`
- Work-order sha256 (file-hash domain, computed over the published file):
  `67b7961f75b596b17d7a916d387b9f79940fb93509208468024efcf5f141c72d`
  (git blob ID of the committed file: `65a4aa4f96bdf9dcb7586dce606e4448f829f797`;
  different hash domains, byte-identical commit)
- `oap/active` bytes: `079-2-e\n` (hex `3037392d322d650a`)
- Numeric objective: 079 (increment 079/2; this round = the named
  backend double-build determinism repair of the `Supply-chain evidence`
  gate failure, per the recorded decision path of order §3)
- PR mode: AMENDED_EXISTING_PR (PR #93; no implementation amendment — the
  round ended BLOCKED before any implementation commit when the binding P1
  proof gate deviated; only the transcript and the report commits landed on
  the branch this round)

## Status

BLOCKED

## Executive summary

The binding P1 proof gate (order §3/§4: "P1 PROVES the mechanism and the
fix locally ... BEFORE any repository change"; "ANY deviation from the
stated expectations: STOP and report BLOCKED ... do NOT proceed to P2
under any outcome") was executed exactly as specified with ZERO repository
changes. P1.1 (baseline at C): the local double build is byte-identical
(2821/2821 manifest entries, 0 differences; target pyc 97723 bytes,
sha256 `49bb1bc8...`, constant `co_filename` in both) — the stated
baseline expectation was met. P1.2 (out-of-tree fix experiment with the
strategy-designed one-line `compileall` addition): the determinism goal was
achieved in the experiment (both fix builds produce a byte-identical
`c_parser.pyc` with the constant
`/build/.venv/lib/python3.12/site-packages/pycparser/c_parser.py`
`co_filename`), but the experiment DEVIATES from stated expectation
P1.2(c): `compileall -q -f /build/.venv` is not file-count neutral — it
adds exactly two entries to the rootfs (`opt/slaif/.venv/bin/__pycache__/`
directory + `activate_this.cpython-312.pyc`), so the fix builds carry 2823
manifest entries where P1.2(c) requires the same count as P1.1 (2821,
"compileall must add no files and remove none"). Per P1.3/§3/§5/§11 the
executor STOPPED: the P2 change was NOT applied to the repository, no
fresh builds/smoke/push/CI were performed, and this round reports BLOCKED
with the exact evidence (all commands, hashes, sizes, `co_filename`
values, entry counts, and the exact two added entries). A second
order-premise deviation is also recorded as observed evidence for the
redesign: the P2 pre-edit gate (`git grep -n 'compileall' -- . ':!oap'`
must be zero matches) would itself have failed at this tree — it returns
three matches (CI workflow, AGENTS.md, CONTRIBUTING.md). The determinism
portions of the candidate fix worked locally; the deviation is strictly a
boundary/file-count property, which strategy must resolve in a new bounded
order (scope-limited recompile, accepted boundary change, or an alternative
mechanism — each requiring its own fresh P1 proof gate).

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#93](https://github.com/ulfe-lmi/slaif-agent-site/pull/93), state
  OPEN (mergeable; `mergeStateStatus: BLOCKED` on the failing required
  check, per order §2)
- Base/head branches: `main` <- `oap/079-2-a-gallery-logogrid`
- Base `main`: `577509e7bc990d85a10af5954bee3c6f7c888a4f` (unchanged)
- Round-start remote SHA C (079-2-d report-only commit):
  `e859056cb1eeb08667a4fefd36f3ed20dfdfa73f`
- Transcript commit T (order + `active` bytes only, 2 files; parent C):
  `7743478da7773af883fa5959557c5bd7d77585d8`
- Implementation head SHA I: NONE — no implementation commit exists; the
  P1 deviation gate (order §4 P1.3) stopped the round before P2
- Report publication commit: SELF (first parent =
  `7743478da7773af883fa5959557c5bd7d77585d8`)
- Remote PR head after report publication: SELF (literal derived via GitHub
  by strategy)
- New PR this turn: no; merge performed: NO

## Blocking gap (exact)

P1.2(c) stated expectation: "the full manifest comparison shows the SAME
entry count as P1.1 (2821 — compileall must add no files and remove none)
and ZERO differing entries."

Observed in the out-of-tree fix experiment (both `--no-cache` builds of
the C tree + the single added line
`RUN /build/.venv/bin/python -m compileall -q -f /build/.venv`):

- Fix build 1 manifest: 2823 entries (2823 unique paths)
- Fix build 2 manifest: 2823 entries (2823 unique paths)
- Fix-vs-fix comparison: only_first 0, only_second 0, common 2823,
  differing entries 0 (the two builds agree)
- Fix-vs-P1.1-baseline comparison: only_first 0, only_second 2, common
  2821, differing entries 0 — the two ADDED entries (present in both fix
  builds, identical in both):

```text
directory  opt/slaif/.venv/bin/__pycache__  mode=0755
file       opt/slaif/.venv/bin/__pycache__/activate_this.cpython-312.pyc
           mode=0644 size=1985
           sha256=3537c91933762defd66cbef27641a8dd11b393d3e60c1d3dfc2697c06efe4092
```

Evidence-based interpretation (for strategy; not a diagnosis-driven
change): `uv sync` under `UV_COMPILE_BYTECODE=1` does not compile
`.venv/bin/activate_this.py` (the P1.1 baseline rootfs contains no
`bin/__pycache__` at all), while `compileall -f /build/.venv` compiles it;
the runtime stage copies `/build/.venv` wholesale to `./.venv`, so the new
`__pycache__` directory and pyc land inside the compared `opt/slaif/`
application-file boundary. The candidate fix as designed therefore changes
the boundary contents (+2 entries) and cannot be applied under this
order's binding P1 gate.

The determinism portions of the experiment met their expectations (P1.2
(a) and (b)): both fix builds' extracted `c_parser.cpython-312.pyc` have
`co_filename =
/build/.venv/lib/python3.12/site-packages/pycparser/c_parser.py` and are
byte-identical (97723 bytes, sha256 `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`,
`cmp` clean); the added `activate_this` pyc is likewise identical in both
fix builds.

Secondary observed deviation (P2 never ran; recorded for the redesign):
the P2 pre-edit gate requires
`git grep -n 'compileall' -- . ':!oap'` to be ZERO matches. Executed at T:
three matches, rc=0:

```text
.github/workflows/ci.yml:33:          python -m compileall -q
AGENTS.md:260:python -m compileall -q tools tests/repository
CONTRIBUTING.md:67:python -m compileall -q tools tests/repository tests/packaging tests/supply_chain
```

## Changes made

1. Transcript commit T: strategy-published order and `oap/active` bytes
   committed exactly (order file sha256
   `67b7961f75b596b17d7a916d387b9f79940fb93509208468024efcf5f141c72d`
   verified on the published file; active bytes `079-2-e\n` = hex
   `3037392d322d650a` verified on the committed blob).
2. Implementation commit: NONE — the P1 deviation gate (order §4 P1.3:
   "ANY deviation from the stated expectations: STOP and report BLOCKED
   with the exact evidence; do NOT proceed to P2 under any outcome"; §5:
   "If P1 deviates: no implementation under any outcome") was triggered by
   P1.2(c) (2823 entries vs required 2821).
3. This report (via the SELF report-only commit).

## Files changed

- `git diff --name-only C..T` = exactly two files:
  `oap/orders/079-2-e-backend-pyc-determinism.md` + `oap/active`
  (transcript only).
- `git diff --name-only T..SELF` = exactly one file: this report.
- `git diff --name-only C..SELF` = exactly three files: the two transcript
  files + this report. Worktree clean.

## Acceptance-criteria evidence

### Criterion 1 (T..I = exactly two files / three added lines)

- NOT SATISFIED — no implementation head I exists. The P1 deviation gate
  fired before P2 (order §3 decision path: "If P1 deviates in ANY way:
  STOP and report BLOCKED with the exact evidence; no implementation").

### Criterion 2 (C..I = exactly four files)

- NOT SATISFIED (no implementation head I exists; see Criterion 1).

### Criterion 3 (complete P1 evidence recorded)

- SATISFIED (as evidence) — the complete P1 record is in Local
  verification and Blocking gap: P1.1 baseline commands, both pyc
  sha256/size/`co_filename`/header, both manifests (2821/2821, 0
  differences); P1.2 out-of-tree experiment commands, both fix-build pyc
  sha256/size/`co_filename` (byte-identical), both fix manifests (2823/2823,
  0 differences vs each other), and the exact fix-vs-baseline diff
  (only_second = 2, both entries listed with kind/mode/size/sha256).

### Criterion 4 (pre/post grep, check_repository, pytest, ruff)

- NOT RUN — R2 (implementation + its gates) is explicitly gated behind a
  fully passing P1 (order §6 R2: "only if R1 passes"). Observed pre-edit
  grep recorded in Blocking gap (three matches — a second order-premise
  deviation, for the redesign).

### Criterion 5 (fresh-build evidence for all five images + full smoke)

- NOT RUN — P3 is gated behind P2, which was gated behind the failed P1
  gate. No builds, no smoke, no push.

### Criterion 6 (all 20 required checks SUCCESS at the exact report-only head S — OR the P5 BLOCKED branch)

- NOT SATISFIED in its SUCCESS form — no new head was pushed (no
  implementation), so there is no CI run at a new head and P5 (which
  triggers "if and only if `Supply-chain evidence` fails at the final
  head" after a push) is not the applicable branch; the round is BLOCKED
  at the P1 proof gate. The terminal check state at the round-start head C
  is recorded in the GitHub CI section (CI run `37154046174` + CodeQL run
  `37154046214`: 18 SUCCESS, 1 FAILURE — the third `Supply-chain evidence`
  occurrence at C, strategy-verified per order §2 — and 1 CANCELLED,
  `Foundation PostgreSQL 14`, observed and not executor-triggered). No CI
  re-run was invoked (flake policy: re-running an unmodified head is
  prohibited; a new pushed head supersedes).

### Criterion 7 (S report-only; parent rule; remote head S; C..S file count)

- PENDING at drafting — the order's criterion assumed an implementation
  head (C..S = five files). In this no-implementation outcome the
  079-2-b precedent applies: S changes only this report, first parent = T
  (the transcript commit, since no I exists), remote PR head = S, and
  `git diff --name-only C..SELF` = exactly three files (order + active +
  report). Verified before the response signal.

### Criterion 8 (honest status)

- BLOCKED — Criteria 1, 2, 4, 5, 6 (SUCCESS form) are not evidenced; the
  exact gap is the P1.2(c) deviation (Boundary/file-count: `compileall`
  adds two entries) plus the recorded secondary P2 pre-grep deviation.

## Local verification

All at 2026-10-03. P1 is local-only with ZERO repository changes (trees
materialized via `git archive` of C; worktree remained clean at T
throughout).

- P1.1 baseline at tree C:
  - `git archive e859056cb1eeb08667a4fefd36f3ed20dfdfa73f | tar -x -C
    /tmp/0792e-base-tree`
  - Build 1: `docker build --pull --no-cache --build-arg
    SOURCE_DATE_EPOCH=1704067200 --build-arg
    SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z --build-arg
    SLAIF_IMAGE_REVISION=e859056cb1eeb08667a4fefd36f3ed20dfdfa73f --build-arg
    SLAIF_IMAGE_VERSION=0.0.0 --file services/backend/Dockerfile --tag
    0792e-base-first:local .` (log `/tmp/0792e/build-base1.log`, rc=0)
  - Build 2: identical command, tag `0792e-base-second:local` (log
    `/tmp/0792e/build-base2.log`, rc=0)
  - Extraction (the gate's own method, `tools/supply_chain/run.sh`
    `export_rootfs`): `docker container create --name
    0792e-base-<attempt>-c <tag>` + `docker container export <container> >
    /tmp/0792e/base-<attempt>.rootfs.tar` + container removal.
  - Target pyc extraction: `tar -xf <rootfs.tar> -O
    opt/slaif/.venv/lib/python3.12/site-packages/pycparser/__pycache__/
    c_parser.cpython-312.pyc > /tmp/0792e/base-<attempt>.c_parser.pyc`
  - Manifest (the gate's exact command): `uv run --frozen python -m
    tools.supply_chain.evidence rootfs-manifest --archive
    /tmp/0792e/base-<attempt>.rootfs.tar --output
    /tmp/0792e/base-<attempt>.files.json --image-name backend`
  - Results (BOTH builds): pyc size 97723; pyc sha256
    `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`;
    marshal-loaded `co_filename =
    '/build/.venv/lib/python3.12/site-packages/pycparser/c_parser.py'`;
    pyc 16-byte header hex `cb0d0d0a03000000c80402aeef6d647c` (identical
    in both). Manifests: 2821/2821 entries; comparison (script
    `/tmp/0792e/manifest-diff.py`): only_first 0, only_second 0, common
    2821, differing entries 0. EXPECTATION MET (baseline deterministic).
- P1.2 fix experiment, OUT OF TREE:
  - `git archive e859056cb1eeb08667a4fefd36f3ed20dfdfa73f | tar -x -C
    /tmp/0792e-fixexp`; in that copy ONLY, exactly one line added to
    `services/backend/Dockerfile`, immediately after the `uv sync` RUN
    chain (after the `sed -i ... "$1/RECORD"` line): `RUN
    /build/.venv/bin/python -m compileall -q -f /build/.venv` (verified
    against the C-tree Dockerfile: exactly one added line).
  - Two `--no-cache` builds with the identical arguments (tags
    `0792e-fix-first:local` / `0792e-fix-second:local`; logs
    `/tmp/0792e/build-fix1.log`, `/tmp/0792e/build-fix2.log`; both rc=0).
    The new step is visible in the build log (line 115 of
    `build-fix1.log`): `#17 [builder 9/9] RUN
    /build/.venv/bin/python -m compileall -q -f /build/.venv`.
  - Extraction/manifest: same gate commands as P1.1 (tags
    `0792e-fix-<attempt>`; `/tmp/0792e/fix-<attempt>.rootfs.tar`,
    `/tmp/0792e/fix-<attempt>.files.json`).
  - Results: BOTH fix builds' extracted pyc: size 97723, sha256
    `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`,
    `co_filename =
    '/build/.venv/lib/python3.12/site-packages/pycparser/c_parser.py'`
    (P1.2(a) MET); the two pycs are byte-identical (`cmp` clean, P1.2(b)
    MET). Fix manifests: 2823/2823 entries; fix-vs-fix comparison:
    only_first 0, only_second 0, common 2823, differing entries 0.
    Fix-vs-P1.1-baseline comparison: only_first 0, only_second 2 (exact
    entries in Blocking gap), common 2821, differing entries 0.
    P1.2(c) DEVIATED (2823 != 2821; compileall added files).
  - Experiment cleanup: all four experiment images
    (`0792e-base-first/second:local`, `0792e-fix-first/second:local`)
    deleted; experiment trees removed; all logs/tars/pycs/manifests and
    the helper scripts retained in `/tmp/0792e/`.
- P1.3 evidence record: complete; the P1.2(c) deviation triggers the STOP
  gate (order §4 P1.3) — no P2 edit was made in the repository under any
  outcome.
- Observed P2 pre-edit grep (recorded; P2 not executed): three matches
  (exact output in Blocking gap), versus the order's required zero.
- `npx --yes markdownlint-cli2@0.23.2 --no-globs <this report's temp
  path>`: 0 issues (before the atomic rename).
- Not run (all gated behind the failed P1 gate): R2 (edits +
  check_repository + targeted pytest + ruff), P3 (fresh builds + full
  smoke), P4 (push + CI), and therefore all broader local gates.

## GitHub CI / required checks

No new head was pushed this round (no implementation), so there is no new
CI run; the state below is the terminal state observed for the
round-start head C `e859056cb1eeb08667a4fefd36f3ed20dfdfa73f` (CI run
`37154046174`, started 2026-10-03T21:08:25Z, conclusion failure; CodeQL
run `37154046214`, conclusion success; all checks terminal, verified
2026-10-03 via the GitHub jobs API):

| Required check | State (head e859056) |
|---|---|
| Analyze (actions) | SUCCESS (CodeQL 37154046214, job 111293659380, 33s) |
| Analyze (javascript-typescript) | SUCCESS (CodeQL 37154046214, job 111293659417, 58s) |
| Analyze (python) | SUCCESS (CodeQL 37154046214, job 111293659437, 1m40s) |
| CodeQL | SUCCESS (CodeQL 37154046214, run-level) |
| Compose and edge packaging | SUCCESS (CI 37154046174, job 111293636685, 11m47s) |
| Dependency review | SUCCESS (CI 37154046174, job 111293636820, 6s) |
| Detect supported languages | SUCCESS (CodeQL 37154046214, job 111293636565, 6s) |
| Foundation PostgreSQL 14 | CANCELLED (CI 37154046174, job 111293636919, 15m18s — started 2026-10-03T21:08:29Z, cancelled 2026-10-03T21:23:47Z; observed state, not triggered by the executor; superseded by any new pushed head) |
| Foundation PostgreSQL 15 | SUCCESS (CI 37154046174, job 111293636955, 10m24s) |
| Foundation PostgreSQL 16 | SUCCESS (CI 37154046174, job 111293636885, 12m50s) |
| Foundation PostgreSQL 17 | SUCCESS (CI 37154046174, job 111293636842, 12m48s) |
| Foundation PostgreSQL 18 | SUCCESS (CI 37154046174, job 111293636904, 10m9s) |
| Markdown | SUCCESS (CI 37154046174, job 111293636767, 13s) |
| Mermaid | SUCCESS (CI 37154046174, job 111293636938, 47s) |
| Node contracts | SUCCESS (CI 37154046174, job 111293636825, 2m38s) |
| Python 3.12 quality and package | SUCCESS (CI 37154046174, job 111293636872, 53s) |
| Python 3.13 quality and package | SUCCESS (CI 37154046174, job 111293636788, 38s) |
| Python 3.14 quality and package | SUCCESS (CI 37154046174, job 111293636831, 50s) |
| Repository policy | SUCCESS (CI 37154046174, job 111293636775, 10s) |
| Supply-chain evidence | FAILURE (CI 37154046174, job 111293636778, 2m22s — the THIRD `backend: normalized application-file drift` occurrence, log line 872; strategy-verified per order §2 with artifact `supply-chain-failure-diagnostics-3856e1bfce4c6c08a6f25e8653dad0a3a1c05031` (upload sha256 `05f18f8636375082374e90ef0f9eb4aed5ba491ccdc9fcd319ee1f5ab27077e4`): 2821/2821 entries, zero only_first/only_second, the SAME single file differing, with the 97733-byte variant in the FIRST build this time (the deviating build is not positionally fixed; the leak is per-build, intermittent)) |

- No CI re-run was invoked (flake policy: the single allowed unmodified
  re-run is reserved for the documented 079/1 `dragUntil` class; neither
  the failure nor the cancellation is that class, and re-running an
  unmodified head is prohibited — a new pushed head supersedes).

## Local setup / dependencies

- Docker: four experiment images built (`0792e-base-first:local`,
  `0792e-base-second:local`, `0792e-fix-first:local`,
  `0792e-fix-second:local`), rootfs-exported, then deleted; no compose
  stack was started; no repository image tags were touched.
- Evidence retained in `/tmp/0792e/`: `build-base{1,2}.log`,
  `build-fix{1,2}.log`, `base-<attempt>.rootfs.tar`,
  `fix-<attempt>.rootfs.tar`, `base-<attempt>.c_parser.pyc`,
  `fix-<attempt>.c_parser.pyc`, `base-<attempt>.files.json`,
  `fix-<attempt>.files.json`, `pyc-info.py`, `manifest-diff.py`,
  `base-dockerfile.txt`.
- No new packages or services; no sudo setup needed. No production
  systems, data, or credentials touched; no secrets in the diff or this
  report.

## Documentation

- None this round (no implementation landed; order §5 forbids any
  documentation change beyond P2, which did not run).

## Safety and scope confirmations

- Unrelated files changed: NO — on the remote this round changed exactly:
  T (2 transcript files), SELF (this report). The repository tree is
  otherwise byte-identical to C (worktree clean; `C..SELF` = exactly three
  transcript files).
- ZERO repository code/configuration changes this round: CONFIRMED (the
  candidate Dockerfile line exists only in the deleted out-of-tree
  experiment copy; the P2 test-file lines were never applied).
- No product code changed: CONFIRMED. No `tools/supply_chain/*` file
  changed: CONFIRMED. The reproducibility gate, comparison, normalization,
  contract, validator, and application-file boundary were NOT weakened or
  changed in any way: CONFIRMED (no `.pyc` exclusion or similar was
  introduced anywhere).
- No CI re-run invoked; no merge; no other PR touched; dependabot PRs
  untouched.
- Activated order/`oap/active` edited: NO — committed byte-identical
  (order file sha256
  `67b7961f75b596b17d7a916d387b9f79940fb93509208468024efcf5f141c72d`
  verified on the published file; git blob ID `65a4aa4f96bdf9dcb7586dce606e4448f829f797`
  on the committed blob; active `079-2-e\n` = hex `3037392d322d650a`
  verified on the committed blob).
- Report commit changes only this report: verified before the response
  signal.

## Cumulative base->head size (2026-09-14 review-unit governance Section 2)

Unchanged from 079-2-d (no implementation this round). Base
`577509e7bc990d85a10af5954bee3c6f7c888a4f` -> the round-start head C
`e859056cb1eeb08667a4fefd36f3ed20dfdfa73f` (exact measured diff,
`git diff --numstat`: 48 files, +5245/-92; this round adds OAP transcript
files only — order 079-2-e +376 lines, `active` replacement, this report
via SELF — so at SELF the count is 50 files, with
+5621/-92 cumulative excluding this report's own lines; the order §10
predeclared estimate was approx. 49 files / ~+5150/-92, an approximate
estimate superseded by the exact table):

| Category | Files (at C) | +lines | -lines |
|---|---|---|---|
| Production/config | 17 | 567 | 71 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 13 | 1318 | 10 |
| Generated artifacts | 5 | 354 | 4 |
| Docs | 4 | 8 | 6 |
| OAP transcript | 9 (4 orders + active + 4 prior reports) | 2998 | 1 |

Production/config remains 17 files / +567 raw diff lines (consistent with
the order §9 predeclared "17 files / ~+568 raw lines"). The ~20-30
implementation-file / several-thousand-line review trigger is NOT crossed;
CLOSURE_ONLY does not begin.

## Known limitations / blockers

- BLOCKING (the P1 proof gate): the strategy-designed one-line candidate
  fix (`RUN /build/.venv/bin/python -m compileall -q -f /build/.venv`) is
  NOT file-count neutral in the local out-of-tree double-build experiment:
  it adds exactly two entries to the compared `opt/slaif/` boundary
  (`opt/slaif/.venv/bin/__pycache__/` +
  `opt/slaif/.venv/bin/__pycache__/activate_this.cpython-312.pyc`,
  1985 bytes, sha256 `3537c91933762defd66cbef27641a8dd11b393d3e60c1d3dfc2697c06efe4092`),
  yielding 2823 manifest entries where order §4 P1.2(c) requires 2821 with
  no files added or removed. Per the binding gate the round is BLOCKED
  with zero repository changes. The determinism portions of the fix were
  proven locally (byte-identical `c_parser.pyc` across both fix builds
  with the constant `/build/.venv/...` `co_filename`; the added pyc also
  identical across both fix builds), so the deviation is strictly a
  boundary/file-count property — a strategy design input, not an executor
  decision.
- Secondary order-premise deviation (observed, P2 not executed): the P2
  pre-edit gate (`git grep -n 'compileall' -- . ':!oap'` = zero matches)
  cannot pass at this tree — three matches exist (`.github/workflows/
  ci.yml:33`, `AGENTS.md:260`, `CONTRIBUTING.md:67`); recorded in Blocking
  gap for the redesign.
- Observed CI state at C (not executor-triggered): `Supply-chain evidence`
  FAILURE (third occurrence, strategy-verified; the deviating build's
  position is not fixed — this time the 97733-byte variant is in the FIRST
  build) and `Foundation PostgreSQL 14` CANCELLED (2026-10-03T21:23:47Z).
  Both are superseded by any new pushed head; the executor invoked no
  re-run (flake policy).

## Recommended strategic follow-up

- A new bounded order (079-2-f or later) redesigning the fix with a fresh
  binding P1 proof gate, choosing among (evidence-informed options; the
  choice is strategy's, and any option changes the reproducibility
  contract surface and would need re-proof): (a) scope-limited in-place
  recompile restricted to the tree uv actually compiles (e.g. `compileall
  -q -f /build/.venv/lib` skipping `.venv/bin`) — P1 must first prove the
  scope is exactly the uv-compiled set (file-count neutral) and that uv's
  compiled set is itself stable per build; (b) acceptance of the +2
  boundary entries by explicit contract amendment (strategy/human
  decision per order §11, since it changes the application-file boundary);
  (c) an alternative mechanism for constant-`co_filename` bytecode (e.g.
  post-`uv sync` recompile of only the files uv already emitted, or a
  uv/buildkit-level fix) with equivalent P1 proof. Note for (a)/(c): the
  P2 pre-edit grep premise also needs updating (three existing
  `compileall` matches outside `oap/`). The reproducibility gate is never
  waived, and a green merge is never obtained by re-running until luck.

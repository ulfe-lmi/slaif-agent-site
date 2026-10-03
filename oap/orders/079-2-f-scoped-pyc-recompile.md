# OAP Work Order — 079-2-f (scoped bytecode recompile for double-build
determinism; 079/2 continuation)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-03 to
> `oap/orders/079-2-f-scoped-pyc-recompile.md` with
> `oap/active` = `079-2-f`, as a same-PR continuation of `079-2-a`,
> `079-2-b`, `079-2-c`, `079-2-d`, and `079-2-e` (PR #93). It retries the
> 079-2-e candidate fix with the scope corrected by the 079-2-e P1
> evidence: the recompile is restricted to `/build/.venv/lib`
> (site-packages only), which strategy-verified from the retained
> rootfs to be exactly the tree `uv sync` compiles (1040 `.py` / 1040
> `.pyc`, 1:1), making the fix file-count neutral. The coding agent
> executes under the normal OAP execution contract; strategy remains
> reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-2-f` (increment-qualified round ID: sixth round of semantic
  increment 2 of numeric Objective 079; same PR as the 079-2-a/b/c/d/e
  rounds).
- Mode: CONTINUATION (same branch, same PR). CREATE_NEW_PR: no.
- PR: #93 (`079-2-a: Gallery + LogoGrid media-reference list components
  (079/2)`), branch `oap/079-2-a-gallery-logogrid`, base `main`.
- Do not create, amend, close, or touch any other PR.

## 2. Verified current state (strategy-verified 2026-10-03 against the
retained 079-2-e P1 artifacts, the retained baseline rootfs, the round
tree, and live GitHub)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f`
  (unchanged).
- PR #93 is OPEN, `mergeable: MERGEABLE`,
  `mergeStateStatus: BLOCKED` (one required check failing at the current
  head). Round-start remote head
  `C = 2c642fec18ece0bd60a32146e2950cb4b850d13c` (079-2-e report-only
  commit; parent `T_e = 7743478da7773af883fa5959557c5bd7d77585d8`).
  Chain to base `577509e` previously verified; local worktree clean at
  `C`.
- 079-2-e status is BLOCKED at its binding P1 proof gate with ZERO
  repository changes (order §4 P1.3 correctly fired):
  - P1.1 baseline at `e859056` (met expectation): local double build
    byte-identical, 2821/2821 entries, 0 differences; target pyc 97723
    bytes, sha256 `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`,
    `co_filename = /build/.venv/lib/python3.12/site-packages/pycparser/
    c_parser.py` in both builds.
  - P1.2 full-scope experiment
    (`RUN /build/.venv/bin/python -m compileall -q -f /build/.venv`):
    the determinism goal was met (both fix builds byte-identical in the
    target pyc with constant `co_filename`) BUT the scope is NOT
    file-count neutral: it additionally compiles
    `.venv/bin/activate_this.py` (which `uv sync` does not compile),
    adding exactly two entries to the compared boundary
    (`opt/slaif/.venv/bin/__pycache__/` directory, mode 0755, and
    `opt/slaif/.venv/bin/__pycache__/activate_this.cpython-312.pyc`,
    mode 0644, 1985 bytes, sha256
    `3537c91933762defd66cbef27641a8dd11b393d3e60c1d3dfc2697c06efe4092`)
    — 2823 entries where 2821 was required.
- Strategy independently re-verified the retained 079-2-e P1 artifacts
  (`/tmp/0792e/`): all four extracted target pycs (baseline x2, fix x2)
  are 97723 bytes, sha256 `49bb1bc8...` (byte-identical across ALL four
  builds); manifest comparisons: base-vs-base 2821/2821 with 0
  differences; fix-vs-fix 2823/2823 with 0 differences; fix-vs-base with
  `only_second` = exactly the two entries above and the 2821 common
  entries with ZERO field differences — i.e. the `compileall -f`
  recompile reproduces `uv`'s pyc bytes exactly when the source path is
  the final `/build/.venv` path.
- Strategy verified the corrected scope from the retained baseline
  rootfs (`/tmp/0792e/base-first.rootfs.tar`): `.venv/lib` contains
  ONLY `python3.12/site-packages` (zero `.py` files anywhere under
  `.venv/lib` outside site-packages); site-packages contains exactly
  1040 `.py` files and exactly 1040 `.pyc` files (1:1 — `uv` compiled
  the complete set); `.venv/bin` contains exactly one `.py` file
  (`activate_this.py`) — the precise cause of the 079-2-e +2. Therefore
  `compileall -q -f /build/.venv/lib` compiles exactly the set of files
  `uv` already compiled: file-count neutral, and the drifted file
  (`pycparser/c_parser.py`, under site-packages) is in scope.
- Strategy verified at the round tree that the 079-2-e order's P2
  pre-edit grep premise was wrong: `git grep -n 'compileall' -- .
  ':!oap'` returns exactly three pre-existing matches (rc=0):
  `.github/workflows/ci.yml:33`, `AGENTS.md:260`, `CONTRIBUTING.md:67`.
  This order's P2 gate uses that closed list instead of zero.
- The 079-2-e report's option (b) (accepting the +2 boundary entries) is
  NOT chosen: this round keeps the compared boundary's file set
  byte-identical to the pre-fix baseline (2821 entries, no additions, no
  removals). No contract, normalization, or validator change is made or
  implied.
- CI state at `C` (terminal, per the 079-2-e report and strategy
  re-verification): 18 SUCCESS, 1 FAILURE (`Supply-chain evidence` —
  the third occurrence, artifact
  `supply-chain-failure-diagnostics-3856e1bfce4c6c08a6f25e8653dad0a3a1c05031`,
  same single named file), 1 CANCELLED (`Foundation PostgreSQL 14`,
  cancelled 2026-10-03T21:23:47Z — observed infra state, not
  executor-triggered, superseded by the new head this round).

## 3. Strategic context

- The 079/2 review unit has exactly one remaining named,
  environment-dependent defect: the intermittent
  `backend: normalized application-file drift` (three CI occurrences on
  this PR, one named file, per-build path leak into the pyc
  `co_filename`). 079-2-e proved the recompile mechanism achieves
  determinism locally; its only deviation was the scope. This round
  applies the same mechanism at the corrected scope with a fresh
  binding P1 proof gate.
- Decision path, recorded: P1 PROVES the corrected-scope fix locally
  (fresh baseline double build at `C`, then out-of-tree double build of
  the corrected one-line change) BEFORE any repository change. P2
  applies the change only if P1 meets every stated expectation. If P1
  deviates in ANY way: STOP and report BLOCKED with the exact evidence;
  no implementation. If `Supply-chain evidence` fails at this round's
  final head in ANY form: P5 STOP + BLOCKED + escalation. Structural
  alternatives (boundary/contract change, uv/buildkit-level fix) are
  strategy/human decisions, never the executor's. The reproducibility
  gate is never waived, and a green merge is never obtained by
  re-running until luck.

## 4. Bounded scope (exactly)

- P1 (PROOF, local only, ZERO repository changes):
  1. P1.1 Fresh baseline at tree `C`: two `--no-cache` backend image
     builds with the exact gate build arguments
     (`tools/supply_chain/run.sh` `build_image`: `--pull --no-cache
     --build-arg SOURCE_DATE_EPOCH=1704067200 --build-arg
     SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z --build-arg
     SLAIF_IMAGE_REVISION=2c642fec18ece0bd60a32146e2950cb4b850d13c
     --build-arg SLAIF_IMAGE_VERSION=0.0.0 --file
     services/backend/Dockerfile`), using a clean `git archive` of `C`
     as the build context. Extract the target pyc
     (`opt/slaif/.venv/lib/python3.12/site-packages/pycparser/
     __pycache__/c_parser.cpython-312.pyc`) from each merged rootfs and
     produce both rootfs file manifests with the gate's exact commands
     (as in 079-2-e: `docker container create` + `docker container
     export` + `uv run --frozen python -m tools.supply_chain.evidence
     rootfs-manifest --archive ... --image-name backend`). EXPECTED
     (consistent with the strategy-verified 079-2-e baseline):
     2821/2821 entries, 0 differences; target pyc 97723 bytes, sha256
     `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`,
     `co_filename = /build/.venv/lib/python3.12/site-packages/pycparser/
     c_parser.py` in both builds. Record everything.
  2. P1.2 Corrected-scope fix experiment, OUT OF TREE: clean `git
     archive` of `C`; in that copy ONLY, add exactly one line to
     `services/backend/Dockerfile`, immediately after the `uv sync` RUN
     chain (the `sed -i ... "$1/RECORD"` line):
     `RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib`
     Two `--no-cache` builds with the identical arguments. EXPECTED:
     (a) the extracted target pyc from BOTH fix builds has
     `co_filename = /build/.venv/lib/python3.12/site-packages/pycparser/
     c_parser.py`, identical in both; (b) the two pycs are
     byte-identical (record both sha256/size); (c) both fix manifests
     have exactly 2821 entries (SAME entry count as P1.1 — file-count
     neutral); (d) fix1-vs-fix2: 0 only_first, 0 only_second, 0 field
     differences; (e) fix-vs-P1.1-baseline: 0 only_first, 0 only_second
     (the file set is unchanged; any byte differences on pre-existing
     entries are expected to be zero given the strategy-verified
     079-2-e finding, but if any occur they must be counted and listed
     — this alone does not deviate, the file-set neutrality of
     (c)/(e-count) and the determinism of (a)/(b)/(d) do).
  3. P1.3 Record every command, extraction method, hash, size,
     `co_filename` value, entry count, and diff count. ANY deviation
     from (a), (b), (c), or (d), or from the P1.1 expectations: STOP
     and report BLOCKED with the exact evidence; do NOT proceed to P2
     under any outcome.
- P2 (implement ONLY if P1 passes every expectation):
  1. `services/backend/Dockerfile`: add exactly ONE line, immediately
     after the `uv sync` RUN chain (the `sed -i ...` line):
     `RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib`
  2. `tests/packaging/test_oci_contract.py`: in
     `test_backend_runtime_uses_only_frozen_production_environment`,
     after the `content = ...` line, add exactly TWO lines:
     `builder = content.split(" AS runtime", maxsplit=1)[0]`
     `self.assertIn("compileall -q -f /build/.venv/lib", builder)`
  3. PRE-EDIT: `git grep -n 'compileall' -- . ':!oap'` must list exactly
     the three strategy-verified pre-existing lines (`.github/
     workflows/ci.yml:33`, `AGENTS.md:260`, `CONTRIBUTING.md:67`) —
     record the exact output. POST-EDIT: the identical grep must list
     exactly five lines: those three plus the new Dockerfile line and
     the new test line. Any other occurrence or count: STOP, report
     BLOCKED.
- P3: force fresh image builds for ALL FIVE affected images (web, nginx,
  backend, postgres, apache — no stale-cache reuse; delete the stale
  local images first) and run the FULL Compose smoke (all 13 projects)
  to rc=0 with the key lines recorded (including the apache edge image
  still building from `openssl=3.0.13-0ubuntu3.16`).
- P4: push the branch; the final head must have ALL 20 required checks
  SUCCESS (in particular `Supply-chain evidence` must pass at the exact
  final head; if it fails, see P5).
- P5: if and only if `Supply-chain evidence` fails at the final head:
  download its failure-diagnostics artifact (the 079-2-d diagnostics
  extension guarantees it retains both rootfs file manifests), produce
  the exact file-level diff (counts of only_first/only_second/differing
  paths, the differing path list, and both entries' sha256/size), then
  STOP and report BLOCKED with that evidence and an explicit
  escalation. No second fix attempt is permitted this round under any
  outcome.
- P6: publish the round report (see Section 9) as a report-only commit
  (`Report publication commit: SELF`) on the same branch.

## 5. Explicit non-goals

- Do NOT apply the 079-2-e full-scope line
  (`compileall -q -f /build/.venv`) — it is proven not file-count
  neutral.
- Do NOT accept the +2 boundary entries (the 079-2-e report's option
  (b)): the compared boundary's file set must remain exactly the
  pre-fix 2821 entries (no additions, no removals).
- No change to any `tools/supply_chain/*` file; no change to the
  double-build comparison, the normalization logic, the reproducibility
  contract, the validator, or the application-file boundary (no `.pyc`
  exclusion or similar); no change to `UV_COMPILE_BYTECODE`,
  `UV_LINK_MODE`, `SOURCE_DATE_EPOCH`, or any other build ENV.
- No change to any Dockerfile other than `services/backend/Dockerfile`;
  no change to `tests/packaging/test_oci_contract.py` beyond the two
  assertion lines; no change to `AGENTS.md`, `CONTRIBUTING.md`,
  `.github/workflows/ci.yml`, or any other file.
- No product code, migration, workflow, lockfile, or documentation
  change of any kind beyond P2.
- No CI re-run is permitted for an unmodified head (flake policy); a new
  pushed head supersedes.
- If P1 deviates: no implementation under any outcome (Section 4 P1.3).
- Do not touch dependabot PRs. Do not merge. Do not edit the committed
  079-2-a/b/c/d/e orders or reports or any other OAP transcript file;
  `active` is replaced by this order per protocol.

## 6. Requirements

### R1 - P1 proof (local only, zero repository changes)

Execute P1.1, P1.2, P1.3 in order and record all evidence exactly as
Section 4 P1 specifies (commands, hashes, sizes, `co_filename` values,
manifest entry counts and diff counts, and the fix-vs-baseline
pre-existing-entry byte-diff count). Any deviation from the stated
expectations: STOP and report BLOCKED; do not proceed to R2.

### R2 - One-line implementation (only if R1 passes)

Apply exactly the two-file, three-line change of Section 4 P2 with the
pre-edit and post-edit grep evidence; then run `uv run --frozen python
tools/check_repository.py` (must PASS) and `uv run --frozen pytest
tests/packaging/ tests/supply_chain/ -q` (must pass); then
`uv run --frozen ruff check` and `uv run --frozen ruff format --check`
on the touched test path (must be clean). Record all results.

### R3 - Fresh builds + full smoke (P3)

Delete the stale local images, force fresh builds of all five affected
images, run the full Compose smoke (13 projects) to rc=0, and record the
smoke log key lines including proof the apache edge image still built
from `openssl=3.0.13-0ubuntu3.16` (exact apt transaction lines + the
`naming to ... apache ... done` line).

### R4 - Push and CI (P4)

Push the implementation commit of this round to the same branch. Verify
(and report) the terminal state of ALL 20 required checks on the exact
final head, with the per-check table and run IDs. If `Supply-chain
evidence` fails, execute P5 and stop.

### R5 - Report (P6)

Publish `oap/reports/079-2-f-scoped-pyc-recompile.md` as a report-only
commit (SELF) whose parent is this round's implementation head.

## 7. Acceptance criteria (observable)

Let T = this round's transcript commit (order + `oap/active` bytes
only), I = this round's implementation head, S = the report-only commit,
C = `2c642fec18ece0bd60a32146e2950cb4b850d13c`.

1. `git diff --name-only T..I` lists exactly two files:
   `services/backend/Dockerfile` and `tests/packaging/
   test_oci_contract.py`; `git diff --numstat T..I` = `1 0` (Dockerfile)
   and `2 0` (test file) — exactly three added lines, zero deleted.
2. `git diff --name-only C..I` lists exactly four files: the two of
   criterion 1 plus
   `oap/orders/079-2-f-scoped-pyc-recompile.md` and `oap/active`.
3. The complete P1 evidence is recorded in the report: P1.1 baseline
   commands, both pyc sha256/size/`co_filename`, both manifests (2821/
   2821, 0 differences); P1.2 corrected-scope experiment commands, both
   fix-build pyc sha256/size/`co_filename` (byte-identical), both fix
   manifests (2821 entries each, fix-vs-fix 0/0/0), and the fix-vs-
   baseline comparison (0 only_first, 0 only_second; pre-existing-entry
   byte-diff count reported).
4. The pre-edit (three-line) and post-edit (five-line) grep outputs, the
   `tools/check_repository.py` PASS, the pytest result, and the ruff
   clean result are recorded in the report.
5. Fresh-build evidence for all five affected images plus the full smoke
   rc=0 key lines (including the apache edge image on the untouched
   `openssl=3.0.13-0ubuntu3.16` pin) are recorded in the report.
6. All 20 required checks SUCCESS on the exact report-only head S
   (per-check table with CI/CodeQL run IDs) — OR, if and only if
   `Supply-chain evidence` failed at I, an honest BLOCKED with the
   exact P5 file-level drift diff from the artifact (or the exact
   artifact contents proving the manifests absent).
7. S changes only
   `oap/reports/079-2-f-scoped-pyc-recompile.md`; its parent is I;
   the remote PR head equals S; and `git diff --name-only C..S` lists
   exactly five files (the four of criterion 2 plus the report).
8. Status is COMPLETE only if criteria 1-5 and 7 are evidenced AND
   criterion 6 is satisfied in its SUCCESS form; otherwise BLOCKED/
   PARTIAL with the exact gap.

## 8. Verification and workflow

- Commit the strategy-published order and `oap/active` bytes exactly
  (blob sha256 verified against the published files) as the transcript-
  only commit T before the implementation commit I; then the report-only
  commit S. One round, one implementation commit; no merge by the
  executor.
- Local, in order: P1.1 baseline double build + extraction + manifest
  comparison; P1.2 out-of-tree corrected-scope experiment + extraction +
  manifest comparisons; P1.3 evidence record (STOP gate); P2 edits +
  pre/post grep (R2), then `uv run --frozen python
  tools/check_repository.py`, targeted pytest, and ruff; P3 fresh builds
  via `sh tools/compose/smoke.sh <project>` full smoke (R3); `npx --yes
  markdownlint-cli2@0.23.2` on the report file (zero issues).
- Push, then poll required checks on the exact head until all are
  terminal; report the per-check table with run IDs; if
  `Supply-chain evidence` failed, download its failure-diagnostics
  artifact and execute P5 before the report.
- GitHub workflow: push to the existing branch only.

## 9. Report requirements

`oap/reports/079-2-f-scoped-pyc-recompile.md` must state: identifier
and mode (CONTINUATION, PR #93); the work-order sha256 (file-hash
domain, computed over the published file; the git blob ID may be noted
alongside, as in 079-2-e); the `oap/active` bytes and hex; exact
transcript commit T, round implementation head I, and report SELF; the
exact three-line diff (file:line per site); the pre-edit and post-edit
grep outputs; the complete P1 evidence (Section 4 P1: all commands,
hashes, sizes, `co_filename` values, entry counts, diff counts, and the
fix-vs-baseline pre-existing-entry byte-diff count); the
`tools/check_repository.py` PASS, pytest, and ruff evidence; the fresh-
build evidence for all five images and the full smoke key lines; the
complete 20-check per-check table at the exact final head with run IDs
(or, for an honest BLOCKED, the P5 file-level drift diff / exact
artifact contents); the cumulative base->head size table per the
2026-09-14 review-unit governance (base `577509e` -> final head,
grouped: production/config, migrations, tests/evidence, generated
artifacts, docs, OAP transcript; state that the review trigger is not
crossed: cumulative production/config 17 files / ~+568 raw lines);
confirmation that no product code changed this round, that the
reproducibility gate was NOT weakened in any way, that the compared
boundary's file set is unchanged (2821 entries, no additions, no
removals), and that no `tools/supply_chain/*` file changed; and an
honest status.

## 10. Predeclared review budget (2026-09-14 review-unit governance)

- Production/config: 1 file changed (`services/backend/Dockerfile`), +1
  line. Migrations: 0.
- Tests/evidence: 1 file changed (`tests/packaging/
  test_oci_contract.py`), +2 lines.
- Generated artifacts: 0. Docs: 0.
- OAP transcript: this order + one new round report + `active`
  replacement.
- Cumulative after this round (base `577509e` -> final head): approx.
  52 files, ~+6900/-92 (approximate predeclared estimate; the exact
  final table belongs in the report), production/config 17 files /
  ~+568 raw lines; the ~20-30 implementation-file /
  several-thousand-line review trigger is NOT crossed; CLOSURE_ONLY
  does not begin.

## 11. Review-unit governance (2026-09-14 amendment, in force)

This round completes the finite, already-named packaging defect inside
the 079/2 review unit per the recorded decision path of Section 3. No
new semantic family, no adjacent feature, no opportunistic scope. The
079-2-a/b/c/d/e rounds are immutable records; their evidence (local
double builds, CI forensics, P1 proofs, P5 file-level diffs, strategy
forensics) is adopted by this order. The P1 proof gate is binding: no
implementation without a fully passing P1. If P5 is triggered, the
round ends in BLOCKED with escalation; any fix beyond this one line (or
any boundary/contract change) requires a new strategy round and, if
structural, human authorization. The reproducibility gate is never
waived, and a green merge is never obtained by re-running until luck.

# OAP Work Order — 079-2-d (apache pin repair + reproducibility-diagnostics
extension; 079/2 continuation)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-03 to
> `oap/orders/079-2-d-apache-pin-and-reproducibility-diagnostics.md` with
> `oap/active` = `079-2-d`, as a same-PR continuation of `079-2-a`,
> `079-2-b`, and `079-2-c` (PR #93). It completes the finite packaging
> defect repair authorized by the 2026-10-03 strategy scope decision with
> the two remaining externally forced defects exposed at head
> `2c21c71`: (A) the rotated-out Ubuntu noble `openssl` pin in the
> out-of-scope-for-079-2-c apache edge image, and (B) the inability to
> name the file behind the intermittent backend reproducibility drift
> (failure-diagnostics retention gap). The coding agent executes under the
> normal OAP execution contract; strategy remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-2-d` (increment-qualified round ID: fourth round of semantic
  increment 2 of numeric Objective 079; same PR as the 079-2-a/b/c rounds).
- Mode: CONTINUATION (same branch, same PR). CREATE_NEW_PR: no.
- PR: #93 (`079-2-a: Gallery + LogoGrid media-reference list components
  (079/2)`), branch `oap/079-2-a-gallery-logogrid`, base `main`.
- Do not create, amend, close, or touch any other PR.

## 2. Verified current state (strategy-verified 2026-10-03 against live
GitHub, job logs, the failure-diagnostics artifact, and local forensics)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f` (unchanged).
- PR #93 is OPEN, `mergeable: MERGEABLE`. Round-start remote head
  `C = 2c21c7189bb0308e5204d5bfdff4428904d6ba30` (079-2-c report-only
  commit; parent `7efcece05390728018a86ab00bd0fc983888b2e7` = the
  079-2-c implementation head I, whose 17-line Alpine repair strategy
  independently verified; chain to base `577509e` verified).
- 079-2-c status is BLOCKED on exactly two new, distinct, externally
  forced failure classes at I (CI run `37148750609`, both strategy-
  re-verified from the job logs):
  - (A) `Compose and edge packaging` (job `111277991401`): all five
    compose images build from the new Alpine pin; the standalone
    `target apache` build then fails with `E: Version
    '3.0.13-0ubuntu3.15' for 'openssl' was not found` (log 3107) —
    the Ubuntu noble archive rotated out the pinned openssl. Strategy
    independently probed the digest-pinned base
    `ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`:
    `apache2{,-bin,-data,-utils}=2.4.58-1ubuntu8.15` are STILL available;
    `openssl` is now available ONLY as `3.0.13-0ubuntu3.16`.
  - (B) `Supply-chain evidence` (job `111277991443`):
    `ERROR: backend: normalized application-file drift` (log 867) — the
    double-build reproducibility gate
    (`tools/supply_chain/run.sh` `build_and_compare` +
    `tools/supply_chain/evidence.py` `compare-builds`) compares the
    normalized `opt/slaif/` rootfs file manifests of two `--no-cache`
    builds of the same tree. The normalized SBOM package signatures
    MATCHED; the file manifest differs. A local double build at I (exact
    CI build arguments) is byte-identical across all 2821 application
    files, so the CI drift is intermittent, not a deterministic tree
    content mismatch. The pin change cannot be the cause: the changed
    layers are apk packages under `/usr`, the compared boundary is
    `opt/slaif/`, and the SBOM level matched. This gate was unreachable
    at every previous head because the backend build failed at the apk
    step.
  - Strategy root-caused the diagnostic gap for (B):
    `tools/supply_chain/failure_diagnostics.py` retains only files
    matching `RAW_FILE = ^[a-z0-9-]+\.raw\.(spdx|syft|grype)\.json$` from
    the temporary root (plus `scan-sboms/*.syft.json`), so the rootfs
    file manifests — first build at
    `<evidence>/manifests/<image>.files.json`, second build at
    `<temporary>/second/<image>.files.json` — are structurally excluded
    from the failure artifact, and the drifted file cannot be named
    (confirmed in artifact `adb9235...`: STATUS INCOMPLETE + SBOM files
    only).

## 3. Strategic context

- The 079-2-a product implementation (catalog 31 with Gallery/LogoGrid,
  bounded error-key vocabulary, fail-closed renderers, exact OpenAPI
  delta) remains fully delivered and locally verified; the Alpine pin
  repair (079-2-c) is complete and CI-proven (every Alpine image builds
  at I; no apk resolution error remains). The only path to 079/2 closure
  is resolving the two remaining externally forced defects in (A) and
  (B), which are finite packaging/evidence defects inside the 079/2
  review unit, not new semantic families.
- Decision path for (B), recorded: this round extends diagnostics ONLY,
  so the next CI occurrence names the drifted file(s). If
  `Supply-chain evidence` passes at this round's final head, that green
  run on the exact head is the acceptance evidence and the round is
  closable; the single intermittent occurrence at I, the byte-identical
  local double build, and the SBOM-level match are recorded in the
  acceptance record. If it fails again, the executor reports the exact
  file-level diff from the new diagnostic and stops; the determinism
  fix (if any is needed) is a subsequent round (079-2-e or later) and —
  if it requires structural changes to the builder, lockfiles, or the
  reproducibility contract — an escalation to strategy/human. The
  reproducibility gate is never waived, and a green merge is never
  obtained by re-running until luck.

## 4. Bounded scope (exactly)

- P1 (class A): replace the exact string `3.0.13-0ubuntu3.15` with
  `3.0.13-0ubuntu3.16` in exactly the three lines of the closed list
  (strategy-verified at C, `git grep -n '3.0.13-0ubuntu3.15' -- .
  ':!oap'` = exactly 3 lines):
  1. `infra/apache/Dockerfile` line 21
     (`'openssl=3.0.13-0ubuntu3.15'`)
  2. `supply-chain/policy.json` line 156
     (`"openssl=3.0.13-0ubuntu3.15"`, the
     `ubuntu_package_overrides.images.apache.install` entry)
  3. `tests/packaging/test_oci_contract.py` line 99 (the
     `test_apache_qualification_is_exact_and_uses_fixed_ubuntu_packages`
     assertion)
  The `apache2{,-bin,-data,-utils}=2.4.58-1ubuntu8.15` pins (12 lines
  across the same three files) are verified still available in the
  noble archive and MUST NOT be changed.
- P2 (class B diagnostics): extend the failure-diagnostics retention
  ONLY, in exactly two files:
  1. `tools/supply_chain/failure_diagnostics.py`: in
     `retain_failure_diagnostics`, add as additional candidates the
     first-build rootfs manifests
     (`<evidence>/manifests/*.files.json`) retained under their own
     names, and the second-build rootfs manifests
     (`<temporary>/second/*.files.json`) retained under the
     collision-free names `second-<image>.files.json`. The existing
     size limits (`MAX_FILE_BYTES`/`MAX_TOTAL_BYTES`), the
     forbidden-marker safety filter, and the STATUS/SHA256SUMS
     generation are unchanged. No other behavior changes.
  2. `tests/supply_chain/test_failure_diagnostics.py`: add a test case
     asserting that, when both manifests exist, `retain` keeps
     `<image>.files.json` and `second-<image>.files.json`, that
     `STATUS.json` `diagnostic_files` lists both, and that
     `validate_failure_diagnostics` passes on the extended bundle.
- P3: force fresh image builds for ALL FIVE affected images (web,
  nginx, backend, postgres, apache — the apache edge image must build
  from the new pin this time; delete the stale local apache image first)
  and run the FULL Compose smoke (all 13 projects) to rc=0 with the key
  lines recorded.
- P4: push the branch; the final head must have ALL 20 required checks
  SUCCESS (in particular `Compose and edge packaging` must flip green
  and `Supply-chain evidence` must pass at the exact final head; if
  `Supply-chain evidence` fails again, see P5).
- P5: if and only if `Supply-chain evidence` fails at the final head:
  the new failure-diagnostics artifact must contain the first and second
  rootfs file manifests of the failing image; download the artifact and
  produce the exact file-level diff (paths only in first, only in
  second, or with differing sha256/size/mode, with counts and the
  differing path list), then STOP and report BLOCKED with that evidence.
  If the manifests are absent from the artifact, report BLOCKED with the
  exact artifact contents. No repair of the drift is permitted this
  round under any outcome.
- P6: publish the round report (see Section 9) as a report-only commit
  (`Report publication commit: SELF`) on the same branch.

## 5. Explicit non-goals

- No change to the `apache2=2.4.58-1ubuntu8.15` pins or any other apt
  package pin; no change to `infra/apache/Dockerfile` beyond line 21.
- No change to any section of `supply-chain/policy.json` beyond line 156.
- No change to any test other than the one assertion line of
  `tests/packaging/test_oci_contract.py` (line 99) and the additive test
  case in `tests/supply_chain/test_failure_diagnostics.py`.
- No change to `tools/supply_chain/evidence.py`,
  `tools/supply_chain/run.sh`, `tools/supply_chain/policy.py`, or any
  other supply-chain code; no change to the double-build comparison, the
  normalization logic, the reproducibility contract, or the
  validator; no attempt to fix or work around the backend drift in this
  round (no builder-stage edits, no bytecode/uv/lockfile changes, no
  Dockerfile structure changes).
- No product code, configuration, migration, workflow, or documentation
  change of any kind beyond P1-P2.
- No version other than `3.0.13-0ubuntu3.16` for openssl (no
  unversioned pin, no source change). If the pre-edit inventory
  deviates from the closed 3-line list, if the new pin fails resolution,
  if the smoke fails, or if any other failure class appears: STOP and
  report BLOCKED with the exact evidence; do not improvise alternatives.
- No CI re-run is permitted for an unmodified head (flake policy); a
  new pushed head supersedes.
- Do not touch dependabot PRs. Do not merge. Do not edit the committed
  079-2-a/b/c orders or reports or any other OAP transcript file;
  `active` is replaced by this order per protocol.

## 6. Requirements

### R1 - Apache pin bump with inventory proof (P1)

1. PRE-EDIT: run `git grep -n '3.0.13-0ubuntu3.15' -- . ':!oap'` at the
   round-start tree; record the exact output; it must be exactly the
   three closed-list lines. Any deviation: STOP, report BLOCKED.
2. Apply exactly the three line replacements.
3. POST-EDIT: re-run the identical grep; record the output; it must be
   zero matches (record the empty output and non-zero exit status).
4. Run `uv run --frozen python tools/check_repository.py` (must PASS —
   it validates the policy/Dockerfile/test consistency this bump
   depends on) and record the result.
5. Run `uv run --frozen pytest tests/packaging/
   tests/supply_chain/ -q` and record the result (must pass, including
   the new diagnostics test case).

### R2 - Failure-diagnostics extension (P2)

Implement the two-file bounded change of Section 4 P2 (additive
candidates only; existing behavior, limits, filters, validator, and
STATUS/SHA256SUMS semantics unchanged), together with the new test
case. Record the exact line counts of both files.

### R3 - Fresh builds + full smoke (P3)

Delete the stale local `apache` image, force fresh builds of all five
affected images (no stale-cache reuse), run the full Compose smoke
(13 projects) to rc=0, and record the smoke log key lines including
proof the apache edge image built from `openssl=3.0.13-0ubuntu3.16`
(exact apt transaction lines + the `naming to ... apache ... done`
line).

### R4 - Push and CI (P4)

Push the implementation commit(s) of this round to the same branch.
Verify (and report) the terminal state of ALL 20 required checks on the
exact final head, with the per-check table and run IDs. If
`Supply-chain evidence` fails, execute P5 and stop.

### R5 - Report (P6)

Publish `oap/reports/079-2-d-apache-pin-and-reproducibility-diagnostics.md`
as a report-only commit (SELF) whose parent is this round's
implementation head.

## 7. Acceptance criteria (observable)

Let T = this round's transcript commit (order + `oap/active` bytes
only), I = this round's implementation head, S = the report-only
commit, C = `2c21c7189bb0308e5204d5bfdff4428904d6ba30`.

1. `git diff --name-only T..I` lists exactly five files: the three P1
   files plus `tools/supply_chain/failure_diagnostics.py` and
   `tests/supply_chain/test_failure_diagnostics.py`; the diff of the
   three P1 files shows exactly three changed lines; the two P2 files
   together show at most 60 changed lines (exact count reported).
2. `git diff --name-only C..I` lists exactly seven files: the five of
   criterion 1 plus
   `oap/orders/079-2-d-apache-pin-and-reproducibility-diagnostics.md`
   and `oap/active`.
3. The pre-edit (3-line) and post-edit (zero-line) grep outputs, the
   `tools/check_repository.py` PASS, and the pytest result are recorded
   in the report.
4. Fresh-build evidence for all five affected images (including the
   apache edge image on the new pin) plus the full smoke rc=0 key lines
   are recorded in the report.
5. All 20 required checks SUCCESS on the exact report-only head S
   (per-check table with CI/CodeQL run IDs) — OR, if and only if
   `Supply-chain evidence` failed at I, an honest BLOCKED with the
   exact file-level drift diff produced per P5 (or the exact artifact
   contents proving the manifests absent).
6. S changes only
   `oap/reports/079-2-d-apache-pin-and-reproducibility-diagnostics.md`;
   its parent is I; the remote PR head equals S; and
   `git diff --name-only C..S` lists exactly eight files (the seven of
   criterion 2 plus the report).
7. Status is COMPLETE only if criteria 1-4 and 6 are evidenced AND
   criterion 5 is satisfied in its SUCCESS form; otherwise BLOCKED/
   PARTIAL with the exact gap.

## 8. Verification and workflow

- Commit the strategy-published order and `oap/active` bytes exactly
  (blob sha256 verified against the published files) as the
  transcript-only commit T before the implementation commit I; then the
  report-only commit S. One round, one implementation commit (or the
  minimal set of in-scope repair commits); no merge by the executor.
- Local, in order: pre-edit grep (R1.1); the three replacements (R1.2);
  post-edit grep (R1.3); `uv run --frozen python
  tools/check_repository.py` (R1.4); targeted pytest (R1.5); the P2
  implementation + test (R2); fresh builds + `sh
  tools/compose/smoke.sh <project>` full smoke (R3); `npx --yes
  markdownlint-cli2@0.23.2` on the report file (zero issues).
- Push, then poll required checks on the exact head until all are
  terminal; report the per-check table with run IDs; if
  `Supply-chain evidence` failed, download its failure-diagnostics
  artifact and execute P5 before the report.
- GitHub workflow: push to the existing branch only.

## 9. Report requirements

`oap/reports/079-2-d-apache-pin-and-reproducibility-diagnostics.md` must
state: identifier and mode (CONTINUATION, PR #93); the work-order
sha256 (computed over the published file); exact transcript commit T,
round implementation head I, and report SELF; the three-line P1 diff
(file:line per site); the P2 diff with exact per-file line counts; the
pre-edit and post-edit grep outputs; the `tools/check_repository.py`
PASS and pytest evidence; the fresh-build evidence for all five images
and the full smoke key lines; the complete 20-check per-check table at
the exact final head with run IDs (or, for an honest BLOCKED, the
P5 file-level drift diff / exact artifact contents); the cumulative
base->head size table per the 2026-09-14 review-unit governance (base
`577509e` -> final head, grouped: production/config, migrations,
tests/evidence, generated artifacts, docs, OAP transcript; state that
the review trigger is not crossed: cumulative production/config 17
files / ~570 substantive lines); confirmation that no product code
changed this round and that no attempt was made to fix the backend
drift; and an honest status.

## 10. Predeclared review budget (2026-09-14 review-unit governance)

- Production/config: 2 files (`infra/apache/Dockerfile`,
  `tools/supply_chain/failure_diagnostics.py`), 3 + <=40 = at most 43
  substantive lines.
- Tests/evidence: 2 files (`tests/packaging/test_oci_contract.py` 1
  line; `tests/supply_chain/test_failure_diagnostics.py` <=20 lines).
  Migrations: 0. Generated artifacts: 0. Docs: 0.
- OAP transcript: this order + one new round report + `active`
  replacement.
- Cumulative after this round (base `577509e` -> final head): 48 files,
  ~+4500/-95 (approximate predeclared estimate; the exact final table
  belongs in the report), production/config 17 files / ~570
  substantive lines; the ~20-30 implementation-file /
  several-thousand-line review trigger is NOT crossed; CLOSURE_ONLY
  does not begin.

## 11. Review-unit governance (2026-09-14 amendment, in force)

This round completes the finite packaging/evidence defect repair inside
the 079/2 review unit per the 2026-10-03 strategy scope decision and
the 079-2-c STOP report. No new semantic family, no adjacent feature,
no opportunistic scope. The 079-2-b and 079-2-c rounds are immutable
BLOCKED records; their evidence (probes, CI forensics, local double
build, artifact analysis) is adopted by this order. The P2 diagnostics
extension is an evidence-only change: it must not alter what the
reproducibility gate accepts or rejects. If the pre-edit inventory
deviates, if the new pin fails, if the smoke fails, or if any other
failure class appears: stop and report BLOCKED with the exact
evidence; strategy decides the next step (a drift determinism fix, if
evidence later requires one, is a separate bounded round and, if
structural, an escalation).

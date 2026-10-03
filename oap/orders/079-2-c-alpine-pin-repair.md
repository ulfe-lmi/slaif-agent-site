# OAP Work Order — 079-2-c (Alpine pin repair, corrected full scope; 079/2
continuation)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-03 to
> `oap/orders/079-2-c-alpine-pin-repair.md` with `oap/active` =
> `079-2-c`, as a same-PR continuation of `079-2-a` and `079-2-b`
> (PR #93). It completes the finite packaging defect repair authorized by
> the 2026-10-03 strategy scope decision (recorded in the 079-2-b order
> Section 2), with the corrected closed file list produced by an unscoped
> repository inventory. The coding agent executes under the normal OAP
> execution contract; strategy remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-2-c` (increment-qualified round ID: third round of semantic
  increment 2 of numeric Objective 079; same PR as `079-2-a`/`079-2-b`).
- Mode: CONTINUATION (same branch, same PR). CREATE_NEW_PR: no.
- PR: #93 (`079-2-a: Gallery + LogoGrid media-reference list components
  (079/2)`), branch `oap/079-2-a-gallery-logogrid`, base `main`.
- Do not create, amend, close, or touch any other PR.

## 2. Verified current state (strategy-verified 2026-10-03 against live
GitHub and local forensics)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f` (unchanged;
  re-fetched 2026-10-03).
- PR #93 is OPEN, `mergeable: MERGEABLE` (`mergeStateStatus` is BLOCKED
  only because required checks fail at the current head). Exact remote
  head `d5c24bc0d73651558bc3654035932348070512f5` (079-2-b report-only
  commit; parent `98e3f2c7e42da7a5d69b5e9ca24ce2d42295ab42` = 079-2-b
  transcript commit; tree byte-identical to
  `b357f8c6c03078ddc3837a058b93c74b79c6f0b3` outside the transcript;
  chain to base `577509e` verified).
- 079-2-b status is BLOCKED by a strategy drafting defect: the 079-2-b
  order P1 closed file list omitted `services/backend/Dockerfile`
  (lines 6 and 36) — the identical rotated-out pin, present at base
  `577509e` (the PR #93 diff touches no Dockerfile) and on the build
  path of the `Supply-chain evidence` required check (CI run
  `37145116286`, job `111267335866`: `backend first build failed after 3
  attempts`, failure-diagnostics artifact `11281568979`). The executor's
  STOP before any implementation commit was the correct behavior under
  the 079-2-b order Section 11. Historical orders and reports are
  immutable; this order is the correction.
- Strategy performed a FULL UNSCOPED inventory 2026-10-03 at head
  `d5c24bc` (`git grep -n '3.5.8-r0' -- . ':!oap'`; the `oap/` transcript
  is immutable history and excluded by design): exactly 17 matching
  lines across exactly 6 files:

  ```text
  apps/web/Dockerfile:7
  apps/web/Dockerfile:36
  infra/nginx/Dockerfile:16
  infra/nginx/Dockerfile:17
  infra/postgres/Dockerfile:20
  infra/postgres/Dockerfile:22
  infra/postgres/Dockerfile:23
  infra/postgres/Dockerfile:25
  services/backend/Dockerfile:6
  services/backend/Dockerfile:36
  supply-chain/policy.json:127
  supply-chain/policy.json:131
  supply-chain/policy.json:136
  supply-chain/policy.json:138
  supply-chain/policy.json:143
  tests/packaging/test_oci_contract.py:80
  tests/packaging/test_oci_contract.py:82
  ```

- Why all six files are mandatory: (1) `tools/supply_chain/policy.py`
  enforces that every `alpine_package_overrides` install package appears
  verbatim as `'<package>'` in the corresponding Dockerfile and raises
  `PolicyError` on drift, so `supply-chain/policy.json` (lines 127, 131,
  136, 138, 143 — the `alpine_package_overrides.images` install entries
  for backend, nginx, postgres, web) MUST be updated atomically with the
  four Dockerfiles; (2) `tests/packaging/test_oci_contract.py`
  (`test_postgres_overlay_is_exact_and_does_not_rebuild_postgres`, lines
  80 and 82) asserts the pinned strings in `infra/postgres/Dockerfile`
  and would fail against the bumped pin; (3) `infra/postgres/Dockerfile`
  lines 23 and 25 are exact-installed-version assertions and must read
  `3.5.9-r0` after the bump. `infra/apache/Dockerfile` and
  `services/browser-worker/Dockerfile` contain no `libcrypto`/`libssl`
  pin or apk line at all (verified at `d5c24bc`) and are OUT of scope.
  No file outside `oap/` mentions `3.5.8` in any other form
  (verified: a tree-wide grep for `3.5.8` excluding `oap/` matches
  exactly the 17 lines above).
- `3.5.9-r0` already resolves on BOTH Alpine base images the repository
  pins: the 079-2-b report (Criterion 2) records both apk probes rc=0 —
  node base `node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5`
  and python base
  `python:3.12.12-alpine3.23@sha256:2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0`
  — with exact outputs in that report.
- Required-check states at head `b357f8c` (CI run `37145116286`, CodeQL
  run `37145116350`; observed 2026-10-03): 18 SUCCESS, 2 FAILURE
  (`Compose and edge packaging` on `infra/nginx/Dockerfile` lines
  16-17; `Supply-chain evidence` on `services/backend/Dockerfile`) —
  both the documented pin. Acceptance under this order is based solely
  on the NEW head produced by this round.

## 3. Strategic context

- The 079-2-a implementation (R1-R8 of that order) was independently
  verified by strategy on 2026-10-03: catalog 31 with exact Gallery /
  LogoGrid R1 contracts; exact bounded error-key vocabulary
  `{gallery,logogrid}.{item-missing,item-foreign-site,item-not-image,
  items-out-of-range}`; fail-closed trusted renderers with no JS, no
  event handlers, no inline styles, no sandbox/target; OpenAPI delta
  exactly four changed `x-slaif-*` values and exactly five new property-
  scope entries (63 -> 68 / 62 -> 67) with strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  verified identical at base and head; in-place `060_001` regeneration
  limited to the two-line baked-catalog pair; lockfiles, workflows,
  supply-chain files, and migrations untouched; full local evidence set
  green.
- The only unsatisfied acceptance item of 079/2 is Criterion 9 (all 20
  required checks green), blocked solely by the externally forced Alpine
  pin rotation. No product defect was found in review. This round
  completes the authorized packaging repair with the corrected closed
  scope; it adds no semantic content.

## 4. Bounded scope (exactly)

- P1: replace the exact string `3.5.8-r0` with `3.5.9-r0` in exactly the
  17 lines of the closed Section 2 list (six files). No other pin,
  package, base image, policy section, test, or file change of any
  kind.
- P2: resolution evidence: cite the two apk probes already recorded in
  the 079-2-b report (Criterion 2; both base images, both rc=0) as the
  prior P2 evidence in this round's report. A re-run is optional; if
  performed, record the fresh output instead.
- P3: force fresh image builds for ALL FOUR affected images (web,
  nginx, backend, postgres) — no stale local-cache reuse of images built
  from the old pin — then run the FULL Compose smoke (`sh
  tools/compose/smoke.sh <project>`, all 13 projects) to rc=0 with the
  key lines recorded.
- P4: push the branch; the final head must have ALL 20 required checks
  SUCCESS (in particular `Compose and edge packaging` and `Supply-chain
  evidence` must flip green).
- P5: publish the round report (see Section 9) as a report-only commit
  (`Report publication commit: SELF`) on the same branch.

## 5. Explicit non-goals

- No change to any other pin, base image, or Dockerfile content.
  `infra/apache/Dockerfile` and `services/browser-worker/Dockerfile`
  contain no `libcrypto`/`libssl` pin (verified) and MUST NOT be
  touched.
- No change to any other section of `supply-chain/policy.json`
  (`scanner_tools`, `oci_sources`, `ubuntu_package_overrides`,
  `browser_runtime`, or any other key).
- No change to any test other than the two assertion lines of
  `tests/packaging/test_oci_contract.py` (lines 80 and 82).
- No product code, configuration, migration, lockfile, workflow, or
  supply-chain file change of any kind beyond P1; no current-truth
  documentation changes (the five R5 surfaces remain accurate; the pin
  repair is not an increment-level documentable fact).
- No version other than `3.5.9-r0` (no `3.6.x`, no unversioned pin, no
  index-pinning workaround). If the pre-edit inventory deviates from the
  closed 17-line list, if `3.5.9-r0` fails resolution, if the smoke
  fails for a new-pin reason, or if any other failure class appears:
  STOP and report BLOCKED with the exact evidence; do not improvise
  alternatives.
- Do not touch dependabot PRs. Do not merge. Do not edit the committed
  079-2-a and 079-2-b orders, their reports, or any other OAP
  transcript file; `active` is replaced by this order per protocol.

## 6. Requirements

### R1 - Full-scope pin bump with inventory proof (P1 + P2)

1. PRE-EDIT: run `git grep -n '3.5.8-r0' -- . ':!oap'` from the
   repository root at the round-start tree (or an equivalent unscoped
   grep of the working tree excluding `oap/`) and record the exact
   output; it must be exactly the 17 lines of Section 2. If it deviates
   in any way, STOP and report BLOCKED before editing anything (a line
   not in the closed list is never edited by this order).
2. Apply exactly the 17 line replacements of P1.
3. POST-EDIT: re-run the identical unscoped grep and record the output;
   it must contain ZERO matches (record the empty output and the
   non-zero exit status as proof).
4. Run `uv run --frozen python tools/check_repository.py` (repository
   policy; must PASS — it validates the policy/Dockerfile consistency
   this bump depends on) and record the result.
5. Run the targeted unit tests
   `uv run --frozen pytest tests/packaging/test_oci_contract.py
   tests/supply_chain/test_policy.py -q` and record the result (must
   pass).
6. Record the P2 citation (079-2-b report, Criterion 2, both base
   images) in the report.

### R2 - Fresh builds + full smoke (P3)

Invalidate/avoid reuse of locally cached images built from the old pin
for the web, nginx, backend, and postgres images, rebuild all four, and
run the full Compose smoke (13 projects) to rc=0. The smoke log must
show the affected images being (re)built (not served from cache) and
the exact key lines: `compose-e2e: OK projects=13 ...`, `media-e2e: OK
...`, `public-agent-acceptance: OK ...`, `compose-smoke: OK`.

### R3 - Push and CI (P4)

Push the implementation commit(s) of this round to the same branch.
Verify (and report) that ALL 20 required checks reach SUCCESS on the
exact final head. If a required check fails for an in-scope reason,
repair within this round's scope, push, and re-verify; the final head
is the acceptance head. No CI re-run is permitted for an unmodified
head (flake policy); a new pushed head supersedes.

### R4 - Report (P5)

Publish `oap/reports/079-2-c-alpine-pin-repair.md` as a report-only
commit (SELF) whose parent is this round's implementation head.

## 7. Acceptance criteria (observable)

Let T = this round's transcript commit (order + `oap/active` bytes
only), I = this round's implementation head, S = the report-only
commit.

1. `git diff --name-only T..I` lists exactly the six P1 files, and
   `git diff --stat T..I` shows exactly 17 changed lines total.
2. `git diff --name-only d5c24bc..I` lists exactly eight files: the six
   P1 files plus `oap/orders/079-2-c-alpine-pin-repair.md` and
   `oap/active`.
3. The pre-edit (17-line) and post-edit (zero-line) unscoped grep
   outputs, the `tools/check_repository.py` PASS, and the targeted
   pytest result are recorded in the report.
4. The P2 citation of the 079-2-b probes (both base images) is in the
   report.
5. Fresh-build evidence for the four affected images plus the full
   smoke rc=0 key lines are recorded in the report.
6. All 20 required checks SUCCESS on the exact report-only head S
   (per-check table with CI/CodeQL run IDs; `Compose and edge
   packaging` and `Supply-chain evidence` included).
7. S changes only `oap/reports/079-2-c-alpine-pin-repair.md`; its
   parent is I; the remote PR head equals S; and
   `git diff --name-only d5c24bc..S` lists exactly nine files (the
   eight of criterion 2 plus the report).
8. Status is COMPLETE only if every criterion above is evidenced;
   otherwise BLOCKED/PARTIAL with the exact gap.

## 8. Verification and workflow

- Commit the strategy-published order and `oap/active` bytes exactly
  (blob sha256 verified against the published files) as the
  transcript-only commit T before the implementation commit I; then the
  report-only commit S. One round, one implementation commit (or the
  minimal set of in-scope repair commits); no merge by the executor.
- Local, in order: pre-edit unscoped grep (R1.1); the 17 line
  replacements (R1.2); post-edit unscoped grep (R1.3); `uv run
  --frozen python tools/check_repository.py` (R1.4); targeted pytest
  (R1.5); fresh image builds + `sh tools/compose/smoke.sh <project>`
  full smoke (R2); `npx --yes markdownlint-cli2@0.23.2` on the report
  file (zero issues).
- Push, then poll required checks on the exact head until all are
  terminal; report the per-check table with run IDs.
- GitHub workflow: push to the existing branch only.

## 9. Report requirements

`oap/reports/079-2-c-alpine-pin-repair.md` must state: identifier and
mode (CONTINUATION, PR #93); the work-order sha256 (computed over the
published file); exact transcript commit T, round implementation head
I, and report SELF; the 17-line diff (file:line per site); the pre-edit
and post-edit unscoped grep outputs; the `tools/check_repository.py`
PASS and targeted pytest evidence; the P2 citation of the 079-2-b
probes (both base images, exact outputs already in the 079-2-b report);
the fresh-build evidence and full smoke key lines; the complete
20-check per-check table at the exact report-only head S with run IDs;
the cumulative base->head size table per the 2026-09-14 review-unit
governance (base `577509e` -> final head, grouped: production/config,
migrations, tests/evidence, generated artifacts, docs, OAP transcript;
state that the review trigger is not crossed: cumulative
production/config 15 files / ~549 substantive lines); confirmation that
no product code changed this round; and an honest status (COMPLETE iff
all Section 7 criteria are evidenced).

## 10. Predeclared review budget (2026-09-14 review-unit governance)

- Production/config: 5 files (the four Dockerfiles +
  `supply-chain/policy.json`), 15 substantive lines.
- Tests/evidence: 1 file (`tests/packaging/test_oci_contract.py`), 2
  lines. Migrations: 0. Generated artifacts: 0. Docs: 0.
- OAP transcript: this order + one new round report + `active`
  replacement.
- Cumulative after this round (base `577509e` -> final head): 43 files,
  ~+4190/-90 (approximate predeclared estimate; the exact final table
  belongs in the report), production/config 15 files / ~549
  substantive lines; the ~20-30 implementation-file /
  several-thousand-line review trigger is NOT crossed; CLOSURE_ONLY
  does not begin.

## 11. Review-unit governance (2026-09-14 amendment, in force)

This round completes the finite packaging defect repair inside the
079/2 review unit per the 2026-10-03 strategy scope decision recorded
in the 079-2-b order Section 2. No new semantic family, no adjacent
feature, no opportunistic scope. The 079-2-b round is an immutable
BLOCKED record caused by a strategy drafting defect (incomplete P1 file
list); its evidence (both apk probes, CI forensics) is adopted by this
order. If the pre-edit inventory deviates from the closed list, if
`3.5.9-r0` fails, or if any other failure class appears: stop and
report BLOCKED with the exact evidence; strategy decides the next step.

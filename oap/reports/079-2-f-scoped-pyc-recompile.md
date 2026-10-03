# OAP Coding-Agent Report — 079-2-f

## Work order

- Identifier: 079-2-f (increment-qualified round ID: sixth round of
  semantic increment 2 of numeric Objective 079, increment 079/2)
- Work-order file:
  `oap/orders/079-2-f-scoped-pyc-recompile.md`
- Work-order sha256 (file-hash domain, computed over the published file):
  `22c0016bfc5327010c28feb34a65073ccd405429c968252d2e4ebf8a2616d0d4`
  (git blob ID of the committed file: `fd3dfd8ea1c8f1905941212c508a6a8b71833e3f`;
  different hash domains, byte-identical commit)
- `oap/active` bytes: `079-2-f\n` (hex `3037392d322d660a`)
- Numeric objective: 079 (increment 079/2; this round = the retry of the
  079-2-e candidate fix with the scope corrected to
  `compileall -q -f /build/.venv/lib` per the recorded decision path of
  order §3)
- PR mode: AMENDED_EXISTING_PR (PR #93; implementation amended:
  `services/backend/Dockerfile` +1 line,
  `tests/packaging/test_oci_contract.py` +2 lines)

## Status

BLOCKED

## Executive summary

The binding P1 proof gate (order §3/§4: "P1 PROVES the corrected-scope fix
locally ... BEFORE any repository change") was executed exactly as specified
with ZERO repository changes and — for the first time in the 079-2 series —
met EVERY stated expectation. P1.1 (fresh baseline at C): two `--no-cache`
backend builds byte-identical in the target pyc (97723 bytes, sha256
`49bb1bc8...`, constant `co_filename`) with 2821/2821 manifest entries and 0
differences. P1.2 (out-of-tree corrected-scope experiment, one added
`compileall -q -f /build/.venv/lib` line): (a) constant `co_filename` in
both fix builds, (b) byte-identical pycs (in fact byte-identical to both
baseline pycs — all four builds identical), (c) exactly 2821 entries in both
fix manifests (file-count neutral, proving the corrected scope compiles
exactly the set `uv` already compiled), (d) fix-vs-fix 0/0/0, (e)
fix-vs-baseline 0/0/0 including zero byte differences on pre-existing
entries. P2 then applied the exact two-file, three-line change (pre-edit
three-line / post-edit five-line grep gates met); R2 gates passed
(`check_repository.py` PASS, 86 pytest passed + 54 subtests, ruff clean);
P3 forced fresh builds of all five affected images and the full 13-project
Compose smoke reached rc=0; P4 pushed the implementation head I.

CI at the exact final head I: 19 of 20 required checks SUCCESS.
`Supply-chain evidence` FAILED, but in a NEW failure class, not the named
one: `browser-worker: unexcepted Critical vulnerabilities` — 24 newly
published Critical CVEs against the pinned, SHA-256-verified Chrome for
Testing `153.0.8010.52` (CfT revision 1681091) in the browser-worker image,
reported 28 seconds after the job's grype vulnerability database updated to
latest (log line 2440, 22:11:10.3374658Z; error line 2441,
22:11:38.2007452Z). The named defect of this review unit —
`backend: normalized application-file drift` — is FIXED and CI-proven at I:
the job log contains zero `drift` occurrences, and the failure artifact's
retained double-build rootfs manifests show 0 only_first / 0 only_second / 0
field differences for every image pair (backend 2821/2821; web 3052/3052;
nginx 1/1; postgres 1/1; apache 199/199; browser-worker 481/481).

Per order §3 ("If `Supply-chain evidence` fails at this round's final head
in ANY form: P5 STOP + BLOCKED + escalation"), §4 P5, and §11 ("No second
fix attempt is permitted this round under any outcome"), the executor
executed P5 (downloaded and verified the failure-diagnostics artifact and
produced the exact file-level diff from it) and STOPPED. This round reports
BLOCKED with that evidence and an explicit escalation. No second fix
attempt was made; no `tools/supply_chain/*`, boundary, contract, or other
Dockerfile was touched; the reproducibility gate was not weakened in any
way.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#93](https://github.com/ulfe-lmi/slaif-agent-site/pull/93), state
  OPEN (`mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED` on the failing
  required check)
- Base/head branches: `main` <- `oap/079-2-a-gallery-logogrid`
- Base `main`: `577509e7bc990d85a10af5954bee3c6f7c888a4f` (unchanged)
- Round-start remote SHA C (079-2-e report-only commit; parent
  `7743478da7773af883fa5959557c5bd7d77585d8`):
  `2c642fec18ece0bd60a32146e2950cb4b850d13c`
- Transcript commit T (order + `active` bytes only, 2 files; parent C):
  `8340fc03dc751ccbdb19fa7e5b5d40eb3f76b19a`
- Implementation head SHA I (pushed; verified as the remote branch head):
  `0f5186e863f4c13e4119309109d2420c3b803b60`
- Report publication commit: SELF (first parent = I)
- Remote PR head after report publication: SELF
- New PR this turn: no; merge performed: NO

## Changes made

1. Transcript commit T: strategy-published order and `oap/active` bytes
   committed exactly (order file sha256
   `22c0016bfc5327010c28feb34a65073ccd405429c968252d2e4ebf8a2616d0d4`
   verified on the published file; git blob ID
   `fd3dfd8ea1c8f1905941212c508a6a8b71833e3f` on the committed blob;
   active bytes `079-2-f\n` = hex `3037392d322d660a` verified on the
   committed blob).
2. Implementation commit I: exactly the two-file, three-line change of
   order §4 P2 (verbatim below).
3. This report (via the SELF report-only commit, parent I).

### Exact three-line diff (T..I)

```diff
diff --git a/services/backend/Dockerfile b/services/backend/Dockerfile
index 10a6b49..e6eaa5a 100644
--- a/services/backend/Dockerfile
+++ b/services/backend/Dockerfile
@@ -20,4 +20,5 @@ RUN uv sync --frozen --no-default-groups --no-editable \
     && rm -- "$1/uv_cache.json" \
     && sed -i '\|slaif_agent_site-.*\.dist-info/uv_cache\.json,|d' "$1/RECORD"
+RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib

 # Keep the readable version beside the immutable top-level multi-architecture digest.
diff --git a/tests/packaging/test_oci_contract.py b/tests/packaging/test_oci_contract.py
index 6019efc..98d0f2c 100644
--- a/tests/packaging/test_oci_contract.py
+++ b/tests/packaging/test_oci_contract.py
@@ -65,4 +65,6 @@ class OciContractTests(unittest.TestCase):
     def test_backend_runtime_uses_only_frozen_production_environment(self) -> None:
         content = (ROOT / "services/backend/Dockerfile").read_text(encoding="utf-8")
+        builder = content.split(" AS runtime", maxsplit=1)[0]
+        self.assertIn("compileall -q -f /build/.venv/lib", builder)
         self.assertIn("uv sync --frozen --no-default-groups --no-editable", content)
         runtime = content.split(" AS runtime", maxsplit=1)[1]
```

Per site (file:line, at I):

- `services/backend/Dockerfile:22`
  (`RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib`) —
  immediately after the `uv sync` RUN chain (the `sed -i ... "$1/RECORD"`
  line), as ordered.
- `tests/packaging/test_oci_contract.py:67`
  (`builder = content.split(" AS runtime", maxsplit=1)[0]`) and
  `tests/packaging/test_oci_contract.py:68`
  (`self.assertIn("compileall -q -f /build/.venv/lib", builder)`) — inside
  `test_backend_runtime_uses_only_frozen_production_environment`,
  immediately after the `content = ...` line, as ordered.

## Files changed

- `git diff --name-only C..T` = exactly two files:
  `oap/orders/079-2-f-scoped-pyc-recompile.md` + `oap/active`
  (transcript only).
- `git diff --name-only T..I` = exactly two files
  (`services/backend/Dockerfile`, `tests/packaging/test_oci_contract.py`);
  `git diff --numstat T..I` = `1 0` + `2 0` (three added lines, zero
  deleted).
- `git diff --name-only I..SELF` = exactly one file: this report.
- `git diff --name-only C..SELF` = exactly five files: the two transcript
  files + the two implementation files + this report. Worktree clean.

## Acceptance-criteria evidence

### Criterion 1 (T..I = exactly two files / three added lines)

MET. `git diff --name-only T..I` lists exactly
`services/backend/Dockerfile` and `tests/packaging/test_oci_contract.py`;
`git diff --numstat T..I` = `1 0` (Dockerfile) and `2 0` (test file) —
exactly three added lines, zero deleted.

### Criterion 2 (C..I = exactly four files)

MET. `git diff --name-only C..I` lists exactly:
`oap/orders/079-2-f-scoped-pyc-recompile.md`, `oap/active`,
`services/backend/Dockerfile`, `tests/packaging/test_oci_contract.py`.

### Criterion 3 (complete P1 evidence recorded)

MET — see "Local verification" below: P1.1 commands, both pyc
sha256/size/`co_filename`, both manifests (2821/2821, 0 differences); P1.2
commands, both fix-build pyc sha256/size/`co_filename` (byte-identical, and
byte-identical to both baseline pycs), both fix manifests (2821 entries
each, fix-vs-fix 0/0/0), and the fix-vs-baseline comparison (0 only_first,
0 only_second, 0 pre-existing-entry byte differences). All stated
expectations (P1.1, P1.2(a)-(e)) were met; no deviation; P1.3 gate passed.

### Criterion 4 (pre/post grep, check_repository, pytest, ruff)

MET — see "Local verification" below: pre-edit grep = exactly the three
strategy-verified lines; post-edit grep = exactly those three plus the two
new lines; `check_repository.py` PASS; `86 passed, 54 subtests passed`;
ruff check clean, ruff format clean.

### Criterion 5 (fresh-build evidence for all five images + full smoke)

MET — see "Local verification" below: stale local images deleted, all five
affected images freshly built in the smoke, rc=0, key lines recorded; the
apache edge image's apt layer was layer-cached because
`infra/apache/Dockerfile` is unchanged this round (out of P2 scope), with
the real `openssl=3.0.13-0ubuntu3.16` transaction provenance cited from the
retained 079-2-d smoke log (noted explicitly, as evidence).

### Criterion 6 (all 20 required checks SUCCESS at the exact report-only
head S — OR the P5 BLOCKED branch)

The FAILURE branch applies at implementation head I: 19 of 20 SUCCESS,
`Supply-chain evidence` FAILURE — see "GitHub CI / required checks" and the
P5 forensics below. The P5 file-level diff from the artifact shows
0/0/0 for every image pair (the named backend drift is fixed and
CI-proven at I); the failure is a NEW external class (24 newly published
Critical CVEs in the browser-worker's pinned Chrome for Testing
153.0.8010.52). Honest BLOCKED per order §3/§4 P5/§11, with explicit
escalation. No second fix attempt was made (forbidden by order §4 P5/§11).
Criterion 6's SUCCESS form is NOT satisfied; note the required checks run
against I, which is the exact final implementation head of this round (S
adds only this report and, per the flake policy and order §5, no CI
re-run of an unmodified head is permitted; S does not change any checked
artifact).

### Criterion 7 (S report-only; parent rule; remote head S; C..S file
count)

To be evidenced at publication: S changes only this report; its first
parent is I; the remote PR head equals S; `git diff --name-only C..S` lists
exactly five files (verified before the response signal).

### Criterion 8 (honest status)

BLOCKED. Criteria 1-5 and 7 are (will be) evidenced; criterion 6 is
satisfied only in its FAILURE form at the exact final head, so per §7.8 the
status is BLOCKED with the exact gap stated.

## Local verification

### P1.1 — fresh baseline at C (local only, ZERO repository changes)

- Build context: clean `git archive` of C extracted to
  `/tmp/0792f-base-tree` (no repository files touched).
- Two builds, exact gate build arguments of
  `tools/supply_chain/run.sh` `build_image`, identical except tag:

  ```bash
  docker build --pull --no-cache \
    --build-arg SOURCE_DATE_EPOCH=1704067200 \
    --build-arg SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z \
    --build-arg SLAIF_IMAGE_REVISION=2c642fec18ece0bd60a32146e2950cb4b850d13c \
    --build-arg SLAIF_IMAGE_VERSION=0.0.0 \
    --file services/backend/Dockerfile \
    -t 0792f-base-first:local .   # second build: -t 0792f-base-second:local
  ```

  Logs: `/tmp/0792f/build-base1.log`, `/tmp/0792f/build-base2.log`
  (both rc=0).
- Extraction (gate's exact commands): `docker container create` +
  `docker container export` per image, then
  `uv run --frozen python -m tools.supply_chain.evidence rootfs-manifest
  --archive <export> --image-name backend`.
- RESULTS (every stated expectation MET):
  - Manifests: first build 2821 entries, second build 2821 entries;
    only_first 0, only_second 0, common 2821, field differences 0.
  - Target pyc
    `opt/slaif/.venv/lib/python3.12/site-packages/pycparser/__pycache__/c_parser.cpython-312.pyc`
    in BOTH builds: 97723 bytes, sha256
    `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`,
    16-byte header hex `cb0d0d0a03000000c80402aeef6d647c`,
    `co_filename = /build/.venv/lib/python3.12/site-packages/pycparser/c_parser.py`
    (identical in both).

### P1.2 — corrected-scope fix experiment, OUT OF TREE

- Context: clean `git archive` of C to `/tmp/0792f-fixexp`; in that copy
  ONLY, exactly one line added to `services/backend/Dockerfile` immediately
  after the `sed -i ... "$1/RECORD"` line (new builder step 9/9):
  `RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib`.
- Two `--no-cache` builds with the identical arguments (same
  `SLAIF_IMAGE_REVISION=C`), tags `0792f-fix-first:local` /
  `0792f-fix-second:local`; logs `/tmp/0792f/build-fix1.log` (the new step
  visible: `#17 [builder 9/9] RUN /build/.venv/bin/python -m compileall -q -f
  /build/.venv/lib`, `#17 DONE 8.4s`) and `build-fix2.log` (both rc=0).
- RESULTS (every stated expectation MET):
  - (a) both fix-build pycs have
    `co_filename = /build/.venv/lib/python3.12/site-packages/pycparser/c_parser.py`
    — constant across builds.
  - (b) the two fix pycs are byte-identical: 97723 bytes, sha256
    `49bb1bc88a0afd15aec16d2c953670e27c7b4b39a121322f4943f26f19ec83bc`
    (identical header hex as P1.1). In fact ALL FOUR pycs (baseline x2,
    fix x2) are byte-identical.
  - (c) both fix manifests have exactly 2821 entries — the SAME count as
    P1.1: the corrected scope is file-count neutral (it compiles exactly
    the set `uv` already compiled, per strategy's rootfs verification of
    1040 `.py`/1040 `.pyc` under `.venv/lib`).
  - (d) fix1-vs-fix2: 0 only_first, 0 only_second, 0 field differences.
  - (e) fix-vs-P1.1-baseline (both pairing directions): 0 only_first,
    0 only_second; pre-existing-entry byte-diff count = 0.
- P1.3 record: all commands, hashes, sizes, `co_filename` values, entry
  counts, and diff counts are recorded above and in `/tmp/0792f/`
  (retained: `build-*.log`, `<tag>.rootfs.tar`, `<tag>.c_parser.pyc`,
  `<tag>.files.json`, `pyc-info.py`, `manifest-diff.py`,
  `base-dockerfile.txt`). NO deviation from any stated expectation -> P2
  authorized.

### P2 + R2 gates (at I)

- PRE-EDIT grep (at C, `git grep -n 'compileall' C -- . ':!oap'`, rc=0) —
  exactly the three strategy-verified pre-existing lines:

  ```text
  .github/workflows/ci.yml:33:          python -m compileall -q
  AGENTS.md:260:python -m compileall -q tools tests/repository
  CONTRIBUTING.md:67:python -m compileall -q tools tests/repository tests/packaging tests/supply_chain
  ```

- POST-EDIT grep (at I, identical command shape, rc=0) — exactly five
  lines: the three above plus the two new lines:

  ```text
  services/backend/Dockerfile:22:RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib
  tests/packaging/test_oci_contract.py:68:        self.assertIn("compileall -q -f /build/.venv/lib", builder)
  ```

- `uv run --frozen python tools/check_repository.py` ->
  `PASS repository policy` (rc=0)
- `uv run --frozen pytest tests/packaging/ tests/supply_chain/ -q` ->
  `86 passed, 54 subtests passed` (rc=0)
- `uv run --frozen ruff check` -> `All checks passed!`
- `uv run --frozen ruff format --check` (touched test path) ->
  `1 file already formatted`

### P3 — fresh builds of all five affected images + full smoke

- Stale local images deleted first: `docker rmi` of
  `slaif-agent-site-{web,nginx,backend,postgres}:local` and
  `slaif-agent-site-apache:test` (5 images).
- `sh tools/compose/smoke.sh slaif0079f` -> rc=0; log
  `/tmp/0792f-smoke-1.log` (1249 lines; final line `compose-smoke: OK`).
- Fresh-build naming lines (all five images built fresh in this run):
  `#35 naming to docker.io/library/slaif-agent-site-browser-worker:local 0.0s done`
  (line 237), `#46 ... postgres:local ... done` (246),
  `#61 ... web:local ... done` (257), `#62 ... nginx:local 0.1s done`
  (267), `#73 naming to docker.io/library/slaif-agent-site-backend:local done`
  (321).
- The new backend step EXECUTED fresh in the smoke build:
  `#24 [secrets-init builder 9/9] RUN /build/.venv/bin/python -m compileall -q -f /build/.venv/lib`
  (lines 90/283/293) with `#24 DONE 7.9s` (line 294) — no layer cache for
  the step.
- Apache edge image (honesty note): `#6 [2/4] RUN apt-get update && apt-get
  install ... 'openssl=3.0.13-0ubuntu3.16' ...` shows `#6 CACHED` (line
  1219-1221), with `#7 CACHED`, `#8 CACHED`, then
  `#9 naming to docker.io/library/slaif-agent-site-apache:test done`
  (line 1235) and `apachectl -t` -> `Syntax OK`. This round changed
  `infra/apache/Dockerfile` in NO way (order §5: the only Dockerfile change
  permitted is `services/backend/Dockerfile`), so BuildKit layer reuse of
  the 079-2-d apt layer is the correct build behavior; the REAL apt
  transaction for that layer (exact pin `openssl=3.0.13-0ubuntu3.16`) is
  retained at `/tmp/0792d-smoke-1.log` line 1202 (the `#6 [2/4] RUN apt-get
  ...` command), line 1407 (`#6 24.58 Unpacking openssl
  (3.0.13-0ubuntu3.16) ...`) and line 1430 (`#6 25.85 Setting up openssl
  (3.0.13-0ubuntu3.16) ...`). This smoke log contains ZERO
  `Unpacking`/`Setting up` lines.
- Key OK lines: `compose-e2e: OK projects=13 setup=1 governance=1
  preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2
  media-publication=1 artifacts=disabled` (line 864);
  `public-agent-acceptance: OK workspace=519f4df2-0aba-4c12-93a5-09ebe6e64e16 ...
  render-restart=verified` (line 867); `media-e2e: OK edge=nginx
  upload=validated-private-read=byte-identical finalization=public-read=byte-identical
  immutable-cache=verified` (line 870); `compose-smoke: OK` (line 1249).

## GitHub CI / required checks

At the exact final implementation head I
`0f5186e863f4c13e4119309109d2420c3b803b60`: CI run `37156984390` (started
2026-10-03T22:00:32Z; conclusion failure) + CodeQL run `37156984426`
(conclusion success). Terminal: 19 SUCCESS, 1 FAILURE.

| Required check | State (head 0f5186e) |
|---|---|
| Analyze (actions) | SUCCESS (CodeQL 37156984426, job 111302287813, 2m1s) |
| Analyze (javascript-typescript) | SUCCESS (CodeQL 37156984426, job 111302287800, 1m9s) |
| Analyze (python) | SUCCESS (CodeQL 37156984426, job 111302287786, 4m24s) |
| CodeQL | SUCCESS (CodeQL 37156984426, run-level) |
| Compose and edge packaging | SUCCESS (CI 37156984390, job 111302265866, 11m28s) |
| Dependency review | SUCCESS (CI 37156984390, job 111302265906, 8s) |
| Detect supported languages | SUCCESS (CodeQL 37156984426, job 111302266042, 5s) |
| Foundation PostgreSQL 14 | SUCCESS (CI 37156984390, job 111302266022, 13m20s) |
| Foundation PostgreSQL 15 | SUCCESS (CI 37156984390, job 111302266816, 11m40s) |
| Foundation PostgreSQL 16 | SUCCESS (CI 37156984390, job 111302266058, 12m49s) |
| Foundation PostgreSQL 17 | SUCCESS (CI 37156984390, job 111302265984, 11m41s) |
| Foundation PostgreSQL 18 | SUCCESS (CI 37156984390, job 111302266050, 6m40s) |
| Markdown | SUCCESS (CI 37156984390, job 111302265942, 11s) |
| Mermaid | SUCCESS (CI 37156984390, job 111302265882, 38s) |
| Node contracts | SUCCESS (CI 37156984390, job 111302265894, 2m34s) |
| Python 3.12 quality and package | SUCCESS (CI 37156984390, job 111302266038, 50s) |
| Python 3.13 quality and package | SUCCESS (CI 37156984390, job 111302265952, 45s) |
| Python 3.14 quality and package | SUCCESS (CI 37156984390, job 111302265900, 37s) |
| Repository policy | SUCCESS (CI 37156984390, job 111302265884, 9s) |
| Supply-chain evidence | FAILURE (CI 37156984390, job 111302265733, 11m11s — NEW failure class: `browser-worker: unexcepted Critical vulnerabilities` (24 newly published CVEs on the pinned Chrome for Testing 153.0.8010.52); the named `backend: normalized application-file drift` did NOT recur (zero drift log lines; artifact double-build manifests 0/0/0) — see P5 forensics) |

### P5 forensics (executed per order §4 P5; STOP after this)

- Job log retained at `/tmp/0792f-cisupply.log` (2493 lines). ZERO
  occurrences of `application-file drift` or `package drift` anywhere in
  the log (contrast: the three prior CI occurrences all named
  `backend: normalized application-file drift`); the backend stage
  completed and the job proceeded to the browser-worker scan.
- The failure, verbatim (log line 2441, 2026-10-03T22:11:38.2007452Z),
  immediately after the grype database update (log line 2440,
  2026-10-03T22:11:10.3374658Z: `Vulnerability database updated to latest
  version!` — 28 seconds earlier):

  ```text
  supply-chain-evidence: ERROR: browser-worker: unexcepted Critical vulnerabilities: CVE-2026-102304, CVE-2026-102306, CVE-2026-102308, CVE-2026-102309, CVE-2026-102316, CVE-2026-102331, CVE-2026-95277, CVE-2026-95281, CVE-2026-95283, CVE-2026-95284, CVE-2026-95299, CVE-2026-95310, CVE-2026-95311, CVE-2026-95313, CVE-2026-95318, CVE-2026-95325, CVE-2026-95329, CVE-2026-95331, CVE-2026-95339, CVE-2026-95347, CVE-2026-95349, CVE-2026-95350, CVE-2026-95356, CVE-2026-95357
  ```

- Failure-diagnostics artifact (079-2-d diagnostics extension; uploaded
  2026-10-03T22:11:41-43Z per log lines 2466-2475): name
  `supply-chain-failure-diagnostics-2014695097249988e72a6591973de29a7424c8ca`,
  final size 11255059 bytes, upload SHA-256 digest
  `1f83e29824afbbb447bc6a1738f92d6ae4c3bd5e32db500ac3fd9a379e08949c`,
  artifact ID `11285803229`, download URL
  `https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/37156984390/artifacts/11285803229`.
  Downloaded to `/tmp/0792f-diag/`; `sha256sum -c SHA256SUMS` -> all 37
  diagnostic files OK (38 entries with `SHA256SUMS`).
- `STATUS.json`: `status: INCOMPLETE`, `qualification: UNQUALIFIED`,
  `success_manifest: ABSENT`, `original_exit_status: 1`,
  `omitted_files: []` — the artifact retains BOTH builds' rootfs file
  manifests for all six images (as the 079-2-d extension guarantees).
- P5 file-level diff from the artifact (gate manifest format; first build
  vs second build, per image):

  | Image | Entries (first/second) | only_first | only_second | field differences |
  |---|---|---|---|---|
  | backend | 2821/2821 | 0 | 0 | 0 |
  | web | 3052/3052 | 0 | 0 | 0 |
  | nginx | 1/1 | 0 | 0 | 0 |
  | postgres | 1/1 | 0 | 0 | 0 |
  | apache | 199/199 | 0 | 0 | 0 |
  | browser-worker | 481/481 | 0 | 0 | 0 |

  -> the named `backend: normalized application-file drift` defect is
  FIXED and CI-proven at I: no manifest-level or drift-level difference of
  any kind exists between the two CI builds.
- Root-cause classification of the FAILURE (external, new class): the 24
  unexcepted Critical CVEs are all against a single artifact in the
  browser-worker image — `chrome==153.0.8010.52` (per the artifact's
  `browser-worker.raw.grype.json`: all 24 Critical matches map to
  `chrome` version `153.0.8010.52`). That binary is the SHA-256-verified
  Chrome for Testing download pinned in
  `services/browser-worker/Dockerfile` (CfT `153.0.8010.52`, revision
  `1681091`, archive sha256
  `e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9`),
  which this order explicitly does NOT permit changing (order §5: no change
  to any Dockerfile other than `services/backend/Dockerfile`; no
  `tools/supply_chain/*` change; no second fix attempt). Grype fix-record
  example from the artifact: `CVE-2026-95350` -> fixed in
  `154.0.8037.57` (first-observed 2026-09-30). The repository's
  `supply-chain/vulnerability-exceptions.json` is currently EMPTY
  (`exceptions: []`), and `supply-chain/policy.json` has
  `fail_severities: [Critical]` with `unfixed_critical_still_fails: true` —
  i.e. none of the 24 CVEs is excepted. The browser-worker CVE
  pin/exception lifecycle (precedent: rounds 072-i/j/n) and the CfT
  version-bump decision (e.g. to a CfT release that fixes these CVEs,
  with the matching policy.json/browser-worker Dockerfile qualification)
  are strategy/human decisions, never the executor's (order §3).
- STOP executed: per order §3/§4 P5/§11 the round ends BLOCKED with this
  evidence and explicit escalation; no second fix attempt was made under
  any outcome; no CI re-run was invoked.

## Local setup / dependencies

- Docker: four P1 experiment images built
  (`0792f-base-first:local`, `0792f-base-second:local`,
  `0792f-fix-first:local`, `0792f-fix-second:local`), rootfs-exported and
  retained; five stale `:local` repository images deleted before the
  smoke; the full 13-project Compose smoke ran under project `slaif0079f`
  and all stacks were torn down by the tool.
- Evidence retained: `/tmp/0792f/` (P1: `build-base{1,2}.log`,
  `build-fix{1,2}.log`, `<tag>.rootfs.tar`, `<tag>.c_parser.pyc`,
  `<tag>.files.json`, `pyc-info.py`, `manifest-diff.py`,
  `base-dockerfile.txt`), `/tmp/0792f-smoke-1.log` (P3),
  `/tmp/0792f-cisupply.log` (P4/P5 job log), `/tmp/0792f-diag/` (P5
  artifact), `/tmp/0792d-smoke-1.log` (079-2-d apache apt provenance),
  `/tmp/0792e/` (079-2-e retained P1 artifacts, strategy-verified).
- Tooling: uv 0.12.5 (frozen), docker/buildx, `gh`; markdownlint via
  `npx --yes markdownlint-cli2@0.23.2` on this report (zero issues). No
  new packages or services. No production systems, data, or credentials
  touched; no secrets in the diff or this report.

## Documentation

- None this round (order §5 forbids any documentation change beyond P2;
  P2 is the two-file, three-line change only).

## Safety and scope confirmations

- Unrelated files changed: NO — on the remote this round changed exactly:
  T (2 transcript files), I (2 implementation files), SELF (this report).
- No product code changed this round: CONFIRMED (the two changed files are
  the ordered `services/backend/Dockerfile` build step and its packaging
  contract test; no `services/*/src` product source, migration, workflow,
  lockfile, or other file changed).
- No `tools/supply_chain/*` file changed: CONFIRMED. The reproducibility
  gate, double-build comparison, normalization logic, contract, validator,
  and application-file boundary were NOT weakened or changed in any way:
  CONFIRMED (no `.pyc` exclusion or similar was introduced anywhere).
- The compared boundary's file set is UNCHANGED: 2821 entries, no
  additions, no removals — proven locally by P1.2(c)/(e) (2821/2821,
  0/0/0 fix-vs-baseline) and in CI by the artifact double-build manifests
  (backend 2821/2821, 0/0/0 at I).
- No CI re-run invoked (flake policy; a new pushed head supersedes — and
  no further head is pushed this round: S is report-only); no merge; no
  other PR touched; dependabot PRs untouched.
- Activated order/`oap/active` edited: NO — committed byte-identical
  (order file sha256
  `22c0016bfc5327010c28feb34a65073ccd405429c968252d2e4ebf8a2616d0d4`
  verified on the published file; git blob ID
  `fd3dfd8ea1c8f1905941212c508a6a8b71833e3f` on the committed blob;
  active `079-2-f\n` = hex `3037392d322d660a` verified on the committed
  blob).
- No second fix attempt made under any outcome (order §4 P5/§11):
  CONFIRMED.
- Report commit changes only this report: verified before the response
  signal.

## Cumulative base->head size (2026-09-14 review-unit governance
Section 2)

Base `577509e7bc990d85a10af5954bee3c6f7c888a4f` -> implementation head I
`0f5186e863f4c13e4119309109d2420c3b803b60` (exact measured diff,
`git diff --numstat`: 51 files, +6452/-92; this report's own lines are
excluded, as in the prior rounds; at S the file count is 52):

| Category | Files | +lines | -lines |
|---|---|---|---|
| Production/config | 17 | 568 | 71 |
| Migrations | 0 | 0 | 0 |
| Tests/evidence | 13 | 1320 | 10 |
| Generated artifacts | 5 | 354 | 4 |
| Docs | 4 | 8 | 6 |
| OAP transcript | 12 (6 orders + active + 5 prior reports) | 4202 | 1 |

Production/config = the same 17 files as at 079-2-d, plus this round's
`services/backend/Dockerfile` +1/-1 delta (now 3/2 cumulative): 17 files /
+568 raw diff lines — exactly the order §9 predeclared "17 files / ~+568
raw lines". This round's test-file delta (+2) is in Tests/evidence (13
files / +1320/-10). The ~20-30 implementation-file / several-thousand-line
review trigger is NOT crossed; CLOSURE_ONLY does not begin. (Order §10
predeclared approx. 52 files / ~+6900/-92 at the final head; the exact
measured table above supersedes the estimate — 51 files at I / 52 at S,
+6452/-92 at I, under the estimate.)

## Known limitations / blockers

- BLOCKING (P5 branch of Criterion 6): `Supply-chain evidence` FAILED at
  the exact final implementation head I — in a NEW, external failure class
  (`browser-worker: unexcepted Critical vulnerabilities`: 24 newly
  published Critical CVEs against the pinned Chrome for Testing
  `153.0.8010.52`, surfaced after the job's grype vulnerability database
  updated mid-run; none excepted —
  `supply-chain/vulnerability-exceptions.json` is empty). The named
  `backend: normalized application-file drift` defect of the 079/2 review
  unit is FIXED and CI-proven at I (zero drift log lines; artifact
  double-build manifests 0/0/0 for all six images, backend 2821/2821).
  Per order §3/§4 P5/§11 the round ends BLOCKED with explicit escalation;
  no second fix attempt was permitted or made. The browser-worker CVE
  resolution (CfT version bump with full re-qualification of
  `services/browser-worker/Dockerfile` + `supply-chain/policy.json`
  browser_runtime pins, and/or a strategy-issued time-boxed exception per
  the 072-i/j/n precedent, `maximum_exception_days: 90`) requires a new
  strategy round and, if structural, human authorization.
- Non-blocking observation: `Criterion 6`'s SUCCESS form is evaluated on
  the exact report-only head S; S adds only this report (no checked
  artifact changes), and the order forbids CI re-runs of an unmodified
  head, so the table above (at I, the exact final implementation head) is
  the authoritative per-check record for this round.
- Observed CI state at round start C (superseded by I):
  `Supply-chain evidence` FAILURE (third drift occurrence) and
  `Foundation PostgreSQL 14` CANCELLED (2026-10-03T21:23:47Z, observed
  infra state, not executor-triggered).

## Recommended strategic follow-up

- A new bounded round for the 079/2 review unit to clear the
  `Supply-chain evidence` gate on the remaining, now-sole defect class:
  the browser-worker Critical CVEs on the pinned CfT
  `153.0.8010.52`. Options (strategy's choice, each needing its own
  bounded order and re-qualification evidence): (a) version bump of the
  browser-worker CfT pin (e.g. to the grype-attested fixing release
  `154.0.8037.57` or later, with matching `BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION`,
  archive sha256, `chromium_revision`, and `supply-chain/policy.json`
  `browser_runtime` updates plus the smoke's `chrome --version` assertion),
  or (b) a strategy-issued time-boxed exception entry (precedent:
  072-i/j/n; policy allows `maximum_exception_days: 90`) with the exact
  24 CVE IDs and expiry. NOTE for whichever round: the backend pyc
  drift defect is already fixed and CI-proven at head I, so that round
  only needs to re-verify the gate (a green `Supply-chain evidence` at a
  new head also re-confirms the drift fix end-to-end under the updated
  grype database). The reproducibility gate is never waived, and a green
  merge is never obtained by re-running until luck.

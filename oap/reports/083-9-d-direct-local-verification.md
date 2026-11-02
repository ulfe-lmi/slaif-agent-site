# OAP 083-9-d execution report: direct local verification (fresh exact-31 at clean Fd), COMPLETE with final SELF CI PENDING

## 0. Header facts

- Round: 083-9-d of unresolved numeric objective 083, semantic
  increment 083/9, mode `AMENDED_EXISTING_PR`. Status COMPLETE:
  N1 MET, N2 MET (qualified carry), N3 MET (31/31 fresh at clean
  Fd this round), N4 MET (qualified carry), N5: current
  implementation (Fd) CI qualified, final SELF six-image CI
  PENDING (fresh after the SELF push; ROOT independently
  verifies before acceptance/merge), N6 MET via this
  publication. Not accepted; not merged. No next order issued;
  ROOT directs after final SELF verification.
- Order: `oap/orders/083-9-d-direct-local-verification.md`
  (292 lines, 17597 bytes, content SHA256
  `f9f44736469916c529731547d94bfaa8dd8ca9da9e7a2d95ff185d994f01f5a9`),
  committed byte-exact at Fd and unchanged. Activated
  2026-11-02T00:28:25.837407Z with one exact control OK (2 bytes
  `4f4b`, no LF) retained by the c-round next-control reader
  (tool session 9455) to actual terminal with EOF.
- PR: `AMENDED_EXISTING_PR` #113
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>, state
  OPEN (API-verified before publication), base main
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (D18), head branch
  `oap/083-9-a-remediate-node-brotli-runtime`, worktree
  `/home/janezp/codex-work/slaif-agent-site-083-9-a`, canonical
  OAP root `/home/janezp/codex-work/slaif-agent-site/oap`.
- Round-start head: SELFc
  `d94dd953df575e0b6114530342ffbdd7210a5bb2` (c report commit,
  sole parent Fc).
- Pushed commits this round (no amend, force-push, or rebase):
  - Fd `d53035fa527993332aa420fe2aeabcaf850e744c` (transcript/
    status checkpoint: d order and active byte-exact, four
    one-line status replacements in `oap/INCREMENTS.md` and
    `oap/MVP-PROGRESS.md`; sole parent SELFc; tree
    `7fa604de9c494d8f9afecf758e127e0d6a1ac179`)
- Literal implementation SHA (Fd):
  `d53035fa527993332aa420fe2aeabcaf850e744c`.
- Report publication commit: SELF (this report; sole parent
  literal Fd `d53035fa527993332aa420fe2aeabcaf850e744c`; sole
  new path `oap/reports/083-9-d-direct-local-verification.md`).
- Execution: local 31 complete 31/31 wrapper natives 0 at clean
  Fd; source unchanged by d; Fd CI and six-image artifact
  qualified by ROOT; final SELF CI PENDING.

## 1. Source state at SELF

No product source changed in d. Twenty-six tracked paths differ
from D18 at SELF: seventeen source paths (unchanged from Fc/Fd)
plus nine transcript paths (`oap/active`, the four round
orders, the four round reports; this report is the fourth).
Source gross 586 (516+/70-) versus D18, unchanged from Fd; 25
tracked paths at Fd, 26 at SELF. All six actual image inputs,
Dockerfiles, pins, and invocations unchanged through Fc/Fd
(ROOT input-equivalence receipts).

## 2. N3: fresh exact-31 at clean Fd (this round)

Qualified anchor:
`/tmp/oap-083-9-d/qualified/run-state.json` SHA256
`703f90ae81117751f06cd8f74e8c414c9f61e751301403fd23d976ce60c66c4e`
(ROOT receipt
`/tmp/oap-083-9-d-control/root-qualified-setup-review.json`).
Setup origin/deadline recorded before any query (setup elapsed
0.941 s); immutable quality-phase origin 2193524.724227689 /
deadline 2207924.724227689 (monotonic, 14400 s, never reset);
per-command cap min(1800, floor(remaining) - 5) with
`timeout -k 5` and fail-closed on non-positive remaining;
private 0600 complete streams; actual wrapper native written
immediately per command; per-call env with `UV_PYTHON` and
`UV_PROJECT_ENVIRONMENT` bound to the approved 3.13.18 venv,
`UV_PYTHON_DOWNLOADS=never`, and PATH prefixes for the corepack
pnpm shim, Node 24.22.1, venv, and py31318 install.

Source bindings: `source_start` at Fd (branch
`oap/083-9-a-remediate-node-brotli-runtime`, head
`d53035fa527993332aa420fe2aeabcaf850e744c`, tree
`7fa604de9c494d8f9afecf758e127e0d6a1ac179`, clean); AFTERSETUP
(after command 20) OK; trueEND OK; final post-audit trueEND
receipt `source-end-final.txt` at 2026-11-02T01:08:05Z / ns
1793581685430045345 (SHA256
`692327704d29aeb1b16c6c2b09a5d9453025af02a607f56cbedeb0dc626d2949`)
again Fd and clean.

Result: 31/31 wrapper natives 0, each observed immediately.
Per-command stream bytes and SHA256 (receipts under
`/tmp/oap-083-9-d/qualified/cmd/`, one listed quality command
per exec call):

- cmd01 `uv lock --check`: 0, 28 B, `9f9cadb2af75195537da99d71320ffbe55bede59f56d46071bf5c81b0db8c0a1`
- cmd02 `uv sync --frozen --all-groups`: 0, 30 B, `611a82acebf716a701d496363051964b6c0f80179797f46f4dbe3315aa925349`
- cmd03 `uv run --frozen ruff check services/backend tests/repository tools`: 0, 19 B, `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a15b64f18`
- cmd04 `uv run --frozen ruff format --check services/backend tests/repository tools`: 0, 28 B, `6114f759b0852f5f0ec9377c2371f14298d568aae6d48b6d956b2f4c9f31333`
- cmd05 `uv run --frozen mypy`: 0, 45 B, `90b3d08a48d49cfda56180a40474c899c0f2313c87dc17c5e5de9f6893438f0`
- cmd06 `uv run --frozen pytest services/backend/tests/unit tests/repository`: 0, 10083 B, `dd3c1a71c9ad1cad3d3abd6c983098f92567374ed38d52660119d3cd3e505f08`
- cmd07 `uv build --out-dir /tmp/slaif-agent-site-distributions`: 0, 255 B, `856083db39621022586a47f1c8ca23a7abd8479cc4b15e52465e7dc3245d1628`
- cmd08 `python -m slaif_agent_site.control_api --check`: 0, 22 B, `709e2c589a8888320aa58a6ba50c4ec6c9d6144d0908e333169fecec1e86eb12`
- cmd09 `python -m slaif_agent_site.editor_api --check`: 0, 21 B, `0caeea60f6e9d603b1d9f89ff9e362fa039218d10320eb57526d48346e6af650`
- cmd10 `python -m slaif_agent_site.agent_api --check`: 0, 20 B, `bdefceeafd0693c4b0304f7d8cf572fe09abf9d56025ae1162cdcbeb0c89ef95`
- cmd11 `python -m slaif_agent_site.render_api --check`: 0, 21 B, `86fd69b6b8f9d10c2c3bd0a0bcaa7e8664122dc63b4847e29df02cbd81be95bd`
- cmd12 `python -m slaif_agent_site.mcp_adapter --check`: 0, 22 B, `0e64852337536a024565e08f83670f8cd49eaffef2b937f9d19d60d651137942`
- cmd13 `python -m slaif_agent_site.media_service --check`: 0, 24 B, `3a83984048347ec498bba3834fa0569f8901cab468c6b0d61c6e3a0266a941e8`
- cmd14 `python -m slaif_agent_site.review_worker --check`: 0, 24 B, `bb316dcdae21d0d1269b909201a98420573dd7060e8727030bd5ce5ea5038f90`
- cmd15 `python -m slaif_agent_site.scheduler --check`: 0, 20 B, `7c23c62c6bf151ff262af4a031518a8a78970bed44aed430688ce04de70a2e33`
- cmd16 `python -m slaif_agent_site.media_gc --check`: 0, 19 B, `d21236ec7f33a279de8ca5185eb0252964c8ae21632ec89864f179bc466ace66`
- cmd17 `python -m slaif_agent_site.bootstrap --check`: 0, 20 B, `8f399ea1c81b42d107eb51084b20b2ec1e4edf204366f0bfa883bad9fd9c2b29`
- cmd18 `node --version`: 0, 9 B, `249baf635bb43877fcb9422efa1a4904b702d0ddf14d3949b7cd0950d5229c81`
- cmd19 `pnpm --version`: 0, 8 B, `a8608bace4e3de4e6d8c1f809759eab6c60aa908a62f739089cab67e9c4955c6`
- cmd20 `pnpm install --frozen-lockfile`: 0, 1884 B, `08f8e52f2215fb3e4b1d5be5cb9ff95f7dd9af916b04a255e2c057e64708aa0b`
- cmd21 `pnpm lint`: 0, 198 B, `1dcc531f7bba4513033f59869282df2a56c20525fd3521ccd8de8b89f9ea03c6`
- cmd22 `pnpm format:check`: 0, 423 B, `2649fa5100fb0ab8fdd1afeb55775bd4b0e76f8bdc6e30aaa63b2c0b9d057b52`
- cmd23 `pnpm typecheck`: 0, 1141 B, `231d7130b19f9202be43be6f1859ae3316455d5763a4f743a771dbc5d8acff3c`
- cmd24 `pnpm test`: 0, 12419 B, `87d7d072cf8050ca68543d71bab65b0fdf70f98c5d3cc6968297a411cf9ea52d`
- cmd25 `pnpm build`: 0, 2688 B, `82f309ce2623831fa2a8eb10d6ba4321a62c95720cb102d6c17faa7a2dfcb958`
- cmd26 `pnpm licenses list --json`: 0, 109086 B, `1ba463d016847ee1941b0f8bbc236fdf50c7dc6ae4a1246d2cd9aff996159eb9`
- cmd27 `python -m compileall -q tools tests/repository`: 0, 0 B, `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- cmd28 `python -m unittest discover -s tests/repository -p test_*.py`: 0, 185 B, `239355fef9820904720343fd0cc8062410e1eab5c0d9b4e6e028b90c01f103b4`
- cmd29 `python tools/check_repository.py`: 0, 23 B, `d2795d514dc7d24027d2c376f59fac0fc2d9b3c57cf3a9bcc9e043079d0f6c7a`
- cmd30 `python tools/check_mermaid.py`: 0, 94 B, `4cecd2d92bf14319e05c54b60fcbcc8b9f21fded8a10c463dd71f91868d4d79c`
- cmd31 `npx --yes markdownlint-cli2@0.23.2 **/*.md`: 0, 293 B, `bd2637388d039ea7c9e54af6542a90379a2d071b215ff3fbfcfd5559b14ca164`

Per-command observations (from retained full streams):
cmd01 lock resolved 45 packages; cmd02 sync checked 44 frozen
packages; cmd03 ruff clean; cmd04 338 files already formatted;
cmd05 mypy success across 316 source files; cmd06 867 passed
with 9 warnings (categories in section 5.2); cmd07 sdist+wheel
built to `/tmp/slaif-agent-site-distributions`; cmd08-17 all ten
`--check` smoke commands printed CHECK_OK; cmd18 v24.22.1;
cmd19 11.22.0; cmd20 frozen install, 254 packages hard-linked
from the content-addressable store, 0 downloaded; cmd21 eslint
`--max-warnings 0` clean; cmd22 all matched files Prettier
conformant; cmd23 typecheck clean (9 workspace projects plus
web and e2e tsc); cmd24 vitest 3 files / 33 tests passed at the
root plus browser-worker 22 tests passed, 0 failures; cmd25
Next.js 16.4.1 (webpack) production build compiled with 9/9
static pages generated; cmd26 109086-byte license JSON (full
stream retained, no errors observed); cmd27 compileall quiet;
cmd28 86 repository unittests OK; cmd29 PASS repository policy;
cmd30 PASS Mermaid rendering, 16 diagrams in 3 files, 573
Markdown files scanned, CLI 11.16.0; cmd31 markdownlint-cli2
0.23.2 (markdownlint 0.41.1) Linting 567 files, 0 issues.

Tool identities (actual, observed): uv 0.12.5; Node v24.22.1
(`/tmp/oap-083-9-a/verify/node-v24.22.1-linux-x64`); pnpm 11.22.0
via cached corepack shim
(`/tmp/oap-083-9-d/toolchain/bin/pnpm`, offline, no new install);
host `timeout` = uutils coreutils 0.10.0 (recorded actual tool;
no GNU or untested process-group claims); quality venv python
3.13.18 (patched official fixed-source build at
`/tmp/oap-083-9-c/py31318/install`; retained build receipt with
BUILD_DONE and build exit 0, GCC 15.2, OpenSSL 3.5.5); the
metadata harness ran on system python3 (3.14), not the quality
venv; post-sync venv verification ok (canonical interpreter
realpath = py31318 install, 3.13.18, project import ok).

## 3. N5: implementation CI qualified; final SELF CI PENDING

- Fd CI: run 41367995545 plus standalone CodeQL 41367995393;
  all 20 strict required correct-app checks and all 10 actual
  PostgreSQL children SUCCESS (all 30), none missing/pending/
  failed/cancelled (ROOT receipt
  `/tmp/oap-083-9-d-control/root-Fd-six-and-CI-independent-review.json`).
- Fd six-image artifact 13108226702: 8212896 bytes, SHA256
  `a83a0e130807bb219aadc82ff94f5da3a302963d196ff0fe77190937b1d96e53`;
  source merge `57bc899dbc7c0e901931fd2b1db4100a3522679e`
  (parents D18+Fd, tree Fd); all 53 payload checksums and 18
  bindings verified; all six loaded copies with repro, license,
  app-deps, and Python artifacts verified; Critical 0, ignored 0,
  empty license/vulnerability exceptions; 12 unchanged High; the
  31 target CVEs (2026-115557, 2026-111497, old 29 Chrome) absent
  at any severity; fresh Grype DB age 18.467 h.
- Final SELF CI: PENDING. It runs fresh after the SELF push; a
  report cannot prove its own future commit's checks. ROOT waits
  and independently verifies the final SELF checks and artifact
  before any acceptance/merge. No acceptance or merge is claimed
  here.

## 4. N2/N4: qualified carry (no reruns in d)

- P1 two-image local runtime (web+worker) remains qualified from
  the a/b rounds (literal P1 observations carry).
- Pc1 backend/worker local runtime qualified: actor terminal
  native 0, 32 command streams (37 total files), complete
  exec/healthy inventory, hash checks, owned cleanup, exact
  healthy absence, true END clean (receipt
  `/tmp/oap-083-9-c/root-Pc1-runtime-independent-review.json`);
  Pc1 CI 41355156975 plus CodeQL 41355156985 green.
- N4: approved runtime ownership/cleanup plus ROOT
  input-equivalence proofs (all six image inputs unchanged
  Fc->Fd; receipts `root-Fc-independent-input-review.json` and
  `root-Fd-independent-input-review.json` in the 9-c/9-d
  scratch dirs).
- No unchanged-gate reruns in d; the exact 31 includes the
  listed Ruff (commands 3/4) and Markdown (command 31) runs.

## 5. Disclosures

### 5.1 Unqualified failed preparations (preserved; not gates)

- `/tmp/oap-083-9-d/` (not `qualified/`) holds: failed prep
  attempt 1 (uncapped probe subprocesses, anchors recorded
  after probes, failed on missing pnpm); attempt 2 (uncapped
  probes), which wrote the superseded `run-state.json` and
  executed cmd01-cmd05 with natives 0 - unqualified and
  disclosed, not counted as passed gates;
  `post-sync-venv-verify.receipt.attempt1.json` (literal
  symlink-name assertion bug; attempt 2 ok). All retained, none
  deleted.
- The earlier failed length assertion stopped before append; the
  subsequent 71-character check is correct. The measured 64-hex
  worker image ID
  `1ad6bf85fd8fca3f3bdab8c7c2042043d9ec3679987b8a304955b94a52a61691`
  in the runtime receipt and c report is correct (ROOT-verified).

### 5.2 d-round errata

- trueEND audit selection bug (tool 90e813): the candidate
  filter matched the per-command `.native`, `.receipt.json`, and
  `.stream` files and reported count 3. This is an audit
  selection bug, not a quality failure. The corrected read-only
  audit (tool fcd100) used exact suffix/base mapping: 31/31
  native 0, exact argv, stream SHA256/size re-verified, with no
  quality rerun, state edit, timer reset, or evidence deletion;
  bounded source queries then ran again and wrote the new
  exclusive final trueEND receipt after the successful audit.
  The earlier `source-end.txt` was preserved; no receipt was
  overwritten.
- Permission correction: receipt and `.native` files created
  before the umask fix were mode 0664; they were narrowed to
  0600 at 2026-11-02T01:03:08Z with prior bits, bytes, and
  hashes recorded in
  `qualified/metadata-perm-correction.txt`. Streams were 0600
  from creation; run-state files were already 0600.
- cmd06 warning categories: the 9 warnings include
  FastAPI/Starlette deprecation warnings as well as pytest
  cleanup warnings for sealed temporary fixture directories;
  they are not all internal-cleanup noise. 867 passed / native 0
  stands as observed. No dependency upgrade, suppression,
  rerun, or manual cleanup was requested or performed.

### 5.3 Forward errata carried from the c report (c unchanged)

- c's prospective planning threshold was 500 with HARD 600; its
  repeated 400 is the earlier a/b threshold. Gross 586 and
  remaining 14 at c closure were correct.
- c's atomic activation was 2026-11-01T19:47:44.876554Z; its
  reported 19:47:44.954787Z is the control-write close, not the
  rename timestamp.
- The four worker Python Medium target hits concern
  CVE-2026-115557. CVE-2026-111497 is the Node/Brotli finding,
  not a Python-package target hit.
- Dockerfile known-record output is Package plus
  db:Status-Status, two space-separated fields; no fourth status
  column. The runtime probe uses the separate
  Package-tab-Status format and its not-installed-or-absent test.
- c's described pip layer is from the official base layout; it
  is not a final product layer containing pip. Actual runtime
  pip absence was proved.
- ROOT's read/hash verification of all 37 c files and full
  semantic stream/inventory review is not a line-by-line
  privacy audit of every build log; no blanket
  credential-absence claim is extended from it.
- c's worktree report was atomically renamed after complete-TEMP
  lint, but its canonical copy was directly created/written/
  fsynced, not atomically renamed; its N6 MET claim is
  qualified accordingly. d publishes BOTH report locations with
  same-filesystem TEMP plus fsync, atomic rename, and parent
  fsync for each.
- c's writer printed literal percent-f timestamps; ROOT's actual
  wire UTC 2026-11-02T00:22:42.649737Z / ns
  1793578962649756263 is authoritative.
- ROOT's warning about a worker-image hash typo was incorrect
  and withdrawn; the measured 64-hex worker ID is correct.

### 5.4 c round NOT_RUN preserved

The c report's ALL31 NOT_RUN and its unsupported draft/native/
hash claims remain exactly as recorded in the immutable c
report. d's fresh local 31 is a distinct qualified run and does
not retroactively qualify the c round.

## 6. Wire and controls

- Control OK: 2026-11-02T00:28:25.837407Z (2 bytes `4f4b`, no
  LF), retained by the c-round reader (tool session 9455) to
  actual terminal with EOF.
- Response: exactly ONE exact ASCII OK (2 bytes `4f4b`, no LF)
  after the bare push and remote proofs, without FIFO fsync and
  without replay; then exactly ONE byte-retaining next-control
  reader (actual handle/PID/EOF/native recorded).
- FIFOs:
  `/home/janezp/codex-supervision/slaif-agent-site/control.fifo`
  (inode 4470111) and `response.fifo` (inode 4470112).

## 7. Criteria

- N1 MET: unique correct same PR; d made no source change;
  gross 586 unchanged; scope/soundness carry from the Fd
  independent review.
- N2 MET (qualified carry): fixed bytes/inventory/licensing with
  qualified literal runtime carry (section 4).
- N3 MET: 31/31 fresh at clean Fd, exact order/argv, complete
  honest receipts (section 2).
- N4 MET: approved runtime ownership/cleanup and ROOT
  input-equivalence proofs (section 4).
- N5 PENDING (by design): Fd implementation CI and artifact
  qualified (section 3); the final SELF fresh six-image CI runs
  after the SELF push and remains PENDING until ROOT
  independently verifies it.
- N6 MET: this report, both report locations published exact
  with same-filesystem atomic renames, remote publication and
  synchronization verified before the response OK.

## 8. Scope, secrets, production, confirmations

- No product source, test, Dockerfile, lock, or CI change in d;
  no new PR or branch; no merge, acceptance, or auto-merge; no
  production system, credential, or external-exploit work.
- PR #112 remains OPEN, ON HOLD/INACTIVE (not accepted, not
  abandoned, not closed).
- No new secrets introduced; no blanket credential-absence or
  privacy claim is made beyond proven scope.
- No deletion workarounds or sealed-fixture cleanup in d.
- No rewrite of activated orders or published reports; prior
  rounds' orders, reports, and active history are immutable.

## 9. Limitations

- d performed no product Docker/build/runtime execution (order
  scope is the direct local 31); image evidence is the
  qualified literal carries plus the Fd CI artifact.
- No new broad or unchanged-gate reruns beyond the exact 31.
- Host `timeout` is uutils coreutils 0.10.0; no untested
  process-group behavior is claimed.
- COMPLETE execution never equals strategic acceptance; ROOT
  alone reviews, accepts, and merges.

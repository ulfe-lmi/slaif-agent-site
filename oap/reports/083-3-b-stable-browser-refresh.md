# OAP Coding-Agent Report — 083-3-b

## Work order

- Order: `oap/orders/083-3-b-stable-browser-refresh.md` (activated via
  `oap/active`; exact strategic FIFO `OK` = 2 bytes hex `4f4b` received
  2026-10-17T22:10:32Z).
- Order SHA-256:
  `24ff3d5e3ba4e5a4e3d3884061bceb9a7c2a36f5ee1e9c1737439022844f76a7`.
- `oap/active` bytes (hex): `3038332d332d620a` (`083-3-b` + LF).
- Round: `083-3-b` (increment-qualified: 083/3 — stable browser refresh).
- Mode: `AMEND_EXISTING_PR`. NO NEW PR. Strategy alone reviews and merges.
- PR: #102 (<https://github.com/ulfe-lmi/slaif-agent-site/pull/102>),
  state OPEN / MERGEABLE / mergeStateStatus BLOCKED; base
  `main` @ `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- Branch: `oap/083-3-a-cache-outbox-consumer`.
- Starting remote head:
  `8b4842d4b01d5974cd953b555857bec47a32aec7`.
- Target identity: Chrome for Testing `155.0.8059.84`, CfT revision
  `1697595`, linux64; archive
  `https://storage.googleapis.com/chrome-for-testing-public/155.0.8059.84/linux64/chrome-linux64.zip`
  SHA-256 `cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc`,
  199014491 bytes; executable
  `/ms-playwright/chromium-1697595/chrome-linux64/chrome`.
- Commits: transcript T `23c79ae6bf7a3eef7600be1ec3c8c43e01ed4234`
  (order + `oap/active` bytes, pushed at activation); implementation I
  `942847a3a9e40fe0ab8129d90b19e82ccf964baf` (the 13-file R1 identity
  refresh, pushed 2026-10-17T23:04Z); report S (SELF, this file,
  report-only, first parent = I).
- Implementation head SHA:
  `942847a3a9e40fe0ab8129d90b19e82ccf964baf`.
- Report publication commit: SELF (its literal SHA becomes the remote PR
  head; verifiable via `gh pr view 102 --json headRefOid`; the SELF commit
  changes only this report file).
- Pushed commits: T, I, SELF.

## Status

PARTIAL/BLOCKED. R1 (the 15-file allowance) is applied as far as measured
data exists: all 13 identity/evidence/docs files are refreshed, committed,
and pushed. Candidate-8 qualification (R2) is BLOCKED by an out-of-scope
external failure: Ubuntu archive rotation removed `apache2
2.4.58-1ubuntu8.15`, pinned in `infra/apache/Dockerfile` (NOT in this
order's 15-file allowance), which breaks (a) the six-image supply-chain
evidence pipeline before any scan and (b) the final Apache adapter build
step of the Compose smoke. Per the order's R2 stop rule, the executor
captures exact diagnostics and reports PARTIAL/BLOCKED without adding
exceptions, weakening gates, or broadening the 15-file allowance. Strategy
acknowledged the boundary and holds a bounded 083-3-c repair on the same
PR. PARTIAL/BLOCKED never means accepted.

## Executive summary

The refresh itself is complete and coherent: every current-truth
identity surface now names CfT `155.0.8059.84` / revision `1697595` /
archive hash `cf0f0498…` / executable path `chromium-1697595`, and the
refreshed browser-worker image builds and passes its in-image version
assertion, the CI `browser-worker-image-policy` assertion, and the full
19-project Compose smoke E2E roster on the implementation head (details
below). The round cannot close C-1 (20/20 checks at the exact final head)
because the two checks that build the Apache adapter image fail on the
rotated package pin — an out-of-scope file this order forbids touching.
All missing acceptance proof (candidate-8 matrix record,
`test_policy.py` sixth qualification block, full local gate roster,
terminal 20/20) carries to 083-3-c.

## Preflight (identity and reconciliation)

- GitHub reconciliation at activation: PR #102 exact open, base main,
  head `8b4842d4…`, zero reviews/comments; no duplicate increment-3 PR;
  no existing `083-3-b` round report.
- P1.1 (2026-10-17T22:10Z): full inventory of old pin/version/revision/
  archive-hash references at the starting head, per file and line.
- P1.3 (2026-10-17T22:12:32Z): official CfT metadata verified —
  `last-known-good` timestamp `2026-10-17T09:18:35.172Z`, channel
  Stable, version `155.0.8059.84`, revision `1697595`, linux64 entry and
  archive URL exactly as ordered; raw JSON snapshots retained.
- P1.2 (2026-10-17T22:12:58Z): official linux64 archive independently
  stream-hashed — 199014491 bytes, SHA-256
  `cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc` —
  MATCH against the order; supplemental extracted-executable SHA-256
  `b866a2964538c825538c454de4867973b926650da57ec12dc3328807d768247b`.
- Inert-draft preactivation lint: 0 issues (markdownlint-cli2@0.23.2,
  product `.markdownlint-cli2.jsonc`, `--no-globs`); draft bytes
  preserved; no draft content executed.

## Changes made (13 files, +39/−39)

1. `services/browser-worker/Dockerfile` — archive URL/hash, asserted
   version, provenance comment, fixed executable/version ENV, copied
   directory (base digest pins and all confinement preserved).
2. `supply-chain/policy.json` — the five chromium identity values only.
3. `tools/supply_chain/policy.py` — five matching literal assertions;
   schema/logic unchanged.
4. `tools/supply_chain/evidence.py` — boundary directory literal
   `chromium-1689415` → `chromium-1697595` only.
5. `tools/compose/smoke.sh` — browser path/version/revision assertions
   and the `browser-worker-image-policy` identity line; all projects and
   assertions preserved.
6. `tests/packaging/test_oci_contract.py` — matching version/hash pins.
7. `tests/supply_chain/test_evidence.py` — matching PURL/version
   fixture.
8. `README.md` — current browser qualification statement only.
9. `docs/CONFIGURATION.md` — current executable/version rows only.
10. `docs/DEPLOYMENT.md` — current browser identity/archive statements.
11. `docs/LICENSE_POLICY.md` — current browser version statement.
12. `docs/SECURITY.md` — current version/revision/hash statement.
13. `docs/SUPPLY_CHAIN.md` — current identity statements, including the
    R1.15 correction of the stale active-qualification sentence (named
    `153.0.8010.52` / `1681091`); historical narrative and matrix
    entries preserved.

Explicitly NOT changed (and verified absent from the diff):
`supply-chain/browser-worker-critical-matrix.json` and
`tests/supply_chain/test_policy.py` (both require measured candidate-8
values — BLOCKED, see below); `infra/apache/Dockerfile` (out of the
15-file allowance — the boundary); all lockfiles, workflows,
`contracts/`, `packages/` (byte-identical to base).

## Pre-declared budget check (order §8 vs measured)

- Starting base→head (`214909f3`→`8b4842d`): 27 files, +3615/−98.
- At T: 28 files, +3913/−98.
- At I: 40 files, +3952/−137 (the I commit itself: 13 files, +39/−39;
  `README.md` overlaps the 083-3-a diff, so +12 new unique files).
- After S: 41 unique files (+1 = this report) vs the order's 43 expected.
- Grouped actual at S: 11 production/config (6 from 083-3-a incl. its
  1 migration + 5 this round; 0 migrations this round), 16
  tests/evidence (14 + 2), 0 generated, 9 docs (4 + 6 − 1 README
  overlap), 5 transcript (3 + 2, `active` overlaps).
- Variances fully classified: −2 files = `browser-worker-critical-
  matrix.json` + `test_policy.py`, both withheld because their content
  requires measured candidate-8 values that the boundary prevented
  (carries to 083-3-c).

## Acceptance-criteria evidence (order §7)

1. PASS — correct PR/base/branch, start SHA, official stable target and
   archive evidence (Preflight); T committed and pushed the exact
   published order and active bytes (order SHA-256 and active hex above).
2. PASS — diff from starting head changes only the 13 named
   identity/evidence/docs files plus order, active, and this report;
   literal identity coherence verified across all 13 files (one
   version/revision/URL/hash/executable everywhere); historical matrix
   entries semantically and textually unchanged (zero diff); residual old
   identifiers remain only in the immutable historical records (matrix
   candidate-7 entry, `test_policy.py` previous-qualification block,
   SUPPLY_CHAIN historical narrative).
3. BLOCKED — candidate-8: identity/archive/executable evidence measured
   (P1.2/P1.3); the refreshed browser-worker image builds cleanly and
   passes its version assertion (local run 2 and CI); but the six-image
   scan never ran (pipeline aborted at the Apache build), so no
   candidate-8 record exists, no PASS label is applied, and no
   exception entries exist.
4. PARTIAL — local policy validation OK (`supply-chain-policy: OK`,
   `dependency-inventory: OK python=44 node=254`,
   `third-party-notices: OK components=298` in both pipeline runs);
   ruff/mypy/unit gates EXIT 0; targeted packaging/supply-chain tests
   inside the unit suite EXIT 0; the complete Compose smoke E2E roster
   ran in CI at the implementation head (19 projects OK, browser
   image-policy OK on the new pin) while its final packaging step FAILED
   (Apache, out of scope); the local standalone smoke was NOT RUN.
5. FAIL at I — 18/20 terminal SUCCESS, 2 FAILURE (both the out-of-scope
   Apache rotation, exact signatures below); C-1 not closed by this
   round; checks newly started by S are honestly pending in this report.
6. PASS — starting report/order and prior qualification evidence
   unchanged; `contracts/`/`packages/` byte-identical; stripped OpenAPI
   identity digest
   `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
   preserved (no contract files in the diff; CI `Node contracts`
   SUCCESS at I); no unauthorized files, logic, dependencies, or trust
   changes.
7. PASS — this report includes the mandated T and implementation SHAs,
   SELF, file inventory, order SHA-256, active bytes/hex, measured
   identity evidence, commands/results, per-check table with run IDs and
   the SHA observed, complete failures, deviations, local setup,
   limitations, and the cumulative grouped size table.

## Local verification (exact, at implementation head I)

| Command | Result |
| --- | --- |
| `uv lock --check` | PASS (exit 0) |
| `uv sync --frozen --all-groups` | PASS (exit 0) |
| `uv run --frozen ruff check services/backend tests/repository tools` | PASS (exit 0) |
| `uv run --frozen ruff format --check services/backend tests/repository tools` | PASS (exit 0) |
| `uv run --frozen mypy` | PASS (exit 0) |
| `uv run --frozen pytest services/backend/tests/unit tests/repository -q` | PASS (exit 0) |
| `uv run --frozen pytest services/backend/tests/integration -q` | CANCELLED — in progress at strategy-directed closure; result NOT RECORDED (disposable PostgreSQL `slaif-integration-pg-0833b` at 127.0.0.1:5432 provisioned and up) |
| `uv build --out-dir /tmp/slaif-agent-site-distributions` | NOT RUN — queued after integration; double-build reproducibility separately proven in both local pipeline runs and CI (both `python-dist-1`/`python-dist-2` sdist+wheel built) |
| `pnpm lint` / `format:check` / `typecheck` / `test` / `licenses list` | NOT RUN locally (CI `Node contracts` SUCCESS at I; frozen install + full workspace build proven in pipeline runs) |
| `compileall` / `unittest discover` / `check_repository.py` / `check_mermaid.py` / `markdownlint-cli2 **/*.md` | NOT RUN locally (CI `Repository policy`, `Mermaid`, `Markdown` SUCCESS at I) |
| markdownlint-cli2@0.23.2 `--no-globs` on this report (repo `.markdownlint-cli2.jsonc`) | PASS (0 issues, verified before publication) |

## Supply-chain evidence attempts (the boundary)

- Run 1 (2026-10-17T22:17→22:29Z): all pre-stages OK (frozen pnpm
  install; policy/inventory/notices OK; double Python dist build; Node
  workspace build 9/10 projects). browser-worker image Step 10/24 failed
  3/3 (transient; the legacy builder suppressed per-step stderr).
  Pipeline exited 143 (SIGTERM); captured diagnostics
  `STATUS.json`: `qualification=UNQUALIFIED`, `status=INCOMPLETE`,
  `success_manifest=ABSENT`, `original_exit_status=143`.
- Run 2 (22:29→22:51Z): the single documented flake-class re-run
  permitted for this PR (083-3-a consumed none; unmodified head; all 13
  file mtimes 22:15:06–22:16:57 prove no worktree change between runs).
  browser-worker build succeeded on the first attempt with the new pin
  (in-image assertion
  `Google Chrome for Testing 155.0.8059.84` passed). The Apache adapter
  image build then failed 3/3:
  `E: Version '2.4.58-1ubuntu8.15' for 'apache2' / 'apache2-bin' /
  'apache2-data' / 'apache2-utils' was not found` (apt exit 100),
  `apache first build failed after 3 attempts`; the pipeline aborted
  before any scan.
- Root-cause verification (2026-10-17T22:55:59Z, Ubuntu archive
  indexes): `noble-updates` now serves `2.4.58-1ubuntu8.16`
  (SHA-256: apache2
  `3b5a53a50f886f671b335765b4c85889ed47c8413024c3163eaaff0903e09c5b`,
  -bin `7aa1a1c6aea9a3053eecce672e39db356f44812499fac7803148b8ed195bb2c5`,
  -data `7f5407f162b51db87d57c0d3f92f7905cf7570516cae67a7483f289387ae0ae5`,
  -utils `e6a5814966dfe4ca0d1e27acd907c4aa3765e8ed38ec2ac071a56d93e009100e`);
  `noble-security` serves `2.4.58-1ubuntu8.17` (SHA-256: apache2
  `289d4b306cc0ab3db559e7b111cc3a1f1dec03b763a71bc5eb8096c190e1b8e1f`,
  -bin `7c31f0e45695c1d0335d4bf654c644fc0977006bbefa22e1b2e0ef04d2e18744`,
  -data `aad82c20829ddbef9e868180b53a82470676966df1232f6eca1aa8526edada69`,
  -utils `754eb0a2896c411d796073c8c2ec74a3b174ce64732c30afffda5122fa99bc69`);
  `openssl 3.0.13-0ubuntu3.16` remains in both pockets
  (`675b84971ffd4467707008c25ef7520f90ea7c23ef27b7a76b0dccf1d7c4dc3f`).
  The pinned `2.4.58-1ubuntu8.15` has been rotated out of both pockets.
- Classification (R2 stop rule): external failure in an unrelated image.
  `infra/apache/Dockerfile` is not in the 15-file allowance; no
  exception was added, no gate weakened, no unrelated dependency
  changed, and the allowance was not broadened.

## Compose smoke

- Local: NOT RUN — the smoke's final step
  (`tools/compose/smoke.sh:1291`,
  `docker build -f infra/apache/Dockerfile -t slaif-agent-site-
  apache:test .`) is deterministically blocked by the rotation; CI
  performed the complete smoke at the implementation head instead.
- CI `Compose and edge packaging` at I (job `117527798235`): the full
  smoke ran with the refreshed pin — `compose-e2e: OK projects=19
  setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6
  agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1
  review-surface=1 accept-lifecycle=1 discard-lifecycle=1
  media-publication=1 artifacts=disabled`; 35/35 `browser-e2e`
  contracts PASSED (desktop Chromium/Firefox/WebKit, tablet, mobile
  Chromium/WebKit); `browser-worker-image-policy: OK playwright=1.62.1
  cft_revision=1697595 chromium=155.0.8059.84 browsers=chromium-only
  package-manager=absent`; the version line `Google Chrome for Testing
  155.0.8059.84` was observed; ~40 assertion groups OK (agent-browser,
  browser-artifact/outage/recovery/root-policy, edge-header/body-policy,
  governance-e2e/restart, media-e2e, public-agent-acceptance/
  component-loop/news-edge/restart, render-*-secret-policy,
  review-worker-media-boundary, database-login-policy,
  control-readiness-fixture; full assertion list in the CI job log,
  retained locally). The job then FAILED at the Apache adapter
  build (same `E: Version '2.4.58-1ubuntu8.15' … not found`, exit 100).
  The smoke E2E portion therefore PASSED at I; the check as a whole is
  not green and is NOT claimed PASS.

## GitHub CI / required checks

Exact 20-check roster (15 `CI`-workflow `pull_request` checks + CodeQL
`CodeQL`, `Analyze (actions)`, `Analyze (javascript-typescript)`,
`Analyze (python)`, `Detect supported languages`).

Honest run history (every run, every failure, every re-run):

- Starting head `8b4842d` (2026-10-06): 19 SUCCESS + 1 FAILURE —
  `Supply-chain evidence` (check-run `112164308347`), the
  CVE-2026-103628 finding on the stale payload that this round
  addresses.
- T `23c79ae` (2026-10-17T22:12Z, CI run `39074084168`, CodeQL run
  `39074084166`): 18 SUCCESS + 2 FAILURE — `Supply-chain evidence`
  (job `117517518231`) and `Compose and edge packaging` (job
  `117517518248`), both the Apache rotation (same `E: Version
  '2.4.58-1ubuntu8.15'` signature); failure-diagnostics artifact
  SHA-256 `9838263e015298586d1508104f31933a3a4e8a4982a494c34fb09d4ae99674a4`
  uploaded by the run.
- I `942847a` (2026-10-17T23:04Z, CI run `39077570732`, CodeQL run
  `39077570677`): all 20 terminal as of 2026-10-17T23:21:25Z —
  18 SUCCESS + 2 FAILURE (both the same out-of-scope Apache rotation).

Per-check table at implementation head
`942847a3a9e40fe0ab8129d90b19e82ccf964baf`:

SUCCESS (18): Repository policy (`117527798247`), Dependency review
(`117527798221`), Markdown (`117527798073`), Mermaid (`117527798150`),
Node contracts (`117527798217`), Python 3.12 quality and package
(`117527798277`), Python 3.13 quality and package (`117527798209`),
Python 3.14 quality and package (`117527798239`), Foundation PostgreSQL
14/15/16/17/18 (`117527798207`/`117527798279`/`117527798254`/
`117527798224`/`117527798240`), Detect supported languages
(`117527797748`), Analyze (actions) (`117527819108`), Analyze (python)
(`117527819130`), Analyze (javascript-typescript)
(`117527819038`), CodeQL (`117527894874`).

FAILURE (2): Compose and edge packaging (`117527798235`) — smoke E2E
OK, then the Apache adapter build failed (out of scope); Supply-chain
evidence (`117527798333`) — `apache first build failed after 3
attempts` (out of scope).

No CI re-run was performed: both failures are deterministic external
package rotation, so an unmodified re-run cannot change the result.
Checks newly started by S may be honestly pending in this immutable
report; strategy independently waits for all 20 at S.

## Local setup / dependencies

- Disposable host with passwordless sudo (constitution authority); uv
  `0.12.5`; Node `v24.22.0` (local download) with corepack pnpm
  `11.22.0`; Docker + BuildKit; disposable PostgreSQL container
  `slaif-integration-pg-0833b` (127.0.0.1:5432, fake fixture
  credentials only). No production systems, data, or credentials
  touched; no secrets, capabilities, cookies, or DB URLs in the diff or
  this report.

## Documentation

Six surfaces updated in I (itemized under "Changes made" 8–13),
including the R1.15 correction of the stale active-qualification
sentence in `docs/SUPPLY_CHAIN.md`. Implemented vs planned kept
distinct; 083/3 remains in flight at `083-3-b` (PARTIAL/BLOCKED);
contractual MVP NOT COMPLETE. No architecture/constitution/protocol
edits.

## Safety and scope confirmations

- Secrets: none introduced; all test credentials fake/fixture values.
- Production access: none. Docker used only for disposable local
  builds/containers under existing runtime authority.
- Byte-identity: `uv.lock`, `pnpm-lock.yaml`, `.github/workflows/*`,
  `contracts/`, `packages/`, `infra/apache/Dockerfile` all unchanged
  (none appear in the base→head diff).
- No vulnerability/dependency exceptions; no lockfile, workflow, base
  image, Node/pnpm/Playwright, migration, role, or topology changes; no
  product logic change.
- Scope: only the itemized 13 files changed by I; the order file and
  `oap/active` committed exactly as activated (T) and never edited;
  untracked `.codex/`, `CODEX-SESSIONS.md`, `codex.sh` preserved and
  never staged.
- Extra PR: NO. Merge/auto-merge/close: NO. Activated order/active
  edited: NO. SELF commit changes only this report: YES (verified at
  publication).

## Known limitations / blockers

1. BLOCKER (external, out of scope): `apache2 2.4.58-1ubuntu8.15`
   rotated out of Ubuntu noble archives (pockets now serve `.16` /
   `.17`) — blocks the six-image evidence pipeline pre-scan and the
   final Apache build step of the Compose smoke, so candidate-8
   qualification and C-1 (20/20) cannot close within this order.
2. `browser-worker-critical-matrix.json` candidate-8 record and
   `test_policy.py` sixth qualification block: NOT ADDED (require
   measured values; carries to 083-3-c).
3. Local integration pytest: CANCELLED at closure (result NOT
   RECORDED); `uv build` standalone: NOT RUN; Node local gate and
   preparation checks: NOT RUN locally (CI equivalents green at I).
4. Full local Compose smoke: NOT RUN (CI smoke E2E passed at I;
   packaging step blocked as in item 1).

## Recommended strategic follow-up

083-3-c on the same PR/branch (strategy draft ready): repair
`infra/apache/Dockerfile` to an available archive pin (this report
captures the exact `.16`/`.17` pocket availability with .deb SHA-256
values), re-run the six-image evidence pipeline for measured
candidate-8, append the matrix record and `test_policy.py` block,
re-run the full local gate roster plus the complete Compose smoke, and
re-close C-1 with 20/20 terminal checks at the exact new head.

Report publication commit: SELF

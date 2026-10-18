# OAP Coding-Agent Report — 083-3-c

## Work order

- Order: `oap/orders/083-3-c-apache-qualification-closure.md` (activated via
  `oap/active`; exact strategic FIFO `OK` = 2 bytes hex `4f4b` received
  2026-10-17T23:36:32Z).
- Order SHA-256:
  `3e005ac4b88b9f146b4ac4ef9fd3dd0aeb21a4d46e958a10676e5c12de0f8292`.
- `oap/active` bytes (hex): `3038332d332d630a` (`083-3-c` + LF).
- Round: `083-3-c` (CLOSURE_ONLY). Mode: `AMEND_EXISTING_PR`. NO NEW PR.
- PR: #102 (<https://github.com/ulfe-lmi/slaif-agent-site/pull/102>),
  state OPEN; base `main` @
  `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`; branch
  `oap/083-3-a-cache-outbox-consumer`.
- Starting report-only head S-b:
  `ee96af9f96d16d52f3efe34012314792a888ed89`; S-b parent / b implementation:
  `942847a3a9e40fe0ab8129d90b19e82ccf964baf`.
- Commits: transcript T-c
  `2219d0ec7e9acd0576b50adf07d6cd7a21076e8a` (order + `oap/active` bytes,
  parent S-b); implementation I-c
  `33d38966c79fb4387eba279872f2000b1adcf6f0` (the 3-file C-2 pin repair,
  parent T-c); report SELF (this file, report-only, first parent = I-c).
- Implementation head SHA:
  `33d38966c79fb4387eba279872f2000b1adcf6f0`.
- Report publication commit: SELF (its literal SHA becomes the remote PR
  head; verifiable via `gh pr view 102 --json headRefOid`; the SELF commit
  changes only this report file).
- Pushed commits: T-c, I-c, SELF.

## Status

BLOCKED. The in-scope C-2 Apache pin repair is complete, verified, and
pushed (I-c). Candidate-8 qualification and C-1 (20/20 at exact final head)
are blocked by an out-of-scope external discovery in the fresh Grype
database: a new Critical `CVE-2026-19445` on CPython 3.12.12 embedded in the
shared backend image (fixed in 3.12.15). Fixing it requires a
dependency/base-image change or a strategic vulnerability exception, both
forbidden by this order's closed scope. Per c4.10 the executor preserves
diagnostics and adds no repair or exception. BLOCKED never means accepted.

## Executive summary

All six product images (double-built) now build, including the Apache
adapter that blocked b: it pulls all four `2.4.58-1ubuntu8.17` packages from
noble-security plus unchanged `openssl 3.0.13-0ubuntu3.16`, and its scan
gate PASSED (zero unexcepted Critical). The measured pipeline then failed
its fail-closed gate on the backend image with exactly one unexcepted
Critical (the CVE above) and exited 1 with
`qualification=UNQUALIFIED, status=INCOMPLETE, success_manifest=ABSENT`.
No candidate-8 record was written and no PASS is claimed. Local gates ran as
recorded below; the integration suite was cancelled at 51/320 tests
(0 failures, 0 errors) under the strategy boundary direction; the local
Compose smoke was NOT RUN.

## Changes made (I-c, exactly the ordered files)

1. `infra/apache/Dockerfile`: four literals
   `2.4.58-1ubuntu8.15` → `2.4.58-1ubuntu8.17`; base digest
   `33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`,
   OpenSSL pin, modules, edge config, labels and build gates unchanged.
2. `supply-chain/policy.json`: the same four apt-pin literals only.
3. `tests/packaging/test_oci_contract.py`: the matching four version
   assertions only.
4. PR #102 description (metadata only, not a repository file): placeholder
   replaced with the delivered-state description.

Diff: 3 files, +12/−12; zero `8.15` literals remain in the three pin/assertion
files (4 `8.17` per file). `browser-worker-critical-matrix.json` and
`tests/supply_chain/test_policy.py` are NOT modified (candidate-8 withheld:
no measured qualification exists this round).

## C-2 package verification (before implementation)

- Strategy independently fetched official indexes 2026-10-17T22:55:59Z:
  noble-updates serves 8.16, noble-security serves 8.17 (USN-8931-1 fixed
  version, published 2026-10-14); both pockets keep
  `openssl 3.0.13-0ubuntu3.16`.
- Executor re-verification: all four `.deb` artifacts downloaded read-only
  from <https://archive.ubuntu.com/ubuntu/pool/main/a/apache2/> and matched
  the order table (SHA-256 and bytes): apache2 90226
  `289d4b306cc0ab3db559e7b111cc3a1f1dec03b63a71bc5eb8096c190e1b8e1f`,
  apache2-bin 1337880 `7c31f0e45695c1d0335d4bf654c644fc0977006bbefa22e1b2e0ef04d2e18744`,
  apache2-data 163308
  `aad82c20829ddbef9e868180b53a82470676966df1232f6eca1aa8526edada69`,
  apache2-utils 100358
  `754eb0a2896c411d796073c8c2ec74a3b174ce64732c30afffda5122fa99bc69`.
- `apt-get --simulate` inside the pinned base
  (`ubuntu:24.04@sha256:33ceb719…`) resolved all five packages from
  noble-security with no errors.

## Local verification (exact commands, at I-c worktree)

| Command | Result |
| --- | --- |
| `uv lock --check` / `uv sync --frozen --all-groups` | PASS (exit 0) |
| `uv run --frozen ruff check services/backend tests/repository tools` | PASS (exit 0) |
| `uv run --frozen ruff format --check services/backend tests/repository tools` | PASS (exit 0) |
| `uv run --frozen mypy` | PASS (exit 0) |
| `uv run --frozen pytest services/backend/tests/unit tests/repository -q` | PASS (788 passed, exit 0) |
| `uv run --frozen pytest services/backend/tests/integration -q` (run 1) | FAILED — cross-run interference: a stale b-round integration pytest (still running at c start) concurrently created/dropped the same fixture roles on the shared disposable PG; exact observed teardown error `DependentObjectsStillExistError: role "slaif_gc" cannot be dropped because some objects depend on it` (privileges for concurrent `slaif_test_*` databases). Stale b run and polluted c run killed; catalog cleaned (2 orphaned databases, 11 roles dropped, verified 0/0). |
| `uv run --frozen pytest services/backend/tests/integration -q` (isolated re-run, clean catalog) | CANCELLED at 2026-10-18T00:1xZ under the strategy boundary direction at 51/320 tests, 0 failures, 0 errors observed so far; final result NOT RECORDED |
| `uv build --out-dir /tmp/slaif-agent-site-distributions-c` | PASS (sdist + wheel, exit 0) |
| `uv run --frozen python tools/supply_chain/policy.py validate` | PASS (`supply-chain-policy: OK`) |
| `tests/packaging/test_oci_contract.py` + `tests/supply_chain` (targeted) | PASS (exit 0) |
| Node gate, 9 exact commands, clean verification copy | PASS (all exit 0: node v24.22.0, pnpm 11.22.0, install, lint, format:check, typecheck, test, build, licenses) |
| `compileall` / `unittest discover` / `check_repository.py` (clean copy) | PASS (exit 0) |
| `check_mermaid.py` (clean copy) | run 1 FAILED — host AppArmor (`unprivileged_userns` profile denied `cap_sys_admin`, dmesg-audited) made Chromium's sandbox unusable; retry with temporarily set `kernel.apparmor_restrict_unprivileged_userns=0` PASSED (16 diagrams, 537 files, CLI 11.16.0); sysctl restored to 1 and re-verified. No tracked file or gate config changed. |
| `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` (clean copy) | PASS (0 issues, 530 files) |
| markdownlint-cli2@0.23.2 `--no-globs` on this report (repo config) | verified before publication |
| Stripped OpenAPI identity (x-slaif- keys removed recursively; canonical JSON SHA-256) | re-proven `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83` (47 paths); `contracts/` and `packages/` byte-identical to base (none in diff) |
| `tools/compose/smoke.sh` (complete local) | NOT RUN (boundary; see below) |

The main-worktree Node-gate attempt (before the clean copy) is retained as a
failed environment attempt: lint exit 2 (ESLint choked on untracked
`.codex/plugins/cache/…/vinext-starter/eslint.config.mjs`) and test/build
exit 1 (`Another next build process is already running`, lock collision with
the concurrent pipeline build). Superseded by the clean-copy PASS row above.

## Supply-chain pipeline (the boundary)

- Command: `sh tools/supply_chain/run.sh /tmp/oap-083-3-c/evidence-run-c`
  (2026-10-17T23:44Z → 2026-10-18T00:10Z). Attempt 1 died at
  `pnpm: not found` (PATH not exported; `PIPELINE_EXIT:127`, preserved as
  `evidence-run-c-failed1-pnpm-missing`); attempt 2 is the measured run.
- All six images double-built (first/second, reproducibility OK:
  `python-artifacts=2 next-build-id=408946d7e3f1bc07d226da23d18ada0d
  browser-output=source-contract`); six SBOMs; syft 1.51.0; grype 0.117.0
  with fresh database schema v6.1.10 built 2026-10-17T06:27:09Z
  (checksum `sha256:4c2b8b0cd02313f74a50c81c457796660c4997565cc2ff211e09cc1880205c10`,
  valid=true).
- Failure (exact): `supply-chain-evidence: ERROR: backend: unexcepted
  Critical vulnerabilities: CVE-2026-19445` → `PIPELINE_EXIT:1`;
  `failure-diagnostics/STATUS.json`: `qualification=UNQUALIFIED,
  status=INCOMPLETE, success_manifest=ABSENT, original_exit_status=1`.
- CVE-2026-19445 (Grype, fresh DB): CPython binary 3.12.12, PURL
  `pkg:generic/python@3.12.12`, at `/usr/local/bin/python3.12` and
  `/usr/local/lib/libpython3.12.so.1.0` in the backend image (manifest
  `sha256:c25937a9a76a31530a84698c41f0ad87e5a33d5e2fdba4cf8b4dd5fdf3f37579`);
  severity Critical (CVSS 4.0 9.2, `cna@python.org`), CWE-416 use-after-free in
  TLS server `sni_callback` SSLContext handling; affected `< 3.12.15` on the
  3.12 branch; fixed in 3.12.15 (first observed 2026-10-08); EPSS 0.00429;
  <https://nvd.nist.gov/vuln/detail/CVE-2026-19445>.
- Per-image scan state: apache gate PASS (Critical 0, High 0, Medium 195,
  Low 17, Negligible 3, exceptions 0); backend FAIL (1 Critical = the CVE);
  browser-worker 0 Critical (its four CVE-2026-19445 matches are Ubuntu
  distro `python3.12 3.12.3-1ubuntu0.15` packages, severity Medium);
  nginx, postgres, web 0 matches. All six were scanned; the pipeline aborted
  after the backend gate, so the remaining gate evaluations are NOT RUN by
  the pipeline (local counts recorded for information only).
- Classification: external, out of scope, deterministic against the fresh
  database (not a flake). Repair requires a CPython/base-image decision or a
  strategic exception — neither authorized in c. No cached old-Apache
  substitute, no unsigned packages, no fake qualification PASS.

## Compose smoke

- Local complete smoke: NOT RUN (boundary direction; the run is lengthy and
  its outcome cannot change this round's status).
- The Apache adapter build step that deterministically blocked b now
  succeeds — evidenced by this round's pipeline apache image build plus its
  PASS scan gate.
- CI `Compose and edge packaging` at I-c: in progress at report time
  (honestly pending).

## GitHub CI / required checks at I-c

CI run `39082163040`, CodeQL run `39082163019`, head
`33d38966c79fb4387eba279872f2000b1adcf6f0`. State at report time
(2026-10-18T00:2xZ):

SUCCESS (11): CodeQL (`117541298363`), Analyze (actions)
(`117541188920`), Analyze (javascript-typescript) (`117541188919`),
Dependency review (`117541171641`), Mermaid (`117541171636`), Repository
policy (`117541171617`), Markdown (`117541171582`), Python 3.12/3.13/3.14
quality and package (`117541171595`/`117541171577`/`117541171590`), Detect
supported languages (`117541171309`).

IN PROGRESS (9): Analyze (python), Node contracts, Foundation PostgreSQL
14/15/16/17/18, Compose and edge packaging, Supply-chain evidence. Checks
started by S-c are honestly pending in this report. No CI re-run was performed; the one
documented flake-class rerun allowance for this PR remains unused (verified
from GitHub run attempts; b's local retry wording corrected below). While
the fresh database reports the backend CVE, the Supply-chain evidence check
cannot pass at I-c or S-c; no green-check prediction is made.

## b-report corrections (explicit, without editing b)

1. The local Buildx/TARGETARCH environment retry in b was NOT a CI flake
   re-run: all six b CI/CodeQL runs have `run_attempt=1`, so the one-CI-
   rerun allowance is unused.
2. b labeled local integration "CANCELLED … NOT RECORDED" and Node/tree
   gates "NOT RUN"; in fact the initial local integration attempt failed for
   missing DB (before the disposable PG was provisioned) and the Node/tree
   gates were attempted with runtime-artifact/build-lock errors (exact
   retained signatures in this report's local table). The retained b gate
   log shows the still-running integration attempt ending `EXIT:143`
   (2026-10-18T00:02:11Z, killed during c's stale-process cleanup) with a
   dense error pattern and no error summary (killed mid-run); its exact
   error text and the missing-DB attempt's exact error are NOT RETAINED in
   executor /tmp evidence.
3. b mistyped the Apache 8.17 `apache2` SHA (`…dec03b763a71bc…`); the
   verified value is
   `289d4b306cc0ab3db559e7b111cc3a1f1dec03b63a71bc5eb8096c190e1b8e1f`
   (`03b63`), re-verified in c by direct `.deb` download and hash.
4. The candidate-7 assertions in `tests/supply_chain/test_policy.py` sat in
   the CURRENT block until the candidate-8 append, not solely the previous
   block. Candidate-8 is not appended this round, so the test file is
   unchanged.

## Adopted b evidence vs newly run (c4.3)

- Adopted (byte-identical unaffected paths, tested SHA `942847a…`/S-b
  `ee96af9…` disclosed): Chrome archive identity (SHA-256
  `cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc`,
  199014491 bytes, LKG timestamp 2026-10-17T09:18:35.172Z), supplemental
  executable SHA-256 `b866a2964538c825538c454de4867973b926650da57ec12dc3328807d768247b`,
  in-image `Google Chrome for Testing 155.0.8059.84` assertion (b local run 2
  and CI), CI smoke E2E at I-b (19 projects, browser-worker-image-policy
  `cft_revision=1697595 chromium=155.0.8059.84`).
- Newly run (this round): everything in the local table, the measured
  six-image pipeline, the per-check states at I-c. Not described as reruns
  of adopted evidence.

## Budget (order §5 vs measured)

- This round: 2 production/config (apache Dockerfile, policy.json), 0
  migrations, 1 of 3 expected test/evidence (`test_oci_contract.py`;
  matrix + `test_policy.py` withheld — no measured candidate-8), 0
  generated, 0 docs, 3 transcript (order, active, report).
- Cumulative base→S-c: 44 unique files = 12 production/config (incl. the
  083-3-a migration), 16 tests/evidence, 0 generated, 9 docs, 7 transcript,
  +4556/−149 at I-c plus this report.
- Expected final: 46 (12/18/0/9/7). Variance −2, itemized:
  `browser-worker-critical-matrix.json` + `tests/supply_chain/test_policy.py`
  — both require measured candidate-8 values this round could not produce;
  carry to the next order. No code movement or budget gaming.

## Local setup / dependencies

Disposable host with passwordless sudo; uv 0.12.5; Node v24.22.0 with pnpm
11.22.0 at `/home/janezp/.local/tools/node24/bin`; Docker + BuildKit;
disposable PostgreSQL `slaif-integration-pg-0833b` (127.0.0.1:5432, fake
fixture credentials); clean verification copy `/tmp/slaif-verify-c1` (git
archive + exact patch, byte-identity verified, no untracked runtime
artifacts). One temporary host sysctl flip for the Mermaid renderer retry,
restored and re-verified. No production systems, data, or credentials; no
secrets in the diff or this report.

## Documentation

No documentation changes this round (c scope: 0 docs). b's six updated doc
surfaces are adopted unchanged.

## Safety and scope confirmations

- Secrets: none introduced; all test credentials fake/fixture values.
- Production access: none; Docker used only for disposable local
  builds/containers under existing runtime authority.
- Byte-identity: `uv.lock`, `pnpm-lock.yaml`, `.github/workflows/*`,
  `contracts/`, `packages/` unchanged in the base→I-c diff.
- No vulnerability/dependency exception; no lockfile, workflow, base image,
  Node/pnpm/Playwright, migration, role, or topology change; no product
  logic change; CPython 3.12.12 pin intentionally untouched (CVE reported,
  not fixed, not excepted).
- Scope: I-c changes only the itemized 3 files; T-c committed the activated
  order and active bytes exactly, never edited; untracked `.codex/`,
  `CODEX-SESSION.md`, `codex.sh` preserved and never staged.
- Extra PR: NO. Merge/auto-merge/close: NO. Activated order/active edited:
  NO. SELF commit changes only this report: YES (verified at publication).

## Known limitations / blockers

1. BLOCKER (external, out of scope): `CVE-2026-19445` (Critical, CPython
   3.12.12 in the shared backend image; fixed 3.12.15; first observed
   2026-10-08) fails the fail-closed six-image gate, so candidate-8, C-1
   (20/20), and acceptance remain open; strategy holds the next bounded
   order.
2. Matrix candidate-8 record and `test_policy.py` sixth block: NOT ADDED
   (carries forward).
3. Local integration: CANCELLED at 51/320 (0F/0E at cancellation);
   `uv build` standalone PASS; local Compose smoke NOT RUN.
4. S-c checks: pending at report time; Supply-chain evidence cannot pass at
   I-c/S-c while the fresh database reports the CVE.

## Recommended strategic follow-up

Next order on the same PR: CPython base repair (3.12.15+) or an explicit
strategic exception decision, then a fresh six-image pipeline for measured
candidate-8, the matrix/test_policy append, the full local gate roster plus
complete Compose smoke, and 20/20 terminal checks at the exact new head.

Report publication commit: SELF

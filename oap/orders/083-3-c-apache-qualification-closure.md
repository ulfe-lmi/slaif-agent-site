# OAP Work Order — 083-3-c: Apache pin repair and qualification closure

> STATUS: ACTIVATED strategic continuation. Operative only when selected by
> exact active `083-3-c` and delivered with exact control FIFO `OK`. The
> activation timestamp is recorded in the strategic timing ledger.

## 1. Identity, authority and verified state

- ID: `083-3-c`; Objective 083, semantic increment 3; CLOSURE_ONLY.
- Mode: AMEND_EXISTING_PR. NO NEW PR. No executor merge/auto-merge/closure.
- PR: [#102](https://github.com/ulfe-lmi/slaif-agent-site/pull/102).
- Branch: `oap/083-3-a-cache-outbox-consumer`; base `main`.
- Starting report-only head S-b: `ee96af9f96d16d52f3efe34012314792a888ed89`.
- S-b parent / b implementation: `942847a3a9e40fe0ab8129d90b19e82ccf964baf`.
- Verified main: `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- b status and observed CI: `Executor PARTIAL/BLOCKED; I-b had 18 SUCCESS and 2 FAILURE. At 2026-10-17T23:35:11.352569+00:00 S-b observed 7 IN_PROGRESS, 13 SUCCESS. No acceptance; required Apache repair remains independently verified.`.

Human authority remains the explicit browser refresh authorization and the
active goal: "now continue OAP coding cycle until product is finished as
planned". This is a necessary bounded package repair within the existing
Apache 2.4 / Ubuntu 24.04 stack; no architecture, license, credential,
service, publication authority or network change is authorized. The coding
agent MUST remain visible in this tmux window's other pane using
`codex --yolo --profile qwen-neumann` with no model/provider override.

Actual repository: `/home/janezp/codex-work/slaif-agent-site`.
Actual strategic workspace: `/home/janezp/codex-supervision/slaif-agent-site`.
Verified control/response FIFOs are in the strategic workspace; read control,
write response, exact bytes `OK` (`4f4b`), no LF. Historical /home/ubuntu paths
are obsolete. Read coding AGENTS/protocol, compact architecture and applicable
governance; no full ARCHITECTURE.md. Select work only after this round's valid
signal and exact `oap/active` = `083-3-c`.

## 2. Finite closure and package evidence

083-3-a criteria 1–10 remain accepted; C-1 (all 20 successful checks at exact
final report head) remains unresolved. b introduced the exact stable browser
pins but could not finish qualification because its six-image build attempted
Apache `2.4.58-1ubuntu8.15`, which current Ubuntu apt indexes no longer list.
The Apache
Dockerfile was outside b scope, so stopping and reporting was correct.

This round's finite closure list is:

1. C-2: restore fresh Apache buildability using the four exact replacement
   package pins below, without changing its base image/OpenSSL/configuration.
2. Finish b criteria 3–5: real successful qualification record/test pins,
   all remaining required local verification and complete Compose smoke,
   and all 20 terminal-successful checks at exact final report-only S-c.
3. Preserve all earlier accepted behavior, immutable history, scope and honest
   evidence, including the report-only SELF chain and cumulative budget.

The c report must explicitly correct these b-report inaccuracies without
editing b: the local Buildx/TARGETARCH environment retry was not a CI flake
rerun (strategy verified all six T/I/S CI/CodeQL runs have run_attempt=1,
so the one-CI-rerun allowance remains unused); initial local integration
failed for missing DB and local Node/tree gates were attempted with runtime
artifact/build-lock errors, rather than simply never attempted; the b report
mistyped the Apache 8.17 apache2 SHA (`03b763` instead of `03b63`; use the
verified table below); and old candidate-7 test assertions remain in the
current block until the candidate-8 append, not solely a previous block.
Use retained logs for exact attempt results; if details were not retained,
say so. Never infer a pass from a pipe's tail exit status or rewrite history.

Strategy independently fetched official noble-updates and noble-security
package indexes at 2026-10-17T22:55:59Z. Updates has Apache 8.16; SECURITY
has 8.17. Both still have OpenSSL `3.0.13-0ubuntu3.16`. Use SECURITY 8.17.
Official [USN-8931-1](https://ubuntu.com/security/notices/USN-8931-1), published
2026-10-14, identifies Noble Apache `2.4.58-1ubuntu8.17` as its fixed version.
This is package availability/security-patch evidence, not a successful image
scan; fresh qualification remains mandatory.

All four packages were independently downloaded read-only and matched the
official index's SHA-256 and size at 2026-10-17T22:56:50Z:

| Package | Version | Bytes | SHA-256 |
|---|---|---:|---|
| apache2 | 2.4.58-1ubuntu8.17 | 90226 | `289d4b306cc0ab3db559e7b111cc3a1f1dec03b63a71bc5eb8096c190e1b8e1f` |
| apache2-bin | 2.4.58-1ubuntu8.17 | 1337880 | `7c31f0e45695c1d0335d4bf654c644fc0977006bbefa22e1b2e0ef04d2e18744` |
| apache2-data | 2.4.58-1ubuntu8.17 | 163308 | `aad82c20829ddbef9e868180b53a82470676966df1232f6eca1aa8526edada69` |
| apache2-utils | 2.4.58-1ubuntu8.17 | 100358 | `754eb0a2896c411d796073c8c2ec74a3b174ce64732c30afffda5122fa99bc69` |

Index: <https://archive.ubuntu.com/ubuntu/dists/noble-security/main/binary-amd64/Packages.xz>.
Artifact URLs are the index Filename entries under
`https://archive.ubuntu.com/ubuntu/`. Reverify exact availability/identity in
the pinned-base apt environment before implementation; if changed, report the
specific discrepancy, do not silently select other versions or a paid source.

## 3. Closed implementation scope

Exactly these five non-transcript files may change in c:

1. `infra/apache/Dockerfile`: ONLY four Apache version literals
   `2.4.58-1ubuntu8.15` → `2.4.58-1ubuntu8.17`. Preserve exact Ubuntu base
   digest `33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`,
   OpenSSL pin, modules, application edge config, labels and build gates.
2. `supply-chain/policy.json`: ONLY the same four Apache apt-pin literals.
   All b Chrome identity values and other policy fields remain unchanged.
3. `tests/packaging/test_oci_contract.py`: ONLY the matching four Apache
   version assertions; preserve all other test strength and b Chrome pins.
4. `supply-chain/browser-worker-critical-matrix.json`: finish b's planned
   candidate-8 append ONLY AFTER a successful measured six-image pipeline.
   Preserve all five existing qualification records and other matrix data.
5. `tests/supply_chain/test_policy.py`: finish b's required history count
   5→6 and previous/current assertion blocks, using exact old candidate-7
   values and actually measured candidate-8 values. No weakened assertions.

No new docs, generated contracts, production logic or migration. The existing
b pin/docs changes are adopted unchanged. The Chrome target remains
`155.0.8059.84`, revision `1697595`, archive SHA-256
`cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc`,
executable `/ms-playwright/chromium-1697595/chrome-linux64/chrome`.
All b requirements and non-goals remain in force except this expressly named
Apache package repair and this round's transcript. No scope by implication.

## 4. Verification, evidence and acceptance

1. Fetch/reconcile the named PR/base/start S-b and exact b report/parent.
   No duplicate increment PR or existing c report; preserve untracked runtime
   `.codex/`, `CODEX-SESSIONS.md`, `codex.sh`. Commit T-c locally first:
   exactly this activated order and active bytes unchanged. Publish T-c
   together with I-c after local work, before report-only S-c. No other PR
   touched.
2. Record official package metadata/download/hash/size verification and native
   apt availability under the pinned base. Apply only section 3 changes.
   Zero old Apache 8.15 literals in the three current pin/assertion files;
   four new 8.17 pins in each; OpenSSL strings and base digest unchanged.
3. Run existing policy validation, exact repository policy, packaging and
   supply-chain tests, and Ruff check/format on touched Python paths. Finish
   every failed/missing b standing gate; record exact commands/exit codes.
   Successful b evidence for byte-identical unaffected paths may be adopted
   with its tested SHA/tree identity and exact result disclosed, not described
   as rerun. Final exact-head GitHub matrix is still mandatory in full.
4. Run a fresh complete existing six-image supply-chain pipeline, preserving
   double-build reproducibility, all manifests, license/SBOM checks, fresh
   database age/checksum requirements, scanner and image digest pins, and all
   fail-closed gates. Verify actual installed Apache versions 8.17 and
   unchanged OpenSSL version, actual Chrome executable version/hash/PURL,
   absence of CVE-2026-103628 from refreshed browser matches, zero unexcepted
   Critical across ALL SIX images, empty exception sets, full High and lower
   severity counts. Save diagnostics and real failure history. No cached old
   Apache substitute or unsigned packages. No fake qualification PASS.
5. Append candidate-8 only from measured successful results; update matching
   assertions and rerun changed policy tests. Record metadata timestamp,
   archive identity, image/executable digests, scanner/database provenance,
   all six-image results and scan checksums. Prior history unchanged.
6. Build current product images without stale browser/Apache reuse and run
   COMPLETE current `tools/compose/smoke.sh` through public NGINX, all 19
   Playwright projects and existing browser-worker proof. Record exact return
   code, project/results counts, new browser-worker-image-policy line and
   fresh-image provenance. No project/filter reduction. Serialize colliding
   host builds; use pipefail/PIPESTATUS, not a masked tail/tee exit code.
7. Preserve b contracts/packages byte identity to the original base and
   starting b head. Reprove stripped OpenAPI digest
   `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`.
8. Replace the existing PR's creation-time placeholder description with a
   concise description of the delivered outbox/public-surface behavior and
   runtime qualification, observed validation and material limitations. No
   predicted green checks, broader MVP claim, new issue or comment. This is
   authorized metadata maintenance of the same PR, not another repository
   file. Push implementation to the same PR, inspect exact-head checks and repair
   only named in-scope defects. All 20 required check names are exactly the
   roster in b section 5/R3; at FINAL report-only S-c every one must be
   terminal SUCCESS, none missing/cancelled/failed/pending. Root strategy
   independently verifies S-c. No deterministic CI rerun; at most one
   documented unmodified flake-class rerun across this PR (unused, verified
   independently from GitHub run attempts; b's local retry wording is corrected
   explicitly above).
9. Publish exactly `oap/reports/083-3-c-apache-qualification-closure.md` as
   a lint-clean atomic report-only S-c. Report contains literal 40-hex
   implementation head I-c and `Report publication commit: SELF`; S-c's
   first parent is I-c, sole path this report, verified remote head S-c.
   Include T-c and all pushed implementation SHAs, order hash, active bytes,
   per-criterion evidence, commands/results/failures/skips, adopted b evidence
   versus newly run checks, measured qualification, per-check SHA/run table,
   exact current and cumulative file categories/budgets, and scope/security
   confirmations, and the explicit b-report corrections above. Use one exact
   status enum, not a combined label. Pending S-c checks are honest pending,
   not green.
10. No repo mutation after S-c. Signal response FIFO exact OK only after
    immutable report and claimed remote state exist. Then end this bounded
    coding goal and return to control wait. COMPLETE is advisory; omitted
    verification means PARTIAL/BLOCKED. If a new out-of-scope failure appears,
    preserve diagnostics and report it; never add another repair/exception.

## 5. Non-goals, security, setup authority and review budget

No vulnerability/license exception, new issue/PR, other dependency or lockfile,
workflow, base image, Node/pnpm/Playwright/foundation change, other Dockerfile,
server/proxy configuration, production code, DB role/schema/credential, service,
mount, port, network, quota, source policy, publication or artifact-policy change.
No dependabot work. Agent authority remains site/workspace-bound, human review
and atomic conflict-safe promotion unchanged, media immutable, artifacts
private, browser observational and separately confined without DB/reviewer/
human credentials. No secrets or production systems. Only registry foundation
`agent-cow-postgresql==0.2.0`; no Git/path fallback or hosted requirement.

The executor owns all routine disposable tooling/Buildx/scanners/test databases/
browsers/services. Use the prepared Node path
`/home/janezp/.local/tools/node24/bin` as appropriate. Local untracked runtime
artifacts must not contaminate whole-tree verification or enter commits;
use a clean verification copy with exact tracked tree/patch identity when
needed, preserve tracked gate configuration. Never transfer setup to human.

This round's budget: 2 production/config files, 0 migrations, 3 test/evidence
files, 0 generated, 0 docs, 3 transcript paths (order, active, report).
Expected production change: 8 literal replacements; tests/qualification
<=160 changed lines. Expected final cumulative base-to-head: 12 production/
config including the existing migration, 18 tests/evidence, 0 generated,
9 docs, 7 transcript = 46 unique files. Compute actual counts and itemize
every variance. The production-file review trigger is not expected to fire;
CLOSURE_ONLY has nonetheless been in force since b activation. No new semantic
family or adjacent feature. No code movement/budget gaming.

Only strategy accepts and merges, in merge-commit mode after independent scope,
architecture/security/evidence review and 20/20 exact-S success, then verifies
merged PR, remote main and post-merge checks. 084 remains a later separately
ordered increment. Earlier orders/reports remain immutable.

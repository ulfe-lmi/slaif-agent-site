# OAP Work Order — 083-3-b: stable browser refresh (083/3)

## 1. Identity, authority, verified state

- ID: `083-3-b`; numeric objective 083; semantic increment 3.
- Mode: **AMEND_EXISTING_PR**. NO NEW PR. Strategy alone reviews and merges.
- Repository: `ulfe-lmi/slaif-agent-site`.
- Existing PR: [#102](https://github.com/ulfe-lmi/slaif-agent-site/pull/102).
- Required branch: `oap/083-3-a-cache-outbox-consumer`; base `main`.
- Starting remote head: `8b4842d4b01d5974cd953b555857bec47a32aec7`.
- Verified remote main: `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- Strategy reverified GitHub on 2026-10-17: PR OPEN/MERGEABLE/BLOCKED,
  zero reviews/comments; exact head has 19 SUCCESS checks and one FAILURE,
  `Supply-chain evidence`. Main is unchanged. Merge commits are enabled;
  main has no branch-protection object (API 404). The OAP 20-check gate
  remains mandatory regardless of branch protection.
- Human authorization, verbatim, received in this session on 2026-10-17:

  > Refresh the browser to the current stable Chrome for Testing as 083-3-b
  > on PR #102. Use the coding agent, verify all 20 checks pass, then review
  > and merge.

The human selected refresh, not a security exception. The inert exception
draft outside the product repository is not an order and must not execute.
Read coding AGENTS, coding communication protocol, compact architecture,
the applicable governance amendments, prior `083-3-a` order/report, and the
079-2-g/h refresh precedents. Do not load full ARCHITECTURE.md.

## 2. Runtime and orchestration

Historical `/home/ubuntu` paths in governance have relocated. Actual paths:

```text
REPO_ROOT=/home/janezp/codex-work/slaif-agent-site
STRATEGIC_WORKSPACE=/home/janezp/codex-supervision/slaif-agent-site
CONTROL_FIFO=/home/janezp/codex-supervision/slaif-agent-site/control.fifo
RESPONSE_FIFO=/home/janezp/codex-supervision/slaif-agent-site/response.fifo
```

Both FIFOs were verified as actual FIFO objects. Read control, write response;
each signal is exactly ASCII `OK` (`4f4b`), with no LF. Select this order only
after the valid control signal and exact `oap/active` = `083-3-b`.
Preserve pre-existing untracked `.codex/`, `CODEX-SESSIONS.md`, `codex.sh`;
never stage them. No other executor is authorized for this round.

## 3. Strategic context and finite closure contract

083-3-a criteria 1–10 were independently accepted as satisfied at the starting
head. Criterion 11 failed solely because the unchanged Chrome for Testing
154.0.8037.92 payload acquired a Critical finding, CVE-2026-103628. The finite
rejection checklist is C-1: all 20 checks successful at the exact final head.
The earlier no-patched-build premise is superseded by the verified stable
release below. Close C-1 with a mechanically bounded browser identity refresh
and fresh qualification, preserving the previously reviewed product behavior.

The human subsequently resumed the strategic goal: "now continue OAP coding
cycle until product is finished as planned". That authorizes strategy's later
sequencing; this executor turn remains bounded exclusively to 083-3-b.

This order explicitly supersedes the exception-specific closure recipe in
the historical rejection record; the record and all earlier orders/reports
remain immutable. No exception is authorized. No Objective 084 work is
authorized by this order. Strategy adopts CLOSURE_ONLY at this activation:
only this named security repair, its evidence, and necessary current pin docs
may enter. No new semantic family.

## 4. Exact target identity and preflight

Strategy fetched the official stable metadata on 2026-10-17 and independently
stream-hashed the official linux64 archive at 2026-10-17T21:57:09Z:

```text
metadata timestamp: 2026-10-17T09:18:35.172Z
channel: Stable
version: 155.0.8059.84
revision: 1697595
platform: linux64 / linux/amd64
archive URL: https://storage.googleapis.com/chrome-for-testing-public/155.0.8059.84/linux64/chrome-linux64.zip
archive SHA-256: cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc
archive bytes: 199014491
executable: /ms-playwright/chromium-1697595/chrome-linux64/chrome
expected version: Google Chrome for Testing 155.0.8059.84
```

Authoritative metadata endpoints:

- <https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json>
- <https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json>

Before any implementation: fetch/reconcile GitHub; prove the exact open PR,
base and starting head, no duplicate increment PR, no existing round report;
inventory all current old pin/version/revision/archive-hash references.
Independently verify this target's official linux64 entry and archive hash and
byte size. Record endpoint timestamps, selected entry, acquisition and digest
evidence. If Stable has advanced or identity/hash differs, do not silently
choose a different target: report the discrepancy for the next strategic
decision. No Beta/Dev/Canary selection. Runtime installation/setup belongs to
the coding agent; strategy does not operate browsers/scanners/databases.

## 5. Bounded requirements

### R1 — Pin and identity references

Only these 15 non-transcript files may change this round:

1. `services/browser-worker/Dockerfile`: archive URL/hash, asserted version,
   provenance comment, fixed executable/version environment, copied directory.
   Preserve both Playwright base-image digest pins and all confinement.
2. `supply-chain/policy.json`: five chromium identity values only (revision,
   version, executable, archive URL/hash).
3. `tools/supply_chain/policy.py`: matching five literal identity assertions
   only. Validation schema/logic remains unchanged.
4. `tools/supply_chain/evidence.py`: browser-worker boundary directory literal
   only, `chromium-1689415` to `chromium-1697595`. No normalization/gate change.
5. `tools/compose/smoke.sh`: fixed browser path/version/revision assertions and
   diagnostic identity line only; preserve every smoke project and assertion.
6. `tests/packaging/test_oci_contract.py`: matching version/hash identity pins.
7. `tests/supply_chain/test_evidence.py`: matching browser PURL/version fixture.
8. `tests/supply_chain/test_policy.py`: qualification history count 5 to 6 and
   existing previous/current qualification assertion blocks only, preserving
   test strength. Previous becomes the exact existing candidate-7 values;
   current asserts measured candidate-8 values.
9. `supply-chain/browser-worker-critical-matrix.json`: append exactly one
   candidate-8 qualification record using existing candidate-7 schema and fresh
   measured values. Preserve every prior entry and other matrix data exactly.
10. `README.md`: current browser qualification statement only.
11. `docs/CONFIGURATION.md`: current executable/version rows only.
12. `docs/DEPLOYMENT.md`: current browser identity/archive statements only.
13. `docs/LICENSE_POLICY.md`: current browser version statement only.
14. `docs/SECURITY.md`: current browser version/revision/hash statement only.
15. `docs/SUPPLY_CHAIN.md`: current browser identity statements, including the
    stale active-qualification sentence currently naming 153.0.8010.52 /
    1681091. Correct that current-truth sentence to the new target; preserve
    actual historical qualification narrative and all immutable evidence.

Use the exact new target consistently. Do not perform blind global replacement
inside historical matrix entries or provenance narrative. Old pin identifiers
may remain only in explicitly historical records and the previous qualification
test block; record/classify residual matches rather than forcing brittle grep
counts. Preserve the other current-truth surfaces' product status this round;
the refresh does not itself accept or merge 083/3.

### R2 — Measured qualification and mandatory verification

Run a full fresh local supply-chain evidence pipeline using the repository's
existing pinned scanner/tools and fail-closed gates. Preserve double-build
reproducibility, byte manifests, registry locks, license policy, SBOM scope,
fresh-database age/checksum validation and all six-image coverage. Capture:

- browser archive identity, built image digest, executable version and SHA-256;
- official metadata entry/timestamp and unchanged Playwright/node/base pins;
- fresh scanner database schema/build/checksum, scanner versions, SBOM Chrome
  PURL/version, full severity counts including High, scan checksums;
- zero unexcepted Critical findings for all six images, no exception entries,
  and absence of CVE-2026-103628 from the refreshed browser matches;
- candidate-8 measured qualification data, preserving prior entries exactly.

Do not label an unsuccessful or incomplete scan PASS. If an unrelated image,
new Critical finding, reproducibility regression, or external failure blocks
qualification, capture exact failure diagnostics and report PARTIAL/BLOCKED.
Do not add exceptions, weaken gates, change unrelated dependencies or broaden
this 15-file allowance to chase a green result.

Run policy validation, repository policy, targeted packaging/supply-chain
tests, and Ruff check/format on touched Python paths. Run every standing
mandatory coding-constitution check applicable to this round; report exact
pass/fail/skip/not-run honestly. Build the refreshed browser image without
stale image reuse, then run the COMPLETE current Compose smoke through public
NGINX (all 19 projects at the starting head, not the old 13-project precedent).
Record fresh image provenance, the new browser-worker-image-policy line,
all-project counts/return code, browser E2E results, and any initial failure.
Preserve six E2E targets and existing media/publication/fault evidence.

### R3 — GitHub checks, immutable transcript and report

Commit T first: exactly the published order and `oap/active` bytes unchanged.
Then bounded implementation/evidence/docs commits. Push only this branch.
Inspect all required checks at the implementation head; fix only in-scope
pin mistakes before report publication. A substantive failure outside scope
requires honest diagnostics and return to strategy, not self-expansion.

Then atomically publish exactly one new report:
`oap/reports/083-3-b-stable-browser-refresh.md`.
Lint complete report before publication. S must be report-only, first parent
equal to the report's literal 40-hex `Implementation head SHA`, and contain
`Report publication commit: SELF`. Push and verify remote S, parent and exact
report bytes BEFORE exact response FIFO OK. No mutation follows S this round.
Checks newly started by S may be honestly pending in the immutable report;
strategy independently waits for all 20 at S. Never edit a published report.

Flake rule: no rerun of deterministic failure or rerun-until-green. At most
one documented rerun for a documented flake class at an unmodified head across
this PR; 083-3-a consumed none. Report the exact signature/run/attempt if used.

The required roster is exactly:

```text
Repository policy
Dependency review
Markdown
Mermaid
Node contracts
Python 3.12 quality and package
Python 3.13 quality and package
Python 3.14 quality and package
Foundation PostgreSQL 14
Foundation PostgreSQL 15
Foundation PostgreSQL 16
Foundation PostgreSQL 17
Foundation PostgreSQL 18
Compose and edge packaging
Supply-chain evidence
Detect supported languages
Analyze (actions)
Analyze (python)
Analyze (javascript-typescript)
CodeQL
```

## 6. Security, scope and explicit non-goals

- NO vulnerability/license exception, new issue, dependency/lockfile, workflow,
  base image, Node/pnpm/Playwright upgrade, other Dockerfile, migration, role,
  privilege, service/mount/environment topology, browser-policy expansion.
- NO product logic, outbox/media/reference behavior, renderer/Puck, REST/MCP
  contract, publication authority, source input or network/confinement change.
- `contracts/` and `packages/` remain byte-identical to starting head and base;
  OpenAPI stripped identity remains
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`.
- Agent remains workspace/site-bound; browser observational and separately
  confined, with no DB/human/agent/reviewer credentials or publication power;
  private artifacts stay private; immutable media and human review preserved.
- Foundation stays registry-only `agent-cow-postgresql==0.2.0`; no new hosted,
  paid/account-bound/non-permissive runtime; no secrets or production access.
- NO dependabot work (current open PRs #103/#104/#105 included), adjacent
  objective, new PR, merge, auto-merge or close by the coding agent.
- NO rewrite of earlier orders/reports or matrix history. Local untracked
  runtime artifacts remain untouched and unstaged.

## 7. Observable acceptance and report contract

1. Correct PR/base/branch, start SHA, official stable target/archive evidence;
   T order/active bytes identical to strategy's activated files.
2. Diff from starting head changes only the 15 named identity/evidence/docs
   files plus this order, active and new report; literal identity coherence
   verified; historical matrix entries semantically and textually unchanged.
3. Candidate-8 contains measured successful qualification, full fresh local
   six-image pipeline and reproducibility/license/SBOM/checksum proof; no
   exceptions; target executable/version/hash and CVE closure proven.
4. Policy/repository/targeted tests/Ruff and full fresh Compose smoke pass;
   standing checks accurately reported; failure/retry history disclosed.
5. At exact report-only S, ALL 20 required checks terminal SUCCESS; no
   failed/cancelled/missing/pending check. Strategy independently verifies.
6. Starting report/order and prior qualification evidence unchanged;
   contracts/packages byte identity and stripped digest preserved; no
   unauthorized files, logic, dependencies or trust changes.
7. Report includes exact T and implementation SHAs, SELF, file inventory,
   order SHA-256, active bytes/hex, measured qualification, commands/results,
   per-check table with run IDs and SHA actually observed, complete failures,
   deviations, local setup, limitations, and cumulative grouped size table.
   S changes only the new report; its first parent is literal implementation
   head; verified remote head is S before FIFO response.

Status COMPLETE is advisory and requires all executed report-time criteria;
pending S checks are expressly identified, never called green. Unresolved
required verification means PARTIAL/BLOCKED. Strategy alone closes C-1 and
accepts after full independent review and terminal-successful exact-S CI.

## 8. Predeclared cumulative review budget and local authority

Starting base-to-head: 27 files, +3615/-98. Grouped: 5 production/config +
1 migration (6 combined), 14 tests/evidence, 0 generated, 4 docs, 3 transcript;
550 substantive implementation lines reported/previously reviewed.

This round: 5 production/config files (Dockerfile, policy JSON, policy Python,
evidence directory literal, smoke assertions); 0 migrations; 4 tests/evidence
(three tests and matrix); 0 generated; 6 docs; 3 transcript paths (2 new plus
active). Expected substantive implementation <=100 lines; qualification/test
evidence <=160 changed lines; docs <=40 changed lines; order/report separate.
Cumulative expectation: 10 production/config +1 migration, 18 tests/evidence,
0 generated, 9 docs, 5 transcript = 43 unique files (README overlaps; active
overlaps). Count actual base-to-head totals and classify every variance.

The production/config review trigger is not expected to fire (11 including
migration), and the repair is one coherent qualification family. Nevertheless
CLOSURE_ONLY is adopted explicitly at this activation following rejection;
do not introduce any new family. No budget gaming or unreviewable growth.

The coding agent owns all necessary disposable local packages, browsers,
Docker/services/databases/scanners/test setup under the existing runtime
authority; never transfer routine setup or log collection to human/strategy.
Real production/protected access, credentials, external outage, unsafe scope
or architecture ambiguity must be reported without weakening requirements.

Strategy will independently review, merge in merge-commit mode only with
20/20 successful exact-S checks, verify merged PR and remote main and
post-merge checks, and update acceptance/state/timings. Any later 084 activation
requires its own new bounded strategic order after verified 083 acceptance.

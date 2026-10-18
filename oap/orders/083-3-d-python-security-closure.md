# OAP Work Order — 083-3-d: Python security pin and qualification closure

> STATUS: ACTIVATED strategic continuation; operative only after exact
> active083-3-d and this round's control FIFO OK. Timing is in strategic ledger.

## 1. Identity and verified state

- ID: `083-3-d`; Objective 083, semantic increment 3; CLOSURE_ONLY.
- Mode: AMEND_EXISTING_PR; NO NEW PR, merge, auto-merge or PR closure.
- PR: [#102](https://github.com/ulfe-lmi/slaif-agent-site/pull/102).
- Branch: `oap/083-3-a-cache-outbox-consumer`; base `main`.
- Starting report-only S-c: `c78afd5f3411d3d42d95cfec67329c2d12c1d5d9`.
- S-c parent / c implementation head: `33d38966c79fb4387eba279872f2000b1adcf6f0`.
- Verified main: `214909f3adf86b8dd4b9fa4a3b1ea9fca78faa2c`.
- Current remote observations: At 2026-10-18T00:28:57.011956+00:00 S-c has20 check runs: 7 IN_PROGRESS, 13 SUCCESS. No acceptance; deterministic backend Critical verified in local six-image evidence. I-c CI was superseded/cancelled when S-c was pushed..

Human authority remains the browser refresh authorization and active full
product OAP goal. This is a necessary security patch in the existing Python
3.12 / Alpine 3.23 family, preserving architecture and registry foundation
`agent-cow-postgresql==0.2.0`. No security exception is authorized. The visible
executor remains in this tmux window's other pane, running exactly
`codex --yolo --profile qwen-neumann`, with no model/provider override.

Actual repo `/home/janezp/codex-work/slaif-agent-site`; strategic workspace
`/home/janezp/codex-supervision/slaif-agent-site`. Read coding AGENTS/protocol,
compact architecture, applicable governance and a/b/c orders/reports. Never
load full ARCHITECTURE.md. Verified FIFOs are in the strategic workspace:
read control, write response, exactly ASCII OK (`4f4b`), no LF. Execute only
after this round's signal and exact active `083-3-d`; never select by filenames.

## 2. Finite security finding and exact target

The c pipeline built/scanned all six images, but its existing fail-closed gate
returned 1: backend has one unexcepted Critical CVE-2026-19445 against
`pkg:generic/python@3.12.12`. The other five raw scans contain zero Critical;
that does not make the failed overall qualification a PASS. Candidate-8 was
correctly withheld. c's Apache repair is adopted; remaining b/c acceptance
obligations are still required. No unrelated feature work enters this PR.

Finite closure: C-2 Apache repair is satisfied; C-1 final20/20 and full
qualification/smoke remain open. C-3 is evidence integrity: the immutable c
report claims isolated integration cancelled at51/320 with0 failures, but
strategy observed orphan uv PID1237274/pytest1237281 still alive at00:25–26Z,
and its retained log contains an F marker. Preserve that log, inspect actual
current processes and clean up only those stale objective descendants before
new tests. Do not assume killing a wrapper terminated its child. Record the
failed/unfinished result honestly; no0-failure or completed-cancellation claim.
Correct c explicitly in the new report without editing it. c's approximate
`00:1xZ`/`00:2xZ` strings are not exact timestamps; supply retained exact times
or say unavailable. Only the HUMAN can approve a vulnerability exception;
c's suggested strategic-exception wording does not grant that authority.

Strategy independently inspected all six c scan JSON files and verified the
official [Python 3.12.15 release](https://www.python.org/downloads/release/python-31215/)
lists CVE-2026-19445 as fixed. The
[upstream issue](https://github.com/python/cpython/issues/156293) describes a
server-side SSLContext lifetime error with SNI callbacks. Do not infer product
exploitability or create an exception from its conditional trigger. Patch the
interpreter and preserve the release-policy gate.

At 2026-10-18T00:12:22Z strategy fetched the official registry index, amd64
manifest and config read-only, independently checking each payload hash and
registry digest header. Exact target:

```text
image: docker.io/library/python:3.12.15-alpine3.23
multi-platform index: sha256:1fd55c2f838c4f76262f9eeed899ff9168ea96ac383c61667d6f204325e1f169
linux/amd64 manifest: sha256:9ce5a4e59b833c002e1c4196c60ec0b38977e3235d626298ba7ffe2e64f5a30c
amd64 config: sha256:56d444819cc60d5188b3e0d64396cf76a0b3e64a952836cb3155f6dc5a7e80b9
PYTHON_VERSION: 3.12.15
PYTHON_SHA256: c2c4321961fab0fb999d66e0cecf521c2ab3994c7992873ea99e306c1094fd5a
source revision: 2a3b794c223ab067d122719541cdd54a068732a5
source directory: 3.12/alpine3.23
```

[Immutable official Dockerfile](https://github.com/docker-library/python/blob/2a3b794c223ab067d122719541cdd54a068732a5/3.12/alpine3.23/Dockerfile).
Registry metadata and c raw scan summaries are indexed at
`/tmp/oap-083-3-d-prep/`. These are strategic read-only evidence aids, not
substitutes for your verification. Independently reverify exact target before
editing; if identity or availability differs, report rather than substitute.

## 3. Closed scope and non-goals

Only these FIVE non-transcript files may change:

1. `services/backend/Dockerfile`: Python provenance comment and both FROM
   literals only. Replace 3.12.12 and index digest
   `2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0`
   with the exact 3.12.15 index above. Preserve uv, frozen install, package
   overlays, paths, deterministic metadata, non-root user and confinement.
2. `supply-chain/policy.json`: ONLY `oci_sources.python` to the same exact
   target. Preserve Apache8.17, OpenSSL, Chrome and every other field.
3. `docs/DEPLOYMENT.md`: ONLY the current Python image/version/digest table row.
4. `supply-chain/browser-worker-critical-matrix.json`: candidate-8 measured
   successful six-image qualification append, preserving all five old records
   and every other field. Append only after full actual pipeline PASS.
5. `tests/supply_chain/test_policy.py`: history length5→6 and existing
   previous/current qualification assertions only. Previous exactly candidate7;
   current exactly measured candidate8. No weakened tests.

No other Dockerfile, application logic, migration, lockfile, foundation,
Python minor family, Alpine family, dependency, workflow, scanner, exception,
license policy, role, service, secret, mount, port, network, source policy,
publication, renderer, media or artifact behavior change. No dependabot work,
adjacent objective, new semantic family or historical transcript rewrite.
Preserve untracked `.codex/`, `CODEX-SESSIONS.md`, `codex.sh`, never stage them.

Browser target remains CfT155.0.8059.84/revision1697595, archive SHA256
`cf0f049892dea22e6a6db26d47ed0d7776b7158edcbec4634086633df8bafcbc`;
Apache remains2.4.58-1ubuntu8.17/OpenSSL3.0.13-0ubuntu3.16. All other b/c
non-goals and architectural security/lifecycle requirements remain in force.

## 4. Required execution and observable acceptance

1. Reconcile exact PR/base/start S-c/parent, no duplicate increment PR, no
   existing d report. Commit T-d locally first: unchanged activated order and
   active bytes only. Push T-d with implementation after local verification.
2. Verify official image identity, PSF/permissive attribution and runtime
   compatibility. Apply only section3 literals. Record actual built backend
   interpreter version/hash, SBOM Python PURL and absence of CVE-2026-19445.
   Preserve exact foundation registry source/version/hashes and all lockfiles.
3. Run policy/repository, targeted packaging/supply-chain, Ruff check/format
   and applicable standing checks; exact command, tested tree/SHA and exit.
   Successful prior-round evidence may be adopted only for byte-identical
   unaffected scope, explicitly named as adoption with tested SHA/result.
   Missing/failed/cancelled gates are not passes. Use an exact clean tracked
   verification copy when untracked runtime artifacts contaminate scans.
   Obtain a completed, isolated full
   `uv run --frozen pytest services/backend/tests/integration -q` result,
   preserving real failure diagnostics and classifying every skip. No filter
   reduction or report-time assertion of cancellation without checking children.
4. Run the COMPLETE fresh six-image supply-chain pipeline, preserving double
   builds/reproducibility, manifests, license/SBOM, pinned scanners, fresh
   database age/checksum gates and empty exception sets. All six images must
   have zero unexcepted Critical. Disclose High and lower counts, hashes,
   image/executable/archive/PURL identities and scanner/DB provenance.
   Reverify CVE-2026-103628 absent from refreshed browser matches.
5. Only after actual pipeline exit0 append candidate8 and matching tests;
   rerun those tests. Preserve every previous qualification byte/text meaning.
6. Run COMPLETE `tools/compose/smoke.sh` through public NGINX with fresh-image
   provenance, all19 projects, all six stable devices, existing browser proof
   and Apache adapter. Record real overall exit0 and actual counts/identity
   lines; no project filters or omitted later smoke stages.
7. Do not overlap integration pytest sessions against the same fixture DB or
   colliding host Next builds. Own stale-objective process cleanup and routine
   disposable tooling/DB/browser/scanner setup. Record initial failures and
   cancelled attempts. Use pipefail/PIPESTATUS; a tee/tail/echo exit is not the
   tested command's exit. Restore temporary host settings on every exit.
8. Preserve contracts/packages bytes and recursively stripped OpenAPI digest
   `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`.
   Strip every nested dict key beginning x-slaif-, recurse lists, canonical
   JSON sorted keys/compact separators/default ASCII, UTF8/no trailing LF.
9. Update existing PR description with actual delivered behavior, qualification,
   validation and material limitations. No new issue/comment/PR or predicted
   green status. Describe anonymous canonical public pages/media separately
   from authorized private workspace/review surfaces; do not imply public
   rendering requires an agent capability or invent product proof endpoints.
   Distinguish passed Python gates from incomplete integration attempts, and
   round-specific scope boundaries from the whole increment's contract.
   Push only this branch; inspect implementation checks. No
   deterministic rerun. The single documented CI flake allowance remains
   unused (all c I/S CI and CodeQL runs independently verified at run_attempt=1); local environment repairs do not consume it.
10. All20 required names from b5/R3 must be terminal SUCCESS on final report-
    only S-d. Strategy independently verifies them; pending S checks may be
    honestly pending in the immutable report, never described as green.

## 5. Publication, report and strategic gate

Publish exactly `oap/reports/083-3-d-python-security-closure.md`, complete
lint-clean atomic file, then report-only S-d whose first parent is the literal
40-hex `Implementation head SHA` and sole path is that report. Include
`Report publication commit: SELF`, exact T/I hashes, activated order hash and
active bytes, per-criterion command/result evidence, prior evidence adoption,
real failure/cancellation history, target and full six-image measurements,
per-check observed SHA/run state, and exact current/cumulative budget groups.
Use a single honest status enum. No invented PASS or missing-as-not-run claim.

Push and verify remote S-d, parent and exact bytes before response FIFO OK.
No repository mutation after S-d. End only this bounded coding goal and return
to control wait. If another out-of-scope failure appears, capture exact
diagnostics and close the round honestly; do not spend hours waiting for
unrelated gates or self-expand. No self-acceptance or merge.

Budget: 2 prod/config,0 migrations,2 tests/evidence,1 docs,3 transcript paths
(active overlaps). Expected final cumulative49 files:12 prod/config +1 existing
migration,18 tests/evidence,9 docs,9 transcript,0 generated. Recompute against
verified actual c baseline and itemize variance. CLOSURE_ONLY remains in force;
no product-file review trigger expected. No code movement/budget gaming.

Only strategy accepts and merges after independent all-round scope/security/
architecture/evidence review and20/20 exact-S success, then verifies merged PR,
remote main and post-merge checks. No 084 activation or whole-product readiness
claim follows merely from a report or green CI.

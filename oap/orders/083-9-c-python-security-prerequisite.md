# OAP 083-9-c: resolve the Python security prerequisite on PR113

## Identity, verified state and reason

- Objective083 remains unresolved; bounded semantic increment083/9.
- Mode: AMEND_EXISTING_PR, SAME PR113:
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>.
- Branch: oap/083-9-a-remediate-node-brotli-runtime; base mainD18
  d18b6e4c9423f61de99b516be90619bf2ab5d3e0.
- Starting remote SELFb: 7e2c40f1282088b3ba725e2cb1fc65c487f30c4e;
  sole parent implementation Fb 8802e6abe8af76935ae862b42239a9504cf2e35d.
  ROOT verified live GitHub open/unmerged branch/base/head, full recursive
  remote maps, sole new b-report path, exact remote/canonical/worktree report
  bytes: 487 lines,26697B/SHA256
  b5c354009c089373e3e57c79b9ead75b04b9ee785bca294b237ce730e756a5a3.
- b is formally PARTIAL, NOT accepted/merged. Exact response OK4f4b/2bytes/EOF
  received 2026-11-01T19:43:15.048896Z, sole ROOT reader73297 terminal native0.
  N3 ALL31 NOTRUN; N5 FAILED. Do not replay b or amend historical transcript.
- Fb CI run41339340523:29success/1failure; Supply-chain job124945822680 failed,
  actual exit1; packaging job124945822664 success. SELFb CI is separate/pending,
  not final acceptance. Live main/rules rechecked before this order's preparation:
  strict20 required contexts with correct integrations, plus ten actual PG children.
- Failure artifact13097047617:10630240B/SHA256
  ea64e4dfc1fe975f9e863dbea734ab9a21a59eb90a1ff40a0d7a51323e34fe63.
  ROOT verified all37 payload checksums/exact set. STATUS INCOMPLETE/UNQUALIFIED,
  original_exit_status1, success manifest ABSENT; this is diagnostic evidence.
- Actual backend python3.12.15 binary at /usr/local/bin/python3.12 and
  /usr/local/lib/libpython3.12.so.1.0 has Critical CVE-2026-115557. The same CVE
  has four Medium worker deb hits: python3.12/python3.12-minimal/
  libpython3.12-stdlib/libpython3.12-minimal, all3.12.3-1ubuntu0.15/not-fixed.
  Other four images show no same-CVE hit. Preserve both severity classifications.
  DB actual built2026-11-01T06:20:12Z, schema6.1.10, checksum
  d0e1af9e6491440e1a671d0a0aafc32c5c7cb5cda787dcec3482799ef298f31c.

The CVE concerns compromised eMudhra CA keys; CPython3.12.16 and3.13.18
security releases on October25 add the ssl denylist. Disclosure was October24,
not the scanner first-observed date. Ubuntu currently says Noble python3.12
Needs evaluation, priorityMedium, CVSS9.4Critical. Checked official package
metadata/changelogs did not establish a fixed Noble backport. That is bounded
absence of proof, not exhaustive proof that no fix exists or that .17 is fixed.

Primary references (independently verify the exact bytes before use):

- <https://www.python.org/downloads/release/python-31216/>
- <https://www.python.org/downloads/release/python-31318/>
- <https://ubuntu.com/security/CVE-2026-115557>
- <https://hub.docker.com/v2/repositories/library/python/tags/3.12.16-alpine3.23/>

ROOT official registry metadata: python:3.12.16-alpine3.23 active index
sha256:a4ad86fc2eaa4f9a5c3153776c9fb56e502dbd8e23dfa855d164308f376a6dd2;
linux/amd64 manifest
sha256:fe32c943235f1c5748d1106dbdfa25d206355c1be1ae1e167444a7ff9dfa9422.
These are metadata observations, not local runtime qualification.

## Prospective scope, ownership and size

Read coding AGENTS.md/OAP-COMMUNICATION-coding-agent.md. Same healthy visible
primary CLI, same worktree /home/janezp/codex-work/slaif-agent-site-083-9-a.
Only actual crash permits restart, only codex --yolo --profile early-beta;
preserve xhigh. Primary alone changes source/setup/Git/reports/FIFO. Secondary
may perform ROOT-assigned read-only review, never merge or choose scope.
No hidden coding agent. ROOT alone accepts/merges; green CI is insufficient.

This round prospectively permits the same-series backend Python security patch
and narrow removal of unnecessary inherited worker Python packages. It supersedes
a/b Python-version freezes only for these named changes and the local3.13.18
verification interpreter. No retrospective waiver or historical edit.

Allowed source paths: the sixteen actual source paths already changed at Fb,
plus services/backend/Dockerfile. They are README.md, apps/web/Dockerfile,
services/browser-worker/Dockerfile, docs/CONFIGURATION.md, docs/DEPLOYMENT.md,
docs/LICENSE_POLICY.md, docs/SECURITY.md, docs/SUPPLY_CHAIN.md,
oap/INCREMENTS.md, oap/MVP-PROGRESS.md,
supply-chain/browser-worker-critical-matrix.json, supply-chain/policy.json,
tests/packaging/test_oci_contract.py, tests/supply_chain/test_policy.py,
tools/compose/smoke.sh, tools/supply_chain/policy.py, and the new backend path.
The controlling set is the sixteen actual Fb source paths plus backend Dockerfile;
do not expand it from optional paths in historical orders.

Keep README.md, apps/web/Dockerfile and every other web image input frozen at Fb.
No new source/helper/test path. No unnecessary edits in allowed paths.
Preserve all eight matrix history objects and all65 finding objects byte-exact;
candidate10 remains historical intermediate P1 qualification. Do not append
manufactured current qualification or change historical assertions to pass.

Current source383gross natural added+removed versusD18 across16source paths.
Prospective planning500 plus reserve100, HARD600 gross including both OAP status
docs, excluding ONLY exact activated orders/reports/active. Maximum24 finalpaths:
17source +7transcript (a/b/c orders/reports and active). Measure each logical unit;
at500 return complete remaining forecast; above600 STOP before more edits/tests/
staging/push. No compression/minification/mirrors/deleting proof to fit.
ROOT explicitly reassesses the20-path trigger: one coherent security prerequisite
now covers web Node and worker Node/Brotli/Chrome/Python plus backend Python;
three Dockerfiles, bounded tests/policy/docs/history, separate transcript.
No feature, architectural or dependency-family expansion. Return actual counts.

No app/COW/promotion/audit/API/schema/migration/framework/distro/Playwright upgrade;
no lock/app dependency/foundation/driver/CI/selector/scanner/license-policy change.
Foundation remains registry-only agent-cow-postgresql==0.2.0 with existing uv.lock
hashes, asyncpg main0.31. No PR112 WIP/helpers/driver0.32 import.
Keep run.sh435L/SHA256
fe1144457ab2e0d960030f1b50daad1ebc2bc421138acb67df5bafd313489d04 frozen.
Keep CfT156.0.8078.80/revision1706539/archive+binary hashes, Node24.22.1 hashes,
libbrotli1=1.1.0-2ubuntu0.1, Playwright1.62.1/Noble base digest and Alpine3.23.
All sandbox/seccomp/egress/user10001/read-only/capability/resource controls remain.
No production/deployment/credential work, external exploit or trust/network/mount
widening, telemetry/hosted requirement, private SDK/raw SQL, broad upgrade or
scan suppression/exception/severity downgrade. Runtime browser observations never
authorize publication. Server-owned site/workspace/operation identity, isolated
agent/editor writes, separate reviewer-only atomic human publication, immutable
media/private artifacts and shared trusted renderer remain unchanged.

## Required implementation and first source checkpoint

1. Backend: update BOTH stages to the verified official3.12.16-alpine3.23 index
   above; preserve exact uv0.12.5, frozen app dependencies and OpenSSL3.5.9-r0
   overlay. Preserve PR111 no-system-pip/no-bootstrap-wheel/no-pip-command
   semantics, ensurepip module retained. Inspect the actual new base's pip
   layout; never assume25.0.1 still names its wheel/metadata. No broad glob
   removing unrelated libraries or venv installers, no hidden alternatePython.
2. Worker: remove unnecessary inherited Python from BOTH stages using normal
   package-manager removal, with an explicit exact package set. Seven currently
   catalogued packages are python3,python3-minimal,libpython3-stdlib,
   python3.12,python3.12-minimal,libpython3.12-stdlib,libpython3.12-minimal.
   Raw513-deb metadata shows dependencies among these seven and no outside
   direct dependency on them; that static observation is not an apt simulation.
   Before actual purge, build-time simulation must fail closed if the solver
   proposes any installation, upgrade or removal outside those seven.
   No autoremove, force-depends, Essential removal or falsified dpkg metadata.
   Verify exactly the intended removal and no surviving interpreter/ssl shared
   module/stdlib alternative under /usr or /opt. Keep Chrome/runtime libraries,
   Node/Brotli/installer-removal/build tooling contracts intact.
   If real dependencies or required build/runtime use prevent this bounded
   purge, STOP with exact safe evidence for ROOT; do not silently widen removal
   or substitute unverified Ubuntu fixedness.
3. Adapt existing policy/guards/tests to the actual new backend base and worker
   absence with meaningful negative checks. Preserve prior assertions/coverage.
   Minimal current docs explain exact patch/removal and remaining gates; no
   claim that generic-binary absence or Node non-use proves Python unaffected.
4. Necessary affected checks: actual broader CI Ruff scope,49-case packaging
   suite and44-case supply suite (report real current counts), Markdown for
   changed prose under Node24.22.1. No invented grand total/unchanged gate rerun.
5. Commit/push source checkpoint Pc on SAME branch/PR including byte-exact
   c order/active, existing transcript unchanged. Return literalSHA/tree/parent,
   full diff/per-path hashes/gross/size forecast, actual tests and finite next
   verification plan. STOP before local Docker/build/probe/ALL31 runner writes
   or execution for ROOT full-source and complete-input review. Automatically
   triggered remote CI is separate. No report/SELF/responseOK at this checkpoint.

No runtime command is authorized merely by writing it in a plan. Routine local
tools/packages/venv setup belong to executor, never human/ROOT. Use patched
Python3.13.18 prospectively for c's local verification; uv0.12.5/Node24.22.1/
pnpm11.22.0 and frozen project locks. Record actual interpreter provenance;
b's older3.13.14 observations remain historical.

## Verification after ROOT source/input approval

Fresh local runtime is required for changed backend and worker, at clean Pc.
Use ONE /tmp/oap-083-9-c/verify-python.sh, planning300/HARD400 natural lines
including inline code; complete in memory/count/hash/fullsource BEFORE write,
ROOT review BEFORE execution. No helper/builders/mirrors/unreviewed active input.
Two owned images only, backend and browser-worker; the web P1 local observation
can carry ONLY if ROOT independently proves all actual per-image repository
inputs unchanged through c. It remains a literalP1 observation, never a c run.

Use the b ownership/finite-execution contract: healthy exact refs/names absent
before mutation, unique owned names, created containerIDs durable BEFOREstart,
safe immutable metadata before disposal, no Env/Args/Cmd/secret/full inspect.
Each build1800s/probe120s/phase5400s excluding setup600s andcleanup600s, grace5s;
every operation bounded by positive monotonic remaining time. Actual owned
terminal/reap, each cleanup native, healthy exact post-absence including refs/
containers/anonymous volumes/networks, true END source AFTERcleanup. No foreign
deletion/prune or retry on residual/unknown ownership; retain full streams/natives.

Backend at user10001: actual interpreter path/version/binary+libpython hash/
size/provenance, ssl import and verified upstream denylist implementation
identity (benign local introspection, no compromised certificate/network test),
frozen foundation0.2.0 registry provenance, imports/representative service checks,
system pip distribution/wheel/commands absent while ensurepip module retained.
Worker at user10001: actual seven packages absent plus no interpreter/stdlib/
ssl alternate, full actual dpkg inventory; unchanged exact Node/Brotli roundtrip/
license/linkage/old-NodeSource/tool absence; exact singleChrome hash/version.
CI smoke separately proves browser sandbox/egress/functionality, not network-none
probes alone. Do not claim unexercised counterfactual failure/privacy guarantees.

After runtime, publish final implementation Fc if source needs honest current
documentation. No new matrix history is required. ROOT compares full remote maps
and ALL actual COPY/ADD/Dockerfile/pins/buildargs/invocations per image.
Pc runtime may carry to Fc only for proven identical inputs, with actual literal
Pc labels/IDs distinguished from Fc; source change requires affected new proof.

Fresh ALL31 at clean finalFc: ONE /tmp/oap-083-9-c/all31.sh, planning120/HARD160
natural lines, all active code inline. Complete in memory/count/hash/fullsource
before write; ROOT review before execution. Bind START/AFTERSETUP/trueEND branch/
SHA/tree/status; full streams/immediate actual natives/realUTC/time_ns and finite
monotonic overall/per-command caps/terminal-reap. Fail closed on any command,
identity/hash/log error. Wrapper timeout native is not unknown child native.
No blind retries or substitute old receipts.

Exact31 commands/order below; plain python is the approved3.13.18 venv:

~~~sh
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv build --out-dir /tmp/slaif-agent-site-distributions
python -m slaif_agent_site.control_api --check
python -m slaif_agent_site.editor_api --check
python -m slaif_agent_site.agent_api --check
python -m slaif_agent_site.render_api --check
python -m slaif_agent_site.mcp_adapter --check
python -m slaif_agent_site.media_service --check
python -m slaif_agent_site.review_worker --check
python -m slaif_agent_site.scheduler --check
python -m slaif_agent_site.media_gc --check
python -m slaif_agent_site.bootstrap --check
node --version
pnpm --version
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm licenses list --json
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
~~~

Final SELF MUST have20strict correct-app required contexts PLUS10actualPG
children allsuccess, none missing/pending/failed/cancelled. Inspect current
actual packaging/WHOLE and complete reproducible all-six evidence: both builds,
loaded-copy/SBOM/checksums/labels/licenses/browser provenance; fresh Grype DB
actual build/checksum/age, ignored0, empty license+vulnerability exceptions,
Critical0; CVE-2026-115557 absent across6 with actual patch/removal provenance,
CVE-2026-111497 and all29 oldChrome matches absent at ANYseverity. Compare full
High six-tuples versus Fb13, a42 and historical19: retained/removed/new. Any new
High/vendorCritical risk needs ROOT review, never automatic approval.
Bind CI checkout merge parents/tree/OCIrevision to literalFc/SELF. No all-permissive/
zero-vulnerability claim. Preserve Medium stock-CPE Chrome2015-1239 honestly.
Strict console/privacy oracles remain; recurring redactedmedia len79 error means
STOP categorical safe evidence, no weakening/raw-private log/rerun-until-green.
Apache syntax is not actualHTTP coverage. No localWHOLE/LOCAL6 required here;
both remain mandatory for PR112 and full product on later resumption.

## Forward corrections, acceptance, report and synchronization

Carry all a/b forward errata WITHOUT altering historical files. Further b
precision: P1 andFb each1120remote leaves, SELFb1121; the three-path delta is
Fb-vsP1 only, whole b did change ChromeDockerfile/pins/docs. Rawbackend Grype
fix.versions explicitly includes3.12.16/statefixed. The good==bad helper wrote
UNCHANGED bytes before asserting (not before write). Actual b hostNode came from
the verified xz tool archive, not gzip comparison data. Synthetic publication
UTC .000000 and faulty writer UTC suffixes are not subsecond proof; rawns/ROOT
wire receipt are authoritative. Healthy quiet/checkpoint/compaction is no crash.
Never read /proc/*/fd/* contents or broad-kill; knownPID metadata only.
Do not poll other actor tool handles or infer native0 from parser/computed data.

N1: unique samePR, all-round scoped source/size and architecture preserved.
N2: fixed actual Node/Brotli/Chrome/Python and no worker Python alternate,
honest license/inventory. N3:freshFc ALL31/affected checks. N4:approved actual
backend/worker probes and qualified literalP1 web input-equivalence, full owned
cleanup/absence. N5:finalSELF20+10 success and fresh full6 security/licensing/
packaging qualification. N6:honest docs/history/report/remote publication/wire.
ROOT alone decides acceptance and merge. No partial or greenCI equals acceptance.

Report literalFc/branch/base/PR, actual source/gate/artifact/log/provenance/
UTC/rawns/natives/cleanup evidence and exact pass/fail/skip/notrun/pending,
all unmet criteria/risks/forwarderrata, local setup/licenses/security/docs.
Publish SAME COMPLETE reportTEMP on reports filesystem; exact repository
markdownlint-cli2@0.23.2 under Node24.22.1 --no-globs, actual0/Linting1file/
0issues BEFORE filefsync/hash/inode/atomicrename/parentfsync/posthash.
Canonical/worktree bytes exact. Report-only SELF soleparentliteralFc/sole new
c-report path; barepush actual native, GitHub APIhead==SELF/open correctbranch/
base, remote report bytes/parent/path verified BEFORE exactlyONE responseOK.
FIFOs actual control4470111/response4470112 in strategicworkspace; exactASCII
OK4f4b/2bytes/noLF/close, NEVER fsyncFIFO. No replay after postwrite error:
inspect retained ROOT wire first. Then exactlyONE byte-retaining next-control
reader and actualhandle/PID/retainedEOF/native. No selfmerge/automerge/bypass.

PR112 remains OPEN ON HOLD/INACTIVE, neither accepted nor abandoned. Resume ONLY
ROOT083-8-j history-preserving mainmerge AFTER113accepted/merged/remotemain
verified. All originalP1-P7/I1-I8 and fullfunctional/product/architecture/security/
responsive/operations/recovery/release evidence remain mandatory. No numeric083
completion/084 advance, MVP/release qualification or scope shrink.

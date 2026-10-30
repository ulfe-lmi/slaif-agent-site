# OAP 083-9-a: remediate the Node and Brotli runtime security prerequisite

## Identity, sequencing and verified state

- Numeric objective: 083, unresolved. Semantic increment: 083/9, bounded runtime
  security prerequisite. Mode: CREATE_NEW_PR. PR: NEW, exactly one.
- Required fresh branch: `oap/083-9-a-remediate-node-brotli-runtime`; base main
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (D18), independently recheck before
  branching; stop and reconcile unexpected main movement with ROOT.
- Previous increment 083/8 PR112 stays OPEN ON HOLD / INACTIVE, neither accepted
  nor abandoned. Its round i closed PARTIAL: untested preservation Wi
  `5bf6c3dfc0ef3ab277eaf279c8d2db3a7888eb64`, report-only Si
  `a3259f6dc2a629c314adf91cb8ba562282fcee05`, sole parent Wi, exact remote
  report 15447 bytes / SHA256
  `e00241c4d0dd27a86f885d66944def3039a79ba863742527c1a07394d9bc5a32`.
  ROOT independently verified complete remote leaf maps and report bytes.
- i's exact response OK/EOF was received 2026-10-30T01:52:57.758154Z. Its first
  writer delivered successfully before unsupported FIFO fsync raised EINVAL;
  the subsequent blocked duplicate writer was erroneous. Its termination and
  reaping must be verified before ROOT starts this round's response reader.
  Do not replay any old wire signal or alter historical reports.
- Starting Sh CI had 28 successes and two failures: Supply-chain evidence
  and Compose and edge packaging, run40981094419, jobs123821259915/123821259675.
  Fresh Si CI is independent; three Python quality jobs failed and other jobs
  remain pending at preparation. Those unmerged WIP failures are deferred to
  the next PR112 order, not silently imported or fixed in this new PR.
- Only ONE active execution increment. After this security PR is accepted,
  merged and remote main verified, ROOT alone resumes PR112 by 083-8-j with a
  history-preserving main merge and all original requirements intact. No 084
  advancement, broader 083 completion, release or qualification claim here.

## Purpose and evidence

Replace actual affected runtime bytes and prove the built images use fixed
copies. No suppression, exception, severity downgrade, wrapper version spoof,
scanner disablement or policy relaxation.

ROOT independently inspected failed artifact12945032923 (ZIP11213308 bytes,
SHA256 `fcd9e822cbe67b67a54c837d6fe66d9f759e45f63fae586bc429118e76235139`):
web has unexcepted Critical CVE-2026-111497, generic Node24.14.1 at
`/usr/local/bin/node`; browser-worker has NodeSource nodejs24.18.1-1nodesource1
and the same CVE at Medium on Ubuntu libbrotli1 1.1.0-2build2. Other five scans'
zero Critical counts do not prove their embedded Node/Brotli unaffected.
All six ignored-match counts were zero. This failure bundle is not a qualified
release bundle. Apache already carries fixed libbrotli1 1.1.0-2ubuntu0.1;
nginx/PostgreSQL brotli-libs1.2.1-r0 were fixed; backend had no Brotli inventory hit.

Primary vendor references:

- <https://nodejs.org/en/blog/vulnerability/october-2026-security-releases>
- <https://nodejs.org/en/blog/release/v24.22.1/>
- <https://ubuntu.com/security/CVE-2026-111497>
- <https://github.com/advisories/GHSA-9v8h-qqgm-4m35>

Node24.22.1 is the fixed 24.x release (October21); scanner firstObserved October29
is not disclosure date. The release cherry-picks the fix; an older embedded
Brotli version string alone does not prove it vulnerable. Ubuntu's own nodejs
package uses system Brotli; do not apply its unaffected status to NodeSource's
third-party binary. Independently verify actual linkage/embedded copies and
fixed binary provenance, no exploit or proof-of-concept execution.

ROOT verified public registry metadata, not pulled/executed image bytes:
`node:24.22.1-alpine3.23` index digest
`sha256:0468540aa58203ff9e40c2aab3907c52644ab818af6176b1c70a026137dc92a2`,
linux/amd64 manifest digest
`sha256:47019ffab12a48f49795a8279603f87e91a64de017fb9aa874e64f489b686079`.
Official glibc x64 archive
`https://nodejs.org/dist/v24.22.1/node-v24.22.1-linux-x64.tar.xz` SHA256
`6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6`.
Executor independently verifies source digests, downloaded bytes, supported
platform and licenses before use; do not guess unverified platform digests.

## Workspace, authority, bounded scope and budgets

Read coding AGENTS.md and OAP-COMMUNICATION-coding-agent.md; strategic owns this
order/active, acceptance, sequencing and merge. No agent profile/effort change.
Use the same healthy visible primary CLI. Only actual crash permits restart,
only `codex --yolo --profile early-beta`. Secondary is read-only reviewer;
primary alone implementation, tests, Git, report and FIFO.

Use a separate clean worktree
`/home/janezp/codex-work/slaif-agent-site-083-9-a` from verified D18. Preserve
original PR112 checkout, all history, untracked `.codex/`, `CODEX-SESSIONS.md`,
`codex.sh`, and the exact 264-line WIP. No reset, force, rebase, amend, clean,
foreign deletion or branch replacement. Canonical OAP root remains
`/home/janezp/codex-work/slaif-agent-site/oap`; this activated order and active
must be copied byte-exact into the new worktree for transcript publication.
Do not change historical transcript or import unmerged PR112 source, expanded
qualification tests/CI, driver upgrade, locks, capture helpers or run.sh.
D18 run.sh is frozen: 435 lines, file SHA256
`fe1144457ab2e0d960030f1b50daad1ebc2bc421138acb67df5bafd313489d04`.

Allowed existing source/documentation paths, only where necessary:

1. `apps/web/Dockerfile`
2. `services/browser-worker/Dockerfile`
3. `supply-chain/policy.json`
4. `tools/supply_chain/policy.py`
5. `tools/compose/smoke.sh` (only affected Node version/provenance assertions)
6. `tests/packaging/test_oci_contract.py`
7. `tests/supply_chain/test_policy.py`
8. `docs/DEPLOYMENT.md`
9. `docs/SUPPLY_CHAIN.md`
10. `docs/TESTING.md`
11. `THIRD_PARTY_NOTICES.md` (only actual inventory/license changes if necessary)
12. `sbom.json` (only if its established generation requires this update)
13. `oap/INCREMENTS.md` (truthful sequencing only)
14. `oap/MVP-PROGRESS.md` (truthful status only)

Plus exact activated order, active and final report: maximum17 changed paths.
Source budget versus D18: planning400 gross added+removed natural lines,
reserve200, HARD600 across the fourteen paths. Normal incremental editing is
permitted; measure after each logical edit; at400 report complete remaining
forecast. If actual draft exceeds600, STOP before further edits, tests, staging
or push and return measured scope/forecast. No packing, generated mirrors,
new helper source paths, minification or proof deletion to force fit.

Non-goals: product features, publication/COW/audit changes, foundation or driver
upgrade, migrations, app package/lock changes, Python dependency changes,
Playwright/CfT/browser/distro/Alpine-family upgrades, CI workflow/selector edits,
scanner/tool/license-policy changes, trusted surface/network/mount widening,
full product qualification or local six-image evidence-pipeline modification.
Keep CfT156.0.8078.47/revision1706539/archive hash, Playwright1.62.1/Noble base
pin, six targets, sandbox, egress, user10001, browser-only runtime and removed
npm/npx/corepack/pnpm tools intact. No production/deployment or credential work.

Keep foundation PyPI agent-cow-postgresql==0.2.0 with exact frozen uv.lock
registry hashes; no VCS/path/fallback. Server-owned site/workspace/operation
context, agent isolation, separate reviewer-only atomic human promotion, private
artifacts, immutable media and one normalized trusted renderer remain intact.
Browser success never grants publication; no DB/reviewer/host/Docker credential
or mount enters browser runtime, no default telemetry or required hosted service.
Never log secrets, private content, credentials or unrestricted diagnostics.

## Required implementation and source checkpoint

Update both web stages to verified fixed Node24.22.1 Alpine3.23 digest.
Fix both browser-worker builder/runtime Node24.18.1 copies while retaining its
Playwright/Noble base. Prefer a verifiable fixed publisher package if available;
otherwise an exact hash-pinned official Node24.22.1 archive is authorized with
actual obsolete NodeSource binary/package removal and honest SBOM inventory.
No lying dpkg metadata, unpatched alternate executable, or version-print wrapper.
Ensure system libbrotli1 is fixed at Noble1.1.0-2ubuntu0.1 using the established
bounded Ubuntu artifact-overlay method where necessary. Inventory every actual
loaded/embedded decoder copy. No broad apt upgrade or unsupported symlink swap.

Update coupled supply policy literals/required keys and smoke assertions to
match actual sources; preserve fail-closed policy and meaningful tests.
Minimal test adaptation must preserve vulnerable-copy refusal and removed-tools
contracts; do not weaken assertion presence or suppress scan results. Inventory
permissive Node/bundled terms and actual OS/browser licenses truthfully.
Document exact versions/provenance and the limited security contract.

Run necessary safe affected checks once. Then commit/push literal implementation
head I9 with exact activated order/active, open exactly ONE new PR from main,
and send ROOT complete actual diff/gross counts/source identities plus finite
verification plan. STOP there for ROOT full-source and runtime-input review
BEFORE ALL31, builds, Docker, WHOLE or supply pipeline. Do not publish a success
report or final response at this checkpoint; primary waits coordination in the
same healthy CLI. ROOT alone authorizes execution after full review.

## Verification after ROOT source and finite-plan approval

Use uv0.12.5, Python3.13.14, Node24.22.1 and pnpm11.22 with frozen application
locks. Routine local setup belongs to coding agent, never human/ROOT. Full logs,
immediate native status, real UTC/raw time_ns, source START/END identity and
clean source after environment setup are required. Do not fabricate no-import
or no-environment-change claims: ordered imports/installations do happen.

Fresh ALL31 in this exact order and argv, rooted in the clean I9 worktree:

```sh
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
```

Use the approved venv for plain python. Also run actual broader CI Ruff scope
and affected supply-chain/packaging tests not included by ALL31; no invented
sum of overlapping tests. Main's foundation/CI counts differ from unmerged112;
report actual counts, not its old730 figure or qualification-specific tests.

ONE active local runtime scratch input is permitted:
`/tmp/oap-083-9-a/verify-node.sh`, planning220 natural lines, HARD350 ALL active
code including inline Python/Node, regardless suffix. Complete in memory and
count BEFORE writing; no builder/mirror/extra runtime helper. ROOT reads full
actual bytes before execution. Other log/receipt data are not active code.
The ALL31 command runner must likewise be fully shown/count-budgeted in the
finite plan before ROOT authorizes writing/execution; planning120/HARD160
natural lines for that command runner, separate from the350 runtime budget.
No unreviewed helpers. A change to an approved input requires another source
review; no unbounded retries or weakened gates.

Local runtime verifies only the two changed images, not full product behavior.
Build two uniquely owned web/browser-worker image references at literal I9.
Before mutation ensure references absent with healthy queries, explicit
ownership; never sweep shared tags/IDs or delete foreign references. Retain
actual successfully created container ID and safe immutable image/user/mount
metadata DURABLY before start; bounded benign Node/Brotli round-trip and actual
executable path/version/hash/provenance checks at user10001; prove runtime tools
absent and fixed system/embedded copies, not merely a displayed version. No
exploit, external HTTP or secret/Env/Args/Cmd/full-inspect logging. Preserve
browser pin/sandbox and inventory its actual executable too.

Finite phase plan: each image build maximum1800s, each probe120s, phase maximum
5400s excluding setup/cleanup up to600s each, kill grace5s. Every child and
Docker operation has finite deadline bounded by phase remaining time; actual
terminal/reap precedes disposal. Do not confuse timeout wrapper PID with image
or owned container identity. Retain complete streams, immediate natives,
pre-disposal metadata, each cleanup native and healthy exact raw absence after
cleanup for all owned containers/anonymous volumes/networks/image references.
Failure or residual/unknown ownership: STOP, no blind retry, prune or foreign
cleanup. Record true final source identity after cleanup, not only before it.

Current final SELF must have all20 required strict checks (correct app IDs)
and all10 actual PG children successful, no missing/pending/failure. Inspect
current CI's actual WHOLE/packaging and reproducible all-six-image artifacts,
both builds, checksums/SBOMs/licenses/browser provenance/Grype DB build time+
age, Critical0, ignored0 and empty exception sets. Require no remaining
CVE-2026-111497 match across all six images, plus fixed-copy provenance above;
scanner absence alone is insufficient. Compare full inherited High tuples
across all six subjects, recording retained/removed/new matches; do not force
old19 if the fix removes one. New High findings need ROOT review, not automatic
acceptance or suppression. Bind actual CI checkout parents/tree to I9/SELF.

Media-publication final console failure on Sh was an unknown redacted len79
HTTPS browser-error tuple. Keep strict console assertions/privacy redaction;
fresh mandatory CI at changed security source is required. A later pass does
not establish Node caused/fixed it. If it recurs, STOP with privacy-safe
categorical evidence for ROOT; do not expose raw private content, weaken the
oracle or rerun until green.

No local WHOLE/LOCAL6 is required or claimed for this bounded two-image security
increment: fresh ALL31, meaningful affected checks, two owned actual runtime
probes and mandatory CI WHOLE/all-six evidence are its evidence contract.
All original PR112 fresh local WHOLE/LOCAL6, I1-I8/P1-P7, source budgets and full
product requirements remain mandatory on resumption; no substitute/carry claim.

## Acceptance, report and synchronization

N1: unique fresh correct PR/base, complete scoped source/size review, exact
source/lock/CI preservation. N2: actual fixed Node/Brotli copies/provenance,
honest inventory/removal/licensing. N3: fresh ALL31/affected checks with exact
results and source binding. N4: approved two-image probes, ownership, bounded
execution and verified actual cleanup/absence. N5: current required20+10 green,
actual packaging and six-image evidence reviewed, full High comparison and
no vulnerability exception. N6: truthful docs/report/remote publication and
exact synchronization. Green CI alone never acceptance; ROOT alone merges.

Report full branch/base/PR URL, literal implementation I9, all source/gate/log/
artifact identities/counts/UTC/native/cleanup proofs, actual pass/fail/skip/
not-run/pending, setup/license/dependency details, unresolved risks and prior
forward errata. Distinguish metadata-only registry observation from actual
built/loaded binary proof. Preserve original full-product/D5-approved sequencing
and unaccepted PR112 status. No complete083/MVP/release claim.

Publish complete report TEMP on same filesystem; lint THAT SAME COMPLETE TEMP
using exact repository markdownlint-cli2@0.23.2 --no-globs, require native0/
1file0issues. Explicit file fsync, hash/inode/size+actual UTC/time_ns, atomic
rename, parent fsync and post-hash comparison. Commit/push report-only SELF
with sole parent literal I9 and sole new report path. Before ONE response OK,
explicitly compare actual PR API head==SELF (recheck stale data), exact remote
report bytes, sole parent/path and open correct PR/base. No historical edits.

Use actual verified control.fifo4470111/response.fifo4470112 in strategic
workspace. Wire is exactly ASCII OK4f4b, no LF, close writer. NEVER fsync a FIFO;
file fsync applies to regular publication files. On a post-write error inspect
retained ROOT response evidence before any further attempt; never replay.
After response create exactly ONE byte-retaining next-control reader, retain
EOF/native and report actual handle/PID/paths. No nohup/replay experiments.
No merge, auto-merge, approval bypass, protected resource or production action.

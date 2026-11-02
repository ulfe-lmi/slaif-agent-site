# OAP 083-9-b: complete the bounded Node, Brotli and Chrome security prerequisite

## Identity and activation reconciliation

- Objective083, unresolved; increment083/9, SAME bounded runtime-security PR.
- Mode: AMEND_EXISTING_PR. PR113:
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>.
- Branch: `oap/083-9-a-remediate-node-brotli-runtime`; base mainD18
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`.
- Round a formally PARTIAL, not accepted/merged. ROOT fully read its464-line/
  25470B report, SHA256
  `0a3b93dccd6e92a3a75ca079064112188dea31b60f2b2dd19d3b23f755b076dc`.
  Actual exact responseOK4f4b/2bytes/EOF2026-10-30T05:03:55.460335Z;
  root51936 tool session ended, actual oldPID875352 gone/lock released.
  Complete1119vs1118remote leafmaps: only that report, soleparentI9;
  all other mode/type/blob equal, remote/canonical/worktree reportbytes exact.
- ROOT verified orphangrep987930 terminal/absent after exact-identity SIGTERM
  2026-10-30T05:16:39.404432Z; it had primaryPTY/dev/pts/2 open. Only this proven
  owned process was terminated; both CLIs and next-control reader stayed alive.
  Actor reaped own session1622 native143; orphan actual exit native UNKNOWN.
  Current primary control reader989105/wrapper989103 is waiting for partner.
- Live main/PR identity rechecked immediately before preparing this complete
  order TEMP; no duplicate round-b order/report. This draft becomes active only
  after ROOT lint, atomic publication/active update and exact controlOK.
- Round-a implementation: `db37a4659277c3a405e375e05acc12c446a2a452`,
  tree `59e56fdf3b622c9951fbef96082a9ccefe11bd83`.
  Report publication head: `fb3ef1fb191910143fe192c8472df342017c4825`.
- PR112 remains OPEN ON HOLD / INACTIVE, not accepted/abandoned/closed.
  Resume only by ROOT083-8-j after security acceptance/merge/remote-main proof.
  No084 advancement, complete083/MVP/release claim, or product-scope shrink.

## Reason, evidence and prospective scope correction

Round a preserved a browser-version freeze and therefore cannot silently fix
newly verified Chrome security findings. This next immutable round prospectively
allows only the same-major Chrome maintenance patch described below; the Node,
Brotli, image confinement and all remaining acceptance requirements continue.
No activated order or published report may be rewritten.

Current implementation CI run41002277149 is fully green, all30 jobs including
ten actual PG children. That is insufficient for acceptance. ROOT downloaded
artifact12954930004, ZIP8415478B/SHA256
`19fe161cf51503c305f2fc3dd19fb4398be3365f796976a5c51dbea89df1b20d`,
matching GitHub's digest, and verified all53 payload checksums excluding SUMS.
All six Grype scans have Critical0, ignored0, no CVE-2026-111497, but42 High:
13 retained, six removed,29 new Chrome156.0.8078.47 six-tuples versus the qualified
historical19. Full tuples and provenance are in ROOT's review index, not an
acceptance claim. DB actual built2026-10-29T06:23:34Z, checksum
`a5ad3344d964e4d1472fa615b0e70f87c27cd21470fede2a8fbf6e4c6c32c907`,
age22.151h at validation; the filename timestamp is not its build time.

Google's October27 Linux stable release156.0.8078.73 includes52 security fixes.
CVE-2026-118331/118344/118348 are vendor Critical and scanner High in this
artifact. Preserve both classifications; scanner Critical0 does not mean the
vendor reported no Critical issues. Do not suppress, downgrade or except them.
Official current CfT Stable metadata gives156.0.8078.80, revision1706539,
document timestamp2026-10-29T22:14:17.810Z. Same revision does not mean unchanged
browser bytes. No exploit or untrusted input execution is authorized.

References:

- <https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html>
- <https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json>
- <https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json>
- ROOT facts: `/tmp/oap-083-9-a/root-official-browser-security-review-and-next-round.json`.
- Exact old29 tuples: `/tmp/oap-083-9-a/root-current-security-artifact-initial-scan-review.json`.

## Fixed source and preserved boundaries

Target exactly official CfT156.0.8078.80/revision1706539/linux64:
<https://storage.googleapis.com/chrome-for-testing-public/156.0.8078.80/linux64/chrome-linux64.zip>.
Archive SHA256: `b711c720f774be355197f32edf37e0651418ba036d92446ee2da19ac017540a7`.
Archive size and independently measured executable hash:
201329937B; Chrome entry302710088B/SHA256
`1bcad71ad1bff85955db13c6d8dd9f32374934d5a5cb079b526c46fb51f9bd97`.
ROOT independently measured whole-archive hash; peer measured the component
from that identical archive. Executor independently verifies both. Old/new
archive names and selected Widevine notices/CDM bytes match; that does not
prove every embedded third-party obligation unchanged. Full browser/OS license
inventory remains required, no blanket all-permissive claim.
These source observations are verified metadata/data, not an executed runtime
qualification; repeat actual downloaded-byte checks before use.
Executor independently verifies metadata/downloaded bytes before pinning them;
stop on mismatch or unexpected stable movement, never guess a hash or platform.

Retain Node24.22.1 in web's pinned Alpine3.23 source and in both worker stages.
Retain official glibc x64 gzip URL and SHA
`eb6728e77c576a35162c122c45ccadf224d89ff00abc8dae46cc2897c6002d7c`,
Node binary126879696B/SHA
`e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb`
and LICENSE157609B/SHA
`5888dbb9a1d2b18f2c3e6c5f6af1b39de658372b402a0577b002777f14c62ace`.
Keep libbrotli1 exactly1.1.0-2ubuntu0.1, obsolete NodeSource package/binary removal,
all npm/npx/corepack/pnpm/pnpx cleanup, entire inherited browser-tree removal
before the verified CfT COPY, and the fail-closed public image guard.

Keep Playwright1.62.1/Noble base digest, Alpine family, six stable targets,
user10001, sandbox/seccomp/egress/read-only root/capabilities/resource limits,
privacy and removed-browser/tool contracts. No Playwright/framework/distro,
app/lock/Python/foundation/driver/CI/scanner/license-policy upgrade or relaxation.
No run.sh edit or unmerged PR112 capture, qualification, driver0.32 or lock copy.
Main run.sh435L/SHA
`fe1144457ab2e0d960030f1b50daad1ebc2bc421138acb67df5bafd313489d04` stays frozen.

Foundation is PyPI agent-cow-postgresql==0.2.0 with existing exact registry hashes;
no VCS/path/fallback/private SDK or SQL. Server-owned site/workspace/operation
context, isolated agent authority, separate human reviewer-only atomic promotion,
private browser artifacts, immutable media and one trusted renderer remain.
No app/publication/COW/audit/migration/feature changes, trust/network/mount widening,
production/deployment/credential access or secret/unrestricted diagnostics.
Browser observations never authorize publication. No new hosted/account-bound
service or non-permissive dependency may silently enter.

## Workspace, ownership, scope and size

Use the SAME healthy visible primary CLI, same existing branch/PR/worktree:
`/home/janezp/codex-work/slaif-agent-site-083-9-a`.
Read coding AGENTS.md and OAP-COMMUNICATION-coding-agent.md. Primary alone edits,
installs approved local tools, executes, commits/pushes, reports and writes the
response FIFO. Secondary is read-only independent reviewer. Only actual crash
permits restart, ONLY `codex --yolo --profile early-beta`; preserve xhigh.
No hidden agent, new branch/PR, force/reset/amend/rebase/clean, foreign deletion,
or damage to canonical PR112 checkout, human files or historical transcript.
Canonical OAP root remains `/home/janezp/codex-work/slaif-agent-site/oap`.
Commit exact strategic order/active bytes without editing them.

Allowed existing source paths are the fourteen in a, plus these five narrowly
coupled Chrome maintenance truth paths:
`README.md`, `docs/CONFIGURATION.md`, `docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
`supply-chain/browser-worker-critical-matrix.json`.
Do not edit a previously optional source path unless actually necessary.
No new helper source path or unrelated formatting/refactor is authorized.

Cumulative source budget against D18 remains planning400 plus reserve200,
HARD600 gross natural added+removed lines, INCLUDING OAP status docs.
Exclude only activated order/report files and active from this source budget.
At400 return measured complete remaining forecast; above600 STOP before more
edits/tests/staging/push. No packing/minification/mirrors/proof deletion to fit.
Maximum24 cumulative changed paths: nineteen allowed source and five exact
transcript paths (a order/report, b order/report, active). Expected actual21,
with sixteen source paths; this explicitly triggers the20-path review threshold.
ROOT authorizes review of this coherent two-image security increment with
separate production/test/inventory/docs/transcript counts, not feature growth.
No retrospective waiver of a's limits or historical records.

## Source checkpoint and truthful qualification history

Update only active source pin/URL/hash/version, exact coupled policy/guard/test
literals and honest current docs/status. Preserve strict guards, Chrome count==1,
Node/version/tool absence, policies and all historical evidence.
Do not globally replace old versions in qualification history or reports.
The old candidate9 remains immutable historical qualification of156.0.8078.47.

Phase1: make bounded runtime/policy/current-doc changes and necessary existing
affected tests. Keep historical matrix assertions/evidence truthful; historical
qualification is not current release acceptance. Commit/push literal P1 and
return full actual diff/per-path hashes/gross plus finite verification plan.
STOP before local ALL31/Docker/build/probe/input writes for ROOT full-source and
complete-input review. CI triggered automatically by a push is not a local gate.
No formal success report/SELF/OK at this source checkpoint.

Phase2 after approval: perform the two owned image probes and inspect P1's actual
mandatory CI/six-image evidence. Then append candidate10 qualification containing
only real observed source/binary/image/scan/DB/checksum/license facts, exact
subject SHA and an explicit intermediate-qualification label. Preserve every
previous history entry/claim. Adapt existing historical assertions to retain
candidate9 and meaningfully guard candidate10; no oracle or coverage reduction.
Do not invent final-image hashes in a commit that changes its own revision label.

Publish final implementation F after all needed docs/history/test data, with
necessary affected checks. ROOT independently compares complete remote maps and
all actual Docker COPY/ADD/build inputs between P1 and F. Only when these image
inputs and fixed binary/archive hashes are identical may the P1 local observations
be carried with their literal P1 subject, never claimed as an F local run. Revision
labels/image IDs may differ and must be reported. Any image-input/code change
requires new source/input review and fresh affected runtime proof. This is an
explicit prospective evidence-equivalence rule, not fictional gate execution.
Fresh ALL31 is performed at clean final F. Mandatory final SELF CI and actual
all-six evidence must be current, not carried from P1. All original PR112 local
WHOLE/LOCAL6 and full-product obligations remain intact on later resumption.

## Approved toolchain and fresh ALL31

Use uv0.12.5, Python3.13.14, Node24.22.1, pnpm11.22 with frozen application locks.
Routine local setup belongs to executor, never human/ROOT. Preserve full streams,
immediate actual natives, real UTC/raw time.time_ns, start/after-setup/true-end
source identities and clean tracked source. Distinguish timeout-wrapper status
from child status when unknown; no tee/tail status masquerading as a child.

Exact31 commands in this order; use the approved venv for plain python:

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

Existing affected source checks already run in a are qualified only to their
actual subjects. Run necessary affected checks for newly changed b files,
including actual broader CI Ruff scope and relevant packaging/supply suites;
no repeated unchanged gate merely for cleaner clocks/prose. Report overlap,
pass/fail/skip/not-run/pending honestly; never invent a grand total.

ONE ALL31 runner `/tmp/oap-083-9-b/all31.sh`, planning120/HARD160 natural lines,
ALL inline active code counted. Build complete INMEMORY/count BEFORE any write,
show full actual contents and obtain ROOT review BEFORE execution. Small in-memory
construction units are permitted; no builder, mirror, helper or unreviewed wrapper.
Bind exact literal worktree/head/branch and initial/final source content/status;
fail closed on identity/hash/git/log errors and fail immediately on command failure.
Use monotonic remaining-time deadlines and bounded preflight/setup/tool commands;
state finite actual overall/per-command caps, full stream/native receipts and
terminal/reap behavior. A revision needs renewed complete review. No blind retries.

## Two-image runtime and current CI evidence

ONE runtime scratch `/tmp/oap-083-9-b/verify-node.sh`, planning220/HARD350 natural
lines INCLUDING all inline code regardless suffix/mode. Complete INMEMORY/count
BEFORE write, full ROOT review BEFORE execution; no extra active helper/mirror.

Build only two uniquely owned web/browser-worker image references at P1.
Before any mutation, healthy queries must prove the exact refs/container names
absent. Never sweep, retag or delete foreign/shared resources. Persist successful
created-container IDs durably BEFORE start, safe immutable image/user/mount
metadata BEFORE disposal. No Env/Args/Cmd/DSN/credentials/full inspect/raw-private
content in logs. Retain complete streams/natives/UTC/source proof.

At user10001 verify actual executable path/hash/version and benign Node/Brotli
round-trip, fixed system/embedded decoder provenance, obsolete NodeSource and
runtime-tool absence (including both Corepack locations), actual Node LICENSE
hash/bundled terms. A version string alone is insufficient; Node's vendor backport
may retain an older embedded Brotli version string. Verify actual new Chrome
executable/hash/version and single-browser tree, all browser pin/confinement
contracts and no vulnerable alternate copy; no exploit/external HTTP.

Each build1800s maximum, probe120s, phase5400s excluding setup/cleanup600s each,
kill grace5s. Every child/Docker operation finite and capped by phase remaining;
actual owned terminal/reap before disposal. Capture each removal native, all
owned container/anonymous-volume/network/image-ref metadata and healthy exact
raw post-cleanup absence. No failed query equals absence, PID/time window equals
ownership, pre-delete/rm0 equals post-absence, or timeout PID equals container ID.
Failure/residual/unknown ownership: STOP, no blind retry/prune/foreign cleanup.
Record true final source identity AFTER cleanup. State actual normal/error-path
coverage rather than claiming every counterfactual was exercised.

Final SELF must have all20 strict required contexts with correct app IDs and
ten actual PG children successful, none missing/pending/failed/cancelled.
Inspect actual current packaging/WHOLE and reproducible six-image artifacts:
all two builds/checksums/SBOM/loaded-copy and browser provenance/licenses,
DB actual build/checksum/age, ignored0/empty license+vulnerability exception sets,
Critical0 and no remaining CVE-2026-111497 or any of a's29 new Chrome matches
at ANY severity. Vendor-known Critical fixes must be addressed, not dismissed
because a database labels them High. Compare full High six-tuples across all
six against both actual a42 and qualified historical19: retained/removed/new,
no forced count and no automatic approval of new High. ROOT reviews new risk.
Bind actual checkout merge parents/tree/OCI revisions to literal source/SELF.

Keep strict console assertions and privacy redaction. If the earlier unknown
redacted media-publication len79 tuple recurs, STOP with safe categorical facts;
no raw-private text, weakened oracle or rerun-until-green. A later pass does not
prove Node caused/fixed the old failure. Apache config validation is not actual
Apache HTTP product coverage. This bounded PR does not close full product083.
No local WHOLE/LOCAL6 is required/claimed here; original PR112 requirements persist.

## Forward precision and protocol containment

Carry these corrections in b's truthful report; never edit immutable a:

- a's section5 broad all-four-bare-push claim is qualified by its own erratum:
  596147a used push|tail, tail0 only; c445 and db37 actual barepush0 were observed.
- c445 affected log10 contains five checks, no compileall; a's compileall0 at
  that boundary is unsupported. Earlier original-I9 compileall was observed.
- a's initial uv sync tail-only evidence was never recaptured as actual uv
  sync by logs09/10/12/13; ALL31 NOTRUN. Fresh b sync fullstreams/native required.
- Check-time hostNode24.22.1 came from the verified xz tool archive. Gzip member
  comparison files were data, not a replacement host toolchain. Same binary hash
  does not justify claiming a different actual extraction route.
- a's NOT_YET_VERIFIED Chrome80 SHA was its initial facts snapshot. ROOT/peer
  actually measured the full archive before b; values and scope are above.
- No LOCAL Docker/probes in a; CI did build images. Smoke tests current paths/
  versions/count, while source/OCI assertions establish the build cleanup recipe.
- a's prospective step7 reused obsolete control reader68477, consumed on a's
  activation. Actual next reader is primary989105/wrapper989103 in9a scratch.
  Do not replay the a signal or overwrite its old retained bytes.
- A primary process-audit command read /proc/*/fd/* contents, which can consume
  live pipes/FIFOs, then used an unsafe broad process-pattern kill. Orphangrep
  987930 was identified by exact command/start identity; activation requires its
  verified containment, now observed above. These actions were not retroactively
  approved; calling this harmless or no-product-impact would be unproved. Past pipe
  consumption cannot be universally ruled out; no broad no-secrets/no-side-effects
  forensic claim. All new evidence must be fresh and source-bound.
- Never read descriptor target contents or broad-kill patterns. Only metadata
  readlink/stat for known processes; terminate only proven owned exact children,
  capture actual wait/terminal facts. Do not poll another actor's tool handles.
- A computed Python payload-validation .native field is not an observed waitpid
  native. ROOT51936 completion omitted exit_code; exact wire/EOF, OS exit and
  lock release were separately verified. Do not invent native0 or retry for
  cosmetics. Preserve actual signal receipts and never fsync FIFO.

## Acceptance, report and exact synchronization

N1: unique same correct PR, a+b requirements/scoped cumulative remote source,
explicit size review and unchanged architecture/locks/CI/foundation/driver.
N2: actual fixed Node/Brotli/Chrome bytes/provenance, honest inventory/licenses,
no old vulnerable alternative or runtime tool residue.
N3: fresh ALL31 at final F plus meaningful affected checks, exact evidence/subjects.
N4: approved two-image local proofs, honest P1-to-F input equivalence where used,
finite ownership/actual cleanup/post-absence and true final source.
N5: current final20+10 success, actual packaging/WHOLE/all-six evidence, full
High/vendor-Critical review, no scanner/license/vulnerability policy exception.
N6: truthful docs/qualification history/report, exact remote publication and wire.
Green CI alone never acceptance; ROOT alone decides and merges.

Report branch/base/PR, literal final implementation F, all actual code/gate/log/
artifact hashes/counts/times/natives/source/cleanup evidence and unmet obligations.
Retain a's failures/forward errata without rewriting history; separate metadata,
static inference, actual binary/probe facts, P1 observations, final F and current
SELF evidence. No blanket all-permissive/no-secrets-in-every-artifact claim.
A partial/blocked round is not acceptance and must say which N criteria remain.

Publish complete report TEMP on same filesystem, exact repository Markdownlint
CLI2.23.2 --no-globs on THAT SAME COMPLETE TEMP, require native0/1file/0issues;
file fsync/hash/inode/size+actual UTC/rawns, atomic rename, parent fsync, posthash.
Canonical OAP report and PR worktree copy must be byte-exact, no historical edits.
Commit/push report-only SELF with sole parent literal F and sole new report path.
Before ONE responseOK compare actual PR API head==SELF, exact remote report bytes,
sole parent/path and correct open branch/base, recheck stale remote data.

FIFOs are actual control4470111/response4470112 in strategic workspace.
Wire EXACT ASCII OK4f4b, no LF, close; NEVER fsync FIFO. 51936 is an old ROOT tool
session handle, not a LinuxPID or a new reader to create. ROOT supplies the new
sole response reader after this order's control handshake; verify actual receipt.
No replay/duplicate writer: on postwrite error inspect retained ROOT wire proof
before any further attempt. After response create exactly ONE byte-retaining
next-control reader, record actual handle/PID/EOF/native; no nohup experiments.
No self-merge, auto-merge, bypass, production or protected-resource mutation.

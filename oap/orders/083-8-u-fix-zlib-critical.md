# OAP 083-8-u: remove the measured zlib Critical from four images

## Identity, authority and verified state

Objective083 remains unresolved; same semantic qualification increment083/8.
AMEND_EXISTING_PR, PR112 <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>.
Head `oap/083-8-a-qualify-public-whole-session`; base `main`
`40cd172109a22ef5f342589b59a4293f35379651`. ROOT refreshed GitHub19:26Z:
OPEN, current report-only St `a8a59b932bb1995af4a5a813fee7937d78d69c22`,
sole parent It `93bf5485e78e91d259ef804eb680b9f886592783`.
T formally CLOSED PARTIAL: ROOT e8c954/native0 at19:24:02.976824Z verified
full1173->1174 leaf maps, sole report74L6781B SHA256
`e1d3645f8e9f2e631fce66cd332bcbde34a6cf6b32f01fce7ceb2651d4c79183`,
remote decoded bytes equal worktree/canonical, clean tree, exact active/report.
ROOT72483 terminal89d3e6/native0 exact2OK+EOF19:16:01.097600Z. It all30 terminal:
29SUCCESS, Supply-chain evidence FAILURE; Compose succeeded. St newer checks
were pending in the dated review. Neither round nor increment is accepted.

ROOT owns architecture/scope/sequencing/acceptance/merge; human owns domain
truth/risk/release. Primary visible pane21 owns all implementation/Git/report/
FIFO writes; peer17 may receive finite ROOT-assigned READONLY review. Keep both
healthy CLIs; actual crash startup ONLY `codex --yolo --profile early-beta`.
No healthy reset/reprofile/restart/hidden executor. Read coding AGENTS/protocol/
applicable nested instructions and compact architecture; NEVER full ARCHITECTURE
without direct human instruction. Execution ONLY
`/home/janezp/codex-work/slaif-agent-site-083-8-j`; canonical OAP
`/home/janezp/codex-work/slaif-agent-site/oap`. Preserve original dirty human
checkout and every immutable order/report/incident artifact. No branch/newPR/
reset/stash/rebase/squash/force push/merge/foreign cleanup. This order activates
only by complete atomic order/active publication and ONE exact control OK.

## Measured failure and official fix evidence

It Supply job130052016651/run42879554323 failed the vulnerability gate:
backend unexcepted Critical CVE-2026-4738. Full RAM log295425B/3353L SHA256
`57c2d52011025780b7e38dd2649ba4261279aba4e13d44b4dc2e760ed9d9af73`,
native0, no APT-unavailable/image-build failure markers. ROOT failure artifact
13794541476: ZIP10406960B SHA256
`61d56ea14782890102d3358343c7a90b5ddbc324d1e18497d05968000c221d8e`,
38files/37declared checksums verified, status UNQUALIFIED, all six raw scans
ignored0. Source synthetic merge13537647d2f9bff52467f613830ab12f058a3914 has
parents[main40cd,It], canonical tree db69a0d685d9bcaa2b6e3f93d6edd0877e8705f5
and full1173-leaf map identical to It; source attribution independently proved.

CVE target matches apk zlib in FOUR images: backend1.3.2-r1/Alpine3.23.7,
web1.3.2-r1/3.23.7, nginx1.3.2-r1/3.24.3, postgres1.3.2-r0/3.23.5.
All Critical, fix_state fixed, fix_versions1.4-r0. Other two images have no
such target matches. This is scan evidence, not full qualification.
ROOT receipts in `/tmp/oap-083-8-t-control/`:
root-It-CVE4738-retained-scan-review.json;
root-zlib14-official-Alpine-proof.json; root-St-independent-closure-review.json.

Official v3.23 ANDv3.24 main/x86_64 APKINDEX and secdb read19:13:49.993892Z
prove zlib1.4-r0 exists, licenseZlib, provider so:libz.so.1=1.4, and CVE4738
fixed at1.4-r0. Signature entries present; ROOT did not cryptographically verify
or install APKs. Normal signed APK verification must remain enabled.
Sources: <https://secdb.alpinelinux.org/v3.23/main.json>,
<https://secdb.alpinelinux.org/v3.24/main.json>,
<https://pkgs.alpinelinux.org/package/v3.23/main/x86_64/zlib>.
Upstream1.4 ChangeLog also lists this fix. No scanner suppression, exception,
severity downgrade or incomplete-diagnostics-as-PASS is authorized.

## Exact bounded source repair

Only these SIX non-transcript paths may change; starting SHA256s:

- `services/backend/Dockerfile`: `14094ed21f5a1cfcbf6d95d97ab62057f879b33c55059e63bd090cfead541080`.
- `apps/web/Dockerfile`: `4f848974e196d385a9535af7b71f13e828becb815233a35b710f7c3c914b99c1`.
- `infra/nginx/Dockerfile`: `2f5245f230cdf58592bbc8392b8548325c920efd81f019b86ab35f20a986fe2f`.
- `infra/postgres/Dockerfile`: `10aa0843bba461d12249e7f56ce30e1c42a078b7b6c22db49b8cbb4564a8f8bd`.
- `supply-chain/policy.json`: `ad0fa275be209490870a472ab879ebacf0396650e3db650a85b28172c6936f03`.
- `tests/packaging/test_oci_contract.py`: `1cf44b569bcd3d97594139502cd49ca4af378a44cc0b7d6b98b944f0a8b19082`.

Add exact `'zlib=1.4-r0'` to existing APK install commands in BOTH builder and
runtime stages of backend/web. In NGINX/PostgreSQL runtime install the same
exact pin and add installed-version assertions using their existing awk/test
pattern. Preserve NGINX's existing v3.24 registry and all others' approved
v3.23 registry; never mix or add repositories. Preserve every base tag/digest,
all other package pins/removals, labels/provenance/entrypoints/users/config,
Apache .18 repair, application source/locks and browser diagnostics.

Add matching exact zlib entries to the four policy install arrays; keep keys,
registry fields and unrelated bytes unchanged except necessary pinned-formatter
array reflow. Extend existing OCI security/runtime contract assertions to guard
all four images, including separate builder/runtime assertions for backend/web.
Keep existing test discovery counts; assertions must fail for a missing runtime
pin even if a builder pin remains. A minimal existing test-name clarification
is allowed. No unrelated test/refactor/workflow/doc change.

Before ANY source write, reconcile current named remote PR/base/head, clean
all-untracked state, six starting hashes, then compute COMPLETE formatted six-
file candidate plus conservative remaining-work forecast. Use existing pinned
Prettier3.9.6 for policy JSON candidate; no tool upgrade or unrelated reformat.
Baseline27 source paths5914default/5910minimal vsmain40cd; four Docker paths
are additional ->31. U allowance MAX60 additional gross changed lines, giving
at most5974default/5970minimal, SAME overall HARD6000. Actual diff after writes
must match forecast and all bounds; stop before writing if it cannot fit.
Exclude ONLY exact activated order/report/active, never whole oap: INCREMENTS/
MVP-PROGRESS remain source. Four-file family3599/HARD3600 vsSg
`89ab5ec85273ebad10f9c6963b98811cdf992c54` and five-doc285/HARD500 vsD18
`d18b6e4c9423f61de99b516be90619bf2ab5d3e0` stay byte-frozen.

ROOT explicitly reassesses the31-path review trigger: most cumulative lines
are existing qualification tests/tooling. This small four-image dependency
repair is required to restore the frozen qualification's security gate and
adds no product feature, architecture or authority. Splitting a new feature
is not involved; no cap is waived. Peer22-gross estimate assumed no JSON comma/
reflow and insufficient runtime/builder assertions; it is NOT an actual
prewrite forecast. Do not pack/delete proof to fit.

## Verification, local authority and Git workflow

First receive ONE control OK through the exact approved64L RAM reader SHA256
`cd366f11ef13843090c6a2c9c1c49f9266d3666dcd181e284a457aa3f035e961`,
B `/tmp/oap-083-8-u-control/ctlreader`, control FIFO4470111. Reap SAME actual
own handle if running; require EOF/native0 and capture exactly2bytes4f4b,
then select active083-8-u. Old T reader and ROOT72483 are terminal; never poll
foreign/terminal handles or replace/replay a signal. ROOT retains one new U
response reader at actual FIFO4470112 to real EOF/native.

Executor owns routine disposable tool setup, never the human/ROOT. No local
Docker/engine/daemon/probe/build, private WHOLE/LOCAL6 construction/parsing/
execution, production credentials or systems. The existing two private scripts
stay byte-identical INERT/NOT_RUN; future runtime qualification needs separate
ROOT order and literal fresh source binding. Foundation remains registry-only
agent-cow-postgresql0.2.0 with frozen hashes; no Python/Node/browser/app-dependency,
physical schema/API/permission/egress/renderer/iframe/security-header change.

Run once each, bare/native preserved, after source repair:

1. `python -m unittest discover -s tests/packaging -p 'test_*.py'`
2. `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`
3. `python tools/compose/verify.py --root .`
4. `python -m tools.supply_chain.policy validate`

No duplicate focused subsets, historical ALL31 or unaffected Node/backend suites.
Correct only an actual in-scope defect; no unchanged reruns. Record every actual
command/tool/subject/native/complete result and failure/skip/not-run honestly.
Commit EXACT8paths(sixsource+uorder+active) as Iu, sole parentSt; bare push,
remote parent/tree/paths/bytes verification, prompt notification to ROOT.
ROOT independently reviews actual diff/caps and remote evidence before report.
Update PR body via body file/actual REST body field; verify bytes. Lead with
measured zlib fix scope/evidence/limits; never report failedIt as newly green.
Naturally triggered CI provides fresh builds/scans/checks; no manual rerun/
cancel, allowlist/ignore/skip/xfail/mock/timeout/retry/assertion weakening.
If a new out-of-scope failure appears, stop source changes and report exact
job/head/safe category. Failed logs RAM-only, no raw line/URL/tail/payload/file;
scanner artifacts may be inspected with bounded verified safe-field extraction.

## Report, forward qualifications and completion boundary

After ROOT reviews Iu, publish one concise immutable u report with literal Iu
and Report publication commit: SELF, sole NEW report-only commit/parentIu.
Full literal reread after every edit; exact repo pinned ONEfile Markdownlint
native0/zero; private EXCL|NOFOLLOW0600 complete same-filesystem TEMP, direct
same-inode rename/fsync into worktree final. Canonical fresh complete TEMP uses
EXCL|NOFOLLOW/write-all/fsync and PRINT+ASSERT pre/post inode/hash/size/mode/owner
before/after atomic rename. Bare push/native preserved, actual remote head/
parent/solepath/decoded report bytes==worktree/canonical before ONE responseOK/
noLF/close. No next control reader until ROOT direction; no merge by executor.

Preserve q/r/S/T reports and errata by precise order/report reference. T's
canonical first call failed argument parsing before execution; corrected0f7d79
used EXCL but omitted literal NOFOLLOW, no retrocredit. Its fetch echo wrapper
outer0 was not each GH native; decoded62f7f6 and ROOT fresh proof establish bytes.
ROOT's initial synthetic-tree assertion compared a ref-echo sha field; actual
commit.tree and full leaf maps proved equality. No real source mismatch.
T's no-dependency wording means app/lock, Apache OS pins DID change; failedIt
staysfailed. Later zlib diagnosis supersedes its dated package/fix unknown.
No report rewrite or global NOFILES/RAM-only claim; private candidate writes
and stored artifact reference are real writes, not runtime qualification.

Eventual acceptance requires CURRENT repaired implementation+final SELF all20
strict checks plus10actualPGchildren=30TOTAL SUCCESS, none failed/cancelled/
missing/pending/neutral; full current six-image artifact/security audit with
original31targetIDs UNION CVE-2026-4738 absent at ANY severity including relatedIDs,
actual zlib1.4-r0 in all four runtime inventories, Critical0/ignored0/empty
exceptions and unchanged High-risk review standards. Full WHOLE/LOCAL6 private
qualification, all rounds/architecture/privacy/docs/scope/policy review, ROOT-
only merge and verified remote main remain mandatory. Browser nonrecurrence
is not a fixed-cause proof. This dependency repair does not implement remaining
D5 immutable pending U/publication closure or complete Objective083/product/MVP/
release. Human remains release authority; the full product goal is preserved.

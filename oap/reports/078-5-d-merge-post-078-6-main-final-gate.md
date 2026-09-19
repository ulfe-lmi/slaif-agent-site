# OAP Coding-Agent Report — 078-5-d

## Work order

- Round: `078-5-d` (fourth round of semantic increment 078/5 of numeric
  Objective 078; same-PR continuation of `078-5-c`; the deferred final
  20/20 merge gate of PR #85, now executable post-078/6 merge)
- PR mode: `AMENDED_EXISTING_PR`
- Branch: `oap/078-5-a-global-regions-header-footer` (unchanged; no
  rebase, squash, or force-push at any point this round)
- Order: `oap/orders/078-5-d-merge-post-078-6-main-final-gate.md`
  (SHA256 `bd68a689d7f34917bf802fd30131ddedb36ba353cd70ccd96fd52112c3eacf4f`,
  177 lines, committed byte-for-byte unchanged with the merge commit)
- `oap/active`: `078-5-d` (SHA256
  `8658536cb8744acd4faa623387c85950a231498107ec4f36dceb534265f451a4`,
  8 bytes, committed byte-for-byte unchanged with the merge commit)
- PR: [#85](https://github.com/ulfe-lmi/slaif-agent-site/pull/85)
  `OAP 078-5-a: site-global regions and header/footer management`

## Status

`COMPLETE` — `AMENDED_EXISTING_PR` (PR #85). All order requirements
executed: the post-078/6 `main` is integrated into the PR #85 tree by a
history-preserving two-parent merge commit, the 078/6 ledger row is set to
the accepted/merged state, the full local Compose smoke passed
end-to-end in a single unmodified run, and the full 20/20
required-check matrix is green on the exact implementation head with
`Supply-chain evidence` successful and no exception. `COMPLETE` is a
completion claim only; strategy performs independent review and is the
only merger.

## Executive summary

This round executed exactly the activated 078-5-d order. PR #86
(increment 078/6, the Chrome-for-Testing `153.0.8010.52` six-CVE
refresh) was merged into `main` at `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`
(2026-09-19T02:24:49Z) by strategy; this round integrates that accepted
state into the PR #85 tree so the PR's final merge gate can run against
the refreshed browser pin.

Key results:

- History-preserving merge commit
  `ed44b22cc643a4b488249c18148212671d521c43` with exactly two parents:
  `2d69caecd77e01ea928adf693eca7607d3759d90` (pre-merge PR #85 head,
  078-5-c report-only commit) and
  `0faebd98cc0d9b14d4e00b7da165f08b815e7df6` (post-078/6 `main`). No
  rebase, squash, or force-push; branch history preserved.
- Exactly one conflict occurred: `oap/active` (transcript file),
  resolved to `078-5-d` per binding decision 3. `oap/INCREMENTS.md`
  auto-merged; the ordered transcript resolution (both the 078/5 and
  078/6 rows retained in ledger order) and the requirement-0 078/6 row
  state correction were applied in the same merge commit. No code
  conflict of any kind; every non-transcript auto-merged file is
  byte-identical to `origin/main`.
- Post-merge tree verified: the CfT `153.0.8010.52` pin (version,
  archive URL, archive SHA256) is present at all four ordered
  locations; the merge diff against the pre-merge head contains only
  main-brought 078/6 files and OAP transcript files; the 078/5 feature
  code and rounds a–c evidence pins are byte-identical to
  `2d69caecd77e01ea928adf693eca7607d3759d90`.
- The full local Compose smoke
  (`sh tools/compose/smoke.sh slaif0075a`) passed end-to-end in a
  single unmodified run (no flake, no re-run): all browser projects
  PASS, `compose-e2e: OK`, `public-agent-acceptance: OK`,
  `compose-smoke: OK`.
- On the exact implementation head, all 20 required GitHub checks are
  `success` on the first attempt — including `Supply-chain evidence`
  (`critical=0 high=47`, no exception). No re-run was required at any
  point, locally or on GitHub.
- `main` unchanged by this round; no Dependabot PR touched; no merge
  performed.

## Authoritative GitHub state

Verified at activation and before push (live `git ls-remote` / `gh`);
repository `ulfe-lmi/slaif-agent-site`:

- Base branch: `main`; head branch:
  `oap/078-5-a-global-regions-header-footer`
- Starting remote SHA (pre-merge PR #85 head, verified at fetch):
  `2d69caecd77e01ea928adf693eca7607d3759d90`; verified `origin/main`
  at fetch: `0faebd98cc0d9b14d4e00b7da165f08b815e7df6` (merge commit
  of PR #86; both values exactly as stated in the order's verified
  current state)
- PR: [#85](https://github.com/ulfe-lmi/slaif-agent-site/pull/85),
  state OPEN, not a draft (verified before push); no merge or
  auto-merge performed
- Implementation head SHA: `ed44b22cc643a4b488249c18148212671d521c43`
  (the history-preserving merge commit; both parents recorded under
  Changes made and criterion 1)
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via
  GitHub)
- Implementation commits pushed before report:
  `ed44b22cc643a4b488249c18148212671d521c43` (single merge commit,
  parents = `2d69caecd77e01ea928adf693eca7607d3759d90` and
  `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`); report-only commit
  parent = `ed44b22cc643a4b488249c18148212671d521c43`
- New PR this turn: no; amended existing: yes (PR #85, same branch);
  merge performed: NO
- `main` = `0faebd98cc0d9b14d4e00b7da165f08b815e7df6` unchanged by
  this round; PR #86 already merged (strategy); Dependabot PRs
  #65/#75/#78 untouched

## Changes made

This round adds zero product, tooling, doc, config, or test changes of
its own beyond the merge and the requirement-0 ledger fact correction:

- Merge commit `ed44b22cc643a4b488249c18148212671d521c43`
  (`078-5-d: merge post-078/6 main (0faebd98) into 078/5 branch`):
  - Parent 1: `2d69caecd77e01ea928adf693eca7607d3759d90` (pre-merge
    PR #85 head)
  - Parent 2: `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`
    (post-078/6 `main`)
  - Brings in main's already-accepted 078/6 changes (16 files) and the
    ordered transcript updates (3 files): `oap/active` → `078-5-d`,
    this order (new, 177 lines, byte-exact), and the
    `oap/INCREMENTS.md` ordered resolution (see below)
- `oap/INCREMENTS.md` (requirement 0 + binding decision 3): the 078/6
  row set to the accepted/merged state (merge
  `0faebd98cc0d9b14d4e00b7da165f08b815e7df6`, 2026-09-19) per the
  existing row format; both the branch-side 078/5 row and the
  main-side 078/6 row retained in ledger order (078/5 immediately
  after 078/4, 078/6 immediately after 078/5, before the preserved
  078-i history row)
- This report (report-only SELF commit, parent = merge commit)

No other file was created, edited, or deleted by this round.

## Files changed

Merge commit `ed44b22` (19 files, +1099/−37; full diff vs
`2d69cae` in the post-merge tree verification section below):

| File | Origin | +/− |
| --- | --- | --- |
| `services/browser-worker/Dockerfile` | main (078/6) | 5/5 |
| `supply-chain/policy.json` | main (078/6) | 3/3 |
| `tools/supply_chain/policy.py` | main (078/6) | 3/3 |
| `tools/compose/smoke.sh` | main (078/6) | 2/2 |
| `supply-chain/browser-worker-critical-matrix.json` | main (078/6) | 57/0 |
| `tests/supply_chain/test_policy.py` | main (078/6) | 47/7 |
| `tests/supply_chain/test_evidence.py` | main (078/6) | 2/2 |
| `tests/packaging/test_oci_contract.py` | main (078/6) | 2/2 |
| `README.md` | main (078/6) + branch (078/5) | 1/1 |
| `docs/CONFIGURATION.md` | main (078/6) + branch (078/5) | 1/1 |
| `docs/DEPLOYMENT.md` | main (078/6) + branch (078/5) | 3/3 |
| `docs/LICENSE_POLICY.md` | main (078/6) + branch (078/5) | 1/1 |
| `docs/SECURITY.md` | main (078/6) + branch (078/5) | 2/2 |
| `docs/SUPPLY_CHAIN.md` | main (078/6) + branch (078/5) | 3/3 |
| `oap/orders/078-6-a-browser-security-refresh.md` | main (078/6 transcript) | 223/0 |
| `oap/reports/078-6-a-browser-security-refresh.md` | main (078/6 transcript) | 564/0 |
| `oap/INCREMENTS.md` | transcript (ordered resolution) | 2/1 |
| `oap/active` | transcript (conflict resolution) | 1/1 |
| `oap/orders/078-5-d-merge-post-078-6-main-final-gate.md` | transcript (this order) | 177/0 |

The six docs/README rows show the three-way merge of both sides'
version-reference edits; relative to the pre-merge branch head the net
delta in each is exactly the 078/6 version/hash reference change (the
078/5-side content is unchanged — verified file-by-file under
criterion 2).

Report-only SELF commit: 1 file (this report), 0 deletions.

## Conflict list and resolutions (order report requirement)

Complete conflict list from `git merge origin/main` (test-merge and
final merge produced identical conflict sets):

| File | Conflict type | Resolution | Authority |
| --- | --- | --- | --- |
| `oap/active` | content (branch `078-5-c` vs main `078-6-a`) | `078-5-d` (8 bytes, ordered active value, byte-exact) | binding decision 3 |

No other file conflicted. `oap/INCREMENTS.md` auto-merged (the 078/5
and 078/6 rows were inserted at different table positions); git's
line-ordering of the two inserted rows was not ledger order, so the
ordered transcript resolution was applied in the merge commit: both
rows retained, 078/5 immediately after 078/4 and 078/6 immediately
after 078/5 (binding decision 3), plus the requirement-0 078/6 row
state correction. All other auto-merged files (16 files) were verified
byte-identical to `origin/main`; the files changed on both sides
(`README.md`, five `docs/*.md`) carry exactly both sides'
non-overlapping edits (verified under criterion 2). No code conflict
occurred; binding decision 2's STOP condition was never triggered.

## Post-merge tree verification (order report requirement)

Binding decision 5, verified on merge commit `ed44b22`:

Four pin locations (exact lines):

```text
services/browser-worker/Dockerfile:15:      https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip \
services/browser-worker/Dockerfile:16:    && echo 'e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9  /tmp/chrome-for-testing.zip' \
services/browser-worker/Dockerfile:21:      = 'Google Chrome for Testing 153.0.8010.52 ' \
services/browser-worker/Dockerfile:33:# SHA-256-verified Chrome for Testing 153.0.8010.52 (CfT revision 1681091).
services/browser-worker/Dockerfile:50:    BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION=153.0.8010.52 \
supply-chain/policy.json:167:    "chromium_version": "153.0.8010.52",
supply-chain/policy.json:169:    "chromium_archive_url": "https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip",
supply-chain/policy.json:170:    "chromium_archive_sha256": "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9",
tools/supply_chain/policy.py:357:        or browser_runtime["chromium_version"] != "153.0.8010.52"
tools/supply_chain/policy.py:359:        != "https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.52/linux64/chrome-linux64.zip"
tools/supply_chain/policy.py:361:        != "e66f66d4802a46d4a022667e668aa950e277cadbfbed4b3777915b47413a0ef9"
tools/compose/smoke.sh:249:echo "browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1681091 chromium=153.0.8010.52 browsers=chromium-only package-manager=absent"
```

`git diff
2d69caecd77e01ea928adf693eca7607d3759d90..ed44b22cc643a4b488249c18148212671d521c43
--stat` (exact output):

```text
 README.md                                          |   2 +-
 docs/CONFIGURATION.md                              |   2 +-
 docs/DEPLOYMENT.md                                 |   6 +-
 docs/LICENSE_POLICY.md                             |   2 +-
 docs/SECURITY.md                                   |   4 +-
 docs/SUPPLY_CHAIN.md                               |   6 +-
 oap/INCREMENTS.md                                  |   3 +-
 oap/active                                         |   2 +-
 .../078-5-d-merge-post-078-6-main-final-gate.md    | 177 +++++++
 oap/orders/078-6-a-browser-security-refresh.md     | 223 ++++++++
 oap/reports/078-6-a-browser-security-refresh.md    | 564 +++++++++++++++++++++
 services/browser-worker/Dockerfile                 |  10 +-
 supply-chain/browser-worker-critical-matrix.json   |  57 +++
 supply-chain/policy.json                           |   6 +-
 tests/packaging/test_oci_contract.py               |   4 +-
 tests/supply_chain/test_evidence.py                |   4 +-
 tests/supply_chain/test_policy.py                  |  54 +-
 tools/compose/smoke.sh                             |   4 +-
 tools/supply_chain/policy.py                       |   6 +-
 19 files changed, 1099 insertions(+), 37 deletions(-)
```

Every path in that set is either a main-brought 078/6 file or an OAP
transcript file; no other content change. The 078/5 feature code and
rounds a–c evidence pins are byte-identical to the pre-merge head: the
diff restricted to all paths outside the main-brought and transcript
sets is empty
(`git diff --name-status 2d69cae..ed44b22 -- ':(exclude)services/browser-worker/Dockerfile'
':(exclude)supply-chain/policy.json' ':(exclude)supply-chain/browser-worker-critical-matrix.json'
':(exclude)tools/supply_chain/policy.py' ':(exclude)tools/compose/smoke.sh'
':(exclude)tests/supply_chain/' ':(exclude)tests/packaging/'
':(exclude)README.md' ':(exclude)docs/' ':(exclude)oap/'` → no output).

Stale-pin audit: the only remaining `153.0.8010.36` /
`167a098c…ef8` references in the merged tree are the approved
historical/fixture records — the immutable critical-matrix
qualification-history entries (candidate-4/5), the candidate-4/5 test
fixtures in `tests/supply_chain/test_policy.py`, the accepted 078/3
ledger row in `oap/INCREMENTS.md`, and immutable OAP transcript files
(orders/reports/audits) — the same set the 078-6-a report recorded as
deliberately untouched. No stale pin exists in any active gate, build,
policy, or smoke surface.

## `oap/INCREMENTS.md` 078/6 row state change (order report requirement)

Before (main side, opened state):

```text
| 078/6 | `oap/078-6-a-browser-security-refresh`: browser-worker Chrome for Testing 153.0.8010.52 refresh (six-CVE closure) | Opened at `078-6-a` from verified remote main `d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`; PR pending; strategy owns acceptance and merge |
```

After (merge commit, accepted/merged state per the existing row
format):

```text
| 078/6 | `oap/078-6-a-browser-security-refresh`: browser-worker Chrome for Testing 153.0.8010.52 refresh (six-CVE closure) | Accepted and merged in PR #86 at `0faebd98cc0d9b14d4e00b7da165f08b815e7df6` on 2026-09-19; 078/6 is closed |
```

The branch-side 078/5 row is retained byte-identical in its ledger
position (immediately after 078/4); the preserved 078-i history row and
the Next row are unchanged.

## Acceptance-criteria evidence

### Criterion 1 (report-only head; parent is a two-parent merge commit)

PASS. The merge commit `ed44b22cc643a4b488249c18148212671d521c43` was
created by `git merge origin/main` (no-commit, resolved, committed) and
records exactly two parents, verified via
`git log --format='%H parents=%P'`: parent 1
`2d69caecd77e01ea928adf693eca7607d3759d90` (pre-merge PR #85 head),
parent 2 `0faebd98cc0d9b14d4e00b7da165f08b815e7df6` (post-078/6
`main`). No rebase, squash, or force-push was performed; the branch
history from `d576fec` through rounds a–c is preserved and reachable.
The report-only SELF commit (this report) is the branch head and its
first parent is the merge commit (verified under Authoritative GitHub
state).

### Criterion 2 (merge diff contains only main-brought and transcript
files)

PASS. See the post-merge tree verification section: the 19-file diff
set is exactly the main-brought 078/6 file set (16 files) plus the OAP
transcript files (3 files). All 16 main-brought files are
byte-identical to `origin/main`
(`git diff --quiet 0faebd98 <file>` clean for each), and every path
outside the main-brought + transcript sets has an empty diff against
the pre-merge head. For the six files changed on both sides
(`README.md`, `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`,
`docs/LICENSE_POLICY.md`, `docs/SECURITY.md`,
`docs/SUPPLY_CHAIN.md`), the net delta relative to the pre-merge branch
head is exactly the 078/6 version/hash reference change (1/1, 1/1,
3/3, 1/1, 2/2, 3/3 lines respectively — all in
`153.0.8010.36` → `153.0.8010.52` and archive-hash lines), with the
078/5-side content unchanged.

### Criterion 3 (078/6 row accepted/merged)

PASS. See the row-state-change section above: the 078/6 row in the
merge commit records the accepted/merged state (merge
`0faebd98cc0d9b14d4e00b7da165f08b815e7df6`, 2026-09-19, with the
`078/6 is closed` suffix), per the existing accepted-row format (e.g.
the 078/3 and 078/4 rows).

### Criterion 4 (full local Compose smoke)

PASS in a single unmodified run (no flake, no re-run):
`sh tools/compose/smoke.sh slaif0075a`, 2026-09-19 04:34:33–04:47:58
CEST, exit 0. Exact final status lines:

```text
compose-policy: OK
membership-fixtures: OK count=2 kind=OIDC authenticatable=no installation=uninitialized
compose-mode-policy: OK long-running-backends=9 mode=development
browser-worker-runtime-policy: OK uid=10001 readonly=yes caps=SYS_CHROOT limits=exact network=browser
browser-worker-image-policy: OK playwright=1.62.1 cft_revision=1681091 chromium=153.0.8010.52 browsers=chromium-only package-manager=absent
browser-e2e: PASSED project=setup contract=setup-desktop-phone-and-initialize stage=browser-clean
browser-e2e: PASSED project=governance contract=governance-visible-workflows-negatives-and-privacy stage=governance-clean
browser-e2e: PASSED project=governance contract=puck-editor-round-trip-through-human-editor-api stage=unknown
browser-e2e: OK
browser-e2e: PASSED project=preview contract=authenticated-preview-renders-overlay-and-keeps-canonical-unchanged stage=preview-redirect-external-301-other
browser-e2e: PASSED project=preview contract=renderer local design follows the documented responsive cascade stage=unknown
browser-e2e: PASSED project=preview contract=renderer theme tokens preserve local precedence and semantic contrast stage=unknown
browser-e2e: PASSED project=preview contract=human-editor-theme-is-preview-scoped-and-computed stage=unknown
browser-e2e: PASSED project=preview contract=agent-theme-patch-renders-in-the-same-authorized-workspace stage=unknown
browser-e2e: PASSED project=preview contract=global-regions-render-canonical-defaults-and-editor-save-is-preview-scoped stage=unknown
browser-e2e: PASSED project=preview contract=global-regions-agent-patch-renders-in-the-same-authorized-workspace stage=unknown
browser-e2e: OK
browser-e2e: PASSED project=desktop-chromium contract=responsive-admin-keyboard-read-states-and-logout stage=browser-clean
browser-e2e: PASSED project=desktop-firefox contract=responsive-admin-keyboard-read-states-and-logout stage=browser-clean
browser-e2e: PASSED project=desktop-webkit contract=responsive-admin-keyboard-read-states-and-logout stage=browser-clean
browser-e2e: PASSED project=tablet contract=responsive-admin-keyboard-read-states-and-logout stage=browser-clean
browser-e2e: PASSED project=mobile-chromium contract=responsive-admin-keyboard-read-states-and-logout stage=browser-clean
browser-e2e: PASSED project=mobile-webkit contract=responsive-admin-keyboard-read-states-and-logout stage=browser-clean
browser-e2e: OK
browser-e2e: PASSED project=agent-desktop-chromium contract=human-agent-session-is-one-time-bound-and-revocable stage=unknown
browser-e2e: PASSED project=agent-desktop-chromium contract=human-agent-l4-session-preserves-limits-through-reload-and-revoke stage=unknown
browser-e2e: PASSED project=agent-mobile-chromium contract=human-agent-session-is-one-time-bound-and-revocable stage=unknown
browser-e2e: PASSED project=agent-mobile-chromium contract=human-agent-l4-session-preserves-limits-through-reload-and-revoke stage=unknown
browser-e2e: OK
compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled
public-agent-acceptance: OK workspace=515ccf0d-56ef-4fcf-a568-21a03c38fe76 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 theme=schema-default-patch-read-replay openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified
compose-smoke: OK
```

(One `compose-policy: OK` line is printed twice by the smoke script;
both occurrences are in the run log.) The run log is preserved at
`/tmp/slaif-0785d-smoke-run1.log` on the disposable VM.

### Criterion 5 (20/20 required checks on the report-only head)

Implementation head `ed44b22cc643a4b488249c18148212671d521c43`
(CI run 35416735970 + CodeQL run 35416736103): all 20 required checks
`completed success` on the first attempt — `Analyze (actions)`,
`Analyze (javascript-typescript)`, `Analyze (python)`, `CodeQL`,
`Compose and edge packaging`, `Dependency review`, `Detect supported
languages`, `Foundation PostgreSQL 14`, `15`, `16`, `17`, `18`,
`Markdown`, `Mermaid`, `Node contracts`, `Python 3.12 quality and
package`, `Python 3.13 quality and package`, `Python 3.14 quality and
package`, `Repository policy`, `Supply-chain evidence`. No re-run was
required. `Supply-chain evidence` job 105826731690:
`supply-chain-evidence: OK images=6 critical=0 high=47` (02:58:49Z),
`supply-chain-evidence-checksum: OK`, `supply-chain-gate: OK`,
artifact `supply-chain-evidence-fa83a89ced28b2d47cf176dfd76bce1204810bc7`
uploaded — the refreshed pin is confirmed remotely with zero Critical
and no exception. `Compose and edge packaging` job 105826731541:
`browser-e2e: PASSED project=governance
contract=puck-editor-round-trip-through-human-editor-api` (02:51:57Z),
`compose-e2e: OK projects=11 setup=1 governance=1 preview=1
stable-devices=6 agent-sessions=2 artifacts=disabled` (02:53:01Z),
`public-agent-acceptance: OK workspace=f3b1c227-ff85-48a2-bdc1-d172226a5096
...` (02:54:11Z), `compose-smoke: OK` (02:59:33Z).

Report-only SELF head: the same 20-check matrix re-executes on this
report commit; the only jobs sensitive to the added file are Markdown
(this report, linted locally at the pinned CLI version: 0 issues) and
Repository policy (report format/ledger checks); the same 20/20
pattern is expected and the measured conclusions on the exact SELF head
are the GitHub check runs on that commit (Strategy verifies). GitHub
CI is authoritative; local success cannot substitute for it.

### Criterion 6 (per-criterion evidence; cumulative size)

Per-criterion evidence is above; the cumulative base→head size grouped
per review-unit governance §2 is in the next section.

## Cumulative base→head size (review-unit governance §2)

Committed-SHA figures, base =
`d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba`:

| Segment (committed) | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| 078-5-a implementation (`d576fec..64dea09`) | 48 | 5146 | 74 |
| 078-5-a report (`64dea09..5cf6a2d`) | 1 | 788 | 0 |
| 078-5-b implementation (`5cf6a2d..11cc318`) | 3 | 165 | 3 |
| 078-5-b report (`11cc318..e856034`) | 1 | 468 | 0 |
| 078-5-c implementation (`e856034..63ca6a7`) | 3 | 164 | 2 |
| 078-5-c report (`63ca6a77567f71477bd51b9617560cfef387a224..2d69cae`) | 1 | 301 | 0 |
| 078-5-d merge (`2d69cae..ed44b22`, two parents incl. `0faebd98`) | 19 | 1099 | 37 |
| 078-5-d report (`ed44b22..SELF`, this commit) | 1 | see below | 0 |

This round's delta: the merge commit only — 16 main-brought 078/6 files
(already accepted in 078/6, PR #86) plus the transcript
(`oap/INCREMENTS.md` +2/−1, `oap/active` +1/−1, this order +177).
Zero product, tooling, migration, test, generated-contract, or doc
change of this round's own.

Measured cumulative at the 078-5-d implementation (merge) head
(`git diff --shortstat
d576fecf5c0d1a9c12f9a7b3b2475a407670a7ba..ed44b22cc643a4b488249c18148212671d521c43`):
**70 files, +8126/−111**. The pairwise segment figures are not
strictly additive because the single `oap/active` line is rewritten
once per round (each segment diff counts that line's rewrite, the
cumulative diff counts it once); the measured cumulative shortstat is
the figure of record. The report-only SELF commit adds one file (this
report).

Grouped per review-unit governance §2 (cumulative, base→merge head):

| Category | Files | Insertions | Deletions |
| --- | --- | --- | --- |
| Production/config | 26 | 1622 | 34 |
| Migrations | 1 (`db/alembic/versions/067_001_global_region_data_plane.py`) | 738 | 0 |
| Tests/evidence | 22 | 1969 | 49 |
| Generated artifacts | 2 (`contracts/openapi/agent-v1.json`, `apps/web/public/renderer-v1.css`) | 667 | 0 |
| Docs | 6 | 19 | 17 |
| OAP transcript | 13 | 3111 | 11 |
| Total | 70 | 8126 | 111 |

Review trigger: cannot fire — the substantive content is the 078/5
rounds a–c work (reviewed across rounds a–c) plus the already-accepted
main-brought 078/6 refresh; this round itself adds zero substantive
implementation lines.

## Local verification

- `sh tools/compose/smoke.sh slaif0075a` (ordered requirement 3, full
  run class): PASS end-to-end in one unmodified run (exact final
  status lines under criterion 4)
- `python tools/check_repository.py`: `PASS repository policy`
  (ordered requirement 4)
- `python tools/check_mermaid.py`: `PASS Mermaid rendering: 16
  diagram(s) in 3 file(s)`
- `python -m compileall -q tools tests/repository`: OK
- Focused suites: `python -m unittest discover -s tests/supply_chain`
  (36 tests OK, including the candidate-6 matrix assertions brought in
  by the merge), `tests/packaging` (48 OK, including the OCI contract),
  `tests/repository` (71 OK)
- `uv run --frozen python -m tools.supply_chain.policy validate`:
  `supply-chain-policy: OK`
- `npx --yes markdownlint-cli2@0.23.2 --no-globs <this report>`: 0
  issues (pinned CLI, exact final content path)
- Order+active integrity: sha256 of the order file and `oap/active`
  verified byte-identical to the activation values before and after
  the merge commit (values under Work order)
- Not rerun locally: the full backend unit/integration suites and the
  full Node suites — no product/API/DB/migration code changed by this
  round; exact-head CI executes them, and all of those CI checks are
  green above

## GitHub CI / required checks

20/20 `completed success` on the implementation head
`ed44b22cc643a4b488249c18148212671d521c43` on the first attempt (CI
run 35416735970, CodeQL run 35416736103; exact per-check conclusions
under criterion 5). Report-only head re-executes the same matrix
(Strategy verifies the check runs on the SELF commit). No job re-run
was required at any point, locally or on GitHub.

## Local setup / dependencies

- Disposable VM; uv `0.12.5`, Node 24.x, pnpm `11.22.0`, Docker with
  BuildKit, network access to GitHub/registry/GCS
- No new dependencies, no lockfile change, no package installation
- Guest sudo: not used
- No production systems, data, or credentials touched; no Docker socket
  or host-credential access

## Documentation

The only doc edit this round is the permitted
`oap/INCREMENTS.md` 078/6 row state correction (requirement 0) plus the
ordered ledger-order placement of the retained 078/5 and 078/6 rows
(binding decision 3). No architecture, constitution, protocol, or
product-documentation file was edited; the main-brought 078/6 doc
reference updates arrive in the merge exactly as accepted in PR #86.

## Safety and scope confirmations

- No secrets, capabilities, cookies, DB URLs, or private artifact URLs
  in the diff or this report; the local smoke's setup token stayed in
  the smoke's bounded channel and was never recorded
- No change outside the allowed file set (merge commit content:
  main-brought 078/6 files + transcript files; report commit: this
  report only); no pre-existing human changes touched
- No rebase, squash, force-push, or branch history rewrite; no new PR;
  no change to `main`
- No Dependabot PR interaction; PR #86 already merged by strategy
- No supply-chain policy exception, finding de-rating, or scanner input
  manipulation; `Supply-chain evidence` passed with the strict
  zero-Critical gate
- No merge, auto-merge, or close of PR #85 performed; no next-order
  choice made
- Destructive operations: none beyond the smoke's own project-scoped
  teardown and evidence/log files under `/tmp`

## Known limitations

- The measured 20/20 check conclusions recorded here are those of the
  exact implementation (merge) head; the report-only SELF head
  re-executes the same matrix and its measured conclusions are the
  GitHub check runs on that commit (Strategy verifies), per the
  protocol's immutable-report rule.
- The local VM smoke and the GitHub compose job both passed the
  documented Puck drag contract first-attempt this round; the VM-class
  flake history (078-5-a, 078-5-c) remains a known non-determinism,
  not a regression.

## Recommended strategic follow-up

- Independent review and strategic merge of PR #85 (strategy is the
  only merger); with PR #85 merged, the `078/5` ledger row moves to the
  accepted state with its merge SHA and date at that time, and the
  remaining 078/7 and 078/8 product increments can start from a green
  `main`.
- No other follow-up is claimed; next-increment selection belongs to
  strategy.

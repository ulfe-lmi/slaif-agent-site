# OAP Work Order — 072-u

## Objective

Continue Objective 072 on its sole PR #66 and close two final strategic-review
governance blockers without changing browser product behavior: reconcile the
authoritative live risk issue body with the exact 41-entry repository exception,
and publish an append-only forensic correction for prior report-immutability
violations. Do not create another PR and do not merge.

## GitHub objective state and verified current state

- Numeric objective: `072`; active round: `072-u`; mode:
  `AMEND_EXISTING_PR`.
- Repository: `ulfe-lmi/slaif-agent-site`; base: `main`; amend only PR
  [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66), branch
  `oap/072-browser-worker-real-playwright`.
- Required starting remote head:
  `07e92ca24c956abad72fdda0bdf3630c4f0dd686`; its sole parent is final
  implementation `8f6928829b0b52ce298dd6a14e66bfd84bbf2d79`. Remote `main`
  is `082f2359b0c4d59b692580d17992c35d46183b12`.
- PR #66 is open, non-draft, uniquely maps Objective 072, and is currently
  mergeable. All 20 checks on the required starting head are successful.
- `supply-chain/vulnerability-exceptions.json` contains exactly 41 unique
  Critical findings for `pkg:generic/chrome@152.0.7977.64`, scope
  `browser-worker`, approver `human:project-owner`, issue #67, created
  `2026-08-28`, expiry `2026-09-04`. The human explicitly authorized this
  temporary bounded exception.
- Live issue #67 is open and its latest comment lists the 41-entry set, but its
  body still says and lists exactly 31 while also calling itself the sole
  exception reference. This fails activated order 072-n requirement 2.
- Git history proves two published report files were subsequently overwritten:
  `072-m` was introduced at `dedf5965bd1fb5e40fedce0432d58cbeb1d03330`
  (parent `aef558f454d4bf0aea5e3649c5abfe04ec9a7e7d`) and modified at
  `e849ea2380ff2056ae724ec957a59c1187209f0c`; `072-o` was introduced at
  `20db9b766a5e646d22372ec1122a78a4ece5d714` (parent
  `c93480b7e881606e89ce2e25cb9ab91c8853dbae`) and modified at
  `23aeaf6b71023ab0417adc66e2fd436ee6d9bfe2`,
  `5249c5d8337f40f6a8dcc520c823218dc533763c`,
  `dd05b9d0505a081c74476f63b5227fad724bf2ad`, and
  `74cb99e3ec31cb2c9284190977792e300d59f51e`. This violated the
  append-only OAP report protocol and cannot be made never to have happened.
- Known additional clerical history: 072-p incorrectly labels its publication
  `CREATED_NEW_PR` although it amended PR #66; 072-q already records the
  correction. Preserve this fact in the forensic record.

## Strategic decision and bounded scope

Do not abandon or rebuild the 21k-line product PR solely to cosmetically erase
an already-visible governance violation. Preserve the Git evidence and make the
transcript truthful through this new immutable correction round. This is a
strategic process remedy, not retroactive compliance: 072-m and 072-o remain
recorded protocol deviations, while all future reports remain strictly
append-only.

Allowed changes/actions are only:

1. Update the existing live GitHub issue #67 body in place as specified below.
2. Commit the already-published `072-u` order and `oap/active` unchanged.
3. Create and publish exactly one new immutable report
   `oap/reports/072-u-reconcile-risk-and-transcript.md` containing the required
   evidence and forensic correction.

Do not modify any prior order or report. Do not change product code, tests,
workflows, dependencies, lockfiles, images, migrations, grants, runtime,
Compose, scanner policy, exception JSON, documentation outside the new report,
or issue state. Do not rerun broad local product, Compose, browser, or supply-
chain work merely for this governance-only round. Do not create a second PR,
merge, enable auto-merge, publish a release, or select later work.

## Requirements and binary acceptance

1. Edit the body—not merely a comment—of open issue #67 so it states 41 rather
   than 31 and lists an exact set equal to all 41 `id` values in
   `supply-chain/vulnerability-exceptions.json`, with no missing or extra CVE.
   Preserve exact runtime/PURL, human authorization, isolated-worker
   mitigations, owner, `2026-09-04` expiry, immediate `.65+` qualified-metadata
   removal trigger, and open state. It may retain a concise drift history but
   may not leave a contradictory current count/set.
2. Verify the remote issue body after mutation using `gh`, parse its current CVE
   set deterministically, and compare it to the repository exception set.
   Acceptance requires `state=OPEN`, body count language `41`, 41 unique body
   IDs, exact set equality, exact PURL, scope, approver, expiry, mitigations, and
   removal trigger. A comment-only update fails.
3. In the new 072-u report, record the exact original-add and later-modification
   commit history above for 072-m and 072-o, state explicitly that those files
   were not immutable, and state that their current versions are corrected
   reconstructions rather than original publication artifacts. Also preserve
   the 072-p PR-mode clerical correction and the fact that 072-n did not satisfy
   its issue-body requirement until 072-u.
4. Do not edit, restore, amend, or republish any 072-a through 072-t report.
   Verification must show the implementation commit changes only the unchanged
   strategic order and active pointer, and the report-publication child changes
   only the new 072-u report.
5. After pushing, require the current PR head to be the report-only commit whose
   sole parent is the literal implementation commit stated in the report.
   Inspect all current required GitHub checks; every required check must be
   successful before this round can be accepted, with no failed, cancelled,
   missing, skipped-as-success, or pending check.

## Security and local authority

This round must neither expand nor conceal the temporary vulnerability
exception. Do not change credentials, expose capability/token/artifact values,
access production systems, weaken scanning, suppress findings, or extend the
expiry. Routine repository/GitHub inspection belongs to the coding agent; no
package, browser, database, or service setup is required.

## GitHub workflow and report contract

Fetch and reconcile GitHub first. Require the exact named open PR, branch, base,
and starting head; stop and report honestly on mismatch. Commit/push the
activated order and `oap/active` unchanged, perform the bounded issue-body
repair and verification, then publish the exact new report as the sole change
in a final report-only commit. Never create another PR or merge.

The report must include: `Result`; repository/PR/branch/base; starting head;
literal 40-hex implementation SHA; `Report publication commit: SELF`; exact
changed files per commit; remote issue URL/state/body update and deterministic
41-ID comparison; unchanged PURL/scope/approver/expiry/mitigations/removal
trigger; the complete 072-m/072-o forensic commit history and explicit protocol-
deviation statement; 072-p and 072-n corrections; current PR head/parent; every
current check and conclusion; skipped/not-run work; no prior report edits; no
product/dependency/policy/exception changes; no second PR; and no merge.

Signal exactly `OK` only after the report is immutable and all claimed remote
state is already published.

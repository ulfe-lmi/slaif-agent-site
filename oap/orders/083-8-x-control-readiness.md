# 083-8-x — stabilize the Control API wrong-role smoke scenario

This order takes effect after canonical activation and one exact control OK.

## Identity and current evidence

Objective 083, increment 083/8, AMEND_EXISTING_PR #112,
<https://github.com/ulfe-lmi/slaif-agent-site/pull/112>. Use branch
`oap/083-8-a-qualify-public-whole-session` and base `main`
`40cd172109a22ef5f342589b59a4293f35379651`.
Starting head `38bb5e066594745f43523f023b3a6242977d9621` is the verified
W report-only commit. Its parent is
`14facd0ff69d6c83a3b50a871ccd5307f74e5d2e`.
W formally closed PARTIAL after exact response OK and complete remote review.

Iw CI 42925034990 finished with 24 of 25 jobs successful and Compose job
130209254438 failed in step 8. Its browser E2E, Agent API acceptance and restart,
and worker recovery passed. The subsequent Control readiness fixture printed
`stage=wrong-role operation=await-readiness reason=timeout`. Both the negative
role-mismatch wait and the positive restored-ready wait use that same label.
The actual timed-out wait and the historical root cause remain open.
Iw supply-chain evidence removed the ten targeted findings at the exact
installed versions. The four newly measured backend SQLite High findings and
the private WHOLE/LOCAL6 qualifications remain separate work.

On the report-only Sw head, CI 42928101256 completed all 25 workflow jobs
successfully. CodeQL 42928101264 passed. The 20 strict named/app checks and
the ten actual PostgreSQL child checks are successful (ROOT ac6dd7).
Compose job 130219627297 passed step 8. Its actual log shows the wrong-role
stage followed by unreadable-secret, recovery, fixture OK, and whole smoke OK
(ROOT 8a5165). GitHub confirms the same main and Sw head (ROOT 98dc7a).
Iw and Sw have identical product source and different Compose outcomes.
The wrong-role transaction ordering defect remains in the shared source.
Artifact 13814649954 independently reproduces the W package result
(ROOT 6ec2d3). Keep current scans and the four SQLite findings visible.

## Scope and acceptance

Change only `tools/compose/control_readiness.py` and its tests in
`tests/packaging/test_compose_policy.py`. Preserve the current source footprint
outside those files. The wrong-role setup currently sends its role switch
and `pg_terminate_backend` query to PostgreSQL in one psql command string.
That request runs in a single transaction. The backend termination signal
can precede commit, allowing an independent readiness probe to reconnect
under the old committed role. Keep the grant and revoke atomic, then
terminate the existing sessions in a separate checked database request after
commit. Preserve the original exact fixture login and PID filter.
<https://www.postgresql.org/docs/current/app-psql.html>

Preserve the expected 503 and role-mismatch reason, liveness and edge
unavailability during the wrong-role state, and ready recovery on the live
service after role restoration. Use distinct fixed allowlisted operation
labels for both waits. Keep the existing time bounds, other readiness stages
and cleanup. Add focused packaging coverage for transaction ordering and
the safe diagnostics. Keep credentials, raw command output, and response
bodies out of the diagnostic. Product code, role policy, Compose topology,
CI, browser fixtures, packages and private qualification remain outside scope.

The W baseline is 39 source paths with 6227 default and 6223 minimal gross
lines against main. The two existing files are currently unchanged from main.
A small fixture and unit-contract repair justifies a cumulative footprint
of up to 41 source paths and 90 additional gross lines under both algorithms,
for an overall bound of 6320. Keep the four-file family at 3599 and the D18
five-doc footprint at 320. Measure actual scope before commit, excluding
only the exact versioned order/report transcript and active pointer.

## Verification and delivery

Run the existing pinned Ruff lint and format checks for both changed files.
Use the complete pinned Node and Python PATH before running the full packaging
suite once as a bare command. Record actual counts and native exit outcomes.
Natural CI must exercise the real wrong-role scenario, both readiness waits,
all later smoke stages, and the existing protection checks. The approved CI
commands and predicates are the runtime evidence. Preserve every attempt
accurately and report remaining limitations. The current run's full required
20 checks, ten PostgreSQL child checks, and six-image evidence remain part of
independent acceptance. Standalone CI evidence does not qualify private runtime.

Use the existing visible executor in
`/home/janezp/codex-work/slaif-agent-site-083-8-j`. Canonical OAP is
`/home/janezp/codex-work/slaif-agent-site/oap`. Follow coding AGENTS and the
coding protocol. The human's allowed startup command after a genuine crash
is `codex --yolo --profile early-beta`.

Use the proven 64-line, 2116-byte control-reader source in
`/tmp/oap-083-8-x-control/root-approved-next-control-reader-source.json`
with SHA-256
`334815b9da28445e16f7a86bfaa4bb4943acff455b3e383e9de4a8c0e66439a1`.
Create the named private 0700 ctlreader directory before executing the exact
source. Receive one control OK, verify real EOF and native status, then read
exact active and the full order.

Stage the two source files and unchanged order and active only. Commit on
the stated parent, then push using the explicit refspec
`git push origin HEAD:refs/heads/oap/083-8-a-qualify-public-whole-session`.
Verify the exact parent, paths and bytes on GitHub, and update the PR body
with dated facts. Use the same explicit refspec for the report-only commit.
Preserve the original human checkout, immutable transcript and unintended
alias ref pending strategic reconciliation. Strategic review and merge remain
ROOT-owned.

Publish one concise immutable report with a literal implementation SHA and
`Report publication commit: SELF`. Report the exact tested predicates, commands,
results, scope, CI and remaining gates. Lint the complete report with the
repository's exact pinned one-file Markdownlint invocation, reread after final
editing, and publish identical bytes atomically to the execution and canonical
locations. After the report-only commit has been pushed and its exact remote
parent and bytes verified, send one exact two-byte response OK and close.

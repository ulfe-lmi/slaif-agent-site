# 083-8-x report: stabilize the Control API wrong-role smoke scenario (PARTIAL)

- Order: `oap/orders/083-8-x-control-readiness.md` (108L, 6379B,
  SHA `ff58751f6420fdbcf220a8acfce4c207f00756662d07add82f2be4a47e15d42e`)
- Mode: AMEND_EXISTING_PR
- Status: PARTIAL
- Repo: ulfe-lmi/slaif-agent-site
- PR: <https://github.com/ulfe-lmi/slaif-agent-site/pull/112> (open)
- Remote head branch: `oap/083-8-a-qualify-public-whole-session`
- Base: main `40cd172109a22ef5f342589b59a4293f35379651`
- Starting head (Sw): `38bb5e066594745f43523f023b3a6242977d9621`
  (verified W report-only commit)
- Implementation SHA (Ix): `fd5ad9d79f372a015de48ced694305b3308c5cda`
  (sole parent Sw)
- Report publication commit: SELF
- Pushed commits: Ix (implementation; 4 paths) and SELF (this report
  only), both via the explicit refspec
  `git push origin HEAD:refs/heads/oap/083-8-a-qualify-public-whole-session`

## Defect and evidence (transaction-ordering race)

The wrong-role setup sent its REVOKE/GRANT role switch and the
`pg_terminate_backend` query in one psql command string, i.e. one
implicit transaction. The backend termination signal could precede
commit, allowing an independent readiness probe to reconnect under
the old committed role, so the negative wait (expecting 503
`role_mismatch`) could observe the old role and time out.

Timing dependence was shown by identical product source on both
heads: Iw CI 42925034990 finished 24 of 25 jobs successful with
Compose job 130209254438 failing step 8, printing
`stage=wrong-role operation=await-readiness reason=timeout` (both
waits shared that label; the actual timed-out wait and the
historical root cause remained open). Report-only Sw CI
42928101256 completed all 25 workflow jobs successfully: CodeQL
42928101264 passed, the 20 strict named/app checks and the ten
PostgreSQL child checks succeeded, and Compose job 130219627297
passed step 8 (wrong-role stage, then unreadable-secret, recovery,
fixture OK, whole smoke OK; ROOT ac6dd7 / 8a5165; GitHub confirmed
main and Sw head, ROOT 98dc7a). Iw supply-chain evidence removed the
ten targeted findings at the exact installed versions, and artifact
13814649954 independently reproduced the W package result (ROOT
6ec2d3). The four backend SQLite High findings and the private
WHOLE/LOCAL6 qualifications remain separate work.

## Fix (tools/compose/control_readiness.py)

- Commit boundary: the role switch
  `REVOKE "slaif_control" FROM "slaif_control_login"; GRANT
  "slaif_reviewer" TO "slaif_control_login"` is now its own atomic
  psql request and commits before any session is terminated
  (marked by a source comment).
- `pg_terminate_backend` runs as a separate checked database request
  after commit, preserving the original exact fixture login (psql
  with `-v ON_ERROR_STOP=1 -U postgres -d slaif`) and the exact PID
  filter `WHERE usename = 'slaif_control_login' AND pid <>
  pg_backend_pid()`.
- Distinct fixed allowlisted operation labels replace the shared
  `await-readiness` mark in the wrong-role stage:
  `await-role-mismatch` (negative wait, `ROLE_MISMATCH`) and
  `await-restored-ready` (positive wait, ready `None`); the
  separate terminate request is marked `terminate-sessions`. All
  labels are added to `DIAGNOSTIC_OPERATIONS`, so a timeout
  diagnostic now names the actual wait.
- Preserved: expected 503 + `role_mismatch` reason, liveness and
  edge unavailability during the wrong-role state, ready recovery
  on the live service after role restoration, the existing time
  bounds, all other readiness stages and cleanup, and the
  diagnostic allowlist (no credentials, raw command output, or
  response bodies in the diagnostic).

## Tests (tests/packaging/test_compose_policy.py) — exact predicates

- New `test_control_fixture_role_switch_commits_before_terminate`:
  AST-scans every single-string `_psql` call in the fixture and
  asserts exactly one statement contains `pg_terminate_backend`;
  that statement contains neither `REVOKE` nor `GRANT` (separate
  request); it retains the exact PID-filter clause; and the atomic
  switch statement (one string containing both
  `REVOKE "slaif_control" FROM "slaif_control_login"` and
  `GRANT "slaif_reviewer" TO "slaif_control_login"`) is positioned
  before the terminate statement in source order.
- The existing diagnostics test now binds each wrong-role mark to
  the next `_wait_readiness` call via the literal two-line source
  sequences (the `ROLE_MISMATCH` and the `None` variants), so a
  label swap fails.
- New `test_control_fixture_wrong_role_waits_are_distinct_and_allowlisted`:
  both labels are members of `DIAGNOSTIC_OPERATIONS`; both mark
  literals appear in the source; `failure_diagnostic` emits the
  exact expected strings and they are distinct.

## Commands and results

- `uv run --frozen ruff check` (both changed files): All checks
  passed (native 0); `uv run --frozen ruff format --check` (both
  changed files): 2 files already formatted (native 0). Run from
  the execution tree, so the pinned interpreter/venv applied.
- packaging suite, first bare run (call 0a6110): 74 tests OK
  (native 0), but the exported PATH put the original checkout's
  venv first because `$PWD` was expanded before `cd`; the
  interpreter was Python 3.13.14, not the pinned 3.13.18. The
  product code under test was the worktree (path-derived via
  `__file__`); the interpreter was not pinned.
- packaging suite, corrected bare run: `cd` into the execution
  worktree first, then export the execution venv and pinned Node
  PATH; identities recorded: python
  `/home/janezp/codex-work/slaif-agent-site-083-8-j/.venv/bin/python`
  (Python 3.13.18), node
  `/tmp/oap-083-9-a/verify/node-v24.22.1-linux-x64/bin/node`
  (v24.22.1); 74 tests in 7.078s OK (native 0) — the credited
  result. 74 = 72 pre-existing + 2 new. An intermediate invocation
  failed on an invalid `node -V` flag before the suite launched; no
  suite run was consumed.
- All checks ran at pre-commit WIP source byte-equivalent to Ix;
  no clean-Ix rerun.

## Scope (measured on the worktree before commit, vs main 40cd)

- 41 source paths (the 39 W-footprint paths plus the two files,
  both previously unchanged from main): 6317 default / 6313
  minimal gross (HARD 6320). X delta +90/+90 (MAX 90):
  `tools/compose/control_readiness.py` 11/3 and
  `tests/packaging/test_compose_policy.py` 76/0.
- Four-file compose family unchanged at 3599 vs Sg
  `89ab5ec85273ebad10f9c6963b98811cdf992c54`; D18 five-doc
  footprint unchanged at 320/320 vs D18
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`.
- Ix committed exactly 4 paths (two source + exact order bytes +
  active), sole parent Sw; pushed 38bb5e0..fd5ad9d (native 0);
  GitHub head/parent/paths/decoded bytes verified equal to the
  worktree.

## CI at Ix (current, dated)

- Initial observation 2026-11-11T00:33:18.026029Z: 24 check-runs
  (4 success, 18 in_progress, 2 queued); no failures at that
  time.
- Terminal state observed 2026-11-11T00:49:45.600644Z (gh
  native 0): runs 42932147342 (ci.yml) and 42932147332
  (codeql.yml) both completed/success; 30 check-runs = 30
  success (20 strict named/app checks + 10 PostgreSQL child
  checks). Compose job 130233275443 passed step 8; its safe log
  shows the wrong-role stage at 00:45:33.531Z, then
  unreadable-secret at 00:45:35.933Z, recovery, control fixture
  OK at 00:46:28.964Z, and full smoke OK at 00:49:18.688Z (ROOT
  7a3764). Ix artifact 13816773014 audit reproduced the package
  evidence with the same 15 High findings, including the four
  backend SQLite findings (ROOT 60c7af). The report-only push
  was withheld until both runs were terminal because the
  workflows group by PR number and cancel in-progress runs on a
  new push; it is pushed after this terminal state.

## Process qualifications

- Pinned-Python erratum as recorded in the commands section: the
  first bare suite run used Python 3.13.14 via a PATH built before
  `cd`; the corrected run used the pinned 3.13.18 and is the
  credited result.
- W round: the first Iw push created the unintended remote alias
  ref `oap/083-8-j-execution`, corrected by explicit refspec; the
  alias is retained for strategic reconciliation (see the W
  report). All pushes in this round use the explicit refspec.
- Prior q/r/s/t/u/v process qualifications are preserved by
  reference to the immutable round transcripts, not recopied here.

## Limitations and remaining gates

- X is a source fix only; it is not a measured build or scan.
- Acceptance requires: the current final implementation AND this
  SELF report to pass the full 30 checks (20 strict + 10
  PostgreSQL children) on the current run; the complete six-image
  evidence artifact with the ten W-targeted finding IDs absent at
  any severity (including related IDs) and the four backend
  SQLite High findings retained as a separate visible assessment;
  separate private WHOLE/LOCAL6 qualification (INERT/NOT_RUN
  under X); and ROOT review and merge.
- Natural CI must exercise the real wrong-role scenario, both
  readiness waits, all later smoke stages, and the existing
  protection checks; the approved CI commands and predicates are
  the runtime evidence. Standalone CI evidence does not qualify
  private runtime.
- No cause-fixed, MVP, release, merge, or six-image-pass claim.

## Confirmations

- No secrets, credentials, or private artifact URLs in this report
  or in the diff; the diagnostic carries no credentials, raw
  command output, or response bodies.
- No production access; no new PR; no merge or auto-merge; no
  force/reset/rebase/stash.
- No change beyond the four Ix paths; no Docker, local browser, or
  image probes under X; no private WHOLE/LOCAL6 work; the
  unintended alias ref is preserved.

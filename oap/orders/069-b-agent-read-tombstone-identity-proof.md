# OAP Work Order — 069-b

## Objective

Continue Objective 069 on PR #60. Preserve the accepted 069-a Agent semantic
read implementation and close four narrow proof gaps: actual COW tombstone
non-resurrection, explicit effective production Agent pool identity, forged
workspace-session denial, and direct workspace-B resource-ID isolation. Do not
redesign the wrappers or reopen mutation scope. Do not merge.

## Verified starting state and review findings

- Numeric objective: `069`; round: `069-b`.
- Mode: `CONTINUE_SAME_PR`; amend only PR #60 on
  `oap/069-agent-semantic-reads`. Do not create another PR.
- Begin from verified remote 069-a report head
  `b563193b8313afd93fb286230ec6a86c30332808`; its only parent is the
  implementation head `ce45513f8f4d280a492e939563f8884f7539dca1` and it
  changes only `oap/reports/069-a-agent-semantic-cow-reads.md`.
- PR #60 remains open, non-draft, mergeable, based on merged Objective 068 main
  `b6946d84b72b44f15548235e3936d4e4202c587e`; reconcile live GitHub before
  editing.
- 069-a's implementation is genuine and retained: all seven public GET routes
  use one capability-workspace `asyncpg_cow_session`; seven narrow
  owner-defined wrappers read foundation COW views; generic Agent app content
  service fallback is removed; exact grants and the main POST→GET/fallback/
  update/isolation/residue path pass real PostgreSQL.
- Gap 1: the 069-a report marks “tombstone/filter behavior” passed, but the test
  only proves status filters and an overlay UPDATE. No canonical row is deleted
  in a workspace and then queried, so non-resurrection from canonical fallback
  is unproved.
- Gap 2: production `AgentDatabase._initialize` enforces expected login and
  membership, but the public-read integration does not explicitly inspect the
  actual app-owned pool's `session_user`, `current_user`, and reachable
  authority roles while servicing this runtime.
- Gap 3: direct wrapper tests cover missing context and a real workspace with a
  wrong site, but not a forged/random workspace UUID carried as
  `app.session_id`.
- Gap 4: same-site workspace collision is proved by list labels, but the B-only
  overlay UUID is discarded in the fixture; workspace A never performs a
  direct GET for that exact B resource ID.

## Bounded scope

Prefer integration evidence only. Change production code or migration SQL only
if the new proof exposes a real defect, and then make the smallest same-contract
correction. Commit this exact order and exact `oap/active` bytes unchanged with
the implementation/evidence commit.

## Explicit non-goals

- No new route, wrapper, scope, mutation, update/delete HTTP API, database
  authority, generic function grant, lifecycle/reviewer path, or COW redesign.
- No change to Agent authentication, idempotency/audit mutation semantics,
  canonical publication, Editor/Puck, media upload, rendering, browser worker,
  freeze/review, accept/discard, or inert objectives 070–078.
- No private foundation patch, direct Agent table privilege, test-only runtime
  credential, or broad role membership.
- Do not edit activated 069-a order/report or any historical OAP artifact.
- No extra PR and no merge.

## Requirements and observable acceptance

### 1. Real tombstone / canonical non-resurrection

- Seed a distinct canonical semantic row (content type is sufficient) in the
  owner-visible `*_base` relation.
- In workspace A, use the existing trusted real-COW fixture/session to issue a
  semantic DELETE through the foundation-managed view, producing a genuine
  workspace tombstone before public reads.
- Through workspace A's public capability-authenticated Agent API, prove both
  list exclusion and exact-resource GET `RESOURCE_NOT_FOUND` for that row.
- Through owner/base inspection, prove the canonical row still exists and is
  unchanged.
- Through workspace B's public Agent API, prove the unchanged canonical row is
  still visible as fallback. This distinguishes workspace-local tombstone from
  global deletion or status filtering.
- Record operation state after fixture setup, then prove the GETs add no COW
  operation, idempotency row, or mutation audit row.

### 2. Explicit production Agent pool identity

- During the production `create_agent_app` lifespan used by the public GET
  proof, inspect the exact app-owned pool and assert:
  - expected database;
  - `session_user` and `current_user` equal the fixture's real Agent login
    corresponding to production `slaif_agent_login`;
  - among product authority roles, the login reaches exactly
    `slaif_agent_runtime` and not owner, Control, Editor, Render, reviewer,
    bootstrap, or other service authority.
- Tie this evidence to the same pool used by `execute_agent_read`; do not use a
  separately SET ROLE test pool as the production-identity proof.

### 3. Forged context and direct B-resource isolation

- Retain the B-only overlay row UUID instead of discarding it.
- Workspace A public exact-resource GET for that UUID must return stable
  non-leaking 404; workspace B exact-resource GET must return its B-only
  overlay value. Keep the deliberately colliding semantic key.
- Invoke a read wrapper under the least-privileged Agent role with a random/
  nonexistent `app.session_id` in an otherwise valid foundation COW session;
  prove fail-closed denial and no residue. Preserve existing missing-context
  and wrong-site-context denials.

### 4. Preserve accepted contract

- All seven routes, wrapper ownership/search path/grants, overlay update,
  canonical fallback across type/page/composition/media, site isolation,
  scopes, malformed/revoked/expired/inactive outcomes, cancellation, success/
  failure cleanup, and 067 mutation regressions remain green.
- No Agent generic function, base/change table, Control/audit table, reviewer,
  DDL, or raw-SQL authority is added.
- Correct the overclaim only through new 069-b evidence/report; do not mutate
  the immutable 069-a report.

## Verification

At minimum run and report exact results for:

- the focused 069 real-PostgreSQL/public-HTTP tombstone/identity/isolation test;
- the complete Agent mutation/read integration file;
- the complete PostgreSQL integration suite;
- Ruff, formatter, mypy, unit/repository, migration-head/downgrade/privilege,
  repository policy/renumber, packaging, docs, process, Node, license,
  `git diff --check`, and repository-required Compose gates in proportion to
  any changed paths;
- all fresh implementation-head GitHub checks, including PostgreSQL 14–18,
  Compose/edge, supply chain, Node, analysis, docs, dependency review, and
  CodeQL, with none missing/pending/failed/cancelled before report publication.

Mark the direct system-Python invocation issue and any reused evidence
honestly; use the repository's frozen runner for valid process checks.

## Documentation

No durable doc change is required if production behavior is unchanged. If a
real defect is found, update only the affected Agent read/role wording. The
069-b report must explicitly distinguish newly proved tombstone behavior from
069-a's prior status-filter/update evidence.

## Security and local authority

Use only the disposable local VM, local PostgreSQL/containers, and normal
GitHub workflow. No production credentials, systems, data, merge, or release
authority. Preserve all least-privilege and site/workspace fail-closed rules.

## GitHub workflow

1. Reconcile PR #60 and exact 069-a report head.
2. Implement only this same-PR evidence continuation.
3. Commit/push evidence/any necessary narrow fix plus this exact order and
   active bytes.
4. Wait for every fresh implementation-head check to succeed.
5. Publish one immutable report-only child commit and push it.
6. Do not merge. Signal exact FIFO `OK` only after remote report verification.

## Required report

Publish exactly:

`oap/reports/069-b-agent-read-tombstone-identity-proof.md`

The report must state `COMPLETE` or `BLOCKED`, `RESULT=OK` or
`RESULT=BLOCKED`, PR/branch/base, implementation SHA, `Report publication
commit: SELF`, exact parent, files/diff, whether production code changed,
canonical/tombstone IDs and A/B/owner observations, exact app-pool identity and
role set, B-overlay UUID direct GET outcomes, forged/missing/wrong-site context
outcomes, before/after operation/idempotency/audit/context cleanup evidence,
all commands/results/checks, intermediate failures, scope/non-goals, and no
merge/extra PR.

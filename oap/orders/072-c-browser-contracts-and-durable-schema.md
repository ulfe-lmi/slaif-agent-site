# OAP Work Order — 072-c

## Objective

Continue Objective 072 on the existing PR #66. Implement one bounded,
independently verifiable foundation slice only: replace the browser-contract
metadata scaffold with versioned typed preview-run contracts and add migration
035 with durable capability browser limits, run/idempotency/lease/artifact
metadata/audit tables, exact Agent-owned functions/grants, and real PostgreSQL
proof. Do not implement Agent HTTP routes, credential signing, dispatcher,
Playwright, artifact files, or browser execution in this round. Do not merge.

## Verified state and correlation

- Numeric objective: `072`; round: `072-c`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #66 on
  `oap/072-browser-worker-real-playwright`. Create no new PR.
- Begin from verified remote 072-b report head
  `3494447ac690fe37f877204153e54f84d0569d83`; its sole parent is
  `9d601c3ce393b39371b68e663ef10ef446fa7884` and its sole changed path
  is `oap/reports/072-b-durable-browser-run-control-plane.md`.
- Remote main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`; PR #66 is open and
  mergeable. Reconcile live GitHub before mutation.
- 072-a and 072-b are truthful PARTIAL transcript rounds with no substantive
  implementation. The 072-b report append-only corrected 072-a's short SHA.
- Current contracts remain metadata-only; migration head is 034; capability
  has no browser limits; no browser-run/artifact/idempotency/audit state or
  browser-specific Agent grants exist.

## Bounded scope and explicit deferrals

Change only:

- `packages/browser-tool-contracts` source/tests/package build output;
- shared Python browser contract models or generated schema/parity tests;
- migration 035;
- database privilege application/validation;
- capability authentication/context fields needed to read browser limits;
- focused unit/real-PostgreSQL/migration/privilege tests; and
- exact database/contract/security/testing documentation.

Do not change Agent HTTP routes, fake browser router, Agent app wiring, worker
source/image/package, Playwright dependency, Compose worker networks/volumes,
Web/Render preview tokens, secret initialization, artifact filesystem, public
API docs that claim routes, or any browser execution. Those remain later
same-PR rounds. No dependency or lockfile change is authorized.

Do not edit migrations 006 through 034, activated 072-a/072-b orders, or
published reports. Add only migration 035 with one linear head. No source
crawling, review, publication, public artifacts, worker DB, extra PR, or merge.

## 1. Versioned browser contracts

Replace the metadata-only contract with immutable versioned TypeScript/Python
facts for:

- first runtime target enum limited to approved Chromium desktop/tablet/mobile
  target names; caller input contains a name only, never viewport/device data;
- curated evidence enum for screenshot, accessibility summary,
  structure/headings/links/media/overflow, console summary, and failed-request
  summary;
- external create request containing only normalized route, one target, and a
  unique bounded evidence list;
- run state enum QUEUED, RUNNING, COMPLETED, FAILED, TIMED_OUT, CANCELLED;
- public run status/result and private artifact metadata schemas;
- internal run specification, lease, and completion metadata schemas for later
  routes/worker; and
- one contract version and deterministic canonical serialization/request digest.

All schemas are extra-forbid and bounded. Reject unknown version/field/state,
duplicate evidence, unsupported target, absolute/scheme-relative URL, origin,
authority, site/workspace/capability/run/artifact IDs in external create input,
viewport dimensions, headers/cookies, JavaScript/browser commands, empty or
oversized route, traversal, query credential, and fragment. Add exact
cross-language parity tests so Python and TypeScript facts cannot drift.

## 2. Migration 035 durable schema

Add conservative non-null browser limits to capability records, with explicit
checks and defaults for total runs, concurrent runs, screenshots, artifact
bytes, route/evidence counts, duration, attempts, and allowed targets.

Add the minimum normalized tables:

- browser idempotency/run record bound immutably to capability, site,
  workspace, delegator, route, target, request digest, reserved quotas, state,
  attempts/lease, summary/error, created/started/completed/expiry timestamps;
- browser artifact metadata bound to the exact run/site/workspace/capability,
  with type, MIME, SHA-256, size, target, route digest, created/expiry and
  visibility; no path, URL, or bytes; and
- append-only browser event/audit rows for enqueue, lease/attempt and terminal
  result/artifact registration, with immutable correlation and no delete/update
  authority for runtime.

Use UUID/FK/composite site-workspace-capability/run constraints, unique
idempotency and operation/run identities, state/terminal/lease/attempt/digest/
size/time/limit checks, deterministic indexes, and no audit cascade deletion.
Browser tables are Control/audit state, never COW content and never publication.

## 3. Exact owner-defined functions and grants

Implement narrow fixed-search-path functions for `slaif_agent_runtime`:

1. begin/replay/mismatch: under the workspace shared advisory transaction lock,
   recheck active unexpired capability/workspace/site, exact
   `preview:inspect`, resource binding and server-supplied request facts;
   atomically reserve capability quotas and create one QUEUED run, idempotency
   and enqueue audit, or replay/mismatch/deny with no residue;
2. get one run and list artifact metadata only for the exact current
   capability/site/workspace and retention state, without mutation/audit;
3. claim one preview run with `FOR UPDATE SKIP LOCKED`, bounded lease/attempt and
   deterministic order for a future Agent-owned dispatcher;
4. renew/release/terminal completion and artifact metadata registration only for
   the exact lease/run and only after current authority recheck; terminal state
   is idempotent and invalid transition fails; and
5. bounded capability browser-limit read returned through existing capability
   authentication, not generic table access.

The future worker has no DB role. Revoke PUBLIC and all direct table/sequence/
function authority except exact Agent function execution. Explicitly deny
public/preview/Editor/Media/scheduler/reviewer/setup roles browser mutation and
Agent role generic Control/job/reviewer/setup/audit access. Extend bootstrap
privilege validation to prove exact ownership, search path, signatures, grants,
direct-relation denials, and absence of PUBLIC defaults.

## 4. Trusted capability context

Extend `AgentCapabilityContext` and authentication records with an immutable,
validated browser-limits model and allowed-target set from database output.
Malformed/null/out-of-policy stored limits fail authentication unavailable or
deny safely; callers cannot override them. Preserve every existing capability
field and Agent route behavior.

Do not expose internal quota counters, lease tokens, signing keys, SQL, roles,
or foreign IDs in capability discovery. Public route wiring remains unchanged
in this round.

## 5. Real PostgreSQL proof

Using real `slaif_agent_login`/`slaif_agent_runtime`, two sites, two workspaces
and multiple capabilities, prove:

- begin success, same-key/same-digest replay, mismatch, concurrent same-key
  serialization, exact one run/idempotency/audit and quota reservation;
- total/concurrent/screenshot/artifact/target/route/evidence quota denial with
  zero partial state and independent capability counters;
- missing `preview:inspect`, revoked/expired capability, inactive/expired/
  revoked workspace/site, wrong site/workspace/capability and forged server
  facts deny with no residue;
- deterministic freeze/revocation race waits on the shared workspace lock,
  rechecks after release and creates no run/audit/idempotency on denial;
- run/artifact reads isolate capabilities/workspaces/sites and random/foreign
  UUIDs are non-leaking absence;
- one claimant obtains a run, concurrent claim skips it, lease expiry permits
  bounded next attempt, max attempts terminate, invalid transitions/artifact
  metadata fail, valid completion is idempotent, and revoked authority prevents
  newly visible terminal artifacts;
- reads create no COW content operation or browser audit row; and
- exact identity/grant/direct DML/base/change/generic control/reviewer/setup/
  other-role denials and pool cleanup hold on success/failure/cancellation.

Owner may seed and inspect exact counts only; it cannot substitute for runtime
function execution. Unit/source tests alone are insufficient for these claims.

## Acceptance and verification

- Shared contracts are real, bounded, versioned and cross-language identical.
- Migration 035 is the sole new migration and supplies coherent durable limits,
  runs/idempotency/leases/artifact metadata/audit with strict constraints.
- Agent runtime can only use narrow browser functions and current capability
  context; browser worker remains DB-less and unchanged.
- Real PostgreSQL proves idempotency, quota, race, lease, transition, artifact
  metadata, isolation and privilege behavior.
- No public browser route or fake completion claim is added; numeric Objective
  072 remains PARTIAL after this foundation round.

Run focused contracts/models/migration/privilege tests; real PostgreSQL matrix;
full backend unit/repository/integration; CI-scope Ruff/format/Mypy/build/process;
complete Node gates; migration upgrade/downgrade and PostgreSQL 14–18; static
Compose worker-no-DB policy and clean Compose regression; Markdown/Mermaid;
supply-chain; and every fresh GitHub required check. Record every failure,
retry, skip, and not-run item honestly.

Update only contract/database/authorization/security/testing docs. Continue to
state that worker Chromium, artifact bytes, public routes, credential dispatch,
confinement and browser E2E are not implemented.

Commit/push the exact strategic 072-c order and active bytes unchanged on the
same PR, then bounded implementation/tests/docs. Publish exactly
`oap/reports/072-c-browser-contracts-and-durable-schema.md` as one report-only
child with `Report publication commit: SELF` and a literal 40-hex
implementation parent. The report should use `PARTIAL` for Objective 072 while
stating exact 072-c completion. Verify remote parent/path/head and signal exact
FIFO `OK`. Do not merge.

The report must state PR/base/branch/all SHAs; contract/schema/function/grant/
quota/idempotency/race/lease/isolation evidence; exact counts and roles;
worker-still-stub limitations; files/dependencies/migration/docs; every local/
CI result; no extra PR; and no merge.

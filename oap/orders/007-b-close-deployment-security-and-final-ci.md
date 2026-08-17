# OAP Work Order — 007-b

## Objective

Amend the existing objective `007` pull request to close the strategic review
findings in the default deployment skeleton:

1. use the truthful local deployment mode rather than `test` mode;
2. make every local PostgreSQL login's database/object authority exactly the
   authority inherited from its sole privilege role, with no direct grant,
   ownership, role-setting, expiry, or configuration drift;
3. apply a tested baseline Content Security Policy and emit exactly one safe
   request-ID response header through both supported edge contracts; and
4. do not send FIFO completion until every check on the final report-only head
   has actually completed successfully.

Keep PR `#10` open and amend it. Do not create a new PR or merge.

## GitHub objective state

- Numeric objective: `007`
- Execution round: `007-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#10`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/10>
- Required head branch: `oap/007-compose-edge-skeleton`
- Base branch: `main`
- Required PR title: `[OAP 007] Add one-command Compose and edge skeleton`
- Current remote PR head:
  `0ae98936e48310feeabb7920e500f1431bd7df3c`
- Previous implementation head:
  `94702b5420b15be0a63171d678c3de56f8a3a31f`
- Repository: `ulfe-lmi/slaif-agent-site`

## Current verified review state

The 007-a report commit has the correct first parent and changes only the
immutable report. The implementation head passed its full 19-check set and the
Compose smoke. The coding agent nevertheless signaled before checks on the
report-only head completed, contrary to the activated order.

Authoritative final-head results are now:

```text
FAIL  Python 3.13 quality/package
FAIL  Foundation PostgreSQL 15
FAIL  Foundation PostgreSQL 18
FAIL  CodeQL JavaScript/TypeScript
SKIP  CodeQL aggregate because one language failed
PASS  the other 14 checks, including Compose/edge packaging
```

Every failure occurred during GitHub runner action download and shows HTTP
429 and/or 503 from `codeload.github.com`; no repository step ran in those
failed jobs and no open code-scanning alert exists. Do not change action pins,
reduce the matrix, or weaken policy for this external condition. The new
continuation/report head will run fresh checks; use permitted GitHub rerun on
that same head if a transient setup download fails again.

Strategic source review found these additional defects:

- `compose.yaml` sets long-running backend `SLAIF_MODE=test`; the default local
  product stack must use `development`. Test-only behavior must never become
  the shipped demo default as future fixtures/features are added.
- `local_login_violations(...)` proves login flags and membership edges but
  does not detect a direct database/schema/relation/sequence/function grant,
  object ownership, per-role GUC, validity, or connection-limit drift. A login
  could therefore exceed its sole privilege role while the current verifier
  reports safe.
- Database `CONNECT` currently remains available through PostgreSQL's default
  `PUBLIC` grant. The dedicated product database should admit product
  principals through their exact privilege roles, not a database-wide public
  default.
- NGINX adds `X-Request-ID` even though backend correlation middleware already
  returns it, producing possible duplicate response fields. Apache has the
  same upstream/set ambiguity. The edge contract must return exactly one
  bounded ID.
- Neither edge adapter emits the architecture-required
  `Content-Security-Policy` header.

## Scope

Change only the existing 007-a path families needed for Compose mode, role/
login provisioning and validation, NGINX/Apache headers, tests/policy, durable
docs, and the new OAP order/report. Add no dependency, service, image, network,
volume, port, product route, table/migration, browser feature, or unrelated
refactor. Preserve the accepted `006_001` readiness state semantics.

## Requirements

### A. Truthful Compose mode

- Set the default long-running backend service and worker mode to
  `development`, with local HTTP/public URL settings appropriate to the
  loopback demo.
- Reserve `test` mode for tests/explicit test overlays. Add policy and live
  inspection proving no default long-running service uses test mode and no
  production mode is falsely claimed.
- Keep production fail-closed rules and documentation unchanged in meaning.

### B. Exact local-login authority

Strengthen fixed local login provisioning/reconciliation and
`local_login_violations(...)` so each login has exactly the effective
authority of its sole privilege role and nothing else.

At minimum:

- revoke `CONNECT` and `TEMPORARY` on the dedicated product database from
  `PUBLIC`;
- grant `CONNECT` to the exact product privilege roles that have a service or
  bootstrap login; grant database `CREATE` only to `slaif_owner`; grant
  `TEMPORARY` to none unless a separately reviewed future need exists;
- reconcile/remove direct database, product/foundation schema, relation,
  sequence, and function grants to each fixed login principal; expected access
  must arrive only through its sole role membership;
- inspect ACL grantees as well as effective privileges so a redundant direct
  grant is not hidden by matching inherited authority;
- detect any product/foundation schema/relation/sequence/routine/database
  ownership by a login principal;
- reconcile and verify connection limit, password-validity state, and per-role
  GUC/config state to one documented safe local contract; no login may inject a
  search path or other role setting;
- retain the exact fixed login names, one non-admin membership, password-file
  handling, non-superuser/non-createdb/non-createrole/non-replication/
  non-bypass-RLS attributes, and incoming/outgoing membership cleanup;
- independently authenticate each login after reconciliation and prove an
  unrelated valid PostgreSQL login without a product role cannot connect to
  the dedicated database after `PUBLIC CONNECT` revocation;
- fail bootstrap closed on any unrepaired/unknown direct authority or ownership
  rather than broadening a role.

Add negative tests for direct database/schema/table/view/sequence/function
grants, direct/default privileges where applicable, owned product object,
unsafe `rolconfig`, connection limit, validity drift, combined membership,
admin option, delegation, and unrelated-login connection denial. Demonstrate
repair for safely reconcilable grants/settings and deterministic failure for
ownership that must not be reassigned silently.

Do not expose password values in SQL/log/test/report output.

### C. CSP and single request correlation header

Apply an explicit baseline CSP through NGINX and the Apache reference. It must
cover at least:

```text
base-uri
object-src
frame-ancestors
form-action
default-src or explicit fetch/script/style/image/connect policy
```

Use no external origin, wildcard, `unsafe-eval`, report endpoint, hosted
service, or telemetry. Do not add `unsafe-inline` merely to silence a test. If
the minimal Next runtime needs a narrower temporary policy choice, preserve
the server-rendered page/health behavior, document the exact limitation, and
keep executable origins self-hosted.

For every proxied Web/API success and 404 response:

- hide/remove an upstream `X-Request-ID` before setting the authoritative edge
  response field, or otherwise prove there is exactly one field;
- generate/pass one bounded safe request ID to the upstream;
- return exactly that one value to the client;
- reject no legitimate request merely because a caller supplied its own ID;
  the trusted edge may replace it consistently;
- ensure Apache's reference behavior is semantically equivalent.

Extend runtime curl/header tests to count header occurrences, validate the
value shape/length, verify CSP appears exactly once with required directives,
verify forbidden directives/origins are absent, and cover landing page,
routed backend health, and an unknown 404. Extend static equivalence tests for
both adapters.

### D. Preserve the accepted deployment boundary

Keep all 007-a positive evidence green:

- exact 15-service inventory and sole loopback 8080 publication;
- secret directory GID hardening and unauthorized-UID denial;
- fixed mounts/networks/users/capabilities/read-only/no-new-privileges policy;
- `EMPTY_SAFE safe=true` bootstrap and fail-closed negative startup;
- Next/browser health-only surfaces;
- digest-pinned images and frozen dependency locks;
- NGINX/Apache syntax, clean/restart/cleanup, and no secret in image/config/
  environment/history/log/Git;
- no owner/provisioner/service DSN mounted into long-running processes.

Do not change the secret-directory traversal fix or reopen its resolved CodeQL
finding.

### E. Final-head protocol and CI

- Preserve the 007-a order/report bytes exactly.
- Commit the 007-b order/active pointer with the implementation, push to PR
  `#10`, and obtain a fully successful implementation-head check set.
- Publish the immutable 007-b report-only `SELF` commit as the last repository
  mutation for the round.
- Then wait for **every check on that exact report-containing head**. If a job
  is pending, keep waiting. If an external 429/503 setup failure occurs, rerun
  failed jobs on the same head and wait. If a repository check fails, repair it
  under a later strategic continuation rather than signaling success.
- Send FIFO `OK` only when all order-required checks on the report head are
  completed `SUCCESS`, none is skipped/neutral/pending/failed/cancelled, and
  open CodeQL alerts are zero.

The report cannot embed its own later check results; record the pre-publication
implementation state truthfully and state that post-publication state will be
verified before signaling. GitHub remains the authoritative proof.

## Non-goals

- No new PR, force push/history rewrite, merge, auto-merge, workflow/action-pin
  workaround, reduced matrix, flaky-test exemption, release, tag, deployment,
  issue, or GitHub setting change.
- No action on PR `#5` or `#7`.
- No product authentication/site/workspace/content/media/browser/review/
  publication behavior, migration, pool, service DSN mount, Playwright,
  Tailwind/Puck/UI expansion, production TLS, or credential rotation feature.
- No additional dependency, base-image update, service/network/volume/port,
  broad grant, PUBLIC database access, or placeholder success behavior.

## Acceptance criteria

1. PR `#10` remains the unique objective-007 PR and is amended with 007-b; no
   new PR, merge, auto-merge, or prior transcript mutation occurs.
2. Default Compose uses `development`, never `test`/false production, for all
   current long-running backend processes; test mode remains test-only.
3. `PUBLIC` lacks database `CONNECT`/`TEMPORARY`; exact privilege roles receive
   only required database authority, and an unrelated login cannot connect.
4. Each fixed login has exactly one non-admin role membership, no direct ACL,
   no product/foundation ownership, no unsafe role setting/expiry/limit drift,
   and effective authority equal to that sole role. Negative drift is repaired
   or fails closed as specified.
5. NGINX and Apache emit one CSP and exactly one safe request ID on Web/API/404
   responses; required CSP directives exist, forbidden origins/directives are
   absent, and current page/health behavior remains functional.
6. The complete clean/restart/failure Compose smoke, role/secret/topology
   inspection, Python/PG14–18/Node/docs/package/edge tests, and all prior 007
   invariants pass without skips.
7. The earlier final-head 429/503 failures are reported accurately as external
   setup failures and no policy/pin was weakened.
8. Every check on the final 007-b report-only head is successful before FIFO
   `OK`; zero check is pending/skipped/neutral/failed/cancelled and zero CodeQL
   alert remains open.
9. `oap/active` is `007-b`, both 007 rounds correlate uniquely, final report
   commit changes only the 007-b report and has its literal implementation head
   as first parent.

## Verification required

Run the complete 007-a local verification again. Additionally report:

- rendered and live default `SLAIF_MODE` inventory;
- database ACL/default ACL/owner/role-config/validity/connection-limit and
  exact login-vs-role effective privilege comparison;
- direct-grant/ownership/config/connection negative fixtures and unrelated
  login connection denial;
- raw response headers for page/API/404 reduced to non-secret facts: request-ID
  count/format/equality and CSP count/directive assertions;
- NGINX/Apache syntax and static equivalence after changes;
- current implementation-head checks and the final report-head wait outcome in
  GitHub, without editing the report after publication;
- exact diff scope, protected/prior artifact hashes, report parent/delta, and
  synchronized clean worktree.

No required Compose/role/header/check test may be skipped.

## Safety / security constraints

Use only fake disposable databases, logins, secrets, containers, networks, and
volumes. Never print a generated secret. Resolve destructive Compose targets
exactly and never prune broadly. Fail closed on unknown ACL/ownership/header/
mode/check state. Do not trade a broader grant, weaker CSP, workflow change, or
test-mode deployment for expedience.

## Local execution capability

Routine PostgreSQL ACL/login setup, Docker/Compose, header inspection,
NGINX/Apache, package/test setup, and GitHub CI diagnosis/reruns belong to the
coding agent in its disposable VM. Do not transfer them to the human or
strategic model.

## GitHub workflow

Fetch and verify open PR `#10`, check out its existing
`oap/007-compose-edge-skeleton` branch, and amend that same PR. Never create a
second objective PR. Do not merge. Do not signal until the final report-head
check condition above is actually true.

## Required report

Atomically publish exactly:

```text
oap/reports/007-b-close-deployment-security-and-final-ci.md
```

Use protocol 1.2 in full. Include the strategic findings, exact fixes and
negative evidence, preserved 007-a topology, dependency/scope state, previous
external CI failures, implementation-head checks, no-secret/no-merge
confirmations, literal implementation head, and
`Report publication commit: SELF`. After pushing it, perform no repository
mutation; wait/rerun only the final-head GitHub checks and send FIFO `OK` only
after they are all successful.

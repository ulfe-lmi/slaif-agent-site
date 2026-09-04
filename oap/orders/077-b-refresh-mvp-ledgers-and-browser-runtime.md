# OAP Work Order — 077-b

## Exceptional human-ordered prerequisite correction

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; no new PR and no
merge. Required starting remote report head:
`7ff0085c48082549fc2b3e58a0fc408c7e7e6afa`, whose sole parent is reported
077-a implementation head `9cad25f9d3d392cbd913e434bc9a616606c548d1`.
Remote `main` remains the accepted Objective 076 merge
`067676314e0d9664d40cb8514ea549b966a4eb2d`.

This order exists because the human supplied new mandatory control-state and
security-maintenance prerequisites after 077-a had already been immutably
activated. It supersedes 077-a's then-current instruction to defer GitHub issue
#67. Preserve 077-a implementation and report history, but do not claim that
077-a or Objective 077 is accepted: report-head CI was still running at first
strategic review, later 077 information-architecture scope remains, and
separate concrete page-review defects are reserved for a subsequent order.

Complete exactly two related prerequisites before normal Objective 077 work
resumes: correct stale current-state MVP ledgers for merged 073–076 outcomes,
and qualify the now-available fixed Chrome-for-Testing Stable runtime so the
expired browser-worker exception can be removed rather than extended.

## 1. Correct current-state MVP ledgers without rewriting history

Update only the current implementation/status portions of
`oap/MVP-PROGRESS.md` and `oap/MVP-CONTRACT-AUDIT.md`. Retain earlier audit
documents, immutable OAP orders/reports, historical caveats, and the binary
`CONTRACTUAL MVP NOT COMPLETE` verdict.

Use GitHub/merged evidence, not report confidence alone:

- Objective 073 / PR #69 merged as `74d9c18...`: truthful audit and roadmap
  repair; no product-completion claim.
- Objective 074 / PR #70 merged as
  `ef456e63abadddfc7d90794c03be3a63677c87f9`: real public human Agent
  workspace/capability issuance, policy/CSRF/site authority, idempotency,
  audit, revoke and Control+Agent restart proof.
- Objective 075 / PR #71 merged as
  `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`: complete editable-domain
  substrate and validators, query contract, fixed locale/navigation/redirect
  data integrity, production COW upgrade and Agent binding.
- Objective 076 / PR #72 merged as
  `067676314e0d9664d40cb8514ea549b966a4eb2d`: public capability-bound Agent
  model/type/field/item/translation/relation/collection-view REST semantics,
  strict scopes/resources/quotas/idempotency/audit/COW/concurrency, generated
  deterministic Agent OpenAPI, public NGINX/restart evidence, and PG14–18 CI.

Required ledger corrections:

1. Move 074, 075 and 076 out of the inert/planned or stale
   `SCAFFOLD/PARTIAL/NOT IMPLEMENTED` classifications for the exact contracts
   those merged objectives prove. Credit only their actual production-boundary
   evidence; do not inflate adjacent pages/composition/media/MCP/lifecycle work.
2. Update the authoritative current-main baseline and audit date to the exact
   Objective 076 merge. Preserve the historical 065–072 evidence table and add
   explicit 073–076 merged evidence instead of erasing it.
3. Record Objective 077 accurately as active on PR #74 and unmerged. On current
   `main`, the broader page/navigation/redirect/Render contract remains
   `PARTIAL`; the unmerged 077-a page slice is evidence under strategic review,
   not merged product truth.
4. Correct the OpenAPI row: Objective 076 now provides the canonical generated
   Agent OpenAPI and bidirectional production-handler/route-policy/schema drift
   checks through the public path. Preserve that MCP parity remains Objective
   080 and is not implied by OpenAPI completion.
5. Correct the mutation/audit row to credit complete 076 model/content/view/
   relation coverage while retaining `PARTIAL` for the broader 077–079 mutation
   surface. Correct the freeze row's obsolete statement that Agent mutations
   lack the shared lifecycle lock, while retaining that immutable freeze/review
   snapshot is not implemented until 082.
6. Replace the stale “remaining sequence” presentation with a clear completed
   073→076 prefix and active 077→091 remainder. Preserve the architecture-first,
   intended-interface, anti-bypass, one-objective/one-PR and Objective-091-only
   final-MVP gate.
7. Correct the old release-claim conflict row to acknowledge Objective 073's
   truthful interim claims while retaining final release/MVP proof for 091.
   Never mark the overall MVP complete or call the repository production-ready.

Every changed classification must cite the exact merged objective/PR evidence
that supports it. A route/table/file alone is not evidence.

## 2. Qualify Chrome-for-Testing Stable 152.0.7977.82

Official Chrome-for-Testing last-known-good metadata fetched on 2026-09-04
reported timestamp `2026-09-03T22:22:57.696Z`, Stable version
`152.0.7977.82`, revision `1669021`, and linux64 archive:

`https://storage.googleapis.com/chrome-for-testing-public/152.0.7977.82/linux64/chrome-linux64.zip`

Independently refetch Google's official last-known-good and exact-version/
known-good metadata. Require the same Stable version, revision, platform, and
URL before use. Download the exact archive in the disposable environment,
calculate and record its SHA-256, verify the archive/extraction shape and actual
`Google Chrome for Testing 152.0.7977.82` executable version, then replace every
current runtime/policy/test/documentation pin of obsolete `152.0.7977.64`.
Keep the existing exact Playwright base-image digest and browser confinement
unless qualification proves a necessary compatible change; do not make an
unrelated Playwright/Node/base-image upgrade.

At minimum reconcile:

- `services/browser-worker/Dockerfile` URL, archive hash, version assertion,
  expected-version environment and comments;
- `supply-chain/policy.json` plus exact enforcement in
  `tools/supply_chain/policy.py`;
- Compose/packaging/runtime assertions and current configuration defaults;
- `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`, `docs/LICENSE_POLICY.md`, and
  `docs/SUPPLY_CHAIN.md` current statements;
- supply-chain/packaging tests and current generated evidence contracts.

Historical OAP orders/reports and the old candidate evidence remain immutable.
Preserve the prior `152.0.7977.64` qualification as historical evidence in
`supply-chain/browser-worker-critical-matrix.json`; append or otherwise clearly
record the new `.82` candidate, official metadata, archive hash, scanner/tool/
database identity, image digest and result. Do not rewrite history merely to
make a repository-wide text search empty.

Build the actual final browser-worker image and run a fresh full vulnerability
scan with a current successful Grype database update. Reconcile scan PURLs and
the project-owned six-image evidence, not a standalone extracted binary only.
Then:

- if all 41 exception-referenced `.64` findings are absent and there are zero
  unexcepted release-policy Critical findings, remove those exact expired
  entries from `supply-chain/vulnerability-exceptions.json` (retain the valid
  schema with an empty list if no other exceptions exist), update tests/docs,
  and prove the normal gate passes without an exception;
- if any Critical finding remains or a new Critical appears, do not extend the
  expired exception, invent a new exception, lower severity, alter PURLs,
  suppress evidence, pin stale scanner data, or weaken the gate. Report the
  exact finding/image/package/version/fixed-in/scanner database as a genuine
  blocker for human risk decision.

Run the browser-worker Node/unit/security tests, archive extraction and OCI
policy tests, deterministic/reproducible image checks, all stable browser
projects exercised by the clean Compose edge acceptance, fresh full
`tools/supply_chain/run.sh` evidence and checksum validation, repository policy,
Markdown and relevant Python tests. Prove the runtime executable version,
readiness expectation, downloaded digest, SBOM PURL/version and policy all agree.

GitHub issue #67 remains the historical exception record. Do not close it from
the coding role and do not claim closure before the fixed commit is merged into
remote `main`. In the report provide exact issue-ready evidence and recommend
strategic closure only after the final containing PR is accepted/merged and
remote main is verified. Do not edit the issue merely to hide an expired state.

## Scope and known 077-a review state

This prerequisite round must not implement more page/navigation/redirect/
locale/Render behavior. Preserve the 077-a page implementation unchanged except
for unavoidable pin-driven generated evidence. Strategic review has already
identified separate product defects—private `content.page_changes` dependence,
implicit locale creation without `locale:configure`, conditional PATCH scope/
OpenAPI mismatch, and missing competing move/route-update race proof. They are
not waived and will receive the next bounded 077 production order after this
prerequisite round; do not silently repair or claim them here.

No 078+ behavior, MCP, media feature, freeze/review/promotion/source/sweep,
dependency expansion, general refactor, architecture edit, production/release
claim, or production secret/system/data access. Do not reopen Objective 076.
Routine Docker/browser/scanner/package work belongs to the disposable coding
environment; passwordless sudo is available. No check may be weakened or
skipped as success.

## GitHub workflow and immutable report

Fetch GitHub and verify the named open PR/head. Check out/update only its
existing branch; commit the exact activated order and `oap/active` unchanged
with the bounded implementation, push to PR #74, and create no PR. Never merge
or enable auto-merge. Inspect and repair in-scope current-head CI failures.

Publish exactly
`oap/reports/077-b-refresh-mvp-ledgers-and-browser-runtime.md` as the final
report-only child of a literal 40-hex implementation SHA, with `Report
publication commit: SELF`, and push before signaling. Include exact PR/base/
head/commits/files; before/after ledger classifications and evidence mapping;
official Chrome metadata response identity; archive URL/SHA/version/revision;
Docker image digest; SBOM PURL; scanner version/database/checksum; exact old
exception removal; matrix history handling; local commands/counts/results/
skips; clean Compose browser results; fresh six-image supply-chain results;
every current check; issue #67 closure recommendation; no-new-exception/
no-weaken/no-new-PR/no-merge/no-secret/scope confirmations; and strongest
remaining reason not to proceed.

Report `COMPLETE` only if both ledgers are truthful and the fixed image passes
the normal supply-chain/browser gates with the expired exception removed.
`PARTIAL`/`BLOCKED` must identify a concrete external/tool or remaining
Critical finding with exact evidence. Do not return because scans/builds/tests
are long. No post-report push. Signal exact FIFO `OK`, then wait for strategic
review.

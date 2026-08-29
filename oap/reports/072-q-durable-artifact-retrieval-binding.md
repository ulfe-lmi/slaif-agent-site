# OAP execution report — 072-q

- Order: `072-q-durable-artifact-retrieval-binding`
- Publication: `AMENDED_EXISTING_PR`
- Result: `PARTIAL`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)
- PR state: `OPEN`, never merged
- Base: `main`
- Head: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `9ad30a48c093fc1c3fe3f96c2c45c84064a60bfe`
- Implementation SHA: `f40967d368cc229429ec52d59f71c5e3a4f4e994`
- Report publication commit: `SELF`
- Pushed implementation commit: `f40967d368cc229429ec52d59f71c5e3a4f4e994`

## Changes

- Added migration `037_001_browser_artifact_worker_binding`: a non-null
  `worker_request_id`, request/kind uniqueness and retrieval index; upgrade
  fails safe if legacy artifacts exist, and downgrade removes only q objects
  while restoring the 036 register signature.
- Extended the Agent-owned register function and dispatcher transaction to bind
  every artifact to the verified signed worker request UUID. Exact replay is
  accepted; request-ID or metadata mismatch fails before terminal completion,
  preserving atomicity.
- Added a SECURITY DEFINER, Agent-runtime-only retrieval binding requiring
  current capability/site/workspace/delegator authority, exact run/artifact
  bindings, retained private artifact, and terminal `COMPLETED` state. No table
  privileges were expanded and the public byte route remains 404.
- Added internal `AgentBrowserRunService.retrieve_artifact`, which reconstructs
  bounded worker metadata without exposing internal IDs, invokes the existing
  authenticated worker client, verifies bytes/size/digest, and maps missing
  binding to non-leaking not-found and worker/storage/digest failures to
  unavailable.
- Corrected continuity facts from 072-p: its delivery was
  `AMENDED_EXISTING_PR` (not `CREATED_NEW_PR`) and its final report/check head
  was `9ad30a48...` (not `e9a8b0a...`). The exact 41-entry Chrome `.64`
  vulnerability exception/issue #67 remains unchanged through `2026-09-04`.

## Evidence

- `uv run --frozen pytest services/backend/tests/unit`: 433 passed.
- Focused browser control-plane integration: 2 passed; completed artifact
  retrieval returned the persisted worker request UUID and exact binding.
- Focused control-database marker integration after migration-head update: 1
  passed.
- Full integration run: 110 passed, 1 initial stale-marker expectation failed;
  the expectation was corrected and the focused test passed (no product failure).
- `uv run --frozen ruff check ...`: pass; format check pass; `uv run --frozen
  mypy`: pass (222 source files); compileall pass.
- Repository unittest: 54 passed; repository policy pass; Mermaid: 16 diagrams
  rendered; Markdown scan pass.
- Node 24.14.1 / pnpm 11.22.0: frozen install, lint, format-check, typecheck,
  tests, build, and license listing passed.
- `uv build --out-dir /tmp/slaif-agent-site-distributions-q`: wheel and sdist
  built successfully.
- Fresh report-head CI run `33267338881` completed with these required-check
  states: `success` — Dependency review, Foundation PostgreSQL 14, 15, 16, 17,
  and 18, Markdown, Mermaid, Node contracts, Python 3.12, 3.13, and 3.14
  quality/package, Repository policy, and Supply-chain evidence; `failure` —
  Compose and edge packaging. CodeQL run `33267338941` was `completed/success`.
  The failed Compose job was retried in the same run; the retry reproduced
  `agent-browser-dispatch: ... state=FAILED code=BROWSER_NAVIGATION_HTTP_404`
  after all services became healthy. No q artifact-registration or migration
  error was reported.
- After the report-only amendment, authoritative final-head CI run
  `33268081604` completed with the same result: every listed check passed
  except Compose and edge packaging, which failed on the same navigation 404;
  final-head CodeQL run `33268081594` passed.
- Failed-job retry on final report head (`33268540702`) passed Supply-chain
  evidence and reproduced only the Compose/edge navigation 404; final-head
  CodeQL `33268540701` passed.
- The final published report head (`bf57a94...`, superseded by this immutable
  report amendment) was verified by CI `33269231669`: all required checks passed
  except Compose/edge, which again emitted the navigation 404; supply-chain
  passed. CodeQL `33269231716` passed.

## Required confirmations

- Scope: only q migration, grants, dispatcher binding, internal retrieval seam,
  tests, and migration-head expectations; no public endpoint, worker runtime,
  storage/network redesign, GC, dependency, release, or second PR changes.
- Secrets, capabilities, cookies, internal IDs, and credentials were not
  committed or logged; production systems/data were not accessed.
- No required check was intentionally skipped; no merge, auto-merge, close, or
  acceptance was performed. Strategy retains review and merge authority.
- Parent Objective 072 remains `PARTIAL` pending the separately ordered 072-r
  public artifact-byte retrieval boundary and final strategic review.

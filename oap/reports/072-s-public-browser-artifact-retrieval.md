# OAP execution report — 072-s

- Order: `072-s-public-browser-artifact-retrieval`
- Publication: `AMENDED_EXISTING_PR`
- Result: `PARTIAL`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)
- PR state: `OPEN`, never merged
- Base: `main`
- Head: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `02ec60520d21fa542c85c73f2509bd61ee34a3a4`
- Implementation SHA: `4d4c8b63e0133c415b552ddc20c76d8b04a1d78f`
- Report publication commit: `SELF`
- Pushed implementation commits: `5968ae422682cf9e92dfac4ea0ee7012d94de072`,
  `cfa41fcb9c8f1cf7ab1ef9f7346b8eb336db64fc`,
  `4d4c8b63e0133c415b552ddc20c76d8b04a1d78f`

## Changes

- Wired `GET /api/agent/v1/preview-runs/{run_id}/artifacts/{artifact_id}` to
  the existing exact capability/site/workspace/delegator retrieval binding.
  Callers cannot supply request UUIDs, MIME, digest, storage paths, or
  authority IDs.
- Returned only bounded verified bytes with exact allowlisted `Content-Type`,
  `Content-Length`, digest ETag, `Content-Disposition: inline`, `nosniff`,
  `Cache-Control: private, no-store`, `Pragma: no-cache`, and
  `X-Robots-Tag: noindex, nofollow, noarchive`. Missing/foreign/expired/
  nonterminal bindings are non-leaking 404s; worker/storage/digest failures are
  503. A 10-second Agent retrieval timeout bounds unavailable-worker latency.
- Extended the disposable Compose smoke to retrieve all six artifacts through
  NGINX, validate PNG dimensions and summary content, verify Agent and worker
  restart retention, foreign/random 404s, worker-secret outage 503/recovery,
  canonical separation, and existing hostile-network/cleanup checks.
- Updated API, deployment, authorization, security, operations, scaling,
  service-authority, and configuration documentation to distinguish implemented
  private retrieval from deferred GC/source/review/publication behavior.

## Evidence

- Focused public route/service tests: 5 passed; exact headers/body/digest and
  unavailable/not-found mappings covered.
- Full backend/unit/repository suite after route wiring: 600 passed plus 26
  subtests; full integration: 111 passed. Ruff, format, mypy, compileall, and
  packaging checks passed.
- Compose smoke contract tests: 7 passed; shell syntax valid. Repository
  policy, Mermaid (16 diagrams), Markdown (0 issues), and Node 24.14.1 / pnpm
  11.22.0 frozen lint/format/typecheck/tests/build/licenses passed.
- Local Compose attempts reached and verified all six public artifact bytes,
  Agent restart retention, and random/foreign 404s. One attempt failed on an
  over-specific structure-summary assertion; three later attempts failed at
  the worker-outage probe before the final harness-only repair. The harness now
  uses a bounded service timeout and a recoverable worker-binding outage path;
  the final local run was not completed after that last adjustment. The
  worker-unavailable 503 path remains covered by focused service tests and
  timeout mapping; this local limitation is reported literally.
- Fresh implementation-head CI/CodeQL states are recorded below after remote
  completion.

## Required confirmations

- Scope: only public Agent retrieval wiring, bounded timeout, tests, Compose
  proof harness, docs, and transcript; no schema/migration/grant, worker
  runtime/store/network redesign, dependency, second PR, merge, or release.
- Secrets, capabilities, cookies, internal IDs, storage paths, and artifact
  bytes were not committed or logged; production systems/data were not
  accessed.
- No required check was intentionally skipped. Strategy retains acceptance and
  merge authority. Objective 072 is `PARTIAL` until this report's final remote
  CI/Compose verification is green and strategic review completes.

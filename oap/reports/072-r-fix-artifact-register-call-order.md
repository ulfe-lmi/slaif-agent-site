# OAP execution report — 072-r

- Order: `072-r-fix-artifact-register-call-order`
- Publication: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)
- PR state: `OPEN`, never merged
- Base: `main`
- Head: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `6be8a751039f49fef731fe2d3bafce543ffe8a86`
- Implementation SHA: `88149e051e4cc53036779edb07c6afe42806dea4`
- Report publication commit: `SELF`
- Pushed implementation commit: `88149e051e4cc53036779edb07c6afe42806dea4`

## Changes

- Corrected the dispatcher call to match migration 037 exactly: positional
  values are `kind TEXT` followed by `worker_request_id UUID`, then MIME,
  digest, size, target, route digest, and expiry. No schema, SQL signature, or
  grant was changed.
- Added a focused dispatcher regression that captures the actual finalization
  call and asserts the positional values and Python types, preventing mock-only
  argument-order drift.
- Preserved the public artifact-byte endpoint at 404, the exact 41-entry Chrome
  `.64` vulnerability exception/issue #67 through `2026-09-04`, and all prior
  worker/retrieval boundaries.

## Evidence

- Real PostgreSQL browser control-plane integration: 2 passed, including
  artifact register, exact replay, persisted request binding, and terminal
  completion through migration 037.
- Full backend integration: 111 passed in 532.54s.
- Unit/repository suite: 488 tests plus 26 subtests passed; focused dispatcher
  unit regression: 4 passed; Python quality/mypy/format checks passed.
- Repository unittest: 54 passed; repository policy pass; Mermaid and Markdown
  preparation checks pass; Python wheel/sdist packaging pass.
- Node 24.14.1 / pnpm 11.22.0: frozen install, lint, format-check, typecheck,
  tests, build, and license listing passed.
- Local clean Compose attempt was blocked before deployment by executor Docker
  socket permission (`/var/run/docker.sock`); no local Compose result is
  claimed.
- Authoritative report-head CI `33270933729` completed `success` across all
  required jobs, including Compose/edge and Supply-chain evidence. CodeQL
  `33270933720` completed `success`.

## Required confirmations

- Scope: only dispatcher positional repair, focused regression, transcript, and
  report; no migration redesign, public route, worker runtime, token/route,
  dependency, GC, review, merge, release, or second PR changes.
- Secrets, capabilities, cookies, internal IDs, and credentials were not
  committed or logged; production systems/data were not accessed.
- No required check was intentionally skipped; no merge, auto-merge, close, or
  acceptance was performed. Strategy retains review and merge authority.
- Objective 072 remains `PARTIAL` pending 072-s public retrieval and final
  review.

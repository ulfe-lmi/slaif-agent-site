# OAP Report — 072-l

- Order: `072-l-durable-browser-dispatch`
- Result: `PARTIAL`
- Delivery: `AMENDED_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66) (OPEN)
- Base: `main` at `082f2359b0c4d59b692580d17992c35d46183b12`
- Branch: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `b5430ccdbfdc7c410d3a318109c89945d9e80600`
- Implementation SHA: `330d3115e3ac3e44cb277a6905d40e708f85e4da`
- Pushed commits: implementation SHA above; report-only child follows.

## Delivered

Added the Agent-owned bounded durable browser dispatcher and typed settings.
Agent API lifespan starts/stops it against the existing Agent pool, signing
key, and authenticated worker client. It claims with fresh leases, mints
run-bound preview credentials, renews leases, verifies signed results and
artifact bindings, retrieves and hashes bytes, and atomically registers private
artifact metadata with terminal completion. Transient failures release leases;
terminal worker states map to the bounded control-plane vocabulary. Cancellation,
shutdown, lease loss, restart recovery, and readiness are fail-closed. No
migration, grant, worker-runtime, public-byte endpoint, or artifact-GC change
was made.

Files include `agent_api/dispatcher.py`, dispatcher configuration and lifespan
wiring, JSONB summary decoding, focused dispatcher tests, Compose settings and
smoke coverage, and updated configuration/operations/testing documentation.
The existing 31-entry browser CVE exception and issue #67 were preserved
unchanged.

## Evidence

Local passing evidence:

- `uv run --frozen ruff check services/backend tests/repository tools`
- `uv run --frozen ruff format --check services/backend tests/repository tools`
- `uv run --frozen mypy`
- `uv run --frozen pytest services/backend/tests/unit` — 425 passed
- `uv run --frozen pytest services/backend/tests/integration/test_agent_browser_http.py services/backend/tests/integration/test_browser_run_control_plane.py` — 4 passed
- Node 24.14.1 / pnpm 11.22.0 lint, format, typecheck, test, build, and licenses — passed
- repository compile/unit/policy/Markdown checks — passed

The clean local Compose smoke reached the dispatcher restart durability marker,
but the real worker fixture returned `BROWSER_NAVIGATION_HTTP_404` for the
queued demo runs; it was stopped after bounded retry/terminal evidence and is
not claimed as a passing real-Chromium completion. GitHub Compose and edge
packaging likewise failed. This remains the blocker to `COMPLETE`; objective
072 stays `PARTIAL` pending the route/projection E2E repair and public artifact
retrieval order.

## CI

Fresh checks for implementation SHA: Python 3.12/3.13/3.14 quality and package,
Node contracts, Foundation PostgreSQL 14–18, Markdown, Mermaid, repository
policy, dependency review, supply-chain evidence, CodeQL, and language analysis
all passed. `Compose and edge packaging` failed (7m15s). No check was skipped
or treated as pass.

## Scope and safety confirmations

- No extra PR, merge, auto-merge, release, or order selection.
- No production systems, credentials, capability values, cookies, or artifact
  bytes were exposed.
- No migration/grant expansion, worker runtime/store/network change, public
  artifact endpoint, GC, MCP, review, promotion, or publication behavior was
  added.
- Report publication is the sole child of the implementation commit.

Report publication commit: SELF

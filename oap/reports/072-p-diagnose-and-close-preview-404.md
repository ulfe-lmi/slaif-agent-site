# OAP execution report — 072-p

- Order: `072-p-diagnose-and-close-preview-404`
- Publication: `CREATED_NEW_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)
- PR state: `OPEN`, never merged
- Base: `main`
- Head: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `74cb99e3ec31cb2c9284190977792e300d59f51e`
- Implementation SHA: `63998f16e056f10bce6c5dff4ea9f28a76662ace`
- Report publication commit: `SELF`
- Pushed implementation commit: `63998f16e056f10bce6c5dff4ea9f28a76662ace`

## Changes

- Added secret-safe Render browser-preview stage telemetry using only the fixed
  `context`, `token-binding`, `authorize-consume`, `cow-context`,
  `authorize-recheck`, `projection-query`, and `success` vocabulary and bounded
  outcomes. No credentials, routes, IDs, payloads, locators, or exception text
  are emitted.
- Diagnosed the 404 boundary: Render reached `success`; dispatcher artifact
  registration rejected worker retention beyond the authoritative run expiry,
  causing lease release and a one-time-token retry. The dispatcher now reads
  the trusted run expiry through the Agent function boundary and clamps only
  artifact registration expiry to it.
- Canonicalized the Next app-path-routes manifest recursively by JSON object
  key (array order preserved), with bounded content-free JSON key-path/hash
  difference evidence.
- Added focused logging and semantic-manifest regressions. Updated the Compose
  smoke harness to assert durable Agent-owned dispatch artifacts after the
  dispatcher became authoritative; direct worker contracts remain covered by
  the browser-worker unit suite.
- Preserved `oap/active` as `072-p` and committed the exact order bytes without
  editing either strategic input.

## Evidence

- Targeted clean-stack browser dispatch before repair: Render stage sequence
  reached `success`; the subsequent retry stopped at `authorize-consume` with
  `not_found`, confirming the one-time token was already consumed. No secret or
  identifier values were recorded.
- Targeted clean-stack browser dispatch after repair: `COMPLETED`; private
  heading artifact returned; Render stages all reached `success`.
- `uv lock --check`: pass.
- `uv sync --frozen --all-groups`: pass.
- `uv run --frozen ruff check services/backend tests/repository tools`: pass.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: pass.
- `uv run --frozen mypy`: pass.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: 484 passed.
- `uv run --frozen pytest services/backend/tests/integration`: 111 passed.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: pass (wheel and sdist).
- Preparation checks: compileall pass; repository unittest 54 passed; repository
  policy pass; Mermaid 16 diagrams pass; markdownlint 0 issues.
- Node gate: Node `v24.14.1`, pnpm `11.22.0`; frozen install, lint,
  format-check, typecheck, tests, build, and license listing passed.
- Clean supply-chain run: reproducibility pass (two Python and two semantic
  Next builds), six immutable images, `critical=41`, `high=115`, checksum pass.
- Final exit-captured clean Compose smoke: `COMPOSE_EXIT=0`; browser E2E,
  durable dispatcher, six private artifacts, restart retention, secret recovery,
  readiness, recovery, and packaging checks passed.
- Focused Compose smoke contract tests: 7 passed.
- Fresh remote required checks on report head `e9a8b0a6cc95f23ab2fde23eb50c74e82e5b5c64`:
  CI run `33265219717` = `completed/success` (all matrix jobs green), CodeQL
  run `33265219715` = `completed/success`.

## Required confirmations

- Scope: bounded to 072-p; no migrations, grants, dispatcher redesign, worker
  runtime/network/store redesign, public artifact retrieval, GC, merge, or
  release changes.
- Secrets/capabilities/cookies/locators: not committed or printed; logs use
  fixed stage/outcome fields only.
- Production systems/data/credentials: not accessed.
- Skipped required checks: none for this order.
- Extra objective PRs: none.
- Merge/auto-merge/close: none; strategy retains acceptance and merge authority.
- Parent objective 072 remains `PARTIAL` only for its separately ordered public
  artifact-byte retrieval boundary; 072-p itself is complete.

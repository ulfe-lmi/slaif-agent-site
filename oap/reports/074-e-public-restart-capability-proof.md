# OAP implementation report — 074-e

- ID/order: `074-e-public-restart-capability-proof`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) (OPEN, unmerged)
- Base: `main`
- Starting remote SHA: `6897d5b46dc7865342786226032443f3e715ba4d`
- Starting report head: `6897d5b46dc7865342786226032443f3e715ba4d`
- Implementation SHA: `b1edcd7ddf717f9f09e61fc79520d5c6b50c1272`
- Report publication commit: SELF

## Proof delivered

- Added `tools/compose/public_agent_restart.py`, a stdlib-only public-edge
  proof helper. It logs in with the disposable Compose fixture account,
  obtains CSRF from the session cookie, creates one bounded L1 workspace and
  capability through NGINX Control endpoints with fixed idempotency keys, and
  retries both mutations to prove one-resource replay. The Agent plaintext
  token exists only in process memory; request bodies, subprocess output,
  files, environment, URLs, artifacts, and failure messages never contain it.
- The helper uses only `/api/control/v1/*`, `/api/agent/v1/*`, and public health
  paths. It restarts exactly `control-api` and `agent-api` with
  `docker compose -p <project> restart control-api agent-api`, waits for both
  public readiness endpoints, authenticates the same token after restart,
  lists persisted workspace/capability metadata, revokes through public
  Control, proves Agent `401`, checks metadata for token absence, and clears
  capability, header, CSRF, password, cookie, and client references.
- Extended `tools/compose/smoke.sh` to run the helper once in the clean public
  Compose flow, capture only its safe IDs/status line, and verify exactly one
  `WORKSPACE_CREATED`, one `CAPABILITY_ISSUED`, and one `CAPABILITY_REVOKED`
  audit row. Existing desktop/phone L1/L4 Agent Playwright contracts remain a
  single run; no redundant Agent Playwright run was added.
- Added focused unit coverage for public-path confinement, redacted output,
  exact restart targets, idempotency headers, failure handling, and cleanup.

## Correction to 074-d report

The 074-d report overstated dynamic Agent-session restart recovery. Its public
browser contracts and later smoke restarts did not use the same human-issued
capability across a Control+Agent restart. This 074-e report limits the claim
to the new deterministic helper and its clean-Compose evidence below; the
074-d report remains unchanged.

## Exact changed surfaces

`tools/compose/public_agent_restart.py`, `tools/compose/smoke.sh`,
`tests/repository/test_public_agent_restart.py`, and the unchanged
074-e `oap/active`/order transcript.

## Evidence

- Focused checks: `sh -n tools/compose/smoke.sh`; Python compileall; Ruff
  format/check on the helper and test; and
  `uv run --frozen pytest tests/repository/test_public_agent_restart.py -q` —
  3 passed.
- One final clean smoke passed with
  `sudo -n env PATH="$PATH" sh tools/compose/smoke.sh slaif071e`.
  It reported `public-agent-restart: OK` with Agent statuses 200 before,
  200 after Control+Agent restart, and 401 after revoke,
  `public-agent-restart-audit: OK ... rows=3`, all desktop/phone setup,
  governance, preview, stable-device, and L1/L4 Agent browser contracts, and
  final `compose-smoke: OK` after 45 smoke tests. The smoke cleanup removed the
  disposable Compose project and volumes.
- Earlier bounded attempts were not treated as evidence: an unprivileged
  Docker-socket invocation failed before execution; a temporary credential-file
  invocation failed because `e2e.sh` removes that file; and a force-recreate
  variant exposed a transient public 404. Those paths were removed/repaired;
  only the final restart-based clean smoke is claimed above.
- Implementation-SHA GitHub checks: all 20 completed successfully, including
  Compose and edge packaging (public NGINX E2E and restart proof), Supply-chain
  evidence, Node contracts, Python 3.12/3.13/3.14, PostgreSQL 14–18,
  Repository policy, Markdown, Mermaid, Dependency review, language detection,
  and CodeQL analyses.

## Scope and safety confirmations

- Only 074-e was executed. The exact `oap/active` value and immutable order
  bytes were committed with implementation `b1edcd7`; its parent is the
  required starting report head. Exactly one report-only child is published.
- PR #70 was amended; no second objective PR, merge, auto-merge, release,
  product/migration/grant/UI/authorization behavior, dependency, or
  supply-chain change occurred. No required check was skipped, pending,
  cancelled, or treated as pass without completion.
- No real secret, capability plaintext, cookie, private URL, credential, or
  token was committed or printed. The coding agent did not merge the PR and
  selected no subsequent order.

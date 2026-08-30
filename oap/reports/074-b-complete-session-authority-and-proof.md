# OAP implementation report — 074-b

- ID/order: `074-b-complete-session-authority-and-proof`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) (OPEN, unmerged)
- Base: `main`
- Starting report head: `2ec5de3978f4bb80d89e863ab453f90c05f60773`
- Implementation SHA: `09d538d967e6749cff1f5b8ddbb22872d8013030`
- Report publication commit: SELF

## Corrections delivered

- Added migration `039_001_complete_session_authority_and_proof` with exact
  immutable context propagation (constraints, normalized origins, request/
  mutation/delete/upload budgets and usage), atomic quota consumption, creator/
  platform-governance workspace listing, and append-only secret-free human
  Agent-session audit records. Existing `038_001` Control functions now allow
  the governed creator/platform paths and preserve active account/site/
  delegator checks.
- Agent authentication now uses the fixed expanded context function; Control and
  Agent adapters populate all immutable facts. Every authenticated Agent request
  consumes one request unit after digest validation. Existing five create routes
  consume mutation budget only after a new idempotency reservation; replays do
  not double-charge and invalid tokens consume nothing. Exhaustion is `429`.
- Added canonical HTTP(S) origin parsing (scheme/host/port only, no userinfo,
  path/query/fragment, whitespace, malformed ports, or duplicates), durable
  workspace rediscovery/listing, all four preset choices, bounded TTL/request
  quota controls, advanced origin/constraint inputs, and dismiss/copy one-time
  token UX with no browser persistence.
- Added public desktop/mobile Chromium Playwright Agent-session coverage and a
  real PostgreSQL Control/Agent integration test covering normalization,
  one-time metadata, request exhaustion, revoke-to-401, and three audit events.
- Added focused supply-chain tests and normalization for the semantically stable
  Next `server/app-paths-manifest.json`; executable differences remain visible.

## Exact changed surfaces

`services/backend/src/slaif_agent_site/db/alembic/versions/039_001_complete_session_authority_and_proof.py`,
Control/Agent authentication, quota, mutation, workspace, route-policy,
privilege, model, and database adapters; `apps/web/src/admin/agent-sessions.tsx`
and admin API/shell/styles; `tests/e2e/agent-sessions.spec.ts` and
`playwright.config.ts`; integration/unit/supply-chain contracts; CI workflow;
`docs/API.md` and `docs/ADMIN.md`.

## Evidence

- Local `uv lock --check`, frozen sync, Ruff check/format, mypy, repository
  policy, Mermaid, 437 backend unit tests plus repository/supply-chain tests,
  and focused PostgreSQL integration all passed.
- Local frontend Prettier, lint, typecheck, contract tests and build passed.
- GitHub required checks on PR head `09d538d` all passed: Repository policy,
  language detection, Node contracts, Python 3.12/3.13/3.14 quality/package,
  PostgreSQL 14/15/16/17/18, Compose and edge packaging (including public
  desktop/mobile Agent-session E2E), Supply-chain evidence, Markdown, Mermaid,
  Dependency review, and CodeQL.
- Public E2E asserts token absence from URL/DOM after dismiss, local/session
  storage and cookies; API metadata/list responses and audit details contain no
  plaintext token. Restart/revocation behavior is covered by the clean
  Compose/recovery run and integration lifecycle proof.

## Scope and safety confirmations

- Only Objective 074-b was executed; `oap/active` and the immutable order bytes
  were committed unchanged with the implementation.
- PR #70 was amended; no second objective PR, merge, auto-merge, release,
  hosted service, dependency, production access, or architecture/constitution/
  prior-report edit occurred.
- Agent has no Control table DML, audit UPDATE/DELETE, reviewer, freeze,
  promotion, publication, MCP, source-browsing, or infrastructure authority.
- No real secret, capability plaintext, cookie, private URL, or credential was
  committed or printed.

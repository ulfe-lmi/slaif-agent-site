# OAP implementation report — 074-c

- ID/order: `074-c-close-session-governance-invariants`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) (OPEN, unmerged)
- Base: `main`
- Starting report head: `3686d5acebc6f839f4170947b38c129983e7a6ce`
- Implementation SHA: `20def0472b625d85d8b09ff402364e104e6a0de5`
- Report publication commit: SELF

## Corrections delivered

- Closed Agent-session authority races in capability context, quota
  consumption, and mutation idempotency reservation. Current active
  delegator membership ceilings (including legacy `L1`–`L4` values) or active
  platform-administrator authority are rechecked; inactive account/site/
  workspace, expiry, revocation, cross-site, and foreign identifiers fail
  closed.
- Added site-governor permission rechecks to owner-defined workspace and
  capability functions. Creators can inspect their own sessions; governors
  with the relevant `workspace:read-all`, `capability:create`, or
  `capability:revoke` permission can govern another delegator. Audit triggers
  record the authenticated human actor through a transaction-local trusted
  actor setting, with no capability plaintext or secret details.
- Made workspace creation and capability issuance require bounded
  `Idempotency-Key` values and durable request digests. Same-body retries
  replay one resource, mismatches return 409, and capability replays never
  redisplay a token. Explicit empty scopes remain empty; omitted scopes use
  the bounded preset, with duplicate/unknown/above-preset values rejected.
- Aligned Pydantic and SQL validation bounds (including nonzero request
  quota), canonical origins, and stable validation/authority/quota mappings.
  Durable lists and status derivation now expose expired versus revoked
  capabilities truthfully; the admin UI preserves all four presets and clears
  one-time tokens on dismiss/revoke.
- Made 038/039 downgrade paths remove only their additions and restore the
  revision-037 authentication function/grant contract. Updated neutral
  PostgreSQL/Compose fixtures to include the active delegated authority that
  the production guard requires.

## Exact changed surfaces

`services/backend/src/slaif_agent_site/db/alembic/versions/038_001_human_agent_session_control_plane.py`,
`services/backend/src/slaif_agent_site/db/alembic/versions/039_001_complete_session_authority_and_proof.py`,
Control workspace/capability routes and database adapters, workspace request
models, admin Agent-session UI/API types, privilege declarations, integration
fixtures/tests, and `tools/compose/smoke.sh`.

## Evidence

- Local gates: `uv lock --check`; frozen all-group sync; Ruff check/format;
  mypy; 491 unit tests plus 26 subtests; 112 integration tests; repository
  policy (54 tests); supply-chain evidence/reproducibility tests (20); policy,
  Mermaid (16 diagrams), Markdown (290 files), and all ten process `--check`
  smoke commands; Python build; Node 24.14.1 / pnpm 11.22.0 lint, format,
  typecheck, tests, build, and license inventory.
- Focused PostgreSQL Agent-session lifecycle, capability authentication,
  mutation, and browser HTTP tests pass, including replay/mismatch,
  exhaustion, membership authority, restart, and revocation behavior.
- GitHub required checks on final head `20def04` all pass: Repository policy,
  language detection, Node contracts, Python 3.12/3.13/3.14 quality/package,
  PostgreSQL 14/15/16/17/18, Compose and edge packaging (public NGINX
  desktop/mobile E2E and restart/leak smoke), Supply-chain evidence,
  Markdown, Mermaid, Dependency review, and CodeQL.

## Scope and safety confirmations

- Only 074-c was executed; `oap/active` and the immutable order bytes were
  committed unchanged with the implementation. Exactly one report-only child
  is published here.
- PR #70 was amended; no second objective PR, merge, auto-merge, release,
  hosted service, dependency, production access, architecture/constitution,
  or prior-report edit occurred.
- No real secret, capability plaintext, cookie, private URL, or credential was
  committed or printed. Agent authority remains limited to the existing
  semantic mutation/session boundaries.

# OAP implementation report — 074-a

- ID/order: `074-a-human-agent-session-control-plane`
- Mode: `CREATED_NEW_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#70](https://github.com/ulfe-lmi/slaif-agent-site/pull/70) (OPEN, unmerged)
- Base: `main`
- Starting remote SHA: `74d9c189fe241356fbe03f2632197ecbb1ce53a3`
- Implementation SHA: `1d381ea644b5eaaf18a903b037343674a60648d0`
- Report publication commit: SELF

## Delivered

- Installed human-session, CSRF, site-membership, permission, and delegation-
  ceiling protected Control routes for Agent workspaces and capabilities.
- Added migration `038_001` with owner-defined fixed-signature workspace and
  capability functions, bounded preset intersections, constraints, origins,
  quotas, base revision, expiry, delegator, digest-only token persistence, and
  active account/site/workspace checks.
- Added one-time opaque capability issuance, metadata-only listing, and revoke;
  freeze/accept/discard remain unexposed.
- Rechecked Agent authentication against active workspace/site/delegator,
  expiry, and revocation and extended the trusted context contract with quota
  facts without adding Control/reviewer authority.
- Added responsive AI Sessions Web UI and API client through the public NGINX
  path, plus API/administrator documentation and route/privilege coverage.

## Evidence

- Local: `ruff check`, `ruff format --check`, `mypy`; 435 backend unit tests;
  repository policy and Mermaid checks; frontend lint, typecheck, tests,
  format, and complete `pnpm test` passed.
- Integration: capability authentication and targeted Control/Agent lifecycle
  suites passed against disposable PostgreSQL. Legacy lifecycle assertions were
  updated to the order-required fail-closed 401 behavior.
- GitHub required checks: all green — Repository policy, Detect supported
  languages, Node contracts, Python 3.12/3.13/3.14 quality and package,
  Foundation PostgreSQL 14/15/16/17/18, Compose and edge packaging,
  Supply-chain evidence, Markdown, Mermaid, Dependency review, and CodeQL.

## Scope and safety confirmations

- Exact order and `oap/active` bytes were committed unchanged with the
  implementation; no other order was selected.
- No extra objective PR, merge, auto-merge, release, hosted dependency,
  architecture/constitution edit, production access, or real secret was used.
- Agent has no Control-table DML or reviewer authority; Control handlers add no
  content DML. Capability plaintext is not logged, cached, persisted, or
  repeated by any later endpoint.
- Remaining review, freeze, promotion, publication, MCP, and full semantic Agent
  expansion remain outside 074-a.

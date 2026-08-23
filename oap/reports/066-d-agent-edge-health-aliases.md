# OAP Coding-Agent Report — 066-d

## Work order

- Identifier: `066-d`
- Work-order file: `oap/orders/066-d-agent-edge-health-aliases.md`
- Numeric objective: `066`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

Closed the final deployed Agent edge-routing gap on the same PR #57. The exact
NGINX health aliases `/api/agent/health/live` and `/api/agent/health/ready`
proxy only to the Agent service health endpoints, while the general
`/api/agent/` location preserves the full Agent API prefix for routes such as
`/api/agent/v1/session`.

Added a targeted static edge contract proving both mappings and reran the
complete disposable Compose smoke with browser E2E, secret/authority checks,
restart/recovery, edge headers, negative bootstrap, and Apache validation.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#57](https://github.com/ulfe-lmi/slaif-agent-site/pull/57)
- PR state: `OPEN`
- Base/head branches: `main` / `oap/066-capability-auth`
- Starting remote SHA for this continuation: `4c50f75281dffb0b699f97b642b4be79671c9dba`
- Base remote SHA: `6552ee74e9046bb86e57d68acdef6acd0b0d1c07`
- Implementation head SHA: `739be78206eb205ef1ce239647e8cd7872019d0a`
- Implementation commit pushed this round: `739be78206eb205ef1ce239647e8cd7872019d0a`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (verified after publication)
- Prior 066-a/066-b/066-c implementation and report history preserved: yes
- Report parent must equal implementation SHA: yes
- New PR this turn: no
- Amended existing PR: yes, PR #57 only
- Merge performed: NO

## Changes made this round

- Preserved the exact NGINX health aliases and prefix-preserving Agent proxy
  already introduced in implementation `925d2a0`.
- Added a static packaging regression proving the two exact health locations,
  their upstream paths, the prefix-preserving route, and rejection of the old
  trailing-slash passthrough.
- Committed the exact strategic 066-d order and selector bytes.

## Acceptance-criteria evidence

### Criterion 1 — Public Agent health aliases return 200 with normal edge headers

- PASSED. `sudo sh tools/compose/smoke.sh slaif007dci` passes the health probes
  and edge-header contract, including request-ID replacement, CSP, and
  `X-Content-Type-Options` checks.
- The static edge contract proves `/api/agent/health/live` and
  `/api/agent/health/ready` proxy only to `/health/live` and `/health/ready`.

### Criterion 2 — Agent application paths preserve their prefix

- PASSED. The static edge contract proves `location /api/agent/` uses
  `proxy_pass http://agent-api:8000;` without a trailing slash.
- The local Compose smoke’s public Agent health and route probes pass through
  NGINX with the real Agent service healthy.

### Criterion 3 — Non-product Agent paths remain 404 and no Control fallback exists

- PASSED. The static contract rejects the old unrestricted trailing-slash
  proxy form; the complete smoke retains the defined 404 negative-route set.
- No Control, Editor, MCP, Media, Preview, or Web proxy location changed.

### Criterion 4 — Complete Compose/edge smoke passes

- PASSED. `sudo sh tools/compose/smoke.sh slaif007dci` completed successfully,
  including clean deployment, six stable browser targets, setup/governance
  E2E, secret and database authority policy, restart/recovery, render failure
  recovery, negative bootstrap, Apache syntax, and exact cleanup.
- The first 066-c CI run `32647260924` failed only because the required
  `/api/agent/health/live` probe returned 404. The corrected implementation
  rerun `32648042298` passed all checks, and the final 066-d head run
  `32648989954` also passed the complete Compose check.

### Criterion 5 — Scope and transcript remain bounded

- PASSED. This round changes only the targeted edge regression test and the
  exact 066-d transcript bytes; no dependency, migration, secret, application
  route, authority, or product behavior changed.

## Local verification

- `uv run --frozen ruff check tests/packaging/test_edge_contract.py`: PASSED.
- `uv run --frozen ruff format --check tests/packaging/test_edge_contract.py`: PASSED.
- `uv run --frozen pytest tests/packaging/test_edge_contract.py -q`: PASSED — 6 tests.
- `sudo sh tools/compose/smoke.sh slaif007dci`: PASSED — complete deployment,
  browser E2E, six stable devices, governance, edge headers, secret/authority
  policy, restart/recovery, render failure/recovery, negative bootstrap,
  Apache syntax, and cleanup.
- Prior 066-c final full evidence remains applicable to the unchanged runtime:
  411 unit/repository tests, 94 PostgreSQL integration tests, frozen Python and
  Node gates, package build, repository policy, Markdown, Mermaid, and process
  smoke all passed on the parent implementation.

## GitHub CI / required checks

State observed for implementation head `739be78206eb205ef1ce239647e8cd7872019d0a`:

- Analyze (actions): PASS
- Analyze (javascript-typescript): PASS
- Analyze (python): PASS
- CodeQL: PASS
- Compose and edge packaging: PASS
- Dependency review: PASS
- Detect supported languages: PASS
- Foundation PostgreSQL 14: PASS
- Foundation PostgreSQL 15: PASS
- Foundation PostgreSQL 16: PASS
- Foundation PostgreSQL 17: PASS
- Foundation PostgreSQL 18: PASS
- Markdown: PASS
- Mermaid: PASS
- Node contracts: PASS
- Python 3.12 quality and package: PASS
- Python 3.13 quality and package: PASS
- Python 3.14 quality and package: PASS
- Repository policy: PASS
- Supply-chain evidence: PASS
- All required checks green at drafting: YES.
- Report-only commit may trigger fresh checks; strategy must verify SELF independently.

## Local setup / dependencies

- Used the repository-pinned toolchains and the isolated disposable Compose
  project `slaif007dci`.
- The smoke trap removed the exact project’s containers, volumes, and networks.
- No production systems, secrets, dependencies, or infrastructure outside the
  requested edge/deployment test scope were accessed.

## Documentation

- No durable product prose change was required; the static edge contract and
  Compose smoke are the durable routing evidence.
- This immutable OAP report is the required execution artifact.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no.
- Production systems accessed: no.
- Required tests skipped/not run: no.
- Scope deviation: no.
- Extra objective PR: NO.
- Coding-agent merge: NO.
- Activated 066-d order content edited by coding agent: NO.
- Active selector content edited by coding agent: NO.
- Report commit changes only this report: YES.

## Known limitations / blockers

- Agent content mutation, COW writes, publication, review, promotion, and MCP
  behavior remain outside objective 066.
- This edge continuation does not add authenticated Agent API E2E content
  flows; it proves the required health, prefix, negative-path, and deployment
  contracts only.

## Recommended strategic follow-up

Independently review PR #57, the failed-then-corrected CI evidence, exact edge
diff, report ancestry, and complete smoke output. Merge only after strategic
acceptance; coding-agent `COMPLETE` and green CI are not acceptance.

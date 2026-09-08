# OAP Coding-Agent Report — 077-m

## Work order

- Identifier: `077-m`
- Work-order file: `oap/orders/077-m-repair-locale-render-and-security-gates.md`
- Work-order SHA-256: `ba2431b4b2911385976c7103a4d9327dc1583a6130b40473cd9dc48eabfe153b`
- Active SHA-256: `cbbb0dacc2800269e2ba1361eb369daf0e5f0395137f99cd57f67ffeeafe9055`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`BLOCKED`

## Executive summary

Repaired the concrete 077-l Agent page-delete failure and completed the
ordered locale, Render, public-journey, migration, and Apache qualification
work on PR #74. The page-delete root cause was reproduced through trusted COW
SQL: after a default-locale switch, migration 051's redirect guard evaluated a
strict page route for a COW-hidden/tombstoned row and raised SQLSTATE `P0002`,
`PAGE_NOT_FOUND`; the public Agent layer consequently returned
`RESOURCE_NOT_FOUND` (404) instead of a valid delete or a stable graph
conflict.

The implementation and Compose/public evidence are green locally. The round
cannot be `COMPLETE` because the current Grype database still reports twelve
unexcepted Apache Critical findings on the official fixed 2.4.68 Alpine 3.24
image. The matching fixed Alpine packages are not currently available in the
official image's Alpine 3.24 dependency set; adding the reported fixed
`libcurl` version fails the package solver against the official httpd
dependency constraint. No exception or scanner weakening was made.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `ced67e819a101ea01dda92bdba649cc838ddd6cf`
- Implementation head SHA:
  `d09d7b97e43dd93f0238f87aa9f25ac5c3ff8a35`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Parent of the implementation commit: `ced67e819a101ea01dda92bdba649cc838ddd6cf`
- New PR this turn: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Added migration `053_001_locale_route_integrity`.
  - Locale create/update/delete functions for Editor and Agent now share the
    existing workspace/site structural serialization and a complete post-write
    page/locale/navigation/redirect graph validator.
  - Invalid default switches roll back atomically with stable domain conflict;
    valid switches preserve COW, quota, idempotency, audit, cancellation, and
    row-version behavior.
  - Base function privileges were revoked; only the role-bound wrappers remain
    executable by their respective runtime roles.
  - Redirect static-target validation now resolves rows safely, avoiding the
    strict `PAGE_NOT_FOUND` failure when a COW tombstone is being evaluated.
- Updated the public acceptance journey to create an `sl-SI` home before the
  default switch and delete it dependency-correctly after restoring English.
- Added real PostgreSQL regression coverage for invalid/valid locale switches,
  page deletion after switching, races/cancellation, and the existing retry and
  audit/quota/COW contracts.
- Expanded Render evidence for Agent move/delete/restore, canonical isolation,
  second-site workspace isolation, localized nested browser credentials,
  one-time replay denial, and a broad corruption matrix covering navigation
  targets/parents/cycles/positions/locale/default/JSON/depth/count and dynamic
  route ambiguity.
- Qualified the official Apache source as
  `httpd:2.4.68-alpine3.24@sha256:1b766f17b84026429b7cb243317b142921b24432336e798bc881c43f45ed9567`.
  The committed build uses the packages actually supplied by that image:
  `apr-util`/`apr-util-ldap=1.6.3-r2` and `libcrypto3`/`libssl3=3.5.7-r0`.
  The Apache-specific Alpine 3.24 registry fact is represented in supply-chain
  policy; other Alpine images remain on their independently qualified 3.23
  sources.

## Files changed

- `services/backend/src/slaif_agent_site/db/alembic/versions/053_001_locale_route_integrity.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_control_database_integration.py`
- `services/backend/tests/integration/test_database_bootstrap.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/integration/test_human_agent_session_control.py`
- `services/backend/tests/integration/test_render_browser_preview.py`
- `services/backend/tests/integration/test_render_structure_router.py`
- `services/backend/tests/unit/test_control_database.py`
- `services/backend/tests/unit/test_foundation_contract.py`
- `tools/compose/public_agent_acceptance.py`
- `infra/apache/Dockerfile`
- `supply-chain/policy.json`
- `tools/supply_chain/policy.py`
- `tests/packaging/test_oci_contract.py`
- `docs/SUPPLY_CHAIN.md`
- exact strategy bytes: `oap/orders/077-m-repair-locale-render-and-security-gates.md`,
  `oap/active`

## Acceptance-criteria evidence

### Page-delete diagnosis and locale graph

- Trusted diagnostic SQLSTATE: `P0002`; message: `PAGE_NOT_FOUND`.
- Root stack: `content.slaif_agent_page_effective_route` called from
  `content.slaif_redirect_static_target_exists`, then
  `content.slaif_redirect_validate_state`, then
  `content.slaif_redirect_page_guard`, during
  `content.slaif_agent_page_delete`.
- Invalid switch without the new locale home: HTTP `409`, locale row version
  remains `1`, prior default remains unchanged.
- Valid switch with the new locale home: HTTP `200`, new locale row version `2`;
  restoring the original default advances affected rows exactly once to `3`.
- The original English page delete succeeds after the valid switch; the new
  locale home is then deleted before the locale itself.
- Existing real-PostgreSQL structural race/cancellation and locale journey
  tests passed after the repair. The migration preserves downgrade guards and
  runtime privilege separation.

### Render, browser, and corruption evidence

- Agent HTTP move, delete, restore and effective-route preview: passed.
- Canonical isolation and separately authorized other-site workspace stability:
  passed.
- Localized nested browser preview credential, binding, no projection, one-time
  consumption and replay denial: passed.
- Corruption matrix: passed, including missing labels, duplicate/non-dense
  positions, dangling PAGE, unsafe INTERNAL/EXTERNAL, cross-navigation parent,
  cycle/unreachable, disabled locale, duplicate default, oversized JSON,
  excessive depth/count, visible dynamic ambiguity, and unknown route data.
- Existing five-status public redirect/header tests remain in the branch and
  local Compose reached the full preview and public-agent journeys.

### Apache qualification and blocker

- Official index digest and final rebuilt image behavior: `httpd -t` passed.
- Current Grype scan of the rebuilt Apache image reported these unexcepted
  Critical IDs: `CVE-2026-10536`, `CVE-2026-11564`, `CVE-2026-11856`,
  `CVE-2026-32327`, `CVE-2026-34191`, `CVE-2026-63073`, `CVE-2026-75803`,
  `CVE-2026-8924`, `CVE-2026-8925`, `CVE-2026-8926`, `CVE-2026-8927`, and
  `CVE-2026-9079`.
- Exact affected package/fix pairs: `libcurl 8.20.0-r1 → 8.21.0-r0`,
  `apr-util`/`apr-util-ldap 1.6.3-r2 → 1.6.4-r0`, and
  `libcrypto3`/`libssl3 3.5.7-r0 → 3.5.8-r0`.
- Attempting the fixed pins fails at Alpine resolution because
  `libcurl-8.20.0-r1` is required by the official httpd dependency set and
  Alpine 3.24 does not currently provide the requested `libcurl=8.21.0-r0`.
  This is an upstream/package-availability blocker. No exception was added.

## Local verification

- `uv lock --check`: PASSED
- `uv sync --frozen --all-groups`: PASSED
- Ruff check/format and mypy: PASSED
- Unit/repository/packaging/supply-chain suite: PASSED — 604 tests, one
  pre-existing Starlette/httpx deprecation warning
- Full integration run: 163 passed, 5 stale migration-expectation failures;
  corrected focused rerun: 11 passed. The failures were only assertions for
  the old `052_001` head and `049_` downgrade guard, now updated to `053_001`
  and `053_`.
- Focused locale, Render, browser, corruption, migration round-trip and
  privilege tests: PASSED
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED — 16 diagrams
- Markdownlint: PASSED — zero issues
- All ten process `--check` smoke commands: PASSED
- `uv build --out-dir /tmp/slaif-agent-site-distributions-077m`: PASSED
- Frozen Node 24/pnpm 11.22 gates, build, tests and license inventory: PASSED
- `sudo -n sh tools/compose/smoke.sh slaif007ci`: PASSED — full Compose,
  public Agent, browser, recovery, edge and secret-policy evidence
- `sh tools/supply_chain/run.sh /tmp/slaif-077m-supply-chain-evidence`:
  BLOCKED at the Apache zero-Critical gate for the exact findings above; no
  evidence finalization or exception was used to claim success.

## GitHub CI / required checks

Observed for implementation head `d09d7b97e43dd93f0238f87aa9f25ac5c3ff8a35`
at report composition:

- SUCCESS: Repository policy; Node contracts; Python 3.12/3.13/3.14 quality
  and package; Foundation PostgreSQL 14, 16, 17, and 18; Markdown; Mermaid;
  Dependency review; CodeQL and its language-analysis jobs.
- PENDING: Foundation PostgreSQL 15; Compose and edge packaging; Supply-chain
  evidence.
- The remote CI run is `34008284872`; CodeQL run `34008284873` is terminal
  success. Pending is not treated as pass.

## Scope, safety, and completion boundary

- No secret, capability, cookie, private preview credential, production system,
  production data, extra PR, merge, release, issue closure, or unrelated
  architecture change occurred.
- Dynamic `{slug}` collection-detail behavior remains out of scope.
- No scanner, vulnerability policy, exception set, or required acceptance
  check was weakened.
- The strongest reason not to accept this round is the concrete upstream
  Apache package blocker and the still-pending remote checks. Objective 077-m /
  PR #74 can be declared complete only when the exact official Apache image
  has a qualified package set with zero unexcepted Critical findings (or a
  strategy-authorized replacement/fixed upstream artifact), all required
  current-head GitHub checks are terminal green, and strategy independently
  accepts the unchanged bounded scope. The coding agent is not authorized to
  merge.

No extra PR was created. No merge or auto-merge was performed.

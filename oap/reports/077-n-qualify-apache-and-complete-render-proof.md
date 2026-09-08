# OAP Coding-Agent Report — 077-n

## Work order

- Identifier: `077-n`
- Work-order file: `oap/orders/077-n-qualify-apache-and-complete-render-proof.md`
- Work-order SHA-256: `fc7226a2708f9e08794bd2bac44a654b39956e12dae1f42e2c73e2302568c195`
- Active SHA-256: `4c9a6a82a4f43c749deb39803b4362622170b3220b7674921443970ff35f98c0`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`BLOCKED`

## Executive summary

Qualified the authorized official Debian Trixie fallback for Apache 2.4.68 and
closed the remaining Render/browser/locale proof gaps that were actionable in
the repository. The final Apache image is reproducible, passes `httpd -t`, and
passes the clean Compose/edge behavior checks. The current Grype database still
reports one unexcepted Critical vulnerability, CVE-2026-5450, on Debian
`libc6`/`libc-bin`; Debian Trixie exposes no fixed package version for it.

No vulnerability exception or scanner weakening was used. Objective 077-n is
therefore blocked on this concrete upstream Debian package state.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `558d7dcb97188410edd566986ae2264e65f48a1d`
- Implementation head SHA:
  `4c95dceea50c71276a23dda6f6c3e2321b4cfdb2`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- Parent of implementation: `558d7dcb97188410edd566986ae2264e65f48a1d`
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Replaced only the Apache Alpine fallback with the independently verified
  official Debian Trixie source:
  - index: `docker.io/library/httpd:2.4.68-trixie@sha256:979c38c2228d28c2edfd45c6e27dcee1c7b4a101a5526721ae8ece454e89e99e`
  - observed linux/amd64 manifest:
    `sha256:570743f3adc135cc48a0b10c4ee893dc9c948ea1d1e59550fa8f8af6e35048be`
  - declared base: `debian:trixie-slim`
- Added deterministic Debian package updates:
  `libaprutil1-ldap`/`libaprutil1t64=1.6.3-3+deb13u1`,
  `libssl3t64`/`openssl=3.5.7-1~deb13u2`; removed unused curl/XML/Perl
  payloads, preserved exact module enablement and edge configuration.
- Updated supply-chain policy, Debian package facts, Apache packaging tests and
  documentation while preserving all other Alpine source pins and the empty
  exception sets.
- Added deterministic repeatable-read Render snapshot proof with concurrent
  public Agent page/navigation/redirect mutations, before/after projection
  assertions, canonical isolation and other-site isolation.
- Added canonical and human-preview cancellation proof after production query
  context establishment, pool reuse, no COW/audit residue, and subsequent
  successful render.
- Added a public Agent-created localized nested browser workflow: Agent HTTP
  creates locale/pages/navigation/redirect, public Agent creates the run,
  internal control claims it, the bound credential is issued and consumed, and
  replay/site/workspace/canonical isolation are asserted.
- Extended locale race/retry proof for shared-lock Agent locale/redirect writes
  and same-key retry after cancellation at the existing cancellation barrier.

## Files changed

- `infra/apache/Dockerfile`
- `supply-chain/policy.json`
- `tools/supply_chain/policy.py`
- `docs/SUPPLY_CHAIN.md`
- `tests/packaging/test_oci_contract.py`
- `services/backend/tests/integration/test_render_structure_router.py`
- `services/backend/tests/integration/test_render_projection_integration.py`
- `services/backend/tests/integration/test_render_browser_preview.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- exact strategy bytes: `oap/orders/077-n-qualify-apache-and-complete-render-proof.md`,
  `oap/active`

## Acceptance-criteria evidence

### Apache source, reproducibility, and blocker

- Two reproducible Debian Trixie Apache builds completed in the supply-chain
  runner; final filesystem/config comparison passed through the build stage.
- `httpd -t`: PASSED for both builds.
- Compose Apache edge syntax/behavior and NGINX/Apache contract checks: PASSED.
- Final Grype result: exactly one Critical ID,
  `CVE-2026-5450`, affecting `libc6 2.41-12+deb13u3` and
  `libc-bin 2.41-12+deb13u3`; Grype reports no fixed version.
- Debian Trixie `apt-cache policy` independently showed the same current
  `2.41-12+deb13u3` candidate. The package is foundational and cannot be
  removed without invalidating the maintained Debian runtime. This is the
  precise upstream blocker; no exception was created.
- The previous Alpine result is superseded by this authorized fallback attempt;
  other images were not changed.

### Snapshot, cancellation, restart, and isolation

- Repeatable-read canonical and human-preview snapshots pause after an actual
  production query; public Agent page/navigation/redirect mutations are
  launched after the snapshot barrier; the paused projection remains the
  complete before-state and a fresh projection sees the complete after-state.
- Canonical and preview cancellation tests pass after query/COW context exists;
  transaction/pool cleanup and no mutation/audit residue are asserted, and a
  subsequent render succeeds.
- Existing Render restart/session-lock evidence remains green, with canonical
  isolation preserved.

### Public Agent browser workflow

- Agent HTTP creates the non-default locale, localized nested pages,
  localized navigation item and redirect.
- Agent HTTP creates the durable preview run; the internal control claim path
  claims the run and the signed run-bound credential is issued for the exact
  route.
- Internal browser Render returns the expected localized nested page, route and
  navigation; token text is absent, replay is denied, wrong workspace is
  denied, and canonical remains unchanged.

### Locale race/cancellation continuity

- Shared structural-lock race between Agent default-locale mutation and Agent
  redirect creation serializes to exact valid outcomes.
- Cancellation while waiting on the shared structural lock leaves durable
  locale/audit/idempotency/COW state unchanged; same-key retry remains usable.
- Migration 053 grants/downgrade coverage and 077-m locale/page-delete proof
  remain green.

## Local verification

- `uv lock --check`, frozen sync, Ruff, format, mypy: PASSED
- Unit/repository/packaging/supply-chain tests: PASSED — 604 tests, one existing
  Starlette/httpx deprecation warning
- Focused Render snapshot/cancellation tests: PASSED — 2
- Focused public Agent browser workflow: PASSED — 1
- Focused locale race/retry: PASSED — 1
- Previous full backend integration evidence: 163 passed; five stale 052/049
  expectation failures were corrected and their focused rerun passed.
- Clean Compose public acceptance/recovery/edge smoke: PASSED
- Final supply-chain run:
  `sh tools/supply_chain/run.sh /tmp/slaif-077n-supply-chain-evidence-2`
  reached the final scan and failed only on the exact Apache Critical above.
- Node/TypeScript, repository, Markdown and Mermaid gates remained green.

## GitHub CI / required checks

Observed for implementation head `4c95dceea50c71276a23dda6f6c3e2321b4cfdb2`:

- SUCCESS: Repository policy, Node contracts, CodeQL/language analysis,
  Python 3.12/3.13/3.14, Foundation PostgreSQL 14–18, Markdown, Mermaid and
  Dependency review.
- SUCCESS: Compose and edge packaging.
- FAILURE: Supply-chain evidence, for `CVE-2026-5450` on the Debian Trixie
  Apache image; CI run `34010658754`.
- CodeQL run `34010658753`: SUCCESS.

## Scope, safety, and completion boundary

- No secrets, capabilities, cookies, production systems/data, extra PR, merge,
  release or issue closure occurred.
- No dynamic `{slug}` collection-detail behavior, 078 composition/design/Puck,
  media/MCP/freeze/review/promotion/source/sweep/076 work was added.
- No required check or vulnerability gate was weakened.
- The strongest reason not to accept is the exact Debian Trixie libc Critical
  blocker. Objective 077-n / PR #74 can be declared complete only when a
  maintained official/reproducible Apache 2.4.68 artifact has zero unexcepted
  Critical findings, all current-head checks are green, and strategy accepts
  the bounded scope. The coding agent is not authorized to merge.

No extra PR was created. No merge or auto-merge was performed.

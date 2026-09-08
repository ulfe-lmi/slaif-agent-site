# OAP Coding-Agent Report — 077-e

## Work order

- Identifier: `077-e`
- Work-order file: `oap/orders/077-e-close-page-route-integrity-gaps.md`
- Numeric objective: `077`
- Work-order SHA-256: `133098953984efbf337407b4e423637b8c941f8241ed4da73ab1b8e6e64f1a49`
- `oap/active` SHA-256: `29315b1dbde0758761ce86fb3bb093cbc5ff2b7260204e35a9cc7947b7e7712d`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The active 077-e order closed the four residual 077-d page/route integrity
defects without reopening the broader Objective 077 scope. Agent page
uniqueness now follows active siblings, dynamic `{slug}` pages are terminal,
049 downgrade uses only the supported public COW-disable path, and conditional
scope declarations are validated generically against typed request schemas and
published OpenAPI metadata.

The substantive implementation is complete and unchanged after local and
remote verification. It is committed and pushed as
`c56d535f312b724639a83078eb243c1a1747eed5`, directly on the required 077-d
report head `f2c46faded0d5bb99632c8c6aebdce7a28b5768a`.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `f2c46faded0d5bb99632c8c6aebdce7a28b5768a`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Implementation head SHA: `c56d535f312b724639a83078eb243c1a1747eed5`
- Implementation head parent: `f2c46faded0d5bb99632c8c6aebdce7a28b5768a`
- Implementation commit pushed before this report: `c56d535f312b724639a83078eb243c1a1747eed5`
- Remote branch before report publication: `c56d535f312b724639a83078eb243c1a1747eed5`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Replaced the active site/locale/slug uniqueness index with
  `uq_page_site_locale_parent_slug_active`, using normalized `parent_id`
  identity and a tombstone-aware partial predicate. Distinct same-locale
  sibling branches can reuse a segment while duplicate active siblings remain
  database-conflicted.
- Added database-enforced dynamic-leaf validation to effective-route,
  subtree-validation, accessibility, create, update, move, and restore paths.
  Active children and active dynamic ancestors are rejected under the existing
  workspace/site structural lock and transaction; tombstoned children do not
  route but restoration revalidates the invariant.
- Removed migration 049’s private foundation relation/function behavior. Its
  direct downgrade preflights the generic `content.page` relation kind and
  fails with `049_DOWNGRADE_REQUIRES_PUBLIC_COW_DISABLE` before data, function,
  privilege, or audit mutation. Bootstrap downgrade now checks pending public
  COW operations and calls the exported `disable_cow_schema` API before
  Alembic.
- Added generic route-policy validation for Agent capability mutation scope
  names, normalized/nonoverlapping condition fields, typed request-body field
  presence, and canonical OpenAPI conditional-scope metadata in both
  directions. The live Agent OpenAPI builder now uses the shared metadata and
  validator; generated contract bytes remain unchanged.
- Added real PostgreSQL/Agent HTTP evidence for sibling routes, duplicate
  residue, locale/site isolation, dynamic terminal behavior, deterministic
  dynamic-parent races, direct/public COW downgrade paths, and synthetic
  conditional-policy/schema/metadata negatives.

## Files changed

The implementation commit changed exactly:

- `oap/active`
- `oap/orders/077-e-close-page-route-integrity-gaps.md`
- `services/backend/src/slaif_agent_site/agent_api/app.py`
- `services/backend/src/slaif_agent_site/bootstrap/service.py`
- `services/backend/src/slaif_agent_site/control_api/route_policy.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/049_001_agent_page_structure.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_editable_domain_proof.py`
- `services/backend/tests/unit/test_route_policy.py`

No generated OpenAPI, product documentation, lockfile, dependency, image, or
architecture file changed.

## Acceptance-criteria evidence

### Hierarchical route uniqueness

- `test_agent_page_sibling_routes_and_dynamic_leaf_contract`: passed. Two
  same-locale parents accept `news` children with `/research/news` and
  `/teaching/news`; a duplicate active sibling returns 409 with unchanged
  quota, audit, idempotency, and COW operation state. Cross-locale and
  cross-site rows do not interfere.
- The same test passes tombstone route reuse and restoration conflict checks;
  the restored old sibling remains absent and no failed-restoration residue is
  created.
- The physical partial unique index and trusted page validation remain active
  for canonical promotion-time structure.

### Terminal dynamic pages and races

- The public Agent test rejects creating a child below an active `{slug}` page,
  rejects changing a parent with an active child to `{slug}`, permits the
  change after the child is tombstoned, and rejects restoring that child below
  the dynamic parent.
- `test_agent_page_dynamic_parent_race_keeps_valid_leaf_or_child_tree`: passed
  with two real connections and the advisory-lock waiter barrier, without
  timing sleeps. The final state is either a dynamic leaf with no active child
  or a static parent with a valid child; no partial result remains.
- The complete integration suite passed, including the pre-existing route/move,
  cycle, restore/reuse, and cancellation race cases.

### Public COW downgrade path

- Migration 049 contains no `page_base`, `page_changes`, private `_cow_*`, or
  unexported teardown relation/function reference. The remaining
  `slaif_agent_require_cow_site` references are product security functions,
  not foundation relation or teardown dependencies.
- `test_agent_049_downgrade_rejects_page_data_atomically`: passed. Direct COW
  enabled invocation refuses with the stable public-disable message before the
  page-data preflight; after public disable, 049-only page data refuses with
  `049_DOWNGRADE_PAGE_DATA_PRESENT` without mutation.
- The 049-compatible 048 downgrade/upgrade, 046/047 round trip, 048 data
  round trip, editable-domain proof, site-data proof, semantic-audit proof,
  and resource-limit migration path all passed using public COW APIs and
  owner-only canonical observations where COW is disabled.

### Generic conditional-scope drift gate

- `services/backend/tests/unit/test_route_policy.py` includes synthetic
  negatives for an invalid Agent scope, a missing typed request field, a
  conditional read/no-body route, and mismatched OpenAPI metadata; all passed.
- The live route-policy coverage validator inspects every conditional Agent
  mutation’s FastAPI typed body schema, including generated `$defs` references.
  The public Agent OpenAPI builder compares policy metadata against published
  operations in both directions while independently comparing live handler and
  policy inventories.
- Existing page PATCH behavior remains unchanged: metadata fields require
  `page:write`, while `slug`, `locale`, and `route_template` additionally
  require `route:write`, with no durable denial residue.

## Local verification

- `python -m compileall -q tools tests/repository services/backend/src`:
  PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED before report
  publication — 369 files, 0 issues.
- `uv lock --check`: PASSED.
- `uv sync --frozen --all-groups`: PASSED.
- `uv run --frozen ruff check services/backend tests/repository tools`:
  PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 264 files formatted.
- `uv run --frozen mypy`: PASSED — 247 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED — 521 tests, 26 subtests, 1 existing Starlette/httpx deprecation
  warning.
- `uv run --frozen pytest services/backend/tests/integration -q`: PASSED —
  150 tests in 19m04s.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source
  and wheel distributions built.
- `node --version`: PASSED — `v24.14.1`.
- `pnpm --version`: PASSED — `11.22.0`.
- `pnpm install --frozen-lockfile`: PASSED.
- `pnpm lint`: PASSED.
- `pnpm format:check`: PASSED.
- `pnpm typecheck`: PASSED after the required serialized Next build generated
  `.next/types`.
- `pnpm test`: PASSED — serialized production build, workspace tests, web 9
  tests, browser-worker 10 tests, and contract tests.
- `pnpm build`: PASSED.
- `pnpm licenses list --json`: PASSED.
- `uv run --frozen python -m <process> --check` for control API, Editor API,
  Agent API, Render API, MCP adapter, media service, review worker, scheduler,
  media GC, and bootstrap: PASSED — all ten `CHECK_OK`.
- `sudo -n sh tools/compose/smoke.sh slaif071e`: PASSED — clean Compose public
  acceptance, recovery, edge, packaging, security, and 47 repository tests;
  final `compose-smoke: OK`.

The first exploratory parallel Node invocation caused an expected Next build
lock/type-generation ordering failure. It was not used as evidence; the exact
Node commands were rerun serially and passed. No required check was skipped,
weakened, or replaced.

## GitHub CI / required checks

For implementation head `c56d535f312b724639a83078eb243c1a1747eed5`, workflow run
`33868789007` and CodeQL run `33868789004` were inspected. Every observed check
was terminal `SUCCESS` / pass:

- Analyze (actions)
- Analyze (javascript-typescript)
- Analyze (python)
- CodeQL
- Compose and edge packaging
- Dependency review
- Detect supported languages
- Foundation PostgreSQL 14
- Foundation PostgreSQL 15
- Foundation PostgreSQL 16
- Foundation PostgreSQL 17
- Foundation PostgreSQL 18
- Markdown
- Mermaid
- Node contracts
- Python 3.12 quality and package
- Python 3.13 quality and package
- Python 3.14 quality and package
- Repository policy
- Supply-chain evidence

All required checks at the implementation head were green: `YES`. The
report-only commit creates a fresh check set; strategy must independently
verify that its `SELF` report is the remote PR head and that its current checks
are terminal success.

## Local setup / dependencies

- Existing frozen uv and pnpm environments were used.
- Disposable PostgreSQL fixtures and the clean Compose stack were operated
  with passwordless sudo for routine test infrastructure only.
- No production dependency, image, lockfile, exception, or foundation version
  changed.
- Foundation use remains through qualified `agentcow.postgres` public APIs.
- No production systems, data, credentials, capabilities, cookies, or private
  artifact URLs were accessed, printed, or committed.

## Documentation and governance

- `oap/active` was committed byte-for-byte as the strategic activation
  supplied by the order; the order file was committed byte-for-byte and was
  not authored or rewritten by coding.
- Canonical Agent OpenAPI was regenerated and remained byte-identical; no
  documentation update was required because the public contract did not
  change.
- No architecture, constitution, communication protocol, historical report,
  prior order, or unrelated strategic artifact was rewritten.

## Safety and scope confirmations

- Unrelated files changed: `NO`.
- Production systems/data accessed: `NO`.
- Real secrets/capabilities/cookies/private credentials printed or committed:
  `NO`; tests used disposable fixtures, fake credentials, and opaque in-memory
  tokens.
- Required checks skipped, weakened, or replaced: `NO`.
- Scope deviation: `NO`; no locale CRUD, navigation, redirect, dynamic Render,
  composition/design/Puck, media/MCP, freeze/review/promotion, 078+, cleanup,
  refactor, dependency, image, exception, architecture, or historical-artifact
  work was added.
- Extra objective PR: `NO`.
- Coding-agent merge or auto-merge: `NO`.
- Report publication commit changes only this report: `YES`.

## Known limitations / completion condition

No 077-e implementation blocker remains. PR #74 remains open because coding
agents never merge objective PRs and `COMPLETE` is not strategic acceptance.
The broader remaining Objective 077 scope outside this bounded page/route
slice is not implemented by this order.

Objective 070/077’s existing PR #74 may be declared complete only when
strategy independently verifies this report-only `SELF` child, its exact
parent/path and all fresh report-head checks, then obtains the required human
review, merges PR #74 to remote `main`, and verifies the merged main state.
Until that strategic/human merge and verification occurs, this is a delivered
077-e implementation round, not objective acceptance.

Report publication commit: SELF

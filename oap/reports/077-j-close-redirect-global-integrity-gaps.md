# OAP Coding-Agent Report — 077-j

## Work order

- Identifier: `077-j`
- Work-order file: `oap/orders/077-j-close-redirect-global-integrity-gaps.md`
- Numeric objective: `077`
- Work-order SHA-256: `91032fec115546fb97e7723bda6a4ac6c6398ce848123e72319647f7b8a2c561`
- `oap/active` bytes: `077-j` followed by LF (`30 37 37 2d 6a 0a`)
- `oap/active` SHA-256: `c81042e8c77fe4515d67651d1db8806a928fa7d576eb0fe34439dbd4637175ef`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

The active 077-j order is complete. The redirect implementation now validates
the complete visible workspace graph under the shared workspace+site structural
lock while retaining capability filtering for authorization and reads. Redirect
resource constraints use the authoritative 050 parser, including strict mixed
array validation. Deterministic PostgreSQL Agent/Editor/page/redirect race and
cancellation evidence covers the ordered cross-interface cases.

The bounded implementation commit and unchanged strategic bytes are pushed at
`f4a8a5a2c0663ef5fae5c44666e1b45e03face1b`. All local gates, clean Compose
acceptance, current-head GitHub CI, and CodeQL are green. No substantive
reimplementation, unrelated cleanup, new feature, second PR, or merge was
performed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74)
- PR state: `OPEN`, unmerged
- Base/head: `main` / `oap/077-agent-site-structure-semantics`
- Starting remote report head: `afacfb33fa56b1489ee9983b61d3b097f1d752b4`
- Starting remote `main`: `067676314e0d9664d40cb8514ea549b966a4eb2d`
- Literal implementation SHA: `f4a8a5a2c0663ef5fae5c44666e1b45e03face1b`
- Implementation parent: `afacfb33fa56b1489ee9983b61d3b097f1d752b4`
- Implementation commit pushed this turn:
  `f4a8a5a2c0663ef5fae5c44666e1b45e03face1b`
- Remote branch verification: `git ls-remote` equals the implementation SHA
- Report publication commit: `SELF`
- New PR this turn: `NO`
- Amended existing PR this turn: `YES`
- Merge or auto-merge performed: `NO`

## Changes made

- Changed the 051 redirect structural validator to inspect the complete site
  redirect/page graph. Capability visibility remains on the requested Agent
  row and input, but hidden redirect rows cannot hide dangling, cyclic,
  colliding, ambiguous-fallback, or over-depth post-mutation state.
- Replaced the duplicate 051 JSON resource parser with a thin projection of
  `control.slaif_agent_resource_constraints`, and strengthened the 050
  authoritative parser for strict string, UUID, locale, key, and array-bound
  validation across type/page/navigation/locale constraints.
- Made page-target and source dependency checks prospective: deletion/update is
  allowed when an exact or locale-fallback page/redirect still satisfies an
  incoming edge, and denied only when the resulting complete graph is invalid.
  External redirect-chain terminals are treated as valid terminals.
- Ensured Agent and Editor page/redirect structural operations acquire the same
  workspace+site lock before dependency/graph checks. Redirect mutation quota
  is not consumed twice by the generic Agent mutation executor.
- Normalized Editor page conflict mapping so the shared route collision has the
  stable existing conflict response rather than a service-unavailable response.
- Added restricted public Agent coverage for hidden route-prefix and locale
  dependencies, valid unrelated hidden mutations, no hidden detail leakage,
  quota/idempotency/audit/COW rollback, malformed constraints, and migration
  privilege/data round-trip.
- Added deterministic production HTTP race coverage for redirect/page create
  and route update, page move/restore, page delete/internal target update,
  redirect delete/dependent create, restricted Agent versus hidden Editor
  dependency, lock-wait cancellation, and post-tentative-mutation
  cancellation. Barriers use database locks/events and no timing sleeps.

## Files changed

The implementation commit changed exactly:

- `oap/active`
- `oap/orders/077-j-close-redirect-global-integrity-gaps.md`
- `services/backend/src/slaif_agent_site/agent_state/mutations.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/050_001_agent_locale_navigation.py`
- `services/backend/src/slaif_agent_site/db/alembic/versions/051_001_agent_redirect_semantics.py`
- `services/backend/src/slaif_agent_site/editor_api/page_http.py`
- `services/backend/tests/integration/test_agent_mutations.py`
- `services/backend/tests/integration/test_human_editor_production_http.py`

The strategic `oap/active` and 077-j order bytes were committed unchanged.
This report is the only file added by the final report-only commit.

## Acceptance-criteria evidence

### Complete graph integrity and authorization separation

- Agent requested-row authentication, authorization, route/resource validation,
  locale bounds, and read visibility remain capability-bound.
- After tentative COW mutation, `content.slaif_redirect_validate_state` walks
  all site rows and redirect edges, including rows hidden by route-prefix or
  locale constraints. Static page checks use complete-site visibility.
- Source update, target update, and delete against hidden dependencies return a
  stable conflict without hidden IDs, paths, locales, or targets. The complete
  graph is rolled back, including row state, COW changes, quota, idempotency,
  and audit effects. A valid unrelated hidden graph mutation remains valid.
- Locale fallback and alternate redirect/page routes are considered in the
  prospective dependency helpers, so valid fallback is not rejected by a broad
  path-only precheck. Existing unique index
  `content.redirect_site_source_locale` from migration 042 remains the source
  uniqueness index; no new index was introduced.

### Authoritative parser, migration, ownership, and grants

- `control.slaif_agent_resource_constraints(uuid)` in migration 050 is the one
  full resource JSON validator. The 051
  `control.slaif_agent_redirect_constraints(uuid)` function is only a projection
  of its `allowed_locales`, `route_prefix`, and `max_visible_redirects` fields.
- Mixed malformed type/page/navigation/locale/delete values fail closed before
  redirect behavior even when HTTP model validation is bypassed. Existing page,
  model, and navigation callers retain `max_visible_redirects` behavior.
- 049→050→051 upgrade, 050→051 upgrade, downgrade/re-upgrade, data preservation,
  owner, search-path, PUBLIC denial, and Agent grant evidence passed.
- The migration’s structural helpers are:
  `control.slaif_agent_redirect_constraints(uuid)`,
  `content.slaif_redirect_is_visible(uuid,text,text)`,
  `content.slaif_redirect_source_conflict(uuid,text,text,uuid)`,
  `content.slaif_redirect_static_target_exists(uuid,text,text,boolean)`,
  `content.slaif_redirect_validate_input(uuid,text,text,integer,text,boolean)`,
  `content.slaif_redirect_validate_state(uuid,boolean)`,
  `content.slaif_redirect_page_guard(uuid)`,
  `content.slaif_redirect_page_target_dependency(uuid,text)`,
  `content.slaif_redirect_page_target_dependency(uuid,text,uuid)`, and
  `content.slaif_redirect_source_dependency(uuid,text,uuid)`.
- Agent wrappers are
  `content.slaif_agent_redirect_list(uuid)`,
  `content.slaif_agent_redirect_get(uuid,uuid)`,
  `content.slaif_agent_redirect_create(uuid,text,text,integer,text)`,
  `content.slaif_agent_redirect_update(uuid,uuid,text,text,integer,text,integer)`,
  and `content.slaif_agent_redirect_delete(uuid,uuid,integer)`. They are owned
  by `slaif_owner`, have PUBLIC access revoked, and grant EXECUTE only to
  `slaif_agent_runtime`. Editor/control wrappers retain their separate grants;
  base helpers are not exposed to Agent runtime.

### Ordered race and cancellation proof

- Agent redirect source create/update versus Editor page create/route update
  serializes to one coherent winner and one conflict.
- Agent page move/restore versus Agent redirect-source creation serializes to
  one coherent winner and one conflict, with no route collision or tombstone
  residue.
- Agent page deletion versus internal redirect-target update leaves either a
  valid retained page or a valid deleted page with the target update; no
  dangling edge remains.
- Agent redirect deletion versus Editor dependent redirect creation produces
  only the allowed serialization/domain-validation outcomes.
- Restricted Agent source update versus hidden Editor dependency is denied
  without hidden-resource disclosure and with unchanged source, quota,
  idempotency, audit, and COW state.
- Cancellation while waiting on the shared structural lock and cancellation
  after tentative graph mutation both roll back cleanly; retry with the same
  idempotency key remains usable. Barriers observe PostgreSQL advisory lock
  waiters; no timing sleep establishes ordering.
- The full Agent and Editor integration files, plus focused graph, migration,
  and race selections, passed. Existing redirect public routes, scopes,
  schemas, errors, HTTPS/static target grammar, locale fallback, page
  dependencies, OpenAPI, and public NGINX journey remain intact.

## Local verification

- `uv lock --check`: PASSED — 45 packages resolved.
- `uv sync --frozen --all-groups`: PASSED — 44 packages checked.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASSED.
- `uv run --frozen ruff format --check services/backend tests/repository tools`:
  PASSED — 266 files already formatted.
- `uv run --frozen mypy`: PASSED — 249 files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
  — 522 tests; one existing Starlette/httpx deprecation warning.
- `uv run --frozen pytest services/backend/tests/integration`: PASSED — 163
  tests in 22:34.
- Full Agent integration file: PASSED — 41 tests in 409.63 seconds.
- Full Editor production HTTP file: PASSED — 4 tests in 41.27 seconds.
- Focused global-graph/resource/race/cancellation/migration selection: PASSED
  — 4 tests; focused hidden graph and migration checks also passed individually.
- `python -m compileall -q tools tests/repository`: PASSED.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: PASSED —
  58 tests.
- `python tools/check_repository.py`: PASSED — repository policy.
- `python tools/check_mermaid.py`: PASSED — 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 379 files, zero
  issues.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED — source
  distribution and wheel built.
- Node versions: `node --version` `v24.14.1`; `pnpm --version` `11.22.0`.
  `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm format:check`,
  `pnpm typecheck`, `pnpm test`, `pnpm build`, and
  `pnpm licenses list --json`: PASSED. Typecheck and test were rerun
  sequentially after an initial local Next build-cache contention; the
  sequential results are the authoritative results.
- All ten required frozen process checks via
  `uv run --frozen python -m <process> --check`: PASSED with `CHECK_OK`.
- `sudo -n sh tools/compose/smoke.sh slaif007ci`: PASSED — final
  `compose-smoke: OK`, including public Agent acceptance, 11 browser projects,
  restart/recovery, edge, database-role, artifact, packaging, and secret-policy
  checks.

No required local gate was skipped, weakened, replaced, or inferred from an
incomplete result. The temporary parallel frontend contention was corrected by
sequential reruns; it caused no repository change.

## GitHub CI / required checks

At implementation head
`f4a8a5a2c0663ef5fae5c44666e1b45e03face1b`, CI run `33934199311` and CodeQL
run `33934199359` are terminal success. Every current check passed:

- Analyze (actions), Analyze (javascript-typescript), Analyze (python), CodeQL,
  Detect supported languages
- Repository policy, Dependency review, Markdown, Mermaid, and Supply-chain
  evidence
- Node contracts
- Python 3.12, 3.13, and 3.14 quality and package
- Foundation PostgreSQL 14, 15, 16, 17, and 18
- Compose and edge packaging

The previous `afacfb3` Compose failure was not carried forward: the replacement
current-head Compose job passed in 9m28s. No current required check is pending,
skipped, failed, or cancelled, and CodeQL reports no current Critical finding.

## Scope, safety, and completion boundary

- No production system, credential store, real secret, capability, cookie,
  private artifact URL, or production resource was accessed. Local Compose used
  disposable resources and fake credentials.
- No dependency, architecture, constitution, protocol, historical strategic
  artifact, or immutable order bytes were rewritten. No extra PR was created;
  no merge, auto-merge, release, issue closure, or production claim was made.
- No dynamic Render, composition/design/Puck, media, MCP, freeze/review,
  promotion, 076, 078+, cleanup, refactor, or unrelated hardening work was
  added. Objective 077’s later dynamic Render scope remains outside this order.
- The strongest remaining reason not to accept is governance review: the
  strategy must independently review the open PR and this evidence before
  accepting or merging it. There is no remaining implementation or CI blocker
  for this 077-j coding order.
- For coding-agent purposes, 077-j is complete when this report-only commit is
  the verified remote PR head and the exact FIFO response `OK` is delivered.
  Strategy alone may independently accept and merge PR #74; this agent is not
  authorized to merge it.

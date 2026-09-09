# OAP Coding-Agent Report — 078-j

## Work order

- Identifier: `078-j-close-component-increment`
- Work-order file: `oap/orders/078-j-close-component-increment.md`
- Numeric objective: `078`; increment: `078/1`
- PR mode: `AMENDED_EXISTING_PR`

## Status

COMPLETE for this bounded continuation. Objective 078 remains `PARTIAL`.

## Executive summary

The original blocker was not a media-store implementation failure. The live PR
contained the already-delivered 078-i site-theme increment outside the retained
component/local-design boundary, and its strategy-authored order/report prose
was part of the Markdownlint exposure. This order removed the theme product
diff without rewriting its immutable history, then repaired the confirmed
component CREATE authority, whole-document property-removal authority, public
null-removal semantics, and durable replay/no-effect ordering.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), `OPEN`, mergeable
- Base/head: `main` / `oap/078-agent-composition-design-semantics`
- Verified base: `ae3a4a681bb888260192b7bb1b2a337b4906828d`
- Starting remote head: `127d7f13c6e7e139af94792739e46ffe57cf843a`
- Implementation commits pushed: `3fad241d7a8d993b90e156563e769f82fedbfcbf`,
  `41b7f7d487c8f022537b34946e09c76a8a3fc7bf`
- Implementation head SHA: `41b7f7d487c8f022537b34946e09c76a8a3fc7bf`
- Report publication commit: `SELF`
- Remote PR head after report publication: `SELF`, verified after push
- New PR: no; existing PR amended; merge/auto-merge: `NO`

## Changes made

- Reversed the 078-i site-theme product, generated, test, and documentation
  diff in the live PR with a normal forward history commit. The 078-i commit
  `567973e1897ff0ec1cc5017704dd7b914a88d6da`, order, and report remain
  preserved; the theme is deferred to a new PR after PR #77 is merged.
- Added migration `062_001_component_authority_repairs.py`. ADD, CHANGE, and
  REMOVE now derive authority from the union of old/new properties, distinguish
  absent from JSON null, require responsive authority for responsive transitions,
  and keep unsupported design properties fail-closed. CREATE requires structure
  authority plus scopes for caller-supplied design values and applies only fixed
  `Columns.count=1` and `Spacer.size="md"` defaults when omitted.
- Generated the shared Python design authority for CREATE selection, public
  PATCH value changes, null removals, and responsive transitions. Component
  CREATE/PATCH checks now run inside the serialized mutation after durable
  idempotency reservation, so replay/mismatch is resolved before fresh scope or
  optimistic no-op classification.
- Published the same route-policy/OpenAPI authority table for component CREATE
  and PATCH, with explicit presence/change/removal/responsive conditions.
- Added public HTTP and runtime-role regressions for Button.variant,
  Image.aspectRatio, CollectionGrid.columns, optional/local design, responsive
  removal, JSON null, unchanged/no-effect, L2 defaults, L2/L3 CREATE, replay,
  and unknown-null input. Added a current CI component selection to the
  PostgreSQL matrix job.
- Reconciled current README/API/MVP/OAP truth and added the approved governance
  amendment unchanged at
  `oap/governance/2026-09-09-bounded-semantic-pr-increments.md`.

## Files changed

The complete implementation diff is the verified `ae3a4a6..41b7f7d` PR diff.
Its principal groups are:

- Runtime: Agent HTTP/mutation service, generated design authority, route policy,
  OpenAPI generation, and current process/bootstrap references.
- Migration: 062 component authority/update/create repair; deferred 062 theme
  migration removed.
- Tests: Agent public/runtime integration, design/OpenAPI/policy/unit,
  migration/readiness head updates, and retained component/Puck tests.
- Generated: canonical Agent OpenAPI and generated design-system authority.
- OAP/docs: 078-j order/active/report, governance amendment, increment ledger,
  current README/API/MVP truth, constitutions/notices, Markdown exceptions for
  exact immutable strategy prose, and CI selection.

Diff category counts against verified main `ae3a4a6` (added/deleted lines):

- Production: `3484/830`
- Migration: `2461/0`
- Tests: `5385/128`
- Generated: `6413/2298`
- OAP/docs: `4061/66`
- Tooling: `2243/121`

The large cumulative OAP PR is the explicitly authorized 078-j closure
exception. The product scope contains no new theme behavior.

## Acceptance-criteria evidence

### Criterion A — property-removal authority

- Baseline: the strategic disposable diagnostic recorded direct runtime
  removal of Button.variant, Image.aspectRatio, and CollectionGrid.columns
  without their L3 scopes. The pre-repair regression run reached the CREATE
  bypass first: expected HTTP 403, observed HTTP 201.
- Repaired: public HTTP and `slaif_agent_runtime` tests deny unauthorized
  removal, preserve row/version and durable state, require responsive scope for
  map removal/map-to-scalar, and permit authorized null/removal/content edits.
- Anchors: generated `required_scopes_for_component_update` in
  `services/backend/src/slaif_agent_site/content_model/design_system.py`; SQL
  authority/update replacements in migration 062.

### Criterion B — CREATE design authority

- Baseline: narrowed L2 HTTP CREATE of a caller-supplied design property
  returned 201 in the strategic diagnostic and baseline regression.
- Repaired: HTTP and direct runtime tests deny L2 Button.variant,
  Image.aspectRatio, and CollectionGrid.columns; exact L3 scopes succeed;
  responsive values additionally require responsive authority; L2 omitted
  Columns/Spacer defaults succeed; content fields do not require content-write.
- The exact CREATE authority table is shared by route derivation and the trusted
  SQL boundary; migration 060/catalog bytes were not rewritten.

### Criterion C — replay/no-effect/OpenAPI

- Baseline: the strategic diagnostic recorded a valid identical Heading PATCH
  followed by a same-key replay returning 409 because stale no-op state was
  checked before durable idempotency.
- Repaired: focused HTTP tests prove durable no-op replay after a subsequent
  edit, same-key/different-body mismatch, fresh stale no-op conflict, unknown
  null validation, no mutation quota/audit/COW effect for a valid no-op, and
  direct/runtime agreement.
- `x-slaif-conditional-scopes` now labels presence versus value-change, and
  `x-slaif-component-authority` explicitly describes CREATE selection, PATCH
  changes, absent/null removal, and responsive transitions.

### Criterion D — retained boundary and governance

- 078-i theme implementation SHA/history is preserved but absent from the live
  product diff. `oap/active` is exactly `078-j\n` and the 078-j order SHA is
  `f881cdeaff1ae9990ad3b65840bc2f97ae0c2dcd0da47adcb9b1479d6309ba0e`.
- The governance amendment is byte-identical to the strategic supervision
  source, SHA-256
  `86f8cea64bfd259e26327196dc7e88b6d35aef58e1d8b1a0d5440d49df0c7e4a`.
- PR #77 remains open and unmerged; Objective 078 is not claimed complete.

## Local verification

- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`:
  `67 passed` in `722.95s`.
- Focused final authority/migration plus unit command: `19 passed`; final
  direct-JSON-null/migration command: `2 passed`.
- Full backend integration:
  `uv run --frozen pytest services/backend/tests/integration -q`:
  `200 passed` in `1918.98s` before the final replay-order-only route commit;
  the post-commit focused tests and final remote CI cover that route commit.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  `538 passed`, one existing Starlette deprecation warning.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`:
  `58 passed`.
- `python tools/check_repository.py`: passed.
- `python tools/check_mermaid.py`: `16 diagram(s)` passed.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: `0 issues in 430 files`.
  Exact immutable strategic prose is narrowly ignored and hash-verified.
- `uv lock --check`, `uv sync --frozen --all-groups`, full Ruff check/format
  check, mypy, and `uv build --out-dir /tmp/slaif-agent-site-distributions`:
  passed; mypy reported no issues in 266 source files.
- Node 24.14.1 / pnpm 11.22.0: frozen install, lint, format check, typecheck,
  test, build, and license inventory passed.
- Ten frozen backend `--check` commands passed as `CHECK_OK` through
  `PYTHONPATH=services/backend/src uv run --frozen`.

## GitHub CI / required checks

At final implementation head `41b7f7d487c8f022537b34946e09c76a8a3fc7bf`, all
20 required checks were `SUCCESS`: Repository policy; supported languages;
Node contracts; CodeQL actions/python/javascript-typescript; Python 3.12,
3.13, 3.14 quality/package; PostgreSQL 14, 15, 16, 17, 18; Compose and edge
packaging; supply-chain evidence; Markdown; Mermaid; and dependency review.

The first CI run at `3fad241` failed only because Compose acceptance exposed
CREATE idempotency mismatch being preempted by a 403 scope check. After the
`41b7f7d` fix, the new CI run had one PostgreSQL 15 timing failure in an
existing advisory-lock waiter test (`got 0`); PostgreSQL 14/16/17/18 passed.
Rerunning only that failed job passed, and the final remote PR check set is
fully green. No check is pending, skipped, cancelled, missing, or failed.

## Local setup / dependencies

Disposable PostgreSQL fixture databases and fixture roles were created and
cleaned by the existing test harness. No production systems, credentials,
capabilities, cookies, database locators, Docker socket, or hosted service were
accessed. No dependency or lockfile changed.

## Documentation

Current README/API/MVP documents describe 078-j component/local-design truth,
the deferred theme, verified main base, and the remaining Objective 078 and
MVP boundaries. Root and maintained strategic/coding notices reference the
prospective semantic-increment amendment. The increment ledger records PR #77
as open/pending strategic review and defers site-theme to a new PR after merge.

## Safety and scope confirmations

- Unrelated product feature work: `NO`; the theme reversal and explicitly
  ordered governance/truth/CI changes are in scope.
- Historical orders/reports rewritten: `NO`; 078-i bytes remain immutable.
- Activated order or active content changed: `NO`; final active bytes are exact.
- Production secrets/systems accessed: `NO`.
- Required tests skipped/not run: `NO` for the ordered local/remote gates;
  the plain non-uv process smoke invocation was an import-path miss and the
  corrected exact health checks all passed.
- Extra objective PR: `NO`; coding-agent merge/auto-merge: `NO`.
- Report commit changes only this report: `YES`.

## Known limitations / blockers

PR #77 is intentionally still open for independent strategic acceptance. Site
theme/global regions, exact-workspace Puck, media expansion, MCP, review,
promotion, publication, and later Objective 078 increments remain deferred.

## Completion condition

Objective 078 increment 1 / PR #77 can be accepted only when strategy reviews
the final diff/report and merges the open PR. The broader Objective 078 can be
declared complete only after its remaining ordered increments are separately
implemented, verified through their required boundaries, accepted, and merged.

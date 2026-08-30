# OAP implementation report — 075-a

- ID/order: `075-a-complete-editable-domain-substrate`
- Mode: `CREATED_NEW_PR`
- Result: `PARTIAL`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN, unmerged)
- Base/head: `main` / `oap/075-editable-domain-substrate`
- Starting remote SHA: `ef456e63abadddfc7d90794c03be3a63677c87f9`
- Implementation SHA: `4c0b706`
- Report publication commit: SELF

## Delivered

- Added migration `040_001` repairing `field_definition.site_id` with deterministic
  backfill, fail-closed inconsistency detection, immutable-site trigger, and
  composite site/type and site/id constraints.
- Added COW-compatible `content_item_translation` and `item_relation` tables,
  bounded constraints, site-confined composite foreign keys, and restricted
  SECURITY DEFINER CRUD functions.
- Added bounded primitive/cardinality/localization validators and immutable
  translation/relation request and record models.
- Added Editor CRUD routes nested under content items, using the existing HUMAN
  workspace resolution, lock, idempotency, semantic audit, and site policy
  envelope. Added route-policy and privilege inventory coverage.
- Repaired existing Agent field-definition create/list compatibility after the
  new required tenant column and corrected Editor item definition-version use.

## Evidence

- `uv run --frozen ruff check services/backend tests/repository tools`: PASS.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASS.
- `uv run --frozen mypy`: PASS.
- Focused validator tests: `2 passed`.
- Real disposable PostgreSQL `test_content_tables_have_cow_triplets`: PASS.
- Agent create-field integration regression after compatibility repair: PASS.
- Repository and Mermaid checks: PASS (`PASS repository policy`; 16 diagrams,
  301 Markdown files scanned).
- Full legacy integration suite: 106 passed, 8 failed. Failures are existing
  assertions hard-coded to migration `039_001` plus one legacy semantic-read
  expectation; they are not claimed as passing.
- GitHub PR checks were inspected. Repository policy, language detection,
  Markdown, and dependency review passed; Python quality jobs failed on the
  same legacy migration-head expectations, with remaining matrix checks pending
  at report publication.

## Scope and safety confirmations

- Only order `075-a` was executed. The exact active/order transcript bytes were
  committed with implementation. Exactly one new objective PR and one report
  child were created; no merge, auto-merge, release, or second objective PR.
- No Agent/MCP authority, freeze/publication, collection/navigation/redirect,
  locale configuration, composition/theme/media expansion, or dependency change
  was made. No real secret, capability, cookie, credential, or private URL was
  committed or printed.
- Required completion remains PARTIAL pending repair/update of the legacy test
  expectations and remaining GitHub checks; the coding agent did not select a
  subsequent order.

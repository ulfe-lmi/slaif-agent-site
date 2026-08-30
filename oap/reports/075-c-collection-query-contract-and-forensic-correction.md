# OAP implementation report — 075-c

- ID/order: `075-c-collection-query-contract-and-forensic-correction`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN, unmerged)
- Base/head: `main` / `oap/075-editable-domain-substrate`
- Starting report head: `76ca21f7dade11dad322e3e1202c3fa308d1511d`
- Starting remote baseline: `ef456e63abadddfc7d90794c03be3a63677c87f9`
- Implementation SHA: `35203a9cf4ddb162218792e486917cf168d254ac`
- Report publication commit: SELF

## Forensic correction

The 075-b report was first published at `f5b4a096...` with parent
implementation `acd64245...`. The implementation was subsequently pushed at
`ef607ce8c57328a98d7f2c3c9672b37b7861c245` and the same report was rewritten
at `76ca21f7dade11dad322e3e1202c3fa308d1511d`. That violated the immutable
report rule. No earlier report is edited by this order; this new report records
the facts and is the append-only correction.

## Collection query contract delivered

- Added the shared typed, bounded `validate_query_contract` DSL for filters,
  sorts, projections, and pagination. It rejects unknown fields, localized
  filters, duplicate projections, excessive depth/clauses/page size, and SQL
  or executable fragments.
- Added versioned, site-confined collection-view COW operations with exact
  definition-version checks, deterministic validation, row-version
  optimistic concurrency, idempotent Editor CRUD, audit/COW locking, stable
  404/409/422/503 mappings, and no cross-site UUID substitution.
- Added migration `041_001` with collection-view definition/row versions,
  site/type constraints, SECURITY DEFINER v2 create/list/get/update/delete
  functions, least-privilege grants, and a downgrade path restoring the
  pre-slice 040 collection contract and grants.
- Wired the same validated canonical form into Editor writes and Render
  projection/execution with parameterized bounded evaluation; canonical
  composition remains unchanged.

## Evidence

- Real authenticated Editor HTTP proof creates a type, fields, items, and a
  collection view, then lists/gets/updates/deletes it; replay, site/type
  mismatch, stale-version, audit/idempotency, COW, and canonical-isolation
  assertions pass.
- Migration proof exercises `040_001 → 039_001 → 040_001` and
  `040_001 → 041_001 → 040_001`, with and without reconciled COW; restored
  collection functions/schema/grants pass.
- Focused proof: `3 passed` (editable-domain migration plus real Editor HTTP).
  Full integration suite: `117 passed`. Full unit suite: `445 passed`.
- Frozen Python quality/package gates, compile/repository policy/unittest
  (`57 passed`), Mermaid (`16 diagram(s), 305 Markdown scanned`), Markdownlint,
  and `uv build` pass. Node 24.14.1 / pnpm 11.22.0 lint, format, typecheck,
  test, build, and licenses gates pass.
- Clean Compose smoke project `slaif071d` passes health, setup, governance,
  Puck, preview, responsive desktop/tablet/mobile, Agent restart/revoke,
  media, edge, database/login, and secret-policy evidence.
- All 20 GitHub required checks on implementation head pass: Repository
  policy; Detect supported languages; Node contracts; Analyze (actions,
  python, javascript-typescript); Python 3.12/3.13/3.14 quality and package;
  Foundation PostgreSQL 14/15/16/17/18; Compose and edge packaging;
  Supply-chain evidence; Markdown; Mermaid; Dependency review; and CodeQL.
  No check was skipped, pending, failed, or cancelled.

## Scope and safety confirmations

- Only order `075-c` was executed. The exact active/order transcript bytes are
  committed with the implementation. This amends PR #71; no second objective
  PR, merge, auto-merge, release, or unrelated architecture/product scope was
  added.
- Existing collection permissions remain authoritative. No direct base/change
  table privilege or Control content DML was added. No real secret,
  capability, cookie, credential, token, or private URL was committed or
  printed.
- Exactly one report-only child is being published from the literal
  implementation SHA above. The coding agent did not merge PR #71 or select a
  subsequent order.

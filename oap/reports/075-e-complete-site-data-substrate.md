# OAP implementation report — 075-e

- ID/order: `075-e-complete-site-data-substrate`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN, unmerged)
- Base/head: `main` / `oap/075-editable-domain-substrate`
- Starting report head: `d84cf7aea64f235fef48b5e81ea7c39cb9bc3f81`
- Starting implementation parent: `5fa544c9589263a851f36a7af8d41f5942babe3e`
- Starting remote baseline: `ef456e63abadddfc7d90794c03be3a63677c87f9`
- Implementation SHA: `ecb1265fb8d2b5dab6f5c0377bb4c4bbc771b6e9`
- Report publication commit: SELF

## Delivered fixed site-data substrate

- Added migration `042_001_site_data_substrate` with COW-compatible,
  site-confined `site_locale`, `navigation_item`, `redirect`, and
  `proposed_side_effect` tables. Every record has UUID/site association,
  timestamps, row version where mutable, bounded JSON/text, and
  site/composite reference constraints. Locale defaults are unique; navigation
  trees have bounded positions and parent/page associations; side effects are
  permanently `PROPOSED` and have no executor or dispatcher.
- Added SECURITY DEFINER, least-privilege functions for locale CRUD,
  navigation-item CRUD/list/get/move, redirect CRUD, and inert proposed-effect
  create/list. Downgrade tears down COW companions safely and restores the
  exact pre-042 (041) schema/functions/grants; upgrade/downgrade works with
  and without reconciled COW.
- Added shared site-data validators for canonical locale tags, normalized
  internal routes, safe HTTP(S) external targets, page targets, redirect
  self-loops/reserved paths, localized labels, allowlisted effect kinds, and
  bounded inert payloads. Editor validates before any write; service checks
  enabled locale references and rejects indirect navigation cycles/depth.
- Added immutable Pydantic request/record contracts and `ContentModelService`
  methods. Added authenticated Editor routes with existing HUMAN workspace,
  CSRF, named permissions, idempotency/audit envelope, COW locking, and
  optimistic row-version handling:
  `/locales`, `/navigation/{navigation_id}/items`,
  `/navigation-items/{item_id}` plus `/move`, and `/redirects` CRUD.
  Existing navigation container/theme routes remain intact; no Agent REST/MCP
  or dynamic public detail routing was added.
- Updated bootstrap privilege inventory, content-function classification,
  route-policy registry, package inventories, and migration/readiness
  expectations to 042. Added the qualified JSON serialization needed by the
  existing navigation container functions under COW.

## Evidence

- Authenticated public Editor HTTP proof creates/lists/gets/updates/deletes
  locales, creates and moves a nested navigation tree, rejects an indirect
  cycle, handles stale row versions, creates/updates/deletes redirects, and
  verifies zero canonical/navigation residue after COW operations. Replay,
  CSRF/site confinement, and audit/idempotency paths are covered.
- Migration proof exercises `040_001 → 039_001 → 040_001`,
  `041_001 → 040_001 → head`, and `042_001 → 041_001 → 042_001`; the final
  round trip includes reconciled COW and verifies restored 041 functions,
  schema, and grants.
- COW triplet proof covers `content_type`, `field_definition`,
  `content_item`, `collection_view`, `site_locale`, `navigation_item`,
  `redirect`, and `proposed_side_effect`.
- Full integration suite: `119 passed in 717.53s`.
  Full frozen unit/repository suite: `513 passed`; focused site-data,
  migration, COW, health, and validator proofs pass (`19` focused unit/health,
  `5` site-data integration, `57` repository unittest).
- `uv lock --check`, frozen sync, Ruff check/format, mypy, compileall,
  repository policy, Mermaid (`16 diagram(s), 309 Markdown scanned`),
  Markdownlint, and `uv build` pass. Node 24.14.1 / pnpm 11.22.0 install,
  lint, format, typecheck, test, build, and license evidence pass.
- Clean local Compose project `slaif071e`: `compose-smoke: OK`, including
  health, setup, governance, Puck, preview, responsive desktop/tablet/mobile,
  Render failure/recovery, Agent restart/revoke, media, edge, database/login,
  secret-policy, and 45 repository checks.
- All 20 required GitHub checks on implementation head
  `ecb1265fb8d2b5dab6f5c0377bb4c4bbc771b6e9` are terminal `SUCCESS`:
  Repository policy; Detect supported languages; Node contracts; Analyze
  (actions, python, javascript-typescript); Python 3.12/3.13/3.14 quality and
  package; Foundation PostgreSQL 14/15/16/17/18; Compose and edge packaging;
  Supply-chain evidence; Markdown; Mermaid; Dependency review; and CodeQL.
  No check is skipped, pending, failed, or cancelled.
- Prior accepted 075-a through 075-d reports remain immutable; this report
  records completion of the final 075 substrate slice and relies on their
  preserved migration, query, translation/relation, COW, review, and safety
  evidence without editing those reports.

## Scope and safety confirmations

- Only order `075-e` was executed. This amends PR #71; no second objective PR,
  merge, auto-merge, release, dependency, hosted service, architecture/prior
  report edit, Agent REST/OpenAPI/MCP surface, dynamic detail renderer,
  composition/global design/media expansion, freeze/publication, or side-effect
  execution/dispatcher was added.
- No caller-selected schema/SQL/code, direct base/change-table privilege, or
  Control content DML was added. Proposed effects remain inert `PROPOSED`
  records and cannot execute or enter canonical/public behavior.
- No real secret, capability, cookie, credential, token, or private URL was
  committed or printed. Exactly one report-only child is being published from
  the literal implementation SHA above. The coding agent did not merge PR #71
  or select a subsequent order.

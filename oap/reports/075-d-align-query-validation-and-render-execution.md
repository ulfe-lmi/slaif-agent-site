# OAP implementation report — 075-d

- ID/order: `075-d-align-query-validation-and-render-execution`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN, unmerged)
- Base/head: `main` / `oap/075-editable-domain-substrate`
- Starting report head: `a20fb6e92bab9b60a897494291a3a45a290373f6`
- Starting implementation parent: `35203a9cf4ddb162218792e486917cf168d254ac`
- Starting remote baseline: `ef456e63abadddfc7d90794c03be3a63677c87f9`
- Implementation SHA: `5fa544c9589263a851f36a7af8d41f5942babe3e`
- Report publication commit: SELF

## 075-c Render-claim correction

075-c persisted the query contract but overstated Render execution: its
top-level walk did not traverse the tuple of query documents, Render had
divergent status/slug/limit-only policy, content-field sort was rejected, and
it filtered/sorted after a physical prefilter cap while ignoring offset. This
order repairs those claims without editing the immutable 075-c report.

## Delivered

- `content_model/query_dsl.py` now walks every supported top-level and nested
  container, enforcing logical depth, per-list clause, total node, and total
  UTF-8 byte bounds. Executable SQL/comment fragments, malformed keys, and
  non-JSON values are rejected at every depth.
- The shared validator now checks primitive/operator/value compatibility,
  enum choices, localized/reserved/unknown fields, scalar sortability,
  projection shape, direction, and bounded offset/limit. The shared
  `matches_filter` and `sort_collection_items` implementations are the sole
  evaluator used by Render; descending sorts retain an ascending ID tie-break.
- Render reads and compares collection-view `definition_version` with the
  exact active content-type version, enforces canonical `PUBLISHED` versus
  preview `PUBLISHED`/`DRAFT` policy, evaluates logical status/slug and typed
  content-field clauses, supports field/slug sorting, offset, limit, and exact
  projection, and uses only parameterized fixed SQL.
- Render counts candidates before fetching and fails closed with a stable
  query-cost error above the explicit bounded cap; malformed stored values,
  stale definitions, invalid sort values, and cross-site/type data fail
  closed rather than yielding an incorrect partial page.
- Files changed: `content_model/query_dsl.py`,
  `render_api/projection.py`, the query DSL unit tests, the real Render
  PostgreSQL integration fixture/proof, and the exact `oap/active` plus 075-d
  order transcript.

## Evidence

- Query DSL unit/evaluator proof covers nested logical forms, top-level
  traversal, over-depth/over-node/over-byte input, executable fragments,
  wrong primitive/operator values, enum bounds, localized fields, and stable
  descending field-sort ID ties: PASS.
- Real PostgreSQL Render integration persists multiple News-like items with
  physical order different from an integer `rank`, then proves typed filter,
  descending rank sort, offset/limit, exact projection, preview/canonical
  status policy, and stale definition failure: PASS.
- Full integration suite: `117 passed in 547.58s`.
- Full frozen unit/repository suite: `505 passed`; focused query/Render proof:
  `10 passed`; repository unittest proof: `57 passed`.
- `uv lock --check`, frozen sync, Ruff check/format, mypy, compileall,
  repository policy, Mermaid (`16 diagram(s), 307 Markdown scanned`),
  Markdownlint, and `uv build` pass.
- Node 24.14.1 / pnpm 11.22.0 install, lint, format, typecheck, test, build,
  and license evidence pass.
- Clean local Compose project `slaif071d`: `compose-smoke: OK`, including
  health, setup, governance, Puck, preview, responsive desktop/tablet/mobile,
  Render failure/recovery, Agent restart/revoke, media, edge, database/login,
  secret-policy, and 45 repository checks.
- All 20 required GitHub checks on implementation head
  `5fa544c9589263a851f36a7af8d41f5942babe3e` are terminal `SUCCESS`:
  Repository policy; Detect supported languages; Node contracts; Analyze
  (actions, python, javascript-typescript); Python 3.12/3.13/3.14 quality and
  package; Foundation PostgreSQL 14/15/16/17/18; Compose and edge packaging;
  Supply-chain evidence; Markdown; Mermaid; Dependency review; and CodeQL.
  No check is skipped, pending, failed, or cancelled.

## Scope and safety confirmations

- Only order `075-d` was executed. This is an amendment to PR #71; no second
  objective PR, merge, auto-merge, release, dependency, architecture/prior
  report edit, new entity/domain/API, navigation/redirect/locale,
  proposed-side-effect, composition/theme/media, Agent REST/MCP, or
  freeze/publication scope was added.
- Editor validation remains authoritative before persistence, and Render uses
  no dynamic SQL identifiers or caller SQL. No direct base/change-table
  privilege or Control content DML was added. No real secret, capability,
  cookie, credential, token, or private URL was committed or printed.
- Exactly one report-only child is being published from the literal
  implementation SHA above. The coding agent did not merge PR #71 or select a
  subsequent order.

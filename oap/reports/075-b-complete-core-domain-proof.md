# OAP implementation report — 075-b

- ID/order: `075-b-complete-core-domain-proof`
- Mode: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN, unmerged)
- Base/head: `main` / `oap/075-editable-domain-substrate`
- Starting report head: `7f2b191e71a75df2f0b32c1d7e1df9860389cbcf`
- Starting remote baseline: `ef456e63abadddfc7d90794c03be3a63677c87f9`
- Implementation SHA: `ef607ce8c57328a98d7f2c3c9672b37b7861c245`
- Report publication commit: SELF

## Remediation delivered

- Removed the non-catalog `relationship:read` permission and restored the
  architecture permission catalog; relation reads use `content-item:read` and
  writes use `relationship:write`.
- Updated authoritative migration/readiness/package/route expectations to
  `040_001`, repaired Agent semantic-read site isolation, and added new typed
  package inventory entries.
- Made translation/relation PATCH and DELETE require positive
  `expected_row_version`; PATCH replaces the complete locale map, locks the
  row, and returns stable conflict on stale versions.
- Added row-locked relation validation for same-site source/field/target,
  source-type ownership, reference versus multi-reference cardinality,
  allowlisted target type, bounded position/metadata, duplicate positions, and
  stale updates. JSONB serialization and legacy content SECURITY DEFINER
  create paths were repaired for real asyncpg Editor calls.
- Added exact pre-040 field-definition and Agent compatibility restoration in
  downgrade, including COW teardown/rename handling.
- Exported translation/relation request and record models and added focused
  validator tests.

## Required product evidence

- Real PostgreSQL Editor HTTP integration uses fixed control/editor roles,
  authenticated HUMAN session and CSRF, public route handlers, required
  idempotency keys, actual COW/reviewer-backed workspace, type/field/item
  creation, translation/relation CRUD, replay, stale-version 409s, deletion,
  canonical isolation, and exact audit/idempotency counts: PASS.
- Migration downgrade proof exercises `040_001 → 039_001 → 040_001`, verifies
  restored field function signature and create path, and passes with and
  without reconciled COW: PASS.
- Full integration suite: `116 passed`.
- Full unit suite: `439 passed`; repository unittest suite: `57 passed`.
- `uv lock --check`, frozen sync, Ruff check/format, mypy, Python build,
  Node lint/format/typecheck/test/build/licenses, repository policy, Mermaid,
  and Markdown checks: PASS.
- One clean Compose smoke (`slaif071c`) passed all health, setup, governance,
  Puck, preview, responsive desktop/tablet/mobile, Agent-session, public
  restart, media, edge, database-login, and secret-policy evidence.
- The public Agent restart helper retries the bounded post-restart session
  request for transient edge readiness; focused helper tests pass and the clean
  proof records `agent-before=200`, `agent-after-restart=200`, and
  `agent-after-revoke=401`.
- All 20 GitHub required checks on implementation head pass: Repository policy;
  Python 3.12/3.13/3.14; PostgreSQL 14/15/16/17/18; Node contracts; Compose
  and edge packaging; Supply-chain evidence; Markdown; Mermaid; Dependency
  review; Detect supported languages; and CodeQL actions/javascript/python.

## Correction to 075-a

The 075-a report used a short implementation SHA and recorded unresolved
legacy-head failures as PARTIAL. This report supersedes those claims with the
literal 40-hex implementation SHA above, records the repaired expectations and
regressions, and records the complete passing evidence for 075-b. The prior
report file remains unchanged as an immutable historical record.

## Scope and safety confirmations

- Only order `075-b` was executed. The exact active/order transcript bytes were
  committed with implementation. This is an amendment to PR #71; no second
  objective PR, merge, auto-merge, release, dependency, architecture, Agent
  REST, MCP, freeze/publication, navigation, redirect, locale configuration,
  query DSL, composition, theme, media, or proposed-side-effect expansion was
  made.
- No direct base/change-table privilege or Control content DML was added. No
  real secret, capability, cookie, credential, token, or private URL was
  committed or printed. All required checks completed successfully; none was
  skipped, pending, cancelled, or treated as pass without completion.
- Exactly one report-only child is being published. The coding agent did not
  merge PR #71 and selected no subsequent order.

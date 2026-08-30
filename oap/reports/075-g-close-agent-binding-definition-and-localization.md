# OAP Report — 075-g

ID: 075-g
Order: `oap/orders/075-g-close-agent-binding-definition-and-localization.md`
Result: COMPLETE
Delivery: AMENDED_EXISTING_PR

Repository: `ulfe-lmi/slaif-agent-site`
PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN)
Base: `main` (`ef456e63abadddfc7d90794c03be3a63677c87f9`)
Branch: `oap/075-editable-domain-substrate`
Starting report head: `6442388b53da0bdd261772877339aefa377461af`
Prior implementation parent: `6e65d58e2925c9e4555a3d53aaf4827baff29d94`
Implementation commit: `b630b6cf3b8ebf35cb03deed41c20a7b42a5e517`

## Changes

- Restored `control.slaif_agent_require_cow_site(p_site_id)` as the first
  operation in 040 Agent field-definition create/list SECURITY DEFINER wrappers,
  including the 040 downgrade-restored contracts; fixed search paths, PUBLIC
  revocation, and Agent-only grants remain intact.
- Added persisted type-definition compatibility checks before item updates,
  translation create/update, and relation create/update. Stale source/target
  definitions fail with validation and cannot mutate COW, audit, idempotency,
  or canonical state; no stored version is rewritten.
- Rejected localized fields in the shared collection projection validator.
  Render catches malformed or legacy localized projections and returns its
  stable fail-closed projection error rather than emitting incomplete values.
- Preserved exact COW resource identity for sparse translation and relation
  insert returns; arbitrary last-row fallback remains absent.

## Evidence

- `uv run --frozen pytest services/backend/tests/integration -q` — 120 passed
  in 738.30s.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q` —
  513 passed, 26 subtests passed in 15.94s.
- Focused Agent mutation, Editor translation/relation, Render projection, and
  collection-query tests passed after the repairs.
- `uv lock --check`; frozen sync; Ruff check/format; mypy; Python build — pass.
- Repository policy, repository unittest discovery (57), Mermaid (16 diagrams
  in 3 files), Markdown (0 issues), and Node 24.14.1 / pnpm 11.22.0 install,
  lint, format, typecheck, test, build, and licenses — pass.
- Remote PR checks: all 20 required checks completed successfully, including
  Python 3.12/3.13/3.14, Foundation PostgreSQL 14/15/16/17/18, Node,
  Compose/edge, supply-chain, repository policy, dependency review, Markdown,
  Mermaid, and CodeQL.

## Scope and controls

No merge, auto-merge, release, second PR, architecture/constitution/protocol
edit, new entity/API family, MCP, dynamic detail, dependency, hosted service,
or production credential access. The exact 075-g order was followed; no
secrets, capabilities, cookies, or private artifact URLs were printed or
committed. PR #71 remains open and unmerged. No extra objective PR was created.

Report publication commit: SELF

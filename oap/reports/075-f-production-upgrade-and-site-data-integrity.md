# OAP Report — 075-f

ID: 075-f
Order: `oap/orders/075-f-production-upgrade-and-site-data-integrity.md`
Result: COMPLETE
Delivery: AMENDED_EXISTING_PR

Repository: `ulfe-lmi/slaif-agent-site`
PR: [#71](https://github.com/ulfe-lmi/slaif-agent-site/pull/71) (OPEN)
Base: `main` (`ef456e63abadddfc7d90794c03be3a63677c87f9`)
Branch: `oap/075-editable-domain-substrate`
Starting remote report head: `ed3e2b6f852bdee2084023d393204ca3d9026510`
Implementation commit: `6e65d58e2925c9e4555a3d53aaf4827baff29d94`
Pushed implementation: yes

## Changes

- Added a production maintenance-upgrade preflight using only the foundation's
  documented public APIs. It discovers product workspaces, rejects pending COW
  operations before teardown, disables COW safely, and runs the Alembic path.
- Extended the qualified foundation boundary with `disable_cow`,
  `disable_cow_schema`, `get_cow_status`, and public operation inspection.
- Hardened migration 042 with deterministic locale backfill, composite locale
  FKs, workspace/site side-effect binding, exact redirect status checks,
  sibling-position uniqueness, advisory serialization, locale guards, target
  consistency, redirect-chain checks, and current-session ACTIVE side-effect
  binding. Side effects remain PROPOSED and non-public.
- Removed arbitrary “last row” recovery. Sparse COW INSERT/UPDATE returns are
  resolved only through exact resource identity, otherwise the operation fails.
- Kept typed shared validators, optimistic row versions, clear/unset behavior,
  site confinement, and Editor COW routes; added a staged enabled-COW upgrade
  proof and updated the public-API contract test.

## Evidence

Focused PostgreSQL proofs:

- `uv run --frozen pytest services/backend/tests/integration/test_editable_domain_proof.py::test_site_data_substrate_downgrades_from_head_to_041_and_back services/backend/tests/integration/test_editable_domain_proof.py::test_upgrade_rebuilds_enabled_cow_without_pending_workspace_operations -q` — passed.
- `uv run --frozen pytest services/backend/tests/integration/test_human_editor_production_http.py::test_editor_http_site_data_substrate_is_cow_and_versioned -q` — passed.
- Eleven previously failing agent/editor/browser integration cases — passed.

Required local gates:

- `uv lock --check`; `uv sync --frozen --all-groups`; Ruff check/format; mypy;
  `uv build` — passed.
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q` —
  513 passed, 26 subtests passed.
- `uv run --frozen pytest services/backend/tests/integration -q` — 120 passed.
- Repository unittest discovery — 57 passed; repository policy — passed;
  Mermaid — 16 diagrams in 3 files, 311 Markdown files; Markdown lint — 0
  issues in 305 files.
- Node 24.14.1 / pnpm 11.22.0: install, lint, format:check, typecheck, test,
  build, and licenses — passed.

Remote PR checks at implementation head: all 20 required checks completed
successfully, including Python 3.12/3.13/3.14, Foundation PostgreSQL 14/15/16/17/18,
Node contracts, Compose and edge packaging, supply-chain evidence, repository
policy, dependency review, Markdown, Mermaid, and CodeQL analyses.

## Scope and controls

No merge, auto-merge, release, second PR, architecture/constitution/protocol
edit, new product entity family, side-effect executor, hosted dependency, or
production credential access. `oap/active` and the exact immutable order were
committed unchanged with the implementation. No secrets, capabilities, cookies,
or private artifact URLs were printed or committed. Pre-existing unrelated
changes were preserved. Pending-work rejection is implemented before any COW
destructive preparation; the staged proof covers the empty-pending maintenance
state, while remote matrix checks provide the independent final gate.

Report publication commit: SELF

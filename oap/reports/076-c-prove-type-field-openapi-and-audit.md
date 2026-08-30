# OAP Report — 076-c

ID: 076-c  
Order: `oap/orders/076-c-prove-type-field-openapi-and-audit.md`  
Result: COMPLETE  
Delivery: AMENDED_EXISTING_PR

Repository: `ulfe-lmi/slaif-agent-site`  
PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) (OPEN)  
Base: `main` (`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`)  
Branch: `oap/076-agent-model-content-semantics`  
Starting report head: `57f9052016830ea2fe43929d485167c26544e41b`

Transcript commit (active/order bytes): `2424d90`  
Final implementation SHA: `0a9fa37ddfaaa4b8853257241be364f92465ff49`  
Implementation commits: `86fac1b`, `0902a88`, `3e593de`, `9dba1fa`, `0a9fa37`  
Report publication commit: SELF

## Changes

- Enforced exact Agent field/type scopes and explicit capability route-policy
  classification/coverage, including OpenAPI and preview routes; Agent app
  construction now fails closed on policy drift.
- Enforced capability resource allowlists before COW and preserved site/type/
  workspace binding; field creation requires `field-definition:create` only.
- Generalized mutation completion status and quota kind (200 update/delete,
  201 create, distinct delete budget), stable validation mapping, and replay
  single-charge behavior.
- Published the bounded Agent-v1 OpenAPI endpoint with bearer security and
  per-route scope metadata while retaining disabled docs UI.
- Added/updated public Agent integration fixtures to exercise the corrected
  scope contract. No items, translations, relations, views, pages, media,
  MCP, review, dependency, or architecture work was included.

## Verification

- Unit/repository: `513 passed, 26 subtests passed`; focused route-policy and
  health tests: `16 passed`; Agent mutation integration: `5 passed`.
- Full integration: `120 passed` (clean single-process run).
- Frozen Python lock/sync, Ruff check/format, mypy, repository policy,
  compileall, repository unittest discovery (`57`), Mermaid (`16` diagrams),
  Markdownlint (`310` files), and Node 24.14.1 / pnpm 11.22.0 gates passed.
- Final implementation PR checks: all 20 completed SUCCESS, including Python
  3.12/3.13/3.14, PostgreSQL 14–18, Node, Compose/edge, supply-chain,
  repository policy, Markdown, Mermaid, dependency review, and CodeQL.

## Evidence and reconciliation

076-a and 076-b reports were not edited. This report records their literal
full implementation/report SHAs and the fact that their report-head checks
were still pending at publication; 076-a also lacked committed functional
tests and had prose whitespace drift. 076-c adds the committed focused/public
coverage and corrects the scope and evidence claims append-only.

## Controls and limitations

No merge, acceptance, second PR, post-report push, architecture/constitution/
protocol edit, production access, or real secret/capability/cookie/token was
used. The PR remains open for independent strategic review; broader Objective
076 continuations remain out of scope.

Report publication commit: SELF

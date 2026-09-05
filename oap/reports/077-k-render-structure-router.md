# OAP implementation report — 077-k

## Publication and identity

- Order: `077-k`, `oap/orders/077-k-render-structure-router.md`
- Order SHA-256: `47848d9c0089c6695fb9424e52af6f7d8b2db274dc4704ea337a69bcc009adbb`
- Active bytes: `077-k` followed by LF; active SHA-256:
  `f8432650d64fa3fd6aa7e4358ba9699ff96fa9f75b85b7c647cb5df4b8143f63`
- Delivery: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `/home/ubuntu/codex-work/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), open,
  non-draft, base `main`, branch `oap/077-agent-site-structure-semantics`
- Required starting remote report head:
  `a51e5d278ac0505a4fc770f75e82af49a3f3693d`
- Literal final implementation SHA:
  `1682327b78a83ef1eed2cde1312ee7def5c7e2c2`
Report publication commit: SELF

The strategy-owned order and `oap/active` were read in full, remained byte-for-
byte unchanged, and were included unchanged in the implementation history.
No second PR was created and the objective PR was not merged.

## Exact implementation delivered

The Render service now has one bounded static structure projection for canonical,
human-preview, and browser-preview contexts. Migration `052_001` adds only the
narrow, site-confined `content.slaif_render_page_resolve` and
`content.slaif_render_navigation_items` SECURITY DEFINER functions. They use the
authoritative effective-route helper, reject terminal dynamic templates, and are
granted only to the public and preview reader roles. No arbitrary page-ID oracle
was exposed.

The implementation updates `SiteResolver` for same-connection resolution,
Render projection routing, locale truth, complete typed navigation, redirect
graph validation, exact redirect status/location projection, and repeatable-read
canonical/COW snapshots. It exposes page parent, route template, and effective
route, while retaining the existing composition, catalog, theme, and binding
contracts.

The Web contract is a discriminated page/redirect result. A small Node Proxy
boundary returns exact 301/302 responses for human public/preview requests;
ordinary pages, reserved application paths, browser-preview requests, and
303/307/308 handling remain on their existing single-request route. Browser
preview credentials are not preflighted and therefore remain one-time. Preview
internal locations retain `/preview/<workspace-id>` and the trusted site prefix.

Changed implementation/test areas are:

- `services/backend/src/slaif_agent_site/db/alembic/versions/052_001_render_structure_projection.py`
- `services/backend/src/slaif_agent_site/db/privileges.py`
- `services/backend/src/slaif_agent_site/sites/resolver.py`
- `services/backend/src/slaif_agent_site/render_api/projection.py`
- `services/backend/src/slaif_agent_site/render_api/site_http.py`
- `apps/web/src/sites/render.ts`
- `apps/web/proxy.ts`
- `apps/web/app/page.tsx`
- `apps/web/app/[...sitePath]/page.tsx`
- `apps/web/app/preview/[workspaceId]/[[...sitePath]]/page.tsx`
- `services/backend/tests/integration/test_render_structure_router.py`
- `tests/e2e/preview.spec.ts`
- `tools/compose/e2e.sh`
- related migration-head, Render-contract, and repository-test expectations

No Agent public route, OpenAPI contract, capability scope, media/MCP behavior,
composition/design behavior, review/promotion behavior, dependency, image,
architecture, or historical OAP artifact was broadened.

## Commit and remote evidence

All commits were pushed to the existing PR branch, in order:

```text
f8ed66e51e1df82473c6ac76c1ca20a1827cf09f feat(render): project static site structure
a90dea93243a4d3efe21d8b6d320bff5b9dcb2ee test(render): verify preview redirect boundary
c742b8ab567f33bcf881d1eb0ad8aff60f637e21 test(render): cover preview redirect result
26c6a4624d9d1ce1579d36846ca07e367d3d9554 test(render): expose redirect boundary diagnostics
e47910c34b0f55381835e710d0f658f74cbe6b65 test(render): record preview redirect status
b905627bf78182ecf9d0e213f3a3bde0f0026e70 fix(web): preserve static redirect status codes
c282f03173353c17908a6d5938d21e70a5ee0c72 fix(web): serve exact static redirects
1682327b78a83ef1eed2cde1312ee7def5c7e2c2 fix(web): preserve one-time browser preview
```

The final remote PR head was verified as the literal implementation SHA above.
The final authoritative CI run was [33944689147](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/33944689147)
and passed every job: Repository policy, Node contracts, Supply-chain evidence,
Dependency review, Compose and edge packaging, Python 3.12/3.13/3.14 quality
and package, Foundation PostgreSQL 14/15/16/17/18, Markdown, and Mermaid.
The final CodeQL run was [33944689280](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/33944689280)
and passed Detect supported languages, Analyze actions, Analyze Python, Analyze
JavaScript/TypeScript, and CodeQL.

## Acceptance evidence

- Real PostgreSQL Render tests cover root, nested hierarchy, effective routes,
  parent/template fields, non-default locale routing, typed navigation and PAGE
  target projection, exact 301/307 redirect projection, reserved/encoded/
  dynamic/disabled-locale negatives, and Agent HTTP-created COW state.
- Canonical reads remain unchanged for unpromoted Agent state and the preview
  projection observes the authorized workspace state only.
- Canonical and COW projections use coherent repeatable-read snapshots;
  cancellation, pool cleanup, authorization recheck, and Render restart tests
  passed. Cross-site and cross-workspace confinement remained enforced.
- The final Compose job passed the public NGINX/Web evidence. Its browser log
  recorded `stage=preview-redirect-301`, followed by `compose-e2e: OK`; the
  complete clean deployment, edge, failure-smoke, public-Agent, browser-worker,
  and secret-policy sequence also passed.
- The Agent public surface remained unchanged; the final Compose acceptance
  recorded exact OpenAPI/restart/isolation checks.
- Dynamic `{slug}` collection-detail matching remains deliberately unresolved,
  as required by this order and reserved for a later Objective 077 slice.

## Verification performed

Local Python and repository gates passed:

- `uv lock --check`
- `uv sync --frozen --all-groups`
- Ruff check and format check, mypy, unit/repository tests: 522 passed, one
  warning, 26 subtests
- Full backend integration suite: 165 passed in 1380.18 seconds
- Focused Render, structure-router, Agent journey, bootstrap, and control
  suites passed, including the 30-test bootstrap subset
- `python -m compileall -q tools tests/repository`
- repository tests: 58 passed, 26 subtests
- `python tools/check_repository.py`: PASS
- `python tools/check_mermaid.py`: PASS, 16 diagrams across 387 Markdown files
- Markdownlint: zero issues in 381 files

Local Node gates passed during the implementation sequence, including Node
24.14.1, pnpm 11.22.0, frozen install, lint, format check, typecheck, contract
tests, build, and license inventory. The final web changes additionally passed
web lint, typecheck, Prettier, and the production `pnpm build`. The authoritative
final PR CI reran the complete frozen Node contract gate and passed it.

Skipped, pending, failed, or cancelled checks are not being claimed as final
evidence. Earlier intermediate heads had a Compose redirect failure and were
superseded by the in-scope Web boundary fixes; the final head passed.

## Scope and completion boundary

No real secrets, capabilities, cookies, private preview credentials, internal
URLs, production systems, or Docker authority were accessed from this workspace.
No extra PR, merge, auto-merge, release, or unrelated cleanup occurred. Issue
`#67` remains open until the containing Objective 077 commit is merged to
verified `main`.

The strongest non-acceptance consideration is governance, not implementation:
PR #74 is intentionally still open for independent strategic review, and this
report covers only 077-k rather than the remaining Objective 077 dynamic-detail
slice. Objective 077-k is execution-complete when strategy accepts this report;
the PR becomes product-complete only after the strategy-controlled review and
eventual merge to verified `main`. The coding agent is not authorized to merge.
